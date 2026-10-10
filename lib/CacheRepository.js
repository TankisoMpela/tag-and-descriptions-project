'use strict';

const path = require('path');
const fs = require('fs');

const DB_DIR = path.join(__dirname, '..', '.pipeline');
const DB_PATH = path.join(DB_DIR, 'cache.json');

const TTL = {
  exa: 7 * 24 * 60 * 60 * 1000,
  serper: 3 * 24 * 60 * 60 * 1000,
  tavily: 7 * 24 * 60 * 60 * 1000,
  firecrawl: 7 * 24 * 60 * 60 * 1000,
  curl: 14 * 24 * 60 * 60 * 1000,
  mcp: 7 * 24 * 60 * 60 * 1000,
};

let cacheData = null;

function loadCache() {
  if (cacheData !== null) return cacheData;
  
  if (!fs.existsSync(DB_DIR)) {
    fs.mkdirSync(DB_DIR, { recursive: true });
  }

  if (fs.existsSync(DB_PATH)) {
    try {
      const content = fs.readFileSync(DB_PATH, 'utf8');
      cacheData = JSON.parse(content);
    } catch (e) {
      cacheData = {};
    }
  } else {
    cacheData = {};
  }
  return cacheData;
}

function saveCache() {
  if (cacheData === null) return;
  try {
    fs.writeFileSync(DB_PATH, JSON.stringify(cacheData, null, 2), 'utf8');
  } catch (e) {
    console.error(`Failed to save cache to ${DB_PATH}: ${e.message}`);
  }
}

async function getCachedSearch(query, source) {
  const data = loadCache();
  const key = `${source}:${query}`;
  const entry = data[key];
  if (entry) {
    const age = Date.now() - entry.cached_at;
    if (age < (TTL[source] || TTL.mcp)) {
      return entry.result;
    }
  }
  return null;
}

async function cacheSearch(query, results, source) {
  const data = loadCache();
  const key = `${source}:${query}`;
  data[key] = {
    result: results,
    cached_at: Date.now()
  };
  saveCache();
}

module.exports = { getCachedSearch, cacheSearch };
