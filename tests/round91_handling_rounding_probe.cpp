// Round 91 B3 G2 fixture exporter. This program only writes one canonical LP;
// it never creates a solver environment or calls Optimize. Not a CTest test.
#include "CanonicalCompactModel.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "PaperK1AmSf.hpp"
#include "Parser.hpp"
#include "Round50IntervalMip.hpp"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

constexpr double kLambda = 0.15;
constexpr double kExpectedObjective = 17.0 / 60.0; // Cross-check only.

const char* kInput =
    "5 2 [5, 5]\n"
    "capacities = [0, 2, 2, 2, 2, 2]\n"
    "initial = [0, 2, 2, 2, 2, 2]\n"
    "target = [0, 1, 1, 1, 1, 1]\n"
    "weights = [0, 1, 1, 1, 1, 1]\n"
    "min_ratio = [0, 0, 0, 0, 0, 0]\n"
    "distances = [\n"
    "0 0 0 0 0 0\n"
    "0 0 0 0 0 0\n"
    "0 0 0 0 0 0\n"
    "0 0 0 0 0 0\n"
    "0 0 0 0 0 0\n"
    "0 0 0 0 0 0\n"
    "]\n";

void require(bool ok, const std::string& what) {
    if (!ok) throw std::runtime_error(what);
}

void writeFile(const fs::path& path, const std::string& value) {
    std::ofstream stream(path, std::ios::binary);
    require(static_cast<bool>(stream), "cannot open " + path.string());
    stream << value;
    stream.flush();
    require(static_cast<bool>(stream), "cannot write " + path.string());
}

std::string json(const std::string& value) {
    std::string out = "\"";
    constexpr char hex[] = "0123456789abcdef";
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') {
            out += '\\';
            out += static_cast<char>(c);
        } else if (c < 0x20) {
            out += "\\u00";
            out += hex[c >> 4];
            out += hex[c & 15];
        } else {
            out += static_cast<char>(c);
        }
    }
    return out + '"';
}

std::string sourceReceipt(const fs::path& root) {
    std::vector<fs::path> files = {
        "tests/round91_handling_rounding_probe.cpp", "CMakeLists.txt"};
    for (const char* directory : {"include", "src"}) {
        for (const auto& entry : fs::recursive_directory_iterator(root / directory)) {
            if (entry.is_regular_file()) files.push_back(fs::relative(entry.path(), root));
        }
    }
    std::sort(files.begin(), files.end());
    std::string out;
    for (const fs::path& rel : files) {
        const fs::path path = root / rel;
        require(fs::is_regular_file(path), "missing source " + path.string());
        if (!out.empty()) out += ",\n";
        out += "    " + json(rel.generic_string()) + ": " +
               json(ebrp::fileSha256(path));
    }
    return out;
}

std::string variableReceipt() {
    std::string out = "[\"G\"";
    const auto append = [&](const std::string& name) { out += "," + json(name); };
    for (int i = 1; i <= 5; ++i) {
        append("Y_" + std::to_string(i));
        for (int y = 0; y <= 2; ++y)
            append("state_" + std::to_string(i) + "_" + std::to_string(y));
        for (int k = 0; k <= 1; ++k) {
            append("p_" + std::to_string(k) + "_" + std::to_string(i));
            append("d_" + std::to_string(k) + "_" + std::to_string(i));
        }
    }
    return out + "]";
}

} // namespace

