//! Statystyki zbiorcze przebiegu (widok „Podsumowanie”).

use std::collections::BTreeMap;

use crate::dane::Przebieg;
use crate::model::{klasa_zgodna, STATUSY};

#[derive(Debug, Default, Clone, PartialEq)]
pub struct StatystykaModelu {
    pub id: String,
    pub nazwa: String,
    /// Dokumenty z wynikiem i znaną klasą oczekiwaną.
    pub ocenione_klasy: usize,
    pub trafione_klasy: usize,
    pub bledy: usize,
    pub srednie_podobienstwo: Option<f64>,
    pub liczba_podobienstw: usize,
    /// kod → (wykryte, łącznie)
    pub wstrzykniete: BTreeMap<String, (usize, usize)>,
}

impl StatystykaModelu {
    pub fn odsetek_klas(&self) -> Option<f64> {
        (self.ocenione_klasy > 0).then(|| self.trafione_klasy as f64 / self.ocenione_klasy as f64)
    }
}

#[derive(Debug, Default, Clone, PartialEq)]
pub struct Podsumowanie {
    pub modele: Vec<StatystykaModelu>,
    /// status → liczba dokumentów (w tym „nieprzejrzany” dla braku pliku, „blad” dla złego pliku)
    pub statusy: BTreeMap<String, usize>,
    /// kod → liczba nadań przez człowieka (problemy dokumentu + stron)
    pub kody_czlowieka: BTreeMap<String, usize>,
}

pub fn policz(przebieg: &Przebieg) -> Podsumowanie {
    let mut wynik = Podsumowanie::default();
    for s in STATUSY {
        wynik.statusy.insert(s.to_string(), 0);
    }

    for m in &przebieg.manifest.modele {
        let mut st = StatystykaModelu { id: m.id.clone(), nazwa: m.nazwa.clone(), ..Default::default() };
        let mut suma_pod = 0.0;
        for poz in &przebieg.pozycje {
            let Ok(dok) = &poz.dokument else { continue };
            let Some(wpis) = dok.modele.get(&m.id) else { continue };
            if wpis.status == "blad" {
                st.bledy += 1;
            }
            if let Some(t) = klasa_zgodna(wpis, dok.klasa_oczekiwana.as_deref()) {
                st.ocenione_klasy += 1;
                if t {
                    st.trafione_klasy += 1;
                }
            }
            if let Some(ocena) = &wpis.ocena_auto {
                for p in ocena.podobienstwo_transkrypcji.iter().filter_map(|p| p.podobienstwo) {
                    suma_pod += p;
                    st.liczba_podobienstw += 1;
                }
            }
            // Wstrzyknięte liczymy tylko tam, gdzie model faktycznie dostał dokument.
            if wpis.status == "ok" {
                let wykryte = wpis.ocena_auto.as_ref().map(|o| o.wykryte_wstrzykniete.as_slice()).unwrap_or(&[]);
                for w in &dok.wstrzykniete {
                    let e = st.wstrzykniete.entry(w.kod.clone()).or_default();
                    e.1 += 1;
                    if wykryte.contains(&w.kod) {
                        e.0 += 1;
                    }
                }
            }
        }
        if st.liczba_podobienstw > 0 {
            st.srednie_podobienstwo = Some(suma_pod / st.liczba_podobienstw as f64);
        }
        wynik.modele.push(st);
    }

    for poz in &przebieg.pozycje {
        *wynik.statusy.entry(poz.adnotacja.status().to_string()).or_default() += 1;
        if let Some(a) = poz.adnotacja.adnotacja() {
            let kody = a.problemy_dokumentu.iter().chain(a.strony.iter().flat_map(|s| s.problemy.iter()));
            for p in kody {
                *wynik.kody_czlowieka.entry(p.kod.clone()).or_default() += 1;
            }
        }
    }
    wynik
}
