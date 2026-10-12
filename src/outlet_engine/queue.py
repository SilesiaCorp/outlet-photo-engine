"""Private durable queue: one worker thread per sheet, no automatic network calls."""
from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .approval import digest, proposal_hash, validate_manifest


def now() -> str:
    return datetime.now(UTC).isoformat()


class JobQueue:
    def __init__(self, path: Path):
        root = Path(__file__).resolve().parents[2]
        try:
            path.resolve().relative_to(root)
        except ValueError:
            pass
        else:
            raise ValueError("Kolejka produkcyjna musi pozostać poza repozytorium.")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
              operation_id TEXT PRIMARY KEY, resource TEXT NOT NULL,
              unit_key TEXT NOT NULL UNIQUE, proposal_sha256 TEXT NOT NULL,
              manifest TEXT NOT NULL, state TEXT NOT NULL, worker TEXT,
              receipt TEXT, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS workers (
              resource TEXT PRIMARY KEY, thread_id TEXT NOT NULL, host_id TEXT NOT NULL);
        """)

    def close(self):
        self.db.close()

    @staticmethod
    def resource(manifest: dict) -> str:
        # One writer for the whole spreadsheet, including both source tabs/queue.
        target = manifest["destination"]
        return digest([target["account_email"].casefold(), target["spreadsheet_id"]])

    def enqueue(self, manifest: dict) -> dict:
        validate_manifest(manifest)
        resource = self.resource(manifest)
        unit_key = digest([resource, manifest["physical_receipt_id"], manifest["identity"]["order_id"],
                           manifest["identity"]["order_product_id"], manifest["identity"]["sku"]])
        hashed = proposal_hash(manifest)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.db.execute("SELECT * FROM jobs WHERE operation_id=? OR unit_key=?",
                                       (manifest["operation_id"], unit_key)).fetchone()
            if existing:
                if existing["proposal_sha256"] != hashed:
                    raise ValueError("To przyjęcie ma już inną propozycję. Rozlicz istniejący wpis przed zmianą.")
                self.db.execute("COMMIT")
                return dict(existing)
            self.db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,'queued',NULL,NULL,?)", (
                manifest["operation_id"], resource, unit_key, hashed,
                json.dumps(manifest, ensure_ascii=False, allow_nan=False), now(),
            ))
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        return self.get(manifest["operation_id"])

    def register_worker(self, resource: str, thread_id: str, host_id: str = "local"):
        if not thread_id or not host_id:
            raise ValueError("Rejestruj rzeczywisty threadId i hostId po zakończeniu tworzenia rozmowy.")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            current = self.db.execute("SELECT * FROM workers WHERE resource=?", (resource,)).fetchone()
            if current and (current["thread_id"], current["host_id"]) != (thread_id, host_id):
                raise ValueError("Arkusz ma już inną rozmowę wykonawczą; nie uruchamiaj drugiego writera.")
            self.db.execute("INSERT OR IGNORE INTO workers VALUES (?,?,?)", (resource, thread_id, host_id))
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def worker(self, resource: str) -> dict | None:
        row = self.db.execute("SELECT * FROM workers WHERE resource=?", (resource,)).fetchone()
        return dict(row) if row else None

    def claim(self, resource: str, thread_id: str) -> dict | None:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            worker = self.worker(resource)
            if not worker or worker["thread_id"] != thread_id:
                raise ValueError("Rozmowa nie jest właścicielem zapisu tego arkusza.")
            active = self.db.execute("SELECT operation_id FROM jobs WHERE resource=? AND state IN ('claimed','write_pending')",
                                     (resource,)).fetchone()
            if active:
                raise ValueError("Poprzednia operacja jest aktywna lub niepewna; najpierw odczytaj jej stan.")
            row = self.db.execute("SELECT * FROM jobs WHERE resource=? AND state='queued' ORDER BY rowid LIMIT 1",
                                  (resource,)).fetchone()
            if row:
                self.db.execute("UPDATE jobs SET state='claimed',worker=?,updated_at=? WHERE operation_id=?",
                                (thread_id, now(), row["operation_id"]))
            self.db.execute("COMMIT")
            return self.get(row["operation_id"]) if row else None
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def update(self, operation_id: str, thread_id: str, state: str, receipt: dict | None = None):
        transitions = {
            "claimed": {"write_pending", "needs_data", "needs_review", "failed"},
            "write_pending": {"verified", "needs_review", "failed"},
            "needs_review": {"verified", "failed"},
        }
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.get(operation_id)
            if row["worker"] != thread_id or state not in transitions.get(row["state"], set()):
                raise ValueError("Niedozwolona zmiana stanu lub inny właściciel operacji.")
            if state == "verified" and (not receipt or receipt.get("verified") is not True
                                        or receipt.get("proposal_sha256") != row["proposal_sha256"]
                                        or not receipt.get("range") or not receipt.get("sheet_url")):
                raise ValueError("Ukończenie wymaga zgodnego odczytu wiersza, hasha i linku.")
            self.db.execute("UPDATE jobs SET state=?,receipt=?,updated_at=? WHERE operation_id=?",
                            (state, json.dumps(receipt, ensure_ascii=False), now(), operation_id))
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def get(self, operation_id: str) -> dict:
        row = self.db.execute("SELECT * FROM jobs WHERE operation_id=?", (operation_id,)).fetchone()
        if not row:
            raise ValueError("Nie znaleziono operacji.")
        return dict(row)
