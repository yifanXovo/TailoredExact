# Round67 — inventory-state encoding

Stage base: Round66 PR127, commit7c3b18912e16c66f9927ff71563fc25a9f488ff5.
Branch: codex/round67-log-inventory-states. Overall research goal remains unmet.
Stage complete. Draft PR128: https://github.com/yifanXovo/TailoredExact/pull/128 .
Implementation/evidence commit: 1aa398ef31d8de22bc62049ca08f3adad0affd09.

## Question and implemented change

Round66's arc-load replacement did not repair D6's actual P-GRB proof advantage.
This stage reopens Round55 VD-P under the current P-GRB-led objective, then
compares a logarithmic encoding of the same inventory-state disjunction. Old
Round55's D3 K1 regression is relevant protection evidence, not an automatic
per-point veto. No historical timing is used as a strict current pair.

VD-P uses one binary selector for each proved feasible integer inventory value
and a disaggregated Gini product. LOG leaves selectors continuous and links
their natural binary offset codes to ceil(log2(domain size)) binary variables.
An integral code forces one unique selector; unused patterns are infeasible.
Its original-variable feasible projection and LP projection equal VD-P's.
The latter projects stationwise to the ordinary McCormick rectangle hull.
See mathematics.md and lp_projection_attribution.md. These are explicit
component proofs and use established disjunctive/convexification ideas, not a
claim of new general theory or guaranteed runtime improvement.

The full paid HGA, original AM organization and native Gurobi MIP remain.
Presets research-round67-vdp and research-round67-log-vdp are default-off.
All ARC, VD-J, resource-budget, additional time/shared-resource and candidate
injection mechanisms are off. The current incumbent only supplies the usual
outer UB/cutoff; it is not submitted as a native Start. See algorithm.md for
the single uniform rule and unchanged logical AM parameters.

A preflight fixture exposed an inherited zero-handling domain defect. Both
domain paths now use capacity when handling is zero and travel permits a visit.
Loaded return and prefix capacity semantics remain unchanged. This correction
is separate from encoding performance, and all four arms are bound to the same
repaired build. The new presets explicitly reject unsupported nonmetric travel;
the inherited route-derived cuts are qualified here for symmetric metric data.
The floating-point metric screen is not a rational certificate of metricity.

## Matched development evidence

All four arms use Gurobi13.0.2, Threads1, Seed0, PresolveAuto, requested gaps0
and original numerical standards. P-GRB is the original compact model, native
defaults, no external starts/cuts/HGA/imported bounds. K1-R is canonical full
HGA plus verified candidate retention and immediate zero termination, without
the inadmissible Round65 budgets. Each complete run pays parsing, HGA, probes,
model construction, all native calls, validation and exit. Only the common
whole-run deadline interrupts an unfinished formal algorithm.

The final machine-readable end-state table is runs.csv; pairs.csv retains all
matched comparisons, including mixed UB/LB outcomes and signed discrepancies.
Practical thresholds were frozen before results in plan.md. They are neither
statistical significance claims nor automatic K1 per-instance vetoes.

- D4 at300: P remains open. K1-R certifies in128.938s, VD-P39.891s and LOG89.313s.
  Both encodings preserve this important P protection. LOG removes many binary
  selectors but is substantially slower than one-hot VD-P. All variants start
  from the same route witness; see d4_screen.md for full native costs.
- D6 at600: all remain open. Absolute gaps are P0.01225529, K1-R0.01374216,
  VD-P0.01226062 and LOG0.01751925. VD-P improves over K1 and nearly matches P's
  gap, with a better UB and weaker LB. This is not stable P superiority or a
  verified long-window repair. LOG is materially worse than P and K1. The paid
  HGA costs about320s; terminal MIP still has about270s. See d6_screen.md.
- D3 at300: all remain open. Gaps are P0.00347140, K1-R0.00115779,
  VD-P0.00318975 and LOG0.00263443. The encodings retain only12.2% and36.2% of
  K1's gap improvement over P. That loss of most existing protection is a
  serious goal-level problem even though their final gaps remain below P's.
  VD-P's UB is worse than P's; LOG has the best UB but a weaker LB than K1.
  Full HGA is only about2s, so this is not startup cost. See d3_screen.md.
