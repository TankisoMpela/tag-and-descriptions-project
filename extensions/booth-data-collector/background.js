/* ===========================================================
 * BOOTH Data Collector — background.js (MV3 service worker)
 *
 * Coordinates the crawl:
 *   LIST PHASE   : walks pages via the active tab (a[rel="next"]),
 *                  extracting li.item-card each time.
 *   DETAIL PHASE : fetches each item page (concurrency + random delay),
 *                  parses description/tags/variants/prices.
 *
 * State is persisted to chrome.storage.local so the worker can be
 * killed and restarted without losing a run. Export happens in the
 * popup (it reads storage directly), keeping message sizes small.
 * =========================================================== */

'use strict';

importScripts('shared.js');
const C = globalThis.BOOTH_COLLECTOR;

const STORE_KEY = 'boothCrawl';
const DEFAULT_SETTINGS = {
  maxPages: 0,          // 0 = unlimited
  maxItems: 500,
  fetchDetails: true,
  detailConcurrency: 3,
  detailDelayMs: 900
};

/* ---------- state helpers ---------- */

let cachedState = null;

async function loadState() {
  if (cachedState) return cachedState;
  const data = await chrome.storage.local.get(STORE_KEY);
  cachedState = data[STORE_KEY] || null;
  return cachedState;
}

async function saveState(state) {
  cachedState = state;
  await chrome.storage.local.set({ [STORE_KEY]: state });
}

function freshState(settings, tabId, url, context) {
  return {
    status: 'running',
    settings: settings,
    startedAt: C.nowIso(),
    updatedAt: C.nowIso(),
    tabId: tabId,
    url: url,
    context: context,
    listPhaseDone: false,
    currentPage: 0,
    pages: [],
    products: [],
    details: {},
    nextUrl: '',
    errors: [],
    log: [],
    stopRequested: false
  };
}

function log(state, line) {
  state.log.push(`[${new Date().toISOString().slice(11, 19)}] ${line}`);
  if (state.log.length > 80) state.log = state.log.slice(-80);
}

function pushError(state, e) {
  state.errors.push({ at: C.nowIso(), msg: String(e && e.message || e) });
  if (state.errors.length > 50) state.errors = state.errors.slice(-50);
}

function pill(state, extra) {
  const n = state.products.length;
  const d = Object.keys(state.details).length;
  const phase = state.listPhaseDone ? 'DETAIL' : 'LIST';
  const text = `BOOTH Collector\n${phase} · page ${state.currentPage} · ${n} cards\n${d} details${extra ? ' · ' + extra : ''}`;
  updatePill(state.tabId, text);
}

async function updatePill(tabId, text) {
  if (tabId == null) return;
  try {
    await chrome.tabs.sendMessage(tabId, { type: 'PROGRESS', text: text });
  } catch (e) { /* tab may be on a non-booth page or closed */ }
}

/* ---------- messaging ---------- */

async function sendToTab(tabId, msg) {
  return new Promise((resolve) => {
    try {
      chrome.tabs.sendMessage(tabId, msg, (resp) => {
        if (chrome.runtime.lastError) {
          resolve({ ok: false, error: chrome.runtime.lastError.message });
        } else {
          resolve(resp || { ok: false, error: 'no response' });
        }
      });
    } catch (e) {
      resolve({ ok: false, error: String(e && e.message || e) });
    }
  });
}

