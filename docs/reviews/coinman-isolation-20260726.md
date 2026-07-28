# Coinman 隔离审计记录

本文件只记录允许的 Git 元数据命令 stdout；不读取 Coinman 文件内容，也不保存代码、数据库、环境变量或凭据。早期 before 与随后复核的两条 stdout 存在外部状态差异，已原样保留；没有证据表明该变化由本项目造成。本项目以最新复核结果作为实现前基线，实现完成后只与该基线逐字比较。

## before: `git status --porcelain=v1`

```text
 M .gitignore
 M Dockerfile
 M MIGRATION.md
 M PROJECT_GUIDELINES.md
 M README.md
 M VIDEO_STACK.md
 M app/__init__.py
RM app/backtest.py -> app/application/backtest.py
RM app/agents.py -> app/application/research.py
RM app/bot.py -> app/application/trading_bot.py
RM app/settings.py -> app/config/settings.py
RM app/strategy.py -> app/domain/cex_strategy.py
RM app/market_filters.py -> app/domain/market_filters.py
R  app/schemas.py -> app/domain/models.py
RM app/oms.py -> app/domain/oms.py
RM app/prediction_strategy.py -> app/domain/prediction_strategy.py
RM app/risk.py -> app/domain/risk.py
RM app/env_config.py -> app/infrastructure/env_config.py
RM app/exchange.py -> app/infrastructure/exchanges.py
RM app/intelligence.py -> app/infrastructure/intelligence.py
RM app/llm_router.py -> app/infrastructure/llm_router.py
RM app/pipeline.py -> app/infrastructure/pipeline.py
RM app/polymarket.py -> app/infrastructure/polymarket.py
RM app/polymarket_execution.py -> app/infrastructure/polymarket_execution.py
RM app/storage.py -> app/infrastructure/storage.py
 M app/main.py
 M app/video_stack.py
 M tests/test_env_config.py
 M tests/test_live_oms_agent_memory.py
 M tests/test_llm_router.py
 M tests/test_oms_backtest_intelligence.py
 M tests/test_polymarket_gateway.py
 M tests/test_prediction_strategy.py
 M tests/test_risk.py
 M tests/test_strategy.py
?? AGENTS.md
?? PROJECT_ENGINEERING_PROMPT.md
?? app/agents.py
?? app/api/
?? app/application/__init__.py
?? app/application/cex_scanner.py
?? app/application/experiment_config.py
?? app/application/llm.py
?? app/application/ports.py
?? app/application/prompts/
?? app/application/read_models.py
?? app/application/run_context.py
?? app/application/runtime.py
?? app/backtest.py
?? app/bot.py
?? app/config/__init__.py
?? app/config/values.py
?? app/domain/__init__.py
?? app/domain/errors.py
?? app/domain/ports.py
?? app/env_config.py
?? app/exchange.py
?? app/infrastructure/__init__.py
?? app/infrastructure/agent_evidence.py
?? app/infrastructure/event_envelope.py
?? app/infrastructure/observability.py
?? app/infrastructure/repositories/
?? app/intelligence.py
?? app/llm_router.py
?? app/market_filters.py
?? app/oms.py
?? app/pipeline.py
?? app/polymarket.py
?? app/polymarket_execution.py
?? app/prediction_strategy.py
?? app/risk.py
?? app/schemas.py
?? app/settings.py
?? app/storage.py
?? app/strategy.py
?? docker-compose.paper.yml
?? docs/
?? engineering_system_prompt.template.md
?? evals/
?? requirements.lock
?? requirements.lock.sha256
?? research-wiki/
?? scripts/paper_smoke.py
?? scripts/render_graph_html.py
?? scripts/verify_artifacts.py
?? test-artifacts/
?? tests/test_agent_evidence.py
?? tests/test_api_lifecycle.py
?? tests/test_event_governance.py
?? tests/test_execution_safety.py
?? tests/test_llm_governance.py
?? tests/test_public_contracts.py
?? tests/test_research_orchestration.py
?? tests/test_run_context.py
```

## before: `git diff --name-only`

```text
.gitignore
Dockerfile
MIGRATION.md
PROJECT_GUIDELINES.md
README.md
VIDEO_STACK.md
app/__init__.py
app/application/backtest.py
app/application/research.py
app/application/trading_bot.py
app/config/settings.py
app/domain/cex_strategy.py
app/domain/market_filters.py
app/domain/oms.py
app/domain/prediction_strategy.py
app/domain/risk.py
app/infrastructure/env_config.py
app/infrastructure/exchanges.py
app/infrastructure/intelligence.py
app/infrastructure/llm_router.py
app/infrastructure/pipeline.py
app/infrastructure/polymarket.py
app/infrastructure/polymarket_execution.py
app/infrastructure/storage.py
app/main.py
app/video_stack.py
tests/test_env_config.py
tests/test_live_oms_agent_memory.py
tests/test_llm_router.py
tests/test_oms_backtest_intelligence.py
tests/test_polymarket_gateway.py
tests/test_prediction_strategy.py
tests/test_risk.py
tests/test_strategy.py
```

