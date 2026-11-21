---
wersja: 0.3.0
aktualizacja: 2026-11-21
status: dokumentacja przygotowawcza
---

# Publikacja prywatna

Cel: organizacja `HackNation2026-dev`; nazwa repo odpowiada nazwie katalogu projektu. Publikacja jest autoryzowana przez użytkownika.

Po uzyskaniu działającego dostępu GitHub:

```bash
python3 scripts/publish_private.py
```

Skrypt sprawdza konto, organizację, prywatność i właściciela. Tworzy repo tylko przy odpowiedzi 404. Dopuszcza aktualizację fast-forward, gdy zdalny main jest przodkiem lokalnego HEAD. Przy rozbieżnej historii zatrzymuje się bez nadpisywania. Po wysłaniu sprawdza zgodność commitów i prywatność. Nie zapisuje tokenu ani klucza API w Git.

Pierwszy tag: v0.1.0. Sam lokalny origin nie potwierdza istnienia repo na GitHub. Status publikacji ustala wynik skryptu i odczyt zdalnego repo.

Stan 2026-11-21: organizację `HackNation2026-dev` utworzył użytkownik ręcznie, bo GitHub.com nie udostępnia API do zakładania organizacji. Konto `kacperpaczos` ma w niej rolę admin. Repo `https://github.com/HackNation2026-dev/odwolania2json` utworzył skrypt. Odczyt API przed wysłaniem materiałów potwierdził `private=true` i właściciela `HackNation2026-dev`. Pierwsza publikacja wysłała `main` = `9762c12` i tagi v0.1.0–v0.2.1, bez force push. Hash drzewa zdalnego był równy lokalnemu. Kolejne wydania wysyła ten sam skrypt i potwierdza ponownym odczytem.
