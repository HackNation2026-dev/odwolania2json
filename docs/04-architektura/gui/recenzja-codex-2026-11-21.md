---
wersja: 0.5.0
aktualizacja: 2026-11-21
status: surowa recenzja Codex (codex exec, tylko odczyt) projektu projekt-ui.md v0.1.0
---

**Akceptuję z poprawkami — projekt spełnia główny kierunek wymagań, ale przed budową makiet trzeba rozstrzygnąć ochronę danych, zapisywanie korekt, zakres MVP i brakujące stany.**

Odwołania do sekcji i linii poniżej dotyczą [projekt-ui.md](projekt-ui.md). To ocena specyfikacji, nie działającego interfejsu. Nie zmieniałem plików.

1. **[KRYTYCZNE] Ochronę danych można ominąć innymi widokami.**  
   **Miejsce:** §3.3.9–13, l. 457–485; §6.5, l. 775.  
   **Dowód:** projekt blokuje „Pobierz” bez flagi „Dane osobowe”, ale pozostawia „Kopiuj”, eksport dowodów i „Pobierz oryginał”. Dla PDF przewiduje tylko „nakładkę zasłaniającą”. Brief, l. 38, wymaga „maskowania i uprawnień”.  
   **Problem:** zasłonięcie obrazu nie chroni tekstu ani oryginalnego PDF pobranego przez przeglądarkę. Brakuje jednej polityki dla formularza, JSON, schowka, dowodów, ZIP, historii i asystenta.  
   **Zmiana:** zdefiniować macierz dostępu obejmującą wszystkie kanały. Pełne dane udostępniać dopiero po autoryzacji backendu; użytkownikowi bez flagi dostarczać bezpieczną reprezentację dokumentu. Demo bez kont ograniczyć do danych syntetycznych, najlepiej lokalnie lub z izolacją sesji.

2. **[WAŻNE] Awaria konfiguracji może zostać przedstawiona jako poprawna klasyfikacja „obcy”.**  
   **Miejsce:** §3.6, l. 565.  
   **Dowód:** „Brak skonfigurowanych klas. Każdy dokument zostanie uznany za spoza zakresu”. Tymczasem `docs/07-decyzje/ADR-002-decyzje-po-recenzji.md`, pkt 11, rozdziela obcy dokument i błąd techniczny.  
   **Problem:** brak klas nie dowodzi, że dokument jest obcy; eksport `{}` ukrywa niesprawność systemu.  
   **Zmiana:** przy braku poprawnej konfiguracji blokować analizę i pokazywać błąd konfiguracji. Przy częściowym wczytaniu klas określić zasady dalszej pracy i zakazać przedstawiania niepełnej klasyfikacji jako pewnego wyniku.

3. **[WAŻNE] Nie wiadomo, co zostanie zatwierdzone lub pobrane przy niezapisanych zmianach.**  
   **Miejsce:** §3.3.7, l. 431–443; §3.3.12, l. 470–477; §4.1, l. 648–651.  
   **Dowód:** użytkownik wybiera „Zapisz” przy polu, a następnie osobno „Zapisz korektę”. Jednocześnie dostępne są „Zatwierdź wynik” i „Pobierz JSON”.  
   **Problem:** dwa poziomy zapisu zwiększają liczbę kroków i ryzyko eksportu poprzedniej wersji. Nie określono zachowania przy błędzie zapisu ani zmianach po zatwierdzeniu w tej samej sesji.  
   **Zmiana:** nazwać zapis pola „Zastosuj” albo uprościć zapis do jednej operacji. Zatwierdzenie i eksport mają jawnie wskazywać wersję oraz wymagać zapisania lub odrzucenia szkicu. Dodać stan „Zapisywanie” i „Nie zapisano — ponów”.

