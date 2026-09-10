#!/usr/bin/env python3
"""Audit, generate, and validate the Citi Bike 443 regional v1 data family.

This is intentionally a data-only tool.  It never launches an optimizer and it
does not modify the legacy Hybrid GA project.  The generated ExactEBRP text
files use the current Hybrid-GA-compatible parser format; route horizon T stays
in the scenario manifest because the current executable receives T by CLI.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT.parent / "Hybrid GA"
EVIDENCE = ROOT / "results" / "data_generation_citibike_round57"
DATASET = ROOT / "reference" / "citibike443-regional-v1"
CAPACITY_SOURCE = LEGACY / "testdata" / "CitiBike" / "coords" / "citibike_selected_443_capacity_list.txt"
COORD_SOURCE = LEGACY / "testdata" / "CitiBike" / "coords" / "citibike_selected_443_coords_utm18n_meters.txt"
FULL_COORD_SOURCE = LEGACY / "testdata" / "CitiBike" / "coords" / "citibike_station_coords_utm18n_meters.txt"
FULL_INFO_SOURCE = LEGACY / "testdata" / "CitiBike" / "coords" / "citibike_station_basic_info_with_capacity.csv"

FAMILY = "citibike443-regional-v1"
GENERATOR_VERSION = "citibike443-regional-v1.0.0"
SOURCE_SCHEMA = "citibike443-source-audit-v1"
DATASET_SCHEMA = "citibike443-regional-dataset-v1"
V_SET = (8, 12, 20, 30, 50)
GEOGRAPHIC_REGIMES = ("compact", "regional")
REPLICATES = (1, 2)
INVENTORY_REGIMES = ("shortage", "balanced", "surplus")
T_SET = (1800, 3600, 10800, 18000)
Q_SET = (20, 30)
M_BY_V = {
    8: (1, 2),
    12: (1, 2),
    20: (2, 3),
    30: (3, 5),
    50: (4, 7),
}
PARSER_SPEED_METERS_PER_SECOND = 1.5
PICKUP_SECONDS = 60.0
DROP_SECONDS = 60.0
LAMBDA = 0.15
COORD_DECIMALS = 3
WEIGHT_DECIMALS = 6
MIN_RATIO_DECIMALS = 4

NEW_PATH_PREFIXES = (
    "reference/citibike443-regional-v1/",
    "results/data_generation_citibike_round57/",
    "scripts/generate_citibike443_regional_v1.py",
    "scripts/round57_parser_probe.cpp",
)


@dataclass(frozen=True)
class SourceStation:
    source_row_index: int
    legacy_internal_index: int
    capacity: int
    x: float
    y: float
    companion_full_row_index: int
    companion_capacity: int | None
    companion_match_status: str
    station_id: str
    name: str
    latitude: float
    longitude: float


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def write_csv(path: Path, rows: Sequence[dict[str, Any]], fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fieldnames), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_text(command: Sequence[str], cwd: Path = ROOT, check: bool = True) -> str:
    completed = subprocess.run(
        list(command), cwd=cwd, check=check, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    return completed.stdout.strip()


def git_text(repo: Path, *args: str) -> str:
    return run_text(["git", "-C", str(repo), *args], cwd=ROOT)


def version_line(command: Sequence[str]) -> str:
    try:
        return run_text(command).splitlines()[0]
    except (OSError, subprocess.CalledProcessError, IndexError):
        return "unavailable"


def stable_seed(material: str) -> int:
    return 1 + int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:8], "big") % 2_147_483_646


def hash_unit(material: str) -> float:
    value = int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:8], "big")
    return value / float((1 << 64) - 1)


def hash_order(indices: Iterable[int], material: str) -> list[int]:
    return sorted(indices, key=lambda idx: (hashlib.sha256(f"{material}|{idx}".encode()).digest(), idx))


def encoding_and_newlines(data: bytes) -> dict[str, Any]:
    bom = data.startswith(b"\xef\xbb\xbf")
    if all(byte < 128 for byte in data):
        encoding = "ASCII (UTF-8-compatible; no BOM)"
    else:
        data.decode("utf-8-sig")
        encoding = "UTF-8 with BOM" if bom else "UTF-8 without BOM"
    crlf = data.count(b"\r\n")
    bare_lf = data.count(b"\n") - crlf
    bare_cr = data.count(b"\r") - crlf
    convention = "none" if crlf == bare_lf == bare_cr == 0 else (
        "LF" if bare_lf and not crlf and not bare_cr else
        "CRLF" if crlf and not bare_lf and not bare_cr else
        "CR" if bare_cr and not crlf and not bare_lf else "mixed")
    return {
        "encoding": encoding,
        "utf8_bom": bom,
        "newline_convention": convention,
        "crlf_count": crlf,
        "lf_count": bare_lf,
        "cr_count": bare_cr,
        "final_newline": data.endswith((b"\n", b"\r")),
    }


def parse_literal_file(path: Path) -> Any:
    return ast.literal_eval(path.read_text(encoding="utf-8-sig"))


def load_source_stations() -> tuple[list[SourceStation], dict[str, Any]]:
    if not CAPACITY_SOURCE.is_file() or not COORD_SOURCE.is_file():
        raise FileNotFoundError("The two authoritative Citi Bike 443 source files are required")
    capacities_raw = parse_literal_file(CAPACITY_SOURCE)
    coords_raw = parse_literal_file(COORD_SOURCE)
    if not isinstance(capacities_raw, list) or not isinstance(coords_raw, list):
        raise ValueError("Authoritative sources must parse as list literals")
    capacities = [int(value) for value in capacities_raw]
    coords = [(float(pair[0]), float(pair[1])) for pair in coords_raw]
    if len(capacities) != 443 or len(coords) != 443:
        raise ValueError(f"Expected 443 capacity/coordinate rows, got {len(capacities)}/{len(coords)}")
    if any(not math.isfinite(x) or not math.isfinite(y) for x, y in coords):
        raise ValueError("Nonfinite authoritative coordinate")

    full_coords = [(round(float(x), 3), round(float(y), 3)) for x, y in parse_literal_file(FULL_COORD_SOURCE)]
    with FULL_INFO_SOURCE.open(newline="", encoding="utf-8-sig") as stream:
        full_info = list(csv.DictReader(stream))
    if len(full_coords) != len(full_info):
        raise ValueError("Full coordinate list and full station-info CSV are not row-aligned")
    coordinate_to_full_rows: dict[tuple[float, float], list[int]] = defaultdict(list)
    for idx, pair in enumerate(full_coords):
        coordinate_to_full_rows[pair].append(idx)

    stations: list[SourceStation] = []
    mapping_issues: list[dict[str, Any]] = []
    for source_idx, (capacity, (x, y)) in enumerate(zip(capacities, coords)):
        key = (round(x, 3), round(y, 3))
        candidates = coordinate_to_full_rows.get(key, [])
        matching = [idx for idx in candidates if int(full_info[idx]["capacity"]) == capacity]
        if len(matching) == 1:
            chosen = matching[0]
            companion_match_status = "exact_coordinate_and_capacity"
        elif len(candidates) == 1:
            chosen = candidates[0]
            companion_match_status = "exact_coordinate_capacity_snapshot_differs"
        else:
            chosen = -1
            companion_match_status = "no_unique_companion_coordinate_match"
        if companion_match_status != "exact_coordinate_and_capacity":
            mapping_issues.append({
                "source_station_row_index": source_idx,
                "coordinate": key,
                "capacity": capacity,
                "coordinate_match_count": len(candidates),
                "capacity_coordinate_match_count": len(matching),
                "issue": companion_match_status,
                "companion_capacity": int(full_info[chosen]["capacity"]) if chosen >= 0 else None,
            })
        if chosen < 0:
            info = {"station_id": "", "name": "", "lat": "nan", "lon": "nan"}
        else:
            info = full_info[chosen]
        stations.append(SourceStation(
            source_row_index=source_idx,
            legacy_internal_index=source_idx + 1,
            capacity=capacity,
            x=round(x, COORD_DECIMALS),
            y=round(y, COORD_DECIMALS),
            companion_full_row_index=chosen,
            companion_capacity=int(info["capacity"]) if chosen >= 0 else None,
            companion_match_status=companion_match_status,
            station_id=info["station_id"],
            name=info["name"],
            latitude=float(info["lat"]),
            longitude=float(info["lon"]),
        ))
    meta = {
        "capacity_count": len(capacities),
        "coordinate_count": len(coords),
        "companion_full_coordinate_count": len(full_coords),
        "companion_station_info_count": len(full_info),
        "mapping_issue_count": len(mapping_issues),
        "mapping_issues": mapping_issues,
        "exact_coordinate_and_capacity_match_count": sum(
            station.companion_match_status == "exact_coordinate_and_capacity" for station in stations),
        "exact_coordinate_only_match_count": sum(
            station.companion_match_status == "exact_coordinate_capacity_snapshot_differs" for station in stations),
        "unmatched_companion_coordinate_count": sum(
            station.companion_match_status == "no_unique_companion_coordinate_match" for station in stations),
        "all_capacity_coordinate_pairs_match_companion": not mapping_issues,
    }
    return stations, meta


def git_status_entries(repo: Path) -> list[dict[str, str]]:
    raw = subprocess.check_output(
        ["git", "-C", str(repo), "status", "--porcelain=v1", "-z", "--untracked-files=all"])
    parts = raw.decode("utf-8", errors="surrogateescape").split("\0")
    entries: list[dict[str, str]] = []
    index = 0
    while index < len(parts):
        item = parts[index]
        index += 1
        if not item:
            continue
        status = item[:2]
        path = item[3:]
        if status[0] in "RC" and index < len(parts):
            old_path = parts[index]
            index += 1
            path = f"{old_path} -> {path}"
        entries.append({"status": status, "path": path.replace("\\", "/")})
    return entries


def filtered_start_status(entries: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    return [entry for entry in entries if not any(entry["path"].startswith(prefix) for prefix in NEW_PATH_PREFIXES)]


def status_summary(entries: Sequence[dict[str, str]]) -> dict[str, Any]:
    tracked = [entry for entry in entries if entry["status"] != "??"]
    untracked = [entry for entry in entries if entry["status"] == "??"]
    grouped: Counter[str] = Counter()
    for entry in untracked:
        parts = entry["path"].split("/")
        key = "/".join(parts[:2]) if parts and parts[0] in {"results", "reference", "build", "tmp"} else parts[0]
        grouped[key] += 1
    material = "\n".join(f"{e['status']} {e['path']}" for e in sorted(entries, key=lambda row: (row["path"], row["status"])))
    return {
        "entry_count": len(entries),
        "tracked_entry_count": len(tracked),
        "untracked_file_entry_count": len(untracked),
        "status_fingerprint_sha256": sha256_bytes(material.encode("utf-8", errors="surrogateescape")),
        "tracked_entries": tracked,
        "untracked_groups": [{"path_group": key, "file_count": grouped[key]} for key in sorted(grouped)],
    }


def tree_snapshot(
        path: Path, complete_hashes: bool = True,
        exclude_relative_prefixes: Sequence[str] = ()) -> dict[str, Any]:
    files = sorted(
        (item for item in path.rglob("*") if item.is_file() and not any(
            item.relative_to(path).as_posix().startswith(prefix) for prefix in exclude_relative_prefixes)),
        key=lambda item: item.relative_to(path).as_posix())
    rows: list[dict[str, Any]] = []
    total = 0
    tree = hashlib.sha256()
    for item in files:
        rel = item.relative_to(path).as_posix()
        size = item.stat().st_size
        digest = sha256_file(item)
        total += size
        tree.update(rel.encode("utf-8"))
        tree.update(b"\0")
        tree.update(str(size).encode("ascii"))
        tree.update(b"\0")
        tree.update(digest.encode("ascii"))
        tree.update(b"\n")
        rows.append({"relative_path": rel, "bytes": size, "sha256": digest})
    representatives: list[dict[str, Any]] = []
    if rows:
        positions = sorted({0, len(rows) // 4, len(rows) // 2, (3 * len(rows)) // 4, len(rows) - 1})
        representatives = [rows[pos] for pos in positions]
    return {
        "path": str(path.resolve()),
        "file_count": len(files),
        "total_bytes": total,
        "complete_content_tree_sha256": tree.hexdigest(),
        "representative_files": representatives,
        "complete_hash_inventory": rows if complete_hashes else None,
    }


def historical_roots() -> list[tuple[str, Path, str, str, str]]:
    return [
        ("legacy_hybrid_ga_testdata", LEGACY / "testdata", "historical_mixed", "mixed_real_derived_and_synthetic", "not_superseded"),
        ("exactebrp_generated", ROOT / "reference" / "generated", "historical_reference", "synthetic", "not_superseded"),
        ("exactebrp_round56", ROOT / "reference" / "round56_paper_candidate", "historical_paper_candidate", "controlled_synthetic", "not_superseded"),
        ("exactebrp_all_pre_round57_reference", ROOT / "reference", "historical_reference_collection", "mixed", "not_superseded"),
        ("exactebrp_testdata", ROOT / "testdata", "historical_testdata", "synthetic_or_example", "not_superseded"),
    ]


def create_start_audit() -> dict[str, Any]:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    exact_entries = filtered_start_status(git_status_entries(ROOT))
    legacy_entries = git_status_entries(LEGACY)
    tracked_hashes: list[dict[str, Any]] = []
    for entry in exact_entries:
        if entry["status"] != "??" and " -> " not in entry["path"]:
            path = ROOT / entry["path"]
            tracked_hashes.append({
                **entry,
                "bytes": path.stat().st_size if path.is_file() else None,
                "sha256": sha256_file(path) if path.is_file() else None,
            })
    legacy_tracked_hashes: list[dict[str, Any]] = []
    for entry in legacy_entries:
        if entry["status"] != "??" and " -> " not in entry["path"]:
            path = LEGACY / entry["path"]
            legacy_tracked_hashes.append({
                **entry,
                "bytes": path.stat().st_size if path.is_file() else None,
                "sha256": sha256_file(path) if path.is_file() else None,
            })

    audit = {
        "schema": "citibike-data-round-repository-start-audit-v1",
        "exactebrp": {
            "absolute_path": str(ROOT.resolve()),
            "branch": git_text(ROOT, "branch", "--show-current"),
            "head": git_text(ROOT, "rev-parse", "HEAD"),
            "tree": git_text(ROOT, "show", "-s", "--format=%T", "HEAD"),
            "status": status_summary(exact_entries),
            "preexisting_tracked_modifications": tracked_hashes,
        },
        "legacy_hybrid_ga": {
            "absolute_path": str(LEGACY.resolve()),
            "read_only_contract": True,
            "is_git_repository": (LEGACY / ".git").exists(),
            "branch": git_text(LEGACY, "branch", "--show-current"),
            "head": git_text(LEGACY, "rev-parse", "HEAD"),
            "tree": git_text(LEGACY, "show", "-s", "--format=%T", "HEAD"),
            "status": status_summary(legacy_entries),
            "preexisting_tracked_modifications": legacy_tracked_hashes,
        },
        "environment": {
            "platform": platform.platform(),
            "python_used": sys.version.replace("\n", " "),
            "python_executable": str(Path(sys.executable).resolve()),
            "gxx": version_line(["D:/msys64/ucrt64/bin/g++.exe", "--version"]),
            "cmake": version_line(["D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe", "--version"]),
        },
        "guardrails": {
            "optimizer_execution_permitted": False,
            "legacy_project_mutation_permitted": False,
            "algorithm_source_mutation_permitted": False,
            "commit_push_or_pr_permitted": False,
        },
    }
    write_json(EVIDENCE / "repository_start_audit.json", audit)

    baseline_path = EVIDENCE / "historical_preservation_baseline.json"
    if not baseline_path.exists():
        snapshots = []
        for family, path, status, derivation, superseded in historical_roots():
            # The all-reference snapshot excludes the new family by construction at start.
            snapshot = tree_snapshot(path, complete_hashes=family != "legacy_hybrid_ga_testdata")
            snapshot.update({
                "family_name": family,
                "status": status,
                "derivation": derivation,
                "superseded": superseded,
                "used_in_historical_experiments": family != "exactebrp_testdata",
            })
            snapshots.append(snapshot)
        write_json(baseline_path, {
            "schema": "citibike-data-round-preservation-baseline-v1",
            "exactebrp_start_head": audit["exactebrp"]["head"],
            "exactebrp_filtered_status_fingerprint_sha256": audit["exactebrp"]["status"]["status_fingerprint_sha256"],
            "legacy_start_head": audit["legacy_hybrid_ga"]["head"],
            "legacy_status_fingerprint_sha256": audit["legacy_hybrid_ga"]["status"]["status_fingerprint_sha256"],
            "families": snapshots,
        })
    return audit


def source_file_record(path: Path, parsed_count: int, header_presence: str, index_convention: str) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "absolute_path": str(path.resolve()),
        "relative_path_within_legacy_project": path.resolve().relative_to(LEGACY.resolve()).as_posix(),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
        **encoding_and_newlines(data),
        "parsed_row_count": parsed_count,
        "header_presence": header_presence,
        "index_convention": index_convention,
    }


def audit_sources(stations: Sequence[SourceStation], mapping_meta: dict[str, Any]) -> dict[str, Any]:
    capacities = [station.capacity for station in stations]
    coords = [(station.x, station.y) for station in stations]
    cap_counts = Counter(capacities)
    coord_counts = Counter(coords)
    cap_file = source_file_record(
        CAPACITY_SOURCE, len(capacities), "no header; one Python-style list literal",
        "row position is canonical zero-based source_station_row_index; legacy loader maps row i to one-based internal index i+1")
    coord_file = source_file_record(
        COORD_SOURCE, len(coords), "no data header; '[' and ']' wrapper lines only",
        "row position is canonical zero-based source_station_row_index; legacy loader maps row i to one-based internal index i+1")
    cap_file.update({
        "empty_row_count": 0,
        "malformed_value_count": 0,
        "duplicate_value_occurrences": sum(count - 1 for count in cap_counts.values()),
        "duplicate_values_are_expected": True,
        "nonfinite_value_count": 0,
        "minimum": min(capacities),
        "maximum": max(capacities),
        "mean": statistics.fmean(capacities),
        "median": statistics.median(capacities),
        "frequency_distribution": {str(key): cap_counts[key] for key in sorted(cap_counts)},
        "invalid_or_suspicious_capacities": [
            {"source_station_row_index": station.source_row_index, "capacity": station.capacity, "issue": "zero_capacity_excluded_from_generated_service_station_pool"}
            for station in stations if station.capacity <= 0
        ],
    })
    xs = [x for x, _ in coords]
    ys = [y for _, y in coords]
    coord_file.update({
        "empty_or_malformed_data_row_count": 0,
        "syntactic_wrapper_line_count": 2,
        "duplicate_coordinate_count": sum(count - 1 for count in coord_counts.values()),
        "duplicate_coordinates": [
            {"x": pair[0], "y": pair[1], "count": count}
            for pair, count in sorted(coord_counts.items()) if count > 1
        ],
        "nonfinite_value_count": 0,
        "coordinate_dimension": 2,
        "coordinate_minimum": {"x": min(xs), "y": min(ys)},
        "coordinate_maximum": {"x": max(xs), "y": max(ys)},
        "geographic_bounding_box_utm18n_meters": {
            "min_easting": min(xs), "max_easting": max(xs),
            "min_northing": min(ys), "max_northing": max(ys),
            "width_meters": max(xs) - min(xs), "height_meters": max(ys) - min(ys),
        },
        "coordinate_system_evidence": [
            "The authoritative filename explicitly labels UTM 18N meters.",
            "Easting/northing magnitudes are consistent with New York City in UTM zone 18N.",
            "442 of 443 selected coordinates map exactly to the older local full-station coordinate list; 438 also match its capacity snapshot.",
        ],
        "consistent_with_utm18n_meters": True,
    })
    alignment_status = "established_line_by_line_from_legacy_loader"
    audit = {
        "schema": SOURCE_SCHEMA,
        "classification": "citibike443_source_valid_with_documented_issues" if any(cap <= 0 for cap in capacities) else "citibike443_source_valid",
        "authoritative_role": "primary trusted real-world station universe",
        "capacity_source": cap_file,
        "coordinate_source": coord_file,
        "alignment": {
            "status": alignment_status,
            "capacity_and_coordinate_parsed_row_counts_equal": len(capacities) == len(coords),
            "legacy_code_basis": "CitiBikeSubsetGenerator.h:143-149 stores both parsed row i values at internal index i+1",
            "independent_companion_mapping": mapping_meta,
            "source_files_contain_station_ids_or_names": False,
            "station_ids_and_names_available_via_local_companion_mapping": mapping_meta["unmatched_companion_coordinate_count"] == 0,
            "station_id_name_annotation_coverage": 443 - mapping_meta["unmatched_companion_coordinate_count"],
            "canonical_source_station_row_index": "zero-based",
            "legacy_internal_index": "one-based; source row i becomes internal index i+1",
        },
        "documented_issues": [
            "One authoritative row has capacity zero. It remains in provenance but is deterministically ineligible as a generated service station.",
            "The older companion station-info snapshot has four capacity differences at exact coordinate matches and lacks one authoritative coordinate; this limits annotations but does not affect authoritative capacity/coordinate row alignment.",
        ],
    }
    write_json(EVIDENCE / "source_file_audit.json", audit)

    station_rows = [{
        "source_station_row_index": station.source_row_index,
        "legacy_internal_index": station.legacy_internal_index,
        "capacity": station.capacity,
        "utm18n_easting_m": f"{station.x:.3f}",
        "utm18n_northing_m": f"{station.y:.3f}",
        "companion_full_row_index": station.companion_full_row_index,
        "companion_capacity": "" if station.companion_capacity is None else station.companion_capacity,
        "companion_match_status": station.companion_match_status,
        "station_id": station.station_id,
        "station_name": station.name,
        "latitude": f"{station.latitude:.12g}",
        "longitude": f"{station.longitude:.12g}",
        "eligible_for_generation": station.capacity > 0,
    } for station in stations]
    write_csv(EVIDENCE / "source_station_table.csv", station_rows)
    alignment_rows = [{
        "source_station_row_index": station.source_row_index,
        "capacity_source_position": station.source_row_index,
        "coordinate_source_position": station.source_row_index,
        "legacy_internal_index": station.legacy_internal_index,
        "capacity": station.capacity,
        "utm18n_easting_m": f"{station.x:.3f}",
        "utm18n_northing_m": f"{station.y:.3f}",
        "companion_full_row_index": station.companion_full_row_index,
        "companion_capacity": "" if station.companion_capacity is None else station.companion_capacity,
        "companion_match_status": station.companion_match_status,
        "station_id": station.station_id,
        "station_name": station.name,
        "capacity_matches_companion": station.companion_match_status == "exact_coordinate_and_capacity",
        "authoritative_capacity_coordinate_alignment_status": "established_by_same_source_row_and_legacy_loader",
        "companion_annotation_status": station.companion_match_status,
    } for station in stations]
    write_csv(EVIDENCE / "capacity_coordinate_alignment.csv", alignment_rows)
    write_text(EVIDENCE / "source_data_summary.md", f"""
