//! Wczytywanie przebiegu oraz atomowy zapis adnotacji i eksportu CSV.
//!
//! Przeglądarka czyta `manifest.json`, `dokumenty/<id>.json` i obrazy stron,
//! a pisze wyłącznie do `adnotacje/` (oraz `adnotacje_zbiorcze.csv` na żądanie).

use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

use crate::model::{Adnotacja, Dokument, Manifest};

/// Stan adnotacji dokumentu wczytanej z dysku.
#[derive(Debug, Clone)]
pub enum StanAdnotacji {
    /// Brak pliku – dokument nieprzejrzany.
    Brak,
    Jest(Box<Adnotacja>),
    /// Plik istnieje, ale nie da się go odczytać. Nie nadpisujemy go.
    Blad(String),
}

impl StanAdnotacji {
    pub fn adnotacja(&self) -> Option<&Adnotacja> {
        match self {
            StanAdnotacji::Jest(a) => Some(a.as_ref()),
            _ => None,
        }
    }

    pub fn status(&self) -> &str {
        match self {
            StanAdnotacji::Brak => "nieprzejrzany",
            StanAdnotacji::Jest(a) => &a.status,
            StanAdnotacji::Blad(_) => "blad",
        }
    }
}

/// Jeden dokument przebiegu: wpis z manifestu + wczytane wyniki i adnotacja.
pub struct PozycjaDokumentu {
    pub wpis: crate::model::WpisDokumentu,
    pub dokument: Result<Dokument, String>,
    pub adnotacja: StanAdnotacji,
    pub rozbieznosc: bool,
}

pub struct Przebieg {
    pub katalog: PathBuf,
    pub manifest: Manifest,
    pub pozycje: Vec<PozycjaDokumentu>,
}

fn czytaj_json<T: serde::de::DeserializeOwned>(sciezka: &Path) -> Result<T, String> {
    let tekst = fs::read_to_string(sciezka).map_err(|e| format!("{}: {e}", sciezka.display()))?;
    serde_json::from_str(&tekst).map_err(|e| format!("{}: błędny JSON: {e}", sciezka.display()))
}

/// Ścieżka względna z pliku (separator `/`) zamieniona na ścieżkę w katalogu przebiegu.
pub fn sciezka_wzgledna(katalog: &Path, wzgledna: &str) -> PathBuf {
    let mut p = katalog.to_path_buf();
    for czesc in wzgledna.split('/').filter(|c| !c.is_empty() && *c != ".") {
        p.push(czesc);
    }
    p
}

pub fn sciezka_adnotacji(katalog: &Path, id: &str) -> PathBuf {
    katalog.join("adnotacje").join(format!("{id}.json"))
}

pub fn wczytaj_adnotacje(katalog: &Path, id: &str) -> StanAdnotacji {
    let sciezka = sciezka_adnotacji(katalog, id);
    if !sciezka.exists() {
        return StanAdnotacji::Brak;
    }
    match czytaj_json::<Adnotacja>(&sciezka) {
        Ok(a) => StanAdnotacji::Jest(Box::new(a)),
        Err(e) => StanAdnotacji::Blad(e),
    }
}

impl Przebieg {
    /// Wczytuje cały przebieg. Błąd zwraca tylko dla manifestu; błędy
    /// pojedynczych dokumentów i adnotacji są trzymane przy pozycjach.
    pub fn wczytaj(katalog: &Path) -> Result<Przebieg, String> {
        let manifest: Manifest = czytaj_json(&katalog.join("manifest.json"))?;
        let pozycje = manifest
            .dokumenty
            .iter()
            .map(|wpis| {
                let plik = if wpis.plik_wynikow.is_empty() {
                    format!("dokumenty/{}.json", wpis.id)
                } else {
                    wpis.plik_wynikow.clone()
                };
                let sciezka = sciezka_wzgledna(katalog, &plik);
                let dokument = czytaj_json::<Dokument>(&sciezka).and_then(|d| {
                    if d.id.is_empty() {
                        Err(format!("{}: brak pola „id” (to nie wygląda na plik dokumentu)", sciezka.display()))
                    } else {
                        Ok(d)
                    }
                });
                let rozbieznosc = dokument.as_ref().map(crate::model::rozbieznosc).unwrap_or(false);
                PozycjaDokumentu {
                    wpis: wpis.clone(),
                    dokument,
                    adnotacja: wczytaj_adnotacje(katalog, &wpis.id),
                    rozbieznosc,
                }
            })
            .collect();
        Ok(Przebieg { katalog: katalog.to_path_buf(), manifest, pozycje })
    }

    pub fn kod_w_taksonomii(&self, kod: &str) -> bool {
        self.manifest.taksonomia.iter().any(|t| t.kod == kod)
    }
}

