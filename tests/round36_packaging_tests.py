#!/usr/bin/env python3
"""Unit tests for deterministic Round 36 evidence packaging."""

from __future__ import annotations

import csv
import gzip
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import package_round36_evidence as package  # noqa: E402


class Round36PackagingTests(unittest.TestCase):
    def test_repository_artifact_size_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            path.write_bytes(b"small")
            package.require_repository_artifact_size(path)
            with mock.patch.object(Path, "stat") as stat:
                stat.return_value.st_size = (
                    package.MAX_REPOSITORY_ARTIFACT_BYTES + 1)
                with self.assertRaisesRegex(RuntimeError, "exceeds 95 MiB"):
                    package.require_repository_artifact_size(path)

    def test_large_trajectory_table_is_packaged_compressed(self) -> None:
        self.assertEqual("trajectory_events.csv.gz",
                         package.COMPRESSED_DERIVED["trajectory_events.csv"])
        inventory_names = [package.COMPRESSED_DERIVED.get(name, name)
                           for name in package.FINAL_DERIVED]
        self.assertIn("trajectory_events.csv.gz", inventory_names)
        self.assertNotIn("trajectory_events.csv", inventory_names)

    def test_official_row_revalidation_is_fail_closed(self) -> None:
        matrix = [{"run_id": "row", "instance_id": "instance"}]
        items = {"instance": {"instance_sha256": "expected"}}
        with mock.patch.object(package.analysis, "artifact_complete",
                               return_value=(True, "ok")) as check:
            package.validate_official_rows(matrix, {}, items)
            check.assert_called_once()
        with mock.patch.object(
                package.analysis, "artifact_complete",
                return_value=(False, "artifact_checksum_mismatch:result.json")):
            with self.assertRaisesRegex(
                    RuntimeError, "artifact_checksum_mismatch:result.json"):
                package.validate_official_rows(matrix, {}, items)

    def test_final_exactness_validation_requires_56_lifecycle_green_rows(
            self) -> None:
        fields = (
            "run_id", "exactness_certificate_audit_passed",
            "false_certificate", "runner_normal_exit",
            "runner_no_emergency_timeout",
            "result_json_verified_after_process_exit",
            "runner_required_artifacts_complete",
            "atomic_completion_marker_valid",
            "algorithmic_solve_state_not_resumed", "runner_lifecycle_valid",
            "certificate_or_graceful_deadline_endpoint_valid", "finite_bounds",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exactness.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for index in range(56):
                    writer.writerow({field: (
                        f"row-{index}" if field == "run_id" else
                        "False" if field == "false_certificate" else "True")
                        for field in fields})
            self.assertTrue(package.final_exactness_valid(path))
            rows = path.read_text(encoding="utf-8").replace(
                "row-55,True,False", "row-54,True,False", 1)
            path.write_text(rows, encoding="utf-8")
            self.assertFalse(package.final_exactness_valid(path))

    def test_required_raw_ledgers_are_covered_without_models(self) -> None:
        required = {
            "result.json", "completion_marker.json", "artifact_manifest.csv",
            "external/initial_decomposition_ledger.csv",
            "external/global_bound_trace.csv",
            "external/lp_status_ledger.csv",
            "external/native_target_ledger.csv",
            "external/paper_leaf_ledger.csv",
            "external/paper_optimize_ledger.csv",
            "external/paper_tree_events.csv",
            "external/parent_child_bound_ledger.csv",
            "external/split_decision_ledger.csv",
        }
        self.assertTrue(required.issubset(set(package.RAW_FILES)))
        self.assertFalse(any("models/" in path for path in package.RAW_FILES))

    def test_sensitive_marker_scan_is_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_bytes(b"prefix WLSSecret suffix")
            self.assertEqual(package.sensitive(path), "wlssecret")
            path.write_bytes(b"ordinary solver evidence")
            self.assertEqual(package.sensitive(path), "")

    def test_gzip_output_is_deterministic_and_lossless(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.csv"
            first, second = root / "first.gz", root / "second.gz"
            payload = (b"a,b,c\n1,2,3\n" * 1000)
            source.write_bytes(payload)
            package.gzip_deterministic(source, first)
            package.gzip_deterministic(source, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with gzip.open(first, "rb") as stream:
                self.assertEqual(stream.read(), payload)


if __name__ == "__main__":
    unittest.main()
