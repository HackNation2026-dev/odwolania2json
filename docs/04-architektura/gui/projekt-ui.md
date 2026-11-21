---
wersja: 0.3.0
aktualizacja: 2026-11-21
status: PROJEKT po recenzji Codex, do zatwierdzenia użytkownika; nie opis implementacji
autor: projektant UI (Claude), aktualizacja Codex na podstawie zlecenia B 0.6.0
---

# Projekt interfejsu Odwołania2JSON

Wejście: [brief projektu UI](brief-projektu-ui.md). Dokument opisuje funkcje, strony, widoki, nawigację, treść, stany, przepływy, model danych widoczny w UI, punkt rozszerzenia, tokeny wizualne, zakres MVP i listę ramek do makiet. Nie wybiera bibliotek UI: komponenty są opisane generycznie (przycisk, karta, tabela, zakładki, szuflada, okno dialogowe, przeglądarka PDF, edytor kodu).

## 0. Oznaczenia źródeł

Każdą decyzję oznaczam jednym ze znaczników:

| Znacznik | Znaczenie | Przykładowe źródło |
|---|---|---|
| **[ORG]** | wymaganie lub wypowiedź organizatora | [punktacja](../../01-zadanie/punktacja.md), [FAQ 12b](../../01-zadanie/zrodla/FAQ-Odwolania2JSON-v1.0.md), [README organizatora](../../02-materialy/organizator-uzp/README.md) |
| **[ZESP]** | decyzja zespołu lub użytkownika | [brief](brief-projektu-ui.md), [ADR-002](../../07-decyzje/ADR-002-decyzje-po-recenzji.md), [wymagania 0.5.0](../../03-wymagania/README.md) |
| **[DANE]** | wynika z wzorców JSON i referencji | [oczekiwane-json](../../02-materialy/organizator-uzp/oczekiwane-json/), [eksperyment YAML](../../05-weryfikacja/eksperyment-yaml-klasy-2026-11-21.md) |
| **[PROP]** | propozycja projektanta, do akceptacji | — |
| **[ADR]** | decyzje i uzupełnienia użytkownika, w tym brak ścieżki idealnej | [ADR-002](../../07-decyzje/ADR-002-decyzje-po-recenzji.md) |
| **[PIPE]** | rekomendacje konsultacji, nie gotowe funkcje | [zlecenie](../../07-decyzje/konsultacja-pipeline-2026-11-21/zlecenie.txt), [ocena](../../07-decyzje/konsultacja-pipeline-2026-11-21/codex-odpowiedz.txt) |
| **[KARTY]** | pomiar lokalizacji znanych referencji, nie skuteczności ekstraktora | [karty](../../05-weryfikacja/karty-dokumentow-2026-11-21.md), [schemat karty](../../../experiments/2026-11-21-przypadki-brzegowe/format/karta.schema.json) |
| **[KODY]** | kanoniczne kody i definicje odstępstw | [katalog przypadków](../../05-weryfikacja/katalog-przypadkow-brzegowych.md), [JSON](../../05-weryfikacja/przypadki-brzegowe.json), [katalog kodów](../../05-weryfikacja/katalog-kodow.md) |
| **[REC]** | poprawki po recenzji, numery 1–11 | [recenzja Codex](recenzja-codex-2026-11-21.md) |
| **[MENTOR]** | odpowiedzi przekazane przez użytkownika | [odpowiedzi 2026-11-21](../../01-zadanie/zrodla/odpowiedzi-mentora-2026-11-21.md) |

Aktualizacja 0.3.0 realizuje zlecenie B użytkownika 0.6.0 z 2026-11-21, [ocenę zgodności UI](ocena-ui-vs-kryteria.txt) pkt 6.1–6.9 i [konsultację Fable](../../07-decyzje/konsultacja-ocena-calosci-2026-11-21/fable-odpowiedz.txt) §4 i §7. W razie różnic z briefem i wcześniejszym opisem pierwszeństwo ma zawężony P0 z §8.1. [Raport zmian](zmiany-ui-0.3.0.md). Bez OpenUI, MVP bez kont, dostarczenie przez pip. To wersja dokumentu, bez zmiany wersji całego repozytorium. Oryginały organizatora pozostają nienaruszone.

Zasady nadrzędne, z których wynika reszta:

1. **Ścieżka krytyczna: wgranie → analiza → PDF obok danych → JSON.** [ORG: FAQ 12b; zgłoszenie „wgranie dokumentów i odczytanie rezultatów”] Wszystko inne jest dodatkiem i nie może jej blokować. Elementy generatywne są poza zakresem. [ADR]
2. **Każda wartość ma widoczny dowód** (strona, fragment), a każdy `null` ma wyjaśnienie. [ORG: „szczególnie premiowane … transparentność procesu ekstrakcji”; ZESP: ADR-002 pkt 10]
3. **Eksport JSON zachowuje kontrakt silnika** (klucze, kolejność, typy); podgląd chroniony jest jawnie oznaczony jako zamaskowany. Dowody pokazujemy osobno. [DANE; ZESP: ADR-002 pkt 9–10]
4. **P0 pokazuje cztery grupy stanów:** w toku, pełny lub częściowy, obcy (`{}`), błąd techniczny. „Niejednoznaczny” i „Wiele dokumentów” są banerami blokującymi eksport (§3.2.1), bez osobnych rozbudowanych widoków. Pełny model diagnoz pozostaje opisem docelowym E1. [ZESP: ADR-002 pkt 11–12]
5. **Klasy dokumentów pochodzą z YAML** i UI to pokazuje (lista klas, YAML, formularz wygenerowany z YAML). [ORG: 1–20 pkt za łatwość dodawania klas; DANE: eksperyment YAML]
6. Bez godeł, logotypów i nazw instytucji jako marki. „Odwołanie do KIO” występuje wyłącznie jako nazwa rodzaju dokumentu. [ZESP: brief]

---

### 0.1. Zakres oznaczeń w całym dokumencie

**P0 = MVP: desktop 1440×900 CSS px, język PL, motyw jasny, wyłącznie S01–S03.** Szczegółowy opis docelowy poniżej pozostaje zachowany. EN, ciemny/systemowy motyw, szerokości 320/360/768/1024, menu telefonu i tabletu są **E1**, także tam, gdzie przy tekście występuje starsze słowo „MVP”. Role, maskowanie, uprawnienia, audyt i logowanie są **E3**. Etykiety PL/EN nie oznaczają dwujęzycznego P0. Etap funkcji i jej wariantu wizualnego muszą być spełnione łącznie. Wiążące listy: §8 i kolumna „Etap” w §9.2.

W P0 zostają obsługa klawiatury, widoczny fokus, semantyka, tekstowe komunikaty i „Tekst strony” na desktopie. Informację „Nie przeprowadzono audytu” i ograniczenia PDF/OCR pokazujemy w rozwijanym bloku S01, dostępnym także z S03; osobne S13 i S14 są E1 (403: E3). Błędy P0 wyświetlamy w S01–S03. Nie deklarujemy zgodności działającej aplikacji na podstawie projektu.

## 1. Role i macierz uprawnień

### 1.1. MVP (hackathon)

[ZESP; ADR; REC-1] Bez kont i logowania, wyłącznie dane syntetyczne. Domyślne uruchomienie lokalne; serwer demonstracyjny wymaga izolacji sesji i wyników oraz usunięcia danych po sesji. „Ostatnie analizy” nigdy nie pokazują cudzej sesji. Brak uwierzytelniania nie oznacza roli Operator w systemie produkcyjnym. Korekty i zatwierdzanie dopiero po MVP (§8).

Stały baner na wszystkich ekranach demo, także na telefonie, bez zamykania i zwijania:

- PL: „Tryb demonstracyjny. Tylko dane syntetyczne. Bez logowania.”
- EN: “Demo mode. Synthetic data only. No sign-in.”

MVP nie deklaruje ochrony prawdziwych danych przez maskowanie. Pełna wersja z prawdziwymi danymi wymaga kontroli backendu z §1.4 przed udostępnieniem treści.

### 1.2. Pełna wersja — role (E3)

[ZESP: brief — „użytkownicy, uprawnienia”; szczegóły ról: PROP]

| Rola (PL) | Role (EN) | Kto to jest |
|---|---|---|
| Operator | Operator | pracownik, który wgrywa dokumenty, przegląda i poprawia wyniki |
| Weryfikator | Reviewer | zatwierdza wyniki (zasada czterech oczu) |
| Konfigurator klas | Class editor | utrzymuje pliki YAML klas i pól |
| Administrator | Administrator | zarządza użytkownikami, rolami i ustawieniami |
| Obserwator | Viewer | tylko odczyt (np. audytor, kierownik) |

Użytkownik może mieć kilka ról. Uprawnienie „Dane osobowe” jest osobną flagą, nie rolą.

### 1.3. Macierz uprawnień (E3)

Legenda: ✔ — tak; — — nie; (w) — tylko w sprawach przypisanych do użytkownika lub jego zespołu [PROP].

| Uprawnienie | Operator | Weryfikator | Konfigurator | Administrator | Obserwator |
|---|---|---|---|---|---|
| Wgrywanie dokumentów i paczek | ✔ | ✔ | — | — | — |
| Uruchomienie / ponowienie analizy | ✔ | ✔ | — | — | — |
| Podgląd spraw, dokumentów, wyników | ✔ (w) | ✔ (w) | ✔ (tylko dane testowe) | ✔ | ✔ (w) |
| Zmiana klasy dokumentu | ✔ | ✔ | — | — | — |
| Korekta pól | ✔ | ✔ | — | — | — |
| Zatwierdzenie wyniku | — | ✔ (nie własnej korekty) | — | — | — |
| Cofnięcie zatwierdzenia | — | ✔ | — | ✔ | — |
| Eksport JSON / paczki | ✔ | ✔ | — | ✔ | ✔ |
| Odsłonięcie PESEL i pełnych rachunków (flaga „Dane osobowe”) | flaga | flaga | — | flaga | flaga |
| Podgląd klas i YAML | ✔ | ✔ | ✔ | ✔ | ✔ |
| Edycja, test i aktywacja klas | — | — | ✔ | — | — |
| Zarządzanie użytkownikami i rolami | — | — | — | ✔ | — |
| Dziennik zdarzeń | własne wpisy | własne wpisy | własne wpisy | ✔ | ✔ |
| Ustawienia systemu (model, retencja) | — | — | — | ✔ | — |

Każde odsłonięcie danych osobowych, eksport i zmiana roli trafia do dziennika zdarzeń [PROP]. Konfigurator używa tylko danych testowych; dostęp do dowolnej sprawy wymaga także właściwego zasięgu i uprawnienia odczytu.

### 1.4. Jedna polityka dostępu dla wszystkich kanałów (E3)

[PROP; REC-1] Każde żądanie backendu sprawdza dostęp do sprawy, dokumentu i wersji oraz flagę „Dane osobowe”. Administrator także potrzebuje tej flagi. Zasięg spraw obowiązuje we wszystkich wierszach §1.3, również przy eksporcie, audycie i wyszukiwaniu. Flaga nie rozszerza zasięgu spraw.

| Kanał | Brak dostępu do sprawy | Dostęp, bez flagi | Dostęp i flaga |
|---|---|---|---|
| Formularz, JSON, wyszukiwarka, historia, diff | odmowa bez treści | reprezentacja zamaskowana przez backend | dane pełne po świadomym odsłonięciu |
| PDF, miniatury, tekst strony, cytaty, dowody | odmowa | bezpieczna pochodna z trwale usuniętą treścią i warstwą tekstową w chronionych obszarach | oryginał po autoryzacji |
| Kopiuj, eksport dowodów, CSV audytu | odmowa | wyłącznie zamaskowana reprezentacja, opisana w nazwie | pełne dane po autoryzacji |
| Oceniany JSON, wynikowy ZIP, oryginał PDF | odmowa | zablokowane; brak surowego payloadu i URL | dozwolone zgodnie z rolą, jawnie wybrana wersja |
| Logi techniczne | identyfikator zdarzenia | bez wartości, cytatów, kluczy i tokenów | ta sama zasada minimalizacji |

Chronione są PESEL, oba rachunki, imiona i nazwiska oraz inne dane osobowe także w nazwach plików i metadanych. Nie zakładamy, że rachunek odbiorcy należy do instytucji. Bezpieczna pochodna obejmuje również obrazy, OCR, adnotacje i załączniki; jeśli jej przygotowanie się nie uda, backend odmawia podglądu („Nie można bezpiecznie wyświetlić dokumentu”), zamiast wysłać oryginał. Nakładka CSS nie jest zabezpieczeniem. Surowe dane nie trafiają do DOM, schowka ani pamięci przeglądarki użytkownika bez uprawnień. Odsłonięcie i eksport są audytowane; po utracie uprawnień widok zostaje zamknięty i dane usunięte z pamięci interfejsu.

Odmowa odsłonięcia: „Nie masz uprawnienia »Dane osobowe«. Dane pozostają ukryte.” / “You don’t have personal-data permission. Data remains hidden.” Przycisk „Zamknij” zwraca fokus do „Pokaż dane”. Tryb prezentacji tylko dodatkowo ukrywa dane na ekranie, nie nadaje uprawnień.

---

## 2. Architektura informacji

### 2.1. Mapa stron

| ID | Strona (PL / EN) | Adres [PROP] | MVP | Pełna |
|---|---|---|---|---|
| S01 | Nowa analiza / New analysis | `/` | ✔ | ✔ |
| S02 | Sprawa (wyniki paczki) / Case | `/sprawy/{id}` | ✔ | ✔ |
| S03 | Przegląd dokumentu / Document review | `/sprawy/{id}/dokumenty/{docId}` | ✔ | ✔ |
| S04 | Sprawy / Cases (lista) | `/sprawy` | — (ostatnie wyniki sesji w S01) | ✔ |
| S05 | Historia wersji / Version history | `/sprawy/{id}/dokumenty/{docId}/wersje` | — | ✔ |
| S06 | Klasy dokumentów / Document classes | `/klasy` | — | ✔ |
| S07 | Klasa: szczegóły i edytor / Class editor | `/klasy/{klasa}` | — | ✔ (edycja, test, wersje) |
| S08 | Jak to działa / How it works | `/jak-to-dziala` | — (krótki opis w S01) | ✔ |
| S09 | Użytkownicy i role / Users and roles | `/admin/uzytkownicy` | — | ✔ |
| S10 | Dziennik zdarzeń / Audit log | `/admin/dziennik` | — | ✔ |
| S11 | Ustawienia / Settings | `/ustawienia` | — (E3; warianty języka/motywu E1) | ✔ |
| S12 | Logowanie / Sign in | `/logowanie` | — | ✔ |
| S13 | Deklaracja dostępności / Accessibility statement | `/dostepnosc` | — (E1; krótki blok w S01/S03 w P0) | ✔ |
| S14 | Strony błędów 403 / 404 / 500 | — | — (E1: 404/500; E3: 403) | ✔ |

Liczba docelowa: 14 stron, bez panelu generatywnego. P0: 3 strony S01, S02, S03. Pozostałe strony i funkcje oznaczone „pełna” lub „po MVP” są specyfikacją docelową, nie obietnicą na dobę.

### 2.2. Nagłówek (wszystkie strony poza S12)

Od lewej do prawej:

1. Znak aplikacji: ikona nawiasów klamrowych `{ }` w kwadracie z zaokrągleniem + napis „Odwołania2JSON” [PROP]. Bez godła, bez barw państwowych. Link do S01.
2. (telefon, tablet) Przycisk menu, ikona „trzy kreski”, etykieta dostępna „Otwórz menu” / “Open menu”.
3. (pełna, ≥1024) Pole wyszukiwania: placeholder „Szukaj sprawy, pliku, NIP…” / “Search case, file, tax ID…”.
4. Przycisk główny „Nowa analiza” / “New analysis” (na 360 px tylko ikona „+” z etykietą dostępną).
5. (E1; w P0 tylko PL, bez przełącznika) Przełącznik języka: segment „PL | EN”, etykieta dostępna „Język interfejsu” / “Interface language”.
6. (E1; w P0 jasny, bez przełącznika) Przełącznik motywu: przycisk z menu „Motyw: Systemowy / Jasny / Ciemny” / “Theme: System / Light / Dark”. Domyślnie „Systemowy”.
7. (pełna) Menu użytkownika: inicjały w kółku; pozycje: imię i nazwisko, role, „Ustawienia”, „Wyloguj” / “Sign out”.

Na 360 px przełączniki języka i motywu przechodzą do szuflady menu (sekcja „Wygląd i język”).

Pierwszy element strony: link „Przejdź do treści” / “Skip to content”, widoczny po fokusie [WCAG 2.4.1].

### 2.3. Nawigacja główna (P0: desktop 1440; pozostałe szerokości E1)

Pozycje (kolejność):

| Ikona | PL | EN | MVP |
|---|---|---|---|
| plus w kółku | Nowa analiza | New analysis | ✔ |
| teczka | Sprawy | Cases | — |
| warstwy | Klasy dokumentów | Document classes | — |
| żarówka/schemat | Jak to działa | How it works | — |
| — separator „Administracja / Administration” — | | | |
| osoby | Użytkownicy i role | Users and roles | — |
| lista z zegarem | Dziennik zdarzeń | Audit log | — |
| koło zębate | Ustawienia | Settings | — |

Zachowanie [PROP]:

| Szerokość | Nawigacja |
|---|---|
| 360 px | górny pasek 56 px; menu jako szuflada z lewej (szer. 288 px, przyciemnione tło, zamykanie Esc, kliknięciem tła i przyciskiem „Zamknij menu”); fokus uwięziony w szufladzie |
| 768 px | jak 360, szuflada 320 px; przycisk „Nowa analiza” z tekstem |
| 1024 px | pasek boczny zwinięty („szyna”) 72 px: same ikony z podpowiedziami; przycisk rozwijania na dole szyny |
| 1440 px | pasek boczny rozwinięty 240 px: ikona + tekst; stan rozwinięcia zapamiętany lokalnie |

Na widoku S03 (przegląd) pasek boczny na 1440 px jest domyślnie zwinięty do szyny, żeby zostawić miejsce na PDF i dane [PROP].

### 2.4. Stopka

Na stronach treściowych (S01, S04, S06, S08, S13). Na S02 i S03 stopka jest ukryta (pełnoekranowa przestrzeń pracy); jej linki są dostępne w menu.

Treść PL:

- Wiersz 1: „Odwołania2JSON {wersja aplikacji} · silnik {wersja} · model {nazwa modelu}, przetwarzanie: {zweryfikowany region}”
- Wiersz 2: „Prototyp przygotowany na hackathon HackNation 2026. Nie jest serwisem żadnej instytucji publicznej.”
- Linki: „Jak to działa” · „Deklaracja dostępności” · „Licencje open source” · „Kod źródłowy”

Treść EN:

- “Odwołania2JSON {app version} · engine {version} · model {model name}, processing: {verified region}”
- “Prototype built for the HackNation 2026 hackathon. Not a service of any public institution.”
- “How it works” · “Accessibility statement” · “Open-source licences” · “Source code”

Pole `{model}`, licencja i region pochodzą z zatwierdzonej konfiguracji backendu [MENTOR; ADR]. Przy braku potwierdzenia: „Model lub region niepotwierdzony”, bez deklaracji zgodności i bez uruchamiania API.

### 2.5. Język i motyw (P0: PL i jasny; pozostałe E1)

- Polski domyślny, angielski dostępny [ZESP: brief]. Wybór zapamiętany lokalnie; atrybut `lang` dokumentu zmienia się razem z językiem.
- **Nie tłumaczymy kluczy JSON** (`OdwolanieKIO`, `przez-pelnomocnika` itd.) ani wartości z dokumentu. Tłumaczymy etykiety pól (§3.3.6) i całą chrome aplikacji [PROP].
- Daty w UI: PL `13.10.2025`, EN `13 Oct 2025`; w JSON zawsze ISO `2025-10-13` [DANE]. Kwoty: PL `10 000,00 zł`, EN `PLN 10,000.00`; w JSON liczba [DANE].
- Motyw: Systemowy (domyślny), Jasny, Ciemny; zmiana bez przeładowania; podgląd PDF zawsze na jasnym tle strony (dokument wygląda jak papier), ciemny motyw dotyczy ramy wokół [PROP].

---

## 3. Strony i widoki

Dla każdej strony: cel, dostęp, treść, komponenty, stany, breakpointy, interakcje. Teksty w cudzysłowach „…” są dokładną treścią PL; po ukośniku EN dla kluczowych.

Wspólne komunikaty stanów (używane dalej przez odwołanie „KS-x”):

