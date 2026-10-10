"""SQLite persistence, indexing, and migration engine for Font Vault."""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("font_vault.db")

@dataclass
class FontItem:
    file_key: str
    file_path: str
    file_size: int
    mtime_ns: int
    stem: str
    display: str
    family_key: str
    family_label: str
    style: str
    status: str
    classification: str
    broken_reason: str
    outline_checked: int


class VaultDB:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_pragmas()
        self._create_schema()

    def _init_pragmas(self) -> None:
        cur = self.conn.cursor()
        cur.execute("PRAGMA journal_mode = WAL;")
        cur.execute("PRAGMA synchronous = NORMAL;")
        cur.execute("PRAGMA foreign_keys = ON;")
        cur.execute("PRAGMA temp_store = MEMORY;")
        cur.execute("PRAGMA cache_size = -64000;")  # 64MB cache

    def _create_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vaults (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                last_opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_query TEXT DEFAULT '',
                last_filter TEXT DEFAULT 'Review queue'
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS font_records (
                file_key TEXT PRIMARY KEY,
                vault_id INTEGER REFERENCES vaults(id) ON DELETE CASCADE,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL,
                stem TEXT NOT NULL,
                display TEXT NOT NULL,
                family_key TEXT DEFAULT '',
                family_label TEXT DEFAULT '',
                style TEXT DEFAULT 'Regular',
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                file_key TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'unreviewed',
                classification TEXT NOT NULL DEFAULT 'reviewable',
                broken_reason TEXT DEFAULT '',
                outline_checked INTEGER NOT NULL DEFAULT 0,
                family_key TEXT DEFAULT '',
                family_label TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)

        # Fast indices for search, queue filtering, and family grouping
        cur.execute("CREATE INDEX IF NOT EXISTS idx_font_vault ON font_records(vault_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_font_vault_display ON font_records(vault_id, display);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_font_family ON font_records(family_key);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_font_display ON font_records(display);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_review_status ON reviews(status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_review_class ON reviews(classification);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_review_family ON reviews(family_key);")
        self.conn.commit()

    def set_app_state(self, key: str, value: Any) -> None:
        val_str = json.dumps(value) if not isinstance(value, str) else value
        with self.conn:
            self.conn.execute(
                "INSERT INTO app_state(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, val_str)
            )

    def get_app_state(self, key: str, default: Any = None) -> Any:
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM app_state WHERE key = ?", (key,))
        row = cur.fetchone()
        if not row:
            return default
        try:
            return json.loads(row["value"])
        except Exception:
            return row["value"]

    def upsert_vault(self, path: Path) -> int:
        norm_path = str(path.resolve())
        name = path.name or norm_path
        with self.conn:
            self.conn.execute("""
                INSERT INTO vaults (path, name, last_opened_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(path) DO UPDATE SET
                    last_opened_at = CURRENT_TIMESTAMP,
                    name = excluded.name;
            """, (norm_path, name))
            cur = self.conn.execute("SELECT id FROM vaults WHERE path = ?", (norm_path,))
            return cur.fetchone()["id"]

    def get_vault_id(self, path: Path) -> int | None:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM vaults WHERE path = ?", (str(path.resolve()),))
        row = cur.fetchone()
        return row["id"] if row else None

    def update_vault_prefs(self, path: Path, query: str, filter_name: str) -> None:
        with self.conn:
            self.conn.execute("""
                UPDATE vaults SET last_query = ?, last_filter = ? WHERE path = ?
            """, (query, filter_name, str(path.resolve())))

    def get_vault_prefs(self, path: Path) -> tuple[str, str]:
        cur = self.conn.cursor()
        cur.execute("SELECT last_query, last_filter FROM vaults WHERE path = ?", (str(path.resolve()),))
        row = cur.fetchone()
        if row:
            return row["last_query"] or "", row["last_filter"] or "Review queue"
        return "", "Review queue"

    def list_recent_vaults(self) -> list[dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, path, name FROM vaults ORDER BY last_opened_at DESC LIMIT 25")
        return [dict(r) for r in cur.fetchall()]

    def count_vault_fonts(self, vault_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM font_records WHERE vault_id = ?", (vault_id,))
        return cur.fetchone()["c"]

    def bulk_insert_font_records(self, vault_id: int, records: list[dict[str, Any]]) -> None:
        with self.conn:
            self.conn.executemany("""
                INSERT OR IGNORE INTO font_records (
                    file_key, vault_id, file_path, file_size, mtime_ns, stem, display, family_key, family_label, style
                ) VALUES (
                    :file_key, :vault_id, :file_path, :file_size, :mtime_ns, :stem, :display, :family_key, :family_label, :style
                )
            """, [{**r, "vault_id": vault_id} for r in records])

    def update_font_family_meta(self, file_key: str, family_key: str, family_label: str, style: str) -> None:
        with self.conn:
            self.conn.execute("""
                UPDATE font_records
                SET family_key = ?, family_label = ?, style = ?
                WHERE file_key = ?
            """, (family_key, family_label, style, file_key))

    def get_review(self, file_key: str) -> dict[str, Any] | None:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT status, classification, broken_reason, outline_checked, family_key, family_label
            FROM reviews WHERE file_key = ?
        """, (file_key,))
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        d["reason"] = d["broken_reason"]
        return d

    def upsert_review(
        self,
        file_key: str,
        status: str | None = None,
        classification: str | None = None,
        broken_reason: str | None = None,
        outline_checked: int | bool | None = None,
        family_key: str | None = None,
        family_label: str | None = None,
        **kwargs: Any
    ) -> None:
        if broken_reason is None and "reason" in kwargs:
            broken_reason = kwargs["reason"]
        if outline_checked is not None:
            outline_checked = 1 if outline_checked else 0

        existing = self.get_review(file_key) or {
            "status": "unreviewed",
            "classification": "reviewable",
            "broken_reason": "",
            "outline_checked": 0,
            "family_key": "",
            "family_label": ""
        }
        st = status if status is not None else existing["status"]
        cl = classification if classification is not None else existing["classification"]
        br = broken_reason if broken_reason is not None else existing["broken_reason"]
        oc = outline_checked if outline_checked is not None else existing["outline_checked"]
        fk = family_key if family_key is not None else existing.get("family_key", "")
        fl = family_label if family_label is not None else existing.get("family_label", "")

        with self.conn:
            self.conn.execute("""
                INSERT INTO reviews (file_key, status, classification, broken_reason, outline_checked, family_key, family_label, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(file_key) DO UPDATE SET
                    status = excluded.status,
                    classification = excluded.classification,
                    broken_reason = excluded.broken_reason,
                    outline_checked = excluded.outline_checked,
                    family_key = CASE WHEN excluded.family_key != '' THEN excluded.family_key ELSE reviews.family_key END,
                    family_label = CASE WHEN excluded.family_label != '' THEN excluded.family_label ELSE reviews.family_label END,
                    updated_at = CURRENT_TIMESTAMP
            """, (file_key, st, cl, br, oc, fk, fl))

    def update_reviews_bulk(self, file_keys: list[str], status: str, family_key: str, family_label: str) -> None:
        with self.conn:
            self.conn.executemany("""
                INSERT INTO reviews (file_key, status, family_key, family_label, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(file_key) DO UPDATE SET
                    status = excluded.status,
                    family_key = excluded.family_key,
                    family_label = excluded.family_label,
                    updated_at = CURRENT_TIMESTAMP
            """, [(k, status, family_key, family_label) for k in file_keys])

    def find_family_candidates(
        self, vault_id: int, parent_dir: str, prefix: str, family_key: str = ""
    ) -> list[dict[str, Any]]:
        """Return candidate fonts in the same folder or sharing a prefix stem / family_key."""
        cur = self.conn.cursor()
        dir_pattern = f"{parent_dir}/%"
        prefix_pattern = f"{prefix}%" if prefix else ""

        cur.execute("""
            SELECT
                f.file_key,
                f.file_path,
                f.file_size,
                f.mtime_ns,
                f.stem,
                f.display,
                f.family_key,
                f.family_label,
                f.style,
                COALESCE(r.status, 'unreviewed') AS status,
                COALESCE(r.classification, 'reviewable') AS classification,
                COALESCE(r.broken_reason, '') AS broken_reason,
                COALESCE(r.broken_reason, '') AS reason,
                COALESCE(r.outline_checked, 0) AS outline_checked
            FROM font_records f
            LEFT JOIN reviews r ON f.file_key = r.file_key
            WHERE f.vault_id = ?
              AND (
                  f.file_path LIKE ?
                  OR (? != '' AND f.display LIKE ?)
                  OR (? != '' AND f.family_key = ?)
              )
            ORDER BY f.display ASC
        """, (vault_id, dir_pattern, prefix_pattern, prefix_pattern, family_key, family_key))
        return [dict(r) for r in cur.fetchall()]

    def _filter_clauses(self, filter_name: str, skip_broken: bool) -> tuple[list[str], list[Any]]:
        """Shared WHERE fragments + params for the queue views."""
        where_clauses: list[str] = []
        params: list[Any] = []
        filter_lower = filter_name.strip().lower()
        if filter_lower == "review queue":
            where_clauses.append("COALESCE(r.status, 'unreviewed') = 'unreviewed'")
            where_clauses.append("COALESCE(r.classification, 'reviewable') = 'reviewable'")
        elif filter_lower == "broken / excluded":
            where_clauses.append("COALESCE(r.classification, 'reviewable') = 'broken'")
        elif filter_lower == "all scanned":
            if skip_broken:
                where_clauses.append("COALESCE(r.classification, 'reviewable') != 'broken'")
        else:
            # Unreviewed, Used, Archived, Skipped
            where_clauses.append("COALESCE(r.status, 'unreviewed') = ?")
            params.append(filter_lower)
            if skip_broken:
                where_clauses.append("COALESCE(r.classification, 'reviewable') != 'broken'")
        return where_clauses, params

    def _query_filter_params(
        self,
        vault_id: int,
        query: str,
        filter_name: str,
        skip_broken: bool,
    ) -> tuple[list[str], list[Any]]:
        where_clauses = ["f.vault_id = ?"]
        params: list[Any] = [vault_id]
        extra, extra_params = self._filter_clauses(filter_name, skip_broken)
        where_clauses.extend(extra)
        params.extend(extra_params)
        if query.strip():
            where_clauses.append("f.display LIKE ?")
            params.append(f"%{query.strip()}%")
        return where_clauses, params

    def query_vault_fonts(
        self,
        vault_id: int,
        query: str = "",
        filter_name: str = "Review queue",
        skip_broken: bool = True,
        limit: int = 2000,
        offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        """Query fonts with instant indexed filtering and total count."""
        where_clauses, params = self._query_filter_params(vault_id, query, filter_name, skip_broken)
        where_sql = " AND ".join(where_clauses)

        # 1. Count query
        cur = self.conn.cursor()
        cur.execute(f"""
            SELECT COUNT(*) AS total
            FROM font_records f
            LEFT JOIN reviews r ON f.file_key = r.file_key
            WHERE {where_sql}
        """, params)
        total_count = cur.fetchone()["total"]

        # 2. Page slice query
        limit_val = -1 if limit <= 0 else limit
        cur.execute(f"""
            SELECT
                f.file_key,
                f.file_path,
                f.file_size,
                f.mtime_ns,
                f.stem,
                f.display,
                f.family_key,
                f.family_label,
                f.style,
                COALESCE(r.status, 'unreviewed') AS status,
                COALESCE(r.classification, 'reviewable') AS classification,
                COALESCE(r.broken_reason, '') AS broken_reason,
                COALESCE(r.broken_reason, '') AS reason,
                COALESCE(r.outline_checked, 0) AS outline_checked
            FROM font_records f
            LEFT JOIN reviews r ON f.file_key = r.file_key
            WHERE {where_sql}
            ORDER BY f.display ASC, f.file_key ASC
            LIMIT ? OFFSET ?
        """, [*params, limit_val, max(0, offset)])

        items = [dict(row) for row in cur.fetchall()]
        return items, total_count

    def find_filtered_index(
        self,
        vault_id: int,
        file_key: str,
        query: str = "",
        filter_name: str = "Review queue",
        skip_broken: bool = True,
    ) -> int | None:
        """Return the 0-based index of a font inside the current filtered view.

        Mirrors query_vault_fonts' filtering/ordering so navigation can jump
        straight to the exact page and row of a remembered font (for example
        the font you were on before Randomize), even when it lives on another
        page. Returns None when the font is not part of the current view.
        """
        cur = self.conn.cursor()
        cur.execute(
            "SELECT display FROM font_records WHERE vault_id = ? AND file_key = ?",
            (vault_id, file_key),
        )
        target = cur.fetchone()
        if not target:
            return None
        where_clauses, params = self._query_filter_params(vault_id, query, filter_name, skip_broken)
        where_sql = " AND ".join(where_clauses)
        # Confirm the target belongs to the current view before ranking.
        cur.execute(f"""
            SELECT COUNT(*) AS c
            FROM font_records f
            LEFT JOIN reviews r ON f.file_key = r.file_key
            WHERE {where_sql} AND f.file_key = ?
        """, [*params, file_key])
        if cur.fetchone()["c"] == 0:
            return None
        # Rank using the same (display, file_key) ordering as the page query.
        cur.execute(f"""
            SELECT COUNT(*) AS rank
            FROM font_records f
            LEFT JOIN reviews r ON f.file_key = r.file_key
            WHERE {where_sql} AND (f.display, f.file_key) <= (?, ?)
        """, [*params, target["display"], file_key])
        return cur.fetchone()["rank"] - 1

    def migrate_from_state_json(self, json_path: Path, force: bool = False) -> int:
        """Migrate legacy state.json into SQLite seamlessly (runs once unless forced)."""
        if not json_path.exists():
            return 0
        if not force and self.get_app_state("migrated_state_json"):
            return 0
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as err:
            logger.warning(f"Could not read state.json for migration: {err}")
            return 0

        # Migrate sources / vaults
        sources = data.get("sources", [])
        vaults_data = data.get("vaults", {})
        for s in sources:
            p = Path(s)
            if p.exists():
                v_id = self.upsert_vault(p)
                v_prefs = vaults_data.get(s, {})
                q = v_prefs.get("query", "")
                f = v_prefs.get("filter", "Review queue")
                self.update_vault_prefs(p, q, f)

        if data.get("last_source"):
            self.set_app_state("last_source", data.get("last_source"))

        # Migrate reviews / items
        items = data.get("items", {})
        migrated = 0
        with self.conn:
            for file_key, v in items.items():
                st = v.get("status", "unreviewed")
                cl = v.get("classification", "reviewable")
                br = v.get("reason", "")
                oc = 1 if v.get("outline_checked") else 0
                fk = v.get("family", "")
                fl = v.get("family_label", "")
                # Only insert items that deviate from unreviewed or have findings
                if st != "unreviewed" or cl == "broken" or fk:
                    self.conn.execute("""
                        INSERT INTO reviews (file_key, status, classification, broken_reason, outline_checked, family_key, family_label, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(file_key) DO UPDATE SET
                            status = excluded.status,
                            classification = excluded.classification,
                            broken_reason = excluded.broken_reason,
                            outline_checked = excluded.outline_checked,
                            family_key = excluded.family_key,
                            family_label = excluded.family_label
                    """, (file_key, st, cl, br, oc, fk, fl))
                    migrated += 1

        self.set_app_state("migrated_state_json", 1)
        return migrated

    def export_to_state_json(self, json_path: Path) -> None:
        """Export SQLite database back to state.json format for external backups."""
        data: dict[str, Any] = {
            "sources": [v["path"] for v in self.list_recent_vaults()],
            "last_source": self.get_app_state("last_source", "") or "",
            "vaults": {},
            "items": {}
        }
        for v in self.list_recent_vaults():
            p = Path(v["path"])
            q, f = self.get_vault_prefs(p)
            data["vaults"][v["path"]] = {"query": q, "filter": f}

        cur = self.conn.cursor()
        cur.execute("SELECT * FROM reviews")
        for r in cur.fetchall():
            row = dict(r)
            data["items"][row["file_key"]] = {
                "status": row["status"],
                "classification": row["classification"],
                "reason": row["broken_reason"],
                "outline_checked": bool(row["outline_checked"]),
                "family": row["family_key"],
                "family_label": row["family_label"],
            }
        tmp = json_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(json_path)

