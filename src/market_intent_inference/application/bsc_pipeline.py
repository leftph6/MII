"""Orchestrates provider discovery, read-only RPC verification, and fail-closed inference."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from ..adapters.bsc_rpc import BSCReadClient, Position, RPCError, SwapLog
from ..adapters.geckoterminal import GeckoTerminalClient, PoolCandidate, ProviderError
from ..domain import (
    Action,
    CalibrationStatus,
    ConstraintSet,
    EventPosition,
    LatentIntent,
    Posterior,
    PredictionContext,
    RiskField,
    RiskSnapshot,
    RiskStatus,
    Role,
    VenueCapability,
    VenueMode,
)
from ..inference import build_prediction_result, decide
from .run_store import RunStore


@dataclass(frozen=True)
class BSCAnalysisConfig:
    top_k: int = 3
    confirmation_lag: int = 3
    lookback_blocks: int = 40
    paper: bool = True
    mode: VenueMode = VenueMode.SPOT_LONG_ONLY

    def __post_init__(self) -> None:
        if self.paper is not True:
            raise ValueError("paper_only")
        if self.mode is not VenueMode.SPOT_LONG_ONLY:
            raise ValueError("unsupported_venue")
        if not 1 <= self.top_k <= 10 or self.confirmation_lag < 0 or self.lookback_blocks < 1:
            raise ValueError("invalid BSC analysis configuration")


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value else None


def _posterior(
    variable: str, key: tuple[str, str], cutoff: EventPosition, reason: str
) -> Posterior:
    return Posterior(
        variable,
        key,
        (),
        {},
        cutoff,
        calibration_status=CalibrationStatus.UNCALIBRATED,
        abstain=True,
        reason_codes=(reason,),
    )


def _features(
    verified: dict[str, Any],
    logs: list[SwapLog],
    lookback: int,
    failure_count: float = 0.0,
) -> dict[str, float]:
    reserve0 = float(verified["reserve0"])
    reserve1 = float(verified["reserve1"])
    buy_count = 0
    sell_count = 0
    token0_in = 0.0
    token1_in = 0.0
    token0_out = 0.0
    token1_out = 0.0
    for log in logs:
        token0_in += log.amount0_in
        token1_in += log.amount1_in
        token0_out += log.amount0_out
        token1_out += log.amount1_out
        if log.amount0_in and log.amount1_out:
            buy_count += 1
        if log.amount1_in and log.amount0_out:
            sell_count += 1
    mid_price = (reserve1 / reserve0) if reserve0 > 0 else 0.0
    net_token0 = token0_in - token0_out
    ofi = float(buy_count - sell_count)
    impact = abs(net_token0) / reserve0 if reserve0 > 0 else 0.0
    return {
        "reserve0": reserve0,
        "reserve1": reserve1,
        "mid_price": mid_price,
        "price_impact_proxy": impact,
        "buy_count": float(buy_count),
        "sell_count": float(sell_count),
        "token0_flow": net_token0,
        "token1_flow": token1_in - token1_out,
        "ofi_net_flow": ofi,
        "event_density": len(logs) / max(lookback, 1),
        "swap_count": float(len(logs)),
        "failure_count": failure_count,
    }


class BSCAnalyzer:
    def __init__(
        self,
        gecko: GeckoTerminalClient,
        rpc: BSCReadClient,
        store: RunStore | None = None,
    ) -> None:
        self.gecko = gecko
        self.rpc = rpc
        self.store = store or RunStore()

    def list_pools(self, top_k: int = 3) -> list[dict[str, Any]]:
        return [self._pool_dict(pool) for pool in self.gecko.discover(top_k=top_k)]

    @staticmethod
    def _pool_dict(pool: PoolCandidate) -> dict[str, Any]:
        return {
            "address": pool.address,
            "network": pool.network,
            "dex_id": pool.dex_id,
            "dex_name": pool.dex_name,
            "pair_name": pool.pair_name,
            "base_token": pool.base_token,
            "quote_token": pool.quote_token,
            "base_symbol": pool.base_symbol,
            "quote_symbol": pool.quote_symbol,
            "provider_rank": pool.provider_rank,
            "volume_24h_usd": pool.volume_24h_usd,
            "liquidity_usd": pool.liquidity_usd,
            "transactions_24h": pool.transactions_24h,
            "observed_at": pool.observed_at,
            "display_only": True,
            "ranking_provider": pool.ranking_provider,
            "ranking_metric": "h24_volume_usd",
        }

    def _candidate_from_address(self, address: str, rank: int) -> PoolCandidate:
        return PoolCandidate(
            address=address.lower(),
            network="bsc",
            dex_id="pancakeswap_v2",
            dex_name="PancakeSwap V2",
            base_token="",
            quote_token="",
            provider_rank=rank,
            volume_24h_usd=None,
            liquidity_usd=None,
            transactions_24h=None,
            observed_at="manual_selection",
            pair_name=None,
            ranking_provider="manual",
        )

    def _event(
        self,
        *,
        event_name: str,
        run_id: str,
        status: str,
        level: str = "info",
        **fields: Any,
    ) -> dict[str, Any]:
        payload = {
            "schema_version": "bsc_webui_event.v0.1",
            "timestamp": datetime.now(UTC).isoformat(),
            "event_name": event_name,
            "level": level,
            "service": "market-intent-inference",
            "module": "bsc_pipeline",
            "operation": event_name,
            "run_id": run_id,
            "trace_id": run_id,
            "status": status,
            "attempt": 1,
            "parent_id": None,
            "duration_ms": 0,
            "error_code": fields.get("error_code"),
            "retryable": False,
            "config_hash": "bsc-webui-config.v0.1",
            "code_version": "bsc-webui.v0.1",
            "data_version": "bsc-data.v0.1",
        }
        payload.update(fields)
        return payload

    def analyze(
        self,
        config: BSCAnalysisConfig | None = None,
        pool_addresses: list[str] | None = None,
    ) -> dict[str, Any]:
        config = config or BSCAnalysisConfig()
        run_id = f"bsc-{int(time.time())}-{uuid4().hex[:8]}"
        events: list[dict[str, Any]] = []
        summary: dict[str, Any] = {
            "run_id": run_id,
            "chain_id": 56,
            "config": {
                "top_k": config.top_k,
                "confirmation_lag": config.confirmation_lag,
                "lookback_blocks": config.lookback_blocks,
                "paper": config.paper,
                "mode": config.mode.value,
            },
            "source": "geckoterminal+bsc_rpc",
            "ranking_provider": "geckoterminal",
            "ranking_metric": "h24_volume_usd",
            "pools": [],
            "quality": "unknown",
            "reason_codes": [],
            "model_version": "none.v0",
            "feature_version": "bsc_microstructure.v0",
            "label_version": "none.v0",
        }
        try:
            pools = self.gecko.discover(top_k=config.top_k)
            mapping = self.gecko.require_pancake_mapping()
            summary["ranking_provider"] = self.gecko.last_source
            summary["mapping_source"] = mapping.source
            events.append(
                self._event(
                    event_name="bsc.discovery",
                    run_id=run_id,
                    status="succeeded",
                    pool_count=len(pools),
                    dex_id=mapping.provider_id,
                    mapping_source=mapping.source,
                    ranking_provider=self.gecko.last_source,
                )
            )
            if pool_addresses:
                wanted = [item.lower() for item in pool_addresses if item]
                by_addr = {pool.address: pool for pool in pools}
                selected = []
                for index, address in enumerate(wanted, start=1):
                    selected.append(
                        by_addr.get(address) or self._candidate_from_address(address, index)
                    )
            else:
                selected = list(pools)
            summary["rpc"] = self.rpc.safe_connection_summary()
            try:
                safe_block = self.rpc.safe_block(config.confirmation_lag)
                safe_time = self.rpc.block_timestamp(safe_block)
            except RPCError as probe_exc:
                summary["reason_codes"] = [probe_exc.reason]
                summary["quality"] = probe_exc.reason
                summary["error_detail"] = probe_exc.reason
                for pool in selected:
                    summary["pools"].append(
                        {
                            "pool": self._pool_dict(pool),
                            "rpc_verified": False,
                            "features": {},
                            "reason_codes": [probe_exc.reason],
                            "error_detail": probe_exc.reason,
                            "decision": {
                                "status": "abstain",
                                "reason_codes": [probe_exc.reason],
                                "paper": True,
                            },
                            "risk": {
                                field.value: RiskStatus.NOT_SUPPORTED.value for field in RiskField
                            },
                        }
                    )
                events.append(
                    self._event(
                        event_name="run.failed",
                        run_id=run_id,
                        status="failed",
                        level="error",
                        error_code=probe_exc.reason,
                    )
                )
                events.append(
                    self._event(
                        event_name="run.completed",
                        run_id=run_id,
                        status="degraded",
                        quality=summary["quality"],
                        reason_codes=summary.get("reason_codes", []),
                    )
                )
                summary["audit"] = self.store.write(run_id, summary, events)
                return summary
            decision_position = Position(safe_block, 2**31 - 1, 2**31 - 1)
            summary["decision_position"] = {
                "block_number": safe_block,
                "transaction_index": decision_position.transaction_index,
                "log_index": decision_position.log_index,
            }
            summary["decision_time"] = _iso(safe_time)
            for pool in selected:
                analysis: dict[str, Any] = {
                    "pool": self._pool_dict(pool),
                    "rpc_verified": False,
                    "features": {},
                    "reason_codes": [],
                    "risk": {field.value: RiskStatus.NOT_SUPPORTED.value for field in RiskField},
                }
                try:
                    verified = self.rpc.verify_pair(
                        pool.address,
                        dex_factory=mapping.factory,
                        dex_router=mapping.router,
                        state_block=safe_block,
                    )
                    analysis["rpc_verified"] = True
                    analysis["verification"] = {
                        "token0": verified["token0"],
                        "token1": verified["token1"],
                        "reserve0": verified["reserve0"],
                        "reserve1": verified["reserve1"],
                        "factory": verified["factory"],
                        "router": verified["router"],
                        "verified": True,
                    }
                    try:
                        logs = self.rpc.swap_logs(
                            pool.address,
                            from_block=max(0, safe_block - config.lookback_blocks),
                            to_block=safe_block,
                            decision_position=decision_position,
                        )
                        log_reason = None
                        if not self.rpc.last_logs_complete:
                            log_reason = self.rpc.last_logs_error or "source_unavailable"
                    except RPCError as log_exc:
                        logs = []
                        log_reason = log_exc.reason
                        analysis["error_detail"] = log_exc.reason
                    # Only timestamp-proven events may enter strict features/posteriors.
                    timed_logs = [
                        log
                        for log in logs
                        if log.event_time is not None
                        and safe_time is not None
                        and log.event_time <= safe_time
                    ]
                    cutoff = logs[-1].position if logs else Position(safe_block, 0, 0)
                    missing_safe_time = safe_time is None
                    # Always expose reserve-based features once the pair is verified.
                    analysis["features"] = _features(
                        verified,
                        timed_logs,
                        config.lookback_blocks,
                        failure_count=1.0 if log_reason else 0.0,
                    )
                    if log_reason is not None:
                        reason = log_reason
                        data_available = False
                    elif missing_safe_time or not timed_logs:
                        reason = "insufficient_data"
                        data_available = False
                    else:
                        reason = "abstain_no_labels"
                        data_available = True
                    analysis["reason_codes"] = [reason]
                    if missing_safe_time or (logs and not timed_logs):
                        analysis["reason_codes"] = list(
                            dict.fromkeys([*analysis["reason_codes"], "insufficient_data"])
                        )
                    analysis["recent_swaps"] = [
                        {
                            "block_number": log.position.block_number,
                            "transaction_index": log.position.transaction_index,
                            "log_index": log.position.log_index,
                            "amount0_in": log.amount0_in,
                            "amount1_in": log.amount1_in,
                            "amount0_out": log.amount0_out,
                            "amount1_out": log.amount1_out,
                            "event_time": _iso(log.event_time),
                        }
                        for log in logs[-5:]
                    ]
                    # Enrich display fields from on-chain verification when provider omitted them.
                    pool_view = analysis["pool"]
                    if not pool_view.get("base_token"):
                        pool_view["base_token"] = verified["token0"]
                    if not pool_view.get("quote_token"):
                        pool_view["quote_token"] = verified["token1"]
                    self._attach_prediction(
                        analysis,
                        safe_time,
                        decision_position,
                        cutoff,
                        config,
                        reason,
                        data_available,
                    )
                    summary.setdefault(
                        "data_cutoff",
                        {
                            "block_number": cutoff.block_number,
                            "transaction_index": cutoff.transaction_index,
                            "log_index": cutoff.log_index,
                        },
                    )
                    events.append(
                        self._event(
                            event_name="bsc.normalize",
                            run_id=run_id,
                            status="succeeded" if analysis["features"] else "degraded",
                            pool=pool.address,
                            swap_count=len(logs),
                            reason_codes=analysis["reason_codes"],
                        )
                    )
                except RPCError as exc:
                    analysis["reason_codes"] = [exc.reason]
                    analysis["error_detail"] = exc.reason
                    analysis["decision"] = {
                        "status": "abstain",
                        "reason_codes": [exc.reason],
                        "paper": True,
                    }
                    events.append(
                        self._event(
                            event_name="bsc.rpc_call",
                            run_id=run_id,
                            status="failed",
                            level="error",
                            pool=pool.address,
                            error_code=exc.reason,
                        )
                    )
                summary["pools"].append(analysis)
            summary["quality"] = (
                "derived"
                if any(
                    item.get("rpc_verified") and item.get("features") for item in summary["pools"]
                )
                else "insufficient_data"
            )
            events.append(
                self._event(
                    event_name="inference.prediction",
                    run_id=run_id,
                    status="degraded",
                    reason_codes=["abstain_no_labels"],
                )
            )
        except (ProviderError, RPCError) as exc:
            summary["reason_codes"] = [exc.reason]
            summary["quality"] = exc.reason
            events.append(
                self._event(
                    event_name="run.failed",
                    run_id=run_id,
                    status="failed",
                    level="error",
                    error_code=exc.reason,
                )
            )
        events.append(
            self._event(
                event_name="run.completed",
                run_id=run_id,
                status="succeeded" if summary["quality"] != "unknown" else "degraded",
                quality=summary["quality"],
                reason_codes=summary.get("reason_codes", []),
            )
        )
        summary["audit"] = self.store.write(run_id, summary, events)
        return summary

    def _attach_prediction(
        self,
        analysis: dict[str, Any],
        safe_time: datetime | None,
        decision_position: Position,
        cutoff: Position,
        config: BSCAnalysisConfig,
        reason: str,
        data_available: bool,
    ) -> None:
        if safe_time is None:
            analysis["prediction"] = {
                "abstain": True,
                "reason_codes": ["insufficient_data"],
                "model_version": "none.v0",
                "feature_version": "bsc_microstructure.v0",
                "label_version": "none.v0",
                "calibration_status": CalibrationStatus.UNCALIBRATED.value,
            }
            analysis["decision"] = {
                "status": "abstain",
                "reason_codes": ["insufficient_data"],
                "paper": True,
            }
            analysis["data_cutoff"] = {
                "block_number": cutoff.block_number,
                "transaction_index": cutoff.transaction_index,
                "log_index": cutoff.log_index,
            }
            analysis["decision_time"] = None
            analysis["horizon_end"] = None
            analysis["target_definition"] = "next_observed_action"
            return
        now = safe_time
        domain_decision = EventPosition(
            decision_position.block_number,
            decision_position.transaction_index,
            decision_position.log_index,
        )
        domain_cutoff = EventPosition(
            cutoff.block_number,
            cutoff.transaction_index,
            cutoff.log_index,
        )
        context = PredictionContext(
            now,
            now + timedelta(minutes=5),
            "next_observed_action",
            domain_decision,
            domain_cutoff,
        )
        key = (Role.UNKNOWN_MIXED.value, Action.UNKNOWN.value)
        result = build_prediction_result(
            context=context,
            role_posterior=_posterior("role", key, domain_cutoff, reason),
            action_posterior=_posterior("action", key, domain_cutoff, reason),
            intent_posterior=_posterior("intent", key, domain_cutoff, reason),
            model_version="none.v0",
            feature_version="bsc_microstructure.v0",
            label_version="none.v0",
        )
        risk = RiskSnapshot({field: RiskStatus.NOT_SUPPORTED for field in RiskField})
        constraints = ConstraintSet(
            config.paper,
            config.mode,
            0.0,
            0.0,
            0.0,
            "unknown",
            "unknown",
            0.0,
        )
        capability = VenueCapability(
            "pancakeswap_v2",
            56,
            True,
            False,
            False,
            False,
            frozenset({Action.BUY_QUOTE_TO_TOKEN}),
        )
        decision = decide(
            constraints=constraints,
            capability=capability,
            risk_snapshot=risk,
            requested_action=Action.UNKNOWN,
            event_data_available=True,
            insufficient_data=not data_available,
            posterior_calibrated=False,
        )
        analysis["prediction"] = {
            "abstain": result.abstain,
            "reason_codes": result.reason_codes,
            "model_version": result.model_version,
            "feature_version": result.feature_version,
            "label_version": result.label_version,
            "calibration_status": CalibrationStatus.UNCALIBRATED.value,
            "roles": list(Role),
            "actions": list(Action),
            "intents": list(LatentIntent),
        }
        analysis["decision"] = {
            "status": decision.status.value,
            "reason_codes": decision.reason_codes,
            "paper": decision.paper,
        }
        analysis["data_cutoff"] = {
            "block_number": cutoff.block_number,
            "transaction_index": cutoff.transaction_index,
            "log_index": cutoff.log_index,
        }
        analysis["decision_time"] = _iso(safe_time)
        analysis["horizon_end"] = _iso(context.horizon_end)
        analysis["target_definition"] = context.target_definition
