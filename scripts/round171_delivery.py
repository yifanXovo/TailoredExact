"""New-evidence carrier, anonymous recovery and bounded closeout."""

import argparse
import concurrent.futures
import csv
import gzip
import io
from pathlib import Path
import re
import shutil
import time
import urllib.parse
import urllib.request
import zipfile

from round170_common import protected
from round171_common import (
    BASE, DLL, DLL_SHA, MASTER, MEASURED, OUT, PE, PE_SHA, REL, ROOT, SCIENCE_CAP, TEMP, WORK,
    bind, blob, clock, digest, git, read, sha, utc, write,
)

SECRET = re.compile(
    rb"(?i)(?:WLSSECRET|WLSACCESSID|CSAPIAccessID|CSAPISecret|AWS_SECRET_ACCESS_KEY|"
    rb"OPENAI_API_KEY|GH_TOKEN|GITHUB_TOKEN|GRB_LICENSE_FILE)\s*(?:to value|[:=])\s*\S+"
)
MAX_PUBLIC_GIT_BYTES = 90 * 1024 * 1024


def verify_member_map(archive, records):
    with zipfile.ZipFile(archive) as carrier:
        names = {item.filename for item in carrier.infolist()}
        assert len(names) == len(carrier.infolist()) == len(records)
        assert names == {r["member"] for r in records}
        for record in records:
            member = Path(record["member"])
            assert not member.is_absolute() and ".." not in member.parts
            raw = carrier.read(record["member"])
            assert len(raw) == int(record["bytes"]) and digest(raw) == record["SHA256"], record["member"]


def package():
    start = time.perf_counter()
    target = OUT / "artifacts"
    target.mkdir(exist_ok=True)
    archive = target / "round171_new_raw.zip"
    index = target / "round171_new_raw_members.csv.gz"
    assert not archive.exists(), "Preserve the previously sealed archive"
    roots = (OUT / "complete_raw", OUT / "qualification/references", OUT / "qualification/export_logs",
             OUT / "review/attempt_logs")
    entries = [file for parent in roots for file in sorted(parent.rglob("*")) if file.is_file()]
    assert len(read(OUT / "complete_arms.json")["rows"]) == 12 and entries
    records = []
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as carrier:
        for path in entries:
            member = path.relative_to(OUT).as_posix()
            assert path.suffix.lower() not in (".dll", ".lic", ".exe", ".key", ".pem")
            assert not any(token in path.name.lower() for token in ("license", "credential", "secret"))
            raw = path.read_bytes()
            assert not SECRET.search(raw), f"Credential-like data in {member}; review locally"
            carrier.writestr(member, raw)
            records.append(dict(member=member, bytes=len(raw), SHA256=digest(raw)))
    assert archive.stat().st_size < MAX_PUBLIC_GIT_BYTES, "Split by producer position before publication"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=("member", "bytes", "SHA256"))
    writer.writeheader()
    writer.writerows(records)
    index.write_bytes(gzip.compress(stream.getvalue().encode("utf-8"), mtime=0))
    verify_member_map(archive, records)
    write(OUT / "evidence_archives.json", dict(
        UTC=utc(), new_only=True, carrier=bind(archive), membermap=bind(index), members=len(records),
        raw_uncompressed_bytes=sum(row["bytes"] for row in records), all_local_member_bytes_verified=True,
        includes_12_producers=True, includes_six_zero_Optimize_references=True, commercial_DLL_licenses_credentials_included=False,
        inherited_PE=dict(commit="b86cef9917a9fd526ca89bcbdad4b667008c7eab", bytes=PE.stat().st_size,
                          archive="results/unified_exact_round169/artifacts/round169_new_raw_and_runtime.zip",
                          member="runtime/ExactEBRP.exe", SHA256=PE_SHA),
        measured_CPP=MEASURED, inherited_DLL_SHA256=DLL_SHA, packaging_seconds=time.perf_counter() - start,
        restore="Place the archive members under results/unified_exact_round171 in an empty recovery root.",
    ))
    print(f"Sealed {len(records)} members into {archive.stat().st_size:,} bytes", flush=True)


