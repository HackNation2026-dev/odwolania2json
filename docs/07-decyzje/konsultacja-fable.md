---
wersja: 0.2.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Konsultacja Fable — zlecenie i status

Status: niewykonana. Brak opinii drugiego modelu. Próba uruchomienia Orca zakończyła się błędem „Timed out waiting for an Orca desktop window”; następnie status wskazał runtime not_running. Nazwy i identyfikatora modelu Fable nie potwierdzono. Nie zastąpiono go innym modelem.

## Zlecenie do przekazania Fable

Przeprowadź niezależną ocenę stosu dla dwóch osobnych monorepo: formularze (COI) i odwolania2json (UZP). Czytaj ich docs, oryginalne materiały oraz najnowsze komunikaty UZP z Discorda. Nie traktuj propozycji poprzedniego autora jako decyzji.

Preferencje zespołu: Rust, Python, TypeScript i Docker. Rust jest preferencją, nie warunkiem. Wybierz dojrzalsze rozwiązanie, jeżeli lepiej spełnia wymagania i skraca wykonanie.

UZP: Python 3.13+, requirements.txt i CLI. Otwarte komponenty i model możliwy do instalacji lokalnej. LLM po publicznym API; jury nie instaluje modelu na laptopie. Darmowe, płatne i własne API dozwolone, z pozostałymi ograniczeniami regionu i licencji. JSON ścisły, listy po treści, wskazane długie teksty z progiem 80%. GUI opcjonalne. Sprawdź ryzyko jakiegokolwiek komponentu Rust.

COI: REST, PDF/DOC/DOCX/ODS/XLSX/JPG/JPEG/PNG -> konfiguracja COI. Działanie bez zależności od zewnętrznych API, MCP i SaaS. Open source bez wykluczonego copyleft; brak wymaganej licencji komercyjnej. Java 21+/Python 3.14+ są preferowane. Docker, pliki użytkownika tylko tymczasowo. Uwzględnij JSON Schema, reguły i przykłady lokalne.

Odpowiedz po polsku w tej samej strukturze dla obu zadań: wariant zalecany, alternatywa, udział Rusta, dojrzałe biblioteki, licencje i zależności, budowanie Docker, ryzyka formatu DOC/OCR/JSON, model i sprzęt, plan pełnej ścieżki. Oddziel wymaganie organizatora od rekomendacji.

Porównaj React/TypeScript i egui tylko w zakresie rzeczywistych potrzeb użytkownika. Podaj źródła dokumentacji technicznej i ograniczenia sprawdzenia. Nie rekomenduj narzędzia wyłącznie na podstawie nazwy lub samej licencji wrappera.

Wynik: tabela decyzji i uzasadnienie. Podaj rzeczywistą nazwę użytego modelu. Nie twórz repo, nie publikuj, nie zmieniaj źródeł i nie odczytuj sekretów.
