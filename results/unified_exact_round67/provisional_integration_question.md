# Open integration question found while the frozen panel runs

This is source review and a possible follow-up, not a selected next candidate,
an opened experiment, or a change to Round67. Final selection waits for D6,
D3 and C2. It must not become another local time slice or instance gate.

D6 K1-R's terminal native log initially shows no incumbent while the outer
controller owns the full-HGA verified route. The distinction is real: a legal
external UB/cutoff is not the same as a native feasible solution. Current
Round61 `prepareRound61Candidate` constructs a separate16-generation PREFIX;
it does not simply pass the already paid full-HGA witness. That prefix can be
worse than the current cutoff and therefore ineligible for a given leaf.

`GurobiBaseline.cpp` already loads GRBsetdblattrarray and has a complete Start
submission path for the older explicit P-GRB-plus-HGA ablation. Official P-GRB
must of course keep that option off. The interval callback paths use the
Round60/61 candidate mechanism and current-model checks instead. Merely turning
on those mechanisms does not establish reuse of the full-HGA witness.

`MipStartMapping.cpp` currently recognizes the original bit/product columns
and rejects unknown columns. It does not yet map VD-P selector/perspective or
LOG code columns. A future existing-witness integration would need a complete
encoding-aware mapping and original-route plus current-bound/type/linear-row
verification before any submission. Equality with F<=U is legal; an incompatible
Gini interval must reject that witness without narrowing the proof range.

Questions worth settling if current evidence warrants the follow-up: does
feeding a compatible already-paid witness improve native search/proof, what
does it cost across all necessary calls, and does it preserve the C2 protection
where prior PREFIX submission lost a certificate? API success alone cannot be
counted as use or benefit. Start insertion and callback submission are distinct
mechanisms, and neither is a new general theoretical contribution. This cannot
by itself repair the HGA startup cost or prove the D6 long-window deficit fixed.

Further source/history review narrows the opportunity: FixedIntervalMipRequest
already carries warm_start_enabled and verified_start_routes. The backend's
Start path is gated by !retained. Round44's verified-start policy explicitly
discards/reloads the leaf to enter that path. Its completed small-panel study
used K4 plus affine envelopes and failed primary/fallback validation overall;
see results/gf_c6_envelope_tail_repair_round44/final_report.md and
mip_start_ablation.md. Thus full-witness starts are not an untested general
mechanism. A future study must isolate current K1/VD-P integration, complete
state-column mapping and deliberate handling of LP/MIP model retention. It
must verify current Gurobi semantics, not assume an old !retained guard is an
unavoidable API limitation. The current frozen Round67 preset submits none.

The Round44 dedicated six-role start ablation reports shifted on/off Work/time
gmeans0.972980/0.981164 and four accepted starts. Crucially, its historical D3
pair considered three starts but accepted none and had identical Work; that is
not an effective positive/negative test of an accepted D3 start. These are old
build/K4-envelope observations, not current timings. The current D3 VD-P run
also spent most of its300s without a native incumbent and ended with gap
0.00318974760831747, losing most of K1-R's P-GRB advantage. This gives a
concrete current integration question, while still leaving proof-cost and
startup hypotheses separate. No performance benefit is presumed.

Backend timing deserves a specific implementation check: its native TimeLimit
is currently assigned before Start mapping. A new mapping/residual pass must
consume the same already-running global deadline, with the remaining allowance
refreshed immediately before Optimize. It must not create a new component
budget or permit mapping time to extend the whole run. Clear or overwrite stale
explicit Start values deliberately when the current witness is incompatible;
do not confuse native reuse of a previous solution with this supplied vector.
