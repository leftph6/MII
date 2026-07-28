# Coinman 隔离核对异常

- 核对对象：`/Users/mashengyu/Desktop/quant research/coinman-arbitrage-bot`
- 处理原则：本项目没有对该目录执行写操作，不恢复、不删除、不读取其代码或运行状态。
- 证据：初始 Git 元数据记录包含未跟踪 `app/prediction_strategy.py`；最终同一组 `git status --porcelain=v1` 与 `git diff --name-only` 输出中该项消失。
- 结论：这是任务期间的外部工作区变化，不能归因于本新项目；因此“Coinman 前后完全相同”验收项标记为未通过/外部阻塞，而新项目独立性仍已验证。
