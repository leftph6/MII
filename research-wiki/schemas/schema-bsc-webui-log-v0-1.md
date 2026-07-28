---
id: schema-bsc-webui-log-v0-1
type: schema
title: BSC WebUI structured event schema v0.1
status: approved
tags:
- bsc
- logging
created_at: '2026-07-25T16:12:45Z'
updated_at: '2026-07-25T16:30:43Z'
---

# BSC WebUI 结构化事件 Schema v0.1

状态：`approved`

每行一个 JSON 对象，写入 `artifacts/runs/<run_id>/events.jsonl`。这是本地审计产物，不等同于生产日志平台。

公共字段：

- `timestamp`：UTC ISO-8601；
- `event_name`：`web.request`、`bsc.discovery`、`bsc.rpc_call`、`bsc.normalize`、`inference.prediction`、`run.completed`、`run.failed`；
- `schema_version`：`bsc_webui_event.v0.1`；
- `level`：`info|warning|error`；
- `service`、`module`、`operation`；
- `run_id`、`trace_id`、`parent_id`；
- `status`：`started|succeeded|degraded|failed`；
- `duration_ms`、`attempt`、`error_code`、`retryable`；
- `config_hash`、`code_version`、`data_version`。

业务字段只保存：provider 名称、chain_id、pool/token 地址、block/tx/log 位置、请求范围、返回数量、质量、missing/reason code、RPC method、HTTP status 和脱敏错误类型。禁止保存 API key、Authorization、Cookie、私钥、完整 headers、完整 raw response 和隐藏推理文本。

幂等键：`run_id + event_name + operation + attempt`。重复事件不覆盖原始事件；重试追加新 attempt。日志写入失败不改变 paper/no-trade 语义，记录内存计数并在 `run.completed` 中标记 `audit_degraded=true`。
