//! Zakładka „Strona”: metryki automatyczne strony i metadane dokumentu.

use super::{Sesja, wspolne};

pub fn zakladka(sesja: &mut Sesja, ui: &mut egui::Ui) {
    let Some(poz) = sesja.przebieg.pozycje.get(sesja.wybrany) else {
        ui.weak("Brak dokumentów w przebiegu.");
        return;
    };
    let dok = match &poz.dokument {
        Ok(d) => d,
        Err(e) => {
            ui.colored_label(wspolne::KOLOR_ZLE, e);
            return;
        }
    };
    egui::ScrollArea::vertical().id_salt("zakladka_strona").show(ui, |ui| {
        ui.heading(format!("Strona {} / {}", sesja.nr_strony(), dok.strony.len()));
        match dok.strony.get(sesja.strona) {
            Some(s) => {
                egui::Grid::new("metryki_strony").num_columns(2).striped(true).show(ui, |ui| {
                    let mut wiersz = |k: &str, v: String| {
                        ui.label(k);
                        ui.label(v);
                        ui.end_row();
                    };
                    wiersz("typ_auto", s.typ_auto.clone());
                    wiersz("znaki_tekstu", wspolne::opcja(&s.znaki_tekstu));
                    wiersz("obrazy", wspolne::opcja(&s.obrazy));
                    wiersz(
                        "pokrycie_obrazami",
                        s.pokrycie_obrazami.map(|p| format!("{:.0}%", p * 100.0)).unwrap_or_else(|| "—".into()),
                    );
                    wiersz("dpi_obrazow", s.dpi_obrazow.map(|d| format!("{d:.0}")).unwrap_or_else(|| "—".into()));
                    wiersz("obrot_pdf", wspolne::opcja(&s.obrot_pdf));
                    wiersz(
                        "rozmiar (pt)",
                        format!("{} × {}", wspolne::opcja(&s.szerokosc_pt), wspolne::opcja(&s.wysokosc_pt)),
                    );
                    wiersz("obraz", s.obraz.clone());
                });
                ui.add_space(6.0);
                ui.strong("probka_tekstu");
                wspolne::tekst_przewijany(ui, "probka_strona", &s.probka_tekstu, 220.0);
            }
            None => {
                ui.weak("Brak danych strony.");
            }
        }

        ui.add_space(10.0);
        ui.separator();
        ui.heading("Dokument");
        egui::Grid::new("metadane_dok").num_columns(2).striped(true).show(ui, |ui| {
            let mut wiersz = |k: &str, v: String| {
                ui.label(k);
                ui.add(egui::Label::new(v).wrap());
                ui.end_row();
            };
            wiersz("id", dok.id.clone());
            wiersz("plik_zrodlowy", dok.plik_zrodlowy.clone());
            wiersz("zrodlo", dok.zrodlo.clone());
            wiersz("klasa_oczekiwana", wspolne::opcja(&dok.klasa_oczekiwana));
            wiersz("sprawa", wspolne::opcja(&dok.sprawa));
            wiersz("typ_auto (manifest)", poz.wpis.typ_auto.clone());
            wiersz("przeslany_do_modeli", if poz.wpis.przeslany_do_modeli { "tak" } else { "nie" }.into());
            let m = &dok.metadane;
            wiersz("producent", wspolne::opcja(&m.producent));
            wiersz("kreator", wspolne::opcja(&m.kreator));
            wiersz(
                "rozmiar",
                m.rozmiar_bajtow.map(|b| format!("{:.1} KiB", b as f64 / 1024.0)).unwrap_or_else(|| "—".into()),
            );
            wiersz("zaszyfrowany", m.zaszyfrowany.map(|z| if z { "tak" } else { "nie" }).unwrap_or("—").into());
            wiersz("wersja_pdf", wspolne::opcja(&m.wersja_pdf));
        });
        if !dok.wstrzykniete.is_empty() {
            ui.add_space(6.0);
            ui.strong("Wstrzyknięte problemy");
            for w in &dok.wstrzykniete {
                ui.horizontal_wrapped(|ui| {
                    wspolne::kod_problemu(ui, &sesja.przebieg, &w.kod);
                    ui.label(format!("(str. {})", wspolne::opcja(&w.strona)));
                    ui.label(&w.opis);
                });
            }
        }
    });
}
