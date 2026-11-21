---
wersja: 0.6.0
aktualizacja: 2026-11-21
status: wynik eksperymentu heurystycznego — zweryfikowana próba pięciu kart
---

# Karty 180 dokumentów — 2026-11-21

## Fakty z pomiaru

Przetworzono niezależnie 180 PDF-ów (po 60 na klasę). [Karty i podsumowanie](../../experiments/2026-11-21-przypadki-brzegowe/wyniki/2026-11-21-v1/karty/podsumowanie.json), [schemat](../../experiments/2026-11-21-przypadki-brzegowe/format/karta.schema.json), [narzędzia](../../experiments/2026-11-21-przypadki-brzegowe/narzedzia/karty.py). Każda karta została zwalidowana schematem draft 2020-12.

Nałożone aktualizacje referencji: p19_odwolanie, p23_odwolanie, p25_odwolanie, p44_odwolanie, p55_odwolanie. Pozostałe referencje pochodzą z migawki bazowej. Oryginały niezmienione. Po uruchomieniu inwentarza porównano zawartość `modele` we wszystkich 206 wcześniejszych plikach dokumentów: bez zmian.

Zlokalizowano 1784/1784 wartości wymagających lokalizacji (100.00%). Mianownik pomija null i wartości wyliczane; to pokrycie znanych referencji, nie F1 ekstraktora. Wszystkich pól: 2316.

| Dopasowanie | Liczba |
|---|---|
| dokladne | 1414 |
| inny_zapis | 370 |
| inna_forma_gramatyczna | 0 |
| wyliczana | 248 |
| nieznaleziona | 0 |
| null_w_referencji | 284 |

### Kody per klasa

Zliczane są dokumenty, nie liczba wystąpień kodu. Kandydaty układu i braku etykiet są przybliżeniami. Pełne definicje i źródła: [katalog kodów](katalog-kodow.md).

| Kod | Razem | Odwołanie | Pełnomocnictwo | Przelew |
|---|---|---|---|---|
| brak_etykiety_roli | 18 | 0 | 15 | 3 |
| etykieta_po_danych | 62 | 0 | 55 | 7 |
| etykieta_synonim | 94 | 60 | 34 | 0 |
| brak_etykiety_przy_wartosci | 180 | 60 | 60 | 60 |
| niewidoczna_tabela | 32 | 0 | 0 | 32 |
| uklad_wielokolumnowy | 78 | 14 | 26 | 38 |
| tabela | 0 | 0 | 0 | 0 |
| brak_informacji_wprost | 0 | 0 | 0 | 0 |
| wartosc_wyliczana | 120 | 60 | 60 | 0 |
| inny_zapis_wartosci | 120 | 60 | 0 | 60 |
| inna_forma_gramatyczna | 0 | 0 | 0 | 0 |
| wiele_wystapien | 162 | 60 | 42 | 60 |
| wartosc_w_kilku_liniach | 135 | 59 | 17 | 59 |
| dane_dalej_niz_3_strona | 21 | 21 | 0 | 0 |
| konsorcjum | 6 | 6 | 0 | 0 |
| wielu_zamawiajacych | 3 | 3 | 0 | 0 |
| wielu_mocodawcow | 6 | 0 | 6 | 0 |
| mocodawca_osoba_fizyczna | 4 | 0 | 4 | 0 |
| pesel_obecny | 1 | 0 | 1 | 0 |
| brak_pelnomocnika | 0 | 0 | 0 | 0 |
| brak_bzp_i_ted | 0 | 0 | 0 | 0 |
| powod_12 | 0 | 0 | 0 | 0 |
| przelew_wpis | 0 | 0 | 0 | 0 |
| skan | 0 | 0 | 0 | 0 |
| skan_z_ocr | 0 | 0 | 0 | 0 |
| zla_warstwa_ocr | 0 | 0 | 0 | 0 |
| strona_mieszana | 0 | 0 | 0 | 0 |
| dokument_mieszany | 0 | 0 | 0 | 0 |
| obrot | 0 | 0 | 0 | 0 |
| obrot_flaga_pdf | 0 | 0 | 0 | 0 |
| przekrzywienie | 0 | 0 | 0 | 0 |
| niska_jakosc | 0 | 0 | 0 | 0 |
| pieczatka_podpis | 0 | 0 | 0 | 0 |
| odreczne | 0 | 0 | 0 | 0 |
| pusta_strona | 0 | 0 | 0 | 0 |
| uciety_tekst | 0 | 0 | 0 | 0 |
| anonimizacja | 0 | 0 | 0 | 0 |
| znak_wodny | 0 | 0 | 0 | 0 |
| nietypowy_rozmiar_strony | 0 | 0 | 0 | 0 |
| wiele_dokumentow | 0 | 0 | 0 | 0 |
| dokument_obcy | 0 | 0 | 0 | 0 |
| podobny_do_klasy | 0 | 0 | 0 | 0 |
| duplikat_pliku | 0 | 0 | 0 | 0 |
| jezyk_obcy | 0 | 0 | 0 | 0 |
| inne | 0 | 0 | 0 | 0 |
| ocr_niedostepny | 0 | 0 | 0 | 0 |
| ocr_blad | 0 | 0 | 0 | 0 |
| pdf_uszkodzony | 0 | 0 | 0 | 0 |
| pdf_zaszyfrowany | 0 | 0 | 0 | 0 |
| llm_niedostepny | 0 | 0 | 0 | 0 |
| llm_autoryzacja | 0 | 0 | 0 | 0 |
| llm_limit | 0 | 0 | 0 | 0 |
| llm_odpowiedz_niepoprawna | 0 | 0 | 0 | 0 |
| konfiguracja_niepoprawna | 0 | 0 | 0 | 0 |
| limit_czasu | 0 | 0 | 0 | 0 |
| limit_kontekstu | 0 | 0 | 0 | 0 |
| zapis_nieudany | 0 | 0 | 0 | 0 |
| walidacja_wyniku_nieudana | 0 | 0 | 0 | 0 |
| klasa_niejednoznaczna | 0 | 0 | 0 | 0 |

