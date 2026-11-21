"""Lokalizacja znanych referencji; heurystyki badawcze, nie ekstraktor produkcyjny.

Każda karta korzysta wyłącznie z jednego PDF i jego referencji. Współrzędne
Popplera: punkty PDF, początek w lewym górnym rogu, strony od 1.
"""
from __future__ import annotations

import re
import statistics
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from rapidfuzz import fuzz
from jsonschema import Draft202012Validator
from wspolne import REPO, RUN, FORMAT, KODY, uruchom, wczytaj_json, zapisz_json

MIESIACE = 'stycznia lutego marca kwietnia maja czerwca lipca sierpnia września października listopada grudnia'.split()
WYLICZANE = {'czynnosc_opis', 'przez-pelnomocnika', 'prowadzacy_postepowanie', 'typ', 'czynnosc_powod_id'}
ROLE = {
 'Odwolujacy': r'odwołując\w*|wykonawc\w*|skarżąc\w*',
 'Zamawiajacy': r'zamawiając\w*',
 'pelnomocnik': r'pełnomocni\w*|reprezentowan\w*|w imieniu',
 'pelnomocnicy': r'pełnomocni\w*|upoważnia\w*|udziela\w*',
 'mocodawca': r'mocodawc\w*|udziela\w*|reprezentowan\w*',
 'podpisujacy': r'podpis\w*|prezes\w*|człon\w*|reprezentowan\w*',
 'platnik': r'płatni\w*|nadawc\w*|zleceniodawc\w*|z rachunku|rachunek nadawcy',
 'odbiorca': r'odbiorc\w*|beneficjent\w*|na rachunek|rachunek odbiorcy',
}
ETYKIETY = {'nip':r'\bNIP\b', 'regon':r'\bREGON\b', 'krs':r'\bKRS\b', 'pesel':r'\bPESEL\b',
 'data':r'\bdata\b', 'data_operacji':r'data operacji|data realizacji', 'kwota':r'kwota',
 'na_rachunek':r'rachunek odbiorcy|na rachunek', 'z_rachunku':r'rachunek nadawcy|z rachunku',
 'tytul':r'tytuł|przedmiot', 'numer_postepowania':r'numer|znak', 'numer_bzp':r'BZP',
 'numer_ted':r'TED|ogłoszeni\w*', 'mail':r'e-mail|email|poczta', 'numer_transakcji':r'numer transakcji|identyfikator'}


def normalizuj(t):
    """Ujednolica wyłącznie Unicode, odstępy i wielkość liter."""
    import unicodedata
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', str(t))).strip().casefold()


def wzorzec(pole, wartosc):
    """Ścisłe formaty z granicami cyfr; żadnego fuzzy dla identyfikatorów."""
    k = pole.rsplit('.', 1)[-1]
    s = str(wartosc)
    if k in {'nip','regon','krs','pesel','na_rachunek','z_rachunku'}:
        cyfry = re.sub(r'\D', '', s.removeprefix('PL'))
        return r'(?<!\w)(?:PL\s*)?' + r'[\s-]*'.join(cyfry) + r'(?!\w)'
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        y,m,d = s.split('-')
        return rf'(?<!\d)(?:{s}|0?{int(d)}[./-]0?{int(m)}[./-]{y}|0?{int(d)}\s+{MIESIACE[int(m)-1]}\s+{y})(?!\d)(?:\s*r\.)?'
    if k == 'kwota':
        a,b = f'{Decimal(s):.2f}'.split('.')
        return rf'(?<![\d.,]){a}[,.]{b}(?!\d)(?:\s*(?:zł|PLN))?'
    if k == 'numer_bzp':
        return r'(?<!\w)' + r'\s*'.join(re.escape(x) for x in s) + r'(?!\w)'
    if k == 'numer_ted' and re.fullmatch(r'\d{6}-\d{4}', s):
        n,y = s.split('-')
        return rf'(?<!\d)(?:{n}-{y}|{y}\s*/\s*S\s*\d{{3}}\s*-\s*{n})(?!\d)'
    return None


