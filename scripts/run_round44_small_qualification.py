#!/usr/bin/env python3
"""Run a frozen Round 44 candidate on validation or sealed holdout."""

from __future__ import annotations

import argparse

import round44_common as common
from run_round44_experiments import run_one


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("validation", "holdout"),
                        required=True)
    parser.add_argument("--candidate", choices=("primary", "veto-f05"),
                        default="primary")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    freeze_path = common.OUT / "final_candidate_freeze.json"
    if not freeze_path.is_file():
        raise SystemExit("final candidate must be frozen first")
    freeze = common.load_json(freeze_path)
    if args.candidate == "primary":
        config = freeze["configuration"]
        expected_executable = freeze["executable_sha256"]
        run_stage = args.stage
        tag = "final"
    else:
        fallback_path = common.OUT / "fallback_candidate_activation_freeze.json"
        if not fallback_path.is_file():
            raise SystemExit("fallback candidate must be activated before use")
        fallback = common.load_json(fallback_path)
        config = fallback["configuration"]
        expected_executable = fallback["executable_sha256"]
        run_stage = ("validation-fallback" if args.stage == "validation"
                     else args.stage)
        tag = "veto-f05"
        primary = common.load_json(common.OUT / "validation_disposition.json")
        if primary.get("passes_all_gates"):
            raise SystemExit("fallback is inadmissible after passing primary validation")
    if expected_executable != common.sha256(common.EXE):
        raise SystemExit("current executable does not match candidate freeze")
    if args.stage == "holdout":
        disposition_name = ("validation_disposition.json" if
                            args.candidate == "primary" else
                            "validation_fallback_disposition.json")
        disposition_path = common.OUT / disposition_name
        if not disposition_path.is_file() or not common.load_json(
                disposition_path).get("passes_all_gates"):
            raise SystemExit("holdout remains sealed until validation passes")
    instance_ids = (common.VALIDATION_IDS if args.stage == "validation"
                    else common.HOLDOUT_IDS)
    namespace = argparse.Namespace(
        stage=run_stage, execution=config["execution"],
        lookahead=config["lookahead"], injection=config["injection"],
        scope=config["scope"], family=config["family"],
        rho_f=config["rho_F"], rho_m=config["rho_M"],
        rho_h=config["rho_H"], rank1=config["rank1"],
        mip_starts=config["mip_starts"],
        consolidation=config["consolidation"], process_cap=3600.0,
        tag=tag, force=args.force)
    for instance_id in instance_ids:
        run_one(namespace, instance_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
