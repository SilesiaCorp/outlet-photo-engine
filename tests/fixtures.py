from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from outlet_engine.approval import proposal_hash


def approve(manifest):
    # Synthetic human evidence for unit tests; not an operational authorization.
    manifest["approval"] = {"origin": "human_user", "approved": True,
                            "message": "DANE UMOWNE: dodaj pokazany wpis do arkusza.",
                            "parent_thread_id": "synthetic-parent", "recorded_at": "2026-10-12T10:00:00Z",
                            "proposal_sha256": proposal_hash(manifest)}
    return manifest


def fixture(sheet="OUTLET"):
    schema = json.loads((ROOT / "configs/sheet-schema.json").read_text(encoding="utf-8"))["sheets"][sheet]
    cells = copy.deepcopy(schema["template"])
    fields = {
        "Nazwa": "Produkt umowny MODEL-100/01", "SKU": "000-DEMO", "Zamówienie BL": "00017",
        "Cena brutto": "123.00", "VAT": "23", "Ilość": 1,
        "Dodane do systemu magazynowego": False, "Nr PZ system magazynowy": None,
        "Notatka": "Opakowanie uszkodzone. Urządzenia nie testowano.",
    }
    if sheet == "OUTLET":
        fields.update({"EAN Oryg.": "0123456789012", "Cena Netto": "100.00",
                       "Data zamówienia": "2026-09-10", "Data przyjęcia": "2026-10-10",
                       "Własność Spółki": "TRACER TEAM", "Konto Allegro": "Konto-demo",
                       "Kupujący": "SILESIA PROTECH", "Notatka AI": "Źródło wyceny: dokument demonstracyjny."})
    else:
        fields.update({"EAN Oryginalny": "0123456789012", "Cena netto": "100.00", "Data": "2026-09-10",
                       "Data otrzymania": "2026-10-10", "Sprzedawca": "TRACER TEAM", "ID": "DEMO-R-001",
                       "Właściciel towaru": "MY", "Status": "Towar po reklamacji u nas",
                       "Informacja": "INNE - komentarz"})
    manifest = approve({
        "schema_version": 1, "scope": "sheet_entry", "entry_mode": "complete",
        "operation_id": "00000000-0000-4000-8000-000000000001", "physical_receipt_id": "RECEIPT-DEMO-001",
        "destination": {"spreadsheet_id": "SYNTHETIC-SHEET", "sheet_title": sheet,
                        "account_email": "test@example.invalid"},
        "identity": {"order_id": "00017", "sku": "000-DEMO", "product_id": 17, "order_product_id": 1701},
        "verified": {key: True for key in ["order_product_binding", "physical_quantity", "receipt_date",
                                          "condition", "intake_value", "ownership"]},
        "currency": "PLN", "unit": "szt", "fields": fields, "pending": [],
        "evidence": {"price_source": "Dokument umowny", "condition_source": "Pracownik: nie testowano"},
    })
    snapshot = {"spreadsheet_id": "SYNTHETIC-SHEET", "account_email": "test@example.invalid",
                "sheet_title": sheet, "sheet_id": 17, "row_number": 20, "grid_rows": 1000,
                "new_row": True, "headers": schema["headers"], "cells": cells,
                "template_row_number": 2, "template_cells": copy.deepcopy(cells)}
    return manifest, snapshot


def apply_requests(snapshot, requests):
    """A small native-cell model for testing actual payload shapes and readback."""
    result = copy.deepcopy(snapshot)
    for request in requests:
        if "copyPaste" in request:
            property_name = "userEnteredFormat" if request["copyPaste"]["pasteType"] == "PASTE_FORMAT" else "dataValidation"
            for index, cell in enumerate(result["template_cells"]):
                result["cells"][index].pop(property_name, None)
                if property_name in cell:
                    result["cells"][index][property_name] = copy.deepcopy(cell[property_name])
        elif "updateCells" in request:
            update = request["updateCells"]
            index = update["range"]["startColumnIndex"]
            result["cells"][index].update(copy.deepcopy(update["rows"][0]["values"][0]))
        elif "repeatCell" in request:
            update = request["repeatCell"]
            result["cells"][update["range"]["startColumnIndex"]].setdefault("userEnteredFormat", {})["numberFormat"] = copy.deepcopy(update["cell"]["userEnteredFormat"]["numberFormat"])
        elif "setDataValidation" in request:
            update = request["setDataValidation"]
            result["cells"][update["range"]["startColumnIndex"]]["dataValidation"] = copy.deepcopy(update["rule"])
        else:
            raise AssertionError("Unknown request")
    return result
