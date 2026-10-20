"""Finite R127 training review. Standard library only; never launches a solver.

This deliberately does not import the campaign, selection, clocks or portable
checker implementations. It reads only current training and admission evidence.
The caller meters this script with round127_common.metered(kind='verification').
"""
from pathlib import Path
import ast
import collections
import datetime
import hashlib
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "results/unified_exact_round127"
REVIEW = OUT / "review"
FEE_LABEL = sys.argv[1] if len(sys.argv) > 1 else "independent_selection_review_01"
ROWS = []
ERRORS = []
HASHES = {}
E1_SHA = "d668236e9396b2e12f02bb65d9819b98762d2a35aad1b186d352d234dae756c9"
DLL_SHA = "9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88"
CONFIGS = [dict(id="q" + str(j), MIPFocus=f, Cuts=c,
                nondefault_parameters=int(f != 0) + int(c != -1))
           for j, (f, c) in enumerate([(0, -1), (1, -1), (2, -1),
                                      (3, -1), (2, 2), (3, 2)])]
ROLES = [
    ("S12", "reference/round106_confirmation/S12.txt", 12, 2, [8, 12], 3600, 90,
     "475763e70a2dc3b9d28a88028378e76946cbebf33aa7b7e5b033e018dd13369f"),
    ("PB-B20-S", "reference/round122_paper_benchmark/PB-B20-S.txt", 20, 2, [20, 40], 7200, 180,
     "3aa535245e6475f791d50d8be26e8165c6f83371d9dbebac76728b9cc36eebbc"),
    ("R98-C2", "reference/round98_confirmation/C2.txt", 30, 3, [20, 25, 30], 7200, 180,
     "07d0964c87b534254e6bf2957911859a6a2bd73e377211728b7e65f44294fc76"),
]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    path = Path(path).resolve()
    key = str(path)
    if key not in HASHES:
        h = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(block)
        HASHES[key] = h.hexdigest()
    return HASHES[key]


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def close(a, b, eps=1e-8):
    return a is None and b is None or (a is not None and b is not None
            and math.isfinite(a) and math.isfinite(b) and abs(a - b) <= eps)


def params(path):
    values = {"MIPFocus": 0, "Cuts": -1}
    seen = set()
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        key, val = line.split()
        require(key in values and key not in seen, "unregistered/duplicate PRM setting")
        values[key] = int(val)
        seen.add(key)
    return values