## after: 实现前隔离复核

以下输出由与 before 完全相同的两条只读命令在计划审查阶段获取。与 before 比较时，`app/polymarket.py` 和 `app/polymarket_execution.py` 两组状态行发生外部变化；两次检查均为只读，当前结果作为本项目的实现前基线。实现完成后必须追加最终 after 区块，并与本节逐字比较。

### `git status --porcelain=v1`

```text
 M .gitignore
 M Dockerfile
 M MIGRATION.md
 M PROJECT_GUIDELINES.md
 M README.md
 M VIDEO_STACK.md
 M app/__init__.py
RM app/backtest.py -> app/application/backtest.py
RM app/agents.py -> app/application/research.py
RM app/bot.py -> app/application/trading_bot.py
RM app/settings.py -> app/config/settings.py
RM app/strategy.py -> app/domain/cex_strategy.py
RM app/market_filters.py -> app/domain/market_filters.py
R  app/schemas.py -> app/domain/models.py
RM app/oms.py -> app/domain/oms.py
RM app/prediction_strategy.py -> app/domain/prediction_strategy.py
RM app/risk.py -> app/domain/risk.py
RM app/env_config.py -> app/infrastructure/env_config.py
RM app/exchange.py -> app/infrastructure/exchanges.py
RM app/intelligence.py -> app/infrastructure/intelligence.py
RM app/llm_router.py -> app/infrastructure/llm_router.py
RM app/pipeline.py -> app/infrastructure/pipeline.py
?? app/polymarket.py
?? app/polymarket_execution.py
RM app/storage.py -> app/infrastructure/storage.py
 M app/main.py
 M app/video_stack.py
 M tests/test_env_config.py
 M tests/test_live_oms_agent_memory.py
 M tests/test_llm_router.py
 M tests/test_oms_backtest_intelligence.py
 M tests/test_polymarket_gateway.py
 M tests/test_prediction_strategy.py
 M tests/test_risk.py
 M tests/test_strategy.py
?? AGENTS.md
?? PROJECT_ENGINEERING_PROMPT.md
?? app/agents.py
?? app/api/
?? app/application/__init__.py
?? app/application/cex_scanner.py
?? app/application/experiment_config.py
?? app/application/llm.py
?? app/application/ports.py
?? app/application/prompts/
?? app/application/read_models.py
?? app/application/run_context.py
?? app/application/runtime.py
?? app/backtest.py
?? app/bot.py
?? app/config/__init__.py
?? app/config/values.py
?? app/domain/__init__.py
?? app/domain/errors.py
?? app/domain/ports.py
?? app/env_config.py
?? app/exchange.py
?? app/infrastructure/__init__.py
?? app/infrastructure/agent_evidence.py
?? app/infrastructure/event_envelope.py
?? app/infrastructure/observability.py
?? app/infrastructure/repositories/
?? app/intelligence.py
?? app/llm_router.py
?? app/market_filters.py
?? app/oms.py
?? app/pipeline.py
?? app/polymarket.py
?? app/polymarket_execution.py
?? app/prediction_strategy.py
?? app/risk.py
?? app/schemas.py
?? app/settings.py
?? app/storage.py
?? app/strategy.py
?? docker-compose.paper.yml
?? docs/
?? engineering_system_prompt.template.md
?? evals/
?? requirements.lock
?? requirements.lock.sha256
?? research-wiki/
?? scripts/paper_smoke.py
?? scripts/render_graph_html.py
?? scripts/verify_artifacts.py
?? test-artifacts/
?? tests/test_agent_evidence.py
?? tests/test_api_lifecycle.py
?? tests/test_event_governance.py
?? tests/test_execution_safety.py
?? tests/test_llm_governance.py
?? tests/test_public_contracts.py
?? tests/test_research_orchestration.py
?? tests/test_run_context.py
```

### `git diff --name-only`

```text
.gitignore
Dockerfile
MIGRATION.md
PROJECT_GUIDELINES.md
README.md
VIDEO_STACK.md
app/__init__.py
app/application/backtest.py
app/application/research.py
app/application/trading_bot.py
app/config/settings.py
app/domain/cex_strategy.py
app/domain/market_filters.py
app/domain/oms.py
app/domain/prediction_strategy.py
app/domain/risk.py
app/infrastructure/env_config.py
app/infrastructure/exchanges.py
app/infrastructure/intelligence.py
app/infrastructure/llm_router.py
app/infrastructure/pipeline.py
app/infrastructure/polymarket.py
app/infrastructure/polymarket_execution.py
app/infrastructure/storage.py
app/main.py
app/video_stack.py
tests/test_env_config.py
tests/test_live_oms_agent_memory.py
tests/test_llm_router.py
tests/test_oms_backtest_intelligence.py
tests/test_polymarket_gateway.py
tests/test_prediction_strategy.py
tests/test_risk.py
tests/test_strategy.py
```

