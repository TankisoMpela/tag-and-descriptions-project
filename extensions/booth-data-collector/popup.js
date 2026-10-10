/* ===========================================================
 * BOOTH Data Collector — popup.js
 * UI glue: start/stop the crawl, monitor progress, export the
 * collected data as CSV (UTF-8 BOM) or JSONL straight from
 * chrome.storage.local.
 * =========================================================== */

'use strict';

const C = globalThis.BOOTH_COLLECTOR;
const STORE_KEY = 'boothCrawl';
const SETTINGS_KEY = 'boothSettings';

const $ = (id) => document.getElementById(id);
const fmt = (n) => (Number.isFinite(n) ? Number(n).toLocaleString() : '0');

const els = {
  status: $('status-chip'),
  ctxUrl: $('ctx-url'),
  ctxTag: $('ctx-tag'),
  ctxCategory: $('ctx-category'),
  ctxSort: $('ctx-sort'),
  statPages: $('stat-pages'),
  statCards: $('stat-cards'),
  statDetails: $('stat-details'),
  log: $('log'),
  btnStart: $('btn-start'),
  btnStop: $('btn-stop'),
  btnCsv: $('btn-csv'),
  btnJsonl: $('btn-jsonl'),
  btnClear: $('btn-clear'),
  setMaxPages: $('set-maxpages'),
  setMaxItems: $('set-maxitems'),
  setDetails: $('set-details'),
  setConcurrency: $('set-concurrency'),
  setDelay: $('set-delay')
};

const STATUS_LABEL = { idle: 'idle', running: 'running', done: 'done', stopped: 'stopped', error: 'error' };

let pollTimer = null;

/* ---------- settings persistence ---------- */

function readSettings() {
  return {
    maxPages: Math.max(0, parseInt(els.setMaxPages.value, 10) || 0),
    maxItems: Math.max(0, parseInt(els.setMaxItems.value, 10) || 0),
    fetchDetails: els.setDetails.checked,
    detailConcurrency: Math.min(6, Math.max(1, parseInt(els.setConcurrency.value, 10) || 3)),
    detailDelayMs: Math.max(0, parseInt(els.setDelay.value, 10) || 900)
  };
}

async function persistSettings() {
  await chrome.storage.local.set({ [SETTINGS_KEY]: readSettings() });
}

async function restoreSettings() {
  const data = await chrome.storage.local.get(SETTINGS_KEY);
  const s = (data && data[SETTINGS_KEY]) || {};
  if (s.maxPages != null) els.setMaxPages.value = s.maxPages;
  if (s.maxItems != null) els.setMaxItems.value = s.maxItems;
  if (s.fetchDetails != null) els.setDetails.checked = !!s.fetchDetails;
  if (s.detailConcurrency != null) els.setConcurrency.value = s.detailConcurrency;
  if (s.detailDelayMs != null) els.setDelay.value = s.detailDelayMs;
}

/* ---------- state / UI refresh ---------- */

function setStatus(status) {
  const label = STATUS_LABEL[status] || status;
  els.status.textContent = label;
  els.status.className = 'chip chip-' + (status || 'idle');
  const running = status === 'running';
  els.btnStart.disabled = running;
  els.btnStop.disabled = !running;
}

function appendLog(state) {
  // reflect the worker's recent log lines + a few internal hints
  const lines = Array.isArray(state.log) ? state.log.slice(-25) : [];
  let text = lines.join('\n');
  if (state.exportReady) {
    text += (text ? '\n' : '') + `— ${state.productCount} products ready to export`;
  }
  els.log.textContent = text || 'Waiting for crawl...';
}

function showContext(tab) {
  if (!tab || !tab.url || !/booth\.pm/.test(tab.url)) {
    els.ctxUrl.textContent = 'open a BOOTH tag / browse page';
    els.ctxTag.textContent = '-';
    els.ctxCategory.textContent = '-';
    els.ctxSort.textContent = '-';
    return;
  }
  const ctx = C.parseContext(tab.url);
  els.ctxUrl.textContent = tab.url;
  els.ctxTag.textContent = ctx.contextTag || '-';
  els.ctxCategory.textContent = (ctx.contextCategory || '-') + (ctx.categoryPath ? ' (' + ctx.categoryPath + ')' : '');
  els.ctxSort.textContent = ctx.sortMode;
}

async function refresh() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  showContext(tab);

  let resp;
  try {
    resp = await chrome.runtime.sendMessage({ type: 'GET_STATE' });
  } catch (e) { /* worker starting up */ }

  if (resp && resp.ok && resp.state) {
    const s = resp.state;
    setStatus(s.status);
    els.statPages.textContent = s.currentPage || 0;
    els.statCards.textContent = fmt(s.productCount);
    els.statDetails.textContent = fmt(s.detailCount);
    els.btnCsv.disabled = !s.exportReady;
    els.btnJsonl.disabled = !s.exportReady;
    appendLog(s);
  } else {
    setStatus('idle');
    els.statPages.textContent = '0';
    els.statCards.textContent = '0';
    els.statDetails.textContent = '0';
    els.btnCsv.disabled = true;
    els.btnJsonl.disabled = true;
    els.log.textContent = 'No active crawl. Pick a BOOTH tag/browse page with live results, then Start.';
  }
}

/* ---------- actions ---------- */

async function startCrawl() {
  const settings = readSettings();
  await persistSettings();
  try {
    await chrome.runtime.sendMessage({ type: 'START_CRAWL', settings });
  } catch (e) {
    appendLog({ log: ['Failed to contact worker: ' + (e && e.message || e)] });
  }
  refresh();
}

function stopCrawl() {
  chrome.runtime.sendMessage({ type: 'STOP_CRAWL' }).catch(() => {});
}

async function exportData(kind) {
  const data = await chrome.storage.local.get(STORE_KEY);
  const state = data[STORE_KEY];
  if (!state || !state.products || !state.products.length) return;

  let content, mime, ext;
  if (kind === 'csv') {
    content = C.buildCsv(state.products);
    mime = 'text/csv;charset=utf-8';
    ext = 'csv';
  } else {
    content = C.buildJsonl(state.products);
    mime = 'application/x-ndjson';
    ext = 'jsonl';
  }
  const base = C.suggestFileName(state.products, 'booth');
  const filename = `${base}.${ext}`;

  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  try {
    await chrome.downloads.download({ url, filename, saveAs: false, conflictAction: 'uniquify' });
  } catch (e) {
    // Fallback: plain anchor download inside the popup.
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }
}

async function clearData() {
  await chrome.runtime.sendMessage({ type: 'CLEAR_DATA' }).catch(() => {});
  refresh();
}

/* ---------- wiring ---------- */

function bind() {
  els.btnStart.addEventListener('click', startCrawl);
  els.btnStop.addEventListener('click', stopCrawl);
  els.btnCsv.addEventListener('click', () => exportData('csv'));
  els.btnJsonl.addEventListener('click', () => exportData('jsonl'));
  els.btnClear.addEventListener('click', clearData);

  els.setMaxPages.addEventListener('change', persistSettings);
  els.setMaxItems.addEventListener('change', persistSettings);
  els.setDetails.addEventListener('change', persistSettings);
  els.setConcurrency.addEventListener('change', persistSettings);
  els.setDelay.addEventListener('change', persistSettings);
}

document.addEventListener('DOMContentLoaded', async () => {
  bind();
  await restoreSettings();
  await refresh();
  pollTimer = setInterval(refresh, 1200);
  window.addEventListener('unload', () => clearInterval(pollTimer));
});