"""Read-only qualification of returned Round171 arms using the inherited contracts."""

import argparse
import inspect
import math
from pathlib import Path

import round170_audit as inherited
from round170_common import result
from round171_common import CAP, DLL_SHA, MARGIN, OUT, PE_SHA, ROOT, bind, read, sha, utc, write

old = inherited.old
core, proof = inherited.core, inherited.proof
TOL = inherited.TOL


def adapt(function, replacements, **namespace):
    """Bind the prior evidence readers to the new matrix, retaining their checks."""
    source = inspect.getsource(function)
    for before, after in replacements:
        assert before in source, before
        source = source.replace(before, after)
    globals_ = dict(function.__globals__, ROOT=ROOT, OUT=OUT, **namespace)
    exec(compile(source, f"{__file__}::{function.__name__}", "exec"), globals_)
    return globals_[function.__name__]


TAILORED = adapt(old.audit, [
    ("matrix_execution_frozen.json", "matrix_frozen.json"),
    ("h_panel_frozen.json", "input_manifest.json"),
    ("p=dict(p,cap_seconds=registered['cap'])",
     "p=dict(p,cap_seconds=registered['cap'],reference=registered['original_compact_reference'])"),
    ("version='candidate',seed=0", "version='candidate',seed=registered['Native_Seed']"),
    ("registered['cap']+2", "registered['cap']"),
    ("round169-independent-new-runner-postreturn-audit-v1", "round171-qualified-tailored-postreturn-audit-v1"),
])

PLAIN = adapt(inherited.plain, [
    ("registered['cap']+2", "registered['cap']"),
    ("r['nominal_process_wall_budget_seconds']==600", "r['nominal_process_wall_budget_seconds']==registered['cap']"),
    ("inputs_frozen.json", "input_manifest.json"),
    ("cap_seconds=600,reference=p['compact_reference']['metadata']",
     "cap_seconds=registered['cap'],reference=registered['original_compact_reference']"),
    ("cap_seconds=600,panel=p", "cap_seconds=registered['cap'],panel=p"),
    ("phase=old.phases(d,600);physical=core.full_fleet(ROOT,p,r)\n    assert abs(physical['F']-r['upper_bound'])<TOL",
     """phase=old.phases(d,registered['cap'])
    if r['verified_incumbent_objective_available']:
        physical=core.full_fleet(ROOT,p,r)
        assert abs(physical['F']-r['upper_bound'])<TOL
    else:
        assert r['gurobi_solution_count']==0 and not js['witnesses'], 'unqualified physical return with a native incumbent'
        physical=None"""),
    ("emitter,physical['F']", "emitter,physical['F'] if physical else None"),
    ("""own=js['witnesses']+[dict(physical,source='actual_R170_return_result',input_SHA=p['input_sha256'],
            physical_verified=True,available=completion['process_outer_seconds'])]""",
     """own=list(js['witnesses'])
        if physical:
            own.append(dict(physical,source='actual_R171_return_result',input_SHA=p['input_sha256'],
                physical_verified=True,available=completion['process_outer_seconds']))"""),
    ("""with call_logs.activate(view),proof.strict_bound_context():
            final=core.cold_returned_bound(ROOT,d,legacy,r)
        lower=max([0.,final['L']]+[b['global_bound'] for b in legacy['bounds'] if b['global_available']])
        upper=physical['F'];certificate=r['gurobi_status']==2 and upper-lower<=TOL
        assert abs(lower-r['lower_bound'])<=TOL and lower<=upper+TOL""",
     """with call_logs.activate(view),proof.strict_bound_context():
            final=core.cold_returned_bound(ROOT,d,legacy,r) if r['native_mip_best_bound_available'] else None
        bounds=[b['global_bound'] for b in legacy['bounds'] if b['global_available']]
        if final:
            bounds.append(final['L'])
        lower=max(0.,max(bounds)) if bounds else None
        upper=physical['F'] if physical else None
        certificate=bool(r['gurobi_status']==2 and upper is not None and lower is not None and upper-lower<=TOL)
        if lower is not None:
            assert abs(lower-r['lower_bound'])<=TOL
            assert upper is None or lower<=upper+TOL"""),
    ("absolute_gap=upper-lower,relative_gap=(upper-lower)/max(abs(upper),1e-12)", 
     """absolute_gap=upper-lower if upper is not None and lower is not None else None,
            relative_gap=(upper-lower)/max(abs(upper),1e-12) if upper is not None and lower is not None else None"""),
    ("round170-qualified-cold-P-postreturn-audit-v1", "round171-qualified-cold-P-postreturn-audit-v1"),
], PE_SHA=PE_SHA, DLL_SHA=DLL_SHA)


def initial_bound(audit, panel, journal):
    if audit["research_arm"] == "P":
        return None
    first = journal.get(1)
    if first is None:
        return None
    own_U = audit["full_paid_H"]["selected"]["original_F"]
    root_proofs = [row for row in audit["qualified_cover"]["scoped_proofs"]
                   if row["call"] == 1 and row["source"] == "actual_optimal_complete_original_LP_relaxation"]
    if not root_proofs:
        return None
    assert len(root_proofs) == 1
    root = root_proofs[0]
    cutoff = root["cutoff"]
    gmax = (panel["V"] - 1) / panel["V"]
    assert first["cutoff"] == cutoff and root["lo"] == first["lower_g"] and root["hi"] == first["upper_g"]
    if root["lo"] > 0 or root["hi"] + 1e-12 < min(cutoff, gmax) or cutoff + TOL < own_U:
        return None
    lower = min(root["L"], cutoff)
    assert 0 <= lower <= own_U + TOL
    return dict(L=lower, raw_LP_value=root["L"], call=1, G_scope=[root["lo"], root["hi"]],
                verified_cutoff=cutoff, proof_sequence=root["sequence"],
                complement="F >= cutoff outside the improving domain (F >= G and qualified root coverage)",
                qualified_original_global_L=True)


