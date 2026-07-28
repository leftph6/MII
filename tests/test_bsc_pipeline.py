from pathlib import Path

import pytest
from test_bsc_rpc import fake

from market_intent_inference.adapters.bsc_rpc import BSCReadClient
from market_intent_inference.adapters.geckoterminal import GeckoTerminalClient
from market_intent_inference.application.bsc_pipeline import BSCAnalysisConfig, BSCAnalyzer
from market_intent_inference.application.run_store import RunStore

FIXTURES = Path(__file__).parent / "fixtures"


def test_pipeline_config_is_paper_only() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        BSCAnalysisConfig(paper=False)


def _transport(method, path):
    if path.endswith("/dexes"):
        return 200, (FIXTURES / "geckoterminal_dexes.json").read_bytes()
    return 200, (FIXTURES / "geckoterminal_top_pools.json").read_bytes()


def test_pipeline_keeps_provider_snapshot_out_of_features(tmp_path) -> None:
    analyzer = BSCAnalyzer(
        GeckoTerminalClient(transport=_transport),
        BSCReadClient("https://rpc.example", transport=fake),
        RunStore(tmp_path),
    )
    result = analyzer.analyze()
    assert result["run_id"]
    assert result["audit"]["audit_degraded"] is False
    assert all("provider_rank" not in pool.get("features", {}) for pool in result["pools"])
    assert all("volume_24h_usd" not in pool.get("features", {}) for pool in result["pools"])
    assert all(pool["rpc_verified"] for pool in result["pools"])
    assert all(pool["features"] for pool in result["pools"])
    assert all(pool["decision"]["status"] == "no_trade" for pool in result["pools"])
    assert all(pool["prediction"]["abstain"] for pool in result["pools"])
    events = analyzer.store.read_events(result["run_id"])
    required = {
        "timestamp",
        "event_name",
        "schema_version",
        "level",
        "service",
        "module",
        "operation",
        "run_id",
        "trace_id",
        "parent_id",
        "status",
        "duration_ms",
        "attempt",
        "retryable",
        "config_hash",
        "code_version",
        "data_version",
    }
    assert required <= set(events[-1])


def test_pipeline_keeps_reserve_features_when_getlogs_fails(tmp_path) -> None:
    def transport(payload):
        if payload["method"] == "eth_getLogs":
            return {"error": {"message": "rate limited"}}
        return fake(payload)

    analyzer = BSCAnalyzer(
        GeckoTerminalClient(transport=_transport),
        BSCReadClient("https://rpc.example", transport=transport),
        RunStore(tmp_path),
    )
    result = analyzer.analyze()
    assert result["pools"]
    assert all(pool["rpc_verified"] for pool in result["pools"])
    assert all(pool["features"].get("reserve0") for pool in result["pools"])
    assert all(pool["features"]["failure_count"] > 0 for pool in result["pools"])
    assert all(pool["decision"]["status"] == "abstain" for pool in result["pools"])


def test_pipeline_abstains_when_timestamps_missing(tmp_path) -> None:
    def transport(payload):
        if payload["method"] == "eth_getBlockByNumber":
            return {"result": {}}
        return fake(payload)

    analyzer = BSCAnalyzer(
        GeckoTerminalClient(transport=_transport),
        BSCReadClient("https://rpc.example", transport=transport),
        RunStore(tmp_path),
    )
    result = analyzer.analyze()
    # Reserve/swap microstructure remains visible; wall-clock gaps force abstain.
    assert result["quality"] == "derived"
    assert all(pool["decision"]["status"] == "abstain" for pool in result["pools"])
    assert all(pool["features"] for pool in result["pools"])
    assert all("insufficient_data" in pool["reason_codes"] for pool in result["pools"])
    assert all(pool["features"].get("swap_count") == 0.0 for pool in result["pools"])
