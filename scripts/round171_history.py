"""Targeted static identity check of the pinned historical input scope."""

import collections
import csv
import io
import json
import re

from generate_citibike443_regional_v1 import parse_instance_mirror
from round163_setup import canonical
from round171_common import BASE, OUT, ROOT, TEMP, blob, digest, git, utc, write


def records(doc):
    if isinstance(doc, dict):
        yield doc
        for item in doc.values():
            yield from records(item)
    elif isinstance(doc, list):
        for item in doc:
            yield from records(item)


def index_history(rounds, r58_panel):
    known = set(git("ls-tree", "-r", "--name-only", BASE, "--", "reference", "results", "testdata").splitlines())
    manifests = [f"results/unified_exact_round{n}/input_manifest.json" for n in rounds]
    index = collections.defaultdict(list)
    selection_map = {}
    raw_inputs, manifests_seen, unresolved = {}, [], []
    config_fields = {"T_seconds", "lambda"}

    def resolve(value):
        normalized = value.replace("\\", "/")
        for stem in ("reference/", "results/", "testdata/"):
            i = normalized.find(stem)
            if i >= 0 and normalized[i:] in known:
                return normalized[i:]
        return normalized if normalized in known else None

    def add_input(path, manifest, role=None, config=None, expected_sha=None):
        if path not in raw_inputs:
            raw = blob(BASE, path)
            assert len(raw) < 1_000_000, path
            place = TEMP / "historical_inputs" / (digest(raw) + ".txt")
            place.parent.mkdir(parents=True, exist_ok=True)
            if not place.exists():
                place.write_bytes(raw)
            try:
                parsed = parse_instance_mirror(place)
                raw_inputs[path] = (digest(raw), parsed)
            except (ValueError, IndexError, AssertionError, KeyError, SyntaxError, AttributeError, TypeError) as error:
                raw_inputs[path] = (digest(raw), None)
                unresolved.append(dict(path=path, manifest=manifest, issue="legacy text schema", detail=str(error)[:160]))
        actual_sha, parsed = raw_inputs[path]
        if expected_sha and expected_sha != actual_sha:
            unresolved.append(dict(path=path, manifest=manifest, issue="manifest byte hash differs from pinned Git blob",
                                   expected=expected_sha, actual=actual_sha))
        if parsed is None:
            return
        base_key, full_key = canonical(parsed, config)
        index[base_key].append(dict(input=path, manifest=manifest, id=role, n=parsed["V"],
                                    checked_input_SHA256=actual_sha, full_key=full_key))
        effective = dict(parsed)
        effective["weights"] = [
            weight / 10 if abs(max(parsed["weights"][1:]) - 10) <= 1e-6 and i else weight
            for i, weight in enumerate(parsed["weights"])
        ]
        effective["weights"] = [0.0 if weight == 0 else weight for weight in effective["weights"]]
        effective["points"] = [[0.0 if coord == 0 else coord for coord in point] for point in parsed["points"]]
        effective_base, effective_full = canonical(effective, config)
        if effective_base != base_key:
            index[effective_base].append(dict(input=path, manifest=manifest, id=role, n=parsed["V"],
                                              full_key=effective_full, parser_effective=True))

    def add_selection(path, source):
        if path in selection_map:
            return
        value = json.loads(blob(BASE, path))
        rows = value.get("selected_source_station_row_indices")
        if rows is not None and source:
            selection_map[path] = dict(path=path, source=source, rows=rows)

    for manifest in manifests:
        if manifest not in known:
            unresolved.append(dict(manifest=manifest, issue="manifest absent at pinned base"))
            continue
        raw = blob(BASE, manifest)
        manifests_seen.append(dict(path=manifest, SHA256=digest(raw)))
        for item in records(json.loads(raw)):
            path = item.get("input_path") or item.get("instance_path") or item.get("input")
            if isinstance(path, str) and path.lower().endswith(".txt"):
                resolved = resolve(path)
                if resolved is None:
                    unresolved.append(dict(manifest=manifest, path=path, issue="unresolved input path"))
                else:
                    config = item if config_fields <= item.keys() and all(
                        isinstance(item[k], (float, int)) for k in config_fields
                    ) else None
                    add_input(resolved, manifest, item.get("id"), config, item.get("input_sha256"))
            selection = item.get("selection_path")
            if isinstance(selection, str) and resolve(selection):
                source = item.get("source") or ("CITI" if "round109/" in manifest else None)
                if source in ("CITI", "CABI", "DIVVY"):
                    add_selection(resolve(selection), source)

    raw = blob(BASE, r58_panel)
    manifests_seen.append(dict(path=r58_panel, SHA256=digest(raw)))
    panel = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    n50_cases = [row for row in panel if int(row["V"]) == 50]
    assert len(n50_cases) == 10
    for case in n50_cases:
        path = resolve(case["instance_path"])
        assert path is not None
        config = {name: float(case[name]) for name in ("T_seconds", "lambda", "pickup_seconds", "drop_seconds")}
        add_input(path, r58_panel, case["scenario_id"], config, case["instance_file_sha256"])
        assert raw_inputs[path][1]["V"] == 50
    original_inputs = [
        path for path in known if path.startswith("reference/") and path.endswith(".txt")
        and re.search(r"(?:^|[/_-])(?:V|[CBXK])?50(?=[/_-]|\.)", path, flags=re.IGNORECASE)
    ]
    for path in sorted(original_inputs):
        if path not in raw_inputs:
            add_input(path, "pinned V50 text inventory")
    old_source_selections = [
        path for path in known if path.startswith("reference/citibike443-regional-v1/selections/") and path.endswith(".json")
    ]
    for path in sorted(old_source_selections):
        add_selection(path, "CITI")
    result = dict(
        UTC=utc(), commit=BASE, manifests=manifests_seen, distinct_text_inputs=len(raw_inputs),
        parsed_inputs=sum(parsed is not None for _, parsed in raw_inputs.values()),
        n50_inputs=sum(parsed is not None and parsed["V"] == 50 for _, parsed in raw_inputs.values()),
        round58_V50_cases=len(n50_cases), normalized_base_keys=dict(index),
        historical_source_selections=list(selection_map.values()), unresolved=unresolved,
        scope="Pinned manifest-linked inputs plus named V50 reference text. Parsed exact base and full keys when the config is present.",
        historical_raw_restored=0, Optimize=0,
    )
    write(OUT / "history_input_index.json", result)
    return result
