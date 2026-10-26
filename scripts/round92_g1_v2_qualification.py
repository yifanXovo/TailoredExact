"""One admitted, zero-Optimize Round92 v2 G1 qualification.

This runner is inert without a separately root-signed admission. It reuses the
existing configured build and never configures, solves, retries, or overwrites.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "results/unified_exact_round92"
BUILD = ROOT / "build/research/round92-handling-activation"
EVIDENCE = RESULT / "qualification_003"
SOURCE_ID = RESULT / "physical_envelope_source_identity.json"
PREREG = RESULT / "preregistration_g1_v2.json"
SOURCE_COMMIT = "ea190d909bbc8fbb0caaaada78c928f71be18bc1"
SOURCE_ID_SHA = "02dbca61efb415d64561a9a15a868b7f8822354b8c0afb4c2f76675b8bbf6bbf"
CMAKE = Path("D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe")
CTEST = CMAKE.with_name("ctest.exe")
PYTHON = ROOT / "build/research/round88-ot/venv/Scripts/python.exe"
PREFIX = "D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin"
OLD_BINARIES = {
    "ExactEBRP.exe": "bf99199172b9d783bcb55ad532d25f748348d08907a9f8b5b5de92bf9afe2524",
    "libexact_ebrp_core.a": "fd977d68e87ea5c116d33a25943abc8a036295e33c72c60c36bdf357c2e26be6",
    "Round92HandlingActivationTests.exe": "fed6f5fd5178bcd69af581dcbabf093c241e5c4063c7702b8f3ab3d1ec946f1a",
    "Round92HandlingIntegrationTests.exe": "c806fcaf6321884e95b738438ad54c8904f90ad3179feb474bab0824dbe9310a",
}
STAGES = ("preserve", "build", "ctest", "export", "readback")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_new(path: Path, data: object) -> None:
    # x mode prevents a repeated attempt from overwriting any receipt.
    with path.open("x", encoding="utf-8", newline="\n") as destination:
        json.dump(data, destination, indent=2, sort_keys=True)
        destination.write("\n")


def checked_path(relative: str) -> Path:
    path = (ROOT / relative).resolve(strict=True)
    if not path.is_relative_to(ROOT) or not path.is_file() or path.is_symlink():
        raise RuntimeError(f"unsafe source path: {relative}")
    return path


def verify_admission(admission: Path) -> dict:
    if not admission.is_file() or admission.is_symlink():
        raise RuntimeError("missing or linked execution admission")
    gate = json.loads(admission.read_text(encoding="utf-8"))
    required = {
        "schema": "round92-g1-v2-execution-admission-v1",
        "authorized_by": "root", "allow_run": True,
        "allow_configure": False, "allow_optimize": False,
        "maximum_optimize_calls": 0,
        "source_commit": SOURCE_COMMIT,
        "source_identity_sha256": SOURCE_ID_SHA,
        "runner_sha256": sha(Path(__file__)),
        "preregistration_sha256": sha(PREREG),
        "evidence_root": "results/unified_exact_round92/qualification_003",
    }
    for key, value in required.items():
        if gate.get(key) != value:
            raise RuntimeError(f"admission mismatch: {key}")
    if sha(SOURCE_ID) != SOURCE_ID_SHA:
        raise RuntimeError("frozen source identity manifest changed")
    source = json.loads(SOURCE_ID.read_text(encoding="utf-8"))
    if (source.get("source_commit") != SOURCE_COMMIT or
            len(source.get("source_files", [])) != 15):
        raise RuntimeError("source identity shape mismatch")
    for item in source["source_files"]:
        path = checked_path(item["path"])
        if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise RuntimeError(f"source bytes mismatch: {item['path']}")
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    if (prereg.get("schema") != "round92-g1-v2-preregistration-v1" or
        prereg.get("source_identity_sha256") != SOURCE_ID_SHA or
        prereg.get("old_binary_sha256") != OLD_BINARIES or
        prereg.get("stages") != list(STAGES)):
        raise RuntimeError("preregistration contract mismatch")
    if EVIDENCE.exists() or (BUILD / "qualified_v1").exists():
        raise RuntimeError("fresh evidence or qualified_v1 destination exists")
    for name, expected in OLD_BINARIES.items():
        binary = BUILD / name
        if not binary.is_file() or binary.is_symlink() or sha(binary) != expected:
            raise RuntimeError(f"qualified v1 binary mismatch: {name}")
    return gate


def compile_contract() -> dict:
    cache = BUILD / "CMakeCache.txt"
    ninja = BUILD / "build.ninja"
    rules = BUILD / "CMakeFiles/rules.ninja"
    files = [cache, ninja, rules]
    for path in files:
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"missing configured build rule: {path}")
    cache_text = cache.read_text(encoding="utf-8", errors="replace")
    ninja_text = ninja.read_text(encoding="utf-8", errors="replace")
    rules_text = rules.read_text(encoding="utf-8", errors="replace")
    selected = [line for line in (ninja_text + "\n" + rules_text).splitlines()
                if any(token in line for token in
                       ("FLAGS =", "DEFINES =", "INCLUDES =", "command ="))]
    cache_selected = [line for line in cache_text.splitlines()
                      if line.startswith(("CMAKE_BUILD_TYPE:",
                                          "CMAKE_CXX_COMPILER:",
                                          "CMAKE_MAKE_PROGRAM:"))]
    contract = {"files": {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path)
                           for path in files},
                "cache_selected": cache_selected, "ninja_rule_lines": selected}
    flags = "\n".join(selected)
    if any(bad in flags for bad in ("-ffast-math", "-Ofast",
                                     "-fassociative-math", "-fexcess-precision=fast")):
        raise RuntimeError("unsupported compiler transform in frozen build rules")
    return contract


def run_stage(name: str, argv: list[str] | None, environment: dict[str, str]) -> dict:
    started = utc()
    clock = time.perf_counter()
    write_new(EVIDENCE / f"{name}.started.json",
              {"stage": name, "utc": started, "argv": argv,
               "cwd": str(ROOT), "path_prefix": PREFIX})
    stdout = EVIDENCE / f"{name}.stdout.log"
    stderr = EVIDENCE / f"{name}.stderr.log"
    exit_code = -1
    error = None
    try:
        with stdout.open("xb") as out, stderr.open("xb") as err:
            if name == "preserve":
                destination = BUILD / "qualified_v1"
                destination.mkdir(mode=0o700)
                records = {}
                for binary, expected in OLD_BINARIES.items():
                    original = BUILD / binary
                    saved = destination / binary
                    with original.open("rb") as src, saved.open("xb") as dst:
                        shutil.copyfileobj(src, dst, 1024 * 1024)
                    actual = sha(saved)
                    if actual != expected:
                        raise RuntimeError(f"preserved v1 binary mismatch: {binary}")
                    records[binary] = {"path": str(saved), "sha256": actual,
                                       "bytes": saved.stat().st_size}
                out.write((json.dumps(records, indent=2) + "\n").encode())
                exit_code = 0
            else:
                assert argv is not None
                proc = subprocess.Popen(argv, cwd=ROOT, env=environment,
                                        stdin=subprocess.DEVNULL, stdout=out,
                                        stderr=err, shell=False,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                exit_code = proc.wait()
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        with stderr.open("ab") as err:
            err.write((error + "\n" + traceback.format_exc()).encode())
    receipt = {"stage": name, "start_utc": started, "finish_utc": utc(),
               "outer_stage_wall_seconds": time.perf_counter() - clock,
               "child_exit_code": exit_code, "error": error,
               "stdout": str(stdout), "stderr": str(stderr)}
    write_new(EVIDENCE / f"{name}.receipt.json", receipt)
    if exit_code != 0 or error:
        raise RuntimeError(f"stage {name} failed: child={exit_code}; {error}")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--admission", type=Path, required=True)
    args = parser.parse_args()
    overall_start = utc()
    overall_clock = time.perf_counter()
    verify_admission(args.admission)
    pre_rules = compile_contract()
    EVIDENCE.mkdir(parents=False)
    write_new(EVIDENCE / "run.started.json",
              {"utc": overall_start, "admission": str(args.admission),
               "admission_sha256": sha(args.admission),
               "source_commit": SOURCE_COMMIT, "stages": STAGES})
    write_new(EVIDENCE / "compile_contract.before.json", pre_rules)
    environment = dict(os.environ)
    environment["PATH"] = PREFIX + ";" + environment.get("PATH", "")
    export = EVIDENCE / "canonical_export"
    commands = {
        "build": [str(CMAKE), "--build", str(BUILD), "--parallel", "4",
                  "--target", "ExactEBRP", "Round92HandlingActivationTests",
                  "Round92HandlingIntegrationTests"],
        "ctest": [str(CTEST), "--test-dir", str(BUILD), "--output-on-failure",
                  "-R", "^(Round92HandlingActivationTests|Round92HandlingActivationCliTests)$"],
        "export": [str(BUILD / "Round92HandlingIntegrationTests.exe"), str(export)],
        "readback": [str(PYTHON),
                     str(ROOT / "tests/round92_handling_lp_readback.py"), str(export)],
    }
    completed = []
    status = "failed_prefix"
    failure = None
    try:
        for name in STAGES:
            completed.append(run_stage(name, commands.get(name), environment))
            if name == "build":
                write_new(EVIDENCE / "compile_contract.after.json", compile_contract())
                binaries = {n: sha(BUILD / n) for n in OLD_BINARIES}
                write_new(EVIDENCE / "v2_binary_hashes.json", binaries)
            if name == "export":
                expected = (
                    "five_station_input.txt", "off.lp", "on.lp", "reused.lp",
                    "invalidated.lp", "raw_only.lp", "zero_handling.lp",
                    "physical_delta.lp",
                )
                exports = {}
                for leaf in expected:
                    path = export / leaf
                    if not path.is_file() or path.is_symlink():
                        raise RuntimeError(f"missing/linked canonical export: {leaf}")
                    exports[leaf] = {"bytes": path.stat().st_size,
                                     "sha256": sha(path)}
                write_new(EVIDENCE / "export_hashes.json", exports)
        # Only explicit frozen source files are rechecked; no repository scan.
        source = json.loads(SOURCE_ID.read_text(encoding="utf-8"))
        for item in source["source_files"]:
            if sha(checked_path(item["path"])) != item["sha256"]:
                raise RuntimeError(f"postflight source changed: {item['path']}")
        status = "zero_optimize_g1_stages_completed_pending_independent_audit"
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
    finally:
        write_new(EVIDENCE / "run.receipt.json",
                  {"status": status, "failure": failure,
                   "start_utc": overall_start, "finish_utc": utc(),
                   "full_runner_wall_seconds": time.perf_counter() - overall_clock,
                   "completed_stages": [r["stage"] for r in completed],
                   "stage_receipts": completed, "optimize_calls_planned": 0})
    if failure:
        print(failure, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