### Rozkład dopasowania per pole

Indeksy list zastąpiono `[]`; identyczne ścieżki różnych elementów agregowano.

| Pole | dokladne | inny_zapis | inna_forma_gramatyczna | wyliczana | nieznaleziona | null_w_referencji |
|---|---|---|---|---|---|---|
| OdwolanieKIO.czynnosc_dzien | 0 | 60 | 0 | 0 | 0 | 0 |
| OdwolanieKIO.czynnosc_opis | 4 | 0 | 0 | 56 | 0 | 0 |
| OdwolanieKIO.czynnosc_powod_id | 0 | 0 | 0 | 60 | 0 | 0 |
| OdwolanieKIO.data | 0 | 45 | 0 | 0 | 0 | 15 |
| OdwolanieKIO.miejscowosc | 45 | 0 | 0 | 0 | 0 | 15 |
| Odwolujacy[].krs | 56 | 0 | 0 | 0 | 0 | 4 |
| Odwolujacy[].nazwa | 60 | 0 | 0 | 0 | 0 | 0 |
| Odwolujacy[].nip | 60 | 0 | 0 | 0 | 0 | 0 |
| Odwolujacy[].pelnomocnik.imie_nazwisko | 60 | 0 | 0 | 0 | 0 | 0 |
| Odwolujacy[].pelnomocnik.mail | 60 | 0 | 0 | 0 | 0 | 0 |
| Odwolujacy[].pelnomocnik.nazwa | 60 | 0 | 0 | 0 | 0 | 0 |
| Odwolujacy[].przez-pelnomocnika | 0 | 0 | 0 | 60 | 0 | 0 |
| Odwolujacy[].regon | 60 | 0 | 0 | 0 | 0 | 0 |
| Zamawiajacy[].krs | 58 | 0 | 0 | 0 | 0 | 5 |
| Zamawiajacy[].nazwa | 63 | 0 | 0 | 0 | 0 | 0 |
| Zamawiajacy[].nip | 63 | 0 | 0 | 0 | 0 | 0 |
| Zamawiajacy[].prowadzacy_postepowanie | 0 | 0 | 0 | 6 | 0 | 57 |
| Zamawiajacy[].regon | 63 | 0 | 0 | 0 | 0 | 0 |
| ZamowieniePubliczne.numer_bzp | 33 | 15 | 0 | 0 | 0 | 12 |
| ZamowieniePubliczne.numer_postepowania | 60 | 0 | 0 | 0 | 0 | 0 |
| ZamowieniePubliczne.numer_ted | 14 | 33 | 0 | 0 | 0 | 13 |
| ZamowieniePubliczne.tytul | 60 | 0 | 0 | 0 | 0 | 0 |
| mocodawca[].data.imie_nazwisko | 4 | 0 | 0 | 0 | 0 | 62 |
| mocodawca[].data.krs | 62 | 0 | 0 | 0 | 0 | 4 |
| mocodawca[].data.nazwa | 66 | 0 | 0 | 0 | 0 | 0 |
| mocodawca[].data.nip | 66 | 0 | 0 | 0 | 0 | 0 |
| mocodawca[].data.typ | 0 | 0 | 0 | 66 | 0 | 0 |
| mocodawca[].podpisujacy[].imie_nazwisko | 95 | 0 | 0 | 0 | 0 | 0 |
| pelnomocnicy[].imie_nazwisko | 98 | 0 | 0 | 0 | 0 | 0 |
| pelnomocnicy[].pesel | 1 | 0 | 0 | 0 | 0 | 97 |
| przelew_bankowy.data_operacji | 13 | 47 | 0 | 0 | 0 | 0 |
| przelew_bankowy.kwota | 0 | 60 | 0 | 0 | 0 | 0 |
| przelew_bankowy.na_rachunek | 5 | 55 | 0 | 0 | 0 | 0 |
| przelew_bankowy.numer_transakcji | 60 | 0 | 0 | 0 | 0 | 0 |
| przelew_bankowy.tytul | 60 | 0 | 0 | 0 | 0 | 0 |
| przelew_bankowy.z_rachunku | 5 | 55 | 0 | 0 | 0 | 0 |

