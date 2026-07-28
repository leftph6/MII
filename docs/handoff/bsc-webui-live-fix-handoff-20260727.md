# BSC WebUI 实装修复交接文档（2026-07-27）

> 给下一个 agent：本文记录「空壳分析 → 切实可用」这一轮的根因、修复、验收状态与未决事项。先读本文，再读 `AGENTS.md`。

## 1. 当前结论（一句话）

BSC localhost WebUI 已从 `pools: []` / `quality: source_unavailable` 空壳，修到可展示候选池 CA/基本信息，并能产出 RPC 核验、微结构特征、recent_swaps 与 abstain/no-trade 推理结果；离线门禁 30 tests 绿；WebUI 默认监听 `http://127.0.0.1:8765`。

## 2. 用户原始问题与验收标准

用户 run 示例（空壳）：

- `run_id`: `bsc-1785062885-fe369436`
- `pools: []`
- `quality: source_unavailable`
- 候选池无数据、分析区无结果

**必须达到：**

1. 候选池表能看到具体交易对 / pool CA / base·quote 基本信息  
2. 分析区有核验与特征（reserves、mid_price、swap 计数等），不是空对象  
3. 推理区有 decision / abstain·no-trade / reason_codes  
4. paper-only，无写链、无钱包资金操作  
5. 不触碰 `coinman-arbitrage-bot`

## 3. 根因清单（已确认）

| # | 根因 | 现象 |
|---|------|------|
| A | 本机 `http.client` 访问 GeckoTerminal 经常 SSL/超时 | 服务端 discovery 失败 |
| B | 真实 Gecko DEX API **不返回** `factory_address`/`router_address`；token 在 `included`+`relationships` | 旧解析建不出 mapping / 缺 CA 元数据 |
| C | 默认公共 RPC（如 bsc-dataseed）对 `eth_getLogs` 拒连/超时；publicnode 常要 archive | verify 偶发成功，logs 失败 |
| D | `getLogs` 失败后无脑二分拆分到单块 | O(n) RPC 爆炸，分析卡住 90s+ |
| E | `block_timestamp` 失败会整段丢掉已拿到的 Swap | `swaps=0`、features 被清空 |
| F | 无 Swap / 缺 wall-clock 时把 `features={}` | UI 分析区空白，像空壳 |
| G | 服务端单次请求里死等 Gecko live（长超时+重试） | `/api/bsc/pools`、`/analyze` 被拖死 |

## 4. 已落地修复（按层）

### 4.1 Discovery（Gecko + bootstrap）

**文件：** `src/market_intent_inference/adapters/geckoterminal.py`  
**数据：** `src/market_intent_inference/adapters/discovery_bootstrap.json`

- 本地固定 Pancake V2 factory/router（MVP 不依赖 Gecko 返回 factory）
- 解析 `included` 中的 base/quote token address + symbol
- live 失败 → `discovery_bootstrap.json` 回退
- 新增 `prefer_bootstrap=True`：服务端可跳过 live，避免卡住  
  - `scripts/run_webui.py` **默认** `prefer_bootstrap=True`
  - 浏览器端仍可直连 Gecko discovery（CORS 成功则用 live）

### 4.2 RPC（BSC read-only）

**文件：** `src/market_intent_inference/adapters/bsc_rpc.py`  
**启动：** `scripts/run_webui.py`

- 默认主 RPC：`https://1rpc.io/bnb`
- 备用：`https://bsc.publicnode.com`、`https://bsc-rpc.publicnode.com`
- 传输：优先 **curl --http1.1**（比 Python SSL 稳），粘性成功端点
- `getLogs`：短超时；最多试 2 个端点；**仅在“range too large”类错误时有限二分**，禁止 auth/archive/rate-limit 触发拆分爆炸
- `block_timestamp` 软失败 → `event_time=None`，**不丢 Swap**
- `chain_id` 缓存；`fallback_urls` 可选
- `log_chunk_blocks` 默认 40（1rpc 近期窗口友好）

