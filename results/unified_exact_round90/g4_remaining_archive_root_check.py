"""One root package-hash/index check; does not decompress or reread raw files."""
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "results/unified_exact_round90"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


started = time.perf_counter()
index_path = STAGE / "runner_lp_g_g4_remaining_raw_index.json"
assert sha(index_path) == "30df7b9b084f0bc386ee08b6f3394042180a231dd2040e252f342cb3cd54c862"
index = json.loads(index_path.read_text(encoding="utf-8"))
assert index["source_group_count"] == 18 and index["archive_count"] == 30
assert index["source_file_count"] == 80473 and index["source_bytes"] == 540343006
assert index["archive_bytes"] == 70820944
paths, packages = set(), []
raw_bytes = archive_bytes = 0
for group in index["groups"]:
    package = (STAGE / group["archive"]).resolve()
    assert package.is_relative_to((STAGE / "runner_lp_g_g4_remaining_raw_archives").resolve())
    assert package.stat().st_size == group["archive_size"] < 45 * 1024 * 1024
    actual = sha(package)
    assert actual == group["archive_sha256"]
    assert group["stream_verification"] == "all_member_sha256_size_equal_source"
    assert len(group["files"]) == group["source_file_count"] == group["verified_file_count"]
    assert sum(row["size"] for row in group["files"]) == group["source_bytes"] == group["verified_bytes"]
    for row in group["files"]:
        assert row["path"] not in paths
        paths.add(row["path"])
    raw_bytes += group["source_bytes"]
    archive_bytes += group["archive_size"]
    packages.append(dict(path=package.relative_to(ROOT).as_posix(),
                         size_bytes=group["archive_size"], sha256=actual))
assert len(paths) == 80473 and raw_bytes == 540343006 and archive_bytes == 70820944
listed = (STAGE / "runner_lp_g_g4_remaining_git_archive_paths.txt").read_text().splitlines()
assert len(listed) == len(set(listed)) == 30
assert set(listed) == {p["path"] for p in packages}
receipt = dict(schema="round90-g4-remaining-archive-root-check-v1", passed=True,
               index_sha256=sha(index_path), packages_verified=30,
               unique_indexed_files=80473, indexed_raw_bytes=raw_bytes,
               archive_bytes=archive_bytes, additional_decompressions=0,
               raw_files_reread=0, elapsed_seconds=time.perf_counter() - started,
               packages=packages)
with (STAGE / "g4_remaining_archive_root_check.json").open("x", encoding="utf-8") as stream:
    json.dump(receipt, stream, indent=2)
    stream.write("\n")
print(json.dumps({k: v for k, v in receipt.items() if k != "packages"}))
