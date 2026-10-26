"""Solver-free source, scope, numerical and exact-union gates for B1 cross."""

from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import round88_ot_b1_cross as cross
from round88_ot_math import pair_cut, support_fingerprint


def small_source():
    supports = {1: [0, 1], 2: [0, 1]}
    targets = {1: 1, 2: 1}
    primal = {"state_1_0": 1.0, "state_1_1": 0.0,
              "state_2_0": 0.0, "state_2_1": 1.0,
              "state_g_1_0": 0.5, "state_g_1_1": 0.0,
              "state_g_2_0": 0.0, "state_g_2_1": 0.5,
              "h_1_2": 0.0}
    manifest = {"structure": {"support": {"1": [0, 1], "2": [0, 1]},
                              "effective_gamma_l": "0", "effective_gamma_u": "1"},
                "instance": {"targets": {"1": 1, "2": 1}}}
    cut = pair_cut("B1", 1, 2, supports, targets, F(0), F(1), primal)
    record = {"kind": "B1", "selected": True, "pair": [1, 2],
              "solver_row_scale": "1", "signs": [list(x) for x in cut.signs],
              "support_fingerprint": support_fingerprint(supports, targets, F(0), F(1)),
              "coefficients_exact": cross.canonical_coefficients(cut.coeff),
              "normalized_violation": 1.0, "selection_margin": 1e-6}
    return {"manifest": manifest, "primal": primal}, record


def large_identity():
    base = {"input_sha256": "same", "source_sha256": "same",
            "binary_sha256": "same", "scenario_id": "D7", "verified_ub": 0.3,
            "lambda": 0.15, "T": 18000, "pickup_time": 60, "drop_time": 60,
            "instance": {"n": 2, "vehicles": 1, "targets": {"1": 1, "2": 2},
                         "capacities": {"1": 2, "2": 2},
                         "weights": {"1": 1.0, "2": 1.0}},
            "structure": {"support": {"1": [0, 1], "2": [0, 1]},
                          "g_bounds": [0.0, 1.0]},
            "leaf_id": "L0", "parent_id": ""}
    child = deepcopy(base)
    child["leaf_id"] = "L0.0"
    child["parent_id"] = "L0"
    child["structure"]["g_bounds"] = [0.0, 0.5]
    return {"manifest": base}, {"manifest": child}


