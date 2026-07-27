# Market Intent Inference 工程规则

## 项目范围

本项目是独立的科研工程混合项目，目标是建立市场微结构下的角色—操作—意图概率推理内核，并在后续以 BNB Smart Chain（BSC）上的 PancakeSwap V2-compatible constant-product pools 实现 paper-only meme coin MVP。

现有 `/Users/mashengyu/Desktop/quant research/coinman-arbitrage-bot` 是独立项目，属于受保护范围。本项目不得修改、导入、读取或共享其未批准代码、数据库、`.env`、虚拟环境、运行目录、凭据或 fixture。

## 不变量

1. 所有预测必须带 `decision_time`、`horizon_end`、`target_definition`、`event_position` 和 `data_cutoff`；特征必须满足 `as_of <= decision_time`。
2. 标签分为 `observed_fact`、`behavioral_hypothesis` 和 `latent_intent`；`verified` 只表示直接观察事实，不表示真实身份或真实意图。
3. 角色是行为假设，不是身份识别；意图是潜变量，必须支持多标签、未知和 abstain。
4. BSC MVP 只支持 chain ID 56、单一 PancakeSwap V2-compatible constant-product pool；V3、StableSwap、Infinity、聚合路由和 mempool 不属于 MVP。
5. 风险状态只允许 `known_true`、`known_false`、`unknown`、`not_supported`；未知不得当作安全。
6. MVP 不包含写链、执行、授权、资产转移、交易广播或私钥；`paper=false` 必须直接拒绝。
7. 回测必须是事件驱动，包含区块内顺序、确认延迟、滑点、手续费、Gas、token tax、失败交易和参与率上限。
8. token universe、标准化器、校准器和聚类器均必须按决策时点或训练集拟合，禁止未来信息泄漏。
9. 所有运行必须保存 run ID、配置/代码/数据版本、区块范围、模型/特征/标签版本和产物摘要。
10. 新元素聚类结果只能进入 candidate registry，经过稳定性、样本外和人工审查后才能正式化。

## 当前首个实现切片

只做纯本地、无网络、无钱包、无 LLM、无聚类的领域内核：

- 不可变领域对象：事件、AMM V2 Swap、市场状态、观察事实、证据、后验、约束和决策；
- 固定 fixture 的 V2 事件标准化与 token0/token1 方向处理；
- 条件频率 + 贝叶斯平滑的归一化后验；
- 数据不足、风险未知或能力不支持时的 abstain/no-trade；
- 单元测试、静态检查和确定性验证。

## 架构

```text
domain       纯领域对象、概率、标签、风险和策略契约
application  推理、聚类、校准、回测和实验编排
adapters     BSC/RPC/DEX/消息/存储适配器（当前切片不启用）
interfaces   CLI/API/报告（当前切片只保留可测试函数）
```

外部适配器必须声明能力、数据范围、完整性和缺失原因；失败进入 `parked/unknown`，禁止静默伪造成功。

## 工作流

设计、实现计划、TDD、独立审查、Research Wiki、Graphify、Harness Eval 和完成前新鲜验证均为必经流程。实现前先读取 `docs/design/PROJECT_PROMPT_DRAFT.md`、`docs/reviews/design-review-20260725.md` 和 `research-wiki/`。

默认工程配置与实验配置分离。敏感值只允许以变量名出现，绝不写入代码、日志、Wiki、测试产物或 Git。

## 项目命令

```zsh
python3 -m pytest -q
python3 -m compileall -q src tests
python3 -m ruff check src tests
python3 -m ruff format --check src tests
conda run -n codex-engineering research-wiki validate ./research-wiki
```

若某命令尚未安装或不适用，必须记录原因，不得伪造通过。
