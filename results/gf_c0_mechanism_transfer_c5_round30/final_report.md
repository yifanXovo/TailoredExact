# Round 30 final report

## Outcome

Round 30 completed all 78 unique official processes with zero failed return
codes, zero emergency timeouts, and no excluded official row. Of these, 65
ended at the engineering time limit and 13 were strictly certified. The
materialized Stage 1/2/3/4 tables contain 21/51/25/10 rows because overlapping
frozen reference rows are reused without rerunning them.

All 27 official C5 rows pass the structural exactness, trace-completeness,
lifecycle, and false-certificate gates. The 17-row primary matrix contains
four strict C5 certificates and thirteen valid time-limited C5 endpoints.

Final classification: **`paper_exact_and_performance_promising`**.

This classification justifies a later long-run C5 validation. It does not
promote C5 automatically: corrected S0/F0-CPLEX remains the stable accepted
paper mainline.

## Evidence correction and post-official analysis incidents

Round 29 C4 did not emit the compatible global-bound trace its analyzer
expected. All 17 historical C4 anytime rows are therefore marked
`auc_unavailable`; no endpoint pseudo-trajectory is used, and historical
Round 29 files are unchanged. Round 30 C4/C5 trajectories are left-continuous
observed traces with no interpolation and no extension after their final
event.

Two analysis-only defects were found after the 78 solver processes completed:

1. dormant zero-valued external-tree fields shadowed valid P-GRB/S0 native
   bounds;
2. the CSV writer inferred columns only from its first row and omitted later
   observed-AUC fields when the first row was unavailable.

Both first-pass outputs are retained under `incidents/`. General arm-aware
extraction and union-field regressions were added. No solver row was rerun,
and no C5 source, binary, parameter, target, split rule, or callback semantic
changed.

## C0 mechanism audit

The audit covers 57 retained C0/C1-equivalent runs, 1,386 native leaf events,
317 splits, and 951 shadow-policy rows. C0 and the rejected C1 label denote
the same frozen algorithm; run variability is not treated as an algorithm
change.

- First leaf processing produced 44.4888993 summed leaf-bound gain and
  43.3156144 immediate global-bound gain using 42,683.8145 observed Work.
- Repeated processing produced 2.40885584 leaf gain and 1.3793574 global gain
  using 69,500.3337 Work; 307/517 second processings were materially useful.
- Only 45/317 splits had an observed material immediate child contribution.
- Native processing closed 216 leaves; only eight verified incumbent
  improvements were observed.

Transferable mechanisms are validity-gated partial native lower bounds,
best-bound leaf interleaving, parent-bound inheritance, exact atomic coverage,
verified cutoff, and objective-defined milestones. Forbidden mechanisms are
30/60/... second quanta, fixed attempt/split ordinals, retries, elapsed
stagnation, Work/node/solution limits, and family/size/seed/instance dispatch.

In the shadow replay, the 1% normalized native-gain rule reached its target
after first processing on 89/317 parents, only after repeated processing on
50/317, and explained 157/317 historical splits without time or attempt
ordinals. All 317 replayed parent-retain/atomic-split choices preserved exact
coverage. The replay makes no counterfactual runtime claim.

## Selected C5 algorithm

C5 is the sole development prototype and is mathematically distinct from S0,
C3, and C4. It uses the same complete parent and two-child LP lookahead as C4,
then:

- splits immediately on child infeasibility;
- splits when normalized child-disjunction gain is at least `rho=0.01`;
- declines and solves the exact complete parent MIP when there is no strict
  gain;
- for a smaller positive gain, processes the same parent model until a valid
  `GRB_CB_MIP_OBJBND` reaches the complete child-disjunction bound, then
  terminates through `GRBterminate`, merges the valid bound, and requeues the
  still-open split-pending parent.

The next best-bound selection performs the delayed atomic split. Native
optimality/infeasibility closes the leaf; the overall process deadline leaves
it open with its valid bound. There is no internal time, Work, node, solution,
attempt, or retry decision.

Rejected directions were an ambiguous native-root-completion event, a
proof-fraction ladder, parent processing before a defensible child target
exists, parent-child basis transfer without a complete mapping proof, a
native-tree continuation claim, and a new cut family unsupported by the
forensics. No fallback prototype was used.

C5 reuses only the same leaf's Gurobi model object across LP-to-MIP domain
restoration. It makes no LP-basis, parent-child state, presolve/cut, or native
tree continuation claim.

## Primary results

Against C4, C5 has 10 final-LB wins, no losses, and seven ties. All 17 pairs
have complete observed common-window AUC: C5 wins 16 and loses one
(Moderate4302 by 0.00035285 normalized AUC while tying its final LB).

By size against C4:

| V | rows | C5 LB wins/losses/ties | C5 AUC wins/losses |
|---:|---:|---:|---:|
| 12 | 2 | 1/0/1 | 2/0 |
| 20 | 12 | 7/0/5 | 11/1 |
| 50 | 3 | 2/0/1 | 3/0 |

