// popup.js — BOOTH Download Count & Product Details popup logic

"use strict";

const els = {
  scanBtn: document.getElementById("scanBtn"),
  copyBtn: document.getElementById("copyBtn"),
  csvBtn: document.getElementById("csvBtn"),
  debugBtn: document.getElementById("debugBtn"),
  collapseBtn: document.getElementById("collapseBtn"),
  content: document.getElementById("content"),
  statusText: document.getElementById("statusText"),
  statusDot: document.getElementById("statusDot"),
  itemCount: document.getElementById("itemCount"),
  toast: document.getElementById("toast")
};

let state = {
  items: [],
  tabId: null,
  expanded: true,
  diagnostics: null
};

function setStatus(text, mode) {
  els.statusText.textContent = text;
  els.statusDot.className = "status-dot " + (mode || "idle");
}

function showToast(msg) {
  els.toast.textContent = msg;
  els.toast.classList.add("show");
  setTimeout(() => els.toast.classList.remove("show"), 1800);
}

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
  );
}

// ----- Popup lifecycle: detect the active tab -----

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function isDashboardTab(url) {
  // Works on the seller items list OR a single item edit page.
  return url && /^https:\/\/manage\.booth\.pm\/items(\/\d+\/edit)?(\?|$)/.test(url);
}

// ----- Scan flow -----

async function runScan() {
  const tab = await getActiveTab();
  if (!tab || !isDashboardTab(tab.url || "")) {
    setStatus("Not on a BOOTH seller items page. Open the dashboard or an item edit page first.", "error");
    return;
  }
  state.tabId = tab.id;

  const isEditPage = /\/items\/\d+\/edit(\?|$)/.test((tab.url || "").split("#")[0]);
  setStatus(
    isEditPage
      ? "Reading this product's file table from the edit page…"
      : "Extracting dashboard cards & download counts…",
    "scanning"
  );
  els.scanBtn.disabled = true;

  try {
    // Ensure the content script is injected
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["content.js"]
      });
    } catch (_e) {
      /* already injected or fails - ignore */
    }

    // Ask content script to extract.
    let resp = await sendMessage(tab.id, { type: "BOOTH_EXTRACT" });
    if (!resp || !resp.items || resp.items.length === 0) {
      // One retry after a short delay
      await new Promise((r) => setTimeout(r, 800));
      resp = await sendMessage(tab.id, { type: "BOOTH_EXTRACT" });
    }

    if (!resp || !resp.items) {
      throw new Error("Could not read this page. Are you logged in?");
    }

    const items = resp.items;
    if (items.length === 0) {
      setStatus(
        isEditPage ? "No file table found on this edit page." : "No dashboard item cards found on this page.",
        "done"
      );
      els.itemCount.textContent = "0 items";
      els.copyBtn.disabled = true;
      els.csvBtn.disabled = true;
      els.scanBtn.disabled = false;
      renderEmpty(
        isEditPage
          ? "No file table found on this edit page."
          : "No items found. Make sure you're on the BOOTH seller items list and logged in."
      );
      return;
    }

    state.items = items;
    state.diagnostics = resp.diagnostics || null;
    els.itemCount.textContent = items.length + (isEditPage ? " product" : " items");
    const dlTotal = items.reduce((n, i) => n + (i.downloadCounts ? i.downloadCounts.length : 0), 0);
    if (isEditPage && dlTotal === 0 && state.diagnostics) {
      setStatus(
        "No counts found. Debug: upload section " +
          (state.diagnostics.uploadSectionPresent ? "present" : "MISSING") +
          ", file-link matches " + state.diagnostics.fileLinkMatches +
          ", text-center matches " + state.diagnostics.textCenterMatches +
          ". Click 🔧 Debug and paste the dump.",
        "error"
      );
    } else {
      setStatus(
        "Done — " + items.length + " product(s), " + dlTotal + " file-count row(s).",
        "done"
      );
    }
    render(items);
    els.copyBtn.disabled = false;
    els.csvBtn.disabled = false;
    els.debugBtn.disabled = !state.diagnostics;
    els.scanBtn.disabled = false;
  } catch (err) {
    console.error(err);
    setStatus("Error: " + err.message, "error");
    els.scanBtn.disabled = false;
    renderEmpty("Something went wrong: " + esc(err.message));
  }
}

function sendMessage(tabId, msg) {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, msg, (res) => {
      if (chrome.runtime.lastError) resolve(null);
      else resolve(res);
    });
  });
}

// ----- Rendering -----

function renderEmpty(msg) {
  els.content.innerHTML = '<div class="empty">' + msg + "</div>";
}

function render(items) {
  if (items.length === 0) return renderEmpty("No data to display.");

  const html = items.map((it, idx) => renderItem(it, idx)).join("");
  els.content.innerHTML =
    '<div id="itemsList" class="' + (state.expanded ? "" : "collapsed") + '">' + html + "</div>";
}

