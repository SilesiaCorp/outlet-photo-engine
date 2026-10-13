from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fixtures import ROOT
from outlet_engine.fast_search import FastCache, FirstCandidateSearch, candidate_rank, exact_token, extract_references, reference
from outlet_engine.rate_limit import RequestBudget

spec = importlib.util.spec_from_file_location("fast_discovery_fixture", ROOT / "scripts/find_outlet_candidates.py")
discovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discovery)


def order(oid=17, *, model="DEMO100/01", status=9, note="", sku="DEMO-001"):
    return {"order_id": oid, "order_status_id": status, "order_source": "kaufland", "currency": "EUR",
            "date_in_status": oid, "admin_comments": note, "email": "private@example.invalid",
            "phone": "private", "custom_extra_fields": {"41787": "1: 100v23", "45809": "Silesia Protech"},
            "products": [{"order_product_id": oid * 10, "product_id": 100, "sku": sku,
                          "name": "Produkt " + model, "ean": "0123456789012", "quantity": 1,
                          "price_brutto": 200, "tax_rate": 19}]}


class FastSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cache = FastCache(Path(self.temp.name) / "fast.sqlite3")
        self.calls, self.events = [], []

    def tearDown(self):
        self.cache.close()
        self.temp.cleanup()

    def search(self, responses, **kwargs):
        def call(method, params):
            self.calls.append((method, params))
            response = responses.get(method)
            if callable(response): return response(params)
            if response is None: raise AssertionError("Unexpected request: " + method)
            if isinstance(response, Exception): raise response
            return response
        kwargs.setdefault("strict_return_reference", True)
        return FirstCandidateSearch(call, self.cache,
            matches=lambda p, skus: discovery.matching_reasons(p, model="DEMO100/01", ean="", skus=skus),
            sanitize=discovery.sanitize_order,
            qualifying=lambda name: discovery.qualifying_status(name, ["zwrot", "zwr", "anul"]),
            config={"base_inventory_id": 17463}, model="DEMO100/01", preview_only=True,
            on_candidate=lambda event: self.events.append((event, list(self.calls))), **kwargs)

    def seed_statuses(self):
        self.cache.save_metadata("statuses", [{"id": 9, "name": "ZWROTY DOTARŁY"}, {"id": 8, "name": "Wysłane"}])

    def test_warm_model_hint_is_one_live_call_and_no_catalogue_scan(self):
        self.seed_statuses()
        self.cache.remember(discovery.sanitize_order(order(), "ZWROTY DOTARŁY"), [])
        result = self.search({"getOrders": {"orders": [order()]}}).run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual([m for m, _ in self.calls], ["getOrders"])
        self.assertEqual(result["scope"]["api_calls_to_first_candidate"], 1)
        self.assertFalse(result["scope"]["global_ranking_complete"])
        self.assertFalse(result["unit_identity_confirmed"])
        self.assertEqual(len(result["candidates"][0]["verdict"]["sheet_fields"]), 22)

    def test_first_candidate_event_precedes_financial_enrichment(self):
        self.seed_statuses()
        engine = self.search({"getOrders": {"orders": [order()]}, "getOrderPackages": {"packages": []},
                              "getInvoices": {"invoices": [{"type": "normal", "seller": "TRACER TEAM"}]}}, order_ids=[17])
        engine.preview_only = False
        result = engine.run()
        self.assertEqual([m for m, _ in self.events[0][1]], ["getOrders"])
        self.assertTrue(result["scope"]["candidate_enrichment_complete"])
        self.assertEqual(result["candidates"][0]["verdict"]["sheet_fields"]["Własność Spółki"], "TRACER TEAM")

    def test_failed_enrichment_keeps_first_candidate_and_marks_missing_data(self):
        self.seed_statuses()
        engine = self.search({"getOrders": {"orders": [order()]}, "getOrderPackages": {"packages": []},
                              "getInvoices": RuntimeError("SYNTHETIC_READ_FAILURE")}, order_ids=[17])
        engine.preview_only = False
        result = engine.run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertFalse(result["scope"]["candidate_enrichment_complete"])
        self.assertIn("candidate_enrichment_failed_requires_readback", result["scope"]["exceptions"])

    def test_cold_full_page_stops_without_next_page_or_next_status(self):
        batch = [order(i, model="OTHER100/01") for i in range(1, 100)] + [order(100)]
        self.seed_statuses()
        result = self.search({"getOrders": {"orders": batch}}).run()
        self.assertEqual(result["best_candidate"], 100)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][1]["status_id"], 9)
        self.assertEqual(self.cache.db.execute("SELECT COUNT(*) FROM hints").fetchone()[0], 100)

    def test_cached_return_number_reads_fresh_order_notes_first(self):
        self.cache.save_refs(17, [{"kind": "return", "value": "ZW-00017", "source": "custom_extra_fields.2"}])
        source = order()
        source["custom_extra_fields"]["2"] = "Zwrot: ZW-00017; reszta prywatnej notatki"
        result = self.search({"getOrders": {"orders": [source]}}, return_number="ZW-00017").run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.events[0][0]["evidence"], "return:custom_extra_fields.2")
        self.assertNotIn("private@example", str(self.cache.orders()))
        self.assertNotIn("reszta prywatnej", str(self.cache.orders()))

    def test_return_number_in_current_order_notes_with_dynamic_field(self):
        self.seed_statuses()
        self.cache.save_metadata("return-fields", {})
        self.cache.save_metadata("order-fields", {"50000": {"name": "Numer zwrotu Allegro", "editor_type": "text"}})
        source = order()
        source["custom_extra_fields"]["50000"] = "ZW-00017"
        result = self.search({"getOrderReturns": {"returns": []}, "getOrders": {"orders": [source]}},
                             return_number="ZW-00017").run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.cache.reference_hints("return", "ZW-00017")[0]["order_id"], 17)

    def test_cached_dedicated_return_field_does_not_need_a_metadata_or_return_scan(self):
        self.cache.save_metadata("order-fields", {"50000": {"name": "Numer zwrotu Allegro", "editor_type": "text"}})
        self.cache.save_refs(17, [{"kind": "return", "value": "ZW-00017", "source": "custom_extra_fields.50000"}])
        source = order()
        source["custom_extra_fields"]["50000"] = "ZW-00017"
        result = self.search({"getOrders": {"orders": [source]}}, return_number="ZW-00017").run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual([m for m, _ in self.calls], ["getOrders"])

    def test_native_return_number_is_proposed_before_unneeded_field_metadata(self):
        record = {"return_id": 7, "order_id": 17, "reference_number": "ZW-00017", "products": [order()["products"][0]]}
        result = self.search({"getOrderReturns": {"returns": [record]}}, return_number="ZW-00017").run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual([m for m, _ in self.calls], ["getOrderReturns"])

    def test_conflicting_external_sale_id_does_not_propose_a_native_return(self):
        record = {"return_id": 7, "order_id": 17, "products": [order()["products"][0]]}
        source = {**order(), "external_order_id": "SALE-OTHER"}
        result = self.search({"getOrderReturns": {"returns": [record]}, "getOrders": {"orders": [source]}},
                             return_id=7, external_order_id="SALE-001").run()
        self.assertIsNone(result["best_candidate"])
        self.assertFalse(self.events)
        self.assertIn("provided_external_order_id_not_linked_to_candidate", result["scope"]["exceptions"])

    def test_known_return_number_never_falls_back_to_same_model_with_different_number(self):
        self.seed_statuses()
        self.cache.save_metadata("return-fields", {})
        self.cache.save_metadata("order-fields", {})
        source = order(note="Numer zwrotu: ZW-99999")
        self.cache.remember(discovery.sanitize_order(source, "ZWROTY DOTARŁY"), [])
        result = self.search({"getOrderReturns": {"returns": []}, "getOrders": {"orders": [source]}},
                             return_number="ZW-00017").run()
        self.assertIsNone(result["best_candidate"])
        self.assertTrue(all("order_id" not in params for method, params in self.calls if method == "getOrders"))

    def test_internal_return_id_binds_only_the_returned_order_product(self):
        source = order()
        source["products"].append({**source["products"][0], "order_product_id": 171, "sku": "OTHER", "name": "OTHER"})
        record = {"return_id": 7, "order_id": 17, "products": [{"order_product_id": 170, "sku": "DEMO-001", "quantity": 1}], "fulfillment_status": 5}
        result = self.search({"getOrderReturns": {"returns": [record]}, "getOrders": {"orders": [source]}}, return_id=7).run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual(result["candidates"][0]["product"]["order_product_id"], 170)
        self.assertEqual(result["scope"]["api_calls_to_first_candidate"], 2)
        self.assertEqual(self.calls[0][1]["return_id"], 7)

    def test_same_order_does_not_select_product_outside_return(self):
        source = order()
        source["products"].append({**source["products"][0], "order_product_id": 171, "sku": "OTHER", "name": "OTHER"})
        record = {"return_id": 7, "order_id": 17, "products": [{"order_product_id": 171, "sku": "OTHER"}]}
        result = self.search({"getOrderReturns": {"returns": [record]}, "getOrders": {"orders": [source]},
                             "getInventoryProductsList": {"products": {}}}, return_id=7).run()
        self.assertIsNone(result["best_candidate"])

    def test_missing_explicit_order_does_not_search_other_orders(self):
        result = self.search({"getOrders": {"orders": []}}, order_ids=[17]).run()
        self.assertIsNone(result["best_candidate"])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(result["scope"]["requested_ids_not_in_current_api"], [17])

    def test_return_record_proposes_original_order_before_order_or_invoice_read(self):
        record = {"return_id": 7, "order_id": 17, "products": [order()["products"][0]]}
        result = self.search({"getOrderReturns": {"returns": [record]}}, return_id=7).run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual(result["scope"]["api_calls_to_first_candidate"], 1)
        self.assertFalse(result["candidates"][0]["order_readback_complete"])
        fields = result["candidates"][0]["verdict"]["sheet_fields"]
        self.assertIsNone(fields["Cena Netto"])
        self.assertIsNone(fields["Ilość"])
        self.assertIsNone(fields["Data zamówienia"])

    def test_cached_native_reference_refreshes_return_before_original_order(self):
        self.cache.save_refs(17, [{"kind": "return", "value": "7", "source": "return_id"}], return_id=7)
        record = {"return_id": 7, "order_id": 17, "products": [order()["products"][0]]}
        result = self.search({"getOrderReturns": {"returns": [record]}}, return_id=7).run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual([m for m, _ in self.calls], ["getOrderReturns"])

    def test_return_link_is_not_lost_when_original_order_is_unavailable_in_current_api(self):
        record = {"return_id": 7, "order_id": 17, "products": [order()["products"][0]]}
        engine = self.search({"getOrderReturns": {"returns": [record]}, "getOrders": {"orders": []}}, return_id=7)
        engine.preview_only = False
        result = engine.run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertIn("original_order_requires_panel_or_archive_readback", result["scope"]["exceptions"])

    def test_conflicting_tracking_number_does_not_propose_a_return_number_match(self):
        self.cache.save_refs(17, [{"kind": "return", "value": "ZW-00017", "source": "admin_comments"}])
        record = {"return_id": 7, "order_id": 17, "reference_number": "ZW-00017", "products": [order()["products"][0]]}
        self.cache.save_metadata("return-fields", {})
        self.cache.save_metadata("order-fields", {})
        self.seed_statuses()
        result = self.search({"getOrders": {"orders": [order(note="Numer zwrotu: ZW-00017")]},
                              "getOrderPackages": {"packages": []}, "getOrderReturns": {"returns": [record]}},
                             return_number="ZW-00017", tracking_number="0007711").run()
        self.assertIsNone(result["best_candidate"])
        self.assertIn("provided_tracking_number_not_linked_to_candidate", result["scope"]["exceptions"])

    def test_conflicting_order_and_return_number_are_not_proposed(self):
        self.cache.save_refs(17, [{"kind": "return", "value": "ZW-00017", "source": "admin_comments"}])
        responses = {"getOrders": lambda p: {"orders": [order(p["order_id"], note="Numer zwrotu: ZW-00017" if p["order_id"] == 17 else "")]}}
        result = self.search(responses, order_ids=[18], return_number="ZW-00017").run()
        self.assertIsNone(result["best_candidate"])
        self.assertIn("provided_order_and_parcel_reference_conflict", result["scope"]["exceptions"])

    def test_excluded_first_candidate_moves_to_next_without_repeating_it(self):
        self.seed_statuses()
        self.cache.remember(discovery.sanitize_order(order(18), "ZWROTY DOTARŁY"), [])
        self.cache.remember(discovery.sanitize_order(order(17), "ZWROTY DOTARŁY"), [])
        result = self.search({"getOrders": {"orders": [order(17)]}}, excluded_order_ids=[18]).run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][1]["order_id"], 17)

    def test_cached_package_reference_is_refreshed(self):
        self.cache.save_refs(17, [{"kind": "tracking", "value": "0007711", "source": "packages.courier_package_nr"}])
        result = self.search({"getOrders": {"orders": [order()]},
                             "getOrderPackages": {"packages": [{"courier_package_nr": "0007711", "is_return": True}]}},
                             tracking_number="0007711").run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual(result["scope"]["api_calls_to_first_candidate"], 2)

    def test_bad_return_number_does_not_block_or_delay_product_candidate(self):
        self.seed_statuses()
        self.cache.remember(discovery.sanitize_order(order(), "ZWROTY DOTARŁY"), [])
        result = self.search({"getOrders": {"orders": [order(note="Numer zwrotu: WRONG-001")]}},
                             return_number="MISTYPED-009", strict_return_reference=False).run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual([m for m, _ in self.calls], ["getOrders"])
        self.assertEqual(result["candidates"][0]["return_reference"]["policy"], "advisory")
        self.assertFalse(result["unit_identity_confirmed"])

    def test_first_read_uses_stronger_product_hint_already_available_in_cache(self):
        self.seed_statuses()
        weak = {**order(), "date_in_status":200}
        stronger = {**order(18,sku="BEST-SKU"), "date_in_status":100}
        for source in [weak,stronger]:
            self.cache.remember(discovery.sanitize_order(source,"ZWROTY DOTARŁY"),[])
        result = self.search({"getOrders":{"orders":[stronger]}},skus=["BEST-SKU"],strict_return_reference=False).run()
        self.assertEqual(result["best_candidate"],18)
        self.assertEqual(self.calls[0][1]["order_id"],18)
        self.assertEqual(len(self.calls),1)

    def test_bad_internal_return_id_does_not_block_a_matching_product(self):
        self.seed_statuses()
        self.cache.remember(discovery.sanitize_order(order(), "ZWROTY DOTARŁY"), [])
        result = self.search({"getOrders": {"orders": [order()]}}, return_id=999,
                             strict_return_reference=False).run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual(len(self.calls), 1)

    def test_return_hint_for_other_order_is_not_checked_before_product_hint(self):
        self.seed_statuses()
        self.cache.save_refs(18, [{"kind": "return", "value": "MISTYPED-009", "source": "extra_field_2"}])
        self.cache.remember(discovery.sanitize_order(order(), "ZWROTY DOTARŁY"), [])
        result = self.search({"getOrders": {"orders": [order()]}}, return_number="MISTYPED-009",
                             strict_return_reference=False).run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertEqual(self.calls[0][1]["order_id"], 17)

    def test_progressive_comparison_emits_first_then_stronger_candidate(self):
        self.seed_statuses()
        self.cache.remember(discovery.sanitize_order(order(), "ZWROTY DOTARŁY"), [])
        stronger = order(18, sku="BEST-SKU")
        checkpoints = []
        result = self.search({"getOrders": lambda p: {"orders": [order()] if "order_id" in p else [order(), stronger]},
                              "getOrderReturns": {"returns": []}}, skus=["BEST-SKU"], continue_search=True,
                             strict_return_reference=False, on_checkpoint=lambda report: checkpoints.append(report)).run()
        self.assertEqual([e[0]["event"] for e in self.events], ["candidate_found", "candidate_updated"])
        self.assertEqual(self.events[0][0]["order_id"], 17)
        self.assertEqual([m for m, _ in self.events[0][1]], ["getOrders"])
        self.assertEqual(self.events[1][0]["order_id"], 18)
        self.assertEqual(checkpoints[0]["best_candidate"], 17)
        self.assertEqual(result["best_candidate"], 18)
        self.assertEqual(len(result["candidates"]), 2)
        self.assertTrue(result["scope"]["current_api_comparison_complete"])
        self.assertEqual(result["scope"]["followup_required"], ["archive"])
        self.assertFalse(result["scope"]["includes_archive"])
        self.assertFalse(result["scope"]["global_ranking_complete"])

    def test_continuation_reuses_first_page_before_reading_next(self):
        self.seed_statuses()
        first = [order(i, model="OTHER") for i in range(1, 100)] + [order(100)]
        result = self.search({"getOrders": lambda p: {"orders": [order(101)] if p.get("id_from") else first},
                              "getOrderReturns": {"returns": []}}, continue_search=True,
                             strict_return_reference=False).run()
        self.assertEqual(result["best_candidate"], 101)
        calls = [params for method, params in self.calls if method == "getOrders"]
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1]["id_from"], 101)
        self.assertEqual(result["scope"]["orders_indexed"], 101)

    def test_failed_continuation_keeps_shown_candidate_and_open_scope(self):
        self.seed_statuses()
        self.cache.remember(discovery.sanitize_order(order(), "ZWROTY DOTARŁY"), [])
        result = self.search({"getOrders": {"orders": [order()]},
                              "getOrderReturns": RuntimeError("SYNTHETIC_READ_FAILURE")},
                             continue_search=True, strict_return_reference=False).run()
        self.assertEqual(result["best_candidate"], 17)
        self.assertFalse(result["scope"]["current_api_comparison_complete"])
        self.assertIn("current_api_comparison_incomplete_requires_followup", result["scope"]["exceptions"])

    def test_return_api_failure_does_not_block_other_current_order_matches(self):
        self.seed_statuses()
        self.cache.remember(discovery.sanitize_order(order(),"ZWROTY DOTARŁY"),[])
        result = self.search({"getOrders":lambda p:{"orders":[order()] if "order_id" in p else [order(),order(18)]},
                              "getOrderReturns":RuntimeError("SYNTHETIC_READ_FAILURE")},
                             continue_search=True,strict_return_reference=False).run()
        self.assertEqual(result["best_candidate"],18)
        self.assertEqual(len(result["candidates"]),2)
        self.assertFalse(result["scope"]["current_api_comparison_complete"])
        self.assertIn("native_return_comparison_unavailable",result["scope"]["exceptions"])

    def test_native_preview_is_completed_when_original_card_appears_in_comparison(self):
        self.seed_statuses()
        record = {"return_id": 7, "order_id": 17, "products": [order()["products"][0]]}
        engine = self.search({"getOrderReturns": {"returns": [record]}, "getOrders": {"orders": [order()]}},
                             return_id=7, strict_return_reference=False)
        initial = engine.result(engine.native_preview(record))
        result = engine.compare_remaining(initial)
        self.assertEqual(result["best_candidate"], 17)
        self.assertTrue(result["candidates"][0]["order_readback_complete"])
        self.assertEqual(result["candidates"][0]["verdict"]["sheet_fields"]["Cena Netto"], "100.00")

    def test_matching_return_code_cannot_raise_the_evidence_rank(self):
        base = {"order_id":17,"matched_by":["MODEL"],"evidence":"matching_product_and_qualifying_status",
                "order_readback_complete":True,"date_in_status":17}
        self.assertEqual(candidate_rank(base), candidate_rank({**base,"return_reference":{"status":"matched_but_not_unit_confirmation"}}))

    def test_comparison_keeps_the_specific_returned_item_when_order_has_two_same_models(self):
        self.seed_statuses()
        source = order()
        source["products"].insert(0, {**source["products"][0], "order_product_id":171})
        record = {"return_id":7,"order_id":17,"products":[order()["products"][0]]}
        engine = self.search({"getOrderReturns":{"returns":[record]},"getOrders":{"orders":[source]}},
                             return_id=7,strict_return_reference=False)
        result = engine.compare_remaining(engine.result(engine.native_preview(record)))
        self.assertEqual(result["candidates"][0]["product"]["order_product_id"], 170)

    def test_bad_pagination_cannot_be_used_as_complete_source(self):
        self.seed_statuses()
        engine = self.search({"getOrders": {"orders": [order(i, model="OTHER") for i in range(1, 101)]},
                              "getInventoryProductsList": {"products": {}}})
        with self.assertRaisesRegex(RuntimeError, "paginacja"):
            engine.run()

    def test_legacy_cache_is_a_hint_and_removes_customer_fields(self):
        source = order()
        payload = {"schema_version": 1, "includes_archive": False, "account_key": "account-A",
                   "orders": [source], "statuses": [{"status_id": 9, "name": "ZWROTY DOTARŁY"}],
                   "created_at": datetime.now(UTC).isoformat(),
                   "orders_sha256": hashlib.sha256(discovery.canonical([source]).encode()).hexdigest()}
        path = Path(self.temp.name) / "legacy.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.cache.import_legacy(path, "account-A", discovery.sanitize_order)
        self.assertNotIn("private@example", str(self.cache.orders()))
        result = self.search({"getOrders": {"orders": [order(status=8)]}, "getOrderPackages": {"packages": []},
                             "getInventoryProductsList": {"products": {}}}).run()
        self.assertIsNone(result["best_candidate"])


