"""Build precise native Sheets requests and verify their actual readback.

This module does not authenticate, send requests, create PZ, or infer approval.
The dedicated Codex worker executes a reviewed plan through its connected account.
"""
from __future__ import annotations

import copy
from datetime import date
from decimal import Decimal

from .approval import decimal, digest, proposal_hash, validate_manifest

TEXT_FIELDS = {"EAN Oryg.", "EAN Oryginalny", "SKU", "Zamówienie BL", "ID",
               "Zamówienie zakupowe", "Dokument korygujący"}
DATE_FIELDS = {"Data zamówienia", "Data przyjęcia", "Data", "Data otrzymania"}
MONEY_FIELDS = {"Cena Netto", "Cena netto", "Cena brutto"}
FLAGS = {"Sprzedano", "Dodane do systemu magazynowego", "lk", "Rozwiązane - wydano"}
PRESERVE = FLAGS | {"Nr PZ system magazynowy", "Wystawione"}
BOOLEAN_DEFAULTS = {"condition": {"type": "BOOLEAN"}}


def column_letter(index: int) -> str:
    value, result = index + 1, ""
    while value:
        value, digit = divmod(value - 1, 26)
        result = chr(65 + digit) + result
    return result


def header_map(headers: list[str]) -> dict[str, int]:
    result = {}
    for index, header in enumerate(headers):
        name = str(header).strip()
        if not name:
            continue
        if name in result:
            raise ValueError(f"Powtórzony nagłówek {name}; nie można bezpiecznie ustalić kolumny.")
        result[name] = index
    return result


def native_value(field: str, value, cell: dict) -> dict:
    if value is None:
        return {}
    if field in FLAGS:
        if not isinstance(value, bool):
            raise ValueError(f"{field} wymaga rzeczywistego boolean.")
        return {"boolValue": value}
    if field == "VAT":
        if cell.get("userEnteredFormat", {}).get("numberFormat", {}).get("type") != "PERCENT":
            raise ValueError("Niepotwierdzony format VAT; odczytaj komórkę procentową.")
        return {"numberValue": float(decimal(value) / 100)}
    if field in MONEY_FIELDS or field == "Ilość":
        return {"numberValue": float(decimal(value))}
    if field in DATE_FIELDS:
        return {"numberValue": (date.fromisoformat(str(value)) - date(1899, 12, 30)).days}
    # A string beginning with '=' remains a string, never a formula.
    return {"stringValue": str(value)}


def validate_cell(value: dict, cell: dict) -> None:
    condition = (cell.get("dataValidation") or {}).get("condition") or {}
    kind = condition.get("type")
    options = [option.get("userEnteredValue") for option in condition.get("values", [])]
    if kind == "ONE_OF_LIST" and value.get("stringValue") not in options:
        raise ValueError("Wartość nie należy do aktualnej listy wyboru.")
    if kind == "BOOLEAN" and ("boolValue" not in value or options):
        raise ValueError("Nieobsługiwany checkbox z wartościami niestandardowymi.")
    if kind in {"NUMBER_GREATER", "NUMBER_GREATER_THAN_EQ"}:
        actual, minimum = decimal(value.get("numberValue")), decimal(options[0])
        if actual < minimum or kind == "NUMBER_GREATER" and actual == minimum:
            raise ValueError("Liczba nie spełnia bieżącej walidacji komórki.")
    supported = {None, "ONE_OF_LIST", "BOOLEAN", "NUMBER_GREATER", "NUMBER_GREATER_THAN_EQ", "DATE_IS_VALID"}
    if kind not in supported:
        raise ValueError("Niestandardowa walidacja wymaga kontroli przed zapisem.")


def values_equal(first: dict, second: dict) -> bool:
    if "numberValue" in first and "numberValue" in second:
        return abs(decimal(first["numberValue"]) - decimal(second["numberValue"])) <= Decimal("0.000000001")
    return first == second


def row_is_empty(headers: list[str], cells: list[dict]) -> bool:
    for header, cell in zip(headers, cells):
        value = cell.get("userEnteredValue") or {}
        if not value or value == {"stringValue": ""}:
            continue
        if header in FLAGS and value == {"boolValue": False}:
            continue
        if header in MONEY_FIELDS and "formulaValue" in value:
            continue
        return False
    return True


