#!/usr/bin/env python3
"""Reusable strict P-GRB model-fingerprint freeze and binding helpers.

The discovery probe and the benchmark solve remain separate operations.  A
benchmark row is admissible only when its input, executable, solver contract,
native model fingerprint, canonical LP hash, and objective-section hash match
the pre-frozen entry.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def objective_fingerprint(lp_path: Path) -> str:
    lines = lp_path.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        start = next(i for i, line in enumerate(lines)
                     if line.strip().lower() in {"minimize", "maximize"})
        end = next(i for i, line in enumerate(lines[start + 1:], start + 1)
                   if line.strip().lower().startswith("subject to"))
    except StopIteration as exc:
        raise RuntimeError(
            f"canonical LP objective section unavailable: {lp_path}") from exc
    canonical = "\n".join(line.rstrip() for line in lines[start:end]) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def freeze_entry(*, instance_id: str, input_path: str, input_sha256: str,
                 time_limit: float, executable_sha256: str,
                 native_fingerprint: int, canonical_lp: Path,
                 native_domain: Mapping[str, Any],
                 solver_contract: Mapping[str, Any],
                 probe_metadata: Mapping[str, Any]) -> dict[str, Any]:
    if not canonical_lp.is_file() or native_fingerprint == 0:
        raise RuntimeError("fingerprint discovery did not construct a model")
    if native_domain.get("native_domain_audit_passed") is not True:
        raise RuntimeError("native variable/row/domain identity did not pass")
    return {
        "instance_id": instance_id,
        "input_path": input_path,
        "input_sha256": input_sha256,
        "T": time_limit,
        "expected_gurobi_model_fingerprint": native_fingerprint,
        "canonical_model_sha256": sha256(canonical_lp),
        "objective_fingerprint_sha256": objective_fingerprint(canonical_lp),
        "variable_row_domain_identity": dict(native_domain),
        "executable_sha256": executable_sha256,
        "solver": dict(solver_contract),
        **dict(probe_metadata),
    }


def audit_binding(entry: Mapping[str, Any], *, input_file: Path,
                  executable: Path, canonical_lp: Path,
                  result: Mapping[str, Any]) -> tuple[bool, str]:
    checks = {
        "input_sha256_mismatch": sha256(input_file) == entry.get("input_sha256"),
        "executable_sha256_mismatch": (
            sha256(executable) == entry.get("executable_sha256")),
        "canonical_model_sha256_mismatch": (
            sha256(canonical_lp) == entry.get("canonical_model_sha256")),
        "objective_fingerprint_mismatch": (
            objective_fingerprint(canonical_lp) ==
            entry.get("objective_fingerprint_sha256")),
        "native_model_fingerprint_mismatch": (
            int(result.get("gurobi_model_fingerprint", 0)) ==
            int(entry.get("expected_gurobi_model_fingerprint", -1))),
        "native_domain_audit_failed": (
            result.get("gurobi_native_domain_audit_passed") is True),
    }
    failed = [reason for reason, passed in checks.items() if not passed]
    return (not failed, "strict_binding_passed" if not failed else ";".join(failed))
