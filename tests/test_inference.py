import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from market_intent_inference.domain import (
    Action,
    ConstraintSet,
    DecisionStatus,
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
from market_intent_inference.inference import (
    build_prediction_result,
    conditional_posterior,
    decide,
    market_state_from_swap,
    normalize_swap_event,
    observed_fact_from_swap,
)

FIXTURE = Path(__file__).parent / "fixtures" / "amm_v2_events.json"


def all_risks(status: RiskStatus = RiskStatus.KNOWN_FALSE) -> RiskSnapshot:
    return RiskSnapshot({field: status for field in RiskField})


def constraints(**overrides):
    values = dict(
        paper=True,
        mode=VenueMode.SPOT_LONG_ONLY,
        capital=100.0,
        max_position=20.0,
        max_loss=5.0,
        fee_model="fixed",
        gas_model="fixed",
        slippage_bps=50.0,
    )
    values.update(overrides)
    return ConstraintSet(**values)


def capability(actions=frozenset({Action.BUY_QUOTE_TO_TOKEN})):
    return VenueCapability("pancakeswap_v2", 56, True, False, False, False, actions)


def test_fixture_normalizes_direction_and_excludes_failed_swap() -> None:
    rows = json.loads(FIXTURE.read_text())
    normalized = [normalize_swap_event(row) for row in rows]
    assert normalized[0].action is Action.BUY_QUOTE_TO_TOKEN
    assert normalized[1].action is Action.SELL_TOKEN_TO_QUOTE
    assert observed_fact_from_swap(normalized[2]) is None
    unconfirmed = dict(rows[0], confirmed=False)
    unconfirmed_event = normalize_swap_event(unconfirmed)
    assert market_state_from_swap(unconfirmed_event) is None
    assert observed_fact_from_swap(unconfirmed_event) is None
    with pytest.raises(ValueError):
        normalize_swap_event(dict(rows[0], confirmed="false"))


def test_conditional_frequency_uses_only_training_cutoff_and_laplace_one() -> None:
    records = [
        (
            Role.INFORMATION_DRIVEN,
            Action.BUY_QUOTE_TO_TOKEN,
            LatentIntent.ACCUMULATION,
            EventPosition(1, 0, 0),
        ),
        (
            Role.INFORMATION_DRIVEN,
            Action.BUY_QUOTE_TO_TOKEN,
            LatentIntent.ACCUMULATION,
            EventPosition(2, 0, 0),
        ),
        (
            Role.INFORMATION_DRIVEN,
            Action.BUY_QUOTE_TO_TOKEN,
            LatentIntent.DISTRIBUTION,
            EventPosition(3, 0, 0),
        ),
        (
            Role.INFORMATION_DRIVEN,
            Action.BUY_QUOTE_TO_TOKEN,
            LatentIntent.TAKE_PROFIT,
            EventPosition(4, 0, 0),
        ),
    ]
    posterior = conditional_posterior(
        records,
        role=Role.INFORMATION_DRIVEN,
        observed_action=Action.BUY_QUOTE_TO_TOKEN,
        training_cutoff=EventPosition(2, 0, 0),
        data_cutoff=EventPosition(2, 0, 0),
        decision_position=EventPosition(4, 0, 0),
    )
    assert posterior.alpha == 1.0
    assert posterior.condition_key == (
        Role.INFORMATION_DRIVEN.value,
        Action.BUY_QUOTE_TO_TOKEN.value,
    )
    assert posterior.categories == tuple(sorted(posterior.categories))
    assert posterior.probabilities[LatentIntent.ACCUMULATION.value] == pytest.approx(3 / 13)
    assert sum(posterior.probabilities.values()) == pytest.approx(1.0)


def test_empty_or_temporally_invalid_posterior_abstains_without_fake_uniform() -> None:
    abstain = conditional_posterior(
        [],
        role=Role.INFORMATION_DRIVEN,
        observed_action=Action.BUY_QUOTE_TO_TOKEN,
        training_cutoff=EventPosition(1, 0, 0),
        data_cutoff=EventPosition(1, 0, 0),
        decision_position=EventPosition(2, 0, 0),
    )
    assert abstain.abstain
    with pytest.raises(TypeError):
        abstain.probabilities["not_a_category"] = 1.0
    with pytest.raises(ValueError):
        conditional_posterior(
            [],
            role=Role.INFORMATION_DRIVEN,
            observed_action=Action.BUY_QUOTE_TO_TOKEN,
            training_cutoff=EventPosition(3, 0, 0),
            data_cutoff=EventPosition(2, 0, 0),
            decision_position=EventPosition(3, 0, 0),
        )


def test_build_prediction_result_returns_three_posterior_contract() -> None:
    key = (Role.INFORMATION_DRIVEN.value, Action.BUY_QUOTE_TO_TOKEN.value)
    role_categories = tuple(sorted(role.value for role in Role))
    action_categories = tuple(sorted(action.value for action in Action))
    intent_categories = tuple(sorted(intent.value for intent in LatentIntent))
    role_posterior = Posterior(
        "role",
        key,
        role_categories,
        {category: 1 / len(role_categories) for category in role_categories},
        EventPosition(1, 0, 0),
    )
    action_posterior = Posterior(
        "action",
        key,
        action_categories,
        {category: 1 / len(action_categories) for category in action_categories},
        EventPosition(1, 0, 0),
    )
    intent_posterior = Posterior(
        "intent",
        key,
        intent_categories,
        {category: 1 / len(intent_categories) for category in intent_categories},
        EventPosition(1, 0, 0),
    )
    result = build_prediction_result(
        context=PredictionContext(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
            "intent_window",
            EventPosition(2, 0, 0),
            EventPosition(1, 0, 0),
        ),
        role_posterior=role_posterior,
        action_posterior=action_posterior,
        intent_posterior=intent_posterior,
        model_version="model.v0",
        feature_version="features.v0",
        label_version="labels.v0",
    )
    assert result.role_posterior.variable == "role"
    assert result.action_posterior.variable == "action"
    assert result.intent_posterior.variable == "intent"


def test_decision_matrix_is_fail_closed() -> None:
    decision = decide(
        constraints=constraints(paper=False),
        capability=capability(),
        risk_snapshot=all_risks(),
        requested_action=Action.BUY_QUOTE_TO_TOKEN,
        event_data_available=True,
        posterior_calibrated=False,
    )
    assert decision.status is DecisionStatus.ABSTAIN
    assert decision.reason_codes == ("paper_only",)

    risk_blocked = decide(
        constraints=constraints(),
        capability=capability(),
        risk_snapshot=RiskSnapshot(
            {field: RiskStatus.KNOWN_FALSE for field in RiskField}
            | {RiskField.HONEYPOT_SCREEN: RiskStatus.KNOWN_TRUE}
        ),
        requested_action=Action.BUY_QUOTE_TO_TOKEN,
        event_data_available=True,
        posterior_calibrated=True,
    )
    assert risk_blocked.status is DecisionStatus.NO_TRADE
    assert risk_blocked.reason_codes == ("risk_blocked",)


def test_unsupported_short_and_unknown_risk_do_not_trade() -> None:
    short_decision = decide(
        constraints=constraints(mode=VenueMode.PERPETUAL_LONG_SHORT),
        capability=capability(),
        risk_snapshot=all_risks(),
        requested_action=Action.SELL_TOKEN_TO_QUOTE,
        event_data_available=True,
        posterior_calibrated=True,
    )
    assert short_decision.reason_codes == ("unsupported_venue",)

    unknown = decide(
        constraints=constraints(),
        capability=capability(),
        risk_snapshot=all_risks(RiskStatus.UNKNOWN),
        requested_action=Action.BUY_QUOTE_TO_TOKEN,
        event_data_available=True,
        posterior_calibrated=True,
    )
    assert unknown.reason_codes == ("risk_unknown",)
