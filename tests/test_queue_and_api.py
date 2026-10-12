from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fixtures import approve, fixture
from outlet_engine.api import BaseLinkerClient, BaseLinkerConfig
from outlet_engine.queue import JobQueue


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.queue = JobQueue(Path(self.temp.name) / "queue.sqlite3")

    def tearDown(self):
        self.queue.close()
        self.temp.cleanup()

    def test_enqueue_repeat_does_not_duplicate(self):
        manifest, _ = fixture()
        first = self.queue.enqueue(manifest)
        self.assertEqual(self.queue.enqueue(manifest)["operation_id"], first["operation_id"])
        self.assertEqual(self.queue.db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 1)

    def test_same_physical_receipt_changed_values_are_blocked(self):
        manifest, _ = fixture()
        self.queue.enqueue(manifest)
        manifest["operation_id"] = "00000000-0000-4000-8000-000000000002"
        approve(manifest)
        with self.assertRaises(ValueError):
            self.queue.enqueue(manifest)

    def test_one_worker_and_active_operation(self):
        manifest, _ = fixture()
        job = self.queue.enqueue(manifest)
        self.queue.register_worker(job["resource"], "synthetic-child")
        with self.assertRaises(ValueError):
            self.queue.register_worker(job["resource"], "other-child")
        claimed = self.queue.claim(job["resource"], "synthetic-child")
        self.assertEqual(claimed["state"], "claimed")
        with self.assertRaises(ValueError):
            self.queue.claim(job["resource"], "synthetic-child")

    def test_completion_requires_readback_not_dispatch(self):
        manifest, _ = fixture()
        job = self.queue.enqueue(manifest)
        self.queue.register_worker(job["resource"], "synthetic-child")
        self.queue.claim(job["resource"], "synthetic-child")
        with self.assertRaises(ValueError):
            self.queue.update(job["operation_id"], "synthetic-child", "verified", {})
        self.queue.update(job["operation_id"], "synthetic-child", "write_pending")
        with self.assertRaises(ValueError):
            self.queue.update(job["operation_id"], "synthetic-child", "verified", {"verified": True})
        self.queue.update(job["operation_id"], "synthetic-child", "verified", {
            "verified": True, "proposal_sha256": job["proposal_sha256"],
            "range": "'OUTLET'!A20:V20", "sheet_url": "https://example.invalid/synthetic-sheet",
        })
        self.assertEqual(self.queue.get(job["operation_id"])["state"], "verified")

    def test_timeout_is_not_requeued_and_other_jobs_can_continue(self):
        manifest, _ = fixture()
        job = self.queue.enqueue(manifest)
        self.queue.register_worker(job["resource"], "synthetic-child")
        self.queue.claim(job["resource"], "synthetic-child")
        self.queue.update(job["operation_id"], "synthetic-child", "write_pending")
        self.queue.update(job["operation_id"], "synthetic-child", "needs_review", {"reason": "timeout"})
        self.assertEqual(self.queue.enqueue(manifest)["state"], "needs_review")
        self.assertIsNone(self.queue.claim(job["resource"], "synthetic-child"))


class ApiReaderTests(unittest.TestCase):
    def test_write_method_rejected_before_network(self):
        client = BaseLinkerClient(BaseLinkerConfig(token="SYNTHETIC-TOKEN"))
        with patch.object(client, "_post") as post:
            with self.assertRaises(ValueError):
                client.call("addInventoryDocument", {})
            post.assert_not_called()

    def test_curl_token_is_only_in_stdin_and_not_repr(self):
        config = BaseLinkerConfig(token="SYNTHETIC-TOKEN")
        self.assertNotIn("SYNTHETIC-TOKEN", repr(config))
        client = BaseLinkerClient(config, transport="curl")
        with patch("outlet_engine.api.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = b'{"status":"SUCCESS","orders":[]}'
            self.assertEqual(client.call("getOrders", {})["orders"], [])
            self.assertNotIn("SYNTHETIC-TOKEN", str(run.call_args.args[0]))
            self.assertIn(b"SYNTHETIC-TOKEN", run.call_args.kwargs["input"])

    def test_private_server_message_is_not_logged(self):
        client = BaseLinkerClient(BaseLinkerConfig(token="SYNTHETIC-TOKEN"))
        with patch.object(client, "_post", return_value=b'{"status":"ERROR","error_code":"NO_ACCESS","error_message":"private@example.invalid"}'):
            with self.assertRaises(RuntimeError) as result:
                client.call("getOrders", {})
            self.assertNotIn("private@", str(result.exception))


if __name__ == "__main__":
    unittest.main()