Against plain Gurobi, C5 has 11 final-LB wins, four losses, and two ties; its
observed AUC is mixed at 8 wins and 9 losses. V20 contributes 9/3 final-LB and
8/4 AUC wins/losses. V50 contributes 2/1 final-LB wins/losses but loses all
three P-GRB AUC comparisons. Thus the transferred mechanism is broadly better
than C4 while plain Gurobi remains a meaningful anytime benchmark.

V12 endpoints:

| instance | arm | runtime (s) | valid LB | verified UB | strict |
|---|---|---:|---:|---:|---:|
| V12_M1 | P-GRB | 34.856 | 0.3572005832084151 | 0.3572005832084155 | yes |
| V12_M1 | C4 | 134.888 | 0.3572005832084146 | 0.3572005832084155 | yes |
| V12_M1 | C5 | 54.153 | 0.3572005832084146 | 0.3572005832084155 | yes |
| V12_M2 | P-GRB | 169.249 | 0.7185040707549712 | 0.7185040707549709 | yes |
| V12_M2 | C4 | 295.023 | 0.6557601837879294 | 0.7185040707549709 | no |
| V12_M2 | C5 | 228.234 | 0.7185040707549704 | 0.7185040707549709 | yes |

On the seven C0 diagnostic anchors, C5 has 3 final-LB wins, 2 losses, and
2 ties. Five pairs have observed AUC (C5 3 wins, 2 losses); both one-callback
exact V12 C0 traces are explicitly unavailable. C0 remains an exact but
non-paper-compatible performance teacher.

On five S0 anchors, C5 has four final-LB wins and one loss. S0 AUC is not
claimed because those runs do not provide a compatible required trajectory.
This comparison does not change the mainline decision.

## Mechanism and resource evidence

Across the 17 primary C5 rows:

- 879 optimize and presolve executions: 665 LP, 94 partial-target MIP, and
  120 exact terminal/continued MIP calls;
- 214 observed MIP root executions;
- 192 completed splits, 82 final declined splits, and zero LP cutoff prunes;
- 211 recorded partial-bound events and 86 target-reached events;
- 665 model reads and 214 same-leaf in-memory LP-to-MIP reuses;
- zero basis submissions/acceptances and zero confirmed native-tree
  continuations;
- 8,394.7046 total Work: 1,020.1526 LP, 160.3141 partial MIP, and
  7,214.2378 terminal MIP Work.

The 94 target phases used 160.3141 Work; 86 stopped on their mathematical
target and eight proved infeasibility. The detailed trace records 172 partial
bound observations, 69 with immediate controlling-global-bound gain, totaling
0.2659695 gain. Terminal MIPs still account for 85.94% of C5 Work and remain
the main unresolved blocker. LP/root cutoff pruning remains zero.

C4 required 1,459 optimize calls, 1,104 LP calls, 355 terminal MIPs, 510
splits, and 8,928.9789 Work on the same primary matrix. C5 therefore translates
partial-bound interleaving into fewer lookaheads, splits, and terminal MIPs,
although terminal proof work still dominates.

## Repeatability

For all five Stage 4 instance pairs, HGA trajectories, leaf-event order,
root/target event sequence, split ledgers, parent-child bounds, final LBs,
certificates, lifecycle results, and model-reuse counts match across
repetitions. Final-LB absolute delta is zero for every pair. Four final leaf
ledgers are byte-identical; tight-T5102 differs only in a noncontrolling
deadline-interrupted leaf bound while retaining identical decisions and final
global LB.

Observed repeat AUC deltas range from -0.00505386 to +0.00072879, reflecting
wall-time placement of otherwise matching events. Complete traces are retained
for all ten repeat rows.

## Builds and audit

The frozen executable source commit is
`57e132254d3a7c5b6ec4a0b83e824c301ecf157a`. GCC/MSYS2 g++ 14.2.0 and CMake
3.30.5 built CPLEX 22.1.1 and Gurobi 13.0.2 variants. Their SHA-256 hashes are:

- CPLEX: `a1db6fdc744e9b253c113bb876ec21f61991bfb5fd6f6182f77d198421a3d5ee`
- Gurobi: `57db932e5eac1b8c7df668e00c302f49c1df19054519d8426133857281f5553e`

Both clean builds passed 13/13 C++ tests; all 13 Python regression scripts
passed before freeze and again after the analysis-only corrections. All Stage
0 gates and all 13 forbidden-logic scan rules pass. The original failed
Stage 0 aggregate and both post-official analyzer passes remain preserved as
incidents.

## Evidence package

The final package contains 10,900 evidence files excluding the manifest and
occupies 1,218,320,788 bytes.
The largest retained artifact is
`runs/stage3__tight_T_seed3101__s0_cplex__300s/global_node_trace.csv.gz` at
6,102,386 bytes. The packager losslessly compressed 3,865 eligible files and
verified every compressed file by restoration size and SHA-256 before
removing its uncompressed original. The manifest was regenerated after all
final narrative and summary edits and independently checked against disk.

## Publication decision

S0/F0-CPLEX remains the stable accepted paper mainline. C0 remains diagnostic,
C3 remains the equivalence reference, C4 remains the child-LP-benefit
reference, and C5 is an exact promising experimental candidate. A later
long-run C5 validation is justified, but this round does not merge or promote
it.