// Extract with retries: give the freshly-loaded page time to render cards.
async function extractWithRetry(tabId, attempts = 10, baseDelay = 700) {
  let delay = baseDelay;
  for (let i = 0; i < attempts; i++) {
    const resp = await sendToTab(tabId, { type: 'EXTRACT_LIST' });
    if (resp && resp.ok && resp.products && resp.products.length > 0) {
      return resp;
    }
    await sleep(delay);
    delay = Math.min(delay * 1.35, 6000);
  }
  // Last chance: accept whatever the page returned even if empty.
  const resp = await sendToTab(tabId, { type: 'EXTRACT_LIST' });
  return resp || { ok: false, error: 'extract failed' };
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/* ---------- list phase ---------- */

async function runListPhase(state, ctx) {
  if (state.stopRequested) return;

  // Start on whatever page the active tab is already showing.
  const first = await extractWithRetry(state.tabId, 4, 600);
  if (first.ok && first.products) {
    appendPage(state, first);
  } else {
    state.errors.push({ at: C.nowIso(), msg: 'first page extract failed: ' + (first.error || 'unknown') });
  }

  while (!state.stopRequested) {
    const limitPages = state.settings.maxPages > 0 && state.currentPage >= state.settings.maxPages;
    const limitItems = state.settings.maxItems > 0 && state.products.length >= state.settings.maxItems;
    if (limitPages || limitItems) break;

    if (!state.nextUrl) break; // no more pages

    state.currentPage += 1;
    log(state, `navigating to page ${state.currentPage}: ${state.nextUrl}`);
    pill(state);

    let updated = false;
    try {
      await chrome.tabs.update(state.tabId, { url: state.nextUrl });
      updated = true;
    } catch (e) {
      state.errors.push({ at: C.nowIso(), msg: 'tab update failed: ' + (e && e.message || e) });
      break;
    }

    for (let attempt = 0; attempt < 12 && !state.stopRequested; attempt++) {
      await sleep(900);
      const resp = await sendToTab(state.tabId, { type: 'EXTRACT_LIST' });
      if (resp && resp.ok && resp.products && (resp.cardCount || 0) > 0) {
        appendPage(state, resp);
        if (!resp.nextUrl) log(state, 'no more pages');
        updated = true;
        break;
      }
      if (resp && resp.ok && resp.nextUrl) {
        // Empty page but still has a next link: record and continue.
        state.nextUrl = resp.nextUrl;
        break;
      }
    }
    if (!updated) {
      log(state, 'giving up on waiting for page cards');
      break;
    }
  }
  state.listPhaseDone = true;
  await saveState(state);
}

function appendPage(state, resp) {
  const page = resp.context ? resp.context.page : (state.currentPage + 1);
  state.currentPage = page;
  state.pages.push({
    page: page,
    cardCount: resp.cardCount || (resp.products ? resp.products.length : 0),
    nextUrl: resp.nextUrl || '',
    url: resp.hostUrl || state.url
  });
  state.nextUrl = resp.nextUrl || '';

  const seen = new Set(state.products.map((p) => p.itemId + '|' + p.itemUrl));
  let added = 0;
  for (const p of resp.products || []) {
    const key = p.itemId + '|' + p.itemUrl;
    if (seen.has(key)) continue;
    seen.add(key);
    state.products.push(p);
    added++;
  }
  log(state, `page ${page}: +${added} new cards (${resp.cardCount || 0} on page)`);
  pill(state);
}

/* ---------- detail phase ---------- */

async function runDetailPhase(state, ctx = {}) {
  if (state.stopRequested || !state.settings.fetchDetails) {
    await saveState(state);
    return;
  }

  const pending = state.products
    .filter((p) => p.itemUrl && !state.details[p.itemId])
    .map((p) => ({ itemId: p.itemId, url: p.itemUrl }));

  log(state, `detail phase: ${pending.length} items queued`);
  pill(state, `queue ${pending.length}`);

  const concurrency = Math.max(1, Math.min(6, state.settings.detailConcurrency || 3));
  let queueIndex = 0;

  const worker = async () => {
    while (!state.stopRequested) {
      const i = queueIndex++;
      if (i >= pending.length) return;
      const job = pending[i];
      if (state.details[job.itemId]) continue;

      const detail = await fetchItemDetailWithRetry(state, job, 3);
      if (detail && detail.detailFetched) {
        state.details[job.itemId] = detail;
        const target = state.products.find((p) => p.itemId === job.itemId || p.itemUrl === job.url);
        if (target) Object.assign(target, detail);
      }
      await sleep((state.settings.detailDelayMs || 900) + Math.floor(Math.random() * 500));
      if ((Object.keys(state.details).length % 10) === 0) {
        await saveState(state); // heartbeat checkpoint
      }
      pill(state, `queue ${Math.max(0, pending.length - i - 1)}`);
    }
  };

  await Promise.all(Array.from({ length: Math.min(concurrency, pending.length) }, () => worker()));
  await saveState(state);
}

async function fetchItemDetailWithRetry(state, job, attempts) {
  for (let attempt = 0; attempt < attempts; attempt++) {
    const text = await fetchRawItem(job.url);
    if (text != null) {
      try {
        return C.parseItemDetail(text, { itemId: job.itemId, itemUrl: job.url });
      } catch (e) {
        pushError(state, 'parse detail ' + job.itemId + ': ' + (e && e.message || e));
      }
    }
    await sleep(1000 * (attempt + 1) + Math.floor(Math.random() * 700));
  }
  pushError(state, 'detail fetch failed after retries: ' + job.itemId);
  return null;
}

async function fetchRawItem(url) {
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 25000);
    const res = await fetch(url, { credentials: 'include', signal: ctrl.signal });
    clearTimeout(timer);
    if (res.status === 429 || res.status >= 500) return null; // retry-able
    if (!res.ok) return '';
    return await res.text();
  } catch (e) {
    return null;
  }
}

