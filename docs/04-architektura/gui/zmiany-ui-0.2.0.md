---
wersja: 0.2.0
aktualizacja: 2026-11-21
status: zestawienie zmian projektu UI, bez implementacji
---

# Zmiany projektu UI 0.2.0

Aktualizacja [projektu UI](projekt-ui.md) względem 0.1.0, na podstawie [recenzji](recenzja-codex-2026-11-21.md), ADR-002 i zlecenia użytkownika 0.5.0. Zachowano 10 sekcji merytorycznych oraz sekcję 0 z oznaczeniami źródeł. Zmieniono tylko projekt i to zestawienie. Oryginały organizatora, kod, VERSION i CHANGELOG nie należą do zakresu tej aktualizacji.

## Uwagi recenzji

| Punkt | Zmiana | Miejsce w projekcie |
|---|---|---|
| 1, krytyczny: ochrona danych | Jedna macierz kanałów, backendowa autoryzacja, bezpieczne pochodne PDF zamiast nakładki; chronione także cytaty, schowek, ZIP, historia i audyt. Demo bez kont, tylko syntetyczne dane i izolacja sesji. | §1.1, §1.4, §3.3.9–13; F12, F35 |
| 2: awaria konfiguracji | Brak poprawnego zestawu blokuje analizę. Częściowe wczytanie nie aktywuje zestawu; poprzedni kompletny pozostaje jawnie wskazany. Nigdy `{}` jako skutek awarii. | §3.6, §4.6; F46–48, F55 |
| 3: zapis i eksport szkicu | „Zastosuj” zmienia szkic, „Zapisz korektę” tworzy trwałą wersję. Zapisywanie, błąd i ponowienie, konflikt zapisu, kontrola szkicu przed eksportem, kopiowaniem, zatwierdzeniem i wyjściem. | §3.3.7, §3.3.12, §4.3; F11, F33–34, F53 |
| 4: kontrast | Ciemny `evidence-border` zmieniony na #8A5300. Na białej stronie 6,33:1 w obu motywach zamiast 1,68:1. Przeliczone pary i jawne tła, wzór WCAG, kompozycja wypełnienia. | §7.1; F09 |
| 5: realne MVP i pip | Jeden zakres P0; foldery, geometria, korekty i zatwierdzanie po MVP. PL/EN, oba motywy, dostępność i tekst strony pozostają P0. Gotowe statyczne zasoby w pakiecie Python, bez Node u jury. | §2.1, §8 |
| 6: generatywne odpowiedzi | Usunięto projekt asystenta, komponentów, integracji i jego ramkę. OpenUI poza MVP i pełną wersją. Pozostał krótki punkt rozszerzenia; bez ocen prawnych na podstawie nazwisk. | §6; dawne F23 zastąpione diagnozą |
| 7: partie i kolizje | Tożsamość partii, pliki w korzeniu i głębokich katalogach, mapowanie ścieżek, kolizje bez zmiany nazw i nadpisywania, jawny częściowy eksport. | §3.4, §4.7; F28, F42, F54 |
| 8: brakujące ramki | S04, S11, S13, S14, niezapisany szkic, błąd zapisu, odmowa danych i pełny cykl aktywacji YAML. Macierz wariantów, pełny widok EN, reflow 320 px. Viewport oddzielony od wysokości treści. | §9; F28–37, F43–50, F53, F55 |
| 9: semantyka pól | Pomoc o pierwszym zarzucie, BZP także z `/##`, Tak/Nie jako 1/0, pełne ścieżki pól zamawiającego i identyfikatory jako tekst. | §3.3.6 |
| 10: klawiatura i telefon | Upload jako kontener z osobnymi kontrolkami, semantyka tabel/list, natywne strzałki w edytorach, skróty zgodne z zakładkami, powrót fokusu i scrolla, obsługa klawiatury ekranowej i dolnego paska. | §3.1, §3.3.16, §7.4 |
| 11: drobne niespójności | Stały baner demo, nazwy klas z konfiguracji, jawnie maskowany podgląd różny od ocenianego pliku, filtr F08 „Wszystkie pola” spójny ze stanem pełnym. | §1.1, §3.3.9, §3.3.14; F03, F08, F13 |

## Nowe ustalenia

1. Grupa może mieć wiele obszarów na różnych stronach; wspólne ID i kolor, przy kolizji oznaczenia pól. Pomiar 446/622 opisany jako wynik heurystyki lokalizacji referencji, bez twierdzeń o F1 (§3.3.4b; F38–39).
2. Diagnoza dokumentu, strony i regionu niezależna od klasy biznesowej; sześć źródeł tekstu, orientacja, jakość, pewność, sygnały, OCR i kody (§3.3.4a; F23).
3. Sześć stanów wyniku rozdzielonych od postępu, flagi przeglądu i zatwierdzenia. Niejednoznaczny i wiele dokumentów mają osobne komunikaty i blokadę nieuzgodnionego eksportu (§3.2.1; F40–41).
4. Pięć powodów braku poza JSON: brak, nie dotyczy, nieczytelne, sprzeczne, nieprzetworzone. W JSON `null`; konflikt kontraktu jawnie blokuje eksport (§3.3.5; F51).
5. Kanoniczne kody przy dokumencie i polu oraz filtr listy; brak kodu nie dowodzi braku problemów (§3.2; F05–07, F28).
6. Każdy dokument i segment analizowany niezależnie, bez przenoszenia wartości między dokumentami (§3.2, §4.7).
7. Dowód: oryginalna strona, cytat, lista obrysów, źródło tekst PDF/OCR, reguła i dowody przesłanek dla wyliczeń. Bez geometrii komunikat o przybliżeniu, bez automatycznego pierwszego trafienia (§3.3, §5; F08–09, F19, F52).

## Wielkość i zakres

Projekt obejmuje **14 stron aplikacji i 56 ramek F00–F55**. MVP obejmuje 5 stron (S01, S02, S03, S13, S14): wgranie PDF, lista statusów, przegląd PDF/dane/JSON z dowodem strona + fragment i pobranie wyniku silnika. Pozostałe funkcje przypisano do E1–E3. Ramki są opisami do makiet, nie wykonanymi ekranami.

Pozostałe pytania są w §10 projektu: biblioteka i przeglądarka PDF, kontrakt geometrii/diagnozy, wynik dla wielu dokumentów, zgodność `null`, model/licencja/hosting, SSO i zasięg spraw, akceptacja propozycji procesu, limity/retencja, przeładowanie YAML, edycja mobilna i sygnatura sprawy. Usunięto pytania o rozstrzygnięte MVP bez logowania, obecność OpenUI i ochronę PDF samą nakładką.

## Weryfikacja

`python3 scripts/verify_docs.py`: **OK: 440 materiałów, 45 dokumentów, odnośniki lokalne i integralność źródeł.** Sprawdzono również wzór i wartości kontrastów, zgodność liczby kolumn tabel, 10 sekcji oraz kompletność unikatowych identyfikatorów 56 ramek. Kontrola angielskich tekstów interfejsu objęła interpunkcję.

Reflow 320 px i warianty macierzy mają kryteria odbioru oraz reprezentatywne opisy ramek. Brak kodu i makiet w tym zleceniu oznacza, że nie wykonano testu renderowania ani audytu WCAG działającego UI.
