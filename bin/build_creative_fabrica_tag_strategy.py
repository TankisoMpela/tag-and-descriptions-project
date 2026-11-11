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
from urllib.parse import urlsplit

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
# strongest style and buyer-intent terms. The output filters these to measured routes.
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


def tag_phrase(tag: str, record: dict) -> str:
    """Render the exact singular/plural suffix used by the measured route."""
    base = re.sub(r"\s+fonts?$", "", tag, flags=re.IGNORECASE).strip().title()
    route_slug = urlsplit(record.get("url", "")).path.rstrip("/").rsplit("/", 1)[-1].casefold()
    suffix = "Fonts" if route_slug.endswith("-fonts") else "Font"
    return f"{base} {suffix}".strip()


def tag_key(tag: str) -> str:
    return re.sub(r"\s+fonts?$", "", tag.casefold()).strip()


def has_exact_font_route(record: dict) -> bool:
    parsed = urlsplit(record.get("url", ""))
    host = parsed.netloc.casefold().split(":", 1)[0]
    parts = [part for part in parsed.path.casefold().split("/") if part]
    if host not in {"creativefabrica.com", "www.creativefabrica.com"} or len(parts) != 2:
        return False
    if parts[0] not in {"tag", "fonts"}:
        return False
    route_slug = parts[1]
    if route_slug.endswith("-fonts"):
        route_base = route_slug[:-6]
    elif route_slug.endswith("-font"):
        route_base = route_slug[:-5]
    else:
        return False
    name = record.get("slug") or record.get("tag") or ""
    base = re.sub(r"[^a-z0-9]+", "-", str(name).casefold()).strip("-")
    base = re.sub(r"-fonts?$", "", base)
    return route_base == base


