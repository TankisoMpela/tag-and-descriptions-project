#!/usr/bin/env node

/**
 * Resumable Creative Fabrica Fonts category census.
 *
 * This intentionally collects category-card metadata only. It does not fetch
 * product pages, descriptions, images, reviews, or image bytes.
 *
 * Usage:
 *   node bin/collect_creative_fabrica_fonts.mjs \
 *     --out outputs/research/creative-fabrica-live-collector \
 *     --browser-url http://127.0.0.1:9223 --max-pages 10
 */

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import crypto from "node:crypto";
import { gzip } from "node:zlib";
import { promisify } from "node:util";
import Database from "better-sqlite3";
import { chromium } from "playwright";

const VERSION = "creative-fabrica-fonts-card-1.0.0";
const ROOT_URL = "https://www.creativefabrica.com/fonts/page/1/";
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const gzipAsync = promisify(gzip);
let stopping = false;
process.on("SIGINT", () => { stopping = true; });
process.on("SIGTERM", () => { stopping = true; });

function arg(name, fallback = null) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

function has(name) {
  return process.argv.includes(`--${name}`);
}

function isoNow() { return new Date().toISOString(); }

async function atomicJson(file, value) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const tmp = `${file}.tmp`;
  await fs.writeFile(tmp, `${JSON.stringify(value, null, 2)}\n`);
  await fs.rename(tmp, file);
}

async function writeRaw(file, body) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const tmp = `${file}.tmp`;
  await fs.writeFile(tmp, await gzipAsync(body, { level: 6 }));
  await fs.rename(tmp, file);
}

function parseArgs() {
  const out = arg("out", "outputs/research/creative-fabrica-live-collector");
  return {
    out,
    browserUrl: arg("browser-url", "http://127.0.0.1:9223"),
    startPage: Number(arg("start-page", "1")),
    maxPages: arg("max-pages") ? Number(arg("max-pages")) : null,
    delay: Number(arg("delay", "1000")),
    retries: Number(arg("retries", "3")),
    retryDelay: Number(arg("retry-delay", "10000")),
    fresh: has("fresh"),
  };
}

function initDb(db) {
  db.pragma("journal_mode = WAL");
  db.pragma("synchronous = FULL");
  db.pragma("foreign_keys = ON");
  db.exec(`
    CREATE TABLE IF NOT EXISTS crawl_runs (
      run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT,
      status TEXT NOT NULL, root_url TEXT NOT NULL, extractor_version TEXT NOT NULL,
      expected_total INTEGER, expected_pages INTEGER, pages_completed INTEGER DEFAULT 0,
      products_seen INTEGER DEFAULT 0, errors INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS crawl_pages (
      run_id TEXT NOT NULL, page INTEGER NOT NULL, url TEXT NOT NULL,
      status TEXT NOT NULL, fetched_at TEXT, http_status INTEGER,
      product_count INTEGER, reported_start INTEGER, reported_end INTEGER,
      reported_total INTEGER, sha256 TEXT, raw_path TEXT, error TEXT,
      attempts INTEGER DEFAULT 0, parser_version TEXT NOT NULL,
      PRIMARY KEY (run_id, page), FOREIGN KEY (run_id) REFERENCES crawl_runs(run_id)
    );
    CREATE TABLE IF NOT EXISTS raw_pages (
      run_id TEXT NOT NULL, page INTEGER NOT NULL, sha256 TEXT NOT NULL,
      raw_path TEXT NOT NULL, byte_count INTEGER NOT NULL,
      PRIMARY KEY (run_id, page), FOREIGN KEY (run_id) REFERENCES crawl_runs(run_id)
    );
    CREATE TABLE IF NOT EXISTS products (
      product_id TEXT, canonical_url TEXT PRIMARY KEY NOT NULL, title TEXT,
      slug TEXT, price_text TEXT, is_free INTEGER, category_text TEXT,
      page_first_seen INTEGER, page_last_seen INTEGER, first_seen_at TEXT NOT NULL,
      last_seen_at TEXT NOT NULL, source_run_id TEXT NOT NULL,
      FOREIGN KEY (source_run_id) REFERENCES crawl_runs(run_id)
    );
    CREATE TABLE IF NOT EXISTS product_tags (
      canonical_url TEXT NOT NULL, tag TEXT NOT NULL, source_run_id TEXT NOT NULL,
      PRIMARY KEY (canonical_url, tag), FOREIGN KEY (canonical_url) REFERENCES products(canonical_url)
    );
    CREATE INDEX IF NOT EXISTS idx_products_id ON products(product_id);
    CREATE INDEX IF NOT EXISTS idx_products_title ON products(title);
    CREATE INDEX IF NOT EXISTS idx_tags_tag ON product_tags(tag);
  `);
}

