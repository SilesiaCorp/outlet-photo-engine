"""Read-only Base outlet discovery; private local cache, never an intake approval."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from outlet_engine.api import BaseLinkerClient  # noqa: E402
from outlet_engine.api import BaseLinkerConfig, require_env  # noqa: E402
from outlet_engine.verdict import markdown_verdict, sheet_verdict  # noqa: E402
from outlet_engine.fast_search import FastCache, FirstCandidateSearch  # noqa: E402
from outlet_engine.rate_limit import RequestBudget  # noqa: E402

READ_METHODS = {"getInventoryProductsList", "getOrderStatusList", "getOrders", "getOrderPackages", "getInvoices",
                "getOrderReturns", "getOrderExtraFields", "getOrderReturnExtraFields"}
ORDER_FIELDS = (
    "order_id", "order_source", "order_source_id", "order_status_id", "date_add",
    "date_in_status", "confirmed", "currency", "delivery_package_module",
)
PRODUCT_FIELDS = (
    "order_product_id", "storage_id", "product_id", "sku", "ean", "name",
    "quantity", "price_brutto", "tax_rate", "warehouse_id",
)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def model_matches(model: str, name: str) -> bool:
    parts = re.findall(r"[a-z]+|[0-9]+", model.casefold())
    if not parts:
        return False
    pattern = r"(?<![a-z0-9])" + r"[\s./_-]*".join(map(re.escape, parts)) + r"(?![a-z0-9])"
    return bool(re.search(pattern, name.casefold()))


def matching_reasons(product: dict, *, model: str, ean: str, skus: set[str]) -> list[str]:
    # A known conflicting suffix is not repaired by an accidental SKU/EAN match.
    if "/" in model:
        family, suffix = model.rsplit("/", 1)
        family_parts = re.findall(r"[a-z]+|[0-9]+", family, re.I)
        family_pattern = r"[\s./_-]*".join(map(re.escape, family_parts))
        other = re.search(r"(?<![a-z0-9])" + family_pattern + r"\s*/\s*([a-z0-9]+)",
                          str(product.get("name") or ""), re.I)
        if other and other[1].casefold() != suffix.strip().casefold():
            return []
    reasons = []
    if ean and str(product.get("ean") or "").strip() == ean:
        reasons.append("EAN")
    if str(product.get("sku") or "").strip() in skus:
        reasons.append("SKU")
    if model_matches(model, str(product.get("name") or "")):
        reasons.append("MODEL")
    return reasons


def qualifying_status(name: str, fragments: list[str]) -> bool:
    return any(fragment in name.casefold() for fragment in fragments)


def sanitize_order(order: dict, status_name: str) -> dict:
    return {
        **{key: order.get(key) for key in ORDER_FIELDS},
        "status_name": status_name,
        "products": [{key: p.get(key) for key in PRODUCT_FIELDS} for p in order.get("products", [])],
    }


def paged_orders(call, status: dict) -> list[dict]:
    found: dict[int, dict] = {}
    cursor = 0
    while True:
        params = {"status_id": int(status["id"]), "get_unconfirmed_orders": True}
        if cursor:
            params["id_from"] = cursor
        batch = call("getOrders", params).get("orders")
        if not isinstance(batch, list):
            raise RuntimeError("Niepełna odpowiedź getOrders; brak wiarygodnego readbacku indeksu.")
        if not batch:
            break
        ids = [int(o["order_id"]) for o in batch]
        if min(ids) < cursor or len(set(ids)) != len(ids) or ids != sorted(ids):
            raise RuntimeError("Nieprawidłowa paginacja Base; indeks nie został uznany za kompletny.")
        for order in batch:
            found[int(order["order_id"])] = sanitize_order(order, status["name"])
        cursor = max(ids) + 1
        if len(batch) < 100:
            break
    return list(found.values())


def collect_index(call, statuses: list[dict], fragments: list[str]) -> dict:
    selected = [s for s in statuses if qualifying_status(s["name"], fragments)]
    orders = []
    counts = []
    for status in selected:
        batch = paged_orders(call, status)
        orders.extend(batch)
        counts.append({"status_id": int(status["id"]), "name": status["name"], "orders": len(batch)})
    payload = {
        "schema_version": 1,
        "complete": True,
        "includes_archive": False,
        "created_at": datetime.now(UTC).isoformat(),
        "status_scope": fragments,
        "statuses": counts,
        "orders": orders,
    }
    payload["orders_sha256"] = hashlib.sha256(canonical(orders).encode("utf-8")).hexdigest()
    return payload


def load_fresh_index(path: Path, max_age: int, fragments: list[str], account_key: str) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        age = (datetime.now(UTC) - datetime.fromisoformat(data["created_at"])).total_seconds()
        digest = hashlib.sha256(canonical(data["orders"]).encode("utf-8")).hexdigest()
        valid = (
            data.get("schema_version") == 1 and data.get("complete") is True
            and data.get("includes_archive") is False and 0 <= age <= max_age
            and data.get("status_scope") == fragments and data.get("account_key") == account_key
            and data.get("orders_sha256") == digest
        )
        return data if valid else None
    except (ValueError, KeyError, TypeError):
        return None


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


@contextmanager
def exclusive_cache(path: Path):
    try:
        handle = path.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise RuntimeError("Indeks ma właściciela lub pozostawiony lock. Sprawdź proces przed wznowieniem.") from exc
    try:
        handle.write(canonical({"pid": os.getpid(), "started_at": datetime.now(UTC).isoformat()}))
        handle.flush()
        yield
    finally:
        handle.close()
        path.unlink()


def candidates(index: dict, *, model: str, ean: str, skus: set[str]) -> list[dict]:
    found = []
    for order in index["orders"]:
        for product in order["products"]:
            reasons = matching_reasons(product, model=model, ean=ean, skus=skus)
            if reasons:
                found.append({**{k: v for k, v in order.items() if k != "products"},
                              "product": product, "matched_by": reasons, "unit_confirmed": False})
    return found


def private_root() -> Path:
    local = os.getenv("LOCALAPPDATA") or os.getenv("XDG_DATA_HOME")
    return (Path(local) if local else Path.home() / ".local" / "share") / "Codex" / "marketplace-ops"


def evidence_text(value: str) -> str:
    if value.startswith("return:"):
        return "Numer zwrotu z paczki zgadza się z informacją w zamówieniu."
    if value.startswith("native_return:"):
        return "Rejestr zwrotów Base łączy produkt z zamówieniem."
    return {
        "native_return_link_requires_original_order_readback": "Rejestr zwrotu wskazuje zamówienie; jego karta wymaga odczytu.",
        "matching_product_and_qualifying_status": "Produkt pasuje; status wskazuje zwrot lub anulowanie.",
        "human_selected_order": "Numer BL wskazany przez pracownika; produkt pasuje.",
        "verified_return_package": "Zamówienie ma przesyłkę zwrotną.",
        "exact_cached_package_refreshed": "Numer przesyłki z etykiety pasuje do zamówienia.",
        "tracking:delivery_package_nr": "Numer przesyłki zgadza się z zamówieniem w Base.",
    }.get(value, "Oznaczenie i produkt pasują do danych Base.")


def main() -> int:
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="", help="Pełny model z etykiety, np. MODEL100/01")
    parser.add_argument("--ean", default="", help="Oryginalny EAN jako tekst")
    parser.add_argument("--sku", action="append", default=[], help="Potwierdzone SKU; można powtórzyć")
    parser.add_argument("--order-id", type=int, action="append", default=[],
                        help="Konkretny numer BL wskazany przez pracownika; bez skanowania wszystkich statusów")
    parser.add_argument("--return-number", "--return-code", dest="return_number", default="",
                        help="Pomocniczy numer zwrotu/RMA; nie blokuje trafienia po produkcie")
    parser.add_argument("--return-id", type=int, help="Wewnętrzny ID zwrotu Base; inny niż numer zamówienia")
    parser.add_argument("--tracking-number", default="", help="Pełny numer przesyłki z etykiety, nie telefon automatu")
    parser.add_argument("--external-order-id", default="", help="Numer transakcji/zamówienia marketplace")
    parser.add_argument("--exclude-order-id", type=int, action="append", default=[], help="Pomiń kandydata odrzuconego dla tej sztuki")
    parser.add_argument("--preview-only", action="store_true", help="Natychmiastowy pierwszy kandydat i ceny z zamówienia; faktury/przesyłki w kolejnym kroku")
    parser.add_argument("--stop-after-first", action="store_true", help="Tylko odczyt wybranej pozycji; bez dalszego porównania")
    parser.add_argument("--strict-return-reference", action="store_true", help="Jawne szukanie konkretnego RMA zamiast pomocniczego tropu")
    parser.add_argument("--full-scan", action="store_true", help="Porównaj wszystkich kandydatów po modelu/SKU/EAN; wolniejszy pełny tryb")
    parser.add_argument("--deep", action="store_true", help="Rozszerz dalsze porównanie na wszystkie bieżące statusy")
    parser.add_argument("--condition-note", help="Potwierdzona obserwacja ze zdjęcia lub od pracownika")
    parser.add_argument("--refresh", action="store_true", help="Odśwież aktualne statusy zamiast cache")
    parser.add_argument("--cache-dir", type=Path, default=private_root() / "outlet-discovery")
    parser.add_argument("--format", choices=["json", "jsonl", "markdown"], default="markdown")
    args = parser.parse_args()
    if not any([args.model.strip(), args.ean.strip(), args.sku, args.order_id, args.return_number.strip(),
                args.return_id is not None, args.tracking_number.strip(), args.external_order_id.strip()]):
        parser.error("Podaj odczytany model, EAN/SKU albo konkretne oznaczenie zamówienia/zwrotu/przesyłki.")
    if args.model and not re.findall(r"[a-z0-9]", args.model.casefold()):
        parser.error("Model nie zawiera czytelnego oznaczenia.")
    if any(order_id <= 0 for order_id in args.order_id):
        parser.error("Numer BL musi być dodatni.")
    if args.return_id is not None and args.return_id <= 0:
        parser.error("ID zwrotu Base musi być dodatni.")
    if args.full_scan and any([args.return_number, args.return_id, args.tracking_number, args.external_order_id, args.preview_only, args.deep, args.stop_after_first, args.strict_return_reference]):
        parser.error("Dla konkretnego oznaczenia użyj trybu pierwszego kandydata; --deep rozszerza jego zakres.")
    config = json.loads((ROOT / "configs" / "outlet-intake.json").read_text(encoding="utf-8"))
    token = require_env("BASELINKER_TOKEN")
    # Separate cache namespaces across Base tokens without persisting the token.
    account_key = hashlib.sha256(token.encode("utf-8")).hexdigest()[:24]
    cache_dir = args.cache_dir.resolve() / account_key
    try:
        cache_dir.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise RuntimeError("Cache produkcyjny musi pozostać poza repozytorium.")
    cache_dir.mkdir(parents=True, exist_ok=True)
    budget = RequestBudget(args.cache_dir.resolve() / "api-budget.sqlite3", account_key)
    client = BaseLinkerClient(BaseLinkerConfig(token=token, inventory_id=config["base_inventory_id"]), request_gate=budget.acquire)
    calls = 0
    read_count_lock = threading.Lock()
    last_call = 0.0

    def read(method: str, parameters: dict) -> dict:
        nonlocal calls, last_call
        if method not in READ_METHODS:
            raise ValueError("Niedozwolona metoda w narzędziu read-only.")
        if args.full_scan:
            time.sleep(max(0, .7 - (time.monotonic() - last_call)))
        with read_count_lock:
            calls += 1
        last_call = time.monotonic()
        return client.call(method, parameters)

    fragments = config["search_status_fragments"]
    index_path = cache_dir / "orders-current.json"
    if not args.full_scan:
        with exclusive_cache(cache_dir / "discovery.lock"):
            fast_cache = FastCache(cache_dir / "fast-cache.sqlite3")
            try:
                if args.refresh:
                    fast_cache.db.execute("DELETE FROM metadata")
                    fast_cache.db.commit()
                else:
                    fast_cache.import_legacy(index_path, account_key, sanitize_order)

                def preview(event):
                    event["created_at"] = datetime.now(UTC).isoformat()
                    event["http_attempts"] = getattr(client, "http_attempts", calls)
                    if event["event"] == "candidate_found":
                        atomic_json(cache_dir / "first-candidate.json", event)
                    atomic_json(cache_dir / "shown-candidate.json", event)
                    if args.format == "jsonl":
                        print(json.dumps(event, ensure_ascii=False), flush=True)
                    elif args.format == "markdown":
                        label = "Najlepszy dotąd kandydat" + (" — aktualizacja" if event["event"] == "candidate_updated" else "")
                        print(f"- {label}: **BL {event['order_id']}**, SKU **{event['product'].get('sku') or 'brak'}**.", flush=True)
                        print(f"- Dowód: {evidence_text(event['evidence'])} Sztuka do potwierdzenia.", flush=True)

                engine = FirstCandidateSearch(read, fast_cache,
                    matches=lambda p, skus: matching_reasons(p, model=args.model, ean=args.ean, skus=skus),
                    sanitize=sanitize_order, qualifying=lambda name: qualifying_status(name, fragments),
                    config=config, model=args.model, ean=args.ean, skus=args.sku, order_ids=args.order_id,
                    return_number=args.return_number, return_id=args.return_id, tracking_number=args.tracking_number,
                    external_order_id=args.external_order_id, excluded_order_ids=args.exclude_order_id,
                    deep=args.deep, on_candidate=preview, preview_only=args.preview_only,
                    condition_note=args.condition_note, started_at=started,
                    strict_return_reference=args.strict_return_reference,
                    continue_search=not args.preview_only and not args.stop_after_first and not args.strict_return_reference and not args.order_id and not args.external_order_id,
                    on_checkpoint=lambda report: atomic_json(cache_dir / "latest-result.json", report))
                result = engine.run()
                result["scope"]["http_attempts"] = getattr(client, "http_attempts", calls)
                atomic_json(cache_dir / "latest-result.json", result)
            finally:
                fast_cache.close()
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.format == "jsonl":
            print(json.dumps({"event": "result", **result}, ensure_ascii=False), flush=True)
        else:
            if result["candidates"]:
                row = result["candidates"][0]
                print(f"- Status: {row['status_name']}.")
                if row.get("order_readback_complete"):
                    print(f"- Ilość: {row['product'].get('quantity')} wg zamówienia; fizyczna do potwierdzenia.")
                elif row.get("native_return"):
                    print(f"- Ilość w rejestrze zwrotu: {row['native_return'].get('selected_item_quantity')}; fizyczna do potwierdzenia.")
                print(markdown_verdict(row["verdict"]))
                if not result["scope"]["candidate_enrichment_complete"]:
                    print("- Wstępny kandydat: faktury/przesyłki i pełna kwalifikacja wymagają dalszego odczytu.")
            else:
                print("- Najlepszy kandydat dotąd: **brak w sprawdzonym zakresie**. Następny krok: inne tropy produktu i archiwum.")
            if result["scope"].get("current_api_comparison_complete"):
                print(f"- Kandydaci w sprawdzonym zakresie API: {len(result['candidates'])}. Archiwum wymaga dalszego sprawdzenia w panelu Base.")
            else:
                print("- Wynik wstępny. Dalsze porównanie Base i archiwum pozostaje do wykonania.")
            timing = result['scope']['time_to_first_candidate_seconds']
            print(f"- API: {calls} żądań" + (f"; pierwsza propozycja po {timing} s." if timing is not None else "."))
        return 0
    with exclusive_cache(cache_dir / "discovery.lock"):
        specified_orders = {}
        if args.order_id:
            statuses = read("getOrderStatusList", {})["statuses"]
            names = {int(s["id"]): s["name"] for s in statuses}
            for order_id in dict.fromkeys(args.order_id):
                response = read("getOrders", {"order_id": order_id, "get_unconfirmed_orders": True,
                                              "include_custom_extra_fields": True})
                if not isinstance(response.get("orders"), list):
                    raise RuntimeError("Niepełny odczyt wskazanego zamówienia.")
                if response["orders"]:
                    specified_orders[order_id] = response["orders"][0]
            index = {"created_at": datetime.now(UTC).isoformat(),
                     "statuses": [{"status_id": key, "name": value} for key, value in names.items()],
                     "orders": [sanitize_order(o, names.get(int(o.get("order_status_id") or 0), ""))
                                for o in specified_orders.values()]}
            cache_used = False
        else:
            index = None if args.refresh else load_fresh_index(
                index_path, config["search_cache_max_age_seconds"], fragments, account_key,
            )
            cache_used = index is not None
            if index is None:
                statuses = read("getOrderStatusList", {})["statuses"]
                index = collect_index(read, statuses, fragments)
                index["account_key"] = account_key
                atomic_json(index_path, index)

        catalog: dict[str, dict] = {}
        queries = [{"filter_name": args.model.split("/")[0].strip()}] if args.model else []
        if args.ean:
            queries.insert(0, {"filter_ean": args.ean})
        for sku in args.sku:
            queries.append({"filter_sku": sku})
        for query in queries:
            page = 1
            while True:
                products = read("getInventoryProductsList", {
                    "inventory_id": config["base_inventory_id"], "include_variants": True,
                    "page": page, **query,
                }).get("products")
                if not isinstance(products, dict):
                    raise RuntimeError("Niepełny odczyt katalogu; nie można uznać go za zero wyników.")
                for pid, product in products.items():
                    if matching_reasons(product, model=args.model, ean=args.ean, skus=set(args.sku)):
                        catalog[str(pid)] = {k: product.get(k) for k in ["id", "sku", "ean", "name"]}
                if len(products) < 1000:
                    break
                page += 1
        skus = set(args.sku) | {p["sku"] for p in catalog.values() if p.get("sku")}
        found = candidates(index, model=args.model, ean=args.ean, skus=skus)
        # Refresh just the candidate orders; cached statuses are search hints, not proof.
        confirmed = []
        for order_id in sorted({c["order_id"] for c in found}):
            if order_id in args.exclude_order_id:
                continue
            orders = [specified_orders[order_id]] if order_id in specified_orders else read("getOrders", {
                "order_id": order_id, "get_unconfirmed_orders": True,
                "include_custom_extra_fields": True}).get("orders")
            if not isinstance(orders, list):
                raise RuntimeError("Niepełny odczyt kandydata; wynik nie jest potwierdzony.")
            if not orders:
                continue
            status_id = orders[0].get("order_status_id")
            status_name = next((s["name"] for s in index["statuses"] if s["status_id"] == status_id), "")
            if not args.order_id and not qualifying_status(status_name, fragments):
                continue
            fresh = candidates({"orders": [sanitize_order(orders[0], status_name)]},
                               model=args.model, ean=args.ean, skus=skus)
            packages = read("getOrderPackages", {"order_id": order_id}).get("packages", [])
            invoices = read("getInvoices", {"order_id": order_id}).get("invoices", [])
            returns = [p for p in packages if p.get("is_return") is True or str(p.get("is_return")) == "1"]
            for row in fresh:
                row["return_package_count"] = len(returns)
                row["return_couriers"] = sorted({str(p.get("courier_code") or "") for p in returns})
                row["verdict"] = sheet_verdict(orders[0], row["product"], invoices,
                                               original_ean=args.ean, condition_note=args.condition_note)
                confirmed.append(row)
        confirmed.sort(key=lambda c: (bool(c["return_package_count"]), c.get("date_in_status") or 0), reverse=True)
        result = {
            "created_at": datetime.now(UTC).isoformat(), "model": args.model, "original_ean": args.ean,
            "catalog": list(catalog.values()), "candidates": confirmed,
            "best_candidate": confirmed[0]["order_id"] if confirmed else None,
            "best_candidate_basis": "verified_return_package_then_status_date",
            "unit_identity_confirmed": False, "intake_authorized": False,
            "scope": {"includes_archive": False, "index_created_at": index["created_at"],
                      "cache_used": cache_used, "orders_indexed": len(index["orders"]),
                      "status_count": len(index["statuses"]), "api_calls": calls,
                      "specified_order_ids": list(dict.fromkeys(args.order_id)),
                      "requested_ids_not_in_current_api": [i for i in args.order_id if i not in specified_orders],
                      "requested_ids_without_product_match": [i for i in specified_orders if i not in {c['order_id'] for c in confirmed}]},
        }
        atomic_json(cache_dir / "latest-result.json", result)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"- Produkt: **{args.model}**, EAN **{args.ean or 'nie odczytano'}**.")
        print(f"- Kartoteki: **{len(catalog)}**; kandydaci w bieżącej bazie: **{len(confirmed)}**.")
        print(f"- Najlepszy kandydat roboczy: **{result['best_candidate'] or 'brak'}**.")
        if confirmed:
            print("\n| BL | SKU | Status | Ilość | Przesyłka zwrotna |")
            print("| --- | --- | --- | --- | --- |")
            for row in confirmed:
                p = row["product"]
                couriers = ", ".join(row["return_couriers"]) or "nie potwierdzono"
                print(f"| {row['order_id']} | {p['sku']} | {row['status_name']} | {p['quantity']} | {couriers} |")
            print()
            print(markdown_verdict(confirmed[0]["verdict"]))
            print()
        print("- Do potwierdzenia: konkretny egzemplarz, fizyczne przyjęcie, stan, własność i wycena.")
        print("- Zakres: bieżąca baza. Archiwum i duplikaty w arkuszu wymagają osobnego sprawdzenia.")
        if args.order_id:
            print("- Wskazane BL sprawdzono bez pełnego skanowania statusów; status nie potwierdza kwalifikacji sztuki.")
            if result["scope"]["requested_ids_not_in_current_api"]:
                print("- Brak wskazanego ID w bieżącym API: sprawdź archiwum, bez przywracania zamówienia.")
            if result["scope"]["requested_ids_without_product_match"]:
                print("- Wskazane zamówienie nie ma pasującej pozycji; powiązanie wymaga wyjaśnienia.")
        print(f"- Odczyt API: {calls} wywołań; raport prywatny: {cache_dir / 'latest-result.json'}.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, OSError) as error:
        print(f"Wyszukiwanie nieukończone: {error}", file=sys.stderr)
        raise SystemExit(1) from error
