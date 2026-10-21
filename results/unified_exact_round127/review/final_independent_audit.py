"""Independent, finite R127 final evidence audit. No solver/library imports.

PREPARED ONLY while formal work runs. Execution requires the parent's explicit
idle notice and --formal-idle-confirmed; the parent meters the complete command.
No primary selection, comparison, physical, LP or proof-reader function is used.
Previously completed all-36 independent selection evidence is bound, not rerun.
Outputs are unique per --attempt so a failed review is never overwritten.
"""
from pathlib import Path
from fractions import Fraction
import argparse
import ast
import collections
import csv
import datetime
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "results/unified_exact_round127"
SELECTION_COMMIT = "44ffd46367478dd784cc6a9595bfd3df174be8a7"
E0_SHA = "5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba"
E1_SHA = "d668236e9396b2e12f02bb65d9819b98762d2a35aad1b186d352d234dae756c9"
DLL_SHA = "9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88"
SELECTED_PRM_SHA = "e7cc6a9d9567f5f1b8d7c8887e5dfdf18f6632b8e97051583f2a2080c22e1f6f"
MAIN_IDS = ["SC-C15-S", "SC-B15-S", "SC-C15-B", "SC-B20-S", "SC-C20-S", "SC-B20-U"]
MAIN_CAPS = [600, 600, 600, 1200, 1200, 1200]
TINY_IDS = ["SM-C8-S", "SM-B10-B"]
CORE_IDS = ["SC-C15-S", "SC-B20-S", "PB-B35-B"]
CORE_ORDERS = [["P", "MR", "MB", "PT", "MD", "MG", "MS2"],
               ["MG", "PT", "MS2", "MB", "MR", "P", "MD"],
               ["MD", "MS2", "P", "MG", "PT", "MR", "MB"]]
CORE_PAIRS = {("MB", "P"), ("MB", "PT"), ("PT", "P"), ("MB", "MD"),
              ("MB", "MR"), ("MB", "MG"), ("MB", "MS2")}
TOL = 1e-7  # inherited numerical closure/physical policy, never a time tie
HASHES = {}
ARMS = []
ROOT_CALLS = {}
MAX_CHAIN_CALLS = 512
MAX_CHAIN_MODEL_BYTES = 512 * 1024 * 1024
MAX_CHAIN_OBSERVATION_BYTES = 128 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def table(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha(path):
    path = Path(path).resolve()
    key = str(path)
    if key not in HASHES:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        HASHES[key] = h.hexdigest()
    return HASHES[key]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def portable(value):
    value = str(value).replace("\\", "/")
    for marker in ["results/", "reference/", "scripts/", "src/", "include/"]:
        if marker in value:
            return ROOT / value[value.index(marker):]
    return Path(value) if Path(value).is_absolute() else ROOT / value


def close(a, b, tol=TOL):
    if a is None or b is None:
        return a is b
    return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a) - float(b)) <= tol


def git(*args):
    return subprocess.check_output(["git", "-c", "gc.auto=0", "-c", "maintenance.auto=false", *args], cwd=ROOT)


def config_file(path):
    result = {"MIPFocus": 0, "Cuts": -1}
    seen = set()
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        name, value = line.split()
        require(name in result and name not in seen, "unregistered/duplicate PRM entry")
        result[name] = int(value)
        seen.add(name)
    return result


def selection_bindings():
    """Bind the completed independent audit and the committed preformal choice."""
    names = ["tuning_selection.json", "selected_P.prm", "experiment_manifest.json", "input_manifest.json",
             "review/selection_independent_review.md", "review/selection_independent_receipt.json",
             "review/selection_independent_audit.py"]
    bindings = {}
    manifest_EOL_binding = None
    for name in names:
        relative = "results/unified_exact_round127/" + name
        committed = git("show", SELECTION_COMMIT + ":" + relative)
        if digest(committed) != sha(OUT / name):
            # This one pre-existing manifest was committed with LF, while its
            # original admitted working bytes are CRLF. Do not rewrite it or
            # relax exact binding for the selected file/PRM/other evidence.
            require(name == "experiment_manifest.json", "selection-era bytes changed: " + name)
            actual = (OUT / name).read_bytes()
            canonical, baseline = actual.replace(b"\r\n", b"\n"), committed.replace(b"\r\n", b"\n")
            require(b"\r" not in canonical and b"\r" not in baseline and canonical == baseline
                    and json.loads(actual) == json.loads(committed), "selection-era manifest differs beyond CRLF/LF")
            first_identity_path = OUT / "training/01_S12_S2_q0/identity.json"
            committed_selection = json.loads(git("show", SELECTION_COMMIT + ":results/unified_exact_round127/tuning_selection.json"))
            require(sha(first_identity_path) == committed_selection["all_rows"][0]["identity_SHA"]
                    and read(first_identity_path)["prereg_sha256"] == sha(OUT / name),
                    "actual manifest bytes not anchored by preselection training identity")
            manifest_EOL_binding = dict(actual_SHA=sha(OUT / name), selection_commit_blob_SHA=digest(committed),
                canonical_LF_SHA=digest(canonical), worktree_CRLF=actual.count(b"\r\n"), commit_CRLF=committed.count(b"\r\n"),
                canonical_text_and_JSON_equal=True, actual_manifest_bytes_unchanged_since_preselection=True,
                training_identity_SHA=sha(first_identity_path),
                training_identity_anchor="first training identity SHA in byte-exact committed tuning_selection.json; its prereg_sha256 binds actual CRLF manifest",
                source_or_evidence_rewritten=False, other_selection_files_still_byte_exact=True)
        bindings[name] = sha(OUT / name)
    earlier = read(OUT / "review/selection_independent_receipt.json")
    selected = read(OUT / "tuning_selection.json")
    require(earlier["status"] == "PASS" and len(earlier["rows"]) == 36
            and earlier["summary"]["all_36_retained"] is True, "completed all-36 independent review")
    require(earlier["summary"]["selected"] == selected["selected"]
            and selected["selected"]["id"] == "q2" and selected["evaluation_results_consulted"] == 0,
            "frozen q2 selection")
    require(sha(OUT / "selected_P.prm") == sha(OUT / "tuning_manifest/q2.prm") == SELECTED_PRM_SHA
            and config_file(OUT / "selected_P.prm") == {"MIPFocus": 2, "Cuts": -1}, "q2 bytes/settings")
    for name, expected in [("E0_SHA", E0_SHA), ("DLL_SHA", DLL_SHA)]:
        require(read(OUT / "experiment_manifest.json")[name] == expected, "layer identity: " + name)
    epoch = int(git("show", "-s", "--format=%ct", SELECTION_COMMIT).decode().strip())
    require(git("merge-base", "--is-ancestor", SELECTION_COMMIT, "HEAD") == b"", "selection commit ancestry")
    return dict(commit=SELECTION_COMMIT, commit_unix=epoch, bindings=bindings, manifest_git_EOL_binding=manifest_EOL_binding,
                independent_all36_review_reused=True, training_rerun=False, selected="q2", selected_prm_SHA=SELECTED_PRM_SHA)


def specifications(manifest, inputs):
    """Derive independent position/pair keys from the user's fixed panel tables."""
    require([p["id"] for p in manifest["E0_main"]] == MAIN_IDS, "six fixed main identities")
    require([p["cap_seconds"] for p in manifest["E0_main"]] == MAIN_CAPS, "fixed main caps")
    groups = []
    for j, p in enumerate(manifest["E0_main"], 1):
        methods = ["P", "MB"] if j % 2 else ["MB", "P"]
        require(["P" if x == "P-GRB" else "MB" for x in p["method_order"]] == methods, "main arm rotation")
        groups.append(dict(stage="main", name=f"main/{j:02d}_{p['id']}", id=p["id"], seed=1, repeat=1,
                           layer="E0", panel=p, methods=methods, pairs=[("MB", "P")]))
    tiny_roles = {p["id"]: p for p in inputs["tiny_roles"]}
    require(set(tiny_roles) == set(TINY_IDS), "two fixed tiny inputs")
    index = 0
    for j, ident in enumerate(TINY_IDS):
        p = tiny_roles[ident]
        require(p["cap_seconds"] == 90 and p["V"] == [8, 10][j] and p["Q_vector"] == [[20], [15, 25]][j]
                and p["T_seconds"] == [2400, 3600][j], "tiny physical specification")
        for seed in range(3):
            for repeat in (1, 2):
                methods = ["P", "MB"] if (j + seed) % 2 == 0 else ["MB", "P"]
                if repeat == 2:
                    methods = methods[::-1]
                declared = manifest["E0_tiny"][index]
                index += 1
                require((declared["group"], declared["role"]["id"], declared["seed"], declared["repeat"], declared["methods"])
                        == (index, ident, seed, repeat, methods), "tiny group rotation/unique key")
                groups.append(dict(stage="tiny", name=f"tiny/{index:02d}_{ident}_S{seed}_R{repeat}", id=ident,
                    seed=seed, repeat=repeat, layer="E0", panel=p, methods=methods, pairs=[("MB", "P")]))
    require(len(manifest["E0_tiny"]) == 12, "twelve fixed tiny pairs")
    for j, g in enumerate(manifest["E1_core"]):
        p = g["role"]
        require(p["id"] == CORE_IDS[j] and g["seed"] == 1 and g["methods"] == CORE_ORDERS[j]
                and p["cap_seconds"] == [600, 1200, 1200][j]
                and len(g["prespecified_pairs"]) == 7
                and set(map(tuple, g["prespecified_pairs"])) == CORE_PAIRS, "fixed core positions/pair keys")
        groups.append(dict(stage="core", name=f"core/{j + 1:02d}_{p['id']}", id=p["id"], seed=1, repeat=1,
            layer="E1", panel=p, methods=[m for m in g["methods"] if m != "MD"], pairs=list(map(tuple, g["prespecified_pairs"]))))
    require(len(manifest["E1_core"]) == 3, "three fixed core roles")
    return groups


