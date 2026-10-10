#!/usr/bin/env python3
"""Turn the accumulated tag corpus into a style guide the agent can learn from.

Reads outputs/research/creative-fabrica-tag-corpus.jsonl (append-only, written by
bin/collect_creative_fabrica_tag_graph.py) and writes
outputs/research/creative-fabrica-tag-patterns.md.

The guide deliberately describes **how Creative Fabrica font tags look and which
kinds dominate** — shapes, types, real examples and their coverage — so the agent
can generate its own tags in that idiom. It is NOT a closed whitelist: an agent
that only ever copies listed strings would be over-constrained.

Counts are catalog coverage signals, never demand or sales evidence.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "outputs/research/creative-fabrica-tag-corpus.jsonl"
BANK = ROOT / "outputs/research/creative-fabrica-tag-bank.json"
DESC = ROOT / "outputs/research/creative-fabrica-description-corpus.jsonl"

DESC_STOP = {
    "font", "fonts", "design", "designs", "project", "projects", "use", "using",
    "perfect", "great", "this", "that", "with", "your", "you", "and", "the",
    "for", "from", "are", "its", "it", "can", "will", "all", "any", "each",
    "every", "into", "over", "more", "most", "also", "including", "includes",
    "create", "creating", "created", "works", "made", "make", "add", "adds",
    "set", "pack", "bundle", "download", "instant", "high", "quality", "whether",
    "them", "these", "those", "when", "where", "while", "about", "just", "like",
    "sure", "need", "want", "look", "looks", "give", "gives", "very", "well",
}
OUT = ROOT / "outputs/research/creative-fabrica-tag-patterns.md"

# Coarse type taxonomy: a tag may match more than one family.
TYPES: dict[str, set[str]] = {
    "structure/letterform": {
        "serif", "sans", "slab", "blackletter", "script", "handwritten",
        "handwriting", "calligraphy", "cursive", "display", "monoline",
        "condensed", "rounded", "outline", "shadow", "stencil", "gothic",
        "typewriter", "brush", "marker", "line", "ballpoint",
    },
    "aesthetic/mood": {
        "elegant", "cute", "fancy", "beautiful", "cool", "pretty", "fun",
        "playful", "whimsical", "luxury", "minimal", "modern", "retro",
        "vintage", "rustic", "boho", "grunge", "bold", "clean", "simple",
        "sweet", "magic", "dreamy", "aesthetic",
    },
    "use-case/buyer-intent": {
        "logo", "wedding", "poster", "branding", "cricut", "craft",
        "invitation", "packaging", "headline", "label", "signage", "apparel",
        "merch", "sublimation", "tshirt", "t-shirt", "blog", "social",
        "greeting", "card", "banner", "quote", "advertising", "sports",
    },
    "audience": {"kids", "baby", "teen", "women", "men", "children", "boy", "girl"},
    "seasonal/holiday": {
        "christmas", "halloween", "valentine", "spring", "summer", "winter",
        "fall", "autumn", "easter", "thanksgiving", "holiday", "birthday",
    },
    "content/shape": {
        "number", "letter", "alphabet", "symbol", "monogram", "ligature",
        "dingbat", "icon", "emoji", "pattern", "texture", "decorative",
        "ornamental", "floral", "nature", "animal",
    },
}


def load() -> dict[str, dict]:
    """Latest observation per slug."""
    latest: dict[str, dict] = {}
    if not CORPUS.exists():
        return latest
    for line in CORPUS.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        latest[record["slug"]] = record
    return latest


def base_word(slug: str) -> str:
    return re.sub(r"-fonts$", "", slug).replace("-", " ")


def classify(name: str) -> list[str]:
    words = set(re.sub(r"[^a-z ]", " ", name.lower()).split())
    return [family for family, keys in TYPES.items() if words & keys]


def main() -> int:
    records = load()
    if not records:
        print(f"no corpus at {CORPUS}; run bin/collect_creative_fabrica_tag_graph.py first")
        return 1

    live = {s: r for s, r in records.items() if r.get("coverage_count")}
    absent = [s for s, r in records.items() if not r.get("coverage_count")]
    stamp = max((r.get("observed", "") for r in records.values()), default="")

    shapes = Counter(len(base_word(s).split()) for s in records)
    family_tags: dict[str, list[tuple[str, int]]] = defaultdict(list)
    family_totals: Counter = Counter()
    for slug, record in live.items():
        name = record.get("display_name") or base_word(slug).replace("-", " ").title()
        count = record["coverage_count"]
        for family in classify(name):
            family_tags[family].append((name, count))
            family_totals[family] += count

    edges = Counter()
    for record in records.values():
        for related in record.get("related_font_tags", []):
            if related in records:
                edges[(record["slug"], related)] += 1

    lines = [
        "# Creative Fabrica font-tag patterns (learned, not a whitelist)",
        "",
        f"- Corpus: `creative-fabrica-tag-corpus.jsonl` — **{len(records)} distinct font tags** observed"
        f" ({len(live)} with a published count, {len(absent)} absent/empty), snapshot **{stamp}**.",
        f"- Collected by `bin/collect_creative_fabrica_tag_graph.py` (append-only; re-run to extend).",
        "- Counts are catalog coverage signals, never demand or sales evidence.",
        "",
        "## The tag unit: `<modifier> Fonts`",
        "",
        "A Creative Fabrica **font** tag is the compound tag page `/tag/<modifier>-fonts/`,",
        "shown as `<Modifier> Fonts`. The bare form is a different, broader tag that is not",
        "font-scoped — measured 2026-09-21:",
        "",
        "| Route | H1 | Published count | What the page shows |",
        "|---|---|---|---|",
        "| `/tag/kids/` | `Kids` | none | graphics — *Beach Vibe Lighthouse Bookmark*, *Png For Testing Week* |",
        "| `/tag/kids-fonts/` | `Kids Fonts` | 14,188 | fonts — *Cute Fonts*, *Bold Fonts* |",
        "| `/tag/logo/` | `Logo` | none | not font-scoped |",
        "| `/tag/logo-fonts/` | `Logo Fonts` | 30,956 | font tag page |",
        "",
        "**A bare one-word tag is the noisy one** — it mixes graphics, SVGs and mockups in",
        "with fonts. The `<modifier> Fonts` compound is font-scoped by construction and",
        "carries the font intent. Write the compound form unless a live route proves otherwise.",
        "",
        "## How the modifier usually looks",
        "",
        "The modifier before `Fonts` is almost always one word, sometimes two, so the rendered",
        "tag still reads as a short high-intent phrase (`Kids Fonts`, `Logo Fonts`, `Modern Fonts`):",
        "",
        "| Modifier words | Tags | Examples |",
        "|---|---:|---|",
    ]
    sample_by_len: dict[int, list[str]] = defaultdict(list)
    for slug, record in sorted(live.items(), key=lambda kv: -kv[1]["coverage_count"]):
        name = record.get("display_name") or base_word(slug).replace("-", " ").title()
        n = len(base_word(slug).split())
        if len(sample_by_len[n]) < 6:
            sample_by_len[n].append(f"{name} Fonts")
    for n in sorted(shapes):
        if not sample_by_len[n]:  # no live example at this length; fall back to the slug
            for slug in sorted(records):
                if len(base_word(slug).split()) == n:
                    sample_by_len[n].append(base_word(slug).title() + " Fonts")
                    break
        lines.append(f"| {n} | {shapes[n]} | " + ", ".join(f"`{x}`" for x in sample_by_len[n]) + " |")

    counts = sorted(r["coverage_count"] for r in live.values())
    total_fonts = None
    if BANK.exists():
        try:
            total_fonts = json.loads(BANK.read_text(encoding="utf-8")).get("total_fonts")
        except json.JSONDecodeError:
            total_fonts = None
    if counts:
        lines += ["", "## How big this picture is", ""]
        if total_fonts:
            lines.append(f"- Creative Fabrica indexes **{total_fonts:,} fonts**.")
        lines += [
            f"- Measured font tags: **{len(counts)}**, from **{max(counts):,}** down to **{min(counts):,}**; median **{counts[len(counts) // 2]:,}**.",
            "- The head is enormous — the top tag covers ~15% of the whole font library — so head tags",
            "  buy reach, not precision, and they overlap heavily (a font routinely carries several).",
            "- Below the median the counts fall away fast: a hyper-specific phrase can describe the font",
            "  perfectly and still reach almost nobody.",
            f"- Universe seen so far: **{len(records)}** font tags fetched; the graph exposes more, so",
            "  treat this as a growing sample rather than the full list.",
        ]

    lines += ["", "## Tag families: what kinds exist and how big they are", "",
              "| Family | Tags seen | Combined coverage | Strongest examples |",
              "|---|---:|---:|---|"]
    for family, total in family_totals.most_common():
        top = sorted(family_tags[family], key=lambda x: -x[1])[:6]
        lines.append(f"| {family} | {len(family_tags[family])} | {total:,} | "
                     + ", ".join(f"`{n}` ({c:,})" for n, c in top) + " |")

    lines += ["", "## Coverage-ranked vocabulary (the heavy hitters)", "",
              "| Tag | Coverage | Family |", "|---|---:|---|"]
    for slug, record in sorted(live.items(), key=lambda kv: -kv[1]["coverage_count"])[:60]:
        name = record.get("display_name") or base_word(slug).replace("-", " ").title()
        lines.append(f"| {name} | {record['coverage_count']:,} | {', '.join(classify(name)) or '—'} |")

    lines += ["", "## How tags co-occur (what popular tags sit beside)",
              "",
              "Most frequent neighbours across observed tag pages — useful for building a",
              "coherent set rather than 40 unrelated strings:", ""]
    for slug, record in sorted(live.items(), key=lambda kv: -kv[1]["coverage_count"])[:12]:
        related = [r for r in record.get("related_font_tags", []) if r in live]
        if not related:
            continue
        pretty = [live[r].get("display_name") or base_word(r).replace("-", " ").title() for r in related[:10]]
        lines.append(f"- **{record.get('display_name') or slug}** → " + ", ".join(f"`{p}`" for p in pretty))

    descriptions = []
    if DESC.exists():
        for line in DESC.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = record.get("description") or ""
            # Only font products: a real font PDP carries a "… Fonts" breadcrumb,
            # while graphics/dingbat pages fall back to the discovery category slug.
            if len(text) >= 60 and str(record.get("category") or "").endswith("Fonts"):
                descriptions.append(record)

    if descriptions:
        unigrams: Counter = Counter()
        bigrams: Counter = Counter()
        trigrams: Counter = Counter()
        for record in descriptions:
            words = [w for w in re.sub(r"[^A-Za-z ]", " ", record["description"]).lower().split()
                     if len(w) > 2 and w not in DESC_STOP]
            unigrams.update(words)
            bigrams.update(" ".join(words[i:i + 2]) for i in range(len(words) - 1))
            trigrams.update(" ".join(words[i:i + 3]) for i in range(len(words) - 2))
        lines += [
            "",
            "## Buyer language (from popular font descriptions)",
            "",
            f"{len(descriptions)} real seller descriptions of popular Creative Fabrica fonts, mined for",
            "the phrasing that actually accompanies a font listing. This is the vocabulary to build",
            "tag and description wording from — not just tag names.",
            "",
            "Some high-frequency phrases are boilerplate (`otf ttf`, `pua encoded`) — those are",
            "description facts, never tags.",
            "",
            "**Most common single words**", "",
            "| Word | Uses |", "|---|---:|",
        ]
        lines += [f"| {w} | {c} |" for w, c in unigrams.most_common(30)]
        lines += ["", "**Most common two-word phrases**", "", "| Phrase | Uses |", "|---|---:|"]
        lines += [f"| {w} | {c} |" for w, c in bigrams.most_common(25) if c > 1]
        lines += ["", "**Most common three-word phrases**", "", "| Phrase | Uses |", "|---|---:|"]
        lines += [f"| {w} | {c} |" for w, c in trigrams.most_common(15) if c > 1]
        lines += ["", "**Style exemplars** (verbatim openings — how a listing actually reads)", ""]
        for record in sorted(descriptions, key=lambda r: -r.get("description_chars", 0))[:6]:
            snippet = record["description"][:200].rsplit(" ", 1)[0] + "…"
            lines.append("- *" + snippet + "*\\n  (`" + str(record["slug"]) + "`, " + str(record.get("category") or "n/a") + ")")
        lines.append("")

    lines += ["", "## How to use this",
              "",
              "1. This is **idiom guidance, not a menu**. Learn the shapes and families, then write",
              "   tags for *this* font in the same style — a real CF tag is a 1-2 word phrase plus",
              "   Font/Fonts, or a buyer-intent phrase that CF itself publishes.",
              "2. Prefer families that are large and coherent with the product; do not stack five",
              "   mood adjectives or five use-cases.",
              "3. Anything you invent must still be live-verified, or cited from the tag bank when",
              "   the bank already measured it.",
              "4. Counts rank *coverage*, not sales. Never present them as demand.",
              ""]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(records)} tags, {len(live)} live)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