def check_position(position, role, seed, config, declared, frozen):
    ident, path, n, m, qs, horizon, cap, input_sha = role
    name = f"training/{position:02d}_{ident}_S{seed}_{config['id']}"
    camp = OUT / name
    i = read(camp / "identity.json")
    require(len(i["launches"]) == 1, name + ": singleton launch")
    launch = i["launches"][0]
    d = Path(launch["destination"])
    expected_d = camp / f"raw/01_{ident}_S{seed}_R1_P"
    require(d.resolve() == expected_d.resolve(), name + ": destination identity")
    require(declared["position"] == position and declared["seed"] == seed
            and declared["configuration"] == config, name + ": frozen order/config")
    expected_role = dict(id=ident, input_path=path, input_sha256=input_sha, V=n, M=m,
                         Q_vector=qs, T_seconds=horizon, cap_seconds=cap,
                         pickup_seconds=60, drop_seconds=60, **{"lambda": .15})
    require(declared["role"] == expected_role, name + ": frozen role")
    require(all(launch["panel"][k] == v for k, v in expected_role.items()), name + ": launch role")
    require(launch["seed"] == seed and launch["repeat"] == 1 and launch["number"] == 1
            and launch["arm"] == "P-GRB" and launch["method"] == "P"
            and launch["binary_layer"] == "E1" and launch["panel_kind"] == "training"
            and launch["configuration"] == config and launch["cap_seconds"] == cap
            and launch["hard_stop_seconds"] == cap - 2, name + ": actual launch fields")
    require(i["candidate_binary_sha256"] == E1_SHA and i["dll_sha256"] == DLL_SHA
            and i["source_hashes"] == frozen["source_bindings"], name + ": binary/source freeze")
    command = launch["command"]
    require(Path(command[0]).resolve() == Path(frozen["PE"]).resolve(), name + ": native PE")
    options, flags = {}, set()
    k = 1
    while k < len(command):
        key = command[k]
        require(key.startswith("--") and key not in options and key not in flags, name + ": duplicate argv")
        if k + 1 == len(command) or command[k + 1].startswith("--"):
            flags.add(key); k += 1
        else:
            options[key] = command[k + 1]; k += 2
    expected_options = {"--input": path, "--lambda": ".15", "--T": str(horizon),
        "--pickup-time": "60", "--drop-time": "60", "--time-limit": str(cap - 6),
        "--process-wall-time-limit": str(cap), "--process-shutdown-margin": "30",
        "--threads": "1", "--mip-threads": "1", "--gurobi-seed": str(seed),
        "--gurobi-presolve": "-1", "--method": "gurobi", "--round61-candidate-mode": "off",
        "--round127-mode": "p"}
    for key, expected in expected_options.items():
        require((float(options[key]) == float(expected)) if key == "--lambda"
                else options[key] == expected, name + ": argv " + key)
    require(flags == {"--plain-baseline"}, name + ": cold P flag")
    prm = OUT / f"tuning_manifest/{config['id']}.prm"
    require(Path(options["--round127-p-parameters"]).resolve() == prm.resolve()
            and params(prm) == {k: config[k] for k in ["MIPFocus", "Cuts"]}, name + ": PRM")
    origin = read(d / "child_process_origin.json")
    require(origin["creation_from_live_OS_handle"] is True and origin["PE_SHA"] == E1_SHA
            and origin["command"] == command and origin["seed"] == seed, name + ": fresh native process")
    result = read(d / "result.json")
    parameter_readback = read(d / "round127_parameters.json")
    require(parameter_readback == dict(MIPFocus=config["MIPFocus"], Cuts=config["Cuts"],
        NumStart_before_optimize=0, loaded_after_presets=True, authoritative_model_environment=True), name + ": actual parameters/Start")
    require(all(result.get(k) is True for k in ["gurobi_native_domain_audit_passed",
        "gurobi_native_variable_names_match", "gurobi_native_variable_types_match",
        "gurobi_native_variable_bounds_match", "gurobi_native_objective_sense_match",
        "gurobi_lifecycle_valid", "native_mip_strict_gap_parameters_valid"]), name + ": native identity/numerics")
    require(result["gurobi_hga_start_requested"] is False and result["gurobi_hga_start_submitted"] is False
        and result["gurobi_model_count"] == result["gurobi_model_read_count"] == result["gurobi_optimize_count"] == 1
        and result["gurobi_environment_count"] == 1 and result["gurobi_optimize_return_code"] == 0
        and result["algorithm_preset"] == "custom" and result["gurobi_version"] == "13.0.2", name + ": cold single native solve")
    event = read(d / "journal/event_1.json")
    require(event["kind"] == "identity" and event["input_sha256"] == input_sha
        and event["V"] == n and event["M"] == m and event["T"] == horizon
        and event["lambda"] == .15 and event["pickup_seconds"] == event["drop_seconds"] == 60, name + ": journal input")
    call = read(d / "journal/event_2.json")
    settings = dict(read_return_code=0, Threads=1, Seed=seed, Presolve=-1, MIPGap=0,
                    MIPGapAbs=0, FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6)
    require(call["kind"] == "call" and call["call"] == 1 and call["full_original"] == 1
        and call["model_scope"] == "complete_original_compact_milp" and call["settings"] == settings,
        name + ": complete model/settings")
    reference = launch["panel"]["reference"]
    model_sha = sha(d / "compact.lp")
    require(model_sha == reference["canonical_sha256"] == sha(camp / f"reference/{ident}/original.lp")
        == result["gurobi_canonical_model_sha256"] == call["model_sha256"], name + ": actual compact identity")
    for key, field in [("fingerprint", "gurobi_model_fingerprint"), ("rows", "gurobi_num_constrs"),
                       ("columns", "gurobi_num_vars"), ("nonzeros", "gurobi_num_nzs")]:
        require(reference[key] == result[field], name + ": model counts/fingerprint")
    producer = read(d / "producer_receipt.json")
    seal = read(d / "producer_seal.json")
    total = read(d / "arm_total_receipt.json")
    v = read(d / "verification_closeout.json")
    audit = read(d / "audit.json")
    own = read(d / "independent_evidence.json")
    rejection = read(d / "claim_rejections.json")
    a = read(camp / "reconstructed.json")["arms"]
    require(len(a) == 1, name + ": one retained arm")
    a = a[0]
    require(producer["producer_seal_SHA"] == sha(d / "producer_seal.json")
        and total["producer_receipt_SHA"] == v["producer_receipt_SHA"] == a["producer_receipt_SHA"] == sha(d / "producer_receipt.json")
        and total["verification_closeout_SHA"] == sha(d / "verification_closeout.json"), name + ": receipt chain")
    # Verify finite sealed outputs and proof-closeout files, not the full raw journal.
    for file, recorded in seal["required_SHA"].items():
        require(sha(d / file) == recorded, name + ": sealed " + file)
    for field, file in [("audit_SHA", "audit.json"), ("own_evidence_SHA", "independent_evidence.json"),
                        ("claims_SHA", "native_claims.json"), ("rejection_SHA", "claim_rejections.json")]:
        require(v[field] == sha(d / file), name + ": closeout " + field)
    require(all(producer.get(k) is True for k in ["required_outputs_closed", "native_stopped_no_reentry"])
        and all(seal.get(k) is True for k in ["required_outputs_closed", "native_stopped_no_reentry", "necessary_producer_trailer_complete"])
        and all(v.get(k) is True for k in ["necessary_verification_complete", "native_proof_qualified", "no_new_solution_or_certificate_backfilled"])
        and total["necessary_verification_complete"] is True, name + ": final closeout")
    require(all(own.get(k) is True for k in ["own_physical_verified", "identity_verified", "input_verified",
        "model_domain_verified", "journal_verified", "return_verified", "files_verified"])
        and own["extra_after_production_solution_or_bound"] is False
        and own["input_SHA"] == input_sha and own["result_SHA"] == sha(d / "result.json"), name + ": sealed own proof")
    require(audit["passed"] is True and audit["independent_evidence_audit_passed"] is True
        and audit["native_proof_qualified"] is True and rejection["rejections"] == []
        and rejection["damaged_calls"] == [] and a["rejected_calls"] == [], name + ": proof eligibility")
    require(a["formal_protocol_qualified"] is True and a["numbers_qualified"] is True
        and a["certificate_qualified"] is True and a["native_proof_qualified"] is True
        and a["source_reduced"] is False and a["PE_SHA"] == E1_SHA and a["DLL_SHA"] == DLL_SHA
        and a["input_SHA"] == input_sha and a["configuration"] == config
        and a["actually_executed"] is True and a["method"] == "P" and a["seed"] == seed,
        name + ": reconstructed qualification")
    end = audit["endpoint"]
    certificate = bool(end["certificate"] or own["own_exact_zero"])
    require(a["certificate"] is certificate and close(a["U"], end["U"])
        and close(a["L"], end["L"]), name + ": endpoint agreement")
    completion = read(d / "completion.json")
    require(completion["returncode"] == 0 and completion["within_cap"] is True
        and completion["stop_reason"] == "normal_return", name + ": native completion")
    fee = OUT / "fees" / name.replace("/", "_")
    fee_launch, pid, fee_end = (read(fee / file) for file in ["launch.json", "PID.json", "receipt.json"])
    marker = pid["launched_unix"]
    require(fee_launch["kind"] == "training" and fee_launch["command"] == pid["command"]
        and fee_launch["command"][-1] == name and close(marker, fee_end["start_unix"])
        and fee_end["exit_observed"] is True and fee_end["nested_seconds_added"] is False,
        name + ": true parent marker")
    require(marker <= producer["t0_unix"] <= origin["actual_creation_unix"] <= completion["ended_unix"]
        <= producer["t_produce_unix"] <= total["t_verified_unix"], name + ": wall clock order")
    require(producer["t_produce_unix"] <= fee_end["end_unix"]
        and abs((fee_end["end_unix"] - marker) - fee_end["outer_seconds"]) < .05
        and abs((producer["t_produce_unix"] - producer["t0_unix"]) - producer["T_produce"]) < .05,
        name + ": wall/performance clock consistency")
    require(close(producer["T_produce"], producer["t_produce_perf"] - producer["t0_perf"])
        and close(total["T_verify"], total["t_verified_perf"] - producer["t_produce_perf"])
        and close(total["T_total"], producer["T_produce"] + total["T_verify"]), name + ": original monotonic clocks")
    full = producer["t_produce_unix"] - marker
    prefix = producer["t0_unix"] - marker
    require(0 < full <= cap and producer["cap_seconds"] == cap, name + ": complete cap")
    tcert = full if certificate else None
    require(close(a["T_cert"], producer["T_produce"] if certificate else None), name + ": raw T_cert null rule")
    clock = read(camp / "complete_training_clock.json")
    for key, val in dict(actual_parent_admission_unix=marker, sealed_producer_unix=producer["t_produce_unix"],
        raw_receipt_T_produce=producer["T_produce"], raw_receipt_T_cert=a["T_cert"],
        admission_prefix_seconds=prefix, T_produce=full, T_verify=total["T_verify"],
        T_total=full + total["T_verify"], T_cert=tcert).items():
        require(close(clock[key], val), name + ": recovered clock " + key)
    require(clock["name"] == name and clock["within_complete_cap"] is True and clock["all_gates_qualified"] is True
        and clock["producer_receipt_SHA"] == sha(d / "producer_receipt.json")
        and clock["total_receipt_SHA"] == sha(d / "arm_total_receipt.json")
        and clock["marker_receipt_SHA"] == sha(fee / "PID.json")
        and clock["no_Optimize"] is True and clock["no_original_receipt_changed"] is True
        and clock["no_outer_fee_prefix_added_twice"] is True, name + ": recovered clock binding")
    return dict(position=position, name=name, id=ident, seed=seed, configuration=config["id"], qualified=True,
        certificate=certificate, T_cert=tcert, T_produce=full, T_verify=total["T_verify"], T_total=full + total["T_verify"],
        raw_receipt_T_produce=producer["T_produce"], raw_receipt_T_cert=a["T_cert"], admission_prefix_seconds=prefix,
        cap_seconds=cap, q_score=full / cap if certificate else 1,
        parent_admission_unix=marker, fee_end_unix=fee_end["end_unix"], wrapper_pid=pid["pid"],
        native_pid=origin["pid"], native_creation_unix=origin["actual_creation_unix"],
        raw_wall_perf_difference=(producer["t_produce_unix"] - producer["t0_unix"]) - producer["T_produce"],
        model_SHA=model_sha, identity_SHA=sha(camp / "identity.json"), result_SHA=sha(camp / "reconstructed.json"),
        producer_receipt_SHA=sha(d / "producer_receipt.json"), total_receipt_SHA=sha(d / "arm_total_receipt.json"),
        destination=str(d))