| ID | PL | EN |
|---|---|---|
| KS-1 Brak uprawnień | „Nie masz dostępu do tej strony. Poproś administratora o nadanie roli.” Przycisk „Wróć do spraw”. | “You don’t have access to this page. Ask an administrator for a role.” / “Back to cases” |
| KS-2 Błąd sieci | „Nie udało się połączyć z serwerem. Sprawdź połączenie i spróbuj ponownie.” Przycisk „Spróbuj ponownie”. | “Couldn’t reach the server. Check your connection and try again.” / “Try again” |
| KS-3 Ładowanie | szkielety (szare bloki) w układzie docelowym; czytnik ekranu: „Wczytywanie…” | “Loading…” |
| KS-4 Nie znaleziono | „Nie znaleziono tej sprawy lub dokumentu. Mógł zostać usunięty.” | “This case or document was not found. It may have been deleted.” |

### 3.1. S01 Nowa analiza (strona startowa)

**Cel:** wgrać PDF (pojedynczy lub kilka; folder ze sprawami po MVP) i uruchomić analizę [ORG: FAQ 12b „wgranie PDF, uruchomienie analizy”].
**Dostęp:** MVP — każdy; pełna — Operator, Weryfikator.

**Treść (od góry):**

1. Nagłówek H1: „Nowa analiza” / “New analysis”.
2. Lead: „Wgraj dokumenty z akt sprawy odwoławczej. Rozpoznamy rodzaj każdego dokumentu po treści i wyodrębnimy dane do JSON.” / “Upload documents from an appeal case file. We’ll identify each document by its content and extract the data to JSON.”
3. Strefa upuszczania (duża karta z przerywaną ramką):
   - ikona dokumentu ze strzałką w górę,
   - „Przeciągnij tutaj pliki PDF” / “Drag PDF files here” (po MVP także folder),
   - przyciski: „Wybierz pliki” / “Choose files” (główny), „Wybierz folder” / “Choose folder” (drugorzędny, po MVP),
   - drobny tekst: „Tylko PDF, do {limit_mb} MB na plik. {komunikat_gotowosci_OCR_z_§3.1.1}” / “PDF only, up to {limit_mb} MB per file. {OCR readiness message, E1}”
4. Karta „Jak grupujemy pliki” (zwijana, domyślnie rozwinięta przy pierwszej wizycie):
   - „Pliki wybrane razem tworzą jedną paczkę roboczą. Każdy dokument analizujemy niezależnie; nie uzupełniamy danych z innych plików.”
   - „Folder z podfolderami: każdy podfolder to osobna sprawa, a nazwy plików i struktura zostaną zachowane w wyniku.” [ORG: README, struktura input/output]
   - „Nazwa pliku nie wpływa na rozpoznanie rodzaju dokumentu.” [ORG: README „nie sugerujcie się nazwą pliku”]
5. Po wybraniu plików pojawia się sekcja „Wybrane pliki ({n})” / “Selected files ({n})”:
   - pole „Nazwa sprawy” / “Case name”, domyślnie nazwa folderu albo „Sprawa z {dd.mm.rrrr, gg:mm}”,
   - lista plików: ikona PDF, nazwa, rozmiar, liczba stron (jeśli znana), przycisk „Usuń z listy” (ikona ×, etykieta dostępna „Usuń {nazwa}”),
   - przy folderze z podfolderami: lista zgrupowana po sprawach, nagłówek grupy „Sprawa: {nazwa podfolderu} · {n} plików”,
   - przycisk główny „Uruchom analizę” / “Run analysis”, drugorzędny „Wyczyść” / “Clear”.
6. Karta „Gotowość i modele” (§3.1.1–3.1.2) i blok „Konfiguracja klas” (§4.6.1). Sekcja „Ostatnie analizy” / “Recent analyses” (MVP: do 5 ostatnich paczek wyłącznie z bieżącej sesji): wiersz = nazwa sprawy, data, liczniki statusów (np. „3 gotowe · 1 obcy”), link „Otwórz”.
7. Stopka.

**Stany:**

| Stan | Zachowanie i treść |
|---|---|
| Pusty (pierwsza wizyta) | jak wyżej, sekcja 6: „Nie masz jeszcze żadnych analiz.” / “No analyses yet.” |
| Przeciąganie nad strefą | ramka ciągła w kolorze `primary`, tło `primary-subtle`, tekst „Upuść, aby dodać” / “Drop to add” |
| Plik nie-PDF | wiersz z ikoną ostrzeżenia: „{nazwa}: to nie jest PDF — pominięto.” / “{name}: not a PDF. skipped.” |
| Plik za duży | „{nazwa}: plik przekracza {limit_mb} MB.” |
| Duplikat w tej samej partii (ten sam skrót) | „{nazwa}: ten sam plik jest już na liście.” |
| Wysyłanie | pasek postępu na każdym pliku + łączny: „Wysyłanie {k} z {n}…”; przycisk „Anuluj wysyłanie” |
| Błąd wysyłki | wiersz czerwony: „Nie udało się wysłać. Spróbuj ponownie.” + przycisk „Ponów” dla tego pliku |
| Brak uprawnień (pełna) | KS-1 |

**Breakpointy:** 360 — strefa upuszczania bez tekstu o przeciąganiu (telefon nie przeciąga): „Wybierz pliki PDF” + dwa przyciski jeden pod drugim na pełną szerokość; „Wybierz folder” ukryty, jeśli przeglądarka go nie obsługuje. 768 — jedna kolumna, maks. szerokość treści 640 px. 1024/1440 — kolumna 720 px wyśrodkowana; „Ostatnie analizy” pod spodem.

**Interakcje:** strefa jest kontenerem, bez roli przycisku. Osobne kontrolki „Wybierz pliki” i (po MVP) „Wybierz folder” obsługują Enter/Spację. Nie zagnieżdżamy przycisków. Po „Uruchom analizę” przejście do S02 tej sprawy (dla kilku spraw — do S04 z filtrem bieżącej partii).

#### 3.1.1. Gotowość OCR i modelu (P0)

W S01 stale widać status OCR, modelu/API, aktywną wersję zestawu YAML i limit pliku z backendu; ten sam skrót „Gotowość i modele” jest w pasku S03. Brak danych o gotowości: „Nie sprawdzono gotowości”, bez zielonego potwierdzenia. „Sprawdź ponownie” sprawdza usługi bez uruchamiania analizy PDF. Czas ostatniego sprawdzenia jest jawny; gotowość nie gwarantuje powodzenia kolejnego żądania.

| Faktyczny stan | Komunikat i zachowanie |
|---|---|
| Działający docelowy OCR | „OCR gotowy: {komponent}, {wersja}. Skany i dokumenty mieszane są obsługiwane (OCR).” Dopiero poprawne sprawdzenie komponentu pozwala na tę deklarację. |
| Działający zamiennik | „OCR tymczasowy (shim): {komponent}, {wersja}. Skany i dokumenty mieszane przetwarza zamiennik. Docelowy własny model OCR nie jest podłączony.” Oznaczenie zostaje także przy dowodzie i w pobranych dowodach. Sam wpis konfiguracji nie potwierdza działania shima. |
| Brak lub awaria komponentu OCR | „OCR niedostępny. Strony wymagające OCR pozostaną nieprzetworzone.” Upload i analiza tekstowego PDF są dostępne. Jeśli potrzeba OCR ujawni się po odczycie, pokazujemy listę nieprzetworzonych stron, powód przy polach i wynik częściowy, jeśli są podstawy do częściowej ekstrakcji, z eksportem według §3.3.5a; gdy brak podstaw do wyniku, błąd techniczny. Nigdy „obcy” z powodu braku OCR. |
| Brak klucza API | „Brak klucza API modelu. Skonfiguruj klucz po stronie serwera zgodnie z instrukcją uruchomienia.” Analiza wymagająca tego modelu zablokowana. W GUI nie ma pola klucza. |
| Odpowiedź 401 / 403 | „API odrzuciło uwierzytelnienie (401)” / „API odmówiło dostępu (403). Sprawdź uprawnienia klucza na serwerze.” Ponowne sprawdzenie po poprawie konfiguracji. |
| Limit zapytań / środków | „Osiągnięto limit zapytań. Ponów po {czas_z_API}” (bez czasu, gdy API go nie podało) / „Brak dostępnych środków API. Uzupełnij budżet po stronie dostawcy.” Rozróżnienie tylko na podstawie odpowiedzi dostawcy. Bez automatycznego płatnego ponawiania. |
| Brak sieci / niedostępny endpoint / timeout | „Nie można połączyć z API modelu” / „Endpoint modelu niedostępny” / „Przekroczono czas odpowiedzi modelu”. „Sprawdź ponownie”; szczegóły: etap, czas, kod i ID zdarzenia, bez sekretów. Awaria w toku zadania daje błąd techniczny, bez podstawiania cache. |
| Niepotwierdzone metadane | „Model, licencja lub lokalizacja niepotwierdzone. Wywołania zablokowane.” Karta wskazuje brakujące potwierdzenie. |

Niedostępność modelu blokuje „Uruchom analizę”, jeżeli aktywna ścieżka wymaga tego modelu. Wybranie plików i odczyt zapisanych wyników nadal działają. Brak backendu to KS-2, a brak sieci backendu do API to powyższy komunikat. Na stronie skanu etykieta „tekst z OCR” pojawia się wyłącznie po wykonanym OCR; inaczej „Skan, nieprzetworzony: OCR niedostępny”. Shim pozostaje wymiennym komponentem za kontraktem OCR [ADR], bez wyboru biblioteki w projekcie UI.

#### 3.1.2. Karta modeli i informacje techniczne (P0)

Przycisk „Gotowość i modele” w S01 i S03 otwiera tę samą kartę, bez przechodzenia do S08. W S03 karta rozdziela konfigurację bieżącą i tę używaną do zapisanego wyniku. Dostępne przez klawiaturę rozwinięcie ma przycisk „Zamknij” zwracający fokus.

| Informacja | Zawartość z backendu |
|---|---|
| Wszystkie modele i role | Nazwa, wersja, rola: klasyfikacja, ekstrakcja, OCR, pomocnicza; także modele zapasowe, z oznaczeniem skonfigurowany/użyty/wyłączony. Bez domyślania się liczby parametrów. |
| Rozmiar | Parametry każdego modelu (dla MoE całkowite i aktywne, jeśli potwierdzone), źródło danych i **największy model systemu**. Przy brakach „Nie ustalono największego modelu”. OCR pokazany osobno; jego udział w punktacji pozostaje pytaniem do mentora. |
| Licencja i instalacja lokalna | Nazwa i wersja licencji, odnośnik do jej treści, źródło wag i instrukcja lokalnej instalacji; stan potwierdzenia. Bez instalowania LLM na sprzęcie jury. |
| Dostawca i lokalizacja | Firma świadcząca API, kraj firmy, kraj serwera, region endpointu, źródło i data potwierdzenia oraz podstawa akceptacji wymogu geograficznego. Samo „Europa” nie zastępuje tych pól. |
| OCR | Dostawca OCR, komponent/model, wersja, lokalnie CPU lub API, kraj firmy i serwera (dla lokalnego: „lokalnie, urządzenie jury”), licencja, parametry albo „nie dotyczy” z uzasadnieniem, status **docelowy / tymczasowy (shim) / niedostępny**. |
| Wersje i zasoby | Wersja aplikacji i silnika, zestaw YAML, identyfikator rewizji kontraktu użytego do walidacji, limit pliku `{limit_mb}`, limity partii i równoległości; odnośnik do wykazu licencji komponentów. Klucze i tokeny niewidoczne. |

Rewizja kontraktu jest przypięta do konkretnego wyniku i widoczna także przy zakładce JSON, np. „Kontrakt: {rewizja}”. Nie wpisujemy „najnowszy” zamiast identyfikatora. Limity pochodzą z konfiguracji backendu, bez przykładowego `50 MB`; brak limitu w odpowiedzi to „Nie pobrano limitów”, blokada uploadu do ich odczytu. Status potwierdzenia licencji i lokalizacji pochodzi z konfiguracji zatwierdzonej przez zespół, a nie z testu łączności.

### 3.2. S02 Sprawa (wyniki paczki)

**Cel:** zobaczyć wszystkie dokumenty sprawy, ich klasę i status; wejść w przegląd; wyeksportować wynik. Zastępuje osobny ekran „postęp analizy” — postęp jest widoczny w tym samym widoku [PROP].
**Dostęp:** MVP — każdy; pełna — Operator, Weryfikator, Obserwator (w), Administrator.

**Treść (od góry):**

1. Okruszki: „Sprawy / {nazwa sprawy}”.
2. H1: „{nazwa sprawy}”, obok przycisk-ikona „Zmień nazwę” (pełna).
3. Wiersz metadanych: „Utworzono {dd.mm.rrrr gg:mm} · {n} dokumentów · konfiguracja klas {wersja}”.
4. Pasek podsumowania P0: „Wszystkie {n}”, „Pełne / częściowe {n}”, „Obce {n}”, „Błędy techniczne {n}”, „W toku {n}”. Banery „Niejednoznaczny” i „Wiele dokumentów” mają łączny licznik „Wymaga rozstrzygnięcia {n}”, bez rozbudowanego filtrowania. E1: osobne filtry pełnych, częściowych, niejednoznacznych i wielu dokumentów. Dodatkowy filtr „Do sprawdzenia {n}” dotyczy flagi przeglądu; „Zatwierdzone {n}” dopiero po MVP.
5. Akcje sprawy (po prawej na desktopie, w menu „Więcej” na telefonie):
   - (po MVP) „Pobierz wynik (ZIP)” / “Download results (ZIP)” — drzewo według ścieżek wejściowych z §4.7 [ORG: README],
   - (po MVP) „Pobierz dowody (ZIP)” / “Download evidence (ZIP)” — osobno, `evidence/` [ZESP: ADR-002 pkt 10],
   - (po MVP) „Dodaj dokumenty” / “Add documents”,
   - „Ponów nieudane” / “Retry failed” (aktywny, gdy są błędy techniczne),
6. Tabela dokumentów (desktop) / lista kart (telefon). Kolumny:
   - „Plik” — nazwa wejściowa, pod nią drobno „{n} str. · tekst / skan / mieszany”,
   - „Rozpoznano jako” — nazwa klasy (np. „Odwołanie do KIO”, „Pełnomocnictwo”, „Potwierdzenie przelewu”, „Dokument spoza zakresu”),
   - „Status” — etykieta statusu (§3.2.1),
   - „Pola” — „{wypełnione}/{wszystkie} · {n} do sprawdzenia” (dla obcego „—”),
   - „Plik wynikowy” — `{nazwa_bazowa}.json` (monospace),
   - akcja: „Przejrzyj” / “Review” (dla błędu technicznego: „Ponów” / “Retry”).
7. Filtr „Kody odstępstw” / “Deviation codes”: wyszukiwanie po kodzie i nazwie [KODY], wybór kilku kodów (OR w filtrze kodów, AND ze statusem i klasą). Przy dokumencie chip, np. `strona_mieszana`; przy polu kod przypisany do ścieżki. „Wyczyść kody” i „Brak dokumentów z wybranymi kodami”. Brak kodów oznacza „Nie zgłoszono odstępstw”, nie potwierdza braku problemów. Nieznany kod: „Nieznany kod: {kod}”, bez zmiany jego identyfikatora. W MVP wystarczy kod z opisem i prosty filtr listy.
8. „Dokumenty przetwarzane niezależnie. Braków nie uzupełniamy z innych dokumentów.” [ADR] Brak akcji przenoszenia wartości i sugestii potwierdzania umocowania na podstawie zgodności nazwisk.

#### 3.2.1. Statusy dokumentu

Status zawsze = ikona + tekst + kolor (nigdy sam kolor) [WCAG 1.4.1]. Rozdzielamy **postęp zadania** (kolejka/analizowanie), **stan wyniku** (sześć wartości poniżej), **flagę przeglądu** i **zatwierdzenie** (po MVP). „Zatwierdzone” nie zastępuje etykiety „Pełny/Częściowy”. W kolejce i w toku wynik jeszcze nie istnieje.

[PROP; PIPE] Awaria uniemożliwiająca poprawny zapis wyniku = błąd techniczny; odczytane fragmenty można zachować tylko w raporcie diagnostycznym. Jeśli niepowodzenie odczytu pozwala ustalić część danych, pokazujemy „Częściowy” i jawne „Nieprzetworzone”, bez ukrywania awarii; możliwość eksportu zależy od walidacji i wybranej polityki §3.3.5a. W P0 pokrycie pokazujemy po stronach, diagnozę regionów dopiero E1. Po odczycie: najpierw wykrycie wielu dokumentów (bez scalania), następnie rozstrzygnięcie klasy. Konflikt klas = niejednoznaczny; obcy wymaga wystarczającego odczytu i poprawnego pełnego zestawu klas. Pełny oznacza ocenę wszystkich pól i stron; częściowy ma listę braków/ograniczeń. Uzasadnione `null` (np. nie dotyczy) może należeć do pełnego wyniku. Nieznany stan backendu = „Nieznany stan. Wymaga sprawdzenia”, eksport zablokowany.

| Status (PL / EN) | Ikona | Kolor tokenu | Znaczenie |
|---|---|---|---|
| W kolejce / Queued | zegar | `neutral-strong` | czeka na przetworzenie |
| Analizowanie: {etap} / Processing: {stage} | wirujący okrąg (zatrzymany przy „ograniczonym ruchu”) | `info` | etap: „Odczyt tekstu”, „OCR”, „Klasyfikacja”, „Ekstrakcja”, „Walidacja” |
| Pełny / Complete | znacznik w okręgu | `success` | „Wynik pełny. Przetworzono wszystkie strony i pola.” Kompletność nie potwierdza prawnej poprawności. |
| Częściowy / Partial | półkole | `warning` | „Wynik częściowy. Sprawdź listę braków ({n}).” Lista: ścieżka pola, powód z §3.3.5, sprawdzone i nieprzetworzone strony/regiony. |
| Niejednoznaczny / Ambiguous | znak zapytania | `accent` | „Nie ustalono jednoznacznie klasy dokumentu. Wymaga przeglądu.” Kandydaci klas z przesłankami i sygnałami przeciwnymi; brak ocenianego JSON i eksportu. |
| Wiele dokumentów / Multiple documents | stos kartek | `info` | „Wykryto wiele dokumentów w jednym PDF. Sprawdź podział.” Segmenty ze stronami oryginału; eksport oceniany zablokowany do ustalenia kontraktu. |
| Zatwierdzone / Approved | znacznik ✔ w okręgu | `success` | pracownik zatwierdził wynik |
| Dokument spoza zakresu / Not a supported document | okrąg przekreślony | `neutral-strong` | klasa „obcy”, wynik `{}` zapisany [ZESP: ADR-002 pkt 11; ORG: README dane negatywne] |
| Błąd techniczny / Technical error | ośmiokąt z ×  | `danger` | **brak wyniku**; nie jest to pusty JSON [ZESP: ADR-002 pkt 11–12] |

**Uproszczenie P0:** tabela powyżej zachowuje docelową semantykę backendu. W P0 kolejka i analizowanie to „W toku”; pełny/częściowy mają wspólną grupę i dokładną etykietę. Dla diagnozy niejednoznacznej lub wielu dokumentów w S02 i S03 wystarczy baner z powodem, zakresem stron (jeśli przekazany) i blokadą JSON. To nie jest „obcy” ani awaria. Nie ma interaktywnego wyboru klasy/segmentu w P0; rozbudowane panele kandydatów i segmentacji to E1.

**Stany strony:**

| Stan | Treść |
|---|---|
| Analiza w toku | nad tabelą pasek postępu: „Przetworzono {k} z {n} dokumentów · {mm:ss}” / “Processed {k} of {n} documents · {mm:ss}”; wiersze w toku mają etapy; region `aria-live="polite"` ogłasza tylko zakończenie dokumentu („{plik}: gotowe”) |
| Wszystko gotowe | baner sukcesu (zamykany): „Analiza zakończona. Podsumowanie wyników: {liczniki grup stanów i banerów P0}.” / “Analysis complete. Result summary: {counts for the six states}.” |
| Partia z błędami technicznymi (odrębne od częściowego dokumentu) | baner ostrzegawczy: „Analiza zakończona z błędami. {k} dokumentów nie przetworzono z powodu błędu technicznego — wynik ekstrakcji nie został zapisany. Pozostałe dokumenty są gotowe. Eksport awarii: {polityka z §3.3.5a}.” Przycisk „Ponów nieudane”. EN: “Analysis finished with errors. {k} documents could not be processed due to a technical error. no result was saved. The other documents are ready.” |
| Pusta sprawa | „Ta sprawa nie zawiera dokumentów.” + „Dodaj dokumenty” |
| Ładowanie / błąd sieci / brak uprawnień / nie znaleziono | KS-3 / KS-2 / KS-1 / KS-4 |