### Najczęstsze braki

Brak pól ze statusem `nieznaleziona`.

### Grupowanie

Ramka na stronę obejmuje pierwsze wystąpienie każdego pola grupy (pierwsze w kolejności Popplera), a także najbliższą wykrytą etykietę roli. Kolizja: środek dowolnego zlokalizowanego wystąpienia pola innej grupy znajduje się w ramce. Puste obszary dają `spojna=false`. Podgrupy pełnomocnika i podpisujących są oddzielne; `mocodawca[i].data` należy do mocodawcy. Wysokość w liniach = wysokość ramki / mediana wysokości linii strony.

| Klasa / typ grupy | Spójne / wszystkie | % | Kompletne | Bez obszaru | Przykłady niespójnych (id: grupa) |
|---|---|---|---|---|---|
| odwolanie / OdwolanieKIO | 21/60 | 35.0 | 60 | 0 | p02_odwolanie: OdwolanieKIO; p03_odwolanie: OdwolanieKIO; p04_odwolanie: OdwolanieKIO; p05_odwolanie: OdwolanieKIO; p06_odwolanie: OdwolanieKIO |
| odwolanie / Odwolujacy[] | 26/60 | 43.33 | 60 | 0 | p02_odwolanie: Odwolujacy[0]; p03_odwolanie: Odwolujacy[0]; p04_odwolanie: Odwolujacy[0]; p05_odwolanie: Odwolujacy[0]; p06_odwolanie: Odwolujacy[0] |
| odwolanie / Odwolujacy[].pelnomocnik | 43/60 | 71.67 | 60 | 0 | p11_odwolanie: Odwolujacy[0].pelnomocnik; p31_odwolanie: Odwolujacy[0].pelnomocnik; p40_odwolanie: Odwolujacy[0].pelnomocnik; p42_odwolanie: Odwolujacy[0].pelnomocnik; p43_odwolanie: Odwolujacy[0].pelnomocnik |
| odwolanie / Zamawiajacy[] | 52/63 | 82.54 | 63 | 0 | p09_odwolanie: Zamawiajacy[0]; p21_odwolanie: Zamawiajacy[0]; p23_odwolanie: Zamawiajacy[0]; p25_odwolanie: Zamawiajacy[0]; p31_odwolanie: Zamawiajacy[0] |
| odwolanie / ZamowieniePubliczne | 60/60 | 100.0 | 60 | 0 |  |
| pelnomocnictwo / mocodawca[] | 45/66 | 68.18 | 66 | 0 | p03_pelnomocnictwo: mocodawca[0]; p06_pelnomocnictwo: mocodawca[0]; p09_pelnomocnictwo: mocodawca[0]; p15_pelnomocnictwo: mocodawca[0]; p18_pelnomocnictwo: mocodawca[0] |
| pelnomocnictwo / mocodawca[].podpisujacy[] | 75/95 | 78.95 | 95 | 0 | p08_pelnomocnictwo: mocodawca[0].podpisujacy[1]; p14_pelnomocnictwo: mocodawca[0].podpisujacy[1]; p16_pelnomocnictwo: mocodawca[0].podpisujacy[1]; p20_pelnomocnictwo: mocodawca[0].podpisujacy[1]; p23_pelnomocnictwo: mocodawca[0].podpisujacy[1] |
| pelnomocnictwo / pelnomocnicy[] | 70/98 | 71.43 | 98 | 0 | p01_pelnomocnictwo: pelnomocnicy[1]; p02_pelnomocnictwo: pelnomocnicy[1]; p04_pelnomocnictwo: pelnomocnicy[1]; p08_pelnomocnictwo: pelnomocnicy[1]; p12_pelnomocnictwo: pelnomocnicy[0] |
| przelew / przelew_bankowy | 60/60 | 100.0 | 60 | 0 |  |

