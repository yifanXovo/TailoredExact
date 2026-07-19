# Round 23 final report

## Outcome

The moderate_seed4301 contradiction is fully explained and resolved by a
general fail-closed correction. All 18 official Stage 1/2 rows pass exactness
and structural audits. The single selected mechanism, P2, is mathematically
valid and preserves strict-certificate coverage, but the six 900-second pairs
classify as 2 improvements and 4 regressions. Corrected S0/F0 therefore remains
the stable paper mainline and P2 remains research-only.

## Required questions

1. **Local base.** Branch
   `codex/round23-moderate4301-correctness-unified-convergence` was created from
   local HEAD `3c69cb2c04889db5ceb40e313a710d600089879d`.

2. **Observed remote main.** The one inspection fetch observed
   `91ed0e314caae51ddbd8375d88cd65a5352c917f`.

3. **Relationship.** The merge base is the local base. Remote main has one
   history-only merge commit; both commits have tree
   `1b6e852b48dad4f5697909642e10acfb0b6fa81e`: different commit history,
   identical source tree.

4. **Forbidden repository operations.** No pull, merge, rebase, reset,
   restore, checkout-path, stash, clean, force push, reclone, or remote-file
   replacement was performed.

5. **Frozen Round 22 executable.** It was available and independently hashed
   as `b3fecef84dce8d6a2323d25a7877d5f16d14aa5f1fb644ae642bf636a229ee62`.
   No current rebuild is labeled as that binary.

6. **Moderate4301 binding.** Plain, S0, and S1 used the same file bytes
   (SHA-256 `8841820f8028da45d98c7d4ebebdb182df03f4a3909b877e4d3ce2bcd131daf6`),
   internal instance hash `67459d3ab38ff69f`, lambda, T, capacities,
   inventories, weights, distance semantics, and core objective. Differences
   are expected model/flow/callback settings recorded in the command audit.

7. **HGA witness.** Independently feasible. Recomputed
   `G=0.015302186003961113`, `P=0.0265057675953079`, and objective
   `0.0192780511432573`; all original route, load, capacity, inventory,
   duration, and objective checks pass.

8. **Plain witness.** Independently feasible, with recomputed objective
   approximately `0.04865896849455245` and all original constraints satisfied.

9. **Partial root fixation.** The HGA semantic fixation is feasible/optimal in
   the actual exported root model at objective `0.0192780511432573`, with
   auxiliary columns free.

10. **Complete extension.** A canonical complete auxiliary extension exists:
    zero unsupported columns, zero bound/integrality failures, zero row
    violations at `1e-9`, and maximum scaled residual `4.221e-17`.

11. **First failing invariant.** A successfully created custom child whose
    closed interval contains a feasible root witness must remain represented
    until processed or validly fathomed. No mathematical root row or bound is
    the first failure.

12. **Loss event.** The HGA Gini value lies in root upper child UID 2. Both
    branch creations returned success; only lower UID 1 was first-touched, and
    UID 2 disappeared before its first relaxation under presolve-on execution.

13. **Primary root cause.** CPLEX presolve is incompatible with the continuous
    generic-callback child lifecycle in this architecture. The causal ablation
    is presolve on -> status 103 after five nodes versus presolve off -> status
    108 through the deadline with many processed children. Overbroad native
    infeasibility scope was the secondary semantic defect.

14. **Generality.** The correction is uniform: every global-Gini continuous
    callback solve requires presolve/Reduce/Linear off with set/get readbacks;
    native local intervals may contract but never expand; status scopes and
    witness consistency fail closed. No benchmark token or dispatcher appears
    in production logic.

15. **Historical blast radius.** Presolve-on Tailored strict/infeasible rows
    are historical evidence, not corrected-S0 certificates. In particular the
    Round 22 moderate4301 status-103 S0/S1 rows are excluded. No immutable row
    is rewritten. Retained non-anomalous comparisons remain descriptive, while
    the fixed subset is revalidated with the safe executable.

