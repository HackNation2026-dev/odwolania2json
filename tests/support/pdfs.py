"""Małe PDF-y budowane w teście bez zewnętrznych narzędzi (ręczna struktura + PIL).

Fabryka pokrywa przypadki czytnika: wiele linii, `/Rotate`, tekst niewidoczny
(tryb 3, biały, 1 pt, poza MediaBox), strona-obraz i PDF zaszyfrowany hasłem.
"""

from __future__ import annotations

import hashlib
import io
import struct
from dataclasses import dataclass

__all__ = ["Run", "build_pdf", "encrypted_pdf", "image_pdf", "text_pdf"]

_PAD = bytes.fromhex("28bf4e5e4e758a4164004e56fffa01082e2e00b6d0683e802f0ca9fe6453697a")


@dataclass(frozen=True)
class Run:
    """Jeden wiersz tekstu Helvetica na stronie (współrzędne użytkownika PDF)."""

    text: str
    x: float = 50.0
    y: float = 100.0
    size: float = 20.0
    color: tuple[float, float, float] | None = None
    render_mode: int | None = None
    # Krój 1 pt powiększony macierzą tekstu do `size`: częsty zapis w prawdziwych PDF-ach.
    scaled_unit_font: bool = False


def _content(runs: list[Run]) -> bytes:
    parts: list[str] = []
    for run in runs:
        ops = ["q", "BT", "/F1 1 Tf" if run.scaled_unit_font else f"/F1 {run.size:g} Tf"]
        if run.color is not None:
            ops.append("{:g} {:g} {:g} rg".format(*run.color))
        if run.render_mode is not None:
            ops.append(f"{run.render_mode} Tr")
        if run.scaled_unit_font:
            ops.append(f"{run.size:g} 0 0 {run.size:g} {run.x:g} {run.y:g} Tm ({run.text}) Tj ET Q")
        else:
            ops.append(f"{run.x:g} {run.y:g} Td ({run.text}) Tj ET Q")
        parts.append(" ".join(ops))
    return "\n".join(parts).encode("latin-1")


def _assemble(objects: list[bytes], trailer_extra: str = "") -> bytes:
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, 1):
        offsets.append(out.tell())
        out.write(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets:
        out.write(f"{offset:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R{trailer_extra} >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode()
    )
    return out.getvalue()


def _page_objects(
    pages: list[list[Run]], rotate: int, size: tuple[int, int]
) -> tuple[list[bytes], int]:
    count = len(pages)
    kids = " ".join(f"{3 + 2 * index} 0 R" for index in range(count))
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {count} >>".encode(),
    ]
    font_id = 3 + 2 * count
    for index, runs in enumerate(pages):
        rotation = f" /Rotate {rotate}" if rotate else ""
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {size[0]} {size[1]}]{rotation} "
            f"/Contents {4 + 2 * index} 0 R "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>".encode()
        )
        stream = _content(runs)
        objects.append(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    return objects, font_id


def build_pdf(
    pages: list[list[Run]], *, rotate: int = 0, size: tuple[int, int] = (300, 200)
) -> bytes:
    """PDF o podanych stronach; każda strona to lista wierszy tekstu."""
    objects, _ = _page_objects(pages, rotate, size)
    return _assemble(objects)


def text_pdf(
    pages: list[str] | None = None, *, rotate: int = 0, size: tuple[int, int] = (300, 200)
) -> bytes:
    """PDF z jednym wierszem 20 pt na stronę w punkcie (50, 100)."""
    texts = pages if pages is not None else ["Hello World"]
    return build_pdf([[Run(text)] for text in texts], rotate=rotate, size=size)


def image_pdf(
    width: int = 600, height: int = 400, *, text: str | None = "SKAN TEST 123", pages: int = 1
) -> bytes:
    """PDF zawierający wyłącznie obraz rastrowy (bez warstwy tekstu): „skan”."""
    from PIL import Image, ImageDraw

    images = []
    for _ in range(pages):
        image = Image.new("RGB", (width, height), "white")
        if text:
            ImageDraw.Draw(image).text((40, height // 3), text, fill="black")
        images.append(image)
    buffer = io.BytesIO()
    images[0].save(buffer, "PDF", resolution=100, save_all=True, append_images=images[1:])
    return buffer.getvalue()


def _rc4(key: bytes, data: bytes) -> bytes:
    state = list(range(256))
    j = 0
    for i in range(256):
        j = (j + state[i] + key[i % len(key)]) % 256
        state[i], state[j] = state[j], state[i]
    i = j = 0
    out = bytearray()
    for byte in data:
        i = (i + 1) % 256
        j = (j + state[i]) % 256
        state[i], state[j] = state[j], state[i]
        out.append(byte ^ state[(state[i] + state[j]) % 256])
    return bytes(out)


def encrypted_pdf(password: str = "tajne-haslo") -> bytes:  # noqa: S107 — hasło testowe
    """PDF ze standardowym szyfrowaniem RC4-40 (R2) i niepustym hasłem użytkownika.

    Strumienie nie są zaszyfrowane: czytnik ma odrzucić plik już na haśle.
    """
    padded = (password.encode("latin-1") + _PAD)[:32]
    permissions = struct.pack("<i", -4)
    file_id = hashlib.md5(b"odwolania2json-test", usedforsecurity=False).digest()
    owner_key = hashlib.md5(padded, usedforsecurity=False).digest()[:5]
    owner = _rc4(owner_key, padded)
    key = hashlib.md5(padded + owner + permissions + file_id, usedforsecurity=False).digest()[:5]
    user = _rc4(key, _PAD)
    objects, font_id = _page_objects([[Run("Secret")]], 0, (300, 200))
    objects.append(
        f"<< /Filter /Standard /V 1 /R 2 /O <{owner.hex()}> /U <{user.hex()}> /P -4 >>".encode()
    )
    extra = f" /Encrypt {font_id + 1} 0 R /ID [<{file_id.hex()}> <{file_id.hex()}>]"
    return _assemble(objects, extra)
