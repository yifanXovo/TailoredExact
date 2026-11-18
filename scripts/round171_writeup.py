"""Translate qualified results into the finite decision and current component paper."""

import argparse
import re

from round170_common import result
from round171_common import OUT, ROOT, bind, read, utc, write

PAPER = ROOT / "results/unified_exact_round137"
SOURCES = {"CITI": "CITI", "CABI": "CABI", "DIVVY": "Divvy"}
TOL = 1e-7


def table(head, records):
    return "\n".join(["| " + " | ".join(head) + " |",
                      "| " + " | ".join("---" for _ in head) + " |"]
                     + ["| " + " | ".join(str(item) for item in row) + " |" for row in records])


def f(value, places=6):
    return f"{value:.{places}f}" if value is not None else "—"


def percent(value):
    return f(100 * value, 2) if value is not None else "—"


def prose(path, text, preserve_newlines=False):
    newline = "\r\n" if preserve_newlines and path.is_file() and b"\r\n" in path.read_bytes() else "\n"
    path.write_bytes(((text.rstrip() + "\n").replace("\n", newline)).encode("utf-8"))


def find_paper(panel):
    return f"{SOURCES[panel['source']]} {panel['geometry']}"


def cases():
    positions = read(OUT / "complete_arms.json")
    pairs = read(OUT / "comparison_BP.json")["rows"]
    inputs = read(OUT / "input_manifest.json")["roles"]
    activity = read(OUT / "activity.json")["runs"]
    assert positions["qualified"] == 12 and len(pairs) == len(inputs) == 6
    return positions["rows"], pairs, inputs, activity, read(OUT / "cost_report.json")


def results_summary(arms, pairs, activity):
    stats = {
        "certificate": {arm: sum(r["certificate"] for r in arms if r["arm"] == arm) for arm in ("B", "P")},
        "feasible": {arm: sum(r["qualified_feasible_U"] for r in arms if r["arm"] == arm) for arm in ("B", "P")},
    }
    for m in ("U", "L", "absolute_gap"):
        stats[m] = {side: sum(p[f"material_B_{m}"] == "favors_" + side for p in pairs) for side in ("B", "P")}
        stats[m]["within_delta"] = sum(p[f"material_B_{m}"] == "difference_within_delta" for p in pairs)
    stats["relative_gap_lower_B"] = sum(p["delta_relative_gap"] is not None and p["delta_relative_gap"] < 0 for p in pairs)
    stats["joint_U_L_abs_gap"] = sum(all(p[f"material_B_{m}"] == "favors_B" for m in ("U", "L", "absolute_gap")) for p in pairs)
    stats["joint_cert"] = sum(p["certificate_comparison"] == "both_CERT" for p in pairs)
    stats["double_open"] = sum(p["certificate_comparison"] == "both_OPEN" for p in pairs)
    stats["B_lower_U_roles"] = [p["role"] for p in pairs if p["material_B_U"] == "favors_B"]
    stats["P_lower_U_roles"] = [p["role"] for p in pairs if p["material_B_U"] == "favors_P"]
    stats["B_higher_L_roles"] = [p["role"] for p in pairs if p["material_B_L"] == "favors_B"]
    stats["P_higher_L_roles"] = [p["role"] for p in pairs if p["material_B_L"] == "favors_P"]
    stats["B_split"] = sum(r["accepted_splits"] for r in activity if r["arm"] == "B")
    stats["B_decline"] = sum(r["declined_splits"] for r in activity if r["arm"] == "B")
    stats["B_child_target_MIP"] = sum(r["child_target_MIP_calls"] for r in activity if r["arm"] == "B")
    stats["B_requeue"] = sum(r["child_target_parent_requeues"] for r in activity if r["arm"] == "B")
    stats["B_H_to_final_material"] = sum(
        (r["initial_U"] - r["U"]) > TOL for r in arms if r["arm"] == "B"
    )
    stats["B_root_available"] = sum(r["initial_root_global_L"] is not None for r in arms if r["arm"] == "B")
    stats["B_root_L_to_final"] = sum(
        r["L"] - r["initial_root_global_L"] > TOL for r in arms if r["arm"] == "B" and r["initial_root_global_L"] is not None
    )
    stats["B_LP_total"] = sum(r["LP_native_seconds"] for r in arms if r["arm"] == "B")
    stats["B_MIP_total"] = sum(r["MIP_native_seconds"] for r in arms if r["arm"] == "B")
    stats["B_availability_advantage"] = [p["role"] for p in pairs if p["feasibility"] == "B_only_feasible"]
    stats["P_availability_advantage"] = [p["role"] for p in pairs if p["feasibility"] == "P_only_feasible"]
    return stats


