#!/usr/bin/env python3
"""Validate the Pixiv-to-BOOTH copy handoff structure."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import campaign_mode  # noqa: E402


REQUIRED = [
    "STATUS",
    "BOOTH DESTINATION",
    "PUBLISHING CHECKLIST",
    "RESEARCH NOTES",
    "PIXIV TAG EVIDENCE",
]

# Pixiv caps a work title at 32 characters (seller-supplied platform limit,
# 2026-09-22). It is a hard cap: an over-long title cannot be pasted, so the
# listing is unusable however good the copy is.
MAX_TITLE_CHARS = 32

# The caption is a discovery hook, not a product page. It carries the offer, two
# or three punch points, the like ask, and the link; the full feature list
# belongs in the BOOTH description. Sellers reported the long captions as
# boring, so the budget is enforced rather than advised.
MAX_CAPTION_CHARS = 220


# The spec, this validator and the agent all write these section headings by
# hand, so fold dash variants to a plain hyphen and collapse runs of whitespace
# before comparing. 86-silken-flourish wrote `POST 1 — STYLE SHOWCASE` (em dash)
# where `POST 1 - STYLE SHOWCASE` (hyphen) was expected, and failed on
# punctuation alone. Cosmetic punctuation is not a contract violation.
DASH_FOLD = str.maketrans({
    "\u2010": "-", "\u2011": "-", "\u2012": "-",
    "\u2013": "-", "\u2014": "-", "\u2015": "-",
})


def fold_heading(text: str) -> str:
    return " ".join(text.translate(DASH_FOLD).split())


def sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    parsed: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        parsed[fold_heading(match.group(1))] = text[match.end() : end].strip()
    return parsed


def first_heading_body(parsed: dict[str, str], prefix: str) -> str:
    key = next((item for item in parsed if item.startswith(prefix)), "")
    return parsed.get(key, "")


def first_field(body: str, label: str) -> str:
    match = re.search(rf"^\s*{re.escape(label)}\s*:\s*(.+?)\s*$", body, re.MULTILINE)
    if match:
        return match.group(1).strip()
    # Accept an optional clarifying parenthetical after the label, so
    # `### Tags (comma-separated, up to 10)` satisfies a `Tags` field just as
    # `### Tags` does. The label is the contract; the aside is a note to the
    # reader, and failing on it made the validator reject the listings it is
    # meant to check.
    heading = re.search(
        rf"^###\s+{re.escape(label)}\s*(?:\([^)]*\))?\s*$([\s\S]*?)(?=^###\s+|\Z)",
        body,
        re.MULTILINE,
    )
    if heading:
        return next((line.strip() for line in heading.group(1).splitlines() if line.strip()), "")
    return ""


def caption_body(body: str) -> str:
    """The whole caption text for a post, whichever form wrote it.

    `first_field` deliberately returns one line, which is right for a presence
    check but wrong for the campaign checks: the offer must be the caption's
    first line while the like ask may sit further down beside the link.
    """
    match = re.search(r"^\s*Caption\s*:\s*(.+?)\s*$", body, re.MULTILINE)
    if match:
        return match.group(1).strip()
    heading = re.search(
        r"^###\s+Caption\s*(?:\([^)]*\))?\s*$([\s\S]*?)(?=^###\s+|\Z)", body, re.MULTILINE
    )
    return heading.group(1).strip() if heading else ""


def post_bodies(parsed: dict[str, str]) -> list[tuple[str, str]]:
    """Accept the active one-post contract and retain compatibility with legacy sets."""
    if "PIXIV POST" in parsed:
        return [("PIXIV POST", parsed["PIXIV POST"])]
    return [
        (key, parsed.get(key, ""))
        for key in ("POST 1 - STYLE SHOWCASE", "POST 2 - LETTERING SHOWCASE", "POST 3 - USE-CASE SHOWCASE")
        if key in parsed
    ]


def _tags_after(body: str, offset: int) -> list[str]:
    """Read a tag block: comma-separated on one line, or one tag per line."""
    tags: list[str] = []
    for line in body[offset:].splitlines():
        stripped = line.strip()
        if not stripped and not tags:
            continue
        if not stripped or stripped.startswith("###"):
            break
        if stripped.startswith("#") or stripped.startswith("-"):
            break
        tags.extend(tag.strip() for tag in stripped.split(",") if tag.strip())
    return tags


TAGS_FIELD = re.compile(r"^[ \t]*Tags[ \t]*:[ \t]*(.*)$", re.MULTILINE)
# `[ \t]` not `\s`: `\s` matches the newline, so the trailing `(.*)` reached past
# the heading and captured the first tag line. That made every post look like it
# had exactly one tag -- the 10-tag ceiling, the duplicate check, and the
# evidence-row count were all comparing against a single tag and could not fail.
TAGS_HEADING = re.compile(
    r"^###[ \t]+Tags(?:[ \t]*\([^)]*\))?[ \t]*:?[ \t]*$", re.MULTILINE
)
# A labelled field ends the block whether the value is on its own line
# (`Caption:` then text) or inline on the same line (`Caption: text`).
# Requiring an empty value let `Caption: ...` and `Image source root: ...`
# be read as tags, which inflated a 10-tag post to 12 and looked like a
# limit violation.
FIELD_LINE = re.compile(
    r"^(?:\*\*)?[A-Za-z][A-Za-z0-9 _/-]{1,40}:(?:\*\*)?(?:\s|$)"
)
LIST_LINE = re.compile(r"^(?:[-*+]\s|\d+\.\s)")


def _tag_lines(body: str) -> tuple[list[str], bool]:
    """Return (tags, used_comma_form) for one post's tag block.

    One tag per line is the contract. A comma-separated line is still split so
    historical packages parse, and the flag lets the caller fail closed rather
    than silently accept the drift that let the newest packages diverge.
    """
    match = TAGS_FIELD.search(body)
    if match is not None:
        inline = match.group(1).strip()
        if inline:
            tags = [tag.strip() for tag in inline.split(",") if tag.strip()]
            return tags, len(tags) > 1
        rest = body[match.end():]
    else:
        heading = TAGS_HEADING.search(body)
        if heading is None:
            return [], False
        rest = body[heading.end():]

    tags: list[str] = []
    comma = False
    for line in rest.splitlines():
        stripped = line.strip()
        if not stripped:
            # A blank line ends the block, but the block starts on the line
            # after the heading, so leading blanks are skipped rather than
            # treated as an empty set.
            if tags:
                break
            continue
        if stripped.startswith("#") or FIELD_LINE.match(stripped) or LIST_LINE.match(stripped):
            break
        if "," in stripped:
            comma = True
            tags.extend(tag.strip().strip("`") for tag in stripped.split(",") if tag.strip())
        else:
            tags.append(stripped.strip("`"))
    return tags, comma


def post_tags(body: str) -> list[str]:
    """Read the tags for one post."""
    return _tag_lines(body)[0]


def _comma_form(body: str) -> bool:
    """True when a tag block puts several tags on one comma-separated line."""
    return _tag_lines(body)[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("listing", type=Path)
    args = parser.parse_args()
    if not args.listing.is_file():
        print(f"[FAIL] listing does not exist: {args.listing}")
        return 1

    text = args.listing.read_text(encoding="utf-8")
    parsed = sections(text)
    failures: list[str] = []

    # Case-insensitive: `platform: pixiv` and `platform: Pixiv` are the same
    # declaration. Rejecting one of them was the same class of brittleness as the
    # dash and parenthetical matches above.
    if not re.search(r"^platform:\s*pixiv\s*$", text, re.MULTILINE | re.IGNORECASE):
        failures.append("frontmatter platform must be Pixiv")
    for heading in REQUIRED:
        if not parsed.get(heading, "").strip():
            failures.append(f"missing or empty section: {heading}")

    destination = parsed.get("BOOTH DESTINATION", "")
    if "LINK REQUIRED" not in destination and not re.search(r"https?://[^\s)]+\.booth\.pm/items/\d+", destination):
        failures.append("BOOTH DESTINATION must contain a public booth.pm/items/<id> URL or LINK REQUIRED")

    posts = post_bodies(parsed)
    if not posts:
        failures.append("no Pixiv post section found: expected PIXIV POST")

    # --- Campaign mode (free/limited-time vs permanent paid) ----------------
    # A free campaign must lead with the offer in the caption's first line, ask
    # for the BOOTH like, and carry at least one free-offer tag. A paid-only
    # post must carry none of that vocabulary.
    mode = campaign_mode.parse_mode(text)
    free_mode = campaign_mode.is_free_mode(mode)
    if mode not in campaign_mode.ALL_MODES:
        print(
            f"[WARN] unrecognised campaign mode '{mode}'; classified as "
            f"{'free' if free_mode else 'paid'} from its label"
        )
    if free_mode:
        campaign_state = parsed.get("CAMPAIGN STATE", "")
        if not campaign_state.strip():
            failures.append(
                f"campaign mode {mode} requires a non-empty '## CAMPAIGN STATE' section"
            )
        else:
            for label in (
                "Campaign mode",
                "Free scope",
                "Start/end or unlock condition",
                "Commercial Use state",
            ):
                if not re.search(
                    rf"^\s*[-*]?\s*{re.escape(label)}\s*:", campaign_state, re.MULTILINE
                ):
                    failures.append(f"CAMPAIGN STATE is missing the '{label}:' field")

    for prefix, body in posts:
        title = first_field(body, "Title")
        tags = post_tags(body)
        caption = first_field(body, "Caption") or first_field(body, "Description")
        if not title:
            failures.append(f"{prefix} is missing a Title field")
        elif len(title) > MAX_TITLE_CHARS:
            failures.append(
                f"{prefix} title is {len(title)} characters; Pixiv caps a work "
                f"title at {MAX_TITLE_CHARS}"
            )
        elif free_mode and not campaign_mode.has_free_offer_term(title):
            # The title is the first thing a browser reads in a feed, so the
            # campaign has to be legible there too, not only in the caption.
            failures.append(
                f"{prefix} free campaign: the title must announce the free offer "
                "(無料/フリーフォント/期間限定無料 …)"
            )
        if not tags:
            failures.append(f"{prefix} is missing a Tags field")
        else:
            if len(tags) > 10:
                failures.append(f"{prefix} has {len(tags)} tags; Pixiv allows at most 10")
            if len(tags) < 1:
                failures.append(f"{prefix} has no tags")
            if len({tag.casefold() for tag in tags}) != len(tags):
                failures.append(f"{prefix} contains duplicate tags")
            if _comma_form(body):
                failures.append(
                    f"{prefix} has comma-separated tags; the contract is one tag per line"
                )
        if not caption:
            failures.append(f"{prefix} is missing a Caption field")
        else:
            full_caption = caption_body(body) or caption
            if len(full_caption) > MAX_CAPTION_CHARS:
                failures.append(
                    f"{prefix} caption is {len(full_caption)} characters; the "
                    f"discovery-hook budget is {MAX_CAPTION_CHARS}. Cut feature "
                    "detail — the product page carries it, not the caption."
                )
        if caption and free_mode:
            # The offer is the headline: first caption line, then the window,
            # then the like ask. A free campaign that buries any of the three
            # is not advertising the offer.
            full_caption = caption_body(body) or caption
            first_line = next(
                (line.strip() for line in full_caption.splitlines() if line.strip()), ""
            )
            if not campaign_mode.has_free_offer_term(first_line):
                failures.append(
                    f"{prefix} free campaign: the caption's first line must open with "
                    f"the free offer; first line is '{first_line[:80]}'"
                )
            if not campaign_mode.has_limited_time(first_line):
                failures.append(
                    f"{prefix} free campaign: the caption's first line must state the "
                    "limited-time window (期間限定/今週/〜まで etc.)"
                )
            if not campaign_mode.has_like_cta(full_caption):
                failures.append(
                    f"{prefix} free campaign: the caption must ask for a BOOTH like "
                    "(いいね/お気に入り/ブックマーク)"
                )
        if caption and "booth.pm/items/" not in (caption + body) and "LINK REQUIRED" not in body:
            failures.append(f"{prefix} caption must contain the BOOTH item URL or LINK REQUIRED")
        if "```" in body or re.search(r"\[[^\]]+\]\(https?://", body):
            failures.append(f"{prefix} contains Markdown formatting in paste-ready fields")

    evidence = parsed.get("PIXIV TAG EVIDENCE", "")
    evidence_header = next(
        (line.strip() for line in evidence.splitlines() if line.strip().startswith("|") and "| Tag |" in line),
        "",
    )
    required_columns = {
        "tag",
        "exact tag/search url",
        "relevant works visible",
        "distinct creators",
        "newest relevant date",
        "tag/use status",
        "tier",
        "provider/status",
        "product-fit decision",
    }
    if not evidence_header:
        failures.append("PIXIV TAG EVIDENCE must include the required evidence-table header")
    else:
        columns = {part.strip().casefold() for part in evidence_header.strip("|").split("|")}
        if "post(s)" not in columns and "use in consolidated post" not in columns:
            failures.append("PIXIV TAG EVIDENCE header missing: post(s) or use in consolidated post")
        missing = sorted(required_columns - columns)
        if missing:
            failures.append("PIXIV TAG EVIDENCE header missing: " + ", ".join(missing))
    evidence_rows = [
        line for line in evidence.splitlines()
        if line.strip().startswith("|")
        and "| Tag |" not in line
        and not re.match(r"\|\s*-+", line)
    ]
    selected_tags: set[str] = set()
    for _, body in posts:
        selected_tags.update(tag.casefold() for tag in post_tags(body))
    if selected_tags and len(evidence_rows) < len(selected_tags):
        failures.append(
            f"PIXIV TAG EVIDENCE rows ({len(evidence_rows)}) are fewer than distinct selected tags ({len(selected_tags)})"
        )
    for index, row in enumerate(evidence_rows, start=1):
        columns = [part.strip() for part in row.strip().strip("|").split("|")]
        if len(columns) < 10:
            failures.append(f"PIXIV TAG EVIDENCE row {index} has {len(columns)} columns; expected 10")
            continue
        if not columns[0] or not columns[1] or not columns[7] or not columns[8] or not columns[9]:
            failures.append(f"PIXIV TAG EVIDENCE row {index} has an empty required value")
        # A row that declares itself a keyword-only fallback has no Pixiv tag
        # page by definition, so it cannot be required to cite one. The test
        # previously matched only the hyphenated "keyword-only", so a row
        # written "keyword only" was held to the tag-page rule it exists to be
        # exempt from. Normalise the hyphen away and treat either spelling,
        # in the status columns or as the source cell, as the declaration.
        row_folded = row.casefold().replace("-", " ")
        is_keyword_only = (
            "keyword only" in row_folded or "fallback" in row_folded
        )
        source = "" if columns[2] in {"—", "-", "N/A"} or columns[2].startswith("(") else columns[2]
        if source.casefold().replace("-", " ") in {"keyword only", "keyword", "no live tag page found"}:
            source = ""
        if source and not ("pixiv.net" in source or "LINK REQUIRED" in source) and not is_keyword_only:
            failures.append(f"PIXIV TAG EVIDENCE row {index} has no Pixiv source URL")
        if not source and not is_keyword_only:
            failures.append(f"PIXIV TAG EVIDENCE row {index} has no Pixiv source URL")
        if columns[6].casefold() == "confirmed tag" and "keyword only" in row.casefold():
            failures.append(f"PIXIV TAG EVIDENCE row {index} contradicts confirmed-tag status")

    if re.search(r"\b(api[_ -]?key|password|secret|cookie|access token)\b", text, re.I):
        failures.append("possible credential or secret found")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    print(f"[PASS] {args.listing}: Pixiv-to-BOOTH structure, tag limits, URL, and plain-text checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
