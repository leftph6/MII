# BSC WebUI 设计独立审查（2026-07-26）

- 审查对象：`docs/design/bsc-webui-design-v0.1.md` 与 `docs/design/bsc-webui-log-schema-v0.1.md`
- 独立审查结论：总体方案基本一致，但修订前不允许进入实现。

## 必须修订的问题

1. Provider 当前 pool snapshot 没有可证明的区块位置，不能进入严格 cutoff 特征或 posterior，只能展示；设计已补充此边界。
2. `eth_getLogs` 不可用属于 `not_supported/source_unavailable`，不应误标为 `future_data`；设计已明确区分。
3. provider 的 DEX 标识不能直接假定为 `pancakeswap_v2`，必须读取 DEX 映射并用 RPC/ABI 只读调用核验 chain ID、Pair 方法和 Swap 事件；设计已补充。

## 已确认的安全边界

- 方案 B（GeckoTerminal discovery + BSC RPC verification）与当前官方接口资料基本一致；
- 不包含钱包、私钥、写链、交易广播或执行路径；
- ranking 不作为严格 feature，confirmation lag、区块内顺序和 cutoff 约束已纳入设计；
- 设计仍处于 `awaiting-review`，日志 schema 仍为 `draft`，待人类批准后才能进入实现计划。

## 修订后终审

- provider snapshot 仅展示，不进入严格 feature/posterior；
- `eth_getLogs` failure 使用 `not_supported/source_unavailable`，不使用 `future_data`；
- DEX/V2 必须通过 provider DEX mapping 与 RPC/ABI 只读核验；
- 终审结论：允许提交人类批准，尚未获得人类批准，因此尚不能实现。
