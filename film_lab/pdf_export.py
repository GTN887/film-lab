"""Minimal single-font PDF writer so scene export works without reportlab."""

from __future__ import annotations

from pathlib import Path


def write_simple_pdf(text: str, dest: Path, *, title: str = "Film Lab scene") -> Path:
    lines = _wrap(text.replace("\r\n", "\n"), width=86)
    pages: list[list[str]] = []
    page: list[str] = []
    for line in lines:
        page.append(line)
        if len(page) >= 52:
            pages.append(page)
            page = []
    if page:
        pages.append(page)
    if not pages:
        pages = [[""]]

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{3 + i} 0 R" for i in range(len(pages)))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode("ascii"))

    font_id = 3 + len(pages)
    for page_lines in pages:
        content = _page_stream(page_lines)
        content_id = font_id + 1 + (len(objects) - 2)  # assigned later; rebuild after
        objects.append(content)  # placeholder, replaced below
        _ = content_id

    # Rebuild page + content objects with correct numbering.
    # Layout: 1 catalog, 2 pages, 3..3+N-1 page dicts, 3+N font, then content streams.
    page_count = len(pages)
    font_num = 3 + page_count
    content_start = font_num + 1
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{' '.join(f'{3 + i} 0 R' for i in range(page_count))}] /Count {page_count} >>".encode(
            "ascii"
        ),
    ]
    streams: list[bytes] = []
    for i, page_lines in enumerate(pages):
        content_num = content_start + i
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_num} 0 R >> >> "
                f"/Contents {content_num} 0 R >>"
            ).encode("ascii")
        )
        streams.append(_page_stream(page_lines))
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    objects.extend(streams)

    dest.parent.mkdir(parents=True, exist_ok=True)
    _write_pdf(dest, objects, title=title)
    return dest


def _page_stream(lines: list[str]) -> bytes:
    cmds = ["BT", "/F1 10 Tf", "14 TL", "48 760 Td"]
    for index, line in enumerate(lines):
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if index:
            cmds.append("T*")
        cmds.append(f"({safe}) Tj")
    cmds.append("ET")
    body = "\n".join(cmds).encode("latin-1", errors="replace")
    return f"<< /Length {len(body)} >>\nstream\n".encode("ascii") + body + b"\nendstream"


def _write_pdf(dest: Path, objects: list[bytes], *, title: str) -> None:
    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    info = f"<< /Title ({_pdf_escape(title)}) /Creator (Film Lab) >>".encode("latin-1", errors="replace")
    all_objects = objects + [info]
    info_num = len(all_objects)
    offsets = [0]
    buf = bytearray(header)
    for i, obj in enumerate(all_objects, start=1):
        offsets.append(len(buf))
        buf.extend(f"{i} 0 obj\n".encode("ascii"))
        buf.extend(obj)
        buf.extend(b"\nendobj\n")
    xref_at = len(buf)
    buf.extend(f"xref\n0 {len(all_objects) + 1}\n".encode("ascii"))
    buf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        buf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    buf.extend(
        (
            f"trailer << /Size {len(all_objects) + 1} /Root 1 0 R /Info {info_num} 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n"
        ).encode("ascii")
    )
    dest.write_bytes(bytes(buf))


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap(text: str, width: int) -> list[str]:
    out: list[str] = []
    for raw in text.split("\n"):
        if not raw:
            out.append("")
            continue
        line = raw
        while len(line) > width:
            cut = line.rfind(" ", 0, width)
            if cut < 1:
                cut = width
            out.append(line[:cut])
            line = line[cut:].lstrip()
        out.append(line)
    return out
