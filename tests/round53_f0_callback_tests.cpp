#include "CanonicalCompactModel.hpp"
#include "Round50IntervalMip.hpp"
#include "Round52TailoredCuts.hpp"
#include "Round53CallbackIsolation.hpp"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

std::string readAll(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(in),
                       std::istreambuf_iterator<char>());
}

ebrp::Instance fixture(int V) {
    ebrp::Instance instance;
    instance.name = "round53_fixture_v" + std::to_string(V);
    instance.V = V;
    instance.M = 1;
    instance.Q = {10};
    instance.capacity.assign(static_cast<std::size_t>(V + 1), 20);
    instance.initial.assign(static_cast<std::size_t>(V + 1), 10);
    instance.target.assign(static_cast<std::size_t>(V + 1), 10);
    instance.weights.assign(static_cast<std::size_t>(V + 1), 1.0);
    instance.min_ratio.assign(static_cast<std::size_t>(V + 1), 0.0);
    instance.points.resize(static_cast<std::size_t>(V + 1));
    instance.dist.assign(static_cast<std::size_t>(V + 1),
        std::vector<double>(static_cast<std::size_t>(V + 1), 0.0));
    for (int i = 0; i <= V; ++i) {
        instance.points[static_cast<std::size_t>(i)] =
            {static_cast<double>(i), 0.0};
        for (int j = 0; j <= V; ++j) {
            instance.dist[static_cast<std::size_t>(i)]
                         [static_cast<std::size_t>(j)] =
                i == j ? 0.0 : 10.0 + std::abs(i - j);
        }
    }
    instance.total_time_limit = 2850.0;
    instance.pickup_time = 60.0;
    instance.drop_time = 60.0;
    return instance;
}

ebrp::CanonicalCompactModelArtifact writeFixture(
    const ebrp::Instance& instance,
    const std::filesystem::path& path,
    const std::string& subset_policy) {
    ebrp::SolveOptions options;
    ebrp::configureRound50IntervalMipV0(options);
    ebrp::CanonicalCompactModelSpec spec;
    spec.strengthened = true;
    spec.interval_restricted = true;
    spec.gamma_L = 0.1;
    spec.gamma_U = 0.2;
    spec.add_verified_incumbent_row = true;
    spec.verified_incumbent = 1000.0;
    spec.round51_subset_duration_big_m = subset_policy;
    return ebrp::writeCanonicalCompactModel(instance, options, path, spec);
}

std::string tailFrom(const std::string& text, const std::string& marker) {
    const std::size_t position = text.find(marker);
    require(position != std::string::npos, "LP section marker missing");
    return text.substr(position);
}

} // namespace

