"""Qualify the compact reference and supervise the preregistered C++ processes."""

import argparse
import csv
import ctypes
import json
from pathlib import Path
import math
import os
import subprocess
import time
import types
import zipfile

from generate_citibike443_regional_v1 import parse_instance_mirror
from round107_reader import instance
from round108_reader import model_contract
import round163_qualify as inherited_reference
from round170_run import OFF, tokens
from round170_common import result
from round171_common import (
    AFFINITY, BASE, CAP, DLL, DLL_SHA, MARGIN, MEASURED, OUT, PE, PE_SHA, ROOT, SCIENCE_CAP,
    SEED, TEMP, bind, clock, digest, env, git, read, require_committed, sha, utc, write,
)

PREVIOUS = ROOT / "results/unified_exact_round170"
ORDER = (("B", "P"), ("P", "B")) * 3
REFERENCE_ROOT = OUT / "qualification/references"
RAW_ROOT = OUT / "complete_raw"
EXPORT = types.FunctionType(inherited_reference.reference.__code__,
                            dict(vars(inherited_reference), OUT=OUT))
TEMPLATES = OUT / "argv_templates.json"


def qualify():
    started = time.perf_counter()
    exporter = inherited_reference.EXPORTER
    build_receipt = ROOT / "results/unified_exact_round137/exporter_build.json"
    previous = read(build_receipt)
    assert sha(exporter) == previous["SHA"] == inherited_reference.EXPORTER_SHA
    assert sha(ROOT / "scripts/round137_export.cpp") == previous["source_SHA"]
    assert sha(DLL) == DLL_SHA
    rows = []
    for panel in read(OUT / "input_manifest.json")["roles"]:
        path = ROOT / panel["input_path"]
        assert sha(path) == panel["input_sha256"]
        data, mirror = instance(ROOT, panel), parse_instance_mirror(path)
        for physical, static in (("b", "initial"), ("D", "target"), ("c", "capacities"), ("w", "weights")):
            assert list(data[physical]) == mirror[static], (panel["id"], physical)
        assert list(map(list, data["xy"])) == list(map(list, mirror["points"]))
        assert data["Q"] == mirror["Q"] == [20, 25, 30]
        assert mirror["V"] == 50 and mirror["M"] == 3
        weights = data["w"][1:]
        assert panel["Omega"] == sum(weights) and panel["lambda"] == 1 / sum(weights)
        assert panel["positive_objective_floor_decimal"] > 0
        build = EXPORT(panel)
        folder = REFERENCE_ROOT / panel["id"]
        facts, model = model_contract(ROOT, panel, folder / "original.lp", "P-GRB")
        coefficients = dict(model["objective"][0])
        assert model["objective"][1] == 0
        assert coefficients == {"G": 1, **{f"e_{i}": panel["lambda"] * w for i, w in enumerate(weights, 1)}}
        assert not any(name.startswith(("state_", "rn_", "r162_")) for name in model["order"])
        assert all(model["types"][f"Y_{i}"] == "I" and model["bounds"][f"Y_{i}"] == (0, data["c"][i])
                   for i in range(1, 51))
        native = read(folder / "native_metadata.json")
        assert native == dict(Optimize=0, columns=build["columns"], rows=build["rows"], objective_sense=1, objective_constant=0)
        with (folder / "native_columns.csv").open(newline="", encoding="utf-8") as handle:
            columns = list(csv.DictReader(handle))
        assert len(columns) == len(model["order"]) == native["columns"]
        for column, name in zip(columns, model["order"]):
            assert column["type"] == model["types"][name], (column, name)
            assert (float(column["lower"]), float(column["upper"])) == model["bounds"][name], (column, name)
            assert float(column["objective"]) == coefficients.get(name, 0), (column, name)
        with (folder / "native_rows.csv").open(newline="", encoding="utf-8") as handle:
            native_rows = list(csv.DictReader(handle))
        assert len(native_rows) == len(model["rows"]) == native["rows"]
        for native_row, (_, sense, rhs) in zip(native_rows, model["rows"]):
            assert native_row["sense"] == {"<=": "<", ">=": ">", "=": "="}[sense]
            assert math.isclose(float(native_row["RHS"]), rhs, rel_tol=1e-14, abs_tol=1e-14)
        export_log = OUT / "qualification/export_logs" / panel["id"] / "receipt.json"
        rows.append(dict(
            id=panel["id"], input=bind(path), T_seconds=panel["T_seconds"], lambda_binary64=panel["lambda_binary64"],
            Q=panel["Q_vector"], pickup_seconds=60, drop_seconds=60, speed_m_per_s=1.5,
            independent_parsers_equal=True, full_original_compact_contract=facts, metadata=build,
            independent_native_column_and_row_contract=True,
            export_files=[bind(path) for path in sorted(folder.iterdir())],
            fee_and_command=bind(export_log), export_seconds=read(export_log)["seconds"],
        ))
    seconds = time.perf_counter() - started
    write(OUT / "qualification/result.json", dict(
        UTC=utc(), PASS=True, inputs=rows, Optimize=0, H=0, outer_seconds_this_session=seconds,
        sum_export_process_seconds=sum(row["export_seconds"] for row in rows),
        qualification_outer_target_seconds=600,
        exporter=bind(exporter), source=bind(ROOT / "scripts/round137_export.cpp"),
        inherited_exporter_build=bind(build_receipt), Gurobi_version="13.0.2", DLL=bind(DLL),
    ))
    print(f"Six zero-Optimize compact references passed with dual input parsers ({seconds:.3f}s)", flush=True)


