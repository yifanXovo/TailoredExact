# Round 54 final report

Status: **round54_complete**. Every mandatory entered-stage row is present; gated stages that did not open have explicit empty ledgers and decisions. Draft stacked PR: https://github.com/yifanXovo/TailoredExact/pull/112.

## 1. Exact K1-AM-SF definition

K1-AM-SF is K1 Adaptive-Mass with Sparse Fixed-Interval Formulation, selected by `paper-k1-am-sf`. The outer tailored Gini-interval branch-and-cut framework uses K0=1, one complete strict-improver interval, midpoint refinement, adaptive-mass score with `tau=0.08`, unchanged native-target/exact-parent/child-infeasibility behavior, exact interval coverage, a monotone valid global lower bound, and strict original-problem certification. Its F0-CLEAN inner backend is Round 50 v0 with only the historical exhaustive V<=12 subset-duration block removed. Gurobi runs with Presolve Auto, Seed 0, Threads 1, zero MIP gaps, native branching, default PreCrush, and no dynamic user-cut callback.

## 2. Paper preset identity

Yes. `paper-k1-am-sf`, `k1-am-f0`, and `paper-k1-am-f0` canonicalize to the same Round 53 K1-AM-F0 semantics; the historical inner-policy alias remains accepted. Six required sentinels match settings, controller actions, interval endpoints, backend policy, objectives, bounds, and certificate class. Major, strong, V10, and numerical roles each have three matching model-file hashes. The bounded V20/V50 sentinels remained in heuristic startup and produced no model file; their evidence is command/controller/backend/outcome identity rather than a fabricated runtime fingerprint.

## 3--5. Round 53 P-GRB correction

The original 12 P-GRB rows lacked binding to a pre-frozen expected model fingerprint. Round 54 preserved every original artifact, verified the original official executable (`b49cc5a...`), froze all 12 expected fingerprints before correction, and required actual readback, valid lifecycle, independent original-solution checking, and objective recomputation. The corrected strict count is **9/12**, up from 0/12; the three M3 time-limit rows remain noncertificates. Work, process time, bounds, gaps, and GI did not change. No Round 53 F0 promotion conclusion changes.

## 6--8. Active, inactive, and contribution status

The 17 active families are: Gini interval domains; direct cap/floor; interval-tight G-times-binary hull; final-inventory penalty and movement-reachability domains; inventory conservation; visit--inventory linking; verified-incumbent cutoff; objective estimator; penalty closure; W_SP McCormick rows and estimator; pair/triple support-duration covers; connectivity flow; iterative propagation; and tight denominator bounds. The representative D1 model has 3,764 rows, 1,404 columns, 16,888 nonzeros, and zero exhaustive subset-duration rows.

Inactive families are the exhaustive subset-duration block, Gini-spread, required-movement, transfer-cutset, subset-inventory, dynamic support-duration, all tailored dynamic user cuts, inventory--route root closure, custom branching, and symmetry. The manifest classifies elements as standard or adapted. No active inequality is claimed novel; inventory--route novelty remains literature-review pending.

## 9. Documentation alignment

README, all required Markdown documents, and all requested manuscript sections now describe K1-AM-SF and its actual Gurobi boundary. Historical CPLEX/callback claims are removed from the current manuscript or explicitly labeled historical/contextual. The documentation audit passes 45/45 checks. The six-page manuscript compiles with zero final warnings and passes page-level visual QA.

## 10--11. Inventory--route proof and separator

For every nonempty station subset excluding the depot, IR-IN and IR-OUT bound net final-inventory displacement by capacity-weighted directed route entry/exit. Summed vehicle load conservation proves both mixed rows; valid interval inventory domains prove their projected companions. Separation is an exact deterministic directed maximum-closure/min-cut computation with explicit depot exclusion, direct violation recomputation, canonical signatures, duplicate/dominance handling, and deterministic tie-breaking. Fresh-model external root closure restores integer types and defaults before the terminal MIP; invalid closure falls back to F0. Dedicated tests pass all 35 checks.

## 12--16. Offline census and variants

IR1 (mixed full closure) and IR2 (mixed plus projected full closure) were run on all 34 frozen states, producing 68 complete rows. Each was valid everywhere, strictly violated in 33 structural roles, and improved the final root bound in 25 states. Each added 737 cuts over 470 closure rounds; aggregate closure Work was 3,632.783, solver time about 1,032.45 seconds for IR1 and 1,038.54 seconds for IR2, summed bound gain 0.846726, and maximum state gain 0.140600. IR2 gave no strict final-closure gain over IR1, so least-expansive IR1 was selected. IR3 (one pass) was predeclared but not opened because its overhead trigger did not occur. One implementation correction propagated the process deadline across closure rounds; all partial census evidence was invalidated and rerun before live selection.

## 17. Fixed-interval outcome

Stage A contains 28/28 engineering-valid rows: 14 F0-CLEAN and 14 IR1 rows at 300 seconds. F0 certifies 11/14; IR1 certifies 9/14; false certificates are zero. D4 is a material hard-state improvement, but IR1 loses F0 certificates on D1 and D13. F0 total Work is 3,461.075 versus IR1 3,555.762; IR1/F0 shifted Work GM is 1.089432. Aggregate GI worsens from 0.498349 to 0.623423. IR1 root closure adds 217 cuts, 96.087 Work, and 35.517 solver seconds over these 14 live rows. The frozen Stage-B gate fails.

## 18--20. K1 integration, major repair, and generalization

Because Stage A failed mandatory no-loss/no-severe/nonworse gates, fixed-interval Stage B, confirmation, and long checks did not open. K1-AM-SF-IR source was not created; K1 integration has 0 entered rows. Therefore no candidate controller run could alter or newly test the major repair; the stable K1-AM-SF repair remains unchanged by construction. The deterministic 4xV12/4xV20/4xV50 panel was generated and sealed before results, but its opening conditions were not met, so generalization and V50 extensions have 0 entered rows. The correct scale qualification is `generalization_panel_not_opened`.

## 21--25. Decision and remaining limits

There are two severe regressions, D1 and D13. K1-AM-SF remains the stable paper mainline (`k1_am_sf_stable_mainline`); K1-AM-SF-IR is not a supported future mainline candidate. Inventory--route strengthening is a bounded negative result: it improves root LPs but not total fixed-interval proof performance. The single next step is to stop this cut family and study a value-disaggregated G-times-Y formulation in a separate frozen round. Unproven items are: IR benefit under a materially different formulation, K1-level IR performance, new-panel V12/V20/V50 IR generalization, universal-scale validation, and literature novelty of the IR family.

## Final classifications

- Evidence: `round53_pgrb_recertified`
- Mainline: `k1_am_sf_mainline_frozen`
- Documentation: `documentation_fully_aligned`
- Separator: `inventory_route_separator_complete`
- Strengthening: `bounded_negative_inventory_route_strengthening`
- Algorithm: `k1_am_sf_stable_mainline`
- Scale: `generalization_panel_not_opened`

Official comparator/candidate executable SHA-256: `55ac7778f8e4a1c009b6d1cc8c4cc5d3b40a54ac241cce5a633363a0a571f441`. Stable paper executable SHA-256: `a08ae3a92483a255593ec22ad6ab6b493db0c598f867c8c0e7d186e1b34a75fc`. Official source freeze: `b6784e930f5df3b8bb048e7572301f942c017cd0`. Packaging snapshot before final binding: `2072043d484f9d330569aae41534ea48f4300667` (tree `eeacfd69e46cdd3ed04afd455c86d51adcb6412d`).
