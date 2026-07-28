# Market Intent Inference 训练与服务器实验交接手册

版本：`handoff-20260728`  
项目：`market-intent-inference`  
适用链：BNB Smart Chain，chain ID `56`  
当前模式：paper-only、只读、无钱包、无写链、无交易广播

## 0. 交接结论

当前项目已经完成：

- venue-neutral 领域契约：市场状态、事件、观察事实、角色、操作、意图、风险、后验和决策；
- BSC PancakeSwap V2-compatible WebUI MVP；
- GeckoTerminal Top-volume discovery；
- BSC RPC 只读核验、储备读取、Swap 日志读取和 cutoff-safe 特征；
- `abstain/no_trade` fail-closed 决策；
- Graphify 代码关系图、Run 审计、Harness Eval 和 Research Wiki；
- 面向训练阶段的数据湖、训练、仿真和实验目录骨架；
- 论文 PDF、数据源和工具文档资源目录；
- 文献综述 PDF。

当前**尚未完成**：

- BSC 历史 gold dataset；
- 角色和潜在意图的高质量标签；
- BSC live pipeline 的数值条件后验；
- 概率校准、OOD 检测和样本外回测；
- AMM 事件驱动反事实仿真器；
- offline RL 策略训练；
- 多主体 RL/ABM 机制实验。

独立审查已确认：本手册是“框架与研究资料交接”，不是“checkout 后即可训练”的完成声明。审查记录见 [`docs/reviews/training-framework-independent-review-20260728.md`](../reviews/training-framework-independent-review-20260728.md)。

本交接建议强化学习作为“决策层”而不是“第一层意图识别器”。第一条服务器实验链应为：

```text
E0 数据集
 -> E1 硬事件标签
 -> E2 条件概率基线
 -> E3 弱标签审查
 -> E4 校准与 OOD
 -> E5 历史确定性回放
 -> E6 行为策略轨迹与 OPE
 -> E7 offline RL
 -> E8 CFMM 反事实仿真校准
 -> E9 multi-agent / online RL
```

## 1. 当前项目事实基线

### 1.1 已有可复用模块

| 层 | 当前文件/能力 | 服务器实验如何使用 |
|---|---|---|
| 领域 | `src/market_intent_inference/domain.py` | 作为所有事件、后验、风险、决策的 schema 基线，不要在训练脚本内重新定义一套字段。 |
| 推理 | `src/market_intent_inference/inference.py` | 已有条件频率 + `alpha=1.0` 平滑的通用 posterior；当前 live BSC 尚未接入训练记录。 |
| BSC 编排 | `src/market_intent_inference/application/bsc_pipeline.py` | 复用 safe block、data cutoff、Swap 特征和 reason code 语义。 |
| RPC | `src/market_intent_inference/adapters/bsc_rpc.py` | 复用只读 RPC allowlist、事件位置和日志降级语义；不把免费 RPC 当作历史数据仓库。 |
| Discovery | `src/market_intent_inference/adapters/geckoterminal.py` | 只用于候选池发现/排序和展示，不把 provider snapshot 直接当训练事实。 |
| WebUI | `web/`、`scripts/run_webui.py` | 用于数据链路 smoke 和人工检查，不是训练入口。 |
| 审计 | `src/market_intent_inference/application/run_store.py` | 复用 run ID、脱敏 JSON/JSONL 和结构化事件字段。 |

### 1.2 当前 BSC 推理为什么没有数值概率

当前 `_attach_prediction()` 对 role/action/intent 使用空 posterior 并标记 `abstain`。这是有意的安全行为：当前没有训练标签和校准模型，系统不会输出伪造的均匀概率。通用 `conditional_posterior()` 已经可以计算：

\[
P(Z=z\mid R=r,A=a,D)=
\frac{N(z,r,a;D)+\alpha}{N(r,a;D)+K\alpha},
\quad \alpha=1
\]

但服务器端必须先提供带 cutoff 的训练记录，再将其接入 BSC pipeline。接入前不得把 `roles/actions/intents` 枚举列表解释为概率。

## 2. 推荐训练系统架构