/// Zapisuje plik atomowo: plik tymczasowy w tym samym katalogu, fsync, rename.
pub fn zapisz_atomowo(sciezka: &Path, tresc: &[u8]) -> Result<(), String> {
    let katalog = sciezka.parent().ok_or_else(|| format!("{}: brak katalogu nadrzędnego", sciezka.display()))?;
    fs::create_dir_all(katalog).map_err(|e| format!("{}: {e}", katalog.display()))?;
    let nazwa = sciezka.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
    let tymczasowy = katalog.join(format!(".{nazwa}.{}.tmp", std::process::id()));
    let wynik = (|| -> std::io::Result<()> {
        let mut plik = fs::File::create(&tymczasowy)?;
        plik.write_all(tresc)?;
        plik.sync_all()?;
        drop(plik);
        fs::rename(&tymczasowy, sciezka)
    })();
    if let Err(e) = wynik {
        let _ = fs::remove_file(&tymczasowy);
        return Err(format!("{}: {e}", sciezka.display()));
    }
    Ok(())
}

pub fn zapisz_adnotacje(katalog: &Path, adnotacja: &Adnotacja) -> Result<(), String> {
    let mut json = serde_json::to_string_pretty(adnotacja).map_err(|e| e.to_string())?;
    json.push('\n');
    zapisz_atomowo(&sciezka_adnotacji(katalog, &adnotacja.id), json.as_bytes())
}

/// Bieżący czas lokalny w ISO 8601 z przesunięciem, np. `2026-11-21T17:30:00+01:00`.
pub fn teraz_iso() -> String {
    chrono::Local::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, false)
}

/// Najnowszy (wg czasu modyfikacji manifestu) podkatalog `wyniki/*/` z `manifest.json`.
pub fn najnowszy_przebieg(wyniki: &Path) -> Option<PathBuf> {
    let mut kandydaci: Vec<(std::time::SystemTime, PathBuf)> = fs::read_dir(wyniki)
        .ok()?
        .filter_map(|w| w.ok())
        .map(|w| w.path())
        .filter(|p| p.join("manifest.json").is_file())
        .map(|p| {
            let czas = fs::metadata(p.join("manifest.json"))
                .and_then(|m| m.modified())
                .unwrap_or(std::time::UNIX_EPOCH);
            (czas, p)
        })
        .collect();
    kandydaci.sort();
    kandydaci.pop().map(|(_, p)| p)
}

/// Domyślne miejsce z przebiegami: `../wyniki` względem katalogu crate'a lub bieżącego.
pub fn domyslny_katalog_wynikow() -> Vec<PathBuf> {
    let mut wyniki = Vec::new();
    if let Ok(cwd) = std::env::current_dir() {
        wyniki.push(cwd.join("..").join("wyniki"));
        wyniki.push(cwd.join("wyniki"));
    }
    wyniki.push(Path::new(env!("CARGO_MANIFEST_DIR")).join("..").join("wyniki"));
    wyniki
}

// ---------------------------------------------------------------- CSV

fn pole_csv(s: &str) -> String {
    if s.contains([',', '"', '\n', '\r']) {
        format!("\"{}\"", s.replace('"', "\"\""))
    } else {
        s.to_string()
    }
}

/// Wiersz na problem: id, strona (puste dla dokumentu), kod, waga, opis, recenzent, status.
pub fn csv_adnotacji<'a>(adnotacje: impl IntoIterator<Item = &'a Adnotacja>) -> String {
    let mut out = String::from("id,strona,kod,waga,opis,recenzent,status\n");
    let mut wiersz = |a: &Adnotacja, strona: Option<u32>, p: &crate::model::Problem| {
        let strona = strona.map(|n| n.to_string()).unwrap_or_default();
        let pola = [a.id.as_str(), &strona, &p.kod, &p.waga, &p.opis, &a.recenzent, &a.status];
        out.push_str(&pola.iter().map(|s| pole_csv(s)).collect::<Vec<_>>().join(","));
        out.push('\n');
    };
    for a in adnotacje {
        for p in &a.problemy_dokumentu {
            wiersz(a, None, p);
        }
        for s in &a.strony {
            for p in &s.problemy {
                wiersz(a, Some(s.nr), p);
            }
        }
    }
    out
}

pub fn eksportuj_csv(przebieg: &Przebieg) -> Result<PathBuf, String> {
    let csv = csv_adnotacji(przebieg.pozycje.iter().filter_map(|p| p.adnotacja.adnotacja()));
    let sciezka = przebieg.katalog.join("adnotacje_zbiorcze.csv");
    zapisz_atomowo(&sciezka, csv.as_bytes())?;
    Ok(sciezka)
}
