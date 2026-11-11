# Listing-Agent Annex

Relocated from AGENTS.md for the current BOOTH and Creative Fabrica listing
agents. Pixiv material below is archived reference only; Pixiv is not a Codex
full-workflow stage. Creative Market follows its dedicated agent spec.

### Campaign mode

New-font launches default to `CAMPAIGN_MODE: FREE_ACTIVE` — a limited-time free
offer. The two BOOTH variants are always `Full Version` (the paid commercial
licence) and `Free Demo` (free while the campaign window is open; the same font
files, not a reduced subset, unless the seller supplies a genuinely reduced
demo). A whole-product-free offer or a different scope requires an explicit user
brief. Complete
permanent-paid work sets `CAMPAIGN_MODE: NORMAL_PAID`. Other modes:
`SAMPLE_ACTIVE` (a genuine reduced sample), `REPOST_UNLOCK`, `MILESTONE_PACK`,
`ANALYSIS`. Never infer a mode: write the `Campaign mode:` line explicitly.
`bin/campaign_mode.py` is the machine-readable source of this contract, and the
listing validators enforce it.

**Free-offer vocabulary** (`無料`, `フリーフォント`, `無料配布`, `無料DL`,
`無料ダウンロード`, `期間限定無料`, `フリー素材`, `お試し`, `無料版あり`,
`free font`) may enter the title, description, and tag set **only** while a free
mode is active and the offer is true. The permanent-paid copy must carry none of
it. `商用利用可` is **not** part of the free offer when only the `Free Demo` is
free: keep it pointing at the paid `Full Version`, never at the giveaway.

**A BOOTH free-mode listing must prove the offer, not assert it.** Its validator fails
the listing when any of these is missing:

- a `## CAMPAIGN STATE` section with `Campaign mode:`, `Free scope:`,
  `Start/end or unlock condition:`, and `Commercial Use state:`;
- the first line of the BOOTH customer description opening
  with the free offer **and** the limited-time window (`期間限定`/`今週`/`〜まで`);
- a BOOTH like/favourite call to action (`いいね`/`お気に入り`) in the copy;
- at least one free-offer tag in the selected BOOTH set.

For BOOTH, a paid-mode listing must select none of that vocabulary. Both copy
states are preserved so the seller can switch back after the promotion without
rewriting from memory: the permanent paid state and the active campaign state.

The zero-fee default path does not upload anywhere; agents produce copy/research
handoffs and never claim publication or upload. Neither mode adds
`無料`-family tags to the tag **bank** as permanent entries: they are
campaign-gated and expire with the offer.


---
## 🚧 LISTING-AGENT SCOPE (NON-NEGOTIABLE)

This scope applies to the current BOOTH and Creative Fabrica listing agents.
Pixiv rules in this annex are archived reference only. The scope does not apply
to preparation, naming, visual-prep, portfolio-marketing, or workflow agents.

Listing agents are copy-and-research specialists only. Their job is to research marketplace SEO language and produce the requested title, description, tags/keywords, and platform-required SEO meta fields.

- Use the user-supplied product description and facts as the primary source of truth. Listing agents may read relevant local product files, README/facts sheets, description documents, filenames, or existing listing text when that helps gather factual details for the copy. They should not systematically inspect the product or enumerate files for QA.
- Do not technically inspect, validate, or cross-check raw product files, ZIP/package contents, fonts, brush files, images, previews, metadata, dimensions, licenses, provenance, AI status, or upload requirements for completeness, correctness, packaging, or marketplace readiness. Reading relevant files for factual copy input is allowed.
- Do not run Fontspector, product/package validators, package/file/asset QA,
  image inspection, manifests, or any product-file validation. The copy-only
  listing validators explicitly required by an agent spec are allowed, and
  they may validate generated listing text only. Do not use them to
  cross-validate the product.
- Do not produce category/taxonomy, attributes, materials, pricing, license, media/alt-text, AI-content, packaging, or upload guidance unless the user explicitly requests that field.
- Keep research focused on competitor titles/descriptions/tags, autocomplete/search language, and other SEO evidence. Validate only copy-level SEO constraints that are necessary for the requested title, description, and tags.
- If required product facts are missing from the supplied description, first read relevant local documentation or product files that may contain the fact. If it is still missing, ask one concise question or mark it as unknown; never invent it.

