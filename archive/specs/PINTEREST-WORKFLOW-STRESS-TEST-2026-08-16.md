# Pinterest Workflow Stress Test

Date: 2026-08-16  
Scope: static/dry-run validation of the four-Pin Pinterest stage and its handoff after Behance; no Pinterest upload or publication was performed.

## Required sequence

`Creative Market (Agent 2) -> MasterBundles (Agent 8) -> Cubebrush (Agent 9) -> BOOTH (Agent 20) -> Behance (Agent 21) -> Pinterest (Agent 10)`

## Passed checks

- Agent 13 now defines four canonical outputs under `visuals/pinterest/`: `pinterest_1.png` through `pinterest_4.png`.
- `bin/compose_pinterest.py --variants 4 --count 3 --seed 2026` creates four 1000x1500 2:3 outputs without modifying the approved 3:2 inputs.
- The compositor selects from the complete `thumbnail_main.png` + `promo_N.png` pool, shuffles panel order deterministically, and does not force `thumbnail_main.png` to be the first panel.
- Agent 13's documented compression loop applies `pngquant` to every Pinterest variant with a `<=700000` byte target.
- Agent 10 requires exactly four Pin sections and the four canonical filenames.
- Every Pin requires a product-specific Creative Market URL shared identically by all four sections; a missing URL produces a blocked package instead of a store-root fallback.
- The Pinterest validator passes `tests/fixtures/pinterest-valid.md` and checks titles, descriptions, alt text, image names, related-topic limits, identical links, official research URLs, and duplicate copy.
- Both OpenCode registries expose the Pinterest specialist, command, and six-stage workflow; native Codex registration parses.
- The workflow skills and Agent 14 enforce Behance before Pinterest and prohibit parallel delegation.

## Research rules captured

The Pinterest agent records current official rules for standard Pins: 100-character titles, 2:3/1000x1500 guidance, descriptions up to 800 characters, alt text up to 500 characters, destination links, and up to 10 related topics. It treats Google Suggest results and other search-MCP results as language proxies, never Pinterest search-volume measurements.

Official sources used:

- [Create a Pin](https://help.pinterest.com/en/article/create-a-pin-from-an-image-or-video)
- [Review Pin specs](https://help.pinterest.com/en/article/review-pin-specs)
- [Add alternative text](https://help.pinterest.com/en/business/article/add-alternative-text-to-your-pins)
- [Pin performance and distribution](https://help.pinterest.com/en/business/article/pin-performance-and-distribution)
- [Pinterest creative best practices](https://business.pinterest.com/en-gb/creative-best-practices/?change_language=true&locale=en_gb)

Repository keyword-proxy discovery was run for `retro display font`, `vintage script font`, `cricut font`, `commercial use font`, `logo font`, `packaging font`, `wedding invitation font`, `font alphabet`, and `typography inspiration`. Most returned cached Google Suggest-style results; `font alphabet` encountered a temporary suggestion-service DNS failure. No result was labeled Pinterest demand.

## Negative checks

- The validator rejects a READY package with a store root or missing product-specific URL.
- The validator rejects fewer or more than four Pin sections.
- The validator rejects over-limit titles, descriptions, alt text, and related-topic lists.
- The validator rejects duplicate Pin titles/descriptions and image-number mismatches.

## Runtime caveats

- Firecrawl/search MCP availability is optional in the agent contract. If a provider is refused or unavailable, the agent must record that fact and continue with official Pinterest documentation and local keyword-proxy evidence.
- The workflow prepares a manual publishing package. It does not claim to publish Pins, schedule them, or verify Pinterest Analytics.

## Result

The four-Pin Pinterest stage is structurally ready to run after Behance. A real product run still requires an exact Creative Market product URL and the completed Agent 13 visual handoff.
