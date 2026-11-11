#!/usr/bin/env python3
"""Font registry for the Daily-Pinterest-Run pipeline.

outputs/pinterest/registry.json is the single directory the daily run works
from: one record per font with its preparation folder, description and Pinterest
profile paths, two prepared-product URLs (Creative Market + Creative Fabrica),
an optional Creative Fabrica source-font match, an assigned board, and public
Blob URLs for its manifested composite pins.

Usage:
  python3 bin/pinterest_registry.py add --slug quiet-acre --number 90 [--name "Quiet Acre"]
  python3 bin/pinterest_registry.py set-url --slug quiet-acre --url https://creativemarket.com/... [--market creative_market]
  python3 bin/pinterest_registry.py set-url --slug quiet-acre --url https://creativefabrica.com/... --market creative_fabrica
  python3 bin/pinterest_registry.py set-source-match --slug quiet-acre --status found --url https://creativefabrica.com/...
  python3 bin/pinterest_registry.py set-source-match --slug quiet-acre --status not_found
  python3 bin/pinterest_registry.py set-board --slug quiet-acre --board "Script & Handwriting Fonts"
  python3 bin/pinterest_registry.py upload --slug quiet-acre [--index 3] [--force]   (default: complete manifested set)
  python3 bin/pinterest_registry.py write-urls --slug quiet-acre
  python3 bin/pinterest_registry.py list [--ready]
  python3 bin/pinterest_registry.py show --slug quiet-acre
  Add --json to any command for machine-readable output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

REGISTRY_PATH = Path("outputs/pinterest/registry.json")
BOARDS = [
    "Display Fonts for Logos & Posters",
    "Script & Handwriting Fonts",
    "Serif Fonts for Branding & Editorial",
    "Retro & Vintage Fonts",
    "Gothic & Blackletter Fonts",
    "Pixel, Gaming & Tech Fonts",
    "Cricut & Craft Fonts",
]
LEGACY_BOARDS = {
    "handwritten fonts": "Script & Handwriting Fonts",
    "script fonts": "Script & Handwriting Fonts",
    "display fonts": "Display Fonts for Logos & Posters",
    "decorative fonts": "Display Fonts for Logos & Posters",
}
MARKETS = ["creative_market", "creative_fabrica"]
IMAGE_GLOBS = ("*.png", "*.jpg", "*.jpeg")
PINSET_MANIFEST = "pinterest-set-manifest.json"
TEMPLATE_MANIFEST = "pinterest-template-manifest.json"
MAX_BUFFER_BULK_IMAGE_BYTES = 5_000_000


def migrate(rec: dict) -> dict:
    """v1→v2: product_url → urls.creative_market; single image → images{N}."""
    if "urls" not in rec:
        rec["urls"] = {"creative_market": rec.pop("product_url", None),
                       "creative_fabrica": None}
    if "images" not in rec:
        images: dict[str, dict] = {}
        img = rec.pop("image", None)
        if img and img.get("url"):
            m = re.search(r"pinterest_(\d+)", img.get("pathname", ""))
            images[str(m.group(1)) if m else "1"] = img
        rec["images"] = images
    return rec


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    if not path.exists():
        return {"version": 2, "fonts": {}}
    reg = json.loads(path.read_text())
    for rec in reg.get("fonts", {}).values():
        migrate(rec)
    return reg


def save_registry(reg: dict, path: Path = REGISTRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def normalize_board(board: str) -> str:
    if board.strip().casefold() in LEGACY_BOARDS:
        return LEGACY_BOARDS[board.strip().casefold()]
    for b in BOARDS:
        if b.lower() == board.strip().lower():
            return b
    lowered = board.strip().lower().removesuffix(" fonts").removesuffix(" font")
    for b in BOARDS:
        if b.removesuffix(" Fonts").lower() == lowered:
            return b
    sys.exit(f"error: unknown board {board!r} — choose from {BOARDS}")


def normalize_market(market: str) -> str:
    aliases = {"cm": "creative_market", "cf": "creative_fabrica"}
    market = aliases.get(market.strip().lower(), market.strip().lower())
    if market not in MARKETS:
        sys.exit(f"error: unknown market {market!r} — choose from {MARKETS}")
    return market


def validate_product_url(market: str, url: str) -> str:
    """Reject seller indexes and non-marketplace URLs before they reach Pins."""
    parsed = urlsplit(url.strip())
    host = (parsed.hostname or "").casefold()
    if parsed.scheme != "https" or not parsed.netloc:
        sys.exit("error: marketplace product URLs must use HTTPS")
    if market == "creative_market":
        if host != "creativemarket.com" and not host.endswith(".creativemarket.com"):
            sys.exit("error: Creative Market URL must be on creativemarket.com")
        segments = [part for part in parsed.path.split("/") if part]
        if len(segments) < 2 or any(key in parsed.query.casefold() for key in ("category=", "status=", "page=")):
            sys.exit("error: Creative Market URL looks like a shop/category index, not a product page")
    else:
        if host != "creativefabrica.com" and not host.endswith(".creativefabrica.com"):
            sys.exit("error: Creative Fabrica URL must be on creativefabrica.com")
        segments = [part for part in parsed.path.split("/") if part]
        if len(segments) < 2 or segments[0].casefold() in {"designer", "search", "category", "categories"}:
            sys.exit("error: Creative Fabrica URL looks like a seller/search index, not a product page")
    return url.strip()


def font_dir(prep_path: Path) -> list[Path]:
    """Return every numbered pin and reject duplicate formats or unnumbered files."""
    vis = prep_path / "visuals" / "New-Images" / "pinterest"
    if not vis.is_dir():
        return []
    paths = sorted({path for pattern in IMAGE_GLOBS for path in vis.glob(pattern) if path.is_file()})
    numbered: dict[int, Path] = {}
    for path in paths:
        match = re.fullmatch(r"pinterest_(\d+)", path.stem, re.IGNORECASE)
        if not match:
            sys.exit(f"error: unnumbered Pinterest image must be handled before upload: {path}")
        index = int(match.group(1))
        if index in numbered:
            sys.exit(f"error: multiple files claim Pinterest index {index}: {numbered[index].name}, {path.name}")
        numbered[index] = path
    return [numbered[index] for index in sorted(numbered)]


def validate_pin_set(prep_path: Path, files: list[Path]) -> tuple[dict, int]:
    """Validate the final dynamic pin set against its hash manifest."""
    vis = prep_path / "visuals" / "New-Images" / "pinterest"
    manifest_path = vis / PINSET_MANIFEST
    if not manifest_path.is_file():
        sys.exit(f"error: missing {manifest_path}; run /font-final-images before Pinterest preparation")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        sys.exit(f"error: invalid Pinterest set manifest: {error}")
    rows = manifest.get("images")
    composite_count = manifest.get("composite_count")
    image_count = manifest.get("image_count")
    if (manifest.get("kind") != "font-pinterest-pin-set" or manifest.get("template_count") != 0
            or composite_count != 10 or image_count != 10
            or not isinstance(rows, list) or len(rows) != image_count):
        sys.exit("error: Pinterest set manifest must list exactly ten composites and no template pins")
    file_by_index = {int(path.stem.rsplit("_", 1)[1]): path for path in files}
    if sorted(file_by_index) != list(range(1, image_count + 1)):
        sys.exit(f"error: expected contiguous Pinterest image indexes 1..{image_count}; found {sorted(file_by_index)}")
    if len(files) != image_count:
        sys.exit(f"error: expected exactly {image_count} Pinterest image files; found {len(files)}")
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or row.get("index") != index:
            sys.exit("error: Pinterest set manifest indexes must be contiguous from 1")
        path = vis / str(row.get("file", ""))
        if path.name != row.get("file") or path != file_by_index[index]:
            sys.exit(f"error: Pinterest set manifest file does not match index {index}")
        byte_size = row.get("bytes")
        if not isinstance(byte_size, int) or byte_size < 1:
            sys.exit(f"error: invalid byte size in Pinterest manifest for {path.name}")
        if byte_size > MAX_BUFFER_BULK_IMAGE_BYTES:
            sys.exit(f"error: {path.name} exceeds Buffer's 5 MB bulk-upload safe target; compress or re-export it")
        if path.stat().st_size != row.get("bytes") or hashlib.sha256(path.read_bytes()).hexdigest() != row.get("sha256"):
            sys.exit(f"error: Pinterest image differs from its set manifest: {path.name}")
        if row.get("kind") != "composite":
            sys.exit(f"error: Pinterest image {index} is not a composite")
        if row.get("width") != 1000 or row.get("height") != 2001:
            sys.exit(f"error: Pinterest image {index} has invalid dimensions in the set manifest")
    return manifest, image_count


def verify_public_image(url: str, local_path: Path, manifest_row: dict) -> dict:
    """Confirm an uploaded URL is public, direct, and serves the exact image."""
    parsed = urlsplit(url)
    extension = local_path.suffix.casefold()
    allowed_types = {
        ".png": {"image/png"},
        ".jpg": {"image/jpeg"},
        ".jpeg": {"image/jpeg"},
        ".webp": {"image/webp"},
    }
    if parsed.scheme != "https" or not parsed.hostname:
        sys.exit(f"error: public image URL must use HTTPS: {url}")
    if Path(parsed.path).suffix.casefold() != extension or extension not in allowed_types:
        sys.exit(f"error: public image URL must end in the supported image extension {extension}: {url}")
    expected_bytes = int(manifest_row["bytes"])
    expected_sha = str(manifest_row["sha256"])
    if not 0 < expected_bytes <= MAX_BUFFER_BULK_IMAGE_BYTES:
        sys.exit(f"error: {local_path.name} is outside Buffer's 5 MB bulk-upload safe target")
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; PaperMoon-Image-Check/1.0)"})
    try:
        with urlopen(request, timeout=30) as response:
            status = response.getcode()
            content_type = response.headers.get_content_type().casefold()
            content_length = response.headers.get("Content-Length")
            if status != 200:
                sys.exit(f"error: public image fetch returned HTTP {status}: {url}")
            if content_type not in allowed_types[extension]:
                sys.exit(f"error: {url} returned {content_type}, expected {', '.join(sorted(allowed_types[extension]))}")
            if content_length and int(content_length) != expected_bytes:
                sys.exit(f"error: public image size header differs from manifest for {local_path.name}")
            size = 0
            digest = hashlib.sha256()
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BUFFER_BULK_IMAGE_BYTES:
                    sys.exit(f"error: public image exceeds Buffer's 5 MB bulk-upload safe target: {url}")
                digest.update(chunk)
    except (OSError, ValueError) as error:
        sys.exit(f"error: could not fetch public image URL {url}: {error}")
    if size != expected_bytes or digest.hexdigest() != expected_sha:
        sys.exit(f"error: public image bytes do not match the local manifest for {local_path.name}")
    return {"passed": True, "http_status": status, "content_type": content_type,
            "bytes": size, "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def get_font(reg: dict, slug: str) -> dict:
    fonts = reg["fonts"]
    if slug not in fonts:
        sys.exit(f"error: {slug!r} not in registry — run `add` first")
    return fonts[slug]


def source_font_family(rec: dict) -> str:
    """Read the original family name from Agent 13's source audit report."""
    prep = Path(str(rec.get("prep_path") or ""))
    name_report_path = prep / "name-report.md"
    audit_report_path = prep / "audit-report.md"
    if not name_report_path.is_file() or not audit_report_path.is_file():
        sys.exit("error: preparation name-report.md and audit-report.md are required for a source match")
    name_report = name_report_path.read_text(encoding="utf-8", errors="replace")
    source_file_match = re.search(r"^- \*\*Source Font\*\*: (.+)$", name_report, re.M)
    if not source_file_match:
        sys.exit("error: source font filename is missing from name-report.md")
    source_file = source_file_match.group(1).strip()
    audit_report = audit_report_path.read_text(encoding="utf-8", errors="replace")
    marker = f"=== Auditing: {source_file} ==="
    start = audit_report.find(marker)
    if start < 0:
        sys.exit(f"error: source font {source_file!r} is missing from audit-report.md")
    rest = audit_report[start + len(marker):]
    next_audit = re.search(r"^=== Auditing: ", rest, re.M)
    source_block = rest[:next_audit.start()] if next_audit else rest
    family = re.search(r"^\s*ID 1:\s*(.+)$", source_block, re.M)
    if not family or not family.group(1).strip():
        sys.exit("error: source family name ID 1 is missing from the pre-flight audit")
    return family.group(1).strip()


