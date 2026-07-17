#include "CplexBaseline.hpp"
#include "ConnectivityFlow.hpp"
#include "IntervalRowFactory.hpp"
#include "ControllingLeafScheduler.hpp"

#include "Evaluator.hpp"
#include "Logger.hpp"
#include "TailoredBC.hpp"
#include "TailoredBCCplexApi.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <limits>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <unordered_map>

namespace ebrp {
namespace {

using Clock = std::chrono::steady_clock;
using Expr = std::map<std::string, double>;

struct VarRegistry {
    std::map<std::string, std::pair<double, double>> bounds;
    std::set<std::string> binaries;
    std::set<std::string> generals;

    void add(const std::string& name, double lb, double ub, const std::string& type) {
        bounds[name] = {lb, ub};
        if (type == "B") binaries.insert(name);
        if (type == "I") generals.insert(name);
    }
};

struct CompactIntervalCutoffConfig {
    bool enabled = false;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    bool add_objective_cutoff = true;
    double incumbent_ub = 0.0;
    double epsilon = 1e-8;
};

struct CompactOracleStrengtheningStats {
    long long gini_spread_cuts_added = 0;
    long long direct_gini_cap_rows_added = 0;
    long long direct_gini_floor_rows_added = 0;
    long long tight_mccormick_rows_added = 0;
    long long inventory_conservation_rows_added = 0;
    long long movement_reachability_domains_tightened = 0;
    long long visit_inventory_linking_rows_added = 0;
    long long objective_estimator_cutoff_rows_added = 0;
    double penalty_lb = 0.0;
    long long penalty_lb_rows_added = 0;
    long long low_gini_centering_rows_added = 0;
    long long variable_s_centering_rows_added = 0;
    long long s_range_rows_added = 0;
    long long sp_product_mccormick_rows_added = 0;
    long long sp_product_estimator_rows_added = 0;
    long long tailored_gini_subset_envelope_candidates = 0;
    long long tailored_gini_subset_envelope_cuts_added = 0;
    long long tailored_low_gini_l1_vars = 0;
    long long tailored_low_gini_l1_rows_added = 0;
    long long tailored_local_centering_rows_added = 0;
    long long tailored_subset_cross_h_centering_rows_added = 0;
    long long tailored_subset_cross_h_centering_candidates = 0;
    long long tailored_local_q_centering_rows_added = 0;
    long long tailored_subset_inventory_imbalance_cuts_added = 0;
    long long tailored_bucket_ratio_domain_rows_added = 0;
    long long tailored_bucket_ratio_domain_bounds_tightened = 0;
    long long tailored_bucket_subset_ratio_domain_cuts_added = 0;
    long long tailored_bucket_subset_ratio_domain_candidates = 0;
    long long tailored_bucket_h_cap_rows_added = 0;
    long long bucket_integer_inventory_bounds_tightened = 0;
    long long bucket_integer_inventory_rows_added = 0;
    long long bucket_integer_inventory_lower_bounds_tightened = 0;
    long long bucket_integer_inventory_upper_bounds_tightened = 0;
    long long bucket_required_movement_rows_added = 0;
    long long bucket_required_visit_rows_added = 0;
    long long bucket_subset_required_movement_rows_added = 0;
    long long bucket_required_movement_violations = 0;
    double bucket_required_movement_max_violation = 0.0;
    long long tailored_transfer_cutset_cuts_added = 0;
    long long tailored_compatible_source_transfer_cuts_added = 0;
    long long tailored_compatible_source_transfer_candidates = 0;
    long long tailored_required_external_source_cuts_added = 0;
    long long tailored_benders_inventory_cuts_added = 0;
    long long tailored_benders_inventory_candidates = 0;
    long long gs_product_variable_added = 0;
    long long gs_mccormick_rows_added = 0;
    long long gs_h_upper_rows_added = 0;
    long long gs_h_lower_rows_added = 0;
    long long disagg_sp_variables_added = 0;
    long long disagg_sp_mccormick_rows_added = 0;
    long long disagg_sp_estimator_rows_added = 0;
    long long vector_support_cover_candidates = 0;
    long long vector_support_cover_cuts_added = 0;
    double vector_support_cover_max_violation = 0.0;
    long long vector_route_cutset_candidates = 0;
    long long vector_route_cutset_cuts_added = 0;
    double vector_route_cutset_max_violation = 0.0;
    bool s_range_refinement_enabled = false;
    double s_range_global_L = 0.0;
    double s_range_global_U = 0.0;
    int s_range_bucket_count = 0;
    int s_range_bucket_id = -1;
    double s_range_bucket_L = 0.0;
    double s_range_bucket_U = 0.0;
    bool s_range_parent_coverage_valid = false;
    bool s_range_certificate_valid = false;
    long long support_duration_pair_cuts_added = 0;
    long long support_duration_triple_cuts_added = 0;
    long long pairwise_transfer_compatibility_cuts_added = 0;
    long long receiver_source_cover_cuts_added = 0;
    double required_movement_lb = 0.0;
    long long required_movement_cuts_added = 0;
    double global_handling_capacity_lb = 0.0;
    long long global_handling_capacity_cuts_added = 0;
    long long transfer_subset_capacity_cuts_added = 0;
    long long low_gini_ratio_band_domains_tightened = 0;
    long long penalty_domains_tightened = 0;
    long long domain_width_before = 0;
    long long domain_width_after = 0;
    std::vector<std::string> enabled_families;
};

struct DynamicCut {
    Expr expr;
    std::string sense;
    double rhs = 0.0;
    std::string family;
    std::string signature;
    double violation = 0.0;
};

struct DynamicCutStats {
    long long support_duration = 0;
    long long route_cutset = 0;
    long long transfer_compat = 0;
    long long visit_inventory_linking = 0;
    long long objective_estimator = 0;
    long long receiver_source_cover = 0;
    long long total = 0;
    double support_duration_violation = 0.0;
    double route_cutset_violation = 0.0;
    double transfer_compat_violation = 0.0;
    double visit_inventory_linking_violation = 0.0;
    double objective_estimator_violation = 0.0;
    double receiver_source_cover_violation = 0.0;
    int rounds_completed = 0;
};

struct ModelSizeStats {
    long long rows = 0;
    long long cols = 0;
    long long nonzeros = 0;
    double memory_mb = 0.0;
};

void addTerm(Expr& e, const std::string& var, double coef) {
    if (std::fabs(coef) <= 1e-12) return;
    e[var] += coef;
    if (std::fabs(e[var]) <= 1e-12) e.erase(var);
}

std::string num(double v) {
    std::ostringstream ss;
    ss << std::setprecision(std::numeric_limits<double>::max_digits10) << v;
    return ss.str();
}

void writeExpr(std::ostream& out, const Expr& e) {
    if (e.empty()) {
        out << "0";
        return;
    }
    bool first = true;
    for (const auto& kv : e) {
        const double c = kv.second;
        if (first) {
            if (c < 0) out << "- ";
        } else {
            out << (c < 0 ? " - " : " + ");
        }
        const double a = std::fabs(c);
        if (std::fabs(a - 1.0) > 1e-12) out << num(a) << " ";
        out << kv.first;
        first = false;
    }
}

void writeConstraint(std::ostream& out,
                     int& id,
                     const Expr& e,
                     const std::string& sense,
                     double rhs) {
    out << " c" << id++ << ": ";
    writeExpr(out, e);
    out << " " << sense << " " << num(rhs) << "\n";
}

std::string xName(int k, int i, int j) { return "x_" + std::to_string(k) + "_" + std::to_string(i) + "_" + std::to_string(j); }
std::string zName(int k, int i) { return "z_" + std::to_string(k) + "_" + std::to_string(i); }
std::string pName(int k, int i) { return "p_" + std::to_string(k) + "_" + std::to_string(i); }
std::string dName(int k, int i) { return "d_" + std::to_string(k) + "_" + std::to_string(i); }
std::string lName(int k, int i) { return "load_" + std::to_string(k) + "_" + std::to_string(i); }
std::string uName(int k, int i) { return "ord_" + std::to_string(k) + "_" + std::to_string(i); }
std::string connectivityName(int k, int i, int j) { return "conn_" + std::to_string(k) + "_" + std::to_string(i) + "_" + std::to_string(j); }
std::string mName(int k, int i) { return "mode_" + std::to_string(k) + "_" + std::to_string(i); }
std::string yName(int i) { return "Y_" + std::to_string(i); }
std::string rName(int i) { return "r_" + std::to_string(i); }
std::string eName(int i) { return "e_" + std::to_string(i); }
std::string hName(int i, int j) { return "h_" + std::to_string(i) + "_" + std::to_string(j); }
std::string bitName(int i, int b) { return "bit_" + std::to_string(i) + "_" + std::to_string(b); }
std::string prodName(int i, int b) { return "prod_" + std::to_string(i) + "_" + std::to_string(b); }
std::string zprodName(int i) { return "zprod_" + std::to_string(i); }

std::vector<double> subsetTspLowerBounds(const Instance& instance) {
    const int V = instance.V;
    const int nmask = 1 << V;
    const double inf = 1e100;
    std::vector<std::vector<double>> dp(nmask, std::vector<double>(V, inf));
    for (int j = 0; j < V; ++j) dp[1 << j][j] = instance.dist[0][j + 1];
    for (int mask = 1; mask < nmask; ++mask) {
        for (int last = 0; last < V; ++last) {
            const double val = dp[mask][last];
            if (val >= inf / 2) continue;
            int rem = (nmask - 1) ^ mask;
            while (rem) {
                const int bit = rem & -rem;
                const int nxt = __builtin_ctz(static_cast<unsigned int>(bit));
                const int nm = mask | bit;
                dp[nm][nxt] = std::min(dp[nm][nxt], val + instance.dist[last + 1][nxt + 1]);
                rem -= bit;
            }
        }
    }
    std::vector<double> tsp(nmask, 0.0);
    for (int mask = 1; mask < nmask; ++mask) {
        double best = inf;
        int m = mask;
        while (m) {
            const int bit = m & -m;
            const int last = __builtin_ctz(static_cast<unsigned int>(bit));
            best = std::min(best, dp[mask][last] + instance.dist[last + 1][0]);
            m -= bit;
        }
        tsp[mask] = best;
    }
    return tsp;
}

double pairCycleLowerBound(const Instance& instance, int a, int b) {
    return std::min(instance.dist[0][a] + instance.dist[a][b] + instance.dist[b][0],
                    instance.dist[0][b] + instance.dist[b][a] + instance.dist[a][0]);
}

double tripleCycleLowerBound(const Instance& instance, int a, int b, int c) {
    const int s[3] = {a, b, c};
    double best = std::numeric_limits<double>::infinity();
    int perm[3] = {0, 1, 2};
    do {
        const double travel = instance.dist[0][s[perm[0]]] +
            instance.dist[s[perm[0]]][s[perm[1]]] +
            instance.dist[s[perm[1]]][s[perm[2]]] +
            instance.dist[s[perm[2]]][0];
        best = std::min(best, travel);
    } while (std::next_permutation(perm, perm + 3));
    return best;
}

double subsetCycleLowerBound(const Instance& instance, const std::vector<int>& subset) {
    if (subset.empty()) return 0.0;
    if (subset.size() == 1) {
        const int a = subset.front();
        return instance.dist[0][a] + instance.dist[a][0];
    }
    if (subset.size() == 2) {
        return pairCycleLowerBound(instance, subset[0], subset[1]);
    }
    if (subset.size() == 3) {
        return tripleCycleLowerBound(instance, subset[0], subset[1], subset[2]);
    }
    std::vector<int> perm = subset;
    std::sort(perm.begin(), perm.end());
    double best = std::numeric_limits<double>::infinity();
    do {
        double travel = instance.dist[0][perm.front()];
        for (std::size_t i = 1; i < perm.size(); ++i) {
            travel += instance.dist[perm[i - 1]][perm[i]];
        }
        travel += instance.dist[perm.back()][0];
        best = std::min(best, travel);
    } while (std::next_permutation(perm.begin(), perm.end()));
    return best;
}

template <typename Fn>
void enumerateStationSubsets(int V, int size, Fn&& fn) {
    std::vector<int> subset;
    std::function<void(int)> rec = [&](int start) {
        if (static_cast<int>(subset.size()) == size) {
            fn(subset);
            return;
        }
        const int remaining = size - static_cast<int>(subset.size());
        for (int i = start; i <= V - remaining + 1; ++i) {
            subset.push_back(i);
            rec(i + 1);
            subset.pop_back();
        }
    };
    rec(1);
}

std::string joinFamilies(const std::vector<std::string>& families) {
    if (families.empty()) return "none";
    std::ostringstream out;
    for (std::size_t i = 0; i < families.size(); ++i) {
        if (i) out << "|";
        out << families[i];
    }
    return out.str();
}

void writeCompactLp(const Instance& instance,
                    const SolveOptions& options,
                    const std::filesystem::path& lp_path,
                    bool strengthened,
                    const CompactIntervalCutoffConfig* cutoff = nullptr,
                    CompactOracleStrengtheningStats* stats = nullptr,
                    const std::vector<DynamicCut>* dynamic_cuts = nullptr) {
    VarRegistry vars;
    const int V = instance.V;
    const int M = instance.M;
    const double cunit = instance.pickup_time + instance.drop_time;
    const ConnectivityFlowVariantResolution flow_resolution =
        resolveConnectivityFlowVariant(
            options.global_gini_tree_root_connectivity_flow,
            options.global_gini_tree_root_connectivity_flow_variant);
    if (!flow_resolution.valid) {
        throw std::runtime_error(
            "invalid root connectivity-flow configuration: " +
            flow_resolution.failure_reason);
    }
    const ConnectivityFlowVariant flow_variant = flow_resolution.variant;

    std::vector<int> y_lb(V + 1, 0);
    std::vector<int> y_ub(V + 1, 0);
    bool domain_infeasible = false;
    for (int i = 1; i <= V; ++i) {
        y_ub[i] = instance.capacity[i];
        if (stats != nullptr) {
            stats->domain_width_before += instance.capacity[i];
        }
    }
    const bool cutoff_active =
        cutoff != nullptr && cutoff->enabled &&
        std::isfinite(cutoff->incumbent_ub) &&
        options.lambda > 1e-12;
    const double cutoff_value = cutoff_active
        ? cutoff->incumbent_ub - cutoff->epsilon
        : std::numeric_limits<double>::infinity();
    const double penalty_budget = cutoff_active
        ? (cutoff_value - cutoff->gamma_L) / options.lambda
        : std::numeric_limits<double>::infinity();
    if (cutoff_active &&
        std::isfinite(penalty_budget) &&
        penalty_budget >= -1e-10 &&
        (options.interval_oracle_penalty_domain_tightening ||
         options.interval_oracle_low_gini_tightening ||
         options.low_gini_ratio_band_tightening)) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("penalty_final_inventory_domain");
        }
        for (int i = 1; i <= V; ++i) {
            if (instance.weights[i] <= 1e-12) continue;
            const double ratio_radius = std::max(0.0, penalty_budget / instance.weights[i]);
            int lo = static_cast<int>(std::ceil(instance.target[i] * (1.0 - ratio_radius) - 1e-9));
            int hi = static_cast<int>(std::floor(instance.target[i] * (1.0 + ratio_radius) + 1e-9));
            lo = std::max(0, lo);
            hi = std::min(instance.capacity[i], hi);
            if (lo > y_lb[i]) {
                y_lb[i] = lo;
                if (stats != nullptr) ++stats->penalty_domains_tightened;
            }
            if (hi < y_ub[i]) {
                y_ub[i] = hi;
                if (stats != nullptr) ++stats->penalty_domains_tightened;
            }
        }
    }
    if (strengthened && options.compact_bc_movement_reachability_domains) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("movement_reachability_final_inventory_domain");
        }
        for (int i = 1; i <= V; ++i) {
            int pickup_reach = 0;
            int drop_reach = 0;
            for (int k = 0; k < M; ++k) {
                const double rt_lb = instance.dist[0][i] + instance.dist[i][0];
                int move_budget = 0;
                if (instance.total_time_limit + 1e-9 >= rt_lb && cunit > 1e-12) {
                    move_budget = static_cast<int>(
                        std::floor((instance.total_time_limit - rt_lb) / cunit + 1e-9));
                }
                pickup_reach = std::max(pickup_reach,
                    std::min({instance.initial[i], instance.Q[k], move_budget}));
                drop_reach = std::max(drop_reach,
                    std::min({instance.capacity[i] - instance.initial[i],
                              instance.Q[k], move_budget}));
            }
            const int reach_lo = std::max(0, instance.initial[i] - pickup_reach);
            const int reach_hi = std::min(instance.capacity[i],
                                          instance.initial[i] + drop_reach);
            if (reach_lo > y_lb[i]) {
                y_lb[i] = reach_lo;
                if (stats != nullptr) ++stats->movement_reachability_domains_tightened;
            }
            if (reach_hi < y_ub[i]) {
                y_ub[i] = reach_hi;
                if (stats != nullptr) ++stats->movement_reachability_domains_tightened;
            }
        }
    }
    for (int i = 1; i <= V; ++i) {
        if (y_lb[i] > y_ub[i]) {
            domain_infeasible = true;
            y_lb[i] = 0;
            y_ub[i] = instance.capacity[i];
        }
        if (stats != nullptr) {
            stats->domain_width_after += std::max(0, y_ub[i] - y_lb[i]);
            if (y_lb[i] > 0 || y_ub[i] < instance.capacity[i]) {
                ++stats->low_gini_ratio_band_domains_tightened;
            }
        }
    }
    double s_lower_domain = 0.0;
    double s_upper_domain = 0.0;
    double penalty_lb_domain = 0.0;
    double penalty_ub_domain = 0.0;
    std::vector<double> e_lower_domain(V + 1, 0.0);
    std::vector<double> e_upper_domain(V + 1, 0.0);
    for (int i = 1; i <= V; ++i) {
        const double target = std::max(1e-12, static_cast<double>(instance.target[i]));
        const double r_lo = static_cast<double>(y_lb[i]) / target;
        const double r_hi = static_cast<double>(y_ub[i]) / target;
        s_lower_domain += r_lo;
        s_upper_domain += r_hi;
        double e_lb = 0.0;
        if (r_hi < 1.0) {
            e_lb = 1.0 - r_hi;
        } else if (r_lo > 1.0) {
            e_lb = r_lo - 1.0;
        }
        const double e_ub = std::max(std::fabs(r_lo - 1.0),
                                     std::fabs(r_hi - 1.0));
        e_lower_domain[i] = std::max(0.0, e_lb);
        e_upper_domain[i] = std::max(e_lower_domain[i], e_ub);
        penalty_lb_domain += instance.weights[i] * std::max(0.0, e_lb);
        penalty_ub_domain += instance.weights[i] * std::max(0.0, e_ub);
    }
    if (penalty_ub_domain < penalty_lb_domain) {
        penalty_ub_domain = penalty_lb_domain;
    }
    double s_bucket_L = s_lower_domain;
    double s_bucket_U = s_upper_domain;
    const bool s_range_requested =
        strengthened && cutoff != nullptr && cutoff->enabled &&
        options.compact_bc_s_range_refinement != "off";
    bool s_range_rows_active = false;
    if (s_range_requested) {
        if (options.compact_bc_s_range_bucket_L >= 0.0 &&
            options.compact_bc_s_range_bucket_U >= options.compact_bc_s_range_bucket_L - 1e-12) {
            s_bucket_L = std::max(s_lower_domain, options.compact_bc_s_range_bucket_L);
            s_bucket_U = std::min(s_upper_domain, options.compact_bc_s_range_bucket_U);
            s_range_rows_active = s_bucket_U >= s_bucket_L - 1e-12;
        } else if (options.compact_bc_s_range_refinement == "diagnostic" &&
                   options.compact_bc_s_range_buckets > 1 &&
                   options.compact_bc_s_range_bucket_id >= 0 &&
                   s_upper_domain > s_lower_domain + 1e-12) {
            const int bucket_count = std::max(1, options.compact_bc_s_range_buckets);
            const int bucket_id = std::min(bucket_count - 1,
                                           options.compact_bc_s_range_bucket_id);
            const double width = (s_upper_domain - s_lower_domain) /
                static_cast<double>(bucket_count);
            s_bucket_L = s_lower_domain + width * static_cast<double>(bucket_id);
            s_bucket_U = (bucket_id == bucket_count - 1)
                ? s_upper_domain
                : s_bucket_L + width;
            s_range_rows_active = true;
        } else if (options.compact_bc_s_range_refinement == "paper-safe" &&
                   options.compact_bc_s_range_buckets <= 1) {
            s_range_rows_active = true;
        }
    }
    if (stats != nullptr) {
        stats->s_range_refinement_enabled = s_range_requested;
        stats->s_range_global_L = s_lower_domain;
        stats->s_range_global_U = s_upper_domain;
        stats->s_range_bucket_count = s_range_requested
            ? std::max(1, options.compact_bc_s_range_buckets)
            : 0;
        stats->s_range_bucket_id = options.compact_bc_s_range_bucket_id;
        stats->s_range_bucket_L = s_bucket_L;
        stats->s_range_bucket_U = s_bucket_U;
        stats->s_range_parent_coverage_valid =
            options.compact_bc_s_range_refinement == "paper-safe" &&
            options.compact_bc_s_range_buckets <= 1;
        stats->s_range_certificate_valid =
            options.compact_bc_s_range_refinement == "paper-safe" &&
            s_range_rows_active;
    }

    const bool tailored_active = strengthened && options.tailored_bc_enabled;
    const bool add_bucket_ratio_domain =
        strengthened && tailored_active && cutoff != nullptr && cutoff->enabled &&
        s_range_rows_active && options.tailored_bc_bucket_ratio_domain_tightening &&
        cutoff->gamma_U >= -1e-12 && s_bucket_U >= s_bucket_L - 1e-12;
    const bool add_bucket_subset_ratio_domain =
        strengthened && tailored_active && cutoff != nullptr && cutoff->enabled &&
        s_range_rows_active && options.tailored_bc_bucket_subset_ratio_domain &&
        cutoff->gamma_U >= -1e-12 && s_bucket_U >= s_bucket_L - 1e-12;
    const std::string bucket_inventory_mode =
        options.tailored_bc_bucket_integer_inventory_domain_mode.empty()
            ? "static"
            : options.tailored_bc_bucket_integer_inventory_domain_mode;
    const bool add_bucket_integer_inventory_domain =
        strengthened && tailored_active && cutoff != nullptr && cutoff->enabled &&
        s_range_rows_active && options.tailored_bc_bucket_integer_inventory_domain &&
        (bucket_inventory_mode == "static" || bucket_inventory_mode == "both") &&
        cutoff->gamma_U >= -1e-12 && s_bucket_U >= s_bucket_L - 1e-12;
    if (add_bucket_ratio_domain || add_bucket_integer_inventory_domain) {
        const double upper_factor = 1.0 / static_cast<double>(V) + cutoff->gamma_U;
        const double lower_factor = 1.0 / static_cast<double>(V) - cutoff->gamma_U;
        for (int i = 1; i <= V; ++i) {
            const double target = std::max(1e-12, static_cast<double>(instance.target[i]));
            const double r_hi = std::max(0.0, upper_factor * s_bucket_U);
            const int y_hi =
                std::min(instance.capacity[i],
                         static_cast<int>(std::floor(target * r_hi + 1e-9)));
            if (y_hi < y_ub[i]) {
                y_ub[i] = std::max(y_lb[i], y_hi);
                if (stats != nullptr) {
                    if (add_bucket_ratio_domain) ++stats->tailored_bucket_ratio_domain_bounds_tightened;
                    if (add_bucket_integer_inventory_domain) {
                        ++stats->bucket_integer_inventory_bounds_tightened;
                        ++stats->bucket_integer_inventory_upper_bounds_tightened;
                    }
                }
            }
            if (lower_factor > 1e-12) {
                const double r_lo = std::max(0.0, lower_factor * s_bucket_L);
                const int y_lo =
                    std::max(0, static_cast<int>(std::ceil(target * r_lo - 1e-9)));
                if (y_lo > y_lb[i]) {
                    y_lb[i] = std::min(y_ub[i], y_lo);
                    if (stats != nullptr) {
                        if (add_bucket_ratio_domain) ++stats->tailored_bucket_ratio_domain_bounds_tightened;
                        if (add_bucket_integer_inventory_domain) {
                            ++stats->bucket_integer_inventory_bounds_tightened;
                            ++stats->bucket_integer_inventory_lower_bounds_tightened;
                        }
                    }
                }
            }
        }
        if (stats != nullptr) {
            if (add_bucket_ratio_domain) {
                stats->enabled_families.push_back("bucket_ratio_domain_tightening");
            }
            if (add_bucket_integer_inventory_domain) {
                stats->enabled_families.push_back("bucket_integer_inventory_domain");
            }
        }
    }

    IntervalRowFactoryResult shared_interval_rows;
    const bool use_shared_interval_rows =
        options.interval_row_factory_round19 && cutoff != nullptr &&
        cutoff->enabled && strengthened;
    if (use_shared_interval_rows) {
        IntervalRowFactoryRequest request;
        request.gamma_L = cutoff->gamma_L;
        request.gamma_U = cutoff->gamma_U;
        request.verified_incumbent = cutoff->incumbent_ub;
        request.incumbent_epsilon = cutoff->epsilon;
        request.add_incumbent_row = cutoff->add_objective_cutoff;
        request.strengthened = strengthened;
        shared_interval_rows = buildRound18StaticIntervalRows(
            instance, options, request);
        y_lb = shared_interval_rows.domain.y_lower;
        y_ub = shared_interval_rows.domain.y_upper;
        domain_infeasible = shared_interval_rows.domain.domain_infeasible;
        s_lower_domain = shared_interval_rows.domain.s_lower;
        s_upper_domain = shared_interval_rows.domain.s_upper;
        penalty_lb_domain = shared_interval_rows.domain.penalty_lower;
        penalty_ub_domain = shared_interval_rows.domain.penalty_upper;
        e_lower_domain = shared_interval_rows.domain.e_lower;
        e_upper_domain = shared_interval_rows.domain.e_upper;
    }

    for (int k = 0; k < M; ++k) {
        for (int i = 0; i <= V; ++i) {
            for (int j = 0; j <= V; ++j) {
                if (i != j) {
                    vars.add(xName(k, i, j), 0, 1, "B");
                    const std::optional<double> flow_upper =
                        connectivityFlowArcUpperBound(flow_variant, V, i, j);
                    if (flow_upper.has_value()) {
                        vars.add(connectivityName(k, i, j), 0,
                                 *flow_upper, "C");
                    }
                }
            }
        }
        for (int i = 1; i <= V; ++i) {
            const int pmax = std::min(instance.initial[i], instance.Q[k]);
            const int dmax = std::min(instance.capacity[i] - instance.initial[i], instance.Q[k]);
            vars.add(zName(k, i), 0, 1, "B");
            vars.add(mName(k, i), 0, 1, "B");
            vars.add(pName(k, i), 0, pmax, "I");
            vars.add(dName(k, i), 0, dmax, "I");
            vars.add(lName(k, i), 0, instance.Q[k], "I");
            vars.add(uName(k, i), 0, V, "C");
        }
    }
    const double g_lb = (cutoff != nullptr && cutoff->enabled)
        ? std::max(0.0, cutoff->gamma_L)
        : 0.0;
    const double g_ub = (cutoff != nullptr && cutoff->enabled)
        ? std::min(1.0, std::max(cutoff->gamma_L, cutoff->gamma_U))
        : 1.0;
    vars.add("G", g_lb, g_ub, "C");
    double max_ratio_cap = 0.0;
    for (int i = 1; i <= V; ++i) {
        max_ratio_cap = std::max(max_ratio_cap,
            static_cast<double>(instance.capacity[i]) / instance.target[i]);
    }
    const bool add_low_gini_centering =
        strengthened && cutoff != nullptr && cutoff->enabled &&
        options.low_gini_ratio_band_tightening && options.compact_bc_direct_gini_rows &&
        V > 1;
    if (add_low_gini_centering) {
        vars.add("r_min", 0, max_ratio_cap, "C");
        vars.add("r_max", 0, max_ratio_cap, "C");
    }
    for (int i = 1; i <= V; ++i) {
        vars.add(yName(i), y_lb[i], y_ub[i], "I");
        vars.add(rName(i), 0, static_cast<double>(instance.capacity[i]) / instance.target[i], "C");
        vars.add(eName(i), 0, std::max(1.0, static_cast<double>(instance.capacity[i]) / instance.target[i] - 1.0), "C");
        if (tailored_active && options.tailored_bc_low_gini_l1_centering &&
            cutoff != nullptr && cutoff->enabled && cutoff->gamma_U >= -1e-12) {
            vars.add("q_l1_" + std::to_string(i), 0,
                     static_cast<double>(instance.capacity[i]) / instance.target[i] + max_ratio_cap,
                     "C");
            if (stats != nullptr) ++stats->tailored_low_gini_l1_vars;
        }
        vars.add(zprodName(i), 0, instance.capacity[i], "C");
        int bits = 1;
        while (((1LL << bits) - 1) < instance.capacity[i]) ++bits;
        for (int b = 0; b < bits; ++b) {
            vars.add(bitName(i, b), 0, 1, "B");
            vars.add(prodName(i, b), 0, g_ub, "C");
        }
    }
    for (int i = 1; i <= V; ++i) {
        for (int j = i + 1; j <= V; ++j) {
            const double ub = static_cast<double>(instance.capacity[i]) / instance.target[i]
                + static_cast<double>(instance.capacity[j]) / instance.target[j];
            vars.add(hName(i, j), 0, ub, "C");
        }
    }
    const double sp_s_lower = s_range_rows_active ? s_bucket_L : s_lower_domain;
    const double sp_s_upper = s_range_rows_active ? s_bucket_U : s_upper_domain;
    const bool add_disagg_sp_definition =
        strengthened && tailored_active && cutoff != nullptr && cutoff->enabled &&
        cutoff->add_objective_cutoff &&
        options.tailored_bc_disaggregated_sp_estimator &&
        s_range_rows_active &&
        sp_s_upper >= sp_s_lower - 1e-12;
    const bool add_disagg_sp_estimator =
        add_disagg_sp_definition &&
        (options.tailored_bc_disaggregated_sp_mode == "static" ||
         options.tailored_bc_disaggregated_sp_mode == "both");
    const bool add_sp_product_estimator =
        strengthened && cutoff != nullptr && cutoff->enabled &&
        cutoff->add_objective_cutoff &&
        options.compact_bc_sp_product_estimator != "off" &&
        s_upper_domain > s_lower_domain - 1e-12 &&
        penalty_ub_domain >= penalty_lb_domain - 1e-12 &&
        !(add_disagg_sp_definition &&
          options.tailored_bc_disaggregated_sp_replace_aggregate);
    if (add_sp_product_estimator) {
        const double w_lb = std::max(0.0, sp_s_lower * penalty_lb_domain);
        const double w_ub = std::max(w_lb, sp_s_upper * penalty_ub_domain);
        vars.add("W_SP", w_lb, w_ub, "C");
    }
    const bool add_gs_product_definition =
        strengthened && tailored_active && cutoff != nullptr && cutoff->enabled &&
        options.tailored_bc_gs_product_coupling &&
        s_range_rows_active &&
        sp_s_upper >= sp_s_lower - 1e-12;
    const bool add_gs_product_static_row =
        add_gs_product_definition &&
        (options.tailored_bc_gs_product_coupling_mode == "static" ||
         options.tailored_bc_gs_product_coupling_mode == "both");
    if (add_gs_product_definition) {
        const double w_lb = std::max(0.0, g_lb * sp_s_lower);
        const double w_ub = std::max(w_lb, g_ub * sp_s_upper);
        vars.add("W_GS", w_lb, w_ub, "C");
        if (stats != nullptr) ++stats->gs_product_variable_added;
    }
    if (add_disagg_sp_definition) {
        for (int i = 1; i <= V; ++i) {
            const double t_lb = std::max(0.0, sp_s_lower * e_lower_domain[i]);
            const double t_ub = std::max(t_lb, sp_s_upper * e_upper_domain[i]);
            vars.add("T_SP_" + std::to_string(i), t_lb, t_ub, "C");
            if (stats != nullptr) ++stats->disagg_sp_variables_added;
        }
    }

    std::filesystem::create_directories(lp_path.parent_path());
    std::ofstream out(lp_path);
    if (!out) throw std::runtime_error("Cannot write CPLEX LP: " + lp_path.string());
    out << std::setprecision(std::numeric_limits<double>::max_digits10);
    out << "\\ ExactEBRP compact MILP generated from C++ command-line runner\n";
    out << "Minimize\n obj: G";
    for (int i = 1; i <= V; ++i) {
        const double coef = options.lambda * instance.weights[i];
        if (coef >= 0) out << " + " << num(coef) << " " << eName(i);
        else out << " - " << num(-coef) << " " << eName(i);
    }
    out << "\nSubject To\n";

    int cid = 1;
    if (use_shared_interval_rows) {
        for (const CanonicalLinearRow& row : shared_interval_rows.rows) {
            Expr expression;
            for (const auto& coefficient : row.coefficients) {
                addTerm(expression, coefficient.first, coefficient.second);
            }
            const std::string sense = row.sense == 'G'
                ? ">=" : (row.sense == 'E' ? "=" : "<=");
            writeConstraint(out, cid, expression, sense, row.rhs);
            if (stats == nullptr) continue;
            if (row.family == "direct_gini_cap") {
                ++stats->direct_gini_cap_rows_added;
            } else if (row.family == "direct_gini_floor") {
                ++stats->direct_gini_floor_rows_added;
            } else if (row.family == "interval_tight_mccormick_G_bit") {
                ++stats->tight_mccormick_rows_added;
            } else if (row.family == "gini_pairwise_spread") {
                ++stats->gini_spread_cuts_added;
            } else if (row.family == "required_station_movement") {
                ++stats->required_movement_cuts_added;
            } else if (row.family == "low_gini_centering_band") {
                ++stats->low_gini_centering_rows_added;
            } else if (row.family == "variable_s_low_gini_centering") {
                ++stats->variable_s_centering_rows_added;
            } else if (row.family == "objective_lower_estimator_cutoff") {
                ++stats->objective_estimator_cutoff_rows_added;
            } else if (row.family == "penalty_lower_bound_closure") {
                ++stats->penalty_lb_rows_added;
            } else if (row.family == "sp_product_mccormick") {
                ++stats->sp_product_mccormick_rows_added;
            } else if (row.family ==
                       "sp_product_objective_estimator_paper_safe") {
                ++stats->sp_product_estimator_rows_added;
            }
        }
        if (stats != nullptr) {
            for (const std::string& family : shared_interval_rows.active_families) {
                stats->enabled_families.push_back(family);
            }
            stats->penalty_lb = shared_interval_rows.domain.penalty_lower;
        }
    }
    if (domain_infeasible) {
        Expr impossible;
        writeConstraint(out, cid, impossible, "<=", -1);
    }
    for (int k = 0; k < M; ++k) {
        Expr start_end;
        Expr start;
        for (int j = 1; j <= V; ++j) {
            addTerm(start, xName(k, 0, j), 1);
            addTerm(start_end, xName(k, 0, j), 1);
            addTerm(start_end, xName(k, j, 0), -1);
        }
        writeConstraint(out, cid, start_end, "=", 0);
        writeConstraint(out, cid, start, "<=", 1);
        for (int i = 1; i <= V; ++i) {
            Expr in_flow;
            Expr out_flow;
            for (int j = 0; j <= V; ++j) {
                if (j == i) continue;
                addTerm(in_flow, xName(k, j, i), 1);
                addTerm(out_flow, xName(k, i, j), 1);
            }
            addTerm(in_flow, zName(k, i), -1);
            addTerm(out_flow, zName(k, i), -1);
            writeConstraint(out, cid, in_flow, "=", 0);
            writeConstraint(out, cid, out_flow, "=", 0);
        }
    }

    // Optional scalable connectivity-flow family.  F0 is the Round 20 model;
    // F1 removes all return-flow columns, F2 adds f>=x normalization and
    // tighter internal-arc bounds, and F3 couples the start flow to the number
    // of visited stations.  Every elementary depot-closed route has the
    // canonical downstream-count projection implemented in ConnectivityFlow.
    if (connectivityFlowEnabled(flow_variant)) {
        for (int k = 0; k < M; ++k) {
            for (int i = 0; i <= V; ++i) {
                for (int j = 0; j <= V; ++j) {
                    const std::optional<double> flow_upper =
                        connectivityFlowArcUpperBound(flow_variant, V, i, j);
                    if (!flow_upper.has_value()) continue;
                    Expr link;
                    addTerm(link, connectivityName(k, i, j), 1.0);
                    addTerm(link, xName(k, i, j), -*flow_upper);
                    writeConstraint(out, cid, link, "<=", 0.0);
                    if (connectivityFlowHasLowerLinks(flow_variant)) {
                        Expr lower_link;
                        addTerm(lower_link, connectivityName(k, i, j), 1.0);
                        addTerm(lower_link, xName(k, i, j), -1.0);
                        writeConstraint(out, cid, lower_link, ">=", 0.0);
                    }
                }
            }
            for (int i = 1; i <= V; ++i) {
                Expr balance;
                for (int j = 0; j <= V; ++j) {
                    if (i == j) continue;
                    if (hasConnectivityFlowColumn(flow_variant, V, j, i)) {
                        addTerm(balance, connectivityName(k, j, i), 1.0);
                    }
                    if (hasConnectivityFlowColumn(flow_variant, V, i, j)) {
                        addTerm(balance, connectivityName(k, i, j), -1.0);
                    }
                }
                addTerm(balance, zName(k, i), -1.0);
                writeConstraint(out, cid, balance, "=", 0.0);
            }
            Expr depot_balance;
            for (int j = 1; j <= V; ++j) {
                addTerm(depot_balance, connectivityName(k, 0, j), 1.0);
                if (hasConnectivityFlowColumn(flow_variant, V, j, 0)) {
                    addTerm(depot_balance, connectivityName(k, j, 0), -1.0);
                }
                addTerm(depot_balance, zName(k, j), -1.0);
            }
            writeConstraint(out, cid, depot_balance, "=", 0.0);
            if (connectivityFlowHasStartCoupling(flow_variant)) {
                for (int j = 1; j <= V; ++j) {
                    Expr start_upper;
                    addTerm(start_upper, connectivityName(k, 0, j), 1.0);
                    for (int i = 1; i <= V; ++i) {
                        addTerm(start_upper, zName(k, i), -1.0);
                    }
                    writeConstraint(out, cid, start_upper, "<=", 0.0);

                    Expr start_lower = start_upper;
                    addTerm(start_lower, xName(k, 0, j),
                            -static_cast<double>(V));
                    writeConstraint(out, cid, start_lower, ">=",
                                    -static_cast<double>(V));
                }
            }
        }
    }

    for (int i = 1; i <= V; ++i) {
        Expr e;
        for (int k = 0; k < M; ++k) addTerm(e, zName(k, i), 1);
        writeConstraint(out, cid, e, "<=", 1);
    }

    if (strengthened && options.compact_bc_inventory_conservation) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("total_station_inventory_conservation");
        }
        double initial_total = 0.0;
        for (int i = 1; i <= V; ++i) initial_total += instance.initial[i];
        double q_total = 0.0;
        for (int q : instance.Q) q_total += q;
        Expr y_total;
        for (int i = 1; i <= V; ++i) addTerm(y_total, yName(i), 1);
        writeConstraint(out, cid, y_total, "<=", initial_total);
        if (stats != nullptr) ++stats->inventory_conservation_rows_added;
        Expr y_total_lb = y_total;
        writeConstraint(out, cid, y_total_lb, ">=", initial_total - q_total);
        if (stats != nullptr) ++stats->inventory_conservation_rows_added;
    }

    if (strengthened && options.transfer_subset_capacity_cuts) {
        if (stats != nullptr) stats->enabled_families.push_back("duration_compatibility_singleton_transfer");
        for (int k = 0; k < M; ++k) {
            for (int i = 1; i <= V; ++i) {
                const double min_visit_time = instance.dist[0][i] + instance.dist[i][0] + cunit;
                if (min_visit_time > instance.total_time_limit + 1e-9) {
                    Expr e;
                    addTerm(e, zName(k, i), 1);
                    writeConstraint(out, cid, e, "<=", 0);
                    if (stats != nullptr) ++stats->transfer_subset_capacity_cuts_added;
                }
            }
        }
    }
    if (strengthened && options.compact_bc_pairwise_transfer_compatibility) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("pairwise_transfer_compatibility");
        }
        for (int k = 0; k < M; ++k) {
            for (int j = 1; j <= V; ++j) {
                Expr compat;
                addTerm(compat, dName(k, j), 1);
                int compatible_pickups = 0;
                for (int i = 1; i <= V; ++i) {
                    if (i == j) continue;
                    const double route_lb = instance.dist[0][i] +
                        instance.dist[i][j] + instance.dist[j][0] + cunit;
                    if (route_lb <= instance.total_time_limit + 1e-9) {
                        addTerm(compat, pName(k, i), -1);
                        ++compatible_pickups;
                    }
                }
                writeConstraint(out, cid, compat, "<=", 0);
                if (stats != nullptr) ++stats->pairwise_transfer_compatibility_cuts_added;
                (void)compatible_pickups;
            }
        }
    }

    if (strengthened && options.compact_bc_receiver_source_cover_cuts) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("receiver_source_cover_singleton_safe");
        }
        for (int j = 1; j <= V; ++j) {
            const int required_delivery =
                std::max(0, y_lb[j] - instance.initial[j]);
            if (required_delivery <= 0) continue;
            Expr delivery;
            for (int k = 0; k < M; ++k) {
                addTerm(delivery, dName(k, j), 1);
            }
            writeConstraint(out, cid, delivery, ">=", required_delivery);
            if (stats != nullptr) ++stats->receiver_source_cover_cuts_added;
        }
        if (options.compact_bc_receiver_source_cover_mode == "pair-net-paper-safe" ||
            options.compact_bc_receiver_source_cover_mode == "paper-safe") {
            if (stats != nullptr) {
                stats->enabled_families.push_back("receiver_source_cover_pair_net_safe");
            }
            for (int a = 1; a <= V; ++a) {
                for (int b = a + 1; b <= V; ++b) {
                    const int required_net = std::max(
                        0,
                        y_lb[a] + y_lb[b] -
                            instance.initial[a] - instance.initial[b]);
                    if (required_net <= 0) continue;
                    Expr net_pair;
                    for (int k = 0; k < M; ++k) {
                        addTerm(net_pair, dName(k, a), 1);
                        addTerm(net_pair, dName(k, b), 1);
                        addTerm(net_pair, pName(k, a), -1);
                        addTerm(net_pair, pName(k, b), -1);
                    }
                    writeConstraint(out, cid, net_pair, ">=", required_net);
                    if (stats != nullptr) ++stats->receiver_source_cover_cuts_added;
                    for (int k = 0; k < M; ++k) {
                        Expr source_cover;
                        addTerm(source_cover, dName(k, a), 1);
                        addTerm(source_cover, dName(k, b), 1);
                        addTerm(source_cover, pName(k, a), -1);
                        addTerm(source_cover, pName(k, b), -1);
                        for (int i = 1; i <= V; ++i) {
                            if (i == a || i == b) continue;
                            addTerm(source_cover, pName(k, i), -1);
                        }
                        writeConstraint(out, cid, source_cover, "<=", 0);
                        if (stats != nullptr) ++stats->receiver_source_cover_cuts_added;
                    }
                }
            }
        }
    }

    for (int k = 0; k < M; ++k) {
        for (int i = 1; i <= V; ++i) {
            Expr lb; addTerm(lb, uName(k, i), 1); addTerm(lb, zName(k, i), -1);
            writeConstraint(out, cid, lb, ">=", 0);
            Expr ub; addTerm(ub, uName(k, i), 1); addTerm(ub, zName(k, i), -V);
            writeConstraint(out, cid, ub, "<=", 0);
        }
        for (int i = 1; i <= V; ++i) {
            for (int j = 1; j <= V; ++j) {
                if (i == j) continue;
                Expr e;
                addTerm(e, uName(k, i), 1);
                addTerm(e, uName(k, j), -1);
                addTerm(e, xName(k, i, j), V);
                writeConstraint(out, cid, e, "<=", V - 1);
            }
        }
    }

    for (int k = 0; k < M; ++k) {
        const int Q = instance.Q[k];
        for (int i = 1; i <= V; ++i) {
            const int pmax = std::min(instance.initial[i], Q);
            const int dmax = std::min(instance.capacity[i] - instance.initial[i], Q);
            Expr ep; addTerm(ep, pName(k, i), 1); addTerm(ep, zName(k, i), -pmax);
            writeConstraint(out, cid, ep, "<=", 0);
            Expr ed; addTerm(ed, dName(k, i), 1); addTerm(ed, zName(k, i), -dmax);
            writeConstraint(out, cid, ed, "<=", 0);
            Expr mm; addTerm(mm, mName(k, i), 1); addTerm(mm, zName(k, i), -1);
            writeConstraint(out, cid, mm, "<=", 0);
            Expr pm; addTerm(pm, pName(k, i), 1); addTerm(pm, mName(k, i), -pmax);
            writeConstraint(out, cid, pm, "<=", 0);
            Expr dm; addTerm(dm, dName(k, i), 1); addTerm(dm, zName(k, i), -dmax); addTerm(dm, mName(k, i), dmax);
            writeConstraint(out, cid, dm, "<=", 0);
            Expr nonzero; addTerm(nonzero, pName(k, i), 1); addTerm(nonzero, dName(k, i), 1); addTerm(nonzero, zName(k, i), -1);
            writeConstraint(out, cid, nonzero, ">=", 0);
            Expr loadz; addTerm(loadz, lName(k, i), 1); addTerm(loadz, zName(k, i), -Q);
            writeConstraint(out, cid, loadz, "<=", 0);
        }

        for (int i = 1; i <= V; ++i) {
            Expr up;
            addTerm(up, lName(k, i), 1);
            addTerm(up, pName(k, i), -1);
            addTerm(up, dName(k, i), 1);
            addTerm(up, xName(k, 0, i), Q);
            writeConstraint(out, cid, up, "<=", Q);
            Expr lo;
            addTerm(lo, lName(k, i), 1);
            addTerm(lo, pName(k, i), -1);
            addTerm(lo, dName(k, i), 1);
            addTerm(lo, xName(k, 0, i), -Q);
            writeConstraint(out, cid, lo, ">=", -Q);
        }
        for (int i = 1; i <= V; ++i) {
            for (int j = 1; j <= V; ++j) {
                if (i == j) continue;
                Expr up;
                addTerm(up, lName(k, j), 1);
                addTerm(up, lName(k, i), -1);
                addTerm(up, pName(k, j), -1);
                addTerm(up, dName(k, j), 1);
                addTerm(up, xName(k, i, j), Q);
                writeConstraint(out, cid, up, "<=", Q);
                Expr lo;
                addTerm(lo, lName(k, j), 1);
                addTerm(lo, lName(k, i), -1);
                addTerm(lo, pName(k, j), -1);
                addTerm(lo, dName(k, j), 1);
                addTerm(lo, xName(k, i, j), -Q);
                writeConstraint(out, cid, lo, ">=", -Q);
            }
        }
        Expr final_load;
        for (int i = 1; i <= V; ++i) {
            addTerm(final_load, pName(k, i), 1);
            addTerm(final_load, dName(k, i), -1);
        }
        writeConstraint(out, cid, final_load, ">=", 0);

        Expr duration;
        for (int i = 0; i <= V; ++i) {
            for (int j = 0; j <= V; ++j) {
                if (i != j) addTerm(duration, xName(k, i, j), instance.dist[i][j]);
            }
        }
        for (int i = 1; i <= V; ++i) addTerm(duration, pName(k, i), cunit);
        writeConstraint(out, cid, duration, "<=", instance.total_time_limit);
    }

    if (strengthened && V <= 12) {
        const std::vector<double> tsp = subsetTspLowerBounds(instance);
        const double big = 100000.0;
        for (int k = 0; k < M; ++k) {
            for (int mask = 1; mask < (1 << V); ++mask) {
                Expr e;
                int count = 0;
                for (int b = 0; b < V; ++b) {
                    if (mask & (1 << b)) {
                        const int i = b + 1;
                        ++count;
                        addTerm(e, pName(k, i), cunit);
                        addTerm(e, zName(k, i), big);
                    }
                }
                writeConstraint(out, cid, e, "<=", instance.total_time_limit - tsp[mask] + big * count);
            }
        }
    }

    if (strengthened && options.compact_bc_support_duration_cuts &&
        options.compact_bc_support_cut_max_size >= 2) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("pair_triple_route_duration_support");
        }
        long long subset_rows_considered = 0;
        auto addSupportCut = [&](int k, const std::vector<int>& subset, double cycle_lb) {
            if (options.compact_bc_support_cut_max_subsets > 0 &&
                subset_rows_considered >= options.compact_bc_support_cut_max_subsets) {
                return;
            }
            ++subset_rows_considered;
            const int s = static_cast<int>(subset.size());
            const double min_handling = cunit * static_cast<double>((s + 1) / 2);
            if (cycle_lb + min_handling > instance.total_time_limit + 1e-9) {
                Expr cut;
                for (int i : subset) addTerm(cut, zName(k, i), 1);
                writeConstraint(out, cid, cut, "<=", s - 1);
                if (stats != nullptr) {
                    if (s == 2) ++stats->support_duration_pair_cuts_added;
                    if (s == 3) ++stats->support_duration_triple_cuts_added;
                }
                return;
            }
            int pmax_sum = 0;
            for (int i : subset) {
                pmax_sum += std::min(instance.initial[i], instance.Q[k]);
            }
            const double big = instance.total_time_limit + cycle_lb +
                cunit * static_cast<double>(std::max(1, pmax_sum));
            Expr conditional;
            for (int i : subset) {
                addTerm(conditional, pName(k, i), cunit);
                addTerm(conditional, zName(k, i), big);
            }
            writeConstraint(out, cid, conditional, "<=",
                            instance.total_time_limit - cycle_lb +
                            big * static_cast<double>(s));
            if (stats != nullptr) {
                if (s == 2) ++stats->support_duration_pair_cuts_added;
                if (s == 3) ++stats->support_duration_triple_cuts_added;
            }
        };
        for (int k = 0; k < M; ++k) {
            for (int a = 1; a <= V; ++a) {
                for (int b = a + 1; b <= V; ++b) {
                    addSupportCut(k, {a, b}, pairCycleLowerBound(instance, a, b));
                }
            }
            if (options.compact_bc_support_cut_max_size >= 3) {
                for (int a = 1; a <= V; ++a) {
                    for (int b = a + 1; b <= V; ++b) {
                        for (int c = b + 1; c <= V; ++c) {
                            addSupportCut(k, {a, b, c},
                                          tripleCycleLowerBound(instance, a, b, c));
                        }
                    }
                }
            }
        }
    }

    if (strengthened && tailored_active && options.tailored_bc_vector_support_cover &&
        (options.tailored_bc_vector_cut_candidate_source == "root" ||
         options.tailored_bc_vector_cut_candidate_source == "both")) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("vector_support_cover");
        }
        const int max_size = std::min({6, V, std::max(2, options.tailored_bc_vector_support_cover_max_size)});
        constexpr long long max_candidates = 50000;
        long long candidates = 0;
        bool stop = false;
        for (int k = 0; k < M && !stop; ++k) {
            for (int s = 2; s <= max_size && !stop; ++s) {
                enumerateStationSubsets(V, s, [&](const std::vector<int>& subset) {
                    if (stop) return;
                    if (++candidates > max_candidates) {
                        stop = true;
                        return;
                    }
                    if (stats != nullptr) ++stats->vector_support_cover_candidates;
                    const double cycle_lb = subsetCycleLowerBound(instance, subset);
                    const double min_handling =
                        cunit * static_cast<double>((static_cast<int>(subset.size()) + 1) / 2);
                    const double violation =
                        cycle_lb + min_handling - instance.total_time_limit;
                    if (violation <= 1e-9) return;
                    Expr cut;
                    for (int station : subset) addTerm(cut, zName(k, station), 1.0);
                    writeConstraint(out, cid, cut, "<=",
                                    static_cast<double>(subset.size() - 1));
                    if (stats != nullptr) {
                        ++stats->vector_support_cover_cuts_added;
                        stats->vector_support_cover_max_violation =
                            std::max(stats->vector_support_cover_max_violation, violation);
                        if (options.tailored_bc_vector_support_cover_max_cuts > 0 &&
                            stats->vector_support_cover_cuts_added >=
                                options.tailored_bc_vector_support_cover_max_cuts) {
                            stop = true;
                        }
                    }
                });
            }
        }
    }

    if (strengthened && tailored_active && options.tailored_bc_vector_route_cutset &&
        (options.tailored_bc_vector_cut_candidate_source == "root" ||
         options.tailored_bc_vector_cut_candidate_source == "both")) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("vector_route_cutset");
        }
        const int max_size = std::min({8, V, std::max(2, options.tailored_bc_vector_route_cutset_max_size)});
        constexpr long long max_candidates = 50000;
        long long candidates = 0;
        bool stop = false;
        for (int k = 0; k < M && !stop; ++k) {
            for (int s = 2; s <= max_size && !stop; ++s) {
                enumerateStationSubsets(V, s, [&](const std::vector<int>& subset) {
                    if (stop) return;
                    if (++candidates > max_candidates) {
                        stop = true;
                        return;
                    }
                    if (stats != nullptr) ++stats->vector_route_cutset_candidates;
                    std::set<int> in_subset(subset.begin(), subset.end());
                    for (int representative : subset) {
                        Expr cut;
                        for (int i = 0; i <= V; ++i) {
                            const bool i_in = in_subset.count(i) > 0;
                            for (int j = 0; j <= V; ++j) {
                                if (i == j) continue;
                                const bool j_in = in_subset.count(j) > 0;
                                if (!i_in && j_in) addTerm(cut, xName(k, i, j), 1.0);
                                if (i_in && !j_in) addTerm(cut, xName(k, i, j), 1.0);
                            }
                        }
                        addTerm(cut, zName(k, representative), -2.0);
                        writeConstraint(out, cid, cut, ">=", 0.0);
                        if (stats != nullptr) {
                            ++stats->vector_route_cutset_cuts_added;
                            if (options.tailored_bc_vector_route_cutset_max_cuts > 0 &&
                                stats->vector_route_cutset_cuts_added >=
                                    options.tailored_bc_vector_route_cutset_max_cuts) {
                                stop = true;
                                break;
                            }
                        }
                    }
                });
            }
        }
    }

    const bool identical_q = std::all_of(instance.Q.begin(), instance.Q.end(),
        [&](int q) { return q == instance.Q.front(); });
    if (strengthened && options.interval_oracle_symmetry_breaking && identical_q && M > 1) {
        for (int k = 0; k + 1 < M; ++k) {
            Expr e;
            for (int i = 1; i <= V; ++i) {
                addTerm(e, zName(k, i), 1);
                addTerm(e, zName(k + 1, i), -1);
            }
            writeConstraint(out, cid, e, ">=", 0);
        }
    }

    for (int i = 1; i <= V; ++i) {
        Expr inv;
        addTerm(inv, yName(i), 1);
        for (int k = 0; k < M; ++k) {
            addTerm(inv, pName(k, i), 1);
            addTerm(inv, dName(k, i), -1);
        }
        writeConstraint(out, cid, inv, "=", instance.initial[i]);
        Expr ratio; addTerm(ratio, rName(i), 1); addTerm(ratio, yName(i), -1.0 / instance.target[i]);
        writeConstraint(out, cid, ratio, "=", 0);
        Expr ep; addTerm(ep, eName(i), 1); addTerm(ep, rName(i), -1);
        writeConstraint(out, cid, ep, ">=", -1);
        Expr em; addTerm(em, eName(i), 1); addTerm(em, rName(i), 1);
        writeConstraint(out, cid, em, ">=", 1);
    }
    if (strengthened && options.compact_bc_visit_inventory_linking) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("visit_final_inventory_linking");
        }
        for (int i = 1; i <= V; ++i) {
            Expr visit;
            for (int k = 0; k < M; ++k) addTerm(visit, zName(k, i), 1);
            Expr upper;
            addTerm(upper, yName(i), 1);
            for (const auto& kv : visit) addTerm(upper, kv.first,
                -static_cast<double>(instance.capacity[i] - instance.initial[i]) * kv.second);
            writeConstraint(out, cid, upper, "<=", instance.initial[i]);
            Expr lower;
            addTerm(lower, yName(i), -1);
            for (const auto& kv : visit) addTerm(lower, kv.first,
                -static_cast<double>(instance.initial[i]) * kv.second);
            writeConstraint(out, cid, lower, "<=", -instance.initial[i]);
            if (stats != nullptr) stats->visit_inventory_linking_rows_added += 2;
        }
    }

    double required_pick_min = 0.0;
    double required_drop_min = 0.0;
    if (strengthened && options.required_movement_cuts &&
        !use_shared_interval_rows) {
        if (stats != nullptr) stats->enabled_families.push_back("required_station_movement");
        for (int i = 1; i <= V; ++i) {
            if (y_lb[i] > instance.initial[i]) {
                const int need_drop = y_lb[i] - instance.initial[i];
                required_drop_min += need_drop;
                Expr e;
                for (int k = 0; k < M; ++k) {
                    addTerm(e, dName(k, i), 1);
                    addTerm(e, pName(k, i), -1);
                }
                writeConstraint(out, cid, e, ">=", need_drop);
                if (stats != nullptr) ++stats->required_movement_cuts_added;
            }
            if (y_ub[i] < instance.initial[i]) {
                const int need_pick = instance.initial[i] - y_ub[i];
                required_pick_min += need_pick;
                Expr e;
                for (int k = 0; k < M; ++k) {
                    addTerm(e, pName(k, i), 1);
                    addTerm(e, dName(k, i), -1);
                }
                writeConstraint(out, cid, e, ">=", need_pick);
                if (stats != nullptr) ++stats->required_movement_cuts_added;
            }
        }
    }
    if (stats != nullptr) {
        stats->required_movement_lb = required_pick_min + required_drop_min;
        stats->global_handling_capacity_lb = cunit * required_pick_min;
    }
    if (strengthened && options.global_handling_capacity_cuts) {
        if (stats != nullptr) stats->enabled_families.push_back("global_handling_capacity_pickup_only");
        Expr handling;
        for (int k = 0; k < M; ++k) {
            for (int i = 1; i <= V; ++i) {
                addTerm(handling, pName(k, i), cunit);
            }
        }
        const double total_duration_capacity =
            static_cast<double>(M) * instance.total_time_limit;
        writeConstraint(out, cid, handling, "<=", total_duration_capacity);
        if (stats != nullptr) ++stats->global_handling_capacity_cuts_added;
        if (stats != nullptr && stats->global_handling_capacity_lb > total_duration_capacity + 1e-9) {
            Expr impossible;
            writeConstraint(out, cid, impossible, "<=", -1);
            ++stats->global_handling_capacity_cuts_added;
        }
    }
    for (int i = 1; i <= V; ++i) {
        for (int j = i + 1; j <= V; ++j) {
            Expr h1; addTerm(h1, hName(i, j), 1); addTerm(h1, rName(i), -1); addTerm(h1, rName(j), 1);
            writeConstraint(out, cid, h1, ">=", 0);
            Expr h2; addTerm(h2, hName(i, j), 1); addTerm(h2, rName(i), 1); addTerm(h2, rName(j), -1);
            writeConstraint(out, cid, h2, ">=", 0);
        }
    }
    if (!use_shared_interval_rows && strengthened && cutoff != nullptr && cutoff->enabled &&
        options.compact_bc_direct_gini_rows) {
        if (stats != nullptr) stats->enabled_families.push_back("direct_gini_cap_floor");
        Expr cap;
        for (int i = 1; i <= V; ++i) {
            addTerm(cap, rName(i), -static_cast<double>(V) * cutoff->gamma_U);
            for (int j = i + 1; j <= V; ++j) addTerm(cap, hName(i, j), 1);
        }
        writeConstraint(out, cid, cap, "<=", 0);
        if (stats != nullptr) ++stats->direct_gini_cap_rows_added;
        Expr floor;
        for (int i = 1; i <= V; ++i) {
            addTerm(floor, rName(i), -static_cast<double>(V) * cutoff->gamma_L);
            for (int j = i + 1; j <= V; ++j) addTerm(floor, hName(i, j), 1);
        }
        writeConstraint(out, cid, floor, ">=", 0);
        if (stats != nullptr) ++stats->direct_gini_floor_rows_added;
    }
    if (add_bucket_ratio_domain) {
        const double upper_factor = 1.0 / static_cast<double>(V) + cutoff->gamma_U;
        const double lower_factor = 1.0 / static_cast<double>(V) - cutoff->gamma_U;
        for (int i = 1; i <= V; ++i) {
            Expr ub;
            addTerm(ub, rName(i), 1.0);
            writeConstraint(out, cid, ub, "<=", std::max(0.0, upper_factor * s_bucket_U));
            if (stats != nullptr) ++stats->tailored_bucket_ratio_domain_rows_added;
            if (lower_factor > 1e-12) {
                Expr lb;
                addTerm(lb, rName(i), 1.0);
                writeConstraint(out, cid, lb, ">=", std::max(0.0, lower_factor * s_bucket_L));
                if (stats != nullptr) ++stats->tailored_bucket_ratio_domain_rows_added;
            }
        }
        Expr h_cap;
        for (int i = 1; i <= V; ++i) {
            for (int j = i + 1; j <= V; ++j) {
                addTerm(h_cap, hName(i, j), 1.0);
            }
        }
        writeConstraint(out, cid, h_cap, "<=",
                        static_cast<double>(V) * cutoff->gamma_U * s_bucket_U);
        if (stats != nullptr) ++stats->tailored_bucket_h_cap_rows_added;
    }
    if (add_bucket_integer_inventory_domain) {
        for (int i = 1; i <= V; ++i) {
            if (y_lb[i] > 0) {
                Expr lb;
                addTerm(lb, yName(i), 1.0);
                writeConstraint(out, cid, lb, ">=", y_lb[i]);
                if (stats != nullptr) ++stats->bucket_integer_inventory_rows_added;
            }
            if (y_ub[i] < instance.capacity[i]) {
                Expr ub;
                addTerm(ub, yName(i), 1.0);
                writeConstraint(out, cid, ub, "<=", y_ub[i]);
                if (stats != nullptr) ++stats->bucket_integer_inventory_rows_added;
            }
        }
    }
    const bool add_bucket_required_movement =
        strengthened && tailored_active && cutoff != nullptr && cutoff->enabled &&
        s_range_rows_active && options.tailored_bc_bucket_required_movement &&
        options.tailored_bc_bucket_integer_inventory_domain;
    const bool add_bucket_required_visit =
        strengthened && tailored_active && cutoff != nullptr && cutoff->enabled &&
        s_range_rows_active && options.tailored_bc_bucket_required_visit &&
        options.tailored_bc_bucket_integer_inventory_domain;
    if (add_bucket_required_movement || add_bucket_required_visit) {
        if (stats != nullptr && add_bucket_required_movement) {
            stats->enabled_families.push_back("bucket_required_movement");
        }
        if (stats != nullptr && add_bucket_required_visit) {
            stats->enabled_families.push_back("bucket_required_visit");
        }
        for (int i = 1; i <= V; ++i) {
            const int required_delivery = std::max(0, y_lb[i] - instance.initial[i]);
            const int required_loss = std::max(0, instance.initial[i] - y_ub[i]);
            if (add_bucket_required_movement && required_delivery > 0) {
                Expr deliver;
                for (int k = 0; k < M; ++k) {
                    addTerm(deliver, dName(k, i), 1.0);
                    addTerm(deliver, pName(k, i), -1.0);
                }
                writeConstraint(out, cid, deliver, ">=", required_delivery);
                if (stats != nullptr) {
                    ++stats->bucket_required_movement_rows_added;
                    ++stats->bucket_required_movement_violations;
                    stats->bucket_required_movement_max_violation =
                        std::max(stats->bucket_required_movement_max_violation,
                                 static_cast<double>(required_delivery));
                }
            }
            if (add_bucket_required_movement && required_loss > 0) {
                Expr loss;
                for (int k = 0; k < M; ++k) {
                    addTerm(loss, pName(k, i), 1.0);
                    addTerm(loss, dName(k, i), -1.0);
                }
                writeConstraint(out, cid, loss, ">=", required_loss);
                if (stats != nullptr) {
                    ++stats->bucket_required_movement_rows_added;
                    ++stats->bucket_required_movement_violations;
                    stats->bucket_required_movement_max_violation =
                        std::max(stats->bucket_required_movement_max_violation,
                                 static_cast<double>(required_loss));
                }
            }
            if (add_bucket_required_visit &&
                (required_delivery > 0 || required_loss > 0)) {
                Expr visit;
                for (int k = 0; k < M; ++k) addTerm(visit, zName(k, i), 1.0);
                writeConstraint(out, cid, visit, ">=", 1.0);
                if (stats != nullptr) ++stats->bucket_required_visit_rows_added;
            }
        }
        if (add_bucket_required_movement) {
            const int max_size = std::min({3, V, std::max(1, options.tailored_bc_bucket_required_movement_max_size)});
            std::vector<int> subset;
            std::function<void(int, int)> gen_req = [&](int start, int remaining) {
                if (remaining == 0) {
                    if (subset.size() <= 1) return;
                    int lower_inventory = 0;
                    int upper_inventory = 0;
                    int initial_inventory = 0;
                    for (int i : subset) {
                        lower_inventory += y_lb[i];
                        upper_inventory += y_ub[i];
                        initial_inventory += instance.initial[i];
                    }
                    const int required_delivery =
                        std::max(0, lower_inventory - initial_inventory);
                    const int required_loss =
                        std::max(0, initial_inventory - upper_inventory);
                    if (required_delivery > 0) {
                        Expr deliver;
                        for (int k = 0; k < M; ++k) {
                            for (int i : subset) {
                                addTerm(deliver, dName(k, i), 1.0);
                                addTerm(deliver, pName(k, i), -1.0);
                            }
                        }
                        writeConstraint(out, cid, deliver, ">=", required_delivery);
                        if (stats != nullptr) ++stats->bucket_subset_required_movement_rows_added;
                    }
                    if (required_loss > 0) {
                        Expr loss;
                        for (int k = 0; k < M; ++k) {
                            for (int i : subset) {
                                addTerm(loss, pName(k, i), 1.0);
                                addTerm(loss, dName(k, i), -1.0);
                            }
                        }
                        writeConstraint(out, cid, loss, ">=", required_loss);
                        if (stats != nullptr) ++stats->bucket_subset_required_movement_rows_added;
                    }
                    return;
                }
                for (int i = start; i <= V - remaining + 1; ++i) {
                    subset.push_back(i);
                    gen_req(i + 1, remaining - 1);
                    subset.pop_back();
                }
            };
            for (int size = 2; size <= max_size; ++size) gen_req(1, size);
        }
    }
    if (add_bucket_subset_ratio_domain) {
        if (stats != nullptr) stats->enabled_families.push_back("bucket_subset_ratio_domain");
        const int max_size = std::min({4, V, std::max(1, options.tailored_bc_bucket_subset_ratio_max_size)});
        std::vector<int> subset;
        std::function<void(int, int)> gen = [&](int start, int remaining) {
            if (remaining == 0) {
                const int a = static_cast<int>(subset.size());
                if (stats != nullptr) ++stats->tailored_bucket_subset_ratio_domain_candidates;
                const double upper = (static_cast<double>(a) / static_cast<double>(V) +
                                      cutoff->gamma_U) * s_bucket_U;
                Expr ub;
                for (int i : subset) addTerm(ub, rName(i), 1.0);
                writeConstraint(out, cid, ub, "<=", std::max(0.0, upper));
                if (stats != nullptr) ++stats->tailored_bucket_subset_ratio_domain_cuts_added;
                const double lower_factor =
                    static_cast<double>(a) / static_cast<double>(V) - cutoff->gamma_U;
                if (lower_factor > 1e-12) {
                    Expr lb;
                    for (int i : subset) addTerm(lb, rName(i), 1.0);
                    writeConstraint(out, cid, lb, ">=", std::max(0.0, lower_factor * s_bucket_L));
                    if (stats != nullptr) ++stats->tailored_bucket_subset_ratio_domain_cuts_added;
                }
                return;
            }
            for (int i = start; i <= V - remaining + 1; ++i) {
                subset.push_back(i);
                gen(i + 1, remaining - 1);
                subset.pop_back();
            }
        };
        for (int size = 1; size <= max_size; ++size) {
            gen(1, size);
        }
    }
    if (tailored_active && cutoff != nullptr && cutoff->enabled &&
        options.tailored_bc_gini_subset_envelope && cutoff->gamma_U >= -1e-12) {
        if (stats != nullptr) stats->enabled_families.push_back("gini_subset_envelope");
        const int max_size = std::min({3, V - 1, std::max(1, options.tailored_bc_gini_subset_max_size)});
        const long long max_cuts = std::max(0, options.tailored_bc_gini_subset_max_cuts);
        long long cuts = 0;
        auto addSubsetEnvelope = [&](const std::vector<int>& subset) {
            if (max_cuts > 0 && cuts + 2 > max_cuts) return;
            const int a = static_cast<int>(subset.size());
            Expr plus;
            Expr minus;
            for (int i = 1; i <= V; ++i) {
                addTerm(plus, rName(i), -static_cast<double>(a) -
                        static_cast<double>(V) * cutoff->gamma_U);
                addTerm(minus, rName(i), static_cast<double>(a) -
                        static_cast<double>(V) * cutoff->gamma_U);
            }
            for (int i : subset) {
                addTerm(plus, rName(i), static_cast<double>(V));
                addTerm(minus, rName(i), -static_cast<double>(V));
            }
            writeConstraint(out, cid, plus, "<=", 0.0);
            writeConstraint(out, cid, minus, "<=", 0.0);
            cuts += 2;
            if (stats != nullptr) {
                ++stats->tailored_gini_subset_envelope_candidates;
                stats->tailored_gini_subset_envelope_cuts_added += 2;
            }
        };
        if (max_size >= 1) {
            for (int a = 1; a <= V; ++a) addSubsetEnvelope({a});
        }
        if (max_size >= 2) {
            for (int a = 1; a <= V; ++a) {
                for (int b = a + 1; b <= V; ++b) addSubsetEnvelope({a, b});
            }
        }
        if (max_size >= 3) {
            for (int a = 1; a <= V; ++a) {
                for (int b = a + 1; b <= V; ++b) {
                    for (int c = b + 1; c <= V; ++c) addSubsetEnvelope({a, b, c});
                }
            }
        }
    }
    if (tailored_active && cutoff != nullptr && cutoff->enabled &&
        options.tailored_bc_low_gini_l1_centering && cutoff->gamma_U >= -1e-12) {
        if (stats != nullptr) stats->enabled_families.push_back("low_gini_l1_centering");
        Expr sum_q;
        for (int i = 1; i <= V; ++i) {
            const std::string q = "q_l1_" + std::to_string(i);
            addTerm(sum_q, q, 1.0);
            Expr pos;
            addTerm(pos, q, static_cast<double>(V));
            addTerm(pos, rName(i), -static_cast<double>(V));
            for (int j = 1; j <= V; ++j) addTerm(pos, rName(j), 1.0);
            writeConstraint(out, cid, pos, ">=", 0.0);
            Expr neg;
            addTerm(neg, q, static_cast<double>(V));
            addTerm(neg, rName(i), static_cast<double>(V));
            for (int j = 1; j <= V; ++j) addTerm(neg, rName(j), -1.0);
            writeConstraint(out, cid, neg, ">=", 0.0);
            if (stats != nullptr) stats->tailored_low_gini_l1_rows_added += 2;
        }
        for (int i = 1; i <= V; ++i) {
            addTerm(sum_q, rName(i), -2.0 * cutoff->gamma_U);
        }
        writeConstraint(out, cid, sum_q, "<=", 0.0);
        if (stats != nullptr) ++stats->tailored_low_gini_l1_rows_added;
    }
    if (tailored_active && cutoff != nullptr && cutoff->enabled &&
        options.tailored_bc_local_centering && cutoff->gamma_U >= -1e-12) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("local_centering_pairwise_h");
        }
        for (int i = 1; i <= V; ++i) {
            Expr pos;
            addTerm(pos, rName(i), static_cast<double>(V));
            for (int j = 1; j <= V; ++j) addTerm(pos, rName(j), -1.0);
            for (int j = 1; j <= V; ++j) {
                if (j == i) continue;
                addTerm(pos, i < j ? hName(i, j) : hName(j, i), -1.0);
            }
            writeConstraint(out, cid, pos, "<=", 0.0);

            Expr neg;
            for (int j = 1; j <= V; ++j) addTerm(neg, rName(j), 1.0);
            addTerm(neg, rName(i), -static_cast<double>(V));
            for (int j = 1; j <= V; ++j) {
                if (j == i) continue;
                addTerm(neg, i < j ? hName(i, j) : hName(j, i), -1.0);
            }
            writeConstraint(out, cid, neg, "<=", 0.0);
            if (stats != nullptr) stats->tailored_local_centering_rows_added += 2;
        }
    }
    if (tailored_active && cutoff != nullptr && cutoff->enabled &&
        options.tailored_bc_subset_cross_h_centering && cutoff->gamma_U >= -1e-12) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("subset_cross_h_centering");
        }
        const int max_size =
            std::min({4, V, std::max(1, options.tailored_bc_subset_cross_h_max_size)});
        const long long max_rows =
            options.tailored_bc_subset_cross_h_max_cuts > 0
                ? static_cast<long long>(options.tailored_bc_subset_cross_h_max_cuts)
                : std::numeric_limits<long long>::max();
        long long rows_added = 0;
        auto addSubsetCrossH = [&](const std::vector<int>& subset) {
            if (rows_added + 2 > max_rows) return;
            std::set<int> in_subset(subset.begin(), subset.end());
            if (stats != nullptr) ++stats->tailored_subset_cross_h_centering_candidates;

            Expr pos;
            for (int i : subset) addTerm(pos, rName(i), static_cast<double>(V));
            for (int j = 1; j <= V; ++j) {
                addTerm(pos, rName(j), -static_cast<double>(subset.size()));
            }
            for (int i : subset) {
                for (int j = 1; j <= V; ++j) {
                    if (in_subset.count(j)) continue;
                    addTerm(pos, i < j ? hName(i, j) : hName(j, i), -1.0);
                }
            }
            writeConstraint(out, cid, pos, "<=", 0.0);

            Expr neg;
            for (int j = 1; j <= V; ++j) {
                addTerm(neg, rName(j), static_cast<double>(subset.size()));
            }
            for (int i : subset) addTerm(neg, rName(i), -static_cast<double>(V));
            for (int i : subset) {
                for (int j = 1; j <= V; ++j) {
                    if (in_subset.count(j)) continue;
                    addTerm(neg, i < j ? hName(i, j) : hName(j, i), -1.0);
                }
            }
            writeConstraint(out, cid, neg, "<=", 0.0);
            rows_added += 2;
            if (stats != nullptr) stats->tailored_subset_cross_h_centering_rows_added += 2;
        };
        for (int a = 1; a <= V && rows_added + 2 <= max_rows; ++a) {
            addSubsetCrossH({a});
        }
        if (max_size >= 2) {
            for (int a = 1; a <= V && rows_added + 2 <= max_rows; ++a) {
                for (int b = a + 1; b <= V && rows_added + 2 <= max_rows; ++b) {
                    addSubsetCrossH({a, b});
                }
            }
        }
        if (max_size >= 3) {
            for (int a = 1; a <= V && rows_added + 2 <= max_rows; ++a) {
                for (int b = a + 1; b <= V && rows_added + 2 <= max_rows; ++b) {
                    for (int c = b + 1; c <= V && rows_added + 2 <= max_rows; ++c) {
                        addSubsetCrossH({a, b, c});
                    }
                }
            }
        }
        if (max_size >= 4) {
            for (int a = 1; a <= V && rows_added + 2 <= max_rows; ++a) {
                for (int b = a + 1; b <= V && rows_added + 2 <= max_rows; ++b) {
                    for (int c = b + 1; c <= V && rows_added + 2 <= max_rows; ++c) {
                        for (int d = c + 1; d <= V && rows_added + 2 <= max_rows; ++d) {
                            addSubsetCrossH({a, b, c, d});
                        }
                    }
                }
            }
        }
    }
    if (tailored_active && cutoff != nullptr && cutoff->enabled &&
        options.tailored_bc_local_q_centering &&
        options.tailored_bc_low_gini_l1_centering && cutoff->gamma_U >= -1e-12) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("local_q_centering");
        }
        for (int i = 1; i <= V; ++i) {
            Expr row;
            addTerm(row, "q_l1_" + std::to_string(i), static_cast<double>(V));
            for (int j = 1; j <= V; ++j) {
                if (j == i) continue;
                addTerm(row, i < j ? hName(i, j) : hName(j, i), -1.0);
            }
            writeConstraint(out, cid, row, "<=", 0.0);
            if (stats != nullptr) ++stats->tailored_local_q_centering_rows_added;
        }
    }
    if (tailored_active && options.tailored_bc_subset_inventory_imbalance) {
        if (stats != nullptr) stats->enabled_families.push_back("subset_inventory_imbalance");
        const int max_size = std::min({3, V, std::max(1, options.tailored_bc_subset_inventory_max_size)});
        auto addSubsetInventory = [&](const std::vector<int>& subset) {
            int initial_sum = 0;
            int room_sum = 0;
            int bikes_sum = 0;
            Expr ysum;
            for (int i : subset) {
                initial_sum += instance.initial[i];
                room_sum += instance.capacity[i] - instance.initial[i];
                bikes_sum += instance.initial[i];
                addTerm(ysum, yName(i), 1.0);
            }
            double plus = 0.0;
            double minus = 0.0;
            for (int k = 0; k < M; ++k) {
                const int move_budget = cunit > 1e-12
                    ? static_cast<int>(std::floor(instance.total_time_limit / cunit + 1e-9))
                    : instance.Q[k];
                plus += std::min({instance.Q[k], room_sum, move_budget});
                minus += std::min({instance.Q[k], bikes_sum, move_budget});
            }
            writeConstraint(out, cid, ysum, "<=", initial_sum + plus);
            Expr ysum_lb = ysum;
            writeConstraint(out, cid, ysum_lb, ">=", initial_sum - minus);
            if (stats != nullptr) stats->tailored_subset_inventory_imbalance_cuts_added += 2;
        };
        if (max_size >= 1) {
            for (int a = 1; a <= V; ++a) addSubsetInventory({a});
        }
        if (max_size >= 2) {
            for (int a = 1; a <= V; ++a) {
                for (int b = a + 1; b <= V; ++b) addSubsetInventory({a, b});
            }
        }
        if (max_size >= 3) {
            for (int a = 1; a <= V; ++a) {
                for (int b = a + 1; b <= V; ++b) {
                    for (int c = b + 1; c <= V; ++c) addSubsetInventory({a, b, c});
                }
            }
        }
    }
    if (tailored_active && options.tailored_bc_transfer_cutset) {
        if (stats != nullptr) stats->enabled_families.push_back("vehicle_transfer_cutset_basic");
        auto addTransferCutset = [&](const std::vector<int>& subset) {
            std::set<int> in_subset(subset.begin(), subset.end());
            for (int k = 0; k < M; ++k) {
                Expr cut;
                for (int j : subset) {
                    addTerm(cut, dName(k, j), 1.0);
                    addTerm(cut, pName(k, j), -1.0);
                }
                for (int i = 1; i <= V; ++i) {
                    if (!in_subset.count(i)) addTerm(cut, pName(k, i), -1.0);
                }
                writeConstraint(out, cid, cut, "<=", 0.0);
                if (stats != nullptr) ++stats->tailored_transfer_cutset_cuts_added;
            }
        };
        for (int a = 1; a <= V; ++a) addTransferCutset({a});
        for (int a = 1; a <= V; ++a) {
            for (int b = a + 1; b <= V; ++b) addTransferCutset({a, b});
        }
    }
    auto generateReceiverSubsets = [&](int max_size, const auto& add_subset) {
        const int capped = std::min({3, V, std::max(1, max_size)});
        for (int a = 1; a <= V; ++a) add_subset(std::vector<int>{a});
        if (capped >= 2) {
            for (int a = 1; a <= V; ++a) {
                for (int b = a + 1; b <= V; ++b) add_subset(std::vector<int>{a, b});
            }
        }
        if (capped >= 3) {
            for (int a = 1; a <= V; ++a) {
                for (int b = a + 1; b <= V; ++b) {
                    for (int c = b + 1; c <= V; ++c) {
                        add_subset(std::vector<int>{a, b, c});
                    }
                }
            }
        }
    };
    if (tailored_active && options.tailored_bc_compatible_source_transfer_cuts) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("compatible_source_transfer_cutset");
        }
        auto sourceCompatible = [&](int k, int source, const std::vector<int>& receivers) {
            (void)k;
            for (int j : receivers) {
                const double travel_lb =
                    instance.dist[0][source] + instance.dist[source][j] + instance.dist[j][0];
                if (travel_lb <= instance.total_time_limit + 1e-9) {
                    return true;
                }
            }
            return false;
        };
        auto addCompatibleSourceTransfer = [&](const std::vector<int>& subset) {
            std::set<int> in_subset(subset.begin(), subset.end());
            for (int k = 0; k < M; ++k) {
                Expr cut;
                for (int j : subset) {
                    addTerm(cut, dName(k, j), 1.0);
                    addTerm(cut, pName(k, j), -1.0);
                }
                int compatible_outside = 0;
                int all_outside = 0;
                for (int i = 1; i <= V; ++i) {
                    if (in_subset.count(i)) continue;
                    ++all_outside;
                    if (sourceCompatible(k, i, subset)) {
                        addTerm(cut, pName(k, i), -1.0);
                        ++compatible_outside;
                    }
                }
                if (stats != nullptr) ++stats->tailored_compatible_source_transfer_candidates;
                if (compatible_outside >= all_outside) {
                    return;
                }
                writeConstraint(out, cid, cut, "<=", 0.0);
                if (stats != nullptr) ++stats->tailored_compatible_source_transfer_cuts_added;
            }
        };
        generateReceiverSubsets(options.tailored_bc_transfer_max_receiver_size,
                                addCompatibleSourceTransfer);
    }
    if (tailored_active && options.tailored_bc_required_external_source_cuts) {
        if (stats != nullptr) {
            stats->enabled_families.push_back("required_external_source");
        }
        auto addRequiredExternalSource = [&](const std::vector<int>& subset) {
            std::set<int> in_subset(subset.begin(), subset.end());
            int lower_inventory = 0;
            int initial_inventory = 0;
            for (int j : subset) {
                lower_inventory += y_lb[j];
                initial_inventory += instance.initial[j];
            }
            const int required_delivery =
                std::max(0, lower_inventory - initial_inventory);
            if (required_delivery <= 0) return;
            Expr cut;
            for (int k = 0; k < M; ++k) {
                for (int i = 1; i <= V; ++i) {
                    if (!in_subset.count(i)) addTerm(cut, pName(k, i), 1.0);
                }
            }
            writeConstraint(out, cid, cut, ">=", static_cast<double>(required_delivery));
            if (stats != nullptr) ++stats->tailored_required_external_source_cuts_added;
        };
        generateReceiverSubsets(options.tailored_bc_transfer_max_receiver_size,
                                addRequiredExternalSource);
    }
    if (tailored_active && options.tailored_bc_benders_inventory_cuts == "diagnostic") {
        if (stats != nullptr) stats->enabled_families.push_back("benders_inventory_diagnostic");
        auto addBendersInventoryCut = [&](const std::vector<int>& subset) {
            std::set<int> in_subset(subset.begin(), subset.end());
            int room_sum = 0;
            int initial_outside = 0;
            for (int i = 1; i <= V; ++i) {
                if (in_subset.count(i)) {
                    room_sum += std::max(0, instance.capacity[i] - instance.initial[i]);
                } else {
                    initial_outside += std::max(0, instance.initial[i]);
                }
            }
            int vehicle_capacity = 0;
            for (int k = 0; k < M; ++k) {
                const int move_budget = cunit > 1e-12
                    ? static_cast<int>(std::floor(instance.total_time_limit / cunit + 1e-9))
                    : instance.Q[k];
                vehicle_capacity += std::max(0, std::min(instance.Q[k], move_budget));
            }
            const double transfer_capacity =
                static_cast<double>(std::min({room_sum, initial_outside, vehicle_capacity}));
            Expr cut;
            for (int k = 0; k < M; ++k) {
                for (int j : subset) {
                    addTerm(cut, dName(k, j), 1.0);
                    addTerm(cut, pName(k, j), -1.0);
                }
            }
            writeConstraint(out, cid, cut, "<=", transfer_capacity);
            if (stats != nullptr) {
                ++stats->tailored_benders_inventory_candidates;
                ++stats->tailored_benders_inventory_cuts_added;
            }
        };
        for (int a = 1; a <= V; ++a) addBendersInventoryCut({a});
        for (int a = 1; a <= V; ++a) {
            for (int b = a + 1; b <= V; ++b) addBendersInventoryCut({a, b});
        }
        for (int a = 1; a <= V; ++a) {
            for (int b = a + 1; b <= V; ++b) {
                for (int c = b + 1; c <= V; ++c) addBendersInventoryCut({a, b, c});
            }
        }
    }
    if (!use_shared_interval_rows && strengthened && cutoff != nullptr && cutoff->enabled &&
        options.gini_spread_cuts && cutoff->gamma_U >= -1e-12 && V > 1) {
        if (stats != nullptr) stats->enabled_families.push_back("gini_pairwise_spread");
        for (int i = 1; i <= V; ++i) {
            for (int j = i + 1; j <= V; ++j) {
                Expr e;
                addTerm(e, hName(i, j), static_cast<double>(V - 1));
                for (int t = 1; t <= V; ++t) {
                    addTerm(e, rName(t), -static_cast<double>(V) * cutoff->gamma_U);
                }
                writeConstraint(out, cid, e, "<=", 0);
                if (stats != nullptr) ++stats->gini_spread_cuts_added;
            }
        }
    }
    if (add_low_gini_centering && !use_shared_interval_rows) {
        if (stats != nullptr) stats->enabled_families.push_back("low_gini_centering_band");
        double s_upper = 0.0;
        for (int i = 1; i <= V; ++i) {
            s_upper += static_cast<double>(y_ub[i]) / instance.target[i];
        }
        const double spread_ub =
            static_cast<double>(V) * cutoff->gamma_U * s_upper /
            static_cast<double>(V - 1);
        for (int i = 1; i <= V; ++i) {
            Expr lo; addTerm(lo, "r_min", 1); addTerm(lo, rName(i), -1);
            writeConstraint(out, cid, lo, "<=", 0);
            Expr hi; addTerm(hi, rName(i), 1); addTerm(hi, "r_max", -1);
            writeConstraint(out, cid, hi, "<=", 0);
            if (stats != nullptr) stats->low_gini_centering_rows_added += 2;
        }
        Expr width; addTerm(width, "r_max", 1); addTerm(width, "r_min", -1);
        writeConstraint(out, cid, width, "<=", std::max(0.0, spread_ub));
        if (stats != nullptr) ++stats->low_gini_centering_rows_added;
        if (options.compact_bc_variable_s_centering) {
            Expr variable_width;
            addTerm(variable_width, "r_max", static_cast<double>(V - 1));
            addTerm(variable_width, "r_min", -static_cast<double>(V - 1));
            for (int i = 1; i <= V; ++i) {
                addTerm(variable_width, rName(i), -static_cast<double>(V) * cutoff->gamma_U);
            }
            writeConstraint(out, cid, variable_width, "<=", 0.0);
            if (stats != nullptr) {
                stats->enabled_families.push_back("variable_s_low_gini_centering");
                ++stats->variable_s_centering_rows_added;
            }
        }
    }

    for (int i = 1; i <= V; ++i) {
        int bits = 1;
        while (((1LL << bits) - 1) < instance.capacity[i]) ++bits;
        Expr ybits; addTerm(ybits, yName(i), 1);
        Expr zprod; addTerm(zprod, zprodName(i), 1);
        for (int b = 0; b < bits; ++b) {
            const double coef = static_cast<double>(1LL << b);
            addTerm(ybits, bitName(i, b), -coef);
            addTerm(zprod, prodName(i, b), -coef);
        }
        writeConstraint(out, cid, ybits, "=", 0);
        writeConstraint(out, cid, zprod, "=", 0);
        for (int b = 0; b < bits; ++b) {
            Expr p_le_g; addTerm(p_le_g, prodName(i, b), 1); addTerm(p_le_g, "G", -1);
            writeConstraint(out, cid, p_le_g, "<=", 0);
            Expr p_le_bit; addTerm(p_le_bit, prodName(i, b), 1); addTerm(p_le_bit, bitName(i, b), -1);
            writeConstraint(out, cid, p_le_bit, "<=", 0);
            Expr p_ge; addTerm(p_ge, prodName(i, b), 1); addTerm(p_ge, "G", -1); addTerm(p_ge, bitName(i, b), -1);
            writeConstraint(out, cid, p_ge, ">=", -1);
            if (!use_shared_interval_rows && strengthened && cutoff != nullptr && cutoff->enabled &&
                options.compact_bc_tight_mccormick) {
                if (stats != nullptr && stats->tight_mccormick_rows_added == 0) {
                    stats->enabled_families.push_back("interval_tight_mccormick_G_bit");
                }
                Expr lb_bit; addTerm(lb_bit, prodName(i, b), 1);
                addTerm(lb_bit, bitName(i, b), -g_lb);
                writeConstraint(out, cid, lb_bit, ">=", 0);
                Expr ub_bit; addTerm(ub_bit, prodName(i, b), 1);
                addTerm(ub_bit, bitName(i, b), -g_ub);
                writeConstraint(out, cid, ub_bit, "<=", 0);
                Expr lb_g; addTerm(lb_g, prodName(i, b), 1);
                addTerm(lb_g, "G", -1);
                addTerm(lb_g, bitName(i, b), -g_ub);
                writeConstraint(out, cid, lb_g, ">=", -g_ub);
                Expr ub_g; addTerm(ub_g, prodName(i, b), 1);
                addTerm(ub_g, "G", -1);
                addTerm(ub_g, bitName(i, b), -g_lb);
                writeConstraint(out, cid, ub_g, "<=", -g_lb);
                if (stats != nullptr) stats->tight_mccormick_rows_added += 4;
            }
        }
    }
    Expr gini;
    for (int i = 1; i <= V; ++i) addTerm(gini, zprodName(i), static_cast<double>(V) / instance.target[i]);
    for (int i = 1; i <= V; ++i) {
        for (int j = i + 1; j <= V; ++j) addTerm(gini, hName(i, j), -1);
    }
    writeConstraint(out, cid, gini, ">=", 0);

    if (cutoff != nullptr && cutoff->enabled) {
        if (!use_shared_interval_rows) {
            Expr gl; addTerm(gl, "G", 1);
            writeConstraint(out, cid, gl, ">=", cutoff->gamma_L);
            Expr gu; addTerm(gu, "G", 1);
            writeConstraint(out, cid, gu, "<=", cutoff->gamma_U);
        }
        if (cutoff->add_objective_cutoff && !use_shared_interval_rows) {
            Expr obj_cutoff; addTerm(obj_cutoff, "G", 1);
            for (int i = 1; i <= V; ++i) {
                addTerm(obj_cutoff, eName(i), options.lambda * instance.weights[i]);
            }
            writeConstraint(out, cid, obj_cutoff, "<=", cutoff->incumbent_ub - cutoff->epsilon);
        }
        const double cutoff_value = cutoff->incumbent_ub - cutoff->epsilon;
        double s_upper = s_upper_domain;
        if (s_range_rows_active) {
            if (stats != nullptr) {
                stats->enabled_families.push_back(
                    options.compact_bc_s_range_refinement == "paper-safe"
                        ? "s_range_refinement_paper_safe"
                        : "s_range_refinement_diagnostic");
            }
            Expr s_lo;
            for (int i = 1; i <= V; ++i) addTerm(s_lo, rName(i), 1);
            writeConstraint(out, cid, s_lo, ">=", s_bucket_L);
            Expr s_hi = s_lo;
            writeConstraint(out, cid, s_hi, "<=", s_bucket_U);
            if (stats != nullptr) stats->s_range_rows_added += 2;
            s_upper = std::min(s_upper, s_bucket_U);
        }
        if (add_gs_product_definition) {
            if (stats != nullptr) {
                stats->enabled_families.push_back("gs_product_coupling");
            }
            Expr s_expr;
            for (int i = 1; i <= V; ++i) addTerm(s_expr, rName(i), 1);
            Expr h_expr;
            for (int i = 1; i <= V; ++i) {
                for (int j = i + 1; j <= V; ++j) addTerm(h_expr, hName(i, j), 1);
            }
            // McCormick envelope for W_GS = G * S over
            // G in [g_lb,g_ub], S in [sp_s_lower,sp_s_upper].
            Expr gs1; addTerm(gs1, "W_GS", 1);
            for (const auto& kv : s_expr) addTerm(gs1, kv.first, -g_lb * kv.second);
            addTerm(gs1, "G", -sp_s_lower);
            writeConstraint(out, cid, gs1, ">=", -g_lb * sp_s_lower);
            Expr gs2; addTerm(gs2, "W_GS", 1);
            for (const auto& kv : s_expr) addTerm(gs2, kv.first, -g_ub * kv.second);
            addTerm(gs2, "G", -sp_s_upper);
            writeConstraint(out, cid, gs2, ">=", -g_ub * sp_s_upper);
            Expr gs3; addTerm(gs3, "W_GS", 1);
            for (const auto& kv : s_expr) addTerm(gs3, kv.first, -g_ub * kv.second);
            addTerm(gs3, "G", -sp_s_lower);
            writeConstraint(out, cid, gs3, "<=", -g_ub * sp_s_lower);
            Expr gs4; addTerm(gs4, "W_GS", 1);
            for (const auto& kv : s_expr) addTerm(gs4, kv.first, -g_lb * kv.second);
            addTerm(gs4, "G", -sp_s_upper);
            writeConstraint(out, cid, gs4, "<=", -g_lb * sp_s_upper);
            if (stats != nullptr) stats->gs_mccormick_rows_added += 4;

            if (add_gs_product_static_row) {
                Expr h_upper = h_expr;
                addTerm(h_upper, "W_GS", -static_cast<double>(V));
                writeConstraint(out, cid, h_upper, "<=", 0.0);
                if (stats != nullptr) ++stats->gs_h_upper_rows_added;
                if (options.tailored_bc_gs_product_lower_row != "off") {
                    Expr h_lower = h_expr;
                    addTerm(h_lower, "W_GS", -static_cast<double>(V));
                    writeConstraint(out, cid, h_lower, ">=", 0.0);
                    if (stats != nullptr) ++stats->gs_h_lower_rows_added;
                }
            }
        }
        if (add_disagg_sp_definition) {
            if (stats != nullptr) {
                stats->enabled_families.push_back("disaggregated_sp_estimator");
            }
            Expr s_expr;
            for (int i = 1; i <= V; ++i) addTerm(s_expr, rName(i), 1);
            for (int i = 1; i <= V; ++i) {
                const std::string t_name = "T_SP_" + std::to_string(i);
                const double e_l = e_lower_domain[i];
                const double e_u = e_upper_domain[i];
                Expr t1; addTerm(t1, t_name, 1);
                for (const auto& kv : s_expr) addTerm(t1, kv.first, -e_l * kv.second);
                addTerm(t1, eName(i), -sp_s_lower);
                writeConstraint(out, cid, t1, ">=", -sp_s_lower * e_l);
                Expr t2; addTerm(t2, t_name, 1);
                for (const auto& kv : s_expr) addTerm(t2, kv.first, -e_u * kv.second);
                addTerm(t2, eName(i), -sp_s_upper);
                writeConstraint(out, cid, t2, ">=", -sp_s_upper * e_u);
                Expr t3; addTerm(t3, t_name, 1);
                for (const auto& kv : s_expr) addTerm(t3, kv.first, -e_l * kv.second);
                addTerm(t3, eName(i), -sp_s_upper);
                writeConstraint(out, cid, t3, "<=", -sp_s_upper * e_l);
                Expr t4; addTerm(t4, t_name, 1);
                for (const auto& kv : s_expr) addTerm(t4, kv.first, -e_u * kv.second);
                addTerm(t4, eName(i), -sp_s_lower);
                writeConstraint(out, cid, t4, "<=", -sp_s_lower * e_u);
                if (stats != nullptr) stats->disagg_sp_mccormick_rows_added += 4;
            }
            if (add_disagg_sp_estimator) {
                Expr disagg_estimator;
                for (int i = 1; i <= V; ++i) {
                    for (int j = i + 1; j <= V; ++j) addTerm(disagg_estimator, hName(i, j), 1);
                }
                for (int i = 1; i <= V; ++i) {
                    addTerm(disagg_estimator, "T_SP_" + std::to_string(i),
                            static_cast<double>(V) * options.lambda * instance.weights[i]);
                    addTerm(disagg_estimator, rName(i), -static_cast<double>(V) * cutoff_value);
                }
                writeConstraint(out, cid, disagg_estimator, "<=", 0.0);
                if (stats != nullptr) ++stats->disagg_sp_estimator_rows_added;
            }
        }
        if (!use_shared_interval_rows && strengthened && options.compact_bc_objective_estimator_cutoff &&
            cutoff->add_objective_cutoff && std::isfinite(s_upper) && s_upper > 1e-12) {
            if (stats != nullptr) {
                stats->enabled_families.push_back("objective_lower_estimator_cutoff");
            }
            Expr estimator;
            for (int i = 1; i <= V; ++i) {
                addTerm(estimator, eName(i),
                        static_cast<double>(V) * s_upper * options.lambda *
                        instance.weights[i]);
                for (int j = i + 1; j <= V; ++j) addTerm(estimator, hName(i, j), 1);
            }
            writeConstraint(out, cid, estimator, "<=",
                            static_cast<double>(V) * s_upper * cutoff_value);
            if (stats != nullptr) ++stats->objective_estimator_cutoff_rows_added;
        }
        if (add_sp_product_estimator && !use_shared_interval_rows) {
            if (stats != nullptr) {
                stats->enabled_families.push_back(
                    options.compact_bc_sp_product_estimator == "paper-safe"
                        ? "sp_product_objective_estimator_paper_safe"
                        : "sp_product_objective_estimator_diagnostic");
            }
            Expr s_expr;
            for (int i = 1; i <= V; ++i) addTerm(s_expr, rName(i), 1);
            Expr p_expr;
            for (int i = 1; i <= V; ++i) {
                addTerm(p_expr, eName(i), instance.weights[i]);
            }
            Expr mc1; addTerm(mc1, "W_SP", 1);
            for (const auto& kv : p_expr) addTerm(mc1, kv.first, -sp_s_lower * kv.second);
            for (const auto& kv : s_expr) addTerm(mc1, kv.first, -penalty_lb_domain * kv.second);
            writeConstraint(out, cid, mc1, ">=", -sp_s_lower * penalty_lb_domain);
            Expr mc2; addTerm(mc2, "W_SP", 1);
            for (const auto& kv : p_expr) addTerm(mc2, kv.first, -sp_s_upper * kv.second);
            for (const auto& kv : s_expr) addTerm(mc2, kv.first, -penalty_ub_domain * kv.second);
            writeConstraint(out, cid, mc2, ">=", -sp_s_upper * penalty_ub_domain);
            Expr mc3; addTerm(mc3, "W_SP", 1);
            for (const auto& kv : p_expr) addTerm(mc3, kv.first, -sp_s_upper * kv.second);
            for (const auto& kv : s_expr) addTerm(mc3, kv.first, -penalty_lb_domain * kv.second);
            writeConstraint(out, cid, mc3, "<=", -sp_s_upper * penalty_lb_domain);
            Expr mc4; addTerm(mc4, "W_SP", 1);
            for (const auto& kv : p_expr) addTerm(mc4, kv.first, -sp_s_lower * kv.second);
            for (const auto& kv : s_expr) addTerm(mc4, kv.first, -penalty_ub_domain * kv.second);
            writeConstraint(out, cid, mc4, "<=", -sp_s_lower * penalty_ub_domain);
            if (stats != nullptr) stats->sp_product_mccormick_rows_added += 4;

            Expr sp_estimator;
            for (int i = 1; i <= V; ++i) {
                for (int j = i + 1; j <= V; ++j) addTerm(sp_estimator, hName(i, j), 1);
            }
            addTerm(sp_estimator, "W_SP", static_cast<double>(V) * options.lambda);
            for (int i = 1; i <= V; ++i) {
                addTerm(sp_estimator, rName(i), -static_cast<double>(V) * cutoff_value);
            }
            writeConstraint(out, cid, sp_estimator, "<=", 0.0);
            if (stats != nullptr) ++stats->sp_product_estimator_rows_added;
        }
        if (!use_shared_interval_rows && strengthened && options.compact_bc_penalty_lb_closure) {
            double penalty_lb = penalty_lb_domain;
            if (stats != nullptr) {
                stats->enabled_families.push_back("penalty_lower_bound_closure");
                stats->penalty_lb = penalty_lb;
            }
            Expr p_lb;
            for (int i = 1; i <= V; ++i) {
                addTerm(p_lb, eName(i), instance.weights[i]);
            }
            writeConstraint(out, cid, p_lb, ">=", penalty_lb);
            if (stats != nullptr) ++stats->penalty_lb_rows_added;
            if (cutoff->add_objective_cutoff &&
                cutoff->gamma_L + options.lambda * penalty_lb >= cutoff_value - 1e-9) {
                Expr impossible;
                writeConstraint(out, cid, impossible, "<=", -1);
                if (stats != nullptr) ++stats->penalty_lb_rows_added;
            }
        }

        if (!use_shared_interval_rows &&
            (options.interval_oracle_penalty_domain_tightening ||
             options.interval_oracle_low_gini_tightening) &&
            cutoff->add_objective_cutoff &&
            options.lambda > 1e-12) {
            const double cutoff_value = cutoff->incumbent_ub - cutoff->epsilon;
            const double penalty_budget = (cutoff_value - cutoff->gamma_L) / options.lambda;
            if (std::isfinite(penalty_budget) && penalty_budget >= -1e-10) {
                for (int i = 1; i <= V; ++i) {
                    if (instance.weights[i] <= 1e-12) continue;
                    const double e_ub = std::max(0.0, penalty_budget / instance.weights[i]);
                    Expr ei; addTerm(ei, eName(i), 1);
                    writeConstraint(out, cid, ei, "<=", e_ub);
                }
            }
        }
    }

    if (dynamic_cuts != nullptr) {
        for (const DynamicCut& cut : *dynamic_cuts) {
            writeConstraint(out, cid, cut.expr, cut.sense, cut.rhs);
        }
    }

    out << "Bounds\n";
    for (const auto& kv : vars.bounds) {
        if (kv.second.second >= 1e90) out << " " << num(kv.second.first) << " <= " << kv.first << "\n";
        else out << " " << num(kv.second.first) << " <= " << kv.first << " <= " << num(kv.second.second) << "\n";
    }
    if (!vars.generals.empty()) {
        out << "Generals\n";
        for (const auto& v : vars.generals) out << " " << v << "\n";
    }
    if (!vars.binaries.empty()) {
        out << "Binaries\n";
        for (const auto& v : vars.binaries) out << " " << v << "\n";
    }
    out << "End\n";
}

