# Binary Content Protocol (BCP), version 1

Default TCP port: 9000. All multi-byte integers are unsigned and big-endian. Version 1 uses one request frame and one response frame per resource. A client can repeat this exchange on the same TCP connection; it sends the next request after reading the previous response. Responses repeat the request's stream ID. TCP reads may return fewer bytes than requested, so a receiver reads exactly 12 bytes for the fixed header, then exactly the advertised payload length. EOF partway through a frame is an error.

## Fixed frame header (12 bytes)

| Offset | Width | Field | Version 1 meaning |
|---:|---:|---|---|
| 0 | 2 | magic | ASCII `BC` (`42 43` hex) |
| 2 | 1 | version | `01` |
| 3 | 1 | type | `01` request; `02` response |
| 4 | 1 | flags | bit 0 (`END_STREAM`) set; other bits clear |
| 5 | 1 | header count | number of fields at the start of the payload |
| 6 | 2 | stream ID | 1-65535 for requests; echoed by replies; 0 for connection errors |
| 8 | 4 | payload length | bytes after this header, at most 8,388,608 in version 1 |

The magic rejects unrelated traffic early. One-byte version and type fields leave room for extensions. A 16-bit ID is sufficient for a sequential client and allows later correlation of overlapping requests. The four-byte length makes even an unfamiliar frame skippable; the 8 MiB implementation cap limits memory use. `END_STREAM` marks the complete message in this single frame and leaves room for multi-frame messages later.

**Forward compatibility:** A receiver meeting a frame type it does not know MUST read and discard exactly `payload length` bytes, ignore that frame's flags, header count, and payload contents, then continue at the next fixed header. It MUST NOT interpret an unfamiliar payload as headers. An unknown type produces no response on its own.

## Payload: headers followed by body

The first `header count` fields form the header block. The rest of the payload is the body. Each field encodes a name followed by a UTF-8 value:

```text
Indexed name:  1-byte code (1-10) | 2-byte value length | value bytes
Literal name:  00 | 1-byte name length | ASCII name | 2-byte value length | value bytes
```

The literal name length is 1-255 bytes; names contain only lowercase `a-z`, digits, and hyphens. Values are 0-65535 bytes. Duplicate names, unknown indexed name codes, invalid UTF-8, and lengths extending past the frame are malformed. Header names are case-sensitive. The body has no extra delimiter; its length is the payload length minus the bytes used by the header block.

| Code | Name | Direction | Code | Name | Direction |
|---:|---|---|---:|---|---|
| 1 | `:method` | request | 6 | `:status` | response |
| 2 | `:path` | request | 7 | `content-length` | response |
| 3 | `host` | request | 8 | `content-type` | response |
| 4 | `user-agent` | request | 9 | `server` | response |
| 5 | `accept` | request | 10 | `connection` | response |

Codes 1-10 replace the ten names sent by the programs; literal code 0 permits other names without a shared dynamic table.

## Requests, responses, and files

A request is type 1, has a nonzero stream ID and no body, and requires `:method`, `:path`, and `host`. The client also sends `user-agent` and `accept`. Version 1 supports `GET`; another method receives 405. `:path` starts with `/`; the optional query after `?` is ignored for file lookup. The server percent-decodes the path once, rejects invalid escapes, NUL, backslash, `.` and `..` segments, duplicate slashes, and paths resolving outside its root. A directory resolves to its `index.html`.

A response is type 2, echoes the request ID, and requires decimal three-digit `:status`, decimal `content-length`, `content-type`, `server`, and `connection`. `content-length` equals the body byte count. Status 200 carries the file bytes; 400 means malformed frame/request or unsafe path; 404 means no readable file; 405 means unsupported method. Errors carry UTF-8 plain text. The client writes the body to stdout, writes hexdumps to stderr with `-v`, and exits nonzero for any 4xx/5xx.

For malformed framing (bad magic/version/flags, oversize or truncated payload, invalid header encoding), the server sends a 400 response with stream ID 0 and `connection: close` if it can, then closes. A request using stream ID 0 also gets 400 and closes. An unknown frame type follows the skip rule above. Otherwise, the connection stays open for more requests. The server closes idle connections after 15 seconds; the client times out after 10 seconds. Peers close only between complete frames during normal operation.