```text
                    ┌──────────────────────────────┐
                    │  BSC raw / indexed sources    │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  Bronze: chain/tx/log/receipt │
                    └──────────────┬───────────────┘
                                   │ deterministic parsers
                    ┌──────────────▼───────────────┐
                    │ Silver: canonical event lake  │
                    │ position/time/source/quality  │
                    └──────────────┬───────────────┘
                                   │ time-safe feature jobs
                    ┌──────────────▼───────────────┐
                    │ Gold: state + actions + labels │
                    └───────┬──────────────┬────────┘
                            │              │
              ┌─────────────▼──────┐  ┌────▼─────────────────┐
              │ conditional model  │  │ event-driven replay  │
              │ role/action/intent │  │ AMM execution model  │
              └─────────────┬──────┘  └────┬─────────────────┘
                            │              │
              ┌─────────────▼──────┐  ┌────▼─────────────────┐
              │ calibration / OOD  │  │ offline RL / policy  │
              └─────────────┬──────┘  └────┬─────────────────┘
                            └──────┬───────┘
                                   ▼
                    paper decision + backtest report
```

### 2.1 数据层

建议使用 Parquet 作为可移植数据格式，DuckDB/Polars 作为本地分析层；大规模训练时再接 Spark/Ray。所有层只追加或按版本写入，禁止覆盖原始数据。

目录约定：

```text
data/raw/        原始 RPC/provider/indexer 响应或 Parquet
data/bronze/     解码后的 block/tx/receipt/log/Transfer/DEX 事件
data/silver/     canonical EventEnvelope、PoolSnapshot、WalletSequence
data/gold/       特征、操作标签、弱角色/意图标签、RL trajectory
data/manifests/  查询、区块范围、schema、checksum、完整性报告
```

每个数据分片必须有 manifest：

```yaml
dataset_id: "[DATASET_ID]"
chain_id: 56
source: "[DUNE|BITQUERY|ARCHIVE_RPC|OTHER]"
source_version: "[VERSION_OR_DATE]"
block_start: "[BLOCK]"
block_end: "[BLOCK]"
ingested_at: "[UTC]"
schema_version: "[SCHEMA]"
sha256: "[CHECKSUM]"
completeness: "[complete|partial|unknown]"
missing_reason: "[NONE_OR_CODE]"
```

服务器开始正式实验前，manifest 还必须补齐：

```text
query_or_export_id
canonical_block_hash
finality_policy
pool_universe_as_of
raw_checksum
license_status
```

当前 `research-resources/datasets/` 只保存数据源说明，尚未包含可再分发的 BSC 历史数据；服务器端不得把当前 WebUI 的 Top 3 discovery 结果当作历史训练 universe。

### 2.2 事件标准化层

首批事件必须覆盖：

- `PairCreated`：池生命周期和池 universe；
- `Swap`：交易方向、数量、区块内位置；
- `Sync`：储备变化；
- `Mint`/`Burn`：LP 增减；
- BEP-20 `Transfer`/`Approval`：地址行为和代币流；
- transaction、receipt、gas、status：执行结果、失败和成本；
- 合约调用与权限事件：代币税、黑名单、暂停、mint、owner 控制等风险特征。

规范化事件字段最低要求：

```text
chain_id
pool_address / token_address / actor_address
block_number / transaction_index / log_index
block_time / event_time
tx_hash / log_topic / decoded_event
amount0_in / amount1_in / amount0_out / amount1_out
reserve0_after / reserve1_after
gas_price / gas_used / tx_status
source / source_version / quality / missing_reason
confirmed / is_reorged / ingested_at
```

AMM 交易不能直接套 CLOB 的 best bid/ask 语义。价格、深度、冲击必须根据 CFMM 曲线、储备、手续费和 token decimals 计算。

## 3. 训练数据方案

### 3.1 推荐数据来源优先级

| 优先级 | 来源 | 用法 | 主要问题 |
|---|---|---|---|
| 1 | 自建 BSC archive node | 最完整、可复核、可固定区块范围 | 磁盘、同步和历史 state 成本高；快照规模可能达到 TB 级。 |
| 2 | Bitquery BSC Parquet | 快速获得 blocks、transactions、transfers、DEX trades、pools、events | 商业服务、字段和历史覆盖要按账号确认。 |
| 3 | Dune BNB raw/decoded/curated | 适合先做研究查询和样本导出 | 查询额度、刷新延迟和数据抽取限制。 |
| 4 | 专用 indexer/API | 适合历史 receipts、traces、labels、风险字段 | 供应商依赖、费用和可复现性。 |
| 5 | BSC RPC | 实时增量、局部校验、最近区块 | 官方公共端点对 `eth_getLogs` 有限制，不适合直接回填全历史。 |
| 6 | GeckoTerminal | Top-volume discovery、OHLCV、展示快照 | 排名和聚合规则是外部 provider 语义，不能作为唯一 ground truth。 |

