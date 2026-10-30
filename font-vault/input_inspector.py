#!/usr/bin/env python3
"""Input Inspector: verify staged font families under font-factory/input.

Font Vault's "Mark used family" copies fonts into numbered folders under
font-factory/input/. This app lists those folders (one row per font inside the
selected folder) so stray fonts in a family can be spotted. Each row can send
its font back to the folder it was copied from, or delete it.

Verdicts live in each folder's rights-verdicts.json, written by /font-rights-check
(bin/font_rights.py): red = still sold by an active holder, amber = no holder and
no licence found (unlicensed, not safe), green = a verified grant. Rows pick them
up when you press Refresh; this app never decides a verdict, it only voids one
when the font it describes is deleted or returned. The rights-chip dialog also
displays the researcher's sourced author, age and distribution history.
"""

from __future__ import annotations

import filecmp
import hashlib
import html
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import QRect, Qt, QTimer, Signal
from PySide6.QtGui import QFontMetrics, QPixmap
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QScrollArea, QSplitter,
    QVBoxLayout, QWidget,
)


ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "font-factory" / "input"
SAVED_DIR = ROOT / "font-factory" / "Saved"
CACHE_DIR = Path(__file__).resolve().parent / "data" / "cache" / "inspector"
DELETED_LOG = INPUT_DIR / "deleted-fonts.md"
# A whole family folder goes here rather than being unlinked: input/ is gitignored, so
# after a mark-used pass pulled its sources out of the dump this may be the only copy.
TRASH_DIR = INPUT_DIR / ".trash"
ARCHIVE_STATE = ".inspector-archive.json"
FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}

sys.path.insert(0, str(ROOT / "bin"))
from font_rights import SIDECAR, load_sidecar, now as utc_stamp, save as save_sidecar  # noqa: E402

DELETED_LOG_HEADER = """# Deleted fonts — not part of the family

Fonts listed here were deleted from staged folders under `font-factory/input/`
with the Input Inspector because the seller judged them **not to belong to the
family**. Never restore, re-copy, or reintroduce these files into an input
folder, a font package, or any pipeline step.

## Entries

"""

SPECIMEN_LINES = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "abcdefghijklmnopqrstuvwxyz",
    "0123456789   ! ? . , : ; / & @ # % + - = ( ) [ ] { } \" ' < > | _ $ * ~ ^",
)

STRIP_W = 1500
MAX_LINE_PX = 64

LOCK_GLYPH = "⚞"  # padlock, two octets: present in DejaVu/Noto/FreeSans, absent from Unicode pictographs


def fstype_locked(value: object) -> bool:
    """True when OS/2.fsType sets a licence-restricting bit (1, 2 or 4).

    fsType is a bitmask, so the common compound values (5, 6, 7) restrict too —
    only 0 (installable) and a lone 8 (no subsetting) do not.
    """
    return isinstance(value, int) and (value & 0b111) != 0


def folder_has_font_files(folder: Path) -> bool:
    """Whether a staged folder has a supported font file (keep unreadable folders visible)."""
    try:
        return any(
            path.is_file() and path.suffix.lower() in FONT_EXTENSIONS
            for path in folder.iterdir()
        )
    except OSError:
        return True


def trash_target(folder: Path) -> Path:
    """Return an unused, collision-safe path under input/.trash/."""
    target = TRASH_DIR / folder.name
    suffix = 2
    while target.exists():
        target = TRASH_DIR / f"{folder.name}__{suffix}"
        suffix += 1
    return target


def move_folder_to_trash(folder: Path) -> Path:
    """Move a family folder into the reversible input/.trash/ area."""
    TRASH_DIR.mkdir(parents=True, exist_ok=True)
    target = trash_target(folder)
    shutil.move(str(folder), str(target))
    return target


def move_empty_family_to_trash(folder: Path) -> Path | None:
    """Hide a family after its last font leaves, retaining its sidecars in trash."""
    if not folder.is_dir():
        return None
    if any(
        path.is_file() and path.suffix.lower() in FONT_EXTENSIONS
        for path in folder.iterdir()
    ):
        return None
    return move_folder_to_trash(folder)


def read_archive_state(folder: Path) -> tuple[bool, set[str]]:
    """Read this family's soft-archive markers; missing state means everything is active."""
    path = folder / ARCHIVE_STATE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, set()
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    family = data.get("family", False)
    if not isinstance(family, bool):
        raise ValueError(f"{path.name} has an invalid family value")
    names = data.get("fonts", [])
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise ValueError(f"{path.name} has an invalid fonts list")
    return family, set(names)