**Breakpointy:** 360 — karty dokumentów jedna pod drugą (nazwa pliku, pod nią klasa, status jako etykieta, licznik pól, przycisk „Przejrzyj” na pełną szerokość); chipy podsumowania zawijane do kolejnych wierszy (strona bez poziomego przewijania); akcje sprawy w menu „Więcej” (ikona trzech kropek). 768 — karty w jednej kolumnie, akcje jako dwa przyciski + „Więcej”. 1024 — tabela bez kolumny „Plik wynikowy” (przeniesiona pod nazwę pliku). 1440 — pełna tabela.

**Interakcje:** tabela ma zwykłą semantykę tabeli, Tab przechodzi do linków „Przejrzyj”, Enter otwiera dokument. Karty są listą z linkami; bez przechwytywania strzałek. Sortowanie po kolumnach „Plik”, „Status”.

### 3.3. S03 Przegląd dokumentu (PDF obok danych)

Najważniejszy widok aplikacji [ORG: FAQ 12b „widok obok siebie: dokument źródłowy i wyodrębnione dane”; ORG: transparentność].

**Cel:** porównać dane z dokumentem, zobaczyć dowód każdego pola i pobrać JSON. Korekta i zatwierdzenie po MVP.
**Dostęp:** MVP — każdy; pełna — Operator, Weryfikator (+ zatwierdzanie), Obserwator i Administrator (tylko odczyt).

#### 3.3.1. Układ (desktop 1440, docelowy z akcjami po MVP)

```
┌ nagłówek aplikacji ─────────────────────────────────────────────────────────┐
├ szyna 72 ┬ pasek dokumentu (okruszki, nazwa, klasa, status, akcje) ──────────┤
│          ├──────────── PDF (50%) ────────────┬─── Dane (50%) ────────────────┤
│          │ pasek: miniatury | str. 1/12 |    │ zakładki: Formularz | JSON |  │
│          │ − 100% + | „Tekst strony”         │ Dowody | (pełna) Historia     │
│          │                                    │ baner klasyfikacji           │
│          │ [strona z podświetleniem dowodu]   │ grupy pól z dowodami          │
│          │                                    │                               │
│          ├────────────────────────────────────┴───────────────────────────────┤
│          │ pasek akcji (przyklejony): Zapisz korektę · Zatwierdź · Pobierz JSON│
└──────────┴─────────────────────────────────────────────────────────────────────┘
```

Rozdzielacz między panelami jest przeciągalny (min. 360 px każdy panel) i obsługiwany klawiaturą (fokus na rozdzielaczu, ←/→ co 5%) [PROP].

#### 3.3.2. Pasek dokumentu (od lewej)

1. Okruszki: „Sprawy / {sprawa} / {plik}”.
2. Nazwa pliku wejściowego (H1, monospace nie — zwykły krój): np. „odwolanie.pdf”.
3. Etykieta klasy: „Odwołanie do KIO”; przycisk „Zmień” wyłącznie E1 (otwiera okno §3.3.8). W P0 przycisku nie ma.
4. Etykieta statusu (§3.2.1).
5. Etykieta wersji wyniku: „Wynik v1 · silnik” lub „Wynik v2 · korekta: {użytkownik}” (po MVP; w MVP „Wynik v1 · silnik”).
6. Skrót „Gotowość i modele” (§3.1.2), rewizja kontraktu i zestaw YAML użyte dla wyniku. Nawigacja między dokumentami sprawy: „‹ Poprzedni” / „Następny ›” + „{k} z {n}”.

#### 3.3.3. Panel PDF

- Pasek narzędzi: przycisk „Miniatury” (przełącza kolumnę miniatur 96 px), „Strona {k} z {n}” (pole liczbowe + strzałki), „Pomniejsz”, „{100}%”, „Powiększ”, „Dopasuj do szerokości”, przełącznik „PDF | Tekst strony” / “PDF | Page text”.
- Miniatury mają znacznik źródła tekstu: „T” (tekst cyfrowy), „OCR” (ukryty lub wykonany), „M” (mieszana), „?” (nierozpoznana) — dla dokumentu mieszanego widać, które strony były skanem [ZESP: wymagania 0.5.0, UZP-02] [PROP: forma].
- Widok „Tekst strony”: tekst odczytany przez silnik (warstwa tekstowa lub OCR), z tymi samymi podświetleniami. To dostępna alternatywa dla obrazu PDF [WCAG 1.1.1] i element transparentności (pokazuje, co „widział” silnik) [PROP].
- Podświetlenie dowodu: prostokąt w kolorze `evidence-bg` z obramowaniem `evidence-border` 2 px; aktywny dowód dodatkowo ma znacznik z numerem pola po lewej. Bez geometrii pokazujemy stronę i cytat oraz „Położenie przybliżone. Brak dokładnej geometrii dowodu.” / “Approximate location. Exact evidence geometry is unavailable.” Nie wybieramy automatycznie pierwszego wystąpienia: lista znalezionych wystąpień wymaga wyboru operatora [PIPE; REC]. MVP pokazuje stronę i fragment bez obrysu.
- Strony skanowane: dopiero po wykonanym OCR nad stroną etykieta „Skan — tekst z OCR” / “Scan. OCR text”; przy słabym OCR: „Niska jakość odczytu OCR na tej stronie” (ostrzeżenie).

#### 3.3.4. Panel danych — baner klasyfikacji (nad zakładkami)

Dla klas obsługiwanych:

> **Rozpoznano: Odwołanie do KIO** · na podstawie treści dokumentu
> Przycisk-link „Dlaczego?” / “Why?” → wysuwany panel:
> - „Znalezione sygnały: »odwołanie« (4), »Krajowa Izba Odwoławcza« (2), »zamawiający« (7)…” (z YAML `klasyfikacja.sygnaly`) [DANE: eksperyment YAML]
> - „Decyzja: {reguły | model językowy | reguły + model}”
> - „O klasyfikacji rozstrzyga treść, nie nazwa pliku.” [ORG: README; PIPE] Liczby trafień to przesłanki, nie ustalony próg poprawności. Pokaż również sygnały przeciwne, wersję konfiguracji i przyczynę nierozstrzygnięcia.

#### 3.3.4a. Diagnoza dokumentu, strony i regionu (pełny panel: E1)

[ADR; PIPE; PROP] Przycisk „Diagnoza” / “Diagnostics” obok „Dlaczego?” otwiera panel. Na telefonie jest w „Więcej”. Poziomy „Dokument / Strona / Region”, wybór strony i regionu; klik znacznika miniatury otwiera właściwy poziom. Klasa biznesowa jest osobnym wierszem i nie zmienia typu odczytu.

Panel pokazuje: „Źródło tekstu”, „Typ strony” (tekstowa / skan / mieszana / pusta / nierozpoznana), „Orientacja” (oryginalna i zastosowana korekta), „Jakość odczytu”, „Pewność diagnozy”, „Sygnały decyzji”, „Decyzja OCR”, „Kody odstępstw”. Źródła regionu: **tekst cyfrowy / OCR ukryty / obraz z tekstem / obraz dekoracyjny / tekst jako krzywe / pusty**. Strona i dokument agregują wiele źródeł, bez sprowadzania mieszanej strony do jednego „T”. Dla OCR wykonanego pokazujemy metodę, jakość i wersję; warstwa ukryta może zostać odrzucona jako niewiarygodna.

Przykład: „Strona 2, region R3 · obraz z tekstem · obrót 90° → 0° · jakość niska · pewność diagnozy: niska · OCR ponowiony · sygnał: tekst warstwy niezgodny z obrazem · zla_warstwa_ocr”. Pewność diagnozy jest oddzielna od pewności klasy, wartości i dowodu; brak skalibrowanej miary: „Nie oceniono”, nigdy wymyślony procent. Nieznany typ: „Nierozpoznany. Wymaga przeglądu”. Brak sygnałów: „Silnik nie przekazał uzasadnienia”.

Stany panelu: KS-3 w czasie ładowania; KS-2 z „Ponów” przy błędzie; „Brak diagnozy dla tego regionu” przy niepełnych danych; KS-1 przy odmowie. Na ≥1024 panel 400 px jako szuflada, na ≤768 pełna szerokość. W MVP podstawowe metadane i kody w rozwijanych szczegółach; pełne drzewo regionów po MVP.

#### 3.3.4b. Grupy z wieloma obrysami (E1)

[KARTY; PIPE; PROP] Grupa logiczna (podmiot) ma stabilne ID, np. G2, niezależne od kolejności pól JSON. Może mieć wiele obszarów na jednej lub kilku stronach. Karty wykazały **446/622 spójnych grup** przy użytej heurystyce; to lokalizacja znanych referencji, nie F1 ani walidacja przypisania ról.

Po MVP przełącznik „Oznaczenia: pola / grupy”. Wszystkie obrysy grupy mają wspólny kolor, numer G2 i numer obszaru, np. „G2 · 2/3 · str. 4”. Legenda zawiera rolę, liczbę obszarów i strony. „Poprzedni obszar / Następny obszar” przechodzi także między stronami. Kolor jest uzupełnieniem numeru i wzoru linii, nigdy jedyną informacją. Aktywne obramowanie używa `evidence-border`; nieaktywne kolory wymagają kontrastu ≥3:1 na białej stronie.

Przy kolizji z cudzą grupą pokazujemy oddzielne obrysy pól i komunikat „Grupy nakładają się. Pokazano oznaczenia pól.” Pozostają ID grupy, powiązania pól i lista obszarów. Nie rysujemy jednej dużej ramki obejmującej cudze dane. Częściowa geometria: „Zlokalizowano {k} z {n} pól grupy”; reszta ma stronę i fragment lub jawny brak lokalizacji. Bez geometrii działa dowód tekstowy z §3.3.3.

#### 3.3.5. Zakładka „Formularz” / “Form” (domyślna)

Pola zgrupowane według obiektów JSON. Grupa = karta z nagłówkiem: nazwa PL + klucz JSON monospace drobno, np. „Odwołanie · `OdwolanieKIO`”. Listy (np. `Odwolujacy`) jako podkarty „Odwołujący 1 z 1”, z przyciskiem „Dodaj odwołującego” (po MVP) i „Usuń” w każdej podkarcie (obie akcje tylko E1; P0 wyłącznie odczyt list).

Wiersz pola (od lewej / od góry na wąskim):

1. Etykieta (PL/EN wg §3.3.6) + klucz JSON drobno monospace (`numer_ted`).
2. Wartość w formacie wyświetlania (np. data `13.10.2025`, kwota `10 000,00 zł`, rachunek grupowany `68 4382 2304 9992 …`). Pod spodem, drobno, wartość dokładnie jak w JSON, jeśli różni się zapisem: „JSON: `2025-10-13`”.
3. Znacznik stanu pola:

| Stan pola (PL / EN) | Wygląd | Kiedy |
|---|---|---|
| Z dokumentu / From document | ikona cytatu, `primary` | wartość + dowód |
| Brak w dokumencie / Not in document | kreska, `neutral-strong`; wartość pokazana jako „brak (null)” | silnik ocenił, że pola nie ma; zgodnie z UZP-04 nie zmyślamy [ORG: FAQ] |
| Wyliczone / Derived | ikona funkcji `f`, `info` | np. `czynnosc_opis` z `czynnosc_powod_id`, `przez-pelnomocnika` z obecności pełnomocnika, `prowadzacy_postepowanie` = null przy jednym zamawiającym [DANE: eksperyment YAML] |
| Do sprawdzenia / Check this | trójkąt, `warning` | format niezgodny z YAML, słaby OCR, kilku kandydatów |
| Poprawione / Edited | ołówek, `accent` | zmienione przez pracownika |

Dla wartości `null` obowiązuje dodatkowy, niezależny powód braku [ADR; PIPE]:

| Powód PL / EN | Treść przy polu | Wygląd |
|---|---|---|
| Brak / Missing | „Nie znaleziono informacji. Sprawdzone strony: {lista}.” | kreska + neutral |
| Nie dotyczy / Not applicable | „Nie dotyczy: {reguła i przesłanki}.” | przekreślone koło + neutral |
| Nieczytelne / Unreadable | „Treść jest obecna, ale nie można jej odczytać.” | oko przekreślone + warning |
| Sprzeczne / Conflicting | „Znaleziono sprzeczne wartości. Porównaj dowody.” | dwie strzałki + warning |
| Nieprzetworzone / Not processed | „Nie przetworzono stron/regionów: {lista}.” | zegar + danger |

Każdy powód jest zapisany poza ocenianym JSON; `null` zgodny z kontraktem może być eksportowany [ADR]. Konflikt z walidatorem niedopuszczającym `null` obsługujemy według dwóch wariantów §3.3.5a, do decyzji użytkownika; nie wybieramy polityki w projekcie UI. Bez pustego tekstu i wartości zastępczej. Nieprzetworzona treść nie może dostać etykiety „Brak”. Filtr „Braki ({n})” obejmuje pięć powodów i pozwala je zawęzić. „Do sprawdzenia” jest osobną flagą, również dla wartości obecnej. Pełny oznacza zakończoną ocenę pól, także uzasadnione `null`; częściowy wymienia wszystkie braki i ograniczenia pokrycia.

4. Dowód (zwinięty do jednej linii): „Str. 1 · Pruszków, dnia 13.10.2025 r.” + „Źródło: tekst PDF / OCR” i osobno metoda „reguła / model / wyliczone”. Przycisk „Pokaż dowód” → PDF przewija się do strony (po MVP także obrys, jeśli geometria jest dostępna); czytnik ekranu ogłasza „Pokazano dowód: strona 1”.
5. Dla stanu „Brak w dokumencie” już w P0: „Nie znaleziono informacji. Sprawdzone strony: {lista}”. Lista nieprzetworzonych stron osobno, także w P0. Brak raportu pokrycia: „Silnik nie przekazał listy sprawdzonych stron”; nie sugerujemy, że sprawdzono cały PDF. Regiony i ich drzewo dopiero E1.
6. Dla „Wyliczone”: „Reguła: ze_slownika, wersja {v}. Przesłanka: `czynnosc_powod_id` = 9” z linkiem do dowodu kodu. Źródło cytatu „tekst PDF / OCR” pokazujemy niezależnie od metody „reguła / model / wyliczone”.
7. (po MVP) „Inni kandydaci ({n})” — rozwijana lista alternatywnych wartości z dowodami i przyciskiem „Użyj tej wartości” [PROP].
8. Po MVP przycisk „Edytuj” (ikona ołówka; etykieta dostępna „Edytuj pole {etykieta}”).

Nad grupami: filtr segmentowy „Wszystkie pola | Do sprawdzenia ({n}) | Braki ({n})” i licznik „Wypełniono {k} z {n} pól”.

#### 3.3.5a. Eksport przy brakach i błędach (dwa warianty do decyzji)

[PROP; ocena 6.1; U-Q13/U-Q14] UI nie rozstrzyga polityki. Wybór należy do użytkownika przed implementacją eksportu; do odpowiedzi mentora oba warianty muszą być reviewowalne w makiecie F61. Wspólne: braków nie uzupełniamy fikcyjną wartością, dowody i raport walidacji są osobno, wynik obcy to `{}` pod nazwą bazową PDF. Nieprzetworzone strony pozostają jawne.

| Sytuacja | Wariant A: ścisła walidacja eksportu | Wariant B: jawny eksport konkursowy mimo braków |
|---|---|---|
| Pełny lub częściowy, wszystkie wartości i `null` dopuszczone kontraktem | „Pobierz {plik}.json”; przy częściowym ostrzeżenie i lista braków. | Tak samo. |
| Brak/nieczytelność, `null` niedopuszczony przez schemat | Status „Częściowy”, baner „Brak wartości niezgodny z kontraktem: {ścieżki}”. „Pobierz JSON” nieaktywny; raport i dowody dostępne. JSON diagnostyczny tylko jako jawnie oznaczony podgląd poza wynikiem do oceny. | Status „Częściowy”, baner „Eksport konkursowy zawiera null niezgodny ze schematem: {ścieżki}. Wynik może zostać odrzucony przez ewaluator”. Akcja „Pobierz JSON z brakami” otwiera podsumowanie konfliktów i wymaga świadomego potwierdzenia; zapis zachowuje klucze/typy pozostałych pól i nazwę bazową. Nie oznaczamy go jako zgodnego z kontraktem. |
| Błąd techniczny, także brak wymaganego OCR bez podstaw do wyniku | „Nie zapisano pliku wynikowego”; pobranie JSON nieaktywne, dostępny raport i ponowienie. | Wyłącznie jeśli użytkownik osobno zatwierdzi regułę U-Q14: akcja „Pobierz zastępcze {} do oceny” z ostrzeżeniem „To znacznik awarii, nie wynik obcy”. Powstaje osobny artefakt eksportu; stan błędu i brak wyniku ekstrakcji pozostają. Bez tej decyzji brak pliku, także w wariancie B. |
| Niejednoznaczny / wiele dokumentów | Baner i brak eksportu do ustalenia kontraktu. | Tak samo; wariant B nie rozstrzyga U-Q12. |

Żaden wariant nie jest domyślnie zatwierdzony. Ekran pokazuje „Polityka eksportu: nieustalona” i blokuje pobranie objęte sporem, pozwalając pobrać bezsporne wyniki, dowody i raport. Po decyzji pokazuje nazwę wybranej polityki. To ustawienie wdrożenia, bez dodatkowego przełącznika użytkownika końcowego w P0. Jeśli zostanie dopuszczone zastępcze `{}`, podsumowanie eksportu E2 osobno liczy wyniki obce i znaczniki awarii, a raport zawiera przyczynę każdego pliku. Nie wolno przedstawiać niezgodnego eksportu jako spełnienia wymogu ścisłego JSON.

#### 3.3.6. Etykiety pól (PL / EN) [PROP; klucze: DANE]

Proponuję dodać do YAML klasy pole `etykieta: {pl, en}` (patrz pytania otwarte); do tego czasu etykiety są w plikach tłumaczeń UI.

**Odwołanie do KIO / Appeal** (`odwolanie`)

| Klucz | PL | EN | Edytor |
|---|---|---|---|
| `OdwolanieKIO` (grupa) | Odwołanie | Appeal | — |
| `data` | Data odwołania | Appeal date | data |
| `czynnosc_dzien` | Data zaskarżonej czynności | Date of challenged action | data |
| `czynnosc_powod_id` | Zaskarżona czynność (kod) | Challenged action (code) | lista 1–12 ze słownika [DANE: `czynnosc_powod_id_dict.md`] |
| `czynnosc_opis` | Zaskarżona czynność (opis) | Challenged action (description) | tylko odczyt, wyliczane |
| `miejscowosc` | Miejscowość | Place | tekst |
| `Odwolujacy[]` (grupa) | Odwołujący | Appellant | lista |
| `krs` | KRS | KRS number | 10 cyfr |
| `nazwa` | Nazwa | Name | tekst |
| `nip` | NIP | Tax ID (NIP) | 10 cyfr |
| `regon` | REGON | REGON | 9 lub 14 cyfr |
| `przez-pelnomocnika` | Działa przez pełnomocnika | Represented by attorney | tylko odczyt (wyliczane), Tak → `1`, Nie → `0`, brak → `null` |
| `pelnomocnik.imie_nazwisko` | Pełnomocnik — imię i nazwisko | Attorney — full name | tekst |
| `pelnomocnik.nazwa` | Pełnomocnik — kancelaria | Attorney — firm | tekst |
| `pelnomocnik.mail` | Pełnomocnik — e-mail | Attorney — e-mail | e-mail |
| `Zamawiajacy[]` (grupa) | Zamawiający | Contracting authority | lista |
| `prowadzacy_postepowanie` | Prowadzi postępowanie | Lead authority | trójstan: „nie dotyczy (null) / Tak (1) / Nie (0)” |
| `ZamowieniePubliczne` (grupa) | Zamówienie | Procurement | — |
| `numer_bzp` | Numer ogłoszenia BZP | BZP notice number | tekst, wzorzec `RRRR/BZP########` z opcjonalnym `/##`, np. `2026/BZP00999778/01` |
| `numer_postepowania` | Numer postępowania | Procedure reference | tekst |
| `numer_ted` | Numer TED | TED number | tekst, `NNNNNN-RRRR` |
| `tytul` | Tytuł zamówienia | Contract title | tekst wielowierszowy |

Pomoc pod `OdwolanieKIO.czynnosc_dzien`, `czynnosc_powod_id` i `czynnosc_opis`: „Dotyczy wyłącznie pierwszego zarzutu.” / “Based only on the first allegation.” Nie wybieramy dowolnej daty z treści. Pod datą odwołania: „Data pisma z nagłówka pierwszej strony”.

