#!/usr/bin/env python3
"""Unit tests for deterministic Round 36 evidence packaging."""

from __future__ import annotations

import gzip
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import package_round36_evidence as package  # noqa: E402


class Round36PackagingTests(unittest.TestCase):
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
