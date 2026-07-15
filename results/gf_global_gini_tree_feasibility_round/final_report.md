# Round 19 global Gini-tree feasibility report

## Decision

Round 19 implemented a mathematically complete, persistent, single-CPLEX-tree
global Gini branch-and-cut mode. Its CPLEX API path is feasible and mechanically
stable with presolve on, traditional search, native best-bound node selection,
default heuristics/probing/cuts, and one thread. Every official global-tree row
uses one environment, one problem, one model read, and one `CPXmipopt`; none
uses a fixed-interval oracle, restart scheduler, time quantum, or child process.

The final classification is **exact but performance-risky**. The mechanism is
not blocked by CPLEX or by row scoping: all exactness audits pass. It retains
useful hard-case behavior, beating Round 18 controlling scheduling on three of
four hard cases at both 300 and 900 seconds. It is not yet ready for promotion,
because the gains are mixed, no hard case certifies, `tight_T_seed3101` loses
substantially, `high_imbalance_seed3201` regresses slightly, and only part of
the legacy control certificates is recovered.

The mode should remain experimental and continue for one focused performance
round. It should not replace the Round 18 controlling mode yet, and it should
not be abandoned.

## Reproducibility and fixed configuration

- Branch: `codex/round19-global-gini-tree-feasibility`.
- CPLEX: IBM ILOG CPLEX 22.1.1.0.
- Executable: `build_round19/ExactEBRP.exe`.
- Executable SHA-256:
  `e602a954108bf091ca721e0cfd53d4cbc2066c0634057bd7ae0e27ac33cac4eb`.
- Official global mode: presolve on, traditional search, best-bound node
  selection, one thread, default CPLEX heuristics/probing/native cuts.
- Row factory: `round19_v2_projected_centering`.
- Same-run incumbent policy: seeded, independently verified, and never imported
  from an earlier result.
- Official matrix: eight instances, four same-binary arms, 300 and 900 seconds,
  serial on one machine.

The official configuration was fixed before Stage 1. Dynamic and auto search
are fail-closed because a reproduced CPLEX 22.1.1 dynamic-search run lost a
continuous-bound sibling despite successful branch return codes. This is an
engineering restriction for this callback design, not a general claim about
all generic CPLEX callbacks.

## What was implemented

`IntervalRowFactory` is now the single deterministic source for fixed-interval
and global-node bounds, rows, family tags, and signatures. It contains all 15
required Round 18 static families: six root-global and nine interval-local.
Low-Gini and variable-S centering use the exact pairwise projection of the
former presolve-sensitive extrema formulation.

The global solver opens one environment and problem, reads one exported root,
registers a generic callback, and makes one `CPXmipopt` call. At an eligible
branching context it reads the current local G bounds and optimal parent
relaxation, creates exactly two gap-free children with
`CPXcallbackmakebranch`, and stores their UIDs and intervals. At each child's
first relaxation, the complete required local pack is forced with
`CPXcallbackaddusercuts(..., CPX_USECUT_FORCE, local=1)`. Descendants inherit
the pack; siblings cannot. Terminal intervals return control to ordinary CPLEX
branching. Solver-final status and bound come from the same problem through
native CPLEX APIs.

## Exactness and engineering evidence

The package contains 24 complete global-tree runs: eight presolve gates, eight
300-second official rows, and eight 900-second official rows.

| Check | Evidence | Failures |
|---|---:|---:|
| Presolve compatibility | 8 gate rows | 0 |
| Root identity / improving-range / recursive branching | 24 each | 0 |
| Parent-child interval coverage | 2,531 branches | 0 |
| Child-estimate validity | 2,531 branches; 1,197 distinct values | 0 |
| Forced local-row sibling isolation | 4,428 attachments | 0 |
| Single-tree lifecycle | 24 runs | 0 |
| Native-bound monotonicity and finalization | 24 runs each | 0 |
| Certificate source and one-thread fairness | 24 runs each | 0 |
| Independent audit suite | 8 scripts | 0 |

All official global rows report zero callback, column-mapping, local-bound,
coverage, child-estimate, local-row, and nonoptimal-relaxation failures. Every
one reports `environment=problem=model_read=mipopt=free=close=1`, native final
best-bound availability, verified incumbent, zero interval oracles, and zero
child processes.

Three standalone V12_M1 fixed-interval LPs reproduce intervals from actual
global child events. Their LPs, result JSONs, logs, commands, and SHA-256 hashes
are retained under `reference_models/`. Deterministic tests verify that the
standalone and callback paths use identical canonical factory signatures and
that projected centering is equivalent to the extrema formulation.

## Matched performance

The tables report valid original-problem lower bounds; higher is better. `*`
marks a certified original problem. `BLOCK` means the process reached the
runner emergency cutoff and contributed no result, bound, or certificate.

### 300 seconds

