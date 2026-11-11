"""Minimal PNG writer so vision fixtures need no dependency.

A PNG is a signature plus length-tagged chunks with a CRC. Filter type 0 means
"the row is the pixels", and zlib does the compression, so the whole encoder is
forty lines of standard library.
"""

from __future__ import annotations

import struct
import zlib

Color = tuple[int, int, int]
Rows = list[list[Color]]


def _chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def write_png(rows: Rows) -> bytes:
    """Encode a list of rows of RGB triples as an 8-bit truecolour PNG."""

    height = len(rows)
    width = len(rows[0]) if height else 0
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for red, green, blue in row:
            raw.extend((red, green, blue))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )


def canvas(width: int, height: int, color: Color = (255, 255, 255)) -> Rows:
    return [[color for _ in range(width)] for _ in range(height)]


def fill_rect(rows: Rows, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
    height = len(rows)
    width = len(rows[0]) if height else 0
    for y in range(max(0, y0), min(height, y1)):
        row = rows[y]
        for x in range(max(0, x0), min(width, x1)):
            row[x] = color


def fill_circle(rows: Rows, cx: int, cy: int, radius: int, color: Color) -> None:
    height = len(rows)
    width = len(rows[0]) if height else 0
    squared = radius * radius
    for y in range(max(0, cy - radius), min(height, cy + radius + 1)):
        row = rows[y]
        dy = y - cy
        for x in range(max(0, cx - radius), min(width, cx + radius + 1)):
            dx = x - cx
            if dx * dx + dy * dy <= squared:
                row[x] = color
