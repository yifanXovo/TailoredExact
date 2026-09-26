"""External whole-process wall cap for the independent OT LP diagnostic.

The cap is a measurement protocol, not a solver time/work budget. A timeout
records unknown and terminates the one diagnostic process; it never selects
cuts or switches an ENS algorithm internally.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--whole-process-limit-seconds", type=float, required=True)
    args = parser.parse_args()
    if args.whole_process_limit_seconds <= 0:
        parser.error("whole-process limit must be positive")
    args.out_dir.mkdir(parents=True, exist_ok=False)
    diagnostic_out = args.out_dir / "diagnostic"
    manifest_sha_before = file_sha(args.manifest)
    command = [sys.executable, str(Path(__file__).with_name("round88_ot_diagnostic.py")),
               "diagnose", "--manifest", str(args.manifest.resolve()),
               "--out-dir", str(diagnostic_out)]
    started = time.perf_counter()
    deadline = started + args.whole_process_limit_seconds
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=max(0.0, deadline - time.perf_counter()))
    except subprocess.TimeoutExpired:
        timed_out = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
    wall = time.perf_counter() - started
    timed_out = timed_out or time.perf_counter() > deadline
    manifest_sha_after = file_sha(args.manifest) if args.manifest.is_file() else None
    result_path = diagnostic_out / "result.json"
    result_file_invalid = False
    result_manifest_sha = None
    if result_path.is_file():
        try:
            result_manifest_sha = json.loads(result_path.read_text(encoding="utf-8"))[
                "manifest_sha256"]
        except (OSError, ValueError, KeyError):
            result_file_invalid = True
    manifest_consistent = (manifest_sha_before == manifest_sha_after
                           and (result_manifest_sha is None
                                or result_manifest_sha == manifest_sha_before))
    result_complete = result_path.is_file() and not result_file_invalid
    (args.out_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
    (args.out_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    status = ("invalid_manifest_drift" if not manifest_consistent else
              "unknown_whole_process_deadline" if timed_out else
              "invalid_diagnostic_result" if process.returncode == 0 and not result_complete else
              "diagnostic_process_finished" if process.returncode == 0 else
              "diagnostic_process_failed")
    receipt = {"status": status, "wall_seconds": wall,
               "whole_process_limit_seconds": args.whole_process_limit_seconds,
               "exit_code": process.returncode,
               "manifest_sha256_before": manifest_sha_before,
               "manifest_sha256_after": manifest_sha_after,
               "diagnostic_result_manifest_sha256": result_manifest_sha,
               "diagnostic_result_file_invalid": result_file_invalid,
               "manifest_identity_consistent": manifest_consistent,
               "diagnostic_result_complete": result_complete,
               "command": command}
    (args.out_dir / "supervision.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(status, file=sys.stderr if status != "diagnostic_process_finished" else sys.stdout)
    return (125 if not manifest_consistent else 124 if timed_out else
            126 if status == "invalid_diagnostic_result" else process.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
