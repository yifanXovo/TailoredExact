# Round 25 frozen evaluation protocol

Protocol version: `round25-v1`.  This document and the adjacent manifests are
frozen before official execution.  No Round 25 outcome may change an arm,
instance, budget, seed, diagnostic rule, or Stage 2 selection.

## Scientific scope and invariant semantics

This is a candidate-validation round, not an algorithm-development or default
migration round.  It changes neither the mathematical formulation nor split,
scheduler, row-factory, certificate, lifecycle, cutoff, HGA, or dispatch
semantics.  Corrected CPLEX S0/F0 remains the stable paper reference.  No option
depends on the instance name, path, family, seed, size, difficulty, or observed
solver behavior.  The unsafe persistent CPLEX presolve-on arm is excluded.

Every run is serial and single-threaded.  Its process-wall budget includes HGA,
artifact construction, lookup and hashing, model read, presolve/root work, all
optimize calls, logs, serialization, verification, certificate construction,
and finalization.  The native solve allowance is uniformly 98% of the process
wall budget, leaving the same 2% finalization reserve in every arm.  Tailored
arms use an explicit same-run HGA budget of 10 seconds and seed `20260626`; only
an independently verified HGA incumbent may be used.  Plain arms receive no HGA
solution, Tailored information, or known UB.

The CPLEX and Gurobi plain arms use the same canonical complete original compact
MILP.  All strict-certificate statements use engineering-exact original-problem
semantics and require the relevant native, verifier, consistency, lifecycle,
and coverage evidence.  Relative and absolute native MIP gaps are zero.

## Frozen arms

`P-CPX` is the complete original compact MILP in one-thread plain CPLEX with
native/default presolve, cuts, heuristics, and branching.

`P-GRB` is the identical canonical original compact MILP in one-thread Gurobi,
automatic/default presolve, Seed 0, `MIPGap=0`, and `MIPGapAbs=0`.

`S0-SAFE` is corrected persistent CPLEX S0/F0: traditional native global Gini
tree, parent-copy estimates, full inherited rows, deferred row timing, presolve
off, Reduce 0, Linear 0, one thread/tree, and P1/P2/F3/native MIP start off.

`EXT-CPX` is the solver-neutral external static F0 interval tree with CPLEX
presolve on, the independently verified same-run HGA UB, non-strict cutoff, and
the current frozen hierarchy, row factory, scheduler, parent-bound inheritance,
artifact cache, lifecycle rules, and certificate logic.

`EXT-GRB-COLD` applies the identical external algorithm and immutable cached
leaf artifacts through one-thread Gurobi with automatic/default presolve and no
explicit cross-model warm start.  It is the principal migration candidate.

`EXT-GRB-WARM` differs from `EXT-GRB-COLD` only by allowing complete,
independently verified same-run primal starts to be mapped to compatible newly
created leaves.  Starts are primal evidence only.  It is a secondary research
arm and cannot become a default from selected wins.

The full exact argv and executable/source/protocol hashes for each arm are in:
`p_cpx_manifest.json`, `p_grb_manifest.json`, `s0_safe_manifest.json`,
`ext_cpx_manifest.json`, `ext_grb_cold_manifest.json`, and
`ext_grb_warm_manifest.json`.

## Frozen instances and stages

Stage 0 runs all build, test, license, native-import, canonical-identity,
certificate, verifier, coverage, lifecycle, cache, warm-start, status, S0
default, HGA-origin, and static no-dispatch gates.  It then runs the 120-second
`moderate_seed4301` sentinel on `S0-SAFE`, `EXT-CPX`, and `EXT-GRB-COLD` and
requires retained verified witnesses with no contradicted infeasibility.

Stage 1 is exactly 48 rows at 900 process-wall seconds: every frozen arm on
`V12_M1`, `V12_M2`, `high_imbalance_seed3202`,
`high_imbalance_seed4201`, `moderate_seed3302`, `moderate_seed4302`,
`tight_T_seed3101`, and `tight_T_seed4101`.