def freeze_templates():
    previous_matrix = read(PREVIOUS / "matrix_frozen.json")
    archive = PREVIOUS / "artifacts/round170_new_raw.zip"
    archive_record = read(PREVIOUS / "evidence_archives.json")["carrier"]
    assert sha(archive) == archive_record["SHA256"]
    templates = {}
    with zipfile.ZipFile(archive) as zip_file:
        for arm in ("B", "P"):
            position = next(p for p in previous_matrix["positions"] if p["arm"] == arm)
            run_id = position["directory"].replace("\\", "/").split("/")[-1]
            member = f"complete_raw/{run_id}/invocation.json"
            record = next(n for n in zip_file.namelist() if n.endswith(member))
            raw = zip_file.read(record)
            audit = read(PREVIOUS / f"review/complete_audit_{position['position']:02d}.json")
            invocation = json.loads(raw)
            assert invocation["argv"] == position["argv"]
            assert audit["actual_invocation"]["SHA256"] == digest(raw)
            templates[arm] = dict(argv=invocation["argv"], directory=position["directory"],
                                  archive_member=record, invocation_SHA256=audit["actual_invocation"]["SHA256"])
    write(TEMPLATES, dict(UTC=utc(), delivery=BASE, carrier=archive_record, arms=templates))


def command(panel, destination, arm, template, fingerprint):
    cmd = [arg.replace(template["directory"], str(destination)) for arg in template["argv"]]
    cmd[0] = str(PE)
    changes = {
        "--input": str(ROOT / panel["input_path"]), "--T": str(panel["T_seconds"]),
        "--lambda": panel["lambda_decimal17"], "--gurobi-seed": str(SEED),
        "--time-limit": str(CAP - MARGIN), "--process-wall-time-limit": str(CAP),
    }
    if arm == "P":
        changes.update({
            "--round24-expected-gurobi-model-fingerprint": str(fingerprint),
            "--round24-executable-sha256": PE_SHA, "--round24-manifest-executable-sha256": PE_SHA,
        })
    for option, value in changes.items():
        cmd[cmd.index(option) + 1] = value
    parameters = tokens(cmd)
    assert parameters["--round166-breakpoint"] == parameters["--round169-primal-mode"] == "off"
    assert parameters["--threads"] == parameters["--mip-threads"] == "1"
    assert parameters["--pickup-time"] == parameters["--drop-time"] == "60"
    assert parameters["--process-shutdown-margin"] == str(MARGIN)
    assert parameters["--gurobi-presolve"] == "-1"
    assert "--round112-ens-start-compact" not in parameters and "--round169-h-panel" not in parameters
    if arm == "P":
        assert "--plain-baseline" in parameters and parameters["--round127-mode"] == "p"
        assert parameters["--method"] == "gurobi" and parameters["--algorithm-preset"] == "custom"
        assert all(parameters[key] == value for key, value in OFF.items())
    else:
        assert "--plain-baseline" not in parameters and parameters["--round127-mode"] == "ms2"
        assert parameters["--method"] == "gcap-frontier"
        assert parameters["--algorithm-preset"] == "research-round83-vds-equal-net-exchange"
    return cmd