16. **Targeted revalidation.** Corrected moderate4301 S0/S1 120-second gates
    reached status 108 with LBs `0.005286223700350229` and
    `0.004205687964173438`, respectively, and zero callback failures. A clean
    Stage 0 build/test/dispatch/API gate passed, followed by 6 Stage 1 and 12
    Stage 2 official rows, all structurally valid.

17. **Feasibility-consistency gate.** Permanent and fail-closed. A verified
    feasible witness contradicting native infeasibility yields
    `certificate_rejected` with reason
    `verified_feasible_witness_contradicts_native_infeasibility`; it does not
    alter the native status or invent a bound.

18. **Retained S0/plain counterexample.** None under the fixed hierarchy after
    excluding the anomalous moderate4301 row: S0 wins all 23 eligible
    repeated-horizon pairs; plain wins 0.

19. **Retained common-UB results.** Across those 23 eligible retained pairs,
    mean S0 common-UB gap is `0.148630` versus plain `0.349089`; mean normalized
    AUC is `0.832663` versus `0.631595`; S0 records 68 threshold crossings
    versus plain 20. Per-pair final LB/gap/AUC and exact crossing times are in
    the five `stable_s0_vs_plain_*` tables; horizons are repeated measurements,
    not independent instances.

20. **Remaining bottlenecks.** Of 46 non-anomalous Tailored retained rows, 40
    classify as sibling starvation and 6 as equal child estimates. Ordinary
    tree growth, simplex work, and late stagnation remain secondary/mixed.

21. **Starvation in node count.** Yes. The retained maximum is 2,940.09 seconds
    and 45,220 processed nodes, so it is not merely wall-clock overhead.

22. **P1 API feasibility.** No within the current architecture. CPLEX 22.1.1
    generic callbacks provide high-level branch/prune operations but not
    supported open-node enumeration/next-node selection; the documented
    selector is in the legacy NodeCallback API. Partial migration or callback
    mixing was forbidden and unsafe.

23. **Selected mechanism.** P2, the uniform dispersion-coupled child
    lower-bound estimate, controlled by
    `--global-gini-tree-child-estimate dispersion-coupled`.

24. **Selection rule.** P1 failed its API-safety gate. P2 was selected before
    performance observation only after its proof, conservative implementation,
    invalid-input gates, hand cases, and exhaustive toy-optimum checks passed.

25. **Proof.** From `H <= (V-1) sum e_i`, `H=VSG`, `G>=L`, and `S>=S_lower`,
    every feasible child satisfies
    `sum e_i >= V L S_lower/(V-1)`. Minimizing weighted deviation over valid
    per-station deviation intervals is a continuous knapsack solved by
    increasing weight. Thus `L + lambda*phi` is a child objective LB; the max
    with the parent relaxation remains valid. Full edge/numerical proof:
    `dispersion_coupled_child_bound_proof.md`.

26. **What P2 changes.** Only the proved value passed as a child estimate and
    therefore potential node order. It changes no row, variable bound, split,
    objective, incumbent semantics, pruning rule, or feasible region.

27. **Certificate preservation.** Yes. Both arms strictly certified V12_M1
    and V12_M2; neither certified the other four. Gains 0, losses 0.

28. **900-second pair counts.** Improve 2, regress 4, tie 0, unavailable 0.
    There are zero preregistered material regressions, but decision D also
    requires more improvements than regressions and is not satisfied.

29. **Targeted performance.** P2 improved final LB/common gap on
    high_imbalance_seed4201 and tight_T_seed3101. It was 0.42% and 2.28% slower
    on the two shared strict certificates, slightly lowered high3202 LB, and
    worsened moderate4302 final gap (`0.912109 -> 0.921875`) and AUC
    (`0.0647884 -> 0.0501894`). Discriminated-pair counts were
    `0,1,0,0,7,68`; valid discrimination did not consistently improve search.

30. **Full-matrix eligibility.** No for P2 in its current form. It is
    research-only under decision C.

31. **Stable mainline.** Corrected S0/F0 remains the stable paper mainline.
    P2 is not a stable-mainline replacement.

32. **Artifact actions.** Removed 0 files. Deterministically compressed 58 new
    Round 23 streams; all original/stored hashes and paths are retained.

