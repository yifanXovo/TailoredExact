# Actual algorithm and state contract (Round64)

| Component | Actual policy and evidence source |
|---|---|
| Cold startup | A verified empty route set, Y=b, in BOTH cold full algorithms and the fixed-F0 harness. `round59_simple_start` returns directly after this candidate; the CLI's inherited `greedy` label does not mean a greedy route search ran. No PREFIX, archive, injected candidate or historical routes. |
| Warm startup | `research-round64-k1-h` explicitly inherits `paper-k1-am-sf`: full HGA, seed 20260626, generation-stagnation 2000. Current process constructs/independently validates candidate and pays its entire wall cost. Source: PaperK1AmSf.cpp and main.cpp preset adapter. |
| Outer | F0, K0=1, midpoint, balanced normalized closure, tau=.08, native-target, exact-parent, inherited coverage. Compatibility C6 rho=.01 is not tau. Current decision ledger is authoritative. |
| LP | Full canonical F0 continuous relaxation with current G interval, F<=U and safe domains. The selected Q/T/SEP/JOINT/QCAP canonical rows are present in every LP. |
| MIP | Same canonical F0 with original integer variables; new q/f continuous. All original physical/Gini rows retained. No new resource callback, cut pool or branch setting. Inherited progress/native-bound-target callbacks remain active. |
| Optional row scope | Round64 rows are global physical; B/c/taubar are bound to all original physical data. Diagnostic pin rows belong only to fresh feasibility probes and never enter full algorithms. |
| Model lifecycle | Inherited per-leaf model object reuse when request permits it and fingerprint is unchanged. New leaves read canonical model; stale fingerprint is an error. For a retained LP, original variable types are restored immediately after the LP solve, before any later MIP request. Terminal requests release model. Disposable child probes remain disposable. See request flags and actual per-call ledger. |
| Reused state | Gurobi model object and whatever state its API retains after type/domain changes; no claim to retained or copied entire B&B tree, nor guaranteed LP basis reuse. No Round63 root/fresh override is enabled. |
| Candidate transfer | Verified original route updates U and domains in warm arms. Stable native-start flags remain false. Auxiliary route mapper computes q/f/h with the identical safe coefficients if actual target names require them; this capability does not enable starts. Mapping/current-domain tests are separate. |
| Stops/certificates | Original independent feasible witness plus complete global coverage and qualified native bounds; zero only from this run's legal zero witness and F>=0. Native status, numeric gate and original certificate remain separate. No tolerance changes. |
| Official reference | Original compact P-GRB, default heuristics, no HGA/PREFIX/extra rows/starts; original model fingerprint checked. |
| Solver | Gurobi 13.0.2, Threads=1, Seed=0, Presolve=-1 (Auto), requested MIPGap=MIPGapAbs=0; native parameter readback required when optimization occurs. |

The static common LP/MIP scope is deliberate. It requires no retained-row
guard workaround, no additional first-LP solve, no copy model and no implicit
restart. Every main arm has the same lifecycle policy; candidate-dependent
incumbent/bound changes may still change the unchanged outer controller's calls.
Cold-to-warm startup differences are never credited to the resource block.

The frozen protocol's formulation `callback="off"` refers to the added
resource mechanism. It does not disable the inherited progress and native
target callbacks that appear in the native logs. Their existing cost and
termination behavior remain part of every complete algorithm run.

Description correction after the full native micro: the initial protocol's
`startup.cold="inherited simple greedy"` repeated a CLI label and was imprecise.
The code at main.cpp's `round59_simple_start` branch, heuristic.csv's
`round59_empty_routes_Y_equals_b` event and frozen canonical hashes establish
the actual empty-route behavior. The original frozen protocol is preserved;
this is a description erratum, not a baseline/model/algorithm modification.

The legacy configuration snapshot has no dedicated Round64 description case,
so research results retain `preset_certificate_scope="custom"` and
`preset_reason="custom command-line configuration"`, with empty descriptive
feature lists. These strings do not imply that actual options are custom or
unknown: the explicit adapter first applies the canonical `paper-k1-am-sf`
configuration and restores the research name, with isolated resource/startup
guards. Actual option values, canonical models, decision ledgers, original
verification and coverage establish the contract and certificate scope. The
generic description fields are not used to certify a run or to claim stable
mainline qualification. They are documented rather than silently interpreted
as complete algorithm metadata; no model/search change is needed.

The implementation adapter and telemetry are engineering, not theoretical
contributions. The q lift is a familiar inventory flow. Claims for arc sharing
require incremental projection evidence and separate complete-cost validation.
All research presets and the shared switch are explicit, default off, and
plain-baseline rejects them. Historical research facilities remain available.