def freeze():
    assert not (OUT / "matrix_frozen.json").exists()
    freeze_templates()
    templates = read(TEMPLATES)["arms"]
    manifest = read(OUT / "input_manifest.json")
    qualification = read(OUT / "qualification/result.json")
    assert qualification["PASS"] and qualification["Optimize"] == 0
    references = {p["id"]: p for p in qualification["inputs"]}
    positions = []
    for block, (role, order) in enumerate(zip(manifest["roles"], ORDER, strict=True), 1):
        reference = references[role["id"]]
        for arm in order:
            position = len(positions) + 1
            run_id = f"{position:02d}_{role['id']}_S{SEED}_{arm}"
            directory = RAW_ROOT / run_id
            positions.append(dict(
                position=position, block=block, role=role["id"], arm=arm, run_id=run_id,
                repeat=1, Native_Seed=SEED, Threads=1, MIPThreads=1,
                cap=CAP, native_time_limit=CAP - MARGIN, shutdown_margin=MARGIN,
                directory=str(directory), argv=command(role, directory, arm, templates[arm], reference["metadata"]["fingerprint"]),
                input_SHA256=role["input_sha256"], original_compact_reference=reference["metadata"],
                PE_SHA256=PE_SHA, DLL_SHA256=DLL_SHA, source_commit=MEASURED, delivery_base=BASE,
            ))
    assert len(positions) == 12 and len(references) == 6
    write(OUT / "matrix_frozen.json", dict(
        UTC=utc(), positions=positions, nominal_process_cap_sum=CAP * len(positions),
        serial=True, H_seed=20260626, expected_H_calls=6, no_result_selection_or_stopping=True,
        delta="max(1e-6,0.001*max(abs(U_P),1e-12))",
        inputs=bind(OUT / "input_manifest.json"), qualification=bind(OUT / "qualification/result.json"),
        templates=bind(TEMPLATES), runtime_identity=bind(OUT / "candidate_manifest.json"), runner=bind(__file__),
    ))
    print("Frozen 12 ordered positions with new references and total nominal cap 14400s", flush=True)


def admission():
    path = OUT / "matrix_frozen.json"
    require_committed(path)
    matrix = read(path)
    assert sha(PE) == PE_SHA and sha(DLL) == DLL_SHA
    for key in ("inputs", "qualification", "templates", "runtime_identity", "runner"):
        expected = matrix[key]
        artifact = ROOT / expected["path"]
        assert sha(artifact) == expected["SHA256"], key
        require_committed(artifact)
    roles = {p["id"]: p for p in read(OUT / "input_manifest.json")["roles"]}
    templates = read(TEMPLATES)["arms"]
    for position in matrix["positions"]:
        role = roles[position["role"]]
        assert sha(ROOT / role["input_path"]) == position["input_SHA256"] == role["input_sha256"]
        p = position
        assert p["argv"] == command(role, p["directory"], p["arm"], templates[p["arm"]],
                                    p["original_compact_reference"]["fingerprint"])
    return matrix


def record_state(path, value):
    temporary = path.with_name(path.name + ".tmp")
    write(temporary, value)
    os.replace(temporary, path)


