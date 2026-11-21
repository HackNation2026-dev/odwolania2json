---
wersja: 0.1.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# ADR-001 — stos i granice implementacji

Status: proponowana. Data: 2026-11-21.

Kontekst: zespół preferuje Rust, Python, TypeScript i Docker. Zadania mają różne warunki użycia modeli i języków.

Decyzja proponowana: zastosować podział opisany w [architekturze](../04-architektura/README.md). Priorytetem jest zgodność z wymaganiami i pełny scenariusz, a nie liczba języków.

Alternatywa: wyłącznie Python dla silnika i API, TypeScript dla opcjonalnego GUI. Mniejszy koszt integracji, mniejszy udział preferowanego Rusta.

Konsekwencje: wspólny kontrakt między komponentami, test samodzielnego startu i kontrola licencji. Wybór modelu wymaga pomiaru oraz potwierdzenia warunków organizatora. Dokument nie oznacza, że aplikacja, model i dostawca już istnieją.
