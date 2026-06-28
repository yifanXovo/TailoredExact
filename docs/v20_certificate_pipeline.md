# V20 Certificate Pipeline

The V20 certificate workflow used in `results/v20_replication_round/` is a
staged exact portfolio:

1. Generate a native HGA-TGBC route-plan incumbent.
2. Verify the complete route plan with the ExactEBRP verifier.
3. Use the incumbent only as an upper-bound cutoff.
4. Run the full Gini-frontier ledger with V20-safe relaxation evidence.
5. Use fixed mip-light compact-flow relaxation with connectivity, station
   residual/domain tightening, and V20-safe route/load cuts.
6. If the full ledger remains unresolved, run exact interval cutoff oracles on
   final unresolved leaves.
7. Merge focused interval results only when `scripts/merge_interval_oracle_results.py`
   proves exact leaf coverage and matching metadata.
8. Use exact BPC interval fallback only as a diagnostic unless exact pricing
   closes the interval.

The corresponding preset is:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-exact-v20-certificate `
  --input reference\hard_stress\V20_M3\high_imbalance_seed3202.txt `
  --lambda 0.15 --T 3600 --time-limit 1200 --frontier-intervals 3
```

The preset keeps archive scanning disabled, uses native HGA-TGBC as the
paper-reproducible UB source, and keeps BPC fallback off by default.  It is an
exact portfolio candidate: certificates may come from full-frontier relaxation
evidence, safely merged exact interval-oracle infeasibility certificates, or
exactly closed BPC interval trees.

Current status: two V20/M3 stress rows are certified in the available evidence
(`high_imbalance_seed3202` and `tight_T_seed3101`).  This supports further
paper-candidate testing, but broader benchmark claims still require more rows.