Współdzielone pola zamawiającego mają pełne ścieżki: `Zamawiajacy[].nazwa` (Nazwa / Name), `Zamawiajacy[].krs` (KRS / KRS number), `Zamawiajacy[].nip` (NIP / Tax ID), `Zamawiajacy[].regon` (REGON / REGON), `Zamawiajacy[].prowadzacy_postepowanie` (Prowadzi postępowanie / Lead authority). Edytory i walidacja identyfikatorów jak u odwołującego; Tak → `1`, Nie → `0`, nie dotyczy → `null`. Liczby identyfikacyjne przechowujemy jako tekst, z zerami wiodącymi. Format BZP dopuszcza oba warianty; aktualny kontrakt określa normalizację, bez samowolnego obcinania `/##`.

**Pełnomocnictwo / Power of attorney** (`pelnomocnictwo`)

| Klucz | PL | EN | Edytor |
|---|---|---|---|
| `mocodawca[]` (grupa) | Mocodawca | Principal | lista |
| `data.typ` | Rodzaj mocodawcy | Principal type | wybór: „osoba prawna” (`osoba_prawna`) / „osoba fizyczna” (`osoba_fizyczna`) |
| `data.nazwa` | Nazwa | Name | tekst |
| `data.imie_nazwisko` | Imię i nazwisko (osoba fizyczna) | Full name (individual) | tekst; aktywne tylko dla osoby fizycznej |
| `data.krs` | KRS | KRS number | 10 cyfr |
| `data.nip` | NIP | Tax ID (NIP) | 10 cyfr |
| `podpisujacy[].imie_nazwisko` | Podpisujący | Signatory | lista tekstów |
| `pelnomocnicy[]` (grupa) | Pełnomocnicy | Attorneys | lista |
| `imie_nazwisko` | Imię i nazwisko | Full name | tekst (mianownik) |
| `pesel` | PESEL | PESEL (national ID) | 11 cyfr, tekst; **maskowany** |

**Potwierdzenie przelewu / Transfer confirmation** (`przelew`)

| Klucz | PL | EN | Edytor |
|---|---|---|---|
| `przelew_bankowy` (grupa) | Przelew | Bank transfer | — |
| `data_operacji` | Data operacji | Transaction date | data |
| `kwota` | Kwota | Amount | liczba, PLN |
| `z_rachunku` | Z rachunku | From account | 26 cyfr, tekst; **częściowo maskowany** |
| `na_rachunek` | Na rachunek | To account | 26 cyfr, tekst; maskowanie wg §1.4 |
| `numer_transakcji` | Numer transakcji | Transaction ID | tekst |
| `tytul` | Tytuł przelewu | Transfer title | tekst wielowierszowy |

#### 3.3.7. Edycja pola (korekta, E1)

- „Edytuj” zamienia wartość na pole edycji odpowiedniego typu (tabela wyżej) z przyciskami „Zastosuj” / “Apply” i „Anuluj” / “Cancel”; Esc = Anuluj, Enter = Zastosuj (w polu wielowierszowym Ctrl+Enter).
- Opcja „Ustaw brak (null)” / “Set to empty (null)” przy polach dopuszczających null [DANE].
- Walidacja z YAML (format, typ, zakres) na bieżąco [DANE: eksperyment YAML]. Komunikaty:
  - „NIP musi mieć 10 cyfr.” / “Tax ID must have 10 digits.”
  - „Rachunek musi mieć 26 cyfr (bez spacji).” / “Account number must have 26 digits.”
  - „Data w formacie DD.MM.RRRR.” / “Use date format DD.MM.YYYY.”
  - „Numer TED w formacie NNNNNN-RRRR, np. 641651-2025.”
  - ogólny z YAML: „Wartość nie pasuje do formatu: {opis formatu}.”
  Błąd: czerwona ramka + ikona + tekst pod polem, powiązany z polem (`aria-describedby`); „Zastosuj” zablokowany.
- Zmiana `czynnosc_powod_id` od razu przelicza `czynnosc_opis` (widoczne w podglądzie JSON).
- Dowód po korekcie: oryginalny dowód pozostaje przypisany starej wartości z dopiskiem „Dowód wartości silnika: {stara}”. Nowa wartość ma własny wskazany dowód albo „Korekta operatora bez nowego dowodu”. (pełna) Opcjonalnie „Wskaż w dokumencie” — zaznaczenie fragmentu w widoku „Tekst strony” jako nowego dowodu [PROP].
- Niezapisane zmiany: pasek akcji pokazuje „Niezapisane zmiany: {n}” i przycisk „Zapisz korektę” / “Save correction”. Wyjście ze strony uruchamia okno i akcje opisane poniżej.
- Zapis korekty tworzy nową wersję wyniku (§4.3); wynik silnika zostaje bez zmian.

[PROP; REC-3] „Zastosuj” zmienia wyłącznie szkic w sesji. „Zapisz korektę” to jedyny zapis trwały, atomowy i wersjonowany. Stan „Zapisywanie…” / “Saving…” blokuje powtórzenie żądania; potwierdzenie backendu daje „Zapisano v{n}”. Błąd: „Nie zapisano. Szkic zachowano w tej sesji.” / “Not saved. Your draft is kept in this session.” + „Ponów zapis”. Nie zamykamy edytora przy błędzie walidacji.

Przed zatwierdzeniem, pobraniem, kopiowaniem JSON lub wyjściem, gdy istnieje szkic: okno „Masz niezapisane zmiany” / “You have unsaved changes”; tekst „Eksport i zatwierdzenie dotyczą zapisanej wersji v{n}. Wybierz, co zrobić ze szkicem.” Akcje: „Zapisz i kontynuuj”, „Odrzuć szkic i kontynuuj”, „Zostań”. Błąd zapisu zatrzymuje zamiar; po sukcesie kontynuacja wskazuje nową wersję. Nie ma cichego eksportu poprzedniej wersji. Przeglądarka przy zamknięciu karty używa ostrzeżenia systemowego, bez obietnicy zachowania szkicu po zamknięciu. Konflikt równoległego zapisu: „Wynik zmienił się na serwerze. Porównaj wersje”, bez nadpisania.

#### 3.3.8. Zmiana klasy (E1)

Okno dialogowe „Zmień rodzaj dokumentu” / “Change document type”:

- „Silnik rozpoznał: {klasa}. Wybierz właściwy rodzaj — dane zostaną wyodrębnione ponownie według nowej klasy.”
- Opcje (radio): „Odwołanie do KIO”, „Pełnomocnictwo”, „Potwierdzenie przelewu”, „Dokument spoza zakresu (wynik: pusty JSON {})”, (+ klasy dodane w YAML).
- Przyciski: „Zmień i wyodrębnij ponownie” / “Change and re-extract”, „Anuluj”. Ręczne wskazanie „obcy” jest audytowaną decyzją operatora, nigdy skutkiem błędu konfiguracji lub odczytu.
- Po zmianie: status „Analizowanie: Ekstrakcja”, a potem nowa wersja wyniku z dopiskiem „klasa zmieniona ręcznie”.

#### 3.3.9. Zakładka „JSON”

- Edytor kodu tylko do odczytu, kolorowanie składni, numery linii, zawijanie wyłączone (przewijanie poziome wewnątrz panelu).
- Nad nim: przełącznik „Wynik silnika | Wynik bieżący” (gdy są korekty), przyciski „Kopiuj” / “Copy” („Skopiowano” przez 2 s, ogłaszane), „Pobierz {nazwa}.json” / “Download {name}.json”.
- Informacja pod spodem: „Zapisany wynik v{n}. Dowody są osobno.” / “Saved result v{n}. Evidence is stored separately.” Przy maskowaniu: „Podgląd zamaskowany. Różni się od ocenianego pliku.” / “Masked preview. Differs from the evaluated file.” [ZESP: ADR-002 pkt 10]
- Klik w linię z wartością zaznacza odpowiadające pole w zakładce „Formularz” i podświetla dowód w PDF [PROP].
- Polityka §1.4 obejmuje podgląd, „Kopiuj” i pobranie. „Kopiuj zamaskowany podgląd” nie kopiuje pełnych wartości. Przed pobraniem: „Pobierz wynik v{n} · silnik/korekta”. Maskowanego podglądu nie oznaczamy jako wynik do oceny. MVP z syntetycznymi danymi pokazuje i eksportuje ten sam zapisany wynik silnika.

#### 3.3.10. Zakładka „Dowody” / “Evidence”

P0: tabela „Pole” (klucz), „Wartość”, „Strona”, „Fragment”, „Źródło tekstu” (warstwa tekstowa / OCR), „Metoda” (reguła / model / wyliczone). Przycisk „Pobierz dowody (JSON)”. Ten widok to czytelna postać pliku z `evidence/` [ZESP: ADR-002 pkt 10]. **Pobranie dowodów jest P0**, osobno jako `evidence/{nazwa_bazowa}.json`, z identyfikatorem dokumentu i wyniku, cytatami, źródłem PDF/OCR, komponentem OCR i flagą shim, regułami/przesłankami oraz raportem braków i pokrycia stron. Dla błędu pobieramy tylko istniejące dowody i raport, z etykietą „Materiał częściowy, analiza nieudana”; brak dowodów ma jawny komunikat. Bez dopisywania metadanych do ocenianego JSON. ZIP dowodów wielu plików to E2.

#### 3.3.11. Zakładka „Historia” (pełna)

Lista wersji wyniku: „v3 · zatwierdzono · {Weryfikator} · {data}”, „v2 · korekta 2 pól · {Operator} · {data}”, „v1 · silnik {wersja}, model {nazwa}, klasy {wersja} · {data}”. Przycisk „Porównaj z poprzednią” → S05.

#### 3.3.12. Pasek akcji (przyklejony na dole panelu danych)

- „Zapisz korektę” (E1, aktywny przy niezapisanych zmianach),
- „Zatwierdź wynik” / “Approve result” (główny; po MVP — Weryfikator, nieaktywny przy własnej korekcie z podpowiedzią „Wynik poprawiony przez Ciebie zatwierdza inna osoba.”),
- po zatwierdzeniu: „Zatwierdzono {data} · Cofnij zatwierdzenie”,
- „Pobierz JSON”.

Pasek P0 zawiera „Pobierz JSON v{n}” i „Pobierz dowody”; w pełnej wersji wszystkie akcje wskazują zapisaną wersję i przechodzą przez kontrolę szkicu (§3.3.7). Gdy są pola „Do sprawdzenia”, „Zatwierdź” pokazuje okno: „{n} pól wymaga sprawdzenia. Czy na pewno zatwierdzić?” — „Zatwierdź mimo to”, „Pokaż pola”.

#### 3.3.13. Maskowanie danych osobowych (E3)

[PROP; REC-1] Obowiązuje §1.4 dla wszystkich wartości, cytatów i pochodnych dokumentu. Przykład PESEL: `85•••••••47`, rachunek: `05 •••• •••• •••• •••• •••• 5024`; nazwiska jako inicjały. Przyciski „Pokaż dane” / “Show data” i „Ukryj dane” / “Hide data”. Odsłonięcie wymaga autoryzacji backendu i wpisu audytu, wygasa przy wyjściu z dokumentu. Odmowa ma własną ramkę F35. Brak flagi nie jest obchodzony przez pobranie PDF, schowek ani historię.

#### 3.3.14. Stany widoku S03

| Stan | Co widać |
|---|---|
| Ładowanie | szkielet PDF (szara strona) + szkielet grup pól; KS-3 |
| W trakcie analizy | panel danych: krokownik etapów „Odczyt tekstu ✔ → OCR (strony 2–3) … → Klasyfikacja → Ekstrakcja → Walidacja”; PDF już dostępny |
| Pełny | jak opisano; tekst i ikona z §3.2.1 |
| Częściowy | status i lista braków z §3.2.1; filtr domyślnie „Do sprawdzenia ({n})”, jeśli są ostrzeżenia; inaczej „Braki ({n})” |
| **Obcy dokument** | panel danych zamiast formularza: ikona okręgu przekreślonego, H2 „Dokument spoza zakresu” / “Not a supported document”, tekst: „Treść nie pasuje do żadnej aktywnej klasy: {nazwy klas z konfiguracji}. Zgodnie z zasadami zapisano pusty wynik {} pod nazwą {plik}.json.” / “The content does not match any supported class. An empty result {} was saved as {file}.json, as required.”; sekcja „Dlaczego?” (najbliższe klasy i liczba sygnałów, np. „Pełnomocnictwo: 1 z 3 wymaganych sygnałów”); przyciski „Zmień rodzaj dokumentu” (E1) i „Pobierz {plik}.json” (P0); zakładka JSON pokazuje `{}` |
| **Błąd techniczny** | panel danych: ikona `danger`, H2 „Nie udało się przetworzyć dokumentu” / “The document could not be processed”, tekst: „To błąd techniczny, a nie wynik analizy. Nie zapisano wyniku ekstrakcji. Eksport przy awarii: {wybrana polityka z §3.3.5a lub nieustalona}.” / “This is a technical error, not an analysis result. No extraction result was saved. Export follows the selected policy (E1).”; szczegóły (rozwijane): „Etap: Ekstrakcja · Przyczyna: model językowy nie odpowiedział w czasie {60} s · Kod: LLM_TIMEOUT · {data}”; przyciski „Ponów analizę” / “Retry analysis”, „Kopiuj szczegóły błędu”. Brak przełączania na stary wynik z pamięci podręcznej [ZESP: ADR-002 pkt 12]. Jeśli istnieje wcześniejsza wersja wyniku tego samego dokumentu, link „Zobacz poprzednią wersję (v{n} z {data})” jest dostępny, ale jako przeszła wersja, nie jako wynik bieżący [PROP] |
| Niejednoznaczny | P0: F40, prosty baner z powodem, bez osobnego panelu. E1: panel kandydatów klas, sygnały za/przeciw i zakres odczytu; „Przejrzyj dowody”; po MVP „Wybierz klasę i ponów”. Bez eksportu JSON. |
| Wiele dokumentów | P0: F41, prosty baner z zakresem stron, jeśli znany, bez wyboru segmentów. E1: lista segmentów z zakresem stron oryginału i klasami; wybór segmentu filtruje dowody, nie scala danych; „Kontrakt eksportu wielu dokumentów nieustalony”. |
| PDF nie do wyświetlenia (uszkodzony, zaszyfrowany) | panel PDF: „Nie można wyświetlić tego pliku PDF. Plik może być uszkodzony lub zabezpieczony hasłem.” + „Pobierz oryginał” wyłącznie zgodnie z §1.4; bez flagi komunikat odmowy |
| Brak uprawnień / nie znaleziono | KS-1 / KS-4 |

#### 3.3.15. Breakpointy S03 (P0: 1440; pozostałe E1)

| Szerokość | Układ |
|---|---|
| 360 | nagłówek dokumentu w dwóch liniach (nazwa pliku skrócona z wielokropkiem, pod nią klasa i status); **zakładki na całą szerokość: „Dokument \| Dane \| JSON”** (Dowody i Historia w menu „Więcej”); klik w dowód przełącza na „Dokument”, przewija do podświetlenia i pokazuje pływający przycisk „‹ Wróć do pola {etykieta}”; pasek akcji na dole: „Pobierz JSON” (MVP), po MVP „Zatwierdź” + menu „Więcej” (Zapisz korektę, Pobierz JSON, Zmień rodzaj, Diagnoza); miniatury jako poziomy pasek nad stroną |
| 768 | jak 360, ale zakładki „Dokument \| Formularz \| JSON \| Dowody”; w orientacji poziomej (1024×768) układ dwupanelowy jak 1024 |
| 1024 | dwa panele 50/50, nawigacja jako szyna 72 px; miniatury domyślnie ukryte |
| 1440 | dwa panele 50/50 (rozdzielacz przeciągalny); szyna 72 px; miniatury domyślnie widoczne; zakładka „Historia” dopiero E1 |

#### 3.3.16. Skróty klawiszowe S03 [PROP]

Skróty jednoklawiszowe działają tylko, gdy fokus jest na liście pól, i można je wyłączyć w ustawieniach [WCAG 2.1.4].

| Skrót | Działanie |
|---|---|
| ↑ / ↓ (na liście pól) | poprzednie / następne pole; PDF podąża za dowodem |
| Enter (na kontenerze pola, po MVP) | edytuj; na przycisku dowodu pokaż dowód |
| Esc | anuluj edycję / zamknij panel |
| Ctrl+S / ⌘S | zapisz korektę |
| Alt+1 / 2 / 3 / 4 | zakładki desktop: Formularz / JSON / Dowody / Historia (ostatnia po MVP); telefon: Dokument / Dane / JSON, Alt+4 bez przypisania; tablet: Dokument / Formularz / JSON / Dowody |
| Alt+D | przenieś fokus do dokumentu PDF |
| Alt+N / Alt+P | następny / poprzedni dokument w sprawie |
| PageUp / PageDown (w PDF) | strona wstecz / dalej |
| ? | lista skrótów (okno dialogowe „Skróty klawiszowe”) |

Lista pól ma semantykę listy z nagłówkami grup, bez udawania `listbox`. Tab przechodzi do przycisków „Pokaż dowód” i „Edytuj”. ↑/↓ działają tylko na fokusowanym kontenerze pola (przeniesienie fokusu programowo, poza zwykłą kolejnością Tab); w input, textarea, select, edytorze i elementach edytowalnych pozostają natywne. Enter na „Pokaż dowód” otwiera dowód; nie uruchamia edycji. Zakładki mają `tablist`, strzałki zmieniają fokus zakładki, Enter/Spacja aktywuje.

Telefon zapamiętuje aktywne pole, filtr i scroll zakładki Dane. „Wróć do pola {etykieta}” przywraca te wartości i fokus do przycisku dowodu. Po otwarciu klawiatury ekranowej edytowane pole i błąd pozostają w widocznym obszarze; pasek akcji przechodzi w zwykły przepływ. Dolny padding uwzględnia wysokość paska i safe area, a powrót z PDF nie zmienia szkicu. Dotyczy też 320 px.

### 3.4. S04 Sprawy / Ostatnie analizy

**Cel:** znaleźć sprawę. **Dostęp:** po MVP, wg macierzy. Ostatnie wyniki demo są wyłącznie w S01 i tylko z bieżącej sesji.

Treść: H1 „Sprawy” / “Cases”; filtr tekstowy „Szukaj po nazwie sprawy, pliku, NIP lub numerze postępowania”; filtry (pełna): „Status”, „Klasa dokumentu”, „Data od–do”, „Przypisane do mnie”; tabela: „Sprawa”, „Dokumenty” (liczba), „Status” (najgorszy status w sprawie + liczniki), „Utworzono”, „Ostatnia zmiana”, „Odpowiedzialny” (pełna); stronicowanie „{k}–{m} z {n}”.

Stany: pusty — „Brak spraw. Zacznij od nowej analizy.” + przycisk „Nowa analiza”; brak wyników filtra — „Brak spraw spełniających kryteria.” + „Wyczyść filtry”; KS-1..4.

Akcje partii: „Pobierz wyniki partii (ZIP)”, „Pobierz dowody partii”, „Ponów nieudane”; podsumowanie eksportu z §4.7. Filtr „Kody odstępstw” jak S02.

Breakpointy: 360/768 — karty; 1024/1440 — tabela.

### 3.5. S05 Historia wersji i porównanie (pełna)

**Cel:** pokazać, co i kto zmienił; przywrócić wersję. **Dostęp:** wszyscy z dostępem do sprawy; przywracanie — Operator, Weryfikator.

Treść: H1 „Historia: {plik}”; dwie listy wersji:

- „Wersje dokumentu” / “Document versions” — „v2 · {plik} · {skrót SHA-256 8 znaków} · wgrał {użytkownik} · {data}”, „v1 …”. Nowa wersja dokumentu uruchamia nową analizę.
- „Wersje wyniku” / “Result versions” — jak w §3.3.11.

Porównanie: wybór „Porównaj: v{a} ⇄ v{b}”; widok różnic po polach (tabela „Pole | v{a} | v{b}”, zmienione wiersze z tłem `warning-subtle` i ikoną) oraz przełącznik „Różnice w JSON” (dwukolumnowy diff). Przycisk „Przywróć v{a}” tworzy nową wersję (historia się nie cofa) — potwierdzenie „Przywrócenie utworzy wersję v{n+1} z treścią v{a}. Kontynuować?”.

Breakpointy: 360/768 — porównanie jako lista pól z „Było: … / Jest: …”; 1024+ — tabela.

### 3.6. S06 Klasy dokumentów (E1: odczyt, E2: konfiguracja)

