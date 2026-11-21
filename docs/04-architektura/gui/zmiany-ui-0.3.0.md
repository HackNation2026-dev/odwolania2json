---
wersja: 0.3.0
aktualizacja: 2026-11-21
status: raport zmian projektu UI; nie potwierdzenie implementacji
---

# Zmiany projektu UI 0.3.0

Zakres zlecenia B 0.6.0: wyłącznie [projekt-ui.md](projekt-ui.md) i ten raport. Bez kodu, zmian stosu i materiałów organizatora. Podstawa: [ocena Codex](ocena-ui-vs-kryteria.txt) pkt 6.1–6.9, [Fable](../../07-decyzje/konsultacja-ocena-calosci-2026-11-21/fable-odpowiedz.txt) §4 i §7 oraz [ADR-002](../../07-decyzje/ADR-002-decyzje-po-recenzji.md), w tym shim OCR i ETL/ELT.

| Zmiana | Miejsce w projekcie |
|---|---|
| Dwa warianty eksportu przy brakach: ścisła blokada albo świadomy eksport z `null` i ostrzeżeniem o niezgodności; osobno warianty braku pliku / zastępczego `{}` przy awarii. Bez rozstrzygania za użytkownika. | §3.3.5a, §4.7, F61 |
| Gotowość zależna od backendu: docelowy OCR, „OCR niedostępny”, „OCR tymczasowy (shim)”; brak klucza, 401/403, limit, brak sieci i endpointu. | §3.1.1, F56–58 |
| Karta wszystkich modeli i ról z S01/S03: największy model, parametry, licencje i wagi, kraj firmy i serwera, dostawca OCR i shim, rewizja kontraktu. | §3.1.2, F56 |
| Pokaz dodania klasy i pola przez YAML poza GUI: przeładowanie, rzeczywista analiza PDF, formularz, JSON i dowody. Pełny edytor pozostaje później. | §4.6.1, F59 |
| Pobranie dowodów w P0, osobno od ocenianego JSON; strona/cytat, źródło, metoda, braki i pokrycie stron. | §3.3.10–12, F60 |
| Pełny scenariusz jury, 10 kroków z oceny, z trzema klasami, obcym PDF, skanem, mieszanym dokumentem, awarią i rozbudową YAML. | §4.8 |
| Odbiór z czystej instalacji pip: osobne projektowane komendy CLI/GUI, zasoby lokalne, worker PDF, fonty, bez CDN, odświeżenie S03, ponawianie i próba pamięci. | §8.1.1 |
| Ujednolicone oznaczenia: zmiana klasy i edycja list dopiero E1, lista sprawdzonych stron już w P0; limit z backendu, rewizja kontraktu i informacje techniczne z S03. | §3.1.2, §3.3.2, §3.3.5 |

P0: **desktop 1440×900, PL, motyw jasny, S01–S03**. Cztery grupy stanów: w toku, pełny lub częściowy, obcy, błąd techniczny; niejednoznaczny i wiele dokumentów jako proste banery. Dowód to strona + cytat. W zakresie są pobranie JSON i dowodów, karta modeli, gotowość OCR oraz pokaz rozbudowy YAML. Klawiatura i fokus pozostają w P0.

Minimum do makiet: **18 ramek P0**, wszystkie J/PL, 1440×900: F01, F02, F05, F06, F08, F10, F13, F14, F40, F41, F51, F52, F56–61. Cały katalog ma **62 ramki F00–F61**. F59 i F61 są pojedynczymi arkuszami przebiegu/porównania. Zachowano opis pozostałych funkcji: E1 obejmuje EN, ciemny/systemowy motyw, telefon/tablet, geometrię, wiele obrysów, diagnozę regionów i korekty; E2 konfigurację w GUI i paczki; E3 role, logowanie, uprawnienia i audyt.

Otwarte pozostają: wybór wariantu eksportu przez użytkownika i odpowiedzi mentora U-Q12–U-Q15, biblioteki UI/PDF, model/API z potwierdzoną licencją i lokalizacją, dostawca shima/docelowego OCR, kanał klucza i budżet API, limity oraz retencja. Przeładowanie YAML może w P0 oznaczać restart; aktywacja bez restartu wymaga decyzji. Pełna lista w §10 projektu.

Status implementacji: projekt nie jest działającym GUI. W przeglądanym repo brak pakietu aplikacji i `requirements.txt`; komendy w §8.1.1 są wymaganiem do wdrożenia i odbioru, nie wynikiem udanego uruchomienia. Zawężenie P0 nie oznacza potwierdzonej realizacji w 24 h.

Weryfikacja dokumentacji: `python3 scripts/verify_docs.py` zakończone kodem 0. Kontrola dotyczy integralności źródeł i odnośników, nie działania aplikacji ani odbioru jury.