# Citi Bike 443 authoritative source summary

The authoritative station universe is the row-aligned pair
`{CAPACITY_SOURCE.resolve()}` and `{COORD_SOURCE.resolve()}`.  Each file parses
to 443 records.  The capacity file SHA-256 is `{cap_file['sha256']}`; the
coordinate file SHA-256 is `{coord_file['sha256']}`.

The source files contain no station identifiers.  Canonical provenance therefore
uses a zero-based `source_station_row_index`.  The legacy loader reads the two
lists in parallel and stores source row *i* at internal index *i+1*.  The same
443 row pairs are paired by the legacy loader.  As an independent annotation
check, {mapping_meta['exact_coordinate_and_capacity_match_count']} pairs map by
exact three-decimal coordinate and capacity to the older local companion table,
{mapping_meta['exact_coordinate_only_match_count']} map by coordinate with a
different companion capacity snapshot, and
{mapping_meta['unmatched_companion_coordinate_count']} has no coordinate match.
The companion mapping supplies {443 - mapping_meta['unmatched_companion_coordinate_count']}
station IDs/names without changing the authority or alignment of the two
requested files.

Capacities range from {min(capacities)} to {max(capacities)}, with mean
{statistics.fmean(capacities):.3f} and median {statistics.median(capacities):.3f}.
One row has capacity zero.  It is preserved in the source table and excluded
from generated service-station subsets.  The UTM bounding box is
[{min(xs):.3f}, {max(xs):.3f}] x [{min(ys):.3f}, {max(ys):.3f}] meters.  There
are {sum(count - 1 for count in coord_counts.values())} duplicate coordinate
occurrences and no nonfinite coordinate values.
""")
    return audit


def legacy_status_by_path() -> dict[str, str]:
    return {entry["path"]: entry["status"] for entry in git_status_entries(LEGACY)}


def relevant_legacy_files() -> list[Path]:
    named = [
        "CitiBikeSubsetGenerator.h", "Instance_Generator.cpp", "InstanceData.h",
        "ModelTuner.h", "Compare_Models.cpp", "RunCplexBatch.h",
        "testdata/CitiBike/coords/citibike_selected_414_capacity_list.txt",
        "testdata/CitiBike/coords/citibike_selected_414_coords_utm18n_meters.txt",
        "testdata/CitiBike/coords/citibike_selected_414_metadata.csv",
        "testdata/CitiBike/coords/citibike_selected_443_capacity_list.txt",
        "testdata/CitiBike/coords/citibike_selected_443_coords_utm18n_meters.txt",
        "testdata/CitiBike/coords/citibike_station_coords_utm18n_meters.txt",
        "testdata/CitiBike/coords/citibike_station_basic_info_with_capacity.csv",
    ]
    return [LEGACY / name for name in named if (LEGACY / name).is_file()]


HEADER_RE = re.compile(r"^\s*(\d+)\s+(\d+)\s+\[([^\]]*)\]")


def named_numbers(text: str, name: str) -> list[float]:
    match = re.search(rf"{re.escape(name)}\s*=\s*\[([^\]]*)\]", text, re.DOTALL)
    if not match:
        return []
    return [float(value) for value in re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", match.group(1))]


def parse_points_from_text(text: str) -> list[tuple[float, float]]:
    match = re.search(r"points\s*=\s*\[([^\]]*)\]", text, re.DOTALL)
    if not match:
        return []
    nums = [float(value) for value in re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", match.group(1))]
    return list(zip(nums[::2], nums[1::2]))


def inventory_historical_instances(stations: Sequence[SourceStation]) -> list[dict[str, Any]]:
    coords443 = {(station.x, station.y) for station in stations}
    coords414 = {(round(float(x), 3), round(float(y), 3)) for x, y in parse_literal_file(
        LEGACY / "testdata" / "CitiBike" / "coords" / "citibike_selected_414_coords_utm18n_meters.txt")}
    rows: list[dict[str, Any]] = []
    for path in sorted((LEGACY / "testdata").rglob("*.txt")):
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        first = text.splitlines()[0] if text.splitlines() else ""
        match = HEADER_RE.match(first)
        if not match:
            continue
        v, m = int(match.group(1)), int(match.group(2))
        q = [int(float(value)) for value in re.findall(r"[-+]?\d+(?:\.\d+)?", match.group(3))]
        capacities = [int(round(value)) for value in named_numbers(text, "capacities")]
        initial = [int(round(value)) for value in named_numbers(text, "initial")]
        target = [int(round(value)) for value in named_numbers(text, "target")]
        points = parse_points_from_text(text)
        service_points = {(round(x, 3), round(y, 3)) for x, y in points[1:]}
        if service_points and service_points.issubset(coords443):
            geographic_origin = "citibike443_coordinate_match"
        elif service_points and service_points.issubset(coords414):
            geographic_origin = "citibike414_coordinate_match"
        else:
            geographic_origin = "synthetic_or_unknown"
        lower_name = path.name.lower()
        scenario = "low" if "low" in lower_name else "high" if "high" in lower_name else "average" if "average" in lower_name else "unlabeled"
        rows.append({
            "relative_path": path.relative_to(LEGACY).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "V": v,
            "M": m,
            "Q_vector": canonical_json(q),
            "scenario_label_from_filename": scenario,
            "capacity_length": len(capacities),
            "initial_length": len(initial),
            "target_length": len(target),
            "points_length": len(points),
            "has_weights": bool(named_numbers(text, "weights")),
            "has_min_ratio": bool(named_numbers(text, "min_ratio")),
            "has_serialized_distances": "distances" in text,
            "geographic_origin": geographic_origin,
            "format_shape_valid": len(capacities) == len(initial) == len(target) == v + 1 and len(q) == m,
        })
    write_csv(EVIDENCE / "historical_instance_inventory.csv", rows)
    return rows


def audit_legacy_project(stations: Sequence[SourceStation]) -> dict[str, Any]:
    status = legacy_status_by_path()
    inventory_rows = []
    for path in relevant_legacy_files():
        rel = path.relative_to(LEGACY).as_posix()
        inventory_rows.append({
            "relative_path": rel,
            "absolute_path": str(path.resolve()),
            "role": (
                "authoritative_source" if "selected_443" in rel else
                "legacy_source_data_or_mapping" if rel.startswith("testdata/") else
                "generation_or_loading_code"),
            "git_status_at_audit": status.get(rel, "tracked_unchanged"),
            "bytes": path.stat().st_size,
            "line_count": len(path.read_text(encoding="utf-8-sig", errors="replace").splitlines()),
            "sha256": sha256_file(path),
        })
    write_csv(EVIDENCE / "legacy_project_file_inventory.csv", inventory_rows)
    historical = inventory_historical_instances(stations)
    v_counts = Counter(int(row["V"]) for row in historical)
    origin_counts = Counter(str(row["geographic_origin"]) for row in historical)

    decisions = [
        ("parallel source-row loading", "CitiBikeSubsetGenerator.h", "117-150", "Coordinates and capacities are parsed independently and row i is placed at internal index i+1.", "retained", "This establishes the authoritative row alignment and stable source index."),
        ("positive-capacity eligibility", "CitiBikeSubsetGenerator.h", "153-159 (working tree)", "Only source capacities greater than zero and below 100 are eligible.", "retained", "The single zero-capacity row remains in provenance but cannot be a service station."),
        ("dense anchor-nearest subset", "CitiBikeSubsetGenerator.h", "169-184", "Choose an unseeded random center and the V nearest eligible stations.", "adapted", "Keep spatial coherence; replace random_device with hash-derived anchors, explicit tie-breaking, and compact/regional regimes."),
        ("sorted source indices", "CitiBikeSubsetGenerator.h", "186-187", "Selected indices are sorted before writing.", "adapted", "Local station order preserves deterministic selection order; source rows remain explicit in mappings."),
        ("centroid artificial depot", "CitiBikeSubsetGenerator.h", "202-210", "Depot is the arithmetic centroid of selected service-station coordinates.", "retained", "It is neutral, deterministic, and clearly distinguishable from a real station."),
        ("real station capacities and coordinates", "CitiBikeSubsetGenerator.h", "213-216", "Selected source capacity and UTM coordinate are copied to the instance.", "retained", "These are the two authoritative real-derived fields."),
        ("uniform random initial inventory", "CitiBikeSubsetGenerator.h", "211-218", "Each initial inventory is independently uniform from zero to capacity.", "rejected", "It confounds V with uncontrolled total balance and local imbalance."),
        ("average/low/high random target bands", "CitiBikeSubsetGenerator.h", "219-230", "Targets are independently random in full, low, or high capacity bands.", "rejected", "The new family uses a common target per station selection and explicit total-balance regimes."),
        ("target-squared normalized weights", "CitiBikeSubsetGenerator.h", "232-244", "Weights are target squared and normalized by the maximum; older committed code used scale 10.", "adapted", "Retain the transparent target emphasis, normalize to [0.1,1], and document it as synthetic."),
        ("uniform random minimum ratio", "CitiBikeSubsetGenerator.h", "234-235", "min_ratio is independently uniform in [0.01,0.5].", "rejected", "Use a bounded deterministic function of target fill ratio."),
        ("Euclidean UTM travel seconds", "CitiBikeSubsetGenerator.h", "248-263", "Euclidean coordinate distance is divided by 1.5.", "retained", "It matches the current parser's fixed reconstruction and is unit-consistent as 1.5 m/s travel time."),
        ("three-decimal points plus four-decimal matrix", "CitiBikeSubsetGenerator.h", "307-325", "Points and a derived matrix are serialized at different precision.", "adapted", "Serialize authoritative three-decimal points only; current Parser.cpp rebuilds the effective matrix from exactly those points."),
        ("random_device/mt19937 generation", "CitiBikeSubsetGenerator.h", "211-212,347-349", "Separate unrecorded random_device seeds choose stations and synthetic fields.", "rejected", "All choices use recorded SHA-256-derived seeds and hash ordering."),
        ("homogeneous Q vector", "CitiBikeSubsetGenerator.h", "193-195,273-278", "Each file stores M identical Q entries.", "retained", "The new family provides Q=20 and Q=30 for every fleet density."),
        ("T supplied outside file", "Instance_Generator.cpp", "403-418,533-546", "The loader receives Time as an argument rather than parsing it from text.", "retained", "The current ExactEBRP CLI supplies T; scenario rows bind T to an immutable input hash."),
    ]
    write_csv(EVIDENCE / "legacy_rule_decision_table.csv", [{
        "rule": rule, "source_file": source, "line_range_or_section": lines,
        "recovered_behavior": behavior, "decision": decision, "reason": reason,
    } for rule, source, lines, behavior, decision, reason in decisions])

    classification = "multiple_legacy_generator_versions_found"
    write_text(EVIDENCE / "legacy_generation_pipeline.md", f"""