def read_arm(group, launch, arm, identity, selection):
    d = portable(launch["destination"])
    p = launch["panel"]
    method = launch["method"]
    prefix = group["name"] + "/" + method
    require((arm["id"], arm["method"], arm["seed"], arm["repeat"], arm["binary_layer"])
            == (group["id"], method, group["seed"], group["repeat"], group["layer"]), prefix + ": arm key")
    require(launch["id"] == group["id"] and launch["seed"] == group["seed"] and launch["repeat"] == group["repeat"]
            and launch["binary_layer"] == group["layer"] and launch["cap_seconds"] == p["cap_seconds"], prefix + ": launch key")
    require(all(p[k] == group["panel"][k] for k in ["V", "M", "Q_vector", "T_seconds", "cap_seconds", "input_sha256"]), prefix + ": role identity")
    require(sha(portable(p["input_path"])) == p["input_sha256"] == arm["input_SHA"], prefix + ": original input bytes")
    expected_pe = E0_SHA if group["layer"] == "E0" else E1_SHA
    saved_sources = read(OUT / ("E0_identity.json" if group["layer"] == "E0" else "E1_frozen.json"))["source_bindings"]
    require(identity["candidate_binary_sha256"] == arm["PE_SHA"] == expected_pe
            and identity["dll_sha256"] == arm["DLL_SHA"] == DLL_SHA
            and identity["source_hashes"] == saved_sources
            and identity["prereg_sha256"] == sha(OUT / "experiment_manifest.json"), prefix + ": layer/DLL/source/protocol identity")
    origin = read(d / "child_process_origin.json")
    require(origin["PE_SHA"] == expected_pe and origin["command"] == launch["command"]
            and origin["creation_from_live_OS_handle"] is True and origin["seed"] == group["seed"], prefix + ": actual native identity")
    require(selection["commit_unix"] < origin["actual_creation_unix"], prefix + ": selection chronology")
    if group["layer"] == "E1":
        git("merge-base", "--is-ancestor", SELECTION_COMMIT, identity["measured_source_commit"])
    producer = read(d / "producer_receipt.json")
    seal = read(d / "producer_seal.json")
    total = read(d / "arm_total_receipt.json")
    closeout = read(d / "verification_closeout.json")
    audit = read(d / "audit.json")
    own = read(d / "independent_evidence.json")
    result = read(d / "result.json")
    completion = read(d / "completion.json")
    require(producer["producer_seal_SHA"] == sha(d / "producer_seal.json")
            and total["producer_receipt_SHA"] == closeout["producer_receipt_SHA"] == arm["producer_receipt_SHA"] == sha(d / "producer_receipt.json")
            and total["verification_closeout_SHA"] == sha(d / "verification_closeout.json"), prefix + ": split-clock seals")
    # All finite required producer outputs are hashed; raw journal files are not swept.
    for file, recorded in seal["required_SHA"].items():
        require(sha(d / file) == recorded, prefix + ": sealed output " + file)
    for field, file in [("audit_SHA", "audit.json"), ("own_evidence_SHA", "independent_evidence.json"),
                         ("claims_SHA", "native_claims.json"), ("rejection_SHA", "claim_rejections.json")]:
        require(closeout[field] == sha(d / file), prefix + ": proof closeout " + field)
    require(all(producer.get(k) is True for k in ["required_outputs_closed", "native_stopped_no_reentry"])
            and all(seal.get(k) is True for k in ["required_outputs_closed", "native_stopped_no_reentry", "necessary_producer_trailer_complete"])
            and total["necessary_verification_complete"] is True
            and closeout["necessary_verification_complete"] is True
            and closeout["no_new_solution_or_certificate_backfilled"] is True, prefix + ": complete sealed producer/verify")
    tprod, tverify = producer["T_produce"], total["T_verify"]
    require(close(tprod, producer["t_produce_perf"] - producer["t0_perf"], 1e-8)
            and close(tverify, total["t_verified_perf"] - producer["t_produce_perf"], 1e-8)
            and close(total["T_total"], tprod + tverify, 1e-8), prefix + ": actual monotonic split clocks")
    require(abs((producer["t_produce_unix"] - producer["t0_unix"]) - tprod) < .05
            and producer["t0_unix"] <= origin["actual_creation_unix"] <= completion["ended_unix"]
            <= producer["t_produce_unix"] <= total["t_verified_unix"], prefix + ": real wall intervals")
    require(0 < tprod <= launch["cap_seconds"] and producer["cap_seconds"] == launch["cap_seconds"], prefix + ": complete producer cap")
    require(all(close(arm[k], val, 1e-8) for k, val in [("T_produce", tprod), ("T_verify", tverify), ("T_total", tprod + tverify)]), prefix + ": published split clocks")
    qualified = all(arm.get(k) is True for k in ["formal_protocol_qualified", "numbers_qualified", "certificate_qualified"])
    qualified = qualified and arm.get("source_reduced") is False
    require(qualified and arm["actually_executed"] is True and arm["rejected_calls"] == []
            and audit["passed"] is True and audit["independent_evidence_audit_passed"] is True
            and closeout["native_proof_qualified"] is True, prefix + ": qualified versus source-reduced evidence")
    require(all(own.get(k) is True for k in ["own_physical_verified", "identity_verified", "input_verified",
            "model_domain_verified", "journal_verified", "return_verified", "files_verified"])
            and own["extra_after_production_solution_or_bound"] is False, prefix + ": own evidence gates")
    end = audit["endpoint"]
    certificate = bool(end["certificate"] or own["own_exact_zero"])
    require(arm["certificate"] is certificate and close(arm["U"], end["U"]) and close(arm["L"], end["L"])
            and close(arm["gap"], arm["U"] - arm["L"]), prefix + ": sealed endpoint/certificate")
    require(close(arm["T_cert"], tprod if certificate else None, 1e-8), prefix + ": no cap-imputed certification time")
    expected_settings = dict(read_return_code=0, Threads=1, Seed=group["seed"], Presolve=-1,
        MIPGap=0, MIPGapAbs=0, FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6)
    require(all(x == expected_settings for x in audit["actual_native_settings"]), prefix + ": actual frozen native readbacks")
    require(completion["returncode"] == 0 and completion["stop_reason"] == "normal_return" and completion["within_cap"] is True,
            prefix + ": observed native end")
    cold = None
    if method in ["P", "PT"]:
        require(result["gurobi_hga_start_requested"] is False and result["gurobi_hga_start_submitted"] is False
                and result["gurobi_native_domain_audit_passed"] is True and result["gurobi_lifecycle_valid"] is True
                and result["gurobi_model_count"] == result["gurobi_model_read_count"] == result["gurobi_optimize_count"] == 1,
                prefix + ": independent cold model")
        cold = sha(d / "compact.lp")
        require(cold == p["reference"]["canonical_sha256"] == result["gurobi_canonical_model_sha256"]
                == sha(d.parents[1] / f"reference/{group['id']}/original.lp"), prefix + ": compact identity")
        require("Loaded user MIP start" not in (d / "native.log").read_text(encoding="utf-8"), prefix + ": unexpected Start")
        if group["layer"] == "E1":
            wanted = {"MIPFocus": 2 if method == "PT" else 0, "Cuts": -1,
                "NumStart_before_optimize": 0, "loaded_after_presets": True, "authoritative_model_environment": True}
            require(read(d / "round127_parameters.json") == wanted, prefix + ": direct parameter/NumStart readback")
        command = launch["command"]
        require(("--round127-p-parameters" in command) == (method == "PT"), prefix + ": only PT gets tuning")
        if method == "PT":
            param_path = portable(command[command.index("--round127-p-parameters") + 1])
            require(sha(param_path) == SELECTED_PRM_SHA, prefix + ": frozen actual PRM")
    return dict(arm, _group=group["name"], _stage=group["stage"], _panel=p, _path=str(d),
        _producer=producer, _total=total, _origin=origin, _result=result, _cold_model_SHA=cold,
        _qualified=qualified, certificate=certificate, signed_gap=arm["U"] - arm["L"],
        absolute_gap=abs(arm["U"] - arm["L"]))


def closed_producing_fees(group, selection):
    """Exact registered wrapper fees, not an any-time/any-PID recovery fallback.

    Only the documented tiny07 resume has two producing wrapper candidates.
    A fee is a logical parent-admission marker, never an invented wrapper birth.
    All original/failed receipts remain separately bound and are not rewritten.
    """
    prefix = group["name"].replace("/", "_")
    labels = [prefix]
    if group["name"] == "tiny/07_SM-B10-B_S0_R1":
        labels.append(prefix + "_read_recovery01")
    require({p.name for p in (OUT / "fees").glob(prefix + "*") if p.is_dir()} == set(labels),
            "unexpected/missing producing-wrapper fee attempt: " + group["name"])
    expected_kind = {"main": "formal_E0_main", "tiny": "formal_E0_tiny", "core": "formal_E1_core"}[group["stage"]]
    fees = []
    for label in labels:
        d = OUT / "fees" / label
        require(all((d / n).is_file() for n in ["launch.json", "PID.json", "receipt.json"]), "producing-wrapper fee is not closed: " + label)
        launch, pid, end = (read(d / n) for n in ["launch.json", "PID.json", "receipt.json"])
        command = launch["command"]
        require(launch["kind"] == expected_kind and command == pid["command"]
                and len(command) == 4 and command[1:] == ["-B", "scripts/round127_campaign.py", group["name"]]
                and Path(command[0]).resolve() == Path("D:/msys64/ucrt64/bin/python.exe").resolve()
                and Path(launch["cwd"]).resolve() == ROOT.resolve(), "exact campaign wrapper fee command: " + label)
        require(type(pid["pid"]) is int and type(pid["parent_pid"]) is int
                and pid["launched_unix"] == end["start_unix"]
                and selection["commit_unix"] < pid["launched_unix"] < end["end_unix"]
                and end["exit_observed"] is True and end["nested_seconds_added"] is False
                and abs(end["end_unix"] - end["start_unix"] - end["outer_seconds"]) < .05,
                "actual closed parent-admission/exit interval: " + label)
        expected_exit = 1 if group["name"] == "tiny/07_SM-B10-B_S0_R1" and label == prefix else 0
        require(end["exit_code"] == expected_exit, "unregistered producing-wrapper failure/recovery: " + label)
        fees.append(dict(label=label, wrapper_pid=pid["pid"], parent_pid=pid["parent_pid"],
            parent_admission_unix=pid["launched_unix"], end_unix=end["end_unix"], exit_code=end["exit_code"],
            launch_SHA=sha(d / "launch.json"), PID_SHA=sha(d / "PID.json"), receipt_SHA=sha(d / "receipt.json"),
            failed_fee_retained=end["exit_code"] != 0))
    require(all(a["end_unix"] <= b["parent_admission_unix"] for a, b in zip(fees, fees[1:])), "nonoverlapping registered producing-wrapper attempts")
    return fees


