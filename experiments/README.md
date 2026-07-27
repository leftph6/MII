# Experiments

每个实验必须有独立配置、run ID 和结果摘要。建议命名：

```text
experiments/configs/<experiment>.yaml
experiments/runs/<run_id>/
```

结果至少保存数据版本、代码版本、特征/标签/模型版本、随机种子、训练/验证/测试区块范围、未见 token 列表、指标、成本假设、失败原因和产物路径。不要用单次收益或单一 Sharpe 宣称 Alpha。
