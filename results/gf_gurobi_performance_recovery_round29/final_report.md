# Round 29 final report

## Outcome

Round 29 classifies C4 as
`exact_but_mixed`.  C4 passed
17/
17 official correctness audits.
The corrected CPLEX S0/F0 remains the stable accepted paper mainline; C4 is a
distinct exact candidate and is not promoted automatically.

## Root cause and deadline repair

Moderate6301 was a pre-exact transition/finalization failure, not evidence of
a C3 external-tree failure.  The optional local re-decode repair launched a
second generation-stagnation HGA whose local seconds cap was ineffective in
that stopping mode.  It could consume the remaining window, and Round 28's
external watchdog then prevented result serialization.

Round 29 uses one monotonic deadline from process entry.  Mathematical work
ends five seconds before the nominal 300-second cap; the fixed margin is only
for interruption, resource release, ledger flush, serialization, and exit.
It never enters a split predicate.  A pre-exact expiry emits a verified UB
when available, explicit `exact_phase_started=false`, conservative LB=0 from
nonnegative `G + lambda P`, and a rejected strict certificate.

## Round 28 diagnosis

The 30 completed C3 rows performed 5,764 optimizations: 4,107 LPs and 1,657
terminal MIPs.  Terminal MIPs consumed 80.4% of recorded LP-plus-MIP Work.
C3 made 2,366 unconditional splits and zero LP-bound prunes.  Among 2,027
splits with both immediate child LPs observed, 723 (35.7%) produced no strict
one-level controlling-bound gain.  Repeated model reads, presolve/root work,
lost state, leaf multiplication, and terminal-MIP startup are separate costs;
the earlier 7.1% median file/read share was not the total restart penalty.

## C4 definition

C4 is a combined, algorithmically distinct exact strategy.  For an eligible
parent with a complete LP bound, it solves both complete child LPs and splits
iff a child LP is infeasible or the minimum feasible child bound exceeds the
parent bound by more than `1e-7`.  Otherwise it discards the speculative
children and solves the complete unsplit parent MIP.  A complete LP may also
be cutoff-fathomed against the independently verified incumbent.

Execution retains the same leaf's Gurobi model object from LP to terminal MIP,
restores every original variable type, and then optimizes the exact MIP.
Split, empty, fathomed, and rejected speculative models are explicitly freed.
No LP basis is submitted, no native search tree is claimed, and no MIP start
is used.  This is model-object reuse only.

## Official matrix

The materialized Stage 2 matrix contains
51 rows.  Completed/failed/emergency-watchdog
counts are 51/0/
0; time-limited results number
48.  P-GRB versus C4 final-LB outcomes are
C4 10 wins, P-GRB 6 wins, and
1 ties.  C3 versus C4 outcomes are C4
13 wins, C3 4 wins, and
0 ties.

### V12

- V12_M1: P-GRB LB 0.357200583, C4 LB 0.357200583, winner tie.
- V12_M2: P-GRB LB 0.718504071, C4 LB 0.655760184, winner P-GRB.

Across V20, C4 records
8 wins and
4 losses against
P-GRB.  Across V50 it records
2 wins and
1 losses.

## Paper-mainline anchors

- V12_M1: S0-CPLEX LB=0.35645046 gap=0.2100%, C2-PAPER LB=0.357200583 gap=0.0000%, C3-REPLICA LB=0.316632361 gap=11.3573%, C4-CANDIDATE LB=0.357200583 gap=0.0000%.
- V12_M2: S0-CPLEX LB=0.707138632 gap=1.5818%, C2-PAPER LB=0.65524969 gap=8.8036%, C3-REPLICA LB=0.65524969 gap=8.8036%, C4-CANDIDATE LB=0.655760184 gap=8.7326%.
- high_imbalance_seed3202: S0-CPLEX LB=1.68058796 gap=3.9287%, C2-PAPER LB=1.61009197 gap=7.9586%, C3-REPLICA LB=1.60996745 gap=7.9658%, C4-CANDIDATE LB=1.6108436 gap=7.9157%.
- moderate_seed3302: S0-CPLEX LB=0.141406467 gap=27.7197%, C2-PAPER LB=0.139515739 gap=28.6861%, C3-REPLICA LB=0.139416918 gap=28.7366%, C4-CANDIDATE LB=0.139532818 gap=28.6774%.
- tight_T_seed3101: S0-CPLEX LB=0.0395481464 gap=63.1262%, C2-PAPER LB=0.0536263671 gap=50.0000%, C3-REPLICA LB=0.0237456114 gap=77.8601%, C4-CANDIDATE LB=0.0536263671 gap=50.0000%.

## Mechanisms and resources

Across the unique official C4 primary rows: optimize/presolve/root counts are
1459/
1459/
355; LP/MIP counts are
1104/
355; splits/declined splits
are 510/
15; final/open leaves are
578/
191.  Total Work is
8924.6 (LP
1429.54, terminal MIP
7495.06); summed per-run peak memory is
4.33426 GB.  LP cutoff prunes number
0.

C4 retained 355 same-leaf
models and restored 1104 LP
domains.  Basis submitted/accepted/rejected counts are
0/
0/
0; MIP-start
submitted/accepted/rejected counts are
0/
0/
0.

Of 1425 terminal-MIP events in the retained primary evidence,
702 immediately raised the global LB and 0
improved the independently verified incumbent.

## Repeatability and interpretation

Stage 4 produced 5 two-run comparisons;
4 have scalar identity
and 5 have full
semantic sequence identity.  Timing-limited prefix divergence is reported,
never replaced by a best repeat.

The unresolved mechanism is reported from the actual C4 evidence: where C4
does not dominate, complete child lookahead and exact terminal parent MIPs
remain costly even after disk rereads are removed.  Because C4 is
exact_but_mixed, a full long-run validation is
not yet; resolve mixed short-run mechanisms first.  S0/F0 remains the stable
mainline in either case.

## Evidence package

The package contains 14911 files totaling
1691235630 bytes.  Its largest retained artifact is
`results/gf_gurobi_performance_recovery_round29/compression_manifest.csv` at 2969941
bytes.  Large raw artifacts are gzip-compressed only after restoration hashes
match their originals.
