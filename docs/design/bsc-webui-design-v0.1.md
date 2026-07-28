# BSC WebUI 与链上数据全流程设计 v0.1

状态：`approved`

## 1. 目标

在现有离线领域内核之上增加一个本地 WebUI 和只读 BSC 数据适配器，使用户可以：

1. 查看 BSC 上按 24 小时交易量排序的候选池；
2. 选择前 K 个池或手工选择一个池；
3. 拉取池详情和最近交易；
4. 以区块位置为截止点标准化 Swap、构造市场状态、计算微结构元素；
5. 输出角色/操作/意图后验、风险状态、数据质量、abstain/no-trade 原因；
6. 在一个页面看到从发现、核验、标准化到推理的完整 run。

本阶段仍然是 paper-only、只读、无钱包、无私钥、无写链、无交易执行。

## 2. 非目标

- 不扫描全链所有 Pair；
- 不实现 PancakeSwap V3、StableSwap、Infinity、Smart Router 聚合或 mempool；
- 不实现聚类、新元素正式注册、自动身份识别、LLM 推理；
- 不进行实盘或自动回测交易；
- 不把 GeckoTerminal 的排名当成链上事实；排名必须标明 provider 与采样时间；
- 不在服务端存储 API key、钱包、Cookie 或用户个人数据。

## 3. 现状证据与架构选择

当前项目只有纯本地领域对象和固定 fixture。领域契约已经固定 `EventPosition`、`data_cutoff`、风险四态、paper-only 和 `PredictionResult`；新适配器必须把外部事件映射到这些对象，而不是绕过契约。

### 方案 A：纯 RPC 扫描

从 PancakeSwap Factory 枚举 Pair，再对大量 Pair 做 `eth_getLogs`，自行计算交易量并排序。

- 优点：数据路径最接近链上原始事实；
- 缺点：Pair 枚举和历史日志量大，公共 RPC 限流/禁用 `eth_getLogs`，本地 MVP 无法稳定展示“Top volume”；
- 结论：暂不采用。

### 方案 B：Provider-assisted discovery + RPC verification（推荐）

使用 GeckoTerminal 的 BSC network/DEX pool ranking 发现候选池，再通过配置的 BSC RPC 检查 chain ID、latest block、池地址和可用的 Swap logs；对已选池生成本地 run snapshot。

- 优点：能在本地快速看到 Top-volume 全流程，同时保留链上核验边界；
- 缺点：排名依赖外部索引器，RPC 日志能力可能不可用；
- 缓解：UI 显示 `discovery_provider`、`observed_at`、`data_age_seconds`、`rpc_verified` 和明确的 `not_supported/unknown`。

### 方案 C：付费链上索引器

使用带历史日志、交易和 token 风险接口的专用 provider。

- 优点：稳定性和历史查询能力最好；
- 缺点：需要账号/API key，超出当前本地 MVP 的授权和成本范围；
- 结论：保留为后续 adapter，不写死接口。

## 4. 推荐数据流

```text
WebUI request
  -> run_id + config snapshot
  -> discovery: GeckoTerminal top pools on BSC
  -> filter: exact DEX / V2-compatible / liquidity & volume guards
  -> RPC capability probe: chainId, latest block, getLogs support
  -> selected-pool fetch: pool snapshot + recent trades/logs
  -> canonical EventEnvelope + AMMV2SwapEvent
  -> MarketState + ObservedFact + Evidence
  -> feature snapshot at data_cutoff
  -> role/action/intent PredictionResult
  -> risk/capability fail-closed Decision
  -> JSONL audit events + WebUI response
```

重要边界：provider 当前 pool snapshot（当前价格、当前流动性、当前储备）只能用于展示和候选排序。若它没有可证明的区块/交易/日志位置，不得写入 cutoff 前的 `MarketState`、feature 或 posterior；严格特征只能来自带可用 `EventPosition` 的 RPC 事件/状态读取，否则为 `unknown`/`insufficient_data`。

## 5. 模块边界

建议新增以下边界，暂不修改现有 Coinman 项目：

- `src/market_intent_inference/adapters/geckoterminal.py`：只负责 discovery/pool/trades HTTP，解析为 provider DTO；
- `src/market_intent_inference/adapters/bsc_rpc.py`：只负责 JSON-RPC allowlist 方法 `eth_chainId`、`eth_blockNumber`、`eth_getLogs`、必要的只读 `eth_call`；
- `src/market_intent_inference/application/bsc_pipeline.py`：编排 run、截止点、标准化和推理；
- `src/market_intent_inference/application/run_store.py`：以 run_id 记录脱敏 JSON/JSONL 产物；
- `src/market_intent_inference/interfaces/web.py`：本地 HTTP API 与静态页面服务；
- `web/index.html`、`web/app.js`、`web/styles.css`：无构建依赖的本地 dashboard；
- `tests/fixtures/`：脱敏 provider/RPC fixture，网络测试默认关闭，仅通过显式 smoke 命令启用。

## 6. WebUI 交互与接口

页面区域：

