from pathlib import Path


def test_project_has_no_coinman_import_or_path() -> None:
    root = Path(__file__).parents[1]
    forbidden = "coinman-arbitrage-bot"
    for path in root.joinpath("src").rglob("*.py"):
        assert forbidden not in path.read_text().lower()
