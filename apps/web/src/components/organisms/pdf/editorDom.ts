/** Adapter DOM dla przypiętej wersji react-web-pdf-editor 0.1.6.
 * dist/index.js: PdfPage renderuje względny .rpe-page[data-page-number],
 * canvas i .textLayer jako dzieci. Portal z procentami dziedziczy rozmiar strony;
 * nie mierzymy położenia względem viewportu ani scrolla. Zmiana wersji wymaga testu adaptera i e2e.
 */
export function editorPages(root: HTMLElement): HTMLElement[] {
  return Array.from(
    root.querySelectorAll<HTMLElement>(".rpe-page[data-page-number]"),
  );
}
export function editorStage(root: HTMLElement) {
  return root.querySelector<HTMLElement>(".rpe-stage");
}