- C2 at300: VD-P certifies in132.656s; P, K1-R and LOG remain open. Their gaps
  are0.05856223,0.03226622 and0.00330776. Both encodings improve this protection
  role, but LOG loses VD-P's certificate. Same initial physical witness,5 LPs,
  one mathematical target MIP and one terminal MIP in each K1 variant. See
  c2_screen.md. This positive result is a reason to continue VD-P development.

The stronger root LP on D3 did not translate to a better final proof. An
LP-gain-only rule would therefore not justify selecting this formulation.
Binary counts, LP bounds and nodes explain behavior but do not replace full
end-state comparisons. Historical D3 certification-tail ordering remains
unsettled by a300-second open run.

## Evidence qualification and cost

The tested binary SHA256 is
45e1ab05aff870660136102e554c8e0d3ec4cd5e1144dc651ebe9c111339a83e.
build_v1.json freezes source, driver, binary and test identity; machine.json
records the environment.44/44 CTests passed in1.77s after two disclosed
preflight failures. Six correctness micros all certify5/24 under the existing
numerical contract; the zero-handling LOG micro actually enters native MIP.
Six build-only original P-GRB exports cost0.376s and perform no optimization.
They match older fingerprints where comparable. See preflight_issue_1.md.

Post-experiment checks independently recompute original routes, operations,
inventory, load prefixes, allowed loaded return, travel/handling time and F.
They check native parameters, integrality restoration, initial Gini coverage
and every retained frontier/child obligation. No bad LB is silently clipped.
The offline witness-model audit additionally constructs every semantic column
of the initial witness in actual compatible LP artifacts and checks bounds,
types, objective and every linear row. Equal-capacity vehicle relabeling is
explicit and physically reverified; Gini-incompatible models are classified
as ineligible. This audit submits nothing to Gurobi and has zero optimizer calls.

All22 runs completed:16 performance and6 native micros,113 experiment optimizer
calls,5157.483s paid process wall, zero failures, within the declared6120s
worst-case experiment plan. No extra performance phase was opened. The final
offline mapping checked84 models:34 Gini-incompatible and50 feasible mappings,
404337 linear rows, maximum residual below6e-15, zero failures,3.907s and zero
optimizer calls.254 compact evidence artifacts were packaged and hashed.
Formal validation is included in paid process wall; build/CTest and additional
post-experiment QA are separately reported qualification costs. These are
numerical certificates plus algebraic component proofs, not strict rational
certification. Full raw logs/models/binaries remain local with paths/hashes;
compact ledgers, lossless trajectories, witnesses and reproduction scripts are
committed. Intermediate P native incumbent reports have no independently saved
vector at each event; never backdate the final verified witness into that trace.

## Stage decision and remaining target

Decision: retain both formulations as isolated research facilities,
do not adopt LOG or advertise either as the final unified algorithm. VD-P has
useful D4/C2 certifications and near-P D6 evidence, but D3 loses most K1
protection. LOG's D6 result is
a direct negative against the primary P-GRB objective. Neither repairs HGA
startup or establishes broad small-instance/nonzero CitiBike performance.
All current roles are development; no independent confirmation or3600/7200
extension has opened. Four development roles cannot establish generalization.
There is no per-point veto on VD-P: continue by addressing a concrete current
integration defect before a blind long-window expansion. Fresh unchanged VD-P
controls in the next stage will also recheck its large observed gains.

The next mechanism worth isolating is reuse of an already-paid complete
verified outer witness in the current native model, especially with VD-P's
state columns and LP/MIP model retention. D6's compatible HGA witness exists
in the actual models despite prolonged native incumbent absence; D3 also has
late native feasibility. This is an integration hypothesis, not a promised
proof improvement. Round44 already tested general starts with another
architecture; its dedicated D3 pair accepted none. The narrower current API
and mapping question is documented in provisional_integration_question.md
and gurobi_start_api_review.md. It cannot by itself solve startup cost, and
must preserve C2 behavior. The follow-up will isolate full existing-witness
Start integration with VD-P, subject to actual backend qualification and its
own declared bounded plan after this draft PR is saved. A complete future
candidate still needs independent confirmation and decisive common-budget
long runs; none are replaced by this development panel.
