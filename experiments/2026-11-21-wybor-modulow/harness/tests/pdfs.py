"""Budowa małych PDF-ów testowych bez zewnętrznych narzędzi (ręczna struktura + PIL)."""

from __future__ import annotations

import io


def text_pdf(pages: list[str] | None = None, *, rotate: int = 0, size: tuple[int, int] = (300, 200)) -> bytes:
    """PDF z jednym wierszem Helvetica 20 pt na stronę, w punkcie (50, 100); opcjonalny /Rotate."""
    pages = pages if pages is not None else ["Hello World"]
    objs: list[bytes] = []
    n = len(pages)
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n))
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode())
    font_id = 3 + 2 * n
    for i, text in enumerate(pages):
        content_id = 4 + 2 * i
        rot = f" /Rotate {rotate}" if rotate else ""
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {size[0]} {size[1]}]{rot} /Contents {content_id} 0 R "
                    f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>".encode())
        stream = f"BT /F1 20 Tf 50 100 Td ({text}) Tj ET".encode()
        objs.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


def image_pdf(width: int = 600, height: int = 400, *, text: str | None = "SKAN TEST 123", dpi: int = 100,
              n_pages: int = 1) -> bytes:
    """PDF zawierający wyłącznie obraz rastrowy (bez warstwy tekstowej) — „skan”."""
    from PIL import Image, ImageDraw, ImageFont

    imgs = []
    for _ in range(n_pages):
        img = Image.new("RGB", (width, height), "white")
        if text:
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
            except OSError:
                font = ImageFont.load_default(48)
            ImageDraw.Draw(img).text((40, height // 3), text, fill="black", font=font)
        imgs.append(img)
    buf = io.BytesIO()
    imgs[0].save(buf, "PDF", resolution=dpi, save_all=True, append_images=imgs[1:])
    return buf.getvalue()