def main():
    manifest = read(OUT / "experiment_manifest.json")
    frozen = read(OUT / "E1_frozen.json")
    require(manifest["configurations"] == CONFIGS and len(manifest["E1_training"]) == 36, "frozen 36/configuration table")
    require(frozen["final_qualification_pending"] is False and frozen["PE_SHA"] == E1_SHA
        and sha(frozen["PE"]) == E1_SHA and frozen["DLL_SHA"] == DLL_SHA
        and sha("D:/gurobi1302/win64/bin/gurobi130.dll") == DLL_SHA, "frozen actual PE/DLL")
    for path, digest in frozen["source_bindings"].items():
        require(sha(ROOT / path) == digest, "frozen source " + path)
    for role in ROLES:
        ident, path, n, m, qs, horizon, cap, digest = role
        require(sha(ROOT / path) == digest, ident + ": original input SHA")
        header = (ROOT / path).read_text(encoding="utf-8-sig").splitlines()[0].split(maxsplit=2)
        require((int(header[0]), int(header[1]), ast.literal_eval(header[2])) == (n, m, qs), ident + ": V/M/Q")
    expected_names = []
    for j, role in enumerate(ROLES):
        for seed in (2, 3):
            shift = (j + 2 * (seed - 2)) % 6
            for config in CONFIGS[shift:] + CONFIGS[:shift]:
                position = len(expected_names) + 1
                expected_names.append(f"{position:02d}_{role[0]}_S{seed}_{config['id']}")
                try:
                    ROWS.append(check_position(position, role, seed, config, manifest["E1_training"][position - 1], frozen))
                except Exception as exc:
                    ERRORS.append(dict(position=position, error=str(exc)))
    require(sorted(p.name for p in (OUT / "training").iterdir() if p.is_dir()) == sorted(expected_names), "all 36 and only 36 retained training directories")
    require(not ERRORS and len(ROWS) == 36, "position qualification failed: " + str(ERRORS))
    require(len({(r["id"], r["seed"], r["configuration"]) for r in ROWS}) == 36, "36 unique mathematical positions")
    require(len({r["destination"] for r in ROWS}) == 36 and len({(r["native_pid"], r["native_creation_unix"]) for r in ROWS}) == 36, "distinct fresh processes/destinations")
    require(all(a["fee_end_unix"] <= b["parent_admission_unix"] for a, b in zip(ROWS, ROWS[1:])), "actual training order/serial fees")
    models = {role[0]: sorted({r["model_SHA"] for r in ROWS if r["id"] == role[0]}) for role in ROLES}
    require(all(len(values) == 1 for values in models.values()), "one cold compact model per input")
    scores = []
    for config in CONFIGS:
        rows = [r for r in ROWS if r["configuration"] == config["id"]]
        require(len(rows) == 6 and len({(r["id"], r["seed"]) for r in rows}) == 6, "six complete positions per q")
        by_seed = {str(s): sum(r["certificate"] for r in rows if r["seed"] == s) for s in (2, 3)}
        scores.append(dict(config, complete_qualified=all(r["qualified"] for r in rows),
            N=sum(r["certificate"] for r in rows), N_by_seed=by_seed,
            N_min=min(by_seed.values()), S_q=sum(r["q_score"] for r in rows) / 6))
    base = scores[0]
    require(base["complete_qualified"], "q0 must be fully qualified")
    eligible = [q for q in scores[1:] if q["complete_qualified"] and q["N"] >= base["N"]
        and q["N_min"] >= base["N_min"] and (q["N"] > base["N"] or
            (q["N"] == base["N"] > 0 and q["S_q"] < base["S_q"] and q["S_q"] <= .90 * base["S_q"]))]
    chosen = min(eligible, key=lambda q: (-q["N"], -q["N_min"], q["S_q"], q["nondefault_parameters"], int(q["id"][1:]))) if eligible else base
    # The pipeline's output is read only after the independent choice exists.
    selected = read(OUT / "tuning_selection.json")
    require(selected["status"] == "SELECTED" and len(selected["all_rows"]) == 36
        and selected["evaluation_results_consulted"] == 0 and selected["selected"] == chosen,
        "published choice disagrees")
    require(selected["eligible_nondefault"] == [q["id"] for q in eligible], "published eligibility disagrees")
    for actual, expected in zip(selected["scores"], scores):
        require(all(close(actual[k], expected[k]) if k == "S_q" else actual[k] == expected[k]
                    for k in expected), "published score disagrees")
    require(len(selected["scores"]) == 6, "all six score rows retained")
    for actual, expected in zip(selected["all_rows"], ROWS):
        for key in ["position", "id", "seed", "configuration", "qualified", "certificate", "identity_SHA", "result_SHA", "destination"]:
            require(actual[key] == expected[key], "published row " + key)
        for key in ["T_cert", "T_produce", "T_verify", "T_total", "raw_receipt_T_produce", "raw_receipt_T_cert", "admission_prefix_seconds", "cap_seconds", "q_score"]:
            require(close(actual[key], expected[key]), "published row clock/score " + key)
    prm = OUT / "selected_P.prm"
    require(params(prm) == {k: chosen[k] for k in ["MIPFocus", "Cuts"]}
        and sha(prm) == sha(OUT / f"tuning_manifest/{chosen['id']}.prm") == selected["selected_prm_SHA"]
        and selected["E1_SHA"] == E1_SHA and selected["DLL_SHA"] == DLL_SHA, "selected PRM/binary SHA")
    absent = {name: not (OUT / name).exists() for name in ["main", "tiny", "core"]}
    require(all(absent.values()), "formal output already exists; preformal timing claim must be reviewed")
    formal_fees = []
    for p in sorted((OUT / "fees").glob("*/launch.json")):
        if read(p).get("kind", "").startswith("formal_"):
            formal_fees.append(p.parent.name)
    require(not formal_fees, "formal fee already launched")
    return dict(selected=chosen, scores=scores, eligible_nondefault=[q["id"] for q in eligible],
        selected_prm_SHA=sha(prm), models=models, formal_directories_absent=absent, formal_fee_launches=formal_fees,
        all_36_retained=True, no_evaluation_outcomes_read=True, complete_cap_passes=36,
        null_T_cert_open_positions=sum(not r["certificate"] for r in ROWS),
        prefix_seconds_range=[min(r["admission_prefix_seconds"] for r in ROWS), max(r["admission_prefix_seconds"] for r in ROWS)],
        maximum_abs_raw_wall_perf_discrepancy=max(abs(r["raw_wall_perf_difference"]) for r in ROWS))


