//! Zakładka „Adnotacja”: edycja oceny człowieka.
//!
//! Edytujemy kopię adnotacji; jeśli po narysowaniu UI różni się od oryginału,
//! zapisujemy ją w sesji i oznaczamy jako niezapisaną.

use egui::RichText;

use super::{NowyProblem, Sesja, wspolne};
use crate::dane::{Przebieg, StanAdnotacji};
use crate::model::{Adnotacja, KLASY_CZLOWIEKA, OCENY_MODELI, Problem, STATUSY, WAGI};

pub fn zakladka(sesja: &mut Sesja, ui: &mut egui::Ui, recenzent: &mut String) {
    let Some(poz) = sesja.przebieg.pozycje.get(sesja.wybrany) else { return };
    let oryginal = match &poz.adnotacja {
        StanAdnotacji::Jest(a) => a.as_ref().clone(),
        StanAdnotacji::Brak => Adnotacja::nowa(&poz.wpis.id),
        StanAdnotacji::Blad(e) => {
            ui.colored_label(wspolne::KOLOR_ZLE, "Nie da się odczytać pliku adnotacji (edycja wyłączona, plik nie zostanie nadpisany):");
            ui.colored_label(wspolne::KOLOR_ZLE, e);
            return;
        }
    };
    let mut a = oryginal.clone();
    let nr = sesja.nr_strony();
    let mut zapisz = false;

    egui::ScrollArea::vertical().id_salt("zakladka_adnotacja").show(ui, |ui| {
        ui.horizontal(|ui| {
            ui.label("Recenzent:");
            ui.add(egui::TextEdit::singleline(recenzent).desired_width(160.0).hint_text("imię / inicjały"));
        });
        if recenzent.trim().is_empty() {
            ui.colored_label(wspolne::KOLOR_UWAGA, "Podaj recenzenta – zostanie zapisany w adnotacji.");
        }
        ui.horizontal(|ui| {
            let niezapisane = sesja.niezapisane.contains(&sesja.wybrany);
            if ui.add_enabled(niezapisane, egui::Button::new("Zapisz (Ctrl+S)")).clicked() {
                zapisz = true;
            }
            if niezapisane {
                ui.colored_label(wspolne::KOLOR_UWAGA, "● niezapisane zmiany");
            } else if !a.zmieniono.is_empty() {
                ui.weak(format!("zapisano: {} ({})", a.zmieniono, a.recenzent));
            }
        });
        ui.separator();

        egui::Grid::new("adn_naglowek").num_columns(2).show(ui, |ui| {
            ui.label("Status:");
            egui::ComboBox::from_id_salt("adn_status").selected_text(a.status.clone()).show_ui(ui, |ui| {
                for s in STATUSY {
                    ui.selectable_value(&mut a.status, s.to_string(), s);
                }
            });
            ui.end_row();
            ui.label("Klasa (człowiek):");
            egui::ComboBox::from_id_salt("adn_klasa")
                .selected_text(a.klasa.clone().unwrap_or_else(|| "(nie oceniono)".into()))
                .show_ui(ui, |ui| {
                    ui.selectable_value(&mut a.klasa, None, "(nie oceniono)");
                    for k in KLASY_CZLOWIEKA {
                        ui.selectable_value(&mut a.klasa, Some(k.to_string()), k);
                    }
                });
            ui.end_row();
        });

        ui.add_space(6.0);
        ui.strong("Problemy dokumentu");
        edytor_problemow(ui, &sesja.przebieg, "dok", &mut a.problemy_dokumentu, &mut sesja.nowy_dok);

        ui.add_space(6.0);
        ui.strong(format!("Problemy strony {nr}"));
        {
            let mut problemy = a.strona(nr).map(|s| s.problemy.clone()).unwrap_or_default();
            let przed = problemy.clone();
            edytor_problemow(ui, &sesja.przebieg, "str", &mut problemy, &mut sesja.nowy_str);
            if problemy != przed {
                a.strona_mut(nr).problemy = problemy;
            }
        }
        ui.label(format!("Notatka strony {nr}:"));
        {
            let mut notatka = a.strona(nr).map(|s| s.notatka.clone()).unwrap_or_default();
            if ui.add(egui::TextEdit::multiline(&mut notatka).desired_rows(2).desired_width(f32::INFINITY)).changed() {
                a.strona_mut(nr).notatka = notatka;
            }
        }
        let inne_strony: Vec<String> = a
            .strony
            .iter()
            .filter(|s| s.nr != nr && (!s.problemy.is_empty() || !s.notatka.is_empty()))
            .map(|s| format!("{} ({})", s.nr, s.problemy.len()))
            .collect();
        if !inne_strony.is_empty() {
            ui.weak(format!("Inne strony z adnotacją (nr (problemy)): {}", inne_strony.join(", ")));
        }

        ui.add_space(6.0);
        ui.label("Notatka dokumentu:");
        ui.add(egui::TextEdit::multiline(&mut a.notatka).desired_rows(3).desired_width(f32::INFINITY));

        ui.add_space(6.0);
        ui.separator();
        ui.strong("Ocena modeli");
        let dok = sesja.przebieg.pozycje[sesja.wybrany].dokument.as_ref().ok();
        egui::Grid::new("ocena_modeli").num_columns(2).show(ui, |ui| {
            for m in &sesja.przebieg.manifest.modele {
                ui.label(&m.nazwa);
                ui.horizontal(|ui| {
                    let mut ocena = a.ocena_modeli.get(&m.id).cloned().unwrap_or_else(|| "brak_oceny".into());
                    let przed = ocena.clone();
                    for o in OCENY_MODELI {
                        ui.radio_value(&mut ocena, o.to_string(), o);
                    }
                    if ocena != przed {
                        a.ocena_modeli.insert(m.id.clone(), ocena);
                    }
                });
                ui.end_row();
            }
        });

        ui.add_space(6.0);
        ui.horizontal_wrapped(|ui| {
            for m in &sesja.przebieg.manifest.modele {
                let wynik = dok.and_then(|d| d.modele.get(&m.id)).and_then(|w| w.wynik_ok());
                let odp = ui
                    .add_enabled(wynik.is_some(), egui::Button::new(format!("Przejmij problemy z modelu {}", m.nazwa)))
                    .on_hover_text("Dopisuje problemy dokumentu i stron z odpowiedzi modelu (bez duplikatów)");
                if odp.clicked()
                    && let Some(w) = wynik
                {
                    a.przejmij_z_modelu(w);
                }
            }
        });
        if !a.inne.is_empty() {
            ui.weak(format!("Dodatkowe pola w pliku (zachowane): {}", a.inne.keys().cloned().collect::<Vec<_>>().join(", ")));
        }
    });

    if let Some(a) = Adnotacja::po_edycji(&oryginal, a) {
        sesja.ustaw_adnotacje(a);
    }
    if zapisz {
        sesja.zapisz(sesja.wybrany, recenzent);
    }
}