def dopasuj(pole, wartosc, tekst, rozmyte=True):
    """Zwraca status i zakres znaków (bez arbitralnego 80% dla krótkich nazw).

    Fuzzy: >=90 dla tekstów >=40 znaków; >=82 dla nazw osób/firm >=12.
    Drugi próg wymaga zgodnych początków wszystkich wyrazów znaczących.
    To kandydat odmiany gramatycznej, nie dowód językoznawczy. Cyfry muszą
    pozostać identyczne. Progi ograniczają przypadkowe trafienia krótkich słów.
    """
    if wartosc is None:
        return 'null_w_referencji', None
    t, v = normalizuj(tekst), normalizuj(wartosc)
    k = pole.rsplit('.',1)[-1]
    pat = wzorzec(pole, wartosc)
    if pat:
        m = re.search(pat, t, re.I)
        if m:
            return ('dokladne' if m.group() == v else 'inny_zapis'), m.span()
        return 'nieznaleziona', None
    # Kody liczbowe nie są lokalizowane jako przypadkowa cyfra w treści.
    if k in WYLICZANE and not isinstance(wartosc, str):
        return 'wyliczana', None
    m = re.search(r'(?<!\w)' + re.escape(v) + r'(?!\w)', t)
    if m:
        return 'dokladne', m.span()
    if k in WYLICZANE:
        return 'wyliczana', None
    if rozmyte and len(v) >= 12 and k in {'nazwa','imie_nazwisko','tytul'}:
        # Okna wyrazowe nie mogą pochłaniać dowolnie długiego kontekstu.
        tokens = list(re.finditer(r'\S+', t)); n = len(v.split()); best = None
        for i in range(len(tokens)):
            for size in range(max(1,n-1),n+3):
                if i+size > len(tokens):
                    continue
                a,b = tokens[i].start(),tokens[i+size-1].end(); sub=t[a:b]
                if re.findall(r'\d+',sub) != re.findall(r'\d+',v):
                    continue
                score=fuzz.ratio(v,sub)
                va=re.findall(r'\w{4,}',v); sa=re.findall(r'\w{4,}',sub)
                odmiana = len(va)==len(sa) and all(x[:4]==y[:4] for x,y in zip(va,sa))
                if (len(v)>=40 and score>=90) or (odmiana and score>=82):
                    if best is None or score>best[0]:
                        best=(score,a,b,odmiana)
        if best:
            return ('inna_forma_gramatyczna' if best[3] else 'inny_zapis'), best[1:3]
    return 'nieznaleziona', None


def splaszcz(obj, prefix=''):
    if isinstance(obj,dict):
        for k,v in obj.items():
            yield from splaszcz(v, f'{prefix}.{k}' if prefix else k)
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            yield from splaszcz(v,f'{prefix}[{i}]')
    else:
        yield prefix,obj


def grupa(pole):
    g=pole.rsplit('.',1)[0]
    return g[:-5] if g.endswith('.data') else g


def typ_grupy(g):
    return re.sub(r'\[\d+\]','[]',g)


def rola_pola(pole):
    """Role podmiotów; metadane i tytuły dokumentu nie są rolami.

    Kontrakt przelewu nie ma osobnych grup stron płatności, więc rolę
    wiążemy wyłącznie z odpowiednim rachunkiem, a nie całym przelewem.
    """
    if pole == 'przelew_bankowy.z_rachunku':
        return 'platnik'
    if pole == 'przelew_bankowy.na_rachunek':
        return 'odbiorca'
    return re.sub(r'\[\d+\]', '', grupa(pole)).rsplit('.', 1)[-1]


def suma_bbox(boxes):
    return [round(f(b[i] for b in boxes),3) for i,f in enumerate((min,min,max,max))]


