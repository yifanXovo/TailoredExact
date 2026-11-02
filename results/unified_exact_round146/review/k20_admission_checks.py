"""Independent K20 admission: read existing evidence only; no solver imports."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "results/unified_exact_round146"
def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

manifest = read(OUT / "candidate_manifest.json")
matrix = read(OUT / "k20_matrix.json")
assert manifest["source_commit"] == "1f470aa5d6a8289347b9d4323764e6e74fa83b2b"
assert manifest["compiled_units"] == ["GurobiBaseline", "PaperExternalGiniTree", "main"]
assert sha(manifest["production_PE"]) == manifest["production_PE_SHA"]
assert sha(manifest["DLL"]) == manifest["DLL_SHA"]
for p, digest in manifest["source_hashes"].items():
    assert sha(ROOT / p) == digest, p
for p, digest in manifest["objects"].items():
    assert sha(p) == digest, p
assert sha(manifest["main_object"]["path"]) == manifest["main_object"]["SHA"]
assert matrix["candidate_manifest_SHA"] == sha(OUT / "candidate_manifest.json")
for p, digest in matrix["helpers"].items():
    assert sha(ROOT / p) == digest, p
assert matrix["serial"] and matrix["threads"] == 1 and matrix["affinity_mask"] == 4
assert matrix["all_own_H"] and matrix["H_seed"] == 20260626 and matrix["Seed_default"] == 0
assert matrix["new_nominal_caps"] == 2400 and len(matrix["groups"]) == 2
normalized = []
for group, method, flag in zip(matrix["groups"], ["STOCK", "STOCK_GD"], ["off", "on"]):
    l = group["launch"]
    assert l["id"] == "K-20-S" and l["R146_method"] == method and l["cap_seconds"] == 1200
    assert l["seed"] == 0 and l["AM_threshold"] == .08
    assert l["panel"]["V"] == 20 and l["panel"]["M"] == 2
    assert l["panel"]["T_seconds"] == 5400 and l["panel"]["lambda"] == .15
    assert l["panel"]["round138_stock_rlt"]
    assert sha(ROOT / l["panel"]["input_path"]) == l["panel"]["input_sha256"]
    identity_path = OUT / group["group"] / "identity.json"
    assert sha(identity_path) == group["identity_SHA"]
    identity = read(identity_path)
    assert identity["launches"] == [l] and identity["no_cross_arm_information"]
    assert identity["candidate_binary_sha256"] == manifest["production_PE_SHA"]
    assert identity["candidate_manifest_SHA"] == matrix["candidate_manifest_SHA"]
    assert identity["measured_source_commit"] == manifest["source_commit"]
    assert not Path(l["destination"]).exists(), "K20 must not already have entered"
    c = l["command"]
    assert c[0] == manifest["production_PE"] and c.count("--round138-stock-rlt") == 1
    for name, value in [("--threads", "1"), ("--mip-threads", "1"), ("--gurobi-seed", "0"),
                        ("--round146-gd", flag), ("--round127-mode", "ms2"),
                        ("--time-limit", "1194"), ("--process-wall-time-limit", "1200")]:
        assert c[c.index(name)+1] == value
    normalized.append([v.replace(l["destination"], "<ARM>") for v in c])
    normalized[-1][c.index("--round146-gd")+1] = "<GD_FLAG>"
assert normalized[0] == normalized[1], "Only GD and output destinations may differ"

exact = read(OUT / "qualification_exact_rows.json")
native = read(OUT / "qualification_native_writer.json")
writer = read(OUT / "qualification/writer/cpp_receipt.json")
assert exact["PASS"] and len(exact["facts"]) == 8 and exact["Optimize"] == exact["Native_load"] == 0
assert all(f["all_exact"] for f in exact["facts"])
assert native["PASS"] and native["Optimize"] == 0 and native["actual_off_K35_equals_historical_BASE"]
assert native["Native"]["sha256"] == manifest["DLL_SHA"]
assert writer["PASS"] and writer["checks"] == 14 and writer["Optimize"] == writer["Native_load"] == 0
assert any(f.get("model") == "child_on" and f["Native_readback"] for f in native["facts"])
assert sum(f.get("point") == "nonminimal_epigraph" for f in native["facts"]) == 3

qm = read(OUT / "qualification_matrix.json")
health_dir = Path(qm["groups"][0]["launch"]["destination"])
audit = read(health_dir / "audit.json")
closeout = read(health_dir / "verification_closeout.json")
gd = read(health_dir / "round146_control_audit.json")
assert audit["passed"] and audit["implementation_qualified"] and audit["evidence_complete"]
assert audit["full_H"]["complete"] and len(audit["full_H"]["seed_ids"]) == 25
assert audit["raw_tree_lifecycle_complete"] and audit["raw_bytes_unchanged"]
assert len(audit["Optimize_return_sequences"]) == len(audit["qualified_return_sequences"]) == 5
assert len(audit["Start_checks"]) == 2
assert max(x["maximum_absolute_residual"] for x in audit["Start_checks"]) < 1e-6
assert closeout["necessary_verification_complete"] and closeout["native_proof_qualified"]
assert closeout["audit_SHA"] == sha(health_dir / "audit.json")
assert audit["endpoint"]["PE_SHA"] == manifest["production_PE_SHA"]
assert audit["endpoint"]["source_commit"] == manifest["source_commit"]
assert not audit["endpoint"]["formal_performance"] and not audit["endpoint"]["certificate"]
assert gd["PASS"] and len(gd["Native_audits"]) == 5
assert all(x["PASS"] and x["GD_rows"] == 2 and x["GD_nonzeros"] == 330 and
           x["source_solves"] == x["new_columns"] == x["Optimize_extra"] == 0 for x in gd["Native_audits"])

lp = []
for p in sorted((OUT / "LP").glob("*/result.json")):
    r = read(p)
    assert r["qualified"] and r["LP_Optimize"] == 1 and r["gain"] > 0
    assert r["complete_objective_constants_old_matrix_support_bounds_cutoff_retained"]
    assert r["actual_Native_GD_readback"] and r["row_header_SHA"] == manifest["source_hashes"]["include/Round146Research.hpp"]
    assert r["Seed"] == 0 and r["Threads"] == 1 and max(r["quality"].values()) <= 1e-6
    assert sha(p.parent / "model.mps") == r["model_SHA"]
    baseline = r["baseline_reused"]
    assert baseline["baseline_Optimize_new"] == 0
    for field in ["result", "solution", "matrix"]:
        assert sha(ROOT / baseline[field]) == baseline[field + "_SHA"]
    assert read(ROOT / baseline["result"])["L"] == r["old_L"]
    assert abs(r["L"] - r["g"] - r["weighted_penalty"]) < 1e-12
    lp.append({k:r[k] for k in ["role","carrier","old_L","L","gain","coefficient_generation_seconds"]})
assert len(lp) == 5
assert {(r["role"], r["carrier"]) for r in lp} == {
    ("K-20-S","base"),("K-20-S","joint"),("K-20-S","stock"),
    ("K-35-U","base"),("R-X20-S-T1","base")}

fees = []
for folder in (OUT / "fees").iterdir():
    assert (folder / "receipt.json").exists(), folder
    fee = read(folder / "receipt.json")
    assert fee["exit_code"] == 0 and not fee["timeout"] and fee["exit_observed"]
    assert fee["nested_H_LP_MIP_not_added"]
    fees.append(fee)
fees.sort(key=lambda f:f["start_unix"])
assert all(a["end_unix"] <= b["start_unix"] for a,b in zip(fees,fees[1:]))
paid = sum(f["G1_seconds"] for f in fees)
assert abs(paid - read(OUT / "qualification_run_return.json")["budget"]["G1_seconds"]) < 1e-9
assert paid + matrix["new_nominal_caps"] + 3000 < 28800

amendment = read(OUT / "engineering/reader_amendment.json")
assert amendment["new_reader_SHA"] == sha(ROOT / "scripts/round146_read.py")
assert amendment["new_frozen_k20_matrix_SHA"] == sha(OUT / "k20_matrix.json")
assert amendment["Optimize"] == amendment["Native_load"] == amendment["compile"] == 0
key = lambda name:int(re.search(r"_generation_(\d+)_round146_GD\.lp$",name).group(1))
synthetic = ["L0.0_epoch_2_generation_3_round146_GD.lp", "L0_epoch_1_generation_1_round146_GD.lp", "L0_epoch_2_generation_10_round146_GD.lp"]
assert sorted(synthetic,key=key)[0] == synthetic[1]

result = dict(decision="ACCEPT", independent_nonimplementer_review=True,
    reviewer="gd_independent_review", UTC=datetime.now(timezone.utc).isoformat(),
    matrix_SHA=sha(OUT / "k20_matrix.json"), candidate_manifest_SHA=sha(OUT / "candidate_manifest.json"),
    source_commit=manifest["source_commit"], production_PE_SHA=manifest["production_PE_SHA"],
    reader_SHA=sha(ROOT / "scripts/round146_read.py"), Optimize=0, Native_load=0, compile=0,
    admitted_scope="Only registered same-PE K20 STOCK / STOCK_GD Seed0 cap1200 pair; no other full role admitted",
    rationale="Five qualified matched LP gains, stronger K20 STOCK+GD signal, actual writer/Start/scope/Native qualification and one complete health pass justify a finite strong-reference test, not promotion",
    fixed_finding="Reader now selects first global numeric artifact generation; old qualification helper and pre-admission matrix preserved; no producer rerun",
    health_U=audit["endpoint"]["U"],health_L=audit["endpoint"]["L"],health_Native_returns=5,
    experimental_outer_seconds_before_K20=paid, new_nominal_caps=2400,
    remaining_experimental_seconds_before_K20=28800-paid,
    source_files_checked=len(manifest["source_hashes"]),helper_files_checked=len(matrix["helpers"]),
    LP=lp, evidence_SHA={name:sha(OUT/name) for name in ["qualification_exact_rows.json","qualification_native_writer.json","qualification/writer/cpp_receipt.json","qualification_run_return.json"]})
(OUT / "review/k20_admission.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:result[k] for k in ["decision","matrix_SHA","production_PE_SHA","experimental_outer_seconds_before_K20","new_nominal_caps"]},indent=2))
