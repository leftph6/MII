"""Minimal read-only JSON-RPC adapter and cutoff-safe V2 log decoder."""

from __future__ import annotations

import hashlib
import http.client
import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

CHAIN_ID = 56
FACTORY_V2 = "0xca143ce32fe78f1f7019d7d551a6402fc5350c73"
ROUTER_V2 = "0x10ed43c718714eb63d5aa57b78b54704e256024e"
SWAP_TOPIC0 = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
CALLS = {
    "token0": "0x0dfe1681",
    "token1": "0xd21220a7",
    "getReserves": "0x0902f1ac",
    "factory": "0xc45a0155",
}
ALLOWED_METHODS = frozenset(
    {"eth_chainId", "eth_blockNumber", "eth_getBlockByNumber", "eth_getLogs", "eth_call"}
)
DEFAULT_FALLBACK_RPCS = (
    "https://bsc.publicnode.com",
    "https://bsc-rpc.publicnode.com",
)


class RPCError(RuntimeError):
    def __init__(self, reason: str, detail: str | None = None) -> None:
        super().__init__(detail or reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True, order=True)
class Position:
    block_number: int
    transaction_index: int
    log_index: int


@dataclass(frozen=True)
class SwapLog:
    position: Position
    pool: str
    sender: str
    recipient: str
    amount0_in: int
    amount1_in: int
    amount0_out: int
    amount1_out: int
    event_time: datetime | None
    source: str = "bsc_rpc"


def _hex(value: Any) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise RPCError("quality_failed")
    try:
        return int(value, 16)
    except ValueError as exc:
        raise RPCError("quality_failed") from exc


def _address(value: str) -> str:
    return "0x" + value[-40:].lower()


def _decode_reserves(raw: str) -> tuple[int, int]:
    data = raw[2:] if raw.startswith("0x") else raw
    if len(data) < 128:
        raise RPCError("quality_failed")
    return int(data[0:64], 16), int(data[64:128], 16)


def _split_rpc_url(rpc_url: str) -> tuple[str, str, str, bool]:
    scheme, rest = rpc_url.split("://", 1) if "://" in rpc_url else ("", rpc_url)
    authority, _, path = rest.partition("/")
    has_userinfo = "@" in authority
    host = authority.rsplit("@", 1)[-1].split("?", 1)[0].split("#", 1)[0]
    return scheme, host, "/" + path if path else "/", has_userinfo


