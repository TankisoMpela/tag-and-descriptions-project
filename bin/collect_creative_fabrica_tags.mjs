#!/usr/bin/env node

/**
 * Creative Fabrica tag-first reconnaissance collector.
 *
 * This is intentionally separate from collect_creative_fabrica_fonts.mjs.
 * It records public tag-directory and tag-route evidence, product URLs,
 * titles, displayed totals, and route positions. Product-page enrichment is
 * a later stage.
 *
 * Example bounded run:
 *   node bin/collect_creative_fabrica_tags.mjs \
 *     --out outputs/research/creative-fabrica-tag-first-collector \
 *     --browser-url http://127.0.0.1:9223 \
 *     --directory-pages 1 \
 *     --tag retro-script-font --tag-pages 1
 */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { gzip } from "node:zlib";
import { promisify } from "node:util";
import Database from "better-sqlite3";
import { chromium } from "playwright";

const VERSION = "creative-fabrica-tag-first-0.1.0";
const TAG_ROOT = "https://www.creativefabrica.com/tag/";
const gzipAsync = promisify(gzip);
let stopping = false;
process.on("SIGINT", () => { stopping = true; });
process.on("SIGTERM", () => { stopping = true; });

function arg(name, fallback = null) {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function args(name) {
  const values = [];
  for (let i = 0; i < process.argv.length; i += 1) {
    if (process.argv[i] === `--${name}` && process.argv[i + 1]) values.push(process.argv[i + 1]);
  }
  return values;
}

function has(name) { return process.argv.includes(`--${name}`); }
function now() { return new Date().toISOString(); }
function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function canonicalUrl(value, expectedPrefix = null) {
  try {
    const url = new URL(value, TAG_ROOT);
    url.hash = "";
    for (const key of [...url.searchParams.keys()]) {
      if (/^(utm_|ref$|source$|campaign$|affiliate)/i.test(key)) url.searchParams.delete(key);
    }
    if (expectedPrefix && !url.pathname.startsWith(expectedPrefix)) return null;
    return `${url.origin}${url.pathname}`.replace(/\/{2,}$/g, "/");
  } catch {
    return null;
  }
}

async function atomicJson(file, value) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const temporary = `${file}.tmp`;
  await fs.writeFile(temporary, `${JSON.stringify(value, null, 2)}\n`);
  await fs.rename(temporary, file);
}

async function writeRaw(file, html) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const compressed = await gzipAsync(html, { level: 6 });
  const temporary = `${file}.tmp`;
  await fs.writeFile(temporary, compressed);
  await fs.rename(temporary, file);
  return { sha256: crypto.createHash("sha256").update(html).digest("hex"), byteCount: compressed.length };
}

