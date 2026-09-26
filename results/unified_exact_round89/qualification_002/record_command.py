"""Record one admitted Round89 qualification command with an outer deadline."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--cap", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not argv or args.cap <= 0 or not args.cwd.is_dir():
        raise SystemExit("invalid command/cap/cwd")
    args.output.mkdir(parents=True, exist_ok=True)
    receipt_path = args.output / f"{args.name}.command_receipt.json"
    if receipt_path.exists():
        raise SystemExit(f"receipt already exists: {receipt_path}")
    stdout_path = args.output / f"{args.name}.stdout.log"
    stderr_path = args.output / f"{args.name}.stderr.log"
    begun = time.monotonic()
    started_utc = utc_now()
    record: dict[str, object] = {
        "name": args.name,
        "argv": argv,
        "cwd": str(args.cwd.resolve()),
        "cap_seconds": args.cap,
        "started_utc": started_utc,
        "stdout": str(stdout_path.resolve()),
        "stderr": str(stderr_path.resolve()),
    }
    if Path(argv[0]).is_file():
        record["executable_sha256_before"] = sha256(Path(argv[0]))
    process = None
    timed_out = False
    try:
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            process = subprocess.Popen(
                argv, cwd=args.cwd, stdout=stdout, stderr=stderr,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            record["pid"] = process.pid
            remaining = max(0.0, args.cap - (time.monotonic() - begun))
            try:
                process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                timed_out = True
                stopped = subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True, text=True, timeout=30,
                    check=False,
                )
                record["taskkill_exit_code"] = stopped.returncode
                record["taskkill_stdout"] = stopped.stdout
                record["taskkill_stderr"] = stopped.stderr
                process.wait(timeout=30)
        record["process_exit_observed_utc"] = utc_now()
        record["process_wall_seconds"] = time.monotonic() - begun
        record["exit_code"] = process.returncode
        record["timed_out"] = timed_out
    except BaseException as error:
        record["exception"] = repr(error)
        if process is not None and process.poll() is None:
            stopped = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True, text=True, timeout=30,
                check=False,
            )
            record["taskkill_exit_code"] = stopped.returncode
            process.wait(timeout=30)
        record["process_exit_observed_utc"] = utc_now()
        record["process_wall_seconds"] = time.monotonic() - begun
        record["exit_code"] = None if process is None else process.returncode
        record["timed_out"] = timed_out
    record["stdout_bytes"] = stdout_path.stat().st_size if stdout_path.exists() else 0
    record["stderr_bytes"] = stderr_path.stat().st_size if stderr_path.exists() else 0
    record["stdout_sha256"] = sha256(stdout_path) if stdout_path.exists() else None
    record["stderr_sha256"] = sha256(stderr_path) if stderr_path.exists() else None
    if Path(argv[0]).is_file():
        record["executable_sha256_after"] = sha256(Path(argv[0]))
    record["receipt_written_utc"] = utc_now()
    record["wrapper_wall_seconds"] = time.monotonic() - begun
    receipt_path.write_text(json.dumps(record, indent=2, sort_keys=True),
                            encoding="utf-8")
    print(json.dumps({"name": args.name, "exit_code": record["exit_code"],
                      "timed_out": timed_out,
                      "process_wall_seconds": record["process_wall_seconds"],
                      "receipt": str(receipt_path)}, sort_keys=True))
    return 0 if record["exit_code"] == 0 and not timed_out and \
        "exception" not in record else 1


if __name__ == "__main__":
    sys.exit(main())
