"""Source-backed purchase context and a reviewable outlet sheet proposal."""
from __future__ import annotations

import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

CENT = Decimal("0.01")
PURCHASE_FIELDS = {"price": "41787", "seller": "42651", "buyer": "45809"}
PRICE_LINE = re.compile(
    r"^(?:(?P<quantity>\d+(?:[.,]\d+)?)\s*:\s*)?"
    r"(?P<amount>\d+(?:[.,]\d+)?)\s*(?:v\s*(?P<vat>\d+(?:[.,]\d+)?))?$",
    re.IGNORECASE,
)


def money(value: Decimal) -> str:
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


def company_name(value: Any) -> str | None:
    text = re.sub(r"[^A-Z]", "", str(value or "").upper())
    if text.startswith("SILESIAPROTECH"):
        return "SILESIA PROTECH"
    if text.startswith("TRACERTEAM"):
        return "TRACER TEAM"
    return None


def purchase_context(order: dict) -> dict:
    custom = order.get("custom_extra_fields") or {}
    raw = str(custom.get(PURCHASE_FIELDS["price"]) or "").strip()
    seller = str(custom.get(PURCHASE_FIELDS["seller"]) or "").strip()
    products = order.get("products") or []
    result: dict[str, Any] = {
        "supplier": None, "seller_account": None, "purchase_account": None,
        "purchase_buyer": company_name(custom.get(PURCHASE_FIELDS["buyer"])),
        "currency": "PLN", "unit_net": None, "unit_gross": None, "vat_rate": None,
        "purchase_quantity": None, "source": "Base custom_extra_fields.41787",
        "input_price_basis": None, "issues": [],
    }
    # These notes identify the supplier; customer delivery/invoice data are never used.
    note = str(order.get("extra_field_1") or "").strip()
    if len(products) == 1 and "|" in note and "\n" not in note and ";" not in note:
        supplier = note.split("|", 1)[1].split(",", 1)[0].strip()
        result["supplier"] = supplier or None
    if len(products) == 1 and seller and "\n" not in seller and ";" not in seller:
        account = re.sub(r"^\d+(?:[.,]\d+)?\s*:\s*", "", seller)
        parts = [part.strip() for part in account.split("|")]
        if len(parts) <= 2:
            result["seller_account"] = parts[0] or None
            result["purchase_account"] = parts[1] if len(parts) == 2 and parts[1] else None
    if not raw:
        result["issues"].append("missing_purchase_price")
        return result
    if len(products) != 1 or re.search(r"[|;\n]", raw):
        result["issues"].append("purchase_allocation_requires_document")
        return result
    match = PRICE_LINE.fullmatch(raw)
    if match is None:
        result["issues"].append("unrecognized_purchase_price_format")
        return result
    try:
        amount = Decimal(match["amount"].replace(",", "."))
        quantity = Decimal((match["quantity"] or "1").replace(",", "."))
        expected = Decimal(str(products[0].get("quantity")))
    except (InvalidOperation, TypeError):
        result["issues"].append("invalid_purchase_quantity")
        return result
    result["purchase_quantity"] = str(quantity)
    # The prefix is a quantity, never an order-product position or identifier.
    if quantity <= 0 or quantity != expected:
        result["issues"].append("purchase_quantity_mismatch")
        return result
    if match["vat"] is None:
        result["input_price_basis"] = "legacy_gross"
        result["unit_gross"] = money(amount)
        result["issues"].append("purchase_vat_requires_document")
        return result
    vat = Decimal(match["vat"].replace(",", "."))
    if vat > 100:
        result["issues"].append("invalid_purchase_vat")
        return result
    result.update(
        input_price_basis="explicit_net", unit_net=money(amount),
        unit_gross=money(amount * (1 + vat / 100)), vat_rate=str(vat),
    )
    return result


def local_order_date(timestamp: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(timestamp), ZoneInfo("Europe/Warsaw")).date().isoformat()
    except (ValueError, TypeError, OSError, OverflowError, ZoneInfoNotFoundError):
        return None


