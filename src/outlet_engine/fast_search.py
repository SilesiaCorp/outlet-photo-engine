"""Identifier-first discovery that stops at the first fresh, plausible candidate."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from .verdict import purchase_context, sheet_verdict

NOTE_FIELDS = {"2"}  # Base's standard Notes field; extra_field_2 is also inspected.
RETURN_LABELS = {"numerzwrotu", "numeryzwrotow", "nrzwrotu", "idzwrotu", "rma",
                 "kodzwrotu", "numerzgloszeniazwrotu", "returnnumber", "returnid", "returnreference", "returncode"}
TRACK_LABELS = {"numerprzesylki", "numerprzesylkizwrotnej", "trackingnumber", "returntracking"}
LABELLED_NUMBER = re.compile(
    r"(?:\b(?:numer|nr|id|number)\s*[_:.-]*\s*zwrot\w*|\bzwrot\w*\s+(?:nr|numer|id)|\brma)"
    r"\s*[:#=_-]*\s*([a-z0-9][a-z0-9/_-]{2,99})", re.I,
)


def fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).replace("ł", "l").replace("Ł", "L")
    return "".join(c for c in value.casefold() if c.isalnum())


def reference(value) -> str:
    # Preserve every digit, including leading zeroes. Do not guess missing digits.
    return re.sub(r"[\s/_-]+", "", str(value or "").strip()).casefold()


def exact_token(text: str, token: str) -> bool:
    parts = re.findall(r"[a-z]+|[0-9]+|[^a-z0-9\s/_-]+", token.strip(), re.I)
    if not parts or not parts[0]:
        return False
    pattern = r"(?<![a-z0-9])" + r"[\s/_-]*".join(re.escape(p) for p in parts) + r"(?![a-z0-9])"
    return bool(re.search(pattern, text, re.I))


def named_return_field(name: str) -> bool:
    return any(name.startswith(label) for label in RETURN_LABELS)


def field_definitions(response: dict) -> dict[str, dict]:
    raw = response.get("extra_fields")
    if isinstance(raw, dict):
        raw = list(raw.values())
    if not isinstance(raw, list):
        raise RuntimeError("Niepełny odczyt definicji pól dodatkowych.")
    return {str(f["extra_field_id"]): f for f in raw}


def extract_references(record: dict, definitions: dict[str, dict], *, native_return=False) -> list[dict]:
    found = []
    def add(kind, value, source):
        if not isinstance(value, (str, int)) or isinstance(value, bool):
            return
        value = str(value).strip()
        if value and len(value) <= 100 and "@" not in value:
            found.append({"kind": kind, "value": value, "source": source})
    if native_return:
        for key in ["return_id", "external_order_id", "reference_number"]:
            add("return", record.get(key), key)
    add("tracking", record.get("delivery_package_nr"), "delivery_package_nr")
    notes = [(key, record.get(key)) for key in ["admin_comments", "extra_field_2"]]
    custom = record.get("custom_extra_fields") or {}
    if isinstance(custom, dict):
        for key, value in custom.items():
            definition = definitions.get(str(key)) or {}
            name = fold(str(definition.get("name") or ""))
            if named_return_field(name):
                add("return", value, f"custom_extra_fields.{key}")
            elif name in TRACK_LABELS:
                add("tracking", value, f"custom_extra_fields.{key}")
            if str(key) in NOTE_FIELDS or name in {"notatki", "notes", "notatkidozamowienia"}:
                notes.append((f"custom_extra_fields.{key}", value))
            # Explicitly labelled identifiers can occur in another text field.
            if definition.get("editor_type") != "file" and isinstance(value, str):
                for match in LABELLED_NUMBER.finditer(value):
                    if any(c.isdigit() for c in match[1]):
                        add("return", match[1], f"custom_extra_fields.{key}")
    for source, text in notes:
        if isinstance(text, str):
            for match in LABELLED_NUMBER.finditer(text):
                if any(c.isdigit() for c in match[1]):
                    add("return", match[1], source)
    return [dict(t) for t in {tuple(sorted(row.items())) for row in found}]


def match_reference(record: dict, definitions: dict[str, dict], token: str, kind: str,
                    *, native_return=False) -> str | None:
    for item in extract_references(record, definitions, native_return=native_return):
        if item["kind"] == kind and reference(item["value"]) == reference(token):
            return item["source"]
    # New return numbers may be free text in the order's Notes, not a return-manager entry.
    if kind == "return":
        notes = {"admin_comments": record.get("admin_comments"), "extra_field_2": record.get("extra_field_2")}
        custom = record.get("custom_extra_fields") or {}
        if isinstance(custom, dict):
            for key, value in custom.items():
                name = fold(str((definitions.get(str(key)) or {}).get("name") or ""))
                if str(key) in NOTE_FIELDS or named_return_field(name) or name in {"notatki", "notes", "notatkidozamowienia"}:
                    notes[f"custom_extra_fields.{key}"] = value
        return next((source for source, text in notes.items()
                     if isinstance(text, str) and exact_token(text, token)), None)
    return None


class FastCache:
    def __init__(self, path: Path):
        self.db = sqlite3.connect(path, timeout=10)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT, at REAL);
            CREATE TABLE IF NOT EXISTS hints (order_id INTEGER PRIMARY KEY, payload TEXT, at REAL);
            CREATE TABLE IF NOT EXISTS refs (kind TEXT, value TEXT, order_id INTEGER, source TEXT,
              return_id INTEGER, PRIMARY KEY(kind,value,order_id,source));
        """)

    def close(self):
        self.db.close()

    def metadata(self, key: str, max_age: float):
        row = self.db.execute("SELECT value,at FROM metadata WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row and 0 <= time.time() - row[1] <= max_age else None

    def save_metadata(self, key: str, value):
        self.db.execute("INSERT OR REPLACE INTO metadata VALUES (?,?,?)",
                        (key, json.dumps(value, ensure_ascii=False), time.time()))
        self.db.commit()

    def remember(self, order: dict, refs: list[dict], *, return_id: int | None = None, commit=True):
        # order is already sanitized by the shared discovery sanitizer.
        self.db.execute("INSERT OR REPLACE INTO hints VALUES (?,?,?)",
                        (order["order_id"], json.dumps(order, ensure_ascii=False), time.time()))
        self.save_refs(order["order_id"], refs, return_id=return_id, commit=False)
        if commit:
            self.db.commit()

    def save_refs(self, order_id: int, refs: list[dict], *, return_id=None, commit=True):
        for item in refs:
            self.db.execute("INSERT OR REPLACE INTO refs VALUES (?,?,?,?,?)", (
                item["kind"], reference(item["value"]), order_id, item["source"], return_id,
            ))
        if commit:
            self.db.commit()

    def remember_batch(self, rows: list[tuple[dict, list[dict]]]):
        for order, refs in rows:
            self.remember(order, refs, commit=False)
        self.db.commit()

    def reference_hints(self, kind: str, token: str) -> list[dict]:
        return [{"order_id": row[0], "source": row[1], "return_id": row[2]}
                for row in self.db.execute("SELECT order_id,source,return_id FROM refs WHERE kind=? AND value=?",
                                           (kind, reference(token)))]

    def orders(self) -> list[dict]:
        return [json.loads(row[0]) for row in self.db.execute("SELECT payload FROM hints ORDER BY at DESC")]

    def import_legacy(self, path: Path, account_key: str, sanitize=None):
        if not path.is_file() or self.metadata("legacy-import", 3600):
            return
        try:
            index = json.loads(path.read_text(encoding="utf-8"))
            canonical = json.dumps(index["orders"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if (index.get("schema_version") != 1 or index.get("includes_archive") is not False
                    or index.get("account_key") != account_key
                    or hashlib.sha256(canonical.encode()).hexdigest() != index.get("orders_sha256")):
                return
            for order in index["orders"]:
                safe = sanitize(order, order.get("status_name", "")) if sanitize else order
                self.remember(safe, [], commit=False)
            self.db.commit()
            age = time.time() - datetime.fromisoformat(index["created_at"]).timestamp()
            if 0 <= age <= 3600:
                self.save_metadata("statuses", [{"id": s["status_id"], "name": s["name"]} for s in index["statuses"]])
            self.save_metadata("legacy-import", True)
        except (ValueError, KeyError, TypeError):
            return


class FirstCandidateSearch:
    def __init__(self, call, cache: FastCache, *, matches, sanitize, qualifying,
                 config: dict, model: str = "", ean: str = "", skus=(), order_ids=(),
                 return_number: str = "", return_id: int | None = None, tracking_number: str = "",
                 external_order_id: str = "", excluded_order_ids=(), deep: bool = False, on_candidate=None,
                 condition_note: str | None = None, preview_only: bool = False, started_at=None):
        self.call, self.cache, self.matches, self.sanitize = call, cache, matches, sanitize
        self.qualifying, self.config = qualifying, config
        self.model, self.ean, self.skus = model, ean, set(skus)
        self.order_ids, self.return_number, self.return_id = list(order_ids), return_number, return_id
        self.tracking, self.external = tracking_number, external_order_id
        self.excluded, self.deep, self.on_candidate = set(excluded_order_ids), deep, on_candidate
        self.condition_note = condition_note
        self.preview_only, self.enrichment_complete = preview_only, False
        self.started, self.calls, self.orders_seen = started_at if started_at is not None else time.monotonic(), 0, 0
        self.counter_lock = threading.Lock()
        stored_statuses = cache.metadata("statuses", 3600) or []
        self.definitions = cache.metadata("order-fields", 86400) or {}
        self.return_definitions = cache.metadata("return-fields", 86400) or {}
        self.status_names = {int(s["id"]): s["name"] for s in stored_statuses}
        self.fresh, self.packages, self.visited, self.scope_steps = {}, {}, set(), []
        self.cache_used, self.first_at, self.first_calls = False, None, None
        self.requested_missing, self.exceptions = [], []
        self.catalog, self.catalog_checked = {}, False

    def read(self, method: str, params: dict, key: str):
        with self.counter_lock:
            self.calls += 1
        response = self.call(method, params)
        value = response.get(key)
        if not isinstance(value, dict if key == "products" else list):
            raise RuntimeError(f"Niepełny odczyt {method}; brak wiarygodnego wyniku.")
        return value

    def statuses(self):
        if not self.status_names:
            data = self.cache.metadata("statuses", 3600)
            if data is None:
                data = self.read("getOrderStatusList", {}, "statuses")
                self.cache.save_metadata("statuses", data)
            self.status_names = {int(s["id"]): s["name"] for s in data}
        return self.status_names

    def fields(self, *, returns=False):
        key = "return-fields" if returns else "order-fields"
        existing = self.cache.metadata(key, 86400)
        if existing is None:
            method = "getOrderReturnExtraFields" if returns else "getOrderExtraFields"
            self.calls += 1
            try:
                existing = field_definitions(self.call(method, {}))
                self.cache.save_metadata(key, existing)
            except RuntimeError:
                self.exceptions.append(f"{key}_metadata_unavailable")
                existing = {}
        if returns:
            self.return_definitions = existing
        else:
            self.definitions = existing

    def order(self, order_id: int) -> dict | None:
        if order_id in self.excluded:
            return None
        if order_id not in self.fresh:
            orders = self.read("getOrders", {"order_id": order_id, "get_unconfirmed_orders": True,
                                             "include_custom_extra_fields": True}, "orders")
            self.fresh[order_id] = next((o for o in orders if int(o["order_id"]) == order_id), None)
        return self.fresh[order_id]

    def product_matches(self, product: dict) -> list[str]:
        return self.matches(product, self.skus)

    def announce(self, row: dict, order: dict):
        if self.first_at is not None:
            return
        self.first_at = time.monotonic() - self.started
        self.first_calls = self.calls
        if self.on_candidate:
            self.on_candidate({"event": "candidate_found", "order_id": row["order_id"],
                               "product": row["product"], "evidence": row["evidence"],
                               "purchase_preview": purchase_context(order), "unit_confirmed": False,
                               "time_to_first_candidate_seconds": round(self.first_at, 3), "api_calls": self.calls})

    def native_preview(self, record: dict) -> dict | None:
        oid = int(record.get("order_id") or 0)
        if not oid or oid in self.excluded or self.order_ids and oid not in self.order_ids:
            return None
        if self.external:
            # A sale's external ID must be checked on the original order, not on the return.
            return None
        if self.return_id is not None and int(record["return_id"]) != self.return_id:
            return None
        if self.return_number and not match_reference(record, self.return_definitions, self.return_number, "return", native_return=True):
            return None
        if self.tracking and not match_reference(record, self.return_definitions, self.tracking, "tracking", native_return=True):
            return None
        matches = [(p, self.product_matches(p)) for p in record.get("products", [])]
        if self.model or self.ean or self.skus:
            matches = [(p, reasons) for p, reasons in matches if reasons]
        elif len(matches) == 1:
            matches = [(matches[0][0], ["PRODUCT_REQUIRES_PHOTO_CHECK"])]
        if len(matches) != 1:
            return None
        selected, reasons = matches[0]
        # Return-manager IDs/quantities/prices are not substituted for original order facts.
        product = {k: selected.get(k) for k in ["order_product_id", "product_id", "sku", "ean", "name"]}
        original = {"order_id": oid, "products": [product]}
        safe = self.sanitize(original, "Powiązanie z RMA; karta zamówienia wymaga odczytu")
        row = {**{k: v for k, v in safe.items() if k != "products"}, "product": safe["products"][0],
               "matched_by": reasons, "evidence": "native_return_link_requires_original_order_readback",
               "unit_confirmed": False, "eligible_for_review": True, "return_package_count": None,
               "return_couriers": [], "order_readback_complete": False,
               "native_return": {key: record.get(key) for key in ["return_id", "status_id", "fulfillment_status"]}}
        row["native_return"]["selected_item_quantity"] = selected.get("quantity")
        row["verdict"] = sheet_verdict(original, product, [], original_ean=self.ean, condition_note=self.condition_note)
        row["verdict"]["quantity_source"] = "not_read_from_original_order_or_physical_receipt"
        row["verdict"]["pending"].append("original_order_and_financial_documents_readback")
        self.announce(row, original)
        return row

    def resolve_catalog(self):
        if self.catalog_checked:
            return
        self.catalog_checked = True
        queries = []
        if self.ean: queries.append({"filter_ean": self.ean})
        if self.model: queries.append({"filter_name": self.model.split("/")[0].strip()})
        for sku in self.skus: queries.append({"filter_sku": sku})
        key = "catalog:" + hashlib.sha256(json.dumps(queries, sort_keys=True).encode()).hexdigest()
        cached = self.cache.metadata(key, 3600)
        if cached is not None:
            self.cache_used = True
            self.catalog = cached
        else:
            self.scope_steps.append("targeted_catalog_fallback")
            for query in queries:
                page = 1
                while True:
                    products = self.read("getInventoryProductsList", {"inventory_id": self.config["base_inventory_id"],
                                         "include_variants": True, "page": page, **query}, "products")
                    for pid, product in products.items():
                        if self.product_matches(product):
                            self.catalog[str(pid)] = {k: product.get(k) for k in ["id", "sku", "ean", "name"]}
                    if len(products) < 1000: break
                    page += 1
            self.cache.save_metadata(key, self.catalog)
        self.skus.update(p["sku"] for p in self.catalog.values() if p.get("sku"))

    def candidate(self, order: dict | None, *, evidence: str = "", returned: dict | None = None,
                  explicitly_selected=False) -> dict | None:
        if order is None or int(order["order_id"]) in self.excluded:
            return None
        if self.external and str(order.get("external_order_id") or "").strip() != self.external.strip():
            self.exceptions.append("provided_external_order_id_not_linked_to_candidate")
            return None
        if self.order_ids and int(order["order_id"]) not in self.order_ids:
            self.exceptions.append("provided_order_and_parcel_reference_conflict")
            return None
        if self.return_id is not None and (returned is None or int(returned["return_id"]) != self.return_id):
            self.exceptions.append("provided_internal_return_id_requires_matching_native_record")
            return None
        products = order.get("products") or []
        if returned is not None:
            linked = {str(p["order_product_id"]) for p in returned.get("products", []) if p.get("order_product_id")}
            if linked:
                products = [p for p in products if str(p.get("order_product_id")) in linked]
            else:
                return_skus = {p.get("sku") for p in returned.get("products", []) if p.get("sku")}
                products = [p for p in products if p.get("sku") in return_skus]
                if len(products) != 1:
                    self.exceptions.append("return_item_binding_requires_review")
                    return None
        matches = [(p, self.product_matches(p)) for p in products]
        if self.model or self.ean or self.skus:
            matches = [(p, reasons) for p, reasons in matches if reasons]
        elif len(matches) == 1 and (evidence or explicitly_selected):
            matches = [(matches[0][0], ["PRODUCT_REQUIRES_PHOTO_CHECK"])]
        else:
            return None
        if not matches:
            if evidence or explicitly_selected:
                self.resolve_catalog()
                matches = [(p, self.product_matches(p)) for p in products]
                matches = [(p, reasons) for p, reasons in matches if reasons]
            if not matches:
                return None
        if not evidence and (self.return_number or self.tracking or self.return_id is not None):
            # A known parcel identifier cannot silently fall back to another unit of the same model.
            return None
        if self.tracking:
            tracking_matches = match_reference(order, self.definitions, self.tracking, "tracking")
            if returned is not None:
                tracking_matches = tracking_matches or match_reference(returned, self.return_definitions, self.tracking, "tracking", native_return=True)
            if not tracking_matches:
                packages = self.packages.get(int(order["order_id"]))
                if packages is None:
                    packages = self.read("getOrderPackages", {"order_id": order["order_id"]}, "packages")
                    self.packages[int(order["order_id"])] = packages
                tracking_matches = any(reference(p.get(k)) == reference(self.tracking) for p in packages
                                       for k in ["courier_package_nr", "courier_inner_number"] if p.get(k))
            if not tracking_matches:
                self.exceptions.append("provided_tracking_number_not_linked_to_candidate")
                return None
        status_name = self.status_names.get(int(order.get("order_status_id") or 0), "")
        if not evidence and not explicitly_selected:
            status_name = self.statuses().get(int(order.get("order_status_id") or 0), "")
            if not self.qualifying(status_name):
                packages = self.read("getOrderPackages", {"order_id": order["order_id"]}, "packages")
                self.packages[int(order["order_id"])] = packages
                if not any(p.get("is_return") is True or str(p.get("is_return")) == "1" for p in packages):
                    return None
                evidence = "verified_return_package"
        status_name = status_name or f"ID {order.get('order_status_id')} — nazwa do odczytu"
        safe = self.sanitize(order, status_name)
        refs = extract_references(order, self.definitions)
        token, kind = (self.return_number or str(self.return_id or ""), "return") if self.return_number or self.return_id is not None else (self.tracking, "tracking")
        source = match_reference(order, self.definitions, token, kind) if token else None
        if source: refs.append({"kind": kind, "value": token, "source": source})
        self.cache.remember(safe, refs)
        product, reasons = matches[0]
        row = {**{k: v for k, v in safe.items() if k != "products"},
               "product": next(p for p in safe["products"] if p.get("order_product_id") == product.get("order_product_id")
                               and p.get("sku") == product.get("sku")),
               "matched_by": reasons, "evidence": evidence or ("human_selected_order" if explicitly_selected else "matching_product_and_qualifying_status"),
               "unit_confirmed": False, "eligible_for_review": True}
        if returned is not None:
            row["native_return"] = {key: returned.get(key) for key in ["return_id", "status_id", "fulfillment_status"]}
            returned_items = [p for p in returned.get("products", [])
                              if str(p.get("order_product_id")) == str(product.get("order_product_id"))]
            row["native_return"]["selected_item_quantity"] = returned_items[0].get("quantity") if len(returned_items) == 1 else None
        row["order_readback_complete"] = True
        self.announce(row, order)
        row["return_package_count"], row["return_couriers"] = None, []
        row["verdict"] = sheet_verdict(order, row["product"], [], original_ean=self.ean,
                                        condition_note=self.condition_note)
        row["verdict"]["pending"].append("invoices_and_return_packages_not_read")
        if self.preview_only:
            return row
        # Only the selected candidate is enriched. No catalogue-wide scan or global ranking.
        try:
            row["status_name"] = self.statuses().get(int(order.get("order_status_id") or 0), status_name)
        except RuntimeError:
            self.exceptions.append("status_name_not_refreshed")
        packages = self.packages.get(int(order["order_id"]))
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                package_job = pool.submit(self.read, "getOrderPackages", {"order_id": order["order_id"]}, "packages") if packages is None else None
                invoice_job = pool.submit(self.read, "getInvoices", {"order_id": order["order_id"]}, "invoices")
                if package_job: packages = package_job.result()
                invoices = invoice_job.result()
        except RuntimeError:
            self.exceptions.append("candidate_enrichment_failed_requires_readback")
            return row
        returns = [p for p in packages if p.get("is_return") is True or str(p.get("is_return")) == "1"]
        row["return_package_count"] = len(returns)
        row["return_couriers"] = sorted({str(p.get("courier_code") or "") for p in returns})
        package_refs = [{"kind": "tracking", "value": str(p[key]), "source": f"packages.{key}"}
                        for p in packages for key in ["courier_package_nr", "courier_inner_number"] if p.get(key)]
        self.cache.remember(safe, refs + package_refs)
        row["verdict"] = sheet_verdict(order, row["product"], invoices, original_ean=self.ean,
                                        condition_note=self.condition_note)
        self.enrichment_complete = True
        return row

    def live_reference(self, order: dict | None) -> str | None:
        if order is None:
            return None
        token, kind = (self.return_number or str(self.return_id or ""), "return") if self.return_number or self.return_id is not None else (self.tracking, "tracking")
        return match_reference(order, self.definitions, token, kind) if token else None

    def native_return(self, record: dict) -> dict | None:
        oid = int(record.get("order_id") or 0)
        if not oid or oid in self.excluded:
            return None
        if record.get("custom_extra_fields") and (
                self.return_number and not match_reference(record, self.return_definitions, self.return_number, "return", native_return=True)
                or self.tracking and not match_reference(record, self.return_definitions, self.tracking, "tracking", native_return=True)):
            self.fields(returns=True)
        self.cache.save_refs(oid, extract_references(record, self.return_definitions, native_return=True),
                             return_id=int(record["return_id"]))
        preview = self.native_preview(record)
        if preview and self.preview_only:
            return preview
        order = self.order(oid)
        if self.return_number and not match_reference(record, self.return_definitions, self.return_number, "return", native_return=True):
            self.exceptions.append("provided_return_id_and_number_conflict")
            return None
        if order is None:
            self.requested_missing.append(oid)
            if preview:
                self.exceptions.append("original_order_requires_panel_or_archive_readback")
                return preview
        return self.candidate(order, evidence=f"native_return:{record['return_id']}", returned=record)

    def pages(self, method: str, base: dict, key: str, id_key: str):
        cursor = 0
        while True:
            params = {**base, **({"id_from": cursor} if cursor else {})}
            batch = self.read(method, params, key)
            ids = [int(item[id_key]) for item in batch]
            if ids and (min(ids) < cursor or ids != sorted(ids) or len(set(ids)) != len(ids)):
                raise RuntimeError("Nieprawidłowa paginacja; nie oznaczaj zakresu jako kompletny.")
            yield batch
            if len(batch) < 100:
                return
            cursor = max(ids) + 1

    def run(self) -> dict:
        row = None
        strong = bool(self.return_number or self.tracking or self.return_id is not None)
        token, kind = (self.return_number or str(self.return_id or ""), "return") if self.return_number or self.return_id is not None else (self.tracking, "tracking")
        if token:
            self.scope_steps.append("exact_reference_cache")
            for hint in self.cache.reference_hints(kind, token):
                self.cache_used = True
                if hint["return_id"]:
                    if hint["source"].startswith("custom_extra_fields."):
                        self.fields(returns=True)
                    batch = self.read("getOrderReturns", {"return_id": hint["return_id"],
                                                          "include_custom_extra_fields": True}, "returns")
                    for record in batch:
                        if match_reference(record, self.return_definitions, token, kind, native_return=True):
                            row = self.native_return(record)
                            if row: break
                    if row: return self.result(row)
                    continue
                order = self.order(int(hint["order_id"]))
                source = self.live_reference(order)
                if not source and hint["source"].startswith("custom_extra_fields."):
                    self.fields()
                    source = self.live_reference(order)
                if source:
                    row = self.candidate(order, evidence=f"{kind}:{source}")
                elif kind == "tracking" and order:
                    packages = self.read("getOrderPackages", {"order_id": order["order_id"]}, "packages")
                    self.packages[int(order["order_id"])] = packages
                    if any(reference(p.get(k)) == reference(token) for p in packages
                           for k in ["courier_package_nr", "courier_inner_number"] if p.get(k)):
                        row = self.candidate(order, evidence="exact_cached_package_refreshed")
                if row: return self.result(row)
        if self.return_id is not None:
            self.scope_steps.append("native_return_id")
            for record in self.read("getOrderReturns", {"return_id": self.return_id,
                                                        "include_custom_extra_fields": True}, "returns"):
                if int(record["return_id"]) == self.return_id:
                    row = self.native_return(record)
                    if row: return self.result(row)
            return self.result(None)
        for oid in self.order_ids:
            self.scope_steps.append("specified_order_id")
            order = self.order(oid)
            if order is None: self.requested_missing.append(oid)
            source = self.live_reference(order) if strong else None
            row = self.candidate(order, evidence=source or "", explicitly_selected=True)
            if row: return self.result(row)
        if self.order_ids:
            return self.result(None)
        if self.external:
            self.scope_steps.append("external_order_id")
            for order in self.read("getOrders", {"filter_external_order_id": self.external,
                                                 "include_custom_extra_fields": True, "get_unconfirmed_orders": True}, "orders"):
                source = self.live_reference(order) if strong else None
                row = self.candidate(order, evidence=source or "", explicitly_selected=True)
                if row: return self.result(row)
            return self.result(None)
        if strong:
            self.scope_steps.append("return_manager_reference")
            for batch in self.pages("getOrderReturns", {"include_custom_extra_fields": True}, "returns", "return_id"):
                if any(match_reference(r, self.return_definitions, token, kind, native_return=True) for r in batch):
                    for record in batch:
                        if match_reference(record, self.return_definitions, token, kind, native_return=True):
                            row = self.native_return(record)
                            if row: return self.result(row)
                if not self.return_definitions and any(r.get("custom_extra_fields") for r in batch):
                    self.fields(returns=True)
                for record in batch:
                    if record.get("order_id"):
                        self.cache.save_refs(int(record["order_id"]),
                            extract_references(record, self.return_definitions, native_return=True),
                            return_id=int(record["return_id"]), commit=False)
                self.cache.db.commit()
                for record in batch:
                    if match_reference(record, self.return_definitions, token, kind, native_return=True):
                        row = self.native_return(record)
                        if row: return self.result(row)
            self.fields()
        self.scope_steps.append("cached_product_or_reference")
        # An absent reference index is not a reason for hundreds of per-order API calls.
        hints = sorted(self.cache.orders(), key=lambda o: o.get("date_in_status") or 0, reverse=True) if not strong else []
        for hint in hints:
            if int(hint["order_id"]) in self.excluded: continue
            if not strong and not any(self.product_matches(p) for p in hint.get("products", [])): continue
            order = self.order(int(hint["order_id"]))
            source = self.live_reference(order) if strong else None
            if strong and not source: continue
            self.cache_used = True
            row = self.candidate(order, evidence=source or "")
            if row: return self.result(row)
        self.scope_steps.append("status_pages_until_first_match")
        names = self.statuses()
        statuses = [(oid, name) for oid, name in names.items() if self.qualifying(name)]
        statuses.sort(key=lambda s: (0 if any(w in fold(s[1]) for w in ["dotarl", "wrocil", "wrocily", "received", "zwr"])
                                    else 1 if "zwrot" in fold(s[1]) else 2, s[0]))
        if self.deep and strong:
            self.scope_steps.append("deep_all_current_orders_reference")
            scopes = [{}]
        else:
            scopes = [{"status_id": oid} for oid, _ in statuses]
        for scope in scopes:
            for batch in self.pages("getOrders", {**scope, "get_unconfirmed_orders": True,
                                                   "include_custom_extra_fields": True}, "orders", "order_id"):
                self.orders_seen += len(batch)
                for order in batch:
                    self.fresh[int(order["order_id"])] = order
                ordered = sorted(batch, key=lambda o: o.get("date_in_status") or 0, reverse=True)
                for order in ordered:
                    source = self.live_reference(order) if strong else None
                    if strong and not source: continue
                    row = self.candidate(order, evidence=f"{kind}:{source}" if source else "")
                    if row: break
                self.cache.remember_batch([(self.sanitize(o, names.get(int(o.get("order_status_id") or 0), "")),
                                           extract_references(o, self.definitions)) for o in batch])
                if row: return self.result(row)
        if not strong:
            self.resolve_catalog()
            for hint in sorted(self.cache.orders(), key=lambda o: o.get("date_in_status") or 0, reverse=True):
                if any(self.product_matches(p) for p in hint.get("products", [])):
                    row = self.candidate(self.order(int(hint["order_id"])))
                    if row: return self.result(row)
        return self.result(None)

    def result(self, row: dict | None) -> dict:
        return {
            "created_at": datetime.now(UTC).isoformat(), "model": self.model, "original_ean": self.ean,
            "catalog": list(self.catalog.values()), "candidates": [row] if row else [],
            "best_candidate": row["order_id"] if row else None, "best_candidate_basis": "first_fresh_plausible_candidate",
            "unit_identity_confirmed": False, "intake_authorized": False,
            "scope": {"mode": "first_candidate", "includes_archive": False, "cache_used": self.cache_used,
                      "stopped_after_first": bool(row), "global_ranking_complete": False,
                      "orders_indexed": self.orders_seen, "status_count": len(self.status_names),
                      "api_calls": self.calls, "api_calls_to_first_candidate": self.first_calls,
                      "candidate_enrichment_complete": self.enrichment_complete,
                      "time_to_first_candidate_seconds": round(self.first_at, 3) if self.first_at is not None else None,
                      "elapsed_seconds": round(time.monotonic() - self.started, 3), "steps": self.scope_steps,
                      "specified_order_ids": self.order_ids, "requested_ids_not_in_current_api": self.requested_missing,
                      "requested_ids_without_product_match": [i for i in self.order_ids if i not in self.requested_missing and (not row or row['order_id'] != i)],
                      "exceptions": self.exceptions,
                      "next_lookup": None if row else "Base exact Notes/return/tracking filter, then archive; use --deep only when needed"},
        }
