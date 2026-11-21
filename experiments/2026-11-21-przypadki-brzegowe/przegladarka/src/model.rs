//! Typy serde odpowiadające schematom z `format/`.
//!
//! Zasady tolerancji (FORMAT.md): nieznane pola są ignorowane (brak
//! `deny_unknown_fields`), brak pola lub `null` daje wartość domyślną,
//! a wartości wyliczeniowe trzymamy jako `String`, żeby nowa wartość
//! (np. nowy kod problemu albo nowy status) nie psuła wczytywania.

use std::collections::BTreeMap;

use serde::{Deserialize, Deserializer, Serialize};

/// Deserializuje pole, zamieniając `null` na wartość domyślną typu.
pub fn nul<'de, D, T>(d: D) -> Result<T, D::Error>
where
    D: Deserializer<'de>,
    T: Deserialize<'de> + Default,
{
    Ok(Option::<T>::deserialize(d)?.unwrap_or_default())
}

pub const WAGI: [&str; 3] = ["niska", "srednia", "wysoka"];
pub const STATUSY: [&str; 4] = ["nieprzejrzany", "w_toku", "przejrzany", "do_dyskusji"];
pub const KLASY_CZLOWIEKA: [&str; 5] = ["odwolanie", "pelnomocnictwo", "przelew", "obcy", "niepewne"];
pub const OCENY_MODELI: [&str; 4] = ["trafne", "czesciowo", "chybione", "brak_oceny"];

