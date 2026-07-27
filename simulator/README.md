# Event-Driven AMM Simulator

这里放 BSC PancakeSwap V2-compatible constant-product 的纸面回放与反事实模拟器。

模拟器必须显式建模：储备与 fee、token decimals、区块内顺序、确认延迟、Gas、滑点、token tax、失败/ revert、流动性上限、交易参与率和观察到的其他参与者行为。没有这些机制时，RL 只是在静态价格序列上优化一个虚假的奖励函数。

ABIDES 的消息驱动思想可借鉴，但不能直接把其 CLOB 撮合模型当成 AMM；AMM 的价格由池子曲线和交易顺序决定。
