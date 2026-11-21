# FAQ – Odwołania2JSON (wersja 1.0)

Źródło: treść przekazana przez użytkownika w tej rozmowie, 21.11.2026.
Wersja źródła: 1.0. Oryginalnego adresu publikacji FAQ nie podano.
Podział na części i treść odpowiedzi zachowano; nagłówki pytań sformatowano jako Markdown.
Podgląd linku FlowHunt z wiadomości nie jest dodatkowym wymaganiem organizatora.

## 1/4

### Na czym polega wyzwanie Odwołania2JSON?

Celem jest stworzenie aplikacji, która automatycznie analizuje dokumenty PDF związane z odwołaniami do Krajowej Izby Odwoławczej, rozpoznaje ich rodzaj (klasyfikuje) i dokonuje ekstrakcji zawartych w nich informacji w ustrukturyzowane dane JSON.

### Jakie dokumenty powinno obsługiwać rozwiązanie?

Trzy rodzaje: odwołanie do KIO, pełnomocnictwo oraz potwierdzenie przelewu. Każdy dokument ma własną strukturę oczekiwanych danych.

### Czy aplikacja musi rozpoznawać rodzaj dokumentu?

Tak. Jednym z elementów wyzwania jest automatyczna klasyfikacja dokumentu i zastosowanie odpowiedniego schematu ekstrakcji.

### Jaki powinien być wynik działania aplikacji?

Dla każdego przetworzonego dokumentu aplikacja powinna wygenerować JSON zgodny z odpowiednim schematem udostępnionym w repozytorium.

### Jakie informacje należy wyodrębniać z dokumentów?

Z odwołań m.in. strony postępowania, dane zamówienia i zaskarżoną czynność; z pełnomocnictw – mocodawców, pełnomocników i podpisujących; z przelewów – kwotę, datę, rachunki i tytuł płatności.

## 2/4

### Co zrobić, gdy dokument nie zawiera wymaganej informacji?

Nie należy wymyślać brakujących danych. W polach, których schemat dopuszcza brak wartości, należy zastosować null zgodnie z udostępnionymi przykładami.

### Czy aplikacja powinna obsługiwać również zeskanowane dokumenty?

Tak. Takie dokumenty występują w opisanym problemie. Rozwiązanie powinno więc uwzględniać zarówno PDF-y zawierające tekst, jak i dokumenty wymagające rozpoznawania tekstu przez OCR.

### Jakie dane treningowe otrzymują uczestnicy?

Repozytorium zawiera co najmniej 39 zestawów przykładów. Każdy obejmuje trzy dokumenty PDF oraz odpowiadające im pliki JSON z danymi referencyjnymi.

### Czy dane testowe będą takie same jak treningowe?

Nie. Organizator przewiduje osobny, nieudostępniony uczestnikom zbiór testowy. Rozwiązanie w związku z tym powinno poprawnie przetwarzać również nowe dokumenty. Wgląd w te dane można uzyskać na stoisku Urzędu Zamówień Publicznych.

### Jak będzie oceniana jakość rozwiązania?

W preselekcji decyduje miara F1 (100%). W etapie finałowym F1 odpowiada za 50% oceny, a pozostałe 50% dotyczy elastyczności i możliwości rozbudowy rozwiązania o nowe klasy dokumentów.

## 3/4

### Czy można korzystać z modeli AI i zewnętrznych API?

Wymagane są komponenty open source, w tym otwartoźródłowe modele językowe, dostępne do użytku bez ograniczeń i opłat licencyjnych. W trakcie hackathonu polecamy wykorzystać dostępne LLM przez API, jednak muszą to być modele które umożliwiają również lokalną instalacje. Adres API musi prowadzić do usługodawcy i serwera znajdującego się na terenie UE.

Zwracamy uwagę, że rozwiązania będą testowane na komputerze „biurowym”, bez GPU, więc decydowanie o „dużym modelu” uruchamianym lokalnie jest bardzo ryzykowne. Oznacza to, że rozwiązania jakie nam dostarczycie powinny zawierać klucz API do usługi, które wykorzystujecie. Obiecujemy nie nadużywać tokenów.

### 12a. Czy konieczne jest przygotowanie CLI?

Tak, to kluczowe jest przygotowanie CLI razem z instrukcją umożliwiające uruchomienie aplikacji z wiersza poleceń.

### 12b. Czy konieczne jest przygotowanie interfejsu użytkownika?

Nie jest konieczne, ale posiadanie będzie dodatkowo punktowane. Idealne rozwiązanie to GUI umożliwiające wgranie PDF, uruchomienie analizy i podgląd wygenerowanego JSON. Preferowany jest widok obok siebie: dokument źródłowy i wyodrębnione dane.

## 4/4

### Czy rozwiązanie musi umożliwiać dodawanie nowych typów dokumentów?

Na starcie wymagane są trzy wskazane typy. Możliwość dodawania kolejnych typów i pól przez konfigurację, bez przebudowy kodu, będzie szczególnie istotna podczas oceny finałowej.

### Czy należy stworzyć kompletny system do obsługi postępowań KIO?

Nie. Przedmiotem wyzwania jest działający prototyp przetwarzający dokumenty PDF na JSON. Nie jest wymagane tworzenie pełnego systemu prowadzenia spraw odwoławczych.

### Co należy przygotować do zgłoszenia rozwiązania?

Wymagane są tytuł projektu i link do działającego prototypu na GitHubie, umożliwiającego wgranie dokumentów oraz odczyt wyników ekstrakcji. Dodatkowo można dostarczyć dokumentację techniczną i wyniki własnych testów.

### Gdzie znajdę szczegółowe wytyczne techniczne?

https://github.com/Urzad-Zamowien-Publicznych/hacknation-2026
