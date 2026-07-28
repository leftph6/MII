---
id: plan-domain-kernel-20260725
type: plan
title: Domain kernel implementation plan 2026-07-25
status: approved
tags:
- implementation-plan
created_at: '2026-07-25T14:23:27Z'
updated_at: '2026-07-25T15:12:05Z'
---

# 首个领域内核实现计划

## 目标

实现独立项目的最小可验证切片：固定 V2-compatible AMM fixture → 标准化事件 → 市场状态/观察事实 → 条件频率后验 → 受 venue capability、风险状态和 paper-only 约束的 `Decision`。

本切片只使用 Python 标准库、固定本地 fixture 和纯函数；不连接网络，不读取 RPC、钱包、环境秘密或 Coinman，不实现 LLM、聚类、真实 BSC 数据、写链和任何交易执行。

## 前置门禁

执行前必须确认：

1. `AGENTS.md`、已批准设计、设计审查、本计划和 `docs/design/domain-contract-v0.1.md` 均已读取；
2. 设计实体状态为 `approved`，计划已通过新的独立审查；
3. 本次 TDD 写入范围只允许 `pyproject.toml`、`src/market_intent_inference/__init__.py`、`src/market_intent_inference/domain.py`、`src/market_intent_inference/inference.py`、`scripts/check_security.py`、`tests/conftest.py`、`tests/fixtures/amm_v2_events.json`、`tests/test_domain.py`、`tests/test_inference.py`、`tests/test_security_boundary.py` 和 `evals/domain-kernel.yaml`；审查报告、Wiki、Harness、Graphify 和隔离证据是额外生成物，不得修改既有设计、论文或历史审查；
4. 禁止修改、写入或读取 `/Users/mashengyu/Desktop/quant research/coinman-arbitrage-bot` 的代码、数据库、环境和运行状态；只允许通过 Git 元数据命令记录其文件状态，用于证明前后未发生变化；
5. 当前新目录没有 Git 元数据，因此不把 Git diff 作为本项目通过证据；使用文件清单、SHA-256、测试产物和现有 Coinman 工作区状态作为替代证据。

## 精确文件范围

TDD 写入白名单：`pyproject.toml`、`src/market_intent_inference/__init__.py`、`src/market_intent_inference/domain.py`、`src/market_intent_inference/inference.py`、`scripts/check_security.py`、`tests/conftest.py`、`tests/fixtures/amm_v2_events.json`、`tests/test_domain.py`、`tests/test_inference.py`、`tests/test_security_boundary.py`、`evals/domain-kernel.yaml`。额外生成物只允许：`harness-results/domain-kernel/`、`graphify-out/`、`test-artifacts/domain-kernel/`、`research-wiki/index.md`、`research-wiki/query_pack.md`、`research-wiki/log.md`、`research-wiki/graph/edges.json`、`research-wiki/plans/plan-domain-kernel-20260725.md` 的状态更新和稳定路径 `research-wiki/reviews/review-plan-final-20260725.md`；不得修改 `AGENTS.md`、`README.md`、已批准设计、`docs/design/domain-contract-v0.md`、`docs/design/domain-contract-v0.1.md`、`docs/research/**`、既有审查或论文实体。

禁止新增执行 adapter、RPC client、wallet、private-key、LLM client、聚类模型、WebUI 或跨项目 import；静态扫描脚本只能读取本项目 `src/`、`tests/` 和受控配置。

## 步骤

### 1. 工程基线与隔离检查

- 创建 `pyproject.toml`、`src/market_intent_inference/__init__.py`、`tests/conftest.py`、`tests/fixtures/amm_v2_events.json` 和 `evals/domain-kernel.yaml`。
- 只使用标准库实现首个切片，fixture 固定 chain ID 56、区块号、交易序号、日志序号、token0/token1、reserve、Swap 输入输出、gas、失败状态和 source/as_of。
- 在 `test-artifacts/domain-kernel/coinman-status-before.txt` 保存 `git -C "/Users/mashengyu/Desktop/quant research/coinman-arbitrage-bot" status --porcelain=v1` 和 `git -C "/Users/mashengyu/Desktop/quant research/coinman-arbitrage-bot" diff --name-only` 的输出；只读取 Git 元数据，不读取 Coinman 代码、数据库或运行状态。
- 验证 `python3 --version`、`python3 -m compileall -q src tests`、新项目文件清单不包含 Coinman 路径；本项目不使用 Git 命令作为通过条件。

### 2. 红灯：领域契约

- 先创建 `tests/test_domain.py`。
- 按 `docs/design/domain-contract-v0.1.md` 的字段类型、枚举值、时间格式、构造器不变量、缺失原因集合、PredictionContext/PredictionResult 和 Decision 输出契约逐项测试。
- 明确测试 `decision_time <= horizon_end`、`data_cutoff <= decision_position`、事件可用条件 `confirmed=true AND event_position <= decision_position`、`event_time <= decision_time`、`as_of <= decision_time`、`paper=false`、风险四态和 capability 矩阵；`PredictionContext` 的字段必须完整进入 `PredictionResult`。
- 预期初始失败原因是目标模块和类型尚未存在。

### 3. 绿灯：领域对象

