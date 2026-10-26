#include "CanonicalCompactModel.hpp"
#include "Evaluator.hpp"
#include "PaperK1AmSf.hpp"
#include "Parser.hpp"
#include "Result.hpp"
#include "Round50IntervalMip.hpp"
#include "Round53CallbackIsolation.hpp"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

std::string readText(const std::filesystem::path& path) {
    std::ifstream stream(path, std::ios::binary);
    std::ostringstream out;
    out << stream.rdbuf();
    return out.str();
}

} // namespace

int main() {
    try {
        int checks = 0;
        auto check = [&](bool value, const std::string& label) {
            if (!value) throw std::runtime_error(label);
            ++checks;
        };

        const std::filesystem::path root = EXACT_EBRP_SOURCE_DIR;
        const auto input = root /
            "reference/round56_paper_candidate/fleet_variants/V08/"
            "r56_V08_M01_Q30.txt";
        const ebrp::Instance short_t =
            ebrp::parseInstanceFile(input, 1800.0, 60.0, 60.0);
        const ebrp::Instance long_t =
            ebrp::parseInstanceFile(input, 18000.0, 60.0, 60.0);
        check(short_t.total_time_limit == 1800.0, "1 --T parse target");
        check(long_t.total_time_limit == 18000.0, "2 alternate --T parse target");
        check(short_t.pickup_time == 60.0, "3 pickup-time propagation");
        check(short_t.drop_time == 60.0, "4 drop-time propagation");
        check(short_t.V == 8, "5 V parse");
        check(short_t.M == 1, "6 M parse");
        check(short_t.Q.size() == 1, "7 Q vector length equals M");
        check(short_t.Q[0] == 30, "8 vehicle capacity parse");
        check(short_t.capacity == long_t.capacity, "9 T leaves capacities unchanged");
        check(short_t.initial == long_t.initial, "10 T leaves initial inventory unchanged");
        check(short_t.target == long_t.target, "11 T leaves targets unchanged");
        check(short_t.weights == long_t.weights, "12 T leaves weights unchanged");
        check(short_t.min_ratio == long_t.min_ratio, "13 T leaves min-ratio unchanged");
        check(short_t.points == long_t.points, "14 T leaves coordinates unchanged");
        check(short_t.dist == long_t.dist, "15 T leaves distances unchanged");
        check(short_t.distance_convention.find("speed factor 1.5") !=
                  std::string::npos,
              "16 distance convention explicit");

        ebrp::SolveOptions preset;
        ebrp::configurePaperK1AmSfOverrides(preset);
        check(preset.algorithm_preset == "paper-k1-am-sf", "17 stable preset");
        check(preset.k1_am_sf_controller_enabled, "18 first-class controller");
        check(preset.initial_gini_interval_count == 1, "19 K0=1");
        check(preset.split_point_rule == "midpoint", "20 midpoint splitting");
        check(preset.split_score_rule == "balanced-normalized-closure",
              "21 balanced closure score");
        check(preset.split_threshold == 0.08, "22 tau=0.08");
        check(preset.external_gini_interval_mip_policy ==
                  "interval-mip-core-no-exhaustive-subset-duration",
              "23 F0-CLEAN policy");
        check(preset.external_gini_backend == "gurobi", "24 Gurobi backend");
        check(preset.gurobi_threads == 1, "25 Gurobi thread contract");
        check(preset.gurobi_seed == 0, "26 Gurobi seed contract");
        check(preset.gurobi_presolve == -1, "27 Presolve Auto");
        check(!preset.round24_research_mode, "28 research mode off");
        check(preset.round48_k1_amf == "off", "29 gamma-veto family off");
        check(preset.round49_k1_am_rc == "off", "30 route candidate off");
        const auto f0 = ebrp::parseRound50IntervalMipPolicy(
            preset.external_gini_interval_mip_policy);
        check(f0.valid, "31 stable inner policy valid");
        check(f0.subset_duration_big_m == "off", "32 historical exhaustive family off");
        check(!ebrp::round53CallbackMipNodeEnabled(f0), "33 callback MIPNODE off");
        check(!ebrp::round53CallbackSubmissionEnabled(f0), "34 dynamic cuts off");
        check(!ebrp::round53CallbackPreCrushEnabled(f0), "35 default PreCrush");

        const auto temp = std::filesystem::temp_directory_path() /
            "exact_ebrp_round56_paper_benchmark_tests";
        std::filesystem::create_directories(temp);
        ebrp::CanonicalCompactModelSpec spec;
        spec.strengthened = true;
        spec.interval_restricted = true;
        spec.gamma_L = 0.0;
        spec.gamma_U = 1.0;
        spec.add_verified_incumbent_row = false;
        spec.round51_subset_duration_big_m = "off";
        spec.station_state_formulation = "bit-product";
        const auto short_model = ebrp::writeCanonicalCompactModel(
            short_t, preset, temp / "T1800.lp", spec);
        const auto long_model = ebrp::writeCanonicalCompactModel(
            long_t, preset, temp / "T18000.lp", spec);
        check(short_model.written && long_model.written, "36 both T models build");
        check(short_model.sha256 != long_model.sha256, "37 T enters model identity");
        const std::string short_lp = readText(short_model.path);
        const std::string long_lp = readText(long_model.path);
        check(short_lp.find("<= 1800") != std::string::npos,
              "38 parent/child model uses T=1800");
        check(long_lp.find("<= 18000") != std::string::npos,
              "39 native/exact model uses T=18000");
        check(short_model.round51_subset_duration_rows == 0,
              "40 F0 omission unchanged by T");

        std::vector<ebrp::RoutePlan> unused(1);
        unused[0].vehicle = 0;
        unused[0].nodes = {0, 0};
        const auto verification = ebrp::verifySolution(short_t, unused, 0.15);
        check(verification.original_solution_feasible, "41 unused vehicle feasible");
        check(verification.routes_start_end_depot, "42 depot closure verified");
        check(verification.load_feasible, "43 unused load feasible");
        check(verification.duration_feasible, "44 unused duration feasible");
        check(verification.route_duration.size() == 1 &&
                  std::fabs(verification.route_duration[0]) < 1e-12,
              "45 unused duration reconstructs to zero");

        ebrp::SolveResult result;
        result.instance_name = short_t.name;
        result.input_path = short_t.path;
        result.scenario_id = "r56_test";
        result.route_time_limit_seconds = short_t.total_time_limit;
        result.solver_process_cap_seconds = 3600.0;
        result.pickup_time_seconds = short_t.pickup_time;
        result.drop_time_seconds = short_t.drop_time;
        result.distance_convention = short_t.distance_convention;
        result.mathematical_instance_sha256 = std::string(64, 'a');
        result.run_identity_sha256 = std::string(64, 'b');
        result.method = "gcap-frontier";
        result.algorithm_preset = "paper-k1-am-sf";
        result.status = "time_limit";
        result.routes = unused;
        result.final_inventory = verification.final_inventory;
        result.verification = verification;
        const std::string json = ebrp::resultToJson(result);
        check(json.find("\"route_time_limit_seconds\": 1800") !=
                  std::string::npos,
              "46 T serialization");
        check(json.find("\"solver_process_cap_seconds\": 3600") !=
                  std::string::npos,
              "47 process-cap serialization");
        check(json.find("\"mathematical_instance_sha256\": \"" +
                        std::string(64, 'a') + "\"") != std::string::npos,
              "48 mathematical identity serialization");
        check(json.find("\"run_identity_sha256\": \"" +
                        std::string(64, 'b') + "\"") != std::string::npos,
              "49 run identity serialization");
        check(json.find("\"nodes\": [0, 0]") != std::string::npos,
              "50 native unused-route roundtrip");
        check(json.find("\"operations\": []") != std::string::npos,
              "51 operation-sequence roundtrip");
        check(json.find("\"distance_convention\":") != std::string::npos,
              "52 distance convention serialization");
        check(json.find("\"scenario_id\": \"r56_test\"") !=
                  std::string::npos,
              "53 scenario identity serialization");
        check(json.find("\"pickup_time_seconds\": 60") != std::string::npos &&
                  json.find("\"drop_time_seconds\": 60") != std::string::npos,
              "54 service-time serialization");
        check(checks >= 49, "55 dedicated Round56 check-count floor");

        std::cout << "Round56PaperBenchmarkTests passed " << checks
                  << " checks\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round56PaperBenchmarkTests failed: "
                  << error.what() << '\n';
        return 1;
    }
}
