# Odwołania2JSON — UZP

Prywatne repozytorium przygotowawcze dla HackNation 2026. Organizacja docelowa: `HackNation2026ORG`. Wersja dokumentacji: **0.1.0**.

## Stan

Przygotowano dokumentację i kopie materiałów źródłowych. Aplikacja konkursowa nie została jeszcze zaimplementowana. Status wysłania na GitHub sprawdzaj w repozytorium zdalnym; lokalny adres `origin` jest adresem docelowym, nie dowodem utworzenia repo.

## Zacznij tutaj

1. [Indeks dokumentacji](docs/README.md)
2. [Zadanie](docs/01-zadanie/README.md)
3. [Materiały i pochodzenie](docs/02-materialy/README.md)
4. [Wymagania i odbiór](docs/03-wymagania/README.md)
5. [Architektura i stos](docs/04-architektura/README.md)
6. [Weryfikacja](docs/05-weryfikacja/README.md)
7. [Prezentacja i zgłoszenie](docs/06-prezentacja/README.md)
8. [Decyzje i pytania](docs/07-decyzje/README.md)

## Kontrola dokumentacji

```bash
python3 scripts/verify_docs.py
```

Skrypt kontroluje odnośniki lokalne i sumy materiałów. Nie testuje nieistniejącej jeszcze aplikacji.

## Wersjonowanie

Zobacz [zasady wersjonowania](docs/00-organizacja/wersjonowanie.md) i [historię zmian](CHANGELOG.md). Oryginały organizatora są oddzielone od opracowań zespołu. Zachowuj ich nazwy i bajty.

## Dostęp i sekrety

Repo ma pozostać prywatne. Klucze API przekazuj jury osobno; aplikacja ma czytać je z konfiguracji środowiska. Dane referencyjne pozostają materiałem organizatora. Repo nie nadaje im nowej licencji.
