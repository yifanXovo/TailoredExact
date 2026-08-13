import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INSTANCE = ROOT / "include" / "Instance.hpp"
GEOMETRY_HEADER = ROOT / "include" / "GiniFrontierGeometry.hpp"
GEOMETRY_SOURCE = ROOT / "src" / "GiniFrontierGeometry.cpp"
TREE = ROOT / "src" / "PaperExternalGiniTree.cpp"
PROTOCOL = (
    ROOT / "results" / "gf_global_frontier_lift_round38" /
    "research_protocol.md"
)


class Round38ProtocolTests(unittest.TestCase):
    def test_policy_is_default_off(self) -> None:
        text = INSTANCE.read_text(encoding="utf-8")
        self.assertIn(
            'std::string round38_c6_frontier_policy = "off";', text
        )

    def test_selector_has_no_forbidden_inputs(self) -> None:
        header = GEOMETRY_HEADER.read_text(encoding="utf-8")
        start = header.index("struct PilotGlobalFrontierSelection")
        end = header.index("// A launch-frozen anchor grid", start)
        contract = header[start:end].lower()
        for forbidden in (
            "instance_id", "scenario", "seed_id", "elapsed", "runtime",
            "work", "node", "processor", "hardware", "winner", "historical",
            "v_specific", "m_specific",
        ):
            self.assertNotIn(forbidden, contract)

        source = GEOMETRY_SOURCE.read_text(encoding="utf-8")
        start = source.index(
            "PilotGlobalFrontierSelection selectPilotGlobalFrontierCell("
        )
        end = source.index(
            "std::string cplexReplicaSplitPhaseName", start
        )
        selector = source[start:end].lower()
        for forbidden in (
            "instance_id", "scenario", "seed_id", "elapsed", "runtime",
            "work", "nodes", "processor", "hardware", "winner", "historical",
        ):
            self.assertNotIn(forbidden, selector)

    def test_active_policy_is_isolated_from_round37(self) -> None:
        source = TREE.read_text(encoding="utf-8")
        self.assertIn(
            'options.round38_c6_frontier_policy ==\n'
            '            "pilot-next-frontier-complete"',
            source,
        )
        self.assertIn("geometry_policy == \"off\"", source)
        self.assertIn(
            "round38_rejected_pilot_resume_c6_next_frontier", source
        )

    def test_protocol_forbids_long_and_effort_driven_decisions(self) -> None:
        protocol = PROTOCOL.read_text(encoding="utf-8").lower()
        self.assertIn("no run may use 3600 seconds or more", protocol)
        self.assertIn(
            "time, work, nodes, instance ids, v/m, scenario labels", protocol
        )


if __name__ == "__main__":
    unittest.main()
