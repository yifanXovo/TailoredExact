"""Independent zero-solver recount of restored R105 exact raw ledgers.

Standard library only. No project imports, solver APIs, executable tests,
subprocess, reconstruction of fabricated calls, or original-tree fallback.
The root must contain both frozen SHA manifests and their restored bytes.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    assert not args.output.exists(), "fresh output required"
    old_prefix = "results/unified_exact_round105/"
    manifest_path = root / (old_prefix + "compact_evidence/manifest.json")
    supplement_path = root / "results/unified_exact_round106/r105_supplement/manifest.json"
    manifest_raw, supplement_raw = manifest_path.read_bytes(), supplement_path.read_bytes()
    manifest, supplement = json.loads(manifest_raw), json.loads(supplement_raw)
    old_hashes = {entry["path"]:entry["sha256"] for entry in manifest["files"]}
    recovered_hashes = {entry["original_path"]:entry["sha256"] for entry in supplement["files"]}
    assert len(recovered_hashes) == 66 and not (old_hashes.keys() & recovered_hashes.keys())
    expected_hashes = {**old_hashes, **recovered_hashes}
    provenance = {}
    def relative_name(value):
        name = str(value).replace("\\", "/")
        for marker in ("results/", "reference/"):
            at = name.find(marker)
            if at >= 0:
                name = name[at:]
                break
        assert not Path(name).is_absolute() and ".." not in Path(name).parts
        return name
    def read(relative):
        name = relative_name(relative)
        path = root / name
        raw = path.read_bytes()
        assert sha(raw) == expected_hashes[name], (name, sha(raw))
        provenance[name] = dict(actual_path=str(path.resolve()), sha256=sha(raw),
                                index="supplement" if name in recovered_hashes else "inherited")
        return raw
    def load(relative):
        return json.loads(read(relative))
    def exact_marker_exists(relative):
        name = relative_name(relative)
        if not (root/name).is_file():
            return False
        read(name)
        return True
    groups, individual, recovered = {}, [], dict(Optimize=0, IIS=0, started=0, returned=0)
    files = sorted((root / old_prefix).rglob("calls.csv"))
    for path in files:
        name = path.relative_to(root).as_posix()
        rows = list(csv.DictReader(io.StringIO(read(name).decode("utf-8-sig"))))
        identities = set()
        for row in rows:
            stage, phase, number = row["stage"], row["phase"], int(row["call"])
            assert stage in ("before", "after")
            identity = (number, phase, stage)
            assert identity not in identities, (name, identity)
            identities.add(identity)
            key = (name, phase)
            group = groups.setdefault(key, dict(started=0, returned=0, native_seconds=0.0))
            if stage == "before":
                group["started"] += 1
                if name in recovered_hashes:
                    recovered["started"] += 1
                    recovered["IIS" if phase == "iis" else "Optimize"] += 1
            else:
                assert (number, phase, "before") in identities, (name, identity)
                group["returned"] += 1
                group["native_seconds"] += float(row["seconds"])
                if name in recovered_hashes:
                    recovered["returned"] += 1
        individual.append(dict(path=name, rows=len(rows), phases=sorted({row["phase"] for row in rows}),
                               sha256=provenance[name]["sha256"]))
    frozen = list(csv.DictReader(io.StringIO(read(old_prefix+"reports02/native_calls.csv").decode("utf-8-sig"))))
    reported_groups = {(row["path"],row["phase"]):row for row in frozen}
    assert groups.keys() == reported_groups.keys()
    for key, group in groups.items():
        report = reported_groups[key]
        assert group["started"] == int(report["started"])
        assert group["returned"] == int(report["returned"])
        assert group["started"]-group["returned"] == int(report["missing_after"])
        assert abs(group["native_seconds"]-float(report["native_seconds"])) < 1e-6
    counts = dict(started=sum(g["started"] for g in groups.values()),
                  returned=sum(g["returned"] for g in groups.values()),
                  Optimize=sum(g["started"] for (path,phase),g in groups.items() if phase != "iis"),
                  IIS=sum(g["started"] for (path,phase),g in groups.items() if phase == "iis"))
    counts["missing_after"] = counts["started"]-counts["returned"]
    assert counts == dict(started=185,returned=184,Optimize=148,IIS=37,missing_after=1)
    assert recovered == dict(Optimize=76,IIS=17,started=93,returned=93)
    summary = json.loads(read(old_prefix+"reports02/summary.json"))
    fee_details = []
    for folder in sorted((root / (old_prefix+"fees")).iterdir()):
        fee_base = folder.relative_to(root).as_posix()+"/"
        launch, receipt = load(fee_base+"launch.json"), load(fee_base+"receipt.json")
        command = launch["command"]
        script = command[1].replace("\\", "/").rsplit("/",1)[-1] if len(command)>1 else ""
        children, method = 0, "outer_only"
        if script == "round105_campaign.py" and command[2] == "prepare":
            identity = load(old_prefix+command[3]+"/identity.json")
            children, method = identity["reference_children"], "frozen_reference_children_declaration"
        elif script == "round105_campaign.py" and command[2] == "run":
            identity = load(old_prefix+command[3]+"/identity.json")
            arm = identity["launches"][int(command[4])-1]
            children = int(exact_marker_exists(arm["destination"]+"/process_start_marker.json"))
            method = "exact_arm_start_marker"
        elif script == "round105_batch.py":
            identity = load(old_prefix+command[2]+"/identity.json")
            children = sum(exact_marker_exists(arm["destination"]+"/process_start_marker.json")
                           for arm in identity["launches"][int(command[3])-1:int(command[4])])
            method = "exact_batch_arm_start_markers"
        elif script == "round105_modes.py" and command[2] == "batch":
            plan = load(command[3])
            for job in plan["jobs"]:
                mode_manifest = load(old_prefix+"modes/"+job["label"]+"/manifest.json")
                mode = mode_manifest["modes"][job["number"]-1]
                children += int(exact_marker_exists(mode["path"]+"/native_launch.json"))
            method = "exact_mode_native_launch_markers"
        elif "review" in command[1]:
            native_execution = load(old_prefix+"review/native_execution.json")
            children, method = native_execution["subprocess_starts"], "frozen_review_subprocess_declaration"
        assert receipt["engineering"] is False
        fee_details.append(dict(label=folder.name,outer_seconds=receipt["outer_seconds"],
                                exit_code=receipt["exit_code"],outer_process_starts=1,
                                nested_process_starts=children,conservative_process_starts=1+children,
                                nested_start_evidence=method))
    fees_frozen = list(csv.DictReader(io.StringIO(read(old_prefix+"reports02/fees.csv").decode("utf-8-sig"))))
    fees_index = {row["label"]:row for row in fees_frozen}
    assert fees_index.keys() == {row["label"] for row in fee_details}
    for fee in fee_details:
        frozen_fee = fees_index[fee["label"]]
        assert abs(fee["outer_seconds"]-float(frozen_fee["outer_seconds"])) < 1e-8
        assert fee["conservative_process_starts"] == int(frozen_fee["conservative_process_starts"])
        assert fee["exit_code"] == int(frozen_fee["exit_code"])
    paid_starts = sum(row["conservative_process_starts"] for row in fee_details)
    paid_outer = sum(row["outer_seconds"] for row in fee_details)
    assert paid_starts == summary["paid_process_starts"] == 55
    assert abs(paid_outer-summary["paid_outer_seconds"]) < 1e-6
    assert abs(paid_outer-12081.441783100076) < 1e-6
    # These two additions are retained summary-level counts. This script
    # independently recounts all R105 calls.csv, not separate P/ENS journal APIs.
    separate = dict(P_ENS=summary["P_ENS_native_Optimize_calls"],
                    previous_independent_review=summary["independent_review_Optimize_starts"])
    assert separate == dict(P_ENS=12,previous_independent_review=3)
    assert counts["Optimize"]+sum(separate.values()) == summary["all_Optimize_starts"] == 163
    assert counts["IIS"] == summary["all_IIS_starts"] == 37
    completion_name = old_prefix+"diagnostic04/raw/01_F5_IR-FULL/completion.json"
    fee_name = old_prefix+"fees/diagnostic_F5_02/receipt.json"
    completion, fee = json.loads(read(completion_name)), json.loads(read(fee_name))
    algorithm, outer = completion["end_to_end_seconds"], fee["outer_seconds"]
    assert abs(algorithm-571.422) < 1e-7 and abs(outer-572.174668) < 1e-7
    receipt_path = root / "restore_receipt.json"
    receipt_raw = receipt_path.read_bytes()
    receipt = json.loads(receipt_raw)
    assert receipt["inherited_archive_sha256"] == manifest["archive_sha256"]
    assert receipt["supplement_manifest_sha256"] == sha(supplement_raw)
    assert receipt["Optimize_calls"] == receipt["IIS_calls"] == 0
    output = dict(status="PASS", reviewer="/root/independent_review", root_absolute_path=str(root),
                  source_absolute_path=str(Path(__file__).resolve()), source_sha256=sha(Path(__file__).read_bytes()),
                  invocation=sys.argv, source_reading_scope="restored root only; no original-tree bytes",
                  manifests=dict(inherited=dict(path=str(manifest_path),sha256=sha(manifest_raw)),
                                 supplement=dict(path=str(supplement_path),sha256=sha(supplement_raw)),
                                 restore_receipt=dict(path=str(receipt_path),sha256=sha(receipt_raw))),
                  raw_R105_call_counts=counts, supplement_counts=recovered,
                  paid_fees=dict(conservative_process_starts=paid_starts,outer_seconds=paid_outer,
                                 receipt_count=len(fee_details),details=fee_details,
                                 scope="outer receipt sums only; nested native seconds not double billed"),
                  retained_summary_level_separate_Optimize_counts=separate,
                  old_compact_incomplete_totals=dict(Optimize=87,IIS=20),
                  restored_combined_totals=dict(Optimize=163,IIS=37),
                  totals_scope="148/37 independently recounted from actual raw R105 calls; 12+3 separate API calls retained at frozen summary level",
                  F5_timing=dict(algorithm_end_to_end_seconds=algorithm,paid_outer_seconds=outer,
                                 completion_source=completion_name,fee_source=fee_name),
                  evidence_provenance=provenance, individual_ledgers=individual,
                  Optimize_calls=0,IIS_calls=0,native_solver_processes=0,subprocess_calls=0)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8",newline="\n") as stream:
        json.dump(output,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(status=output["status"],raw_counts=counts,supplement_counts=recovered,
                          paid_starts=paid_starts,paid_outer_seconds=paid_outer,
                          F5=output["F5_timing"],Optimize_calls=0,IIS_calls=0)))


if __name__ == "__main__":
    main()