def is_ready(rec: dict) -> bool:
    urls = rec.get("urls") or {}
    images = rec.get("images") or {}
    image_set = rec.get("image_set") or {}
    try:
        board = normalize_board(str(rec.get("board") or ""))
    except SystemExit:
        board = None
    expected = image_set.get("image_count")
    if isinstance(expected, int) and expected > 0:
        image_indexes = {int(key) for key in images if str(key).isdigit()}
        images_complete = (image_indexes == set(range(1, expected + 1))
                           and all((images.get(str(index)) or {}).get("url")
                                   for index in range(1, expected + 1)))
    else:
        # Keep pre-manifest records usable during migration; all current uploads
        # receive image_set metadata and must have their complete image set.
        images_complete = bool(images) and all(image.get("url") for image in images.values())
    return bool(board
                and (urls.get("creative_market") or urls.get("creative_fabrica"))
                and images_complete)


def primary_url(rec: dict) -> str | None:
    urls = rec.get("urls") or {}
    return urls.get("creative_market") or urls.get("creative_fabrica")


def cmd_add(args, reg: dict) -> int:
    if args.slug in reg["fonts"] and not args.update:
        sys.exit(f"error: {args.slug!r} already registered — pass --update to change it")
    if args.prep_path:
        prep = Path(args.prep_path)
    else:
        candidates = [
            Path(f"outputs/font-preparation/{n:0{w}d}-{args.slug}")
            for w in (1, 2, 3) for n in [args.number]
        ]
        prep = next((p for p in candidates if p.is_dir()), candidates[-1])
    if not prep.is_dir():
        sys.exit(f"error: preparation folder not found: {prep}")
    desc = prep / "description.txt"
    rec = migrate(reg["fonts"].get(args.slug, {}))
    rec.update({
        "slug": args.slug,
        "number": args.number,
        "name": args.name or rec.get("name") or args.slug.replace("-", " ").title(),
        "prep_path": str(prep),
        "description_path": str(desc) if desc.is_file() else None,
        "profile_path": str(prep / "pinterest-profile.json"),
    })
    reg["fonts"][args.slug] = rec
    save_registry(reg)
    out = {"added": args.slug, "prep_path": str(prep), "description_found": desc.is_file()}
    print(json.dumps(out, indent=2) if args.json else f"added {args.slug} ({prep})")
    return 0


