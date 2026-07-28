"""GeckoTerminal discovery with local Pancake mapping and bootstrap fallback."""

from __future__ import annotations

import hashlib
import http.client
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ProviderError(RuntimeError):
    def __init__(self, reason: str, status: int | None = None, detail: str | None = None) -> None:
        super().__init__(detail or reason)
        self.reason = reason
        self.status = status
        self.detail = detail


@dataclass(frozen=True)
class DEXMapping:
    provider_id: str
    canonical_name: str
    factory: str
    router: str
    source: str = "provider"


@dataclass(frozen=True)
class PoolCandidate:
    address: str
    network: str
    dex_id: str
    dex_name: str
    base_token: str
    quote_token: str
    provider_rank: int
    volume_24h_usd: float | None
    liquidity_usd: float | None
    transactions_24h: int | None
    observed_at: str
    pair_name: str | None = None
    base_symbol: str | None = None
    quote_symbol: str | None = None
    display_only: bool = True
    ranking_provider: str = "geckoterminal"


ALLOWED_HOSTS = frozenset({"api.geckoterminal.com"})
PANCAKE_FACTORY = "0xca143ce32fe78f1f7019d7d551a6402fc5350c73"
PANCAKE_ROUTER = "0x10ed43c718714eb63d5aa57b78b54704e256024e"
LOCAL_DEX = {
    "pancakeswap_v2": DEXMapping(
        "pancakeswap_v2",
        "PancakeSwap V2",
        PANCAKE_FACTORY,
        PANCAKE_ROUTER,
    )
}


