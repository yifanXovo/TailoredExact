"""Create and verify Git-sized parts of the already validated R94 ZIP."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "results/unified_exact_round94/archive_v4"
SOURCE = DIRECTORY / "round94_full_evidence_v4.zip"
MANIFEST = DIRECTORY / "archive_parts_manifest.json"
EXPECTED_SHA256 = "f16239464f23c80ec146743f6d4b3622022d3509afa304378b1bfe38e393fcb7"
EXPECTED_BYTES = 113_905_614
PART_BYTES = 32 * 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    began = time.perf_counter()
    assert SOURCE.is_file() and SOURCE.stat().st_size == EXPECTED_BYTES
    assert sha256_file(SOURCE) == EXPECTED_SHA256
    assert not MANIFEST.exists(), "never overwrite a parts manifest"
    expected_names = [f"round94_full_evidence_v4.zip.part{i:04d}" for i in range(1, 5)]
    assert all(not (DIRECTORY / name).exists() for name in expected_names), \
        "parts already exist; never retry or overwrite"
    parts = []
    with SOURCE.open("rb") as original:
        for number, name in enumerate(expected_names, 1):
            path = DIRECTORY / name
            digest = hashlib.sha256()
            size = 0
            with path.open("xb") as part:
                while size < PART_BYTES:
                    block = original.read(min(1024 * 1024, PART_BYTES - size))
                    if not block:
                        break
                    part.write(block)
                    digest.update(block)
                    size += len(block)
            assert 0 < size <= PART_BYTES
            parts.append({"number": number, "file": name, "size_bytes": size,
                          "sha256": digest.hexdigest()})
        assert original.read(1) == b"", "unexpected fifth part"
    assert sum(part["size_bytes"] for part in parts) == EXPECTED_BYTES
    reconstructed_hash = hashlib.sha256()
    reconstructed_bytes = 0
    for part in parts:
        path = DIRECTORY / part["file"]
        assert path.stat().st_size == part["size_bytes"]
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
                reconstructed_hash.update(block)
                reconstructed_bytes += len(block)
        assert digest.hexdigest() == part["sha256"]
    assert reconstructed_bytes == EXPECTED_BYTES
    assert reconstructed_hash.hexdigest() == EXPECTED_SHA256
    receipt = {
        "schema": "round94-validated-zip-parts-manifest-v4",
        "source_zip": SOURCE.relative_to(ROOT).as_posix(),
        "source_size_bytes": EXPECTED_BYTES,
        "source_sha256": EXPECTED_SHA256,
        "maximum_part_size_bytes": 40 * 1024 * 1024,
        "actual_chunk_size_bytes": PART_BYTES,
        "parts": parts,
        "streamed_ordered_concat_size_bytes": reconstructed_bytes,
        "streamed_ordered_concat_sha256": reconstructed_hash.hexdigest(),
        "ordered_concat_verified": True,
        "original_zip_and_raw_preserved": True,
        "elapsed_before_manifest_write_seconds": time.perf_counter() - began,
    }
    with MANIFEST.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(receipt, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps({"parts": len(parts), "source_size_bytes": EXPECTED_BYTES,
                      "reconstructed_sha256": reconstructed_hash.hexdigest(),
                      "manifest": MANIFEST.relative_to(ROOT).as_posix()}), flush=True)


if __name__ == "__main__":
    main()
