import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCAN_ROOTS = (ROOT / "src", ROOT / "tests", ROOT / "pyproject.toml")
FORBIDDEN = re.compile(
    r"eth_sendRawTransaction|private[_-]?key|mnemonic|web3|requests|httpx|"
    r"urllib|subprocess|os\.environ",
    re.IGNORECASE,
)


def files_to_scan():
    for root in SCAN_ROOTS:
        if root.is_file():
            yield root
        elif root.exists():
            yield from root.rglob("*.py")


def main() -> int:
    violations = []
    for path in files_to_scan():
        text = path.read_text(encoding="utf-8")
        if match := FORBIDDEN.search(text):
            violations.append(f"{path.relative_to(ROOT)}:{match.group(0)}")
    if violations:
        print("security_boundary_failed")
        print("\n".join(violations))
        return 1
    print("security_boundary_ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
