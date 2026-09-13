# Actual algorithm and state contract (Round64 initial implementation)

| Component | Actual policy and evidence source |
|---|---|
| Cold startup | Existing simple greedy startup; empty initial diagnostic state only in fixed-F0 structural harness. No PREFIX, archive, injected candidate or historical routes. |
| Warm startup | `research-round64-k1-h` explicitly inherits `paper-k1-am-sf`: full HGA, seed 20260626, generation-stagnation 2000. Current process constructs/independently validates candidate and pays its entire wall cost. Source: PaperK1AmSf.cpp and main.cpp preset adapter. |
| Outer | F0, K0=1, midpoint, balanced normalized closure, tau=.08, native-target, exact-parent, inherited coverage. Compatibility C6 rho=.01 is not tau. Current decision ledger is authoritative. |
| LP | Full canonical F0 continuous relaxation with current G interval, F<=U and safe domains. Q/T/SEP/JOINT canonical rows are present in every LP. |
| MIP | Same canonical F0 with original integer variables; new q/f continuous. All original physical/Gini rows retained. No callback/resource cut pool or new branch setting. |
| Optional row scope | Round64 rows are global physical; B/c/taubar are bound to all original physical data. Diagnostic pin rows belong only to fresh feasibility probes and never enter full algorithms. |
| Model lifecycle | Inherited per-leaf model object reuse when request permits it and fingerprint is unchanged. New leaves read canonical model; stale fingerprint is an error. Temporary LP types restored to integer types on subsequent MIP. Terminal requests release model. Disposable child probes remain disposable. See request flags and actual per-call ledger. |
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

The implementation adapter and telemetry are engineering, not theoretical
contributions. The q lift is a familiar inventory flow. Claims for arc sharing
require incremental projection evidence and separate complete-cost validation.
All research presets and the shared switch are explicit, default off, and
plain-baseline rejects them. Historical research facilities remain available.