环境变量：

```text
BSC_RPC_URL=https://1rpc.io/bnb
BSC_RPC_FALLBACKS=https://bsc.publicnode.com,https://bsc-rpc.publicnode.com
```

### 4.3 Pipeline（分析编排）

**文件：** `src/market_intent_inference/application/bsc_pipeline.py`

- 默认 `lookback_blocks=40`
- pair **一旦 rpc_verified**：始终产出 reserve 类 features（即使 lookback 内 0 swap 或 getLogs 失败）
- features 使用全部 block-ordered swaps（不强制要求 `event_time`）
- `recent_swaps` 展示最近最多 5 条（含无时间戳）
- getLogs 失败：保留 verification + reserve features，`reason_codes` 带失败原因，decision abstain
- safe_block 探测失败：仍返回已发现 pools（降级，非空壳）
- 决策仍 fail-closed：无校准标签 → `abstain_no_labels` / risk `not_supported` → `no_trade`；缺数据 → `abstain`

### 4.4 WebUI

**文件：** `web/index.html`、`web/app.js`、`web/styles.css`、`src/market_intent_inference/interfaces/web.py`

- 候选池：pair、完整 CA、base/quote symbol+address、volume/liquidity
- 分析区：verification、features、`recent_swaps` 表、`error_detail`
- 推理区：decision / prediction / decision_time / horizon / feature snapshot
- 浏览器优先直连 Gecko；失败则服务端/bootstrap
- `ThreadingHTTPServer`；仅绑定 `127.0.0.1`

## 5. 关键文件清单

```text
src/market_intent_inference/adapters/geckoterminal.py
src/market_intent_inference/adapters/discovery_bootstrap.json
src/market_intent_inference/adapters/bsc_rpc.py
src/market_intent_inference/application/bsc_pipeline.py
src/market_intent_inference/interfaces/web.py
scripts/run_webui.py
web/app.js
web/styles.css
web/index.html                    # 若本地有改动一并核对
tests/test_bsc_rpc.py
tests/test_bsc_pipeline.py
tests/fixtures/...                # 既有 gecko/rpc fixtures
```

相关既有设计（勿重复造轮）：

- `docs/design/bsc-webui-design-v0.1.md`
- `docs/plans/bsc-webui-implementation-plan-20260726.md`
- `docs/reviews/bsc-webui-code-review-20260726.md`
- `test-artifacts/bsc-webui/verification-20260726.md`
- `AGENTS.md`（不变量与隔离规则）

## 6. 如何启动与验收

### 启动

```zsh
cd "/Users/mashengyu/Desktop/quant research/market-intent-inference"
# 可选：export BSC_RPC_URL="https://1rpc.io/bnb"
PYTHONPATH=src conda run -n codex-engineering python scripts/run_webui.py
```

打开：http://127.0.0.1:8765  
硬刷新后：加载候选池 → 运行分析。

### 离线门禁（必须绿）

```zsh
python3 -m pytest -q
python3 -m compileall -q src tests
python3 -m ruff check src tests
python3 -m ruff format --check src tests
conda run -n codex-engineering python scripts/check_security.py
# wiki（若环境有）：
# conda run -n codex-engineering research-wiki validate ./research-wiki
```

交接时状态：**30 passed**；ruff / security 通过。

### Live 冒烟（建议）

```zsh
curl -sS http://127.0.0.1:8765/api/health
curl -sS 'http://127.0.0.1:8765/api/bsc/pools?top_k=3'
curl -sS -X POST http://127.0.0.1:8765/api/bsc/analyze \
  -H 'Content-Type: application/json' \
  -d '{"paper":true,"mode":"spot_long_only","top_k":2,"lookback_blocks":40,"confirmation_lag":3,"pool_addresses":["0xd926c15150afc0301eb81b68ea3bc81e3f1adba3"]}'
```

