#!/usr/bin/env node
import { chromium } from "playwright";
import { createHash } from "node:crypto";
import { mkdir, readdir, rm, stat, writeFile, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "../..");
const argv = process.argv.slice(2);
const option = (name, fallback = null) => {
  const index = argv.indexOf(name);
  return index >= 0 ? argv[index + 1] : fallback;
};
const mode = option("--mode", "review");
const overwrite = argv.includes("--overwrite");
const positionalOut = argv[0] && !argv[0].startsWith("--") ? argv[0] : null;
const reviewDate = new Date().toISOString().slice(0, 10);
const out = path.resolve(option("--out", positionalOut || path.join(repo, `outputs/pinterest-template-review-${reviewDate}`)));
const fontPath = option("--font") ? path.resolve(option("--font")) : null;
const fontName = option("--font-name", "");
if (!["review", "pins"].includes(mode)) throw new Error(`Unknown render mode: ${mode}`);
if (mode === "pins" && (!fontPath || !fontName.trim())) throw new Error("--mode pins requires --font and --font-name");
const pageSource = path.join(here, "editor.html");
const ids = ["hero", "set", "wall", "full_stack", "studio_cover", "specimen_mosaic", "initials", "knotband", "scriptorium", "carol", "illuminated_broadside", "scribe_gallery", "crest", "bib", "lane", "finish", "timer", "guide", "trace", "letter_study", "coffee_roaster", "punk_manifesto", "neon_overprint"];
const extensions = { hero: "png", set: "png", full_stack: "jpg", specimen_mosaic: "png", knotband: "png", bib: "png", finish: "png", lane: "jpg", timer: "png" };
const classes = {
  elegant: new Set(["hero", "set", "wall", "full_stack", "studio_cover", "specimen_mosaic"]),
  blackletter: new Set(["initials", "knotband", "scriptorium", "carol", "illuminated_broadside", "scribe_gallery"]),
  sports: new Set(["crest", "bib", "lane", "finish", "timer"]),
  script: new Set(["guide", "trace", "letter_study"]),
};
const className = (id) => Object.entries(classes).find(([, ids]) => ids.has(id))?.[0] || "reference-inspired";
const sourceFor = {
  coffee_roaster: "references/coffee-roaster.jpg",
  punk_manifesto: "references/born-broke.jpg",
  neon_overprint: "references/neon-script.jpg",
};

await mkdir(out, { recursive: true });
const expectedOutputs = mode === "pins"
  ? [...ids.map((_, i) => `pinterest_${i + 1}.jpg`), "pinterest-template-manifest.json"]
  : [...ids.map((id) => `${id}.${extensions[id] || "jpg"}`), "render-manifest.json", "index.html"];
const existing = new Map((await readdir(out, { withFileTypes: true })).map((entry) => [entry.name, entry]));
const managedOutputs = new Set(expectedOutputs);
if (mode === "pins") {
  for (const name of existing.keys()) {
    if (/^pinterest_\d+\.(?:png|jpe?g)$/iu.test(name)) managedOutputs.add(name);
  }
}
const collisions = [...managedOutputs].filter((name) => existing.has(name));
if (collisions.length && !overwrite) {
  throw new Error(`Output already contains renderer-managed files. Choose a new --out folder or pass --overwrite:\n${collisions.join("\n")}`);
}
for (const name of collisions) {
  if (!existing.get(name).isFile()) throw new Error(`Refusing to replace non-file output: ${path.join(out, name)}`);
  await rm(path.join(out, name));
}

