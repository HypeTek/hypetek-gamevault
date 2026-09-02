import fs from "node:fs";
import vm from "node:vm";
import {fileURLToPath} from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourcePath = path.join(root, "server", "static", "i18n.js");
let source = fs.readFileSync(sourcePath, "utf8");
source = source.replace(
  "window.MissionControlI18n = {applyUiLanguage, tr, trForLanguage, resolveUiLanguage, supportedLanguages: SUPPORTED_UI_LANGUAGES};",
  "window.__missionControlPacks = UI_PACKS;",
);

const context = {
  window: {},
  navigator: {languages: ["en"], language: "en"},
  document: {},
  Node: {TEXT_NODE: 3},
  CustomEvent: function CustomEvent() {},
};
vm.createContext(context);
vm.runInContext(source, context, {filename: sourcePath});
const packs = context.window.__missionControlPacks;
if (!packs) throw new Error("Could not inspect Mission Control language packs.");

const settingsPrefixes = ["settings.", "maintenance.", "profiles.", "library.", "translator."];
for (const language of ["tlh", "sjn"]) {
  const fallbacks = Object.keys(packs.en).filter((key) =>
    settingsPrefixes.some((prefix) => key.startsWith(prefix)) && packs[language][key] === packs.en[key]
  );
  if (fallbacks.length) {
    throw new Error(`${language} still uses English settings fallbacks: ${fallbacks.join(", ")}`);
  }
}

const coverKeys = ["editor.coverFit", "editor.coverFill", "editor.coverContain", "editor.coverZoom", "editor.coverReset"];
for (const [language, pack] of Object.entries(packs)) {
  const missing = coverKeys.filter((key) => !pack[key]);
  if (missing.length) throw new Error(`${language} is missing cover controls: ${missing.join(", ")}`);
}

console.log("Mission Control i18n regression checks passed.");