/* ---------- worker message routing ---------- */

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab || null;
}

async function startCrawl(settings) {
  const tab = await getActiveTab();
  if (!tab) throw new Error('No active tab');
  const url = tab.url || '';
  if (!/booth\.pm/.test(url)) throw new Error('Active tab is not a BOOTH page');

  const mergedSettings = Object.assign({}, DEFAULT_SETTINGS, settings || {});
  const context = C.parseContext(url);
  const state = freshState(mergedSettings, tab.id, url, context);
  await saveState(state);
  log(state, `crawl start @ ${url}`);
  log(state, `context: tag="${context.contextTag}" category="${context.contextCategory}" sort=${context.sortMode}`);
  await saveState(state);

  try {
    await runListPhase(state, context);
    if (!state.stopRequested) {
      await runDetailPhase(state, context);
    }
    if (state.stopRequested) {
      state.status = 'stopped';
      log(state, 'stopped by user');
    } else {
      state.status = 'done';
      log(state, `complete: ${state.products.length} products, ${Object.keys(state.details).length} details`);
    }
  } catch (e) {
    state.status = 'error';
    pushError(state, e);
    log(state, 'crawl error: ' + (e && e.message || e));
  }
  state.updatedAt = C.nowIso();
  await saveState(state);
  await updatePill(state.tabId, 'BOOTH Collector\nidle');
  await chrome.runtime.sendMessage({ type: 'CRAWL_DONE', status: state.status }).catch(() => {});
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (!msg || typeof msg !== 'object') return;
  switch (msg.type) {
    case 'START_CRAWL':
      (async () => {
        try {
          await startCrawl(msg.settings);
          const st = await loadState();
          sendResponse({ ok: true, status: st ? st.status : 'idle' });
        } catch (e) {
          sendResponse({ ok: false, error: String(e && e.message || e) });
        }
      })();
      return true; // async

    case 'STOP_CRAWL':
      (async () => {
        const st = await loadState();
        if (st && st.status === 'running') {
          st.stopRequested = true;
          await saveState(st);
        }
        sendResponse({ ok: true });
      })();
      return true;

    case 'GET_STATE':
      (async () => {
        const st = await loadState();
        if (!st) { sendResponse({ ok: true, state: null }); return; }
        // Send a slim view: log, status, counts, settings. Full data is in storage for export.
        sendResponse({
          ok: true,
          state: {
            status: st.status,
            startedAt: st.startedAt,
            updatedAt: st.updatedAt,
            settings: st.settings,
            url: st.url,
            context: st.context,
            currentPage: st.currentPage,
            productCount: st.products.length,
            detailCount: Object.keys(st.details).length,
            log: st.log.slice(-30),
            errors: st.errors.slice(-10),
            exportReady: st.products.length > 0
          }
        });
      })();
      return true;

    case 'CLEAR_DATA':
      (async () => {
        cachedState = null;
        await chrome.storage.local.remove(STORE_KEY);
        sendResponse({ ok: true });
      })();
      return true;

    default:
      return false;
  }
});