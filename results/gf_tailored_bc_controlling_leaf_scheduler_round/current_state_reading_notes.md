# Round 18 Current-State Reading Notes

## Source state at the start of Round 18

- Local project: `E:/codes/ExactEBRP`.
- Initial local HEAD: `e4c8c8755f87e2e4416c2a0050d6f02de0274ac0`.
- Initial branch: `codex/longrun-round17-local-results`, upstream `origin/codex/longrun-round17-local-results`.
- GitHub default branch: `main`.
- GitHub `main` SHA at task start: `fcfc91188a8b4086059c10e0710fb4ccdfcc882f`.
- Initial tracked source states synchronized: **no**. The local Round 17 tip was one tree-identical PR merge commit behind GitHub `main`.
- The GitHub SHA was initially absent from the local object database. After preserving the dirty worktree, one targeted `git fetch origin main` established that `e4c8c87` is an ancestor of `fcfc911` and that their trees have no differences.
- No clone, pull, rebase, reset, clean, force checkout, or overwrite was used. The dedicated branch `codex/round18-controlling-leaf-scheduler` was created directly at verified GitHub `main`.
- Post-verification Round 18 base HEAD equals GitHub `main`: `fcfc91188a8b4086059c10e0710fb4ccdfcc882f`.
- Round 17 reference `e4c8c8755f87e2e4416c2a0050d6f02de0274ac0`: present in local history.
- Previously observed merged-main reference `fcfc91188a8b4086059c10e0710fb4ccdfcc882f`: present after the permitted targeted fetch and is the Round 18 base.
- The two pre-existing tracked result modifications, all pre-existing untracked files, five ignored `ExactEBRP*.exe` binaries, and relevant ignored build/log directories are recorded in `local_worktree_preservation_manifest.csv` and must remain untouched.

The machine-readable source-state record is `local_github_source_sync_audit.csv`.

## Current paper-facing algorithm

The implementation exposed by `--method gcap-frontier --algorithm-preset paper-gf-tailored-bc` is a Gini-frontier exact framework:

1. Generate a same-run HGA-TGBC incumbent and accept it only after independent route/load/inventory/Gini/penalty/objective verification.
2. Cover every potentially improving Gini value by a frontier of intervals.
3. Give every interval the valid base bound `max(0, gamma_L)`, apply movement/penalty/projection prepasses, and run the valid inventory-route-Gini relaxation.
4. Apply the existing adaptive split mechanism with exact child coverage, maximum depth 8 under the paper preset unless explicitly overridden, the configured minimum width, and the configured split factor.
5. Run the existing focused relaxation and BPC retry/final-closure phases on minimum-bound unresolved intervals.
6. Serialize a final-leaf frontier ledger. Replaced parents do not contribute; every non-replaced relevant interval contributes its valid lower bound even when it was never processed.
7. Optionally invoke the automatic fixed-interval compact-MIP oracle after the frontier function returns, merge only valid original-fixed-interval bounds by maximum, and take the minimum over relevant final leaves as the global lower bound.
8. Certify only when the verifier, full Gini coverage, interval accounting, bound source, pricing requirements, and sealed-run evidence checks all pass.

Plain CPLEX solves the current compact MILP directly and is benchmark-only. BPC, focus-only runs, route-mask enumeration, imported/archive/external incumbents, historical bounds, and diagnostic rows are excluded from the Tailored certificate ledger.

## Exact Round 17 static/no-callback leaf formulation

The Round 17 `tailored_static_no_callback` command used `paper-gf-tailored-bc`, but then explicitly selected:

- `--tailored-bc-enabled true`;
- `--tailored-bc-mode static`;
- `--tailored-bc-callback-cut-profile off`;
- `--compact-bc-root-cut-rounds 0`;
- `--compact-bc-dynamic-cut-families none`;
- every tailored callback/branch/vector/S-bucket mechanism off.

The fixed-interval compact model retained the original objective and interval/cutoff semantics plus the Round 17 common static profile:

- balanced compact cut profile;
- safe low-Gini strengthening;
- tight denominator bounds;
- adaptive objective estimator mode;
- iterative domain propagation with two rounds;
- variable-S centering;
- paper-safe `S*P` product estimator with tight bounds;
- preset-enabled direct Gini cap/floor, interval-tight McCormick, inventory conservation, movement-reachability, visit-inventory linking, objective-cutoff estimator, penalty lower-bound closure, Gini spread, required movement, global handling, support-duration, pairwise transfer compatibility, and the other already active static paper-safe families.

This is the formulation to freeze for both Round 18 Tailored arms. Route-cutset, user-cut, lazy, incumbent, branch, and telemetry callbacks are not part of the official static arms.

