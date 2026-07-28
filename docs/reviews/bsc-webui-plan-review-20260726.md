# BSC WebUI 实施计划独立审查

日期：2026-07-26

结论：`approved-for-implementation`

## 审查范围

审查了 `AGENTS.md`、已批准设计 `docs/design/bsc-webui-design-v0.1.md`、日志 schema `docs/design/bsc-webui-log-schema-v0.1.md`、实施计划、`evals/bsc-webui.yaml` 与 Coinman 隔离记录。

## 已闭合门禁

- discovery 缓存为进程内缓存，包含 config fingerprint，TTL 范围、失败不缓存和命中/过期/键隔离测试已明确；
- `decision_time` 来自 safe block timestamp；缺失 timestamp 的事件不得进入任何 feature、MarketState 或后验条件；
- Gecko DEX mapping 必须同时携带并校验 factory/router，且与固定 PancakeSwap V2 配置一致；
- URL、userinfo、query、fragment、Authorization、API-key-like 值及 fingerprint 的脱敏测试边界已明确；
- Harness YAML 已存在并声明 unit-tests、compile、security-boundary 三项可执行检查；Graphify 与 Research Wiki 命令已固定；
- Coinman 只允许两条 Git 元数据命令。早期 before 与后续复核出现外部状态差异，已原样记录；最新复核作为实现基线，最终 after 必须与之逐字一致。此最终 after 不能在实现前预先生成，故保留为不可跳过的交付门禁。

## 执行决定

允许进入 TDD 实现。实现代理不得读取或修改 Coinman；不得修改既有领域契约、旧测试、AGENTS 或既有设计正文。实现结束后若 Coinman 最终 after 与最新基线不同，则不得声称项目完成。
