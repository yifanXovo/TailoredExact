"""One-use research process-tree watchdog for the signed R91 D3/C2 LP items.

This never calls Optimize itself. It uses the previously qualified Round88
kill-on-close Win32 Job implementation and preserves each item's raw output.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from round88_quantity_probe import _WindowsJob, _kill_process_tree  # noqa: E402


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("D3", "C2"), required=True)
    args = parser.parse_args()
    wrapper_started = time.perf_counter()
    contract_path = ROOT / "results/unified_exact_round91/handling_real_watchdog_contract_001.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract["authorized_by"] != "root" or contract["maximum_launch_to_exit_seconds_per_case"] != 120 or \
            contract["whole_process_tree_watchdog"] is not True or contract["attempts_per_case"] != 1:
        raise ValueError("not the signed one-attempt 120 s watchdog contract")
    entry = next(row for row in contract["cases"] if row["case"] == args.case)
    python = Path(contract["python"]).resolve()
    script = (ROOT / contract["script"]).resolve()
    prereg = (ROOT / contract["preregistration"]).resolve()
    admission_path = (ROOT / entry["admission"]).resolve()
    admission = json.loads(admission_path.read_text(encoding="utf-8"))
    if admission["case"] != args.case or admission["allow_optimize"] is not True or \
            admission["whole_process_limit_seconds"] != 120 or \
            digest(script) != admission["script_sha256"] or \
            digest(prereg) != admission["prereg_sha256"]:
        raise ValueError("signed source identity changed before launch")
    destination = (ROOT / entry["output"]).resolve()
    if destination.exists():
        raise ValueError("item destination already exists; never rerun")
    outer = destination.parent / ("outer_" + args.case)
    outer.mkdir(exist_ok=False)
    command = [str(python), str(script), contract["mode"],
               "--prereg", str(prereg), "--admission", str(admission_path),
               "--case", args.case, "--out", str(destination)]
    started_utc = utc()
    started = time.perf_counter()
    deadline = started + 120
    process = None
    job = None
    timed_out = False
    launch_error = None
    returncode = None
    pid = None
    with (outer / "stdout.log").open("x", encoding="utf-8") as stdout, \
         (outer / "stderr.log").open("x", encoding="utf-8") as stderr:
        try:
            job = _WindowsJob()
            process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            pid = process.pid
            job.assign(process)
            try:
                returncode = process.wait(timeout=max(0.0, deadline - time.perf_counter()))
            except subprocess.TimeoutExpired:
                timed_out = True
                _kill_process_tree(process, job)
                job = None
                returncode = process.returncode
        except Exception as error:
            launch_error = repr(error)
            if process is not None:
                _kill_process_tree(process, job)
                job = None
                returncode = process.returncode
        finally:
            if job is not None:
                job.close()  # Kills any surviving descendants after normal parent exit.
            if process is not None and process.poll() is None:
                _kill_process_tree(process, None)
                returncode = process.returncode
    launch_to_exit = time.perf_counter() - started
    timed_out = timed_out or launch_to_exit > 120
    status = ("invalid_launch" if launch_error is not None else
              "unknown_whole_process_deadline" if timed_out else
              "returned_zero_pending_evidence_audit" if returncode == 0 else
              "process_nonzero_or_unknown")
    receipt = dict(schema="round91-real-handling-outer-watchdog-v1", case=args.case,
                   status=status, exact_command=command, working_directory=str(ROOT),
                   started_utc=started_utc, ended_utc=utc(),
                   launch_to_exit_wall_seconds=launch_to_exit,
                   wrapper_full_wall_seconds_before_receipt=time.perf_counter() - wrapper_started,
                   limit_seconds=120, timed_out=timed_out, exit_code=returncode,
                   child_pid=pid, launch_error=launch_error,
                   win32_job_kill_on_close_used=True,
                   process_tree_closed=True,
                   python_sha256=digest(python), script_sha256=digest(script),
                   prereg_sha256=digest(prereg), admission_sha256=digest(admission_path),
                   watchdog_contract_sha256=digest(contract_path),
                   watchdog_helper_sha256=digest(ROOT / "scripts/round88_quantity_probe.py"),
                   stdout_path=str((outer / "stdout.log").relative_to(ROOT)),
                   stderr_path=str((outer / "stderr.log").relative_to(ROOT)))
    (outer / "outer_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                                               encoding="utf-8")
    print(json.dumps(dict(case=args.case, status=status, exit_code=returncode,
                          wall_seconds=launch_to_exit)), flush=True)
    return 0 if status == "returned_zero_pending_evidence_audit" else 124 if timed_out else 1


if __name__ == "__main__":
    raise SystemExit(main())
