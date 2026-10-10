#!/usr/bin/env python3
"""Font Vault: a local, lazy font-review desktop app."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import random
import re
import signal
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy, QSplitter, QVBoxLayout, QWidget,
)


ROOT = Path(__file__).resolve().parent.parent
RENDERER = ROOT / "bin" / "render_font_specimens.py"
DATA_DIR = Path(__file__).resolve().parent / "data"
CACHE_DIR = DATA_DIR / "cache"
INPUT_DIR = ROOT / "font-factory" / "input"
STATE_PATH = DATA_DIR / "state.json"
DB_PATH = DATA_DIR / "vault.db"
BACKUP_DIR = DATA_DIR / "backups"
# A snapshot older than this is refreshed even when nothing was reviewed.
BACKUP_MAX_AGE_SECONDS = 20 * 3600
FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}

from db import VaultDB


@dataclass
class FontRecord:
    key: str
    display: str
    source: str
    entry: str | None = None


SAMPLE_SENTENCE = "The Quick Brown Fox Jumps Over The Lazy Dog."
ANALYSIS_VERSION = 4
MAX_QUEUE_ROWS = 2000
# Measured across 771 sampled fonts the deep outline pass runs 88 ms at p95; the
# slowest real file finished in 350 ms, so 0.5 s gives every font room to answer.
DEEP_OUTLINE_TIMEOUT = 0.5


class OutlineTimeoutError(Exception):
    """The bounded outline pass ran out of time — no verdict about the font."""


def pretty_display(display: str) -> str:
    """Return a human-readable Title Case name from a raw font filename stem.

    Converts separators to spaces and title-cases each word so that names like
    ``WALKWAY_BOLD``, ``Maidega-Italic``, or ``myFont_ExtraBold`` render as
    ``Walkway Bold``, ``Maidega Italic``, and ``Myfont Extrabold`` respectively.
    """
    return re.sub(r"[-_]+", " ", display).title()

# Words that describe a *style* rather than a family. These may be dropped from
# a family name and are accepted as a filename suffix after the family stem.
# Foundry/redistribution tags (db, ssi, bt, dtc, ef, itc, be, urw, com) are
# deliberately NOT here: a vendor clone is a separate product with its own
# outlines and licence, and stripping them merged "Bauhaus ITC", "Bauhaus BT"
# and "Bauhaus EF" into one family, so "Mark used family" copied all of them.
MODIFIER_TOKENS = {
    "thin", "hairline", "extra light", "extralight", "ultra light", "ultralight",
    "light", "book", "regular", "normal", "plain", "roman",
    "medium", "med", "semi bold", "semibold", "demi bold", "demibold", "demi",
    "bold", "extra bold", "extrabold", "ultra bold", "ultrabold",
    "black", "heavy", "extra black", "extrablack", "ultra black", "ultrablack",
    "ultra", "poster", "fat",
    "ultra condensed", "ultracondensed", "extra condensed", "extracondensed",
    "condensed", "cond", "cn", "compressed", "compact", "narrow",
    "extended", "ext", "expanded", "wide",
    "italic", "ita", "it", "oblique", "obl", "slanted",
    "outline", "inline", "shadow", "shadowed", "shaded", "3d", "open", "caps", "titling", "display",
    "bd", "lt", "bk", "blk", "rg", "sm",
    "demo", "trial", "free", "sample",
}


def is_style_token(word: str) -> bool:
    return word.casefold() in MODIFIER_TOKENS


SUBTOKEN_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z]|\b|\d)|[A-Z]?[a-z]+|[0-9]+")


def split_subtokens(value: str) -> list[str]:
    """Cut a name into words: 'BulmerMTDisplay' → ['Bulmer', 'MT', 'Display']."""
    parts: list[str] = []
    for chunk in re.split(r"[\s\-_/.\\]+", value):
        if chunk:
            parts.extend(SUBTOKEN_RE.findall(chunk))
    return parts


def family_key_of(label: str) -> str:
    """Comparison identity for a family name: spelling noise cancelled, nothing dropped.

    'BulmerMTDisplay' and 'Bulmer MT Display' are one family written two ways, so
    they must share a key. Re-segmenting (and casefolding) unifies them the way the
    old filename route always could. Dropping style words is what the old guesser
    did with this same splitter, and that is what merged 'Encode Sans Condensed'
    with 'Encode Sans Narrow' — so this key keeps every word.

    A label made only of punctuation splits into nothing; falling back to the raw
    text keeps two such fonts from sharing an empty key and merging.
    """
    parts = [part.casefold() for part in split_subtokens(label)]
    return " ".join(parts) if parts else " ".join(label.casefold().split())


def clean_family_name(raw_name: str) -> str:
    cleaned: list[str] = []
    for chunk in re.split(r"[\s\-_/.]+", raw_name):
        if not chunk:
            continue
        if is_style_token(chunk):
            continue
        subs = SUBTOKEN_RE.findall(chunk)
        for s in subs:
            if not is_style_token(s):
                cleaned.append(s)
    if not cleaned:
        return raw_name
    return " ".join(cleaned)


def detect_style_from_name(display_name: str, family_label: str) -> str:
    """Detect style keywords (e.g. Bold Italic, Thin, Black) from filename or display stem."""
    remainder = re.sub(re.escape(family_label), "", display_name, flags=re.IGNORECASE).strip(" _-.")
    if not remainder:
        return "Regular"
    tokens = [c for c in re.split(r"[\s\-_/.]+", remainder) if c]
    style_parts = []
    for t in tokens:
        if is_style_token(t):
            style_parts.append(t.capitalize())
        else:
            subs = SUBTOKEN_RE.findall(t)
            for s in subs:
                if is_style_token(s):
                    style_parts.append(s.capitalize())
    if style_parts:
        return " ".join(style_parts)
    return "Regular"


def is_valid_style_remainder(remainder: str) -> bool:
    """Ensure that the suffix remainder after the family stem contains only valid typographic style tokens."""
    remainder = remainder.strip(" _-.()[]")
    if not remainder:
        return True
    words = [w for w in re.split(r"[\s\-_/.]+", remainder) if w]
    for w in words:
        if is_style_token(w):
            continue
        subs = SUBTOKEN_RE.findall(w)
        if not subs or not all(is_style_token(s) for s in subs):
            return False
    return True


GENERIC_NAMES = {"new", "font", "regular", "unknown", "unnamed", "untitled", ""}
WEIGHT_NAMES = (
    (100, "Thin"), (200, "Extra Light"), (300, "Light"), (400, "Regular"),
    (500, "Medium"), (600, "Semi Bold"), (700, "Bold"), (800, "Extra Bold"),
    (900, "Black"), (950, "Extra Black"),
)
WIDTH_NAMES = {
    1: "Ultra Condensed", 2: "Extra Condensed", 3: "Condensed", 4: "Semi Condensed",
    5: "", 6: "Semi Expanded", 7: "Expanded", 8: "Extra Expanded", 9: "Ultra Expanded",
}


@dataclass(frozen=True)
class FamilyInfo:
    key: str
    label: str
    style: str
    source: str
    display: str


def normalize_family_text(value: str) -> str:
    """Normalise separators only.

    Metadata family names are the designer's own words, so nothing is dropped
    from them: "Encode Sans Condensed" and "Bauhaus 93" are families, not
    styles of "Encode Sans" or "Bauhaus".
    """
    return " ".join(part for part in re.split(r"[\s_./\\-]+", value.strip()) if part)


def family_from_ps_name(ps_name: str) -> str:
    """'BauhausITC-Bold' → 'BauhausITC'; the PostScript name's tail is the style."""
    head, _, tail = ps_name.rpartition("-")
    if head and is_valid_style_remainder(tail):
        return head
    return ps_name


def weight_name(weight_class: int) -> str:
    if weight_class <= 0:
        return ""
    return min(WEIGHT_NAMES, key=lambda item: abs(item[0] - weight_class))[1]


def style_from_metrics(weight_class: int, width_class: int, italic: bool) -> str:
    parts = [weight_name(weight_class), WIDTH_NAMES.get(width_class, ""), "Italic" if italic else ""]
    return " ".join(part for part in parts if part)


