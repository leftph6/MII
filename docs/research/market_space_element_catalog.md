# 市场空间元素基本集合（研究草案）

检索日期：2026-07-25（Asia/Singapore）。本表是初始 ontology，不是最终标签。元素分为“直接观测”“派生特征”“弱监督标签”，并要求保存 as-of 时间和来源。

## 1. CLOB/传统电子市场

| 类别 | 基本元素 | 备注 |
|---|---|---|
| 价格 | bid、ask、mid、microprice、last、OHLC、收益 | 记录报价时间与成交时间 |
| 交易成本 | spread、有效 spread、手续费、冲击成本 | 与订单大小绑定 |
| 深度 | 各档数量、累计深度、深度斜率、深度不平衡 | 多档比单档更稳健 |
| 订单事件 | 新挂单、撤单、改单、成交、部分成交 | 需要事件级时间顺序 |
| 订单流 | buy/sell volume、aggressor imbalance、OFI、累计 delta | OFI 与深度共同决定短期价格冲击 |
| 队列 | queue position、订单寿命、成交概率、撤单率 | 适用于有队列的 CLOB |
| 动态流动性 | spread 恢复、深度恢复、扫单后重建、流动性消失 | 可刻画冲击后的韧性 |
| 毒性/信息 | VPIN 类流量毒性、异常成交、潜在知情交易概率 | 只能作为估计量，不是身份证明 |
| 状态 | 波动、趋势、跳跃、流动性 regime、交易时段 | 作为条件状态而非意图 |

