# 首个领域内核实现计划独立审查

- 审查日期：2026-07-25
- 审查对象：`docs/plans/implementation-plan-20260725.md`
- 结论：不通过，已按意见修订计划并等待重新审查

## 主要问题

原计划缺少领域标签、时间防泄漏、安全拒绝、完整文件范围、Harness/Graphify 验证和当前目录无 Git 元数据的现实处理。

## 修订要求

计划必须明确：

1. 角色、操作、行为假设、潜在意图、风险状态和完整时间语义；
2. 预测时点、同区块后续事件、数据截止和未来条件频数测试；
3. `paper=false`、未知风险和不支持能力的 no-trade 测试；
4. fixture、领域测试、推理测试、Harness 规格、隔离检查和 Wiki/Graphify 生成文件范围；
5. 当前新目录无 Git 元数据时不把 Git diff 当作通过证据，而使用文件清单、哈希和现有 Coinman 零修改检查；
6. Ruff、compileall、pytest、Harness、Graphify 和 Wiki 验证的强制执行与失败语义。
