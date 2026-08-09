# Round 34 final report

## 1. Current C6 algorithm

The validated Gurobi mainline remains **C6-HGA-FULL**: a verified HGA-TGBC
upper bound followed by four strengthened Gini intervals, external best-bound
scheduling, complete parent LPs, launch-frozen next-strict-frontier native
targets, valid partial dual-bound harvesting and requeue, lazy child LP
lookahead, the current normalized child-disjunction gain test (`rho=0.01`),
adaptive midpoint splits (depth at most 8, width at least `1e-4`), atomic
coverage replacement, exact closure, and original-problem certification.
HGA is an upper-bound provider; exactness does not assume it finds an optimum.

The source-grounded algorithm, state machine, exactness proof, 15 active
strengthening families, HGA implementation, and source-to-paper mapping are in
the six first-class algorithm documents.  No C7 was created.  S0/F0-CPLEX is
unchanged and remains the accepted tailored CPLEX mainline.

Round 34 did touch the C++ exact driver file `PaperExternalGiniTree.cpp`, but
only its startup-contract gate and serialized startup label: it admits the two
predeclared exploratory verified-incumbent providers while retaining the
original HGA-FULL contract.  No model-row, scheduler, backend, target, split, or
closure decision was changed.  Frozen function/body checks cover the active
frontier, split, and terminal decisions (9/9 equivalent rows), and the clean
official executable is bound to solver-source commit `9fef376714dcc25205e677b82e2e473bc4f61398`.
The other C++ changes are observational HGA elapsed telemetry, CLI/result
plumbing, and serialization.  One engineering test was repaired to compare
deterministic generation/fitness/improvement columns separately from naturally
nondeterministic wall-clock telemetry; all 14 C++ tests and all 18 repository
Python scripts then passed.

## 2. Complete convergence evidence

| Instance | Arm | Strict | Certificate s | Objective | Proof-gap AUC |
|---|---|---|---|---|---|
| V12_M2 | C6-HGA-FULL | True | 122.994 | 0.719 | 0.086 |
| V12_M2 | P-GRB | True | 171.944 | 0.719 | 0.045 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | C6-HGA-FULL | True | 10.721 | 4.357 | 0.195 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | P-GRB | True | 325.920 | 4.357 | 0.090 |
| round33_v10_high_imbalance_M3_Q30_seed1765289896 | C6-HGA-FULL | True | 76.811 | 1.006 | 0.134 |
| round33_v10_high_imbalance_M3_Q30_seed1765289896 | P-GRB | True | 2529.931 | 1.006 | 0.092 |

All three predeclared pairs ran with 7,200-second safety caps.  Detailed
plot-ready trajectories, threshold times, phase timings, work/nodes, native
targets, child lookahead, splits, and terminal closures are provided in the
case-study tables and narrative.

## 3. HGA startup evidence

HGA-LIGHT is the same HGA with the uniformly frozen 1,000 no-improvement-
generation requirement.  SIMPLE-START is the existing deterministic verified
three-mode greedy constructor.  The identical C6 exact framework follows each
verified startup.  Across V10, LIGHT/FULL has geometric-mean end-to-end ratio
0.815 and wins 18/18;
SIMPLE/FULL has ratio 0.413 and wins
18/18.  Across the four V12/V20 transfer anchors the ratios
are 0.918 and
0.586, respectively.
FULL's median V10 startup is 2.310 s, LIGHT's is
1.368 s, and SIMPLE's is
0.003 s.  LIGHT preserves FULL's startup UB on all
22 official primary pairs.  SIMPLE has a weaker UB on
12/18 V10 and
3/4 transfer pairs, yet its downstream
exact-phase geometric-mean ratios are
0.954 and
0.821.

### V10 outcomes by M, Q, and scenario

| Grouping | Value | Candidate | N | Wins | Candidate/FULL geometric mean |
|---|---|---|---|---|---|
| M | 1 | C6-HGA-LIGHT | 6 | 6 | 0.674 |
| M | 2 | C6-HGA-LIGHT | 6 | 6 | 0.919 |
| M | 3 | C6-HGA-LIGHT | 6 | 6 | 0.873 |
| M | 1 | C6-SIMPLE-START | 6 | 6 | 0.299 |
| M | 2 | C6-SIMPLE-START | 6 | 6 | 0.627 |
| M | 3 | C6-SIMPLE-START | 6 | 6 | 0.376 |
| Q | 20 | C6-HGA-LIGHT | 9 | 9 | 0.797 |
| Q | 30 | C6-HGA-LIGHT | 9 | 9 | 0.832 |
| Q | 20 | C6-SIMPLE-START | 9 | 9 | 0.380 |
| Q | 30 | C6-SIMPLE-START | 9 | 9 | 0.449 |
| scenario | high_imbalance | C6-HGA-LIGHT | 6 | 6 | 0.843 |
| scenario | moderate | C6-HGA-LIGHT | 6 | 6 | 0.757 |
| scenario | tight_T | C6-HGA-LIGHT | 6 | 6 | 0.847 |
| scenario | high_imbalance | C6-SIMPLE-START | 6 | 6 | 0.445 |
| scenario | moderate | C6-SIMPLE-START | 6 | 6 | 0.304 |
| scenario | tight_T | C6-SIMPLE-START | 6 | 6 | 0.521 |