def bind_producing_fee(group, launch, arm, fees):
    producer, native = arm["_producer"], arm["_origin"]
    matches = [f for f in fees if f["wrapper_pid"] == native["parent_pid"]
        and f["parent_admission_unix"] <= producer["t0_unix"] <= native["actual_creation_unix"]
        <= producer["t_produce_unix"] <= f["end_unix"]]
    require(len(matches) == 1, "native-parent PID and sealed production interval do not identify exactly one registered wrapper")
    fee = matches[0]
    first = launch["number"] == 1
    require(producer["first_arm_includes_wrapper_creation_and_import"] is first,
            "first-arm wrapper creation/import clock flag or later-arm admission flag changed")
    # Frozen campaign source maps logical arm 1 back to OS wrapper birth through
    # process_origin(), thereby including imports; later arms tick before input/
    # PE admission checks. The parent fee start remains a separate marker.
    require(producer["t0_unix"] < native["actual_creation_unix"], "producer clock must begin before native process creation")
    recovery = group["name"] == "tiny/07_SM-B10-B_S0_R1"
    if recovery:
        expected = group["name"].replace("/", "_") + ("" if launch["method"] == "MB" else "_read_recovery01")
        require(fee["label"] == expected, "tiny07 MB/P must bind original/resumed actual wrappers respectively")
    verify_after_original_exit = arm["_total"]["t_verified_unix"] > fee["end_unix"]
    if verify_after_original_exit:
        require(recovery and launch["method"] == "MB" and fee["failed_fee_retained"],
                "verification extends beyond its producing wrapper without the registered tiny07 recovery")
        focused = read(OUT / "review/tiny07_empty_route_attempts/empty02/receipt.json")
        saved = read(OUT / "review/tiny07_failure_snapshot/preservation.json")
        require(sha(OUT / "review/tiny07_empty_route_attempts/empty02/receipt.json")
                == "d9c8eba45ef70fd5318c57b262f16bfdc39390762c21094adcda53434fe1e90c"
                and focused["status"] == "PASS" and focused["full_reader_recovered"] is True
                and focused["final_qualification_pending"] is False
                and focused["original_T_produce"] == producer["T_produce"]
                and saved["producer_receipt_SHA"] == sha(Path(arm["_path"]) / "producer_receipt.json")
                and saved["producer_seal_SHA"] == sha(Path(arm["_path"]) / "producer_seal.json")
                and saved["original_native_creation"] == native
                and saved["failed_fee_receipt"] == read(OUT / "fees" / fee["label"] / "receipt.json"),
                "focused recovered-producer identity/qualification and retained original failed fee")
    return dict(group=group["name"], method=launch["method"], number=launch["number"], **fee,
        native_pid=native["pid"], native_actual_creation_unix=native["actual_creation_unix"],
        producer_start_unix=producer["t0_unix"], producer_seal_unix=producer["t_produce_unix"],
        first_arm_clock_scope="OS wrapper birth with imports per frozen process_origin source" if first else "logical later-arm admission before input/PE checks",
        original_T_produce=producer["T_produce"], original_T_verify=arm["T_verify"], original_T_total=arm["T_total"],
        verification_extends_beyond_original_producing_fee=verify_after_original_exit,
        clocks_or_cap_changed=False, fee_parent_prefix_added_to_production=False)


def collect(groups, selection):
    fee_bindings, retained_fees = [], []
    frozen_runner_SHA = digest(git("show", SELECTION_COMMIT + ":scripts/round127_campaign.py"))
    require(sha(ROOT / "scripts/round127_campaign.py") == frozen_runner_SHA, "formal runner/process_origin/admission clock source changed")
    for stage in ["main", "tiny", "core"]:
        expected = {g["name"].split("/", 1)[1] for g in groups if g["stage"] == stage}
        actual = {p.name for p in (OUT / stage).iterdir() if p.is_dir()}
        require(actual == expected, "exact formal group coverage: " + stage)
    for group in groups:
        camp = OUT / group["name"]
        identity = read(camp / "identity.json")
        reconstructed = read(camp / "reconstructed.json")
        launches, arms = identity["launches"], reconstructed["arms"]
        require([l["method"] for l in launches] == group["methods"]
                and len(arms) == len(launches), "actual frozen group method order/count")
        require(len({a["method"] for a in arms}) == len(arms), "duplicate actual arm")
        by = {a["method"]: a for a in arms}
        require(identity["runner_sha256"] == frozen_runner_SHA, "actual group runner/import/admission timing source binding")
        fees = closed_producing_fees(group, selection)
        retained_fees.extend(fees)
        previous = None
        for l in launches:
            a = read_arm(group, l, by[l["method"]], identity, selection)
            fee_bindings.append(bind_producing_fee(group, l, a, fees))
            if previous:
                require(previous["_total"]["t_verified_perf"] <= a["_producer"]["t0_perf"], "serial complete arms")
            previous = a
            ARMS.append(a)
    require(collections.Counter(a["_stage"] for a in ARMS) == {"main": 12, "tiny": 24, "core": 18}, "54 actual arms")
    require(len({(a["binary_layer"], a["id"], a["seed"], a["repeat"], a["method"]) for a in ARMS}) == 54, "54 unique typed actual arm keys")
    require(len({(a["_origin"]["pid"], a["_origin"]["actual_creation_unix"]) for a in ARMS}) == 54, "54 fresh native processes")
    cold = collections.defaultdict(set)
    for a in ARMS:
        if a["_cold_model_SHA"]:
            cold[a["input_SHA"]].add(a["_cold_model_SHA"])
    require(all(len(v) == 1 for v in cold.values()), "same-input P/PT cold model identity")
    return dict(actual_arms=54, per_stage={"main": 12, "tiny": 24, "core": 18},
        unique_native_creations=54, same_input_cold_groups=len(cold), all_54_split_clocks_caps_qualified=True,
        actual_producing_fee_bindings=fee_bindings, registered_wrapper_fees=retained_fees,
        failed_original_group_fee_retained=True, broad_wrapper_or_clock_fallback=False,
        E1_direct_NumStart0_readbacks=6,
        E0_cold_scope="fresh model/single Optimize, no requested/submitted/loaded Start; old PE does not serialize a direct NumStart attribute")


def paired(group, left, right):
    by = {a["method"]: a for a in ARMS if a["_group"] == group["name"]}
    a, b = by.get(left), by.get(right)
    row = dict(id=group["id"], panel={"main": "E0_main", "tiny": "E0_tiny", "core": "E1_core"}[group["stage"]],
        seed=group["seed"], repeat=group["repeat"] if group["stage"] == "tiny" else None,
        left=left, right=right, classification="UNEVALUABLE", direction="UNEVALUABLE", alias=False, nonalias_entry=True,
        binary_layer=group["layer"], left_T_cert=a["T_cert"] if a else None, right_T_cert=b["T_cert"] if b else None,
        left_minus_right_seconds=None, right_over_left_certification_ratio=None, legacy_materiality=None)
    if right == "MD":
        require(a is not None and b is None, "MD must stay blocked before formal")
        return row
    require(a and b and a["_qualified"] and b["_qualified"], "pair uses unqualified/missing evidence")
    require(a["PE_SHA"] == b["PE_SHA"] and a["DLL_SHA"] == b["DLL_SHA"]
            and a["input_SHA"] == b["input_SHA"] and a["seed"] == b["seed"], "within-layer matched pair identity")
    ac, bc = a["certificate"], b["certificate"]
    if ac and bc:
        require(close(a["U"], b["U"]), "own certified objective disagreement")
        dt = a["T_cert"] - b["T_cert"]  # deliberately unrounded, no tolerance tie
        row.update(classification="BOTH_CERTIFIED", direction="Win" if dt < 0 else "Lose" if dt > 0 else "Tie",
            left_minus_right_seconds=dt, right_over_left_certification_ratio=b["T_cert"] / a["T_cert"])
        threshold = max(30, .1 * b["T_cert"])
        row["legacy_materiality"] = "LEFT_MATERIALLY_FASTER" if dt <= -threshold else "RIGHT_MATERIALLY_FASTER" if dt >= threshold else "TIME_CLOSE"
    elif ac:
        row.update(classification="LEFT_ONLY_CERTIFIED", direction="Win")
    elif bc:
        row.update(classification="RIGHT_ONLY_CERTIFIED", direction="Lose")
    else:
        row.update(classification="BOTH_OPEN", direction="UNDETERMINED")
    if group["stage"] == "tiny":
        row["dt_ge_10_warning"] = row["left_minus_right_seconds"] >= 10 if row["classification"] == "BOTH_CERTIFIED" else None
        row["P_only_risk"] = row["classification"] == "RIGHT_ONLY_CERTIFIED"
    return row


def pair_summary(rows):
    nonalias = [r for r in rows if r["nonalias_entry"]]
    both = [r for r in nonalias if r["classification"] == "BOTH_CERTIFIED"]
    gm = math.exp(math.fsum(math.log(r["right_over_left_certification_ratio"]) for r in both) / len(both)) if both else None
    return dict(rows=len(rows), nonalias_typed_entries=len(nonalias),
        evaluable_nonalias_entries=sum(r["classification"] != "UNEVALUABLE" for r in nonalias),
        unevaluable_nonalias_entries=sum(r["classification"] == "UNEVALUABLE" for r in nonalias), alias_entries=len(rows) - len(nonalias),
        classes=dict(collections.Counter(r["classification"] for r in nonalias)), directions=dict(collections.Counter(r["direction"] for r in nonalias)),
        both_certified_intersection_n=len(both), both_certified_ids=[r["id"] for r in both], conditional_geometric_mean=gm)