# Legacy Hybrid GA generation-pipeline audit

Classification: **{classification}**.

The legacy project at `{LEGACY.resolve()}` contains more than one generator.
`Instance_Generator.cpp:36-294` and `716-820` generate fully synthetic
capacities, inventory, targets, coordinates and distances using unrecorded
`random_device` state.  `CitiBikeSubsetGenerator.h:117-365` instead loads paired
Citi Bike capacity/coordinate lists, chooses either an arbitrary shuffled subset
or an anchor-nearest dense subset, places an artificial centroid depot, then
generates inventory, targets, weights and minimum ratios synthetically.  Active
call sites are split between the older 414-station sources and the requested
443-station sources (`ModelTuner.h:258-311`).

The working tree also contains uncommitted generator changes: zero/very-large
capacity filtering, wider low/high target bands, and weight normalization from
[0,10] to [0,1].  Those changes are preserved read-only and recorded in the
file/status inventory.  The old writer emits `V M [Q...]`, depot-inclusive
capacity/initial/target/weight/min-ratio arrays, points, and a distance matrix.
The paired reader ignores the serialized matrix when points are present and
recomputes Euclidean distance divided by 1.5.  T is supplied to the loader.

The historical inventory contains {len(historical)} parse-shaped `.txt` files.
Observed V frequencies are `{canonical_json(dict(sorted(v_counts.items())))}`;
coordinate-origin counts are `{canonical_json(dict(sorted(origin_counts.items())))}`.
These files remain historical evidence; they are not copied or overwritten.

The new design therefore retains source-row alignment, positive-capacity
eligibility, spatially local selection, an artificial centroid depot, real
capacities/coordinates, homogeneous Q vectors, and the 1.5 m/s parser convention.
It replaces every unrecorded random choice and every uncontrolled inventory rule.
The complete retain/adapt/reject ledger is in `legacy_rule_decision_table.csv`.
""")
    return {
        "classification": classification,
        "relevant_file_count": len(inventory_rows),
        "historical_instance_count": len(historical),
        "historical_V_distribution": dict(sorted(v_counts.items())),
        "historical_origin_distribution": dict(sorted(origin_counts.items())),
    }


def audit_exactebrp_requirements() -> dict[str, Any]:
    parser_path = ROOT / "src" / "Parser.cpp"
    instance_path = ROOT / "include" / "Instance.hpp"
    main_path = ROOT / "src" / "main.cpp"
    decision = {
        "schema": "citibike443-parser-format-decision-v1",
        "parser_source": {"path": repo_path(parser_path), "sha256": sha256_file(parser_path)},
        "instance_contract_source": {"path": repo_path(instance_path), "sha256": sha256_file(instance_path)},
        "cli_source": {"path": repo_path(main_path), "sha256": sha256_file(main_path)},
        "chosen_format": "current ExactEBRP Hybrid-GA-compatible text input",
        "first_line": "V M [Q_1, ..., Q_M]",
        "arrays": ["capacities", "initial", "target", "weights", "min_ratio"],
        "array_length": "V+1 including depot at index 0",
        "coordinates": "points list with V+1 (x,y) pairs; depot first",
        "serialized_distance_matrix": False,
        "effective_distance_rule": "Parser.cpp rebuilds Euclidean(points_i,points_j)/1.5 whenever V+1 points are present",
        "T_representation": "scenario manifest and --T CLI argument; not embedded in input text",
        "pickup_drop_representation": "fixed current SolveOptions defaults of 60 seconds pickup and 60 seconds drop; no current CLI override",
        "depot_placeholders": {"capacity": 100000, "initial": 50000, "target": 0, "weight": 0.0, "min_ratio": 0.0},
        "parser_change_required": False,
        "reason": "The existing parser accepts all required fields and derives the authoritative travel-time matrix from serialized points.",
    }
    write_json(EVIDENCE / "parser_format_decision.json", decision)
    write_text(EVIDENCE / "exactebrp_data_requirement_audit.md", f"""
# Current ExactEBRP data-requirement audit

The frozen parser is `{repo_path(parser_path)}` (SHA-256
`{decision['parser_source']['sha256']}`).  `Parser.cpp:126-199` accepts the
Hybrid-GA-compatible text format.  The first line must contain integer `V`,
integer `M`, and a bracketed vehicle-capacity vector of exactly M values.
Named arrays `capacities`, `initial`, and `target` must each have V+1 values.
`weights` and `min_ratio` also resolve to V+1 values; absent values receive
legacy defaults, but this family writes them explicitly.  Service-station
targets must be positive and weights finite/nonnegative.

Index zero is the depot.  This family uses the repository's established
placeholders `capacity=100000`, `initial=50000`, `target=0`, `weight=0`, and
`min_ratio=0`.  Service stations occupy indices 1..V.

When exactly V+1 points are present, `Parser.cpp:91-103,177-180` ignores any
serialized matrix and rebuilds the effective symmetric matrix as Euclidean UTM
distance divided by 1.5.  The new files therefore serialize only points, at
three decimals, and make those values authoritative.  This avoids two
competing matrices and the Round 56 pre-freeze rounding defect.

Operational horizon T is not an input-file field.  `main.cpp:631-635` receives
it through `--T`, then `main.cpp:19085-19092` passes it to the parser.  Pickup
and drop service times are current `SolveOptions` defaults of 60 seconds each
(`Instance.hpp:23-25,40-43`); no current CLI override exists.  Scenario rows
therefore bind an input-file hash to T, pickup/drop defaults, and lambda.

