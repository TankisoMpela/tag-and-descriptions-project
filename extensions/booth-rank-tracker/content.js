/*
 * BOOTH Rank Tracker — content script (MV3)
 * -----------------------------------------
 * Finds where all of your shop's products rank (page number + in-page position
 * + global rank) for the BOOTH tag/category listing page currently open.
 *
 * Works on server-rendered BOOTH search/browse pages (`booth.pm/en|ja/items`
 * and `booth.pm/en|ja/browse/...` with optional `tags%5B%5D=...` params).
 * Each `li.item-card` carries `data-product-brand` (= shop subdomain slug),
 * `data-product-position` (0-based, resets per page) plus title/id/price.
 * Those pages are server-rendered HTML, so remaining pages can be fetched
 * same-origin and parsed without navigating the tab.
 */
(function () {
  'use strict';

  const DEFAULT_SETTINGS = {
    shopSlug: 'papermoonstudio',
    maxPages: 50,     // safety cap on how many pages to fetch
    delayMs: 350      // politeness delay between page fetches
  };
  const PER_PAGE = 60; // BOOTH renders 60 cards per page
  const STORAGE_KEY_SETTINGS = 'brt_settings';
  const STORAGE_KEY_SNAPSHOTS = 'brt_snapshots';

  let settings = { ...DEFAULT_SETTINGS };
  let snapshots = {};
  let scanning = false;
  let abortRequested = false;
  let currentResults = [];

  /* ------------------------------------------------------------------ *
   * Pure helpers (exposed on window.__BRT__ for headless validation)    *
   * ------------------------------------------------------------------ */

  function parseCards(root) {
    const els = root.querySelectorAll('li.item-card');
    return Array.from(els).map(li => {
      const posRaw = li.getAttribute('data-product-position');
      return {
        id: (li.getAttribute('data-product-id') || '').trim(),
        name: (li.getAttribute('data-product-name') ||
          (li.querySelector('.item-card__title') && li.querySelector('.item-card__title').textContent) || '').trim(),
        price: (li.getAttribute('data-product-price') || '').trim(),
        brand: (li.getAttribute('data-product-brand') || '').trim(),
        position: posRaw !== null && posRaw !== '' ? parseInt(posRaw, 10) : null,
        shopName: (li.querySelector('.item-card__shop-name') &&
          li.querySelector('.item-card__shop-name').textContent || '').trim(),
        shopUrl: (li.querySelector('.item-card__shop-info a') &&
          li.querySelector('.item-card__shop-info a').getAttribute('href') || '').trim(),
        itemUrl: (li.querySelector('a[href*="/items/"]') &&
          li.querySelector('a[href*="/items/"]').getAttribute('href') || '').trim()
      };
    });
  }

  /**
   * Total page count for the current result set. Uses the dedicated
   * `a.nav-item.last-page` anchor when present; falls back to the largest
   * numbered pagination link; defaults to 1.
   */
  function getLastPage(root) {
    const last = root.querySelector('a.nav-item.last-page');
    if (last && last.getAttribute('href')) {
      try {
        const u = new URL(last.getAttribute('href'), window.location.href);
        const p = parseInt(u.searchParams.get('page'), 10);
        if (!Number.isNaN(p) && p > 0) return p;
      } catch (e) { /* fall through */ }
    }
    let maxN = 1;
    root.querySelectorAll('.pager a.nav-item').forEach(a => {
      const n = parseInt((a.textContent || '').trim(), 10);
      if (!Number.isNaN(n) && n > maxN) maxN = n;
    });
    return maxN;
  }

  /** Build the URL for a page of the same result set, preserving all
   *  existing query params (tags[], sort, etc.) by swapping only `page`. */
  function buildPageUrl(baseUrl, page) {
    const u = new URL(baseUrl);
    u.searchParams.set('page', String(page));
    return u.toString();
  }

  /** Reduce 'https://papermoonstudio.booth.pm/' -> 'papermoonstudio'. */
  function normalizeSlug(input) {
    return String(input || '')
      .trim().toLowerCase()
      .replace(/^https?:\/\//, '')
      .replace(/^www\./, '')
      .replace(/(\.booth\.pm).*$/, '$1')
      .replace(/\.booth\.pm.*$/, '')
      .replace(/\/+$/, '');
  }

  /** Primary: data-product-brand matches the slug.
   *  Fallback: shop URL host contains the slug. */
  function matchesShop(card) {
    const slug = normalizeSlug(settings.shopSlug);
    if (!slug) return false;
    const brand = (card.brand || '').toLowerCase();
    const shopUrl = (card.shopUrl || '').toLowerCase();
    return brand === slug ||
      shopUrl.includes(slug + '.booth.pm') ||
      shopUrl.includes('//' + slug + '.');
  }

  /** Attach page number + in-page position + global rank to every card. */
  function computeRanks(cards, page) {
    return cards.map((c, i) => {
      const pos = c.position !== null && c.position >= 0 ? c.position : i;
      return {
        ...c,
        page,
        inPageRank: pos + 1,
        globalRank: (page - 1) * PER_PAGE + pos + 1
      };
    });
  }

  /** BOM-prefixed CSV for Excel-friendly Japanese title handling. */
  function toCsv(matches) {
    const header = ['global_rank', 'page', 'in_page_rank', 'item_id', 'title', 'price',
      'shop_brand', 'shop_name', 'shop_url', 'item_url'];
    const esc = v => {
      const s = String(v === undefined || v === null ? '' : v);
      return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    };
    const rows = matches.map(m =>
      [m.globalRank, m.page, m.inPageRank, m.id, m.name, m.price,
        m.brand, m.shopName, m.shopUrl, m.itemUrl].map(esc).join(','));
    return '\uFEFF' + header.join(',') + '\n' + rows.join('\n');
  }

  /* ------------------------------------------------------------------ *
   * Storage                                                             *
   * ------------------------------------------------------------------ */

  async function saveSettings() {
    try { await chrome.storage.local.set({ [STORAGE_KEY_SETTINGS]: settings }); } catch (e) {}
  }

  async function loadSettings() {
    try {
      const o = await chrome.storage.local.get(STORAGE_KEY_SETTINGS);
      if (o[STORAGE_KEY_SETTINGS]) settings = { ...DEFAULT_SETTINGS, ...o[STORAGE_KEY_SETTINGS] };
    } catch (e) {}
  }

  async function loadSnapshots() {
    try {
      const o = await chrome.storage.local.get(STORAGE_KEY_SNAPSHOTS);
      snapshots = o[STORAGE_KEY_SNAPSHOTS] || {};
    } catch (e) { snapshots = {}; }
  }

  async function saveSnapshot(url, snap) {
    snapshots[url] = snap;
    try { await chrome.storage.local.set({ [STORAGE_KEY_SNAPSHOTS]: snapshots }); } catch (e) {}
  }

  /* ------------------------------------------------------------------ *
   * Fetch + crawl                                                       *
   * ------------------------------------------------------------------ */

  const sleep = ms => new Promise(r => setTimeout(r, ms));

  async function fetchAndParse(pageUrl) {
    const res = await fetch(pageUrl, {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    if (!res.ok) throw new Error('HTTP ' + res.status + ' for ' + pageUrl);
    const html = await res.text();
    const doc = new DOMParser().parseFromString(html, 'text/html');
    return { cards: parseCards(doc), lastPage: getLastPage(doc) };
  }

  async function runScan() {
    if (scanning) return;
    await bootPromise; // ensure settings + UI host are ready
    const baseUrl = window.location.href;
    const page1Cards = parseCards(document);
    if (!page1Cards.length) {
      setStatus('No product cards detected on this page. Open a BOOTH tag/category listing ' +
        '(e.g. /en/browse/Fonts?tags%5B%5D=font) first.', 'error');
      return;
    }
    const lastPage = Math.min(getLastPage(document), settings.maxPages);
    if (lastPage < 1) { setStatus('No pagination detected on this page.', 'error'); return; }

    scanning = true;
    abortRequested = false;
    currentResults = [];
    let scannedPages = 0;
    setScanningUI(true);
    setStatus('Scanning ' + lastPage + ' page(s) for shop "' + normalizeSlug(settings.shopSlug) + '"…', 'info');

    try {
      for (let p = 1; p <= lastPage; p++) {
        if (abortRequested) { setStatus('Aborted by user after page ' + scannedPages + '.', 'info'); break; }
        let cards;
        if (p === 1) {
          cards = page1Cards;
        } else {
          const pageUrl = buildPageUrl(baseUrl, p);
          const r = await fetchAndParse(pageUrl);
          if (!r.cards || !r.cards.length) break; // reached the last real page
          cards = r.cards;
        }
        computeRanks(cards, p).forEach(c => { if (matchesShop(c)) currentResults.push(c); });
        scannedPages = p;
        setProgress(p, lastPage);
        if (p < lastPage) await sleep(settings.delayMs);
      }
      currentResults.sort((a, b) => a.globalRank - b.globalRank);
      await saveSnapshot(baseUrl, {
        scannedAt: new Date().toISOString(),
        scannedPages,
        lastPage,
        pageUrl: baseUrl,
        slug: normalizeSlug(settings.shopSlug),
        matches: currentResults.map(({ globalRank, page, inPageRank, id, name, price, brand, shopName, shopUrl, itemUrl }) =>
          ({ globalRank, page, inPageRank, id, name, price, brand, shopName, shopUrl, itemUrl }))
      });
      setStatus('Scan complete: ' + currentResults.length + ' of your product(s) found across ' +
        scannedPages + '/' + lastPage + ' page(s).', 'ok');
      renderResults(currentResults);
    } catch (err) {
      setStatus('Scan stopped after error: ' + err.message, 'error');
      renderResults(currentResults);
    } finally {
      scanning = false;
      setScanningUI(false);
      setProgress(scannedPages, lastPage);
    }
  }

  /* ------------------------------------------------------------------ *
   * UI (shadow DOM so BOOTH styles cannot interfere)                    *
   * ------------------------------------------------------------------ */

  let host = null;
  let shadow = null;

  function shouldShowIfActive() {
    // Show the launcher on listing pages only (server-rendered grids or
    // listing routes). Avoids noise on item detail / non-BOOTH paths.
    const p = window.location.pathname;
    const q = window.location.search;
    return /\/items(\/|$|\?)/.test(p) || /\/browse\//.test(p) ||
      document.querySelector('li.item-card') !== null ||
      q.includes('tags%5B') || q.includes('tags[]');
  }

  function ensureHost() {
    if (host) return;
    host = document.createElement('div');
    host.id = 'brt-host';
    shadow = host.attachShadow({ mode: 'open' });
    (document.body || document.documentElement).appendChild(host);
    shadow.innerHTML = `
<style>
  :host { all: initial; }
  * { box-sizing: border-box; }
  .brt-fab {
    position: fixed; right: 16px; bottom: 16px; z-index: 2147483000;
    background: #0f172a; color: #fff; border: none; border-radius: 999px;
    padding: 12px 18px; font: 600 14px/1 system-ui, sans-serif; cursor: pointer;
    box-shadow: 0 4px 16px rgba(0,0,0,.35); transition: transform .12s ease;
  }
  .brt-fab:hover { transform: translateY(-2px); }
  .brt-panel {
    position: fixed; top: 16px; right: 16px; z-index: 2147483001;
    width: 460px; max-width: calc(100vw - 32px); max-height: calc(100vh - 32px);
    display: flex; flex-direction: column;
    background: #fff; color: #111827; border: 1px solid #d1d5db; border-radius: 12px;
    box-shadow: 0 12px 40px rgba(0,0,0,.28); font: 13px/1.45 system-ui, -apple-system, sans-serif;
    overflow: hidden;
  }
  .brt-head {
    display: flex; align-items: center; gap: 8px; padding: 10px 14px;
    background: #0f172a; color: #fff; cursor: move; user-select: none;
  }
  .brt-title { font-weight: 700; font-size: 14px; flex: 1; }
  .brt-btn-min, .brt-btn-close {
    background: transparent; border: none; color: #cbd5e1; cursor: pointer;
    font-size: 16px; line-height: 1; padding: 4px 6px; border-radius: 6px;
  }
  .brt-btn-min:hover, .brt-btn-close:hover { background: #1e293b; color: #fff; }
  .brt-body { padding: 12px 14px 14px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
  .brt-url { font-size: 11.5px; color: #6b7280; word-break: break-all; background: #f3f4f6; border-radius: 8px; padding: 8px 10px; }
  .brt-status { padding: 8px 10px; border-radius: 8px; font-weight: 600; }
  .brt-status.info { background: #eff6ff; color: #1d4ed8; }
  .brt-status.ok { background: #ecfdf5; color: #047857; }
  .brt-status.warn { background: #fffbeb; color: #b45309; }
  .brt-status.error { background: #fef2f2; color: #b91c1c; }
  .brt-progress { height: 6px; border-radius: 3px; background: #e5e7eb; overflow: hidden; }
  .brt-progress > div { height: 100%; width: 0%; background: #2563eb; transition: width .2s ease; }
  .brt-controls { display: flex; gap: 10px; flex-wrap: wrap; }
  .brt-field { display: flex; flex-direction: column; gap: 3px; }
  .brt-field label { font-size: 11px; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: .03em; }
  .brt-field input {
    font: 12.5px/1.3 system-ui, sans-serif; padding: 7px 9px; min-width: 150px;
    border: 1px solid #d1d5db; border-radius: 8px; color: #111827; background: #fff;
  }
  .brt-field input:focus { outline: 2px solid #bfdbfe; border-color: #2563eb; }
  .brt-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
  .brt-btn {
    font: 600 12.5px/1 system-ui, sans-serif; padding: 9px 12px; border-radius: 8px;
    cursor: pointer; border: 1px solid transparent;
  }
  .brt-btn-primary { background: #2563eb; color: #fff; }
  .brt-btn-primary:hover { background: #1d4ed8; }
  .brt-btn-primary:disabled { background: #93c5fd; cursor: not-allowed; }
  .brt-btn-abort { background: #fee2e2; color: #b91c1c; }
  .brt-btn-abort:hover { background: #fecaca; }
  .brt-btn-abort:disabled { background: #fde8e8; color: #f3b0b0; cursor: not-allowed; }
  .brt-btn-ghost { background: #fff; color: #374151; border-color: #d1d5db; }
  .brt-btn-ghost:hover { background: #f9fafb; }
  .brt-btn-ghost:disabled { color: #9ca3af; cursor: not-allowed; }
  .brt-summary { font-size: 12px; color: #374151; font-weight: 600; }
  .brt-hits { max-height: 240px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 8px; }
  .brt-hits table { width: 100%; border-collapse: collapse; font-size: 11.5px; }
  .brt-hits th {
    position: sticky; top: 0; background: #f9fafb; text-align: left; padding: 6px 8px;
    font-size: 10.5px; text-transform: uppercase; letter-spacing: .04em; color: #6b7280;
    border-bottom: 1px solid #e5e7eb;
  }
  .brt-hits td { padding: 6px 8px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }
  .brt-hits tr:hover td { background: #f8fafc; }
  .brt-id { font-family: ui-monospace, Menlo, monospace; font-size: 10.5px; color: #6b7280; }
  .brt-empty { color: #9ca3af; padding: 14px; text-align: center; }
  .brt-snap-note { font-size: 11px; color: #6b7280; }
  .brt-rank-badge {
    display: inline-block; min-width: 30px; text-align: center; padding: 2px 6px;
    border-radius: 999px; font-weight: 700; font-size: 11px;
    background: #dbeafe; color: #1e40af;
  }
</style>
<button class="brt-fab" id="brt-fab" title="Open BOOTH Rank Tracker">🏷 Rank</button>
<div class="brt-panel" id="brt-panel" hidden>
  <div class="brt-head" id="brt-head">
    <span class="brt-title">BOOTH Rank Tracker</span>
    <button class="brt-btn-min" id="brt-min" title="Minimize">—</button>
    <button class="brt-btn-close" id="brt-close" title="Close">✕</button>
  </div>
  <div class="brt-body">
    <div class="brt-url" id="brt-url"></div>
    <div class="brt-status" id="brt-status">Ready</div>
    <div class="brt-progress" id="brt-progress"><div></div></div>
    <div class="brt-controls">
      <div class="brt-field">
        <label for="brt-slug">Shop slug or URL</label>
        <input id="brt-slug" placeholder="papermoonstudio">
      </div>
      <div class="brt-field">
        <label for="brt-maxpages">Max pages</label>
        <input id="brt-maxpages" type="number" min="1" max="500" style="min-width:90px">
      </div>
    </div>
    <div class="brt-buttons">
      <button class="brt-btn brt-btn-primary" id="brt-scan">Scan tag rankings</button>
      <button class="brt-btn brt-btn-abort" id="brt-abort" disabled>Abort</button>
      <button class="brt-btn brt-btn-ghost" id="brt-csv" disabled>Export CSV</button>
    </div>
    <div class="brt-snap-note" id="brt-snap"></div>
    <div class="brt-summary" id="brt-summary"></div>
    <div class="brt-hits" id="brt-hits"></div>
  </div>
</div>
`;
    shadow.getElementById('brt-fab').addEventListener('click', togglePanel);
    shadow.getElementById('brt-min').addEventListener('click', minimize);
    shadow.getElementById('brt-close').addEventListener('click', () => {
      shadow.getElementById('brt-panel').hidden = true;
    });
    shadow.getElementById('brt-scan').addEventListener('click', runScan);
    shadow.getElementById('brt-abort').addEventListener('click', () => { abortRequested = true; });
    shadow.getElementById('brt-csv').addEventListener('click', exportCsv);
    shadow.getElementById('brt-slug').addEventListener('input', onSlugInput);
    shadow.getElementById('brt-maxpages').addEventListener('input', onMaxPagesInput);
    // keep guest panel from capturing drag on inputs
    shadow.getElementById('brt-head').addEventListener('mousedown', onHeadDragStart);
    shadow.getElementById('brt-slug').value = settings.shopSlug;
    shadow.getElementById('brt-maxpages').value = settings.maxPages;
    populateUrlAndSnapshot();
  }

  function togglePanel() {
    const panel = shadow.getElementById('brt-panel');
    const fab = shadow.getElementById('brt-fab');
    panel.hidden = !panel.hidden;
    fab.hidden = !panel.hidden;
    if (!panel.hidden) populateUrlAndSnapshot();
  }

  function minimize() { shadow.getElementById('brt-panel').hidden = true; shadow.getElementById('brt-fab').hidden = false; }

  function setStatus(text, kind) {
    const el = shadow.getElementById('brt-status');
    el.textContent = text;
    el.className = 'brt-status ' + (kind || 'info');
  }

  function setProgress(cur, total) {
    const bar = shadow.getElementById('brt-progress').firstElementChild;
    bar.style.width = (total ? Math.round(cur / total * 100) : 0) + '%';
  }

  function setScanningUI(on) {
    shadow.getElementById('brt-scan').disabled = on;
    shadow.getElementById('brt-abort').disabled = !on;
    shadow.getElementById('brt-csv').disabled = on || currentResults.length === 0;
  }

  function populateUrlAndSnapshot() {
    shadow.getElementById('brt-url').textContent = window.location.href;
    const snap = snapshots[window.location.href];
    const el = shadow.getElementById('brt-snap');
    if (snap) {
      el.innerHTML = '📦 Last scan: ' + new Date(snap.scannedAt).toLocaleString() +
        ' · ' + snap.matches.length + ' product(s) found in ' + snap.scannedPages + '/' + snap.lastPage + ' page(s).' +
        ' <button class="brt-btn brt-btn-ghost" id="brt-restore" style="padding:4px 8px">Reload snapshot</button>';
      shadow.getElementById('brt-restore').addEventListener('click', () => {
        currentResults = snap.matches.map(m => ({ ...m, inPageRank: m.inPageRank, globalRank: m.globalRank }));
        setStatus('Snapshot loaded (' + new Date(snap.scannedAt).toLocaleString() + ').', 'info');
        renderResults(currentResults);
      });
    } else {
      el.textContent = '';
    }
  }

  function renderResults(matches) {
    const hits = shadow.getElementById('brt-hits');
    const summary = shadow.getElementById('brt-summary');
    if (!matches.length) {
      summary.textContent = '';
      hits.innerHTML = '<div class="brt-empty">No products from your shop found in the scanned pages.</div>';
    } else {
      summary.textContent = '🏆 ' + matches.length + ' of your product(s) ranked in this tag/category.';
      let rows = '<table><thead><tr><th>Global</th><th>Page</th><th>Pos</th><th>Item</th><th>Title</th><th>Price</th></tr></thead><tbody>';
      for (const m of matches) {
        const link = m.itemUrl
          ? '<a href="' + m.itemUrl + '" target="_blank" rel="noreferrer">' + (m.name || m.id || '-') + '</a>'
          : (m.name || m.id || '-');
        rows += '<tr><td><span class="brt-rank-badge">' + m.globalRank + '</span></td>' +
          '<td>' + m.page + '</td><td>' + m.inPageRank + '</td>' +
          '<td class="brt-id">' + (m.id || '-') + '</td>' +
          '<td>' + link + (m.shopName ? '<br><span class="brt-id">' + m.shopName + '</span>' : '') + '</td>' +
          '<td>' + (m.price !== '' ? '¥' + Number(m.price).toLocaleString() : '-') + '</td></tr>';
      }
      rows += '</tbody></table>';
      hits.innerHTML = rows;
    }
    shadow.getElementById('brt-csv').disabled = !matches.length;
  }

  function exportCsv() {
    if (!currentResults.length) return;
    const csv = toCsv(currentResults);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'booth-rank-' + normalizeSlug(settings.shopSlug) + '-' +
      new Date().toISOString().slice(0, 10) + '.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }

  function onSlugInput() {
    settings.shopSlug = shadow.getElementById('brt-slug').value.trim();
    saveSettings();
  }

  function onMaxPagesInput() {
    let v = parseInt(shadow.getElementById('brt-maxpages').value, 10);
    if (Number.isNaN(v) || v < 1) v = DEFAULT_SETTINGS.maxPages;
    settings.maxPages = Math.min(500, v);
    shadow.getElementById('brt-maxpages').value = settings.maxPages;
    saveSettings();
  }

  // Simple drag of the panel by its header.
  let drag = null;
  function onHeadDragStart(ev) {
    if (ev.target.closest('button')) return;
    const panel = shadow.getElementById('brt-panel');
    const rect = panel.getBoundingClientRect();
    drag = { dx: ev.clientX - rect.left, dy: ev.clientY - rect.top };
    const move = e => {
      panel.style.left = (e.clientX - drag.dx) + 'px';
      panel.style.top = (e.clientY - drag.dy) + 'px';
      panel.style.right = 'auto';
    };
    const up = () => {
      document.removeEventListener('mousemove', move);
      document.removeEventListener('mouseup', up);
      drag = null;
    };
    document.addEventListener('mousemove', move);
    document.addEventListener('mouseup', up);
  }

  /* ------------------------------------------------------------------ *
   * Boot                                                                *
   * ------------------------------------------------------------------ */

  async function init() {
    await loadSettings();
    await loadSnapshots();
    if (shouldShowIfActive()) ensureHost();
  }

  const bootPromise = init();

  // Surface pure helpers for headless validation (isolated world only).
  window.__BRT__ = {
    DEFAULT_SETTINGS,
    parseCards,
    getLastPage,
    buildPageUrl,
    normalizeSlug,
    matchesShop,
    computeRanks,
    toCsv,
    runScan,
    _results: () => currentResults.map(x => ({ ...x })),
    _setSettings: s => { settings = { ...settings, ...s }; }
  };
})();