# BSC WebUI 数据源核对（2026-07-26）

## BNB Smart Chain 官方 RPC

- 主网 chain ID 为 `56`（十六进制 `0x38`）。
- 官方文档列出多个公共 RPC，并提示主网部分端点禁用 `eth_getLogs`；频繁拉取日志应使用支持日志查询的第三方 RPC 或 WebSocket。
- 因此适配器必须把 RPC URL 配置化，启动时执行 `eth_chainId` 能力探测；日志不可用时输出 `not_supported`，不能假装链上核验成功。

来源：

- https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/
- https://docs.bnbchain.org/bnb-smart-chain/developers/wallet-configuration/

## Top-volume pool discovery

- GeckoTerminal keyless public API 的 onchain 根为 `https://api.geckoterminal.com/api/v2`。
- 网络 Top pools 接口支持 `sort=h24_volume_usd_desc`，返回最多 20 个池/页；BSC 网络标识使用 `bsc`。
- 具体池接口可返回价格、流动性、交易量等；池 trades 接口可返回过去 24 小时最近交易，文档注明最多 300 条。
- 公开接口有 IP 级限流，429 时需要指数退避；UI 必须展示 provider、采样时间和数据新鲜度。

来源：

- https://docs.coingecko.com/docs/keyless-public-api
- https://docs.coingecko.com/reference/top-pools-dex
- https://docs.coingecko.com/reference/pool-address
- https://docs.coingecko.com/reference/endpoint-overview

## PancakeSwap V2 边界

- PancakeSwap Router V2 的 BSC 地址由官方文档列为 `0x10ED43C718714eb63d5aA57B78B54704E256024E`。
- 本切片只接受发现结果中可识别的 PancakeSwap V2-compatible constant-product pool；不接 Smart Router 聚合、V3、StableSwap、Infinity 或写链。

来源：

- https://docs.pancakeswap.finance/to-delete/smart-contracts/pancakeswap-exchange/v2-contracts/router-v2
- https://docs.pancakeswap.finance/trade/pancakeswap-exchange/smart-router-v2