def find_duplicate(manifest: dict, rows: list[dict]) -> dict | None:
    """Rows must be targeted existing sheet rows with header-keyed plain values."""
    op = manifest["operation_id"]
    for row in rows:
        values = row["values"]
        notes = str(values.get("Notatka AI") or "") + " " + str(values.get("Notatka") or "")
        if op in notes:
            return row
        if (str(values.get("Zamówienie BL") or "") == str(manifest["identity"]["order_id"])
                and str(values.get("SKU") or "") == manifest["identity"]["sku"]):
            resolution = manifest.get("evidence", {}).get("duplicate_resolution") or {}
            if not (resolution.get("separate_physical_receipt") is True
                    and resolution.get("source") and resolution.get("approved_by_human") is True):
                raise ValueError("Istnieje ten sam BL/SKU; sprawdź wpis/PZ i przypisanie sztuki przed nowym wierszem.")
    return None


def snapshot_from_cells(response: dict, *, sheet_title: str, row_number: int,
                        account_email: str, new_row: bool, template_row_number: int | None = None) -> dict:
    """Consume structuredContent from native get_spreadsheet_cells, not displayed text."""
    if "structuredContent" in response:
        response = response["structuredContent"]
    sheet = next((s for s in response.get("sheets", []) if s.get("properties", {}).get("title") == sheet_title), None)
    if sheet is None:
        raise ValueError("W odpowiedzi nie ma właściwej karty.")
    properties = sheet["properties"]
    width = properties["gridProperties"]["columnCount"]
    collected = {}
    for block in sheet.get("data", []):
        if block.get("startColumn", 0) == 0:
            # A separately requested, completely blank row may have no rowData.
            collected.setdefault(block.get("startRow", 0) + 1, [{} for _ in range(width)])
        for offset, row in enumerate(block.get("rowData", [])):
            number = block.get("startRow", 0) + offset + 1
            target = collected.setdefault(number, [{} for _ in range(width)])
            for column, cell in enumerate(row.get("values", []), block.get("startColumn", 0)):
                target[column] = copy.deepcopy(cell)
    if 1 not in collected or row_number not in collected:
        raise ValueError("Odczytaj nagłówki i docelowy wiersz, także gdy komórki są puste.")
    headers = [c.get("formattedValue") or c.get("userEnteredValue", {}).get("stringValue", "") for c in collected[1]]
    result = {
        "spreadsheet_id": response["spreadsheetId"], "account_email": account_email,
        "sheet_title": sheet_title, "sheet_id": properties["sheetId"],
        "grid_rows": properties["gridProperties"]["rowCount"], "row_number": row_number,
        "new_row": new_row, "headers": headers, "cells": collected[row_number],
    }
    if template_row_number is not None:
        if template_row_number not in collected:
            raise ValueError("Nie odczytano wzorcowego wiersza.")
        result.update(template_row_number=template_row_number, template_cells=collected[template_row_number])
    return result


