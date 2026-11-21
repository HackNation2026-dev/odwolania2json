use std::fs;
use std::path::{Path, PathBuf};

use przegladarka::dane::{self, Przebieg, StanAdnotacji};
use przegladarka::model::{Adnotacja, Dokument, Manifest, Problem};
use przegladarka::{obrazy, podsumowanie};

fn fixture() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("fixtures/przebieg-demo")
}

/// Kopia fixture w katalogu tymczasowym, żeby testy zapisu nie ruszały repozytorium.
fn kopia_fixture() -> tempfile::TempDir {
    fn kopiuj(z: &Path, do_: &Path) {
        fs::create_dir_all(do_).unwrap();
        for w in fs::read_dir(z).unwrap() {
            let w = w.unwrap();
            let cel = do_.join(w.file_name());
            if w.file_type().unwrap().is_dir() {
                kopiuj(&w.path(), &cel);
            } else {
                fs::copy(w.path(), cel).unwrap();
            }
        }
    }
    let tmp = tempfile::tempdir().unwrap();
    kopiuj(&fixture(), tmp.path());
    tmp
}

#[test]
fn wczytuje_fixture() {
    let p = Przebieg::wczytaj(&fixture()).expect("manifest");
    assert_eq!(p.manifest.przebieg, "przebieg-demo");
    assert_eq!(p.manifest.modele.len(), 3);
    assert_eq!(p.pozycje.len(), 3);
    for poz in &p.pozycje {
        assert!(poz.dokument.is_ok(), "{}: {:?}", poz.wpis.id, poz.dokument.as_ref().err());
    }
    let id = |s: &str| p.pozycje.iter().find(|x| x.wpis.id == s).unwrap();

    let odw = id("odw-001");
    assert!(odw.rozbieznosc, "MiniMax wskazał pełnomocnictwo");
    assert_eq!(odw.adnotacja.status(), "przejrzany");

    let syn = id("syn-001");
    assert!(!syn.rozbieznosc, "model z błędem nie liczy się do rozbieżności");
    let dok = syn.dokument.as_ref().unwrap();
    assert_eq!(dok.wstrzykniete.len(), 3);
    assert!(dok.modele["minimax"].wynik.is_none());
    assert_eq!(dok.modele["codex"].ocena_auto.as_ref().unwrap().podobienstwo(2), Some(0.81));

    let neg = id("neg-001");
    assert!(matches!(neg.adnotacja, StanAdnotacji::Brak));
    assert_eq!(neg.adnotacja.status(), "nieprzejrzany");
    assert!(neg.dokument.as_ref().unwrap().modele.is_empty());
}

#[test]
fn obrazy_fixture_dekoduja_sie_a_brak_pliku_to_blad() {
    let p = Przebieg::wczytaj(&fixture()).unwrap();
    for poz in &p.pozycje {
        for s in &poz.dokument.as_ref().unwrap().strony {
            let obraz = obrazy::dekoduj(&dane::sciezka_wzgledna(&p.katalog, &s.obraz)).expect("obraz");
            assert!(obraz.size[0] > 0 && obraz.size[1] > 0);
        }
    }
    assert!(obrazy::dekoduj(&fixture().join("strony/nie-ma.jpg")).is_err());
}

#[test]
fn roundtrip_zapisu_i_odczytu_adnotacji() {
    let tmp = kopia_fixture();
    let mut a = Adnotacja::nowa("neg-001");
    a.status = "do_dyskusji".into();
    a.klasa = Some("obcy".into());
    a.notatka = "Notatka z \"cudzysłowem\" i ąęłńóśźż".into();
    a.problemy_dokumentu.push(Problem { kod: "kod_spoza".into(), opis: "x".into(), waga: "wysoka".into() });
    a.strona_mut(1).problemy.push(Problem { kod: "slaba_jakosc_skanu".into(), opis: "szum".into(), waga: "dziwna".into() });
    a.strona_mut(3); // pusty wpis – ma zniknąć przy zapisie
    let modele = Przebieg::wczytaj(tmp.path()).unwrap().manifest.modele;
    a.przygotuj_do_zapisu("Recenzent A", &modele, dane::teraz_iso());
    dane::zapisz_adnotacje(tmp.path(), &a).unwrap();

    let wczytana = match dane::wczytaj_adnotacje(tmp.path(), "neg-001") {
        StanAdnotacji::Jest(x) => *x,
        inny => panic!("{inny:?}"),
    };
    assert_eq!(wczytana, a);
    assert_eq!(wczytana.wersja, 1);
    assert_eq!(wczytana.recenzent, "Recenzent A");
    assert_eq!(wczytana.strony.len(), 1, "pusta strona usunięta");
    assert_eq!(wczytana.strony[0].problemy[0].waga, "srednia", "waga znormalizowana");
    assert_eq!(wczytana.ocena_modeli.len(), 3);
    assert!(wczytana.ocena_modeli.values().all(|v| v == "brak_oceny"));
    // ISO 8601 z przesunięciem
    assert!(chrono::DateTime::parse_from_rfc3339(&wczytana.zmieniono).is_ok(), "{}", wczytana.zmieniono);

    // Wymagane pola schematu obecne w pliku
    let surowy: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(dane::sciezka_adnotacji(tmp.path(), "neg-001")).unwrap()).unwrap();
    for pole in ["id", "wersja", "recenzent", "zmieniono", "status", "klasa", "notatka", "problemy_dokumentu", "strony", "ocena_modeli"] {
        assert!(surowy.get(pole).is_some(), "brak pola {pole}");
    }
}