// ---------------------------------------------------------------- manifest

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct Manifest {
    #[serde(deserialize_with = "nul")]
    pub format: String,
    #[serde(deserialize_with = "nul")]
    pub wersja: i64,
    #[serde(deserialize_with = "nul")]
    pub przebieg: String,
    #[serde(deserialize_with = "nul")]
    pub utworzono: String,
    #[serde(deserialize_with = "nul")]
    pub opis: String,
    #[serde(deserialize_with = "nul")]
    pub taksonomia: Vec<KodTaksonomii>,
    #[serde(deserialize_with = "nul")]
    pub modele: Vec<ModelInfo>,
    #[serde(deserialize_with = "nul")]
    pub dokumenty: Vec<WpisDokumentu>,
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct KodTaksonomii {
    #[serde(deserialize_with = "nul")]
    pub kod: String,
    #[serde(deserialize_with = "nul")]
    pub nazwa: String,
    #[serde(deserialize_with = "nul")]
    pub opis: String,
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct ModelInfo {
    #[serde(deserialize_with = "nul")]
    pub id: String,
    #[serde(deserialize_with = "nul")]
    pub nazwa: String,
    #[serde(deserialize_with = "nul")]
    pub model: String,
    pub uwagi: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct WpisDokumentu {
    #[serde(deserialize_with = "nul")]
    pub id: String,
    #[serde(deserialize_with = "nul")]
    pub plik_zrodlowy: String,
    #[serde(deserialize_with = "nul")]
    pub zrodlo: String,
    pub klasa_oczekiwana: Option<String>,
    pub sprawa: Option<String>,
    #[serde(deserialize_with = "nul")]
    pub liczba_stron: u32,
    #[serde(deserialize_with = "nul")]
    pub plik_wynikow: String,
    #[serde(deserialize_with = "nul")]
    pub typ_auto: String,
    #[serde(deserialize_with = "nul")]
    pub przeslany_do_modeli: bool,
}

// ---------------------------------------------------------------- dokument

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct Dokument {
    #[serde(deserialize_with = "nul")]
    pub id: String,
    #[serde(deserialize_with = "nul")]
    pub plik_zrodlowy: String,
    #[serde(deserialize_with = "nul")]
    pub zrodlo: String,
    pub klasa_oczekiwana: Option<String>,
    pub sprawa: Option<String>,
    #[serde(deserialize_with = "nul")]
    pub metadane: Metadane,
    #[serde(deserialize_with = "nul")]
    pub strony: Vec<StronaDokumentu>,
    #[serde(deserialize_with = "nul")]
    pub wstrzykniete: Vec<Wstrzykniety>,
    #[serde(deserialize_with = "nul")]
    pub modele: BTreeMap<String, WpisModelu>,
}

impl Dokument {
    pub fn strona(&self, nr: u32) -> Option<&StronaDokumentu> {
        self.strony.iter().find(|s| s.nr == nr)
    }
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct Metadane {
    pub producent: Option<String>,
    pub kreator: Option<String>,
    pub rozmiar_bajtow: Option<u64>,
    pub zaszyfrowany: Option<bool>,
    pub wersja_pdf: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct StronaDokumentu {
    #[serde(deserialize_with = "nul")]
    pub nr: u32,
    #[serde(deserialize_with = "nul")]
    pub obraz: String,
    pub szerokosc_pt: Option<f64>,
    pub wysokosc_pt: Option<f64>,
    pub obrot_pdf: Option<i64>,
    pub znaki_tekstu: Option<u64>,
    pub obrazy: Option<u64>,
    pub pokrycie_obrazami: Option<f64>,
    pub dpi_obrazow: Option<f64>,
    #[serde(deserialize_with = "nul")]
    pub typ_auto: String,
    #[serde(deserialize_with = "nul")]
    pub probka_tekstu: String,
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct Wstrzykniety {
    #[serde(deserialize_with = "nul")]
    pub kod: String,
    pub strona: Option<u32>,
    #[serde(deserialize_with = "nul")]
    pub opis: String,
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct WpisModelu {
    #[serde(deserialize_with = "nul")]
    pub status: String,
    pub czas_s: Option<f64>,
    pub blad: Option<String>,
    #[serde(deserialize_with = "nul")]
    pub strony_przeslane: Vec<u32>,
    pub wynik: Option<WynikModelu>,
    pub ocena_auto: Option<OcenaAuto>,
}

impl WpisModelu {
    /// Wynik tylko wtedy, gdy model zakończył się poprawnie.
    pub fn wynik_ok(&self) -> Option<&WynikModelu> {
        if self.status == "ok" { self.wynik.as_ref() } else { None }
    }
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct WynikModelu {
    #[serde(deserialize_with = "nul")]
    pub klasa: String,
    #[serde(deserialize_with = "nul")]
    pub uzasadnienie_klasy: String,
    #[serde(deserialize_with = "nul")]
    pub strony: Vec<StronaModelu>,
    #[serde(deserialize_with = "nul")]
    pub problemy_dokumentu: Vec<Problem>,
}

impl WynikModelu {
    pub fn strona(&self, nr: u32) -> Option<&StronaModelu> {
        self.strony.iter().find(|s| s.nr == nr)
    }
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct StronaModelu {
    #[serde(deserialize_with = "nul")]
    pub nr: u32,
    #[serde(deserialize_with = "nul")]
    pub typ: String,
    pub obrot_stopnie: Option<i64>,
    #[serde(deserialize_with = "nul")]
    pub jakosc: String,
    #[serde(deserialize_with = "nul")]
    pub transkrypcja_poczatku: String,
    #[serde(deserialize_with = "nul")]
    pub problemy: Vec<Problem>,
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct OcenaAuto {
    pub klasa_trafiona: Option<bool>,
    #[serde(deserialize_with = "nul")]
    pub podobienstwo_transkrypcji: Vec<Podobienstwo>,
    #[serde(deserialize_with = "nul")]
    pub wykryte_wstrzykniete: Vec<String>,
    #[serde(deserialize_with = "nul")]
    pub pominiete_wstrzykniete: Vec<String>,
}

impl OcenaAuto {
    pub fn podobienstwo(&self, nr: u32) -> Option<f64> {
        self.podobienstwo_transkrypcji
            .iter()
            .find(|p| p.nr == nr)
            .and_then(|p| p.podobienstwo)
    }
}

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(default)]
pub struct Podobienstwo {
    #[serde(deserialize_with = "nul")]
    pub nr: u32,
    pub podobienstwo: Option<f64>,
}

// ---------------------------------------------------------------- problemy i adnotacje

#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Problem {
    #[serde(deserialize_with = "nul")]
    pub kod: String,
    #[serde(deserialize_with = "nul")]
    pub opis: String,
    #[serde(deserialize_with = "nul")]
    pub waga: String,
}

impl Problem {
    /// Kopia z wagą sprowadzoną do dozwolonych wartości (dla zapisu adnotacji).
    pub fn znormalizowany(&self) -> Problem {
        let waga = if WAGI.contains(&self.waga.as_str()) { self.waga.clone() } else { "srednia".into() };
        Problem { kod: self.kod.clone(), opis: self.opis.clone(), waga }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Adnotacja {
    #[serde(deserialize_with = "nul")]
    pub id: String,
    #[serde(deserialize_with = "nul")]
    pub wersja: i64,
    #[serde(deserialize_with = "nul")]
    pub recenzent: String,
    #[serde(deserialize_with = "nul")]
    pub zmieniono: String,
    #[serde(deserialize_with = "nul")]
    pub status: String,
    pub klasa: Option<String>,
    #[serde(deserialize_with = "nul")]
    pub notatka: String,
    #[serde(deserialize_with = "nul")]
    pub problemy_dokumentu: Vec<Problem>,
    #[serde(deserialize_with = "nul")]
    pub strony: Vec<AdnotacjaStrony>,
    #[serde(deserialize_with = "nul")]
    pub ocena_modeli: BTreeMap<String, String>,
    /// Nieznane pola zachowujemy przy ponownym zapisie (zgodność w przód).
    #[serde(flatten)]
    pub inne: serde_json::Map<String, serde_json::Value>,
}

impl Default for Adnotacja {
    fn default() -> Self {
        Adnotacja {
            id: String::new(),
            wersja: 1,
            recenzent: String::new(),
            zmieniono: String::new(),
            status: "nieprzejrzany".into(),
            klasa: None,
            notatka: String::new(),
            problemy_dokumentu: Vec::new(),
            strony: Vec::new(),
            ocena_modeli: BTreeMap::new(),
            inne: serde_json::Map::new(),
        }
    }
}

impl Adnotacja {
    pub fn nowa(id: &str) -> Self {
        Adnotacja { id: id.to_string(), ..Default::default() }
    }

    pub fn strona(&self, nr: u32) -> Option<&AdnotacjaStrony> {
        self.strony.iter().find(|s| s.nr == nr)
    }

    pub fn strona_mut(&mut self, nr: u32) -> &mut AdnotacjaStrony {
        if let Some(i) = self.strony.iter().position(|s| s.nr == nr) {
            &mut self.strony[i]
        } else {
            self.strony.push(AdnotacjaStrony { nr, ..Default::default() });
            self.strony.sort_by_key(|s| s.nr);
            let i = self.strony.iter().position(|s| s.nr == nr).unwrap_or(0);
            &mut self.strony[i]
        }
    }

    /// Wynik edycji w UI: `None`, gdy nic się nie zmieniło. Pierwsza edycja
    /// dokumentu „nieprzejrzany” zmienia jego status na „w_toku”.
    pub fn po_edycji(oryginal: &Adnotacja, mut edytowana: Adnotacja) -> Option<Adnotacja> {
        if &edytowana == oryginal {
            return None;
        }
        if edytowana.status == "nieprzejrzany" && oryginal.status == "nieprzejrzany" {
            edytowana.status = "w_toku".into();
        }
        Some(edytowana)
    }

    /// Dopisuje problemy dokumentu i stron z odpowiedzi modelu (bez duplikatów).
    pub fn przejmij_z_modelu(&mut self, wynik: &WynikModelu) {
        fn dopisz(cel: &mut Vec<Problem>, zrodlo: &[Problem]) {
            for p in zrodlo.iter().map(Problem::znormalizowany) {
                if !cel.contains(&p) {
                    cel.push(p);
                }
            }
        }
        dopisz(&mut self.problemy_dokumentu, &wynik.problemy_dokumentu);
        for s in wynik.strony.iter().filter(|s| !s.problemy.is_empty()) {
            dopisz(&mut self.strona_mut(s.nr).problemy, &s.problemy);
        }
    }

    /// Porządkuje przed zapisem: usuwa puste wpisy stron, normalizuje wagi,
    /// uzupełnia oceny brakujących modeli i ustawia pola techniczne.
    pub fn przygotuj_do_zapisu(&mut self, recenzent: &str, modele: &[ModelInfo], teraz: String) {
        self.wersja = 1;
        if !recenzent.trim().is_empty() {
            self.recenzent = recenzent.trim().to_string();
        }
        self.zmieniono = teraz;
        if !STATUSY.contains(&self.status.as_str()) {
            self.status = "w_toku".into();
        }
        self.strony.retain(|s| !s.problemy.is_empty() || !s.notatka.trim().is_empty());
        self.strony.sort_by_key(|s| s.nr);
        for p in self.problemy_dokumentu.iter_mut() {
            *p = p.znormalizowany();
        }
        for s in self.strony.iter_mut() {
            for p in s.problemy.iter_mut() {
                *p = p.znormalizowany();
            }
        }
        for m in modele {
            self.ocena_modeli.entry(m.id.clone()).or_insert_with(|| "brak_oceny".into());
        }
        for v in self.ocena_modeli.values_mut() {
            if !OCENY_MODELI.contains(&v.as_str()) {
                *v = "brak_oceny".into();
            }
        }
    }
}

#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct AdnotacjaStrony {
    #[serde(deserialize_with = "nul")]
    pub nr: u32,
    #[serde(deserialize_with = "nul")]
    pub problemy: Vec<Problem>,
    #[serde(deserialize_with = "nul")]
    pub notatka: String,
}

// ---------------------------------------------------------------- pomocnicze

/// Klasa modelu sprowadzona do słownika klas oczekiwanych
/// (modele mówią „inny”, a manifest „obcy”).
pub fn klasa_porownywalna(klasa: &str) -> &str {
    if klasa == "inny" { "obcy" } else { klasa }
}

/// Czy klasa modelu zgadza się z oczekiwaną. `None`, gdy nie ma czego porównać.
pub fn klasa_zgodna(wpis: &WpisModelu, oczekiwana: Option<&str>) -> Option<bool> {
    if let Some(t) = wpis.ocena_auto.as_ref().and_then(|o| o.klasa_trafiona) {
        return Some(t);
    }
    let wynik = wpis.wynik_ok()?;
    let ocz = oczekiwana?;
    Some(klasa_porownywalna(&wynik.klasa) == ocz)
}

/// Rozbieżność: modele wskazały różne klasy albo klasę inną niż oczekiwana.
pub fn rozbieznosc(dok: &Dokument) -> bool {
    let klasy: std::collections::BTreeSet<&str> = dok
        .modele
        .values()
        .filter_map(|w| w.wynik_ok())
        .map(|w| klasa_porownywalna(&w.klasa))
        .collect();
    if klasy.len() > 1 {
        return true;
    }
    match dok.klasa_oczekiwana.as_deref() {
        Some(ocz) => klasy.iter().any(|k| *k != ocz),
        None => false,
    }
}