class ReferenceTests(unittest.TestCase):
    def test_full_token_and_leading_zeroes(self):
        self.assertTrue(exact_token("Zwrot ZW-00017.", "ZW00017"))
        self.assertFalse(exact_token("Zwrot ZW-000170.", "ZW00017"))
        self.assertNotEqual(reference("00017"), reference("17"))

    def test_phone_and_customer_notes_are_not_indexed_as_return_numbers(self):
        refs = extract_references({"phone": "private", "email": "private@example.invalid",
                                   "extra_field_2": "Automat DPD 123456789; kontakt do klienta"}, {})
        self.assertEqual(refs, [])

    def test_return_label_and_dedicated_field_are_indexed_without_full_notes(self):
        refs = extract_references({"admin_comments": "NR ZWROTU: ZW-00017; adres prywatny",
                                   "custom_extra_fields": {"50000": "R-0012"}},
                                  {"50000": {"name": "Numer zwrotu Allegro"}})
        self.assertTrue(any(r["value"] == "ZW-00017" for r in refs))
        self.assertTrue(any(r["value"] == "R-0012" for r in refs))
        self.assertNotIn("adres prywatny", str(refs))

    def test_original_ean_or_sku_does_not_override_conflicting_model_variant(self):
        reasons = discovery.matching_reasons({"sku": "SKU", "ean": "EAN", "name": "Philips FC 8240 / 19"},
                                             model="FC8240/09", ean="EAN", skus={"SKU"})
        self.assertEqual(reasons, [])


class RequestBudgetTests(unittest.TestCase):
    def test_requests_do_not_sleep_until_documented_budget_is_used(self):
        with tempfile.TemporaryDirectory() as temporary:
            instant, waits = [100.0], []
            def sleep(seconds):
                waits.append(seconds)
                instant[0] += seconds
            path = Path(temporary) / "budget.sqlite3"
            first = RequestBudget(path, "A", capacity=2, window_seconds=60, clock=lambda: instant[0], sleep=sleep)
            second = RequestBudget(path, "A", capacity=2, window_seconds=60, clock=lambda: instant[0], sleep=sleep)
            first.acquire()
            second.acquire()
            self.assertEqual(waits, [])
            first.acquire()
            self.assertEqual(len(waits), 1)
            self.assertGreaterEqual(waits[0], 60)

    def test_other_token_budget_does_not_consume_this_budget(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "budget.sqlite3"
            waits = []
            first = RequestBudget(path, "A", capacity=1, clock=lambda: 100, sleep=waits.append)
            second = RequestBudget(path, "B", capacity=1, clock=lambda: 100, sleep=waits.append)
            first.acquire()
            second.acquire()
            self.assertEqual(waits, [])


if __name__ == "__main__":
    unittest.main()
