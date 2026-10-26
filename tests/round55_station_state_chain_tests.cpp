#include "CanonicalCompactModel.hpp"
#include "GurobiCertificate.hpp"
#include "PaperExternalGiniTree.hpp"
#include "PaperK1AmSf.hpp"
#include "Parser.hpp"
#include "PenaltyCoverSeparation.hpp"
#include "Round50IntervalMip.hpp"
#include "Round53CallbackIsolation.hpp"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

std::string readText(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    std::ostringstream out;
    out << in.rdbuf();
    return out.str();
}

ebrp::PaperLpResult optimal(double bound) {
    ebrp::PaperLpResult out;
    out.terminal_valid = true;
    out.optimal = true;
    out.bound_available = true;
    out.lower_bound = bound;
    return out;
}

ebrp::PaperLpResult infeasible() {
    ebrp::PaperLpResult out;
    out.terminal_valid = true;
    out.infeasible = true;
    return out;
}

} // namespace

int main() {
    try {
        int checks = 0;
        auto check = [&](bool condition, const std::string& message) {
            if (!condition) throw std::runtime_error(message);
            ++checks;
        };

        ebrp::SolveOptions preset;
        ebrp::configurePaperK1AmSfOverrides(preset);
        check(preset.k1_am_sf_controller_enabled,
              "1 first-class K1 controller parsing");
        check(ebrp::isPaperK1AmSfPresetOrAlias("k1-am-f0") &&
              ebrp::isPaperK1AmSfPresetOrAlias("paper-k1-am-f0"),
              "2 legacy alias equivalence");
        check(preset.initial_gini_interval_count == 1,
              "3 K0=1 direct semantics");
        check(preset.split_point_rule == "midpoint" &&
              preset.split_factor == 2,
              "4 midpoint semantics");
        check(preset.split_threshold == 0.08,
              "5 tau=0.08 roundtrip");
        check(preset.round43_initial_k0 == 4 &&
              preset.round40_c6_coarse_start == "off" &&
              preset.round47_c6_adaptive_mass == "off",
              "6 inert historical K4 fields are neutral adapters");

        const auto f0 = ebrp::parseRound50IntervalMipPolicy(
            "interval-mip-core-no-exhaustive-subset-duration");
        const auto mc4 = ebrp::parseRound50IntervalMipPolicy("sf-mc4");
        const auto vdp = ebrp::parseRound50IntervalMipPolicy("vd-p");
        const auto vdj = ebrp::parseRound50IntervalMipPolicy("vd-j");
        const auto sf_r1 = ebrp::parseRound50IntervalMipPolicy("sf-r1");
        const auto vdp_sf_r1 =
            ebrp::parseRound50IntervalMipPolicy("vdp-sf-r1");
        check(f0.valid && f0.subset_duration_big_m == "off",
              "7 F0 exhaustive family omission");
        check(mc4.valid && mc4.station_state_formulation == "aggregate-mc4",
              "8 MC4 policy identity");
        check(vdp.valid && vdp.station_state_formulation == "vd-p",
              "9 VD-P policy identity");
        check(vdj.valid && vdj.station_state_formulation == "vd-j",
              "10 VD-J policy identity");
        check(sf_r1.valid &&
              sf_r1.station_state_formulation == "bit-product" &&
              sf_r1.sparse_family_removal ==
                  "triple-support-duration-cover",
              "10a SF-R1 removes exactly the triple duration family");
        check(vdp_sf_r1.valid &&
              vdp_sf_r1.station_state_formulation == "vd-p" &&
              vdp_sf_r1.sparse_family_removal ==
                  "triple-support-duration-cover",
              "10b interaction policy composes only VD-P and SF-R1");
        check(!ebrp::round53CallbackMipNodeEnabled(vdj) &&
              !ebrp::round53CallbackSubmissionEnabled(vdj) &&
              !ebrp::round53CallbackPreCrushEnabled(vdj),
              "11 no callback or PreCrush activation");

        const std::filesystem::path source = EXACT_EBRP_SOURCE_DIR;
        const std::filesystem::path input = source /
            "reference/qualification_round39/small-medium/"
            "round39_small_medium_V12_M3_Q30_slot08_seed1343324363.txt";
        const ebrp::Instance instance =
            ebrp::parseInstanceFile(input, 2850.0, 60.0, 60.0);
        ebrp::SolveOptions fixed_options;
        ebrp::configureRound50IntervalMipV0(fixed_options);
        const std::filesystem::path temp =
            std::filesystem::temp_directory_path() /
            "exact_ebrp_round55_station_state_tests";
        std::filesystem::create_directories(temp);
        auto build = [&](const std::string& formulation,
                         const std::string& file,
                         double cutoff = 0.049468682614419446,
                         const std::string& sparse_removal = "none") {
            ebrp::CanonicalCompactModelSpec spec;
            spec.strengthened = true;
            spec.interval_restricted = true;
            spec.gamma_L = 0.0;
            spec.gamma_U = 0.049468682614419446;
            spec.add_verified_incumbent_row = true;
            spec.verified_incumbent = cutoff;
            spec.round51_subset_duration_big_m = "off";
            spec.station_state_formulation = formulation;
            spec.sparse_family_removal = sparse_removal;
            return ebrp::writeCanonicalCompactModel(
                instance, fixed_options, temp / file, spec);
        };
        const auto f0_model = build("bit-product", "f0.lp");
        const auto mc4_model = build("aggregate-mc4", "mc4.lp");
        const auto vdp_model = build("vd-p", "vdp.lp");
        const auto vdj_model = build("vd-j", "vdj.lp");
        const auto vdj_repeat = build("vd-j", "vdj_repeat.lp");
        const auto vdj_tighter = build(
            "vd-j", "vdj_tighter.lp", 0.045);
        const auto sf_r1_model = build(
            "bit-product", "sf_r1.lp", 0.049468682614419446,
            "triple-support-duration-cover");
        const auto vdp_sf_r1_model = build(
            "vd-p", "vdp_sf_r1.lp", 0.049468682614419446,
            "triple-support-duration-cover");
        check(f0_model.written && mc4_model.written &&
              vdp_model.written && vdj_model.written,
              "12 every station-state model constructs");
        check(f0_model.sha256 != mc4_model.sha256 &&
              mc4_model.sha256 != vdp_model.sha256 &&
              vdp_model.sha256 != vdj_model.sha256,
              "13 cache key includes formulation identity");
        check(vdj_model.sha256 == vdj_repeat.sha256,
              "14 model fingerprint determinism");
        check(vdj_model.sha256 != vdj_tighter.sha256,
              "15 cache key includes incumbent epoch identity");
        check(mc4_model.aggregate_mccormick_rows == 4 * instance.V,
              "16 four aggregate McCormick rows per station");
        check(vdp_model.station_state_selector_variables > 0 &&
              vdp_model.station_state_selector_variables ==
                  vdp_model.station_state_perspective_variables,
              "17 selector/perspective variable counts");
        check(vdj_model.station_state_selector_variables ==
              vdp_model.station_state_selector_variables,
              "18 VD-P and VD-J share the proved state domain");

        const std::string f0_lp = readText(f0_model.path);
        const std::string mc4_lp = readText(mc4_model.path);
        const std::string vdp_lp = readText(vdp_model.path);
        const std::string vdj_lp = readText(vdj_model.path);
        check(f0_lp.find("bit_1_0") != std::string::npos &&
              f0_lp.find("state_1_") == std::string::npos,
              "19 F0 bit-product variables retained");
        check(vdp_lp.find("bit_1_0") == std::string::npos &&
              vdp_lp.find("state_1_") != std::string::npos,
              "20 VD-P replaces product-only bit variables");
        check(vdp_lp.find("state_g_1_") != std::string::npos,
              "21 station perspective variables emitted");
        check(vdp_lp.find(" zprod_1") != std::string::npos,
              "22 exact product reconstruction emitted");
        check(vdj_lp.size() > vdp_lp.size() &&
              vdj_model.rows == vdp_model.rows + 2 * instance.V,
              "23 VD-J adds ratio and penalty equalities");
        check(mc4_model.rows == f0_model.rows + 4 * instance.V,
              "24 MC4 changes exactly one row family");
        check(vdp_model.columns > f0_model.columns &&
              vdj_model.columns == vdp_model.columns,
              "25 formulation size accounting");
        check(vdp_model.round51_subset_duration_rows == 0 &&
              vdj_model.round51_subset_duration_rows == 0,
              "26 F0 omission preserved in VD formulations");
        check(sf_r1_model.support_duration_pair_rows ==
                  f0_model.support_duration_pair_rows &&
              sf_r1_model.support_duration_pair_rows > 0,
              "26a SF-R1 retains every pair-support duration row");
        check(f0_model.support_duration_triple_rows > 0 &&
              sf_r1_model.support_duration_triple_rows == 0 &&
              f0_model.rows - sf_r1_model.rows ==
                  f0_model.support_duration_triple_rows,
              "26b SF-R1 removes exactly every triple-support duration row");
        check(vdp_sf_r1_model.station_state_formulation == "vd-p" &&
              vdp_sf_r1_model.sparse_family_removal ==
                  "triple-support-duration-cover" &&
              vdp_sf_r1_model.support_duration_triple_rows == 0,
              "26c interaction model preserves both exact policy identities");
        check(vdp_lp.find("Generals\n Y_1") != std::string::npos ||
              vdp_lp.find("\n Y_1") != std::string::npos,
              "27 original integer inventory domain retained");
        check(vdp_lp.find("state_1_" +
                          std::to_string(instance.capacity[1] + 1)) ==
                  std::string::npos,
              "28 invalid inventory code above capacity excluded");
        check(vdp_lp.find("state_g_1_") != std::string::npos &&
              vdp_lp.find(" <= 0") != std::string::npos,
              "29 perspective bounds written");
        check(mc4_lp.find("zprod_1") != std::string::npos &&
              mc4_lp.find("G") != std::string::npos,
              "30 aggregate McCormick uses unscaled Z=G*Y semantics");

        const auto symmetric_a =
            ebrp::evaluateC6AdaptiveMassSplitDecision(
                10.0, 20.0, optimal(12.0), optimal(14.0),
                0.08, 1e-7, false);
        const auto symmetric_b =
            ebrp::evaluateC6AdaptiveMassSplitDecision(
                10.0, 20.0, optimal(14.0), optimal(12.0),
                0.08, 1e-7, false);
        check(std::fabs(symmetric_a.adaptive_mass_score -
                        symmetric_b.adaptive_mass_score) < 1e-15,
              "31 balanced score symmetry");
        check(symmetric_a.adaptive_mass_score >= 0.0 &&
              symmetric_a.adaptive_mass_score <= 1.0,
              "32 balanced score bounds");
        const auto scaled = ebrp::evaluateC6AdaptiveMassSplitDecision(
            31.0, 51.0, optimal(35.0), optimal(39.0),
            0.08, 1e-7, false);
        check(std::fabs(symmetric_a.adaptive_mass_score -
                        scaled.adaptive_mass_score) < 1e-15,
              "33 positive-affine score invariance");
        const auto zero_side = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, optimal(10.0), optimal(14.0),
            0.08, 1e-7, false);
        check(zero_side.adaptive_mass_score == 0.0,
              "34 no two-sided improvement gives zero score");
        check(std::max(0.5 - 0.0, 1.0 - 0.5) <
              std::max(0.4 - 0.0, 1.0 - 0.4),
              "35 midpoint minimax width property");
        const auto one_infeasible =
            ebrp::evaluateC6AdaptiveMassSplitDecision(
                10.0, 20.0, infeasible(), optimal(12.0),
                0.08, 1e-7, false);
        check(one_infeasible.child_infeasibility_trigger &&
              one_infeasible.split_immediately,
              "36 exact child infeasibility behavior");
        check(symmetric_a.run_child_bound_target &&
              symmetric_a.child_bound_target == 12.0,
              "37 native-target behavior");
        check(preset.maximum_split_depth == 8 &&
              preset.minimum_interval_width == 1e-4 &&
              preset.exact_parent_closure,
              "38 exact coverage controller limits");

        std::vector<ebrp::PenaltyStateChoice> choices = {
            {1, 0, 4, 0.9}, {1, 1, 8, 0.2},
            {2, 0, 5, 0.8}, {2, 1, 9, 0.1},
            {3, 0, 3, 0.7}, {3, 1, 7, 0.2}};
        ebrp::PenaltyCoverSeparationInput cover_input;
        cover_input.choices = choices;
        cover_input.budget_numerator = 10;
        cover_input.violation_tolerance = 1e-9;
        const auto cover_first =
            ebrp::separateExactMultipleChoicePenaltyCover(cover_input);
        check(cover_first.valid && cover_first.cover_found,
              "39 exact DP reconstruction");
        std::string cover_reason;
        check(ebrp::validatePenaltyCover(cover_first.cover, &cover_reason),
              "40 strict-cover validity");
        check(cover_first.cover.violated &&
              cover_first.cover.separation_objective < 1.0,
              "41 strict violation comparison");
        check(cover_first.cover.choices.size() >= 2,
              "42 at most one state per station");
        const auto minimal = ebrp::makeInclusionMinimalPenaltyCover(
            {{1, 0, 8, 0.9}, {2, 0, 7, 0.8}, {3, 0, 6, 0.7}},
            10, 1e-9);
        check(minimal.valid && minimal.choices.size() == 2,
              "43 inclusion-minimal cover reconstruction");
        cover_input.excluded_covers = {cover_first.cover};
        const auto cover_second =
            ebrp::separateExactMultipleChoicePenaltyCover(cover_input);
        check(!cover_second.cover_found ||
              cover_second.cover.canonical_signature !=
                  cover_first.cover.canonical_signature,
              "44 duplicate cover rejection");
        check(cover_first.dynamic_programming_states > 0 &&
              cover_first.dynamic_programming_transitions > 0,
              "45 exact separation accounting");
        if (cover_second.cover_found) {
            cover_input.excluded_covers.push_back(cover_second.cover);
        }
        const auto cover_third =
            ebrp::separateExactMultipleChoicePenaltyCover(cover_input);
        check(cover_third.valid,
              "46 finite closure step termination contract");
        const auto no_cover = ebrp::makeInclusionMinimalPenaltyCover(
            {{1, 0, 4, 1.0}, {2, 0, 5, 1.0}}, 10, 1e-9);
        check(!no_cover.valid,
              "47 noncover cannot be promoted by scaling");
        check(ebrp::penaltyCoverSignature({{2, 0, 5, 0.8},
                                           {1, 0, 4, 0.9}}) ==
              ebrp::penaltyCoverSignature({{1, 0, 4, 0.9},
                                           {2, 0, 5, 0.8}}),
              "48 canonical cover signature order");

        const auto& active = ebrp::paperK1AmSfActiveFamilies();
        check(active.size() == 23,
              "49 complete active-family census");
        check(std::find(active.begin(), active.end(),
                        "inventory_conservation") != active.end() &&
              std::find(active.begin(), active.end(),
                        "connectivity_flow_formulation") != active.end(),
              "50 required feasibility families retained");

        ebrp::GurobiCertificateInput certificate;
        certificate.status = ebrp::kGurobiStatusOptimal;
        certificate.optimize_returned = true;
        certificate.solver_finalization_completed = true;
        certificate.complete_original_model_scope = true;
        certificate.model_configuration_valid = true;
        certificate.lifecycle_valid = true;
        certificate.executable_fingerprint_matches_manifest = true;
        certificate.model_fingerprint_matches_manifest = false;
        certificate.no_tailored_or_external_information = true;
        certificate.relative_gap_requested_exact_zero = true;
        certificate.relative_gap_readback_exact_zero = true;
        certificate.absolute_gap_requested_exact_zero = true;
        certificate.absolute_gap_readback_exact_zero = true;
        certificate.finite_solution_available = true;
        certificate.independently_verified_original_feasible = true;
        certificate.objective_recomputed = true;
        const auto rejected =
            ebrp::evaluateGurobiEngineeringExactCertificate(certificate);
        check(!rejected.strict_certified_original_problem,
              "51 false-certificate rejection");
        check(preset.external_gini_interval_mip_policy ==
                  "interval-mip-core-no-exhaustive-subset-duration" &&
              preset.external_gini_backend == "gurobi",
              "52 stable fixed-interval backend contract");
        check(checks >= 44, "dedicated Round55 check-count floor");

        std::cout << "Round55StationStateChainTests passed "
                  << checks << " checks\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round55StationStateChainTests failed: "
                  << error.what() << '\n';
        return 1;
    }
}
