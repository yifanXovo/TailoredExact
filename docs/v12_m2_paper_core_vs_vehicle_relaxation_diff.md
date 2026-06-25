# V12 M2 Paper-Core vs Vehicle-Relaxation Diff

## Rows Compared

- `results/longrun_round17_local/raw/v12_m2_paper_bpc_core_3600s.json`
- `results/longrun_round17_local/ablation/v12_m2_ablation_plus_vehicle_relaxation_1200s.json`
- `results/paper_core_round_next/raw/v12_m2_vehicle_relaxation_repro_1200s.json`
- `results/paper_core_round_next/raw/v12_m2_paper_core_300s_relax_portfolio.json`
- `results/paper_core_round_next/raw/v12_m2_paper_core_1200s_relax_portfolio.json`

## Explanation

The older formal `paper-bpc-core` row enabled route-mask operation-budget cuts,
final-inventory branching, and operation-mode branching. These choices are
certificate-safe, but they changed time allocation. On the critical child
intervals, the operation-budget route-mask MIP was harder to close and returned
weaker time-limited lower bounds. The solver then entered exact-label BPC tree
work and spent most time in pricing, leaving unresolved intervals.

The custom vehicle-relaxation ablation disabled operation-budget cuts and
branching. Its weaker route-mask relaxation was easier to solve and proved
cutoff infeasibility for the critical child intervals. Since every final
interval was bound-fathomed by valid non-pricing lower bounds, it produced a
valid relaxation-only frontier certificate.

## Option Differences That Mattered

| option | old paper-core | custom vehicle-relaxation | integrated paper-core |
|---|---|---|---|
| vehicle-indexed operation relaxation | true | true | true |
| vehicle-indexed transfer flow | true | true | true |
| route-mask operation-budget cuts | true | false | true plus no-budget fallback |
| branch-inventory / operation-mode | true | false | true, but skipped when relaxation fathoms |
| exact-label pricing | true | true | true |
| route-pool incumbent | true | true | true, UB only |
| compact / ng-DSSR / two-track | false | false | false |

## Direct Answers

- Did paper-core enter expensive exact BPC tree work before exploiting the
  vehicle-indexed relaxation? Yes. The old paper-core row did not try the
  easier no-operation-budget relaxation after the operation-budget MIP returned
  a weak time-limited bound.
- Did operation-budget cuts cause worse time allocation? Yes. They are valid
  cuts, but they made the relaxation MIP harder on these intervals.
- Did the paper-core ledger lose a valid lower bound after adaptive split
  replacement? The final old ledger stayed valid, but it did not try the
  compatible no-budget relaxation that later proved the child intervals.
- Did the custom ablation use a stronger relaxation? No. It used a weaker but
  easier relaxation that still gave a stronger valid lower-bound result within
  the time budget.
- Is the custom certificate safe enough to become paper-core default? Yes, as a
  relaxation portfolio fallback. The integrated path keeps operation-budget
  cuts enabled but, if they fail to fathom an interval, also solves the
  no-operation-budget relaxation and keeps the stronger valid lower bound.