#[test]
fn zapis_jest_atomowy_i_nie_zostawia_plikow_tymczasowych() {
    let tmp = kopia_fixture();
    let mut a = Adnotacja::nowa("odw-001");
    a.status = "w_toku".into();
    dane::zapisz_adnotacje(tmp.path(), &a).unwrap();
    a.notatka = "druga wersja".into();
    dane::zapisz_adnotacje(tmp.path(), &a).unwrap();

    let pliki: Vec<String> = fs::read_dir(tmp.path().join("adnotacje"))
        .unwrap()
        .map(|w| w.unwrap().file_name().to_string_lossy().into_owned())
        .collect();
    assert_eq!(pliki, vec!["odw-001.json".to_string()], "tylko plik docelowy, bez .tmp");
    let StanAdnotacji::Jest(w) = dane::wczytaj_adnotacje(tmp.path(), "odw-001") else { panic!() };
    assert_eq!(w.notatka, "druga wersja");

    // Gdy zapis się nie uda (cel jest katalogiem), stary plik zostaje, a tymczasowy jest sprzątany.
    let cel = tmp.path().join("adnotacje").join("katalog.json");
    fs::create_dir_all(cel.join("x")).unwrap();
    assert!(dane::zapisz_atomowo(&cel, b"{}").is_err());
    let tymczasowe = fs::read_dir(tmp.path().join("adnotacje"))
        .unwrap()
        .filter(|w| w.as_ref().unwrap().file_name().to_string_lossy().ends_with(".tmp"))
        .count();
    assert_eq!(tymczasowe, 0);
}

#[test]
fn toleruje_nieznane_pola_i_null() {
    let manifest: Manifest = serde_json::from_str(
        r#"{"format":"uzp-przypadki-brzegowe","wersja":1,"przebieg":null,"cos_nowego":42,
            "taksonomia":null,"modele":[{"id":"m","nazwa":null,"model":"x","uwagi":null,"extra":1}],
            "dokumenty":[{"id":"a","klasa_oczekiwana":null,"sprawa":null,"liczba_stron":null,"typ_auto":"nowy_typ"}]}"#,
    )
    .unwrap();
    assert_eq!(manifest.przebieg, "");
    assert!(manifest.taksonomia.is_empty());
    assert_eq!(manifest.dokumenty[0].typ_auto, "nowy_typ");
    assert_eq!(manifest.dokumenty[0].liczba_stron, 0);

    let dok: Dokument = serde_json::from_str(
        r#"{"id":"a","zrodlo":"nowe_zrodlo","metadane":null,"wstrzykniete":null,
            "strony":[{"nr":1,"obraz":"strony/a/p001.jpg","dpi_obrazow":null,"znaki_tekstu":null,"probka_tekstu":null,"x":[]}],
            "modele":{"m":{"status":"ok","czas_s":null,"blad":null,"strony_przeslane":null,
                "wynik":{"klasa":"inny","strony":[{"nr":1,"obrot_stopnie":null,"problemy":null}],"problemy_dokumentu":[{"kod":"nowy","waga":null}]},
                "ocena_auto":null}}}"#,
    )
    .unwrap();
    assert_eq!(dok.strony[0].probka_tekstu, "");
    assert!(dok.strony[0].dpi_obrazow.is_none());
    let w = dok.modele["m"].wynik.as_ref().unwrap();
    assert_eq!(w.problemy_dokumentu[0].kod, "nowy");
    assert_eq!(w.strony[0].obrot_stopnie, None);

    // Nieznane pola adnotacji przetrwają ponowny zapis.
    let a: Adnotacja = serde_json::from_str(
        r#"{"id":"a","wersja":1,"recenzent":null,"zmieniono":"","status":"w_toku","klasa":null,
            "notatka":null,"problemy_dokumentu":null,"strony":[],"ocena_modeli":{},"pole_v2":{"k":1}}"#,
    )
    .unwrap();
    assert_eq!(a.recenzent, "");
    let json = serde_json::to_value(&a).unwrap();
    assert_eq!(json["pole_v2"]["k"], 1);
    assert!(json["klasa"].is_null());

    // Uszkodzony plik adnotacji -> stan błędu zamiast paniki.
    let tmp = tempfile::tempdir().unwrap();
    fs::create_dir_all(tmp.path().join("adnotacje")).unwrap();
    fs::write(tmp.path().join("adnotacje/zly.json"), "{ nie json").unwrap();
    assert!(matches!(dane::wczytaj_adnotacje(tmp.path(), "zly"), StanAdnotacji::Blad(_)));
}

