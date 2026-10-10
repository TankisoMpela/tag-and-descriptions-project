# Listing-Agent Annex

Relocated from AGENTS.md so only listing agents load it (booth, pixiv,
creative-fabrica). Authoritative; the visual, preparation, and final-image
agents do not need it.

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

**A free-mode listing must prove the offer, not assert it.** The validators fail
the listing when any of these is missing:

- a `## CAMPAIGN STATE` section with `Campaign mode:`, `Free scope:`,
  `Start/end or unlock condition:`, and `Commercial Use state:`;
- the first line of the customer description (BOOTH) or caption (Pixiv) opening
  with the free offer **and** the limited-time window (`期間限定`/`今週`/`〜まで`);
- a BOOTH like/favourite call to action (`いいね`/`お気に入り`) in the copy;
- **BOOTH only:** at least one free-offer tag in the selected set. Pixiv tag
  selection is unchanged by the campaign — its own fresh discovery rules apply.

For BOOTH, a paid-mode listing must select none of that vocabulary; for Pixiv,
tag rules are identical in both modes and only the copy state changes. Both copy
states are preserved so the seller can switch back after the promotion without
rewriting from memory: the permanent paid state and the active campaign state.

The zero-fee default path does not upload anywhere; agents produce copy/research
handoffs and never claim publication or upload. Neither mode adds
`無料`-family tags to the tag **bank** as permanent entries: they are
campaign-gated and expire with the offer.


---
## 🚧 LISTING-AGENT SCOPE (NON-NEGOTIABLE)

This scope applies to the active marketplace listing agents (BOOTH, Pixiv, Creative Fabrica). It does not apply to the dedicated preparation, naming, visual-prep, portfolio-marketing, or workflow-orchestration agents.

Listing agents are copy-and-research specialists only. Their job is to research marketplace SEO language and produce the requested title, description, tags/keywords, and platform-required SEO meta fields.

- Use the user-supplied product description and facts as the primary source of truth. Listing agents may read relevant local product files, README/facts sheets, description documents, filenames, or existing listing text when that helps gather factual details for the copy. They should not systematically inspect the product or enumerate files for QA.
- Do not technically inspect, validate, or cross-check raw product files, ZIP/package contents, fonts, brush files, images, previews, metadata, dimensions, licenses, provenance, AI status, or upload requirements for completeness, correctness, packaging, or marketplace readiness. Reading relevant files for factual copy input is allowed.
- Do not run Fontspector, `validate_*` scripts, package/file/asset QA, image inspection, manifests, or any product-file validation. Do not reopen a generated listing to cross-validate the product.
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
| **BOOTH** | `booth` | `outputs/booth/{NUM}-{slug}-booth.md` | **18-25 validated tags** (target 20; fail closed below 18 or above 25) | None publicly documented | Target approximately 80 chars; verify live editor | N/A | N/A | Paid Digital item under visible `Source Materials` (select a font child only when exposed), Japanese-first native title/description with selective English SEO terms, live tag evidence with numeric counts + provider + date, buy-intent hook description, JPY pricing, exact package/license facts, first image as thumbnail, attached Digital File, and recorded proxy/overseas setting. Tag set combines the font-clear family (pages dominated by fonts: フォント・書体・オリジナルフォント・タイポグラフィ・font-family styles) with the high-volume buyer-intent family (商用利用可能・テロップ・ロゴ・サムネイル・レトロ・ポップ), which substitutes for the lower-value font-clear filler. When requested, include named `Full Version` and `Free Demo` variants, explain both, and set the `Free Demo` at ¥0 only while a free campaign window is open. No Pixiv posts or automatic upload. |
| **Pixiv** | `pixiv` | `outputs/pixiv/{NUM}-{slug}-pixiv.md` | Up to 10 per work | None documented | **32 characters (hard cap; the validator fails a longer title)** | N/A | N/A | Illustration discovery/funnel package; three distinct post angles, Japanese-first declarative captions, comma-separated tags, exact public BOOTH item URL/widget CTA, approved image order, AI-setting recommendation, provider research notes; no upload claim. |
| **Font Prep** | `prep` | `outputs/font-preparation/{NUM}-{slug}/` | N/A | N/A | N/A | N/A | N/A | User-supplied name; font-named binary folder; clean Commercial Use ZIP + clean Personal Use ZIP + demo-stamped Free-Trial-Demo ZIP (digits/punctuation watermark); root-level unbundled description; mechanical copies of Agent-27's prevalidated 3:2 and 1:1 sources including `thumbnail_japanese.png`; full-dimension JPEG copies targeting ≤500 KB in `visuals/main/` and `visuals/squares/`; main 1920x1080 16:9 video and the 2:1 `1920x960` promo video plus its script; metadata |

---


---
## 🏷️ TAG TRACKING & COUNTING RULES

