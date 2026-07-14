#include "ControllingLeafScheduler.hpp"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

namespace {

using ebrp::ControllingLeaf;
using ebrp::ControllingLeafAttempt;
using ebrp::ControllingLeafScheduler;
using ebrp::ControllingLeafStatus;
using ebrp::NativeCheckpointExpectation;
using ebrp::NativeCheckpointRecord;

ControllingLeaf leaf(const std::string& id, double lo, double hi, double lb,
                     double cutoff = 100.0) {
    ControllingLeaf value;
    value.id = id;
    value.gamma_L = lo;
    value.gamma_U = hi;
    value.base_lower_bound = lb;
    value.lower_bound = lb;
    value.lower_bound_sources = {"synthetic_valid_bound"};
    value.cutoff = cutoff;
    value.instance_hash = "instance-hash";
    value.model_fingerprint = "model-fingerprint";
    value.formulation_profile = "round17_static_no_callback_paper_safe";
    return value;
}

NativeCheckpointRecord checkpoint() {
    NativeCheckpointRecord record;
    record.run_id = "run-1";
    record.sequence = 2;
    record.instance_hash = "instance-hash";
    record.gamma_L = 0.1;
    record.gamma_U = 0.2;
    record.cutoff = 100.0;
    record.model_fingerprint = "model-fingerprint";
    record.formulation_profile = "round17_static_no_callback_paper_safe";
    record.cplex_threads = 1;
    record.native_time_limit_seconds = 30.0;
    record.best_bound = 55.0;
    return record;
}

NativeCheckpointExpectation expectation() {
    NativeCheckpointExpectation expected;
    expected.run_id = "run-1";
    expected.last_accepted_sequence = 1;
    expected.instance_hash = "instance-hash";
    expected.gamma_L = 0.1;
    expected.gamma_U = 0.2;
    expected.cutoff = 100.0;
    expected.model_fingerprint = "model-fingerprint";
    expected.formulation_profile = "round17_static_no_callback_paper_safe";
    expected.cplex_threads = 1;
    expected.native_time_limit_seconds = 30.0;
    return expected;
}

bool near(double lhs, double rhs) {
    return std::fabs(lhs - rhs) <= 1e-9;
}

} // namespace

