from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "find_outlet_candidates.py"
SPEC = importlib.util.spec_from_file_location("outlet_discovery", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
discovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discovery)


class OutletDiscoveryTests(unittest.TestCase):
    def test_model_suffix_and_boundaries(self):
        self.assertTrue(discovery.model_matches("FC8240/09", "Philips FC 8240 / 09, 750 W"))
        self.assertFalse(discovery.model_matches("FC8240/09", "Philips FC8240/19"))
        self.assertFalse(discovery.model_matches("FC8240/09", "Philips FC8240/091"))
        self.assertFalse(discovery.model_matches("FC8240/09", "Philips XFC8240/09"))

    def test_exact_sku_and_ean_keep_leading_zero(self):
        self.assertEqual(discovery.matching_reasons(
            {"sku": "0007", "ean": "0123456789012", "name": ""},
            model="FC8240/09", ean="0123456789012", skus={"0007"},
        ), ["EAN", "SKU"])
        self.assertEqual(discovery.matching_reasons(
            {"sku": "0007 v2", "ean": "123456789012", "name": ""},
            model="FC8240/09", ean="0123456789012", skus={"0007"},
        ), [])

    def test_cancelled_polish_forms_are_all_in_scope(self):
        for name in ["ALLEGRO Anulacja", "ERLI Anulowane", "PIGU Anulowane", "ZWROTY DOTARŁY"]:
            self.assertTrue(discovery.qualifying_status(name, ["zwrot", "zwr", "anul"]))
        self.assertFalse(discovery.qualifying_status("KAUFLAND Wysłane", ["zwrot", "zwr", "anul"]))

    def test_unknown_and_customer_fields_do_not_reach_index(self):
        safe = discovery.sanitize_order({
            "order_id": 17, "email": "customer@example.invalid", "phone": "private",
            "admin_comments": "private", "custom_extra_fields": {"token": "private"},
            "products": [{"sku": "0007", "quantity": 1, "unknown_customer_field": "private"}],
        }, "Zwrócone")
        self.assertNotIn("private", discovery.canonical(safe))
        self.assertNotIn("email", safe)
        self.assertEqual(safe["products"][0]["sku"], "0007")

    def test_full_page_uses_id_cursor_and_includes_unconfirmed(self):
        calls = []

        def call(method, parameters):
            calls.append((method, parameters))
            start = parameters.get("id_from", 1)
            return {"orders": [{"order_id": i, "products": []} for i in range(start, min(start + 100, 103))]}

        result = discovery.paged_orders(call, {"id": 9, "name": "Anulowane"})
        self.assertEqual(len(result), 102)
        self.assertEqual(calls[1][1]["id_from"], 101)
        self.assertTrue(all(p["get_unconfirmed_orders"] for _, p in calls))

    def test_bad_pagination_cannot_claim_complete(self):
        def call(method, parameters):
            return {"orders": [{"order_id": i, "products": []} for i in range(1, 101)]}

        with self.assertRaises(RuntimeError):
            discovery.paged_orders(call, {"id": 9, "name": "Anulowane"})

    def test_missing_orders_is_not_an_empty_complete_result(self):
        with self.assertRaises(RuntimeError):
            discovery.paged_orders(lambda method, params: {"status": "SUCCESS"},
                                   {"id": 9, "name": "Anulowane"})

    def test_no_status_can_confirm_physical_unit(self):
        index = {"orders": [{"order_id": 17, "status_name": "ZWROTY DOTARŁY", "products": [
            {"sku": "0007", "ean": "0123456789012", "name": "Philips FC8240/09"},
        ]}]}
        result = discovery.candidates(index, model="FC8240/09", ean="0123456789012", skus={"0007"})
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["unit_confirmed"])

    def test_cache_rejects_wrong_account_tamper_and_stale_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "index.json"
            payload = {
                "schema_version": 1, "complete": True, "includes_archive": False,
                "created_at": datetime.now(UTC).isoformat(), "orders": [],
                "status_scope": ["anul"], "account_key": "account-A",
                "orders_sha256": hashlib.sha256(b"[]").hexdigest(),
            }
            discovery.atomic_json(path, payload)
            self.assertIsNotNone(discovery.load_fresh_index(path, 3600, ["anul"], "account-A"))
            self.assertIsNone(discovery.load_fresh_index(path, 3600, ["anul"], "account-B"))
            payload["orders"] = [{"order_id": 17}]
            discovery.atomic_json(path, payload)
            self.assertIsNone(discovery.load_fresh_index(path, 3600, ["anul"], "account-A"))
            payload["orders"] = []
            payload["created_at"] = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
            discovery.atomic_json(path, payload)
            self.assertIsNone(discovery.load_fresh_index(path, 3600, ["anul"], "account-A"))

    def test_one_writer_and_release_on_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            lock = Path(temporary) / "discovery.lock"
            with self.assertRaises(ValueError):
                with discovery.exclusive_cache(lock):
                    with self.assertRaises(RuntimeError):
                        with discovery.exclusive_cache(lock):
                            self.fail("Second writer was allowed")
                    raise ValueError("intentional test failure")
            self.assertFalse(lock.exists())

    def test_read_methods_contain_no_mutations(self):
        self.assertTrue(all(method.startswith("get") for method in discovery.READ_METHODS))


if __name__ == "__main__":
    unittest.main()