def tiny_summary(rows):
    out = []
    for ident in TINY_IDS:
        rr = [r for r in rows if r["id"] == ident]
        require(len(rr) == 6 and {(r["seed"], r["repeat"]) for r in rr} == {(s, r) for s in range(3) for r in (1, 2)}, "all six tiny observations")
        dts = [r["left_minus_right_seconds"] for r in rr if r["classification"] == "BOTH_CERTIFIED"]
        median = statistics.median(dts) if dts else None
        count = sum(x >= 10 for x in dts)
        by = {str(seed): [r["left_minus_right_seconds"] for r in rr if r["seed"] == seed] for seed in range(3)}
        out.append(dict(id=ident, observations=6, both_certified_pairs=len(dts), median_dt=median,
            median_scope="all six pairs" if len(dts) == 6 else "explicit both-certified subset only",
            P_only_count=sum(r["classification"] == "RIGHT_ONLY_CERTIFIED" for r in rr), dt_ge10_count=count,
            at_least_one_ge10=count > 0, repeated_ge10=count >= 2, typical_median_ge10=median >= 10 if len(dts) == 6 else None,
            by_seed=by, per_seed_medians={s: statistics.median([x for x in v if x is not None]) if any(x is not None for x in v) else None for s, v in by.items()},
            per_seed_median_scope={s: "both observations" if all(x is not None for x in v) else "both-certified subset only" for s, v in by.items()}))
    return out


def compare_publication(groups):
    rows = {s: [paired(g, a, b) for g in groups if g["stage"] == s for a, b in g["pairs"]] for s in ["main", "tiny", "core"]}
    require([len(rows[s]) for s in rows] == [6, 12, 21], "39 predeclared typed pair entries")
    require(sum(r["classification"] == "UNEVALUABLE" for rr in rows.values() for r in rr) == 3, "three MD unevaluable typed entries")
    for stage, rr in rows.items():
        published = table(OUT / (stage + "_pairs.csv"))
        key = lambda r: (r["id"], int(r["seed"]), int(r["repeat"]) if r["repeat"] not in (None, "") else None, r["left"], r["right"])
        require(len(published) == len(rr) and len(set(map(key, published))) == len(rr)
                and set(map(key, published)) == set(map(key, rr)), "published exact pair keys " + stage)
        by = {key(r): r for r in published}
        for expected in rr:
            actual = by[key(expected)]
            for field in ["classification", "direction", "binary_layer"]:
                require(actual[field] == expected[field], "published pair " + field)
            require(actual["alias"] == "False" and actual["nonalias_entry"] == "True", "alias/nonalias denominator")
            for field in ["left_T_cert", "right_T_cert", "left_minus_right_seconds", "right_over_left_certification_ratio"]:
                val = float(actual[field]) if actual[field] else None
                # CSV binary64 round-trip must retain the actual unrounded arithmetic.
                require(val == expected[field], "published exact paired arithmetic: " + field)
            require(actual["legacy_materiality"] == (expected["legacy_materiality"] or ""), "legacy label is separate")
            if stage == "tiny":
                require(actual["dt_ge_10_warning"] == ("" if expected["dt_ge_10_warning"] is None else str(expected["dt_ge_10_warning"])), "exact tiny >=10 boundary")
    expected_summaries = {"main": pair_summary(rows["main"]), "tiny": pair_summary(rows["tiny"]),
        "core_by_comparison": {a + "/" + b: pair_summary([r for r in rows["core"] if (r["left"], r["right"]) == (a, b)]) for a, b in sorted(CORE_PAIRS)}}
    primary = read(OUT / "stratified_summary.json")
    for stage in ["main", "tiny"]:
        for k, v in expected_summaries[stage].items():
            require(close(primary[stage][k], v, 1e-12) if k == "conditional_geometric_mean" else primary[stage][k] == v, "published denominator/summary " + stage + "/" + k)
    require(set(primary["core_by_comparison"]) == {a + "/" + b for a, b in CORE_PAIRS}, "seven shared-record comparison types")
    for name, expected in expected_summaries["core_by_comparison"].items():
        for k, v in expected.items():
            require(close(primary["core_by_comparison"][name][k], v, 1e-12) if k == "conditional_geometric_mean" else primary["core_by_comparison"][name][k] == v, "published typed denominator " + name + "/" + k)
    tiny = tiny_summary(rows["tiny"])
    for expected in tiny:
        actual = next(r for r in primary["tiny_risks"] if r["id"] == expected["id"])
        for k, v in expected.items():
            if k not in ["per_seed_medians", "per_seed_median_scope"]:
                require(actual[k] == v, "published tiny median/threshold scope: " + k)
    require(primary["observed_formal_arms"] == 54 and primary["distinct_evaluation_inputs"] == 9
            and primary["distinct_training_inputs"] == 3 and primary["blocked_core_arms"] == 3
            and primary["PT_aliases"] == 0 and primary["all_observed_arms_qualified"] is True, "final scope counts")
    require(read(OUT / "PT_aliases.json") == [], "q2 has no aliases")
    blocked = read(OUT / "blocked_core_arms.json")
    require(len(blocked) == 3 and {(x["id"], x["method"]) for x in blocked} == {(x, "MD") for x in CORE_IDS}
            and all(x["status"] == "BLOCKED_BEFORE_FORMAL" and x["not_a_mechanism_negative"] is True for x in blocked), "MD mode-level block")
    hashes = {a["input_SHA"] for a in ARMS}
    training = {p["role"]["input_sha256"] for p in read(OUT / "experiment_manifest.json")["E1_training"]}
    require(len(hashes) == 9 and len(training) == 3 and not hashes & training, "9 evaluation versus 3 disjoint training identities")
    return dict(pairs=rows, summaries=expected_summaries, tiny=tiny,
        typed_entries=39, nonalias_entries=39, evaluable_entries=36, unevaluable_entries=3, aliases=0,
        unique_evaluation_inputs=9, unique_training_inputs=3,
        warning="Repeated Seeds/repeats, E0/E1 identities and shared MB/P core records remain typed entries; they are not 39 independent trials.")


def physical(panel, witness):
    """Own route/inventory/load/duration/objective arithmetic, no project reader."""
    source = portable(panel["input_path"]).read_text(encoding="utf-8-sig")
    arrays = {}
    for name in ["initial", "target", "capacities", "weights", "points"]:
        match = re.search(r"^\s*" + name + r"\s*=\s*(\[[^\n]*\])", source, re.M)
        require(match is not None, "physical input vector missing: " + name)
        arrays[name] = ast.literal_eval(match[1])
    n, cars = panel["V"], panel["M"]
    require(all(len(v) == n + 1 for v in arrays.values()), "physical input vector lengths")
    require(len(panel["Q_vector"]) == cars and all(x > 0 for x in arrays["target"][1:]), "physical Q/positive target domain")
    # The inherited parser normalizes legacy weights with maximum 10 to [0,1].
    weights = arrays["weights"]
    normalized = abs(max(weights[1:]) - 10) < 1e-6
    if normalized:
        weights = [x / 10 for x in weights]
    y = list(arrays["initial"])
    seen, vehicles, details = set(), set(), []
    for route in witness["routes"]:
        vehicle = route.get("vehicle", route.get("vehicle_id"))
        require(vehicle not in vehicles and isinstance(vehicle, int) and 0 <= vehicle < cars, "physical vehicle identity")
        vehicles.add(vehicle)
        nodes = route["nodes"]
        require(len(nodes) >= 2 and nodes[0] == nodes[-1] == 0 and all(isinstance(i, int) for i in nodes), "depot/route sequence")
        operations = {}
        for op in route["operations"]:
            station, pickup, drop = (op["station"], op["pickup"], op["drop"]) if isinstance(op, dict) else op
            require(station not in operations and pickup >= 0 and drop >= 0 and int(pickup) == pickup
                    and int(drop) == drop and bool(pickup) != bool(drop), "nonzero integer unidirectional service")
            operations[station] = (pickup, drop)
        require(len(nodes[1:-1]) == len(set(nodes[1:-1])) and set(nodes[1:-1]) == set(operations), "one station/one visit")
        load, pickups = 0, 0
        prefix_loads = []
        for station in nodes[1:-1]:
            require(1 <= station <= n and station not in seen, "global single station service")
            seen.add(station)
            pickup, drop = operations[station]
            load += pickup - drop
            pickups += pickup
            require(0 <= load <= panel["Q_vector"][vehicle], "prefix load/capacity")
            prefix_loads.append(load)
            y[station] += drop - pickup
            require(0 <= y[station] <= arrays["capacities"][station], "station final inventory/capacity")
        travel = math.fsum(math.hypot(arrays["points"][i][0] - arrays["points"][j][0],
            arrays["points"][i][1] - arrays["points"][j][1]) / 1.5 for i, j in zip(nodes, nodes[1:]))
        duration = travel + (panel["pickup_seconds"] + panel["drop_seconds"]) * pickups
        require(duration <= panel["T_seconds"] + TOL, "complete travel plus pickup/drop work duration")
        details.append(dict(vehicle=vehicle, Q=panel["Q_vector"][vehicle], pickups=pickups,
                            return_load=load, prefix_loads=prefix_loads, travel_seconds=travel, duration_seconds=duration))
    for vehicle in range(cars):
        if vehicle not in vehicles:
            details.append(dict(vehicle=vehicle, Q=panel["Q_vector"][vehicle], pickups=0,
                                return_load=0, prefix_loads=[], travel_seconds=0, duration_seconds=0, implicit_empty=True))
    require(sum(y[1:]) == sum(arrays["initial"][1:]) - sum(v["return_load"] for v in details), "stock conservation with loaded depot return")
    ratios = [y[i] / arrays["target"][i] for i in range(1, n + 1)]
    denominator = math.fsum(ratios)
    g = math.fsum(abs(x - z) for i, x in enumerate(ratios) for z in ratios[i + 1:]) / (n * denominator) if denominator > 0 else 0
    penalty = math.fsum(weights[i] * abs(ratios[i - 1] - 1) for i in range(1, n + 1))
    objective = g + panel["lambda"] * penalty
    reported = witness.get("F", witness.get("objective"))
    require(reported is not None and close(objective, reported), "independently replayed own physical F")
    for key, value in [("G", g), ("P", penalty)]:
        if key in witness:
            require(close(value, witness[key]), "independently replayed " + key)
    return dict(F=objective, G=g, P=penalty, Y=y, full_fleet_vehicles=cars, routes=details,
                legacy_weights_normalized=normalized, source_input_SHA=sha(portable(panel["input_path"])))