Stage 2 is exactly 24 rows at 1200 process-wall seconds: every frozen arm on the
preselected difficult subset `high_imbalance_seed3202`,
`high_imbalance_seed4201`, `moderate_seed4302`, and `tight_T_seed3101`.
Stage 1 results cannot change this subset or its options.

Exact source paths and SHA-256 values are frozen in
`round25_instance_manifest.csv`.  An input failure or difficulty never permits
replacement.

## Reporting-only common UB and trajectory metrics

For an instance/horizon, the reporting common UB is the minimum independently
verified UB among all six official rows at that horizon.  It is calculated only
after the rows finish, never passed into a solver, and never used to alter an
official result.  A diagnostic replay is assessed against that instance's
already frozen Stage 1 common UB and cannot improve it.  The rule is frozen in
`round25_common_ub_manifest.csv`.

Common-UB relative gap is `max(0,(common_ub-valid_lb)/abs(common_ub))` when both
quantities are valid and the denominator is nonzero.  Bound-progress AUC uses
the monotone valid-LB trajectory, the reporting common UB, linear trapezoidal
integration over the complete process-wall horizon, and normalization to
`1-gap_auc`.  Gap thresholds are 10%, 5%, 1%, and 0.1%; reported crossings are
the adjacent observation interval, not interpolated point estimates.  Missing
or unsupported evidence is reported unavailable, never imputed.

## Preregistered underperformance diagnostics

After all 48 Stage 1 rows, compare `EXT-CPX` with `P-CPX` and
`EXT-GRB-COLD` with `P-GRB`, in this lexicographic hierarchy:

1. strict certificate;
2. lower process-wall certificate time if both certify;
3. higher valid final LB if neither certifies;
4. lower reporting common-UB gap;
5. higher bound-progress AUC.

Every external arm that loses triggers exactly one 300-second replay with the
same executable, options, seed, split/scheduler/HGA/cutoff/row/warm policy.
The replay is diagnostic only and cannot replace its official row.

`EXT-GRB-WARM` is similarly compared with `EXT-GRB-COLD`, but its loss must be
material: certificate time tolerance is `max(1 second, 1% of cold time)`, valid
LB tolerance is `max(1e-9, 1e-6*max(1,abs(cold LB)))`, common-gap tolerance is
`1e-5`, and normalized AUC tolerance is `1e-3`.  Each materially losing warm
pair triggers exactly one otherwise identical 300-second warm replay.

Each replay retains the enhanced attempt trace and receives one evidence-based
classification from: repeated presolve/root overhead; excessive native model
restarts; model build/read/I/O overhead; weak leaf lower bounds; overly coarse
or late Gini splitting; controlling-leaf or scheduler stagnation; native
backend weakness on the interval formulation; incumbent/cutoff weakness;
warm-start rejection or overhead; numerical instability; performance ordering
not reproduced and therefore unstable; or insufficient evidence.  No diagnosis
authorizes an algorithm repair in this round.

## Audit, ranking, and publication rules

An affected row is blocked by any model-equivalence, license, import,
certificate, verifier, status, coverage, consistency, or lifecycle failure.
There is no solver fallback.  Correctness-valid results are ranked by strict
certificate, certificate process-wall time, valid final LB, common-UB gap, AUC,
and threshold crossing.  Paired views remain separate for backend strength,
Tailored benefit by backend, external backend comparison, warm effect, and both
external candidates versus S0.  No family-dependent selector is created.

Native presolve/root timing and cut counts are recorded only where the API
provides safe direct evidence.  Unsupported CPLEX or Gurobi phase timers are
explicitly unavailable and are not estimated.  Complete raw evidence is kept;
files of at least 4 MiB are losslessly and deterministically gzip-compressed
with level 9, zero timestamp, no embedded filename, and verified restored hash
and size.

Round 25 may classify external Gurobi and recommend a later production round,
but cannot alter defaults, promote a warm-start variant automatically, or
create a portfolio.  Publication is a normal non-force branch push; main is not
modified or merged.

