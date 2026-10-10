/* ===========================================================
 * BOOTH Data Collector — content.js
 * Runs inside https://booth.pm/* pages.
 * - EXTRACT_LIST: parses current page cards, replies with products + nextUrl.
 * - FETCH_ITEM: same-origin fetch fallback for item detail pages (returns text).
 * - PROGRESS / SET_PILL: update a small floating status pill.
 * =========================================================== */

(function () {
  'use strict';

  const C = globalThis.BOOTH_COLLECTOR;

  /* ---------- floating status pill ---------- */

  let pill = null;
  function ensurePill() {
    if (pill && document.contains(pill)) return pill;
    pill = document.createElement('div');
    pill.id = 'booth-collector-pill';
    pill.style.cssText = [
      'position:fixed', 'right:12px', 'bottom:12px', 'z-index:2147483647',
      'background:rgba(20,24,35,0.92)', 'color:#fff', 'font:12px/1.5 system-ui,sans-serif',
      'padding:8px 12px', 'border-radius:8px', 'box-shadow:0 4px 14px rgba(0,0,0,.35)',
      'max-width:280px', 'white-space:pre-wrap', 'pointer-events:none',
      'user-select:none'
    ].join(';');
    pill.textContent = 'BOOTH Collector';
    document.documentElement.appendChild(pill);
    return pill;
  }
  function setPill(text) {
    try {
      const el = ensurePill();
      el.textContent = String(text);
      el.style.display = text ? 'block' : 'none';
    } catch (e) { /* ignore */ }
  }
  function removePill() {
    try {
      if (pill && pill.parentNode) pill.parentNode.removeChild(pill);
      pill = null;
    } catch (e) { /* ignore */ }
  }

  /* ---------- extraction ---------- */

  function extractFromPage() {
    const out = C.extractList(document, location.href);
    out.extractedAt = new Date().toISOString();
    out.hostUrl = location.href;
    return out;
  }

  /* ---------- message bridge ---------- */

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (!msg || typeof msg !== 'object') return;

    switch (msg.type) {
      case 'EXTRACT_LIST':
        try {
          sendResponse({ ok: true, ...extractFromPage() });
        } catch (e) {
          sendResponse({ ok: false, error: String(e && e.message || e) });
        }
        return false; // sync response

      case 'FETCH_ITEM':
        (async () => {
          try {
            const ctrl = new AbortController();
            const to = setTimeout(() => ctrl.abort(), 20000);
            const res = await fetch(String(msg.url), { credentials: 'include', signal: ctrl.signal });
            clearTimeout(to);
            if (!res.ok) {
              sendResponse({ ok: false, error: 'HTTP ' + res.status });
              return;
            }
            const text = await res.text();
            sendResponse({ ok: true, text: text, itemId: msg.itemId });
          } catch (e) {
            sendResponse({ ok: false, error: String(e && e.message || e) });
          }
        })();
        return true; // async response

      case 'PROGRESS':
        setPill(msg.text);
        sendResponse({ ok: true });
        return false;

      case 'HIDE_PILL':
        removePill();
        sendResponse({ ok: true });
        return false;

      default:
        return false;
    }
  });

  // Notify the background worker that this page finished loading (used for
  // pagination stepping: worker navigates tab, then waits for this).
  if (document.body && document.querySelector('li.item-card')) {
    chrome.runtime.sendMessage({
      type: 'PAGE_LIST_READY',
      hostUrl: location.href,
      cardCount: document.querySelectorAll('li.item-card').length
    }).catch(() => { /* worker may be sleeping; it re-extracts on demand anyway */ });
  }

  globalThis.BOOTH_PAGE_BRIDGE = { extractFromPage, setPill, removePill };
})();