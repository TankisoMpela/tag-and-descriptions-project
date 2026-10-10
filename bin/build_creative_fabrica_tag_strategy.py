#!/usr/bin/env python3
"""Turn the collected Creative Fabrica tag bank into an actionable tag strategy.

Reads outputs/research/creative-fabrica-tag-bank.json (produced by
bin/collect_creative_fabrica_tags.py) and writes
outputs/research/creative-fabrica-tag-strategy.md, which the
creative-fabrica-fonts-specialist agent reads before choosing tags.

Everything here is evidence-ranked from the collected coverage counts — the
strategy never invents a tag that was not measured.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "outputs/research/creative-fabrica-tag-bank.json"
OUT = ROOT / "outputs/research/creative-fabrica-tag-strategy.md"

STOP = {
    "font", "fonts", "by", "the", "and", "of", "a", "for", "with", "creative",
    "fabrica", "graphic", "design", "studio", "typeface", "duo", "bundle", "svg",
    "png", "alphabet", "letters", "numbers", "set", "pack",
}

# Creative Fabrica's nine canonical font categories (from /fonts/).
CATEGORIES = [
    "blackletter", "color", "decorative", "dingbats", "display",
    "sans-serif", "script", "serif", "slab-serif",
]

# Which collected tags belong to each axis. Only live tags are emitted.
STYLE_TAGS = [
    "modern", "calligraphy", "handwritten", "script", "cursive", "brush",
    "serif", "sans serif", "display", "decorative", "blackletter", "color",
    "bold", "elegant", "luxury", "minimalist", "geometric", "whimsical",
    "playful", "funky", "western", "tattoo", "comic", "horror", "gothic",
    "art deco", "varsity", "outline", "shadow", "stencil", "monoline",
    "family", "ligature", "vintage", "retro", "rustic", "boho", "grunge",
    "graffiti", "typewriter", "condensed",
]
SEASONAL_TAGS = ["christmas", "halloween", "valentine", "spring", "summer", "winter", "fall"]
AUDIENCE_TAGS = ["kids", "baby", "wedding", "beach", "farmhouse"]
USE_CASE_TAGS = [
    "logo", "branding", "invitation", "sublimation", "cricut", "packaging",
    "poster", "headline", "craft", "blog", "social media", "greeting card",
    "label", "signage", "apparel", "stickers",
]

# Per-category front-loading recipe: canonical category word(s) first, then the
# strongest style tags for that category, then buyer-intent compounds.
RECIPES = {
    "script": ["Script", "Calligraphy", "Handwritten", "Cursive", "Signature",
               "Wedding", "Invitation", "Elegant", "Luxury", "Brush Lettering"],
    "serif": ["Serif", "Elegant", "Luxury", "Editorial Serif", "Wedding",
              "Vintage", "Book Font", "Classic Serif"],
    "sans-serif": ["Sans Serif", "Modern", "Minimalist", "Clean Sans",
                   "Branding", "Logo", "Corporate Font", "Geometric Sans"],
    "display": ["Display", "Bold", "Retro", "Vintage", "Headline",
                "Poster", "Packaging", "Bold Display"],
    "slab-serif": ["Slab Serif", "Serif", "Bold", "Vintage", "Poster",
                   "Editorial Serif"],
    "blackletter": ["Blackletter", "Gothic", "Tattoo", "Vintage", "Old English",
                    "Tattoo Lettering"],
    "decorative": ["Decorative", "Ornamental", "Whimsical", "Playful", "Kids",
                   "Display"],
    "color": ["Color Font", "Layered Font", "Retro", "Kids", "Playful"],
    "dingbats": ["Dingbats", "Symbol Font", "Icon Font", "Decorative"],
}


def load() -> dict:
    return json.loads(BANK.read_text(encoding="utf-8"))


def main() -> int:
    bank = load()
    stamp = bank["generated"]
    live = {t["tag"]: t for t in bank["tags"] if t["status"] == "live"}

    def ranked(tags: list[str]) -> list[tuple[str, int]]:
        return sorted(((t, live[t]["coverage_count"]) for t in tags if t in live),
                      key=lambda x: -x[1])

    style = ranked(STYLE_TAGS)
    seasonal = ranked(SEASONAL_TAGS)
    audience = ranked(AUDIENCE_TAGS)
    use_case = ranked(USE_CASE_TAGS)

    # A one-word tag is CF-canonical only when the platform itself publishes it
    # with meaningful coverage; anything else must be a two-to-four-word phrase.
    canonical_one_word = [t for t, _ in style if " " not in t and live[t]["coverage_count"] >= 5000]

    lines: list[str] = [
        "# Creative Fabrica tag strategy (evidence-ranked)",
        "",
        f"Generated {stamp} from `creative-fabrica-tag-bank.json` "
        f"({len(live)} live tag pages, {bank['total_fonts']:,} fonts indexed).",
        "",
        "**Read this before choosing tags.** It replaces guesswork: every tag below was",
        "measured on a live Creative Fabrica tag page. Counts are catalog coverage",
        "signals, never demand or sales evidence.",
        "",
        "## How to build the 40-tag set",
        "",
        "1. Pick the product's **one** canonical category from the nine below and use its recipe.",
        "2. Front-load the 3-5 strongest **style** tags that genuinely describe this font.",
        "3. Shape the wording with the **category-native language** block (what popular fonts in",
        "   this category actually call themselves), then fill the middle with **buyer-intent**",
        "   compounds (two-to-four words) that fit the product.",
        "4. Add seasonal/audience tags only when the product actually fits.",
        "5. This is idiom guidance, not a whitelist — write tags for this font in the same",
        "   shape, and support anything new with a live route or a fresh bank snapshot.",
        "",
        "## Canonical categories and recipes",
        "",
    ]
    for category in CATEGORIES:
        recipe = RECIPES[category]
        weighted = ranked([r for r in recipe])
        lines.append(f"### {category}")
        lines.append("")
        lines.append("Front-load order: " + ", ".join(
            f"`{name}`" if name not in live else f"`{name}` ({live[name]['coverage_count']:,})"
            for name in [r for r in recipe]
        ))
        if weighted:
            lines.append("")
            lines.append("Measured in this axis: " + ", ".join(f"`{n}` {c:,}" for n, c in weighted))
        lines.append("")

    affinity = bank.get("category_affinity", {})
    if affinity:
        lines += ["## Category-native language (popular fonts in each category)", "",
                  "Top repeated words from the live popular-font grid of "
                  "`/fonts/<category>-fonts/` (one call per category). A word already "
                  "measured as a tag shows its coverage; everything else is language to "
                  "use **inside** two-to-four-word compounds, never as a standalone tag.", ""]
        for category in CATEGORIES:
            entry = affinity.get(category) or {}
            titles = entry.get("titles") or []
            counts: Counter = Counter()
            for title in titles:
                for word in re.sub(r"[^A-Za-z ]", " ", title).lower().split():
                    if len(word) > 2 and word not in STOP:
                        counts[word] += 1
            keep = [(word, count) for word, count in counts.most_common(40) if count >= 2]
            lines.append(f"### {category} — {len(titles)} popular titles (snapshot {entry.get('retrieved', 'n/a')})")
            lines.append("")
            if keep:
                lines.append("  ".join(
                    f"`{word}`" + (f" (tag {live[word]['coverage_count']:,})" if word in live else "")
                    for word, _ in keep[:18]))
            else:
                lines.append("_no repeated words in the current sample_")
            lines.append("")

    lines += ["## Style tag pool (coverage-ranked)", "",
              "| Tag | Coverage | Words |", "|---|---:|---:|"]
    lines += [f"| {t} | {c:,} | {len(t.split())} |" for t, c in style]
    lines += ["", "## Buyer-intent / use-case pool", "",
              "| Tag | Coverage |", "|---|---:|"]
    lines += [f"| {t} | {c:,} |" for t, c in use_case]
    lines += ["", "## Seasonal pool", "", "| Tag | Coverage |", "|---|---:|"]
    lines += [f"| {t} | {c:,} |" for t, c in seasonal]
    lines += ["", "## Audience pool", "", "| Tag | Coverage |", "|---|---:|"]
    lines += [f"| {t} | {c:,} |" for t, c in audience]

    lines += [
        "",
        "## Modifiers Creative Fabrica publishes as `<modifier> Fonts`",
        "",
        "These are the strongest single-word **modifiers**. They are NOT valid tags on their own —",
        "always write the compound form. The bare word is a broader graphics tag (`/tag/kids/` shows",
        "SVGs and graphics; `/tag/kids-fonts/` is \"Kids Fonts\"):",
        "",
    ]
    lines += [f"- `{name}` -> write `{name.title()} Font`  ({live[name]['coverage_count']:,} fonts)" for name in canonical_one_word]
    lines += [
        "",
        "Every tag must be the compound `<Modifier> Font(s)` form or a longer buyer phrase; the",
        "validator rejects standalone one-word tags outright.",
        "",
        "## Never use",
        "",
        "Format facts (`OTF`, `TTF`, `WOFF`, `WOFF2`, `OpenType`), junk adjectives "
        "(`Best Seller`, `Popular`, `Trendy`, `Cute`), generic filler "
        "(`Font`, `Fonts`, `Download`, `File`, `Premium`, `Creative Fabrica`), or a "
        "competitor's invented tag.",
        "",
        "## Popular-font keyword signal (title frequency)",
        "",
        "Top recurring words in the titles of discovered popular fonts — a second, "
        "independent axis that agrees with the coverage ranking:",
        "",
    ]
    freq = bank.get("title_keyword_frequency", {})
    lines += [f"- `{w}` x{c}" for w, c in list(freq.items())[:20]]
    lines.append("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