No parser or algorithm modification is needed.  Parser compatibility is
verified with a standalone probe compiled only from the current `Parser.cpp`;
the ExactEBRP optimizer executable is never launched.
""")

    mappings = [
        ("legacy V", "first-line integer V", "first-line integer V", "retained"),
        ("legacy M", "first-line integer M", "first-line integer M", "retained"),
        ("legacy Q", "bracketed vector, usually homogeneous", "complete homogeneous vector [Q]*M", "retained; Q=20 and Q=30 variants"),
        ("station capacity", "depot-inclusive capacities", "authoritative source capacity at indices 1..V", "retained real-derived field"),
        ("initial inventory", "uniform independent random integer", "controlled shortage/balanced/surplus integer inventory", "redesigned synthetic field"),
        ("target inventory", "uniform target band by average/low/high label", "shared deterministic target profile per geographic selection", "redesigned synthetic field"),
        ("weights", "target squared normalized, historical scales 10 or 1", "max(0.1,(target/max_target)^2), normalized max 1", "adapted synthetic field"),
        ("min_ratio", "uniform random [0.01,0.5]", "0.10+0.40*(target/capacity), bounded [0.1,0.5]", "redesigned synthetic field"),
        ("points", "depot centroid plus selected UTM coordinates", "rounded centroid plus exact three-decimal authoritative UTM coordinates", "retained with explicit precision contract"),
        ("distances", "serialized, but legacy/current readers recompute from points", "not serialized; parser recomputes Euclidean/1.5", "adapted to one authority"),
        ("T", "loader argument", "scenario-manifest field and --T", "retained external representation"),
        ("pickup/drop", "code constants", "current 60/60-second parser arguments", "retained current default"),
        ("dataset identity", "path/filename only", "canonical family, IDs, source hashes, file hashes, scenario identities", "new provenance layer"),
    ]
    write_csv(EVIDENCE / "legacy_to_current_field_mapping.csv", [{
        "field": field, "legacy_representation": legacy, "current_representation": current, "decision": mapping,
    } for field, legacy, current, mapping in mappings])
    return decision


def euclidean(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def pairwise_stats(points: Sequence[tuple[float, float]], depot: tuple[float, float]) -> dict[str, Any]:
    station_distances = [euclidean(points[i], points[j]) for i in range(len(points)) for j in range(i + 1, len(points))]
    depot_distances = [euclidean(depot, point) for point in points]
    return {
        "geographic_diameter_m": max(station_distances) if station_distances else 0.0,
        "mean_pairwise_station_distance_m": statistics.fmean(station_distances) if station_distances else 0.0,
        "maximum_pairwise_station_distance_m": max(station_distances) if station_distances else 0.0,
        "mean_depot_distance_m": statistics.fmean(depot_distances) if depot_distances else 0.0,
        "maximum_depot_distance_m": max(depot_distances) if depot_distances else 0.0,
        "bounding_box_width_m": max(x for x, _ in points) - min(x for x, _ in points),
        "bounding_box_height_m": max(y for _, y in points) - min(y for _, y in points),
    }


def farthest_anchor_indices(eligible: Sequence[SourceStation], v: int) -> list[int]:
    material = f"{FAMILY}|geographic-anchor-set|V={v}"
    first = hash_order((station.source_row_index for station in eligible), material)[0]
    by_index = {station.source_row_index: station for station in eligible}
    anchors = [first]
    while len(anchors) < len(GEOGRAPHIC_REGIMES) * len(REPLICATES):
        best = max(
            (station.source_row_index for station in eligible if station.source_row_index not in anchors),
            key=lambda idx: (
                min(euclidean((by_index[idx].x, by_index[idx].y), (by_index[a].x, by_index[a].y)) for a in anchors),
                -idx,
            ))
        anchors.append(best)
    return anchors


def build_selection(stations: Sequence[SourceStation], v: int, geographic_regime: str, replicate: int) -> dict[str, Any]:
    eligible = [station for station in stations if 0 < station.capacity < 100]
    by_index = {station.source_row_index: station for station in stations}
    anchor_slot = GEOGRAPHIC_REGIMES.index(geographic_regime) * len(REPLICATES) + REPLICATES.index(replicate)
    anchor_idx = farthest_anchor_indices(eligible, v)[anchor_slot]
    anchor = by_index[anchor_idx]
    distance_order = sorted(
        eligible,
        key=lambda station: (euclidean((station.x, station.y), (anchor.x, anchor.y)), station.source_row_index))
    if geographic_regime == "compact":
        selected = distance_order[:v]
        candidate_pool_size = v
        selection_mechanism = "anchor plus V nearest eligible stations"
    elif geographic_regime == "regional":
        pool = distance_order[: min(len(distance_order), 2 * v)]
        chosen = [anchor]
        chosen_ids = {anchor.source_row_index}
        while len(chosen) < v:
            candidate = max(
                (station for station in pool if station.source_row_index not in chosen_ids),
                key=lambda station: (
                    min(euclidean((station.x, station.y), (other.x, other.y)) for other in chosen),
                    -euclidean((station.x, station.y), (anchor.x, anchor.y)),
                    -station.source_row_index,
                ))
            chosen.append(candidate)
            chosen_ids.add(candidate.source_row_index)
        selected = chosen
        candidate_pool_size = len(pool)
        selection_mechanism = "farthest-first coverage inside the 2V nearest eligible stations around the anchor"
    else:
        raise ValueError(f"Unknown geographic regime {geographic_regime}")
    points = [(station.x, station.y) for station in selected]
    depot = (
        round(statistics.fmean(x for x, _ in points), COORD_DECIMALS),
        round(statistics.fmean(y for _, y in points), COORD_DECIMALS),
    )
    selection_id = f"cb443_V{v:02d}_{geographic_regime}_r{replicate}"
    seed_material = f"{FAMILY}|selection|V={v}|geography={geographic_regime}|replicate={replicate}"
    return {
        "schema": "citibike443-geographic-selection-v1",
        "dataset_family": FAMILY,
        "generator_version": GENERATOR_VERSION,
        "selection_id": selection_id,
        "V": v,
        "geographic_regime": geographic_regime,
        "replicate": replicate,
        "seed": stable_seed(seed_material),
        "seed_derivation_material": seed_material,
        "anchor_source_station_row_index": anchor_idx,
        "anchor_coordinate_utm18n_meters": [anchor.x, anchor.y],
        "selection_mechanism": selection_mechanism,
        "tie_breaking": "ascending zero-based source_station_row_index",
        "eligible_station_rule": "0 < source capacity < 100",
        "eligible_station_count": len(eligible),
        "candidate_pool_size": candidate_pool_size,
        "selected_source_station_row_indices": [station.source_row_index for station in selected],
        "selection_order_is_local_station_order": True,
        "depot_rule": "artificial arithmetic centroid of serialized service-station coordinates, rounded to three decimals",
        "depot_coordinate_utm18n_meters": [depot[0], depot[1]],
        "source_capacity_summary": {
            "minimum": min(station.capacity for station in selected),
            "maximum": max(station.capacity for station in selected),
            "mean": statistics.fmean(station.capacity for station in selected),
            "median": statistics.median(station.capacity for station in selected),
        },
        "geographic_statistics": pairwise_stats(points, depot),
    }


def target_profile(selection: dict[str, Any], stations: Sequence[SourceStation]) -> list[int]:
    by_index = {station.source_row_index: station for station in stations}
    material = f"{FAMILY}|target-profile|{selection['selection_id']}"
    targets: list[int] = []
    for source_idx in selection["selected_source_station_row_indices"]:
        capacity = by_index[source_idx].capacity
        fraction = 0.44 + 0.12 * hash_unit(f"{material}|row={source_idx}")
        targets.append(max(1, min(capacity, int(math.floor(capacity * fraction + 0.5)))))
    return targets


def adjust_total(values: list[int], desired_total: int, lower: Sequence[int], upper: Sequence[int], order: Sequence[int]) -> None:
    difference = desired_total - sum(values)
    while difference != 0:
        progressed = False
        if difference > 0:
            for idx in order:
                if values[idx] < upper[idx]:
                    values[idx] += 1
                    difference -= 1
                    progressed = True
                    if difference == 0:
                        break
        else:
            for idx in order:
                if values[idx] > lower[idx]:
                    values[idx] -= 1
                    difference += 1
                    progressed = True
                    if difference == 0:
                        break
        if not progressed:
            raise ValueError("Unable to adjust inventory to desired total within bounds")


def ensure_both_local_signs(initial: list[int], target: Sequence[int], capacity: Sequence[int], material: str) -> None:
    if any(a > b for a, b in zip(initial, target)) and any(a < b for a, b in zip(initial, target)):
        return
    order = hash_order(range(len(initial)), f"{material}|sign-repair")
    receiver = next((idx for idx in order if initial[idx] < capacity[idx]), None)
    donor = next((idx for idx in reversed(order) if initial[idx] > 0 and idx != receiver), None)
    if receiver is None or donor is None:
        raise ValueError("Cannot create both surplus and deficit stations")
    max_move = min(capacity[receiver] - initial[receiver], initial[donor])
    needed_up = max(1, target[receiver] + 1 - initial[receiver])
    needed_down = max(1, initial[donor] - target[donor] + 1)
    move = min(max_move, max(needed_up, needed_down))
    if move <= 0:
        raise ValueError("No valid zero-sum local-imbalance repair")
    initial[receiver] += move
    initial[donor] -= move
    if not (any(a > b for a, b in zip(initial, target)) and any(a < b for a, b in zip(initial, target))):
        # A deterministic exhaustive pair search handles rare extreme profiles.
        for recv in order:
            for give in reversed(order):
                if recv == give:
                    continue
                need = max(1, target[recv] + 1 - initial[recv], initial[give] - target[give] + 1)
                if initial[recv] + need <= capacity[recv] and initial[give] - need >= 0:
                    initial[recv] += need
                    initial[give] -= need
                    return
        raise ValueError("Failed to establish both local signs")


def build_landscape(selection: dict[str, Any], inventory_regime: str, stations: Sequence[SourceStation]) -> dict[str, Any]:
    by_index = {station.source_row_index: station for station in stations}
    selected = [by_index[idx] for idx in selection["selected_source_station_row_indices"]]
    capacities = [station.capacity for station in selected]
    target = target_profile(selection, stations)
    target_total = sum(target)
    total_capacity = sum(capacities)
    delta_amount = max(selection["V"], int(math.floor(0.12 * target_total + 0.5)))
    if inventory_regime == "shortage":
        desired_total = max(0, target_total - delta_amount)
        local_scale = 0.30
    elif inventory_regime == "balanced":
        desired_total = target_total
        local_scale = 0.18
    elif inventory_regime == "surplus":
        desired_total = min(total_capacity, target_total + delta_amount)
        local_scale = 0.30
    else:
        raise ValueError(f"Unknown inventory regime {inventory_regime}")

    material = f"{FAMILY}|inventory|{selection['selection_id']}|{inventory_regime}"
    order = hash_order(range(selection["V"]), material)
    initial = target.copy()
    signs = {idx: (1 if rank % 2 == 0 else -1) for rank, idx in enumerate(order)}
    for idx in order:
        magnitude = max(1, int(math.floor(local_scale * capacities[idx] + 0.5)))
        initial[idx] = max(0, min(capacities[idx], target[idx] + signs[idx] * magnitude))
    adjust_total(initial, desired_total, [0] * len(initial), capacities, order)
    ensure_both_local_signs(initial, target, capacities, material)
    if sum(initial) != desired_total:
        raise AssertionError("Sign repair changed inventory total")

    max_target = max(target)
    weights = [round(max(0.1, (value / max_target) ** 2), WEIGHT_DECIMALS) for value in target]
    max_weight = max(weights)
    weights = [round(value / max_weight, WEIGHT_DECIMALS) for value in weights]
    min_ratios = [round(0.10 + 0.40 * (goal / capacity), MIN_RATIO_DECIMALS) for goal, capacity in zip(target, capacities)]
    deltas = [a - b for a, b in zip(initial, target)]
    landscape_id = f"{selection['selection_id']}_{inventory_regime}"
    source_hashes = {
        "capacity_sha256": sha256_file(CAPACITY_SOURCE),
        "coordinate_sha256": sha256_file(COORD_SOURCE),
    }
    return {
        "schema": "citibike443-station-landscape-v1",
        "dataset_family": FAMILY,
        "classification": "generated_untested_paper_candidate",
        "generator_version": GENERATOR_VERSION,
        "landscape_id": landscape_id,
        "selection_id": selection["selection_id"],
        "V": selection["V"],
        "geographic_regime": selection["geographic_regime"],
        "replicate": selection["replicate"],
        "inventory_regime": inventory_regime,
        "local_imbalance_level": "moderate" if inventory_regime == "balanced" else "high",
        "seed": stable_seed(material),
        "seed_derivation_material": material,
        "source_station_row_indices": selection["selected_source_station_row_indices"],
        "source_hashes": source_hashes,
        "depot": {
            "artificial": True,
            "coordinate_utm18n_meters": selection["depot_coordinate_utm18n_meters"],
            "capacity_placeholder": 100000,
            "initial_placeholder": 50000,
            "target_placeholder": 0,
        },
        "capacities": capacities,
        "initial": initial,
        "target": target,
        "weights": weights,
        "min_ratio": min_ratios,
        "points_utm18n_meters": [[station.x, station.y] for station in selected],
        "statistics": {
            **selection["geographic_statistics"],
            "capacity_minimum": min(capacities),
            "capacity_maximum": max(capacities),
            "capacity_mean": statistics.fmean(capacities),
            "capacity_median": statistics.median(capacities),
            "total_capacity": total_capacity,
            "total_initial_inventory": sum(initial),
            "total_target_inventory": target_total,
            "station_inventory_minus_target": sum(initial) - target_total,
            "absolute_total_shortage_or_surplus": abs(sum(initial) - target_total),
            "local_l1_imbalance": sum(abs(delta) for delta in deltas),
            "maximum_local_absolute_imbalance": max(abs(delta) for delta in deltas),
            "surplus_station_count": sum(delta > 0 for delta in deltas),
            "deficit_station_count": sum(delta < 0 for delta in deltas),
            "balanced_station_count": sum(delta == 0 for delta in deltas),
            "weight_minimum": min(weights),
            "weight_maximum": max(weights),
            "weight_mean": statistics.fmean(weights),
            "min_ratio_minimum": min(min_ratios),
            "min_ratio_maximum": max(min_ratios),
        },
    }


def with_depot(values: Sequence[Any], depot_value: Any) -> list[Any]:
    return [depot_value, *values]


def format_int_vector(name: str, values: Sequence[int]) -> str:
    return f"{name} = [" + ", ".join(str(value) for value in values) + "]"


def format_float_vector(name: str, values: Sequence[float], decimals: int) -> str:
    return f"{name} = [" + ", ".join(f"{value:.{decimals}f}" for value in values) + "]"


def instance_text(landscape: dict[str, Any], m: int, q: int) -> str:
    points = [landscape["depot"]["coordinate_utm18n_meters"], *landscape["points_utm18n_meters"]]
    point_text = ", ".join(f"({float(x):.{COORD_DECIMALS}f}, {float(y):.{COORD_DECIMALS}f})" for x, y in points)
    lines = [
        f"{landscape['V']} {m} [" + ", ".join([str(q)] * m) + "]",
        format_int_vector("capacities", with_depot(landscape["capacities"], landscape["depot"]["capacity_placeholder"])),
        format_int_vector("initial    ", with_depot(landscape["initial"], landscape["depot"]["initial_placeholder"])),
        format_int_vector("target     ", with_depot(landscape["target"], landscape["depot"]["target_placeholder"])),
        format_float_vector("weights    ", with_depot(landscape["weights"], 0.0), WEIGHT_DECIMALS),
        format_float_vector("min_ratio  ", with_depot(landscape["min_ratio"], 0.0), MIN_RATIO_DECIMALS),
        f"points = [{point_text}]",
    ]
    return "\n".join(lines) + "\n"


def parse_instance_mirror(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines:
        raise ValueError("empty instance")
    header = HEADER_RE.match(lines[0])
    if not header:
        raise ValueError("invalid first line")
    v, m = int(header.group(1)), int(header.group(2))
    q = [int(float(value)) for value in re.findall(r"[-+]?\d+(?:\.\d+)?", header.group(3))]
    capacities = [int(round(value)) for value in named_numbers(text, "capacities")]
    initial = [int(round(value)) for value in named_numbers(text, "initial")]
    target = [int(round(value)) for value in named_numbers(text, "target")]
    weights = named_numbers(text, "weights")
    min_ratio = named_numbers(text, "min_ratio")
    points = parse_points_from_text(text)
    expected = v + 1
    for label, vector in (
        ("Q", q), ("capacities", capacities), ("initial", initial), ("target", target),
        ("weights", weights), ("min_ratio", min_ratio), ("points", points)):
        required = m if label == "Q" else expected
        if len(vector) != required:
            raise ValueError(f"{label} length {len(vector)} != {required}")
    matrix = [[euclidean(points[i], points[j]) / PARSER_SPEED_METERS_PER_SECOND for j in range(expected)] for i in range(expected)]
    return {
        "V": v, "M": m, "Q": q, "capacities": capacities, "initial": initial,
        "target": target, "weights": weights, "min_ratio": min_ratio,
        "points": points, "distances": matrix,
    }


def design_proposal_text() -> str:
    return f"""
# Dataset-design proposal: {FAMILY}

Status before full generation: proposed and structurally piloted; no optimizer
evidence is used.  The family will initially be classified
`generated_untested_paper_candidate`.

## Sources and fields

The only authoritative real-world fields are station capacity and UTM 18N
coordinate from `{CAPACITY_SOURCE.resolve()}` and `{COORD_SOURCE.resolve()}`.
Their SHA-256 values are recorded in `source_file_audit.json`.  Station ID,
name, latitude and longitude are provenance annotations recovered by exact
coordinate/capacity matching to the local companion station table; they do not
replace the two authoritative files.  Inventory, target, weight, minimum ratio,
depot, M, Q and T are synthetic design fields.