function extractPage(page) {
  return page.evaluate(() => {
    const body = document.body?.innerText || "";
    const shown = body.match(/Showing\s+(\d+)\s*-\s*(\d+)\s+of\s+([\d,]+)/i);
    const byUrl = new Map();
    const allFontsHeading = [...document.querySelectorAll("h2")].find((heading) => heading.innerText.trim() === "All Fonts");
    const listingRoot = allFontsHeading?.parentElement?.parentElement || document;
    for (const anchor of listingRoot.querySelectorAll("a[href]")) {
      const url = new URL(anchor.href, location.href);
      if (!url.pathname.startsWith("/product/")) continue;
      const canonical = `${url.origin}${url.pathname}`.replace(/\/$/, "/");
      const image = anchor.querySelector("img");
      let card = anchor;
      for (let i = 0; i < 4 && card.parentElement; i += 1) card = card.parentElement;
      const text = (card.innerText || "").replace(/\s+/g, " ").trim();
      const title = image?.alt?.trim() || anchor.innerText.trim() || text.split(" In ")[0].trim();
      const price = text.match(/(?:\$|€|£)[\d,.]+/)?.[0] || null;
      const isFree = /\$0\.00|€0\.00|£0\.00|free/i.test(text) ? 1 : 0;
      const category = [...card.querySelectorAll("a[href]")]
        .map((a) => a.innerText.trim()).find((value) => value && value !== title && value !== "Fonts") || null;
      const existing = byUrl.get(canonical);
      if (!existing || title.length > existing.title.length) {
        byUrl.set(canonical, { canonicalUrl: canonical, title, priceText: price, isFree, categoryText: category });
      }
    }
    const products = [...byUrl.values()];
    return {
      url: location.href,
      title: document.title,
      products,
      reportedStart: shown ? Number(shown[1]) : null,
      reportedEnd: shown ? Number(shown[2]) : null,
      reportedTotal: shown ? Number(shown[3].replaceAll(",", "")) : null,
    };
  });
}

async function waitForListing(page, expectedStart, timeoutMs = 45000) {
  const deadline = Date.now() + timeoutMs;
  const pattern = /Showing\s+(\d+)\s*-\s*(\d+)\s+of\s+([\d,]+)/i;
  while (Date.now() < deadline) {
    const text = await page.locator("body").innerText().catch(() => "");
    const match = text.match(pattern);
    if (match && Number(match[1]) === expectedStart) return;
    await page.waitForTimeout(500);
  }
  throw new Error(`listing marker not ready for start=${expectedStart}`);
}