def audit_position(number):
    matrix = read(OUT / "matrix_frozen.json")
    registered = matrix["positions"][number - 1]
    assert registered["position"] == number and registered["Native_Seed"] == 0
    directory = Path(registered["directory"])
    invocation = read(directory / "invocation.json")
    completion = read(directory / "completion.json")
    assert invocation["matrix_SHA256"] == sha(OUT / "matrix_frozen.json")
    assert invocation["PE"]["SHA256"] == PE_SHA and invocation["DLL"]["SHA256"] == DLL_SHA
    assert completion["affinity"]["set_success"] and completion["process_outer_seconds"] <= CAP
    panel = next(row for row in read(OUT / "input_manifest.json")["roles"] if row["id"] == registered["role"])
    assert sha(ROOT / panel["input_path"]) == registered["input_SHA256"] == panel["input_sha256"]

    if registered["arm"] == "P":
        value = PLAIN(number)
    else:
        value = TAILORED(number)
        h = value["full_paid_H"]
        assert h["complete_arm_initialization"] and h["selection"]["mode"] == "off"
        assert h["expected_arm_calls"] == 1 and h["selected"]["effective_seed"] == 20260626
        assert h["selected"]["search_lambda"] == panel["lambda"] and h["selected"]["seed_ids"] == list(range(1, 26))
        trace = read(directory / "primal/base/path.json")
        assert all(trace[name] for name in ("valid", "joint_complete", "descent_complete", "closure_complete"))
        assert not trace["qualified_zero"] and trace["input_SHA256"] == panel["input_sha256"]
        params = read(directory / "round137_parameters.json")
        assert params == dict(split_threshold=0.08, delete_ab=False, delete_cr=False, delete_cg=False, loaded_after_presets=True)
        for auxiliary in ("round166_parameters.json", "round153_parameters.json", "round154_parameters.json",
                          "round156_parameters.json", "round160_parameters.json", "round162_parameters.json"):
            assert not (directory / auxiliary).exists(), auxiliary
        value["B_loaded_parameters"] = params
    r = result(directory / "result.json")
    if value["U"] is not None:
        assert value["U"] >= panel["positive_objective_floor_decimal"] - TOL
        assert (directory / "fleet.json").is_file()
    journal = {}
    for path in (directory / "journal").glob("event_*.json"):
        event = read(path)
        if event["kind"] == "call":
            journal[event["call"]] = event

    calls = []
    for binding in value["actual_call_log_bindings"]:
        event = journal[binding["call"]]
        time_limit = binding["parameters"]["TimeLimit"]
        assert math.isfinite(time_limit) and 0 < time_limit <= CAP - MARGIN + 1e-7
        assert event["model_sha256"] == binding["model_SHA"]
        assert event["settings"]["Threads"] == 1 and event["settings"]["Seed"] == 0
        model = next(row["model"] for row in value["models"] if row["call"] == binding["call"])
        version_text = (ROOT / binding["raw_log"]).read_bytes()[binding["byte_begin"]:binding["byte_end"]]
        assert b"Gurobi Optimizer version 13.0.2 " in version_text
        calls.append(dict(
            call=binding["call"], leaf=binding["leaf"], kind=binding["solve_kind"],
            settings=dict(event["settings"], TimeLimit=time_limit),
            TimeLimit_provenance="Actual Optimize banner in the bound native log",
            model_SHA256=binding["model_SHA"], model_fingerprint=binding["fingerprint"],
            model_rows=model["rows"], model_columns=model["columns"], status_returned=binding["journal_returned"],
            native_log_SHA256=binding["raw_log_SHA"], native_log_segment_SHA256=binding["segment_SHA"],
        ))
    assert len(calls) == value["actual_Optimize"]
    runtime_receipt = OUT / "runtime_readbacks" / f"{number:02d}.json"
    value.update(
        Native_Seed=0, run_id=directory.name, actual_Optimize_parameters=calls,
        initial_qualified_global_L=initial_bound(value, panel, journal),
        exact_first_hit_global_seconds=None,
        first_hit_missing_reason="Logs do not expose an unambiguous process-wall first-hit time.",
        native_DLL_live_readback=bind(runtime_receipt) if runtime_receipt.is_file() else None,
        CPP_effective_preset=r["algorithm_preset"], raw_status=r["status"],
    )
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("position", type=int)
    args = parser.parse_args()
    value = audit_position(args.position)
    path = OUT / "review" / f"complete_audit_{args.position:02d}.json"
    assert not path.exists(), f"Preserve the accepted audit at {path}"
    write(path, value)
    print(f"{utc()} AUDIT {args.position:02d} U={value['U']} L={value['L']} CERT={value['certificate']} "
          f"Optimize={value['actual_Optimize']}", flush=True)