Preparation and visual agents remain responsible for technical/file/asset QA. Listing agents must not duplicate that work.

---

---
## 📊 PLATFORM CONSTRAINT MATRIX (TAGS, CHARACTERS & VALIDATION)

Listing agents may enforce only the title, description, tag, and SEO-text constraints relevant to the copy they are producing. Product/file/asset, package, upload, license, media, and AI-content checks belong to preparation or visual agents and must not be duplicated here.

| Platform | Code | Output File Pattern | Tag Count | Tag Length Limit | Title Limit | Meta Title Limit | Meta Desc Limit | Special Rules & Mandatory Constraints |
|---|---|---|---|---|---|---|---|---|
| **BOOTH** | `booth` | `outputs/booth/{NUM}-{slug}-booth.md` | **18-25 validated tags** (target 20; above 25 fails; below 18 is allowed only by the validator's documented win-rate exemption) | None publicly documented | Target approximately 80 chars; no live editor check | N/A | N/A | Japanese-first title and description with selective English SEO terms; frozen local census evidence with snapshot date and numeric coverage counts; buyer-intent wording grounded in product facts and local evidence. Counts describe the stored Fonts-category snapshot, not current BOOTH-wide totals or page activity. When requested, include named `Full Version` and `Free Demo` variants and explain the campaign state. No seller setup, pricing calculation, package, media attachment, or upload checklist. |
| **Pixiv (archived)** | `pixiv` | `outputs/pixiv/{NUM}-{slug}-pixiv.md` | Historical reference | None documented | Historical reference | N/A | N/A | Archived marketplace workflow; not run by Codex `/full-workflow`. |
| **Creative Fabrica Fonts** | `creative-fabrica` | `outputs/creative-fabrica/{NUM}-{slug}-cf.md` | About 30 relevant tags (up to 40), no padding | See Agent 29 spec | See Agent 29 spec | N/A | N/A | Exact route vocabulary plus buyer-use and long-tail phrases from relevant comparable Designer Tags; one close, high-engagement PDP can support a phrase. Validator required; no upload claim. |

---


---
## 🏷️ TAG TRACKING & COUNTING RULES

1. **Marketplace-specific discovery**:
   - For non-BOOTH marketplaces with a documented or tested suggestion surface, run `node bin/search.js [--marketplace "marketplace"] --batch "tag1,tag2,..."` and apply that marketplace's evidence rules.
   - BOOTH font SEO research is local-only. Use `outputs/research/booth-live-collector/booth.db` through `bin/booth_tag_evidence.py` and `bin/query_booth_db.py`, plus `outputs/research/booth-font-tag-bank.md`, `outputs/research/booth-free-tag-evidence.md`, the saved `outputs/research/booth-demand/demand-signals.md`, and `outputs/booth/booth-tag-ledger.md` through `bin/booth_tag_ledger.py`. Never run live BOOTH searches, Google Suggest, `bin/search.js`, `bin/booth_tag_route_count.py`, or any page fetch/browser request for a BOOTH listing. This changes only on the user's explicit instruction.
   - The current census is a frozen `フォント・書体` category dataset (snapshot 2026-09-08; database rebuilt 2026-09-22). Read its local manifest/metadata for provenance on each run. Its counts are category coverage and competition signals, not current BOOTH-wide totals, page-life status, search volume, or demand. Never describe snapshot coverage as live or current activity. If a required fact is absent from local data, mark it unknown/unconfirmed, use a keyword phrase only, or omit it; do not fill the gap online.
   - Every selected BOOTH tag must carry an evidence row with generated canonical exact-tag/category URLs, local snapshot counts, paid-product and distinct-seller counts where available, snapshot coverage label, evidence tier, and product-fit reason. The URLs are route references generated by `bin/booth_evidence_table.py`; they are not fetched evidence. Do not count the current product, previous FontFairy products, or the seller's own shop as independent competitor repetition.
   - Before local BOOTH analysis, run `python3 bin/booth_owned_registry.py` and use it with the database's `pm_uses` information to exclude FontFairy-owned products from independent repetition and paid/seller counts. No BOOTH page is opened. Record the owned-product count and state that zero URLs were fetched.
   - Expand candidates locally across language-plus-object, style-plus-object, use-case-plus-object, commercial-rights, format/purchase-intent, English equivalents, and tag intersections represented in the snapshot. Select an expansion tag only when local coverage, independent paid-product evidence, and product fit support it; otherwise keep it as a keyword phrase or ledger rejection. Database coverage thresholds (0, 1–16, and 17+) describe snapshot coverage only, not current page life. `フリーフォント` and other free-offer terms are eligible **only** in an active free campaign (see Campaign mode); a free tag rejected in a `NORMAL_PAID` run is `MODE-CONDITIONAL`, not a dead lead, and may be evaluated against the local free cohort during a campaign.
   - Pixiv discovery must use exact/current tag or search routes plus fetched relevant works. Record the candidate term, tag/use status, visible relevant-work lower bound, distinct creators, newest relevant date when exposed, provider/fallback, product fit, and Tier A/B/C or REJECT decision in `outputs/pixiv/pixiv-tag-ledger.md`; snippets and visible views are not Pixiv demand or sales evidence.
2. **Tag Formatting**:
   - For marketplaces with valid suggestion scoring, order tags descending by the marketplace's suggest score. For BOOTH, order by product fit, local snapshot evidence tier, independent paid-product repetition, and category coverage instead.
   - Remove duplicate root words (synonym clustering).
   - Cap leading-word repetitions at a maximum of 3 tags starting with the same word.
3. **Strict Verification Check**:
   - Before writing the file, count the final tags list. If count $\neq$ required count, fix the list before outputting.
   - BOOTH has no stable documented public tag cap. Target **18-25 validated, non-redundant snapshot-supported tags** (aim for 20); above 25 fails. Below 18 is normally blocked, but the validator permits the documented exception only when every selected tag clears the measured win-rate gate. Never pad to reach the floor. Combine font-category terms with buyer-intent and use-case terms supported by the local census and product fit. Prefer the stronger category and intent evidence, keep other useful words in the description, and treat Japanese and English tags equally when their local evidence and product fit support them. Provide a local evidence row for every selected tag; no live cap check or page-life check is performed. Do not pad with generic phrases, near-synonym category words, or claims that snapshot coverage is current.
   - **Mandatory BOOTH validation gate**: after writing `outputs/booth/{NUM}-{slug}-booth.md`, the agent MUST run `python bin/validate_booth_listing.py outputs/booth/{NUM}-{slug}-booth.md` from the project root. The listing is NOT complete until the validator prints `[PASS]` (exit 0). Every `[FAIL]` must be resolved and the validator re-run until it passes. The validator is fail-closed (exit 1 on any failure) and enforces the 18-25 validated-tag contract (target 20), evidence-URL decoding, numeric counts, frozen-snapshot provenance/date/coverage status cells, the max-3 low-coverage-exception cap, stale-evidence warnings, and sibling-advisory overlap checks when `--booth-dir` is supplied. Hand-checking is not a substitute. Copy-level only; it never inspects product files, packages, images, licenses, pricing, or upload readiness.


---
## 🌐 NON-BOOTH WEB RESEARCH FETCH POLICY

This policy applies only to platform work that permits external research. It does
not apply to BOOTH: the BOOTH font listing stage is local-only and must not
fetch or search external BOOTH pages.

For every batch of unique page URLs:

- Use `mcp__firecrawl_scrape` as the primary page-content provider for
  every de-duplicated URL. Never have more than **6 Firecrawl calls in flight
  at once**. Split larger URL sets into sequential batches of at most six,
  wait for each batch to finish, record its results, and only then start the
  next batch.
- Use `mcp__serper_search` for high-recall discovery, URL replacement, and
  query-language expansion when Firecrawl rate-limits or when a page URL must
  be rediscovered. If Serper is unavailable, use Exa or another available
  search MCP and record that substitution.
- If Firecrawl rate-limits or fails for a URL, use the configured `webfetch`
  tool once for that URL. Do not repeatedly retry Firecrawl, and do not call
  Crawl4AI for current agent research.
- When a research set is larger than six URLs, use Serper/Exa alongside the
  Firecrawl batches for discovery and URL expansion; do not turn the larger
  set into one oversized Firecrawl burst.
- Search snippets discover URLs and wording; they do not prove page content,
  tag counts, activity, or sales. Record one row per URL in `RESEARCH NOTES`
  with Firecrawl status, complement provider, actual content provider, status,
  and fallback/limitation.


---

