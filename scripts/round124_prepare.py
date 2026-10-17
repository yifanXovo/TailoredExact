"""Select finite, already-published evidence. No solver imports or subprocesses."""
import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

BASE = "fca82e8737183aceb9d5f8950d2f2322393ae6fd"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prior", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    start = time.perf_counter()
    out = args.root / "results/unified_exact_round124"
    auth = out / "authorities"
    auth.mkdir(parents=True, exist_ok=True)
    records = []

    def read(rel):
        p = args.prior / rel
        raw = p.read_bytes()
        records.append({"source": rel, "source_commit": BASE,
                        "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        return raw

    copies = {
        "results/unified_exact_round122/all32_arms.json": "r122_arms.json",
        "results/unified_exact_round122/all48_pairs.json": "r122_pairs.json",
        "results/unified_exact_round122/input_manifest.json": "r122_inputs.json",
        "results/unified_exact_round123/production_identity.json": "production_identity.json",
        "reference/round122_paper_benchmark/PB-C50-S.txt": "PB-C50-S.txt",
    }
    for rel, name in copies.items():
        (auth / name).write_bytes(read(rel))
    core = json.loads(read("results/unified_exact_round123/reconstruction/final/current_core.json"))
    finite = {k: core[k] for k in ["group", "arms", "pairs", "own_fleets", "checkpoints",
              "decision", "PE_SHA", "DLL_SHA", "default_ENS_changed", "observation_clock_contract_SHA"]}
    finite["proof_obligations"] = [{k: v for k, v in ob.items() if k in {
        "arm", "U", "L", "certificate", "full_original_single_call", "qualified_cover",
        "active_cover", "unresolved_leaves", "final_controlling_leaf",
        "own_final_fleet_and_call_domains", "native_calls"}} for ob in core["proof_obligations"]]
    # Native-call rows are finite summaries; exclude verbose embedded matrix/journal evidence.
    for ob in finite["proof_obligations"]:
        if "native_calls" in ob:
            ob["native_calls"] = [{k: v for k, v in c.items() if not isinstance(v, (list, dict))}
                                  for c in ob["native_calls"]]
    (auth / "r123_finite.json").write_text(json.dumps(finite, indent=2) + "\n", encoding="utf-8")
    # Small published CSVs retain actual request counts and scopes without raw expansion.
    for name in ["native_counts.csv", "native_calls.csv", "time_partitions.csv", "covers.csv"]:
        (auth / ("r123_" + name)).write_bytes(read("results/unified_exact_round123/reconstruction/final/" + name))
    bindings = json.loads((auth / "production_identity.json").read_text())["source_bindings"]
    mismatches = []
    for rel, sha in bindings.items():
        p = args.root / rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != sha:
            mismatches.append(rel)
    assert not mismatches, mismatches
    receipt = {"base": BASE, "scope": "finite published table/final-fleet/cover selection; no campaign reconstruction",
               "sources": records, "production_source_bindings_checked": len(bindings),
               "production_source_mismatches": mismatches, "native_processes_started": 0,
               "optimization_calls": 0, "production_compilations": 0,
               "elapsed_seconds": time.perf_counter() - start}
    (out / "source_selection.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources": len(records), "bindings": len(bindings),
                      "selected_bytes": sum(p.stat().st_size for p in auth.iterdir()),
                      "elapsed_seconds": receipt["elapsed_seconds"]}))

if __name__ == "__main__":
    main()
