"""Small Base API reader; production writes are deliberately unavailable."""
from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

READ_METHODS = frozenset({
    "getOrderStatusList", "getOrders", "getOrderPackages", "getOrderReturns",
    "getOrderSources", "getInvoices", "getJournalList", "getInventories",
    "getInventoryWarehouses", "getInventoryProductsList", "getInventoryProductsData",
    "getInventoryProductsStock", "getInventoryDocuments", "getInventoryDocumentItems",
    "getInventoryPurchaseOrders", "getInventoryPurchaseOrderItems",
})


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Brak konfiguracji {name}; ustaw ją lokalnie bez ujawniania sekretu.")
    return value


@dataclass(frozen=True)
class BaseLinkerConfig:
    token: str = field(repr=False)
    inventory_id: int = 17463


class BaseLinkerClient:
    endpoint = "https://api.baselinker.com/connector.php"

    def __init__(self, config: BaseLinkerConfig, *, transport: str | None = None):
        self.config = config
        self.transport = transport or ("curl" if os.name == "nt" else "urllib")
        if self.transport not in {"curl", "urllib"}:
            raise ValueError("Nieobsługiwany transport HTTP.")

    @staticmethod
    def _escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "").replace("\n", "")

    def _post(self, body: bytes) -> bytes:
        if self.transport == "curl":
            # curl receives the token through stdin, never through argv or a file.
            lines = ["silent", "show-error", "ssl-revoke-best-effort", 'request = "POST"',
                     f'url = "{self.endpoint}"',
                     f'header = "X-BLToken: {self._escape(self.config.token)}"',
                     'header = "Content-Type: application/x-www-form-urlencoded"',
                     f'data-binary = "{self._escape(body.decode("ascii"))}"', ""]
            result = subprocess.run(["curl.exe", "--disable", "--config", "-"],
                                    input="\n".join(lines).encode(), capture_output=True,
                                    timeout=45, check=False)
            if result.returncode:
                raise OSError(f"Transport curl zakończył się kodem {result.returncode}.")
            return result.stdout
        request = Request(self.endpoint, data=body, method="POST", headers={
            "X-BLToken": self.config.token, "Content-Type": "application/x-www-form-urlencoded",
        })
        with urlopen(request, timeout=45) as response:
            return response.read()

    def call(self, method: str, parameters: dict, *, retries: int = 3) -> dict:
        if method not in READ_METHODS:
            raise ValueError("Adapter silnika dopuszcza wyłącznie wymienione metody odczytu Base.")
        if not 1 <= retries <= 3:
            raise ValueError("Odczyt dopuszcza od 1 do 3 prób.")
        body = urlencode({"method": method, "parameters": json.dumps(
            parameters, ensure_ascii=False, separators=(",", ":"),
        )}).encode()
        error_code = "TRANSPORT_OR_INVALID_RESPONSE"
        for attempt in range(retries):
            try:
                result = json.loads(self._post(body))
                if not isinstance(result, dict):
                    raise ValueError("Invalid response")
                if result.get("status") == "SUCCESS":
                    return result
                error_code = str(result.get("error_code") or "UNKNOWN")
                if error_code not in {"ERROR_RATE_LIMIT", "ERROR_TEMPORARY"}:
                    break
            except (OSError, TimeoutError, URLError, ValueError):
                error_code = "TRANSPORT_OR_INVALID_RESPONSE"
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
        # Server messages can contain private values. Report only a bounded code.
        safe_code = "".join(c for c in error_code if c.isalnum() or c == "_")[:80]
        raise RuntimeError(f"Base {method}: {safe_code}; odczyt nie został potwierdzony.")
