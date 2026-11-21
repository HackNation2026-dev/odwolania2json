# UZP — doprecyzowania Discord, 21.11.2026

Źródło: wiadomości przekazane przez użytkownika w rozmowie. Autorzy i godziny według przekazanej treści. Brak bezpośrednich odnośników Discord i samego załącznika prezentacji. Poniżej zachowano istotne wypowiedzi organizatorów; nie jest to pełny eksport kanału.

## Radek Ratajczak — 09:38, fragment prezentacji wyzwania

Jakie dane macie do dyspozycji?
39 zestawów przykładowych danych
117 dokumentów PDF
3 rodzaje dokumentów: odwołanie, pełnomocnictwo i potwierdzenie przelewu
Referencyjne pliki JSON oraz ground_truth.yaml

Jak oceniamy rozwiązania?
Preselekcja: 100% – jakość ekstrakcji (F1)
Finał: 50% – jakość ekstrakcji (F1), 50% – elastyczność i możliwość rozbudowy

Nagroda główna: 20 000 zł

ODWOLANIA2JSON_HackNation2026.pdf — 840.59 KB
Materiały wyzwania: https://hacknation.pl/zadania

## MateuszSz — 09:42

Dodatkowo, jako że nasz proces oceny jest zautomatyzowany, chcielibyśmy podzielić się z Wami wstępnymi wymaganiami dotyczącymi opracowanych projektów:
język programowania dozwolony do użytku to Python 3.13+
dodatkowe zależności powinny być umieszczone w pliku requirements.txt i posiadać w miarę uproszczoną metodę instalacji (np. poprzez pip)
dozwolone jest użycie wyłącznie komponentów open source
program powinien być możliwy do uruchomienia lokalnie bez GPU
program powinien zawierać prostą metodę uruchomienia (np. komenda run z argumentami, plik .bat)
Mamy nadzieję że te wymogi nie będą ograniczać Waszej kreatywności, i będziemy trzymać za Was kciuki!

## Kontekst pytania uczestnika — 11:02

Uczestnik pytał, czy zgodne są trzy opcje: otwarte modele przez darmowe API, własny model wystawiony po API oraz otwarte modele przez płatne API. To opis pytania uczestnika, nie odrębne wymaganie.

## MateuszSz — 11:23

Wszystkie 3 są zgodne z naszymi ustaleniami

## MateuszSz — 11:26

True Positive - wartość występuje w JSONie i jest zgodna z oczekiwanym ground truth (w przypadku długich stringów takich jak nazwy firm, będzie brany pod uwagę procent zgodności, obecnie jest to 80%)
True Negative - wartości nie ma zarówno w JSONie jak i w ground truth
False Positive - wartość występuje tylko w JSON, lub wartość występuje w JSON i w ground truth, ale jest nieprawidłowa
False Negative - wartość nie występuje w JSON ale występuje w ground truth

## Dominik Olczak — 11:28

tylko jak LLMy płatne, to potrzebujemy Waszych kluczy do oceny

## Dominik Olczak — 12:47

Na prezentacji jest zła liczba, bo dzisiaj dorobiliśmy jeszcze kilkanaście większych przykładów. Dlatego wszystkich jest 60. ground_truth.yaml usunęliśmy, bo to de facto byly scalone pliki .json.
Zbiór testowy to syntetyczne dokumenty wygenerowane na podstawie prawdziwych caseów. Nie ma skanów bez warstawy testowej w przykładach.
JSON ściśle zgodny z formatem.
Jeżeli mamy dokument spoza puli (odwołanie, potwierdzenie przelewu, pełnomocnictwo) to na etapie określenia typu powinniśmy dostać odpowiedź, że nie udało się znaleźć typu (nie udało się dopasować). Nie zwracamy wtedy JSONa.
Mamy zwykłego laptopa, nie ma limitu czasu, ale nie instalujemy modelu lokalnie na sprzęcie - dlatego API.
Mamy dostęp do Internetu, endpoint musi być publicznie dostępny.

## MateuszSz — 13:13

Tak, natomiast teraz mamy już na Githubie słownik dla tych kodów (w folderze oczekiwane-json), żebyście mogli zobaczyć co ten kod 12 oznacza

## MateuszSz — 13:26

Pola "długi string" to: Nazwa firmy pełnomocnika, tytuł przelewu, Nazwa Odwołującego/Zamawiającego, tytuł zamówienia publicznego
Listy dopasowywane są po treści

## MateuszSz — 13:27 — ostatnia korekta w przekazanym materiale

Również poprawka co do zachowania w przypadku wykrycia obcego pliku (takiego który ma nie zostać zaklasyfikowany do żadnego z 3 typów) - powinien to być pusty JSON z nazwą oryginalnego pliku
