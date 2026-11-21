"""Tworzy syntetyczne „skany” i dokumenty mieszane z tekstowych PDF-ów organizatora.

Wynik: RUN/syntetyczne/*.pdf + RUN/syntetyczne/syntetyczne.json (znane, wstrzyknięte problemy).
Przypadki pozytywne organizatora nie zawierają skanów, a test ukryty je zawiera (mentor, 2026-11-21).
"""
from __future__ import annotations

import io
import json
import random
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pypdf import PdfReader, PdfWriter, Transformation

from wspolne import MAT, REPO, RUN, pdfinfo, uruchom, wczytaj_json, zapisz_json

LOS = random.Random(20261121)
OUT = RUN / "syntetyczne"
DPI_SKANU = 150


def renderuj(pdf: Path, nr: int, dpi: int = DPI_SKANU) -> Image.Image:
    with tempfile.TemporaryDirectory() as d:
        uruchom(["pdftoppm", "-f", str(nr), "-l", str(nr), "-r", str(dpi), "-png", "-singlefile", str(pdf), f"{d}/s"])
        return Image.open(f"{d}/s.png").convert("RGB")


def jak_skan(img: Image.Image, szum: float = 0.0, kat: float = 0.0, tlo: int = 255) -> Image.Image:
    if kat:
        img = img.rotate(kat, resample=Image.BICUBIC, expand=False, fillcolor=(tlo, tlo, tlo))
    a = np.asarray(img).astype(np.float32)
    if tlo < 255:
        a = a * (tlo / 255.0)
    if szum:
        a += np.random.default_rng(LOS.randint(0, 10**6)).normal(0, szum, a.shape)
        kropki = np.random.default_rng(LOS.randint(0, 10**6)).random(a.shape[:2]) < 0.0015
        a[kropki] = 30
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def jako_jpeg(img: Image.Image, jakosc: int) -> Image.Image:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=jakosc)
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


def zapisz_obrazy_pdf(obrazy: list[Image.Image], cel: Path, dpi: int = DPI_SKANU) -> None:
    obrazy[0].save(cel, "PDF", resolution=dpi, save_all=True, append_images=obrazy[1:])


def strona_pdf_z_obrazu(img: Image.Image, dpi: int = DPI_SKANU):
    buf = io.BytesIO()
    img.save(buf, "PDF", resolution=dpi)
    return PdfReader(io.BytesIO(buf.getvalue())).pages[0]


def pieczatka(img: Image.Image, srodek: tuple[int, int], tekst: str = "ZAPŁACONO") -> Image.Image:
    img = img.copy()
    warstwa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(warstwa)
    x, y = srodek
    d.ellipse([x - 230, y - 110, x + 230, y + 110], outline=(200, 30, 40, 170), width=10)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
    except OSError:
        font = ImageFont.load_default(64)
    d.text((x, y), tekst, fill=(200, 30, 40, 170), font=font, anchor="mm")
    d.line([x - 260, y + 160, x + 120, y + 130, x + 260, y + 190], fill=(20, 40, 160, 200), width=6)
    return Image.alpha_composite(img.convert("RGBA"), warstwa.rotate(-12, center=srodek)).convert("RGB")


