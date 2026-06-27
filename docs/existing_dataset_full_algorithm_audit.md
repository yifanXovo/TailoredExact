# Existing Dataset Full-Algorithm Audit

This round reran the complete paper-core algorithm with native HGA-TGBC upper
bounds and explicit UB event logging.

| case | status | UB | LB | gap | certificate | UB improved after initial |
| --- | --- | ---: | ---: | ---: | --- | --- |
| V4 smoke | optimal | 0 | 0 | 0 | original-problem certified | no |
| regenerated V12 M2 average | optimal | 0.718504070755 | 0.718504070755 | 0 | relaxation-only full-frontier certificate | no |
| regenerated V12 M1 average | gcap_frontier_not_closed | 0.357200583208 | 0.332675660948 | 0.0686586848205 | noncertified | no |
| regenerated V12 M2 average, greedy start | optimal | 0.718504070755 | 0.718504070755 | 0 | original-problem certified | yes, local re-decode repair |

The V12 M2 claim is now backed by raw JSON in
`results/exact_primal_stress_round/raw/v12_m2_core_300s.json` and by the
local audit CSV in `results/exact_primal_stress_round/certificate_audit.csv`.
The prior concern that a `0.7185` statement was not raw-backed is resolved for
this round's artifact.

V12 M1 remains noncertified in the 300-second row even with a strong verified
native HGA-TGBC incumbent. The plateau is not primal quality: the final UB is
already `0.357200583208`. The active issue is lower-bound/frontier closure.