function initDb(db) {
  db.pragma("journal_mode = WAL");
  db.pragma("synchronous = FULL");
  db.pragma("foreign_keys = ON");
  db.exec(`
    CREATE TABLE IF NOT EXISTS crawl_runs (
      run_id TEXT PRIMARY KEY,
      started_at TEXT NOT NULL,
      finished_at TEXT,
      status TEXT NOT NULL,
      parser_version TEXT NOT NULL,
      notes TEXT
    );
    CREATE TABLE IF NOT EXISTS raw_documents (
      raw_id INTEGER PRIMARY KEY,
      run_id TEXT NOT NULL REFERENCES crawl_runs(run_id),
      url TEXT NOT NULL,
      final_url TEXT,
      document_type TEXT NOT NULL,
      http_status INTEGER,
      content_hash TEXT NOT NULL,
      storage_path TEXT NOT NULL,
      fetched_at TEXT NOT NULL,
      UNIQUE(run_id, url, content_hash)
    );
    CREATE TABLE IF NOT EXISTS directory_pages (
      run_id TEXT NOT NULL REFERENCES crawl_runs(run_id),
      page_number INTEGER NOT NULL,
      requested_url TEXT NOT NULL,
      final_url TEXT,
      discovered_tag_count INTEGER NOT NULL DEFAULT 0,
      discovered_pagination_count INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL,
      content_hash TEXT,
      fetched_at TEXT NOT NULL,
      PRIMARY KEY(run_id, page_number)
    );
    CREATE TABLE IF NOT EXISTS crawl_errors (
      error_id INTEGER PRIMARY KEY,
      run_id TEXT NOT NULL REFERENCES crawl_runs(run_id),
      url TEXT NOT NULL,
      entity_type TEXT NOT NULL,
      entity_key TEXT,
      page_number INTEGER,
      attempt_number INTEGER NOT NULL,
      error_class TEXT NOT NULL,
      error_message TEXT NOT NULL,
      created_at TEXT NOT NULL,
      resolved_at TEXT
    );
    CREATE TABLE IF NOT EXISTS tags (
      tag_id INTEGER PRIMARY KEY,
      canonical_slug TEXT NOT NULL UNIQUE,
      canonical_url TEXT NOT NULL UNIQUE,
      display_name TEXT,
      first_seen_at TEXT NOT NULL,
      last_seen_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS tag_pages (
      run_id TEXT NOT NULL REFERENCES crawl_runs(run_id),
      tag_id INTEGER NOT NULL REFERENCES tags(tag_id),
      sort_mode TEXT NOT NULL,
      page_number INTEGER NOT NULL,
      requested_url TEXT NOT NULL,
      final_url TEXT,
      displayed_start INTEGER,
      displayed_end INTEGER,
      displayed_total INTEGER,
      observed_card_count INTEGER,
      unique_product_count INTEGER,
      duplicate_card_count INTEGER,
      status TEXT NOT NULL,
      content_hash TEXT,
      fetched_at TEXT NOT NULL,
      PRIMARY KEY(run_id, tag_id, sort_mode, page_number)
    );
    CREATE TABLE IF NOT EXISTS tag_crawl_status (
      run_id TEXT NOT NULL REFERENCES crawl_runs(run_id),
      tag_id INTEGER NOT NULL REFERENCES tags(tag_id),
      sort_mode TEXT NOT NULL,
      expected_pages INTEGER,
      successful_pages INTEGER NOT NULL,
      failed_pages INTEGER NOT NULL,
      observed_total INTEGER,
      total_values TEXT,
      status TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      PRIMARY KEY(run_id, tag_id, sort_mode)
    );
    CREATE TABLE IF NOT EXISTS products (
      product_id INTEGER PRIMARY KEY,
      canonical_url TEXT NOT NULL UNIQUE,
      current_title TEXT,
      first_seen_at TEXT NOT NULL,
      last_seen_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS product_tags (
      product_id INTEGER NOT NULL REFERENCES products(product_id),
      tag_id INTEGER NOT NULL REFERENCES tags(tag_id),
      first_seen_run_id TEXT NOT NULL REFERENCES crawl_runs(run_id),
      last_seen_run_id TEXT NOT NULL REFERENCES crawl_runs(run_id),
      route_confirmed INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(product_id, tag_id)
    );
    CREATE TABLE IF NOT EXISTS product_route_observations (
      run_id TEXT NOT NULL REFERENCES crawl_runs(run_id),
      tag_id INTEGER NOT NULL REFERENCES tags(tag_id),
      product_id INTEGER NOT NULL REFERENCES products(product_id),
      sort_mode TEXT NOT NULL,
      page_number INTEGER NOT NULL,
      position_on_page INTEGER NOT NULL,
      global_position INTEGER NOT NULL,
      displayed_total INTEGER,
      PRIMARY KEY(run_id, tag_id, product_id, sort_mode)
    );
    CREATE INDEX IF NOT EXISTS idx_tag_pages_status ON tag_pages(status);
    CREATE INDEX IF NOT EXISTS idx_product_tags_tag ON product_tags(tag_id);
    CREATE INDEX IF NOT EXISTS idx_route_rank ON product_route_observations(tag_id, sort_mode, global_position);
  `);
}

