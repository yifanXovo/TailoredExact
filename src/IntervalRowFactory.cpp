#include "IntervalRowFactory.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <limits>
#include <set>
#include <sstream>

namespace ebrp {
namespace {

std::string yName(int i) { return "Y_" + std::to_string(i); }
std::string rName(int i) { return "r_" + std::to_string(i); }
std::string eName(int i) { return "e_" + std::to_string(i); }
std::string hName(int i, int j) {
    if (j < i) std::swap(i, j);
    return "h_" + std::to_string(i) + "_" + std::to_string(j);
}
std::string bitName(int i, int b) {
    return "bit_" + std::to_string(i) + "_" + std::to_string(b);
}
std::string prodName(int i, int b) {
    return "prod_" + std::to_string(i) + "_" + std::to_string(b);
}
std::string pName(int k, int i) {
    return "p_" + std::to_string(k) + "_" + std::to_string(i);
}
std::string dName(int k, int i) {
    return "d_" + std::to_string(k) + "_" + std::to_string(i);
}

void add(std::map<std::string, double>& coefficients,
         const std::string& variable,
         double value) {
    if (std::fabs(value) <= 1e-14) return;
    coefficients[variable] += value;
    if (std::fabs(coefficients[variable]) <= 1e-14) {
        coefficients.erase(variable);
    }
}

std::string stableHash(const std::string& value) {
    std::uint64_t hash = 1469598103934665603ull;
    for (unsigned char ch : value) {
        hash ^= static_cast<std::uint64_t>(ch);
        hash *= 1099511628211ull;
    }
    std::ostringstream out;
    out << std::hex << std::setw(16) << std::setfill('0') << hash;
    return out.str();
}

std::string number(double value) {
    if (std::fabs(value) < 5e-14) value = 0.0;
    std::ostringstream out;
    out << std::setprecision(17) << value;
    return out.str();
}

void addRow(IntervalRowFactoryResult& out,
            const std::string& family,
            std::map<std::string, double> coefficients,
            char sense,
            double rhs,
            bool depends_L,
            bool depends_U,
            const std::string& proof_tag) {
    CanonicalLinearRow row;
    row.family = family;
    row.coefficients = std::move(coefficients);
    row.sense = sense;
    row.rhs = rhs;
    row.depends_on_gamma_L = depends_L;
    row.depends_on_gamma_U = depends_U;
    row.scope = IntervalRowScope::IntervalLocal;
    row.proof_tag = proof_tag;
    row.signature = canonicalRowSignature(row);
    out.rows.push_back(std::move(row));
}

void addBound(IntervalRowFactoryResult& out,
              const std::string& family,
              const std::string& variable,
              char direction,
              double value,
              bool depends_L,
              bool depends_U,
              const std::string& proof_tag) {
    CanonicalBoundChange bound;
    bound.family = family;
    bound.variable = variable;
    bound.direction = direction;
    bound.value = value;
    bound.depends_on_gamma_L = depends_L;
    bound.depends_on_gamma_U = depends_U;
    bound.proof_tag = proof_tag;
    bound.signature = canonicalBoundSignature(bound);
    out.bound_changes.push_back(std::move(bound));
}

void noteFamily(IntervalRowFactoryResult& out, const std::string& family) {
    if (std::find(out.active_families.begin(), out.active_families.end(), family) ==
        out.active_families.end()) {
        out.active_families.push_back(family);
    }
}

void registerFamily(IntervalRowFactoryResult& out,
                    const std::string& family,
                    IntervalRowScope scope,
                    bool active,
                    bool implemented,
                    const std::string& proof_tag) {
    IntervalRowFamilyRegistryEntry entry;
    entry.family = family;
    entry.scope = scope;
    entry.active = active;
    entry.implemented = implemented;
    entry.proof_tag = proof_tag;
    out.family_registry.push_back(std::move(entry));
    if (active) noteFamily(out, family);
}

} // namespace

std::string intervalRowScopeName(IntervalRowScope scope) {
    switch (scope) {
    case IntervalRowScope::Global: return "global";
    case IntervalRowScope::IntervalLocal: return "interval_local";
    case IntervalRowScope::IntervalBound: return "interval_bound";
    case IntervalRowScope::DiagnosticExcluded: return "diagnostic_excluded";
    }
    return "unknown";
}

std::string canonicalRowSignature(const CanonicalLinearRow& row) {
    std::ostringstream canonical;
    canonical << row.family << '|' << row.sense << '|' << number(row.rhs)
              << '|' << intervalRowScopeName(row.scope) << '|'
              << (row.depends_on_gamma_L ? '1' : '0')
              << (row.depends_on_gamma_U ? '1' : '0') << '|'
              << row.proof_tag;
    for (const auto& coefficient : row.coefficients) {
        canonical << '|' << coefficient.first << '=' << number(coefficient.second);
    }
    return stableHash(canonical.str());
}

std::string canonicalBoundSignature(const CanonicalBoundChange& bound) {
    std::ostringstream canonical;
    canonical << bound.family << '|' << bound.variable << '|'
              << bound.direction << '|' << number(bound.value) << '|'
              << intervalRowScopeName(bound.scope) << '|'
              << (bound.depends_on_gamma_L ? '1' : '0')
              << (bound.depends_on_gamma_U ? '1' : '0') << '|'
              << bound.proof_tag;
    return stableHash(canonical.str());
}

IntervalRowFactoryResult buildRound18StaticIntervalRows(
    const Instance& instance,
    const SolveOptions& options,
    const IntervalRowFactoryRequest& request) {
    IntervalRowFactoryResult out;
    const int V = instance.V;
    const int M = instance.M;
    const double cunit = instance.pickup_time + instance.drop_time;
    const bool interval_enabled = request.strengthened &&
        std::isfinite(request.gamma_L) && std::isfinite(request.gamma_U) &&
        request.gamma_U >= request.gamma_L - 1e-12;
    registerFamily(out, "inventory_conservation", IntervalRowScope::Global,
                   options.compact_bc_inventory_conservation, true,
                   "original_inventory_balance_valid_for_full_root_domain");
    registerFamily(out, "movement_reachability_domains", IntervalRowScope::Global,
                   options.compact_bc_movement_reachability_domains, true,
                   "route_reachability_domain_valid_for_full_root_domain");
    registerFamily(out, "visit_inventory_linking", IntervalRowScope::Global,
                   options.compact_bc_visit_inventory_linking, true,
                   "visit_operation_link_valid_for_full_root_domain");
    registerFamily(out, "global_handling_capacity", IntervalRowScope::Global,
                   options.global_handling_capacity_cuts, true,
                   "fleet_handling_capacity_valid_for_full_root_domain");
    registerFamily(out, "support_duration", IntervalRowScope::Global,
                   options.compact_bc_support_duration_cuts, true,
                   "support_duration_cover_valid_for_full_root_domain");
    registerFamily(out, "transfer_compat", IntervalRowScope::Global,
                   options.compact_bc_pairwise_transfer_compatibility, true,
                   "pairwise_transfer_compatibility_valid_for_full_root_domain");
    registerFamily(out, "direct_gini_cap_floor", IntervalRowScope::IntervalLocal,
                   options.compact_bc_direct_gini_rows, true,
                   "gini_cross_multiplication_uses_child_bounds");
    registerFamily(out, "interval_tight_mccormick", IntervalRowScope::IntervalLocal,
                   options.compact_bc_tight_mccormick, true,
                   "mccormick_envelope_uses_child_bounds");
    registerFamily(out, "objective_estimator_cutoff", IntervalRowScope::IntervalLocal,
                   options.compact_bc_objective_estimator_cutoff, true,
                   "objective_estimator_uses_child_domains");
    registerFamily(out, "penalty_lb_closure", IntervalRowScope::IntervalLocal,
                   options.compact_bc_penalty_lb_closure, true,
                   "penalty_closure_uses_child_inventory_domains");
    registerFamily(out, "gini_spread", IntervalRowScope::IntervalLocal,
                   options.gini_spread_cuts, true,
                   "pairwise_spread_uses_child_gini_upper_bound");
    registerFamily(out, "required_movement", IntervalRowScope::IntervalLocal,
                   options.required_movement_cuts, true,
                   "movement_requirement_uses_child_inventory_domains");
    registerFamily(out, "low_gini_centering", IntervalRowScope::IntervalLocal,
                   options.low_gini_ratio_band_tightening, true,
                   "centering_band_uses_child_gini_upper_bound");
    registerFamily(out, "variable_s_centering", IntervalRowScope::IntervalLocal,
                   options.compact_bc_variable_s_centering, true,
                   "variable_ratio_sum_centering_uses_child_gini_upper_bound");
    registerFamily(out, "sp_product_estimator", IntervalRowScope::IntervalLocal,
                   options.compact_bc_sp_product_estimator != "off", true,
                   "ratio_sum_penalty_product_uses_child_domains");
    registerFamily(out, "gini_interval_bound", IntervalRowScope::IntervalBound,
                   interval_enabled, true, "exact_parent_child_interval_subset");
    registerFamily(out, "verified_incumbent_objective_row", IntervalRowScope::Global,
                   request.add_incumbent_row, true,
                   "same_run_verified_incumbent_preserves_an_optimum");
    out.domain.y_lower.assign(static_cast<std::size_t>(V + 1), 0);
    out.domain.y_upper.assign(static_cast<std::size_t>(V + 1), 0);
    out.domain.e_lower.assign(static_cast<std::size_t>(V + 1), 0.0);
    out.domain.e_upper.assign(static_cast<std::size_t>(V + 1), 0.0);
    for (int i = 1; i <= V; ++i) out.domain.y_upper[i] = instance.capacity[i];
    out.domain.g_lower = interval_enabled ? std::max(0.0, request.gamma_L) : 0.0;
    out.domain.g_upper = interval_enabled
        ? std::min(1.0, std::max(request.gamma_L, request.gamma_U))
        : 1.0;

    const bool cutoff_active = interval_enabled &&
        std::isfinite(request.verified_incumbent) &&
        request.verified_incumbent > 0.0 && options.lambda > 1e-12;
    const double cutoff_value = cutoff_active
        ? request.verified_incumbent - request.incumbent_epsilon
        : std::numeric_limits<double>::infinity();
    const double penalty_budget = cutoff_active
        ? (cutoff_value - request.gamma_L) / options.lambda
        : std::numeric_limits<double>::infinity();

    if (cutoff_active && std::isfinite(penalty_budget) &&
        penalty_budget >= -1e-10 &&
        (options.interval_oracle_penalty_domain_tightening ||
         options.interval_oracle_low_gini_tightening ||
         options.low_gini_ratio_band_tightening)) {
        noteFamily(out, "penalty_final_inventory_domain");
        for (int i = 1; i <= V; ++i) {
            if (instance.weights[i] <= 1e-12) continue;
            const double radius = std::max(0.0, penalty_budget / instance.weights[i]);
            int lo = static_cast<int>(std::ceil(
                instance.target[i] * (1.0 - radius) - 1e-9));
            int hi = static_cast<int>(std::floor(
                instance.target[i] * (1.0 + radius) + 1e-9));
            out.domain.y_lower[i] = std::max(0, lo);
            out.domain.y_upper[i] = std::min(instance.capacity[i], hi);
        }
    }

    if (request.strengthened && options.compact_bc_movement_reachability_domains) {
        for (int i = 1; i <= V; ++i) {
            int pickup_reach = 0;
            int drop_reach = 0;
            for (int k = 0; k < M; ++k) {
                const double travel = instance.dist[0][i] + instance.dist[i][0];
                int movement = 0;
                if (instance.total_time_limit + 1e-9 >= travel && cunit > 1e-12) {
                    movement = static_cast<int>(std::floor(
                        (instance.total_time_limit - travel) / cunit + 1e-9));
                }
                pickup_reach = std::max(pickup_reach,
                    std::min({instance.initial[i], instance.Q[k], movement}));
                drop_reach = std::max(drop_reach,
                    std::min({instance.capacity[i] - instance.initial[i],
                              instance.Q[k], movement}));
            }
            out.domain.y_lower[i] = std::max(
                out.domain.y_lower[i], instance.initial[i] - pickup_reach);
            out.domain.y_upper[i] = std::min(
                out.domain.y_upper[i], instance.initial[i] + drop_reach);
        }
    }

    for (int i = 1; i <= V; ++i) {
        if (out.domain.y_lower[i] > out.domain.y_upper[i]) {
            out.domain.domain_infeasible = true;
            out.domain.y_lower[i] = 0;
            out.domain.y_upper[i] = instance.capacity[i];
        }
        const double target = std::max(1e-12,
            static_cast<double>(instance.target[i]));
        const double r_lo = static_cast<double>(out.domain.y_lower[i]) / target;
        const double r_hi = static_cast<double>(out.domain.y_upper[i]) / target;
        out.domain.s_lower += r_lo;
        out.domain.s_upper += r_hi;
        double e_lo = 0.0;
        if (r_hi < 1.0) e_lo = 1.0 - r_hi;
        else if (r_lo > 1.0) e_lo = r_lo - 1.0;
        const double e_hi = std::max(std::fabs(r_lo - 1.0),
                                     std::fabs(r_hi - 1.0));
        out.domain.e_lower[i] = std::max(0.0, e_lo);
        out.domain.e_upper[i] = std::max(out.domain.e_lower[i], e_hi);
        out.domain.penalty_lower += instance.weights[i] * out.domain.e_lower[i];
        out.domain.penalty_upper += instance.weights[i] * out.domain.e_upper[i];
    }
    out.domain.penalty_upper = std::max(out.domain.penalty_lower,
                                        out.domain.penalty_upper);

    if (!interval_enabled) {
        out.complete_round18_static_migration = true;
        return out;
    }

    addBound(out, "gini_interval_bound", "G", 'L', out.domain.g_lower,
             true, false, "parent_child_interval_subset");
    addBound(out, "gini_interval_bound", "G", 'U', out.domain.g_upper,
             false, true, "parent_child_interval_subset");
    noteFamily(out, "gini_interval_bound");
    for (int i = 1; i <= V; ++i) {
        addBound(out, "penalty_final_inventory_domain", yName(i), 'L',
                 out.domain.y_lower[i], true, false,
                 "verified_incumbent_nonnegative_penalty_domain");
        addBound(out, "penalty_final_inventory_domain", yName(i), 'U',
                 out.domain.y_upper[i], true, false,
                 "verified_incumbent_nonnegative_penalty_domain");
    }

    if (options.compact_bc_direct_gini_rows) {
        std::map<std::string, double> cap;
        std::map<std::string, double> floor;
        for (int i = 1; i <= V; ++i) {
            add(cap, rName(i), -static_cast<double>(V) * request.gamma_U);
            add(floor, rName(i), -static_cast<double>(V) * request.gamma_L);
            for (int j = i + 1; j <= V; ++j) {
                add(cap, hName(i, j), 1.0);
                add(floor, hName(i, j), 1.0);
            }
        }
        addRow(out, "direct_gini_cap", std::move(cap), 'L', 0.0,
               false, true, "gini_definition_upper_cross_multiplication");
        addRow(out, "direct_gini_floor", std::move(floor), 'G', 0.0,
               true, false, "gini_definition_lower_cross_multiplication");
        noteFamily(out, "direct_gini_cap_floor");
    }

    if (options.compact_bc_tight_mccormick) {
        for (int i = 1; i <= V; ++i) {
            int bits = 1;
            while (((1LL << bits) - 1) < instance.capacity[i]) ++bits;
            for (int b = 0; b < bits; ++b) {
                std::map<std::string, double> lb_bit;
                add(lb_bit, prodName(i, b), 1.0);
                add(lb_bit, bitName(i, b), -out.domain.g_lower);
                addRow(out, "interval_tight_mccormick_G_bit", std::move(lb_bit),
                       'G', 0.0, true, false, "mccormick_binary_product");
                std::map<std::string, double> ub_bit;
                add(ub_bit, prodName(i, b), 1.0);
                add(ub_bit, bitName(i, b), -out.domain.g_upper);
                addRow(out, "interval_tight_mccormick_G_bit", std::move(ub_bit),
                       'L', 0.0, false, true, "mccormick_binary_product");
                std::map<std::string, double> lb_g;
                add(lb_g, prodName(i, b), 1.0);
                add(lb_g, "G", -1.0);
                add(lb_g, bitName(i, b), -out.domain.g_upper);
                addRow(out, "interval_tight_mccormick_G_bit", std::move(lb_g),
                       'G', -out.domain.g_upper, false, true,
                       "mccormick_binary_product");
                std::map<std::string, double> ub_g;
                add(ub_g, prodName(i, b), 1.0);
                add(ub_g, "G", -1.0);
                add(ub_g, bitName(i, b), -out.domain.g_lower);
                addRow(out, "interval_tight_mccormick_G_bit", std::move(ub_g),
                       'L', -out.domain.g_lower, true, false,
                       "mccormick_binary_product");
            }
        }
        noteFamily(out, "interval_tight_mccormick_G_bit");
    }

    if (options.gini_spread_cuts && V > 1) {
        for (int i = 1; i <= V; ++i) {
            for (int j = i + 1; j <= V; ++j) {
                std::map<std::string, double> row;
                add(row, hName(i, j), static_cast<double>(V - 1));
                for (int t = 1; t <= V; ++t) {
                    add(row, rName(t), -static_cast<double>(V) * request.gamma_U);
                }
                addRow(out, "gini_pairwise_spread", std::move(row), 'L', 0.0,
                       false, true, "pair_deviation_bounded_by_total_gini");
            }
        }
        noteFamily(out, "gini_pairwise_spread");
    }

    if (options.required_movement_cuts) {
        for (int i = 1; i <= V; ++i) {
            if (out.domain.y_lower[i] > instance.initial[i]) {
                std::map<std::string, double> row;
                for (int k = 0; k < M; ++k) {
                    add(row, dName(k, i), 1.0);
                    add(row, pName(k, i), -1.0);
                }
                addRow(out, "required_station_movement", std::move(row), 'G',
                       out.domain.y_lower[i] - instance.initial[i], true, false,
                       "final_inventory_balance_local_domain");
            }
            if (out.domain.y_upper[i] < instance.initial[i]) {
                std::map<std::string, double> row;
                for (int k = 0; k < M; ++k) {
                    add(row, pName(k, i), 1.0);
                    add(row, dName(k, i), -1.0);
                }
                addRow(out, "required_station_movement", std::move(row), 'G',
                       instance.initial[i] - out.domain.y_upper[i], true, false,
                       "final_inventory_balance_local_domain");
            }
        }
        noteFamily(out, "required_station_movement");
    }

    const bool low_centering = options.low_gini_ratio_band_tightening &&
        options.compact_bc_direct_gini_rows && V > 1;
    if (low_centering) {
        const double spread_upper = static_cast<double>(V) * request.gamma_U *
            out.domain.s_upper / static_cast<double>(V - 1);
        // The Round 18 r_min/r_max extended formulation is projected to its
        // exact pairwise form here.  CPLEX 22.1.1 can eliminate the two
        // auxiliary extrema during presolve and then incorrectly crush
        // stronger child-local rows that reference them.  The inequalities
        // below describe exactly max(r)-min(r) <= spread_upper without those
        // eliminable columns and are therefore safe in a presolved local-cut
        // context.
        for (int i = 1; i <= V; ++i) {
            for (int j = i + 1; j <= V; ++j) {
                std::map<std::string, double> forward;
                add(forward, rName(i), 1.0);
                add(forward, rName(j), -1.0);
                addRow(out, "low_gini_centering_band", std::move(forward),
                       'L', std::max(0.0, spread_upper), false, true,
                       "projected_exact_ratio_range_upper_bound");
                std::map<std::string, double> reverse;
                add(reverse, rName(j), 1.0);
                add(reverse, rName(i), -1.0);
                addRow(out, "low_gini_centering_band", std::move(reverse),
                       'L', std::max(0.0, spread_upper), false, true,
                       "projected_exact_ratio_range_upper_bound");
            }
        }
        noteFamily(out, "low_gini_centering_band");
        if (options.compact_bc_variable_s_centering) {
            for (int i = 1; i <= V; ++i) {
                for (int j = i + 1; j <= V; ++j) {
                    auto variableRange = [&](int positive, int negative) {
                        std::map<std::string, double> row;
                        add(row, rName(positive),
                            static_cast<double>(V - 1));
                        add(row, rName(negative),
                            -static_cast<double>(V - 1));
                        for (int t = 1; t <= V; ++t) {
                            add(row, rName(t),
                                -static_cast<double>(V) * request.gamma_U);
                        }
                        addRow(out, "variable_s_low_gini_centering",
                               std::move(row), 'L', 0.0, false, true,
                               "projected_exact_variable_ratio_sum_range");
                    };
                    variableRange(i, j);
                    variableRange(j, i);
                }
            }
            noteFamily(out, "variable_s_low_gini_centering");
        }
    }

    if (request.add_incumbent_row && cutoff_active) {
        std::map<std::string, double> objective;
        add(objective, "G", 1.0);
        for (int i = 1; i <= V; ++i) {
            add(objective, eName(i), options.lambda * instance.weights[i]);
        }
        addRow(out, "verified_incumbent_objective_row", std::move(objective),
               'L', cutoff_value, false, false,
               "same_run_verified_incumbent_preserves_optimum");
        noteFamily(out, "verified_incumbent_objective_row");
    }

    if (options.compact_bc_objective_estimator_cutoff &&
        request.add_incumbent_row && cutoff_active &&
        out.domain.s_upper > 1e-12) {
        std::map<std::string, double> estimator;
        for (int i = 1; i <= V; ++i) {
            add(estimator, eName(i), static_cast<double>(V) *
                out.domain.s_upper * options.lambda * instance.weights[i]);
            for (int j = i + 1; j <= V; ++j) {
                add(estimator, hName(i, j), 1.0);
            }
        }
        addRow(out, "objective_lower_estimator_cutoff", std::move(estimator),
               'L', static_cast<double>(V) * out.domain.s_upper * cutoff_value,
               true, false, "gini_denominator_upper_and_incumbent_row");
        noteFamily(out, "objective_lower_estimator_cutoff");
    }

    if (options.compact_bc_penalty_lb_closure) {
        std::map<std::string, double> penalty;
        for (int i = 1; i <= V; ++i) {
            add(penalty, eName(i), instance.weights[i]);
        }
        addRow(out, "penalty_lower_bound_closure", std::move(penalty), 'G',
               out.domain.penalty_lower, true, false,
               "absolute_deviation_local_inventory_domain");
        noteFamily(out, "penalty_lower_bound_closure");
        if (request.add_incumbent_row && cutoff_active &&
            request.gamma_L + options.lambda * out.domain.penalty_lower >=
                cutoff_value - 1e-9) {
            addRow(out, "penalty_lower_bound_closure", {}, 'L', -1.0,
                   true, false, "interval_no_improver_domain_closure");
        }
    }

    if ((options.interval_oracle_penalty_domain_tightening ||
         options.interval_oracle_low_gini_tightening) &&
        request.add_incumbent_row && cutoff_active && options.lambda > 1e-12 &&
        std::isfinite(penalty_budget) && penalty_budget >= -1e-10) {
        for (int i = 1; i <= V; ++i) {
            if (instance.weights[i] <= 1e-12) continue;
            std::map<std::string, double> row;
            add(row, eName(i), 1.0);
            addRow(out, "penalty_deviation_upper_bound", std::move(row), 'L',
                   std::max(0.0, penalty_budget / instance.weights[i]), true,
                   false, "incumbent_row_and_gini_floor_penalty_budget");
        }
        noteFamily(out, "penalty_deviation_upper_bound");
    }

    const bool sp_estimator = request.add_incumbent_row && cutoff_active &&
        options.compact_bc_sp_product_estimator != "off" &&
        out.domain.s_upper >= out.domain.s_lower - 1e-12 &&
        out.domain.penalty_upper >= out.domain.penalty_lower - 1e-12;
    if (sp_estimator) {
        std::map<std::string, double> s_expr;
        std::map<std::string, double> p_expr;
        for (int i = 1; i <= V; ++i) {
            add(s_expr, rName(i), 1.0);
            add(p_expr, eName(i), instance.weights[i]);
        }
        auto productRow = [&](double s_coef, double p_coef, char sense,
                              double rhs) {
            std::map<std::string, double> row;
            add(row, "W_SP", 1.0);
            for (const auto& item : p_expr) add(row, item.first, s_coef * item.second);
            for (const auto& item : s_expr) add(row, item.first, p_coef * item.second);
            addRow(out, "sp_product_mccormick", std::move(row), sense, rhs,
                   true, false, "mccormick_ratio_sum_penalty_product");
        };
        productRow(-out.domain.s_lower, -out.domain.penalty_lower, 'G',
                   -out.domain.s_lower * out.domain.penalty_lower);
        productRow(-out.domain.s_upper, -out.domain.penalty_upper, 'G',
                   -out.domain.s_upper * out.domain.penalty_upper);
        productRow(-out.domain.s_upper, -out.domain.penalty_lower, 'L',
                   -out.domain.s_upper * out.domain.penalty_lower);
        productRow(-out.domain.s_lower, -out.domain.penalty_upper, 'L',
                   -out.domain.s_lower * out.domain.penalty_upper);
        std::map<std::string, double> estimator;
        for (int i = 1; i <= V; ++i) {
            for (int j = i + 1; j <= V; ++j) {
                add(estimator, hName(i, j), 1.0);
            }
            add(estimator, rName(i), -static_cast<double>(V) * cutoff_value);
        }
        add(estimator, "W_SP", static_cast<double>(V) * options.lambda);
        addRow(out, "sp_product_objective_estimator_paper_safe",
               std::move(estimator), 'L', 0.0, true, false,
               "cross_multiplied_objective_incumbent_estimator");
        noteFamily(out, "sp_product_objective_estimator_paper_safe");
    }

    const std::vector<std::pair<bool, std::string>> unsupported = {
        {options.compact_bc_s_range_refinement != "off", "s_range_refinement"},
        {options.tailored_bc_gini_subset_envelope, "tailored_gini_subset_envelope"},
        {options.tailored_bc_low_gini_l1_centering, "tailored_low_gini_l1_centering"},
        {options.tailored_bc_local_centering, "tailored_local_centering"},
        {options.tailored_bc_subset_cross_h_centering, "tailored_subset_cross_h_centering"},
        {options.tailored_bc_local_q_centering, "tailored_local_q_centering"},
        {options.tailored_bc_gs_product_coupling, "tailored_gs_product_coupling"},
        {options.tailored_bc_disaggregated_sp_estimator, "tailored_disaggregated_sp"},
        {options.tailored_bc_bucket_ratio_domain_tightening, "bucket_ratio_domain"},
        {options.tailored_bc_bucket_subset_ratio_domain, "bucket_subset_ratio_domain"},
        {options.tailored_bc_bucket_integer_inventory_domain, "bucket_inventory_domain"},
        {options.tailored_bc_bucket_required_movement, "bucket_required_movement"},
        {options.tailored_bc_bucket_required_visit, "bucket_required_visit"}
    };
    for (const auto& item : unsupported) {
        registerFamily(out, item.second, IntervalRowScope::DiagnosticExcluded,
                       item.first, false,
                       "excluded_from_round18_static_no_callback_official_profile");
        if (item.first) out.unsupported_active_families.push_back(item.second);
    }
    out.complete_round18_static_migration = out.unsupported_active_families.empty();
    for (const IntervalRowFamilyRegistryEntry& entry : out.family_registry) {
        if (entry.active && !entry.implemented) {
            out.complete_round18_static_migration = false;
        }
    }

    std::vector<std::string> signatures;
    signatures.reserve(out.rows.size() + out.bound_changes.size());
    for (const auto& row : out.rows) signatures.push_back(row.signature);
    for (const auto& bound : out.bound_changes) signatures.push_back(bound.signature);
    std::sort(signatures.begin(), signatures.end());
    std::ostringstream aggregate;
    aggregate << out.factory_version;
    for (const auto& signature : signatures) aggregate << '|' << signature;
    out.aggregate_signature = stableHash(aggregate.str());
    return out;
}

} // namespace ebrp
