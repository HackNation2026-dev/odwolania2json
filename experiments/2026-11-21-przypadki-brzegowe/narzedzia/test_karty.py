"""Regresja formatów, przypadków negatywnych i mutacji pojedynczej cyfry."""
import copy
import pytest
from jsonschema import Draft202012Validator, ValidationError
from karty import dopasuj, normalizuj, splaszcz, buduj_grupy, odczytaj, lokalizuj
from wspolne import FORMAT, REPO, KODY, TAKSONOMIA, wczytaj_json

@pytest.mark.parametrize('pole,wartosc,tekst,status', [
 ('x.nip','1234567890','NIP: PL 123-456-78-90','inny_zapis'),
 ('x.krs','0000123456','KRS 0000123456','dokladne'),
 ('x.regon','123456789','REGON: 123 456 789','inny_zapis'),
 ('x.pesel','12345678901','PESEL 12345678901','dokladne'),
 ('x.na_rachunek','12345678901234567890123456','PL12 3456 7890 1234 5678 9012 3456','inny_zapis'),
 ('x.data','2026-11-21','21 listopada 2026 r.','inny_zapis'),
 ('x.data','2026-01-02','2.1.2026','inny_zapis'),
 ('x.data','2026-11-21','2026-11-21','dokladne'),
 ('x.kwota',200.0,'Kwota: 200,00 zł','inny_zapis'),
 ('x.kwota',200.0,'200.00 PLN','inny_zapis'),
 ('x.numer_bzp','2026/BZP00999778','2026/BZP 00999778','inny_zapis'),
 ('x.numer_ted','999327-2026','2026/S 147-999327','inny_zapis'),
 ('x.nazwa','Firma ABC','FIRMA   ABC','dokladne'),
 ('x.imie_nazwisko','Piotr Zalewski','Piotra Zalewskiego','inna_forma_gramatyczna'),
 ('x.mail','abc@firma.pl','kontakt: abc@firma.pl','dokladne'),
 ('x.typ','osoba_prawna','spółka akcyjna','wyliczana'),
 ('x.czynnosc_powod_id',1,'1. pierwsza strona','wyliczana'),
 ('x.czynnosc_opis','Decyzja o odrzuceniu oferty','Decyzja o odrzuceniu oferty','dokladne'),
 ('x.nip',None,'NIP 1234567890','null_w_referencji'),
])
def test_formaty(pole,wartosc,tekst,status):
    assert dopasuj(pole,wartosc,tekst)[0]==status

@pytest.mark.parametrize('pole,wartosc,tekst', [
 ('x.nip','1234567890','1234567891'),
 ('x.nip','1234567890','01234567890'),
 ('x.nip','1234567890','12345678901'),
 ('x.krs','0000123456','0000123457'),
 ('x.pesel','12345678901','12345678902'),
 ('x.z_rachunku','12345678901234567890123456','12345678901234567890123457'),
 ('x.data','2026-11-21','22 listopada 2026 r.'),
 ('x.data','2026-11-21','21 grudnia 2026'),
 ('x.data','2026-11-21','21.11.2025'),
 ('x.kwota',200.0,'1200,00'),
 ('x.kwota',200.0,'200,01'),
 ('x.numer_ted','999327-2026','2026/S 147-999328'),
 ('x.numer_bzp','2026/BZP00999778','2026/BZP00999779'),
 ('x.mail','abc@firma.pl','xabc@firma.pl'),
 ('x.numer_transakcji','ABC123456789','ABC123456788'),
 ('x.imie_nazwisko','Piotr Zalewski','Piotr Kowalski'),
 ('x.tytul','Budowa drogi numer 123 wraz z instalacją oświetlenia','Budowa drogi numer 124 wraz z instalacją oświetlenia'),
])
def test_negatywne(pole,wartosc,tekst):
    assert dopasuj(pole,wartosc,tekst)[0]=='nieznaleziona'

