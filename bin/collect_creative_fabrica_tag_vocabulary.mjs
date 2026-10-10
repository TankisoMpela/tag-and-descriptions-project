#!/usr/bin/env node

/**
 * Cheap Creative Fabrica public tag-vocabulary collector.
 *
 * Crawls only /tag/ directory and alphabetical-search pages. It does not
 * open tag result pages or product pages, so it collects tag names/URLs and
 * Popular Tags vocabulary without incurring product-catalog crawling.
 */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { gzip } from "node:zlib";
import { promisify } from "node:util";
import Database from "better-sqlite3";
import { chromium } from "playwright";

const VERSION = "creative-fabrica-tag-vocabulary-0.1.0";
const ROOT = "https://www.creativefabrica.com/tag/";
const gzipAsync = promisify(gzip);
let stopping = false;
process.on("SIGINT", () => { stopping = true; });
process.on("SIGTERM", () => { stopping = true; });

function arg(name, fallback = null) {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function has(name) { return process.argv.includes(`--${name}`); }
function now() { return new Date().toISOString(); }
function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

async function atomicJson(file, value) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const temporary = `${file}.tmp`;
  await fs.writeFile(temporary, `${JSON.stringify(value, null, 2)}\n`);
  await fs.rename(temporary, file);
}

async function saveRaw(file, html) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const compressed = await gzipAsync(html, { level: 6 });
  const temporary = `${file}.tmp`;
  await fs.writeFile(temporary, compressed);
  await fs.rename(temporary, file);
  return crypto.createHash("sha256").update(html).digest("hex");
}

function initDb(db) {
  db.pragma("journal_mode = WAL");
  db.pragma("synchronous = FULL");
  db.exec(`
    CREATE TABLE IF NOT EXISTS runs (
      run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT,
      status TEXT NOT NULL, parser_version TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS pages (
      run_id TEXT NOT NULL REFERENCES runs(run_id),
      search_letter TEXT NOT NULL,
      page_number INTEGER NOT NULL,
      requested_url TEXT NOT NULL,
      final_url TEXT,
      displayed_start INTEGER,
      displayed_end INTEGER,
      displayed_total INTEGER,
      tag_count INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL,
      content_hash TEXT,
      error TEXT,
      fetched_at TEXT NOT NULL,
      PRIMARY KEY(run_id, search_letter, page_number)
    );
    CREATE TABLE IF NOT EXISTS tags (
      tag_id INTEGER PRIMARY KEY,
      canonical_slug TEXT NOT NULL UNIQUE,
      canonical_url TEXT NOT NULL UNIQUE,
      display_name TEXT,
      first_seen_at TEXT NOT NULL,
      last_seen_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS tag_sources (
      tag_id INTEGER NOT NULL REFERENCES tags(tag_id),
      run_id TEXT NOT NULL REFERENCES runs(run_id),
      source_type TEXT NOT NULL,
      search_letter TEXT,
      page_number INTEGER,
      first_seen_at TEXT NOT NULL,
      PRIMARY KEY(tag_id, run_id, source_type, search_letter, page_number)
    );
    CREATE INDEX IF NOT EXISTS idx_vocabulary_sources ON tag_sources(source_type, search_letter);
  `);
}

function parseMarker(text) {
  const match = text.match(/Showing\s+(\d+)\s*[\u2013-]\s*(\d+)\s+of\s+([\d,]+)\s+results?/i);
  return match ? { start: Number(match[1]), end: Number(match[2]), total: Number(match[3].replaceAll(",", "")) } : null;
}

async function extractPage(page) {
  return page.evaluate(() => {
    const tags = new Map();
    const pagination = new Set();
    for (const anchor of document.querySelectorAll('a[href*="/tag/"]')) {
      const url = new URL(anchor.href, location.href);
      const match = url.pathname.match(/^\/tag\/([^/]+)\/$/);
      if (match && !["page", "search"].includes(match[1])) {
        tags.set(`${url.origin}/tag/${match[1]}/`, {
          slug: match[1], url: `${url.origin}/tag/${match[1]}/`, name: anchor.innerText.trim() || match[1],
        });
      }
      if (/^\/tag\/page\/\d+\/$/.test(url.pathname) && url.searchParams.has("search")) pagination.add(url.href);
    }
    const marker = document.body?.innerText.match(/Showing\s+(\d+)\s*[\u2013-]\s*(\d+)\s+of\s+([\d,]+)\s+results?/i);
    return {
      marker: marker ? { start: Number(marker[1]), end: Number(marker[2]), total: Number(marker[3].replaceAll(",", "")) } : null,
      tags: [...tags.values()],
      pagination: [...pagination],
    };
  });
}

