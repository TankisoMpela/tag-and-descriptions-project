#!/usr/bin/env python3
"""Validate BOOTH listing-copy structure and SEO evidence.

This validator enforces the copy and SEO-evidence contract only. Category,
price, package, preview, license, and upload checks are deliberately outside
this validator because BOOTH agent 20 is a copy-and-research agent.

Evidence rules enforced here (matching the agent spec):
- Every selected tag must carry an evidence row whose first cell equals the tag.
- The exact-tag URL must use the BOOTH `tags[]` route and its decoded query must
  contain the tag text.
- The font-category URL must use the `/browse/` route and, when it carries a
  `tags[]` param, that param must match the tag text.
- Each row must carry numeric overall and font-category counts, a
  paid-products/distinct-sellers value, a provider + date + activity label in
  the status cell, an evidence tier, and a product-fit reason.
- Low-activity (1-16 relevant font listings) tags are allowed only as a limited
  number of documented exceptions.
- The tag block targets 18-25 validated tags (aim for 25). Fewer than 18 or
  more than 25 after validation marks the listing BLOCKED (fail closed).
- When --booth-dir is supplied, a sibling-advisory check compares the tag set
  with prior listings and emits WARN-level overlap/saturation nudges. This is
  advisory only and never blocks the listing.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import campaign_mode  # noqa: E402

# The workflow targets 18-25 validated tags, aiming for 25. Fewer than 18 or
# more than 25 marks the listing BLOCKED (fail closed) rather than padding.
TARGET_BOOTH_TAGS = 25
MIN_BOOTH_TAGS = 18
MAX_BOOTH_TAGS = 25
# Young-cohort win-rate floor. A listing may carry fewer than MIN_BOOTH_TAGS
# tags only when every selected tag's evidence row proves it cleared this floor
# (spec: "if fewer than 20 are defensible, report the exact count and why;
# never manufacture tags").
GATE_WIN_RATE_FLOOR = 5.0
MAX_LOW_ACTIVITY_EXCEPTIONS = 3

REQUIRED_SECTIONS = [
    "STATUS",
    "PRODUCT TITLE",
    "PRODUCT DESCRIPTION (PASTE-READY)",
    "KEYWORD COVERAGE",
    "TAG EVIDENCE",
    "RESEARCH NOTES",
]

TAG_SECTION_HEADINGS = (
    "BOOTH TAGS (18-25 VALIDATED TAGS, ONE PER LINE)",
    "BOOTH TAGS (10-25 VALIDATED TAGS, ONE PER LINE)",
    "BOOTH TAGS (10-25 VALIDATED TAGS, NORMALLY 20, ONE PER LINE)",
    "BOOTH TAGS (10-25 TARGET, ONE PER LINE)",
    "BOOTH TAGS (32 VALIDATED TAGS, ONE PER LINE)",
    "BOOTH TAGS (25 VALIDATED TAGS, ONE PER LINE)",
    "BOOTH TAGS (ENTER EXACTLY 30 PRIORITIZED TAGS, ONE PER LINE)",
    "BOOTH TAGS (ENTER UP TO 30 PRIORITIZED TAG CANDIDATES, ONE PER LINE)",
    "BOOTH TAGS (12-20 VALIDATED TAGS, ONE PER LINE)",
    "BOOTH TAGS (VALIDATED TAGS, ONE PER LINE)",
    # Headings written by the 2026-09-11 quality-gated regeneration, which
    # reported the honest count instead of padding to 20 (spec: "never
    # manufacture tags"). Kept as aliases so those listings are found.
    "BOOTH TAGS (10-14 VALIDATED TAGS, ONE PER LINE)",
    "BOOTH TAGS (10-18 VALIDATED TAGS, ONE PER LINE)",
    "BOOTH TAGS (18-30 VALIDATED TAGS, ONE PER LINE)",
    "BOOTH TAGS (11 VALIDATED SELECTED TAGS, ONE PER LINE)",
)

# Accepted ways a row can state a count that BOOTH did not expose. Anything
# else is treated as missing numeric evidence.
COUNT_PLACEHOLDERS = {
    "—",
    "-",
    "n/a",
    "not exposed",
    "total unknown",
    "fewer than 17 visible; total unknown",
    "fewer than 17 visible",
}

VALID_TIERS = {"a", "b", "c"}

# Patterns that indicate a plausible BOOTH activity label. The status cell must
# contain a provider and a date-like fragment to be treated as current live
# evidence rather than a vague "Live" assertion.
PROVIDER_HINTS = (
    "firecrawl",
    "webfetch",
    "serper",
    "exa",
    "tavily",
    "crawl4ai",
)
DATE_RE = re.compile(r"\b(202[0-9])[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12][0-9]|3[01])\b")


def sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[heading] = text[start:end].strip()
    return result


def first_content(value: str | None) -> str:
    if not value:
        return ""
    for line in value.splitlines():
        line = line.strip()
        if line and not line.startswith("<!--"):
            return line
    return ""


def parse_tag_param(url: str) -> str | None:
    """Return the decoded first tags[] value in a URL, or None."""
    try:
        q = urllib.parse.urlparse(url).query
    except Exception:
        return None
    if not q:
        return None
    pairs = urllib.parse.parse_qs(q, keep_blank_values=True)
    vals = pairs.get("tags[]")
    if not vals:
        return None
    return vals[0].strip()


def is_browse_url(url: str) -> bool:
    return "/browse/" in url.lower()


def count_placeholder(value: str) -> bool:
    return value.strip().casefold() in {p.casefold() for p in COUNT_PLACEHOLDERS}


def is_numeric_count(value: str) -> bool:
    """Accept integers plus live-count formatting such as '1,433', '1,434+',
    '318+', '1,067', or trailing '~'/'頃'. Rejects words, empty, or '—'."""
    v = value.strip()
    if not v:
        return False
    if count_placeholder(v):
        return True
    core = v.rstrip("+~頃").replace(",", "").strip()
    return core.isdigit() and int(core) > 0


def is_low_activity(status: str, cat_count: str) -> bool:
    """A row counts as a low-activity exception when the category count is in
    1-16, or the status labels it low/fewer-than-17, or the paid-proof is weak."""
    txt = status.casefold()
    if any(s in txt for s in ("low activity", "fewer than 17", "low-activity")):
        return True
    v = cat_count.strip().rstrip("+~頃").replace(",", "").strip()
    if v.isdigit():
        return 1 <= int(v) <= 16
    return False


def _check_sibling_advisory(
    tags: list[str], booth_dir: Path, exclude: Path | None = None
) -> list[str]:
    """Compare the current tag set against prior BOOTH listings for overlap and
    saturation. Returns WARN-level messages only — never a veto.

    Overlap: too many shared tags with any single sibling listing dilutes
    differentiation. Saturation: a tag carried by most prior listings has no
    discovery breadth left AND cannot be tested, because a near-constant is not a
    variable. The advisory therefore promotes ROTATION rather than removal — a
    small number of slots explored per listing, so the effect of a tag can
    eventually be measured.
    """
    warnings: list[str] = []
    prior_tag_sets: list[tuple[str, set[str]]] = []

    for path in sorted(booth_dir.glob("*-booth.md")):
        # Never compare a listing against itself: the wholesale overlap it would
        # report is trivially 100% and says nothing about differentiation.
        if exclude is not None and path.resolve() == exclude.resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        # Extract tags from the BOOTH TAGS section
        in_tag_section = False
        current_tags: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("## BOOTH TAGS"):
                in_tag_section = True
                continue
            if in_tag_section and stripped.startswith("## "):
                break
            if in_tag_section and stripped and not stripped.startswith("<!--"):
                current_tags.append(stripped.lstrip("-*").strip())
        if current_tags:
            prior_tag_sets.append((path.name, set(t.casefold() for t in current_tags)))

    if not prior_tag_sets:
        return warnings

    current_set = set(t.casefold() for t in tags)
    tag_counts: dict[str, int] = {}
    for _, pset in prior_tag_sets:
        for t in pset:
            tag_counts[t] = tag_counts.get(t, 0) + 1

    num_prior = len(prior_tag_sets)

    # Overlap, summarised rather than enumerated. One wrapper per sibling made
    # this advisory impossible to read: with this many listings it emitted
    # hundreds of lines, which buries the rotation guidance that matters.
    overlaps = sorted(
        ((fname, len(current_set & pset)) for fname, pset in prior_tag_sets),
        key=lambda x: -x[1],
    )
    heavy = [x for x in overlaps if x[1] >= 8]
    if heavy:
        top = ", ".join(f"{n} ({c})" for n, c in heavy[:3])
        warnings.append(
            f"sibling advisory: {len(heavy)} of {num_prior} listings share >=8 tags "
            f"with this set (worst: {top}). High overlap across the catalogue means "
            f"the set differentiates little from what already exists."
        )

    # Saturation / rotation. Threshold is a SHARE of prior listings, not "all of
    # them": with this many siblings no tag appears in every one, so an equality
    # test against num_prior can never fire.
    NEAR_UNIVERSAL = 0.80
    CORE = 0.50
    near = sorted(
        ((t, c) for t, c in tag_counts.items() if c >= NEAR_UNIVERSAL * num_prior and t in current_set),
        key=lambda x: -x[1],
    )
    core = [t for t, c in tag_counts.items() if c >= CORE * num_prior and t in current_set]

    if near:
        shown = ", ".join(f"{t} ({c}/{num_prior})" for t, c in near[:6])
        warnings.append(
            f"sibling advisory: {len(near)} selected tag(s) are near-universal across "
            f"your listings — {shown}. These carry no differentiation and cannot be "
            f"tested, because a near-constant is not a variable."
        )
    if len(core) >= 5:
        # Rotation is deliberately aggressive here, because a low-traffic
        # catalogue has little to protect. Measured on this shop 2026-09-22:
        # 31 items, median 6 likes, none above 100, best global rank 2,541 of
        # ~4,958. At that position a tag change costs nothing, and there is no
        # evidence any single tag is producing the likes the shop does get --
        # the gate win-rates are market-wide, not measured per shop.
        #
        # Explore most of the core set (two thirds, minimum 3) so a tag's effect
        # can actually be observed, while keeping a third as a stable baseline
        # to compare against. A near-constant is not a variable.
        rotate = max(3, (len(core) * 2) // 3)
        warnings.append(
            f"sibling advisory: {len(core)} of {len(tags)} selected tags appear in "
            f">=50% of your {num_prior} listings. Rotation target: vary {rotate} "
            f"slot(s) per listing — this catalogue has low measured traffic "
            f"(median 6 likes, none above 100), so exploration costs little and "
            f"variance is what produces learning. Keep the remaining ~{len(core) - rotate} "
            f"core tags as a stable baseline so the change is comparable, and swap "
            f"only for candidates that clear the gate. Record which slot was varied."
        )

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("listing", type=Path)
    parser.add_argument(
        "--today",
        default=datetime.date.today().isoformat(),
        help="Reference date (ISO) for freshness checks; defaults to today.",
    )
    parser.add_argument(
        "--booth-dir",
        type=Path,
        default=None,
        help="Directory of prior BOOTH listings for sibling-advisory overlap check (advisory only, never a veto).",
    )
    args = parser.parse_args()

    try:
        today = datetime.date.fromisoformat(args.today)
    except ValueError:
        today = datetime.date.today()

    if not args.listing.is_file():
        print(f"[FAIL] listing does not exist: {args.listing}")
        return 1

    text = args.listing.read_text(encoding="utf-8")
    parsed = sections(text)
    failures: list[str] = []
    warnings: list[str] = []

    # --- Structural / scope checks -----------------------------------------
    if not re.search(r"^platform:\s*BOOTH\s*$", text, re.MULTILINE):
        failures.append("frontmatter platform must be BOOTH")

    for heading in REQUIRED_SECTIONS:
        if heading not in parsed or not parsed[heading].strip():
            failures.append(f"missing or empty section: {heading}")

    tag_heading = next((h for h in TAG_SECTION_HEADINGS if h in parsed), None)
    if tag_heading is None or not parsed[tag_heading].strip():
        failures.append("missing or empty BOOTH tag section")

    title = first_content(parsed.get("PRODUCT TITLE"))
    if not title:
        failures.append("product title is empty")
    elif len(title) > 100:
        failures.append(f"product title is {len(title)} characters; target <= 100")

    description = parsed.get("PRODUCT DESCRIPTION (PASTE-READY)", "")
    if not description.strip():
        failures.append("paste-ready description is empty")
    if re.search(r"^#{1,6}\s|\*\*|```", description, re.MULTILINE):
        failures.append("paste-ready description contains Markdown formatting")

    tag_body = parsed.get(tag_heading, "") if tag_heading else ""
    tag_lines = [
        line.strip().lstrip("-*").strip()
        for line in tag_body.splitlines()
        if line.strip() and not line.strip().startswith("<!--")
    ]
    if not tag_lines or tag_lines[0].startswith("["):
        failures.append("selected BOOTH tag block is empty or still a placeholder")
        tags: list[str] = []
    else:
        tags = tag_lines
        if any("," in tag for tag in tags):
            failures.append("BOOTH tags must be one tag per line, not comma-separated")
        if len(tags) > MAX_BOOTH_TAGS:
            failures.append(
                f"selected BOOTH tag count is {len(tags)}; above the {MAX_BOOTH_TAGS} hard cap"
            )
        # A count below MIN_BOOTH_TAGS is checked AFTER the evidence table is
        # parsed, so the exemption is verified rather than asserted: the count
        # may be low only when every selected tag's evidence row shows a
        # young-cohort win-rate at or above GATE_WIN_RATE_FLOOR.
        lowered = [item.casefold() for item in tags]
        if len(lowered) != len(set(lowered)):
            failures.append("selected BOOTH tags contain duplicates")

    # --- Evidence block ----------------------------------------------------
    evidence = parsed.get("TAG EVIDENCE", "")
    evidence_header = next(
        (
            line.strip()
            for line in evidence.splitlines()
            if line.strip().startswith("|") and "| Tag |" in line
        ),
        "",
    )
    required_evidence_columns = {
        "tag",
        "language",
        "exact tag url",
        "font-category url",
        "overall count",
        "font-category count",
        "paid products / distinct sellers",
        "activity and provider status",
        "evidence tier",
        "product-fit reason",
    }
    if evidence_header:
        ordered_header_columns = [
            part.strip().casefold()
            for part in evidence_header.strip().strip("|").split("|")
        ]
        header_columns = set(ordered_header_columns)
        missing_columns = sorted(required_evidence_columns - header_columns)
        if missing_columns:
            failures.append(
                "TAG EVIDENCE header is missing required columns: "
                + ", ".join(missing_columns)
            )
            # The failure is already recorded; without this guard the row loop
            # below would KeyError on the absent column and crash the run
            # instead of reporting a clean FAIL.
            ordered_header_columns = []
    else:
        ordered_header_columns = []
        failures.append(
            "TAG EVIDENCE must include the 10-column header with exact-tag, "
            "font-category, counts, activity/provider, tier, and fit fields"
        )

    evidence_rows = [
        line
        for line in evidence.splitlines()
        if (
            line.strip().startswith("|")
            and not re.match(r"\|\s*-+", line)
            and "| Tag |" not in line
        )
    ]
    if tags and len(evidence_rows) < len(tags):
        failures.append(
            f"tag evidence rows ({len(evidence_rows)}) are fewer than selected tags ({len(tags)})"
        )

    low_activity_count = 0
    gate_failures: list[str] = []
    if tags:
        for index, row in enumerate(evidence_rows[: len(tags)], start=1):
            columns = [part.strip() for part in row.strip().strip("|").split("|")]
            if len(columns) != len(ordered_header_columns):
                failures.append(
                    f"tag evidence row {index} has {len(columns)} columns; "
                    f"expected {len(ordered_header_columns)} to match the evidence header"
                )
                continue

            # Map by header name, not position. Listings may carry extra
            # evidence columns (e.g. the young-cohort win-rate) without
            # failing the gate; the required ten must all be present.
            cell = dict(zip(ordered_header_columns, columns))
            evidence_tag = cell["tag"]
            language = cell["language"]
            exact_url = cell["exact tag url"]
            cat_url = cell["font-category url"]
            overall = cell["overall count"]
            cat_count = cell["font-category count"]
            paid = cell["paid products / distinct sellers"]
            status = cell["activity and provider status"]
            tier = cell["evidence tier"]
            fit = cell["product-fit reason"]

            # 10. Young-cohort win-rate, when the listing carries the column.
            #     This is what a below-floor tag count is exempted against, so
            #     it is verified from the table rather than trusted from prose.
            young = cell.get("young paid n / sellers / win-rate", "")
            win_match = re.search(r"win\s*([\d.]+)\s*%", young)
            if win_match:
                if float(win_match.group(1)) < GATE_WIN_RATE_FLOOR:
                    gate_failures.append(
                        f"'{evidence_tag.strip('`* ')}' (row {index}, win {win_match.group(1)}%)"
                    )
            else:
                gate_failures.append(
                    f"'{evidence_tag.strip('`* ')}' (row {index}, no win-rate recorded)"
                )

            # 1. Selected tag must match the row's first cell.
            if evidence_tag.strip("`* ").casefold() != tags[index - 1].casefold():
                failures.append(
                    f"tag evidence row {index} does not match selected tag '{tags[index - 1]}'"
                )

            # 2. Exact-tag URL must use the tags[] route AND its decoded value
            #    must contain the tag text.
            if "tags%5b%5d=" not in exact_url.casefold() and "tags[]=" not in exact_url.casefold():
                failures.append(f"tag evidence row {index} exact-tag URL is missing the tags[] route")
            else:
                decoded = parse_tag_param(exact_url)
                if decoded is not None and tags[index - 1].casefold() not in decoded.casefold():
                    failures.append(
                        f"tag evidence row {index} exact-tag URL decodes to '{decoded}', which does not match tag '{tags[index - 1]}'"
                    )

            # 3. Font-category URL must use the /browse/ route, and any tags[]
            #    param must match the tag text.
            if not is_browse_url(cat_url):
                failures.append(f"tag evidence row {index} font-category URL is missing the /browse/ route")
            else:
                decoded = parse_tag_param(cat_url)
                if decoded is not None and tags[index - 1].casefold() not in decoded.casefold():
                    failures.append(
                        f"tag evidence row {index} font-category URL decodes to '{decoded}', which does not match tag '{tags[index - 1]}'"
                    )

            # 4. Numeric evidence: overall + category counts must be a
            #    positive integer (accepting , and + formatting) or an
            #    accepted documented placeholder.
            for label, val in (("overall", overall), ("font-category", cat_count)):
                if is_numeric_count(val):
                    continue
                failures.append(
                    f"tag evidence row {index} {label} count '{val}' is not a number or an accepted placeholder"
                )

            # 5. Paid-products / distinct-sellers must not be empty.
            if not paid.strip():
                failures.append(f"tag evidence row {index} paid-products/distinct-sellers is empty")

            # 6. Activity/provider status must contain a provider hint and a date,
            #    and an activity label.
            if not status.strip():
                failures.append(f"tag evidence row {index} activity/provider status is empty")
            else:
                lowered_status = status.casefold()
                frozen_snapshot = "frozen snapshot" in lowered_status
                if not frozen_snapshot and not any(prov in lowered_status for prov in PROVIDER_HINTS):
                    failures.append(
                        f"tag evidence row {index} status must name the retrieval provider or frozen snapshot"
                    )
                if not DATE_RE.search(status):
                    failures.append(
                        f"tag evidence row {index} status must include a retrieval date (YYYY-MM-DD)"
                    )
                if not any(
                    w in lowered_status
                    for w in ("live", "low activity", "dead", "blocked", "low-activity", "stale", "no coverage")
                ):
                    failures.append(
                        f"tag evidence row {index} status must carry an activity label (live/low-activity/dead/etc.)"
                    )

            # 7. Evidence tier must be A, B, or C.
            tier_clean = tier.strip("`* ").casefold()
            if tier_clean not in VALID_TIERS:
                failures.append(f"tag evidence row {index} evidence tier '{tier}' is not A/B/C")

            # 8. Product-fit reason must be populated.
            if not fit.strip():
                failures.append(f"tag evidence row {index} product-fit reason is empty")

            # 9. Track low-activity exceptions against the cap.
            if is_low_activity(status, cat_count):
                low_activity_count += 1

    if low_activity_count > MAX_LOW_ACTIVITY_EXCEPTIONS:
        failures.append(
            f"{low_activity_count} low-activity tags exceed the maximum of {MAX_LOW_ACTIVITY_EXCEPTIONS} documented exceptions"
        )

    # --- Below-floor tag count, exempted only by verified gate evidence -----
    # The spec forbids padding to reach TARGET_BOOTH_TAGS and tells the agent to
    # report the honest count when fewer candidates clear the gate. So a count
    # under MIN_BOOTH_TAGS is allowed only when every selected tag's evidence row
    # PROVES it cleared GATE_WIN_RATE_FLOOR. This is not a prose justification:
    # a row with a win-rate below the floor, or with no win-rate recorded, keeps
    # the listing BLOCKED.
    if tags and len(tags) < MIN_BOOTH_TAGS:
        if gate_failures:
            failures.append(
                f"selected BOOTH tag count is {len(tags)}, below the {MIN_BOOTH_TAGS} floor, "
                f"and the below-floor exemption is not earned: "
                + "; ".join(gate_failures[:5])
                + (f" (+{len(gate_failures) - 5} more)" if len(gate_failures) > 5 else "")
            )
        else:
            warnings.append(
                f"tag count {len(tags)} is below the {MIN_BOOTH_TAGS} floor but every selected "
                f"tag proves a young-cohort win-rate >= {GATE_WIN_RATE_FLOOR}%; "
                f"below-floor exemption applied"
            )
    elif tags and len(tags) < TARGET_BOOTH_TAGS:
        # Within contract but short of the aim. Reported, never fatal: the target
        # is a goal, not a quota, and padding to reach it is what the spec bans.
        warnings.append(
            f"tag count {len(tags)} is within the {MIN_BOOTH_TAGS}-{MAX_BOOTH_TAGS} contract "
            f"but below the {TARGET_BOOTH_TAGS} target; add further distinct, "
            f"evidence-clearing routes only if they exist"
        )

    # --- Campaign mode (free/limited-time vs permanent paid) ----------------
    # The campaign state decides whether free-offer vocabulary is legitimate.
    # A free mode must PROVE the offer in the copy (first-line offer, stated
    # window, like CTA, at least one free tag); a paid mode must not carry it.
    mode = campaign_mode.parse_mode(text)
    if mode not in campaign_mode.ALL_MODES:
        warnings.append(
            f"unrecognised campaign mode '{mode}'; classified as "
            f"{'free' if campaign_mode.is_free_mode(mode) else 'paid'} from its label"
        )
    if campaign_mode.is_free_mode(mode):
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

        description_first_line = first_content(description)
        if not campaign_mode.has_free_offer_term(description_first_line):
            failures.append(
                "free campaign: the paste-ready description must open with the "
                f"free offer; first line is '{description_first_line[:80]}'"
            )
        if not campaign_mode.has_limited_time(description_first_line):
            failures.append(
                "free campaign: the description's first line must state the "
                "limited-time window (期間限定/今週/〜まで etc.)"
            )
        if not campaign_mode.has_like_cta(description):
            failures.append(
                "free campaign: the description must ask for a BOOTH like/favourite "
                "(いいね/お気に入り)"
            )
        if tags and not campaign_mode.free_offer_tags(tags):
            failures.append(
                "free campaign: the selected tag set must carry at least one "
                "free-offer tag (無料/フリーフォント/期間限定無料/free font …)"
            )
    else:
        stray_free = campaign_mode.free_offer_tags(tags)
        if stray_free:
            failures.append(
                f"paid-only campaign mode {mode} must not select free-offer tags: "
                + ", ".join(stray_free)
            )

    # --- Sibling advisory check (WARN only, never a veto) -------------------
    if args.booth_dir is not None and args.booth_dir.is_dir():
        sibling_warnings = _check_sibling_advisory(tags, args.booth_dir, args.listing)
        warnings.extend(sibling_warnings)
    elif args.booth_dir is not None:
        warnings.append(
            f"--booth-dir path does not exist or is not a directory: {args.booth_dir}"
        )

    # Freshness: the newest evidence date should not be unreasonably old.
    newest = None
    for row in evidence_rows[: len(tags)]:
        m = DATE_RE.search(row)
        if m:
            try:
                d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                newest = d if newest is None or d > newest else newest
            except ValueError:
                pass
    if newest is not None and (today - newest).days > 45:
        warnings.append(
            f"newest evidence date {newest} is older than 45 days from {today}; refresh page-life evidence"
        )

    # Out-of-scope customer-facing phrases.
    customer_fields = "\n".join(
        parsed.get(name, "")
        for name in (
            "PRODUCT TITLE",
            "PRODUCT DESCRIPTION (PASTE-READY)",
            *TAG_SECTION_HEADINGS,
            "KEYWORD COVERAGE",
        )
    ).casefold()
    for phrase in campaign_mode.BANNED_CUSTOMER_PHRASES:
        if phrase in customer_fields:
            failures.append(f"out-of-scope customer-facing phrase found: {phrase}")

    if re.search(r"\b(api[_ -]?key|password|secret|cookie|access token)\b", text, re.I):
        failures.append("possible credential or secret found in listing")

    for warning in warnings:
        print(f"[WARN] {warning}")
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    print(
        f"[PASS] {args.listing}: BOOTH listing-copy, one-per-line tags, evidence, and scope checks passed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
