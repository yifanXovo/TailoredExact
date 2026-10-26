#!/usr/bin/env python3
"""Create deterministic compact and local-raw Round 55 evidence inventories."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


EXCLUDED_INVENTORIES = {
    "compact_evidence_inventory.csv",
    "local_raw_evidence_inventory.csv",
    "final_evidence_inventory.csv",
    "evidence_storage_audit.md",
    "final_evidence_hash_audit.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory(paths: list[Path], root: Path, storage: str) -> list[dict[str, object]]:
    rows = []
    for path in sorted(paths, key=lambda value: value.as_posix()):
        rows.append({
            "path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "storage_class": storage,
            "reproducible": True,
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = ["path", "size_bytes", "sha256", "storage_class", "reproducible"]
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--evidence",
                        default="results/gf_k1_am_sf_station_state_chain_round55")
    args = parser.parse_args()
    root = args.root.resolve()
    evidence = (root / args.evidence).resolve()
    compact_paths = [
        path for path in evidence.iterdir()
        if path.is_file() and path.name not in EXCLUDED_INVENTORIES
    ]
    raw_root = evidence / "local_raw"
    raw_paths = [path for path in raw_root.rglob("*") if path.is_file()]
    compact = inventory(compact_paths, root, "committed_compact")
    local_raw = inventory(raw_paths, root, "local_only_raw")
    write_csv(evidence / "compact_evidence_inventory.csv", compact)
    write_csv(evidence / "local_raw_evidence_inventory.csv", local_raw)
    write_csv(evidence / "final_evidence_inventory.csv", compact + local_raw)
    compact_bytes = sum(int(row["size_bytes"]) for row in compact)
    raw_bytes = sum(int(row["size_bytes"]) for row in local_raw)
    audit = f"""# Evidence storage audit

Round 55 stores mathematical contracts, decisions, proofs, compact CSV/JSON
tables, documentation, and reproduction commands in Git.  Native logs, model
exports, progress traces, and other bulky solver artifacts remain local under
`local_raw/`; every local file is individually inventoried with SHA-256.

- compact committed files inventoried: {len(compact)}
- compact bytes: {compact_bytes}
- local-raw files inventoried: {len(local_raw)}
- local-raw bytes: {raw_bytes}
- temporary working evidence under `tmp/`: excluded from scientific evidence
- inventory self-files: excluded from their own hash set to avoid circularity

The compact tables record executable identity, caps, status, bounds, Work,
time, certificates, and artifact locations.  Raw evidence is reproducible from
the frozen manifests and commands; it is not required in the Git history.
"""
    (evidence / "evidence_storage_audit.md").write_text(audit, encoding="utf-8")
    print(f"compact={len(compact)} raw={len(local_raw)} "
          f"compact_bytes={compact_bytes} raw_bytes={raw_bytes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
