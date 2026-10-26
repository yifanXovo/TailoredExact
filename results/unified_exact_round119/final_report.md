# Round119 fixed-candidate result

**STOP_TESTED_CONFIGURATION**. All nine fixed development arms qualified and the mechanism was actually exposed in all three candidate arms. F2 has a material complete-certificate time WIN, while N40 remains an open TIE against M-B. R98-C2 has a severe regression against the primary cold P-GRB benchmark and a severe loss against M-B. The predeclared primary-risk admission condition therefore fails; all three fixed E50-C1 positions are canceled, and this default-off tested configuration is stopped without another variant or default promotion.

The fixed panel completed 9 current arms with one PE SHA `e107d34ca849e3615cb812a7525ba9879e53946e04c7405d13a767786d3e06c6` and the frozen Gurobi13.0.2 DLL. ENS-C remains the default. R118 results remain unchanged.

## Complete endpoints and clocks

| Role | Method | own U | qualified L | signed gap | Original certificate | T_produce | T_verify | T_total |
|---|---|---:|---:|---:|---|---:|---:|---:|
| N40-R1-S | P-GRB | 0.8837281542 | 0.3511496789 | 0.5325784753 | False | 5371.481553 | 0.9363328 | 5372.417886 |
| N40-R1-S | M-B | 0.7822196776 | 0.5738917387 | 0.2083279388 | False | 5370.549561 | 14.4486398 | 5384.998201 |
| N40-R1-S | MB-PC | 0.7871576614 | 0.5682844249 | 0.2188732365 | False | 5371.8213 | 27.5480889 | 5399.369389 |
| F2 | M-B | 0.8659435203 | 0.8659435175 | 2.862223125e-09 | True | 717.4892725 | 4.2976478 | 721.7869203 |
| F2 | MB-PC | 0.8659435203 | 0.8659435203 | 2.553512957e-15 | True | 150.9622661 | 4.0343543 | 154.9966204 |
| F2 | P-GRB | 0.8659435203 | 0.7638685387 | 0.1020749817 | False | 1170.57582 | 1.5289497 | 1172.10477 |
| R98-C2 | MB-PC | 0.2404865434 | 0.1897550443 | 0.0507314991 | False | 1771.132937 | 12.0303405 | 1783.163277 |
| R98-C2 | P-GRB | 0.1983028486 | 0.186638092 | 0.01166475662 | False | 1770.57424 | 0.6476527 | 1771.221893 |
| R98-C2 | M-B | 0.1946348157 | 0.1907221082 | 0.003912707505 | False | 1770.460181 | 6.1574105 | 1776.617591 |

Signed gaps are preserved, including tiny negatives. A local interruption, local infeasibility or interval shrink is not a complete original certificate. Ratios of final proof time are not inferred for two open arms.

## Three fixed pairs per role

| Role | Pair | Classification | Severe regression vs control | Basis |
|---|---|---|---|---|
| N40-R1-S | MB-PC/M-B | TIE | False | both_uncertified_absolute_materiality |
| N40-R1-S | MB-PC/P-GRB | WIN | False | both_uncertified_absolute_materiality |
| N40-R1-S | M-B/P-GRB | WIN | False | both_uncertified_absolute_materiality |
| F2 | MB-PC/M-B | WIN | False | both_complete_certificate_time |
| F2 | MB-PC/P-GRB | WIN | False | candidate_only_complete_certificate |
| F2 | M-B/P-GRB | WIN | False | candidate_only_complete_certificate |
| R98-C2 | MB-PC/M-B | LOSS | True | both_uncertified_absolute_materiality |
| R98-C2 | MB-PC/P-GRB | LOSS | True | both_uncertified_absolute_materiality |
| R98-C2 | M-B/P-GRB | WIN | False | both_uncertified_absolute_materiality |

Materiality is unchanged: a_U=max(.001,.01*abs(U_control)), a_gap=max(.001,.10*abs(gap_control)), a_t=max(30,.10*t_control); complete certificates have priority. Cross-arm physical witnesses can revoke a source-scoped numerical claim but never replace an arm's own fleet.

## Mechanism exposure and full-solving cost

N40-R1-S: paid child certificates 4, own updates 11, strict termination requests 1, committed contractions 1, rebuilt MIPs 1.
Actual commit at producer process time 2629.416724s: [0,0.8064986407] to [0,0.4032493204], depth1; source call3; next actual Optimize calls [6, 9]. Full request/return/commit times, old scope/cutoff, own witness, complements and Start readback remain in the event journal and reconstructed tables.
F2: paid child certificates 4, own updates 3, strict termination requests 1, committed contractions 1, rebuilt MIPs 1.
Actual commit at producer process time 4.9101817s: [0,0.8853483009] to [0,0.4426741505], depth1; source call3; next actual Optimize calls [6, 9]. Full request/return/commit times, old scope/cutoff, own witness, complements and Start readback remain in the event journal and reconstructed tables.
R98-C2: paid child certificates 4, own updates 25, strict termination requests 1, committed contractions 1, rebuilt MIPs 1.
Actual commit at producer process time 69.866364s: [0,0.3916208967] to [0,0.1958104484], depth1; source call3; next actual Optimize calls [6, 9]. Full request/return/commit times, old scope/cutoff, own witness, complements and Start readback remain in the event journal and reconstructed tables.