4. **[WAŻNE] Obrys dowodu w ciemnym motywie nie spełnia zadeklarowanego kontrastu.**  
   **Miejsce:** §7.1, l. 791–806.  
   **Dowód:** dla `evidence-border` projekt deklaruje „≥3 : 1 względem białej strony”. Obliczony kontrast `#F2C14E` na `#FFFFFF` wynosi **1,68:1**.  
   **Zmiana:** użyć ciemnego obrysu dowodu także w ciemnym motywie — strona PDF pozostaje biała. Poprawić tabelę obliczeń:

   | Para | Projekt | Obliczenie |
   |---|---:|---:|
   | `text` / `bg`, jasny | 16,9 | 16,88 |
   | `text` / `bg`, ciemny | 15,3 | 15,32 |
   | `on-primary` / `primary`, ciemny | 7,9 | 7,90 |
   | `warning` / `warning-subtle`, ciemny | 10,0* | 7,93 |
   | `evidence-border` / biała strona, ciemny | ≥3 | **1,68** |

   \* W części wierszy nie wskazano jednoznacznie tła. Podstawowe pary tekstu mają dobry kontrast; problemem jest obrys i niedokładna dokumentacja, a nie cała paleta.

5. **[WAŻNE] MVP na dobę ma sprzeczne priorytety i zbyt szeroką ścieżkę P0.**  
   **Miejsce:** §1.1, l. 45; §8.1, l. 860–874.  
   **Dowód:** „Maskowanie PESEL działa także w MVP”, ale maskowanie, EN i „Tekst strony” trafiają do P1. P0 obejmuje jednocześnie foldery, responsywność, dwa motywy i podświetlanie dowodów.  
   **Problem:** dostępna alternatywa tekstowa PDF jest odkładana, choć P0 deklaruje dostępność. Brakuje też sposobu dostarczenia frontendu przy wymaganiu „Wyłącznie pip” (`odpowiedzi-mentora-2026-11-21.md`, l. 16).  
   **Zmiana:** minimum: pliki PDF → lista statusów → PDF/dane/JSON → dowód jako strona i fragment → pobranie wyniku. Zachować wymagania zespołu dotyczące języka, motywów i dostępności albo jawnie uzgodnić ich ograniczenie. Przesunąć podświetlanie współrzędnych, foldery wielosprawowe, korekty i zatwierdzanie poza pierwszy etap. Opisać frontend dołączony jako gotowe zasoby do pakietu Python, bez budowania Node u jury. OpenUI zostawić poza dobą.

6. **[WAŻNE] OpenUI chroni wartości komponentów, ale nie chroni treści odpowiedzi.**  
   **Miejsce:** §6.3–5, l. 745–775; F23, l. 985.  
   **Dowód:** „Model nie podaje wartości pól”, lecz `Text` i `Callout` przyjmują dowolny tekst. F23 odpowiada „Tak” na pytanie o posiadanie pełnomocnictwa na podstawie zgodności nazwiska.  
   **Problem:** zgodność osoby nie potwierdza zakresu, ważności ani skuteczności pełnomocnictwa. Model nadal może zmyślić opis lub ujawnić dane w tekście. Sprawdzenie, czy cytat występuje na stronie, nie potwierdza wniosku.  
   **Zmiana:** ograniczyć odpowiedzi do wskazania dokumentów i porównania pól; pokazywać „Ta sama osoba występuje w obu dokumentach”, bez oceny prawnej. Walidować identyfikatory względem sprawy i uprawnień, filtrować kontekst przed wysłaniem oraz walidować również tekstowy wariant zastępczy. Zachować bezpośrednie API, hosting w Europie i model nie większy od już używanego; uruchomienie uzależnić od potwierdzenia licencji i dostawcy.

7. **[WAŻNE] Eksport wielu spraw i kolizje nazw nie mają kompletnego przepływu.**  
   **Miejsce:** §3.1, l. 208–233; §3.4, l. 530; §4.2–3, l. 657–667.  
   **Dowód:** §4.2 przewiduje „Pobierz wynik (ZIP) na poziomie partii”, ale S04 nie opisuje tej akcji. Dodanie osobnego dokumentu jako „{nazwa} (2)” zmienia nazwę, choć `docs/03-wymagania/README.md`, UZP-06, wymaga zachowania nazw i podfolderów.  
   **Zmiana:** określić tożsamość partii, obsługę PDF w katalogu głównym i głębszych podfolderów, kolizje nazw oraz mapowanie ścieżek eksportu. Dodać ekran podsumowania częściowego eksportu, który jasno wymienia pominięte błędy techniczne.