### V12/V20 transfer anchors

| Instance | V | Candidate | FULL s | Candidate s | Candidate/FULL |
|---|---|---|---|---|---|
| V12_M1 | 12 | C6-HGA-LIGHT | 29.649 | 27.113 | 0.914 |
| V12_M1 | 12 | C6-SIMPLE-START | 29.649 | 21.863 | 0.737 |
| V12_M2 | 12 | C6-HGA-LIGHT | 123.004 | 120.140 | 0.977 |
| V12_M2 | 12 | C6-SIMPLE-START | 123.004 | 82.523 | 0.671 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | 20 | C6-HGA-LIGHT | 10.715 | 8.593 | 0.802 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | 20 | C6-SIMPLE-START | 10.715 | 3.826 | 0.357 |
| tight_T_seed4101 | 20 | C6-HGA-LIGHT | 498.063 | 493.834 | 0.992 |
| tight_T_seed4101 | 20 | C6-SIMPLE-START | 498.063 | 332.668 | 0.668 |

### Repeatability

| Instance | Arm | Primary s | Repeat s | Repeat/primary | Same startup UB |
|---|---|---|---|---|---|
| V12_M2 | C6-HGA-FULL | 123.004 | 122.869 | 0.999 | True |
| V12_M2 | C6-HGA-LIGHT | 120.140 | 119.864 | 0.998 | True |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | C6-HGA-FULL | 10.715 | 10.841 | 1.012 | True |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | C6-HGA-LIGHT | 8.593 | 8.602 | 1.001 | True |
| round33_v10_high_imbalance_M1_Q20_seed2098545008 | C6-HGA-FULL | 4.773 | 4.738 | 0.993 | True |
| round33_v10_high_imbalance_M1_Q20_seed2098545008 | C6-HGA-LIGHT | 3.115 | 3.097 | 0.994 | True |
| round33_v10_high_imbalance_M3_Q30_seed1765289896 | C6-HGA-FULL | 76.994 | 76.901 | 0.999 | True |
| round33_v10_high_imbalance_M3_Q30_seed1765289896 | C6-HGA-LIGHT | 75.768 | 76.123 | 1.005 | True |
| round33_v10_moderate_M2_Q20_seed1118884127 | C6-HGA-FULL | 4.463 | 4.493 | 1.007 | True |
| round33_v10_moderate_M2_Q20_seed1118884127 | C6-HGA-LIGHT | 3.575 | 3.556 | 0.995 | True |

Final startup classification:
`simple_start_promising_for_future_validation`.

SIMPLE-START passes the material V10 and transfer gates and has a lower geometric-mean ratio than LIGHT on V10 without a worse transfer ratio.

This does not promote an exploratory arm.  Any startup modification requires a
later separately frozen qualification round.

## Correctness and audit

- Official rows: 82; strict certificates:
  82; false certificates:
  0.
- Exactness audit: True.
- Trace monotonicity/completeness audit: True.
- Single-thread command audit: True.
- Round/result separation audit: True.
- Pre-existing worktree preservation audit: True
  (577 recorded entries; status/existence/byte-count scope).
- The official source commit and executable SHA-256 are bound in every row and
  in `round34_frozen_manifest.json`.

Raw official evidence remains separated under `runs/`; historical results are
explicitly labeled and are not included in official Round 34 pairwise tables.


## Evidence package

The package contains 3939 files excluding its self-manifest and totals
168231205 bytes.  787 large raw artifacts were compressed
losslessly and independently restored to the original byte count and SHA-256.
The largest retained artifact is `results/gf_c6_documentation_hga_round34/case_bound_trajectories.csv`
(50796776 bytes).  A package-wide sensitive-license-marker scan
found zero hits.  After compression, the package manifest and restoration
hashes supersede per-run pre-compression artifact manifests for integrity.