def cmd_set_url(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    market = normalize_market(args.market)
    product_url = validate_product_url(market, args.url)
    rec.setdefault("urls", {"creative_market": None, "creative_fabrica": None})
    rec["urls"][market] = product_url
    save_registry(reg)
    print(f"{args.slug}: {market} = {product_url}" if not args.json else json.dumps(rec, indent=2))
    return 0


def cmd_set_source_match(args, reg: dict) -> int:
    """Record whether the original source font has an exact Creative Fabrica item."""
    rec = get_font(reg, args.slug)
    source_name = source_font_family(rec)
    if args.status == "found":
        if not args.url:
            sys.exit("error: --url is required when --status is found")
        product_url = validate_product_url("creative_fabrica", args.url)
    else:
        if args.url:
            sys.exit("error: --url is only allowed when --status is found")
        product_url = None
    rec["source_font_match"] = {
        "source_name": source_name,
        "status": args.status,
        "url": product_url,
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_registry(reg)
    if args.json:
        print(json.dumps({"slug": args.slug, **rec["source_font_match"]}, indent=2))
    else:
        result = product_url or "no confirmed exact source-font match"
        print(f"{args.slug}: Creative Fabrica source match {args.status} — {result}")
    return 0


def cmd_set_board(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    rec["board"] = normalize_board(args.board)
    save_registry(reg)
    print(f"{args.slug}: assigned board = {rec['board']}" if not args.json else json.dumps(rec, indent=2))
    return 0


def cmd_set_profile(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    prep = Path(rec["prep_path"]).resolve()
    profile_path = Path(args.profile_file).resolve()
    try:
        profile_path.relative_to(prep)
    except ValueError:
        sys.exit(f"error: profile file must stay inside the preparation folder: {prep}")
    if not profile_path.is_file():
        sys.exit(f"error: profile file not found: {profile_path}")
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        sys.exit(f"error: invalid Pinterest profile JSON: {error}")
    if not isinstance(profile, dict) or profile.get("schema_version") != 1:
        sys.exit("error: Pinterest profile must be an object with schema_version 1")
    if str(profile.get("font_name", "")).strip().casefold() != str(rec.get("name", "")).strip().casefold():
        sys.exit(f"error: Pinterest profile font_name must match registered name {rec.get('name')!r}")
    for key in ("metadata_summary", "visual_summary"):
        if not isinstance(profile.get(key), str) or not profile[key].strip():
            sys.exit(f"error: Pinterest profile needs a non-empty {key}")
    try:
        datetime.strptime(str(profile.get("reviewed_on", "")), "%Y-%m-%d")
    except ValueError:
        sys.exit("error: Pinterest profile reviewed_on must use YYYY-MM-DD")
    for key in ("metadata_sources", "reviewed_assets", "letterform_traits", "mood_terms", "best_uses", "keyword_bank"):
        value = profile.get(key)
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            sys.exit(f"error: Pinterest profile {key} must be a list of non-empty strings")
    if not profile["metadata_sources"]:
        sys.exit("error: Pinterest profile must cite at least one local metadata source")
    keywords = [" ".join(value.split()).casefold() for value in profile["keyword_bank"]]
    if len(keywords) != len(set(keywords)) or not 10 <= len(keywords) <= 60:
        sys.exit("error: Pinterest profile keyword_bank must contain 10-60 unique phrases")
    review_paths: list[Path] = []
    for value in profile["reviewed_assets"]:
        candidate = (prep / value).resolve()
        try:
            candidate.relative_to(prep)
        except ValueError:
            sys.exit(f"error: reviewed asset must stay inside the preparation folder: {value}")
        if not candidate.is_file():
            sys.exit(f"error: reviewed image is missing: {value}")
        review_paths.append(candidate)
    if len(review_paths) != len(set(review_paths)):
        sys.exit("error: Pinterest profile reviewed_assets contains duplicates")
    if not any("thumbnail_main" in path.name.casefold() for path in review_paths):
        sys.exit("error: Pinterest profile must record a reviewed main thumbnail")
    reviewed_supports = {
        path for path in review_paths
        if path.name.casefold().startswith("support-") and "_1x1" not in path.stem.casefold()
    }
    vis = prep / "visuals" / "New-Images"
    available_supports = {
        path.resolve() for pattern in ("support-*.png", "support-*.jpg", "support-*.jpeg")
        for path in vis.glob(pattern) if "_1x1" not in path.stem.casefold()
    }
    if not reviewed_supports:
        sys.exit("error: Pinterest profile must record reviewed support images")
    if available_supports and reviewed_supports != available_supports:
        missing = sorted(path.name for path in available_supports - reviewed_supports)
        sys.exit("error: Pinterest profile must record every distinct support design; missing: " + ", ".join(missing[:8]))
    try:
        stored_path = str(profile_path.relative_to(Path.cwd().resolve()))
    except ValueError:
        stored_path = str(profile_path)
    rec["profile_path"] = stored_path
    save_registry(reg)
    result = {"slug": args.slug, "profile_path": stored_path,
              "keyword_count": len(profile["keyword_bank"]),
              "reviewed_images": len(review_paths)}
    print(json.dumps(result, indent=2) if args.json else
          f"{args.slug}: profile saved ({len(profile['keyword_bank'])} keywords, {len(review_paths)} reviewed images)")
    return 0


def _upload_one(slug: str, chosen: Path, force: bool, rec: dict,
                manifest_row: dict | None = None) -> dict:
    index = re.search(r"pinterest_(\d+)", chosen.stem)
    # An unnumbered file must not claim slot "1" from pinterest_1.png.
    key = index.group(1) if index else chosen.stem.casefold()
    images = rec.setdefault("images", {})
    source_hash = hashlib.sha256(chosen.read_bytes()).hexdigest()
    if key in images and not force and images[key].get("sha256") == source_hash:
        if manifest_row:
            images[key].update({"kind": manifest_row.get("kind"),
                                "template": manifest_row.get("template")})
        print(f"  skip {chosen.name} (already uploaded — pass --force to replace)")
        return images[key]
    pathname = f"fonts/{slug}/{chosen.stem.lower()}-{source_hash}{chosen.suffix.lower()}"
    upload_command = [sys.executable, "bin/papermoon-blob.py", "upload", str(chosen),
                      "--pathname", pathname, "--json"]
    if force:
        upload_command.append("--allow-overwrite")
    proc = subprocess.run(
        upload_command,
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.exit(f"error: blob upload failed for {chosen.name}:\n{proc.stderr or proc.stdout}")
    blob = json.loads(proc.stdout)
    images[key] = {
        "source": str(chosen),
        "sha256": source_hash,
        "pathname": blob["pathname"],
        "url": blob["url"],
        "uploaded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": (manifest_row or {}).get("kind"),
        "template": (manifest_row or {}).get("template"),
    }
    print(f"  uploaded {chosen.name} → {blob['url']}")
    return images[key]


def cmd_upload(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    prep = Path(rec["prep_path"])
    files = font_dir(prep)
    if not files:
        sys.exit(f"error: no pin images under {rec['prep_path']}/visuals/New-Images/pinterest/")
    pin_manifest, expected_count = validate_pin_set(prep, files)
    manifest_rows = {int(row["index"]): row for row in pin_manifest["images"]}
    set_manifest_path = prep / "visuals" / "New-Images" / "pinterest" / PINSET_MANIFEST
    rec["image_set"] = {
        "template_count": 0,
        "composite_count": pin_manifest["composite_count"],
        "image_count": expected_count,
        "manifest_sha256": hashlib.sha256(set_manifest_path.read_bytes()).hexdigest(),
    }
    if args.index is not None:
        matches = [f for f in files if f.stem == f"pinterest_{args.index}"]
        if not matches:
            sys.exit(f"error: no pinterest_{args.index} image among {[f.name for f in files]}")
        files = matches
    else:
        valid_keys = {str(index) for index in range(1, expected_count + 1)}
        rec["images"] = {key: value for key, value in (rec.get("images") or {}).items()
                         if key in valid_keys}
    for chosen in files:
        index_match = re.search(r"pinterest_(\d+)", chosen.stem)
        metadata = manifest_rows.get(int(index_match.group(1))) if index_match else None
        image = _upload_one(args.slug, chosen, args.force, rec, metadata)
        save_registry(reg)
        if metadata is None:
            sys.exit(f"error: no manifest row found for {chosen.name}")
        image["public_check"] = verify_public_image(image["url"], chosen, metadata)
        save_registry(reg)
        print(f"  public URL verified: HTTP 200, {image['public_check']['content_type']}, "
              f"{image['public_check']['bytes']} bytes, SHA-256 matches")
    images = rec.get("images", {})
    print(f"{args.slug}: {len(images)}/{expected_count} pin images on the Blob store")
    print(json.dumps({"slug": args.slug, "images": images}, indent=2))
    return 0


def cmd_write_urls(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    prep = Path(rec["prep_path"])
    images = rec.get("images") or {}
    if not images:
        sys.exit(f"error: {args.slug} has no uploaded Pinterest image links")
    image_count = (rec.get("image_set") or {}).get("image_count")
    if isinstance(image_count, int) and image_count > 0:
        unchecked = [str(index) for index in range(1, image_count + 1)
                     if not ((images.get(str(index)) or {}).get("public_check") or {}).get("passed")]
        if unchecked:
            sys.exit("error: public image preflight is incomplete for pin(s) "
                     + ", ".join(unchecked) + "; rerun `upload` before writing public-urls.md")
    urls = rec.get("urls") or {}
    rows = [f"# Public Pinterest assets — {rec.get('name') or args.slug}", ""]
    for key in sorted(images, key=lambda value: int(value) if value.isdigit() else 10**9):
        value = images[key]
        rows.append(f"- Pin image {key}: {value.get('url') or 'MISSING'}")
        check = value.get("public_check") or {}
        rows.append(f"  Public image check: {'PASS' if check.get('passed') else 'NOT CHECKED'}")
    rows.extend([
        f"- Creative Market product URL: {urls.get('creative_market') or 'MISSING'}",
        f"- Creative Fabrica product URL: {urls.get('creative_fabrica') or 'MISSING'}",
        f"- Assigned board: {rec.get('board') or 'MISSING'}",
        f"- Pinterest content profile: {rec.get('profile_path') or 'MISSING'}",
    ])
    destination = prep / "public-urls.md"
    destination.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"[PASS] wrote {len(images)} Pinterest links: {destination}")
    return 0


def cmd_list(args, reg: dict) -> int:
    rows = []
    for slug in sorted(reg["fonts"], key=lambda s: rec_num(reg["fonts"][s])):
        rec = reg["fonts"][slug]
        if args.ready and not is_ready(rec):
            continue
        urls = rec.get("urls") or {}
        rows.append({
            "number": rec.get("number"),
            "slug": slug,
            "name": rec.get("name"),
            "board": rec.get("board"),
            "urls": urls,
            "image_count": len(rec.get("images") or {}),
            "ready": is_ready(rec),
        })
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            state = "READY" if r["ready"] else "incomplete"
            n_urls = sum(1 for v in r["urls"].values() if v)
            print(f"{str(r['number'] or '-'):>4}  {r['slug']:<28} {state:<10} "
                  f"board={r['board'] or '-':<18} urls={n_urls}/{len(MARKETS)} "
                  f"imgs={r['image_count']}")
        print(f"{len(rows)} font(s)")
    return 0


def rec_num(rec: dict) -> int:
    return rec.get("number") or 0


def cmd_show(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    print(json.dumps(rec, indent=2, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", parents=[common])
    add.add_argument("--slug", required=True)
    add.add_argument("--number", type=int, required=True)
    add.add_argument("--name")
    add.add_argument("--prep-path")
    add.add_argument("--update", action="store_true", help="overwrite an existing record's paths")
    add.set_defaults(func=cmd_add)

    su = sub.add_parser("set-url", parents=[common])
    su.add_argument("--slug", required=True)
    su.add_argument("--url", required=True)
    su.add_argument("--market", default="creative_market",
                    help="creative_market (default) or creative_fabrica; aliases cm/cf")
    su.set_defaults(func=cmd_set_url)

    sm = sub.add_parser("set-source-match", parents=[common])
    sm.add_argument("--slug", required=True)
    sm.add_argument("--status", choices=("found", "not_found"), required=True,
                    help="whether an exact Creative Fabrica source-font item was confirmed")
    sm.add_argument("--url", help="direct Creative Fabrica item URL; required for found")
    sm.set_defaults(func=cmd_set_source_match)

    sb = sub.add_parser("set-board", parents=[common])
    sb.add_argument("--slug", required=True)
    sb.add_argument("--board", required=True, help="one primary existing Pinterest board; does not create it")
    sb.set_defaults(func=cmd_set_board)

    sp = sub.add_parser("set-profile", parents=[common])
    sp.add_argument("--slug", required=True)
    sp.add_argument("--profile-file", required=True)
    sp.set_defaults(func=cmd_set_profile)

    up = sub.add_parser("upload", parents=[common])
    up.add_argument("--slug", required=True)
    up.add_argument("--index", type=int, help="upload only a specific numbered Pinterest image")
    up.add_argument("--force", action="store_true", help="replace already-uploaded images")
    up.set_defaults(func=cmd_upload)

    li = sub.add_parser("list", parents=[common])
    li.add_argument("--ready", action="store_true",
                    help="product URL + complete current manifest; legacy records need stored image links")
    li.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", parents=[common])
    sh.add_argument("--slug", required=True)
    sh.set_defaults(func=cmd_show)

    urls = sub.add_parser("write-urls", parents=[common])
    urls.add_argument("--slug", required=True)
    urls.set_defaults(func=cmd_write_urls)

    args = ap.parse_args(argv)
    return args.func(args, load_registry())


if __name__ == "__main__":
    sys.exit(main())
