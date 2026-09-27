#include "Round48K1AMF.hpp"
#include "Instance.hpp"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

void writeModel(const std::filesystem::path& path,
                double g_lower, double g_upper,
                double y_lower, double y_upper,
                double r_lower, double r_upper,
                double product_upper,
                double wsp_lower, double wsp_upper) {
    std::ofstream out(path);
    out << "Minimize\n obj: G\nSubject To\n c1: G >= 0\nBounds\n"
        << " " << g_lower << " <= G <= " << g_upper << "\n"
        << " " << y_lower << " <= Y_1 <= " << y_upper << "\n"
        << " " << r_lower << " <= r_1 <= " << r_upper << "\n"
        << " 0 <= e_1 <= 2\n"
        << " 0 <= e_2 <= 0\n"
        << " 0 <= h_1_2 <= 3\n"
        << " 0 <= bit_1_0 <= 1\n"
        << " 0 <= prod_1_0 <= " << product_upper << "\n"
        << " 0 <= p_0_1 <= 4\n"
        << " 0 <= d_0_1 <= 4\n"
        << " " << wsp_lower << " <= W_SP <= " << wsp_upper << "\n"
        << " 0 <= W_GS <= 5\n"
        << " 0 <= unrelated <= 9\nGenerals\n Y_1\nEnd\n";
}

ebrp::C6CurrentSplitDecision baseDecision(
        double left, double right, double tolerance = 1e-12) {
    ebrp::C6CurrentSplitDecision out;
    out.valid = true;
    out.adaptive_mass_enabled = true;
    out.g_left = left;
    out.g_right = right;
    out.adaptive_eta = std::min(left, right);
    out.adaptive_mu = (left + right) / 2.0;
    out.adaptive_mass_score = out.adaptive_eta * out.adaptive_mu;
    out.adaptive_score_tolerance = tolerance;
    out.adaptive_rho = 1.0;
    const bool strict = std::min(left, right) > 0.0;
    out.split_immediately = out.adaptive_mass_score + tolerance >=
        ebrp::kRound48K1AMFTau;
    out.run_child_bound_target = strict && !out.split_immediately;
    out.launch_exact_closure = !strict;
    out.child_bound_target = 0.5;
    out.reason = out.split_immediately ? "am_split" :
        (strict ? "am_native_target" : "am_exact_close");
    return out;
}

} // namespace