def build_plan(manifest: dict, snapshot: dict) -> dict:
    validate_manifest(manifest)
    target = manifest["destination"]
    for key in ["spreadsheet_id", "account_email", "sheet_title"]:
        if target[key] != snapshot[key]:
            raise ValueError(f"Odczyt pochodzi z innego celu: {key}.")
    headers = snapshot["headers"]
    indexes = header_map(headers)
    row, sheet_id = snapshot["row_number"], snapshot["sheet_id"]
    if not 2 <= row <= snapshot["grid_rows"]:
        raise ValueError("Wiersz nie mieści się w odczytanej siatce. Najpierw rozszerz i ponownie odczytaj.")
    cells = copy.deepcopy(snapshot["cells"])
    if len(cells) != len(headers):
        raise ValueError("Niepełny odczyt komórek docelowego wiersza.")
    if snapshot["new_row"] and not row_is_empty(headers, cells):
        raise ValueError("Docelowy wiersz nie jest pusty; odczytaj go ponownie.")
    if not snapshot["new_row"]:
        for name, expected in [("SKU", manifest["identity"]["sku"]), ("Zamówienie BL", manifest["identity"]["order_id"])]:
            actual = cells[indexes[name]].get("effectiveValue") or cells[indexes[name]].get("userEnteredValue") or {}
            actual_text = actual.get("stringValue", actual.get("numberValue", ""))
            if str(actual_text) != str(expected):
                raise ValueError("Wiersz po sortowaniu ma inną tożsamość; wyszukaj trwałe OP/ID.")
        added = cells[indexes["Dodane do systemu magazynowego"]].get("userEnteredValue", {}).get("boolValue")
        document = cells[indexes["Nr PZ system magazynowy"]].get("userEnteredValue") or {}
        if added is True or document not in [{}, {"stringValue": ""}]:
            raise ValueError("Wiersz ma wcześniejsze przyjęcie; odtwórz jego wynik zamiast planować nowy wpis.")
    requests, expected_values, preserved_formulas = [], {}, {}
    if snapshot["new_row"] and snapshot.get("template_cells"):
        template = snapshot["template_cells"]
        if len(template) != len(headers) or snapshot["template_row_number"] == row:
            raise ValueError("Nieprawidłowy wzorzec rodzimej struktury wiersza.")
        for kind in ["PASTE_FORMAT", "PASTE_DATA_VALIDATION"]:
            requests.append({"copyPaste": {
                "source": {"sheetId": sheet_id, "startRowIndex": snapshot["template_row_number"] - 1,
                           "endRowIndex": snapshot["template_row_number"], "startColumnIndex": 0,
                           "endColumnIndex": len(headers)},
                "destination": {"sheetId": sheet_id, "startRowIndex": row - 1, "endRowIndex": row,
                                "startColumnIndex": 0, "endColumnIndex": len(headers)},
                "pasteType": kind, "pasteOrientation": "NORMAL",
            }})
        for index, exemplar in enumerate(template):
            for property_name in ["userEnteredFormat", "dataValidation"]:
                cells[index].pop(property_name, None)
                if property_name in exemplar:
                    cells[index][property_name] = copy.deepcopy(exemplar[property_name])
    fields = copy.deepcopy(manifest["fields"])
    for name in fields:
        if name not in indexes:
            raise ValueError(f"Aktualny arkusz nie ma kolumny {name}; wyjaśnij zmianę schematu.")
    if snapshot["new_row"]:
        fields.update({name: False for name in FLAGS if name in indexes})
        if "Wystawione" in indexes and fields.get("Wystawione") is None:
            fields["Wystawione"] = "NIE"
    for name in PRESERVE:
        if not snapshot["new_row"]:
            fields.pop(name, None)
    status_name = "Notatka AI" if snapshot["sheet_title"] == "OUTLET" else "Notatka"
    if status_name not in indexes:
        raise ValueError("Brak kolumny notatki dla trwałego OP.")
    previous_note = cells[indexes[status_name]].get("userEnteredValue", {}).get("stringValue", "")
    status = "WPISANE" if manifest["entry_mode"] == "complete" else "WYMAGA DANYCH"
    marker = f"ARKUSZ: {status} · OP: {manifest['operation_id']} · MAG: NIEPRZYJĘTE"
    parts = [previous_note, fields.get(status_name), marker]
    fields[status_name] = "\n".join(dict.fromkeys(str(part) for part in parts if part))
    note_updates = {}
    for name, value in fields.items():
        if value is None:
            continue
        index, cell = indexes[name], cells[indexes[name]]
        if cell.get("chipRuns"):
            raise ValueError("Docelowa komórka ma chip; sklasyfikuj go przed zmianą.")
        native = native_value(name, value, cell)
        validate_cell(native, cell)
        formula = cell.get("userEnteredValue", {}).get("formulaValue")
        if formula:
            if name not in MONEY_FIELDS:
                raise ValueError("Nie nadpisuj formuły w polu wejściowym.")
            preserved_formulas[name] = formula
            expected_values[name] = native
            continue
        original = cell.get("userEnteredValue") or {}
        if (not snapshot["new_row"] and name not in {"Notatka", "Notatka AI"}
                and original not in [{}, {"stringValue": ""}] and not values_equal(original, native)):
            change = manifest.get("approved_changes", {}).get(name) or {}
            if change.get("previous_native") != original or change.get("replacement") != value or not change.get("source"):
                raise ValueError(f"Istniejące {name} ma inną wartość; nie nadpisuj jej bez rozliczenia konfliktu.")
        if name == "Notatka" and status_name != name:
            old = cell.get("userEnteredValue", {}).get("stringValue", "")
            native = {"stringValue": "\n".join(dict.fromkeys(p for p in [old, str(value)] if p))}
        block = {"sheetId": sheet_id, "startRowIndex": row - 1, "endRowIndex": row,
                 "startColumnIndex": index, "endColumnIndex": index + 1}
        update = {"userEnteredValue": native}
        mask = "userEnteredValue"
        if name == status_name:
            audit = f"OP: {manifest['operation_id']}\nManifest SHA-256: {proposal_hash(manifest)}\n"
            audit += f"Źródło: BL {manifest['identity']['order_id']}, pozycja {manifest['identity']['order_product_id']}\n"
            audit += "Braki: " + "; ".join(manifest.get("pending") or [])
            update["note"] = "\n".join(filter(None, [cell.get("note"), audit]))
            note_updates[name] = update["note"]
            mask += ",note"
        requests.append({"updateCells": {"range": block, "rows": [{"values": [update]}], "fields": mask}})
        if name in DATE_FIELDS or name in TEXT_FIELDS:
            number_format = {"type": "DATE", "pattern": "yyyy-MM-dd"} if name in DATE_FIELDS else {"type": "TEXT"}
            requests.append({"repeatCell": {"range": block, "cell": {"userEnteredFormat": {"numberFormat": number_format}},
                                            "fields": "userEnteredFormat.numberFormat"}})
            cell.setdefault("userEnteredFormat", {})["numberFormat"] = number_format
        if name in FLAGS and not cell.get("dataValidation"):
            requests.append({"setDataValidation": {"range": block, "rule": BOOLEAN_DEFAULTS}})
            cell["dataValidation"] = BOOLEAN_DEFAULTS
        expected_values[name] = native
    title = "'" + snapshot["sheet_title"].replace("'", "''") + "'"
    return {
        "schema_version": 1, "operation_id": manifest["operation_id"],
        "proposal_sha256": proposal_hash(manifest), "preimage_sha256": digest(snapshot),
        "spreadsheet_id": snapshot["spreadsheet_id"], "account_email": snapshot["account_email"],
        "sheet_id": sheet_id, "sheet_title": snapshot["sheet_title"], "row_number": row,
        "range": f"{title}!A{row}:{column_letter(len(headers) - 1)}{row}",
        "requests": requests, "expected_values": expected_values, "expected_notes": note_updates,
        "preserved_formulas": preserved_formulas, "before_cells": snapshot["cells"],
        "expected_structure": cells, "new_row": snapshot["new_row"], "headers": headers,
    }