def describe(stats):
    return (f"B returned a qualified fleet on {stats['feasible']['B']}/6 configurations and P on "
            f"{stats['feasible']['P']}/6. At the prespecified descriptive scale, B had a lower U in "
            f"{stats['U']['B']}/6 pairs, a higher global L in {stats['L']['B']}/6 and a smaller "
            f"absolute gap in {stats['absolute_gap']['B']}/6. The corresponding counts for P were "
            f"{stats['U']['P']}/6, {stats['L']['P']}/6 and {stats['absolute_gap']['P']}/6. "
            f"B certified {stats['certificate']['B']}/6 and P {stats['certificate']['P']}/6, with "
            f"{stats['double_open']}/6 joint OPEN and {stats['joint_cert']}/6 joint CERT pairs.")


def controller_sentence(stats):
    return (f"The B controller accepted {stats['B_split']} splits and declined {stats['B_decline']}. "
            f"Its {stats['B_child_target_MIP']} child-bound-target MIP phases requeued the parent "
            f"{stats['B_requeue']} times. The unchanged full/root controls leave the controller's "
            "independent net benefit unresolved.")


def cost_sentence(fees):
    return (f"The producer clocks sum to {fees['process_outer_seconds']:.2f} s. "
            f"The {fees['H_calls']} own H calls took {fees['H_seconds']:.2f} s, and "
            f"{fees['actual_Optimize']} Optimize calls ({fees['LP']} LP and {fees['MIP']} MIP) "
            f"recorded {fees['Native_seconds']:.2f} Native s. "
            f"The six zero-Optimize references took {fees['qualification_outer_seconds']:.2f} s including static checks. "
            f"Successful independent post-return readers cost {fees['audit_seconds']:.2f} s "
            f"({fees['all_actual_audit_attempt_seconds']:.2f} s across all reader attempts).")


def paired_table(pairs):
    return table(
        ("Configuration", "B / P state", "B / P U", "B / P L", "B / P absolute gap",
         "B / P gap %", "B / P process s", "B / P audit s", "Cert. ratio"),
        [(p["role"], f"{p['B_state']} / {p['P_state']}",
          f"{f(p['B_U'])} / {f(p['P_U'])}", f"{f(p['B_L'])} / {f(p['P_L'])}",
          f"{f(p['B_absolute_gap'])} / {f(p['P_absolute_gap'])}",
          f"{percent(p['B_relative_gap'])} / {percent(p['P_relative_gap'])}",
          f"{f(p['B_process_outer_seconds'],3)} / {f(p['P_process_outer_seconds'],3)}",
          f"{f(p['B_audit_seconds'],3)} / {f(p['P_audit_seconds'],3)}",
          f(p["B_over_P_T_cert_process"], 4))
         for p in pairs])


def native_objective_disclosure(arms):
    disclosures = []
    for arm in arms:
        if arm["arm"] != "P" or arm["U"] is None:
            continue
        returned = result(ROOT / arm["raw_result"]["path"])
        if returned["verified_incumbent_objective_consistent"]:
            continue
        native = returned["gurobi_obj_val"]
        gap = native - arm["U"]
        disclosures.append(
            f"Cold P on {arm['role']} has Native ObjVal {native:.9f} and a separately verified physical U of "
            f"{arm['U']:.9f} (Native minus physical {gap:.2e}). Its incumbent consistency flag is false. "
            f"The OPEN comparison uses the physical U and the same run's qualified global L of {arm['L']:.9f}."
        )
    return "\n\n".join(disclosures)


