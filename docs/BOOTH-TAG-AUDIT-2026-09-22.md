# BOOTH tag audit — 2026-09-22

Measured against the 48 listings in `outputs/booth/` and the DB at
`outputs/research/booth-live-collector/booth.db`.

---

## 1. The tags themselves are good — better than the winners'

Comparing the tags actually in use against `analysis_tag_lift`:

| | tags in your listings | top-ranked competitors |
|---|---:|---:|
| **avg lift** | **2.53** | 1.96 |
| tags with lift ≥ 2.5 | **55%** | 33% |

`lift` is how much more likely top-ranked items are to use a tag than average.
Your listings' tags average **2.53** — *above* the 1.96 of the items that
outrank you.

The saturated vocabulary has correctly been dropped:

| saturated tag | coverage | in your listings |
|---|---:|---:|
| `フォント` | 3,092 items | **0 / 48** |
| `商用利用可` | 1,334 items | **1 / 48** |
| `font` | 1,620 items | 4 / 48 |
| `タイポグラフィ` | 640 items | 4 / 48 |

And the narrow high-yield cluster is in use:

| tag | median likes | in your listings |
|---|---:|---:|
| `ロゴ素材` | — | **35 / 48** |
| `タイポグラフィー` | 405 | **18 / 48** |
| `書体 商用利用` | 398 | **11 / 48** |
| `書体 商用利用 ダウンロード` | 415 | 8 / 48 |
| `フォント かっこいい` | — | 8 / 48 |

**Tag quality is not your problem, and hasn't been since the 2026-09-11
regeneration.** The earlier DB-based claim that these tags were missing was an
artifact of a stale crawl (2026-09-08) taken before the listings were rewritten.

---

## 2. But the validator calls 45 of 48 listings BLOCKED

Three separate mismatches between the listings and
`bin/validate_booth_listing.py`:

### a. Tag count — 45 / 48 fail

`MIN_BOOTH_TAGS = 18`. The listings carry:

| tags | listings |
|---:|---:|
| 8 | 1 |
| 10 | 5 |
| 11 | 2 |
| 12 | 8 |
| 13 | 8 |
| **14** | **20** |
| 15 | 1 |

Only **3 of 48** clear 18.

### b. Heading — 46 / 48 fail before the count is even checked

41 listings use `## BOOTH TAGS (10-14 VALIDATED TAGS, ONE PER LINE)`. The
validator's `TAG_SECTION_HEADINGS` alias list contains `10-25`, `12-20`, `25`,
`30`, `32` and others — but **not `10-14`**, and not `10-18` (3 listings). The
section is not found at all, so it reports *"missing or empty BOOTH tag
section"*.

### c. Evidence table — rows rejected for having 11 columns

The listings' TAG EVIDENCE table is:

    | Tag | Language | Exact tag URL | Font-category URL | Overall count |
      Font-category count | Young paid n / sellers / win-rate |
      Paid products / distinct sellers | Activity and provider status |
      Evidence tier | Product-fit reason |

That is **11 columns**. The validator requires **exactly 10** per row
(`len(columns) != 10`). The extra column is `Young paid n / sellers / win-rate`
— the young-cohort win-rate, which is the central evidence metric of the whole
method. The listings are *richer* than the validator expects.

---

## 3. The root cause: the spec and the validator contradict each other

`agents/agent-20-booth-fonts-specialist.md` lines 516-520:

> Build the first 13 from the strongest core, style, language, rights, and
> buyer-intent families, then use the tier-below candidates to reach 20 when they
> have product fit and measurable BOOTH evidence. […] **Do not pad with
> near-synonyms, unsupported use cases, or low-activity candidates merely to
> reach 20. If fewer than 20 are defensible, report the exact count and why;
> never manufacture tags.**

So the spec **explicitly authorises fewer than 20** when the remaining
candidates do not clear the evidence gate, and forbids padding.

The 2026-09-11 regeneration run did exactly that. The ledger records
`New set (12 tags …)`, `(13 tags)`, `(14 tags)` with notes like
*"All young win-rate ≥ 5.0% floor"* and *"0 exception slots"*. It applied a
strict ≥5% young-cohort win-rate gate and reported the honest count rather than
padding to 20.

The validator then marks every one of those listings **BLOCKED** for being under
18 — and the wrapper says:

> Before reporting completion run `validate_booth_listing.py` and **require
> `[PASS]`; every `[FAIL]` must be fixed and re-run.**

**An agent following its spec produces listings its validator rejects, and its
wrapper forbids it from reporting that outcome.** That is why 46 of 48 listings
"fail the validator" — not sloppiness, but a rule conflict.

---

## 4. What this means

**Your tag work is correct and stricter than the spec's count contract.** The
open question is which rule wins, and that is a policy decision, not a bug fix:

- If **quality wins** — the `10-14` heading reflects the real contract, and the
  validator, its heading aliases, and the evidence-table column count should be
  brought up to match the listings.
