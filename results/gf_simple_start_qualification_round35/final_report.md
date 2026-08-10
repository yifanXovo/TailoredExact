# Round 35 final report

## Outcome

Classification: `incumbent_decomposition_interaction_detected`.

Round 35 completed all 52 frozen new rows: 47 primary
qualification rows and 5 predeclared repeats. The primary
matrix contains 19 strict certificates and
28 valid time-limited rows, with
0 failed rows and 0
emergency watchdog timeouts.

## Primary comparisons

| comparison | pairs | SIMPLE gap wins | comparator gap wins | ties | SIMPLE certs | comparator certs | SIMPLE AUC wins | comparator AUC wins |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HGA-FULL 1,800 s | 35 | 8 | 12 | 15 | 16 | 15 | 23 | 11 |
| P-GRB 1,800 s | 35 | 31 | 1 | 3 | 16 | 2 | 33 | 2 |
| HGA-FULL 3,600 s V50 | 12 | 1 | 8 | 3 | 3 | 3 | 6 | 6 |
| P-GRB 3,600 s V50 | 12 | 11 | 1 | 0 | 3 | 0 | 11 | 1 |

All gaps use the independently verified common UB of the paired rows. AUC uses
only the common observed time window, is left-continuous, and performs neither
interpolation nor post-last-event extension. Fixed-threshold timings follow the
same convention.

## Startup and exact phase

The startup comparison covers all 47 compatible HGA-FULL pairs.
SIMPLE startup is deterministic and independently verifies three candidates in
every new row. Pattern labels are diagnostic only and are not a dispatch rule.
Detailed startup time, UB degradation, exact-phase time, final gap, Work,
nodes, AUC, and V/M/scenario summaries are in the companion CSVs.

## Repeatability and mechanism observation

The five predeclared repeats passed the deterministic sequence gate:
True. Timing was not a determinism
condition. The interaction audit records range geometry, interval domains,
cutoff rows, LP bounds, scheduling, targets, requeues, lookahead, splitting,
terminal Work, closures, native incumbents, and proof trajectories. It reports
association only; Round 35 changed no exact mechanism.

## Correctness and lifecycle

- Exactness audit: True.
- Certificate audit: True; false certificates:
  0.
- Trace audit: True.
- Single-thread command audit: True.
- New/historical result separation: True.
- Pre-existing worktree preservation: True.
- Frozen C6 source/decision equivalence: True
  (10/10 entries identical).
- Clean build/test gate: True (14 C++ tests and
  20 Python test scripts).
- Compatible historical rows: 94; historical comparator reruns: 0.

## Decision

S0/F0-CPLEX remains the tailored CPLEX mainline. C6-HGA-FULL remains the
validated Gurobi mainline pending review. Round 35 does not automatically
promote C6-SIMPLE-START. The machine-readable decision gates are preserved in
`final_audit_summary.json`.

- Stronger HGA incumbents materially help the large-instance matrix under the
  predeclared decision rule: True.
- SIMPLE preserves the validated tailored-Gurobi advantage over P-GRB:
  True.
- A later incumbent-decomposition mechanism study is justified by mixed
  performance plus structural-sequence changes:
  True.


## Evidence package

The package contains 2040 files excluding its self-manifest and totals
470488166 bytes. 391 large raw artifacts were compressed
losslessly and restored to their original byte counts and SHA-256 values. The
largest retained artifact is `results/gf_simple_start_qualification_round35/runs/matrix1800__round32_multi_m_high_imbalance_V50_M4_seed163456187__c6_simple_start__1800s/external/models/L2.0.lp.gz`
(2498176 bytes). A package-wide sensitive-license-marker scan
found zero hits, and no artifact reaches 100 MiB. The package manifest and
compression restoration hashes supersede per-run pre-compression artifact
manifests for post-package integrity.