1. **Marketplace-specific discovery**:
   - For marketplaces with a documented or tested suggestion surface, run `node bin/search.js [--marketplace "marketplace"] --batch "tag1,tag2,..."` and apply that marketplace's evidence rules.
   - For BOOTH, Google Suggest is Japanese query-language seed discovery only. The `--marketplace "booth"` option prefixes the query; it is not BOOTH autocomplete and its count must not be called BOOTH search volume.
   - BOOTH tags require live public-page validation through the exact-tag route and the `フォント・書体` category route, followed by a page-life check for active relevant listings. Treat 0 relevant font-category listings as dead/no coverage, 1–16 as low activity to record and deprioritize, and 17+ as the basic activity threshold; if only visible cards are available, record the lower bound and do not infer a total. Record overall exact-tag count, font-category count, activity status, and rejected/dead/low-activity candidates in `outputs/booth/booth-tag-ledger.md` as coverage/activity signals, not demand volume.
   - Every selected BOOTH tag must also carry an evidence row with the exact-tag URL, font-category URL, paid-product count, distinct-seller count, activity/provider status, evidence tier, and product-fit reason. Do not count the current product, previous FontFairy products, or the seller's own shop as independent competitor repetition.
   - Before live BOOTH research, the BOOTH agent must read existing `outputs/booth/*.md` listing files (excluding `booth-tag-ledger.md`) to build the FontFairy-owned product registry. Filter those product names/slugs and the FontFairy shop/seller pages before fetching; record owned results as skipped and never use them as competitor, repetition, paid-product, distinct-seller, or activity evidence.
   - Beyond the first five or six core tags, BOOTH requires a deliberate expansion pass across language-plus-object, style-plus-object, use-case-plus-object, commercial-rights, format/purchase-intent, English equivalents, and exact-tag intersection candidates. A low count is not automatically good or bad: select an expansion tag only when its exact route, font-category relevance, paid-product evidence, and product fit survive; otherwise keep it as a keyword phrase or ledger rejection. Test repeated `tags[]` intersections without treating an AND result as proof of a new compound tag. `フリーフォント` and the other free-offer terms are eligible **only** in an active free campaign (see Campaign mode); a free tag rejected in a `NORMAL_PAID` run is `MODE-CONDITIONAL`, not a dead lead, and may be retested under a campaign.
   - Authenticated BOOTH editor observation (2026-08-19): the `add Tag` field provides autocomplete for some terms but also permits a typed custom tag through an explicit Enter action. Autocomplete presence is not marketplace activity evidence, and autocomplete absence is not rejection; both require the public exact-tag/category/page-life checks. No visible numeric tag counter or maximum was exposed on the inspected editor page.
   - Pixiv discovery must use exact/current tag or search routes plus fetched relevant works. Record the candidate term, tag/use status, visible relevant-work lower bound, distinct creators, newest relevant date when exposed, provider/fallback, product fit, and Tier A/B/C or REJECT decision in `outputs/pixiv/pixiv-tag-ledger.md`; snippets and visible views are not Pixiv demand or sales evidence.
2. **Tag Formatting**:
   - For marketplaces with valid suggestion scoring, order tags descending by the marketplace's suggest score. For BOOTH, order by product fit, live evidence tier, comparable paid-product repetition, and font-category coverage instead.
   - Remove duplicate root words (synonym clustering).
   - Cap leading-word repetitions at a maximum of 3 tags starting with the same word.
3. **Strict Verification Check**:
   - Before writing the file, count the final tags list. If count $\neq$ required count, fix the list before outputting.
   - BOOTH has no stable documented public tag cap, but this workflow targets **18-25 validated, non-redundant live-confirmed tags** (aim for 20); the listing fails closed (reports BLOCKED) if fewer than 18 or more than 25 can be defended, rather than padding. The set combines the **font-clear family** from the latest research — tags whose unfiltered result pages are dominated by fonts (フォント 3,078, 書体 1,263, フォント・書体 1,428, オリジナルフォント 1,076, タイポグラフィ 636, デザインフォント 311, 欧文フォント 143, and font-family styles such as サンセリフ/カリグラフィ which are >85% font-share) — with the **high-volume buyer-intent / use-case family** (商用利用可能, 商用可, テロップ, ロゴ, サムネイル, レトロ, ポップ, ヴィンテージ) that has broad, font-relevant coverage even when its page is Materials-mixed. The buyer-intent family substitutes for the lower-value font-clear filler (e.g. 明朝, 丸文字, 装飾フォント) that has tiny volume. Prefer font-clear tags as the anchor; also spend a tag slot on the higher-volume intent terms that are genuinely font-relevant, and keep leftover use-case words in the description (BOOTH indexes description text). Frontload by strength and treat English tags as equal candidates when exact BOOTH evidence, font-category relevance, and product fit support them. Record the live cap if exposed and provide an evidence row for every selected tag. Every final candidate must also pass a live page-life check through Firecrawl first; if Firecrawl rate-limits or fails, use WebFetch once and Serper/Exa to discover a current alternate URL, recording the actual provider and limitation. Do not pad with generic web phrases, near-synonym category words, or present them as confirmed BOOTH tags.
   - **Mandatory BOOTH validation gate**: after writing `outputs/booth/{NUM}-{slug}-booth.md`, the agent MUST run `python bin/validate_booth_listing.py outputs/booth/{NUM}-{slug}-booth.md` from the project root. The listing is NOT complete until the validator prints `[PASS]` (exit 0). Every `[FAIL]` must be resolved and the validator re-run until it passes. The validator is fail-closed (exit 1 on any failure) and enforces the 18-25 validated-tag contract (target 20), evidence-URL decoding, numeric counts, provider+date+activity status cells, the max-3 low-activity-exception cap, stale-evidence warnings, and sibling-advisory overlap checks when `--booth-dir` is supplied. Hand-checking is not a substitute. Copy-level only; it never inspects product files, packages, images, licenses, pricing, or upload readiness.


---
## 🌐 WEB RESEARCH FETCH POLICY

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

