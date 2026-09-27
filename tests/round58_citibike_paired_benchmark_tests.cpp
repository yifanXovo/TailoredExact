#include "PaperK1AmSf.hpp"
#include "Parser.hpp"
#include "Round50IntervalMip.hpp"
#include "Round53CallbackIsolation.hpp"
#include "Round58Benchmark.hpp"

#include <cmath>
#include <filesystem>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>

int main() {
    try {
        int checks = 0;
        auto check = [&](bool value, const std::string& label) {
            if (!value) throw std::runtime_error(label);
            ++checks;
        };
        const std::filesystem::path root = EXACT_EBRP_SOURCE_DIR;
        const auto v8 = ebrp::parseInstanceFile(
            root / "reference/citibike443-regional-v1/instances/V08/"
                   "cb443_V08_compact_r1_balanced_M01_Q20.txt",
            3600.0, 60.0, 60.0);
        const auto v20 = ebrp::parseInstanceFile(
            root / "reference/citibike443-regional-v1/instances/V20/"
                   "cb443_V20_regional_r1_shortage_M02_Q30.txt",
            10800.0, 60.0, 60.0);
        const auto v50 = ebrp::parseInstanceFile(
            root / "reference/citibike443-regional-v1/instances/V50/"
                   "cb443_V50_compact_r2_surplus_M07_Q30.txt",
            18000.0, 60.0, 60.0);
        check(v8.V == 8 && v8.M == 1 && v8.Q == std::vector<int>{20},
              "1 V8 CitiBike parser sentinel");
        check(v20.V == 20 && v20.M == 2 && v20.Q == std::vector<int>({30, 30}),
              "2 V20 CitiBike parser sentinel");
        check(v50.V == 50 && v50.M == 7 && v50.Q.size() == 7,
              "3 V50 CitiBike parser sentinel");
        check(v8.total_time_limit == 3600.0 &&
              v20.total_time_limit == 10800.0 &&
              v50.total_time_limit == 18000.0,
              "4 route horizons remain model inputs");
        check(v8.distance_convention.find("speed factor 1.5") != std::string::npos,
              "5 parser distance convention frozen");

        ebrp::SolveOptions k1;
        ebrp::configurePaperK1AmSfOverrides(k1);
        check(k1.algorithm_preset == "paper-k1-am-sf", "6 K1 preset identity");
        check(k1.initial_gini_interval_count == 1, "7 K0=1");
        check(k1.split_point_rule == "midpoint", "8 midpoint splitting");
        check(k1.split_score_rule == "balanced-normalized-closure",
              "9 balanced normalized closure score");
        check(std::fabs(k1.split_threshold - 0.08) < 1e-12, "10 tau=0.08");
        check(k1.external_gini_backend == "gurobi", "11 native Gurobi inner backend");
        check(k1.gurobi_threads == 1 && k1.gurobi_seed == 0 &&
              k1.gurobi_presolve == -1, "12 native solver settings");
        const auto f0 = ebrp::parseRound50IntervalMipPolicy(
            k1.external_gini_interval_mip_policy);
        check(f0.valid && f0.subset_duration_big_m == "off", "13 F0-CLEAN identity");
        check(!ebrp::round53CallbackMipNodeEnabled(f0), "14 no MIPNODE user cuts");
        check(!ebrp::round53CallbackSubmissionEnabled(f0), "15 no dynamic cut submission");
        check(!ebrp::round53CallbackPreCrushEnabled(f0), "16 default PreCrush");

        ebrp::SolveOptions pgrb;
        pgrb.method = "gurobi";
        pgrb.plain_baseline = true;
        pgrb.gurobi_threads = 1;
        pgrb.gurobi_seed = 0;
        pgrb.gurobi_presolve = -1;
        pgrb.gurobi_hga_start = false;
        check(pgrb.method == "gurobi" && pgrb.plain_baseline,
              "17 direct P-GRB identity");
        check(!pgrb.gurobi_hga_start && pgrb.incumbent_json_path.empty() &&
              pgrb.hga_incumbent_path.empty() &&
              pgrb.external_incumbent_path.empty(),
              "18 no imported or heuristic route source");
        check(!pgrb.gcap_seed_cplex && !pgrb.round24_research_mode,
              "19 no tailored or research mechanisms");

        const auto gap = ebrp::computeRound58Gap(90.0, 100.0);
        check(gap.computable && gap.absolute_gap == 10.0, "20 absolute-gap formula");
        check(std::fabs(gap.relative_gap - 0.1) < 1e-12,
              "21 relative-gap formula");
        check(std::fabs(gap.scaled_gap - 0.1) < 1e-12,
              "22 scaled-gap formula");
        check(!ebrp::computeRound58Gap(std::nullopt, 100.0).computable,
              "23 missing lower bound rejects gaps");
        check(!ebrp::computeRound58Gap(90.0, std::nullopt).computable,
              "24 missing verified upper bound rejects gaps");
        check(ebrp::computeRound58Gap(101.0, 100.0).absolute_gap == 0.0,
              "25 inverted numerical residual clamps at zero");

        check(ebrp::round58FirstMethod(std::string(64, '2')) == "k1_am_sf",
              "26 even SHA digit selects K1 first");
        check(ebrp::round58FirstMethod(std::string(64, 'b')) == "pgrb",
              "27 odd SHA digit selects P-GRB first");
        bool invalid_sha_rejected = false;
        try { (void)ebrp::round58FirstMethod("invalid"); }
        catch (const std::invalid_argument&) { invalid_sha_rejected = true; }
        check(invalid_sha_rejected, "28 invalid scenario identity rejected");

        ebrp::Round58ScreenPairInput pair;
        auto decision = ebrp::decideRound58ScreenExtension(pair);
        check(decision.extend_k1_to_10800 && decision.extend_pgrb_to_10800,
              "29 neither-certified pair extends both");
        pair.k1_certified = true;
        pair.pgrb_certified = true;
        decision = ebrp::decideRound58ScreenExtension(pair);
        check(!decision.extend_k1_to_10800 && !decision.extend_pgrb_to_10800,
              "30 both-certified pair does not extend");
        pair.pgrb_certified = false;
        pair.pgrb_relative_gap = 0.10;
        pair.k1_completion_seconds = 100.0;
        decision = ebrp::decideRound58ScreenExtension(pair);
        check(decision.extend_pgrb_to_10800, "31 one-certified near-gap extension");
        pair.pgrb_relative_gap = 0.10001;
        pair.k1_completion_seconds = 2700.0;
        decision = ebrp::decideRound58ScreenExtension(pair);
        check(decision.extend_pgrb_to_10800, "32 hard certified-time extension gate");
        pair.k1_completion_seconds = 2699.9;
        decision = ebrp::decideRound58ScreenExtension(pair);
        check(!decision.extend_pgrb_to_10800,
              "33 one-certified large-gap pair is censored");

        auto near = ebrp::decideRound58NearConvergenceExtension(false, 0.05, 10800);
        check(near.extend && near.next_cap_seconds == 21600,
              "34 <=5% at 10800 authorizes 21600");
        near = ebrp::decideRound58NearConvergenceExtension(false, 0.08, 10800);
        check(near.extend && near.next_cap_seconds == 16200,
              "35 5-10% at 10800 authorizes 16200");
        near = ebrp::decideRound58NearConvergenceExtension(false, 0.11, 10800);
        check(!near.extend, "36 >10% does not extend");
        near = ebrp::decideRound58NearConvergenceExtension(false, 0.05, 16200);
        check(near.extend && near.next_cap_seconds == 21600,
              "37 <=5% at 16200 authorizes final cap");
        near = ebrp::decideRound58NearConvergenceExtension(false, 0.051, 16200);
        check(!near.extend, "38 >5% at 16200 stops");
        near = ebrp::decideRound58NearConvergenceExtension(false, 0.0, 21600);
        check(!near.extend, "39 six-hour hard cap");
        near = ebrp::decideRound58NearConvergenceExtension(true, 0.0, 10800);
        check(!near.extend, "40 certified run never extends");

        check(ebrp::classifyRound58Pair(true, true, {}, {}, 10, 20) ==
                  "both_certified_k1_faster", "41 both-certified K1 faster class");
        check(ebrp::classifyRound58Pair(false, true, {}, {}) ==
                  "pgrb_only_certified", "42 P-GRB-only class");
        check(ebrp::classifyRound58Pair(false, false, 0.02, 0.04) ==
                  "neither_certified_k1_better_bound", "43 neither-certified bound class");
        check(ebrp::classifyRound58Pair(false, false, {}, 0.04) ==
                  "invalid_or_uncomputable", "44 invalid pair class");
        check(checks == 44, "45 Round58 semantic check count");
        std::cout << "Round58CitiBikePairedBenchmarkTests passed "
                  << checks << " checks\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round58CitiBikePairedBenchmarkTests failed: "
                  << error.what() << '\n';
        return 1;
    }
}

