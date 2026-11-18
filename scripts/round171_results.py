"""Build the endpoint, activity, cost and master-CSV tables from qualified returns."""

import argparse
import csv
import io
import math
from pathlib import Path

from round170_common import result
from round170_results import table_csv
from round171_common import (
    BASE, CAP, DLL_SHA, MASTER, MASTER_BASE_BYTES, MASTER_BASE_SHA, MEASURED, OUT,
    PE_SHA, REL, ROOT, TEMP, bind, blob, clock, digest, git, read, sha, utc, write,
)

MATRIX = OUT / "matrix_frozen.json"
MANIFEST = OUT / "input_manifest.json"
INCREMENT = OUT / "GI_TBC_R171_B_increment_28col.csv"
BEGINNING = "2bf623c537ec363a9d6eb13c9ab0496d074d9c47"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def interval_activity(directory, audit, returned):
    details = directory / "external"
    ledger = rows(details / "paper_optimize_ledger.csv")
    lp = [row for row in ledger if row["solve_kind"] == "LP"]
    mip = [row for row in ledger if row["solve_kind"] != "LP"]
    assert len(ledger) == len(lp) + len(mip) == audit["actual_Optimize"]
    assert len(lp) == audit["LP"] and len(mip) == audit["MIP"]
    targets = rows(details / "native_target_ledger.csv")
    child_targets = [row for row in targets if row["target_kind"] == "child_disjunction"]
    assert len(child_targets) == returned["external_gini_tree_child_bound_target_phase_count"]
    requeues = sum(int(row["requeued"]) for row in child_targets)
    assert requeues <= returned["external_gini_tree_native_requeue_count"]
    accepted = returned["external_gini_tree_split_count"]
    declined = returned["external_gini_tree_declined_split_count"]
    initial_leaves = returned["external_gini_tree_initial_leaf_count"]
    live = audit["qualified_cover"]["live_leaves"]
    coalesced = returned.get("round42_sibling_pairs_coalesced", 0)
    if not coalesced:
        assert live == initial_leaves + accepted, "Coverage leaf accounting needs reconciliation"
    parent = [row for row in lp if row["leaf_id"] == "L0"]
    child = [row for row in lp if row["leaf_id"] != "L0"]
    return dict(
        ledger=ledger, LP_seconds=sum(float(row["solver_runtime"]) for row in lp),
        MIP_seconds=sum(float(row["solver_runtime"]) for row in mip),
        Work=sum(float(row["work"]) for row in ledger),
        nodes=sum(float(row["nodes"]) for row in ledger),
        parent_LP_calls=len(parent), child_LP_calls=len(child),
        parent_LP_seconds=sum(float(row["solver_runtime"]) for row in parent),
        child_LP_seconds=sum(float(row["solver_runtime"]) for row in child),
        LP_count_scope="Actual root L0 and descendant LP calls, including child probes.",
        accepted_splits=accepted, declined_splits=declined, coverage_leaf_count_initial=initial_leaves,
        coverage_leaf_count_terminal=live, maximum_live_coverage_leaves=live if not coalesced else None,
        coverage_leaf_count_scope="Unreplaced coverage leaves, including discharged ones. Peak follows final count when no coalescence occurs.",
        open_leaves_terminal=audit["qualified_cover"]["open_leaves"], coalesced_sibling_pairs=coalesced,
        child_target_MIP_calls=len(child_targets), child_target_parent_requeues=requeues,
        child_target_MIP_seconds=sum(float(row["solver_runtime"]) for row in child_targets),
        total_native_requeues=returned["external_gini_tree_native_requeue_count"],
        controller_termination=returned["external_gini_tree_failure_reason"],
        actual_AM_decisions=rows(details / "adaptive_mass_decision_ledger.csv"),
        actual_target_phases=targets,
    )


