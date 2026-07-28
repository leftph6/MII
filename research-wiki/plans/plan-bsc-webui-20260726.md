---
id: plan-bsc-webui-20260726
type: plan
title: BSC WebUI 与链上只读闭环实施计划 v0.1
status: approved
tags:
- implementation-plan
created_at: '2026-07-25T16:30:44Z'
updated_at: '2026-07-25T17:18:22Z'
---

# BSC WebUI 与链上只读闭环实施计划 v0.1

状态：`approved`

## 目标

在已批准的 BSC WebUI 设计上实现最小可运行闭环：本地 HTTP dashboard → GeckoTerminal BSC Top-volume discovery → 可配置 BSC RPC 能力探测与 V2-compatible 核验 → 最近 Swap 日志标准化 → cutoff-safe 市场状态/微结构元素 → 结构化 abstain/no-trade 推理结果 → run JSON/JSONL 产物。

## 严格范围

- 只支持 chain ID 56；
- discovery 默认使用 GeckoTerminal keyless public API；
- `BSC_RPC_URL` 可配置，未配置时使用官方公共 RPC 作为默认连接尝试；
- 默认 `top_k=3`，服务端限制 `1 <= top_k <= 10`；
- 只读方法：`eth_chainId`、`eth_blockNumber`、`eth_getBlockByNumber`、`eth_getLogs`、必要的只读 `eth_call`；
- 只接受通过 DEX mapping + RPC/ABI 核验的 PancakeSwap V2-compatible pair；
- provider 当前快照只展示，不进入严格 feature/posterior；
- 预测因无标注训练集默认结构化 abstain，不伪造概率优势；风险未知输出 no-trade；
- 不连接 Coinman，不读写 Coinman，不写钱包/私钥/环境秘密，不实现任何发送交易方法。

## 设计前置

已批准设计：`design-bsc-webui-v0-1`；已批准日志 schema：`schema-bsc-webui-log-v0-1`；独立设计审查已关闭 provider snapshot、eth_getLogs error semantic、DEX/V2 verification 三项问题。

## TDD 白名单

实现代理只能写入以下业务/测试文件：

- `pyproject.toml`；
- `src/market_intent_inference/adapters/__init__.py`；
- `src/market_intent_inference/adapters/geckoterminal.py`；
- `src/market_intent_inference/adapters/bsc_rpc.py`；
- `src/market_intent_inference/application/__init__.py`；
- `src/market_intent_inference/application/bsc_pipeline.py`；
- `src/market_intent_inference/application/run_store.py`；
- `src/market_intent_inference/interfaces/__init__.py`；
- `src/market_intent_inference/interfaces/web.py`；
- `web/index.html`、`web/app.js`、`web/styles.css`；
- `scripts/run_webui.py`、`scripts/bsc_smoke.py`；
- `tests/fixtures/geckoterminal_top_pools.json`、`tests/fixtures/geckoterminal_dexes.json`、`tests/fixtures/rpc_logs.json`；
- `tests/test_geckoterminal.py`、`tests/test_bsc_rpc.py`、`tests/test_bsc_pipeline.py`、`tests/test_run_store.py`、`tests/test_web.py`、`tests/test_external_boundary.py`；
- `evals/bsc-webui.yaml`。

允许的额外生成物仅为：`artifacts/runs/<run_id>/summary.json`、`artifacts/runs/<run_id>/events.jsonl`、`harness-results/<runner-created-run>/`、`graphify-out/GRAPH_REPORT.md`、`graphify-out/graph.json`、`test-artifacts/bsc-webui/`、`research-wiki/index.md`、`research-wiki/query_pack.md`、`research-wiki/log.md`、`research-wiki/graph/edges.json`、本计划的 Wiki 副本、`research-wiki/reviews/review-bsc-webui-plan-20260726.md` 和 `docs/reviews/coinman-isolation-20260726.md`。任何 `__pycache__`、`.pytest_cache`、`.ruff_cache` 必须在验证后删除，不得作为交付物；不得使用笼统通配符扩大写入范围。

禁止修改：Coinman、现有领域契约、旧领域测试、旧研究论文、旧设计正文、旧审查正文、AGENTS.md，除非后续独立审查确认是必要且另行批准。

## 实施步骤

### 1. 配置和网络边界

