//! Lewy panel: filtry i lista dokumentów.

use egui::{RichText, Sense};
use egui_extras::{Column, TableBuilder};

use super::{Sesja, wspolne};
use crate::model::STATUSY;

const ZRODLA: [&str; 4] = ["pozytywny", "negatywny", "szablon", "syntetyczny"];

fn combo_opcji(ui: &mut egui::Ui, id: &str, etykieta: &str, wartosc: &mut Option<String>, opcje: &[&str]) {
    ui.horizontal(|ui| {
        ui.label(etykieta);
        egui::ComboBox::from_id_salt(id)
            .selected_text(wartosc.clone().unwrap_or_else(|| "wszystkie".into()))
            .show_ui(ui, |ui| {
                ui.selectable_value(wartosc, None, "wszystkie");
                for o in opcje {
                    ui.selectable_value(wartosc, Some(o.to_string()), *o);
                }
            });
    });
}

pub fn panel(sesja: &mut Sesja, ui: &mut egui::Ui, recenzent: &str) {
    egui::Panel::left("lista_dokumentow").resizable(true).default_size(380.0).min_size(260.0).show(ui, |ui| {
        ui.heading("Dokumenty");
        let f = &mut sesja.filtry;
        ui.horizontal(|ui| {
            ui.label("Szukaj id:");
            ui.add(egui::TextEdit::singleline(&mut f.szukaj).desired_width(160.0));
        });
        combo_opcji(ui, "filtr_zrodlo", "Źródło:", &mut f.zrodlo, &ZRODLA);
        let mut statusy: Vec<&str> = STATUSY.to_vec();
        statusy.push("blad");
        combo_opcji(ui, "filtr_status", "Status:", &mut f.status, &statusy);
        ui.checkbox(&mut f.tylko_przeslane, "tylko przesłane do modeli");
        ui.checkbox(&mut f.tylko_rozbieznosc, "tylko z rozbieżnością");

        let widoczne = sesja.widoczne();
        ui.weak(format!("Widoczne: {} z {}", widoczne.len(), sesja.przebieg.pozycje.len()));
        ui.separator();

        let mut klikniety = None;
        let mut tabela = TableBuilder::new(ui)
            .striped(true)
            .sense(Sense::click())
            .column(Column::exact(16.0))
            .column(Column::auto().at_least(90.0).clip(true).resizable(true))
            .column(Column::auto().at_least(60.0))
            .column(Column::auto().at_least(60.0))
            .column(Column::auto())
            .column(Column::auto())
            .column(Column::remainder().at_least(40.0));
        if sesja.przewin_liste
            && let Some(poz) = widoczne.iter().position(|&i| i == sesja.wybrany)
        {
            tabela = tabela.scroll_to_row(poz, Some(egui::Align::Center));
        }
        sesja.przewin_liste = false;
        tabela
            .header(20.0, |mut h| {
                for t in ["", "id", "źródło", "klasa ocz.", "typ", "str.", "rozb."] {
                    h.col(|ui| {
                        ui.strong(t);
                    });
                }
            })
            .body(|body| {
                body.rows(20.0, widoczne.len(), |mut row| {
                    let i = widoczne[row.index()];
                    let poz = &sesja.przebieg.pozycje[i];
                    row.set_selected(i == sesja.wybrany);
                    row.col(|ui| wspolne::znacznik_statusu(ui, poz.adnotacja.status()));
                    row.col(|ui| {
                        let mut t = RichText::new(&poz.wpis.id).monospace();
                        if poz.dokument.is_err() {
                            t = t.color(wspolne::KOLOR_ZLE);
                        }
                        let napis = if sesja.niezapisane.contains(&i) { "●" } else { "" };
                        let odp = ui.label(t);
                        if !napis.is_empty() {
                            ui.colored_label(wspolne::KOLOR_UWAGA, napis);
                        }
                        if let Err(e) = &poz.dokument {
                            odp.on_hover_text(e);
                        }
                    });
                    row.col(|ui| {
                        ui.label(&poz.wpis.zrodlo);
                    });
                    row.col(|ui| {
                        ui.label(wspolne::opcja(&poz.wpis.klasa_oczekiwana));
                    });
                    row.col(|ui| {
                        ui.label(&poz.wpis.typ_auto);
                    });
                    row.col(|ui| {
                        ui.label(poz.wpis.liczba_stron.to_string());
                    });
                    row.col(|ui| {
                        if poz.rozbieznosc {
                            ui.colored_label(wspolne::KOLOR_UWAGA, "⚠")
                                .on_hover_text("Modele wskazały różne klasy lub klasę inną niż oczekiwana");
                        }
                    });
                    if row.response().clicked() {
                        klikniety = Some(i);
                    }
                });
            });
        if let Some(i) = klikniety {
            sesja.wybierz(i, recenzent);
            sesja.przewin_liste = false;
        }
    });
}
