#include "Bounds.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <functional>
#include <limits>
#include <iomanip>
#include <regex>
#include <sstream>
#include <thread>
#include <unordered_map>
#include <vector>

namespace ebrp {
namespace {

std::string num(double v) {
    std::ostringstream ss;
    ss << std::setprecision(12) << v;
    return ss.str();
}

std::string quote(const std::filesystem::path& p) {
    return "\"" + p.string() + "\"";
}

std::string defaultCplexPath() {
    const char* env = std::getenv("CPLEX_BIN");
    if (env != nullptr) {
        std::filesystem::path p = std::filesystem::path(env) / "cplex.exe";
        if (std::filesystem::exists(p)) return p.string();
    }
    for (const char* s : {
             "C:/Program Files/IBM/ILOG/CPLEX_Studio2211/cplex/bin/x64_win64",
             "C:/Program Files/IBM/ILOG/CPLEX_Studio2212/cplex/bin/x64_win64",
             "C:/Program Files/IBM/ILOG/CPLEX_Studio221/cplex/bin/x64_win64"}) {
        std::filesystem::path p = std::filesystem::path(s) / "cplex.exe";
        if (std::filesystem::exists(p)) return p.string();
    }
    return "cplex.exe";
}

bool statusIsOptimal(const std::string& status) {
    std::string s = status;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return s.find("optimal") != std::string::npos;
}

bool statusIsInfeasible(const std::string& status) {
    std::string s = status;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return s.find("infeasible") != std::string::npos;
}

bool logSaysInfeasible(const std::filesystem::path& log_path) {
    std::ifstream in(log_path);
    if (!in) return false;
    std::ostringstream ss;
    ss << in.rdbuf();
    std::string text = ss.str();
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return text.find("infeasible") != std::string::npos;
}

double parseObjective(const std::filesystem::path& sol_path, std::string& status) {
    std::ifstream in(sol_path);
    if (!in) return std::numeric_limits<double>::quiet_NaN();
    std::ostringstream ss;
    ss << in.rdbuf();
    const std::string text = ss.str();
    std::smatch m;
    if (std::regex_search(text, m, std::regex("solutionStatusString=\"([^\"]*)\""))) {
        status = m[1].str();
    }
    if (std::regex_search(text, m, std::regex("objectiveValue=\"([^\"]*)\""))) {
        return std::stod(m[1].str());
    }
    return std::numeric_limits<double>::quiet_NaN();
}

double parseMipBestBound(const std::filesystem::path& log_path) {
    std::ifstream in(log_path);
    if (!in) return std::numeric_limits<double>::quiet_NaN();
    std::ostringstream ss;
    ss << in.rdbuf();
    const std::string text = ss.str();
    std::smatch m;
    double bound = std::numeric_limits<double>::quiet_NaN();
    const std::regex current_bound(
        "Current MIP best bound\\s*=\\s*([-+0-9.eE]+)");
    auto begin = std::sregex_iterator(text.begin(), text.end(), current_bound);
    auto end = std::sregex_iterator();
    for (auto it = begin; it != end; ++it) {
        bound = std::stod((*it)[1].str());
    }
    return bound;
}

double ratioSumUpperBoundForInventoryRelaxation(
    const Instance& instance,
    double penalty_budget = std::numeric_limits<double>::infinity(),
    int min_station_bikes = 0) {
    int total_bikes = 0;
    for (int i = 1; i <= instance.V; ++i) total_bikes += instance.initial[i];
    min_station_bikes = std::max(0, std::min(min_station_bikes, total_bikes));

    auto greedyConservationBound = [&]() {
        struct Slot {
            double ratio_per_bike = 0.0;
            int capacity = 0;
        };
        std::vector<Slot> slots;
        for (int i = 1; i <= instance.V; ++i) {
            slots.push_back(Slot{
                1.0 / static_cast<double>(instance.target[i]),
                std::max(0, instance.capacity[i])
            });
        }
        std::sort(slots.begin(), slots.end(), [](const Slot& a, const Slot& b) {
            return a.ratio_per_bike > b.ratio_per_bike;
        });
        int remaining = total_bikes;
        double s_upper = 0.0;
        for (const Slot& slot : slots) {
            if (remaining <= 0) break;
            const int take = std::min(remaining, slot.capacity);
            s_upper += static_cast<double>(take) * slot.ratio_per_bike;
            remaining -= take;
        }
        return std::max(s_upper, 1e-9);
    };

    if (!std::isfinite(penalty_budget)) return greedyConservationBound();
    if (penalty_budget < -1e-9) return 1e-9;
    if (total_bikes > 2000) return greedyConservationBound();

    std::vector<std::vector<std::pair<double, double>>> states(total_bikes + 1);
    states[0].push_back({0.0, 0.0});
    constexpr double eps = 1e-9;
    for (int i = 1; i <= instance.V; ++i) {
        std::vector<std::vector<std::pair<double, double>>> next(total_bikes + 1);
        for (int used = 0; used <= total_bikes; ++used) {
            if (states[used].empty()) continue;
            const int max_y = std::min(instance.capacity[i], total_bikes - used);
            for (const auto& state : states[used]) {
                for (int y = 0; y <= max_y; ++y) {
                    const double ratio = static_cast<double>(y) /
                        static_cast<double>(instance.target[i]);
                    const double penalty = state.first +
                        instance.weights[i] * std::fabs(ratio - 1.0);
                    if (penalty > penalty_budget + eps) continue;
                    next[used + y].push_back({penalty, state.second + ratio});
                }
            }
        }
        for (auto& bucket : next) {
            if (bucket.size() <= 1) continue;
            std::sort(bucket.begin(), bucket.end(),
                      [](const auto& a, const auto& b) {
                          if (std::fabs(a.first - b.first) > 1e-12) return a.first < b.first;
                          return a.second > b.second;
                      });
            std::vector<std::pair<double, double>> pruned;
            double best_s = -std::numeric_limits<double>::infinity();
            for (const auto& state : bucket) {
                if (state.second > best_s + 1e-10) {
                    pruned.push_back(state);
                    best_s = state.second;
                }
            }
            bucket.swap(pruned);
        }
        states.swap(next);
    }

    double best = -std::numeric_limits<double>::infinity();
    for (int used = min_station_bikes; used <= total_bikes; ++used) {
        for (const auto& state : states[used]) {
            if (state.first <= penalty_budget + eps) {
                best = std::max(best, state.second);
            }
        }
    }
    if (!std::isfinite(best)) return 1e-9;
    return std::max(best, 1e-9);
}

std::string yName(int i) { return "yb_" + std::to_string(i); }
std::string pName(int i) { return "pb_" + std::to_string(i); }
std::string dName(int i) { return "db_" + std::to_string(i); }
std::string vName(int i) { return "vb_" + std::to_string(i); }
std::string modeName(int i) { return "mb_" + std::to_string(i); }
std::string rName(int i) { return "rb_" + std::to_string(i); }
std::string eName(int i) { return "eb_" + std::to_string(i); }
std::string routeMaskName(int vehicle, int mask) {
    return "zmb_" + std::to_string(vehicle) + "_" + std::to_string(mask);
}
std::string routePickupName(int vehicle, int station) {
    return "pkb_" + std::to_string(vehicle) + "_" + std::to_string(station);
}
std::string routeDropName(int vehicle, int station) {
    return "dkb_" + std::to_string(vehicle) + "_" + std::to_string(station);
}
std::string routeVisitName(int vehicle, int station) {
    return "ykb_" + std::to_string(vehicle) + "_" + std::to_string(station);
}
std::string transferName(int pickup_station, int drop_station) {
    return "f_" + std::to_string(pickup_station) + "_" +
           std::to_string(drop_station);
}
std::string unloadName(int pickup_station) {
    return "hu_" + std::to_string(pickup_station);
}
std::string vehicleTransferName(int vehicle, int pickup_station, int drop_station) {
    return "fkb_" + std::to_string(vehicle) + "_" +
           std::to_string(pickup_station) + "_" +
           std::to_string(drop_station);
}
std::string vehicleUnloadName(int vehicle, int pickup_station) {
    return "hukb_" + std::to_string(vehicle) + "_" +
           std::to_string(pickup_station);
}
std::string hName(int i, int j) {
    return "hb_" + std::to_string(i) + "_" + std::to_string(j);
}

std::vector<std::vector<double>> metricClosure(const Instance& instance) {
    std::vector<std::vector<double>> d = instance.dist;
    const int n = static_cast<int>(d.size());
    for (int k = 0; k < n; ++k) {
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                d[i][j] = std::min(d[i][j], d[i][k] + d[k][j]);
            }
        }
    }
    return d;
}

double routeCycleLength(const std::vector<std::vector<double>>& d, int station_mask, int V) {
    if (station_mask == 0) return 0.0;
    std::vector<int> stations;
    for (int i = 1; i <= V; ++i) {
        if (station_mask & (1 << (i - 1))) stations.push_back(i);
    }
    std::sort(stations.begin(), stations.end());
    double best = std::numeric_limits<double>::infinity();
    do {
        double travel = 0.0;
        int last = 0;
        for (int station : stations) {
            travel += d[last][station];
            last = station;
        }
        travel += d[last][0];
        best = std::min(best, travel);
    } while (std::next_permutation(stations.begin(), stations.end()));
    return std::isfinite(best) ? best : 0.0;
}

int popcountMask(int mask) {
    int count = 0;
    while (mask != 0) {
        mask &= (mask - 1);
        ++count;
    }
    return count;
}

double partitionTravelLowerBound(const std::vector<std::vector<double>>& d,
                                 int station_mask,
                                 int V,
                                 int M) {
    if (station_mask == 0) return 0.0;
    const int max_mask = 1 << V;
    const double inf = std::numeric_limits<double>::infinity();
    std::vector<double> route_cost(max_mask, inf);
    route_cost[0] = 0.0;
    for (int sub = station_mask; sub; sub = (sub - 1) & station_mask) {
        route_cost[sub] = routeCycleLength(d, sub, V);
    }
    std::vector<double> dp(max_mask, inf), next(max_mask, inf);
    dp[0] = 0.0;
    for (int k = 0; k < std::max(1, M); ++k) {
        next = dp;
        for (int mask = 0; mask < max_mask; ++mask) {
            if (!std::isfinite(dp[mask])) continue;
            const int remaining = station_mask & ~mask;
            for (int sub = remaining; sub; sub = (sub - 1) & remaining) {
                next[mask | sub] = std::min(next[mask | sub], dp[mask] + route_cost[sub]);
            }
        }
        dp.swap(next);
    }
    return std::isfinite(dp[station_mask]) ? dp[station_mask] : 0.0;
}

std::vector<double> allPartitionTravelLowerBounds(
    const std::vector<std::vector<double>>& d,
    int V,
    int M) {
    const int max_mask = 1 << V;
    const double inf = std::numeric_limits<double>::infinity();
    std::vector<std::vector<double>> path(max_mask, std::vector<double>(V, inf));
    for (int i = 1; i <= V; ++i) {
        path[1 << (i - 1)][i - 1] = d[0][i];
    }
    for (int mask = 1; mask < max_mask; ++mask) {
        for (int last = 1; last <= V; ++last) {
            const int last_bit = 1 << (last - 1);
            if (!(mask & last_bit) || !std::isfinite(path[mask][last - 1])) continue;
            const int remaining = ((max_mask - 1) ^ mask);
            for (int next = 1; next <= V; ++next) {
                const int next_bit = 1 << (next - 1);
                if (!(remaining & next_bit)) continue;
                const int next_mask = mask | next_bit;
                path[next_mask][next - 1] = std::min(
                    path[next_mask][next - 1],
                    path[mask][last - 1] + d[last][next]);
            }
        }
    }

    std::vector<double> cycle(max_mask, inf);
    cycle[0] = 0.0;
    for (int mask = 1; mask < max_mask; ++mask) {
        for (int last = 1; last <= V; ++last) {
            if (!(mask & (1 << (last - 1)))) continue;
            if (std::isfinite(path[mask][last - 1])) {
                cycle[mask] = std::min(cycle[mask], path[mask][last - 1] + d[last][0]);
            }
        }
    }

    std::vector<double> best(max_mask, inf);
    best[0] = 0.0;
    for (int vehicle = 0; vehicle < std::max(1, M); ++vehicle) {
        std::vector<double> next = best;
        for (int mask = 0; mask < max_mask; ++mask) {
            if (!std::isfinite(best[mask])) continue;
            const int remaining = (max_mask - 1) ^ mask;
            for (int sub = remaining; sub; sub = (sub - 1) & remaining) {
                if (!std::isfinite(cycle[sub])) continue;
                next[mask | sub] = std::min(next[mask | sub], best[mask] + cycle[sub]);
            }
        }
        best.swap(next);
    }
    for (double& value : best) {
        if (!std::isfinite(value)) value = 0.0;
    }
    return best;
}

