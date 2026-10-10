#!/usr/bin/env python3
"""Shared campaign-mode contract for the FontFairy listing tools.

One source of truth for the campaign state that BOOTH/Pixiv copy and their
validators must agree on:

- the set of campaign modes and which carry a free/limited-time offer;
- the free-offer vocabulary that is legitimate ONLY in a free mode;
- the limited-time and like-CTA markers the copy must carry in a free mode;
- reading the `Campaign mode:` declaration out of a listing's STATUS section.

The human-readable contract is `agents/reference/AGENTS-annex-listing.md`
(section "Campaign mode"). Keep the two in sync; this module is what the
validators and the census evidence gate actually enforce.
"""

from __future__ import annotations

import re

# New-font launches default to a limited-time free offer. This is the
# AUTHORING default the agents write into new listings; the validators must not
# infer it from a missing declaration, because every pre-campaign listing omits
# the line and would be retroactively reclassified as free.
DEFAULT_MODE = "FREE_ACTIVE"
# What a listing with no `Campaign mode:` line is treated as. Legacy listings
# predate campaign mode, and all of them are paid-only.
LEGACY_MODE = "NORMAL_PAID"

# Modes that carry an active free / limited-time offer.
FREE_MODES = frozenset(
    {"FREE_ACTIVE", "SAMPLE_ACTIVE", "REPOST_UNLOCK", "MILESTONE_PACK", "DEMO_ACTIVE"}
)
# Modes that must not carry free-offer language.
PAID_MODES = frozenset({"NORMAL_PAID", "ANALYSIS"})
ALL_MODES = FREE_MODES | PAID_MODES

# Substrings that mark a non-standard mode as free-bearing, so a legacy or
# hand-written mode label is classified instead of silently treated as paid.
FREE_MODE_HINTS = ("FREE", "TRIAL", "DEMO", "SAMPLE", "UNLOCK", "MILESTONE", "無料")

# Free-offer vocabulary. These terms may enter the selected tag set and the
# customer copy ONLY while a free mode is active and the offer is true; the
# permanent paid copy must not carry them.
FREE_OFFER_TERMS = (
    "無料",
    "フリーフォント",
    "フリー素材",
    "フリー",
    "無料配布",
    "無料dl",
    "無料ダウンロード",
    "期間限定無料",
    "お試し",
    "無料版あり",
    "free font",
    "freebie",
    "free",
)

# A limited-time claim needs a window word, not just the word "free". Without
# one of these the copy reads as a permanent free product.
LIMITED_TIME_MARKERS = (
    "期間限定",
    "限定",
    "今週",
    "今週中",
    "今だけ",
    "週間",
    "先着",
    "まで",
    "まで無料",
    "配布中",
    "無料配布中",
    "終了",
)

# The like/favourite call to action the campaign asks for on BOOTH.
LIKE_CTA_MARKERS = ("いいね", "お気に入り", "ブックマーク", "フォロー")

# Customer-facing phrases that stay out of scope: they are internal workflow
# jargon, not seller copy. `free demo` is deliberately NOT here — `Free Demo` is
# the sanctioned name of the free BOOTH variant (see the campaign contract).
BANNED_CUSTOMER_PHRASES = (
    "pixiv post",
    "pixiv caption",
    "freemium",
    "free sample",
    "free-to-paid",
)

# Capture the mode label, then stop at the first token that is not an
# all-caps/underscore mode token. Listings write the mode inline with a
# trailing explanation ("Campaign mode: `NORMAL_PAID` — paid-only permanent
# copy"), so a bare `\w+` capture would swallow prose.
MODE_TAIL_RE = re.compile(r"campaign[\s_-]*mode\s*:\s*(.+)", re.IGNORECASE)
MODE_TOKEN_RE = re.compile(r"^[`*]*([A-Za-z_][A-Za-z_0-9]*)[`*]*$")


def parse_mode(text: str, default: str = LEGACY_MODE) -> str:
    """Return the campaign mode declared in a listing, normalised to upper case.

    A missing declaration falls back to `LEGACY_MODE`, not the authoring
    default: pre-campaign listings omit the line and are paid-only, so
    inferring FREE_ACTIVE from absence would silently rewrite their contract.
    """
    match = MODE_TAIL_RE.search(text or "")
    if not match:
        return default
    tokens: list[str] = []
    for raw in match.group(1).strip().split():
        token = MODE_TOKEN_RE.match(raw)
        if token is None:
            break
        value = token.group(1)
        if value != value.upper():
            break
        tokens.append(value)
    if not tokens:
        return default
    return "_".join(tokens).upper()


def is_free_mode(mode: str) -> bool:
    """True when the mode carries a free/limited-time offer.

    A mode outside the canonical set is classified by its own label so a
    legacy or hand-written mode ("DEMO ACTIVE", "trial") is not silently
    treated as paid-only.
    """
    value = (mode or "").upper()
    if value in ALL_MODES:
        return value in FREE_MODES
    return any(hint in value for hint in FREE_MODE_HINTS)


def has_free_offer_term(text: str) -> bool:
    """True when text contains any free-offer term (substring match)."""
    low = (text or "").casefold()
    return any(term.casefold() in low for term in FREE_OFFER_TERMS)


def is_free_offer_tag(tag: str) -> bool:
    """True when a tag carries free-offer vocabulary (substring match)."""
    return has_free_offer_term(tag)


def free_offer_tags(tags) -> list[str]:
    return [t for t in tags if is_free_offer_tag(t)]


def has_limited_time(text: str) -> bool:
    return any(marker in (text or "") for marker in LIMITED_TIME_MARKERS)


def has_like_cta(text: str) -> bool:
    return any(marker in (text or "") for marker in LIKE_CTA_MARKERS)
