#!/usr/bin/env python3
"""Daily Pinterest run — pick fonts, brief the agent, assemble the bulk CSV.

Mechanical half of the Daily-Pinterest-Run pipeline. The agent writes the
creative copy (copy.json); this tool does selection, profile-backed and
mechanical keyword candidates in the brief, validation, staggered publish times,
and both CSVs: buffer.csv (Buffer free-plan import, carries Alt Text —
primary destination) and pins.csv (Pinterest-native fallback).

Outputs live in outputs/pinterest/{YYYY-MM-DD}/:
  selection.json  the fonts picked for the day (pick)
  brief.md        per-font facts for the agent to write from (brief)
  copy.json       agent-written pin copy (input to assemble)
  buffer.csv      Buffer bulk-upload file — has Alt Text (assemble, primary)
  pins.csv        Pinterest-native bulk-import file (assemble, fallback)
  tag-report.md   prepared tag choices (assemble)

Usage:
  python3 bin/make_daily_pins.py pick --date 2026-10-11 [--count 10] [--seed S]
  python3 bin/make_daily_pins.py brief --date 2026-10-11
  python3 bin/make_daily_pins.py assemble --date 2026-10-11 [--start-hour 9] [--interval-min 60]
  Add --json to pick/brief for machine-readable output.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pinterest_registry  # noqa: E402
import pinterest_tag_ledger  # noqa: E402

EXCLUSION_DAYS = 14
SCHEDULING_WINDOW_DAYS = 14
MIN_KEYWORDS, MAX_KEYWORDS = 3, 10
# How many of a font's own past pins brief.md shows. Enough to make repeated
# phrasing obvious without burying the new copy under old copy.
PRIOR_PINS_IN_BRIEF = 4
CSV_HEADER = ["Title", "Media URL", "Pinterest board", "Thumbnail",
              "Description", "Link", "Publish date", "Keywords"]
# Exact column order from Buffer's own Pinterest import template
# (docs/pinterest/Buffer_Import_Template.csv): Text, Image URL, Board Name,
# Tags, Posting Time, Title, Alt Text, Link — all cells quoted, UTF-8 BOM.
BUFFER_HEADER = ["Text", "Image URL", "Board Name", "Tags", "Posting Time",
                 "Title", "Alt Text", "Link"]

# Mechanical description-derived candidates supplement the preparer's
# profile; they narrow the drafting space while the ledger owns rotation.
STYLE_TERMS = ("art deco", "sans serif", "sans-serif", "blackletter", "handwritten",
               "calligraphy", "signature", "decorative", "minimalist", "minimal",
               "geometric", "condensed", "monoline", "outline", "stencil", "rounded",
               "serif", "script", "display", "retro", "vintage", "modern", "elegant",
               "luxury", "bold", "brush", "slab", "gothic")
USE_CASE_TERMS = ("save the date", "social media", "love letter", "baby shower",
                  "t-shirt", "letterhead", "scrapbooking", "watermark", "packaging",
                  "wedding", "invitation", "branding", "commercial", "halloween",
                  "christmas", "valentine", "birthday", "instagram", "youtube",
                  "certificate", "stationery", "craft", "cricut", "vinyl", "poster",
                  "label", "logo", "brand", "menu", "sign", "card", "journal",
                  "holiday", "easter", "spring", "summer", "love")
FORMAT_TERMS = ("commercial use", "personal use", "alternates", "ligatures",
                "swashes", "multilingual")


def day_dir(date: str) -> Path:
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        sys.exit(f"error: bad date {date!r} — use YYYY-MM-DD")
    return Path("outputs/pinterest") / date


def recent_pins(con, date: str) -> set[str]:
    since = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=EXCLUSION_DAYS)).strftime("%Y-%m-%d")
    return {r[0] for r in con.execute(
        "SELECT font_slug FROM pinned_runs WHERE run_date >= ? AND run_date < ?", (since, date))}


def looks_like_shop_root(url: str) -> bool:
    """A shop/store root (no product path) — weak pin destination, worth flagging."""
    parsed = urlparse(url)
    segments = [s for s in parsed.path.split("/") if s]
    host = (parsed.hostname or "").casefold()
    query = parsed.query.casefold()
    return (len(segments) <= 1
            or (host.endswith("creativefabrica.com") and segments[0].casefold() in {"designer", "search"})
            or any(key in query for key in ("category=", "status=", "page=")))


def image_index(key: str, image: dict) -> int | None:
    if str(key).isdigit():
        return int(key)
    match = re.search(r"pinterest_(\d+)", image.get("pathname", ""), re.IGNORECASE)
    return int(match.group(1)) if match else None


def assign_images(slugs: list[str], reg_fonts: dict, date: str) -> dict[str, dict]:
    """Choose one stable image per font and spread a batch across image indexes."""
    rng = random.Random(f"images:{date}")
    index_uses: dict[int, int] = {}
    assignments: dict[str, dict] = {}
    for slug in slugs:
        rec = reg_fonts.get(slug) or {}
        keyed_images = [(key, image) for key, image in (rec.get("images") or {}).items()
                        if image.get("url")]
        if not keyed_images:
            continue
        choices = [(key, image, image_index(key, image)) for key, image in keyed_images]
        indexed = [choice for choice in choices if choice[2] is not None]
        pool = indexed or choices
        min_uses = min(index_uses.get(index, 0) for _, _, index in pool if index is not None) \
            if indexed else 0
        balanced = [(key, image, index) for key, image, index in pool
                    if index is None or index_uses.get(index, 0) == min_uses]
        key, image, index = rng.choice(balanced)
        assignments[slug] = {**image, "index": index, "registry_key": key}
        if index is not None:
            index_uses[index] = index_uses.get(index, 0) + 1
    return assignments


def image_description(rec: dict, image: dict) -> str:
    """Describe the selected pin from its uploaded manifest metadata."""
    kind, template = image.get("kind"), image.get("template")
    if not kind:
        image_set = rec.get("image_set") or {}
        index = image.get("index")
        template_count = image_set.get("template_count")
        image_count = image_set.get("image_count")
        if isinstance(index, int) and isinstance(template_count, int):
            if index <= template_count:
                kind = "template"
            elif isinstance(image_count, int) and index <= image_count:
                kind = "composite"
    if kind == "template" and template:
        return f"Template layout: {str(template).replace('_', ' ')}"
    if kind == "template":
        return "Template layout (identify the visible copy and composition in this design)"
    if kind == "composite":
        return "Seller-image composite (describe the visible artwork and font treatment)"
    return "Manifested Pinterest image (describe the selected design, not only the font)"


def assign_links(slugs: list[str], reg_fonts: dict, date: str) -> dict[str, str]:
    """Per-pin destination: split fonts that have BOTH marketplace product
    pages evenly between Creative Market and Creative Fabrica (5/5 of 10),
    shuffled with the date seed; fonts with one URL get that URL."""
    both = [s for s in slugs
            if (reg_fonts[s].get("urls") or {}).get("creative_market")
            and (reg_fonts[s].get("urls") or {}).get("creative_fabrica")]
    rng = random.Random(f"links:{date}")
    half = len(both) // 2
    choices = ["creative_market"] * half + ["creative_fabrica"] * half
    if len(both) % 2:
        choices.append(rng.choice(["creative_market", "creative_fabrica"]))
    rng.shuffle(choices)
    out: dict[str, str] = {}
    for slug, market in zip(both, choices):
        out[slug] = reg_fonts[slug]["urls"][market]
    for s in slugs:
        if s not in out:
            out[s] = pinterest_registry.primary_url(reg_fonts[s]) or ""
    return out


def extract_candidates(text: str, max_out: int = 12) -> list[str]:
    """Mechanical keyword seed from a description: style/use-case/format hits
    assembled into search-phrase candidates. A seed only — the agent varies
    phrasing and the ledger rotates."""
    t = " " + text.lower() + " "
    def hit(term: str) -> bool:
        return re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", t) is not None
    styles = [s for s in STYLE_TERMS if hit(s)]
    uses = [u for u in USE_CASE_TERMS if hit(u)]
    fmts = [f for f in FORMAT_TERMS if hit(f)]
    out: list[str] = []
    for u in uses[:2]:
        for s in styles[:2]:
            out.append(f"{u} {s} font")
    for s in styles[:3]:
        out.append(f"{s} font")
    for u in uses[:3]:
        out.append(f"{u} font")
    out.extend(fmts[:3])
    seen: set[str] = set()
    res: list[str] = []
    for c in out:
        c = " ".join(c.split())
        if c and c not in seen:
            seen.add(c)
            res.append(c)
    return res[:max_out]


def load_content_profile(rec: dict) -> tuple[dict | None, str | None]:
    """Load the preparer's metadata-and-visual profile when one is registered."""
    prep = Path(rec.get("prep_path") or ".").resolve()
    profile_value = rec.get("profile_path")
    path = Path(profile_value) if profile_value else prep / "pinterest-profile.json"
    path = path.resolve()
    try:
        path.relative_to(prep)
    except ValueError:
        sys.exit(f"error: Pinterest profile must stay inside the preparation folder: {path}")
    if not path.is_file():
        return None, str(path)
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        sys.exit(f"error: invalid Pinterest profile {path}: {error}")
    if not isinstance(profile, dict) or profile.get("schema_version") != 1:
        sys.exit(f"error: Pinterest profile {path} must be an object with schema_version 1")
    if str(profile.get("font_name", "")).strip().casefold() != str(rec.get("name", "")).strip().casefold():
        sys.exit(f"error: Pinterest profile {path} does not match registered font {rec.get('name')!r}")
    for key in ("metadata_summary", "visual_summary"):
        if not isinstance(profile.get(key), str) or not profile[key].strip():
            sys.exit(f"error: Pinterest profile {path} needs a non-empty {key}")
    for key in ("letterform_traits", "mood_terms", "best_uses", "keyword_bank"):
        value = profile.get(key)
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            sys.exit(f"error: Pinterest profile {path} has an invalid {key} list")
    return profile, str(path)