8. **[WAŻNE] Lista ramek nie wystarcza do wykonania całego projektu bez zgadywania.**  
   **Miejsce:** §9, l. 893–999.  
   **Dowód:** F00–F27 nie obejmują m.in. S04, S11, S13, S14, okna niezapisanych zmian, błędu zapisu, odmowy odsłonięcia danych ani pełnego przepływu aktywacji YAML. F07 i F18 mają jednocześnie rozmiar 360×800 oraz inną „wysokość”.  
   **Zmiana:** dodać macierz „widok × stan × szerokość × motyw × język” i wskazać reprezentatywne ramki. Uzupełnić kluczowe stany oraz przynajmniej jeden widok EN i sprawdzenie reflow 320 px. Oddzielić rozmiar viewportu od wysokości przewijanej treści.

9. **[WAŻNE] Formularz wymaga doprecyzowania semantyki pól i walidacji.**  
   **Miejsce:** §3.3.6–7, l. 381–437.  
   **Dowód:** wzorzec `oczekiwane-json/odwolanie.json` wymaga ustalenia czynności „WYŁĄCZNIE na podstawie pierwszego zarzutu”, czego etykiety nie wyjaśniają. Wzorzec BZP dopuszcza końcówkę `/##`, a projekt podaje tylko `RRRR/BZP########`.  
   **Zmiana:** dodać pomoc „dotyczy pierwszego zarzutu”, pełny format BZP oraz jawne mapowanie „Tak/Nie” na `1/0`. Uzupełnić pełne ścieżki współdzielonych pól zamawiającego. Nazwy głównych kluczy są poprawne; tekstowy PESEL słusznie wynika z późniejszej decyzji zespołu, mimo liczby we wzorcu.

10. **[WAŻNE] Obsługa klawiatury jest opisana częściowo, a telefon wymaga dopracowania powrotu do pracy.**  
    **Miejsce:** §3.1, l. 201–233; §3.3.15–16, l. 505–524; §7.4.  
    **Dowód:** „cała strefa jest przyciskiem”, choć zawiera dwa przyciski. Skróty zakładek opisują desktop, podczas gdy telefon ma inny zestaw zakładek.  
    **Zmiana:** strefę wgrywania pozostawić kontenerem z osobnymi kontrolkami. Określić semantykę listy pól, zachowanie strzałek podczas edycji i powrót fokusu po obejrzeniu dowodu. Na telefonie zachować pozycję przewijania i widoczność pola nad klawiaturą ekranową. Przyklejony pasek nie może zasłaniać treści. Zakładki zamiast PDF|dane na 360 px są właściwą decyzją.

11. **[DROBNE] Kilka tekstów i stanów przeczy pozostałym sekcjom.**  
    **Miejsce:** l. 40, 496, 712, 911, 937.  
    **Dowód:** baner demo jest „nie do zamknięcia na stronie startowej”, lecz F03 go zwija. Obcy dokument wymienia na sztywno trzy klasy mimo rozszerzalności YAML. JSON jest „bez przekształceń”, choć podgląd maskuje wartości. F08 pokazuje wszystkie pola mimo domyślnego filtra ostrzeżeń.  
    **Zmiana:** rozstrzygnąć wariant banera, generować nazwy klas z konfiguracji, oznaczyć maskowany podgląd jako różniący się od pliku i ujednolicić stan filtra.

Pokrycie dziesięciu punktów briefu: **wszystkie są obecne, ale nie wszystkie są gotowe wykonawczo**. Role, model danych, podział wersji i pytania opisano konkretnie. Architektura informacji, treści i stany wszystkich stron, przepływy, OpenUI, tokeny oraz lista ramek wymagają powyższych uzupełnień. Szczególnie skrótowe są S10–S14.

Warto zachować: rozdzielenie `{}` od błędu technicznego, dowody poza ocenianym JSON, PDF obok danych na desktopie, przełączanie dokument/dane na telefonie, formularze z YAML, statusy jako tekst i ikona oraz neutralną markę. To dobrze odpowiada wymaganiom organizatora i pracy urzędnika.