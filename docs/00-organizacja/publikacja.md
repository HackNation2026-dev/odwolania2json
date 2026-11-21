---
wersja: 0.1.1
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Publikacja prywatna

Cel: organizacja `HackNation2026-dev`; nazwa repo odpowiada nazwie katalogu projektu. Publikacja jest autoryzowana przez użytkownika.

Po uzyskaniu działającego dostępu GitHub:

```bash
python3 scripts/publish_private.py
```

Skrypt sprawdza konto, organizację, prywatność i właściciela. Tworzy repo tylko przy odpowiedzi 404. Zatrzymuje się przy innym zdalnym main i nie nadpisuje historii. Po wysłaniu sprawdza zgodność commitów i prywatność. Nie zapisuje tokenu ani klucza API w Git.

Pierwszy tag: v0.1.0. Sam lokalny origin nie potwierdza istnienia repo na GitHub. Status publikacji ustala wynik skryptu i odczyt zdalnego repo.

Aktualny cel: `https://github.com/HackNation2026-dev/odwolania2json`. Organizacja ani publikacja nie zostały potwierdzone. Ostatnia kontrola: CLI nie łączy się z api.github.com; brak zainstalowanej integracji GitHub oraz zapisanej sesji przeglądarki. Skrypt nie tworzy organizacji: musi ona istnieć i być dostępna dla zalogowanego konta.
