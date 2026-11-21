---
wersja: 0.4.0
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

## Historia stanu

Stan zapisany do wersji 0.2.1 (przywrócony w 0.4.0, bez zmian treści):

> Aktualny cel: `https://github.com/HackNation2026-dev/odwolania2json`. Organizacja ani publikacja nie zostały potwierdzone. Ostatnia kontrola: CLI nie łączy się z api.github.com; brak zainstalowanej integracji GitHub oraz zapisanej sesji przeglądarki. Skrypt nie tworzy organizacji: musi ona istnieć i być dostępna dla zalogowanego konta.

## Zmiana widoczności (2026-11-21)

Użytkownik zmienił widoczność repo `HackNation2026-dev/odwolania2json` na **publiczną** około 14:02 UTC i potwierdził to w rozmowie. Wersję 0.4.0 wysłano już do repo publicznego. `scripts/publish_private.py` nadal wymaga `private=true`, więc przy repo publicznym zatrzyma się bez wysyłania. Kolejne wydania wysyła się zwykłym `git push` bez force; po wysłaniu trzeba sprawdzić zgodność SHA. Repo publiczne udostępnia kopie materiałów organizatorów, wyciąg Discord i wynik konsultacji Fable.
