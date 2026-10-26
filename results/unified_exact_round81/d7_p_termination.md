# D7 P-GRB: valid interrupted evidence at the frozen whole deadline

The original twelfth arm reaches the already-declared whole-run hard stop at
3598.061999999918 paid seconds, within its3600s cap. The supervisor terminates
the still-running child, records returncode1 and restores the original affinity.
There is no normal native finalization or result.json. One Optimize starts and
zero Optimize-return events occur. The native log still advances at3594s; its
last progress row is not a final nodes/iterations/Work total.

This is the existing whole-experiment deadline policy, not a new component
slice, forced diagnostic, algorithm restart or outcome-dependent rule. The
frozen round81_research.py explicitly accepts either normal return or this
within-cap hard stop before replaying the committed evidence. launch.forced
is false. completion.forced_criterion_seen only records that a native witness
and a bound were observed; it does not mean the forced diagnostic path ran.

All305 observed commits pass the driver's independent replay, including235
original-physical native witnesses and68 full-domain bound events. The best
physical U is .2372849915487284, global L .19858649317712468, and absolute
gap .03869849837160372. The last improving witness is available at3535.828s.
The endpoint source is interrupted_committed_evidence; certificate and
solver_finalization_certificate are both false. No unobserved or incomplete
payload supplies this endpoint. Joint stage receipt/physical/scope replay is
still pending while the remaining two originally admitted arms run.

The same frozen analysis uses observed evidence for this arm's checkpoints,
including3600s, instead of treating it as a normally finalized result. It also
counts normal returns separately. Full paid process cost remains charged;
.241846600082s of offline per-run replay is separately retained. Nothing is
backdated, clipped or assigned a missing final native Work total of zero.

This arm is retained without rerun. It is distinct from the invalid R72 D7
watchdog experiment, which exceeded its cap and remains excluded. The present
run does not establish an optimality certificate or strict rational proof.

The official Gurobi13.0 parameter reference, checked2026-09-16, states that
TimeLimit can be exceeded while termination-related attribute computations
finish. Thus a native TimeLimit is not itself an exact whole-process deadline.
This documents a general API limitation; the present logs do not identify
which internal computation delayed this particular return. No settings or
deadline margins are changed after observing it. Source:
[Gurobi TimeLimit parameter reference](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html).
