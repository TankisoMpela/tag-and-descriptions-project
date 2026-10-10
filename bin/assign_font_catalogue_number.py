#!/usr/bin/env python3
"""Assign stable catalogue numbers to font workspaces and preparation outputs.

The catalogue number is deliberately separate from the user-facing font name
and slug. Existing preparation folders can be migrated oldest-first; new
source workspaces retain their path and store the assigned number in
visual-direction/catalogue-number.txt.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


NUMBERED_DIR = re.compile(r"^(\d{3})-(.+)$")
ARCHIVE_DIRS = {"archive", "incoming"}


def unnumbered_name(name: str) -> str:
    while True:
        match = NUMBERED_DIR.fullmatch(name)
        if not match:
            return name
        name = match.group(2)


def age_key(path: Path, kind: str) -> int:
    """Use untouched workspace contents when the root mtime changed on registration."""
    if kind == "source":
        content_paths = [
            child for child in path.rglob("*")
            if "visual-direction" not in child.parts
        ]
        if content_paths:
            return max(child.stat().st_mtime_ns for child in content_paths)
    return path.stat().st_mtime_ns


def list_source_workspaces(source_root: Path) -> list[Path]:
    return [
        path for path in source_root.iterdir()
        if path.is_dir() and path.name.casefold() not in ARCHIVE_DIRS
    ] if source_root.is_dir() else []


def existing_numbers(output_root: Path, source_root: Path | None = None) -> set[int]:
    numbers: set[int] = set()
    if not output_root.is_dir():
        return numbers
    for path in output_root.iterdir():
        if not path.is_dir():
            continue
        match = NUMBERED_DIR.fullmatch(path.name)
        if match:
            numbers.add(int(match.group(1)))
    if source_root and source_root.is_dir():
        for workspace in list_source_workspaces(source_root):
            marker = workspace / "visual-direction" / "catalogue-number.txt"
            if workspace.is_dir() and marker.is_file():
                value = marker.read_text(encoding="utf-8").strip()
                if re.fullmatch(r"\d{3}", value):
                    numbers.add(int(value))
    return numbers


def next_number(output_root: Path, source_root: Path | None = None) -> int:
    numbers = existing_numbers(output_root, source_root)
    if numbers:
        return max(numbers) + 1
    return sum(1 for path in output_root.iterdir() if path.is_dir()) + 1 if output_root.is_dir() else 1


def migrate_outputs(output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    folders = [
        path for path in output_root.iterdir()
        if path.is_dir() and not NUMBERED_DIR.fullmatch(path.name)
    ]
    folders.sort(key=lambda path: (path.stat().st_mtime_ns, path.name.casefold()))
    all_dirs = [path for path in output_root.iterdir() if path.is_dir()]
    occupied = {path.name for path in all_dirs}
    assignments = [(index, path) for index, path in enumerate(folders, start=1)]
    temporary: list[tuple[Path, Path]] = []
    for number, path in assignments:
        temporary_path = output_root / f".__catalogue_migration_{number:03d}__"
        if temporary_path.name in occupied:
            raise SystemExit(f"temporary migration path already exists: {temporary_path}")
        path.rename(temporary_path)
        temporary.append((temporary_path, output_root / f"{number:03d}-{path.name}"))
    for temporary_path, final_path in temporary:
        if final_path.exists():
            raise SystemExit(f"catalogue destination already exists: {final_path}")
        temporary_path.rename(final_path)
        print(f"{final_path.name}")


def migrate_existing(output_root: Path, source_root: Path) -> None:
    """Assign one chronological number sequence across source and outputs."""
    output_root.mkdir(parents=True, exist_ok=True)
    source_root.mkdir(parents=True, exist_ok=True)
    source_workspaces = list_source_workspaces(source_root)
    output_workspaces = [path for path in output_root.iterdir() if path.is_dir()]
    entries = [(age_key(path, "source"), "source", path) for path in source_workspaces]
    entries.extend((age_key(path, "output"), "output", path) for path in output_workspaces)
    entries.sort(key=lambda item: (item[0], item[2].name.casefold(), item[1]))

    output_temporary: list[tuple[Path, Path]] = []
    for number, (_, kind, path) in enumerate(entries, start=1):
        if kind == "source":
            marker_dir = path / "visual-direction"
            marker_dir.mkdir(parents=True, exist_ok=True)
            (marker_dir / "catalogue-number.txt").write_text(f"{number:03d}\n", encoding="utf-8")
        else:
            temporary_path = output_root / f".__catalogue_migration_{number:03d}__"
            path.rename(temporary_path)
            output_temporary.append((temporary_path, output_root / f"{number:03d}-{unnumbered_name(path.name)}"))
    for temporary_path, final_path in output_temporary:
        temporary_path.rename(final_path)
    for _, kind, path in entries:
        print(f"{kind}\t{path.name}")


def register_workspace(workspace: Path, output_root: Path, source_root: Path) -> int:
    if not workspace.is_dir():
        raise SystemExit(f"workspace does not exist: {workspace}")
    marker_dir = workspace / "visual-direction"
    marker = marker_dir / "catalogue-number.txt"
    if marker.is_file():
        value = marker.read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"\d{3}", value):
            raise SystemExit(f"invalid catalogue number in {marker}: {value!r}")
        print(value)
        return int(value)
    number = next_number(output_root, source_root)
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker.write_text(f"{number:03d}\n", encoding="utf-8")
    print(f"{number:03d}")
    return number


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=Path("outputs/font-preparation"))
    parser.add_argument("--source-root", type=Path, default=Path("font-factory/fonts"))
    parser.add_argument("--migrate-outputs", action="store_true")
    parser.add_argument("--migrate-existing", action="store_true")
    parser.add_argument("--workspace", type=Path)
    args = parser.parse_args()

    selected = sum(bool(value) for value in (args.migrate_outputs, args.migrate_existing, args.workspace))
    if selected != 1:
        parser.error("choose exactly one of --migrate-outputs, --migrate-existing, or --workspace")
    if args.migrate_outputs:
        migrate_outputs(args.output_root)
        return 0
    if args.migrate_existing:
        migrate_existing(args.output_root, args.source_root)
        return 0
    register_workspace(args.workspace, args.output_root, args.source_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
