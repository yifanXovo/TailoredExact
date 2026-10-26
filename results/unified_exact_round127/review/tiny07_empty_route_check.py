"""Bounded independent post-seal tiny07 check; run only inside a verification meter.

Only standard library and our own prepared independent model/physical/proof
helpers are used. No production verifier is imported and no native call occurs.
The real handoff wrapper is extracted as AST for isolated behavior probes.
"""
from pathlib import Path
import argparse
import ast
import copy
import datetime
import hashlib
import importlib.util
import json
import re
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "results/unified_exact_round127"
CAMP = OUT / "tiny/07_SM-B10-B_S0_R1"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def legacy_hash(witness):
    parts = []
    for route in sorted(witness["routes"], key=lambda r: r["vehicle"]):
        operations = sorted((o["station"], o["pickup"], o["drop"]) for o in route["operations"])
        parts.append("v=" + str(route["vehicle"]) + ";nodes=" + "".join(str(i) + "," for i in route["nodes"])
            + ";ops=" + "".join(":".join(map(str, o)) + "," for o in operations) + "|")
    return hashlib.sha256("".join(parts).encode("ascii")).hexdigest()


def check(args):
    spec = importlib.util.spec_from_file_location("tiny07_own_independent_helpers", Path(__file__).with_name("final_independent_audit.py"))
    own = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(own)  # definitions/stdlib imports only; its CLI/audit is not invoked
    legacy_sources = {}
    for name in ["round100_campaign.py", "round73_seed_diagnostic.py", "round75_startup.py",
                 "round108_reader.py", "round120_evidence.py", "round122_evidence.py"]:
        path = ROOT / "scripts" / name
        committed = own.git("show", own.SELECTION_COMMIT + ":scripts/" + name)
        r126 = own.git("show", "473594a56ae9f1730899111375b3210f437adec2:scripts/" + name)
        actual = path.read_bytes()
        # Some inherited files have ordinary Windows CRLF worktree conversion;
        # others are -text. Preserve/report both exact byte identities. Only
        # CRLF -> LF is allowed for program-text comparison, never arbitrary
        # whitespace/source normalization or a rewrite of the original file.
        require(committed == r126, "legacy Git source differs from actual R126 base: " + name)
        canonical = actual.replace(b"\r\n", b"\n")
        baseline = committed.replace(b"\r\n", b"\n")
        require(b"\r" not in canonical and b"\r" not in baseline and canonical == baseline,
                "legacy helper program text changed beyond CRLF/LF: " + name)
        legacy_sources[name] = dict(actual_path=str(path.resolve()), actual_SHA=sha(path),
            selection_commit_blob_SHA=hashlib.sha256(committed).hexdigest(),
            R126_blob_SHA=hashlib.sha256(r126).hexdigest(), canonical_LF_SHA=hashlib.sha256(canonical).hexdigest(),
            raw_bytes_equal=actual == committed, worktree_CRLF=actual.count(b"\r\n"),
            commit_CRLF=committed.count(b"\r\n"), program_text_equal_with_only_CRLF_to_LF=True,
            source_files_rewritten=False)
    identity = read(CAMP / "identity.json")
    launch = identity["launches"][0]
    require((launch["method"], launch["seed"], launch["repeat"], launch["binary_layer"])
            == ("MB", 0, 1, "E0"), "fixed tiny07 MB identity")
    d, panel = Path(launch["destination"]), launch["panel"]
    saved = read(OUT / "review/tiny07_failure_snapshot/preservation.json")
    require(sha(d / "producer_receipt.json") == saved["producer_receipt_SHA"]
            and sha(d / "producer_seal.json") == saved["producer_seal_SHA"], "original producer/seal unchanged")
    require(read(d / "producer_receipt.json") == saved["original_producer_receipt"], "original production clock unchanged")
    for name, expected in saved["original_producer_required_SHA"].items():
        require(sha(d / name) == expected, "sealed output unchanged: " + name)
    for name, expected in saved["copied_failed_verification_files"].items():
        require(sha(OUT / "review/tiny07_failure_snapshot" / name) == expected, "failed derived evidence preserved: " + name)
    require(read(d / "child_process_origin.json") == saved["original_native_creation"], "no second native process identity")
    observations = read(d / "observations.json")
    startup = [r["payload"] for r in observations if r["payload"]["kind"] == "witness" and r["payload"]["call"] == 0]
    require(len(startup) == 1, "one own startup witness")
    startup = startup[0]
    initial, final = [read(d / ("hga.csv.exchange/" + n + ".json")) for n in ["initial", "final"]]
    require(initial["routes"] == final["routes"] == [] and len(startup["routes"]) == panel["M"] == 2,
            "actual discrepancy is only explicit empty-vehicle representation")
    require(legacy_hash(startup) not in {legacy_hash(initial), legacy_hash(final)}, "original hash mismatch reproduced")
    replays = [own.physical(panel, witness) for witness in [initial, final, startup]]
    require(all(r["Y"] == replays[0]["Y"] and all(own.close(r[k], replays[0][k]) for k in ["F", "G", "P"])
                for r in replays), "empty fleet physical/objective/inventory equivalence")
    source_path = ROOT / "scripts/round127_evidence.py"
    source = source_path.read_text(encoding="utf-8")
    parsed = ast.parse(source)
    wrapper = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == "handoff_adapter")
    writes = []
    namespace = dict(types=types, Path=Path, sha=sha,
        write=lambda path, value: writes.append((str(path), copy.deepcopy(value))))
    exec(compile(ast.Module(body=[wrapper], type_ignores=[]), str(source_path) + "::isolated_handoff_probe", "exec"), namespace)
    api = types.SimpleNamespace(route_hash=legacy_hash, normalize=copy.deepcopy)
    def probe_adapter(l, records, completion, identity):
        witness, left, right = records
        assert r90.route_hash(r90.normalize(witness)) in {r90.route_hash(left), r90.route_hash(right)}
        return dict(probe_passed=True)
    probe = types.FunctionType(probe_adapter.__code__, dict(probe_adapter.__globals__, r90=api), "probe_adapter")
    adapted = namespace["handoff_adapter"](probe)
    before = copy.deepcopy([startup, initial, final])
    require(adapted(launch, [startup, initial, final], None, None)["probe_passed"] is True, "actual local proxy accepts only the physical omission")
    require([startup, initial, final] == before and api.route_hash is legacy_hash, "raw witnesses/original hash API unchanged")
    nonempty = dict(vehicle=0, nodes=[0, 1, 2, 0], operations=[dict(station=1, pickup=1, drop=0), dict(station=2, pickup=0, drop=1)])
    empty = dict(vehicle=1, nodes=[0, 0], operations=[])
    good = dict(routes=[nonempty, empty])
    require(adapted(launch, [good, dict(routes=[nonempty]), dict(routes=[nonempty])], None, None)["probe_passed"], "nonempty route retained exactly")
    negative = [dict(routes=[empty, empty]), dict(routes=[dict(empty, vehicle=2)]), dict(routes=[dict(empty, vehicle=-1)]),
        dict(routes=[dict(empty, vehicle=0.)]), dict(routes=[dict(empty, vehicle=True)]),
        dict(routes=[dict(vehicle=0, nodes=[0, 1, 0], operations=[])]),
        dict(routes=[dict(nonempty, vehicle=1)]),
        dict(routes=[dict(nonempty, operations=[dict(station=1, pickup=2, drop=0), dict(station=2, pickup=0, drop=2)])])]
    for k, bad in enumerate(negative):
        reference = dict(routes=[nonempty]) if k >= 6 else dict(routes=[])
        try:
            adapted(launch, [bad, reference, reference], None, None)
        except (AssertionError, KeyError, ValueError):
            pass
        else:
            raise ValueError("proxy wrongly accepts changed label/quantity or invalid/duplicate vehicle case " + str(k))
    calls = [r["payload"] for r in observations if r["payload"]["kind"] == "call"]
    require(len(calls) == 1 and calls[0]["leaf"] == "L0" and calls[0]["lower_g"] == 0
            and calls[0]["upper_g"] == min(calls[0]["cutoff"], calls[0]["gmax"]), "full relevant initial root scope")
    result = read(d / "result.json")
    require(calls[0]["cutoff"] == result["upper_bound"] == replays[0]["F"]
            and result["lower_bound"] == result["upper_bound"], "own physical U and actual root bound")
    sample = dict(_path=str(d), _panel=panel, _result=result, _group="tiny/07_SM-B10-B_S0_R1",
        method="MB", seed=0, U=result["upper_bound"], L=result["lower_bound"], certificate=True, native_Optimize=1)
    chain = own.proof_chain(sample)
    require(chain["native_calls"] == 1 and chain["native_records"][0]["solve_kind"] == "LP"
            and chain["native_records"][0]["proof"]["source"] == "linked_complete_optimal_LP", "optimal complete LP proof, no target-only substitute")
    complete = all((d / n).is_file() for n in ["audit.json", "verification_closeout.json", "arm_total_receipt.json"])
    recovered = False
    if complete:
        audit, closeout, total = [read(d / n) for n in ["audit.json", "verification_closeout.json", "arm_total_receipt.json"]]
        recovered = (audit.get("passed") is True and audit.get("endpoint", {}).get("certificate") is True
            and closeout.get("necessary_verification_complete") is True and closeout.get("native_proof_qualified") is True
            and closeout.get("no_new_solution_or_certificate_backfilled") is True
            and total.get("necessary_verification_complete") is True)
        if recovered:
            producer = read(d / "producer_receipt.json")
            require(total["producer_receipt_SHA"] == sha(d / "producer_receipt.json")
                    and total["verification_closeout_SHA"] == sha(d / "verification_closeout.json")
                    and own.close(total["T_verify"], total["t_verified_perf"] - producer["t_produce_perf"], 1e-8)
                    and own.close(total["T_total"], producer["T_produce"] + total["T_verify"], 1e-8), "verification recovery includes the actual elapsed wall span")
    if args.require_full_reader:
        require(recovered, "complete inherited reader/closeout/total receipts are still required")
    return dict(status="PASS", own_normalizer_probe_scope="isolated actual handoff wrapper with original hash grammar; production verifier not invoked",
        positive_proxy_cases=2, rejecting_invalid_or_changed_nonempty_cases=len(negative), original_producer_unchanged=True,
        original_failed_evidence_preserved=True, original_T_produce=saved["original_producer_receipt"]["T_produce"],
        parameter_native_PID_and_raw_outputs_unchanged=True, patched_evidence_source_SHA=sha(source_path),
        own_helper_source_SHA=sha(Path(__file__).with_name("final_independent_audit.py")),
        legacy_source_byte_and_program_bindings=legacy_sources,
        empty_fleet_replays=replays, complete_root_LP_cover_proof=chain,
        full_reader_recovered=recovered, final_qualification_pending=not recovered,
        no_new_Optimize=True, no_build=True, no_new_native_process=True, no_raw_rewrite=True,
        scope="One fixed sealed tiny07 arm, exact unused-route representation and complete actual root-LP provenance only; no outcome-based model/parameter change")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--fee-label", required=True)
    parser.add_argument("--require-full-reader", action="store_true")
    args = parser.parse_args()
    require(re.fullmatch(r"[a-z0-9_-]{1,64}", args.attempt), "safe unique attempt")
    output = OUT / "review/tiny07_empty_route_attempts" / args.attempt
    output.mkdir(parents=True, exist_ok=False)
    try:
        receipt = check(args)
    except Exception as exc:
        receipt = dict(status="FAIL", error=type(exc).__name__ + ": " + str(exc), no_new_Optimize=True, no_build=True)
    receipt.update(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), verification_fee_label=args.fee_label,
                   script_SHA=sha(__file__), independent_helper_only=True)
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=receipt["status"], error=receipt.get("error"), receipt=str(output / "receipt.json"),
        full_reader_recovered=receipt.get("full_reader_recovered"))), flush=True)
    sys.exit(0 if receipt["status"] == "PASS" else 1)
