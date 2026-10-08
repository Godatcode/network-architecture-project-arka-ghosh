import importlib.machinery
import importlib.util
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / name))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


server = load_script("bserve")
client = load_script("bcurl")


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "index.html").write_bytes(b"one socket\n")

    def tearDown(self):
        self.temp.cleanup()

    def start_server(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        listener.settimeout(2)
        port = listener.getsockname()[1]
        accepted = []

        def run():
            try:
                conn, _ = listener.accept()
                accepted.append(conn)
                server.handle_connection(conn, self.root)
            finally:
                listener.close()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return port, thread, accepted

    def test_client_server_one_connection_two_requests_and_verbose(self):
        port, thread, accepted = self.start_server()
        result = subprocess.run(
            [str(ROOT / "bcurl"), "-v", f"127.0.0.1:{port}/index.html", f"127.0.0.1:{port}/missing.txt"],
            capture_output=True, timeout=5,
        )
        thread.join(2)
        self.assertEqual(result.returncode, 22, result.stderr)
        self.assertEqual(result.stdout, b"one socket\nfile not found\n")
        self.assertEqual(len(accepted), 1)
        self.assertEqual(result.stderr.count(b"> request stream"), 2)
        self.assertEqual(result.stderr.count(b"< frame type 2"), 2)

    def test_unknown_type_is_skipped_before_next_request(self):
        left, right = socket.socketpair()
        thread = threading.Thread(target=server.handle_connection, args=(right, self.root), daemon=True)
        thread.start()
        opaque = b"not a header block"
        unknown = server.FIXED.pack(b"BC", 1, 99, 0xff, 255, 7, len(opaque)) + opaque
        left.sendall(unknown + client.make_request("localhost", 9000, "/index.html", 8))
        kind, stream, headers, body, _ = client.read_response(left)
        self.assertEqual((kind, stream, headers[":status"], body), (2, 8, "200", b"one socket\n"))
        left.close()
        thread.join(2)

    def test_bad_header_and_unsafe_path(self):
        left, right = socket.socketpair()
        thread = threading.Thread(target=server.handle_connection, args=(right, self.root), daemon=True)
        thread.start()
        left.sendall(client.make_request("localhost", 9000, "/%2e%2e/secret", 1))
        _, _, fields, _, _ = client.read_response(left)
        self.assertEqual(fields[":status"], "400")
        malformed = server.FIXED.pack(b"BC", 1, 1, 1, 1, 2, 2) + b"\x01\x00"
        left.sendall(malformed)
        _, stream, fields, _, _ = client.read_response(left)
        self.assertEqual((stream, fields[":status"], fields["connection"]), (0, "400", "close"))
        left.close()
        thread.join(2)

    def test_client_skips_unknown_response_type(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]

        def peer():
            with listener:
                conn, _ = listener.accept()
                with conn:
                    conn.recv(4096)
                    opaque = b"future bytes"
                    conn.sendall(server.FIXED.pack(b"BC", 1, 77, 0xff, 200, 9, len(opaque)) + opaque)
                    conn.sendall(server.reply(1, 200, b"ok"))

        thread = threading.Thread(target=peer, daemon=True)
        thread.start()
        result = subprocess.run([str(ROOT / "bcurl"), "-v", f"127.0.0.1:{port}/x"], capture_output=True, timeout=5)
        thread.join(2)
        self.assertEqual((result.returncode, result.stdout), (0, b"ok"), result.stderr)
        self.assertEqual(result.stderr.count(b"< frame type"), 2)


if __name__ == "__main__":
    unittest.main()