成功样例特征：

- `ranking_provider`: `geckoterminal_bootstrap` 或浏览器 live
- `quality`: `derived`
- pool：`rpc_verified: true`，`features.mid_price` / `reserve*` 非空
- 有成交时：`features.swap_count > 0`，`recent_swaps` 非空
- decision：`abstain` 或 `no_trade`（paper + 未校准，预期）

近期成功 run 目录示例：`artifacts/runs/bsc-1785088195-4f9c1925`

## 7. 架构与行为不变量（下一轮不要破坏）

1. paper-only；`paper=false` 必须拒绝；无写链/私钥/广播  
2. chain ID **仅 56**；仅 Pancake V2 constant-product  
3. 特征 `as_of <= decision_time`；预测带 decision_time / horizon_end / target / event_position / data_cutoff  
4. 角色是行为假设，意图是潜变量；`verified` ≠ 真实身份/意图  
5. risk：`known_true|known_false|unknown|not_supported`；未知不当安全  
6. 与 `coinman-arbitrage-bot` **零共享**（代码/DB/.env/venv/凭据）  
7. 服务端 discovery 默认 bootstrap-first；不要把长超时 Gecko live 重新塞回请求关键路径  
8. `getLogs` 失败处理：**禁止**对非 range 错误做深度二分

## 8. 已知限制 / 下一轮可做

按优先级建议：

1. **刷新 bootstrap**  
   - `discovery_bootstrap.json` 是快照；高波动 meme 池排名会过期  
   - 可用浏览器 live discovery，或写只读脚本定期刷新（仍禁止碰 coinman）

2. **getLogs 稳定性**  
   - 免费 RPC 会限流；偶发 `source_unavailable` 但应仍有 reserve features  
   - 可注册免费带 logs 的 RPC（Ankr 等需 key），用 env 注入，**密钥只进环境变量**

3. **服务端 live Gecko（可选）**  
   - 现 prefer_bootstrap；若要服务端 live，应用 curl 传输 + 超时 ≤5s + retries=0 + bootstrap 回退

4. **UI/产物**  
   - 多池并行分析超时提示  
   - 把本交接摘要同步进 research-wiki / graphify（若流程要求）  
   - 更新 `test-artifacts/bsc-webui/verification-*.md` 记一次 live 验收

5. **不要做（超出当前切片）**  
   - V3 / StableSwap / mempool / 聚合路由  
   - 聚类正式化、写链执行、钱包授权  
   - 把 provider volume 泄漏进交易特征（已有测试守护）

## 9. 给下一 agent 的建议工作流

1. 读本文 + `AGENTS.md` + `docs/design/bsc-webui-design-v0.1.md`  
2. 跑离线门禁确认基线绿  
3. 启动 WebUI，浏览器硬刷新验收候选池 + 分析  
4. 若空壳复现：先看 `quality` / `reason_codes` / `error_detail` / `rpc.active_rpc_host`，再查 getLogs 是否爆炸或 Gecko 是否又阻塞  
5. 改代码后：pytest + ruff + security；live 再冒烟一次  
6. 需要提交时等用户明确要求（本仓交接时 **不是 git repo** 或需再确认）

## 10. 快速定位口令

- 候选池空 → gecko live 挂了？bootstrap 是否加载？前端是否走了 `/api/bsc/pools`？  
- 有池无分析 → analyze 是否卡在 getLogs？看进程里是否大量 `curl ... eth_getLogs`  
- verified 但 swaps=0 → lookback 内确实无 Swap，或 getLogs 失败（应仍有 mid/reserves）  
- `quality: source_unavailable` 且 `pools: []` → discovery/RPC 探测在进循环前失败（旧 bug；现应尽量保留 pools）

---

**交接日期：** 2026-07-27  
**切片：** BSC WebUI paper-only MVP（本地、无写链）  
**状态：** 功能可用，可继续增强稳定性与 bootstrap 新鲜度  