- 创建 `src/market_intent_inference/domain.py`。
- 严格实现 `docs/design/domain-contract-v0.1.md` 中的 `PredictionContext`、`PredictionResult`、`EventEnvelope`、`AMMV2SwapEvent`、`MarketState`、`Role`、`Action`、`BehavioralHypothesis`、`LatentIntent`、`ObservedFact`、`Evidence`、`RiskField`、`RiskSnapshot`、`Posterior`、`ConstraintSet`、`Decision` 和 `VenueCapability`。
- `RiskStatus=known_true` 和 `unknown/not_supported` 均不得放行交易；只有关键风险为 `known_false` 且其他约束通过才允许 paper trade。
- 字段类型、枚举值、时间格式、缺失原因集合、能力矩阵、posterior 不变量和 Decision 输出以 `docs/design/domain-contract-v0.1.md` 为唯一契约；测试与实现不得自行扩展。
- 测试全部九个 `RiskField` 必须存在；构造缺字段失败；多个拒绝条件同时出现时严格断言 reason-code 优先级：`paper_only > future_data > insufficient_data > risk_blocked > risk_unknown > unsupported_venue > uncalibrated`。

### 4. 红灯：事件与概率行为

- 创建或扩展 `tests/test_inference.py` 与固定 fixture，覆盖 PredictionContext 的完整输入/输出、`event_time > decision_time`、`event_time is None`、`success=False` 不产生状态改变事实、token0/token1 方向、完整路径、事件可用集合、event position、data cutoff、未来标签只作 target/evaluation、训练 cutoff 与 decision/horizon 关系、未来条件频数隔离、角色/操作/意图多标签/unknown、条件频率+平滑、abstain 和 no-trade。
- 对后验固定断言：`alpha == 1.0`；`condition_key == (role.value, observed_action.value)`；类别全集来自固定枚举并按 Unicode code-point ascending 排序；`training_cutoff <= data_cutoff <= decision_position`；训练样本严格 `event_position <= training_cutoff`，预测样本不计数。
- 明确测试 `paper=false -> abstain/paper_only`、`known_true -> no_trade/risk_blocked`、`unknown/not_supported -> no_trade/risk_unknown`、short/leverage/write capability 不支持 -> `no_trade/unsupported_venue`，以及任何 Coinman import/路径均失败。
- 预期初始失败原因是标准化器、后验和决策函数尚不存在。

### 5. 绿灯：纯函数实现

- 创建 `src/market_intent_inference/inference.py`。
- 实现 V2 Swap 标准化、事件到状态/观察事实映射、带训练截止点和 Laplace 平滑的条件后验、evidence 处理和安全决策函数。
- 只允许 `paper=True`、`mode=spot_long_only`、关键风险全部为 `known_false` 和 venue capability 的 `supported_paper_actions` 支持的 action；`supports_write_execution=False` 只禁止真实写链，不阻止 paper simulation；其余严格输出契约定义的结构化 reason code 和优先级。
- 禁止 RPC、钱包、LLM、聚类、写链调用、`eth_sendRawTransaction` 和未来数据访问。

### 6. 强制验证与产物

- 固定 fixture，测试同样输入得到同样输出；检查概率和为 1、无未来数据和无执行能力。
- 强制运行 `python3 -m pytest -q`、`python3 -m compileall -q src tests`、`python3 -m ruff check src tests`、`python3 -m ruff format --check src tests`、Harness Eval validate/run、首次 `graphify build .` 后再 `graphify update .`/`graphify validate .`、核心符号 query/path、Research Wiki index/pack/validate 和静态安全/隔离检查。
- `evals/domain-kernel.yaml` 必须使用参数数组命令、有限 timeout、非空 `no_external_dependencies_reason`，且不设置 `dependency_snapshot_commands`/`dependency_integrity_files`；三项检查固定为 `unit-tests`、`compile`、`security-boundary`，每项有唯一 ID、期望退出码、至少一条 stdout/stderr 包含或不包含断言；运行器必须写入新的 `harness-results/<runner-created-directory>/`，不得覆盖旧报告，报告必须有 run ID、规格 hash、命令、退出码和产物路径。
- `scripts/check_security.py` 必须扫描 `src/`、`tests/` 和 `pyproject.toml`，对 `eth_sendRawTransaction|private[_-]?key|mnemonic|web3|requests|httpx|urllib|subprocess|os\.environ` 命中即返回非零；允许的标准库导入需在报告中解释。Ruff 未安装时记录退出原因，不得把未运行写成通过。
- 在 `test-artifacts/domain-kernel/coinman-status-after.txt` 保存同一组 Coinman Git 元数据命令输出，并要求 before/after 完全相同；只比较 Git 元数据，不读取 Coinman 代码或运行状态。将最终计划审查摘要写入稳定路径 `research-wiki/reviews/review-plan-final-20260725.md`，再刷新 index/query_pack/validate。

## 回滚

首个切片只新增新项目文件和知识库/验证生成物；如验证失败，保留失败证据并只修正本切片，不触碰现有 Coinman 项目。由于本目录没有 Git 元数据，使用文件清单、SHA-256 和 Coinman 零修改检查替代 `git diff --check`。

## 暂不实现

真实 BSC RPC/索引器、PancakeSwap 地址抓取、合约风险扫描、聚类、新意图发现、WebUI、策略回测和任何交易执行，均等待下一份经过审查的计划。