## Interpretacja i ograniczenia

Grupowanie można zbudować, ale jedna ramka na podmiot nie działa niezawodnie dla wszystkich dokumentów. UI powinno dopuszczać kilka obszarów i zaznaczenia pojedynczych pól. Spójność nie dowodzi prawidłowego przypisania semantycznego: ta sama miejscowość może występować w adresach różnych stron. Kontrola kolizji obejmuje tylko pola referencji, nie wszystkie obce dane obecne w PDF (np. partnera konsorcjum nieuwzględnionego w referencji). Brak kolizji w grupie przelewu ma ograniczoną wartość, bo to jedyna grupa w kontrakcie.

Etykiety ról: wyłącznie role podmiotów, słownik i okno 8 linii o umownej wysokości 14 pt. Tytuł ODWOŁANIE, metadane zamówienia i nagłówek potwierdzenia przelewu nie są rolami. W przelewie osobno sprawdza się płatnika dla z_rachunku i odbiorcę dla na_rachunek. Po zawężeniu definicji przeliczono wszystkie karty w wersji dokumentacji 0.6.0; zmiana liczebności nie jest zmianą oryginałów. Etykiety pól: ta sama lub poprzednia linia Popplera. Wynik „brak” oznacza brak wykrycia, a nie stwierdzony brak etykiety. Liczba kolumn to kandydat 1/2 (co najmniej trzy przerwy >45 pt w wierszach o zbliżonym y), bez analizy linii graficznych; nie rozstrzyga, czy tabela ma widoczne krawędzie. `niewidoczna_tabela` oznacza kandydata z etykietą i wartością na tej samej wysokości, w różnych blokach.

Normalizacja tekstów: Unicode NFKC, wielkość liter i odstępy. Identyfikatory porównuje się bez spacji/myślników i opcjonalnego PL; daty i kwoty według jawnych wariantów. Dopasowanie rozmyte tylko dla nazw i tytułów: >=90 dla tekstów >=40 znaków albo >=82 i zgodne początki słów dla kandydatów odmiany; cyfry muszą być identyczne. Próg nie został skalibrowany na odrębnym zbiorze, a `inna_forma_gramatyczna` jest hipotezą. Literalne wartości wyliczane są lokalizowane; liczbowe kody reguł nie są szukane jako przypadkowe cyfry.