第一批服务器实验建议：使用 Bitquery/Dune 导出一个固定区块窗口作为可重复数据源，同时用第二来源抽样核对；随后再决定是否部署 archive node。不要一开始下载全 BSC 或全链所有 meme coin。

### 3.2 数据集范围建议

第一阶段不是追求全量，而是构造可审计的研究 panel：

1. 选定 PancakeSwap V2-compatible pool universe；记录选择时点、流动性门槛和 quote token。
2. 覆盖多个市场阶段：上涨、下跌、横盘、流动性枯竭、暴涨暴跌和撤池事件。
3. 同时保留存活 token、死亡 token、撤池 token 和极低流动性 token，避免幸存者偏差。
4. 按时间分 train/validation/test；额外按 token 做 unseen-token test，按市场阶段做 regime test。
5. 对重叠预测窗口实施 purge/embargo，避免相邻窗口共享未来标签。
6. 先做 1 个固定小 panel 验证 schema，再扩展到服务器容量允许的全量。

具体 token 数、区块跨度和事件数应由服务器实际数据源覆盖、磁盘和预算决定，不应在没有探测结果前伪造固定规模承诺。

## 4. 标签设计

### 4.1 观察操作标签：优先做硬标签

直接由可验证事件生成：

| 标签 | 证据 |
|---|---|
| `buy_quote_to_token` | Pair Swap 的输入/输出方向，结合 token0/token1 与 quote 配置。 |
| `sell_token_to_quote` | 相反方向。 |
| `add_liquidity` | Mint/LP token 增加及对应储备变化。 |
| `remove_liquidity` | Burn/LP token 减少及对应储备变化。 |
| `transfer` | BEP-20 Transfer，但必须避免把池内记账转移误认成用户交易。 |
| `unknown` | 事件不完整、路由复杂、方向不确定或失败交易。 |

操作标签必须区分 observed 和 inferred。多跳路由要把完整 transaction path 解码后再标注，不能只用某一个 Transfer。

### 4.2 角色与行为标签：弱监督而非身份断言

训练目标必须分层：

```text
observed_action       # 链上事件可核验
behavioral_pattern    # 规则/模型归纳的行为模式
intent_hypothesis     # 带证据的潜在意图假设
```

第一版优先训练 `P(behavioral_pattern | observed_action, state, history)`；`intent_hypothesis` 只能作为候选解释，不得当成真实心理标签。每个弱标签必须记录 `target_definition`、`label_as_of`、`evidence_cutoff`、`label_rule_version`、`confidence`、`review_status`，并支持 `unknown` 和多标签。

角色候选可以由以下证据组合：

- 已知协议/路由/桥/交易所合约地址：基础设施候选；
- LP Mint/Burn、长期库存和双边交易：LP/做市候选；
- 跨池、跨 token、短时价格差闭环：套利候选；
- 高频、小时间间隔、gas/区块位置特征：MEV 候选；
- 首发资金、财库转移、权限调用：项目方/早期持币者候选；
- 单边持续流出、余额约束和价格压力：被迫退出候选；
- 其他：未知/混合。

这些只是 `behavioral_hypothesis`。同一地址可能换角色，地址也可能是代理、聚合器或共享控制实体；不能把地址标签当真实身份。

### 4.3 意图标签：事件后窗口的弱标签

意图不可直接观察，建议用可审计规则生成弱标签并保留置信度：

- `accumulation`：一段窗口内净积累且没有快速反向退出；
- `distribution`：一段窗口内净分发且库存下降；
- `take_profit`：大幅上涨后分阶段减仓；
- `stop_loss_or_exit`：波动/风险事件后快速退出；
- `market_making_inventory`：双向流、库存回归和 LP 状态配合；
- `liquidity_migration`：LP Burn 后在新池 Mint 或路由迁移；
- `mev_extraction`：同块/邻近交易、价格影响和回收路径符合 MEV 模式；
- `project_treasury_management`：与已知项目合约、财库钱包或权限调用相连；
- `inducement_manipulation_hypothesis`：只能作为待验证假设，不作为事实标签；
- `unknown_multi`：多个解释同样合理时保留多标签或 abstain。

标签必须记录 `label_source`、`label_rule_version`、`confidence`、`review_status`、`evidence_positions` 和 `label_as_of`。未来窗口只能生成 target，不能回流到决策时点的 feature。

## 5. 条件概率学习框架

### 5.1 第一层：可解释统计基线

先实现当前已有的 Dirichlet/Laplace 条件计数：

