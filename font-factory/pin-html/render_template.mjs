#!/usr/bin/env node
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const id = process.argv[2];
const target = path.resolve(process.argv[3] || `/tmp/${id || "pin"}.png`);
if (!id) throw new Error("Usage: node render_template.mjs <template-id> [output.png]");
const editor = path.join(here, "templates", id, "editor.html");
const browser = await chromium.launch({ executablePath: "/usr/bin/chromium", headless: true, args: ["--no-sandbox", "--allow-file-access-from-files"] });
try {
  const page = await browser.newPage({ viewport: { width: 1100, height: 1600 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(editor).href, { waitUntil: "networkidle" });
  const board = page.locator("#artboard");
  await board.evaluate((node) => Object.assign(node.style, { position: "fixed", left: "0", top: "0", width: "1000px", height: "1500px", maxWidth: "none", margin: "0", zIndex: "2147483647" }));
  await page.evaluate(() => window.configureTemplate({}));
  await page.evaluate(() => document.fonts.ready);
  const report = await page.evaluate(() => window.configureTemplate({}));
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  await mkdir(path.dirname(target), { recursive: true });
  const jpeg = target.toLowerCase().endsWith(".jpg") || target.toLowerCase().endsWith(".jpeg");
  await board.screenshot({ path: target, type: jpeg ? "jpeg" : "png", ...(jpeg ? { quality: 94 } : {}) });
  console.log(JSON.stringify({ template: id, output: target, report }, null, 2));
} finally {
  await browser.close();
}
