# HGA-TGBC startup forensics

## Result

The frozen exploratory classification is
`simple_start_promising_for_future_validation`.  SIMPLE-START passes the material V10 and transfer gates and has a lower geometric-mean ratio than LIGHT on V10 without a worse transfer ratio.  This is an ablation conclusion only:
C6-HGA-FULL remains the validated Gurobi mainline, and no startup variant is
promoted in Round 34.

## Required questions

1. **M=1 HGA fraction.** HGA-TGBC accounts for an arithmetic mean of
   69.97% of full C6 process time over the six official
   V10 M=1 rows.  Other pre-exact startup accounts for
   0.20% and the downstream exact framework
   accounts for 29.83%.  Phase-level construction and
   downstream timings remain available per run.
2. **Work after the last useful improvement.** The median official FULL run
   executes 2000 generations after its last strict
   incumbent improvement; the fixed baseline stop is 2,000 stagnant
   generations.
3. **HGA-LIGHT UB quality.** LIGHT loses no startup-UB quality beyond tolerance
   on 0/18 V10 and 0/4 transfer pairs (that is, zero degraded pairs).  Exact
   per-instance values are in `hga_incumbent_quality_tradeoff.csv`; LIGHT uses
   the one frozen 1,000-stagnation setting selected from historical replay and
   development evidence.
4. **Downstream exact cost.** The paired exact-phase ratios are in
   `hga_exact_phase_tradeoff.csv`; the V10 geometric-mean LIGHT/FULL exact-phase
   ratio is 0.994.
5. **End-to-end LIGHT time.** LIGHT wins 18/18 V10 pairs;
   its geometric-mean total-time ratio is
   0.815.
6. **Consistency by M.**

| M | Instances | LIGHT wins | LIGHT/FULL geometric mean |
|---|---|---|---|
| 1 | 6 | 6 | 0.674 |
| 2 | 6 | 6 | 0.919 |
| 3 | 6 | 6 | 0.873 |

   The paired outcomes for both exploratory arms, grouped independently by M,
   Q, and scenario, are:

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

7. **Simple verified startup.** Yes.  The pre-existing deterministic greedy
   path evaluates its three general construction modes, independently verifies
   every candidate, and selects the best; no new heuristic was invented.
8. **SIMPLE-START tradeoff.** It wins 18/18 V10 pairs with a
   geometric-mean total ratio of 0.413;
   median startup falls from 2.310 s for FULL to
   0.003 s.  Its UB is weaker on
   12/18 V10 and
   3/4 transfer pairs; maximum relative
   degradation is 6.984984 on V10
   and 0.213127 on transfer.
   Despite that, its exact-phase geometric-mean ratios are
   0.954 and
   0.821, respectively.
9. **Harder transfer value.** On the four frozen V12/V20 anchors, LIGHT/FULL
   has geometric-mean total ratio
   0.918, while SIMPLE/FULL has
   0.586.
10. **Is 2,000-stagnation justified?** The observed incumbent and exact-phase
    tradeoff, rather than generation count alone, determines the classification
    above.  The long post-improvement tail shows reducible startup effort, but
    only the uniform transfer gate can establish whether reducing it is safe.
11. **Future uniform candidate.** The classification and its stated gate are
    the answer; per-instance tuning or dispatch was not used.
12. **Mainline decision.** Evidence may justify a later separately frozen
    qualification only when the classification names a promising alternative.
    Round 34 itself keeps C6-HGA-FULL stable.

## Timing convention and scope

All official comparisons use one thread, one executable, Gurobi 13.0.2,
process-entry timing, and the identical frozen exact phase.  Startup time is
included in the total.  Historical Round 33 generation logs were used only to
select the single uniform LIGHT setting before official execution; historical
raw rows are not mixed into the Round 34 paired tables.
