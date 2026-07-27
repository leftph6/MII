# Experiment Configs

配置文件应把数据、标签、模型、策略和执行成本分开：

```yaml
data: {source: "[DATA_SOURCE]", chain_id: 56}
split: {train_cutoff: "[BLOCK]", validation_cutoff: "[BLOCK]", test_cutoff: "[BLOCK]"}
model: {feature_version: "[VERSION]", label_version: "[VERSION]", seed: 0}
policy: {mode: "spot_long_only", paper: true}
costs: {fee_bps: "[VALUE]", gas_model: "[MODEL]", slippage_model: "[MODEL]"}
```

不要把 RPC URL、API token、私钥或账号写入配置文件；只允许写环境变量名。