```text
P(intent | role, observed_action, state_bin)
```

初始 `state_bin` 可由离线拟合的 regime 分箱构成：流动性、波动、事件密度、OFI、price impact、pool age、token age、market phase。分箱器只在训练集拟合，并保存版本。

必须输出：样本计数、平滑参数、后验、训练 cutoff、有效类别数和 abstain 条件。样本过少时优先 abstain，而不是提高模型复杂度。

### 5.2 第二层：监督/弱监督多任务模型

推荐结构：

```text
event sequence encoder
    -> action head
    -> role head
    -> intent head conditioned on role/action
    -> calibration + abstention head
```

可比较的模型顺序：

1. Logistic/Dirichlet/Markov baseline；
2. CatBoost/LightGBM tabular baseline；
3. GRU/TCN/Transformer event sequence model；
4. address interaction graph model；
5. Bayesian/ensemble uncertainty model。

DeepLOB/Sirignano-Cont 的经验支持共享微结构表示和跨资产 pooling，但它们主要针对 CLOB/传统交易数据，不能未经适配直接作为 BSC AMM 结论。当前 BSC 应先验证 token0/token1、CFMM 储备、LP/Swap/Transfer 和区块排序特征。

### 5.3 第三层：校准和 OOD

每个 posterior 必须记录：

- `calibration_status`；
- reliability curve / ECE；
- Brier score、log loss、top-k coverage；
- abstention coverage/risk curve；
- token holdout 和 regime holdout；
- 数据源不一致时的 ensemble disagreement。

概率没有通过校准和样本外测试前，只能用于研究展示，不能进入 RL reward 或交易决策。

## 6. 强化学习路线评估

### 6.1 为什么不直接用 PPO 训练历史数据

静态历史数据是由旧行为策略产生的。直接在数据上训练 online PPO/DQN 会隐含地访问数据中没有覆盖的动作，并把“没有发生”误当作“执行后结果”。在真实市场中，动作还会改变池储备、价格、参与率和其他参与者行为。

另外，历史 Swap 只说明市场参与者发生了什么，不等于本项目策略的 `(state, action, reward, next_state, done)` trajectory。offline RL 的 trajectory 必须标记为真实策略日志、规则行为策略、模拟行为策略或 synthetic；未标记来源的 transition 不得进入 RL 训练。

这会产生：

- offline RL 的分布外动作/外推误差；
- 交易成本和成交可得性被低估；
- 单步价格标签被误当成长期 reward；
- 策略对静态历史市场没有反事实影响；
- 训练环境和真实 AMM 机制不一致。

### 6.2 推荐 RL 分层

**阶段 A：行为克隆/策略评估**

从 observed action 学习行为策略 `\hat{\mu}(a|s)`，检查状态覆盖和动作覆盖，不宣称优越收益。

**阶段 B：offline RL**

使用事件轨迹：

```text
(state_t, action_t, reward_t, state_{t+1}, done_t, mask_t)
```

优先比较 BC、CQL 和 IQL。CQL 的核心思想是对数据分布外动作采取保守价值估计；它适合做第一批 offline RL 对照，但不能消除数据缺失和环境错误。

**阶段 C：模型辅助/仿真 RL**

用历史数据校准 AMM event-driven simulator，再在仿真器中比较 PPO/SAC/TD3 等 online RL。仿真器必须报告与真实数据的 stylized facts、流动性、波动、交易量、失败率和顺序统计差异。

**阶段 D：多主体机制实验**

用 PettingZoo 风格接口表示多个角色；AMM 使用自定义 CFMM environment。ABIDES 可参考消息驱动和延迟建模，但其默认市场是 CLOB，不能直接当 PancakeSwap AMM。

### 6.3 RL 状态、动作、奖励

状态 `s_t`：

- 最新 safe position 和 confirmation lag；
- reserve/decimals/fee/price impact；
- Swap/LP/Transfer 事件序列；
- OFI、事件密度、波动、池龄、流动性和价格状态；
- 地址/角色 posterior、数据质量、风险状态；
- 账户现金、库存、仓位、回撤、剩余资金；
- gas、slippage、token tax、RPC/latency 状态。

动作 `a_t`（第一版只做现货只多）：

```text
no_trade | buy_quote_to_token | reduce/exit | hold_inventory
```

动作必须经过 venue capability 和 risk gate。做空、杠杆、合约只有在另一个明确的 execution adapter 和历史数据契约批准后才允许加入。