## Geographic selections and depot

For every V in {list(V_SET)}, the generator derives four widely separated
anchors by deterministic farthest-first selection, beginning with a SHA-256
ranked eligible source row.  Capacity-zero rows are never eligible.  Two
replicates use the V nearest stations to their anchors (`compact`).  Two use
farthest-first coverage inside the 2V nearest stations (`regional`).  Distance
ties use ascending zero-based source row index.  This gives four independent
real-station selections per V and preserves exact three-decimal source
coordinates.  The artificial depot is the three-decimal arithmetic centroid of
the selected serialized coordinates; it is never represented as a Citi Bike
station.

## Controlled synthetic profiles

Each geographic selection has one shared deterministic target profile, with a
fill fraction in [0.44,0.56] derived from SHA-256 values.  Three initial-inventory
profiles then impose station-total shortage, exact balance, and station-total
surplus.  Shortage/surplus magnitudes are 12% of total target inventory (at
least V units); local transfers ensure at least one surplus and one deficit
station.  Balanced cases use exact total equality with moderate local
imbalance.  All values are integer and remain within station capacity.

Weights adapt the legacy target-squared rule as
`max(0.1,(target/max_target)^2)`, renormalized to maximum 1.  Minimum ratio is
`0.10 + 0.40*(target/capacity)`, rounded to four decimals.  Both are explicitly
synthetic and are not claimed as observed demand.

## Format, distance, fleet, and horizons

Inputs use the current ExactEBRP text parser with depot-inclusive arrays.
Points are authoritative at three decimals.  No redundant distance matrix is
serialized; the current parser reconstructs symmetric travel seconds as
Euclidean UTM meters / {PARSER_SPEED_METERS_PER_SECOND}.  T is external and is
bound to each immutable input hash in the scenario manifest.  Pickup/drop
service times are the current fixed defaults {PICKUP_SECONDS:.0f}/{DROP_SECONDS:.0f}
seconds.

For each of 60 station landscapes (5 V x 4 geographic selections x 3 inventory
regimes), two M values are provided according to `{canonical_json(M_BY_V)}` and
both Q=20 and Q=30 are written.  This yields 240 complete parser inputs and a
fully factorial 960-row T scenario manifest for T={list(T_SET)}.  Per V this is
4 independent selections, 12 landscapes, 48 inputs, and 192 scenarios.

## Reproducibility and organization

All seeds are the first 64 bits of SHA-256 derivation material reduced to a
positive 31-bit integer.  Actual ordering and scalar draws are SHA-256 based,
so results do not depend on a language PRNG implementation.  LF newlines and
fixed numeric precision are mandatory.  The dataset root is
`{DATASET.resolve()}` with separate `selections`, `landscapes`, `mappings`,
`instances`, and `manifests` directories.  Audit and validation evidence stays
under `{EVIDENCE.resolve()}`.

Known limitations are: no observed trip/demand history, an artificial centroid
depot, Euclidean rather than road-network travel, a fixed 1.5 m/s convention,
homogeneous vehicle capacities, and no performance qualification in this round.
"""


def pilot_cases() -> list[tuple[int, str, int, str, int, int]]:
    return [
        (8, "compact", 1, "shortage", 1, 20),
        (8, "regional", 2, "surplus", 2, 30),
        (20, "compact", 2, "balanced", 2, 20),
        (20, "regional", 1, "shortage", 3, 30),
        (50, "compact", 1, "balanced", 4, 20),
        (50, "regional", 2, "surplus", 7, 30),
    ]


def run_structural_pilot(stations: Sequence[SourceStation]) -> list[dict[str, Any]]:
    write_text(EVIDENCE / "dataset_design_proposal.md", design_proposal_text())
    temp = EVIDENCE / "_structural_pilot_temp"
    if temp.exists():
        resolved = temp.resolve()
        if resolved.parent != EVIDENCE.resolve() or not resolved.name.startswith("_structural_pilot_temp"):
            raise RuntimeError("Refusing to remove unexpected pilot temporary directory")
        shutil.rmtree(resolved)
    temp.mkdir(parents=True)
    rows: list[dict[str, Any]] = []
    for v, geography, replicate, inventory_regime, m, q in pilot_cases():
        selection = build_selection(stations, v, geography, replicate)
        landscape = build_landscape(selection, inventory_regime, stations)
        path = temp / f"{landscape['landscape_id']}_M{m:02d}_Q{q:02d}.txt"
        write_text(path, instance_text(landscape, m, q))
        parsed = parse_instance_mirror(path)
        stats = landscape["statistics"]
        rows.append({
            "pilot_id": path.stem,
            "V": v,
            "geographic_regime": geography,
            "replicate": replicate,
            "inventory_regime": inventory_regime,
            "M": m,
            "Q": q,
            "selection_seed": selection["seed"],
            "inventory_seed": landscape["seed"],
            "source_station_row_indices": ";".join(map(str, landscape["source_station_row_indices"])),
            "geographic_diameter_m": f"{stats['geographic_diameter_m']:.6f}",
            "mean_pairwise_station_distance_m": f"{stats['mean_pairwise_station_distance_m']:.6f}",
            "maximum_depot_distance_m": f"{stats['maximum_depot_distance_m']:.6f}",
            "capacity_minimum": stats["capacity_minimum"],
            "capacity_maximum": stats["capacity_maximum"],
            "capacity_mean": f"{stats['capacity_mean']:.6f}",
            "total_initial_inventory": stats["total_initial_inventory"],
            "total_target_inventory": stats["total_target_inventory"],
            "station_inventory_minus_target": stats["station_inventory_minus_target"],
            "local_l1_imbalance": stats["local_l1_imbalance"],
            "surplus_station_count": stats["surplus_station_count"],
            "deficit_station_count": stats["deficit_station_count"],
            "weight_minimum": f"{stats['weight_minimum']:.6f}",
            "weight_maximum": f"{stats['weight_maximum']:.6f}",
            "parser_mirror_accepted": parsed["V"] == v and parsed["M"] == m,
            "pilot_file_sha256": sha256_file(path),
            "pilot_file_retained": False,
        })
    write_csv(EVIDENCE / "structural_pilot_manifest.csv", rows)

    compact = [float(row["geographic_diameter_m"]) for row in rows if row["geographic_regime"] == "compact"]
    regional = [float(row["geographic_diameter_m"]) for row in rows if row["geographic_regime"] == "regional"]
    failures = []
    for row in rows:
        expected_sign = -1 if row["inventory_regime"] == "shortage" else 1 if row["inventory_regime"] == "surplus" else 0
        actual = int(row["station_inventory_minus_target"])
        if (actual > 0) - (actual < 0) != expected_sign:
            failures.append(f"{row['pilot_id']}: inventory total class mismatch")
        if int(row["surplus_station_count"]) < 1 or int(row["deficit_station_count"]) < 1:
            failures.append(f"{row['pilot_id']}: missing a local surplus or deficit station")
        if not row["parser_mirror_accepted"]:
            failures.append(f"{row['pilot_id']}: parser mirror rejected")
    if len({row["source_station_row_indices"] for row in rows}) != len(rows):
        failures.append("pilot geographic selections are not distinct")
    write_text(EVIDENCE / "structural_pilot_analysis.md", f"""
# Structural pilot analysis

The six-case pilot covers V=8, 20 and 50; both compact and regional geography;
all shortage, balanced and surplus total-inventory regimes; both Q values; and
both fleet-density levels.  It used no optimizer and retained no temporary
instance files after recording their hashes.

Compact pilot diameters span {min(compact):.3f} to {max(compact):.3f} meters;
regional pilot diameters span {min(regional):.3f} to {max(regional):.3f} meters.
All six source-row sets are distinct.  Every inventory profile has at least one
surplus and one deficit station, all shortage/balance/surplus total signs match
their labels, and every pilot file passes the Python mirror of current parser
shape and distance semantics.

Structural defect count: {len(failures)}.  Defects: {canonical_json(failures)}.
No performance measurements, objectives, gaps, certificates, or runtimes were
used.  The design is {'not frozen because structural defects remain' if failures else 'structurally satisfactory and eligible to freeze'}.
""")
    write_text(EVIDENCE / "generator_revision_history.md", f"""
# Generator revision history

## Pre-pilot candidate ({GENERATOR_VERSION})

The initial current-project design used four farthest-separated anchors per V,
compact nearest-V and regional coverage-within-nearest-2V selections, a rounded
centroid depot, one shared target profile per selection, and three explicitly
controlled inventory totals.

## Pilot finding

The pilot found {len(failures)} structural defects.  {'No rule revision was needed.' if not failures else 'Generation was stopped pending rule revision.'}
All inspected differences were descriptive and structural; no optimizer was
run and no generated case was accepted or rejected by performance.

## Frozen effect

{'The pre-pilot rules were frozen unchanged.  Pilot files were temporary and no mathematical instance was replaced.' if not failures else 'No full family was frozen.'}
""")
    shutil.rmtree(temp)
    if failures:
        raise RuntimeError("Structural pilot failed: " + "; ".join(failures))
    return rows


def generator_contract() -> dict[str, Any]:
    return {
        "schema": "citibike443-frozen-generator-contract-v1",
        "dataset_family": FAMILY,
        "dataset_classification": "generated_untested_paper_candidate",
        "generator_version": GENERATOR_VERSION,
        "generator_source": repo_path(Path(__file__)),
        "generator_source_sha256": sha256_file(Path(__file__)),
        "source_files": {
            "capacity": {"path": str(CAPACITY_SOURCE.resolve()), "sha256": sha256_file(CAPACITY_SOURCE)},
            "coordinates": {"path": str(COORD_SOURCE.resolve()), "sha256": sha256_file(COORD_SOURCE)},
        },
        "canonical_source_index": "zero-based source_station_row_index",
        "eligible_station_rule": "0 < capacity < 100",
        "station_selection": {
            "anchor_set": "SHA-256-ranked initial anchor followed by deterministic farthest-first anchors",
            "compact": "V nearest eligible stations to anchor",
            "regional": "farthest-first V-station coverage within the 2V nearest eligible stations",
            "tie_breaking": "ascending source_station_row_index",
            "V": list(V_SET),
            "replicates_per_geographic_regime": len(REPLICATES),
        },
        "depot": "artificial centroid of serialized source coordinates rounded to three decimals",
        "target_rule": "per-station fill fraction 0.44+0.12*hash_unit, rounded half-up and bounded [1,capacity]",
        "inventory_regimes": {
            "shortage": "target total minus max(V, round(0.12*target total)); high local imbalance",
            "balanced": "target total exactly; moderate local imbalance",
            "surplus": "target total plus max(V, round(0.12*target total)), capped by total capacity; high local imbalance",
        },
        "weight_rule": "max(0.1,(target/max_target)^2), then normalized to maximum 1",
        "minimum_ratio_rule": "0.10+0.40*(target/capacity), rounded to four decimals",
        "distance_rule": "current parser rebuilds Euclidean serialized UTM coordinate distance / 1.5 m/s",
        "coordinate_decimals": COORD_DECIMALS,
        "distance_matrix_serialized": False,
        "M_BY_V": {str(key): list(value) for key, value in M_BY_V.items()},
        "Q": list(Q_SET),
        "T_seconds": list(T_SET),
        "pickup_seconds": PICKUP_SECONDS,
        "drop_seconds": DROP_SECONDS,
        "lambda": LAMBDA,
        "seed_policy": "positive 31-bit display seeds and all ordering/scalars derived from SHA-256 material",
        "newline": "LF",
        "expected_counts": {
            "independent_geographic_selections": 20,
            "station_landscapes": 60,
            "complete_parser_inputs_or_fleet_variants": 240,
            "future_T_scenarios": 960,
        },
        "optimizer_results_used": False,
        "frozen_after_structural_pilot": True,
    }


def mapping_rows(selection: dict[str, Any], stations: Sequence[SourceStation]) -> list[dict[str, Any]]:
    by_index = {station.source_row_index: station for station in stations}
    anchor = int(selection["anchor_source_station_row_index"])
    anchor_station = by_index[anchor]
    depot_x, depot_y = selection["depot_coordinate_utm18n_meters"]
    rows: list[dict[str, Any]] = [{
        "selection_id": selection["selection_id"],
        "generated_local_station_index": 0,
        "source_station_row_index": "",
        "legacy_internal_index": "",
        "station_id": "",
        "station_name": "ARTIFICIAL_CENTROID_DEPOT",
        "original_capacity": "",
        "original_utm_easting_m": "",
        "original_utm_northing_m": "",
        "selected_utm_easting_m": f"{depot_x:.3f}",
        "selected_utm_northing_m": f"{depot_y:.3f}",
        "is_depot": True,
        "geographic_selection_seed": selection["seed"],
        "geographic_regime": selection["geographic_regime"],
        "replicate": selection["replicate"],
        "anchor_source_station_row_index": anchor,
        "distance_from_anchor_m": "",
        "selection_order": 0,
    }]
    for local, source_idx in enumerate(selection["selected_source_station_row_indices"], start=1):
        station = by_index[int(source_idx)]
        rows.append({
            "selection_id": selection["selection_id"],
            "generated_local_station_index": local,
            "source_station_row_index": station.source_row_index,
            "legacy_internal_index": station.legacy_internal_index,
            "station_id": station.station_id,
            "station_name": station.name,
            "original_capacity": station.capacity,
            "original_utm_easting_m": f"{station.x:.3f}",
            "original_utm_northing_m": f"{station.y:.3f}",
            "selected_utm_easting_m": f"{station.x:.3f}",
            "selected_utm_northing_m": f"{station.y:.3f}",
            "is_depot": False,
            "geographic_selection_seed": selection["seed"],
            "geographic_regime": selection["geographic_regime"],
            "replicate": selection["replicate"],
            "anchor_source_station_row_index": anchor,
            "distance_from_anchor_m": f"{euclidean((station.x, station.y), (anchor_station.x, anchor_station.y)):.6f}",
            "selection_order": local,
        })
    return rows


def dataset_readme_text(counts: dict[str, int]) -> str:
    return f"""
# {FAMILY}

Classification: **generated_untested_paper_candidate**.  This family has not
been performance-tested and is not final paper evidence.