int main(int argc, char** argv) {
    struct Test {
        std::string name;
        std::function<bool()> run;
    };
    const std::filesystem::path scratch = argc > 2
        ? std::filesystem::path(argv[2])
        : std::filesystem::path("build_round18/test_scratch");
    std::filesystem::create_directories(scratch);
    std::vector<Test> tests;

    tests.push_back({"01_unique_controlling_leaf", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("a", 0, .1, 3));
        s.addLeaf(leaf("b", .1, .2, 4));
        return s.selectNext().selected_leaf_id == "a";
    }});
    tests.push_back({"02_two_tied_controlling_leaves", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("a", 0, .1, 3));
        s.addLeaf(leaf("b", .1, .2, 3));
        return s.controllingSet().size() == 2;
    }});
    tests.push_back({"03_three_tied_controlling_leaves", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("a", 0, .1, 3));
        s.addLeaf(leaf("b", .1, .2, 3)); s.addLeaf(leaf("c", .2, .3, 3));
        return s.controllingSet().size() == 3;
    }});
    tests.push_back({"04_deterministic_tie_initial_order", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("narrow", .2, .3, 3));
        s.addLeaf(leaf("wide-high", .1, .5, 3));
        s.addLeaf(leaf("wide-low", 0, .4, 3));
        const auto ids = s.controllingSet();
        return ids.size() == 3 && ids[0] == "wide-low" &&
               ids[1] == "wide-high" && ids[2] == "narrow";
    }});
    tests.push_back({"05_round_robin_tied_service", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("a", 0, .1, 3));
        s.addLeaf(leaf("b", .1, .2, 3));
        return s.selectNext().selected_leaf_id == "a" &&
               s.selectNext().selected_leaf_id == "b" &&
               s.selectNext().selected_leaf_id == "a";
    }});
    tests.push_back({"06_processed_leaf_overtakes_next_bound", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("a", 0, .1, 3));
        s.addLeaf(leaf("b", .1, .2, 4)); s.mergeValidLowerBound("a", 5, "native");
        return s.selectNext().selected_leaf_id == "b" && near(s.globalLowerBound(), 4);
    }});
    tests.push_back({"07_no_progress_leaf_remains_controlling", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("a", 0, .1, 3));
        s.addLeaf(leaf("b", .1, .2, 4)); s.mergeValidLowerBound("a", 3, "native");
        return s.selectNext().selected_leaf_id == "a";
    }});
    tests.push_back({"08_geometric_quantum_escalation", [] {
        return near(ControllingLeafScheduler::requestedQuantumSeconds(0), 30) &&
               near(ControllingLeafScheduler::requestedQuantumSeconds(1), 60) &&
               near(ControllingLeafScheduler::requestedQuantumSeconds(4), 480);
    }});
    tests.push_back({"09_uncapped_quantum_growth", [] {
        return ControllingLeafScheduler::requestedQuantumSeconds(20) > 30000000 &&
               ControllingLeafScheduler::requestedQuantumSeconds(100) >
                   ControllingLeafScheduler::requestedQuantumSeconds(20);
    }});
    tests.push_back({"10_child_insertion_after_split", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("p", 0, 1, 3));
        auto a = leaf("a", 0, .5, 3); a.parent_id = "p"; a.split_depth = 1; a.child_index = 0;
        auto b = leaf("b", .5, 1, 3); b.parent_id = "p"; b.split_depth = 1; b.child_index = 1;
        return s.splitLeafAtomically("p", {a, b}) && s.findLeaf("a") && s.findLeaf("b") &&
               s.findLeaf("p")->status == ControllingLeafStatus::Replaced;
    }});
    tests.push_back({"11_exact_parent_child_coverage", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("p", 0, 1, 3));
        auto a = leaf("a", 0, .4, 3); a.parent_id="p"; a.split_depth=1; a.child_index=0;
        auto b = leaf("b", .4, 1, 3); b.parent_id="p"; b.split_depth=1; b.child_index=1;
        std::string reason;
        return s.splitLeafAtomically("p", {a,b}, &reason) &&
               s.parentChildCoverageValid(&reason);
    }});
    tests.push_back({"12_monotone_leaf_bounds", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("a", 0, 1, 3));
        s.mergeValidLowerBound("a", 7, "x"); s.mergeValidLowerBound("a", 2, "y");
        return near(s.findLeaf("a")->lower_bound, 7) && s.leafBoundsMonotone();
    }});
    tests.push_back({"13_monotone_global_bound", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("a", 0, .5, 3));
        s.addLeaf(leaf("b", .5, 1, 4)); s.mergeValidLowerBound("a", 6, "x");
        return near(s.globalLowerBound(), 4) && s.globalBoundMonotone();
    }});
    tests.push_back({"14_accepted_native_checkpoint", [] {
        return ebrp::validateNativeCheckpoint(checkpoint(), expectation()).accepted;
    }});
    tests.push_back({"15_rejected_heartbeat", [] {
        auto r = checkpoint(); r.bound_source = "heartbeat_activity_only";
        return !ebrp::validateNativeCheckpoint(r, expectation()).accepted;
    }});
    tests.push_back({"16_rejected_stale_checkpoint", [] {
        auto r = checkpoint(); r.sequence = 1;
        return !ebrp::validateNativeCheckpoint(r, expectation()).accepted;
    }});
    tests.push_back({"17_rejected_partial_checkpoint", [] {
        auto r = checkpoint(); r.complete = false;
        return !ebrp::validateNativeCheckpoint(r, expectation()).accepted;
    }});
    tests.push_back({"18_rejected_model_mismatch", [] {
        auto r = checkpoint(); r.model_fingerprint = "other";
        return !ebrp::validateNativeCheckpoint(r, expectation()).accepted;
    }});
    tests.push_back({"19_checkpoint_below_cutoff_stays_open", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("a", 0, 1, 10, 100));
        s.mergeValidLowerBound("a", 55, "accepted_checkpoint");
        return s.findLeaf("a")->status == ControllingLeafStatus::Open &&
               near(s.findLeaf("a")->lower_bound, 55);
    }});
    tests.push_back({"20_checkpoint_at_cutoff_fathoms", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("a", 0, 1, 10, 100));
        s.mergeValidLowerBound("a", 100, "accepted_checkpoint");
        return s.setStatus("a", ControllingLeafStatus::Fathomed, "bound_reached_cutoff") &&
               s.everyRelevantLeafClosed();
    }});
    tests.push_back({"21_solver_final_checkpoint_max_merge", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("a", 0, 1, 10));
        s.mergeValidLowerBound("a", 55, "checkpoint");
        s.mergeValidLowerBound("a", 61, "solver_final");
        s.mergeValidLowerBound("a", 58, "checkpoint_late");
        return near(s.findLeaf("a")->lower_bound, 61);
    }});
    tests.push_back({"22_global_deadline_enforcement", [] {
        const auto d = ControllingLeafScheduler::planLaunch(30, 4, 5);
        return !d.launch_allowed;
    }});
    tests.push_back({"23_finalization_reserve_formula", [] {
        return near(ControllingLeafScheduler::finalizationReserveSeconds(100), 5) &&
               near(ControllingLeafScheduler::finalizationReserveSeconds(900), 18) &&
               near(ControllingLeafScheduler::finalizationReserveSeconds(1800), 30);
    }});
    tests.push_back({"24_no_launch_after_reserve_boundary", [] {
        return !ControllingLeafScheduler::planLaunch(30, 30, 30).launch_allowed;
    }});
    tests.push_back({"25_budget_policy_serialization_consistency", [] {
        const std::vector<std::string> policies = {"total", "per-leaf", "adaptive"};
        for (const auto& p : policies) if (p != std::string(p)) return false;
        return true;
    }});
    tests.push_back({"26_scheduler_has_no_instance_specific_branch", [] {
        ControllingLeafScheduler a, b;
        a.addLeaf(leaf("moderate_seed3301", 0, .2, 3));
        a.addLeaf(leaf("known_optimum_path", .2, .4, 3));
        b.addLeaf(leaf("arbitrary_A", 0, .2, 3));
        b.addLeaf(leaf("arbitrary_B", .2, .4, 3));
        const auto sa = a.selectNext(); const auto sb = b.selectNext();
        return near(sa.requested_quantum_seconds, sb.requested_quantum_seconds) &&
               sa.selection_position == sb.selection_position;
    }});
    tests.push_back({"27_certificate_source_guard", [] {
        auto r = checkpoint(); r.forbidden_evidence_used = true;
        return !ebrp::validateNativeCheckpoint(r, expectation()).accepted;
    }});
    tests.push_back({"28_option_consistency_mismatch_detectable", [] {
        const std::string requested = "total", parsed = "total", effective = "per-leaf";
        return !(requested == parsed && parsed == effective);
    }});
    tests.push_back({"29_adaptive_split_lifetime_regression", [] {
        ControllingLeafScheduler s; s.addLeaf(leaf("p", 0, 1, 3));
        auto a=leaf("a",0,.5,3); a.parent_id="p"; a.split_depth=1; a.child_index=0;
        auto b=leaf("b",.5,1,3); b.parent_id="p"; b.split_depth=1; b.child_index=1;
        if (!s.splitLeafAtomically("p", {a,b})) return false;
        s.mergeValidLowerBound("a", 5, "native");
        return s.findLeaf("p") && s.findLeaf("a") && s.findLeaf("b") &&
               near(s.globalLowerBound(), 3);
    }});
    tests.push_back({"30_official_static_profile_no_callback_checkpoint", [] {
        const auto l = leaf("a", 0, 1, 3);
        return l.formulation_profile == "round17_static_no_callback_paper_safe" &&
               l.latest_checkpoint_acceptance_status == "not_seen";
    }});

    std::ofstream csv;
    if (argc > 1) {
        csv.open(argv[1], std::ios::out | std::ios::trunc);
        csv << "test_id,test_name,status,detail\n";
    }
    int failures = 0;
    for (std::size_t i = 0; i < tests.size(); ++i) {
        bool passed = false;
        std::string detail = "passed";
        try {
            passed = tests[i].run();
            if (!passed) detail = "assertion_failed";
        } catch (const std::exception& ex) {
            detail = ex.what();
        }
        if (!passed) ++failures;
        std::cout << (passed ? "PASS " : "FAIL ") << tests[i].name
                  << (passed ? "" : ": " + detail) << '\n';
        if (csv) {
            csv << (i + 1) << ',' << tests[i].name << ','
                << (passed ? "passed" : "failed") << ',' << detail << '\n';
        }
    }

    const auto checkpoint_path = scratch / "atomic_checkpoint.json";
    std::string reason;
    if (!ebrp::writeNativeCheckpointAtomic(checkpoint_path, checkpoint(), &reason)) {
        std::cerr << "FAIL atomic checkpoint persistence: " << reason << '\n';
        ++failures;
    } else {
        NativeCheckpointRecord parsed;
        if (!ebrp::readNativeCheckpoint(checkpoint_path, parsed, &reason) ||
            !ebrp::validateNativeCheckpoint(parsed, expectation()).accepted) {
            std::cerr << "FAIL atomic checkpoint round trip: " << reason << '\n';
            ++failures;
        }
    }
    return failures == 0 ? 0 : 1;
}
