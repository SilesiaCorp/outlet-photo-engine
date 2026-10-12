"""Shared local Base request budget, with immediate calls while budget is free."""
from __future__ import annotations

import sqlite3
import time
from contextlib import closing
from pathlib import Path


class RequestBudget:
    def __init__(self, path: Path, account_key: str, *, capacity: int = 100,
                 window_seconds: float = 60, clock=time.time, sleep=time.sleep):
        if capacity < 1 or window_seconds <= 0:
            raise ValueError("Nieprawidłowy budżet żądań.")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path, self.account_key = path, account_key
        self.capacity, self.window = capacity, window_seconds
        self.clock, self.sleep = clock, sleep
        with closing(sqlite3.connect(path, timeout=10)) as db:
            db.execute("CREATE TABLE IF NOT EXISTS requests (account TEXT, at REAL)")
            db.execute("CREATE INDEX IF NOT EXISTS request_window ON requests(account,at)")
            db.commit()

    def acquire(self):
        while True:
            current = self.clock()
            with closing(sqlite3.connect(self.path, timeout=10)) as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("DELETE FROM requests WHERE at<=?", (current - self.window,))
                times = [row[0] for row in db.execute(
                    "SELECT at FROM requests WHERE account=? ORDER BY at", (self.account_key,))]
                if len(times) < self.capacity:
                    db.execute("INSERT INTO requests VALUES (?,?)", (self.account_key, current))
                    db.commit()
                    return
                wait = max(.01, times[0] + self.window - current + .01)
                db.commit()
            # Sleep outside the transaction; no model polling or database lock.
            self.sleep(wait)