This dataset uses real Citi Bike station coordinates and capacities from the
two immutable local 443-row sources listed in `source_provenance.json`.  The
source files do not themselves contain IDs or names; those annotations are
recovered from a uniquely matching local companion station table.  Inventory,
targets, weights, minimum ratios, the centroid depot, fleet settings and route
horizons are synthetic.

Each V in {list(V_SET)} has four independent geographic selections: two compact
nearest-V regions and two broader regional selections covering V stations
inside the nearest-2V pool.  Each selection has shortage, balanced and surplus
inventory variants sharing the same station targets.  Source mapping CSVs make
every local station traceable to a zero-based authoritative source row.

The artificial depot is the rounded centroid of the selected points.  Input
files serialize exact three-decimal UTM 18N points and omit a redundant distance
matrix.  Current ExactEBRP rebuilds travel seconds as Euclidean meters / 1.5.
Every file contains two homogeneous-Q fleet densities per V and Q in {list(Q_SET)}.
T is not embedded in text; the scenario manifest binds each input SHA-256 to T
in {list(T_SET)}, pickup/drop defaults 60/60 seconds, and lambda 0.15.

Counts: {counts['selections']} independent selections, {counts['landscapes']}
station landscapes, {counts['instances']} complete parser inputs, and
{counts['scenarios']} future T scenarios.

Directory layout:

- `selections/`: geographic selection records;
- `landscapes/`: inventory/target/weight/min-ratio records;
- `mappings/`: depot and source-station provenance;
- `instances/`: current ExactEBRP text inputs;
- `manifests/`: selection, landscape, fleet/input, and T-scenario tables.

Regenerate from the ExactEBRP root with the commands in
`results/data_generation_citibike_round57/reproduction_commands.md`.  The
generator requires the legacy project at `{LEGACY.resolve()}` and verifies the
two authoritative hashes before use.