**Cel:** pokazać, że klasy i pola są konfiguracją, nie kodem [ORG: 1–20 pkt; „konfiguracja nowych klas … jedynie przez pliki konfiguracyjne”].
**Dostęp:** po MVP, syntetyczne demo do odczytu; w wersji urzędowej zgodnie z §1.3, Konfigurator edycja.

Treść:

1. H1 „Klasy dokumentów” / “Document classes”.
2. Lead: „Każdy rodzaj dokumentu jest opisany jednym plikiem YAML: sygnały rozpoznania, pola, typy, formaty i reguły. Dodanie klasy lub pola korzystającego z istniejących mechanizmów nie wymaga zmiany kodu. Nowy mechanizm wymaga rozszerzenia silnika.” / “Each document type is described by one YAML file … Adding a class or field using existing mechanisms requires no code changes.”
3. Karty klas: nazwa („Odwołanie do KIO”), identyfikator (`odwolanie`), „wersja {n}”, „{n} pól · {k} wyliczanych”, „aktywna”, link „Szczegóły”.
   - Odwołanie do KIO — `odwolanie` — {liczba grup i pól z aktywnego YAML}
   - Pełnomocnictwo — `pelnomocnictwo` — {liczba grup i pól z aktywnego YAML}
   - Potwierdzenie przelewu — `przelew` — {liczba grup i pól z aktywnego YAML}
   - Karta specjalna „Dokument spoza zakresu” — „Wynik: pusty JSON {}. Nie jest konfigurowana.”
4. (pełna) Przycisk „Nowa klasa” / “New class”: „Z szablonu”, „Kopiuj istniejącą”, „Wgraj plik YAML”.

Stany: brak klas — „Błąd konfiguracji. Brak poprawnego zestawu klas. Analiza zablokowana.” / “Configuration error. No valid class set. Analysis blocked.” Nie tworzymy `{}`; błąd wczytania YAML — karta z błędem „Nie wczytano klasy {plik}.yaml: {komunikat walidatora}” (np. „brak normalizatora 'nieistniejacy' w rejestrze” [DANE: eksperyment YAML]).

[PROP; REC-2] Zestaw klas aktywuje się atomowo. Częściowe wczytanie nowego zestawu nie zmienia aktywnego: „Nie aktywowano zestawu. Klasa {id}: {błąd}”. Poprzedni kompletny zestaw może obsługiwać nowe analizy, z jawną wersją. Gdy go nie ma, analiza jest zablokowana w S01/S02, a rozpoczęte zadania z wadliwą konfiguracją mają błąd techniczny, nie „obcy”. Wyniki historyczne nadal wskazują swój zestaw. Celowo mniejszy zakres klas wymaga nowej, poprawnej wersji całego zestawu; nie uznajemy go za cichą degradację.

Breakpointy: 360 — karty w kolumnie; 768 — 2 kolumny; 1024/1440 — 3 kolumny.

### 3.7. S07 Klasa: szczegóły i edytor (E1: odczyt, E2: edycja)

**Cel:** po MVP zobaczyć i zmienić definicję klasy z podglądem efektu.
**Dostęp:** odczyt wszyscy; edycja Konfigurator.

Treść:

1. Okruszki „Klasy dokumentów / {klasa}”; H1 „{Nazwa klasy}”; metadane „`{id}` · wersja {n} · aktywna od {data}”.
2. Zakładki:
   - **„Pola” / “Fields”** — drzewo/tabela: „Ścieżka” (`Odwolujacy[].nip`), „Etykieta”, „Typ” (tekst, liczba, data, lista, obiekt, wybór), „Może być pusty” (tak/nie), „Format”, „Metoda” (reguła / model / wyliczane), „Opis”.
   - **„YAML”** — edytor kodu (po MVP: odczyt, przycisk „Kopiuj” i „Pobierz {id}.yaml”).
   - **„Podgląd formularza” / “Form preview”** — formularz S03 wygenerowany z YAML z przykładowymi wartościami; pod nim „Podgląd JSON” — pusty szablon wyniku z kluczami w kolejności z YAML. Deterministyczny, bez modelu [PROP].
   - **„Test na pliku” / “Test on a file”** (po MVP) — „Wgraj PDF, aby sprawdzić tę klasę bez zapisywania wyniku w sprawie.” → wynik jak w S03 (tylko odczyt).
   - **„Wersje”** (pełna) — lista wersji YAML, autor, data, „Porównaj”, „Aktywuj”.
3. (pełna) Tryb edycji: przycisk „Edytuj YAML”; walidacja na bieżąco, komunikaty z numerem linii: „Linia 14: brak normalizatora 'nieistniejacy' w rejestrze.”; podgląd formularza odświeża się po każdej poprawnej zmianie; przyciski „Zapisz jako wersję {n+1}” (nieaktywny przy błędach), „Odrzuć zmiany”. Po zapisie: „Zapisano wersję {n+1}. Nie jest jeszcze aktywna.” + „Aktywuj” z oknem: „Aktywacja zmienia cały zestaw klas. Nowe analizy będą używać nowego zestawu; trwające zadania i wyniki zachowają poprzedni.” Szczegóły aktywacji w §4.6.
4. Pasek informacyjny przy edycji: „Nowa reguła (np. inny słownik) wymaga funkcji w rejestrze silnika. Dostępne funkcje: ze_slownika, obecnosc, null_gdy_lista_jednoelementowa.” [DANE: eksperyment YAML — granica „bez kodu”]

Breakpointy: 360 — zakładki przewijane; edytor YAML tylko do odczytu (edycja na telefonie wyłączona z komunikatem „Edycja YAML jest dostępna na większym ekranie.” [PROP]); 768 — edycja dozwolona, podgląd pod edytorem; 1024/1440 — edytor i podgląd obok siebie (60/40).

### 3.8. S08 Jak to działa / How it works (E1; karta modeli już w P0)

**Cel:** transparentność procesu i informacje dla jury (model, region, rozmiar) [ORG: transparentność; README — moc modelu, serwery w UE/EOG].
**Dostęp:** każdy, także bez logowania (pełna).

Treść:

1. H1 „Jak to działa” / “How it works”.
2. Schemat etapów (poziomy na desktopie, pionowy na telefonie; każdy krok to karta z numerem): „1. Odczyt tekstu z PDF” → „2. Diagnoza stron i regionów, OCR według potrzeby” → „3. Rozpoznanie rodzaju dokumentu” → „4. Grupy, role i kandydaci pól z dowodami” → „5. Scalanie, kontrola pokrycia, normalizacja i walidacja” → „6. Zapis JSON i osobnego raportu braków oraz dowodów”. Pod każdą kartą 1–2 zdania, np. krok 3: „Rodzaj rozpoznajemy po treści, nie po nazwie pliku. Dokument spoza zakresu daje pusty wynik {}.”
3. Tabela rozszerza kartę modeli P0 (§3.1.2), obejmując wszystkie modele, role, największy model, kraje firmy i serwera oraz dostawcę OCR i flagę shim. „Model i przetwarzanie” / “Model and processing”: „Model językowy: {nazwa}”, „Rozmiar: {liczba parametrów}”, „Licencja: {licencja}”, „Dostawca API i region: {dostawca}, {zweryfikowany kraj w Europie}”, „OCR: {komponent}”, „Wersja silnika: {wersja}”, „Wersja konfiguracji klas: {wersja}”. Wartości z backendu.
4. Sekcja „Co oznaczają stany pól” — legenda stanów i pięciu powodów braku z §3.3.5.
5. Sekcja „Czego nie robimy”: „Braki opisujemy osobno, w JSON stosujemy null zgodnie z kontraktem.” [ORG: UZP-04]; „Przy awarii modelu nie podajemy starego wyniku z pamięci — pokazujemy błąd techniczny.” [ZESP: ADR-002 pkt 12]
6. Stopka.

### 3.9. S09 Użytkownicy i role (pełna)

**Dostęp:** Administrator.

Treść: H1 „Użytkownicy i role”; przycisk „Dodaj użytkownika” / “Add user”; filtr „Szukaj po imieniu lub e-mailu”; tabela: „Imię i nazwisko”, „E-mail”, „Role” (etykiety), „Dane osobowe” (Tak/Nie), „Status” (Aktywny / Zablokowany / Zaproszony), „Ostatnie logowanie”, akcje „Edytuj”, „Zablokuj”/„Odblokuj”.
Okno „Dodaj użytkownika”: pola „Imię i nazwisko”, „E-mail”, „Role” (pola wyboru z opisem roli z §1.2), „Uprawnienie »Dane osobowe«” (przełącznik + opis „Pozwala odsłaniać PESEL i pełne numery rachunków. Każde odsłonięcie jest zapisywane.”), przyciski „Zapisz”, „Anuluj”.
Zakładka „Role” — macierz §1.3 tylko do odczytu.
Stany: pusty — „Brak innych użytkowników.”; próba odebrania sobie roli Administratora, gdy jest jedynym — błąd „Musi pozostać co najmniej jeden administrator.”; KS-1.
Breakpointy: 360/768 — karty; 1024+ — tabela.

### 3.10. S10 Dziennik zdarzeń (pełna)

**Cel:** ustalić kto i kiedy wykonał działanie. **Dostęp:** Administrator i Obserwator w swoim zasięgu; pozostali tylko własne wpisy (§1.3–1.4).

H1 „Dziennik zdarzeń” / “Audit log”. Filtry „Rodzaj zdarzenia”, „Użytkownik”, „Data od–do”, „Obiekt”; przyciski „Wyczyść filtry”, „Eksportuj CSV”. Tabela „Czas | Użytkownik | Zdarzenie | Obiekt | Szczegóły”; szczegóły zmiany „Było / Jest” są maskowane przez backend. Zdarzenia: wgranie, analiza, błąd, korekta, zmiana klasy, zatwierdzenie/cofnięcie, eksport, odsłonięcie/odmowa, aktywacja YAML, zmiana ról, logowanie i nieudane logowanie. Wpisy tylko do odczytu.

Pusty: „Brak zdarzeń w tym zakresie”; filtr bez wyników: „Brak zdarzeń spełniających kryteria” + „Wyczyść filtry”; KS-1/2/3. Eksport: „Przygotowywanie CSV…” → „CSV gotowy” albo „Nie udało się przygotować CSV. Ponów”. 320/360/768: karty z etykietami; ≥1024: tabela. Tab wybiera filtry i szczegóły, Enter otwiera szczegóły, Esc zamyka i przywraca fokus.

### 3.11. S11 Ustawienia (pełna)

**Cel:** zmienić preferencje; Administrator także retencję. **Dostęp:** każdy zalogowany do preferencji; Administrator do sekcji systemowych.

H1 „Ustawienia” / “Settings”. Sekcje „Wygląd” (Motyw: Systemowy/Jasny/Ciemny, Gęstość: Wygodna/Zwarta), „Język” (Polski/English), „Dostępność” („Wyłącz skróty jednoklawiszowe”, „Ogranicz animacje”). Preferencje lokalne stosują się od razu, komunikat „Preferencje zapisano na tym urządzeniu”.

Administrator: „Przetwarzanie” tylko do odczytu (model, licencja, region, limity; bez kluczy i tokenów); „Przechowywanie danych” z polem „Usuń sprawy po (liczba dni)”, opisem „Zmiana obejmie także istniejące sprawy”, przyciskiem „Zapisz retencję”. Zakres pochodzi z konfiguracji serwera. Błędna wartość: „Podaj liczbę dni z zakresu {min}–{max}”. Przed zmianą: „Nowa retencja: {n} dni. Do usunięcia przy najbliższym cyklu: {k} spraw” + „Zapisz”/„Anuluj”. Usunięcie według zatwierdzonej polityki trafia do audytu.

Stany: KS-3/2/1 dla sekcji serwera; „Zapisywanie…” → „Zapisano retencję” albo „Nie zapisano. Ponów”; niezapisana retencja przy wyjściu uruchamia okno szkicu. 320/360/768: jedna kolumna; ≥1024: etykiety po lewej, kontrolki po prawej, max. 960 px. Tab po kontrolkach, natywne strzałki w wyborach, fokus na błędzie po nieudanym zapisie. F29.

### 3.12. S12 Logowanie (pełna)

Treść: znak aplikacji; H1 „Zaloguj się” / “Sign in”; pola „E-mail”, „Hasło” (z przyciskiem „Pokaż hasło”); przycisk „Zaloguj”; tekst „Nie masz konta? Poproś administratora.”; błąd: „Nieprawidłowy e-mail lub hasło.” (bez wskazywania, które); po 5 próbach: „Zbyt wiele prób. Spróbuj ponownie za {n} min.” Przełączniki języka i motywu w prawym górnym rogu. Mechanizm uwierzytelniania (np. SSO) — pytanie otwarte.

### 3.13. S13 Deklaracja dostępności (E1; w P0 blok S01/S03)

**Cel:** przedstawić stan sprawdzenia interfejsu i drogę zgłoszenia problemu. **Dostęp:** publiczny; bez danych dokumentów.

H1 „Dostępność” / “Accessibility”. Tekst „Projektujemy zgodnie z WCAG 2.1 AA. Stan zgodności zostanie opisany po audycie działającej aplikacji.” Bez niepotwierdzonej deklaracji zgodności. Sekcje „Stan sprawdzenia” (data i zakres testu albo „Nie przeprowadzono audytu”), „Znane ograniczenia” („Obraz PDF może nie być dostępny dla czytnika ekranu. Użyj »Tekst strony«. OCR może zawierać błędy.”), „Zgłoś problem” z kontaktem zespołu z konfiguracji. Gdy go brak: „Kontakt nie został skonfigurowany”, bez fikcyjnego adresu. Link „Wróć do analizy”.

Stany: treść statyczna dostępna także przy awarii API; brak daty audytu opisany jawnie. 320–1440: jedna kolumna max. 720 px, tekst zawijany, linki dostępne przez Tab. F30.

### 3.14. S14 Strony błędów (E1, 403: E3)

**Cel:** wyjaśnić problem i umożliwić powrót. **Dostęp:** wszyscy; bez ujawniania istnienia cudzej sprawy. Dla identyfikatora spoza zasięgu wspólne KS-4, niezależnie od istnienia obiektu.

- 404: „Nie znaleziono strony.” / “Page not found.” + „Przejdź do nowej analizy” / “Start a new analysis”.
- 403 (brak roli do funkcji): KS-1; „Wróć do analizy” w demo, „Wróć do spraw” w pełnej wersji.
- 500: „Nie udało się wyświetlić strony.” / “The page could not be displayed.”; „Spróbuj ponownie” / “Try again”, „Przejdź do nowej analizy”, „Identyfikator zdarzenia: {id}”. Bez stack trace, treści dokumentów i kluczy. Ponowienie odczytu strony nie uruchamia ponownie ekstrakcji ani zapisu.

Fokus po nawigacji na H1; komunikat awarii ogłaszany czytnikowi. 320–1440: wyśrodkowana kolumna max. 640 px, przyciski na telefonie jeden pod drugim, bez poziomego scrolla. Ramki F31, F32, F49.

---

## 4. Przepływy

### 4.1. Pojedynczy plik: analiza i wynik; korekta po MVP

MVP: kroki 1–4 → pobranie zapisanego wyniku silnika. Kroki 5–7 i ZIP w kroku 8 dotyczą etapów po MVP.

1. S01: użytkownik wybiera `odwolanie.pdf` → lista „Wybrane pliki (1)”, nazwa sprawy „Sprawa z 21.11.2026, 14:05”.
2. „Uruchom analizę” → wysyłka → przejście do S02; wiersz „Analizowanie: Odczyt tekstu” → „Klasyfikacja” → „Ekstrakcja” → „Walidacja”.
3. Stan wyniku „Częściowy”, flaga „Do sprawdzenia” (np. 1 pole). Region aria-live: „odwolanie.pdf: gotowe, 1 pole do sprawdzenia.”
4. „Przejrzyj” → S03, filtr „Do sprawdzenia (1)”, fokus na pierwszym polu, PDF przewinięty do dowodu.
5. Użytkownik porównuje, klika „Edytuj”, poprawia `numer_ted` z `641651 2025` na `641651-2025`, „Zastosuj” (zmiana szkicu).
6. Pasek akcji: „Niezapisane zmiany: 1” → „Zapisz korektę” → powstaje wynik v2 („Poprawione”).
7. „Zatwierdź wynik” → status „Zatwierdzone”.
8. „Pobierz JSON v{n}” → `odwolanie.json` (jawnie wybrana, zapisana wersja). Po MVP ZIP odtwarza ścieżkę względną wejścia (§4.7).

Uwaga [PROP]: plik oceniany przez jury powstaje w CLI z folderów `input/`→`output/` [ORG: README]. GUI eksportuje ten sam format; przy korekcie eksport zawiera wersję poprawioną, a przełącznik w zakładce JSON pozwala pobrać wynik silnika.

### 4.2. Paczka / sprawa (foldery i ZIP po MVP)

1. S01 → „Wybierz folder” → folder `input/` z podfolderami `przyklad_01 … przyklad_60`.
2. Podgląd: „60 spraw · 187 plików” (lista zgrupowana; grupy zwinięte powyżej 10).
3. „Uruchom analizę” → S04 z filtrem bieżącej partii i paskiem „Przetworzono {k} z {n} dokumentów”. Każda sprawa ma własną stronę S02.
4. Błędy techniczne nie zatrzymują partii [ZESP: ADR-002 pkt 11]; na końcu baner częściowego wyniku i „Ponów nieudane”.
5. „Pobierz wynik (ZIP)” na poziomie partii odtwarza drzewo `output/` z zachowanymi nazwami podfolderów i plików [ORG: README; ZESP: UZP-06].

Pełna: wgranie ZIP z drzewem zamiast folderu; dołączanie dokumentów do istniejącej sprawy („Dodaj dokumenty”).

### 4.3. Wersjonowanie dokumentu i wyniku (po MVP)

- **Wersja dokumentu** powstaje, gdy w sprawie wgrano plik o tej samej nazwie. Okno: „Plik {nazwa} już jest w tej sprawie. Co zrobić?” — „Dodaj jako nową wersję (v{n+1})”, „Dodaj do osobnej paczki z zachowaniem ścieżki”, „Anuluj”. Gdy skrót pliku identyczny: „Ten sam plik jest już w sprawie (v{n}). Nie dodano.”
- **Wersja wyniku** powstaje przy: analizie (v1), ponownej analizie (nowa wersja dokumentu, zmiana klasy, nowa wersja konfiguracji klas, ponowienie), zapisie korekty, przywróceniu. Każda wersja zapisuje: autora (silnik/użytkownik), model, wersję klasy YAML, wersję silnika, czas.
- Zatwierdzenie dotyczy konkretnej wersji. Historyczne zatwierdzenie pozostaje przy poprzedniej wersji; nowa wersja po zatwierdzeniu ma status „Niezatwierdzone” z komunikatem „Wynik zmienił się po zatwierdzeniu. Wymaga ponownego zatwierdzenia.”
- Ponowna analiza nigdy nie nadpisuje korekty bez pytania: „Nowa analiza utworzy wersję v{n+1}. Twoje korekty z v{k} nie zostaną przeniesione automatycznie. Kontynuować?” [PROP]

### 4.4. Skany, dokumenty mieszane, obce, błędy techniczne

| Przypadek | Gdzie widać | Treść |
|---|---|---|
| Skan po wykonanym OCR | S02: „{n} str. · skan”; S03: miniatury „OCR”, etykieta nad stroną | „Skan — tekst z OCR” |
| Mieszany | S02: „· mieszany”; S03: miniatury „T”/„OCR” per strona | dowód pokazuje „Źródło tekstu: OCR” |
| Słaby OCR | pole „Do sprawdzenia”, ostrzeżenie na stronie | „Niska jakość odczytu OCR na tej stronie. Sprawdź wartość z obrazem dokumentu.” |
| Obcy | S02 status „Dokument spoza zakresu”; S03 stan obcy | §3.3.14 |
| Błąd techniczny | S02 status czerwony + baner częściowy; S03 stan błędu | §3.3.14; brak wyniku ekstrakcji, eksport według §3.3.5a; „Ponów” |
| OCR niedostępny / shim | S01, S03 i źródło dowodu | §3.1.1; bez obietnicy obsługi skanów przy niedostępności |
| Błąd po części dokumentów partii | S02/S04 baner | partia kontynuowana |

### 4.5. Zarządzanie użytkownikami (E3)

Administrator: S09 → „Dodaj użytkownika” → role + flaga → „Zapisz” → status „Zaproszony” → użytkownik loguje się (S12) → status „Aktywny”. Zmiana roli i blokada wpisywane do dziennika. Blokada natychmiast unieważnia sesję.

### 4.6. Konfiguracja klas (YAML) z podglądem

