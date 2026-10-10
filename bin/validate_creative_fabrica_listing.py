#!/usr/bin/env python3
"""Validate the Creative Fabrica font listing-copy handoff.

This is a copy/research validator only. It deliberately does not inspect
font files, packages, images, licenses, provenance, or upload readiness.
Creative Fabrica has no stable public author tag cap in the research baseline;
the exactly-40-tag block is this project's internal handoff contract.

Quality gates for the tag set (added 2026-09-09 after a live PDP census showed
the field runs at 40-50+ visible designer tags, not 30):
- format terms (OTF, TTF, WOFF, WOFF2, OpenType) are not search tags;
- junk adjectives (best seller, popular, trendy, cute) are not filler;
- near-duplicate intent families (Sport/Sports/Sport Font,
  Energy/Energetic, Headline/Headlines/Headline Font, and singular/plural
  or {word}/{word} font(s) variants) collapse to one tag rather than padding,
  while distinct compound routes (e.g. Funky Font vs Funky Letters) are kept.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path


TAG_HEADINGS = (
    "TAGS (40 - Creative Fabrica research package, comma-separated)",
    "TAGS (up to 40 - Creative Fabrica research package, comma-separated)",
)
SEO_MAP_HEADING = "DESCRIPTION SEO MAP"
MAX_TITLE_CHARS = 30
MIN_DESCRIPTION_WORDS = 150
MAX_DESCRIPTION_WORDS = 350
EXPECTED_TAG_COUNT = 40
EVIDENCE_CLASSES = {
    "canonical category",
    "canonical tag route",
    "pdp recurrence",
    "independent wording",
    "verified product fact",
    # A tag already measured in outputs/research/creative-fabrica-tag-bank.json:
    # cite its tag-page URL plus the bank snapshot date instead of re-fetching.
    "strategy snapshot route",
}

# A bank snapshot older than this must be refreshed before it can back a tag.
SNAPSHOT_MAX_AGE_DAYS = 45

# The real Creative Fabrica font-tag route is the PLURAL compound page
# /tag/<modifier>-fonts/ (or the /fonts/<category>-fonts/ equivalent). The bare
# index (/tag/, /fonts/) and the singular /tag/<modifier>-font/ form carry no
# published count and must not be accepted as tag evidence.
FONT_ROUTE_RE = re.compile(r"creativefabrica\.com/(?:tag|fonts)/[a-z0-9-]+-fonts/?(?:[\s\)]|$)", re.IGNORECASE)
PRODUCT_URL_RE = re.compile(r"creativefabrica\.com/product/[a-z0-9-]+/", re.IGNORECASE)
TAG_ROUTE_CLASSES = {"canonical category", "canonical tag route", "strategy snapshot route", "independent wording"}
RESEARCH_SECTIONS = (
    "RUN",
    "PRODUCT FACTS",
    "RESEARCH BUDGET",
    "FETCHED URL INDEX",
    "SEARCH / CANDIDATE LOG",
    "EVIDENCE CHECKPOINTS",
    "COMPLICATIONS / LIMITATIONS",
    "METHOD AUDIT",
    "DESCRIPTION SEO AUDIT",
    "FINAL DECISIONS / NEXT ACTION",
)
REQUIRED = [
    "STATUS",
    "PRODUCT TITLE",
    "PRODUCT DESCRIPTION",
    SEO_MAP_HEADING,
    "CATEGORY",
    "TAG EVIDENCE",
    "COMPARABLE PDP SIGNALS",
    "RESEARCH NOTES",
]

PRICE_RE = re.compile(
    r"(?:[$€£]\s*\d|\b\d+(?:\.\d+)?\s*(?:usd|eur|gbp)\b|\b(?:price|pricing|discount|sale|off)\b)",
    re.IGNORECASE,
)
LICENSE_RE = re.compile(r"\b(?:personal|commercial|extended)\s+license\b|\blicense\s+(?:terms|file|information)\b", re.IGNORECASE)
CONTACT_RE = re.compile(r"(?:https?://|www\.|@[A-Za-z0-9_.-]+\.[A-Za-z]{2,}|\b(?:email|contact)\s+me\b)", re.IGNORECASE)

# Quality gates for the extra tag slots: format terms are facts, not search
# tags; junk adjectives are filler even when leaders publish them.
FORMAT_TAGS = {"otf", "ttf", "woff", "woff2", "opentype"}
JUNK_TAGS = {"best seller", "popular", "trendy", "cute"}
# Creative Fabrica FONT tags are the compound `<modifier> Font(s)` form. A bare
# one-word tag resolves to a broader graphics tag (measured: /tag/kids/ has no
# count and shows SVGs/graphics, /tag/kids-fonts/ = "Kids Fonts" 14,188), so a
# standalone one-word tag is never valid font-tag evidence.
MAX_SINGLE_WORD_TAGS = 0
# Intent families that differ only by singular/plural or a trailing " font":
# keep the single strongest tag instead of padding the set.
NEAR_DUPLICATE_FAMILIES = (
    {"sport", "sports", "sport font"},
    {"energy", "energetic"},
    {"headline", "headlines", "headline font"},
)


def sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(1).strip()] = text[match.end() : end].strip()
    return result


def first_content(value: str | None) -> str:
    if not value:
        return ""
    for line in value.splitlines():
        line = line.strip()
        if line and not line.startswith("[") and not line.startswith("<!--"):
            return line
    return ""


def evidence_rows(value: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in value.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or cells[0].casefold() in {"#", "tag"}:
            continue
        if all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def is_near_duplicate_pair(a: str, b: str) -> bool:
    """Detect singular/plural or {word} vs {word} font(s) variant tags."""
    if a == b:
        return True
    for base, ext in ((a, b), (b, a)):
        if ext == base + "s":
            return True
        if ext in (base + " font", base + " fonts"):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("listing", type=Path)
    args = parser.parse_args()

    if not args.listing.is_file():
        print(f"[FAIL] listing does not exist: {args.listing}")
        return 1

    try:
        text = args.listing.read_text(encoding="utf-8")
    except OSError as error:
        print(f"[FAIL] could not read listing: {error}")
        return 1

    parsed = sections(text)
    failures: list[str] = []
    warnings: list[str] = []

    if not re.search(r"^platform:\s*Creative Fabrica\s*$", text, re.MULTILINE | re.IGNORECASE):
        failures.append("frontmatter platform must be Creative Fabrica")

    for heading in REQUIRED:
        if not parsed.get(heading, "").strip():
            failures.append(f"missing or empty section: {heading}")

    title = first_content(parsed.get("PRODUCT TITLE"))
    if not title:
        failures.append("empty product title")
    else:
        if len(title) > MAX_TITLE_CHARS:
            failures.append(f"product title is {len(title)} characters; maximum is {MAX_TITLE_CHARS}")
        if re.search(r"\bfonts?\b", title, re.IGNORECASE):
            failures.append("product title must not add the category word font/fonts")

    description = parsed.get("PRODUCT DESCRIPTION", "")
    description_text = " ".join(line.strip() for line in description.splitlines() if line.strip())
    if len(description_text) < 50:
        failures.append(f"product description is {len(description_text)} characters; provide informative paste-ready copy")
    description_word_count = len(re.findall(r"\b[\w'-]+\b", description_text))
    if not MIN_DESCRIPTION_WORDS <= description_word_count <= MAX_DESCRIPTION_WORDS:
        failures.append(
            f"product description is {description_word_count} words; expected {MIN_DESCRIPTION_WORDS}-{MAX_DESCRIPTION_WORDS}"
        )
    if "```" in description:
        failures.append("product description contains a fenced code block")
    for label, pattern in (("price/discount wording", PRICE_RE), ("license wording", LICENSE_RE), ("contact/third-party URL", CONTACT_RE)):
        if pattern.search(description_text):
            failures.append(f"product description contains prohibited {label}")

    seo_map = parsed.get(SEO_MAP_HEADING, "")
    seo_header = next(
        (
            line.strip()
            for line in seo_map.splitlines()
            if line.strip().startswith("|") and "| Phrase |" in line
        ),
        "",
    )
    required_seo_columns = {
        "phrase",
        "role",
        "source / evidence",
        "used in description?",
        "actual placement",
        "natural and factual?",
        "selected tag?",
        "decision",
    }
    if not seo_header:
        failures.append("DESCRIPTION SEO MAP must include the required audit-table header")
    else:
        seo_columns = {part.strip().casefold() for part in seo_header.strip("|").split("|")}
        missing = sorted(required_seo_columns - seo_columns)
        if missing:
            failures.append("DESCRIPTION SEO MAP header missing: " + ", ".join(missing))
    seo_rows = [
        row for row in evidence_rows(seo_map) if row and row[0].casefold() != "phrase"
    ]
    if len(seo_rows) < 2:
        failures.append("DESCRIPTION SEO MAP must audit at least two phrases")
    else:
        roles = {row[1].casefold() for row in seo_rows if len(row) > 1}
        if not any("primary" in role for role in roles):
            failures.append("DESCRIPTION SEO MAP must include a primary phrase")
        if not any("support" in role for role in roles):
            failures.append("DESCRIPTION SEO MAP must include a supporting phrase")
        for index, row in enumerate(seo_rows, start=1):
            if len(row) < 8:
                failures.append(f"DESCRIPTION SEO MAP row {index} has {len(row)} columns; expected 8")
                continue
            phrase = row[0].strip()
            used = row[3].casefold()
            if not phrase:
                failures.append(f"DESCRIPTION SEO MAP row {index} has an empty phrase")
            if used in {"yes", "used", "actually used", "自然に使用"} and phrase.casefold() not in description_text.casefold():
                failures.append(f"DESCRIPTION SEO MAP phrase is marked used but absent from description: {phrase}")

    category = parsed.get("CATEGORY", "")
    if not re.search(r"Creative Fabrica\s*>\s*Fonts|Fonts\s*(?:category|collection)", category, re.IGNORECASE):
        failures.append("category must identify Creative Fabrica > Fonts")

    tag_heading = next((heading for heading in TAG_HEADINGS if heading in parsed), None)
    if tag_heading is None:
        failures.append("missing or empty Creative Fabrica tag section")
    tag_line = first_content(parsed.get(tag_heading, "")) if tag_heading else ""
    tags = [tag.strip() for tag in tag_line.split(",") if tag.strip()]
    if len(tags) != EXPECTED_TAG_COUNT:
        failures.append(f"tag count is {len(tags)}; expected exactly {EXPECTED_TAG_COUNT} internal handoff tags")
    folded = [tag.casefold() for tag in tags]
    if len(folded) != len(set(folded)):
        failures.append("tags contain duplicates")
    banned_standalone = {"font", "fonts", "download", "file", "best", "premium", "creative fabrica"}
    for tag in tags:
        if tag.startswith("#"):
            failures.append(f"hashtag is not allowed: {tag}")
        if ";" in tag:
            failures.append(f"semicolon-separated tag is not allowed: {tag}")
        if tag.casefold() in banned_standalone:
            failures.append(f"generic standalone tag is not allowed: {tag}")
    # Quality gates for the 40-tag contract.
    for tag, casefolded in zip(tags, folded):
        if casefolded in FORMAT_TAGS:
            failures.append(f"format tag is not allowed in the tag set: {tag}")
        if casefolded in JUNK_TAGS:
            failures.append(f"junk adjective tag is not allowed: {tag}")
    for family in NEAR_DUPLICATE_FAMILIES:
        present = sorted(family & set(folded))
        if len(present) > 1:
            failures.append("near-duplicate intent family must collapse to one tag: " + ", ".join(present))
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            if is_near_duplicate_pair(folded[i], folded[j]):
                failures.append(f"near-duplicate variant tags: {tags[i]} / {tags[j]}")
    starts: dict[str, int] = {}
    for tag in tags:
        first = tag.casefold().split()[0] if tag.split() else ""
        starts[first] = starts.get(first, 0) + 1
    for first, count in starts.items():
        if count > 3:
            failures.append(f"leading-word repetition exceeds 3: {first} ({count})")

    rows = evidence_rows(parsed.get("TAG EVIDENCE", ""))
    if len(rows) < len(tags):
        failures.append(f"tag evidence rows are {len(rows)}; expected at least {len(tags)}")
    selected_tag_keys = {tag.casefold(): tag for tag in tags}
    evidence_tag_counts = {key: 0 for key in selected_tag_keys}
    for index, row in enumerate(rows, start=1):
        if len(row) < 8:
            failures.append(f"TAG EVIDENCE row {index} has {len(row)} columns; expected 8")
            continue
        row_tag = row[1].strip()
        row_tag_key = row_tag.casefold()
        if row_tag_key in evidence_tag_counts:
            evidence_tag_counts[row_tag_key] += 1
        score = row[2].strip()
        try:
            numeric_score = float(score)
        except ValueError:
            numeric_score = -1
        if not 0 <= numeric_score <= 100:
            failures.append(f"TAG EVIDENCE row {index} score must be a number from 0 to 100")
        evidence_class = row[3].strip().casefold()
        if evidence_class not in EVIDENCE_CLASSES:
            failures.append(f"TAG EVIDENCE row {index} has an unsupported evidence class: {row[3].strip()}")
        if evidence_class != "verified product fact" and not re.search(r"https?://", row[4], re.IGNORECASE):
            failures.append(f"TAG EVIDENCE row {index} needs an exact public URL for its evidence class")
        row_urls = re.findall(r"https?://\S+", row[4])
        if evidence_class in TAG_ROUTE_CLASSES and not any(FONT_ROUTE_RE.search(u) for u in row_urls):
            failures.append(
                f"TAG EVIDENCE row {index} needs a specific font tag route "
                "(`https://www.creativefabrica.com/tag/<modifier>-fonts/`) — the bare index "
                "(`/tag/`, `/fonts/`) and the singular `-font/` form are not tag evidence"
            )
        if evidence_class == "pdp recurrence" and not any(
                FONT_ROUTE_RE.search(u) or PRODUCT_URL_RE.search(u) for u in row_urls):
            failures.append(f"TAG EVIDENCE row {index} needs a specific tag route or product URL")
        if evidence_class == "strategy snapshot route":
            if "creativefabrica.com" not in row[4].casefold():
                failures.append(f"TAG EVIDENCE row {index} snapshot route must be a creativefabrica.com tag-page URL")
            snapshot = re.search(r"(\d{4}-\d{2}-\d{2})", " ".join(row))
            if not snapshot:
                failures.append(
                    f"TAG EVIDENCE row {index} uses a strategy snapshot but does not record its date "
                    "(write e.g. `https://www.creativefabrica.com/tag/<slug>-fonts/ (snapshot YYYY-MM-DD)`)"
                )
            else:
                try:
                    age = (date.today() - date.fromisoformat(snapshot.group(1))).days
                except ValueError:
                    age = -1
                if age < 0 or age > SNAPSHOT_MAX_AGE_DAYS:
                    failures.append(
                        f"TAG EVIDENCE row {index} tag-bank snapshot is stale ({snapshot.group(1)}); "
                        "refresh with bin/collect_creative_fabrica_tags.py"
                    )
        for column, value in (("visible signal", row[5]), ("product-fit reason", row[6]), ("decision", row[7])):
            if not value.strip():
                failures.append(f"TAG EVIDENCE row {index} has an empty {column}")
    for tag_key, tag in selected_tag_keys.items():
        count = evidence_tag_counts[tag_key]
        if count == 0:
            failures.append(f"missing evidence row for selected tag: {tag}")
        elif count > 1:
            failures.append(f"selected tag has {count} evidence rows instead of one: {tag}")

    # Compound-form gate: every tag must be the `<modifier> Font(s)` form (or a
    # longer buyer phrase). A bare word is a graphics tag, not a font tag.
    single_word_tags = [tag for tag in tags if len(tag.split()) == 1]
    if len(single_word_tags) > MAX_SINGLE_WORD_TAGS:
        failures.append(
            f"standalone one-word tags are not allowed ({len(single_word_tags)} found) — "
            "write the compound `<Modifier> Font(s)` form instead: " + ", ".join(single_word_tags)
        )

    comparable = parsed.get("COMPARABLE PDP SIGNALS", "")
    if len(evidence_rows(comparable)) < 3 and len([line for line in comparable.splitlines() if line.strip() and not line.strip().startswith("[")]) < 3:
        failures.append("COMPARABLE PDP SIGNALS must record at least three comparables")
    if not re.search(r"\b(?:tag count|designer tags|visible tags)\b", comparable, re.IGNORECASE):
        failures.append("COMPARABLE PDP SIGNALS must record a visible designer-tag count per comparable")
    if re.search(r"\b(?:sales|demand|downloads?)\s*(?:score|volume|rank)\b", comparable, re.IGNORECASE):
        failures.append("comparable section must not label visible engagement as sales/demand/download evidence")

    research = parsed.get("RESEARCH NOTES", "")
    if not re.search(r"(?:provider|retriev|fallback|limitation)", research, re.IGNORECASE):
        failures.append("RESEARCH NOTES must record provider/retrieval and fallback or limitation information")
    filename_match = re.fullmatch(r"(\d+)-(.+)-cf\.md", args.listing.name)
    if filename_match:
        scratch_path = args.listing.parent / ".research" / f"{filename_match.group(1)}-{filename_match.group(2)}-research.md"
        if not scratch_path.is_file():
            failures.append(f"missing Creative Fabrica research scratch file: {scratch_path}")
        else:
            try:
                scratch = scratch_path.read_text(encoding="utf-8")
            except OSError as error:
                failures.append(f"could not read Creative Fabrica research scratch file: {error}")
            else:
                for heading in RESEARCH_SECTIONS:
                    section_match = re.search(
                        rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
                        scratch,
                        re.IGNORECASE | re.MULTILINE,
                    )
                    if not section_match or not section_match.group(1).strip():
                        failures.append(f"research scratch section is missing or empty: {heading}")
                if scratch_path.name not in research and str(scratch_path) not in research:
                    failures.append("RESEARCH NOTES must name the product-specific research scratch file")
    cap_context = (research + parsed.get("STATUS", "")).casefold()
    if not ("stable" in cap_context and ("not" in cap_context or "no" in cap_context)):
        warnings.append("record that Creative Fabrica's public author tag cap is not stable/documented")

    if "—" in text:
        warnings.append("em dash found; use a plain hyphen in paste-ready copy where practical")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        for warning in warnings:
            print(f"[WARN] {warning}")
        return 1
    print(f"[PASS] {args.listing}: Creative Fabrica listing-copy hard gates passed")
    for warning in warnings:
        print(f"[WARN] {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
