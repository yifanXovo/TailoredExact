# Round 25 final report

## Decision

`EXT-GRB-COLD` is **ready for a full production validation round** and is broadly nonregressive against
plain Gurobi. It wins the frozen hierarchy on 10/12 matched rows
versus `P-GRB`, 12/12 versus `EXT-CPX`, and 12/12
versus `S0-SAFE`. Its two losses to plain Gurobi are the preregistered V12
certificate-time triggers; every non-V12 family/seed row favors the cold
external arm, including all three held-out V20 seeds and all four 1200-second
rows. This is enough to justify a later full production validation round, but
not a production-default migration in Round 25.

`EXT-GRB-WARM` is **mixed**: warm wins 5/12 and cold wins
7/12. Only 6 of
156 official candidates were accepted
(24 submitted;
150 rejected), and two material Stage 1
warm losses triggered diagnostics. It does not become the default.

Corrected CPLEX `S0-SAFE` remains the stable paper/mainline reference. No
default, dispatch rule, portfolio, or family-dependent selector changed.

## Provenance, qualification, and exactness

The authoritative local base is `d52e340ef62be2bc2f248a1c5ad93cbbb75c6920`;
the frozen executable was built from Round 25 implementation commit
`2017358042c48c44c4386256a904bba0f3bcbf85`. The observed `origin/main` was
`639c3772687d4a22e6b2cf3daa4d16c03d015ecd`. The frozen unified executable is
`a8e6d9abee48fee832f0277e9635ef1518c9563f1b32f10ddab3690b4759f4d1` and the CPLEX-only control is
`e399af58f8a853bb9e5691d77d18e14cecb3388521ac926536eba8bb847c9047`. Solver versions are CPLEX
22.1.1.0 and Gurobi 13.0.2.

Both clean release configurations passed 9/9 C++ tests (18/18 total). All six
Python regression scripts passed. Static exactness passed 29/29 checks with
zero production instance/seed dispatch matches. Native Gurobi import, domain,
name, type, and bound audits passed on 10/10 inputs. The four tiny qualification
runs passed, including two strict toy certificates with zero CPLEX/Gurobi
objective delta. The moderate4301 sentinel passed 3/3 arms, retained three
verified witnesses, and reported zero contradicted infeasibilities.

All 79 retained sentinel/official/diagnostic rows are authoritative,
have verified witnesses, and pass every applicable verifier, coverage,
lifecycle, and consistency gate. There are 0 correctness
failures.

## Official outcomes and strict certificates

Round 25 completed 72/72 official processes:
48 at 900 seconds and 24 at 1200 seconds.
Completed/failed/interrupted/excluded counts are
72/0/0/0.
Of the completed rows, 57 ended at a valid solver time limit and 15
ended optimal/strict; time-limited completion is not counted as interruption.

| Horizon | P-CPX | P-GRB | S0-SAFE | EXT-CPX | EXT-GRB-COLD | EXT-GRB-WARM |
| --- | --- | --- | --- | --- | --- | --- |
| 900s | 1/8 | 2/8 | 2/8 | 2/8 | 3/8 | 3/8 |
| 1200s | 0/4 | 0/4 | 0/4 | 0/4 | 1/4 | 1/4 |

## Frozen paired hierarchy

Win columns are `left-right-tie`; strict columns and mean gap/AUC columns are
also `left-right`. The ranking is certificate, certificate time, valid LB,
common-UB gap, then AUC; never relative gap with different UBs.