std::string defaultCplexPath() {
    const char* bin = std::getenv("CPLEX_STUDIO_BINARIES2211");
    if (bin && *bin) {
        std::string s(bin);
        const std::size_t semi = s.find(';');
        if (semi != std::string::npos) s = s.substr(0, semi);
        std::filesystem::path p = std::filesystem::path(s) / "cplex.exe";
        if (std::filesystem::exists(p)) return p.string();
    }
    const std::filesystem::path fallback =
        "C:/Program Files/IBM/ILOG/CPLEX_Studio2211/cplex/bin/x64_win64/cplex.exe";
    if (std::filesystem::exists(fallback)) return fallback.string();
    return "cplex.exe";
}

std::string quote(const std::filesystem::path& p) {
    return "\"" + p.string() + "\"";
}

std::unordered_map<std::string, double> parseSolValues(const std::filesystem::path& sol_path,
                                                       std::string& status,
                                                       double& objective,
                                                       double& best_bound) {
    std::ifstream in(sol_path);
    if (!in) throw std::runtime_error("CPLEX solution file missing: " + sol_path.string());
    std::ostringstream ss;
    ss << in.rdbuf();
    const std::string text = ss.str();

    std::smatch m;
    if (std::regex_search(text, m, std::regex("solutionStatusString=\"([^\"]*)\""))) status = m[1].str();
    if (std::regex_search(text, m, std::regex("objectiveValue=\"([^\"]*)\""))) objective = std::stod(m[1].str());
    if (std::regex_search(text, m, std::regex("bestObjective=\"([^\"]*)\""))) best_bound = std::stod(m[1].str());

    std::unordered_map<std::string, double> values;
    const std::regex var_re("<variable [^>]*name=\"([^\"]+)\"[^>]*value=\"([^\"]+)\"");
    for (auto it = std::sregex_iterator(text.begin(), text.end(), var_re);
         it != std::sregex_iterator(); ++it) {
        values[it->str(1)] = std::stod(it->str(2));
    }
    return values;
}

