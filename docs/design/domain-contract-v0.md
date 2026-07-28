# 领域契约 v0

## 时间与事件可用性

- 所有时间字段都是带 UTC 时区的 `datetime`。
- `decision_time <= horizon_end`，`data_cutoff <= decision_time`。
- `event_position = (block_number, transaction_index, log_index)`，三者均为非负整数。
- 事件只有在 `confirmed=true` 且 `event_position <= decision_position` 时才能进入预测状态；同一区块中位置更晚的事件属于未来事件。
- `event_time` 不能晚于 `decision_time`；若链上时间粒度导致无法证明，状态为 `unknown` 并拒绝交易决策。
- `target_definition` 是非空字符串，第一切片只允许 `next_observed_action` 和 `intent_window`。

## 枚举

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

RiskStatus = known_true | known_false | unknown | not_supported
EvidenceQuality = observed_fact | derived | weak_label | unknown
CalibrationStatus = calibrated | uncalibrated | not_applicable
DecisionStatus = trade | no_trade | abstain
VenueMode = spot_long_only | spot_long_short | perpetual_long_short
```

`verified` 不属于角色或意图状态；可观察事实的 `EvidenceQuality` 使用 `observed_fact`。

## 缺失原因

`missing_reason` 只能为：`not_provided`、`source_unavailable`、`outside_retention`、`not_supported`、`redacted`、`quality_failed`。

## 领域对象

| 对象 | 必需字段与不变量 |
|---|---|
| `EventEnvelope` | `schema_version: str`、`chain_id: int`、`event_name: str`、`event_position`、`event_time`、`confirmed: bool`、`source: str`、`quality: EvidenceQuality`；位置和链 ID 非负 |
| `AMMV2SwapEvent` | envelope、`pool_address`、`token0`、`token1`、`amount0_in/out`、`amount1_in/out`、`reserve0/1_after`、`gas_price`、`gas_used`；金额和地址非空且非负 |
| `MarketState` | `decision_time`、`decision_position`、`data_cutoff`、`source`、`quality`、`missing_reason`、不可变元素映射；禁止未来事件 |
| `ObservedFact` | `kind`、`action: Action`、`observed: bool=True`、`evidence_quality=observed_fact`、事件位置；不得使用 latent intent 作为事实 |
| `Evidence` | `source`、`as_of`、`quality`、`missing_reason`、`summary`；summary 不保存秘密或隐藏推理 |
| `Posterior` | `variable: str`、`probabilities: Mapping[str,float]`、`training_cutoff`、`calibration_status`、`abstain: bool`、`reason_codes`；概率有限、非负、和为 1 ± 1e-9 |
| `VenueCapability` | `venue_id`、`chain_id`、`supports_spot_long_only`、`supports_short`、`supports_leverage`、`supports_write_execution`、`supported_actions`；MVP write 必须为 false |
| `RiskStatus` | 每个风险字段都带四态 status；`unknown`/`not_supported` 不是安全 |
| `ConstraintSet` | `paper: bool`、`mode: VenueMode`、`capital`、`max_position`、`max_loss`、`fee_model`、`gas_model`、`slippage_bps`；MVP `paper=True`、`mode=spot_long_only` |
| `Decision` | `status: DecisionStatus`、`action: Action | None`、`paper`、`expected_utility: float | None`、`reason_codes`、`posterior_ids`、`evidence_ids`；只有 `trade` 才允许 action 非空，且必须通过 capability 和 risk gate |

## 能力与风险拒绝矩阵

| 条件 | 结果 |
|---|---|
| `paper=False` | `abstain`, `paper_only` |
| `supports_write_execution=False` | 所有写链 action 为 `no_trade`, `unsupported_venue` |
| 请求 short 且 `supports_short=False` | `no_trade`, `unsupported_venue` |
| 请求 leverage 且 `supports_leverage=False` | `no_trade`, `unsupported_venue` |
| 任何关键风险为 `known_true` | `no_trade`, `risk_blocked` |
| 任何关键风险为 `unknown/not_supported` | `no_trade`, `risk_unknown` |
| 数据缺失或未来事件 | `abstain`, `insufficient_data` 或 `future_data` |
| 未校准 posterior | `abstain`, `uncalibrated` |
| 全部约束通过 | 仅允许 paper `trade` |

## 条件后验

输入必须显式包含 `training_cutoff`。训练样本只允许 `event_position <= training_cutoff`，预测样本不得进入计数。类别排序为 Unicode code-point ascending；Laplace 平滑参数 `alpha > 0` 且由配置固定。无样本或证据质量不足时返回 abstain，而不是均匀伪造概率。
