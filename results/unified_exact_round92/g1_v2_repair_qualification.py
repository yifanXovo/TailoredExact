"""One admitted Q004 test-only repair qualification; no solver Optimize."""
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

ROOT = Path("E:/codes/ExactEBRP")
BUILD = ROOT / "build/research/round92-handling-activation"
OUT = ROOT / "results/unified_exact_round92/qualification_004"
GATE = ROOT / "results/unified_exact_round92/g1_v2_repair_execution_admission.json"
GATE_SHA = "e6434dbb6dd18645b9626a954291ec9ed917341369b990a9d0c81133c841c624"
STABLE = ("ExactEBRP.exe", "libexact_ebrp_core.a", "Round92HandlingIntegrationTests.exe")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def put(path, obj):
    with Path(path).open("x", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def check_sources(gate):
    for item in gate["source_hashes"]:
        p = (ROOT / item["path"]).resolve(strict=True)
        if not p.is_relative_to(ROOT) or p.is_symlink() or not p.is_file():
            raise RuntimeError("unsafe source: " + item["path"])
        if p.stat().st_size != item["bytes"] or sha(p) != item["sha256"]:
            raise RuntimeError("source identity mismatch: " + item["path"])


def stable_hashes(gate):
    result = {}
    for name in STABLE:
        p = BUILD / name
        if not p.is_file() or p.is_symlink():
            raise RuntimeError("missing stable binary: " + name)
        result[name] = sha(p)
        if result[name] != gate["prebuild_binary_hashes"][name]:
            raise RuntimeError("stable binary mismatch: " + name)
    return result


def stage(name, argv, env):
    start = utc()
    clock = time.perf_counter()
    put(OUT / (name + ".started.json"), {"stage": name, "start_utc": start,
        "argv": argv, "cwd": str(ROOT)})
    code = None
    error = None
    stdout = OUT / (name + ".stdout.log")
    stderr = OUT / (name + ".stderr.log")
    try:
        with stdout.open("xb") as out, stderr.open("xb") as err:
            child = subprocess.Popen(argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=out, stderr=err, shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW)
            code = child.wait()
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        with stderr.open("ab") as err:
            err.write((error + "\n" + traceback.format_exc()).encode())
    receipt = {"stage": name, "start_utc": start, "finish_utc": utc(),
        "outer_stage_wall_seconds": time.perf_counter() - clock,
        "child_exit_code": code, "error": error, "stdout": str(stdout),
        "stderr": str(stderr)}
    put(OUT / (name + ".receipt.json"), receipt)
    if code != 0 or error:
        raise RuntimeError(f"{name} failed, exit={code}, error={error}")
    return receipt


def main():
    started = utc()
    clock = time.perf_counter()
    if sha(GATE) != GATE_SHA:
        raise RuntimeError("admission bytes mismatch")
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    if (gate.get("schema") != "round92-g1-v2-fixture-repair-admission-v1"
        or gate.get("allow_run") is not True or gate.get("maximum_runs") != 1
        or gate.get("allow_optimize") is not False
        or gate.get("source_commit") != "a0e35a221c770f71ef19c405edf9af73e43d93d7"
        or len(gate.get("source_hashes", [])) != 15
        or len(gate.get("sequential_commands", [])) != 4):
        raise RuntimeError("admission contract mismatch")
    if OUT.exists():
        raise RuntimeError("Q004 evidence already exists")
    saved = Path(gate["preserve"]["destination"])
    if saved.parent.exists():
        raise RuntimeError("failed_003 preservation already exists")
    check_sources(gate)
    before = stable_hashes(gate)
    pure = Path(gate["preserve"]["source"])
    if pure.is_symlink() or sha(pure) != gate["preserve"]["sha256"]:
        raise RuntimeError("failed Q003 pure binary changed")
    for argv in gate["sequential_commands"]:
        if not Path(argv[0]).is_file():
            raise RuntimeError("missing command executable: " + argv[0])
    OUT.mkdir()
    put(OUT / "run.started.json", {"start_utc": started, "admission_sha256": GATE_SHA,
        "source_commit": gate["source_commit"], "commands": gate["sequential_commands"],
        "stable_binary_hashes_before": before})
    completed = []
    status = "failed_prefix"
    failure = None
    env = dict(os.environ)
    env["PATH"] = "D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;" + env.get("PATH", "")
    try:
        save_start = utc()
        save_clock = time.perf_counter()
        saved.parent.mkdir()
        with pure.open("rb") as src, saved.open("xb") as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
        if sha(saved) != gate["preserve"]["sha256"]:
            raise RuntimeError("preserved failed binary differs")
        put(OUT / "preserve.receipt.json", {"start_utc": save_start,
            "finish_utc": utc(), "wall_seconds": time.perf_counter()-save_clock,
            "source": str(pure), "destination": str(saved),
            "sha256": sha(saved), "bytes": saved.stat().st_size})
        for index, name in enumerate(("build_pure", "pure", "export", "readback")):
            completed.append(stage(name, gate["sequential_commands"][index], env))
            if index == 0:
                after_build = stable_hashes(gate)
                put(OUT / "binary_hashes.after_build.json",
                    {"stable": after_build, "pure": sha(pure)})
        check_sources(gate)
        final_stable = stable_hashes(gate)
        put(OUT / "source_postflight.json", {"status": "match", "source_count": 15,
            "stable_binary_hashes": final_stable, "pure_sha256": sha(pure)})
        status = "zero_optimize_stages_completed_pending_audit"
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
    finally:
        put(OUT / "run.receipt.json", {"status": status, "failure": failure,
            "start_utc": started, "finish_utc": utc(),
            "runner_wall_seconds": time.perf_counter()-clock,
            "completed_stages": [r["stage"] for r in completed],
            "optimize_calls_planned": 0})
    if failure:
        print(failure, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
