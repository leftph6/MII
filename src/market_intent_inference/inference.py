"""Pure normalization, posterior, and fail-closed decision functions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from .domain import (
    Action,
    AMMV2SwapEvent,
    CalibrationStatus,
    ConstraintSet,
    Decision,
    DecisionStatus,
    EventEnvelope,
    EventPosition,
    EvidenceQuality,
    LatentIntent,
    MarketState,
    ObservedFact,
    Posterior,
    PredictionContext,
    PredictionResult,
    RiskSnapshot,
    RiskStatus,
    Role,
    VenueCapability,
    VenueMode,
)


@dataclass(frozen=True)
class NormalizedSwap:
    event: AMMV2SwapEvent
    action: Action


def _strict_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _position(raw: list[int] | tuple[int, int, int]) -> EventPosition:
    if len(raw) != 3:
        raise ValueError("event_position must contain block, transaction, and log index")
    return EventPosition(*raw)


def normalize_swap_event(raw: dict) -> NormalizedSwap:
    envelope = EventEnvelope(
        schema_version=raw["schema_version"],
        chain_id=int(raw["chain_id"]),
        event_name=raw["event_name"],
        event_position=_position(raw["event_position"]),
        event_time=datetime.fromisoformat(raw["event_time"]) if raw.get("event_time") else None,
        confirmed=_strict_bool(raw["confirmed"], "confirmed"),
        source=raw["source"],
        quality=EvidenceQuality(raw["quality"]),
    )
    event = AMMV2SwapEvent(
        envelope=envelope,
        pool_address=raw["pool"],
        token0=raw["token0"],
        token1=raw["token1"],
        amount0_in=float(raw["amount0_in"]),
        amount1_in=float(raw["amount1_in"]),
        amount0_out=float(raw["amount0_out"]),
        amount1_out=float(raw["amount1_out"]),
        reserve0_after=float(raw["reserve0_after"]),
        reserve1_after=float(raw["reserve1_after"]),
        gas_price=float(raw["gas_price"]),
        gas_used=int(raw["gas_used"]),
        success=_strict_bool(raw["success"], "success"),
        revert_reason=raw.get("revert_reason"),
    )
    if not event.success:
        action = Action.UNKNOWN
    elif event.amount0_in > 0 and event.amount1_out > 0:
        action = Action.BUY_QUOTE_TO_TOKEN
    elif event.amount1_in > 0 and event.amount0_out > 0:
        action = Action.SELL_TOKEN_TO_QUOTE
    else:
        action = Action.UNKNOWN
    return NormalizedSwap(event=event, action=action)


def market_state_from_swap(normalized: NormalizedSwap) -> MarketState | None:
    event = normalized.event
    if not event.success or not event.envelope.confirmed or event.envelope.event_time is None:
        return None
    context = PredictionContext(
        decision_time=event.envelope.event_time,
        horizon_end=event.envelope.event_time,
        target_definition="next_observed_action",
        decision_position=event.envelope.event_position,
        data_cutoff=event.envelope.event_position,
    )
    return MarketState(
        context=context,
        elements={
            "reserve0": event.reserve0_after,
            "reserve1": event.reserve1_after,
            "pool_address": event.pool_address,
        },
        source=event.envelope.source,
        quality=event.envelope.quality,
        missing_reason=None,
        available_positions=(event.envelope.event_position,),
    )


def observed_fact_from_swap(normalized: NormalizedSwap) -> ObservedFact | None:
    event = normalized.event
    if not event.success or not event.envelope.confirmed or normalized.action is Action.UNKNOWN:
        return None
    return ObservedFact(
        kind="observed_action",
        action=normalized.action,
        observed=True,
        evidence_quality=event.envelope.quality,
        event_position=event.envelope.event_position,
    )


def conditional_posterior(
    records: Iterable[
        tuple[Role, Action, LatentIntent, EventPosition]
        | tuple[Role, Action, LatentIntent, EventPosition, EvidenceQuality]
    ],
    *,
    role: Role,
    observed_action: Action,
    training_cutoff: EventPosition,
    data_cutoff: EventPosition,
    decision_position: EventPosition,
) -> Posterior:
    if training_cutoff > data_cutoff:
        raise ValueError("training_cutoff must be <= data_cutoff")
    if data_cutoff > decision_position:
        raise ValueError("data_cutoff must be <= decision_position")
    categories = tuple(sorted(intent.value for intent in LatentIntent))
    counts = {category: 0 for category in categories}
    total = 0
    for record in records:
        if len(record) == 4:
            record_role, record_action, intent, record_position = record
            quality = EvidenceQuality.OBSERVED_FACT
        elif len(record) == 5:
            record_role, record_action, intent, record_position, quality = record
        else:
            raise ValueError("posterior records must contain four or five fields")
        if (
            quality is not EvidenceQuality.UNKNOWN
            and record_position <= training_cutoff
            and record_role is role
            and record_action is observed_action
        ):
            counts[intent.value] += 1
            total += 1
    if total == 0:
        return Posterior(
            variable="intent",
            condition_key=(role.value, observed_action.value),
            categories=(),
            probabilities={},
            training_cutoff=training_cutoff,
            calibration_status=CalibrationStatus.UNCALIBRATED,
            abstain=True,
            reason_codes=("insufficient_data",),
        )
    denominator = total + len(categories)
    probabilities = {category: (counts[category] + 1.0) / denominator for category in categories}
    return Posterior(
        variable="intent",
        condition_key=(role.value, observed_action.value),
        categories=categories,
        probabilities=probabilities,
        training_cutoff=training_cutoff,
        alpha=1.0,
        calibration_status=CalibrationStatus.UNCALIBRATED,
    )


def build_prediction_result(
    *,
    context: PredictionContext,
    role_posterior: Posterior,
    action_posterior: Posterior,
    intent_posterior: Posterior,
    model_version: str,
    feature_version: str,
    label_version: str,
) -> PredictionResult:
    posteriors = (role_posterior, action_posterior, intent_posterior)
    expected_variables = ("role", "action", "intent")
    if tuple(posterior.variable for posterior in posteriors) != expected_variables:
        raise ValueError("prediction posteriors must be role, action, and intent in order")
    if any(posterior.training_cutoff > context.data_cutoff for posterior in posteriors):
        raise ValueError("posterior training cutoff must be <= context data cutoff")
    reason_codes = tuple(
        dict.fromkeys(code for posterior in posteriors for code in posterior.reason_codes)
    )
    return PredictionResult(
        context=context,
        role_posterior=role_posterior,
        action_posterior=action_posterior,
        intent_posterior=intent_posterior,
        model_version=model_version,
        feature_version=feature_version,
        label_version=label_version,
        abstain=any(posterior.abstain for posterior in posteriors),
        reason_codes=reason_codes,
    )


def decide(
    *,
    constraints: ConstraintSet,
    capability: VenueCapability,
    risk_snapshot: RiskSnapshot,
    requested_action: Action,
    event_data_available: bool,
    posterior_calibrated: bool,
    future_data: bool = False,
    insufficient_data: bool = False,
) -> Decision:
    """Apply the fixed fail-closed decision matrix in priority order."""
    if not constraints.paper:
        return Decision(DecisionStatus.ABSTAIN, None, False, None, ("paper_only",), (), ())
    if future_data or not event_data_available:
        return Decision(DecisionStatus.ABSTAIN, None, True, None, ("future_data",), (), ())
    if insufficient_data:
        return Decision(DecisionStatus.ABSTAIN, None, True, None, ("insufficient_data",), (), ())
    if any(status is RiskStatus.KNOWN_TRUE for status in risk_snapshot.statuses.values()):
        return Decision(DecisionStatus.NO_TRADE, None, True, None, ("risk_blocked",), (), ())
    if any(
        status in {RiskStatus.UNKNOWN, RiskStatus.NOT_SUPPORTED}
        for status in risk_snapshot.statuses.values()
    ):
        return Decision(DecisionStatus.NO_TRADE, None, True, None, ("risk_unknown",), (), ())
    supported_mode = (
        constraints.mode is VenueMode.SPOT_LONG_ONLY and capability.supports_spot_long_only
    )
    if requested_action not in capability.supported_paper_actions or not supported_mode:
        return Decision(DecisionStatus.NO_TRADE, None, True, None, ("unsupported_venue",), (), ())
    if not posterior_calibrated:
        return Decision(DecisionStatus.ABSTAIN, None, True, None, ("uncalibrated",), (), ())
    return Decision(DecisionStatus.TRADE, requested_action, True, 0.0, (), (), ())
