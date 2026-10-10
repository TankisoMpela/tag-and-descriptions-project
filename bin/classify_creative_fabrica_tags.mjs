#!/usr/bin/env node

/**
 * Classify discovered tag routes using a bounded PDP sample.
 *
 * Input: a creative-fabrica-tags.db containing product route observations.
 * Output: tag classifications based on observed PDP category/subcategory,
 * never on tag-name guesses alone.
 */

import crypto from "node:crypto";
import Database from "better-sqlite3";
import { chromium } from "playwright";

const VERSION = "creative-fabrica-tag-classifier-0.1.0";
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function arg(name, fallback = null) {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function now() { return new Date().toISOString(); }

function initDb(db) {
  db.pragma("journal_mode = WAL");
  db.pragma("synchronous = FULL");
  db.pragma("foreign_keys = ON");
  db.exec(`
    CREATE TABLE IF NOT EXISTS tag_classifications (
      classification_id INTEGER PRIMARY KEY,
      run_id TEXT NOT NULL,
      tag_id INTEGER NOT NULL REFERENCES tags(tag_id),
      sample_target INTEGER NOT NULL,
      sample_attempted INTEGER NOT NULL,
      sample_successful INTEGER NOT NULL,
      font_product_count INTEGER NOT NULL,
      font_share REAL,
      font_designer_count INTEGER NOT NULL,
      subcategories_json TEXT,
      decision TEXT NOT NULL,
      decision_reason TEXT NOT NULL,
      observed_at TEXT NOT NULL,
      UNIQUE(run_id, tag_id)
    );
    CREATE TABLE IF NOT EXISTS tag_classification_products (
      run_id TEXT NOT NULL,
      tag_id INTEGER NOT NULL REFERENCES tags(tag_id),
      product_id INTEGER NOT NULL REFERENCES products(product_id),
      category_name TEXT,
      subcategory_name TEXT,
      designer_name TEXT,
      is_font INTEGER,
      status TEXT NOT NULL,
      observed_at TEXT NOT NULL,
      PRIMARY KEY(run_id, tag_id, product_id)
    );
  `);
}

async function extractProduct(page) {
  return page.evaluate(() => {
    const body = document.body?.innerText || "";
    const links = [...document.querySelectorAll("a[href]")];
    const designer = links.find((a) => /\/designer\//.test(new URL(a.href, location.href).pathname));
    const categories = [...new Map(links
      .filter((a) => /^\/fonts\//.test(new URL(a.href, location.href).pathname))
      .map((a) => [a.href, a.innerText.trim()])).values()].filter(Boolean).slice(0, 3);
    return {
      title: document.querySelector("h1")?.innerText.trim() || null,
      category: categories[0] || null,
      subcategory: categories[1] || null,
      categoryPath: categories.join(" > "),
      designer: designer?.innerText.trim() || null,
      isFont: categories[0]?.toLowerCase() === "fonts" ? 1 : 0,
    };
  });
}

async function main() {
  const dbPath = arg("db", "outputs/research/creative-fabrica-tag-first-collector/creative-fabrica-tags.db");
  const db = new Database(dbPath);
  initDb(db);
  const browser = await chromium.connectOverCDP(arg("browser-url", "http://127.0.0.1:9223"));
  const context = browser.contexts()[0];
  if (!context) throw new Error("No browser context found");
  const page = await context.newPage();
  const runId = `${Date.now()}-${crypto.randomBytes(3).toString("hex")}`;
  const sampleTarget = Number(arg("samples-per-tag", "5"));
  const minSample = Number(arg("min-sample", "3"));
  const fontThreshold = Number(arg("font-threshold", "0.5"));
  const minDesigners = Number(arg("min-designers", "2"));
  const maxTags = Number(arg("max-tags", "1000000"));
  const tagFilter = arg("tag", null);
  const tags = db.prepare(`SELECT tag_id,canonical_slug,display_name FROM tags
    WHERE (? IS NULL OR canonical_slug=?)
      AND EXISTS (SELECT 1 FROM product_route_observations o
        WHERE o.tag_id=tags.tag_id AND o.sort_mode='popularity')
    ORDER BY tag_id LIMIT ?`).all(tagFilter, tagFilter, maxTags);
  const productsForTag = db.prepare(`SELECT DISTINCT o.product_id,p.canonical_url
    FROM product_route_observations o JOIN products p ON p.product_id=o.product_id
    WHERE o.tag_id=? AND o.sort_mode='popularity' ORDER BY o.global_position LIMIT ?`);
  const insertObservation = db.prepare(`INSERT OR REPLACE INTO tag_classification_products
    (run_id,tag_id,product_id,category_name,subcategory_name,designer_name,is_font,status,observed_at)
    VALUES (?,?,?,?,?,?,?,?,?)`);
  const insertClassification = db.prepare(`INSERT OR REPLACE INTO tag_classifications
    (run_id,tag_id,sample_target,sample_attempted,sample_successful,font_product_count,font_share,font_designer_count,subcategories_json,decision,decision_reason,observed_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`);

  db.prepare(`INSERT INTO crawl_runs (run_id,started_at,status,parser_version,notes)
    VALUES (?,?,?,?,?)`).run(runId, now(), "running", VERSION, "bounded font relevance classification");

  let completed = 0;
  for (const tag of tags) {
    const candidates = productsForTag.all(tag.tag_id, sampleTarget);
    let successful = 0;
    let fontCount = 0;
    const designers = new Set();
    const subcategories = new Map();
    for (const product of candidates) {
      let result = null;
      let error = null;
      try {
        await page.goto(product.canonical_url, { waitUntil: "domcontentloaded", timeout: 60000 });
        await page.locator("h1").first().waitFor({ state: "visible", timeout: 30000 });
        result = await extractProduct(page);
      } catch (caught) {
        error = caught;
      }
      if (!result) {
        insertObservation.run(runId, tag.tag_id, product.product_id, null, null, null, null, "FAILED", now());
        console.error(`[classify] ${tag.canonical_slug} ${product.canonical_url}: ${error?.message}`);
        continue;
      }
      successful += 1;
      fontCount += result.isFont;
      if (result.isFont && result.designer) designers.add(result.designer);
      if (result.isFont && result.subcategory) subcategories.set(result.subcategory, (subcategories.get(result.subcategory) || 0) + 1);
      insertObservation.run(runId, tag.tag_id, product.product_id, result.category, result.subcategory,
        result.designer, result.isFont, "COMPLETE", now());
      await sleep(Number(arg("delay", "1000")));
    }
    const share = successful ? fontCount / successful : null;
    const decision = successful < minSample
      ? "INSUFFICIENT"
      : share >= fontThreshold && designers.size >= minDesigners
        ? "FONT_RELEVANT"
        : share >= fontThreshold
          ? "FONT_RELEVANT_LOW_DESIGNER_DIVERSITY"
          : "NON_FONT";
    const reason = `font_share=${share === null ? "unknown" : share.toFixed(3)}; successful=${successful}; designers=${designers.size}; threshold=${fontThreshold}; min_designers=${minDesigners}`;
    insertClassification.run(runId, tag.tag_id, sampleTarget, candidates.length, successful, fontCount, share,
      designers.size, JSON.stringify(Object.fromEntries(subcategories)), decision, reason, now());
    completed += 1;
    console.log(`[classify] ${completed}/${tags.length} ${tag.canonical_slug} ${decision} ${reason}`);
  }
  const status = tags.length === completed ? "COMPLETE" : "INCOMPLETE";
  db.prepare("UPDATE crawl_runs SET status=?,finished_at=? WHERE run_id=?").run(status, now(), runId);
  console.log(JSON.stringify({ runId, status, tags: tags.length, completed, sampleTarget, fontThreshold, minDesigners }, null, 2));
  await browser.close().catch(() => {});
  db.close();
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
