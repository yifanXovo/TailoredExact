"""Freeze one archived-source recipe, then generate its six static inputs."""

import argparse
import base64
import collections
import csv
import dataclasses
import gzip
import io
import json
import math
import re
import sys
import time
import zipfile
from pathlib import Path
from fractions import Fraction

import generate_citibike443_regional_v1 as selection_math
import round109_data as landscape_math
import round122_data as source_reader
from round163_setup import canonical
from round170_common import protected
from round171_common import (
    AFFINITY, BASE, BRANCH, CAP, DLL, DLL_SHA, MAIN, MASTER, MASTER_BASE_BYTES, MASTER_BASE_SHA,
    MEASURED, OUT, PE, PE_SHA, PR_BASE, ROOT, SCIENCE_CAP, SCIENCE_START, TEMP, WORK, bind, blob,
    digest, env, git, read, require_committed, sha, utc, write,
)

FAMILY = "round171-frozen-b-n50-positive-v1"
SPECS = [
    ("R171-C50-S-C", "CITI", "compact"), ("R171-C50-S-R", "CITI", "regional"),
    ("R171-B50-S-C", "CABI", "compact"), ("R171-B50-S-R", "CABI", "regional"),
    ("R171-X50-S-C", "DIVVY", "compact"), ("R171-X50-S-R", "DIVVY", "regional"),
]
VEHICLES = [20, 25, 30]
SOURCE_FILES = [
    "results/data_generation_citibike_round57/source_station_table.csv",
    "results/unified_exact_round116/source/source_station_table.csv",
    "results/unified_exact_round116/source/snapshot.json",
    "results/unified_exact_round116/source/row_decisions.json",
    "results/unified_exact_round116/projection_contract.json",
    "results/unified_exact_round116/source/requests/station_information/01.response",
    "results/unified_exact_round132/source/DIVVY/qualified_stations.json",
    "results/unified_exact_round132/source/DIVVY/snapshot.json",
    "results/unified_exact_round132/source/DIVVY/row_decisions.json",
    "results/unified_exact_round132/source/DIVVY/station_information.json",
]
DEPENDENCIES = [
    "scripts/round171_setup.py", "scripts/round171_common.py", "scripts/round171_history.py",
    "scripts/round163_setup.py",
    "scripts/round137_setup.py", "scripts/round122_common.py", "scripts/round122_data.py",
    "scripts/round109_data.py", "scripts/round118_data.py", "scripts/round107_reader.py",
    "scripts/generate_citibike443_regional_v1.py",
]
OLD_58 = "results/gf_citibike443_k1_vs_pgrb_round58/round58_complete_panel.csv"
HISTORY_ROUNDS = (109, 110, 116, 122, 123, 130, 131, 132, 137, 163)
SOURCES_132 = ROOT / "results/unified_exact_round132/source/DIVVY"