def representative_fleets(proof_arm):
    selected = []
    # Fixed role/method sampling; no fastest/best-result sample selection.
    for stage, ident, methods in [("main", MAIN_IDS[0], ["MB"]), ("tiny", TINY_IDS[0], ["MB"]),
                                  ("tiny", TINY_IDS[1], ["MB"]), ("core", CORE_IDS[0], ["P", "PT", "MB", "MR", "MG", "MS2"])]:
        for method in methods:
            selected.append(next(a for a in ARMS if a["_stage"] == stage and a["id"] == ident
                                 and a["method"] == method and (stage != "tiny" or (a["seed"], a["repeat"]) == (0, 1))))
    if proof_arm not in selected:
        selected.append(proof_arm)
    return [dict(group=a["_group"], method=a["method"], seed=a["seed"], repeat=a["repeat"],
                 result_SHA=sha(Path(a["_path"]) / "result.json"), replay=physical(a["_panel"], a["_result"])) for a in selected]


NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")
RELATION = re.compile(r"\s(<=|>=|=)\s(\S+)\s*$")


def model(path):
    """Independent exact-decimal parser for the archived one-line LP dialect."""
    columns, bounds, types, rows = set(), {}, {}, []
    objective, section = None, None
    def expression(text):
        tokens, index, sign = text.split(), 0, Fraction(1)
        coefficients, constant = collections.defaultdict(Fraction), Fraction(0)
        while index < len(tokens):
            token = tokens[index]
            if token in ["+", "-"]:
                sign = Fraction(1 if token == "+" else -1)
                index += 1
                require(index < len(tokens), "dangling LP sign")
                token = tokens[index]
            if NAME.fullmatch(token):
                columns.add(token); coefficients[token] += sign; index += 1
            else:
                value = Fraction(token) * sign
                index += 1
                if index < len(tokens) and NAME.fullmatch(tokens[index]):
                    columns.add(tokens[index]); coefficients[tokens[index]] += value; index += 1
                else:
                    constant += value
            sign = Fraction(1)
        return tuple(sorted((k, v) for k, v in coefficients.items() if v)), constant
    with Path(path).open(encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("\\"):
                continue
            if line in ["Minimize", "Subject To", "Bounds", "Generals", "Binaries", "End"]:
                section = line
            elif section == "Minimize":
                require(objective is None and line.startswith("obj:"), "one LP objective")
                objective = expression(line.split(":", 1)[1])
            elif section == "Subject To":
                body = line.split(":", 1)[1]
                relation = RELATION.search(body)
                require(relation is not None, "LP relation grammar")
                terms, constant = expression(body[:relation.start()])
                rows.append((terms, relation[1], Fraction(relation[2]) - constant))
            elif section == "Bounds":
                low, op, variable, op2, high = line.split()
                require(op == op2 == "<=" and variable not in bounds, "complete unique bound grammar")
                bounds[variable] = (Fraction(low), Fraction(high)); columns.add(variable)
            elif section in ["Generals", "Binaries"]:
                for variable in line.split():
                    require(NAME.fullmatch(variable) and variable not in types, "LP type uniqueness")
                    columns.add(variable); types[variable] = "I" if section == "Generals" else "B"
            else:
                raise ValueError("unsupported LP section/line")
    require(section == "End" and objective is not None and set(bounds) == columns
            and all(lo <= hi for lo, hi in bounds.values()), "complete LP model")
    return dict(objective=objective, rows=rows, bounds=bounds, types={n: types.get(n, "C") for n in columns})


def family(row):
    terms, relation, rhs = row
    c = dict(terms)
    names = set(c)
    p = {n for n in names if re.fullmatch(r"p_\d+_\d+", n)}
    z = {n for n in names if re.fullmatch(r"z_\d+_\d+", n)}
    d = {n for n in names if re.fullmatch(r"d_\d+_\d+", n)}
    h = {n for n in names if re.fullmatch(r"h_\d+_\d+", n)}
    r = {n for n in names if re.fullmatch(r"r_\d+", n)}
    e = {n for n in names if re.fullmatch(r"e_\d+", n)}
    if len(d) == 1 and p and names == d | p and relation == "<=" and rhs == 0 and all(c[n] == 1 for n in d) and all(c[n] == -1 for n in p):
        return "ordered_supply"
    if names == z and len(z) in [2, 3] and relation == "<=" and rhs == len(z) - 1 and all(c[n] == 1 for n in z):
        return "cover_" + str(len(z))
    if names == p | z and len(z) in [2, 3] and len(p) == len(z) and relation == "<=" and all(c[n] == 120 for n in p) and len({c[n] for n in z}) == 1:
        return "conditional_" + str(len(z))
    if "W_SP" in names:
        return "W_SP"
    if names == h | r and len(h) == 1 and relation == "<=" and rhs == 0:
        return "H_spread"
    if names == r and r and relation == "<=":
        return "fixed_centering" if len(r) == 2 else "variable_S_centering"
    if h and e and names == h | e and relation == "<=":
        return "linear_objective_estimator"
    return "UNEXPECTED"


def deletion(base, weak, method, n):
    require(base["objective"] == weak["objective"], "ablation changed objective")
    a, b = collections.Counter(base["rows"]), collections.Counter(weak["rows"])
    require(not b - a, "ablation adds/changes rows")
    removed = a - b
    auxiliary = {"W_SP", "r_min", "r_max"} if method == "MG" else set()
    require(set(base["types"]) - set(weak["types"]) == auxiliary and not set(weak["types"]) - set(base["types"]), "exact auxiliary column difference")
    require({k: v for k, v in base["types"].items() if k not in auxiliary} == weak["types"]
            and {k: v for k, v in base["bounds"].items() if k not in auxiliary} == weak["bounds"], "retained types/bounds/derived domains")
    counts = collections.Counter()
    for row, count in removed.items():
        counts[family(row)] += count
    allowed = {"MR": {"ordered_supply", "cover_2", "cover_3", "conditional_2", "conditional_3"},
               "MS2": {"cover_3", "conditional_3"},
               "MG": {"W_SP", "H_spread", "fixed_centering", "variable_S_centering", "linear_objective_estimator"}}[method]
    require(set(counts) <= allowed, "unexpected removed row family: " + str(counts))
    if method == "MG":
        require(sum(counts.values()) == 5 * math.comb(n, 2) + 6 and counts["W_SP"] == 5
                and counts["linear_objective_estimator"] == 1, "complete explicit Gini block difference")
    return dict(method=method, removed_rows=sum(removed.values()), removed_columns=sorted(auxiliary),
        families=dict(counts), retained_objective_bounds_types_and_duplicate_rows_identical=True,
        base_rows=len(base["rows"]), weak_rows=len(weak["rows"]), base_columns=len(base["types"]), weak_columns=len(weak["types"]))


def root_call(d):
    key = str(d)
    if key not in ROOT_CALLS:
        ROOT_CALLS[key] = None
        # H generates no unbounded list of native calls before the first root.
        # Only a bounded journal prefix is read here, never an all-file sweep.
        for seq in range(1, 257):
            path = Path(d) / "journal" / f"event_{seq}.json"
            if not path.exists():
                break
            event = read(path)
            if event["kind"] == "call":
                require(event["leaf"] == "L0", "first interval call is not root")
                require(sha(portable(event["model_path"])) == event["model_sha256"], "actual root model SHA")
                ROOT_CALLS[key] = event
                break
    return ROOT_CALLS[key]


def normalized_fleet(panel, witness):
    routes = {r.get("vehicle", r.get("vehicle_id")): r for r in witness["routes"]}
    result = []
    for capacity in sorted(set(panel["Q_vector"])):
        ids = [i for i, q in enumerate(panel["Q_vector"]) if q == capacity]
        values = []
        for vehicle in ids:
            r = routes.get(vehicle, dict(nodes=[0, 0], operations=[]))
            ops = {(o["station"] if isinstance(o, dict) else o[0]): (o["pickup"], o["drop"]) if isinstance(o, dict) else (o[1], o[2]) for o in r["operations"]}
            values.append(dict(nodes=r["nodes"], operations=[(i, *ops[i]) for i in r["nodes"][1:-1]]))
        result += [(capacity, v) for v in sorted(values, key=lambda v: json.dumps(v, sort_keys=True))]
    return result


def h_identity(a):
    d = Path(a["_path"])
    descent = table(d / "hga.csv.descent.csv")
    complete = {int(r["seed"]) for r in descent} == set(range(1, 26)) and not any(r.get("interrupted") == "1" for r in descent)
    final = read(d / "hga.csv.exchange/final.json")
    final_physical = physical(a["_panel"], final)
    csv_metadata = {"process_seconds", "elapsed_seconds", "elapsed", "timestamp", "wall_seconds"}
    json_metadata = {"sha256", "elapsed_seconds", "process_seconds", "wall_seconds", "timestamp", "path"}
    def strip(value):
        if isinstance(value, dict):
            return {k: strip(v) for k, v in value.items() if k not in json_metadata}
        if isinstance(value, list):
            return [strip(v) for v in value]
        return value
    traces = {}
    for p in sorted(d.glob("hga.csv.*.csv")):
        traces[p.name] = [{k: v for k, v in r.items() if k not in csv_metadata} for r in table(p)]
    for p in sorted((d / "hga.csv.exchange").iterdir()):
        key = "exchange/" + p.name
        if p.suffix == ".csv":
            traces[key] = [{k: v for k, v in r.items() if k not in csv_metadata} for r in table(p)]
        elif p.suffix == ".json":
            traces[key] = strip(read(p))
        elif p.suffix == ".jsonl":
            traces[key] = [strip(json.loads(s)) for s in p.read_text(encoding="utf-8").splitlines() if s]
    return dict(complete=complete, physical=final_physical, fleet=normalized_fleet(a["_panel"], final),
                traces_SHA=digest(json.dumps(traces, sort_keys=True, separators=(",", ":")).encode()))


def matrix_samples():
    """Finite qualification children and at most one actual exposed role per mode."""
    samples, formal, mismatches = [], [], []
    q = OUT / "qualification/exports/S12"
    for scope in ["root", "left", "right"]:
        base = model(q / scope / "mb/original.lp")
        for method in ["MR", "MG", "MS2"]:
            path = q / scope / method.lower() / "original.lp"
            require(sha(path) == read(path.parent / "build.json")["canonical_sha256"], "qualification archived model binding")
            samples.append(dict(scope="qualification_S12_" + scope, base_SHA=sha(q / scope / "mb/original.lp"),
                                weak_SHA=sha(path), **deletion(base, model(path), method, 12)))
    # MD remains only a functional qualification sample; never a formal arm.
    smoke = read(OUT / "qualification/smoke_E1/identity.json")
    md_by = {l["method"]: l for l in smoke["launches"]}
    md_calls = {m: root_call(portable(md_by[m]["destination"])) for m in ["MB", "MD"]}
    require(all(md_calls.values()), "retained MD functional root sample")
    mb, md = (model(portable(md_calls[m]["model_path"])) for m in ["MB", "MD"])
    require(mb == md, "MD qualification must keep the same static root model")
    md_sample = dict(scope="S12_functional_only_not_mathematical_admission", rows=len(mb["rows"]), columns=len(mb["types"]),
        identical_root_rows_columns_objective_types_bounds=True, generally_qualified=False,
        reason="inherited no-strict-improver equality closure conflicts with MD inclusive-root/own-U0-Start requirement")
    h_cache, mb_cache = {}, {}
    for method in ["MR", "MG", "MS2"]:
        chosen = None
        for ident in CORE_IDS:
            by = {a["method"]: a for a in ARMS if a["_stage"] == "core" and a["id"] == ident}
            base_arm, weak_arm = by["MB"], by[method]
            calls = [root_call(Path(a["_path"])) for a in [base_arm, weak_arm]]
            for a in [base_arm, weak_arm]:
                if a["_path"] not in h_cache:
                    h_cache[a["_path"]] = h_identity(a)
            hs = [h_cache[a["_path"]] for a in [base_arm, weak_arm]]
            matched = (all(calls) and all(h["complete"] for h in hs) and hs[0]["fleet"] == hs[1]["fleet"]
                and hs[0]["traces_SHA"] == hs[1]["traces_SHA"]
                and all(calls[0][k] == calls[1][k] for k in ["lower_g", "upper_g", "cutoff"]))
            if not matched:
                mismatches.append(dict(id=ident, method=method, H_complete=[h["complete"] for h in hs],
                    same_actions=hs[0]["traces_SHA"] == hs[1]["traces_SHA"], same_fleet=hs[0]["fleet"] == hs[1]["fleet"],
                    root_available=list(map(bool, calls)), status="UNKNOWN_H_OR_SCOPE_MISMATCH_NO_COMPONENT_ATTRIBUTION"))
                continue
            base_path, weak_path = [portable(c["model_path"]) for c in calls]
            if str(base_path) not in mb_cache:
                mb_cache[str(base_path)] = model(base_path)
            comparison = deletion(mb_cache[str(base_path)], model(weak_path), method, weak_arm["V"])
            if comparison["removed_rows"] == 0:
                mismatches.append(dict(id=ident, method=method, status="NO_DELETED_ROW_EXPOSURE_AT_MATCHED_ROOT"))
                continue
            chosen = dict(id=ident, method=method, matched_complete_H_actions_fleet_and_scope=True,
                base_SHA=sha(base_path), weak_SHA=sha(weak_path), lower_g=calls[0]["lower_g"], upper_g=calls[0]["upper_g"],
                cutoff=calls[0]["cutoff"], comparison=comparison)
            break
        formal.append(chosen or dict(method=method, status="NO_MATCHED_EXPOSED_FORMAL_ROOT_IN_PREDECLARED_ROLES"))
    return dict(qualification_root_and_child_checks=samples, MD_functional_only=md_sample,
                actual_exposed_formal_roots=formal, H_or_scope_mismatches=mismatches,
                scope="Exact serialized decimal Counter differences and retained domains for finite models; not a universal rational proof or new solve.")


def committed_event(d, row):
    event = row["payload"]
    seq = event["sequence"]
    path = d / "journal" / f"event_{seq}.json"
    require(read(path) == event and sha(path) == row["sha256"], "sampled event payload/hash")
    marker = (d / "journal" / f"event_{seq}.commit").read_text(encoding="utf-8").split()
    require(int(marker[1]) == seq and int(marker[3]) == path.stat().st_size and marker[4] == sha(path), "sampled event commit seal")


def scope_model(call, actual_model, panel):
    """Check the saved true-G domain, objective cutoff and frozen MB A/B links."""
    lo, hi, cutoff = call["lower_g"], call["upper_g"], call["cutoff"]
    require(close(float(actual_model["bounds"]["G"][0]), lo, 1e-12)
            and close(float(actual_model["bounds"]["G"][1]), hi, 1e-12), "proof model G scope")
    counter = collections.Counter(actual_model["rows"])
    terms, constant = actual_model["objective"]
    require(any(t == terms and rel == "<=" and close(float(rhs + constant), cutoff, 1e-10)
                for t, rel, rhs in actual_model["rows"]), "proof model own cutoff row")
    n, cars = panel["V"], panel["M"]
    for gamma, relation in [(lo, ">="), (hi, "<=")]:
        expected = {f"h_{i}_{j}": 1. for i in range(1, n + 1) for j in range(i + 1, n + 1)}
        if gamma:
            expected.update({f"r_{i}": -n * gamma for i in range(1, n + 1)})
        found = any(rel == relation and rhs == 0 and set(dict(t)) == set(expected)
            and all(close(float(v), expected[k], 1e-10) for k, v in t) for t, rel, rhs in actual_model["rows"])
        require(found, "proof actual true-G cap/floor")
    types = actual_model["types"]
    require(all(types[f"{name}_{k}_{i}"] == "C" for name in ["p", "d"] for k in range(cars) for i in range(1, n + 1)), "frozen continuous quantities")
    require(all(types[name] in ["I", "B"] for name in types if name.startswith(("x_", "load_", "Y_"))), "frozen route/load/Y integrality")
    require(all(types[name] == "B" for name in types if name.startswith(("mode_", "z_", "state_")) and not name.startswith("state_g_")), "frozen direction/state binaries")
    text = portable(panel["input_path"]).read_text(encoding="utf-8-sig")
    initial = ast.literal_eval(re.search(r"^\s*initial\s*=\s*(\[[^\n]*\])", text, re.M)[1])
    for i in range(1, n + 1):
        a = {f"{q}_{k}_{i}": Fraction(1) for q in ["p", "d"] for k in range(cars)}
        for name in types:
            if re.fullmatch("state_" + str(i) + r"_\d+", name):
                amount = abs(initial[i] - int(name.rsplit("_", 1)[1]))
                if amount:
                    a[name] = Fraction(-amount)
        b = {f"z_{k}_{i}": Fraction(1) for k in range(cars)}
        if f"state_{i}_{initial[i]}" in types:
            b[f"state_{i}_{initial[i]}"] = Fraction(1)
        require(counter[(tuple(sorted(a.items())), "=", Fraction(0))] >= 1
                and counter[(tuple(sorted(b.items())), "=", Fraction(1))] >= 1, "frozen A/B links")


def interval_support(lo, hi, proofs):
    require(0 <= lo <= hi, "physical true-G interval")
    endpoints = sorted({lo, hi, *[x for p in proofs for x in [p["lo"], p["hi"]] if lo < x < hi]})
    pieces = list(zip(endpoints, endpoints[1:])) or [(lo, hi)]
    support = math.inf
    for left, right in pieces:
        candidates = [min(p["value"], p["cutoff"]) for p in proofs if p["lo"] <= left + 1e-12 and p["hi"] + 1e-12 >= right]
        # F>=G is the independent nonnegative penalty floor on this subinterval.
        support = min(support, max([left] + candidates))
    return support


def proof_chain(sample):
    """One nonzero MB certificate: raw returns -> actual models -> complete cover.

    Local callback values retain their raw global flags. Offline mathematical
    scope qualification is based on the linked returned original model; no raw
    callback is rewritten into an online global claim. Cutoff complements bound
    only min(local_bound,cutoff), under the retained numerical closure contract.
    """
    d, panel = Path(sample["_path"]), sample["_panel"]
    observation_path = d / "observations.json"
    require(observation_path.stat().st_size <= MAX_CHAIN_OBSERVATION_BYTES, "representative observation bound exceeded")
    observations = read(observation_path)
    require(all(r["payload"]["sequence"] == i for i, r in enumerate(observations, 1)), "representative journal sequence")
    calls = {r["payload"]["call"]: r["payload"] for r in observations if r["payload"]["kind"] == "call"}
    returned = {r["payload"]["call"]: r["payload"]["sequence"] for r in observations if r["payload"]["kind"] == "returned"}
    skipped = {r["payload"]["call"] for r in observations if r["payload"]["kind"] == "not_started"}
    require(len(calls) == sum(r["payload"]["kind"] == "call" for r in observations)
            and len(returned) == sum(r["payload"]["kind"] == "returned" for r in observations)
            and len(skipped) == sum(r["payload"]["kind"] == "not_started" for r in observations), "unique native call dispositions")
    require(len(calls) <= MAX_CHAIN_CALLS and set(returned).isdisjoint(skipped)
            and set(returned) | skipped == set(calls), "finite complete call dispositions")
    ledger = table(d / "external/paper_optimize_ledger.csv")
    actual = [c for cid, c in calls.items() if cid not in skipped]
    require(len(actual) == len(ledger) == sample["native_Optimize"], "actual returned Optimize ledger count")
    views = read(d / "call_log_views.json")["bindings"]
    require(len(views) == len(actual) and len({v["call"] for v in views}) == len(actual), "one bound log view per actual call")
    bindings = {v["call"]: v for v in views}
    lp_status = table(d / "external/lp_status_ledger.csv")
    require(len(lp_status) == sum(row["solve_kind"] == "LP" for row in ledger), "all complete LP returns linked")
    lp_index, total_model_bytes, facts, returned_proofs = 0, 0, {}, {}
    models, logs, native_records = collections.OrderedDict(), {}, []
    unique_models = {c["model_sha256"]: portable(c["model_path"]) for c in actual}
    require(sum(p.stat().st_size for p in unique_models.values()) <= MAX_CHAIN_MODEL_BYTES, "representative finite model-byte bound exceeded")
    wanted_settings = dict(read_return_code=0, Threads=1, Seed=sample["seed"], Presolve=-1,
        MIPGap=0, MIPGapAbs=0, FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6)
    for ordinal, (call, row) in enumerate(zip(actual, ledger), 1):
        cid = call["call"]
        require(call["settings"] == wanted_settings and not call["full_original"]
                and call["model_scope"] == "complete_original_compact_milp_intersected_with_static_gini_interval", "original interval/settings provenance")
        require(row["leaf_id"] == call["leaf"] and row["model_sha256"] == call["model_sha256"]
                and int(row["optimize_return_code"]) == 0 and cid in returned, "returned call/model/leaf linkage")
        require(observations[returned[cid] - 1]["payload"]["return_code"] == 0, "successful journal return")
        committed_event(d, observations[call["sequence"] - 1])
        committed_event(d, observations[returned[cid] - 1])
        path = portable(call["model_path"])
        require(sha(path) == call["model_sha256"], "representative immutable model bytes")
        if call["model_sha256"] in models:
            m = models.pop(call["model_sha256"])
        else:
            m = model(path)
            scope_model(call, m, panel)
        models[call["model_sha256"]] = m
        while len(models) > 2:
            models.popitem(last=False)
        binding = bindings[cid]
        require(binding["serial_ordinal"] == ordinal and binding["model_SHA"] == call["model_sha256"]
                and binding["leaf"] == call["leaf"] and binding["true_G_interval"] == [call["lower_g"], call["upper_g"]]
                and binding["cutoff"] == call["cutoff"] and binding["journal_returned"] is True
                and binding["return_sequence"] == returned[cid], "per-call byte view binding")
        log_path = portable(binding["raw_log"])
        require(log_path == portable(call["native_log_path"]) == portable(row["native_log"]), "actual serial log path")
        if str(log_path) not in logs:
            require(log_path.stat().st_size <= MAX_CHAIN_OBSERVATION_BYTES, "bounded native log")
            logs[str(log_path)] = log_path.read_bytes()
        data = logs[str(log_path)]
        part = data[binding["byte_begin"]:binding["byte_end"]]
        require(digest(data) == binding["raw_log_SHA"] and digest(part) == binding["segment_SHA"], "native original byte interval SHA")
        text = part.decode("utf-8")
        header = re.search(r"Optimize a model with (\d+) rows, (\d+) columns", text)
        require(header is not None and (int(header[1]), int(header[2])) == (len(m["rows"]), len(m["types"])), "actual original model dimensions")
        require(part.count(b"Optimize a model with ") == 1, "unique Optimize in bound log segment")
        source = None
        value = None
        if row["solve_kind"] == "LP":
            s = lp_status[lp_index]
            lp_index += 1
            require(s["leaf_id"] == call["leaf"] and s["native_status"] == row["native_status"]
                    and close(float(s["gamma_L"]), call["lower_g"], 1e-12)
                    and close(float(s["gamma_U"]), call["upper_g"], 1e-12)
                    and int(row["integer_domain_restored"]) == 1, "complete LP model/return/restored native types")
            require(binding["native_types"] == {"C": len(m["types"]), "I": 0, "B": 0}, "actual LP-relaxed variable types")
            if int(s["terminal_valid"]) and int(s["optimal"]) and int(s["bound_available"]):
                value, source = float(s["lower_bound"]), "linked_complete_optimal_LP"
                printed = re.findall(r"Optimal objective\s+([-+0-9.eE]+)", text)
                require(printed and close(float(printed[-1]), value), "actual LP optimum print/readback")
            elif int(s["terminal_valid"]) and int(s["infeasible"]):
                require("infeasible" in text.lower(), "actual LP infeasibility return")
                value, source = call["cutoff"], "linked_complete_LP_infeasible_no_improver"
        else:
            types = re.search(r"Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)", text)
            counted = collections.Counter(m["types"].values())
            require(types is not None and (int(types[1]), int(types[2]) - int(types[3]), int(types[3]))
                    == (counted["C"], counted["I"], counted["B"]), "actual original MIP variable types")
            if row["native_status"] == "INFEASIBLE":
                require("Infeasible model" in text or "Model is infeasible" in text, "actual MIP infeasibility return")
                value, source = call["cutoff"], "linked_returned_MIP_infeasible_no_improver"
            else:
                printed = re.findall(r"Best objective [^,]+, best bound ([^,]+), gap", text)
                if printed:
                    candidate = float(printed[-1])
                    if math.isfinite(candidate) and abs(candidate) < 1e90:
                        value, source = candidate, "linked_returned_original_MIP_bound"
                if row["native_status"] == "OPTIMAL":
                    require("Optimal solution found" in text and value is not None, "actual optimal native MIP return")
        for parameter, observed in re.findall(r"(?m)^(Threads|Seed|Presolve|MIPGap|MIPGapAbs|FeasibilityTol|IntFeasTol|OptimalityTol)\s+([-+0-9.eE]+)\s*$", text):
            require(float(observed) == wanted_settings[parameter], "actual printed native parameter")
        facts[cid] = dict(is_LP=row["solve_kind"] == "LP", call=call, return_sequence=returned[cid])
        if value is not None:
            require(math.isfinite(value), "finite qualified local proof value")
            returned_proofs[cid] = dict(call=cid, lo=call["lower_g"], hi=call["upper_g"], cutoff=call["cutoff"],
                value=value, sequence=returned[cid], source=source, model_SHA=call["model_sha256"], raw_native_preconditions=call["native_preconditions"])
        native_records.append(dict(call=cid, leaf=call["leaf"], solve_kind=row["solve_kind"], model_SHA=call["model_sha256"],
            actual_model_rows=len(m["rows"]), actual_model_columns=len(m["types"]), return_sequence=returned[cid],
            native_log_SHA=binding["raw_log_SHA"], native_segment_SHA=binding["segment_SHA"], proof=returned_proofs.get(cid)))
    # Independent chronological support checks for each saved call cover.
    available, call_covers, callback_count, checked_bound_sequences = {}, [], 0, set()
    def check_callback_origins():
        for p in available.values():
            if p["source"] == "own_committed_local_MIP_callback_bound" and p["sequence"] not in checked_bound_sequences:
                committed_event(d, observations[p["sequence"] - 1])
                checked_bound_sequences.add(p["sequence"])
    for record in observations:
        e = record["payload"]
        kind = e["kind"]
        if kind == "call":
            check_callback_origins()
            pieces = []
            for leaf in e["cover"]:
                supported = interval_support(leaf["lower_g"], leaf["upper_g"], list(available.values()))
                require(min(leaf["lower"], leaf["cutoff"]) <= supported + TOL, "future/unsupported saved call-cover bound")
                pieces.append(dict(id=leaf["id"], reported=leaf["lower"], cutoff=leaf["cutoff"], supported=supported))
            call_covers.append(dict(call=e["call"], sequence=e["sequence"], leaves=pieces, future_evidence_used=False))
        elif kind == "bound" and e["call"] in facts and not facts[e["call"]]["is_LP"]:
            value = e.get("native_bound")
            if value is not None and math.isfinite(value) and abs(value) < 1e90:
                require(not e["inconsistent"], "inconsistent native callback in representative proof")
                c = calls[e["call"]]
                p = dict(call=e["call"], lo=c["lower_g"], hi=c["upper_g"], cutoff=c["cutoff"], value=value,
                         sequence=e["sequence"], source="own_committed_local_MIP_callback_bound")
                if e["call"] not in available or value > available[e["call"]]["value"]:
                    available[e["call"]] = p
                callback_count += 1
        elif kind == "returned" and e["call"] in returned_proofs:
            p = returned_proofs[e["call"]]
            if e["call"] not in available or p["value"] > available[e["call"]]["value"]:
                available[e["call"]] = p
    check_callback_origins()
    leaves = table(d / "external/paper_leaf_ledger.csv")
    live = [r for r in leaves if r["status"] not in ["replaced", "coalesced"]]
    trace = table(d / "external/global_bound_trace.csv")
    require(live and trace, "actual complete final frontier/trace")
    covered, supported_leaves = 0., []
    for leaf in sorted(live, key=lambda r: float(r["gamma_L"])):
        lo, hi, lower = (float(leaf[k]) for k in ["gamma_L", "gamma_U", "lower_bound"])
        require(0 <= lo <= hi and lo <= covered + TOL and leaf["status"] != "invalid", "complete physical true-G coverage")
        covered = max(covered, hi)
        support = interval_support(lo, hi, list(available.values()))
        require(min(lower, sample["U"]) <= support + TOL, "unsupported final leaf bound")
        discharged = leaf["status"] in ["closed", "fathomed", "empty"] or lo >= sample["U"] - TOL or lower >= sample["U"] - TOL
        require(discharged, "certificate retains unresolved relevant leaf")
        supported_leaves.append(dict(id=leaf["leaf_id"], lo=lo, hi=hi, raw_lower=lower, independent_support=support,
            status=leaf["status"], lower_bound_sources=leaf["lower_bound_sources"], closure_source=leaf["closure_source"]))
    require(covered + TOL >= min(sample["U"], (panel["V"] - 1) / panel["V"]), "full relevant G domain covered")
    previous_l, previous_u = -math.inf, math.inf
    for row in trace:
        upper = float(row["verified_global_upper_bound"])
        candidates = [upper] + [float(row[k]) for k in ["active_leaf_valid_lower_bound", "other_open_leaf_min_valid_lower_bound"] if row[k] != ""]
        lower = float(row["valid_global_lower_bound"])
        require(close(lower, min(candidates)) and lower >= previous_l - TOL and upper <= previous_u + TOL, "actual global cover trace aggregation/monotonicity")
        previous_l, previous_u = lower, upper
    relevant = [r for r in live if float(r["gamma_L"]) < previous_u - TOL]
    raw_l = min((float(r["lower_bound"]) for r in relevant), default=0.)
    require(close(raw_l, sample["L"]) and close(previous_u, sample["U"])
            and close(previous_l, min(previous_u, raw_l)), "raw complete endpoint versus clipped observational trace")
    replay = physical(panel, sample["_result"])
    require(close(replay["F"], sample["U"]) and sample["U"] > 1e-12 and sample["U"] - raw_l <= TOL
            and sample["certificate"] is True and actual, "nonzero native certificate obligations")
    return dict(group=sample["_group"], method="MB", U=sample["U"], raw_L=raw_l, signed_gap=sample["U"] - raw_l,
        nonzero=True, native_calls=len(actual), returned_original_model_proofs=len(returned_proofs), native_records=native_records,
        unique_models=len(unique_models), unique_model_bytes=sum(p.stat().st_size for p in unique_models.values()),
        chronological_saved_call_covers=call_covers, callback_local_bound_records=callback_count,
        covered_G_upper=covered, live_leaves=supported_leaves, physical_endpoint=replay,
        raw_leaf_ledger_SHA=sha(d / "external/paper_leaf_ledger.csv"), global_trace_SHA=sha(d / "external/global_bound_trace.csv"),
        raw_online_flags_unchanged=True, cutoff_complement_rule="min(local bound, own cutoff); retained tolerance policy, not inclusive-root/U0-Start preservation",
        scope="One complete actual interval/returned-call proof chain independently checked at serialized numerical precision; no universal rational certificate or new optimization.")


def source_bindings():
    counts = {}
    for layer, name, field in [("E0", "E0_identity.json", "production_PE_SHA"), ("E1", "E1_frozen.json", "PE_SHA")]:
        saved = read(OUT / name)
        require(saved[field] == (E0_SHA if layer == "E0" else E1_SHA) and saved["DLL_SHA"] == DLL_SHA, "source identity layer")
        for path, recorded in saved["source_bindings"].items():
            current = ROOT / path
            if sha(current) != recorded:
                current = OUT / "source_E0" / path
            require(sha(current) == recorded, "frozen source byte binding " + layer + ":" + path)
        counts[layer] = len(saved["source_bindings"])
    admission = read(OUT / "review/performance_admission.json")
    require(set(admission["qualified_methods"]) == {"P", "PT", "MB", "MR", "MG", "MS2"}
            and admission["blocked_methods"] == ["MD"], "mode-level mathematical admission")
    require(sha(OUT / "qualification/admission_summary.json") == read(OUT / "E1_frozen.json")["qualification_summary_SHA"], "frozen finite admission evidence")
    return dict(source_files_per_layer=counts, Cpp_and_binary_identity_unchanged=True,
        MD_blocked=True, MD_math_review_SHA=sha(OUT / "review/preformal_cutoff_boundary_review.md"),
        scope="MD's inclusive-root/equal-U0 Start obligation fails the inherited no-strict-improver boundary; this does not revoke frozen MB or other admitted modes wholesale.")


def arm_publication():
    fields = ["T_cert", "T_produce", "T_verify", "T_total", "U", "L", "signed_gap", "absolute_gap"]
    for stage in ["main", "tiny", "core"]:
        actual = table(OUT / (stage + "_arms.csv"))
        key = lambda r: (r["id"], r["method"], int(r["seed"]), int(r["repeat"]), r["binary_layer"])
        expected = [a for a in ARMS if a["_stage"] == stage]
        require(len(actual) == len(expected) and len({key(a) for a in actual}) == len(actual)
                and set(map(key, actual)) == set(map(key, expected)), "published 54 arm keys")
        by = {key(a): a for a in actual}
        for a in expected:
            row = by[key(a)]
            for field in fields:
                val = float(row[field]) if row[field] else None
                require(val == a[field], "published endpoint/time round trip " + field)
            require(row["certificate"] == str(a["certificate"]) and row["source_reduced"] == "False"
                    and row["formal_protocol_qualified"] == row["numbers_qualified"] == row["certificate_qualified"] == "True",
                    "published qualification/source reduction")
    return dict(published_arm_rows=54, exact_unrounded_time_and_gap_columns=True, source_reduced_rows=0)


def execute(args):
    tick = time.perf_counter()
    output = OUT / "review/final_independent_attempts" / args.attempt
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(schema="round127-final-independent-finite-audit-v1", status="RUNNING",
        UTC_started=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        reviewer="qualification_reviewer, separate executor; not third-party replication",
        execution_authority="Parent explicitly confirmed formal processes idle before this invocation",
        verification_fee_label=args.fee_label, script_SHA=sha(__file__), no_Optimize=True, no_build=True, no_native_rerun=True,
        sections={}, errors=[], bounds=dict(max_chain_calls=MAX_CHAIN_CALLS, max_chain_model_bytes=MAX_CHAIN_MODEL_BYTES,
            max_chain_observation_bytes=MAX_CHAIN_OBSERVATION_BYTES, final_fleets_at_most=10,
            matrix_scope="S12 qualification root/left/right MR/MG/MS2, S12 MD functional root, at most one matched exposed formal role per MR/MG/MS2"),
        exclusions=["no fresh native solve/LP", "no all-journal-file sweep for all arms", "no all-matrix rational proof",
                    "no training reselection", "no manuscript/PDF review before generation"])
    def step(name, function):
        start = time.perf_counter()
        result = function()
        receipt["sections"][name] = result
        print(json.dumps(dict(section=name, status="PASS", seconds=time.perf_counter() - start)), flush=True)
        return result
    try:
        selection = step("committed_independent_selection", selection_bindings)
        step("frozen_source_and_admission", source_bindings)
        manifest, inputs = read(OUT / "experiment_manifest.json"), read(OUT / "input_manifest.json")
        groups = specifications(manifest, inputs)
        step("54_actual_sealed_arms_and_split_clocks", lambda: collect(groups, selection))
        step("54_published_arm_rows", arm_publication)
        step("39_predeclared_typed_pair_entries", lambda: compare_publication(groups))
        step("finite_mode_root_and_child_matrices", matrix_samples)
        # Predeclared sample rule: first formal MB in fixed group/arm order with
        # nonzero own certified F and actual native work. Never the fastest run.
        proof_arm = next((a for a in ARMS if a["method"] == "MB" and a["certificate"]
                          and a["U"] > 1e-12 and a["native_Optimize"] > 0), None)
        require(proof_arm is not None, "no nonzero native MB certificate available for the required proof sample")
        step("bounded_physical_fleet_replays", lambda: representative_fleets(proof_arm))
        step("one_complete_nonzero_MB_native_cover_chain", lambda: proof_chain(proof_arm))
        receipt["status"] = "PASS"
    except Exception as exc:
        receipt["status"] = "FAIL"
        receipt["errors"].append(dict(type=type(exc).__name__, message=str(exc)))
    receipt["UTC_completed"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt["seconds"] = time.perf_counter() - tick
    receipt["inspected_file_SHA"] = HASHES
    receipt["scope"] = ("All current formal endpoint/seal/clock and typed arithmetic evidence; bounded independent physical, "
        "serialized-model and one complete actual nonzero MB proof/cover replay. Existing full native reader qualification is retained. "
        "Shared arms and repeated Seeds are not independent trials. The MD qualification block is preserved; "
        "this review does not claim universal exact arithmetic or blanket invalidity of MB.")
    (output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    text = ["# Final independent finite Round127 audit", "", "Status: " + receipt["status"] + ".", "",
        receipt["scope"], "", "The audit calls no primary selection/comparison/physical/model/proof reader. "
        "It executes only after the parent's idle confirmation and is charged as verification. "
        "All failed attempts and original experimental fees remain preserved.", ""]
    if receipt["status"] == "PASS":
        text += ["All 54 actual arms retain qualified, sealed endpoints and complete split clocks within their caps. "
            "The independently reviewed q2 selection and its bytes are committed before every formal launch. "
            "The 39 typed entries consist of 36 evaluable comparisons and 3 MD UNEVALUABLE entries, with no alias. "
            "Nine evaluation identities remain separate from the three training identities.", "",
            "Certification-only ratios and unrounded directions match the published tables. Tiny >=10-second flags, "
            "per-Seed differences/medians and all-six versus explicitly censored-subset medians are independently recomputed "
            "in the machine receipt. No cap substitutes for missing T_cert or a censored ratio.", "",
            "Finite matrix differences, H/scope mismatches or missing exposure, complete physical vehicle replays and "
            "the representative nonzero MB returned-call/true-G-cover chain are recorded separately below sections in the machine receipt. "
            "MD remains blocked on its mode-specific inclusive-root/own-U0-Start requirement; no mechanism ineffectiveness claim follows from that block.", ""]
    else:
        text += ["This attempt does not close the final audit gate. Findings:", ""] + ["- " + x["type"] + ": " + x["message"] for x in receipt["errors"]] + [""]
    text += ["Machine receipt: `receipt.json`. Script SHA256: `" + receipt["script_SHA"] + "`.", "",
             "Manuscript and rendered PDF review follows their generation and is outside this machine evidence gate."]
    (output / "review.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=receipt["status"], attempt=args.attempt, output=str(output), errors=receipt["errors"], seconds=receipt["seconds"])), flush=True)
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formal-idle-confirmed", action="store_true", help="Only use after the parent's explicit idle notification")
    parser.add_argument("--attempt", required=True, help="Unique review attempt name; prior attempts are never overwritten")
    parser.add_argument("--fee-label", required=True, help="Outer round127_common.metered verification fee label")
    arguments = parser.parse_args()
    require(arguments.formal_idle_confirmed, "Do not execute while formal processes are active")
    require(re.fullmatch(r"[a-z0-9_-]{1,64}", arguments.attempt), "safe unique review attempt name")
    sys.exit(execute(arguments))
