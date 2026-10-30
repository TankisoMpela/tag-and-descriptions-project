#!/usr/bin/env python3
"""Rights queue and verdict ledger for staged fonts under ``font-factory/input/``.

Mechanical half of the font-rights workflow: it answers "what is unresearched",
shows the evidence embedded in each binary, and validates and stores the verdict
a research agent decides. It never decides anything itself, and it never edits
the font, the manifest, or ``in-use.txt``.

Verdicts live in ``font-factory/input/<folder>/rights-verdicts.json``, keyed by
exact filename. The staging folder number is not a product number, so nothing
here carries ``{NUM}``.

That staging directory is gitignored, so ``sync`` mirrors the sidecars into one
tracked ledger under ``outputs/research/`` — committing that ledger is what gives a
verdict a history, since returning a font deletes its record from the folder.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "font-factory" / "input"
SIDECAR = "rights-verdicts.json"
# ``font-factory/input/`` is gitignored, so the sidecars and the fonts they describe
# both vanish if the staging is cleaned out. This mirrors them into one tracked file:
# a mirror, not an archive, so the history of a deleted verdict is git's.
LEDGER = ROOT / "outputs" / "research" / "font-rights-ledger.json"
FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}
STATES = ("claimed", "orphan", "clear")
# name IDs the tool quotes evidence from: style/family, preferred family,
# copyright, unique ID, postscript name, manufacturer, designer, vendor URL,
# author URL, licence, licence info URL.
NAME_IDS = (0, 1, 2, 3, 6, 8, 9, 11, 12, 13, 14, 19)
GRANT_IDS = (0, 11, 12, 13, 14)
DEAD_CODES = {404, 410}
UA = "Mozilla/5.0 (compatible; font-rights-check)"

# Where a ``claimed`` evidence URL is allowed to live. Red asserts an active rights
# offer or claim, so the page has to be capable of making that good: a commercial
# seller, the claimed holder's own domain, or a type-rights reference. Free-font
# directories are useful provenance, but a page hosting a download is not itself a
# rights claim; those URLs belong in the separate research.sources field.
SELLER_DOMAINS = frozenset(
    {
        "myfonts.com", "fonts.com", "monotype.com", "linotype.com", "creativelibrary.com",
        "fonts.adobe.com", "rentafont.com", "fontspring.com", "creativefabrica.com",
        "creative.market",
    }
)
# Directory pages are recorded as distribution history, not as evidence that the
# uploader owns the font or that a download label grants commercial rights.
DISTRIBUTION_DOMAINS = frozenset(
    {
        "dafont.com", "fontsgeek.com", "fontgeek.com", "fontfreak.com", "fontspace.com",
        "1001fonts.com", "1001freefonts.com", "abstractfonts.com", "fontasy.de",
        "1001freefonts.net", "ffonts.net", "fontsquirrel.com", "fontlibrary.org",
        "openfontlibrary.org", "fontarchive.com", "fontsc.com", "fontframe.com",
        "urbanfonts.com", "fontpalace.com",
    }
)
# No shop, but a documented record of who made and owns a design — Devroye's catalogue
# of foundries and their fate is the backbone of the defunct-holder research.
REFERENCE_DOMAINS = frozenset({"luc.devroye.org", "devroyefonts.com", "fontsinuse.com", "whattheythink.com"})
# Name-table scrapers that re-publish the metadata of this exact dump. They are the
# corpus echoing back at itself: finding the font there proves a file was uploaded,
# never that a holder is alive, so they can never support any verdict.
MIRROR_DOMAINS = frozenset(
    {"wfonts.com", "onlinewebfonts.com", "fontpark.com", "ziti.net.cn", "fontsfree.org", "webfonts.org"}
)
# This dump is full of fonts whose head dates were zeroed by whoever repackaged
# them; fontTools shouts about it on every open, and the noise would bury the
# queue output.
logging.getLogger("fontTools").setLevel(logging.ERROR)


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def natural_key(text: str) -> list:
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", text)]


def folders() -> list[Path]:
    if not INPUT_DIR.is_dir():
        return []
    return sorted(
        (p for p in INPUT_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")),
        key=lambda p: natural_key(p.name),
    )


def resolve_folder(value: str) -> Path | None:
    """Accept ``7``, ``7-Bulmer_MT`` or ``Bulmer`` when it matches exactly one folder."""
    wanted = value.strip()
    for folder in folders():
        if folder.name.lower() == wanted.lower():
            return folder
    if wanted.isdigit():
        for folder in folders():
            if re.match(rf"^{wanted}(-|$)", folder.name):
                return folder
    hits = [f for f in folders() if wanted.lower() in f.name.lower()]
    return hits[0] if len(hits) == 1 else None


def font_files(folder: Path) -> list[Path]:
    try:
        return sorted(
            (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in FONT_EXTENSIONS),
            key=lambda p: natural_key(p.stem),
        )
    except OSError:
        return []


CORE_STYLE = re.compile(r"\b(reg(ular)?|normal|roman|plain|book|text|standard)\b", re.I)
OTHER_STYLE = re.compile(
    r"\b(italic|oblique|bold|light|thin|black|semi|med|cond|extd|extended|compr|"
    r"outline|inline|shadow|display|caps|alt|alternates)\b",
    re.I,
)


def plan_of(folder: Path) -> tuple[Path, dict, list[tuple[Path, dict]]]:
    """The staged folder is one family: the Regular answers for all of it.

    The seller curates folders by family, so researching every weight is
    redundant. This picks the file that represents the family — plain style
    first, then the shortest name — and returns it with every sibling.
    """
    members = [(path, embedded(path)) for path in font_files(folder)]
    if not members:
        reject(f"{folder.name} holds no font files")

    def rank(index: int, path: Path, info: dict) -> tuple:
        style = squash(info["names"].get("2") or "") or squash(path.stem)
        core = bool(CORE_STYLE.search(style))
        fancy = bool(OTHER_STYLE.search(style))
        return (fancy and not core, not core, len(path.stem), index)

    _path, _info, index = min(
        ((path, info, i) for i, (path, info) in enumerate(members)),
        key=lambda item: rank(item[2], item[0], item[1]),
    )
    return members[index][0], members[index][1], members


def load_sidecar(folder: Path) -> tuple[dict, str | None]:
    """Return (payload, error). A missing file is an empty payload, not an error."""
    target = folder / SIDECAR
    if not target.exists():
        return ({}, None)
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return ({}, "unreadable")
    if not isinstance(data, dict) or not isinstance(data.get("verdicts"), dict):
        return ({}, "unreadable")
    return (data, None)


def save(folder: Path, payload: dict) -> None:
    target = folder / SIDECAR
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, target)


def embedded(path: Path) -> dict:
    """Read the evidence a font carries about itself; never decompile outlines."""
    out: dict = {"names": {}, "fstype": None, "created": None, "modified": None, "error": None}
    try:
        with TTFont(path, lazy=True, ignoreDecompileErrors=True) as font:
            names: dict[str, str] = {}
            for rec in font["name"].names:
                if rec.nameID in NAME_IDS:
                    try:
                        text = str(rec)
                    except Exception:
                        continue
                    names.setdefault(str(rec.nameID), text)
            out["names"] = names
            if "OS/2" in font:
                out["fstype"] = font["OS/2"].fsType
            if "head" in font:
                for key in ("created", "modified"):
                    value = getattr(font["head"], key, None)
                    if isinstance(value, int) and value > 0:
                        try:
                            stamp = datetime(1904, 1, 1) + timedelta(seconds=value)
                            out[key] = stamp.strftime("%Y-%m-%d")
                        except (OverflowError, ValueError):
                            out[key] = f"raw:{value}"
    except Exception as error:  # unreadable binary is evidence in itself
        out["error"] = type(error).__name__
    return out


def check_link(url: str, timeout: int = 12) -> tuple[str, int]:
    """Classify a URL as live, blocked or dead. Only a definitive answer rejects."""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            code = getattr(response, "status", 200)
    except urllib.error.HTTPError as error:
        code = error.code
    except Exception:
        return ("dead", 0)
    if code in DEAD_CODES:
        return ("dead", code)
    if code < 400:
        return ("live", code)
    return ("blocked", code)


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def identity(text: str) -> str:
    """Matching form of a name string: punctuation and spacing differences are noise.

    Two cuts of the same family routinely differ only in "reserved. monotype" versus
    "reserved.monotype", which would otherwise split a group into two passes.
    """
    return re.sub(r"[^a-z0-9]", "", text.casefold())


def holder_of(names: dict) -> str:
    """Matching form of the holder a file claims: manufacturer, else copyright, else designer."""
    return identity(names.get("8") or names.get("0") or names.get("9") or "")


def foreign_holders(rep_names: dict, members: list[tuple[Path, dict]]) -> list[str]:
    """Siblings whose claimed holder differs from the one this folder was judged on.

    A folder is meant to hold one family, so a differing holder string means the
    folder also holds somebody else's production — which must never inherit a verdict.
    """
    base = holder_of(rep_names)
    return [path.name for path, sibling in members if holder_of(sibling["names"]) != base]


def host_of(url: str) -> str:
    """Lowercased host of a URL with no leading www — the thing a domain rule is judged on."""
    netloc = urllib.parse.urlsplit(url if "//" in url else "http://" + url).netloc
    host = netloc.rsplit("@", 1)[-1].split(":", 1)[0].lower()
    return host[4:] if host.startswith("www.") else host


def on_domain(host: str, domains: frozenset) -> bool:
    return any(host == domain or host.endswith("." + domain) for domain in domains)


# Host labels that say nothing about who owns a design. Matching on these would let
# any .org URL look like the holder's own site whenever "org" survives in a
# normalised copyright string.
GENERIC_LABELS = frozenset(
    {
        "com", "org", "net", "edu", "gov", "mil", "int", "info", "biz", "xyz", "club",
        "co", "uk", "de", "fr", "jp", "ru", "cn", "in", "io", "me", "tv", "cc", "eu",
        "www", "cdn", "static", "assets", "images", "media", "files", "web", "app",
        "shop", "store", "blog", "news", "help", "support", "docs", "api",
    }
)


def evidence_class(url: str, holder_text: str) -> str:
    """Classify claim-capable URLs separately from distribution-only listings.

    ``unknown`` is a page that can be perfectly live and still prove nothing: a blog
    post, a forum thread, a re-host of the font itself. ``holder_text`` must already
    be in identity() form, so a foundry's own domain matches the name in the file.
    """
    host = host_of(url)
    if on_domain(host, MIRROR_DOMAINS):
        return "mirror"
    if on_domain(host, DISTRIBUTION_DOMAINS):
        return "distribution"
    if on_domain(host, SELLER_DOMAINS):
        return "seller"
    if on_domain(host, REFERENCE_DOMAINS):
        return "reference"
    labels = [item for item in host.split(".") if item not in GENERIC_LABELS]
    if any(len(label) >= 3 and label in holder_text for label in labels):
        return "holder"
    return "unknown"


RESEARCH_FIELDS = frozenset(
    {
        "author", "author_status", "first_known_date", "age_estimate", "age_basis",
        "distribution_assessment", "abandonware_assessment", "abandonware_basis", "sources",
    }
)
RESEARCH_REQUIRED_FIELDS = RESEARCH_FIELDS
RESEARCH_SOURCE_FIELDS = frozenset(
    {
        "site", "url", "source_type", "match", "availability", "distribution_label",
        "uploader", "date", "note",
    }
)
RESEARCH_SOURCE_REQUIRED_FIELDS = RESEARCH_SOURCE_FIELDS - {"note"}
RESEARCH_SOURCE_TYPES = frozenset(
    {"free_distribution", "commercial_listing", "author", "reference", "archive", "other"}
)


def research_record(raw: str) -> dict:
    """Validate and normalize the sourced provenance notes stored beside a verdict."""
    if not raw.strip():
        reject("--research-json is required; use 'unknown' with a short reason when a detail is unavailable")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        reject(f"--research-json is not valid JSON: {error.msg}")
    if not isinstance(value, dict):
        reject("--research-json must be a JSON object")
    missing = RESEARCH_REQUIRED_FIELDS - set(value)
    if missing:
        reject("--research-json is missing required field(s): " + ", ".join(sorted(missing)))
    unknown = set(value) - RESEARCH_FIELDS
    if unknown:
        reject("--research-json has unknown field(s): " + ", ".join(sorted(unknown)))

    result: dict = {}
    for key, item in value.items():
        if key == "sources":
            if not isinstance(item, list):
                reject("research.sources must be a JSON list")
            if len(item) > 20:
                reject("research.sources may contain at most 20 pages per family pass")
            sources: list[dict] = []
            for index, source in enumerate(item, start=1):
                if not isinstance(source, dict):
                    reject(f"research.sources[{index}] must be a JSON object")
                missing_source = RESEARCH_SOURCE_REQUIRED_FIELDS - set(source)
                if missing_source:
                    reject(
                        f"research.sources[{index}] is missing required field(s): "
                        + ", ".join(sorted(missing_source))
                    )
                extra = set(source) - RESEARCH_SOURCE_FIELDS
                if extra:
                    reject(f"research.sources[{index}] has unknown field(s): " + ", ".join(sorted(extra)))
                if not isinstance(source.get("site"), str) or not source["site"].strip():
                    reject(f"research.sources[{index}].site is required")
                if not isinstance(source.get("url"), str):
                    reject(f"research.sources[{index}].url is required")
                try:
                    parsed = urllib.parse.urlsplit(source["url"].strip())
                    hostname = parsed.hostname
                except ValueError:
                    reject(f"research.sources[{index}].url is malformed")
                if parsed.scheme not in ("http", "https") or not hostname:
                    reject(f"research.sources[{index}].url must be an absolute http(s) URL")
                source_type = source.get("source_type")
                if not isinstance(source_type, str) or source_type not in RESEARCH_SOURCE_TYPES:
                    reject(
                        f"research.sources[{index}].source_type must be one of: "
                        + ", ".join(sorted(RESEARCH_SOURCE_TYPES))
                    )
                normalized = {"site": source["site"].strip(), "url": source["url"].strip(),
                              "source_type": source_type}
                for field in RESEARCH_SOURCE_FIELDS - {"site", "url", "source_type"}:
                    field_value = source.get(field, "")
                    if not isinstance(field_value, str):
                        reject(f"research.sources[{index}].{field} must be text")
                    if len(field_value) > 500:
                        reject(f"research.sources[{index}].{field} is longer than 500 characters")
                    if field_value.strip():
                        normalized[field] = field_value.strip()
                    elif field in RESEARCH_SOURCE_REQUIRED_FIELDS:
                        reject(f"research.sources[{index}].{field} must contain a finding or 'unknown'")
                sources.append(normalized)
            result[key] = sources
            continue
        if not isinstance(item, str):
            reject(f"research.{key} must be text")
        if len(item) > 2000:
            reject(f"research.{key} is longer than 2000 characters")
        if item.strip():
            result[key] = item.strip()
        elif key in RESEARCH_REQUIRED_FIELDS:
            reject(f"research.{key} must contain a finding or 'unknown' with its reason")

    assessment = result.get("abandonware_assessment", "").casefold()
    if assessment and assessment not in {"yes", "no", "unclear"}:
        reject("research.abandonware_assessment must be yes, no, or unclear")
    if assessment and not result.get("abandonware_basis"):
        reject("research.abandonware_assessment needs research.abandonware_basis")
    return result


def group_key(info: dict) -> tuple:
    """The rights identity of a font: same design name, same claimed holder, same licence bits.

    Research answers "who owns this design and do they still sell it", which is a
    family question, not a per-weight question — so a verdict may fan out to the
    siblings that share all three. A re-cut with a different maker string or a
    different fsType is a different production and never inherits.
    """
    names = info["names"]
    family = identity(names.get("19") or names.get("1") or names.get("6") or "")
    return (family, holder_of(names), info["fstype"])


def reject(message: str) -> None:
    print(f"REJECTED: {message}", file=sys.stderr)
    raise SystemExit(2)


def cmd_status(args: argparse.Namespace) -> int:
    scoped = [resolve_folder(args.folder)] if args.folder else folders()
    scoped = [f for f in scoped if f]
    if not scoped:
        print(f"No staged folders under {INPUT_DIR}")
        return 0
    total_marked = total_fonts = 0
    tally = {state: 0 for state in STATES}
    unmarked: list[str] = []
    for folder in scoped:
        payload, error = load_sidecar(folder)
        verdicts = payload.get("verdicts", {})
        files = font_files(folder)
        marked = [p.name for p in files if p.name in verdicts]
        total_marked += len(marked)
        total_fonts += len(files)
        for name in marked:
            state = verdicts[name].get("state")
            if state in tally:
                tally[state] += 1
        note = "  [verdict file unreadable]" if error else ""
        print(f"{folder.name}  {len(marked)}/{len(files)} researched{note}")
        if args.unmarked and len(marked) < len(files):
            unmarked.append(folder.name)
    print(
        f"\nTOTAL {total_marked}/{total_fonts} researched across {len(scoped)} folder(s)"
        f"  ·  {tally['claimed']} claimed / {tally['orphan']} orphan / {tally['clear']} clear."
    )
    if args.unmarked:
        if not unmarked:
            print("Queue empty: every staged family has a verdict.")
        else:
            print(f"\nFOLDERS NEEDING A PASS ({len(unmarked)}) — one research pass each, in this order:")
            for item in unmarked[: args.limit]:
                print(f"  {item}")
            if len(unmarked) > args.limit:
                print(f"  … {len(unmarked) - args.limit} more (raise --limit)")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    folder = resolve_folder(args.folder)
    if folder is None:
        reject(f"folder {args.folder!r} is missing or ambiguous under {INPUT_DIR}")
    rep, info, members = plan_of(folder)
    verdicts = load_sidecar(folder)[0].get("verdicts", {})
    names = info["names"]
    marked = [path.name for path, _ in members if path.name in verdicts]
    unmarked = [path.name for path, _ in members if path.name not in verdicts]

    print(f"folder: {folder.name}  ·  {len(members)} file(s)  ·  ONE family, ONE research pass")
    print(f"research this one: {rep.name!r}")
    print(f"  family: {names.get('19') or names.get('1') or names.get('6') or '(nothing in the file)'}")
    print(f"  holder: {names.get('8') or names.get('0') or names.get('9') or '(none — match on the family name only)'}")
    print(f"  fsType: {info['fstype']}  ·  head created {info['created']} / modified {info['modified']}")
    print(f"  licence: {(names.get('13') or '(no licence string in the file)')[:160]}")
    print(f"inherits: {len(members) - 1} sibling(s) — write this verdict with --fanout")
    if marked:
        print(f"already marked: {len(marked)}/{len(members)}")
        if rep.name in verdicts and unmarked:
            print(f"  the family is judged; {len(unmarked)} sibling(s) never inherited — "
                  f"re-write the representative with --amend --fanout to spread it")
    odd = foreign_holders(names, members)
    if odd:
        print(f"! {len(odd)} file(s) name a different holder than the representative —")
        print("  the folder is meant to be one family, so this is a curation sign, not a research task:")
        for name in odd[:8]:
            print(f"    {name}")
        if len(odd) > 8:
            print(f"    … {len(odd) - 8} more")
    return 0


def cmd_groups(args: argparse.Namespace) -> int:
    folder = resolve_folder(args.folder)
    if folder is None:
        reject(f"folder {args.folder!r} is missing or ambiguous under {INPUT_DIR}")
    groups: dict[tuple, list[tuple[Path, dict]]] = {}
    for path in font_files(folder):
        info = embedded(path)
        groups.setdefault(group_key(info), []).append((path, info))
    verdicts = load_sidecar(folder)[0].get("verdicts", {})
    print(f"folder: {folder.name}  ·  {len(font_files(folder))} font(s) in {len(groups)} rights group(s)")
    print("one research pass per group; the first file is the representative.\n")
    for (family, holder, fstype), members in groups.items():
        names = members[0][1]["names"]
        print(f"[{fstype if fstype is not None else '?'}] "
              f"{(names.get('19') or names.get('1') or names.get('6') or '(no family name in the file)')[:40]}"
              f"  ·  holder: {(names.get('8') or names.get('0') or names.get('9') or '(none — nothing to match on)')[:64]}")
        if not family or not holder:
            print("    ! nothing to group on — this file stands alone unless you can name the holder")
        for index, (path, _info) in enumerate(members):
            mark = "← research this one" if index == 0 else "  inherits  "
            done = verdicts.get(path.name, {}).get("state", "")
            print(f"    {mark} {path.name}" + (f"  [{done}]" if done else ""))
        print()
    needed = sum(1 for m in groups.values() if not any(verdicts.get(p.name) for p, _ in m))
    print(f"Passes needed: {needed} of {len(groups)} group(s)"
          f"  ·  {sum(len(m) for m in groups.values())} files,"
          f" so one pass covers {sum(len(m) for m in groups.values()) / max(len(groups), 1):.1f} fonts on average.")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    folder = resolve_folder(args.folder) if args.folder else None
    if folder is None:
        if args.folder:
            reject(f"folder {args.folder!r} is missing or ambiguous under {INPUT_DIR}")
        reject("show needs --folder")
    payload, error = load_sidecar(folder)
    if error:
        print(f"NOTE: existing {SIDECAR} is unreadable and will be treated as empty.\n")
    if args.file:
        match = next((p for p in font_files(folder) if p.name == args.file), None)
        if match is None:
            reject(f"{args.file!r} is not a font file in {folder.name}")
        info = embedded(match)
        print(f"folder: {folder.name}\nfile: {match.name}")
        print(f"fsType: {info['fstype']}  head.created: {info['created']}  head.modified: {info['modified']}")
        if info["error"]:
            print(f"binary error: {info['error']}")
        for key in NAME_IDS:
            value = info["names"].get(str(key))
            if value:
                print(f"  name{key}: {value[:200]}")
        verdict = payload.get("verdicts", {}).get(match.name)
        print("verdict: " + (json.dumps(verdict, ensure_ascii=False) if verdict else "none"))
        return 0
    print(f"folder: {folder.name}  ({len(payload.get('verdicts', {}))} verdicts on file)\n")
    for path in font_files(folder):
        info = embedded(path)
        names = info["names"]
        holder = names.get("0") or names.get("8") or names.get("9") or "(no holder in the file)"
        state = payload.get("verdicts", {}).get(path.name, {}).get("state", "unresearched")
        print(f"{path.name}\n  {state}  |  fsType {info['fstype']}  |  {holder[:120]}")
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    folder = resolve_folder(args.folder)
    if folder is None:
        reject(f"folder {args.folder!r} is missing or ambiguous under {INPUT_DIR}")
    path = next((p for p in font_files(folder) if p.name == args.file), None)
    if path is None:
        reject(f"{args.file!r} is not a font file in {folder.name}")

    payload, error = load_sidecar(folder)
    if error:
        reject(f"{SIDECAR} in {folder.name} is unreadable; fix or remove it before writing")
    stored_folder = payload.get("folder")
    if stored_folder and stored_folder != folder.name:
        reject(f"{SIDECAR} belongs to {stored_folder!r}, not {folder.name!r} — do not move verdicts between folders")
    verdicts = payload.setdefault("verdicts", {})
    if args.file in verdicts and not args.amend:
        reject(f"{args.file} already has a verdict; pass --amend to replace it (the old one is kept in history)")

    evidence = list(args.evidence or [])
    looked = list(args.looked or [])
    research = research_record(args.research_json)
    info = embedded(path)
    grant = args.grant_quote
    contact = args.author_contact
    confidence = args.confidence
    holder_text = identity(
        " ".join(info["names"].get(i, "") for i in ("0", "6", "8", "9", "11", "12")) + " " + args.maker
    )
    kinds: list[str] = []

    if args.state == "claimed":
        if not evidence:
            reject("claimed needs at least one --evidence URL of the live offer")
        kinds = [evidence_class(url, holder_text) for url in evidence]
        if not any(kind in ("seller", "reference", "holder") for kind in kinds):
            reject(
                "no --evidence URL here can carry a rights claim ("
                + ", ".join(f"{host_of(url)}: {kind}" for url, kind in zip(evidence, kinds))
                + ") — red needs the shop selling it, the holder's own domain, or a type-rights "
                  "reference; free-font directories are distribution records, not rights claims"
            )
        if args.skip_link_check:
            link_state = "skipped"
        else:
            checked = [(url, *check_link(url)) for url in evidence]
            for url, state, code in checked:
                print(f"  link {state} ({code}) {url}")
            if all(state == "dead" for _url, state, _code in checked):
                reject("every --evidence URL is a dead page; a dead link does not prove a live offer")
            link_state = "verified" if any(state == "live" for _url, state, _code in checked) else "blocked-only"

    elif args.state == "orphan":
        if evidence:
            reject("orphan means no live holder was found; --evidence contradicts it — use claimed, or drop the URLs")
        distinct = {squash(item) for item in looked if item.strip()}
        if len(distinct) < 2:
            reject("orphan needs at least two distinct --looked avenues actually searched (e.g. myfonts, dafont)")
        if confidence == "high":
            reject("orphan cannot be high confidence — 'I found nobody' is never proof; use medium, or claim/verify a grant")
        link_state = "not-applicable"

    else:  # clear
        if grant:
            haystack = squash(" ".join(info["names"].get(str(i), "") for i in GRANT_IDS))
            if squash(grant) not in haystack:
                reject(
                    "grant_quote was not found in this binary's name records (0/11/12/13/14). "
                    "An in-file claim you cannot quote from the file is not a grant — write orphan "
                    "and put the wording in --note"
                )
        if contact:
            if not re.search(r"[@.]", contact):
                reject("author_contact must be a URL or an email address reached this run")
            if not args.skip_link_check and "@" not in contact:
                url = contact if contact.startswith("http") else "https://" + contact
                if check_link(url)[0] == "dead":
                    reject("author_contact target does not resolve")
        if not grant and not contact:
            reject("clear needs --grant-quote (verified in the binary) or --author-contact (reached this run)")
        if not confidence:
            confidence = "high"
        link_state = "not-applicable"

    if confidence not in ("high", "medium", "low"):
        confidence = confidence or "medium"

    record = {
        "state": args.state,
        "maker": args.maker or "",
        "evidence": evidence,
        "evidence_kind": kinds,
        "looked": looked,
        "note": args.note or "",
        "confidence": confidence,
        "fstype": info["fstype"],
        "grant_quote": grant,
        "author_contact": contact,
        "research": research,
        "link_check": link_state,
        "checked_utc": now(),
        "derived_from": None,
        "history": [],
    }
    if args.file in verdicts:
        prior = dict(verdicts[args.file])
        prior.pop("history", None)
        record["history"] = list(verdicts[args.file].get("history", [])) + [prior]
        record["history"] = record["history"][-10:]
    verdicts[args.file] = record

    inherited: list[str] = []
    held_back: list[str] = []
    if args.fanout:
        siblings = [(path, embedded(path)) for path in font_files(folder) if path.name != args.file]
        odd = foreign_holders(info["names"], siblings)
        if args.state == "clear" and odd:
            held_back.append(
                f"{len(odd)} sibling(s) name a different holder than {args.file} "
                f"({', '.join(odd[:5])}{' …' if len(odd) > 5 else ''}) — a grant never "
                f"inherits across holders; judge those files on their own"
            )
        else:
            for sibling, sibling_info in siblings:
                if sibling.name in verdicts and not args.amend:
                    held_back.append(f"{sibling.name}: already judged on its own")
                    continue
                if grant:
                    haystack = squash(
                        " ".join(sibling_info["names"].get(str(i), "") for i in GRANT_IDS)
                    )
                    if squash(grant) not in haystack:
                        held_back.append(f"{sibling.name}: grant quote is not in this binary")
                        continue
                copy = dict(record)
                copy["derived_from"] = args.file
                copy["fstype"] = sibling_info["fstype"]
                copy["history"] = []
                if sibling.name in verdicts:
                    prior = dict(verdicts[sibling.name])
                    prior.pop("history", None)
                    copy["history"] = list(verdicts[sibling.name].get("history", [])) + [prior]
                    copy["history"] = copy["history"][-10:]
                verdicts[sibling.name] = copy
                inherited.append(sibling.name)

    payload["version"] = 1
    payload["folder"] = folder.name
    payload["updated_utc"] = now()
    save(folder, payload)
    print(f"WROTE {args.state} for {args.file} in {folder.name} ({SIDECAR})")
    if args.fanout:
        print(f"  fanned out to {len(inherited)} sibling(s) in {folder.name}"
              + (f": {', '.join(inherited)}" if inherited else ""))
        for reason in held_back:
            print(f"  held back — {reason}")
    return 0


def ledger_payload() -> dict:
    """Every verdict currently on disk in the staged sidecars, in folder order."""
    entries: dict[str, dict] = {}
    unreadable: list[str] = []
    totals = {state: 0 for state in STATES}
    verdicts_total = 0
    for folder in [item for item in folders() if item]:
        payload, error = load_sidecar(folder)
        if error:
            unreadable.append(folder.name)
            continue
        verdicts = payload.get("verdicts", {})
        if not verdicts:
            continue
        for record in verdicts.values():
            if record.get("state") in totals:
                totals[record["state"]] += 1
        entries[folder.name] = {
            "updated_utc": payload.get("updated_utc"),
            "verdicts": verdicts,
        }
        verdicts_total += len(verdicts)
    return {
        "version": 1,
        "synced_utc": now(),
        "source": f"{INPUT_DIR.relative_to(ROOT)}/*/{SIDECAR}",
        "totals": {"folders": len(entries), "verdicts": verdicts_total, **totals},
        "unreadable": unreadable,
        "folders": entries,
    }


def cmd_sync(args: argparse.Namespace) -> int:
    data = ledger_payload()
    totals = data["totals"]
    if args.check:
        try:
            stored = json.loads(LEDGER.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            stored = None
        if isinstance(stored, dict) and stored.get("folders") == data["folders"]:
            print(f"LEDGER UP TO DATE — {totals['verdicts']} verdict(s) in {LEDGER.relative_to(ROOT)}")
            return 0
        print(
            f"LEDGER STALE or missing — the sidecars hold {totals['verdicts']} verdict(s); "
            f"run `sync` so the tracked copy in {LEDGER.relative_to(ROOT)} matches.",
            file=sys.stderr,
        )
        return 1
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEDGER.with_suffix(LEDGER.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, LEDGER)
    print(
        f"LEDGER {totals['verdicts']} verdict(s) across {totals['folders']} folder(s) "
        f"· {totals['claimed']} claimed / {totals['orphan']} orphan / {totals['clear']} clear"
    )
    print(f"  wrote {LEDGER.relative_to(ROOT)}")
    for name in data["unreadable"]:
        print(f"  WARNING: {name}'s {SIDECAR} is unreadable — not mirrored")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="what is researched and what is still queued")
    status.add_argument("--folder")
    status.add_argument("--unmarked", action="store_true", help="also list the folders still needing a research pass")
    status.add_argument("--limit", type=int, default=200)
    status.set_defaults(func=cmd_status)

    show = sub.add_parser("show", help="the evidence a folder or one font carries")
    show.add_argument("--folder", required=True)
    show.add_argument("--file")
    show.set_defaults(func=cmd_show)

    plan = sub.add_parser("plan", help="one research pass per staged folder: the family and its representative")
    plan.add_argument("--folder", required=True)
    plan.set_defaults(func=cmd_plan)

    groups = sub.add_parser("groups", help="which staged fonts share one rights question")
    groups.add_argument("--folder", required=True)
    groups.set_defaults(func=cmd_groups)

    write = sub.add_parser("write", help="store a verdict, validating it first")
    write.add_argument("--folder", required=True)
    write.add_argument("--file", required=True)
    write.add_argument("--state", required=True, choices=STATES)
    write.add_argument("--maker", default="")
    write.add_argument("--evidence", action="append", help="URL backing a claimed offer or rights-holder claim (repeat)")
    write.add_argument("--looked", action="append", help="search avenue with no matching page (repeat)")
    write.add_argument("--note", default="")
    write.add_argument(
        "--research-json", default="",
        help="required JSON research: author, age, distribution, abandonware and source pages",
    )
    write.add_argument("--confidence", default="")
    write.add_argument("--grant-quote", default="", help="verbatim text found in this binary's name records")
    write.add_argument("--author-contact", default="", help="URL or email reached this run")
    write.add_argument("--amend", action="store_true", help="replace an existing verdict, keeping it in history")
    write.add_argument("--fanout", action="store_true",
                       help="spread this verdict over the rest of the folder — the staged folder is one family, so the Regular answers for every weight")
    write.add_argument("--skip-link-check", action="store_true", help="no network; recorded as unverified")
    write.set_defaults(func=cmd_write)

    sync = sub.add_parser("sync", help="mirror the sidecars into the tracked ledger under outputs/research")
    sync.add_argument("--check", action="store_true", help="report drift instead of writing")
    sync.set_defaults(func=cmd_sync)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