function parseMarker(text) {
  const match = text.match(/Showing\s+(\d+)\s*[\u2013-]\s*(\d+)\s+of\s+([\d,]+)\s+results?/i);
  return match ? {
    start: Number(match[1]),
    end: Number(match[2]),
    total: Number(match[3].replaceAll(",", "")),
  } : null;
}

async function waitForMarker(page, expectedStart, timeoutMs = 45000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const text = await page.locator("body").innerText().catch(() => "");
    const marker = parseMarker(text);
    if (marker && marker.start === expectedStart) return marker;
    await page.waitForTimeout(500);
  }
  throw new Error(`listing marker not ready for start=${expectedStart}`);
}

async function extractDirectory(page) {
  return page.evaluate(() => {
    const tags = new Map();
    const pagination = new Set();
    for (const anchor of document.querySelectorAll("a[href]")) {
      const url = new URL(anchor.href, location.href);
      if (url.pathname === "/tag/" && url.searchParams.has("search")) continue;
      if (/^\/tag\/page\/\d+\/$/.test(url.pathname)) {
        pagination.add(url.href);
        continue;
      }
      const match = url.pathname.match(/^\/tag\/([^/]+)\/$/);
      if (!match) continue;
      const slug = match[1];
      if (["page", "search"].includes(slug)) continue;
      tags.set(`${url.origin}/tag/${slug}/`, {
        url: `${url.origin}/tag/${slug}/`,
        slug,
        name: anchor.innerText.trim() || slug,
      });
    }
    return {
      title: document.title,
      text: document.body?.innerText || "",
      tags: [...tags.values()],
      pagination: [...pagination],
    };
  });
}

async function extractTagPage(page) {
  return page.evaluate(() => {
    const body = document.body?.innerText || "";
    const shown = body.match(/Showing\s+(\d+)\s*[\u2013-]\s*(\d+)\s+of\s+([\d,]+)\s+results?/i);
    const products = [];
    const seen = new Set();
    const structured = [...document.querySelectorAll('script[type="application/ld+json"]')]
      .flatMap((script) => {
        try { return [JSON.parse(script.textContent)]; } catch { return []; }
      })
      .find((data) => data?.["@type"] === "ItemList" && Array.isArray(data.itemListElement));
    const primaryItems = structured?.itemListElement?.filter((item) => item?.url)?.map((item) => ({
      canonicalUrl: new URL(item.url, location.href).href,
      title: String(item.name || "").trim(),
    })) || [];
    const candidates = primaryItems.length ? primaryItems : [...document.querySelectorAll('a[href*="/product/"]')].map((anchor) => ({
      canonicalUrl: anchor.href,
      title: (anchor.innerText.trim() || anchor.querySelector("img")?.alt?.trim() || "").replace(/\s+/g, " "),
    }));
    for (const candidate of candidates) {
      const url = new URL(candidate.canonicalUrl, location.href);
      if (!url.pathname.startsWith("/product/")) continue;
      const canonical = `${url.origin}${url.pathname}`.replace(/\/{2,}$/g, "/");
      const duplicate = seen.has(canonical);
      seen.add(canonical);
      products.push({ canonicalUrl: canonical, title: candidate.title, duplicate });
    }
    const relatedTags = [...document.querySelectorAll('a[href*="/tag/"]')]
      .map((anchor) => ({ name: anchor.innerText.trim(), url: anchor.href }))
      .filter((entry) => entry.name && /^https:\/\/www\.creativefabrica\.com\/tag\/[^/?]+\/$/.test(entry.url));
    return {
      url: location.href,
      title: document.title,
      marker: shown ? {
        start: Number(shown[1]),
        end: Number(shown[2]),
        total: Number(shown[3].replaceAll(",", "")),
      } : null,
      products,
      relatedTags,
    };
  });
}