int main() {
    try {
        int checks = 0;
        auto check = [&](bool value, const std::string& message) {
            require(value, message);
            ++checks;
        };

        check(ebrp::round48AMFEligibleFamily("Y_12") == "final_inventory",
              "eligible Y registry");
        check(ebrp::round48AMFEligibleFamily("r_2") == "station_ratio",
              "eligible ratio registry");
        check(ebrp::round48AMFEligibleFamily("e_3") == "absolute_deviation",
              "eligible deviation registry");
        check(ebrp::round48AMFEligibleFamily("h_1_2") ==
                  "pairwise_ratio_difference",
              "eligible pair registry");
        check(ebrp::round48AMFEligibleFamily("bit_1_5") == "inventory_bit" &&
                  ebrp::round48AMFEligibleFamily("prod_1_5") ==
                      "gini_inventory_product",
              "eligible bit/product registry");
        check(ebrp::round48AMFEligibleFamily("p_0_1") == "pickup_movement" &&
                  ebrp::round48AMFEligibleFamily("d_0_1") == "drop_movement",
              "eligible movement registry");
        check(ebrp::round48AMFEligibleFamily("W_SP") ==
                  "ratio_penalty_product",
              "eligible product registry");
        check(ebrp::round48AMFEligibleFamily("G").empty() &&
                  ebrp::round48AMFEligibleFamily("W_GS").empty(),
              "Gini and diagnostic variables excluded");

        const auto temp = std::filesystem::temp_directory_path() /
            "exactebrp_round48_k1_amf_tests";
        std::filesystem::create_directories(temp);
        const auto parent = temp / "parent.lp";
        const auto left = temp / "left.lp";
        const auto right = temp / "right.lp";
        writeModel(parent, 0.0, 1.0, 0.0, 10.0, 0.0, 2.0,
                   1.0, 0.0, 20.0);
        writeModel(left, 0.0, 0.5, 2.0, 8.0, 0.0, 2.0,
                   0.5, 0.0, 10.0);
        writeModel(right, 0.5, 1.0, 0.0, 10.0, 0.0, 2.0,
                   1.0, 5.0, 15.0);
        const ebrp::AMFFormulationProfile profile =
            ebrp::buildRound48AMFFormulationProfile(
                parent, left, right, 1e-7);
        check(profile.valid, "finite effective profiles valid");
        check(profile.excluded_gini_variable_count == 1,
              "Gini coordinate fully excluded");
        check(profile.eligible_variable_count == 9,
              "eligible variables deduplicated and complete");
        check(std::none_of(
                  profile.variables.begin(), profile.variables.end(),
                  [](const ebrp::AMFVariableContraction& item) {
                      return item.variable == "e_2";
                  }),
              "zero parent-width variable excluded");
        check(profile.family_counts.at("final_inventory") == 1 &&
                  profile.family_counts.at("gini_inventory_product") == 1,
              "per-family diagnostic counts");
        check(std::fabs(profile.variables[0].width_tolerance - 1e-7) < 1e-15,
              "certificate-derived width tolerance");
        check(profile.phi_left >= 0.0 && profile.phi_left <= 1.0 &&
                  profile.phi_right >= 0.0 && profile.phi_right <= 1.0,
              "phi range");
        check(std::fabs(profile.phi_left - (0.4 + 0.5 + 0.5) / 9.0) < 1e-12,
              "equal variable weighting");
        check(std::fabs(profile.phi_right - 0.5 / 9.0) < 1e-12,
              "right contraction reconstruction");
        check(profile.fixed_left_count == 0 && profile.fixed_right_count == 0,
              "fixed-variable counts");

        writeModel(right, 0.5, 1.0, -1.0, 11.0, 0.0, 2.0,
                   1.0, 5.0, 15.0);
        const auto nonmonotone = ebrp::buildRound48AMFFormulationProfile(
            parent, left, right, 1e-7);
        check(!nonmonotone.valid && nonmonotone.invalid_variable_count == 1 &&
                  nonmonotone.phi_left == 0.0 && nonmonotone.phi_right == 0.0,
              "child-domain nonmonotonicity fails closed");
        writeModel(right, 0.5, 1.0, 0.0, 10.0, 0.0, 2.0,
                   1.0, 5.0, 15.0);
        writeModel(right, 0.5, 1.0, 0.0,
                   std::numeric_limits<double>::infinity(), 0.0, 2.0,
                   1.0, 5.0, 15.0);
        const auto nonfinite = ebrp::buildRound48AMFFormulationProfile(
            parent, left, right, 1e-7);
        check(!nonfinite.valid, "nonfinite effective bound rejected");
        writeModel(right, 0.5, 1.0, 0.0, 10.0, 0.0, 2.0,
                   1.0, 5.0, 15.0);

        ebrp::AMFFormulationProfile zero;
        zero.valid = true;
        zero.failure_reason = "none";
        const auto am = baseDecision(0.20, 0.60);
        const auto reduced = ebrp::evaluateK1AMFDecision(am, zero);
        check(reduced.valid && std::fabs(reduced.s_amf - reduced.s_am) < 1e-15,
              "AMF reduces to AM for phi zero");
        ebrp::AMFFormulationProfile credit = zero;
        credit.phi_left = 0.5;
        credit.phi_right = 0.25;
        const auto adjusted = ebrp::evaluateK1AMFDecision(am, credit);
        check(adjusted.eta_hat + 1e-15 >= adjusted.eta &&
                  adjusted.eta_hat <= std::max(adjusted.g_left,
                                               adjusted.g_right) + 1e-15,
              "eta_hat mathematical bounds");
        check(adjusted.s_amf + 1e-15 >= adjusted.s_am,
              "S_AMF dominates S_AM");
        check(adjusted.gtilde_left > adjusted.g_left &&
                  adjusted.gtilde_right == adjusted.g_right,
              "weak-child symmetric credit");
        ebrp::AMFFormulationProfile mirrored_profile = zero;
        mirrored_profile.phi_left = 0.25;
        mirrored_profile.phi_right = 0.5;
        const auto mirrored = ebrp::evaluateK1AMFDecision(
            baseDecision(0.60, 0.20), mirrored_profile);
        check(std::fabs(mirrored.s_amf - adjusted.s_amf) < 1e-15,
              "left-right symmetry");
        const auto equal = ebrp::evaluateK1AMFDecision(
            baseDecision(0.4, 0.4), credit);
        check(std::fabs(equal.s_amf - equal.s_am) < 1e-15,
              "equal gains receive no formulation change");

        const double equality_gain = std::sqrt(ebrp::kRound48K1AMFTau);
        const auto equality = ebrp::evaluateK1AMFDecision(
            baseDecision(equality_gain, equality_gain, 0.0), zero);
        check(equality.amf_split, "split at tau equality");
        const auto below = ebrp::evaluateK1AMFDecision(
            baseDecision(0.10, 0.20, 0.0), zero);
        check(!below.amf_split, "retain below tau");
        ebrp::AMFFormulationProfile invalid;
        invalid.valid = false;
        invalid.failure_reason = "incomplete_effective_bounds:test";
        invalid.phi_left = 1.0;
        invalid.phi_right = 1.0;
        const auto fallback = ebrp::evaluateK1AMFDecision(am, invalid);
        check(fallback.valid && fallback.fallback_to_am &&
                  fallback.s_amf == fallback.s_am,
              "invalid profile exact AM fallback");
        check(fallback.decision_hash.find('.') == std::string::npos,
              "decision hash excludes runtime telemetry");

        auto native = baseDecision(0.10, 0.20, 0.0);
        const auto native_amf = ebrp::evaluateK1AMFDecision(native, zero);
        ebrp::applyK1AMFDecision(native, native_amf);
        check(native.run_child_bound_target && native.child_bound_target == 0.5,
              "native target preserved without rescue");
        auto exact = baseDecision(0.0, 0.40, 0.0);
        const auto exact_amf = ebrp::evaluateK1AMFDecision(exact, zero);
        ebrp::applyK1AMFDecision(exact, exact_amf);
        check(exact.launch_exact_closure,
              "exact-parent closure preserved without rescue");
        auto rescued_base = baseDecision(0.10, 0.70, 0.0);
        ebrp::AMFFormulationProfile rescue_profile = zero;
        rescue_profile.phi_left = 0.5;
        const auto rescue = ebrp::evaluateK1AMFDecision(
            rescued_base, rescue_profile);
        ebrp::applyK1AMFDecision(rescued_base, rescue);
        check(rescue.rescue_activated && rescued_base.split_immediately &&
                  !rescued_base.run_child_bound_target &&
                  !rescued_base.launch_exact_closure,
              "formulation rescue applies one midpoint split decision");

        ebrp::SolveOptions options;
        check(options.round48_k1_amf == "off" &&
                  options.round47_c6_adaptive_mass == "off",
              "Round 48 and historical Round 47 default off");
        options.round48_k1_amf = "k1-amf";
        options.round40_c6_coarse_start = "k1-adaptive";
        options.round47_c6_adaptive_mass = "adaptive-mass";
        check(options.round40_c6_coarse_start == "k1-adaptive" &&
                  std::fabs(ebrp::kRound48K1AMFTau - 0.07915) < 1e-15,
              "K0=1 path and one shared tau");
        check(options.round47_c6_adaptive_mass != "adaptive-mass-contraction",
              "AMC remains off");
        check(options.round45_point_rule == "midpoint" &&
                  !options.c6_normalized_split_threshold_explicit,
              "midpoint only and no rho cap");
        ebrp::SolveResult certificate_state;
        certificate_state.external_gini_tree_root_coverage_valid = true;
        certificate_state.external_gini_tree_parent_child_coverage_valid = true;
        certificate_state.strict_certified_original_problem = true;
        ebrp::applyK1AMFDecision(rescued_base, rescue);
        check(certificate_state.external_gini_tree_root_coverage_valid &&
                  certificate_state.external_gini_tree_parent_child_coverage_valid &&
                  certificate_state.strict_certified_original_problem,
              "AMF decision leaves certificate and coverage state untouched");
        check(certificate_state.round48_amf_extra_lp_count == 0 &&
                  certificate_state.round48_amf_extra_mip_count == 0,
              "zero additional LP and MIP calls by default");
        check(options.round45_adaptive_parametric_partition == "off" &&
                  options.round47_c6_adaptive_mass == "adaptive-mass" &&
                  ebrp::SolveOptions{}.round47_c6_adaptive_mass == "off",
              "historical Round 45 through 47 defaults remain unchanged");
        check(std::string(ebrp::kRound48AMFProfileVersion) ==
                  "round48-canonical-interval-sensitive-v1",
              "formulation profile version frozen");
        check(checks >= 28, "Round 48 required check count");
        std::filesystem::remove_all(temp);
        std::cout << "Round48K1AMFTests passed " << checks << " checks\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round48K1AMFTests failed: " << error.what() << '\n';
        return 1;
    }
}