def merge_candidates(profile: dict | None, description: str) -> list[str]:
    """Put the reviewed profile's phrases first, then add mechanical seeds."""
    candidates = (profile.get("keyword_bank") or []) if profile else []
    candidates = list(candidates) + (extract_candidates(description, max_out=12) if description else [])
    seen: set[str] = set()
    result: list[str] = []
    for candidate in candidates:
        phrase = " ".join(str(candidate).split())
        key = phrase.casefold()
        if phrase and key not in seen:
            seen.add(key)
            result.append(phrase)
        if len(result) >= 60:
            break
    return result


def cmd_pick(args, con) -> int:
    if not 1 <= args.count <= 10:
        sys.exit("error: count must be between 1 and 10 for the current Buffer free-plan batch")
    reg = pinterest_registry.load_registry()
    eligible = [s for s, r in reg["fonts"].items()
                if pinterest_registry.is_ready(r) and s not in recent_pins(con, args.date)]
    if not eligible:
        sys.exit("error: no ready fonts remain after the 14-day exclusion; confirm each font has a valid prepper-assigned board, product URL, and complete uploaded image set")
    seed = args.seed or f"{args.date}:{args.count}"
    rng = random.Random(seed)
    chosen = sorted(rng.sample(eligible, min(args.count, len(eligible))))
    out_dir = day_dir(args.date)
    out_dir.mkdir(parents=True, exist_ok=True)
    sel = {"date": args.date, "seed": seed, "requested": args.count,
           "eligible": len(eligible), "fonts": chosen}
    (out_dir / "selection.json").write_text(json.dumps(sel, indent=2) + "\n")
    if args.json:
        print(json.dumps(sel, indent=2))
    else:
        reg_fonts = reg["fonts"]
        for s in chosen:
            r = reg_fonts[s]
            print(f"{str(r['number'] or '-'):>4}  {s:<28} {r['board'] or '-'}")
        print(f"picked {len(chosen)}/{args.count} from {len(eligible)} eligible "
              f"(14-day exclusion applied; seed {seed})")
        if len(chosen) < args.count:
            print("warning: fewer eligible fonts than requested — prepare and classify "
                  "more fonts, or wait until the 14-day exclusion window passes")
        for s in chosen:
            urls = reg_fonts[s].get("urls") or {}
            for market, url in urls.items():
                if url and looks_like_shop_root(url):
                    print(f"warning: {s}: {market} URL {url!r} looks like a shop root, "
                          f"not a product page — set-url before importing this CSV")
    return 0


