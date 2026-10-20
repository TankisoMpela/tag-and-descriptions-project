#!/usr/bin/env node
import { chromium } from "playwright";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../../..");
const output = path.join(here, "output");
const files = {
  source: path.join(root, "font-factory/support-references/T27485_08.jpg"),
  skia: path.join(output, "skia.png"),
  html: path.join(output, "html.png"),
};
await Promise.all(Object.values(files).map((file) => stat(file)));
const uri = async (file) => {
  const ext = path.extname(file).toLowerCase();
  const mime = ext === ".jpg" || ext === ".jpeg" ? "image/jpeg" : "image/png";
  return `data:${mime};base64,${(await readFile(file)).toString("base64")}`;
};

const browser = await chromium.launch({
  executablePath: "/usr/bin/chromium",
  headless: true,
  args: ["--no-sandbox", "--allow-file-access-from-files"],
});
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 620 }, deviceScaleFactor: 1 });
  const [source, skia, html] = await Promise.all(Object.values(files).map(uri));
  await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box}body{margin:0;background:#17191d;color:#f2f1ec;font:13px/1.45 system-ui,sans-serif}
    header{height:55px;display:flex;align-items:center;padding:0 18px;color:#d2d0c8;font-size:12px;letter-spacing:.12em;text-transform:uppercase}
    main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:0 12px 12px}
    figure{margin:0;min-width:0}figcaption{height:30px;padding:5px 2px;color:#c5c4c0;font-size:11px;letter-spacing:.08em;text-transform:uppercase}
    .frame{width:100%;aspect-ratio:3/2;background:#eee9df;display:grid;place-items:center;overflow:hidden}
    img{width:100%;height:100%;object-fit:contain;display:block}
    footer{padding:0 18px 16px;color:#aaa9a4;font-size:11px}
  </style></head><body><header>crest32 · source-fit review · 2400 × 1600 output</header><main>
    <figure><figcaption>Original reference · T27485_08</figcaption><div class="frame"><img src="${source}" alt="Original Escape from Ordinary crest"></div></figure>
    <figure><figcaption>Current Skia · same font and copy</figcaption><div class="frame"><img src="${skia}" alt="Current Skia output"></div></figure>
    <figure><figcaption>HTML/CSS · no hero/arc overlap</figcaption><div class="frame"><img src="${html}" alt="HTML and CSS crest recreation"></div></figure>
  </main><footer>Both renderer outputs use the same local display font and copy.</footer></body></html>`);
  await page.screenshot({ path: path.join(output, "comparison.png"), fullPage: true });
  console.log(path.join(output, "comparison.png"));
} finally {
  await browser.close();
}
