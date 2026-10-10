// content.js — BOOTH Dashboard / Edit page extractor
// Runs on https://manage.booth.pm/items/*  (list AND single item edit pages)
//
// Two modes:
//  - EDIT PAGE  (/items/{id}/edit): read the upload file table directly from
//    the current page DOM. Includes detailed diagnostics so unknown markup
//    can be reported back for a precise selector fix.
//  - DASHBOARD  (/items/): read every item card, then fetch per-variant
//    counts via same-origin hidden iframes to each item's /edit page.

(function () {
  "use strict";

  // ----- Message handling -----

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg && msg.type === "BOOTH_EXTRACT") {
      const isEdit = /\/items\/\d+\/edit(\?|$)/.test(location.pathname + location.search);
      if (isEdit) {
        const item = extractEditPageItem();
        sendResponse({
          mode: "edit",
          items: item ? [item] : [],
          count: item ? 1 : 0,
          diagnostics: item ? item.diagnostics : null
        });
      } else {
        // Dashboard list mode
        const cards = Array.from(document.querySelectorAll(".cell.item-name-with-stock"));
        const items = cards.map(extractCard);
        enrichWithDownloadCounts(items).then(() => {
          sendResponse({ mode: "dashboard", items, count: items.length });
        });
        return true; // async (iframe fetching)
      }
    }
  });

  // ----- Text helpers -----

  function textOf(el) {
    return el ? (el.textContent || "").trim() : "";
  }

  function visibleTextOf(el) {
    return el ? (el.innerText || "").trim() : "";
  }

  // ----- EDIT PAGE extraction (single product, from current DOM) -----

  function extractEditPageItem() {
    const idMatch = location.pathname.match(/\/items\/(\d+)\/edit/);
    const item = {
      mode: "edit",
      title: "",
      id: idMatch ? idMatch[1] : "",
      publicUrl: idMatch ? "https://booth.pm/items/" + idMatch[1] : "",
      editUrl: location.href.split("#")[0].split("?")[0],
      sales: "",
      tags: [],
      variants: [],
      downloadCounts: [],
      downloadError: "",
      diagnostics: null
    };

    item.title =
      textOf(document.querySelector("input[name='title'], #title")) ||
      visibleTextOf(document.querySelector(".item-title, h1, .dashboard-item-title")) ||
      "";

    item.sales =
      visibleTextOf(document.querySelector("*[class*='sales']")) ||
      visibleTextOf(document.querySelector("*[class*='stock']")) ||
      "";

    const res = parseDownloadCountsFromDoc(document);
    item.downloadCounts = res.counts;
    item.downloadError = res.counts.length ? "" : "no counts found on edit page";
    item.diagnostics = res.diagnostics;
    return item;
  }

  // ----- Download-count parsing with diagnostics -----

  // Pattern: <filename>.<ext> immediately followed by the download count.
  // Works whether the count is adjacent in text ("file.zip1") or on its own
  // line, because \s*? spans newlines. Found on the live page:
  //   const downloadCount = element.innerText.match(/Moonletter-Personal-Use\.zip(\d+)/)[1];
  function parseCountsFromText(text) {
    if (!text) return [];
    const re =
      /([^\n]+?)\.(zip|7z|rar|otf|ttf|woff2?|pdf|png|jpe?g|gif|ai|psd|svg|txt|html?|css|mp4|mov|ase|brush|json)\s*?(\d{1,6})/gi;
    const out = [];
    let m;
    while ((m = re.exec(text)) !== null) {
      const after = text.slice(re.lastIndex).replace(/^\s+/, "");
      // Guard against file-size numbers like "62 KB", "1.5 MB", "0 bytes",
      // "300 px" being mistaken for download counts.
      const isSize =
        /^\.\d+\s*(?:KB|MB|GB|TB|bytes?|KiB|MiB|GiB)/i.test(after) ||
        /^(?:KB|MB|GB|TB|bytes?|KiB|MiB|GiB|px|%)/i.test(after);
      if (isSize) continue;
      const filename = (m[1] || "").replace(/[\s:]+$/g, "").trim();
      if (!filename) continue;
      out.push({ filename: filename + "." + m[2].toLowerCase(), count: m[3] });
    }
    return out;
  }

  // Prefer the modal container (identified on the live page), falling back to
  // other containers and finally the whole body text.
  function parseDownloadCountsFromDoc(doc) {
    const diagnostics = {
      pageLength: 0,
      uploadSectionPresent: false,
      tailwindFilesModalFound: 0,
      anchorMatches: 0,
      textCenterMatches: 0,
      parsedVia: "",
      note: "",
      sampleHtml: ""
    };

    const counts = [];
    if (!doc.body) return { counts, diagnostics };

    const html = doc.body.innerHTML;
    diagnostics.pageLength = html.length;
    if (html.indexOf("アップロードしたファイル") >= 0) {
      diagnostics.uploadSectionPresent = true;
    }

    // --- Candidate text sources, in priority order ---

    // 1) The "Add/Edit Files" modal (Tailwind classes confirmed on live page).
    const modalEls = Array.from(
      doc.querySelectorAll('div.bg-white.relative.text-left[class*="desktop:w-[800px]"]')
    );
    if (!modalEls.length) {
      // Broader: any element whose class contains the "desktop:w-[" pattern
      modalEls.push(...Array.from(doc.querySelectorAll('[class*="desktop:w-["]')));
    }
    diagnostics.tailwindFilesModalFound = modalEls.length;

    let src = "";
    if (modalEls.length) {
      const text = textOf(modalEls[0]) || visibleTextOf(modalEls[0]);
      const c = parseCountsFromText(text);
      if (c.length) {
        counts.push(...c);
        diagnostics.parsedVia = "tailwind files modal";
        diagnostics.sampleHtml = html.substring(0, 0); // not captured here
      } else {
        src = text;
      }
    }

    // 2) Existing anchor markup (old BOOTH structure).
    if (!counts.length) {
      const anchors = Array.from(doc.querySelectorAll('a[class*="break-keep"], a.whitespace-nowrap'));
      diagnostics.anchorMatches = anchors.length;
      for (const a of anchors) {
        const filename = textOf(a);
        if (!filename) continue;
        const row = a.closest("li, tr, div, details");
        let count = "";
        if (row) {
          const ce = row.querySelector('div.text-center, *[class*="text-center"]');
          if (ce) {
            const t = textOf(ce).trim();
            if (/^\d[\d,]*$/.test(t)) count = t;
          }
        }
        if (filename) counts.push({ filename, count });
      }
      if (counts.length) {
        diagnostics.parsedVia = "legacy anchor markup";
      }
    }

    // 3) Full body text (both visible and hidden via textContent).
    if (!counts.length) {
      diagnostics.textCenterMatches =
        doc.querySelectorAll("div.text-center, *[class*='text-center']").length;
      const bodyText = textOf(doc.body);
      const c = parseCountsFromText(bodyText);
      if (c.length) {
        counts.push(...c);
        diagnostics.parsedVia = "body textContent scan";
      }
    }

    // Fallback diagnostics if still nothing.
    if (!counts.length) {
      diagnostics.note = diagnostics.note ||
        "No file+count pattern found. If you see counts on screen, open the 'Add/Edit files' / file management modal, then re-scan.";
    }

    // Deduplicate identical filename+count rows.
    const seen = new Set();
    const deduped = [];
    for (const c of counts) {
      const key = c.filename.toLowerCase() + "|" + c.count;
      if (!seen.has(key)) {
        seen.add(key);
        deduped.push(c);
      }
    }
    return { counts: deduped, diagnostics };
  }

  // ----- DASHBOARD card extraction -----

  function extractCard(card) {
    const item = {
      mode: "dashboard",
      title: "",
      id: "",
      publicUrl: "",
      editUrl: "",
      sales: "",
      tags: [],
      variants: [],
      downloadCounts: [],
      downloadError: ""
    };

    const link = card.querySelector("a.full-url") ||
      card.querySelector("a[href*='/items/']") ||
      card.querySelector('a[href*="booth.pm/items/"]');
    const href = link ? link.getAttribute("href") || "" : "";
    const idMatch = href.match(/(\d+)\/?$/);
    if (idMatch) {
      item.id = idMatch[1];
      item.publicUrl = "https://booth.pm/items/" + idMatch[1];
      item.editUrl = "https://manage.booth.pm/items/" + idMatch[1] + "/edit";
    }

    item.title =
      firstText(card, [
        ".dashboard-item-name", ".dashboard-items-name", ".item-name",
        ".item-title", ".dashboard-item-title", "h3", "h2",
        ".cell-top a", ".item-name-with-stock a"
      ]) || "";

    item.sales =
      firstText(card, [
        ".dashboard-item-sales", ".dashboard-items-sales",
        ".dashboard-item-stock", ".dashboard-items-stock",
        ".item-sales", ".sales", "*[class*='sales']", "*[class*='stock']"
      ]) || "";

    const tagsEl = card.querySelector(".dashboard-items-tags") ||
      card.querySelector("*[class*='tags']");
    if (tagsEl) {
      item.tags = Array.from(new Set(
        Array.from(tagsEl.querySelectorAll("a, .tag, span")).map(textOf).filter(Boolean)
      ));
    }

    const existingList = card.querySelector(".dashboard-items-variation");
    item.variants = existingList && existingList.children.length
      ? Array.from(existingList.querySelectorAll("li")).map(textOf).filter(Boolean)
      : parseVariantsFromCard(card);

    return item;
  }

  function firstText(root, selectors) {
    for (const s of selectors) {
      const el = root.querySelector(s);
      if (el) {
        const t = textOf(el);
        if (t) return t;
      }
    }
    return "";
  }

  function parseVariantsFromCard(card) {
    const raw = textOf(card);
    if (!raw) return [];
    const results = [];
    const re = /([^\n|;]{0,80}?)(?:Price)([\d,]+)\s*JPY(?:Stock-?Sales([\d,]*))(?:[\s\S]{0,20}?Proceeds)([\d,]*)\s*JPY/g;
    let m;
    while ((m = re.exec(raw)) !== null) {
      const name = m[1].replace(/\s*Undispatched(?:Unpaid|Paid)\s*-?\s*/g, "").trim();
      results.push(
        (name ? name + " | " : "") +
          "Price " + m[2] + " JPY, Sales " + (m[3] || "0") + ", Proceeds " + m[4] + " JPY"
      );
    }
    return results.length ? results : [];
  }

  // ----- Dashboard: fetch counts via hidden same-origin iframes -----

  function fetchDownloadCountsFrame(item) {
    return new Promise((resolve) => {
      if (!item.editUrl) return resolve([]);
      const frame = document.createElement("iframe");
      frame.src = item.editUrl;
      frame.style.display = "none";
      let done = false;
      const finish = (c) => {
        if (done) return;
        done = true;
        try { frame.remove(); } catch (_e) {}
        resolve(c);
      };
      setTimeout(() => finish([]), 10000);
      frame.onload = () => {
        setTimeout(() => {
          try {
            const d = frame.contentDocument;
            finish(d ? parseDownloadCountsFromDoc(d).counts : []);
          } catch (_e) {
            finish([]);
          }
        }, 700);
      };
      frame.onerror = () => finish([]);
      document.body.appendChild(frame);
    });
  }

  async function enrichWithDownloadCounts(items) {
    const CONCURRENCY = 2;
    let idx = 0;
    async function worker() {
      while (idx < items.length) {
        const i = idx++;
        const it = items[i];
        if (!it.editUrl) { it.downloadCounts = []; continue; }
        try {
          it.downloadCounts = await fetchDownloadCountsFrame(it);
          it.downloadError = it.downloadCounts.length ? "" : "no counts found on edit page";
        } catch (e) {
          it.downloadCounts = [];
          it.downloadError = String(e);
        }
      }
    }
    await Promise.all(Array.from({ length: Math.min(CONCURRENCY, items.length) }, worker));
  }
})();