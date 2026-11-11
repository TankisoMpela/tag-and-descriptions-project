# Shared Marketplace Research Checkpoint Protocol

This protocol applies to the BOOTH font agent (20), Creative Market font agent (2), and
Creative Fabrica font agent (29). It exists to preserve research findings before
context compaction and to prevent a search from expanding after the evidence is
already sufficient. BOOTH research is local-only: it has a zero-external-request
budget and uses the frozen local census and evidence files.

## Scratch paths

In normal write mode, create or resume one product-specific scratch file before
the first research decision. For platforms that allow external research, this
is before the first search or page fetch:

- BOOTH: `outputs/booth/.research/{NUM}-{product-slug}-research.md`
- Creative Market: `outputs/creativemarket/.research/{NUM}-{product-slug}-research.md`
- Creative Fabrica: `outputs/creative-fabrica/.research/{NUM}-{product-slug}-research.md`

These files are temporary research records, not customer-facing copy or
persistent tag ledgers. The existing `.gitignore` already excludes `outputs/`.
Keep the scratch file until the listing/package validator passes.

When an agent has an explicitly locked platform snapshot, its ordinary run may
have zero external requests. In that mode, create the scratch file before the
first local selection decision, record the snapshot path/date as the source
checkpoint, and finish with the same candidate, limitation, method, and
description/caption SEO audit fields. A frozen-source checkpoint is not a
reason to launch a refresh.

## Write timing

1. Read and resume the existing product scratch file before doing new research.
2. Record the product facts, current date, mode, output path, source provenance,
   provider availability, and finite budget before research begins.
3. For platforms that allow external research, after each completed search or
   page-fetch batch append a checkpoint before starting another batch. A batch
   may contain at most two concurrent Firecrawl page requests, and later batches
   must wait for the prior checkpoint. BOOTH makes no external requests; record
   checkpoints for local database/ledger queries instead.
4. Record failed, timed-out, blocked, duplicate, owned, and fallback requests;
   do not silently retry them or repeat a completed URL.
5. Before candidate expansion, record why the current candidate pool is
   insufficient and what next source or local query is needed. For platforms
   with external research, also record the remaining request budget and stop
   when it is exhausted.
6. Before reporting completion, append the final selection, rejected terms,
   complications, method audit, description SEO audit, and next-action status.

Assume compaction can happen after any tool call. A finding that exists only in
conversation memory is not recorded.

## Required scratch sections

Use these headings in every agent's scratch file. Platform-specific evidence
tables may follow them, but the checkpoint fields stay consistent.

```markdown
# {Product} {Platform} research scratch

## RUN
- Product number:
- Product slug:
- Final product name:
- Mode: normal write or dry run
- Research window:
- Assigned providers available:
- Output path:

## PRODUCT FACTS
- Supplied facts used for copy:
- Facts intentionally unknown:

## RESEARCH BUDGET
- Budget by category:
- Used:
- Remaining:
- Stop condition:

## FETCHED URL INDEX
| URL or request | Purpose | Batch | Assigned provider | Actual provider | Status | Retrieval date | Fallback / limitation | Evidence captured |
|---|---|---:|---|---|---|---|---|---|

## SEARCH / CANDIDATE LOG
| Phrase or query | Source | Candidate state | Evidence or result | Product-fit decision | Next action |
|---|---|---|---|---|---|

## EVIDENCE CHECKPOINTS
| Batch | Completed at | Requests completed | Findings written | Decisions made | Budget remaining |
|---:|---|---|---|---|---|

## COMPLICATIONS / LIMITATIONS
| Date | Request or practice | Complication | Impact on evidence | Workaround or stop decision |
|---|---|---|---|---|

## METHOD AUDIT
| Current practice | Why it is not optimal or what it cannot prove | Better bounded practice | Applied to this run |
|---|---|---|---|

## DESCRIPTION SEO AUDIT
| Phrase | Source and product fit | Field | Actual placement | Natural and factual? | Selected tag? | Decision |
|---|---|---|---|---|---|---|

## FINAL DECISIONS / NEXT ACTION
- Selected terms and evidence status:
- Rejected or keyword-only terms:
- Remaining limitation:
- Next action:
```

Updates should be append-only checkpoints where practical. If a context patch
fails, reread the file and append a recovery note rather than repeating the same
patch or web request. When a value is refreshed, retain the old value and add the
new date/provider instead of erasing the history.

## Finite budgets

These are total per-product-run budgets, not allowances per provider, candidate,
or tag. A fallback provider replaces a failed primary request; it is not a new
research loop.

| Agent | Discovery and evidence ceiling | Stop condition |
|---|---|---|
| BOOTH 20 | Frozen local census, tag bank, campaign evidence, saved query-language notes, and ledger; **zero external requests** | Stop after selecting 18-25 defensible tags from local snapshot evidence or exhausting the local candidate pool. Never refresh BOOTH evidence online; disclose the snapshot date and any missing/stale evidence. |
| Creative Market 2 | One bounded current Creative Market/browser pass: closest taxonomy surfaces, a representative Popular/Bestselling sample, and 2-3 relevant product pages; no Firecrawl or external SEO-volume workflow | Use supplied product facts to select distinct buyer-language phrases; distinguish observed marketplace wording from inferred queries. Stop when the bounded pass is complete and further candidates would be redundant or technical metadata. No fixed tag quota or demand claim. |
| Creative Fabrica 29 | Ordinary run: frozen bank, local tag DB, reusable ledger, prior listings, and product facts; zero external requests. Explicit refresh/gap-fill only: two official guides, Fonts browse, All Tags, at most one additional popular/style surface; 3 discovery queries total; up to 48 candidate phrases and exact-route checks; at most 6 comparable PDPs | Target about 30 relevant phrases, up to 40. Select exact-route tags plus relevant wording from comparable font `Designer tags`; a single close, high-engagement PDP may support a long-tail phrase, while independent recurrence strengthens it. `Suggested Categories` and `Font Style` are classification fields, not seller-tag evidence. Product facts filter relevance but do not invent tag wording. Ordinary runs stop at the local evidence limit; refresh stops near 30 or when the bounded pool is reviewed. Never pad the set. |

For platform passes that explicitly use Firecrawl, use the shared two-request
batch ceiling. Creative Market follows its specialist's bounded native
Creative Market/browser pass and does not use Firecrawl. BOOTH is local-only and
must not use Firecrawl, search tools, browser, or network fetches. No numeric
route count, snippet, favorite, view, review, or unlabeled `+K` value is demand
or sales evidence.

## Keyword and description SEO rule

Keywords are being used properly when the copy maps a small set of supported,
high-fit phrases to real placements and uses them in natural language. The
description audit must distinguish:

- selected platform tags, which require that platform's evidence;
- title/description/caption keywords, which may be useful without being native
  tags; and
- unsupported, stale, generic, or rejected wording, which must not enter copy.

For BOOTH, put the product name, strongest style/category phrase, and one
concrete use case in the opening one or two sentences, then use factual
specification sections. For Pixiv, use a readable title and caption opening as
one discovery cluster with a small rotated tag set; do not paste a tag block into
the caption. For Creative Fabrica, lead with the name and structural style or
buyer use, follow with supported applications, and then include verified format
or software facts. Do not repeat all tags mechanically, stuff near-synonyms, or
import a competitor's unsupported feature.

Every final listing must include a keyword/caption map or description SEO map,
and its research notes must say which mapped phrases were actually used,
title/caption-only, omitted, or rejected. A map of intended keywords is not
evidence that the description used them correctly; audit the final text itself.