def wybierz_sprawy() -> dict[str, str]:
    dane = MAT / "dane"
    sprawy = sorted(p.name for p in dane.glob("przyklad_*"))
    def strony(s, plik):
        return pdfinfo(dane / s / plik)["n"]
    krotka = next(s for s in sprawy if strony(s, "odwolanie.pdf") == 2)
    dluga = next(s for s in sprawy if strony(s, "odwolanie.pdf") >= 10)
    inne = [s for s in sprawy if s not in (krotka, dluga)]
    return {"A": krotka, "B": dluga, "C": inne[0]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    s = wybierz_sprawy()
    dane = MAT / "dane"
    P = lambda k, plik: dane / s[k] / plik  # noqa: E731
    opis = []

    def dodaj(id_, klasa, sprawa, wstrz, zrodla):
        opis.append({"id": id_, "plik": f"syntetyczne/{id_}.pdf", "klasa": klasa, "sprawa": sprawa,
                     "wstrzykniete": [{"kod": k, "strona": st, "opis": o} for k, st, o in wstrz],
                     "strony_zrodlowe": [None if z is None else {"pdf": str(z[0].relative_to(REPO)), "strona": z[1]} for z in zrodla]})

    # x01: pełnomocnictwo jako skan obrócony o 90°
    src = P("A", "pelnomocnictwo.pdf")
    zapisz_obrazy_pdf([jak_skan(renderuj(src, 1), szum=6).rotate(90, expand=True)], OUT / "x01_obrot90.pdf")
    dodaj("x01_obrot90", "pelnomocnictwo", s["A"], [("skan", 1, "cała strona jako obraz"), ("obrot", 1, "obrót o 90°")], [(src, 1)])

    # x02: przelew jako skan obrócony o 180°
    src = P("B", "potwierdzenie_przelewu.pdf")
    zapisz_obrazy_pdf([jak_skan(renderuj(src, 1), szum=6).rotate(180)], OUT / "x02_obrot180.pdf")
    dodaj("x02_obrot180", "przelew", s["B"], [("skan", 1, "cała strona jako obraz"), ("obrot", 1, "obrót o 180°")], [(src, 1)])

    # x03: odwołanie (2 strony) przekrzywione o 3°
    src = P("A", "odwolanie.pdf")
    zapisz_obrazy_pdf([jak_skan(renderuj(src, n), szum=5, kat=3.0) for n in (1, 2)], OUT / "x03_przekrzywienie.pdf")
    dodaj("x03_przekrzywienie", "odwolanie", s["A"], [("skan", None, "obie strony jako obraz"), ("przekrzywienie", None, "przekrzywienie 3°")], [(src, 1), (src, 2)])

    # x04: przelew w niskiej jakości (72 dpi, rozmycie, JPEG q25)
    src = P("C", "potwierdzenie_przelewu.pdf")
    img = renderuj(src, 1, dpi=72).filter(ImageFilter.GaussianBlur(0.9))
    zapisz_obrazy_pdf([jako_jpeg(jak_skan(img, szum=10), 25)], OUT / "x04_niska_jakosc.pdf", dpi=72)
    dodaj("x04_niska_jakosc", "przelew", s["C"], [("skan", 1, "obraz 72 dpi"), ("niska_jakosc", 1, "72 dpi, rozmycie, JPEG q25")], [(src, 1)])

    # x05: pełnomocnictwo jak ksero: szare tło, szum, przekrzywienie 1,5°
    src = P("C", "pelnomocnictwo.pdf")
    zapisz_obrazy_pdf([jak_skan(renderuj(src, 1), szum=18, kat=-1.5, tlo=215)], OUT / "x05_ksero.pdf")
    dodaj("x05_ksero", "pelnomocnictwo", s["C"], [("skan", 1, "obraz"), ("niska_jakosc", 1, "szare tło i szum jak z ksero"), ("przekrzywienie", 1, "-1,5°")], [(src, 1)])

    # x06: odwołanie: strona 1 tekst, strona 2 skan
    src = P("A", "odwolanie.pdf")
    w = PdfWriter()
    w.add_page(PdfReader(src).pages[0])
    w.add_page(strona_pdf_z_obrazu(jak_skan(renderuj(src, 2), szum=6)))
    w.write(OUT / "x06_mieszany.pdf")
    dodaj("x06_mieszany", "odwolanie", s["A"], [("dokument_mieszany", None, "strona 1 tekst, strona 2 skan"), ("skan", 2, "strona 2 jako obraz")], [(src, 1), (src, 2)])

    # x07: pełnomocnictwo i przelew w jednym pliku
    w = PdfWriter()
    for f in (P("A", "pelnomocnictwo.pdf"), P("A", "potwierdzenie_przelewu.pdf")):
        for pg in PdfReader(f).pages:
            w.add_page(pg)
    w.write(OUT / "x07_dwa_dokumenty.pdf")
    dodaj("x07_dwa_dokumenty", "pelnomocnictwo", s["A"], [("wiele_dokumentow", None, "pełnomocnictwo i potwierdzenie przelewu w jednym pliku")],
          [(P("A", "pelnomocnictwo.pdf"), 1), (P("A", "potwierdzenie_przelewu.pdf"), 1)])

    # x08: przelew jako skan z pieczątką i podpisem na środku
    src = P("A", "potwierdzenie_przelewu.pdf")
    img = jak_skan(renderuj(src, 1), szum=5)
    zapisz_obrazy_pdf([pieczatka(img, (img.width // 2, int(img.height * 0.35)))], OUT / "x08_pieczatka.pdf")
    dodaj("x08_pieczatka", "przelew", s["A"], [("skan", 1, "obraz"), ("pieczatka_podpis", 1, "czerwona pieczątka i podpis na treści")], [(src, 1)])

    # x09: pełnomocnictwo jako skan z uciętym prawym marginesem (18%)
    src = P("B", "pelnomocnictwo.pdf")
    img = jak_skan(renderuj(src, 1), szum=5)
    img = img.crop((0, 0, int(img.width * 0.82), img.height))
    zapisz_obrazy_pdf([img], OUT / "x09_uciety.pdf")
    dodaj("x09_uciety", "pelnomocnictwo", s["B"], [("skan", 1, "obraz"), ("uciety_tekst", 1, "ucięte 18% szerokości z prawej")], [(src, 1)])

    # x10: odwołanie z pustą stroną wstawioną jako strona 2
    src = P("A", "odwolanie.pdf")
    r = PdfReader(src)
    w = PdfWriter()
    w.add_page(r.pages[0])
    w.add_blank_page(width=float(r.pages[0].mediabox.width), height=float(r.pages[0].mediabox.height))
    w.add_page(r.pages[1])
    w.write(OUT / "x10_pusta_strona.pdf")
    dodaj("x10_pusta_strona", "odwolanie", s["A"], [("pusta_strona", 2, "wstawiona pusta strona")], [(src, 1), None, (src, 2)])

    # x11: długie odwołanie, 3 pierwsze strony; strona 2 jako skan obrócony o 90°
    src = P("B", "odwolanie.pdf")
    r = PdfReader(src)
    w = PdfWriter()
    w.add_page(r.pages[0])
    w.add_page(strona_pdf_z_obrazu(jak_skan(renderuj(src, 2), szum=6).rotate(90, expand=True)))
    w.add_page(r.pages[2])
    w.write(OUT / "x11_mieszany_obrot.pdf")
    dodaj("x11_mieszany_obrot", "odwolanie", s["B"], [("dokument_mieszany", None, "strony 1 i 3 tekst, 2 skan"), ("skan", 2, "obraz"), ("obrot", 2, "obrót o 90°")], [(src, 1), (src, 2), (src, 3)])

    # x12: tekstowy przelew z wklejonym obrazem pieczątki i podpisu (strona mieszana)
    src = P("C", "potwierdzenie_przelewu.pdf")
    w = PdfWriter(clone_from=src)
    strona = w.pages[0]
    wklejka = pieczatka(Image.new("RGB", (900, 520), (250, 250, 247)), (450, 230), "OPŁACONO")
    wk = strona_pdf_z_obrazu(jak_skan(wklejka, szum=8))
    W, H = float(strona.mediabox.width), float(strona.mediabox.height)
    skala = (W * 0.42) / float(wk.mediabox.width)
    strona.merge_transformed_page(wk, Transformation().scale(skala, skala).translate(W * 0.52, H * 0.40))
    w.write(OUT / "x12_strona_mieszana.pdf")
    dodaj("x12_strona_mieszana", "przelew", s["C"], [("strona_mieszana", 1, "tekst cyfrowy + wklejony obraz pieczątki i podpisu (nie zasłania tekstu)")], [(src, 1)])

    zapisz_json(OUT / "syntetyczne.json", {"sprawy_zrodlowe": s, "dokumenty": opis})
    print(f"Syntetyczne: {len(opis)} plików, sprawy {s}")


if __name__ == "__main__":
    main()
