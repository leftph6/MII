# BSC WebUI final verification evidence

Environment: `conda run -n codex-engineering`, project root `/Users/mashengyu/Desktop/quant research/market-intent-inference`.

Fresh checks:

- `conda run -n codex-engineering pytest -q` → `35 passed`
- `PYTHONDONTWRITEBYTECODE=1 conda run -n codex-engineering python -m compileall -q src tests scripts` → exit 0
- `conda run -n codex-engineering ruff check src tests scripts` → All checks passed
- `conda run -n codex-engineering python scripts/check_security.py` → `security_boundary_ok`
- `conda run -n codex-engineering harness-eval validate ./evals/bsc-webui.yaml` → 规格有效
- `conda run -n codex-engineering harness-eval run ./evals/bsc-webui.yaml --output ./harness-results/bsc-webui-20260727-final` → 评测通过（35 passed）
- `conda run -n codex-engineering graphify build .`、`update .`、`validate .` → 图有效且与源码同步（55 files / 537 nodes / 1506 relations）
- `conda run -n codex-engineering graphify query BSCAnalyzer --root . --limit 20`、`query create_server ...` → 返回分析器与 WebUI 入口符号
- `conda run -n codex-engineering research-wiki index ./research-wiki`、`pack ./research-wiki`、`validate ./research-wiki` → `校验通过：21 个实体，11 条关系`
- WebUI：静态页面包含候选池表、分析/推理区、run 审计与 Graphify canvas；本沙箱禁止绑定监听端口，HTTP handler 端到端 smoke 未在本次会话重复执行；交接文档记录的 live smoke 结果保留。

Isolation: Coinman 仅执行允许的两条 git 元数据命令；after 与实现前 baseline 逐字一致，见 `docs/reviews/coinman-isolation-20260726.md`。
