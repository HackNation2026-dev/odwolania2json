---
wersja: 0.1.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Zasady wersjonowania

Dokumentacja i materiały są śledzone w Git. Pierwsze wydanie: `v0.1.0`.

1. Zapisz źródło, jego wersję lub rewizję i datę pozyskania.
2. Zachowaj oryginalne pliki. Przy nowej wersji źródła udokumentuj zmianę i poprzedni skrót Git.
3. Zaktualizuj wymagania i rejestr rozbieżności. Komunikat mentora zapisz z datą i kanałem.
4. Przelicz manifest materiałów: `python3 scripts/material_manifest.py`.
5. Uruchom `python3 scripts/verify_docs.py`.
6. Zmień `VERSION`, metadane edytowanych dokumentów i `CHANGELOG.md`. Utwórz commit; tag oznacza spójne wydanie.

Wersja poprawkowa: korekta opisu bez zmiany wymagań. Wersja mniejsza: nowe materiały lub wymagania. Wersja główna: zmiana kontraktu niezgodna z poprzednią implementacją.

Wersja dokumentacji zespołu nie jest wersją FAQ ani rewizją materiałów organizatora. Te wartości zapisuje się osobno.
