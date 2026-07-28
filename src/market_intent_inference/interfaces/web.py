"""Localhost-only WebUI and JSON API."""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from ..application.bsc_pipeline import BSCAnalysisConfig, BSCAnalyzer


def _query(path: str) -> dict[str, str]:
    raw = path.split("?", 1)[1] if "?" in path else ""
    result: dict[str, str] = {}
    for part in raw.split("&"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[key] = value
    return result


def make_handler(analyzer: BSCAnalyzer, static_root: str | Path = "web"):
    root = Path(static_root).resolve()
    project_root = root.parent if root.name == "web" else root

    class Handler(BaseHTTPRequestHandler):
        def _send(
            self,
            value: Any,
            status: int = 200,
            content_type: str = "application/json",
        ) -> None:
            if isinstance(value, bytes):
                body = value
            elif content_type.startswith("application/json"):
                body = json.dumps(value, ensure_ascii=False).encode("utf-8")
            else:
                body = str(value).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _safe_static(self, relative: str) -> Path | None:
            candidate = (root / relative).resolve()
            if root not in candidate.parents and candidate != root:
                return None
            return candidate if candidate.is_file() else None

        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            if ".." in path or path.startswith("//"):
                self._send({"error": "not_found"}, 404)
                return
            if path == "/api/health":
                rpc = analyzer.rpc.safe_connection_summary()
                chain_id = 56
                payload = {
                    "ok": True,
                    "chain_id": chain_id,
                    "provider": "geckoterminal",
                    "ranking_metric": "h24_volume_usd",
                    "paper_only": True,
                    "rpc": rpc,
                    "rpc_configured": bool(rpc.get("rpc_host")),
                }
                try:
                    chain_id = analyzer.rpc.chain_id()
                    payload["chain_id"] = chain_id
                    payload["safe_block"] = analyzer.rpc.safe_block()
                except Exception:  # noqa: BLE001 - health remains available on probe failure
                    payload["ok"] = False
                    payload["safe_block"] = None
                    payload["rpc_probe"] = "degraded"
                self._send(payload)
                return
            if path == "/api/bsc/pools":
                try:
                    top_k = int(_query(self.path).get("top_k", "3"))
                    if not 1 <= top_k <= 10:
                        raise ValueError
                    pools = analyzer.list_pools(top_k)
                    self._send(
                        {
                            "top_k": top_k,
                            "pools": pools,
                            "ranking_provider": analyzer.gecko.last_source,
                            "ranking_metric": "h24_volume_usd",
                        }
                    )
                except (ValueError, RuntimeError) as exc:
                    reason = getattr(exc, "reason", None) or "source_unavailable"
                    self._send({"error": reason}, 503)
                return
            if path == "/api/bsc/analyze":
                self._send({"error": "method_not_allowed"}, 405)
                return
            if path.startswith("/api/runs/"):
                parts = [part for part in path.split("/") if part]
                if len(parts) >= 3:
                    run_id = parts[2]
                    if "/" in run_id or ".." in run_id:
                        self._send({"error": "not_found"}, 404)
                        return
                    if len(parts) == 4 and parts[3] == "events":
                        self._send({"run_id": run_id, "events": analyzer.store.read_events(run_id)})
                        return
                    if len(parts) == 3:
                        summary = analyzer.store.read_summary(run_id)
                        self._send(summary or {"error": "not_found"}, 200 if summary else 404)
                        return
            if path in {"/", "/index.html"}:
                file_path = self._safe_static("index.html")
                if file_path is None:
                    self._send("not_found", 404, "text/plain")
                    return
                self._send(
                    file_path.read_text(encoding="utf-8"),
                    content_type="text/html; charset=utf-8",
                )
                return
            if path in {"/app.js", "/styles.css"}:
                file_path = self._safe_static(path[1:])
                if file_path is None:
                    self._send("not_found", 404, "text/plain")
                    return
                content_type = "text/javascript" if path.endswith("js") else "text/css"
                self._send(file_path.read_text(encoding="utf-8"), content_type=content_type)
                return
            if path == "/graphify-out/GRAPH_REPORT.md":
                report = (project_root / "graphify-out" / "GRAPH_REPORT.md").resolve()
                if not report.is_file() or project_root not in report.parents:
                    self._send("not_found", 404, "text/plain")
                    return
                self._send(
                    report.read_text(encoding="utf-8"),
                    content_type="text/markdown; charset=utf-8",
                )
                return
            if path == "/graphify-out/graph.json":
                graph = (project_root / "graphify-out" / "graph.json").resolve()
                if not graph.is_file() or project_root not in graph.parents:
                    self._send("not_found", 404, "text/plain")
                    return
                self._send(graph.read_bytes(), content_type="application/json")
                return
            self._send({"error": "not_found"}, 404)

        def do_POST(self) -> None:  # noqa: N802
            if self.path.split("?", 1)[0] != "/api/bsc/analyze":
                self._send({"error": "not_found"}, 404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > 32_768:
                    raise ValueError
                payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
                if not isinstance(payload, dict):
                    raise ValueError
                allowed = {
                    "paper",
                    "mode",
                    "top_k",
                    "confirmation_lag",
                    "lookback_blocks",
                    "pool_addresses",
                }
                if set(payload) - allowed:
                    raise ValueError
                mode = payload.get("mode", "spot_long_only")
                if payload.get("paper") is not True or mode != "spot_long_only":
                    raise ValueError
                top_k = payload.get("top_k", 3)
                lookback_blocks = payload.get("lookback_blocks", 40)
                confirmation_lag = payload.get("confirmation_lag", 3)
                if (
                    type(top_k) is not int
                    or not 1 <= top_k <= 10
                    or type(lookback_blocks) is not int
                    or not 1 <= lookback_blocks <= 5_000
                    or type(confirmation_lag) is not int
                    or not 0 <= confirmation_lag <= 64
                ):
                    raise ValueError
                if any(
                    any(
                        token in str(key).lower()
                        for token in ("wallet", "private", "secret", "key")
                    )
                    for key in payload
                ):
                    raise ValueError
                addresses = payload.get("pool_addresses")
                if addresses is not None and (
                    not isinstance(addresses, list)
                    or not 1 <= len(addresses) <= 10
                    or any(
                        not isinstance(address, str)
                        or re.fullmatch(r"0x[0-9a-fA-F]{40}", address) is None
                        for address in addresses
                    )
                ):
                    raise ValueError
                config = BSCAnalysisConfig(
                    top_k=top_k,
                    confirmation_lag=confirmation_lag,
                    lookback_blocks=lookback_blocks,
                )
                result = analyzer.analyze(config, payload.get("pool_addresses"))
                self._send(result)
            except (ValueError, TypeError, RuntimeError) as exc:
                reason = getattr(exc, "reason", None) or "quality_failed"
                self._send({"error": reason}, 400)

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def create_server(
    analyzer: BSCAnalyzer,
    host: str = "127.0.0.1",
    port: int = 8765,
    static_root: str | Path = "web",
) -> ThreadingHTTPServer:
    if host != "127.0.0.1":
        raise ValueError("WebUI must bind to localhost")
    return ThreadingHTTPServer((host, port), make_handler(analyzer, static_root))