def main() -> int:
    bank = load()
    stamp = bank["generated"]
    live = {
        tag_key(t["tag"]): t for t in bank["tags"]
        if t.get("status") == "live" and has_exact_font_route(t)
    }

    def ranked(tags: list[str]) -> list[tuple[str, int]]:
        return sorted(
            ((t, live[tag_key(t)]["coverage_count"]) for t in tags if tag_key(t) in live),
            key=lambda x: -x[1],
        )

    style = ranked(STYLE_TAGS)
    seasonal = ranked(SEASONAL_TAGS)
    audience = ranked(AUDIENCE_TAGS)
    use_case = ranked(USE_CASE_TAGS)

    # A one-word modifier is usable only when its exact font-scoped route was measured.
    canonical_one_word = [t for t, _ in style if " " not in t and live[tag_key(t)]["coverage_count"] >= 5000]

    lines: list[str] = [
        "# Creative Fabrica tag strategy (evidence-ranked)",
        "",
        f"Generated {stamp} from `creative-fabrica-tag-bank.json` "
        f"({len(live)} live tag pages, {bank['total_fonts']:,} fonts indexed).",
        "",
        "**Read this before choosing tags.** It replaces guesswork: every tag below was",
        "measured on a live Creative Fabrica tag page. Counts are catalog coverage",
        "signals, never demand or sales evidence.",
        "This guide reports measured tag-route labels and coverage. For seller-editor wording, follow",
        "the exact phrase shown in public font PDP `Designer tags`; `Suggested Categories` is separate.",
        "",
        "## How to build a tag set (working target about 30, maximum 40)",
        "",
        "1. Pick the product's **one** canonical category from the nine below and use its recipe.",
        "2. Front-load the strongest **style** tags that genuinely describe this font; use 3-5 only when they qualify.",
        "3. Use measured font-tag routes as one candidate source. Add relevant buyer-use and long-tail",
        "   phrases observed in relevant font PDP `Designer tags`; one relevant PDP may support a",
        "   fitting phrase. Engagement is optional context. Product facts filter fit but do not invent tag wording.",
        "4. Add seasonal/audience tags only when the product actually fits.",
        "5. About 30 is the working target and 40 is the ceiling. Use a mixed set without padding.",
        "6. A longer exact route proves the phrase exists, not that it merits a slot; tiny coverage is a reason to omit it unless that narrow buyer intent is central.",
        "7. Preserve exact route or Designer Tags wording. Do not add singular/plural variants",
        "   automatically; include both only when separate evidence suggests plausible query coverage.",
        "",
        "## Canonical categories and recipes",
        "",
    ]
    for category in CATEGORIES:
        recipe = RECIPES[category]
        weighted = ranked([r for r in recipe])
        lines.append(f"### {category}")
        lines.append("")
        measured_recipe = [name for name in recipe if tag_key(name) in live]
        lines.append("Front-load order (measured routes only): " + (
            ", ".join(f"`{tag_phrase(name, live[tag_key(name)])}` ({live[tag_key(name)]['coverage_count']:,})" for name in measured_recipe)
            if measured_recipe else "_no measured route in this category recipe_"
        ))
        if weighted:
            lines.append("")
            lines.append("Measured in this axis: " + ", ".join(f"`{tag_phrase(n, live[tag_key(n)])}` {c:,}" for n, c in weighted))
        lines.append("")

    affinity = bank.get("category_affinity", {})
    if affinity:
        lines += ["## Category-native language (popular fonts in each category)", "",
                  "Top repeated words from the live popular-font grid of "
                  "`/fonts/<category>-fonts/` (one call per category). A word already "
                  "measured as a tag shows its coverage; everything else is wording for "
                  "descriptions or route discovery, not a phrase to turn into a tag.", ""]
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
                    f"`{word}`" + (f" (tag {live[tag_key(word)]['coverage_count']:,})" if tag_key(word) in live else "")
                    for word, _ in keep[:18]))
            else:
                lines.append("_no repeated words in the current sample_")
            lines.append("")

    lines += ["## Style tag pool (coverage-ranked)", "",
              "| Tag phrase | Coverage | Words |", "|---|---:|---:|"]
    lines += [f"| {tag_phrase(t, live[tag_key(t)])} | {c:,} | {len(t.split()) + 1} |" for t, c in style]
    lines += ["", "## Buyer-intent / use-case pool", "",
              "| Tag phrase | Coverage |", "|---|---:|"]
    lines += [f"| {tag_phrase(t, live[tag_key(t)])} | {c:,} |" for t, c in use_case]
    lines += ["", "## Seasonal pool", "", "| Tag phrase | Coverage |", "|---|---:|"]
    lines += [f"| {tag_phrase(t, live[tag_key(t)])} | {c:,} |" for t, c in seasonal]
    lines += ["", "## Audience pool", "", "| Tag phrase | Coverage |", "|---|---:|"]
    lines += [f"| {tag_phrase(t, live[tag_key(t)])} | {c:,} |" for t, c in audience]

    lines += [
        "",
        "## Measured font-tag modifiers",
        "",
        "These are the strongest single-word **route modifiers**. This is a coverage lookup, not",
        "editor wording: public Designer tags may use a different exact label, including a bare",
        "word or a singular/plural Font suffix. Copy the phrase seen in Designer tags for editor input.",
        "",
    ]
    lines += [f"- `{name}` -> route label `{tag_phrase(name, live[tag_key(name)])}`  ({live[tag_key(name)]['coverage_count']:,} fonts)" for name in canonical_one_word]
    lines += [
        "",
        "A measured modifier is not permission to append another adjective or feature. The selected",
        "seller tag wording must come from an exact route or explicit Designer tags; a relevant PDP may support a fitting long-tail phrase. Engagement is optional context. Route coverage alone",
        "does not make a phrase useful.",
        "",
        "## Never use",
        "",
        "Format facts (`OTF`, `TTF`, `WOFF`, `WOFF2`, `OpenType`), junk adjectives "
        "(`Best Seller`, `Popular`, `Trendy`), irrelevant mood adjectives, generic filler "
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
