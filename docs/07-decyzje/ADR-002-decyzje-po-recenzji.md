---
wersja: 0.6.0
aktualizacja: 2026-11-21
status: decyzje użytkownika, częściowo otwarte
---

# ADR-002: decyzje użytkownika po recenzji architektury (Codex)

Data: 2026-11-21. Kanał: rozmowa z asystentem. Kontekst: architektura na tablicy Miro „HackNation 2026: architektura” (https://miro.com/app/board/uXjVELOtLzE=/), niezależna recenzja Codex (`codex exec`, tryb tylko do odczytu, werdykt „akceptuję z poprawkami”), zestawienie punktów 1–15. ADR-001 i [proponowany stos](../04-architektura/proponowany-stos.md) pozostają historią; ten dokument ma pierwszeństwo tam, gdzie się różnią.

## Zaakceptowane

| Nr | Decyzja |
|---|---|
| 1 | Python 3.13, jeden pakiet, `requirements.txt`, CLI jako główne wejście. |
| 2 | Bez Rusta w rdzeniu. |
| 9 | Serializacja wyłącznie w kodzie: stała kolejność kluczy, `null` zamiast braku klucza, typy jak w referencjach. |
| 10 | Dowody (strona, fragment) w osobnym `evidence/`, poza ocenianym JSON-em. |
| 11 | Obcy dokument: pusty JSON pod nazwą oryginału. Błąd techniczny to osobny stan: raport, kontynuacja batcha, kod wyjścia, zapis atomowy. |
| 13 | Ewaluator przybliżonego F1: zbiór kontrolny z całych spraw, osobne miary klasyfikacji, struktury i pól, próg 80% tylko dla wskazanych pól tekstowych, listy dopasowywane po treści. |
| 14 | Loader referencji nakłada poprawki organizatora na migawkę bazową i mapuje nazwy (`potwierdzenie_przelewu.pdf` ↔ `przelew.json`); wynik nazwany według wejścia. |
| — | Kolejność budowy po poprawkach Codexa: najpierw F1 wszystkich klas, GUI po stabilnym F1. |

## Odrzucone lub otwarte

| Nr | Decyzja użytkownika |
|---|---|
| 3 | **Odczyt tekstu z PDF (`pypdfium2`): nie akceptuję.** Będzie własne, lepsze rozwiązanie, dostarczone później. |
| 4 | **OCR (`rapidocr`): nie akceptuję.** Jak w pkt 3. |
| 5 | Klasyfikacja: do ponownego rozpatrzenia po zmianach w pkt 3 i 4. |
| 6 | Regex tylko dla pól o stałym formacie. **Pewność i sposób działania każdego wzorca ustalamy eksperymentalnie i pilnujemy testami mutacyjnymi.** Pozostałe pola: LLM; jaki i jak dokładnie wynika z pkt 3, 4 i 5. |
| 7 | Dostawca i model LLM: otwarte. Zgodność API według użytkownika: **MiniMax technicznie zaleca API zgodne z Claude (Anthropic); DeepSeek, GLM i OpenAI — API zgodne z OpenAI.** Klient LLM musi więc obsłużyć oba protokoły. Do sprawdzenia przy wyborze: wymóg organizatora, że API świadczy firma z serwerów w UE/EOG (README organizatora, l. 158; FAQ: UE) oraz otwarta licencja modelu. |
| 8 | YAML jako opis klasy: użytkownik nie był pewien, czy wystarczy; zgoda na eksperyment. Wynik: [eksperyment YAML](../05-weryfikacja/eksperyment-yaml-klasy-2026-11-21.md). |
| 12 | **Nie zwracać automatycznie starego wyniku z cache tylko dlatego, że API nie odpowiada.** Cache wolno użyć wyłącznie jako zwykłej optymalizacji przy identycznym kluczu (dokument, model, prompt, konfiguracja, wersja ekstraktora), nie jako zastępstwa przy awarii. Awaria API = jawny błąd techniczny (pkt 11). |
| 15 | GUI: React i TypeScript jako baza, prawdopodobnie Next.js. Konkretne biblioteki wskaże użytkownik. |

## Konsekwencje

- Nie wybieramy bibliotek odczytu PDF, OCR ani GUI w imieniu użytkownika.
- Projekt ekstrakcji (kandydaci wartości, role, scalanie) czeka na pkt 3–5.
- Testy mutacyjne są obowiązkowe dla wzorców regex (pkt 6) i walidatora wyniku.

## Uzupełnienie: odpowiedzi mentora (2026-11-21)

Źródło: [odpowiedzi mentora](../01-zadanie/zrodla/odpowiedzi-mentora-2026-11-21.md).

- Pkt 4 (OCR) zyskuje priorytet: test zawiera skany i dokumenty mieszane. Własne rozwiązanie musi obsłużyć oba przypadki.
- Pkt 7: wymóg brzmi „hostowane w Europie”. Rozmiar modelu do punktacji to największy model w całym systemie, także wieloagentowym.
- Pkt 15: GUI jest obowiązkowe (decyzja zespołu); minimum to wgranie pliku, pełna wersja to aplikacja dla urzędu (wersjonowanie, przeglądanie spraw, użytkownicy, uprawnienia). Zakres pełnej wersji do zaprojektowania. Kolejność „GUI po stabilnym F1” dotyczy pełnej wersji; minimum warto mieć wcześnie.
- Dostarczenie: tylko pip na teście; Docker wyłącznie deweloperski.
- Typy: numery jako tekst albo `null`, zgodnie z referencjami.

## Uzupełnienie: zasady użytkownika dla przypadków brzegowych (2026-11-21, interpretacja asystenta do potwierdzenia)

- Wszystkie przypadki brzegowe mają nazwy w dokumentacji ([katalog](../05-weryfikacja/katalog-przypadkow-brzegowych.md)).
- Najpierw zestaw testowy wygenerowany z oryginalnych danych organizatora (oryginały nienaruszone), dopiero potem budowa systemu.
- Przetwarzanie wsadowe wielu dokumentów, ale **każdy dokument niezależnie** — wymóg. Ekstrakcja nie korzysta z innych dokumentów sprawy.
- Dokument może zawierać wszystkie informacje w nieuporządkowanej formie. **Braki trzeba jawnie wskazywać** (w raporcie poza ocenianym JSON, gdzie pole ma `null`).

## Uzupełnienie: brak „happy path”, system odrzuceń (użytkownik, 2026-11-21)

- Nie zakładamy ścieżki idealnej. Gdy dokument nie pasuje do wzorca, system robi tyle, ile się da, i **katalogizuje typ odstępstwa** (np. brak pewności, czy strona jest skanem, mieszana, czy ma warstwę OCR).
- Wymagana **bogata wewnętrzna klasyfikacja** dokumentu, strony i regionu (źródło tekstu, jakość, pewność), niezależna od klasy biznesowej (odwołanie, pełnomocnictwo, przelew, obcy).
- Typy odstępstw i odrzutów mają kody w katalogu, tak jak przypadki brzegowe.

## Uzupełnienie: decyzje GUI (użytkownik, 2026-11-21)

- React + TypeScript; gotowa biblioteka komponentów UI: tak (konkretną nazwę wskaże użytkownik; projekt pozostaje neutralny wobec biblioteki — interpretacja asystenta).
- Logowanie: projektujemy w UI; nie wiadomo, czy trafi do kodu. **MVP bez logowania.**
- **Bez OpenUI** na tym etapie (elementy generatywne poza zakresem; projekt może zostawić punkt rozszerzenia).
- Projekt UI uwzględnia poprawki z recenzji Codex i zakłada możliwość wprowadzenia nowych pomysłów (grupy z wieloma obrysami, diagnoza stron i regionów, typy odrzutów, stany „obcy / niejednoznaczny / błąd techniczny”).

## Uzupełnienie: OCR i kolejne kroki (użytkownik, 2026-11-21)

- Zespół planuje **własny model ML do OCR**, ale nie może go dostarczyć na tym etapie. Architektura musi traktować OCR jako wymienny komponent z określonym kontraktem (wejście: obraz strony lub regionu; wyjście: tekst z geometrią i pewnością), a do czasu dostarczenia modelu działać bez niego i jawnie diagnozować strony wymagające OCR.
- Kolejność: ocena architektury, GUI i pomysłów (Fable, Codex) → zapis, krytyczny przegląd i commit → **plik OpenAPI i backend**.

## Uzupełnienie: tymczasowy OCR (shim) i model ETL/ELT (użytkownik, 2026-11-21)

- Do czasu dostarczenia własnego modelu ML do OCR używamy **tymczasowego shima OCR** (wcześniejsza propozycja: lokalny OCR instalowany przez pip, działający na CPU, np. rapidocr + onnxruntime) za tym samym kontraktem komponentu OCR. **Decyzja o własnym modelu ML się nie zmienia**; shim jest zastępstwem i może zostać usunięty bez zmian w reszcie systemu. Pkt 4 (odrzucenie rapidocr jako rozwiązania docelowego) pozostaje w mocy.
- Architekturę opisujemy jako **klasyczny proces ETL/ELT wzbogacony o warstwę OCR i ekstraktory oparte na AI**.
- Następny krok: opis API (OpenAPI) i zachowania systemu.

## Uzupełnienie 0.6.0: Next.js i konsekwencje ELT

„Prawdopodobnie Next.js” w pkt 15 oznacza dopuszczalność **wyłącznie statycznego eksportu** dostarczanego jako gotowe zasoby w pakiecie pip. U jury nie wymagamy Node ani serwera Next.js. Budowanie frontendu odbywa się przed wydaniem pakietu. Konsekwencja: funkcje wymagające serwera Node nie są częścią tego wariantu; API i obsługę zadań zapewnia Python. React + TypeScript pozostają decyzją, konkretne biblioteki wskazuje użytkownik.

[Architektura wewnętrzna 0.6.0](../04-architektura/architektura-wewnetrzna.md) opisuje E → trwały L → T1–T5, kontrakty OCR/odczytu, dowodów, braków i diagnoz oraz wspólny katalog kodów wykonawczych. Konsekwencje ELT: ponowne transformacje bez powtarzania OCR i porównywalne pomiary, kosztem miejsca na dysku, wersjonowania i retencji artefaktów. V1 ograniczamy do E/L/T1/T3/T5; T2, T4 i regiony wymagają wykazania poprawy F1. Shim OCR nie zmienia pkt 4. To rozwinięcie projektu, nie potwierdzenie gotowości produktu ani wyboru bibliotek odczytu.

Zadania z odpytywaniem i dysk bez bazy oraz polityki eksportu/`null`/wielu dokumentów pozostają **propozycjami do decyzji użytkownika** (§9–10 architektury). Uzupełnienie nie rozstrzyga otwartych odpowiedzi mentora.

## Uzupełnienie: decyzje przed OpenAPI (użytkownik, 2026-11-21)

Numeracja według listy decyzji z rozmowy (i `architektura-wewnetrzna.md` §9–§10):

1. **Model wykonania i trwałość:** użytkownik pyta o bazę PostgreSQL. Rekomendacja asystenta: na teście u jury (wyłącznie pip) bez serwera bazy — katalog roboczy na dysku, ewentualnie SQLite (biblioteka standardowa Pythona); PostgreSQL jako opcja pełnej wersji serwerowej za tym samym interfejsem repozytorium danych. **Do potwierdzenia przez użytkownika.**
2. **Pola wymagane bez wartości w dokumencie** i 3. **błąd techniczny / brak OCR:** obecne ustalenia potwierdzone jako dobre. Dokument spoza typów → `{}` pod nazwą pliku wejściowego (potwierdzone wcześniej przez mentora).
4. **Jeden dokument = jeden PDF**, o nieograniczonej liczbie stron. Nie dzielimy pliku na kilka dokumentów wynikowych.
5. **Geometria (bbox) obowiązkowa** dla dowodów.
6. **Kod, API, nazwy plików i identyfikatory po angielsku.** Wyjątek: oceniany JSON zachowuje klucze z referencji organizatora (kontrakt konkursowy). Dokumentacja zespołu pozostaje po polsku.
7. **Klucz API:** zmienna środowiskowa; przy jej braku program prosi o podanie klucza, wykonuje samosprawdzenie (self-check: test połączenia i autoryzacji) i dopiero wtedy przechodzi dalej — mechanizm konfiguracji.

## Uzupełnienie: model LLM i OCR (użytkownik, 2026-11-21)

8. **LLM: MiniMax przez `api.minimax.io`** (zespół ma klucz), protokół zgodny z Anthropic („tryb Claude”, zalecany przez MiniMax; endpoint `https://api.minimax.io/anthropic`). Model z eksperymentu: `MiniMax-M3.1-Flash-Preview`.
   **Ryzyko zgodności — do rozstrzygnięcia przed zgłoszeniem.** Wymóg organizatora: API świadczone przez firmę i z serwerów w UE/EOG (README organizatora, l. 158; FAQ: UE; mentor: „hostowane w Europie”) oraz wyłącznie modele open source. Ustalenia z wyszukiwania 2026-11-21:
   - `platform.minimax.io` prowadzi **Nanonoble Pte. Ltd., Singapur** (regulamin serwisu, źródło pierwotne).
   - Według serwisów zewnętrznych (standardcompute.com, llmproviders.ai — niezweryfikowane u źródła) dane osobowe są przechowywane w centrum danych w USA, lokalizacja obliczeń nieujawniona, możliwe transfery do podmiotów powiązanych w Szanghaju.
   - Wagi `MiniMax-M3.1-Flash` są publiczne na Hugging Face na **MiniMax Community License** (bezpłatnie do użytku niekomercyjnego, warunki dla komercyjnego) — to nie jest licencja open source w rozumieniu OSI; zgodność z wymogiem „open source” do potwierdzenia.
   - Rozmiar: źródła zewnętrzne podają ok. 220 mld albo 427 mld parametrów (MoE, ok. 23 mld aktywnych) — duży model obniża punkty za „moc modelu”.
   Wniosek: MiniMax nadaje się do rozwoju i eksperymentów; do zgłoszenia potrzebne potwierdzenie mentora albo dostawca/model zgodny z wymogiem. Klient LLM jest niezależny od dostawcy, więc zmiana nie wymaga przebudowy.
9. **OCR: własny model ML zespołu ma być gotowy w ciągu ok. 3 godzin** (od 2026-11-21, wieczór). Shim (rapidocr) tylko do tego czasu i jako awaryjny dostawca za tym samym kontraktem.

## Uzupełnienie: GUI, nazwa, repozytorium (użytkownik, 2026-11-21)

10. **Stos GUI:** React, TypeScript, Zod, Next.js (statyczny eksport w pakiecie pip, bez serwera Node u jury), biblioteka komponentów **gluestack** (gluestack-ui), PDF: **react-pdf.org** (`@react-pdf/renderer`) i **react-web-pdf-editor**.
    Ustalenia asystenta (2026-11-21, strony projektów): `@react-pdf/renderer` **tworzy** PDF z komponentów React, nie wyświetla istniejących plików — nadaje się do generowania raportu/eksportu, nie do podglądu dokumentu źródłowego. `react-web-pdf-editor` (MIT, 0.1.6, PDF.js) wyświetla i edytuje PDF; domyślnie ładuje worker PDF.js z CDN (unpkg) — trzeba hostować lokalnie; programowe nakładanie ramek dowodów nie jest opisane w dokumentacji — **do sprawdzenia spike'iem**; alternatywa: PDF.js lub `react-pdf` (wojtekmaj) z własną warstwą ramek.
11. **Zawężone P0 GUI zaakceptowane** (projekt UI 0.3.0).
12. **Nazwa projektu: Arkadiana** (Odwołania2JSON pozostaje nazwą zadania konkursowego).
13. **Commity etapami** zaakceptowane.
14. **Push na `origin`** zaakceptowany.

## Uzupełnienie: MiniMax zamknięty (użytkownik, 2026-11-21)

Użytkownik potwierdza: używany MiniMax jest hostowany w Europie. Punkt 8 jest **zamknięty decyzją zespołu**; wcześniejsze „ryzyko zgodności” (oparte na wyszukiwaniu asystenta) nie jest już otwartą kwestią.

## Uzupełnienie: trwałość danych (użytkownik, 2026-11-21)

1. **Wersja demo (u jury, tylko pip): SQLite** (biblioteka standardowa Pythona) + katalog roboczy na dysku dla plików i artefaktów. **PostgreSQL przy skalowanym wdrożeniu**, za tym samym interfejsem repozytorium danych (`DataRepository`). Decyzja zamknięta.

## Uzupełnienie: uzgodnienie z gałęzią `feat/python-fastapi-docker` (użytkownik, 2026-11-21)

Gałąź `feat/python-fastapi-docker` (od v0.4.0) zawiera szkielet backendu, kontrakt OpenAPI, warstwę PostgreSQL, normalizatory i plany. Decyzje użytkownika rozstrzygające rozbieżności:

- **Obowiązuje architektura v0.6.1** (`docs/04-architektura/architektura-wewnetrzna.md`), także dla kontraktu OpenAPI.
- **SQLite zostaje** w wersji demo; PostgreSQL przy skalowanym wdrożeniu.
- **PESEL to tekst** (nie liczba).
- **Panel do przeglądania bazy danych — mile widziany jako osobne narzędzie.** Nie zastępuje GUI: GUI (P0: PDF obok danych, dowody, pobranie JSON) jest czymś innym.
- **Docker: tak**, ale równolegle utrzymujemy i testujemy instalację **przez pip** (wymóg na teście).
- **Python 3.13+.**

## Uzupełnienie 0.7.0: eksport, paleta i przepływy (użytkownik, 2026-11-21)

- **Polityka eksportu: wariant A, ścisła walidacja.** Pobranie ocenianego JSON jest zablokowane, gdy `null` jest niedopuszczony przez schemat, przy błędzie technicznym, niejednoznaczności i wielu dokumentach. Zastępcze `{}` przy awarii nie jest stosowane: błąd techniczny to brak pliku wynikowego (`no_file`). Dowody i raport pozostają dostępne osobno. **Zastępuje domyślne `error_export=empty_json` z wpisu 0.6.1.** Architektura wewnętrzna §10 i `.env`/konfiguracja wymagają zsynchronizowania; do wykonania, nie zrobione w tym wpisie.
- **Paleta UI: zatwierdzona przez użytkownika** (tło #F3F5F0, powierzchnia #FDFEFC, separator #D4DCD4, tekst #202620, tekst drugorzędny #60675E, kolor główny #314A40, zaznaczenie #EBEEEB, statusy według makiet). Paleta nie definiowała ramki kontrolki: przyjęto #647D70 (focus), kontrast 4,06 na tle. **Motyw ciemny wyprowadzono z tej palety jako propozycję niezatwierdzoną** (kontrasty policzone, podgląd w pliku FigCraft, ramka F65d).
- **Przepływy użytkownika:** [user-flow.md](../04-architektura/gui/user-flow.md); ekrany i grafy w [figcraft/](../04-architektura/gui/figcraft/). Dokument wygenerował Codex na podstawie projektu UI i makiet; wymaga recenzji użytkownika.
- **Otwarte, nierozstrzygnięte:** pole klucza API w GUI (projekt-ui §3.1.1 wyklucza je, architektura opisuje wpisywanie klucza tylko w CLI); próg automatycznej galerii (propozycja: od 7 dokumentów); nazwa produktu „Arkadiana” a „Odwołania2JSON” w UI. Pełna lista: sekcja „Luki i pytania otwarte” w user-flow.md.
