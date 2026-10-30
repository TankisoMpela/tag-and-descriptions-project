#!/usr/bin/env node
import { chromium } from "playwright";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const get = (key, fallback = "") => {
  const index = process.argv.indexOf("--" + key);
  return index < 0 ? fallback : process.argv[index + 1];
};
const getAll = (key) => process.argv.flatMap((value, index) =>
  value === "--" + key && process.argv[index + 1] ? [process.argv[index + 1]] : []);
const template = get("template");
const entry = get("editor");
const ratio = get("ratio", "3x2");
const frames = {
  "3x2": { cssWidth: 1200, cssHeight: 800, width: 2400, height: 1600 },
  "1x1": { cssWidth: 800, cssHeight: 800, width: 1600, height: 1600 },
};
const frameSpec = frames[ratio];
const source = get("source", "");
const font = get("font", "");
const labelFont = get("label-font", "");
const familyFonts = getAll("family-font");
const out = path.resolve(get("out", path.join(here, `${template || "template"}.png`)));
let props = {};
try {
  props = JSON.parse(get("props", "{}"));
} catch (error) {
  throw new Error("--props must be valid JSON: " + error.message);
}
if (!template || !entry) throw new Error("--template and --editor are required");
if (!frameSpec) throw new Error('--ratio must be "3x2" or "1x1"');
if (template === "italicregular32" && familyFonts.length < 1) {
  throw new Error("italicregular32 requires a real sibling family font via --family-font");
}