Known limitations: no observed trip/demand history, artificial centroid depot,
straight-line rather than street-network travel, a fixed 1.5 m/s conversion,
homogeneous vehicle capacities, and no performance evidence.
"""


def generate_family(stations: Sequence[SourceStation], output_root: Path = DATASET) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    source_hashes = {"capacity_sha256": sha256_file(CAPACITY_SOURCE), "coordinate_sha256": sha256_file(COORD_SOURCE)}
    selections: list[dict[str, Any]] = []
    selection_rows: list[dict[str, Any]] = []
    landscape_rows: list[dict[str, Any]] = []
    fleet_rows: list[dict[str, Any]] = []
    scenario_rows: list[dict[str, Any]] = []
    all_mapping_rows: list[dict[str, Any]] = []

    for v in V_SET:
        for geography in GEOGRAPHIC_REGIMES:
            for replicate in REPLICATES:
                selection = build_selection(stations, v, geography, replicate)
                selections.append(selection)
                selection_path = output_root / "selections" / f"V{v:02d}" / f"{selection['selection_id']}.json"
                write_json(selection_path, selection)
                mapping_path = output_root / "mappings" / f"V{v:02d}" / f"{selection['selection_id']}_source_mapping.csv"
                current_mapping_rows = mapping_rows(selection, stations)
                write_csv(mapping_path, current_mapping_rows)
                all_mapping_rows.extend(current_mapping_rows)
                stats = selection["geographic_statistics"]
                selection_rows.append({
                    "dataset_family": FAMILY,
                    "selection_id": selection["selection_id"],
                    "V": v,
                    "geographic_regime": geography,
                    "replicate": replicate,
                    "seed": selection["seed"],
                    "anchor_source_station_row_index": selection["anchor_source_station_row_index"],
                    "candidate_pool_size": selection["candidate_pool_size"],
                    "selected_source_station_row_indices": ";".join(map(str, selection["selected_source_station_row_indices"])),
                    "depot_easting_m": f"{selection['depot_coordinate_utm18n_meters'][0]:.3f}",
                    "depot_northing_m": f"{selection['depot_coordinate_utm18n_meters'][1]:.3f}",
                    "geographic_diameter_m": f"{stats['geographic_diameter_m']:.6f}",
                    "mean_pairwise_station_distance_m": f"{stats['mean_pairwise_station_distance_m']:.6f}",
                    "maximum_depot_distance_m": f"{stats['maximum_depot_distance_m']:.6f}",
                    "selection_path": output_root_relative(selection_path, output_root),
                    "selection_file_sha256": sha256_file(selection_path),
                    "mapping_path": output_root_relative(mapping_path, output_root),
                    "mapping_file_sha256": sha256_file(mapping_path),
                    **source_hashes,
                })

                for inventory_regime in INVENTORY_REGIMES:
                    landscape = build_landscape(selection, inventory_regime, stations)
                    landscape_path = output_root / "landscapes" / f"V{v:02d}" / f"{landscape['landscape_id']}.json"
                    write_json(landscape_path, landscape)
                    stats = landscape["statistics"]
                    landscape_row = {
                        "dataset_family": FAMILY,
                        "landscape_id": landscape["landscape_id"],
                        "selection_id": selection["selection_id"],
                        "V": v,
                        "geographic_regime": geography,
                        "replicate": replicate,
                        "inventory_regime": inventory_regime,
                        "local_imbalance_level": landscape["local_imbalance_level"],
                        "seed": landscape["seed"],
                        "source_station_row_indices": ";".join(map(str, landscape["source_station_row_indices"])),
                        "total_initial_inventory": stats["total_initial_inventory"],
                        "total_target_inventory": stats["total_target_inventory"],
                        "station_inventory_minus_target": stats["station_inventory_minus_target"],
                        "local_l1_imbalance": stats["local_l1_imbalance"],
                        "surplus_station_count": stats["surplus_station_count"],
                        "deficit_station_count": stats["deficit_station_count"],
                        "landscape_path": output_root_relative(landscape_path, output_root),
                        "landscape_file_sha256": sha256_file(landscape_path),
                        "mapping_path": output_root_relative(mapping_path, output_root),
                        **source_hashes,
                    }
                    landscape_rows.append(landscape_row)

                    for m in M_BY_V[v]:
                        for q in Q_SET:
                            instance_id = f"{landscape['landscape_id']}_M{m:02d}_Q{q:02d}"
                            instance_path = output_root / "instances" / f"V{v:02d}" / f"{instance_id}.txt"
                            write_text(instance_path, instance_text(landscape, m, q))
                            instance_sha = sha256_file(instance_path)
                            fleet_row = {
                                **landscape_row,
                                "instance_id": instance_id,
                                "M": m,
                                "Q": q,
                                "complete_Q_vector": canonical_json([q] * m),
                                "instance_path": output_root_relative(instance_path, output_root),
                                "instance_file_sha256": instance_sha,
                                "parser_format": "ExactEBRP Hybrid-GA-compatible text; points-authoritative",
                                "distance_convention": "Euclidean serialized UTM meters / 1.5 m/s, rebuilt by Parser.cpp",
                            }
                            fleet_rows.append(fleet_row)
                            for t in T_SET:
                                scenario_id = f"{instance_id}_T{t:05d}"
                                identity_material = canonical_json({
                                    "family": FAMILY, "instance_sha256": instance_sha, "T": t,
                                    "pickup_seconds": PICKUP_SECONDS, "drop_seconds": DROP_SECONDS, "lambda": LAMBDA,
                                })
                                scenario_rows.append({
                                    **fleet_row,
                                    "scenario_id": scenario_id,
                                    "T_seconds": t,
                                    "pickup_seconds": f"{PICKUP_SECONDS:.1f}",
                                    "drop_seconds": f"{DROP_SECONDS:.1f}",
                                    "lambda": f"{LAMBDA:.2f}",
                                    "mathematical_scenario_identity_sha256": sha256_bytes(identity_material.encode("utf-8")),
                                    "future_k1_am_sf_command": (
                                        f"build/ExactEBRP.exe --method tailored --algorithm-preset paper-k1-am-sf "
                                        f"--input {output_root_relative(instance_path, output_root)} --lambda {LAMBDA} --T {t} "
                                        "--time-limit <solver-seconds> --threads 1 --mip-threads 1 --out <result.json>"),
                                    "future_p_grb_command": (
                                        f"build/ExactEBRP.exe --method gurobi --plain-baseline --input {output_root_relative(instance_path, output_root)} "
                                        f"--lambda {LAMBDA} --T {t} --time-limit <solver-seconds> --threads 1 --gurobi-threads 1 --out <result.json>"),
                                })

    manifests = output_root / "manifests"
    write_csv(manifests / "geographic_selection_manifest.csv", selection_rows)
    write_csv(manifests / "station_landscape_manifest.csv", landscape_rows)
    write_csv(manifests / "fleet_variant_manifest.csv", fleet_rows)
    write_csv(manifests / "T_scenario_manifest.csv", scenario_rows)
    write_csv(manifests / "source_station_mapping_manifest.csv", all_mapping_rows)
    contract = generator_contract()
    write_json(output_root / "generator_contract.json", contract)
    write_json(output_root / "source_provenance.json", {
        "schema": "citibike443-source-provenance-v1",
        "authoritative_sources": contract["source_files"],
        "source_files_copied": False,
        "source_reference_policy": "immutable local legacy paths plus SHA-256",
        "real_derived_fields": ["service-station UTM coordinates", "service-station capacities"],
        "synthetic_fields": ["depot", "initial inventory", "target inventory", "weights", "minimum ratios", "M", "Q", "T"],
    })
    counts = {
        "selections": len(selection_rows),
        "landscapes": len(landscape_rows),
        "instances": len(fleet_rows),
        "scenarios": len(scenario_rows),
        "mapping_rows": len(all_mapping_rows),
    }
    if counts != {"selections": 20, "landscapes": 60, "instances": 240, "scenarios": 960, "mapping_rows": 500}:
        raise AssertionError(f"Unexpected family counts: {counts}")
    write_text(output_root / "README.md", dataset_readme_text(counts))
    write_json(manifests / "dataset_counts.json", counts)
    return {
        "counts": counts,
        "selection_rows": selection_rows,
        "landscape_rows": landscape_rows,
        "fleet_rows": fleet_rows,
        "scenario_rows": scenario_rows,
    }


def output_root_relative(path: Path, output_root: Path) -> str:
    relative = path.resolve().relative_to(output_root.resolve()).as_posix()
    return f"reference/{FAMILY}/{relative}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def validate_python_and_structure(stations: Sequence[SourceStation]) -> dict[str, list[dict[str, Any]]]:
    by_index = {station.source_row_index: station for station in stations}
    fleet_rows = read_csv(DATASET / "manifests" / "fleet_variant_manifest.csv")
    landscape_rows = read_csv(DATASET / "manifests" / "station_landscape_manifest.csv")
    generated_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    distance_rows: list[dict[str, Any]] = []
    inventory_rows: list[dict[str, Any]] = []

    for row in fleet_rows:
        path = ROOT / row["instance_path"]
        errors: list[str] = []
        try:
            parsed = parse_instance_mirror(path)
            v, m = int(row["V"]), int(row["M"])
            expected_q = int(row["Q"])
            if parsed["V"] != v or parsed["M"] != m:
                errors.append("header V/M mismatch")
            if parsed["Q"] != [expected_q] * m:
                errors.append("Q vector mismatch")
            if any(value < 0 or value > cap for value, cap in zip(parsed["initial"][1:], parsed["capacities"][1:])):
                errors.append("initial out of bounds")
            if any(value <= 0 or value > cap for value, cap in zip(parsed["target"][1:], parsed["capacities"][1:])):
                errors.append("target out of bounds")
            if any(not math.isfinite(value) or value < 0 for value in parsed["weights"][1:]):
                errors.append("invalid weight")
            if any(not math.isfinite(value) or not 0 <= value <= 1 for value in parsed["min_ratio"][1:]):
                errors.append("invalid min_ratio")
        except Exception as error:  # audit row captures exact failure
            errors.append(str(error))
            parsed = {"V": 0, "M": 0, "Q": []}
        generated_rows.append({
            "instance_id": row["instance_id"],
            "instance_path": row["instance_path"],
            "file_sha256_expected": row["instance_file_sha256"],
            "file_sha256_observed": sha256_file(path),
            "V": row["V"], "M": row["M"], "Q": row["Q"],
            "array_lengths_valid": not errors,
            "inventory_bounds_valid": not any("bounds" in error for error in errors),
            "weights_and_min_ratio_valid": not any("weight" in error or "min_ratio" in error for error in errors),
            "python_parser_mirror_accepted": not errors,
            "validation_status": "PASS" if not errors else "FAIL",
            "errors": "; ".join(errors),
        })

    for row in landscape_rows:
        landscape_path = ROOT / row["landscape_path"]
        landscape = json.loads(landscape_path.read_text(encoding="utf-8"))
        selected_indices = [int(value) for value in landscape["source_station_row_indices"]]
        expected_caps = [by_index[idx].capacity for idx in selected_indices]
        expected_points = [[by_index[idx].x, by_index[idx].y] for idx in selected_indices]
        source_errors: list[str] = []
        if len(set(selected_indices)) != landscape["V"]:
            source_errors.append("duplicate source station")
        if landscape["capacities"] != expected_caps:
            source_errors.append("capacity provenance mismatch")
        if landscape["points_utm18n_meters"] != expected_points:
            source_errors.append("coordinate provenance mismatch")
        if any(by_index[idx].capacity <= 0 for idx in selected_indices):
            source_errors.append("ineligible source station selected")
        source_rows.append({
            "landscape_id": landscape["landscape_id"],
            "selection_id": landscape["selection_id"],
            "V": landscape["V"],
            "unique_source_station_count": len(set(selected_indices)),
            "all_source_rows_exist": all(idx in by_index for idx in selected_indices),
            "capacities_match_authoritative_source": landscape["capacities"] == expected_caps,
            "coordinates_match_authoritative_source": landscape["points_utm18n_meters"] == expected_points,
            "source_hashes_match": landscape["source_hashes"] == {
                "capacity_sha256": sha256_file(CAPACITY_SOURCE),
                "coordinate_sha256": sha256_file(COORD_SOURCE),
            },
            "validation_status": "PASS" if not source_errors else "FAIL",
            "errors": "; ".join(source_errors),
        })

        depot = tuple(float(value) for value in landscape["depot"]["coordinate_utm18n_meters"])
        points = [depot, *[tuple(float(value) for value in pair) for pair in landscape["points_utm18n_meters"]]]
        matrix = [[euclidean(points[i], points[j]) / PARSER_SPEED_METERS_PER_SECOND for j in range(len(points))] for i in range(len(points))]
        finite = all(math.isfinite(value) for matrix_row in matrix for value in matrix_row)
        diagonal_zero = all(matrix[idx][idx] == 0.0 for idx in range(len(matrix)))
        symmetry_error = max(abs(matrix[i][j] - matrix[j][i]) for i in range(len(matrix)) for j in range(len(matrix)))
        source_duplicate_count = len(points[1:]) - len(set(points[1:]))
        distance_rows.append({
            "landscape_id": landscape["landscape_id"],
            "V": landscape["V"],
            "matrix_dimension": len(matrix),
            "finite": finite,
            "diagonal_zero": diagonal_zero,
            "maximum_symmetry_error": f"{symmetry_error:.17g}",
            "unintended_duplicate_service_coordinates": source_duplicate_count,
            "maximum_travel_seconds": f"{max(max(values) for values in matrix):.10f}",
            "matrix_source": "recomputed from exact serialized points using current Parser.cpp factor 1.5",
            "serialized_matrix_present": False,
            "validation_status": "PASS" if finite and diagonal_zero and symmetry_error == 0 and source_duplicate_count == 0 else "FAIL",
        })

        initial, target, capacity = landscape["initial"], landscape["target"], landscape["capacities"]
        deltas = [a - b for a, b in zip(initial, target)]
        total_delta = sum(deltas)
        regime = landscape["inventory_regime"]
        total_class_ok = total_delta < 0 if regime == "shortage" else total_delta > 0 if regime == "surplus" else total_delta == 0
        bounds_ok = all(0 <= value <= cap for value, cap in zip(initial, capacity)) and all(1 <= value <= cap for value, cap in zip(target, capacity))
        both_signs = any(delta > 0 for delta in deltas) and any(delta < 0 for delta in deltas)
        inventory_rows.append({
            "landscape_id": landscape["landscape_id"],
            "V": landscape["V"],
            "inventory_regime": regime,
            "total_initial_inventory": sum(initial),
            "total_target_inventory": sum(target),
            "station_inventory_minus_target": total_delta,
            "total_class_satisfied": total_class_ok,
            "inventory_and_target_bounds_valid": bounds_ok,
            "surplus_station_count": sum(delta > 0 for delta in deltas),
            "deficit_station_count": sum(delta < 0 for delta in deltas),
            "both_local_signs_present": both_signs,
            "local_l1_imbalance": sum(abs(delta) for delta in deltas),
            "weights_finite_and_in_0_1": all(math.isfinite(value) and 0 <= value <= 1 for value in landscape["weights"]),
            "minimum_ratios_finite_and_in_0_1": all(math.isfinite(value) and 0 <= value <= 1 for value in landscape["min_ratio"]),
            "validation_status": "PASS" if total_class_ok and bounds_ok and both_signs else "FAIL",
        })

    write_csv(EVIDENCE / "generated_instance_validation.csv", generated_rows)
    write_csv(EVIDENCE / "source_mapping_validation.csv", source_rows)
    write_csv(EVIDENCE / "distance_validation.csv", distance_rows)
    write_csv(EVIDENCE / "inventory_regime_validation.csv", inventory_rows)
    for label, rows in {
        "generated inputs": generated_rows, "source mappings": source_rows,
        "distance matrices": distance_rows, "inventory regimes": inventory_rows,
    }.items():
        failures = [row for row in rows if row["validation_status"] != "PASS"]
        if failures:
            raise RuntimeError(f"{label} validation failed for {len(failures)} rows")
    return {
        "generated": generated_rows,
        "source": source_rows,
        "distance": distance_rows,
        "inventory": inventory_rows,
    }


def compile_and_run_current_parser_probe() -> list[dict[str, Any]]:
    tools_dir = EVIDENCE / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    executable = tools_dir / "round57_parser_probe.exe"
    compiler = Path("D:/msys64/ucrt64/bin/g++.exe")
    command = [
        str(compiler), "-std=c++17", "-O0", "-I", str(ROOT / "include"),
        str(ROOT / "src" / "Parser.cpp"), str(ROOT / "scripts" / "round57_parser_probe.cpp"),
        "-o", str(executable),
    ]
    compile_result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    write_text(EVIDENCE / "tools" / "parser_probe_build.log", compile_result.stdout or "compile completed without output")
    if compile_result.returncode != 0:
        raise RuntimeError("Parser-only probe compilation failed")
    probe = subprocess.run(
        [str(executable), str(DATASET / "instances")], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    rows: list[dict[str, Any]] = []
    for line in probe.stdout.splitlines():
        parts = line.split("\t", 8)
        if len(parts) != 9:
            continue
        status, path, v, m, q_count, node_count, point_count, distance_rows, detail = parts
        observed_path = Path(path)
        try:
            rel = observed_path.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            rel = path
        rows.append({
            "instance_path": rel,
            "current_cpp_parser_status": status,
            "V": v,
            "M": m,
            "Q_count": q_count,
            "node_array_count": node_count,
            "point_count": point_count,
            "distance_row_count": distance_rows,
            "distance_convention_or_error": detail,
            "parser_source_path": repo_path(ROOT / "src" / "Parser.cpp"),
            "parser_source_sha256": sha256_file(ROOT / "src" / "Parser.cpp"),
            "probe_source_sha256": sha256_file(ROOT / "scripts" / "round57_parser_probe.cpp"),
        })
    write_csv(EVIDENCE / "parser_compatibility.csv", rows)
    if probe.returncode != 0 or len(rows) != 240 or any(row["current_cpp_parser_status"] != "PASS" for row in rows):
        raise RuntimeError(f"Current C++ parser compatibility failed: return={probe.returncode}, rows={len(rows)}")
    return rows


def deterministic_regeneration(stations: Sequence[SourceStation]) -> list[dict[str, Any]]:
    temp = EVIDENCE / "_deterministic_regeneration_tmp"
    if temp.exists():
        resolved = temp.resolve()
        if resolved.parent != EVIDENCE.resolve() or resolved.name != "_deterministic_regeneration_tmp":
            raise RuntimeError("Refusing to remove unexpected deterministic-regeneration path")
        shutil.rmtree(resolved)
    generate_family(stations, temp)
    authoritative = {path.relative_to(DATASET).as_posix(): path for path in DATASET.rglob("*") if path.is_file()}
    regenerated = {path.relative_to(temp).as_posix(): path for path in temp.rglob("*") if path.is_file()}
    all_paths = sorted(set(authoritative) | set(regenerated))
    rows: list[dict[str, Any]] = []
    for rel in all_paths:
        original = authoritative.get(rel)
        replay = regenerated.get(rel)
        original_sha = sha256_file(original) if original else ""
        replay_sha = sha256_file(replay) if replay else ""
        rows.append({
            "relative_path": rel,
            "authoritative_present": original is not None,
            "regenerated_present": replay is not None,
            "authoritative_sha256": original_sha,
            "regenerated_sha256": replay_sha,
            "byte_equal": bool(original and replay and original.read_bytes() == replay.read_bytes()),
            "validation_status": "PASS" if original and replay and original_sha == replay_sha else "FAIL",
        })
    write_csv(EVIDENCE / "deterministic_regeneration_audit.csv", rows)
    failures = [row for row in rows if row["validation_status"] != "PASS"]
    resolved = temp.resolve()
    if resolved.parent != EVIDENCE.resolve() or resolved.name != "_deterministic_regeneration_tmp":
        raise RuntimeError("Temporary regeneration directory safety check failed")
    shutil.rmtree(resolved)
    if failures:
        raise RuntimeError(f"Deterministic regeneration differs for {len(failures)} files")
    return rows


def verify_preservation() -> dict[str, Any]:
    baseline = json.loads((EVIDENCE / "historical_preservation_baseline.json").read_text(encoding="utf-8"))
    final_families: list[dict[str, Any]] = []
    all_pass = True
    for before in baseline["families"]:
        path = Path(before["path"])
        excluded = (f"{FAMILY}/",) if before["family_name"] == "exactebrp_all_pre_round57_reference" else ()
        after = tree_snapshot(path, complete_hashes=False, exclude_relative_prefixes=excluded)
        passed = (
            before["file_count"] == after["file_count"] and
            before["total_bytes"] == after["total_bytes"] and
            before["complete_content_tree_sha256"] == after["complete_content_tree_sha256"]
        )
        all_pass = all_pass and passed
        final_families.append({
            "family_name": before["family_name"],
            "local_path": before["path"],
            "file_count": before["file_count"],
            "total_size_bytes": before["total_bytes"],
            "complete_content_tree_sha256_before": before["complete_content_tree_sha256"],
            "complete_content_tree_sha256_after": after["complete_content_tree_sha256"],
            "representative_hashes": before["representative_files"],
            "status": before["status"],
            "used_in_historical_experiments": before["used_in_historical_experiments"],
            "real_derived_or_synthetic": before["derivation"],
            "superseded": before["superseded"],
            "preservation_status": "PASS" if passed else "FAIL",
        })

    exact_audit = json.loads((EVIDENCE / "repository_start_audit.json").read_text(encoding="utf-8"))["exactebrp"]
    legacy_audit = json.loads((EVIDENCE / "repository_start_audit.json").read_text(encoding="utf-8"))["legacy_hybrid_ga"]
    exact_final_entries = filtered_start_status(git_status_entries(ROOT))
    legacy_final_entries = git_status_entries(LEGACY)
    exact_status_match = status_summary(exact_final_entries)["status_fingerprint_sha256"] == exact_audit["status"]["status_fingerprint_sha256"]
    legacy_status_match = status_summary(legacy_final_entries)["status_fingerprint_sha256"] == legacy_audit["status"]["status_fingerprint_sha256"]
    def preserved_tracked_row(repo: Path, row: dict[str, Any]) -> bool:
        path = repo / row["path"]
        if row.get("sha256") is None:
            return not path.is_file()
        return path.is_file() and sha256_file(path) == row["sha256"]

    tracked_hash_match = all(
        preserved_tracked_row(ROOT, row)
        for row in exact_audit["preexisting_tracked_modifications"])
    legacy_tracked_hash_match = all(
        preserved_tracked_row(LEGACY, row)
        for row in legacy_audit["preexisting_tracked_modifications"])
    head_unchanged = git_text(ROOT, "rev-parse", "HEAD") == exact_audit["head"]
    branch_unchanged = git_text(ROOT, "branch", "--show-current") == exact_audit["branch"]
    legacy_head_unchanged = git_text(LEGACY, "rev-parse", "HEAD") == legacy_audit["head"]
    source_unchanged = (
        sha256_file(CAPACITY_SOURCE) == "92ca9b05e66d1425bbc801be2dd9c0776b1a9707e62a60b821d941aa98625ae1" and
        sha256_file(COORD_SOURCE) == "c5fd892cc82e07332d4796edb0527182d9c60883acc9b87a5410dab569f990d1")
    all_pass = all_pass and exact_status_match and legacy_status_match and tracked_hash_match and legacy_tracked_hash_match and head_unchanged and branch_unchanged and legacy_head_unchanged and source_unchanged
    manifest = {
        "schema": "citibike-data-round-historical-preservation-manifest-v1",
        "classification": "all_historical_datasets_preserved" if all_pass else "historical_dataset_preservation_failure",
        "families": final_families,
        "new_family": {
            "family_name": FAMILY,
            "local_path": str(DATASET.resolve()),
            "file_count": sum(path.is_file() for path in DATASET.rglob("*")),
            "total_size_bytes": sum(path.stat().st_size for path in DATASET.rglob("*") if path.is_file()),
            "status": "generated_untested_paper_candidate",
            "real_derived_or_synthetic": "real Citi Bike geography/capacity plus documented synthetic fields",
            "used_in_historical_experiments": False,
            "superseded": False,
        },
        "repository_checks": {
            "exactebrp_branch_unchanged": branch_unchanged,
            "exactebrp_head_unchanged": head_unchanged,
            "exactebrp_preexisting_filtered_status_unchanged": exact_status_match,
            "exactebrp_preexisting_tracked_modification_hashes_unchanged": tracked_hash_match,
            "legacy_head_unchanged": legacy_head_unchanged,
            "legacy_status_unchanged": legacy_status_match,
            "legacy_preexisting_tracked_modification_hashes_unchanged": legacy_tracked_hash_match,
            "authoritative_source_hashes_unchanged": source_unchanged,
        },
        "interpretation": {
            "legacy_hybrid_ga": "retained as historical mixed real-derived/synthetic data and provenance evidence",
            "round56": "retained as controlled synthetic benchmark data",
            "new_family": "adds real Citi Bike geographic and capacity provenance and has not been performance-tested",
        },
    }
    write_json(EVIDENCE / "historical_dataset_preservation_manifest.json", manifest)
    if not all_pass:
        raise RuntimeError("Historical preservation verification failed")
    return manifest


def write_reproduction_docs() -> None:
    python_exe = str(Path(sys.executable).resolve())
    write_text(EVIDENCE / "reproduction_commands.md", f"""
# Reproduction commands

Run from `{ROOT.resolve()}`.  These commands perform data audit, generation and
validation only; none launches an optimizer.

```powershell
& '{python_exe}' scripts/generate_citibike443_regional_v1.py --phase audit-pilot
& '{python_exe}' scripts/generate_citibike443_regional_v1.py --phase full
& '{python_exe}' scripts/generate_citibike443_regional_v1.py --phase validate
```

The validation phase compiles `scripts/round57_parser_probe.cpp` together with
the current `src/Parser.cpp` at `-O0` and parses all 240 input files.  It does not
link or launch ExactEBRP optimization code.  It also regenerates the deterministic
dataset in a guarded temporary directory, requires byte equality for every file,
and removes only that temporary directory.