long long parseCplexNodes(const std::filesystem::path& log_path) {
    std::ifstream in(log_path);
    if (!in) return 0;
    std::ostringstream ss;
    ss << in.rdbuf();
    const std::string text = ss.str();
    std::smatch m;
    long long nodes = 0;
    const std::regex nodes_re(R"(Nodes\s*=\s*([0-9]+))");
    for (auto it = std::sregex_iterator(text.begin(), text.end(), nodes_re);
         it != std::sregex_iterator(); ++it) {
        nodes = std::stoll(it->str(1));
    }
    return nodes;
}

double parseCplexBestBound(const std::filesystem::path& log_path) {
    std::ifstream in(log_path);
    if (!in) return std::numeric_limits<double>::quiet_NaN();
    std::ostringstream ss;
    ss << in.rdbuf();
    const std::string text = ss.str();
    std::smatch m;
    double bound = std::numeric_limits<double>::quiet_NaN();
    const std::regex final_bound_re(R"(Current MIP best bound\s*=\s*([-+0-9.eE]+))");
    if (std::regex_search(text, m, final_bound_re)) {
        bound = std::stod(m[1].str());
    }
    return bound;
}

std::string parseCplexTerminalStatus(const std::filesystem::path& log_path) {
    std::ifstream in(log_path);
    if (!in) return "log missing";
    std::ostringstream ss;
    ss << in.rdbuf();
    std::string text = ss.str();
    std::string lower = text;
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    if (lower.find("time limit exceeded") != std::string::npos) {
        return "time limit exceeded";
    }
    if (lower.find("integer infeasible") != std::string::npos ||
        lower.find("mip - integer infeasible") != std::string::npos ||
        lower.find("problem is integer infeasible") != std::string::npos ||
        lower.find("infeasibility row") != std::string::npos) {
        return "infeasible";
    }
    if (lower.find("optimal") != std::string::npos) {
        return "optimal";
    }
    return "unknown";
}

