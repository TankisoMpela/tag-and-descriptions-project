#!/usr/bin/env python3
"""Move one selected Saved font family into font-factory/fonts/.

Select the family by exact folder name or choose one eligible folder randomly.
Only direct, original OTF/TTF files in that Saved folder are moved. Nested
repair/output directories and non-font files are intentionally excluded. The
moved source files remain in font-factory/fonts/ as the source of record.
Concurrent selections and moves are serialized.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAVED_ROOT = PROJECT_ROOT / "font-factory" / "Saved"
FONTS_ROOT = PROJECT_ROOT / "font-factory" / "fonts"
FONT_SUFFIXES = {".otf", ".ttf"}


def font_files(folder: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in folder.iterdir()
            if path.is_file() and not path.is_symlink() and path.suffix.lower() in FONT_SUFFIXES
        ),
        key=lambda path: path.name.casefold(),
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    if not slug or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise SystemExit(f"cannot make a safe input slug from {value!r}; pass --slug explicitly")
    return slug


def list_saved() -> int:
    if not SAVED_ROOT.is_dir():
        raise SystemExit(f"Saved directory not found: {SAVED_ROOT}")
    folders = sorted(
        (
            item for item in SAVED_ROOT.iterdir()
            if item.is_dir() and not item.is_symlink() and font_files(item)
        ),
        key=lambda path: path.name.casefold(),
    )
    if not folders:
        print("No Saved folders with root-level OTF/TTF source files.")
        return 0
    for folder in folders:
        files = font_files(folder)
        names = ", ".join(path.name for path in files) if files else "no root-level OTF/TTF files"
        print(f"{folder.name}: {names}")
    return 0


def random_saved_source() -> tuple[str, str]:
    """Choose one stageable Saved family without touching unrelated sources."""
    if not SAVED_ROOT.is_dir():
        raise SystemExit(f"Saved directory not found: {SAVED_ROOT}")
    candidates: list[tuple[str, str]] = []
    for folder in SAVED_ROOT.iterdir():
        if not folder.is_dir() or folder.is_symlink() or not font_files(folder):
            continue
        try:
            slug = slugify(folder.name)
        except SystemExit:
            # Keep non-Latin folder names eligible while making a safe stable
            # ASCII input path for the selected source.
            slug = "saved-" + hashlib.sha256(folder.name.encode("utf-8")).hexdigest()[:10]
        if not (FONTS_ROOT / slug).exists():
            candidates.append((folder.name, slug))
    if not candidates:
        raise SystemExit(
            "No stageable Saved folders with root-level OTF/TTF files and a fresh destination."
        )
    return secrets.choice(candidates)


def matching_import(destination: Path, source_name: str) -> bool:
    """Check that destination is the recorded, intact source for this Saved folder."""
    if destination.is_symlink() or not destination.is_dir():
        return False
    manifest_path = destination / "source-import.json"
    if not manifest_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if manifest.get("source_folder") != f"font-factory/Saved/{source_name}":
        return False
    entries = manifest.get("files")
    if not isinstance(entries, list):
        return False
    recorded = {
        entry.get("name"): entry.get("sha256")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    current = {path.name: sha256(path) for path in font_files(destination)}
    return bool(recorded) and current == recorded


def stage(args: argparse.Namespace) -> int:
    if args.random:
        source_name, selected_slug = random_saved_source()
        print(f"Randomly selected Saved family: {source_name}")
    else:
        source_name, selected_slug = args.source, None
    if not source_name or Path(source_name).name != source_name or source_name in {".", ".."}:
        raise SystemExit(
            "source must be the exact name of one folder directly inside font-factory/Saved"
        )
    if not SAVED_ROOT.is_dir():
        raise SystemExit(f"Saved directory not found: {SAVED_ROOT}")

    source = SAVED_ROOT / source_name
    slug = args.slug or selected_slug or slugify(source_name)
    destination = FONTS_ROOT / slug

    if source.is_symlink():
        raise SystemExit(f"Saved source folder is a symlink: {source}")
    if not source.exists():
        if matching_import(destination, source_name):
            if args.random:
                raise SystemExit(
                    "randomly selected Saved family was already claimed by another run; "
                    "start a fresh --random invocation"
                )
            print(f"Already moved with matching source hashes: {destination}")
            print(f"Source workspace: {destination}")
            return 0
        raise SystemExit(f"Saved source folder not found or already moved elsewhere: {source}")
    if not source.is_dir():
        raise SystemExit(f"Saved source folder is not a directory: {source}")
    files = font_files(source)
    if not files:
        if matching_import(destination, source_name):
            if args.random:
                raise SystemExit(
                    "randomly selected Saved family was already claimed by another run; "
                    "start a fresh --random invocation"
                )
            print(f"Already moved with matching source hashes: {destination}")
            print(f"Source workspace: {destination}")
            return 0
        raise SystemExit(f"no direct OTF/TTF source files found in {source}")

    expected = {path.name: sha256(path) for path in files}

    if destination.exists():
        if not destination.is_dir() or destination.is_symlink():
            raise SystemExit(f"destination exists and is not a safe directory: {destination}")
        staged_fonts = font_files(destination)
        actual = {path.name: sha256(path) for path in staged_fonts}
        manifest_path = destination / "source-import.json"
        same_source = all(
            path.name in actual and actual[path.name] == expected[path.name]
            for path in files
        )
        if matching_import(destination, source_name) and same_source:
            # Reconcile older copy-staged imports to the new move contract.
            for path in files:
                path.unlink()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["source_moved"] = True
            manifest["source_moved_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            try:
                source.rmdir()
            except OSError:
                pass
            print(f"Moved source ownership to the matching existing destination: {destination}")
            print(f"Source workspace: {destination}")
            return 0
        raise SystemExit(
            f"refusing to overwrite existing destination {destination}; choose a new --slug"
        )

    FONTS_ROOT.mkdir(parents=True, exist_ok=True)
    destination.mkdir()
    moved: list[Path] = []
    try:
        for path in files:
            target = destination / path.name
            os.replace(path, target)
            moved.append(target)
        moved_hashes = {path.name: sha256(path) for path in moved}
        if moved_hashes != expected:
            raise RuntimeError("source-move checksum mismatch; the move was rolled back")
        manifest = {
            "source_folder": f"font-factory/Saved/{source.name}",
            "staged_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source_moved": True,
            "files": [
                {"name": path.name, "bytes": (destination / path.name).stat().st_size,
                 "sha256": expected[path.name]}
                for path in files
            ],
        }
        (destination / "source-import.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        source.mkdir(parents=True, exist_ok=True)
        for path in reversed(moved):
            if path.exists():
                os.replace(path, source / path.name)
        shutil.rmtree(destination, ignore_errors=True)
        raise

    try:
        source.rmdir()
    except OSError:
        pass
    print(f"Moved {len(files)} original font file(s) into the source workspace: {destination}")
    print(f"Source workspace: {destination}")
    if args.random:
        print(
            "RANDOM_SOURCE_CLAIMED: "
            f"font-factory/Saved/{source.name} -> font-factory/fonts/{slug}"
        )
    for path in files:
        print(f"  {path.name}  sha256={expected[path.name]}")
    print("Source bytes were moved unchanged; nested repair folders were not included.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="list Saved folders and their original root-level OTF/TTF files")
    group.add_argument("--source", help="exact Saved folder whose root font files will be moved")
    group.add_argument("--random", action="store_true", help="randomly choose and stage one eligible Saved family")
    parser.add_argument("--slug", help="destination input slug; defaults to a normalized source-folder name")
    args = parser.parse_args()

    if args.list:
        if args.slug:
            parser.error("--slug is only valid with --source or --random")
        return list_saved()

    # Serialize candidate selection and the complete move so concurrent runs
    # cannot both claim the same still-eligible Saved family.
    lock_path = PROJECT_ROOT / "font-factory" / ".stage_saved_font.lock"
    with lock_path.open("a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        return stage(args)


if __name__ == "__main__":
    raise SystemExit(main())