def _number(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def normalize_dex_id(value: str) -> str:
    text = str(value or "").strip().lower()
    if text.startswith("bsc_"):
        return text[4:]
    return text


def _split_endpoint(endpoint: str) -> tuple[str, str, str]:
    scheme, rest = endpoint.split("://", 1) if "://" in endpoint else ("", endpoint)
    authority, _, path = rest.partition("/")
    host = authority.split("@", 1)[-1].split(":", 1)[0]
    base = "/" + path.rstrip("/") if path else ""
    return scheme, host, base


def _token_from_included(included: dict[str, Any], rel_id: str) -> tuple[str, str | None]:
    attrs = included.get(rel_id, {}).get("attributes", {})
    address = str(attrs.get("address") or rel_id.split("_", 1)[-1]).lower()
    symbol = attrs.get("symbol")
    return address, str(symbol) if symbol else None


class GeckoTerminalClient:
    def __init__(
        self,
        *,
        endpoint: str = "https://api.geckoterminal.com/api/v2",
        transport: Callable[[str, str], tuple[int, bytes]] | None = None,
        clock: Callable[[], float] = time.time,
        cache_ttl_seconds: int = 30,
        max_retries: int = 2,
        allow_bootstrap: bool = True,
        prefer_bootstrap: bool = False,
        timeout_seconds: int = 20,
    ) -> None:
        if not 5 <= cache_ttl_seconds <= 60:
            raise ValueError("cache_ttl_seconds must be between 5 and 60")
        _, host, _ = _split_endpoint(endpoint)
        if transport is None and host not in ALLOWED_HOSTS:
            raise ProviderError("source_unavailable", detail="endpoint host not allowlisted")
        self.endpoint = endpoint.rstrip("/")
        self.transport = transport
        self.clock = clock
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_retries = max_retries
        self.allow_bootstrap = allow_bootstrap
        self.prefer_bootstrap = prefer_bootstrap
        self.timeout_seconds = timeout_seconds
        self._cache: dict[tuple[Any, ...], tuple[float, Any]] = {}
        self.last_source = "geckoterminal"

    def _fingerprint(self) -> str:
        raw = (
            f"{self.endpoint}|timeout={self.timeout_seconds}|retry={self.max_retries}"
            f"|limit=1048576|ttl={self.cache_ttl_seconds}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _request_once(self, path: str) -> tuple[int, bytes]:
        if self.transport is not None:
            return self.transport("GET", path)
        scheme, authority_host, base = _split_endpoint(self.endpoint)
        _, rest = self.endpoint.split("://", 1)
        authority = rest.split("/", 1)[0]
        if authority_host not in ALLOWED_HOSTS:
            raise ProviderError("source_unavailable", detail="host not allowlisted")
        connection: http.client.HTTPConnection
        if scheme == "https":
            connection = http.client.HTTPSConnection(authority, timeout=self.timeout_seconds)
        elif scheme == "http":
            connection = http.client.HTTPConnection(authority, timeout=self.timeout_seconds)
        else:
            raise ProviderError("source_unavailable", detail="unsupported scheme")
        try:
            connection.request(
                "GET",
                f"{base}{path}",
                headers={
                    "Accept": "application/json",
                    "User-Agent": "market-intent-inference/0.1 (+paper-research)",
                },
            )
            response = connection.getresponse()
            return response.status, response.read(1_048_577)
        finally:
            connection.close()

    def _request(self, path: str) -> dict[str, Any]:
        last_error: ProviderError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                status, body = self._request_once(path)
            except (TimeoutError, OSError, http.client.HTTPException) as exc:
                last_error = ProviderError(
                    "source_unavailable",
                    detail=f"transport_error:{type(exc).__name__}",
                )
                if attempt >= self.max_retries:
                    raise last_error from exc
                time.sleep(0.2 * (2**attempt))
                continue
            if status == 429:
                last_error = ProviderError("source_unavailable", status, detail="http_429")
                if attempt >= self.max_retries:
                    raise last_error
                time.sleep(0.4 * (2**attempt))
                continue
            if status < 200 or status >= 300:
                raise ProviderError("source_unavailable", status, detail=f"http_{status}")
            if len(body) > 1_048_576:
                raise ProviderError("quality_failed", status, detail="response_too_large")
            try:
                value = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ProviderError("quality_failed", status, detail="malformed_json") from exc
            if not isinstance(value, dict):
                raise ProviderError("quality_failed", status, detail="non_object_json")
            return value
        raise last_error or ProviderError("source_unavailable")

    def dex_mappings(self) -> dict[str, DEXMapping]:
        document = self._request("/networks/bsc/dexes")
        mappings: dict[str, DEXMapping] = {}
        for row in document.get("data", []):
            provider_id = normalize_dex_id(str(row.get("id", "")))
            attrs = row.get("attributes", {})
            if provider_id in LOCAL_DEX:
                local = LOCAL_DEX[provider_id]
                mappings[provider_id] = DEXMapping(
                    local.provider_id,
                    local.canonical_name,
                    local.factory,
                    local.router,
                    "provider_id+configured_v2",
                )
                continue
            factory = str(attrs.get("factory_address", "")).lower()
            router = str(attrs.get("router_address", "")).lower()
            if provider_id and factory and router:
                mappings[provider_id] = DEXMapping(
                    provider_id,
                    str(attrs.get("name", provider_id)),
                    factory,
                    router,
                )
        return mappings

    def require_pancake_mapping(self, dex: str = "pancakeswap_v2") -> DEXMapping:
        dex = normalize_dex_id(dex)
        if self.prefer_bootstrap and self.allow_bootstrap:
            local = LOCAL_DEX.get(dex)
            mapping = (
                DEXMapping(
                    local.provider_id,
                    local.canonical_name,
                    local.factory,
                    local.router,
                    "bootstrap_snapshot",
                )
                if local
                else None
            )
        else:
            mapping = self.dex_mappings().get(dex)
        if mapping is None:
            raise ProviderError("quality_failed", detail="dex_not_mapped")
        if mapping.factory != PANCAKE_FACTORY or mapping.router != PANCAKE_ROUTER:
            raise ProviderError("quality_failed", detail="factory_router_mismatch")
        return mapping

    def _parse_pools(self, document: dict[str, Any], *, dex: str, page: int) -> list[PoolCandidate]:
        if not isinstance(document.get("data"), list) or not isinstance(
            document.get("included", []), list
        ):
            raise ProviderError("quality_failed", detail="malformed_pool_schema")
        mapping = LOCAL_DEX[dex]
        included = {str(item.get("id")): item for item in document.get("included", [])}
        result: list[PoolCandidate] = []
        for index, row in enumerate(document.get("data", []), start=1):
            if not isinstance(row, dict):
                raise ProviderError("quality_failed", detail="malformed_pool_row")
            attrs = row.get("attributes", {})
            if not isinstance(attrs, dict):
                raise ProviderError("quality_failed", detail="malformed_pool_attributes")
            relationships = row.get("relationships", {})
            raw_dex = attrs.get("dex_id") or relationships.get("dex", {}).get("data", {}).get(
                "id", ""
            )
            row_dex = normalize_dex_id(str(raw_dex))
            address = str(attrs.get("address") or str(row.get("id", "")).rsplit("_", 1)[-1]).lower()
            if row_dex != dex or not address.startswith("0x") or len(address) != 42:
                continue
            base_rel = str(relationships.get("base_token", {}).get("data", {}).get("id", ""))
            quote_rel = str(relationships.get("quote_token", {}).get("data", {}).get("id", ""))
            base_token, base_symbol = _token_from_included(included, base_rel)
            quote_token, quote_symbol = _token_from_included(included, quote_rel)
            if not base_token:
                base_token = str(attrs.get("base_token_address", "")).lower()
            if not quote_token:
                quote_token = str(attrs.get("quote_token_address", "")).lower()
            tx_block = attrs.get("transactions", {}).get("h24", {})
            buys = tx_block.get("buys", 0) or 0
            sells = tx_block.get("sells", 0) or 0
            numeric = isinstance(buys, (int, float)) and isinstance(sells, (int, float))
            tx = buys + sells if numeric else None
            result.append(
                PoolCandidate(
                    address=address,
                    network="bsc",
                    dex_id=dex,
                    dex_name=mapping.canonical_name,
                    base_token=base_token,
                    quote_token=quote_token,
                    provider_rank=(page - 1) * 20 + index,
                    volume_24h_usd=_number((attrs.get("volume_usd") or {}).get("h24")),
                    liquidity_usd=_number(attrs.get("reserve_in_usd")),
                    transactions_24h=int(tx) if isinstance(tx, (int, float)) else None,
                    observed_at=str(
                        attrs.get("updated_at") or attrs.get("pool_created_at") or "unknown"
                    ),
                    pair_name=str(attrs.get("name")) if attrs.get("name") else None,
                    base_symbol=base_symbol,
                    quote_symbol=quote_symbol,
                    ranking_provider=self.last_source,
                )
            )
        return result

    def _load_bootstrap(self, top_k: int) -> list[PoolCandidate]:
        path = Path(__file__).with_name("discovery_bootstrap.json")
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProviderError("source_unavailable", detail="bootstrap_missing") from exc
        pools: list[PoolCandidate] = []
        for row in document.get("pools", []):
            pools.append(
                PoolCandidate(
                    address=str(row["address"]).lower(),
                    network="bsc",
                    dex_id=str(row.get("dex_id", "pancakeswap_v2")),
                    dex_name=str(row.get("dex_name", "PancakeSwap V2")),
                    base_token=str(row.get("base_token", "")).lower(),
                    quote_token=str(row.get("quote_token", "")).lower(),
                    provider_rank=int(row.get("provider_rank", len(pools) + 1)),
                    volume_24h_usd=_number(row.get("volume_24h_usd")),
                    liquidity_usd=_number(row.get("liquidity_usd")),
                    transactions_24h=int(row["transactions_24h"])
                    if row.get("transactions_24h") is not None
                    else None,
                    observed_at=str(
                        row.get("observed_at") or document.get("captured_at") or "unknown"
                    ),
                    pair_name=row.get("pair_name"),
                    base_symbol=row.get("base_symbol"),
                    quote_symbol=row.get("quote_symbol"),
                    ranking_provider="geckoterminal_bootstrap",
                )
            )
            if len(pools) >= top_k:
                break
        if not pools:
            raise ProviderError("quality_failed", detail="bootstrap_empty")
        self.last_source = "geckoterminal_bootstrap"
        return pools[:top_k]

    def discover(self, *, top_k: int = 3, dex: str = "pancakeswap_v2") -> list[PoolCandidate]:
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10")
        dex = normalize_dex_id(dex)
        try:
            self.require_pancake_mapping(dex)
        except ProviderError:
            if self.allow_bootstrap:
                return self._load_bootstrap(top_k)
            raise
        if self.prefer_bootstrap and self.allow_bootstrap:
            return self._load_bootstrap(top_k)
        result: list[PoolCandidate] = []
        try:
            self.last_source = "geckoterminal"
            page = 1
            while len(result) < top_k and page <= 5:
                key = (
                    "geckoterminal",
                    "bsc",
                    dex,
                    "h24_volume_usd_desc",
                    page,
                    20,
                    self._fingerprint(),
                )
                cached = self._cache.get(key)
                now = self.clock()
                if cached and now - cached[0] <= self.cache_ttl_seconds:
                    document = cached[1]
                else:
                    document = self._request(
                        "/networks/bsc/pools"
                        "?include=base_token,quote_token,dex"
                        f"&page={page}&sort=h24_volume_usd_desc"
                    )
                parsed = self._parse_pools(document, dex=dex, page=page)
                if not cached or now - cached[0] > self.cache_ttl_seconds:
                    self._cache[key] = (now, document)
                for pool in parsed:
                    result.append(pool)
                    if len(result) >= top_k:
                        break
                if not document.get("data"):
                    break
                page += 1
            if result:
                return result[:top_k]
            raise ProviderError("quality_failed", detail="no_pancake_v2_pools")
        except ProviderError:
            if not self.allow_bootstrap:
                raise
            return self._load_bootstrap(top_k)