std::vector<double> allRouteCycleLowerBounds(const std::vector<std::vector<double>>& d,
                                             int V) {
    const int max_mask = 1 << V;
    const double inf = std::numeric_limits<double>::infinity();
    std::vector<std::vector<double>> path(max_mask, std::vector<double>(V, inf));
    for (int i = 1; i <= V; ++i) {
        path[1 << (i - 1)][i - 1] = d[0][i];
    }
    for (int mask = 1; mask < max_mask; ++mask) {
        for (int last = 1; last <= V; ++last) {
            const int last_bit = 1 << (last - 1);
            if (!(mask & last_bit) || !std::isfinite(path[mask][last - 1])) continue;
            const int remaining = ((max_mask - 1) ^ mask);
            for (int next = 1; next <= V; ++next) {
                const int next_bit = 1 << (next - 1);
                if (!(remaining & next_bit)) continue;
                const int next_mask = mask | next_bit;
                path[next_mask][next - 1] = std::min(
                    path[next_mask][next - 1],
                    path[mask][last - 1] + d[last][next]);
            }
        }
    }

    std::vector<double> cycle(max_mask, inf);
    cycle[0] = 0.0;
    for (int mask = 1; mask < max_mask; ++mask) {
        for (int last = 1; last <= V; ++last) {
            if (!(mask & (1 << (last - 1)))) continue;
            if (std::isfinite(path[mask][last - 1])) {
                cycle[mask] = std::min(cycle[mask], path[mask][last - 1] + d[last][0]);
            }
        }
    }
    return cycle;
}

} // namespace

ResourceRelaxationBound computeResourceRelaxationBound(const Instance& instance,
                                                       double lambda) {
    ResourceRelaxationBound bound;
    const double unit_operation_time = instance.pickup_time + instance.drop_time;
    if (unit_operation_time <= 1e-12 || instance.V <= 0 || instance.M <= 0) {
        bound.note = "resource relaxation skipped because operation time or dimensions are invalid";
        return bound;
    }

    for (int k = 0; k < instance.M; ++k) {
        bound.total_pickup_limit += static_cast<int>(
            std::floor(instance.total_time_limit / unit_operation_time + 1e-9));
    }

    if (bound.total_pickup_limit <= 0) {
        double penalty = 0.0;
        for (int i = 1; i <= instance.V; ++i) {
            const double ratio = static_cast<double>(instance.initial[i]) /
                static_cast<double>(instance.target[i]);
            penalty += instance.weights[i] * std::fabs(ratio - 1.0);
        }
        bound.computed = true;
        bound.penalty_lower_bound = penalty;
        bound.objective_lower_bound = lambda * penalty;
        bound.note = "resource relaxation fixed all station inventories because pickup limit is zero";
        return bound;
    }

    // Keep this relaxation cheap and deterministic. If the operation-time cap is
    // very loose, the bound is usually weak; returning zero remains valid.
    if (bound.total_pickup_limit > 5000) {
        bound.note = "resource relaxation skipped because total pickup limit is too large";
        return bound;
    }

    const double inf = std::numeric_limits<double>::infinity();
    std::vector<std::unordered_map<int, double>> states(bound.total_pickup_limit + 1);
    states[0][0] = 0.0;

    for (int i = 1; i <= instance.V; ++i) {
        std::vector<std::unordered_map<int, double>> next(bound.total_pickup_limit + 1);
        const int lo = std::max(0, instance.initial[i] - bound.total_pickup_limit);
        const int hi = std::min(instance.capacity[i],
                                instance.initial[i] + bound.total_pickup_limit);
        for (int pickup = 0; pickup <= bound.total_pickup_limit; ++pickup) {
            for (const auto& state : states[pickup]) {
                const int net = state.first;
                const double penalty = state.second;
                for (int y = lo; y <= hi; ++y) {
                    const int q = instance.initial[i] - y;
                    const int next_pickup = pickup + std::max(0, q);
                    if (next_pickup > bound.total_pickup_limit) continue;
                    const int next_net = net + q;
                    const double ratio = static_cast<double>(y) /
                        static_cast<double>(instance.target[i]);
                    const double next_penalty = penalty +
                        instance.weights[i] * std::fabs(ratio - 1.0);
                    auto& bucket = next[next_pickup];
                    auto it = bucket.find(next_net);
                    if (it == bucket.end() || next_penalty < it->second) {
                        bucket[next_net] = next_penalty;
                    }
                }
            }
        }
        for (const auto& bucket : next) {
            bound.states_processed += static_cast<long long>(bucket.size());
        }
        states.swap(next);
    }

    double best_penalty = inf;
    for (int pickup = 0; pickup <= bound.total_pickup_limit; ++pickup) {
        for (const auto& state : states[pickup]) {
            const int net = state.first;
            if (net < 0) continue; // vehicles may return bikes to the depot, but cannot create bikes.
            best_penalty = std::min(best_penalty, state.second);
        }
    }

    if (!std::isfinite(best_penalty)) {
        bound.note = "resource relaxation found no inventory vector; returning the safe zero bound";
        return bound;
    }

    bound.computed = true;
    bound.penalty_lower_bound = best_penalty;
    bound.objective_lower_bound = lambda * best_penalty;
    std::ostringstream note;
    note << "resource relaxation lower bound: total_pickup_limit="
         << bound.total_pickup_limit
         << ", penalty_lb=" << bound.penalty_lower_bound
         << ", objective_lb=" << bound.objective_lower_bound
         << ", states=" << bound.states_processed;
    bound.note = note.str();
    return bound;
}

InventoryRatioProjectionBound computeInventoryRatioProjectionBound(
    const Instance& instance,
    double lambda,
    const std::vector<int>& lower_inventory,
    const std::vector<int>& upper_inventory,
    double gamma_floor,
    const std::string& bound_scope) {
    InventoryRatioProjectionBound bound;
    bound.bound_scope = bound_scope;
    if (instance.V <= 0) {
        bound.warnings.push_back("projection bound skipped because instance has no stations");
        return bound;
    }
    if (static_cast<int>(lower_inventory.size()) <= instance.V ||
        static_cast<int>(upper_inventory.size()) <= instance.V) {
        bound.warnings.push_back("projection bound skipped because inventory interval vectors are too short");
        return bound;
    }

    std::vector<double> ell(instance.V + 1, 0.0);
    std::vector<double> u(instance.V + 1, 0.0);
    for (int i = 1; i <= instance.V; ++i) {
        if (instance.target[i] <= 0) {
            bound.warnings.push_back("projection bound skipped because station target is nonpositive");
            return bound;
        }
        if (lower_inventory[i] > upper_inventory[i]) {
            bound.warnings.push_back("projection bound saw an empty station inventory interval");
            return bound;
        }
        ell[i] = static_cast<double>(lower_inventory[i]) /
                 static_cast<double>(instance.target[i]);
        u[i] = static_cast<double>(upper_inventory[i]) /
               static_cast<double>(instance.target[i]);
        bound.S_upper_bound += u[i];
        double deviation_lb = 0.0;
        if (ell[i] > 1.0) {
            deviation_lb = ell[i] - 1.0;
        } else if (u[i] < 1.0) {
            deviation_lb = 1.0 - u[i];
        }
        bound.P_lower_bound += instance.weights[i] * deviation_lb;
    }
    if (bound.S_upper_bound <= 1e-12) {
        bound.warnings.push_back("projection bound skipped because S upper bound is nonpositive");
        return bound;
    }

    for (int i = 1; i <= instance.V; ++i) {
        for (int j = i + 1; j <= instance.V; ++j) {
            double delta = 0.0;
            if (ell[i] > u[j]) {
                delta = ell[i] - u[j];
            } else if (ell[j] > u[i]) {
                delta = ell[j] - u[i];
            }
            bound.H_lower_bound += delta;
        }
    }

    bound.G_lower_bound =
        bound.H_lower_bound / (static_cast<double>(instance.V) * bound.S_upper_bound);
    bound.objective_lower_bound =
        bound.G_lower_bound + lambda * bound.P_lower_bound;
    if (std::isfinite(gamma_floor) && gamma_floor >= 0.0) {
        const double floor_bound = std::max(0.0, gamma_floor);
        bound.objective_lower_bound = std::max({
            bound.objective_lower_bound,
            floor_bound,
            floor_bound + lambda * bound.P_lower_bound
        });
        bound.G_lower_bound = std::max(bound.G_lower_bound, floor_bound);
    }
    bound.valid = true;
    return bound;
}

PenaltyDomainTighteningResult tightenInventoryIntervalsByPenaltyBudget(
    const Instance& instance,
    double lambda,
    double gamma_floor,
    double objective_cutoff,
    std::vector<int>& lower_inventory,
    std::vector<int>& upper_inventory) {
    PenaltyDomainTighteningResult out;
    if (instance.V <= 0) return out;
    if (static_cast<int>(lower_inventory.size()) <= instance.V ||
        static_cast<int>(upper_inventory.size()) <= instance.V) {
        out.warnings.push_back("penalty tightening skipped because inventory interval vectors are too short");
        return out;
    }
    for (int i = 1; i <= instance.V; ++i) {
        out.total_domain_width_before +=
            std::max(0, upper_inventory[i] - lower_inventory[i]);
    }
    if (!std::isfinite(objective_cutoff) || objective_cutoff <= 0.0 ||
        lambda <= 1e-12) {
        out.total_domain_width_after = out.total_domain_width_before;
        return out;
    }

    const double floor_bound = std::max(0.0, gamma_floor);
    out.penalty_budget = (objective_cutoff - floor_bound) / lambda;
    out.valid = true;
    if (out.penalty_budget < -1e-9) {
        out.fathomed_by_budget = true;
        out.total_domain_width_after = out.total_domain_width_before;
        return out;
    }

    for (int i = 1; i <= instance.V; ++i) {
        if (instance.target[i] <= 0 || instance.weights[i] <= 1e-12) continue;
        const int old_lo = lower_inventory[i];
        const int old_hi = upper_inventory[i];
        const double ratio_radius = out.penalty_budget / instance.weights[i];
        const double lo_ratio = std::max(0.0, 1.0 - ratio_radius);
        const double hi_ratio = 1.0 + ratio_radius;
        const int tight_lo = static_cast<int>(
            std::ceil(static_cast<double>(instance.target[i]) * lo_ratio - 1e-9));
        const int tight_hi = static_cast<int>(
            std::floor(static_cast<double>(instance.target[i]) * hi_ratio + 1e-9));
        lower_inventory[i] = std::max(lower_inventory[i], tight_lo);
        upper_inventory[i] = std::min(upper_inventory[i], tight_hi);
        lower_inventory[i] = std::max(0, lower_inventory[i]);
        upper_inventory[i] = std::min(instance.capacity[i], upper_inventory[i]);
        if (lower_inventory[i] != old_lo || upper_inventory[i] != old_hi) {
            ++out.domains_tightened_count;
        }
    }
    for (int i = 1; i <= instance.V; ++i) {
        out.total_domain_width_after +=
            std::max(0, upper_inventory[i] - lower_inventory[i]);
    }
    return out;
}

