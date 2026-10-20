#!/usr/bin/env node
import { chromium } from "playwright";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(new URL(process.argv[1], "file:")));
const template = path.basename(here);
const specs = {
  mountain32: {
    title: "mountain32 · source fidelity study · 2400 × 1600",
    source: "T33631_05",
    change: ['[name="wordScale"]', "1.02"],
    font: "font-factory/font-preparation/braewick/Braewick/Braewick-Regular.otf",
    fontLabel: "Braewick-Regular.otf",
  },
  contactlist32: {
    title: "contactlist32 · source fidelity study · 2400 × 1600",
    source: "T30332_06",
    change: ['[name="scale"]', "1.02"],
    font: "outputs/font-preparation/074-circuit-sprint/Circuit-Sprint/CircuitSprint-Regular.otf",
    fontLabel: "CircuitSprint-Regular.otf",
  },
  messageframe32: {
    title: "messageframe32 · source fidelity study · 2400 × 1600",
    source: "T30332_05",
    change: ['[name="scale"]', "1.02"],
    font: "outputs/font-preparation/074-circuit-sprint/Circuit-Sprint/CircuitSprint-Regular.otf",
    fontLabel: "CircuitSprint-Regular.otf",
  },
  cliffpostcard32: {
    title: "cliffpostcard32 · source fidelity study · 2400 × 1600",
    source: "T30332_02",
    change: ['[name="scale"]', "1.02"],
    font: "outputs/font-preparation/074-circuit-sprint/Circuit-Sprint/CircuitSprint-Regular.otf",
    fontLabel: "CircuitSprint-Regular.otf",
  },
  kindersea32: {
    title: "kindersea32 · source fidelity study · 2400 × 1600",
    source: "T30332_04",
    change: ['[name="scale"]', "1.02"],
    font: "font-factory/fonts/Lost Contact/AOT Lost Contact – Contemporary Pixel Font RGMBLWG/OpenType-TT/AOT Lost Contact.ttf",
    fontLabel: "AOT Lost Contact.ttf",
  },
  sunsetpromise32: {
    title: "sunsetpromise32 · source fidelity study · 2400 × 1600",
    source: "T30332_07",
    change: ['[name="scale"]', "1.02"],
    font: "outputs/font-preparation/074-circuit-sprint/Circuit-Sprint/CircuitSprint-Regular.otf",
    fontLabel: "CircuitSprint-Regular.otf",
  },
  phonegarden32: {
    title: "phonegarden32 · source fidelity study · 2400 × 1600",
    source: "T30332_08",
    change: ['[name="scale"]', "1.02"],
    font: "outputs/font-preparation/93-blazher/Blazher/Blazher-Regular.otf",
    fontLabel: "Blazher-Regular.otf",
  },
  pixelquote32: {
    title: "pixelquote32 · source fidelity study · 2400 × 1600",
    source: "T30332_09",
    change: ['[name="scale"]', "1.02"],
    labelFont: false,
    font: "outputs/font-preparation/93-blazher/Blazher/Blazher-Regular.otf",
    fontLabel: "Blazher-Regular.otf",
  },
  ravencover32: {
    title: "ravencover32 · source fidelity study · 2400 × 1600",
    source: "T28660_00",
    change: ['[name="scale"]', "1.02"],
    font: "outputs/font-preparation/93-blazher/Blazher/Blazher-Regular.otf",
    fontLabel: "Blazher-Regular.otf",
  },
  confident32: {
    title: "confident32 · source fidelity study · 2400 × 1600",
    source: "T28576_04",
    change: ['[name="scale"]', "1.02"],
    font: "outputs/font-preparation/93-blazher/Blazher/Blazher-Regular.otf",
    fontLabel: "Blazher-Regular.otf",
  },
  focusposter32: {
    title: "focusposter32 · source fidelity study · 2400 × 1600",
    source: "T28576_06",
    change: ['[name="titleScale"]', "1.02"],
    labelFont: false,
    font: "outputs/font-preparation/93-blazher/Blazher/Blazher-Regular.otf",
    fontLabel: "Blazher-Regular.otf",
  },
  wideclaim32: {
    title: "wideclaim32 · source fidelity study · 2400 × 1600",
    source: "T28576_07",
    change: ['[name="scale"]', "1.02"],
    labelFont: false,
    font: "outputs/font-preparation/93-blazher/Blazher/Blazher-Regular.otf",
    fontLabel: "Blazher-Regular.otf",
  },
  line32: {
    title: "line32 · broadside layout study · 2400 × 1600",
    source: "No Supplied Source",
    referenceLabel: "Skia Baseline · No Supplied Source",
    change: ['[name="scale"]', "1.02"],
    font: "outputs/font-preparation/93-blazher/Blazher/Blazher-Regular.otf",
    fontLabel: "Blazher-Regular.otf",
  },
  rio32: {
    title: "rio32 · source fidelity study · 2400 × 1600",
    source: "T24250_04",
    change: ['[name="titleScale"]', "1.02"],
    font: "outputs/font-preparation/93-blazher/Blazher/Blazher-Regular.otf",
    fontLabel: "Blazher-Regular.otf",
  },
  card32: {
    title: "card32 · paper stack layout study · 2400 × 1600",
    source: "No Supplied Source",
    referenceLabel: "Skia Baseline · No Supplied Source",
    change: ['[name="scale"]', "1.02"],
    font: "font-factory/fonts/archive/Esviga/Esviga – Blackletter Font 7DZ3HHR/Esviga.ttf",
    fontLabel: "Esviga.ttf",
  },
  plakat32: {
    title: "plakat32 · source fidelity study · 2400 × 1600",
    source: "T27673_00",
    change: ['[name="headline"]', "Make Room For Type"],
    font: "font-factory/fonts/archive/Kaitten/Kaitten Modern Sans Font N6QD9GC/Kaitten-Regular.otf",
    fontLabel: "Kaitten-Regular.otf",
  },
  plakatart32: {
    title: "plakatart32 · source fidelity study · 2400 × 1600",
    source: "T27673_10",
    change: ['[name="headline"]', "Color"],
    font: "outputs/font-preparation/93-blazher/Blazher/Blazher-Regular.otf",
    fontLabel: "Blazher-Regular.otf",
  },
  birvase32: {
    title: "birvase32 · source fidelity study · 2400 × 1600",
    source: "T33110_08",
    change: ['[name="headline"]', "Bloom"],
    font: "font-factory/fonts/archive/Old Norse/Download/OldNorse-Regular.ttf",
    fontLabel: "OldNorse-Regular.ttf",
  },
  weightfamily32: {
    title: "weightfamily32 · source fidelity study · 2400 × 1600",
    source: "T30930_01",
    change: ['[name="scale"]', "1.02"],
    font: "font-factory/fonts/archive/Kaitten/Kaitten Modern Sans Font N6QD9GC/Kaitten-Regular.otf",
    familyFonts: ["Kaitten-Regular.otf", "Kaitten-Italic.otf"],
    fontLabel: "Kaitten Family",
  },
  mangosboard32: {
    title: "mangosboard32 · source fidelity study · 2400 × 1600",
    source: "T30930_04",
    change: ['[name="scale"]', "1.02"],
    font: "font-factory/fonts/archive/DIanda/Dianda – Retro Serif Typeface 987JHGZ/TTF/Dianda-Regular.ttf",
    familyFonts: ["Dianda-Extrude.ttf", "Dianda-Outline.ttf", "Dianda-Regular.ttf"],
    fontLabel: "Dianda Family",
  },
  ovalword32: {
    title: "ovalword32 · source fidelity study · 2400 × 1600",
    source: "T30332_00",
    change: ['[name="headline"]', "Sadie"],
    font: "font-factory/fonts/Maidega/Maidega-Regular.ttf",
    fontLabel: "Maidega-Regular.ttf",
  },
  stardust32: {
    title: "stardust32 · source fidelity study · 2400 × 1600",
    source: "T30332_01",
    change: ['[name="headline"]', "Dreams And\nWonder"],
    font: "font-factory/fonts/Maidega/Maidega-Regular.ttf",
    fontLabel: "Maidega-Regular.ttf",
  },
  blossom32: {
    title: "blossom32 · source fidelity study · 2400 × 1600",
    source: "T28576_08",
    change: ['[name="headline"]', "Bloom\nInto Calm"],
    font: "font-factory/fonts/Maidega/Maidega-Regular.ttf",
    fontLabel: "Maidega-Regular.ttf",
  },
  neue32: {
    title: "neue32 · source fidelity study · 2400 × 1600",
    source: "T25441_04",
    change: ['[name="repeated"]', "Neue!"],
    font: "font-factory/fonts/archive/Kaitten/Kaitten Modern Sans Font N6QD9GC/Kaitten-Regular.otf",
    fontLabel: "Kaitten-Regular.otf",
  },
  electromagnetic32: {
    title: "electromagnetic32 · source fidelity study · 2400 × 1600",
    source: "T19827_01",
    change: ['[name="headline"]', "Electro\nMagnetic\nShady-01\nCourse-"],
    font: "font-factory/fonts/Opensga/Opengsa – Gym Sport Font L2S6XLG/Opengsa.ttf",
    fontLabel: "Opensga.ttf",
  },
  mirror32: {
    title: "mirror32 · source fidelity study · 2400 × 1600",
    source: "T13692_12",
    change: ['[name="line1"]', "PEOPLE WAIT"],
    labelFont: false,
    font: "font-factory/fonts/Maidega/Maidega-Regular.ttf",
    fontLabel: "Maidega",
  },
  neon32: {
    title: "neon32 · source fidelity study · 2400 × 1600",
    source: "T30173_07",
    change: ['[name="headline"]', "Bright Tonight\nAfter Hours"],
    labelFont: false,
    fontLabel: "Gladista Script",
  },
  latestlook32: {
    title: "latestlook32 · source fidelity study · 2400 × 1600",
    source: "T24908_02",
    change: ['[name="lineTwo"]', "Spring"],
  },
  gelatocards32: {
    title: "gelatocards32 · source fidelity study · 2400 × 1600",
    source: "T24908_03",
    change: ['[name="frontOne"]', "FRESH"],
  },
  meditation32: {
    title: "meditation32 · source fidelity study · 2400 × 1600",
    source: "T25990_02",
    change: ['[name="headline"]', "CALM"],
  },
  strongweak32: {
    title: "strongweak32 · source fidelity study · 2400 × 1600",
    source: "T26289_00",
    change: ['[name="weakest"]', "SOFTEST"],
  },
  funkyfashion32: {
    title: "funkyfashion32 · source fidelity study · 2400 × 1600",
    source: "T26289_01",
    change: ['[name="headlineTwo"]', "STYLE"],
  },
  typewall32: {
    title: "typewall32 · source fidelity study · 2400 × 1600",
    source: "T26223_02",
    change: ['[name="row2"]', "Musical Letterforms"],
    labelFont: false,
  },
  manualbrew32: {
    title: "manualbrew32 · source fidelity study · 2400 × 1600",
    source: "T26223_03",
    change: ['[name="lineTwo"]', "ROAST"],
    labelFont: false,
    font: "font-factory/support-html/assets/LilitaOne-Regular.ttf",
    fontLabel: "Lilita One",
  },
  pastpresent32: {
    title: "pastpresent32 · source fidelity study · 2400 × 1600",
    source: "T26223_04",
    change: ['[name="present"]', "TODAY"],
    labelFont: false,
    font: "font-factory/support-html/assets/LilitaOne-Regular.ttf",
    fontLabel: "Lilita One",
  },
  herbalproduct32: {
    title: "herbalproduct32 · source fidelity study · 2400 × 1600",
    source: "T26223_05",
    change: ['[name="headline"]', "HERBAL"],
    font: "font-factory/support-html/assets/LilitaOne-Regular.ttf",
    fontLabel: "Lilita One",
  },
  colosseum32: {
    title: "colosseum32 · source fidelity study · 2400 × 1600",
    source: "T26074_01",
    change: ['[name="lineTwo"]', "grüngöling"],
    labelFont: false,
    font: "font-factory/support-html/assets/LilitaOne-Regular.ttf",
    fontLabel: "Lilita One",
  },
};
const spec = specs[template];
if (!spec) throw new Error(`Unknown support benchmark directory: ${template}`);

