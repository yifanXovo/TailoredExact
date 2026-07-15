# Round 19 Current State and CPLEX API Plan

## Source and worktree state before implementation

- Local project: `E:/codes/ExactEBRP`.
- Initial local HEAD: `97e0be26b95e3c978a590db4606398624fc9137d` on
  `codex/round18-controlling-leaf-scheduler`.
- Read-only `git ls-remote --heads origin main` result:
  `e1666c2cfb5243469712398ed0c6672fe4e33d29`.
- The remote commit was initially absent from the local object database, so one
  targeted `git fetch --no-tags origin main:refs/remotes/origin/main` was used
  only for inspection. No pull, rebase, reset, clean, clone, or force operation
  was used.
- Local HEAD tree and GitHub `main` tree are identical:
  `f040603b34f613cc14b58da2fd6939b994e862ca`. The SHA difference is only the
  tree-identical GitHub merge commit.
- Round 19 branch:
  `codex/round19-global-gini-tree-feasibility`, created from the verified local
  source state.
- Pre-existing tracked modifications to preserve:
  `results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv`
  and
  `results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json`.
- Pre-existing untracked protected artifacts include manuscript aux/bbl/blg/out
  files, `build_round18/`, manual results, prior raw sidecars and progress
  traces, optimization scratch JSON, and `scripts/__pycache__/`.
- Pre-existing executables are under `build/`, `build-codex/`, and
  `build_round18/`; Round 19 will use only `build_round19/`.

## Round 18 behavior and restart limitation

Round 18 retained the paper-safe static fixed-interval formulation and changed
only leaf scheduling. Its controlling set is recomputed from current valid leaf
bounds, tied leaves are water-filled deterministically, and requested quanta
grow as `30*2^k`. Every attempt rebuilds and resolves a fixed-interval model;
CPLEX pseudo-costs, incumbent state, cuts, node queue, and processed nodes are
not resumed. The final report records 72/72 official rows and no audit failures,
but six legacy certificates were lost and `tight_T_seed3102` regressed. The
reported next target is restart-amortized persistent fixed-interval solving.

## Current callback implementation

`TailoredBCCplexApi.cpp` dynamically loads `cplex2211.dll`, reads one exported
LP, installs a generic callback, and makes one `CPXmipopt` call. Its callback
can inspect relaxation/candidate points, separate several optional valid cuts,
and perform a diagnostic one-shot Gini split. The Gini branch state is global:
`gini_branch_created` prevents all descendant Gini splits. When that path is
enabled the current code explicitly selects traditional search, disables
presolve, and disables heuristics. Those settings originated in the diagnostic
branch smoke implementation, which assumed stable unpresolved column indices;
they are not an installed-API requirement for generic callbacks.

## Verified CPLEX 22.1.1 boundary

The local installation is IBM ILOG CPLEX Optimization Studio 22.1.1 under
`C:/Program Files/IBM/ILOG/CPLEX_Studio2211`.

Verified from the installed 22.1.1 headers and HTML reference:

- `CPXcallbacksetfunc` registers a generic callback on one problem object.
- `CPX_CALLBACKCONTEXT_BRANCHING` is `0x0080`; relaxation, candidate, and
  global-progress contexts are also available.
- `CPXcallbackgetlocallb` and `CPXcallbackgetlocalub` are permitted in branching
  context and return current-node local bounds.
- `CPXcallbackgetrelaxationpoint` returns the current relaxation point and
  objective in branching context.
- `CPXCALLBACKINFO_NODEUID`, `CPXCALLBACKINFO_NODEDEPTH`,
  `CPXCALLBACKINFO_BEST_BND`, `CPXCALLBACKINFO_BEST_SOL`, and
  `CPXCALLBACKINFO_NODECOUNT` are available through the typed callback-info
  routines.
- `CPXcallbackmakebranch` accepts original-space variable bound changes and
  additional original-space linear constraints, a node estimate, and returns a
  unique child sequence number. Rows supplied to one branch define that child
  and descendants, not its sibling.
- Generic callback actions are expressed in the original model while CPLEX maps
  them to its presolved model. Branching context may cause CPLEX to suppress
  some presolve reductions automatically, but the API does not require setting
  `CPXPARAM_Preprocessing_Presolve` (`1030`) to off.
- Generic callbacks are compatible with dynamic search. Legacy control
  callbacks are not; this implementation uses the generic API only.
