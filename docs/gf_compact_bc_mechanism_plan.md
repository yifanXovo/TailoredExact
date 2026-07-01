# GF Compact BC Mechanism Plan

The `paper-gf-compact-bc` command template is:

```powershell
build\ExactEBRP.exe --method gcap-frontier `
  --algorithm-preset paper-gf-compact-bc `
  --paper-run-sealed true `
  --input <instance> --lambda 0.15 --T 3600 `
  --time-limit <seconds> --threads <N> --mip-threads <N> `
  --compact-bc-cut-profile balanced `
  --compact-bc-root-cut-rounds 0 `
  --out results\gf_compact_bc_round\raw\<row>.json
```

The preset runs the normal frontier relaxation phase first.  Remaining leaves
are sent automatically to the compact interval BC subsolver with fixed
`gamma_L/gamma_U`, objective-bound mode, an incumbent cutoff row, and mergeable
CPLEX best-bound evidence when the model scope is original fixed interval.

Default safe families include direct Gini cap/floor rows, interval-tight
McCormick rows, station-inventory conservation, movement-reachability domains,
visit/final-inventory linking, objective lower-estimator cutoff, penalty lower
bound, required movement rows, pickup-only aggregate handling capacity, Gini
spread rows, low-Gini centering, support-duration pair/triple rows, and
pairwise transfer compatibility rows.

Receiver-set source-cover cuts are not default paper-core evidence.  They remain
diagnostic/future work until the compatibility proof and separation tests cover
internal transfers in receiver sets.

`--compact-bc-root-cut-rounds` is currently recorded and reserved for future
iterative root-cut separation.  The current implementation is a static-cut
compact BC model solved by CPLEX.
