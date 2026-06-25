# V12 M1 Pricing Plateau Next Audit

Before this round, V12 M1 appeared to be dominated by exact-label pricing/tree
closure on narrow active intervals. The new relaxation-portfolio paper-core row
changes that diagnosis.

## Current Result

| row | status | objective | LB | UB | runtime | pricing time | bound time |
|---|---|---:|---:|---:|---:|---:|---:|
| V12 M1 paper-core 300s | optimal | 0.357200583208 | 0.357200583208 | 0.357200583208 | 265.220702 | 0 | 255.8016535 |
| V12 M1 paper-core 1200s | optimal | 0.357200583208 | 0.357200583208 | 0.357200583208 | 257.5489498 | 0 | 248.4369619 |

Final V12 M1 intervals are all bound-fathomed by inventory/route/Gini
relaxation; no exact-label pricing tree is used in the certificate.

The controlling intervals from the old plateau no longer remain active:

- `[0.223250364505,0.245575400956]` fathomed at LB `0.357200583208`;
- `[0.245575400956,0.256737919181]` fathomed at LB `0.357200583208`;
- `[0.256737919181,0.267900437406]` fathomed at LB `0.357200583208`.

## Next Optimization Target

The immediate next target is no longer broad frontier depth or heuristic
incumbent generation. The next useful work is to reduce bound-time in the
inventory/route/Gini relaxation portfolio:

- cache no-operation-budget fallback results by interval and cutoff;
- record operation-budget MIP status/best-bound deltas explicitly;
- add safe early selection when the no-budget relaxation proves cutoff
  infeasibility before the operation-budget solve is attempted.

Exact-label pricing-state reduction remains useful for instances where the
relaxation portfolio cannot fathom the frontier, but it is no longer the V12 M1
blocking component in the current regenerated benchmark.