def assert_preimage(plan: dict, fresh_snapshot: dict) -> None:
    if plan["preimage_sha256"] != digest(fresh_snapshot):
        raise ValueError("Wiersz, schemat lub walidacja zmieniły się przed zapisem. Zbuduj nowy plan.")


def verify_readback(plan: dict, snapshot: dict) -> dict:
    for name in ["spreadsheet_id", "account_email", "sheet_id", "sheet_title", "row_number", "headers"]:
        if plan[name] != snapshot[name]:
            raise ValueError("Odczyt wyniku ma inny cel lub schemat.")
    indexes = header_map(snapshot["headers"])
    for name, native in plan["expected_values"].items():
        cell = snapshot["cells"][indexes[name]]
        if name in plan["preserved_formulas"]:
            if cell.get("userEnteredValue", {}).get("formulaValue") != plan["preserved_formulas"][name]:
                raise ValueError("Formuła ceny została zmieniona.")
            actual = cell.get("effectiveValue") or {}
        else:
            actual = cell.get("userEnteredValue") or {}
        if not values_equal(actual, native):
            raise ValueError(f"Zapis/obliczenie {name} nie zgadza się z manifestem.")
        validate_cell(native, cell)
        if name in plan["expected_notes"] and cell.get("note") != plan["expected_notes"][name]:
            raise ValueError("Nie potwierdzono trwałego OP i notatki audytu.")
        if name == "VAT" and cell.get("userEnteredFormat", {}).get("numberFormat", {}).get("type") != "PERCENT":
            raise ValueError("VAT nie zachował formatu procentowego.")
        if name in DATE_FIELDS | TEXT_FIELDS:
            kind = "DATE" if name in DATE_FIELDS else "TEXT"
            if cell.get("userEnteredFormat", {}).get("numberFormat", {}).get("type") != kind:
                raise ValueError("Nie zachowano rodzimego typu daty/identyfikatora.")
    for index, name in enumerate(plan["headers"]):
        current = snapshot["cells"][index]
        if name not in plan["expected_values"]:
            if current.get("userEnteredValue", {}) != plan["before_cells"][index].get("userEnteredValue", {}):
                raise ValueError("Zmieniono nieobjętą zakresem komórkę.")
        expected = plan["expected_structure"][index].get("dataValidation")
        if name in FLAGS and name in plan["expected_values"] and not expected:
            expected = BOOLEAN_DEFAULTS
        if current.get("dataValidation") != expected:
            raise ValueError("Walidacja wiersza nie została zachowana.")
        if current.get("userEnteredFormat", {}) != plan["expected_structure"][index].get("userEnteredFormat", {}):
            raise ValueError("Format komórki nie zgadza się z planem rodzimego wiersza.")
    return {
        "verified": True, "operation_id": plan["operation_id"], "proposal_sha256": plan["proposal_sha256"],
        "range": plan["range"], "readback_sha256": digest(snapshot),
        "sheet_url": f"https://docs.google.com/spreadsheets/d/{plan['spreadsheet_id']}/edit#gid={plan['sheet_id']}&range=A{plan['row_number']}",
        "warehouse_intake": False,
    }
