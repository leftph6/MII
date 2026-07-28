"""Small, strict domain model for the first market-intent inference slice."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from math import isfinite
from types import MappingProxyType


class _ValueEnum(StrEnum):
    def __str__(self) -> str:
        return self.value


class Role(_ValueEnum):
    LP_MARKET_MAKER = "lp_market_maker"
    INFORMATION_DRIVEN = "information_driven"
    ARBITRAGEUR = "arbitrageur"
    MOMENTUM_SPECULATOR = "momentum_speculator"
    MEAN_REVERSION = "mean_reversion"
    PROJECT_TREASURY = "project_treasury"
    INFRASTRUCTURE = "infrastructure"
    MEV_CANDIDATE = "mev_candidate"
    FORCED_EXIT_CANDIDATE = "forced_exit_candidate"
    UNKNOWN_MIXED = "unknown_mixed"


class Action(_ValueEnum):
    BUY_QUOTE_TO_TOKEN = "buy_quote_to_token"
    SELL_TOKEN_TO_QUOTE = "sell_token_to_quote"
    ADD_LIQUIDITY = "add_liquidity"
    REMOVE_LIQUIDITY = "remove_liquidity"
    TRANSFER = "transfer"
    NO_OBSERVED_ACTION = "no_observed_action"
    UNKNOWN = "unknown"


class BehavioralHypothesis(_ValueEnum):
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    LIQUIDITY_MANAGEMENT = "liquidity_management"
    TREASURY_FLOW = "treasury_flow"
    MEV_CANDIDATE = "mev_candidate"
    FORCED_EXIT_CANDIDATE = "forced_exit_candidate"
    UNKNOWN = "unknown"


class LatentIntent(_ValueEnum):
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    TAKE_PROFIT = "take_profit"
    STOP_LOSS_OR_EXIT = "stop_loss_or_exit"
    HEDGING = "hedging"
    MARKET_MAKING_INVENTORY = "market_making_inventory"
    LIQUIDITY_MIGRATION = "liquidity_migration"
    MEV_EXTRACTION = "mev_extraction"
    INDUCEMENT_MANIPULATION_HYPOTHESIS = "inducement_manipulation_hypothesis"
    PROJECT_TREASURY_MANAGEMENT = "project_treasury_management"
    UNKNOWN_MULTI = "unknown_multi"


class RiskField(_ValueEnum):
    TOKEN_TRANSFER_RESTRICTION = "token_transfer_restriction"
    SELLABILITY = "sellability"
    TRANSFER_TAX = "transfer_tax"
    OWNER_CONTROL = "owner_control"
    MINT_AUTHORITY = "mint_authority"
    PAUSE_AUTHORITY = "pause_authority"
    LP_WITHDRAWAL = "lp_withdrawal"
    HOLDER_CONCENTRATION = "holder_concentration"
    HONEYPOT_SCREEN = "honeypot_screen"


class RiskStatus(_ValueEnum):
    KNOWN_TRUE = "known_true"
    KNOWN_FALSE = "known_false"
    UNKNOWN = "unknown"
    NOT_SUPPORTED = "not_supported"


class EvidenceQuality(_ValueEnum):
    OBSERVED_FACT = "observed_fact"
    DERIVED = "derived"
    WEAK_LABEL = "weak_label"
    UNKNOWN = "unknown"


class CalibrationStatus(_ValueEnum):
    CALIBRATED = "calibrated"
    UNCALIBRATED = "uncalibrated"
    NOT_APPLICABLE = "not_applicable"


class DecisionStatus(_ValueEnum):
    TRADE = "trade"
    NO_TRADE = "no_trade"
    ABSTAIN = "abstain"


class VenueMode(_ValueEnum):
    SPOT_LONG_ONLY = "spot_long_only"
    SPOT_LONG_SHORT = "spot_long_short"
    PERPETUAL_LONG_SHORT = "perpetual_long_short"


MISSING_REASONS = frozenset(
    {
        "not_provided",
        "source_unavailable",
        "outside_retention",
        "not_supported",
        "redacted",
        "quality_failed",
    }
)


def _utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True, order=True)
class EventPosition:
    block_number: int
    transaction_index: int
    log_index: int

    def __post_init__(self) -> None:
        if any(
            type(v) is not int or v < 0
            for v in (self.block_number, self.transaction_index, self.log_index)
        ):
            raise ValueError("event position fields must be non-negative integers")


@dataclass(frozen=True)
class PredictionContext:
    decision_time: datetime
    horizon_end: datetime
    target_definition: str
    decision_position: EventPosition
    data_cutoff: EventPosition
    schema_version: str = "prediction_context.v0.1"

    def __post_init__(self) -> None:
        decision = _utc(self.decision_time, "decision_time")
        horizon = _utc(self.horizon_end, "horizon_end")
        object.__setattr__(self, "decision_time", decision)
        object.__setattr__(self, "horizon_end", horizon)
        if self.schema_version != "prediction_context.v0.1":
            raise ValueError("unsupported PredictionContext schema_version")
        if horizon < decision:
            raise ValueError("horizon_end must be >= decision_time")
        if self.target_definition not in {"next_observed_action", "intent_window"}:
            raise ValueError("unsupported target_definition")
        if self.data_cutoff > self.decision_position:
            raise ValueError("data_cutoff must be <= decision_position")


@dataclass(frozen=True)
class EventEnvelope:
    schema_version: str
    chain_id: int
    event_name: str
    event_position: EventPosition
    event_time: datetime | None
    confirmed: bool
    source: str
    quality: EvidenceQuality

    def __post_init__(self) -> None:
        if self.chain_id <= 0:
            raise ValueError("chain_id must be positive")
        if type(self.confirmed) is not bool:
            raise ValueError("confirmed must be a boolean")
        if self.event_time is not None:
            object.__setattr__(self, "event_time", _utc(self.event_time, "event_time"))

    def is_available(self, *, decision_time: datetime, decision_position: EventPosition) -> bool:
        if not self.confirmed or self.event_time is None:
            return False
        return self.event_position <= decision_position and self.event_time <= _utc(
            decision_time, "decision_time"
        )


@dataclass(frozen=True)
class AMMV2SwapEvent:
    envelope: EventEnvelope
    pool_address: str
    token0: str
    token1: str
    amount0_in: float
    amount1_in: float
    amount0_out: float
    amount1_out: float
    reserve0_after: float
    reserve1_after: float
    gas_price: float
    gas_used: int
    success: bool
    revert_reason: str | None = None

    def __post_init__(self) -> None:
        values = (
            self.amount0_in,
            self.amount1_in,
            self.amount0_out,
            self.amount1_out,
            self.reserve0_after,
            self.reserve1_after,
            self.gas_price,
        )
        if any(not isfinite(value) or value < 0 for value in values) or self.gas_used < 0:
            raise ValueError("amount, reserve, gas, and gas_used values must be non-negative")
        if type(self.success) is not bool:
            raise ValueError("success must be a boolean")


@dataclass(frozen=True)
class MarketState:
    context: PredictionContext
    elements: Mapping[str, float | str | None]
    source: str
    quality: EvidenceQuality
    missing_reason: str | None
    available_positions: tuple[EventPosition, ...]

    def __post_init__(self) -> None:
        if self.missing_reason not in MISSING_REASONS | {None}:
            raise ValueError("invalid missing_reason")
        if any(position > self.context.decision_position for position in self.available_positions):
            raise ValueError("available positions must not be future positions")


@dataclass(frozen=True)
class ObservedFact:
    kind: str
    action: Action
    event_position: EventPosition
    observed: bool = True
    evidence_quality: EvidenceQuality = EvidenceQuality.OBSERVED_FACT

    def __post_init__(self) -> None:
        if not self.observed or self.evidence_quality is not EvidenceQuality.OBSERVED_FACT:
            raise ValueError("ObservedFact must be an observed fact")


@dataclass(frozen=True)
class Evidence:
    source: str
    as_of: datetime | None
    quality: EvidenceQuality
    missing_reason: str | None
    summary: str

    def __post_init__(self) -> None:
        if self.as_of is not None:
            object.__setattr__(self, "as_of", _utc(self.as_of, "as_of"))
        if self.missing_reason not in MISSING_REASONS | {None}:
            raise ValueError("invalid missing_reason")


@dataclass(frozen=True)
class RiskSnapshot:
    statuses: Mapping[RiskField, RiskStatus]

    def __post_init__(self) -> None:
        expected = set(RiskField)
        if set(self.statuses) != expected:
            raise ValueError("RiskSnapshot must contain exactly all RiskField values")
        if any(
            not isinstance(k, RiskField) or not isinstance(v, RiskStatus)
            for k, v in self.statuses.items()
        ):
            raise ValueError("invalid risk status mapping")
        object.__setattr__(self, "statuses", MappingProxyType(dict(self.statuses)))


@dataclass(frozen=True)
class Posterior:
    variable: str
    condition_key: tuple[str, ...]
    categories: tuple[str, ...]
    probabilities: Mapping[str, float]
    training_cutoff: EventPosition
    alpha: float = 1.0
    calibration_status: CalibrationStatus | str = CalibrationStatus.UNCALIBRATED
    abstain: bool = False
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.condition_key) != 2:
            raise ValueError("condition_key must contain role and observed action")
        if self.condition_key[0] not in {role.value for role in Role}:
            raise ValueError("condition_key role is outside the fixed enum")
        if self.condition_key[1] not in {action.value for action in Action}:
            raise ValueError("condition_key action is outside the fixed enum")
        category_sets = {
            "role": {role.value for role in Role},
            "action": {action.value for action in Action},
            "intent": {intent.value for intent in LatentIntent},
        }
        if self.variable not in category_sets:
            raise ValueError("posterior variable is outside the fixed first-slice set")
        if self.abstain:
            if self.categories or self.probabilities or not self.reason_codes:
                raise ValueError("abstain posterior must be empty and carry reason_codes")
            object.__setattr__(self, "probabilities", MappingProxyType({}))
            return
        allowed_categories = category_sets.get(self.variable)
        if allowed_categories is not None and set(self.categories) != allowed_categories:
            raise ValueError("posterior categories are outside the fixed enum")
        if len(self.categories) == 0 or len(self.categories) != len(self.probabilities):
            raise ValueError(
                "posterior categories and probabilities must have equal nonzero length"
            )
        if tuple(self.categories) != tuple(sorted(self.categories)) or len(
            set(self.categories)
        ) != len(self.categories):
            raise ValueError("posterior categories must be unique and Unicode-sorted")
        if self.alpha != 1.0 or not isfinite(self.alpha) or self.alpha <= 0:
            raise ValueError("first-slice alpha must be exactly 1.0")
        if set(self.probabilities) != set(self.categories):
            raise ValueError("posterior probabilities must cover all categories")
        values = tuple(self.probabilities[category] for category in self.categories)
        if any(not isfinite(p) or p < 0 for p in values) or abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("posterior probabilities must be finite, non-negative, and sum to one")
        if isinstance(self.calibration_status, str):
            object.__setattr__(
                self, "calibration_status", CalibrationStatus(self.calibration_status)
            )
        object.__setattr__(self, "probabilities", MappingProxyType(dict(self.probabilities)))

    @property
    def calibration(self) -> CalibrationStatus:
        return self.calibration_status


@dataclass(frozen=True)
class VenueCapability:
    venue_id: str
    chain_id: int
    supports_spot_long_only: bool
    supports_short: bool
    supports_leverage: bool
    supports_write_execution: bool
    supported_paper_actions: frozenset[Action]

    def __post_init__(self) -> None:
        if self.chain_id <= 0:
            raise ValueError("chain_id must be positive")
        bool_fields = (
            self.supports_spot_long_only,
            self.supports_short,
            self.supports_leverage,
            self.supports_write_execution,
        )
        if any(type(value) is not bool for value in bool_fields):
            raise ValueError("venue capability flags must be booleans")
        if self.supports_write_execution:
            raise ValueError("the first slice is paper-only and cannot support write execution")


@dataclass(frozen=True)
class ConstraintSet:
    paper: bool
    mode: VenueMode
    capital: float
    max_position: float
    max_loss: float
    fee_model: str
    gas_model: str
    slippage_bps: float

    def __post_init__(self) -> None:
        if type(self.paper) is not bool:
            raise ValueError("paper must be a boolean")
        values = (self.capital, self.max_position, self.max_loss, self.slippage_bps)
        if any(not isfinite(value) or value < 0 for value in values):
            raise ValueError("constraint values must be non-negative")


@dataclass(frozen=True)
class Decision:
    status: DecisionStatus
    action: Action | None
    paper: bool
    expected_utility: float | None
    reason_codes: tuple[str, ...]
    posterior_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.paper) is not bool:
            raise ValueError("paper must be a boolean")
        if not self.paper and self.status is DecisionStatus.TRADE:
            raise ValueError("paper=False cannot produce a trade decision")
        if self.status is DecisionStatus.TRADE and self.action is None:
            raise ValueError("trade decisions require an action")
        if self.status is not DecisionStatus.TRADE and self.action is not None:
            raise ValueError("non-trade decisions cannot carry an action")


@dataclass(frozen=True)
class PredictionResult:
    context: PredictionContext
    role_posterior: Posterior
    action_posterior: Posterior
    intent_posterior: Posterior
    model_version: str
    feature_version: str
    label_version: str
    abstain: bool
    reason_codes: tuple[str, ...]