class CrossQualificationTests(unittest.TestCase):
    def test_only_frozen_reliable_b1_without_g_or_q_is_accepted(self):
        source, record = small_source()
        identifier, row = cross.parse_selected_b1(record, source)
        self.assertEqual(identifier, cross.row_id(
            {name: F(value) for name, value in row["coefficients_exact"].items()}))
        for changed, message in (({"kind": "B2"}, "already selected B1"),
                                 ({"solver_row_scale": "2"}, "scaled"),
                                 ({"support_fingerprint": "other"}, "identity"),
                                 ({"normalized_violation": 1e-7}, "reliably")):
            bad = {**record, **changed}
            with self.assertRaisesRegex(ValueError, message):
                cross.parse_selected_b1(bad, source)
        bad = deepcopy(record)
        bad["coefficients_exact"]["G"] = "1"
        with self.assertRaisesRegex(ValueError, "contains G"):
            cross.parse_selected_b1(bad, source)
        bad = deepcopy(record)
        bad["coefficients_exact"]["state_1_0"] = "-2"
        with self.assertRaisesRegex(ValueError, "coefficients/signs"):
            cross.parse_selected_b1(bad, source)

    def test_parent_child_input_support_cutoff_and_scope_gate(self):
        parent, child = large_identity()
        cross.verify_shared_identity(parent, child)
        for key, value in (("input_sha256", "other"), ("verified_ub", 0.2)):
            bad = deepcopy(child)
            bad["manifest"][key] = value
            with self.assertRaisesRegex(ValueError, key):
                cross.verify_shared_identity(parent, bad)
        bad = deepcopy(child)
        bad["manifest"]["structure"]["support"]["2"] = [0, 1, 2]
        with self.assertRaisesRegex(ValueError, "support"):
            cross.verify_shared_identity(parent, bad)
        bad = deepcopy(child)
        bad["manifest"]["structure"]["g_bounds"] = [-0.1, 0.5]
        with self.assertRaisesRegex(ValueError, "not contained"):
            cross.verify_shared_identity(parent, bad)

    def test_exact_union_and_duplicate_rejection(self):
        first = {"h_1_2": F(1), "state_1_0": F(-1)}
        second = {"state_1_0": F(1), "h_1_2": F(1)}
        a, b = cross.row_id(first), cross.row_id(second)
        self.assertEqual(a, cross.row_id(dict(reversed(list(first.items())))))
        self.assertNotEqual(a, b)
        bank = {"contract": "round88_d7_exact_b1_cross_point_v1",
                "rows": {a: {"pair": [1, 2], "coefficients_exact": cross.canonical_coefficients(first)},
                         b: {"pair": [1, 2], "coefficients_exact": cross.canonical_coefficients(second)}},
                "sets": {"R_parent": [a], "R_child": [a, b], "union": sorted([a, b])}}
        cross.validate_row_bank(bank)
        duplicate = deepcopy(bank)
        duplicate["sets"]["R_parent"] = [a, a]
        with self.assertRaisesRegex(ValueError, "invalid exact row set"):
            cross.validate_row_bank(duplicate)
        omitted = deepcopy(bank)
        omitted["sets"]["union"] = [a]
        with self.assertRaisesRegex(ValueError, "exact set union"):
            cross.validate_row_bank(omitted)
        altered = deepcopy(bank)
        altered["rows"][a]["coefficients_exact"]["h_1_2"] = "2"
        with self.assertRaisesRegex(ValueError, "identifier mismatch"):
            cross.validate_row_bank(altered)

    def test_source_sha_mismatch_rejected(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "source.json"
            p.write_text("{}", encoding="utf-8")
            with mock.patch.object(cross, "path_for", return_value=p):
                with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                    cross.verified_file("source.json", "0" * 64)

    def test_lp_and_input_asset_bytes_must_match_audit(self):
        with TemporaryDirectory() as tmp:
            lp, inp = Path(tmp) / "original.lp", Path(tmp) / "input.txt"
            lp.write_text("original model", encoding="utf-8")
            inp.write_text("original instance", encoding="utf-8")
            manifest = {"lp": str(lp), "lp_sha256": hashlib.sha256(lp.read_bytes()).hexdigest(),
                        "input": str(inp),
                        "input_sha256": hashlib.sha256(inp.read_bytes()).hexdigest()}
            cross.verify_model_assets(manifest, {"lp_sha256": manifest["lp_sha256"]})
            inp.write_text("changed instance", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source LP/input bytes changed"):
                cross.verify_model_assets(manifest)

    def test_supervisor_uses_remaining_whole_process_time(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            manifest, out = base / "manifest.json", base / "supervised"
            manifest.write_text('{"whole_process_limit_seconds": 2.0}', encoding="utf-8")
            calls = []
            class FakeProcess:
                returncode = 0
                def communicate(self, timeout):
                    calls.append(timeout)
                    (out / "diagnostic").mkdir()
                    (out / "diagnostic" / "result.json").write_text(json.dumps({
                        "manifest_sha256": cross.sha256(manifest),
                        "status": "completed_six_arms_optimal"}), encoding="utf-8")
                    return "", ""
            clock = iter((0.0, 0.4, 0.7, 0.7))
            with mock.patch.object(cross.subprocess, "Popen", return_value=FakeProcess()), \
                 mock.patch.object(cross.time, "perf_counter", side_effect=lambda: next(clock)):
                self.assertEqual(cross.supervise(manifest, out, 2.0), 0)
            self.assertEqual(calls, [1.6])
            self.assertEqual(json.loads((out / "supervision.json").read_text())["status"],
                             "diagnostic_process_finished")

    def test_supervisor_timeout_is_unknown_without_retry(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            manifest, out = base / "manifest.json", base / "supervised"
            manifest.write_text('{"whole_process_limit_seconds": 2.0}', encoding="utf-8")
            calls = []
            class FakeProcess:
                returncode = None
                stopped = False
                def communicate(self, timeout):
                    calls.append(timeout)
                    if not self.stopped:
                        raise subprocess.TimeoutExpired("fake", timeout)
                    return "", ""
                def terminate(self):
                    self.stopped = True
                    self.returncode = -15
                def kill(self):
                    raise AssertionError("unneeded second termination")
            fake = FakeProcess()
            clock = iter((0.0, 2.0, 2.1))
            with mock.patch.object(cross.subprocess, "Popen", return_value=fake), \
                 mock.patch.object(cross.time, "perf_counter", side_effect=lambda: next(clock)):
                self.assertEqual(cross.supervise(manifest, out, 2.0), 124)
            self.assertTrue(fake.stopped)
            self.assertEqual(calls, [0.0, 5])
            self.assertEqual(json.loads((out / "supervision.json").read_text())["status"],
                             "unknown_whole_process_deadline")

    def test_supervisor_rejects_changed_deadline_before_launch(self):
        with TemporaryDirectory() as tmp:
            manifest, out = Path(tmp) / "manifest.json", Path(tmp) / "output"
            manifest.write_text('{"whole_process_limit_seconds": 120}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs from frozen manifest"):
                cross.supervise(manifest, out, 121)
            self.assertFalse(out.exists())

    def test_partial_result_cannot_look_like_six_arm_success(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            manifest, out = base / "manifest.json", base / "supervised"
            manifest.write_text('{"whole_process_limit_seconds": 2.0}', encoding="utf-8")
            class FakeProcess:
                returncode = 0
                def communicate(self, timeout):
                    (out / "diagnostic").mkdir()
                    (out / "diagnostic" / "result.json").write_text(json.dumps({
                        "manifest_sha256": cross.sha256(manifest),
                        "status": "partial_unknown_arm_not_optimal"}), encoding="utf-8")
                    return "", ""
            clock = iter((0.0, 0.1, 0.5, 0.5))
            with mock.patch.object(cross.subprocess, "Popen", return_value=FakeProcess()), \
                 mock.patch.object(cross.time, "perf_counter", side_effect=lambda: next(clock)):
                self.assertEqual(cross.supervise(manifest, out, 2.0), 126)
            self.assertEqual(json.loads((out / "supervision.json").read_text())["status"],
                             "partial_unknown_arm_not_optimal")


if __name__ == "__main__":
    unittest.main()
