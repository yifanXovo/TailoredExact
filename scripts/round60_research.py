"""Bounded, serial Round 60 execution; never launches a historical panel."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_verified_candidate_native_round60"
RAW = OUT / "local_raw"
PANEL59 = ROOT / "results/gf_core_attribution_native_round59/panel.json"
EXE = ROOT / "build/round60-dev/ExactEBRP.exe"
FIXED_EXE = ROOT / "build/round60-dev/Round50IntervalMipExperiment.exe"
LEDGER = OUT / "processes.jsonl"
MAX_PROCESSES = 72
MANUAL_NATIVE_MICRO_PROCESSES = 5


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def panel_rows():
    rows = json.loads(PANEL59.read_text(encoding="utf-8"))["panel"]
    return {row["id"]: row for row in rows}


def freeze():
    target = OUT / "protocol.json"
    if target.exists():
        raise RuntimeError("Round 60 protocol is already frozen")
    panel = panel_rows()
    selected = []
    for identity in ["D1", "D2", "D3", "D4", "D6", "D7", "C1", "C2"]:
        row = dict(panel[identity])
        if identity == "C2":
            row["round60_role"] = "development_real_split_attribution"
            row["stage"] = "development"
        selected.append(row)
    write_json(target, {
        "schema": "round60-frozen-protocol-v1",
        "base_commit": "12cec3924a6852d4b36d954acbb5e9b20000c9c5",
        "branch": "codex/round60-verified-candidate-native-injection",
        "panel": selected,
        "solver": {
            "engine": "Gurobi 13.0.2",
            "Threads": 1,
            "Seed": 0,
            "Presolve": "Auto",
            "MIPGap": 0,
            "MIPGapAbs": 0,
        },
        "candidate": {
            "construction": "deterministic_data_target_or_root_LP_guided_append",
            "maximum_objective_evaluations": 512,
            "maximum_distinct_stations": 16,
            "triggers": ["first_eligible_MIP_before_incumbent",
                         "first_two_optimal_root_MIPNODE_cut_passes"],
            "mapping": "complete_original_variable_vector",
            "verification": ["original_route_verifier",
                             "bounds_types_and_all_linear_rows"],
        },
        "predeclared_decision_thresholds": {
            "meaningful_improvement":
                "relative final absolute-gap reduction >=5% and absolute reduction >=0.001, or same certificate >=10s faster",
            "obvious_regression":
                "relative final absolute-gap increase >=5% and absolute increase >=0.001, or same certificate >=10s slower, or certificate loss",
            "subsecond_difference": "timing differences below 1s are neutral",
            "certificate_loss_reported_separately": True,
        },
        "budget": {
            "maximum_end_to_end_processes": MAX_PROCESSES,
            "maximum_native_micro_processes": 6,
            "native_micro_already_charged": MANUAL_NATIVE_MICRO_PROCESSES,
            "reserved_for_long_and_integration": 16,
        },
    })


def ledger_entries():
    if not LEDGER.exists():
        return []
    return [json.loads(line) for line in LEDGER.read_text(
        encoding="utf-8").splitlines() if line.strip()]


def completion_success(path):
    return json.loads(Path(path).read_text(
        encoding="utf-8")).get("returncode") == 0


def execute(command, destination, identity, cap, optimization=True):
    destination = Path(destination)
    if destination.exists():
        completion = destination / "completion.json"
        if completion.exists() and json.loads(completion.read_text(
                encoding="utf-8"))["returncode"] == 0:
            print("skip", identity["id"], identity["arm"], flush=True)
            return
        raise RuntimeError(f"refusing to overwrite {destination}")
    entries = ledger_entries()
    charged_before = MANUAL_NATIVE_MICRO_PROCESSES + sum(
        bool(item.get("optimization", True)) for item in entries)
    if optimization and charged_before >= MAX_PROCESSES:
        raise RuntimeError("Round 60 72-process budget exhausted")
    destination.mkdir(parents=True)
    launch = dict(identity)
    launch.update({
        "command": [str(item) for item in command],
        "executable_sha256": sha256(command[0]),
        "started_unix": time.time(),
        "cap_seconds": cap,
        "optimization": optimization,
        "charged_process_number": charged_before + 1 if optimization else None,
    })
    write_json(destination / "launch.json", launch)
    OUT.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(launch) + "\n")
    environment = dict(os.environ)
    environment["PATH"] = (
        "D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;" +
        environment.get("PATH", ""))
    started = time.monotonic()
    with (destination / "stdout.log").open("w", encoding="utf-8") as stdout, \
         (destination / "stderr.log").open("w", encoding="utf-8") as stderr:
        try:
            process = subprocess.Popen(command, cwd=ROOT, env=environment,
                                       stdout=stdout, stderr=stderr)
        except Exception as error:
            write_json(destination / "completion.json", {
                "returncode": -998,
                "wall_seconds": time.monotonic() - started,
                "watchdog": False,
                "launch_error": f"{type(error).__name__}: {error}",
            })
            raise
        try:
            returncode = process.wait(timeout=cap + 20)
            watchdog = False
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            returncode = process.returncode
            watchdog = True
    completion = {
        "returncode": returncode,
        "wall_seconds": time.monotonic() - started,
        "watchdog": watchdog,
    }
    write_json(destination / "completion.json", completion)
    print(identity["id"], identity["arm"], returncode,
          round(completion["wall_seconds"], 3), flush=True)
    if returncode != 0:
        raise RuntimeError(f"failed run: {destination}")


def fixed_command(row, destination, mode, cap, monitor=True):
    command = [
        str(FIXED_EXE), "--mode", "solve", "--state-id",
        f'{row["id"]}-empty-F0-{mode}', "--input", row["instance_path"],
        "--artifact-dir", str(destination), "--policy",
        "interval-mip-core-no-exhaustive-subset-duration", "--T",
        str(row["T_seconds"]), "--pickup-time", str(row["pickup_seconds"]),
        "--drop-time", str(row["drop_seconds"]), "--process-cap", str(cap),
        "--round59-empty-state", "--round59-current-f0",
        "--round60-candidate-mode", mode,
        "--round60-candidate-max-evaluations", "512",
        "--round60-candidate-max-stations", "16",
    ]
    if monitor:
        command.append("--round59-monitor")
    return command


def run_fixed(ids, modes, cap, stage):
    rows = panel_rows()
    for identity in ids:
        row = rows[identity]
        assert sha256(ROOT / row["instance_path"]) == row["input_sha256"]
        for mode in modes:
            destination = RAW / stage / identity / mode
            execute(fixed_command(row, destination, mode, cap), destination,
                    {"id": identity, "arm": mode.upper(), "stage": stage,
                     "scope": "fixed_simple_start_F0"}, cap)


def full_command(row, destination, preset, cap, candidate_mode="off",
                 publish=False):
    return [
        str(EXE), "--input", row["instance_path"], "--lambda", "0.15",
        "--T", str(row["T_seconds"]),
        "--time-limit", str(cap - 6), "--process-wall-time-limit", str(cap),
        "--process-shutdown-margin", "3", "--threads", "1",
        "--mip-threads", "1", "--gurobi-seed", "0",
        "--gurobi-presolve", "-1", "--method", "gcap-frontier",
        "--algorithm-preset", preset, "--out", str(destination / "result.json"),
        "--log", str(destination / "native.log"),
        "--process-phase-ledger", str(destination / "process_phases.csv"),
        "--external-gini-artifact-dir", str(destination / "external"),
        "--heuristic-candidates-csv", str(destination / "heuristic_candidates.csv"),
        "--primal-heuristic-generation-log", str(destination / "hga_generations.csv"),
        "--progress-log", str(destination / "progress.csv"),
        "--round60-hga-publish-verified", "true" if publish else "false",
        "--round60-hga-candidate-log", str(destination / "hga_candidates.csv"),
        "--round60-candidate-mode", candidate_mode,
        "--round60-candidate-max-evaluations", "512",
        "--round60-candidate-max-stations", "16",
        "--round60-candidate-log-dir", str(destination / "candidate_events"),
    ]


def run_hga(cap):
    rows = panel_rows()
    for identity in ["D6", "D7"]:
        row = rows[identity]
        for publish in [False, True]:
            arm = "HGA-PUBLISH" if publish else "HGA-ORIGINAL"
            destination = RAW / f"hga_publish_{cap}" / identity / arm
            command = full_command(row, destination, "paper-k1-am-sf", cap,
                                   publish=publish)
            execute(command, destination,
                    {"id": identity, "arm": arm,
                     "stage": f"hga_publish_{cap}",
                     "scope": "full_original_problem"}, cap)


def run_split(cap):
    rows = panel_rows()
    for identity in ["D2", "C2"]:
        row = rows[identity]
        for arm, preset in [
                ("K1-H", "paper-k1-am-sf"),
                ("Single-H", "research-round60-f0-single-h")]:
            destination = RAW / f"split_{cap}" / identity / arm
            command = full_command(row, destination, preset, cap)
            execute(command, destination,
                    {"id": identity, "arm": arm,
                     "stage": f"split_{cap}",
                     "scope": "full_original_problem_real_split_attribution",
                     "C2_reclassified_as_development": identity == "C2"}, cap)


def run_integration(cap):
    rows = panel_rows()
    for identity in ["D1", "C1"]:
        row = rows[identity]
        for mode in ["off", "inject"]:
            arm = "Single-S" if mode == "off" else "Single-S+INJECT"
            destination = RAW / f"integration_{cap}" / identity / arm
            command = full_command(
                row, destination, "research-round59-f0-single-s", cap,
                candidate_mode=mode)
            execute(command, destination,
                    {"id": identity, "arm": arm,
                     "stage": f"integration_{cap}",
                     "scope": "full_original_problem"}, cap)


def run_same_build_reference(cap):
    """Run the two frozen official/stable arms without Round 60 features."""
    rows = panel_rows()
    expected = {
        item["instance_id"]: item["expected_gurobi_model_fingerprint"]
        for item in json.loads((ROOT /
            "results/gf_citibike443_k1_vs_pgrb_round58/"
            "pgrb_expected_fingerprints.json").read_text(encoding="utf-8"))[
                "entries"]
    }
    executable_hash = sha256(EXE)
    for identity in ["D1", "C1"]:
        row = rows[identity]
        for arm in ["P-GRB", "K1-H"]:
            destination = RAW / f"same_build_reference_{cap}" / identity / arm
            if destination.exists():
                completion_path = destination / "completion.json"
                if completion_path.exists() and completion_success(
                        completion_path):
                    print("skip", identity, arm, flush=True)
                    continue
                retry = 1
                while (destination.parent /
                       f"{arm}-retry{retry}").exists():
                    retry += 1
                destination = destination.parent / f"{arm}-retry{retry}"
            if arm == "K1-H":
                command = full_command(
                    row, destination, "paper-k1-am-sf", cap)
            else:
                command = [
                    str(EXE), "--input", row["instance_path"], "--lambda", "0.15",
                    "--T", str(row["T_seconds"]), "--time-limit", str(cap - 6),
                    "--process-wall-time-limit", str(cap),
                    "--process-shutdown-margin", "3", "--threads", "1",
                    "--mip-threads", "1", "--gurobi-seed", "0",
                    "--gurobi-presolve", "-1", "--out",
                    str(destination / "result.json"), "--log",
                    str(destination / "native.log"), "--process-phase-ledger",
                    str(destination / "process_phases.csv"), "--method", "gurobi",
                    "--plain-baseline", "--gurobi-model-export",
                    str(destination / "compact.lp"),
                    "--round24-expected-gurobi-model-fingerprint",
                    str(expected[row["scenario_id"]]),
                    "--round24-executable-sha256", executable_hash,
                    "--round24-manifest-executable-sha256", executable_hash,
                ]
            execute(command, destination,
                    {"id": identity, "arm": arm,
                     "stage": f"same_build_reference_{cap}",
                     "scope": "unchanged_same_build_reference"}, cap)


def run_partial_integration(cap):
    """Exercise Round 60 injection through a real K1 partial-target path."""
    row = panel_rows()["C2"]
    for mode in ["off", "inject"]:
        arm = "K1-H" if mode == "off" else "K1-H+INJECT"
        destination = RAW / f"partial_integration_{cap}" / "C2" / arm
        command = full_command(
            row, destination, "paper-k1-am-sf", cap,
            candidate_mode=mode)
        execute(command, destination,
                {"id": "C2", "arm": arm,
                 "stage": f"partial_integration_{cap}",
                 "scope": "full_original_problem_partial_target_candidate",
                 "C2_reclassified_as_development": True}, cap)


def run_final_native_micro():
    """Use the sixth and final native micro slot on the deliverable build."""
    destination = RAW / "native_micro" / "final-inject"
    command = [
        str(FIXED_EXE), "--mode", "solve", "--state-id",
        "tiny-final-inject", "--input", "tests/data/round59_tiny.txt",
        "--artifact-dir", str(destination), "--policy",
        "interval-mip-core-no-exhaustive-subset-duration", "--T", "5",
        "--pickup-time", "1", "--drop-time", "1", "--process-cap", "15",
        "--round59-empty-state", "--round59-current-f0",
        "--round60-candidate-mode", "inject",
        "--round60-candidate-max-evaluations", "64",
        "--round60-candidate-max-stations", "3",
    ]
    execute(command, destination,
            {"id": "micro", "arm": "FINAL-INJECT",
             "stage": "native_micro_final",
             "scope": "tiny_exact_native_candidate_acceptance"}, 15)


def build_identity():
    rows = panel_rows()
    for identity in ["D2", "D3", "D4"]:
        row = rows[identity]
        destination = RAW / "build_identity" / identity
        command = [
            str(FIXED_EXE), "--mode", "build", "--state-id", identity,
            "--input", row["instance_path"], "--artifact-dir",
            str(destination), "--policy",
            "interval-mip-core-no-exhaustive-subset-duration", "--T",
            str(row["T_seconds"]), "--pickup-time", str(row["pickup_seconds"]),
            "--drop-time", str(row["drop_seconds"]), "--process-cap", "30",
            "--round59-empty-state", "--round59-current-f0",
        ]
        execute(command, destination,
                {"id": identity, "arm": "BUILD-F0",
                 "stage": "build_identity", "scope": "build_only"},
                30, optimization=False)


def extract_latest_inventory(identity):
    sample_path = RAW / "fixed_120" / identity / "off/node_samples.csv"
    rows = list(csv.DictReader(sample_path.open(encoding="utf-8")))
    selected = [row for row in rows
                if row["sample_kind"] == "latest_root_relaxation" and
                row["variable"].startswith("Y_")]
    if not selected:
        raise RuntimeError(f"no latest-root inventory for {identity}")
    values = {int(row["variable"].split("_")[1]): float(row["value"])
              for row in selected}
    vector = [0] + [int(round(values[index]))
                    for index in range(1, max(values) + 1)]
    integral = all(abs(values[index] - vector[index]) <= 1e-7
                   for index in values)
    return vector, integral, values


def run_product_route(cap):
    rows = panel_rows()
    inventory_records = []
    for identity in ["D3", "D4", "D6"]:
        row = rows[identity]
        vector, integral, raw = extract_latest_inventory(identity)
        inventory_records.append({
            "id": identity,
            "source": "latest_root_relaxation",
            "root_inventory_integral": integral,
            "rounding": "none" if integral else "nearest_integer_heuristic",
            "raw_inventory": raw,
            "fixed_inventory": vector,
        })
        gamma_upper = 1.0 - 1.0 / int(row["V"])
        for mode in ["lp", "solve"]:
            arm = "FIXED-Y-LP" if mode == "lp" else "FIXED-Y-MIP"
            destination = RAW / "product_route" / identity / arm
            command = [
                str(FIXED_EXE), "--mode", mode, "--state-id",
                f"{identity}-fixed-Y", "--input", row["instance_path"],
                "--artifact-dir", str(destination), "--policy",
                "interval-mip-core-no-exhaustive-subset-duration", "--T",
                str(row["T_seconds"]), "--pickup-time",
                str(row["pickup_seconds"]), "--drop-time",
                str(row["drop_seconds"]), "--process-cap", str(cap),
                "--gamma-lower", "0", "--gamma-upper", str(gamma_upper),
                "--cutoff", "100", "--round59-current-f0",
                "--round60-fixed-inventory",
                ",".join(str(value) for value in vector),
            ]
            execute(command, destination,
                    {"id": identity, "arm": arm,
                     "stage": "product_route",
                     "scope": "fixed_inventory_diagnostic",
                     "root_inventory_integral": integral}, cap)
    write_json(OUT / "fixed_inventory_selection.json", inventory_records)


def run_product_time_relaxed(cap):
    rows = panel_rows()
    selections = {item["id"]: item for item in json.loads(
        (OUT / "fixed_inventory_selection.json").read_text(encoding="utf-8"))}
    for identity in ["D3", "D4"]:
        row = rows[identity]
        vector = selections[identity]["fixed_inventory"]
        destination = RAW / "product_route" / identity / "FIXED-Y-MIP-T-RELAXED"
        gamma_upper = 1.0 - 1.0 / int(row["V"])
        command = [
            str(FIXED_EXE), "--mode", "solve", "--state-id",
            f"{identity}-fixed-Y-time-relaxed", "--input",
            row["instance_path"], "--artifact-dir", str(destination),
            "--policy", "interval-mip-core-no-exhaustive-subset-duration",
            "--T", "1000000", "--pickup-time", str(row["pickup_seconds"]),
            "--drop-time", str(row["drop_seconds"]), "--process-cap", str(cap),
            "--gamma-lower", "0", "--gamma-upper", str(gamma_upper),
            "--cutoff", "100", "--round59-current-f0",
            "--round60-fixed-inventory",
            ",".join(str(value) for value in vector),
        ]
        execute(command, destination,
                {"id": identity, "arm": "FIXED-Y-MIP-T-RELAXED",
                 "stage": "product_route_time_counterfactual",
                 "scope": "fixed_inventory_diagnostic",
                 "only_changed_factor": "route_time_limit_1000000"}, cap)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=[
        "freeze", "identity", "fixed", "long", "hga", "split",
        "integration", "partial-integration", "reference", "product-route",
        "product-time-relaxed", "final-micro"])
    parser.add_argument("--cap", type=int, default=120)
    parser.add_argument("--ids", nargs="+")
    parser.add_argument("--modes", nargs="+")
    args = parser.parse_args()
    if args.action == "freeze":
        freeze()
    elif args.action == "identity":
        build_identity()
    elif args.action == "fixed":
        run_fixed(args.ids or ["D3", "D4", "D6", "D7"],
                  args.modes or ["off", "dry", "inject"],
                  args.cap, f"fixed_{args.cap}")
    elif args.action == "long":
        run_fixed(args.ids or ["D3", "D4", "D6"],
                  ["off", "inject"], args.cap, f"long_{args.cap}")
    elif args.action == "hga":
        run_hga(args.cap)
    elif args.action == "split":
        run_split(args.cap)
    elif args.action == "integration":
        run_integration(args.cap)
    elif args.action == "partial-integration":
        run_partial_integration(args.cap)
    elif args.action == "reference":
        run_same_build_reference(args.cap)
    elif args.action == "product-route":
        run_product_route(args.cap)
    elif args.action == "product-time-relaxed":
        run_product_time_relaxed(args.cap)
    elif args.action == "final-micro":
        run_final_native_micro()


if __name__ == "__main__":
    main()