def odczytaj(pdf):
    xml=uruchom(['pdftotext','-bbox-layout',str(pdf),'-'])
    root=ET.fromstring(xml); strony=[]
    for nr,page in enumerate(root.findall('.//{*}page'),1):
        words=[]; lines=[]
        for bi,block in enumerate(page.findall('.//{*}block')):
            for line in block.findall('.//{*}line'):
                li=len(lines); row=[]
                for w in line.findall('{*}word'):
                    row.append({'tekst':w.text or '', 'bbox':[float(w.attrib[x]) for x in ('xMin','yMin','xMax','yMax')], 'linia':li,'blok':bi})
                if row:
                    lines.append({'tekst':' '.join(w['tekst'] for w in row),'bbox':suma_bbox([w['bbox'] for w in row]),'blok':bi})
                    words.extend(row)
        # Zachowujemy kolejność bloków Popplera; normalizowane słowa mapujemy na znaki.
        text=''; spans=[]
        for w in words:
            if text: text+=' '
            start=len(text); text+=normalizuj(w['tekst']); spans.append((start,len(text),w))
        strony.append({'nr':nr,'szerokosc':float(page.attrib['width']),'wysokosc':float(page.attrib['height']), 'slowa':words,'linie':lines,'tekst':text,'zakresy':spans})
    return strony


def etykieta_roli(g, page, box):
    typ=re.sub(r'\[\d+\]','',g).rsplit('.',1)[-1]
    pat=ROLE.get(typ)
    kand=[]
    if pat:
        for li,line in enumerate(page['linie']):
            m=re.search(pat,line['tekst'],re.I)
            if m:
                # Ograniczamy etykietę do najbliższych 8 typowych linii.
                dist=abs(line['bbox'][1]-box[1])/14
                if dist<=8:
                    ws=[w['bbox'] for w in page['slowa'] if w['linia']==li and re.search(pat,w['tekst'],re.I)]
                    if not ws: ws=[line['bbox']]
                    kand.append((dist,line,m.group(),suma_bbox(ws)))
    if not kand:
        return {'tekst':None,'polozenie':'brak','odleglosc_linii':None}
    dist,line,t,b=min(kand,key=lambda x:x[0])
    return {'tekst':t,'polozenie':'przed' if b[1]<=box[1] else 'po','odleglosc_linii':round(dist,2),'strona':page['nr'],'bbox':b}


def lokalizuj(pole, value, pages):
    occurrences=[]; statuses=[]
    for page in pages:
        pos=0
        while pos<len(page['tekst']):
            status,span=dopasuj(pole,value,page['tekst'][pos:],rozmyte=False)
            if span is None: break
            a,b=span; a+=pos; b+=pos
            words=[w for x,y,w in page['zakresy'] if x<b and y>a]
            if words:
                box=suma_bbox([w['bbox'] for w in words]); line=words[0]['linia']
                nearby=' '.join(l['tekst'] for j,l in enumerate(page['linie']) if j in {line,line-1})
                label=re.search(ETYKIETY.get(pole.rsplit('.',1)[-1],r'(?!)'),nearby,re.I)
                occurrences.append({'strona':page['nr'],'bbox':box,'tekst_w_dokumencie':' '.join(w['tekst'] for w in words), 'etykieta_pola':label.group() if label else None,'etykieta_roli':etykieta_roli(rola_pola(pole),page,box),'liczba_linii':len({w['linia'] for w in words})})
                statuses.append(status)
            pos=b
    if not occurrences and value is not None and pole.rsplit('.',1)[-1] not in WYLICZANE:
        for page in pages:
            status,span=dopasuj(pole,value,page['tekst'])
            if span is not None:
                a,b=span; ws=[w for x,y,w in page['zakresy'] if x<b and y>a]; box=suma_bbox([w['bbox'] for w in ws])
                occurrences.append({'strona':page['nr'],'bbox':box,'tekst_w_dokumencie':' '.join(w['tekst'] for w in ws),'etykieta_pola':None,'etykieta_roli':etykieta_roli(rola_pola(pole),page,box),'liczba_linii':len({w['linia'] for w in ws})}); statuses.append(status)
    status=min(statuses,key=lambda x:['dokladne','inny_zapis','inna_forma_gramatyczna'].index(x)) if statuses else ('null_w_referencji' if value is None else 'wyliczana' if pole.rsplit('.',1)[-1] in WYLICZANE else 'nieznaleziona')
    return {'wartosc':value,'dopasowanie':status,'wystapienia':occurrences}


