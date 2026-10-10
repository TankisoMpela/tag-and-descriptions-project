#!/usr/bin/env python3
"""Build a separate BOOTH brush ZIP with a supplied Japanese README.

The source directory is never modified. Existing README files are omitted
from the delivery copy and replaced by the supplied README.txt content.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


STORE_URL = "https://fontfairy.booth.pm/"
README_NAMES = {"readme", "readme.txt", "readme.md", "readme.rst"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path, help="source/ directory containing the brush files")
    parser.add_argument("readme", type=Path, help="agent-written Japanese README text")
    parser.add_argument("output_zip", type=Path, help="separate BOOTH delivery ZIP")
    args = parser.parse_args()

    source_dir = args.source_dir.expanduser().resolve()
    readme = args.readme.expanduser().resolve()
    output_zip = args.output_zip.expanduser().resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"Source directory not found: {source_dir}")
    if not readme.is_file():
        raise SystemExit(f"README file not found: {readme}")
    readme_text = readme.read_text(encoding="utf-8")
    if STORE_URL not in readme_text:
        raise SystemExit(f"README must contain the FontFairy BOOTH URL: {STORE_URL}")
    files = sorted(path for path in source_dir.rglob("*") if path.is_file())
    if not files:
        raise SystemExit(f"No source files found in {source_dir}")

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_zip, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            if path.name.casefold() in README_NAMES:
                continue
            archive.write(path, path.relative_to(source_dir).as_posix())
        archive.writestr("README.txt", readme_text.replace("\r\n", "\n"))

    with ZipFile(output_zip) as archive:
        names = archive.namelist()
        if "README.txt" not in names:
            raise SystemExit("Packaging failed: README.txt is missing from the ZIP")
        if not any(name.lower().endswith((".abr", ".brush", ".brushset")) for name in names):
            raise SystemExit("Packaging failed: no .abr, .brush, or .brushset file is present")
    print(f"Wrote {output_zip}")
    print(f"Files in package: {len(names)}")
    print(f"README: README.txt; store: {STORE_URL}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from error
