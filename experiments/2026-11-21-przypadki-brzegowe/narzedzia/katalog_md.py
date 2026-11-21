"""Generuje katalog Markdown i zestawienie kart z kanonicznych danych JSON."""
from wspolne import KATALOG, REPO, RUN, wczytaj_json

DOC = REPO/'docs/05-weryfikacja'
FRONT = '---\nwersja: 0.6.0\naktualizacja: 2026-11-21\nstatus: wynik eksperymentu heurystycznego — zweryfikowana próba pięciu kart\n---\n\n'
STATUSY=['dokladne','inny_zapis','inna_forma_gramatyczna','wyliczana','nieznaleziona','null_w_referencji']


def tabela(headers,rows):
    def cell(v): return str(v).replace('|',r'\|').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|']+['| '+' | '.join(cell(v) for v in row)+' |' for row in rows])+'\n\n'


def main():
    catalog=wczytaj_json(KATALOG); summary=wczytaj_json(RUN/'karty/podsumowanie.json')
    text=FRONT+'# Katalog kodów przypadków brzegowych\n\n'
    text+='Źródło definicji: [kanoniczny JSON](przypadki-brzegowe.json). Liczby dotyczą 180 pozytywnych PDF-ów, każdy liczony raz dla danego kodu. O/P/R = odwołanie/pełnomocnictwo/przelew. Zero oznacza brak wykrycia przez użyte heurystyki, a nie dowód nieobecności. Kody wymagające oceny obrazu nie są automatycznie rozstrzygane. Grupa `wykonanie` opisuje zachowanie silnika; jej zera w kartach nie są pomiarem odporności, bo narzędzie nie uruchamia produktu.\n\n'
    rows=[]
    for p in catalog['przypadki']:
        c=summary['kody'][p['kod']]
        data=f"{c['razem']} ("+'/'.join(str(c['per_klasa'].get(k,0)) for k in ['odwolanie','pelnomocnictwo','przelew'])+')'
        rows.append([p['kod'],p['grupa'],p['nazwa'],p['definicja'],', '.join(p['zrodla']),p['wykrywanie'],p['testowanie'],data])
    text+=tabela(['Kod','Grupa','Nazwa','Definicja','Źródła','Wykrywanie','Testowanie','W danych: razem (O/P/R)'],rows)
    text+='Źródła: '+ '; '.join(f"**{k}** — {v}" for k,v in catalog['zrodla'].items())+'.\n\n[Wyniki i ograniczenia kart](karty-dokumentow-2026-11-21.md).\n'
    (DOC/'katalog-kodow.md').write_text(text,encoding='utf-8')
    text=FRONT+'# Karty 180 dokumentów — 2026-11-21\n\n'
    text+='## Fakty z pomiaru\n\n'
    text+='Przetworzono niezależnie 180 PDF-ów (po 60 na klasę). [Karty i podsumowanie](../../experiments/2026-11-21-przypadki-brzegowe/wyniki/2026-11-21-v1/karty/podsumowanie.json), [schemat](../../experiments/2026-11-21-przypadki-brzegowe/format/karta.schema.json), [narzędzia](../../experiments/2026-11-21-przypadki-brzegowe/narzedzia/karty.py). Każda karta została zwalidowana schematem draft 2020-12.\n\n'
    text+='Nałożone aktualizacje referencji: '+', '.join(summary['referencje_z_aktualizacji'])+'. Pozostałe referencje pochodzą z migawki bazowej. Oryginały niezmienione. Po uruchomieniu inwentarza porównano zawartość `modele` we wszystkich 206 wcześniejszych plikach dokumentów: bez zmian.\n\n'
    d=summary['dopasowanie']; located=sum(d.get(k,0) for k in STATUSY[:3]); denom=located+d.get('nieznaleziona',0)
    text+=f"Zlokalizowano {located}/{denom} wartości wymagających lokalizacji ({100*located/denom:.2f}%). Mianownik pomija null i wartości wyliczane; to pokrycie znanych referencji, nie F1 ekstraktora. Wszystkich pól: {sum(d.values())}.\n\n"
    text+=tabela(['Dopasowanie','Liczba'],[(k,d.get(k,0)) for k in STATUSY])
    text+='### Kody per klasa\n\nZliczane są dokumenty, nie liczba wystąpień kodu. Kandydaty układu i braku etykiet są przybliżeniami. Pełne definicje i źródła: [katalog kodów](katalog-kodow.md).\n\n'
    text+=tabela(['Kod','Razem','Odwołanie','Pełnomocnictwo','Przelew'],[(k,v['razem'],*(v['per_klasa'].get(c,0) for c in ['odwolanie','pelnomocnictwo','przelew'])) for k,v in summary['kody'].items()])
    text+='### Rozkład dopasowania per pole\n\nIndeksy list zastąpiono `[]`; identyczne ścieżki różnych elementów agregowano.\n\n'
    text+=tabela(['Pole',*STATUSY],[(p,*(v.get(k,0) for k in STATUSY)) for p,v in sorted(summary['dopasowanie_per_pole'].items())])
    text+='### Najczęstsze braki\n\n'
    text+=tabela(['Pole','Nieznaleziona'],[(v['pole'],v['liczba']) for v in summary['najczestsze_braki']]) if summary['najczestsze_braki'] else 'Brak pól ze statusem `nieznaleziona`.\n\n'
    text+='### Grupowanie\n\nRamka na stronę obejmuje pierwsze wystąpienie każdego pola grupy (pierwsze w kolejności Popplera), a także najbliższą wykrytą etykietę roli. Kolizja: środek dowolnego zlokalizowanego wystąpienia pola innej grupy znajduje się w ramce. Puste obszary dają `spojna=false`. Podgrupy pełnomocnika i podpisujących są oddzielne; `mocodawca[i].data` należy do mocodawcy. Wysokość w liniach = wysokość ramki / mediana wysokości linii strony.\n\n'
    text+=tabela(['Klasa / typ grupy','Spójne / wszystkie','%','Kompletne','Bez obszaru','Przykłady niespójnych (id: grupa)'],[(k,f"{v['spojne']}/{v['wszystkie']}",v['odsetek_spojnych'],v['kompletne'],v['bez_obszaru'],'; '.join(x['id']+': '+x['grupa'] for x in v['przyklady_niespojnych'])) for k,v in summary['grupowanie'].items()])
    text+='## Interpretacja i ograniczenia\n\n'
    text+='Grupowanie można zbudować, ale jedna ramka na podmiot nie działa niezawodnie dla wszystkich dokumentów. UI powinno dopuszczać kilka obszarów i zaznaczenia pojedynczych pól. Spójność nie dowodzi prawidłowego przypisania semantycznego: ta sama miejscowość może występować w adresach różnych stron. Kontrola kolizji obejmuje tylko pola referencji, nie wszystkie obce dane obecne w PDF (np. partnera konsorcjum nieuwzględnionego w referencji). Brak kolizji w grupie przelewu ma ograniczoną wartość, bo to jedyna grupa w kontrakcie.\n\n'
    text+='Etykiety ról: wyłącznie role podmiotów, słownik i okno 8 linii o umownej wysokości 14 pt. Tytuł ODWOŁANIE, metadane zamówienia i nagłówek potwierdzenia przelewu nie są rolami. W przelewie osobno sprawdza się płatnika dla z_rachunku i odbiorcę dla na_rachunek. Po zawężeniu definicji przeliczono wszystkie karty w wersji dokumentacji 0.6.0; zmiana liczebności nie jest zmianą oryginałów. Etykiety pól: ta sama lub poprzednia linia Popplera. Wynik „brak” oznacza brak wykrycia, a nie stwierdzony brak etykiety. Liczba kolumn to kandydat 1/2 (co najmniej trzy przerwy >45 pt w wierszach o zbliżonym y), bez analizy linii graficznych; nie rozstrzyga, czy tabela ma widoczne krawędzie. `niewidoczna_tabela` oznacza kandydata z etykietą i wartością na tej samej wysokości, w różnych blokach.\n\n'
    text+='Normalizacja tekstów: Unicode NFKC, wielkość liter i odstępy. Identyfikatory porównuje się bez spacji/myślników i opcjonalnego PL; daty i kwoty według jawnych wariantów. Dopasowanie rozmyte tylko dla nazw i tytułów: >=90 dla tekstów >=40 znaków albo >=82 i zgodne początki słów dla kandydatów odmiany; cyfry muszą być identyczne. Próg nie został skalibrowany na odrębnym zbiorze, a `inna_forma_gramatyczna` jest hipotezą. Literalne wartości wyliczane są lokalizowane; liczbowe kody reguł nie są szukane jako przypadkowe cyfry.\n\n'
    text+='Dopasowanie literalne nie potwierdza roli: data czynności może pojawić się przy innym zdarzeniu, numer transakcji w tytule, miejscowość w cudzym adresie. Status pola opisuje najlepsze dopasowanie; lista wystąpień zawiera wszystkie trafienia ścisłe, a fuzzy tylko najlepsze trafienie na stronę, jeśli w całym dokumencie brak trafień ścisłych. Bbox obejmuje całe słowa Popplera (także końcową interpunkcję); wielowierszowa wartość ma prostokąt obejmujący także pustą przestrzeń. Nie weryfikuje się poprawności merytorycznej referencji.\n\n'
    text+='## Kontrola ręczna\n\n'
    text+='Próba warstwowa: obowiązkowe `p41_odwolanie`, `p42_odwolanie`; pozostałe losowano z posortowanych id przez `random.Random(20261121)` kolejno z klas pełnomocnictwo, przelew, pełnomocnictwo (bez powtórzeń). Porównano wszystkie niepuste wartości tych pięciu kart z tekstem `pdftotext -layout`; dla odwołań sprawdzono nagłówek i opis czynności (strony 1–2), a także powtórzenia w dalszej treści. Obejrzano render pierwszych stron i położenia ramek.\n\n'
    text+=tabela(['Karta','Co sprawdzono i wynik'],[
      ['p41_odwolanie','Lider Torvex, odrębny partner Hydromel, NIP/KRS/REGON, pełnomocnik, TED 2026/S 142-999327, tytuł w kilku liniach, data 4 sierpnia. Wykryto i poprawiono fałszywy brak REGON: numer 2) następnej pozycji listy blokował wzorzec. Dodano regresję. Ramka lidera nie obejmuje partnera, którego pola nie występują w referencji.'],
      ['p42_odwolanie','Obaj zamawiający, ich cztery dane identyfikacyjne, BZP, nazwa i mail pełnomocnika, data pisma na s.1 i czynności na s.2. Odróżniono konsorcjum innego wykonawcy (s.3) od odwołującego; zawężono kod konsorcjum do nagłówka roli. Pozostają kolizje z miejscowością Kraków obecną też w adresach.'],
      ['p34_pelnomocnictwo','Galdaris, NIP/KRS, Ignacy Sikorski, Marek Jabłoński i Norbert Rutkiewicz. Wszystkie wartości literalne poprawne. Zawężono bbox etykiety roli do jej słów zamiast całej linii; po poprawce obie grupy pełnomocników są spójne.'],
      ['p12_przelew','Data operacji 09-07-2026 zamiast daty pisma 12 lipca, kwota 200.00 PLN, dwa rachunki ze spacjami, tytuł w dwóch liniach i dwa wystąpienia numeru transakcji. Literalna lokalizacja numeru zaczyna się już w tytule.'],
      ['p18_pelnomocnictwo','Balttec, NIP/KRS, Dorota Zawadzki i Grzegorz Bąkiewicz. Dane mocodawcy i pełnomocnika są w tym samym akapicie; najbliższa etykieta może objąć inną grupę. To ograniczenie jednej ramki.'],
    ])
    text+='Poprawki po kontroli zastosowano ponownie do wszystkich 180 kart. Próba nie stanowi pełnego audytu semantycznego ani pomiaru trafności heurystyk na całym zbiorze.\n\n'
    text+='## Odtworzenie i weryfikacja\n\nZ katalogu głównego repo uruchom wskazanym Pythonem 3.13: `experiments/2026-11-21-przypadki-brzegowe/narzedzia/inwentarz.py`, następnie `narzedzia/karty.py` oraz `narzedzia/katalog_md.py` (dwie ostatnie ścieżki względem katalogu eksperymentu). Testy: `python -m pytest experiments/2026-11-21-przypadki-brzegowe/narzedzia/test_karty.py -q`. Dokumentacja: `python3 scripts/verify_docs.py`. Bez sieci i API. Weryfikacja 0.6.0: 74 testy pytest zakończone powodzeniem (w tym walidacja wszystkich 180 kart i regresje etykiet ról); `python3 scripts/verify_docs.py`: OK, 440 materiałów i 48 dokumentów. `git diff --check`: bez błędów. Historyczna kontrola ręczna pięciu kart dotyczyła lokalizacji referencji; nie jest ponownym audytem zmienionych etykiet ról.\n'
    (DOC/'karty-dokumentow-2026-11-21.md').write_text(text,encoding='utf-8')


if __name__=='__main__': main()
