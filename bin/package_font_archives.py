#!/usr/bin/env python3
"""Create the Commercial-Use, Personal-Use, and Free-Trial-Demo font ZIP archives.

Preparation runs should prefer ``prepare_font_package.py``, which builds all
three archives as part of the same pass. This helper remains for packaging
an already-built package folder by hand.

The Commercial-Use and Personal-Use archives contain the same clean font
binaries (Personal-Use may additionally carry a like-request note at the
archive root). The Free-Trial-Demo archive is rebuilt from a temporary copy
whose digits and ASCII punctuation carry the FontFairy demo stamp
(bin/stamp_personal_use.py); letters stay clean. A demo README may be
supplied at the Free-Trial-Demo archive root.

``--like-note`` supplies the optional Personal-Use like-request note, and
``--demo-readme`` supplies the optional Free-Trial-Demo root README.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


FONT_SUFFIXES = {".otf", ".ttf", ".woff", ".woff2"}
NOTE_NAME = "PLEASE-GIVE-US-A-LIKE.txt"
ROOT = Path(__file__).resolve().parent.parent


def _write_archive(archive_path: Path, files: list[Path], package_name: str, note: bytes | None, note_name: str = NOTE_NAME) -> None:
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive_path_in_zip = f"{package_name}/{path.name}"
            info = zipfile.ZipInfo(archive_path_in_zip, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
        if note is not None:
            info = zipfile.ZipInfo(note_name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, note)


def _stamp_into(package_dir: Path, tmp_root: Path) -> Path:
    """Stamp package_dir into tmp_root/{package_dir.name} via the shared tool."""
    stamp_tool = ROOT / "bin" / "stamp_personal_use.py"
    out_dir = tmp_root / package_dir.name
    result = subprocess.run(
        [
            sys.executable,
            str(stamp_tool),
            "stamp",
            "--package-dir",
            str(package_dir),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            "free-trial-demo stamp failed:\n" + (result.stdout + result.stderr).strip()
        )
    return out_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--commercial", type=Path, required=True)
    parser.add_argument("--personal", type=Path, required=True)
    parser.add_argument(
        "--free-trial-demo",
        type=Path,
        default=None,
        help="destination for the stamped Free-Trial-Demo archive; "
        "defaults to the Personal-Use path with the suffix swapped",
    )
    parser.add_argument(
        "--like-note",
        type=Path,
        default=None,
        help="optional plain-text like-request note embedded at the root of the "
        "Personal-Use archive only; Commercial Use stays font-binaries-only",
    )
    parser.add_argument(
        "--demo-readme",
        type=Path,
        default=None,
        help="README embedded at the root of the Free-Trial-Demo archive",
    )
    parser.add_argument(
        "--no-stamp",
        action="store_true",
        help="skip the stamped Free-Trial-Demo archive (legacy behaviour; "
        "not for new deliveries)",
    )
    args = parser.parse_args()

    package_dir = args.package_dir.resolve()
    if not package_dir.is_dir():
        raise SystemExit(f"package folder not found: {package_dir}")

    files = sorted(path for path in package_dir.iterdir() if path.is_file())
    invalid = [path for path in files if path.suffix.casefold() not in FONT_SUFFIXES]
    nested = [path for path in package_dir.rglob("*") if path.is_dir()]
    if invalid or nested:
        details = [f"non-font file: {path.name}" for path in invalid]
        details.extend(f"nested directory: {path.relative_to(package_dir)}" for path in nested)
        raise SystemExit("package folder must contain font binaries only: " + "; ".join(details))
    if not files:
        raise SystemExit(f"package folder contains no font binaries: {package_dir}")

    demo_path = args.free_trial_demo
    if demo_path is None and not args.no_stamp:
        # Derive from the Personal-Use filename: Foo-Personal-Use.zip -> Foo-Free-Trial-Demo.zip
        stem = args.personal.name
        if stem.endswith("-Personal-Use.zip"):
            demo_path = args.personal.with_name(stem[: -len("-Personal-Use.zip")] + "-Free-Trial-Demo.zip")
        else:
            demo_path = args.personal.with_name(args.personal.stem + "-Free-Trial-Demo.zip")

    like_note = None
    like_note_name = NOTE_NAME
    if args.like_note is not None:
        like_path = args.like_note.resolve()
        if not like_path.is_file():
            raise SystemExit(f"archive note not found: {like_path}")
        like_note = like_path.read_bytes()

    demo_note = None
    if args.demo_readme is not None:
        demo_path_note = args.demo_readme.resolve()
        if not demo_path_note.is_file():
            raise SystemExit(f"archive note not found: {demo_path_note}")
        demo_note = demo_path_note.read_bytes()

    args.commercial.parent.mkdir(parents=True, exist_ok=True)
    args.personal.parent.mkdir(parents=True, exist_ok=True)
    if demo_path is not None:
        demo_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_commercial = Path(
        tempfile.mkstemp(prefix=f".{args.commercial.name}.", dir=args.commercial.parent, suffix=".tmp")[1]
    )
    tmp_personal = Path(
        tempfile.mkstemp(prefix=f".{args.personal.name}.", dir=args.personal.parent, suffix=".tmp")[1]
    )
    tmp_demo: Path | None = None
    if demo_path is not None:
        tmp_demo = Path(
            tempfile.mkstemp(prefix=f".{demo_path.name}.", dir=demo_path.parent, suffix=".tmp")[1]
        )

    stamp_tmp: tempfile.TemporaryDirectory | None = None
    try:
        # Commercial and Personal carry the same clean font binaries; only the
        # Personal archive may add the like-request note.
        _write_archive(tmp_commercial, files, package_dir.name, note=None)
        _write_archive(tmp_personal, files, package_dir.name, note=like_note, note_name=like_note_name)
        os.replace(tmp_commercial, args.commercial)
        os.replace(tmp_personal, args.personal)

        if demo_path is not None and tmp_demo is not None:
            stamp_tmp = tempfile.TemporaryDirectory(prefix="font-demo-stamp-")
            stamped_root = _stamp_into(package_dir, Path(stamp_tmp.name))
            demo_files = sorted(p for p in stamped_root.iterdir() if p.is_file())
            if not demo_files:
                raise SystemExit("stamp produced no font binaries")
            _write_archive(tmp_demo, demo_files, stamped_root.name, note=demo_note, note_name="README.txt")
            os.replace(tmp_demo, demo_path)
            tmp_demo = None
    finally:
        tmp_commercial.unlink(missing_ok=True)
        tmp_personal.unlink(missing_ok=True)
        if tmp_demo is not None:
            tmp_demo.unlink(missing_ok=True)
        if stamp_tmp is not None:
            stamp_tmp.cleanup()

    with zipfile.ZipFile(args.commercial) as zc, zipfile.ZipFile(args.personal) as zp:
        font_names = sorted(n for n in zc.namelist() if n.endswith(tuple(FONT_SUFFIXES)))
        personal_names = sorted(n for n in zp.namelist() if n.endswith(tuple(FONT_SUFFIXES)))
        if font_names != personal_names:
            raise SystemExit(
                "font payload differs between archives: "
                f"{font_names} vs {personal_names}"
            )
        identical = all(zc.read(name) == zp.read(name) for name in font_names)
        note_names = [n for n in zp.namelist() if n == like_note_name]

    if not identical:
        raise SystemExit(
            "personal archive fonts differ from commercial (personal must be clean)"
        )
    print("[PASS] commercial and personal archives carry identical clean fonts")

    if like_note is not None:
        if not note_names:
            raise SystemExit(f"personal archive is missing {like_note_name}")
        print(f"[PASS] personal archive also carries {like_note_name} at archive root")

    if demo_path is not None:
        with zipfile.ZipFile(args.commercial) as zc, zipfile.ZipFile(demo_path) as zd:
            commercial_fonts = {
                n: zc.read(n) for n in zc.namelist() if n.endswith(tuple(FONT_SUFFIXES))
            }
            demo_fonts = {
                n: zd.read(n) for n in zd.namelist() if n.endswith(tuple(FONT_SUFFIXES))
            }
            if sorted(demo_fonts) != sorted(commercial_fonts):
                raise SystemExit(
                    "font payload differs between commercial and free-trial-demo: "
                    f"{sorted(commercial_fonts)} vs {sorted(demo_fonts)}"
                )
            if all(demo_fonts[n] == commercial_fonts[n] for n in commercial_fonts):
                raise SystemExit(
                    "free-trial-demo archive is not stamped (font binaries identical to commercial)"
                )
            if demo_note is not None and "README.txt" not in zd.namelist():
                raise SystemExit("free-trial-demo archive is missing README.txt")
        print("[PASS] free-trial-demo archive: stamped (digits+punct watermark)")
        if demo_note is not None:
            print("[PASS] free-trial-demo archive also carries README.txt at archive root")

    print(f"[PASS] packaged {len(files)} font binaries")
    print(f"[PASS] commercial archive: {args.commercial.resolve()}")
    print(f"[PASS] personal archive: {args.personal.resolve()}")
    if demo_path is not None:
        print(f"[PASS] free-trial-demo archive: {demo_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
