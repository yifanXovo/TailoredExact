#!/usr/bin/env python3
"""Round 21 diagnostic-only connectivity-flow degeneracy forensics.

This runner deliberately operates on *copies* of exported F0 global-root LPs.
It relaxes every integer/binary declaration, solves the original root LP, and
then optimizes two connectivity-flow aggregates over a narrow numerical band
around that root-optimal objective face.  None of the generated models,
solutions, or measurements are consumed by an ExactEBRP production solve.

Expected source instances (in deterministic order):
  moderate_seed3301, tight_T_seed3101, high_imbalance_seed3202

Explicit source mapping is repeatable, for example:
  --lp moderate_seed3301=results/.../global_root.lp

The default discovery searches Round 21 JSON manifests/results first, then
global-root-looking LP files beneath the Round 21 results directory.  A source
is accepted as F0 only when its conn_k_i_j columns form the complete directed
arc family, including every station-to-depot return-flow column.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
ROUND_RESULTS = ROOT / "results" / "gf_global_gini_tree_strict_flow_round"
DIAGNOSTICS = ROUND_RESULTS / "diagnostics" / "flow_degeneracy"
DEGENERACY_CSV = ROUND_RESULTS / "flow_degeneracy_diagnostics.csv"
MODEL_SIZE_CSV = ROUND_RESULTS / "flow_model_size_and_presolve.csv"
DEFAULT_CPLEX = Path(
    r"C:\Program Files\IBM\ILOG\CPLEX_Studio2211\cplex\bin\x64_win64\cplex.exe"
)
TARGET_INSTANCES = (
    "moderate_seed3301",
    "tight_T_seed3101",
    "high_imbalance_seed3202",
)
SOLVES: Tuple[Tuple[str, str, str], ...] = (
    ("root_original_objective", "original", "min"),
    ("face_min_total_return_flow", "return", "min"),
    ("face_max_total_return_flow", "return", "max"),
    ("face_min_total_conn_flow", "all", "min"),
    ("face_max_total_conn_flow", "all", "max"),
)
FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
NAME = r"[A-Za-z_][A-Za-z0-9_.$]*"
CONN_RE = re.compile(r"\bconn_(\d+)_(\d+)_(\d+)\b")
X_RE = re.compile(r"\bx_(\d+)_(\d+)_(\d+)\b")
SECTION_RE = re.compile(
    r"^\s*(minimize|minimum|min|maximize|maximum|max|subject\s+to|such\s+that|"
    r"st|s\.t\.|bounds|bound|generals|general|gen|binaries|binary|bin|"
    r"semi-continuous|semicontinuous|sos|end)\s*$",
    re.IGNORECASE,
)


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except (OSError, ValueError):
        return str(path.resolve()).replace("\\", "/")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lp_text(path: Path) -> str:
    if path.suffix.lower() == ".gz":
        with gzip.open(path, "rt", encoding="utf-8-sig") as stream:
            return stream.read()
    return path.read_text(encoding="utf-8-sig")


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def as_float(value: Any, default: float = math.nan) -> float:
    try:
        answer = float(value)
    except (TypeError, ValueError):
        return default
    return answer if math.isfinite(answer) else default


def fmt(value: float) -> str:
    return format(value, ".17g")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str]) -> None:
    material = list(rows)
    names = list(fields)
    for row in material:
        for key in row:
            if key not in names:
                names.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def flatten_result_json(value: Any) -> List[Mapping[str, Any]]:
    if isinstance(value, dict):
        answer: List[Mapping[str, Any]] = [value]
        results = value.get("results")
        if isinstance(results, list):
            answer.extend(item for item in results if isinstance(item, dict))
        return answer
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def resolve_recorded_path(raw: Any, owner: Path) -> Optional[Path]:
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw.strip().strip('"'))
    candidates = [path] if path.is_absolute() else [ROOT / path, owner.parent / path]
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:
            pass
    return candidates[0].resolve() if candidates else None


def parse_explicit_lp(values: Sequence[str]) -> Dict[str, Path]:
    answer: Dict[str, Path] = {}
    for raw in values:
        entries = [part.strip() for part in raw.split(",") if part.strip()]
        for entry in entries:
            if "=" not in entry:
                raise ValueError(f"--lp expects INSTANCE=PATH, received {entry!r}")
            instance, filename = entry.split("=", 1)
            instance, filename = instance.strip(), filename.strip().strip('"')
            if instance not in TARGET_INSTANCES:
                raise ValueError(
                    f"unknown --lp instance {instance!r}; expected one of "
                    + ", ".join(TARGET_INSTANCES)
                )
            if instance in answer:
                raise ValueError(f"duplicate --lp mapping for {instance}")
            path = Path(filename)
            answer[instance] = (path if path.is_absolute() else ROOT / path).resolve()
    return answer


@dataclass
class F0Inventory:
    valid: bool = False
    reason: str = "not_evaluated"
    conn_names: List[str] = field(default_factory=list)
    return_names: List[str] = field(default_factory=list)
    x_names: List[str] = field(default_factory=list)
    vehicles: int = 0
    stations: int = 0
    expected_conn_columns: int = 0
    missing_conn_arcs: int = 0
    unexpected_conn_arcs: int = 0
    has_integer_sections: bool = False


def inspect_f0_text(text: str) -> F0Inventory:
    conn_tuples = {(int(k), int(i), int(j)) for k, i, j in CONN_RE.findall(text)}
    x_tuples = {(int(k), int(i), int(j)) for k, i, j in X_RE.findall(text)}
    answer = F0Inventory(
        conn_names=sorted(f"conn_{k}_{i}_{j}" for k, i, j in conn_tuples),
        return_names=sorted(f"conn_{k}_{i}_{j}" for k, i, j in conn_tuples if j == 0),
        x_names=sorted(f"x_{k}_{i}_{j}" for k, i, j in x_tuples),
        has_integer_sections=bool(
            re.search(r"(?im)^\s*(?:generals?|gen|binaries|binary|bin)\s*$", text)
        ),
    )
    if not conn_tuples:
        answer.reason = "no_connectivity_flow_columns"
        return answer
    vehicle_ids = sorted({k for k, _, _ in conn_tuples})
    node_ids = sorted({node for _, i, j in conn_tuples for node in (i, j)})
    if not vehicle_ids or vehicle_ids != list(range(vehicle_ids[-1] + 1)):
        answer.reason = "noncontiguous_connectivity_vehicle_indices"
        return answer
    if not node_ids or node_ids[0] != 0 or node_ids != list(range(node_ids[-1] + 1)):
        answer.reason = "noncontiguous_connectivity_node_indices"
        return answer
    answer.vehicles = len(vehicle_ids)
    answer.stations = node_ids[-1]
    expected = {
        (k, i, j)
        for k in vehicle_ids
        for i in node_ids
        for j in node_ids
        if i != j
    }
    answer.expected_conn_columns = len(expected)
    answer.missing_conn_arcs = len(expected - conn_tuples)
    answer.unexpected_conn_arcs = len(conn_tuples - expected)
    expected_returns = answer.vehicles * answer.stations
    if answer.missing_conn_arcs or answer.unexpected_conn_arcs:
        answer.reason = (
            f"not_complete_F0_arc_family:missing={answer.missing_conn_arcs}:"
            f"unexpected={answer.unexpected_conn_arcs}"
        )
        return answer
    if len(answer.return_names) != expected_returns:
        answer.reason = (
            f"not_F0_return_family:found={len(answer.return_names)}:"
            f"expected={expected_returns}"
        )
        return answer
    if not expected.issubset(x_tuples):
        answer.reason = f"missing_matching_x_columns:{len(expected - x_tuples)}"
        return answer
    if not answer.has_integer_sections:
        answer.reason = "source_is_not_an_exported_MILP:no_Generals_or_Binaries_section"
        return answer
    answer.valid = True
    answer.reason = "complete_F0_directed_arc_and_return_flow_family"
    return answer


def inspect_f0(path: Path) -> Tuple[F0Inventory, str]:
    try:
        text = lp_text(path)
    except (OSError, UnicodeError, gzip.BadGzipFile) as error:
        return F0Inventory(reason=f"source_read_failed:{type(error).__name__}:{error}"), ""
    return inspect_f0_text(text), text


def record_instance(record: Mapping[str, Any]) -> str:
    keys = (
        "round21_instance",
        "instance",
        "instance_name",
        "round20_instance",
    )
    for key in keys:
        value = record.get(key)
        if isinstance(value, str):
            for instance in TARGET_INSTANCES:
                if instance.lower() in value.lower():
                    return instance
    run_id = record.get("run_id", record.get("round21_run_id", ""))
    if isinstance(run_id, str):
        for instance in TARGET_INSTANCES:
            if instance.lower() in run_id.lower():
                return instance
    return ""


def discover_sources(explicit: Mapping[str, Path]) -> Tuple[Dict[str, Path], Dict[str, str]]:
    found: Dict[str, Path] = dict(explicit)
    origins: Dict[str, str] = {instance: "explicit_--lp" for instance in explicit}
    candidates: Dict[str, List[Tuple[int, float, Path, str]]] = {
        instance: [] for instance in TARGET_INSTANCES if instance not in found
    }
    path_keys = (
        "global_gini_tree_root_model_path",
        "global_gini_tree_root_export_path",
        "root_lp",
        "root_model_path",
        "global_root_lp",
    )
    if ROUND_RESULTS.exists():
        for json_path in ROUND_RESULTS.rglob("*.json"):
            if DIAGNOSTICS in json_path.parents:
                continue
            for record in flatten_result_json(load_json(json_path)):
                instance = record_instance(record)
                if not instance or instance not in candidates:
                    continue
                variant = str(
                    record.get(
                        "global_gini_tree_root_connectivity_flow_variant_resolved",
                        record.get("root_connectivity_flow_variant_resolved", ""),
                    )
                ).strip().upper()
                for key in path_keys:
                    candidate = resolve_recorded_path(record.get(key), json_path)
                    if candidate is None or not candidate.is_file():
                        continue
                    score = 100 + (50 if variant == "F0" else 0)
                    candidates[instance].append(
                        (score, candidate.stat().st_mtime, candidate, f"json:{rel(json_path)}:{key}")
                    )
        lp_candidates = list(ROUND_RESULTS.rglob("*.lp")) + list(
            ROUND_RESULTS.rglob("*.lp.gz")
        )
        for lp_path in lp_candidates:
            if DIAGNOSTICS in lp_path.parents:
                continue
            lowered = str(lp_path).lower()
            instance = next(
                (name for name in candidates if name.lower() in lowered), ""
            )
            if not instance:
                continue
            name_score = 20 if "global_root" in lp_path.name.lower() else 0
            f0_score = 20 if re.search(r"(?:^|[_\-])f0(?:[_\-.]|$)", lowered) else 0
            candidates[instance].append(
                (name_score + f0_score, lp_path.stat().st_mtime, lp_path.resolve(), "lp_scan")
            )
    for instance, options in candidates.items():
        # Structural validation outranks filenames/metadata.  Among valid F0
        # sources, prefer stronger metadata score and then the newest export.
        valid_options: List[Tuple[int, float, Path, str]] = []
        for option in options:
            inventory, _ = inspect_f0(option[2])
            if inventory.valid:
                valid_options.append(option)
        if valid_options:
            chosen = max(valid_options, key=lambda item: (item[0], item[1]))
            found[instance] = chosen[2]
            origins[instance] = chosen[3]
    return found, origins


def section_name(line: str) -> str:
    match = SECTION_RE.match(line)
    return match.group(1).lower() if match else ""


def continuous_relaxation(text: str, source: Path) -> str:
    """Remove integer declarations while preserving all bounds and rows."""
    if re.search(r"(?im)^\s*(?:semi-?continuous|semi-?integer|sos)\s*$", text):
        raise ValueError("unsupported noncontinuous LP section outside Generals/Binaries")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    output = [
        "\\ Round 21 DIAGNOSTIC ONLY continuous relaxation; never certificate evidence",
        f"\\ Source: {rel(source)}",
        f"\\ Source SHA256: {sha256(source)}",
    ]
    dropping = False
    saw_end = False
    for line in lines:
        section = section_name(line)
        if section in {"generals", "general", "gen", "binaries", "binary", "bin"}:
            dropping = True
            continue
        if dropping:
            if section == "end":
                dropping = False
                output.append("End")
                saw_end = True
            elif section:
                # The compact writer places End after the integrality blocks.
                # Retain any unexpected later section and continue fail-visibly.
                dropping = False
                output.append(line)
            continue
        output.append(line)
        if section == "end":
            saw_end = True
    if not saw_end:
        raise ValueError("source LP has no End section")
    relaxed = "\n".join(output).rstrip() + "\n"
    if re.search(r"(?im)^\s*(?:generals?|gen|binaries|binary|bin)\s*$", relaxed):
        raise ValueError("integrality section survived relaxation")
    return relaxed


def objective_parts(lp_text: str) -> Tuple[str, str, int, int]:
    lines = lp_text.splitlines()
    objective_index = -1
    subject_index = -1
    sense = ""
    for index, line in enumerate(lines):
        section = section_name(line)
        if section in {"minimize", "minimum", "min", "maximize", "maximum", "max"}:
            objective_index = index
            sense = "max" if section.startswith("max") else "min"
            break
    if objective_index < 0:
        raise ValueError("LP objective section not found")
    for index in range(objective_index + 1, len(lines)):
        section = section_name(lines[index])
        if section in {"subject to", "such that", "st", "s.t."}:
            subject_index = index
            break
    if subject_index < 0:
        raise ValueError("LP Subject To section not found")
    raw = " ".join(line.strip() for line in lines[objective_index + 1 : subject_index]).strip()
    if ":" in raw:
        raw = raw.split(":", 1)[1].strip()
    if not raw:
        raise ValueError("LP objective expression is empty")
    return sense, raw, objective_index, subject_index


def parse_linear_expression(expression: str) -> Dict[str, float]:
    """Parse the simple CPLEX-LP linear expressions emitted by ExactEBRP."""
    token_re = re.compile(rf"\s*([+-]?)\s*(?:({FLOAT})\s+)?({NAME})")
    position = 0
    coefficients: Dict[str, float] = {}
    while position < len(expression):
        match = token_re.match(expression, position)
        if not match:
            remainder = expression[position:].strip()
            if not remainder:
                break
            raise ValueError(f"unsupported objective token near {remainder[:80]!r}")
        sign, number, name = match.groups()
        coefficient = float(number) if number is not None else 1.0
        if sign == "-":
            coefficient = -coefficient
        coefficients[name] = coefficients.get(name, 0.0) + coefficient
        position = match.end()
    if not coefficients:
        raise ValueError("no variable terms parsed from original objective")
    return coefficients


def wrapped_sum(names: Sequence[str], label: str = "diag_obj") -> str:
    if not names:
        raise ValueError("cannot build an empty diagnostic objective")
    lines: List[str] = []
    for offset in range(0, len(names), 8):
        terms = names[offset : offset + 8]
        prefix = f" {label}: " if offset == 0 else "   + "
        separator = " + "
        lines.append(prefix + separator.join(terms))
    return "\n".join(lines)


def face_model(
    relaxed: str,
    aggregate_names: Sequence[str],
    secondary_sense: str,
    original_optimum: float,
    face_tolerance: float,
) -> str:
    _, expression, objective_index, subject_index = objective_parts(relaxed)
    lines = relaxed.splitlines()
    heading = "Maximize" if secondary_sense == "max" else "Minimize"
    replacement = [heading, wrapped_sum(aggregate_names)]
    upper = original_optimum + face_tolerance
    lower = original_optimum - face_tolerance
    face_rows = [
        f" diag_original_face_ub: {expression} <= {fmt(upper)}",
        f" diag_original_face_lb: {expression} >= {fmt(lower)}",
    ]
    result = (
        lines[:objective_index]
        + replacement
        + [lines[subject_index]]
        + face_rows
        + lines[subject_index + 1 :]
    )
    return "\n".join(result).rstrip() + "\n"


def text_model_inventory(lp_text: str) -> Dict[str, Any]:
    """Inventory generated LP text; CPLEX log values remain authoritative."""
    lines = lp_text.splitlines()
    bounds_start = -1
    subject_start = -1
    constraint_end = -1
    for index, line in enumerate(lines):
        section = section_name(line)
        if section in {"subject to", "such that", "st", "s.t."}:
            subject_start = index + 1
        elif section in {"bounds", "bound"}:
            bounds_start = index + 1
            constraint_end = index
            break
    bound_names: set[str] = set()
    if bounds_start >= 0:
        for line in lines[bounds_start:]:
            if section_name(line):
                break
            names = re.findall(rf"\b({NAME})\b", line)
            # ExactEBRP bounds have one variable; exclude LP keywords.
            for name in names:
                if name.lower() not in {"free", "infinity", "inf"}:
                    bound_names.add(name)
    rows = 0
    nonzeros = 0
    if subject_start >= 0 and constraint_end >= subject_start:
        records: List[str] = []
        current = ""
        for line in lines[subject_start:constraint_end]:
            if re.match(rf"^\s*{NAME}\s*:", line):
                if current:
                    records.append(current)
                current = line.strip()
            elif current:
                current += " " + line.strip()
        if current:
            records.append(current)
        rows = len(records)
        for record in records:
            body = record.split(":", 1)[1] if ":" in record else record
            lhs = re.split(r"\s(?:<=|>=|=)\s", body, maxsplit=1)[0]
            nonzeros += len(set(re.findall(rf"\b{NAME}\b", lhs)))
    return {
        "text_rows": rows,
        "text_columns": len(bound_names),
        "text_nonzeros": nonzeros,
        "text_inventory_source": "diagnostic LP parser; CPLEX log preferred",
    }


@dataclass
class Solution:
    available: bool = False
    parse_reason: str = "solution_not_read"
    status_value: str = ""
    status_string: str = ""
    type_string: str = ""
    method_string: str = ""
    primal_feasible: str = ""
    dual_feasible: str = ""
    objective: float = math.nan
    simplex_iterations: int = -1
    values: Dict[str, float] = field(default_factory=dict)
    statuses: Dict[str, str] = field(default_factory=dict)
    reduced_costs: Dict[str, float] = field(default_factory=dict)
    quality: Dict[str, str] = field(default_factory=dict)


def parse_solution(path: Path) -> Solution:
    result = Solution()
    if not path.is_file():
        result.parse_reason = "solution_file_missing"
        return result
    try:
        root = ET.parse(path).getroot()
        header = root.find("header")
        if header is None:
            result.parse_reason = "solution_header_missing"
            return result
        result.status_value = header.get("solutionStatusValue", "")
        result.status_string = header.get("solutionStatusString", "")
        result.type_string = header.get("solutionTypeString", "")
        result.method_string = header.get("solutionMethodString", "")
        result.primal_feasible = header.get("primalFeasible", "")
        result.dual_feasible = header.get("dualFeasible", "")
        result.objective = as_float(header.get("objectiveValue"))
        try:
            result.simplex_iterations = int(header.get("simplexIterations", "-1"))
        except ValueError:
            result.simplex_iterations = -1
        quality = root.find("quality")
        if quality is not None:
            result.quality = dict(quality.attrib)
        variables = root.find("variables")
        if variables is not None:
            for variable in variables.findall("variable"):
                name = variable.get("name", "")
                if not name:
                    continue
                value = as_float(variable.get("value"))
                if finite(value):
                    result.values[name] = value
                status = variable.get("status")
                if status is not None:
                    result.statuses[name] = status
                reduced = as_float(variable.get("reducedCost"))
                if finite(reduced):
                    result.reduced_costs[name] = reduced
        result.available = True
        result.parse_reason = "parsed_CPLEX_XML_solution"
    except (ET.ParseError, OSError, UnicodeError, ValueError) as error:
        result.parse_reason = f"solution_parse_failed:{type(error).__name__}:{error}"
    return result


def parse_log(text: str) -> Dict[str, Any]:
    answer: Dict[str, Any] = {
        "log_original_rows": "",
        "log_original_columns": "",
        "log_original_nonzeros": "",
        "presolve_reduced_rows": "",
        "presolve_reduced_columns": "",
        "presolve_reduced_nonzeros": "",
        "presolve_dimensions_available": False,
        "presolve_dimensions_unavailable_reason": "no_reduced_LP_dimension_line",
        "presolve_eliminated_rows": "",
        "presolve_eliminated_columns": "",
        "log_solution_time_seconds": "",
        "log_simplex_iterations": "",
    }
    original_patterns = (
        rf"(?:Problem|LP)\s+['\"][^'\"]+['\"]\s+has\s+(\d+)\s+rows?,\s+"
        rf"(\d+)\s+columns?,\s+(?:and\s+)?(\d+)\s+nonzeros?",
    )
    for pattern in original_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            answer["log_original_rows"] = int(match.group(1))
            answer["log_original_columns"] = int(match.group(2))
            answer["log_original_nonzeros"] = int(match.group(3))
            break
    if answer["log_original_rows"] == "":
        variables = re.search(r"(?m)^Variables\s*:\s*(\d+)\b", text)
        constraints = re.search(
            r"(?ms)^Linear constraints\s*:\s*(\d+)\b.*?^\s*Nonzeros\s*:\s*(\d+)\b",
            text,
        )
        if variables and constraints:
            answer["log_original_rows"] = int(constraints.group(1))
            answer["log_original_columns"] = int(variables.group(1))
            answer["log_original_nonzeros"] = int(constraints.group(2))
    reduced = list(
        re.finditer(
            r"Reduced\s+LP\s+has\s+(\d+)\s+rows?,\s+(\d+)\s+columns?,\s+(?:and\s+)?(\d+)\s+nonzeros?",
            text,
            re.IGNORECASE,
        )
    )
    if reduced:
        match = reduced[-1]
        answer.update(
            {
                "presolve_reduced_rows": int(match.group(1)),
                "presolve_reduced_columns": int(match.group(2)),
                "presolve_reduced_nonzeros": int(match.group(3)),
                "presolve_dimensions_available": True,
                "presolve_dimensions_unavailable_reason": "",
            }
        )
    elif re.search(
        r"(?:Presolve eliminated all rows and columns|All rows and columns eliminated)",
        text,
        re.IGNORECASE,
    ):
        answer.update(
            {
                "presolve_reduced_rows": 0,
                "presolve_reduced_columns": 0,
                "presolve_reduced_nonzeros": 0,
                "presolve_dimensions_available": True,
                "presolve_dimensions_unavailable_reason": "",
            }
        )
    eliminated = list(
        re.finditer(
            r"(?:LP\s+)?Presolve eliminated\s+(\d+)\s+rows?\s+and\s+(\d+)\s+columns?",
            text,
            re.IGNORECASE,
        )
    )
    if eliminated:
        answer["presolve_eliminated_rows"] = sum(int(m.group(1)) for m in eliminated)
        answer["presolve_eliminated_columns"] = sum(int(m.group(2)) for m in eliminated)
    times = re.findall(rf"Solution time\s*=\s*({FLOAT})\s*sec", text, re.IGNORECASE)
    if times:
        answer["log_solution_time_seconds"] = as_float(times[-1])
    iterations = re.findall(r"Iterations\s*=\s*(\d+)", text, re.IGNORECASE)
    if iterations:
        answer["log_simplex_iterations"] = int(iterations[-1])
    return answer


def cplex_path(configured: str) -> Path:
    if configured:
        return Path(configured).resolve()
    env = os.environ.get("CPLEX_STUDIO_BINARIES2211", "").split(";", 1)[0].strip()
    if env:
        candidate = Path(env) / "cplex.exe"
        if candidate.is_file():
            return candidate.resolve()
    return DEFAULT_CPLEX


def cplex_quote(path: Path) -> str:
    return '"' + str(path.resolve()).replace("\\", "/") + '"'


def make_command(model: Path, solution: Path, time_limit: int) -> str:
    return "\n".join(
        [
            "set threads 1",
            f"set timelimit {time_limit}",
            "set preprocessing presolve yes",
            "set simplex display 2",
            "set simplex tolerances feasibility 1e-9",
            "set simplex tolerances optimality 1e-9",
            f"read {cplex_quote(model)}",
            "display problem stats",
            "optimize",
            "display solution objective",
            f"write {cplex_quote(solution)}",
            "quit",
            "",
        ]
    )


def run_cplex(
    executable: Path,
    command_path: Path,
    log_path: Path,
    record_path: Path,
    time_limit: int,
) -> Dict[str, Any]:
    argv = [str(executable), "-f", str(command_path.resolve())]
    record: Dict[str, Any] = {
        "diagnostic_only": True,
        "feeds_production": False,
        "start_time": now(),
        "command": argv,
        "command_line": subprocess.list2cmdline(argv),
        "command_file": rel(command_path),
        "command_file_sha256": sha256(command_path),
        "cplex_executable": str(executable),
        "time_limit_seconds": time_limit,
        "serial_threads": 1,
    }
    write_json(record_path, record)
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            argv,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=time_limit + 30,
            check=False,
        )
        timed_out = False
        launch_error = ""
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        return_code = completed.returncode
    except subprocess.TimeoutExpired as error:
        timed_out = True
        launch_error = ""
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return_code = -98
    except OSError as error:
        timed_out = False
        launch_error = f"cplex_launch_failed:{type(error).__name__}:{error}"
        stdout = ""
        stderr = launch_error
        return_code = -97
    wall = time.perf_counter() - started
    log_path.write_text(
        str(stdout) + "\n--- STDERR ---\n" + str(stderr), encoding="utf-8"
    )
    record.update(
        {
            "end_time": now(),
            "return_code": return_code,
            "runner_timeout": timed_out,
            "actual_process_wall_seconds": wall,
            "log_file": rel(log_path),
            "log_sha256": sha256(log_path),
            "blocker": "runner_emergency_timeout" if timed_out else launch_error,
        }
    )
    write_json(record_path, record)
    return record


def evaluate_expression(coefficients: Mapping[str, float], values: Mapping[str, float]) -> float:
    return sum(coefficient * values.get(name, 0.0) for name, coefficient in coefficients.items())


def variable_metrics(
    solution: Solution,
    inventory: F0Inventory,
    coefficients: Mapping[str, float],
    positive_threshold: float,
    x_small_threshold: float,
) -> Dict[str, Any]:
    expected_names = set(inventory.conn_names) | set(inventory.x_names) | set(coefficients)
    missing = sorted(expected_names - set(solution.values))
    conn_values = {name: solution.values.get(name, 0.0) for name in inventory.conn_names}
    return_values = {name: solution.values.get(name, 0.0) for name in inventory.return_names}
    positive_returns = [value for value in return_values.values() if value > positive_threshold]
    small_x_flows: List[float] = []
    for conn_name, value in conn_values.items():
        if value <= positive_threshold:
            continue
        match = CONN_RE.fullmatch(conn_name)
        if match is None:
            continue
        x_name = f"x_{match.group(1)}_{match.group(2)}_{match.group(3)}"
        if solution.values.get(x_name, 0.0) <= x_small_threshold:
            small_x_flows.append(value)
    statuses_complete = not missing and bool(solution.statuses) and not (
        set(solution.values) - set(solution.statuses)
    )
    reduced_complete = not missing and bool(solution.reduced_costs) and not (
        set(solution.values) - set(solution.reduced_costs)
    )
    reduced_values = list(solution.reduced_costs.values())
    conn_reduced = [
        solution.reduced_costs[name]
        for name in inventory.conn_names
        if name in solution.reduced_costs
    ]
    return {
        "solution_variables_reported": len(solution.values),
        "expected_diagnostic_variables": len(expected_names),
        "missing_expected_solution_variables": len(missing),
        "missing_expected_solution_variable_examples": "|".join(missing[:10]),
        "reconstructed_original_objective": evaluate_expression(coefficients, solution.values),
        "total_return_conn_flow": sum(return_values.values()),
        "total_conn_flow": sum(conn_values.values()),
        "positive_return_count": len(positive_returns),
        "positive_return_sum": sum(positive_returns),
        "positive_return_max": max(positive_returns, default=0.0),
        "positive_conn_on_x_at_or_below_small_count": len(small_x_flows),
        "positive_conn_on_x_at_or_below_small_sum": sum(small_x_flows),
        "positive_conn_on_x_at_or_below_small_max": max(small_x_flows, default=0.0),
        "positive_flow_threshold": positive_threshold,
        "x_small_threshold": x_small_threshold,
        "basis_status_available": statuses_complete,
        "basis_status_unavailable_reason": "" if statuses_complete else (
            "CPLEX_XML_solution_did_not_report_status_for_every_written_variable"
        ),
        "basis_status_counts": json.dumps(dict(sorted(Counter(solution.statuses.values()).items()))),
        "reduced_costs_available": reduced_complete,
        "reduced_costs_unavailable_reason": "" if reduced_complete else (
            "CPLEX_XML_solution_did_not_report_reducedCost_for_every_written_variable"
        ),
        "reduced_cost_count": len(reduced_values),
        "reduced_cost_min": min(reduced_values) if reduced_values else "",
        "reduced_cost_max": max(reduced_values) if reduced_values else "",
        "reduced_cost_max_abs": max((abs(value) for value in reduced_values), default=""),
        "conn_zero_reduced_cost_count": sum(abs(value) <= 1e-9 for value in conn_reduced),
        "basis_kappa_available": finite(solution.quality.get("kappa")),
        "basis_kappa": solution.quality.get("kappa", ""),
        "basis_kappa_unavailable_reason": "" if finite(solution.quality.get("kappa")) else (
            "CPLEX_XML_quality_did_not_report_kappa"
        ),
    }


def base_row(instance: str, source: Optional[Path], origin: str) -> Dict[str, Any]:
    return {
        "instance": instance,
        "diagnostic_only": True,
        "feeds_production": False,
        "source_lp": rel(source) if source else "",
        "source_discovery": origin,
        "source_lp_sha256": sha256(source) if source and source.is_file() else "",
    }


def blocker_rows(
    instance: str,
    source: Optional[Path],
    origin: str,
    blocker: str,
    dry_run: bool,
    inventory: Optional[F0Inventory] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    diagnostic: List[Dict[str, Any]] = []
    sizes: List[Dict[str, Any]] = []
    for solve_name, family, sense in SOLVES:
        row = base_row(instance, source, origin)
        row.update(
            {
                "diagnostic_kind": solve_name,
                "secondary_family": family,
                "secondary_sense": sense,
                "status": "dry_run_blocked" if dry_run else "blocked",
                "blocker": blocker,
                "f0_structural_validation": inventory.valid if inventory else False,
                "f0_validation_reason": inventory.reason if inventory else "not_evaluated",
                "basis_status_available": False,
                "basis_status_unavailable_reason": "solve_not_run:" + blocker,
                "reduced_costs_available": False,
                "reduced_costs_unavailable_reason": "solve_not_run:" + blocker,
                "basis_kappa_available": False,
                "basis_kappa_unavailable_reason": "solve_not_run:" + blocker,
            }
        )
        diagnostic.append(row)
        size = base_row(instance, source, origin)
        size.update(
            {
                "diagnostic_kind": solve_name,
                "status": row["status"],
                "blocker": blocker,
                "presolve_dimensions_available": False,
                "presolve_dimensions_unavailable_reason": "solve_not_run:" + blocker,
            }
        )
        sizes.append(size)
    return diagnostic, sizes


def prepare_instance_directories(instance: str) -> Dict[str, Path]:
    root = DIAGNOSTICS / instance
    paths = {
        "root": root,
        "models": root / "models",
        "commands": root / "commands",
        "logs": root / "logs",
        "solutions": root / "solutions",
        "records": root / "records",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def gzip_deterministic(source: Path, destination: Path) -> None:
    """Create a reproducible gzip archive (no source name and mtime zero)."""
    with source.open("rb") as input_stream, destination.open("wb") as raw_output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_output, mtime=0) as output:
            shutil.copyfileobj(input_stream, output, length=1024 * 1024)


def archive_instance_artifacts(
    instance: str,
    diagnostic_rows: List[Dict[str, Any]],
    size_rows: List[Dict[str, Any]],
    threshold: int,
) -> None:
    """Hash every preserved artifact and gzip large models/logs/solutions.

    Compression happens only after all parsing is complete.  It is confined to
    the diagnostics directory, and the manifest retains both the uncompressed
    content hash and the actual archive hash/path.  Historical .cplex commands
    intentionally retain the paths used at execution time; replay requires
    inflating any archived model first.
    """
    root = (DIAGNOSTICS / instance).resolve()
    if not root.is_dir():
        return
    entries: List[Dict[str, Any]] = []
    replacements: Dict[str, Dict[str, Any]] = {}
    created_archives: set[Path] = set()
    compress_roots = {root / "models", root / "logs", root / "solutions"}
    candidates = sorted(path for path in root.rglob("*") if path.is_file())
    for path in candidates:
        if path.resolve() in created_archives:
            continue
        if path.name == "artifact_hashes_and_compression_manifest.json":
            continue
        original_rel = rel(path)
        original_size = path.stat().st_size
        original_hash = sha256(path)
        should_compress = (
            original_size >= threshold
            and path.suffix.lower() != ".gz"
            and any(parent == path.parent or parent in path.parents for parent in compress_roots)
        )
        entry: Dict[str, Any] = {
            "logical_original_path": original_rel,
            "uncompressed_bytes": original_size,
            "uncompressed_sha256": original_hash,
            "compressed": should_compress,
        }
        if should_compress:
            archive = path.with_name(path.name + ".gz")
            # Both paths are resolved below the diagnostics root by
            # construction.  Never remove an input/export outside this tree.
            if root not in archive.resolve().parents or root not in path.resolve().parents:
                raise RuntimeError("refusing to archive a path outside diagnostics root")
            gzip_deterministic(path, archive)
            created_archives.add(archive.resolve())
            archive_rel = rel(archive)
            entry.update(
                {
                    "preserved_path": archive_rel,
                    "preserved_bytes": archive.stat().st_size,
                    "preserved_sha256": sha256(archive),
                    "compression": "gzip; deterministic mtime=0; original filename omitted",
                }
            )
            path.unlink()
            replacements[original_rel] = entry
        else:
            entry.update(
                {
                    "preserved_path": original_rel,
                    "preserved_bytes": original_size,
                    "preserved_sha256": original_hash,
                    "compression": "none",
                }
            )
        entries.append(entry)

    for row in diagnostic_rows + size_rows:
        if row.get("instance") != instance:
            continue
        for field_name in ("model_path", "log_path", "solution_path"):
            old_path = str(row.get(field_name, ""))
            if not old_path:
                continue
            entry = replacements.get(old_path)
            if entry is not None:
                row[field_name] = entry["preserved_path"]
                row[field_name + "_uncompressed_sha256"] = entry["uncompressed_sha256"]
                row[field_name + "_compressed"] = True
                row[field_name + "_sha256"] = entry["preserved_sha256"]
            else:
                preserved = next(
                    (item for item in entries if item["logical_original_path"] == old_path),
                    None,
                )
                if preserved is not None:
                    row[field_name + "_compressed"] = False
                    row[field_name + "_sha256"] = preserved["preserved_sha256"]
        # Keep the established model_sha256 column aligned with the actual
        # path named in model_path after optional compression.
        if row.get("model_path_sha256"):
            row["model_sha256"] = row["model_path_sha256"]
    write_json(
        root / "artifact_hashes_and_compression_manifest.json",
        {
            "diagnostic_only": True,
            "feeds_production": False,
            "instance": instance,
            "created_at": now(),
            "gzip_threshold_bytes": threshold,
            "replay_note": (
                "Commands are preserved exactly as executed. Inflate any .lp.gz to its "
                "logical_original_path before replaying a command whose model was archived."
            ),
            "artifacts": entries,
        },
    )


def solve_status_ok(solution: Solution, record: Mapping[str, Any]) -> Tuple[bool, str]:
    if int(record.get("return_code", -1)) != 0:
        return False, f"cplex_process_return_code:{record.get('return_code')}"
    if not solution.available:
        return False, solution.parse_reason
    if solution.status_string.strip().lower() != "optimal":
        return False, "LP_not_optimal:" + solution.status_string
    if solution.primal_feasible not in {"", "1"}:
        return False, "solution_not_primal_feasible"
    if not finite(solution.objective):
        return False, "solution_objective_unavailable"
    return True, ""


def run_instance(
    instance: str,
    source: Path,
    origin: str,
    executable: Path,
    args: argparse.Namespace,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    inventory, source_text = inspect_f0(source)
    if not source.is_file():
        return blocker_rows(instance, source, origin, "source_lp_missing", args.dry_run, inventory)
    if not inventory.valid:
        return blocker_rows(
            instance,
            source,
            origin,
            "source_rejected_as_non_F0:" + inventory.reason,
            args.dry_run,
            inventory,
        )
    paths = prepare_instance_directories(instance)
    source_copy = paths["models"] / (
        "source_F0_global_root.lp.gz" if source.suffix.lower() == ".gz"
        else "source_F0_global_root.lp"
    )
    shutil.copy2(source, source_copy)
    relaxed_path = paths["models"] / "relaxed_original_objective.lp"
    try:
        relaxed = continuous_relaxation(source_text, source)
        sense, expression, _, _ = objective_parts(relaxed)
        if sense != "min":
            raise ValueError(f"expected minimization root objective, found {sense}")
        coefficients = parse_linear_expression(expression)
        relaxed_path.write_text(relaxed, encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as error:
        return blocker_rows(
            instance,
            source,
            origin,
            f"relaxation_generation_failed:{type(error).__name__}:{error}",
            args.dry_run,
            inventory,
        )
    manifest = {
        "diagnostic_only": True,
        "feeds_production": False,
        "instance": instance,
        "created_at": now(),
        "source_lp": rel(source),
        "source_lp_sha256": sha256(source),
        "source_lp_decompressed_content_sha256": hashlib.sha256(
            source_text.encode("utf-8")
        ).hexdigest(),
        "source_copy": rel(source_copy),
        "source_copy_sha256": sha256(source_copy),
        "relaxed_model": rel(relaxed_path),
        "relaxed_model_sha256": sha256(relaxed_path),
        "relaxation_operation": "removed Generals/Binaries declarations only; retained all rows/bounds",
        "f0_validation": inventory.__dict__,
        "original_objective_expression": expression,
        "original_objective_coefficients": coefficients,
    }
    write_json(paths["root"] / "diagnostic_manifest.json", manifest)
    if args.dry_run:
        diagnostics, sizes = blocker_rows(
            instance,
            source,
            origin,
            "dry_run_no_CPLEX_invocation",
            True,
            inventory,
        )
        for row in diagnostics:
            row["status"] = "dry_run_ready"
            row["blocker"] = ""
            row["basis_status_unavailable_reason"] = "solve_not_run:dry_run"
            row["reduced_costs_unavailable_reason"] = "solve_not_run:dry_run"
            row["basis_kappa_unavailable_reason"] = "solve_not_run:dry_run"
        for row in sizes:
            row["status"] = "dry_run_ready"
            row["blocker"] = ""
            row["presolve_dimensions_unavailable_reason"] = "solve_not_run:dry_run"
        text_size = text_model_inventory(relaxed)
        for row in sizes:
            if row["diagnostic_kind"] == "root_original_objective":
                row.update(text_size)
                row["model_path"] = rel(relaxed_path)
                row["model_sha256"] = sha256(relaxed_path)
        return diagnostics, sizes

    root_solution_path = paths["solutions"] / "root_original_objective.sol"
    root_command_path = paths["commands"] / "root_original_objective.cplex"
    root_log_path = paths["logs"] / "root_original_objective.log"
    root_record_path = paths["records"] / "root_original_objective.json"
    root_command_path.write_text(
        make_command(relaxed_path, root_solution_path, args.time_limit), encoding="utf-8"
    )
    root_record = run_cplex(
        executable, root_command_path, root_log_path, root_record_path, args.time_limit
    )
    root_solution = parse_solution(root_solution_path)
    root_ok, root_blocker = solve_status_ok(root_solution, root_record)
    if not root_ok:
        diagnostics, sizes = blocker_rows(
            instance,
            source,
            origin,
            "root_LP_solve_failed:" + root_blocker,
            False,
            inventory,
        )
        root_metrics = parse_log(root_log_path.read_text(encoding="utf-8", errors="replace"))
        sizes[0].update(text_model_inventory(relaxed))
        sizes[0].update(root_metrics)
        sizes[0].update(
            {
                "model_path": rel(relaxed_path),
                "model_sha256": sha256(relaxed_path),
                "command_path": rel(root_command_path),
                "log_path": rel(root_log_path),
                "solution_path": rel(root_solution_path) if root_solution_path.exists() else "",
                "runner_wall_seconds": root_record.get("actual_process_wall_seconds", ""),
            }
        )
        return diagnostics, sizes

    root_optimum = root_solution.objective
    face_tolerance = max(
        args.face_absolute_tolerance,
        args.face_relative_tolerance * max(1.0, abs(root_optimum)),
    )
    models: Dict[str, Path] = {"root_original_objective": relaxed_path}
    for solve_name, family, sense in SOLVES[1:]:
        aggregate = inventory.return_names if family == "return" else inventory.conn_names
        model = paths["models"] / f"{solve_name}.lp"
        model.write_text(
            face_model(relaxed, aggregate, sense, root_optimum, face_tolerance),
            encoding="utf-8",
        )
        models[solve_name] = model

    solutions: Dict[str, Solution] = {"root_original_objective": root_solution}
    records: Dict[str, Dict[str, Any]] = {"root_original_objective": root_record}
    logs: Dict[str, Path] = {"root_original_objective": root_log_path}
    commands: Dict[str, Path] = {"root_original_objective": root_command_path}
    solution_paths: Dict[str, Path] = {"root_original_objective": root_solution_path}
    for solve_name, _, _ in SOLVES[1:]:
        model = models[solve_name]
        command = paths["commands"] / f"{solve_name}.cplex"
        log = paths["logs"] / f"{solve_name}.log"
        solution_path = paths["solutions"] / f"{solve_name}.sol"
        record_path = paths["records"] / f"{solve_name}.json"
        command.write_text(
            make_command(model, solution_path, args.time_limit), encoding="utf-8"
        )
        commands[solve_name] = command
        logs[solve_name] = log
        solution_paths[solve_name] = solution_path
        records[solve_name] = run_cplex(
            executable, command, log, record_path, args.time_limit
        )
        solutions[solve_name] = parse_solution(solution_path)

    metric_cache: Dict[str, Dict[str, Any]] = {}
    ok_cache: Dict[str, Tuple[bool, str]] = {}
    for solve_name, _, _ in SOLVES:
        solution = solutions[solve_name]
        ok_cache[solve_name] = solve_status_ok(solution, records[solve_name])
        if solution.available:
            metric_cache[solve_name] = variable_metrics(
                solution,
                inventory,
                coefficients,
                args.positive_threshold,
                args.x_small_threshold,
            )
            missing_count = int(
                metric_cache[solve_name].get("missing_expected_solution_variables", 0)
            )
            if ok_cache[solve_name][0] and missing_count:
                ok_cache[solve_name] = (
                    False,
                    f"incomplete_full_solution_vector:missing={missing_count}",
                )
        else:
            metric_cache[solve_name] = {}

    def aggregate_value(name: str, field_name: str) -> float:
        if not ok_cache[name][0]:
            return math.nan
        return as_float(metric_cache[name].get(field_name))

    return_min = aggregate_value("face_min_total_return_flow", "total_return_conn_flow")
    return_max = aggregate_value("face_max_total_return_flow", "total_return_conn_flow")
    flow_min = aggregate_value("face_min_total_conn_flow", "total_conn_flow")
    flow_max = aggregate_value("face_max_total_conn_flow", "total_conn_flow")
    ranges = {
        "return_flow_face_min": return_min if finite(return_min) else "",
        "return_flow_face_max": return_max if finite(return_max) else "",
        "return_flow_face_range": return_max - return_min
        if finite(return_min) and finite(return_max)
        else "",
        "total_conn_flow_face_min": flow_min if finite(flow_min) else "",
        "total_conn_flow_face_max": flow_max if finite(flow_max) else "",
        "total_conn_flow_face_range": flow_max - flow_min
        if finite(flow_min) and finite(flow_max)
        else "",
    }
    diagnostics: List[Dict[str, Any]] = []
    sizes: List[Dict[str, Any]] = []
    face_lower = root_optimum - face_tolerance
    face_upper = root_optimum + face_tolerance
    for solve_name, family, sense in SOLVES:
        solution = solutions[solve_name]
        ok, blocker = ok_cache[solve_name]
        row = base_row(instance, source, origin)
        row.update(
            {
                "diagnostic_kind": solve_name,
                "secondary_family": family,
                "secondary_sense": sense,
                "status": "completed" if ok else "failed",
                "blocker": blocker,
                "f0_structural_validation": inventory.valid,
                "f0_validation_reason": inventory.reason,
                "f0_vehicle_count": inventory.vehicles,
                "f0_station_count": inventory.stations,
                "f0_conn_column_count": len(inventory.conn_names),
                "f0_return_conn_column_count": len(inventory.return_names),
                "root_original_objective_optimum": root_optimum,
                "objective_face_tolerance": face_tolerance,
                "objective_face_lower": face_lower,
                "objective_face_upper": face_upper,
                "solver_reported_objective": solution.objective if finite(solution.objective) else "",
                "solution_status_value": solution.status_value,
                "solution_status_string": solution.status_string,
                "solution_type_string": solution.type_string,
                "solution_method_string": solution.method_string,
                "solution_primal_feasible": solution.primal_feasible,
                "solution_dual_feasible": solution.dual_feasible,
                "solution_parse_reason": solution.parse_reason,
                "simplex_iterations": solution.simplex_iterations
                if solution.simplex_iterations >= 0
                else "",
                "model_path": rel(models[solve_name]),
                "model_sha256": sha256(models[solve_name]),
                "command_path": rel(commands[solve_name]),
                "log_path": rel(logs[solve_name]),
                "solution_path": rel(solution_paths[solve_name])
                if solution_paths[solve_name].exists()
                else "",
                "cplex_return_code": records[solve_name].get("return_code", ""),
                "runner_timeout": records[solve_name].get("runner_timeout", ""),
                "runner_wall_seconds": records[solve_name].get(
                    "actual_process_wall_seconds", ""
                ),
            }
        )
        row.update(metric_cache[solve_name])
        reconstructed = as_float(row.get("reconstructed_original_objective"))
        row["objective_face_violation"] = (
            max(0.0, face_lower - reconstructed, reconstructed - face_upper)
            if finite(reconstructed)
            else ""
        )
        row.update(ranges)
        diagnostics.append(row)

        log_text = logs[solve_name].read_text(encoding="utf-8", errors="replace")
        size = base_row(instance, source, origin)
        size.update(
            {
                "diagnostic_kind": solve_name,
                "status": row["status"],
                "blocker": blocker,
                "model_path": rel(models[solve_name]),
                "model_sha256": sha256(models[solve_name]),
                "model_bytes": models[solve_name].stat().st_size,
                "simplex_iterations": row["simplex_iterations"],
                "runner_wall_seconds": row["runner_wall_seconds"],
            }
        )
        size.update(text_model_inventory(models[solve_name].read_text(encoding="utf-8")))
        size.update(parse_log(log_text))
        sizes.append(size)
    write_json(
        paths["root"] / "completed_summary.json",
        {
            "diagnostic_only": True,
            "feeds_production": False,
            "instance": instance,
            "root_original_objective_optimum": root_optimum,
            "objective_face_tolerance": face_tolerance,
            **ranges,
            "all_solves_completed": all(value[0] for value in ok_cache.values()),
            "solve_status": {
                name: {"ok": status[0], "blocker": status[1]}
                for name, status in ok_cache.items()
            },
        },
    )
    return diagnostics, sizes


DIAGNOSTIC_FIELDS = (
    "instance",
    "diagnostic_kind",
    "secondary_family",
    "secondary_sense",
    "status",
    "blocker",
    "diagnostic_only",
    "feeds_production",
    "source_lp",
    "source_discovery",
    "source_lp_sha256",
    "f0_structural_validation",
    "f0_validation_reason",
    "f0_vehicle_count",
    "f0_station_count",
    "f0_conn_column_count",
    "f0_return_conn_column_count",
    "root_original_objective_optimum",
    "objective_face_tolerance",
    "objective_face_lower",
    "objective_face_upper",
    "solver_reported_objective",
    "reconstructed_original_objective",
    "objective_face_violation",
    "return_flow_face_min",
    "return_flow_face_max",
    "return_flow_face_range",
    "total_conn_flow_face_min",
    "total_conn_flow_face_max",
    "total_conn_flow_face_range",
    "total_return_conn_flow",
    "total_conn_flow",
    "positive_return_count",
    "positive_return_sum",
    "positive_return_max",
    "positive_conn_on_x_at_or_below_small_count",
    "positive_conn_on_x_at_or_below_small_sum",
    "positive_conn_on_x_at_or_below_small_max",
    "positive_flow_threshold",
    "x_small_threshold",
    "solution_status_value",
    "solution_status_string",
    "solution_type_string",
    "solution_method_string",
    "solution_primal_feasible",
    "solution_dual_feasible",
    "solution_variables_reported",
    "expected_diagnostic_variables",
    "missing_expected_solution_variables",
    "missing_expected_solution_variable_examples",
    "simplex_iterations",
    "runner_wall_seconds",
    "basis_status_available",
    "basis_status_unavailable_reason",
    "basis_status_counts",
    "basis_kappa_available",
    "basis_kappa",
    "basis_kappa_unavailable_reason",
    "reduced_costs_available",
    "reduced_costs_unavailable_reason",
    "reduced_cost_count",
    "reduced_cost_min",
    "reduced_cost_max",
    "reduced_cost_max_abs",
    "conn_zero_reduced_cost_count",
    "model_path",
    "model_sha256",
    "model_path_compressed",
    "model_path_sha256",
    "model_path_uncompressed_sha256",
    "command_path",
    "log_path",
    "log_path_compressed",
    "log_path_sha256",
    "log_path_uncompressed_sha256",
    "solution_path",
    "solution_path_compressed",
    "solution_path_sha256",
    "solution_path_uncompressed_sha256",
    "cplex_return_code",
    "runner_timeout",
)


MODEL_FIELDS = (
    "instance",
    "diagnostic_kind",
    "status",
    "blocker",
    "diagnostic_only",
    "feeds_production",
    "source_lp",
    "source_discovery",
    "source_lp_sha256",
    "model_path",
    "model_sha256",
    "model_path_compressed",
    "model_path_sha256",
    "model_path_uncompressed_sha256",
    "model_bytes",
    "text_rows",
    "text_columns",
    "text_nonzeros",
    "text_inventory_source",
    "log_original_rows",
    "log_original_columns",
    "log_original_nonzeros",
    "presolve_reduced_rows",
    "presolve_reduced_columns",
    "presolve_reduced_nonzeros",
    "presolve_dimensions_available",
    "presolve_dimensions_unavailable_reason",
    "presolve_eliminated_rows",
    "presolve_eliminated_columns",
    "simplex_iterations",
    "log_simplex_iterations",
    "log_solution_time_seconds",
    "runner_wall_seconds",
)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lp",
        action="append",
        default=[],
        metavar="INSTANCE=PATH",
        help="repeatable explicit F0 root-LP mapping (comma-separated mappings also accepted)",
    )
    parser.add_argument(
        "--cplex",
        default="",
        help="CPLEX 22.1.1 command-line executable; installed/default path is auto-detected",
    )
    parser.add_argument(
        "--time-limit",
        type=int,
        default=300,
        help="seconds per serial LP solve (1..3600; default 300)",
    )
    parser.add_argument(
        "--face-absolute-tolerance",
        type=float,
        default=1e-9,
        help="absolute width component for the root-optimal objective face band",
    )
    parser.add_argument(
        "--face-relative-tolerance",
        type=float,
        default=1e-9,
        help="relative width component for the root-optimal objective face band",
    )
    parser.add_argument(
        "--positive-threshold",
        type=float,
        default=1e-8,
        help="flow magnitude treated as positive in diagnostics",
    )
    parser.add_argument(
        "--x-small-threshold",
        type=float,
        default=1e-8,
        help="x value at/below which positive corresponding conn flow is flagged",
    )
    parser.add_argument(
        "--max-instances",
        type=int,
        default=len(TARGET_INSTANCES),
        help="process only the first N target instances in deterministic order",
    )
    parser.add_argument(
        "--gzip-threshold-bytes",
        type=int,
        default=256 * 1024,
        help=(
            "gzip generated models/logs/solutions at or above this size after parsing "
            "(default 262144; hashes and logical paths are preserved in a manifest)"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="discover/validate/copy/relax sources and emit visible plan rows without invoking CPLEX",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if not 1 <= args.time_limit <= 3600:
        raise SystemExit("--time-limit must be between 1 and 3600 seconds")
    if not 1 <= args.max_instances <= len(TARGET_INSTANCES):
        raise SystemExit(f"--max-instances must be between 1 and {len(TARGET_INSTANCES)}")
    if args.gzip_threshold_bytes < 1:
        raise SystemExit("--gzip-threshold-bytes must be positive")
    for option in (
        "face_absolute_tolerance",
        "face_relative_tolerance",
        "positive_threshold",
        "x_small_threshold",
    ):
        value = getattr(args, option)
        if not math.isfinite(value) or value < 0:
            raise SystemExit(f"--{option.replace('_', '-')} must be finite and nonnegative")
    try:
        explicit = parse_explicit_lp(args.lp)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    selected = TARGET_INSTANCES[: args.max_instances]
    sources, origins = discover_sources(explicit)
    executable = cplex_path(args.cplex)
    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    write_json(
        DIAGNOSTICS / "run_configuration.json",
        {
            "diagnostic_only": True,
            "feeds_production": False,
            "created_at": now(),
            "dry_run": args.dry_run,
            "instances": list(selected),
            "explicit_lp_mappings": {key: rel(value) for key, value in explicit.items()},
            "discovered_lp_mappings": {key: rel(value) for key, value in sources.items()},
            "source_origins": origins,
            "cplex_executable": str(executable),
            "cplex_available": executable.is_file(),
            "time_limit_seconds_per_solve": args.time_limit,
            "serial_threads": 1,
            "face_absolute_tolerance": args.face_absolute_tolerance,
            "face_relative_tolerance": args.face_relative_tolerance,
            "positive_threshold": args.positive_threshold,
            "x_small_threshold": args.x_small_threshold,
            "gzip_threshold_bytes": args.gzip_threshold_bytes,
            "production_dependency": "none",
        },
    )
    diagnostic_rows: List[Dict[str, Any]] = []
    size_rows: List[Dict[str, Any]] = []
    for instance in selected:
        source = sources.get(instance)
        origin = origins.get(instance, "not_discovered")
        if source is None:
            diagnostics, sizes = blocker_rows(
                instance,
                None,
                origin,
                "F0_root_LP_not_discovered; supply --lp INSTANCE=PATH",
                args.dry_run,
            )
        elif not args.dry_run and source.is_file() and not executable.is_file():
            inventory, _ = inspect_f0(source)
            diagnostics, sizes = blocker_rows(
                instance,
                source,
                origin,
                "CPLEX_command_line_executable_missing:" + str(executable),
                False,
                inventory,
            )
        else:
            try:
                diagnostics, sizes = run_instance(
                    instance, source, origin, executable, args
                )
            except Exception as error:
                inventory, _ = inspect_f0(source)
                diagnostics, sizes = blocker_rows(
                    instance,
                    source,
                    origin,
                    f"diagnostic_runner_exception:{type(error).__name__}:{error}",
                    args.dry_run,
                    inventory,
                )
        diagnostic_rows.extend(diagnostics)
        size_rows.extend(sizes)
        archive_instance_artifacts(
            instance, diagnostic_rows, size_rows, args.gzip_threshold_bytes
        )
        write_csv(DEGENERACY_CSV, diagnostic_rows, DIAGNOSTIC_FIELDS)
        write_csv(MODEL_SIZE_CSV, size_rows, MODEL_FIELDS)
    failures = [
        row for row in diagnostic_rows if row.get("status") not in {"completed"}
    ]
    print(
        json.dumps(
            {
                "diagnostic_only": True,
                "dry_run": args.dry_run,
                "instances": list(selected),
                "rows": len(diagnostic_rows),
                "noncompleted_rows": len(failures),
                "flow_degeneracy_diagnostics": rel(DEGENERACY_CSV),
                "flow_model_size_and_presolve": rel(MODEL_SIZE_CSV),
                "diagnostics_directory": rel(DIAGNOSTICS),
            },
            indent=2,
        )
    )
    # Dry-run blockers are an expected planning state before the F0 exports
    # exist.  A real run is fail-closed if any requested solve is unavailable.
    return 0 if args.dry_run or not failures else 2


if __name__ == "__main__":
    sys.exit(main())