1. 顶部状态：BSC chain ID、RPC URL 是否配置、latest block、provider 更新时间；
2. Top pools 表：rank、base/quote、pool、24h volume、liquidity、24h tx count、provider age、RPC verified；
3. 选择区：`top_k`（默认 3，可选 1–10）、DEX filter、lookback blocks、refresh；
4. 分析区：selected pool 的 reserves/price/impact、Swap 方向、buy/sell counts、OFI-like net flow、事件位置；
5. 推理区：role/action/intent posterior、calibration、abstain reason、risk fields；
6. 全流程 run 区：run_id、各阶段耗时、成功/降级/失败阶段、产物下载链接。

只读 API：

- `GET /api/health`
- `GET /api/bsc/pools?top_k=3&dex=pancakeswap_v2`
- `POST /api/bsc/analyze`，body 包含 `pool_addresses`、`lookback_blocks`、`paper=true`、`mode=spot_long_only`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/events`

API 不接受私钥、交易 calldata、写链参数；所有未知/不支持信息显式返回。

## 7. 数据与截止点

- discovery provider 的 ranking time 只用于候选排序，不直接成为链上 feature；
- 分析确定 `decision_position=(block, tx, log)`，仅使用不晚于该位置且具备可证明时间的事件；
- RPC 返回的 latest block 要先扣除可配置 confirmation lag，再作为 `decision_position.block_number`；
- 同一 block 内按 transaction index/log index 排序；同一位置之后事件不得进入 feature；
- provider trades 无法证明原始区块位置时只作为弱证据/展示，不进入严格 posterior 训练样本；
- RPC `eth_getLogs` 失败、端点禁用或超过范围时进入 `not_supported`/`source_unavailable`，不伪造空交易，也不把 provider 不可用误标为 `future_data`；只有事件位置/时间确实晚于 cutoff 才使用 `future_data`。

## 8. 交易量最高池的定义

MVP 的“最高交易量”定义为：指定采样时刻，指定 BSC 网络和精确 DEX filter 下，provider 返回的 `h24_volume_usd_desc` 前 K 池。UI 必须显示：

- `ranking_provider=geckoterminal`；
- `ranking_metric=h24_volume_usd`；
- `ranking_observed_at`；
- `provider_rank`；
- `rpc_verified`；
- `selection_filters`。

这避免把 provider 排名误称为完整链上重算结果。后续可加入纯 RPC historical-volume rank 作为第二种可比较定义。

Provider 返回的 `dexId` 不能在设计中硬编码为 `pancakeswap_v2`。实现必须先读取 provider 的 BSC DEX 列表，按配置的名称/地址映射选择目标 DEX，并在候选池上执行链上核验：chain ID=56、池合约只读调用 `token0()`/`token1()`/`getReserves()`（必要时 `factory()`）、Pair `Swap` ABI 事件可解码、且 factory/router 映射符合配置。核验失败时保留候选展示，但不得进入严格 V2 分析。

## 9. 错误、降级和安全

- HTTP timeout/429：指数退避，有限重试；最终 `source_unavailable`；
- RPC chain ID 非 56：`unsupported_venue`；
- `eth_getLogs` 不支持：保留 provider 展示，严格分析输出 `abstain/insufficient_data` 或 `no_trade/unsupported_venue`，不使用 `future_data`；
- pool 非 V2-compatible、事件 ABI 不匹配、token decimals 缺失：`quality_failed`；
- 风险字段 unknown/not_supported：只输出 no-trade，不输出可执行买卖建议；
- 所有 API 默认 localhost；不绑定公网地址；不包含 CORS 放开、认证和钱包连接；
- 日志只记录地址、区块位置、provider、错误码、耗时和 run_id；不记录密钥、Cookie、完整 RPC headers 或自由文本隐藏推理。

## 10. 验收标准

1. 本地启动后能打开 dashboard；
2. 在网络可用且 provider 成功时，显示至少 3 个 BSC Top-volume 候选池；
3. 至少一个候选池能完成详情、RPC 能力探测、事件标准化和推理展示；
4. RPC logs 不可用时 UI 明确显示降级，不伪造“已核验”；
5. 所有结果带 run_id、decision_position/data_cutoff、provider/rpc source、quality 和 reason codes；
6. 离线 fixture 测试不依赖网络；显式 smoke 测试才访问外部服务；
7. 没有写链、钱包、私钥、交易广播路径；
8. Coinman 目录不被读写、导入或共享。

## 11. 未决问题（批准前）

- 默认 RPC 是否使用 BSC 官方公共端点，还是由用户提供支持 `eth_getLogs` 的 RPC URL？
- 是否接受 GeckoTerminal 作为 Top-volume discovery provider，还是必须完全由链上 RPC 重算排名？
- 默认展示 top 3 还是 top 5？
- 本地 run snapshot 保留多久、是否需要 CSV/JSON 下载？

推荐默认：官方 BSC RPC URL 可配置、GeckoTerminal keyless discovery、top 3、JSON snapshot、默认 30 秒缓存；任何无法核验的部分保留 unknown/abstain。