## after: 实现完成

实现完成后复检，与本轮实现前 baseline（本会话开始时捕获的 stdout）逐字一致，差异为零。

### `git status --porcelain=v1`

```text
 M .gitignore
 M Dockerfile
 M MIGRATION.md
 M PROJECT_GUIDELINES.md
 M README.md
 M VIDEO_STACK.md
 M app/__init__.py
RM app/backtest.py -> app/application/backtest.py
RM app/agents.py -> app/application/research.py
RM app/bot.py -> app/application/trading_bot.py
RM app/settings.py -> app/config/settings.py
RM app/strategy.py -> app/domain/cex_strategy.py
RM app/market_filters.py -> app/domain/market_filters.py
R  app/schemas.py -> app/domain/models.py
RM app/oms.py -> app/domain/oms.py
RM app/prediction_strategy.py -> app/domain/prediction_strategy.py
RM app/risk.py -> app/domain/risk.py
RM app/env_config.py -> app/infrastructure/env_config.py
RM app/exchange.py -> app/infrastructure/exchanges.py
RM app/intelligence.py -> app/infrastructure/intelligence.py
RM app/llm_router.py -> app/infrastructure/llm_router.py
RM app/pipeline.py -> app/infrastructure/pipeline.py
RM app/polymarket.py -> app/infrastructure/polymarket.py
RM app/polymarket_execution.py -> app/infrastructure/polymarket_execution.py
RM app/storage.py -> app/infrastructure/storage.py
 M app/main.py
 M app/video_stack.py
 M tests/test_env_config.py
 M tests/test_live_oms_agent_memory.py
 M tests/test_llm_router.py
 M tests/test_oms_backtest_intelligence.py
 M tests/test_polymarket_gateway.py
 M tests/test_prediction_strategy.py
 M tests/test_risk.py
 M tests/test_strategy.py
?? AGENTS.md
?? PROJECT_ENGINEERING_PROMPT.md
?? app/agents.py
?? app/api/
?? app/application/__init__.py
?? app/application/cex_scanner.py
?? app/application/experiment_config.py
?? app/application/llm.py
?? app/application/ports.py
?? app/application/prompts/
?? app/application/read_models.py
?? app/application/run_context.py
?? app/application/runtime.py
?? app/backtest.py
?? app/bot.py
?? app/config/__init__.py
?? app/config/values.py
?? app/domain/__init__.py
?? app/domain/errors.py
?? app/domain/ports.py
?? app/env_config.py
?? app/exchange.py
?? app/infrastructure/__init__.py
?? app/infrastructure/agent_evidence.py
?? app/infrastructure/event_envelope.py
?? app/infrastructure/observability.py
?? app/infrastructure/repositories/
?? app/intelligence.py
?? app/llm_router.py
?? app/market_filters.py
?? app/oms.py
?? app/pipeline.py
?? app/polymarket.py
?? app/polymarket_execution.py
?? app/prediction_strategy.py
?? app/risk.py
?? app/schemas.py
?? app/settings.py
?? app/storage.py
?? app/strategy.py
?? docker-compose.paper.yml
?? docs/
?? engineering_system_prompt.template.md
?? evals/
?? requirements.lock
?? requirements.lock.sha256
?? research-wiki/
?? scripts/paper_smoke.py
?? scripts/render_graph_html.py
?? scripts/verify_artifacts.py
?? test-artifacts/
?? tests/test_agent_evidence.py
?? tests/test_api_lifecycle.py
?? tests/test_event_governance.py
?? tests/test_execution_safety.py
?? tests/test_llm_governance.py
?? tests/test_public_contracts.py
?? tests/test_research_orchestration.py
?? tests/test_run_context.py
```

### `git diff --name-only`

```text
.gitignore
Dockerfile
MIGRATION.md
PROJECT_GUIDELINES.md
README.md
VIDEO_STACK.md
app/__init__.py
app/application/backtest.py
app/application/research.py
app/application/trading_bot.py
app/config/settings.py
app/domain/cex_strategy.py
app/domain/market_filters.py
app/domain/oms.py
app/domain/prediction_strategy.py
app/domain/risk.py
app/infrastructure/env_config.py
app/infrastructure/exchanges.py
app/infrastructure/intelligence.py
app/infrastructure/llm_router.py
app/infrastructure/pipeline.py
app/infrastructure/polymarket.py
app/infrastructure/polymarket_execution.py
app/infrastructure/storage.py
app/main.py
app/video_stack.py
tests/test_env_config.py
tests/test_live_oms_agent_memory.py
tests/test_llm_router.py
tests/test_oms_backtest_intelligence.py
tests/test_polymarket_gateway.py
tests/test_prediction_strategy.py
tests/test_risk.py
tests/test_strategy.py
```
