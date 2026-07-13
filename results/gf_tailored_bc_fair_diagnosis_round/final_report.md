# Fair Full-Frontier Diagnosis v2

## Status

Fresh package-local full rows: **144**; completed nominal budgets: **300, 900, 1800 s**.
Fresh isolated/engineering diagnostic rows: **38**. The full matrix contains 8 instances x 6 variants x 3 budgets; isolated rows are never certificate evidence.

The diagnosis status is **frontier scheduling is the first optimization target, with a separate moderate_seed3302 leaf-bound weakness**. Route-cutset callback is not promoted.

## Hard-Case Snapshot

| Instance | Comparable budget | Selected Tailored variant | Tailored gap | Plain gap | Worst leaf | G interval | 900 s isolated bounds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| moderate_seed3301 | 300 | tailored_static_no_callback | 0.75 | 0.442849635501 | 8 | [0.0122881381662, 0.0153601727077] | plain 0.0491525526647; Tailored 0.0491525526647 |
| moderate_seed3302 | 300 | tailored_full_static_baseline | 0.875 | 0.463439315391 | 6 | [0.0244545258186, 0.0366817887279] | plain 0.14117883864; Tailored 0.14052838974 |
| high_imbalance_seed3201 | 1800 | tailored_static_no_callback | 0.287015734552 | 0.157449413757 | 15 | [0.48984375, 0.5046875] | plain 2.1975143526; Tailored 2.38861621775 |
| tight_T_seed3102 | 900 | tailored_full_static_baseline | 0.474370843117 | 0.213178413509 | 14 | [0.140790102348, 0.14548310576] | plain 0.38558986743; Tailored 0.600704436685 |

## Required Answers

1. **Fresh/package-local:** Yes. Every selected row points to this package; the cross-round audit is authoritative.
2. **Hardware/solver fairness:** Yes. All controlled rows ran on WIN-3NO58RVQ4VC (Intel i7-12700KF, 34.16 GB RAM) with CPLEX 22.1.1.0, one CPLEX thread, one common build, and matched nominal budgets.
3. **Concurrent CPLEX jobs:** No. The runner launched one fresh solver job at a time; no official row overlaps another.
4. **UB provenance:** All accepted paper-row events are same-run and verifier-gated.
5. **Engineering/native exit reproduced:** Yes, but on the first pre-matrix V12 M2 cheap-profile row: Windows access violation 0xC0000005. The tight_T_seed3102 300/900 s post-fix checks did not reproduce a native exit.
6. **Engineering disposition:** Fixed. Debug symbols localized a stale adaptive-frontier parent reference invalidated by child-vector insertion; the code now copies the parent lower-bound source first. The identical V12 M2 row then certified, and all post-fix engineering checks finalized normally.
7. **Best Tailored variant by hard case:** At the highest comparable nonblocked budget, moderate_seed3301=`tailored_static_no_callback`, moderate_seed3302=`tailored_full_static_baseline`, high_imbalance_seed3201=`tailored_static_no_callback`, and tight_T_seed3102=`tailored_full_static_baseline`. These are ranking selections among gap ties, not evidence that one profile dominates.
8. **Route-cutset callback:** It did not improve any selected hard-case full-row gap over static/cheap. Across every matched cell it beat plain in 9 and lost in 10, but the hard-case causal comparisons show added callbacks/cuts without a parent-gap gain.
9. **Static/no-callback/cheap versus route:** None systematically outperforms the route profile on the four full rows; they mostly tie. The important result is that route cuts add work without transferring isolated-leaf gains to the full frontier, so route callback remains experimental.
10. **moderate_seed3301 bottleneck:** Fresh leaf `8` over G=[0.0122881381662, 0.0153601727077].
11. **Why moderate_seed3301 fails:** The 300 s full frontier leaves the controlling low-Gini leaf open with gap 0.75, while both plain and Tailored isolated 900 s runs close that leaf at the cutoff. Four 1800 s paper rows also hit wrapper/resource finalization. The demonstrated primary cause is leaf allocation/finalization, with low-Gini root weakness secondary.
12. **Why moderate_seed3302 regresses:** All Tailored profiles tie at gap 0.875 at 300 s versus plain 0.463439. On the isolated 900 s leaf, plain bound 0.14117883864 exceeds the best Tailored bound 0.14052838974; cheap and route are weaker still. This is a real fixed-leaf root/search deficit, not just callback overhead, and no cheap/full policy is justified.
13. **Why high_imbalance_seed3201 loses to plain:** At 1800 s plain gap 0.157449 beats Tailored 0.287016, but the isolated leaf reverses the bound ordering (Tailored route 2.388616 versus plain 2.197514). The frontier scheduler is spending insufficient time on a leaf where Tailored is stronger.
14. **Why tight_T_seed3102 fails:** The post-fix native-exit check is clean. At 900 s the full Tailored gap is 0.474371 versus plain 0.213178, yet isolated Tailored closes the controlling leaf at 0.600704 while plain remains at 0.385590. The full loss is scheduler/finalization behavior; 1800 s blocked cells are inconclusive.
15. **Isolated-leaf causality:** moderate_seed3301, high_imbalance_seed3201, and tight_T_seed3102 implicate the full-frontier scheduler/finalizer because Tailored closes or materially outbounds plain in isolation. moderate_seed3302 instead implicates the leaf formulation/root search because plain remains stronger in isolation.
16. **Generic policy candidate:** None implemented. No generic early metric wins or ties across controls and all hard cases, and instance-specific activation is prohibited.
17. **Hard-case certificates:** none under the fresh paper-valid full rows.
18. **Easy-control regressions:** none. V12 M1, V12 M2, tight_T_seed3101, and high_imbalance_seed3202 retain Tailored certificates; runtime inflation on some larger-budget rows is reported but is not a correctness regression.
19. **Plain CPLEX strength:** Plain has the better full-row gap in the highest valid comparable cell for all four hard cases. This does not imply universal subproblem dominance: Tailored wins the isolated high-imbalance and tight-T leaves, ties closure on moderate3301, and loses only the isolated moderate3302 leaf.
20. **Paper contamination:** None detected. Telemetry, isolated leaves, wrapper checkpoints, and plain CPLEX remain diagnostic/benchmark-only and are excluded from Tailored certificate ledgers.
21. **Exact next target:** Replace the current frontier time allocation with a generic controlling-leaf scheduler that prioritizes valid leaf gap contribution and preserves per-leaf checkpoints. Re-test the isolated advantages end to end; only then target moderate_seed3302 with stronger root-bound formulation work.

## Interpretation

The paper-facing method remains the Gini-frontier Tailored-BC framework. Strong relaxation closure is valid and desirable; Tailored fixed-interval evidence matters where the frontier leaves work unresolved. This round validates the fixed-interval subsolver on selected leaves but shows that its advantage is not propagated reliably by the current full-frontier scheduler.

## Audit Snapshot

- Frontier ledger checks: 120; failures: 0.
- Leaf source checks: 776; failures: 0.
- UB source checks: 144; failures: 0.
- The complete command-level audit result is in `audit_summary.csv`; every required audit must pass before publication or commit.