def read_family_metadata(path: Path) -> dict:
    """Read the identity a font carries about itself: name records, plus the
    numeric weight/width/slant its outlines were actually built to."""
    names: dict[int, str] = {}
    weight = width = 0
    italic = False
    try:
        with TTFont(path, lazy=True, ignoreDecompileErrors=True) as font:
            for record in sorted(font["name"].names, key=lambda item: (item.nameID, item.platformID != 3)):
                if record.nameID not in {1, 2, 6, 16, 17} or record.nameID in names:
                    continue
                try:
                    value = " ".join(record.toUnicode().split())
                except Exception:
                    continue
                if value:
                    names[record.nameID] = value
            try:
                os2 = font["OS/2"]
                weight = int(os2.usWeightClass or 0)
                width = int(os2.usWidthClass or 0)
                italic = bool(int(os2.fsSelection) & 1)
            except Exception:
                pass
    except Exception:
        pass
    return {"names": names, "weight": weight, "width": width, "italic": italic}


def resolve_family(display: str, meta: dict) -> FamilyInfo:
    """Work out which family a font belongs to, trusting the font first.

    Order: typographic family (nameID 16), legacy family (1), PostScript name
    prefix (6), then — only when the font says nothing usable — the filename
    with style words removed. `source` records which tier answered, because a
    font that names its own family must not be merged into a look-alike.
    """
    names = meta["names"]
    label = ""
    source = "filename"
    for raw in (names.get(16), names.get(1)):
        normalized = normalize_family_text(raw or "")
        if normalized and normalized.casefold() not in GENERIC_NAMES:
            label, source = normalized, "metadata"
            break
    if not label:
        normalized = normalize_family_text(family_from_ps_name(names.get(6) or ""))
        if normalized and normalized.casefold() not in GENERIC_NAMES:
            label, source = normalized, "psname"
    if not label:
        label = clean_family_name(display)
    # A common bad-metadata value in 125 Mil Fuentes is "New" for unrelated
    # files, and style stripping can reduce those names to nothing.
    if not label.strip():
        label = display

    style = names.get(17) or names.get(2) or ""
    if style.casefold() in {"regular", "normal", "plain", "standard", ""}:
        style = style_from_metrics(meta["weight"], meta["width"], meta["italic"]) or "Regular"
        if style == "Regular":
            style = detect_style_from_name(display, label)
    return FamilyInfo(
        key=family_key_of(label),
        label=label,
        style=style,
        source=source,
        display=display,
    )


def family_member_matches(target: FamilyInfo, candidate: FamilyInfo) -> bool:
    """Decide whether `candidate` is a style of the `target` family."""
    if candidate.key == target.key:
        return True
    # The font states a different family itself: its filename resembling the
    # target is not evidence, it is a different product.
    if candidate.source == "metadata":
        return False
    pattern = r"^" + re.escape(target.label) + r"([\s\-_.]|$)"
    match = re.match(pattern, candidate.display, re.IGNORECASE)
    if match:
        return is_valid_style_remainder(candidate.display[match.end():])
    if candidate.display.lower().startswith(target.label.lower()):
        return is_valid_style_remainder(candidate.display[len(target.label):])
    return False


class DirectoryScanWorker(QObject):
    """Find font paths off the UI thread; index directly into SQLite with fast batching."""

    progress = Signal(int)
    batch = Signal(object)
    completed = Signal(int)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, path: Path, db: VaultDB, vault_id: int) -> None:
        super().__init__()
        self.path = path
        self.db = db
        self.vault_id = vault_id

    @Slot()
    def run(self) -> None:
        pending_records: list[dict] = []
        ui_batch: list[FontRecord] = []
        total_count = 0
        try:
            for font_path in sorted(self.path.rglob("*")):
                if font_path.is_file() and font_path.suffix.lower() in FONT_EXTENSIONS:
                    stat = font_path.stat()
                    key = f"file:{font_path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}"
                    record = FontRecord(key, font_path.stem, str(font_path))
                    ui_batch.append(record)
                    pending_records.append({
                        "file_key": key,
                        "file_path": str(font_path.resolve()),
                        "file_size": stat.st_size,
                        "mtime_ns": stat.st_mtime_ns,
                        "stem": font_path.stem,
                        "display": font_path.stem,
                        "family_key": "",
                        "family_label": "",
                        "style": "Regular"
                    })
                    total_count += 1
                    if len(pending_records) >= 1000:
                        self.db.bulk_insert_font_records(self.vault_id, pending_records)
                        pending_records = []
                    if len(ui_batch) >= 500:
                        self.batch.emit(ui_batch)
                        ui_batch = []
                    if total_count % 1000 == 0:
                        self.progress.emit(total_count)
            if pending_records:
                self.db.bulk_insert_font_records(self.vault_id, pending_records)
            if ui_batch:
                self.batch.emit(ui_batch)
            self.completed.emit(total_count)
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.finished.emit()


class SpecimenRenderWorker(QObject):
    """Render the combined specimen and read font facts off the UI thread.

    Each batch is rendered in the given order (the currently viewed font first,
    then prefetched neighbours). Font files and PIL/subprocess work are safe in
    this thread; only the file path + facts text are emitted back to the UI
    thread, which owns the QPixmap.
    """

    ready = Signal(object, str, str, str)  # record key, render path, facts text, classification note
    failed = Signal(object, str)           # record key, error message
    done = Signal()

    def __init__(self, window: "FontVaultWindow", records: list[FontRecord]) -> None:
        super().__init__()
        self.window = window
        self.records = records
        self.cancelled = False

    @Slot()
    def run(self) -> None:
        for record in self.records:
            if self.cancelled:
                break
            try:
                # Deep outline checks use SIGALRM timeouts and must stay on the
                # UI thread (queue_selected runs them); the worker uses the fast
                # cmap pass, which is enough for broken/missing-letter notes.
                state = self.window.analyze_record(record, deep=False)
                note = f" · excluded: {state.get('reason')}" if state.get("classification") == "broken" else ""
                path = str(self.window.render_path(record))
                facts = self.window.inspect(record) + note
            except Exception as error:
                self.failed.emit(record.key, str(error))
                continue
            self.ready.emit(record.key, path, facts, note)
        self.done.emit()


class FontVaultWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Font Vault — local font review")
        self.resize(1360, 860)
        self.setMinimumSize(1040, 700)
        self.setStyleSheet(self.styles())
        self.db = VaultDB(DB_PATH)
        # One-time transparent migration from state.json if needed
        self.db.migrate_from_state_json(STATE_PATH)
        try:
            self.backup_vault()
        except (OSError, sqlite3.Error) as error:
            QMessageBox.warning(
                self,
                "Could not back up the vault",
                f"{error}\n\nReview data is not being snapshotted into {BACKUP_DIR}.",
            )
        self.state = {"items": {}}
        self.records: list[FontRecord] = []
        self.filtered_records: list[FontRecord] = []
        self.visible: list[FontRecord] = []
        self.visible_index: dict[str, int] = {}
        self.filtered_index: dict[str, int] = {}
        self.current: FontRecord | None = None
        self.source_path: Path | None = None
        self.vault_id: int | None = None
        self.source_kind = ""
        self.rng = random.SystemRandom()
        self.family_cache: dict[str, FamilyInfo] = {}
        self.queue_page = 0
        self._closing = False
        self.scan_thread: QThread | None = None
        self.scan_worker: DirectoryScanWorker | None = None
        # Background specimen rendering + result caches
        self._pixmap_orig_cache: dict[str, QPixmap] = {}
        self._pixmap_cache: dict[str, QPixmap] = {}
        self._facts_cache: dict[str, str] = {}
        self._render_thread: QThread | None = None
        self._render_worker: SpecimenRenderWorker | None = None
        self._pending_renders: list[FontRecord] = []

        self.batch_label = QLabel("No font batch loaded")
        self.status_label = QLabel("Choose a font directory to begin.")
        self.search = QLineEdit(); self.search.setPlaceholderText("Search this batch")
        self.filter = QComboBox(); self.filter.addItems(["Review queue", "Unreviewed", "Used", "Archived", "Skipped", "Broken / excluded", "All scanned"])
        self.skip_broken = QCheckBox("Auto-skip broken fonts")
        self.skip_broken.setChecked(True)
        self.queue = QListWidget()
        self.preview = QLabel("Open a font directory\n\nThe next font renders on demand.")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.name_label = QLabel("No font selected")
        self.facts_label = QLabel("")
        self.build_ui()
        self.search.textChanged.connect(self.refresh_list)
        self.filter.currentTextChanged.connect(self.refresh_list)
        self.queue.currentRowChanged.connect(self.queue_selected)
        self.skip_broken.stateChanged.connect(self.refresh_list)
        for label in (self.batch_label, self.status_label, self.name_label, self.facts_label, self.preview):
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
            label.setCursor(Qt.CursorShape.IBeamCursor)
        self.copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self.queue)
        self.copy_shortcut.activated.connect(self.copy_queue_selection)
        self.populate_recent_vaults()
        self.resume_last_vault()

    @staticmethod
    def styles() -> str:
        return """
        QWidget { background: #111315; color: #eeeae2; font-size: 13px; }
        QFrame#panel { background: #191c1f; border-radius: 10px; }
        QLabel#title { color: #f3f0e8; font-size: 21px; font-weight: 700; letter-spacing: 2px; }
        QLabel#muted, QLabel#facts, QLabel#status { color: #9ca5a8; }
        QLabel#fontName { color: #f0eee9; font-size: 19px; font-weight: 700; }
        QLineEdit, QComboBox { background: #2a2f33; color: #f0eee9; border: 1px solid #3a4246; border-radius: 6px; padding: 8px; }
        QListWidget { background: #191c1f; border: 0; color: #dedbd3; outline: 0; }
        QListWidget::item { padding: 8px 7px; border-radius: 5px; }
        QListWidget::item:selected { background: #6f5839; color: #fff9ef; }
        QPushButton { background: #2a2f33; color: #eeeae2; border: 0; border-radius: 6px; padding: 9px 13px; }
        QPushButton:hover { background: #394148; }
        QPushButton#primary { background: #d5a85e; color: #141414; font-weight: 700; }
        QPushButton#primary:hover { background: #efc777; }
        QPushButton:focus, QLineEdit:focus, QComboBox:focus, QListWidget:focus { border: 1px solid #d5a85e; }
        QComboBox { min-height: 20px; }
        QCheckBox { color: #b7c0c2; spacing: 8px; }
        QPushButton#skipFamily { background: #4a3b2b; }
        QPushButton#skipFamily:hover { background: #604b34; }
        """

    def button(self, text: str, slot, primary: bool = False) -> QPushButton:
        button = QPushButton(text)
        if primary:
            button.setObjectName("primary")
        button.clicked.connect(slot)
        return button

    def build_ui(self) -> None:
        root = QWidget(); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(18, 18, 18, 14); outer.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel("FONT VAULT"); title.setObjectName("title"); header.addWidget(title)
        self.batch_label.setObjectName("muted"); header.addWidget(self.batch_label); header.addStretch()
        self.recent_vaults = QComboBox(); self.recent_vaults.setMinimumWidth(220); self.recent_vaults.setToolTip("Saved vaults stay available after unloading.")
        header.addWidget(self.recent_vaults); header.addWidget(self.button("Load recent", self.open_recent)); header.addWidget(self.button("↻ Re-sync", self.resync_vault)); header.addWidget(self.button("Unload", self.unload_vault)); header.addWidget(self.button("Open directory", self.open_directory, True)); outer.addLayout(header)

        split = QSplitter(Qt.Orientation.Horizontal); split.setChildrenCollapsible(False)
        sidebar = QFrame(); sidebar.setObjectName("panel"); sidebar.setMinimumWidth(220); sidebar.setMaximumWidth(275)
        side_layout = QVBoxLayout(sidebar); side_layout.setContentsMargins(14, 14, 14, 14); side_layout.setSpacing(10)
        label = QLabel("REVIEW QUEUE"); label.setObjectName("muted"); side_layout.addWidget(label); side_layout.addWidget(self.search); side_layout.addWidget(self.filter); side_layout.addWidget(self.skip_broken); side_layout.addWidget(self.queue, 1); side_layout.addWidget(self.button("Copy selected row", self.copy_queue_selection))
        page_row = QHBoxLayout(); page_row.addWidget(self.button("← Page", self.previous_queue_page)); page_row.addWidget(self.button("Page →", self.next_queue_page)); side_layout.addLayout(page_row)
        self.page_label = QLabel("No indexed fonts"); self.page_label.setObjectName("muted"); self.page_label.setWordWrap(True); side_layout.addWidget(self.page_label)

        main = QWidget(); main_layout = QVBoxLayout(main); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(12)
        preview_panel = QFrame(); preview_panel.setObjectName("panel"); preview_layout = QVBoxLayout(preview_panel); preview_layout.setContentsMargins(14, 14, 14, 14)
        specimen_label = QLabel("COMBINED SPECIMEN  ·  CHARACTER SET + SENTENCE"); specimen_label.setObjectName("muted"); preview_layout.addWidget(specimen_label)
        self.name_label.setObjectName("fontName"); preview_layout.addWidget(self.name_label)
        # Metadata facts live in a compact scroll area so long descriptions
        # (license text, URLs, authors) can never steal space from the specimen.
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMaximumHeight(120)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: 0; }")
        self.facts_label.setObjectName("facts"); self.facts_label.setWordWrap(True)
        self.facts_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.facts_label)
        preview_layout.addWidget(scroll)
        copy_row = QHBoxLayout(); copy_row.addWidget(self.button("Copy font details", self.copy_current_details)); copy_row.addWidget(self.button("Copy specimen text", self.copy_specimen_text)); copy_row.addStretch(); preview_layout.addLayout(copy_row)
        preview_layout.addWidget(self.preview, 1); main_layout.addWidget(preview_panel, 1)

        actions = QHBoxLayout(); actions.addStretch(); actions.addWidget(self.button("Create fsType=0 working copy…", self.create_installable_copy)); actions.addWidget(self.button("Mark used family", self.mark_used_family)); actions.addWidget(self.button("Archive family", self.archive_family))
        navigation = QVBoxLayout(); navigation.setSpacing(5)
        skip_button = self.button("Skip family →", self.skip_family); skip_button.setObjectName("skipFamily"); skip_button.setToolTip("Mark every style in this font family as skipped and move to the next family."); navigation.addWidget(skip_button)
        movement = QHBoxLayout(); movement.setSpacing(5); movement.addWidget(self.button("← Previous", self.previous)); movement.addWidget(self.button("Next →", self.next, True)); navigation.addLayout(movement)
        navigation.addWidget(self.button("Randomize", self.randomize)); actions.addLayout(navigation); main_layout.addLayout(actions)
        split.addWidget(sidebar); split.addWidget(main); split.setSizes([245, 1100]); outer.addWidget(split, 1)
        self.status_label.setObjectName("status"); outer.addWidget(self.status_label)

    def open_directory(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Choose a font directory")
        if chosen: self.load_directory(Path(chosen))

    def load_directory(self, path: Path, force_rescan: bool = False) -> None:
        if self.scan_thread and self.scan_thread.isRunning():
            self.status_label.setText("A vault is already loading. Please wait for that scan to finish.")
            return
        if not path.is_dir():
            self.status_label.setText(f"Directory not found: {path}")
            return
        self.source_path, self.source_kind = path, "directory"
        self.records = []; self.filtered_records = []; self.visible = []; self.current = None; self.queue_page = 0; self.queue.clear()

        # Register vault in DB and check if already indexed
        vault_id = self.db.upsert_vault(path)
        self.vault_id = vault_id
        existing_count = self.db.count_vault_fonts(vault_id)

        if existing_count > 0 and not force_rescan:
            # Instant load from DB index — no disk scan needed
            self._load_from_db(path, vault_id, existing_count)
            return

        self.batch_label.setText(f"{'Re-scanning' if force_rescan else 'Scanning'} {path.name}…")
        self.preview.setText("Scanning directory…\n\nThe app is staying responsive while it indexes font paths.")
        self.status_label.setText("Scanning directory…")
        self.scan_thread = QThread(self)
        self.scan_worker = DirectoryScanWorker(path, self.db, vault_id)
        self.scan_worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.batch.connect(self.append_scan_records)
        self.scan_worker.progress.connect(lambda count: self.status_label.setText(f"Scanning directory… {count:,} font files found"))
        self.scan_worker.completed.connect(self.finish_load)
        self.scan_worker.failed.connect(self.scan_failed)
        self.scan_worker.finished.connect(self.scan_thread.quit)
        self.scan_worker.finished.connect(self.scan_worker.deleteLater)
        self.scan_thread.finished.connect(self.scan_thread.deleteLater)
        self.scan_thread.finished.connect(self.scan_finished)
        self.scan_thread.start()

    def _load_from_db(self, path: Path, vault_id: int, total: int) -> None:
        """Instant vault load from SQLite index — no disk scan required."""
        q, f = self.db.get_vault_prefs(path)
        self.search.setText(q)
        if self.filter.findText(f) >= 0:
            self.filter.setCurrentText(f)
        # Keep one page of records in memory. Filtering, paging, navigation and
        # family lookups all go through SQLite, so materialising the whole
        # vault here only costs RAM.
        rows, _total = self.db.query_vault_fonts(vault_id, "", "All scanned", skip_broken=False, limit=MAX_QUEUE_ROWS)
        self.records = [
            FontRecord(
                key=r["file_key"],
                display=r["display"],
                source=r["file_path"],
                entry=None,
            )
            for r in rows
        ]
        self.db.update_vault_prefs(path, q, f)
        self.db.set_app_state("last_source", str(path))
        self._update_recent_sources(path)
        self.batch_label.setText(f"{path.name}  ·  {total:,} font(s) — loaded from index")
        self.populate_recent_vaults()
        self.refresh_list(select_first=True)
        self.status_label.setText(
            f"Opened instantly from SQLite index — {total:,} fonts. "
            "Use ↻ Re-sync if you've added new fonts to this directory."
        )

    def scan_finished(self) -> None:
        self.scan_thread = None
        self.scan_worker = None

    def scan_failed(self, message: str) -> None:
        self.records = []; self.filtered_records = []; self.visible = []; self.current = None; self.queue_page = 0; self.queue.clear()
        self.batch_label.setText("Vault load failed")
        self.preview.setText("This directory could not be loaded.")
        self.status_label.setText(f"Load failed: {message}")

    def populate_recent_vaults(self) -> None:
        if not hasattr(self, "recent_vaults"): return
        self.recent_vaults.blockSignals(True); self.recent_vaults.clear()
        vaults = self.db.list_recent_vaults()
        if not vaults:
            self.recent_vaults.addItem("No saved vaults")
        else:
            for v in vaults:
                path = Path(v["path"])
                if path.is_dir():
                    self.recent_vaults.addItem(f"{path.name}  ·  {v['path']}", v["path"])
        if self.recent_vaults.count() == 0:
            self.recent_vaults.addItem("No available saved directories")
        self.recent_vaults.blockSignals(False)

    def _update_recent_sources(self, path: Path) -> None:
        """Keep saved vaults and last_source updated in SQLite."""
        self.db.upsert_vault(path)
        self.db.set_app_state("last_source", str(path))

    def open_recent(self) -> None:
        source = self.recent_vaults.currentData()
        if source: self.load_directory(Path(source))

    def resync_vault(self) -> None:
        """Force a fresh disk scan of the current vault to pick up newly added fonts."""
        if not self.source_path:
            self.status_label.setText("No vault is currently loaded. Open a directory first.")
            return
        if self.scan_thread and self.scan_thread.isRunning():
            self.status_label.setText("A scan is already running. Please wait for it to finish.")
            return
        self.load_directory(self.source_path, force_rescan=True)

    def unload_vault(self) -> None:
        if self.scan_thread and self.scan_thread.isRunning():
            self.status_label.setText("The vault is still loading; it will be safe to unload after indexing finishes.")
            return
        if not self.source_path:
            self.status_label.setText("No vault is currently loaded. Saved vaults remain available above.")
            return
        unloaded = self.source_path
        self.records = []; self.filtered_records = []; self.visible = []; self.visible_index = {}; self.current = None; self.queue_page = 0
        # Per-vault caches: statuses and family metadata live in SQLite, so the
        # in-memory copies must be dropped or they accumulate across vaults.
        self.state = {"items": {}}
        self.family_cache = {}
        self._pixmap_orig_cache = {}; self._pixmap_cache = {}; self._facts_cache = {}
        self.source_path = None; self.source_kind = ""; self.vault_id = None
        self.queue.clear(); self.preview.setText("No vault loaded.\n\nChoose a saved vault or open a directory.")
        self.name_label.setText("No font selected"); self.facts_label.clear(); self.batch_label.setText("No vault loaded · data saved")
        self.db.set_app_state("last_source", ""); self.populate_recent_vaults()
        self.status_label.setText(f"Unloaded {unloaded.name}. Review data and cache remain saved.")

    def backup_vault(self) -> Path | None:
        """Snapshot the review database, but only when there is something to protect.

        A snapshot is written when none exists, when the newest one is older than
        BACKUP_MAX_AGE_SECONDS, or when reviews changed after it — so a crash or a
        bad WAL recovery loses at most one day of triage.
        """
        newest = max(BACKUP_DIR.glob("vault-*.db"), key=lambda p: p.stat().st_mtime, default=None)
        if newest is not None:
            stamp = int(newest.stat().st_mtime)
            if time.time() - stamp < BACKUP_MAX_AGE_SECONDS and self.db.latest_review_epoch() <= stamp:
                return None
        snapshot = self.db.backup(BACKUP_DIR)
        if snapshot is not None:
            self.db.export_to_state_json(BACKUP_DIR / "reviews.json")
        return snapshot

    def closeEvent(self, event) -> None:
        """Stop worker threads, snapshot the review data, then fold the WAL back in."""
        self._closing = True
        if self._render_worker is not None:
            self._render_worker.cancelled = True
        for thread in (self._render_thread, self.scan_thread):
            if thread is not None and thread.isRunning():
                thread.quit()
                # quit() is only heard once the worker's run() returns; without this
                # wait the QThread is destroyed while still running, which aborts.
                if not thread.wait(10000):
                    print("A worker thread did not stop; leaving it running.", file=sys.stderr)
        try:
            self.backup_vault()
        except (OSError, sqlite3.Error) as error:
            print(f"Vault backup failed on close: {error}", file=sys.stderr)
        try:
            self.db.conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        except sqlite3.Error:
            pass
        self.db.close()
        super().closeEvent(event)

    def append_scan_records(self, records: list[FontRecord]) -> None:
        self.records.extend(records)
        # Fill the first page quickly, then refresh once per page-sized batch.
        if len(self.records) <= MAX_QUEUE_ROWS or len(self.records) % MAX_QUEUE_ROWS < len(records):
            self.refresh_list(select_first=not self.current, reset_page=False)
        self.batch_label.setText(f"Loading {self.source_path.name if self.source_path else 'vault'}… {len(self.records):,} font(s)")

    def finish_load(self, total: int) -> None:
        label = self.source_path.name if self.source_path else "Vault"
        self.batch_label.setText(f"{label}  ·  {len(self.records):,} font(s)")
        # Restore saved search/filter from DB
        q, f = self.db.get_vault_prefs(self.source_path)
        self.search.setText(q)
        if self.filter.findText(f) >= 0:
            self.filter.setCurrentText(f)
        # Persist vault as last-used in DB
        self.db.set_app_state("last_source", str(self.source_path))
        self._update_recent_sources(self.source_path)
        self.populate_recent_vaults(); self.refresh_list(select_first=True)
        queue_note = f" Use Page → to browse all {len(self.records):,} indexed fonts." if len(self.records) > MAX_QUEUE_ROWS else ""
        self.status_label.setText("Vault loaded. Font paths are indexed; glyph checks happen only when you open a font." + queue_note)

    def resume_last_vault(self) -> None:
        saved = self.db.get_app_state("last_source")
        if not saved:
            recent = self.db.list_recent_vaults()
            saved = recent[0]["path"] if recent else None
        if not saved: return
        path = Path(saved)
        if not path.exists(): return
        try:
            if path.is_dir(): self.load_directory(path)
        except Exception as error:
            self.status_label.setText(f"Could not resume the last vault: {error}")

    def item_state(self, record: FontRecord) -> dict:
        """Return the mutable review dict for a record, backed by SQLite with in-memory cache."""
        items = self.state.setdefault("items", {})
        if record.key not in items:
            # Populate from DB on first access
            db_row = self.db.get_review(record.key)
            if db_row:
                items[record.key] = {
                    "status": db_row.get("status", "unreviewed"),
                    "classification": db_row.get("classification", "reviewable"),
                    "reason": db_row.get("reason", "") or db_row.get("broken_reason", ""),
                    "outline_checked": bool(db_row.get("outline_checked", False)),
                    "analysis_version": ANALYSIS_VERSION if db_row.get("outline_checked") else "",
                    "family": db_row.get("family_key", ""),
                    "family_label": db_row.get("family_label", ""),
                }
            else:
                items[record.key] = {
                    "status": "unreviewed",
                    "classification": "reviewable",
                    "reason": "",
                    "outline_checked": False,
                    "family": "",
                    "family_label": "",
                }
        return items[record.key]



    def analyze_record(self, record: FontRecord, deep: bool = False) -> dict:
        state = self.item_state(record)
        if state.get("analysis_version") == ANALYSIS_VERSION and "classification" in state and (not deep or state.get("outline_checked")):
            return state
        result = {"classification": "reviewable", "reason": ""}
        alarm_fired = False
        try:
            # Keep queue rebuilding lightweight. Corrupt old glyf tables can
            # otherwise make startup spend minutes unpacking invalid outlines.
            font = TTFont(self.materialize(record), lazy=True, ignoreDecompileErrors=True)
            cmap = font.getBestCmap() or {}
            missing: list[str] = []
            for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
                glyph_name = cmap.get(ord(char))
                if not glyph_name or glyph_name == ".notdef":
                    missing.append(char); continue
            if missing:
                result = {"classification": "broken", "reason": "missing " + "".join(missing), "outline_checked": True}
            elif deep:
                # Outline checks are bounded because a few historical fonts
                # contain malformed glyf data that can otherwise hang startup.
                def timeout_handler(_signum, _frame):
                    nonlocal alarm_fired
                    alarm_fired = True
                    raise OutlineTimeoutError("outline inspection timed out")

                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.setitimer(signal.ITIMER_REAL, DEEP_OUTLINE_TIMEOUT)
                try:
                    glyph_set = font.getGlyphSet()
                    signatures: dict[str, str] = {}
                    blank: list[str] = []
                    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
                        pen = RecordingPen()
                        glyph_set[cmap[ord(char)]].draw(pen)
                        if not pen.value:
                            blank.append(char)
                        signatures[char] = repr(pen.value)
                    if blank:
                        result = {"classification": "broken", "reason": "blank " + "".join(blank)}
                    elif all(signatures[upper] == signatures[lower] for upper, lower in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")):
                        result = {"classification": "broken", "reason": "uppercase and lowercase outlines are identical"}
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    signal.signal(signal.SIGALRM, old_handler)
                    # Only a pass that ran to completion is remembered, so the
                    # bounded check does not repeat on every selection — and an
                    # interrupted one is not, because running out of time is no
                    # evidence about the font and a verdict this cheap would stick.
                    if not alarm_fired:
                        state["outline_checked"] = True
            font.close()
        except Exception as error:
            if alarm_fired:
                # The alarm can go off inside fontTools' lazy table loading, which
                # swallows exceptions and hands back a half-built table. What we
                # caught is that aftermath, not a defect in the font: leave the
                # font reviewable and unverified so the next selection retries.
                result = {"classification": "reviewable", "reason": ""}
            else:
                result = {"classification": "broken", "reason": f"could not inspect font: {error}"}
        state.update(result, analysis_version=ANALYSIS_VERSION)
        # Persist classification to SQLite so it survives app restarts
        self.db.upsert_review(
            file_key=record.key,
            status=state.get("status", "unreviewed"),
            classification=state.get("classification", "reviewable"),
            broken_reason=state.get("reason", ""),
            outline_checked=int(bool(state.get("outline_checked", False))),
            family_key=state.get("family", ""),
            family_label=state.get("family_label", ""),
        )
        return state

    def refresh_list(self, _value=None, select_first: bool = False, reset_page: bool = True) -> None:
        query = self.search.text().strip().lower(); selected_filter = self.filter.currentText(); wanted = selected_filter.lower(); matches: list[FontRecord] = []
        if reset_page: self.queue_page = 0
        if self.source_path and self.vault_id is not None:
            # Fast DB path: let SQLite handle all filtering and counting
            self.db.update_vault_prefs(self.source_path, self.search.text(), selected_filter)
            skip_broken = self.skip_broken.isChecked()
            rows, total_matches = self.db.query_vault_fonts(
                self.vault_id, query, selected_filter, skip_broken=skip_broken,
                limit=MAX_QUEUE_ROWS, offset=self.queue_page * MAX_QUEUE_ROWS,
            )
            # Rebuild visible FontRecord objects from DB rows
            self.visible = [
                FontRecord(
                    key=r["file_key"],
                    display=r["display"],
                    source=r["file_path"],
                    entry=None,
                )
                for r in rows
            ]
            # Update in-memory item_state cache from DB rows so markers are correct
            items = self.state.setdefault("items", {})
            for r in rows:
                items[r["file_key"]] = {
                    "status": r.get("status", "unreviewed"),
                    "classification": r.get("classification", "reviewable"),
                    "reason": r.get("reason", "") or r.get("broken_reason", ""),
                    "outline_checked": bool(r.get("outline_checked", 0)),
                    "family": r.get("family_key", ""),
                    "family_label": r.get("family_label", ""),
                }
            page_count = max(1, (total_matches + MAX_QUEUE_ROWS - 1) // MAX_QUEUE_ROWS)
            self.page_count = page_count
            self.total_matches = total_matches
            self.queue_page = min(self.queue_page, page_count - 1)
            # filtered_records/filtered_index are kept as approximations for next/prev navigation
            # (full set not loaded; use DB total for page math)
            self.filtered_records = self.visible  # only current page in memory
            self.filtered_index = {r.key: i for i, r in enumerate(self.visible)}
            self.queue.blockSignals(True); self.queue.clear()
            for record in self.visible:
                st = items.get(record.key, {}); status = st.get("status", "unreviewed")
                marker = {"archived": "▣", "used": "✓", "skipped": "»", "unreviewed": "·"}.get(status, "·")
                broken = f"  · {st.get('reason')}" if st.get("classification") == "broken" else ""
                self.queue.addItem(QListWidgetItem(f"{marker}  {record.display}{broken}"))
            self.queue.blockSignals(False)
            self.visible_index = {r.key: i for i, r in enumerate(self.visible)}
            start = self.queue_page * MAX_QUEUE_ROWS
            if total_matches:
                first = start + 1; last = min(start + len(self.visible), total_matches)
                self.page_label.setText(f"Showing {first:,}–{last:,} of {total_matches:,} matching fonts · page {self.queue_page + 1}/{page_count}")
            else:
                self.page_label.setText("No fonts match this view.")
            if select_first and self.visible: self.queue.setCurrentRow(0)
            elif not self.visible: self.clear_current("No fonts match this view.")
            return

        # Fallback: in-memory Python loop (used during active scan before vault_id is set)
        if self.source_path:
            self.state.setdefault("vaults", {}).setdefault(str(self.source_path), {}).update(query=self.search.text(), filter=selected_filter)
        for record in self.records:
            # Do not open every font while rebuilding the queue. Unknown fonts
            # are checked when selected; cached broken classifications remain
            # excluded immediately.
            state = self.item_state(record); status = state.get("status", "unreviewed"); classification = state.get("classification", "reviewable")
            if self.skip_broken.isChecked() and selected_filter not in {"Broken / excluded", "All scanned"} and classification == "broken": continue
            if selected_filter == "Review queue" and (classification != "reviewable" or status != "unreviewed"): continue
            if selected_filter == "Broken / excluded" and classification != "broken": continue
            if selected_filter == "All scanned": pass
            elif selected_filter not in {"Review queue", "Broken / excluded"} and status != wanted: continue
            if query and query not in record.display.lower() and query not in (record.entry or "").lower(): continue
            matches.append(record)
        self.filtered_records = matches
        self.filtered_index = {record.key: index for index, record in enumerate(matches)}
        page_count = max(1, (len(matches) + MAX_QUEUE_ROWS - 1) // MAX_QUEUE_ROWS)
        self.queue_page = min(self.queue_page, page_count - 1)
        start = self.queue_page * MAX_QUEUE_ROWS
        self.visible = matches[start:start + MAX_QUEUE_ROWS]
        self.queue.blockSignals(True); self.queue.clear()
        for record in self.visible:
            state = self.item_state(record); status = state.get("status", "unreviewed"); marker = {"archived": "▣", "used": "✓", "skipped": "»", "unreviewed": "·"}.get(status, "·"); broken = f"  · {state.get('reason')}" if state.get("classification") == "broken" else ""; item = QListWidgetItem(f"{marker}  {record.display}{broken}"); self.queue.addItem(item)
        self.queue.blockSignals(False)
        self.visible_index = {record.key: index for index, record in enumerate(self.visible)}
        if matches:
            first = start + 1; last = min(start + len(self.visible), len(matches)); self.page_label.setText(f"Showing {first:,}–{last:,} of {len(matches):,} matching fonts · page {self.queue_page + 1}/{page_count}")
        else:
            self.page_label.setText("No fonts match this view.")
        if select_first and self.visible: self.queue.setCurrentRow(0)
        elif not self.visible: self.clear_current("No fonts match this view.")


    def previous_queue_page(self) -> None:
        if self.queue_page > 0:
            self.queue_page -= 1
            self.refresh_list(select_first=True, reset_page=False)

    def next_queue_page(self) -> None:
        page_count = getattr(self, "page_count", max(1, (len(self.filtered_records) + MAX_QUEUE_ROWS - 1) // MAX_QUEUE_ROWS))
        if self.queue_page + 1 < page_count:
            self.queue_page += 1
            self.refresh_list(select_first=True, reset_page=False)

    def queue_selected(self, row: int) -> None:
        if 0 <= row < len(self.visible):
            self.current = self.visible[row]
            state = self.analyze_record(self.current, deep=True)
            # DB persistence now happens inside analyze_record; no save_json needed here
            if state.get("classification") == "broken" and self.skip_broken.isChecked() and self.filter.currentText() not in {"Broken / excluded", "All scanned"}:
                self.status_label.setText(f"Auto-skipped {self.current.display}: {state.get('reason')}")
                self.refresh_list()
                # Do not immediately re-enter queue_selected here: a page can
                # contain many broken fonts, and recursive auto-skipping could
                # overflow the UI stack. Leave the queue ready for the next
                # explicit selection/navigation action instead.
                self.current = None; self.queue.clearSelection()
                if not self.visible: self.clear_current("No reviewable fonts remain in this view.")
                return
            self.render_current()

    def copy_queue_selection(self) -> None:
        item = self.queue.currentItem()
        if not item:
            self.status_label.setText("Select a queue item first, then copy it.")
            return
        QApplication.clipboard().setText(item.text())
        self.status_label.setText("Selected queue text copied to the clipboard.")

    def copy_current_details(self) -> None:
        if not self.current:
            self.status_label.setText("Select a font first, then copy its details.")
            return
        details = f"{self.name_label.text()}\n{self.facts_label.text()}"
        QApplication.clipboard().setText(details)
        self.status_label.setText("Font details copied to the clipboard.")

    def copy_specimen_text(self) -> None:
        specimen = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ\n"
            "abcdefghijklmnopqrstuvwxyz\n"
            "0123456789\n"
            "! ? . , : ; / & @ # % + - = ( ) [ ] { }\n\n"
            f"{SAMPLE_SENTENCE}"
        )
        QApplication.clipboard().setText(specimen)
        self.status_label.setText("Specimen text copied to the clipboard.")

    def materialize(self, record: FontRecord) -> Path:
        return Path(record.source)

    def renderable_path(self, record: FontRecord) -> Path:
        source = self.materialize(record); render_source = source
        if source.suffix.lower() in {".woff", ".woff2"}:
            converted = CACHE_DIR / "renderable" / (hashlib.sha256(record.key.encode()).hexdigest()[:20] + ".otf")
            if not converted.exists():
                converted.parent.mkdir(parents=True, exist_ok=True); font = TTFont(source); font.flavor = None; font.save(converted); font.close()
            render_source = converted
        return render_source

    def render_path(self, record: FontRecord) -> Path:
        render_source = self.renderable_path(record)
        output = CACHE_DIR / "renders" / hashlib.sha256((record.key + ":combined-v3").encode()).hexdigest()[:20]; output.mkdir(parents=True, exist_ok=True); image_path = output / "main" / "specimen-alphabet-numerals.png"
        if not image_path.exists():
            result = subprocess.run([sys.executable, str(RENDERER), str(render_source), str(output), "--name", record.display.title(), "--basic", "--fast-png"], capture_output=True, text=True)
            if result.returncode != 0: raise RuntimeError((result.stdout + result.stderr).strip()[-1000:])
        combined_path = output / "combined-specimen.png"
        if not combined_path.exists() or combined_path.stat().st_mtime_ns < image_path.stat().st_mtime_ns:
            base = Image.open(image_path).convert("RGB")
            width, height = base.size
            sentence_height = 430
            combined = Image.new("RGB", (width, height + sentence_height), (8, 8, 10))
            combined.paste(base, (0, 0))
            draw = ImageDraw.Draw(combined)
            sentence_font_size = 148
            sentence_font = ImageFont.truetype(str(render_source), sentence_font_size)
            sentence = SAMPLE_SENTENCE
            while sentence_font_size > 44 and draw.textlength(sentence, font=sentence_font) > width - 180:
                sentence_font_size -= 4
                sentence_font = ImageFont.truetype(str(render_source), sentence_font_size)
            label_font = ImageFont.truetype(str(render_source), 42)
            label = "Sentence"
            label_width = draw.textlength(label, font=label_font)
            sentence_width = draw.textlength(sentence, font=sentence_font)
            draw.text(((width - label_width) / 2, height + 45), label, font=label_font, fill=(155, 155, 155))
            draw.text(((width - sentence_width) / 2, height + 145), sentence, font=sentence_font, fill=(248, 248, 245))
            combined.save(combined_path, format="PNG")
        return combined_path

    def inspect(self, record: FontRecord) -> str:
        return self.inspect_path(self.materialize(record))

    def inspect_path(self, path: Path) -> str:
        font = TTFont(path); cmap = font.getBestCmap() or {}; letters = sum(1 for c in cmap if 0x41 <= c <= 0x5A or 0x61 <= c <= 0x7A)
        dates = "font dates unavailable"
        if "head" in font:
            def format_date(value) -> str:
                try:
                    # OpenType head timestamps are seconds since 1904-01-01
                    # (the Macintosh epoch), not seconds after 1970.
                    return datetime.fromtimestamp(value - 2082844800, tz=timezone.utc).strftime("%Y-%m-%d")
                except (OverflowError, OSError, TypeError, ValueError):
                    return "unknown"
            head = font["head"]; dates = f"created={format_date(head.created)} · modified={format_date(head.modified)}"
        name_values: dict[int, str] = {}
        for record in font["name"].names if "name" in font else []:
            if record.nameID in {8, 9, 11, 12, 13, 14} and record.nameID not in name_values:
                try:
                    value = record.toUnicode().strip()
                    if value:
                        name_values[record.nameID] = value
                except Exception:
                    continue
        author = name_values.get(9) or name_values.get(8) or "unknown"
        license_text = name_values.get(13, "unknown")
        url = name_values.get(14) or name_values.get(12) or name_values.get(11) or "unknown"
        facts = f"{len(font.getGlyphOrder())} glyphs  ·  {letters}/52 basic letters  ·  {dates}  ·  author={author}  ·  license={license_text}  ·  url={url}  ·  fsType={font['OS/2'].fsType if 'OS/2' in font else 'unknown'}  ·  legacy kern={'yes' if 'kern' in font else 'no'}  ·  GPOS={'yes' if 'GPOS' in font else 'no'}  ·  GSUB={'yes' if 'GSUB' in font else 'no'}"; font.close(); return facts

    def render_current(self, _mode=None) -> None:
        """Show the specimen instantly when cached; render in the background otherwise.

        Rendering (subprocess + font inspection) has moved off the UI thread, so
        switching fonts stays responsive even for never-seen fonts. Results are
        cached in memory per font key and the images resize lazily on window
        resize without re-decoding the originals.
        """
        if not self.current: return
        current = self.current
        key = current.key
        self.name_label.setText(pretty_display(current.display))
        if key in self._pixmap_orig_cache:
            self._set_cached_preview(key)
            if self._facts_cache.get(key):
                self.facts_label.setText(self._facts_cache[key])
            self.status_label.setText("Combined specimen rendered.")
        else:
            self.preview.clear(); self.preview.setText("Rendering specimen…")
            self.facts_label.clear()
            self._request_render([current], replace=True)
        self._prefetch_adjacent()

    def _request_render(self, records: list[FontRecord], replace: bool = False) -> None:
        """Queue a background render batch, starting it if none is running."""
        batch = [r for r in records if r.key not in self._pixmap_orig_cache]
        if not batch:
            return
        if self._render_thread and self._render_thread.isRunning():
            if replace and self._render_worker is not None:
                # A freshly selected font takes priority: cancel the in-flight
                # prefetch batch and render it as soon as the thread drains.
                self._render_worker.cancelled = True
                self._pending_renders = batch
            elif replace:
                self._pending_renders = batch
            else:
                seen = {r.key for r in self._pending_renders}
                self._pending_renders.extend(r for r in batch if r.key not in seen)
            return
        self._start_render_batch(batch)

    def _start_render_batch(self, records: list[FontRecord]) -> None:
        if self._closing:
            return
        self._render_thread = QThread(self)
        self._render_worker = SpecimenRenderWorker(self, records)
        self._render_worker.cancelled = False
        self._render_worker.moveToThread(self._render_thread)
        self._render_thread.started.connect(self._render_worker.run)
        self._render_worker.ready.connect(self._on_render_ready)
        self._render_worker.failed.connect(self._on_render_failed)
        self._render_worker.done.connect(self._render_thread.quit)
        self._render_worker.done.connect(self._render_worker.deleteLater)
        self._render_thread.finished.connect(self._render_thread.deleteLater)
        self._render_thread.finished.connect(self._render_thread_finished)
        self._render_thread.start()

    def _render_thread_finished(self) -> None:
        self._render_thread = None
        self._render_worker = None
        if self._closing:
            return
        if self._pending_renders:
            batch = self._pending_renders
            self._pending_renders = []
            self._start_render_batch(batch)

    def _on_render_ready(self, key, path, facts, _note) -> None:
        self._facts_cache[key] = facts
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            if self.current and self.current.key == key:
                self.preview.clear(); self.preview.setText(f"Font could not be rendered.\n\n{path}")
                self.facts_label.setText(facts or "Source load/render failed.")
                self.status_label.setText("Font render failed; the font remains selected for review.")
            return
        self._pixmap_orig_cache[key] = pixmap
        self._trim_pixmap_cache()
        if self.current and self.current.key == key:
            self._set_cached_preview(key)
            self.facts_label.setText(facts)
            self.status_label.setText("Combined specimen rendered.")

    def _on_render_failed(self, key, message) -> None:
        if self.current and self.current.key == key:
            self.preview.clear(); self.preview.setText(f"Font could not be rendered.\n\n{message}")
            self.facts_label.setText("Source load/render failed.")
            self.status_label.setText("Font render failed; the font remains selected for review.")

    def _prefetch_adjacent(self) -> None:
        """Eagerly render the next couple of fonts so Next feels instant."""
        start = max(self.queue.currentRow(), 0)
        wanted: list[FontRecord] = []
        for record in self.visible[start + 1:]:
            if record.key not in self._pixmap_orig_cache:
                wanted.append(record)
                if len(wanted) >= 2:
                    break
        if wanted:
            self._request_render(wanted, replace=False)

    def _set_cached_preview(self, key: str) -> bool:
        orig = self._pixmap_orig_cache.get(key)
        if orig is None:
            return False
        size = self.preview.size()
        scaled = self._pixmap_cache.get(key)
        if scaled is None or scaled.size() != size:
            scaled = orig.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self._pixmap_cache[key] = scaled
        self.preview.setPixmap(scaled)
        return True

    def _trim_pixmap_cache(self, limit: int = 60) -> None:
        while len(self._pixmap_orig_cache) > limit:
            oldest = next(iter(self._pixmap_orig_cache))
            self._pixmap_orig_cache.pop(oldest, None)
            self._pixmap_cache.pop(oldest, None)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._pixmap_cache.clear()

    def clear_current(self, message: str) -> None:
        self.current = None; self.preview.clear(); self.preview.setText(message); self.name_label.setText("No font selected"); self.facts_label.clear(); self.status_label.setText(message)

    def set_status(self, status: str) -> None:
        if not self.current: return
        current = self.current
        old_row = self.visible_index.get(current.key, -1)
        # Update in-memory cache
        state = self.item_state(current)
        state["status"] = status
        # Persist to SQLite
        self.db.upsert_review(
            file_key=current.key,
            status=status,
            classification=state.get("classification", "reviewable"),
            broken_reason=state.get("reason", ""),
            outline_checked=int(bool(state.get("outline_checked", False))),
            family_key=state.get("family", ""),
            family_label=state.get("family_label", ""),
        )
        self.refresh_list()
        if self.visible:
            self.queue.setCurrentRow(min(max(old_row, 0), len(self.visible) - 1))

    def family_info(self, record: FontRecord) -> FamilyInfo:
        """The family a font reports, cached per session and mirrored into the index."""
        info = self.family_cache.get(record.key)
        if info is None:
            info = resolve_family(record.display, read_family_metadata(self.materialize(record)))
            self.family_cache[record.key] = info
            # Persist family metadata to DB so find_family_candidates can use the index
            self.db.update_font_family_meta(record.key, info.key, info.label, info.style)
        return info

    def family_for_record(self, record: FontRecord) -> str:
        return self.family_info(record).key

    def family_label_for_record(self, record: FontRecord) -> str:
        return self.family_info(record).label

    def find_family_members(self, target_record: FontRecord) -> list[FontRecord]:
        """Find all styles belonging to the same family using DB candidate pre-filtering and list adjacency."""
        target_info = self.family_info(target_record)
        family_key = target_info.key
        target_path = Path(target_record.source)
        target_dir = str(target_path.parent)
        prefix = family_key[:3] if len(family_key) >= 3 else family_key

        # 1. Fetch candidates from database (same directory + prefix matches, ordered alphabetically)
        if self.vault_id is not None:
            legacy_key = " ".join(target_info.label.casefold().split())
            db_candidates = self.db.find_family_candidates(
                self.vault_id, target_dir, prefix, family_key=family_key, legacy_family_key=legacy_key
            )
            candidates = [
                FontRecord(key=r["file_key"], display=r["display"], source=r["file_path"])
                for r in db_candidates
            ]
        else:
            candidates = []
            for r in self.records:
                r_path = Path(r.source)
                if r_path.parent == target_path.parent or (prefix and prefix in r.display.casefold()):
                    candidates.append(r)
            if not candidates:
                candidates = self.records

        # 2. Match family members
        members: list[FontRecord] = []
        seen_keys: set[str] = set()

        def belongs_to_family(r: FontRecord) -> bool:
            return family_member_matches(target_info, self.family_info(r))

        # First pass: check candidates in the same directory and prefix matches
        for r in candidates:
            if r.key in seen_keys:
                continue
            if belongs_to_family(r):
                members.append(r)
                seen_keys.add(r.key)

        # Second pass: Check adjacent neighbors in the visible queue list
        # Inspect preceding and succeeding items in the queue list for contiguous family members
        if getattr(self, "visible", None):
            target_idx = -1
            for idx, r in enumerate(self.visible):
                if r.key == target_record.key:
                    target_idx = idx
                    break
            if target_idx >= 0:
                # Walk backward in list
                curr = target_idx - 1
                while curr >= 0:
                    cand = self.visible[curr]
                    if belongs_to_family(cand):
                        if cand.key not in seen_keys:
                            members.append(cand)
                            seen_keys.add(cand.key)
                        curr -= 1
                    else:
                        break
                # Walk forward in list
                curr = target_idx + 1
                while curr < len(self.visible):
                    cand = self.visible[curr]
                    if belongs_to_family(cand):
                        if cand.key not in seen_keys:
                            members.append(cand)
                            seen_keys.add(cand.key)
                        curr += 1
                    else:
                        break

        # Ensure target_record itself is always included
        if not any(m.key == target_record.key for m in members):
            members.insert(0, target_record)

        # Sort members nicely by display name
        members.sort(key=lambda item: item.display.lower())
        return members

    def skip_family(self) -> None:
        if not self.current:
            return
        family = self.family_for_record(self.current)
        family_label = self.family_label_for_record(self.current)
        members = self.find_family_members(self.current)
        keys = [r.key for r in members]
        # Bulk-write to SQLite in one transaction
        self.db.update_reviews_bulk(keys, "skipped", family, family_label)
        # Update in-memory cache
        for record in members:
            st = self.item_state(record)
            st["status"] = "skipped"; st["family"] = family; st["family_label"] = family_label
        self.filter.setCurrentText("Review queue")
        self.refresh_list()
        if self.visible:
            self.queue.setCurrentRow(0)
        else:
            self.clear_current("No unreviewed font families remain in this view.")
        self.status_label.setText(f"Skipped family: {family_label} ({len(members)} style(s)).")

    def archive_family(self) -> None:
        if not self.current:
            return
        family = self.family_for_record(self.current)
        family_label = self.family_label_for_record(self.current)
        members = self.find_family_members(self.current)
        keys = [r.key for r in members]
        # Bulk-write to SQLite in one transaction
        self.db.update_reviews_bulk(keys, "archived", family, family_label)
        # Update in-memory cache
        for record in members:
            st = self.item_state(record)
            st["status"] = "archived"; st["family"] = family; st["family_label"] = family_label
        self.filter.setCurrentText("Review queue")
        self.refresh_list()
        if self.visible:
            self.queue.setCurrentRow(0)
        else:
            self.clear_current("No unreviewed font families remain in this view.")
        self.status_label.setText(f"Archived family: {family_label} ({len(members)} style(s)).")

    def mark_used_family(self) -> None:
        if not self.current:
            return
        family = self.family_for_record(self.current)
        family_label = self.family_label_for_record(self.current)
        members = self.find_family_members(self.current)
        source_dir = str(Path(self.current.source).parent.resolve())
        safe_family = re.sub(r"[^A-Za-z0-9._-]+", "_", family_label).strip("._") or "unnamed-family"
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        used_numbers = []
        for child in INPUT_DIR.iterdir():
            if child.is_dir():
                match = re.match(r"^(\d+)-", child.name)
                if match:
                    used_numbers.append(int(match.group(1)))
        next_number = max(used_numbers, default=0) + 1
        destination_dir = INPUT_DIR / f"{next_number}-{safe_family}"
        destination_dir.mkdir(parents=True, exist_ok=True)
        copied = []
        copied_records = []
        seen_hashes: dict[str, str] = {}
        for record in members:
            source = self.materialize(record)
            digest = hashlib.sha1(source.read_bytes()).hexdigest()
            if digest in seen_hashes:
                copied.append({"source": str(source), "display": record.display, "style": self.family_info(record).style, "duplicate_of": seen_hashes[digest]})
                copied_records.append(record)
                continue
            destination = destination_dir / source.name
            if destination.exists():
                destination = destination_dir / f"{source.stem}__{digest[:8]}{source.suffix}"
            shutil.copy2(source, destination)
            seen_hashes[digest] = str(destination)
            copied.append({"source": str(source), "copied_to": str(destination), "display": record.display, "style": self.family_info(record).style})
            copied_records.append(record)
        for record in copied_records:
            self.item_state(record)["status"] = "used"
            self.item_state(record)["family"] = family
            self.item_state(record)["family_label"] = family_label
        # Bulk-write "used" status to SQLite for all copied records
        copied_keys = [r.key for r in copied_records]
        self.db.update_reviews_bulk(copied_keys, "used", family, family_label)
        manifest_payload = {
            "family": family_label,
            "family_key": family,
            "source_directory": source_dir,
            "files": copied,
            "duplicate_files_skipped": len(members) - len(seen_hashes),
        }
        (destination_dir / "font-vault-manifest.json").write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")
        # Also write a clear, dedicated text file detailing the source directory
        (destination_dir / "source-directory.txt").write_text(
            f"Font Family: {family_label}\n"
            f"Original Source Directory: {source_dir}\n"
            f"Extracted Files Count: {len(copied)}\n",
            encoding="utf-8"
        )
        self.filter.setCurrentText("Review queue")
        self.refresh_list()
        if self.visible:
            self.queue.setCurrentRow(0)
        else:
            self.clear_current("No unreviewed font families remain in this view.")
        self.status_label.setText(f"Marked used and copied family: {family_label} ({len(seen_hashes)} unique file(s), {len(members) - len(seen_hashes)} duplicates skipped).")

    def next(self) -> None:
        if not self.visible:
            return
        row = self.queue.currentRow()
        if row < 0:
            self.queue.setCurrentRow(0)
            return
        if row + 1 < len(self.visible):
            self.queue.setCurrentRow(row + 1)
        else:
            page_count = getattr(self, "page_count", 1)
            if self.queue_page + 1 < page_count:
                self.queue_page += 1
                self.refresh_list(select_first=True, reset_page=False)
            else:
                if self.queue_page != 0:
                    self.queue_page = 0
                    self.refresh_list(select_first=True, reset_page=False)
                else:
                    self.queue.setCurrentRow(0)

    def previous(self) -> None:
        if not self.visible:
            return
        row = self.queue.currentRow()
        if row <= 0:
            if self.queue_page > 0:
                self.queue_page -= 1
                self.refresh_list(select_first=False, reset_page=False)
                if self.visible:
                    self.queue.setCurrentRow(len(self.visible) - 1)
            else:
                page_count = getattr(self, "page_count", 1)
                if page_count > 1:
                    self.queue_page = page_count - 1
                    self.refresh_list(select_first=False, reset_page=False)
                    if self.visible:
                        self.queue.setCurrentRow(len(self.visible) - 1)
                else:
                    if self.visible:
                        self.queue.setCurrentRow(len(self.visible) - 1)
        else:
            self.queue.setCurrentRow(row - 1)

    def randomize(self) -> None:
        total = getattr(self, "total_matches", len(self.visible))
        if total <= 1:
            return
        rand_idx = self.rng.randrange(total)
        target_page, target_row = divmod(rand_idx, MAX_QUEUE_ROWS)
        if target_page != self.queue_page:
            self.queue_page = target_page
            self.refresh_list(select_first=False, reset_page=False)
        if 0 <= target_row < self.queue.count():
            self.queue.setCurrentRow(target_row)

    def create_installable_copy(self) -> None:
        if not self.current: return
        source = self.materialize(self.current); target, _ = QFileDialog.getSaveFileName(self, "Save cleaned working copy", source.name, "Font file (*.ttf *.otf *.woff *.woff2);;All files (*)")
        if not target: return
        answer = QMessageBox.question(self, "Create working copy", "This changes only the copy's fsType embedding flag to 0. It does not change the original or grant licensing rights. Continue?")
        if answer != QMessageBox.StandardButton.Yes: return
        try:
            font = TTFont(source); font["OS/2"].fsType = 0; font.flavor = ("woff" if source.suffix.lower() == ".woff" else "woff2" if source.suffix.lower() == ".woff2" else None); font.save(target); font.close(); self.status_label.setText(f"Saved working copy: {target}")
        except Exception as error: QMessageBox.critical(self, "Could not create copy", str(error))


def main() -> None:
    app = QApplication(sys.argv); window = FontVaultWindow(); window.show(); sys.exit(app.exec())


if __name__ == "__main__": main()
