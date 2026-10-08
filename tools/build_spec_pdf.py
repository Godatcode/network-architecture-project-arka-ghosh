#!/usr/bin/env python3
"""Build the two-page BCP wire specification for hand-in."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


OUT = Path(__file__).resolve().parents[1] / "docs" / "protocol-specification.pdf"
navy = colors.HexColor("#17324a")
teal = colors.HexColor("#087e81")
gray = colors.HexColor("#536474")
paper = colors.HexColor("#f0f5f7")
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleBCP", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=17, leading=20, textColor=navy, spaceAfter=7))
styles.add(ParagraphStyle(name="SubBCP", parent=styles["Normal"], fontSize=8.7, leading=12, textColor=gray, spaceAfter=12))
styles.add(ParagraphStyle(name="HeadBCP", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10.7, leading=13, textColor=teal, spaceBefore=10, spaceAfter=5))
styles.add(ParagraphStyle(name="BodyBCP", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.6, leading=12.2, spaceAfter=6))
styles.add(ParagraphStyle(name="SmallBCP", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.6, leading=10.5, spaceAfter=4))
styles.add(ParagraphStyle(name="CellBCP", parent=styles["Normal"], fontName="Helvetica", fontSize=7.4, leading=9.3))
styles.add(ParagraphStyle(name="CellHeadBCP", parent=styles["CellBCP"], fontName="Helvetica-Bold", textColor=colors.white))


def para(text, style="BodyBCP"):
    return Paragraph(text, styles[style])


def table(rows, widths):
    cells = [[para(str(value), "CellHeadBCP" if n == 0 else "CellBCP") for value in row] for n, row in enumerate(rows)]
    result = Table(cells, colWidths=widths, hAlign="LEFT", repeatRows=1)
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, paper]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d5e0e5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return result


story = [
    para("Binary Content Protocol (BCP) - version 1", "TitleBCP"),
    para("Wire specification  |  TCP port 9000  |  all multi-byte integers unsigned, big-endian", "SubBCP"),
    para("1. Connection model", "HeadBCP"),
    para("BCP retrieves named files. A client opens one TCP connection and may make several exchanges on it. Version 1 sends one request frame, reads its response, then sends the next request. Responses echo the request's nonzero stream ID. TCP has no message boundaries: read exactly 12 fixed-header bytes, then exactly the stated payload length. A short read is normal; EOF inside a frame is an error."),
    para("2. Fixed frame header - 12 bytes", "HeadBCP"),
    table([
        ["Offset", "Bytes", "Field", "Value or meaning"],
        ["0", "2", "magic", "ASCII BC (hex 42 43)"],
        ["2", "1", "version", "01"],
        ["3", "1", "type", "01 request; 02 response"],
        ["4", "1", "flags", "bit 0 END_STREAM = 1; others 0"],
        ["5", "1", "header count", "number of fields at payload start"],
        ["6", "2", "stream ID", "1-65535; 0 for connection errors"],
        ["8", "4", "payload length", "following bytes; version 1 cap 8,388,608"],
    ], [44, 44, 88, 340]),
    Spacer(1, 6),
    para("The magic rejects unrelated traffic; one-byte version/type fields leave extension space. A 16-bit ID suffices for sequential exchanges and permits later correlation. The four-byte length lets a receiver locate the next frame even when it cannot interpret this one; the 8 MiB cap bounds memory use. END_STREAM says this frame completes the message and leaves room for multi-frame messages later.", "SmallBCP"),
    para("Forward compatibility rule", "HeadBCP"),
    para("A receiver meeting a frame type it does not know <b>MUST read and discard exactly its payload length</b>, ignore that frame's flags, header count, and contents, then continue at the next fixed header. It MUST NOT parse the unknown payload as headers. An unknown type alone causes no response."),
    para("3. Payload and header names", "HeadBCP"),
    para("The first <b>header count</b> fields are headers; all remaining payload bytes are the body. Indexed field: <font name='Courier'>code(1) | value length(2) | UTF-8 value</font>. Literal field: <font name='Courier'>00 | name length(1) | ASCII name | value length(2) | UTF-8 value</font>. Literal names are 1-255 bytes of lowercase letters, digits, or hyphens; values are 0-65,535 bytes. Duplicate names, unknown index codes, bad UTF-8, and lengths beyond the frame are malformed. Names are case-sensitive."),
    table([
        ["Code", "Name", "Sent by", "Code", "Name", "Sent by"],
        ["1", ":method", "client", "6", ":status", "server"],
        ["2", ":path", "client", "7", "content-length", "server"],
        ["3", "host", "client", "8", "content-type", "server"],
        ["4", "user-agent", "client", "9", "server", "server"],
        ["5", "accept", "client", "10", "connection", "server"],
    ], [38, 118, 60, 38, 132, 130]),
    PageBreak(),
    para("Binary Content Protocol (BCP) - version 1", "TitleBCP"),
    para("Message semantics and error handling", "SubBCP"),
    para("4. Request", "HeadBCP"),
    para("A request has type 1, END_STREAM set, a nonzero stream ID, and an empty body. It requires <font name='Courier'>:method</font> = GET, an origin-form <font name='Courier'>:path</font> starting with /, and <font name='Courier'>host</font>. The supplied client also sends <font name='Courier'>user-agent</font> and <font name='Courier'>accept</font>. A different method gets 405. Header values are UTF-8; the path's optional query after ? is ignored for file lookup."),
    para("5. Response", "HeadBCP"),
    para("A response has type 2, END_STREAM set, and the matching stream ID. It includes a three-digit decimal <font name='Courier'>:status</font>, decimal <font name='Courier'>content-length</font>, <font name='Courier'>content-type</font>, <font name='Courier'>server</font>, and <font name='Courier'>connection</font>. Content length is the exact body byte count. A 200 body is the requested file's bytes; an error body is UTF-8 plain text. The client writes bodies to stdout, hexdumps every frame to stderr with -v, and exits nonzero for any 4xx/5xx."),
    para("6. File mapping", "HeadBCP"),
    para("The server maps the decoded path beneath its configured root. It percent-decodes once and rejects invalid percent escapes, NUL, backslash, duplicate slashes, . or .. path segments, and paths that resolve outside the root (including symlinks). A directory maps to index.html. Missing or unreadable files produce 404."),
    para("7. Status and connection behavior", "HeadBCP"),
    table([
        ["Status", "When sent", "Connection"],
        ["200", "File returned", "stays open"],
        ["400", "Malformed frame/request or unsafe path", "closes for framing errors; otherwise stays open"],
        ["404", "File missing or unreadable", "stays open"],
        ["405", "Method other than GET", "stays open"],
    ], [56, 244, 216]),
    Spacer(1, 7),
    para("For bad magic/version/flags, an oversize or truncated payload, or malformed header encoding, the server sends 400 on stream 0 with <font name='Courier'>connection: close</font> if possible, then closes. A request using stream 0 also gets 400 and closes. Unknown frame types follow the skip rule on page 1. Otherwise the connection remains available for more requests. The server's idle timeout is 15 seconds; the client's is 10 seconds. Normal closure occurs between complete frames."),
    para("8. Byte-level example", "HeadBCP"),
    para("For GET /index.html on stream 1, the 12-byte request prefix is <font name='Courier'>42 43 01 01 01 05 00 01 00 00 00 37</font>: magic BC, version 1, request type, END_STREAM, five headers, stream 1, and 55 payload bytes. The response repeats stream 1. See the accompanying annotated-hexdump.md for every byte of a complete exchange."),
]


def footer(canvas, doc):
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#c9d7dd"))
    canvas.line(40, 35, width - 40, 35)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(gray)
    canvas.drawString(40, 23, "BCP v1 | Network Architecture project")
    canvas.drawRightString(width - 40, 23, f"{doc.page} / 2")
    canvas.restoreState()


document = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=40, rightMargin=40, topMargin=38, bottomMargin=48)
document.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
