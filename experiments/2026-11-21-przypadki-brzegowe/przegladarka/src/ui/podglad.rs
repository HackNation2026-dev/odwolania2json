//! Środkowy panel: podgląd obrazu strony, nawigacja i zoom.

use egui::{RichText, Vec2};

use super::{Sesja, Zoom, wspolne};
use crate::dane;

const ZOOM_MIN: f32 = 0.1;
const ZOOM_MAX: f32 = 8.0;

/// Mnoży bieżące powiększenie; z trybu „dopasuj” startuje od ostatniej skali dopasowania.
pub fn powieksz(sesja: &mut Sesja, mnoznik: f32) {
    let baza = match sesja.zoom {
        Zoom::Skala(s) => s,
        Zoom::Dopasuj => sesja.skala_dopasowania,
    };
    sesja.zoom = Zoom::Skala((baza * mnoznik).clamp(ZOOM_MIN, ZOOM_MAX));
}

pub fn panel(sesja: &mut Sesja, ui: &mut egui::Ui) {
    let n = sesja.liczba_stron();
    // Pasek zawija się, żeby nie poszerzał panelu (to psułoby „dopasuj”).
    ui.horizontal_wrapped(|ui| {
        if ui.add_enabled(sesja.strona > 0, egui::Button::new("◀ Poprzednia")).clicked() {
            sesja.przesun_strone(-1);
        }
        ui.label(format!("Strona {} / {}", if n == 0 { 0 } else { sesja.strona + 1 }, n));
        if ui.add_enabled(sesja.strona + 1 < n, egui::Button::new("Następna ▶")).clicked() {
            sesja.przesun_strone(1);
        }
        ui.separator();
        if ui.selectable_label(sesja.zoom == Zoom::Dopasuj, "Dopasuj").clicked() {
            sesja.zoom = Zoom::Dopasuj;
        }
        if ui.selectable_label(sesja.zoom == Zoom::Skala(1.0), "100%").clicked() {
            sesja.zoom = Zoom::Skala(1.0);
        }
        if ui.button("−").clicked() {
            powieksz(sesja, 1.0 / 1.25);
        }
        if ui.button("+").clicked() {
            powieksz(sesja, 1.25);
        }
        let skala = match sesja.zoom {
            Zoom::Skala(s) => s,
            Zoom::Dopasuj => sesja.skala_dopasowania,
        };
        ui.weak(format!("{:.0}%", skala * 100.0));
    });
    ui.separator();

    let id_dok = sesja.przebieg.pozycje.get(sesja.wybrany).map(|p| p.wpis.id.clone()).unwrap_or_default();
    if let Some(Err(e)) = sesja.przebieg.pozycje.get(sesja.wybrany).map(|p| &p.dokument) {
        ui.colored_label(wspolne::KOLOR_ZLE, format!("Nie udało się wczytać dokumentu {id_dok}:\n{e}"));
        return;
    }
    let Some(strona) = sesja.biezaca_strona() else {
        ui.weak("Dokument nie ma stron.");
        return;
    };
    if strona.obraz.is_empty() {
        ui.colored_label(wspolne::KOLOR_ZLE, "Brak ścieżki obrazu dla tej strony.");
        return;
    }
    let sciezka = dane::sciezka_wzgledna(&sesja.przebieg.katalog, &strona.obraz);
    let ctx = ui.ctx().clone();
    let tekstura = match sesja.obrazy.pobierz(&ctx, &sciezka) {
        Ok(t) => t,
        Err(e) => {
            ui.colored_label(wspolne::KOLOR_ZLE, RichText::new(format!("Brak obrazu: {e}")));
            return;
        }
    };

    let rozmiar_obrazu = tekstura.size_vec2();
    // Odejmujemy miejsce na paski przewijania, żeby dopasowany obraz ich nie wymuszał.
    let dostepne = ui.available_size() - egui::vec2(12.0, 12.0);
    let skala = match sesja.zoom {
        Zoom::Skala(s) => s,
        Zoom::Dopasuj => {
            let s = (dostepne.x / rozmiar_obrazu.x).min(dostepne.y / rozmiar_obrazu.y).clamp(ZOOM_MIN, ZOOM_MAX);
            sesja.skala_dopasowania = s;
            s
        }
    };
    let rozmiar: Vec2 = rozmiar_obrazu * skala;
    egui::ScrollArea::both().id_salt(("podglad", id_dok, sesja.strona)).auto_shrink(false).show(ui, |ui| {
        ui.add(egui::Image::from_texture((tekstura.id(), rozmiar)).fit_to_exact_size(rozmiar));
    });
}
