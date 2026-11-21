//! Generuje małe obrazy stron dla `fixtures/przebieg-demo/strony/`.
//! Uruchomienie: `cargo run --example generuj_fixture`

use std::path::Path;

use image::{Rgb, RgbImage};

/// Prosta „strona”: białe tło, nagłówek i szare paski udające wiersze tekstu.
fn strona(szer: u32, wys: u32, wierszy: u32, szum: u8, ciemniej: u8) -> RgbImage {
    let mut img = RgbImage::from_pixel(szer, wys, Rgb([255 - ciemniej; 3]));
    let margines = szer / 10;
    let mut y = wys / 12;
    // nagłówek
    for yy in y..y + 10 {
        for x in margines..szer / 2 {
            img.put_pixel(x, yy, Rgb([40, 40, 40]));
        }
    }
    y += 24;
    for w in 0..wierszy {
        let dl = szer - 2 * margines - (w * 37 % (szer / 4));
        for yy in y..(y + 4).min(wys) {
            for x in margines..margines + dl {
                img.put_pixel(x, yy, Rgb([110, 110, 110]));
            }
        }
        y += 12;
        if y + 4 >= wys - margines {
            break;
        }
    }
    if szum > 0 {
        let mut s: u32 = 12345;
        for p in img.pixels_mut() {
            s = s.wrapping_mul(1_103_515_245).wrapping_add(12345);
            let d = ((s >> 16) % (szum as u32 * 2 + 1)) as i32 - szum as i32;
            for c in p.0.iter_mut() {
                *c = (*c as i32 + d).clamp(0, 255) as u8;
            }
        }
    }
    img
}

fn zapisz(img: &RgbImage, sciezka: &Path) {
    std::fs::create_dir_all(sciezka.parent().unwrap()).unwrap();
    let mut plik = std::fs::File::create(sciezka).unwrap();
    image::codecs::jpeg::JpegEncoder::new_with_quality(&mut plik, 70).encode_image(img).unwrap();
    println!("zapisano {}", sciezka.display());
}

fn main() {
    let baza = Path::new(env!("CARGO_MANIFEST_DIR")).join("fixtures/przebieg-demo/strony");
    zapisz(&strona(300, 424, 22, 0, 0), &baza.join("odw-001/p001.jpg"));
    zapisz(&strona(300, 424, 10, 0, 0), &baza.join("odw-001/p002.jpg"));
    // strona „obrócona”: pozioma, z paskami pionowymi po obróceniu
    let obrocona = image::imageops::rotate90(&strona(300, 424, 18, 12, 20));
    zapisz(&obrocona, &baza.join("syn-001/p001.jpg"));
    zapisz(&strona(300, 424, 8, 40, 50), &baza.join("syn-001/p002.jpg"));
    zapisz(&strona(300, 424, 16, 20, 35), &baza.join("neg-001/p001.jpg"));
}