double solValue(const std::unordered_map<std::string, double>& values,
                const std::string& name) {
    auto it = values.find(name);
    return it == values.end() ? 0.0 : it->second;
}

bool familyEnabled(const SolveOptions& options, const std::string& family) {
    std::string list = options.compact_bc_dynamic_cut_families;
    std::transform(list.begin(), list.end(), list.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    if (list.empty() || list == "all") return true;
    return list.find(family) != std::string::npos;
}

void addDynamicCut(std::vector<DynamicCut>& cuts,
                   std::set<std::string>& signatures,
                   DynamicCutStats& stats,
                   const DynamicCut& cut) {
    if (!signatures.insert(cut.signature).second) return;
    cuts.push_back(cut);
    ++stats.total;
    if (cut.family == "support_duration") {
        ++stats.support_duration;
        stats.support_duration_violation =
            std::max(stats.support_duration_violation, cut.violation);
    } else if (cut.family == "route_cutset") {
        ++stats.route_cutset;
        stats.route_cutset_violation =
            std::max(stats.route_cutset_violation, cut.violation);
    } else if (cut.family == "transfer_compat") {
        ++stats.transfer_compat;
        stats.transfer_compat_violation =
            std::max(stats.transfer_compat_violation, cut.violation);
    } else if (cut.family == "visit_inventory_linking") {
        ++stats.visit_inventory_linking;
        stats.visit_inventory_linking_violation =
            std::max(stats.visit_inventory_linking_violation, cut.violation);
    } else if (cut.family == "objective_estimator") {
        ++stats.objective_estimator;
        stats.objective_estimator_violation =
            std::max(stats.objective_estimator_violation, cut.violation);
    } else if (cut.family == "receiver_source_cover") {
        ++stats.receiver_source_cover;
        stats.receiver_source_cover_violation =
            std::max(stats.receiver_source_cover_violation, cut.violation);
    }
}

std::string dynamicCutSummary(const DynamicCutStats& stats) {
    std::ostringstream out;
    out << "support_duration=" << stats.support_duration
        << ";route_cutset=" << stats.route_cutset
        << ";transfer_compat=" << stats.transfer_compat
        << ";visit_inventory_linking=" << stats.visit_inventory_linking
        << ";objective_estimator=" << stats.objective_estimator
        << ";receiver_source_cover=" << stats.receiver_source_cover;
    return out.str();
}

std::string dynamicViolationSummary(const DynamicCutStats& stats) {
    std::ostringstream out;
    out << "support_duration=" << stats.support_duration_violation
        << ";route_cutset=" << stats.route_cutset_violation
        << ";transfer_compat=" << stats.transfer_compat_violation
        << ";visit_inventory_linking=" << stats.visit_inventory_linking_violation
        << ";objective_estimator=" << stats.objective_estimator_violation
        << ";receiver_source_cover=" << stats.receiver_source_cover_violation;
    return out.str();
}

std::vector<DynamicCut> separateDynamicCuts(
    const Instance& instance,
    const SolveOptions& options,
    const CompactIntervalCutoffConfig& cutoff,
    const std::unordered_map<std::string, double>& values,
    std::set<std::string>& signatures,
    DynamicCutStats& stats) {
    std::vector<DynamicCut> added;
    const int V = instance.V;
    const int M = instance.M;
    const double cunit = instance.pickup_time + instance.drop_time;
    const double tol = std::max(1e-9, options.compact_bc_dynamic_cut_violation_tol);

    auto emit = [&](const DynamicCut& cut) {
        if (cut.family == "support_duration" &&
            options.tailored_bc_vector_support_cover_max_cuts > 0 &&
            stats.support_duration >= options.tailored_bc_vector_support_cover_max_cuts) {
            return;
        }
        if (cut.family == "route_cutset" &&
            options.tailored_bc_vector_route_cutset_max_cuts > 0 &&
            stats.route_cutset >= options.tailored_bc_vector_route_cutset_max_cuts) {
            return;
        }
        if (cut.violation + 1e-15 < options.tailored_bc_vector_cut_min_violation) {
            return;
        }
        const std::size_t before = added.size();
        addDynamicCut(added, signatures, stats, cut);
        if (added.size() == before) {
            // Duplicate in this round; global signature set already rejected it.
        }
    };

    if (familyEnabled(options, "support") || familyEnabled(options, "duration")) {
        const int max_support = std::max(2, std::min(4, options.compact_bc_support_cut_max_size));
        for (int k = 0; k < M; ++k) {
            std::vector<std::pair<double, int>> frac;
            for (int i = 1; i <= V; ++i) {
                const double z = solValue(values, zName(k, i));
                if (z > tol) frac.push_back({z, i});
            }
            std::sort(frac.begin(), frac.end(), std::greater<>());
            if (frac.size() > 10) frac.resize(10);
            const int n = static_cast<int>(frac.size());
            for (int a = 0; a < n; ++a) {
                for (int b = a + 1; b < n; ++b) {
                    std::vector<int> subset = {frac[a].second, frac[b].second};
                    const double lhs =
                        solValue(values, zName(k, subset[0])) +
                        solValue(values, zName(k, subset[1]));
                    const double cycle = pairCycleLowerBound(instance, subset[0], subset[1]);
                    const double min_handling = cunit;
                    if (cycle + min_handling <= instance.total_time_limit + 1e-9) continue;
                    const double violation = lhs - 1.0;
                    if (violation <= tol) continue;
                    DynamicCut cut;
                    cut.family = "support_duration";
                    cut.signature = "support:k" + std::to_string(k) + ":"
                        + std::to_string(subset[0]) + "_" + std::to_string(subset[1]);
                    for (int i : subset) addTerm(cut.expr, zName(k, i), 1);
                    cut.sense = "<=";
                    cut.rhs = 1.0;
                    cut.violation = violation;
                    emit(cut);
                }
            }
            if (max_support >= 3) {
                for (int a = 0; a < n; ++a) {
                    for (int b = a + 1; b < n; ++b) {
                        for (int c = b + 1; c < n; ++c) {
                            std::vector<int> subset = {
                                frac[a].second, frac[b].second, frac[c].second};
                            const double lhs =
                                solValue(values, zName(k, subset[0])) +
                                solValue(values, zName(k, subset[1])) +
                                solValue(values, zName(k, subset[2]));
                            const double cycle = tripleCycleLowerBound(
                                instance, subset[0], subset[1], subset[2]);
                            const double min_handling = cunit * 2.0;
                            if (cycle + min_handling <= instance.total_time_limit + 1e-9) continue;
                            const double violation = lhs - 2.0;
                            if (violation <= tol) continue;
                            DynamicCut cut;
                            cut.family = "support_duration";
                            cut.signature = "support:k" + std::to_string(k) + ":"
                                + std::to_string(subset[0]) + "_"
                                + std::to_string(subset[1]) + "_"
                                + std::to_string(subset[2]);
                            for (int i : subset) addTerm(cut.expr, zName(k, i), 1);
                            cut.sense = "<=";
                            cut.rhs = 2.0;
                            cut.violation = violation;
                            emit(cut);
                        }
                    }
                }
            }
        }
    }

    if (familyEnabled(options, "route") || familyEnabled(options, "cutset")) {
        const int max_size = std::min({5, V,
            std::max(2, options.tailored_bc_vector_route_cutset_max_size)});
        for (int k = 0; k < M; ++k) {
            std::vector<std::pair<double, int>> ranked;
            for (int i = 1; i <= V; ++i) {
                const double z = solValue(values, zName(k, i));
                if (z > tol) ranked.push_back({z, i});
            }
            std::sort(ranked.begin(), ranked.end(), std::greater<>());
            if (ranked.size() > 10) ranked.resize(10);
            std::vector<int> subset;
            std::function<void(int, int)> enumerate = [&](int start, int target_size) {
                if (options.tailored_bc_vector_route_cutset_max_cuts > 0 &&
                    stats.route_cutset >= options.tailored_bc_vector_route_cutset_max_cuts) {
                    return;
                }
                if (static_cast<int>(subset.size()) == target_size) {
                    std::set<int> inside(subset.begin(), subset.end());
                    for (int representative : subset) {
                        double boundary = 0.0;
                        Expr expr;
                        for (int i = 0; i <= V; ++i) {
                            const bool i_in = inside.count(i) > 0;
                            for (int j = 0; j <= V; ++j) {
                                if (i == j) continue;
                                const bool j_in = inside.count(j) > 0;
                                if (i_in == j_in) continue;
                                boundary += solValue(values, xName(k, i, j));
                                addTerm(expr, xName(k, i, j), 1.0);
                            }
                        }
                        const double violation =
                            2.0 * solValue(values, zName(k, representative)) - boundary;
                        if (violation <= tol) continue;
                        DynamicCut cut;
                        cut.family = "route_cutset";
                        std::ostringstream signature;
                        signature << "route:k" << k << ":l" << representative;
                        for (int station : subset) signature << ':' << station;
                        cut.signature = signature.str();
                        cut.expr = expr;
                        addTerm(cut.expr, zName(k, representative), -2.0);
                        cut.sense = ">=";
                        cut.rhs = 0.0;
                        cut.violation = violation;
                        emit(cut);
                        if (options.tailored_bc_vector_route_cutset_max_cuts > 0 &&
                            stats.route_cutset >= options.tailored_bc_vector_route_cutset_max_cuts) {
                            return;
                        }
                    }
                    return;
                }
                for (int pos = start; pos < static_cast<int>(ranked.size()); ++pos) {
                    subset.push_back(ranked[static_cast<std::size_t>(pos)].second);
                    enumerate(pos + 1, target_size);
                    subset.pop_back();
                }
            };
            for (int size = 2; size <= max_size; ++size) enumerate(0, size);
        }
    }

    if (familyEnabled(options, "transfer")) {
        for (int k = 0; k < M; ++k) {
            for (int j = 1; j <= V; ++j) {
                double lhs = solValue(values, dName(k, j));
                Expr expr;
                addTerm(expr, dName(k, j), 1);
                for (int i = 1; i <= V; ++i) {
                    if (i == j) continue;
                    const double route_lb =
                        instance.dist[0][i] + instance.dist[i][j] +
                        instance.dist[j][0] + cunit;
                    if (route_lb <= instance.total_time_limit + 1e-9) {
                        lhs -= solValue(values, pName(k, i));
                        addTerm(expr, pName(k, i), -1);
                    }
                }
                if (lhs <= tol) continue;
                DynamicCut cut;
                cut.family = "transfer_compat";
                cut.signature = "transfer:k" + std::to_string(k) + ":j" + std::to_string(j);
                cut.expr = expr;
                cut.sense = "<=";
                cut.rhs = 0.0;
                cut.violation = lhs;
                emit(cut);
            }
        }
    }

    if (familyEnabled(options, "visit") || familyEnabled(options, "inventory")) {
        for (int i = 1; i <= V; ++i) {
            double visit_mass = 0.0;
            Expr visit;
            for (int k = 0; k < M; ++k) {
                visit_mass += solValue(values, zName(k, i));
                addTerm(visit, zName(k, i), 1);
            }
            const double y = solValue(values, yName(i));
            const double up_lhs = y - instance.initial[i] -
                static_cast<double>(instance.capacity[i] - instance.initial[i]) * visit_mass;
            if (up_lhs > tol) {
                DynamicCut cut;
                cut.family = "visit_inventory_linking";
                cut.signature = "visit_up:i" + std::to_string(i);
                addTerm(cut.expr, yName(i), 1);
                for (int k = 0; k < M; ++k) {
                    addTerm(cut.expr, zName(k, i),
                        -static_cast<double>(instance.capacity[i] - instance.initial[i]));
                }
                cut.sense = "<=";
                cut.rhs = instance.initial[i];
                cut.violation = up_lhs;
                emit(cut);
            }
            const double lo_lhs = instance.initial[i] - y -
                static_cast<double>(instance.initial[i]) * visit_mass;
            if (lo_lhs > tol) {
                DynamicCut cut;
                cut.family = "visit_inventory_linking";
                cut.signature = "visit_lo:i" + std::to_string(i);
                addTerm(cut.expr, yName(i), -1);
                for (int k = 0; k < M; ++k) {
                    addTerm(cut.expr, zName(k, i), -static_cast<double>(instance.initial[i]));
                }
                cut.sense = "<=";
                cut.rhs = -instance.initial[i];
                cut.violation = lo_lhs;
                emit(cut);
            }
        }
    }

    if (familyEnabled(options, "objective") && cutoff.enabled &&
        cutoff.add_objective_cutoff && std::isfinite(cutoff.incumbent_ub)) {
        double S_U = 0.0;
        for (int i = 1; i <= V; ++i) {
            S_U += static_cast<double>(instance.capacity[i]) / instance.target[i];
        }
        if (S_U > 1e-12) {
            double h_val = 0.0;
            for (int i = 1; i <= V; ++i) {
                for (int j = i + 1; j <= V; ++j) {
                    h_val += solValue(values, hName(i, j));
                }
            }
            double p_val = 0.0;
            for (int i = 1; i <= V; ++i) {
                p_val += instance.weights[i] * solValue(values, eName(i));
            }
            const double rhs = static_cast<double>(V) * S_U *
                (cutoff.incumbent_ub - cutoff.epsilon);
            const double lhs = h_val + static_cast<double>(V) * S_U *
                options.lambda * p_val;
            const double violation = lhs - rhs;
            if (violation > tol) {
                DynamicCut cut;
                cut.family = "objective_estimator";
                cut.signature = "objective_estimator";
                for (int i = 1; i <= V; ++i) {
                    for (int j = i + 1; j <= V; ++j) {
                        addTerm(cut.expr, hName(i, j), 1);
                    }
                    addTerm(cut.expr, eName(i),
                        static_cast<double>(V) * S_U * options.lambda * instance.weights[i]);
                }
                cut.sense = "<=";
                cut.rhs = rhs;
                cut.violation = violation;
                emit(cut);
            }
        }
    }

    if (familyEnabled(options, "receiver") &&
        (options.compact_bc_receiver_source_cover_mode == "singleton-paper-safe" ||
         options.compact_bc_receiver_source_cover_mode == "pair-net-paper-safe" ||
         options.compact_bc_receiver_source_cover_mode == "paper-safe")) {
        for (int j = 1; j <= V; ++j) {
            const double y = solValue(values, yName(j));
            const double required = std::max(0.0, y - instance.initial[j]);
            if (required <= tol) continue;
            double delivered = 0.0;
            Expr expr;
            for (int k = 0; k < M; ++k) {
                delivered += solValue(values, dName(k, j));
                addTerm(expr, dName(k, j), 1);
            }
            const double violation = required - delivered;
            if (violation <= tol) continue;
            DynamicCut cut;
            cut.family = "receiver_source_cover";
            cut.signature = "receiver_singleton:j" + std::to_string(j);
            cut.expr = expr;
            cut.sense = ">=";
            cut.rhs = required;
            cut.violation = violation;
            emit(cut);
        }
    }

    return added;
}

ModelSizeStats analyzeLpModel(const std::filesystem::path& lp_path) {
    ModelSizeStats stats;
    std::ifstream in(lp_path);
    if (!in) return stats;
    std::string line;
    bool in_subject = false;
    bool in_bounds = false;
    bool in_generals = false;
    bool in_binaries = false;
    std::set<std::string> vars;
    const std::regex var_re(R"(([A-Za-z_][A-Za-z0-9_]*))");
    while (std::getline(in, line)) {
        if (line == "Subject To") {
            in_subject = true; in_bounds = in_generals = in_binaries = false; continue;
        }
        if (line == "Bounds") {
            in_bounds = true; in_subject = in_generals = in_binaries = false; continue;
        }
        if (line == "Generals") {
            in_generals = true; in_subject = in_bounds = in_binaries = false; continue;
        }
        if (line == "Binaries") {
            in_binaries = true; in_subject = in_bounds = in_generals = false; continue;
        }
        if (line == "End") break;
        if (in_subject && !line.empty() && line[0] == ' ') {
            ++stats.rows;
            for (auto it = std::sregex_iterator(line.begin(), line.end(), var_re);
                 it != std::sregex_iterator(); ++it) {
                const std::string token = it->str(1);
                if (token == "c") continue;
                if (token.size() > 0 && token[0] == 'c' &&
                    std::all_of(token.begin() + 1, token.end(), [](unsigned char ch) {
                        return std::isdigit(ch) != 0;
                    })) continue;
                if (token == "obj") continue;
                vars.insert(token);
                ++stats.nonzeros;
            }
        } else if ((in_bounds || in_generals || in_binaries) && !line.empty()) {
            for (auto it = std::sregex_iterator(line.begin(), line.end(), var_re);
                 it != std::sregex_iterator(); ++it) {
                const std::string token = it->str(1);
                if (token == "inf") continue;
                vars.insert(token);
            }
        }
    }
    stats.cols = static_cast<long long>(vars.size());
    stats.memory_mb = (static_cast<double>(stats.nonzeros) * 24.0 +
                       static_cast<double>(stats.rows + stats.cols) * 128.0) /
        (1024.0 * 1024.0);
    return stats;
}

std::string disabledFamiliesSummary(const SolveOptions& before,
                                    const SolveOptions& after) {
    std::vector<std::string> names;
    if (before.compact_bc_support_duration_cuts && !after.compact_bc_support_duration_cuts) {
        names.push_back("support_duration_static");
    }
    if (before.compact_bc_pairwise_transfer_compatibility && !after.compact_bc_pairwise_transfer_compatibility) {
        names.push_back("pairwise_transfer_static");
    }
    if (before.compact_bc_receiver_source_cover_cuts && !after.compact_bc_receiver_source_cover_cuts) {
        names.push_back("receiver_source_cover_static");
    }
    if (before.compact_bc_tight_mccormick && !after.compact_bc_tight_mccormick) {
        names.push_back("tight_mccormick");
    }
    if (before.low_gini_ratio_band_tightening && !after.low_gini_ratio_band_tightening) {
        names.push_back("low_gini_centering");
    }
    if (names.empty()) return "none";
    std::ostringstream out;
    for (std::size_t i = 0; i < names.size(); ++i) {
        if (i) out << "|";
        out << names[i];
    }
    return out.str();
}

long long estimateSupportRows(const Instance& instance, const SolveOptions& opt) {
    if (!opt.compact_bc_support_duration_cuts) return 0;
    const long long V = instance.V;
    const long long M = instance.M;
    long long pairs = V * (V - 1) / 2;
    long long triples = 0;
    if (opt.compact_bc_support_cut_max_size >= 3 && V >= 3) {
        triples = V * (V - 1) * (V - 2) / 6;
    }
    long long total = M * (pairs + triples);
    if (opt.compact_bc_support_cut_max_subsets > 0) {
        total = std::min(total, static_cast<long long>(opt.compact_bc_support_cut_max_subsets));
    }
    return total;
}

SolveOptions applyResourceAdaptiveCompactOptions(const Instance& instance,
                                                 const SolveOptions& opt,
                                                 SolveResult& result) {
    SolveOptions adjusted = opt;
    result.compact_bc_model_size_policy = opt.compact_bc_model_size_policy;
    const long long V = instance.V;
    const long long M = instance.M;
    result.compact_bc_rows_estimated =
        M * (V + 1) * (V + 1) * 4 +
        V * V * 6 +
        estimateSupportRows(instance, adjusted);
    result.compact_bc_cols_estimated =
        M * (V + 1) * (V + 1) +
        M * V * 6 +
        V * V * 2;
    result.compact_bc_nonzeros_estimated =
        result.compact_bc_rows_estimated * 8;
    result.compact_bc_memory_estimate_mb =
        (static_cast<double>(result.compact_bc_nonzeros_estimated) * 24.0 +
         static_cast<double>(result.compact_bc_rows_estimated + result.compact_bc_cols_estimated) * 128.0) /
        (1024.0 * 1024.0);
    if (opt.compact_bc_model_size_policy == "diagnostic-minimal") {
        adjusted.compact_bc_support_duration_cuts = false;
        adjusted.compact_bc_pairwise_transfer_compatibility = false;
        adjusted.compact_bc_receiver_source_cover_cuts = false;
        adjusted.compact_bc_tight_mccormick = false;
        adjusted.low_gini_ratio_band_tightening = false;
        adjusted.compact_bc_support_cut_max_subsets = 0;
    } else if (opt.compact_bc_model_size_policy == "resource-adaptive") {
        const bool row_hit = opt.compact_bc_max_rows > 0 &&
            result.compact_bc_rows_estimated > opt.compact_bc_max_rows;
        const bool col_hit = opt.compact_bc_max_cols > 0 &&
            result.compact_bc_cols_estimated > opt.compact_bc_max_cols;
        const bool nz_hit = opt.compact_bc_max_nonzeros > 0 &&
            result.compact_bc_nonzeros_estimated > opt.compact_bc_max_nonzeros;
        const bool mem_hit = opt.compact_bc_max_memory_mb > 0.0 &&
            result.compact_bc_memory_estimate_mb > opt.compact_bc_max_memory_mb;
        if (row_hit || col_hit || nz_hit || mem_hit) {
            adjusted.compact_bc_support_duration_cuts = false;
            adjusted.compact_bc_pairwise_transfer_compatibility = false;
            adjusted.compact_bc_receiver_source_cover_cuts = false;
            adjusted.low_gini_ratio_band_tightening = false;
            adjusted.compact_bc_support_cut_max_subsets = 0;
            if (adjusted.compact_bc_root_cut_rounds <= 0) {
                adjusted.compact_bc_root_cut_rounds = 1;
            }
            if (adjusted.compact_bc_dynamic_cut_families.empty()) {
                adjusted.compact_bc_dynamic_cut_families =
                    "support,transfer,visit,objective,receiver";
            }
        }
    }
    if (opt.compact_bc_expensive_static_families == "off" ||
        opt.compact_bc_use_dynamic_instead_of_static) {
        adjusted.compact_bc_support_duration_cuts = false;
        adjusted.compact_bc_pairwise_transfer_compatibility = false;
        adjusted.compact_bc_receiver_source_cover_cuts = false;
        adjusted.compact_bc_support_cut_max_subsets = 0;
        if (adjusted.compact_bc_root_cut_rounds <= 0 &&
            opt.compact_bc_use_dynamic_instead_of_static) {
            adjusted.compact_bc_root_cut_rounds = 1;
        }
        if (adjusted.compact_bc_dynamic_cut_families.empty() &&
            opt.compact_bc_use_dynamic_instead_of_static) {
            adjusted.compact_bc_dynamic_cut_families =
                "support,transfer,visit,objective,receiver";
        }
    }
    result.compact_bc_disabled_families_due_to_size =
        disabledFamiliesSummary(opt, adjusted);
    return adjusted;
}

std::unordered_map<std::string, double> solveRootRelaxation(
    const SolveOptions& options,
    const std::filesystem::path& lp_path,
    const std::filesystem::path& sol_path,
    const std::filesystem::path& log_path,
    double time_limit,
    int threads,
    std::string& status,
    double& objective,
    double& best_bound) {
    const std::filesystem::path cmd_path = log_path.parent_path() /
        (log_path.stem().string() + ".cplex");
    std::ofstream cmd(cmd_path);
    cmd << "set threads " << std::max(1, threads) << "\n";
    if (time_limit > 0.0) cmd << "set timelimit " << time_limit << "\n";
    cmd << "read " << lp_path.string() << "\n";
    cmd << "change problem lp\n";
    cmd << "optimize\n";
    cmd << "write " << sol_path.string() << "\n";
    cmd << "quit\n";
    cmd.close();
    const std::string cplex = defaultCplexPath();
    const std::string command = "cmd /C \"" + quote(cplex) + " -f "
        + quote(cmd_path) + " > " + quote(log_path) + " 2>&1\"";
    const int rc = std::system(command.c_str());
    (void)options;
    (void)rc;
    if (!std::filesystem::exists(sol_path)) {
        status = parseCplexTerminalStatus(log_path);
        objective = std::numeric_limits<double>::quiet_NaN();
        best_bound = std::numeric_limits<double>::quiet_NaN();
        return {};
    }
    return parseSolValues(sol_path, status, objective, best_bound);
}

std::vector<RoutePlan> reconstructRoutes(const Instance& instance,
                                         const std::unordered_map<std::string, double>& v) {
    std::vector<RoutePlan> routes;
    for (int k = 0; k < instance.M; ++k) {
        RoutePlan route;
        route.vehicle = k;
        route.nodes.push_back(0);
        int current = 0;
        std::set<int> seen;
        while (true) {
            int next = -1;
            for (int j = 0; j <= instance.V; ++j) {
                if (j == current) continue;
                auto it = v.find(xName(k, current, j));
                if (it != v.end() && it->second > 0.5) {
                    next = j;
                    break;
                }
            }
            if (next <= 0) break;
            if (!seen.insert(next).second) break;
            route.nodes.push_back(next);
            current = next;
        }
        route.nodes.push_back(0);
        for (std::size_t idx = 1; idx + 1 < route.nodes.size(); ++idx) {
            const int station = route.nodes[idx];
            StopOperation op;
            op.station = station;
            auto pit = v.find(pName(k, station));
            auto dit = v.find(dName(k, station));
            op.pickup = (pit == v.end()) ? 0 : static_cast<int>(std::llround(pit->second));
            op.drop = (dit == v.end()) ? 0 : static_cast<int>(std::llround(dit->second));
            route.operations.push_back(op);
        }
        routes.push_back(std::move(route));
    }
    return routes;
}

bool statusIsOptimal(const std::string& status) {
    std::string s = status;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s.find("optimal") != std::string::npos;
}

bool statusIsInfeasible(const std::string& status) {
    std::string s = status;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s.find("infeasible") != std::string::npos;
}

bool statusIsTimeLimited(const std::string& status) {
    std::string s = status;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s.find("time") != std::string::npos || s.find("limit") != std::string::npos;
}

std::string nativeMipStatusClass(int status_code) {
    switch (status_code) {
    case kCplexMipOptimal: return "native_exact_optimal_status";
    case kCplexMipOptimalTolerance: return "native_tolerance_optimal_status";
    case kCplexMipInfeasible: return "native_infeasible_status";
    case kCplexMipTimeLimitFeasible: return "native_time_limit_feasible_status";
    case kCplexMipTimeLimitNoIncumbent:
        return "native_time_limit_no_incumbent_status";
    case kCplexMipOptimalUnscaledInfeasibilities:
        return "native_optimal_unscaled_infeasibilities_status";
    default: return "unknown_native_status";
    }
}

void populateNativeMipEvidenceFields(
    SolveResult& result,
    const NativeMipEvidence& native,
    long long environment_count,
    long long problem_count,
    long long model_read_count,
    long long mipopt_count,
    long long freeprob_count,
    long long close_count,
    long long node_count,
    long long open_node_count,
    int solution_count) {
    result.native_mip_evidence_available = native.solve_returned;
    result.native_mipopt_return_code = native.mipopt_return_code;
    result.native_mip_status_code = native.status_code;
    result.native_mip_status_text_available = !native.status_text.empty();
    result.native_mip_status_text = native.status_text;
    result.native_mip_status_class = nativeMipStatusClass(native.status_code);
    result.native_mip_status_code_text_consistent =
        cplexMipStatusTextConsistent(native.status_code, native.status_text);
    result.native_mip_objective_return_code = native.objective_return_code;
    result.native_mip_objective_available = native.objective_available;
    result.native_mip_objective = native.objective;
    result.native_mip_best_bound_return_code = native.best_bound_return_code;
    result.native_mip_best_bound_available = native.best_bound_available;
    result.native_mip_best_bound = native.best_bound;

    result.native_mip_relative_gap_param_id = native.relative_gap.parameter_id;
    result.native_mip_relative_gap_requested = native.relative_gap.requested;
    result.native_mip_relative_gap_set_return_code =
        native.relative_gap.setter_return_code;
    result.native_mip_relative_gap_get_return_code =
        native.relative_gap.getter_return_code;
    result.native_mip_relative_gap_effective_available =
        native.relative_gap.getter_return_code == 0;
    result.native_mip_relative_gap_effective = native.relative_gap.effective;
    result.native_mip_absolute_gap_param_id = native.absolute_gap.parameter_id;
    result.native_mip_absolute_gap_requested = native.absolute_gap.requested;
    result.native_mip_absolute_gap_set_return_code =
        native.absolute_gap.setter_return_code;
    result.native_mip_absolute_gap_get_return_code =
        native.absolute_gap.getter_return_code;
    result.native_mip_absolute_gap_effective_available =
        native.absolute_gap.getter_return_code == 0;
    result.native_mip_absolute_gap_effective = native.absolute_gap.effective;
    result.native_mip_strict_gap_parameters_valid =
        native.strict_gap_configuration_valid;
    result.native_mip_cplex_relative_gap_return_code =
        native.mip_relative_gap_return_code;
    result.native_mip_cplex_relative_gap_available =
        native.mip_relative_gap_available;
    result.native_mip_cplex_relative_gap = native.mip_relative_gap;

    result.native_mip_node_count_available = native.solve_returned;
    result.native_mip_node_count = node_count;
    result.native_mip_open_node_count_available = native.solve_returned;
    result.native_mip_open_node_count = open_node_count;
    result.native_mip_solution_count_available = native.solve_returned;
    result.native_mip_solution_count = solution_count;
    result.native_mip_solver_finalization_reached = native.solve_returned &&
        native.mipopt_return_code == 0;
    result.native_mip_evidence_capture_complete =
        native.evidence_capture_complete;
    result.native_mip_problem_freed = native.free_problem_return_code == 0;
    result.native_mip_freeprob_return_code = native.free_problem_return_code;
    result.native_mip_environment_closed =
        native.close_environment_return_code == 0;
    result.native_mip_close_return_code =
        native.close_environment_return_code;
    result.native_mip_environment_count = environment_count;
    result.native_mip_problem_count = problem_count;
    result.native_mip_model_read_count = model_read_count;
    result.native_mip_mipopt_count = mipopt_count;
    result.native_mip_freeprob_count = freeprob_count;
    result.native_mip_close_count = close_count;
    result.native_mip_lifecycle_valid =
        environment_count == 1 && problem_count == 1 &&
        model_read_count == 1 && mipopt_count == 1 &&
        freeprob_count == 1 && close_count == 1 &&
        result.native_mip_problem_freed &&
        result.native_mip_environment_closed;
    result.native_mip_finalization_state =
        result.native_mip_lifecycle_valid &&
                result.native_mip_solver_finalization_reached
            ? "solver_returned_and_cleanup_complete"
            : (native.solve_returned ? "solver_returned_cleanup_incomplete"
                                     : "solver_not_returned");
}

StrictCertificateDecision evaluateAndPopulateStrictCertificate(
    SolveResult& result,
    const NativeMipEvidence& native,
    bool verified_objective_available,
    double verified_objective,
    bool verified_original_feasible,
    bool verified_objective_consistent,
    bool exactness_lifecycle_complete) {
    result.verified_incumbent_objective_available =
        verified_objective_available;
    result.verified_incumbent_objective = verified_objective;
    result.verified_incumbent_original_problem_feasible =
        verified_original_feasible;
    result.verified_incumbent_objective_consistent =
        verified_objective_consistent;
    result.verified_incumbent_objective_residual_available =
        verified_objective_available && native.objective_available;
    if (result.verified_incumbent_objective_residual_available) {
        result.verified_incumbent_objective_residual =
            verified_objective - native.objective;
    }

    StrictCertificateInput input;
    input.native_status_code = native.status_code;
    input.native_status_text = native.status_text;
    input.native_objective_return_code = native.objective_return_code;
    input.native_objective_available = native.objective_available;
    input.native_objective = native.objective;
    input.native_best_bound_return_code = native.best_bound_return_code;
    input.native_best_bound_available = native.best_bound_available;
    input.native_best_bound = native.best_bound;
    input.native_cplex_relative_gap_return_code =
        native.mip_relative_gap_return_code;
    input.native_cplex_relative_gap_available =
        native.mip_relative_gap_available;
    input.native_cplex_relative_gap = native.mip_relative_gap;
    input.verified_upper_bound_available = verified_objective_available;
    input.verified_upper_bound = verified_objective;
    input.verifier_passed = verified_original_feasible &&
        verified_objective_consistent;
    input.solver_finalization_reached = native.solve_returned &&
        native.mipopt_return_code == 0;
    input.lifecycle_complete = exactness_lifecycle_complete;
    // No production objective-lattice or independent exact module exists in
    // Round 21.  Exact floating-point equality is therefore observational and
    // cannot close a 102/tolerance certificate.
    input.bound_equality_proof_conditions_passed = false;
    input.independent_exact_certificate_conditions_passed = false;
    input.relative_gap = native.relative_gap;
    input.absolute_gap = native.absolute_gap;
    const StrictCertificateDecision decision =
        classifyStrictCertificate(input);

    result.strict_certificate_class = decision.certificate_class;
    result.strict_certificate_rejection_reason = decision.rejection_reason.empty()
        ? "none" : decision.rejection_reason;
    result.strict_certified_original_problem =
        decision.strict_certified_original_problem;
    result.strict_native_objective_valid = decision.native_objective_valid;
    result.strict_native_best_bound_valid = decision.native_best_bound_valid;
    result.strict_bound_equality_closed = decision.bound_equality_closed;
    result.strict_bound_equality_proof_module = "none";
    result.strict_bound_equality_proof_conditions_satisfied = false;
    result.strict_independent_exact_certificate_module = "none";
    result.strict_independent_exact_certificate_conditions_satisfied = false;

    result.native_mip_absolute_gap_available = decision.native_gap_available;
    result.native_mip_signed_bound_residual_available =
        decision.native_gap_available;
    result.native_mip_relative_gap_available = decision.native_gap_available;
    if (decision.native_gap_available) {
        result.native_mip_absolute_gap = decision.native_absolute_gap;
        result.native_mip_signed_bound_residual =
            decision.native_signed_bound_residual;
        result.native_mip_bound_inversion = decision.native_bound_inversion;
        result.native_mip_relative_gap = decision.native_relative_gap;
    }
    result.verified_incumbent_absolute_gap_available =
        decision.verified_gap_available;
    result.verified_incumbent_signed_bound_residual_available =
        decision.verified_gap_available;
    result.verified_incumbent_relative_gap_available =
        decision.verified_gap_available;
    result.verified_incumbent_project_relative_gap_available =
        decision.verified_gap_available;
    if (decision.verified_gap_available) {
        result.verified_incumbent_absolute_gap =
            decision.verified_absolute_gap;
        result.verified_incumbent_signed_bound_residual =
            decision.verified_signed_bound_residual;
        result.verified_incumbent_bound_inversion =
            decision.verified_bound_inversion;
        result.verified_incumbent_relative_gap =
            decision.verified_relative_gap;
        result.verified_incumbent_project_relative_gap =
            decision.verified_project_relative_gap;
    }
    result.strict_lower_bound_source = native.best_bound_available
        ? "native_CPXgetbestobjval" : "unavailable";
    return decision;
}

} // namespace

