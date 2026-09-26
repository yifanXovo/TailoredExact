Round87 left a mixed picture: ENS-C certified D6 much faster than P-GRB, while D7/U6/F5 remained censored and exposed primal/proof tradeoffs. Round88 tests a simpler startup and mathematically justified Gini/quantity refinements. **The outcome so far retains ENS-C's original 24+1 startup, parks both tested quantity-flow variants, and continues only a sparse formulation of the Gini strengthening. No candidate promotion or large long-run campaign has started.**

This is a stacked draft research PR against Round87 `0bf04b71268d6a39d127a8a692b6410b1b66edfb` / PR149. Work stays in the original `ExactEBRP` checkout; legacy local results are preserved. Explicit Sol high/xhigh selections were checked in runtime metadata. The formal-method restrictions exclude instance/history dispatch, internal time/Work slicing, hidden restart costs, and benchmark/tolerance changes. Whole-run diagnostic deadlines are external research censoring only.

## Startup ablation and complete-method screen

The default-off A1 switch applies the existing finite decoded descent only to ENS-C's verified joint constructive seed; physical closure and exact proof remain unchanged. Default ENS-C still uses 24 random starts plus that constructive seed. The qualified same-build P-GRB arm preserves the original baseline model and receives no candidate starts or cuts.

All 24 G3 runs pass physical/scope and cross-arm checks, with no retry or severe-signal stop. Process wall seconds for the smaller roles:

| Instance | P-GRB | ENS-C | A1 |
|---|---:|---:|---:|
| E8 | 1.891 | 2.750 | 2.765 |
| S12 | 6.312 | 1.953 | 1.562 |
| D3 | 597.141, uncertified | 153.797 | 153.531 |
| C2 | 597.109, uncertified | 122.344 | 124.109 |

The other entries in this table return original-problem numerical optimality certificates. These are single observations, not estimates of timing variability. On D7/U6/F5/F6 all three arms remain uncertified at their 1200-second whole-run cutoff. D7/F5 ENS and A1 endpoints match; F6 A1's absolute gap is slightly smaller (0.015460454 versus 0.016134134). U6 worsens materially: 0.030967676 versus 0.022362482, +38.48%, with a worse UB. This does not cross the preregistered severe-regression trigger, but does not justify a larger A1-only screen.

A separate D6 startup-only diagnosis takes 6.078s for ENS-C and 0.297s for A1, with UB worsening from 0.1575098036 to 0.1716116268; both have zero Optimize calls. The coordinator therefore retains the reference startup. The 18 larger G3 processes cost 16113.577s, plus 4.656s prelaunch and 5.594s separately recorded audit; the six smoke processes cost 17.233s. See [A1 decision](results/unified_exact_round88/a1_g3_decision.md) and [complete screen report](results/unified_exact_round88/runner_rest_report.md).

## Gini inequalities: valid strengthening, unresolved whole-method value

Independent proofs establish the inventory-CDF B1 transport inequality, its endpoint-conditioned B2 extension, and domain-local validity. The full B2 family implies B1 on a positive-width G domain; finite one-point row banks need not have that ordering. The isolated state/product-block minimum-cost result does not prove the full routing-model hull or novelty.

The initial 15 fixed-point LP arms and a six-arm shared-row-set test establish real relaxation strengthening. In the shared-row test, the 2,343-row union gives D7 parent/child values 0.1917810802 / 0.1943018267, but the parent solve alone costs 27.432s. Full formulation nesting is not established, and the child was historically rejected by ENS-C. Thus it is neither a retained tree gain nor evidence of faster convergence.

The subsequent nine repeated-separation diagnostics complete with 216 full LP rounds and total outside-command cost **1929.1104196s**:

| Fixed LP | Base value | Last B1 value | Last B2 value | Last combined value | Outcome |
|---|---:|---:|---:|---:|---|
| F2 root | 0.5286256495 | 0.5327745494 | 0.5327743944 | 0.5327745494 | no reliable new row |
| D7 root | 0.1859374766 | 0.1933707117 | 0.1933504902 | 0.1933529631 | each whole arm timed out at 300s |
| D7 child | 0.1859374766 | 0.1968399059 | 0.1968150425 | 0.1968050981 | each whole arm timed out at 300s |

