# Marketore Font Agent Stress Test

Date: 2026-08-20

## Scope

This stress test checks the deterministic parts of the new Marketore agent
against the banked live research. It does not claim to execute or replace the
language model's product-fit judgment, and it does not upload anything.

## Evidence under test

- `outputs/research/marketore-font-seo-research.md`
- `outputs/research/marketore-tags-vocabulary.json`
- `outputs/research/raw/marketore-fonts-page-top48.json`

## Checks

- The complete vocabulary contains 4,353 unique folded tag entries.
- The captured browse page contains 48 font listings.
- The research cache records the exact-10-tag pattern, first-sentence metadata
  extraction, and the observed Personal/Commercial/Extended price ratios.
- Recurring core tags are present without treating their high counts as demand.
- `Modern` is classified as saturated; `Font Duo` and `blackletter` are
  classified as ultra-niche from exact tag adoption.
- A positive listing fixture passes the Marketore validator with exactly 10
  canonical tags and ten evidence rows.
- A negative fixture is rejected for Creative Market taxonomy, a description
  below the live minimum, an invented tag, and incomplete tag evidence.

## Run

```text
python3 bin/stress_test_marketore.py
```

Result on 2026-08-20: all checks passed.

## Limitations kept explicit

- Vocabulary and public search counts are catalog-coverage/competition
  signals, not buyer demand or sales.
- The test cannot prove that a generated tag is semantically right for every
  future font; the agent must still apply the supplied-facts fit gate and
  record its reason for every tag.
- The live seller form may change. The agent must record any discrepancy from
  the locally observed category, subcategory, tag, description, or price
  controls instead of silently assuming the snapshot remains current.