E2 (pełny edytor; mały pokaz P0 w §4.6.1): S06 → klasa → S07: „Pola”, „YAML”, „Podgląd formularza”, „Test na pliku”. Konfigurator tworzy szkic, waliduje kontrakt i rejestr mechanizmów, testuje PDF, zapisuje nieaktywną wersję, a następnie wybiera „Aktywuj zestaw”.

Okno aktywacji: „Aktywuj zestaw {nowa_wersja}?”; „Nowe analizy użyją tego zestawu. Trwające zadania i zapisane wyniki zachowają {stara_wersja}.” Lista zmian, liczba klas i wynik walidacji/testu. Akcje „Aktywuj” / “Activate”, „Anuluj”. Stan „Aktywowanie…” → „Zestaw {wersja} aktywny” albo „Nie aktywowano. Nadal aktywny {stara_wersja}. Ponów”. Bez aktywnego poprzednika błąd blokuje analizę (§3.6). Cofnięcie aktywacji wybiera kompletny wcześniejszy zestaw; nie przelicza wyników. Nie obiecujemy przeładowania bez restartu przed ustaleniem mechanizmu (§10).

#### 4.6.1. Dodanie klasy i pola bez edytora GUI (P0)

Pokaz obejmuje rzeczywistą analizę, a nie tylko renderowanie formularza z eksperymentu YAML. Nowy mechanizm ekstrakcji nadal wymaga kodu; pokaz korzysta z mechanizmów już obsługiwanych przez silnik.

1. W S01 odczytać „Konfiguracja klas: {wersja}, {liczba} klas”. Użyć osobnego demonstracyjnego zestawu YAML, bez zmian trzech oficjalnych kontraktów i materiałów organizatora.
2. Poza GUI dodać YAML syntetycznej klasy „Nota testowa”, z sygnałem rozpoznania i polem tekstowym `numer_noty`; syntetyczny PDF zawiera np. „Nota testowa. Numer noty: NT-2026-001”. Dodać również nowe pole `oznaczenie_sprawy` do tej demonstracyjnej klasy, pochodzące z frazy „Oznaczenie sprawy: DEMO-42”. Zmianę pola pokazać jako drugą wersję YAML, bez zmiany kodu.
3. Przeładować kompletny zestaw: P0 dopuszcza restart serwera z nową konfiguracją, potem odświeżenie S01. „Odśwież konfigurację” w UI tylko ponownie odczytuje stan backendu; nie udaje aktywacji. Przeładowanie bez restartu jest otwarte (§10). Zadania zachowują przypiętą wersję.
4. S01 pokazuje nową wersję i liczbę klas/pól. Niepoprawny YAML daje błąd konfiguracji, ze starą wersją nadal aktywną lub blokadą, jeśli jej nie ma (§3.6).
5. Wgrać PDF, uruchomić nową analizę i sprawdzić klasyfikację po treści, odczyt wartości i dowód. W S03 formularz z YAML pokazuje `numer_noty`, a po drugim przeładowaniu także `oznaczenie_sprawy`. Zakładka JSON i pobrany plik zawierają odpowiednio `NT-2026-001` i `DEMO-42`.
6. Pobrać JSON i dowody, sprawdzić wersję YAML. Przywrócić oficjalny zestaw przed ocenianym uruchomieniem. Wynik klasy demonstracyjnej jest oznaczony „Przykład rozszerzenia, poza kontraktami konkursowymi”.

Warunek zaliczenia: nowa klasa zostaje rozpoznana i oba pola rzeczywiście wyekstrahowane z PDF w dwóch kolejnych konfiguracjach. Sam szablon formularza lub wstawione ręcznie wartości nie zaliczają pokazu. S06/S07 z edytorem pozostają E1/E2. Ramka F59 pokazuje S01 po przeładowaniu oraz S03 z nowym formularzem i JSON, bez nowej strony.

### 4.7. Tożsamość partii, kolizje i eksport częściowy

[PROP; REC-7; ORG: UZP-06] Partia ma niezmienne `batch_id`, katalog wejściowy i listę dokumentów ze ścieżką względną. Sprawa to organizacja pracy, nie źródło wartości. Pliki z katalogu głównego należą do grupy „Katalog główny”; pierwszy poziom podfolderów wyznacza sprawy, dalsze poziomy zachowujemy w ścieżce dokumentu. Nazwa sprawy w UI nie zmienia ścieżki eksportu.

Mapowanie: `input/a.pdf` → `output/a.json`; `input/sprawa/zalaczniki/a.pdf` → `output/sprawa/zalaczniki/a.json`. ZIP partii zawiera takie `output/`, a dowody pobiera się osobno w `evidence/` z tym samym drzewem. MVP dla plików bez folderu eksportuje każdy plik osobno pod oryginalną nazwą bazową, o ile dopuszcza to polityka §3.3.5a.

Duplikat skrótu pod inną ścieżką: ostrzeżenie `duplikat_pliku`, obie ścieżki zachowane, dokumenty nadal niezależne. Ta sama ścieżka z różnymi bajtami: blokada przed analizą; „Kolizja ścieżki {ścieżka}. Wybierz nową wersję dokumentu, osobną paczkę albo anuluj”. W MVP trzeba usunąć konfliktujący plik z wyboru lub analizować go w osobnej paczce. Kolizje po usunięciu rozszerzenia, normalizacji lub zmianie wielkości liter także blokują wspólny eksport, bez automatycznych `(2)` i bez nadpisania. Wersja dokumentu zachowuje oryginalną ścieżkę; eksport wybiera dokładnie jedną zapisaną wersję na ścieżkę.

S04 z filtrem partii ma „Pobierz wyniki partii (ZIP)” i „Pobierz dowody partii”. Przed eksportem F42: „Eksport częściowy”, lista **uwzględnionych** pełnych, dopuszczonych polityką częściowych i obcych oraz **pominiętych** z przyczyną i ścieżką: błąd techniczny, niejednoznaczny, wiele dokumentów, niezgodny kontrakt lub brak uprawnień. Przy szkicu najpierw §3.3.7. „Pobierz {n} wyników” / “Download {n} results”, „Wróć”. Gdy n=0: „Brak wyników do pobrania”, bez pustego ZIP udającego sukces. Raport pominięć jest osobnym plikiem do pobrania, poza `output/`; rzeczywiście obcy dokument daje `{}` jako wynik klasyfikacji; ewentualny zastępczy `{}` dla awarii wymaga osobnej decyzji i oznaczenia z §3.3.5a. Wyniki niezgodne przez `null` są uwzględniane wyłącznie według zatwierdzonej polityki, z osobnym licznikiem ostrzeżeń. Zapis plików atomowy, awarie nie zatrzymują pozostałych dokumentów [ADR].

### 4.8. Pełny scenariusz pokazu jury (P0, 10 kroków)

[Ocena UI §4; Fable §7] Pokaz na desktopie 1440×900, PL, jasny motyw, po odbiorze §8.1.1. Wszystkie PDF syntetyczne, przygotowane poza katalogami organizatora; scenariusz jest planem, nie raportem z testu. Dopuszczamy własny syntetyczny PDF jury. Nie pokazujemy korekt jako automatycznego wyniku ani nie deklarujemy F1 na podstawie makiet.

| Krok | Działanie i dane | Oczekiwany dowód na ekranie / w pliku |
|---|---|---|
| 1. Gotowość | Lokalny start CLI i serwera GUI; S01, karta modeli. | Wersje, aktywny YAML, rewizja kontraktu, największy model, licencje i kraje, status modelu/OCR lub shima. Pokazać też bezpieczne komunikaty braku klucza i niedostępnego API (§3.1.1). |
| 2. Wgranie | Trzy PDF: `dokument_01.pdf` (odwołanie pod neutralną nazwą), `pelnomocnictwo_demo.pdf`, `przelew_demo.pdf`. | Trzy klasy rozpoznane po treści. Dane podmiotu w dwóch plikach celowo różne; wartości nie przenoszą się między plikami. |
| 3. Analiza | Uruchomić paczkę; obserwować S02. | Etapy, czas, niezależne zakończenie każdego pliku i zachowanie gotowych wyników. Ponowne kliknięcie/odświeżenie nie tworzy drugiej analizy. |
| 4. PDF obok danych | Otworzyć odwołanie w S03. | Rola podmiotu (np. odwołujący i zamawiający), wybrana wartość oraz przynajmniej jedno pole wymagające uwagi. Dodatkowy syntetyczny wariant z brakującym NIP pokazuje listę sprawdzonych stron i właściwy powód braku. |
| 5. Dowód | „Pokaż dowód”; otworzyć „Dowody” i pobrać je osobno. | Strona oryginału + cytat, źródło tekst PDF/OCR, metoda. Dla `czynnosc_opis`: reguła i przesłanka `czynnosc_powod_id` z dowodem. Bez obrysu i udawanej dokładnej lokalizacji. |
| 6. JSON i pobranie | Zakładka JSON; pobrać `dokument_01.json`, otworzyć plik i porównać z wynikiem CLI dla tych samych bajtów/konfiguracji. | Ten sam zapisany wynik silnika, nazwa bazowa zachowana, kontrakt przypięty. Dowody nie trafiają do ocenianego JSON. Sporne braki prezentować według zatwierdzonego wariantu §3.3.5a; bez decyzji pokazać blokadę. |
| 7. Obcy dokument | Wgrać `obcy_demo.pdf` z czytelną treścią spoza klas; otworzyć wynik. | Uzasadnienie, stan „Dokument spoza zakresu”, faktycznie pobrany `obcy_demo.json` z `{}`. Nie tylko etykieta na ekranie. |
| 8. Skan i mieszany | Wgrać `skan_demo.pdf` oraz `mieszany_demo.pdf` (strona tekstowa i skanowana). Następnie kontrolowany wariant z wyłączonym OCR. | Rzeczywisty tekst OCR, źródło dowodu, oznaczenie shima, jeśli użyty; ostrzeżenie jakości, jeśli zgłoszone przez silnik. Bez OCR: baner, nieprzetworzone strony i ograniczenie wyniku. Diagnoza bez OCR nie zalicza obsługi skanów. |
| 9. Błąd techniczny | Kontrolowana awaria endpointu podczas jednej analizy; pozostałe dokumenty paczki kończą się niezależnie. Przywrócić usługę i jawnie ponowić. | Błąd z etapem/kodem, brak wyniku ekstrakcji i brak JSON w ścisłym wariancie A. W wariancie B ewentualny znacznik awarii tylko po osobnej decyzji i ostrzeżeniu. Bez cache udającego bieżący wynik; gotowe pliki pozostają dostępne. |
| 10. Dodanie klasy i pola | Wykonać §4.6.1: YAML poza GUI → przeładowanie → rzeczywista analiza `nota_demo.pdf` → nowa klasa i pole, potem drugi YAML z dodatkowym polem → ponowna analiza. | S01 potwierdza wersję, S03 pokazuje formularz i JSON z wartościami `NT-2026-001` oraz `DEMO-42`, pobrane JSON/dowody potwierdzają ekstrakcję. Bez zmian kodu i bez przedstawiania samego formularza jako dowodu działania ekstraktora. |

Po pokazie przywrócić oficjalny zestaw klas i wybrać „Zakończ i wyczyść sesję”. EN, telefon/tablet, obrysy, diagnoza regionów, role, audyt i edytor YAML w GUI nie są częścią tego scenariusza.

---

## 5. Model danych widoczny w UI

[PROP; zgodny z ADR-002 pkt 9–12 i eksperymentem YAML]

| Encja | Pola widoczne w UI | Gdzie |
|---|---|---|
| **Sprawa** (Case) | id, nazwa, data utworzenia, autor, liczba dokumentów, liczniki statusów, wersja konfiguracji klas użyta przy analizie, (pełna) odpowiedzialny | S02, S04 |
| **Dokument** (Document) | id, nazwa pliku wejściowego, ścieżka względna w paczce, rozmiar, liczba stron, rodzaj tekstu (tekst / skan / mieszany), skrót SHA-256, bieżąca wersja, status | S02, S03 |
| **Wersja dokumentu** (Document version) | numer, skrót, autor wgrania, data | S05 |
| **Ekstrakcja / wersja wyniku** (Extraction) | numer, rodzaj (silnik / korekta / przywrócenie / ponowna analiza), klasa, sposób ustalenia klasy (silnik / ręcznie), model i jego wersja, wersja YAML klasy, wersja silnika, czas trwania, postęp zadania, sześć stanów wyniku (§3.2.1) i osobny stan zatwierdzenia, JSON wyniku, autor, zatwierdzający, data | S03, S05 |
| **Błąd techniczny** (Technical error) | etap, kod, komunikat, czas, możliwość ponowienia | S03, S02, S10 |
| **Pole** (Field) | ścieżka JSON, etykieta PL/EN, typ, wartość, wartość silnika (przy korekcie), stan (z dokumentu / brak / wyliczone / do sprawdzenia / poprawione), metoda (reguła / model / wyliczone), ostrzeżenia, kandydaci alternatywni | S03 |
| **Dowód** (Evidence) | ścieżka pola, strona oryginału, cytat, lista obrysów (opcjonalna), źródło tekstu (tekst PDF / OCR), metoda, reguła i dowody przesłanek dla wartości wyliczonej | S03 „Dowody”, podświetlenia |
| **Klasa** (Class) | id, nazwa PL/EN, wersja, status (aktywna / szkic), sygnały rozpoznania, pola (z YAML), autor wersji | S06, S07 |
| **Użytkownik** (User) | imię i nazwisko, e-mail, role, flaga „Dane osobowe”, status, ostatnie logowanie | S09 |
| **Rola** (Role) | nazwa, opis, uprawnienia (macierz) | S09 |
| **Wpis audytu** (Audit entry) | czas, użytkownik, zdarzenie, obiekt (sprawa/dokument/pole/klasa/użytkownik), szczegóły (było/jest, maskowane) | S10 |

Reguła prezentacji: JSON jest polem encji Ekstrakcja; podgląd podlega §1.4, a oceniany eksport zachowuje kontrakt. Stany, dowody, kandydaci i diagnoza są osobno.

Rozszerzenia modelu [PROP; PIPE; KARTY]:

| Encja | Dane i powiązania |
|---|---|
| Partia | `batch_id`, korzeń wejścia, ścieżki, zadania niezależnych dokumentów, podsumowanie eksportu |
| Diagnoza | poziom dokument/strona/region, źródła tekstu, typ, orientacja i transformacja, jakość, pewność osobno dla diagnozy, sygnały, decyzja OCR, kody |
| Segment | ID, zakres stron oryginału, kandydaci klas i dowody; brak scalania między segmentami |
| Grupa/podmiot | stabilne ID, rola i jej przesłanki, lista ścieżek pól, `obszary[]`, spójność i kolizje |
| Obszar/dowód | ID dokumentu i skrót wersji, strona (od 1), region/ID słów, cytat, bbox lub wielokąt, wymiary i jednostki strony, obrót i transformacja OCR do oryginału |
| Pole (uzupełnienie) | pięć powodów braku, pokrycie stron/regionów, kody odstępstw i dowody kodu, stan wartości, flaga przeglądu, reguła i przesłanki wartości wyliczonej |
| Wynik (uzupełnienie) | sześć stanów wyniku niezależnie od postępu i zatwierdzenia; lista braków; konfiguracja, prompt, model, ekstraktor i ich wersje; szkic oddzielony od trwałej wersji |

Adapter kart v1 odczytuje `pola.*.wystapienia[]`, `grupy[].obszary[]`, `spojna`, `kolidujace_pola`, `kody[].{kod,pole,dowod}` i `braki[]`. Karta nie zawiera pełnej diagnozy ani wszystkich metadanych dowodu: brakujące dane pokazujemy jako „Nie przekazano”, nie wyprowadzamy ich z nazwy pliku. Grupa karty i obiekt JSON nie muszą być tożsame. Schemat kart pozostaje nienaruszony; to propozycja adaptera, nie deklaracja wdrożonego kontraktu silnika.

---

## 6. Punkt rozszerzenia (poza zakresem)

[ADR; ZESP; REC-6] OpenUI i elementy generatywne są poza MVP i pełną wersją tego projektu. Nie ma asystenta, jego ramek, endpointów ani dodatkowych wywołań modelu. Ewentualny przyszły projekt wymaga osobnej decyzji: autoryzacja danych i identyfikatorów, kontrola całej treści odpowiedzi, bez wniosków prawnych z dopasowania nazwisk, potwierdzona licencja modelu i europejski hosting. Nie rezerwujemy miejsca w bieżącej nawigacji.

---

## 7. Tokeny wizualne

P0 używa tylko jasnej palety; ciemna paleta i motyw systemowy są E1. Neutralne wobec biblioteki; nazwy semantyczne do zmapowania na zmienne CSS lub motyw wybranej biblioteki. Kontrasty policzone wzorem WCAG 2.1 (luminancja względna) dla podanych par.

### 7.1. Kolory

| Token | Jasny | Ciemny | Użycie | Kontrast (jasny / ciemny) |
|---|---|---|---|---|
| `bg` | #FFFFFF | #111418 | tło strony | — |
| `surface` | #F5F6F8 | #1A1E24 | karty, panele | — |
| `surface-raised` | #FFFFFF | #232831 | okna, szuflady, menu | — |
| `border` | #D9DDE3 | #2E343D | podziały dekoracyjne (nie granice kontrolek) | — |
| `border-control` | #7A828F | #7D8694 | ramki pól, pól wyboru, rozdzielacza | 3,88 / 4,55 na bg / surface |
| `text` | #1A1D23 | #E8EAED | tekst podstawowy | 16,88 / 15,32 na bg |
| `text-muted` | #545D6B | #A9B1BD | tekst drugorzędny, klucze JSON | 6,66 / 8,54 na bg |
| `primary` | #1F5FBF | #7FB0FF | przyciski główne, linki, aktywne | 6,09 / 8,40 na bg |
| `on-primary` | #FFFFFF | #0B1A33 | tekst na `primary` | 6,09 / 7,90 na primary |
| `primary-subtle` | #E8F0FC | #1C2B44 | tło zaznaczenia, strefa upuszczania | — |
| `focus-ring` | #1F5FBF | #7FB0FF | obrys fokusu 2 px + odstęp 2 px | 6,09 / 7,61 na bg / surface |
| `success` / `success-subtle` | #1E7A3C / #E8F5EC | #6FCF8E / #183324 | „Zatwierdzone” | 4,79 / 7,15 na success-subtle |
| `warning` / `warning-subtle` | #8A5300 / #FFF4DB | #F2C14E / #3A2E10 | „Do sprawdzenia” | 5,79 / 7,93 na warning-subtle |
| `danger` / `danger-subtle` | #B42318 / #FDECEA | #FF8A80 / #3D1A18 | „Błąd techniczny”, błędy walidacji | 5,75 / 6,77 na danger-subtle |
| `info` / `info-subtle` | #0B6A85 / #E6F4F8 | #6FD0EA / #13303A | „Analizowanie”, „Wyliczone” | 5,46 / 7,86 na info-subtle |
| `accent` / `accent-subtle` | #5B3FB5 / #F1EDFB | #B9A6FF / #2A2342 | „Poprawione”, „Niejednoznaczny” | 6,46 / 7,03 na accent-subtle |
| `neutral-strong` | #545D6B | #A9B1BD | „Dokument spoza zakresu” | 6,66 / 8,54 na bg |
| `evidence-bg` | #FFE380 (krycie 55% na PDF) | #FFE380 (krycie 45%) | podświetlenie dowodu na stronie PDF | 13,31 / 13,31; tekst #1A1D23 na pełnym #FFE380, bez alfa |
| `evidence-border` | #8A5300 | #8A5300 | obrys aktywnego dowodu | 6,33 / 6,33 na pdf-page (biała strona w obu motywach) |
| `evidence-text-bg` | #FFF4DB | #5C4A00 | podświetlenie w „Tekst strony” | 15,45 / 7,16 na text / evidence-text-bg |
| `pdf-page` | #FFFFFF | #FFFFFF | strona PDF zawsze biała | — |
| `pdf-canvas` | #E4E7EC | #0B0D10 | tło pod stronami PDF | — |

Obliczenie dla sRGB: kanał `c = składowa/255`; `c_lin = c/12,92` dla `c ≤ 0,04045`, w przeciwnym razie `((c+0,055)/1,055)^2,4`. Luminancja `L = 0,2126 R_lin + 0,7152 G_lin + 0,0722 B_lin`; kontrast `(L_jaśniejsza + 0,05)/(L_ciemniejsza + 0,05)`. Wyniki zaokrąglone dopiero na końcu do dwóch miejsc. Każdy wiersz wskazuje tło; statusy to tekst koloru statusu na odpowiadającym `*-subtle`.

Dodatkowe pary kontrolne:

