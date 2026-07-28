"""Start the localhost-only BSC WebUI."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from typing import Any

from market_intent_inference.adapters.bsc_rpc import (
    DEFAULT_FALLBACK_RPCS,
    BSCReadClient,
    RPCError,
)
from market_intent_inference.adapters.geckoterminal import GeckoTerminalClient
from market_intent_inference.application.bsc_pipeline import BSCAnalyzer
from market_intent_inference.interfaces.web import create_server


def _rpc_urls_from_env() -> list[str]:
    primary = os.getenv("BSC_RPC_URL") or "https://1rpc.io/bnb"
    extra = os.getenv("BSC_RPC_FALLBACKS", "")
    configured = [item.strip() for item in extra.split(",") if item.strip()]
    merged: list[str] = []
    for item in [primary, *configured, *DEFAULT_FALLBACK_RPCS]:
        if item not in merged:
            merged.append(item)
    return merged


def _curl_rpc_transport(rpc_urls: list[str]):
    curl = shutil.which("curl")
    if curl is None:
        return None
    preferred = {"url": rpc_urls[0]}

    def _once(rpc_url: str, payload: dict[str, Any], timeout: str) -> dict[str, Any]:
        completed = subprocess.run(
            [
                curl,
                "-sS",
                "-m",
                timeout,
                "--http1.1",
                "--max-filesize",
                "1048576",
                "-X",
                "POST",
                rpc_url,
                "-H",
                "Content-Type: application/json",
                "-H",
                "User-Agent: market-intent-inference/0.1",
                "--data-binary",
                json.dumps(payload),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            raise RPCError(
                "source_unavailable",
                detail=completed.stderr.strip() or "curl_failed",
            )
        try:
            value = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RPCError(
                "source_unavailable",
                detail="curl_malformed_json",
            ) from exc
        if not isinstance(value, dict):
            raise RPCError("source_unavailable", detail="curl_non_object")
        if "error" in value:
            err = value.get("error") or {}
            raise RPCError("source_unavailable", detail=str(err.get("message", "rpc_error")))
        return value

    def transport(payload: dict[str, Any]) -> dict[str, Any]:
        method = str(payload.get("method", ""))
        # getLogs can hang on some free endpoints; keep a short timeout and
        # prefer the sticky primary before spending time on fallbacks.
        timeout = "8" if method == "eth_getLogs" else "10"
        ordered = [preferred["url"], *[url for url in rpc_urls if url != preferred["url"]]]
        if method == "eth_getLogs":
            ordered = ordered[:2]  # primary + one fallback, no deep fanout
        last_error: RPCError | None = None
        for rpc_url in ordered:
            try:
                value = _once(rpc_url, payload, timeout)
                preferred["url"] = rpc_url
                return value
            except RPCError as exc:
                last_error = exc
                continue
        raise last_error or RPCError("source_unavailable", detail="all_rpc_endpoints_failed")

    return transport


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    rpc_urls = _rpc_urls_from_env()
    primary = rpc_urls[0]
    transport = _curl_rpc_transport(rpc_urls)
    rpc = BSCReadClient(
        primary,
        transport=transport,
        fallback_urls=() if transport else rpc_urls[1:],
        log_chunk_blocks=40,
        timeout_seconds=20,
        max_retries=3,
    )
    analyzer = BSCAnalyzer(
        GeckoTerminalClient(
            allow_bootstrap=True,
            prefer_bootstrap=True,
            timeout_seconds=5,
            max_retries=0,
        ),
        rpc,
    )
    server = create_server(analyzer, args.host, args.port)
    print(f"market-intent WebUI listening on http://{args.host}:{args.port}")
    summary = analyzer.rpc.safe_connection_summary()
    print(
        "rpc_host="
        f"{summary.get('rpc_host')} "
        f"endpoints={len(rpc_urls)} "
        f"transport={'curl-failover' if transport else 'http.client-failover'}"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
