# 首个领域内核代码审查与修复复审

- 审查对象：首个领域内核切片
- 审查范围：领域契约、条件后验、事件可用性、paper-only 安全边界、Harness 与静态安全
- 初审结论：不通过；发现截止点可省略、空样本返回 None、后验类别/变量未闭合、未确认事件可入状态、对象级 paper-only 约束不足、映射可变等问题。
- 修复方式：每项确认问题先加入失败测试，再做最小修复；没有扩大到真实 BSC、网络、钱包或交易执行。
- 最终独立复审结论：通过，剩余阻塞项为零。

## 修复证据

- `conditional_posterior` 强制 `training_cutoff <= data_cutoff <= decision_position`；
- 无训练样本返回结构化 `Posterior(abstain=True, reason_codes=("insufficient_data",))`，不返回伪造均匀概率；
- `Posterior` 仅允许 `role/action/intent`，类别必须是对应固定枚举全集，条件键必须是合法 role/action；
- `build_prediction_result` 强制三后验顺序为 role/action/intent；
- 未确认或失败事件不生成状态改变事实；`PredictionContext` schema、EventPosition、布尔和有限数值均严格校验；
- `MappingProxyType` 防止风险和概率映射在构造后被修改；
- `paper=False` 不能构造 trade，首切片 VenueCapability 不能启用写链；
- 最终复审验证：14 passed、Ruff check/format 通过、compileall 通过、安全边界输出 `security_boundary_ok`、Harness validate/run 通过。