| Para | Jasny | Ciemny |
|---|---:|---:|
| text / surface | 15,61:1 | 13,88:1 |
| text-muted / surface | 6,16:1 | 7,74:1 |
| dawny evidence-border / pdf-page | 6,33:1 | 1,68:1 |

Dawny ciemny obrys 1,68:1 jest odrzucony. Nowy obrys #8A5300 działa na białej stronie także w ciemnym motywie. Wypełnienie `evidence-bg` jest dekoracyjne, nie zastępuje obrysu: po kompozycji 55% na bieli daje #FFF0B9, a 45% daje #FFF2C6; kontrast tekstu #1A1D23 wynosi odpowiednio 14,81 i 15,09:1 (kanały po kompozycji zaokrąglone do 8 bitów). Nie gwarantuje to kontrastu treści dowolnego PDF, dlatego zawsze dostępny jest „Tekst strony”. Hover, focus na innych tłach i stany biblioteki wymagają kontroli po implementacji; tabela nie jest audytem aplikacji.

### 7.2. Typografia

| Token | Rozmiar / interlinia | Grubość | Użycie |
|---|---|---|---|
| `font-sans` | krój bezszeryfowy z polskimi znakami, hostowany lokalnie (bez CDN — wymóg lokalnych zasobów z [pełnej aplikacji](../pelna-aplikacja.md)); zapas: krój systemowy | — | całe UI |
| `font-mono` | krój stałej szerokości z polskimi znakami, lokalny | — | JSON, klucze, nazwy plików, numery |
| `display` | 32/40 (telefon 28/36) | 600 | H1 strony startowej |
| `h1` | 24/32 (telefon 22/28) | 600 | tytuły stron |
| `h2` | 20/28 | 600 | sekcje, nagłówki grup pól |
| `h3` | 16/24 | 600 | podsekcje, etykiety kart |
| `body` | 16/24 | 400 | tekst podstawowy, wartości pól |
| `body-sm` | 14/20 | 400 | metadane, dowody, etykiety tabel |
| `caption` | 12/16 | 500 | klucze JSON pod etykietą, znaczniki miniatur — tylko z kontrastem ≥ 4,5 : 1 |
| `code` | 13/20 | 400 | edytor JSON/YAML |

Tekst skalowalny do 200% bez utraty treści; jednostki względne [WCAG 1.4.4].

### 7.3. Odstępy, rozmiary, promienie, cienie

- Skala odstępów (podstawa 4 px): `space-1` 4, `space-2` 8, `space-3` 12, `space-4` 16, `space-5` 24, `space-6` 32, `space-7` 48, `space-8` 64.
- Marginesy strony: 360 → 16 px; 768 → 24 px; 1024 → 24 px; 1440 → 32 px.
- Cel dotykowy minimum 44×44 px (na telefonie i tablecie), 32 px wysokości kontrolek na desktopie w trybie „Zwarta” [PROP].
- Promienie: `radius-sm` 4 (pola, etykiety statusów), `radius-md` 8 (przyciski, karty), `radius-lg` 12 (okna, strefa upuszczania), `radius-full` (chipy, awatary).
- Cienie: `shadow-1` 0 1 2 rgba(16,24,40,.08) — karty; `shadow-2` 0 8 24 rgba(16,24,40,.16) — okna i szuflady. W ciemnym motywie zamiast cienia jaśniejsza powierzchnia (`surface-raised`) + `border`.
- Ruch: 150 ms dla stanów, 250 ms dla szuflad; przy `prefers-reduced-motion` bez animacji przesuwania (zmiana natychmiastowa), wirujący wskaźnik zastąpiony statycznym tekstem „W toku”.
- Siatka: 4 kolumny (360), 8 (768), 12 (1024, 1440).

### 7.4. Dostępność — zasady wykonawcze (WCAG 2.1 AA)

- Fokus zawsze widoczny (`focus-ring`), kolejność fokusu zgodna z wizualną; okna i szuflady więżą fokus i zwracają go do wywołującego elementu.
- Każda kontrolka ma widoczną etykietę; przyciski-ikony mają etykietę dostępną (podana w tekstach powyżej).
- Statusy: ikona + tekst; komunikaty błędów walidacji tekstowe i powiązane z polem.
- Komunikaty asynchroniczne (postęp, zapis, kopiowanie) przez `aria-live="polite"`; błędy krytyczne przez `role="alert"`.
- Przeglądarka PDF: obraz strony z alternatywą „Tekst strony”; nawigacja stron klawiaturą.
- Reflow: brak poziomego przewijania strony przy 320 px; tabele przechodzą w karty; edytor kodu i PDF przewijają się wewnątrz swoich paneli.
- Język interfejsu `lang="pl"` / `"en"`; cytaty mają język źródła, a nie automatycznie polski.
- Limit czasu sesji (pełna): ostrzeżenie 2 min wcześniej z „Przedłuż sesję” [WCAG 2.2.1].

Kontrola projektu przy **320 px** (F44, F45): marginesy 16 px zostawiają 288 px treści; strefa uploadu i przyciski mają 100% tej szerokości. Szuflada max. `viewport − 32 px`, dialog max. `viewport − 32 px`, bez stałego minimum 480 px. Długie ścieżki, kody, cytaty, etykiety EN i identyfikatory zawijają się; filtry przechodzą do kolejnych wierszy. Zakładki mieszczą trzy pozycje, „Więcej” otwiera resztę. Tabele zmieniają się w karty; w tekście JSON opcja „Zawijaj linie” jest domyślnie włączona na telefonie. PDF jako obraz może wymagać dwuwymiarowego przewijania we własnym panelu; alternatywa „Tekst strony” zawija się bez tego wymogu.

Odbiór implementacji: viewport 320×800 oraz desktop 1280 px przy powiększeniu 400% (równoważne 320 CSS px), oba motywy i oba języki; brak poziomego scrolla strony, utraty kontrolek i zasłonięcia fokusu. Osobno tekst 200%, otwarta klawiatura, powrót do pola i modal. To kryteria i ramki projektu, **kontrola działającego reflow nie została wykonana**, bo zlecenie nie obejmuje kodu ani makiet.

---

## 8. Zakres MVP (hackathon) vs pełna wersja

### 8.1. MVP / P0 do makiet i implementacji

[ZESP; zlecenie B 0.6.0; Fable §4 i §7] Jeden zakres: **desktop 1440×900, PL, motyw jasny, S01–S03**, bez kont. Kilka PDF przetwarzanych niezależnie; bez folderów i ZIP w GUI. Dane i komunikaty gotowości pochodzą z silnika. Projekt nie potwierdza gotowego API, OCR ani ekstrakcji; makiety nie są wynikami działania aplikacji.

| Zakres P0 | Odbiór |
|---|---|
| Upload → S02 → PDF obok formularza/JSON w S03 | własny syntetyczny PDF jury, zachowana nazwa bazowa |
| W toku / pełny lub częściowy / obcy / błąd techniczny | czas i etap, jawne braki, niezależne zakończenia; niejednoznaczny i wiele dokumentów tylko jako banery blokujące eksport |
| Dowód = strona + cytat, PDF/OCR; reguła i przesłanki dla wyliczeń | bez geometrii i obrysów; lista sprawdzonych oraz nieprzetworzonych stron już w P0; „Nie przekazano”, gdy raportu brakuje |
| Pobranie zapisanego JSON i osobnych dowodów | zgodność podglądu z pobranym artefaktem, jawna rewizja kontraktu, dwa warianty polityki eksportu do decyzji (§3.3.5a) |
| Gotowość OCR i modelu, karta wszystkich modeli z S01 i S03 | rozróżnienie shima, braku OCR, błędów API, największy model i metadane |
| Dodanie klasy i pola w YAML poza GUI | przeładowanie, rzeczywista analiza PDF, formularz i JSON (§4.6.1) |
| Klawiatura, fokus, semantyka, desktopowy „Tekst strony”, baner syntetycznego demo | bez deklaracji audytu; ograniczenia w bloku S01/S03 |

Warunki implementacji: API z rzeczywistym raportem dowodów i gotowości, zatwierdzone polityki spornego eksportu, wybrane biblioteki przez użytkownika. Bez tych warunków można wykonać makiety; nie deklarujemy gotowości konkursowej. Nie zakładamy ukończenia całości w 24 h. P0 nie obejmuje EN, ciemnego/systemowego motywu, telefonu/tabletu, geometrii, panelu regionów, korekt, ról i audytu; ich opis pozostaje w E1–E3.

React + TypeScript, gotowa biblioteka komponentów wskazana przez użytkownika. Gotowe statyczne JS/CSS/fonty i zasoby przeglądarki PDF są budowane przez zespół i dołączane do pakietu Pythona. Next.js dopuszczalny wyłącznie jako statyczny eksport [ADR]. Instalacja u jury wyłącznie pip; Python serwuje zasoby i API tego samego silnika co CLI. Proces to ETL/ELT z OCR i ekstraktorami AI; etapy i wersje artefaktów pokazuje backend. UI nie wybiera technologii odczytu ani docelowego OCR.

#### 8.1.1. Odbiór uruchomienia u jury (P0)

Poniższe komendy są **projektowanym kontraktem uruchomienia do implementacji**, nie istniejącym CLI: repo na dzień przeglądu nie zawiera pakietu aplikacji ani `requirements.txt`. Instrukcja wydania musi zawierać przetestowane dokładne odpowiedniki; dopóki ich nie ma, odbiór pozostaje niezaliczony. Przygotować publiczny endpoint modelu i klucz poza Git oraz frontendem, w lokalnym pliku konfiguracji według instrukcji wydania, przekazanym jury uzgodnionym kanałem. Konfiguracja obejmuje modele, dostawców, potwierdzenia licencji/lokalizacji, OCR, zestaw klas, politykę eksportu i limity.

Projekt komend wspólnych dla Windows i Linux, po utworzeniu czystego środowiska Python 3.13+ (wywołanie `python` oznacza interpreter tego środowiska):

```text
python -m venv .venv
python -m pip install -r requirements.txt
python -m odwolania2json batch --input input --output output --config konfiguracja-lokalna.yaml
python -m odwolania2json serve --host 127.0.0.1 --port 8000 --config konfiguracja-lokalna.yaml
```

Pierwsza komenda tworzy środowisko; pozostałe uruchamia się jego interpreterem: Linux `.venv/bin/python`, Windows `.venv\Scripts\python.exe` zamiast `python`. Nie wymagamy bash, Node, npm, Dockera, kompilacji ani GPU. Gotowy frontend, **worker PDF**, JS/CSS, fonty, ikony, mapy znaków CMap i pozostałe zasoby wymagane przez wybrany viewer są lokalnie w pakiecie. Także wagi i konfiguracja lokalnego shima OCR muszą być dołączone do dystrybucji pip lub zainstalowane jej zależnościami; bez ukrytego pobierania przy pierwszej analizie. Zespół weryfikuje licencje całego kompletu.

| Próba odbiorowa | Warunek zaliczenia |
|---|---|
| Czysta instalacja | Python 3.13+, tylko pip i instrukcja, próba Windows i Linux; zapisane wersje systemu, zależności i wynik. To próba przenośności, nie dodatkowy potwierdzony wymóg organizatora. |
| CLI | `input/sprawa/a.pdf` daje `output/sprawa/a.json`; GUI dla tych samych bajtów i konfiguracji pobiera `a.json` o identycznej zawartości. Błędy mają raport i kod wyjścia; batch kontynuuje pozostałe pliki. |
| GUI i adres S03 | Start serwera, własny syntetyczny PDF, analiza, formularz/JSON/dowody. Odświeżenie i bezpośrednie wejście na `/sprawy/{id}/dokumenty/{docId}` w tej samej sesji odtwarza widok i stan zadania, bez 404, utraty wyniku i nowego wywołania modelu. Nieistniejący lub usunięty dokument daje KS-4 w powłoce S03. |
| Zasoby lokalne | W narzędziach sieciowych przeglądarki wszystkie zasoby UI/PDF pochodzą z lokalnego serwera; brak CDN, zdalnych fontów i brakujących plików workera. Po odcięciu Internetu UI i zapisany PDF/JSON nadal działają; nowa analiza wymagająca API pokazuje błąd sieci. |
| Gotowość | Sprawdzić działający OCR, shim, brak OCR oraz brak klucza, 401/403, limit i niedostępny endpoint. Brak OCR nie zalicza wymogu obsługi skanów. Działający shim wymaga rzeczywistego testu skanu i dokumentu mieszanego; jego oznaczenie pozostaje jawne. |
| Ponawianie i koszty | Wielokrotny klik „Uruchom”/„Ponów” i odświeżenie nie tworzą dodatkowych zadań dla tego samego żądania. Przycisk blokowany do potwierdzenia, stan odczytywany po ID zadania; odświeżenie tylko odpytuje. Awaria nie przywraca starego cache. |
| Laptop i pamięć | i7, 16 GB RAM, bez GPU: kolejka, początkowo jedno zadanie analizy/OCR na raz, renderowanie wyłącznie widocznych stron PDF i ograniczona pula miniatur. Zapisać szczyt pamięci i czas dla tekstu, skanu i dokumentu mieszanego; limity stroić po pomiarze, bez wymyślonego limitu czasu jury. |
| Sesja demonstracyjna | Wyłącznie syntetyczne pliki. „Zakończ i wyczyść sesję” w S01/S03 usuwa pliki i artefakty sesji oraz linki wyników po potwierdzeniu. Dla serwera publicznego izolacja i retencja wymagają zatwierdzonej konfiguracji przed udostępnieniem. |

Odbiór wymaga wyników tych prób na wydanym pakiecie; ten dokument nie oznacza ich wykonania.

### 8.2. Etapy po MVP

| Etap | Zakres |
|---|---|
| E1: przegląd i korekta | EN, motyw ciemny/systemowy, telefon/tablet i pozostałe szerokości 320/360/768/1024; S13 i S14 404/500; geometria dowodów i wiele obrysów grup, pełna diagnoza regionów, kandydaci, korekty i wersje wyników, zmiana klasy; S05, S06/S07 odczyt i S08 |
| E2: konfiguracja i paczki | foldery, głębokie ścieżki, kolizje, ZIP i częściowy eksport, S04; edycja/test/aktywacja YAML |
| E3: urząd | S09–S12, logowanie i role, backendowa kontrola wszystkich kanałów, bezpieczne pochodne PDF, audyt, retencja, zatwierdzanie i zasada czterech oczu |

Etapy są planem docelowym; E1/E2 nadal mogą pracować wyłącznie na danych syntetycznych. Prawdziwe dane wymagają ukończenia ochrony E3. Elementy generatywne nie należą do żadnego etapu.

---

## 9. Lista ramek do figcraft

### 9.1. Konwencje i układy

[PROP; REC-8] **62 ramki F00–F61**, w tym **18 ramek P0**, bez ramek generatywnych. 14 stron docelowych S01–S14, P0 tylko S01–S03. To specyfikacja do wykonania makiet, nie zestaw już wyrenderowanych ekranów.

W tabeli `viewport` oznacza rozmiar okna w CSS px; `treść H` to projektowana wysokość przewijanej zawartości (minimum, do weryfikacji po składzie). Dłuższa treść nigdy nie zmienia viewportu. J/C = jasny/ciemny; PL/EN = język interfejsu. Każda pozycja to odrębna ramka, bez ukrytych kopii. Nagłówek desktop 64 px, telefon 56 px; baner demo pozostaje w przepływie i jest stale widoczny, bez zwijania. Przykłady są syntetyczne [DANE]; plik skanowany to projektowany wariant przykładu, nie twierdzenie o oryginale.

Układy wspólne:

- S01: kolumna max. 720 px; baner, H1, lead, strefa wyboru, lista plików, „Uruchom analizę”, ostatnie wyniki sesji, stopka. MVP bez przycisku folderu.
- S02: H1 paczki, postęp i podsumowanie, filtry statusów i kodów, tabela ≥1024 / karty ≤768; nazwa, typ odczytu, klasa, stan, braki, akcja. MVP bez ZIP i zatwierdzania.
- S03 ≥1024: szyna 72 px, pasek dokumentu, dwa panele 50/50; PDF biały, dane z zakładkami, pasek pobrania. ≤768: zakładki z §3.3.15. W wariancie E1/E3 dochodzą wyłącznie wskazane akcje. Każdy dowód ma stronę, cytat, źródło i link powrotu; szczegóły według §3.3.
- S04/S06/S09/S10: H1, filtry/akcje, tabela albo karty; S05 porównanie wersji; S07 edytor i podgląd 60/40, na tablecie pionowo; S08/S11/S13/S14 kolumna tekstowa według §3.
- Dialog: tło właściwej strony, max. 480 px szerokości, H2, komunikat, akcje z §3/4, fokus w oknie i powrót po zamknięciu. Błąd nie zamyka dialogu.

Dane podstawowe: `przyklad_01`, `odwolanie.pdf`, firma „Belmoria Rozwiązania S.A.”, zamawiający „Aurelink Automatyka S.A.”, BZP `2026/BZP00999778`, TED `999137-2026`, kod czynności `9`; kwota przelewu `200.00`, syntetyczny PESEL `85120133547`. Pełne ścieżki i typy według §3.3.6, cytaty z bieżącego dokumentu. Przykłady diagnostyczne i graniczne oznaczamy „Scenariusz syntetyczny”; nie dopisujemy ich do oryginalnych kart.

### 9.2. Ramki

