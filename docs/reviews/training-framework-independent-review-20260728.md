# 训练框架独立审查

版本：`review-training-framework-20260728`  
审查对象：训练交接手册、文献综述、训练/仿真目录骨架、研究资源清单  
审查结论：**框架方向可继续，但暂不进入 PPO/CQL/IQL 或多主体 RL 实现。**

## 总结

当前项目已具备 WebUI、领域契约、BSC 只读数据链路、paper-only 安全边界、研究资源和训练分层文档，但还不具备“GitHub checkout 后直接启动训练”的条件。下一阶段应先实现一个固定小 panel 的最小闭环：

```text
ingest -> normalize -> build_labels -> fit_baseline -> evaluate
```

只有这个闭环能够在无未来泄漏、可复核 manifest 和固定 fixture 上运行，才应扩展到大规模数据、序列模型和 offline RL。

## P0：训练前必须解决

### P0-1：最小训练闭环尚未实现

当前 `data/`、`training/`、`simulator/` 和 `experiments/` 主要是目录契约与 README，尚无历史数据导入、canonical event、标签生成、切分、后验拟合、trajectory 构建和统一评估入口。因此本次交接应明确为“框架与研究资料交接”，不是“可运行训练交接”。

建议先实现固定小 panel 的四个命令或等价 API，并让条件频率基线在 fixture 上完整跑通；不要先写 RL。

### P0-2：标签必须分层

链上可硬验证的是 `observed_action`，而“散户/机构”“止损/诱多”等是行为或意图假设。第一版应改成：

```text
observed_action
behavioral_pattern
intent_hypothesis
```

每个非硬标签都必须记录 `target_definition`、`label_as_of`、`evidence_cutoff`、`label_rule_version`、`confidence`、`review_status`，并允许 unknown 与多标签。第一版主要报告：

```text
P(behavioral_pattern | observed_action, state, history)
```

不得把未来涨跌结果反向命名为真实意图。

### P0-3：市场日志不等于策略 trajectory

历史 Swap 只说明市场参与者发生了什么，不等于本项目策略采取了什么动作。offline RL 所需的 transition 必须明确来源：真实策略日志、规则行为策略、模拟策略或其他 synthetic 数据。synthetic trajectory 必须单独标记，不得伪装成真实反事实观测。

正式阶段应为：

```text
E0 数据集 -> E1 硬事件标签 -> E2 条件概率基线
-> E3 弱标签审查 -> E4 校准/OOD -> E5 历史确定性回放
-> E6 行为策略轨迹/OPE -> E7 offline RL
-> E8 CFMM 反事实仿真校准 -> E9 multi-agent/online RL
```

### P0-4：数据集必须固定为可复核 manifest

在选择 Dune、Bitquery 或 archive node 之前，不应写死“全 BSC”或用当前 Top 3 discovery 结果构造历史 universe。最小 manifest 必须包含：

```text
dataset_id, source, query_or_export_id, chain_id
block_start, block_end, canonical_block_hash, finality_policy
pool_universe_as_of, schema_version, raw_checksum
completeness, missing_reason, license_status
```

池 universe 需要保留死亡、撤池、极低流动性和后来归零的样本，避免幸存者偏差。

## P1：实现前应补齐

- 训练顺序必须区分历史确定性回放器和反事实 CFMM simulator；
- 评估加入 macro-F1/PR-AUC、多标签 micro/macro、block/bootstrap 区间、selective risk、FQE/WIS/DR、action support、CVaR、失败率和 gas 占比；
- 增加 `feature_as_of_block`、`label_window_start/end`、`universe_as_of`、`canonical_block_hash`、`finality_depth`、`reorg_status`；
- 明确 EOA/router/pair attribution、多跳路径、池内 Transfer、失败交易和 token tax 的优先级；
- 固定 CFMM 公式、手续费、decimals、税、滑点保护、deadline、多跳、Gas、revert、区块内顺序和确认延迟，并为其编写不变量测试；
- 提供训练环境锁定文件、PyTorch/CUDA 矩阵、数据引擎版本、算法实现 commit、GPU/磁盘估算、seed、checkpoint 和断点续训规范；
- 将策略输入契约固定为 `strategy_mode`、`venue`、`leverage_min/max`、`capital`、`position_limit`、`max_drawdown`、`holding_horizon`、`fee_budget` 和 `tax_policy`。

## 审查后的决策

本审查支持保留当前“监督式后验优先、offline RL 后置、多主体仿真最后”的总体方向，但不支持在数据契约和 E0 fixture 完成前实现 PPO、CQL/IQL 或产生交易收益结论。
