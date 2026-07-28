from pathlib import Path

from market_intent_inference.adapters.geckoterminal import GeckoTerminalClient, ProviderError

ROOT = Path(__file__).parent / "fixtures"


def test_top_three_are_parsed_and_success_is_cached() -> None:
    calls = []

    def transport(method, path):
        calls.append(path)
        if path.endswith("/dexes"):
            return 200, (ROOT / "geckoterminal_dexes.json").read_bytes()
        return 200, (ROOT / "geckoterminal_top_pools.json").read_bytes()

    client = GeckoTerminalClient(transport=transport)
    first = client.discover()
    second = client.discover()
    assert [pool.provider_rank for pool in first] == [1, 2, 3]
    assert second[0].display_only is True
    assert second[0].dex_id == "pancakeswap_v2"
    assert second[0].base_symbol == "AAA"
    assert second[0].quote_symbol == "WBNB"
    assert second[0].pair_name == "AAA / WBNB"
    assert (
        sum(
            path.endswith(
                "/pools?include=base_token,quote_token,dex&page=1&sort=h24_volume_usd_desc"
            )
            for path in calls
        )
        == 1
    )


def test_provider_failure_falls_back_to_bootstrap() -> None:
    def transport(method, path):
        return 429, b"{}"

    client = GeckoTerminalClient(transport=transport, max_retries=0, allow_bootstrap=True)
    pools = client.discover(top_k=3)
    assert len(pools) == 3
    assert pools[0].ranking_provider == "geckoterminal_bootstrap"
    assert pools[0].address.startswith("0x")


def test_provider_failure_without_bootstrap_is_structured() -> None:
    calls = 0

    def transport(method, path):
        nonlocal calls
        calls += 1
        return 429, b"{}"

    client = GeckoTerminalClient(transport=transport, max_retries=0, allow_bootstrap=False)
    try:
        client.discover()
    except ProviderError as exc:
        assert exc.reason == "source_unavailable"
    else:
        raise AssertionError("expected provider failure")
    assert calls == 1
    assert client._cache == {}


def test_cache_expires_and_fingerprint_isolates() -> None:
    clock = {"now": 100.0}
    calls = []

    def transport(method, path):
        calls.append(path)
        if path.endswith("/dexes"):
            return 200, (ROOT / "geckoterminal_dexes.json").read_bytes()
        return 200, (ROOT / "geckoterminal_top_pools.json").read_bytes()

    client = GeckoTerminalClient(
        transport=transport,
        clock=lambda: clock["now"],
        cache_ttl_seconds=5,
    )
    client.discover()
    clock["now"] += 6
    client.discover()
    assert (
        sum(
            path.endswith(
                "/pools?include=base_token,quote_token,dex&page=1&sort=h24_volume_usd_desc"
            )
            for path in calls
        )
        == 2
    )
    other = GeckoTerminalClient(
        transport=transport,
        clock=lambda: clock["now"],
        cache_ttl_seconds=30,
    )
    other.discover()
    assert other._fingerprint() != client._fingerprint()