| ID | Widok i stan | Viewport | Treść H | Motyw / język | Etap | Zawartość i dokładne teksty wyróżnionej części |
|---|---|---|---:|---|---|---|
| F00 | Tokeny i komponenty | 1440×900 | 1800 | J / PL | projekt | Paleta §7, typografia, grupy stanów P0 i banery oraz stany docelowe, 5 powodów braku, przyciski/fokus, modal, pole walidacji. |
| F01 | S01 pusty | 1440×900 | 1000 | J / PL | P0 | „Nowa analiza”, stały baner, „Wybierz pliki”, „Nie masz jeszcze żadnych analiz.” |
| F02 | S01 pliki wybrane | 1440×900 | 1100 | J / PL | P0 | „Wybrane pliki (4)”, lista PDF z rozmiarami, usuń, „Uruchom analizę”, „Wyczyść”. Błędny DOCX: „To nie jest PDF. Pominięto.” |
| F03 | S01 pusty telefon | 360×800 | 1100 | J / PL | E1 | Jeden przycisk wyboru na pełną szerokość, pełny baner i stopka; bez zwijania ostrzeżenia demo. |
| F04 | Menu otwarte | 360×800 | 800 | C / PL | E1 | Szuflada 288 px, „Nowa analiza”, link dostępności, PL/EN, Motyw; fokus na „Zamknij menu”. |
| F05 | S02 analiza w toku | 1440×900 | 1000 | J / PL | P0 | „Przetworzono 2 z 4”, odwołanie w ekstrakcji, skan w OCR, pozostałe pełny i obcy; kody przy wierszach. |
| F06 | S02 wyniki mieszane | 1440×900 | 1100 | J / PL | P0 | Cztery dokumenty: pełny, częściowy (2 braki), obcy, błąd techniczny. Baner „1 dokument z błędem technicznym”; „Ponów nieudane”. |
| F07 | S02 wyniki telefon | 360×800 | 1500 | C / PL | E1 | Cztery karty jak F06, filtry zawijane, kod i licznik braków; brak akcji ZIP. |
| F08 | S03 pełny z dowodem | 1440×900 | 1300 | J / PL | P0 | Filtr „Wszystkie pola” jawnie aktywny; Tytuł zamówienia wybrany. „Str. 1”, cytat, „Źródło: tekst PDF”, bez obrysu; „Pobierz JSON v1”. |
| F09 | S03 dowód geometryczny | 1440×900 | 1300 | C / PL | E1 | Taki sam tytuł; biała strona i obrys #8A5300; numer pola; geometria tylko z dowodu. |
| F10 | S03 JSON | 1440×900 | 1200 | J / PL | P0 | JSON zapisanej v1, „Kopiuj”, „Pobierz odwolanie.json · v1”; `null` bez dopisanych powodów, dowody osobno. |
| F11 | S03 walidacja korekty | 1440×900 | 1300 | J / PL | E1 | Numer TED `999137 2026`; komunikat formatu; „Zastosuj” zablokowane, „Anuluj”, szkic bez trwałego zapisu. |
| F12 | S03 chroniony skan | 1440×900 | 1400 | C / PL | E3 | Bezpieczna pochodna PDF, zamaskowane nazwiska, PESEL i cytaty; „Pokaż dane”. JSON/original eksport zablokowany bez flagi. |
| F13 | S03 obcy | 1440×900 | 1000 | J / PL | P0 | „Dokument spoza zakresu”, lista klas z konfiguracji, przesłanki decyzji, kod `dokument_obcy`, JSON `{}`, pobranie pod nazwą wejścia. |
| F14 | S03 błąd techniczny | 1440×900 | 1100 | J / PL | P0 | „Nie udało się przetworzyć dokumentu”; etap, kod `LLM_TIMEOUT`, czas; brak wyniku ekstrakcji, eksport według §3.3.5a, „Ponów analizę”. Bez starego cache jako wyniku. |
| F15 | S03 zmiana klasy | 1440×900 | 900 | J / PL | E1 | Dialog z klasami aktywnego zestawu; „Zmień i wyodrębnij ponownie”, „Anuluj”; szkic rozstrzygnięty przed otwarciem. |
| F16 | S03 układ pośredni | 1024×768 | 1300 | J / PL | E1 | Dwa panele, miniatury ukryte, źródło i fragment dowodu widoczne, „Tekst strony”. |
| F17 | S03 tablet | 768×1024 | 1500 | J / PL | E1 | Zakładki Dokument/Formularz/JSON/Dowody; Formularz aktywny, pełny wynik, jedna kolumna. |
| F18 | S03 telefon dane | 360×800 | 1700 | J / PL | E1 | Dokument/Dane/JSON, Dane aktywne; wartości i dowody pionowo; „Pobierz JSON”; dolny odstęp chroni ostatnie pole. |
| F19 | S03 telefon dowód | 360×800 | 1300 | C / PL | E1 | Dokument aktywny, „Strona 1”, fragment bez obrysu, „Położenie przybliżone”, „Wróć do pola Tytuł zamówienia”. |
| F20 | S06 klasy | 1440×900 | 1200 | J / PL | E1 | Karty klas i liczby pól z YAML, wersja zestawu, specjalna karta obcego, „Szczegóły”. |
| F21 | S07 YAML odczyt | 1440×900 | 1400 | C / PL | E1 | Pola/YAML/Podgląd formularza/Test; YAML i formularz 60/40; „Kopiuj”, „Pobierz przelew.yaml”. |
| F22 | S08 proces | 1440×900 | 1600 | J / PL | E1 | 6 etapów §3.8 z diagnozą regionów i pokryciem, model/licencja/region z konfiguracji, legenda braków. |
| F23 | S03 diagnoza | 1440×900 | 1400 | C / PL | E1 | Panel 400 px: Dokument/Strona/Region, R3 strony 2, obraz z tekstem, obrót 90° → 0°, jakość i pewność niskie; sygnały, `zla_warstwa_ocr`. |
| F24 | S05 historia | 1440×900 | 1300 | J / PL | E1 | Dokument v1, wyniki v1 silnik/v2 korekta/v3 zatwierdzony; porównanie TED; „Przywróć v1” tworzy nową wersję. |
| F25 | S09 użytkownicy | 1440×900 | 1200 | J / PL | E3 | Syntetyczni użytkownicy, role, flaga, status; „Dodaj użytkownika”; dialog ról i zakresu spraw. |
| F26 | S10 audyt | 1440×900 | 1300 | C / PL | E3 | Filtry, zdarzenia §3.10, maskowane Było/Jest, odsłonięcie bez wartości w logu, „Eksportuj CSV”. |
| F27 | S12 logowanie | 360×800 | 950 | J / PL | E3 | E-mail, Hasło, Pokaż hasło, Zaloguj; PL/EN i motyw. Bez kont w MVP. |
| F28 | S04 partia i filtry | 1440×900 | 1300 | J / PL | E2 | Filtr partii `B-01`, sprawy + „Katalog główny”, kody; „Pobierz wyniki partii (ZIP)”, „Pobierz dowody partii”, „Ponów nieudane”. |
| F29 | S11 ustawienia | 768×1024 | 1700 | C / PL | E3 | Preferencje, dostępność, model tylko odczyt i retencja; błąd liczby dni powiązany z polem, „Zapisz retencję”. |
| F30 | S13 dostępność | 360×800 | 1300 | J / PL | E1 | Cel WCAG i „Nie przeprowadzono audytu”; znane ograniczenia PDF/OCR, kontakt z konfiguracji, powrót. |
| F31 | S14 404 | 360×800 | 800 | J / PL | E1 | „Nie znaleziono strony”, „Przejdź do nowej analizy”; H1 z fokusem. |
| F32 | S14 500 | 1440×900 | 900 | C / PL | E1 | Komunikat §3.14, ID zdarzenia, „Spróbuj ponownie”; brak danych dokumentu i stack trace. |
| F33 | S03 niezapisany szkic | 1440×900 | 900 | J / PL | E1 | Dialog §3.3.7 po kliknięciu eksportu; zapis v2 vs szkic, trzy jednoznaczne akcje; zamiar kontynuacji zachowany. |
| F34 | S03 błąd zapisu | 360×800 | 1200 | C / PL | E1 | „Nie zapisano. Szkic zachowano w tej sesji”, „Ponów zapis”; JSON v2 i szkic rozdzielone; eksport wstrzymany. |
| F35 | S03 odmowa odsłonięcia | 360×800 | 800 | J / PL | E3 | Dialog odmowy §1.4 nad F12 w układzie telefonu, zamaskowane dane; „Zamknij” przywraca fokus. |
| F36 | S07 test i walidacja | 1440×900 | 1500 | J / PL | E2 | YAML z błędem „Linia 14: brak normalizatora”; zapis/aktywacja zablokowane; wynik poprzedniego testu opisany jako nieaktualny. |
| F37 | S07 aktywacja gotowa | 1440×900 | 900 | C / PL | E2 | Dialog „Aktywuj zestaw v2?”, lista zmian i wyniki testów, wpływ na nowe zadania, „Aktywuj”/„Anuluj”. |
| F38 | S03 wiele obrysów | 1440×900 | 1500 | J / PL | E1 | G2 ma 3 obszary: dwa na str. 1, jeden na str. 4; kolor + ID + numer, legenda, „Następny obszar”, lokalizacja 4/5 pól. |
| F39 | S03 kolizja grup | 768×1024 | 1600 | C / PL | E1 | G2 i G3 w jednym akapicie; „Grupy nakładają się. Pokazano oznaczenia pól”; osobne obrysy NIP/nazwy, bez wspólnej obwiedni. |
| F40 | S03 niejednoznaczny | 1440×900 | 1200 | J / PL | P0 | Baner „Nie ustalono jednoznacznie klasy dokumentu”, powód od silnika, bez panelu kandydatów; eksport zablokowany. Panel kandydatów: E1. |
| F41 | S03 wiele dokumentów | 1440×900 | 1300 | J / PL | P0 | Baner „Wiele dokumentów”, zakresy stron przekazane przez silnik, kod `wiele_dokumentow`; wybór segmentu dopiero E1; „Kontrakt eksportu wielu dokumentów nieustalony”. |
| F42 | S04 eksport częściowy | 1440×900 | 1400 | J / PL | E2 | Podsumowanie §4.7: Przykład wariantu A: 3 uwzględnione (pełny/częściowy zgodny/obcy), 3 pominięte (awaria/niejednoznaczny/wiele dokumentów), ścieżki, „Pobierz 3 wyniki”, osobny raport. Wariant B osobno ujawnia niezgodności i ewentualne znaczniki awarii (§3.3.5a). |
| F43 | S03 pełny EN | 1440×900 | 1300 | C / EN | E1 | Pełny widok angielski opisany w §9.3; cytaty i klucze pozostają źródłowe. |
| F44 | S01 reflow | 320×800 | 1400 | J / EN | E1 | Treść 288 px, pełny baner EN i długi plik; jeden przycisk w wierszu, zawijanie komunikatu uploadu. |
| F45 | S03 reflow | 320×800 | 2000 | C / EN | E1 | Dane z długimi etykietami, cytatami i kodami; trzy zakładki, JSON zawijany, brak poziomego scrolla strony. |
| F46 | S06 brak konfiguracji | 1440×900 | 1000 | J / PL | E2 | „Błąd konfiguracji. Brak poprawnego zestawu klas. Analiza zablokowana.” Link do szczegółów; nigdy `{}`. Ten sam komunikat obowiązuje w MVP na S01. |
| F47 | S07 aktywowanie | 1440×900 | 900 | C / PL | E2 | „Aktywowanie…”; przyciski chwilowo zablokowane, brak podwójnego zapisu; aktywna stara wersja do potwierdzenia backendu. |
| F48 | S07 błąd aktywacji | 1440×900 | 1000 | J / PL | E2 | „Nie aktywowano. Nadal aktywny v1. Ponów”; błędna klasa wymieniona, nowy zestaw nieaktywny. |
| F49 | S14 403 | 768×1024 | 1024 | C / PL | E3 | KS-1, „Wróć do spraw”, bez treści obiektu. |
| F50 | S12 nieudane logowanie | 360×800 | 1050 | C / EN | E3 | “Sign in”, “Email”, “Password”, “Incorrect email or password”, “Try again”; brak ujawnienia istnienia konta. |
| F51 | S03 częściowy i braki | 1440×900 | 1600 | J / PL | P0 | „Wynik częściowy”, lista pięciu powodów z §3.3.5 na pięciu różnych polach syntetycznych; JSON `null` i ostrzeżenia według wybranej polityki §3.3.5a, sprawdzone i nieprzetworzone strony jawnie, kod przy polu; filtr „Braki (5)”. |
| F52 | S03 tekst strony | 1440×900 | 1600 | J / PL | P0 | „Tekst strony”, str. 2, „Źródło: OCR”, błąd OCR i cytat; link powrotu do pola, tekst zawijany. |
| F53 | S03 zapisywanie | 1440×900 | 1300 | J / PL | E1 | „Zapisywanie…”, szkic widoczny, eksport i zatwierdzenie czekają; po potwierdzeniu „Zapisano v3”. |
| F54 | S01/S04 kolizja ścieżki | 1440×900 | 1100 | C / PL | E2 | Dwa `sprawa/a.pdf` o różnych skrótach; dialog §4.7: nowa wersja/osobna paczka/anuluj, bez `(2)` i nadpisania. |
| F55 | S07 aktywacja zakończona | 1440×900 | 1200 | J / PL | E2 | „Zestaw v2 aktywny”, lista klas i wersji, stare zadanie v1 nadal opisane jako v1; nowe używa v2. |
| F56 | S01/S03 karta modeli i gotowość | 1440×900 | 1600 | J / PL | P0 | Karta §3.1.2: wszystkie modele i role, największy, parametry/licencje/wagi, kraj firmy i serwera, OCR/shim, wersje/rewizja kontraktu. Gotowość API: stan, przyczyna, „Sprawdź ponownie”; komunikaty braku klucza/401/403/limitu/braku sieci z §3.1.1 są wariantami tego komponentu. |
| F57 | S01/S03 OCR niedostępny | 1440×900 | 1200 | J / PL | P0 | „OCR niedostępny. Strony wymagające OCR pozostaną nieprzetworzone”; dostępna analiza tekstu; w S03 lista stron nieprzetworzonych i brak obietnicy odczytu skanu. |
| F58 | S01/S03 OCR shim | 1440×900 | 1300 | J / PL | P0 | „OCR tymczasowy (shim): {komponent}, {wersja}”; dowód rzeczywistego skanu, źródło OCR i oznaczenie zamiennika, bez deklaracji podłączenia własnego modelu. |
| F59 | S01/S03 dodanie klasy i pola | 1440×900 | 1800 | J / PL | P0 | Storyboard §4.6.1: YAML poza GUI → restart/przeładowanie → wersja w S01 → analiza PDF → formularz z `numer_noty`, następnie `oznaczenie_sprawy` → JSON i dowody. Jeden arkusz przebiegu, bez edytora S07. |
| F60 | S03 dowody i pobranie | 1440×900 | 1500 | J / PL | P0 | Tabela strona/cytat/źródło/metoda, reguła i przesłanki wyliczenia, braki i pokrycie stron; „Pobierz dowody (JSON)”, osobny artefakt `evidence/odwolanie.json`. |
| F61 | S03 polityka eksportu przy brakach | 1440×900 | 1500 | J / PL | P0 | Dwa opisane warianty §3.3.5a obok siebie do decyzji projektowej: A blokada; B ostrzeżenie i świadome pobranie z brakami; osobna nierozstrzygnięta reguła zastępczego `{}` przy awarii. Nieustalona polityka blokuje sporny eksport. To arkusz porównania, nie przełącznik w produkcie. |

### 9.3. Jeden kompletny widok EN: F43 (E1)

Nagłówek: “New analysis”, “PL | EN” (EN aktywne), “Theme”. Baner: “Demo mode. Synthetic data only. No sign-in.” Okruszki: “Recent analyses / przyklad_01 / odwolanie.pdf”. Tytuł pliku i nazwa firmy pozostają oryginalne; klasa “Appeal”, stan “Complete”, “Result v1 · engine”.

Lewy panel: “Thumbnails”, “Page 1 of 12”, “Zoom out”, “100%”, “Zoom in”, “Fit to width”, “PDF | Page text”. Prawy: “Form | JSON | Evidence”, “All fields” aktywne, “Needs attention (0)”, “Missing values (0)”. Karty “Appellant”, “Contracting authority”, “Procurement”; pole “Contract title” z oryginalnym tytułem PL i kluczem `ZamowieniePubliczne.tytul`. Dowód: “Page 1 · Source: PDF text”, cytat PL, “Show evidence”, “Approximate location. Exact evidence geometry is unavailable.” Akcje: “Copy”, “Download odwolanie.json · v1”. Pod JSON: “Saved result v1. Evidence is stored separately.” Brak edycji i zatwierdzania w wariancie MVP. Komunikat czytnika po wyborze dowodu: “Evidence shown: page 1”.

### 9.4. Macierz widok × stan × szerokość × motyw × język

Macierz docelowa E1–E3 wskazuje **reprezentatywne** ramki, nie udaje wykonania pełnego iloczynu wariantów. Wszystkie strony docelowe dziedziczą KS-1/2/3/4 i zachowanie breakpointów z §3. Wspólne komponenty stanów są w F00; docelowa implementacja wymaga sprawdzenia PL i EN oraz J i C przy każdej szerokości. Poniżej pokrycie projektu i oczekiwane adaptacje.

| Widok | Stany reprezentowane | Szerokości ramek (CSS px) | Motyw | Język | Ramki |
|---|---|---|---|---|---|
| S01 | pusty, wybrane/błędne pliki, menu, reflow, kolizja | 320/360/1440 | J/C | PL/EN | F01–04, F44, F54 |
| S02 | w toku, mieszany wynik, lista braków i kody | 360/1440 | J/C | PL | F05–07; EN dziedziczy tłumaczenia statusów §3.2.1 |
| S03 | pełny, JSON, dowód, tekst strony | 320/360/768/1024/1440 | J/C | PL/EN | F08–10, F16–19, F43, F45, F52 (desktop 1440) |
| S03 | częściowy, obcy, awaria, niejednoznaczny, wiele dokumentów | 1440 | J/C | PL | F13–14, F40–41, F51; ≤768 jak F18 |
| S03 | korekta, szkic, zapisywanie, błąd zapisu, odmowa | 360/1440 | J/C | PL | F11–12, F15, F33–35, F53 |
| S03 | diagnoza, wiele obrysów, kolizja grup | 768/1440 | J/C | PL | F23, F38–39; telefon diagnoza pełnoekranowa |
| S04 | lista partii, filtry, eksport częściowy | 1440 | J | PL | F28, F42; ≤768 karty jak F07 |
| S05 | historia i porównanie | 1440 | J | PL | F24; ≤768 Było/Jest w jednej kolumnie |
| S06 | lista klas, błąd konfiguracji | 1440 | J | PL | F20, F46; ≤768 karty w 1/2 kolumnach |
| S07 | odczyt, błędny szkic/test, aktywacja: gotowa/w toku/błąd/sukces | 1440 | J/C | PL | F21, F36–37, F47–48, F55; telefon odczyt |
| S08 | opis procesu | 1440 | J | PL | F22; ≤768 kroki pionowo |
| S09 | lista użytkowników i dialog ról | 1440 | J | PL | F25; ≤768 karty i dialog pełnej szerokości |
| S10 | lista audytu i maskowanie | 1440 | C | PL | F26; ≤768 karty |
| S11 | preferencje, retencja i błąd pola | 768 | C | PL | F29; telefon jedna kolumna |
| S12 | formularz, błąd uwierzytelnienia | 360 | J/C | PL/EN | F27, F50 |
| S13 | nieaudytowany prototyp i ograniczenia | 360 | J | PL | F30; EN tłumaczy treść §3.13 |
| S14 | 404/500/403 | 360/768/1440 | J/C | PL | F31–32, F49; EN teksty §3.14 |

Dla list brak danych i brak wyników filtra używają F00 z dokładnymi tekstami §3; ładowanie stosuje szkielety KS-3, awaria odczytu KS-2, odmowa KS-1. Takie adaptacje nie są doliczane jako osobne ramki. Minimalny zestaw makiet P0: **F01, F02, F05, F06, F08, F10, F13, F14, F40, F41, F51, F52, F56, F57, F58, F59, F60, F61 (18 ramek)**. Wszystkie 1440×900, J/PL. F40/F41 są prostymi banerami. F59/F61 to pojedyncze arkusze przebiegu/porównania, bez doliczania wewnętrznych kroków jako dodatkowych ramek. F00 jest wspólną planszą komponentów, poza liczbą minimum P0. Pozostałe ramki należą do etapów wskazanych w §9.2; macierz zachowuje docelowe warianty i nie rozszerza P0.

| Pokrycie P0 | Ramki |
|---|---|
| S01 upload i konfiguracja/gotowość | F01–02, F56–59 |
| S02 w toku i wyniki | F05–06 |
| S03 formularz, JSON, dowody, tekst strony | F08, F10, F51–52, F60 |
| S03 obcy, awaria i banery | F13–14, F40–41 |
| Sporne polityki eksportu do decyzji | F61 |

---

## 10. Otwarte pytania

Pytania nie wstrzymują ukończenia tego projektu; propozycje zachowują wskazane ograniczenia.

1. Jaką gotową bibliotekę komponentów i przeglądarkę PDF wskaże użytkownik? React + TypeScript są ustalone; pakiet dla jury musi zawierać gotowe zasoby statyczne.
2. Jaki kontrakt geometrii i diagnozy zwróci własny odczyt PDF/OCR (wymiary, współrzędne, transformacje, regiony, pewności)? P0 działa dowodem strona + fragment; geometria w E1 dopiero po potwierdzeniu, bez automatycznego wyboru pierwszego trafienia.
3. Jak serializować wiele dokumentów w jednym PDF w ocenianym wyniku? Do ustalenia z mentorem eksport tego stanu jest zablokowany.
4. Jak pogodzić jawne `null` z polami wymaganymi przez aktualny walidator, który go nie dopuszcza? UI pokazuje braki; wariant A blokuje eksport, wariant B pozwala świadomie pobrać wynik z `null` i ostrzeżeniem o niezgodności (§3.3.5a). Wybór należy do użytkownika. Osobno U-Q14: brak pliku czy zastępcze `{}` przy awarii.
5. Jaki model, dostawca, licencja i europejski region zostaną potwierdzone dla API? Brak potwierdzenia blokuje wywołania. Klucz i kanał przekazania jury poza Git.
6. Jaki mechanizm logowania w E3: konta lokalne czy SSO, oraz jaki zasięg spraw/zespołów? MVP bez logowania jest rozstrzygnięte.
7. Czy zatwierdzamy propozycję czterech oczu, bieżącej zapisanej wersji jako domyślnego eksportu i etykiet `etykieta: {pl, en}` w YAML? Do tego czasu to oznaczone [PROP] rozwiązania docelowe.
8. Jakie limity plików/partii oraz retencja demo i pełnej wersji? UI pobiera rzeczywisty limit z backendu i blokuje upload bez konfiguracji limitów (§3.1.2). Demo serwerowe wymaga izolacji i usuwania po sesji.
9. Czy aktywacja całego zestawu YAML może działać bez restartu? Niezależnie od mechanizmu obowiązuje atomowa aktywacja i przypięcie wersji do zadania.
10. Czy zaakceptować odczyt YAML na telefonie bez edycji oraz nazwę sprawy bez obowiązkowej sygnatury? To propozycje do etapów E2/E3.
11. Czy OCR liczy się jako największy model (U-Q15) i jak raportować MoE? Do wyjaśnienia karta ujawnia wszystkie modele, także OCR; nie przypisujemy punktów.
12. Który wariant eksportu przy brakach i regułę eksportu przy awarii zatwierdza użytkownik (§3.3.5a), z uwzględnieniem odpowiedzi mentora U-Q13/U-Q14? Żaden nie jest domyślnie przyjęty.
