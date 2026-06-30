#!/usr/bin/env python3
"""Conservative audit for V-threshold or instance-specific paper-core logic.

The paper-gf-bpc-core preset is allowed to use resource guards in implementation
code, but its certificate path must not change mathematical paradigm by V, M, or
instance name.  This script focuses on the preset and certificate logic rather
than historical diagnostics.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple


ROOTS = ["src", "include", "scripts"]
INSTANCE_TOKENS = [
    "_".join(["high", "imbalance", "seed3201"]),
    "_".join(["high", "imbalance", "seed3202"]),
    "_".join(["tight", "T", "seed3101"]),
    "_".join(["tight", "T", "seed3102"]),
    "_".join(["moderate", "seed3301"]),
    "_".join(["moderate", "seed3302"]),
]
FORBIDDEN_CORE_PATTERNS = [
    re.compile(r"paper-gf-bpc-core.*instance\.V"),
    re.compile(r"paper-gf-bpc-core.*\bV\s*[<>]=?"),
]


def iter_files(root: Path) -> Iterable[Path]:
    for rel in ROOTS:
        base = root / rel
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.suffix.lower() in {".cpp", ".hpp", ".h", ".py", ".md", ".txt", ".ps1"}:
                yield path
    readme = root / "README.md"
    if readme.exists():
        yield readme


def line_context(lines: List[str], idx: int, radius: int = 10) -> str:
    start = max(0, idx - radius)
    end = min(len(lines), idx + radius + 1)
    return "\n".join(lines[start:end])


def audit(root: Path) -> Tuple[List[str], List[str]]:
    failures: List[str] = []
    warnings: List[str] = []
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            warnings.append(f"{path}: unreadable: {exc}")
            continue
        if path.match("scripts/audit_no_v_threshold_paper_core.py"):
            continue
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            stripped = line.strip()
            # Instance names are allowed in docs/results-oriented scripts.  In
            # source or solver/audit logic they are suspicious.
            if path.parts and path.parts[0] in {"src", "include"}:
                for token in INSTANCE_TOKENS:
                    if token in stripped:
                        failures.append(
                            f"{path}:{idx + 1}: instance token in solver source: {token}"
                        )
            if "paper-gf-bpc-core" in stripped:
                ctx = line_context(lines, idx)
                for pattern in FORBIDDEN_CORE_PATTERNS:
                    if pattern.search(ctx):
                        failures.append(
                            f"{path}:{idx + 1}: forbidden paper-core V/instance branch: "
                            f"{pattern.pattern}"
                        )
                if "route_mask_all_subset_enumeration_certifying = true" in ctx:
                    failures.append(
                        f"{path}:{idx + 1}: paper-core may not mark route-mask enumeration certifying"
                    )
    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    failures, warnings = audit(Path(args.root))
    lines: List[str] = []
    lines.append("no_v_threshold_paper_core_audit")
    lines.append(f"failures={len(failures)}")
    lines.append(f"warnings={len(warnings)}")
    if failures:
        lines.append("FAILURES:")
        lines.extend(failures)
    if warnings:
        lines.append("WARNINGS:")
        lines.extend(warnings)
    if not failures:
        lines.append("PASS: paper-gf-bpc-core has no detected V/M or instance-name certificate branch.")
    output = "\n".join(lines) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
