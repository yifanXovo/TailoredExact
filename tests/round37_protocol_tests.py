import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
TREE = ROOT / "src" / "PaperExternalGiniTree.cpp"
GEOMETRY = ROOT / "src" / "GiniFrontierGeometry.cpp"
INSTANCE = ROOT / "include" / "Instance.hpp"
ROUND37 = ROOT / "results" / "gf_gini_geometry_mechanism_round37"


class Round37ProtocolTests(unittest.TestCase):
    def test_all_exact_evidence_ledgers_use_round_trip_precision(self) -> None:
        source = TREE.read_text(encoding="utf-8")
        streams = (
            "events", "optimize", "lp_ledger", "bound_ledger",
            "split_ledger", "global_trace", "native_targets",
            "initial_decomposition",
        )
        for stream in streams:
            self.assertIn(f"{stream} << std::setprecision(17);", source)

    def test_round36_consolidation_preserves_frozen_stage_b(self) -> None:
        text = (ROUND37 / "round36_reporting_consolidation.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("intermediate decision artifacts", text)
        self.assertIn("C6-HGA-FULL remained", text)
        self.assertIn("PR 83", text)
        self.assertIn("retained byte for", text)

    def test_cleanup_is_narrow_and_hash_guarded(self) -> None:
        source = (ROOT / "scripts" /
                  "cleanup_round36_local_artifacts.py").read_text(
                      encoding="utf-8"
                  )
        self.assertIn("path.resolve().parent != round36_resolved", source)
        self.assertIn("trajectory compression identity check failed", source)
        self.assertNotIn("rmtree", source)
        self.assertNotIn("unlink(missing_ok", source)

    def test_round37_policy_is_default_off_and_uniform(self) -> None:
        instance = INSTANCE.read_text(encoding="utf-8")
        self.assertIn(
            'std::string round37_c6_geometry_policy = "off";', instance
        )
        source = GEOMETRY.read_text(encoding="utf-8")
        start = source.index(
            "PilotWeakestGiniCellSelection selectPilotWeakestGiniCell("
        )
        end = source.index(
            "std::string cplexReplicaSplitPhaseName", start
        )
        selector = source[start:end].lower()
        for forbidden in (
            "elapsed", "runtime", "node_count", "instance_name",
            "scenario", "historical", "work_units", "hardware",
        ):
            self.assertNotIn(forbidden, selector)
        self.assertIn("lp_lower_bound", selector)
        self.assertIn("interval.lower", selector)

    def test_round37_panel_was_frozen_before_candidate_results(self) -> None:
        panel = (ROUND37 / "frozen_development_panel.json").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            '"candidate_result_rows_present_before_freeze": 0', panel
        )
        self.assertIn(
            '"panel_sha256": '
            '"bc73e8ed85831870112cec68f95aa45a31eb73436b5442b5f1260e695bb6b919"',
            panel,
        )


if __name__ == "__main__":
    unittest.main()
