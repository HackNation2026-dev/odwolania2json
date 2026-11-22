import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
const require = createRequire(import.meta.url);
const editorRequire = createRequire(require.resolve("react-web-pdf-editor"));
const pdfRoot = dirname(editorRequire.resolve("pdfjs-dist/package.json"));
const { version } = JSON.parse(
  await readFile(join(pdfRoot, "package.json"), "utf8"),
);
await mkdir("public/pdf", { recursive: true });
await copyFile(
  join(pdfRoot, "legacy/build/pdf.worker.min.mjs"),
  "public/pdf/pdf.worker.min.mjs",
);
await copyFile(join(pdfRoot, "LICENSE"), "public/pdf/pdfjs-LICENSE.txt");
await copyFile(join(dirname(dirname(require.resolve("react-web-pdf-editor"))), "LICENSE"), "public/pdf/editor-LICENSE.txt");
await copyFile(join(dirname(editorRequire.resolve("pdf-lib/package.json")), "LICENSE.md"), "public/pdf/pdf-lib-LICENSE.txt");
await writeFile(
  "public/pdf/version.json",
  JSON.stringify({ version, editor: "0.1.6" }, null, 2) + "\n",
);
console.log(`Lokalny worker PDF.js ${version}`);