def run_record(registered, panel, audit, fees):
    n = registered["position"]
    directory = Path(registered["directory"])
    returned = result(directory / "result.json")
    phase = {row["event"]: float(row["process_seconds"]) for row in rows(directory / "phases.csv")}
    audit_seconds = fees["audit_process_outer_seconds"]
    process = audit["completion"]["process_outer_seconds"]
    assert n == audit["position"] == fees["position"] and audit["run_id"] == registered["run_id"]
    assert audit["passed"] and audit["Optimize_run_by_reviewer"] == 0 and fees["rc"] == 0
    assert fees["audit"]["SHA256"] == sha(OUT / "review" / f"complete_audit_{n:02d}.json")
    assert 0 < process <= CAP and audit["completion"]["affinity"]["set_success"]
    physical = audit["true_final_physical"]
    h = audit["full_paid_H"]
    bank = audit["actual_Optimize_parameters"]
    b_arm = registered["arm"] == "B"
    lp_seconds, mip_seconds = 0.0, returned["gurobi_runtime"]
    process_to_first_native = phase.get("plain_gurobi_optimize_launch")
    activity = None
    path = None
    if b_arm:
        assert h and len(h["paths"]) == 1
        path = read(directory / "primal/base/path.json")
        activity = interval_activity(directory, audit, returned)
        lp_seconds, mip_seconds = activity["LP_seconds"], activity["MIP_seconds"]
        process_to_first_native = phase.get("first_lp_optimize_launch")
    else:
        assert h is None and audit["cold_parameters"]["NumStart_before_optimize"] == 0 and not audit["Start_checks"]
    assert math.isclose(lp_seconds + mip_seconds, audit["Native_seconds"], abs_tol=1e-5)
    outer_finalize = phase["process_exit"] - max(binding["return_available"] for binding in audit["actual_call_log_bindings"])
    assert outer_finalize >= 0
    h_seconds = path["H_seconds"] if path else 0.0
    h_check_seconds = path["original_verification_seconds"] if path else 0.0
    model_seconds = returned["external_gini_tree_model_build_seconds"] if b_arm else None
    model_read_seconds = returned["external_gini_tree_model_read_seconds"] if b_arm else None
    first_build = None
    if "root_canonical_model_construction_complete" in phase:
        first_build = phase["root_canonical_model_construction_complete"] - phase["root_canonical_model_construction_start"]
    residual = process - h_seconds - lp_seconds - mip_seconds
    assert residual >= -0.2
    cert = audit["certificate"]
    signed = audit["absolute_gap"]
    ratio = audit["relative_gap"]
    initial_L = audit["initial_qualified_global_L"]
    fold = dict(
        position=n, block=registered["block"], role=registered["role"], arm=registered["arm"], run_id=registered["run_id"],
        source=panel["source"], geometry=panel["geometry"], V=panel["V"], M=panel["M"], Q=panel["Q_vector"],
        input_path=panel["input_path"], input_SHA256=panel["input_sha256"], physical_key=panel["normalized_base_key"],
        full_key=panel["normalized_full_key"], T_seconds=panel["T_seconds"], pickup_seconds=60, drop_seconds=60,
        lambda_value=panel["lambda"], lambda_decimal17=panel["lambda_decimal17"], lambda_binary64=panel["lambda_binary64"],
        Native_Seed=0, repeat=1, Threads=1, MIPThreads=1, cap_seconds=CAP,
        source_commit=MEASURED, delivery_base=BASE, PE_SHA256=PE_SHA, DLL_SHA256=DLL_SHA,
        CPP_effective_preset=audit["CPP_effective_preset"],
        live_runtime=bind(OUT / "runtime_readbacks" / f"{n:02d}.json"),
        initial_U=h["selected"]["original_F"] if h else None, U=audit["U"], L=audit["L"],
        G=physical["G"] if physical else None, P=physical["P"] if physical else None,
        qualified_feasible_U=audit["U"] is not None, initial_root_global_L=initial_L["L"] if initial_L else None,
        signed_absolute_gap=signed, signed_relative_gap=ratio,
        absolute_gap=max(0., signed) if signed is not None else None,
        relative_gap=max(0., ratio) if ratio is not None else None,
        state="CERT" if cert else "OPEN", certificate=cert, certificate_basis=audit["certificate_basis"],
        raw_status=returned["status"], stop_reason=returned.get("stop_reason"),
        T_cert_process=process if cert else None, exact_first_hit_global_seconds=None,
        process_outer_seconds=process, CPP_process_seconds=returned["final_process_wall_time_seconds"],
        audit_seconds=audit_seconds, audit_reader_function_seconds=audit["audit_seconds"],
        T_total_with_independent_audit=process + audit_seconds,
        H_calls=1 if h else 0, H_seed=h["selected"]["effective_seed"] if h else None, H_seconds=h_seconds,
        H_decoded_checks=path["decoded_checks"] if path else 0,
        H_original_reverification_seconds=h_check_seconds,
        H_initialization_seconds=h["selection"]["total_initialization_seconds"] if h else 0.0,
        actual_Optimize=len(bank), LP=audit["LP"], MIP=audit["MIP"], Native_seconds=lp_seconds + mip_seconds,
        LP_native_seconds=lp_seconds, MIP_native_seconds=mip_seconds,
        Work=activity["Work"] if activity else returned["gurobi_work"],
        nodes=activity["nodes"] if activity else returned["gurobi_node_count"],
        first_model_rows=bank[0]["model_rows"], first_model_columns=bank[0]["model_columns"],
        max_model_rows=max(x["model_rows"] for x in bank), max_model_columns=max(x["model_columns"] for x in bank),
        root_model_construction_seconds=first_build, all_recorded_model_build_seconds=model_seconds,
        all_recorded_model_import_seconds=model_read_seconds, pre_first_optimize_seconds=process_to_first_native,
        post_last_optimize_seconds=outer_finalize,
        post_last_optimize_scope="C++ return publication marker to process exit, including checks, cleanup and serialization.",
        process_residual_after_H_and_Native_seconds=residual,
        P_NumStart_before_optimize=audit["cold_parameters"]["NumStart_before_optimize"] if not b_arm else None,
        audit_file=fees["audit"], invocation=audit["actual_invocation"], raw_result=audit["completion"]["result"],
        raw_fleet=bind(directory / "fleet.json") if (directory / "fleet.json").is_file() else None,
        raw_archive_member=f"complete_raw/{directory.name}/result.json",
    )
    assert fold["live_runtime"]["SHA256"] == audit["native_DLL_live_readback"]["SHA256"]
    if cert:
        assert 0 < fold["U"] and abs(fold["signed_absolute_gap"]) <= 1e-7
    if activity:
        activity.pop("ledger")
    summary = dict(
        role=fold["role"], arm=fold["arm"], run_id=fold["run_id"], H_F=fold["initial_U"], final_U=fold["U"],
        initial_original_global_L=fold["initial_root_global_L"], final_L=fold["L"], H_seconds=fold["H_seconds"],
        first_model_rows=fold["first_model_rows"], first_model_columns=fold["first_model_columns"],
        recorded_model_build_seconds=model_seconds, pre_first_optimize_seconds=process_to_first_native,
        LP_seconds=lp_seconds, MIP_seconds=mip_seconds, final_state=fold["state"], native_status=fold["raw_status"],
        stop_reason=fold["stop_reason"], Native_Work=fold["Work"], nodes=fold["nodes"],
    )
    for field in ("parent_LP_calls", "child_LP_calls", "parent_LP_seconds", "child_LP_seconds",
                  "accepted_splits", "declined_splits", "maximum_live_coverage_leaves",
                  "coverage_leaf_count_terminal", "open_leaves_terminal", "child_target_MIP_calls",
                  "child_target_parent_requeues", "child_target_MIP_seconds", "total_native_requeues",
                  "controller_termination", "actual_AM_decisions", "actual_target_phases"):
        summary[field] = activity[field] if activity else None
    return fold, summary


