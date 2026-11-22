# Blokery i uwagi o uprzęży (grupa B)

Harnessu nie zmieniano. Zaobserwowano:

1. **Klucz współdzielony i 429.** `harness/llm.py` ponawia 429 tylko 2 razy z odstępem 1–2 s; przy kilku grupach na jednym kluczu 17 z pierwszych ~110 wywołań padło z `llm_rate_limit`. Obejście: `pola/llm_calls.py` (ponowienia zewnętrzne do 6× z odstępem 10–45 s, błędy przejściowe nie trafiają do cache). Błędów nie zliczano jako „odpowiedzi poza schematem”.
2. **Ewaluator.** `appeal` w referencji ma tylko pierwszego pełnomocnika w `Odwolujacy[].pelnomocnik`, a pełnomocnictwo wymienia wielu; nie jest to błąd harnessu, ale wymaga zasady w ekstraktorze.
3. **Router uprzęży** (`RulesRouter`) nie obsługuje dokumentów bez tytułu (35/147 poprawnych bez nagłówka) i myli wyciąg bankowy z przelewem (5/5): zgłoszone jako wynik E06, nie poprawiane.
4. **OCR bez wątków.** `RapidOcr` w uprzęży nie ustawia `intra_op_num_threads`; zestaw OCR grupy B zbudowano przed uwagą koordynatora o obciążeniu (jeden proces, `nice`), bez ograniczenia wątków.
5. Zestawu skanów grupy A (`odczyt/ZESTAW.md`) w chwili pracy nie było: E08 i E06 używają własnego, syntetycznego zestawu OCR (render 150 dpi + `jak_skan`), opisanego w README E08.
