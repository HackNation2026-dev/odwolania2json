---
wersja: 0.5.0
aktualizacja: 2026-11-21
status: BRIEF — wejście dla projektanta UI (Claude), potem recenzja Codex i zatwierdzenie użytkownika
---

# Brief: projekt interfejsu Odwołania2JSON

## Cel

Zaprojektować interfejs aplikacji Odwołania2JSON: funkcje, strony, widoki, menu, stopkę i **dokładną treść** każdego widoku. Proces: projekt (Claude) → niezależna recenzja (Codex) → zatwierdzenie użytkownika → makiety w figcraft (Claude). Na tym etapie nie piszemy kodu.

## Co robi silnik (kontekst)

PDF z akt sprawy odwoławczej → klasyfikacja (odwołanie do KIO, pełnomocnictwo, potwierdzenie przelewu, dokument obcy) → ekstrakcja pól do JSON właściwej klasy. Obcy dokument daje `{}` pod nazwą pliku. Każde pole ma dowód (strona i fragment źródła) zapisywany poza ocenianym JSON-em. Klasy i pola definiuje YAML (nowa klasa bez zmiany kodu). Wejściem są pliki tekstowe, skany i dokumenty mieszane. Błąd techniczny (np. brak odpowiedzi API) to osobny stan, nie pusty wynik. Szczegóły: [wymagania](../../03-wymagania/README.md), [kontrakt danych](../../03-wymagania/kontrakt-danych.md), [ADR-002](../../07-decyzje/ADR-002-decyzje-po-recenzji.md), [eksperyment YAML](../../05-weryfikacja/eksperyment-yaml-klasy-2026-11-21.md), wzorce wyniku w `docs/02-materialy/organizator-uzp/oczekiwane-json/`.

## Wymagania organizatora dotyczące GUI (cytaty w [punktacji](../../01-zadanie/punktacja.md))

- GUI dodatkowo punktowane (finał: 1–10 pkt za dodatkowe funkcje, np. GUI).
- FAQ 12b: idealnie GUI umożliwiające wgranie PDF, uruchomienie analizy i podgląd wygenerowanego JSON; preferowany **widok obok siebie**: dokument źródłowy i wyodrębnione dane.
- „Szczególnie premiowane” rozwiązania wspierające **transparentność procesu ekstrakcji**.
- Zgłoszenie: działający prototyp umożliwiający wgranie dokumentów i odczytanie rezultatów.
- Za łatwość dodawania nowych klas i pól: 1–20 pkt (warto to pokazać w UI).

## Decyzje zespołu

- GUI **obowiązkowe**. Minimum: wgranie pliku i PDF obok JSON. Pełna wersja: aplikacja dla urzędu — wersjonowanie dokumentów, przeglądanie dokumentów lub całych paczek (spraw), użytkownicy, uprawnienia. Zakres pełnej wersji do przemyślenia: zaproponuj podział MVP / pełna wersja.
- React + TypeScript, prawdopodobnie Next.js. **Konkretne biblioteki UI wskaże użytkownik** — nie wybieraj ich; projektuj tak, żeby dało się to zbudować na typowej bibliotece komponentów.
- **Mobile first**: telefon, tablet, desktop; w pełni responsywnie.
- Motyw **jasny i ciemny**.
- Języki **polski i angielski** (polski domyślny).
- **OpenUI** (https://www.openui.com/, repo thesysdev/openui, licencja MIT, React/Next.js) dla elementów generatywnych, jeśli takie będą. Model opisuje UI w OpenUI Lang, renderer składa go z naszych komponentów. Ograniczenia: każdy element generatywny to wywołanie LLM, które musi być hostowane w Europie i liczy się do punktacji „największego modelu w systemie”; nie zakładaj chmurowego OpenUI Gateway (Thesys) — model wołamy bezpośrednio. Elementy generatywne nie mogą być na ścieżce krytycznej (wgranie → wynik → JSON musi działać bez nich). Zaproponuj, gdzie generatywny UI daje realną wartość, a gdzie wystarczy zwykły widok.

## Ograniczenia

- Projekt nie może podszywać się pod realną instytucję: bez godeł, logotypów i nazw UZP/KIO jako marki aplikacji. Nazwa robocza: „Odwołania2JSON”.
- Dostępność: sektor publiczny w Polsce — projektuj pod WCAG 2.1 AA (kontrast w obu motywach, obsługa klawiaturą, etykiety, focus).
- Dane osobowe w dokumentach (PESEL, nazwiska): uwzględnij w projekcie maskowanie i uprawnienia.

## Oczekiwany wynik

Jeden dokument `docs/04-architektura/gui/projekt-ui.md` (po polsku), zawierający co najmniej:

1. Role i macierz uprawnień.
2. Architekturę informacji: mapa stron, nawigacja (menu na desktopie, tablecie i telefonie), stopka, nagłówek, przełączniki motywu i języka.
3. Dla każdej strony/widoku: cel, kto ma dostęp, **dokładna treść** (nagłówki, etykiety pól, przyciski, komunikaty — PL, z odpowiednikami EN dla kluczowych tekstów), komponenty, stany (pusty, ładowanie, błąd, częściowy, brak uprawnień), zachowanie na breakpointach (proponowane: 360, 768, 1024, 1440 px), interakcje i skróty.
4. Przepływy: wgranie pojedynczego pliku → analiza → przegląd PDF|JSON z dowodami → korekta → akceptacja → eksport; wgranie paczki/sprawy; wersjonowanie dokumentu i wyniku; obsługa skanów, dokumentów mieszanych, obcych i błędów technicznych; zarządzanie użytkownikami; konfiguracja klas (YAML) z podglądem.
5. Model danych widoczny w UI (sprawa, dokument, wersja, ekstrakcja, pole, dowód, użytkownik, rola, wpis audytu).
6. Elementy generatywne (OpenUI): gdzie, po co, jaki model, co gdy model niedostępny.
7. Tokeny wizualne dla motywu jasnego i ciemnego (kolory, typografia, odstępy, promienie), neutralne wobec biblioteki.
8. Zakres MVP na hackathon vs pełna wersja, z uzasadnieniem punktowym.
9. Lista ramek do figcraft: nazwa, rozmiar (telefon 360×800, tablet 768×1024, desktop 1440×900), motyw, co pokazuje.
10. Otwarte pytania do użytkownika.