Future performance commands are stored per row in
`reference/{FAMILY}/manifests/T_scenario_manifest.csv`.  They are documentation
only in this round.  A recommended next experiment is a preregistered structural
screen of all 960 rows followed by a balanced subset comparing K1-AM-SF and
P-GRB, using identical T, one thread, fixed solver budgets and no result-based
instance replacement.
""")


def write_registry_and_naming() -> None:
    write_json(EVIDENCE / "dataset_naming_decision.json", {
        "schema": "citibike443-dataset-naming-decision-v1",
        "canonical_name": FAMILY,
        "dataset_root": str(DATASET.resolve()),
        "reason": "The name identifies the authoritative 443-station universe, the regional/compact multiregime design, and its first frozen version without falsely claiming legacy reproduction or final paper status.",
        "classification": "generated_untested_paper_candidate",
        "subfamilies": {"geographic": list(GEOGRAPHIC_REGIMES), "inventory": list(INVENTORY_REGIMES)},
    })
    write_json(EVIDENCE / "local_dataset_registry.json", {
        "schema": "exactebrp-local-dataset-registry-v1",
        "families": [
            {"name": "legacy-hybrid-ga", "path": str((LEGACY / "testdata").resolve()), "status": "historical", "provenance": "mixed"},
            {"name": "exactebrp-generated", "path": str((ROOT / "reference" / "generated").resolve()), "status": "historical", "provenance": "synthetic"},
            {"name": "round56-paper-candidate", "path": str((ROOT / "reference" / "round56_paper_candidate").resolve()), "status": "historical-controlled-synthetic", "provenance": "synthetic"},
            {"name": FAMILY, "path": str(DATASET.resolve()), "status": "generated_untested_paper_candidate", "provenance": "real coordinates/capacities plus synthetic operational fields"},
        ],
    })


def write_final_report(
        source_audit: dict[str, Any], legacy_audit: dict[str, Any],
        validations: dict[str, list[dict[str, Any]]], parser_rows: Sequence[dict[str, Any]],
        regeneration_rows: Sequence[dict[str, Any]], preservation: dict[str, Any]) -> None:
    counts = json.loads((DATASET / "manifests" / "dataset_counts.json").read_text(encoding="utf-8"))
    source = source_audit
    cap = source["capacity_source"]
    coord = source["coordinate_source"]
    report = f"""
# Local Citi Bike data reconstruction round — final report

## Decision and paths

Completion status: **local_data_only_round_complete**.  Source classification:
**{source['classification']}**.  Legacy audit: **{legacy_audit['classification']}**.
Dataset design: **adaptive_citibike_dataset_design_frozen**.  Generation:
**citibike_derived_candidate_dataset_complete_with_subfamilies**.  Compatibility:
**exactebrp_input_compatible**.  Preservation:
**{preservation['classification']}**.

- ExactEBRP: `{ROOT.resolve()}`; branch `{git_text(ROOT, 'branch', '--show-current')}`;
  HEAD `{git_text(ROOT, 'rev-parse', 'HEAD')}`.
- Legacy Hybrid GA: `{LEGACY.resolve()}`; branch
  `{git_text(LEGACY, 'branch', '--show-current')}`; HEAD
  `{git_text(LEGACY, 'rev-parse', 'HEAD')}`.
- Capacity source: `{CAPACITY_SOURCE.resolve()}` — {cap['parsed_row_count']} rows,
  SHA-256 `{cap['sha256']}`.
- Coordinate source: `{COORD_SOURCE.resolve()}` — {coord['parsed_row_count']} rows,
  SHA-256 `{coord['sha256']}`.

Capacity and coordinate rows are aligned line by line.  The legacy loader maps
both source row i values to one-based internal index i+1.  The older companion
snapshot confirms 438 pairs by coordinate and capacity, four more by coordinate
with a changed capacity snapshot, and lacks one coordinate.  These annotation
issues do not alter the explicit source-row pairing.  The authoritative files
contain no IDs or names; companion IDs/names are included only where mapped.
One zero-capacity row is preserved but excluded from generated service subsets.

## Legacy findings and current format

Multiple legacy generator versions exist.  Generic routines synthesize every
field; the Citi Bike routine reads 414- or 443-row local lists, uses random or
anchor-nearest subsets, an artificial centroid depot, unseeded random inventory
and targets, target-squared weights, random minimum ratios, and Euclidean
distance / 1.5.  Its writer emits the current seven-field text shape plus a
matrix, while its reader rebuilds the matrix from points.  Working-tree changes
to capacity filtering, target bands, and weight scale are documented and were
not modified.

Retained rules are paired source-row alignment, positive-capacity eligibility,
spatial locality, the centroid depot, exact source capacities/coordinates,
homogeneous Q vectors, external T, and Euclidean UTM / 1.5 travel seconds.
Adapted or replaced rules are deterministic anchor choice/ties, two meaningful
geographic regimes, controlled inventory totals, a shared target comparison
profile, bounded target-derived weights/minimum ratios, and a points-only
single-authority file representation.

The current ExactEBRP parser requires `V M [Q...]`, five depot-inclusive arrays,
and either V+1 points or a matrix.  This family writes V+1 points, so the parser
rebuilds the matrix.  T is a scenario-manifest/`--T` value; pickup/drop remain
the current 60/60-second defaults.

## Frozen family design

Canonical name: **{FAMILY}**.  Root: `{DATASET.resolve()}`.  Its classification
is `generated_untested_paper_candidate`, not final paper evidence.

Four independent source selections exist for each V: two compact nearest-V
regions and two regional farthest-first selections within the anchor's nearest
2V eligible stations.  Four anchors per V are farthest-separated after a
SHA-256-ranked start.  The depot is the three-decimal centroid.  Real-derived
fields are service coordinates and capacities; all inventories, targets,
weights, minimum ratios, depot and fleet/scenario settings are synthetic.

Each selection shares one target profile across shortage, exact-balance and
surplus initial-inventory regimes.  Shortage/surplus magnitude is 12% of total
target (at least V); local transfers guarantee both surplus and deficit stations.
Weights are bounded target-squared values normalized to one.  Minimum ratios are
0.10+0.40 times target fill ratio.  Points are serialized at source precision;
travel time is symmetric Euclidean meters / 1.5 m/s.

Coverage is V={list(V_SET)}, M={canonical_json(M_BY_V)}, Q={list(Q_SET)}, and
T={list(T_SET)} seconds.  Counts are {counts['selections']} geographic
selections, {counts['landscapes']} station landscapes, {counts['instances']}
complete parser input/fleet variants, and {counts['scenarios']} future T
scenarios.  Per V there are 4 selections, 12 landscapes, 48 inputs, and 192
scenarios.

## Pilot, validation, and preservation

The structural pilot used six small/medium/large cases across both geography
rules and all inventory-total rules.  It found no structural defect, so no
generated instance was replaced and the initial current-project rules were
frozen unchanged.  No performance criterion was examined.

All {len(validations['generated'])} inputs pass structural and Python parser-
semantic checks.  The standalone current-C++-parser probe accepted all
{len(parser_rows)} files.  All {len(validations['source'])} landscapes map every
station to authoritative source rows; distance and inventory validation pass
for all {len(validations['distance'])}/{len(validations['inventory'])} rows.
Deterministic regeneration achieved byte equality for all {len(regeneration_rows)}
dataset files and removed the guarded temporary directory.

All historical dataset tree hashes, both repositories' starting HEAD/status,
the three pre-existing ExactEBRP tracked edits, the legacy tracked edits, and
the two authoritative source hashes are unchanged.  The legacy project was
read-only.  No optimizer executable, K1-AM-SF, P-GRB, VD-P, Gurobi, CPLEX, HGA,
branch-and-cut, or runtime experiment was executed.  No commit, push, pull
request update, pull request creation, or merge occurred.

## Limitations and next experiment

The family has no trip/demand observations, uses an artificial centroid depot,
straight-line travel at a fixed 1.5 m/s, synthetic operational fields,
homogeneous Q, and no difficulty/performance qualification.  The companion IDs
are inferred only through exact local coordinate/capacity matching.

Next, preregister the 960-row structural matrix and a balanced screening subset
before any solve.  Run K1-AM-SF and P-GRB with identical one-thread budgets and
all four T values; retain every result, avoid replacing instances, and use the
inventory/geography labels only for stratified analysis.

## Main artifacts

- Dataset README: `{(DATASET / 'README.md').resolve()}`
- Selection/landscape/fleet/T manifests: `{(DATASET / 'manifests').resolve()}`
- Source mappings: `{(DATASET / 'mappings').resolve()}`
- Source and legacy audits: `{EVIDENCE.resolve()}`
- Validation tables: `{EVIDENCE.resolve()}`
- Reproduction commands: `{(EVIDENCE / 'reproduction_commands.md').resolve()}`
"""
    write_text(EVIDENCE / "final_report.md", report)

    decision = {
        "schema": "citibike-data-round-final-decision-v1",
        "completion_status": "complete",
        "source_classification": source["classification"],
        "legacy_audit_classification": legacy_audit["classification"],
        "dataset_design_classification": "adaptive_citibike_dataset_design_frozen",
        "generation_classification": "citibike_derived_candidate_dataset_complete_with_subfamilies",
        "compatibility_classification": "exactebrp_input_compatible",
        "preservation_classification": preservation["classification"],
        "execution_classification": "local_data_only_round_complete",
        "adaptive_design_note": "current_project_adaptive_design_not_exact_legacy_reproduction",
        "dataset_name": FAMILY,
        "dataset_root": str(DATASET.resolve()),
        "counts": counts,
        "all_cpp_parser_rows_pass": len(parser_rows) == 240 and all(row["current_cpp_parser_status"] == "PASS" for row in parser_rows),
        "deterministic_regeneration_pass": all(row["validation_status"] == "PASS" for row in regeneration_rows),
        "optimizer_executed": False,
        "commit_created": False,
        "push_performed": False,
        "pull_request_created_or_updated": False,
    }
    write_json(EVIDENCE / "final_decision.json", decision)


def write_final_inventory() -> list[dict[str, Any]]:
    candidates = [Path(__file__), ROOT / "scripts" / "round57_parser_probe.cpp"]
    candidates.extend(path for path in DATASET.rglob("*") if path.is_file())
    candidates.extend(path for path in EVIDENCE.rglob("*") if path.is_file() and path.name != "final_data_inventory.csv")
    unique = sorted({path.resolve() for path in candidates}, key=lambda path: str(path).lower())
    rows = [{
        "path": repo_path(path),
        "absolute_path": str(path),
        "category": "dataset" if DATASET.resolve() in path.parents else "evidence" if EVIDENCE.resolve() in path.parents else "reproduction_tool",
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    } for path in unique]
    write_csv(EVIDENCE / "final_data_inventory.csv", rows)
    return rows


def require_authoritative_hashes() -> None:
    expected = {
        CAPACITY_SOURCE: "92ca9b05e66d1425bbc801be2dd9c0776b1a9707e62a60b821d941aa98625ae1",
        COORD_SOURCE: "c5fd892cc82e07332d4796edb0527182d9c60883acc9b87a5410dab569f990d1",
    }
    for path, digest in expected.items():
        observed = sha256_file(path)
        if observed != digest:
            raise RuntimeError(f"Authoritative source hash changed for {path}: {observed}")


def audit_and_pilot() -> tuple[list[SourceStation], dict[str, Any], dict[str, Any]]:
    create_start_audit()
    require_authoritative_hashes()
    stations, mapping_meta = load_source_stations()
    source_audit = audit_sources(stations, mapping_meta)
    legacy_audit = audit_legacy_project(stations)
    audit_exactebrp_requirements()
    write_registry_and_naming()
    run_structural_pilot(stations)
    return stations, source_audit, legacy_audit


def full_generation(stations: Sequence[SourceStation]) -> dict[str, Any]:
    required = [
        EVIDENCE / "dataset_design_proposal.md",
        EVIDENCE / "structural_pilot_manifest.csv",
        EVIDENCE / "structural_pilot_analysis.md",
        EVIDENCE / "generator_revision_history.md",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Audit/pilot must precede full generation; missing: " + ", ".join(missing))
    contract = generator_contract()
    write_json(EVIDENCE / "frozen_generator_contract.json", contract)
    generated = generate_family(stations, DATASET)
    write_reproduction_docs()
    return generated


def validation_and_finalization(
        stations: Sequence[SourceStation], source_audit: dict[str, Any], legacy_audit: dict[str, Any]) -> dict[str, Any]:
    if not (DATASET / "generator_contract.json").is_file():
        raise RuntimeError("Full generation must precede validation")
    validations = validate_python_and_structure(stations)
    parser_rows = compile_and_run_current_parser_probe()
    regeneration_rows = deterministic_regeneration(stations)
    preservation = verify_preservation()
    write_reproduction_docs()
    write_registry_and_naming()
    write_final_report(source_audit, legacy_audit, validations, parser_rows, regeneration_rows, preservation)
    inventory = write_final_inventory()
    return {
        "dataset": FAMILY,
        "dataset_root": str(DATASET.resolve()),
        "selection_count": 20,
        "landscape_count": 60,
        "instance_count": len(validations["generated"]),
        "scenario_count": 960,
        "cpp_parser_pass_count": sum(row["current_cpp_parser_status"] == "PASS" for row in parser_rows),
        "deterministic_file_count": len(regeneration_rows),
        "final_inventory_row_count": len(inventory),
        "preservation_classification": preservation["classification"],
        "optimizer_executed": False,
        "commit_push_pr_activity": False,
    }


def load_existing_audit_summaries() -> tuple[dict[str, Any], dict[str, Any]]:
    source_audit = json.loads((EVIDENCE / "source_file_audit.json").read_text(encoding="utf-8"))
    historical = read_csv(EVIDENCE / "historical_instance_inventory.csv")
    legacy_audit = {
        "classification": "multiple_legacy_generator_versions_found",
        "historical_instance_count": len(historical),
    }
    return source_audit, legacy_audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("audit-pilot", "full", "validate", "all"), default="all")
    args = parser.parse_args()
    if ROOT.resolve() != Path.cwd().resolve():
        raise RuntimeError(f"Run from ExactEBRP repository root: {ROOT}")
    if not LEGACY.is_dir():
        raise FileNotFoundError(f"Legacy Hybrid GA project not found: {LEGACY}")

    summary: dict[str, Any] = {"phase": args.phase, "optimizer_executed": False}
    if args.phase in {"audit-pilot", "all"}:
        stations, source_audit, legacy_audit = audit_and_pilot()
        summary.update({
            "source_classification": source_audit["classification"],
            "legacy_classification": legacy_audit["classification"],
            "pilot_status": "PASS",
        })
    else:
        require_authoritative_hashes()
        stations, _ = load_source_stations()
        source_audit, legacy_audit = load_existing_audit_summaries()

    if args.phase in {"full", "all"}:
        generated = full_generation(stations)
        summary.update(generated["counts"])

    if args.phase in {"validate", "all"}:
        summary.update(validation_and_finalization(stations, source_audit, legacy_audit))

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
