# Representative trajectory analysis

## Scope

This note compares the two predeclared opposing witnesses using the final
Round 41 executable (`572834f01bf923ae0026300b4f6a5b88f9ca78db27cc0bb38b39938de836fcdd`).
Every C6-derived row used the same verified HGA-FULL start, one thread, Seed 0,
Gurobi Presolve Auto, and zero relative and absolute gaps. Times below are the
exact phase, including the small construction/finalization overhead recorded by
the common analyzer. Raw event sequences and hashes are in
`representative_trajectory_analysis.csv`.

## Fragmentation witness

Instance: `round39_small_medium_V12_M3_Q30_slot08_seed1343324363`.

| Arm | Strict certificate | Exact phase (s) | Work | Nodes | Independent integer jobs |
|---|---:|---:|---:|---:|---:|
| external K4 | yes | 1777.865 | 4014.177 | 31545 | 8 total integer jobs; 4 terminal MIPs |
| external K1 | yes | 1339.296 | 3052.420 | 37107 | 1 |
| P-GRB | yes | 945.554 | 1607.915 | 145209 | 1 |
| ST-K2-I | no (time limit) | 1777.852 | 3897.965 | 35091 | 1 |
| ST-K2-P-Core | yes | 760.801 | 1738.405 | 17047 | 1 |
| ST-K2-P-Extended | yes | 1584.966 | 3616.226 | 46443 | 1 |

The K1 root bound is `0.0209774956074392`; the direct left/right interval
bounds are `0.024872307366954508` and `0.03764950371085417`, so the external K2
disjunctive bound is `0.024872307366954508`. All three static formulations
match that disjunctive bound to numerical precision. Core therefore preserves
the useful K2 root strength while executing one native MIP job.

External K4 executed 22 native optimizes, including four partial and four
terminal MIP optimizes. Core certified the same objective
`0.045001550055628357` using 0.428 of K4 exact-phase time and 0.433 of K4 Work.
Both ratios are below the frozen 0.80 ceilings. ST-K2-I reached the cap with
objective `0.045054161580534623`, bound `0.043589007168930924`, and no
certificate. Extended certified, but its time and Work ratios versus K4 were
0.891 and 0.901; the added continuous-copy pack harmed search relative to
Core. Core passes the fragmentation-witness half of Gate C.

## Coarse-K1 weakness witness

Instance: `round39_small_hard_V12_M3_Q30_slot08_seed1288546114`.

| Arm | Strict certificate | Exact phase (s) | Work | Nodes | Independent integer jobs |
|---|---:|---:|---:|---:|---:|
| external K4 | yes | 74.789 | 133.735 | 7878 | 7 total integer jobs; 3 terminal MIPs |
| external K1 | yes | 406.559 | 739.784 | 24652 | 1 |
| P-GRB | no (time limit) | 1780.451 | 3022.429 | 866259 | 1 |
| ST-K2-I | yes | 175.453 | 313.328 | 16879 | 1 |
| ST-K2-P-Core | yes | 98.225 | 183.296 | 11378 | 1 |
| ST-K2-P-Extended | no (strict gate rejected) | 112.496 | 208.754 | 11094 | 1 |

The K1 and external-K2 disjunctive root bounds are both
`0.09394825539359326`; the right interval alone is much stronger at
`0.32496933294190883`, but the left interval controls the disjunction. Core's
root bound is `0.09399500766227341`, an absolute improvement of about
`4.68e-5`; I and Extended remain at the K1 value.

Core certifies the common objective `0.50634330756520596` using 0.242 of K1
time and 0.248 of K1 Work, so it clearly remedies the coarse-K1 weakness.
However, its ratios versus external K4 are 1.313 time and 1.371 Work, exceeding
both frozen 1.25 ceilings. Extended's native status was optimal and its
incumbent verified, but the native-bound residual `1.33e-7` failed the strict
certificate gate; it cannot count as a gate pass. Core therefore fails the
positive-control half of Gate C.

## Interpretation

Core is the only serious static candidate: it combines complete K2 root-bound
capture on every panel row with a single native proof job, wins decisively on
the fragmentation witness, and strongly improves over K1 on the opposing
witness. It nevertheless does not preserve external K4's best case under the
predeclared tolerance. The experiment therefore supports the architecture as
technically feasible and scientifically informative, but not as a replacement
for the validated external K4 C6 default.

The trajectories also reject two simpler explanations. One-tree operation by
itself is insufficient (ST-K2-I caps on the fragmentation witness), and the
Extended continuous-copy pack is not automatically stronger in practice
(identical root bound and roughly double Core time on that witness). The
inventory-bit perspective block changes search behavior even when the root
objective is unchanged, but root strength alone does not predict the full
proof trajectory.
