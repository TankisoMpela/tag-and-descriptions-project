#!/usr/bin/env python3
"""Font registry for the Daily-Pinterest-Run pipeline.

outputs/pinterest/registry.json is the single directory the daily run works
from: one record per font with its preparation folder, description path,
TWO product-page URLs (Creative Market + Creative Fabrica), a suggested
board, and the public Blob URLs of ALL FOUR pin images.

Usage:
  python3 bin/pinterest_registry.py add --slug quiet-acre --number 90 [--name "Quiet Acre"]
  python3 bin/pinterest_registry.py set-url --slug quiet-acre --url https://creativemarket.com/... [--market creative_market]
  python3 bin/pinterest_registry.py set-url --slug quiet-acre --url https://creativefabrica.com/... --market creative_fabrica
  python3 bin/pinterest_registry.py set-board --slug quiet-acre --board "Script Fonts"
  python3 bin/pinterest_registry.py upload --slug quiet-acre [--index 3] [--force]   (default: all four images)
  python3 bin/pinterest_registry.py list [--ready]
  python3 bin/pinterest_registry.py show --slug quiet-acre
  Add --json to any command for machine-readable output.
"""

from __future__ import annotations

import argparse
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
# Each font is prepared with four pin images; the daily run picks one per pin.
EXPECTED_IMAGES = 4


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
    """The folder's pin images — exactly one file per pinterest_N index.

    Sellers' folders routinely hold both pinterest_1.png and pinterest_1.jpg.
    Images are keyed by index, so returning both would make the second upload a
    silent no-op; IMAGE_GLOBS order makes the lossless .png the one that wins.
    A file with no pinterest_N index is kept under its own name rather than
    dropped, so nothing in the folder is silently ignored.
    """
    vis = prep_path / "visuals" / "New-Images" / "pinterest"
    if not vis.is_dir():
        return []
    numbered: dict[int, Path] = {}
    others: list[Path] = []
    for pattern in IMAGE_GLOBS:
        for path in sorted(vis.glob(pattern)):
            if not path.is_file():
                continue
            m = re.search(r"pinterest_(\d+)", path.stem)
            if m:
                numbered.setdefault(int(m.group(1)), path)
            else:
                others.append(path)
    return [numbered[i] for i in sorted(numbered)] + others


def get_font(reg: dict, slug: str) -> dict:
    fonts = reg["fonts"]
    if slug not in fonts:
        sys.exit(f"error: {slug!r} not in registry — run `add` first")
    return fonts[slug]


def is_ready(rec: dict) -> bool:
    urls = rec.get("urls") or {}
    return bool((urls.get("creative_market") or urls.get("creative_fabrica"))
                and rec.get("images"))


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
    print(f"{args.slug}: board = {rec['board']}" if not args.json else json.dumps(rec, indent=2))
    return 0


def _upload_one(slug: str, chosen: Path, force: bool, rec: dict) -> dict:
    index = re.search(r"pinterest_(\d+)", chosen.stem)
    # An unnumbered file must not claim slot "1" from pinterest_1.png.
    key = index.group(1) if index else chosen.stem.casefold()
    images = rec.setdefault("images", {})
    if key in images and not force:
        print(f"  skip {chosen.name} (already uploaded — pass --force to replace)")
        return images[key]
    pathname = f"fonts/{slug}/{chosen.stem.lower()}{chosen.suffix.lower()}"
    proc = subprocess.run(
        [sys.executable, "bin/papermoon-blob.py", "upload", str(chosen),
         "--pathname", pathname, "--json"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.exit(f"error: blob upload failed for {chosen.name}:\n{proc.stderr or proc.stdout}")
    blob = json.loads(proc.stdout)
    images[key] = {
        "source": str(chosen),
        "pathname": blob["pathname"],
        "url": blob["url"],
        "uploaded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    print(f"  uploaded {chosen.name} → {blob['url']}")
    return images[key]


def cmd_upload(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    files = font_dir(Path(rec["prep_path"]))
    if not files:
        sys.exit(f"error: no pin images under {rec['prep_path']}/visuals/New-Images/pinterest/")
    if args.index is not None:
        matches = [f for f in files if f.stem == f"pinterest_{args.index}"]
        if not matches:
            sys.exit(f"error: no pinterest_{args.index} image among {[f.name for f in files]}")
        files = matches
    elif len(files) < EXPECTED_IMAGES:
        print(f"warning: only {len(files)} pin image(s) found, expected "
              f"{EXPECTED_IMAGES} — the daily run rotates over whatever exists",
              file=sys.stderr)
    for chosen in files:
        _upload_one(args.slug, chosen, args.force, rec)
    save_registry(reg)
    images = rec.get("images", {})
    print(f"{args.slug}: {len(images)}/{EXPECTED_IMAGES} pin images on the Blob store")
    print(json.dumps({"slug": args.slug, "images": images}, indent=2))
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
                  f"imgs={r['image_count']}/{EXPECTED_IMAGES}")
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
    sb.add_argument("--board", required=True)
    sb.set_defaults(func=cmd_set_board)

    up = sub.add_parser("upload", parents=[common])
    up.add_argument("--slug", required=True)
    up.add_argument("--index", type=int, help="upload only a specific pinterest_N image")
    up.add_argument("--force", action="store_true", help="replace already-uploaded images")
    up.set_defaults(func=cmd_upload)

    li = sub.add_parser("list", parents=[common])
    li.add_argument("--ready", action="store_true",
                    help="only fonts with a product URL + at least one image")
    li.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", parents=[common])
    sh.add_argument("--slug", required=True)
    sh.set_defaults(func=cmd_show)

    args = ap.parse_args(argv)
    return args.func(args, load_registry())


if __name__ == "__main__":
    sys.exit(main())
