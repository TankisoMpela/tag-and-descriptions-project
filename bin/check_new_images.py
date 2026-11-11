#!/usr/bin/env python3
"""Report the mechanical situation inside a seller's visuals/New-Images folder.

Prints facts only — counts, ratio classification, name-marked thumbnails,
existing generated state — so an agent can inspect the folder and decide
which processor flags to use. Never writes inside the folder.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from process_final_font_images import (  # noqa: E402
    IMAGE_SUFFIXES,
    MAIN_RATIO,
    SQUARE_RATIO,
    SQUARE_THUMB_MARKERS,
    inspect_ratio,
    is_alt_thumbnail_name,
    is_main_thumbnail_name,
    ratio_matches,
)


def classify(path: Path) -> dict[str, object]:
    entry: dict[str, object] = {"file": path.name}
    entry["thumbnail_main_candidate"] = is_main_thumbnail_name(path)
    entry["thumbnail_alt_candidate"] = is_alt_thumbnail_name(path)
    try:
        width, height, ratio = inspect_ratio(path, path.name)
    except SystemExit as error:
        entry["ratio"] = "undecodable"
        entry["error"] = str(error)
        return entry
    entry["width"] = width
    entry["height"] = height
    entry["ratio"] = "3:2" if ratio_matches(ratio, MAIN_RATIO) else (
        "1:1" if ratio_matches(ratio, SQUARE_RATIO) else "unsupported"
    )
    if entry["ratio"] == "1:1":
        entry["name_marked_square_thumbnail"] = any(
            token in path.name.lower() for token in SQUARE_THUMB_MARKERS
        )
    return entry


def generated_state(folder: Path) -> dict[str, object]:
    state: dict[str, object] = {}
    for label, relative in (
        ("source_3x2", "source/3x2"),
        ("source_1x1", "source/1x1"),
        ("main_jpegs", "main"),
        ("square_jpegs", "squares"),
        ("pinterest", "pinterest"),
    ):
        target = folder / relative
        state[label] = len([p for p in target.iterdir() if p.is_file()]) if target.is_dir() else 0
    state["manifest"] = (folder / "final-image-manifest.md").is_file()
    return state


def notes_for(files: list[dict[str, object]]) -> list[str]:
    main = [f for f in files if f["ratio"] == "3:2"]
    squares = [f for f in files if f["ratio"] == "1:1"]
    main_thumbnails = [f for f in main if f.get("thumbnail_main_candidate")]
    square_thumbnails = [f for f in squares if f.get("thumbnail_main_candidate")]
    main_alternates = [f for f in main if f.get("thumbnail_alt_candidate")]
    square_alternates = [f for f in squares if f.get("thumbnail_alt_candidate")]
    notes = []
    if any(f["ratio"] in ("unsupported", "undecodable") for f in files):
        notes.append("Blocker: every direct file must be a decodable 3:2 or 1:1 image.")
    if not main:
        notes.append("Waiting: add the seller-generated 3:2 main thumbnail and supporting images.")
    if not squares:
        notes.append("Waiting: add the seller-generated 1:1 main thumbnail; square thumbnails are never derived from 3:2.")
    if len(main_thumbnails) != 1:
        notes.append("Waiting: name exactly one 3:2 main thumbnail with `thumbnail_main` in its filename (for example `thumbnail_main_3x2.png`).")
    if len(square_thumbnails) != 1:
        notes.append("Waiting: name exactly one 1:1 main thumbnail with `thumbnail_main` in its filename (for example `thumbnail_main_1x1.png`).")
    if len(main_alternates) != 1:
        notes.append("Waiting: name exactly one 3:2 alternate thumbnail with `thumbnail_alt` in its filename (for example `thumbnail_alt_3x2.png`).")
    if len(square_alternates) != 1:
        notes.append("Waiting: name exactly one 1:1 alternate thumbnail with `thumbnail_alt` in its filename (for example `thumbnail_alt_1x1.png`).")
    if len(main) < 3:
        notes.append("Waiting: add at least two additional direct 3:2 images for the ten Pinterest composites.")
    if not notes:
        notes.append("Ready: the main and alternate thumbnail pairs and the minimum 3:2 Pinterest image pool are present.")
    return notes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report facts about a New-Images folder; writes nothing."
    )
    parser.add_argument("folder", type=Path, help="visuals/New-Images folder to inspect")
    parser.add_argument("--json", action="store_true", help="Emit one JSON object instead of text")
    args = parser.parse_args()

    folder = args.folder.expanduser().resolve()
    if not folder.is_dir():
        print(f"Folder not found: {folder}", file=sys.stderr)
        return 1

    direct = sorted(
        p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    )
    files = [classify(path) for path in direct]
    main_thumbnails = [f for f in files
                       if f["ratio"] == "3:2" and f.get("thumbnail_main_candidate")]
    square_thumbnails = [f for f in files
                         if f["ratio"] == "1:1" and f.get("thumbnail_main_candidate")]
    main_alternates = [f for f in files
                       if f["ratio"] == "3:2" and f.get("thumbnail_alt_candidate")]
    square_alternates = [f for f in files
                         if f["ratio"] == "1:1" and f.get("thumbnail_alt_candidate")]
    counts = {
        "3:2": sum(1 for f in files if f["ratio"] == "3:2"),
        "1:1": sum(1 for f in files if f["ratio"] == "1:1"),
        "unsupported": sum(1 for f in files if f["ratio"] == "unsupported"),
        "undecodable": sum(1 for f in files if f["ratio"] == "undecodable"),
    }
    ready = (
        counts["unsupported"] == 0
        and counts["undecodable"] == 0
        and len(main_thumbnails) == 1
        and len(square_thumbnails) == 1
        and len(main_alternates) == 1
        and len(square_alternates) == 1
        and counts["3:2"] >= 3
    )
    report = {
        "folder": str(folder),
        "direct_images": files,
        "counts": counts,
        "ready_for_final_processing": ready,
        "name_marked_square_thumbnails": [
            f["file"] for f in files if f.get("name_marked_square_thumbnail")
        ],
        "thumbnail_main_candidates": {
            ratio: [f["file"] for f in files
                    if f["ratio"] == ratio and f.get("thumbnail_main_candidate")]
            for ratio in ("3:2", "1:1")
        },
        "thumbnail_alt_candidates": {
            ratio: [f["file"] for f in files
                    if f["ratio"] == ratio and f.get("thumbnail_alt_candidate")]
            for ratio in ("3:2", "1:1")
        },
        "generated_state": generated_state(folder),
        "notes": notes_for(files),
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"New-Images situation report: {folder}")
    print("")
    if not direct:
        print("Direct images: none")
        print("")
        for note in report["notes"]:
            print(f"Note: {note}")
        return 0
    print("Direct images (stable filename order = processing order):")
    for entry in files:
        if "width" in entry:
            marker = " [name-marked square thumbnail]" if entry.get("name_marked_square_thumbnail") else ""
            print(f"  {entry['file']}: {entry['width']}x{entry['height']} ({entry['ratio']}){marker}")
        else:
            print(f"  {entry['file']}: UNDECODABLE — {entry.get('error', 'unknown error')}")
    counts = report["counts"]
    print("")
    print(f"Counts: {counts['3:2']} x 3:2, {counts['1:1']} x 1:1, "
          f"{counts['unsupported']} unsupported, {counts['undecodable']} undecodable")
    print(f"Ready for final processing: {'yes' if ready else 'no'}")
    state = report["generated_state"]
    print("Generated state: " + ", ".join(
        f"{key}={value}" for key, value in state.items()
    ))
    print("")
    for note in report["notes"]:
        print(f"Note: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
