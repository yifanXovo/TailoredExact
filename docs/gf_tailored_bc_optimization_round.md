# GF Tailored BC Optimization Round

This round starts from commit `85fc9493f2699229e78b2a71e1094eca0ff73ff5` and keeps `paper-gf-tailored-bc` as the paper-facing line. The first step was a fair one-thread baseline before algorithmic changes. The baseline outputs live under `results/gf_tailored_bc_optimization_round/`.

The implemented algorithmic change is a bounded, deviation-ranked separator for the paper-safe Gini subset-envelope callback cuts. The cut itself is unchanged:

`|V R_A - |A| S| <= V gamma_U S`.

Only the separation policy changed. The callback now ranks stations by LP ratio deviation from `S/V`, tests high-deviation singleton/pair/triple/quad subsets first, respects `--tailored-bc-gini-subset-max-size`, and limits callback additions with `--tailored-bc-gini-subset-max-cuts`.

The hard fixed-interval diagnostic rows in this round exposed a more basic blocker: under several hard-leaf configurations the interval subsolver did not emit solver-final JSON within the wrapper cap, even with short internal limits. Those rows are written as honest noncertified wrapper/native-exit artifacts and are not certificate evidence.

Current status:

- Baseline and final control CSVs are present.
- `tight_T_seed3101`, `high_imbalance_seed3202`, and rerun V12 M2 preserve certification under one-thread settings.
- V12 M1 remains noncertified at the 300s bounded row in this round; prior post-merge callback-round evidence remains outside this round.
- Benders-like transfer-network cuts remain diagnostic-only.
- The next required engineering step is reliable interval-solver checkpoint/finalization for hard leaves before further cut-rate conclusions can be trusted.