奖励 `r_t` 应是成本后的风险调整增量，而不是裸价格变化：

```text
reward = pnl_after_fee_gas_tax_slippage
         - inventory_penalty
         - drawdown_penalty
         - risk_penalty
         - unsupported_or_missing_penalty
```

奖励要避免鼓励“永远不交易”或无限持仓；必须与 `no_trade` 基线、行为策略基线和买入持有基线共同评估。

## 7. 推荐技术栈

| 用途 | 推荐 | 说明 |
|---|---|---|
| 原始/标准化数据 | Parquet + PyArrow | 可版本化、列式读取、适合远程对象存储。 |
| 本地查询 | DuckDB + Polars | 适合先做固定 panel、分区查询和审计 SQL。 |
| 统计/特征 | NumPy + pandas/scikit-learn | 先完成简单基线和校准，不急于 GPU。 |
| Tabular baseline | CatBoost 或 LightGBM | 对结构化微结构特征提供强基线，方便解释。 |
| 深度模型 | PyTorch | 共享 encoder、多任务 head、ensemble 和 GPU 训练。 |
| 单体环境 | Gymnasium | 统一 reset/step/action/observation 接口。 |
| 多主体环境 | PettingZoo | 定义角色交互；不要直接把它当市场机制。 |
| Offline RL | CORL/CQL/IQL 参考实现 | 先在标准 benchmark smoke，再接本项目 trajectory。 |
| 多主体仿真 | 自定义 AMM event-driven simulator | 使用 CFMM 机制；ABIDES 只借鉴消息/延迟思想。 |
| 聚类 | HDBSCAN/UMAP + 稳定性分析 | UMAP 用于探索，正式聚类必须记录随机种子和稳定性。 |
| 追踪 | MLflow/W&B 或自建 JSON manifest | 服务器按组织政策选择；敏感配置只存变量名。 |
| 分布式训练 | 先单 GPU，再 Ray/torchrun | 未证明数据规模前不要先上大规模分布式。 |

当前 MVP 不应把这些依赖直接加入生产 WebUI 环境；服务器可建立独立 research environment。

## 8. 服务器资源分级

### Level 0：CPU 研究验证

- 固定小 panel、DuckDB、条件频率、CatBoost/LightGBM；
- 目标是校验 schema、标签、cutoff、回测和指标；
- 不运行大型 Transformer 或多主体 RL。

### Level 1：单 GPU

- PyTorch sequence encoder、ensemble、校准和 CQL/IQL 小规模训练；
- 可对多个 token 做 pooled model；
- 适合先判断意图标签是否有可预测性。

### Level 2：多 GPU/多节点

- 仅在 Level 1 证明样本外改善且数据覆盖足够后使用；
- 才考虑 Transformer、graph model、parallel simulator、Ray/torchrun；
- 必须保存每个 worker 的 seed、data shard、checkpoint 和 failure report。

### Level 3：多主体仿真集群

- 只用于机制研究、压力测试和反事实实验；
- 仿真结果必须和真实 BSC stylized facts 对照；
- 仿真收益不得直接视为可交易 Alpha。

## 9. 服务器初始化顺序

```bash
git clone [GITHUB_REPOSITORY_URL]
cd market-intent-inference

# 先验证当前 MVP，不要先安装大模型依赖
conda run -n codex-engineering pytest -q
conda run -n codex-engineering python -m compileall -q src tests scripts
conda run -n codex-engineering research-wiki validate ./research-wiki
conda run -n codex-engineering graphify validate .

# 配置变量名，不把值写入 Git
export BSC_RPC_URL="[RPC_ENDPOINT]"
export BSC_RPC_FALLBACKS="[OPTIONAL_COMMA_SEPARATED_ENDPOINTS]"

# 运行当前 paper WebUI
PYTHONPATH=src python scripts/run_webui.py --host 127.0.0.1 --port 8765
```

上述命令在当前本地 checkout 仅能验证 WebUI 与现有测试；训练入口尚未实现。服务器接手后的第一条可执行训练链应为：

```text
ingest -> normalize -> build_labels -> fit_baseline -> evaluate
```

这条链应先在固定小 panel fixture 上通过，再扩展到真实 BSC 数据；不要跳过 fixture 直接启动 PPO、CQL/IQL 或多主体 RL。

服务器实验开始前必须先填写：

- `[DATA_SOURCE]` 与服务条款；
- `[DATASET_ID]`、区块范围和 checksum；
- archive/indexer 的历史覆盖和 `eth_getLogs` 能力；
- token universe 选择规则；
- fee/gas/slippage/tax 模型；
- 训练/验证/测试 cutoff；
- 允许的 GPU、磁盘、并行度和预算。

