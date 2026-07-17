#include "GiniFrontierGeometry.hpp"
#include "IntervalRowFactory.hpp"
#include "Result.hpp"

#include <algorithm>
#include <cmath>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

ebrp::Instance representativeInstance() {
    ebrp::Instance instance;
    instance.name = "representative";
    instance.V = 4;
    instance.M = 1;
    instance.Q = {4};
    instance.capacity = {0, 12, 11, 10, 9};
    instance.initial = {0, 1, 9, 2, 7};
    instance.target = {0, 6, 5, 5, 4};
    instance.weights = {0.0, 1.0, 1.5, 0.75, 2.0};
    instance.pickup_time = 60.0;
    instance.drop_time = 60.0;
    instance.total_time_limit = 3600.0;
    instance.dist.assign(5, std::vector<double>(5, 0.0));
    for (int i = 0; i <= instance.V; ++i) {
        for (int j = 0; j <= instance.V; ++j) {
            instance.dist[i][j] = i == j ? 0.0 : 10.0 + std::abs(i - j);
        }
    }
    return instance;
}

ebrp::SolveOptions round18StaticOptions() {
    ebrp::SolveOptions options;
    options.lambda = 0.15;
    options.compact_bc_inventory_conservation = true;
    options.compact_bc_movement_reachability_domains = true;
    options.compact_bc_visit_inventory_linking = true;
    options.global_handling_capacity_cuts = true;
    options.compact_bc_support_duration_cuts = true;
    options.compact_bc_pairwise_transfer_compatibility = true;
    options.compact_bc_direct_gini_rows = true;
    options.compact_bc_tight_mccormick = true;
    options.compact_bc_objective_estimator_cutoff = true;
    options.compact_bc_penalty_lb_closure = true;
    options.gini_spread_cuts = true;
    options.required_movement_cuts = true;
    options.low_gini_ratio_band_tightening = true;
    options.compact_bc_variable_s_centering = true;
    options.compact_bc_sp_product_estimator = "paper-safe";
    options.interval_oracle_penalty_domain_tightening = true;
    options.interval_oracle_low_gini_tightening = true;
    options.compact_bc_s_range_refinement = "off";
    options.tailored_bc_gini_subset_envelope = false;
    options.tailored_bc_low_gini_l1_centering = false;
    options.tailored_bc_local_centering = false;
    options.tailored_bc_subset_cross_h_centering = false;
    options.tailored_bc_local_q_centering = false;
    options.tailored_bc_gs_product_coupling = false;
    options.tailored_bc_disaggregated_sp_estimator = false;
    options.tailored_bc_bucket_ratio_domain_tightening = false;
    options.tailored_bc_bucket_subset_ratio_domain = false;
    options.tailored_bc_bucket_integer_inventory_domain = false;
    options.tailored_bc_bucket_required_movement = false;
    options.tailored_bc_bucket_required_visit = false;
    return options;
}

ebrp::IntervalRowFactoryResult makeRows(double lower, double upper) {
    ebrp::IntervalRowFactoryRequest request;
    request.gamma_L = lower;
    request.gamma_U = upper;
    request.verified_incumbent = 0.8;
    request.incumbent_epsilon = 0.0;
    request.add_incumbent_row = true;
    request.strengthened = true;
    return ebrp::buildRound18StaticIntervalRows(
        representativeInstance(), round18StaticOptions(), request);
}

std::set<std::string> signatures(
    const ebrp::IntervalRowFactoryResult& rows) {
    std::set<std::string> answer;
    for (const auto& row : rows.rows) answer.insert(row.signature);
    for (const auto& bound : rows.bound_changes) answer.insert(bound.signature);
    return answer;
}