- 使用 Python 标准库 `http.client`、`http.server`、`json`、`os.getenv`；不引入第三方网络库；
- 所有外部请求带 timeout、有限重试、响应大小上限、provider/RPC allowlist；
- discovery 缓存只允许用于已解析的 provider pool/DEX DTO：缓存为进程内存缓存，键固定为 `(provider, network, dex_id, sort, page, page_size, config_fingerprint)`，`config_fingerprint` 覆盖 allowlist、endpoint、timeout、retry、response limit 和 `cache_ttl_seconds`；默认 TTL 为 30 秒且允许范围固定为 5–60 秒；成功结果按 TTL 返回，失败、429、timeout、malformed 响应不写入缓存；配置、排序、分页或 DEX 变化立即形成新键，过期结果默认不提供 stale fallback；测试必须覆盖命中、TTL 过期、键隔离、配置 fingerprint 隔离和失败不缓存；
- URL、chain ID、top_k、lookback、confirmation lag 和 cache TTL 由不可变配置对象承载；`BSC_RPC_URL` 只用于连接，不写入日志/summary/config snapshot；持久化只允许 `rpc_scheme`、`rpc_host`、`has_userinfo` 和 URL fingerprint，必须移除 userinfo、query、fragment、Authorization 和 API-key-like 字段；
- 禁止 `eth_sendRawTransaction`、wallet、private key、交易 calldata 和写方法字符串进入业务代码；
- 测试中只使用 fake transport，不访问网络。

### 2. GeckoTerminal adapter

- 读取 BSC DEX 列表，建立 provider DEX id → canonical name/factory/router/address 映射；只有映射的 network、factory 和 router 与本地固定配置完全一致时才可进入链上核验；
- 请求 BSC pools，按 `h24_volume_usd_desc` 分页，筛选配置 DEX；
- 解析 `data/included` 为 `PoolCandidate`，保留 provider rank、volume、liquidity、tx count、observed_at；
- 对 malformed/429/timeout 返回结构化 `source_unavailable`/`quality_failed`，不返回空成功列表；
- provider 快照字段标记为 display-only。

### 3. BSC RPC adapter

- `eth_chainId` 必须等于 `0x38`；
- `eth_blockNumber` 作为 latest block，扣除 confirmation lag 得到 decision block；
- 通过只读 `eth_getBlockByNumber(block, false)` 获取每个 distinct block 的 timestamp；事件 `event_time` 由其 block timestamp 得到，无法取得时为 unknown；
- `decision_position` 固定为 `(safe_block, MAX_TX_INDEX, MAX_LOG_INDEX)`，`data_cutoff` 为本次完整读取范围内的最后可证明事件位置；无事件时使用 `(safe_block, 0, 0)` 并输出 insufficient_data；
- 对候选池只读调用 `token0()`、`token1()`、`getReserves()`、`factory()`；`factory()` 必须等于配置的 PancakeSwap V2 Factory `0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73`，配置的 Router V2 必须等于官方 `0x10ED43C718714eb63d5aA57B78B54704E256024E`；provider DEX mapping、factory、router、ABI 事件任一不匹配即核验失败；
- `eth_getLogs` 只查询显式池地址、有限 block range；解析 V2 Pair Swap ABI 的 indexed sender/to 与四个 amount；
- `eth_getBlockByNumber` 得到的 safe-block timestamp 定义 `decision_time`；事件 timestamp 缺失时事件仍可保留其 position 供审计，但不得进入任何 features、MarketState elements、data_cutoff 的时间断言或后验条件；若 safe-block timestamp 或全部事件 timestamp 缺失则质量为 `insufficient_data` 并 abstain；
- log 无法查询/超范围/端点禁用时输出 `not_supported` 或 `source_unavailable`，绝不转成 `future_data`；
- 所有事件按 `(block_number, transaction_index, log_index)` 排序并过滤到 cutoff；测试必须覆盖 block timestamp 缺失、same-block later event、factory mismatch 和 router config mismatch。

### 4. Pipeline 与推理

- 生成 run_id、PredictionContext、decision_position、data_cutoff；
- provider ranking 不进入 MarketState elements；严格 elements 只来自带 position 的 RPC event/state；
- 计算 reserves、mid price、price impact proxy、buy/sell counts、quote/token flow、OFI-like net flow、event density 和 failure count；
- V2 核验失败、数据缺失或无可用日志时生成结构化 abstain；
- 首阶段无训练集，role/action/intent 使用完整固定枚举的 abstain posterior；
- 风险 snapshot 默认 unknown/not_supported，Decision 固定 no-trade；
- 返回 `PoolAnalysis`、`PredictionResult`、`Decision` 与每阶段 evidence/reason codes。

### 5. Run store 与结构化日志

- `artifacts/runs/<run_id>/summary.json` 保存脱敏摘要；
- `artifacts/runs/<run_id>/events.jsonl` 遵循 `bsc_webui_event.v0.1`；
- 原始 provider/RPC response 不原样持久化；只保存解析后的字段、响应 hash/数量和错误类型；RPC URL 脱敏测试必须使用包含 userinfo、query、fragment、Authorization header、API-key-like query/header 值的伪造输入，并断言这些秘密及其原文 URL 不出现在 summary、JSONL、异常、结构化事件或 HTTP response；同时断言 fingerprint 只由允许的非秘密连接元数据计算；
- run store 写失败不改变 no-trade 语义，标记 `audit_degraded=true`；
- `GET /api/runs/{run_id}/events` 只返回脱敏事件。

### 6. WebUI

