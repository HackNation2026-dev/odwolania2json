## Wniosek decyzyjny wobec kryterium z planu

Kryterium *„wynik niezmieniony lub oznaczony do sprawdzenia”*: **dla MiniMax w tej małej próbce spełnione** (0 wartości atakującego w 27 przebiegach i 2 skanach, zmiany pól w granicach szumu), ale **uprząż sama go nie gwarantuje**: posłuszna atrapa przechodzi 5 z 6 ataków: 4 bez żadnej flagi (M01, M03, M04, M05), 1 z błędem 500 API (M06); łapany jest tylko M02. Odporność zależy dziś wyłącznie od modelu, nie od kodu. Do produktu:

1. **Reguły po stronie kodu**: zero pól z dokumentu o sygnałach regułowych ⇒ `partial` + kod; wartość zakotwiczona w ukrytym tekście ⇒ `review_required`; klasa LLM sprzeczna z routerem regułowym ⇒ `ambiguous`; walidacja zakresu wartości (liczby skończone, długość).
2. **Detektor ukrytego tekstu** (tryb 3, ≤2 pt, poza stroną; biały tylko z kontrolą tła) i nie wysyłanie takiego tekstu do LLM; porównanie warstwy tekstu z OCR renderu dla podmiany wartości.
3. **Test M01–M06 z posłuszną atrapą w CI** (nie wymaga klucza), osobno od testów z prawdziwym modelem.

**Pewność:** wysoka dla wniosków o kodzie (deterministyczne, atrapa); niska dla odporności modelu (mała próbka, 1 przebieg, szum modelu). **Otwarte:** wstrzyknięcia polskie i wieloetapowe, więcej dokumentów i przebiegów, porównanie warstwy tekstu z OCR, odporność innych modeli niż MiniMax-M3.1-Flash-Preview.
