from datetime import UTC, datetime

import pytest

from market_intent_inference.domain import (
    Action,
    ConstraintSet,
    Decision,
    DecisionStatus,
    EventEnvelope,
    EventPosition,
    EvidenceQuality,
    LatentIntent,
    ObservedFact,
    Posterior,
    PredictionContext,
    PredictionResult,
    RiskField,
    RiskSnapshot,
    RiskStatus,
    Role,
    VenueCapability,
    VenueMode,
)

UTC = UTC
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def pos(block: int, tx: int = 0, log: int = 0) -> EventPosition:
    return EventPosition(block, tx, log)


def test_event_position_and_context_are_temporally_ordered() -> None:
    context = PredictionContext(
        decision_time=NOW,
        horizon_end=datetime(2026, 1, 1, 0, 5, tzinfo=UTC),
        target_definition="next_observed_action",
        decision_position=pos(10),
        data_cutoff=pos(9),
    )
    assert context.data_cutoff <= context.decision_position
    assert context.schema_version == "prediction_context.v0.1"

    with pytest.raises(ValueError):
        PredictionContext(
            decision_time=NOW,
            horizon_end=datetime(2025, 12, 31, tzinfo=UTC),
            target_definition="next_observed_action",
            decision_position=pos(10),
            data_cutoff=pos(9),
        )

    with pytest.raises(ValueError):
        PredictionContext(
            decision_time=NOW,
            horizon_end=NOW,
            target_definition="next_observed_action",
            decision_position=pos(10),
            data_cutoff=pos(9),
            schema_version="wrong",
        )


def test_event_available_requires_confirmation_position_and_time() -> None:
    envelope = EventEnvelope(
        schema_version="event.v0.1",
        chain_id=56,
        event_name="Swap",
        event_position=pos(9),
        event_time=NOW,
        confirmed=True,
        source="fixture",
        quality=EvidenceQuality.OBSERVED_FACT,
    )
    assert envelope.is_available(decision_time=NOW, decision_position=pos(10))
    assert not envelope.is_available(decision_time=NOW, decision_position=pos(8))
    assert not EventEnvelope(
        schema_version="event.v0.1",
        chain_id=56,
        event_name="Swap",
        event_position=pos(9),
        event_time=None,
        confirmed=True,
        source="fixture",
        quality=EvidenceQuality.UNKNOWN,
    ).is_available(decision_time=NOW, decision_position=pos(10))


def test_domain_facts_and_decisions_fail_closed() -> None:
    with pytest.raises(ValueError):
        EventPosition(True, 0, 0)
    with pytest.raises(ValueError):
        ObservedFact(
            kind="observed_action",
            action=Action.BUY_QUOTE_TO_TOKEN,
            observed=False,
            evidence_quality=EvidenceQuality.DERIVED,
            event_position=pos(1),
        )
    with pytest.raises(ValueError):
        Decision(
            status=DecisionStatus.TRADE,
            action=Action.BUY_QUOTE_TO_TOKEN,
            paper=False,
            expected_utility=1.0,
            reason_codes=(),
            posterior_ids=(),
            evidence_ids=(),
        )


def test_prediction_result_keeps_three_posteriors_and_context() -> None:
    categories = tuple(sorted(intent.value for intent in LatentIntent))
    posterior = Posterior(
        variable="intent",
        condition_key=(Role.INFORMATION_DRIVEN.value, Action.BUY_QUOTE_TO_TOKEN.value),
        categories=categories,
        probabilities={category: 1 / len(categories) for category in categories},
        training_cutoff=pos(8),
        calibration_status="calibrated",
    )
    result = PredictionResult(
        context=PredictionContext(NOW, NOW, "intent_window", pos(10), pos(9)),
        role_posterior=posterior,
        action_posterior=posterior,
        intent_posterior=posterior,
        model_version="model.v0",
        feature_version="features.v0",
        label_version="labels.v0",
        abstain=False,
        reason_codes=(),
    )
    assert result.context.decision_position == pos(10)