fn combo_wagi(ui: &mut egui::Ui, id: impl egui::AsIdSalt, waga: &mut String) {
    egui::ComboBox::from_id_salt(id)
        .width(80.0)
        .selected_text(RichText::new(waga.as_str()).color(wspolne::kolor_wagi(waga)))
        .show_ui(ui, |ui| {
            for w in WAGI {
                ui.selectable_value(waga, w.to_string(), w);
            }
        });
}

fn edytor_problemow(ui: &mut egui::Ui, przebieg: &Przebieg, id: &str, problemy: &mut Vec<Problem>, nowy: &mut NowyProblem) {
    ui.push_id(id, |ui| {
        let mut do_usuniecia = None;
        if problemy.is_empty() {
            ui.weak("(brak)");
        }
        for (i, p) in problemy.iter_mut().enumerate() {
            ui.horizontal(|ui| {
                if ui.small_button("✖").on_hover_text("Usuń").clicked() {
                    do_usuniecia = Some(i);
                }
                wspolne::kod_problemu(ui, przebieg, &p.kod);
                combo_wagi(ui, ("waga", i), &mut p.waga);
                ui.add(egui::TextEdit::singleline(&mut p.opis).desired_width(f32::INFINITY).hint_text("opis"));
            });
        }
        if let Some(i) = do_usuniecia {
            problemy.remove(i);
        }

        ui.horizontal(|ui| {
            let tekst = if nowy.kod.is_empty() { "wybierz kod…".to_string() } else { nowy.kod.clone() };
            egui::ComboBox::from_id_salt("nowy_kod").width(180.0).selected_text(tekst).show_ui(ui, |ui| {
                for t in &przebieg.manifest.taksonomia {
                    ui.selectable_value(&mut nowy.kod, t.kod.clone(), format!("{} — {}", t.kod, t.nazwa))
                        .on_hover_text(&t.opis);
                }
            });
            combo_wagi(ui, "nowa_waga", &mut nowy.waga);
        });
        ui.horizontal(|ui| {
            let odp = ui.add(egui::TextEdit::singleline(&mut nowy.opis).desired_width(ui.available_width() - 70.0).hint_text("opis problemu"));
            let enter = odp.lost_focus() && ui.input(|i| i.key_pressed(egui::Key::Enter));
            if ui.add_enabled(!nowy.kod.is_empty(), egui::Button::new("Dodaj")).clicked() || (enter && !nowy.kod.is_empty()) {
                problemy.push(Problem { kod: nowy.kod.clone(), opis: nowy.opis.trim().to_string(), waga: nowy.waga.clone() });
                nowy.opis.clear();
            }
        });
    });
}