def delta_values(b, p, metric):
    left, right = b[metric], p[metric]
    if left is None or right is None:
        return None, None
    difference = left - right
    return difference, 100 * difference / abs(right) if abs(right) > 1e-12 else None


def matched_pair(b, p):
    keys = ("role", "input_SHA256", "full_key", "T_seconds", "lambda_binary64", "Native_Seed",
            "repeat", "cap_seconds", "Threads", "MIPThreads", "PE_SHA256", "DLL_SHA256", "source_commit")
    assert b["arm"] == "B" and p["arm"] == "P"
    assert all(b[k] == p[k] for k in keys), "Not a strict matched pair"
    delta = max(1e-6, .001 * max(abs(p["U"]), 1e-12)) if p["U"] is not None else None
    detail = {k: b[k] for k in ("role", "Native_Seed", "cap_seconds", "input_SHA256", "full_key")}
    detail.update(B_run=b["run_id"], P_run=p["run_id"], delta=delta)
    for arm, row in (("B", b), ("P", p)):
        for key in ("state", "initial_U", "U", "L", "signed_absolute_gap", "absolute_gap", "relative_gap",
                    "T_cert_process", "process_outer_seconds", "audit_seconds", "H_seconds", "Native_seconds", "Work", "nodes"):
            detail[f"{arm}_{key}"] = row[key]
    for metric in ("U", "L", "absolute_gap", "relative_gap", "process_outer_seconds", "Native_seconds", "Work", "nodes"):
        diff, rel = delta_values(b, p, metric)
        detail[f"delta_{metric}"], detail[f"pct_change_{metric}"] = diff, rel
    if b["certificate"] and p["certificate"]:
        assert abs(b["U"] - p["U"]) <= 1e-7, "Joint certificate objectives differ"
        cert_case = "both_CERT"
        ratio = b["T_cert_process"] / p["T_cert_process"]
    else:
        cert_case = "B_only_CERT" if b["certificate"] else "P_only_CERT" if p["certificate"] else "both_OPEN"
        ratio = None
    detail.update(certificate_comparison=cert_case, B_over_P_T_cert_process=ratio)
    for metric, sign in (("U", -1), ("L", 1), ("absolute_gap", -1)):
        diff = detail[f"delta_{metric}"]
        detail[f"material_B_{metric}"] = (("favors_B" if sign * diff > delta else "favors_P" if sign * diff < -delta
                                         else "difference_within_delta") if delta is not None and diff is not None else None)
    detail["feasibility"] = ("both_feasible" if b["qualified_feasible_U"] and p["qualified_feasible_U"]
                             else "B_only_feasible" if b["qualified_feasible_U"]
                             else "P_only_feasible" if p["qualified_feasible_U"] else "neither_feasible")
    return detail