def master_base(goal):
    name = MASTER.name
    origin = "attached Markdown I2 (gzip Base64)"
    packages = sorted(goal.parent.glob("*Round171*.zip"))
    data = None
    for package in packages:
        with zipfile.ZipFile(package) as carrier:
            members = [member for member in carrier.namelist() if Path(member).name == name]
            if members:
                assert len(members) == 1
                data = carrier.read(members[0])
                origin = package.name + "/" + members[0]
                break
    if data is None:
        content = goal.read_text(encoding="utf-8-sig")
        marker = "GI_TBC_MASTER_126_GZIP_BASE64"
        blocks = re.findall(r"(?m)^BEGIN_" + marker + r"\n([A-Za-z0-9/+=\n]+)\nEND_" + marker + r"$", content)
        assert len(blocks) == 1
        data = gzip.decompress(base64.b64decode("".join(blocks[0].splitlines()), validate=True))
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"), newline="")))
    assert len(data) == MASTER_BASE_BYTES and digest(data) == MASTER_BASE_SHA and data.startswith(b"\xef\xbb\xbf")
    assert len(rows) == 127 and {len(row) for row in rows} == {28}
    assert data.count(b"\n") == data.count(b"\r\n") and data.endswith(b"\r\n")
    local = WORK / "data" / name
    local.parent.mkdir(parents=True, exist_ok=True)
    previous = None
    if local.is_file() and local.read_bytes() != data:
        previous = local.with_name("GI_TBC_preserved_" + sha(local)[:16] + ".csv")
        if not previous.exists():
            previous.write_bytes(local.read_bytes())
        assert previous.read_bytes() == local.read_bytes()
    local.write_bytes(data)
    MASTER.parent.mkdir(parents=True, exist_ok=True)
    if MASTER.exists():
        assert MASTER.read_bytes() == data, "An existing authority differs. Preserve it."
    else:
        MASTER.write_bytes(data)
    write(OUT / "CSV_base_receipt.json", dict(
        UTC=utc(), origin=origin, baseline=bind(MASTER), local_working_copy=str(local),
        prior_working_copy_preserved=str(previous) if previous else None, records=126, columns=28,
        BOM="UTF-8", line_ending="CRLF", previous_118_prefix_bytes=70240,
        previous_118_prefix_SHA256=digest(data[:70240]), Optimize=0,
    ))


def prepare(goal):
    assert not (OUT / "source_recipe.json").exists()
    assert git("rev-parse", "HEAD") == BASE
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "goal.md").write_bytes(goal.read_bytes())
    protected_status = protected()
    TEMP.mkdir(parents=True, exist_ok=True)
    write(TEMP / "protected_trees.json", protected_status)
    write(OUT / "entry_state.json", dict(
        UTC=utc(), science_start_epoch=SCIENCE_START, science_cap_seconds=SCIENCE_CAP,
        base=BASE, branch=BRANCH, PR_base=PR_BASE, main=MAIN, PR232="OPEN Draft",
        main_contains_round170=False, goal=bind(OUT / "goal.md"),
        policy=bind(ROOT / "WORKSPACE_POLICY.md"), AGENTS_found=False,
        protected=[dict(root=row["root"], HEAD=row["HEAD"], modified_tracked_files=len(row["files"]))
                   for row in protected_status],
    ))

    measured = read(ROOT / "results/unified_exact_round169/candidate_manifest.json")
    assert measured["source_commit"] == MEASURED
    assert PE.stat().st_size == 9_884_148 and sha(PE) == PE_SHA and sha(DLL) == DLL_SHA
    build = {name: bind(PE.parent / name) for name in ("CMakeCache.txt", "build.ninja", ".ninja_log")}
    assert build["CMakeCache.txt"]["SHA256"] == measured["build_cache"]["SHA256"]
    assert build["build.ninja"]["SHA256"] == measured["build_ninja"]["SHA256"]
    for name, expected in measured["source_hashes"].items():
        checked = (ROOT / name).read_bytes()
        assert digest(checked) == expected, name
        assert checked.replace(b"\r\n", b"\n") == blob(MEASURED, name).replace(b"\r\n", b"\n"), name
    write(OUT / "candidate_manifest.json", dict(
        UTC=utc(), source_commit=MEASURED, delivery_base=BASE, source_hashes=measured["source_hashes"],
        source_files_verified=len(measured["source_hashes"]), PE=bind(PE), DLL=bind(DLL), rebuilt=False,
        compiler=bind("D:/msys64/ucrt64/bin/g++.exe"), compiler_version=measured["compiler_version"],
        flags=measured["flags"], original_build_commands=measured["build_commands"], actual_build_evidence=build,
    ))
    write(OUT / "environment_manifest.json", dict(
        UTC=utc(), producer_PATH_prefix=env()["PATH"].split(";")[:2], Python=sys.version,
        PE=bind(PE), DLL=bind(DLL), Native_Seed=0, Threads=1, MIPThreads=1, H_seed=20260626,
        affinity_mask=AFFINITY, serial=True, installation_changed=False,
    ))
    for name in SOURCE_FILES:
        path = ROOT / name
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob(BASE, name))
        require_committed(path, BASE)
    master_base(goal)
    write(OUT / "source_recipe.json", dict(
        UTC=utc(), family=FAMILY, source_commit=BASE, specs=[
            dict(id=name, source=source, geometry=geometry, n=50, inventory="shortage",
                 replicate=1, Q=VEHICLES, M=len(VEHICLES), cap_seconds=CAP)
            for name, source, geometry in SPECS
        ],
        selection_id_rule="r171_<ID> plus _collision_k only for exact physical collisions",
        family_rule="FAMILY|source=<source>|source_sha256=<source_identity_SHA>, plus |collision=k if needed",
        anchors="R57/R137 hash-first, then farthest-first with original tie-break; compact slot 0 and regional slot 2",
        eligibility="Qualified archived rows with 0 < capacity < 100, excluding earlier accepted rows of the same source",
        regional_selection="R57 nearest-2n regional pool",
        inventory="R109 shortage, original target, weight, total adjustment and sign repair, checked with assert_equivalent",
        projections=dict(CITI="R57 UTM 18N metres", CABI="R116 EPSG:32618", DIVVY="R132 EPSG:32616"),
        measurements="Archived coordinates/capacity, synthetic or transformed operational fields",
        rho=1, lambda_rule="1/sum(serialized non-depot weights)", T_rule="300*ceil(max(1800,0.75*T_base)/300)",
        T_base="2*d_max/1.5 + 120*sum(max(b_i-D_i,0))/M, using serialized inputs",
        positivity="s=sum(D)-sum(b)>0 and min(w_i/D_i)>0 imply F >= lambda*min(w_i/D_i)*s>0; offline only",
        historical_identity_rule="R163 row-order-invariant base and full keys; bounded pinned input manifests and public text",
        generation_dependencies={name: sha(ROOT / name) for name in DEPENDENCIES},
        source_files={name: bind(ROOT / name) for name in SOURCE_FILES},
        before_any_H_DP_RN_or_Optimize=True, no_outcome_selection=True,
    ))
    print("Source recipe, 254 measured source bindings, PE/DLL and CSV126 verified", flush=True)


