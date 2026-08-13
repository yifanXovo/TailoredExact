# Round 37 structural-geometry research protocol

## Fixed reference

The mainline reference is C6-HGA-FULL: verified HGA startup, K=4, rho=0.01,
single-threaded Gurobi seed 0, proof normalization, and the existing exact
coverage/lifecycle contract. No K/rho sweep, wider incumbent anchor, instance
label, hardware counter, elapsed-time branch, or instance-dependent dispatch is
permitted.

## Hypothesis G1 - pilot weakest-cell pre-refinement

The interval-local LP relaxation loses strength through finite-width Gini
domains (including G-bit McCormick envelopes and gamma-dependent domain rows).
After all four existing initial LPs complete, the open interval with the lowest
valid LP bound is the actual relaxation bottleneck. A single deterministic
midpoint refinement of that interval should tighten the controlling relaxation
before native-bound targeting, at the cost of two child LPs and one extra leaf.
Ties use lower bound, lower endpoint, upper endpoint, then leaf ID.

The rule is startup-scale independent after the proof range is frozen: it uses
only valid LP bounds and interval geometry. It must preserve exact coverage,
verified proof cutoffs, atomic parent replacement, open-leaf accounting, and
the original final verifier/certificate.

## Frozen development panel and stages

The 12-row panel in `frozen_development_panel.csv` was frozen before any G1
candidate result. It contains both V12 rows, all four V50 rows, and six V20 rows
spanning positive, hurt, tie, no-exposure, and split-stress evidence.

1. **Exploratory smoke:** paired reference/G1 runs at 120-180 seconds on six
   representative rows. Continue only with zero false certificates, complete
   coverage/lifecycle gates, and actual G1 exposure.
2. **Focused diagnostic:** paired 300-600 second runs on the frozen panel or a
   predeclared subset selected solely by smoke mechanism exposure and V/scenario
   coverage. No candidate rule changes after this point.
3. **Selected confirmation:** at most 900-1200 seconds on predeclared hard
   positive and regression witnesses if the diagnostic signal is coherent.
   No 3600-second run and no automatic broad validation.

Runs are serial, non-resumed, and isolated by run directory. Baseline and G1
use identical commands except the explicit geometry-policy option.

## Evidence and decision

Every run must retain the command, result, initial decomposition, LP, parent/
child, scheduler, target, split, optimize, closure, global-bound, and process-
phase records. Primary comparisons are strict-certificate state and final gap
to a paired common verified UB. Observed proof AUC is diagnostic on the common
event window only; wall time, Work, and nodes are descriptive. Sequence hashes
exclude clocks and solver-effort fields.

G1 is promising only if it has no certificate regression or false certificate,
improves the controlling LP mechanism on exposed cases, and does not concentrate
final-gap harm in a V/scenario class. The round may conclude that the mechanism
is real but the fixed one-cell policy is insufficient. No outcome automatically
promotes a candidate; C6-HGA-FULL remains mainline.