def write_reports(arms, pairs, inputs, activity, fees, stats):
    by_arm = fees["by_arm"]
    rel = "Both objective comparisons and the cost ledger use each arm's own evidence."
    time_note = ("Joint certificates are compared on the original objective and outer process time."
                 if stats["joint_cert"] else "Certificate-time comparisons had an empty joint-CERT subset.")
    clock_issue = "Gross elapsed, occupied scientific time and ordinary publication I/O are recorded in the closeout receipts."
    report = f"""# Frozen GI-TBC on six positive n50 configurations

{describe(stats)} B reduced relative gap in {stats['relative_gap_lower_B']}/6 pairs and jointly improved U, L
and absolute gap at the descriptive scale in {stats['joint_U_L_abs_gap']}/6. {time_note} {rel}

{paired_table(pairs)}

The gap percentage is 100 times the nonnegative display gap divided by
the arm's own U. The signed gap and full-precision values are in the
arm table. A dash means the reported quantity was unavailable or
inapplicable. OPEN durations are budget outcomes and certificate times
are reserved for qualified certificates.
{native_objective_disclosure(arms)}
[Complete arms](complete_arms.csv) · [Matched differences and costs](comparison_BP.csv)

## Paid work and observable bottlenecks

{cost_sentence(fees)} Native LP and MIP work consumed
{fees['LP_native_seconds']:.2f} s and {fees['MIP_native_seconds']:.2f} s, respectively.
Native MIP accounts for {100 * fees['MIP_native_seconds']/fees['process_outer_seconds']:.2f}% of the total
producer clock. The unresolved gaps persist after this paid search.
B's recorded strengthened-model construction used {fees['B_all_reported_build_seconds']:.2f} s and
its imports used {fees['B_all_reported_model_import_seconds']:.2f} s. P's
combined pre-Optimize phase used {by_arm['P']['pre_first_optimize_seconds']:.2f} s
across the six arms. The frozen P trace has a combined pre-Native timer.
The final raw Optimize-return marker precedes the qualified journal tail.
The total return-marker-to-tail interval is {fees['return_marker_to_qualified_tail_seconds']:.3f} s.
The remaining tail-to-exit interval is {fees['qualified_tail_to_exit_seconds']:.3f} s.
These timers include evidence handling and finalization. {clock_issue}

B improved its own H incumbent during the paid exact phase on
{stats['B_H_to_final_material']}/6 arms (difference greater than the inherited numerical tolerance).
The root LP yielded a qualified original global L on
{stats['B_root_available']}/6. Subsequent proof raised it on {stats['B_root_L_to_final']}/6.
{controller_sentence(stats)} Endpoint movement and time attribution are
descriptions of this lifecycle. The different model, cutoff and startup
can all change Native search.
[Initial proof scope and actual controller activity](activity.json) · [Costs](cost_report.json)

## Scope

All six generated inputs were included with Seed 0, one thread, three
heterogeneous capacities and the 1,200-s complete-process budget.
Each arm used the same frozen PE and DLL. Each B independently paid for
one full H. P was built separately in its original compact domain with
zero submitted starts. The calibrated T1 route horizon is an input
property. History and archived source-row overlap remain linked.
[Research design](research_design.md) · [Input manifest](input_manifest.json)

The observations extend direct complete-method evidence to six
positive-target configurations at n=50. Their archive-based, synthetic
operational data and single solver Seed delimit the claim. The retained
n15/20/35 evidence answers separate questions. B remains the uniform
main method and C166, D167 and fixed C169 remain off.
[Finite research decision](research_decision.md)
"""
    prose(OUT / "final_report.md", report)
    favourable = ("The endpoint advantage is consistent across these six configurations."
                   if stats["joint_U_L_abs_gap"] == 6 else
                   "The finite evidence is mixed across endpoint metrics or configurations."
                   if stats["U"]["B"] or stats["L"]["B"] or stats["absolute_gap"]["B"] or stats["B_availability_advantage"] else
                   "The finite panel did not retain a material B advantage on the common measured endpoints.")
    decision = f"""# Research decision

{favourable} {describe(stats)} {time_note}

B's six producer clocks total {by_arm['B']['process_outer_seconds']:.2f} s and
P's total {by_arm['P']['process_outer_seconds']:.2f} s. B pays
{fees['H_seconds']:.2f} s for six independent full H calls. Native MIP
dominates the costs, at {100 * fees['MIP_native_seconds']/fees['process_outer_seconds']:.2f}%
of the joint producer clock. The panel's OPEN durations describe
resource use at the common cap.

The transport-method case for EJOR/TRE connects the shared
inventory/service/product formulation to complete feasible routing,
paid exact control and bounded transportation decisions. The direct
computational scope now covers the six archived-source n50 shortage
configurations at a common 1,200-s cap. The existing resource and weight
comparisons carry their original denominators. The new single-Seed panel
adds finite endpoint evidence under combined changes in station set,
geometry and the input-based horizon. Larger-scale behavior, stability
across Native Seeds and out-of-sample operations remain open.

{controller_sentence(stats)} The activity exposes the existing
true-G coverage, bound progression and Native search. It has not
supplied a new mathematical object or falsifiable cross-problem
prediction beyond the local and conditioned representation, route-family,
and full/root questions already investigated. There is no supported
new OR mechanism to price or execute from this panel.

B stays uniform. The outcome closes the prospective validation question
for this finite panel and leaves the existing candidate decisions in force.
"""
    prose(OUT / "research_decision.md", decision)
    memo = f"""# Author decision on the current manuscript

{describe(stats)}

Keep the integrated GI-TBC/transportation decision position for EJOR/TRE.
The updated computational section shows the n50 evidence alongside the
existing breadth, resource, weight and adverse candidate observations.
Use the feasible U, qualified L and gap endpoints to specify the scope.
The OR positioning still depends on a distinct transferable structural
claim. The interval and Native traces in this panel support a process
description and leave that research gate unresolved. The existing
manuscript is the deliverable for this round.
[Decision and boundary](research_decision.md)
"""
    prose(OUT / "author_decision_memo.md", memo)
    write(OUT / "decision.json", dict(UTC=utc(), stats=stats, uniform_B=True,
                                      C166_D167_C169_off=True, new_OR_mechanism=False,
                                      round_complete_on_this_panel=True))