| Instance | Plain | Legacy static | Controlling static | Global tree |
|---|---:|---:|---:|---:|
| V12_M1 | 0.357201* | 0.348563 | 0.357201* | 0.357201* |
| V12_M2 | 0.623636 | 0.718504* | 0.666387 | 0.703613 |
| tight_T_seed3101 | 0.015875 | 0.107253* | 0.031294 | 0.015058 |
| high_imbalance_seed3202 | 1.066815 | 1.064215 | 1.673126 | 1.613731 |
| moderate_seed3301 | 0.037875 | 0.012288 | 0.044528 | **0.045838** |
| moderate_seed3302 | 0.114499 | 0.030568 | 0.122825 | **0.139485** |
| high_imbalance_seed3201 | 1.977653 | 1.742108 | **2.293179** | 2.284280 |
| tight_T_seed3102 | 0.465853 | 0.315748 | 0.450528 | **0.507093** |

### 900 seconds

| Instance | Plain | Legacy static | Controlling static | Global tree |
|---|---:|---:|---:|---:|
| V12_M1 | 0.357201* | 0.353172 | 0.357201* | 0.357201* |
| V12_M2 | 0.645351 | 0.718504* | 0.718504* | 0.718504* |
| tight_T_seed3101 | 0.018607 | 0.107253* | 0.031507 | 0.016723 |
| high_imbalance_seed3202 | 1.137835 | 1.749313* | 1.707011 | 1.648983 |
| moderate_seed3301 | 0.040436 | BLOCK | 0.046648 | **0.046742** |
| moderate_seed3302 | 0.119626 | BLOCK | 0.124548 | **0.139491** |
| high_imbalance_seed3201 | 2.039049 | BLOCK | **2.303605** | 2.289518 |
| tight_T_seed3102 | 0.478265 | BLOCK | 0.450528 | **0.523303** |

Against controlling scheduling, global tree wins four, loses three, and ties
one row at 300 seconds. At 900 seconds it wins three, loses three, and ties two.
On the four hard cases it wins three and loses one at both budgets. Against
plain CPLEX it wins six, loses one, and ties one at both budgets.

Certificate counts are:

| Budget | Plain | Legacy | Controlling | Global tree |
|---|---:|---:|---:|---:|
| 300 s | 1/8 | 2/8 | 1/8 | 1/8 |
| 900 s | 1/8 | 3/4 fresh + 4 blocked | 2/8 | 2/8 |

The global tree therefore matches Round 18 controlling's certificate count but
does not preserve all legacy certificates. It recovers V12_M2 by 900 seconds,
but not tight_T_seed3101 or high_imbalance_seed3202.

## Blocked rows and timeout policy

All 64 matrix slots were executed or retained as explicit blockers. There are
60 fresh result JSONs and four blocked 900-second legacy-scheduler rows:

- `moderate_seed3301`: 920.0265 s;
- `moderate_seed3302`: 920.0176 s;
- `high_imbalance_seed3201`: 922.3515 s including kill cleanup; and
- `tight_T_seed3102`: 920.0307 s.

They all have `return_code=-98`, `runner_emergency_timeout=true`, and
`engineering_blocker=runner_emergency_timeout`. They contribute no bound or
certificate. The initially too-large +120-second emergency policy and its
correction are disclosed in `interrupted_attempts/timeout_policy_incident.md`;
the interrupted partial controlling row is retained and excluded from every
comparison.

## Answers to the 23 required questions

1. **Was a complete recursive global Gini tree implemented?** Yes. Eligible
   descendants recursively split to ten observed generations; terminal nodes
   use ordinary CPLEX branching in the same tree.

2. **Does every official global-tree run use exactly one environment, problem,
   and `CPXmipopt`?** Yes. All 16 official global rows, and all eight gates,
   pass the one/one/one lifecycle audit.

3. **Was the Round 18 restart mechanism completely removed from global-tree
   mode?** Yes. Interval-oracle count, child-process count, and time-quantum use
   are all zero. Solver state, cuts, incumbents, pseudo-costs, and node queue
   remain in the one CPLEX solve.

4. **Is native best-bound node selection active?** Yes.
   `CPXPARAM_MIP_Strategy_NodeSelect=1` is requested and effective in every
   global run.

5. **Are child estimates valid and nonconstant?** Yes, with a limitation.
   All 2,531 checked branch estimates equal a certified optimal parent
   relaxation and are valid lower estimates; there are 1,197 distinct values
   across the tree. Siblings currently receive the same parent estimate, so the
   estimate is not child-discriminating.

6. **Can recursive Gini branching coexist with presolve?** Yes. All four
   presolve-on gates pass, match the exact path, and the official mode retains
   presolve on. The exact pairwise centering projection was necessary to avoid
   presolve-eliminated extrema columns.

7. **Can heuristics, probing, and native cuts remain enabled?** Yes. They remain
   at CPLEX's automatic/default settings; none is explicitly disabled. Reported
   heuristic/probing value zero denotes the automatic policy, not an off
   override. Native cuts remain default.

