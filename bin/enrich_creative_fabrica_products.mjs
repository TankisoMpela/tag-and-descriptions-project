#!/usr/bin/env node

/** Enrich products already discovered by collect_creative_fabrica_tags.mjs. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { gzip } from "node:zlib";
import { promisify } from "node:util";
import Database from "better-sqlite3";
import { chromium } from "playwright";

const VERSION = "creative-fabrica-pdp-enrichment-0.1.0";
const gzipAsync = promisify(gzip);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function arg(name, fallback = null) {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function now() { return new Date().toISOString(); }

async function writeRaw(file, body) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const compressed = await gzipAsync(body, { level: 6 });
  const temporary = `${file}.tmp`;
  await fs.writeFile(temporary, compressed);
  await fs.rename(temporary, file);
  return crypto.createHash("sha256").update(body).digest("hex");
}

function initDb(db) {
  db.pragma("journal_mode = WAL");
  db.pragma("synchronous = FULL");
  db.pragma("foreign_keys = ON");
  db.exec(`
    CREATE TABLE IF NOT EXISTS product_snapshots (
      snapshot_id INTEGER PRIMARY KEY,
      run_id TEXT NOT NULL REFERENCES crawl_runs(run_id),
      product_id INTEGER NOT NULL REFERENCES products(product_id),
      title TEXT,
      designer_name TEXT,
      designer_url TEXT,
      category_name TEXT,
      subcategory_name TEXT,
      category_path TEXT,
      price_text TEXT,
      access_mode TEXT,
      is_free INTEGER,
      is_subscription INTEGER,
      favorites_count INTEGER,
      publication_date TEXT,
      update_date TEXT,
      structured_data_json TEXT,
      extraction_status TEXT NOT NULL,
      observed_at TEXT NOT NULL,
      UNIQUE(run_id, product_id)
    );
    CREATE TABLE IF NOT EXISTS product_pdp_tags (
      run_id TEXT NOT NULL REFERENCES crawl_runs(run_id),
      product_id INTEGER NOT NULL REFERENCES products(product_id),
      tag_id INTEGER NOT NULL REFERENCES tags(tag_id),
      position_on_pdp INTEGER,
      PRIMARY KEY(run_id, product_id, tag_id)
    );
    CREATE TABLE IF NOT EXISTS enrichment_errors (
      run_id TEXT NOT NULL REFERENCES crawl_runs(run_id),
      product_id INTEGER NOT NULL REFERENCES products(product_id),
      url TEXT NOT NULL,
      attempts INTEGER NOT NULL,
      error_message TEXT NOT NULL,
      created_at TEXT NOT NULL,
      PRIMARY KEY(run_id, product_id)
    );
  `);
}

async function extractProduct(page) {
  return page.evaluate(() => {
    const body = document.body?.innerText || "";
    const h1 = document.querySelector("h1")?.innerText.trim() || null;
    const links = [...document.querySelectorAll("a[href]")];
    const designer = links.find((a) => /\/designer\//.test(new URL(a.href, location.href).pathname));
    const fontLinks = links.filter((a) => /^\/fonts\//.test(new URL(a.href, location.href).pathname));
    const categoryPath = [...new Map(fontLinks.map((a) => [a.href, a.innerText.trim()])).values()]
      .filter(Boolean).slice(0, 3);
    const favoriteMatch = body.match(/([\d,]+)\s*X\s*ADDED TO FAVORITES/i);
    const priceMatch = body.match(/(?:FREE\s*\([^\n]*\)|(?:USD|EUR|GBP)?\s*[\$€£]\s*[\d,.]+)/i);
    const tagHeading = [...document.querySelectorAll("h1,h2,h3,h4")]
      .find((heading) => /designer tags/i.test(heading.innerText));
    const tagRoot = tagHeading?.parentElement?.nextElementSibling || document;
    const tags = [...tagRoot.querySelectorAll('a[href*="/tag/"]')]
      .map((a) => ({ name: a.innerText.trim(), url: a.href }))
      .filter((tag) => tag.name && /^https:\/\/www\.creativefabrica\.com\/tag\/[^/?]+\/$/.test(tag.url));
    const jsonLd = [...document.querySelectorAll('script[type="application/ld+json"]')]
      .map((script) => { try { return JSON.parse(script.textContent); } catch { return null; } })
      .filter(Boolean);
    return {
      url: location.href,
      title: h1,
      designerName: designer?.innerText.trim() || null,
      designerUrl: designer?.href || null,
      categoryPath,
      priceText: priceMatch?.[0] || null,
      isFree: /DOWNLOAD FOR FREE|FREE\s*\(\s*\$?0/i.test(body) ? 1 : 0,
      isSubscription: /only available as part of our subscription|subscription only/i.test(body) ? 1 : 0,
      favorites: favoriteMatch ? Number(favoriteMatch[1].replaceAll(",", "")) : null,
      tags,
      jsonLd,
    };
  });
}

async function main() {
  const out = path.resolve(arg("out", "outputs/research/creative-fabrica-tag-first-collector"));
  const db = new Database(path.join(out, "creative-fabrica-tags.db"));
  initDb(db);
  const browser = await chromium.connectOverCDP(arg("browser-url", "http://127.0.0.1:9223"));
  const context = browser.contexts()[0];
  if (!context) throw new Error("No browser context found");
  const page = await context.newPage();
  const runId = `${Date.now()}-${crypto.randomBytes(3).toString("hex")}`;
  db.prepare("INSERT INTO crawl_runs (run_id,started_at,status,parser_version,notes) VALUES (?,?,?,?,?)")
    .run(runId, now(), "running", VERSION, "PDP enrichment");
  const products = db.prepare(`SELECT product_id,canonical_url FROM products
    WHERE product_id NOT IN (SELECT product_id FROM product_snapshots WHERE extraction_status='COMPLETE')
    ORDER BY product_id LIMIT ?`).all(Number(arg("max-products", "1000000")));
  const upsertTag = db.prepare(`INSERT INTO tags
    (canonical_slug,canonical_url,display_name,first_seen_at,last_seen_at)
    VALUES (?,?,?,?,?) ON CONFLICT(canonical_url) DO UPDATE SET display_name=excluded.display_name,last_seen_at=excluded.last_seen_at`);
  const findTag = db.prepare("SELECT tag_id FROM tags WHERE canonical_url=?");
  const insertSnapshot = db.prepare(`INSERT OR REPLACE INTO product_snapshots
    (run_id,product_id,title,designer_name,designer_url,category_name,subcategory_name,category_path,
     price_text,access_mode,is_free,is_subscription,favorites_count,structured_data_json,extraction_status,observed_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`);
  const insertPdpTag = db.prepare(`INSERT OR REPLACE INTO product_pdp_tags
    (run_id,product_id,tag_id,position_on_pdp) VALUES (?,?,?,?)`);
  const rawDir = path.join(out, "raw", "products");
  let completed = 0;
  for (const product of products) {
    let result = null;
    let error = null;
    for (let attempt = 1; attempt <= Number(arg("retries", "3")); attempt += 1) {
      try {
        await page.goto(product.canonical_url, { waitUntil: "domcontentloaded", timeout: 60000 });
        await page.locator("h1").first().waitFor({ state: "visible", timeout: 30000 });
        result = await extractProduct(page);
        if (!result.title) throw new Error("missing product title");
        break;
      } catch (caught) {
        error = caught;
        await sleep(Number(arg("retry-delay", "10000")) * attempt);
      }
    }
    if (!result) {
      db.prepare(`INSERT OR REPLACE INTO enrichment_errors
        (run_id,product_id,url,attempts,error_message,created_at) VALUES (?,?,?,?,?,?)`)
        .run(runId, product.product_id, product.canonical_url, Number(arg("retries", "3")), String(error?.message || error), now());
      console.error(`[pdp] FAILED ${product.canonical_url}: ${error?.message}`);
      continue;
    }
    const rawPath = path.join(rawDir, `${String(product.product_id).padStart(8, "0")}.html.gz`);
    const rawHash = await writeRaw(rawPath, await page.content());
    const pathParts = result.categoryPath;
    insertSnapshot.run(runId, product.product_id, result.title, result.designerName, result.designerUrl,
      pathParts[0] || null, pathParts[1] || null, pathParts.join(" > ") || null, result.priceText,
      result.isSubscription ? "subscription" : result.isFree ? "free" : "paid_or_unknown",
      result.isFree, result.isSubscription, result.favorites, JSON.stringify({ rawHash, data: result.jsonLd }),
      "COMPLETE", now());
    for (let index = 0; index < result.tags.length; index += 1) {
      const tag = result.tags[index];
      const slug = new URL(tag.url).pathname.split("/").filter(Boolean).pop();
      upsertTag.run(slug, tag.url, tag.name, now(), now());
      insertPdpTag.run(runId, product.product_id, findTag.get(tag.url).tag_id, index + 1);
    }
    completed += 1;
    console.log(`[pdp] ${completed}/${products.length} ${product.canonical_url} favorites=${result.favorites ?? "unknown"} tags=${result.tags.length}`);
    await sleep(Number(arg("delay", "1500")));
  }
  const failed = db.prepare("SELECT COUNT(*) AS count FROM enrichment_errors WHERE run_id=?").get(runId).count;
  const status = failed ? "INCOMPLETE" : "COMPLETE";
  db.prepare("UPDATE crawl_runs SET status=?,finished_at=? WHERE run_id=?").run(status, now(), runId);
  console.log(JSON.stringify({ runId, status, attempted: products.length, completed, failed }, null, 2));
  await browser.close().catch(() => {});
  db.close();
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
