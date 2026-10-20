#!/usr/bin/env node
import { chromium } from "playwright";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../../..");
const output = path.join(here, "output");
const displayFont = path.join(root, "font-factory/fonts/archive/Hexagreat/Hexagreat – Sport Display Font VT98G82/Hexagreat/OTF file/Hexagreat-Regular.otf");
const images = {
  source: path.join(output, "reference.png"),
  skia: path.join(output, "skia.png"),
  html: path.join(output, "html.png"),
};
const imageUrl = async (file) => `data:image/png;base64,${(await readFile(file)).toString("base64")}`;
await mkdir(output, { recursive: true });
await Promise.all([...Object.values(images), displayFont].map((file) => stat(file)));

const browser = await chromium.launch({
  executablePath: "/usr/bin/chromium",
  headless: true,
  args: ["--no-sandbox", "--allow-file-access-from-files"],
});
try {
  const page = await browser.newPage({ viewport: { width: 1920, height: 620 }, deviceScaleFactor: 1 });
  const [source, skia, html] = await Promise.all(Object.values(images).map(imageUrl));
  await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box}body{margin:0;background:#17191d;color:#f2f1ec;font:13px/1.45 system-ui,sans-serif}
    header{height:55px;display:flex;align-items:center;padding:0 18px;color:#d2d0c8;font-size:12px;letter-spacing:.12em;text-transform:uppercase}
    main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:0 12px 12px}
    figure{margin:0;min-width:0}figcaption{height:30px;padding:5px 2px;color:#c5c4c0;font-size:11px;letter-spacing:.06em;text-transform:uppercase}
    .frame{width:100%;aspect-ratio:3/2;background:#a92128;overflow:hidden}img{width:100%;height:100%;object-fit:contain;display:block}
  </style></head><body><header>stadiumposter32 · source fidelity study · 2400 × 1600</header><main>
    <figure><figcaption>Original · T21458_11</figcaption><div class="frame"><img src="${source}" alt="Original matchday poster"></div></figure>
    <figure><figcaption>Current Skia · same display face and copy</figcaption><div class="frame"><img src="${skia}" alt="Current Skia support image"></div></figure>
    <figure><figcaption>HTML/CSS · same display face and copy</figcaption><div class="frame"><img src="${html}" alt="HTML/CSS source-led support image"></div></figure>
  </main></body></html>`);
  await page.screenshot({ path: path.join(output, "comparison.png"), fullPage: true });

  const editor = path.join(root, "font-factory/support-html/templates/stadiumposter32/editor.html");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(pathToFileURL(editor).href, { waitUntil: "networkidle" });
  await page.locator("#font-file").setInputFiles(displayFont);
  await page.getByText(/loaded as the live display font/).waitFor();
  await page.evaluate(() => document.fonts.ready);
  const desktopLayout = await page.evaluate(() => window.getLayoutReport());
  if (desktopLayout.outOfBounds.length) throw new Error(`Desktop editor has off-canvas elements: ${JSON.stringify(desktopLayout.outOfBounds)}`);
  await page.screenshot({ path: path.join(output, "editor-desktop.png"), fullPage: true });

  const editToPaintMs = await page.evaluate(async () => {
    const input = document.querySelector('[name="lineTwo"]');
    const original = input.value;
    const start = performance.now();
    input.value = "TERRACE";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const elapsed = performance.now() - start;
    input.value = original;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    return Number(elapsed.toFixed(2));
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const mobileLayout = await page.evaluate(() => window.getLayoutReport());
  if (mobileLayout.outOfBounds.length) throw new Error(`Mobile editor has off-canvas elements: ${JSON.stringify(mobileLayout.outOfBounds)}`);
  await page.screenshot({ path: path.join(output, "editor-mobile.png"), fullPage: true });
  const result = { comparison: path.join(output, "comparison.png"), editor, browser: browser.version(), exportPixels: { width: 2400, height: 1600 }, editToPaintMs, desktopLayout, mobileLayout };
  await writeFile(path.join(output, "benchmark.json"), JSON.stringify(result, null, 2) + "\n");
  console.log(JSON.stringify(result, null, 2));
} finally {
  await browser.close();
}
