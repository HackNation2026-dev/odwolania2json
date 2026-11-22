# E18: wybór modelu LLM (i ustawienia effort)

**Wynik nie jest oficjalnym F1.** Ten sam prompt p2, to samo wejście (tekst PDF), te same sprawy; ewaluator produkcyjny; bootstrap po sprawach (ziarno 20261122).
Czas: pod obciążeniem maszyny (load avg ok. 20–35 na 8 rdzeniach, kilka grup liczy naraz): czasy i RSS ORIENTACYJNE, nie do decyzji. Model „bazowy” to `MiniMax-M3.1-Flash-Preview` (API zwraca `MiniMax-M3.1-Flash`).

## Zakres: inny dostawca
Zlecenie dopuszcza tylko klucz MiniMax (`MINIMAX_KEY_FILE`). W katalogu domowym są pliki z kluczami innych usług, ale NIE zostały użyte: spoza zakresu zlecenia, a zgodność dostawcy z wymogiem UE/EOG rozstrzyga ADR-002. Dlatego E18 porównuje modele MiniMax dostępne na jednym kluczu
(`MiniMax-M3`, `M2.7`, `M2.5`; `MiniMax-M3.1` dało HTTP 400, `M2.1` i `M2` HTTP 404) oraz ustawienia `effort` bazowego modelu. Porównania z innymi rodzinami (mniejszy otwarty model z UE) pozostają otwarte.

## Hipoteza i reguła (prerejestracja pkt 6)
Mniejszy lub tańszy model zastępuje bazę, gdy dolna granica ΔF1 (model − baza) > −0,02 oraz tokeny wyjściowe na dokument i mediana czasu wywołania nie są większe od bazy. Rozmiar parametrów nie jest ujawniony przez API; „tańszy” = mniej tokenów i krótszy czas (cennika nie znamy).

## Metoda
Modele: 25 spraw rozwojowych (75 dokumentów pozytywnych; negatywów nie uruchamiano), 2 powtórzenia, tekst + p2, temperatura 0. Baza do porównania: `e10-text-p2` na tych samych dokumentach i powtórzeniach 1–2. Effort: `low`/`high` na 12 sprawach (36 dok.), 3 powtórzenia (z E10).
API przyjmuje `output_config.effort`, ale nie weryfikowaliśmy, czy model je uwzględnia (sprawdzić po różnicy tokenów).

## Wyniki
| Model / ustawienie | F1 [95%] | ΔF1 vs baza (sparowane) | Zakres | Tokeny wej./wyj. na dok. | Czas wywołania (mediana) | Reguła: zastępuje bazę |
|---|---|---|---|---|---|---|
| M3 | 0.961 [0.943; 0.976] | +0.035 [+0.002; +0.076] (cand>base) | 138 wierszy, powt. 2 | 1964 / 706 (baza 2566) | 4.19 s (baza 13.75 s) | TAK |
| M2.7 | 0.955 [0.934; 0.972] | +0.029 [-0.004; +0.071] (nierozstrzygnięte) | 150 wierszy, powt. 2 | 1272 / 1119 (baza 2566) | 4.5 s (baza 13.75 s) | TAK |
| M2.5 | 0.959 [0.948; 0.969] | +0.033 [+0.007; +0.067] (cand>base) | 150 wierszy, powt. 2 | 1189 / 1107 (baza 2566) | 11.17 s (baza 13.75 s) | TAK |
| effort-low | 0.942 [0.931; 0.954] | +0.036 [-0.004; +0.095] (nierozstrzygnięte) | 108 wierszy, powt. 3 | 1195 / 915 (baza 2528) | 16.28 s (baza 15.45 s) | nie |
| effort-high | 0.940 [0.910; 0.963] | +0.033 [-0.006; +0.080] (nierozstrzygnięte) | 108 wierszy, powt. 3 | 1121 / 1535 (baza 2528) | 8.64 s (baza 15.45 s) | TAK |

## Jak to działa i dlaczego tak wyszło
M3 zwraca ok. 706 tokenów wyjściowych na dokument wobec 2566 u bazy: nie generuje długiego rozumowania, więc jest szybszy i tańszy w tokenach, a F1 na tych sprawach nie jest gorszy. Czas wywołania wyznaczają tokeny wyjściowe (rozumowanie), nie wejściowe.

## Ograniczenia
Jeden dostawca; 25 spraw (przesiew effortu na 12); 2 powtórzenia modeli; negatywów nie uruchamiano, więc nie mierzymy fałszywych pozytywów routera dla modeli; aliasy MiniMax mogą zmienić rewizję (zapisane nazwy zwrócone przez API: patrz `E18/wyniki.json`).
Czas pod obciążeniem (nie do decyzji); tokeny są wiążące. Brak ceny, więc „koszt” = tokeny.

## Wniosek decyzyjny
Reguła z prerejestracji wskazuje: M3, M2.7, M2.5, effort-high. Pewność umiarkowana: jeden dostawca, 25 spraw, 2 powtórzenia; przed ADR sprawdzić M3 w wariancie końcowym E11 (D) i potwierdzić licencję/lokalizację modelu w ADR-002.

## Stan końcowy (finalizacja z replayu, bez wywołań API; 22.11.2026)
- Wykonane: M3 (138 wierszy; 12 niepowtórzonych w `*.jsonl`, 62 wiersze błędów w `.errors.jsonl`), M2.7 (150), M2.5 (150), effort low/high (108 wierszy każdy, 12 spraw). Wiersze z błędem sieci/limitu nie weszły do liczb (łącznie 379 wierszy w `E18/raw/*.errors.jsonl`).
- Uwaga do interpretacji: wszystkie cztery warianty mają ΔF1 ok. +0.03 wobec bazy. To może znaczyć, że baza (M3.1-Flash-Preview, długie rozumowanie, 2566 tok. wyj.) jest słabsza na tych sprawach, ale 24 z 435 wierszy bazy to stałe niepowodzenia odpowiedzi (puste/niepoprawne), które obniżają jej wynik; różnica nie jest więc czystą różnicą jakości modeli. Dolna granica przedziału > −0.02 jest spełniona przez wszystkie z wyjątkiem low (nie spełnia warunku czasu), ale warunek „nie gorszy” różni się od „lepszy”: przedziały M2.7, effort-low i effort-high obejmują 0.
- Inny dostawca (UE/EOG): NIE sprawdzono (klucz poza zakresem zlecenia, ADR-002). M3.1 pełne: HTTP 400.
- M3 w wariancie D: zob. E11 (DM3, 87 dok. tekstowych, skany 39 dok.): wynik nierozstrzygnięty wobec bazy, próbka na skanach mała.
- Decyzja: kandydatem na model domyślny jest MiniMax-M3 (najniższe tokeny wyjściowe i czas, F1 nie gorszy, ΔF1 +0.035 [+0.002; +0.076]); M2.5 i M2.7 są alternatywami. Decyzję trzeba potwierdzić powtórzeniem po odnowieniu limitu i sprawdzeniem negatywów; licencja i lokalizacja w ADR-002.
