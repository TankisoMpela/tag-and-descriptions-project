#!/usr/bin/env python3
"""Font registry for the Daily-Pinterest-Run pipeline.

outputs/pinterest/registry.json is the single directory the daily run works
from: one record per font with its preparation folder, description path,
product URL, suggested board, and the public Blob URL of its pin image.

Usage:
  python3 bin/pinterest_registry.py add --slug quiet-acre --number 90 [--name "Quiet Acre"]
  python3 bin/pinterest_registry.py set-url --slug quiet-acre --url https://creativemarket.com/...
  python3 bin/pinterest_registry.py set-board --slug quiet-acre --board "Script Fonts"
  python3 bin/pinterest_registry.py upload --slug quiet-acre --date 2026-10-10 [--index 3] [--force]
  python3 bin/pinterest_registry.py list [--ready]
  python3 bin/pinterest_registry.py show --slug quiet-acre
  Add --json to any command for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = Path("outputs/pinterest/registry.json")
BOARDS = ["Handwritten Fonts", "Display Fonts", "Script Fonts", "Decorative Fonts"]
IMAGE_GLOBS = ("*.png", "*.jpg", "*.jpeg")


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    if not path.exists():
        return {"version": 1, "fonts": {}}
    return json.loads(path.read_text())


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


def font_dir(prep_path: Path) -> list[Path]:
    vis = prep_path / "visuals" / "New-Images" / "pinterest"
    if not vis.is_dir():
        return []
    files: list[Path] = []
    for pattern in IMAGE_GLOBS:
        files.extend(p for p in vis.glob(pattern) if p.is_file())
    return sorted(files)


def pick_image(files: list[Path], seed: str) -> Path:
    return sorted(files, key=lambda p: p.name)[
        random.Random(seed).randrange(len(files))
    ]


def get_font(reg: dict, slug: str) -> dict:
    fonts = reg["fonts"]
    if slug not in fonts:
        sys.exit(f"error: {slug!r} not in registry — run `add` first")
    return fonts[slug]


def is_ready(rec: dict) -> bool:
    return bool(rec.get("product_url") and rec.get("image", {}).get("url"))


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
    rec = reg["fonts"].get(args.slug, {})
    rec.update({
        "slug": args.slug,
        "number": args.number,
        "name": args.name or rec.get("name") or args.slug.replace("-", " ").title(),
        "prep_path": str(prep),
        "description_path": str(desc) if desc.is_file() else None,
    })
    rec.setdefault("product_url", None)
    rec.setdefault("board", None)
    rec.setdefault("image", None)
    reg["fonts"][args.slug] = rec
    save_registry(reg)
    out = {"added": args.slug, "prep_path": str(prep), "description_found": desc.is_file()}
    print(json.dumps(out, indent=2) if args.json else f"added {args.slug} ({prep})")
    return 0


def cmd_set_url(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    rec["product_url"] = args.url
    save_registry(reg)
    print(f"{args.slug}: product_url set" if not args.json else json.dumps(rec, indent=2))
    return 0


def cmd_set_board(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    rec["board"] = normalize_board(args.board)
    save_registry(reg)
    print(f"{args.slug}: board = {rec['board']}" if not args.json else json.dumps(rec, indent=2))
    return 0


def cmd_upload(args, reg: dict) -> int:
    rec = get_font(reg, args.slug)
    files = font_dir(Path(rec["prep_path"]))
    if not files:
        sys.exit(f"error: no pin images under {rec['prep_path']}/visuals/New-Images/pinterest/")
    if rec.get("image") and not args.force:
        sys.exit(f"error: {args.slug} already uploaded ({rec['image']['pathname']}) — pass --force to replace")
    if args.index is not None:
        matches = [f for f in files if f.stem == f"pinterest_{args.index}"]
        if not matches:
            sys.exit(f"error: no pinterest_{args.index} image among {[f.name for f in files]}")
        chosen = matches[0]
    else:
        seed = f"{args.date}:{args.slug}" if args.date else f"{args.slug}"
        chosen = pick_image(files, seed)
    pathname = f"fonts/{args.slug}/{chosen.stem.lower()}{chosen.suffix.lower()}"
    proc = subprocess.run(
        [sys.executable, "bin/papermoon-blob.py", "upload", str(chosen),
         "--pathname", pathname, "--json"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.exit(f"error: blob upload failed:\n{proc.stderr or proc.stdout}")
    blob = json.loads(proc.stdout)
    rec["image"] = {
        "source": str(chosen),
        "pathname": blob["pathname"],
        "url": blob["url"],
        "uploaded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_registry(reg)
    print(json.dumps({"slug": args.slug, "image": rec["image"]}, indent=2))
    return 0


def cmd_list(args, reg: dict) -> int:
    rows = []
    for slug in sorted(reg["fonts"], key=lambda s: reg["fonts"][s].get("number") or 0):
        rec = reg["fonts"][slug]
        if args.ready and not is_ready(rec):
            continue
        rows.append({
            "number": rec.get("number"),
            "slug": slug,
            "name": rec.get("name"),
            "board": rec.get("board"),
            "product_url": rec.get("product_url"),
            "image_url": (rec.get("image") or {}).get("url"),
            "ready": is_ready(rec),
        })
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            state = "READY" if r["ready"] else "incomplete"
            print(f"{str(r['number'] or '-'):>4}  {r['slug']:<28} {state:<10} board={r['board'] or '-':<18} url={'yes' if r['product_url'] else 'no':<3} img={'yes' if r['image_url'] else 'no'}")
        print(f"{len(rows)} font(s)")
    return 0


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
    su.set_defaults(func=cmd_set_url)

    sb = sub.add_parser("set-board", parents=[common])
    sb.add_argument("--slug", required=True)
    sb.add_argument("--board", required=True)
    sb.set_defaults(func=cmd_set_board)

    up = sub.add_parser("upload", parents=[common])
    up.add_argument("--slug", required=True)
    up.add_argument("--date", help="YYYY-MM-DD; makes the random image pick reproducible")
    up.add_argument("--index", type=int, help="force a specific pinterest_N image")
    up.add_argument("--force", action="store_true", help="replace an already-uploaded image")
    up.set_defaults(func=cmd_upload)

    li = sub.add_parser("list", parents=[common])
    li.add_argument("--ready", action="store_true", help="only fonts with product URL + image URL")
    li.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", parents=[common])
    sh.add_argument("--slug", required=True)
    sh.set_defaults(func=cmd_show)

    args = ap.parse_args(argv)
    return args.func(args, load_registry())


if __name__ == "__main__":
    sys.exit(main())
