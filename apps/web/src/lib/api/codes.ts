/** Architektura §6: kanoniczny kod katalogu → proponowany kod techniczny. */
export const executionCodes = {
  ocr_niedostepny: "ocr_unavailable", ocr_blad: "ocr_error", pdf_uszkodzony: "pdf_corrupted", pdf_zaszyfrowany: "pdf_encrypted",
  llm_niedostepny: "llm_unavailable", llm_autoryzacja: "llm_authorization", llm_limit: "llm_rate_limit", llm_odpowiedz_niepoprawna: "llm_invalid_response",
  konfiguracja_niepoprawna: "invalid_configuration", limit_czasu: "time_limit", limit_kontekstu: "context_limit", zapis_nieudany: "write_failed",
  walidacja_wyniku_nieudana: "result_validation_failed", klasa_niejednoznaczna: "class_ambiguous", skan: "scan", strona_mieszana: "mixed_page",
  dokument_mieszany: "mixed_document", niska_jakosc: "low_quality", zla_warstwa_ocr: "invalid_ocr_layer", uciety_tekst: "clipped_text",
  dokument_obcy: "foreign_document", brak_informacji_wprost: "information_not_explicit", dane_dalej_niz_3_strona: "data_after_page_3", podobny_do_klasy: "class_lookalike", wiele_dokumentow: "multiple_documents",
} as const;
/** Kod z projektu UI F14 zachowany bez udawania kodu istniejącego w OpenAPI. */
export const uiTimeoutCode = "LLM_TIMEOUT";
/** Źródłem 12 opisów pozostaje enum zgodny z powody.py, nie pięć powodów braków. */
export { default as contractSchemas } from "./contract.generated.json";
