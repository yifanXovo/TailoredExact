// Zero-Optimize canonical writer qualification. Keep the Round91 L0 fixture
// independent of the Round92 inequality and bind default-off bytes to its
// frozen SHA. A separate Gurobi LP readback checks parsed coefficient rows.
#include "CanonicalCompactModel.hpp"
#include "FileSha256.hpp"
#include "PaperK1AmSf.hpp"
#include "Parser.hpp"
#include "Round50IntervalMip.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
namespace {
const char* kInput =
    "5 2 [5, 5]\n"
    "capacities = [0, 2, 2, 2, 2, 2]\n"
    "initial = [0, 2, 2, 2, 2, 2]\n"
    "target = [0, 1, 1, 1, 1, 1]\n"
    "weights = [0, 1, 1, 1, 1, 1]\n"
    "min_ratio = [0, 0, 0, 0, 0, 0]\n"
    "distances = [\n"
    "0 0 0 0 0 0\n0 0 0 0 0 0\n0 0 0 0 0 0\n"
    "0 0 0 0 0 0\n0 0 0 0 0 0\n0 0 0 0 0 0\n]\n";

void require(bool good, const std::string& why) {
    if (!good) throw std::runtime_error(why);
}

ebrp::CanonicalCompactModelSpec modelSpec(
    double cutoff, ebrp::Round92HandlingActivationCache* cache) {
    const auto policy = ebrp::parseRound50IntervalMipPolicy("round55-vd-p");
    require(policy.valid, "VD-P policy unavailable");
    ebrp::CanonicalCompactModelSpec spec;
    spec.strengthened = true;
    spec.interval_restricted = true;
    spec.gamma_L = 0;
    spec.gamma_U = cutoff;
    spec.add_verified_incumbent_row = true;
    spec.verified_incumbent = cutoff;
    spec.incumbent_epsilon = 0;
    spec.round51_subset_duration_big_m = policy.subset_duration_big_m;
    spec.station_state_formulation = policy.station_state_formulation;
    spec.sparse_family_removal = policy.sparse_family_removal;
    spec.round92_handling_cache = cache;
    return spec;
}
} // namespace

int main(int argc, char** argv) {
    try {
        require(argc == 2, "usage: Round92HandlingIntegrationTests OUTPUT_DIR");
        const fs::path root = fs::absolute(argv[1]);
        require(!fs::exists(root), "output exists; retain previous evidence");
        fs::create_directories(root);
        const fs::path input = root / "five_station_input.txt";
        { std::ofstream out(input, std::ios::binary); out << kInput; }
        const ebrp::Instance instance = ebrp::parseInstanceFile(input, 5, 1, 1);
        ebrp::SolveOptions options;
        options.interval_oracle_low_gini_tightening = true;
        options.interval_oracle_objective_cutoff_row = true;
        options.interval_oracle_symmetry_breaking = true;
        options.interval_oracle_service_operation_tightening = true;
        options.service_operation_min_handling_cuts = true;
        ebrp::configurePaperK1AmSfOverrides(options);
        options.algorithm_preset = "research-round83-vds-equal-net-exchange";
        options.external_gini_interval_mip_policy = "round55-vd-p";
        options.lambda = 0.15;
        const double cutoff = 17.0 / 60.0;
        const auto off = ebrp::writeCanonicalCompactModel(
            instance, options, root / "off.lp", modelSpec(cutoff, nullptr));
        require(off.written && off.rows == 555 &&
                    off.sha256 ==
                    "9872d149c970c99f2b0175929221fb42692c6915a68a4e57e94dd1492fb79a29" &&
                    off.round92_handling_rows == 0,
                "default-off canonical bytes differ from frozen Round91 L0");
        options.round92_handling_activation = true;
        ebrp::Round92HandlingActivationCache cache;
        const auto spec = modelSpec(cutoff, &cache);
        const auto on = ebrp::writeCanonicalCompactModel(
            instance, options, root / "on.lp", spec);
        require(on.written && on.rows == off.rows + instance.M &&
                    on.round92_handling_rows == instance.M &&
                    on.round92_handling_B == 2 &&
                    on.round92_handling_first_row_id >= 0 &&
                    !on.round92_handling_cache_hit && cache.misses == 1,
                "candidate row or first preparation missing");
        const auto reused = ebrp::writeCanonicalCompactModel(
            instance, options, root / "reused.lp", spec);
        require(reused.written && reused.sha256 == on.sha256 &&
                    reused.round92_handling_cache_hit && cache.hits == 1,
                "identical normalized duration failed run-local reuse");
        ebrp::Instance changed = instance;
        changed.dist[0][1] = 1.0;
        const auto invalidated = ebrp::writeCanonicalCompactModel(
            changed, options, root / "invalidated.lp", spec);
        require(invalidated.written && !invalidated.round92_handling_cache_hit &&
                    cache.misses == 2,
                "changed emitted arc coefficient failed to invalidate cache");
        ebrp::SolveOptions wrong_flow = options;
        wrong_flow.global_gini_tree_root_connectivity_flow_variant = "f1";
        const auto rejected = ebrp::writeCanonicalCompactModel(
            instance, wrong_flow, root / "rejected_f1.lp", spec);
        require(!rejected.written &&
                    rejected.failure_reason.find("round92_requires_canonical_interval_F0")
                        != std::string::npos,
                "candidate accepted non-F0 connectivity");
        ebrp::Instance zero_handling = instance;
        zero_handling.pickup_time = zero_handling.drop_time = 0;
        const auto no_row = ebrp::writeCanonicalCompactModel(
            zero_handling, options, root / "zero_handling.lp", spec);
        require(no_row.written && no_row.round92_handling_rows == 0 &&
                    no_row.round92_handling_reason ==
                        "zero_handling_has_no_duration_quantity_bound",
                "valid emitted c=0 must be recorded as no-row");
        std::cout << "Round92 canonical off/on/cache export PASS\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