function renderItem(it, idx) {
  let variantsHtml = "";
  if (it.variants && it.variants.length) {
    variantsHtml =
      '<div class="section-label">Variants / Prices</div>' +
      '<table class="variants-table"><thead><tr><th>Variant</th></tr></thead><tbody>' +
      it.variants.map((v) => "<tr><td>" + esc(v) + "</td></tr>").join("") +
      "</tbody></table>";
  }

  let dlHtml = "";
  if (it.downloadCounts && it.downloadCounts.length) {
    dlHtml =
      '<div class="section-label">Per-File Download Counts</div>' +
      '<table class="downloads-table"><thead><tr><th>Filename</th><th class="num">Count</th></tr></thead><tbody>' +
      it.downloadCounts
        .map(
          (d) =>
            "<tr><td>" + esc(d.filename) + "</td><td class=\"num\">" + esc(d.count) + "</td></tr>"
        )
        .join("") +
      "</tbody></table>";
  } else if (it.downloadError) {
    dlHtml =
      '<div class="section-label">Download Counts</div><div style="color:var(--warn);font-size:11px">' +
      "Could not load: " + esc(it.downloadError) + "</div>";
  } else {
    dlHtml =
      '<div class="section-label">Download Counts</div><div style="color:#6b7280;font-size:11px">' +
      "No download counts found for this item.</div>";
  }

  const tagsHtml =
    it.tags && it.tags.length
      ? '<div class="tags">' + it.tags.map((t) => '<span class="tag">' + esc(t) + "</span>").join("") + "</div>"
      : "";

  return (
    '<div class="item" id="item-' + idx + '">' +
    "<h3>" + (idx + 1) + ". " + esc(it.title || it.publicUrl || "Untitled") + "</h3>" +
    '<div class="url">Public: ' +
    (it.publicUrl ? '<a href="' + esc(it.publicUrl) + '" target="_blank">' + esc(it.publicUrl) + "</a>" : "—") +
    "</div>" +
    '<div class="meta">' +
    "<span><b>Sales/Stock:</b> " + esc(it.sales || "—") + "</span>" +
    "<span><b>ID:</b> " + esc(it.id || "—") + "</span>" +
    "</div>" +
    tagsHtml +
    variantsHtml +
    dlHtml +
    "</div>"
  );
}

// ----- Clipboard & CSV -----

function toClipboardText(items) {
  const lines = [];
  for (const it of items) {
    lines.push("=== " + (it.title || it.publicUrl || "Untitled") + " (ID " + (it.id || "?") + ") ===");
    lines.push("Public URL: " + (it.publicUrl || "—"));
    lines.push("Edit URL:   " + (it.editUrl || "—"));
    lines.push("Sales/Stock: " + (it.sales || "—"));
    if (it.tags && it.tags.length) lines.push("Tags: " + it.tags.join(", "));
    if (it.variants && it.variants.length) lines.push("Variants: " + it.variants.join(" | "));
    lines.push("Download counts:");
    if (it.downloadCounts && it.downloadCounts.length) {
      for (const d of it.downloadCounts) lines.push("  " + d.filename + " = " + d.count);
    } else {
      lines.push("  (none)");
    }
    lines.push("", "----------------", "");
  }
  return lines.join("\n");
}

function toCSV(items) {
  const rows = [["Title", "ID", "Public URL", "Edit URL", "Sales/Stock", "Tags", "Filename", "Download Count"]];
  for (const it of items) {
    const base = [
      it.title || it.publicUrl || "",
      it.id || "",
      it.publicUrl || "",
      it.editUrl || "",
      it.sales || "",
      (it.tags || []).join("; ")
    ];
    if (it.downloadCounts && it.downloadCounts.length) {
      for (const d of it.downloadCounts) {
        rows.push([...base, d.filename, d.count]);
      }
    } else {
      rows.push([...base, "", ""]);
    }
  }
  return rows
    .map((r) =>
      r
        .map((cell) => {
          const c = String(cell == null ? "" : cell);
          return /[",\n]/.test(c) ? '"' + c.replace(/"/g, '""') + '"' : c;
        })
        .join(",")
    )
    .join("\n");
}

// ----- Event wiring -----

els.scanBtn.addEventListener("click", runScan);

els.copyBtn.addEventListener("click", async () => {
  if (!state.items.length) return;
  const text = toClipboardText(state.items);
  try {
    await navigator.clipboard.writeText(text);
    showToast("Copied to clipboard ✓");
  } catch (e) {
    showToast("Copy failed");
  }
});

els.csvBtn.addEventListener("click", () => {
  if (!state.items.length) return;
  const csv = toCSV(state.items);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "booth-dashboard-" + Date.now() + ".csv";
  a.click();
  URL.revokeObjectURL(url);
  showToast("CSV exported ✓");
});

els.collapseBtn.addEventListener("click", () => {
  state.expanded = !state.expanded;
  const list = document.getElementById("itemsList");
  if (list) list.classList.toggle("collapsed", !state.expanded);
  els.collapseBtn.textContent = state.expanded ? "⊟ Collapse all" : "⊞ Expand all";
});

els.debugBtn.addEventListener("click", async () => {
  const d = state.diagnostics;
  if (!d) { showToast("No diagnostics available"); return; }
  const text = [
    "===== BOOTH EXTENSION DEBUG DUMP =====",
    "pageLength: " + d.pageLength,
    "uploadSectionPresent: " + d.uploadSectionPresent,
    "fileLinkMatches (a.whitespace-nowrap / break-keep): " + d.fileLinkMatches,
    "textCenterMatches: " + d.textCenterMatches,
    "sectionHtmlLength: " + d.sectionHtmlLength,
    "note: " + (d.note || ""),
    "",
    "===== RAW HTML of 'アップロードしたファイル' section (first 4000 chars) =====",
    d.sampleHtml || "(empty)"
  ].join("\n");
  try {
    await navigator.clipboard.writeText(text);
    showToast("Debug dump copied — paste it to the agent ✓");
  } catch (e) {
    showToast("Copy failed");
  }
});

// On open, detect the current tab to give context
(async () => {
  const tab = await getActiveTab();
  if (!isDashboardTab(tab.url || "")) {
    els.statusText.textContent = "Not on BOOTH seller items page. Open manage.booth.pm/items and click Scan.";
  }
})();
