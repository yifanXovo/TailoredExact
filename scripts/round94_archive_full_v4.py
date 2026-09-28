"""Archive and verify the complete frozen R94 result tree once, without deletion."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import time
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/unified_exact_round94"
ARCHIVE_DIR = RESULTS / "archive_v4"
ZIP = ARCHIVE_DIR / "round94_full_evidence_v4.zip"
MANIFEST = ARCHIVE_DIR / "member_manifest.jsonl"
VERIFICATION = ARCHIVE_DIR / "verification.json"
EXTRAS = (
    "build/research/round90-lp-g-split/ExactEBRP.exe",
    "scripts/round94_archive_full_v4.py",
    "scripts/round94_lpg_contemporary.py",
    "scripts/round94_lpg_formal_recovery_v3.py",
    "scripts/round94_lpg_formal_recovery_v4.py",
    "scripts/round90_lp_g_d6_tail.py",
    "scripts/round90_lp_g_g3.py",
    "scripts/round88_a1_g3.py",
    "scripts/round86_native_evidence.py",
    "reference/round86_unadapted_confirmation/F2.txt",
    "reference/citibike443-regional-v1/instances/V20/cb443_V20_compact_r2_shortage_M02_Q20.txt",
    "reference/citibike443-regional-v1/instances/V50/cb443_V50_regional_r1_balanced_M04_Q30.txt",
    "reference/round82_unadapted_confirmation/U6.txt",
    "research_plans/ensc_optimization_instances_2026-09-26.json",
    "results/unified_exact_round87/campaign/identity.json",
)


def sha256_stream(stream) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    with path.open("rb") as source:
        return sha256_stream(source)


def write_new(path: Path, obj) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(obj, output, ensure_ascii=False, indent=2)
        output.write("\n")


def assert_expected_evidence(paths: set[str]) -> None:
    def has(relative: str) -> bool:
        return relative in paths

    mandatory = (
        "results/unified_exact_round94/final_report.md",
        "results/unified_exact_round94/formal_results_v4_report.md",
        "results/unified_exact_round94/formal_evidence_summary_v4.json",
        "results/unified_exact_round94/independent_final_review.md",
        "results/unified_exact_round94/formal_outer_receipt_v2.json",
        "results/unified_exact_round94/formal_recovery_run_outer_v4.json",
        "results/unified_exact_round94/runner_lpg_contemporary/recovery_v2/formal_completion.json",
        "results/unified_exact_round94/runner_lpg_contemporary/formal_recovery_v3/preflight.json",
        "results/unified_exact_round94/runner_lpg_contemporary/formal_recovery_v4/formal_completion.json",
        "results/unified_exact_round94/runner_lpg_contemporary/qualification_failure_01.json",
        "results/unified_exact_round94/runner_lpg_contemporary/recovery_v2/qualification_completion.json",
        "build/research/round90-lp-g-split/ExactEBRP.exe",
    )
    assert all(has(path) for path in mandatory), "missing a required evidence member"
    identity = json.loads(
        (RESULTS / "runner_lpg_contemporary/formal_recovery_v4/identity.json").read_text(encoding="utf-8")
    )
    for launch in identity["original_formal_launches"]:
        relative = Path(launch["destination"]).relative_to(ROOT).as_posix()
        if launch["arm"] == "P-GRB":
            assert has(f"{relative}/compact.lp"), f"missing original compact LP: {relative}"
        else:
            assert any(path.startswith(f"{relative}/external/models/") and path.endswith(".lp")
                       for path in paths), f"missing original external LPs: {relative}"
        assert has(f"{relative}/completion.json"), f"missing completion: {relative}"
        assert any(path.startswith(f"{relative}/journal/") for path in paths), \
            f"missing native journal: {relative}"
    qualification = RESULTS / "runner_lpg_contemporary/qualification"
    assert len([path for path in qualification.iterdir() if path.is_dir()]) == 4
    for path in qualification.iterdir():
        if path.is_dir():
            relative = path.relative_to(ROOT).as_posix()
            assert has(f"{relative}/compact.lp")
            assert any(name.startswith(f"{relative}/journal/") for name in paths)


def list_members() -> list[Path]:
    files = []
    for directory, dirs, names in os.walk(RESULTS, topdown=True, followlinks=False):
        base = Path(directory)
        dirs[:] = sorted(name for name in dirs if base / name != ARCHIVE_DIR)
        for name in sorted(names):
            files.append(base / name)
    files.extend(ROOT / relative for relative in EXTRAS)
    files.sort(key=lambda path: path.relative_to(ROOT).as_posix())
    relative = [path.relative_to(ROOT).as_posix() for path in files]
    assert len(relative) == len(set(relative)), "duplicate archive member"
    for path in files:
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode), f"non-regular member: {path}"
        assert not path.is_symlink(), f"symlink member: {path}"
    assert_expected_evidence(set(relative))
    return files


def main() -> None:
    began = time.perf_counter()
    assert not ARCHIVE_DIR.exists(), "archive output already exists; never overwrite or retry"
    assert not ZIP.exists() and not MANIFEST.exists() and not VERIFICATION.exists()
    files = list_members()
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=False)
    rows = []
    with MANIFEST.open("x", encoding="utf-8", newline="\n") as manifest:
        for path in files:
            before = path.stat()
            size = before.st_size
            digest = sha256_file(path)
            after = path.stat()
            assert (after.st_size, after.st_mtime_ns) == (size, before.st_mtime_ns), \
                f"source changed while hashing: {path}"
            row = {"path": path.relative_to(ROOT).as_posix(), "size_bytes": size,
                   "sha256": digest}
            manifest.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            rows.append(row)
    manifest_seconds = time.perf_counter() - began
    with zipfile.ZipFile(ZIP, "x", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=3, allowZip64=True) as archive:
        for path, row in zip(files, rows):
            archive.write(path, arcname=row["path"])
    creation_seconds = time.perf_counter() - began - manifest_seconds
    with zipfile.ZipFile(ZIP, "r", allowZip64=True) as archive:
        infos = archive.infolist()
        assert len(infos) == len(rows), "archive member count differs"
        for info, expected in zip(infos, rows):
            assert info.filename == expected["path"], "archive path/order mismatch"
            assert info.file_size == expected["size_bytes"], f"archive size mismatch: {info.filename}"
            with archive.open(info, "r") as member:
                assert sha256_stream(member) == expected["sha256"], \
                    f"archive SHA mismatch: {info.filename}"
    verification_seconds = time.perf_counter() - began - manifest_seconds - creation_seconds
    result = {
        "schema": "round94-full-evidence-archive-verification-v4",
        "archive_path": ZIP.relative_to(ROOT).as_posix(),
        "archive_size_bytes": ZIP.stat().st_size,
        "archive_sha256": sha256_file(ZIP),
        "manifest_path": MANIFEST.relative_to(ROOT).as_posix(),
        "manifest_sha256": sha256_file(MANIFEST),
        "member_count": len(rows),
        "uncompressed_bytes": sum(row["size_bytes"] for row in rows),
        "all_members_path_size_sha256_verified": True,
        "zip_crc_checked_while_streaming_each_member": True,
        "original_files_preserved": True,
        "manifest_seconds_before_archive": manifest_seconds,
        "archive_creation_seconds": creation_seconds,
        "member_verification_seconds_before_final_receipt": verification_seconds,
        "elapsed_before_verification_receipt_seconds": time.perf_counter() - began,
        "excluded_output_directory": ARCHIVE_DIR.relative_to(ROOT).as_posix(),
    }
    write_new(VERIFICATION, result)
    print(json.dumps({key: result[key] for key in (
        "archive_path", "archive_size_bytes", "archive_sha256", "member_count",
        "uncompressed_bytes", "all_members_path_size_sha256_verified")}), flush=True)


if __name__ == "__main__":
    main()