def cmd_brief(args, con) -> int:
    sel, reg = read_selection(args.date)
    image_assignments = assign_images(sel["fonts"], reg["fonts"], args.date)
    lines = [f"# Pinterest brief — {args.date}", ""]
    brief_fonts = []
    for slug in sel["fonts"]:
        r = reg["fonts"][slug]
        desc = ""
        if r.get("description_path") and Path(r["description_path"]).is_file():
            raw = Path(r["description_path"]).read_text(errors="replace")
            desc = " ".join(raw.split())[:400]
        used = pinterest_tag_ledger.font_counts(con, slug)
        top_used = sorted(used.items(), key=lambda kv: -kv[1])[:8]
        prior = pinterest_tag_ledger.font_pins(con, slug, PRIOR_PINS_IN_BRIEF)
        profile, profile_path = load_content_profile(r)
        candidates = merge_candidates(profile, desc)
        urls = r.get("urls") or {}
        board = r.get("board")
        if not board:
            sys.exit(f"error: {slug} has no preparer-assigned Pinterest board; rerun `/pinterest-prepare` first")
        try:
            board = pinterest_registry.normalize_board(board)
        except SystemExit:
            sys.exit(f"error: {slug} has an invalid Pinterest board assignment; rerun `/pinterest-prepare`")
        today_image = image_assignments.get(slug)
        entry = {
            "slug": slug, "number": r.get("number"), "name": r.get("name"),
            "board": board, "urls": urls,
            "today_image": ({
                "index": today_image.get("index"),
                "kind": today_image.get("kind"),
                "template": today_image.get("template"),
                "description": image_description(r, today_image),
                "source_path": today_image.get("source"),
                "url": today_image.get("url"),
            } if today_image else None),
            "description_excerpt": desc,
            "profile_path": profile_path,
            "profile": ({
                "metadata_summary": profile.get("metadata_summary"),
                "visual_summary": profile.get("visual_summary"),
                "letterform_traits": profile.get("letterform_traits", []),
                "mood_terms": profile.get("mood_terms", []),
                "best_uses": profile.get("best_uses", []),
                "keyword_bank": profile.get("keyword_bank", []),
            } if profile else None),
            "candidates": candidates,
            "most_used_tags": [t for t, _ in top_used],
            "previous_pins": prior,
        }
        brief_fonts.append(entry)
        lines.append(f"## {r['name']} ({slug})")
        lines.append(f"- Assigned board (from preparer): {board}")
        if today_image:
            index_label = f"#{today_image['index']}" if today_image.get("index") else "selected"
            lines.append(f"- Assigned image {index_label}: {image_description(r, today_image)}")
            if today_image.get("source"):
                lines.append(f"- Local image to inspect for accurate alt text: {today_image['source']}")
            lines.append(f"- Media URL used by both CSVs: {today_image['url']}")
            lines.append("- Alt text must describe this exact image and its visible wording/layout; do not use a generic font-only specimen description.")
        else:
            lines.append("- Assigned image: MISSING — no uploaded image URL is available.")
        if urls.get("creative_market"):
            lines.append(f"- Creative Market product URL: {urls['creative_market']}")
        if urls.get("creative_fabrica"):
            lines.append(f"- Creative Fabrica product URL: {urls['creative_fabrica']}")
        lines.append("- Image choice is stable for this date and balanced across selected fonts; "
                     "when both product URLs exist, destinations are split as evenly as possible.")
        lines.append(f"- Description source: {desc or '(no description.txt)'}…")
        if profile:
            lines.append(f"- Content profile: {profile_path}")
            lines.append(f"- Verified metadata: {profile['metadata_summary']}")
            lines.append(f"- Visual vibe: {profile['visual_summary']}")
            if profile.get("letterform_traits"):
                lines.append(f"- Letterform traits: {', '.join(profile['letterform_traits'])}")
            if profile.get("mood_terms"):
                lines.append(f"- Mood terms: {', '.join(profile['mood_terms'])}")
            if profile.get("best_uses"):
                lines.append(f"- Best-fit uses: {', '.join(profile['best_uses'])}")
        else:
            lines.append(f"- Content profile: MISSING ({profile_path}); use description fallback and flag for preparer refresh.")
        if candidates:
            source = "reviewed profile + description seed" if profile else "description-only seed"
            lines.append(f"- Candidate keywords ({source}; filter for this Pin, then rotate via ledger): {', '.join(candidates)}")
        if entry["most_used_tags"]:
            lines.append(f"- Tags already used most (rotate away): {', '.join(entry['most_used_tags'])}")
        if prior:
            lines.append(f"- ALREADY PINNED — write copy that reads differently; "
                         f"repeating your own strings is what cannibalizes:")
            for p in prior:
                lines.append(f"  - {p['run_date']} [{p['board']}] {p['title']}")
                lines.append(f"      keywords: {p['keywords']}")
            newest = prior[0]
            if newest.get("alt"):
                lines.append(f"  - most recent alt text: {newest['alt']}")
        else:
            lines.append("- No previous pin recorded for this font — first run.")
        lines.append("")
    text = "\n".join(lines)
    day_dir(args.date).mkdir(parents=True, exist_ok=True)
    (day_dir(args.date) / "brief.md").write_text(text)
    if args.json:
        print(json.dumps(brief_fonts, indent=2))
    else:
        print(text)
    return 0


