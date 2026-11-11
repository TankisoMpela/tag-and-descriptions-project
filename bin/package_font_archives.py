#!/usr/bin/env python3
"""Create one font-named ZIP containing OTF, TTF, and WOFF format folders."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

FORMAT_FOLDERS = {"OTF": ".otf", "TTF": ".ttf", "WOFF": ".woff"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True,
                        help="destination ZIP, normally named after the font")
    args = parser.parse_args()

    package = args.package_dir.expanduser().resolve()
    archive_path = args.archive.expanduser().resolve()
    if not package.is_dir():
        raise SystemExit(f"font package folder not found: {package}")
    files = sorted(path for path in package.rglob("*") if path.is_file())
    unwanted = sorted(
        path.relative_to(package).as_posix() for path in files
        if path.parent.name not in FORMAT_FOLDERS or path.suffix.casefold() != FORMAT_FOLDERS.get(path.parent.name)
    )
    unwanted.extend(path.name for path in package.iterdir()
                    if path.is_dir() and path.name not in FORMAT_FOLDERS)
    unwanted.extend(name for name in FORMAT_FOLDERS if not any(
        path.parent.name == name and path.suffix.casefold() == FORMAT_FOLDERS[name] for path in files
    ))
    if unwanted:
        raise SystemExit("package must contain separate non-empty OTF/TTF/WOFF folders: " + ", ".join(unwanted))
    if not files:
        raise SystemExit(f"no font files found in {package}")

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            entry = f"{package.name}/{path.relative_to(package).as_posix()}"
            info = zipfile.ZipInfo(entry, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())

    expected = {f"{package.name}/{path.relative_to(package).as_posix()}": path.read_bytes() for path in files}
    with zipfile.ZipFile(archive_path) as archive:
        actual = {name: archive.read(name) for name in archive.namelist()}
    if actual != expected:
        archive_path.unlink(missing_ok=True)
        raise SystemExit("archive contents do not exactly match the OTF package")

    print(f"[PASS] one OTF/TTF/WOFF archive: {archive_path}")
    print(f"[PASS] {len(files)} font files in separate format folders, with no extra entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