void testGeometry() {
    const ebrp::GiniIntervalGeometry root{0.0, 0.8};
    const auto initial = ebrp::makeLegacyFrontierIntervals(0.0, 0.8, 4);
    std::string reason;
    require(ebrp::exactIntervalCoverage(root, initial, 1e-12, &reason),
            "legacy initial intervals must cover the root exactly");
    require(initial[0].upper == initial[1].lower,
            "adjacent children must overlap at exactly the shared boundary");
    auto generation = initial;
    for (int depth = 0; depth < 2; ++depth) {
        std::vector<ebrp::GiniIntervalGeometry> next;
        for (const auto& parent : generation) {
            const auto children = ebrp::splitLegacyFrontierInterval(
                parent.lower, parent.upper, 2);
            require(children.size() == 2,
                    "unchanged binary adaptive split must create two children");
            require(ebrp::exactIntervalCoverage(parent, children, 1e-12),
                    "recursive children must exactly cover every parent");
            next.insert(next.end(), children.begin(), children.end());
        }
        generation = std::move(next);
    }
    require(generation.size() == 16,
            "two adaptive generations after four initial leaves must yield sixteen leaves");
    require(ebrp::legacyAdaptiveSplitEligible(0.0, 0.2, 0, 2, 1e-4),
            "eligible interval unexpectedly rejected");
    require(!ebrp::legacyAdaptiveSplitEligible(0.0, 0.2, 2, 2, 1e-4),
            "maximum adaptive depth must be terminal");
}

void testFactoryAndRegistry() {
    const auto first = makeRows(0.1, 0.3);
    const auto second = makeRows(0.1, 0.3);
    require(first.complete_round18_static_migration,
            "Round 18 static family migration must be complete");
    require(first.unsupported_active_families.empty(),
            "official static profile must have no unsupported active family");
    require(first.aggregate_signature == second.aggregate_signature,
            "shared row factory aggregate signature must be deterministic");
    require(signatures(first) == signatures(second),
            "standalone fixed-interval and node-local signatures must match");

    const std::map<std::string, ebrp::IntervalRowScope> expected = {
        {"inventory_conservation", ebrp::IntervalRowScope::Global},
        {"movement_reachability_domains", ebrp::IntervalRowScope::Global},
        {"visit_inventory_linking", ebrp::IntervalRowScope::Global},
        {"global_handling_capacity", ebrp::IntervalRowScope::Global},
        {"support_duration", ebrp::IntervalRowScope::Global},
        {"transfer_compat", ebrp::IntervalRowScope::Global},
        {"direct_gini_cap_floor", ebrp::IntervalRowScope::IntervalLocal},
        {"interval_tight_mccormick", ebrp::IntervalRowScope::IntervalLocal},
        {"objective_estimator_cutoff", ebrp::IntervalRowScope::IntervalLocal},
        {"penalty_lb_closure", ebrp::IntervalRowScope::IntervalLocal},
        {"gini_spread", ebrp::IntervalRowScope::IntervalLocal},
        {"required_movement", ebrp::IntervalRowScope::IntervalLocal},
        {"low_gini_centering", ebrp::IntervalRowScope::IntervalLocal},
        {"variable_s_centering", ebrp::IntervalRowScope::IntervalLocal},
        {"sp_product_estimator", ebrp::IntervalRowScope::IntervalLocal}
    };
    std::set<std::string> seen;
    for (const auto& entry : first.family_registry) {
        const auto wanted = expected.find(entry.family);
        if (wanted == expected.end()) continue;
        require(entry.active && entry.implemented,
                "required Round 18 family must be active and implemented: " +
                    entry.family);
        require(entry.scope == wanted->second,
                "incorrect global/local family scope: " + entry.family);
        require(!entry.proof_tag.empty(),
                "family scope must carry a proof tag: " + entry.family);
        seen.insert(entry.family);
    }
    require(seen.size() == expected.size(),
            "not every Round 18 static paper-safe family was registered");

    const auto objective_row = std::find_if(
        first.rows.begin(), first.rows.end(), [](const auto& row) {
            return row.family == "verified_incumbent_objective_row";
        });
    require(objective_row != first.rows.end(),
            "same-run verified incumbent row is missing");
    require(std::fabs(objective_row->coefficients.at("G") - 1.0) < 1e-12,
            "incumbent row must preserve the original G objective coefficient");
    const auto instance = representativeInstance();
    for (int i = 1; i <= instance.V; ++i) {
        require(std::fabs(objective_row->coefficients.at(
                    "e_" + std::to_string(i)) -
                    0.15 * instance.weights[i]) < 1e-12,
                "incumbent row must preserve every original penalty coefficient");
    }
    require(std::fabs(objective_row->rhs - 0.8) < 1e-12,
            "official incumbent row must use U, never U-epsilon");
}