SolveResult solveCplexBaseline(const Instance& instance, const SolveOptions& options) {
    const auto start = Clock::now();
    SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "cplex";
    result.status = "running";
    result.solver_finalization_reached = false;
    result.process_return_code = -1;
    result.time_budget_seconds = options.solve_time_limit;
    result.notes.push_back(instance.distance_convention);
    const int effective_cplex_threads =
        options.cplex_threads > 0 ? options.cplex_threads : std::max(1, options.threads);
    result.cplex_threads = effective_cplex_threads;
    result.mip_threads = options.mip_threads;
    result.compact_bc_solver_threads = 0;
    result.solver_thread_policy =
        effective_cplex_threads == 1
            ? "plain_cplex_single_thread"
            : "plain_cplex_multithread";
    result.thread_fairness_class =
        effective_cplex_threads == 1
            ? "one_thread_fair"
            : "multithread_diagnostic";

    const bool strengthened = !options.plain_baseline;
    result.notes.push_back(strengthened
        ? "CPLEX compact MILP with operation-time conservation, mode constraints, subset duration cuts, and symmetry cuts."
        : "CPLEX compact MILP with operation-time conservation and original-style Gini product linearization.");

    try {
        const std::string stem = std::filesystem::path(instance.name).stem().string()
            + (strengthened ? "_strengthened" : "_plain");
        const auto run_id = std::chrono::duration_cast<std::chrono::milliseconds>(
            Clock::now().time_since_epoch()).count();
        const std::filesystem::path work_dir = std::filesystem::path("results") / "cplex_work"
            / (stem + "_" + std::to_string(run_id));
        std::filesystem::create_directories(work_dir);
        const std::filesystem::path lp_path = work_dir / "model.lp";
        const std::filesystem::path cplex_log = options.log_path.empty()
            ? (work_dir / "cplex.log") : std::filesystem::path(options.log_path);
        result.log_file = cplex_log.string();
        result.notes.push_back("In-process CPLEX callable-library solve sets and reads back threads="
            + std::to_string(effective_cplex_threads)
            + "; plain CPLEX rows are fair single-thread rows only when --cplex-threads 1 is used.");

        std::string solver_name = options.mip_solver.empty()
            ? "cplex" : options.mip_solver;
        std::transform(solver_name.begin(), solver_name.end(), solver_name.begin(),
                       [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
        if (solver_name != "cplex") {
            throw std::runtime_error("compact interval BC currently supports --mip-solver cplex only");
        }

        writeCompactLp(instance, options, lp_path, strengthened);
        const PlainCplexApiSolveResult api = solvePlainCplexWithStrictApi(
            lp_path, options.solve_time_limit, effective_cplex_threads,
            cplex_log);
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.actual_runtime_seconds = result.runtime_seconds;

        populateNativeMipEvidenceFields(
            result, api.native, api.environment_count, api.problem_count,
            api.model_read_count, api.mipopt_count, api.freeprob_count,
            api.close_count, api.node_count, api.open_node_count,
            api.native_solution_count);
        result.native_mip_threads_requested = api.threads_requested;
        result.native_mip_threads_set_return_code =
            api.threads_set_return_code;
        result.native_mip_threads_get_return_code =
            api.threads_get_return_code;
        result.native_mip_threads_effective = api.threads_effective;
        result.native_mip_presolve_requested = api.presolve_requested;
        result.native_mip_presolve_set_return_code =
            api.presolve_set_return_code;
        result.native_mip_presolve_get_return_code =
            api.presolve_get_return_code;
        result.native_mip_presolve_effective = api.presolve_effective;
        result.native_mip_search_requested = api.search_requested;
        result.native_mip_search_set_return_code = api.search_set_return_code;
        result.native_mip_search_get_return_code = api.search_get_return_code;
        result.native_mip_search_effective = api.search_effective;
        result.native_mip_node_select_requested = api.node_select_requested;
        result.native_mip_node_select_set_return_code =
            api.node_select_set_return_code;
        result.native_mip_node_select_get_return_code =
            api.node_select_get_return_code;
        result.native_mip_node_select_effective = api.node_select_effective;
        result.native_mip_time_limit_param_id = api.time_limit_parameter_id;
        result.native_mip_time_limit_requested = api.time_limit_requested;
        result.native_mip_time_limit_set_return_code =
            api.time_limit_set_return_code;
        result.native_mip_time_limit_get_return_code =
            api.time_limit_get_return_code;
        result.native_mip_time_limit_effective_available =
            api.time_limit_get_return_code == 0;
        result.native_mip_time_limit_effective = api.time_limit_effective;
        result.nodes = api.node_count;
        result.open_nodes = api.open_node_count;
        result.solver_finalization_reached =
            result.native_mip_solver_finalization_reached;
        result.process_return_code = api.native.mipopt_return_code;

        bool verified_objective_available = false;
        bool verified_original_feasible = false;
        bool verified_objective_consistent = false;
        double verified_objective = 0.0;
        if (api.native.objective_available && !api.values.empty()) {
            result.routes = reconstructRoutes(instance, api.values);
            result.verification = verifySolution(
                instance, result.routes, options.lambda);
            verified_original_feasible = result.verification.feasible &&
                result.verification.objective_matches &&
                result.verification.errors.empty() &&
                std::isfinite(result.verification.objective);
            if (verified_original_feasible) {
                verified_objective_available = true;
                verified_objective = result.verification.objective;
                result.final_inventory = result.verification.final_inventory;
                result.G = result.verification.G;
                result.P = result.verification.P;
                result.objective = verified_objective;
                result.upper_bound = verified_objective;
                verified_objective_consistent =
                    std::fabs(verified_objective - api.native.objective) <=
                    1e-8 * std::max({1.0, std::fabs(verified_objective),
                                     std::fabs(api.native.objective)});
            }
        }
        if (api.native.best_bound_available) {
            result.lower_bound = api.native.best_bound;
        }
        const StrictCertificateDecision decision =
            evaluateAndPopulateStrictCertificate(
                result, api.native, verified_objective_available,
                verified_objective, verified_original_feasible,
                verified_objective_consistent,
                api.lifecycle_valid && api.native.mipopt_return_code == 0);
        if (decision.verified_gap_available) {
            result.gap = decision.verified_project_relative_gap;
        }
        result.strict_serialized_lower_bound_matches_native =
            api.native.best_bound_available &&
            result.lower_bound == api.native.best_bound;
        result.strict_serialized_gap_consistent =
            decision.verified_gap_available &&
            result.gap == decision.verified_project_relative_gap;

        if (decision.strict_certified_original_problem) {
            result.status = "optimal";
            result.certificate =
                "Strict Round 21 certificate: native CPLEX status 101, zero relative/absolute MIP-gap parameter round trips, retained native best bound, completed lifecycle, and independently verified native incumbent.";
        } else if (decision.certificate_class == "infeasible") {
            result.status = "infeasible";
            result.certificate =
                "Native CPLEX status 103 certifies model infeasibility; no optimal incumbent certificate is claimed.";
        } else if (decision.certificate_class == "time_limit_valid_bound") {
            result.status = "time_limit";
            result.certificate =
                "Time limit reached; the retained official lower bound is the raw CPXgetbestobjval value and no strict optimality claim is made.";
        } else if (!api.available || !api.native.solve_returned) {
            result.status = "error";
            result.certificate = "In-process CPLEX solve failed before native finalization: " +
                (api.fail_reason.empty() ? std::string("unknown_failure")
                                         : api.fail_reason);
        } else {
            result.status = "not_certified";
            result.certificate = "Strict optimality rejected (" +
                decision.certificate_class + "): " +
                result.strict_certificate_rejection_reason +
                ". Raw native objective, best bound, gaps, and status remain serialized.";
        }
        result.notes.push_back("CPLEX native status code/text: " +
            std::to_string(api.native.status_code) + " / " +
            api.native.status_text);
        result.notes.push_back("CPXmipopt return code: " +
            std::to_string(api.native.mipopt_return_code));
        result.notes.push_back("strict certificate class: " +
            decision.certificate_class);
        result.notes.push_back("LP file: " + lp_path.string());
        result.notes.push_back(
            "Solver output is emitted by the in-process callable library to the enclosing run log: " +
            cplex_log.string());
    } catch (const std::bad_alloc& e) {
        result.status = "model_size_limit";
        result.interval_exact_cutoff_certificate_basis = "compact_interval_bc_model_size_limit";
        result.certificate = std::string("Compact interval BC model generation/solve exceeded available memory: ") + e.what();
        result.compact_interval_bc_rejection_reason = result.certificate;
        result.compact_bc_rejection_reason = result.certificate;
        result.compact_bc_model_size_stop_reason = "std_bad_alloc";
        result.compact_interval_bc_bound_valid = false;
        result.compact_bc_bound_valid = false;
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.actual_runtime_seconds = result.runtime_seconds;
        result.interval_exact_cutoff_runtime_seconds = result.runtime_seconds;
        result.compact_bc_time_seconds = result.runtime_seconds;
    } catch (const std::exception& e) {
        result.status = "error";
        result.certificate = std::string("CPLEX baseline failed: ") + e.what();
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.actual_runtime_seconds = result.runtime_seconds;
    }

    return result;
}

SolveResult solveIntervalExactCutoffOracle(const Instance& instance, const SolveOptions& options) {
    const auto start = Clock::now();
    SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "interval-cutoff-oracle";
    result.status = "running";
    result.certificate_scope = "interval_original_cutoff_oracle";
    result.interval_exact_cutoff_oracle = options.interval_exact_cutoff_oracle;
    result.interval_exact_cutoff_attempted = true;
    result.interval_exact_cutoff_gamma_L = options.interval_exact_cutoff_gamma_L;
    result.interval_exact_cutoff_gamma_U = options.interval_exact_cutoff_gamma_U;
    result.interval_exact_cutoff_UB = options.interval_exact_cutoff_UB;
    result.interval_exact_cutoff_epsilon = options.interval_exact_cutoff_epsilon;
    result.compact_interval_bc_enabled =
        options.interval_exact_cutoff_oracle == "compact-mip";
    result.compact_interval_bc_solver = options.mip_solver.empty()
        ? "cplex" : options.mip_solver;
    const int effective_compact_threads = options.compact_bc_threads > 0
        ? options.compact_bc_threads
        : (options.mip_threads > 0 ? options.mip_threads : std::max(1, options.threads));
    result.cplex_threads = options.cplex_threads;
    result.mip_threads = options.mip_threads;
    result.compact_interval_bc_threads = effective_compact_threads;
    result.compact_bc_solver_threads = result.compact_interval_bc_threads;
    result.solver_thread_policy =
        effective_compact_threads == 1
            ? "compact_bc_single_thread"
            : "compact_bc_multithread";
    result.thread_fairness_class =
        effective_compact_threads == 1
            ? "one_thread_fair"
            : "multithread_diagnostic";
    result.compact_bc_cut_profile = options.compact_bc_cut_profile;
    result.compact_bc_receiver_source_cover_mode =
        options.compact_bc_receiver_source_cover_mode;
    result.compact_bc_root_cut_rounds = options.compact_bc_root_cut_rounds;
    result.compact_bc_total_root_cut_rounds = options.compact_bc_root_cut_rounds;
    result.compact_bc_root_cut_time_limit = options.compact_bc_root_cut_time_limit;
    result.compact_bc_dynamic_cut_families = options.compact_bc_dynamic_cut_families;
    result.compact_bc_root_probe = options.compact_bc_root_probe;
    result.compact_bc_domain_propagation_mode =
        options.compact_bc_domain_propagation_mode;
    result.compact_bc_domain_propagation_rounds =
        options.compact_bc_domain_propagation_rounds;
    result.compact_bc_low_gini_strengthening =
        options.compact_bc_low_gini_strengthening;
    result.compact_bc_denominator_bound_mode =
        options.compact_bc_denominator_bound_mode;
    result.compact_bc_objective_estimator_mode =
        options.compact_bc_objective_estimator_mode;
    result.compact_bc_low_gini_aggressive_diagnostic =
        options.compact_bc_low_gini_strengthening == "aggressive-diagnostic";
    result.compact_bc_s_range_refinement =
        options.compact_bc_s_range_refinement;
    result.s_range_bucket_count = options.compact_bc_s_range_buckets;
    result.s_range_bucket_id = options.compact_bc_s_range_bucket_id;
    result.s_range_bucket_L = options.compact_bc_s_range_bucket_L;
    result.s_range_bucket_U = options.compact_bc_s_range_bucket_U;
    result.tailored_bc_s_bucket_ledger = options.tailored_bc_s_bucket_ledger;
    result.tailored_bc_s_bucket_count =
        std::max(1, options.tailored_bc_s_bucket_count);
    result.tailored_bc_s_bucket_policy = options.tailored_bc_s_bucket_policy;
    result.tailored_bc_s_bucket_time_budget =
        options.tailored_bc_s_bucket_time_budget;
    result.tailored_bc_s_bucket_merge_audit =
        options.tailored_bc_s_bucket_merge_audit;
    result.tailored_bc_s_bucket_max_depth =
        options.tailored_bc_s_bucket_max_depth;
    result.tailored_bc_s_bucket_min_width =
        options.tailored_bc_s_bucket_min_width;
    result.tailored_bc_s_bucket_refine_top_k =
        options.tailored_bc_s_bucket_refine_top_k;
    result.tailored_bc_s_bucket_refine_rule =
        options.tailored_bc_s_bucket_refine_rule;
    result.compact_bc_variable_s_centering =
        options.compact_bc_variable_s_centering;
    result.compact_bc_rmin_rmax_propagation =
        options.compact_bc_rmin_rmax_propagation;
    result.compact_bc_rmin_rmax_propagation_safe =
        options.compact_bc_rmin_rmax_propagation == "safe";
    result.compact_bc_sp_product_estimator =
        options.compact_bc_sp_product_estimator;
    result.compact_bc_sp_product_bounds =
        options.compact_bc_sp_product_bounds;
    result.compact_bc_sp_product_paper_safe =
        options.compact_bc_sp_product_estimator == "paper-safe";
    result.compact_bc_low_gini_precheck =
        options.compact_bc_low_gini_precheck;
    populateTailoredBCResultFields(options, result);
    result.compact_bc_expensive_static_families =
        options.compact_bc_expensive_static_families;
    result.compact_bc_use_dynamic_instead_of_static =
        options.compact_bc_use_dynamic_instead_of_static;
    result.time_budget_seconds = options.solve_time_limit;
    std::string oracle_mode = options.interval_exact_oracle_mode;
    std::transform(oracle_mode.begin(), oracle_mode.end(), oracle_mode.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (oracle_mode != "objective-bound" &&
        oracle_mode != "cutoff-feasibility" &&
        oracle_mode != "both") {
        oracle_mode = "cutoff-feasibility";
    }
    const bool objective_bound_mode =
        oracle_mode == "objective-bound" || oracle_mode == "both";
    const bool add_objective_cutoff =
        !objective_bound_mode || options.interval_oracle_objective_cutoff_row;
    result.interval_oracle_model_type = objective_bound_mode
        ? "original_compact_objective_bound"
        : "original_compact_cutoff_feasibility";
    result.interval_oracle_bound_scope = "original_fixed_interval";
    result.interval_oracle_objective_sense = "minimize";
    result.interval_oracle_has_objective_cutoff_row = add_objective_cutoff;
    result.interval_oracle_has_gamma_interval_rows = true;
    result.compact_interval_bc_model_type = result.interval_oracle_model_type;
    result.compact_bc_bound_scope = "original_fixed_interval";
    result.compact_interval_bc_bound_scope = "original_fixed_interval";
    result.interval_exact_cutoff_scope = objective_bound_mode
        ? "original fixed-interval objective-bound compact MIP"
        : "original fixed-interval cutoff feasibility compact MIP";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Interval oracle is local to one Gini interval. It never certifies the full original problem unless merged into a complete full-frontier ledger.");

    const bool params_valid =
        options.interval_exact_cutoff_oracle == "compact-mip" &&
        std::isfinite(options.interval_exact_cutoff_gamma_L) &&
        std::isfinite(options.interval_exact_cutoff_gamma_U) &&
        options.interval_exact_cutoff_gamma_L >= -1e-12 &&
        options.interval_exact_cutoff_gamma_U >= options.interval_exact_cutoff_gamma_L - 1e-12 &&
        std::isfinite(options.interval_exact_cutoff_UB) &&
        options.interval_exact_cutoff_UB > 0.0;
    if (!params_valid) {
        result.status = "error";
        result.certificate = "interval cutoff oracle requires --interval-exact-cutoff-oracle compact-mip, valid gamma bounds, and positive --interval-exact-cutoff-UB";
        result.interval_exact_cutoff_certificate_basis = "interval_exact_cutoff_mip_invalid_parameters";
        result.interval_oracle_model_type = "diagnostic_unknown";
        result.interval_oracle_bound_scope = "diagnostic";
        result.compact_interval_bc_model_type = "diagnostic_unknown";
        result.compact_interval_bc_bound_scope = "diagnostic";
        result.compact_interval_bc_rejection_reason = result.certificate;
        result.compact_bc_rejection_reason = result.certificate;
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        return result;
    }

    try {
        const std::string stem = std::filesystem::path(instance.name).stem().string()
            + "_interval_cutoff_"
            + std::to_string(static_cast<long long>(std::llround(options.interval_exact_cutoff_gamma_L * 1000000000.0)))
            + "_"
            + std::to_string(static_cast<long long>(std::llround(options.interval_exact_cutoff_gamma_U * 1000000000.0)));
        const auto run_id = std::chrono::duration_cast<std::chrono::milliseconds>(
            Clock::now().time_since_epoch()).count();
        const std::filesystem::path default_dir = std::filesystem::path("results") / "interval_cutoff_work"
            / (stem + "_" + std::to_string(run_id));
        std::filesystem::create_directories(default_dir);
        const std::filesystem::path lp_path = options.interval_exact_cutoff_export_lp.empty()
            ? (default_dir / "interval_cutoff.lp")
            : std::filesystem::path(options.interval_exact_cutoff_export_lp);
        const std::filesystem::path sol_path = options.interval_exact_cutoff_result.empty()
            ? (default_dir / "interval_cutoff.sol")
            : std::filesystem::path(options.interval_exact_cutoff_result);
        const std::filesystem::path cmd_path = default_dir / "run_interval_cutoff.cplex";
        const std::filesystem::path cplex_log = options.log_path.empty()
            ? (default_dir / "interval_cutoff.cplex.log") : std::filesystem::path(options.log_path);
        result.log_file = cplex_log.string();
        result.interval_exact_cutoff_lp_path = lp_path.string();
        result.interval_exact_cutoff_solution_path = sol_path.string();
        result.interval_exact_cutoff_log_path = cplex_log.string();

        std::filesystem::create_directories(lp_path.parent_path());
        std::filesystem::create_directories(sol_path.parent_path());
        std::filesystem::create_directories(cplex_log.parent_path());
        std::error_code ignored;
        std::filesystem::remove(sol_path, ignored);
        std::filesystem::remove(cplex_log, ignored);

        CompactIntervalCutoffConfig cutoff;
        cutoff.enabled = true;
        cutoff.gamma_L = options.interval_exact_cutoff_gamma_L;
        cutoff.gamma_U = options.interval_exact_cutoff_gamma_U;
        cutoff.add_objective_cutoff = add_objective_cutoff;
        cutoff.incumbent_ub = options.interval_exact_cutoff_UB;
        cutoff.epsilon = options.interval_exact_cutoff_epsilon;
        if (objective_bound_mode && !add_objective_cutoff) {
            result.notes.push_back(
                "interval oracle objective-bound mode omits the objective cutoff row; finite CPLEX dual bounds are valid original fixed-interval lower bounds");
        } else if (objective_bound_mode && add_objective_cutoff) {
            result.notes.push_back(
                "interval oracle objective-bound mode includes the incumbent objective cutoff row; finite CPLEX dual bounds are merged as valid no-improver lower bounds with the cutoff disjunction");
        } else if (!options.interval_oracle_objective_cutoff_row) {
            result.notes.push_back(
                "interval_oracle_objective_cutoff_row=false requested; exact cutoff oracle keeps the original cutoff row because it is required for a valid interval certificate");
        }
        double time_limit = options.interval_exact_cutoff_time_limit;
        if (objective_bound_mode && options.interval_oracle_objective_bound_time_limit > 0.0) {
            time_limit = options.interval_oracle_objective_bound_time_limit;
        } else if (!objective_bound_mode &&
                   options.interval_oracle_cutoff_feasibility_time_limit > 0.0) {
            time_limit = options.interval_oracle_cutoff_feasibility_time_limit;
        }
        if (options.compact_bc_time_limit > 0.0) {
            time_limit = options.compact_bc_time_limit;
        }
        if (time_limit <= 0.0) time_limit = std::max(1.0, options.solve_time_limit);
        SolveOptions model_options =
            applyResourceAdaptiveCompactOptions(instance, options, result);
        // Round 19 keeps standalone fixed-interval and global-tree child
        // formulations on the same deterministic interval-row path.
        model_options.interval_row_factory_round19 = true;
        result.compact_bc_root_cut_rounds = model_options.compact_bc_root_cut_rounds;
        result.compact_bc_root_cut_time_limit = model_options.compact_bc_root_cut_time_limit;
        result.compact_bc_dynamic_cut_families = model_options.compact_bc_dynamic_cut_families;
        result.compact_bc_root_probe = model_options.compact_bc_root_probe;
        result.compact_bc_domain_propagation_mode =
            model_options.compact_bc_domain_propagation_mode;
        result.compact_bc_domain_propagation_rounds =
            model_options.compact_bc_domain_propagation_rounds;
        result.compact_bc_low_gini_strengthening =
            model_options.compact_bc_low_gini_strengthening;
        result.compact_bc_denominator_bound_mode =
            model_options.compact_bc_denominator_bound_mode;
        result.compact_bc_objective_estimator_mode =
            model_options.compact_bc_objective_estimator_mode;
        result.compact_bc_low_gini_aggressive_diagnostic =
            model_options.compact_bc_low_gini_strengthening == "aggressive-diagnostic";
        result.compact_bc_s_range_refinement =
            model_options.compact_bc_s_range_refinement;
        result.s_range_bucket_count = model_options.compact_bc_s_range_buckets;
        result.s_range_bucket_id = model_options.compact_bc_s_range_bucket_id;
        result.s_range_bucket_L = model_options.compact_bc_s_range_bucket_L;
        result.s_range_bucket_U = model_options.compact_bc_s_range_bucket_U;
        result.tailored_bc_s_bucket_ledger =
            model_options.tailored_bc_s_bucket_ledger;
        result.tailored_bc_s_bucket_count =
            std::max(1, model_options.tailored_bc_s_bucket_count);
        result.tailored_bc_s_bucket_policy =
            model_options.tailored_bc_s_bucket_policy;
        result.tailored_bc_s_bucket_time_budget =
            model_options.tailored_bc_s_bucket_time_budget;
        result.tailored_bc_s_bucket_merge_audit =
            model_options.tailored_bc_s_bucket_merge_audit;
        result.tailored_bc_s_bucket_max_depth =
            model_options.tailored_bc_s_bucket_max_depth;
        result.tailored_bc_s_bucket_min_width =
            model_options.tailored_bc_s_bucket_min_width;
        result.tailored_bc_s_bucket_refine_top_k =
            model_options.tailored_bc_s_bucket_refine_top_k;
        result.tailored_bc_s_bucket_refine_rule =
            model_options.tailored_bc_s_bucket_refine_rule;
        result.compact_bc_variable_s_centering =
            model_options.compact_bc_variable_s_centering;
        result.compact_bc_rmin_rmax_propagation =
            model_options.compact_bc_rmin_rmax_propagation;
        result.compact_bc_rmin_rmax_propagation_safe =
            model_options.compact_bc_rmin_rmax_propagation == "safe";
        result.compact_bc_sp_product_estimator =
            model_options.compact_bc_sp_product_estimator;
        result.compact_bc_sp_product_bounds =
            model_options.compact_bc_sp_product_bounds;
        result.compact_bc_sp_product_paper_safe =
            model_options.compact_bc_sp_product_estimator == "paper-safe";
        result.compact_bc_low_gini_precheck =
            model_options.compact_bc_low_gini_precheck;
        populateTailoredBCResultFields(model_options, result);
        result.compact_bc_expensive_static_families =
            model_options.compact_bc_expensive_static_families;
        result.compact_bc_use_dynamic_instead_of_static =
            model_options.compact_bc_use_dynamic_instead_of_static;
        std::vector<DynamicCut> dynamic_cuts;
        std::set<std::string> dynamic_signatures;
        DynamicCutStats dynamic_stats;
        if (model_options.compact_bc_root_cut_rounds > 0) {
            for (int round = 0; round < model_options.compact_bc_root_cut_rounds; ++round) {
                const std::filesystem::path root_lp =
                    default_dir / ("root_round_" + std::to_string(round + 1) + ".lp");
                const std::filesystem::path root_sol =
                    default_dir / ("root_round_" + std::to_string(round + 1) + ".sol");
                const std::filesystem::path root_log =
                    default_dir / ("root_round_" + std::to_string(round + 1) + ".log");
                CompactOracleStrengtheningStats probe_stats;
                writeCompactLp(instance, model_options, root_lp, true, &cutoff,
                               &probe_stats, &dynamic_cuts);
                std::string root_status = "unknown";
                double root_obj = std::numeric_limits<double>::quiet_NaN();
                double root_bound = std::numeric_limits<double>::quiet_NaN();
                const double root_time =
                    model_options.compact_bc_root_cut_time_limit > 0.0
                        ? model_options.compact_bc_root_cut_time_limit
                        : std::min(30.0, std::max(1.0, time_limit * 0.10));
                auto root_values = solveRootRelaxation(
                    model_options, root_lp, root_sol, root_log, root_time,
                    effective_compact_threads, root_status, root_obj, root_bound);
                result.notes.push_back("compact BC root cut round "
                    + std::to_string(round + 1)
                    + " status=" + root_status
                    + " objective=" + (std::isfinite(root_obj) ? num(root_obj) : "nan"));
                if (root_values.empty()) break;
                DynamicCutStats before = dynamic_stats;
                std::vector<DynamicCut> added = separateDynamicCuts(
                    instance, model_options, cutoff, root_values,
                    dynamic_signatures, dynamic_stats);
                ++dynamic_stats.rounds_completed;
                result.notes.push_back("compact BC root cut round "
                    + std::to_string(round + 1)
                    + " added_dynamic_cuts=" + std::to_string(dynamic_stats.total - before.total));
                if (added.empty()) break;
            }
        }

        CompactOracleStrengtheningStats strengthening_stats;
        writeCompactLp(instance, model_options, lp_path, true, &cutoff,
                       &strengthening_stats, &dynamic_cuts);
        const ModelSizeStats model_size = analyzeLpModel(lp_path);
        result.compact_bc_model_rows = model_size.rows;
        result.compact_bc_model_cols = model_size.cols;
        result.compact_bc_model_nonzeros = model_size.nonzeros;
        if (model_size.memory_mb > 0.0) {
            result.compact_bc_memory_estimate_mb = model_size.memory_mb;
        }
        result.compact_bc_dynamic_cuts_added_by_family =
            dynamicCutSummary(dynamic_stats);
        result.compact_bc_dynamic_max_violation_by_family =
            dynamicViolationSummary(dynamic_stats);
        result.compact_bc_dynamic_cuts_added_total = dynamic_stats.total;
        result.compact_bc_total_root_cut_rounds = dynamic_stats.rounds_completed;
        result.compact_bc_dynamic_cut_violation_tol =
            model_options.compact_bc_dynamic_cut_violation_tol;
        result.compact_bc_model_size_policy = model_options.compact_bc_model_size_policy;
        result.compact_bc_domain_propagation_rounds_completed =
            model_options.compact_bc_domain_propagation_mode == "off"
                ? 0
                : std::min(1, std::max(1, model_options.compact_bc_domain_propagation_rounds));
        if (model_options.compact_bc_model_size_policy != "full" &&
            result.compact_bc_disabled_families_due_to_size != "none") {
            result.notes.push_back("resource-adaptive compact BC disabled families: "
                + result.compact_bc_disabled_families_due_to_size);
        }
        if (options.interval_oracle_penalty_domain_tightening ||
            options.interval_oracle_low_gini_tightening) {
            result.notes.push_back(
                "interval oracle added safe penalty-budget e_i upper bounds derived from G>=gamma_L and G+lambda*P<=UB-epsilon");
        }
        result.gini_spread_cuts_added = strengthening_stats.gini_spread_cuts_added;
        result.compact_bc_direct_gini_cap_rows_added =
            strengthening_stats.direct_gini_cap_rows_added;
        result.compact_bc_direct_gini_floor_rows_added =
            strengthening_stats.direct_gini_floor_rows_added;
        result.compact_bc_tight_mccormick_rows_added =
            strengthening_stats.tight_mccormick_rows_added;
        result.compact_bc_inventory_conservation_rows_added =
            strengthening_stats.inventory_conservation_rows_added;
        result.compact_bc_movement_reachability_domains_tightened =
            strengthening_stats.movement_reachability_domains_tightened;
        result.compact_bc_visit_inventory_linking_rows_added =
            strengthening_stats.visit_inventory_linking_rows_added;
        result.compact_bc_objective_estimator_cutoff_rows_added =
            strengthening_stats.objective_estimator_cutoff_rows_added;
        result.compact_bc_penalty_lb = strengthening_stats.penalty_lb;
        result.compact_bc_penalty_lb_rows_added =
            strengthening_stats.penalty_lb_rows_added;
        result.compact_bc_low_gini_centering_rows_added =
            strengthening_stats.low_gini_centering_rows_added;
        result.compact_bc_variable_s_centering_rows_added =
            strengthening_stats.variable_s_centering_rows_added;
        result.s_range_refinement_enabled =
            strengthening_stats.s_range_refinement_enabled;
        result.s_range_global_L = strengthening_stats.s_range_global_L;
        result.s_range_global_U = strengthening_stats.s_range_global_U;
        result.parent_S_L = strengthening_stats.s_range_global_L;
        result.parent_S_U = strengthening_stats.s_range_global_U;
        result.S_domain_source =
            "Y_bounds_target_ratios_capacity_penalty_movement_domains";
        result.S_domain_proof_status =
            (strengthening_stats.s_range_global_U >=
             strengthening_stats.s_range_global_L - 1e-12)
                ? "valid_interval_from_model_domain_bounds"
                : "invalid_empty_or_reversed_domain";
        result.S_domain_audit_passed =
            strengthening_stats.s_range_global_U >=
            strengthening_stats.s_range_global_L - 1e-12;
        result.s_range_bucket_count = strengthening_stats.s_range_bucket_count;
        result.s_range_bucket_id = strengthening_stats.s_range_bucket_id;
        result.s_range_bucket_L = strengthening_stats.s_range_bucket_L;
        result.s_range_bucket_U = strengthening_stats.s_range_bucket_U;
        result.s_range_parent_coverage_valid =
            strengthening_stats.s_range_parent_coverage_valid;
        result.s_range_certificate_valid =
            strengthening_stats.s_range_certificate_valid;
        result.compact_bc_s_range_rows_added =
            strengthening_stats.s_range_rows_added;
        result.compact_bc_sp_product_mccormick_rows_added =
            strengthening_stats.sp_product_mccormick_rows_added;
        result.compact_bc_sp_product_estimator_rows_added =
            strengthening_stats.sp_product_estimator_rows_added;
        result.tailored_bc_gini_subset_envelope_candidates =
            strengthening_stats.tailored_gini_subset_envelope_candidates;
        result.tailored_bc_gini_subset_envelope_cuts_added =
            strengthening_stats.tailored_gini_subset_envelope_cuts_added;
        result.tailored_bc_user_cuts_added_total =
            strengthening_stats.tailored_gini_subset_envelope_cuts_added +
            strengthening_stats.tailored_low_gini_l1_rows_added +
            strengthening_stats.tailored_local_centering_rows_added +
            strengthening_stats.tailored_subset_cross_h_centering_rows_added +
            strengthening_stats.tailored_local_q_centering_rows_added +
            strengthening_stats.tailored_subset_inventory_imbalance_cuts_added +
            strengthening_stats.bucket_integer_inventory_rows_added +
            strengthening_stats.bucket_required_movement_rows_added +
            strengthening_stats.bucket_required_visit_rows_added +
            strengthening_stats.bucket_subset_required_movement_rows_added +
            strengthening_stats.tailored_transfer_cutset_cuts_added +
            strengthening_stats.tailored_compatible_source_transfer_cuts_added +
            strengthening_stats.tailored_required_external_source_cuts_added +
            strengthening_stats.tailored_benders_inventory_cuts_added +
            strengthening_stats.gs_mccormick_rows_added +
            strengthening_stats.gs_h_upper_rows_added +
            strengthening_stats.gs_h_lower_rows_added +
            strengthening_stats.disagg_sp_mccormick_rows_added +
            strengthening_stats.disagg_sp_estimator_rows_added +
            strengthening_stats.vector_support_cover_cuts_added +
            strengthening_stats.vector_route_cutset_cuts_added;
        result.tailored_bc_low_gini_l1_centering_vars =
            strengthening_stats.tailored_low_gini_l1_vars;
        result.tailored_bc_low_gini_l1_centering_rows_added =
            strengthening_stats.tailored_low_gini_l1_rows_added;
        result.tailored_bc_local_centering_rows_added =
            strengthening_stats.tailored_local_centering_rows_added;
        result.tailored_bc_subset_cross_h_centering_rows_added =
            strengthening_stats.tailored_subset_cross_h_centering_rows_added;
        result.tailored_bc_subset_cross_h_centering_candidates =
            strengthening_stats.tailored_subset_cross_h_centering_candidates;
        result.tailored_bc_local_q_centering_rows_added =
            strengthening_stats.tailored_local_q_centering_rows_added;
        result.tailored_bc_subset_inventory_imbalance_cuts_added =
            strengthening_stats.tailored_subset_inventory_imbalance_cuts_added;
        result.tailored_bc_bucket_ratio_domain_rows_added =
            strengthening_stats.tailored_bucket_ratio_domain_rows_added;
        result.tailored_bc_bucket_ratio_domain_bounds_tightened =
            strengthening_stats.tailored_bucket_ratio_domain_bounds_tightened;
        result.tailored_bc_bucket_ratio_domain_proof_status =
            result.tailored_bc_bucket_ratio_domain_rows_added > 0 ||
            result.tailored_bc_bucket_ratio_domain_bounds_tightened > 0
                ? "paper_safe_s_bucket_ratio_domain"
                : "not_enabled";
        result.tailored_bc_bucket_subset_ratio_domain_cuts_added =
            strengthening_stats.tailored_bucket_subset_ratio_domain_cuts_added;
        result.tailored_bc_bucket_subset_ratio_domain_candidates =
            strengthening_stats.tailored_bucket_subset_ratio_domain_candidates;
        result.tailored_bc_bucket_subset_ratio_domain_max_size =
            model_options.tailored_bc_bucket_subset_ratio_max_size;
        result.tailored_bc_bucket_h_cap_rows_added =
            strengthening_stats.tailored_bucket_h_cap_rows_added;
        result.bucket_integer_inventory_bounds_tightened =
            strengthening_stats.bucket_integer_inventory_bounds_tightened;
        result.bucket_integer_inventory_rows_added =
            strengthening_stats.bucket_integer_inventory_rows_added;
        result.bucket_integer_inventory_lower_bounds_tightened =
            strengthening_stats.bucket_integer_inventory_lower_bounds_tightened;
        result.bucket_integer_inventory_upper_bounds_tightened =
            strengthening_stats.bucket_integer_inventory_upper_bounds_tightened;
        result.bucket_integer_inventory_domain_mode =
            model_options.tailored_bc_bucket_integer_inventory_domain
                ? model_options.tailored_bc_bucket_integer_inventory_domain_mode
                : "off";
        result.bucket_integer_inventory_domain_proof_status =
            result.bucket_integer_inventory_bounds_tightened > 0 ||
            result.bucket_integer_inventory_rows_added > 0
                ? "paper_safe_s_bucket_integer_inventory_domain"
                : "not_enabled";
        result.bucket_required_movement_rows_added =
            strengthening_stats.bucket_required_movement_rows_added;
        result.bucket_required_visit_rows_added =
            strengthening_stats.bucket_required_visit_rows_added;
        result.bucket_subset_required_movement_rows_added =
            strengthening_stats.bucket_subset_required_movement_rows_added;
        result.bucket_required_movement_violations =
            strengthening_stats.bucket_required_movement_violations;
        result.bucket_required_movement_max_violation =
            strengthening_stats.bucket_required_movement_max_violation;
        result.bucket_required_movement_max_size =
            model_options.tailored_bc_bucket_required_movement_max_size;
        result.bucket_required_movement_proof_status =
            result.bucket_required_movement_rows_added > 0 ||
            result.bucket_required_visit_rows_added > 0 ||
            result.bucket_subset_required_movement_rows_added > 0
                ? "paper_safe_bucket_integer_inventory_required_movement"
                : "not_enabled";
        result.tailored_bc_transfer_cutset_cuts_added =
            strengthening_stats.tailored_transfer_cutset_cuts_added;
        result.tailored_bc_compatible_source_transfer_cuts_added =
            strengthening_stats.tailored_compatible_source_transfer_cuts_added;
        result.tailored_bc_compatible_source_transfer_candidates =
            strengthening_stats.tailored_compatible_source_transfer_candidates;
        result.tailored_bc_required_external_source_cuts_added =
            strengthening_stats.tailored_required_external_source_cuts_added;
        result.tailored_bc_benders_inventory_cuts_mode =
            options.tailored_bc_benders_inventory_cuts;
        result.tailored_bc_benders_inventory_cuts_added =
            strengthening_stats.tailored_benders_inventory_cuts_added;
        result.tailored_bc_benders_inventory_candidates =
            strengthening_stats.tailored_benders_inventory_candidates;
        result.tailored_bc_gs_product_coupling_enabled =
            model_options.tailored_bc_gs_product_coupling;
        result.tailored_bc_gs_product_coupling_mode =
            model_options.tailored_bc_gs_product_coupling_mode;
        result.tailored_bc_gs_product_lower_row =
            model_options.tailored_bc_gs_product_lower_row;
        result.gs_product_variable_added =
            strengthening_stats.gs_product_variable_added;
        result.gs_mccormick_rows_added =
            strengthening_stats.gs_mccormick_rows_added;
        result.gs_h_upper_rows_added =
            strengthening_stats.gs_h_upper_rows_added;
        result.gs_h_lower_rows_added =
            strengthening_stats.gs_h_lower_rows_added;
        result.gs_product_coupling_proof_status =
            result.gs_h_upper_rows_added > 0
                ? (model_options.tailored_bc_gs_product_lower_row == "paper-safe"
                       ? "upper_and_lower_rows_paper_safe"
                       : "upper_row_paper_safe_lower_row_" +
                             model_options.tailored_bc_gs_product_lower_row)
                : (result.gs_mccormick_rows_added > 0
                       ? "paper_safe_product_definition_callback_separation"
                       : "not_enabled");
        result.tailored_bc_disaggregated_sp_estimator_enabled =
            model_options.tailored_bc_disaggregated_sp_estimator;
        result.tailored_bc_disaggregated_sp_mode =
            model_options.tailored_bc_disaggregated_sp_mode;
        result.tailored_bc_disaggregated_sp_replace_aggregate =
            model_options.tailored_bc_disaggregated_sp_replace_aggregate;
        result.disagg_sp_variables_added =
            strengthening_stats.disagg_sp_variables_added;
        result.disagg_sp_mccormick_rows_added =
            strengthening_stats.disagg_sp_mccormick_rows_added;
        result.disagg_sp_estimator_rows_added =
            strengthening_stats.disagg_sp_estimator_rows_added;
        result.disagg_sp_proof_status =
            result.disagg_sp_estimator_rows_added > 0
                ? "paper_safe_bucket_local_disaggregated_sp_estimator"
                : (result.disagg_sp_mccormick_rows_added > 0
                       ? "paper_safe_product_definition_callback_separation"
                       : "not_enabled");
        result.tailored_bc_vector_support_cover_enabled =
            model_options.tailored_bc_vector_support_cover;
        result.tailored_bc_vector_support_cover_max_size =
            model_options.tailored_bc_vector_support_cover_max_size;
        result.tailored_bc_vector_support_cover_max_cuts =
            model_options.tailored_bc_vector_support_cover_max_cuts;
        result.tailored_bc_vector_route_cutset_enabled =
            model_options.tailored_bc_vector_route_cutset;
        result.tailored_bc_vector_route_cutset_max_size =
            model_options.tailored_bc_vector_route_cutset_max_size;
        result.tailored_bc_vector_route_cutset_max_cuts =
            model_options.tailored_bc_vector_route_cutset_max_cuts;
        result.tailored_bc_vector_cut_min_violation =
            model_options.tailored_bc_vector_cut_min_violation;
        result.tailored_bc_vector_cut_candidate_source =
            model_options.tailored_bc_vector_cut_candidate_source;
        result.tailored_bc_structural_profile =
            model_options.tailored_bc_structural_profile;
        result.vector_support_cover_candidates =
            strengthening_stats.vector_support_cover_candidates;
        result.vector_support_cover_cuts_added =
            strengthening_stats.vector_support_cover_cuts_added;
        result.vector_support_cover_max_violation =
            strengthening_stats.vector_support_cover_max_violation;
        result.vector_route_cutset_candidates =
            strengthening_stats.vector_route_cutset_candidates;
        result.vector_route_cutset_cuts_added =
            strengthening_stats.vector_route_cutset_cuts_added;
        result.vector_route_cutset_max_violation =
            strengthening_stats.vector_route_cutset_max_violation;
        result.vector_route_cuts_proof_status =
            (result.vector_support_cover_cuts_added > 0 ||
             result.vector_route_cutset_cuts_added > 0)
                ? "paper_safe_universal_rows_vector_selected_candidates"
                : "not_enabled";
        {
            std::ostringstream tbc;
            tbc << "gini_subset_envelope="
                << result.tailored_bc_gini_subset_envelope_cuts_added
                << ";low_gini_l1_centering="
                << result.tailored_bc_low_gini_l1_centering_rows_added
                << ";local_centering="
                << result.tailored_bc_local_centering_rows_added
                << ";subset_cross_h_centering="
                << result.tailored_bc_subset_cross_h_centering_rows_added
                << ";local_q_centering="
                << result.tailored_bc_local_q_centering_rows_added
                << ";subset_inventory_imbalance="
                << result.tailored_bc_subset_inventory_imbalance_cuts_added
                << ";bucket_ratio_domain="
                << result.tailored_bc_bucket_ratio_domain_rows_added
                << ";bucket_subset_ratio_domain="
                << result.tailored_bc_bucket_subset_ratio_domain_cuts_added
                << ";bucket_h_cap="
                << result.tailored_bc_bucket_h_cap_rows_added
                << ";bucket_integer_inventory="
                << result.bucket_integer_inventory_rows_added
                << ";bucket_required_movement="
                << result.bucket_required_movement_rows_added
                << ";bucket_required_visit="
                << result.bucket_required_visit_rows_added
                << ";bucket_subset_required_movement="
                << result.bucket_subset_required_movement_rows_added
                << ";transfer_cutset="
                << result.tailored_bc_transfer_cutset_cuts_added
                << ";compatible_source_transfer="
                << result.tailored_bc_compatible_source_transfer_cuts_added
                << ";required_external_source="
                << result.tailored_bc_required_external_source_cuts_added
                << ";benders_inventory_diagnostic="
                << result.tailored_bc_benders_inventory_cuts_added
                << ";gs_product_coupling="
                << (result.gs_mccormick_rows_added +
                    result.gs_h_upper_rows_added +
                    result.gs_h_lower_rows_added)
                << ";disaggregated_sp_estimator="
                << (result.disagg_sp_mccormick_rows_added +
                    result.disagg_sp_estimator_rows_added)
                << ";vector_support_cover="
                << result.vector_support_cover_cuts_added
                << ";vector_route_cutset="
                << result.vector_route_cutset_cuts_added;
            result.tailored_bc_user_cuts_added_by_family = tbc.str();
        }
        result.compact_bc_support_duration_pair_cuts_added =
            strengthening_stats.support_duration_pair_cuts_added;
        result.compact_bc_support_duration_triple_cuts_added =
            strengthening_stats.support_duration_triple_cuts_added;
        result.compact_bc_pairwise_transfer_compatibility_cuts_added =
            strengthening_stats.pairwise_transfer_compatibility_cuts_added;
        result.compact_bc_receiver_source_cover_cuts_added =
            strengthening_stats.receiver_source_cover_cuts_added;
        result.required_movement_lb = strengthening_stats.required_movement_lb;
        result.required_movement_cuts_added = strengthening_stats.required_movement_cuts_added;
        result.global_handling_capacity_lb = strengthening_stats.global_handling_capacity_lb;
        result.global_handling_capacity_cuts_added = strengthening_stats.global_handling_capacity_cuts_added;
        result.transfer_subset_capacity_cuts_enabled = options.transfer_subset_capacity_cuts;
        result.transfer_subset_capacity_cuts_added =
            strengthening_stats.transfer_subset_capacity_cuts_added;
        result.low_gini_ratio_band_domains_tightened =
            strengthening_stats.low_gini_ratio_band_domains_tightened;
        result.oracle_strengthening_families_enabled =
            joinFamilies(strengthening_stats.enabled_families);
        if (dynamic_stats.total > 0) {
            result.oracle_strengthening_families_enabled +=
                (result.oracle_strengthening_families_enabled.empty() ||
                 result.oracle_strengthening_families_enabled == "none")
                    ? "dynamic_root"
                    : "|dynamic_root";
        }
        result.compact_interval_bc_cut_families_enabled =
            result.oracle_strengthening_families_enabled;
        result.compact_bc_enabled_cut_families =
            result.oracle_strengthening_families_enabled;
        result.compact_bc_enabled_families_requested =
            result.oracle_strengthening_families_enabled;
        result.compact_bc_enabled_families_effective =
            result.oracle_strengthening_families_enabled;
        {
            std::ostringstream cuts;
            cuts << "direct_gini_cap=" << result.compact_bc_direct_gini_cap_rows_added
                 << ";direct_gini_floor=" << result.compact_bc_direct_gini_floor_rows_added
                 << ";tight_mccormick=" << result.compact_bc_tight_mccormick_rows_added
                 << ";inventory_conservation=" << result.compact_bc_inventory_conservation_rows_added
                 << ";visit_inventory_linking=" << result.compact_bc_visit_inventory_linking_rows_added
                 << ";objective_estimator_cutoff=" << result.compact_bc_objective_estimator_cutoff_rows_added
                 << ";penalty_lb=" << result.compact_bc_penalty_lb_rows_added
                 << ";variable_s_centering=" << result.compact_bc_variable_s_centering_rows_added
                 << ";s_range=" << result.compact_bc_s_range_rows_added
                 << ";sp_product_mccormick=" << result.compact_bc_sp_product_mccormick_rows_added
                 << ";sp_product_estimator=" << result.compact_bc_sp_product_estimator_rows_added
                 << ";tailored_gini_subset_envelope=" << result.tailored_bc_gini_subset_envelope_cuts_added
                 << ";tailored_low_gini_l1_centering=" << result.tailored_bc_low_gini_l1_centering_rows_added
                 << ";tailored_subset_inventory_imbalance=" << result.tailored_bc_subset_inventory_imbalance_cuts_added
                 << ";tailored_bucket_ratio_domain=" << result.tailored_bc_bucket_ratio_domain_rows_added
                 << ";tailored_bucket_subset_ratio_domain=" << result.tailored_bc_bucket_subset_ratio_domain_cuts_added
                 << ";tailored_bucket_h_cap=" << result.tailored_bc_bucket_h_cap_rows_added
                 << ";bucket_integer_inventory=" << result.bucket_integer_inventory_rows_added
                 << ";bucket_required_movement=" << result.bucket_required_movement_rows_added
                 << ";bucket_required_visit=" << result.bucket_required_visit_rows_added
                 << ";bucket_subset_required_movement=" << result.bucket_subset_required_movement_rows_added
                 << ";tailored_transfer_cutset=" << result.tailored_bc_transfer_cutset_cuts_added
                 << ";tailored_benders_inventory_diagnostic=" << result.tailored_bc_benders_inventory_cuts_added
                 << ";gs_product_coupling=" << (result.gs_mccormick_rows_added + result.gs_h_upper_rows_added + result.gs_h_lower_rows_added)
                 << ";disaggregated_sp_estimator=" << (result.disagg_sp_mccormick_rows_added + result.disagg_sp_estimator_rows_added)
                 << ";vector_support_cover=" << result.vector_support_cover_cuts_added
                 << ";vector_route_cutset=" << result.vector_route_cutset_cuts_added
                 << ";gini_spread=" << result.gini_spread_cuts_added
                 << ";required_movement=" << result.required_movement_cuts_added
                 << ";global_handling_capacity=" << result.global_handling_capacity_cuts_added
                 << ";support_duration_pair=" << result.compact_bc_support_duration_pair_cuts_added
                 << ";support_duration_triple=" << result.compact_bc_support_duration_triple_cuts_added
                 << ";transfer_compat=" << result.compact_bc_pairwise_transfer_compatibility_cuts_added
                 << ";receiver_source_cover=" << result.compact_bc_receiver_source_cover_cuts_added
                 << ";dynamic_root_total=" << dynamic_stats.total;
        result.compact_bc_cuts_added_by_family = cuts.str();
        result.compact_bc_total_cuts_added_by_family =
            result.compact_bc_cuts_added_by_family;
        }
        {
            std::ostringstream domains;
            domains << "penalty_domains=" << strengthening_stats.penalty_domains_tightened
                    << ";movement_reachability="
                    << result.compact_bc_movement_reachability_domains_tightened
                    << ";bucket_ratio_domain="
                    << result.tailored_bc_bucket_ratio_domain_bounds_tightened
                    << ";bucket_integer_inventory="
                    << result.bucket_integer_inventory_bounds_tightened
                    << ";domain_width_before=" << strengthening_stats.domain_width_before
                    << ";domain_width_after=" << strengthening_stats.domain_width_after;
        result.compact_bc_domains_tightened_by_family = domains.str();
        result.compact_bc_total_domains_tightened_by_family =
            result.compact_bc_domains_tightened_by_family;
        }
        if (strengthening_stats.domain_width_before > 0) {
            result.total_domain_width_before = strengthening_stats.domain_width_before;
            result.total_domain_width_after = strengthening_stats.domain_width_after;
            result.domains_tightened_count =
                static_cast<int>(strengthening_stats.penalty_domains_tightened);
        }

        std::string cplex_status = "unknown";
        double cplex_obj = std::numeric_limits<double>::quiet_NaN();
        double best_bound = std::numeric_limits<double>::quiet_NaN();
        std::unordered_map<std::string, double> values;
        int rc = 0;
        bool used_callback_api = false;
        TailoredBCCplexApiSolveResult api_solve;
        const bool static_native_api =
            result.tailored_bc_enabled &&
            result.tailored_bc_mode == "static_fallback";
        if (result.tailored_bc_enabled &&
            result.tailored_bc_callback_available &&
            (result.tailored_bc_mode == "callback" || static_native_api)) {
            std::vector<double> callback_dist;
            callback_dist.reserve(static_cast<std::size_t>((instance.V + 1) * (instance.V + 1)));
            for (int i = 0; i <= instance.V; ++i) {
                for (int j = 0; j <= instance.V; ++j) {
                    callback_dist.push_back(instance.dist[i][j]);
                }
            }
            TailoredBCNativeCheckpointConfig native_checkpoint;
            native_checkpoint.enabled = !static_native_api &&
                !options.progress_log_path.empty();
            if (native_checkpoint.enabled) {
                native_checkpoint.path =
                    std::filesystem::path(options.progress_log_path).string() +
                    ".native_checkpoint.json";
                native_checkpoint.run_id = lp_path.stem().string();
                native_checkpoint.instance_hash =
                    stableFileFingerprint(instance.path);
                native_checkpoint.model_fingerprint =
                    stableFileFingerprint(lp_path);
                native_checkpoint.formulation_profile =
                    "callback_managed_original_fixed_interval_compact_mip";
            }
            api_solve = solveLpWithTailoredBCCplexApi(
                lp_path,
                time_limit,
                std::max(1, effective_compact_threads),
                cutoff.gamma_L,
                cutoff.gamma_U,
                !static_native_api,
                !static_native_api &&
                    (result.tailored_bc_lazy_callback_enabled ||
                     result.tailored_bc_incumbent_callback_enabled),
                !static_native_api && result.tailored_bc_branch_callback_enabled &&
                    (result.tailored_bc_gini_branch_mode == "branch_callback" ||
                     result.tailored_bc_gini_branch_mode == "outer_controller"),
                !static_native_api && result.tailored_bc_branch_priority_enabled,
                options.tailored_bc_gini_branch_min_width,
                instance.initial,
                instance.capacity,
                instance.target,
                instance.weights,
                instance.Q,
                callback_dist,
                instance.V + 1,
                instance.total_time_limit,
                instance.pickup_time + instance.drop_time,
                options.tailored_bc_support_duration_cover_mode,
                options.tailored_bc_gini_subset_max_size,
                options.tailored_bc_gini_subset_max_cuts,
                options.tailored_bc_vector_route_cutset_max_size,
                options.tailored_bc_vector_route_cutset_max_cuts,
                options.tailored_bc_vector_cut_min_violation,
                options.tailored_bc_callback_separation_pacing,
                options.tailored_bc_callback_separation_min_calls,
                options.tailored_bc_callback_cut_profile,
                options.tailored_bc_local_centering,
                options.tailored_bc_subset_cross_h_centering,
                options.tailored_bc_subset_cross_h_max_size,
                options.tailored_bc_subset_cross_h_max_cuts,
                options.tailored_bc_subset_cross_h_separation_profile,
                options.tailored_bc_local_q_centering,
                options.lambda,
                cutoff.incumbent_ub - cutoff.epsilon,
                instance.M,
                static_native_api || options.progress_log_path.empty()
                    ? std::filesystem::path()
                    : std::filesystem::path(options.progress_log_path),
                result.compact_bc_progress_interval_seconds > 0.0
                    ? result.compact_bc_progress_interval_seconds
                    : options.progress_interval_seconds,
                !static_native_api,
                native_checkpoint);
            if (native_checkpoint.enabled) {
                NativeCheckpointRecord checkpoint_record;
                std::string checkpoint_read_reason;
                if (readNativeCheckpoint(
                        native_checkpoint.path,
                        checkpoint_record,
                        &checkpoint_read_reason)) {
                    NativeCheckpointExpectation expected;
                    expected.run_id = native_checkpoint.run_id;
                    expected.instance_hash = native_checkpoint.instance_hash;
                    expected.gamma_L = cutoff.gamma_L;
                    expected.gamma_U = cutoff.gamma_U;
                    expected.cutoff = cutoff.incumbent_ub - cutoff.epsilon;
                    expected.model_fingerprint =
                        native_checkpoint.model_fingerprint;
                    expected.formulation_profile =
                        native_checkpoint.formulation_profile;
                    expected.cplex_threads =
                        std::max(1, effective_compact_threads);
                    expected.native_time_limit_param_id =
                        api_solve.native_time_limit_param_id;
                    expected.native_time_limit_seconds =
                        api_solve.native_time_limit_seconds;
                    const NativeCheckpointValidation validation =
                        validateNativeCheckpoint(checkpoint_record, expected);
                    result.compact_bc_native_checkpoint_sequence =
                        checkpoint_record.sequence;
                    if (!options.controlling_leaf_checkpoint_merge) {
                        result.compact_bc_native_checkpoint_acceptance_status =
                            "rejected";
                        result.compact_bc_native_checkpoint_rejection_reason =
                            "checkpoint_merge_disabled_by_ablation";
                    } else if (validation.accepted) {
                        result.compact_bc_native_checkpoint_acceptance_status =
                            "accepted";
                        result.compact_bc_native_checkpoint_rejection_reason =
                            "none";
                        api_solve.checkpoint_best_bound_available = true;
                        api_solve.checkpoint_best_bound =
                            checkpoint_record.best_bound;
                        if (!api_solve.best_bound_available ||
                            checkpoint_record.best_bound >
                                api_solve.best_bound) {
                            api_solve.best_bound = checkpoint_record.best_bound;
                            api_solve.best_bound_available = true;
                            api_solve.best_bound_fail_reason =
                                "validated_atomic_native_checkpoint";
                        }
                    } else {
                        result.compact_bc_native_checkpoint_acceptance_status =
                            "rejected";
                        result.compact_bc_native_checkpoint_rejection_reason =
                            validation.reason;
                    }
                } else {
                    result.compact_bc_native_checkpoint_acceptance_status =
                        "not_seen";
                    result.compact_bc_native_checkpoint_rejection_reason =
                        checkpoint_read_reason;
                }
                if (api_solve.best_bound_fail_reason ==
                        "checkpoint_cplex_native_best_bound" &&
                    result.compact_bc_native_checkpoint_acceptance_status !=
                        "accepted") {
                    api_solve.best_bound_available = false;
                    api_solve.best_bound = 0.0;
                    api_solve.best_bound_fail_reason =
                        "unvalidated_checkpoint_not_mergeable:" +
                        result.compact_bc_native_checkpoint_rejection_reason;
                }
            }
            if (api_solve.checkpoint_log_written) {
                result.progress_log_path = options.progress_log_path;
                result.progress_checkpoints_written =
                    api_solve.checkpoint_rows_written;
                result.gap_trajectory_available =
                    api_solve.checkpoint_rows_written > 0;
                result.last_progress_event = "tailored_bc_callback_checkpoint";
                result.last_bound_improvement_time =
                    api_solve.last_checkpoint_time;
            }
            result.compact_bc_best_bound_available =
                api_solve.best_bound_available;
            result.compact_bc_best_bound_fail_reason =
                api_solve.best_bound_fail_reason;
            result.compact_bc_native_time_limit_param_id =
                api_solve.native_time_limit_param_id;
            result.compact_bc_native_time_limit_seconds =
                api_solve.native_time_limit_seconds;
            result.compact_bc_native_time_limit_set_rc =
                api_solve.native_time_limit_set_rc;
            result.compact_bc_native_mip_gap_param_id =
                api_solve.native_mip_gap_param_id;
            result.compact_bc_native_mip_gap =
                api_solve.native_mip_gap;
            result.compact_bc_native_mip_gap_set_rc =
                api_solve.native_mip_gap_set_rc;
            result.compact_bc_callback_abort_requests =
                api_solve.callback_abort_requests;
            result.compact_bc_terminate_set_rc =
                api_solve.terminate_set_rc;
            result.compact_bc_terminate_triggered =
                api_solve.terminate_triggered;
            result.compact_bc_terminate_after_seconds =
                api_solve.terminate_after_seconds;
            result.compact_bc_checkpoint_best_bound_available =
                api_solve.checkpoint_best_bound_available;
            result.compact_bc_checkpoint_best_bound =
                api_solve.checkpoint_best_bound;
            result.compact_bc_checkpoint_incumbent_available =
                api_solve.checkpoint_incumbent_available;
            result.compact_bc_checkpoint_incumbent =
                api_solve.checkpoint_incumbent;
            result.compact_bc_checkpoint_node_count =
                api_solve.checkpoint_node_count;
            if (api_solve.best_bound_available) {
                result.best_valid_lb_seen = api_solve.best_bound;
                result.best_valid_gap_seen =
                    (std::fabs(options.interval_exact_cutoff_UB) > 1e-12)
                        ? std::max(0.0,
                            (options.interval_exact_cutoff_UB - api_solve.best_bound) /
                                std::fabs(options.interval_exact_cutoff_UB))
                        : 0.0;
                result.best_valid_ledger_time = api_solve.last_checkpoint_time;
                result.best_valid_ledger_checkpoint = options.progress_log_path;
                result.interrupted_run_best_bound_preserved =
                    api_solve.terminate_triggered ||
                    api_solve.callback_wall_time_abort;
                result.final_json_uses_best_checkpoint =
                    api_solve.best_bound_fail_reason ==
                        "checkpoint_cplex_native_best_bound";
                if (api_solve.best_bound_fail_reason ==
                    "checkpoint_cplex_native_best_bound") {
                    result.finalization_source =
                        "cplex_callback_checkpoint_with_valid_best_bound";
                } else if (api_solve.terminate_triggered ||
                           api_solve.callback_wall_time_abort ||
                           statusIsTimeLimited(api_solve.status)) {
                    result.finalization_source =
                        "cplex_time_limit_with_valid_best_bound";
                } else {
                    result.finalization_source = "cplex_solver_final";
                }
            } else {
                result.finalization_source = api_solve.terminate_triggered
                    ? "cplex_terminate_without_valid_best_bound"
                    : "cplex_solver_final_no_valid_bound";
            }
            used_callback_api = api_solve.available && api_solve.solved;
            rc = api_solve.return_code;
            if (used_callback_api) {
                cplex_status = api_solve.status;
                cplex_obj = api_solve.objective;
                best_bound = api_solve.best_bound;
                values = std::move(api_solve.values);
                result.nodes = api_solve.node_count;
                result.tailored_bc_relaxation_callback_calls =
                    api_solve.relaxation_callback_calls;
                result.tailored_bc_candidate_callback_calls =
                    api_solve.candidate_callback_calls;
                result.tailored_bc_branch_callback_calls =
                    api_solve.branch_callback_calls;
                result.tailored_bc_progress_callback_calls =
                    api_solve.progress_callback_calls;
                result.tailored_bc_callback_vector_export_claimed =
                    api_solve.relaxation_vector_api_called;
                result.tailored_bc_callback_vector_export_working =
                    api_solve.relaxation_vector_snapshot_available &&
                    api_solve.relaxation_vector_nonzero_values > 0;
                result.tailored_bc_callback_vector_export_status =
                    result.tailored_bc_callback_vector_export_working
                        ? "callback_vector_export_working"
                        : (api_solve.relaxation_vector_api_called
                               ? "unknown_failure"
                               : "callback_context_not_reached");
                result.tailored_bc_callback_vector_context_seen =
                    api_solve.relaxation_callback_calls > 0 ||
                    api_solve.candidate_callback_calls > 0;
                result.tailored_bc_callback_vector_relaxation_context_seen =
                    api_solve.relaxation_callback_calls > 0;
                result.tailored_bc_callback_vector_candidate_context_seen =
                    api_solve.candidate_callback_calls > 0;
                result.tailored_bc_callback_vector_api_called =
                    api_solve.relaxation_vector_api_called;
                result.tailored_bc_callback_vector_api_return_code =
                    api_solve.relaxation_vector_api_return_code;
                result.tailored_bc_callback_vector_length_requested =
                    api_solve.relaxation_vector_length_requested;
                result.tailored_bc_callback_vector_length_returned =
                    api_solve.relaxation_vector_length_returned;
                result.tailored_bc_callback_vector_nonzero_values_count =
                    api_solve.relaxation_vector_nonzero_values;
                result.tailored_bc_callback_vector_sample_variable_names =
                    api_solve.relaxation_vector_sample_variable_names;
                result.tailored_bc_callback_vector_sample_variable_values =
                    api_solve.relaxation_vector_sample_variable_values;
                result.tailored_bc_callback_vector_full_variable_names =
                    api_solve.relaxation_vector_full_variable_names;
                result.tailored_bc_callback_vector_full_variable_values =
                    api_solve.relaxation_vector_full_variable_values;
                result.tailored_bc_callback_vector_failure_reason =
                    api_solve.relaxation_vector_failure_reason;
                result.tailored_bc_callback_candidate_vector_api_called =
                    api_solve.candidate_vector_api_called;
                result.tailored_bc_callback_candidate_vector_api_return_code =
                    api_solve.candidate_vector_api_return_code;
                result.tailored_bc_callback_candidate_vector_length_requested =
                    api_solve.candidate_vector_length_requested;
                result.tailored_bc_callback_candidate_vector_length_returned =
                    api_solve.candidate_vector_length_returned;
                result.tailored_bc_callback_candidate_vector_nonzero_values_count =
                    api_solve.candidate_vector_nonzero_values;
                result.tailored_bc_callback_candidate_vector_sample_variable_names =
                    api_solve.candidate_vector_sample_variable_names;
                result.tailored_bc_callback_candidate_vector_sample_variable_values =
                    api_solve.candidate_vector_sample_variable_values;
                result.tailored_bc_callback_candidate_vector_full_variable_names =
                    api_solve.candidate_vector_full_variable_names;
                result.tailored_bc_callback_candidate_vector_full_variable_values =
                    api_solve.candidate_vector_full_variable_values;
                result.tailored_bc_callback_candidate_vector_failure_reason =
                    api_solve.candidate_vector_failure_reason;
                result.tailored_bc_user_cuts_added_total +=
                    api_solve.user_cuts_added;
                result.tailored_bc_lazy_rejections_total =
                    api_solve.lazy_rejections;
                result.tailored_bc_incumbents_seen =
                    api_solve.incumbents_seen;
                result.tailored_bc_incumbents_verified =
                    api_solve.incumbents_verified;
                result.tailored_bc_incumbents_rejected =
                    api_solve.incumbents_rejected;
                if (api_solve.lazy_rejections > 0) {
                    std::ostringstream lazy;
                    lazy << "candidate_gini_interval_violation="
                         << api_solve.lazy_gini_interval_rejections
                         << ";candidate_visit_inventory_violation="
                         << api_solve.lazy_visit_inventory_rejections
                         << ";candidate_gini_subset_envelope_violation="
                         << api_solve.lazy_gini_subset_envelope_rejections
                         << ";candidate_low_gini_l1_violation="
                         << api_solve.lazy_low_gini_l1_rejections
                         << ";candidate_variable_s_centering_violation="
                         << api_solve.lazy_variable_s_centering_rejections
                         << ";candidate_subset_inventory_imbalance_violation="
                         << api_solve.lazy_subset_inventory_imbalance_rejections
                         << ";candidate_projection_ratio_violation="
                         << api_solve.candidate_projection_ratio_rejections
                         << ";candidate_projection_penalty_violation="
                         << api_solve.candidate_projection_penalty_rejections
                         << ";candidate_projection_objective_violation="
                         << api_solve.candidate_projection_objective_rejections
                         << ";candidate_route_flow_violation="
                         << api_solve.candidate_route_projection_flow_rejections
                         << ";candidate_route_station_violation="
                         << api_solve.candidate_route_projection_station_rejections
                         << ";candidate_route_service_violation="
                         << api_solve.candidate_route_projection_service_rejections
                         << ";candidate_route_duration_violation="
                         << api_solve.candidate_route_projection_duration_rejections
                         << ";candidate_route_inventory_violation="
                         << api_solve.candidate_route_projection_inventory_rejections;
                    result.tailored_bc_lazy_rejections_by_reason = lazy.str();
                } else {
                    result.tailored_bc_lazy_rejections_by_reason = "none";
                }
                result.tailored_bc_candidate_projection_checks =
                    api_solve.candidate_projection_checks;
                result.tailored_bc_candidate_projection_verified =
                    api_solve.candidate_projection_verified;
                result.tailored_bc_candidate_projection_rejections =
                    api_solve.candidate_projection_rejections;
                result.tailored_bc_candidate_projection_unsupported_mismatches =
                    api_solve.candidate_projection_unsupported_mismatches;
                result.tailored_bc_candidate_projection_rejection_reasons =
                    "ratio=" +
                    std::to_string(api_solve.candidate_projection_ratio_rejections) +
                    ";penalty=" +
                    std::to_string(api_solve.candidate_projection_penalty_rejections) +
                    ";objective=" +
                    std::to_string(api_solve.candidate_projection_objective_rejections);
                result.tailored_bc_candidate_projection_max_gini_underestimate =
                    api_solve.candidate_projection_max_gini_underestimate;
                result.tailored_bc_candidate_projection_max_objective_underestimate =
                    api_solve.candidate_projection_max_objective_underestimate;
                result.tailored_bc_candidate_route_projection_checks =
                    api_solve.candidate_route_projection_checks;
                result.tailored_bc_candidate_route_projection_verified =
                    api_solve.candidate_route_projection_verified;
                result.tailored_bc_candidate_route_projection_rejections =
                    api_solve.candidate_route_projection_rejections;
                result.tailored_bc_candidate_route_projection_unsupported_mismatches =
                    api_solve.candidate_route_projection_unsupported_mismatches;
                result.tailored_bc_candidate_route_projection_rejection_reasons =
                    "flow=" +
                    std::to_string(api_solve.candidate_route_projection_flow_rejections) +
                    ";station=" +
                    std::to_string(api_solve.candidate_route_projection_station_rejections) +
                    ";service=" +
                    std::to_string(api_solve.candidate_route_projection_service_rejections) +
                    ";duration=" +
                    std::to_string(api_solve.candidate_route_projection_duration_rejections) +
                    ";inventory=" +
                    std::to_string(api_solve.candidate_route_projection_inventory_rejections) +
                    ";load_unsupported=" +
                    std::to_string(api_solve.candidate_route_projection_load_mismatches);
                result.tailored_bc_gini_branches_created =
                    api_solve.gini_branches_created;
                if (api_solve.callback_wall_time_abort) {
                    result.notes.push_back(
                        "CPLEX callback wall-clock guard aborted mipopt after the configured interval time limit plus grace; row is unresolved unless a valid bound closes it.");
                }
                result.tailored_bc_branching_priorities_summary +=
                    ";cplex_copyorder_status=" + api_solve.branch_priority_status +
                    ";cplex_priorities_applied=" +
                    std::to_string(api_solve.branch_priorities_applied);
                result.tailored_bc_user_cuts_added_by_family +=
                    ";callback_gini_interval_cap=" +
                    std::to_string(api_solve.callback_gini_interval_cuts_added) +
                    ";callback_visit_inventory_linking=" +
                    std::to_string(api_solve.callback_visit_inventory_cuts_added) +
                    ";callback_gini_subset_envelope=" +
                    std::to_string(api_solve.callback_gini_subset_envelope_cuts_added) +
                    ";callback_low_gini_l1_centering=" +
                    std::to_string(api_solve.callback_low_gini_l1_cuts_added) +
                    ";callback_local_centering=" +
                    std::to_string(api_solve.callback_local_centering_cuts_added) +
                    ";callback_subset_cross_h_centering=" +
                    std::to_string(api_solve.callback_subset_cross_h_centering_cuts_added) +
                    ";callback_local_q_centering=" +
                    std::to_string(api_solve.callback_local_q_centering_cuts_added) +
                    ";callback_gs_product_coupling=" +
                    std::to_string(api_solve.callback_gs_product_cuts_added) +
                    ";callback_disaggregated_sp_estimator=" +
                    std::to_string(api_solve.callback_disagg_sp_cuts_added) +
                    ";callback_vector_route_cutset=" +
                    std::to_string(api_solve.callback_vector_route_cutset_cuts_added) +
                    ";callback_variable_s_centering=" +
                    std::to_string(api_solve.callback_variable_s_centering_cuts_added) +
                    ";callback_subset_inventory_imbalance=" +
                    std::to_string(api_solve.callback_subset_inventory_imbalance_cuts_added) +
                    ";callback_transfer_cutset=" +
                    std::to_string(api_solve.callback_transfer_cutset_cuts_added) +
                    ";callback_support_duration_pair=" +
                    std::to_string(api_solve.callback_support_duration_pair_cuts_added) +
                    ";callback_support_duration_triple=" +
                    std::to_string(api_solve.callback_support_duration_triple_cuts_added) +
                    ";callback_support_duration_quad=" +
                    std::to_string(api_solve.callback_support_duration_quad_cuts_added) +
                    ";callback_support_duration_lifted=" +
                    std::to_string(api_solve.callback_support_duration_lifted_cuts_added);
                result.tailored_bc_gini_subset_envelope_candidates +=
                    api_solve.callback_gini_subset_envelope_candidates;
                result.tailored_bc_gini_subset_envelope_violations +=
                    api_solve.callback_gini_subset_envelope_violations;
                result.tailored_bc_gini_subset_envelope_cuts_added +=
                    api_solve.callback_gini_subset_envelope_cuts_added;
                result.tailored_bc_max_gini_subset_violation =
                    std::max(result.tailored_bc_max_gini_subset_violation,
                             api_solve.callback_gini_subset_envelope_max_violation);
                result.tailored_bc_callback_separation_pacing =
                    options.tailored_bc_callback_separation_pacing;
                result.tailored_bc_callback_expensive_separation_calls =
                    api_solve.callback_expensive_separation_calls;
                result.tailored_bc_callback_expensive_separation_skips =
                    api_solve.callback_expensive_separation_skips;
                result.tailored_bc_callback_cut_profile =
                    options.tailored_bc_callback_cut_profile;
                result.tailored_bc_low_gini_l1_centering_violations +=
                    api_solve.callback_low_gini_l1_violations;
                result.tailored_bc_low_gini_l1_centering_rows_added +=
                    api_solve.callback_low_gini_l1_cuts_added;
                result.tailored_bc_local_centering_violations +=
                    api_solve.callback_local_centering_violations;
                result.tailored_bc_local_centering_rows_added +=
                    api_solve.callback_local_centering_cuts_added;
                result.tailored_bc_local_centering_max_violation =
                    std::max(result.tailored_bc_local_centering_max_violation,
                             api_solve.callback_local_centering_max_violation);
                result.tailored_bc_subset_cross_h_centering_candidates +=
                    api_solve.callback_subset_cross_h_centering_candidates;
                result.tailored_bc_subset_cross_h_centering_violations +=
                    api_solve.callback_subset_cross_h_centering_violations;
                result.tailored_bc_subset_cross_h_centering_rows_added +=
                    api_solve.callback_subset_cross_h_centering_cuts_added;
                result.tailored_bc_subset_cross_h_centering_max_violation =
                    std::max(result.tailored_bc_subset_cross_h_centering_max_violation,
                             api_solve.callback_subset_cross_h_centering_max_violation);
                result.tailored_bc_local_q_centering_violations +=
                    api_solve.callback_local_q_centering_violations;
                result.tailored_bc_local_q_centering_rows_added +=
                    api_solve.callback_local_q_centering_cuts_added;
                result.tailored_bc_local_q_centering_max_violation =
                    std::max(result.tailored_bc_local_q_centering_max_violation,
                             api_solve.callback_local_q_centering_max_violation);
                result.gs_product_callback_rows_added +=
                    api_solve.callback_gs_product_cuts_added;
                result.gs_product_coupling_violations +=
                    api_solve.callback_gs_product_violations;
                result.gs_product_coupling_max_violation =
                    std::max(result.gs_product_coupling_max_violation,
                             api_solve.callback_gs_product_max_violation);
                result.disagg_sp_callback_rows_added +=
                    api_solve.callback_disagg_sp_cuts_added;
                result.disagg_sp_violations +=
                    api_solve.callback_disagg_sp_violations;
                result.disagg_sp_max_violation =
                    std::max(result.disagg_sp_max_violation,
                             api_solve.callback_disagg_sp_max_violation);
                result.vector_callback_route_cutset_candidates +=
                    api_solve.callback_vector_route_cutset_candidates;
                result.vector_callback_route_cutset_cuts_added +=
                    api_solve.callback_vector_route_cutset_cuts_added;
                result.vector_callback_route_cutset_max_violation =
                    std::max(result.vector_callback_route_cutset_max_violation,
                             api_solve.callback_vector_route_cutset_max_violation);
                result.vector_callback_route_cutset_violations +=
                    api_solve.callback_vector_route_cutset_violations;
                result.vector_callback_route_cutset_violation_sum +=
                    api_solve.callback_vector_route_cutset_violation_sum;
                result.vector_callback_route_cutset_average_violation =
                    result.vector_callback_route_cutset_violations > 0
                        ? result.vector_callback_route_cutset_violation_sum /
                              static_cast<double>(result.vector_callback_route_cutset_violations)
                        : 0.0;
                result.vector_callback_route_cutset_cuts_size_2 +=
                    api_solve.callback_vector_route_cutset_cuts_size_2;
                result.vector_callback_route_cutset_cuts_size_3 +=
                    api_solve.callback_vector_route_cutset_cuts_size_3;
                result.vector_callback_route_cutset_cuts_size_4 +=
                    api_solve.callback_vector_route_cutset_cuts_size_4;
                result.vector_callback_route_cutset_cuts_size_5 +=
                    api_solve.callback_vector_route_cutset_cuts_size_5;
                result.vector_callback_support_cover_candidates +=
                    api_solve.callback_support_duration_pair_candidates +
                    api_solve.callback_support_duration_triple_candidates +
                    api_solve.callback_support_duration_quad_candidates;
                result.vector_callback_support_cover_cuts_added +=
                    api_solve.callback_support_duration_pair_cuts_added +
                    api_solve.callback_support_duration_triple_cuts_added +
                    api_solve.callback_support_duration_quad_cuts_added;
                result.tailored_bc_variable_s_centering_violations +=
                    api_solve.callback_variable_s_centering_violations;
                result.tailored_bc_variable_s_centering_cuts_added +=
                    api_solve.callback_variable_s_centering_cuts_added;
                result.tailored_bc_subset_inventory_imbalance_cuts_added +=
                    api_solve.callback_subset_inventory_imbalance_cuts_added;
                result.tailored_bc_subset_inventory_imbalance_candidates +=
                    api_solve.callback_subset_inventory_imbalance_candidates;
                result.tailored_bc_subset_inventory_imbalance_violations +=
                    api_solve.callback_subset_inventory_imbalance_violations;
                result.tailored_bc_transfer_cutset_cuts_added +=
                    api_solve.callback_transfer_cutset_cuts_added;
                result.tailored_bc_transfer_cutset_candidates +=
                    api_solve.callback_transfer_cutset_candidates;
                result.tailored_bc_transfer_cutset_violations +=
                    api_solve.callback_transfer_cutset_violations;
                result.tailored_bc_support_duration_pair_cuts_added +=
                    api_solve.callback_support_duration_pair_cuts_added;
                result.tailored_bc_support_duration_pair_candidates +=
                    api_solve.callback_support_duration_pair_candidates;
                result.tailored_bc_support_duration_pair_violations +=
                    api_solve.callback_support_duration_pair_violations;
                result.tailored_bc_support_duration_triple_cuts_added +=
                    api_solve.callback_support_duration_triple_cuts_added;
                result.tailored_bc_support_duration_triple_candidates +=
                    api_solve.callback_support_duration_triple_candidates;
                result.tailored_bc_support_duration_triple_violations +=
                    api_solve.callback_support_duration_triple_violations;
                result.tailored_bc_support_duration_quad_cuts_added +=
                    api_solve.callback_support_duration_quad_cuts_added;
                result.tailored_bc_support_duration_quad_candidates +=
                    api_solve.callback_support_duration_quad_candidates;
                result.tailored_bc_support_duration_quad_violations +=
                    api_solve.callback_support_duration_quad_violations;
                result.tailored_bc_support_duration_lifted_cuts_added +=
                    api_solve.callback_support_duration_lifted_cuts_added;
                result.tailored_bc_support_duration_lifted_candidates +=
                    api_solve.callback_support_duration_lifted_candidates;
                result.tailored_bc_support_duration_lifted_violations +=
                    api_solve.callback_support_duration_lifted_violations;
                if (result.gs_h_upper_rows_added > 0 ||
                    result.gs_product_callback_rows_added > 0) {
                    result.gs_product_coupling_proof_status =
                        model_options.tailored_bc_gs_product_lower_row == "diagnostic"
                            ? "upper_row_paper_safe_lower_row_diagnostic"
                            : "paper_safe_upper_row";
                }
                if (result.disagg_sp_estimator_rows_added > 0 ||
                    result.disagg_sp_callback_rows_added > 0) {
                    result.disagg_sp_proof_status =
                        "paper_safe_bucket_local_disaggregated_sp_estimator";
                }
                if (result.vector_callback_route_cutset_cuts_added > 0 ||
                    result.vector_callback_support_cover_cuts_added > 0) {
                    result.vector_route_cuts_proof_status =
                        "paper_safe_universal_rows_vector_selected_candidates";
                }
                result.notes.push_back(static_native_api
                    ? "CPLEX native C API backend used without registering any callback; solver-final best bound and native time-limit return code captured"
                    : "CPLEX dynamic callback API backend used for tailored BC; callback events relaxation="
                    + std::to_string(api_solve.relaxation_callback_calls)
                    + ", candidate=" + std::to_string(api_solve.candidate_callback_calls)
                    + ", branch=" + std::to_string(api_solve.branch_callback_calls)
                    + ", progress=" + std::to_string(api_solve.progress_callback_calls)
                    + ", user_cuts=" + std::to_string(api_solve.user_cuts_added)
                    + ", lazy_rejections=" + std::to_string(api_solve.lazy_rejections)
                    + ", projection_checks=" +
                        std::to_string(api_solve.candidate_projection_checks)
                    + ", projection_verified=" +
                        std::to_string(api_solve.candidate_projection_verified)
                    + ", branch_priorities=" +
                        std::to_string(api_solve.branch_priorities_applied));
            } else {
                result.notes.push_back(
                    "CPLEX dynamic callback API backend unavailable at solve time: "
                    + api_solve.fail_reason + "; falling back to command-file CPLEX");
            }
        }
        if (!used_callback_api) {
            std::ofstream cmd(cmd_path);
            cmd << "set threads " << std::max(1, effective_compact_threads) << "\n";
            cmd << "set timelimit " << time_limit << "\n";
            cmd << "set mip tolerances mipgap 0\n";
            if (options.interval_oracle_profile == "infeasibility-focus") {
                cmd << "set emphasis mip 1\n";
            } else if (options.interval_oracle_profile == "bound-focus") {
                cmd << "set emphasis mip 3\n";
            } else if (options.interval_oracle_profile == "integrality-focus") {
                cmd << "set emphasis mip 4\n";
            }
            cmd << "read " << lp_path.string() << "\n";
            cmd << "optimize\n";
            cmd << "write " << sol_path.string() << "\n";
            cmd << "quit\n";
            cmd.close();

            const std::string cplex = defaultCplexPath();
            const std::string command = "cmd /C \"" + quote(cplex) + " -f "
                + quote(cmd_path) + " > " + quote(cplex_log) + " 2>&1\"";
            rc = std::system(command.c_str());
            if (std::filesystem::exists(sol_path)) {
                values = parseSolValues(sol_path, cplex_status, cplex_obj, best_bound);
            } else {
                cplex_status = parseCplexTerminalStatus(cplex_log);
                if (cplex_status == "unknown") {
                    cplex_status = (rc == 0) ? "no solution file" : "cplex process failed";
                }
            }
            result.nodes = parseCplexNodes(cplex_log);
        }
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.actual_runtime_seconds = result.runtime_seconds;
        result.interval_exact_cutoff_runtime_seconds = result.runtime_seconds;
        result.compact_bc_time_seconds = result.runtime_seconds;
        result.compact_bc_total_solver_time = result.runtime_seconds;
        result.interval_exact_cutoff_solver_status = cplex_status;
        result.compact_bc_solver_status = cplex_status;
        result.interval_exact_cutoff_nodes = result.nodes;
        result.compact_bc_nodes = result.nodes;
        if (!used_callback_api) {
            const double log_best_bound = parseCplexBestBound(cplex_log);
            if (!std::isfinite(best_bound) && std::isfinite(log_best_bound)) {
                best_bound = log_best_bound;
                result.compact_bc_best_bound_available = true;
                result.compact_bc_best_bound_fail_reason = "none";
            }
            if (!result.compact_bc_best_bound_available &&
                result.compact_bc_best_bound_fail_reason.empty()) {
                result.compact_bc_best_bound_fail_reason =
                    "best_bound_unavailable_in_cplex_log";
            }
        }
        result.interval_exact_cutoff_best_bound = std::isfinite(best_bound) ? best_bound : 0.0;
        result.interval_exact_cutoff_objective = std::isfinite(cplex_obj) ? cplex_obj : 0.0;
        result.interval_oracle_solver_best_bound = result.interval_exact_cutoff_best_bound;
        result.interval_oracle_solver_incumbent = result.interval_exact_cutoff_objective;
        result.compact_bc_best_bound = result.interval_exact_cutoff_best_bound;
        if (std::isfinite(best_bound)) {
            result.compact_bc_best_bound_available = true;
            if (result.compact_bc_best_bound_fail_reason.empty()) {
                result.compact_bc_best_bound_fail_reason = "none";
            }
        } else if (result.compact_bc_best_bound_fail_reason.empty()) {
            result.compact_bc_best_bound_fail_reason =
                "best_bound_unavailable";
        }
        result.compact_bc_incumbent = result.interval_exact_cutoff_objective;
        result.compact_bc_time_seconds = result.interval_exact_cutoff_runtime_seconds;

        const double cutoff_value = options.interval_exact_cutoff_UB - options.interval_exact_cutoff_epsilon;
        result.interval_oracle_gap_to_cutoff = std::isfinite(best_bound)
            ? (cutoff_value - best_bound)
            : 0.0;
        const bool finite_bound = std::isfinite(best_bound);
        const bool best_bound_is_valid =
            finite_bound &&
            (objective_bound_mode ||
             best_bound <= cutoff_value + 1e-7 ||
             best_bound >= cutoff_value - 1e-7);
        result.interval_oracle_bound_valid = best_bound_is_valid;
        result.interval_oracle_can_merge_bound =
            best_bound_is_valid &&
            result.interval_oracle_bound_scope == "original_fixed_interval";
        result.compact_interval_bc_bound_valid = result.interval_oracle_bound_valid;
        result.compact_bc_bound_valid = result.interval_oracle_bound_valid;
        if (statusIsInfeasible(cplex_status)) {
            result.status = "interval_closed";
            result.lower_bound = options.interval_exact_cutoff_UB;
            result.upper_bound = options.interval_exact_cutoff_UB;
            result.gap = 0.0;
            result.interval_exact_cutoff_proven_infeasible = true;
            result.interval_exact_cutoff_certificate_basis = "interval_exact_cutoff_mip_infeasible";
            result.interval_oracle_bound_valid = true;
            result.interval_oracle_can_merge_bound = true;
            result.compact_interval_bc_bound_valid = true;
            result.compact_bc_bound_valid = true;
            result.compact_interval_bc_closed_leaves = 1;
            result.compact_bc_closed_leaf_count = 1;
            result.certificate = "CPLEX proved the original compact fixed-interval cutoff MIP infeasible; no incumbent-improving original solution exists in this interval.";
        } else if (statusIsOptimal(cplex_status) && std::isfinite(cplex_obj) &&
                   cplex_obj >= cutoff_value - 1e-7) {
            result.status = "interval_closed";
            result.lower_bound = cplex_obj;
            result.upper_bound = options.interval_exact_cutoff_UB;
            result.gap = 0.0;
            result.interval_exact_cutoff_proven_infeasible = true;
            result.interval_exact_cutoff_certificate_basis = objective_bound_mode
                ? "interval_exact_objective_bound_optimal_no_improver"
                : "interval_exact_cutoff_mip_optimal_no_improver";
            result.interval_oracle_bound_valid = true;
            result.interval_oracle_can_merge_bound = true;
            result.compact_interval_bc_bound_valid = true;
            result.compact_bc_bound_valid = true;
            result.compact_interval_bc_closed_leaves = 1;
            result.compact_bc_closed_leaf_count = 1;
            result.certificate = "CPLEX optimized the fixed-interval cutoff MIP and its objective excludes all incumbent-improving solutions in this interval.";
        } else if (statusIsOptimal(cplex_status) && !values.empty()) {
            result.routes = reconstructRoutes(instance, values);
            result.verification = verifySolution(instance, result.routes, options.lambda);
            result.final_inventory = result.verification.final_inventory;
            result.G = result.verification.G;
            result.P = result.verification.P;
            result.objective = result.verification.objective;
            result.upper_bound = result.objective;
            result.lower_bound = std::isfinite(best_bound) ? best_bound : 0.0;
            result.gap = (std::fabs(result.upper_bound) > 1e-12)
                ? std::max(0.0, (result.upper_bound - result.lower_bound) / std::fabs(result.upper_bound))
                : 0.0;
            const bool in_interval =
                result.G >= options.interval_exact_cutoff_gamma_L - 1e-7 &&
                result.G <= options.interval_exact_cutoff_gamma_U + 1e-7;
            const bool improving = result.verification.feasible &&
                in_interval &&
                result.objective <= cutoff_value + 1e-7;
            result.interval_exact_cutoff_feasible_improving = improving;
            result.status = improving ? "interval_feasible_improving_ub" : "interval_unresolved_feasible_relaxation_solution";
            result.interval_exact_cutoff_certificate_basis = improving
                ? "interval_exact_cutoff_mip_feasible_improving"
                : (objective_bound_mode
                    ? "interval_exact_objective_bound_optimal_below_cutoff"
                    : "interval_exact_cutoff_mip_feasible_not_verified_original_interval_improver");
            result.interval_oracle_bound_valid = finite_bound;
            result.interval_oracle_can_merge_bound = finite_bound;
            result.compact_interval_bc_bound_valid = finite_bound;
            result.compact_bc_bound_valid = finite_bound;
            result.compact_bc_unresolved_leaf_count = improving ? 0 : 1;
            result.certificate = improving
                ? "CPLEX found an original feasible incumbent-improving route plan in this interval; it is UB-only and requires frontier restart."
                : "CPLEX found/optimized an interval solution below the incumbent cutoff; interval remains unresolved but its valid solver bound may be merged.";
        } else {
            const bool interval_timed_out =
                statusIsTimeLimited(cplex_status) ||
                (used_callback_api && api_solve.callback_wall_time_abort);
            result.status = interval_timed_out
                ? "interval_unresolved_timeout"
                : "interval_unresolved";
            result.interval_exact_cutoff_timeout = interval_timed_out;
            result.compact_interval_bc_timed_out_leaves =
                result.interval_exact_cutoff_timeout ? 1 : 0;
            double merge_bound = 0.0;
            if (best_bound_is_valid) {
                merge_bound = (objective_bound_mode && !add_objective_cutoff)
                    ? best_bound
                    : std::min(best_bound, cutoff_value);
            }
            result.lower_bound = merge_bound;
            result.upper_bound = options.interval_exact_cutoff_UB;
            result.gap = (std::fabs(result.upper_bound) > 1e-12)
                ? std::max(0.0, (result.upper_bound - result.lower_bound) / std::fabs(result.upper_bound))
                : 0.0;
            result.interval_exact_cutoff_gap = result.gap;
            result.interval_exact_cutoff_certificate_basis = result.interval_exact_cutoff_timeout
                ? "interval_exact_cutoff_mip_timeout"
                : "interval_exact_cutoff_mip_unresolved";
            result.compact_bc_unresolved_leaf_count = 1;
            result.compact_interval_bc_rejection_reason =
                best_bound_is_valid ? "valid_bound_below_cutoff" : "no_mergeable_bound";
            result.compact_bc_rejection_reason =
                result.compact_interval_bc_rejection_reason;
            result.certificate = best_bound_is_valid
                ? "CPLEX did not close the interval, but returned a valid original fixed-interval objective lower bound; interval remains unresolved unless the bound reaches incumbent cutoff."
                : "CPLEX did not prove fixed-interval cutoff infeasibility or produce a valid mergeable bound; interval remains unresolved. CPLEX status: " + cplex_status;
            result.plateau_detected = result.interval_exact_cutoff_timeout;
            result.plateau_reason = best_bound_is_valid
                ? "valid_bound_below_cutoff_after_compact_bc_timeout"
                : result.compact_bc_best_bound_fail_reason;
            if (result.last_bound_improvement_time <= 0.0) {
                result.last_bound_improvement_time =
                    result.progress_checkpoints_written > 0
                        ? result.runtime_seconds
                        : 0.0;
            }
        }
        result.compact_interval_bc_bound_valid = result.interval_oracle_bound_valid;
        result.compact_bc_bound_valid = result.interval_oracle_bound_valid;
        result.compact_interval_bc_bound_scope = result.interval_oracle_bound_scope;
        result.compact_bc_bound_scope = result.interval_oracle_bound_scope;
        result.s_range_bucket_closed =
            result.s_range_refinement_enabled && result.status == "interval_closed";
        if (result.s_range_refinement_enabled &&
            result.compact_bc_s_range_refinement != "paper-safe") {
            result.s_range_certificate_valid = false;
            result.notes.push_back(
                "S-range refinement was run in diagnostic mode; bucket evidence is not a full parent-leaf certificate unless coverage is explicitly merged.");
        }
        result.oracle_strengthening_lb_improvement =
            std::max(0.0, result.lower_bound - options.interval_exact_cutoff_gamma_L);
        result.notes.push_back("CPLEX solution status: " + cplex_status);
        result.notes.push_back("CPLEX process return code: " + std::to_string(rc));
        result.notes.push_back("LP file: " + lp_path.string());
        result.notes.push_back("CPLEX log: " + cplex_log.string());
        if (result.tailored_bc_enabled) {
            result.tailored_bc_source_class = tailoredBCSourceClass(result);
            if (result.tailored_bc_mode == "static_fallback") {
                result.notes.push_back(options.tailored_bc_mode == "static"
                    ? "paper-gf-tailored-bc static no-callback mode was explicitly requested; no CPLEX callback was registered."
                    : "paper-gf-tailored-bc callback mode is unavailable in this build; this fixed-interval row is static fallback evidence, not a true callback BC claim.");
            }
        }
    } catch (const std::exception& e) {
        result.status = "error";
        result.interval_exact_cutoff_certificate_basis = "interval_exact_cutoff_mip_error";
        result.certificate = std::string("Interval exact cutoff oracle failed: ") + e.what();
        result.compact_interval_bc_rejection_reason = result.certificate;
        result.compact_bc_rejection_reason = result.certificate;
        result.compact_interval_bc_bound_valid = false;
        result.compact_bc_bound_valid = false;
        result.compact_bc_best_bound_available = false;
        result.compact_bc_best_bound_fail_reason =
            "exception_before_best_bound:" + std::string(e.what());
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.interval_exact_cutoff_runtime_seconds = result.runtime_seconds;
        result.compact_bc_time_seconds = result.runtime_seconds;
        if (result.tailored_bc_enabled) {
            result.tailored_bc_source_class = tailoredBCSourceClass(result);
        }
    }
    return result;
}

SolveResult solveGlobalGiniTree(const Instance& instance,
                                const SolveOptions& options,
                                const SolveResult& verified_seed,
                                double root_gamma_L,
                                double root_gamma_U) {
    const auto start = Clock::now();
    SolveResult result = verified_seed;
    result.method = "gcap-frontier";
    result.frontier_execution_mode = "global-gini-tree";
    result.certificate_scope = "original_global_gini_single_tree";
    result.log_file = options.log_path;
    result.global_gini_tree_attempted = true;
    result.global_gini_tree_root_gamma_L = root_gamma_L;
    result.global_gini_tree_root_gamma_U = root_gamma_U;
    result.time_budget_seconds = options.solve_time_limit;
    result.finalization_source = "native_single_cplex_problem";
    result.wrapper_synthesized_final_json = false;
    result.full_certificate_requires_pricing_closure = false;
    result.full_certificate_pricing_closure_satisfied = true;
    result.full_certificate_all_intervals_accounted = false;
    result.full_certificate_basis = "global_gini_single_tree_native_bound";
    result.full_certificate_rejection_reason = "global_tree_not_finalized";
    result.unresolved_intervals = 1;
    result.open_nodes = 0;
    result.solver_finalization_reached = false;
    result.process_return_code = -1;
    populateNativeMipEvidenceFields(
        result, NativeMipEvidence{}, 0, 0, 0, 0, 0, 0, 0, 0, 0);
    // The global-tree solve owns its native evidence.  Do not inherit a seed
    // solver's certificate merely because its feasible route is copied.
    result.native_mip_evidence_available = false;
    result.native_mip_objective_available = false;
    result.native_mip_best_bound_available = false;
    result.native_mip_cplex_relative_gap_available = false;
    result.native_mip_absolute_gap_available = false;
    result.native_mip_signed_bound_residual_available = false;
    result.native_mip_bound_inversion = false;
    result.native_mip_relative_gap_available = false;
    result.verified_incumbent_absolute_gap_available = false;
    result.verified_incumbent_signed_bound_residual_available = false;
    result.verified_incumbent_bound_inversion = false;
    result.verified_incumbent_relative_gap_available = false;
    result.verified_incumbent_project_relative_gap_available = false;
    result.verified_incumbent_objective_residual_available = false;
    result.native_mip_lifecycle_valid = false;
    result.native_mip_solver_finalization_reached = false;
    result.strict_certificate_class = "invalid_or_unavailable_bound";
    result.strict_certificate_rejection_reason = "global_tree_not_evaluated";
    result.strict_certified_original_problem = false;
    result.strict_native_objective_valid = false;
    result.strict_native_best_bound_valid = false;
    result.strict_bound_equality_closed = false;
    result.strict_bound_equality_proof_module = "none";
    result.strict_bound_equality_proof_conditions_satisfied = false;
    result.strict_independent_exact_certificate_module = "none";
    result.strict_independent_exact_certificate_conditions_satisfied = false;
    result.strict_lower_bound_source = "unavailable";
    result.strict_serialized_lower_bound_matches_native = false;
    result.strict_serialized_gap_consistent = false;
    result.native_mip_threads_requested = 0;
    result.native_mip_threads_set_return_code = -1;
    result.native_mip_threads_get_return_code = -1;
    result.native_mip_threads_effective = 0;
    result.native_mip_presolve_requested = 0;
    result.native_mip_presolve_set_return_code = -1;
    result.native_mip_presolve_get_return_code = -1;
    result.native_mip_presolve_effective = 0;
    result.native_mip_search_requested = 0;
    result.native_mip_search_set_return_code = -1;
    result.native_mip_search_get_return_code = -1;
    result.native_mip_search_effective = 0;
    result.native_mip_node_select_requested = 0;
    result.native_mip_node_select_set_return_code = -1;
    result.native_mip_node_select_get_return_code = -1;
    result.native_mip_node_select_effective = 0;
    result.native_mip_time_limit_set_return_code = -1;
    result.native_mip_time_limit_get_return_code = -1;
    result.native_mip_time_limit_effective_available = false;

    const ConnectivityFlowVariantResolution flow_resolution =
        resolveConnectivityFlowVariant(
            options.global_gini_tree_root_connectivity_flow,
            options.global_gini_tree_root_connectivity_flow_variant);
    result.global_gini_tree_root_connectivity_flow_variant_requested =
        flow_resolution.requested.empty() ? "invalid" : flow_resolution.requested;
    result.global_gini_tree_root_connectivity_flow_variant_resolved =
        flow_resolution.valid ? flow_resolution.resolved : "invalid";
    if (!flow_resolution.valid) {
        result.status = "global_gini_tree_invalid_connectivity_flow_variant";
        result.certificate =
            "Global Gini tree rejected an invalid or conflicting root connectivity-flow configuration.";
        result.global_gini_tree_fail_reason = flow_resolution.failure_reason;
        result.full_certificate_rejection_reason =
            "invalid_root_connectivity_flow_variant";
        result.runtime_seconds =
            std::chrono::duration<double>(Clock::now() - start).count();
        result.wall_time_seconds = result.runtime_seconds;
        return result;
    }
    const ConnectivityFlowCounts flow_counts =
        connectivityFlowTheoreticalCounts(
            flow_resolution.variant, instance.V, instance.M);
    if (!flow_counts.valid) {
        result.status = "global_gini_tree_invalid_connectivity_flow_counts";
        result.global_gini_tree_fail_reason = flow_counts.failure_reason;
        result.full_certificate_rejection_reason =
            "invalid_root_connectivity_flow_dimensions";
        result.runtime_seconds =
            std::chrono::duration<double>(Clock::now() - start).count();
        result.wall_time_seconds = result.runtime_seconds;
        return result;
    }
    result.global_gini_tree_connectivity_flow_columns = flow_counts.columns;
    result.global_gini_tree_connectivity_flow_upper_link_rows =
        flow_counts.upper_link_rows;
    result.global_gini_tree_connectivity_flow_lower_link_rows =
        flow_counts.lower_link_rows;
    result.global_gini_tree_connectivity_flow_station_balance_rows =
        flow_counts.station_balance_rows;
    result.global_gini_tree_connectivity_flow_depot_balance_rows =
        flow_counts.depot_balance_rows;
    result.global_gini_tree_connectivity_flow_start_upper_rows =
        flow_counts.start_upper_rows;
    result.global_gini_tree_connectivity_flow_start_lower_rows =
        flow_counts.start_lower_rows;
    result.global_gini_tree_connectivity_flow_total_rows =
        flow_counts.total_rows;
    result.global_gini_tree_connectivity_flow_total_nonzeros =
        flow_counts.total_nonzeros;

    if (!verified_seed.verification.feasible ||
        !verified_seed.verification.objective_matches ||
        !verified_seed.verification.errors.empty()) {
        result.status = "global_gini_tree_no_verified_incumbent";
        result.certificate =
            "Global Gini tree was not started because the same-run incumbent failed independent verification.";
        result.global_gini_tree_fail_reason = "same_run_incumbent_not_verified";
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.wall_time_seconds = result.runtime_seconds;
        return result;
    }
    if (root_gamma_L < -1e-12 || root_gamma_U < root_gamma_L - 1e-12 ||
        !result.frontier_covers_all_improving_gini_values) {
        result.status = "global_gini_tree_invalid_root_range";
        result.certificate =
            "Global Gini tree rejected a root interval that did not cover the complete improving Gini range.";
        result.global_gini_tree_fail_reason = "incomplete_or_invalid_root_range";
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.wall_time_seconds = result.runtime_seconds;
        return result;
    }
    if (options.compact_bc_root_cut_rounds > 0) {
        result.status = "global_gini_tree_unsupported_root_cut_loop";
        result.certificate =
            "Global Gini tree forbids preliminary repeated root solves; use the Round 18 static-no-callback profile with zero root cut rounds.";
        result.global_gini_tree_fail_reason = "root_cut_rounds_would_violate_single_mipopt_lifecycle";
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.wall_time_seconds = result.runtime_seconds;
        return result;
    }

    try {
        const auto run_id = std::chrono::duration_cast<std::chrono::milliseconds>(
            Clock::now().time_since_epoch()).count();
        const std::string stem = std::filesystem::path(instance.name).stem().string();
        const std::filesystem::path default_dir =
            std::filesystem::path("results") /
            "gf_global_gini_tree_feasibility_round" / "runs" /
            (stem + "_" + std::to_string(run_id));
        std::filesystem::create_directories(default_dir);
        const std::filesystem::path root_lp =
            options.global_gini_tree_root_export_path.empty()
                ? default_dir / "global_root.lp"
                : std::filesystem::path(options.global_gini_tree_root_export_path);
        const std::filesystem::path node_trace =
            options.global_gini_tree_node_trace_path.empty()
                ? default_dir / "global_node_trace.csv"
                : std::filesystem::path(options.global_gini_tree_node_trace_path);
        const std::filesystem::path bound_trace =
            options.global_gini_tree_bound_trace_path.empty()
                ? default_dir / "global_bound_trajectory.csv"
                : std::filesystem::path(options.global_gini_tree_bound_trace_path);
        const std::filesystem::path manifest =
            options.global_gini_tree_manifest_path.empty()
                ? default_dir / "model_lifecycle_manifest.csv"
                : std::filesystem::path(options.global_gini_tree_manifest_path);
        if (root_lp.has_parent_path()) {
            std::filesystem::create_directories(root_lp.parent_path());
        }

        SolveOptions model_options = options;
        model_options.interval_row_factory_round19 = true;
        auto defaultTrace = [&](const std::string& configured,
                                const std::string& filename) {
            return configured.empty()
                ? (default_dir / filename).string() : configured;
        };
        model_options.global_gini_tree_post_row_trace_path = defaultTrace(
            options.global_gini_tree_post_row_trace_path,
            "post_local_row_reoptimization.csv");
        model_options.global_gini_tree_topology_trace_path = defaultTrace(
            options.global_gini_tree_topology_trace_path,
            "gini_branch_topology.csv");
        model_options.global_gini_tree_sibling_trace_path = defaultTrace(
            options.global_gini_tree_sibling_trace_path,
            "gini_sibling_delay.csv");
        model_options.global_gini_tree_row_delta_trace_path = defaultTrace(
            options.global_gini_tree_row_delta_trace_path,
            "row_delta_trace.csv");
        model_options.global_gini_tree_memory_trace_path = defaultTrace(
            options.global_gini_tree_memory_trace_path,
            "tree_memory_trace.csv");
        model_options.global_gini_tree_mip_start_audit_path = defaultTrace(
            options.global_gini_tree_mip_start_audit_path,
            "native_mip_start_audit.csv");
        CompactIntervalCutoffConfig root_cutoff;
        root_cutoff.enabled = true;
        root_cutoff.gamma_L = root_gamma_L;
        root_cutoff.gamma_U = root_gamma_U;
        root_cutoff.add_objective_cutoff = true;
        root_cutoff.incumbent_ub = verified_seed.objective;
        root_cutoff.epsilon = 0.0;
        CompactOracleStrengtheningStats root_stats;
        writeCompactLp(instance, model_options, root_lp, true, &root_cutoff,
                       &root_stats, nullptr);
        const ModelSizeStats root_model_size = analyzeLpModel(root_lp);
        result.global_gini_tree_root_model_size_available =
            root_model_size.rows > 0 && root_model_size.cols > 0;
        result.global_gini_tree_root_model_rows = root_model_size.rows;
        result.global_gini_tree_root_model_cols = root_model_size.cols;
        result.global_gini_tree_root_model_nonzeros = root_model_size.nonzeros;

        const int solver_threads = options.compact_bc_threads > 0
            ? options.compact_bc_threads
            : (options.mip_threads > 0
                   ? options.mip_threads
                   : std::max(1, options.threads));
        const GlobalGiniTreeApiSolveResult api =
            solveGlobalGiniTreeWithTailoredBCCplexApi(
                root_lp, instance, model_options, root_gamma_L, root_gamma_U,
                verified_seed.objective, verified_seed.routes,
                options.solve_time_limit,
                solver_threads, node_trace, bound_trace, manifest);

        result.global_gini_tree_root_model_size_available =
            api.model_rows > 0 && api.model_columns > 0;
        result.global_gini_tree_root_model_rows = api.model_rows;
        result.global_gini_tree_root_model_cols = api.model_columns;
        result.global_gini_tree_root_model_nonzeros = api.model_nonzeros;
        if (root_model_size.rows != api.model_rows ||
            root_model_size.cols != api.model_columns ||
            root_model_size.nonzeros != api.model_nonzeros) {
            result.notes.push_back(
                "LP text analyzer differs from authoritative CPLEX model dimensions: text=" +
                std::to_string(root_model_size.rows) + "/" +
                std::to_string(root_model_size.cols) + "/" +
                std::to_string(root_model_size.nonzeros) + ", CPLEX=" +
                std::to_string(api.model_rows) + "/" +
                std::to_string(api.model_columns) + "/" +
                std::to_string(api.model_nonzeros));
        }

        result.global_gini_tree_available = api.available;
        result.global_gini_tree_solved = api.solved;
        result.global_gini_tree_return_code = api.return_code;
        result.global_gini_tree_status_code = api.status_code;
        result.global_gini_tree_solver_status = api.status;
        result.global_gini_tree_fail_reason = api.fail_reason;
        result.global_gini_tree_environment_count = api.environment_count;
        result.global_gini_tree_problem_count = api.problem_count;
        result.global_gini_tree_model_read_count = api.model_read_count;
        result.global_gini_tree_mipopt_count = api.mipopt_count;
        result.global_gini_tree_freeprob_count = api.freeprob_count;
        result.global_gini_tree_close_count = api.close_count;
        result.global_gini_tree_interval_oracle_count = api.interval_oracle_count;
        result.global_gini_tree_child_process_count = api.child_process_count;
        result.global_gini_tree_branch_callback_calls = api.branch_callback_calls;
        result.global_gini_tree_relaxation_callback_calls =
            api.relaxation_callback_calls;
        result.global_gini_tree_candidate_callback_calls =
            api.candidate_callback_calls;
        result.global_gini_tree_progress_callback_calls = api.progress_callback_calls;
        result.global_gini_tree_gini_branch_nodes = api.gini_branch_nodes;
        result.global_gini_tree_gini_children_created = api.gini_children_created;
        result.global_gini_tree_gini_branch_generations = api.gini_branch_generations;
        result.global_gini_tree_ordinary_branch_fallbacks = api.ordinary_branch_fallbacks;
        result.global_gini_tree_nonoptimal_relaxation_fallbacks =
            api.nonoptimal_relaxation_fallbacks;
        result.global_gini_tree_local_rows_attached = api.local_rows_attached;
        result.global_gini_tree_local_bound_changes_attached =
            api.local_bound_changes_attached;
        result.global_gini_tree_local_row_failures = api.local_row_failures;
        result.global_gini_tree_column_mapping_failures = api.column_mapping_failures;
        result.global_gini_tree_coverage_failures = api.coverage_failures;
        result.global_gini_tree_child_estimate_failures = api.child_estimate_failures;
        result.global_gini_tree_local_bound_api_failures = api.local_bound_api_failures;
        result.global_gini_tree_node_info_api_failures = api.node_info_api_failures;
        result.global_gini_tree_callback_failures = api.callback_failures;
        result.global_gini_tree_post_row_reoptimizations =
            api.post_row_reoptimizations;
        result.global_gini_tree_post_row_reoptimization_failures =
            api.post_row_reoptimization_failures;
        result.global_gini_tree_theoretical_full_rows =
            api.theoretical_full_rows;
        result.global_gini_tree_theoretical_full_bounds =
            api.theoretical_full_bounds;
        result.global_gini_tree_exact_duplicate_rows_omitted =
            api.exact_duplicate_rows_omitted;
        result.global_gini_tree_identical_bounds_omitted =
            api.identical_bounds_omitted;
        result.global_gini_tree_dominance_omissions = api.dominance_omissions;
        result.global_gini_tree_delta_rows_attached = api.delta_rows_attached;
        result.global_gini_tree_delta_bounds_attached = api.delta_bounds_attached;
        result.global_gini_tree_ordinary_branches_before_terminal_gini =
            api.ordinary_branches_before_terminal_gini;
        result.global_gini_tree_ordinary_branches_after_terminal_gini =
            api.ordinary_branches_after_terminal_gini;
        result.global_gini_tree_sibling_first_process_count =
            api.sibling_first_process_count;
        result.global_gini_tree_sibling_equal_estimate_pairs =
            api.sibling_equal_estimate_pairs;
        result.global_gini_tree_sibling_discriminated_pairs =
            api.sibling_discriminated_pairs;
        result.global_gini_tree_native_simplex_iterations =
            api.native_simplex_iterations;
        result.global_gini_tree_native_open_nodes = api.native_open_nodes;
        result.global_gini_tree_native_solution_pool_count =
            api.native_solution_pool_count;
        result.global_gini_tree_first_gini_branch_time =
            api.first_gini_branch_time;
        result.global_gini_tree_row_factory_seconds = api.row_factory_seconds;
        result.global_gini_tree_callback_packing_seconds =
            api.callback_packing_seconds;
        result.global_gini_tree_local_row_api_seconds =
            api.local_row_api_seconds;
        result.global_gini_tree_presolve_requested = api.presolve_requested;
        result.global_gini_tree_presolve_set_rc = api.presolve_set_rc;
        result.global_gini_tree_presolve_effective = api.presolve_effective;
        result.global_gini_tree_search_requested = api.search_requested;
        result.global_gini_tree_search_set_rc = api.search_set_rc;
        result.global_gini_tree_search_effective = api.search_effective;
        result.global_gini_tree_node_select_requested = api.node_select_requested;
        result.global_gini_tree_node_select_set_rc = api.node_select_set_rc;
        result.global_gini_tree_node_select_effective = api.node_select_effective;
        result.global_gini_tree_heuristics_effective = api.heuristics_effective;
        result.global_gini_tree_probing_effective = api.probing_effective;
        result.global_gini_tree_threads_effective = api.threads_effective;
        result.global_gini_tree_native_time_limit_set_rc =
            api.native_time_limit_set_rc;
        result.global_gini_tree_native_time_limit_seconds =
            api.native_time_limit_seconds;
        result.global_gini_tree_native_cuts_default = api.native_cuts_default;
        result.global_gini_tree_solver_finalization_reached =
            api.solver_finalization_reached;
        result.global_gini_tree_callback_abort_used = api.callback_abort_used;
        result.global_gini_tree_recursive_branching_complete =
            api.recursive_branching_complete;
        result.global_gini_tree_row_migration_complete = api.row_migration_complete;
        result.global_gini_tree_sibling_isolation_by_construction =
            api.sibling_isolation_by_construction;
        result.global_gini_tree_root_coverage_valid = api.root_coverage_valid;
        result.global_gini_tree_branch_coverage_valid = api.branch_coverage_valid;
        result.global_gini_tree_lifecycle_valid = api.lifecycle_valid;
        result.global_gini_tree_global_bound_monotone = api.global_bound_monotone;
        result.global_gini_tree_no_time_quantum = api.no_time_quantum;
        result.global_gini_tree_no_instance_special_case = api.no_instance_special_case;
        result.global_gini_tree_native_mip_start_attempted =
            api.native_mip_start_attempted;
        result.global_gini_tree_native_mip_start_mapping_complete =
            api.native_mip_start_mapping_complete;
        result.global_gini_tree_native_mip_start_submitted =
            api.native_mip_start_submitted;
        result.global_gini_tree_native_mip_start_stored =
            api.native_mip_start_stored;
        result.global_gini_tree_native_mip_start_accepted =
            api.native_mip_start_accepted;
        result.global_gini_tree_native_mip_start_return_code =
            api.native_mip_start_return_code;
        result.global_gini_tree_native_mip_start_stored_count =
            api.native_mip_start_stored_count;
        result.global_gini_tree_native_mip_start_failure_reason =
            api.native_mip_start_failure_reason;
        result.global_gini_tree_child_estimate_mode = api.child_estimate_mode;
        result.global_gini_tree_row_attachment_mode = api.row_attachment_mode;
        result.global_gini_tree_row_timing_mode = api.row_timing_mode;
        result.global_gini_tree_native_cut_counts = api.native_cut_counts;
        result.global_gini_tree_native_best_bound_available = api.best_bound_available;
        result.global_gini_tree_native_objective = api.objective;
        result.global_gini_tree_native_best_bound = api.best_bound;
        result.global_gini_tree_row_factory_version = api.row_factory_version;
        result.global_gini_tree_root_model_fingerprint =
            api.root_model_fingerprint;
        result.global_gini_tree_objective_fingerprint =
            api.objective_fingerprint;
        result.global_gini_tree_root_row_signature = api.root_row_signature;
        result.global_gini_tree_root_model_path = root_lp.string();
        result.global_gini_tree_node_trace_path = node_trace.string();
        result.global_gini_tree_bound_trace_path = bound_trace.string();
        result.global_gini_tree_manifest_path = manifest.string();
        result.global_gini_tree_post_row_trace_path = api.post_row_trace_path;
        result.global_gini_tree_topology_trace_path = api.topology_trace_path;
        result.global_gini_tree_sibling_trace_path = api.sibling_trace_path;
        result.global_gini_tree_row_delta_trace_path = api.row_delta_trace_path;
        result.global_gini_tree_memory_trace_path = api.memory_trace_path;
        result.global_gini_tree_mip_start_audit_path = api.mip_start_audit_path;
        result.nodes = api.node_count;
        result.solver_finalization_reached = api.solver_finalization_reached;
        result.process_return_code = api.native.mipopt_return_code;

        populateNativeMipEvidenceFields(
            result, api.native, api.environment_count, api.problem_count,
            api.model_read_count, api.mipopt_count, api.freeprob_count,
            api.close_count, api.node_count, api.native_open_nodes,
            static_cast<int>(api.native_solution_pool_count));
        result.native_mip_threads_requested = api.threads_requested;
        result.native_mip_threads_set_return_code = api.threads_set_rc;
        result.native_mip_threads_get_return_code = api.threads_get_rc;
        result.native_mip_threads_effective = api.threads_effective;
        result.native_mip_presolve_requested = api.presolve_requested;
        result.native_mip_presolve_set_return_code = api.presolve_set_rc;
        result.native_mip_presolve_get_return_code = api.presolve_get_rc;
        result.native_mip_presolve_effective = api.presolve_effective;
        result.native_mip_search_requested = api.search_requested;
        result.native_mip_search_set_return_code = api.search_set_rc;
        result.native_mip_search_get_return_code = api.search_get_rc;
        result.native_mip_search_effective = api.search_effective;
        result.native_mip_node_select_requested = api.node_select_requested;
        result.native_mip_node_select_set_return_code = api.node_select_set_rc;
        result.native_mip_node_select_get_return_code = api.node_select_get_rc;
        result.native_mip_node_select_effective = api.node_select_effective;
        result.native_mip_time_limit_param_id = 1039;
        result.native_mip_time_limit_requested =
            api.native_time_limit_requested;
        result.native_mip_time_limit_set_return_code =
            api.native_time_limit_set_rc;
        result.native_mip_time_limit_get_return_code =
            api.native_time_limit_get_rc;
        result.native_mip_time_limit_effective_available =
            api.native_time_limit_get_rc == 0;
        result.native_mip_time_limit_effective =
            api.native_time_limit_effective;

        bool native_candidate_feasible = false;
        bool native_candidate_objective_consistent = false;
        double native_candidate_objective = 0.0;
        if (api.native.objective_available && !api.values.empty()) {
            const std::vector<RoutePlan> candidate_routes =
                reconstructRoutes(instance, api.values);
            const Verification candidate =
                verifySolution(instance, candidate_routes, options.lambda);
            native_candidate_feasible = candidate.feasible &&
                candidate.objective_matches && candidate.errors.empty() &&
                std::isfinite(candidate.objective);
            native_candidate_objective = candidate.objective;
            native_candidate_objective_consistent =
                native_candidate_feasible &&
                std::fabs(candidate.objective - api.native.objective) <=
                    1e-8 * std::max({1.0, std::fabs(candidate.objective),
                                     std::fabs(api.native.objective)});
            if (native_candidate_objective_consistent &&
                candidate.objective <= result.objective +
                    1e-8 * std::max({1.0, std::fabs(candidate.objective),
                                     std::fabs(result.objective)})) {
                result.routes = candidate_routes;
                result.verification = candidate;
                result.final_inventory = candidate.final_inventory;
                result.G = candidate.G;
                result.P = candidate.P;
                result.objective = candidate.objective;
                result.upper_bound = candidate.objective;
            } else {
                result.notes.push_back(
                    "global Gini tree native incumbent was rejected by the independent original-solution verifier or objective consistency check");
            }
        }
        const bool retained_incumbent_feasible =
            result.verification.feasible &&
            result.verification.objective_matches &&
            result.verification.errors.empty() &&
            std::isfinite(result.objective);
        const bool retained_objective_consistent =
            retained_incumbent_feasible && api.native.objective_available &&
            std::fabs(result.objective - api.native.objective) <=
                1e-8 * std::max({1.0, std::fabs(result.objective),
                                 std::fabs(api.native.objective)});
        result.global_gini_tree_incumbent_verified =
            native_candidate_feasible &&
            native_candidate_objective_consistent;
        if (api.native.best_bound_available) {
            result.lower_bound = api.native.best_bound;
        }

        const bool exactness_lifecycle_complete =
            api.solved && api.lifecycle_valid &&
            api.native.mipopt_return_code == 0 &&
            api.solver_finalization_reached &&
            api.recursive_branching_complete && api.row_migration_complete &&
            api.sibling_isolation_by_construction && api.root_coverage_valid &&
            api.branch_coverage_valid && !api.callback_abort_used &&
            api.callback_failures == 0 && api.coverage_failures == 0 &&
            api.column_mapping_failures == 0;
        const StrictCertificateDecision decision =
            evaluateAndPopulateStrictCertificate(
                result, api.native, retained_incumbent_feasible,
                result.objective, retained_incumbent_feasible,
                retained_objective_consistent,
                exactness_lifecycle_complete);
        if (decision.verified_gap_available) {
            result.gap = decision.verified_project_relative_gap;
        }
        result.strict_serialized_lower_bound_matches_native =
            api.native.best_bound_available &&
            result.lower_bound == api.native.best_bound;
        result.strict_serialized_gap_consistent =
            decision.verified_gap_available &&
            result.gap == decision.verified_project_relative_gap;
        result.global_gini_tree_optimality_accepted =
            decision.strict_certified_original_problem;

        {
            std::ofstream manifest_out(manifest, std::ios::app);
            if (manifest_out) {
                manifest_out
                    << "root_connectivity_flow_variant_requested,"
                    << flow_resolution.requested << '\n'
                    << "root_connectivity_flow_variant_resolved,"
                    << flow_resolution.resolved << '\n'
                    << "lp_text_analyzer_rows," << root_model_size.rows << '\n'
                    << "lp_text_analyzer_columns," << root_model_size.cols << '\n'
                    << "lp_text_analyzer_nonzeros," << root_model_size.nonzeros << '\n'
                    << "connectivity_flow_columns," << flow_counts.columns << '\n'
                    << "connectivity_flow_upper_link_rows,"
                    << flow_counts.upper_link_rows << '\n'
                    << "connectivity_flow_lower_link_rows,"
                    << flow_counts.lower_link_rows << '\n'
                    << "connectivity_flow_station_balance_rows,"
                    << flow_counts.station_balance_rows << '\n'
                    << "connectivity_flow_depot_balance_rows,"
                    << flow_counts.depot_balance_rows << '\n'
                    << "connectivity_flow_start_upper_rows,"
                    << flow_counts.start_upper_rows << '\n'
                    << "connectivity_flow_start_lower_rows,"
                    << flow_counts.start_lower_rows << '\n'
                    << "connectivity_flow_total_rows,"
                    << flow_counts.total_rows << '\n'
                    << "connectivity_flow_total_nonzeros,"
                    << flow_counts.total_nonzeros << '\n';
            }
        }

        if (decision.strict_certified_original_problem) {
            result.status = "optimal";
            result.unresolved_intervals = 0;
            result.full_certificate_all_intervals_accounted = true;
            result.full_certificate_rejection_reason = "none";
            result.compact_bc_certificate_valid = true;
            result.certificate =
                "Strict Round 21 global-tree certificate: native CPLEX status 101, zero relative/absolute gap parameter round trips, retained raw best bound, one-problem lifecycle and coverage audits, and an independently verified native incumbent all passed.";
        } else if (!api.solved) {
            result.status = "global_gini_tree_error";
            result.full_certificate_rejection_reason = api.fail_reason.empty()
                ? "global_tree_api_solve_failed" : api.fail_reason;
            result.certificate =
                "Global Gini tree did not produce a usable solver-final result: " +
                result.full_certificate_rejection_reason;
        } else {
            result.status = decision.certificate_class == "time_limit_valid_bound"
                ? "global_gini_tree_time_limit"
                : "global_gini_tree_not_certified";
            result.full_certificate_rejection_reason =
                decision.rejection_reason.empty()
                    ? decision.certificate_class
                    : decision.rejection_reason;
            result.certificate = api.native.best_bound_available
                ? "The one persistent CPLEX tree returned a raw native solver-final lower bound, but strict original-problem optimality was rejected as " +
                    decision.certificate_class + "."
                : "The one persistent CPLEX tree did not return a native solver-final best bound; no official lower-bound row may be synthesized.";
        }
        result.notes.push_back("global Gini tree root model: " + root_lp.string());
        result.notes.push_back("global Gini tree native CPLEX status code/text: " +
            std::to_string(api.native.status_code) + " / " +
            api.native.status_text);
        result.notes.push_back("global Gini tree strict certificate class: " +
            decision.certificate_class);
        if (native_candidate_feasible) {
            result.notes.push_back("verified native candidate objective: " +
                num(native_candidate_objective));
        }
    } catch (const std::exception& error) {
        result.status = "global_gini_tree_error";
        result.global_gini_tree_fail_reason = error.what();
        result.full_certificate_rejection_reason =
            "exception_before_native_global_tree_finalization";
        result.certificate =
            std::string("Global Gini tree failed: ") + error.what();
    }
    result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    result.actual_runtime_seconds = result.runtime_seconds;
    return result;
}

} // namespace ebrp
