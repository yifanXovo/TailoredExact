#include "CplexBaseline.hpp"

#include "Evaluator.hpp"
#include "Logger.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
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
    long long transfer_compat = 0;
    long long visit_inventory_linking = 0;
    long long objective_estimator = 0;
    long long receiver_source_cover = 0;
    long long total = 0;
    double support_duration_violation = 0.0;
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
    ss << std::setprecision(12) << v;
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

    for (int k = 0; k < M; ++k) {
        for (int i = 0; i <= V; ++i) {
            for (int j = 0; j <= V; ++j) {
                if (i != j) vars.add(xName(k, i, j), 0, 1, "B");
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

    std::filesystem::create_directories(lp_path.parent_path());
    std::ofstream out(lp_path);
    if (!out) throw std::runtime_error("Cannot write CPLEX LP: " + lp_path.string());
    out << std::setprecision(12);
    out << "\\ ExactEBRP compact MILP generated from C++ command-line runner\n";
    out << "Minimize\n obj: G";
    for (int i = 1; i <= V; ++i) {
        const double coef = options.lambda * instance.weights[i];
        if (coef >= 0) out << " + " << num(coef) << " " << eName(i);
        else out << " - " << num(-coef) << " " << eName(i);
    }
    out << "\nSubject To\n";

    int cid = 1;
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
    if (strengthened && options.required_movement_cuts) {
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
    if (strengthened && cutoff != nullptr && cutoff->enabled &&
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
    if (strengthened && cutoff != nullptr && cutoff->enabled &&
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
    if (add_low_gini_centering) {
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
            if (strengthened && cutoff != nullptr && cutoff->enabled &&
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
        Expr gl; addTerm(gl, "G", 1);
        writeConstraint(out, cid, gl, ">=", cutoff->gamma_L);
        Expr gu; addTerm(gu, "G", 1);
        writeConstraint(out, cid, gu, "<=", cutoff->gamma_U);
        if (cutoff->add_objective_cutoff) {
            Expr obj_cutoff; addTerm(obj_cutoff, "G", 1);
            for (int i = 1; i <= V; ++i) {
                addTerm(obj_cutoff, eName(i), options.lambda * instance.weights[i]);
            }
            writeConstraint(out, cid, obj_cutoff, "<=", cutoff->incumbent_ub - cutoff->epsilon);
        }
        const double cutoff_value = cutoff->incumbent_ub - cutoff->epsilon;
        double s_upper = 0.0;
        for (int i = 1; i <= V; ++i) {
            s_upper += static_cast<double>(y_ub[i]) / instance.target[i];
        }
        if (strengthened && options.compact_bc_objective_estimator_cutoff &&
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
        if (strengthened && options.compact_bc_penalty_lb_closure) {
            double penalty_lb = 0.0;
            for (int i = 1; i <= V; ++i) {
                double e_lb = 0.0;
                if (y_ub[i] < instance.target[i]) {
                    e_lb = 1.0 - static_cast<double>(y_ub[i]) / instance.target[i];
                } else if (y_lb[i] > instance.target[i]) {
                    e_lb = static_cast<double>(y_lb[i]) / instance.target[i] - 1.0;
                }
                penalty_lb += instance.weights[i] * std::max(0.0, e_lb);
            }
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

        if ((options.interval_oracle_penalty_domain_tightening ||
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
        << ";transfer_compat=" << stats.transfer_compat
        << ";visit_inventory_linking=" << stats.visit_inventory_linking
        << ";objective_estimator=" << stats.objective_estimator
        << ";receiver_source_cover=" << stats.receiver_source_cover;
    return out.str();
}

std::string dynamicViolationSummary(const DynamicCutStats& stats) {
    std::ostringstream out;
    out << "support_duration=" << stats.support_duration_violation
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

} // namespace

SolveResult solveCplexBaseline(const Instance& instance, const SolveOptions& options) {
    const auto start = Clock::now();
    SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "cplex";
    result.status = "running";
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
        const std::filesystem::path sol_path = work_dir / "solution.sol";
        const std::filesystem::path cmd_path = work_dir / "run.cplex";
        const std::filesystem::path cplex_log = options.log_path.empty()
            ? (work_dir / "cplex.log") : std::filesystem::path(options.log_path);
        result.log_file = cplex_log.string();
        result.notes.push_back("CPLEX command file sets threads="
            + std::to_string(effective_cplex_threads)
            + "; plain CPLEX rows are fair single-thread rows only when --cplex-threads 1 is used.");
        std::error_code ignored;
        std::filesystem::remove(sol_path, ignored);
        std::filesystem::remove(cplex_log, ignored);

        writeCompactLp(instance, options, lp_path, strengthened);

        std::ofstream cmd(cmd_path);
        cmd << "set threads " << effective_cplex_threads << "\n";
        cmd << "set timelimit " << options.solve_time_limit << "\n";
        cmd << "set mip tolerances mipgap 1e-8\n";
        cmd << "read " << lp_path.string() << "\n";
        cmd << "optimize\n";
        cmd << "write " << sol_path.string() << "\n";
        cmd << "quit\n";
        cmd.close();

        std::string solver_name = options.mip_solver.empty()
            ? "cplex" : options.mip_solver;
        std::transform(solver_name.begin(), solver_name.end(), solver_name.begin(),
                       [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
        if (solver_name != "cplex") {
            throw std::runtime_error("compact interval BC currently supports --mip-solver cplex only");
        }
        const std::string cplex = defaultCplexPath();
        std::filesystem::create_directories(cplex_log.parent_path());
        const std::string command = "cmd /C \"" + quote(cplex) + " -f "
            + quote(cmd_path) + " > " + quote(cplex_log) + " 2>&1\"";
        const int rc = std::system(command.c_str());
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.actual_runtime_seconds = result.runtime_seconds;

        std::string cplex_status = "unknown";
        double cplex_obj = 0.0;
        double best_bound = std::numeric_limits<double>::quiet_NaN();
        auto values = parseSolValues(sol_path, cplex_status, cplex_obj, best_bound);
        result.nodes = parseCplexNodes(cplex_log);
        const double log_best_bound = parseCplexBestBound(cplex_log);
        if (!std::isfinite(best_bound) && std::isfinite(log_best_bound)) best_bound = log_best_bound;
        result.routes = reconstructRoutes(instance, values);
        result.verification = verifySolution(instance, result.routes, options.lambda);
        result.final_inventory = result.verification.final_inventory;
        result.G = result.verification.G;
        result.P = result.verification.P;
        result.objective = result.verification.objective;
        result.upper_bound = result.objective;
        if (statusIsOptimal(cplex_status)) {
            result.status = result.verification.feasible ? "optimal" : "verification_failed";
            result.lower_bound = result.objective;
            result.gap = 0.0;
            result.certificate = result.verification.feasible
                ? "CPLEX reported optimality and the independent verifier recomputed the same feasible objective."
                : "CPLEX reported optimality, but the independent verifier rejected the reconstructed solution.";
        } else {
            result.status = "not_certified";
            result.lower_bound = std::isfinite(best_bound) ? best_bound : 0.0;
            result.gap = (std::fabs(result.upper_bound) > 1e-12)
                ? std::max(0.0, (result.upper_bound - result.lower_bound) / std::fabs(result.upper_bound))
                : 0.0;
            result.certificate = "CPLEX did not report optimality: " + cplex_status;
        }
        result.notes.push_back("CPLEX solution status: " + cplex_status);
        result.notes.push_back("CPLEX process return code: " + std::to_string(rc));
        result.notes.push_back("LP file: " + lp_path.string());
        result.notes.push_back("CPLEX log: " + cplex_log.string());
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
        result.compact_bc_root_cut_rounds = model_options.compact_bc_root_cut_rounds;
        result.compact_bc_root_cut_time_limit = model_options.compact_bc_root_cut_time_limit;
        result.compact_bc_dynamic_cut_families = model_options.compact_bc_dynamic_cut_families;
        result.compact_bc_root_probe = model_options.compact_bc_root_probe;
        result.compact_bc_domain_propagation_mode =
            model_options.compact_bc_domain_propagation_mode;
        result.compact_bc_domain_propagation_rounds =
            model_options.compact_bc_domain_propagation_rounds;
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
        const int rc = std::system(command.c_str());
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.actual_runtime_seconds = result.runtime_seconds;
        result.interval_exact_cutoff_runtime_seconds = result.runtime_seconds;
        result.compact_bc_time_seconds = result.runtime_seconds;
        result.compact_bc_total_solver_time = result.runtime_seconds;

        std::string cplex_status = "unknown";
        double cplex_obj = std::numeric_limits<double>::quiet_NaN();
        double best_bound = std::numeric_limits<double>::quiet_NaN();
        std::unordered_map<std::string, double> values;
        if (std::filesystem::exists(sol_path)) {
            values = parseSolValues(sol_path, cplex_status, cplex_obj, best_bound);
        } else {
            cplex_status = parseCplexTerminalStatus(cplex_log);
            if (cplex_status == "unknown") {
                cplex_status = (rc == 0) ? "no solution file" : "cplex process failed";
            }
        }
        result.interval_exact_cutoff_solver_status = cplex_status;
        result.compact_bc_solver_status = cplex_status;
        result.nodes = parseCplexNodes(cplex_log);
        result.interval_exact_cutoff_nodes = result.nodes;
        result.compact_bc_nodes = result.nodes;
        const double log_best_bound = parseCplexBestBound(cplex_log);
        if (!std::isfinite(best_bound) && std::isfinite(log_best_bound)) best_bound = log_best_bound;
        result.interval_exact_cutoff_best_bound = std::isfinite(best_bound) ? best_bound : 0.0;
        result.interval_exact_cutoff_objective = std::isfinite(cplex_obj) ? cplex_obj : 0.0;
        result.interval_oracle_solver_best_bound = result.interval_exact_cutoff_best_bound;
        result.interval_oracle_solver_incumbent = result.interval_exact_cutoff_objective;
        result.compact_bc_best_bound = result.interval_exact_cutoff_best_bound;
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
            result.status = statusIsTimeLimited(cplex_status) ? "interval_unresolved_timeout" : "interval_unresolved";
            result.interval_exact_cutoff_timeout = statusIsTimeLimited(cplex_status);
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
        }
        result.compact_interval_bc_bound_valid = result.interval_oracle_bound_valid;
        result.compact_bc_bound_valid = result.interval_oracle_bound_valid;
        result.compact_interval_bc_bound_scope = result.interval_oracle_bound_scope;
        result.compact_bc_bound_scope = result.interval_oracle_bound_scope;
        result.oracle_strengthening_lb_improvement =
            std::max(0.0, result.lower_bound - options.interval_exact_cutoff_gamma_L);
        result.notes.push_back("CPLEX solution status: " + cplex_status);
        result.notes.push_back("CPLEX process return code: " + std::to_string(rc));
        result.notes.push_back("LP file: " + lp_path.string());
        result.notes.push_back("CPLEX log: " + cplex_log.string());
    } catch (const std::exception& e) {
        result.status = "error";
        result.interval_exact_cutoff_certificate_basis = "interval_exact_cutoff_mip_error";
        result.certificate = std::string("Interval exact cutoff oracle failed: ") + e.what();
        result.compact_interval_bc_rejection_reason = result.certificate;
        result.compact_bc_rejection_reason = result.certificate;
        result.compact_interval_bc_bound_valid = false;
        result.compact_bc_bound_valid = false;
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.interval_exact_cutoff_runtime_seconds = result.runtime_seconds;
        result.compact_bc_time_seconds = result.runtime_seconds;
    }
    return result;
}

} // namespace ebrp