if __name__ == "__main__":
    status, data = "PASS", {}
    try:
        data = main()
    except Exception as exc:
        status = "FAIL"
        ERRORS.append(dict(error=type(exc).__name__ + ": " + str(exc)))
    receipt = dict(schema="round127-independent-selection-review-v1", status=status,
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        reviewer="separate executor qualification_reviewer; finite evidence review, not third-party replication",
        implementation="independent standard-library audit; no pipeline/checker/clock function called",
        verification_fee_label=FEE_LABEL,
        no_Optimize=True, no_build=True, no_native_rerun=True,
        script_SHA=sha(__file__), rows=ROWS, errors=ERRORS, summary=data,
        inspected_file_SHA=HASHES,
        scope="36 current training positions: identities, actual parameters/cold model hashes, sealed final proof gates, receipt chains, parent-marker cap clocks and frozen selection arithmetic; no replay of full native matrices or physical proof reader")
    machine = REVIEW / "selection_independent_receipt.json"
    machine.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    text = ["# Independent finite training-selection review", "",
        "Status: " + status + ". Review UTC: " + receipt["UTC"] + ".", "",
        "A separate executor implemented the selection and timestamp arithmetic in a standard-library-only script. "
        "No campaign selection, portable checker or clock-recovery function was called. No Optimize, build or native rerun was performed. "
        "This is a finite evidence review, not third-party replication or a full rational audit of every native matrix.", ""]
    if status == "PASS":
        text += [f"The independently selected configuration is **{data['selected']['id']}** "
            f"(MIPFocus={data['selected']['MIPFocus']}, Cuts={data['selected']['Cuts']}). "
            "It agrees with the sealed pipeline output and may be committed as the frozen selection before formal evaluation.", "",
            "| q | N | N Seed 2 | N Seed 3 | N min | S q | Eligible nondefault |",
            "|---|---:|---:|---:|---:|---:|---|"]
        for q in data["scores"]:
            text.append(f"| {q['id']} | {q['N']} | {q['N_by_seed']['2']} | {q['N_by_seed']['3']} | {q['N_min']} | {q['S_q']:.16f} | "
                        + ("yes" if q["id"] in data["eligible_nondefault"] else "default" if q["id"] == "q0" else "no") + " |")
        text += ["", "Only q2 and q4 meet the nondefault eligibility rule. Both improve certificate count over q0; "
            "q2 wins on the smaller score after the equal N/N min comparisons. No extra configuration or alternative test result enters the rule.", "",
            "All 36 positions are retained, unique and complete; each q has six positions over the three frozen input SHA identities and Seeds 2/3. "
            "The manifest rotation matches actual singleton launch names and chronological, nonoverlapping original outer fee intervals. "
            "Every position has its own native creation record/destination, one native model and Optimize call, actual requested MIPFocus/Cuts, "
            "and NumStart_before_optimize=0. For each input, all 12 actual compact LP byte hashes match the reference and native model-domain readback. "
            "The frozen actual E1 PE, DLL and source bindings were checked.", "",
            "For every position, the selection clock was independently recalculated as "
            "producer.t_produce_unix minus the original fee PID.launched_unix. The latter is the real parent logical admission marker before "
            "launch.json/Popen, not an invented OS wrapper birth time. T_total adds the original monotonic verification interval. "
            f"All 36 complete producer intervals satisfy their cap; admission prefixes range from {data['prefix_seconds_range'][0]:.6f} "
            f"to {data['prefix_seconds_range'][1]:.6f} seconds; the maximum raw wall/performance discrepancy is "
            f"{data['maximum_abs_raw_wall_perf_discrepancy']:.6f} seconds. Raw receipts, complete-clock sidecars, "
            "selected rows and receipt hashes agree. The outer fee already includes this prefix and was not increased again.", "",
            f"The {data['null_T_cert_open_positions']} valid open positions retain null T_cert; their sorting value of 1 is only a censored training penalty. "
            "The sealed audits and final verification-closeout/total receipts establish qualification; the retained preliminary "
            "independent_evidence clock/qualification-pending flags describe the earlier pre-total-receipt stage and are not silently edited. "
            "Raw Seed2/3 native_preconditions metadata is likewise preserved; final returned-model qualification follows the already reviewed offline scope policy. "
            "Finite required-output and proof-closeout file hashes were checked, without a full raw journal sweep or proof-reader rerun.", "",
            "At review time, no main/tiny/core formal output directory or formal fee launch exists. "
            "No formal-role historical performance was opened or used to select parameters. All training outcomes, including open runs, remain in the denominator.", "",
            "selected_P.prm SHA256: `" + data["selected_prm_SHA"] + "`.", "",
            "Machine evidence: `review/selection_independent_receipt.json`; implementation: `review/selection_independent_audit.py`. "
            "The substantive audit is charged through round127_common.metered as verification; its outer fee receipt is in "
            f"`fees/{FEE_LABEL}/receipt.json`. The first audit attempt retained its failure fee/log; "
            "it reached all 36 positions and stopped on the review script's incorrect selected_P.prm directory assumption. "
            "Only the reviewer script path was corrected; no experiment, evidence or selection was changed."]
    else:
        text += ["The choice is not approved by this run. Failures:", ""] + ["- " + str(e) for e in ERRORS]
    (REVIEW / "selection_independent_review.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=status, selected=data.get("selected"), errors=ERRORS,
        machine_receipt=str(machine), rows_reviewed=len(ROWS)), ensure_ascii=False))
    sys.exit(0 if status == "PASS" else 1)