class BSCReadClient:
    def __init__(
        self,
        rpc_url: str,
        *,
        transport: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        fallback_urls: list[str] | tuple[str, ...] | None = None,
        log_chunk_blocks: int = 40,
        timeout_seconds: int = 20,
        max_retries: int = 3,
    ) -> None:
        primary = rpc_url.strip()
        extras = [
            item.strip()
            for item in (fallback_urls or ())
            if item and item.strip() and item.strip() != primary
        ]
        self.rpc_urls = [primary, *extras]
        self.rpc_url = primary
        self.transport = transport
        self.log_chunk_blocks = max(1, log_chunk_blocks)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._request_id = 0
        self._active_index = 0
        self._cached_chain_id: int | None = None
        self._lock = threading.RLock()
        self.last_logs_complete = True
        self.last_logs_error: str | None = None

    def safe_connection_summary(self) -> dict[str, Any]:
        scheme, host, _, has_userinfo = _split_rpc_url(self.rpc_url)
        material = f"{scheme}|{host}|has_userinfo={has_userinfo}"
        return {
            "rpc_scheme": scheme,
            "rpc_host": host,
            "has_userinfo": has_userinfo,
            "rpc_fingerprint": hashlib.sha256(material.encode()).hexdigest()[:16],
            "rpc_fallback_count": max(0, len(self.rpc_urls) - 1),
            "active_rpc_host": _split_rpc_url(self.rpc_urls[self._active_index])[1],
        }

    def _post_once(self, rpc_url: str, payload: dict[str, Any]) -> dict[str, Any]:
        scheme, host, path, _ = _split_rpc_url(rpc_url)
        connection: http.client.HTTPConnection
        if scheme == "https":
            connection = http.client.HTTPSConnection(host, timeout=self.timeout_seconds)
        elif scheme == "http":
            connection = http.client.HTTPConnection(host, timeout=self.timeout_seconds)
        else:
            raise RPCError("source_unavailable", detail="unsupported_scheme")
        try:
            connection.request(
                "POST",
                path.split("?", 1)[0].split("#", 1)[0] or "/",
                body=json.dumps(payload),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "market-intent-inference/0.1 (+paper-research)",
                },
            )
            raw_bytes = connection.getresponse().read(1_048_577)
            if len(raw_bytes) > 1_048_576:
                raise RPCError("quality_failed", detail="response_too_large")
            raw = raw_bytes.decode()
            return json.loads(raw)
        finally:
            connection.close()

    def _rotate(self) -> bool:
        if self._active_index + 1 >= len(self.rpc_urls):
            return False
        self._active_index += 1
        self.rpc_url = self.rpc_urls[self._active_index]
        self._cached_chain_id = None
        return True

    def _invoke(
        self,
        rpc_url: str,
        payload: dict[str, Any],
        *,
        use_transport: bool,
    ) -> dict[str, Any]:
        if use_transport and self.transport is not None:
            return self.transport(payload)
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return self._post_once(rpc_url, payload)
            except (
                TimeoutError,
                OSError,
                http.client.HTTPException,
                json.JSONDecodeError,
            ) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise RPCError(
                        "source_unavailable",
                        detail=f"{type(exc).__name__}:{exc}",
                    ) from exc
                time.sleep(0.25 * (2**attempt))
        raise RPCError("source_unavailable", detail=str(last_error))

    def call(self, method: str, params: list[Any]) -> Any:
        with self._lock:
            return self._call(method, params)

    def _call(self, method: str, params: list[Any]) -> Any:
        if method.startswith("eth_send") or method not in ALLOWED_METHODS:
            raise RPCError("not_supported")
        self._request_id += 1
        payload = {"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": params}
        last_error: RPCError | None = None
        attempts = 0
        while attempts < len(self.rpc_urls):
            rpc_url = self.rpc_urls[self._active_index]
            use_transport = self.transport is not None and self._active_index == 0
            try:
                response = self._invoke(rpc_url, payload, use_transport=use_transport)
                if "error" in response:
                    err = response.get("error") or {}
                    message = str(err.get("message", "rpc_error"))
                    if method == "eth_getLogs":
                        raise RPCError("not_supported", detail=message)
                    raise RPCError("source_unavailable", detail=message)
                return response.get("result")
            except RPCError as exc:
                last_error = exc
                if exc.reason not in {"source_unavailable", "not_supported"}:
                    raise
                if not self._rotate():
                    raise
                attempts += 1
                continue
        raise last_error or RPCError("source_unavailable")

    def chain_id(self) -> int:
        if self._cached_chain_id is not None:
            return self._cached_chain_id
        value = _hex(self.call("eth_chainId", []))
        if value != CHAIN_ID:
            raise RPCError("quality_failed")
        self._cached_chain_id = value
        return value

    def safe_block(self, confirmation_lag: int = 3) -> int:
        latest = _hex(self.call("eth_blockNumber", []))
        if confirmation_lag < 0 or latest < confirmation_lag:
            raise RPCError("quality_failed")
        return latest - confirmation_lag

    def block_timestamp(self, block_number: int) -> datetime | None:
        try:
            value = self.call("eth_getBlockByNumber", [hex(block_number), False])
        except RPCError:
            return None
        if not isinstance(value, dict) or not value.get("timestamp"):
            return None
        try:
            timestamp = _hex(value["timestamp"])
            if timestamp <= 0:
                return None
            return datetime.fromtimestamp(timestamp, tz=UTC)
        except (RPCError, OverflowError, OSError, ValueError):
            return None

    def verify_pair(
        self,
        pool: str,
        *,
        dex_factory: str = FACTORY_V2,
        dex_router: str = ROUTER_V2,
        state_block: int | None = None,
    ) -> dict[str, Any]:
        if dex_factory.lower() != FACTORY_V2 or dex_router.lower() != ROUTER_V2:
            raise RPCError("quality_failed")
        chain = self.chain_id()
        block_tag = hex(state_block) if state_block is not None else "latest"
        values = {
            name: self.call("eth_call", [{"to": pool, "data": data}, block_tag])
            for name, data in CALLS.items()
        }
        if any(not isinstance(values[name], str) for name in CALLS):
            raise RPCError("quality_failed", detail="eth_call_missing")
        factory = _address(str(values["factory"])[2:])
        if factory.lower() != FACTORY_V2:
            raise RPCError("quality_failed", detail="factory_mismatch")
        reserve0, reserve1 = _decode_reserves(str(values["getReserves"]))
        return {
            "chain_id": chain,
            "pool": pool.lower(),
            "token0": _address(str(values["token0"])[2:]),
            "token1": _address(str(values["token1"])[2:]),
            "reserve0": reserve0,
            "reserve1": reserve1,
            "factory": FACTORY_V2,
            "router": ROUTER_V2,
            "verified": True,
        }

    def _get_logs_range(
        self,
        pool: str,
        start: int,
        end: int,
        *,
        depth: int = 0,
    ) -> list[dict[str, Any]]:
        span = end - start + 1
        try:
            chunk = self.call(
                "eth_getLogs",
                [
                    {
                        "address": pool,
                        "fromBlock": hex(start),
                        "toBlock": hex(end),
                        "topics": [SWAP_TOPIC0],
                    }
                ],
            )
        except RPCError as exc:
            detail = (exc.detail or "").lower()
            # Only bisect when the provider rejects the window size — never on
            # auth/archive/rate-limit errors, which would explode into O(n) calls.
            range_limited = any(
                token in detail
                for token in (
                    "block range",
                    "range is too large",
                    "too many blocks",
                    "query returned more than",
                    "exceed maximum block",
                )
            )
            if span > 1 and depth < 4 and range_limited:
                mid = start + span // 2 - 1
                left = self._get_logs_range(pool, start, mid, depth=depth + 1)
                try:
                    right = self._get_logs_range(pool, mid + 1, end, depth=depth + 1)
                except RPCError as right_exc:
                    self.last_logs_complete = False
                    self.last_logs_error = right_exc.reason
                    return left
                return left + right
            raise RPCError(exc.reason, detail=exc.detail) from exc
        if not isinstance(chunk, list):
            raise RPCError("quality_failed")
        return chunk

    def swap_logs(
        self,
        pool: str,
        *,
        from_block: int,
        to_block: int,
        decision_position: Position,
    ) -> list[SwapLog]:
        with self._lock:
            return self._swap_logs(
                pool,
                from_block=from_block,
                to_block=to_block,
                decision_position=decision_position,
            )

    def _swap_logs(
        self,
        pool: str,
        *,
        from_block: int,
        to_block: int,
        decision_position: Position,
    ) -> list[SwapLog]:
        if to_block < from_block:
            return []
        self.last_logs_complete = True
        self.last_logs_error = None
        rows: list[dict[str, Any]] = []
        start = from_block
        while start <= to_block:
            end = min(to_block, start + self.log_chunk_blocks - 1)
            try:
                rows.extend(self._get_logs_range(pool, start, end))
            except RPCError as exc:
                # Keep verified rows for display, but expose incomplete coverage.
                if rows:
                    self.last_logs_complete = False
                    self.last_logs_error = exc.reason
                    break
                raise RPCError(exc.reason, detail=exc.detail) from exc
            start = end + 1
        parsed: list[SwapLog] = []
        timestamps: dict[int, datetime | None] = {}
        for row in rows:
            topics = row.get("topics", [])
            data = str(row.get("data", "0x"))[2:]
            position = Position(
                _hex(row.get("blockNumber")),
                _hex(row.get("transactionIndex", "0x0")),
                _hex(row.get("logIndex", "0x0")),
            )
            if len(topics) < 3 or len(data) != 256 or position > decision_position:
                continue
            if str(topics[0]).lower() != SWAP_TOPIC0:
                continue
            words = [_hex("0x" + data[index : index + 64]) for index in range(0, 256, 64)]
            if position.block_number not in timestamps:
                timestamps[position.block_number] = self.block_timestamp(position.block_number)
            parsed.append(
                SwapLog(
                    position,
                    pool.lower(),
                    _address(topics[1][2:]),
                    _address(topics[2][2:]),
                    *words,
                    timestamps[position.block_number],
                )
            )
        return sorted(parsed, key=lambda item: item.position)
