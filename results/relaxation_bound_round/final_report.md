# Relaxation Bound Round Final Report

Branch: `codex/longrun-round17-local-results`

Start commit: `ef4cb62edf3081ffcfd06976d18705bf861b4edc`

Final commit: `PENDING`

## Build

CMake was unavailable on this machine. The verified build command was:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/hga_tgbc/HgaTgbcGreedy.cpp src/HgaTgbcRunner.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
```

Build succeeded with pre-existing HGA warning messages.

## Implemented Changes

- Added `--v20-safe-relaxation-cuts`.
- Added continuous vehicle-indexed station, pickup, drop, load-balance,
  operation-budget, depot-star duration, pairwise route-duration cover, and
  vehicle transfer-cap constraints for V20-safe relaxation bounds.
- Added controlled BPC fallback options:
  `--frontier-bpc-fallback-mode`,
  `--frontier-bpc-fallback-reserve-fraction`,
  `--frontier-bpc-fallback-min-seconds`, and
  `--frontier-bpc-fallback-max-intervals`.
- Fixed hard stress instance metadata so V20/M3 rows are labelled
  `hard_generated_v20_m3`, not `historical_target`.
- Added docs for V20-safe cuts, scheduler behavior, BPC fallback diagnostics,
  plateau diagnosis, and V20/M3 stress results.

Proof sketches are in:

- `docs/v20_safe_relaxation_cuts.md`
- `docs/bpc_fallback_on_unresolved_intervals.md`
- `docs/relaxation_variant_scheduler.md`

## V12 Results

| row | status | LB | UB | gap | notes |
|---|---:|---:|---:|---:|---|
| V4 smoke 30s | optimal | 0 | 0 | 0 | regression passes |
| V12 M2 original paper-core 300s command | optimal | 0.718504070755 | 0.718504070755 | 0 | relaxation-only full-frontier certificate preserved |
| V12 M2 altered 300s command | not closed | 0.676165688664 | 0.718504070755 | 0.0589257372558 | documents scheduling sensitivity, not used as canonical success |
| V12 M1 300s relaxation | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 | same plateau as previous round |
| V12 M1 300s BPC fallback | not closed | 0.331296710948 | 0.357200583208 | 0.0725191208467 | one node/one pricing call; not useful |
| V12 M1 1200s relaxation | optimal | 0.357200583208 | 0.357200583208 | 0 | relaxation-only full-frontier certificate |

The V12 M1 1200s closure is the main improvement of this round.

## V20/M3 Results

All V20/M3 hard stress rows remain noncertified. Metadata is fixed to
`hard_generated_v20_m3`.

300s improved-relaxation rows:

| instance | LB | UB | gap |
|---|---:|---:|---:|
| high_imbalance_seed3201 | 2.14348953154 | 2.44340319194 | 0.122744236967 |
| high_imbalance_seed3202 | 1.57423364041 | 1.74931345205 | 0.100084871258 |
| moderate_seed3301 | 0.0427477151184 | 0.0491525526647 | 0.130305288314 |
| moderate_seed3302 | 0.131033733249 | 0.195636206549 | 0.33021736845 |
| tight_T_seed3101 | 0.00336907581205 | 0.107252734134 | 0.968587506517 |
| tight_T_seed3102 | 0.469176890001 | 0.600704436685 | 0.21895551065 |

Representative 1200s row:

- `high_imbalance_seed3202`: LB improved to `1.60644024991`, gap improved to
  `0.081673871528`, but the row remains noncertified with unresolved intervals.

## BPC Fallback

BPC fallback was tested on V12 M1 and three representative V20/M3 rows.
It did not produce closed interval evidence in this round. V12 M1 fallback
started one BPC node and one pricing call, but the lost relaxation time produced
a weaker final bound than the relaxation-only 300s row. V20 fallback rows also
remained relaxation dominated.

Conclusion: the current bottleneck is still relaxation-bound strength and
scheduling. BPC fallback is certificate-safe and diagnostic, but not yet useful
as a default on these rows.

## Audit

Commands:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\relaxation_bound_round\raw --csv-out results\relaxation_bound_round\certificate_audit.csv --fail-on-error
```

Audit result: `audited_rows=16 failures=0`.

No heuristic, route-pool, CPLEX, or imported incumbent evidence is used as a
lower bound. V20/M3 rows do not use complete all-subset route-mask enumeration
as certifying evidence.

## Remaining Bottleneck

The next round should continue targeted relaxation strengthening rather than
broad benchmarking. Priority targets:

- stronger station residual cover cuts;
- stronger vehicle-indexed flow/capacity cuts;
- deterministic parallel interval relaxation;
- better stop/split policy before invoking BPC fallback;
- sharper large-instance lower-bound formulations that remain valid without
  complete route-mask enumeration.