def test_risk_snapshot_requires_all_nine_fields_and_four_state_semantics() -> None:
    statuses = {field: RiskStatus.KNOWN_FALSE for field in RiskField}
    snapshot = RiskSnapshot(statuses=statuses)
    assert len(snapshot.statuses) == 9
    assert snapshot.statuses[RiskField.SELLABILITY] is RiskStatus.KNOWN_FALSE
    with pytest.raises(ValueError):
        RiskSnapshot(statuses={RiskField.SELLABILITY: RiskStatus.KNOWN_FALSE})


def test_posterior_validates_categories_and_probabilities() -> None:
    posterior = Posterior(
        variable="intent",
        condition_key=(Role.INFORMATION_DRIVEN.value, Action.BUY_QUOTE_TO_TOKEN.value),
        categories=tuple(sorted(intent.value for intent in LatentIntent)),
        probabilities={
            category.value: (0.25 if category is LatentIntent.ACCUMULATION else 0.75 / 10)
            for category in LatentIntent
        },
        training_cutoff=pos(8),
        alpha=1.0,
        calibration_status="uncalibrated",
    )
    assert sum(posterior.probabilities.values()) == pytest.approx(1.0)
    with pytest.raises(TypeError):
        posterior.probabilities[LatentIntent.ACCUMULATION.value] = 0.5
    with pytest.raises(ValueError):
        Posterior(
            variable="intent",
            condition_key=(Role.INFORMATION_DRIVEN.value, Action.BUY_QUOTE_TO_TOKEN.value),
            categories=("a", "b"),
            probabilities={"a": 0.5, "b": 0.5},
            training_cutoff=pos(8),
        )
    with pytest.raises(ValueError):
        Posterior(
            variable="intent",
            condition_key=("x", "y"),
            categories=("b", "a"),
            probabilities={"b": 0.5, "a": 0.5},
            training_cutoff=pos(8),
            alpha=1.0,
            calibration_status="uncalibrated",
        )
    with pytest.raises(ValueError):
        Posterior(
            variable="other",
            condition_key=(Role.INFORMATION_DRIVEN.value, Action.BUY_QUOTE_TO_TOKEN.value),
            categories=tuple(sorted(intent.value for intent in LatentIntent)),
            probabilities={intent.value: 1 / len(LatentIntent) for intent in LatentIntent},
            training_cutoff=pos(8),
        )


def test_decision_and_capability_are_paper_only() -> None:
    capability = VenueCapability(
        venue_id="pancakeswap_v2",
        chain_id=56,
        supports_spot_long_only=True,
        supports_short=False,
        supports_leverage=False,
        supports_write_execution=False,
        supported_paper_actions=frozenset({Action.BUY_QUOTE_TO_TOKEN}),
    )
    constraints = ConstraintSet(
        paper=True,
        mode=VenueMode.SPOT_LONG_ONLY,
        capital=100.0,
        max_position=20.0,
        max_loss=5.0,
        fee_model="fixed",
        gas_model="fixed",
        slippage_bps=50.0,
    )
    decision = Decision(
        status=DecisionStatus.TRADE,
        action=Action.BUY_QUOTE_TO_TOKEN,
        paper=constraints.paper,
        expected_utility=0.1,
        reason_codes=(),
        posterior_ids=(),
        evidence_ids=(),
    )
    assert decision.paper and capability.supports_spot_long_only
    with pytest.raises(ValueError):
        VenueCapability("pancakeswap_v2", 56, "true", False, False, False, frozenset())
    with pytest.raises(ValueError):
        ConstraintSet(
            paper="false",
            mode=VenueMode.SPOT_LONG_ONLY,
            capital=100.0,
            max_position=20.0,
            max_loss=5.0,
            fee_model="fixed",
            gas_model="fixed",
            slippage_bps=50.0,
        )
