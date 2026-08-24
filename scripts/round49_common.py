#!/usr/bin/env python3
"""Frozen identities and deterministic helpers for Round 49 K1-AM-RC."""

from __future__ import annotations

import os
from pathlib import Path

import round48_common as r48


ROOT = r48.ROOT
OUT = ROOT / "results" / "gf_k1_lp_primal_dual_rescue_round49"
RUNS = OUT / "runs"
TAU = 0.07915
MAX_PROCESS_CAP = 1800
CERTIFICATE_TOLERANCE = 1e-7
EXE = Path(os.environ.get(
    "EXACTEBRP_ROUND49_EXE",
    str(ROOT / "build" / "official-round49" / "ExactEBRP.exe")))

MECHANISM = r48.MECHANISM
EXISTING_CONFIRMATION = r48.EXISTING_CONFIRMATION
ADDITIONAL_CONFIRMATION = r48.ADDITIONAL_CONFIRMATION
STAGE4 = MECHANISM + EXISTING_CONFIRMATION
STAGE5 = STAGE4 + ADDITIONAL_CONFIRMATION
INSTANCE_PATHS = r48.INSTANCE_PATHS

ROLES = dict(r48.ROLES)
ROLES.update({
    MECHANISM[0]: "major_harmful_split_witness",
    MECHANISM[1]: "strong_control_beneficial_split",
    MECHANISM[2]: "harmful_split_negative_control",
    MECHANISM[3]: "numerical_beneficial_split",
    MECHANISM[4]: "beneficial_k1_root_split",
    MECHANISM[5]: "existing_useful_multilevel_refinement",
    MECHANISM[6]: "good_k1_bound_trajectory_guard",
    MECHANISM[7]: "confirmed_beneficial_descendant_split",
})

sha256 = r48.sha256
stable_hash = r48.stable_hash
load_json = r48.load_json
csv_rows = r48.csv_rows
write_text = r48.write_text
write_json = r48.write_json
write_csv = r48.write_csv
replace_option = r48.replace_option
remove_option = r48.remove_option


PRIMITIVE_FAMILIES = (
    ("routing_arc", "x_", 3, "binary", "vehicle arc-selection decision"),
    ("visit_selection", "z_", 2, "binary", "vehicle-station visit decision"),
    ("operation_mode", "mode_", 2, "binary", "pickup/drop operation-mode decision"),
    ("pickup_quantity", "p_", 2, "general_integer", "pickup transfer quantity"),
    ("drop_quantity", "d_", 2, "general_integer", "drop transfer quantity"),
    ("vehicle_load", "load_", 2, "general_integer", "vehicle load-state decision"),
    ("final_inventory", "Y_", 1, "general_integer", "station final-inventory decision"),
)


def frozen_instances():
    freeze = load_json(OUT / "dataset_freeze.json")
    return {row["instance"]: row for row in freeze["instances"]}


def input_path(item):
    return ROOT / item["path"]


def historical_k1_am_command(item, run_dir, process_cap, executable):
    command = r48.historical_k1_am_command(
        item, run_dir, process_cap, executable)
    replace_option(command, "--round48-k1-amf", "off")
    replace_option(command, "--round49-k1-am-rc", "off")
    replace_option(command, "--external-gini-artifact-dir", run_dir / "external")
    return command


def candidate_command(item, run_dir, process_cap, executable, rule):
    command = historical_k1_am_command(item, run_dir, process_cap, executable)
    replace_option(command, "--round49-k1-am-rc", rule)
    return command

