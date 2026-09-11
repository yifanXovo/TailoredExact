# Round 59 frozen scope and execution protocol

Baseline: `codex/round58-citibike443-k1-vs-pgrb` at
`edd65fe9f5bd37616366c1c6ca48379df062cdcf`. PR 117 targets Round56;
PR 118 targets main; neither is merged. The new PR targets Round58.
The repository start audit preserves the three pre-existing tracked changes
by hash and inventories untracked paths. No reset, stash or cleanup is used.

`panel.json` freezes eight development and two confirmation scenarios before
Round59 performance. Original input bytes, V/M/Q, mathematical T and handling
times are retained. No confirmation result selects a candidate.
120 seconds is a complete process budget, with six seconds withheld from
the solver and a three-second normal shutdown margin. A serial Python
watchdog kills a process at the cap. All attempted performance processes,
including failed CLI launches, are charged to the 80-process ledger.
Maximums: 12 distinct performance scenarios; twelve 1800-second processes;
four 3600-second processes. No longer runs are authorized.

The four attribution arms are official compact P-GRB, unchanged paper K1-H,
research K1-S (independently verified empty routes and Y=b), and research
F0-Single-S. Empty-start rejection fails explicitly, never invokes HGA.
K1-S retains the entire first-class outer controller. F0-Single-S retains
complete improving-domain coverage and exact closure but bypasses the split
eligibility and the intermediate native-target frontier action. Parent LP
processing remains part of the measured process; a state closed by its LP
may legitimately make zero MIP calls. It must never make speculative child
LP calls or multiple terminal MIP calls. This is checked from lifecycle logs.
No native MIP start or hint is requested by either simple-start arm.
Source inspection confirms that the existing canonical K1 writer actually
sets `incumbent_epsilon=0`: its explicit row is F<=U, a closed superset of
strict improvers. Round59 preserves this value and logs it; it does not
silently change it to F<=U-epsilon. The original global certificate still
requires independently verified U, valid lower bounds and complete coverage.

## Internal hypothesis A: tighter support-duration rows and execution

The historical static conditional support row uses a large coefficient;
Round52 dynamic separation considered up to triples and Round53 isolated
PreCrush, no-op callbacks, dry-run enumeration and submission. Those results
are pre-epoch-fix performance context, not new matched comparators.
This experiment uses **the same deterministic all-pair cut set** in static
and native pool arms, compared to no added rows. No instance-name dispatch,
larger enumeration, or root-violation gate chooses the set. On selected
small frozen states the set has M*n*(n-1)/2 rows at most.

Let c=c_pick+c_drop. For a pair A, add
`c sum_A p_ki + t(A)(sum_A z_ki - 1) <= T`.
Compute t(A) as the cheaper depot-pair-depot order in the directed all-pairs
shortest-path closure. Nonnegative travel times are checked. Shortcutting
any realized route in that closure proves its travel is at least t(A) if
both pair stations are visited, even when original distances are nonmetric.
If at most one is visited, the t term is nonpositive and the row follows
from the existing total operation budget. Thus the row is integer redundant
relative to the full route model, and may legally use Lazy=-1. In particular,
no violation is possible when sum_A z<=1 and the original operation budget
holds. Pool attribute values must be read back; failure rejects the run.
This proof supplies a stronger conditional coefficient than the legacy
static big-M row, not a claim of literature novelty.

The initial matched states are the major and strong control, using their
independently evaluated empty incumbent, full improving interval, identical
cutoff, epoch zero and deterministic model identity. Static/pool are also
compared on LP/root cost, nodes and wall time. Pool submission is not evidence
of immediate insertion or persistent activity. Root and representative
nonroot samples are observations of relaxation points, not branching choices.

## Independent hypothesis B: bounded native primal-search diagnostic

Historical Round50 evidence records delayed incumbents as well as weak root
bounds; its rejected B1/B2/B3 assigned entire families and A1 used probes.
After inspecting current fixed-state samples and incumbent trajectories,
one uniform MIPFocus=1 diagnostic is eligible on two to four development
states with default branching retained. It adds no probes, historical bounds,
starts, or route imports. The same model, cutoff and cap remain in force.
This is a search-process diagnostic, not a mathematical contribution or a
new recommended preset. If the current evidence instead points to product
representation, an explicitly documented structural candidate may replace it.
Each independent mechanism permits at most one reasoned revision; combinations
open only if both separately qualify. A protected-instance regression blocks
promotion but does not suppress the other mechanism's experiment.

## Gurobi API interpretation

Gurobi 13.0.2 headers are installed at D:/gurobi1302/win64/include.
The installed docs directory only contains a logo, so official online
reference pages are the documentation fallback:
[Lazy attribute](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/constraintlinear.html),
[C callback API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/callback.html),
[parameters](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html).
Lazy=-1 creates an optional user-cut pool entry; it must not replace a
necessary feasibility or objective-definition row. GRBcbsolution is a
supported API but was not loaded by this adapter at the start. The public
API does not expose the full native pool, local model or branching scores.
