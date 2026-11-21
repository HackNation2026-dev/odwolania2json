//! Widok „Podsumowanie”: statystyki modeli i adnotacji, eksport CSV.

use egui::RichText;

use super::{Sesja, wspolne};
use crate::podsumowanie::policz;

/// Zwraca `true`, gdy kliknięto „Eksport CSV”.
pub fn widok(sesja: &mut Sesja, ui: &mut egui::Ui) -> bool {
    let p = policz(&sesja.przebieg);
    let mut eksport = false;
    egui::ScrollArea::vertical().id_salt("podsumowanie").show(ui, |ui| {
        ui.horizontal(|ui| {
            ui.heading("Podsumowanie przebiegu");
            if ui.button("Eksport CSV").on_hover_text("Zapisuje adnotacje_zbiorcze.csv w katalogu przebiegu").clicked() {
                eksport = true;
            }
        });
        ui.add_space(8.0);

        ui.strong("Modele");
        egui::Grid::new("pods_modele").striped(true).num_columns(4).show(ui, |ui| {
            for t in ["model", "trafność klasy", "śr. podobieństwo transkrypcji", "błędy"] {
                ui.label(RichText::new(t).strong());
            }
            ui.end_row();
            for m in &p.modele {
                ui.label(&m.nazwa);
                ui.label(match m.odsetek_klas() {
                    Some(o) => format!("{} / {} ({:.0}%)", m.trafione_klasy, m.ocenione_klasy, o * 100.0),
                    None => "—".into(),
                });
                ui.label(match m.srednie_podobienstwo {
                    Some(s) => format!("{:.1}% (n={})", s * 100.0, m.liczba_podobienstw),
                    None => "—".into(),
                });
                ui.label(m.bledy.to_string());
                ui.end_row();
            }
        });

        let mut kody: Vec<&String> = p.modele.iter().flat_map(|m| m.wstrzykniete.keys()).collect();
        kody.sort();
        kody.dedup();
        ui.add_space(10.0);
        ui.strong("Wykrycia wstrzykniętych problemów (wykryte / łącznie)");
        if kody.is_empty() {
            ui.weak("Brak dokumentów syntetycznych z wynikami modeli.");
        } else {
            egui::Grid::new("pods_wstrzykniete").striped(true).show(ui, |ui| {
                ui.label(RichText::new("kod").strong());
                for m in &p.modele {
                    ui.label(RichText::new(&m.nazwa).strong());
                }
                ui.end_row();
                for k in kody {
                    wspolne::kod_problemu(ui, &sesja.przebieg, k);
                    for m in &p.modele {
                        let (w, l) = m.wstrzykniete.get(k).copied().unwrap_or((0, 0));
                        ui.label(format!("{w} / {l}"));
                    }
                    ui.end_row();
                }
            });
        }

        ui.add_space(10.0);
        ui.strong("Dokumenty wg statusu adnotacji");
        egui::Grid::new("pods_statusy").striped(true).show(ui, |ui| {
            for (s, n) in &p.statusy {
                ui.horizontal(|ui| {
                    wspolne::znacznik_statusu(ui, s);
                    ui.label(s);
                });
                ui.label(n.to_string());
                ui.end_row();
            }
        });

        ui.add_space(10.0);
        ui.strong("Kody problemów nadane przez człowieka");
        if p.kody_czlowieka.is_empty() {
            ui.weak("Brak.");
        } else {
            let mut kody: Vec<(&String, &usize)> = p.kody_czlowieka.iter().collect();
            kody.sort_by(|a, b| b.1.cmp(a.1).then(a.0.cmp(b.0)));
            egui::Grid::new("pods_kody").striped(true).show(ui, |ui| {
                for (k, n) in kody {
                    wspolne::kod_problemu(ui, &sesja.przebieg, k);
                    ui.label(n.to_string());
                    ui.end_row();
                }
            });
        }
    });
    eksport
}
