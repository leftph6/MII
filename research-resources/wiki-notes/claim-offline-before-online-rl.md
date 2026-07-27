## Claim

For this project, offline RL is a better first RL baseline than online PPO because the initial evidence is a static historical event log and the environment is not yet calibrated. The claim is methodological, not a performance guarantee.

## Conditions

It only applies while policy learning remains paper-only, action support is measured, costs are modeled and the simulator is validated against held-out BSC event statistics.

## Evidence

D4RL motivates dataset-support diagnostics; CQL provides a conservative offline-RL baseline; ABIDES motivates a separate calibrated simulator layer.