@pytest.mark.parametrize('idx',range(10))
def test_mutacja_kazdej_cyfry_nip(idx):
    value='1234567890'; changed=value[:idx]+str((int(value[idx])+1)%10)+value[idx+1:]
    assert dopasuj('nip',value,changed)[0]=='nieznaleziona'

def test_normalizacja():
    assert normalizuj('  SPÓŁKA\n  z\u00a0o.o. ')== 'spółka z o.o.'

def test_sciezki_i_grupy():
    assert dict(splaszcz({'mocodawca':[{'data':{'nip':'123'},'podpisujacy':[{'imie_nazwisko':None}]}]}))=={'mocodawca[0].data.nip':'123','mocodawca[0].podpisujacy[0].imie_nazwisko':None}

def test_taksonomia_i_schemat():
    assert len(KODY)==len(set(KODY))==len(TAKSONOMIA)
    schema=wczytaj_json(FORMAT/'karta.schema.json')
    assert schema['properties']['kody']['items']['properties']['kod']['enum']==KODY
    Draft202012Validator.check_schema(schema)

def test_wiele_linii_i_wystapien():
    pages=odczytaj(REPO/'docs/02-materialy/organizator-uzp/dane/przyklad_41/odwolanie.pdf')
    field=lokalizuj('Odwolujacy[0].nazwa','Torvex Budownictwo sp. z o.o.',pages)
    assert field['dopasowanie']=='dokladne'
    assert len(field['wystapienia'])>=2
    assert all(0<=o['bbox'][0]<o['bbox'][2] for o in field['wystapienia'])

def test_kolizja_grup():
    page={'nr':1,'linie':[{'bbox':[0,0,100,10]}]}
    def f(b):return {'dopasowanie':'dokladne','wystapienia':[{'strona':1,'bbox':b,'etykieta_roli':{'tekst':None}}]}
    fields={'A.nazwa':f([0,0,100,10]),'A.nip':f([0,30,100,40]),'B.nazwa':f([10,15,90,25])}
    groups=buduj_grupy(fields,[page])
    assert not groups[0]['spojna']
    assert groups[0]['obszary'][0]['kolidujace_pola']==['B.nazwa']

def test_nieznany_kod_odrzucony():
    from wspolne import RUN
    c=wczytaj_json(RUN/'karty/p01_odwolanie.json'); c=copy.deepcopy(c)
    c['kody'].append({'kod':'niekanoniczny','pole':None,'dowod':'test'})
    with pytest.raises(ValidationError):
        Draft202012Validator(wczytaj_json(FORMAT/'karta.schema.json')).validate(c)


def test_regon_przed_numerowana_lista():
    assert dopasuj('regon','999473016','REGON: 999473016 2) Partner Konsorcjum')[0]=='dokladne'


def test_mutacja_dnia_dla_kazdego_miesiaca():
    from karty import MIESIACE
    for m,nazwa in enumerate(MIESIACE,1):
        assert dopasuj('data',f'2026-{m:02d}-21',f'22 {nazwa} 2026')[0]=='nieznaleziona'
        assert dopasuj('data',f'2026-{m:02d}-21',f'21 {nazwa} 2026')[0]=='inny_zapis'


def test_wszystkie_karty_i_referencje():
    """Integracja: kompletność ścieżek, poprawki referencji, geometria i agregacja."""
    from karty import podsumuj
    from wspolne import RUN
    cards=[]
    schema=Draft202012Validator(wczytaj_json(FORMAT/'karta.schema.json'))
    manifest=wczytaj_json(RUN/'manifest.json')
    positive=[d for d in manifest['dokumenty'] if d['zrodlo']=='pozytywny']
    assert len(positive)==180
    for d in positive:
        c=wczytaj_json(RUN/'karty'/f"{d['id']}.json"); schema.validate(c); cards.append(c)
        expected=dict(splaszcz(wczytaj_json(REPO/c['referencja'])))
        assert {p:f['wartosc'] for p,f in c['pola'].items()}==expected
        metadata=wczytaj_json(RUN/d['plik_wynikow'])
        for f in c['pola'].values():
            for o in f['wystapienia']:
                page=metadata['strony'][o['strona']-1]; x0,y0,x1,y1=o['bbox']
                assert 0<=x0<x1<=page['szerokosc_pt']+1
                assert 0<=y0<y1<=page['wysokosc_pt']+1
        assert {p for g in c['grupy'] for p in g['pola']}==set(c['pola'])
        assert sum(len(g['pola']) for g in c['grupy'])==len(c['pola'])
    assert podsumuj(cards)==wczytaj_json(RUN/'karty/podsumowanie.json')
    assert len([c for c in cards if 'organizator-uzp-aktualizacje' in c['referencja']])==5


