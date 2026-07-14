# Round 18: Controlling-Leaf Scheduler

## Decision summary

Fresh official rows: **72/72**. Diagnostic checkpoint-ablation rows: **6/6**. Engineering-blocked official rows: **0**. Audit failures: **0**.

The controlling scheduler has a lower matched gap than legacy in **10** instance-budget cells, a higher gap in **8**, and ties in **6**. A lower gap is better.

Hard-case matched cells where controlling Tailored beats plain CPLEX: **9** (moderate_seed3301@300s, moderate_seed3302@300s, high_imbalance_seed3201@300s, moderate_seed3301@900s, moderate_seed3302@900s, high_imbalance_seed3201@900s, moderate_seed3301@1800s, moderate_seed3302@1800s, high_imbalance_seed3201@1800s).

The official Tailored arms remained static and callback-free. Consequently, accepted checkpoint bounds in official rows were **0**; the checkpoint ablation tests persistence/merge plumbing but cannot attribute an official static-arm improvement to checkpoints when no checkpoint exists.

Original-problem certificates: **19/72**. Controlling lost a legacy certificate in **6** matched cells (V12_M2@300s, tight_T_seed3101@300s, tight_T_seed3101@900s, high_imbalance_seed3202@900s, tight_T_seed3101@1800s, high_imbalance_seed3202@1800s); all resulting bounds remain valid, but these are material control regressions.

## 1. Local/GitHub source-state verification

The task began at local `e4c8c8755f87e2e4416c2a0050d6f02de0274ac0`; GitHub `main` was `fcfc91188a8b4086059c10e0710fb4ccdfcc882f`. The commits differed but their tracked trees were identical. A single targeted fetch was used only after that mismatch, and no clone, pull, rebase, reset, clean, or force operation was used. See `local_github_source_sync_audit.csv`.

## 2. Local worktree and executable preservation

The pre-existing executables and unrelated modified result files were preserved. Round 18 was built only in `build_round18/`; the preservation evidence is in `local_worktree_preservation_manifest.csv`.

## 3. Mathematical correctness

The controller changes only exact-solve order and time allocation. Leaf bounds merge by maximum, the full-frontier bound is the minimum over relevant final leaves, timeout alone never closes a leaf, and atomic parent replacement requires exact child coverage. Formal arguments are in `docs/controlling_leaf_scheduler_exactness.md`.

## 4. Implementation correctness

The same binary exposes explicit `legacy` and `controlling-leaf` modes. The requested/parsed/effective/serialized total-budget policy is audited, tied controlling leaves use deterministic round-robin water filling, and requested quanta are `30*2^k` seconds with no fixed cap.

## 5. Source/build/executable identity

All official arms use the isolated release executable recorded in `build_source_identity.csv`; same-binary and fixed-interval fingerprint audits prevent cross-arm model substitution.

## 6. Engineering stability

Rows beyond the wall tolerance or with missing/nonzero finalization remain visible and non-comparable. Observed blockers: **0**.

## 7. Scheduler behavior

Decision traces record each recomputed controlling set and selected leaf. Fairness, trace-integrity, deadline, native-time-limit, leaf-monotonicity, global-monotonicity, and coverage audits determine whether the early-leaf starvation mechanism was removed; no instance name or benchmark value is used. At 1800 seconds it devoted 1720.7s, 1720.3s, and 1644.9s to the controlling sets in the three named transfer cases.

## 8. Full-frontier lower-bound improvement

Across fresh matched cells, controlling beats legacy in 10, loses in 8, and ties in 6. At 1800 seconds it improves `moderate_seed3301` (2.4445% to 1.7467%), `moderate_seed3302` (84.3750% to 35.1868%), and `high_imbalance_seed3201` (5.7308% to 5.3207%), but regresses on `tight_T_seed3102` (11.5442% to 25.0000%). Detailed LB/UB/gap, timing, controlling service, unresolved leaves, and trajectory metrics are in `matched_plain_legacy_new_comparison.csv`.

## 9. Plain CPLEX comparison

The controlling arm beats plain CPLEX on 9 valid hard-case matched cells. Plain rows remain benchmark-only and never enter the Tailored certificate ledger.

## 10. Remaining fixed-interval weakness and causal answers

1. Initial source synchronization was a commit-SHA mismatch with identical trees; this is recorded, not disguised.
2. Clone/pull/rebase/reset/clean were avoided; one permitted targeted fetch followed the mismatch.
3. Pre-existing binaries and unrelated worktree files were preserved.
4. The Round 17 budget-policy recording mismatch was repaired and round-trip audited.
5. Leaf and global bounds are accepted only under monotonic runtime/audit checks.
6. Water filling prevents a second tied quantum before every open tied controller is served.
7. The three named 1800-second transfer cases receive 1720.7s, 1720.3s, and 1644.9s of controlling-set service, so the old early-leaf starvation mechanism is removed without name-based policy.
8. Yes. `moderate_seed3301` improves beyond merely reaching the leaf: LB rises from 0.047951 to 0.048294, and gap falls from 2.4445% to 1.7467%.
9. Yes, modestly. `high_imbalance_seed3201` LB rises from 2.30338 to 2.3134; gap falls from 5.7308% to 5.3207%.
10. No. `tight_T_seed3102` controlling regresses from the legacy gap 11.5442% to 25.0000% despite substantial controlling service; the isolated advantage does not transfer.
11. Yes. `moderate_seed3302` improves strongly over legacy, but its controlling gap remains 35.1868% with four unresolved leaves, the weakest named controlling result.
12. Scheduling helps but does not remove that weakness. Together with the Round 17 isolated-leaf plain bound advantage, the evidence supports fixed-interval root/search strength and branch-and-bound throughput as the residual mechanism; it does not isolate root cuts, model size, or restart cost individually.
13. Static official rows have no callback checkpoints, so observed official deltas are scheduling, not checkpoint preservation; see the six ablations.
14. All controls remain mathematically valid and audits pass, but they are not regression-free: 6 legacy certificates are lost. These are incomplete valid controlling runs, not invalid certificates, and they block promotion.
15. Controlling beats legacy in 10 matched cells.
16. It beats plain CPLEX on 9 valid hard-case matched cells.
17. No further promotion is recommended this round: audits pass, but eight gap regressions and six lost legacy certificates are not sufficiently consistent. The preset remains unchanged.
18. Route-cutset callbacks remain experimental and disabled in official arms.
19. The controlling scheduler remains an explicit experimental mode, not the recommended paper configuration.
20. The single next optimization target is restart-amortized/persistent fixed-interval solving so quanta retain branch-and-bound progress and recover legacy certificate closures without instance-specific tuning.

## Audit status

Audit rows: 25; failures: 0. A nonzero failure count means the package is not fully passing.
