# Research Resources

本目录保存本项目研究交接所需的论文、官方数据源和工具文档索引。论文 PDF 仅作为研究便利的本地副本；正式引用应以 `manifest.csv` 中的原始 URL、DOI 或出版方页面为准。

检索截止日期：2026-07-28。  
研究主题：市场微结构、AMM/DEX、角色与意图推理、条件概率、offline RL、市场仿真和 BSC 数据工程。

## 资源分层

### 已下载的核心论文

位于 `papers/`：

- `sirignano-cont-2018.pdf`：跨资产、跨时间的价格形成表示；支持共享微结构表示的研究假设。
- `deeplob-2018.pdf`：CNN + LSTM 的订单簿时序预测基线。
- `bdlob-2018.pdf`：带不确定性估计的 Bayesian DeepLOB。
- `flash-boys-2-0-2020.pdf`：DEX 交易排序、套利、PGA/MEV 风险。
- `abides-2019.pdf`：高保真多主体市场仿真框架。
- `d4rl-2020.pdf`：offline RL 数据集与评估问题。
- `cql-neurips-2020.pdf`：Conservative Q-Learning，处理 offline RL 分布外动作的代表方法。
- `finrl-2020.pdf`：金融 DRL 环境、约束和回测组织方式参考。
- `market-making-lob-rl-2023.pdf`：订单簿市场做市 RL 的状态、动作和奖励设计参考。

### 需要在线访问的资料

- BNB Chain JSON-RPC 与 `eth_getLogs` 能力说明；
- GeckoTerminal API 的网络、池排名、OHLCV 与 trades 文档；
- Dune BNB Chain raw/decoded/curated 数据目录；
- Bitquery BSC Parquet 导出；
- BNB Chain 全历史节点快照；
- Gymnasium、PettingZoo、FinRL、CORL、ABIDES 的代码和 API 文档。

## 数据使用建议

`GeckoTerminal` 适合发现候选池和提供排序快照，不应作为唯一的训练真相。训练 gold dataset 应优先由带 block/transaction/log position 的链上事件构成，并保存原始来源、抓取时间、区块范围、完整性和缺失原因。历史回填优先使用 Dune/Bitquery/自建 archive node；实时 RPC 只负责增量和验证。

## 版权和可复现性

下载文件不代表再分发权。上传 GitHub 前应检查每份 PDF 的许可证和所在平台的分发条款；代码仓库可以保留 manifest 和引用链接，必要时删除本地 PDF。所有实验记录应保存查询语句、访问日期、数据版本和 checksum。

已下载 PDF 的 SHA-256 位于 [`checksums.sha256`](checksums.sha256)，版权与公开仓库处理规则见 [`NOTICE.md`](NOTICE.md)。
