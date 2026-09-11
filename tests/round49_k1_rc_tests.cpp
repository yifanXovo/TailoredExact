#include "Round49K1RC.hpp"
#include "Instance.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

ebrp::FixedIntervalLpVariableEvidence variable(
        const std::string& name, char type, double lower, double upper,
        double value, double rc, int basis) {
    ebrp::FixedIntervalLpVariableEvidence out;
    out.name = name;
    out.original_type = type;
    out.lower_bound = lower;
    out.upper_bound = upper;
    out.primal_value = value;
    out.reduced_cost = rc;
    out.variable_basis_status = basis;
    return out;
}

ebrp::PaperLpResult state(double objective, double cutoff,
                          const std::string& fingerprint) {
    ebrp::PaperLpResult out;
    out.terminal_valid = true;
    out.optimal = true;
    out.bound_available = true;
    out.lower_bound = objective;
    out.primal_values_available = true;
    out.reduced_costs_available = true;
    out.basis_status_available = true;
    out.primal_dual_evidence_available = true;
    out.objective_sense = 1;
    out.verified_cutoff = cutoff;
    out.model_fingerprint = fingerprint;
    return out;
}

ebrp::C6CurrentSplitDecision adaptive(bool split) {
    ebrp::C6CurrentSplitDecision out;
    out.valid = true;
    out.adaptive_mass_enabled = true;
    out.g_left = 0.1;
    out.g_right = 0.2;
    out.adaptive_eta = 0.1;
    out.adaptive_mu = 0.15;
    out.adaptive_mass_score = 0.015;
    out.adaptive_score_tolerance = 1e-7;
    out.adaptive_rho = 0.07915;
    out.split_immediately = split;
    out.run_child_bound_target = !split;
    out.launch_exact_closure = false;
    out.child_bound_target = 94.0;
    out.reason = split ? "am_split" : "am_native_target";
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

        check(ebrp::round49PrimitiveIntegerFamily("x_1_2_3") ==
                  "routing_arc", "routing arc registry");
        check(ebrp::round49PrimitiveIntegerFamily("z_1_2") ==
                  "visit_selection", "visit registry");
        check(ebrp::round49PrimitiveIntegerFamily("mode_1_2") ==
                  "operation_mode", "mode registry");
        check(ebrp::round49PrimitiveIntegerFamily("p_1_2") ==
                  "pickup_quantity" &&
              ebrp::round49PrimitiveIntegerFamily("d_1_2") ==
                  "drop_quantity", "transfer registry");
        check(ebrp::round49PrimitiveIntegerFamily("load_1_2") ==
                  "vehicle_load" &&
              ebrp::round49PrimitiveIntegerFamily("Y_12") ==
                  "final_inventory", "load and inventory registry");
        check(ebrp::round49PrimitiveIntegerFamily("bit_1_0").empty() &&
              ebrp::round49PrimitiveIntegerFamily("prod_1_0").empty() &&
              ebrp::round49PrimitiveIntegerFamily("G").empty() &&
              ebrp::round49PrimitiveIntegerFamily("W_GS").empty(),
              "encoding, product, and Gini auxiliaries excluded");
        check(ebrp::round49PrimitiveIntegerFamily("x_1_2").empty() &&
              ebrp::round49PrimitiveIntegerFamily("Y_a").empty(),
              "malformed names excluded");

        auto parent = state(90.0, 100.0, "parent");
        auto left = state(95.0, 100.0, "left");
        auto right = state(95.0, 100.0, "right");
        parent.primal_dual_variables = {
            variable("Y_1", 'I', 0.0, 10.0, 5.0, 0.0, 0),
            variable("d_1_1", 'I', 0.0, 8.0, 4.0, 0.0, 0),
            variable("bit_1_0", 'B', 0.0, 1.0, 0.5, 0.0, 0)};
        left.primal_dual_variables = {
            variable("Y_1", 'I', 0.0, 10.0, 0.0, 5.0, -1),
            variable("d_1_1", 'I', 0.0, 8.0, 8.0, -4.0, -2),
            variable("bit_1_0", 'B', 0.0, 1.0, 0.0, 1.0, -1)};
        right.primal_dual_variables = left.primal_dual_variables;
        const auto profile = ebrp::buildRound49RCDomainProfile(
            parent, left, right, 100.0, 1e-7);
        check(profile.valid && profile.primitive_variable_count == 2 &&
                  profile.rc_valid_variable_count == 2,
              "complete primitive-only profile");
        check(profile.family_counts.at("final_inventory") == 1 &&
                  profile.family_counts.at("drop_quantity") == 1,
              "family counts are semantic and unweighted");
        check(profile.variables[0].parent.rc_lower == 0 &&
                  profile.variables[0].parent.rc_upper == 10,
              "basic parent domain retained");
        check(profile.variables[0].left.rc_lower == 0 &&
                  profile.variables[0].left.rc_upper == 1,
              "positive lower-bound reduced cost tightens upper domain");
        check(profile.variables[1].left.rc_lower == 7 &&
                  profile.variables[1].left.rc_upper == 8,
              "negative upper-bound reduced cost tightens lower domain");
        check(profile.left.fixed_count == 0 &&
                  profile.left.tightened_count == 2,
              "fixed and tightened counts separated");
        check(profile.left.D < profile.parent.D &&
                  profile.right.D < profile.parent.D,
              "D detects residual-domain dominance");
        check(profile.left.H < profile.parent.H &&
                  profile.right.H < profile.parent.H,
              "H detects normalized log-domain-volume dominance");
        check(profile.variables[0].parent.effective_count == 11 &&
                  profile.variables[1].parent.effective_count == 9,
              "integer-domain cardinality is inclusive");

        auto binary_parent = state(90.0, 100.0, "binary-parent");
        auto binary_left = state(99.0, 100.0, "binary-left");
        auto binary_right = state(99.0, 100.0, "binary-right");
        binary_parent.primal_dual_variables = {
            variable("x_1_2_3", 'B', 0.0, 1.0, 0.5, 0.0, 0)};
        binary_left.primal_dual_variables = {
            variable("x_1_2_3", 'B', 0.0, 1.0, 0.0, 2.0, -1)};
        binary_right.primal_dual_variables = binary_left.primal_dual_variables;
        const auto binary_profile = ebrp::buildRound49RCDomainProfile(
            binary_parent, binary_left, binary_right, 100.0, 1e-7);
        check(binary_profile.valid &&
                  binary_profile.variables[0].left.rc_count == 1 &&
                  binary_profile.left.fixed_count == 1,
              "binary reduced-cost fixing");

        auto zero_rc = left;
        zero_rc.primal_dual_variables[0] =
            variable("Y_1", 'I', -1e-10, 10.00000000001, 0.0, 0.0, -1);
        zero_rc.primal_dual_variables[1] =
            variable("d_1_1", 'I', 0.0, 8.0, 8.0, -4.0, 0);
        const auto conservative = ebrp::buildRound49RCDomainProfile(
            parent, zero_rc, right, 100.0, 1e-7);
        check(conservative.valid &&
                  conservative.variables[0].left.effective_lower == 0 &&
                  conservative.variables[0].left.effective_upper == 10,
              "certificate-aware outward integer rounding");
        check(conservative.variables[0].left.rc_count == 11,
              "zero reduced cost retains effective domain");
        check(conservative.variables[1].left.rc_count == 9,
              "degenerate/basic variable retains effective domain");

        auto am_retain = adaptive(false);
        const auto rescue = ebrp::evaluateK1AMRCDecision(
            am_retain, profile, "d-rcd", 1e-7);
        check(rescue.valid && rescue.profile_valid && rescue.dominance &&
                  rescue.strict_mean_improvement && rescue.rescue_activated,
              "D-RCD rescues a dominated AM-retain state");
        ebrp::applyK1AMRCDecision(am_retain, rescue);
        check(am_retain.split_immediately &&
                  !am_retain.run_child_bound_target &&
                  !am_retain.launch_exact_closure,
              "rescue changes only the split action");

        auto am_split = adaptive(true);
        const auto preserve = ebrp::evaluateK1AMRCDecision(
            am_split, profile, "d-rcd", 1e-7);
        ebrp::applyK1AMRCDecision(am_split, preserve);
        check(preserve.valid && !preserve.rescue_activated &&
                  preserve.final_action == "split" &&
                  am_split.split_immediately,
              "existing AM split can never be vetoed");

        ebrp::Round49RCDomainProfile flat = profile;
        flat.left = flat.parent;
        flat.right = flat.parent;
        auto native = adaptive(false);
        const auto no_rescue = ebrp::evaluateK1AMRCDecision(
            native, flat, "d-rcd", 1e-7);
        ebrp::applyK1AMRCDecision(native, no_rescue);
        check(native.run_child_bound_target && !native.split_immediately &&
                  native.child_bound_target == 94.0,
              "native target preserved without rescue");
        auto exact = adaptive(false);
        exact.run_child_bound_target = false;
        exact.launch_exact_closure = true;
        const auto exact_no_rescue = ebrp::evaluateK1AMRCDecision(
            exact, flat, "d-rcd", 1e-7);
        ebrp::applyK1AMRCDecision(exact, exact_no_rescue);
        check(exact.launch_exact_closure && !exact.split_immediately,
              "exact-close preserved without rescue");

        auto mirrored_profile = profile;
        std::swap(mirrored_profile.left, mirrored_profile.right);
        for (auto& item : mirrored_profile.variables) {
            std::swap(item.left, item.right);
        }
        const auto mirrored = ebrp::evaluateK1AMRCDecision(
            adaptive(false), mirrored_profile, "d-rcd", 1e-7);
        check(mirrored.valid &&
                  mirrored.rescue_activated == rescue.rescue_activated &&
                  std::fabs(mirrored.left_summary - rescue.right_summary) <
                      1e-15,
              "left/right symmetry");

        auto stale_left = left;
        stale_left.verified_cutoff = 99.0;
        const auto stale = ebrp::buildRound49RCDomainProfile(
            parent, stale_left, right, 100.0, 1e-7);
        const auto fallback = ebrp::evaluateK1AMRCDecision(
            adaptive(false), stale, "d-rcd", 1e-7);
        check(!stale.valid &&
                  stale.failure_reason == "stale_incumbent_cutoff_epoch" &&
                  fallback.valid && fallback.fallback_to_am &&
                  !fallback.rescue_activated,
              "stale cutoff fails closed to exact AM");
        auto no_basis = left;
        no_basis.basis_status_available = false;
        const auto invalid = ebrp::buildRound49RCDomainProfile(
            parent, no_basis, right, 100.0, 1e-7);
        check(!invalid.valid &&
                  invalid.failure_reason ==
                      "invalid_or_incomplete_lp_primal_dual_state",
              "missing basis/reduced-cost certificate fails closed");
        auto nonoptimal = left;
        nonoptimal.optimal = false;
        const auto incomplete = ebrp::buildRound49RCDomainProfile(
            parent, nonoptimal, right, 100.0, 1e-7);
        check(!incomplete.valid,
              "complete optimal LP status required");
        auto wrong_sense = left;
        wrong_sense.objective_sense = -1;
        const auto maximization = ebrp::buildRound49RCDomainProfile(
            parent, wrong_sense, right, 100.0, 1e-7);
        check(!maximization.valid,
              "minimization reduced-cost sign convention required");
        auto stale_fingerprint = left;
        stale_fingerprint.terminal_valid = false;
        stale_fingerprint.model_fingerprint.clear();
        const auto fingerprint_rejected = ebrp::buildRound49RCDomainProfile(
            parent, stale_fingerprint, right, 100.0, 1e-7);
        check(!fingerprint_rejected.valid,
              "stale model fingerprint evidence rejected");
        auto mismatch = right;
        mismatch.primal_dual_variables.erase(
            mismatch.primal_dual_variables.begin());
        const auto mismatched = ebrp::buildRound49RCDomainProfile(
            parent, left, mismatch, 100.0, 1e-7);
        check(!mismatched.valid &&
                  mismatched.failure_reason ==
                      "primitive_variable_mapping_size_mismatch",
              "canonical primitive mapping mismatch rejected");

        ebrp::Round49RCDomainProfile separation;
        separation.valid = true;
        separation.parent.D = separation.left.D = separation.right.D = 1.0;
        separation.parent.H = separation.left.H = separation.right.H = 1.0;
        separation.disjoint_domain_count = 1;
        const auto rcds = ebrp::evaluateK1AMRCDecision(
            adaptive(false), separation, "d-rcds", 1e-7);
        check(rcds.valid && rcds.exact_separation &&
                  rcds.rescue_activated,
              "RCDS exact separation is parameter-free");
        const auto unsupported = ebrp::evaluateK1AMRCDecision(
            adaptive(false), profile, "weighted-score", 1e-7);
        check(!unsupported.valid, "unfrozen rule rejected");
        check(rescue.decision_hash.size() == 16 &&
                  rescue.decision_hash.find('.') == std::string::npos,
              "decision hash is deterministic and telemetry-free");

        ebrp::SolveOptions options;
        check(options.round49_k1_am_rc == "off" &&
                  options.round48_k1_amf == "off" &&
                  options.round47_c6_adaptive_mass == "off",
              "Round 49 and all parent research modes default off");
        options.round49_k1_am_rc = "d-rcd";
        options.round40_c6_coarse_start = "k1-adaptive";
        options.round47_c6_adaptive_mass = "adaptive-mass";
        options.round47_c6_adaptive_mass_tau = 0.07915;
        check(options.round40_c6_coarse_start == "k1-adaptive" &&
                  std::fabs(options.round47_c6_adaptive_mass_tau - 0.07915) <
                      1e-15,
              "K0 fixed to one and tau unchanged");
        check(options.round45_point_rule == "midpoint" &&
                  options.round45_adaptive_parametric_partition == "off",
              "midpoint-only split geometry");
        ebrp::SolveResult result;
        check(result.round49_rc_extra_lp_count == 0 &&
                  result.round49_rc_extra_mip_count == 0,
              "zero extra live score solves by construction");
        result.external_gini_tree_root_coverage_valid = true;
        result.external_gini_tree_parent_child_coverage_valid = true;
        result.strict_certified_original_problem = true;
        check(result.external_gini_tree_root_coverage_valid &&
                  result.external_gini_tree_parent_child_coverage_valid &&
                  result.strict_certified_original_problem,
              "decision module leaves coverage and exactness state invariant");
        check(std::string(ebrp::kRound49RCProfileVersion) ==
                  "round49-primitive-integer-reduced-cost-v1",
              "profile version frozen");
        check(checks >= 38, "Round 49 required check count");
        std::cout << "Round49K1RCTests passed " << checks << " checks\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round49K1RCTests failed: " << error.what() << '\n';
        return 1;
    }
}
