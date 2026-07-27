# Data Lake Contract

服务器端数据目录按生命周期分层，不把原始链上数据直接覆盖成训练特征：

```text
data/raw/        外部原始响应、Parquet、区块/日志快照，只追加不改写
data/bronze/     解析后的链、交易、receipt、log、Transfer、DEX 事件
data/silver/     标准化 EventEnvelope、PoolSnapshot、WalletSequence
data/gold/       训练样本、标签、特征和回测输入
data/manifests/  查询、区块范围、来源、版本、checksum、完整性报告
```

所有表必须包含 `chain_id`、`source`、`ingested_at`、`block_number`、`transaction_index`、`log_index` 或明确的 `position_missing_reason`。训练样本还必须包含 `decision_time`、`horizon_end`、`data_cutoff`、`feature_version`、`label_version` 和 `split_id`。
