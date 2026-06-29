#!/usr/bin/env python3
"""Conservative scan for instance-specific solver logic.

The sealed paper pipeline may mention instance names in input paths, generated
data manifests, summaries, or human-readable reports.  It must not branch on
specific instance names or known objective values inside solver decision logic.
This audit scans production C++ and non-report scripts.  Generator scripts are
allowed to contain deterministic instance ids because they create benchmark
data rather than selecting solver behavior.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PATTERNS = [
    r"high_imbalance_seed3201",
    r"high_imbalance_seed3202",
    r"tight_T_seed3101",
    r"tight_T_seed3102",
    r"moderate_seed3301",
    r"moderate_seed3302",
    r"0\.718504070755",
    r"1\.74931345205",
    r"0\.107252734134",
    r"0\.357200583208",
]

SCAN_GLOBS = [
    "src/**/*.cpp",
    "src/**/*.hpp",
    "include/**/*.hpp",
    "scripts/*.py",
]

ALLOWLIST = {
    "scripts/generate_hard_exact_stress_instances.py",
    "scripts/generate_capacity_inventory_variants.py",
    "scripts/generate_reference_instances.py",
    "scripts/audit_no_instance_special_cases.py",
}

ALLOW_PREFIXES = (
    "scripts/summarize_",
    "scripts/run_",
)


def should_scan(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if rel in ALLOWLIST:
        return False
    return not any(rel.startswith(prefix) for prefix in ALLOW_PREFIXES)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    regexes = [re.compile(pattern) for pattern in FORBIDDEN_PATTERNS]
    failures: list[str] = []

    for glob in SCAN_GLOBS:
        for path in sorted(root.glob(glob)):
            if not path.is_file() or not should_scan(path):
                continue
            rel = path.relative_to(root).as_posix()
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                failures.append(f"{rel}: read_error: {exc}")
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                for regex in regexes:
                    if regex.search(line):
                        failures.append(f"{rel}:{lineno}: {line.strip()}")

    lines = []
    if failures:
        lines.append("FAIL: instance-specific solver logic patterns found")
        lines.extend(failures)
    else:
        lines.append("PASS: no instance-specific solver logic patterns found")
        lines.append("Scope: src/, include/, and non-report scripts.")
        lines.append("Allowed: deterministic data generator ids and summary/report scripts.")

    output = "\n".join(lines) + "\n"
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