| Horizon | Comparison | Wins | Strict | Mean common gap | Mean AUC |
| --- | --- | ---: | ---: | ---: | ---: |
| 900s | plain CPLEX versus plain Gurobi | 0-8-0 | 1-2 | 0.4287-0.3585 | 0.5542-0.6171 |
| 1200s | plain CPLEX versus plain Gurobi | 0-4-0 | 0-0 | 0.6221-0.5432 | 0.3632-0.4218 |
| 900s | plain CPLEX versus EXT-CPX | 0-8-0 | 1-2 | 0.4287-0.1735 | 0.5542-0.7944 |
| 1200s | plain CPLEX versus EXT-CPX | 0-4-0 | 0-0 | 0.6221-0.2278 | 0.3632-0.7354 |
| 900s | plain Gurobi versus EXT-GRB-COLD | 2-6-0 | 2-3 | 0.3585-0.1374 | 0.6171-0.8256 |
| 1200s | plain Gurobi versus EXT-GRB-COLD | 0-4-0 | 0-1 | 0.5432-0.2045 | 0.4218-0.7616 |
| 900s | external CPLEX versus external Gurobi | 0-8-0 | 2-3 | 0.1735-0.1374 | 0.7944-0.8256 |
| 1200s | external CPLEX versus external Gurobi | 0-4-0 | 0-1 | 0.2278-0.2045 | 0.7354-0.7616 |
| 900s | cold versus warm external Gurobi | 4-4-0 | 3-3 | 0.1374-0.1345 | 0.8256-0.8265 |
| 1200s | cold versus warm external Gurobi | 3-1-0 | 1-1 | 0.2045-0.1972 | 0.7616-0.7608 |
| 900s | S0-SAFE versus EXT-CPX | 1-7-0 | 2-2 | 0.2385-0.1735 | 0.7440-0.7944 |
| 1200s | S0-SAFE versus EXT-CPX | 0-4-0 | 0-0 | 0.3708-0.2278 | 0.6115-0.7354 |
| 900s | S0-SAFE versus EXT-GRB-COLD | 0-8-0 | 2-3 | 0.2385-0.1374 | 0.7440-0.8256 |
| 1200s | S0-SAFE versus EXT-GRB-COLD | 0-4-0 | 0-1 | 0.3708-0.2045 | 0.6115-0.7616 |

Plain Gurobi beats plain CPLEX on all 8/8 Stage 1 and 4/4 Stage 2 rows.
EXT-CPX beats plain CPLEX on all 12 matched rows. Cold external Gurobi beats
plain Gurobi 6-2 at 900 seconds and 4-0 at 1200 seconds; it beats EXT-CPX and
S0-SAFE 8-0 then 4-0. EXT-CPX beats S0-SAFE 7-1 then 4-0. Warm/cold is 4-4 at
900 seconds and 1-3 at 1200 seconds.

### Cold external Gurobi versus plain Gurobi by family

| Horizon | Family | P-GRB-cold wins | Mean common gap | Mean AUC |
| --- | --- | ---: | ---: | ---: |
| 900s | high_imbalance | 0-2-0 | 0.2088-0.0044 | 0.7279-0.9631 |
| 900s | moderate | 0-2-0 | 0.6693-0.2538 | 0.3295-0.6705 |
| 900s | tight_T | 0-2-0 | 0.5561-0.2916 | 0.4167-0.6846 |
| 900s | v12 | 2-0-0 | 0.0000-0.0000 | 0.9943-0.9843 |
| 1200s | high_imbalance | 0-2-0 | 0.2018-0.0023 | 0.7446-0.9722 |
| 1200s | moderate | 0-1-0 | 1.0000-0.3337 | 0.0000-0.5967 |
| 1200s | tight_T | 0-1-0 | 0.7694-0.4795 | 0.1979-0.5052 |

The only family regression is V12 certificate time. High-imbalance, moderate,
and tight-T all favor cold external Gurobi on both hard-stress and held-out
seeds, so the result does not depend on a selected seed or warm-start luck.
No held-out V20 seed produced a strict certificate, however; all produced valid
bounds. That missing held-out certificate coverage blocks production migration
now and is a required target of the recommended full production validation.

## Common-gap and trajectory summaries

Values are mean/median across the fixed instances. Exact per-row AUC and all
304 observed threshold-crossing interval records are retained in
`bound_progress_auc.csv` and `time_to_gap_thresholds.csv`.

| Horizon | Arm | Strict | Common gap mean/median | AUC mean/median |
| --- | --- | ---: | ---: | ---: |
| 900s | P-CPX | 1/8 | 0.4287 / 0.3698 | 0.5542 / 0.6143 |
| 900s | P-GRB | 2/8 | 0.3585 / 0.3344 | 0.6171 / 0.6518 |
| 900s | S0-SAFE | 2/8 | 0.2385 / 0.0900 | 0.7440 / 0.8942 |
| 900s | EXT-CPX | 2/8 | 0.1735 / 0.0776 | 0.7944 / 0.8931 |
| 900s | EXT-GRB-COLD | 3/8 | 0.1374 / 0.0549 | 0.8256 / 0.9157 |
| 900s | EXT-GRB-WARM | 3/8 | 0.1345 / 0.0515 | 0.8265 / 0.9164 |
| 1200s | P-CPX | 0/4 | 0.6221 / 0.6131 | 0.3632 / 0.3689 |
| 1200s | P-GRB | 0/4 | 0.5432 / 0.5545 | 0.4218 / 0.4131 |
| 1200s | S0-SAFE | 0/4 | 0.3708 / 0.3107 | 0.6115 / 0.6726 |
| 1200s | EXT-CPX | 0/4 | 0.2278 / 0.1910 | 0.7354 / 0.7565 |
| 1200s | EXT-GRB-COLD | 1/4 | 0.2045 / 0.1692 | 0.7616 / 0.7837 |
| 1200s | EXT-GRB-WARM | 1/4 | 0.1972 / 0.1538 | 0.7608 / 0.7828 |