def short_run(arm):
    return f"{arm['position']:02d} / {arm['arm']}"


def supplement_text(arms, inputs, activity, fees):
    input_table = table(
        ("Configuration", "Archive / geometry", "T (s)", "Omega", "lambda", "Shortfall", "F floor (approx.)"),
        [(p["id"], find_paper(p), p["T_seconds"], f(p["Omega"]), p["lambda_decimal17"], p["shortage"],
          f(p["positive_objective_floor_decimal"], 8)) for p in inputs])
    endpoints = table(
        ("Run", "State", "Own H F", "Final U", "Qualified L", "Signed U-L", "Gap %", "Cert. s", "Process s", "Audit s"),
        [(short_run(a), a["state"], f(a["initial_U"]), f(a["U"]), f(a["L"]), f(a["signed_absolute_gap"], 8),
          percent(a["relative_gap"]), f(a["T_cert_process"], 3), f(a["process_outer_seconds"], 3), f(a["audit_seconds"], 3))
         for a in arms])
    paid = table(
        ("Run", "Rows", "Cols", "H s", "Build s", "First launch s", "LP s", "MIP s", "After Native s", "Work", "Nodes"),
        [(short_run(a), a["first_model_rows"], a["first_model_columns"], f(a["H_seconds"], 3),
          f(a["all_recorded_model_build_seconds"], 3), f(a["pre_first_optimize_seconds"], 3),
          f(a["LP_native_seconds"], 3), f(a["MIP_native_seconds"], 3), f(a["post_last_optimize_seconds"], 3),
          f(a["Work"], 1), f(a["nodes"], 0)) for a in arms])
    controller = table(
        ("Configuration", "Initial root L", "Final L", "Root/child LPs", "Root/child LP s",
         "Accepted / declined", "Peak leaves", "Target MIPs / requeues"),
        [(a["role"].removeprefix("R171-"), f(a["initial_original_global_L"]), f(a["final_L"]),
          f"{a['parent_LP_calls']}/{a['child_LP_calls']}",
          f"{f(a['parent_LP_seconds'], 2)}/{f(a['child_LP_seconds'], 2)}",
          f"{a['accepted_splits']}/{a['declined_splits']}", a["maximum_live_coverage_leaves"],
          f"{a['child_target_MIP_calls']}/{a['child_target_parent_requeues']}")
         for a in activity if a["arm"] == "B"])
    return rf"""
## S171 Prospective positive n50 configurations

The precommitted generation draws one compact and one regional 50-station
selection per archive, with four original hash/farthest anchors and a
nearest-100 regional pool. The selections within a source are disjoint.
CITI and CABI use UTM 18N and Divvy uses UTM 16N. Archive coordinates and
capacities support the spatial cases. Depot, stock, targets and weights
have synthetic or transformed values. The unchanged shortage generator,
serialized bytes, original row mapping and historical identity scope are
in the input ledger. The vehicles have capacities 20, 25 and 30. The original
problem uses empty departures, at most one nonzero directed service per station,
prefix capacity, loaded return and paid unloading, with speed 1.5 m/s
and pickup and drop each 60 s/unit.

Each input uses \(T=T_1\) under §4.1 and \(\lambda=1/\Omega\), where
\(\Omega=\sum_i\omega_i\) excludes the depot. With \(s=\sum_i D_i-\sum_i b_i>0\)
and \(a=\min_i \omega_i/D_i>0\), conservation gives
\(P\ge a\sum_i|D_i-Y_i|\ge as\), hence \(F\ge\lambda as>0\).
These serialized-data bounds certify positivity for the design. The
optimization arms use their frozen proof sources. Input horizons and
the 1,200-s complete-process clock are distinct quantities.

**Table S171.1. Input-derived settings and positivity.**

{input_table}

Each block is run serially at Native Seed 0 and one thread, alternating
B then P and P then B. B pays for complete own H with seed 20260626
before exact search. P uses the original compact model and zero user
starts, retaining Gurobi's default heuristics. Each P Optimize matches
its own zero-Optimize reference. Each B publishes model, own Start,
Native log and proof coverage readbacks. The C++ budget starts at
process entry and allocates each actual Optimize the remaining work
window. The 6-s shutdown allowance is part of the cap.
[Input and provenance ledger](../unified_exact_round171/input_manifest.json) ·
[Matrix](../unified_exact_round171/matrix_frozen.json)

**Table S171.2. All 12 qualified arm endpoints and external clocks.**

{endpoints}

The process clock owns preparation, H, build, Start mapping, all
Native calls and runtime validation. T_cert is the outer process clock
of the qualified CERT arm. Independent post-return audit is separate.
Run labels give the frozen matrix position and arm. The two consecutive
positions for each configuration follow the order in Table S171.1.
The complete ledger carries the full run ID.
The signed U-L retains numerical sign, while the display percentage uses
the nonnegative gap convention. Missing values are shown with a dash.

{native_objective_disclosure(arms)}

**Table S171.3. Recorded work inside the paid clocks.**

{paid}

Rows and columns refer to the first actual Optimize model. B build
seconds are summed over recorded canonical model construction. For P,
first launch includes preparation, export, environment, import and model
validation together. The post-Native interval begins at the raw final
Optimize-return publication in the C++ journal. It includes subsequent
checked-evidence publication and process finalization. The machine table
retains the later qualified tail and the two disjoint intervals.
Costs are nested in the process clock. {cost_sentence(fees)}

**Table S171.4. Interval activity on the six B arms.**

{controller}

Root L reaches the original problem only with an eligible returned LP,
qualified cutoff complement and complete improving-Gini root scope.
The configuration IDs in this activity table omit the R171 prefix.
Descendant LP counts include probes. Coverage leaves are unreplaced
intervals and can be discharged. The exact distribution of accepted
splits, targets and requeues follows the saved events. These observations
leave the independent performance effect of external interval treatment
unresolved.
[Full costs](../unified_exact_round171/cost_report.json) ·
[Activity ledger](../unified_exact_round171/activity.json) ·
[Arm and audit identities](../unified_exact_round171/complete_arms.json)
"""