async function main() {
  const out = path.resolve(arg("out", "outputs/research/creative-fabrica-tag-vocabulary"));
  await fs.mkdir(path.join(out, "raw"), { recursive: true });
  const db = new Database(path.join(out, "creative-fabrica-tag-vocabulary.db"));
  initDb(db);
  const runId = `${Date.now()}-${crypto.randomBytes(3).toString("hex")}`;
  db.prepare("INSERT INTO runs VALUES (?,?,?,?,?)").run(runId, now(), null, "running", VERSION);
  const heartbeatPath = path.join(out, "heartbeat.json");
  const heartbeat = (data) => atomicJson(heartbeatPath, { runId, pid: process.pid, updatedAt: now(), ...data });
  await heartbeat({ status: "RUNNING", phase: "startup" });

  const browser = await chromium.connectOverCDP(arg("browser-url", "http://127.0.0.1:9223"));
  const context = browser.contexts()[0];
  if (!context) throw new Error("No browser context found");
  const page = await context.newPage();
  const letters = (arg("letters", "ABCDEFGHIJKLMNOPQRSTUVWXYZ").toUpperCase().match(/[A-Z]/g) || []);
  const pageLimit = Number(arg("max-pages-per-letter", "1000000"));
  const delay = Number(arg("delay", "1500"));
  const upsertTag = db.prepare(`INSERT INTO tags
    (canonical_slug,canonical_url,display_name,first_seen_at,last_seen_at) VALUES (?,?,?,?,?)
    ON CONFLICT(canonical_url) DO UPDATE SET display_name=excluded.display_name,last_seen_at=excluded.last_seen_at`);
  const findTag = db.prepare("SELECT tag_id FROM tags WHERE canonical_url=?");
  const insertSource = db.prepare(`INSERT OR IGNORE INTO tag_sources
    (tag_id,run_id,source_type,search_letter,page_number,first_seen_at) VALUES (?,?,?,?,?,?)`);

  try {
    for (const letter of letters) {
      let expectedPages = null;
      let pageNumber = 1;
      while (!stopping && pageNumber <= pageLimit && (expectedPages === null || pageNumber <= expectedPages)) {
        const url = pageNumber === 1 ? `${ROOT}?search=${letter}` : `${ROOT}page/${pageNumber}/?search=${letter}`;
        await heartbeat({ status: "RUNNING", phase: "letter_page", letter, pageNumber, expectedPages, url });
        let result = null;
        let error = null;
        for (let attempt = 1; attempt <= Number(arg("retries", "3")); attempt += 1) {
          try {
            await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
            const text = await page.locator("body").innerText();
            result = await extractPage(page);
            result.marker ||= parseMarker(text);
            if (!result.marker) throw new Error("missing tag-directory result marker");
            break;
          } catch (caught) {
            error = caught;
            await heartbeat({ status: "RETRYING", phase: "page_error", letter, pageNumber, attempt, url, error: String(error.message || error) });
            await sleep(Number(arg("retry-delay", "10000")) * attempt);
          }
        }
        if (!result) {
          db.prepare(`INSERT OR REPLACE INTO pages
            (run_id,search_letter,page_number,requested_url,status,error,fetched_at) VALUES (?,?,?,?,?,?,?)`)
            .run(runId, letter, pageNumber, url, "FAILED", String(error?.message || error), now());
          console.error(`[vocabulary] FAILED ${letter} page=${pageNumber}: ${error?.message}`);
          break;
        }
        expectedPages ??= Math.ceil(result.marker.total / (result.marker.end - result.marker.start + 1));
        const rawPath = path.join(out, "raw", `${letter}-${String(pageNumber).padStart(5, "0")}.html.gz`);
        const hash = await saveRaw(rawPath, await page.content());
        db.prepare(`INSERT OR REPLACE INTO pages
          (run_id,search_letter,page_number,requested_url,final_url,displayed_start,displayed_end,displayed_total,tag_count,status,content_hash,fetched_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`).run(runId, letter, pageNumber, url, page.url(), result.marker.start,
          result.marker.end, result.marker.total, result.tags.length, "COMPLETE", hash, now());
        for (const tag of result.tags) {
          upsertTag.run(tag.slug, tag.url, tag.name, now(), now());
          insertSource.run(findTag.get(tag.url).tag_id, runId, "alphabetical_search", letter, pageNumber, now());
        }
        console.log(`[vocabulary] letter=${letter} page=${pageNumber}/${expectedPages} tags=${result.tags.length} unique=${db.prepare("select count(*) as count from tags").get().count}`);
        pageNumber += 1;
        await sleep(delay);
      }
    }
    const status = stopping ? "INTERRUPTED" : "COMPLETE";
    db.prepare("UPDATE runs SET status=?,finished_at=? WHERE run_id=?").run(status, now(), runId);
    await heartbeat({ status, phase: "finished" });
    console.log(JSON.stringify({ runId, status, letters: letters.length, tagCount: db.prepare("select count(*) as count from tags").get().count }, null, 2));
  } finally {
    await browser.close().catch(() => {});
    db.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