@pytest.mark.parametrize('typ,tekst,oczekiwana', [
    ('OdwolanieKIO', 'ODWOŁANIE', False),
    ('ZamowieniePubliczne', 'Postępowanie o udzielenie zamówienia', False),
    ('przelew_bankowy', 'Potwierdzenie przelewu', False),
    ('Odwolujacy', 'Odwołujący: Firma ABC', True),
    ('Zamawiajacy', 'Zamawiający: Urząd', True),
    ('platnik', 'Rachunek nadawcy', True),
    ('odbiorca', 'Rachunek odbiorcy', True),
    ('platnik', 'Rachunek odbiorcy', False),
    ('odbiorca', 'Rachunek nadawcy', False),
])
def test_etykiety_dotycza_rol_podmiotow(typ, tekst, oczekiwana):
    from karty import etykieta_roli
    page = {'nr': 1, 'linie': [{'tekst': tekst, 'bbox': [0, 0, 200, 10]}],
            'slowa': [{'tekst': tekst, 'linia': 0, 'bbox': [0, 0, 200, 10]}]}
    assert bool(etykieta_roli(typ, page, [0, 14, 100, 24])['tekst']) == oczekiwana


@pytest.mark.parametrize('typ,etykieta,kod', [
    ('OdwolanieKIO', None, None),
    ('ZamowieniePubliczne', None, None),
    ('przelew_bankowy', None, None),
    ('OdwolanieKIO', {'tekst': 'ODWOŁANIE', 'polozenie': 'po'}, None),
    ('Odwolujacy[0]', None, 'brak_etykiety_roli'),
    ('Zamawiajacy[0]', {'tekst': 'Zamawiający', 'polozenie': 'po'}, 'etykieta_po_danych'),
])
def test_kody_etykiet_pomijaja_metadane(typ, etykieta, kod):
    from karty import kody_karty
    groups = [{'id': typ, 'obszary': [{}], 'etykieta_roli': etykieta}]
    codes = kody_karty({}, groups, [], [], {}, {'strony': []})
    assert [c['kod'] for c in codes] == ([kod] if kod else [])


@pytest.mark.parametrize('pole,tekst,kod', [
    ('przelew_bankowy.z_rachunku', 'Rachunek nadawcy', None),
    ('przelew_bankowy.na_rachunek', 'Rachunek odbiorcy', None),
    ('przelew_bankowy.z_rachunku', 'Potwierdzenie przelewu', 'brak_etykiety_roli'),
    ('przelew_bankowy.na_rachunek', 'Potwierdzenie przelewu', 'brak_etykiety_roli'),
])
def test_kody_rol_stron_przelewu(pole, tekst, kod):
    from karty import etykieta_roli, rola_pola, kody_karty
    page = {'nr': 1, 'linie': [{'tekst': tekst, 'bbox': [0, 0, 200, 10]}],
            'slowa': [{'tekst': tekst, 'linia': 0, 'bbox': [0, 0, 200, 10]}]}
    role = etykieta_roli(rola_pola(pole), page, [0, 14, 100, 24])
    fields = {pole: {'dopasowanie': 'dokladne', 'wartosc': '123', 'wystapienia': [
        {'etykieta_roli': role, 'etykieta_pola': 'rachunek', 'strona': 1, 'liczba_linii': 1}]}}
    codes = kody_karty(fields, [], [], [], {}, {'strony': []})
    assert [c['kod'] for c in codes] == ([kod] if kod else [])