def wewnatrz(a,b):
    """Czy środki wystąpień wpadają w ramkę (także częściowo zasłonięte wartości)."""
    return a[0] <= (b[0]+b[2])/2 <= a[2] and a[1] <= (b[1]+b[3])/2 <= a[3]


def buduj_grupy(fields,pages):
    groups=[]
    for g in sorted({grupa(p) for p in fields}):
        own=[p for p in fields if grupa(p)==g]; first=[(p,fields[p]['wystapienia'][0]) for p in own if fields[p]['wystapienia']]
        areas=[]; labels=[]
        for page in pages:
            found=[(p,o) for p,o in first if o['strona']==page['nr']]
            if not found: continue
            roles=[o['etykieta_roli'] for p,o in found if o['etykieta_roli']['tekst']]
            boxes=[o['bbox'] for p,o in found]
            # Jedna najbliższa etykieta roli na stronę.
            label=min(roles,key=lambda x:x['odleglosc_linii']) if roles else None
            if label: boxes.append(label['bbox']); labels.append(label)
            box=suma_bbox(boxes)
            collisions=sorted({p for p,f in fields.items() if grupa(p)!=g for o in f['wystapienia'] if o['strona']==page['nr'] and wewnatrz(box,o['bbox'])})
            heights=[l['bbox'][3]-l['bbox'][1] for l in page['linie']]
            areas.append({'strona':page['nr'],'bbox':box,'spojna':not collisions,'kolidujace_pola':collisions,'wysokosc_linii':round((box[3]-box[1])/(statistics.median(heights) if heights else 14),2)})
        groups.append({'id':g,'typ':typ_grupy(g),'pola':own,'etykieta_roli':labels[0] if labels else None,'obszary':areas,'spojna':bool(areas) and all(a['spojna'] for a in areas),'pola_zlokalizowane':len(first),'pola_do_lokalizacji':sum(fields[p]['dopasowanie'] not in {'wyliczana','null_w_referencji'} for p in own)})
    return groups


def uklad(page,fields):
    rows=defaultdict(list)
    for w in page['slowa']: rows[round(w['bbox'][1]/3)*3].append(w)
    gaps=[]; split=[]
    for y,ws in rows.items():
        ws.sort(key=lambda w:w['bbox'][0])
        for a,b in zip(ws,ws[1:]):
            if b['bbox'][0]-a['bbox'][2]>45:
                gaps.append({'y':y,'odstep_pt':round(b['bbox'][0]-a['bbox'][2],2),'rozne_bloki':a['blok']!=b['blok']})
    for p,f in fields.items():
        for o in f['wystapienia']:
            if o['strona']!=page['nr']: continue
            pat=ETYKIETY.get(p.rsplit('.',1)[-1])
            if not pat: continue
            vs=[w for w in page['slowa'] if wewnatrz(o['bbox'],w['bbox'])]
            for l in page['linie']:
                if abs(l['bbox'][1]-o['bbox'][1])<4 and re.search(pat,l['tekst'],re.I) and vs and l['blok']!=vs[0]['blok']:
                    split.append(p)
    return {'strona':page['nr'],'przyblizenie':True,'liczba_kolumn':2 if len(gaps)>=3 else 1,'linie_z_odstepami':gaps,'etykieta_i_wartosc_w_roznych_blokach':sorted(set(split))}


