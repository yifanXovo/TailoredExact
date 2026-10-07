"""Independent closed-evidence Round106 admission checks, standard library only.

No project imports, optimization, IIS, test executable, native process or DP.
This verifies source/evidence/binary bindings and raw callback ledgers. It is
not independent model reproduction or performance measurement.
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
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve()
    assert not args.output.exists()
    prefix="results/unified_exact_round106/"
    origins={}
    def raw(name):
        path=root/name
        data=path.read_bytes()
        origins[name]=dict(actual_path=str(path.resolve()),sha256=sha(data))
        return data
    def load(name):
        return json.loads(raw(name))
    def csv_rows(name):
        return list(csv.DictReader(io.StringIO(raw(name).decode("utf-8-sig"))))
    identity=load(prefix+"qualification/identity.json")
    for group in ("source_bindings","tests_SHA","retained_evidence_SHA"):
        for name,expected in identity[group].items():
            assert sha(raw(name)) == expected, (group,name)
    binaries={"production_PE_SHA":"ExactEBRP.exe", "test_PE_SHA":"Round106Tests.exe",
              "research_PE_SHA":"Round106Research.exe"}
    binary_observed={}
    for field,name in binaries.items():
        relative="build/research/round106-events-v1/"+name
        binary_observed[field]=sha(raw(relative))
        assert binary_observed[field] == identity[field], field
    installed={"DLL_SHA":Path("D:/gurobi1302/win64/bin/gurobi130.dll"),
               "header_SHA":Path("D:/gurobi1302/win64/include/gurobi_c.h")}
    for field,path in installed.items():
        observed=sha(path.read_bytes())
        assert observed == identity[field]
        binary_observed[field]=dict(actual_path=str(path),sha256=observed)
    assert identity["no_formal_performance_yet"] is True
    runtime_count=0
    for path in (root/(prefix+"qualification")).rglob("runtime.json"):
        name=path.relative_to(root).as_posix()
        runtime=load(name)
        assert runtime["dll_sha256"] == identity["DLL_SHA"]
        assert runtime["runtime"] == "13.0.2"
        expected=dict(Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,
                      FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
        for key,value in expected.items():
            assert runtime["parameters"][key] == value, (name,key)
        runtime_count+=1
    def vector(name):
        result={}
        for line in raw(name).decode("utf-8-sig").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            variable,value=line.split()
            assert variable not in result
            result[variable]=float(value)
        return result
    lazy_checks=[]
    for case in ("native02/full","native02/core","native02/struct","native02/native_B",
                 "replay01/C2_A","replay01/F2_B","replay01/inner_deadline"):
        base=prefix+"qualification/"+case+"/round106/"
        summary=load(base+"summary.json")
        assert summary["master_calls"] == 1
        events={event["event"]:event for event in
                (json.loads(line) for line in raw(base+"events.jsonl").decode().splitlines())}
        rows=csv_rows(base+"lazy.csv")
        assert len(rows) == summary["lazy_calls"] and rows
        submitted=set()
        for item in rows:
            event_number,row_number=int(item["event"]),int(item["row"])
            row=csv_rows(base+f"row_{row_number}.csv")
            coefficients={entry["variable"]:float(entry["coefficient"]) for entry in row}
            assert len(coefficients) == len(row)
            x=vector(base+f"candidate_{event_number}.sol")
            activity=sum(value*x.get(name,0.0) for name,value in coefficients.items())
            rhs=float(item["rhs"])
            tolerance=max(1e-7,1e-6*max(1,abs(activity),abs(rhs)))
            assert activity-rhs>tolerance
            assert abs(activity-float(item["activity"])) < 1e-8*max(1,abs(activity))
            assert int(item["api_return"]) == 0
            assert bool(int(item["repeat_submission"])) == (row_number in submitted)
            assert row_number in events[event_number]["submitted_lazy_rows"]
            assert events[event_number]["outcome"] == "REJECTED_PROVED_LAZY"
            assert float(item["start_activity"]) <= rhs+1e-7*max(1,abs(rhs),abs(float(item["start_activity"])))
            submitted.add(row_number)
        lazy_checks.append(dict(case=case,master_calls=summary["master_calls"],lazy_calls=len(rows),
                                repeat_submissions=sum(int(item["repeat_submission"]) for item in rows),
                                structural_proofs=summary["structural_proofs"],certified=summary["certified"]))
    native_b=load(prefix+"qualification/native02/native_B/round106/summary.json")
    assert native_b["structural_proofs"] >= 2 and native_b["certified"] is True
    c2_a=load(prefix+"qualification/replay01/C2_A/round106/summary.json")
    c2_lazy=csv_rows(prefix+"qualification/replay01/C2_A/round106/lazy.csv")
    assert any(row["family"] == "A_MST" for row in c2_lazy)
    assert c2_a["events"] > 1 and c2_a["repeat_events"] > 0
    assert any(int(row["repeat_submission"]) for row in c2_lazy)
    tiny=load(prefix+"qualification/native02/contracts/contracts.json")
    large=load(prefix+"qualification/replay01/C2_contracts/contracts.json")
    for data in (tiny,large):
        assert data["Optimize_calls"] == data["IIS_calls"] == data["oracle_calls"] == 0
        for key in ("repeat_INF_resubmitted","repeat_FEAS_not_resubmitted", "nonviolated_row_not_sent",
                    "UNKNOWN_without_rejection_interrupt"):
            assert data[key] is True
    assert tiny["inflated_epigraph_checked"] and tiny["physical_UB_before_native_acceptance"]
    assert large["one_car_reject_other_UNKNOWN"]
    proof=identity["scripted_INF_proof_binding"]
    binding={"candidate_SHA":"candidate_2.sol", "native_ledger_SHA":"inner/calls.csv",
             "native_INF_model_SHA":"event_2_k0/full.lp", "native_INF_log_SHA":"event_2_k0/full.lp.log"}
    proof_base=prefix+"qualification/native02/full/round106/"
    for field,tail in binding.items():
        assert sha(raw(proof_base+tail)) == proof[field]
    assert any(row["phase"] == "oracle" and row["stage"] == "after" and row["status"] == "3"
               for row in csv_rows(proof_base+"inner/calls.csv"))
    deadline_base=prefix+"qualification/replay01/inner_deadline/round106/"
    deadline=load(deadline_base+"summary.json")
    calls=csv_rows(deadline_base+"calls.csv")+csv_rows(deadline_base+"inner/calls.csv")
    assert all(float(row["remaining"])>0 and float(row["process_seconds"])<12
               for row in calls if row["stage"] == "before")
    assert deadline["master_calls"] == deadline["oracle_calls"] == deadline["iis_calls"] == 1
    assert deadline["core_confirmation_calls"] == 0
    assert deadline["inner_cancelled"] and deadline["outer_cancelled"]
    assert 12 <= deadline["inner_termination_seconds"] < 12.05
    assert deadline["inner_termination_seconds"] <= deadline["outer_termination_seconds"] < 12.10
    assert deadline["status"] == "global_deadline_after_valid_rejection"
    assert deadline["LB"] == 0 and abs(deadline["UB"]-0.39162089674952894)<1e-14
    assert not deadline["certified"] and not deadline["unresolved_candidate"]
    assert not deadline["final_native_bound_qualified"]
    inherited=csv_rows(prefix+"qualification/replay01/inherited_native/qualification.csv")
    cases=[row for row in inherited if row["case"].isdigit()]
    assert len(cases) == 21
    assert all((row["enumeration"] == "1") == (row["native_status"] == "0") for row in cases)
    fixed=load(prefix+"fixed_Y/protocol.json")
    math=load(prefix+"review/independent_math_check05.json")
    assert fixed["Y"] == math["C2"]["Y"][1:]
    assert fixed["Ftrue"] == math["C2"]["objective"]["F"]
    assert fixed["input_SHA"] == math["input_sha256"]["R98-C2"]
    assert sha(raw(fixed["input_path"])) == fixed["input_SHA"]
    for name,expected in fixed["source_bindings"].items():
        assert sha(raw(name)) == expected
    assert fixed["cap_seconds"] == 1200 and fixed["reserve_seconds"] == 30
    assert fixed["distinct_historical_candidates"] == fixed["distinct_ownership"] == 4
    assert fixed["distinct_historical_Y"] == 1
    assert fixed["production_handoff"] is False and fixed["no_extension_after_UNKNOWN"] is True
    inventories=list(map(int,raw(prefix+"fixed_Y/inventory.txt").decode().split()))
    assert inventories == fixed["Y"]
    assert fixed["research_PE_SHA"] == identity["research_PE_SHA"]
    assert fixed["production_PE_SHA"] == identity["production_PE_SHA"]
    assert fixed["DLL_SHA"] == identity["DLL_SHA"]
    output=dict(status="PASS",reviewer="/root/independent_review",root_absolute_path=str(root),
                source_absolute_path=str(Path(__file__).resolve()),source_sha256=sha(Path(__file__).read_bytes()),
                invocation=sys.argv,frozen_identity=origins[prefix+"qualification/identity.json"],
                source_bindings_checked=len(identity["source_bindings"]),retained_hashes_checked=len(identity["retained_evidence_SHA"]),
                actual_binaries=binary_observed,runtime_parameter_records_checked=runtime_count,
                lazy_raw_checks=lazy_checks,deadline=deadline,
                scripted_scope="Audited native vectors with injected callback API; 0 Optimize/IIS, not actual native callback observations or new INF proof",
                inherited_native_cases_checked=21,fixed_Y=dict(protocol_sha256=origins[prefix+"fixed_Y/protocol.json"]["sha256"],
                                                               exact_Y_verified=True, cap=1200,reserve=30,production_handoff=False),
                evidence_provenance=origins,Optimize_calls=0,IIS_calls=0,native_solver_processes=0,subprocess_calls=0,
                scope="Independent audit of retained qualification evidence; no independent native model or performance rerun")
    with args.output.open("x",encoding="utf-8",newline="\n") as stream:
        json.dump(output,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(status=output["status"],source_hashes=output["source_bindings_checked"],
                          evidence_hashes=output["retained_hashes_checked"],raw_lazy_rows=sum(row["lazy_calls"] for row in lazy_checks),
                          inner_cancel_seconds=deadline["inner_termination_seconds"],outer_cancel_seconds=deadline["outer_termination_seconds"],
                          Optimize_calls=0,IIS_calls=0)))


if __name__ == "__main__":
    main()