def launch(p):
    directory = Path(p["directory"])
    directory.mkdir(parents=True, exist_ok=False)
    write(directory / "invocation.json", dict(
        UTC=utc(), argv=p["argv"], PE=bind(PE), DLL=bind(DLL), source=git("rev-parse", "HEAD"),
        measured_core_source=MEASURED, deadline_seconds=CAP, H_free_reuse=False, affinity_mask=AFFINITY,
        matrix_SHA256=sha(OUT / "matrix_frozen.json"),
    ))
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    set_affinity = kernel.SetProcessAffinityMask
    set_affinity.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    set_affinity.restype = ctypes.c_int
    environment = env()
    native_temp = TEMP / "native_tmp"
    native_temp.mkdir(parents=True, exist_ok=True)
    environment["TEMP"] = environment["TMP"] = str(native_temp)
    wall_start = time.time()
    clock_start = time.perf_counter()
    killed = False
    with (directory / "console.log").open("xb") as console:
        proc = subprocess.Popen(p["argv"], cwd=ROOT, env=environment, stdout=console, stderr=subprocess.STDOUT)
        affinity_ok = bool(set_affinity(int(proc._handle), AFFINITY))
        record_state(OUT / "active_position.json", dict(
            UTC=utc(), position=p["position"], role=p["role"], arm=p["arm"], pid=proc.pid,
            started_epoch=wall_start, deadline_epoch=wall_start + CAP,
            output=str(directory), Native_Seed=SEED, affinity_mask=AFFINITY, affinity_set=affinity_ok,
        ))
        try:
            returncode = proc.wait(timeout=max(0, CAP - (time.perf_counter() - clock_start)))
        except subprocess.TimeoutExpired:
            killed = True
            proc.kill()
            returncode = proc.wait()
        outer_seconds = time.perf_counter() - clock_start
        wall_end = time.time()
    result_path = directory / "result.json"
    receipt = dict(
        UTC=utc(), started_epoch=wall_start, ended_epoch=wall_end, process_outer_seconds=outer_seconds,
        rc=returncode, affinity=dict(mask=AFFINITY, set_success=affinity_ok, wrapper_killed=killed),
        result=bind(result_path) if result_path.is_file() else None, deadline_seconds=CAP,
    )
    write(directory / "completion.json", receipt)
    return receipt


def panel():
    matrix = admission()
    positions = matrix["positions"]
    remaining = sum(not Path(p["directory"]).exists() for p in positions)
    assert clock()["occupied_conservative_seconds"] + remaining * CAP < SCIENCE_CAP, "Insufficient scientific capacity"
    lock = OUT / "producer.lock"
    with lock.open("x", encoding="utf-8") as handle:
        handle.write(str(os.getpid()) + "\n")
    completed = []
    try:
        for p in positions:
            directory = Path(p["directory"])
            if directory.exists():
                assert (directory / "completion.json").is_file(), f"Inspect partial position {p['run_id']} before resuming"
                receipt = read(directory / "completion.json")
                print(f"RESUME {p['run_id']}: preserved producer", flush=True)
            else:
                other = subprocess.run(["tasklist", "/FI", "IMAGENAME eq ExactEBRP.exe", "/FO", "CSV", "/NH"],
                                       check=True, text=True, capture_output=True)
                assert "ExactEBRP.exe" not in other.stdout, "The local optimizer is occupied"
                print(f"START {p['run_id']} {utc()}", flush=True)
                receipt = launch(p)
            success = receipt["rc"] == 0 and receipt["result"] and receipt["affinity"]["set_success"]
            success = bool(success and not receipt["affinity"]["wrapper_killed"] and receipt["process_outer_seconds"] <= CAP)
            endpoint = result(directory / "result.json") if receipt["result"] else {}
            record = dict(
                position=p["position"], role=p["role"], arm=p["arm"], run_id=p["run_id"],
                process_completed_within_cap=success, receipt=receipt,
                raw_endpoint={key: endpoint.get(key) for key in
                              ("status", "upper_bound", "lower_bound", "gap", "strict_certified_original_problem")},
            )
            completed.append(record)
            record_state(OUT / "complete_status.json", dict(
                UTC=utc(), positions_finished=len(completed), records=completed,
                process_outer_seconds=sum(row["receipt"]["process_outer_seconds"] for row in completed),
            ))
            print(f"END {p['run_id']} rc={receipt['rc']} {receipt['process_outer_seconds']:.3f}s", flush=True)
            assert success, f"Preserved failure at {p['run_id']}; diagnose before resuming"
        record_state(OUT / "panel_complete.json", dict(UTC=utc(), positions=len(completed), all_returned=True))
    finally:
        lock.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["qualify", "freeze", "panel"])
    args = parser.parse_args()
    {"qualify": qualify, "freeze": freeze, "panel": panel}[args.stage]()
