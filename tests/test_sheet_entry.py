from __future__ import annotations

import copy
import unittest

from fixtures import apply_requests, approve, fixture
from outlet_engine.approval import validate_manifest
from outlet_engine.sheet import assert_preimage, build_plan, find_duplicate, header_map, verify_readback
from outlet_engine.sheet import snapshot_from_cells


class SheetEntryTests(unittest.TestCase):
    def test_complete_outlet_native_payload_and_readback(self):
        manifest, snapshot = fixture()
        plan = build_plan(manifest, snapshot)
        actual = apply_requests(snapshot, plan["requests"])
        receipt = verify_readback(plan, actual)
        self.assertTrue(receipt["verified"])
        self.assertFalse(receipt["warehouse_intake"])
        self.assertEqual(plan["expected_values"]["VAT"], {"numberValue": .23})
        self.assertEqual(plan["expected_values"]["EAN Oryg."], {"stringValue": "0123456789012"})
        self.assertEqual(plan["expected_values"]["Zamówienie BL"], {"stringValue": "00017"})
        self.assertEqual(plan["expected_values"]["Dodane do systemu magazynowego"], {"boolValue": False})
        self.assertNotIn("Nr PZ system magazynowy", plan["expected_values"])
        self.assertEqual(plan["range"], "'OUTLET'!A20:V20")

    def test_complete_complaint_including_client_ownership_is_sheet_only(self):
        manifest, snapshot = fixture("REKLAMACJE")
        manifest["fields"]["Właściciel towaru"] = "KLIENT"
        approve(manifest)
        plan = build_plan(manifest, snapshot)
        self.assertTrue(verify_readback(plan, apply_requests(snapshot, plan["requests"]))["verified"])
        self.assertEqual(plan["expected_values"]["Właściciel towaru"], {"stringValue": "KLIENT"})
        self.assertEqual(plan["expected_values"]["Dodane do systemu magazynowego"], {"boolValue": False})

    def test_changed_payload_invalidates_approval(self):
        manifest, snapshot = fixture()
        manifest["fields"]["Cena Netto"] = "200.00"
        with self.assertRaisesRegex(ValueError, "zgody"):
            build_plan(manifest, snapshot)

    def test_instruction_or_ai_cannot_approve(self):
        manifest, snapshot = fixture()
        manifest["approval"]["origin"] = "document_instruction"
        with self.assertRaises(ValueError):
            build_plan(manifest, snapshot)

    def test_receipt_quantity_is_not_order_quantity_by_default(self):
        manifest, snapshot = fixture()
        manifest["verified"]["physical_quantity"] = False
        approve(manifest)
        with self.assertRaisesRegex(ValueError, "fizyczn"):
            build_plan(manifest, snapshot)

    def test_zero_is_valid_missing_is_not_zero(self):
        manifest, snapshot = fixture()
        manifest["fields"].update({"Cena Netto": "0.00", "Cena brutto": "0.00", "VAT": "0"})
        approve(manifest)
        self.assertEqual(build_plan(manifest, snapshot)["expected_values"]["Cena Netto"], {"numberValue": 0.0})
        manifest["fields"]["Cena Netto"] = None
        approve(manifest)
        with self.assertRaises(ValueError):
            build_plan(manifest, snapshot)

    def test_gross_vat_inconsistency_is_blocked(self):
        manifest, snapshot = fixture()
        manifest["fields"]["Cena brutto"] = "122.99"
        approve(manifest)
        with self.assertRaisesRegex(ValueError, "spójne"):
            build_plan(manifest, snapshot)

    def test_sheet_entry_cannot_create_stock_confirmation(self):
        manifest, snapshot = fixture()
        manifest["fields"]["Dodane do systemu magazynowego"] = True
        approve(manifest)
        with self.assertRaises(ValueError):
            build_plan(manifest, snapshot)

    def test_header_reorder_routes_by_name(self):
        manifest, snapshot = fixture()
        snapshot["headers"].reverse()
        snapshot["cells"].reverse()
        snapshot["template_cells"].reverse()
        plan = build_plan(manifest, snapshot)
        update = next(r["updateCells"] for r in plan["requests"] if "updateCells" in r and r["updateCells"]["rows"][0]["values"][0].get("userEnteredValue") == {"numberValue": .23})
        self.assertEqual(update["range"]["startColumnIndex"], snapshot["headers"].index("VAT"))

    def test_duplicate_and_missing_headers_stop_write(self):
        manifest, snapshot = fixture()
        snapshot["headers"][0] = "SKU"
        with self.assertRaises(ValueError):
            build_plan(manifest, snapshot)
        with self.assertRaises(ValueError):
            header_map(["SKU", "SKU"])

    def test_nonempty_destination_and_wrong_account_are_blocked(self):
        manifest, snapshot = fixture()
        snapshot["cells"][4]["userEnteredValue"] = {"stringValue": "Cudzy produkt"}
        with self.assertRaisesRegex(ValueError, "pusty"):
            build_plan(manifest, snapshot)
        snapshot["cells"][4].pop("userEnteredValue")
        snapshot["account_email"] = "other@example.invalid"
        with self.assertRaisesRegex(ValueError, "account_email"):
            build_plan(manifest, snapshot)

    def test_formula_preserved_and_effective_result_verified(self):
        manifest, snapshot = fixture()
        indexes = header_map(snapshot["headers"])
        snapshot["cells"][indexes["Cena brutto"]]["userEnteredValue"] = {"formulaValue": "=H20*(1+J20)"}
        plan = build_plan(manifest, snapshot)
        self.assertEqual(plan["preserved_formulas"]["Cena brutto"], "=H20*(1+J20)")
        actual = apply_requests(snapshot, plan["requests"])
        actual["cells"][indexes["Cena brutto"]]["effectiveValue"] = {"numberValue": 123.00}
        self.assertTrue(verify_readback(plan, actual)["verified"])
        actual["cells"][indexes["Cena brutto"]]["effectiveValue"] = {"numberValue": 124.00}
        with self.assertRaises(ValueError):
            verify_readback(plan, actual)

    def test_notes_are_appended_and_existing_flags_retained(self):
        manifest, snapshot = fixture()
        indexes = header_map(snapshot["headers"])
        snapshot["new_row"] = False
        for name in ["SKU", "Zamówienie BL"]:
            snapshot["cells"][indexes[name]]["userEnteredValue"] = {"stringValue": manifest["fields"][name]}
        snapshot["cells"][indexes["Sprzedano"]]["userEnteredValue"] = {"boolValue": True}
        snapshot["cells"][indexes["Notatka"]]["userEnteredValue"] = {"stringValue": "Poprzednia notatka"}
        plan = build_plan(manifest, snapshot)
        self.assertNotIn("Sprzedano", plan["expected_values"])
        self.assertIn("Poprzednia notatka", plan["expected_values"]["Notatka"]["stringValue"])
        self.assertTrue(verify_readback(plan, apply_requests(snapshot, plan["requests"]))["verified"])

    def test_stale_preimage_and_bad_readback_are_detected(self):
        manifest, snapshot = fixture()
        plan = build_plan(manifest, snapshot)
        assert_preimage(plan, snapshot)
        changed = copy.deepcopy(snapshot)
        changed["cells"][4]["userEnteredValue"] = {"stringValue": "Zmiana równoległa"}
        with self.assertRaises(ValueError):
            assert_preimage(plan, changed)
        actual = apply_requests(snapshot, plan["requests"])
        actual["cells"][9]["userEnteredValue"] = {"numberValue": 23}
        with self.assertRaises(ValueError):
            verify_readback(plan, actual)

    def test_native_validation_preserved_not_values_only_append(self):
        manifest, snapshot = fixture()
        plan = build_plan(manifest, snapshot)
        self.assertFalse(any("appendCells" in r for r in plan["requests"]))
        self.assertTrue(all(len(r) == 1 for r in plan["requests"]))
        self.assertEqual({r["copyPaste"]["pasteType"] for r in plan["requests"] if "copyPaste" in r}, {"PASTE_FORMAT", "PASTE_DATA_VALIDATION"})
        actual = apply_requests(snapshot, plan["requests"])
        actual["cells"][18].pop("dataValidation")
        with self.assertRaises(ValueError):
            verify_readback(plan, actual)

    def test_draft_requires_explicit_approval_and_missing_fields(self):
        manifest, snapshot = fixture()
        manifest["entry_mode"] = "draft"
        manifest["pending"] = ["Data fizycznego przyjęcia", "Fizyczna ilość"]
        manifest["fields"]["Data przyjęcia"] = None
        manifest["fields"]["Ilość"] = None
        approve(manifest)
        plan = build_plan(manifest, snapshot)
        self.assertNotIn("Data przyjęcia", plan["expected_values"])
        self.assertNotIn("Ilość", plan["expected_values"])
        self.assertIn("WYMAGA DANYCH", plan["expected_values"]["Notatka AI"]["stringValue"])

    def test_duplicate_same_operation_recovers_existing_row(self):
        manifest, _ = fixture()
        row = {"row_number": 22, "values": {"Notatka AI": "OP: " + manifest["operation_id"]}}
        self.assertEqual(find_duplicate(manifest, [row]), row)
        with self.assertRaises(ValueError):
            find_duplicate(manifest, [{"values": {"SKU": "000-DEMO", "Zamówienie BL": "00017"}}])

    def test_existing_price_needs_exact_approved_change(self):
        manifest, snapshot = fixture()
        indexes = header_map(snapshot["headers"])
        snapshot["new_row"] = False
        for name in ["SKU", "Zamówienie BL"]:
            snapshot["cells"][indexes[name]]["userEnteredValue"] = {"stringValue": manifest["fields"][name]}
        snapshot["cells"][indexes["Cena Netto"]]["userEnteredValue"] = {"numberValue": 90}
        with self.assertRaises(ValueError):
            build_plan(manifest, snapshot)
        manifest["approved_changes"] = {"Cena Netto": {"previous_native": {"numberValue": 90}, "replacement": "100.00", "source": "DANE UMOWNE: zgoda na korektę"}}
        approve(manifest)
        self.assertEqual(build_plan(manifest, snapshot)["expected_values"]["Cena Netto"], {"numberValue": 100.0})

    def test_invalid_dropdown_cannot_be_written(self):
        manifest, snapshot = fixture()
        manifest["fields"]["Własność Spółki"] = "SP"
        approve(manifest)
        with self.assertRaises(ValueError):
            build_plan(manifest, snapshot)

    def test_draft_does_not_allow_bad_price_currency_or_fake_physical_quantity(self):
        manifest, snapshot = fixture()
        manifest["entry_mode"] = "draft"
        manifest["pending"] = ["Sprawdzenie"]
        manifest["currency"] = "EUR"
        approve(manifest)
        with self.assertRaises(ValueError):
            build_plan(manifest, snapshot)
        manifest["currency"] = "PLN"
        manifest["verified"]["physical_quantity"] = False
        approve(manifest)
        with self.assertRaises(ValueError):
            build_plan(manifest, snapshot)

    def test_blank_native_row_can_be_normalized_with_header_and_template(self):
        manifest, snapshot = fixture()
        response = {"spreadsheetId": snapshot["spreadsheet_id"], "sheets": [{
            "properties": {"title": "OUTLET", "sheetId": 17,
                           "gridProperties": {"columnCount": 22, "rowCount": 1000}},
            "data": [{"startRow": 0, "rowData": [{"values": [{"formattedValue": h} for h in snapshot["headers"]]}]},
                     {"startRow": 19}, {"startRow": 1, "rowData": [{"values": snapshot["template_cells"]}]}],
        }]}
        native = snapshot_from_cells(response, sheet_title="OUTLET", row_number=20,
                                     account_email="test@example.invalid", new_row=True, template_row_number=2)
        self.assertEqual(len(native["cells"]), 22)
        self.assertTrue(verify_readback(build_plan(manifest, native), apply_requests(native, build_plan(manifest, native)["requests"]))["verified"])

    def test_existing_intake_is_not_marked_as_not_received(self):
        manifest, snapshot = fixture()
        snapshot["new_row"] = False
        indexes = header_map(snapshot["headers"])
        for name in ["SKU", "Zamówienie BL"]:
            snapshot["cells"][indexes[name]]["userEnteredValue"] = {"stringValue": manifest["fields"][name]}
        snapshot["cells"][indexes["Dodane do systemu magazynowego"]]["userEnteredValue"] = {"boolValue": True}
        with self.assertRaisesRegex(ValueError, "wcześniejsze"):
            build_plan(manifest, snapshot)


if __name__ == "__main__":
    unittest.main()
