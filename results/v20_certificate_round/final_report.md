# V20 Certificate Round Final Report

Branch: `codex/longrun-round17-local-results`

Starting remote head: `e37955f58f4b6396bec7ca441987f70adde6fa3f`

Final commit SHA: see final response after push.

## Implemented Changes

- Added `--relaxation-portfolio-mode exhaustive`.
- Added cutoff-feasibility certificate metadata and JSON fields.
- Added interval-closure CLI metadata fields.
- Added a conservative Python focused interval-closure harness.
- Added service-operation minimum handling cut alias
  `--service-operation-min-handling`.
- Fixed result-level cutoff-feasibility reporting so it is true only when the
  reported valid lower bound reaches the cutoff.

## Did high_imbalance_seed3202 Certify?

No.

The full 300s exhaustive attempt reports:

| LB | UB | gap | status |
|---:|---:|---:|---|
| 1.61719766358 | 1.74931345205 | 0.0755243654678 | not closed |

This is weaker than the previous best mip-light 1200s gap
`0.0317627113992`.  Therefore no V20 certificate was obtained.

## Hardest Intervals

The previous best 1200s trace leaves the controlling intervals near:

- `[0.534375,0.554166666667]`;
- `[0.554166666667,0.573958333333]`.

Focused closure attempts on interval IDs 13 and 18 did not close and were not
safe to merge into the full frontier ledger.

## Which Variant Helped?

No new variant improved the priority target.  Exhaustive mode showed that the
current selected candidates still keep the baseline bound on the controlling
interval.  Cutoff-feasibility status is `best_valid_bound_below_cutoff`.

## Did BPC Interval Fallback Help?

BPC fallback was not rerun as a default path in this round because previous
fallback rows did not improve bounds and the focused relaxation attempt did not
reduce the controlling interval set.  It remains diagnostic.

## V12 Stability

| row | status | LB | UB | gap | runtime |
|---|---:|---:|---:|---:|---:|
| V4 smoke 30s | optimal | 0 | 0 | 0 | 0.870s |
| V12 M2 canonical 300s | optimal | 0.718504070755 | 0.718504070755 | 0 | 204.375s |
| V12 M1 adaptive 300s | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 310.353s |
| V12 M1 adaptive 600s | optimal | 0.357200583208 | 0.357200583208 | 0 | 473.481s |

## Audit

`audit_bpc_certificate.py --self-test` passed.

`results/v20_certificate_round/certificate_audit.csv` reports
`audited_rows=9 failures=0`.

## Recommendation

A V20 paper-candidate preset is not justified.  The next targeted round should
implement a true standalone cutoff-feasibility MIP for a fixed gamma interval
or carry inherited full-frontier bounds into focused interval solves with a
formal coverage merge.  Broad benchmark testing should wait.