void testSiblingIsolation() {
    auto lower = makeRows(0.0, 0.2);
    const auto upper = makeRows(0.2, 0.4);
    require(lower.aggregate_signature != upper.aggregate_signature,
            "different sibling domains must have different local aggregates");
    bool bound_difference = false;
    for (const auto& left : lower.bound_changes) {
        for (const auto& right : upper.bound_changes) {
            if (left.variable == "G" && right.variable == "G" &&
                left.direction == right.direction &&
                std::fabs(left.value - right.value) > 1e-12) {
                bound_difference = true;
            }
        }
    }
    require(bound_difference,
            "siblings must retain distinct child-local G bounds");
    const std::string untouched = upper.aggregate_signature;
    lower.rows.clear();
    lower.bound_changes.clear();
    require(upper.aggregate_signature == untouched && !upper.rows.empty(),
            "child row containers must not be reused across siblings");
}

void testProjectedCenteringEquivalence() {
    const auto rows = makeRows(0.1, 0.3);
    std::size_t fixed_band_rows = 0;
    std::size_t variable_band_rows = 0;
    for (const auto& row : rows.rows) {
        if (row.family == "low_gini_centering_band") {
            ++fixed_band_rows;
        } else if (row.family == "variable_s_low_gini_centering") {
            ++variable_band_rows;
        } else {
            continue;
        }
        require(row.coefficients.count("r_min") == 0 &&
                    row.coefficients.count("r_max") == 0,
                "presolve-safe projected centering must not reference eliminable extrema");
    }
    const std::size_t expected_pair_rows =
        static_cast<std::size_t>(representativeInstance().V) *
        static_cast<std::size_t>(representativeInstance().V - 1);
    require(fixed_band_rows == expected_pair_rows,
            "fixed centering projection must contain both directions for every pair");
    require(variable_band_rows == expected_pair_rows,
            "variable-S centering projection must contain both directions for every pair");

    const std::vector<std::vector<double>> samples = {
        {0.8, 0.9, 1.0, 1.1},
        {0.1, 0.1, 0.1, 0.1},
        {0.2, 0.7, 0.4, 0.6}
    };
    for (const auto& ratios : samples) {
        const double minimum = *std::min_element(ratios.begin(), ratios.end());
        const double maximum = *std::max_element(ratios.begin(), ratios.end());
        const double range = maximum - minimum;
        double maximum_pair_difference = 0.0;
        for (std::size_t i = 0; i < ratios.size(); ++i) {
            for (std::size_t j = i + 1; j < ratios.size(); ++j) {
                maximum_pair_difference = std::max(
                    maximum_pair_difference,
                    std::fabs(ratios[i] - ratios[j]));
            }
        }
        require(std::fabs(range - maximum_pair_difference) < 1e-12,
                "pairwise centering is not the exact projection of r_min/r_max");
    }
}

