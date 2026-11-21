//! Interfejs: aplikacja eframe, sesja przeglądania, skróty klawiszowe.

mod adnotacja;
mod lista;
mod modele;
mod podglad;
mod podsumowanie;
mod strona;
mod wspolne;

use std::collections::BTreeSet;
use std::path::PathBuf;

use egui::{Key, Modifiers};

use crate::dane::{self, Przebieg, StanAdnotacji};
use crate::model::{Adnotacja, Dokument, StronaDokumentu};
use crate::obrazy::PamiecObrazow;

const KLUCZ_RECENZENT: &str = "recenzent";

pub struct Aplikacja {
    recenzent: String,
    ekran: Ekran,
}

enum Ekran {
    Start { sciezka: String, blad: Option<String> },
    Przegladanie(Box<Sesja>),
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Widok {
    Przeglad,
    Podsumowanie,
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Zakladka {
    Strona,
    Modele,
    Adnotacja,
}

#[derive(Clone, Copy, PartialEq)]
pub enum Zoom {
    Dopasuj,
    Skala(f32),
}

#[derive(Default)]
pub struct Filtry {
    pub zrodlo: Option<String>,
    pub status: Option<String>,
    pub tylko_przeslane: bool,
    pub tylko_rozbieznosc: bool,
    pub szukaj: String,
}

/// Formularz dodawania problemu (kod + waga + opis).
pub struct NowyProblem {
    pub kod: String,
    pub waga: String,
    pub opis: String,
}

impl Default for NowyProblem {
    fn default() -> Self {
        NowyProblem { kod: String::new(), waga: "srednia".into(), opis: String::new() }
    }
}

pub struct Sesja {
    pub przebieg: Przebieg,
    pub wybrany: usize,
    /// Indeks strony w `dokument.strony` (od 0).
    pub strona: usize,
    /// Indeksy dokumentów z niezapisanymi zmianami adnotacji.
    pub niezapisane: BTreeSet<usize>,
    pub komunikat: Option<(String, bool)>,
    pub filtry: Filtry,
    pub zoom: Zoom,
    /// Skala wyliczona ostatnio w trybie „dopasuj” (punkt startowy dla +/−).
    pub skala_dopasowania: f32,
    pub zakladka: Zakladka,
    pub widok: Widok,
    pub obrazy: PamiecObrazow,
    pub nowy_dok: NowyProblem,
    pub nowy_str: NowyProblem,
    pub przewin_liste: bool,
}

impl Sesja {
    fn nowa(przebieg: Przebieg) -> Self {
        Sesja {
            przebieg,
            wybrany: 0,
            strona: 0,
            niezapisane: BTreeSet::new(),
            komunikat: None,
            filtry: Filtry::default(),
            zoom: Zoom::Dopasuj,
            skala_dopasowania: 1.0,
            zakladka: Zakladka::Strona,
            widok: Widok::Przeglad,
            obrazy: PamiecObrazow::default(),
            nowy_dok: NowyProblem::default(),
            nowy_str: NowyProblem::default(),
            przewin_liste: true,
        }
    }

    pub fn dokument(&self) -> Option<&Dokument> {
        self.przebieg.pozycje.get(self.wybrany).and_then(|p| p.dokument.as_ref().ok())
    }

    pub fn liczba_stron(&self) -> usize {
        self.dokument().map(|d| d.strony.len()).unwrap_or(0)
    }

    pub fn biezaca_strona(&self) -> Option<&StronaDokumentu> {
        self.dokument().and_then(|d| d.strony.get(self.strona))
    }

    /// Numer bieżącej strony (od 1), zgodny z polem `nr`.
    pub fn nr_strony(&self) -> u32 {
        self.biezaca_strona().map(|s| s.nr).unwrap_or(self.strona as u32 + 1)
    }

    /// Indeksy dokumentów spełniających filtry, w kolejności manifestu.
    pub fn widoczne(&self) -> Vec<usize> {
        let f = &self.filtry;
        let szukaj = f.szukaj.trim().to_lowercase();
        self.przebieg
            .pozycje
            .iter()
            .enumerate()
            .filter(|(_, p)| f.zrodlo.as_ref().is_none_or(|z| &p.wpis.zrodlo == z))
            .filter(|(_, p)| f.status.as_ref().is_none_or(|s| p.adnotacja.status() == s))
            .filter(|(_, p)| !f.tylko_przeslane || p.wpis.przeslany_do_modeli)
            .filter(|(_, p)| !f.tylko_rozbieznosc || p.rozbieznosc)
            .filter(|(_, p)| szukaj.is_empty() || p.wpis.id.to_lowercase().contains(&szukaj))
            .map(|(i, _)| i)
            .collect()
    }

    pub fn zapisz(&mut self, indeks: usize, recenzent: &str) {
        if !self.niezapisane.contains(&indeks) {
            return;
        }
        let modele = self.przebieg.manifest.modele.clone();
        let Some(poz) = self.przebieg.pozycje.get_mut(indeks) else { return };
        let StanAdnotacji::Jest(a) = &mut poz.adnotacja else { return };
        a.przygotuj_do_zapisu(recenzent, &modele, dane::teraz_iso());
        match dane::zapisz_adnotacje(&self.przebieg.katalog, a) {
            Ok(()) => {
                self.niezapisane.remove(&indeks);
                self.komunikat = Some((format!("Zapisano adnotację {}", a.id), false));
            }
            Err(e) => self.komunikat = Some((format!("Błąd zapisu: {e}"), true)),
        }
    }

    pub fn zapisz_wszystko(&mut self, recenzent: &str) {
        for i in self.niezapisane.clone() {
            self.zapisz(i, recenzent);
        }
    }

    /// Zmienia dokument; wcześniej automatycznie zapisuje zmiany bieżącego.
    pub fn wybierz(&mut self, indeks: usize, recenzent: &str) {
        if indeks == self.wybrany || indeks >= self.przebieg.pozycje.len() {
            return;
        }
        self.zapisz(self.wybrany, recenzent);
        self.wybrany = indeks;
        self.strona = 0;
        self.przewin_liste = true;
    }

    /// Przejście o `krok` w liście widocznych (przefiltrowanych) dokumentów.
    pub fn przesun_dokument(&mut self, krok: isize, recenzent: &str) {
        let widoczne = self.widoczne();
        if widoczne.is_empty() {
            return;
        }
        let nowy = match widoczne.iter().position(|&i| i == self.wybrany) {
            Some(p) => (p as isize + krok).clamp(0, widoczne.len() as isize - 1) as usize,
            None => 0,
        };
        self.wybierz(widoczne[nowy], recenzent);
    }

    pub fn przesun_strone(&mut self, krok: isize) {
        let n = self.liczba_stron();
        if n > 0 {
            self.strona = (self.strona as isize + krok).clamp(0, n as isize - 1) as usize;
        }
    }

    /// Zastępuje adnotację bieżącego dokumentu wersją edytowaną w UI.
    pub fn ustaw_adnotacje(&mut self, a: Adnotacja) {
        if let Some(poz) = self.przebieg.pozycje.get_mut(self.wybrany) {
            poz.adnotacja = StanAdnotacji::Jest(Box::new(a));
            self.niezapisane.insert(self.wybrany);
        }
    }

    fn eksportuj(&mut self, recenzent: &str) {
        self.zapisz_wszystko(recenzent);
        self.komunikat = Some(match dane::eksportuj_csv(&self.przebieg) {
            Ok(p) => (format!("Wyeksportowano: {}", p.display()), false),
            Err(e) => (format!("Błąd eksportu: {e}"), true),
        });
    }
}

impl Aplikacja {
    pub fn new(cc: &eframe::CreationContext<'_>, katalog: Option<PathBuf>) -> Self {
        let recenzent = cc
            .storage
            .and_then(|s| eframe::get_value::<String>(s, KLUCZ_RECENZENT))
            .unwrap_or_default();
        let mut app = Aplikacja { recenzent, ekran: Ekran::Start { sciezka: String::new(), blad: None } };
        match katalog {
            Some(k) => app.otworz(k),
            None => {
                let najnowszy = dane::domyslny_katalog_wynikow().iter().find_map(|w| dane::najnowszy_przebieg(w));
                match najnowszy {
                    Some(k) => app.otworz(k),
                    None => {
                        app.ekran = Ekran::Start {
                            sciezka: String::new(),
                            blad: Some("Nie znaleziono przebiegu w ../wyniki/. Podaj ścieżkę.".into()),
                        }
                    }
                }
            }
        }
        app
    }

    fn otworz(&mut self, katalog: PathBuf) {
        self.ekran = match Przebieg::wczytaj(&katalog) {
            Ok(p) => Ekran::Przegladanie(Box::new(Sesja::nowa(p))),
            Err(e) => Ekran::Start { sciezka: katalog.display().to_string(), blad: Some(e) },
        };
    }

    fn ekran_startowy(&mut self, ui: &mut egui::Ui) {
        let mut do_otwarcia = None;
        egui::CentralPanel::default().show(ui, |ui| {
            let Ekran::Start { sciezka, blad } = &mut self.ekran else { return };
            ui.heading("Przeglądarka przypadków brzegowych");
            ui.add_space(8.0);
            ui.label("Katalog przebiegu (zawierający manifest.json):");
            let odp = ui.add(egui::TextEdit::singleline(sciezka).desired_width(600.0));
            let enter = odp.lost_focus() && ui.input(|i| i.key_pressed(Key::Enter));
            if ui.button("Otwórz").clicked() || enter {
                do_otwarcia = Some(PathBuf::from(sciezka.trim()));
            }
            if let Some(b) = blad {
                ui.add_space(8.0);
                ui.colored_label(ui.visuals().error_fg_color, b.as_str());
            }
        });
        if let Some(k) = do_otwarcia {
            self.otworz(k);
        }
    }

    fn skroty(sesja: &mut Sesja, ctx: &egui::Context, recenzent: &str) {
        if ctx.input_mut(|i| i.consume_key(Modifiers::COMMAND, Key::S)) {
            sesja.zapisz(sesja.wybrany, recenzent);
        }
        // Klawisze funkcyjne działają także podczas pisania w polach tekstowych.
        let fkey = |k: Key| ctx.input_mut(|i| i.consume_key(Modifiers::NONE, k));
        for (k, z) in [(Key::F1, Zakladka::Strona), (Key::F2, Zakladka::Modele), (Key::F3, Zakladka::Adnotacja)] {
            if fkey(k) {
                sesja.widok = Widok::Przeglad;
                sesja.zakladka = z;
            }
        }
        if fkey(Key::F4) {
            sesja.widok = if sesja.widok == Widok::Przeglad { Widok::Podsumowanie } else { Widok::Przeglad };
        }
        if ctx.egui_wants_keyboard_input() || sesja.widok != Widok::Przeglad {
            return;
        }
        let wcisniete = |k: Key| ctx.input_mut(|i| i.consume_key(Modifiers::NONE, k));
        if wcisniete(Key::ArrowLeft) {
            sesja.przesun_strone(-1);
        }
        if wcisniete(Key::ArrowRight) {
            sesja.przesun_strone(1);
        }
        if wcisniete(Key::ArrowUp) || wcisniete(Key::PageUp) {
            sesja.przesun_dokument(-1, recenzent);
        }
        if wcisniete(Key::ArrowDown) || wcisniete(Key::PageDown) {
            sesja.przesun_dokument(1, recenzent);
        }
        if ctx.input_mut(|i| i.consume_key(Modifiers::NONE, Key::Plus) || i.consume_key(Modifiers::NONE, Key::Equals)) {
            podglad::powieksz(sesja, 1.25);
        }
        if wcisniete(Key::Minus) {
            podglad::powieksz(sesja, 1.0 / 1.25);
        }
    }

    fn gorny_pasek(sesja: &mut Sesja, ui: &mut egui::Ui, recenzent: &str) -> bool {
        let mut zmien_przebieg = false;
        egui::Panel::top("gorny_pasek").show(ui, |ui| {
            egui::MenuBar::new().ui(ui, |ui| {
                ui.selectable_value(&mut sesja.widok, Widok::Przeglad, "Przegląd");
                ui.selectable_value(&mut sesja.widok, Widok::Podsumowanie, "Podsumowanie");
                ui.separator();
                if ui.button("Zmień przebieg…").clicked() {
                    zmien_przebieg = true;
                }
                ui.separator();
                let m = &sesja.przebieg.manifest;
                ui.label(format!("Przebieg: {}", if m.przebieg.is_empty() { "?" } else { &m.przebieg }))
                    .on_hover_text(format!("{}\n{}\n{}", sesja.przebieg.katalog.display(), m.utworzono, m.opis));
                if !sesja.niezapisane.is_empty() {
                    ui.separator();
                    ui.colored_label(wspolne::KOLOR_UWAGA, format!("● niezapisane: {}", sesja.niezapisane.len()));
                    if ui.button("Zapisz wszystko").clicked() {
                        sesja.zapisz_wszystko(recenzent);
                    }
                }
            });
        });
        zmien_przebieg
    }

    fn dolny_pasek(sesja: &mut Sesja, ui: &mut egui::Ui) {
        egui::Panel::bottom("dolny_pasek").show(ui, |ui| {
            ui.horizontal(|ui| {
                match &sesja.komunikat {
                    Some((t, true)) => {
                        ui.colored_label(ui.visuals().error_fg_color, t);
                    }
                    Some((t, false)) => {
                        ui.label(t);
                    }
                    None => {
                        ui.weak("←/→ strona · ↑/↓ PgUp/PgDn dokument · +/− zoom · F1–F3 zakładki · F4 podsumowanie · Ctrl+S zapis");
                    }
                }
                if sesja.komunikat.is_some() && ui.small_button("✖").clicked() {
                    sesja.komunikat = None;
                }
            });
        });
    }
}

impl eframe::App for Aplikacja {
    fn ui(&mut self, ui: &mut egui::Ui, _frame: &mut eframe::Frame) {
        if matches!(self.ekran, Ekran::Start { .. }) {
            self.ekran_startowy(ui);
            return;
        }
        let recenzent = self.recenzent.clone();
        let Ekran::Przegladanie(sesja) = &mut self.ekran else { return };
        let ctx = ui.ctx().clone();
        Self::skroty(sesja, &ctx, &recenzent);
        // Zamknięcie okna: zapisz wszystko, co zmienione.
        if ctx.input(|i| i.viewport().close_requested()) {
            sesja.zapisz_wszystko(&recenzent);
        }

        let zmien = Self::gorny_pasek(sesja, ui, &recenzent);
        Self::dolny_pasek(sesja, ui);
        match sesja.widok {
            Widok::Przeglad => {
                lista::panel(sesja, ui, &recenzent);
                egui::Panel::right("prawy_panel").resizable(true).default_size(480.0).min_size(320.0).show(ui, |ui| {
                    ui.horizontal(|ui| {
                        ui.selectable_value(&mut sesja.zakladka, Zakladka::Strona, "Strona");
                        ui.selectable_value(&mut sesja.zakladka, Zakladka::Modele, "Modele");
                        let tytul = if sesja.niezapisane.contains(&sesja.wybrany) { "Adnotacja ●" } else { "Adnotacja" };
                        ui.selectable_value(&mut sesja.zakladka, Zakladka::Adnotacja, tytul);
                    });
                    ui.separator();
                    match sesja.zakladka {
                        Zakladka::Strona => strona::zakladka(sesja, ui),
                        Zakladka::Modele => modele::zakladka(sesja, ui),
                        Zakladka::Adnotacja => adnotacja::zakladka(sesja, ui, &mut self.recenzent),
                    }
                });
                egui::CentralPanel::default().show(ui, |ui| podglad::panel(sesja, ui));
            }
            Widok::Podsumowanie => {
                let mut eksport = false;
                egui::CentralPanel::default().show(ui, |ui| eksport = podsumowanie::widok(sesja, ui));
                if eksport {
                    sesja.eksportuj(&recenzent);
                }
            }
        }
        if zmien {
            sesja.zapisz_wszystko(&recenzent);
            let sciezka = sesja.przebieg.katalog.display().to_string();
            self.ekran = Ekran::Start { sciezka, blad: None };
        }
    }

    fn save(&mut self, storage: &mut dyn eframe::Storage) {
        eframe::set_value(storage, KLUCZ_RECENZENT, &self.recenzent);
        if let Ekran::Przegladanie(sesja) = &mut self.ekran {
            let recenzent = self.recenzent.clone();
            sesja.zapisz_wszystko(&recenzent);
        }
    }
}
