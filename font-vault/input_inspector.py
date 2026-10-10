#!/usr/bin/env python3
"""Input Inspector: verify staged font families under font-factory/input.

Font Vault's "Mark used family" copies fonts into numbered folders under
font-factory/input/. This app lists those folders (one row per font inside the
selected folder) so stray fonts in a family can be spotted. Each row can send
its font back to the folder it was copied from, or delete it.
"""

from __future__ import annotations

import filecmp
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSplitter,
    QVBoxLayout, QWidget,
)


ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "font-factory" / "input"
CACHE_DIR = Path(__file__).resolve().parent / "data" / "cache" / "inspector"
DELETED_LOG = INPUT_DIR / "deleted-fonts.md"
FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}

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


def natural_key(text: str) -> list:
    """Sort keys so folder names like 2-x come before 10-y."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def count_fonts(folder: Path) -> int:
    try:
        return sum(1 for p in folder.iterdir() if p.suffix.lower() in FONT_EXTENSIONS)
    except OSError:
        return 0


def renderable_path(path: Path) -> Path:
    """Convert WOFF/WOFF2 to OTF once so PIL can render it."""
    if path.suffix.lower() not in {".woff", ".woff2"}:
        return path
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    converted = CACHE_DIR / (hashlib.sha256(str(path).encode()).hexdigest()[:20] + ".otf")
    if not converted.exists():
        font = TTFont(path)
        font.flavor = None
        font.save(converted)
        font.close()
    return converted


def render_strip(path: Path) -> Path:
    """Render one combined strip (alphabet, digits, punctuation), cached on disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        stat = path.stat()
        seed = f"{path}:{stat.st_mtime_ns}:{stat.st_size}"
    except OSError:
        seed = str(path)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
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
    """Find the original location a staged font was copied from."""
    manifest = folder / "font-vault-manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        for entry in data.get("files", []):
            copied_to = str(entry.get("copied_to") or "")
            source = entry.get("source")
            if source and Path(copied_to).name == filename:
                return Path(source)
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


