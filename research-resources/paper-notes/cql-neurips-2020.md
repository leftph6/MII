## Evidence

Conservative Q-Learning regularizes value estimates toward conservative behavior outside the observed data distribution. It is a candidate offline-RL baseline for a logged market dataset.

## Relevance

Use CQL only after supervised posterior baselines, data support diagnostics, simulator checks and cost-aware reward definitions are in place.

## Limitation

CQL cannot correct missing history, incorrect rewards, future leakage or a misspecified AMM simulator.

## Source

https://proceedings.neurips.cc/paper/2020/hash/0d2b2061826a5df3221116a5085a6052-Abstract.html