Dopasowanie literalne nie potwierdza roli: data czynności może pojawić się przy innym zdarzeniu, numer transakcji w tytule, miejscowość w cudzym adresie. Status pola opisuje najlepsze dopasowanie; lista wystąpień zawiera wszystkie trafienia ścisłe, a fuzzy tylko najlepsze trafienie na stronę, jeśli w całym dokumencie brak trafień ścisłych. Bbox obejmuje całe słowa Popplera (także końcową interpunkcję); wielowierszowa wartość ma prostokąt obejmujący także pustą przestrzeń. Nie weryfikuje się poprawności merytorycznej referencji.

## Kontrola ręczna

Próba warstwowa: obowiązkowe `p41_odwolanie`, `p42_odwolanie`; pozostałe losowano z posortowanych id przez `random.Random(20261121)` kolejno z klas pełnomocnictwo, przelew, pełnomocnictwo (bez powtórzeń). Porównano wszystkie niepuste wartości tych pięciu kart z tekstem `pdftotext -layout`; dla odwołań sprawdzono nagłówek i opis czynności (strony 1–2), a także powtórzenia w dalszej treści. Obejrzano render pierwszych stron i położenia ramek.

| Karta | Co sprawdzono i wynik |
|---|---|
| p41_odwolanie | Lider Torvex, odrębny partner Hydromel, NIP/KRS/REGON, pełnomocnik, TED 2026/S 142-999327, tytuł w kilku liniach, data 4 sierpnia. Wykryto i poprawiono fałszywy brak REGON: numer 2) następnej pozycji listy blokował wzorzec. Dodano regresję. Ramka lidera nie obejmuje partnera, którego pola nie występują w referencji. |
| p42_odwolanie | Obaj zamawiający, ich cztery dane identyfikacyjne, BZP, nazwa i mail pełnomocnika, data pisma na s.1 i czynności na s.2. Odróżniono konsorcjum innego wykonawcy (s.3) od odwołującego; zawężono kod konsorcjum do nagłówka roli. Pozostają kolizje z miejscowością Kraków obecną też w adresach. |
| p34_pelnomocnictwo | Galdaris, NIP/KRS, Ignacy Sikorski, Marek Jabłoński i Norbert Rutkiewicz. Wszystkie wartości literalne poprawne. Zawężono bbox etykiety roli do jej słów zamiast całej linii; po poprawce obie grupy pełnomocników są spójne. |
| p12_przelew | Data operacji 09-07-2026 zamiast daty pisma 12 lipca, kwota 200.00 PLN, dwa rachunki ze spacjami, tytuł w dwóch liniach i dwa wystąpienia numeru transakcji. Literalna lokalizacja numeru zaczyna się już w tytule. |
| p18_pelnomocnictwo | Balttec, NIP/KRS, Dorota Zawadzki i Grzegorz Bąkiewicz. Dane mocodawcy i pełnomocnika są w tym samym akapicie; najbliższa etykieta może objąć inną grupę. To ograniczenie jednej ramki. |

Poprawki po kontroli zastosowano ponownie do wszystkich 180 kart. Próba nie stanowi pełnego audytu semantycznego ani pomiaru trafności heurystyk na całym zbiorze.

## Odtworzenie i weryfikacja

Z katalogu głównego repo uruchom wskazanym Pythonem 3.13: `experiments/2026-11-21-przypadki-brzegowe/narzedzia/inwentarz.py`, następnie `narzedzia/karty.py` oraz `narzedzia/katalog_md.py` (dwie ostatnie ścieżki względem katalogu eksperymentu). Testy: `python -m pytest experiments/2026-11-21-przypadki-brzegowe/narzedzia/test_karty.py -q`. Dokumentacja: `python3 scripts/verify_docs.py`. Bez sieci i API. Weryfikacja 0.6.0: 74 testy pytest zakończone powodzeniem (w tym walidacja wszystkich 180 kart i regresje etykiet ról); `python3 scripts/verify_docs.py`: OK, 440 materiałów i 48 dokumentów. `git diff --check`: bez błędów. Historyczna kontrola ręczna pięciu kart dotyczyła lokalizacji referencji; nie jest ponownym audytem zmienionych etykiet ról.