- If **the count wins** — 45 listings need 4-10 more defensible tags each, which
  requires either finding new tags that clear the ≥5% gate or lowering the gate
  itself. The spec currently forbids the second option.

Until one is chosen, every BOOTH run reports BLOCKED and the gate is noise.

---

## 5. What else these tools can do (tested, not theorised)

Everything below was run today. `[TESTED]` means I have output; `[INFERENCE]`
means reasoned but not verified.

| capability | status | value |
|---|---|---|
| **Google autocomplete** (serper) | **[TESTED] built** | **the only typed-query signal available** |
| **Tag route counts** (Firecrawl past Cloudflare) | **[TESTED] built** | supply/competition per tag |
| **Census refresh** | **[TESTED] feasible, not done** | **largest remaining win** |
| **GA4 item views** | **[TESTED] live** | views per font — the missing funnel number |
| BOOTH search volume | **[TESTED] does not exist** | — |
| GSC for `booth.pm` | **[TESTED] impossible** | — |
| Related-tag co-occurrence graph | [INFERENCE] | which tags cluster together |
| `?sort=new` rising-tag detection | **[TESTED] reachable** | new winners vs all-time lift |
| Competitor tag monitoring | [INFERENCE] | rival tagging changes over time |

### The biggest one: the census is stale

`--top-lanes`, the agent's tag-discovery tool, reads a census frozen at
**2026-09-08**. BOOTH's フォント・書体 category now reports **5,024** items
against the census's **4,958** — the category has grown ~1.3% in two weeks, and
every tag decision is being made against the older snapshot.

`bin/collect_booth_category.py` is fully resumable (`--resume`) and already
exists, so a refresh is a matter of running it, then:

    bin/refresh_booth_db.sh    # now also rebuilds analysis_* (fixed today)

`?sort=new` also works, so the same crawl can capture **rising** tags rather
than only all-time lift — more actionable for a new listing than a tag that was
strong in 2021.

### The autocomplete finding, in full

Mined via `bin/font_demand_signals.py`. Three classes that change copy:

**App terms** — buyers search by the tool they will use the font in:
`booth フォント クリスタ`, `アイビス`, `使い方 イラレ`. Near-absent from current
listings and from the tag bank.

**Licensing anxiety** — doubt surfaces as questions, and a hesitant buyer does
not convert:
`フォント 商用利用 バレる` ("will I get caught"), `商用利用 どこまで`,
`商用利用 とは`, `商用利用 確認 方法`, `booth フォント 安全`,
`booth フォント ダウンロードできない`. The description should answer these
directly rather than restating the licence.

**Free intent** — `無料`/`フリー` saturate the tail of nearly every seed,
confirming this is a free-dominant market. Relevant when choosing campaign mode.

Also surfaced: `フォント 商用利用 同人` and `商用利用可 英語`, plus wording
variants and typos (`booth fonto`/`fonnto`, `手書き風` vs `手書き`).

**Honest limit:** suggestion *order* is a popularity hint. There is no count,
and none can be derived. Never quote it as volume.

---

## 6. One-time demand harvest — what was recorded

Per-run querying was the wrong shape: the seeds return the same keywords every
time, so it would only make each run expensive. So the harvest was done **once**
and recorded under `outputs/research/booth-demand/`:

| artifact | size | contents |
|---|---:|---|
| `autocomplete-corpus.jsonl` | 290 KB | 2,314 rows — 1,090 distinct suggestions across 504 seeds |
| `route-counts.jsonl` | 8 KB | 112 BOOTH-wide exact-tag route counts |
| `demand-signals.md` | 9.5 KB | the distilled result the agent reads per run |
| `harvest-state.json` | 18 KB | resume bookkeeping |

`bin/harvest_booth_demand.py` reproduces all of it and is resumable in three
phases (`--autocomplete --expand`, `--routes --top N`, `--distil`). It is a
harvest tool, **not** a per-run tool; agent-20 reads `demand-signals.md` and
does not invoke the script during a listing.

### Correction: `配信素材` is not a low-competition tag

The distribution harvested earlier ranked tags by **font-category** count, which
made `配信素材` (194 font items) look like a narrow, uncontested space. Its
BOOTH-wide route count is **33,600** — it is a vast, generic, non-font tag.

The most competitive tags on BOOTH are mostly **not font tags at all**:

| tag | BOOTH-wide items |
|---|---:|
| `オリジナル` | 113,916 |
| `かわいい` | 66,581 |
| `素材` | 45,130 |
| `配信素材` | 33,600 |
| `TRPG素材` | 27,697 |
| `フリー素材` | 21,691 |
| `商用利用可` | 17,659 |

A high BOOTH-wide count with a low font-category count means the tag is
dominated by other product types — it will not surface a font to font buyers.
**Use both numbers: font-category count for relevance, route count for
competition.** `配信素材` fails the first test.
