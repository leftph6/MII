"""Explicit opt-in BSC RPC capability smoke; never sends a transaction."""

from __future__ import annotations

import os

from market_intent_inference.adapters.bsc_rpc import BSCReadClient, RPCError


def main() -> int:
    rpc_url = os.getenv("BSC_RPC_URL")
    if not rpc_url:
        print("BSC_RPC_URL_missing")
        return 0
    client = BSCReadClient(rpc_url)
    try:
        print({"rpc": client.safe_connection_summary(), "chain_id": client.chain_id()})
    except RPCError as exc:
        print({"rpc": client.safe_connection_summary(), "error": exc.reason})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
