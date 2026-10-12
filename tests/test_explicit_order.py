from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("outlet_explicit_discovery", ROOT / "scripts/find_outlet_candidates.py")
discovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discovery)


class ExplicitOrderTests(unittest.TestCase):
    def run_discovery(self, order_present=True):
        calls = []
        product = {"product_id": 17, "order_product_id": 1701, "sku": "DEMO-17",
                   "ean": "0123456789012", "name": "Model DEMO100/01", "quantity": 1,
                   "price_brutto": 200, "tax_rate": 19}
        order = {"order_id": 17, "order_status_id": 8, "order_source": "kaufland", "currency": "EUR",
                 "products": [product], "custom_extra_fields": {"41787": "1: 100v23"}}

        class Client:
            def call(self, method, params):
                calls.append((method, params))
                if method == "getOrderStatusList":
                    return {"statuses": [{"id": 8, "name": "Wysłane"}]}
                if method == "getOrders":
                    return {"orders": [order] if order_present else []}
                if method == "getInventoryProductsList":
                    return {"products": {"17": product}}
                if method == "getOrderPackages":
                    return {"packages": []}
                if method == "getInvoices":
                    return {"invoices": []}
                raise AssertionError(method)

        with tempfile.TemporaryDirectory() as temporary, patch.object(discovery, "BaseLinkerClient", return_value=Client()), patch.object(discovery, "require_env", return_value="SYNTHETIC-TOKEN"), patch.object(discovery.time, "sleep"), patch.object(discovery.sys, "argv", ["find", "--model", "DEMO100/01", "--order-id", "17", "--format", "json", "--cache-dir", temporary]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(discovery.main(), 0)
            return json.loads(output.getvalue()), calls

    def test_selected_shipped_order_uses_one_targeted_getorders(self):
        result, calls = self.run_discovery()
        orders = [p for method, p in calls if method == "getOrders"]
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["order_id"], 17)
        self.assertTrue(orders[0]["include_custom_extra_fields"])
        self.assertFalse(any("status_id" in p for p in orders))
        self.assertEqual(result["best_candidate"], 17)
        self.assertFalse(result["unit_identity_confirmed"])
        self.assertEqual(result["candidates"][0]["verdict"]["purchase"]["unit_net"], "100.00")

    def test_empty_current_api_is_explicit_archive_exception(self):
        result, _ = self.run_discovery(order_present=False)
        self.assertEqual(result["scope"]["requested_ids_not_in_current_api"], [17])
        self.assertFalse(result["scope"]["includes_archive"])
        self.assertIsNone(result["best_candidate"])


if __name__ == "__main__":
    unittest.main()