void testObjectiveIdentityAndDomainEstimate() {
    const auto instance = representativeInstance();
    const auto options = round18StaticOptions();
    const std::vector<int> inventory = {0, 3, 7, 5, 2};
    const ebrp::ObjectiveParts parts =
        ebrp::computeObjectiveParts(instance, inventory, options.lambda);
    require(std::fabs(parts.objective -
                      (parts.G + options.lambda * parts.P)) < 1e-12,
            "authoritative objective must equal G + lambda P");

    for (int station = 1; station <= instance.V; ++station) {
        for (int lower = 0; lower <= instance.capacity[station]; ++lower) {
            for (int upper = lower; upper <= instance.capacity[station]; ++upper) {
                double exact = 1e100;
                for (int y = lower; y <= upper; ++y) {
                    exact = std::min(exact, std::fabs(
                        static_cast<double>(y) / instance.target[station] - 1.0));
                }
                double formula = 0.0;
                if (upper < instance.target[station]) {
                    formula = 1.0 - static_cast<double>(upper) /
                        instance.target[station];
                } else if (lower > instance.target[station]) {
                    formula = static_cast<double>(lower) /
                        instance.target[station] - 1.0;
                }
                require(std::fabs(exact - formula) < 1e-12,
                        "piecewise station deviation lower bound is not exact");
            }
        }
    }

    const auto child = makeRows(0.2, 0.3);
    const auto estimate = ebrp::computeChildDomainEstimate(
        instance, options, child.domain, 0.2, 0.17);
    require(estimate.valid, "valid child-domain estimate was rejected");
    require(estimate.final_estimate + 1e-12 >= 0.17,
            "child estimate must inherit the parent relaxation");
    require(std::fabs(estimate.domain_estimate -
        (0.2 + options.lambda * child.domain.penalty_lower)) < 1e-12,
        "domain estimate must contain only the proved gamma and penalty terms");

    double exact_inventory_optimum = 1e100;
    std::vector<int> y(instance.V + 1, 0);
    for (int y1 = child.domain.y_lower[1]; y1 <= child.domain.y_upper[1]; ++y1) {
        y[1] = y1;
        for (int y2 = child.domain.y_lower[2]; y2 <= child.domain.y_upper[2]; ++y2) {
            y[2] = y2;
            for (int y3 = child.domain.y_lower[3]; y3 <= child.domain.y_upper[3]; ++y3) {
                y[3] = y3;
                for (int y4 = child.domain.y_lower[4]; y4 <= child.domain.y_upper[4]; ++y4) {
                    y[4] = y4;
                    const auto candidate =
                        ebrp::computeObjectiveParts(instance, y, options.lambda);
                    if (candidate.G + 1e-12 >= 0.2 &&
                        candidate.G <= 0.3 + 1e-12) {
                        exact_inventory_optimum = std::min(
                            exact_inventory_optimum, candidate.objective);
                    }
                }
            }
        }
    }
    if (std::isfinite(exact_inventory_optimum) &&
        exact_inventory_optimum < 1e90) {
        require(estimate.domain_estimate <= exact_inventory_optimum + 1e-10,
                "domain estimate exceeded an exhaustive child optimum");
    }

    ebrp::IntervalDomainSummary infeasible = child.domain;
    infeasible.domain_infeasible = true;
    const auto rejected = ebrp::computeChildDomainEstimate(
        instance, options, infeasible, 0.2, 0.17);
    require(!rejected.valid && !rejected.failure_reason.empty(),
            "factory-detected infeasibility must fail closed");
}

void testExactIncrementalInheritance() {
    const auto parent = makeRows(0.0, 0.4);
    const auto child = makeRows(0.0, 0.2);
    auto inherited = ebrp::makeCanonicalInheritanceState(parent);
    require(inherited.valid, "parent canonical state construction failed");
    const auto delta = ebrp::computeExactIncrementalDelta(inherited, child);
    require(delta.valid, "exact incremental delta construction failed");
    require(delta.exact_duplicate_rows_omitted > 0,
            "expected inherited exact row duplicates were not detected");
    require(delta.dominance_omissions == 0,
            "Round 20 delta mode must not perform unproved dominance omission");
    require(!delta.rows_to_attach.empty(),
            "endpoint-dependent child rows must survive the delta");
    require(ebrp::mergeCanonicalInheritanceState(
                inherited, delta.rows_to_attach, delta.bounds_to_attach),
            "delta merge into inherited state failed");
    for (const auto& row : child.rows) {
        require(inherited.rows_by_signature.count(row.signature) == 1,
                "inherited parent plus delta is missing a complete-pack row");
    }
    for (const auto& bound : child.bound_changes) {
        const std::string key = bound.variable + "|" +
            std::string(1, bound.direction);
        require(inherited.effective_bounds_by_key.count(key) == 1,
                "inherited parent plus delta is missing a complete-pack bound");
    }

    ebrp::CanonicalInheritanceState collision =
        ebrp::makeCanonicalInheritanceState(parent);
    ebrp::CanonicalLinearRow forged = parent.rows.front();
    forged.rhs += 1.0;
    std::string failure;
    require(!ebrp::mergeCanonicalInheritanceState(
                collision, {forged}, {}, &failure) &&
                failure.find("collision") != std::string::npos,
            "ambiguous canonical signature matching must fail closed");
}

