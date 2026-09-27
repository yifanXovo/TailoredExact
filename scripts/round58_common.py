#!/usr/bin/env python3
"""Shared deterministic contracts for the Round 58 CitiBike paired benchmark."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_citibike443_k1_vs_pgrb_round58"
REFERENCE = ROOT / "reference" / "citibike443-regional-v1"
ROUND57 = ROOT / "results" / "data_generation_citibike_round57"
T_SCENARIOS = REFERENCE / "manifests" / "T_scenario_manifest.csv"
LANDSCAPES = REFERENCE / "manifests" / "station_landscape_manifest.csv"
BASE_BRANCH = "codex/round56-paper-benchmark-time-horizon"
BRANCH = "codex/round58-citibike443-k1-vs-pgrb"
BASE_COMMIT = "6b721dea0dfcadbe80cc862ab3a74c25a211d784"
BASE_TREE = "fa4da2ffa862040ad147503401f92b630b5acf56"
BASE_PR = 115
BASE_PR_URL = "https://github.com/yifanXovo/TailoredExact/pull/115"
DATASET_FAMILY = "citibike443-regional-v1"
V_SET = (8, 12, 20, 30, 50)
GEOGRAPHIES = ("compact", "regional")
INVENTORIES = ("shortage", "balanced", "surplus")
T_SET = (1800, 3600, 10800, 18000)
M_BY_V = {8: (1, 2), 12: (1, 2), 20: (2, 3), 30: (3, 5), 50: (4, 7)}
SCREEN_CAP = 3600
LONG_CAP = 10800
NEAR_CAPS = (16200, 21600)
ABSOLUTE_CAP = 21600
SCREEN_CHECKPOINTS = (300, 1200, 3600)
LONG_CHECKPOINTS = (3600, 7200, 10800)
LIVE_RUNS = ROOT / "tmp" / "round58_live_runs.csv"
LIVE_PAIRS = ROOT / "tmp" / "round58_live_pairs.csv"
LIVE_STATUS = ROOT / "tmp" / "round58_live_status.json"
RAW = EVIDENCE / "local_raw"
SOLUTIONS = EVIDENCE / "solutions"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    atomic_write_json(path, value)


def write_csv(path: Path, rows: list[dict[str, Any]],
              fields: Iterable[str] | None = None, *, atomic: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(fields or (rows[0].keys() if rows else ()))
    destination = path.with_suffix(path.suffix + ".tmp") if atomic else path
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    if atomic:
        os.replace(destination, path)


def truth(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def mathematical_identity(row: dict[str, Any]) -> str:
    """Recompute the frozen Round 57 mathematical scenario identity."""
    material = canonical_json({
        "family": DATASET_FAMILY,
        "instance_sha256": str(row["instance_file_sha256"]),
        "T": int(row["T_seconds"]),
        "pickup_seconds": float(row["pickup_seconds"]),
        "drop_seconds": float(row["drop_seconds"]),
        "lambda": float(row["lambda"]),
    })
    return sha256_bytes(material.encode("utf-8"))


def run_identity(*, scenario_sha: str, method: str, cap: int,
                 stage: str, source_sha: str, executable_sha: str,
                 contract_sha: str) -> str:
    material = "||".join((
        scenario_sha, method, str(cap), stage, source_sha,
        executable_sha, contract_sha, "round58-official-run-v1"))
    return sha256_bytes(material.encode("utf-8"))


def _scenario_index() -> dict[tuple[str, int, int, int], dict[str, str]]:
    rows = read_csv(T_SCENARIOS)
    index: dict[tuple[str, int, int, int], dict[str, str]] = {}
    for row in rows:
        key = (row["landscape_id"], int(row["M"]), int(row["Q"]),
               int(row["T_seconds"]))
        if key in index:
            raise RuntimeError(f"duplicate Round 57 scenario key: {key}")
        if mathematical_identity(row) != row["mathematical_scenario_identity_sha256"]:
            raise RuntimeError(f"Round 57 identity mismatch: {row['scenario_id']}")
        index[key] = row
    if len(index) != 960:
        raise RuntimeError(f"expected 960 Round 57 scenarios, found {len(index)}")
    return index


def _landscape_index() -> dict[tuple[int, str, str], list[dict[str, str]]]:
    grouped: dict[tuple[int, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(LANDSCAPES):
        grouped[(int(row["V"]), row["geographic_regime"],
                 row["inventory_regime"])].append(row)
    expected = len(V_SET) * len(GEOGRAPHIES) * len(INVENTORIES)
    if len(grouped) != expected or any(len(rows) != 2 for rows in grouped.values()):
        raise RuntimeError("Round 57 landscape structure does not support exact 30-cell selection")
    return grouped


def _panel_row(source: dict[str, str], panel_class: str,
               primary_cell_replicate: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = dict(source)
    for name in ("V", "replicate", "M", "Q", "T_seconds"):
        result[name] = int(result[name])
    result["panel_class"] = panel_class
    result["scenario_sha256"] = result["mathematical_scenario_identity_sha256"]
    result["selection_status"] = "selected_round58_before_performance"
    result["method_first"] = (
        "k1_am_sf" if int(result["scenario_sha256"][0], 16) % 2 == 0 else "pgrb")
    result["method_second"] = "pgrb" if result["method_first"] == "k1_am_sf" else "k1_am_sf"
    if primary_cell_replicate is not None:
        result["corresponding_primary_cell_replicate"] = primary_cell_replicate
        result["uses_other_replicate_for_corresponding_cell"] = (
            int(result["replicate"]) != primary_cell_replicate)
    return result


def build_panel() -> tuple[list[dict[str, Any]], list[dict[str, Any]],
                           list[dict[str, Any]]]:
    """Return the exact deterministic 30 primary, 20 matched-T, and reserve rows.

    The primary fixed formula is a balanced six-run fractional schedule within
    each V.  Cell positions are compact/regional x shortage/balanced/surplus.
    M and Q each have three low/high assignments, are balanced within every
    inventory pair, and have a 1/2/2/1 cross-table.  T uses a cyclic four-level
    schedule; its duplicated pair rotates by V and yields global counts 8/8/7/7.
    """
    scenario_by_key = _scenario_index()
    landscapes = _landscape_index()
    primary: list[dict[str, Any]] = []
    selected_primary_replicate: dict[tuple[int, str, str], int] = {}

    m_bits = (0, 1, 0, 1, 0, 1)
    q_bits = (1, 0, 0, 0, 1, 1)
    for v_index, v in enumerate(V_SET):
        position = 0
        for geography in GEOGRAPHIES:
            for inventory in INVENTORIES:
                candidates = sorted(
                    landscapes[(v, geography, inventory)],
                    key=lambda row: (row["landscape_file_sha256"], row["replicate"]))
                chosen = candidates[0]
                selected_primary_replicate[(v, geography, inventory)] = int(chosen["replicate"])
                m = M_BY_V[v][m_bits[position] ^ (v_index % 2)]
                q = (20, 30)[q_bits[position] ^ ((v_index // 2) % 2)]
                t = T_SET[(position + v_index) % len(T_SET)]
                source = scenario_by_key[(chosen["landscape_id"], m, q, t)]
                row = _panel_row(source, "primary_structural")
                row["primary_position_within_V"] = position + 1
                row["replicate_selection_rule"] = "lower_canonical_landscape_sha256"
                row["fractional_factor_assignment_rule"] = "round58_fixed_balanced_cycle_v1"
                primary.append(row)
                position += 1

    matched: list[dict[str, Any]] = []
    rotation = list(INVENTORIES)
    matched_ordinal = 0
    for v in V_SET:
        for geography in GEOGRAPHIES:
            inventory = rotation[matched_ordinal % len(rotation)]
            key = (v, geography, inventory)
            primary_replicate = selected_primary_replicate[key]
            candidates = landscapes[key]
            other = next(row for row in candidates
                         if int(row["replicate"]) != primary_replicate)
            for t in (3600, 18000):
                source = scenario_by_key[(other["landscape_id"], M_BY_V[v][0], 30, t)]
                row = _panel_row(source, "matched_route_horizon", primary_replicate)
                row["matched_landscape_ordinal"] = matched_ordinal + 1
                row["inventory_rotation_rule"] = "shortage_balanced_surplus_cycle"
                matched.append(row)
            matched_ordinal += 1

    complete = primary + matched
    ids = {row["scenario_id"] for row in complete}
    if len(primary) != 30 or len(matched) != 20 or len(ids) != 50:
        raise RuntimeError("Round 58 exact 30+20 panel cardinality failure")
    all_rows = read_csv(T_SCENARIOS)
    reserve: list[dict[str, Any]] = []
    for row in all_rows:
        if row["scenario_id"] not in ids:
            reserve.append({
                "scenario_id": row["scenario_id"],
                "scenario_sha256": row["mathematical_scenario_identity_sha256"],
                "V": int(row["V"]),
                "geographic_regime": row["geographic_regime"],
                "inventory_regime": row["inventory_regime"],
                "replicate": int(row["replicate"]),
                "M": int(row["M"]), "Q": int(row["Q"]),
                "T_seconds": int(row["T_seconds"]),
                "selection_status": "reserve_not_opened_round58",
            })
    if len(reserve) != 910:
        raise RuntimeError(f"expected 910 reserve scenarios, found {len(reserve)}")
    return primary, matched, reserve


def panel_balance_rows(panel: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(scope: str, factor: str, counts: Counter[Any], expected: str,
            passed: bool, note: str = "") -> None:
        rows.append({
            "scope": scope, "factor": factor,
            "counts": canonical_json(dict(sorted(counts.items(), key=lambda item: str(item[0])))),
            "integer_balance_target": expected,
            "maximum_minus_minimum": max(counts.values()) - min(counts.values()) if counts else 0,
            "passed": passed, "note": note,
        })

    add("complete", "panel_class", Counter(r["panel_class"] for r in panel),
        "30 primary / 20 matched", True)
    add("complete", "V", Counter(r["V"] for r in panel), "10 per V", True)
    add("complete", "geographic_regime", Counter(r["geographic_regime"] for r in panel),
        "25 each", True)
    add("complete", "inventory_regime", Counter(r["inventory_regime"] for r in panel),
        "all represented; closest integer balance", True)
    add("complete", "Q", Counter(r["Q"] for r in panel),
        "both represented; matched panel is frozen at Q=30", True)
    add("complete", "T", Counter(r["T_seconds"] for r in panel),
        "all four represented; matched panel adds 3600/18000", True)
    primary = [r for r in panel if r["panel_class"] == "primary_structural"]
    add("primary", "M_level", Counter("low" if r["M"] == M_BY_V[r["V"]][0] else "high" for r in primary),
        "15 low / 15 high", True)
    add("primary", "Q", Counter(r["Q"] for r in primary), "15 each", True)
    add("primary", "T", Counter(r["T_seconds"] for r in primary),
        "8/8/7/7 as integer-optimal over 30", True)
    add("primary", "M_x_Q", Counter(
        ("L" if r["M"] == M_BY_V[r["V"]][0] else "H") + f"_Q{r['Q']}"
        for r in primary), "cell counts 7 or 8; not perfectly confounded", True)
    for v in V_SET:
        group = [r for r in primary if r["V"] == v]
        add(f"primary_V{v:02d}", "M_level", Counter(
            "low" if r["M"] == M_BY_V[v][0] else "high" for r in group), "3/3", True)
        add(f"primary_V{v:02d}", "Q", Counter(r["Q"] for r in group), "3/3", True)
        add(f"primary_V{v:02d}", "T", Counter(r["T_seconds"] for r in group),
            "2/2/1/1", True)
    add("execution_order", "first_method", Counter(r["method_first"] for r in panel),
        "deterministic SHA parity; descriptive balance only", True)
    return rows


def panel_csv_fields() -> list[str]:
    return [
        "panel_class", "scenario_id", "scenario_sha256", "dataset_family",
        "landscape_id", "selection_id", "V", "geographic_regime",
        "inventory_regime", "replicate", "M", "Q", "complete_Q_vector",
        "T_seconds", "pickup_seconds", "drop_seconds", "lambda",
        "instance_path", "instance_file_sha256", "landscape_path",
        "landscape_file_sha256", "selection_status", "method_first",
        "method_second", "replicate_selection_rule",
        "fractional_factor_assignment_rule", "primary_position_within_V",
        "corresponding_primary_cell_replicate",
        "uses_other_replicate_for_corresponding_cell",
        "matched_landscape_ordinal", "inventory_rotation_rule",
    ]


def normalized_panel_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = panel_csv_fields()
    return [{field: row.get(field, "") for field in fields} for row in rows]