#[test]
fn brak_pliku_dokumentu_nie_psuje_przebiegu() {
    let tmp = kopia_fixture();
    fs::remove_file(tmp.path().join("dokumenty/neg-001.json")).unwrap();
    fs::write(tmp.path().join("dokumenty/syn-001.json"), "[]").unwrap();
    let p = Przebieg::wczytaj(tmp.path()).unwrap();
    assert_eq!(p.pozycje.iter().filter(|x| x.dokument.is_err()).count(), 2);
}

#[test]
fn podsumowanie_i_csv() {
    let p = Przebieg::wczytaj(&fixture()).unwrap();
    let s = podsumowanie::policz(&p);
    let m = |id: &str| s.modele.iter().find(|m| m.id == id).unwrap();
    assert_eq!((m("codex").trafione_klasy, m("codex").ocenione_klasy), (2, 2));
    assert_eq!((m("minimax").trafione_klasy, m("minimax").ocenione_klasy), (0, 1));
    assert_eq!(m("minimax").bledy, 1);
    assert_eq!(m("codex").wstrzykniete["obrot_strony"], (1, 1));
    assert_eq!(m("claude").wstrzykniete["slaba_jakosc_skanu"], (0, 1));
    assert!(!m("minimax").wstrzykniete.contains_key("obrot_strony"), "model z błędem nie jest liczony");
    let pod = m("codex").srednie_podobienstwo.unwrap();
    assert!((pod - (0.93 + 0.97 + 0.81) / 3.0).abs() < 1e-9);
    assert_eq!(s.statusy["przejrzany"], 1);
    assert_eq!(s.statusy["nieprzejrzany"], 2);
    assert_eq!(s.kody_czlowieka["pieczec_naklada_tekst"], 1);

    let tmp = kopia_fixture();
    let p = Przebieg::wczytaj(tmp.path()).unwrap();
    let sciezka = dane::eksportuj_csv(&p).unwrap();
    let csv = fs::read_to_string(sciezka).unwrap();
    let wiersze: Vec<&str> = csv.lines().collect();
    assert_eq!(wiersze[0], "id,strona,kod,waga,opis,recenzent,status");
    assert_eq!(wiersze[1], "odw-001,2,pieczec_naklada_tekst,niska,\"Podpis lekko na tekście, czytelne\",demo,przejrzany");
}

#[test]
fn najnowszy_przebieg_wybiera_katalog_z_manifestem() {
    let tmp = tempfile::tempdir().unwrap();
    fs::create_dir_all(tmp.path().join("bez_manifestu")).unwrap();
    assert!(dane::najnowszy_przebieg(tmp.path()).is_none());
    fs::create_dir_all(tmp.path().join("p1")).unwrap();
    fs::write(tmp.path().join("p1/manifest.json"), "{}").unwrap();
    assert_eq!(dane::najnowszy_przebieg(tmp.path()).unwrap(), tmp.path().join("p1"));
}

#[test]
fn pierwsza_edycja_zmienia_status_na_w_toku() {
    let oryginal = Adnotacja::nowa("x");
    assert!(Adnotacja::po_edycji(&oryginal, oryginal.clone()).is_none(), "bez zmian = bez zapisu");

    let mut e = oryginal.clone();
    e.notatka = "coś".into();
    assert_eq!(Adnotacja::po_edycji(&oryginal, e).unwrap().status, "w_toku");

    // Jawny wybór statusu przez człowieka nie jest nadpisywany.
    let mut e = oryginal.clone();
    e.status = "przejrzany".into();
    assert_eq!(Adnotacja::po_edycji(&oryginal, e).unwrap().status, "przejrzany");
}

#[test]
fn przejmowanie_problemow_z_modelu_bez_duplikatow() {
    let p = Przebieg::wczytaj(&fixture()).unwrap();
    let syn = p.pozycje.iter().find(|x| x.wpis.id == "syn-001").unwrap().dokument.as_ref().unwrap();
    let wynik = syn.modele["claude"].wynik.as_ref().unwrap();
    let mut a = Adnotacja::nowa("syn-001");
    a.przejmij_z_modelu(wynik);
    a.przejmij_z_modelu(wynik);
    assert_eq!(a.strona(1).unwrap().problemy.len(), 1);
    let p2 = &a.strona(2).unwrap().problemy;
    assert_eq!(p2.len(), 1);
    assert_eq!(p2[0].kod, "kod_wymyslony_przez_model", "kod spoza taksonomii zachowany");
    assert_eq!(p2[0].waga, "srednia", "nieznana waga „krytyczna” znormalizowana");
}
