---
wersja: 0.6.0
aktualizacja: 2026-11-21
status: zlecenie dla Codex — projekt UI 0.3.0
---

# Zlecenie B (Codex): projekt UI 0.3.0

Repo `odwolania2json`. Po polsku. Zmieniasz **wyłącznie** pliki w `docs/04-architektura/gui/`: `projekt-ui.md` (→ 0.3.0) i nowy `zmiany-ui-0.3.0.md`. Nie piszesz kodu. Na końcu `python3 scripts/verify_docs.py` musi przejść (równolegle inne zlecenie zmienia pliki poza `gui/` — nie ruszaj ich).

Przeczytaj: `projekt-ui.md` (0.2.0), `ocena-ui-vs-kryteria.txt` (Codex), `docs/07-decyzje/konsultacja-ocena-calosci-2026-11-21/fable-odpowiedz.txt` (sekcje 4 i 7), `docs/07-decyzje/ADR-002-decyzje-po-recenzji.md` (z uzupełnieniami: shim OCR, ETL).

Nanieś:

1. **Obowiązkowe** z `ocena-ui-vs-kryteria.txt` pkt 6.1–6.3: polityka eksportu przy brakach (opisz zachowanie UI dla obu wariantów, decyzja należy do użytkownika — nie rozstrzygaj); odbiór uruchomienia u jury (czysta instalacja pip, komendy CLI i serwera GUI, wszystkie zasoby lokalne, worker PDF, fonty, bez CDN, odświeżenie adresu S03); komunikaty zależne od rzeczywistej gotowości OCR i modelu (stan „OCR niedostępny”, „OCR tymczasowy (shim)”, brak klucza/401/limit/brak sieci).
2. **Punktowe** 6.4–6.7: pokaz dodania klasy i pola w MVP (zmiana YAML poza GUI + przeładowanie + analiza PDF + formularz + JSON); karta modeli w P0 dostępna z S01 i S03 (wszystkie modele i role, największy model, parametry, licencja, dostawca, kraj firmy i serwera, dostawca OCR i czy to shim); pełny scenariusz pokazu jury (10 kroków z oceny) jako nowa sekcja; pobranie dowodów w P0.
3. **Zawężenie P0** (Fable pkt 4): desktop 1440, PL, jeden motyw (jasny), S01–S03, stany: w toku / pełny lub częściowy / obcy / błąd techniczny, „niejednoznaczny” i „wiele dokumentów” jako baner, dowód = strona + cytat, pobranie JSON i dowodów, karta modeli, gotowość OCR. Pozostałe (EN, ciemny motyw, telefon/tablet, wiele obrysów, diagnoza regionów, role, audyt) przenieś do etapów E1–E3 — **nie usuwaj** ich opisu, oznacz etap.
4. Drobne 6.8–6.9 z oceny.
5. Zaktualizuj listę ramek: oznacz, które ramki należą do P0 (minimum do makiet), i dodaj ramki: karta modeli, stan OCR niedostępny / shim, scenariusz dodania klasy.

Raport: krótko — co zmieniono, zakres P0, liczba ramek P0, pozostałe pytania, wynik `verify_docs.py`.
