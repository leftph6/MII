## Gap

Existing microstructure papers mostly predict price movement from CLOB order-flow data; AMM work formalizes reserves and price impact; offline-RL work studies static datasets and distribution shift. There is no validated, generally observable BSC meme-coin label set for `role` and `intent` conditioned on AMM event state.

## Consequence

The project must treat role/intent as probabilistic weak labels with evidence, unknown and audit status. The first falsifiable deliverable is calibration and temporal OOS generalization, not a profitable strategy claim.

## Next test

Construct a multi-pool, time-split dataset with hard action labels, rule-generated weak labels and human-audited samples. Compare a transparent tabular baseline against a sequence model and report calibration, abstention, OOD and cluster stability.
