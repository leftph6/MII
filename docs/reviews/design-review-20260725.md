# 独立设计审查：Market Intent Inference

- 审查日期：2026-07-25
- 审查对象：`docs/design/PROJECT_PROMPT_DRAFT.md`
- 审查范围：需求覆盖、概率/标签可识别性、CLOB/AMM 边界、BSC MVP、回测泄漏、安全和现有项目隔离
- 审查结论：有条件通过

## 审查意见

方向覆盖用户要求：空间元素集合、聚类发现候选新元素、条件概率、微结构 Alpha 和约束下的理性决策均已包含。

进入完整 BSC MVP 前必须补齐：预测时点/窗口/目标变量、观察事实与行为假设/潜在意图分层、单一 DEX 和 V2-compatible 池型、数据源能力声明、风险字段的 unknown/not_supported 语义、事件驱动回测成交模型、点时 token universe、同区块后续事件排除、训练拟合隔离和代码级只读安全。

## 已处理修改

草案已新增或收紧：

1. `decision_time`、`horizon_end`、`target_definition`、`event_position` 和 `data_cutoff`；
2. `observed_fact`、`behavioral_hypothesis`、`latent_intent` 三层标签；
3. `hold` 改为库存状态或 `no_observed_action`；
4. BSC MVP 限定为 chain ID 56、PancakeSwap V2-compatible constant-product pools；
5. `known_true/known_false/unknown/not_supported` 风险语义；
6. 数据源能力、缺失与 parked/unknown 语义；
7. 点时 universe、同区块顺序、purge/embargo、拟合隔离和成本后回测；
8. MVP 禁止写链、广播、授权、资产转移和 `paper=false`。

## 开始实现的条件

仅允许从纯本地、无网络、无钱包、无 LLM、无聚类的领域内核切片开始。该切片不得引入任何真实执行能力，也不得依赖现有 Coinman 项目。
