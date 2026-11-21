"""Scala surowe wyniki modeli z dokumenty/<id>.json i liczy ocenę automatyczną.

Ocena automatyczna (przybliżona, do weryfikacji przez człowieka w przeglądarce):
- klasa_trafiona: klasa modelu == oczekiwana (obcy ↔ inny); niepewne = False.
- podobieństwo transkrypcji: rapidfuzz partial_ratio(transkrypcja, tekst referencyjny strony) / 100,
  gdzie tekst referencyjny to warstwa tekstu strony, a dla syntetycznych skanów warstwa tekstu strony źródłowej.
- wstrzyknięte problemy: wykryte, jeśli model podał ten kod (strona lub dokument) albo równoważny sygnał
  (skan: typ strony skan/mieszana; obrot: obrot_stopnie != 0; pusta_strona: typ pusta).
Wynik: dokumenty zaktualizowane + podsumowanie.json + podsumowanie.md w katalogu przebiegu.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from rapidfuzz import fuzz

from wspolne import REPO, RUN, normalizuj, tekst_strony, wczytaj_json, zapisz_json

MODELE = ["codex", "claude", "minimax"]


def tekst_referencyjny(dok: dict, synt: dict) -> dict[int, str]:
    ref = {s["nr"]: s["probka_tekstu"] for s in dok["strony"]}
    if dok["id"] in synt:
        for nr, z in enumerate(synt[dok["id"]]["strony_zrodlowe"], 1):
            if z and len(ref.get(nr, "")) < 50:
                ref[nr] = normalizuj(tekst_strony(REPO / z["pdf"], z["strona"]))[:400]
    return ref


def wykryte(kod: str, strona: int | None, wynik: dict) -> bool:
    strony = {s["nr"]: s for s in wynik["strony"]}
    docel = [strony[strona]] if strona and strona in strony else list(strony.values())
    kody = {p["kod"] for p in wynik["problemy_dokumentu"]} | {p["kod"] for s in docel for p in s["problemy"]}
    if kod in kody:
        return True
    if kod == "skan":
        return any(s["typ"] in ("skan", "mieszana") for s in docel)
    if kod == "obrot":
        return any(s["obrot_stopnie"] != 0 for s in docel)
    if kod == "pusta_strona":
        return any(s["typ"] == "pusta" for s in docel)
    if kod == "dokument_mieszany":
        return {"tekst", "skan"} <= {s["typ"] for s in strony.values()}
    return False


def main() -> None:
    manifest = wczytaj_json(RUN / "manifest.json")
    synt_plik = RUN / "syntetyczne" / "syntetyczne.json"
    synt = {d["id"]: d for d in wczytaj_json(synt_plik)["dokumenty"]} if synt_plik.exists() else {}
    stat = {m: defaultdict(list) for m in MODELE}
    wstrz = {m: defaultdict(lambda: [0, 0]) for m in MODELE}
    kody_modeli = {m: Counter() for m in MODELE}
    for wpis in manifest["dokumenty"]:
        sciezka = RUN / wpis["plik_wynikow"]
        dok = wczytaj_json(sciezka)
        ref = tekst_referencyjny(dok, synt)
        for m in MODELE:
            surowy = RUN / "_surowe" / m / f"{dok['id']}.json"
            if not surowy.exists():
                if wpis["przeslany_do_modeli"]:
                    dok["modele"][m] = {"status": "pominiety", "czas_s": None, "blad": None, "strony_przeslane": [], "wynik": None, "ocena_auto": None}
                continue
            r = wczytaj_json(surowy)
            ocena = None
            if r["status"] == "ok":
                w = r["wynik"]
                oczek = {"obcy": "inny"}.get(dok["klasa_oczekiwana"], dok["klasa_oczekiwana"])
                trafiona = w["klasa"] == oczek
                pod = []
                for s in w["strony"]:
                    t = normalizuj(s["transkrypcja_poczatku"]).lower()
                    rt = ref.get(s["nr"], "").lower()
                    pod.append({"nr": s["nr"], "podobienstwo": round(fuzz.partial_ratio(t, rt) / 100, 3) if t and len(rt) >= 50 else None})
                wyk = [x["kod"] for x in dok["wstrzykniete"] if wykryte(x["kod"], x["strona"], w)]
                pom = [x["kod"] for x in dok["wstrzykniete"] if x["kod"] not in wyk]
                ocena = {"klasa_trafiona": trafiona, "podobienstwo_transkrypcji": pod, "wykryte_wstrzykniete": wyk, "pominiete_wstrzykniete": pom}
                stat[m]["klasa"].append(trafiona)
                stat[m][f"klasa_{dok['zrodlo']}"].append(trafiona)
                stat[m]["podobienstwo"] += [p["podobienstwo"] for p in pod if p["podobienstwo"] is not None]
                for x in dok["wstrzykniete"]:
                    wstrz[m][x["kod"]][1] += 1
                    wstrz[m][x["kod"]][0] += x["kod"] in wyk
                for p in w["problemy_dokumentu"] + [p for s in w["strony"] for p in s["problemy"]]:
                    kody_modeli[m][p["kod"]] += 1
            stat[m]["status"].append(r["status"])
            stat[m]["czas"].append(r.get("czas_s") or 0)
            dok["modele"][m] = {"status": r["status"], "czas_s": r.get("czas_s"), "blad": r.get("blad"),
                                "strony_przeslane": r.get("strony_przeslane", []), "wynik": r.get("wynik"), "ocena_auto": ocena}
        zapisz_json(sciezka, dok)

    pods = {}
    for m in MODELE:
        s = stat[m]
        sr = lambda xs: round(sum(xs) / len(xs), 3) if xs else None  # noqa: E731
        pods[m] = {"wywolan": len(s["status"]), "ok": s["status"].count("ok"), "sredni_czas_s": sr(s["czas"]),
                   "trafnosc_klasy": sr(s["klasa"]), "trafnosc_klasy_wg_zrodla": {z[6:]: sr(v) for z, v in s.items() if z.startswith("klasa_")},
                   "srednie_podobienstwo_transkrypcji": sr(s["podobienstwo"]),
                   "wstrzykniete_wykryte": {k: f"{a}/{b}" for k, (a, b) in sorted(wstrz[m].items())},
                   "kody_zgloszone": dict(kody_modeli[m].most_common())}
    zapisz_json(RUN / "podsumowanie.json", pods)
    wiersze = ["| Miara | " + " | ".join(MODELE) + " |", "|---|" + "---|" * len(MODELE)]
    def w(nazwa, f):
        wiersze.append(f"| {nazwa} | " + " | ".join(str(f(pods[m])) for m in MODELE) + " |")
    w("Poprawne odpowiedzi (format)", lambda p: f"{p['ok']}/{p['wywolan']}")
    w("Średni czas [s]", lambda p: p["sredni_czas_s"])
    w("Trafność klasy", lambda p: p["trafnosc_klasy"])
    for z in ("pozytywny", "negatywny", "szablon", "syntetyczny"):
        w(f"Trafność klasy: {z}", lambda p, z=z: p["trafnosc_klasy_wg_zrodla"].get(z))
    w("Średnie podobieństwo transkrypcji", lambda p: p["srednie_podobienstwo_transkrypcji"])
    for kod in sorted({k for m in MODELE for k in pods[m]["wstrzykniete_wykryte"]}):
        w(f"Wykryte wstrzyknięte: {kod}", lambda p, kod=kod: p["wstrzykniete_wykryte"].get(kod, "-"))
    (RUN / "podsumowanie.md").write_text("\n".join(wiersze) + "\n", encoding="utf-8")
    print("\n".join(wiersze))


if __name__ == "__main__":
    main()