- `ThreadingHTTPServer` 仅绑定 `127.0.0.1`；
- 静态页面无构建依赖；
- API：health、pools、analyze、run summary、run events；
- JSON schema 校验 `top_k`、pool addresses、lookback 和 `paper=true/mode=spot_long_only`；
- 不接受任何交易执行参数；
- UI 显示 provider rank 与 RPC verified 的分离状态，并显示 `unknown/not_supported`。

### 7. 测试与验证

先写红灯测试，再实现：

- DTO 解析、分页排序、malformed/429/timeout；
- RPC chain ID、hex decode、ABI calls、log order、cutoff、confirmation lag、RPC disabled；
- V2 verification pass/fail；provider snapshot 不进入 features；
- no-data abstain、risk unknown no-trade、paper-only、无写链静态边界；
- run store JSON/JSONL schema、脱敏、幂等和写失败降级；
- web route、method allowlist、path traversal、JSON validation、localhost binding；
- 离线全量 pytest、compileall、Ruff、security、Harness、Graphify、Research Wiki；
- 显式网络 smoke 只在用户环境配置 `BSC_RPC_URL` 后执行，不作为离线 Harness 通过条件；网络 smoke 只记录脱敏 host 和能力状态。

## 固定隔离与质量门禁命令

- 领域回归：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src conda run -n codex-engineering python -m pytest -p no:cacheprovider -q`，必须保持既有 14 项通过；
- BSC 离线测试：同一命令覆盖 adapter/pipeline/run-store/web，必须全部通过；
- 编译：`PYTHONDONTWRITEBYTECODE=1 conda run -n codex-engineering python -m compileall -q src tests scripts`，退出码 0；
- 静态检查：`RUFF_NO_CACHE=true conda run -n codex-engineering python -m ruff check src tests` 与 `ruff format --check src tests`，均通过；
- 安全：`PYTHONDONTWRITEBYTECODE=1 conda run -n codex-engineering python scripts/check_security.py`，输出 `security_boundary_ok`，另验证无写链方法、钱包、私钥、Coinman import/path；
- Harness：仓库内必须存在完整 `evals/bsc-webui.yaml`，声明 `version/name/root/timeout_seconds/no_external_dependencies_reason` 及 unit-tests、compile、security-boundary 三个 checks，每个 check 均声明 command、expected_exit_code 和 stdout/stderr contains/not_contains；执行 `conda run -n codex-engineering harness-eval validate ./evals/bsc-webui.yaml`；随后使用尚不存在的明确目录运行 `conda run -n codex-engineering harness-eval run ./evals/bsc-webui.yaml --output ./harness-results/bsc-webui-20260726`，报告带 run_id/spec hash/产物路径；若目录已存在，先选择一个明确且不存在的日期后缀，不覆盖任何既有报告；
- Graphify：依次执行 `conda run -n codex-engineering graphify build .`、`conda run -n codex-engineering graphify update .`、`conda run -n codex-engineering graphify validate .`、`conda run -n codex-engineering graphify query "bsc_pipeline|GeckoTerminal|BSC_RPC_URL" --root . --limit 20`，图谱必须与源码同步且 query 返回新增闭环符号；
- Research Wiki：`conda run -n codex-engineering research-wiki index ./research-wiki`、`conda run -n codex-engineering research-wiki pack ./research-wiki`、`conda run -n codex-engineering research-wiki validate ./research-wiki`，校验通过；
- Coinman：历史基线若与最新只读复核不一致，只记录为外部状态差异，不归因、不恢复、不修改；以紧邻实现开始前的最新 stdout 作为本轮 baseline。实现前后各执行且只执行 `git -C "/Users/mashengyu/Desktop/quant research/coinman-arbitrage-bot" status --porcelain=v1` 与 `git -C "/Users/mashengyu/Desktop/quant research/coinman-arbitrage-bot" diff --name-only`；将两次 stdout 原样保存到本项目 `docs/reviews/coinman-isolation-20260726.md` 并与该 baseline 逐字比较，最终差异必须为零；不得执行 `find/cat/rg/python/open` 指向 Coinman，不得读取代码/数据库/环境/凭据；
- 验证后删除显式列出的 Python/cache 生成物，并检查新项目不含未列入白名单的代码文件。

## 验收标准

1. `python scripts/run_webui.py` 可启动本地 dashboard；
2. `GET /api/health` 返回 chain/config/provider 状态；
3. fixture 模式能稳定展示 Top 3、选择池并回放完整分析；
4. 真实网络 smoke 配置正确时能获取候选池；RPC logs 可用时至少一个池完成链上事件分析；
5. RPC logs 不可用时 UI 明确降级为 not_supported/insufficient_data；
6. 所有摘要带 run_id、decision_position、data_cutoff、quality、source 和 reason codes；
7. 测试与静态扫描确认无钱包、私钥、写链和 Coinman import；
8. 不改变既有 14 项领域内核测试的行为。

## 回滚

新增适配器/UI 文件可整体移除；现有 domain 与 tests 不改行为；网络 smoke 只产生新 run artifacts，不修改代码或 Coinman。
