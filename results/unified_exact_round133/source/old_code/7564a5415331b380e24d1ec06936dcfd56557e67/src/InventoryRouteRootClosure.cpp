#include "InventoryRouteRootClosure.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <map>
#include <regex>
#include <set>
#include <sstream>

namespace ebrp {
namespace {

std::string lowerAscii(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(),
        [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
    return value;
}

InventoryRouteLpState lpStateFromOutcome(
    const Instance& instance,
    const FixedIntervalMipOutcome& outcome,
    bool& valid,
    std::string& reason) {
    InventoryRouteLpState state;
    state.station_count = instance.V;
    state.vehicle_capacities = instance.Q;
    state.initial_inventory.assign(instance.initial.begin(),
                                   instance.initial.end());
    state.final_inventory.resize(static_cast<std::size_t>(instance.V + 1));
    state.final_inventory_lower.resize(
        static_cast<std::size_t>(instance.V + 1));
    state.final_inventory_upper.resize(
        static_cast<std::size_t>(instance.V + 1));
    std::vector<bool> inventory_seen(static_cast<std::size_t>(instance.V + 1));
    inventory_seen[0] = true;
    const std::regex y_pattern(R"(^Y_([0-9]+)$)");
    const std::regex x_pattern(R"(^x_([0-9]+)_([0-9]+)_([0-9]+)$)");
    for (const auto& variable : outcome.lp_primal_dual_variable_evidence) {
        std::smatch match;
        if (std::regex_match(variable.name, match, y_pattern)) {
            const int station = std::stoi(match[1].str());
            if (station <= 0 || station > instance.V ||
                inventory_seen[static_cast<std::size_t>(station)]) {
                reason = "invalid_or_duplicate_final_inventory_registry";
                return state;
            }
            inventory_seen[static_cast<std::size_t>(station)] = true;
            state.final_inventory[static_cast<std::size_t>(station)] =
                variable.primal_value;
            state.final_inventory_lower[static_cast<std::size_t>(station)] =
                variable.lower_bound;
            state.final_inventory_upper[static_cast<std::size_t>(station)] =
                variable.upper_bound;
        } else if (std::regex_match(variable.name, match, x_pattern)) {
            InventoryRouteArcValue arc;
            arc.vehicle = std::stoi(match[1].str());
            arc.from = std::stoi(match[2].str());
            arc.to = std::stoi(match[3].str());
            arc.value = variable.primal_value;
            state.route_arcs.push_back(arc);
        }
    }
    const bool inventories_complete = std::all_of(
        inventory_seen.begin() + 1, inventory_seen.end(),
        [](bool seen) { return seen; });
    const long long expected_arcs = static_cast<long long>(instance.M) *
        static_cast<long long>(instance.V + 1) * instance.V;
    valid = outcome.lp_terminal_valid && outcome.optimal &&
        outcome.lp_primal_dual_evidence_available && inventories_complete &&
        static_cast<long long>(state.route_arcs.size()) == expected_arcs;
    reason = valid ? "none" :
        (!outcome.lp_terminal_valid ? "lp_terminal_invalid" :
         !outcome.optimal ? "lp_not_optimal" :
         !outcome.lp_primal_dual_evidence_available
             ? "lp_primal_evidence_unavailable" :
         !inventories_complete ? "final_inventory_registry_incomplete" :
         "route_arc_registry_incomplete");
    return state;
}

bool sameSubset(const InventoryRouteCut& left,
                const InventoryRouteCut& right) {
    return left.subset == right.subset;
}

} // namespace

InventoryRouteClosureVariant parseInventoryRouteClosureVariant(
    const std::string& requested) {
    const std::string value = lowerAscii(requested);
    if (value == "ir1" || value == "ir1-mixed-full-closure" ||
        value == "research-ir1-mixed-root-closure") {
        return InventoryRouteClosureVariant::MixedFull;
    }
    if (value == "ir2" || value == "ir2-mixed-projected-full-closure" ||
        value == "research-ir2-mixed-projected-root-closure") {
        return InventoryRouteClosureVariant::MixedProjectedFull;
    }
    if (value == "ir3" || value == "ir3-mixed-one-pass" ||
        value == "research-ir3-one-pass-mixed") {
        return InventoryRouteClosureVariant::MixedOnePass;
    }
    return InventoryRouteClosureVariant::Invalid;
}

std::string inventoryRouteClosureVariantName(
    InventoryRouteClosureVariant variant) {
    switch (variant) {
    case InventoryRouteClosureVariant::MixedFull:
        return "IR1-mixed-full-closure";
    case InventoryRouteClosureVariant::MixedProjectedFull:
        return "IR2-mixed-projected-full-closure";
    case InventoryRouteClosureVariant::MixedOnePass:
        return "IR3-mixed-one-pass";
    case InventoryRouteClosureVariant::Invalid: return "invalid";
    }
    return "invalid";
}

FixedIntervalMipRequest::AdditionalLinearRow inventoryRouteBackendRow(
    const InventoryRouteCut& cut,
    int ordinal) {
    FixedIntervalMipRequest::AdditionalLinearRow row;
    row.row_name = "round54_ir_" + std::to_string(ordinal);
    row.sense = cut.sense;
    row.rhs = cut.rhs;
    row.canonical_signature = cut.canonical_signature;
    row.scope = cut.scope;
    for (const auto& coefficient : cut.row_coefficients) {
        row.variable_names.push_back(coefficient.variable_name);
        row.coefficients.push_back(coefficient.coefficient);
    }
    return row;
}

InventoryRouteRootClosureResult runInventoryRouteRootClosure(
    FixedIntervalMipBackend& backend,
    const Instance& instance,
    const FixedIntervalMipRequest& base_request,
    InventoryRouteClosureVariant variant,
    double certificate_tolerance) {
    InventoryRouteRootClosureResult result;
    result.attempted = true;
    result.variant = inventoryRouteClosureVariantName(variant);
    if (variant == InventoryRouteClosureVariant::Invalid) {
        result.fallback_required = true;
        result.failure_reason = "invalid_inventory_route_closure_variant";
        return result;
    }
    if (!(certificate_tolerance > 0.0) ||
        !std::isfinite(certificate_tolerance)) {
        result.fallback_required = true;
        result.failure_reason = "invalid_certificate_tolerance";
        return result;
    }
    std::set<std::string> signatures;
    int round_index = 0;
    const auto closure_started = std::chrono::steady_clock::now();
    while (true) {
        InventoryRouteClosureRound round;
        round.round = round_index;
        FixedIntervalMipRequest request = base_request;
        request.solve_kind = FixedIntervalSolveKind::PaperLpRelaxation;
        request.leaf_id = base_request.leaf_id + "__ir_lp_" +
            std::to_string(round_index);
        request.new_leaf = true;
        request.retain_model_after_solve = false;
        request.incremental_model_reuse_enabled = false;
        request.capture_native_bound_events = false;
        request.capture_lp_primal_dual_evidence = true;
        request.branch_priority_overrides.clear();
        request.variable_bound_overrides.clear();
        request.additional_linear_rows.clear();
        const double closure_elapsed = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - closure_started).count();
        request.global_deadline_remaining_seconds =
            base_request.global_deadline_remaining_seconds - closure_elapsed;
        if (!(request.global_deadline_remaining_seconds > 0.0)) {
            round.status = "external_process_cap_exhausted_before_lp_round";
            result.rounds.push_back(round);
            result.fallback_required = true;
            result.failure_reason = round.status;
            return result;
        }
        for (std::size_t index = 0; index < result.accepted_cuts.size(); ++index) {
            request.additional_linear_rows.push_back(inventoryRouteBackendRow(
                result.accepted_cuts[index], static_cast<int>(index)));
        }
        const FixedIntervalMipOutcome outcome = backend.solve(request);
        round.lp_work = outcome.work;
        round.lp_runtime_seconds = outcome.solver_runtime_seconds;
        round.lp_simplex_iterations = outcome.simplex_iterations;
        round.lp_infeasible = outcome.lp_terminal_valid && outcome.infeasible;
        round.lp_valid = round.lp_infeasible ||
            (outcome.lp_terminal_valid && outcome.optimal &&
             outcome.lp_objective_value_available &&
             outcome.model_fingerprint_matches_request &&
             outcome.additional_linear_rows_valid);
        round.lp_objective = outcome.lp_objective_value;
        result.cumulative_lp_work += outcome.work;
        result.cumulative_lp_runtime_seconds += outcome.solver_runtime_seconds;
        result.cumulative_lp_simplex_iterations += outcome.simplex_iterations;
        result.model_read_seconds += outcome.model_read_seconds;
        if (round_index == 0 && outcome.lp_objective_value_available) {
            result.initial_lp_objective = outcome.lp_objective_value;
        }
        if (outcome.lp_objective_value_available) {
            result.final_lp_objective = outcome.lp_objective_value;
        }
        if (round.lp_infeasible) {
            round.status = "lp_infeasible_closure";
            result.rounds.push_back(round);
            result.infeasible = true;
            result.converged = true;
            result.valid = true;
            result.failure_reason = "none";
            return result;
        }
        if (!round.lp_valid) {
            round.status = "invalid_lp_evidence";
            result.rounds.push_back(round);
            result.fallback_required = true;
            result.failure_reason = outcome.failure_reason.empty()
                ? "invalid_root_closure_lp" : outcome.failure_reason;
            return result;
        }
        bool state_valid = false;
        std::string state_reason;
        const InventoryRouteLpState state = lpStateFromOutcome(
            instance, outcome, state_valid, state_reason);
        if (!state_valid) {
            round.status = state_reason;
            result.rounds.push_back(round);
            result.fallback_required = true;
            result.failure_reason = state_reason;
            return result;
        }
        round.separation = separateInventoryRouteCuts(
            state, certificate_tolerance);
        if (!round.separation.valid) {
            round.status = round.separation.failure_reason;
            result.rounds.push_back(round);
            result.fallback_required = true;
            result.failure_reason = round.separation.failure_reason;
            return result;
        }
        std::vector<InventoryRouteCut> candidates = {
            round.separation.mixed_inbound,
            round.separation.mixed_outbound};
        if (variant == InventoryRouteClosureVariant::MixedProjectedFull) {
            candidates.push_back(round.separation.projected_inbound);
            candidates.push_back(round.separation.projected_outbound);
        }
        std::vector<InventoryRouteCut> accepted_this_round;
        for (const auto& cut : candidates) {
            ++round.cuts_generated;
            ++result.cuts_generated;
            if (!cut.violated) {
                ++round.nonviolated_rejections;
                ++result.nonviolated_rejections;
                continue;
            }
            if (cut.kind == InventoryRouteCutKind::ProjectedInbound ||
                cut.kind == InventoryRouteCutKind::ProjectedOutbound) {
                const InventoryRouteCut& mixed =
                    cut.kind == InventoryRouteCutKind::ProjectedInbound
                        ? round.separation.mixed_inbound
                        : round.separation.mixed_outbound;
                if (mixed.violated && sameSubset(cut, mixed)) {
                    ++round.dominated_rejections;
                    ++result.dominated_rejections;
                    continue;
                }
            }
            if (!signatures.insert(cut.canonical_signature).second) {
                ++round.duplicate_rejections;
                ++result.duplicate_rejections;
                // A previously added row remains strictly violated in the
                // current optimal LP: this is a numerical inconsistency, not
                // a reason to stop closure successfully.
                round.status = "strictly_violated_duplicate_after_reoptimize";
                result.rounds.push_back(round);
                result.fallback_required = true;
                result.failure_reason = round.status;
                return result;
            }
            accepted_this_round.push_back(cut);
        }
        for (const auto& cut : accepted_this_round) {
            result.accepted_cuts.push_back(cut);
            ++round.cuts_added;
            ++result.cuts_added;
        }
        if (accepted_this_round.empty()) {
            round.status = "mathematical_closure_complete";
            result.rounds.push_back(round);
            result.converged = true;
            result.valid = true;
            result.failure_reason = "none";
            return result;
        }
        round.status = "cuts_added_reoptimize";
        result.rounds.push_back(round);
        if (variant == InventoryRouteClosureVariant::MixedOnePass) {
            result.converged = false;
            result.valid = true;
            result.failure_reason = "none_one_pass_policy";
            return result;
        }
        ++round_index;
    }
}

} // namespace ebrp
