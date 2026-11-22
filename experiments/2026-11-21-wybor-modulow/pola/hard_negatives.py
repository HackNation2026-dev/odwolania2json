"""Negatywy zbliżone do klas (syntetyczne, szablonowe, deterministyczne): lure'y z słowami „odwołanie”, „pełnomocnik”, „rachunek”, „kwota”.

Etykieta `foreign` = jednoznacznie obcy dokument; `boundary` = przypadek graniczny klasy (np. przelew niezrealizowany), raportowany osobno.
Nazwy podmiotów pochodzą z referencji rozwojowych (bez zbioru kontrolnego). Tylko tekst (bez PDF): router działa na tekście odczytu.
"""
from __future__ import annotations

import random

import lib


def _names() -> list[str]:
    out = []
    for it in lib.dev_items():
        if it.document_class == "odwolanie":
            r = lib.reference_for(it)
            out.append(r["Odwolujacy"][0]["nazwa"])
            out.append(r["Zamawiajacy"][0]["nazwa"])
    return out


T: dict[str, tuple[str, str]] = {
 "odpowiedz_na_odwolanie": ("foreign", """Odpowiedź na odwołanie
Do Prezesa Krajowej Izby Odwoławczej
ul. Postępu 17A, 02-676 Warszawa
Zamawiający: {B}
Odwołujący: {A}
dotyczy: odwołania wniesionego w dniu 3 marca 2026 roku, sygnatura KIO 1234/26
W imieniu Zamawiającego wnoszę o oddalenie odwołania w całości. Zarzuty Odwołującego są bezzasadne.
Zarzut nr 1 nie zasługuje na uwzględnienie, gdyż Zamawiający dokonał czynności zgodnie z art. 226 ust. 1 pkt 5 Pzp.
Do pisma załączam pełnomocnictwo oraz dowód nadania."""),
 "przystapienie": ("foreign", """Zgłoszenie przystąpienia do postępowania odwoławczego
Krajowa Izba Odwoławcza, Warszawa
Przystępujący: {A}
Działając na podstawie art. 525 ust. 1 Pzp zgłaszam przystąpienie do postępowania odwoławczego po stronie Zamawiającego {B}.
Odwołanie zostało wniesione przez innego wykonawcę. Pełnomocnik Przystępującego: r. pr. Jan Nowak."""),
 "skarga_na_wyrok": ("foreign", """Skarga na wyrok Krajowej Izby Odwoławczej
Sąd Okręgowy w Warszawie – Sąd Zamówień Publicznych
za pośrednictwem Prezesa Krajowej Izby Odwoławczej
Skarżący: {A}
Zamawiający: {B}
Na podstawie art. 579 ust. 1 Pzp wnoszę skargę na wyrok KIO z dnia 12 maja 2026 r. sygn. akt KIO 2001/26 oddalający odwołanie.
Wnoszę o uchylenie wyroku w całości. Pełnomocnik skarżącego: adw. Anna Kowalska."""),
 "wyciag_bankowy": ("foreign", """WYCIĄG Z RACHUNKU BANKOWEGO
Bank Pomorski S.A.
Posiadacz rachunku: {A}
Rachunek: PL61 1090 1014 0000 0712 1981 2874
Saldo początkowe: 12 450,00 PLN
Data operacji | Opis | Kwota
04.03.2026 | Przelew przychodzący | 2 300,00
09.03.2026 | Opłata skarbowa | -17,00
Saldo końcowe: 14 733,00 PLN"""),
 "faktura": ("foreign", """FAKTURA VAT nr FV/2026/03/118
Sprzedawca: {B}
Nabywca: {A}
Rachunek bankowy sprzedawcy: PL27 1140 2004 0000 3002 0135 5387
Pozycja: usługi doradcze, kwota netto 8 000,00 zł, VAT 23%, razem 9 840,00 zł
Termin płatności: 14 dni. Pełnomocnik sprzedawcy nie występuje."""),
 "wezwanie_do_zaplaty": ("foreign", """Wezwanie do zapłaty
{B} wzywa {A} do zapłaty kwoty 10 000,00 zł tytułem kary umownej w terminie 7 dni na rachunek PL27 1140 2004 0000 3002 0135 5387.
W razie braku zapłaty sprawa zostanie skierowana do sądu. Pełnomocnik wierzyciela: r. pr. Piotr Zieliński."""),
 "wezwanie_kio_wpis": ("foreign", """Krajowa Izba Odwoławcza
Wezwanie do uzupełnienia braków formalnych odwołania
Odwołujący: {A}
Zamawiający: {B}
Wzywa się Odwołującego do uzupełnienia dowodu uiszczenia wpisu od odwołania w terminie 3 dni od doręczenia wezwania pod rygorem zwrotu odwołania.
Przewodniczący"""),
 "protokol_rozprawy": ("foreign", """Protokół z rozprawy przed Krajową Izbą Odwoławczą
Sygn. akt KIO 1500/26
Odwołujący: {A}, Zamawiający: {B}
Obecni: pełnomocnik Odwołującego, pełnomocnik Zamawiającego. Izba oddaliła wniosek dowodowy. Kwota wpisu 15 000,00 zł została uiszczona."""),
 "pelnomocnictwo_notarialne_inne": ("boundary", """PEŁNOMOCNICTWO
Ja, {A}, ustanawiam pełnomocnikiem Pana Jana Kowalskiego do zawarcia w moim imieniu umowy sprzedaży nieruchomości położonej w Krakowie.
Pełnomocnictwo nie dotyczy postępowań przed KIO. Mocodawca: .............. """),
 "przelew_niezrealizowany": ("boundary", """POLECENIE PRZELEWU – ODRZUCONE
Płatnik: {A}
Rachunek obciążany: PL27 1140 2004 0000 3002 0135 5387
Rachunek odbiorcy: PL61 1090 1014 0000 0712 1981 2874
Kwota operacji: 17,00 PLN
Status: niezrealizowane z powodu braku środków. Operacja nie została wykonana."""),
}


def build(per_type: int = 5, seed: int = 20261122) -> list[dict]:
    rng = random.Random(seed)
    names = _names()
    docs = []
    for kind, (label, tpl) in T.items():
        for i in range(per_type):
            a, b = rng.sample(names, 2)
            docs.append({"key": f"hard/{kind}/{i}", "kind": kind, "label": label, "pages": [{"number": 1, "text": tpl.format(A=a, B=b)}]})
    return docs