## Lifecycle and restart accounting

Counts below sum all 72 official rows. Restart columns are
fresh/same-leaf/child. CPLEX external presolve/root counts and phase times are
marked unavailable because callable-library logging cannot safely isolate them
per leaf; native phase time is also unavailable from the Gurobi C API. These
values are not estimated.

| Arm | Optimize | Model reads | Artifacts | Presolve | Root | Restarts | Splits | Closures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P-CPX | 12 | 12 | 0+0 hits | 12 | 12 | 0/0/0 | 0 | 0 |
| P-GRB | 12 | 12 | 0+0 hits | 12 | 12 | 0/0/0 | 0 | 0 |
| S0-SAFE | 12 | 12 | 0+0 hits | 0 | 12 | 0/0/0 | 0 | 0 |
| EXT-CPX | 274 | 274 | 178+96 hits | unavailable (12 rows) | unavailable (12 rows) | 274/0/178 | 70 | 48 |
| EXT-GRB-COLD | 248 | 155 | 155+93 hits | 248 | 154 | 155/93/155 | 59 | 55 |
| EXT-GRB-WARM | 248 | 156 | 156+92 hits | 248 | 155 | 156/92/156 | 59 | 56 |

## Preregistered diagnostics

Exactly 4 pairs triggered and all
4 exactly-once 300-second replays
completed. They remain diagnostic and do not replace official rows.

| Trigger | Official reason | Replay outcome | Evidence-based classifications |
| --- | --- | --- | --- |
| V12_M1__ext_grb_cold | both_strict_plain_lower_certificate_wall_time | performance_ordering_not_reproduced_and_therefore_unstable | performance ordering not reproduced and therefore unstable, repeated presolve/root overhead, excessive native model restarts |
| V12_M2__ext_grb_cold | both_strict_plain_lower_certificate_wall_time | official_ordering_reproduced_at_300s | repeated presolve/root overhead, excessive native model restarts |
| moderate_seed3302__ext_grb_warm | plain_higher_valid_final_lb | official_ordering_reproduced_at_300s | repeated presolve/root overhead, excessive native model restarts, weak leaf lower bounds, warm-start rejection or overhead |
| tight_T_seed3101__ext_grb_warm | plain_higher_valid_final_lb | performance_ordering_not_reproduced_and_therefore_unstable | performance ordering not reproduced and therefore unstable, repeated presolve/root overhead, excessive native model restarts, weak leaf lower bounds, controlling-leaf or scheduler stagnation, warm-start rejection or overhead |

V12_M1 reverses its very small official certificate-time ordering in replay
(cold 35.280s versus the official plain 35.321s), so that loss is unstable.
V12_M2 reproduces the plain advantage (169.341s versus replay cold 174.701s),
with repeated native model/presolve/root execution. The moderate3302 warm loss
is reproduced at 300 seconds (cold LB 0.159864 versus replay warm 0.159609).
The tight-T warm loss reverses at 300 seconds (cold LB 0.052886 versus replay
warm 0.052925), hence unstable. Complete enhanced traces and per-trigger reports
are retained; unsupported phase timers remain explicitly unavailable.

## Evidence accounting and limitations

Official process wall totals 16h 50m 49.5s; all 79 retained solve
rows total 17h 9m 40.0s, excluding build/test/reporting overhead.
The package currently contains 2171 files and
284.5 MiB. Its largest artifact is
`results/gf_solver_backend_validation_round25/runs/stage1__V12_M1__p_cpx__900s/dense_progress.csv.gz` at 21328820 bytes. Large/dense files and
the text LP model corpus are deterministic gzip streams with restored hashes
and byte counts recorded in compression manifests. The final package audit
independently restored and hash-verified
586 compressed
files and found no retained sensitive license marker.

There were no failed diagnostics, contradictory rows, missing official rows,
silent backend fallbacks, or invalid bounds. The main limitation is unavailable
safe per-leaf CPLEX presolve/root timing (and unavailable native Gurobi phase
timers/cut totals), which prevents converting repeated phase counts into exact
time attribution. Warm-start behavior is mixed and largely rejected. These
limitations support retaining CPLEX S0/F0 as mainline while advancing cold
external Gurobi to a dedicated production-validation round.