MovementReachabilityTighteningResult tightenInventoryIntervalsByMovementReachability(
    const Instance& instance,
    std::vector<int>& lower_inventory,
    std::vector<int>& upper_inventory) {
    const auto start = std::chrono::steady_clock::now();
    MovementReachabilityTighteningResult out;
    if (instance.V <= 0) return out;
    if (static_cast<int>(lower_inventory.size()) <= instance.V ||
        static_cast<int>(upper_inventory.size()) <= instance.V) {
        out.warnings.push_back("movement reachability tightening skipped because inventory interval vectors are too short");
        return out;
    }
    const double unit_operation_time = instance.pickup_time + instance.drop_time;
    if (unit_operation_time <= 1e-12) {
        out.warnings.push_back("movement reachability tightening skipped because operation time is invalid");
        return out;
    }

    const std::vector<std::vector<double>> metric_dist = metricClosure(instance);
    for (int i = 1; i <= instance.V; ++i) {
        out.total_domain_width_before +=
            std::max(0, upper_inventory[i] - lower_inventory[i]);
        int pickup_reach = 0;
        int drop_reach = 0;
        const double rt_lb = metric_dist[0][i] + metric_dist[i][0];
        for (int k = 0; k < instance.M; ++k) {
            int move_budget = 0;
            if (instance.total_time_limit + 1e-9 >= rt_lb) {
                move_budget = static_cast<int>(
                    std::floor((instance.total_time_limit - rt_lb) /
                               unit_operation_time + 1e-9));
            }
            const int q = k < static_cast<int>(instance.Q.size()) ? instance.Q[k] : 0;
            pickup_reach = std::max(
                pickup_reach,
                std::min({std::max(0, instance.initial[i]), std::max(0, q),
                          std::max(0, move_budget)}));
            drop_reach = std::max(
                drop_reach,
                std::min({std::max(0, instance.capacity[i] - instance.initial[i]),
                          std::max(0, q), std::max(0, move_budget)}));
        }
        if (pickup_reach == 0 && drop_reach == 0) {
            ++out.unreachable_station_count;
        }
        const int old_lo = lower_inventory[i];
        const int old_hi = upper_inventory[i];
        lower_inventory[i] = std::max(lower_inventory[i],
                                      std::max(0, instance.initial[i] - pickup_reach));
        upper_inventory[i] = std::min(upper_inventory[i],
                                      std::min(instance.capacity[i],
                                               instance.initial[i] + drop_reach));
        if (lower_inventory[i] != old_lo || upper_inventory[i] != old_hi) {
            ++out.domains_tightened_count;
        }
        out.total_domain_width_after +=
            std::max(0, upper_inventory[i] - lower_inventory[i]);
    }
    out.valid = true;
    out.time_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    return out;
}

