# E19: normalizatory kontra referencje

Plan: normalizatory (daty, kwoty, NIP, rachunki, wielkość liter) kontra referencje, bez LLM i OCR. Skrypt: `../e19_normalizers.py` (jedno polecenie, ok. 2 s), surowe liczby: `wyniki.json`.
Kod pod testem: `apps/backend/odwolania2json/domain/normalize.py` (bez zmian). Zbiór rozwojowy, 147 dokumentów (49 spraw), zbioru kontrolnego nie użyto.

## Hipoteza

Normalizatory z backendu sprowadzają każdy zapis wartości do formy referencyjnej organizatora; suma kontrolna mogłaby służyć jako filtr kandydatów.

## Metoda

- **A. Dokumenty rzeczywiste.** Każdą niepustą wartość referencyjną (NIP, REGON, KRS, PESEL, rachunki, kwota, daty, BZP, TED, nazwy) odnaleziono w tekście PDF (pypdfium2) i przepuszczono przez normalizator z surowego zapisu. Daty i kwoty: wszystkie napisy w formacie daty/kwoty z dokumentu przez normalizator, a pytanie brzmi, czy wartość referencyjna należy do zbioru wyników.
- **B. Test obiegowy (syntetyczny).** 49 wariantów zapisu tych samych wartości (spacje, myślniki, prefiks `PL`, `1 234,50 zł`, `1.000,50`, daty skrócone, rzymskie miesiące, TED ze spacjami). To nie jest rozkład z prawdziwych dokumentów, tylko próba krawędzi.
- **C. Sumy kontrolne wartości referencyjnych** (NIP, REGON, IBAN mod 97, PESEL).

## Wynik

| Część | Wynik |
|---|---|
| A, NIP / KRS / REGON / rachunek | 154/154, 141/141, 101/101, 98/98 zgodne po normalizacji (w dokumentach wartości są zapisane ciągłymi cyframi lub grupami po 4) |
| A, daty | 133/133 wartości referencyjnych należy do zbioru znormalizowanych dat dokumentu (1002 napisów; 66 „niesparsowanych” to fałszywe trafienia mojego wyrażenia na fragmentach numerów, nie błąd normalizatora) |
| A, kwota / BZP / TED / PESEL | 49/49, 38/38, 39/39, 1/1 |
| A, nazwy | 154/154 nazw referencyjnych występuje w tekście dosłownie (z uwzględnieniem wielkości liter) |
| B, rachunek | 7/7 |
| B, NIP | **5/8: porażki dla zapisu z myślnikami lub spacjami między cyframi** (`999-928-40-65`, `999 928 40 65`) |
| B, REGON, KRS | REGON `999 642 785` i KRS `9999 405 188` → `None` |
| B, kwota | 10/12: **`1.000,50` i `1,000.50` dają 1.0** (cicha wartość błędna, nie `None`) |
| B, data | 10/14: porażki: rok dwucyfrowy, miesiąc rzymski, `2026/04/01`, miesiąc słowny po „pierwszego” |
| B, TED | 4/5: `2026/S 224 - 999211` → `None` |
| C, poprawna suma kontrolna w referencjach | NIP 98/154 (64%), REGON 71/101 (70%), IBAN 33/98 (34%), PESEL 1/1 |

## Jak to działa i dlaczego tak wyszło

Dane organizatora są szablonowe i syntetyczne: identyfikatory zapisano ciągle albo grupami po 4 (rachunek), więc część A jest łatwa i nie rozróżnia niczego; 100% zgodności mówi o danych, nie o odporności normalizatorów. Część B pokazuje luki: `_blok_cyfr` wymaga ciągłego bloku cyfr, więc NIP/REGON/KRS ze spacjami lub myślnikami nie przechodzą (rachunek ma osobną ścieżkę usuwającą spacje, stąd 7/7). `normalize_amount` usuwa spacje i bierze pierwszy `\d+[.,]\d+`, więc przy separatorze tysięcy będącym przecinkiem lub kropką zwraca część całkowitą przed separatorem.

Dane referencyjne mają losowe cyfry kontrolne: **tylko 64% NIP, 70% REGON i 34% IBAN ma poprawną sumę**. Użycie sumy jako twardego filtra odrzuciłoby 36% prawdziwych NIP i 66% prawdziwych rachunków z referencji. Zbiór testowy organizatora prawdopodobnie ma ten sam charakter (zakładamy, nie wiemy), więc suma może być co najwyżej sygnałem rankingowym (tak już robi `checksum_valid`).

## Ograniczenia

Część A jest bliska tautologii (wartość znaleziona po cyfrach, potem normalizowana). Część B to 49 przypadków ułożonych przeze mnie, nie próba losowa. Nie testowano tekstu z OCR (to E08) ani LLM.

## Wniosek decyzyjny

Kryterium z planu („normalizatory zgodne z referencjami”) jest spełnione na danych rozwojowych (A: 100%). Do naprawy w produkcji przed użyciem na danych z OCR lub z innych źródeł: (1) NIP/REGON/KRS ze spacjami i myślnikami, (2) kwoty z separatorem tysięcy `.`/`,` (cicha błędna wartość jest groźniejsza niż `None`), (3) daty skrócone i `RRRR/MM/DD`, (4) TED ze spacjami wokół myślnika. Sumy kontrolnej nie używać jako filtra twardego. Pewność: wysoka co do luk (powtarzalny test), niska co do rozkładu zapisów w zbiorze testowym organizatora.

## Uwaga o czasie

Czasy wywołań LLM i przebiegów zebrano pod obciążeniem maszyny i współdzielonym kluczem (429, ponowienia): **niewiążące**, nie do decyzji. Miary jakości od obciążenia nie zależą.