def write_archive_state(folder: Path, family_archived: bool, archived_fonts: set[str]) -> None:
    """Persist the soft-archive state atomically inside its family folder."""
    path = folder / ARCHIVE_STATE
    names = sorted(archived_fonts, key=natural_key)
    if not family_archived and not names:
        path.unlink(missing_ok=True)
        return
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps({"family": family_archived, "fonts": names}, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def visible_fonts(folder: Path, view: str) -> tuple[list[Path], str | None]:
    """Return the family's fonts for the Active or Archive view."""
    try:
        paths = [
            path for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in FONT_EXTENSIONS
        ]
        family_archived, archived = read_archive_state(folder)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        paths = font_paths(folder)
        return (paths if view == "active" else []), str(error)
    paths.sort(key=lambda path: natural_key(path.stem))
    if view == "archive":
        return (paths if family_archived else [p for p in paths if p.name in archived]), None
    return ([] if family_archived else [p for p in paths if p.name not in archived]), None


def font_paths(folder: Path) -> list[Path]:
    """List supported font files in a folder, sorted by filename."""
    try:
        paths = [
            path for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in FONT_EXTENSIONS
        ]
    except OSError:
        return []
    paths.sort(key=lambda path: natural_key(path.stem))
    return paths


def saved_target(folder: Path) -> Path:
    """Return an unused destination that preserves the family folder in Saved/."""
    target = SAVED_DIR / folder.name
    suffix = 2
    while target.exists():
        target = SAVED_DIR / f"{folder.name}__{suffix}"
        suffix += 1
    return target


def prune_archived_font(folder: Path, filename: str) -> None:
    """Remove a departed font's archive marker so a later same-name file is active."""
    try:
        family_archived, archived = read_archive_state(folder)
        archived.discard(filename)
        write_archive_state(folder, family_archived, archived)
    except (OSError, json.JSONDecodeError, ValueError):
        pass


VERDICT_OBJECT = {
    "claimed": "verdictClaimed",
    "orphan": "verdictOrphan",
    "clear": "verdictClear",
}
VERDICT_RISK = {
    "claimed": "RED — still sold by an active rights holder; shipping this is infringement exposure.",
    "orphan": "AMBER — unlicensed, no active holder found; NOT safe to ship.",
    "clear": "GREEN — free/commercial grant verified in the binary, or permission confirmed with the author.",
}
NO_VERDICT_TIP = "No rights verdict yet — queued for /font-rights-check."
VERDICT_HEX = {"claimed": "#c0392b", "orphan": "#d5a85e", "clear": "#5da36e"}
# A stylesheet's colour wins over the palette for anchors, so the link colour is
# set inline — the palette route renders Qt's own blue no matter what you put in it.
LINK_HEX = "#7fb3d5"
# evidence_kind as the tool stores it, spelled out for a human reading the dialog.
EVIDENCE_KIND_LABEL = {
    "seller": "marketplace",
    "distribution": "font distribution page",
    "holder": "holder's own site",
    "reference": "rights reference",
    "mirror": "scraper mirror",
    "unknown": "unclassified",
}
# link_check is what the tool observed on the network, not what the agent believed.
LINK_CHECK_LABEL = {
    "verified": "the tool loaded at least one of these",
    "blocked-only": "none of these could be loaded — the server refused or blocked it",
    "skipped": "not checked against the network this run",
    "": "the tool recorded no link check for this verdict",
}
RESEARCH_SOURCE_LABEL = {
    "free_distribution": "free-font distribution listing",
    "commercial_listing": "commercial listing",
    "author": "author source",
    "reference": "rights or history reference",
    "archive": "archived page",
    "other": "research source",
}
UNRESEARCHED_REPORT = (
    "Nobody has judged this font yet. Run /font-rights-check and it will land here "
    "as red, amber or green."
)


class Section(NamedTuple):
    """One block of the verdict dialog.

    ``lines`` is the plain text the copied report carries, and the widget renders from
    the same list, so a field can never show up on screen without also going out in the
    report — the whole point of which is that you can take the record away with you.
    """

    title: str
    lines: tuple[str, ...]
    note: str = ""
    urls: tuple[str, ...] = ()
    kinds: tuple[str, ...] = ()
    quote: bool = False


def evidence_urls(verdict: dict | None) -> list[str]:
    """Every URL the record carries, including provenance pages."""
    urls = [str(item) for item in (verdict or {}).get("evidence") or [] if str(item).strip()]
    contact = str((verdict or {}).get("author_contact") or "")
    if contact.lower().startswith(("http://", "https://")) and contact not in urls:
        urls.append(contact)
    research = (verdict or {}).get("research") or {}
    sources = research.get("sources", []) if isinstance(research, dict) else []
    if isinstance(sources, list):
        for source in sources:
            url = str(source.get("url") or "") if isinstance(source, dict) else ""
            if url and url not in urls:
                urls.append(url)
    return urls


def verdict_facts(verdict: dict) -> list[tuple[str, str]]:
    """The identity row-pairs: the grid's labels and values, in the order shown."""
    derived = verdict.get("derived_from")
    fstype = verdict.get("fstype")
    rows = [
        ("Claimed holder", str(verdict.get("maker") or "(none named in the file)")),
        ("Verdict is from", "this binary" if not derived
                            else f"its folder's own pass: {derived}"),
        ("Confidence", str(verdict.get("confidence") or "medium")),
        ("Checked (UTC)", str(verdict.get("checked_utc") or "unknown")),
        ("fsType", f"{fstype} — the binary itself restricts printing, embedding or editing"
                   if fstype_locked(fstype) else f"{fstype} — no licence-restricting bit set"),
    ]
    contact = str(verdict.get("author_contact") or "")
    if contact and not contact.lower().startswith(("http://", "https://")):
        rows.append(("Author contacted", contact))
    return rows


def verdict_sections(verdict: dict) -> list[Section]:
    """The read-the-prose blocks, in the order the dialog stacks them."""
    sections: list[Section] = []
    evidence = [str(item) for item in verdict.get("evidence") or [] if str(item).strip()]
    if evidence:
        kinds = [str(item) for item in verdict.get("evidence_kind") or []]
        lines = []
        for index, url in enumerate(evidence):
            # An unrecognised kind is spelled out as stored rather than dropped: the report
            # is the record you follow up elsewhere, so it must not lose a category.
            kind = kinds[index] if index < len(kinds) else ""
            lines.append(f"· {url}" + (f"  ({EVIDENCE_KIND_LABEL.get(kind) or kind})" if kind else ""))
        sections.append(Section(
            "Evidence — pages that carry the claim",
            tuple(lines),
            note=LINK_CHECK_LABEL.get(str(verdict.get("link_check") or ""), LINK_CHECK_LABEL[""]),
            urls=tuple(evidence),
            kinds=tuple(kinds),
        ))
    quote = str(verdict.get("grant_quote") or "")
    if quote:
        sections.append(Section("Grant quoted from this binary", (f"“{quote}”",), quote=True))
    contact = str(verdict.get("author_contact") or "")
    if contact.lower().startswith(("http://", "https://")):
        sections.append(Section(
            "Author reached this run",
            (f"· {contact}",),
            note=LINK_CHECK_LABEL["verified"],
            urls=(contact,),
        ))
    research = verdict.get("research") or {}
    if isinstance(research, dict) and research:
        context_lines = []
        for field, label in (
            ("author", "Author named in research"),
            ("author_status", "Author status"),
            ("first_known_date", "Earliest date found"),
            ("age_estimate", "Estimated age"),
            ("age_basis", "Age basis"),
            ("distribution_assessment", "Observed distribution or licence claims"),
            ("abandonware_assessment", "Abandonware assessment (not permission)"),
            ("abandonware_basis", "Abandonware basis"),
        ):
            value = str(research.get(field) or "").strip()
            if value:
                context_lines.append(f"{label}: {value}")
        if context_lines:
            sections.append(Section(
                "Font history and distribution research",
                tuple(context_lines),
                note="These are sourced research findings. A free download or an abandonware label does not grant a licence.",
            ))
        sources = research.get("sources") or []
        if isinstance(sources, list):
            for source in sources:
                if not isinstance(source, dict) or not source.get("url"):
                    continue
                site = str(source.get("site") or "Research source")
                source_type = str(source.get("source_type") or "other")
                details = []
                for field, label in (
                    ("match", "Match"),
                    ("availability", "Availability"),
                    ("distribution_label", "Page's licence label"),
                    ("uploader", "Uploader / credited source"),
                    ("date", "Date shown"),
                    ("note", "Finding"),
                ):
                    value = str(source.get(field) or "").strip()
                    if value:
                        details.append(f"{label}: {value}")
                url = str(source["url"])
                sections.append(Section(
                    f"Source — {site}",
                    (f"· {url}",),
                    note=" · ".join(details) or "No additional page details recorded.",
                    urls=(url,),
                    kinds=(RESEARCH_SOURCE_LABEL.get(source_type, source_type),),
                ))
    else:
        sections.append(Section(
            "Font history and distribution research",
            ("Not recorded for this verdict. New rights-research runs show it here.",),
        ))
    looked = [str(item) for item in verdict.get("looked") or [] if str(item).strip()]
    if looked:
        sections.append(Section("Search avenues",
                                tuple(f"· {item}" for item in looked)))
    if verdict.get("note"):
        sections.append(Section("Why this verdict", (str(verdict["note"]),)))
    history = list(verdict.get("history") or [])
    if history:
        sections.append(Section(
            f"Earlier verdicts kept ({len(history)})",
            tuple(
                f"· {row.get('state') or '?'} as of {row.get('checked_utc') or 'unknown'}"
                for row in history
            )))
    return sections


def verdict_report(filename: str, folder: str, verdict: dict | None) -> str:
    """The whole record as plain text, for pasting into a browser, an email or a note.

    What the dialog shows is built from verdict_facts() and verdict_sections(), so this
    is the same content spelled out rather than a second summary that can fall behind.
    """
    state = str((verdict or {}).get("state") or "")
    lines = [
        f"FONT RIGHTS VERDICT — {filename}",
        f"Folder: {folder}",
        # VERDICT_RISK already spells the colour out, so it goes in whole.
        VERDICT_RISK.get(state) or f"UNRESEARCHED — {NO_VERDICT_TIP}",
    ]
    if state not in VERDICT_RISK:
        lines += ["", UNRESEARCHED_REPORT]
    else:
        lines += ["", "Facts"]
        width = max(len(key) for key, _value in verdict_facts(verdict))
        lines += [f"  {key.ljust(width)}: {value}" for key, value in verdict_facts(verdict)]
        for section in verdict_sections(verdict):
            # Section titles go out exactly as the dialog spells them, so a grep for a
            # heading you can see on screen finds it in the text you copied.
            lines += ["", section.title]
            if section.note:
                lines.append(f"  {section.note}")
            lines += [f"  {line}" for line in section.lines]
    lines += [
        "",
        "—",
        f"Record: {Path(folder) / SIDECAR if folder else SIDECAR}",
        "Copied from Font Vault's Input Inspector, which only displays what "
        "/font-rights-check wrote; it decides nothing itself.",
    ]
    return "\n".join(lines) + "\n"



def natural_key(text: str) -> list:
    """Sort keys so folder names like 2-x come before 10-y."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def font_names(folder: Path) -> list[str]:
    """Exact filenames of the font files in a folder, as rights verdicts are keyed."""
    try:
        return [
            p.name for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in FONT_EXTENSIONS
        ]
    except OSError:
        return []


def cache_seed(path: Path) -> str:
    """Cache identity for a font: replacing the file must invalidate its previews."""
    try:
        stat = path.stat()
        return f"{path}:{stat.st_mtime_ns}:{stat.st_size}"
    except OSError:
        return str(path)


def renderable_path(path: Path) -> Path:
    """Convert WOFF/WOFF2 to OTF once so PIL can render it."""
    if path.suffix.lower() not in {".woff", ".woff2"}:
        return path
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    converted = CACHE_DIR / (hashlib.sha256(cache_seed(path).encode()).hexdigest()[:20] + ".otf")
    if not converted.exists():
        font = TTFont(path)
        font.flavor = None
        font.save(converted)
        font.close()
    return converted


def render_strip(path: Path) -> Path:
    """Render one combined strip (alphabet, digits, punctuation), cached on disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(cache_seed(path).encode("utf-8")).hexdigest()[:24]
    output = CACHE_DIR / f"{digest}.png"
    if output.exists():
        return output
    source = renderable_path(path)
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    max_w = STRIP_W - 56

    def fitted(line: str) -> tuple[ImageFont.FreeTypeFont, int]:
        probe = ImageFont.truetype(str(source), 100)
        probe_w = measure.textlength(line, font=probe)
        size = max(16, min(MAX_LINE_PX, int(100 * max_w / max(probe_w, 1))))
        font_obj = ImageFont.truetype(str(source), size)
        while size > 16 and measure.textlength(line, font=font_obj) > max_w:
            size -= 2
            font_obj = ImageFont.truetype(str(source), size)
        return font_obj, size

    fitted_fonts = [fitted(line) for line in SPECIMEN_LINES]
    gap = 16
    height = sum(size for _f, size in fitted_fonts) + gap * (len(SPECIMEN_LINES) - 1) + 26
    image = Image.new("RGB", (STRIP_W, height), (8, 8, 10))
    draw = ImageDraw.Draw(image)
    y = 13
    for line, (font_obj, size) in zip(SPECIMEN_LINES, fitted_fonts):
        draw.text((28, y), line, font=font_obj, fill=(245, 243, 238))
        y += size + gap
    image.save(output, format="PNG")
    return output


def find_source(folder: Path, filename: str) -> Path | None:
    """Find the original location a staged font was copied from.

    The manifest is the record; the folder-level source line only stands in for a folder
    that never got a manifest. A font the manifest does not list was not staged from
    there, and guessing a path would push a stranger file into the source dump.
    """
    manifest = folder / "font-vault-manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        for entry in data.get("files", []):
            source = entry.get("source")
            if source and Path(str(entry.get("copied_to") or "")).name == filename:
                return Path(source)
        return None
    source_dir = folder / "source-directory.txt"
    if source_dir.exists():
        try:
            for line in source_dir.read_text(encoding="utf-8").splitlines():
                if line.lower().startswith("original source directory:"):
                    base = line.split(":", 1)[1].strip()
                    if base:
                        return Path(base) / filename
        except OSError:
            pass
    return None


def prune_manifest(folder: Path, filename: str) -> None:
    """Drop a returned/deleted font from the folder's manifest."""
    manifest = folder / "font-vault-manifest.json"
    if not manifest.exists():
        return
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        files = data.get("files", [])
        kept = [entry for entry in files if Path(str(entry.get("copied_to") or "")).name != filename]
        if len(kept) == len(files):
            return
        data["files"] = kept
        manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass


def log_deletion(path: Path, source: Path | None) -> str | None:
    """Record a family-mismatch deletion in input/deleted-fonts.md.

    Returns an error message on failure, or None on success.
    """
    try:
        if not DELETED_LOG.exists():
            DELETED_LOG.write_text(DELETED_LOG_HEADER, encoding="utf-8")
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        origin = str(source) if source else "unknown (no source recorded)"
        entry = (
            f"- **{stamp}** — `{path.name}` removed from `{path.parent.name}/`\n"
            f"  - Original source: `{origin}`\n"
            f"  - Reason: does not match the family (deleted in Input Inspector)\n"
        )
        with DELETED_LOG.open("a", encoding="utf-8") as handle:
            handle.write(entry)
    except OSError as error:
        return str(error)
    return None


def load_in_use(folder: Path) -> set[str]:
    """Return the filenames marked In Use in the folder's in-use.txt."""
    target = folder / "in-use.txt"
    if not target.exists():
        return set()
    try:
        return {line.strip() for line in target.read_text(encoding="utf-8").splitlines() if line.strip()}
    except OSError:
        return set()


def set_in_use(folder: Path, filename: str, used: bool) -> None:
    """Add or remove a filename from the folder's in-use.txt (removes it when empty)."""
    marks = load_in_use(folder)
    if used:
        marks.add(filename)
    else:
        marks.discard(filename)
    target = folder / "in-use.txt"
    if marks:
        target.write_text("\n".join(sorted(marks)) + "\n", encoding="utf-8")
    else:
        target.unlink(missing_ok=True)


def verdict_counts(folder: Path) -> tuple[int, int, bool]:
    """Return (researched, total fonts, verdict file unreadable) for one staged folder."""
    payload, error = load_sidecar(folder)
    verdicts = payload.get("verdicts", {})
    names = font_names(folder)
    return sum(1 for name in names if name in verdicts), len(names), bool(error)


def chip_hint(verdict: dict | None) -> str:
    """One line for hover. The detail lives in the dialog the chip opens on click."""
    state = str((verdict or {}).get("state") or "")
    if state not in VERDICT_RISK:
        return f"{NO_VERDICT_TIP}  Click to open."
    colour = {"claimed": "RED", "orphan": "AMBER", "clear": "GREEN"}[state]
    return f"{colour} — {state}. Click for the evidence behind it."


def copy_button(text: str, payload: str) -> QPushButton:
    """A button that copies and says so for a moment, so a click is visible."""
    button = QPushButton(text)
    button.setObjectName("copy")

    def fired() -> None:
        QApplication.clipboard().setText(payload)
        button.setText("Copied ✓")
        QTimer.singleShot(1400, lambda: button.setText(text))

    button.clicked.connect(fired)
    return button


class VerdictDialog(QDialog):
    """The evidence behind one rights chip, laid out to read — and every URL clickable."""

    def __init__(self, filename: str, folder: str, verdict: dict | None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Rights verdict — {filename}")
        self.setModal(True)
        screen = (parent.window().screen() if parent else QApplication.primaryScreen()) \
            or QApplication.primaryScreen()
        available = screen.availableGeometry()
        widest = min(int(available.width() * 0.8), 1600)
        tallest = min(int(available.height() * 0.88), 1200)
        self.setMinimumSize(int(available.width() * 0.42), int(available.height() * 0.3))
        self.resize(widest, tallest)
        shell = QVBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(30, 26, 30, 22)
        layout.setSpacing(20)
        layout.addWidget(self._headline(filename, folder, verdict))
        self.report = verdict_report(filename, folder, verdict)
        if not verdict or str(verdict.get("state") or "") not in VERDICT_RISK:
            waiting = QLabel(UNRESEARCHED_REPORT)
            waiting.setWordWrap(True)
            waiting.setObjectName("muted")
            layout.addWidget(waiting)
            layout.addStretch()
        else:
            # Two columns — the identity facts on the left, everything you have to read on
            # the right. One stack across a wide dialog left the bottom half empty.
            columns = QHBoxLayout()
            columns.setSpacing(20)
            left = QVBoxLayout()
            left.setSpacing(20)
            left.addWidget(self._facts(verdict))
            left.addStretch()
            right = QVBoxLayout()
            right.setSpacing(20)
            for section in verdict_sections(verdict):
                right.addWidget(self._panel(section))
            right.addStretch()
            columns.addLayout(left, 2)
            columns.addLayout(right, 3)
            layout.addLayout(columns)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        shell.addWidget(scroll, 1)
        footer = QFrame()
        footer.setObjectName("dialogFooter")
        bar = QHBoxLayout(footer)
        bar.setContentsMargins(30, 16, 30, 20)
        # The report goes out first and always: an amber verdict has no links to copy, but
        # the searched avenues and the note are exactly what you need to follow up yourself.
        bar.addWidget(copy_button("Copy full report", self.report))
        urls = evidence_urls(verdict)
        if urls:
            bar.addWidget(copy_button("Copy all links", "\n".join(urls)))
        bar.addStretch()
        close = QPushButton("Close")
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        bar.addWidget(close)
        shell.addWidget(footer)

        # Take the height the content actually needs at this width; a verdict with two
        # links should not open a screenful of empty panel below itself. The laid-out
        # geometry is the only honest number — wrapped labels under-report their height
        # to sizeHint, and a scroll area happily leaves the difference as dead space.
        shell.activate()
        # Measure at the width the body will really have, by laying it out in a box that
        # is wide but generously tall: asking the scroll area instead reports its startup
        # size while the dialog is still hidden, and text wrapped into that is far taller
        # than the verdict really is — which bakes in the dead space this removes.
        body.layout().setGeometry(QRect(0, 0, self.width() - 60, 4000))
        content_bottom = max((widget.geometry().bottom() for widget in body.children()
                              if isinstance(widget, QWidget)), default=0)
        if content_bottom > 0:
            wanted = content_bottom + 30 + footer.sizeHint().height()
            self.resize(self.width(), max(self.minimumHeight(), min(tallest, wanted)))

    @staticmethod
    def _headline(filename: str, folder: str, verdict: dict | None) -> QFrame:
        state = str((verdict or {}).get("state") or "")
        head = QFrame()
        head.setObjectName("dialogHead")
        box = QVBoxLayout(head)
        box.setContentsMargins(28, 22, 28, 22)
        box.setSpacing(8)
        colour = {"claimed": "● RED", "orphan": "● AMBER", "clear": "● GREEN"}.get(state, "● UNRESEARCHED")
        title = QLabel(f"{colour}   {filename}")
        title.setObjectName("dialogTitle")
        if state:
            title.setStyleSheet(f"color: {VERDICT_HEX[state]};")
        box.addWidget(title)
        where = QLabel(f"{folder}  ·  {VERDICT_RISK.get(state, NO_VERDICT_TIP)}")
        where.setWordWrap(True)
        where.setObjectName("dialogRisk")
        box.addWidget(where)
        return head

    @classmethod
    def _facts(cls, verdict: dict) -> QFrame:
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        # Without this the wide dialog hands half the row to the label column, so the
        # right-aligned keys drift out of the empty space instead of hugging their values.
        grid.setColumnStretch(1, 1)
        for index, (key, value) in enumerate(verdict_facts(verdict)):
            label = QLabel(key)
            label.setObjectName("muted")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            field = QLabel(value)
            field.setWordWrap(True)
            field.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(label, index, 0)
            grid.addWidget(field, index, 1)
        box = QFrame()
        box.setObjectName("dialogSection")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.addLayout(grid)
        return box

    @staticmethod
    def _panel(section: Section) -> QFrame:
        """One Section, rendered — clickable URLs when it has them, prose when not."""
        box = QFrame()
        box.setObjectName("dialogSection")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)
        heading = QLabel(section.title)
        heading.setObjectName("sectionHead")
        layout.addWidget(heading)
        if section.note:
            note = QLabel(section.note)
            note.setObjectName("muted")
            note.setWordWrap(True)
            layout.addWidget(note)
        if not section.urls:
            body = QLabel("\n".join(section.lines))
            body.setWordWrap(True)
            body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if section.quote:
                body.setObjectName("quoted")
            layout.addWidget(body)
            return box
        for index, url in enumerate(section.urls):
            row = QHBoxLayout()
            row.setSpacing(8)
            kind = section.kinds[index] if index < len(section.kinds) else ""
            link = QLabel(
                f'<a href="{html.escape(url, quote=True)}" '
                f'style="color:{LINK_HEX};">{html.escape(url)}</a>')
            link.setOpenExternalLinks(True)
            link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            link.setWordWrap(True)
            link.setObjectName("url")
            row.addWidget(link, 1)
            if kind:
                tag = QLabel(EVIDENCE_KIND_LABEL.get(kind) or kind)
                tag.setObjectName("muted")
                row.addWidget(tag)
            row.addWidget(copy_button("Copy", url))
            layout.addLayout(row)
        return box



def prune_verdict(folder: Path, filename: str) -> None:
    """Void a font's rights verdict when the file itself leaves the folder.

    A verdict is a claim about one specific binary; keeping it after a delete or
    a return would let a later copy under the same name inherit the old answer.
    """
    payload, error = load_sidecar(folder)
    if error or filename not in payload.get("verdicts", {}):
        return
    payload["verdicts"].pop(filename)
    payload["updated_utc"] = utc_stamp()
    try:
        save_sidecar(folder, payload)
    except OSError:
        pass


class VerdictChip(QLabel):
    """The coloured rights dot. It opens the evidence dialog instead of hoarding it in a tooltip."""

    clicked = Signal()

    def __init__(self, text: str, object_name: str, tooltip: str) -> None:
        super().__init__(text)
        self.setObjectName(object_name)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class FontRow(QFrame):
    """One staged font: name + archive/mark/return/delete buttons and its preview strip."""

    activated = Signal()
    verdict_clicked = Signal()

    def __init__(
        self,
        path: Path,
        verdict: dict | None = None,
        archived: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.path = path
        self.verdict = verdict
        self._pix: QPixmap | None = None
        self.setObjectName("fontRow")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 9, 12, 9)
        outer.setSpacing(6)

        head = QHBoxLayout()
        head.setSpacing(8)
        name = QLabel(path.stem)
        fm = QFontMetrics(name.font())
        name.setText(fm.elidedText(path.stem, Qt.TextElideMode.ElideMiddle, 560))
        name.setToolTip(str(path))
        name.setObjectName("rowName")
        head.addWidget(name)
        head.addStretch()
        self.verdict_chip = VerdictChip(
            f"{LOCK_GLYPH}●" if fstype_locked((verdict or {}).get("fstype")) else "●",
            VERDICT_OBJECT.get(str((verdict or {}).get("state") or ""), "verdictNone"),
            f"{path.name}\n{chip_hint(verdict)}",
        )
        self.verdict_chip.clicked.connect(self.verdict_clicked.emit)
        head.addWidget(self.verdict_chip)
        self.use_btn = QPushButton("In Use")
        self.use_btn.setCheckable(True)
        self.use_btn.setObjectName("useToggle")
        self.use_btn.setToolTip("Mark this font as In Use (stored in the folder's in-use.txt).")
        self.use_btn.setChecked(path.name in load_in_use(path.parent))
        head.addWidget(self.use_btn)
        self.archive_btn = QPushButton("Restore" if archived else "Archive")
        self.archive_btn.setObjectName("primary" if archived else "")
        self.archive_btn.setToolTip(
            "Return this font to the active list." if archived
            else "Hide this font from the active list; find it in Archive."
        )
        head.addWidget(self.archive_btn)
        self.return_btn = QPushButton("↩ Return to source")
        self.return_btn.setToolTip(
            "Send this font back to the folder it was copied from.\n"
            "If the original is still there, the staged copy is simply removed."
        )
        self.delete_btn = QPushButton("✕ Delete")
        self.delete_btn.setObjectName("danger")
        self.delete_btn.setToolTip("Permanently delete this font file from this folder.")
        head.addWidget(self.return_btn)
        head.addWidget(self.delete_btn)
        outer.addLayout(head)

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.preview.setMinimumHeight(80)
        outer.addWidget(self.preview)
        self.load_preview()

    def mousePressEvent(self, event) -> None:
        self.activated.emit()
        super().mousePressEvent(event)

    def load_preview(self) -> None:
        try:
            image_path = render_strip(self.path)
            pix = QPixmap(str(image_path))
            if pix.isNull():
                raise RuntimeError("preview image could not be opened")
            self._pix = pix
            self.preview.setStyleSheet("")
            self.preview.setText("")
        except Exception as error:
            self._pix = None
            self.preview.setText(f"Preview failed: {error}")
            self.preview.setStyleSheet("color: #e0917f; padding: 4px; font-size: 12px;")
            return
        self._fit()

    def _fit(self) -> None:
        if self._pix is None or self._pix.isNull():
            return
        width = min(self.preview.width(), STRIP_W)
        if width < 20:
            return
        scaled = self._pix.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)
        self.preview.setPixmap(scaled)
        self.preview.setMinimumHeight(scaled.height())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit()


class InspectorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Input Inspector — family check")
        self.resize(1360, 860)
        self.setMinimumSize(1040, 700)
        self.setStyleSheet(self.styles())
        self.folders: list[Path] = []
        self.rows: list[FontRow] = []
        self.active_row: FontRow | None = None
        self.current_idx = -1
        self.view_mode = "active"
        self.build_ui()
        self.folder_list.currentRowChanged.connect(self.folder_selected)
        self.view_combo.currentIndexChanged.connect(self.view_changed)
        self._refresh_folders()
        if self.folders:
            self.load_folder(0)
        else:
            self.status.setText(f"No family folders found under {INPUT_DIR}")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)

    @staticmethod
    def styles() -> str:
        return """
        QWidget { background: #111315; color: #eeeae2; font-size: 13px; }
        QLabel { background: transparent; }
        QFrame#panel { background: #191c1f; border-radius: 10px; }
        QFrame#fontRow { background: #191c1f; border-radius: 8px; }
        QFrame#fontRow:hover { background: #1e2226; }
        QLabel#title { color: #f3f0e8; font-size: 21px; font-weight: 700; letter-spacing: 2px; }
        QLabel#folderTitle { color: #d5a85e; font-size: 17px; font-weight: 700; }
        QLabel#rowName { color: #dedbd3; font-size: 13px; font-weight: 600; }
        QLabel#muted, QLabel#status { color: #9ca5a8; }
        QLabel#verdictWarn { color: #e0917f; font-weight: 600; }
        QLabel#verdictClaimed { color: #c0392b; font-size: 15px; }
        QLabel#verdictOrphan { color: #d5a85e; font-size: 15px; }
        QLabel#verdictClear { color: #5da36e; font-size: 15px; }
        QLabel#verdictNone { color: #525b60; font-size: 15px; }
        QListWidget { background: #191c1f; border: 0; color: #dedbd3; outline: 0; }
        QListWidget::item { padding: 8px 7px; border-radius: 5px; }
        QListWidget::item:selected { background: #6f5839; color: #fff9ef; }
        QPushButton { background: #2a2f33; color: #eeeae2; border: 0; border-radius: 6px; padding: 8px 12px; }
        QPushButton:hover { background: #394148; }
        QPushButton:disabled { color: #6a7174; background: #21252a; }
        QPushButton#primary { background: #d5a85e; color: #141414; font-weight: 700; }
        QPushButton#primary:hover { background: #efc777; }
        QComboBox { background: #2a2f33; color: #eeeae2; border: 0; border-radius: 6px; padding: 7px 10px; min-width: 92px; }
        QComboBox::drop-down { border: 0; }
        QComboBox QAbstractItemView { background: #191c1f; selection-background-color: #6f5839; }
        QPushButton#useToggle:checked { background: #d5a85e; color: #141414; font-weight: 700; }
        QPushButton#useToggle:checked:hover { background: #efc777; }
        QPushButton#danger { background: #3a2622; color: #e6b0a3; }
        QPushButton#danger:hover { background: #55352f; }
        QScrollArea { border: 0; background: transparent; }
        QScrollBar:vertical { background: #14171a; width: 11px; border-radius: 5px; }
        QScrollBar::handle:vertical { background: #3a4246; border-radius: 5px; min-height: 30px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QDialog { background: #14171a; font-size: 17px; }
        QDialog QLabel#muted { color: #a9b1b4; font-size: 15px; }
        QFrame#dialogHead { background: #1c2024; border-bottom: 1px solid #2a2f33; }
        QLabel#dialogTitle { font-size: 28px; font-weight: 700; letter-spacing: 0.5px; }
        QLabel#dialogRisk { color: #d6d0c6; font-size: 18px; }
        QFrame#dialogSection { background: #1c2024; border: 1px solid #2a3036; border-radius: 8px; }
        QLabel#sectionHead { color: #d5a85e; font-size: 16px; font-weight: 700; letter-spacing: 1px; }
        QLabel#url { font-size: 18px; }
        QLabel#quoted { color: #c3cec7; font-style: italic; font-size: 18px; }
        QFrame#dialogFooter { background: #191c1f; border-top: 1px solid #2a2f33; }
        QPushButton#copy { background: #2a2f33; font-size: 14px; padding: 8px 14px; }
        QPushButton#copy:hover { background: #454f57; }
        """

    def button(self, text: str, slot, primary: bool = False) -> QPushButton:
        button = QPushButton(text)
        if primary:
            button.setObjectName("primary")
        button.clicked.connect(slot)
        return button

    def build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(18, 18, 18, 14)
        outer.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("INPUT INSPECTOR")
        title.setObjectName("title")
        header.addWidget(title)
        self.folder_title = QLabel("No folder selected")
        self.folder_title.setObjectName("folderTitle")
        header.addWidget(self.folder_title)
        header.addStretch()
        self.count_label = QLabel("")
        self.count_label.setObjectName("muted")
        header.addWidget(self.count_label)
        self.verdict_warn = QLabel("")
        self.verdict_warn.setObjectName("verdictWarn")
        header.addWidget(self.verdict_warn)
        outer.addLayout(header)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addStretch()
        view_label = QLabel("View")
        view_label.setObjectName("muted")
        toolbar.addWidget(view_label)
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Active", "Archive"])
        self.view_combo.setToolTip("Switch between active fonts and archived fonts.")
        toolbar.addWidget(self.view_combo)
        self.archive_family_btn = self.button("Archive family", self.toggle_family_archive)
        self.archive_family_btn.setEnabled(False)
        toolbar.addWidget(self.archive_family_btn)
        self.save_family_btn = self.button("Save", self.save_family, primary=True)
        self.save_family_btn.setEnabled(False)
        self.save_family_btn.setToolTip(
            "Move this family folder and its fonts out of input/ into font-factory/Saved/."
        )
        toolbar.addWidget(self.save_family_btn)
        self.delete_folder_btn = self.button("✕ Delete family folder", self.delete_folder)
        self.delete_folder_btn.setObjectName("danger")
        self.delete_folder_btn.setEnabled(False)
        self.delete_folder_btn.setToolTip(
            "Move the selected folder and everything inside it to font-factory/input/.trash/.\n"
            "Nothing is unlinked — empty the trash folder yourself when you are sure."
        )
        toolbar.addWidget(self.delete_folder_btn)
        self.refresh_btn = self.button("↻ Refresh", self.refresh_action)
        self.refresh_btn.setToolTip(
            "Re-read the folders under font-factory/input/ and each folder's rights-verdicts.json.\n"
            "Verdicts written by /font-rights-check land here."
        )
        toolbar.addWidget(self.refresh_btn)
        outer.addLayout(toolbar)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        side = QFrame()
        side.setObjectName("panel")
        side.setMinimumWidth(220)
        side.setMaximumWidth(300)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(14, 14, 14, 14)
        side_layout.setSpacing(8)
        label = QLabel("FAMILY FOLDERS — ACTIVE")
        label.setObjectName("muted")
        self.family_list_label = label
        side_layout.addWidget(label)
        self.folder_list = QListWidget()
        side_layout.addWidget(self.folder_list, 1)
        legend_title = QLabel("RIGHTS VERDICT")
        legend_title.setObjectName("muted")
        side_layout.addWidget(legend_title)
        for state, meaning in (
            ("claimed", "sold by an owner"),
            ("orphan", "no holder, no licence"),
            ("clear", "grant verified"),
            ("", "not researched"),
        ):
            entry = QLabel(f"●  {meaning}")
            entry.setObjectName(VERDICT_OBJECT.get(state, "verdictNone"))
            side_layout.addWidget(entry)
        hint = QLabel("One preview row per font in\nthe selected folder.\n\nClick a ● to open the evidence\nbehind that verdict — the links\nare clickable and copyable.\n\n↩ Return sends a stray font\nback where it came from.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        side_layout.addWidget(hint)

        main = QFrame()
        main.setObjectName("panel")
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(12, 12, 12, 12)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.rows_host = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_host)
        self.rows_layout.setContentsMargins(6, 6, 6, 6)
        self.rows_layout.setSpacing(10)
        self.scroll.setWidget(self.rows_host)
        main_layout.addWidget(self.scroll)

        split.addWidget(side)
        split.addWidget(main)
        split.setSizes([260, 1100])
        outer.addWidget(split, 1)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        self.status = QLabel("Choose a family folder to inspect.")
        self.status.setObjectName("status")
        footer.addWidget(self.status, 1)
        self.prev_btn = self.button("◀ Previous", self.go_prev)
        self.next_btn = self.button("Next ▶", self.go_next, primary=True)
        unmarked_btn = self.button("Next not In Use →", self.next_unmarked)
        unmarked_btn.setToolTip("Jump to the next font in this folder without the In Use toggle.")
        unchecked_btn = self.button("Next no verdict →", self.next_unchecked)
        unchecked_btn.setToolTip(
            "Jump to the next font in this folder with no rights verdict yet — the /font-rights-check queue."
        )
        for control in (self.prev_btn, unmarked_btn, unchecked_btn, self.next_btn):
            footer.addWidget(control)
        outer.addLayout(footer)

    def _refresh_folders(self, select: int | None = None) -> None:
        if INPUT_DIR.is_dir():
            folders = []
            for folder in INPUT_DIR.iterdir():
                if not folder.is_dir() or folder.name.startswith(".") or not folder_has_font_files(folder):
                    continue
                shown, _archive_error = visible_fonts(folder, self.view_mode)
                if shown:
                    folders.append(folder)
            folders.sort(key=lambda p: natural_key(p.name))
        else:
            folders = []
        self.folders = folders
        self.folder_list.blockSignals(True)
        self.folder_list.clear()
        for folder in folders:
            shown, _archive_error = visible_fonts(folder, self.view_mode)
            payload, unreadable = load_sidecar(folder)
            verdicts = payload.get("verdicts", {})
            researched = sum(1 for path in shown if path.name in verdicts)
            checked = "?" if unreadable else str(researched)
            item = QListWidgetItem(f"{folder.name}  ·  {len(shown)} font(s)  ·  {checked}/{len(shown)} researched")
            item.setToolTip(folder.name)
            item.setData(Qt.ItemDataRole.UserRole, str(folder))
            self.folder_list.addItem(item)
        if select is not None and folders:
            self.folder_list.setCurrentRow(min(max(select, 0), len(folders) - 1))
        self.folder_list.blockSignals(False)
        if not folders:
            self.archive_family_btn.setEnabled(False)
            self.save_family_btn.setEnabled(False)
            self.delete_folder_btn.setEnabled(False)

    def view_changed(self, index: int) -> None:
        self.view_mode = "archive" if index == 1 else "active"
        self.family_list_label.setText(
            "FAMILY FOLDERS — ARCHIVE" if self.view_mode == "archive" else "FAMILY FOLDERS — ACTIVE"
        )
        previous = max(self.current_idx, 0)
        self.current_idx = -1
        self._refresh_folders(select=previous)
        if self.folders:
            self.load_folder(min(previous, len(self.folders) - 1))
            self.status.setText(f"Showing {self.view_mode} families — {len(self.folders)} folder(s).")
        else:
            self._clear_rows()
            self.folder_title.setText("No folder selected")
            self.count_label.setText("")
            self.verdict_warn.setText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.status.setText(f"No {self.view_mode} font families found under {INPUT_DIR}.")

    def folder_selected(self, row: int) -> None:
        if 0 <= row < len(self.folders) and row != self.current_idx:
            self.load_folder(row)

    def load_folder(self, idx: int) -> None:
        if not (0 <= idx < len(self.folders)):
            return
        self.current_idx = idx
        self.archive_family_btn.setEnabled(True)
        self.archive_family_btn.setText("Restore family" if self.view_mode == "archive" else "Archive family")
        self.archive_family_btn.setToolTip(
            "Restore every font in this family to Active."
            if self.view_mode == "archive"
            else "Hide every font in this family from Active; find it in Archive."
        )
        self.save_family_btn.setEnabled(True)
        self.delete_folder_btn.setEnabled(True)
        if self.folder_list.currentRow() != idx:
            self.folder_list.blockSignals(True)
            self.folder_list.setCurrentRow(idx)
            self.folder_list.blockSignals(False)
        folder = self.folders[idx]
        fonts, archive_error = visible_fonts(folder, self.view_mode)
        payload, sidecar_error = load_sidecar(folder)
        verdicts = payload.get("verdicts", {})
        researched = sum(1 for path in fonts if path.name in verdicts)
        self.folder_title.setText(folder.name + ("  ·  ARCHIVE" if self.view_mode == "archive" else ""))
        self.count_label.setText(
            f"family {idx + 1}/{len(self.folders)}  ·  {len(fonts)} font(s)  ·  "
            f"{researched}/{len(fonts)} researched"
        )
        warnings = []
        if sidecar_error:
            warnings.append(f"{SIDECAR} in this folder is unreadable — rows show no verdicts until it is fixed.")
        if archive_error:
            warnings.append(f"{ARCHIVE_STATE} could not be read: {archive_error}")
        self.verdict_warn.setText("  ".join(warnings))
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < len(self.folders) - 1)
        self._clear_rows()
        if not fonts:
            empty = QLabel("No archived font files in this family." if self.view_mode == "archive" else "No active font files in this family.")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.rows_layout.addWidget(empty)
            self.rows_layout.addStretch()
            self.status.setText(f"{folder.name}: no {self.view_mode} font files.")
            return
        for path in fonts:
            row = FontRow(path, verdict=verdicts.get(path.name), archived=self.view_mode == "archive")
            row.activated.connect(lambda r=row: self._activate_row(r))
            row.verdict_clicked.connect(lambda r=row: self.show_verdict(r))
            row.use_btn.toggled.connect(lambda state, p=path: self.toggle_in_use(p, state))
            row.return_btn.clicked.connect(lambda _=False, p=path: self.return_font(p))
            row.delete_btn.clicked.connect(lambda _=False, p=path: self.delete_font(p))
            row.archive_btn.clicked.connect(lambda _=False, p=path: self.toggle_font_archive(p))
            self.rows_layout.addWidget(row)
            self.rows.append(row)
        self.rows_layout.addStretch()
        self.status.setText(f"Loaded {len(fonts)} {self.view_mode} font(s) from {folder.name}.")

    def _clear_rows(self) -> None:
        self.rows = []
        self.active_row = None
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _activate_row(self, row: FontRow, scroll: bool = False) -> None:
        if self.active_row is not None and self.active_row is not row:
            self.active_row.setStyleSheet("")
        self.active_row = row
        row.setStyleSheet(
            "QFrame#fontRow { border: 2px solid #d5a85e; border-radius: 8px; }"
        )
        if scroll:
            self.scroll.ensureWidgetVisible(row)

    def show_verdict(self, row: FontRow) -> None:
        """Open the evidence behind a chip; the row it came from is highlighted too."""
        self._activate_row(row)
        VerdictDialog(row.path.name, row.path.parent.name, row.verdict, self).exec()

    def _jump_to(self, matches, label: str, when_none: str) -> None:
        """Activate the first row after the active one that matches, wrapping around."""
        if not self.rows:
            return
        start = 0
        if self.active_row in self.rows:
            start = self.rows.index(self.active_row) + 1
        order = list(range(start, len(self.rows))) + list(range(0, start))
        for index in order:
            row = self.rows[index]
            if matches(row):
                self._activate_row(row, scroll=True)
                self.status.setText(f"{label}: {row.path.name} ({index + 1}/{len(self.rows)})")
                return
        self.status.setText(when_none)

    def next_unmarked(self) -> None:
        """Jump to the next row that is not marked In Use (wraps within the folder)."""
        self._jump_to(
            lambda row: not row.use_btn.isChecked(),
            "Next not In Use",
            "All fonts in this folder are marked In Use — use Next ▶ for the next family.",
        )

    def next_unchecked(self) -> None:
        """Jump to the next row with no rights verdict yet (wraps within the folder)."""
        self._jump_to(
            lambda row: row.verdict is None,
            "Next no verdict",
            "Every font in this folder has a rights verdict — use Next ▶ for the next family.",
        )

    def go_prev(self) -> None:
        if self.current_idx > 0:
            self.load_folder(self.current_idx - 1)

    def go_next(self) -> None:
        if self.current_idx < len(self.folders) - 1:
            self.load_folder(self.current_idx + 1)

    def refresh_view_after_change(self, previous: int, message: str) -> None:
        """Rebuild the current Active/Archive list after an archive or move action."""
        self._refresh_folders(select=previous)
        if self.folders:
            self.load_folder(min(previous, len(self.folders) - 1))
        else:
            self._clear_rows()
            self.active_row = None
            self.current_idx = -1
            self.folder_title.setText("No folder selected")
            self.count_label.setText("")
            self.verdict_warn.setText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
        self.status.setText(message)

    def toggle_font_archive(self, path: Path) -> None:
        """Archive one font or restore it from the Archive view."""
        try:
            family_archived, archived = read_archive_state(path.parent)
            if self.view_mode == "active":
                archived.add(path.name)
                write_archive_state(path.parent, family_archived, archived)
                message = f"Archived {path.name}; it is now in the Archive view."
            else:
                if family_archived:
                    archived = set(font_names(path.parent)) - {path.name}
                    family_archived = False
                else:
                    archived.discard(path.name)
                write_archive_state(path.parent, family_archived, archived)
                message = f"Restored {path.name} to the Active view."
        except (OSError, json.JSONDecodeError, ValueError) as error:
            QMessageBox.critical(self, "Could not update archive", str(error))
            return
        self.refresh_view_after_change(max(self.current_idx, 0), message)

    def toggle_family_archive(self) -> None:
        """Hide or restore every font in the selected family."""
        if not (0 <= self.current_idx < len(self.folders)):
            return
        folder = self.folders[self.current_idx]
        try:
            read_archive_state(folder)
            if self.view_mode == "active":
                write_archive_state(folder, True, set())
                message = f"Archived the {folder.name} family. Find it in the Archive view."
            else:
                write_archive_state(folder, False, set())
                message = f"Restored the {folder.name} family to Active."
        except (OSError, json.JSONDecodeError, ValueError) as error:
            QMessageBox.critical(self, "Could not update archive", str(error))
            return
        self.refresh_view_after_change(self.current_idx, message)

    def save_family(self) -> None:
        """Move only the selected family folder out of input/ and into Saved/."""
        if not (0 <= self.current_idx < len(self.folders)):
            return
        folder = self.folders[self.current_idx]
        target = saved_target(folder)
        font_count = len(font_names(folder))
        answer = QMessageBox.question(
            self,
            "Save family",
            f"Move {folder.name} and its {font_count} font file(s) out of input/?\n\n"
            f"The family folder will be moved to:\n{target}\n\n"
            "Other family folders in input/ will stay where they are.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            SAVED_DIR.mkdir(parents=True, exist_ok=True)
            target = saved_target(folder)
            shutil.move(str(folder), str(target))
        except OSError as error:
            QMessageBox.critical(self, "Could not save family", f"{error}\n\n{folder.name} is still in input/.")
            return
        self.refresh_view_after_change(
            self.current_idx,
            f"Saved {folder.name} to {target.relative_to(ROOT)}.",
        )

    def refresh_action(self) -> None:
        previous = max(self.current_idx, 0)
        self._refresh_folders(select=previous)
        if self.folders:
            self.load_folder(min(previous, len(self.folders) - 1))
            self.status.setText(f"Refreshed — {len(self.folders)} family folder(s).")
        else:
            self._clear_rows()
            self.active_row = None
            self.current_idx = -1
            self.folder_title.setText("No folder selected")
            self.count_label.setText("")
            self.verdict_warn.setText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.status.setText(f"No {self.view_mode} font families found under {INPUT_DIR}")

    def reload_current(self) -> None:
        if not self.folders:
            return
        idx = min(max(self.current_idx, 0), len(self.folders) - 1)
        self._refresh_folders(select=idx)
        if self.folders:
            self.load_folder(idx)
        else:
            self._clear_rows()
            self.active_row = None
            self.current_idx = -1
            self.folder_title.setText("No folder selected")
            self.count_label.setText("")
            self.verdict_warn.setText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)

    def reload_after_font_removed(self, folder: Path, action: str) -> None:
        """Refresh after a font leaves and move its now-empty family to reversible trash."""
        moved_to: Path | None = None
        cleanup_error: OSError | None = None
        try:
            moved_to = move_empty_family_to_trash(folder)
        except OSError as error:
            cleanup_error = error
        self.reload_current()
        if moved_to is not None:
            action += f" Empty family folder moved to {moved_to.relative_to(INPUT_DIR.parent)}."
        elif cleanup_error is not None:
            action += f" The empty family folder remains in input because it could not be moved to trash: {cleanup_error}"
        self.status.setText(action)

    def return_font(self, path: Path) -> None:
        folder = path.parent
        source = find_source(folder, path.name)
        if source is None:
            QMessageBox.information(
                self,
                "No source recorded",
                f"No original location is recorded for:\n{path.name}\n\n"
                "Use Delete to remove it from this folder.",
            )
            return
        if source == path:
            QMessageBox.information(
                self,
                "Source is this file",
                "This font's recorded source is the file itself.",
            )
            return
        try:
            if source.exists():
                if filecmp.cmp(str(path), str(source), shallow=False):
                    path.unlink()
                    action = f"original already at {source.parent}/ — staged copy removed"
                else:
                    answer = QMessageBox.question(
                        self,
                        "Files differ",
                        f"{path.name} exists at the source location but the contents\n"
                        "differ from the staged copy.\n\n"
                        "Overwrite the original with this staged copy?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    if answer != QMessageBox.StandardButton.Yes:
                        self.status.setText(f"Returned {path.name}: cancelled.")
                        return
                    shutil.copy2(path, source)
                    path.unlink()
                    action = f"staged copy copied over {source}"
            else:
                if not source.parent.is_dir():
                    QMessageBox.information(
                        self,
                        "Source folder is gone",
                        f"The recorded source folder no longer exists:\n{source.parent}\n\n"
                        "The staged copy was left in this folder rather than moved to a\n"
                        "guessed location. Use Delete if this font is not part of the family.",
                    )
                    return
                shutil.move(str(path), str(source))
                action = f"moved back to {source.parent}/"
        except OSError as error:
            QMessageBox.critical(self, "Could not return font", str(error))
            return
        prune_manifest(folder, path.name)
        prune_verdict(folder, path.name)
        prune_archived_font(folder, path.name)
        set_in_use(folder, path.name, False)
        self.reload_after_font_removed(folder, f"Returned {path.name}: {action}.")

    def toggle_in_use(self, path: Path, state: bool) -> None:
        try:
            set_in_use(path.parent, path.name, state)
        except OSError as error:
            self.status.setText(f"Could not save In Use mark: {error}")
            return
        if state:
            self.status.setText(f"Marked {path.name} as In Use.")
        else:
            self.status.setText(f"Removed In Use mark from {path.name}.")

    def delete_font(self, path: Path) -> None:
        answer = QMessageBox.question(
            self,
            "Delete font",
            f"Delete {path.name} from {path.parent.name}?\n\n"
            "This permanently removes the file and records it in\n"
            "font-factory/input/deleted-fonts.md as not part of the family.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        source = find_source(path.parent, path.name)
        # Write the do-not-restore ledger before deleting: an unlink that leaves
        # no entry would silently lose the reason the font was judged wrong.
        log_error = log_deletion(path, source)
        if log_error:
            QMessageBox.critical(
                self,
                "Could not write the deletion log",
                f"{log_error}\n\nThe font was not deleted.",
            )
            return
        try:
            path.unlink()
        except OSError as error:
            QMessageBox.critical(
                self,
                "Could not delete font",
                f"{error}\n\nThe deletion log already records {path.name}; delete it again to make the two agree.",
            )
            return
        prune_manifest(path.parent, path.name)
        prune_verdict(path.parent, path.name)
        prune_archived_font(path.parent, path.name)
        set_in_use(path.parent, path.name, False)
        self.reload_after_font_removed(
            path.parent,
            f"Deleted {path.name} — recorded in input/deleted-fonts.md (not part of the family).",
        )

    def delete_folder(self) -> None:
        """Move the selected family folder out of input/ and into input/.trash/."""
        if not (0 <= self.current_idx < len(self.folders)):
            self.status.setText("Choose a family folder in the list first.")
            return
        folder = self.folders[self.current_idx]
        if not folder.is_dir():
            self.status.setText(f"{folder.name} is already gone — press ↻ Refresh.")
            return
        researched, total, unreadable = verdict_counts(folder)
        target = trash_target(folder)
        answer = QMessageBox.question(
            self,
            "Delete family folder",
            f"Move {folder.name} out of input/?\n\n"
            f"{total} font file(s)  ·  {'?' if unreadable else researched}/{total} researched.\n\n"
            "The whole folder leaves input/ — its fonts, its In Use marks, its manifest,\n"
            f"and its {SIDECAR} (those verdicts drop out of the ledger on the next sync).\n\n"
            "Nothing is unlinked. It lands at:\n"
            f"{target}\n\n"
            "If this family was staged with Mark used family, its originals are already out\n"
            "of the source dump — this folder is the only copy, so empty the trash yourself\n"
            "when you are sure.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        previous = self.current_idx
        try:
            target = move_folder_to_trash(folder)
        except OSError as error:
            QMessageBox.critical(
                self,
                "Could not move the folder",
                f"{error}\n\n{folder.name} is still where it was.",
            )
            return
        self._clear_rows()
        self.active_row = None
        self.current_idx = -1
        moved = f"Moved {folder.name} to {target.relative_to(INPUT_DIR.parent)}"
        self._refresh_folders(select=previous)
        if self.folders:
            self.load_folder(min(previous, len(self.folders) - 1))
            self.status.setText(moved + ".")
        else:
            self.folder_title.setText("No folder selected")
            self.count_label.setText("")
            self.verdict_warn.setText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.status.setText(moved + f" — no family folders left under {INPUT_DIR}")


def main() -> None:
    app = QApplication(sys.argv)
    window = InspectorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
