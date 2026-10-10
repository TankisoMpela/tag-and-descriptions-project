# Shared Marketplace Research Checkpoint Protocol

This protocol applies to the BOOTH font agent (20), Creative Market font agent (2), and
Creative Fabrica font agent (29). It exists to preserve research findings before
context compaction and to prevent a search from expanding after the evidence is
already sufficient.

## Scratch paths

In normal write mode, create or resume one product-specific scratch file before
the first external search or page fetch:

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
2. Record the product facts, current date, mode, output path, provider
   availability, and the finite budget before the first request.
3. After every completed search or page-fetch batch, append a checkpoint before
   starting another batch. A batch may contain at most two concurrent Firecrawl
   page requests, and later batches must wait for the prior checkpoint. Divide
   searches into small sequential batches the same way; never fire several
   search calls at the same time.
4. Record failed, timed-out, blocked, duplicate, owned, and fallback requests;
   do not silently retry them or repeat a completed URL.
5. Before any candidate expansion, write why the existing candidate pool is
   insufficient and how much budget remains. If no budget remains, stop.
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
| BOOTH 20 | Four seed routes; 48 candidate phrases; exact/category validation for the strongest 30 plus at most 8 alternates; one global cohort of 4-8 paid comparables; at most one optional tag intersection | Stop when 30 tags pass or the bounded pool/alternates are exhausted. Use the evidence-limited fallback for any lower defensible count. |
| Creative Market 2 | Local `outputs/creativemarket/*.md` corpus plus the derived `creative-market-font-tag-bank.md`; zero external requests in the default run | Stop after exactly 30 product-fit tags, one supported classification, and a passing `validate_cm_listing.py` result. Do not research for a higher score. |
| Creative Fabrica 29 | Ordinary run: frozen bank, local tag DB, reusable ledger, prior listings, and product facts; zero external requests. Explicit refresh/gap-fill only: two official guides, Fonts browse, All Tags, at most one additional popular/style surface; 3 discovery queries total; 48 candidate phrases; at most 48 exact-tag checks; at most 6 comparable PDPs | Ordinary run stops after the local evidence sheet and exactly-40 package. A refresh stops immediately when the gap is closed or 40 defensible tags are selected; never research for a higher score after the handoff is defensible. |

Use the shared two-request Firecrawl batch ceiling. Do not use a second page-life
request when the primary response already establishes a live page and the
required evidence; fetch a fallback only for an empty, ambiguous, blocked, or
failed response. No numeric route count, snippet, favorite, view, review, or
unlabeled `+K` value is demand or sales evidence.

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