- `CPXPARAM_MIP_Strategy_NodeSelect` is `2018`; value
  `CPX_NODESEL_BESTBOUND` is `1` and is the documented best-bound rule.
- `CPXPARAM_MIP_Strategy_Search` is `2109` with auto/traditional/dynamic values
  0/1/2. Mechanical gates will determine the official effective search mode;
  no mode will be described as required unless the run demonstrates it.
- `CPXPARAM_TimeLimit`/legacy `CPX_PARAM_TILIM` is `1039`.
  `CPXgetbestobjval` is the post-solve native global-bound source.
- Probing (`2042`), heuristic frequency (`2031`), presolve (`1030`), and native
  cuts need not be disabled for a generic branching callback. The official
  candidate keeps their defaults unless a reproduced failure proves otherwise.
- The generic callback must call only routines taking a callback-context
  pointer. Model/environment API calls remain outside callback execution.

## Planned exact global-tree architecture

1. Run the existing same-run seeded paper primal heuristic and independent
   verifier exactly as the frontier mode already does.
2. Derive the complete root range
   `[0,min(U,(V-1)/V)]` from the verified incumbent `U`, nonnegative penalty,
   and the global Gini bound. Add `original objective <= U`, never `U-epsilon`.
3. Build one exact compact root LP with unchanged objective `G + lambda*P`.
4. Route all Round 18 static interval-dependent formulas through a deterministic
   canonical row factory. The standalone fixed-interval reference builder and
   global-tree callback use the same factory and signatures.
5. Keep globally valid families once at the root. Represent interval bounds as
   child bound changes and attach every required interval-local row directly to
   each child through `CPXcallbackmakebranch`.
6. Recover each node interval only from current local `G` bounds. Use the shared
   legacy/adaptive geometry functions (same initial range, split factor, depth,
   and width eligibility) and recursively create two gap-free children while
   eligible. Otherwise return without creating a branch so ordinary CPLEX
   branching proceeds.
7. Use the current relaxation objective as both child estimates, explicitly set
   best-bound node selection, retain one environment/problem/`CPXmipopt`, and
   retrieve the solver-final bound from that problem.
8. Record callback node events, child IDs, bounds, estimates, row families and
   signatures, global-bound trajectory, feature settings, and lifecycle counts.
9. Reconstruct any incumbent route plan and re-run the independent verifier
   before accepting it or an optimality certificate.

## Row-scope plan

Globally valid Round 18 families include the original compact formulation,
inventory conservation, movement-reachability global bounds, visit/final-
inventory linking, global handling capacity, route support-duration cuts, and
pairwise transfer compatibility. Interval-local families include penalty-budget
inventory bounds, direct Gini cap/floor rows, interval-tight McCormick rows,
Gini spread, required movement induced by local inventory bounds, low-Gini
centering and variable-S centering, objective-estimator cutoff, penalty lower
bound/closure, and the paper-safe S-penalty product envelope/estimator. The
registry and equivalence audit will fail on an unclassified or omitted active
family.

## Expected source changes

- Add shared interval row and Gini geometry components under `include/` and
  `src/`.
- Extend `TailoredBCCplexApi` with a dedicated recursive global-tree solve path.
- Extend `CplexBaseline` with a one-root-model builder and verified solution
  reconstruction for the new mode.
- Add an explicit frontier execution option and serialization fields in
  `Instance`, `Result`, and `main`.
- Add deterministic C++ tests, a Round 19 runner/auditor, exactness/capability
  documentation, and the dedicated result package.

## Correctness and performance risks

- A missing or sibling-leaking interval row is a correctness failure.
- Child rows must use original column indices and all names must resolve before
  `CPXmipopt`; any mapping mismatch rejects the run.
- Branch callbacks occur only when CPLEX reaches a branch decision. Terminal
  intervals must hand control back to ordinary branching without pruning.
- Additional rows on every Gini child may be large; callback packing and model
  growth may dominate performance even when mathematically exact.
- Branching context can reduce presolve freedom automatically. Presolve-on
  correctness and throughput are therefore feasibility gates.
- Dynamic search may be API-compatible yet fail to expose the strict native
  best-bound processing semantics required by this experiment. Effective mode
  is fixed only after the mechanical comparison.
- Native time-limit finalization must return from `CPXmipopt` and expose
  `CPXgetbestobjval`; wrapper-only finalization blocks official evidence.
- An exact but slow result is not sufficient for promotion. The final report
  will separate mathematical exactness, API feasibility, stability, feature
  preservation, certificates, controls, and hard-case performance.
