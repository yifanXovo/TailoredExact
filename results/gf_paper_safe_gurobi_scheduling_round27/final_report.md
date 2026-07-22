# Round 27 final report

## Outcome

Classification: **paper_compatible_but_performance_risky**. C2 is not promoted; the stable mainline
is unchanged. The paper-compatibility static audit is True, the
dynamic exactness/lifecycle audit is True, and deterministic HGA
repeatability is True.

The clean build/test gate executed 20 C++
tests across the two configurations, all
8 Python test scripts, and
18 direct Round 27 checks. The C2/P-GRB
executable SHA-256 is `90bc8a3f55c0e372aea78831823ae5aac1422ae2ab2170507bdc96c0b638aa2b`; C0 is
`002ab0f3f3fc1f80bb4b8a6eb10fddaaf013f5c493317884c977098ede0cc15c`; the CPLEX-only build is
`44809e109cda75bfd51921df2f8112d8cfa964df2573f6412554b6d72b4e233e`. Solver versions are Gurobi
13.0.2 and CPLEX 22.1.1.0.

## Frozen algorithm

C2 fixes seed 20260626 and stops HGA only after 2,000 consecutive completed
generations without strict global-best fitness improvement. No wall-clock
predicate is present in that loop; wall time is telemetry. The exact phase
selects the minimum-valid-bound leaf, solves its complete LP relaxation,
solves both eligible midpoint-child LPs, atomically splits only for child LP
infeasibility or a strict certificate-tolerance bound gain, and otherwise
optimizes the complete terminal interval MIP exactly once. An overall-deadline
interruption leaves that leaf open and stops the whole tree.

## HGA qualification

- high_imbalance_seed3202 rep 1: 2083 generations, 2000 final non-improving generations, UB 1.74931, 32545 decoder calls, 15.8519 s telemetry.
- moderate_seed6301 rep 1: 3325 generations, 2000 final non-improving generations, UB 0.607529, 50065 decoder calls, 51.1336 s telemetry.
- V12_M2 rep 1: 2123 generations, 2000 final non-improving generations, UB 0.718504, 24494 decoder calls, 6.96824 s telemetry.
- V12_M2 rep 2: 2123 generations, 2000 final non-improving generations, UB 0.718504, 24494 decoder calls, 7.06336 s telemetry.

## V12 certificates

- V12_M1: strict=True, LB=0.357201, UB=0.357201, gap=2.6419e-15, wall=142.581 s.
- V12_M2: strict=False, LB=0.65576, UB=0.718504, gap=0.0873257, wall=294.051 s.

## Difficult V20 comparison

Across available high-imbalance, moderate, and tight-T pairs, median C2-minus-C0
common-UB gap is 0.0500912 and median C2-minus-C0 bound-progress
AUC is 0.00308107. Pairwise evidence is in `c0_vs_c2.csv`; the
plain-Gurobi comparison is in `p_grb_vs_c2.csv`. C2 beat P-GRB's final bound
on all three difficult V20 instances, but it did not retain C0's endpoint
advantage on high3202 or moderate3302. The generation-stagnation C2 verified
UB exactly matched C0's verified UB on all five Stage 2 instances.

## V50 smoke

- C2 status=missing_result, authoritative=False, LB=unavailable, UB=unavailable, gap=unavailable, peak memory=unavailable GB, lifecycle=False.

C2 completed the same byte-identical 3,325-generation HGA trajectory as Stage
1, then exceeded the emergency shutdown margin before creating its first paper
tree ledger or final JSON. The row is failed/excluded without retry. P-GRB
returned valid LB 0.43346, verified UB
1.04213, Work
722.382, and peak memory
0.463385 GB. See
`v50_failure_audit.md`.

## Run accounting and resources

The official matrix contains 21/21 observed rows: 20 completed,
1 process failure, 12 time-limited/interrupted, and
1 excluded from authoritative quantitative comparison. Aggregate Work,
LP Work/count, terminal-MIP Work/count, splits, model reads/builds, and maximum
peak memory by arm are serialized in `final_audit_summary.json` and the
per-run values in `lifecycle_and_resource_summary.csv`.

- P-GRB: Work 2741.93; LP count/Work 0/0; terminal-MIP leaves/optimizes/Work 0/0/0; splits 0; reads/builds 6/0; models created/freed 6/6; maximum peak memory 0.463385 GB.
- C0-LEGACY: Work 1952.22; LP count/Work 0/0; terminal-MIP leaves/optimizes/Work 0/0/0; splits 6; reads/builds 30/30; models created/freed 30/0; maximum peak memory 0.321154 GB.
- C2-PAPER: Work 2160.8; LP count/Work 511/224.47; terminal-MIP leaves/optimizes/Work 167/167/1936.33; splits 239; reads/builds 678/511; models created/freed 678/678; maximum peak memory 0.183163 GB.

The dedicated LP/terminal-event counters are C2 fields; their zeros for
P-GRB and C0 mean not applicable rather than absence of native MIP work.

Lossless packaging compressed 598 artifacts from
855170807 original bytes
to 119811027 bytes; all
restoration hashes and byte counts match. The largest retained artifact is
`results/gf_paper_safe_gurobi_scheduling_round27/runs/stage2__V12_M2__p_grb__300s/progress.csv.gz` (532020 bytes).

## Exactness and compatibility

The LP relaxation is a valid lower bound for its unchanged interval MIP; child
bounds inherit valid parent bounds; atomic interval replacement preserves
coverage; declining a split retains and solves the entire parent MIP; LP
statuses never serve as integer certificates; interrupted terminal leaves stay
open; and the global bound remains the minimum valid relevant-leaf bound.
Strict certification requires every relevant leaf closed. C2 contains no
internal seconds, Work, node, solution, attempt, or retry scheduling decision.
The only event TimeLimit is the remaining overall experiment deadline.

Unresolved performance issue: C2 missed the V12_M2 certificate, its difficult-instance final gaps regressed, and V50 terminated after HGA before its first paper-tree event.