void testRootConnectivityFlowProjection() {
    const int V = 4;
    const std::vector<int> route = {0, 3, 1, 4, 0};
    std::map<std::pair<int, int>, double> x;
    std::map<std::pair<int, int>, double> flow;
    for (std::size_t pos = 1; pos < route.size(); ++pos) {
        const std::pair<int, int> arc{route[pos - 1], route[pos]};
        x[arc] = 1.0;
        flow[arc] = static_cast<double>(route.size() - 1 - pos);
    }
    const std::set<int> visited = {1, 3, 4};
    for (int i = 0; i <= V; ++i) {
        for (int j = 0; j <= V; ++j) {
            if (i == j) continue;
            const std::pair<int, int> arc{i, j};
            require(flow[arc] <= V * x[arc] + 1e-12,
                    "projected connectivity flow violates its arc link");
        }
    }
    for (int i = 1; i <= V; ++i) {
        double balance = 0.0;
        for (int j = 0; j <= V; ++j) {
            if (i == j) continue;
            balance += flow[{j, i}] - flow[{i, j}];
        }
        const double visit = visited.count(i) ? 1.0 : 0.0;
        require(std::fabs(balance - visit) < 1e-12,
                "route projection does not consume one flow unit per visit");
    }
    double depot_balance = 0.0;
    for (int j = 1; j <= V; ++j) {
        depot_balance += flow[{0, j}] - flow[{j, 0}];
    }
    require(std::fabs(depot_balance - static_cast<double>(visited.size())) < 1e-12,
            "route projection has the wrong depot supply");
}

void testCertificateGuard() {
    ebrp::SolveResult result;
    result.method = "gcap-frontier";
    result.frontier_execution_mode = "global-gini-tree";
    result.status = "optimal";
    result.objective = 0.5;
    result.lower_bound = 0.5;
    result.upper_bound = 0.5;
    result.gap = 0.0;
    result.option_audit_consistent = true;
    result.verification.feasible = true;
    result.verification.objective_matches = true;
    result.global_gini_tree_attempted = true;
    result.global_gini_tree_solved = true;
    result.global_gini_tree_solver_finalization_reached = true;
    result.global_gini_tree_native_best_bound_available = true;
    result.global_gini_tree_recursive_branching_complete = true;
    result.global_gini_tree_row_migration_complete = true;
    result.global_gini_tree_sibling_isolation_by_construction = true;
    result.global_gini_tree_root_coverage_valid = true;
    result.global_gini_tree_branch_coverage_valid = true;
    result.global_gini_tree_incumbent_verified = true;
    result.global_gini_tree_optimality_accepted = true;
    result.global_gini_tree_environment_count = 1;
    result.global_gini_tree_problem_count = 1;
    result.global_gini_tree_model_read_count = 1;
    result.global_gini_tree_mipopt_count = 1;
    result.global_gini_tree_freeprob_count = 1;
    result.global_gini_tree_close_count = 1;
    const std::string rejected = ebrp::resultToJson(result);
    require(rejected.find("not_certified_incomplete_certificate") !=
                std::string::npos,
            "lifecycle mismatch must reject an optimality claim");
    result.global_gini_tree_lifecycle_valid = true;
    result.strict_certified_original_problem = true;
    const std::string accepted = ebrp::resultToJson(result);
    require(accepted.find("\"status\": \"optimal\"") != std::string::npos,
            "complete global-tree audit should preserve optimal status");
}

} // namespace

int main() {
    try {
        testGeometry();
        testFactoryAndRegistry();
        testSiblingIsolation();
        testProjectedCenteringEquivalence();
        testObjectiveIdentityAndDomainEstimate();
        testExactIncrementalInheritance();
        testRootConnectivityFlowProjection();
        testCertificateGuard();
        std::cout << "GlobalGiniTreeTests: 8 groups passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "GlobalGiniTreeTests failed: " << error.what() << '\n';
        return 1;
    }
}
