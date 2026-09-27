## Problem and proposed change

The fixed Round91 canonical-LP diagnostic found a processing-capacity relaxation gap on C2: its numerical original-F bound rose from 0.60266647 to 0.62264258 with two rounded travel/activation rows. D3 showed no objective gain. This PR prepares one uniform static row family for a later full-method test, without claiming that a root-bound gain makes MIP faster.

For each vehicle, the proposed row bounds total integer pickup by a proved processing allowance times binary depot activation. A directed shortest-route lower bound uses the same coefficients as the original canonical duration row. The pure helper computes outward numerical bounds and rounds the reliable quotient upper bound down to an integer; ambiguous exact-floor equality yields a conservative valid row, rather than a retry or an instance-specific algorithm choice. The design covers zero handling, no closed route, loaded return, coefficient serialization and unsupported arithmetic.

## Status and validation

The candidate is now **integrated in source and awaiting its first build/qualification**. A default-off CLI flag and isolated identity enable the canonical rows, an exact-key cache owned by one algorithm run, and a model-bound row ledger. The original ENS-C startup, AM, split depth, solver tolerances and control flow are preserved; A1, native B1 and LP-G combinations are rejected. The frozen Round90 executable remains unchanged. No test, model export or Optimize has yet run for Round92.

The [independent static review](results/unified_exact_round92/handling_activation_independent_static_review.md) accepts the integrated source for one finite zero-Optimize G1 qualification. Its prepared checks cover outward arithmetic, loaded-return pickup exceeding vehicle capacity, unsafe floating environments, cache identity, CLI rejection, the historical default-off LP SHA, and independent readback of the actual duration and added rows. The [plan](results/unified_exact_round92/plan.md) allows only one candidate and a finite subsequent screen. Default-off identity, exact coefficient/cache correspondence, unchanged original tolerances and complete costs remain required.

R7/R8/R63 related constraints and negative performance evidence are retained. This is an application of known rounding/activation reasoning, not a new general inequality theorem or a full routing-model convex hull. Round90 measurements keep their own frozen identity; there is no promotion or broad long campaign here.

## Paper preparation

Two source/evidence notes prepare the final paper without admitting extra experiments. The [controller termination note](results/unified_exact_round92/controller_termination_note.md) proves conditional finite requeue behavior for the audited default ENS-C path using the one-time frontier milestone and same-epoch child-LP cache, in addition to finite epochs and leaf IDs. Root checked the decisive predicates against the source; this does not prove native solve-time bounds or extend to unaudited optional variants. The [benchmark evidence map](results/unified_exact_round92/benchmark_evidence_blueprint.md) separates historical P-GRB runs from contemporary R90 pairs, preserves censoring and the D6 risk, and identifies the comparisons still needed for a final method.

## Completed Round90 follow-up

This stack also preserves the [remaining-nine G4 report](results/unified_exact_round90/g4_remaining_report.md), [independent evidence review](results/unified_exact_round90/g4_remaining_independent_evidence_review.md) and [whole-panel decision](results/unified_exact_round90/g4_panel_decision.md). All eighteen arms passed their audits. B50 improves from 1148.078s to 762.406s, while C20 worsens from 341.219s to 382.922s; C6/C8/S50 remain doubly censored. The fixed nineteen-role development panel is mixed, including the previously unresolved D6 loss of certification at 3600s. One new D6 pair at a common 7200s whole-run cap is in preparation, with no automatic extension or promotion. These are measurements of the frozen Round90 executable, not Round92 performance.

All 80,473 remaining-batch raw files (540,343,006 bytes) are retained locally and preserved in thirty member-verified packages (70,820,944 bytes). Root independently checked every package hash/size and the unique index totals. Archive command wall is 381.245s including one preserved adapter-only failed plan; the complete first-attempt-to-handoff interval is 624.854s. No solver was rerun for archival.