## Current frontier scheduling phases

The current source has several sequential allocation mechanisms rather than one authoritative controller:

1. Cheap movement/penalty/projection prepass over initial intervals.
2. Initial interval pass ordered by lower bound, then proximity to incumbent Gini, then interval index. The paper preset sets `frontier_split_before_tree=true`, so eligible intervals can defer BPC tree work.
3. Adaptive split pass on eligible minimum-bound leaves, with child relaxations while time remains.
4. Focused intensification: repeatedly choose the minimum valid lower-bound leaf, rerun a stronger relaxation, and invoke the existing split operation if no progress and the existing split conditions hold.
5. Focused BPC retry passes on minimum-bound unresolved leaves.
6. Optional BPC fallback/final-closure phases.
7. After the frontier function returns and writes its ledger, `runAutoIntervalOracleClosure` reads the CSV, builds a target list once, sorts it according to `auto_interval_oracle_order`, and calls the fixed-interval compact oracle sequentially. With Round 17 `order=all`, the order is interval ID rather than the currently controlling full-frontier lower bound.

The automatic oracle does not recompute its target priority after each accepted solver-final bound. It can therefore spend the full oracle budget on earlier noncontrolling leaves while a later controlling leaf remains unattempted.

## Current budget semantics

Round 17 did not enforce one process-level deadline inside the binary. The campaign runner split each nominal Tailored budget generically into approximately 68% frontier, 28% automatic-oracle, and 4% wrapper/model allowance, passed the frontier slice as `--time-limit`, and passed the oracle slice separately as `--auto-interval-oracle-total-budget`.

The runner requested `--auto-interval-oracle-leaf-budget-policy total`. However, `applyAlgorithmPreset()` runs after command-line parsing and unconditionally resets `paper-gf-tailored-bc` to `per-leaf`. The parsed option therefore became `per-leaf` even though the command requested `total`; raw JSON serialized `auto_interval_oracle_budget_policy=per-leaf` while retaining the requested total-budget scalar. The existing option audit does not include this option and incorrectly permits `option_audit_consistent=true`.

The legacy automatic oracle computes a fixed requested leaf time and may truncate it only by its separate oracle timer when the effective policy is total. The outer campaign wrapper allowed substantial extra termination grace. This is not the Round 18 required single process-level budget.

## Current finalization and checkpoint semantics

- Static/no-callback leaves run through command-file CPLEX with a native `set timelimit` and merge a solver-final best bound parsed from the solution/log. They currently do not record the native parameter identifier or parameter-set return code.
- Callback-managed leaves use the dynamically loaded CPLEX C API, set `CPX_PARAM_TILIM` (id 1039), set the MIP gap, register callback contexts, and collect CPLEX-native best-bound information. A heartbeat thread writes progress CSV rows.
- Existing callback progress is not an authoritative atomic checkpoint protocol: heartbeat-only rows and native-bound rows share a CSV; there is no complete identity tuple containing run ID, sequence, instance hash, interval, cutoff, objective sense, formulation profile, and full model fingerprint; persistence is not an atomic temporary-file rename.
- Existing wrapper code may preserve a native-bound progress row as diagnostic-only JSON after terminating a worker. It intentionally sets `interval_oracle_can_merge_bound=false`, so Round 17 checkpoints do not enter the parent paper ledger.
- Solver-final and mergeable timeout bounds are valid only for the original fixed-interval model and are merged by maximum. A bound below the cutoff leaves the interval unresolved; infeasibility, optimal no-improver completion, or a valid bound reaching the cutoff can close it.
- The final frontier ledger takes the minimum lower bound over non-replaced relevant final leaves. Unprocessed leaves remain with their gamma-floor/inherited bound. A timeout alone does not close a leaf.
- The pre-auto-oracle parent JSON and final JSON record best-seen fields, but current finalization does not validate a persisted checkpoint against a complete model identity before a parent merge.

## Round 17 causal findings

Round 17 produced 144 fresh full rows (eight instances, six variants, three nominal budgets) and 38 fresh isolated/engineering diagnostics. Its audited conclusion was that frontier scheduling/finalization is the first optimization target, with a separate fixed-leaf weakness for `moderate_seed3302`.