Cont、Kukanov 和 Stoikov 的研究将短时价格变化与 order-flow imbalance 和市场深度联系起来；相关论文和摘要见：[The Price Impact of Order Book Events](https://arxiv.org/abs/1011.6402)。DeepLOB 说明 LOB 的空间结构和时间依赖可用于短期预测，但本项目仍要求先建立可解释基线：[DeepLOB](https://arxiv.org/abs/1808.03668)。

## 2. AMM/DEX

| 类别 | 基本元素 | 备注 |
|---|---|---|
| 池状态 | token0/token1、reserve0/reserve1、TVL、LP supply | 取自链上状态或事件 |
| 曲线 | constant product/其他 CFMM 参数、报价曲线、边际价格 | 不能用 CLOB spread 替代 |
| 执行质量 | quote、price impact、滑点、minimum received、路由长度 | 必须按订单大小计算 |
| 交易事件 | Swap、Sync、PairCreated、Mint、Burn | 识别买卖、储备变化和 LP 变化 |
| 资金事件 | Transfer、Approval、mint/burn token、transfer tax | BEP-20 事件是基础观测 |
| 流动性 | 加 LP、减 LP、LP concentration、锁定/解锁、池迁移 | 与 rug/退出风险相关 |
| 区块微结构 | block number、tx index、gas price、priority fee、失败/回滚 | 区块内顺序是 BSC 的重要状态 |
| MEV | sandwich 候选、arbitrage bundle、backrun、priority gas auction | 必须使用候选/概率表述 |
| 合约风险 | owner 权限、mint、pause、blacklist、maxTx、税费、可卖出性 | 风险过滤，不是安全证明 |
| 账户状态 | 余额、成本基础估计、持仓集中度、资金流入/流出、地址图 | 不能直接推断真实身份 |

Uniswap v2 白皮书和官方说明将池子、储备和恒定乘积机制作为 AMM 的核心；见：[Uniswap v2 Core](https://blog.uniswap.org/whitepaper.pdf) 和 [How does the Uniswap protocol work?](https://support.uniswap.org/hc/en-us/articles/8671577468813-How-does-the-uniswap-protocol-work)。BSC 的 BEP-20 基础事件包括 Transfer 和 Approval；见：[BEP-20](https://github.com/bnb-chain/BEPs/blob/master/BEP20.md)。

## 3. 参与者与角色元素

| 角色候选 | 可观测行为元素 | 主要混淆 |
|---|---|---|
| LP/做市 | 提供/撤出流动性、库存变化、被动交易、费用收入 | 项目方流动性管理 |
| 套利者 | 跨池价差、短持仓、低方向暴露、同区块多跳 | MEV 与普通套利 |
| 动量投机者 | 追涨、短持仓、成交方向持续、价格冲击敏感 | 信息交易者 |
| 逆势交易者 | 下跌买入、上涨卖出、均值回归 | 逢低吸筹 |
| 早期/项目方资金 | 早期获得、集中持仓、向池/交易所转移 | 早期投资者 |
| 被迫交易 | 借贷/清算、快速风险收缩、外部资金压力 | 主动止损 |
| MEV 候选 | 区块位置、Gas、前后夹持、同区块回转 | 套利者 |
| 基础设施 | 路由、桥、交易所热钱包、合约地址 | 资金归集 |
| 未知/混合 | 行为不稳定或证据不足 | 所有角色 |

链上行为研究表明，交易量、交易节奏和交易网络结构可以用于刻画经济代理，但不能直接对应真实线下身份；见：[Characterizing key agents in the cryptocurrency economy](https://link.springer.com/article/10.1140/epjds/s13688-021-00276-9)。

## 4. 意图候选元素

| 意图 | 支持证据 | 反证/限制 |
|---|---|---|
| 吸筹 | 分批买入、价格冲击控制、持仓增加、卖压吸收 | 也可能是短期动量 |
| 派发 | 分批卖出、持仓减少、对池子持续施压 | 也可能是止盈 |
| 止盈 | 前期持仓收益、价格扩张后减仓、风险下降 | 成本基础通常不完整 |
| 止损 | 大幅不利价格后快速退出、波动/风险触发 | 可能是被迫卖出 |
| 套利 | 同区块跨池/跨市场往返、净方向暴露小 | 需要多市场数据 |
| 做市再平衡 | LP/库存变化与价格方向相反或受费用驱动 | 需识别 LP 头寸 |
| 对冲 | 相关资产反向交易、净风险下降 | 相关性时变 |
| 流动性退出 | Burn、LP 转移、池深度骤减 | 可能是迁移到新池 |
| MEV | 交易前后夹持、Gas 优先级、区块内配对 | 只能输出候选概率 |
| 项目方退出风险 | 关联地址向池出售、权限变化、LP 撤出 | 地址关联不总是可靠 |
| 诱导/操纵假设 | 非自然交易序列、异常集中、社交扩散与交易联动 | 不能视为已证实 |

## 5. 新元素发现计划

将标准元素编码为时序和图特征，使用层次聚类、HDBSCAN 或图社区发现产生候选元素。每个候选必须通过：

1. 簇内行为相似度与簇间差异；
2. 时间滚动稳定性；
3. 未见 token/市场阶段迁移测试；
4. 人类可解释命名；
5. 与现有元素的增量信息量；
6. 对策略表现和误报率的影响；
7. 防止使用未来事件的标签审计。

新元素先进入 `candidate`，由研究记录和人工审查后才可升级为 `approved`。

## 6. 关键限制

- BSC AMM 没有传统 CLOB 的完整订单簿和公开挂单队列；
- mempool 可见性取决于节点和服务，历史数据通常不完整；
- 地址聚类不是身份识别；
- 意图标签天然存在不可识别性；
- meme coin 的合约风险、交易税和流动性变化会破坏简单回测；
- 高概率预测不等于高期望收益，必须经过成本和风险层。

链上交易排序和 MEV 的系统性影响见：[Flash Boys 2.0](https://arxiv.org/abs/1904.05234)。BSC 官方文档说明主网 Chain ID 为 56，并提供 JSON-RPC/日志访问边界；见：[BSC JSON-RPC endpoints](https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/) 和 [Ethereum JSON-RPC](https://ethereum.org/developers/docs/apis/json-rpc/)。
