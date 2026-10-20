import { chromium } from "playwright";
import { mkdir, writeFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const out = path.resolve(process.argv[2] || path.join(here, "output"));
const url = process.argv[3] || "http://127.0.0.1:8812/font-factory/support-html/benchmarks/T26074-12/layout-editor.html";
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ executablePath: "/usr/bin/chromium", headless: true, args: ["--no-sandbox"] });
try {
  const page = await browser.newPage({ viewport: { width: 1520, height: 1024 }, deviceScaleFactor: 2 });
  const loadStart = performance.now();
  await page.goto(url, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(100);
  const pageLoadMs = performance.now() - loadStart;
  const fontReady = await page.evaluate(() => ({
    lilita: document.fonts.check('16px "Lilita One"'),
    noto: document.fonts.check('16px "Noto Condensed"'),
  }));
  const frame = page.locator("#artboard");
  await page.screenshot({ path: path.join(out, "editor.png") });
  await frame.evaluate(el => {
    Object.assign(el.style, {
      position: "fixed", left: "0", top: "0", width: "1200px",
      maxWidth: "none", margin: "0", zIndex: "2147483647",
    });
  });
  await page.evaluate(() => window.updateLayout());
  await page.evaluate(() => new Promise(requestAnimationFrame));
  const box = await frame.boundingBox();
  if (!box) throw new Error("HTML frame has no visible bounds");
  if (Math.abs(box.width / 1.5 - box.height) > 1) throw new Error(`Unexpected frame aspect ${box.width}x${box.height}`);
  const screenshotStart = performance.now();
  const preview = path.join(out, "browser-preview.png");
  await frame.screenshot({ path: preview });
  const screenshotMs = performance.now() - screenshotStart;
  const edits = await page.evaluate(async () => {
    async function measure(edit) {
      const started = performance.now();
      edit();
      await new Promise(requestAnimationFrame);
      await new Promise(requestAnimationFrame);
      return Number((performance.now() - started).toFixed(2));
    }
    const angle = document.querySelector("#angle");
    const copy = document.querySelector("#copy");
    const lime = document.querySelector("#lime");
    const angleMs = await measure(() => {
      angle.value = "-6";
      angle.dispatchEvent(new Event("input", { bubbles: true }));
    });
    const copyMs = await measure(() => {
      copy.value = "Find the signal\nfollow the rhythm\nkeep on moving.";
      copy.dispatchEvent(new Event("input", { bubbles: true }));
    });
    const colorMs = await measure(() => {
      lime.value = "#d6ec45";
      lime.dispatchEvent(new Event("input", { bubbles: true }));
    });
    return { anglePaintMs: angleMs, copyPaintMs: copyMs, colorPaintMs: colorMs };
  });
  const uploadStart = performance.now();
  await page.locator("#font-file").setInputFiles(path.join(here, "assets/NotoSans-CondensedExtraBold.ttf"));
  await page.getByText(/loaded as the live headline font/).waitFor();
  const uploadedFontMs = Number((performance.now() - uploadStart).toFixed(2));
  const edited = path.join(out, "browser-edited.png");
  const editScreenshotStart = performance.now();
  await frame.screenshot({ path: edited });
  const editedScreenshotMs = performance.now() - editScreenshotStart;
  const result = {
    url,
    browser: browser.version(),
    frameCssPixels: { width: box.width, height: box.height },
    frameExportPixels: { width: Math.round(box.width * 2), height: Math.round(box.height * 2) },
    fontsReady: fontReady,
    pageLoadAndFontMs: Number(pageLoadMs.toFixed(2)),
    editPaintMs: edits,
    localFontUploadAndPaintMs: uploadedFontMs,
    fullSizeScreenshotMs: Number(screenshotMs.toFixed(2)),
    editedScreenshotMs: Number(editedScreenshotMs.toFixed(2)),
    finalFiles: Object.fromEntries(await Promise.all([preview, edited, path.join(out, "editor.png")].map(async f => [path.basename(f), (await stat(f)).size]))),
  };
  await writeFile(path.join(out, "benchmark.json"), JSON.stringify(result, null, 2) + "\n");
  console.log(JSON.stringify(result, null, 2));
} finally {
  await browser.close();
}
