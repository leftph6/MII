# BSC WebUI 实现代码审查与验收复审

- 审查对象：BSC WebUI 只读闭环（adapters / pipeline / run_store / web / frontend）
- 审查范围：GeckoTerminal discovery、BSC RPC V2 核验、cutoff-safe Swap 特征、abstain/no-trade、脱敏审计、localhost WebUI、Graphify 前端展示
- 结论：通过；剩余阻塞项为零。

## 已关闭问题

1. `dex_id` 误切分导致 discovery `quality_failed`：改为只剥离 `bsc_` 前缀。
2. Swap `data` fixture 长度与解码器不一致：固定为 4×uint256=256 hex；并校验 Swap topic0。
3. RPC fingerprint 不再哈希含 userinfo/query 的原始 URL，只使用 scheme/host/has_userinfo。
4. provider ranking / volume 不进入严格 features；风险 `not_supported/unknown` 固定 `no_trade`；无标签时后验 abstain。
5. WebUI 拒绝 `paper=false`、写链参数与非 localhost 绑定；静态路径防穿越；可只读加载 `graphify-out`。

## 验证证据

见 `test-artifacts/bsc-webui/verification-20260726.md` 与 `harness-results/bsc-webui-20260726/REPORT.md`。