def kody_karty(fields,groups,layouts,pages,ref,meta):
    codes=[]
    def add(k,p,d):
        if k not in KODY: raise ValueError(f'Nieznany kod: {k}')
        codes.append({'kod':k,'pole':p,'dowod':d})
    def kod_roli(pole, role):
        if not role or not role['tekst']:
            add('brak_etykiety_roli',pole,'Nie wykryto lokalnej etykiety roli podmiotu (okno 8 linii)')
        elif role['polozenie']=='po':
            add('etykieta_po_danych',pole,role['tekst'])
        if role and role['tekst'] and re.search(r'wykonawc|skarżąc|reprezentowan|udziela|upoważnia|w imieniu',role['tekst'],re.I):
            add('etykieta_synonim',pole,role['tekst'])
    mapping={'wyliczana':'wartosc_wyliczana','inny_zapis':'inny_zapis_wartosci','inna_forma_gramatyczna':'inna_forma_gramatyczna','nieznaleziona':'brak_informacji_wprost'}
    for p,f in fields.items():
        if f['dopasowanie'] in mapping: add(mapping[f['dopasowanie']],p,f['dopasowanie']+'; wynik heurystyki, nie potwierdzenie braku w PDF')
        occ=f['wystapienia']
        if len(occ)>1: add('wiele_wystapien',p,f'{len(occ)} wystąpień')
        if any(o['liczba_linii']>1 for o in occ): add('wartosc_w_kilku_liniach',p,'BBox obejmuje kilka linii Popplera')
        if any(o['strona']>3 for o in occ): add('dane_dalej_niz_3_strona',p,'Wystąpienie na stronie >3')
        if occ and not occ[0]['etykieta_pola']: add('brak_etykiety_przy_wartosci',p,'Nie wykryto etykiety słownikowej w tej ani poprzedniej linii')
        if occ and rola_pola(p) in {'platnik', 'odbiorca'}:
            kod_roli(p, occ[0]['etykieta_roli'])
        if p.endswith('.pesel') and occ: add('pesel_obecny',p,'Zlokalizowany PESEL')
        if p.endswith('.typ') and f['wartosc']=='osoba_fizyczna': add('mocodawca_osoba_fizyczna',p,'Wariant w referencji')
        if p.endswith('.czynnosc_powod_id') and f['wartosc']==12: add('powod_12',p,'Kod w referencji')
        if p.endswith('.przez-pelnomocnika') and f['wartosc']==0: add('brak_pelnomocnika',p,'Wariant w referencji')
    for g in groups:
        if not g['obszary']: continue
        typ=re.sub(r'\[\d+\]','',g['id']).rsplit('.',1)[-1]
        if typ in ROLE:
            kod_roli(g['id'], g['etykieta_roli'])
    for l in layouts:
        if l['liczba_kolumn']>1: add('uklad_wielokolumnowy',None,f"Kandydat: strona {l['strona']}, duże odstępy")
        if l['etykieta_i_wartosc_w_roznych_blokach']: add('niewidoczna_tabela',None,f"Kandydat: strona {l['strona']}; etykieta i wartość w różnych blokach; brak analizy krawędzi")
    text=' '.join(p['tekst'] for p in pages)
    if ref.get('Odwolujacy') and re.search(r'odwołujący:\s*konsorcjum',text,re.I): add('konsorcjum',None,'Odwołujący: Konsorcjum w nagłówku dokumentu; referencja zawiera lidera')
    if len(ref.get('Zamawiajacy',[]))>1: add('wielu_zamawiajacych',None,'Więcej niż jeden element referencji')
    if len(ref.get('mocodawca',[]))>1: add('wielu_mocodawcow',None,'Więcej niż jeden element referencji')
    if 'ZamowieniePubliczne' in ref and not any(ref['ZamowieniePubliczne'].get(x) for x in ('numer_bzp','numer_ted')): add('brak_bzp_i_ted',None,'Oba numery null')
    if ref.get('przelew_bankowy',{}).get('kwota',0)>=1000 and re.search(r'wpis',text): add('przelew_wpis',None,'Kwota >=1000 i wzmianka o wpisie')
    for p in meta['strony']:
        for typ,k in [('skan','skan'),('skan_z_ocr','skan_z_ocr'),('mieszana','strona_mieszana'),('pusta','pusta_strona')]:
            if p['typ_auto']==typ: add(k,None,f"Inwentarz: strona {p['nr']}")
        if p['obrot_pdf']: add('obrot_flaga_pdf',None,f"/Rotate {p['obrot_pdf']}")
        if abs(p['szerokosc_pt']-595)>50 or abs(p['wysokosc_pt']-842)>50: add('nietypowy_rozmiar_strony',None,f"Strona {p['nr']}: {p['szerokosc_pt']} × {p['wysokosc_pt']} pt")
    return codes