def collect(partial=False):
    manifest = read(MANIFEST)
    matrix = read(MATRIX)
    roles = {p["id"]: p for p in manifest["roles"]}
    attempts_path = OUT / "review/audit_process_costs.json"
    attempts = read(attempts_path) if attempts_path.is_file() else []
    fees = {row["position"]: row for row in attempts if row["rc"] == 0}
    outputs = TEMP / "preview" if partial else OUT
    outputs.mkdir(parents=True, exist_ok=True)
    complete, activity, missing = [], [], []
    for position in matrix["positions"]:
        n = position["position"]
        path = OUT / "review" / f"complete_audit_{n:02d}.json"
        if n in fees and path.is_file():
            row, controller = run_record(position, roles[position["role"]], read(path), fees[n])
            complete.append(row)
            activity.append(controller)
        else:
            completion_path = Path(position["directory"]) / "completion.json"
            missing.append(dict(
                position=n, input=position["role"], arm=position["arm"], run_id=position["run_id"],
                actual_producer_receipt=read(completion_path) if completion_path.is_file() else None,
                audit_attempts=[a for a in attempts if a["position"] == n],
            ))
    if not partial:
        assert not missing and read(OUT / "panel_complete.json")["positions"] == 12
    if not complete:
        return
    lookup = {(row["role"], row["arm"]): row for row in complete}
    pairs = [matched_pair(lookup[(key, "B")], lookup[(key, "P")]) for key in roles
             if (key, "B") in lookup and (key, "P") in lookup]
    table_csv(outputs / "complete_arms.csv", complete)
    write(outputs / "complete_arms.json", dict(UTC=utc(), qualified=len(complete), registered=len(matrix["positions"]),
                                              missing=missing, rows=complete, source=bind(MATRIX)))
    table_csv(outputs / "activity.csv", activity)
    write(outputs / "activity.json", dict(UTC=utc(), runs=activity, B_root_L_scope="Audit of original improving domain and its complement."))
    write(outputs / "comparison_BP.json", dict(UTC=utc(), matched=len(pairs), rows=pairs, materiality=matrix["delta"]))
    if pairs:
        table_csv(outputs / "comparison_BP.csv", pairs)

    fields = ("process_outer_seconds", "H_calls", "H_seconds", "H_original_reverification_seconds",
              "H_initialization_seconds", "actual_Optimize", "LP", "MIP", "LP_native_seconds", "MIP_native_seconds",
              "Native_seconds", "Work", "nodes", "audit_seconds", "T_total_with_independent_audit",
              "pre_first_optimize_seconds", "post_last_optimize_seconds")
    costs = {key: sum(row[key] for row in complete if row[key] is not None) for key in fields}
    aggregate = {arm: {key: sum(row[key] for row in complete if row["arm"] == arm and row[key] is not None)
                       for key in fields} for arm in ("B", "P")}
    producer_costs = [read(Path(p["directory"]) / "completion.json") for p in matrix["positions"]
                      if (Path(p["directory"]) / "completion.json").is_file()]
    costs.update(
        UTC=utc(), nominal_process_cap_sum=CAP * len(matrix["positions"]), by_arm=aggregate,
        qualified_positions=len(complete), all_actual_producers_outer_seconds=sum(row["process_outer_seconds"] for row in producer_costs),
        all_actual_audit_attempt_seconds=sum(a["audit_process_outer_seconds"] for a in attempts),
        total_audit_attempts=len(attempts), failed_audit_attempts=sum(a["rc"] != 0 for a in attempts),
        qualification_outer_seconds=read(OUT / "qualification/result.json")["outer_seconds_this_session"],
        B_all_reported_build_seconds=sum(row["all_recorded_model_build_seconds"] for row in complete if row["arm"] == "B"),
        B_all_reported_model_import_seconds=sum(row["all_recorded_model_import_seconds"] for row in complete if row["arm"] == "B"),
        P_isolated_build_seconds=None, post_return_check_seconds_combined_with_finalization=True,
        timer_scope="H, Native, construction, mapping, checks and serialization are nested in the producer process.",
        clock=clock(),
    )
    write(outputs / "cost_report.json", costs)
    print(f"{len(complete)} qualified, {len(pairs)} matched, {costs['actual_Optimize']} Optimize, "
          f"{costs['process_outer_seconds']:.3f} process seconds", flush=True)


