# Odwołania2json

**Od dokumentów do danych. Inteligentna transformacja odwołań KIO do modelu JSON**

# Krótki opis wyzwania

Każdego roku do systemu zamówień publicznych trafiają tysiące dokumentów zawierających kluczowe informacje o postępowaniach, wykonawcach, pełnomocnikach i czynnościach zamawiających. Najczęściej są to dokumenty tekstowe z kluczowymi, jednak ułożonymi w przeróżny sposób, informacjami z reguły na pierwszych trzech stronach. Celem wyzwania jest stworzenie rozwiązania, które automatycznie zamieni wielodokumentową sprawę administracyjną w spójny, ustrukturyzowany model danych JSON gotowy do dalszego wykorzystania przez systemy informatyczne administracji publicznej.

# 1. Wprowadzenie

Urząd Zamówień Publicznych odpowiada za funkcjonowanie systemu zamówień publicznych w Polsce oraz wspiera uczestników rynku w prawidłowym stosowaniu przepisów prawa. Jednym z elementów tego systemu są postępowania odwoławcze prowadzone przed Krajową Izbą Odwoławczą.

Sprawa odwoławcza nie jest pojedynczym dokumentem. Stanowi zbiór wielu powiązanych ze sobą dokumentów zawierających informacje o wykonawcach, zamawiających, pełnomocnikach, postępowaniach, płatnościach, czynnościach procesowych i innych elementach wymagających dalszego przetwarzania.

Obecnie większość takich dokumentów występuje w postaci plików PDF o zróżnicowanej strukturze. Część z nich powstaje elektronicznie, część jest wynikiem skanowania dokumentów papierowych. Informacje niezbędne do dalszej obsługi sprawy są rozproszone pomiędzy wieloma dokumentami i często zapisane w różny sposób.

Dla człowieka zrozumienie takiej dokumentacji jest stosunkowo proste. Dla systemów informatycznych stanowi jednak duże wyzwanie. Aby możliwa była automatyzacja dalszych procesów, dane muszą zostać najpierw przekształcone do postaci ustrukturyzowanej.

W praktyce oznacza to konieczność przejścia od modelu:

**wiele dokumentów PDF → analiza treści → identyfikacja informacji → model danych JSON**

Wyzwanie dotyczy zatem budowy rozwiązania, które pozwoli automatycznie przekształcać wielodokumentowe sprawy administracyjne w kanoniczny model danych możliwy do dalszego wykorzystania przez systemy administracji publicznej.

Najciekawsze rozwiązania mają szansę stać się podstawą pilotażowych wdrożeń realizowanych przez Urząd Zamówień Publicznych.

# 2. Wyzwanie

Zaprojektuj i zaimplementuj rozwiązanie, które:

1.  przyjmie dokument PDF składający się na odwołanie: dokument z treścią odwolania, pełnomocnictwo, dokument potwierdzenia przelewu
2.  rozpozna rodzaj dokumentu
3.  wyodrębni informacje biznesowe istotne dla danego typu dokumentu,
4.  wygeneruje:
    - JSON dla każdego dokumentu zgodny z https://github.com/Urzad-Zamowien-Publicznych/hacknation-2026/blob/main/oczekiwane-json

Szczegółowa struktura danych:
https://github.com/Urzad-Zamowien-Publicznych/hacknation-2026/blob/main/oczekiwane-json/odwolanie.json

zestawy treningowe:
https://github.com/Urzad-Zamowien-Publicznych/hacknation-2026/blob/main/dane

# 3. Oczekiwany rezultat

Oczekiwanym rezultatem jest działająca aplikacja pobierająca plik PDF i zwracająca plik JSON w ustalonym formacie.

Rozwiązanie powinno zawierać:

### Moduł przetwarzania dokumentów

Odpowiedzialny za:

- analizę dokumentów,

- ekstrakcję informacji,

- klasyfikację dokumentów,

- budowę modelu danych.

### Interfejs użytkownika

Umożliwiający:

- załadowanie dokumentu,

- uruchomienie procesu analizy,

- podgląd wygenerowanych danych (najlepiej w układzie dzielonego widoku: dane wygenerowane \<\>dane źródłowe - umożliwiającego sprawną weryfikację danych bez konieczności oddzielnego otwierania dokumentów źródłowych).

### Wynik działania

Generujący:

- JSON dla dokumentu

# 4. Wymagania formalne

Projekt przesyłany do oceny powinien zawierać:

- tytuł projektu,

- Link do GitHub działającego prototypu umożliwiający wgranie dokumentów i odczytanie rezultatów ekstrakcji informacji.

Dodatkowo uczestnicy mogą dostarczyć:

- repozytorium projektu,

- dokumentację techniczną,

- wyniki własnych testów jakości.

# 5. Wymagania techniczne

Rozwiązanie musi:

- wykorzystywać wyłącznie komponenty open source (w tym otwarto-źródłowe modele językowe),

- umożliwiać uruchomienie w środowisku lokalnym (on-premise) bez GPU (LLM po API).

Szczególnie premiowane będą rozwiązania:

- umożliwiające konfigurację nowych klas dokumentów bez modyfikacji kodu źródłowego (jedynie przez pliki konfiguracyjne),

- wspierające transparentność procesu ekstrakcji danych.

# 6. Sposób testowania i walidacji

Ocena zostanie przeprowadzona na dwóch zbiorach danych:

### Zbiór treningowy

Udostępniony uczestnikom podczas realizacji wyzwania.

### Zbiór testowy

Nieudostępniony uczestnikom przed oceną.

Zbiór testowy będzie zawierał kompletne sprawy administracyjne przygotowane przez organizatora.

Wyniki wygenerowane przez rozwiązanie zostaną porównane z zestawem danych referencyjnych przygotowanym przez ekspertów merytorycznych.

Podstawową miarą jakości będzie [wskaźnik F1](https://en.wikipedia.org/wiki/F-score).

# 7. Kryteria oceny

Etap 1 - preselekcja:

### 1. Jakość ekstrakcji danych (F1 Score) – 100%

Ocena zgodności wyników z danymi referencyjnymi na nieznanym zbiorze testowym.

Etap 2 - wybór finalny:

### 1. Jakość ekstrakcji danych (F1 Score) – 50%

Ocena zgodności wyników z danymi referencyjnymi na nieznanym zbiorze testowym.

### 2. Elastyczność i możliwość rozbudowy rozwiązania – 50%

Łatwość dodawania nowych typów dokumentów i nowych klas danych bez konieczności przebudowy całego systemu.

