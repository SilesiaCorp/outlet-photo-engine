"""Validate an exact proposal and its recorded, directly human approval."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

COMPANIES = {"SILESIA PROTECH", "TRACER TEAM"}


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def proposal_hash(manifest: dict) -> str:
    return digest({key: value for key, value in manifest.items() if key != "approval"})


def decimal(value) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError("Brak liczby; FALSE/TRUE nie są kwotą ani ilością.")
    try:
        number = Decimal(str(value).replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("Nieprawidłowa liczba.") from exc
    if not number.is_finite():
        raise ValueError("Liczba musi być skończona.")
    return number


def validate_manifest(manifest: dict) -> None:
    if manifest.get("schema_version") != 1 or manifest.get("scope") != "sheet_entry":
        raise ValueError("Nieobsługiwany zakres manifestu; ten moduł zapisuje tylko arkusz.")
    UUID(str(manifest["operation_id"]))
    approval = manifest.get("approval") or {}
    if (approval.get("origin") != "human_user" or approval.get("approved") is not True
            or not approval.get("message") or not approval.get("parent_thread_id")
            or not approval.get("recorded_at")
            or approval.get("proposal_sha256") != proposal_hash(manifest)):
        raise ValueError("Brak zgodnej zgody człowieka na dokładny manifest.")
    target = manifest["destination"]
    if not target.get("spreadsheet_id") or not target.get("account_email"):
        raise ValueError("Brak jednoznacznego arkusza lub konta Google.")
    if target.get("sheet_title") not in {"OUTLET", "REKLAMACJE"}:
        raise ValueError("Zakres wpisu obejmuje OUTLET albo REKLAMACJE.")
    if not manifest.get("physical_receipt_id"):
        raise ValueError("Brak trwałego ID fizycznego przyjęcia; numer wiersza nie wystarcza.")
    identity = manifest["identity"]
    if not all(identity.get(key) for key in ["order_id", "sku", "product_id", "order_product_id"]):
        raise ValueError("Brak identyfikatorów produktu i konkretnej pozycji zamówienia.")
    confirmed = manifest.get("verified") or {}
    if confirmed.get("order_product_binding") is not True:
        raise ValueError("Niepotwierdzone powiązanie produktu z wybranym zamówieniem.")
    fields = manifest["fields"]
    if str(fields.get("Zamówienie BL")) != str(identity["order_id"]) or fields.get("SKU") != identity["sku"]:
        raise ValueError("Pola arkusza nie zgadzają się z tożsamością pozycji.")
    if not fields.get("Nazwa"):
        raise ValueError("Brak nazwy/modelu.")
    if fields.get("Dodane do systemu magazynowego") not in {None, False} or fields.get("Nr PZ system magazynowy"):
        raise ValueError("Wpis do arkusza nie może potwierdzać przyjęcia magazynowego.")
    mode = manifest.get("entry_mode")
    if mode not in {"complete", "draft"}:
        raise ValueError("Wymagany tryb complete albo jawnie zatwierdzony draft.")
    for key in ["Cena Netto", "Cena netto", "Cena brutto"]:
        if fields.get(key) is not None and fields.get(key) != "":
            if decimal(fields[key]) < 0 or manifest.get("currency") != "PLN":
                raise ValueError("Kwoty arkusza muszą być nieujemne i w PLN, także w szkicu.")
    if fields.get("VAT") is not None and fields.get("VAT") != "" and not 0 <= decimal(fields["VAT"]) <= 100:
        raise ValueError("VAT poza poprawnym zakresem.")
    if fields.get("Ilość") is not None and fields.get("Ilość") != "":
        quantity = decimal(fields["Ilość"])
        if quantity <= 0 or confirmed.get("physical_quantity") is not True:
            raise ValueError("Wpisana ilość musi być dodatnią, potwierdzoną ilością fizyczną.")
        if manifest.get("unit", "szt") == "szt" and quantity != quantity.to_integral_value():
            raise ValueError("Urządzenia w sztukach wymagają całkowitej ilości.")
    for key in ["Data zamówienia", "Data przyjęcia", "Data", "Data otrzymania"]:
        if fields.get(key) is not None and fields.get(key) != "":
            date.fromisoformat(str(fields[key]))
            if key in {"Data przyjęcia", "Data otrzymania"} and confirmed.get("receipt_date") is not True:
                raise ValueError("Wpisana data otrzymania wymaga potwierdzenia fizycznego przyjęcia.")
    if mode == "draft":
        if not manifest.get("pending"):
            raise ValueError("Szkic musi jawnie wskazać brakujące dane.")
        return
    for gate in ["physical_quantity", "receipt_date", "condition", "intake_value", "ownership"]:
        if confirmed.get(gate) is not True:
            raise ValueError(f"Niepotwierdzone dane: {gate}.")
    outlet = target["sheet_title"] == "OUTLET"
    net_key, receipt_key = ("Cena Netto", "Data przyjęcia") if outlet else ("Cena netto", "Data otrzymania")
    required = [net_key, "Cena brutto", "VAT", "Ilość", receipt_key]
    if any(fields.get(k) is None or fields.get(k) == "" for k in required):
        raise ValueError("Pełny wpis ma brakujące dane ilości, cen, VAT albo daty przyjęcia.")
    net, gross, vat, quantity = map(decimal, [fields[net_key], fields["Cena brutto"], fields["VAT"], fields["Ilość"]])
    if net < 0 or gross < 0 or not 0 <= vat <= 100 or quantity <= 0:
        raise ValueError("Kwoty/VAT/ilość poza poprawnym zakresem.")
    if manifest.get("unit", "szt") == "szt" and quantity != quantity.to_integral_value():
        raise ValueError("Urządzenia w sztukach wymagają całkowitej ilości.")
    from decimal import ROUND_HALF_UP
    if gross != (net * (1 + vat / 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):
        raise ValueError("Cena netto, brutto i VAT nie są spójne.")
    date.fromisoformat(str(fields[receipt_key]))
    if manifest.get("currency") != "PLN" or not manifest.get("evidence", {}).get("price_source"):
        raise ValueError("Pełny wpis wymaga netto PLN oraz źródła zaakceptowanej wyceny.")
    if outlet and fields.get("Własność Spółki") not in COMPANIES:
        raise ValueError("Niepotwierdzona spółka właściciela outletu.")
    if not outlet and (not fields.get("ID") or fields.get("Właściciel towaru") not in {"MY", "KLIENT"}
                       or fields.get("Sprzedawca") not in COMPANIES):
        raise ValueError("Reklamacja wymaga trwałego ID, sprzedawcy i własności MY/KLIENT.")
