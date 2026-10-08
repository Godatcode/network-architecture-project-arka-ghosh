#!/usr/bin/env python3
"""Capture and annotate an exchange between the submitted programs."""

import importlib.machinery
import importlib.util
from pathlib import Path
import socket
import threading


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / name))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


server = load("bserve")
client = load("bcurl")
request = client.make_request("localhost", 9000, "/index.html", 1)
left, right = socket.socketpair()
thread = threading.Thread(target=server.handle_connection, args=(right, ROOT / "www"))
thread.start()
left.sendall(request)
kind, stream, headers, body, response = client.read_response(left)
left.close()
thread.join()
assert (kind, stream, headers[":status"]) == (2, 1, "200")
assert body == (ROOT / "www" / "index.html").read_bytes()


def hexline(raw):
    result = []
    for offset in range(0, len(raw), 16):
        chunk = raw[offset:offset + 16]
        digits = " ".join(f"{item:02x}" for item in chunk)
        display = "".join(chr(item) if 32 <= item < 127 else "." for item in chunk)
        result.append(f"{offset:04x}  {digits:<47}  |{display}|")
    return "\n".join(result)


def describe(raw):
    magic, version, kind, flags, count, stream, length = server.FIXED.unpack(raw[:12])
    result = [
        f"| `00-01` | `{raw[:2].hex(' ')}` | magic `{magic.decode('ascii')}` |",
        f"| `02` | `{version:02x}` | version {version} |",
        f"| `03` | `{kind:02x}` | {'request' if kind == 1 else 'response'} |",
        f"| `04` | `{flags:02x}` | `END_STREAM` set |",
        f"| `05` | `{count:02x}` | {count} header fields |",
        f"| `06-07` | `{raw[6:8].hex(' ')}` | stream {stream} |",
        f"| `08-0b` | `{raw[8:12].hex(' ')}` | {length} payload bytes |",
    ]
    offset = 12
    for _ in range(count):
        start = offset
        code = raw[offset]
        offset += 1
        if code:
            name = server.NAMES[code]
        else:
            name_length = raw[offset]
            offset += 1
            name = raw[offset:offset + name_length].decode("ascii")
            offset += name_length
        width = int.from_bytes(raw[offset:offset + 2], "big")
        offset += 2
        value = raw[offset:offset + width].decode("utf-8")
        offset += width
        result.append(f"| `{start:02x}-{offset - 1:02x}` | `{raw[start:offset].hex(' ')}` | name code {code}: `{name}` = `{value}` ({width} value bytes) |")
    if offset < len(raw):
        result.append(f"| `{offset:02x}-{len(raw) - 1:02x}` | see dump | body: {len(raw) - offset} bytes, begins `{raw[offset:offset + 4].hex(' ')}` |")
    return "\n".join(result)


document = f"""# Annotated BCP wire exchange

Captured from the submitted `bcurl` request encoder and `bserve` connection handler over a socket pair. The response parser checked the status, stream ID, and body against `www/index.html`. Hex offsets start at zero for each frame. Integers are big-endian. Both frames are shown in full.

## Request: `GET /index.html` ({len(request)} bytes)

| Offset | Bytes | Meaning |
|---|---|---|
{describe(request)}

No bytes remain after the fifth request header, so the request body is empty.

```text
{hexline(request)}
```

## Response: `200` ({len(response)} bytes)

| Offset | Bytes | Meaning |
|---|---|---|
{describe(response)}

The body is the complete {len(body)}-byte `www/index.html` file. Its first four bytes (`{body[:4].hex(' ')}`) are `<!do` in ASCII. The `content-length` value is {len(body)}, matching the body exactly. The server keeps the connection available for another frame after this response.

```text
{hexline(response)}
```
"""
(ROOT / "docs" / "annotated-hexdump.md").write_text(document)
