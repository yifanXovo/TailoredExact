# Oracle Bound Merge Round Final Report

Branch: `codex/longrun-round17-local-results`

Implementation commit before this report-only update: 5b01507bbbd14edd3611d5371bdc21f8ba241ae6.
Final pushed HEAD is recorded in the assistant final response to avoid a self-referential commit hash.

## Code Changes

- Added interval oracle model semantics fields to JSON output.
- Added `--interval-exact-oracle-mode objective-bound|cutoff-feasibility|both`.
- Added `--interval-oracle-merge-timeout-bound true|false`.
- Added safe timeout-bound merge into the full frontier leaf ledger.
- Added oracle-bound ledger columns and recomputation of the full frontier LB
  from final leaves.
- Updated certificate audit to reject mergeable bounds unless their model type,
  scope, objective sense, and Gini interval rows are audit-visible.
- Fixed invalid JSON emission from nonfinite oracle gap values.

## Bound Semantics

Timeout best bounds are mergeable only when they come from a valid original
fixed-interval compact model. In this round, `both` mode uses the original
compact objective-bound oracle, omits the objective cutoff row, and minimizes
`G + lambda * P` over `gamma_L <= G <= gamma_U`.

Cutoff-feasibility remains a valid infeasibility certificate, but timeout rows
are not merged unless `interval_oracle_can_merge_bound=true`.

## V20/M3 Results

| instance | status | LB | UB | gap | note |
| --- | --- | ---: | ---: | ---: | --- |
| high_imbalance_seed3202 | certified | 1.74931345205 | 1.74931345205 | 0 | stable |
| tight_T_seed3101 | certified | 0.107252734134 | 0.107252734134 | 0 | stable |
| moderate_seed3301 | noncertified | 0.047773 | 0.0491525526647 | 0.0280667552335 | gap reduced below 0.05 |
| tight_T_seed3102 | noncertified | 0.450176109171 | 0.600704436685 | 0.250586342169 | oracle bounds did not close leaves |
| high_imbalance_seed3201 | noncertified | 2.141566 | 2.44340319194 | 0.123531471571 | improved but still open |
| moderate_seed3302 | skipped | | | | not rerun in this round |

`moderate_seed3301` did not certify. The two remaining open leaves have valid
objective-bound oracle lower bounds but remain below the incumbent cutoff:

- `[0.0122881381662, 0.0245762763324]`, merged LB `0.047773`;
- `[0.0245762763324, 0.0368644144986]`, merged LB `0.048467`.

## Stability

- V12 M2 remains certified: `0.718504070755`.
- V12 M1 remains certified: `0.357200583208`.
- `high_imbalance_seed3202` remains certified.
- `tight_T_seed3101` remains certified.
- V4 smoke was skipped because the expected V4 input is not present in this
  checkout.

## BPC Fallback

BPC fallback closed zero leaves. It remains diagnostic and should not be
promoted into the default certificate path until exact interval pricing closure
is operational.

## Audit

Commands run:

- `D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test`
- `D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\oracle_bound_merge_round\raw --csv-out results\oracle_bound_merge_round\certificate_audit.csv --fail-on-error --require-progress-finals results\oracle_bound_merge_round\raw`
- `build\ExactEBRP.exe --method certificate-basis-test --input reference\regen_candidate_V12_M2_average.txt --out results\oracle_bound_merge_round\certificate_basis_test.json`
- `build\ExactEBRP.exe --method option-consistency-test --input reference\regen_candidate_V12_M2_average.txt --out results\oracle_bound_merge_round\option_consistency_test.json`
- `D:\msys64\ucrt64\bin\python.exe scripts\audit_no_instance_special_cases.py --out results\oracle_bound_merge_round\no_instance_special_case_audit.txt`

All optimal claims passed audit. Noncertified rows remain honestly
noncertified.

## Readiness Decision

The project is not ready for a broad paper benchmark matrix. The V20/M3 stress
suite remains at `2/6` certified rows. The round did achieve the minimum target
for `moderate_seed3301`: valid oracle-bound merge reduced the audited
full-frontier gap below `0.05`.

Next recommended action: another targeted exact-closure round focused on the
two remaining `moderate_seed3301` leaves, either by strengthening the compact
objective-bound oracle or making exact BPC leaf closure operational.
