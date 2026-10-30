#!/usr/bin/env python3
"""Font registry for the Daily-Pinterest-Run pipeline.

outputs/pinterest/registry.json is the single directory the daily run works
from: one record per font with its preparation folder, description path,
TWO product-page URLs (Creative Market + Creative Fabrica), a suggested
board, and the public Blob URLs for every manifested template and composite pin.

Usage:
  python3 bin/pinterest_registry.py add --slug quiet-acre --number 90 [--name "Quiet Acre"]
  python3 bin/pinterest_registry.py set-url --slug quiet-acre --url https://creativemarket.com/... [--market creative_market]
  python3 bin/pinterest_registry.py set-url --slug quiet-acre --url https://creativefabrica.com/... --market creative_fabrica
  python3 bin/pinterest_registry.py set-board --slug quiet-acre --board "Script Fonts"
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

REGISTRY_PATH = Path("outputs/pinterest/registry.json")
BOARDS = ["Handwritten Fonts", "Display Fonts", "Script Fonts", "Decorative Fonts"]
MARKETS = ["creative_market", "creative_fabrica"]
IMAGE_GLOBS = ("*.png", "*.jpg", "*.jpeg")
PINSET_MANIFEST = "pinterest-set-manifest.json"
TEMPLATE_MANIFEST = "pinterest-template-manifest.json"


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
    template_count = manifest.get("template_count")
    composite_count = manifest.get("composite_count")
    image_count = manifest.get("image_count")
    if (manifest.get("kind") != "font-pinterest-pin-set" or not isinstance(template_count, int)
            or template_count < 1 or composite_count != 10 or image_count != template_count + composite_count
            or not isinstance(rows, list) or len(rows) != image_count):
        sys.exit("error: Pinterest set manifest must list all template pins plus exactly ten composite pins")
    template_path = vis / TEMPLATE_MANIFEST
    if not template_path.is_file():
        sys.exit(f"error: missing template source manifest: {template_path}")
    try:
        template_manifest = json.loads(template_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        sys.exit(f"error: invalid Pinterest template manifest: {error}")
    template_rows = template_manifest.get("images")
    if template_manifest.get("template_count") != template_count or not isinstance(template_rows, list) or len(template_rows) != template_count:
        sys.exit("error: final set and template manifests disagree on the number of template pins")
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
        if path.stat().st_size != row.get("bytes") or hashlib.sha256(path.read_bytes()).hexdigest() != row.get("sha256"):
            sys.exit(f"error: Pinterest image differs from its set manifest: {path.name}")
        expected_kind = "template" if index <= template_count else "composite"
        if row.get("kind") != expected_kind:
            sys.exit(f"error: Pinterest image {index} has the wrong kind in the set manifest")
        if row.get("width") != 1000 or row.get("height") != 1500:
            sys.exit(f"error: Pinterest image {index} has invalid dimensions in the set manifest")
        if index <= template_count:
            source_row = template_rows[index - 1]
            if row.get("template") != source_row.get("template") or row.get("sha256") != source_row.get("sha256"):
                sys.exit(f"error: template pin {index} differs from Agent 27's template manifest")
    return manifest, image_count


def get_font(reg: dict, slug: str) -> dict:
    fonts = reg["fonts"]
    if slug not in fonts:
        sys.exit(f"error: {slug!r} not in registry — run `add` first")
    return fonts[slug]


def is_ready(rec: dict) -> bool:
    urls = rec.get("urls") or {}
    images = rec.get("images") or {}
    image_set = rec.get("image_set") or {}
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
    return bool((urls.get("creative_market") or urls.get("creative_fabrica"))
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
    })
    reg["fonts"][args.slug] = rec
    save_registry(reg)
    out = {"added": args.slug, "prep_path": str(prep), "description_found": desc.is_file()}
    print(json.dumps(out, indent=2) if args.json else f"added {args.slug} ({prep})")
    return 0


def cmd_set_url(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    market = normalize_market(args.market)
    rec.setdefault("urls", {"creative_market": None, "creative_fabrica": None})
    rec["urls"][market] = args.url
    save_registry(reg)
    print(f"{args.slug}: {market} = {args.url}" if not args.json else json.dumps(rec, indent=2))
    return 0


def cmd_set_board(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    rec["board"] = normalize_board(args.board)
    save_registry(reg)
    print(f"{args.slug}: board suggestion = {rec['board']}" if not args.json else json.dumps(rec, indent=2))
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
        "template_count": pin_manifest["template_count"],
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
        _upload_one(args.slug, chosen, args.force, rec, metadata)
        save_registry(reg)
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
    urls = rec.get("urls") or {}
    rows = [f"# Public Pinterest assets — {rec.get('name') or args.slug}", ""]
    for key in sorted(images, key=lambda value: int(value) if value.isdigit() else 10**9):
        value = images[key]
        rows.append(f"- Pin image {key}: {value.get('url') or 'MISSING'}")
    rows.extend([
        f"- Creative Market product URL: {urls.get('creative_market') or 'MISSING'}",
        f"- Creative Fabrica product URL: {urls.get('creative_fabrica') or 'MISSING'}",
        f"- Board suggestion: {rec.get('board') or 'MISSING'}",
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

    sb = sub.add_parser("set-board", parents=[common])
    sb.add_argument("--slug", required=True)
    sb.add_argument("--board", required=True, help="recommended board; does not create it on Pinterest")
    sb.set_defaults(func=cmd_set_board)

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
