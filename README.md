# Binary Content Protocol (BCP)

This submission contains the two tracks in the project brief: a TCP file server (`bserve`) and a TCP command-line client (`bcurl`). They have separate wire-format implementations. The document in `docs/` is their shared contract.

Requires Python 3.10 or newer. No runtime packages are needed.

## Run

In one terminal:

```sh
./bserve ./www 9000
```

In another:

```sh
./bcurl -v localhost:9000/index.html
./bcurl localhost:9000/index.html localhost:9000/missing.txt
```

The body goes to standard output. `-v` sends a complete hexdump of every sent and received frame to standard error. The second command uses one connection and exits with code 22 because the second response is 404. A framing or connection failure exits with code 2.

## Hand-in files

- `docs/protocol-specification.pdf`: the two-page protocol specification
- `docs/protocol-specification.md`: editable source of the specification
- `bserve` and `bcurl`: executable server and client
- `docs/annotated-hexdump.md`: one complete, annotated request and response captured from these programs
- `www/index.html`: demonstration file used in the trace

To run the integration checks: `python3 -m unittest discover -s tests -v`.
