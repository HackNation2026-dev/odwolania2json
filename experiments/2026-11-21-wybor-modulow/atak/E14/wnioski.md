## Wniosek decyzyjny wobec kryterium z planu

Kryterium *„zgodność z architekturą §6 i §9.1”* jest **spełnione** dla klas błędów LLM i sieci w uprzęży (14 przypadków atrapy + 6 sieciowych: kody zgodne, brak zmyślonych danych, brak wycieku kanarka, brak podmiany z cache), z trzema lukami do zamknięcia w produkcie:

1. **Walidacja `base_url` i wysyłka klucza** (C02): allowlista hosta, https, jeden nagłówek zależnie od protokołu.
2. **Budżet LLM** (L02, L03): limit wywołań i tokenów na dokument i wsad, wyłącznik po serii błędów, `context_limit` przed wysłaniem.
3. **Odrzucanie nieznanych pól** formularza z kodem (C01) zamiast cichego przyjęcia.

Test kanarka (każda klasa błędu → grep po odpowiedziach, logach, dysku) jest tani i powinien wejść do CI produktu jako stały. **Pewność:** wysoka dla wniosków o kodach i wycieku w uprzęży (deterministyczne, powtarzalne); niska dla zachowania prawdziwego dostawcy. **Otwarte:** awarie prawdziwego OCR przez HTTP; cache produktu (klucz z modelem i promptem); zachowanie przy `Retry-After` w produkcie. Dodatkowa luka znaleziona w E13 (M06): wartość tekstowa z samych cyfr w polu `kwota` daje `inf` → `GET /result` zwraca 500 (patrz E13).
