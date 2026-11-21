//! Zakładka „Modele”: odpowiedzi modeli dla dokumentu i bieżącej strony.

use egui::RichText;

use super::{Sesja, wspolne};
use crate::dane::Przebieg;
use crate::model::{Dokument, ModelInfo, klasa_zgodna};

/// Minimalna szerokość kolumny modelu, przy której układamy kolumny obok siebie.
const MIN_KOLUMNA: f32 = 240.0;

pub fn zakladka(sesja: &mut Sesja, ui: &mut egui::Ui) {
    let Some(poz) = sesja.przebieg.pozycje.get(sesja.wybrany) else { return };
    let dok = match &poz.dokument {
        Ok(d) => d,
        Err(e) => {
            ui.colored_label(wspolne::KOLOR_ZLE, e);
            return;
        }
    };
    let nr = sesja.nr_strony();
    let przebieg = &sesja.przebieg;
    let modele = &przebieg.manifest.modele;

    egui::ScrollArea::vertical().id_salt("zakladka_modele").show(ui, |ui| {
        ui.label(format!("Klasa oczekiwana: {}", wspolne::opcja(&dok.klasa_oczekiwana)));
        if !poz.wpis.przeslany_do_modeli {
            ui.colored_label(wspolne::KOLOR_UWAGA, "Dokument nie był przesłany do modeli.");
        }
        ui.strong(format!("probka_tekstu (str. {nr})"));
        let probka = dok.strona(nr).map(|s| s.probka_tekstu.as_str()).unwrap_or("");
        wspolne::tekst_przewijany(ui, "probka_modele", probka, 100.0);

        if !dok.wstrzykniete.is_empty() {
            ui.add_space(6.0);
            ui.strong("Wstrzyknięte problemy (dokument syntetyczny)");
            egui::Grid::new("wstrzykniete").striped(true).show(ui, |ui| {
                ui.label("kod");
                ui.label("str.");
                for m in modele {
                    ui.label(RichText::new(&m.nazwa).strong());
                }
                ui.end_row();
                for w in &dok.wstrzykniete {
                    wspolne::kod_problemu(ui, przebieg, &w.kod);
                    ui.label(wspolne::opcja(&w.strona)).on_hover_text(&w.opis);
                    for m in modele {
                        let ocena = dok.modele.get(&m.id).and_then(|w| w.ocena_auto.as_ref());
                        let stan = ocena.map(|o| {
                            if o.wykryte_wstrzykniete.contains(&w.kod) {
                                Some(true)
                            } else if o.pominiete_wstrzykniete.contains(&w.kod) {
                                Some(false)
                            } else {
                                None
                            }
                        });
                        ui.label(wspolne::tak_nie(stan.flatten())).on_hover_text(match stan {
                            Some(Some(true)) => "wykryty",
                            Some(Some(false)) => "pominięty",
                            _ => "brak oceny",
                        });
                    }
                    ui.end_row();
                }
            });
        }

        ui.add_space(6.0);
        ui.separator();
        if modele.is_empty() {
            ui.weak("Manifest nie zawiera modeli.");
            return;
        }
        let szerokosc = ui.available_width();
        if szerokosc / modele.len() as f32 >= MIN_KOLUMNA {
            ui.columns(modele.len(), |kolumny| {
                for (k, m) in kolumny.iter_mut().zip(modele) {
                    kolumna_modelu(k, przebieg, dok, m, nr);
                }
            });
        } else {
            for m in modele {
                kolumna_modelu(ui, przebieg, dok, m, nr);
                ui.separator();
            }
        }
    });
}

fn kolumna_modelu(ui: &mut egui::Ui, przebieg: &Przebieg, dok: &Dokument, m: &ModelInfo, nr: u32) {
    ui.push_id(&m.id, |ui| {
        ui.heading(&m.nazwa).on_hover_text(format!("{}\n{}", m.model, m.uwagi.clone().unwrap_or_default()));
        let Some(wpis) = dok.modele.get(&m.id) else {
            ui.weak("Brak wyniku tego modelu.");
            return;
        };
        let kolor = match wpis.status.as_str() {
            "ok" => wspolne::KOLOR_OK,
            "blad" => wspolne::KOLOR_ZLE,
            _ => egui::Color32::GRAY,
        };
        ui.horizontal(|ui| {
            ui.label("Status:");
            ui.colored_label(kolor, &wpis.status);
            ui.label(format!("czas: {}", wpis.czas_s.map(|c| format!("{c:.1} s")).unwrap_or_else(|| "—".into())));
        });
        if let Some(b) = &wpis.blad {
            ui.colored_label(wspolne::KOLOR_ZLE, b);
        }
        if !wpis.strony_przeslane.is_empty() {
            let s: Vec<String> = wpis.strony_przeslane.iter().map(|n| n.to_string()).collect();
            ui.weak(format!("Przesłane strony: {}", s.join(", ")));
        }
        let Some(wynik) = wpis.wynik.as_ref() else {
            ui.weak("Brak wyniku.");
            return;
        };
        ui.horizontal(|ui| {
            ui.label("Klasa:");
            ui.strong(&wynik.klasa);
            ui.label(wspolne::tak_nie(klasa_zgodna(wpis, dok.klasa_oczekiwana.as_deref())));
        });
        if !wynik.uzasadnienie_klasy.is_empty() {
            egui::CollapsingHeader::new("Uzasadnienie klasy").id_salt("uzasadnienie").show(ui, |ui| {
                ui.add(egui::Label::new(&wynik.uzasadnienie_klasy).wrap());
            });
        }

        ui.add_space(4.0);
        ui.strong(format!("Strona {nr}"));
        match wynik.strona(nr) {
            Some(s) => {
                ui.label(format!(
                    "typ: {} · obrót: {} · jakość: {}",
                    s.typ,
                    s.obrot_stopnie.map(|o| format!("{o}°")).unwrap_or_else(|| "—".into()),
                    s.jakosc
                ));
                let pod = wpis.ocena_auto.as_ref().and_then(|o| o.podobienstwo(nr));
                ui.label(format!(
                    "Podobieństwo do próbki: {}",
                    pod.map(|p| format!("{:.0}%", p * 100.0)).unwrap_or_else(|| "—".into())
                ));
                ui.label("transkrypcja_poczatku:");
                wspolne::tekst_przewijany(ui, ("transkrypcja", &m.id), &s.transkrypcja_poczatku, 100.0);
                ui.label("Problemy strony:");
                wspolne::lista_problemow(ui, przebieg, &s.problemy);
            }
            None => {
                ui.weak("Model nie opisał tej strony.");
            }
        }
        ui.add_space(4.0);
        ui.strong("Problemy dokumentu");
        wspolne::lista_problemow(ui, przebieg, &wynik.problemy_dokumentu);

        if let Some(o) = &wpis.ocena_auto
            && !dok.wstrzykniete.is_empty()
        {
            ui.add_space(4.0);
            ui.label(format!("Wykryte wstrzyknięte: {}", lista_lub_kreska(&o.wykryte_wstrzykniete)));
            ui.label(format!("Pominięte wstrzyknięte: {}", lista_lub_kreska(&o.pominiete_wstrzykniete)));
        }
    });
}

fn lista_lub_kreska(v: &[String]) -> String {
    if v.is_empty() { "—".into() } else { v.join(", ") }
}
