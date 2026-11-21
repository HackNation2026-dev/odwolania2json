---
wersja: 0.6.0
aktualizacja: 2026-11-21
status: wynik eksperymentu heurystycznego — zweryfikowana próba pięciu kart
---

# Katalog kodów przypadków brzegowych

Źródło definicji: [kanoniczny JSON](przypadki-brzegowe.json). Liczby dotyczą 180 pozytywnych PDF-ów, każdy liczony raz dla danego kodu. O/P/R = odwołanie/pełnomocnictwo/przelew. Zero oznacza brak wykrycia przez użyte heurystyki, a nie dowód nieobecności. Kody wymagające oceny obrazu nie są automatycznie rozstrzygane. Grupa `wykonanie` opisuje zachowanie silnika; jej zera w kartach nie są pomiarem odporności, bo narzędzie nie uruchamia produktu.

| Kod | Grupa | Nazwa | Definicja | Źródła | Wykrywanie | Testowanie | W danych: razem (O/P/R) |
|---|---|---|---|---|---|---|---|
| brak_etykiety_roli | uklad | Brak etykiety roli | Nie wykryto lokalnej etykiety roli podmiotu: zamawiającego, odwołującego, pełnomocnika, mocodawcy, podpisującego albo płatnika/odbiorcy. Rola może wynikać ze zdania. Dotyczy tylko podmiotów, nie grup metadanych; tytuł dokumentu (np. ODWOŁANIE) nie jest etykietą roli. Brak wykrycia w karcie nie dowodzi braku etykiety w PDF. | U | karta | nowe układy (grupa C) z usuniętą etykietą | 18 (0/15/3) |
| etykieta_po_danych | uklad | Etykieta po danych | Lokalna etykieta roli podmiotu (zamawiający, odwołujący, pełnomocnik, mocodawca, podpisujący, płatnik/odbiorca) stoi po jego danych albo w środku bloku. Tytuł dokumentu (np. ODWOŁANIE) ani etykieta metadanych nie jest etykietą roli. | U | karta | nowe układy z permutacją kolejności | 62 (0/55/7) |
| etykieta_synonim | uklad | Synonim etykiety | Rola nazwana innym słowem niż klucz JSON (np. Wykonawca, Skarżący, Strona, „w imieniu”). | U, D | karta | mutacje etykiet w nowych układach | 94 (60/34/0) |
| brak_etykiety_przy_wartosci | uklad | Wartość bez etykiety pola | Wartość stoi bez etykiety typu „NIP:”, „KRS:”, „Data:” w tej samej lub poprzedniej linii. | U | karta | nowe układy bez etykiet pól | 180 (60/60/60) |
| niewidoczna_tabela | uklad | Niewidoczna tabela | Układ oparty na tabeli bez widocznych krawędzi (białe na białym); tekst jednego wiersza trafia do różnych bloków przy ekstrakcji. | U | karta (heurystyka) + ręczne | nowe układy z niewidoczną tabelą 2–3 kolumny | 32 (0/0/32) |
| uklad_wielokolumnowy | uklad | Układ wielokolumnowy | Tekst w kilku kolumnach lub ramkach obok siebie. | D | karta (heurystyka) | regresja na oryginałach | 78 (14/26/38) |
| tabela | uklad | Tabela | Dane w tabeli z widocznymi krawędziami, trudne do odczytu liniowego. | D | ręczne | regresja | 0 (0/0/0) |
| brak_informacji_wprost | tresc | Brak informacji wprost | Wartość referencji nie występuje dosłownie w dokumencie; trzeba ją wywnioskować z treści albo jej brakuje (wtedy null i jawne wskazanie braku). | U | karta | dokumenty z usuniętymi wprost podanymi faktami | 0 (0/0/0) |
| wartosc_wyliczana | tresc | Wartość wyliczana | Wartość pochodzi z reguły lub słownika (np. czynnosc_opis, przez-pelnomocnika, prowadzacy_postepowanie, typ mocodawcy). | D | karta | regresja; walidacja reguł | 120 (60/60/0) |
| inny_zapis_wartosci | tresc | Inny zapis wartości | Wartość zapisana inaczej niż w referencji (rachunek z PL i spacjami, data słownie lub DD.MM.RRRR, BZP ze spacją, TED jako RRRR/S…, kwota z przecinkiem). | K, D | karta | regresja; mutacje zapisu w nowych układach | 120 (60/0/60) |
| inna_forma_gramatyczna | tresc | Inna forma gramatyczna | Imię i nazwisko albo nazwa w innym przypadku niż w referencji (np. dopełniacz zamiast mianownika). | D | karta | regresja | 0 (0/0/0) |
| wiele_wystapien | tresc | Wiele wystąpień | Ta sama wartość występuje w dokumencie kilka razy (różne strony, role lub zapisy). | K, D | karta | warianty zasłaniające jedno wystąpienie (grupa B) | 162 (60/42/60) |
| wartosc_w_kilku_liniach | tresc | Wartość w kilku liniach | Wartość (np. długi tytuł, nazwa firmy) jest rozbita na kilka linii lub bloków. | A | karta | regresja | 135 (59/17/59) |
| dane_dalej_niz_3_strona | tresc | Dane dalej niż na 3. stronie | Co najmniej jedna wartość występuje wyłącznie po 3. stronie. | K, D | karta | regresja | 21 (21/0/0) |
| konsorcjum | wariant | Konsorcjum | Odwołujący to konsorcjum; referencja zawiera lidera. | K, D | karta | regresja | 6 (6/0/0) |
| wielu_zamawiajacych | wariant | Wielu zamawiających | Więcej niż jeden zamawiający; prowadzacy_postepowanie 1/0. | D | karta | regresja | 3 (3/0/0) |
| wielu_mocodawcow | wariant | Wielu mocodawców | Pełnomocnictwo udzielone przez więcej niż jeden podmiot. | D | karta | regresja | 6 (0/6/0) |
| mocodawca_osoba_fizyczna | wariant | Mocodawca: osoba fizyczna | Mocodawca jest osobą fizyczną (imie_nazwisko, typ osoba_fizyczna). | D | karta | regresja | 4 (0/4/0) |
| pesel_obecny | wariant | PESEL obecny | Pełnomocnik ma PESEL w dokumencie. | D | karta | nowe treści (grupa C) | 1 (0/1/0) |
| brak_pelnomocnika | wariant | Brak pełnomocnika | Odwołujący działa bez pełnomocnika (przez-pelnomocnika 0). | K, D | karta | nowe treści (grupa C) | 0 (0/0/0) |
| brak_bzp_i_ted | wariant | Brak BZP i TED | Odwołanie bez numeru BZP i bez numeru TED. | K, D | karta | nowe treści (grupa C) | 0 (0/0/0) |
| powod_12 | wariant | Powód czynności 12 | Zaskarżone projektowane postanowienia umowy (kod 12). | K, D | karta | nowe treści (grupa C) | 0 (0/0/0) |
| przelew_wpis | wariant | Przelew: wpis od odwołania | Potwierdzenie przelewu wpisu od odwołania (kwoty rzędu tysięcy zł), a nie opłaty skarbowej. | K, D | karta | nowe treści (grupa C) | 0 (0/0/0) |
| skan | pdf | Skan | Strona jest obrazem (zdjęcie lub skan), bez cyfrowej warstwy tekstu. | M, D | inwentarz | grupa A | 0 (0/0/0) |
| skan_z_ocr | pdf | Skan z warstwą OCR | Obraz strony z ukrytą warstwą tekstu z OCR. | K | inwentarz | grupa A | 0 (0/0/0) |
| zla_warstwa_ocr | pdf | Błędna warstwa OCR | Warstwa tekstu niezgodna z obrazem (błędne cyfry, znaki, kolejność, braki); cichy błąd. | K | ręczne | grupa A: obraz poprawny + błędny niewidoczny tekst | 0 (0/0/0) |
| strona_mieszana | pdf | Obraz z treścią na stronie tekstowej | Strona ma warstwę tekstu, ale część treści (także dane do JSON) jest wklejonym obrazem; wymaga OCR regionu. | U, K | inwentarz | grupa A: blok danych jako obraz | 0 (0/0/0) |
| dokument_mieszany | pdf | Dokument mieszany | W jednym pliku strony tekstowe i zeskanowane. | M | inwentarz | grupa A | 0 (0/0/0) |
| obrot | pdf | Obrót treści | Treść obrócona o 90/180/270° w obrazie. | K, D | ręczne / model | grupa A | 0 (0/0/0) |
| obrot_flaga_pdf | pdf | Obrót flagą PDF | Strona obrócona atrybutem /Rotate. | D | inwentarz | grupa A | 0 (0/0/0) |
| przekrzywienie | pdf | Przekrzywienie | Skan lekko przekrzywiony (kilka stopni). | K | ręczne / model | grupa A | 0 (0/0/0) |
| niska_jakosc | pdf | Niska jakość | Niska rozdzielczość, rozmycie, szum, kompresja, ksero, faks, słaby kontrast. | K | ręczne / model | grupa A | 0 (0/0/0) |
| pieczatka_podpis | pdf | Pieczątka lub podpis na treści | Pieczątka, podpis lub adnotacja nachodzi na tekst. | K, D | ręczne / model | grupa B | 0 (0/0/0) |
| odreczne | pdf | Pismo odręczne | Istotna treść napisana ręcznie. | K, D | ręczne / model | fizyczne skany | 0 (0/0/0) |
| pusta_strona | pdf | Pusta strona | Strona bez treści lub prawie pusta. | K, D | inwentarz | grupa A | 0 (0/0/0) |
| uciety_tekst | pdf | Ucięty tekst | Tekst ucięty przy krawędzi strony. | K | ręczne / model | grupa B | 0 (0/0/0) |
| anonimizacja | pdf | Anonimizacja | Zaczernienia lub usunięte dane. | D | ręczne / model | grupa B | 0 (0/0/0) |
| znak_wodny | pdf | Znak wodny | Znak wodny lub tło utrudniające odczyt. | A | ręczne / model | grupa A | 0 (0/0/0) |
| nietypowy_rozmiar_strony | pdf | Nietypowy rozmiar strony | Rozmiar strony daleki od A4 (np. piksele zapisane jako punkty). | D | inwentarz | grupa A | 0 (0/0/0) |
| wiele_dokumentow | klasa | Wiele dokumentów w pliku | Kilka różnych dokumentów w jednym pliku; wynik do ustalenia z mentorem. | K | ręczne / model | test „nie wywraca się” | 0 (0/0/0) |
| dokument_obcy | klasa | Dokument obcy | Dokument spoza klas: odwołanie, pełnomocnictwo, przelew. | M, D | referencja | negatywy | 0 (0/0/0) |
| podobny_do_klasy | klasa | Trudny negatyw | Dokument obcy łudząco podobny do jednej z klas (np. wyrok KIO, ogłoszenie BZP/TED). | K, D | ręczne / model | negatywy | 0 (0/0/0) |
| duplikat_pliku | klasa | Duplikat pliku | Plik identyczny bajtowo z innym (traktować jako jedną rodzinę przy podziale). | K, D | inwentarz | kontrola podziału | 0 (0/0/0) |
| jezyk_obcy | klasa | Język obcy | Treść w języku innym niż polski. | A | ręczne / model | negatywy | 0 (0/0/0) |
| inne | klasa | Inne | Problem spoza listy, opisany w polu opis; kandydat na nowy kod. | A | ręczne | — | 0 (0/0/0) |
| ocr_niedostepny | wykonanie | OCR niedostępny | Strona wymaga OCR, ale dostawca jest wyłączony lub niegotowy. Nie oznacza dokumentu obcego. | A | E: gotowość dostawcy i diagnoza strony | wyłączenie OCR dla skanu i dokumentu mieszanego; jawne nieprzetworzone pola | 0 (0/0/0) |
| ocr_blad | wykonanie | Błąd OCR | Dostępny dostawca OCR nie zakończył odczytu strony lub regionu. | A | E: wyjątek lub wadliwy wynik adaptera | atrapa awarii OCR; zachowanie odczytu innych stron | 0 (0/0/0) |
| pdf_uszkodzony | wykonanie | Uszkodzony PDF | Struktury PDF nie można odczytać; to nie to samo co ucięta treść strony. | A | E: błąd parsera | uszkodzona kopia PDF poza oryginałami; kontynuacja wsadu | 0 (0/0/0) |
| pdf_zaszyfrowany | wykonanie | Zaszyfrowany PDF | Treść PDF wymaga hasła lub pozostaje niedostępna dla czytnika. | A | E: informacja czytnika o szyfrowaniu i braku dostępu | zaszyfrowana kopia bez hasła; jawny raport | 0 (0/0/0) |
| llm_niedostepny | wykonanie | LLM niedostępny | Brak sieci lub niedostępność usługi AI uniemożliwia analizę. | A | T1/T3/T4: błąd połączenia lub niedostępności API | atrapa niedostępnej sieci/usługi; brak podmiany starym cache | 0 (0/0/0) |
| llm_autoryzacja | wykonanie | Błąd autoryzacji LLM | API odrzuca klucz lub uprawnienia (401/403). | A | T1/T3/T4: status API | atrapa 401/403; bez ujawnienia klucza i bez automatycznej pętli prób | 0 (0/0/0) |
| llm_limit | wykonanie | Limit LLM | API ogranicza wywołania (429) albo wyczerpano budżet. | A | T1/T3/T4: status API lub kontrola budżetu | atrapa 429; ograniczenie ponowień i czasu | 0 (0/0/0) |
| llm_odpowiedz_niepoprawna | wykonanie | Niepoprawna odpowiedź LLM | Odpowiedź AI nie spełnia kontraktu: np. wadliwy JSON, nieznane pola lub brak wymaganych dowodów. | A | T1/T3/T4: walidacja odpowiedzi i dowodów | wadliwy JSON i cytat bez pokrycia; jawny stan błędu | 0 (0/0/0) |
| konfiguracja_niepoprawna | wykonanie | Niepoprawna konfiguracja | YAML klasy, słownik lub ustawienia silnika nie spełniają kontraktu. | A | start/T5: walidacja konfiguracji | brak słownika, nieznana reguła i błędny typ; brak pozornego wyniku | 0 (0/0/0) |
| limit_czasu | wykonanie | Limit czasu | Etap przekroczył skonfigurowany limit zadania; nie jest to deklaracja limitu jury. | A | wykonawca: pomiar czasu etapu | kontrolowane opóźnienie; zakończenie zadania i kontynuacja wsadu | 0 (0/0/0) |
| limit_kontekstu | wykonanie | Limit kontekstu | Cała treść dokumentu nie mieści się w kontekście modelu; zakresu nie wolno cicho uciąć. | A | T1/T3: obliczenie rozmiaru wejścia | długi dokument; jawne wskazanie nieprzetworzonych zakresów | 0 (0/0/0) |
| zapis_nieudany | wykonanie | Błąd zapisu | Nie udało się zatwierdzić stagingu lub artefaktu wynikowego na dysku. | A | L/eksport: wyjątek zapisu lub zastąpienia pliku | atrapa błędu dysku/uprawnień; atomowość i brak niepełnego wyniku | 0 (0/0/0) |
| walidacja_wyniku_nieudana | wykonanie | Błąd walidacji wyniku | Dane kanoniczne nie spełniają YAML klasy lub referencyjnego kontraktu eksportu. | A | T5: błędy walidatora | brak nienullowalnego pola, zły typ i dodatkowy klucz; raport poza JSON | 0 (0/0/0) |
| klasa_niejednoznaczna | wykonanie | Niejednoznaczna klasa | Router nie rozstrzyga klasy: konflikt kandydatów lub za mało przesłanek przy dostępnym odczycie. To nierozstrzygnięcie, nie awaria infrastruktury. | A | T1: progi per klasa i odstęp kandydatów | trudny negatyw i konflikt funkcji; nie zastępować stanem obcy | 0 (0/0/0) |

Źródła: **U** — wiedza użytkownika o prawdziwych dokumentach (rozmowa 2026-11-21); **M** — mentor UZP (docs/01-zadanie/zrodla/odpowiedzi-mentora-2026-11-21.md); **K** — konsultacja Fable i Codex (docs/07-decyzje/konsultacja-trudne-przypadki-2026-11-21/); **D** — sprawdzone w danych organizatora (inwentarz, karty dokumentów); **A** — propozycja asystenta.

[Wyniki i ograniczenia kart](karty-dokumentow-2026-11-21.md).
