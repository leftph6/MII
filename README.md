# Market Intent Inference

面向金融市场微结构的角色—操作—意图概率推理研究项目。

当前状态：BSC PancakeSwap V2-compatible paper-only WebUI MVP 已完成；训练数据湖、条件后验学习、离线强化学习和多主体仿真是下一阶段服务器实验工作。项目与 `coinman-arbitrage-bot` 完全隔离。

## 快速入口

- WebUI：`web/index.html`、`web/app.js`、`web/styles.css`
- BSC 启动入口：`scripts/run_webui.py`
- 当前领域内核：`src/market_intent_inference/`
- 前端字段说明：[docs/user-guide/bsc-webui-inference-guide.md](docs/user-guide/bsc-webui-inference-guide.md)
- 服务器交接手册：[docs/handoff/market-intent-training-handoff-20260728.md](docs/handoff/market-intent-training-handoff-20260728.md)
- 文献综述源文件：[docs/research/bsc-market-intent-literature-review.md](docs/research/bsc-market-intent-literature-review.md)
- 文献综述 PDF：[output/pdf/bsc-market-intent-literature-review.pdf](output/pdf/bsc-market-intent-literature-review.pdf)
- 论文与数据资源：[research-resources/README.md](research-resources/README.md)
- 独立训练框架审查：[docs/reviews/training-framework-independent-review-20260728.md](docs/reviews/training-framework-independent-review-20260728.md)

## 当前原则

1. 先学习可观察操作，再学习角色/意图条件后验，最后训练受约束的决策策略。
2. 历史链上数据属于 offline dataset；不能把 PPO 直接放在静态历史数据上当作真实环境训练。
3. 所有特征、标签、聚类器、校准器和 token universe 都必须遵守决策时点，禁止未来信息泄漏。
4. 数据不足、风险未知、概率未校准或场所能力不支持时，输出 `abstain/no_trade`。
5. 当前项目不包含钱包、私钥、写链、交易广播或真实执行。

## 运行当前 WebUI

```bash
PYTHONPATH=src python scripts/run_webui.py --host 127.0.0.1 --port 8765
```

配置 `BSC_RPC_URL` 后再使用真实 RPC；GeckoTerminal discovery 和公共 RPC 的历史日志能力可能受限，结果必须检查 `quality` 与 `reason_codes`。
