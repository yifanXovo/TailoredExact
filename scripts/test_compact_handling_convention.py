#!/usr/bin/env python3
"""Regression test for the compact-BC aggregate handling convention.

The compact model's route duration convention charges handling as

    travel + (pickup_time + drop_time) * pickup_quantity <= T.

The paper-core aggregate handling cut must therefore not contain drop
variables.  This test asks ExactEBRP to emit a compact interval LP and checks
the global handling-capacity row, identified by the aggregate vehicle time
right-hand side, for stray ``d_k_i`` terms.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def first_line_vm(path: Path) -> tuple[int, int]:
    line = path.read_text(encoding="utf-8").splitlines()[0]
    values = [int(x) for x in re.findall(r"-?\d+", line)]
    if len(values) < 2:
        raise RuntimeError(f"cannot parse V/M from first line of {path}")
    return values[0], values[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", default="build/ExactEBRP.exe")
    parser.add_argument("--instance", default="reference/regen_candidate_V12_M2_average.txt")
    parser.add_argument("--out-dir", default="results/gf_compact_bc_round/handling_convention_test")
    parser.add_argument("--T", type=float, default=3600.0)
    args = parser.parse_args()

    exe = Path(args.exe)
    instance = Path(args.instance)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    lp_path = out_dir / "handling_convention.lp"
    json_path = out_dir / "handling_convention.json"

    _, m = first_line_vm(instance)
    aggregate_rhs = args.T * m

    cmd = [
        str(exe),
        "--method", "interval-cutoff-oracle",
        "--input", str(instance),
        "--lambda", "0.15",
        "--T", str(args.T),
        "--time-limit", "1",
        "--interval-exact-cutoff-oracle", "compact-mip",
        "--interval-exact-oracle-mode", "objective-bound",
        "--interval-exact-cutoff-gamma-L", "0",
        "--interval-exact-cutoff-gamma-U", "1",
        "--interval-exact-cutoff-UB", "999",
        "--interval-exact-cutoff-time-limit", "1",
        "--global-handling-capacity-cuts", "true",
        "--required-movement-cuts", "true",
        "--compact-bc-support-duration-cuts", "false",
        "--interval-exact-cutoff-export-lp", str(lp_path),
        "--out", str(json_path),
    ]
    subprocess.run(cmd, check=False)
    if not lp_path.exists():
        raise RuntimeError(f"expected generated LP at {lp_path}")

    rhs_re = re.compile(rf"<=\s*{aggregate_rhs:g}\s*$")
    aggregate_rows = []
    for raw_line in lp_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if rhs_re.search(line) and " p_" in f" {line}":
            aggregate_rows.append(line)
    if not aggregate_rows:
        raise RuntimeError("did not find aggregate handling-capacity row in generated LP")
    bad = [line for line in aggregate_rows if " d_" in f" {line}"]
    if bad:
        raise AssertionError(
            "aggregate handling-capacity row contains drop variables; "
            "old unsafe cunit*(p+d) convention is present"
        )
    print(f"handling convention OK: {len(aggregate_rows)} aggregate row(s) charge pickup variables only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