def read_selection(date: str) -> tuple[dict, dict]:
    path = day_dir(date) / "selection.json"
    if not path.is_file():
        sys.exit(f"error: {path} missing — run `pick --date {date}` first")
    return json.loads(path.read_text()), pinterest_registry.load_registry()


def add_utm(url: str, date: str, content: str) -> str:
    sep = "&" if "?" in url else "?"
    return (f"{url}{sep}utm_source=pinterest&utm_medium=organic_pin"
            f"&utm_campaign=daily-{date}&utm_content={content}")


def validate(entries: list[dict], reg: dict, date: str, start_hour: int, interval: int) -> tuple[list[list[str]], list[str]]:
    errors: list[str] = []
    rows: list[list[str]] = []
    titles: dict[str, int] = {}
    links: dict[str, int] = {}
    batch_links = assign_links([e.get("slug") or "" for e in entries], reg["fonts"], date)
    batch_images = assign_images([e.get("slug") or "" for e in entries], reg["fonts"], date)
    now = datetime.now(timezone.utc)
    start = datetime.strptime(f"{date}T00:00:00", "%Y-%m-%dT%H:%M:%S").replace(
        hour=start_hour, tzinfo=timezone.utc)
    if interval > 0:
        last = start + timedelta(minutes=interval * (len(entries) - 1))
        if last.day != start.day:
            errors.append(f"stagger spills past midnight: {len(entries)} pins × {interval} min from {start_hour:02d}:00 UTC")
    if start <= now:
        errors.append(f"first publish slot {start:%Y-%m-%dT%H:%M:%S} UTC is not in the future — use a later date")
    if start > now + timedelta(days=SCHEDULING_WINDOW_DAYS):
        errors.append(f"first publish slot is more than {SCHEDULING_WINDOW_DAYS} days out")
    for i, e in enumerate(entries):
        slug = e.get("slug") or f"row{i + 1}"
        if slug not in reg["fonts"]:
            errors.append(f"{slug}: not in registry")
            continue
        r = reg["fonts"][slug]
        title = str(e.get("title", "")).strip()
        if not (1 <= len(title) <= 100):
            errors.append(f"{slug}: title must be 1-100 chars (got {len(title)})")
        titles[title] = titles.get(title, 0) + 1
        desc = str(e.get("description", "")).strip()
        if not (1 <= len(desc) <= 500):
            errors.append(f"{slug}: description must be 1-500 chars (got {len(desc)})")
        alt = str(e.get("alt", "")).strip()
        if not (1 <= len(alt) <= 500):
            errors.append(f"{slug}: alt must be 1-500 chars (got {len(alt)}) — buffer.csv needs it")
        kws = [pinterest_tag_ledger.norm(k) for k in e.get("keywords", [])]
        kws = list(dict.fromkeys(k for k in kws if k))
        if any("#" in k for k in kws):
            errors.append(f"{slug}: keywords must not contain #")
        if not (MIN_KEYWORDS <= len(kws) <= MAX_KEYWORDS):
            errors.append(f"{slug}: need {MIN_KEYWORDS}-{MAX_KEYWORDS} keywords (got {len(kws)})")
        registered_board = r.get("board")
        if not registered_board:
            errors.append(f"{slug}: no preparer-assigned board; rerun /pinterest-prepare")
            continue
        try:
            board = pinterest_registry.normalize_board(registered_board)
        except SystemExit:
            errors.append(f"{slug}: invalid registry board {registered_board!r}; rerun /pinterest-prepare")
            continue
        requested_board = e.get("board")
        if requested_board:
            try:
                requested_board = pinterest_registry.normalize_board(requested_board)
            except SystemExit:
                errors.append(f"{slug}: unknown board {requested_board!r}")
                continue
            if requested_board != board:
                errors.append(f"{slug}: copy board {requested_board!r} conflicts with preparer assignment {board!r}")
                continue
        link = e.get("link") or batch_links.get(slug)
        if not link:
            errors.append(f"{slug}: no product URL in registry and no link in copy")
            continue
        link = add_utm(link, date, f"{slug}-{i + 1}")
        if e.get("link"):
            links[link] = links.get(link, 0) + 1
        selected_image = batch_images.get(slug)
        media = selected_image.get("url") if selected_image else None
        if not media:
            errors.append(f"{slug}: no uploaded image URL in registry")
            continue
        pub = start + timedelta(minutes=interval * i)
        rows.append([title, media, board, "", desc, link,
                     pub.strftime("%Y-%m-%dT%H:%M:%S"), ", ".join(kws)])
        e["_tags"] = kws
        e["_alt"] = alt
        e["_image_index"] = selected_image.get("index") if selected_image else None
        e["_pub"] = pub.strftime("%Y-%m-%d %H:%M")
    for t, n in titles.items():
        if n > 1:
            errors.append(f"duplicate title ×{n}: {t[:60]!r}")
    for l, n in links.items():
        if n > 1:
            errors.append(f"duplicate link ×{n} in batch (dedup risk): {l[:80]!r}")
    return rows, errors