const browser = await chromium.launch({
  ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
    ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH }
    : {}),
  headless: true,
  args: ["--no-sandbox", "--allow-file-access-from-files"],
});
const records = [];
try {
  const page = await browser.newPage({ viewport: { width: 1100, height: 1600 }, deviceScaleFactor: 1 });
  const sourceFontHash = mode === "pins" ? createHash("sha256").update(await readFile(fontPath)).digest("hex") : null;
  const pinRecords = [];
  for (const id of ids) {
    const editor = path.join(here, "templates", id, "editor.html");
    await page.goto(pathToFileURL(editor).href, { waitUntil: "networkidle" });
    const board = page.locator("#artboard");
    await board.evaluate((node) => Object.assign(node.style, { position: "fixed", left: "0", top: "0", width: "1000px", height: "1500px", maxWidth: "none", margin: "0", zIndex: "2147483647" }));
    await page.evaluate(() => document.fonts.ready);
    let configured;
    if (mode === "pins") {
      await page.locator("#font-file").setInputFiles(fontPath);
      await page.waitForFunction(() => document.body.dataset.uploadedFont === "PinLive", null, { timeout: 15000 });
      await page.evaluate(() => document.fonts.ready);
      const preserveBrand = ["coffee_roaster", "punk_manifesto", "neon_overprint"].includes(id);
      configured = await page.evaluate(({ values }) => window.configureTemplate(values), {
        values: { fontName, production: true, ...(preserveBrand ? {} : { name: fontName }) },
      });
    } else {
      await page.evaluate(() => window.configureTemplate({}));
      configured = await page.evaluate(() => window.configureTemplate({}));
    }
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const report = await page.evaluate(() => window.getLayoutReport());
    const contrast = report.inkOnPaperContrast;
    if (mode === "pins" && (report.outOfBounds.length || report.stackOverlaps.length)) {
      throw new Error(`${id}: layout validation failed (bounds=${report.outOfBounds.join(",")}; overlaps=${report.stackOverlaps.join(",")})`);
    }
    if (report.outOfBounds.length || report.stackOverlaps.length) {
      console.warn(`${id}: bounds=${report.outOfBounds.join(",")} overlaps=${report.stackOverlaps.join(",")}`);
    }
    const ext = mode === "pins" ? "jpg" : extensions[id] || "jpg";
    const index = mode === "pins" ? pinRecords.length + 1 : null;
    const file = mode === "pins" ? `pinterest_${index}.jpg` : `${id}.${ext}`;
    const dest = path.join(out, file);
    if (mode === "pins") {
      let quality = 92;
      for (const candidate of [92, 88, 84, 80, 76, 72, 68, 64, 60, 55, 50]) {
        quality = candidate;
        await board.screenshot({ path: dest, type: "jpeg", quality });
        if ((await stat(dest)).size <= 200000) break;
      }
      const bytes = (await stat(dest)).size;
      if (bytes > 200000) throw new Error(`${file} is ${bytes} bytes after JPEG quality ladder`);
      pinRecords.push({ index, template: id, file, width: 1000, height: 1500, bytes, quality, sha256: createHash("sha256").update(await readFile(dest)).digest("hex"), layout: report });
      console.log(`${file} · ${id} · ${bytes} bytes · q${quality}`);
      continue;
    }
    await board.screenshot({ path: dest, type: ext === "jpg" ? "jpeg" : "png", quality: ext === "jpg" ? 94 : undefined });
    const metadata = await page.evaluate(() => ({
      title: document.querySelector("#studio-title")?.textContent || "",
      props: window.configureTemplate({}).props || {},
    }));
    const info = await stat(dest);
    records.push({ template: id, class: className(id), title: metadata.title, font: ({ elegant: "Maidega", blackletter: "Esviga", sports: "Opengsa", script: "Regality Script", "reference-inspired": ({ coffee_roaster: "Maidega", invest_poster: "Opengsa", punk_manifesto: "Opengsa", green_starburst: "Opengsa", neon_overprint: "Regality Script" })[id] })[className(id)], kind: sourceFor[id] ? "reference-inspired" : "ported", source: sourceFor[id] || `Skia template: ${id}`, file, width: 1000, height: 1500, bytes: info.size, layout: report, contrast, editor: `../../font-factory/pin-html/templates/${id}/editor.html` });
    console.log(`${file} · ${info.size} bytes`);
  }
  if (mode === "pins") {
    if (pinRecords.length !== ids.length) throw new Error(`Rendered ${pinRecords.length}/${ids.length} active Pinterest templates`);
    const manifest = { schema: 1, kind: "font-template-pinterest-pins", font_name: fontName, font_source: path.basename(fontPath), font_sha256: sourceFontHash, canvas: [1000, 1500], renderer: "HTML/CSS + headless Chromium", template_count: pinRecords.length, images: pinRecords };
    await writeFile(path.join(out, "pinterest-template-manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
    console.log(`[PASS] rendered ${pinRecords.length} template Pinterest pins for ${fontName}: ${out}`);
  }
  if (mode === "review") {
    const manifest = { title: "Pinterest Template Review — HTML/CSS Port", canvas: [1000, 1500], renderer: "HTML/CSS + headless Chromium", renderCount: records.length, droppedFromReview: ["copybook.jpg", "folio.png", "garden_note.png", "invest_poster.jpg", "jersey_panel.png", "markup.jpg", "reliquary_seal.jpg", "sample.jpg", "scoreboard_split.png", "wordmark_atelier.png", "green_starburst.jpg", "phrase.png"], images: records };
    await writeFile(path.join(out, "render-manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
    const cards = records.map((r) => `<article class="card" data-class="${r.class}"><a href="${r.file}" target="_blank"><img src="${r.file}" alt="${r.title}"></a><div class="card-copy"><span>${r.class.replaceAll("-", " ")}</span><h2>${r.title}</h2><p>${r.file} · <a href="${r.editor}">Open Editable Layout</a></p></div></article>`).join("\n");
    const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${manifest.title}</title><style>*{box-sizing:border-box}body{margin:0;background:#131517;color:#f2eee7;font:15px/1.45 system-ui,"Segoe UI",sans-serif}.head{padding:30px clamp(20px,4vw,64px) 24px;border-bottom:1px solid #383b40}.head p{margin:7px 0 0;color:#acb0b5}.head h1{margin:0;font-size:clamp(24px,3vw,38px);letter-spacing:-.04em}.controls{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}.controls button{border:1px solid #4b4e52;border-radius:999px;padding:7px 13px;background:#202327;color:#eee9df;font:inherit;cursor:pointer}.controls button[aria-pressed="true"]{background:#efe7d6;color:#24201b;border-color:#efe7d6}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:18px;padding:24px clamp(20px,4vw,64px) 56px}.card{overflow:hidden;border:1px solid #34383d;background:#1a1d20}.card img{display:block;width:100%;height:auto;aspect-ratio:2/3;object-fit:cover;background:#25272b}.card-copy{padding:12px 13px 14px}.card-copy span{color:#d89a6c;font-size:12px;letter-spacing:.09em;text-transform:uppercase}.card-copy h2{margin:5px 0 2px;font-size:16px;font-weight:600}.card-copy p{margin:0;color:#a9acb0;font-size:13px}.card-copy a{color:#e5b786;text-decoration:none}.card-copy a:hover{text-decoration:underline}.note{padding:0 clamp(20px,4vw,64px) 8px;color:#a9acb0;font-size:13px}@media(max-width:520px){.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.card-copy{padding:9px}.card-copy h2{font-size:13px}}</style></head><body><header class="head"><h1>${manifest.title}</h1><p>${records.length} individual 1000 × 1500 compositions. Open any image full size, or open its editable browser layout.</p><nav class="controls" aria-label="Filter templates"><button data-filter="all" aria-pressed="true">All ${records.length}</button><button data-filter="elegant">Elegant</button><button data-filter="blackletter">Blackletter</button><button data-filter="sports">Sports</button><button data-filter="script">Script</button><button data-filter="reference-inspired">New Reference Layouts</button></nav></header><p class="note">Twelve requested variants are excluded from this review folder. Source implementations remain in the library.</p><main class="grid">${cards}</main><script>document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-filter]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.querySelectorAll('.card').forEach(c=>c.hidden=b.dataset.filter!=='all'&&c.dataset.class!==b.dataset.filter)}));</script></body></html>`;
    await writeFile(path.join(out, "index.html"), html);
  }
} finally { await browser.close(); }
