# Round67: inventory-state disjunction encoding

Base: Round66 PR127, 7c3b18912e16c66f9927ff71563fc25a9f488ff5.
Branch codex/round67-log-inventory-states, workspace E:/codes/ExactEBRP-round66.
Round66 is complete. Reuse its research map and the full user contract there.

The primary target remains D6's actual P-GRB proof advantage. ARC did not repair
it; its root LP objective did not improve. This stage turns to the inventory/Gini
product. Reassess Round55 VD-P, previously stopped by a single D3 K1 regression,
and replace its one-hot integrality with a logarithmic encoding of the same
allowed inventory states. General disjunctive encoding is established theory;
the contribution being tested is its integration and full BRP performance.

Formal arms: P-GRB (original compact, native heuristics), K1-R (canonical full
HGA, verified retention/zero stop only), VD-P (K1-R plus original one-hot VD-P),
LOG (K1-R plus logarithmic VD-P). ARC, time/load extras, VD-J penalty equality,
resource credits, projection, and other research mechanisms are off. Native
Gurobi remains the complete MIP engine, 13.0.2, Threads1, Seed0, PresolveAuto,
zero requested gaps and original numerical settings. HGA seed20260626 and
stagnation2000/pop24/decoder10 remain unchanged. No new tuning parameter.

Before results: maximum16 development launches, four arms on each of D3/D4/C2
at300 and D6 at600. Maximum3 native micros at20 (P-GRB, VD-P, LOG), plus build-only
fingerprint/shape exports and the necessary CTest suite. All optimizers serial;
no concurrent compilation/heavy audit. Worst experiment allowance6060 seconds.
Record actual calls and wall cost. Any additional phase needs a written resource
revision before launch. A component timeout ends the whole run; budgets never
select between the formal algorithms.

Roles: D3 old VD-P regression and current nonzero proof/protection; D4 major
K1-vs-P protection; C2 short-T nonzero multi-call protection; D6 long-T V30
CitiBike proof deficit. These are all development data, not sealed confirmation.
New same-build P-GRB and K1-R binding is required. Do not splice old times into
strict pairs. Compare actual initial witnesses and model/parameter identities.

Keep Round66's practical thresholds: both-certified small V<=12/under60,
material >2s and >20%, severe >5s and >50%; other certified material >10s and
>15%, severe >30s and >50%. Uncertified absolute-gap material >.001 and >10%,
severe >.01 and >50%. P-certified/candidate-open is a separate important negative.
These are not significance claims or a per-point K1 veto. Report UB and LB
separately, including mixed outcomes and raw signed numerical discrepancies.

No confirmation or3600-second expansion is yet authorized by this stage plan;
open a bounded extension only if the complete development evidence supports it.
Stage completion requires a new draft PR regardless of positive/mixed/negative
performance. The overall goal remains active and unmet.