## 10. 推荐实验顺序与验收条件

### E0：数据可用性

验收：固定区块 panel 可重复下载；抽样与第二来源一致；schema、位置、时间、完整性和缺失原因报告通过。

### E1：操作标签

验收：Swap/Mint/Burn/Transfer 的方向和误分类率经过人工抽样；路由、池内记账、失败交易和多跳路径有单独测试。

### E2：条件概率基线

验收：条件计数、Laplace 平滑和 abstain 结果可复现；训练 cutoff 不读取未来；输出 coverage、Brier、log loss 和置信区间。

### E3：角色/意图弱监督

验收：每个弱标签带规则版本和证据；抽样人工审查；未知/多标签保留；cluster 只能进入 candidate registry。

### E4：监督模型与校准

验收：至少超过简单基线或明确解释没有超过；未见 token、未见时期、未见 source 测试通过；校准没有被单一随机切分掩盖。

### E5：事件驱动回测

验收：确认延迟、区块内顺序、手续费、Gas、滑点、税、失败和参与率上限均被建模；与买入持有、随机、无信号、简单动量比较。

### E6：offline RL

验收：先在行为策略覆盖范围内评估；CQL/IQL/BC 与基线比较；报告 OOD action rate、policy support、off-policy uncertainty、成本后收益和 drawdown；任何异常改善都要回到事件级审计。

### E7：多主体仿真

验收：仿真器能重现真实事件密度、价格冲击、流动性、波动、LP 行为和区块顺序统计；改变随机种子和 agent mix 后结论稳定。

## 11. 绝对不要做的事情

1. 直接用 PPO 在一条静态价格序列上训练，然后把收益当作市场适应能力。
2. 用未来涨跌结果给当前地址贴“知情/操纵/止损”标签，再把标签输入当前特征。
3. 把 GeckoTerminal 的当前 volume/liquidity 或 provider ranking 当作历史时点事实。
4. 用 candle close 代替真实 AMM 执行、储备变化和滑点。
5. 忽略 token decimals、税、honeypot、撤池和交易失败。
6. 用全样本拟合标准化器、聚类器、token universe 或校准器。
7. 只做随机 train/test split，不做时间、token、regime 和 source holdout。
8. 把 `unknown` 当成安全，把 `no_trade` 当成做空，把 `abstain` 当成负预测。
9. 用一次 Sharpe、一次回测或模拟器收益宣称 Alpha。
10. 将角色概率、意图概率或 LLM 解释写成真实身份/真实动机断言。
11. 在研究服务器上放入私钥、助记词、钱包 Cookie、RPC token 或真实交易接口。
12. 修改或导入 `/Users/mashengyu/Desktop/quant research/coinman-arbitrage-bot`。

## 12. 交接后第一批需要人类确认的决策

服务器端真正开始训练前，请确认：

1. 选择 Dune、Bitquery、自建 archive node 或组合方案；
2. 研究区块范围、token/pool universe 和 quote token；
3. 允许的历史数据费用和 GPU/磁盘预算；
4. 第一版标签采用纯规则、人工抽样弱标签，还是引入地址聚类；
5. 第一版是否只预测 `intent | observed_action, state`，暂不预测真实角色；
6. 第一版策略是否固定 spot long-only、paper-only；
7. 风险字段达到什么覆盖率后才允许将 `no_trade` 放宽到策略回测；
8. 是否允许下载论文 PDF 到 GitHub，或只上传 manifest 和引用链接。

在这些决策确认前，推荐继续保留当前系统的 `abstain/no_trade` 默认行为。

## 13. 独立审查后的不可越过门槛

在以下条件完成前，不得把训练结果称为“识别真实意图”，也不得声称策略具有可交易 Alpha：

1. 固定小 panel 可以完成 ingest、normalize、build_labels、fit_baseline、evaluate；
2. 所有弱标签都可追溯到规则版本、证据窗口和审查状态；
3. 数据 manifest 可复现，包含 checksum、完整性、历史 universe 和许可证状态；
4. 历史回放器通过成本、滑点、失败交易和 reserve reconciliation 检查；
5. 策略 trajectory 与市场事件日志分离，OPE 和 action support 已报告；
6. 训练环境和 CUDA/依赖版本锁定；
7. 结果经过 token、pool、regime、wallet 和数据源外推测试。