- `moderate_seed3301`: the full static/no-callback 300-second row ended at LB 0.0122881381662, UB 0.0491525526647, gap 0.75. Controlling leaf 8, G=[0.0122881381662, 0.0153601727077], received zero fixed-interval solver time. In isolation the static Tailored leaf closed at the cutoff in about 2.95 seconds (plain also closed).
- `moderate_seed3302`: the full 300-second Tailored gap was 0.875 versus plain 0.463439. Controlling leaf 6, G=[0.0244545258186, 0.0366817887279], received zero fixed-interval solver time. In the isolated 900-second comparison, plain reached 0.14117883864 and static Tailored reached 0.14052838974, showing a genuine fixed-interval root/search deficit after scheduler effects are removed.
- `high_imbalance_seed3201`: at 1800 seconds, Tailored gap 0.287016 lost to plain 0.157449. Controlling leaf 15, G=[0.48984375, 0.5046875], received zero fixed-interval solver time, while the isolated static Tailored leaf reached 2.378754 and the route diagnostic reached 2.388616 versus plain 2.197514.
- `tight_T_seed3102`: at the valid 900-second comparison, Tailored gap 0.474371 lost to plain 0.213178. Controlling leaf 14, G=[0.140790102348, 0.14548310576], received zero fixed-interval solver time. The isolated static Tailored leaf closed at the cutoff 0.600704 while plain remained at 0.385590.
- The four controls retained correct Tailored certificates with no unexplained correctness regression.
- Route-cutset callbacks added work without improving the matched hard-case full-frontier gaps and remained experimental.
- Four 1800-second paper rows for several hard cases were wrapper/resource-finalization blocked and were reported as inconclusive.

The direct leaf-allocation evidence is stronger than the narrative alone: `leaf_time_allocation.csv` records each of the four named controlling leaves as `subsolver_variant=relaxation_only`, `leaf_selected_order=not_called`, `leaf_runtime=0`, with reason `tree_not_started_before_time_limit_or_reserve`.

## Documentation, command, JSON, and source discrepancies

1. Round 17 commands request total oracle policy, but preset application changes the effective and serialized value to per-leaf.
2. The existing option-consistency snapshot omits the requested/parsed/effective/serialized budget-policy chain, so it does not detect that mismatch.
3. `Manuscript/sections/branch_and_cut_implementation.tex` and parts of `algorithm_framework.tex` describe the stable paper leaf as callback-enabled with a selected route-cutset separator. Round 17's audited paper-safe control and the required Round 18 formulation are instead static and callback-off; route-cutset remains experimental.
4. `Manuscript/sections/computational_protocol.tex` documents a 68/28/4 split. It does not describe one process deadline with an in-budget finalization reserve.
5. The static command-file CPLEX path applies a native time limit but does not serialize the parameter id/set return code required for a fully audited bounded attempt.
6. Existing heartbeat/checkpoint CSV persistence lacks atomicity and complete model identity and is therefore insufficient for an official parent-ledger checkpoint merge.
7. The frontier interval CSV omits canonical parent/depth/child coverage and per-attempt allocation fields even though some metadata exists in memory.
8. The automatic oracle target list is sorted once; it is not an authoritative dynamic controlling-set ledger and does not provide tied-leaf water filling or uncapped geometric quanta.
9. `README.md` contains historical instance/size-oriented scheduler modes. They are pre-existing diagnostic paths; the Round 18 scheduler must not use them or add any instance, path, seed, V/M, class, or known-objective branch.

## Source expected to change in Round 18

Expected implementation changes are deliberately scheduler/finalization-only:

- `include/Instance.hpp`: explicit scheduler/deadline/checkpoint options and requested/parsed/effective budget-policy provenance.
- `include/Result.hpp` and `src/Result.cpp`: scheduler, ledger, checkpoint, deadline, native-limit, and option-round-trip result fields.
- a small new controller module under `include/` and `src/` for deterministic controlling-set selection, round-robin tie service, geometric quanta, monotone bound merges, exact child insertion, deadline/reserve checks, and checkpoint identity validation.
- `src/main.cpp`: option parsing/normalization, deterministic test entry points, authoritative final-leaf integration, one parent deadline, controlling-leaf dispatch, trace emission, and honest legacy mode.
- `include/TailoredBCCplexApi.hpp`, `src/TailoredBCCplexApi.cpp`, and `src/CplexBaseline.cpp`: auditable static no-callback in-process solver-final path where practical, native time-limit provenance, and atomic identity-bearing checkpoint engineering for callback/abnormal diagnostics.
- `CMakeLists.txt`: compile the controller module.
- a new Round 18 campaign runner and audits under `scripts/`, leaving historical runners and result packages unchanged.
- `docs/controlling_leaf_scheduler_exactness.md`, manuscript corrections, and the dedicated Round 18 result package.

The mathematical objective, compact formulation, static row families and parameters, verifier rules, incumbent policy, adaptive split eligibility/depth/width/factor, plain CPLEX benchmark formulation, and all CPLEX parameters other than one-thread and native per-attempt time limit remain frozen.