// All display copy uses Title Case, including source-led remakes. Only literal
// glyph specimen strings preserve their source casing; URLs and colours are
// data, not prose.
const literalCaseKeys = {
  alphabet32: new Set(["uppercase", "lowercase", "figures", "alphabet", "glyphs"]),
  glyphsheet32: new Set(["symbols", "digits", "figures"]),
  alternatechart32: new Set(["upperRows", "lowerRows", "figures"]),
  mangosboard32: new Set(["glyphs", "tileA", "tileAt"]),
  weightfamily32: new Set(["row1", "row2", "row3"]),
  practicehard32: new Set(["powerOne", "powerTwo", "powerThree", "powerFour"]),
  neue32: new Set(["repeated"]),
  italicregular32: new Set(["leftGlyph", "rightGlyph"]),
  smokeletters32: new Set(["leftGlyph", "rightGlyph"]),
  awakeportrait32: new Set(["year"]),
};
function titleCaseCopy(value) {
  const urls = [];
  let text = String(value ?? "").replace(/(?:https?:\/\/|www\.)[^\s]+/giu, (url) => {
    const token = `\uE000${urls.length}\uE001`;
    urls.push(url);
    return token;
  });
  text = text.replace(/\p{L}+(?:['’]\p{L}+)*/gu, (word) => {
    const first = word.slice(0, 1).toLocaleUpperCase("en");
    const rest = word === word.toLocaleUpperCase("en")
      ? word.slice(1).toLocaleLowerCase("en") : word.slice(1);
    return first + rest;
  });
  return text.replace(/\uE000(\d+)\uE001/gu, (_match, index) => urls[Number(index)]);
}
function titleCaseProps(value, key = "", templateId = template) {
  if (Array.isArray(value)) {
    return value.map((item) => titleCaseProps(item, key, templateId));
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([childKey, child]) =>
      [childKey, titleCaseProps(child, childKey, templateId)]));
  }
  if (typeof value !== "string") return value;
  if (key === "fontClass" || literalCaseKeys[templateId]?.has(key) || key === "warnings" ||
      key.toLocaleLowerCase("en").includes("url") ||
      /^(?:#[\da-f]{3,8}|rgba?\(|hsla?\()/iu.test(value.trim())) return value;
  return titleCaseCopy(value);
}
props = titleCaseProps(props);

const editor = path.resolve(process.cwd(), entry);
await mkdir(path.dirname(out), { recursive: true });
const browser = await chromium.launch({
  ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
    ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH }
    : {}),
  headless: true,
  // Source artwork may be a local image mask inside an editor loaded via
  // file://. Allow same-session local assets for this isolated export browser.
  args: ["--no-sandbox", "--allow-file-access-from-files"],
});
try {
  const page = await browser.newPage({
    viewport: { width: 1520, height: 1024 },
    deviceScaleFactor: 2,
  });
  await page.goto(pathToFileURL(editor).href, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.addStyleTag({
    content: "#artboard, #artboard * { text-transform: none !important; }",
  });
  if (font) {
    const input = page.locator("#font-file");
    if (!(await input.count())) throw new Error(`${template}: editor is missing #font-file`);
    await input.setInputFiles(path.resolve(font));
    await page.getByText(/loaded as the live .* font/).waitFor();
  }
  if (labelFont) {
    const input = page.locator("#label-font-file");
    if (!(await input.count())) throw new Error(`${template}: editor is missing #label-font-file`);
    await input.setInputFiles(path.resolve(labelFont));
    await page.getByText(/loaded as the live label font/).waitFor();
  }
  if (familyFonts.length) {
    const faces = await Promise.all(familyFonts.map(async (file, index) => ({
      name: `SupportFamily${index + 1}`,
      data: (await readFile(path.resolve(file))).toString("base64"),
    })));
    await page.evaluate(async (items) => {
      window.SupportFamilyAvailable = [];
      for (const item of items) {
        const face = new FontFace(item.name, `url(data:font/ttf;base64,${item.data})`);
        await face.load();
        document.fonts.add(face);
        window.SupportFamilyAvailable.push(item.name);
      }
      await document.fonts.ready;
    }, faces);
  }
  await page.evaluate(() => document.fonts.ready);
  const frame = page.locator("#artboard");
  if (!(await frame.count())) throw new Error(`${template}: editor is missing #artboard`);
  await frame.evaluate((el, spec) => Object.assign(el.style, {
    position: "fixed",
    left: "0",
    top: "0",
    width: `${spec.cssWidth}px`,
    height: `${spec.cssHeight}px`,
    maxWidth: "none",
    margin: "0",
    zIndex: "2147483647",
  }), frameSpec);
  await frame.evaluate((el, value) => {
    el.dataset.ratio = value;
    document.documentElement.dataset.supportRatio = value;
  }, ratio);
  const bounds = await frame.boundingBox();
  if (!bounds || Math.round(bounds.width) !== frameSpec.cssWidth ||
      Math.round(bounds.height) !== frameSpec.cssHeight) {
    throw new Error(`${template}: expected a ${frameSpec.cssWidth} × ${frameSpec.cssHeight} CSS artboard, got ${JSON.stringify(bounds)}`);
  }
  const configured = await page.evaluate((values) => {
    if (typeof window.configureTemplate !== "function") {
      throw new Error("editor must expose window.configureTemplate(props)");
    }
    return window.configureTemplate(values);
  }, props);
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const layoutReport = await page.evaluate(() => {
    if (typeof window.getLayoutReport === "function") return window.getLayoutReport();
    return typeof window.layoutReport === "function" ? window.layoutReport() : null;
  }) || configured;
  if (!layoutReport) throw new Error(`${template}: editor returned no layout report`);
  if (layoutReport.outOfBounds?.length) {
    throw new Error(`${template}: HTML layout has off-canvas elements: ${JSON.stringify(layoutReport.outOfBounds)}`);
  }
  if (layoutReport.stackOverlaps?.length) {
    throw new Error(`${template}: text rows overlap inside a declared stack: ${JSON.stringify(layoutReport.stackOverlaps)}`);
  }
  const contrast = layoutReport.inkOnLimeContrast ?? layoutReport.inkOnPaperContrast ?? layoutReport.contrast;
  if (contrast === undefined || !Number.isFinite(Number(contrast))) {
    throw new Error(`${template}: editor must report a text/background contrast ratio`);
  }
  const contrastException = layoutReport.contrastException;
  const exceptionIsValid = contrastException &&
    Number.isFinite(Number(contrastException.minimum)) &&
    Number(contrastException.minimum) >= 1 &&
    typeof contrastException.rationale === "string" &&
    contrastException.rationale.trim().length >= 24;
  if (Number.isFinite(Number(contrast)) && Number(contrast) < 4.5 &&
      !(exceptionIsValid && Number(contrast) >= Number(contrastException.minimum))) {
    throw new Error(`${template}: text contrast is below 4.5:1: ${contrast}`);
  }
  if (layoutReport.noteOnPaperContrast !== undefined &&
      Number(layoutReport.noteOnPaperContrast) < 4.5) {
    throw new Error(`${template}: note contrast is below 4.5:1: ${layoutReport.noteOnPaperContrast}`);
  }
  const accentContrast = layoutReport.accentOnPaperContrast;
  if (accentContrast !== undefined && Number(accentContrast) < 4.5) {
    throw new Error(`${template}: accent contrast is below 4.5:1: ${accentContrast}`);
  }
  const reviewWarnings = [];
  if (Number.parseFloat(layoutReport.headlineFontSize || "0") < 38) {
    const warning = `headline is below the 38 CSS px legibility floor: ${layoutReport.headlineFontSize}`;
    if (props.reviewMode) reviewWarnings.push(warning);
    else throw new Error(`${template}: ${warning}`);
  }
  await frame.screenshot({ path: out, scale: "device" });
  const report = {
    renderer: "HTML/CSS + headless Chromium",
    browser: browser.version(),
    template,
    source,
    ratio,
    exportPixels: { width: frameSpec.width, height: frameSpec.height },
    font: font ? path.resolve(font) : "editor default",
    labelFont: labelFont ? path.resolve(labelFont) : undefined,
    headline: props.headline ?? props.copy ?? "",
    descriptor: props.descriptor ?? "",
    body: props.body ?? "",
    badge: props.badge ?? "",
    fontClass: props.fontClass ?? "",
    reviewWarnings,
    layoutReport,
    output: out,
    outputBytes: (await stat(out)).size,
  };
  if (!process.argv.includes("--no-record")) {
    await writeFile(out.replace(/\.png$/i, ".json"), JSON.stringify(report, null, 2) + "\n");
  }
  console.log(JSON.stringify(report, null, 2));
} finally {
  await browser.close();
}
