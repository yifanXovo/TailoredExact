# Round 26 frozen evaluation protocol

This protocol was sealed before V12 forensics, candidate development, or any
held-out solve. All runs are serial, one-threaded, Seed 0, and include model
generation, HGA (where applicable), artifact work, native optimization,
verification, certification, and finalization in the process-wall budget.

## Frozen arms

- **P-GRB**: the complete original compact MILP in Gurobi 13.0.2, automatic
  presolve, `MIPGap=0`, `MIPGapAbs=0`, with no HGA, known UB, or Tailored data.
- **C0**: the exact Round 25 `EXT-GRB-COLD` solver-neutral external global-Gini
  tree, static F0 leaf models, independently verified same-run HGA UB,
  non-strict cutoff, frozen interval/scheduler/lifecycle/certificate rules, and
  no explicit cross-model warm start.
- **C1**: at most C0 plus one uniform solver-independent mechanism, with one
  parameter set on every instance. It equals C0 if no prototype passes.
- **S0-REF**: immutable corrected CPLEX S0/F0 historical context; it receives no
  Round 26 optimization work.

No arm may dispatch on instance, family, seed, V, M, path, known objective, or
observed result. There is no plain-Gurobi fallback, warm production arm,
portfolio, restricted-route proof, enumeration, or heuristic proof.

## Sealing and blind choices

The development suite is exactly V12_M1, V12_M2, high3202, moderate3302, and
tight3101. The six new V20 and three V50 files are fixed by the accompanying
SHA-256 manifests. They remain solver-sealed until C1 and its exactness argument
are frozen. Seed substitutions follow the preregistered audit rule in
`heldout_seal.json`; no performance filtering is allowed.

The four long cases are fixed blindly as high-imbalance 5202, moderate 5301,
tight-time 5102, and V50 moderate 6301. They may not be replaced.

## V12 forensics and candidate selection

Run three fresh 300-second repetitions of P-GRB and C0 on each V12 case (12
runs). Classify noise when wall ordering changes but median Work and structure
stay within 5%; structural overhead when C0 repeatedly incurs more Work,
presolve/root/model-read executions, or restarts; otherwise classify mixed.

At most two prototypes may run, only on the five development instances, at no
more than 600 seconds per run. C1 passes development only if all correctness,
coverage, lifecycle, verifier, bound, and certificate gates pass; V12_M1 median
certificate Work/time is no more than 5% worse than P-GRB; V12_M2 is within 5%
or reduces C0's excess deterministic Work by at least 50%; each difficult
development case loses at most 0.02 normalized final-LB and bound-AUC versus
C0; and one uniform parameter set is used. A failed prototype cannot become C1.

## Official matrix

- Stage 0: clean Gurobi-enabled and CPLEX-only builds, all C++/Python tests,
  license/model/import/coverage/lifecycle/scheduler/status/artifact/certificate
  gates, no-dispatch scans, and C0/C1 moderate4301 120-second sentinels.
- Stage 1: 5 development instances x P-GRB/C0/C1 x 1200 seconds = 15 rows.
- Stage 2: 6 sealed V20 x P-GRB/C0/C1 x 1800 seconds = 18 rows.
- Stage 3: 3 sealed V50 x P-GRB/C1 x 1800 seconds = 6 rows.
- Stage 4: 4 fixed long cases x P-GRB/C1 x 3600 seconds = 8 rows.

Exactly 47 official rows are required. Every official P-GRB/C1 pair is ranked
by strict certificate, certificate time, valid final LB, common-UB gap,
normalized bound-progress AUC, then gap-threshold crossings. Each P-GRB win
triggers exactly one enhanced C1 replay (600 seconds for V12/V20, 900 for V50),
which never replaces the official row.

## Frozen promotion rule

C1 is promoted only if every qualitative gate in the task passes and all of:

1. zero correctness, verifier, coverage, lifecycle, bound, or certificate
   failures and zero no-dispatch findings;
2. both V12 regressions meet the development bounds above or are supported as
   timing noise by three-repeat Work/structure evidence;
3. C1 wins at least 80% of non-V12 P-GRB pairs across known and held-out V20,
   with no family having a majority of C1 regressions;
4. held-out V20 mean and median common-UB gap or bound-AUC improve materially;
5. C1 produces at least one strict held-out V20 certificate on a case not
   strictly certified by its matched P-GRB row or not certified at 1800 seconds
   before its fixed 3600-second closure run;
6. all V50 models and bounds validate and C1 wins at least two of three
   1800-second V50 pairs;
7. each non-certified 3600-second C1 row improves its valid global LB after
   the halfway checkpoint (a strict certificate also satisfies this gate);
8. C1 wins or ties at least 80% of C0 pairs, has no family-level majority
   regression, and loses at most 0.02 normalized final-LB/AUC on any difficult
   case;
9. source/manifests prove no warm-start, seed/objective knowledge, portfolio,
   or instance-dependent resolution.

One failed gate retains corrected CPLEX S0/F0 as stable mainline. No mixed
selector is permitted, and official observations cannot change this rule.