8. **Is traditional search required by the CPLEX branch callback?** It is
   required for this Round 19 implementation. Dynamic search reproduced lost
   continuous-bound siblings and false optimality. This is not asserted as a
   universal generic-callback restriction.

9. **If dynamic search is unavailable, is traditional best-bound search
   stable?** Yes mechanically. Twenty-four global runs complete with zero
   callback/coverage/isolation/finalization failures and monotone native bounds.

10. **Does the global-tree root model exactly preserve the original problem?**
    Yes for optimization and certification. It keeps the original objective
    and all original feasible improving solutions, adds only valid global
    strengthening and the non-strict verified-incumbent cutoff, and covers the
    full improving G range. Root/objective/row fingerprints are retained.

11. **Are all Round 18 paper-safe static families migrated without omission?**
    Yes: six root-global plus nine interval-local families. The run fails closed
    if an unsupported callback or bucket family is active.

12. **Are interval-local rows identical to standalone fixed-interval rows?**
    Yes by shared construction and deterministic signature tests. Three actual
    child intervals also have retained standalone LP exports and hashes.

13. **Is sibling leakage zero?** Yes. All 4,428 attachments use forced local
    user cuts with `local=1`; the isolation audit has zero failures.

14. **Does the native global lower bound remain valid and monotone?** Yes. All
    24 global bound trajectories have zero monotonicity violations, and bounds
    are reported only from the native single problem.

15. **Does native solver-final best-bound retrieval work reliably at the
    deadline?** Yes. Every official and gate global row reaches native
    finalization and returns a valid `CPXgetbestobjval` result; wrapper synthesis
    is zero.

16. **Are legacy control certificates preserved or recovered?** Partly. Global
    tree preserves V12_M1 and recovers V12_M2 at 900 seconds, matching the
    controlling mode's 1/8 and 2/8 certificate counts. It does not recover the
    legacy tight_T_seed3101 or high_imbalance_seed3202 certificates.

17. **Does the global tree retain the hard-case gains observed with Round 18
    controlling scheduling?** Mostly, but not uniformly. It wins on
    moderate_seed3301, moderate_seed3302, and tight_T_seed3102 at both budgets;
    it loses slightly on high_imbalance_seed3201. No hard case certifies.

18. **Does tight_T_seed3102 avoid the 10,629-restart failure mechanism?** Yes
    architecturally: it uses one `CPXmipopt`, zero interval oracles/restarts, and
    a native final bound. It also beats controlling by 0.056565 at 300 seconds
    and 0.072775 at 900 seconds.

19. **Does moderate_seed3302 improve once restart overhead is removed?** Yes.
    Its global lower bound exceeds controlling by 0.016660 at 300 seconds and
    0.014943 at 900 seconds, reducing the gap from 0.3722 to 0.2870 and from
    0.3634 to 0.2870 respectively. It still does not certify.

20. **How does performance compare at both budgets?** The two matched tables
    above are authoritative. Global tree is much stronger than plain on six of
    eight rows, mixed against controlling, weaker than legacy on several
    controls, and strongest on three of four hard cases. Its certificates match
    controlling, not legacy.

21. **What is the classification?** **Exact but performance-risky.** It is not
    API-blocked: recursive intervals, presolve, row scope, lifecycle, and native
    bounds all work. Mixed controls and incomplete hard-case closure prevent a
    promising/default-method claim.

22. **Should it remain experimental, continue, or be abandoned?** Keep it
    experimental and continue for one targeted optimization round. Do not make
    it the default yet; do not abandon the one-tree direction.

23. **What is the single next optimization target?** Add **child-specific,
    factory-derived valid lower estimates at Gini branch creation**, using the
    incremental interval-local row delta without launching auxiliary solves.
    The current parent-copy estimates are safe but cannot distinguish siblings;
    improving them lets native best-bound search prioritize the useful Gini
    subtree while preserving the one-tree exactness contract.

## Artifact map

- Full rows: `official_full_matrix.csv`.
- Matched comparison: `matched_four_arm_comparison.csv`.
- Audit rollup: `audit_summary.csv`.
- Node/bound evidence: `global_node_trace.csv` and
  `global_bound_trajectory.csv`.
- Lifecycle and certificate evidence: `single_tree_lifecycle_audit.csv`,
  `native_solver_finalization_audit.csv`, and `certificate_source_audit.csv`.
- Family/equivalence/isolation evidence: `global_local_row_registry.csv`,
  `fixed_interval_node_row_equivalence_audit.csv`, and
  `sibling_local_row_isolation_audit.csv`.
- Reference models: `reference_models/`.
- Commands/raw/logs/traces/root models/manifests: their like-named package
  directories.
- Exactness proof: `../../docs/global_gini_tree_exactness.md`.
- CPLEX boundary: `../../docs/global_gini_tree_cplex_capability.md`.
