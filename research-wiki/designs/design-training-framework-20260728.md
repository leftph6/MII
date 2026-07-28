---
id: design-training-framework-20260728
type: design
title: Time-safe posterior and offline-RL training framework
status: awaiting-review
tags:
- bsc
- offline-rl
- training
created_at: '2026-07-27T17:34:08Z'
updated_at: '2026-07-27T17:34:08Z'
evidence_cutoff: '2026-07-28'
---

## Decision boundary

The next implementation should have four layers: a time-safe data lake and manifest; supervised multi-task posterior learning; an event-driven BSC CFMM simulator; and offline-RL/policy evaluation. PPO or other online RL is deferred until simulator calibration and historical support diagnostics pass.

## Required invariants

Every record carries decision time, horizon end, target event position and data cutoff. Future labels never enter features. The system can emit unknown or abstain. Strategy evaluation includes gas, swap fee, slippage, liquidity limits, token tax uncertainty and failed transactions. No wallet signing or write-chain action is in scope.

## Review status

Awaiting human confirmation of label ontology, data access tier, target horizons and paper-only risk limits before production training code is implemented.