const root = path.resolve(here, "../../../..");
const output = path.join(here, "output");
const font = path.join(root, spec.font || "font-factory/fonts/16-Gladista-Script/Gladista.ttf");
const familyFonts = (spec.familyFonts || []).map((file) => path.join(path.dirname(font), file));
const fontLabel = spec.fontLabel || "Gladista";
const labelFont = path.join(root, "font-factory/support-html/assets/NotoSans-CondensedLight.ttf");
const files = {
  source: path.join(output, "reference.png"),
  skia: path.join(output, "skia.png"),
  html: path.join(output, "html.png"),
};
const data = async (file) => "data:image/png;base64," + (await readFile(file)).toString("base64");
await mkdir(output, { recursive: true });
await Promise.all([...Object.values(files), font, labelFont, ...familyFonts].map((file) => stat(file)));

const browser = await chromium.launch({
  executablePath: "/usr/bin/chromium",
  headless: true,
  args: ["--no-sandbox", "--allow-file-access-from-files"],
});
try {
  const page = await browser.newPage({ viewport: { width: 1920, height: 620 }, deviceScaleFactor: 1 });
  const [source, skia, html] = await Promise.all(Object.values(files).map(data));
  await page.setContent('<!doctype html><html><head><meta charset="utf-8"><style>' +
    '*{box-sizing:border-box}body{margin:0;background:#17191d;color:#f2f1ec;font:13px/1.45 system-ui,sans-serif}' +
    'header{height:55px;display:flex;align-items:center;padding:0 18px;color:#d2d0c8;font-size:12px;letter-spacing:.12em;text-transform:uppercase}' +
    'main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:0 12px 12px}' +
    'figure{margin:0;min-width:0}figcaption{height:30px;padding:5px 2px;color:#c5c4c0;font-size:11px;letter-spacing:.06em;text-transform:uppercase}' +
    '.frame{width:100%;aspect-ratio:3/2;background:#a27760;overflow:hidden}img{width:100%;height:100%;object-fit:contain;display:block}' +
    '</style></head><body><header>' + spec.title + '</header><main>' +
    '<figure><figcaption>' + (spec.referenceLabel || 'Original · ' + spec.source) + '</figcaption><div class="frame"><img src="' + source + '" alt="Original source reference"></div></figure>' +
    '<figure><figcaption>Current Skia · ' + fontLabel + '</figcaption><div class="frame"><img src="' + skia + '" alt="Current Skia support image"></div></figure>' +
    '<figure><figcaption>HTML/CSS · ' + fontLabel + '</figcaption><div class="frame"><img src="' + html + '" alt="HTML and CSS source-led support image"></div></figure>' +
    '</main></body></html>');
  await page.screenshot({ path: path.join(output, "comparison.png"), fullPage: true });

  const editor = path.join(root, "font-factory/support-html/templates", template, "editor.html");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(pathToFileURL(editor).href, { waitUntil: "networkidle" });
  await page.locator("#font-file").setInputFiles(font);
  await page.getByText(/loaded as the live display font/).waitFor();
  for (const [index, familyFont] of familyFonts.entries()) {
    const familyInput = page.locator(`#family-font-${index + 1}`);
    if (!(await familyInput.count())) throw new Error(`${template}: family font picker ${index + 1} is missing`);
    await familyInput.setInputFiles(familyFont);
  }
  if (spec.labelFont !== false && await page.locator("#label-font-file").count()) {
    await page.locator("#label-font-file").setInputFiles(labelFont);
    await page.getByText(/loaded as the live small copy font|loaded as the live label font/).waitFor();
  }
  await page.evaluate(() => document.fonts.ready);
  const desktopLayout = await page.evaluate(() => window.getLayoutReport());
  if (desktopLayout.outOfBounds.length) throw new Error("Desktop editor has off-canvas elements: " + JSON.stringify(desktopLayout.outOfBounds));
  await page.screenshot({ path: path.join(output, "editor-desktop.png"), fullPage: true });

  const editToPaintMs = await page.evaluate(async ([selector, value]) => {
    const input = document.querySelector(selector);
    if (!input) throw new Error("Missing editable control " + selector);
    const original = input.value;
    const start = performance.now();
    input.value = value;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const elapsed = performance.now() - start;
    input.value = original;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    return Number(elapsed.toFixed(2));
  }, spec.change);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.configureTemplate());
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const mobileLayout = await page.evaluate(() => window.getLayoutReport());
  if (mobileLayout.outOfBounds.length) throw new Error("Mobile editor has off-canvas elements: " + JSON.stringify(mobileLayout.outOfBounds));
  await page.screenshot({ path: path.join(output, "editor-mobile.png"), fullPage: true });
  const result = {
    comparison: path.join(output, "comparison.png"),
    editor,
    browser: browser.version(),
    displayFont: fontLabel,
    exportPixels: { width: 2400, height: 1600 },
    editToPaintMs,
    imageBytes: {
      html: (await stat(files.html)).size,
      skia: (await stat(files.skia)).size,
    },
    desktopLayout,
    mobileLayout,
  };
  await writeFile(path.join(output, "benchmark.json"), JSON.stringify(result, null, 2) + "\n");
  console.log(JSON.stringify(result, null, 2));
} finally {
  await browser.close();
}