def recover(science):
    start = time.perf_counter()
    destination = WORK / "recovery" / f"round171-public-{science[:12]}"
    if destination.exists():
        suffix = 2
        while destination.with_name(destination.name + f"-{suffix}").exists():
            suffix += 1
        destination = destination.with_name(destination.name + f"-{suffix}")
    destination.mkdir(parents=True, exist_ok=False)
    paths = git("diff", "--name-only", BASE, science).splitlines()
    expected = {}
    for name in paths:
        raw = blob(science, name)
        expected[name] = (len(raw), digest(raw))
        assert sha(ROOT / name) == expected[name][1], name
    fetch_start = time.perf_counter()

    def retrieve(item):
        name, (size, expected_hash) = item
        began = time.perf_counter()
        relative = urllib.parse.quote(name, safe="/")
        url = f"https://raw.githubusercontent.com/yifanXovo/TailoredExact/{science}/{relative}"
        headers = {"User-Agent": "TailoredExact-R171-public-byte-recovery"}
        request = urllib.request.Request(url, headers=headers)
        last = None
        for _ in range(3):
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    body = response.read()
                assert len(body) == size and digest(body) == expected_hash, name
                break
            except (TimeoutError, OSError) as error:
                last = error
        else:
            raise last
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        assert sha(path) == expected_hash
        return dict(path=name, bytes=size, SHA256=expected_hash, elapsed_seconds=time.perf_counter() - began,
                    anonymous_HTTPS=True, bytes_equal=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        files = list(executor.map(retrieve, expected.items()))
    fetched = time.perf_counter() - fetch_start
    manifest = read(destination / REL / "evidence_archives.json")
    archive_path = destination / manifest["carrier"]["path"]
    member_map_path = destination / manifest["membermap"]["path"]
    members = list(csv.DictReader(io.StringIO(gzip.decompress(member_map_path.read_bytes()).decode("utf-8"))))
    assert len(members) == manifest["members"]
    verify_member_map(archive_path, members)
    csv_bytes = (destination / MASTER.relative_to(ROOT)).read_bytes()
    recon = read(destination / REL / "CSV_reconciliation.json")
    assert digest(csv_bytes) == recon["master"]["SHA256"]
    assert digest(csv_bytes[:recon["baseline_bytes"]]) == recon["baseline_SHA256"]
    receipt = dict(
        UTC=utc(), PASS=True, scientific_commit=science, downloaded_files=len(files), verified_member_count=len(members),
        verified_bytes=sum(row["bytes"] for row in files), public_master_SHA256=digest(csv_bytes),
        master_PREFIX_SHA256=recon["baseline_SHA256"], file_bindings=files, empty_root=str(destination),
        anonymous_HTTPS=True, all_new_member_bytes_verified=True, old_raw_recovery=False,
        public_transfer_seconds=fetched, total_public_verification_seconds=time.perf_counter() - start,
    )
    write(OUT / "public_recovery.json", receipt)
    write(destination / "recovery_receipt.json", receipt)
    print(f"Verified public bytes for {len(files)} files and {len(members)} raw members", flush=True)


def scientific_close():
    arms = read(OUT / "complete_arms.json")
    costs = read(OUT / "cost_report.json")
    csv_audit = read(OUT / "CSV_QA.json")
    pdf = read(OUT / "document_qa.json")
    reviews = [bind(OUT / "review" / f"{slot}_review_final.json")
               for slot in ("math", "execution", "research")]
    assert arms["qualified"] == 12 and costs["H_calls"] == 6
    assert costs["process_outer_seconds"] <= 14_400 and costs["qualification_outer_seconds"] <= 600
    assert pdf["status"] == "PASS" and csv_audit["PASS"]
    assert all(sha(ROOT / value["file"]["path"]) == value["file"]["SHA256"] for value in pdf["documents"])
    assert all(read(ROOT / row["path"])["status"] == "PASS" for row in reviews)
    before = read(TEMP / "protected_trees.json")
    after = protected()
    assert before == after, "Protected tracked status or dirty file bytes changed; inspect without overwriting"
    write(OUT / "protected_tree_check.json", dict(UTC=utc(), PASS=True, protected_roots=[
        dict(root=value["root"], HEAD=value["HEAD"], dirty_file_count=len(value["files"])) for value in after
    ], tracked_status_and_dirty_bytes_equal=True))
    assert sha(PE) == PE_SHA and sha(DLL) == DLL_SHA
    assert all(sha(ROOT / path) == value for path, value in read(OUT / "candidate_manifest.json")["source_hashes"].items())
    marker = clock()
    assert marker["occupied_conservative_seconds"] <= SCIENCE_CAP
    costs.update(clock=marker, independent_final_reviews=reviews)
    write(OUT / "cost_report.json", costs)
    write(OUT / "science_close.json", dict(
        UTC=utc(), clock=marker, scientific_objective_achieved=True, positions=arms["qualified"],
        independent_final_reviews=reviews, CSV_QA=bind(OUT / "CSV_QA.json"), visual_QA=bind(OUT / "document_qa.json"),
        B_default=True, C166_D167_C169_off=True, no_new_round_started=True,
    ))
    print(f"Scientific closeout at {marker['occupied_conservative_seconds']:.2f}s", flush=True)


def cleanup():
    receipt = read(OUT / "public_recovery.json")
    assert receipt["PASS"] and receipt["all_new_member_bytes_verified"]
    free_before = shutil.disk_usage(WORK).free
    materials = []
    for directory in (OUT, TEMP, Path(receipt["empty_root"])):
        paths = [p for p in directory.rglob("*") if p.is_file()]
        materials.append(dict(path=str(directory), files=len(paths), logical_bytes=sum(p.stat().st_size for p in paths),
                              retained=True))
    free_after = shutil.disk_usage(WORK).free
    write(OUT / "cleanup_record.json", dict(
        UTC=utc(), mode="bounded metadata check; zero deletions", verified_recoverable_new_round_only=True,
        retained=materials, deletion_count=0, deletion_bytes=0, volume_free_before=free_before,
        volume_free_after=free_after, observed_free_delta=free_after-free_before,
        reason="The current tree, raw evidence, reader attempts, PDFs and fresh recovery support active delivery.",
    ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["package", "recover", "scientific-close", "cleanup"])
    parser.add_argument("science", nargs="?")
    args = parser.parse_args()
    if args.stage == "recover":
        recover(args.science)
    else:
        {"package": package, "scientific-close": scientific_close, "cleanup": cleanup}[args.stage]()