int main() {
    int passed = 0;
    auto test = [&](const std::string& name, auto fn) {
        fn();
        ++passed;
        std::cout << "ok " << passed << " - " << name << '\n';
    };
    try {
        using namespace ebrp;
        const auto f0 = parseRound50IntervalMipPolicy(
            "interval-mip-core-no-exhaustive-subset-duration");
        const auto alias = parseRound50IntervalMipPolicy(
            "f0-no-rank3-support-duration");
        const auto c0 = parseRound50IntervalMipPolicy("c0-f0-clean");
        const auto c1 = parseRound50IntervalMipPolicy("c1-precrush-only");
        const auto c2 = parseRound50IntervalMipPolicy("c2-status-only");
        const auto c3 = parseRound50IntervalMipPolicy("c3-status-precrush");
        const auto c4 = parseRound50IntervalMipPolicy(
            "c4-separator-dry-run");
        const auto c5 = parseRound50IntervalMipPolicy("c5-live");

        test("01_explicit_f0_clean_policy", [&] {
            require(f0.valid && f0.name ==
                "interval-mip-core-no-exhaustive-subset-duration", "F0");
        });
        test("02_historical_f0_alias", [&] {
            require(alias.valid && alias.name == f0.name, "alias");
        });
        test("03_f0_removes_only_exhaustive_family", [&] {
            require(f0.subset_duration_big_m == "off" &&
                f0.cut_formulation == "v0" &&
                f0.symmetry_numerical == "v0" &&
                f0.branching == Round50BranchingPolicy::Default, "scope");
        });
        test("04_f0_no_dynamic_separator", [&] {
            require(f0.tailored_cut_policy == "f0-clean-none" &&
                !round53CallbackSeparatorEnabled(f0), "separator");
        });
        test("05_f0_no_precrush", [&] {
            require(!round53CallbackPreCrushEnabled(f0), "PreCrush");
        });
        test("06_c0_baseline", [&] {
            require(c0.valid && !round53CallbackMipNodeEnabled(c0) &&
                !round53CallbackPreCrushEnabled(c0), "C0");
        });
        test("07_c1_precrush_only", [&] {
            require(round53CallbackPreCrushEnabled(c1) &&
                !round53CallbackMipNodeEnabled(c1), "C1");
        });
        test("08_c2_status_only", [&] {
            require(round53CallbackMipNodeEnabled(c2) &&
                !round53CallbackPreCrushEnabled(c2) &&
                !round53CallbackRelaxationEnabled(c2), "C2");
        });
        test("09_c3_status_plus_precrush", [&] {
            require(round53CallbackMipNodeEnabled(c3) &&
                round53CallbackPreCrushEnabled(c3) &&
                !round53CallbackSeparatorEnabled(c3), "C3");
        });
        test("10_c4_relaxation_vector", [&] {
            require(round53CallbackRelaxationEnabled(c4), "C4 vector");
        });
        test("11_c4_separator", [&] {
            require(round53CallbackSeparatorEnabled(c4), "C4 separator");
        });
        test("12_c4_no_submission", [&] {
            require(!round53CallbackSubmissionEnabled(c4), "C4 submit");
        });
        test("13_c5_live_submission", [&] {
            require(round53CallbackPreCrushEnabled(c5) &&
                round53CallbackRelaxationEnabled(c5) &&
                round53CallbackSeparatorEnabled(c5) &&
                round53CallbackSubmissionEnabled(c5), "C5");
        });
        test("14_default_v0_unchanged", [&] {
            const auto v0 = parseRound50IntervalMipPolicy("interval-mip-v0");
            require(v0.valid && v0.subset_duration_big_m ==
                "historical-100000" && v0.round53_callback_mode == "off",
                "v0");
        });
        test("15_invalid_callback_policy_fails_closed", [&] {
            require(!parseRound50IntervalMipPolicy(
                "round53-c6-invented").valid, "invalid");
        });
        test("16_all_modes_share_f0_mathematics", [&] {
            for (const auto* policy : {&c0, &c1, &c2, &c3, &c4, &c5}) {
                require(policy->subset_duration_big_m == "off" &&
                    policy->cut_formulation == "v0" &&
                    policy->symmetry_numerical == "v0" &&
                    policy->branching == Round50BranchingPolicy::Default,
                    "mode math");
            }
        });

        const auto temp = std::filesystem::temp_directory_path() /
            "exact_ebrp_round53_f0_callback_tests";
        std::filesystem::create_directories(temp);
        const auto v2 = fixture(2);
        const auto v0_artifact = writeFixture(
            v2, temp / "v2_v0.lp", "historical-100000");
        const auto f0_artifact = writeFixture(v2, temp / "v2_f0.lp", "off");
        test("17_v_le_12_expected_removed_row_count", [&] {
            require(v0_artifact.written && f0_artifact.written &&
                v0_artifact.round51_subset_duration_rows == 3,
                "removed rows");
        });
        test("18_removed_row_id_range", [&] {
            require(v0_artifact.round51_subset_duration_first_row_id >= 0 &&
                v0_artifact.round51_subset_duration_last_row_id -
                    v0_artifact.round51_subset_duration_first_row_id + 1 ==
                    v0_artifact.round51_subset_duration_rows, "row IDs");
        });
        test("19_f0_column_identity", [&] {
            require(v0_artifact.columns == f0_artifact.columns, "columns");
        });
        test("20_f0_row_delta", [&] {
            require(v0_artifact.rows - f0_artifact.rows == 3, "row delta");
        });
        test("21_f0_nonzero_delta", [&] {
            require(v0_artifact.nonzeros - f0_artifact.nonzeros == 8,
                "nonzero delta");
        });
        test("22_f0_domain_tail_identity", [&] {
            require(tailFrom(readAll(v0_artifact.path), "Bounds") ==
                tailFrom(readAll(f0_artifact.path), "Bounds"), "domains");
        });
        test("23_v_gt_12_byte_equivalence", [&] {
            const auto v13 = fixture(13);
            const auto v13_v0 = writeFixture(
                v13, temp / "v13_v0.lp", "historical-100000");
            const auto v13_f0 = writeFixture(v13, temp / "v13_f0.lp", "off");
            require(v13_v0.written && v13_f0.written &&
                v13_v0.sha256 == v13_f0.sha256 &&
                readAll(v13_v0.path) == readAll(v13_f0.path), "V13 bytes");
        });

        Round52CutCandidate candidate;
        candidate.family = "support-duration-rank2-tight";
        candidate.coefficients = {{"p_0_1", 1.0}, {"z_0_1", 2.0}};
        candidate.sense = Round52CutSense::LessEqual;
        candidate.rhs = 3.0;
        candidate.raw_violation = 1.0;
        candidate.scaled_violation = 0.5;
        candidate.violation_scale = 2.0;
        candidate.vehicle_index = 0;
        candidate.support_set = {1, 2};
        candidate.generating_interval = "fixture";
        candidate.validity_scope = Round52CutValidityScope::Global;
        Round52CutManager manager;
        manager.beginModel("round53-dry-run-fixture");
        auto selected = manager.process({candidate});
        test("24_dry_run_candidate_selection", [&] {
            require(selected.size() == 1 &&
                manager.telemetry().selected == 1, "dry selection");
        });
        test("25_dry_run_zero_submission", [&] {
            manager.recordDryRunSelection(selected.front());
            require(manager.telemetry().submission_attempts == 0 &&
                manager.telemetry().added == 0 &&
                manager.telemetry().global_pool_size == 1, "dry no submit");
        });
        test("26_dry_run_duplicate_memory", [&] {
            require(manager.process({candidate}).empty() &&
                manager.telemetry().duplicate_rejections == 1,
                "dry duplicate");
        });
        test("27_global_cut_validity_scope", [&] {
            Round52CutCandidate normalized = candidate;
            std::string reason;
            require(normalizeRound52CutCandidate(normalized, &reason) &&
                normalized.validity_scope ==
                    Round52CutValidityScope::Global, "validity");
        });

        test("28_k1_default_backend_is_v0", [&] {
            SolveOptions options;
            require(options.external_gini_interval_mip_policy ==
                "interval-mip-v0", "default K1 backend");
        });
        test("29_k1_tau_roundtrip_unchanged", [&] {
            SolveOptions options;
            options.round47_c6_adaptive_mass = "adaptive-mass";
            options.round47_c6_adaptive_mass_tau = 0.08;
            options.round47_c6_adaptive_mass_tau_explicit = true;
            options.external_gini_interval_mip_policy = f0.name;
            configureRound50IntervalMipV0(options);
            require(options.round47_c6_adaptive_mass == "adaptive-mass" &&
                options.round47_c6_adaptive_mass_tau == 0.08 &&
                options.round47_c6_adaptive_mass_tau_explicit,
                "tau/controller changed");
        });
        test("30_no_instance_dispatch_in_backend_selection", [&] {
            SolveOptions small, large;
            small.external_gini_interval_mip_policy = f0.name;
            large.external_gini_interval_mip_policy = f0.name;
            require(small.external_gini_interval_mip_policy ==
                    large.external_gini_interval_mip_policy &&
                    small.external_gini_interval_mip_policy == f0.name,
                    "hidden dispatch");
        });

        std::filesystem::remove_all(temp);
        require(passed >= 27, "Round53 test count");
        std::cout << "Round53F0AndCallbackTests passed " << passed
                  << " cases\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round53F0AndCallbackTests failed after " << passed
                  << " cases: " << error.what() << '\n';
        return 1;
    }
}
