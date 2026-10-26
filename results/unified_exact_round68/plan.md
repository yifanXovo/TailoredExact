# Round68 — reuse the existing complete witness in native VD-P MIP

Base: completed Round67 PR128, a47e86a57a1f68ca6e515877193cb8696d1aa13e.
Branch codex/round68-vdp-verified-start; owned E:/codes/ExactEBRP-round66.
The original user workspace and frozen Round66/67 binaries/evidence stay intact.
Overall goal remains active and unmet. No subagents or parallel optimizers.

Hypothesis: VD-P's stronger relaxation and C2/D4 gains may be retained while
reducing D3/D6 native feasibility difficulty by supplying the full already-paid
outer witness to the actual current MIP. D6's witness was feasible in every
compatible inspected model, yet terminal MIP lacked an incumbent. D3's VD-P
native incumbents were late. This is an integration question, not a guarantee
that a supplied incumbent improves dual proof or fixes HGA startup.

Use research-round68-vdp-start (VD-S) versus same-build VD-P, K1-R and original
P-GRB. Full HGA seed20260626/pop24/decoder10/stagnation2000 and AM remain fixed.
Only current original-route witnesses acquired inside that paid run are allowed.
Normalize interchangeable equal-Q vehicles, reverify, map all actual VD-P
columns, check the current interval/cutoff, bounds/types, every linear row and
objective, then submit one complete Start before each needed MIP. Include the
LP-to-MIP retained-model path. Incompatible intervals skip that witness without
changing proof coverage. No new search/construction, native parameter tuning,
reset, forced reload, instance gate, timed retry, internal seconds or Work limit.

Read back submitted Start values; separately record native loading/acceptance
and observation of the supplied vector. API success is not adoption. Preserve
the full witness/vector and actual model identity for post-experiment checks.
Recompute the remaining single whole-run deadline immediately before Optimize
so mapping/validation cost cannot extend it. All overhead is paid. Unexpected
eligible mapping/API/row failures invalidate qualification, rather than quietly
counting a supposedly enabled mechanism that never ran.

This repeats neither Round61's separately constructed16-generation/30s PREFIX
nor Round44's K4/envelope discard-and-reload start setting. Round44's dedicated
D3 pair accepted no starts. See Round67 provisional_integration_question.md
and gurobi_start_api_review.md for primary official API checks and history.
Start reuse is established technology, not a new general theorem.

Before native experiments, run the necessary CTest suite and at most4 native
original-problem micros at20s, including an actual retained LP-to-MIP Start.
Main development plan: four arms on D3 at300, D6 at600, C2 at300 (12 runs).
If this reveals a useful candidate without unresolved implementation failures,
open the already-declared D4 protection check with the same four arms at300.
Maximum16 performance+4 micros,6080 experiment seconds. Build-only identity
exports and CTest are separate qualification costs; optimizer calls and all
failed attempts are counted explicitly. Optimizers serial, no concurrent build
or heavy audit. A new written resource revision is required beyond this plan.

Evaluation thresholds remain Round67's predeclared rules: both-certified
V<=12 and both under60, material>2s/20%, severe>5s/50%; otherwise certified,
material>10s/15%, severe>30s/50%. Both open, absolute-gap material>.001/10%,
severe>.01/50%. Certificate gains/losses and mixed UB/LB outcomes are separate.
These are not significance tests or automatic K1 per-point vetoes. New VD-P
controls also recheck the previous stage's large gains; no old times are spliced
into strict pairs. P-GRB is unchanged compact/native defaults without starts,
cuts/HGA/imported bounds. Gurobi13.0.2, Threads1, Seed0, PresolveAuto, original
zero requested gaps and numerical standards for all arms.

All current roles are development. No confirmation or3600/7200 extension is
opened. The stage needs actual implementation, credible full-run comparisons,
an honest decision and a new independent draft PR, regardless of result.
