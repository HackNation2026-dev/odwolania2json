#![forbid(unsafe_code)]

use std::path::PathBuf;

fn main() -> eframe::Result {
    let katalog = std::env::args_os().nth(1).map(PathBuf::from);
    let opcje = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("Przeglądarka przypadków brzegowych")
            .with_app_id("przegladarka-przypadkow")
            .with_inner_size([1500.0, 900.0]),
        ..Default::default()
    };
    eframe::run_native(
        "przegladarka-przypadkow",
        opcje,
        Box::new(move |cc| Ok(Box::new(przegladarka::ui::Aplikacja::new(cc, katalog)))),
    )
}
