"""Offline audit of the candidate-only Round92 model-generation receipt.

This module reads evidence after a timed process exits. It never imports a
solver or changes the optimization model.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
import re


FIELDS = {
    "leaf_id", "incumbent_epoch", "model_path", "model_sha256", "model_scope",
    "model_written", "rows", "first_row_id", "last_row_id", "B", "reason",
    "uniform_envelope_floor_certified", "cache_hit", "cache_hits_total",
    "cache_misses_total", "normalization_seconds", "lookup_seconds",
    "preparation_seconds", "proof_version", "c_lower", "lmin_lower",
    "lmin_upper", "physical_horizon_upper", "common_horizon_upper",
    "quotient_lower", "quotient_upper", "failure_reason",
}
SHA = re.compile(r"[0-9a-f]{64}\Z")
ROW = re.compile(r"^\s*c(\d+):\s*(.*?)\s*$")


def _int(value: str, label: str) -> int:
    parsed = int(value)
    assert str(parsed) == value, (label, value)
    return parsed


def _finite(value: str, label: str) -> float:
    parsed = float(value)
    assert math.isfinite(parsed), (label, value)
    return parsed


def _current_rows(path: Path, first: int, last: int, count: int, b: int) -> None:
    # Writer emits the added row inside each vehicle block; its IDs are
    # increasing but not contiguous. Locate the exact canonical expression.
    rows: dict[int, str] = {}
    with path.open(encoding="utf-8", errors="strict") as stream:
        for line in stream:
            match = ROW.match(line)
            if match:
                rows[int(match.group(1))] = match.group(2)
    assert first in rows and last in rows
    first_pickups = re.findall(r"\bp_0_(\d+)\b", rows[first])
    stations = len(first_pickups)
    assert stations > 0
    assert first_pickups == [str(i) for i in sorted(
        range(1, stations + 1), key=lambda i: f"p_0_{i}")]
    found = []
    for vehicle in range(count):
        # Expr is std::map<string,double>, hence LP terms are lexicographic
        # (station 10 precedes station 2), not insertion/numeric order.
        pickup_ids = sorted(range(1, stations + 1), key=lambda i: f"p_{vehicle}_{i}")
        depot_ids = sorted(range(1, stations + 1), key=lambda i: f"x_{vehicle}_0_{i}")
        expression = " + ".join(f"p_{vehicle}_{i}" for i in pickup_ids)
        if b:
            coefficient = "" if b == 1 else f"{b} "
            expression += "".join(
                f" - {coefficient}x_{vehicle}_0_{i}" for i in depot_ids)
        expression += " <= 0"
        matches = [row_id for row_id, actual in rows.items() if actual == expression]
        assert len(matches) == 1, (path, vehicle, "missing or duplicate exact added row")
        found.append(matches[0])
    assert found == sorted(found) and len(set(found)) == count
    assert found[0] == first and found[-1] == last


def audit(destination: Path, arm: str, result: dict | None, reason: str,
          sha, read) -> dict:
    path = destination / "external" / "round92_handling_activation_rows.csv"
    if arm == "ENS-C":
        assert not path.exists(), "default-off run emitted a candidate ledger"
        return {"status": "not_applicable_default_off", "model_generations": 0}
    assert arm == "H-ACT"
    if not path.is_file() or path.is_symlink():
        if reason == "normal_return":
            raise AssertionError("completed candidate run missing row ledger")
        return {"status": "unknown_missing_ledger_after_interruption",
                "model_generations": None}
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames is not None and set(reader.fieldnames) == FIELDS
        rows = [dict(row, ledger_row_number=index + 2)
                for index, row in enumerate(reader)]
    assert all(None not in row and all(value is not None for value in row.values())
               for row in rows), "incomplete candidate ledger"
    model_dir = (destination / "external" / "models").resolve()
    latest: dict[str, dict] = {}
    normalized = []
    for row in rows:
        assert row["leaf_id"] and SHA.fullmatch(row["model_sha256"])
        assert row["model_scope"].endswith(
            ";round92_static_rounded_handling_activation")
        assert row["failure_reason"] == ""
        assert _int(row["proof_version"], "proof_version") == 2
        assert _int(row["model_written"], "model_written") == 1
        assert _int(row["incumbent_epoch"], "epoch") >= 0
        assert _int(row["cache_hit"], "cache_hit") in {0, 1}
        assert _int(row["uniform_envelope_floor_certified"], "floor flag") in {0, 1}
        count = _int(row["rows"], "rows")
        b = _int(row["B"], "B")
        assert count >= 0 and b >= 0
        first = _int(row["first_row_id"], "first_row_id")
        last = _int(row["last_row_id"], "last_row_id")
        if count:
            assert first >= 1 and last >= first + count - 1
        else:
            assert first == last == -1
            assert row["reason"] == "zero_common_lower_service_has_no_quantity_bound"
        for field in ("cache_hits_total", "cache_misses_total"):
            assert _int(row[field], field) >= 0
        for field in ("normalization_seconds", "lookup_seconds",
                      "preparation_seconds", "c_lower", "lmin_lower",
                      "lmin_upper", "physical_horizon_upper",
                      "common_horizon_upper", "quotient_lower", "quotient_upper"):
            _finite(row[field], field)
        model = Path(row["model_path"]).resolve(strict=True)
        assert model.is_file() and not model.is_symlink()
        assert model.parent == model_dir and model.name == row["leaf_id"] + ".lp"
        latest[row["leaf_id"]] = row
        normalized.append({"ledger_row_number": row["ledger_row_number"],
                           "leaf_id": row["leaf_id"], "incumbent_epoch": row["incumbent_epoch"],
                           "model_sha256": row["model_sha256"], "model_scope": row["model_scope"],
                           "rows": count, "B": b, "cache_hit": row["cache_hit"],
                           "proof_version": 2})
    current = []
    for leaf, row in latest.items():
        model = Path(row["model_path"])
        actual = sha(model)
        if result is not None:
            assert actual == row["model_sha256"], (leaf, "latest canonical bytes differ")
        if actual == row["model_sha256"] and _int(row["rows"], "rows"):
            _current_rows(model, _int(row["first_row_id"], "first_row_id"),
                          _int(row["last_row_id"], "last_row_id"),
                          _int(row["rows"], "rows"), _int(row["B"], "B"))
        current.append({"leaf_id": leaf, "canonical_path": str(model),
                        "canonical_sha256_at_audit": actual,
                        "latest_ledger_sha256": row["model_sha256"],
                        "current_bytes_verified": actual == row["model_sha256"]})
    if result is not None:
        assert result["external_gini_tree_canonical_artifact_generation_count"] == len(rows), (
            "candidate model generation/ledger cardinality")
        optimize = destination / "external" / "paper_optimize_ledger.csv"
        assert optimize.is_file() and not optimize.is_symlink(), "normal result missing Optimize ledger"
        assert Path(result["external_gini_tree_optimize_ledger_path"]).resolve() == optimize.resolve()
        with optimize.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            assert reader.fieldnames is not None and {
                "leaf_id", "model_sha256", "solve_kind", "native_log"} <= set(reader.fieldnames)
            calls = list(reader)
        ledger_models = {(r["leaf_id"], r["model_sha256"]) for r in rows}
        assert all((call["leaf_id"], call["model_sha256"]) in ledger_models
                   for call in calls), "Optimize call without candidate model-generation receipt"
        status = "complete_model_generation_evidence" if rows else "not_exposed_zero_model_generation"
    else:
        status = "partial_unknown_after_interruption"
    return {"status": status, "ledger_path": str(path), "ledger_sha256": sha(path),
            "model_generations": len(rows), "models_with_added_row": sum(r["rows"] > 0 for r in normalized),
            "rows_total_across_generations": sum(r["rows"] for r in normalized),
            "cache_hits": sum(r["cache_hit"] == "1" for r in normalized),
            "historical_overwritten_model_bytes_archived": False,
            "historical_model_rows": normalized, "latest_canonical_models": current}