class FontRow(QFrame):
    """One staged font: name + mark/return/delete buttons over a full-width preview strip."""

    activated = Signal()

    def __init__(self, path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.path = path
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
        self.use_btn = QPushButton("In Use")
        self.use_btn.setCheckable(True)
        self.use_btn.setObjectName("useToggle")
        self.use_btn.setToolTip("Mark this font as In Use (stored in the folder's in-use.txt).")
        self.use_btn.setChecked(path.name in load_in_use(path.parent))
        head.addWidget(self.use_btn)
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
        self.build_ui()
        self.folder_list.currentRowChanged.connect(self.folder_selected)
        self._refresh_folders()
        if self.folders:
            self.load_folder(0)
        else:
            self.status.setText(f"No family folders found under {INPUT_DIR}")

    @staticmethod
    def styles() -> str:
        return """
        QWidget { background: #111315; color: #eeeae2; font-size: 13px; }
        QFrame#panel { background: #191c1f; border-radius: 10px; }
        QFrame#fontRow { background: #191c1f; border-radius: 8px; }
        QFrame#fontRow:hover { background: #1e2226; }
        QLabel#title { color: #f3f0e8; font-size: 21px; font-weight: 700; letter-spacing: 2px; }
        QLabel#folderTitle { color: #d5a85e; font-size: 17px; font-weight: 700; }
        QLabel#rowName { color: #dedbd3; font-size: 13px; font-weight: 600; }
        QLabel#muted, QLabel#status { color: #9ca5a8; }
        QListWidget { background: #191c1f; border: 0; color: #dedbd3; outline: 0; }
        QListWidget::item { padding: 8px 7px; border-radius: 5px; }
        QListWidget::item:selected { background: #6f5839; color: #fff9ef; }
        QPushButton { background: #2a2f33; color: #eeeae2; border: 0; border-radius: 6px; padding: 8px 12px; }
        QPushButton:hover { background: #394148; }
        QPushButton:disabled { color: #6a7174; background: #21252a; }
        QPushButton#primary { background: #d5a85e; color: #141414; font-weight: 700; }
        QPushButton#primary:hover { background: #efc777; }
        QPushButton#useToggle:checked { background: #d5a85e; color: #141414; font-weight: 700; }
        QPushButton#useToggle:checked:hover { background: #efc777; }
        QPushButton#danger { background: #3a2622; color: #e6b0a3; }
        QPushButton#danger:hover { background: #55352f; }
        QScrollArea { border: 0; background: transparent; }
        QScrollBar:vertical { background: #14171a; width: 11px; border-radius: 5px; }
        QScrollBar::handle:vertical { background: #3a4246; border-radius: 5px; min-height: 30px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
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
        outer.addLayout(header)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.prev_btn = self.button("◀ Previous", self.go_prev)
        self.next_btn = self.button("Next ▶", self.go_next, primary=True)
        toolbar.addWidget(self.prev_btn)
        toolbar.addWidget(self.next_btn)
        toolbar.addWidget(self.button("Next Unmarked →", self.next_unmarked))
        toolbar.addStretch()
        toolbar.addWidget(self.button("↻ Refresh", self.refresh_action))
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
        label = QLabel("FAMILY FOLDERS")
        label.setObjectName("muted")
        side_layout.addWidget(label)
        self.folder_list = QListWidget()
        side_layout.addWidget(self.folder_list, 1)
        hint = QLabel("One preview row per font in\nthe selected folder.\n\n↩ Return sends a stray font\nback where it came from.")
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
        self.status = QLabel("Choose a family folder to inspect.")
        self.status.setObjectName("status")
        outer.addWidget(self.status)

    def _refresh_folders(self, select: int | None = None) -> None:
        if INPUT_DIR.is_dir():
            folders = [
                p for p in INPUT_DIR.iterdir()
                if p.is_dir() and not p.name.startswith(".")
            ]
            folders.sort(key=lambda p: natural_key(p.name))
        else:
            folders = []
        self.folders = folders
        self.folder_list.blockSignals(True)
        self.folder_list.clear()
        for folder in folders:
            item = QListWidgetItem(f"{folder.name}  ·  {count_fonts(folder)}")
            item.setData(Qt.ItemDataRole.UserRole, str(folder))
            self.folder_list.addItem(item)
        if select is not None and folders:
            self.folder_list.setCurrentRow(min(max(select, 0), len(folders) - 1))
        self.folder_list.blockSignals(False)

    def folder_selected(self, row: int) -> None:
        if 0 <= row < len(self.folders) and row != self.current_idx:
            self.load_folder(row)

    def load_folder(self, idx: int) -> None:
        if not (0 <= idx < len(self.folders)):
            return
        self.current_idx = idx
        if self.folder_list.currentRow() != idx:
            self.folder_list.blockSignals(True)
            self.folder_list.setCurrentRow(idx)
            self.folder_list.blockSignals(False)
        folder = self.folders[idx]
        try:
            fonts = [
                p for p in folder.iterdir()
                if p.is_file() and p.suffix.lower() in FONT_EXTENSIONS
            ]
        except OSError:
            fonts = []
        fonts.sort(key=lambda p: natural_key(p.stem))
        self.folder_title.setText(folder.name)
        self.count_label.setText(
            f"family {idx + 1}/{len(self.folders)}  ·  {len(fonts)} font(s)"
        )
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < len(self.folders) - 1)
        self._clear_rows()
        if not fonts:
            empty = QLabel("No font files in this folder.")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.rows_layout.addWidget(empty)
            self.rows_layout.addStretch()
            self.status.setText(f"{folder.name}: no font files.")
            return
        for path in fonts:
            row = FontRow(path)
            row.activated.connect(lambda r=row: self._activate_row(r))
            row.use_btn.toggled.connect(lambda state, p=path: self.toggle_in_use(p, state))
            row.return_btn.clicked.connect(lambda _=False, p=path: self.return_font(p))
            row.delete_btn.clicked.connect(lambda _=False, p=path: self.delete_font(p))
            self.rows_layout.addWidget(row)
            self.rows.append(row)
        self.rows_layout.addStretch()
        self.status.setText(f"Loaded {len(fonts)} font(s) from {folder.name}.")

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

    def next_unmarked(self) -> None:
        """Jump to the next row that is not marked In Use (wraps within the folder)."""
        if not self.rows:
            return
        start = 0
        if self.active_row in self.rows:
            start = self.rows.index(self.active_row) + 1
        order = list(range(start, len(self.rows))) + list(range(0, start))
        for index in order:
            row = self.rows[index]
            if not row.use_btn.isChecked():
                self._activate_row(row, scroll=True)
                self.status.setText(
                    f"Next unmarked: {row.path.name} ({index + 1}/{len(self.rows)})"
                )
                return
        self.status.setText(
            "All fonts in this folder are marked In Use — use Next ▶ for the next family."
        )

    def go_prev(self) -> None:
        if self.current_idx > 0:
            self.load_folder(self.current_idx - 1)

    def go_next(self) -> None:
        if self.current_idx < len(self.folders) - 1:
            self.load_folder(self.current_idx + 1)

    def refresh_action(self) -> None:
        previous = max(self.current_idx, 0)
        self._refresh_folders(select=previous)
        if self.folders:
            self.load_folder(min(previous, len(self.folders) - 1))
            self.status.setText(f"Refreshed — {len(self.folders)} family folder(s).")
        else:
            self.status.setText(f"No family folders found under {INPUT_DIR}")

    def reload_current(self) -> None:
        if not self.folders:
            return
        idx = min(max(self.current_idx, 0), len(self.folders) - 1)
        self._refresh_folders(select=idx)
        if self.folders:
            self.load_folder(idx)
        else:
            self._clear_rows()
            self.folder_title.setText("No folder selected")
            self.count_label.setText("")

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
                source.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(source))
                action = f"moved back to {source.parent}/"
        except OSError as error:
            QMessageBox.critical(self, "Could not return font", str(error))
            return
        prune_manifest(folder, path.name)
        set_in_use(folder, path.name, False)
        self.status.setText(f"Returned {path.name}: {action}.")
        self.reload_current()

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
        try:
            path.unlink()
        except OSError as error:
            QMessageBox.critical(self, "Could not delete font", str(error))
            return
        prune_manifest(path.parent, path.name)
        set_in_use(path.parent, path.name, False)
        log_error = log_deletion(path, source)
        if log_error:
            self.status.setText(
                f"Deleted {path.name}, but the deletion log could not be updated: {log_error}"
            )
        else:
            self.status.setText(
                f"Deleted {path.name} — recorded in input/deleted-fonts.md (not part of the family)."
            )
        self.reload_current()


def main() -> None:
    app = QApplication(sys.argv)
    window = InspectorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
