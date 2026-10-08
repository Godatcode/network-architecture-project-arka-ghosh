# Annotated BCP wire exchange

Captured from the submitted `bcurl` request encoder and `bserve` connection handler over a socket pair. The response parser checked the status, stream ID, and body against `www/index.html`. Hex offsets start at zero for each frame. Integers are big-endian. Both frames are shown in full.

## Request: `GET /index.html` (67 bytes)

| Offset | Bytes | Meaning |
|---|---|---|
| `00-01` | `42 43` | magic `BC` |
| `02` | `01` | version 1 |
| `03` | `01` | request |
| `04` | `01` | `END_STREAM` set |
| `05` | `05` | 5 header fields |
| `06-07` | `00 01` | stream 1 |
| `08-0b` | `00 00 00 37` | 55 payload bytes |
| `0c-11` | `01 00 03 47 45 54` | name code 1: `:method` = `GET` (3 value bytes) |
| `12-1f` | `02 00 0b 2f 69 6e 64 65 78 2e 68 74 6d 6c` | name code 2: `:path` = `/index.html` (11 value bytes) |
| `20-30` | `03 00 0e 6c 6f 63 61 6c 68 6f 73 74 3a 39 30 30 30` | name code 3: `host` = `localhost:9000` (14 value bytes) |
| `31-3c` | `04 00 09 62 63 75 72 6c 2f 31 2e 30` | name code 4: `user-agent` = `bcurl/1.0` (9 value bytes) |
| `3d-42` | `05 00 03 2a 2f 2a` | name code 5: `accept` = `*/*` (3 value bytes) |

No bytes remain after the fifth request header, so the request body is empty.

```text
0000  42 43 01 01 01 05 00 01 00 00 00 37 01 00 03 47  |BC.........7...G|
0010  45 54 02 00 0b 2f 69 6e 64 65 78 2e 68 74 6d 6c  |ET.../index.html|
0020  03 00 0e 6c 6f 63 61 6c 68 6f 73 74 3a 39 30 30  |...localhost:900|
0030  30 04 00 09 62 63 75 72 6c 2f 31 2e 30 05 00 03  |0...bcurl/1.0...|
0040  2a 2f 2a                                         |*/*|
```

## Response: `200` (135 bytes)

| Offset | Bytes | Meaning |
|---|---|---|
| `00-01` | `42 43` | magic `BC` |
| `02` | `01` | version 1 |
| `03` | `02` | response |
| `04` | `01` | `END_STREAM` set |
| `05` | `05` | 5 header fields |
| `06-07` | `00 01` | stream 1 |
| `08-0b` | `00 00 00 7b` | 123 payload bytes |
| `0c-11` | `06 00 03 32 30 30` | name code 6: `:status` = `200` (3 value bytes) |
| `12-16` | `07 00 02 35 39` | name code 7: `content-length` = `59` (2 value bytes) |
| `17-31` | `08 00 18 74 65 78 74 2f 68 74 6d 6c 3b 20 63 68 61 72 73 65 74 3d 75 74 66 2d 38` | name code 8: `content-type` = `text/html; charset=utf-8` (24 value bytes) |
| `32-3e` | `09 00 0a 62 73 65 72 76 65 2f 31 2e 30` | name code 9: `server` = `bserve/1.0` (10 value bytes) |
| `3f-4b` | `0a 00 0a 6b 65 65 70 2d 61 6c 69 76 65` | name code 10: `connection` = `keep-alive` (10 value bytes) |
| `4c-86` | see dump | body: 59 bytes, begins `3c 21 64 6f` |

The body is the complete 59-byte `www/index.html` file. Its first four bytes (`3c 21 64 6f`) are `<!do` in ASCII. The `content-length` value is 59, matching the body exactly. The server keeps the connection available for another frame after this response.

```text
0000  42 43 01 02 01 05 00 01 00 00 00 7b 06 00 03 32  |BC.........{...2|
0010  30 30 07 00 02 35 39 08 00 18 74 65 78 74 2f 68  |00...59...text/h|
0020  74 6d 6c 3b 20 63 68 61 72 73 65 74 3d 75 74 66  |tml; charset=utf|
0030  2d 38 09 00 0a 62 73 65 72 76 65 2f 31 2e 30 0a  |-8...bserve/1.0.|
0040  00 0a 6b 65 65 70 2d 61 6c 69 76 65 3c 21 64 6f  |..keep-alive<!do|
0050  63 74 79 70 65 20 68 74 6d 6c 3e 0a 3c 74 69 74  |ctype html>.<tit|
0060  6c 65 3e 42 43 50 3c 2f 74 69 74 6c 65 3e 0a 3c  |le>BCP</title>.<|
0070  68 31 3e 4f 6e 65 20 63 6f 6e 6e 65 63 74 69 6f  |h1>One connectio|
0080  6e 3c 2f 68 31 3e 0a                             |n</h1>.|
```
