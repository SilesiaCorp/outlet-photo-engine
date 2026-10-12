from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from outlet_engine.verdict import markdown_verdict, purchase_context, sheet_verdict


def source(price="1: 100v23", quantity=1):
    return {
        "order_id": 17, "order_source": "kaufland", "currency": "EUR", "date_add": 1785686944,
        "extra_field_1": "0123456789012 | Dostawca Demonstracyjny,adres prywatny",
        "custom_extra_fields": {"41787": price, "42651": "1: sklep-demo | Konto-demo", "45809": "Silesia Protech"},
        "products": [{"sku": "DEMO-001", "name": "Produkt demonstracyjny", "quantity": quantity,
                      "price_brutto": 200, "tax_rate": 19}],
    }


class OutletVerdictTests(unittest.TestCase):
    def test_v_marker_means_net_and_gross_is_calculated(self):
        value = purchase_context(source("1: 123,45v23"))
        self.assertEqual(value["unit_net"], "123.45")
        self.assertEqual(value["unit_gross"], "151.84")
        self.assertEqual(value["vat_rate"], "23")

    def test_prefix_is_quantity_not_position_and_price_is_unit_price(self):
        value = purchase_context(source("2: 100v23", quantity=2))
        self.assertEqual(value["purchase_quantity"], "2")
        self.assertEqual(value["unit_net"], "100.00")
        self.assertEqual(value["unit_gross"], "123.00")

    def test_mismatched_purchase_quantity_is_not_assigned(self):
        value = purchase_context(source("2: 100v23", quantity=1))
        self.assertIsNone(value["unit_net"])
        self.assertIn("purchase_quantity_mismatch", value["issues"])

    def test_legacy_gross_does_not_guess_purchase_vat(self):
        value = purchase_context(source("1: 123"))
        self.assertEqual(value["unit_gross"], "123.00")
        self.assertIsNone(value["unit_net"])
        self.assertIsNone(value["vat_rate"])

    def test_zero_and_explicit_zero_vat_are_valid(self):
        value = purchase_context(source("1: 0v0"))
        self.assertEqual(value["unit_net"], "0.00")
        self.assertEqual(value["unit_gross"], "0.00")
        self.assertEqual(value["vat_rate"], "0")

    def test_multiple_products_require_an_allocation_document(self):
        order = source("1: 100v23;1: 200v23")
        order["products"].append({"sku": "DEMO-002", "quantity": 1})
        value = purchase_context(order)
        self.assertIsNone(value["unit_net"])
        self.assertIsNone(value["supplier"])
        self.assertIn("purchase_allocation_requires_document", value["issues"])

    def test_purchase_company_sale_owner_and_currencies_are_separate(self):
        order = source()
        invoices = [{"type": "normal", "seller": "TRACER TEAM Sp. z o.o.\nAdres"}]
        value = sheet_verdict(order, order["products"][0], invoices, original_ean="0123456789012")
        fields = value["sheet_fields"]
        self.assertEqual(fields["Kupujący"], "SILESIA PROTECH")
        self.assertEqual(fields["Własność Spółki"], "TRACER TEAM")
        self.assertEqual(fields["Konto Allegro"], "Konto-demo")
        self.assertEqual(fields["Cena Netto"], "100.00")
        self.assertEqual(fields["VAT"], "23")
        self.assertEqual(value["purchase"]["currency"], "PLN")
        self.assertEqual(value["sale"]["currency"], "EUR")

    def test_unknown_receipt_and_intake_price_are_never_approved(self):
        order = source()
        value = sheet_verdict(order, order["products"][0], [], original_ean="0123456789012")
        self.assertIsNone(value["sheet_fields"]["Data przyjęcia"])
        self.assertIsNone(value["sheet_fields"]["Nr PZ system magazynowy"])
        self.assertFalse(value["sheet_fields"]["Dodane do systemu magazynowego"])
        self.assertFalse(value["ready_to_add"])
        self.assertIn("requires_intake_valuation_approval", value["price_status"])

    def test_all_outlet_columns_present_and_customer_data_excluded(self):
        order = source()
        order.update(email="private@example.invalid", phone="private", invoice_fullname="private")
        invoices = [{"type": "correcting", "number": "KOR/DEMO", "invoice_fullname": "private"}]
        value = sheet_verdict(order, order["products"][0], invoices, original_ean="0123456789012")
        self.assertEqual(len(value["sheet_fields"]), 22)
        self.assertEqual(value["sheet_fields"]["Dokument korygujący"], "KOR/DEMO")
        self.assertNotIn("private", str(value))
        self.assertNotIn("adres prywatny", str(value))
        self.assertIn("BRAK DANYCH", markdown_verdict(value))

    def test_invoice_seller_conflict_never_chooses_an_owner(self):
        order = source()
        invoices = [{"type": "normal", "seller": "TRACER TEAM"},
                    {"type": "normal", "seller": "SILESIA PROTECH"}]
        value = sheet_verdict(order, order["products"][0], invoices, original_ean="0123456789012")
        self.assertIsNone(value["sheet_fields"]["Własność Spółki"])


if __name__ == "__main__":
    unittest.main()