These are the last completed numerical LP values under unchanged solver/residual conventions, without rational dual certificates. F2 still has positive candidates, including a B2 violation 0.000315 below its original reliability margin 0.000469; no closure is claimed. Six D7 arms have an unfinished Optimize after their last valid result, and all paid partial work is retained. No identity, numerical-rejection, existing-row violation or resource failure occurred. See [diagnostic report](results/unified_exact_round88/ot_closure_diagnostic_report.md), [independent review](results/unified_exact_round88/ot_closure_diagnostic_independent_review.md) and [decision](results/unified_exact_round88/ot_closure_decision.md).

The repeated-LP service is not admitted to ENS-C. One follow-up represents the same entire B1/B2 family with absolute-value epigraphs and shared sparse station prefixes. Elimination proves equal projection; B2 needs no redundant combined arm. This is distinct from historical station-local MC4/VD-J, but its extra matrix size may still hurt runtime. Only source/test preparation is currently admitted. See [sparse formulation proof](results/unified_exact_round88/ot_compact_epigraph_proposal.md).

## Quantity optimization and other reviewed mechanisms

A fixed-route integral min-cost circulation, full integer primitive-line search and original-C++ verifier adapter have exact finite-enumeration and residual-certificate checks. A toy proves an improvement outside the old single/pair neighborhood, but the three fixed D6/E8/S12 real witnesses show **no original-F improvement** for the fully linearized oracle.

The single admitted follow-up retains the entire convex separable penalty and linearizes only the local Gini term. Its six oracle tests include 216 independent inventory enumerations; its six adapter tests and one native importer qualification pass. All three real diagnoses complete in 1.6516373s total, with 14/14 original-C++ receipts valid and no accepted original-F decrease. E8 checks nine nonbaseline integer points. Negative proxy change does not imply descent of the original fractional objective. Both flow variants are parked without adding endpoints, seeds or tunable variants. See [composite report](results/unified_exact_round88/a2_composite_endpoint_diagnostic_001/report.md), [independent review](results/unified_exact_round88/a2_composite_endpoint_independent_review.md) and [decision](results/unified_exact_round88/a2_composite_endpoint_decision.md).

Reviewed split proposals establish midpoint product-error bounds and an LP-G point that maximizes a specified one-point row-violation measure; neither proves runtime improvement or finite termination of unrestricted unbalanced splitting. The depth audit corrects lost-buffering interpretations in U6/F5 rather than treating empty ledgers as no splits. A B3 history audit identifies a potential multi-event fleet-cover gap beyond pair cliques, while explicitly lacking full-model LP separation evidence. No split, branching or B3 candidate is integrated.

## Validation, evidence and next gate

A1 passes 11/11 focused CTest checks, the qualified source/binary identities, and all 19 input identity checks. The OT tools have independent exact-rational micro-oracles, original-model audits, separately enabled hand-computable Gurobi toys, and real Windows descendant cleanup. The final closure suite has seven passing pure tests and one explicitly gated toy; four toy Optimize calls and all eight qualification receipts cost 5.3059186s in total. Root and the xhigh reviewer separately check executable receipts, stopping boundaries and cost attribution. Source identities, every failed test/preparation attempt, negative results and partial work remain documented.

The 18 new G3 arms plus ledgers cover 34,147 source files / 667.72MB, packaged in 33 archives totaling 99.25MB; four deferred cross-preparation attempts occupy five further archives totaling 3.67MB. Every archive member is actually streamed and SHA/size checked; original raw directories remain intact. The new OT closure evidence covers 1,172 files / 1.145GB in 37 packages totaling 160.01MB, also with complete member read-back verification and independent root package-hash checks. Small composite-flow raw receipts are committed directly. Original raw files are preserved.

The active-path audit discloses the existing 50,000 support-row cap and top-8/top-6 compound decoder candidates. The declared two propagation rounds are not implemented as two rounds and are not cited as a mechanism. No frozen reference behavior is silently changed.

The goal remains active. Advancement requires useful complete-method evidence and regression protection, not only stronger LP bounds or completed diagnostics. Before any proposed mainline promotion and broad long convergence campaign, the user must receive the compiled, visually checked paper-style LaTeX/PDF method and actual instance comparisons, including censoring and costs. Stable defaults remain unchanged.