# Final verification evidence

Environment: `conda run -n codex-engineering`, Python 3.12.13; project root is `/Users/mashengyu/Desktop/quant research/market-intent-inference`.

Fresh checks:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src conda run -n codex-engineering python -m pytest -p no:cacheprovider -q` → `14 passed`;
- `PYTHONDONTWRITEBYTECODE=1 conda run -n codex-engineering python -m compileall -q src tests` → exit 0;
- `RUFF_NO_CACHE=true conda run -n codex-engineering python -m ruff check src tests` → `All checks passed`;
- `RUFF_NO_CACHE=true conda run -n codex-engineering python -m ruff format --check src tests` → `7 files already formatted`;
- `PYTHONDONTWRITEBYTECODE=1 conda run -n codex-engineering python scripts/check_security.py` → `security_boundary_ok`;
- `conda run -n codex-engineering harness-eval validate ./evals/domain-kernel.yaml` → 规格有效；
- `conda run -n codex-engineering harness-eval run ./evals/domain-kernel.yaml` → 评测通过，报告：`harness-results/20260725T155405Z-domain-kernel-bf46296fe4f14663802f70a12f3dee74/REPORT.md`；
- `conda run -n codex-engineering graphify update .` / `validate .` → 图谱与当前源码同步且有效；
- `conda run -n codex-engineering research-wiki validate ./research-wiki` → `13 个实体，5 条关系`，校验通过；
- 最终独立复审 → 通过，剩余阻塞项为零。

Isolation note: Coinman Git metadata was captured before and after. The current external Coinman worktree differs from the captured baseline by the disappearance of the pre-existing untracked `app/prediction_strategy.py`; no write operation was issued against Coinman by this project, and the file was not restored or deleted by this task.