def source_pools():
    snapshots = source_reader.load_sources()
    divvy = read(SOURCES_132 / "snapshot.json")
    response_path = ROOT / divvy["response_path"]
    assert sha(response_path) == divvy["response_SHA"]
    response = read(response_path)["data"]["stations"]
    qualified = read(SOURCES_132 / "qualified_stations.json")
    decisions = {row["station_id"]: row for row in read(SOURCES_132 / "row_decisions.json") if row["accepted"]}
    assert len(response) == divvy["raw_rows"] and len(qualified) == len(decisions) == divvy["qualified"]
    assert [row["source_row_index"] for row in qualified] == list(range(len(qualified)))
    for row in qualified:
        indices = row["original_row_indices"]
        assert indices == decisions[row["station_id"]]["original_rows"]
        assert row["x"] == round(row["unrounded_x"], 3) and row["y"] == round(row["unrounded_y"], 3)
        for index in indices:
            raw = response[index]
            assert raw["station_id"] == row["station_id"] and raw["capacity"] == row["capacity"]
            assert raw["lat"] == row["latitude"] and raw["lon"] == row["longitude"]
            assert raw.get("is_virtual_station") is not True
    snapshots["DIVVY"] = [
        source_reader.cabi.Station(row["source_row_index"], row["station_id"], row["capacity"], row["x"],
                                   row["y"], row["latitude"], row["longitude"], tuple(row["original_row_indices"]))
        for row in qualified
    ]
    ids = {name: info["identity_SHA"] for name, info in source_reader.SOURCES.items()}
    ids["DIVVY"] = divvy["response_SHA"]
    return snapshots, ids


