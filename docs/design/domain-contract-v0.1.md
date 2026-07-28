# 领域契约 v0.1（首个领域内核）

本文件是首个实现切片的唯一可执行契约；它只扩展角色—操作—意图的纯本地对象，不改变已批准的总体设计。

## 时间与 PredictionContext

所有时间字段都是带 UTC 时区的 `datetime`。`decision_time <= horizon_end`。`data_cutoff` 是 `EventPosition`，必须满足 `data_cutoff <= decision_position`；事件时间字段另行满足 `event_time <= decision_time`。

`EventPosition = (block_number: int, transaction_index: int, log_index: int)`，三者非负，按字典序比较。

`PredictionContext` 必须包含：

```text
schema_version = "prediction_context.v0.1"
decision_time: datetime
horizon_end: datetime
target_definition: "next_observed_action" | "intent_window"
decision_position: EventPosition
data_cutoff: EventPosition
```

事件可用当且仅当：`confirmed is True` 且 `event_position <= decision_position` 且 `event_time is not None` 且 `event_time <= decision_time`。事件时间缺失或无法证明时，状态为 unknown，不能进入 trade decision。未来标签只能进入 target/evaluation，不得进入 feature/state。

`PredictionResult` 必须包含 `context`、`role_posterior`、`action_posterior`、`intent_posterior`、`model_version`、`feature_version`、`label_version`、`abstain` 和 `reason_codes`。

## 固定枚举

```text
Role = lp_market_maker | information_driven | arbitrageur | momentum_speculator
       | mean_reversion | project_treasury | infrastructure | mev_candidate
       | forced_exit_candidate | unknown_mixed

Action = buy_quote_to_token | sell_token_to_quote | add_liquidity
         | remove_liquidity | transfer | no_observed_action | unknown

BehavioralHypothesis = momentum | mean_reversion | arbitrage | liquidity_management
                       | treasury_flow | mev_candidate | forced_exit_candidate | unknown

LatentIntent = accumulation | distribution | take_profit | stop_loss_or_exit
               | hedging | market_making_inventory | liquidity_migration
               | mev_extraction | inducement_manipulation_hypothesis
               | project_treasury_management | unknown_multi

RiskField = token_transfer_restriction | sellability | transfer_tax
            | owner_control | mint_authority | pause_authority
            | lp_withdrawal | holder_concentration | honeypot_screen

RiskStatus = known_true | known_false | unknown | not_supported
EvidenceQuality = observed_fact | derived | weak_label | unknown
CalibrationStatus = calibrated | uncalibrated | not_applicable
DecisionStatus = trade | no_trade | abstain
VenueMode = spot_long_only | spot_long_short | perpetual_long_short
```

第一切片的 `Posterior` 是 single-categorical。`BehavioralHypothesis`/`LatentIntent` 可在事实对象中保存 `frozenset` 多标签；若无法归并为单一类别，posterior 使用 `unknown_multi`，不把多标签强行压成单一真实意图。真正的 multilabel posterior 属于后续版本。

## 对象字段与不变量

| 对象 | 字段与约束 |
|---|---|
| `EventEnvelope` | `schema_version: str`、`chain_id: int`、`event_name: str`、`event_position: EventPosition`、`event_time: datetime | None`、`confirmed: bool`、`source: str`、`quality: EvidenceQuality`；链 ID、位置非负 |
| `AMMV2SwapEvent` | envelope、`pool_address: str`、`token0: str`、`token1: str`、四个 amount、`reserve0_after`、`reserve1_after`、`gas_price`、`gas_used`、`success: bool`、`revert_reason: str | None`；amount/reserve/gas 非负；`success=False` 时不产生状态改变的 observed action |
| `ObservedFact` | `kind: str`、`action: Action`、`observed: bool=True`、`evidence_quality=observed_fact`、event position；只能表达可观察事实 |
| `MarketState` | `context: PredictionContext`、`elements: Mapping[str,float|str|None]`、`source`、`quality`、`missing_reason`、`available_positions`；所有 position 满足事件可用规则 |
| `Evidence` | `source: str`、`as_of: datetime | None`、`quality`、`missing_reason`、`summary: str`；不保存秘密或隐藏推理 |
| `Posterior` | `variable: str`、`condition_key: tuple[str,...]`、`categories: tuple[str,...]`、`probabilities: Mapping[str,float]`、`training_cutoff: EventPosition`、`alpha=1.0`、`calibration_status`、`abstain`、`reason_codes`；类别按 code-point 排序，概率有限非负且和为 1 ± 1e-9 |
| `VenueCapability` | `venue_id`、`chain_id`、`supports_spot_long_only: bool`、`supports_short: bool`、`supports_leverage: bool`、`supports_write_execution: bool`、`supported_paper_actions: frozenset[Action]`；首切片 write 必须 false |
| `RiskSnapshot` | `statuses: Mapping[RiskField,RiskStatus]`；必须包含全部 `RiskField`，缺少字段构造失败 |
| `ConstraintSet` | `paper: bool`、`mode: VenueMode`、`capital: float`、`max_position: float`、`max_loss: float`、`fee_model: str`、`gas_model: str`、`slippage_bps: float`；MVP `paper=True`、`mode=spot_long_only` |
| `Decision` | `status`、`action: Action | None`、`paper`、`expected_utility: float | None`、`reason_codes: tuple[str,...]`、`posterior_ids`、`evidence_ids`；只有 trade 可有 action，且必须通过 capability/risk/calibration gates |
| `PredictionResult` | context、三个 posterior、model/feature/label version、abstain、reason codes；不得缺少 context 时间字段 |

## 缺失原因与计数

`missing_reason` 只能为：`not_provided`、`source_unavailable`、`outside_retention`、`not_supported`、`redacted`、`quality_failed`。

条件后验的 `condition_key=(role.value, observed_action.value)`。`training_cutoff` 是 `EventPosition`，必须同时满足 `training_cutoff <= data_cutoff <= decision_position`。训练样本只允许 `event_position <= training_cutoff`；预测样本、未来标签和同一区块位置更晚的事件不计数。第一切片 `alpha=1.0` 固定，类别全集由固定枚举按 Unicode code-point ascending 排序得到；无样本或质量不足时 `abstain=True`，不得返回伪造均匀概率。

## 拒绝矩阵与 reason-code 优先级

reason-code 优先级从高到低：`paper_only`、`future_data`、`insufficient_data`、`risk_blocked`、`risk_unknown`、`unsupported_venue`、`uncalibrated`。

| 条件 | 输出 |
|---|---|
| `paper=False` | `abstain`, `paper_only` |
| `event_time` 缺失/晚于决策时间/未来位置 | `abstain`, `future_data` |
| 关键数据缺失 | `abstain`, `insufficient_data` |
| 任一风险 `known_true` | `no_trade`, `risk_blocked` |
| 任一风险 `unknown/not_supported` | `no_trade`, `risk_unknown` |
| 请求 action 不在 `supported_paper_actions` | `no_trade`, `unsupported_venue` |
| short/leverage 模式能力为 false | `no_trade`, `unsupported_venue` |
| posterior `uncalibrated` | `abstain`, `uncalibrated` |
| 全部条件通过 | 仅允许 paper `trade` |

`supports_write_execution=False` 不阻止 paper simulation；它只表示不能发送真实写链交易。由于 `paper=False` 永远先被 `paper_only` 拒绝，首切片不会产生写链路径。
