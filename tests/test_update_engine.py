from __future__ import annotations

import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fixtures import ROOT

spec = importlib.util.spec_from_file_location("outlet_updater_fixture", ROOT / "scripts/update_engine.py")
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class UpdateSafetyTests(unittest.TestCase):
    def test_only_canonical_remote_is_allowed(self):
        updater.verify_remote("https://github.com/SilesiaCorp/outlet-photo-engine.git")
        updater.verify_remote("git@github.com:SilesiaCorp/outlet-photo-engine.git")
        with self.assertRaises(ValueError):
            updater.verify_remote("https://example.invalid/another-repo.git")

    def test_active_or_uncertain_writer_blocks_code_update(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "jobs.sqlite3"
            db = sqlite3.connect(path)
            try:
                db.execute("CREATE TABLE jobs (state TEXT)")
                db.execute("INSERT INTO jobs VALUES ('write_pending')")
                db.commit()
                with self.assertRaises(ValueError):
                    updater.ensure_no_active_write(path)
                db.execute("UPDATE jobs SET state='needs_review'")
                db.commit()
                with self.assertRaises(ValueError):
                    updater.ensure_no_active_write(path)
                db.execute("UPDATE jobs SET state='verified'")
                db.commit()
                updater.ensure_no_active_write(path)
            finally:
                db.close()

    def test_absent_queue_is_not_created_by_update_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing.sqlite3"
            updater.ensure_no_active_write(path)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
