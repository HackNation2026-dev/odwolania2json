---
wersja: 0.1.0
aktualizacja: 2026-11-22
status: przyjęta technicznie; zgodność dostawcy zapasowego z wymogami konkursu otwarta
---

# ADR-007: łańcuch dostawców LLM (główny i zapasowy)

## Kontekst

Wynik `process` zależy od odpowiedzi LLM. Limit konta dostawcy głównego (MiniMax) wyczerpał się w nocy 22.11.2026 i ponownie w dniu pomiaru produktu (HTTP 429): bez odpowiedzi modelu każdy dokument dostaje `{}`. Zadanie Z04 wymaga, żeby wywołanie LLM nie zerowało wyniku wsadu.

## Decyzja

1. **Łańcuch dwóch dostawców** (`llm/chain.py`): główny, potem opcjonalny zapasowy. Zapasowy jest konfigurowany wyłącznie przez środowisko (`LLM_FALLBACK_*`); adres i klucz **nie mają wartości domyślnych w kodzie**.
2. **Przełączenie** następuje po wyczerpaniu ponowień dostawcy głównego z powodu: 429, 5xx, błędu sieci lub limitu czasu, 402 (brak środków), odrzuconego żądania (inne 4xx) oraz 401/403. Odrzucony klucz głównego zostawia w raporcie ostrzeżenie `llm_primary_unauthorized` i komunikat na stderr.
3. **Odpowiedź poza schematem** najpierw dostaje ponowienie semantyczne u tego samego dostawcy; dopiero drugie niepowodzenie przekazuje dokument zapasowemu. Odpowiedź zapasowego przechodzi tę samą walidację (pydantic) i to samo ponowienie.
4. **Wyłączenie dostawcy w trakcie wsadu:** po błędzie konta (401/403, 402) do końca wsadu; po błędzie przejściowym (429, 5xx, sieć) na `LLM_PROVIDER_COOLDOWN_S` sekund (domyślnie 300). Kolejne dokumenty nie czekają wtedy na ponowienia niedziałającego dostawcy.
5. **Budżet wsadu jest wspólny**: limit wywołań (`LLM_MAX_CALLS`) i tokenów (`LLM_MAX_TOTAL_TOKENS`) liczy się łącznie dla obu dostawców.
6. **Self-check przed wsadem** sprawdza obu. Wsad rusza, gdy działa co najmniej jeden; niedziałający główny przy działającym zapasowym i niedziałający albo błędnie skonfigurowany zapasowy to ostrzeżenia. Gdy nie działa żaden, kod wyjścia 2 bez przetwarzania.
7. **Raport** (`report.jsonl`, pole `llm`) zapisuje dla każdego dokumentu: dostawcę (`primary` \| `fallback`), model, powód przełączenia i ostrzeżenia. Klucze i nagłówki nie trafiają do raportu, logów ani wyjątków (testy kanarka dla obu kluczy).
8. **Ta sama walidacja adresu** co dla głównego: tylko `https`, host z `LLM_ALLOWED_HOSTS`. Nagłówki dodatkowe (`LLM_FALLBACK_HEADERS`, `LLM_FALLBACK_USER_AGENT`) nie mogą podmienić nagłówka klucza; znacznik `{session}` to identyfikator bieżącego uruchomienia (jeden UUID na proces). Domyślny `User-Agent` to `odwolania2json/<wersja>`: program przedstawia się własną nazwą.

## Konsekwencje

- **Zgodność dostawcy zapasowego z wymogiem konkursu („firma i serwery w UE/EOG”, model open source) jest nieznana.** Dla konfiguracji używanej w pomiarze (GLM `glm-5.3-flash` przez OpenCode) nie mamy dowodu lokalizacji ani licencji. Kod niczego w tej sprawie nie zakłada. Wynik uzyskany na dostawcy zapasowym nie dowodzi, że rozwiązanie spełnia ten wymóg; decyzja o użyciu u jury należy do człowieka ([pytania otwarte](pytania-otwarte.md), ADR-002 pkt 8).
- **Warunki planu OpenCode Go:** plan jest przeznaczony dla agentów kodujących, a dostawca monitoruje ruch pod kątem nadużyć. Użycie go do wsadów ekstrakcji dokumentów jest ryzykiem dla konta użytkownika, przyjętym przez użytkownika 22.11.2026 na czas pomiaru. Program nie podszywa się pod inny klient; nie należy tego zmieniać konfiguracją. Endpoint płatny tego dostawcy (bez `/go`) zwraca 402 przy pustym saldzie.
- **Dwa modele to dwa rozkłady błędów.** F1 zmierzony na jednym modelu nie przenosi się na drugi; raport pokazuje, który model odpowiedział dla ilu dokumentów, i tak trzeba cytować wyniki.
- Treść dokumentów trafia do drugiego podmiotu. Dla danych konkursowych (syntetycznych) to bez znaczenia; dla danych rzeczywistych wymaga osobnej zgody.
- Bez skonfigurowanego zapasu zachowanie jest takie jak przed tą decyzją (ADR-006): błąd LLM po ponowieniach to `{}` i wpis w raporcie.
- Przełączanie także przy 401/403 dostawcy głównego oznacza, że zły klucz nie zatrzymuje wsadu, gdy zapas działa: jedynym śladem jest ostrzeżenie w raporcie i na stderr.
