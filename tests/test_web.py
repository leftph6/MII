from pathlib import Path

import pytest
from test_bsc_rpc import fake

from market_intent_inference.adapters.bsc_rpc import BSCReadClient
from market_intent_inference.adapters.geckoterminal import GeckoTerminalClient
from market_intent_inference.application.bsc_pipeline import BSCAnalyzer
from market_intent_inference.application.run_store import RunStore
from market_intent_inference.interfaces.web import create_server, make_handler


def test_local_web_health_and_validation(tmp_path) -> None:
    fixtures = Path(__file__).parent / "fixtures"
    web_root = tmp_path / "web"
    web_root.mkdir()
    (web_root / "index.html").write_text("<html>ok</html>", encoding="utf-8")

    def transport(method, path):
        name = (
            "geckoterminal_dexes.json"
            if path.endswith("/dexes")
            else "geckoterminal_top_pools.json"
        )
        return 200, (fixtures / name).read_bytes()

    analyzer = BSCAnalyzer(
        GeckoTerminalClient(transport=transport),
        BSCReadClient("https://rpc.example", transport=fake),
        RunStore(tmp_path / "runs"),
    )
    handler = make_handler(analyzer, web_root)
    assert handler.__name__ == "Handler"
    with pytest.raises(ValueError):
        create_server(analyzer, host="0.0.0.0", port=0, static_root=web_root)