def history():
    """Read small pinned inputs. Missing paths and legacy schemas remain visible."""
    from round171_history import index_history

    return index_history(HISTORY_ROUNDS, OLD_58)


def generate():
    recipe_path = OUT / "source_recipe.json"
    require_committed(recipe_path)
    recipe = read(recipe_path)
    assert not (OUT / "input_manifest.json").is_file()
    for name, expected in recipe["generation_dependencies"].items():
        assert sha(ROOT / name) == expected, name
        checked = (ROOT / name).read_bytes()
        assert checked.replace(b"\r\n", b"\n") == blob("HEAD", name).replace(b"\r\n", b"\n"), name
    for name, expected in recipe["source_files"].items():
        assert sha(ROOT / name) == expected["SHA256"], name
    history_index = history()
    keys = history_index["normalized_base_keys"]
    inventory, replicate, n = "shortage", 1, 50
    snapshots, identities = source_pools()
    used = collections.defaultdict(set)
    roles, attempts, overlaps = [], [], []
    for name, source, geometry in SPECS:
        stations = snapshots[source]
        pool = [station for station in stations
                if 0 < station.capacity < 100 and station.source_row_index not in used[source]]
        collision_id = 0
        while True:
            selection_id = "r171_" + name
            family = f"{FAMILY}|source={source}|source_sha256={identities[source]}"
            if collision_id:
                family += f"|collision={collision_id}"
                selection_id += f"_collision_{collision_id}"
            selection_math.FAMILY = landscape_math.VERSION = family
            landscape_math.SOURCE_SHA = identities[source]
            selected = selection_math.build_selection(pool, n, geometry, replicate)
            projection = "EPSG:32616" if source == "DIVVY" else "EPSG:32618"
            selected.update(selection_id=selection_id, source=source, coordinate_CRS=projection,
                            excluded_previous_new_rows=sorted(used[source]),
                            pool_source_rows=[row.source_row_index for row in pool])
            landscape = landscape_math.landscape(selected, inventory, stations)
            landscape_math.assert_equivalent(selected, inventory, stations, landscape)
            lines = selection_math.instance_text(landscape, len(VEHICLES), VEHICLES[0]).splitlines()
            lines[0] = f"{n} {len(VEHICLES)} {json.dumps(VEHICLES)}"
            folder = f"collision_{collision_id}" if collision_id else "first"
            dest = OUT / "inputs" / name / folder / "instance.txt"
            dest.parent.mkdir(parents=True, exist_ok=True)
            instance_bytes = ("\n".join(lines).rstrip() + "\n").encode("utf-8")
            if dest.exists():
                assert dest.read_bytes() == instance_bytes
            else:
                dest.write_bytes(instance_bytes)
            parsed = selection_math.parse_instance_mirror(dest)
            assert (parsed["V"], parsed["M"], parsed["Q"]) == (n, len(VEHICLES), VEHICLES)
            c, b, demand, w = [parsed[key][1:] for key in ("capacities", "initial", "target", "weights")]
            assert all(0 <= x <= cap and 0 < d <= cap < 100 for cap, x, d in zip(c, b, demand))
            assert all(math.isfinite(weight) and weight > 0 for weight in w)
            assert abs(max(w) - 10) > 1e-6, "Legacy weight scaling changes this serialized input"
            assert all(math.isfinite(value) for point in parsed["points"] for value in point)
            surplus = sum(max(x - d, 0) for x, d in zip(b, demand))
            shortage = sum(demand) - sum(b)
            assert surplus > 0 and shortage > 0 and any(x < d for x, d in zip(b, demand))
            Omega = sum(w)
            lam = 1 / Omega
            a = min(Fraction(weight) / d for weight, d in zip(w, demand))
            floor = Fraction(lam) * a * shortage
            assert floor > 0
            d_max = max(selection_math.euclidean(parsed["points"][0], point) for point in parsed["points"][1:])
            T_base = 2 * d_max / 1.5 + 120 * surplus / len(VEHICLES)
            route_limit = 300 * math.ceil(max(1800, 0.75 * T_base) / 300)
            conf = {"T_seconds": route_limit, "lambda": lam, "pickup_seconds": 60, "drop_seconds": 60}
            physical_key, full_key = canonical(parsed, conf)
            path = dest.relative_to(ROOT).as_posix()
            collision = keys.get(physical_key, [])
            attempts.append(dict(
                id=name, k=collision_id, input=path, SHA256=sha(dest), family=family, selection_id=selection_id,
                base_key=physical_key, full_key=full_key, collisions=collision,
            ))
            by_index = {station.source_row_index: station for station in stations}
            selected_rows = selected["selected_source_station_row_indices"]
            mapping = [dict(local_station_index=i, source_identity_SHA256=identities[source],
                            **dataclasses.asdict(by_index[row]))
                       for i, row in enumerate(selected_rows, 1)]
            for label, value in (("selection", selected), ("landscape", landscape),
                                 ("parsed", parsed), ("source_mapping", mapping)):
                write(dest.with_name(label + ".json"), value)
            if not collision:
                break
            collision_id += 1

        assert len(set(selected_rows)) == n and not used[source].intersection(selected_rows)
        used[source].update(selected_rows)
        keys[physical_key] = [dict(id=name, input=path, base_key=physical_key, full_key=full_key)]
        for past in history_index["historical_source_selections"]:
            if past["source"] == source:
                match = sorted(set(selected_rows).intersection(past["rows"]))
                overlaps.append(dict(input=name, source=source, previous=past["path"], rows=match, count=len(match)))
        roles.append(dict(
            id=name, base_id=name, V=n, M=len(VEHICLES), Q_vector=VEHICLES, source=source,
            inventory=inventory, geometry=geometry, replicate=replicate, coordinate_CRS=projection,
            input_path=path, instance_path=path, input_sha256=sha(dest),
            selection_path=dest.with_name("selection.json").relative_to(ROOT).as_posix(),
            landscape_path=dest.with_name("landscape.json").relative_to(ROOT).as_posix(),
            source_identity_SHA=identities[source], family=family, selection_id=selection_id,
            cap_seconds=CAP, gurobi_seed=0, rho=1, Omega=Omega, sum_weights=Omega,
            lambda_decimal17=format(lam, ".17g"), lambda_binary64=lam.hex(),
            total_initial=sum(b), total_target=sum(demand), total_capacity=sum(c), shortage=shortage,
            donor_surplus_units=surplus, d_max_metres=d_max, T_base_seconds=T_base,
            a_min_w_over_D=float(a), a_exact_binary64_weights=str(a),
            positive_objective_floor_decimal=float(floor), positive_objective_floor_exact=str(floor),
            normalized_base_key=physical_key, normalized_full_key=full_key, **conf,
        ))
    write(OUT / "generation_attempts.json", attempts)
    write(OUT / "source_overlap.json", overlaps)
    write(OUT / "input_manifest.json", dict(
        UTC=utc(), recipe_commit=git("rev-parse", "HEAD"), source_recipe_SHA256=sha(recipe_path),
        history_index=bind(OUT / "history_input_index.json"), roles=roles,
        generation_once=True, H=0, Optimize=0, RN=0, DP=0, source_rows_disjoint_within_panel=True,
        no_performance_screening=True, base_or_full_collision_in_audited_history=False,
    ))
    print(json.dumps([{k: p[k] for k in ("id", "T_seconds", "lambda", "shortage", "input_sha256")} for p in roles]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "generate"])
    parser.add_argument("--goal", type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    if args.stage == "prepare":
        prepare(args.goal)
    else:
        generate()
    print(f"{args.stage} seconds={time.perf_counter() - started:.3f}")
