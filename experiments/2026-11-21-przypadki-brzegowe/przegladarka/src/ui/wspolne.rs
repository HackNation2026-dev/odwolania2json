//! Drobne elementy UI używane w kilku zakładkach.

use egui::{Color32, RichText, Ui};

use crate::dane::Przebieg;
use crate::model::Problem;

pub const KOLOR_UWAGA: Color32 = Color32::from_rgb(230, 160, 40);
pub const KOLOR_OK: Color32 = Color32::from_rgb(80, 180, 90);
pub const KOLOR_ZLE: Color32 = Color32::from_rgb(220, 80, 70);

pub fn kolor_statusu(status: &str) -> Color32 {
    match status {
        "nieprzejrzany" => Color32::from_gray(140),
        "w_toku" => KOLOR_UWAGA,
        "przejrzany" => KOLOR_OK,
        "do_dyskusji" => Color32::from_rgb(150, 110, 230),
        _ => KOLOR_ZLE,
    }
}

pub fn znacznik_statusu(ui: &mut Ui, status: &str) {
    ui.label(RichText::new("●").color(kolor_statusu(status))).on_hover_text(status);
}

pub fn kolor_wagi(waga: &str) -> Color32 {
    match waga {
        "niska" => Color32::from_rgb(120, 160, 200),
        "srednia" => KOLOR_UWAGA,
        "wysoka" => KOLOR_ZLE,
        _ => Color32::from_gray(150),
    }
}

pub fn tak_nie(ok: Option<bool>) -> RichText {
    match ok {
        Some(true) => RichText::new("✓").color(KOLOR_OK).strong(),
        Some(false) => RichText::new("✗").color(KOLOR_ZLE).strong(),
        None => RichText::new("–").weak(),
    }
}

pub fn opcja<T: std::fmt::Display>(v: &Option<T>) -> String {
    v.as_ref().map(|x| x.to_string()).unwrap_or_else(|| "—".into())
}

/// Kod problemu: z podpowiedzią z taksonomii albo oznaczeniem „spoza taksonomii”.
pub fn kod_problemu(ui: &mut Ui, przebieg: &Przebieg, kod: &str) {
    match przebieg.manifest.taksonomia.iter().find(|t| t.kod == kod) {
        Some(t) => {
            ui.label(RichText::new(kod).monospace()).on_hover_text(format!("{}\n{}", t.nazwa, t.opis));
        }
        None => {
            ui.label(RichText::new(kod).monospace().italics())
                .on_hover_text("Kod spoza taksonomii");
        }
    }
}

/// Lista problemów tylko do odczytu.
pub fn lista_problemow(ui: &mut Ui, przebieg: &Przebieg, problemy: &[Problem]) {
    if problemy.is_empty() {
        ui.weak("(brak)");
        return;
    }
    for p in problemy {
        ui.horizontal_wrapped(|ui| {
            ui.label(RichText::new(format!("[{}]", p.waga)).color(kolor_wagi(&p.waga)));
            kod_problemu(ui, przebieg, &p.kod);
            ui.label(&p.opis);
        });
    }
}

/// Tekst w ramce z przewijaniem (np. próbka tekstu, transkrypcja).
pub fn tekst_przewijany(ui: &mut Ui, id: impl egui::AsIdSalt, tekst: &str, wysokosc: f32) {
    egui::Frame::group(ui.style()).show(ui, |ui| {
        egui::ScrollArea::vertical().id_salt(id).max_height(wysokosc).auto_shrink([false, true]).show(ui, |ui| {
            if tekst.is_empty() {
                ui.weak("(pusto)");
            } else {
                ui.add(egui::Label::new(RichText::new(tekst).monospace()).wrap());
            }
        });
    });
}
