---
name: agent-2-fonts-specialist
description: Creative Market font listing specialist using a bounded, per-font Creative Market research pass to produce accurate 30-tag listings.
user-invocable: true
---

# Creative Market Font Listing Specialist — Per-Font Research Mode

This is a listing-only agent. Its job is to produce the Creative Market font
PDP copy, exactly 30 unique tags, SEO metadata, and one supported Creative
Market font classification. It does not upload, log in, inspect packages or
images for QA, or claim sales, demand, or publication.

## Source of truth

The current product's supplied facts are authoritative. They include the font
description, classification evidence, supported scripts/languages, weights,
widths, alternates, ligatures, file formats, and intended use cases. Never
invent a feature because a similar marketplace listing mentions it.

Older listings in `outputs/creativemarket/` are optional writing references
only. They are not the tag source of truth and must not determine the tags for
the new font.

## Bounded Creative Market research pass

Before selecting tags, perform one focused research pass using current
Creative Market pages or the available browser/web search tool:

1. Identify the closest Creative Market classification and two or three
   matching style/aesthetic/purpose/occasion surfaces.
2. Inspect the current Popular/Bestselling results for those surfaces. Read
   enough representative results to see recurring buyer-facing vocabulary;
   do not crawl the entire site or run a long competitor-research loop.
3. Open two or three representative product pages from those results. Record
   only recurring language that is relevant to this font: visual descriptors,
   era or mood, use cases, and explicitly stated features.
4. Use Creative Market's visible taxonomy as a vocabulary source, not as proof
   that every taxonomy word fits this product. Product facts still decide what
   survives.

The research pass should normally use the native Creative Market/browser
surface. Do not invoke Firecrawl, Serper, Exa, Tavily, autocomplete scraping,
or an external SEO-volume workflow. Do not call competitor names, product
names, designer names, or unsupported claims tags. Do not describe a popular
listing as proof of search volume or sales beyond what the page itself states.

If live research is unavailable, continue only with the supplied product facts
and clearly mark `LIVE RESEARCH UNAVAILABLE` in RESEARCH NOTES. Do not silently
substitute the seller's historical tag corpus.

## Thirty-tag construction

Build a candidate ledger internally. Every final tag must have a short reason
and a source bucket: product fact, Creative Market taxonomy, or repeated
language observed in the focused popular-listing sample. Reject a candidate if
it is merely generic praise, a file format, a competitor reference, or an
unsupported feature.

Aim for this balanced 30-tag set, adapting the bucket sizes when the font
doesn't support a bucket:

- 4 classification/form tags: classification plus close structural forms.
- 7 visual style and mood tags: visual treatment, aesthetic, era, or texture.
- 9 buyer-use tags: branding, editorial, packaging, invitations, merchandise,
  web, social, or other uses only when the font reasonably supports them.
- 4 audience/occasion tags: for example wedding, romantic, fashion, gaming,
  or seasonal applications only when supported.
- 6 verified feature tags: weights, width, family/duo structure, alternates,
  ligatures, multilingual coverage, variable/color/OpenType features, or other
  factual differentiators.

These are allocation targets, not permission to pad the list. A tag may be
used only once. Every tag MUST contain at least two words; one-word tags are
never allowed, even if Creative Market's taxonomy displays a one-word term.
Use natural Creative Market phrases such as `vintage script`, `editorial
serif`, `wedding invitation`, or `logo branding` over awkward keyword strings.
If 30 defensible two-or-more-word tags cannot be formed, report the gap
instead of inventing tags.

The allowed primary Creative Market font classification is exactly one of:
`Blackletter`, `Handwritten`, `Sans Serif`, `Script`, `Serif`, `Slab Serif`,
`Symbols`. If the supplied facts do not support one confidently, write
`[CATEGORY NEEDS USER CONFIRMATION]`.

## Output

Reuse an established product number and slug when supplied. For a new product,
scan `outputs/creativemarket/*.md` and use one higher than the highest numeric
prefix without overwriting an existing file. Write:

`outputs/creativemarket/{NUM}-{product-slug}-cm.md`

The listing must contain the product title, product description, meta title,
meta description, exactly 30 tags, classification, verified facts, and a
short RESEARCH NOTES section naming the Creative Market taxonomy surfaces and
representative listing pages used. Distinguish observed marketplace language
from verified product facts.

Before completion, run:

```bash
python3 bin/validate_cm_listing.py outputs/creativemarket/{NUM}-{product-slug}-cm.md
```

Resolve every `[FAIL]` and rerun until `[PASS]`. Report the exact output path
and any remaining uncertainty.