def master_fields(arm):
    if arm is None:
        return ["无配对结果", "", "", "", ""]
    if arm["certificate"]:
        return ["已收敛", arm["T_cert_process"], "", arm["L"], arm["U"]]
    gap = arm["relative_gap"]
    return ["未收敛", "", 100 * gap if gap is not None else "", arm["L"], arm["U"]]


def apply_master(data_commit):
    base = blob(BEGINNING, MASTER)
    assert len(base) == MASTER_BASE_BYTES and digest(base) == MASTER_BASE_SHA
    assert base.endswith(b"\r\n")
    table = list(csv.reader(io.StringIO(base.decode("utf-8-sig"), newline="")))
    header = table[0]
    assert len(table) == 127 and {len(r) for r in table} == {28} and header[-2:] == ["实验数据来源", "实例元数据来源"]
    arms = read(OUT / "complete_arms.json")["rows"]
    manifest = read(MANIFEST)
    index = {(row["role"], row["arm"]): row for row in arms}
    pairs = {v["role"]: v for v in read(OUT / "comparison_BP.json")["rows"]}
    url = f"https://github.com/yifanXovo/TailoredExact/blob/{data_commit}/"
    data_path = (REL / "complete_arms.json").as_posix()
    meta_path = (REL / "input_manifest.json").as_posix()
    assert blob(data_commit, data_path) == (OUT / "complete_arms.json").read_bytes()
    assert blob(data_commit, meta_path) == MANIFEST.read_bytes()

    values, mapping = [], []
    for p in manifest["roles"]:
        role = p["id"]
        b, plain, pair = index.get((role, "B")), index.get((role, "P")), pairs.get(role)
        if b is None:
            continue
        status = "分指标比较" if pair else "N/A"
        note = f"同输入同预算B/P；B {b['state']}，P {plain['state']}" if pair else "合格B运行；N/A-P"
        if pair:
            for column, tag in (("delta_U", "ΔU"), ("delta_L", "ΔL"), ("delta_absolute_gap", "Δ绝对gap")):
                value = pair[column]
                note += f"；{tag}={value:.17g}" if value is not None else f"；{tag}=缺失"
        note += f"；Native Seed0；cap={CAP}s；B={b['run_id']}"
        if pair:
            note += f"；P={plain['run_id']}"
        note += f"；CPP={MEASURED}；PE={PE_SHA}；证时=T_cert_process"
        geometry = {"compact": "紧凑分布", "regional": "区域分布"}[p["geometry"]]
        row = [
            role, p["V"], p["M"], "库存短缺", "S", p["source"], geometry, p["T_seconds"],
            p["lambda_decimal17"], format(p["lambda"] / .15, ".17g"), 0, 1, 171, CAP,
            *master_fields(b), *master_fields(plain), status, note, url + data_path, url + meta_path,
        ]
        values.append(row)
        mapping.append(dict(
            master_line=len(table) + len(values), physical_key=p["normalized_base_key"], input_SHA256=p["input_sha256"],
            role=role, B_run=b["run_id"], P_run=plain["run_id"] if plain else None,
            strict_pair=pair is not None, evidence_commit=data_commit,
        ))

    serial = io.StringIO(newline="")
    csv.writer(serial, lineterminator="\r\n").writerows(values)
    increment_bytes = serial.getvalue().encode("utf-8")
    updated = base + increment_bytes
    assert MASTER.read_bytes() in (base, updated), "An authority already exists with different bytes"
    verify = list(csv.reader(io.StringIO(updated.decode("utf-8-sig"), newline="")))
    assert verify[:127] == table and len(verify) == 127 + len(mapping) and {len(row) for row in verify} == {28}
    keys = [(row[0], row[10], row[11], row[12], row[13], row[7], row[8]) for row in verify]
    if mapping:
        new_keys = keys[-len(mapping):]
        assert len(set(new_keys)) == len(mapping)
        assert set(keys[:-len(mapping)]).isdisjoint(new_keys)
    assert updated.count(b"\n") == updated.count(b"\r\n")
    head = io.StringIO(newline="")
    csv.writer(head, lineterminator="\r\n").writerow(header)
    INCREMENT.write_bytes(b"\xef\xbb\xbf" + head.getvalue().encode("utf-8") + increment_bytes)
    MASTER.write_bytes(updated)
    write(OUT / "CSV_reconciliation.json", dict(
        UTC=utc(), evidence_data_commit=data_commit, baseline_commit=git("rev-parse", BEGINNING),
        baseline_bytes=MASTER_BASE_BYTES, baseline_SHA256=MASTER_BASE_SHA, baseline_records=126,
        baseline_prefix_exact=MASTER.read_bytes()[:MASTER_BASE_BYTES] == base, master=bind(MASTER),
        records=len(verify) - 1, columns=28, BOM="UTF-8", line_endings="CRLF",
        increment=bind(INCREMENT), new_B_records=len(values), new_strict_pairs=len(pairs),
        new_physical_identities=len({p["normalized_base_key"] for p in manifest["roles"]}),
        B_lower_U_material=sum(v["material_B_U"] == "favors_B" for v in pairs.values()),
        B_higher_L_material=sum(v["material_B_L"] == "favors_B" for v in pairs.values()),
        B_narrower_absolute_gap_material=sum(v["material_B_absolute_gap"] == "favors_B" for v in pairs.values()),
        B_joint_U_L_gap_material=sum(all(v[f"material_B_{k}"] == "favors_B" for k in ("U", "L", "absolute_gap"))
                                     for v in pairs.values()),
        mapping=mapping, status_policy="Qualified CERT uses T_cert_process. OPEN gaps are in percent.",
    ))
    print(f"CSV {len(table)-1} -> {len(verify)-1}, SHA256 {sha(MASTER)}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--partial", action="store_true")
    stage.add_argument("--append-master", metavar="DATA_COMMIT")
    args = parser.parse_args()
    if args.append_master:
        apply_master(args.append_master)
    else:
        collect(args.partial)