function parseOptions() {
  return {
    out: path.resolve(arg("out", "outputs/research/creative-fabrica-tag-first-collector")),
    browserUrl: arg("browser-url", "http://127.0.0.1:9223"),
    directoryPages: arg("directory-pages") ? Number(arg("directory-pages")) : null,
    tagSlugs: args("tag").map((value) => value.replace(/^\/tag\//, "").replace(/\/$/, "")),
    tagPages: arg("tag-pages") ? Number(arg("tag-pages")) : null,
    sortModes: args("sort").length ? args("sort") : ["popularity"],
    discoverOnly: has("discover-only"),
    allDiscovered: has("all-discovered"),
    maxTagPages: Number(arg("max-tag-pages", "500")),
    allowLargeTags: has("allow-large-tags"),
    delay: Number(arg("delay", "1500")),
    retries: Number(arg("retries", "3")),
    retryDelay: Number(arg("retry-delay", "10000")),
    fresh: has("fresh"),
  };
}

async function main() {
  const options = parseOptions();
  await fs.mkdir(path.join(options.out, "raw"), { recursive: true });
  const dbPath = path.join(options.out, "creative-fabrica-tags.db");
  if (options.fresh) await fs.rm(dbPath, { force: true });
  const db = new Database(dbPath);
  initDb(db);
  const statePath = path.join(options.out, "crawl-state.json");
  const heartbeatPath = path.join(options.out, "heartbeat.json");
  const oldState = options.fresh
    ? {}
    : await fs.readFile(statePath, "utf8").then(JSON.parse).catch(() => ({}));
  const runId = oldState.runId || `${Date.now()}-${crypto.randomBytes(3).toString("hex")}`;
  db.prepare("INSERT OR IGNORE INTO crawl_runs (run_id,started_at,status,parser_version,notes) VALUES (?,?,?,?,?)")
    .run(runId, now(), "running", VERSION, "bounded tag-first reconnaissance");
  const heartbeat = (data) => atomicJson(heartbeatPath, {
    pid: process.pid,
    runId,
    updatedAt: now(),
    ...data,
  });
  await heartbeat({ status: "RUNNING", phase: "browser_startup" });

  const browser = await chromium.connectOverCDP(options.browserUrl);
  const context = browser.contexts()[0];
  if (!context) throw new Error("No browser context found at --browser-url");
  const page = await context.newPage();

  const saveRaw = async (url, documentType, pageName) => {
    const html = await page.content();
    const rawPath = path.join(options.out, "raw", `${pageName}.html.gz`);
    const raw = await writeRaw(rawPath, html);
    db.prepare(`INSERT OR IGNORE INTO raw_documents
      (run_id,url,final_url,document_type,http_status,content_hash,storage_path,fetched_at)
      VALUES (?,?,?,?,?,?,?,?)`).run(runId, url, page.url(), documentType, 200, raw.sha256, rawPath, now());
    return raw;
  };

  const saveError = (url, entityType, entityKey, pageNumber, attempt, error) => {
    db.prepare(`INSERT INTO crawl_errors
      (run_id,url,entity_type,entity_key,page_number,attempt_number,error_class,error_message,created_at)
      VALUES (?,?,?,?,?,?,?,?,?)`).run(runId, url, entityType, entityKey, pageNumber, attempt,
      error.name || "Error", String(error.message || error), now());
  };

  const selectSortMode = async (sortMode) => {
    if (sortMode === "popularity") return;
    const select = page.locator('select[name="orderby"]').first();
    if (await select.count()) {
      const value = sortMode === "latest" ? "date" : "popularity";
      await select.selectOption(value);
      await select.waitFor({ state: "attached", timeout: 10000 });
      await page.waitForFunction((expected) => document.querySelector('select[name="orderby"]')?.value === expected, value, { timeout: 10000 });
      await page.waitForTimeout(3000);
      return;
    }
    throw new Error(`sort control not exposed for mode=${sortMode}`);
  };

  try {
    await page.goto(TAG_ROOT, { waitUntil: "domcontentloaded", timeout: 60000 });
    const directory = await extractDirectory(page);
    const directoryRaw = await saveRaw(TAG_ROOT, "tag_directory", "directory-1");
    const discovered = new Map(directory.tags.map((tag) => [tag.url, tag]));
    db.prepare(`INSERT OR REPLACE INTO directory_pages
      (run_id,page_number,requested_url,final_url,discovered_tag_count,discovered_pagination_count,status,content_hash,fetched_at)
      VALUES (?,?,?,?,?,?,?,?,?)`).run(runId, 1, TAG_ROOT, page.url(), directory.tags.length,
      directory.pagination.length, "COMPLETE", directoryRaw.sha256, now());
    console.log(`[directory] tags=${discovered.size} pagination=${directory.pagination.length} raw=${directoryRaw.sha256}`);

    const directoryQueue = [...new Set(directory.pagination)]
      .map((url) => Number(new URL(url).pathname.match(/\/page\/(\d+)\//)?.[1]))
      .filter(Number.isFinite)
      .sort((a, b) => a - b);
    const directoryLimit = options.directoryPages || directoryQueue.length + 1;
    for (let queueIndex = 0; queueIndex < directoryQueue.length && queueIndex + 2 <= directoryLimit && !stopping; queueIndex += 1) {
      const pageNumber = directoryQueue[queueIndex];
      const url = `${TAG_ROOT}page/${pageNumber}/`;
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
      const result = await extractDirectory(page);
      const raw = await saveRaw(url, "tag_directory", `directory-${pageNumber}`);
      db.prepare(`INSERT OR REPLACE INTO directory_pages
        (run_id,page_number,requested_url,final_url,discovered_tag_count,discovered_pagination_count,status,content_hash,fetched_at)
        VALUES (?,?,?,?,?,?,?,?,?)`).run(runId, pageNumber, url, page.url(), result.tags.length,
        result.pagination.length, "COMPLETE", raw.sha256, now());
      for (const tag of result.tags) discovered.set(tag.url, tag);
      console.log(`[directory] page=${pageNumber} tags=${result.tags.length} total=${discovered.size}`);
      await sleep(options.delay);
    }

    const upsertTag = db.prepare(`INSERT INTO tags
      (canonical_slug,canonical_url,display_name,first_seen_at,last_seen_at)
      VALUES (?,?,?,?,?)
      ON CONFLICT(canonical_url) DO UPDATE SET display_name=excluded.display_name,last_seen_at=excluded.last_seen_at`);
    for (const tag of discovered.values()) {
      upsertTag.run(tag.slug, tag.url, tag.name, now(), now());
    }

    // A bounded run may target a valid tag that is not present on the first
    // directory page. Keep it as an explicit route seed rather than treating
    // directory-page visibility as proof that the tag is unknown.
    for (const slug of options.tagSlugs) {
      upsertTag.run(slug, `${TAG_ROOT}${slug}/`, slug, now(), now());
    }

    const requestedTags = options.discoverOnly
      ? []
      : options.allDiscovered
        ? [...discovered.values()].map((tag) => tag.slug)
      : options.tagSlugs.length
        ? options.tagSlugs
        : [...discovered.values()].slice(0, 1).map((tag) => tag.slug);
    const insertProduct = db.prepare(`INSERT INTO products
      (canonical_url,current_title,first_seen_at,last_seen_at) VALUES (?,?,?,?)
      ON CONFLICT(canonical_url) DO UPDATE SET current_title=COALESCE(excluded.current_title,products.current_title),last_seen_at=excluded.last_seen_at`);
    const findProduct = db.prepare("SELECT product_id FROM products WHERE canonical_url=?");
    const findTag = db.prepare("SELECT tag_id FROM tags WHERE canonical_slug=?");
    const insertRelation = db.prepare(`INSERT INTO product_tags
      (product_id,tag_id,first_seen_run_id,last_seen_run_id,route_confirmed)
      VALUES (?,?,?,?,1)
      ON CONFLICT(product_id,tag_id) DO UPDATE SET last_seen_run_id=excluded.last_seen_run_id,route_confirmed=1`);
    const insertObservation = db.prepare(`INSERT OR REPLACE INTO product_route_observations
      (run_id,tag_id,product_id,sort_mode,page_number,position_on_page,global_position,displayed_total)
      VALUES (?,?,?,?,?,?,?,?)`);

    for (const slug of requestedTags) {
      for (const sortMode of options.sortModes) {
        const tagUrl = `${TAG_ROOT}${slug}/`;
        let total = null;
        let pageSize = null;
        let expectedPages = null;
        let skippedLarge = false;
        let pageNumber = 1;
        while (!stopping && (options.tagPages ? pageNumber <= options.tagPages : expectedPages === null || pageNumber <= expectedPages)) {
          const url = pageNumber === 1 ? tagUrl : `${TAG_ROOT}${slug}/page/${pageNumber}/`;
          let result = null;
          let lastError = null;
          for (let attempt = 1; attempt <= options.retries; attempt += 1) {
            try {
              await heartbeat({ status: "RUNNING", phase: "tag_page", tag: slug, sortMode, pageNumber, attempt, url });
              await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
              await selectSortMode(sortMode);
              const marker = await waitForMarker(page, (pageNumber - 1) * 36 + 1);
              result = await extractTagPage(page);
              if (!result.marker || result.marker.start !== marker.start || !result.products.length) {
                throw new Error("invalid tag-page shape");
              }
              break;
            } catch (error) {
              lastError = error;
              saveError(url, "tag_page", slug, pageNumber, attempt, error);
              await heartbeat({ status: "RETRYING", phase: "tag_page_error", tag: slug, sortMode, pageNumber, attempt, url, error: String(error.message || error) });
              await sleep(options.retryDelay * attempt);
            }
          }
          const tag = findTag.get(slug);
          if (!tag) {
            console.error(`[tag] unknown slug=${slug}`);
            break;
          }
          if (!result) {
            db.prepare(`INSERT OR REPLACE INTO tag_pages
              (run_id,tag_id,sort_mode,page_number,requested_url,status,fetched_at)
              VALUES (?,?,?,?,?,?,?)`).run(runId, tag.tag_id, sortMode, pageNumber, url, "FAILED", now());
            console.error(`[tag] FAILED slug=${slug} sort=${sortMode} page=${pageNumber}: ${lastError?.message}`);
            await heartbeat({ status: "INCOMPLETE", phase: "tag_page_failed", tag: slug, sortMode, pageNumber, url, error: String(lastError?.message || lastError) });
            break;
          }
          total ??= result.marker.total;
          pageSize ??= result.marker.end - result.marker.start + 1;
          expectedPages = Math.ceil(result.marker.total / pageSize);
          // A one-page metadata run is deliberately allowed to sample large
          // tags. The safety cap applies only when requesting full pagination.
          if (!options.tagPages && !options.allowLargeTags && expectedPages > options.maxTagPages) {
            skippedLarge = true;
            console.warn(`[tag] SKIP slug=${slug} sort=${sortMode} expected_pages=${expectedPages} max=${options.maxTagPages}`);
            break;
          }
          const raw = await saveRaw(url, "tag_route", `tag-${slug}-${sortMode}-${pageNumber}`);
          const uniqueProducts = new Set(result.products.map((product) => product.canonicalUrl));
          const pageRecord = db.prepare(`INSERT OR REPLACE INTO tag_pages
            (run_id,tag_id,sort_mode,page_number,requested_url,final_url,displayed_start,displayed_end,displayed_total,observed_card_count,unique_product_count,duplicate_card_count,status,content_hash,fetched_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`);
          pageRecord.run(runId, tag.tag_id, sortMode, pageNumber, url, result.url,
            result.marker.start, result.marker.end, result.marker.total, result.products.length,
            uniqueProducts.size, result.products.length - uniqueProducts.size, "COMPLETE", raw.sha256, now());

          for (let index = 0; index < result.products.length; index += 1) {
            const product = result.products[index];
            const canonical = canonicalUrl(product.canonicalUrl, "/product/");
            if (!canonical) continue;
            insertProduct.run(canonical, product.title || null, now(), now());
            const productRow = findProduct.get(canonical);
            insertRelation.run(productRow.product_id, tag.tag_id, runId, runId);
            insertObservation.run(runId, tag.tag_id, productRow.product_id, sortMode, pageNumber,
              index + 1, ((pageNumber - 1) * 36) + index + 1, result.marker.total);
          }
          console.log(`[tag] slug=${slug} sort=${sortMode} page=${pageNumber}/${expectedPages}${options.tagPages ? ` (cap=${options.tagPages})` : ""} products=${result.products.length} total=${total}`);
          await heartbeat({ status: "RUNNING", phase: "tag_page_complete", tag: slug, sortMode, pageNumber, expectedPages, products: result.products.length });
          await sleep(options.delay);
          pageNumber += 1;
        }
        const tag = findTag.get(slug);
        if (tag) {
          const rows = db.prepare(`SELECT status, displayed_total FROM tag_pages
            WHERE run_id=? AND tag_id=? AND sort_mode=? ORDER BY page_number`).all(runId, tag.tag_id, sortMode);
          const totals = [...new Set(rows.map((row) => row.displayed_total).filter((value) => value !== null))];
          const failed = rows.filter((row) => row.status !== "COMPLETE").length;
          const expected = totals.length ? Math.ceil(totals[totals.length - 1] / 36) : expectedPages;
          const limited = Boolean(options.tagPages && expected && options.tagPages < expected);
          const status = skippedLarge
            ? "SKIPPED_TOO_LARGE"
            : !rows.length
              ? (stopping ? "INTERRUPTED" : "INCOMPLETE")
              : failed
                ? "INCOMPLETE"
                : limited
                  ? "BOUNDED_INCOMPLETE"
                  : totals.length > 1 ? "DRIFTED" : "COMPLETE";
          db.prepare(`INSERT OR REPLACE INTO tag_crawl_status
            (run_id,tag_id,sort_mode,expected_pages,successful_pages,failed_pages,observed_total,total_values,status,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)`).run(runId, tag.tag_id, sortMode, expected, rows.length - failed,
            failed, totals[totals.length - 1] ?? null, JSON.stringify(totals), status, now());
          console.log(`[tag] summary slug=${slug} sort=${sortMode} status=${status} pages=${rows.length}/${expected ?? "?"} totals=${totals.join(",") || "unknown"}`);
        }
      }
    }

    const incompleteCount = db.prepare("SELECT COUNT(*) AS count FROM tag_crawl_status WHERE run_id=? AND status != 'COMPLETE'").get(runId).count;
    const bounded = Boolean(options.directoryPages || options.tagPages);
    const state = {
      runId,
      status: stopping ? "INTERRUPTED" : incompleteCount ? "INCOMPLETE" : bounded ? "BOUNDED_INCOMPLETE" : "COMPLETE",
      discoveredTags: discovered.size,
      requestedTags,
      updatedAt: now(),
      parserVersion: VERSION,
    };
    await atomicJson(statePath, state);
    await heartbeat({ status: state.status, phase: "finished", discoveredTags: discovered.size, requestedTags });
    db.prepare("UPDATE crawl_runs SET status=?,finished_at=? WHERE run_id=?")
      .run(state.status, now(), runId);
    console.log(JSON.stringify({ runId, ...state }, null, 2));
  } finally {
    await browser.close().catch(() => {});
    db.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