Each candidate actually used one strict proof event and retained half its old interval. Own-update counts above include the initial incumbent; strict new counts are one less. The native call counts are P1, M-B5 (3LP+2MIP), MB-PC9 (6LP+3MIP) on every role; M-B has three distinct scoped model SHAs and MB-PC six.

| Role | Source proof registered | own U record | Termination requested | Real return | Atomic commit | New retained-root LP | Global L at commit |
|---|---:|---:|---:|---:|---:|---:|---:|
| N40-R1-S | 16.0131109 | 2629.355429 | 2629.355449 | 2629.416406 | 2629.416724 | 0.4789746698 | 0.5609817266 |
| F2 | 2.1041882 | 4.8955164 | 4.8955359 | 4.9098287 | 4.9101817 | 0.6105473608 | 0.7690075404 |
| R98-C2 | 11.205493 | 69.8394245 | 69.8394432 | 69.8659879 | 69.866364 | 0.1620054822 | 0.1887650441 |

These are actual C++ journal/event process timestamps. `mechanism_account.json` also binds next actual LP/MIP identities, the closed request record after model construction, externally observed producer-clock upper bounds, integer Y, original scope/cutoff, predicate margin and both old child bounds. Exact model-build start/API-entry and internal first discovery remain unknown. Every real requested stop returned INTERRUPTED before its transaction. Actual complete own Starts were submitted and checked on the new MIPs.
F2 complete-certificate production time is 150.9622661s versus M-B717.4892725s (ratio0.2104035166); this is an actual full proof benefit on a known role. N40 is an open TIE with slightly worse U/gap; R98-C2 is a severe LOSS against both controls. Every new retained-root LP reproduces its already paid old-left LP bound to the recorded precision. On N40 that is0.4789746698, only about0.000382452 above the original root LP0.4785922180 and below the inherited old MIP bound0.5609817266. The removed0.7875472937 is never treated as a new global bound.
The current traces cannot identify whether unhelpful removal, changed native branching/cuts/heuristics or rebuilding dominates a negative role. There is no extra counterfactual run. Old search-tree, local-cut and basis migration is not claimed. All rebuild/Start/LP/MIP costs are paid under one deadline. A paired endpoint change does not isolate an internal Gurobi cause; lost-tree cost and an unrun counterfactual cannot be measured by subtracting wall times.

## Admission, certification and resource closure

Development admission: {"complete_certificate_count_preserved": true, "material_WIN_or_additional_complete_certificate": true, "no_severe_P_regression_and_fewer_than_two_P_LOSS": false, "nonempty_contraction_and_subsequent_solve": true}.
All three E50-C1 positions are CANCELED_NOT_ADMITTED, unrun and not counted as completed.
This round did not close the V40 nonzero proof; its qualified U/L/gap remain open.
Nonrefundable solver/qualification accounting: 25/40 conservative starts, 23921.007995/48000 outer seconds; qualification 12/12 starts and 333.054728/2400 seconds.
qual01 retains the successful native chain and failed old MB-PC call-view wiring; the read-only fix reused sealed output without rerunning that slot. qual02 retains all three H100 positions and the recorded parent-shell exit upper bound. qual03 retains the finite two-contraction prefix and failed expected empty-fleet assertion; the corrected physical-tail test was not rerun, and pure physical mathematics/source review is separately labeled.
Qualification exit accounting excludes the long subsequent assistant idle interval using an original command-completion event; it does not change any producer, verification or total clock. Engineering/build/scan/export/restore costs are separate. Human elapsed effort is unknown, not zero.
formal01 retains all three successful sealed/verified arms and its failed group-summary attempt caused by a missing campaign-local cold-reference path. reader_repair01 was separately billed, copied only the existing frozen zero-Optimize exporter reference bytes, preserved the failed directory, and rebuilt the same three-arm summary without changing producer/reader bytes or rerunning a formal position.

## Evidence, delivery and limitations

Current reconstruction tables include own fleets/UB, target availability, actual call/model/scope/epoch/Start, LP and native ledger, physical rejection, cover, event records and all three clocks. `candidate_identity.json`, `pre_formal_freeze.json`, `argv_freeze.json`, `protocol.json` and fee receipts bind the positions and versions.
The successful native chain, finite physical native embeddings, pure mathematical completion, formal performance, subsequent empty-root reconstruction and separate extra review are distinct layers. The implementation author conducts the separate review process; no third-party native reproduction is claimed.
Named development/confirmation roles were already exposed. This is finite configuration evidence within V<=50, not geographic/Seed stability, statistical superiority or uniform P dominance. Standard bound pruning is not a new general theorem. No default promotion, merge, future grid or automatic research continuation follows this decision.
The current safe carrier contains only necessary current raw/source and small named safe authorities. Actual export/recovery, extra review and remote observations are recorded separately in `delivery/` and the delivery summary; these scientific records do not attest their own future commits or all Git history.