GiniIntervalInventoryRelaxationBound computeGiniIntervalInventoryRelaxationBound(
    const Instance& instance,
    double lambda,
    double gamma_floor,
    double gamma_cap,
    double time_limit_seconds,
    double objective_cutoff,
    int route_mask_max_v,
    bool projection_bound_enabled,
    bool penalty_domain_tightening_enabled,
    bool movement_domain_tightening_enabled,
    bool route_mask_support_duration_pruning_enabled,
    bool pickup_drop_compat_flow_enabled,
    bool pickup_drop_transfer_cap_flow_enabled,
    bool route_mask_operation_budget_cuts_enabled,
    bool vehicle_indexed_operation_relaxation_enabled,
    bool vehicle_indexed_transfer_flow_enabled) {
    GiniIntervalInventoryRelaxationBound bound;
    if (instance.V <= 0 || gamma_cap < -1e-12) {
        bound.note = "inventory-Gini relaxation skipped because interval parameters are invalid";
        return bound;
    }

    const double unit_operation_time = instance.pickup_time + instance.drop_time;
    if (unit_operation_time <= 1e-12) {
        bound.note = "inventory-Gini relaxation skipped because operation time is invalid";
        return bound;
    }
    for (int k = 0; k < instance.M; ++k) {
        bound.total_pickup_limit += static_cast<int>(
            std::floor(instance.total_time_limit / unit_operation_time + 1e-9));
    }

    const auto run_id = std::chrono::high_resolution_clock::now()
        .time_since_epoch().count();
    const auto thread_id = std::hash<std::thread::id>{}(std::this_thread::get_id());
    const std::filesystem::path work_dir = std::filesystem::path("results") /
        "bound_work" / (std::filesystem::path(instance.name).stem().string() +
        "_" + std::to_string(run_id) + "_" + std::to_string(thread_id));
    std::filesystem::create_directories(work_dir);
    const std::filesystem::path lp_path = work_dir / "inventory_gini_bound.lp";
    const std::filesystem::path sol_path = work_dir / "inventory_gini_bound.sol";
    const std::filesystem::path log_path = work_dir / "inventory_gini_bound.log";
    const std::filesystem::path cmd_path = work_dir / "run.cplex";

    const bool cutoff_bound_active =
        std::isfinite(objective_cutoff) && objective_cutoff > 0.0 &&
        lambda > 1e-12;
    const double floor_bound = std::max(0.0, gamma_floor);
    const double penalty_budget = cutoff_bound_active
        ? (objective_cutoff - floor_bound) / lambda
        : std::numeric_limits<double>::infinity();
    bound.penalty_budget = std::isfinite(penalty_budget) ? penalty_budget : 0.0;
    auto cutoffCappedLowerBound = [&](double value) {
        if (!std::isfinite(value)) {
            return cutoff_bound_active ? objective_cutoff : value;
        }
        value = std::max(0.0, value);
        if (cutoff_bound_active) value = std::min(value, objective_cutoff);
        return value;
    };
    if (cutoff_bound_active && penalty_budget < -1e-9) {
        bound.computed = true;
        bound.objective_lower_bound = objective_cutoff;
        bound.gini_lower_bound = floor_bound;
        bound.lambda_penalty_lower_bound =
            std::max(0.0, bound.objective_lower_bound - bound.gini_lower_bound);
        std::ostringstream note;
        note << "inventory-route-Gini relaxation cutoff-fathomed by interval floor: interval=["
             << gamma_floor << "," << gamma_cap << "]"
             << ", incumbent_cutoff_bound=true"
             << ", objective_lb=" << bound.objective_lower_bound;
        bound.note = note.str();
        return bound;
    }

    std::vector<int> inventory_lower(instance.V + 1, 0);
    std::vector<int> inventory_upper(instance.V + 1, 0);
    for (int i = 1; i <= instance.V; ++i) {
        inventory_lower[i] = 0;
        inventory_upper[i] = instance.capacity[i];
    }

    if (movement_domain_tightening_enabled) {
        MovementReachabilityTighteningResult move_tighten =
            tightenInventoryIntervalsByMovementReachability(
                instance, inventory_lower, inventory_upper);
        bound.movement_tightening_time_seconds = move_tighten.time_seconds;
        bound.movement_domains_tightened_count =
            move_tighten.domains_tightened_count;
        bound.movement_domain_width_before =
            move_tighten.total_domain_width_before;
        bound.movement_domain_width_after =
            move_tighten.total_domain_width_after;
        bound.movement_unreachable_station_count =
            move_tighten.unreachable_station_count;
    }

    if (penalty_domain_tightening_enabled) {
        const auto tighten_start = std::chrono::steady_clock::now();
        PenaltyDomainTighteningResult tighten =
            tightenInventoryIntervalsByPenaltyBudget(
                instance, lambda, gamma_floor, objective_cutoff,
                inventory_lower, inventory_upper);
        bound.penalty_tightening_time_seconds =
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - tighten_start).count();
        bound.penalty_budget = tighten.penalty_budget;
        bound.domains_tightened_count = tighten.domains_tightened_count;
        if (bound.total_domain_width_before == 0 &&
            bound.total_domain_width_after == 0) {
            bound.total_domain_width_before = tighten.total_domain_width_before;
            bound.total_domain_width_after = tighten.total_domain_width_after;
        } else {
            bound.total_domain_width_after = tighten.total_domain_width_after;
        }
        bound.penalty_budget_fathomed = tighten.fathomed_by_budget;
        if (tighten.fathomed_by_budget) {
            bound.computed = true;
            bound.objective_lower_bound = objective_cutoff;
            bound.gini_lower_bound = floor_bound;
            bound.lambda_penalty_lower_bound =
                std::max(0.0, bound.objective_lower_bound - bound.gini_lower_bound);
            bound.note = "inventory-route-Gini relaxation cutoff-fathomed by penalty budget before LP";
            return bound;
        }
    } else {
        if (bound.total_domain_width_before == 0 &&
            bound.total_domain_width_after == 0) {
            for (int i = 1; i <= instance.V; ++i) {
                bound.total_domain_width_before += instance.capacity[i];
                bound.total_domain_width_after +=
                    std::max(0, inventory_upper[i] - inventory_lower[i]);
            }
        }
    }

    if (projection_bound_enabled) {
        const auto projection_start = std::chrono::steady_clock::now();
        InventoryRatioProjectionBound projection =
            computeInventoryRatioProjectionBound(
                instance, lambda, inventory_lower, inventory_upper,
                gamma_floor, "global");
        bound.projection_bound_time_seconds =
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - projection_start).count();
        if (projection.valid) {
            bound.projection_bound_valid = true;
            bound.projection_penalty_lower_bound = projection.P_lower_bound;
            bound.projection_h_lower_bound = projection.H_lower_bound;
            bound.projection_s_upper_bound = projection.S_upper_bound;
            bound.projection_gini_lower_bound = projection.G_lower_bound;
            bound.projection_objective_lower_bound =
                cutoffCappedLowerBound(projection.objective_lower_bound);
            bound.projection_bound_scope = projection.bound_scope;
            if (bound.projection_objective_lower_bound >= objective_cutoff - 1e-9 &&
                cutoff_bound_active) {
                bound.computed = true;
                bound.projection_bound_fathomed = true;
                bound.objective_lower_bound = objective_cutoff;
                bound.gini_lower_bound = std::max(floor_bound,
                                                  bound.projection_gini_lower_bound);
                bound.lambda_penalty_lower_bound =
                    std::max(0.0, bound.objective_lower_bound -
                                  bound.gini_lower_bound);
                bound.note = "inventory-ratio projection lower bound cutoff-fathomed this interval before LP";
                return bound;
            }
        }
    }
    for (int i = 1; i <= instance.V; ++i) {
        if (inventory_lower[i] > inventory_upper[i]) {
            bound.computed = true;
            bound.infeasible = true;
            bound.objective_lower_bound = cutoff_bound_active
                ? objective_cutoff
                : std::numeric_limits<double>::infinity();
            bound.gini_lower_bound = floor_bound;
            bound.lambda_penalty_lower_bound =
                std::max(0.0, bound.objective_lower_bound - bound.gini_lower_bound);
            bound.status = "infeasible";
            bound.note = "inventory interval tightening produced an empty final-inventory domain; interval is infeasible under necessary conditions";
            return bound;
        }
    }

    int total_initial = 0;
    for (int i = 1; i <= instance.V; ++i) total_initial += instance.initial[i];
    int max_vehicle_capacity = 0;
    for (int q : instance.Q) max_vehicle_capacity = std::max(max_vehicle_capacity, q);
    int total_vehicle_capacity = 0;
    for (int q : instance.Q) total_vehicle_capacity += q;
    const int min_station_bikes_after_return =
        std::max(0, total_initial - total_vehicle_capacity);
    const double s_upper =
        ratioSumUpperBoundForInventoryRelaxation(instance, penalty_budget,
                                                 min_station_bikes_after_return);
    const double h_coeff = 1.0 / (static_cast<double>(instance.V) * s_upper);
    const std::vector<std::vector<double>> metric_dist = metricClosure(instance);
    const std::vector<double> route_subset_lb =
        allPartitionTravelLowerBounds(metric_dist, instance.V, instance.M);
    const std::vector<double> route_cycle_lb =
        allRouteCycleLowerBounds(metric_dist, instance.V);
    const bool integer_inventory_relaxation = instance.V <= 12;
    const bool route_mask_relaxation =
        integer_inventory_relaxation && instance.V <= route_mask_max_v &&
        instance.M <= 4;
    const auto vehicle_relax_start = std::chrono::steady_clock::now();
    const bool vehicle_indexed_ops =
        route_mask_relaxation &&
        vehicle_indexed_operation_relaxation_enabled &&
        instance.V <= 30;
    bound.vehicle_indexed_operation_relaxation_enabled = vehicle_indexed_ops;
    if (vehicle_indexed_ops) {
        bound.vehicle_indexed_y_variables =
            static_cast<long long>(instance.M) * instance.V;
        bound.vehicle_indexed_pickup_variables =
            static_cast<long long>(instance.M) * instance.V;
        bound.vehicle_indexed_drop_variables =
            static_cast<long long>(instance.M) * instance.V;
    }
    std::vector<std::vector<int>> allowed_route_masks_by_vehicle(instance.M);
    std::vector<std::vector<int>> route_mask_pickup_budget_by_vehicle(instance.M);
    if (route_mask_relaxation) {
        const auto support_start = std::chrono::steady_clock::now();
        const int max_mask = 1 << instance.V;
        const double cunit = std::max(0.0, unit_operation_time);
        bound.route_mask_support_duration_pruning =
            route_mask_support_duration_pruning_enabled;
        long long operation_budget_sum = 0;
        for (int k = 0; k < instance.M; ++k) {
            for (int mask = 1; mask < max_mask; ++mask) {
                if (mask >= static_cast<int>(route_cycle_lb.size())) continue;
                if (route_cycle_lb[mask] > instance.total_time_limit + 1e-9) {
                    continue;
                }
                const int support_size = popcountMask(mask);
                const int min_pickups = (support_size + 1) / 2;
                const double support_duration_lb =
                    route_cycle_lb[mask] + cunit * static_cast<double>(min_pickups);
                ++bound.route_mask_count_before_support_duration;
                if (route_mask_support_duration_pruning_enabled &&
                    support_duration_lb > instance.total_time_limit + 1e-9) {
                    ++bound.route_masks_removed_by_support_duration;
                    bound.route_mask_support_duration_max_removed_subset_size =
                        std::max(bound.route_mask_support_duration_max_removed_subset_size,
                                 support_size);
                    if (bound.route_mask_support_duration_removed_examples.size() < 8) {
                        std::ostringstream example;
                        example << "vehicle=" << k
                                << ", mask=" << mask
                                << ", popcount=" << support_size
                                << ", cycle_lb=" << route_cycle_lb[mask]
                                << ", min_pickups=" << min_pickups
                                << ", support_duration_lb=" << support_duration_lb
                                << ", route_limit=" << instance.total_time_limit;
                        bound.route_mask_support_duration_removed_examples.push_back(
                            example.str());
                    }
                    continue;
                }
                allowed_route_masks_by_vehicle[k].push_back(mask);
                ++bound.route_mask_count_after_support_duration;
                int pickup_budget = max_vehicle_capacity;
                if (route_mask_operation_budget_cuts_enabled && cunit > 1e-12) {
                    const double residual =
                        instance.total_time_limit - route_cycle_lb[mask];
                    pickup_budget = residual >= -1e-9
                        ? static_cast<int>(std::floor(
                              std::max(0.0, residual) / cunit + 1e-9))
                        : 0;
                    const int q = k < static_cast<int>(instance.Q.size())
                        ? instance.Q[k] : max_vehicle_capacity;
                    pickup_budget = std::max(0, std::min(pickup_budget, q));
                    if (pickup_budget == 0) ++bound.route_mask_operation_budget_zero_masks;
                    if (pickup_budget < q) {
                        ++bound.route_mask_operation_budget_tightened_masks;
                    }
                    if (bound.route_mask_operation_budget_min <= 0.0) {
                        bound.route_mask_operation_budget_min = pickup_budget;
                    } else {
                        bound.route_mask_operation_budget_min =
                            std::min(bound.route_mask_operation_budget_min,
                                     static_cast<double>(pickup_budget));
                    }
                    bound.route_mask_operation_budget_max =
                        std::max(bound.route_mask_operation_budget_max,
                                 static_cast<double>(pickup_budget));
                    operation_budget_sum += pickup_budget;
                    if (bound.route_mask_operation_budget_examples.size() < 8) {
                        std::ostringstream example;
                        example << "vehicle=" << k
                                << ", mask=" << mask
                                << ", popcount=" << support_size
                                << ", cycle_lb=" << route_cycle_lb[mask]
                                << ", pickup_budget=" << pickup_budget
                                << ", route_limit=" << instance.total_time_limit;
                        bound.route_mask_operation_budget_examples.push_back(
                            example.str());
                    }
                } else {
                    const int q = k < static_cast<int>(instance.Q.size())
                        ? instance.Q[k] : max_vehicle_capacity;
                    pickup_budget = std::max(0, q);
                }
                route_mask_pickup_budget_by_vehicle[k].push_back(pickup_budget);
            }
        }
        if (route_mask_operation_budget_cuts_enabled && cunit <= 1e-12) {
            bound.route_mask_operation_budget_examples.push_back(
                "operation_budget_disabled: pickup_time+drop_time <= 0");
        }
        if (route_mask_operation_budget_cuts_enabled) {
            bound.route_mask_operation_budget_cuts_added =
                static_cast<long long>(instance.M);
            const long long allowed_count = bound.route_mask_count_after_support_duration;
            if (allowed_count > 0) {
                bound.route_mask_operation_budget_avg =
                    static_cast<double>(operation_budget_sum) /
                    static_cast<double>(allowed_count);
            }
        }
        bound.route_mask_support_duration_precompute_time_seconds =
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - support_start).count();
        bound.route_mask_operation_budget_precompute_time_seconds =
            bound.route_mask_support_duration_precompute_time_seconds;
    }
    const bool compat_flow =
        pickup_drop_compat_flow_enabled && instance.V <= 30;
    bound.pickup_drop_compat_flow_enabled = compat_flow;
    std::vector<std::vector<char>> pickup_drop_compatible(
        instance.V + 1, std::vector<char>(instance.V + 1, 0));
    std::vector<std::vector<int>> pickup_drop_transfer_cap(
        instance.V + 1, std::vector<int>(instance.V + 1, 0));
    if (compat_flow) {
        const auto compat_start = std::chrono::steady_clock::now();
        const int qmax = max_vehicle_capacity;
        long long transfer_cap_sum = 0;
        std::vector<std::string> restrictive_examples;
        for (int i = 1; i <= instance.V; ++i) {
            for (int j = 1; j <= instance.V; ++j) {
                if (i == j) continue;
                ++bound.pickup_drop_pairs_total;
                const int pickup_cap =
                    std::max(0, std::min(instance.initial[i],
                                         inventory_upper[i]));
                const int drop_cap =
                    std::max(0, std::min(instance.capacity[j] - instance.initial[j],
                                         instance.capacity[j] - inventory_lower[j]));
                const int loose_cap = std::max(0, std::min(qmax,
                    std::min(pickup_cap, drop_cap)));
                int best_cap = pickup_drop_transfer_cap_flow_enabled
                    ? 0 : loose_cap;
                double best_path_lb = std::numeric_limits<double>::infinity();
                for (int k = 0; k < instance.M; ++k) {
                    const double path_lb =
                        metric_dist[0][i] + metric_dist[i][j] +
                        metric_dist[j][0];
                    best_path_lb = std::min(best_path_lb, path_lb);
                    if (pickup_drop_transfer_cap_flow_enabled) {
                        const double budget =
                            instance.total_time_limit - path_lb;
                        const int move_budget = budget >= -1e-9
                            ? static_cast<int>(std::floor(
                                  std::max(0.0, budget) /
                                  unit_operation_time + 1e-9))
                            : 0;
                        const int vehicle_cap = std::max(0, std::min(instance.Q[k],
                            std::min(pickup_cap, drop_cap)));
                        best_cap = std::max(best_cap,
                            std::min(vehicle_cap, move_budget));
                    } else if (path_lb + unit_operation_time <=
                               instance.total_time_limit + 1e-9) {
                        best_cap = loose_cap;
                    }
                }
                if (best_cap > 0) {
                    pickup_drop_compatible[i][j] = 1;
                    pickup_drop_transfer_cap[i][j] = best_cap;
                    ++bound.pickup_drop_pairs_compatible;
                    ++bound.pickup_drop_transfer_cap_variables;
                    transfer_cap_sum += best_cap;
                    if (bound.pickup_drop_transfer_cap_min <= 0.0) {
                        bound.pickup_drop_transfer_cap_min = best_cap;
                    } else {
                        bound.pickup_drop_transfer_cap_min =
                            std::min(bound.pickup_drop_transfer_cap_min,
                                     static_cast<double>(best_cap));
                    }
                    bound.pickup_drop_transfer_cap_max =
                        std::max(bound.pickup_drop_transfer_cap_max,
                                 static_cast<double>(best_cap));
                    if (pickup_drop_transfer_cap_flow_enabled &&
                        best_cap < loose_cap) {
                        ++bound.pickup_drop_pairs_capacity_limited;
                        if (restrictive_examples.size() < 8) {
                            std::ostringstream example;
                            example << "pickup=" << i
                                    << ", drop=" << j
                                    << ", cap=" << best_cap
                                    << ", loose_cap=" << loose_cap
                                    << ", path_lb=" << best_path_lb
                                    << ", route_limit="
                                    << instance.total_time_limit;
                            restrictive_examples.push_back(example.str());
                        }
                    }
                } else {
                    ++bound.pickup_drop_pairs_incompatible;
                    if (bound.pickup_drop_incompatible_examples.size() < 8) {
                        std::ostringstream example;
                        example << "pickup=" << i
                                << ", drop=" << j
                                << ", directed_lb="
                                << (metric_dist[0][i] + metric_dist[i][j] +
                                    metric_dist[j][0] + unit_operation_time)
                                << ", route_limit=" << instance.total_time_limit;
                        bound.pickup_drop_incompatible_examples.push_back(
                            example.str());
                    }
                }
            }
        }
        bound.pickup_drop_compat_flow_variables =
            bound.pickup_drop_pairs_compatible + instance.V;
        bound.pickup_drop_compat_flow_constraints = 2LL * instance.V;
        bound.pickup_drop_transfer_cap_constraints =
            bound.pickup_drop_transfer_cap_variables;
        if (bound.pickup_drop_pairs_compatible > 0) {
            bound.pickup_drop_transfer_cap_avg =
                static_cast<double>(transfer_cap_sum) /
                static_cast<double>(bound.pickup_drop_pairs_compatible);
        }
        bound.pickup_drop_compat_flow_time_seconds =
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - compat_start).count();
        bound.pickup_drop_transfer_cap_time_seconds =
            bound.pickup_drop_compat_flow_time_seconds;
        for (const std::string& example : restrictive_examples) {
            bound.pickup_drop_incompatible_examples.push_back(
                "capacity_limited_pair={" + example + "}");
        }
    }
    const bool vehicle_transfer_flow =
        compat_flow && vehicle_indexed_ops &&
        vehicle_indexed_transfer_flow_enabled;
    std::vector<std::vector<std::vector<int>>> vehicle_transfer_cap(
        instance.M, std::vector<std::vector<int>>(
            instance.V + 1, std::vector<int>(instance.V + 1, 0)));
    if (vehicle_transfer_flow) {
        const auto vt_start = std::chrono::steady_clock::now();
        long long cap_sum = 0;
        std::vector<std::string> vehicle_restrictive_examples;
        for (int k = 0; k < instance.M; ++k) {
            const int qk = k < static_cast<int>(instance.Q.size())
                ? instance.Q[k] : max_vehicle_capacity;
            for (int i = 1; i <= instance.V; ++i) {
                for (int j = 1; j <= instance.V; ++j) {
                    if (i == j) continue;
                    ++bound.vehicle_transfer_pairs_total;
                    const int pickup_cap =
                        std::max(0, std::min(instance.initial[i],
                                             inventory_upper[i]));
                    const int drop_cap =
                        std::max(0, std::min(
                            instance.capacity[j] - instance.initial[j],
                            instance.capacity[j] - inventory_lower[j]));
                    const int loose_cap = std::max(0, std::min(qk,
                        std::min(pickup_cap, drop_cap)));
                    const double path_lb =
                        metric_dist[0][i] + metric_dist[i][j] +
                        metric_dist[j][0];
                    const double residual = instance.total_time_limit - path_lb;
                    const int move_budget = residual >= -1e-9
                        ? static_cast<int>(std::floor(
                              std::max(0.0, residual) /
                              unit_operation_time + 1e-9))
                        : 0;
                    const int cap = std::max(0, std::min(loose_cap, move_budget));
                    vehicle_transfer_cap[k][i][j] = cap;
                    if (cap <= 0) {
                        ++bound.vehicle_transfer_pairs_zero_cap;
                        continue;
                    }
                    ++bound.vehicle_transfer_flow_variables;
                    cap_sum += cap;
                    if (bound.vehicle_transfer_cap_min <= 0.0) {
                        bound.vehicle_transfer_cap_min = cap;
                    } else {
                        bound.vehicle_transfer_cap_min =
                            std::min(bound.vehicle_transfer_cap_min,
                                     static_cast<double>(cap));
                    }
                    bound.vehicle_transfer_cap_max =
                        std::max(bound.vehicle_transfer_cap_max,
                                 static_cast<double>(cap));
                    if (cap < loose_cap) {
                        ++bound.vehicle_transfer_pairs_capacity_limited;
                        if (vehicle_restrictive_examples.size() < 8) {
                            std::ostringstream example;
                            example << "vehicle=" << k
                                    << ", pickup=" << i
                                    << ", drop=" << j
                                    << ", cap=" << cap
                                    << ", loose_cap=" << loose_cap
                                    << ", path_lb=" << path_lb
                                    << ", route_limit="
                                    << instance.total_time_limit;
                            vehicle_restrictive_examples.push_back(example.str());
                        }
                    }
                }
            }
        }
        bound.vehicle_transfer_depot_unload_variables =
            static_cast<long long>(instance.M) * instance.V;
        bound.vehicle_transfer_flow_balance_constraints =
            2LL * instance.M * instance.V;
        bound.vehicle_transfer_mask_linking_constraints =
            bound.vehicle_transfer_flow_variables +
            bound.vehicle_transfer_depot_unload_variables;
        if (bound.vehicle_transfer_flow_variables > 0) {
            bound.vehicle_transfer_cap_avg =
                static_cast<double>(cap_sum) /
                static_cast<double>(bound.vehicle_transfer_flow_variables);
        }
        bound.vehicle_transfer_flow_time_seconds =
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - vt_start).count();
        for (const std::string& example : vehicle_restrictive_examples) {
            bound.pickup_drop_incompatible_examples.push_back(
                "vehicle_capacity_limited_pair={" + example + "}");
        }
    }
    auto routeMaskSupportNote = [&]() {
        std::ostringstream ss;
        ss << ", route_mask_support_duration_pruning="
           << (route_mask_support_duration_pruning_enabled ? "true" : "false")
           << ", route_mask_count_before_support_duration="
           << bound.route_mask_count_before_support_duration
           << ", route_mask_count_after_support_duration="
           << bound.route_mask_count_after_support_duration
           << ", route_masks_removed_by_support_duration="
           << bound.route_masks_removed_by_support_duration
           << ", route_mask_support_duration_max_removed_subset_size="
           << bound.route_mask_support_duration_max_removed_subset_size;
        ss << ", route_mask_operation_budget_cuts="
           << (route_mask_operation_budget_cuts_enabled ? "true" : "false")
           << ", route_mask_operation_budget_cuts_added="
           << bound.route_mask_operation_budget_cuts_added
           << ", route_mask_operation_budget_min="
           << bound.route_mask_operation_budget_min
           << ", route_mask_operation_budget_avg="
           << bound.route_mask_operation_budget_avg
           << ", route_mask_operation_budget_max="
           << bound.route_mask_operation_budget_max
           << ", route_mask_operation_budget_tightened_masks="
           << bound.route_mask_operation_budget_tightened_masks
           << ", route_mask_operation_budget_zero_masks="
           << bound.route_mask_operation_budget_zero_masks;
        for (const std::string& example :
             bound.route_mask_support_duration_removed_examples) {
            ss << ", removed_mask_example={" << example << "}";
        }
        for (const std::string& example :
             bound.route_mask_operation_budget_examples) {
            ss << ", operation_budget_example={" << example << "}";
        }
        return ss.str();
    };
    auto pickupDropCompatNote = [&]() {
        std::ostringstream ss;
        ss << ", pickup_drop_compat_flow="
           << (compat_flow ? "true" : "false")
           << ", pickup_drop_pairs_total=" << bound.pickup_drop_pairs_total
           << ", pickup_drop_pairs_compatible="
           << bound.pickup_drop_pairs_compatible
           << ", pickup_drop_pairs_incompatible="
           << bound.pickup_drop_pairs_incompatible
           << ", pickup_drop_pairs_capacity_limited="
           << bound.pickup_drop_pairs_capacity_limited
           << ", pickup_drop_transfer_cap_min="
           << bound.pickup_drop_transfer_cap_min
           << ", pickup_drop_transfer_cap_avg="
           << bound.pickup_drop_transfer_cap_avg
           << ", pickup_drop_transfer_cap_max="
           << bound.pickup_drop_transfer_cap_max
           << ", pickup_drop_transfer_cap_variables="
           << bound.pickup_drop_transfer_cap_variables
           << ", pickup_drop_transfer_cap_constraints="
           << bound.pickup_drop_transfer_cap_constraints
           << ", pickup_drop_compat_flow_variables="
           << bound.pickup_drop_compat_flow_variables
           << ", pickup_drop_compat_flow_constraints="
           << bound.pickup_drop_compat_flow_constraints
           << ", vehicle_indexed_operation_relaxation="
           << (vehicle_indexed_ops ? "true" : "false")
           << ", vehicle_indexed_y_variables="
           << bound.vehicle_indexed_y_variables
           << ", vehicle_indexed_pickup_variables="
           << bound.vehicle_indexed_pickup_variables
           << ", vehicle_indexed_drop_variables="
           << bound.vehicle_indexed_drop_variables
           << ", vehicle_indexed_linking_constraints="
           << bound.vehicle_indexed_linking_constraints
           << ", vehicle_indexed_balance_constraints="
           << bound.vehicle_indexed_balance_constraints
           << ", vehicle_indexed_operation_budget_constraints="
           << bound.vehicle_indexed_operation_budget_constraints
           << ", vehicle_indexed_transfer_flow="
           << (vehicle_transfer_flow ? "true" : "false")
           << ", vehicle_transfer_flow_variables="
           << bound.vehicle_transfer_flow_variables
           << ", vehicle_transfer_depot_unload_variables="
           << bound.vehicle_transfer_depot_unload_variables
           << ", vehicle_transfer_flow_balance_constraints="
           << bound.vehicle_transfer_flow_balance_constraints
           << ", vehicle_transfer_mask_linking_constraints="
           << bound.vehicle_transfer_mask_linking_constraints
           << ", vehicle_transfer_pairs_total="
           << bound.vehicle_transfer_pairs_total
           << ", vehicle_transfer_pairs_zero_cap="
           << bound.vehicle_transfer_pairs_zero_cap
           << ", vehicle_transfer_pairs_capacity_limited="
           << bound.vehicle_transfer_pairs_capacity_limited
           << ", vehicle_transfer_cap_min="
           << bound.vehicle_transfer_cap_min
           << ", vehicle_transfer_cap_avg="
           << bound.vehicle_transfer_cap_avg
           << ", vehicle_transfer_cap_max="
           << bound.vehicle_transfer_cap_max;
        for (const std::string& example :
             bound.pickup_drop_incompatible_examples) {
            ss << ", incompatible_pair_example={" << example << "}";
        }
        return ss.str();
    };

    std::ofstream lp(lp_path);
    if (!lp) {
        bound.note = "inventory-Gini relaxation could not write LP";
        return bound;
    }
    lp << std::setprecision(12);
    lp << "\\ final-inventory Gini/pickup relaxation lower bound\n";
    lp << "Minimize\n obj: gbound";
    for (int i = 1; i <= instance.V; ++i) {
        const double coeff = lambda * instance.weights[i];
        if (std::fabs(coeff) > 1e-12) lp << " + " << num(coeff) << " " << eName(i);
    }
    lp << "\nSubject To\n";

    int cid = 0;
    auto row = [&](const std::string& body) {
        lp << " c" << cid++ << ": " << body << "\n";
    };

    auto addPositiveTerm = [&](std::ostringstream& ss,
                               bool& first_term,
                               double coeff,
                               const std::string& var) {
        if (std::fabs(coeff) <= 1e-12) return;
        if (!first_term) ss << " + ";
        ss << num(coeff) << " " << var;
        first_term = false;
    };

    for (int i = 1; i <= instance.V; ++i) {
        row(yName(i) + " - " + num(instance.target[i]) + " " + rName(i) + " = 0");
        row(rName(i) + " - " + eName(i) + " <= 1");
        row("- " + rName(i) + " - " + eName(i) + " <= -1");
        row(pName(i) + " - " + dName(i) + " + " + yName(i) +
            " = " + num(instance.initial[i]));
        row(pName(i) + " + " + yName(i) + " >= " + num(instance.initial[i]));
        row(dName(i) + " - " + yName(i) + " >= " + num(-instance.initial[i]));
        row(pName(i) + " - " + num(instance.initial[i]) + " " + vName(i) + " <= 0");
        row(dName(i) + " - " + num(std::max(0, instance.capacity[i] - instance.initial[i])) +
            " " + vName(i) + " <= 0");
        if (max_vehicle_capacity > 0) {
            row(pName(i) + " - " + num(max_vehicle_capacity) + " " + vName(i) + " <= 0");
            row(dName(i) + " - " + num(max_vehicle_capacity) + " " + vName(i) + " <= 0");
        }
        const int station_pick_cap = std::min(instance.initial[i], max_vehicle_capacity);
        const int station_drop_cap = std::min(
            std::max(0, instance.capacity[i] - instance.initial[i]),
            max_vehicle_capacity);
        const int station_single_mode_cap =
            std::max(station_pick_cap, station_drop_cap);
        row(pName(i) + " + " + dName(i) + " - " +
            num(std::max(0, station_single_mode_cap)) + " " + vName(i) + " <= 0");
        row(pName(i) + " + " + dName(i) + " - " + vName(i) + " >= 0");
        row(pName(i) + " - " + num(std::max(0, station_pick_cap)) + " " +
            modeName(i) + " <= 0");
        row(dName(i) + " + " + num(std::max(0, station_drop_cap)) + " " +
            modeName(i) + " <= " + num(std::max(0, station_drop_cap)));
        row(num(unit_operation_time) + " " + pName(i) + " + " +
            num(2.0 * metric_dist[0][i]) + " " + vName(i) +
            " <= " + num(instance.total_time_limit));
    }

    if (cutoff_bound_active) {
        std::ostringstream penalty_cut;
        bool first_penalty = true;
        for (int i = 1; i <= instance.V; ++i) {
            const double coeff = instance.weights[i];
            if (std::fabs(coeff) <= 1e-12) continue;
            if (!first_penalty) penalty_cut << " + ";
            penalty_cut << num(coeff) << " " << eName(i);
            first_penalty = false;
        }
        if (first_penalty) penalty_cut << "0";
        penalty_cut << " <= " << num(std::max(0.0, penalty_budget));
        row(penalty_cut.str());
    }

    std::ostringstream pickup;
    for (int i = 1; i <= instance.V; ++i) {
        if (i > 1) pickup << " + ";
        pickup << pName(i);
    }
    pickup << " <= " << bound.total_pickup_limit;
    row(pickup.str());

    const bool aggregate_compat_flow = compat_flow && !vehicle_transfer_flow;
    if (aggregate_compat_flow) {
        for (int i = 1; i <= instance.V; ++i) {
            std::ostringstream pickup_balance;
            pickup_balance << pName(i);
            for (int j = 1; j <= instance.V; ++j) {
                if (pickup_drop_compatible[i][j]) {
                    pickup_balance << " - " << transferName(i, j);
                }
            }
            pickup_balance << " - " << unloadName(i) << " = 0";
            row(pickup_balance.str());
        }
        for (int j = 1; j <= instance.V; ++j) {
            std::ostringstream drop_balance;
            drop_balance << dName(j);
            for (int i = 1; i <= instance.V; ++i) {
                if (pickup_drop_compatible[i][j]) {
                    drop_balance << " - " << transferName(i, j);
                }
            }
            drop_balance << " = 0";
            row(drop_balance.str());
        }
    }

    if (route_mask_relaxation) {
        for (int k = 0; k < instance.M; ++k) {
            std::ostringstream route_use;
            bool first_use = true;
            for (int mask : allowed_route_masks_by_vehicle[k]) {
                addPositiveTerm(route_use, first_use, 1.0, routeMaskName(k, mask));
            }
            if (first_use) route_use << "0";
            route_use << " <= 1";
            row(route_use.str());
        }

        if (vehicle_indexed_ops) {
            for (int k = 0; k < instance.M; ++k) {
                for (int i = 1; i <= instance.V; ++i) {
                    std::ostringstream vehicle_cover;
                    vehicle_cover << routeVisitName(k, i);
                    const int bit = 1 << (i - 1);
                    for (int mask : allowed_route_masks_by_vehicle[k]) {
                        if (mask & bit) {
                            vehicle_cover << " - " << routeMaskName(k, mask);
                        }
                    }
                    vehicle_cover << " = 0";
                    row(vehicle_cover.str());
                    ++bound.vehicle_indexed_linking_constraints;
                }
            }
            for (int i = 1; i <= instance.V; ++i) {
                std::ostringstream cover;
                bool first_cover = true;
                for (int k = 0; k < instance.M; ++k) {
                    addPositiveTerm(cover, first_cover, 1.0,
                                    routeVisitName(k, i));
                }
                if (first_cover) cover << "0";
                cover << " - " << vName(i) << " = 0";
                row(cover.str());
                ++bound.vehicle_indexed_linking_constraints;
            }
        } else {
            for (int i = 1; i <= instance.V; ++i) {
                std::ostringstream cover;
                bool first_cover = true;
                const int bit = 1 << (i - 1);
                for (int k = 0; k < instance.M; ++k) {
                    for (int mask : allowed_route_masks_by_vehicle[k]) {
                        if (mask & bit) {
                            addPositiveTerm(cover, first_cover, 1.0,
                                            routeMaskName(k, mask));
                        }
                    }
                }
                if (first_cover) cover << "0";
                cover << " - " << vName(i) << " = 0";
                row(cover.str());
            }
        }

        for (int i = 1; i <= instance.V; ++i) {
            std::ostringstream pickup_assign;
            std::ostringstream drop_assign;
            bool first_pickup = true;
            bool first_drop = true;
            for (int k = 0; k < instance.M; ++k) {
                addPositiveTerm(pickup_assign, first_pickup, 1.0,
                                routePickupName(k, i));
                addPositiveTerm(drop_assign, first_drop, 1.0,
                                routeDropName(k, i));
            }
            pickup_assign << " - " << pName(i) << " = 0";
            drop_assign << " - " << dName(i) << " = 0";
            row(pickup_assign.str());
            row(drop_assign.str());
        }

        for (int k = 0; k < instance.M; ++k) {
            for (int i = 1; i <= instance.V; ++i) {
                const int bit = 1 << (i - 1);
                const int pickup_cap =
                    std::min(instance.initial[i], k < static_cast<int>(instance.Q.size())
                        ? instance.Q[k] : max_vehicle_capacity);
                const int drop_cap =
                    std::min(std::max(0, instance.capacity[i] - instance.initial[i]),
                             k < static_cast<int>(instance.Q.size())
                                 ? instance.Q[k] : max_vehicle_capacity);

                std::ostringstream pickup_link;
                pickup_link << routePickupName(k, i);
                if (vehicle_indexed_ops) {
                    pickup_link << " - " << num(pickup_cap) << " "
                                << routeVisitName(k, i);
                } else {
                    for (int mask : allowed_route_masks_by_vehicle[k]) {
                        if (mask & bit) {
                            pickup_link << " - " << num(pickup_cap) << " "
                                        << routeMaskName(k, mask);
                        }
                    }
                }
                pickup_link << " <= 0";
                row(pickup_link.str());
                if (vehicle_indexed_ops) ++bound.vehicle_indexed_linking_constraints;

                std::ostringstream drop_link;
                drop_link << routeDropName(k, i);
                if (vehicle_indexed_ops) {
                    drop_link << " - " << num(drop_cap) << " "
                              << routeVisitName(k, i);
                } else {
                    for (int mask : allowed_route_masks_by_vehicle[k]) {
                        if (mask & bit) {
                            drop_link << " - " << num(drop_cap) << " "
                                      << routeMaskName(k, mask);
                        }
                    }
                }
                drop_link << " <= 0";
                row(drop_link.str());
                if (vehicle_indexed_ops) ++bound.vehicle_indexed_linking_constraints;
            }
        }

        for (int k = 0; k < instance.M; ++k) {
            std::ostringstream duration;
            bool first_duration = true;
            for (int i = 1; i <= instance.V; ++i) {
                addPositiveTerm(duration, first_duration, unit_operation_time,
                                routePickupName(k, i));
            }
            for (int mask : allowed_route_masks_by_vehicle[k]) {
                addPositiveTerm(duration, first_duration, route_cycle_lb[mask],
                                routeMaskName(k, mask));
            }
            if (first_duration) duration << "0";
            duration << " <= " << num(instance.total_time_limit);
            row(duration.str());

            if (route_mask_operation_budget_cuts_enabled &&
                k < static_cast<int>(route_mask_pickup_budget_by_vehicle.size()) &&
                route_mask_pickup_budget_by_vehicle[k].size() ==
                    allowed_route_masks_by_vehicle[k].size()) {
                std::ostringstream op_budget;
                bool first_budget = true;
                for (int i = 1; i <= instance.V; ++i) {
                    addPositiveTerm(op_budget, first_budget, 1.0,
                                    routePickupName(k, i));
                }
                for (std::size_t pos = 0;
                     pos < allowed_route_masks_by_vehicle[k].size(); ++pos) {
                    const int mask = allowed_route_masks_by_vehicle[k][pos];
                    const int budget = route_mask_pickup_budget_by_vehicle[k][pos];
                    if (budget > 0) {
                        op_budget << " - " << num(budget) << " "
                                  << routeMaskName(k, mask);
                    }
                }
                if (first_budget) op_budget << "0";
                op_budget << " <= 0";
                row(op_budget.str());
                if (vehicle_indexed_ops) {
                    ++bound.vehicle_indexed_operation_budget_constraints;
                }
            }

            std::ostringstream route_drop_balance;
            bool first_drop_balance = true;
            for (int i = 1; i <= instance.V; ++i) {
                addPositiveTerm(route_drop_balance, first_drop_balance, 1.0,
                                routeDropName(k, i));
            }
            for (int i = 1; i <= instance.V; ++i) {
                route_drop_balance << " - " << routePickupName(k, i);
            }
            route_drop_balance << " <= 0";
            row(route_drop_balance.str());
            if (vehicle_indexed_ops) ++bound.vehicle_indexed_balance_constraints;

            std::ostringstream route_return_load;
            bool first_return_load = true;
            for (int i = 1; i <= instance.V; ++i) {
                addPositiveTerm(route_return_load, first_return_load, 1.0,
                                routePickupName(k, i));
            }
            for (int i = 1; i <= instance.V; ++i) {
                route_return_load << " - " << routeDropName(k, i);
            }
            const int q = k < static_cast<int>(instance.Q.size())
                ? instance.Q[k] : max_vehicle_capacity;
            route_return_load << " <= " << num(q);
            row(route_return_load.str());
            if (vehicle_indexed_ops) ++bound.vehicle_indexed_balance_constraints;
        }

        if (vehicle_transfer_flow) {
            for (int k = 0; k < instance.M; ++k) {
                for (int i = 1; i <= instance.V; ++i) {
                    std::ostringstream pickup_balance;
                    pickup_balance << routePickupName(k, i);
                    for (int j = 1; j <= instance.V; ++j) {
                        if (vehicle_transfer_cap[k][i][j] > 0) {
                            pickup_balance << " - "
                                           << vehicleTransferName(k, i, j);
                        }
                    }
                    pickup_balance << " - " << vehicleUnloadName(k, i) << " = 0";
                    row(pickup_balance.str());
                }
                for (int j = 1; j <= instance.V; ++j) {
                    std::ostringstream drop_balance;
                    drop_balance << routeDropName(k, j);
                    for (int i = 1; i <= instance.V; ++i) {
                        if (vehicle_transfer_cap[k][i][j] > 0) {
                            drop_balance << " - "
                                         << vehicleTransferName(k, i, j);
                        }
                    }
                    drop_balance << " = 0";
                    row(drop_balance.str());
                }
                for (int i = 1; i <= instance.V; ++i) {
                    const int pickup_cap =
                        std::min(instance.initial[i],
                                 k < static_cast<int>(instance.Q.size())
                                     ? instance.Q[k] : max_vehicle_capacity);
                    std::ostringstream unload_link;
                    unload_link << vehicleUnloadName(k, i)
                                << " - " << num(std::max(0, pickup_cap)) << " "
                                << routeVisitName(k, i) << " <= 0";
                    row(unload_link.str());
                    for (int j = 1; j <= instance.V; ++j) {
                        const int cap = vehicle_transfer_cap[k][i][j];
                        if (cap <= 0) continue;
                        std::ostringstream transfer_link;
                        transfer_link << vehicleTransferName(k, i, j);
                        const int bit_i = 1 << (i - 1);
                        const int bit_j = 1 << (j - 1);
                        bool any_mask = false;
                        for (int mask : allowed_route_masks_by_vehicle[k]) {
                            if ((mask & bit_i) && (mask & bit_j)) {
                                transfer_link << " - " << num(cap) << " "
                                              << routeMaskName(k, mask);
                                any_mask = true;
                            }
                        }
                        if (!any_mask) {
                            transfer_link << " <= 0";
                        } else {
                            transfer_link << " <= 0";
                        }
                        row(transfer_link.str());
                    }
                }
            }
        }
    }

    const int max_route_cut_size = (instance.V <= 12) ? instance.V : 5;
    std::vector<int> subset;
    std::function<void(int, int)> generateRouteCut = [&](int next_station, int target_size) {
        if (static_cast<int>(subset.size()) == target_size) {
            int mask = 0;
            for (int station : subset) mask |= (1 << (station - 1));
            const double travel_lb = (mask >= 0 && mask < static_cast<int>(route_subset_lb.size()))
                ? route_subset_lb[mask]
                : partitionTravelLowerBound(metric_dist, mask, instance.V, instance.M);
            std::ostringstream cut;
            bool first_term = true;
            auto add = [&](double coeff, const std::string& var) {
                if (std::fabs(coeff) <= 1e-12) return;
                if (!first_term) cut << " + ";
                cut << num(coeff) << " " << var;
                first_term = false;
            };
            for (int station : subset) add(unit_operation_time, pName(station));
            for (int station : subset) add(travel_lb, vName(station));
            if (first_term) cut << "0";
            cut << " <= "
                << num(instance.M * instance.total_time_limit +
                       (target_size - 1) * travel_lb);
            row(cut.str());
            return;
        }
        for (int station = next_station; station <= instance.V; ++station) {
            if (static_cast<int>(subset.size()) + (instance.V - station + 1) < target_size) break;
            subset.push_back(station);
            generateRouteCut(station + 1, target_size);
            subset.pop_back();
        }
    };
    for (int size = 2; size <= max_route_cut_size; ++size) {
        generateRouteCut(1, size);
    }

    std::ostringstream bike_total;
    for (int i = 1; i <= instance.V; ++i) {
        if (i > 1) bike_total << " + ";
        bike_total << yName(i);
    }
    bike_total << " <= " << total_initial;
    row(bike_total.str());
    std::ostringstream bike_return_cap;
    for (int i = 1; i <= instance.V; ++i) {
        if (i > 1) bike_return_cap << " + ";
        bike_return_cap << yName(i);
    }
    bike_return_cap << " >= " << min_station_bikes_after_return;
    row(bike_return_cap.str());

    for (int i = 1; i <= instance.V; ++i) {
        for (int j = i + 1; j <= instance.V; ++j) {
            row(rName(i) + " - " + rName(j) + " - " + hName(i, j) + " <= 0");
            row("- " + rName(i) + " + " + rName(j) + " - " + hName(i, j) + " <= 0");
        }
    }

    std::ostringstream hsum;
    std::ostringstream hneg;
    bool first = true;
    for (int i = 1; i <= instance.V; ++i) {
        for (int j = i + 1; j <= instance.V; ++j) {
            if (!first) hsum << " + ";
            first = false;
            hsum << hName(i, j);
            hneg << " - " << hName(i, j);
        }
    }
    const std::string h_positive = first ? "0" : hsum.str();
    const std::string h_negative = hneg.str();
    std::ostringstream sneg;
    for (int i = 1; i <= instance.V; ++i) {
        sneg << " - " << rName(i);
    }
    row(h_positive + " - " + num(static_cast<double>(instance.V) * gamma_cap) +
        " Sbound <= 0");
    row("Sbound" + sneg.str() + " = 0");
    if (gamma_floor >= 0.0) {
        row(h_positive + " - " + num(static_cast<double>(instance.V) * gamma_floor) +
            " Sbound >= 0");
    }
    row("gbound >= " + num(std::max(0.0, gamma_floor)));
    row("gbound - " + num(h_coeff) + " Hbound >= 0");
    row("Hbound" + h_negative + " = 0");

    lp << "Bounds\n";
    for (int i = 1; i <= instance.V; ++i) {
        lp << " " << inventory_lower[i] << " <= " << yName(i)
           << " <= " << inventory_upper[i] << "\n";
        lp << " 0 <= " << pName(i) << "\n";
        lp << " 0 <= " << dName(i) << "\n";
        lp << " 0 <= " << vName(i) << " <= 1\n";
        lp << " 0 <= " << modeName(i) << " <= 1\n";
        lp << " 0 <= " << rName(i) << "\n";
        lp << " 0 <= " << eName(i) << "\n";
        for (int j = i + 1; j <= instance.V; ++j) {
            lp << " 0 <= " << hName(i, j) << "\n";
        }
    }
    if (aggregate_compat_flow) {
        for (int i = 1; i <= instance.V; ++i) {
            const int pickup_cap =
                std::min(instance.initial[i], max_vehicle_capacity);
            lp << " 0 <= " << unloadName(i) << " <= "
               << std::max(0, pickup_cap) << "\n";
            for (int j = 1; j <= instance.V; ++j) {
                if (!pickup_drop_compatible[i][j]) continue;
                const int transfer_cap = pickup_drop_transfer_cap[i][j] > 0
                    ? pickup_drop_transfer_cap[i][j]
                    : pickup_cap;
                lp << " 0 <= " << transferName(i, j) << " <= "
                   << transfer_cap << "\n";
            }
        }
    }
    if (route_mask_relaxation) {
        for (int k = 0; k < instance.M; ++k) {
            for (int i = 1; i <= instance.V; ++i) {
                if (vehicle_indexed_ops) {
                    lp << " 0 <= " << routeVisitName(k, i) << " <= 1\n";
                }
                lp << " 0 <= " << routePickupName(k, i) << "\n";
                lp << " 0 <= " << routeDropName(k, i) << "\n";
                if (vehicle_transfer_flow) {
                    const int pickup_cap =
                        std::min(instance.initial[i],
                                 k < static_cast<int>(instance.Q.size())
                                     ? instance.Q[k] : max_vehicle_capacity);
                    lp << " 0 <= " << vehicleUnloadName(k, i) << " <= "
                       << std::max(0, pickup_cap) << "\n";
                    for (int j = 1; j <= instance.V; ++j) {
                        const int cap = vehicle_transfer_cap[k][i][j];
                        if (cap <= 0) continue;
                        lp << " 0 <= " << vehicleTransferName(k, i, j)
                           << " <= " << cap << "\n";
                    }
                }
            }
        }
    }
    lp << " 0 <= Sbound\n";
    lp << " 0 <= Hbound\n";
    lp << " 0 <= gbound\n";
    if (integer_inventory_relaxation) {
        lp << "Generals\n";
        for (int i = 1; i <= instance.V; ++i) {
            lp << " " << yName(i) << " " << pName(i) << " " << dName(i) << "\n";
        }
        lp << "Binary\n";
        for (int i = 1; i <= instance.V; ++i) {
            lp << " " << vName(i) << "\n";
        }
        if (route_mask_relaxation) {
            for (int k = 0; k < instance.M; ++k) {
                for (int mask : allowed_route_masks_by_vehicle[k]) {
                    lp << " " << routeMaskName(k, mask) << "\n";
                }
            }
        }
    }
    lp << "End\n";
    lp.close();
    bound.vehicle_indexed_relaxation_time_seconds =
        vehicle_indexed_ops
            ? std::chrono::duration<double>(
                  std::chrono::steady_clock::now() - vehicle_relax_start).count()
            : 0.0;

    const bool continuous_precheck_promising =
        cutoff_bound_active &&
        (gamma_cap <= objective_cutoff * 0.5 ||
         gamma_floor >= objective_cutoff * 0.75);
    if (integer_inventory_relaxation && continuous_precheck_promising) {
        const auto precheck_start = std::chrono::steady_clock::now();
        bound.continuous_relaxation_precheck_run = true;
        const std::filesystem::path cont_sol_path =
            work_dir / "inventory_gini_bound_continuous.sol";
        const std::filesystem::path cont_log_path =
            work_dir / "inventory_gini_bound_continuous.log";
        const std::filesystem::path cont_cmd_path =
            work_dir / "run_continuous.cplex";
        const double cont_time_limit =
            std::max(0.1, std::min(0.5, time_limit_seconds * 0.05));
        std::ofstream cont_cmd(cont_cmd_path);
        cont_cmd << "set threads 1\n";
        cont_cmd << "set timelimit " << cont_time_limit << "\n";
        cont_cmd << "read " << lp_path.string() << "\n";
        cont_cmd << "change problem lp\n";
        cont_cmd << "optimize\n";
        cont_cmd << "write " << cont_sol_path.string() << "\n";
        cont_cmd << "quit\n";
        cont_cmd.close();

        const std::string cont_command = "cmd /C \"" +
            quote(defaultCplexPath()) + " -f " + quote(cont_cmd_path) +
            " > " + quote(cont_log_path) + " 2>&1\"";
        const int cont_rc = std::system(cont_command.c_str());
        bound.continuous_relaxation_precheck_time_seconds =
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - precheck_start).count();
        if (cont_rc == 0) {
            std::string cont_status = "unknown";
            const double cont_obj = parseObjective(cont_sol_path, cont_status);
            bound.continuous_relaxation_precheck_status = cont_status;
            if (std::isfinite(cont_obj)) {
                bound.continuous_relaxation_precheck_objective =
                    cutoffCappedLowerBound(cont_obj);
            }
            const bool cont_infeasible =
                statusIsInfeasible(cont_status) ||
                (!std::filesystem::exists(cont_sol_path) &&
                 logSaysInfeasible(cont_log_path));
            if (cont_infeasible) {
                bound.computed = true;
                bound.infeasible = false;
                bound.continuous_relaxation_precheck_infeasible = true;
                bound.continuous_relaxation_precheck_fathomed = true;
                bound.objective_lower_bound = objective_cutoff;
                bound.gini_lower_bound = floor_bound;
                bound.lambda_penalty_lower_bound =
                    std::max(0.0, bound.objective_lower_bound -
                                  bound.gini_lower_bound);
                bound.status = "continuous relaxation infeasible";
                std::ostringstream note;
                note << "inventory-route-Gini cutoff relaxation infeasible in continuous LP precheck; no incumbent-improving solution exists in this interval: interval=["
                     << gamma_floor << "," << gamma_cap << "]"
                     << ", pickup_limit=" << bound.total_pickup_limit
                     << ", route_visit_cuts=singletons+subsets_up_to_"
                     << max_route_cut_size
                     << ", integer_inventory_relaxation=true"
                     << ", continuous_relaxation_precheck=true"
                     << ", continuous_relaxation_precheck_infeasible=true"
                     << ", continuous_relaxation_precheck_time_seconds="
                     << bound.continuous_relaxation_precheck_time_seconds
                     << ", station_flow_conservation=true"
                     << ", depot_return_capacity=true"
                     << ", station_operation_capacity=true"
                     << ", station_operation_mode_cuts=true"
                     << ", nonzero_visit_operation_cuts=true"
                     << ", route_mask_duration_load_relaxation="
                     << (route_mask_relaxation ? "true" : "false")
                     << ", route_mask_max_v=" << route_mask_max_v
                     << routeMaskSupportNote()
                     << pickupDropCompatNote()
                     << ", incumbent_cutoff_bound=true"
                     << ", penalty_budget=" << num(penalty_budget)
                     << ", min_station_bikes=" << min_station_bikes_after_return
                     << ", objective_lb=" << bound.objective_lower_bound
                     << ", status=" << bound.status
                     << ", lp=" << lp_path.string();
                bound.note = note.str();
                return bound;
            }
            if (statusIsOptimal(cont_status) && std::isfinite(cont_obj)) {
                const double cont_lb = std::max(
                    cutoffCappedLowerBound(cont_obj),
                    bound.projection_bound_valid
                        ? bound.projection_objective_lower_bound : 0.0);
                bound.continuous_relaxation_precheck_objective = cont_lb;
                if (cont_lb >= objective_cutoff - 1e-9) {
                    bound.computed = true;
                    bound.continuous_relaxation_precheck_fathomed = true;
                    bound.objective_lower_bound = objective_cutoff;
                    bound.gini_lower_bound = floor_bound;
                    bound.lambda_penalty_lower_bound =
                        std::max(0.0, bound.objective_lower_bound -
                                      bound.gini_lower_bound);
                    bound.status = cont_status;
                    std::ostringstream note;
                    note << "inventory-route-Gini continuous relaxation cutoff-fathomed this interval before integer route-mask MIP: interval=["
                         << gamma_floor << "," << gamma_cap << "]"
                         << ", pickup_limit=" << bound.total_pickup_limit
                         << ", route_visit_cuts=singletons+subsets_up_to_"
                         << max_route_cut_size
                         << ", integer_inventory_relaxation=true"
                         << ", continuous_relaxation_precheck=true"
                         << ", continuous_relaxation_precheck_objective="
                         << cont_lb
                         << ", continuous_relaxation_precheck_time_seconds="
                         << bound.continuous_relaxation_precheck_time_seconds
                         << ", station_flow_conservation=true"
                         << ", depot_return_capacity=true"
                         << ", station_operation_capacity=true"
                         << ", station_operation_mode_cuts=true"
                         << ", nonzero_visit_operation_cuts=true"
                         << ", route_mask_duration_load_relaxation="
                         << (route_mask_relaxation ? "true" : "false")
                         << ", route_mask_max_v=" << route_mask_max_v
                         << routeMaskSupportNote()
                         << pickupDropCompatNote()
                         << ", incumbent_cutoff_bound=true"
                         << ", penalty_budget=" << num(penalty_budget)
                         << ", min_station_bikes="
                         << min_station_bikes_after_return
                         << ", objective_lb=" << bound.objective_lower_bound
                         << ", status=" << cont_status
                         << ", lp=" << lp_path.string();
                    bound.note = note.str();
                    return bound;
                }
            }
        } else {
            bound.continuous_relaxation_precheck_status =
                "command_failed_" + std::to_string(cont_rc);
        }
    }

    std::ofstream cmd(cmd_path);
    cmd << "set threads 1\n";
    cmd << "set timelimit " << std::max(0.1, time_limit_seconds) << "\n";
    if (integer_inventory_relaxation) {
        cmd << "set mip tolerances mipgap 1e-8\n";
    }
    cmd << "read " << lp_path.string() << "\n";
    cmd << "optimize\n";
    cmd << "write " << sol_path.string() << "\n";
    cmd << "quit\n";
    cmd.close();

    const std::string command = "cmd /C \"" + quote(defaultCplexPath()) + " -f "
        + quote(cmd_path) + " > " + quote(log_path) + " 2>&1\"";
    const int rc = std::system(command.c_str());
    if (rc != 0) {
        bound.note = "inventory-Gini relaxation CPLEX command failed with return code " +
            std::to_string(rc);
        return bound;
    }
    if (!std::filesystem::exists(sol_path) && logSaysInfeasible(log_path)) {
        bound.computed = true;
        bound.infeasible = !cutoff_bound_active;
        bound.objective_lower_bound = cutoff_bound_active
            ? objective_cutoff
            : std::numeric_limits<double>::infinity();
        bound.status = "infeasible";
        bound.gini_lower_bound = floor_bound;
        bound.lambda_penalty_lower_bound =
            std::max(0.0, bound.objective_lower_bound - bound.gini_lower_bound);
        if (cutoff_bound_active) {
            std::ostringstream note;
            note << "inventory-route-Gini cutoff relaxation infeasible; no incumbent-improving solution exists in this interval: interval=["
                 << gamma_floor << "," << gamma_cap << "]"
                 << ", pickup_limit=" << bound.total_pickup_limit
                 << ", route_visit_cuts=singletons+subsets_up_to_" << max_route_cut_size
                 << ", integer_inventory_relaxation="
                 << (integer_inventory_relaxation ? "true" : "false")
                 << ", station_flow_conservation=true"
                 << ", depot_return_capacity=true"
                 << ", station_operation_capacity=true"
                 << ", station_operation_mode_cuts=true"
                 << ", nonzero_visit_operation_cuts=true"
                 << ", route_mask_duration_load_relaxation="
                 << (route_mask_relaxation ? "true" : "false")
                 << ", route_mask_max_v=" << route_mask_max_v
                 << routeMaskSupportNote()
                 << pickupDropCompatNote()
                 << ", incumbent_cutoff_bound=true"
                 << ", penalty_budget=" << num(penalty_budget)
                 << ", min_station_bikes=" << min_station_bikes_after_return
                 << ", objective_lb=" << bound.objective_lower_bound
                 << ", lp=" << lp_path.string();
            bound.note = note.str();
        } else {
            bound.note = "inventory-route-Gini relaxation infeasible; original interval is empty under necessary inventory/resource conditions";
        }
        return bound;
    }

    std::string status = "unknown";
    const double obj = parseObjective(sol_path, status);
    bound.status = status;
    if (statusIsInfeasible(status)) {
        bound.computed = true;
        bound.infeasible = !cutoff_bound_active;
        bound.objective_lower_bound = cutoff_bound_active
            ? objective_cutoff
            : std::numeric_limits<double>::infinity();
        bound.gini_lower_bound = floor_bound;
        bound.lambda_penalty_lower_bound =
            std::max(0.0, bound.objective_lower_bound - bound.gini_lower_bound);
        if (cutoff_bound_active) {
            std::ostringstream note;
            note << "inventory-route-Gini cutoff relaxation infeasible; no incumbent-improving solution exists in this interval: interval=["
                 << gamma_floor << "," << gamma_cap << "]"
                 << ", pickup_limit=" << bound.total_pickup_limit
                 << ", route_visit_cuts=singletons+subsets_up_to_" << max_route_cut_size
                 << ", integer_inventory_relaxation="
                 << (integer_inventory_relaxation ? "true" : "false")
                 << ", station_flow_conservation=true"
                 << ", depot_return_capacity=true"
                 << ", station_operation_capacity=true"
                 << ", station_operation_mode_cuts=true"
                 << ", nonzero_visit_operation_cuts=true"
                 << ", route_mask_duration_load_relaxation="
                 << (route_mask_relaxation ? "true" : "false")
                 << ", route_mask_max_v=" << route_mask_max_v
                 << routeMaskSupportNote()
                 << pickupDropCompatNote()
                 << ", incumbent_cutoff_bound=true"
                 << ", penalty_budget=" << num(penalty_budget)
                 << ", min_station_bikes=" << min_station_bikes_after_return
                 << ", objective_lb=" << bound.objective_lower_bound
                 << ", status=" << status
                 << ", lp=" << lp_path.string();
            bound.note = note.str();
        } else {
            bound.note = "inventory-route-Gini relaxation infeasible; original interval is empty under necessary inventory/resource conditions";
        }
        return bound;
    }
    if (!statusIsOptimal(status) || !std::isfinite(obj)) {
        const double mip_best_bound = integer_inventory_relaxation
            ? parseMipBestBound(log_path)
            : std::numeric_limits<double>::quiet_NaN();
        if (std::isfinite(mip_best_bound)) {
            bound.computed = true;
            bound.objective_lower_bound = std::max(
                cutoffCappedLowerBound(mip_best_bound),
                bound.projection_bound_valid ? bound.projection_objective_lower_bound : 0.0);
            bound.gini_lower_bound = floor_bound;
            bound.lambda_penalty_lower_bound =
                std::max(0.0, bound.objective_lower_bound - bound.gini_lower_bound);
            std::ostringstream note;
            note << "inventory-route-Gini integer relaxation time-limited; using valid CPLEX MIP best bound: interval=["
                 << gamma_floor << "," << gamma_cap << "]"
                 << ", pickup_limit=" << bound.total_pickup_limit
                 << ", route_visit_cuts=singletons+subsets_up_to_" << max_route_cut_size
                 << ", integer_inventory_relaxation=true"
                 << ", station_flow_conservation=true"
                 << ", depot_return_capacity=true"
                 << ", station_operation_capacity=true"
                 << ", station_operation_mode_cuts=true"
                 << ", nonzero_visit_operation_cuts=true"
                 << ", route_mask_duration_load_relaxation="
                 << (route_mask_relaxation ? "true" : "false")
                 << ", route_mask_max_v=" << route_mask_max_v
                 << routeMaskSupportNote()
                 << pickupDropCompatNote()
                 << ", incumbent_cutoff_bound=" << (cutoff_bound_active ? "true" : "false")
                 << ", penalty_budget=" << (cutoff_bound_active ? num(penalty_budget) : "inf")
                 << ", penalty_domain_tightening=" << (penalty_domain_tightening_enabled ? "true" : "false")
                 << ", domains_tightened=" << bound.domains_tightened_count
                 << ", domain_width_before=" << bound.total_domain_width_before
                 << ", domain_width_after=" << bound.total_domain_width_after
                 << ", projection_bound_enabled=" << (projection_bound_enabled ? "true" : "false")
                 << ", projection_bound_valid=" << (bound.projection_bound_valid ? "true" : "false")
                 << ", projection_bound_lb=" << bound.projection_objective_lower_bound
                 << ", projection_bound_scope=" << bound.projection_bound_scope
                 << ", min_station_bikes=" << min_station_bikes_after_return
                 << ", s_upper=" << s_upper
                 << ", objective_lb=" << bound.objective_lower_bound
                 << ", status=" << status
                 << ", lp=" << lp_path.string();
            bound.note = note.str();
            return bound;
        }
        bound.note = "inventory-Gini relaxation did not solve to optimality: " + status;
        return bound;
    }
    bound.computed = true;
    bound.objective_lower_bound = std::max(
        cutoffCappedLowerBound(obj),
        bound.projection_bound_valid ? bound.projection_objective_lower_bound : 0.0);
    bound.gini_lower_bound = floor_bound;
    bound.lambda_penalty_lower_bound =
        std::max(0.0, bound.objective_lower_bound - bound.gini_lower_bound);
    std::ostringstream note;
    note << "inventory-route-Gini relaxation lower bound: interval=["
         << gamma_floor << "," << gamma_cap << "]"
         << ", pickup_limit=" << bound.total_pickup_limit
         << ", route_visit_cuts=singletons+subsets_up_to_" << max_route_cut_size
         << ", integer_inventory_relaxation="
         << (integer_inventory_relaxation ? "true" : "false")
         << ", station_flow_conservation=true"
         << ", depot_return_capacity=true"
         << ", station_operation_capacity=true"
         << ", station_operation_mode_cuts=true"
         << ", nonzero_visit_operation_cuts=true"
         << ", route_mask_duration_load_relaxation="
         << (route_mask_relaxation ? "true" : "false")
         << ", route_mask_max_v=" << route_mask_max_v
        << routeMaskSupportNote()
        << pickupDropCompatNote()
         << ", incumbent_cutoff_bound=" << (cutoff_bound_active ? "true" : "false")
         << ", penalty_budget=" << (cutoff_bound_active ? num(penalty_budget) : "inf")
         << ", penalty_domain_tightening=" << (penalty_domain_tightening_enabled ? "true" : "false")
         << ", domains_tightened=" << bound.domains_tightened_count
         << ", domain_width_before=" << bound.total_domain_width_before
         << ", domain_width_after=" << bound.total_domain_width_after
         << ", projection_bound_enabled=" << (projection_bound_enabled ? "true" : "false")
         << ", projection_bound_valid=" << (bound.projection_bound_valid ? "true" : "false")
         << ", projection_bound_lb=" << bound.projection_objective_lower_bound
         << ", projection_bound_scope=" << bound.projection_bound_scope
         << ", min_station_bikes=" << min_station_bikes_after_return
         << ", s_upper=" << s_upper
         << ", objective_lb=" << bound.objective_lower_bound
         << ", status=" << status
         << ", lp=" << lp_path.string();
    bound.note = note.str();
    return bound;
}

} // namespace ebrp
