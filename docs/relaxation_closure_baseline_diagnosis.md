# Relaxation Closure Baseline Diagnosis

Date: 2026-06-27

This round starts from branch `codex/longrun-round17-local-results` at
`0c2627821415515973eccbc0e9b4d412d6e7167d`.

## Current Bottleneck

The current bottleneck is valid relaxation lower-bound closure. It is not
native HGA-TGBC incumbent quality and it is not route-load pricing on the tested
rows:

- V12 M2 regenerated closes with the native HGA-TGBC UB `0.718504070755`.
- V12 M1 regenerated has the same verified UB in 300s and 600s, but 300s stops
  with LB `0.332675660948` and one unresolved interval.
- V12 M1 600s closes by continuing relaxation splitting/fathoming, not by BPC
  pricing.
- V20/M3 rows spend essentially all time in relaxation/bound work. Pricing and
  master times remain zero or near zero unless BPC fallback is forced.

The machine-generated interval table is:

```text
results/relaxation_closure_round/baseline_interval_diagnosis.csv
```

## V12 M1: 300s Versus 600s/1200s

The canonical 300s row remains:

| row | status | LB | UB | gap | unresolved |
|---|---:|---:|---:|---:|---:|
| `v12_m1_current_300s` | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 1 |

The 600s row closes:

| row | status | LB | UB | gap | runtime |
|---|---:|---:|---:|---:|---:|
| `v12_m1_default_600s` | optimal | 0.357200583208 | 0.357200583208 | 0 | 481.106s |

The closure is obtained by more time for the same relaxation-led frontier
splitting sequence. The 300s controlling interval is the high-Gini child around
`[0.238133722139, 0.357200583208]`; the later run splits and fathoms that band.

The attempted batch pre-split strategy did not accelerate closure:

| row | LB | gap | note |
|---|---:|---:|---|
| `v12_m1_presplit_300s` | 0.329549359470 | 0.0774109143105 | worse than canonical 300s |

This is because splitting multiple active parents consumes bound time and leaves
more child intervals with underprocessed relaxation evidence.

## V20/M3

The hard-generated V20/M3 stress rows are relaxation-strength tests. Complete
route-mask enumeration is disabled for certification, so any V20 lower bound
must come from valid large-instance relaxations.

The previous plateau was:

- `high_imbalance_seed3202`: 300s gap about `0.100084871258`;
- `tight_T_seed3102`: 300s gap about `0.218955510650`;
- `tight_T_seed3101`: 300s gap about `0.968587506517`.

New compact-flow `mip-light` rows show that the relaxation model, rather than
pricing, is the active lever:

- `high_imbalance_seed3202_miplight_300s` gap `0.0544001976401`;
- `high_imbalance_seed3202_miplight_1200s` gap `0.0317627113992`;
- `tight_T_seed3101_miplight_300s` gap `0.333333333333`.

The same variant is not uniformly better: it weakens moderate rows and
`tight_T_seed3102` in short runs. The next scheduler should select between LP
and `mip-light` variants per interval instead of enabling `mip-light` globally.
