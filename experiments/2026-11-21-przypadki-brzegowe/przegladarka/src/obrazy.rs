//! Leniwe ładowanie obrazów stron z małą pamięcią podręczną (LRU).
//!
//! Dekodujemy JPEG crate'em `image` i tworzymy teksturę przez
//! `Context::load_texture`. Trzymamy tylko kilka ostatnio oglądanych stron,
//! więc przebieg z setkami stron nie zajmuje pamięci GPU naraz.

use std::collections::VecDeque;
use std::path::{Path, PathBuf};

use egui::{ColorImage, Context, TextureHandle, TextureOptions};

const POJEMNOSC: usize = 8;

#[derive(Default)]
pub struct PamiecObrazow {
    wpisy: VecDeque<(PathBuf, Result<TextureHandle, String>)>,
}

pub fn dekoduj(sciezka: &Path) -> Result<ColorImage, String> {
    let obraz = image::ImageReader::open(sciezka)
        .map_err(|e| format!("{}: {e}", sciezka.display()))?
        .with_guessed_format()
        .map_err(|e| format!("{}: {e}", sciezka.display()))?
        .decode()
        .map_err(|e| format!("{}: nie da się zdekodować obrazu: {e}", sciezka.display()))?
        .to_rgb8();
    let rozmiar = [obraz.width() as usize, obraz.height() as usize];
    Ok(ColorImage::from_rgb(rozmiar, obraz.as_raw()))
}

impl PamiecObrazow {
    /// Zwraca teksturę dla ścieżki, ładując ją przy pierwszym użyciu.
    pub fn pobierz(&mut self, ctx: &Context, sciezka: &Path) -> Result<TextureHandle, String> {
        if let Some(i) = self.wpisy.iter().position(|(p, _)| p == sciezka) {
            let wpis = self.wpisy.remove(i).expect("indeks z position");
            let wynik = wpis.1.clone();
            self.wpisy.push_back(wpis);
            return wynik;
        }
        let wynik = dekoduj(sciezka).map(|obraz| {
            ctx.load_texture(sciezka.to_string_lossy(), obraz, TextureOptions::LINEAR)
        });
        self.wpisy.push_back((sciezka.to_path_buf(), wynik.clone()));
        while self.wpisy.len() > POJEMNOSC {
            self.wpisy.pop_front();
        }
        wynik
    }

    pub fn wyczysc(&mut self) {
        self.wpisy.clear();
    }
}