def cmd_assemble(args, con) -> int:
    sel, reg = read_selection(args.date)
    copy_path = day_dir(args.date) / "copy.json"
    if not copy_path.is_file():
        sys.exit(f"error: {copy_path} missing — the agent must write pin copy first")
    entries = json.loads(copy_path.read_text())
    if not isinstance(entries, list):
        sys.exit("error: copy.json must be a JSON list of pin objects")
    if not entries:
        sys.exit("error: copy.json has no pins to assemble")
    picked, slugs = sel["fonts"], [e.get("slug") for e in entries]
    if slugs != picked:
        sys.exit(f"error: copy.json slugs/order don't match selection.json\n"
                 f"  selection: {picked}\n  copy:      {slugs}")
    imported = {row[0] for row in con.execute(
        "SELECT font_slug FROM pins WHERE run_date=? AND font_slug IN (%s)" %
        ",".join("?" for _ in picked), (args.date, *picked))} if picked else set()
    if imported:
        sys.exit("error: this date already has imported pin history for "
                 f"{', '.join(sorted(imported))}; do not overwrite an imported batch")
    rows, errors = validate(entries, reg, args.date, args.start_hour, args.interval_min)
    if errors:
        print("validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
    out_dir = day_dir(args.date)
    csv_path = out_dir / "pins.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)
        w.writerows(rows)
    buffer_path = out_dir / "buffer.csv"
    buffer_rows = [[r[4], r[1], r[2], "", e["_pub"], r[0], e["_alt"], r[5]]
                   for e, r in zip(entries, rows)]
    with buffer_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(BUFFER_HEADER)
        w.writerows(buffer_rows)
    report = [f"# Draft tag report — {args.date}", "",
              "These are prepared drafts. History and re-pin exclusion update only after you confirm the destination accepted the import.", ""]
    for e, row in zip(entries, rows):
        pinterest_tag_ledger.prepare_pin(
            con, slug=e["slug"], date=args.date, title=row[0], description=row[4],
            alt=e["_alt"], keywords=e["_tags"], board=row[2], image_url=row[1],
            link=row[5], csv_path=str(csv_path))
        counts = pinterest_tag_ledger.font_counts(con, e["slug"])
        total = sum(counts.values()) or 1
        top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        report.append(f"## {e['slug']}")
        report.append(f"- prepared keywords: {', '.join(e['_tags'])}")
        if top:
            report.append("- historical tag mix: " + ", ".join(f"{t} ({100 * c // total}%)" for t, c in top))
        report.append(f"- selected image index: {e.get('_image_index') or 'unknown'}")
    con.commit()
    (out_dir / "tag-report.md").write_text("\n".join(report) + "\n")
    print(f"buffer.csv written: {buffer_path} ({len(buffer_rows)} rows, publish {rows[0][6]} → {rows[-1][6]} UTC)")
    print(f"pins.csv written:   {csv_path} (Pinterest-native fallback, no alt text)")
    print("Buffer requires each Board Name in the CSV to already exist in Pinterest; see the agent guide for one-time setup.")
    print("After Buffer accepts/queues rows (or Pinterest accepts pins.csv), record only those fonts:")
    print(f"python3 bin/pinterest_tag_ledger.py mark-imported --date {args.date} --slugs " + " ".join(picked))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="command", required=True)

    pk = sub.add_parser("pick", parents=[common])
    pk.add_argument("--date", required=True)
    pk.add_argument("--count", type=int, default=10)
    pk.add_argument("--seed")
    pk.set_defaults(func=cmd_pick)

    br = sub.add_parser("brief", parents=[common])
    br.add_argument("--date", required=True)
    br.set_defaults(func=cmd_brief)

    asm = sub.add_parser("assemble", parents=[common])
    asm.add_argument("--date", required=True)
    asm.add_argument("--start-hour", type=int, default=9, help="first publish hour UTC (default 9)")
    asm.add_argument("--interval-min", type=int, default=60, help="minutes between pins (default 60)")
    asm.set_defaults(func=cmd_assemble)

    args = ap.parse_args(argv)
    return args.func(args, pinterest_tag_ledger.open_db())


if __name__ == "__main__":
    sys.exit(main())
