#!/usr/bin/env node
import { chromium } from "playwright";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../../..");
const output = path.join(here, "output");
const displayFont = "/usr/share/fonts/noto/NotoSans-CondensedBlack.ttf";
const labelFont = "/usr/share/fonts/Adwaita/AdwaitaSans-Regular.ttf";
const images = {
  source: path.join(root, "font-factory/support-references/T26074_03.jpg"),
  skia: path.join(output, "skia.png"),
  html: path.join(output, "html.png"),
};
const uri = async (file) => {
  const extension = path.extname(file).toLowerCase();
  const mime = extension === ".jpg" || extension === ".jpeg" ? "image/jpeg" : "image/png";
  return `data:${mime};base64,${(await readFile(file)).toString("base64")}`;
};
await Promise.all([...Object.values(images), displayFont, labelFont].map((file) => stat(file)));

const browser = await chromium.launch({
  executablePath: "/usr/bin/chromium",
  headless: true,
  args: ["--no-sandbox", "--allow-file-access-from-files"],
});
try {
  const page = await browser.newPage({ viewport: { width: 1920, height: 600 }, deviceScaleFactor: 1 });
  const [source, skia, html] = await Promise.all(Object.values(images).map(uri));
  await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box}body{margin:0;background:#17191d;color:#f2f1ec;font:13px/1.45 system-ui,sans-serif}
    header{height:55px;display:flex;align-items:center;padding:0 18px;color:#d2d0c8;font-size:12px;letter-spacing:.12em;text-transform:uppercase}
    main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:0 12px 12px}
    figure{margin:0;min-width:0}figcaption{height:30px;padding:5px 2px;color:#c5c4c0;font-size:11px;letter-spacing:.06em;text-transform:uppercase}
    .frame{width:100%;aspect-ratio:3/2;background:#efebcd;display:grid;place-items:center;overflow:hidden}
    img{width:100%;height:100%;object-fit:contain;display:block}
  </style></head><body><header>freakscene32 · source fidelity study · 2400 × 1600 output</header><main>
    <figure><figcaption>Original · T26074_03</figcaption><div class="frame"><img src="${source}" alt="Pink and yellow source poster"></div></figure>
    <figure><figcaption>Current Skia · same face; current copy</figcaption><div class="frame"><img src="${skia}" alt="Current Skia support image"></div></figure>
    <figure><figcaption>HTML/CSS · same face; source wording</figcaption><div class="frame"><img src="${html}" alt="Source-led HTML and CSS poster"></div></figure>
  </main></body></html>`);
  await page.screenshot({ path: path.join(output, "comparison.png"), fullPage: true });

  const editor = path.join(root, "font-factory/support-html/templates/freakscene32/editor.html");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(pathToFileURL(editor).href, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.locator("#font-file").setInputFiles(displayFont);
  await page.getByText(/loaded as the live display font/).waitFor();
  await page.locator("#label-font-file").setInputFiles(labelFont);
  await page.getByText(/loaded as the live label font/).waitFor();
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const desktopLayout = await page.evaluate(() => window.getLayoutReport());
  if (desktopLayout.outOfBounds.length) throw new Error(`Desktop editor has off-canvas elements: ${JSON.stringify(desktopLayout.outOfBounds)}`);
  await page.screenshot({ path: path.join(output, "editor-desktop.png"), fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const mobileLayout = await page.evaluate(() => window.getLayoutReport());
  if (mobileLayout.outOfBounds.length) throw new Error(`Mobile editor has off-canvas elements: ${JSON.stringify(mobileLayout.outOfBounds)}`);
  await page.screenshot({ path: path.join(output, "editor-mobile.png"), fullPage: true });
  console.log(JSON.stringify({ comparison: path.join(output, "comparison.png"), editor, desktopLayout, mobileLayout }, null, 2));
} finally {
  await browser.close();
}
