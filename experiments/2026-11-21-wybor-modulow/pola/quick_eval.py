import lib, rules, json, re, collections, sys
t=lib.read_text_cache(); its={i.key:i for i in lib.dev_items()}
def assemble_appeal(tx):
    fx=rules.extract_appeal_fixed(tx); act=rules.extract_act(tx); pa=rules.extract_parties(tx)
    return {"OdwolanieKIO":{"data":fx["data"],"czynnosc_dzien":act["czynnosc_dzien"],"czynnosc_powod_id":act["czynnosc_powod_id"],"czynnosc_opis":act["czynnosc_opis"],"miejscowosc":fx["miejscowosc"]},
     "Odwolujacy":pa["Odwolujacy"] or [{}],"Zamawiajacy":pa["Zamawiajacy"] or [{}],
     "ZamowieniePubliczne":{"numer_bzp":fx["numer_bzp"],"numer_postepowania":fx["numer_postepowania"],"numer_ted":fx["numer_ted"],"tytul":pa["tytul"]}}
def assemble_poa(tx):
    p=rules.extract_poa(tx)
    mm=[{"data":{"imie_nazwisko":None,"krs":m["krs"],"nazwa":m["nazwa"],"nip":m["nip"],"typ":"osoba_prawna"},"podpisujacy":[]} for m in p["mocodawcy"]]
    mm=mm or [{"data":{"imie_nazwisko":p["imie_nazwisko"],"krs":p["krs"],"nazwa":p["nazwa"],"nip":p["nip"],"typ":p["typ"]},"podpisujacy":[]}]
    mm[0]["podpisujacy"]=[{"imie_nazwisko":n} for n in p["podpisujacy"]]
    return {"mocodawca":mm,
            "pelnomocnicy":[{"imie_nazwisko":n,"pesel":None} for n in p["pelnomocnicy"]]}
def assemble_tr(tx):
    return {"przelew_bankowy":{**rules.extract_transfer(tx),"tytul":None}}
fn={"odwolanie":assemble_appeal,"pelnomocnictwo":assemble_poa,"przelew":assemble_tr}
per={}; errs=collections.defaultdict(list)
for k,i in its.items():
    if i.document_class not in fn: continue
    ref=lib.reference_for(i); pred=fn[i.document_class](lib.doc_text(t[k]))
    o=lib.outcomes(pred,ref); per[k]=o
    for p,v in o:
        if v in('fp','fn'): errs[lib.generic(p)].append((k,v))
print(lib.f1_report(per))
for p,f in lib.per_field(per).items(): print(p,f)
if len(sys.argv)>1:
    for p,l in errs.items():
        if sys.argv[1] in p: print(p,l[:12])