async function main() {
  const options = parseArgs();
  const root = path.resolve(options.out);
  await fs.mkdir(root, { recursive: true });
  const dbPath = path.join(root, "creative-fabrica.db");
  if (options.fresh) await fs.rm(dbPath, { force: true });
  const db = new Database(dbPath);
  initDb(db);
  const statePath = path.join(root, "crawl-state.json");
  const rawDir = path.join(root, "raw", "category");
  const state = options.fresh ? {} : await fs.readFile(statePath, "utf8").then(JSON.parse).catch(() => ({}));
  const runId = state.runId || `${new Date().toISOString().replace(/[-:.TZ]/g, "")}-${crypto.randomBytes(3).toString("hex")}`;
  const run = db.prepare("SELECT * FROM crawl_runs WHERE run_id = ?").get(runId);
  if (!run) db.prepare("INSERT INTO crawl_runs (run_id,started_at,status,root_url,extractor_version) VALUES (?,?,?,?,?)")
    .run(runId, isoNow(), "running", ROOT_URL, VERSION);

  const browser = await chromium.connectOverCDP(options.browserUrl);
  const context = browser.contexts()[0];
  if (!context) throw new Error("No browser context found at --browser-url");
  // Prefer an already verified category tab; a fresh navigation can trigger a
  // new challenge even when the visible page already has valid HTML.
  let page = null;
  for (const candidate of context.pages()) {
    const text = await candidate.locator("body").innerText().catch(() => "");
    if (/Showing\s+\d+\s*-\s*\d+\s+of\s+[\d,]+/i.test(text)) {
      page = candidate;
      break;
    }
  }
  page ||= await context.newPage();
  await page.route("**/*", async (route) => {
    const type = route.request().resourceType();
    if (["image", "font", "media", "stylesheet"].includes(type)) return route.abort();
    return route.continue();
  });
  const completed = new Set(db.prepare("SELECT page FROM crawl_pages WHERE run_id = ? AND status = 'complete' AND parser_version = ?")
    .all(runId, VERSION).map((row) => row.page));
  const totalPages = state.expectedPages || null;
  let pageNumber = Math.max(options.startPage, state.nextPage || 1);
  const endPage = options.maxPages ? pageNumber + options.maxPages - 1 : Infinity;
  let paused = false;
  const commit = db.transaction((number, data, rawPath, rawSize, hash) => {
    const now = isoNow();
    for (const product of data.products) {
      const slug = product.canonicalUrl.split("/product/")[1]?.replace(/\/$/, "") || null;
      db.prepare(`INSERT INTO products
        (product_id,canonical_url,title,slug,price_text,is_free,category_text,page_first_seen,page_last_seen,first_seen_at,last_seen_at,source_run_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(canonical_url) DO UPDATE SET title=excluded.title,price_text=excluded.price_text,
        is_free=excluded.is_free,category_text=excluded.category_text,page_last_seen=excluded.page_last_seen,last_seen_at=excluded.last_seen_at`)
        .run(null, product.canonicalUrl, product.title || null, slug, product.priceText, product.isFree,
          product.categoryText, number, number, now, now, runId);
    }
    db.prepare(`INSERT INTO crawl_pages
      (run_id,page,url,status,fetched_at,http_status,product_count,reported_start,reported_end,reported_total,sha256,raw_path,attempts,parser_version)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(run_id,page) DO UPDATE SET status='complete',fetched_at=excluded.fetched_at,http_status=excluded.http_status,
      product_count=excluded.product_count,reported_start=excluded.reported_start,reported_end=excluded.reported_end,
      reported_total=excluded.reported_total,sha256=excluded.sha256,raw_path=excluded.raw_path,attempts=excluded.attempts,parser_version=excluded.parser_version,error=NULL`)
      .run(runId, number, data.url, "complete", now, 200, data.products.length, data.reportedStart,
        data.reportedEnd, data.reportedTotal, hash, rawPath, 1, VERSION);
    db.prepare("INSERT OR REPLACE INTO raw_pages (run_id,page,sha256,raw_path,byte_count) VALUES (?,?,?,?,?)")
      .run(runId, number, hash, rawPath, rawSize);
    db.prepare("UPDATE crawl_runs SET expected_total=COALESCE(expected_total,?),expected_pages=COALESCE(expected_pages,?),pages_completed=(SELECT COUNT(*) FROM crawl_pages WHERE run_id=? AND status='complete'),products_seen=(SELECT COUNT(*) FROM products WHERE source_run_id=?) WHERE run_id=?")
      .run(data.reportedTotal, data.reportedTotal ? Math.ceil(data.reportedTotal / 36) : null, runId, runId, runId);
  });

  try {
    while (pageNumber <= endPage && !stopping) {
      if (completed.has(pageNumber)) { pageNumber += 1; continue; }
      const url = `${ROOT_URL.replace(/page\/1\/$/, "")}page/${pageNumber}/`;
      let lastError;
      for (let attempt = 1; attempt <= options.retries; attempt += 1) {
        try {
          const expectedStart = (pageNumber - 1) * 36 + 1;
          const currentText = await page.locator("body").innerText().catch(() => "");
          const currentMarker = currentText.match(/Showing\s+(\d+)\s*-\s*(\d+)\s+of\s+([\d,]+)/i);
          if (page.url() !== url || !currentMarker || Number(currentMarker[1]) !== expectedStart) {
            await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
            await waitForListing(page, expectedStart);
          }
          const data = await extractPage(page);
          if (!data.reportedTotal || data.products.length === 0 || data.products.length > 100 ||
              data.reportedStart !== expectedStart) {
            throw new Error(`invalid page shape: products=${data.products.length}, total=${data.reportedTotal}`);
          }
          const raw = await page.content();
          const hash = crypto.createHash("sha256").update(raw).digest("hex");
          const rawPath = path.join(rawDir, `page-${String(pageNumber).padStart(6, "0")}-${hash.slice(0, 12)}.html.gz`);
          await writeRaw(rawPath, raw);
          commit(pageNumber, data, path.relative(root, rawPath), Buffer.byteLength(raw), hash);
          await atomicJson(statePath, { runId, nextPage: pageNumber + 1, expectedTotal: data.reportedTotal,
            expectedPages: Math.ceil(data.reportedTotal / 36), pagesCompleted: pageNumber, updatedAt: isoNow(), status: "running" });
          console.log(`[PAGE ${pageNumber}] ${data.products.length} products; total=${data.reportedTotal}`);
          lastError = null;
          break;
        } catch (error) {
          lastError = error;
          await sleep(Math.min(120000, options.retryDelay * attempt));
        }
      }
      if (lastError) {
        db.prepare("INSERT OR REPLACE INTO crawl_pages (run_id,page,url,status,error,attempts,parser_version) VALUES (?,?,?,?,?,?,?)")
          .run(runId, pageNumber, url, "error", String(lastError), options.retries, VERSION);
        db.prepare("UPDATE crawl_runs SET errors=errors+1 WHERE run_id=?").run(runId);
        console.error(`[ERROR page ${pageNumber}] ${lastError}`);
        await atomicJson(statePath, { runId, nextPage: pageNumber, expectedTotal: state.expectedTotal,
          expectedPages: state.expectedPages, pagesCompleted: pageNumber - 1, updatedAt: isoNow(), status: "paused" });
        paused = true;
        break;
      }
      pageNumber += 1;
      await sleep(options.delay);
    }
    const complete = paused ? "paused" : stopping ? "interrupted" : (options.maxPages ? "partial" : "complete");
    db.prepare("UPDATE crawl_runs SET status=?,finished_at=? WHERE run_id=?").run(complete, isoNow(), runId);
    await atomicJson(statePath, { ...state, runId, nextPage: pageNumber, updatedAt: isoNow(), status: complete });
  } finally {
    db.close();
  }
}

main().then(() => process.exit(0)).catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
