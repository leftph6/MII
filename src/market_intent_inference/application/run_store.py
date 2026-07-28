"""Append-only, redacted run summaries and structured JSONL events."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_SECRET_KEY = re.compile(
    r"(authorization|api[_-]?key|access[_-]?token|secret|password|private[_-]?key)",
    re.I,
)
_SECRET_VALUE = re.compile(
    r"(bearer\s+\S+|api[_-]?key[=:]\S+|://[^/\s]+:[^@/\s]+@)",
    re.I,
)


def _redact_string(text: str) -> str:
    if "://" in text:
        scheme, rest = text.split("://", 1)
        authority = rest.split("/", 1)[0]
        host = authority.rsplit("@", 1)[-1].split("?", 1)[0].split("#", 1)[0]
        text = f"{scheme}://{host}"
    if _SECRET_KEY.search(text) or _SECRET_VALUE.search(text):
        return "[REDACTED]"
    return text


def _redact(value: Any, key: str = "") -> Any:
    if _SECRET_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): _redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v, key) for v in value]
    if isinstance(value, str):
        return _redact_string(value)
    return value


class RunStore:
    def __init__(self, root: str | Path = "artifacts/runs") -> None:
        self.root = Path(root)

    def write(
        self, run_id: str, summary: dict[str, Any], events: list[dict[str, Any]]
    ) -> dict[str, Any]:
        try:
            summary_path = self._safe_path(run_id, "summary.json")
            events_path = self._safe_path(run_id, "events.jsonl")
            if summary_path is None or events_path is None:
                return {"run_id": run_id, "audit_degraded": True, "path": None}
            directory = summary_path.parent
            directory.mkdir(parents=True, exist_ok=True)
            summary_path = self._safe_path(run_id, "summary.json")
            events_path = self._safe_path(run_id, "events.jsonl")
            if summary_path is None or events_path is None:
                return {"run_id": run_id, "audit_degraded": True, "path": None}
            safe_summary = _redact(dict(summary))
            safe_summary["run_id"] = run_id
            safe_summary.setdefault("audit_degraded", False)
            summary_path.write_text(
                json.dumps(safe_summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            with events_path.open("a", encoding="utf-8") as handle:
                for event in events:
                    handle.write(
                        json.dumps(_redact(event), ensure_ascii=False, sort_keys=True) + "\n"
                    )
            return {"run_id": run_id, "audit_degraded": False, "path": None}
        except OSError:
            return {"run_id": run_id, "audit_degraded": True, "path": None}

    def _safe_path(self, run_id: str, filename: str) -> Path | None:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", run_id):
            return None
        root = self.root.resolve()
        path = (root / run_id / filename).resolve()
        if root not in path.parents or path.name != filename:
            return None
        return path

    def read_summary(self, run_id: str) -> dict[str, Any] | None:
        path = self._safe_path(run_id, "summary.json")
        if path is None:
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def read_events(self, run_id: str) -> list[dict[str, Any]]:
        path = self._safe_path(run_id, "events.jsonl")
        if path is None:
            return []
        try:
            return [
                json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line
            ]
        except (OSError, json.JSONDecodeError):
            return []