def karta(d):
    pdf=REPO/d['plik_zrodlowy']; base=pdf.with_name(d['klasa_oczekiwana']+'.json')
    update=REPO/'docs/02-materialy/organizator-uzp-aktualizacje/main-7590db8/dane'/pdf.parent.name/base.name
    source=update if update.exists() else base; ref=wczytaj_json(source); pages=odczytaj(pdf)
    fields={p:lokalizuj(p,v,pages) for p,v in splaszcz(ref)}
    groups=buduj_grupy(fields,pages); layouts=[uklad(p,fields) for p in pages]
    meta=wczytaj_json(RUN/d['plik_wynikow'])
    return {'format':'uzp-karta-dokumentu','wersja':1,'id':d['id'],'klasa':d['klasa_oczekiwana'],'pdf':d['plik_zrodlowy'],'referencja':source.relative_to(REPO).as_posix(),'metoda':'Heurystyka referencja → pdftotext -bbox-layout; każdy PDF niezależnie','pola':fields,'grupy':groups,'uklad':layouts,'kody':kody_karty(fields,groups,layouts,pages,ref,meta),'braki':[{'pole':p,'hipoteza':'Inny zapis/odmiana, rozdzielenie bloków lub brak wartości w dokumencie; wymaga sprawdzenia'} for p,f in fields.items() if f['dopasowanie']=='nieznaleziona']}


def podsumuj(cards):
    counts=Counter(); byclass=defaultdict(Counter); fields=defaultdict(Counter); groups=defaultdict(Counter); examples=defaultdict(list)
    for c in cards:
        for k in {x['kod'] for x in c['kody']}: byclass[k][c['klasa']]+=1
        for p,f in c['pola'].items():
            counts[f['dopasowanie']]+=1; fields[typ_grupy(p)][f['dopasowanie']]+=1
        for g in c['grupy']:
            key=c['klasa']+' / '+g['typ']; groups[key]['wszystkie']+=1; groups[key]['spojne']+=g['spojna']; groups[key]['bez_obszaru']+=not bool(g['obszary'])
            groups[key]['kompletne']+=g['pola_zlokalizowane']==g['pola_do_lokalizacji']
            if not g['spojna'] and len(examples[key])<5: examples[key].append({'id':c['id'],'grupa':g['id'],'kolidujace_pola':sorted({p for a in g['obszary'] for p in a['kolidujace_pola']})})
    for status in ('dokladne','inny_zapis','inna_forma_gramatyczna','wyliczana','nieznaleziona','null_w_referencji'):
        counts.setdefault(status,0)
    return {'dokumenty':len(cards),'referencje_z_aktualizacji':[c['id'] for c in cards if 'organizator-uzp-aktualizacje' in c['referencja']],'klasy':dict(Counter(c['klasa'] for c in cards)),'dopasowanie':dict(counts),'dopasowanie_per_pole':dict(fields),'kody':{k:{'razem':sum(byclass[k].values()),'per_klasa':dict(byclass[k])} for k in KODY},'najczestsze_braki':sorted([{'pole':p,'liczba':v['nieznaleziona']} for p,v in fields.items() if v['nieznaleziona']],key=lambda x:-x['liczba']),'grupowanie':{k:{**v,'odsetek_spojnych':round(100*v['spojne']/v['wszystkie'],2),'przyklady_niespojnych':examples[k]} for k,v in groups.items()}}


def main():
    validator=Draft202012Validator(wczytaj_json(FORMAT/'karta.schema.json'))
    cards=[]
    for d in wczytaj_json(RUN/'manifest.json')['dokumenty']:
        if d['zrodlo']!='pozytywny': continue
        c=karta(d); validator.validate(c); zapisz_json(RUN/'karty'/f"{c['id']}.json",c); cards.append(c)
        print(c['id'],flush=True)
    zapisz_json(RUN/'karty/podsumowanie.json',podsumuj(cards))


if __name__=='__main__': main()
