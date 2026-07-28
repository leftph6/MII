# Graphify 报告

## 摘要

- 源文件：77
- 节点：615
- 关系：1639
- 诊断：0
- 未解析源码：0

## 节点类型

| 类型 | 数量 |
| --- | ---: |
| `class` | 37 |
| `external` | 308 |
| `file` | 77 |
| `function` | 168 |
| `module` | 25 |

## 关系类型

| 类型 | 数量 |
| --- | ---: |
| `calls` | 1283 |
| `contains` | 230 |
| `imports` | 119 |
| `links` | 7 |

## 源文件

- `AGENTS.md`（markdown）
- `README.md`（markdown）
- `data/README.md`（markdown）
- `docs/design/PROJECT_PROMPT_DRAFT.md`（markdown）
- `docs/design/bsc-webui-design-v0.1.md`（markdown）
- `docs/design/bsc-webui-log-schema-v0.1.md`（markdown）
- `docs/design/domain-contract-v0.1.md`（markdown）
- `docs/design/domain-contract-v0.md`（markdown）
- `docs/handoff/bsc-webui-live-fix-handoff-20260727.md`（markdown）
- `docs/handoff/market-intent-training-handoff-20260728.md`（markdown）
- `docs/plans/bsc-webui-implementation-plan-20260726.md`（markdown）
- `docs/plans/implementation-plan-20260725.md`（markdown）
- `docs/research/bsc-market-intent-literature-review.md`（markdown）
- `docs/research/market_space_element_catalog.md`（markdown）
- `docs/research/source_agent_identifiability_2021.md`（markdown）
- `docs/research/source_bsc_webui_data_20260726.md`（markdown）
- `docs/research/source_cont_2014.md`（markdown）
- `docs/research/source_deeplob_2018.md`（markdown）
- `docs/research/source_flash_boys_2019.md`（markdown）
- `docs/research/source_kyle_1985.md`（markdown）
- `docs/research/source_uniswap_v2.md`（markdown）
- `docs/reviews/bsc-webui-code-review-20260726.md`（markdown）
- `docs/reviews/bsc-webui-code-review-fix-20260727.md`（markdown）
- `docs/reviews/bsc-webui-design-review-20260726.md`（markdown）
- `docs/reviews/bsc-webui-plan-review-20260726.md`（markdown）
- `docs/reviews/code-review-fix-20260725.md`（markdown）
- `docs/reviews/coinman-isolation-20260726.md`（markdown）
- `docs/reviews/coinman-isolation-anomaly-20260725.md`（markdown）
- `docs/reviews/design-review-20260725.md`（markdown）
- `docs/reviews/plan-review-20260725.md`（markdown）
- `docs/reviews/review-plan-final-20260725.md`（markdown）
- `docs/reviews/training-framework-independent-review-20260728.md`（markdown）
- `docs/user-guide/bsc-webui-inference-guide.md`（markdown）
- `experiments/README.md`（markdown）
- `experiments/configs/README.md`（markdown）
- `output/pdf/README.md`（markdown）
- `research-resources/NOTICE.md`（markdown）
- `research-resources/README.md`（markdown）
- `research-resources/paper-notes/abides-2019.md`（markdown）
- `research-resources/paper-notes/bdlob-2018.md`（markdown）
- `research-resources/paper-notes/cql-neurips-2020.md`（markdown）
- `research-resources/paper-notes/d4rl-2020.md`（markdown）
- `research-resources/paper-notes/finrl-2020.md`（markdown）
- `research-resources/paper-notes/sirignano-cont-2018.md`（markdown）
- `research-resources/wiki-notes/claim-offline-before-online-rl.md`（markdown）
- `research-resources/wiki-notes/design-training-framework.md`（markdown）
- `research-resources/wiki-notes/gap-bsc-latent-intent.md`（markdown）
- `scripts/bsc_smoke.py`（python）
- `scripts/build_literature_pdf.py`（python）
- `scripts/check_security.py`（python）
- `scripts/run_webui.py`（python）
- `simulator/README.md`（markdown）
- `src/market_intent_inference/__init__.py`（python）
- `src/market_intent_inference/adapters/__init__.py`（python）
- `src/market_intent_inference/adapters/bsc_rpc.py`（python）
- `src/market_intent_inference/adapters/geckoterminal.py`（python）
- `src/market_intent_inference/application/__init__.py`（python）
- `src/market_intent_inference/application/bsc_pipeline.py`（python）
- `src/market_intent_inference/application/run_store.py`（python）
- `src/market_intent_inference/domain.py`（python）
- `src/market_intent_inference/inference.py`（python）
- `src/market_intent_inference/interfaces/__init__.py`（python）
- `src/market_intent_inference/interfaces/web.py`（python）
- `test-artifacts/bsc-webui/verification-20260726.md`（markdown）
- `test-artifacts/domain-kernel/verification-20260725.md`（markdown）
- `tests/conftest.py`（python）
- `tests/test_bsc_pipeline.py`（python）
- `tests/test_bsc_rpc.py`（python）
- `tests/test_domain.py`（python）
- `tests/test_external_boundary.py`（python）
- `tests/test_geckoterminal.py`（python）
- `tests/test_inference.py`（python）
- `tests/test_run_store.py`（python）
- `tests/test_security_boundary.py`（python）
- `tests/test_web.py`（python）
- `training/README.md`（markdown）
- `web/app.js`（javascript）

## Python 源码根

- `src`

## 语言分析能力

- `javascript`：classes, functions, explicit-relative-imports, conservative-calls
- `markdown`：internal-links
- `python`：modules, classes, functions, imports, calls
- `typescript`：classes, functions, explicit-relative-imports, conservative-calls

## 当前未解析的源码

- _未发现已知但不受支持的源码后缀_。

## 查询提示

```zsh
conda run -n codex-engineering graphify query 关键词
conda run -n codex-engineering graphify path 起点 终点
conda run -n codex-engineering graphify explain 符号
conda run -n codex-engineering graphify affected 符号 --depth 2
```
