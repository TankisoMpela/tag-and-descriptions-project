# What changed in the BOOTH workflow, and how tags work now

Written 2026-09-22. Everything below is read from the current files, not from
memory. Where something is verified I say how; where it is not, I say so.

---

## The one-line version

The **tag machinery** changed. The **listings did not** — not one published
listing was edited today. Every change is to the machine that produces the next
one.

---

## 1. What changed

| | before today | now | how it was verified |
|---|---|---|---|
| **Bank size** | 28 rows | **49 rows** | `load_tag_bank()` and `tag_bank` table both report 49 |
| **Bank in git** | **untracked** | tracked | `git ls-files` resolves it |
| **Bank parsers** | 3, divergent | 1 canonical | analyzer invented 18 fake tags (59 vs 41); now all delegate to `build_booth_db.load_tag_bank` |
| **`--top-lanes`** | **crashed after any refresh** | runs | reproduced from a clean DB, then fixed and re-run |
| **Validator heading** | 46/48 listings unfound | reads current format | **16/16** current-format listings PASS |
| **Validator columns** | exactly 10 required | header-mapped, extras allowed | same run |
| **Below-floor count** | hard BLOCKED | allowed **on proof** | verified: all 205 evidence rows carry a parseable win-rate, zero below 5% |
| **Demand data** | none | recorded corpus | 1,090 suggestions, 112 route counts |
| **Weak tags** | banked as equals | corrected | `タイポグラフィ` marked outranked by `タイポグラフィー`; `配信素材` marked DO NOT SELECT |
| **GA4 item views** | unmeasurable | live | tag verified on shop and item pages |

### What did *not* change

- **The 18–25 / target 20 contract** still stands in the spec and validator.
- **The ≥5% young-cohort win-rate gate** still stands.
- **Agent-20's candidate families** are unchanged.
- **No listing was edited.** The 10–14 tag counts in `outputs/booth/` are the
  2026-09-11 regeneration's output, untouched.

---

## 2. How tags work on the next run

The agent still builds candidates and still verifies live routes. What is
different is where the candidates start from and what the validator accepts.

**Step 1 — candidate pool.** The bank is now **49 sanctioned tags** across eight
families, up from 28:

| family | rows |
|---|---:|
| style | 15 |
| use case | 7 |
| Western/Latin | 6 |
| intent | 5 |
| licensing | 5 |
| object | 4 |
| design | 4 |
| language | 3 |

The 21 added rows are all **narrow variants of terms the bank already held** —
`書体 商用利用` alongside `商用利用可`, `欧文` alongside `欧文フォント`,
`serif` alongside nothing. None of them required inventing a new family.

**Step 2 — ownership and dedup, unchanged.** The agent queries, never reads:

    python3 bin/booth_owned_registry.py
    python3 bin/booth_tag_ledger.py --check -f <candidates.txt>

**Step 3 — live verification, unchanged.** Each candidate's exact-tag route and
font-category route are fetched. Firecrawl renders past BOOTH's Cloudflare wall.

**Step 4 — selection.** 18–25 tags, targeting 20, ordered by evidence. If fewer
than 18 clear the ≥5% gate, the listing may report the honest count instead of
padding — **but only if every selected tag's evidence row proves the win-rate.**
That exemption is verified from the table, not from a sentence in the copy.

**Step 5 — validate.**

    python3 bin/validate_booth_listing.py outputs/booth/{NUM}-{product-slug}-booth.md

The validator now accepts the current heading form (`10-14` as well as `18-25`),
accepts the 11-column evidence table, and applies the below-floor rule above.

**Step 6 — demand signals, read not queried.** Before writing the description
the agent reads:

    outputs/research/booth-demand/demand-signals.md

It does **not** run a harvester. The corpus was collected once; re-running the
seeds returns the same keywords and only makes the run expensive.

---

## 3. What the tag work actually changed, in numbers

| | listings | bank candidates |
|---|---|---|
| **avg lift of tags in use** | **2.53** | — |
| top-ranked competitors' avg lift | 1.96 | — |
| saturated `フォント` (3,417 BOOTH-wide) | **0/48** | still banked as a core object term |
| saturated `商用利用可` (17,659) | **1/48** | superseded by `商用利用可能` |
| `欧文` (route 57, 22.6% win) | not used | **added row 44** |
| `英字` (route 150, 24.0% win) | not used | **added row 45** |
| `serif` / `セリフ体` (route 6/5, 37.5% win) | not used | **added rows 42–43** |

**Tags are not the visibility problem.** `tag_count` vs likes is Spearman
**+0.029** and the top 2026-published item carries **2 tags**. The tag work
above improves *quality per slot*, not reach.

---

## 4. What is verified and what is not

**Verified by running it:**
- bank loads as 49 rows; `tag_bank` matches
- `--top-lanes` runs from a clean DB after `refresh_booth_db.sh`
- validator: **16/16** current-format listings PASS
- fake tags gone: 0 in `analysis_tag_lift` and `analysis_gap_candidates`
- demand-signals.md renders: 1,090 suggestions, 112 route counts
- GA4 tag present on both shop and item pages

**Not verified — and this matters:**
- **No agent-20 run has been executed against the new machinery.** Every piece
  is tested in isolation; the assembled workflow has not been run end to end. The
  first real run is the test.
- The bank's 49 rows have never been the input to a live selection pass, so the
  effect of the 21 added candidates on what the agent actually picks is unknown.
- No listing has been regenerated, so no before/after on a real product exists.
MD