def sheet_verdict(order: dict, product: dict, invoices: list[dict], *,
                 original_ean: str, condition_note: str | None = None) -> dict:
    purchase = purchase_context(order)
    normal = [i for i in invoices if i.get("type") == "normal"]
    sellers = {company_name(i.get("seller")) for i in normal if company_name(i.get("seller"))}
    owner = next(iter(sellers)) if len(sellers) == 1 else None
    owner_source = "sale_invoice_seller" if owner else None
    if not normal:
        source = str(order.get("order_source") or "").casefold()
        if source.startswith("kaufland"):
            owner, owner_source = "TRACER TEAM", "channel_rule_requires_sale_verification"
        elif source == "ebay":
            owner, owner_source = "SILESIA PROTECH", "channel_rule_requires_sale_verification"
    corrections = [i["number"] for i in invoices if i.get("type") == "correcting" and i.get("number")]
    note = condition_note or "Stan, kompletność i test urządzenia wymagają potwierdzenia."
    supplier_note = "; ".join(filter(None, [
        f"Dostawca zakupu: {purchase['supplier']}" if purchase["supplier"] else None,
        f"Sprzedawca zakupu: {purchase['seller_account']}" if purchase["seller_account"] else None,
        note,
    ]))
    fields = {
        "Sprzedano": False, "Dodane do systemu magazynowego": False,
        "Nr PZ system magazynowy": None, "lk": False,
        "Nazwa": product.get("name"), "EAN Oryg.": original_ean or None,
        "SKU": product.get("sku"), "Cena Netto": purchase["unit_net"],
        "Cena brutto": purchase["unit_gross"], "VAT": purchase["vat_rate"],
        "Ilość": product.get("quantity"), "Zamówienie BL": str(order.get("order_id")),
        "Data zamówienia": local_order_date(order.get("date_add")), "Data przyjęcia": None,
        "Dokument korygujący": "; ".join(corrections) or None,
        "Zamówienie zakupowe": None, "Konto Allegro": purchase["purchase_account"],
        "Kupujący": purchase["purchase_buyer"], "Własność Spółki": owner,
        "Wystawione": None, "Notatka": supplier_note,
        "Notatka AI": "MAG: WYMAGA DANYCH · przypisanie sztuki i wycena przyjęcia do potwierdzenia",
    }
    sale_prices = {
        "currency": order.get("currency"), "unit_gross": product.get("price_brutto"),
        "vat_rate": product.get("tax_rate"), "source": "Base order product; sale, not purchase",
    }
    return {
        "purchase": purchase, "sale": sale_prices, "sheet_name": "OUTLET", "sheet_fields": fields,
        "price_status": "proposal_from_purchase_cost_requires_intake_valuation_approval",
        "owner_source": owner_source, "owner_conditional_on_unit_binding": True,
        "quantity_source": "order_quantity_not_physical_receipt", "ready_to_add": False,
        "pending": ["physical_unit_binding", "physical_received_quantity", "receipt_date",
                    "device_condition_completeness_test", "approved_current_owner_intake_value",
                    "purchase_document_number_if_available", "duplicate_check_and_intake_authorization"],
    }


def markdown_verdict(verdict: dict) -> str:
    purchase = verdict["purchase"]
    lines = ["**Werdykt — dane do przygotowania OUTLETU**", "",
             f"- Dostawca zakupu: **{purchase['supplier'] or 'BRAK DANYCH'}**; "
             f"sprzedawca: {purchase['seller_account'] or 'BRAK DANYCH'}.",
             f"- Zakup przez: **{purchase['purchase_account'] or 'BRAK DANYCH'}**; "
             f"spółka kupująca: **{purchase['purchase_buyer'] or 'BRAK DANYCH'}**.",
             "", "| Pole arkusza | Wartość / propozycja |", "| --- | --- |"]
    for name, value in verdict["sheet_fields"].items():
        if value is None:
            text = "BRAK DANYCH / do potwierdzenia"
        elif isinstance(value, bool):
            text = "TRUE" if value else "FALSE"
        else:
            text = str(value).replace("|", "\\|").replace("\n", " ")
            if name in {"Cena Netto", "Cena brutto"}:
                text = text.replace(".", ",") + " PLN — koszt zakupu; wycena przyjęcia do akceptacji"
            elif name == "VAT":
                text += "% zakupu"
            elif name == "Ilość":
                text += " wg zamówienia; ilość fizyczna do potwierdzenia"
            elif name == "Zamówienie BL":
                text += " — kandydat"
            elif name == "Własność Spółki":
                text += " — po potwierdzeniu przypisania sztuki"
        lines.append(f"| {name} | {text} |")
    lines += ["", "Ceny i VAT zakupu są oddzielone od ceny sprzedaży klientowi. "
              "Propozycja nie upoważnia do wpisu ani przyjęcia PZ; "
              "koszt obecnego właściciela może wymagać dokumentu transferu SP→TT."]
    return "\n".join(lines)
