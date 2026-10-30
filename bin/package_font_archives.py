#!/usr/bin/env python3
"""Create matching Commercial-Use and Personal-Use font ZIP archives.

Both archives contain the same clean font binaries. The Personal-Use archive
may additionally contain a like-request note at its root. Free-trial demo
watermarking is no longer part of the preparation workflow.

Preparation runs should prefer ``prepare_font_package.py``, which builds and
audits both archives as part of the complete font preparation pass.
"""

from __future__ import annotations

import argparse
import os
import tempfile
import zipfile
from pathlib import Path


FONT_SUFFIXES = {".otf", ".ttf", ".woff", ".woff2"}
NOTE_NAME = "PLEASE-GIVE-US-A-LIKE.txt"


def _write_archive(
    archive_path: Path,
    files: list[Path],
    package_name: str,
    note: bytes | None,
    note_name: str = NOTE_NAME,
) -> None:
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            entry = f"{package_name}/{path.name}"
            info = zipfile.ZipInfo(entry, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
        if note is not None:
            info = zipfile.ZipInfo(note_name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, note)


def _temporary_path(destination: Path) -> Path:
    """Create a same-directory staging path suitable for atomic replacement."""
    fd, filename = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent, suffix=".tmp"
    )
    os.close(fd)
    return Path(filename)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--commercial", type=Path, required=True)
    parser.add_argument("--personal", type=Path, required=True)
    parser.add_argument(
        "--like-note",
        type=Path,
        default=None,
        help="optional plain-text like-request note in the Personal-Use archive only",
    )
    args = parser.parse_args()

    package_dir = args.package_dir.resolve()
    commercial = args.commercial.resolve()
    personal = args.personal.resolve()
    if not package_dir.is_dir():
        raise SystemExit(f"package folder not found: {package_dir}")
    if commercial == personal:
        raise SystemExit("commercial and personal archives must have different paths")

    files = sorted(path for path in package_dir.iterdir() if path.is_file())
    invalid = [path for path in files if path.suffix.casefold() not in FONT_SUFFIXES]
    nested = [path for path in package_dir.rglob("*") if path.is_dir()]
    if invalid or nested:
        details = [f"non-font file: {path.name}" for path in invalid]
        details.extend(f"nested directory: {path.relative_to(package_dir)}" for path in nested)
        raise SystemExit("package folder must contain font binaries only: " + "; ".join(details))
    if not files:
        raise SystemExit(f"package folder contains no font binaries: {package_dir}")

    like_note = None
    if args.like_note is not None:
        like_path = args.like_note.resolve()
        if not like_path.is_file():
            raise SystemExit(f"archive note not found: {like_path}")
        like_note = like_path.read_bytes()

    commercial.parent.mkdir(parents=True, exist_ok=True)
    personal.parent.mkdir(parents=True, exist_ok=True)
    staged_commercial = _temporary_path(commercial)
    staged_personal = _temporary_path(personal)
    try:
        _write_archive(staged_commercial, files, package_dir.name, note=None)
        _write_archive(staged_personal, files, package_dir.name, note=like_note)

        with zipfile.ZipFile(staged_commercial) as commercial_zip, zipfile.ZipFile(staged_personal) as personal_zip:
            commercial_names = sorted(commercial_zip.namelist())
            personal_names = sorted(personal_zip.namelist())
            expected_font_names = sorted(
                f"{package_dir.name}/{path.name}" for path in files
            )
            commercial_fonts = [name for name in commercial_names
                                if Path(name).suffix.casefold() in FONT_SUFFIXES]
            personal_fonts = [name for name in personal_names
                              if Path(name).suffix.casefold() in FONT_SUFFIXES]
            if commercial_fonts != expected_font_names or personal_fonts != expected_font_names:
                raise SystemExit("archive font entries do not match the prepared package")
            if any(commercial_zip.read(name) != personal_zip.read(name)
                   for name in expected_font_names):
                raise SystemExit("commercial and personal archives have different font binaries")
            if commercial_names != expected_font_names:
                raise SystemExit("commercial archive must contain only the font binaries")
            expected_personal_names = sorted(
                expected_font_names + ([NOTE_NAME] if like_note is not None else [])
            )
            if personal_names != expected_personal_names:
                raise SystemExit("personal archive contains unexpected entries")

        os.replace(staged_commercial, commercial)
        os.replace(staged_personal, personal)
    finally:
        staged_commercial.unlink(missing_ok=True)
        staged_personal.unlink(missing_ok=True)

    print("[PASS] commercial and personal archives carry identical font binaries")
    if like_note is not None:
        print(f"[PASS] personal archive also carries {NOTE_NAME} at archive root")
    print(f"[PASS] packaged {len(files)} font binaries")
    print(f"[PASS] commercial archive: {commercial}")
    print(f"[PASS] personal archive: {personal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
