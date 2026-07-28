# BSC WebUI 代码审查修复复审

日期：2026-07-27

## 反馈处理

- 接受并修复 safe-block 泄漏：`verify_pair(..., state_block=...)` 使用 confirmation-lag 后的 block tag；新增探针测试。
- 接受并修复未知/未来 timestamp 进入特征：只有不晚于 safe-block time 的事件进入严格 features；缺失时间戳保留 recent_swaps 但输出 abstain/insufficient_data。
- 接受并修复 partial logs 语义：非 range 错误不再二分；递归左半结果保留并标记 `last_logs_complete=false`；pipeline 记录 failure_count/reason。
- 接受并修复非法 timestamp、RPC/curl 响应大小上限、RunStore append-only 和 symlink containment。
- 接受并修复 paper-only 配置/API schema：拒绝 `paper=false`、未知字段、非整数/越界参数、非法 pool address 与执行相关字段。
- 接受并修复结构化日志公共字段、HTTP 错误 detail 脱敏、Health RPC 降级状态、前端动态内容转义及候选池表头错位。
- provider DEX mapping 明确区分 `provider_id+configured_v2` 与 `bootstrap_snapshot`；bootstrap 仅为 discovery 降级来源，严格分析仍要求链上 factory/router 核验。

## 当前验证

- `pytest`: 35 passed；
- compileall、Ruff、JS syntax、security boundary：通过；
- Graphify：55 files / 537 nodes / 1506 relations，build/update/validate/query 通过；
- Harness：`bsc-webui-20260727-final` 评测通过；Research Wiki：21 个实体、11 条关系，校验通过；
- Coinman：实现前后两条只读 Git 元数据 stdout 与 baseline 逐字一致；
- live RPC 与真实 localhost socket 受当前环境限制：未配置 `BSC_RPC_URL`，沙箱禁止绑定监听端口；交接文档记录的 live smoke 保留。

## 结论

修复范围内的 P1 已关闭。bootstrap snapshot、免费 RPC `eth_getLogs` 可用性和 live localhost smoke 是已明确披露的运行环境限制，不伪装成实时数据可用性。