33. **Bytes saved.** `244,603,007` bytes (`337,785,627 -> 93,182,620`).

34. **Round 22 mutation.** None. Git diff under the immutable package is empty;
    the cleanup audit records zero affected files.

35. **Single next experiment.** Run a preregistered full-matrix corrected
    S0/F0 mechanism-off revalidation to replace potentially affected
    presolve-on historical certificates with safe current evidence. Do not
    promote P2 at full-matrix scale without a new ordering rationale.

## Official Stage 2 metrics

| Instance | S0-C status/LB | S0-M status/LB | C gap / M gap | C AUC / M AUC | Pair |
|---|---:|---:|---:|---:|---|
| V12_M1 | 101 / 0.3572005832 | 101 / 0.3572005832 | ~0 / ~0 | .973684 / .973745 | regress (strict time) |
| V12_M2 | 101 / 0.7185040708 | 101 / 0.7185040708 | 0 / 0 | .980096 / .980279 | regress (strict time) |
| high_imbalance_seed3202 | 108 / 1.6963486675 | 108 / 1.6963405848 | .0302775 / .0302821 | .961790 / .961806 | regress |
| high_imbalance_seed4201 | 108 / 2.7402724835 | 108 / 2.7404997089 | .0157448 / .0156631 | .981429 / .981451 | improve |
| tight_T_seed3101 | 108 / .0430599383 | 108 / .0439911366 | .598519 / .589837 | .371877 / .369139 | improve |
| moderate_seed4302 | 108 / .0042664622 | 108 / .0037924108 | .912109 / .921875 | .064788 / .050189 | regress |

## Validation and artifact audit

The clean official executable is
`880f9fb08dd178d0849447b76c8bfbafee2d5abe9402dcfbc594e558d630e3c4`,
built from preregistration commit
`427e15f4cb1a993093d3a355356e8a772a964cc3`. Eight C++ executables pass
111 groups/requirements. The Round 20, Round 22, moderate4301, runner, and
final-evidence Python suites pass; all 18 official rows have strictly
increasing raw timestamps, solver-final endpoint equality, zero exactness
failure counters, and matching environment/source/executable/instance/manifest
bindings.

Three pre-official candidate smoke attempts are retained as excluded failed
diagnostics: they exposed the existing equality-only metadata guard after
valid root-bound contraction. The nested-contraction fix was added, directly
tested, and the next smoke plus both Stage 0 arms passed. Official failed runs:
0; official interrupted runs: 0; excluded diagnostic directories: 16.

The audit individually hashes 20,808 tracked/immutable/current evidence files
and summarizes 284,964 large scratch/build files (71.23 GB) at directory level.
It removes nothing because no uncertain ownership/reference path is treated as
disposable. The largest new artifact is the 9,298,387-byte compressed tight-T
S0-M node trace. `evidence_package_manifest.csv` binds every committed Round 23
evidence file except its self-referential manifest row.

## Separate conclusions

- **Moderate4301 correctness:** fully resolved with causal controls and a
  general correction.
- **HGA/verifier reliability:** both retained witnesses are independently
  valid; invalid-candidate gates remain fail-closed.
- **Model/callback correctness:** complete root extension is valid; presolve
  caused lifecycle loss; corrected official rows pass all audits.
- **Existing S0/plain evidence:** no retained non-anomalous plain-over-S0
  counterexample, but historical presolve-on certificates are not silently
  relabeled as corrected evidence.
- **Remaining bottleneck:** sibling starvation dominates, with node-count and
  wall-time evidence.
- **Selected mechanism:** P2 is proved valid but has sparse/inconsistent search
  utility.
- **Targeted performance:** mixed, 2 improvements and 4 regressions.
- **Stable status:** corrected S0/F0 remains stable; P2 research-only.
- **Artifact hygiene:** 0 removals, 58 deterministic compressions, immutable
  Round 22 untouched.
- **Remaining risk:** the fixed subset is not a full safe-configuration
  revalidation matrix; historical presolve-on results require replacement.