def refine_scope(body, app, supplement):
    body = body.replace(
        "Ten new draws in total include four additional shortage bases",
        "The ten new draws in the breadth and resource studies include four additional shortage bases", 1,
    )
    app = app.replace("the resource panel fixes \\(\\rho=1\\)",
                      "the resource and prospective n50 panels fix \\(\\rho=1\\)", 1)
    candidate = ("Close further optimization of the fixed C169 recipe. Preserve its correctly paid complete-H initialization improvements and the B35/X35 Seed 1 primal positives as local research findings, together with every adverse U/L/gap and C20 time result. Do not promote it as a candidate confirmed across these two additional Native Seeds. B/GI-TBC remains uniform default and C166/D167/C169 remain default off. This closes this recipe without adding weights, H seeds, a third Native Seed, longer caps, new neighborhoods or a successor round.")
    supplement = supplement.replace(candidate, (
        "The two additional Native Seeds did not confirm the fixed C169 recipe as a complete-method improvement. "
        "The paid complete-H initialization and B35/X35 Seed 1 primal gains remain local findings alongside "
        "the adverse U/L/gap and C20 timing results. B/GI-TBC remains uniform. C166, D167 and C169 remain off."
    ), 1)
    return body, app, supplement


def manuscript(arms, pairs, inputs, activity, fees, stats):
    body_path = PAPER / "paper_body.md"
    app_path = PAPER / "model_and_algorithm_appendices.md"
    supplement_path = PAPER / "supplement.md"
    body = body_path.read_text(encoding="utf-8-sig")
    app = app_path.read_text(encoding="utf-8-sig")
    supplement = supplement_path.read_text(encoding="utf-8-sig")
    assert "### 4.7" not in body and "## S171 " not in supplement
    body, app, supplement = refine_scope(body, app, supplement)
    declarations = re.compile(r"\bTable (8|9|10|11)\b")
    body = declarations.sub(lambda m: f"Table {int(m[1])+1}", body)
    app = declarations.sub(lambda m: f"Table {int(m[1])+1}", app)
    body = body.replace(
        "Seed checks retain open and adverse endpoints.",
        f"Seed checks retain open and adverse endpoints. In six prospective positive-target n50 pairs at a 1,200-s cap, "
        f"GI-TBC has materially lower feasible objectives in {stats['U']['B']}/6 and higher qualified global bounds "
        f"in {stats['L']['B']}/6, with {stats['certificate']['B']}/6 certificates versus {stats['certificate']['P']}/6 for cold P.",
    )
    body = body.replace("For each new resource base, let", "For each resource base and prospective n50 configuration, let", 1)
    body = body.replace(
        "Within each T pair, every datum except T is identical.",
        "Within each T pair, every datum except T is identical. The n50 comparison takes T1 alone and compares B and P within each generated configuration.",
        1,
    )
    body = body.replace(
        "| Compact shared-state comparison | 6 exposed inputs / 12 fresh same-build B/C166 Seed0 arms | Equivalent common LP information and complete-method costs |",
        "| Compact shared-state comparison | 6 exposed inputs / 12 fresh same-build B/C166 Seed0 arms | Equivalent common LP information and complete-method costs |\n"
        "| Prospective positive n50 | 6 new configurations / 12 B/P Seed0 arms | Complete paid endpoints at 1,200 s |",
        1,
    )
    old = ("Close further optimization of this fixed recipe. Retain its initialization and local paid positives as bounded findings, "
           "with B remaining uniform default and C169 default off; this selected exposed-input study does not confirm a repeatable complete-method benefit.")
    new = ("The exposed-input confirmation supports a local initialization finding and closes the fixed reweighting line. "
           "GI-TBC/B remains the uniform default, with C169 disabled.")
    assert body.count(old) == 1
    body = body.replace(old, new)
    old = "Preserve these mixed and adverse findings and close the C169 optimization line."
    assert body.count(old) == 1
    body = body.replace(old, "The fixed reweighting recipe is closed after this mixed confirmation.")
    main_table = table(
        ("Archive / geometry", "B U / L", "P U / L", "B / P gap %", "B / P state"),
        [(find_paper(q), f"{f(p['B_U'])} / {f(p['B_L'])}", f"{f(p['P_U'])} / {f(p['P_L'])}",
          f"{percent(p['B_relative_gap'])} / {percent(p['P_relative_gap'])}", f"{p['B_state']} / {p['P_state']}")
         for q, p in zip(inputs, pairs, strict=True)])
    if stats["joint_cert"]:
        cert_text = "The joint-CERT ratios use T_cert_process from the independently qualified arms (Supplement S171)."
    else:
        cert_text = "The joint-CERT subset is empty. The OPEN endpoints quantify progress at the common budget."
    insert = rf"""### 4.7 Prospective positive n50 endpoint evidence

Six precommitted shortage configurations use 50 stations, three vehicles
of capacities 20, 25 and 30, and one compact and one regional geometry
from each of CITI, CABI and Divvy. The draws use archived station
locations and capacities, with synthetic or transformed operational
inputs. Each configuration uses \(\rho=1\) and its own \(T_1\). Positive
shortage and weights bound the original objective away from zero.
The single Seed 0 comparison gives each complete process 1,200 s,
including B's own H. Each arm is independently qualified. All six inputs
enter without performance screening (Supplement S171).

**Table 8. Qualified B and cold P endpoints on the prospective n50 configurations.**

{main_table}

{describe(stats)} {cert_text} B spent {stats['B_MIP_total']:.1f} s in Native MIP and {stats['B_LP_total']:.1f} s in LP calls across the six arms.
{controller_sentence(stats)} The archived-source n50 observations
extend the direct coverage of the integrated pair-only method. The
comparisons are conditional on these geometries, physical horizons
and synthetic operational quantities.

"""
    anchor = "## 5. Certified transportation decisions"
    assert body.count(anchor) == 1
    body = body.replace(anchor, insert + anchor)
    conclusion = (f"The prospective n50 comparison adds six direct tests of the frozen complete method. "
                  f"B's material U, L and absolute-gap advantages occur in {stats['U']['B']}/6, "
                  f"{stats['L']['B']}/6 and {stats['absolute_gap']['B']}/6 pairs, with "
                  f"{stats['certificate']['B']}/6 B and {stats['certificate']['P']}/6 P certificates. "
                  "These archived-source shortage results bound the evidence at one solver Seed and one paid cap. "
                  "The controls leave independent external scheduling gains and a general scalability claim unresolved.")
    body = body.rstrip() + "\n\n" + conclusion
    prose(body_path, body, preserve_newlines=True)
    prose(app_path, app, preserve_newlines=True)
    prose(supplement_path, supplement + supplement_text(arms, inputs, activity, fees), preserve_newlines=True)
    write(OUT / "manuscript_change_record.json", dict(
        UTC=utc(), current_folder=PAPER.relative_to(ROOT).as_posix(), body=bind(body_path),
        appendices=bind(app_path), supplement=bind(supplement_path), references=bind(PAPER / "references.bib"),
        new_main_section="4.7", new_main_tables=1, supplement_section="S171",
        historical_Table_8_through_11_shifted_by_one=True, explicitly_kept_old_adverse_evidence=True,
    ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["reports", "manuscript"])
    args = parser.parse_args()
    arms, pairs, inputs, activity, fees = cases()
    stats = results_summary(arms, pairs, activity)
    if args.stage == "reports":
        write_reports(arms, pairs, inputs, activity, fees, stats)
    else:
        manuscript(arms, pairs, inputs, activity, fees, stats)
