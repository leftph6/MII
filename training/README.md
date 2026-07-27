# Training Framework

训练分三层，禁止跳过基线直接进入端到端 RL：

1. `supervised/`：观察操作分类、角色/意图弱监督、多任务序列模型、概率校准和 OOD/abstention。
2. `offline_rl/`：从事件轨迹训练受约束的 paper 决策策略，优先 BC、CQL、IQL，再比较 conservative policy improvement。
3. `multi_agent/`：在已校准的市场回放/AMM 仿真器中做多主体实验；只用于机制研究，不能把模拟收益当成真实 Alpha。

第一版建议使用 PyTorch + scikit-learn/CatBoost 基线 + DuckDB/Parquet；offline RL 可评估 CORL/CQL/IQL，环境接口使用 Gymnasium，真正的多主体环境使用 PettingZoo。ABIDES 主要针对 CLOB，BSC AMM 应使用自定义事件驱动 CFMM 环境。
