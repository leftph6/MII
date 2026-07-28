import json
from pathlib import Path

import pytest

from market_intent_inference.adapters.bsc_rpc import BSCReadClient, Position, RPCError

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "rpc_logs.json").read_text())
POOL = "0x0000000000000000000000000000000000000001"
TOKEN0 = "0x0000000000000000000000000000000000000011"
TOKEN1 = "0x0000000000000000000000000000000000000022"


def fake(payload):
    method = payload["method"]
    if method == "eth_chainId":
        return {"result": FIXTURE["chain_id"]}
    if method == "eth_blockNumber":
        return {"result": FIXTURE["latest"]}
    if method == "eth_getBlockByNumber":
        return {"result": FIXTURE["blocks"].get(payload["params"][0])}
    if method == "eth_getLogs":
        return {"result": FIXTURE["logs"]}
    if method == "eth_call":
        selector = payload["params"][0]["data"]
        if selector.endswith("0dfe1681"):
            return {"result": "0x" + "0" * 24 + TOKEN0[2:]}
        if selector.endswith("d21220a7"):
            return {"result": "0x" + "0" * 24 + TOKEN1[2:]}
        if selector.endswith("c45a0155"):
            return {"result": "0x" + "0" * 24 + "ca143ce32fe78f1f7019d7d551a6402fc5350c73"}
        return {"result": "0x" + ("0" * 62 + "64") + ("0" * 62 + "c8") + ("0" * 64)}
    raise AssertionError(method)


def test_chain_pair_and_cutoff_safe_logs() -> None:
    client = BSCReadClient(
        "https://user:token@rpc.example.test/path?key=value#fragment",
        transport=fake,
    )
    assert client.chain_id() == 56
    assert client.safe_block(3) == 109
    verified = client.verify_pair(POOL)
    assert verified["verified"] is True
    assert verified["reserve0"] == 100
    assert verified["reserve1"] == 200
    logs = client.swap_logs(
        POOL,
        from_block=109,
        to_block=109,
        decision_position=Position(109, 0, 0),
    )
    assert len(logs) == 1
    assert logs[0].event_time is not None
    summary = client.safe_connection_summary()
    assert summary["has_userinfo"] is True
    assert "token" not in summary["rpc_fingerprint"]
    assert summary["rpc_host"] == "rpc.example.test"


def test_same_block_later_event_is_excluded() -> None:
    client = BSCReadClient("https://rpc.example.test", transport=fake)
    logs = client.swap_logs(
        POOL,
        from_block=109,
        to_block=109,
        decision_position=Position(109, 0, 0),
    )
    assert [log.position.transaction_index for log in logs] == [0]


def test_missing_block_timestamp_keeps_position_but_null_time() -> None:
    def transport(payload):
        if payload["method"] == "eth_getBlockByNumber":
            return {"result": {}}
        return fake(payload)

    client = BSCReadClient("https://rpc.example.test", transport=transport)
    logs = client.swap_logs(
        POOL,
        from_block=109,
        to_block=109,
        decision_position=Position(109, 2**31 - 1, 2**31 - 1),
    )
    assert logs and all(log.event_time is None for log in logs)


def test_block_timestamp_rpc_errors_do_not_drop_swaps() -> None:
    def transport(payload):
        if payload["method"] == "eth_getBlockByNumber":
            raise RPCError("source_unavailable", detail="timeout")
        return fake(payload)

    client = BSCReadClient("https://rpc.example.test", transport=transport)
    logs = client.swap_logs(
        POOL,
        from_block=109,
        to_block=109,
        decision_position=Position(109, 2**31 - 1, 2**31 - 1),
    )
    assert logs and all(log.event_time is None for log in logs)


def test_factory_and_chain_mismatch_fail_closed() -> None:
    client = BSCReadClient("https://rpc.example.test", transport=fake)
    with pytest.raises(RPCError):
        client.verify_pair(POOL, dex_router="0x0000000000000000000000000000000000000000")

    def wrong_chain(payload):
        if payload["method"] == "eth_chainId":
            return {"result": "0x1"}
        return fake(payload)

    with pytest.raises(RPCError):
        BSCReadClient("https://rpc.example.test", transport=wrong_chain).chain_id()


def test_pair_state_reads_use_safe_block_and_bad_timestamp_is_soft() -> None:
    calls = []

    def recording(payload):
        calls.append(payload)
        if payload["method"] == "eth_getBlockByNumber":
            return {"result": {"timestamp": "0xnot-a-number"}}
        return fake(payload)

    client = BSCReadClient("https://rpc.example.test", transport=recording)
    client.verify_pair(POOL, state_block=109)
    assert {item["params"][1] for item in calls if item["method"] == "eth_call"} == {"0x6d"}
    assert client.block_timestamp(109) is None


def test_partial_log_failure_is_exposed_without_dropping_rows() -> None:
    def partial(payload):
        if payload["method"] == "eth_getLogs" and payload["params"][0]["fromBlock"] == "0x6e":
            return {"error": {"message": "temporary unavailable"}}
        return fake(payload)

    client = BSCReadClient("https://rpc.example.test", transport=partial, log_chunk_blocks=1)
    logs = client.swap_logs(
        POOL, from_block=109, to_block=110, decision_position=Position(110, 0, 0)
    )
    assert logs
    assert client.last_logs_complete is False
    assert client.last_logs_error == "not_supported"

    def wrong_factory(payload):
        if payload["method"] == "eth_call" and payload["params"][0]["data"].endswith("c45a0155"):
            return {"result": "0x" + "0" * 24 + "1111111111111111111111111111111111111111"}
        return fake(payload)

    with pytest.raises(RPCError):
        BSCReadClient("https://rpc.example.test", transport=wrong_factory).verify_pair(POOL)