int main(int argc, char** argv) {
    try {
        require(argc == 5 && std::string(argv[1]) == "--out" &&
                    std::string(argv[3]) == "--source-root",
                "usage: Round91HandlingRoundingProbe --out NEW_DIR --source-root REPO");
        const fs::path output = fs::absolute(argv[2]);
        const fs::path source_root = fs::canonical(argv[4]);
        require(!fs::exists(output), "output directory already exists");
        require(fs::exists(output.parent_path()), "output parent absent");
        require(fs::create_directory(output), "cannot create output directory");
        const std::string sources_before = sourceReceipt(source_root);

        const fs::path input_path = output / "five_station_input.txt";
        writeFile(input_path, kInput);
        const auto in = ebrp::parseInstanceFile(input_path, 5.0, 1.0, 1.0);
        require(in.V == 5 && in.M == 2 && in.Q == std::vector<int>({5, 5}),
                "parsed dimensions differ from fixed fixture");
        require(ebrp::hasMetricTravelLowerBounds(in), "zero travel lost metric identity");
        for (int i = 1; i <= 5; ++i) {
            require(in.initial[i] == 2 && in.capacity[i] == 2 &&
                        in.target[i] == 1 && in.weights[i] == 1.0,
                    "parsed station differs from fixed fixture");
        }
        for (const auto& row : in.dist)
            for (double d : row) require(d == 0.0, "travel is not zero");

        const std::vector<ebrp::RoutePlan> routes = {
            {0, {0, 1, 2, 0}, {{1, 1, 0}, {2, 1, 0}}},
            {1, {0, 3, 4, 0}, {{3, 1, 0}, {4, 1, 0}}}};
        const auto verified = ebrp::verifySolution(in, routes, kLambda);
        require(verified.feasible && verified.original_solution_feasible &&
                    verified.original_objective_recomputed &&
                    std::isfinite(verified.objective) && verified.objective > 0.0,
                "physical witness rejected");
        require(verified.final_inventory ==
                    std::vector<int>({0, 1, 1, 1, 1, 2}),
                "physical witness inventory differs");

        ebrp::SolveOptions options;
        // main.cpp's paper-gf-tailored-bc foundation precedes the K1 override.
        // These are its remaining model-writer-affecting interval flags.
        options.interval_oracle_low_gini_tightening = true;
        options.interval_oracle_objective_cutoff_row = true;
        options.interval_oracle_symmetry_breaking = true;
        options.interval_oracle_service_operation_tightening = true;
        options.service_operation_min_handling_cuts = true;
        ebrp::configurePaperK1AmSfOverrides(options); // Includes canonical F0.
        options.algorithm_preset = "research-round83-vds-equal-net-exchange";
        options.external_gini_interval_mip_policy = "round55-vd-p";
        options.lambda = kLambda;
        const auto policy = ebrp::parseRound50IntervalMipPolicy(
            options.external_gini_interval_mip_policy);
        require(policy.valid && policy.station_state_formulation == "vd-p" &&
                    policy.subset_duration_big_m == "off" &&
                    policy.sparse_family_removal == "none",
                "not the inherited R83 VD-P/F0 formulation");

        ebrp::CanonicalCompactModelSpec spec;
        spec.strengthened = true;
        spec.interval_restricted = true;
        spec.gamma_L = 0.0;
        spec.gamma_U = std::min(
            verified.objective, static_cast<double>(in.V - 1) / in.V);
        spec.add_verified_incumbent_row = true;
        spec.verified_incumbent = verified.objective; // Never 17/60 constant.
        spec.incumbent_epsilon = 0.0;
        spec.round51_subset_duration_big_m = policy.subset_duration_big_m;
        spec.station_state_formulation = policy.station_state_formulation;
        spec.sparse_family_removal = policy.sparse_family_removal;
        const auto artifact = ebrp::writeCanonicalCompactModel(
            in, options, output / "canonical_L0.lp", spec);
        require(artifact.written && artifact.station_state_formulation == "vd-p" &&
                    artifact.interval_restricted && artifact.verified_incumbent_row &&
                    artifact.model_scope ==
                        "complete_original_compact_milp_intersected_with_static_gini_interval" &&
                    artifact.sha256 == ebrp::fileSha256(artifact.path),
                "canonical artifact invalid: " + artifact.failure_reason);

        require(sourceReceipt(source_root) == sources_before,
                "source files changed during fixture export");
        const std::string binary_sha = ebrp::fileSha256(fs::absolute(argv[0]));
        const std::string input_sha = ebrp::fileSha256(input_path);
        require(binary_sha.size() == 64 && input_sha.size() == 64,
                "binary or input hash unavailable");
        std::ofstream manifest(output / "export_manifest.json", std::ios::binary);
        require(static_cast<bool>(manifest), "cannot open export manifest");
        manifest << std::setprecision(17)
            << "{\n  \"diagnostic\": \"round91_fixed_five_station_handling_rounding\",\n"
            << "  \"optimizer_calls\": 0,\n"
            << "  \"source_root\": " << json(source_root.string()) << ",\n"
            << "  \"source_files_sha256\": {\n" << sources_before << "\n  },\n"
            << "  \"binary_sha256\": " << json(binary_sha) << ",\n"
            << "  \"input_path\": " << json(input_path.string()) << ",\n"
            << "  \"input_sha256\": " << json(input_sha) << ",\n"
            << "  \"instance\": {\"V\":5,\"M\":2,\"Q\":[5,5],"
               "\"capacity\":[0,2,2,2,2,2],\"initial\":[0,2,2,2,2,2],"
               "\"target\":[0,1,1,1,1,1],\"weights\":[0,1,1,1,1,1],"
               "\"T\":5,\"pickup_time\":1,\"drop_time\":1,"
               "\"travel\":\"all_zero_6_by_6\"},\n"
            << "  \"witness_routes\": [{\"vehicle\":0,\"nodes\":[0,1,2,0],"
               "\"pickup\":[[1,1],[2,1]]},{\"vehicle\":1,"
               "\"nodes\":[0,3,4,0],\"pickup\":[[3,1],[4,1]]}],\n"
            << "  \"witness\": {\"feasible\":true,\"final_inventory\":[0,1,1,1,1,2],"
            << "\"G\":" << verified.G << ",\"P\":" << verified.P
            << ",\"F\":" << verified.objective
            << ",\"expected_F_check_only\":" << kExpectedObjective
            << ",\"expected_F_residual\":" <<
                   verified.objective - kExpectedObjective << "},\n"
            << "  \"effective_options\": {\"configuration\":"
               "\"configurePaperK1AmSfOverrides_from_SolveOptions_defaults\","
               "\"algorithm_preset_label\":\"research-round83-vds-equal-net-exchange\","
               "\"external_gini_interval_mip_policy\":\"round55-vd-p\","
               "\"paper_gf_foundation_interval_flags\":true,"
               "\"global_gini_tree_root_connectivity_flow_variant\":"
            << json(options.global_gini_tree_root_connectivity_flow_variant)
            << ",\"global_gini_tree_root_connectivity_flow\":"
            << (options.global_gini_tree_root_connectivity_flow ? "true" : "false")
            << ",\"lambda\":" << options.lambda << "},\n"
            << "  \"spec\": {\"strengthened\":true,\"interval_restricted\":true,"
               "\"gamma_L\":" << spec.gamma_L << ",\"gamma_U\":" << spec.gamma_U
            << ",\"verified_incumbent_row\":true,\"verified_incumbent\":"
            << spec.verified_incumbent
            << ",\"incumbent_epsilon\":0,\"station_state_formulation\":"
            << json(spec.station_state_formulation)
            << ",\"round51_subset_duration_big_m\":"
            << json(spec.round51_subset_duration_big_m)
            << ",\"sparse_family_removal\":"
            << json(spec.sparse_family_removal) << "},\n"
            << "  \"lp_path\": " << json(artifact.path.string()) << ",\n"
            << "  \"lp_sha256\": " << json(artifact.sha256) << ",\n"
            << "  \"required_variable_names\": " << variableReceipt() << ",\n"
            << "  \"row_signature\": " << json(artifact.row_signature) << ",\n"
            << "  \"model_scope\": " << json(artifact.model_scope) << ",\n"
            << "  \"rows\": " << artifact.rows << ", \"columns\": "
            << artifact.columns << ", \"nonzeros\": " << artifact.nonzeros << "\n}\n";
        manifest.flush();
        require(static_cast<bool>(manifest), "cannot persist export manifest");
        std::cout << "canonical LP " << artifact.sha256 << " verified UB "
                  << std::setprecision(17) << verified.objective << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "round91 fixture export failed: " << error.what() << '\n';
        return 1;
    }
}
