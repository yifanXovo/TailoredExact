#include "TailoredExact.hpp"

#include "CplexBaseline.hpp"
#include "Evaluator.hpp"
#include "Logger.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <future>
#include <limits>
#include <numeric>
#include <sstream>
#include <unordered_map>

namespace ebrp {
namespace {

using Clock = std::chrono::steady_clock;

struct Column {
    int vehicle = 0;
    int mask = 0;
    std::vector<int> path;      // station sequence, no depot
    std::vector<int> q;         // index 1..V, pickup positive, drop negative
    int pickup = 0;
    double travel = 0.0;
    double duration = 0.0;
};

struct EnumStats {
    long long dfs_states = 0;
    long long generated_columns = 0;
    bool timed_out = false;
};

struct EnumOutput {
    std::vector<Column> columns;
    EnumStats stats;
};

void appendInt(std::string& key, int value) {
    for (int shift = 0; shift < 32; shift += 8) {
        key.push_back(static_cast<char>((static_cast<unsigned int>(value) >> shift) & 0xffU));
    }
}

std::string columnKey(const std::vector<int>& q) {
    std::string key;
    key.reserve(q.size() * sizeof(int));
    for (int value : q) appendInt(key, value);
    return key;
}

std::string stateKey(int mask, const std::vector<int>& y, int V) {
    std::string key;
    key.reserve((V + 2) * sizeof(int));
    appendInt(key, mask);
    for (int i = 1; i <= V; ++i) appendInt(key, y[i]);
    return key;
}

class VehicleEnumerator {
public:
    VehicleEnumerator(const Instance& instance,
                      int vehicle,
                      double deadline_seconds,
                      Clock::time_point start,
                      std::atomic<bool>& stop)
        : instance_(instance),
          vehicle_(vehicle),
          deadline_seconds_(deadline_seconds),
          start_(start),
          stop_(stop) {}

    EnumOutput enumerate(int threads) {
        EnumOutput out;
        if (threads <= 1 || instance_.V <= 1) {
            std::unordered_map<std::string, Column> best;
            for (int first = 1; first <= instance_.V; ++first) {
                enumerateFirst(first, best, out.stats);
                if (stop_.load()) break;
            }
            if (stop_.load()) {
                out.stats.timed_out = true;
                return out;
            }
            out.columns = mapToVector(best);
            out.stats.timed_out = stop_.load();
            return out;
        }

        std::vector<std::future<EnumOutput>> futures;
        for (int first = 1; first <= instance_.V; ++first) {
            futures.push_back(std::async(std::launch::async, [this, first]() {
                EnumOutput part;
                std::unordered_map<std::string, Column> local;
                enumerateFirst(first, local, part.stats);
                if (stop_.load()) {
                    part.stats.timed_out = true;
                    return part;
                }
                part.columns = mapToVector(local);
                part.stats.timed_out = stop_.load();
                return part;
            }));
        }

        std::unordered_map<std::string, Column> merged;
        for (auto& fut : futures) {
            EnumOutput part = fut.get();
            out.stats.dfs_states += part.stats.dfs_states;
            out.stats.generated_columns += part.stats.generated_columns;
            out.stats.timed_out = out.stats.timed_out || part.stats.timed_out;
            if (out.stats.timed_out || stop_.load()) {
                stop_.store(true);
                out.columns.clear();
                continue;
            }
            for (const Column& col : part.columns) {
                insertBest(merged, col);
            }
        }
        if (!out.stats.timed_out && !stop_.load()) out.columns = mapToVector(merged);
        out.stats.timed_out = out.stats.timed_out || stop_.load();
        return out;
    }

private:
    const Instance& instance_;
    int vehicle_;
    double deadline_seconds_;
    Clock::time_point start_;
    std::atomic<bool>& stop_;

    bool shouldStop() {
        if (stop_.load()) return true;
        if (deadline_seconds_ <= 0.0) return false;
        const double elapsed = std::chrono::duration<double>(Clock::now() - start_).count();
        if (elapsed >= deadline_seconds_) {
            stop_.store(true);
            return true;
        }
        return false;
    }

    static std::vector<Column> mapToVector(const std::unordered_map<std::string, Column>& best) {
        std::vector<Column> columns;
        columns.reserve(best.size());
        for (const auto& kv : best) columns.push_back(kv.second);
        return columns;
    }

    static void insertBest(std::unordered_map<std::string, Column>& best, const Column& col) {
        std::string key = columnKey(col.q);
        auto it = best.find(key);
        if (it == best.end() || col.duration < it->second.duration - 1e-9) {
            best[std::move(key)] = col;
        }
    }

    void addColumn(const std::vector<int>& path,
                   const std::vector<int>& q,
                   int mask,
                   int pickup,
                   double travel,
                   std::unordered_map<std::string, Column>& best,
                   EnumStats& stats) {
        if (path.empty()) return;
        const double duration = travel + (instance_.pickup_time + instance_.drop_time) * pickup;
        if (duration > instance_.total_time_limit + 1e-9) return;
        Column col;
        col.vehicle = vehicle_;
        col.mask = mask;
        col.path = path;
        col.q = q;
        col.pickup = pickup;
        col.travel = travel;
        col.duration = duration;
        insertBest(best, col);
        ++stats.generated_columns;
    }

    void enumerateFirst(int first,
                        std::unordered_map<std::string, Column>& best,
                        EnumStats& stats) {
        if (shouldStop()) return;
        const double travel = instance_.dist[0][first];
        const double return_travel = instance_.dist[first][0];
        if (travel + return_travel > instance_.total_time_limit + 1e-9) return;
        std::vector<int> path{first};
        routeDfs(path, 1 << (first - 1), first, travel, best, stats);
    }

    void routeDfs(std::vector<int>& path,
                  int mask,
                  int last,
                  double travel_without_return,
                  std::unordered_map<std::string, Column>& best,
                  EnumStats& stats) {
        ++stats.dfs_states;
        if ((stats.dfs_states & 0x3fff) == 0 && shouldStop()) return;

        const double route_travel = travel_without_return + instance_.dist[last][0];
        if (route_travel <= instance_.total_time_limit + 1e-9) {
            enumerateOperationsForPath(path, mask, route_travel, best, stats);
        }

        for (int i = 1; i <= instance_.V; ++i) {
            const int bit = 1 << (i - 1);
            if (mask & bit) continue;
            const double travel2 = travel_without_return + instance_.dist[last][i];
            const double return_travel = instance_.dist[i][0];
            if (travel2 + return_travel > instance_.total_time_limit + 1e-9) {
                continue;
            }
            path.push_back(i);
            routeDfs(path, mask | bit, i, travel2, best, stats);
            path.pop_back();
        }
    }

    void enumerateOperationsForPath(const std::vector<int>& path,
                                    int mask,
                                    double route_travel,
                                    std::unordered_map<std::string, Column>& best,
                                    EnumStats& stats) {
        const double cunit = instance_.pickup_time + instance_.drop_time;
        const int pickup_budget = static_cast<int>(
            std::floor((instance_.total_time_limit - route_travel) / cunit + 1e-9));
        if (pickup_budget <= 0) return;
        std::vector<int> q(instance_.V + 1, 0);
        operationDfs(path, 0, mask, route_travel, 0, 0, pickup_budget, q, best, stats);
    }

    void operationDfs(const std::vector<int>& path,
                      std::size_t pos,
                      int mask,
                      double route_travel,
                      int load,
                      int pickup,
                      int pickup_budget,
                      std::vector<int>& q,
                      std::unordered_map<std::string, Column>& best,
                      EnumStats& stats) {
        if ((stats.generated_columns & 0xffff) == 0 && shouldStop()) return;
        if (pos == path.size()) {
            if (pickup > 0) addColumn(path, q, mask, pickup, route_travel, best, stats);
            return;
        }

        const int station = path[pos];
        const int q_capacity = instance_.Q[vehicle_];

        const int max_pick = std::min({
            instance_.initial[station],
            q_capacity - load,
            pickup_budget - pickup
        });
        for (int p = 1; p <= max_pick; ++p) {
            if (shouldStop()) return;
            q[station] = p;
            operationDfs(path, pos + 1, mask, route_travel, load + p, pickup + p,
                         pickup_budget, q, best, stats);
            q[station] = 0;
        }

        const int max_drop = std::min(instance_.capacity[station] - instance_.initial[station], load);
        for (int d = 1; d <= max_drop; ++d) {
            if (shouldStop()) return;
            q[station] = -d;
            operationDfs(path, pos + 1, mask, route_travel, load - d, pickup,
                         pickup_budget, q, best, stats);
            q[station] = 0;
        }
    }
};

struct MasterState {
    int mask = 0;
    std::vector<int> y;
    std::vector<int> selected; // per vehicle, column index or -1
};

struct MasterOutput {
    bool complete = true;
    long long states_processed = 0;
    MasterState best_state;
    ObjectiveParts best_parts;
};

struct InventorySearchOutput {
    bool complete = false;
    bool has_solution = false;
    long long nodes = 0;
    long long route_checks = 0;
    long long domain_values = 0;
    int max_domain_size = 0;
    ObjectiveParts best_parts;
    std::vector<int> best_y;
    std::vector<RoutePlan> best_routes;
    double runtime_seconds = 0.0;
};

bool deadlineReached(Clock::time_point start, double limit_seconds) {
    if (limit_seconds <= 0.0) return false;
    return std::chrono::duration<double>(Clock::now() - start).count() >= limit_seconds;
}

struct RouteOracleResult {
    bool feasible = false;
    double travel = 0.0;
    std::vector<int> path;
};

RouteOracleResult checkOneVehicleRoute(const Instance& instance,
                                       const std::vector<int>& q,
                                       int vehicle,
                                       int mask) {
    RouteOracleResult out;
    if (mask == 0) {
        out.feasible = true;
        return out;
    }

    const int V = instance.V;
    const int Q = instance.Q[vehicle];
    const int nmask = 1 << V;
    const double inf = 1e100;
    std::vector<int> load_sum(nmask, 0);
    std::vector<int> pickup_sum(nmask, 0);
    for (int m = 1; m < nmask; ++m) {
        const int bit = m & -m;
        const int idx = __builtin_ctz(static_cast<unsigned int>(bit)) + 1;
        const int prev = m ^ bit;
        load_sum[m] = load_sum[prev] + q[idx];
        pickup_sum[m] = pickup_sum[prev] + std::max(0, q[idx]);
    }
    const double operation_time = (instance.pickup_time + instance.drop_time) * pickup_sum[mask];
    if (operation_time > instance.total_time_limit + 1e-9) return out;

    std::vector<std::vector<double>> dp(nmask, std::vector<double>(V + 1, inf));
    std::vector<std::vector<int>> parent(nmask, std::vector<int>(V + 1, -1));
    for (int i = 1; i <= V; ++i) {
        const int bit = 1 << (i - 1);
        if (!(mask & bit)) continue;
        if (q[i] < 0 || q[i] > Q) continue;
        dp[bit][i] = instance.dist[0][i];
    }
    for (int s = 1; s < nmask; ++s) {
        if ((s & mask) != s) continue;
        const int load = load_sum[s];
        if (load < 0 || load > Q) continue;
        for (int last = 1; last <= V; ++last) {
            const double cur = dp[s][last];
            if (cur >= inf / 2) continue;
            int rem = mask ^ s;
            while (rem) {
                const int bit = rem & -rem;
                const int nxt = __builtin_ctz(static_cast<unsigned int>(bit)) + 1;
                const int ns = s | bit;
                const int nload = load_sum[ns];
                if (nload >= 0 && nload <= Q) {
                    const double nv = cur + instance.dist[last][nxt];
                    if (nv < dp[ns][nxt]) {
                        dp[ns][nxt] = nv;
                        parent[ns][nxt] = last;
                    }
                }
                rem -= bit;
            }
        }
    }

    double best = inf;
    int best_last = -1;
    for (int last = 1; last <= V; ++last) {
        const double val = dp[mask][last] + instance.dist[last][0];
        if (val < best) {
            best = val;
            best_last = last;
        }
    }
    if (best_last < 0 || best + operation_time > instance.total_time_limit + 1e-9) return out;

    std::vector<int> rev;
    int s = mask;
    int last = best_last;
    while (last > 0) {
        rev.push_back(last);
        const int bit = 1 << (last - 1);
        const int prev_last = parent[s][last];
        s ^= bit;
        last = prev_last;
        if (s == 0) break;
    }
    std::reverse(rev.begin(), rev.end());
    out.feasible = true;
    out.travel = best;
    out.path = std::move(rev);
    return out;
}

std::vector<double> computeDepotCycleLowerBounds(const Instance& instance) {
    const int V = instance.V;
    const int nmask = 1 << V;
    const double inf = 1e100;
    std::vector<std::vector<double>> dp(nmask, std::vector<double>(V + 1, inf));
    for (int i = 1; i <= V; ++i) dp[1 << (i - 1)][i] = instance.dist[0][i];
    for (int mask = 1; mask < nmask; ++mask) {
        for (int last = 1; last <= V; ++last) {
            const double cur = dp[mask][last];
            if (cur >= inf / 2) continue;
            int rem = (nmask - 1) ^ mask;
            while (rem) {
                const int bit = rem & -rem;
                const int nxt = __builtin_ctz(static_cast<unsigned int>(bit)) + 1;
                const int nm = mask | bit;
                dp[nm][nxt] = std::min(dp[nm][nxt], cur + instance.dist[last][nxt]);
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
            const int last = __builtin_ctz(static_cast<unsigned int>(bit)) + 1;
            best = std::min(best, dp[mask][last] + instance.dist[last][0]);
            m -= bit;
        }
        tsp[mask] = best;
    }
    return tsp;
}

bool buildFeasiblePartitionRoutes(const Instance& instance,
                                  const std::vector<int>& q,
                                  std::vector<RoutePlan>& routes,
                                  long long& route_checks) {
    int active = 0;
    int net = 0;
    for (int i = 1; i <= instance.V; ++i) {
        if (q[i] != 0) active |= 1 << (i - 1);
        net += q[i];
    }
    if (net < 0) return false;

    if (instance.M == 1) {
        ++route_checks;
        RouteOracleResult r = checkOneVehicleRoute(instance, q, 0, active);
        if (!r.feasible) return false;
        RoutePlan route;
        route.vehicle = 0;
        route.nodes.push_back(0);
        for (int station : r.path) {
            route.nodes.push_back(station);
            StopOperation op;
            op.station = station;
            if (q[station] > 0) op.pickup = q[station];
            if (q[station] < 0) op.drop = -q[station];
            route.operations.push_back(op);
        }
        route.nodes.push_back(0);
        routes = {route};
        return true;
    }

    if (instance.M != 2) return false;
    for (int sub = active; ; sub = (sub - 1) & active) {
        const int other = active ^ sub;
        ++route_checks;
        RouteOracleResult r0 = checkOneVehicleRoute(instance, q, 0, sub);
        if (r0.feasible) {
            ++route_checks;
            RouteOracleResult r1 = checkOneVehicleRoute(instance, q, 1, other);
            if (r1.feasible) {
                routes.clear();
                for (int vehicle = 0; vehicle < 2; ++vehicle) {
                    const RouteOracleResult& rr = (vehicle == 0) ? r0 : r1;
                    RoutePlan route;
                    route.vehicle = vehicle;
                    route.nodes.push_back(0);
                    for (int station : rr.path) {
                        route.nodes.push_back(station);
                        StopOperation op;
                        op.station = station;
                        if (q[station] > 0) op.pickup = q[station];
                        if (q[station] < 0) op.drop = -q[station];
                        route.operations.push_back(op);
                    }
                    route.nodes.push_back(0);
                    routes.push_back(std::move(route));
                }
                return true;
            }
        }
        if (sub == 0) break;
    }
    return false;
}

class InventoryBranchSearch {
public:
    InventoryBranchSearch(const Instance& instance,
                          double lambda,
                          double time_limit_seconds,
                          Clock::time_point start,
                          const SolveResult* incumbent = nullptr)
        : instance_(instance),
          lambda_(lambda),
          time_limit_seconds_(time_limit_seconds),
          start_(start),
          max_total_pickup_(instance.M * static_cast<int>(
              std::floor(instance.total_time_limit / (instance.pickup_time + instance.drop_time)))) {
        order_.resize(instance_.V);
        std::iota(order_.begin(), order_.end(), 1);
        std::sort(order_.begin(), order_.end(), [&](int a, int b) {
            return instance_.weights[a] > instance_.weights[b];
        });
        y_.assign(instance_.V + 1, 0);
        assigned_.assign(instance_.V + 1, false);
        q_.assign(instance_.V + 1, 0);
        if (incumbent != nullptr && incumbent->verification.feasible && !incumbent->final_inventory.empty()) {
            output_.best_parts = computeObjectiveParts(instance_, incumbent->final_inventory, lambda_);
            output_.best_y = incumbent->final_inventory;
            output_.best_routes = incumbent->routes;
            output_.has_solution = true;
        } else {
            output_.best_parts = computeObjectiveParts(instance_, instance_.initial, lambda_);
            output_.best_y = instance_.initial;
        }

        domains_.resize(instance_.V + 1);
        min_penalty_.assign(instance_.V + 1, 0.0);
        min_pickup_.assign(instance_.V + 1, 0);
        max_net_q_.assign(instance_.V + 1, 0);
        r_lo_.assign(instance_.V + 1, 0.0);
        r_hi_.assign(instance_.V + 1, 0.0);
        const int max_q = *std::max_element(instance_.Q.begin(), instance_.Q.end());
        for (int i = 1; i <= instance_.V; ++i) {
            const int lo = std::max(0, instance_.initial[i] - max_q);
            const int hi = std::min(instance_.capacity[i], instance_.initial[i] + max_q);
            double best_station_penalty = std::numeric_limits<double>::infinity();
            for (int val = lo; val <= hi; ++val) {
                const double ratio = static_cast<double>(val) / instance_.target[i];
                const double station_penalty = instance_.weights[i] * std::fabs(ratio - 1.0);
                if (lambda_ * station_penalty < output_.best_parts.objective - 1e-12) {
                    domains_[i].push_back(val);
                    best_station_penalty = std::min(best_station_penalty, station_penalty);
                }
            }
            if (domains_[i].empty()) {
                best_station_penalty = std::numeric_limits<double>::infinity();
            }
            std::sort(domains_[i].begin(), domains_[i].end(), [&](int a, int b) {
                const double ta = std::fabs(static_cast<double>(a) / instance_.target[i] - 1.0);
                const double tb = std::fabs(static_cast<double>(b) / instance_.target[i] - 1.0);
                if (std::fabs(ta - tb) > 1e-12) return ta < tb;
                return std::abs(a - instance_.initial[i]) < std::abs(b - instance_.initial[i]);
            });
            if (!domains_[i].empty()) {
                const auto mm = std::minmax_element(domains_[i].begin(), domains_[i].end());
                r_lo_[i] = static_cast<double>(*mm.first) / instance_.target[i];
                r_hi_[i] = static_cast<double>(*mm.second) / instance_.target[i];
                min_penalty_[i] = best_station_penalty;
                int local_min_pickup = std::numeric_limits<int>::max();
                int local_max_net = std::numeric_limits<int>::min();
                for (int val : domains_[i]) {
                    const int q = instance_.initial[i] - val;
                    local_min_pickup = std::min(local_min_pickup, std::max(0, q));
                    local_max_net = std::max(local_max_net, q);
                }
                min_pickup_[i] = local_min_pickup;
                max_net_q_[i] = local_max_net;
            }
            output_.domain_values += static_cast<long long>(domains_[i].size());
            output_.max_domain_size = std::max(output_.max_domain_size,
                                               static_cast<int>(domains_[i].size()));
        }
        std::sort(order_.begin(), order_.end(), [&](int a, int b) {
            const double width_a = r_hi_[a] - r_lo_[a];
            const double width_b = r_hi_[b] - r_lo_[b];
            if (std::fabs(width_a - width_b) > 1e-12) return width_a > width_b;
            if (domains_[a].size() != domains_[b].size()) return domains_[a].size() > domains_[b].size();
            return instance_.weights[a] > instance_.weights[b];
        });
        suffix_min_penalty_.assign(order_.size() + 1, 0.0);
        for (int d = static_cast<int>(order_.size()) - 1; d >= 0; --d) {
            suffix_min_penalty_[d] = suffix_min_penalty_[d + 1] + min_penalty_[order_[d]];
        }
        suffix_min_pickup_.assign(order_.size() + 1, 0);
        suffix_max_net_q_.assign(order_.size() + 1, 0);
        for (int d = static_cast<int>(order_.size()) - 1; d >= 0; --d) {
            const int station = order_[d];
            suffix_min_pickup_[d] = suffix_min_pickup_[d + 1] + min_pickup_[station];
            suffix_max_net_q_[d] = suffix_max_net_q_[d + 1] + max_net_q_[station];
        }
        buildSuffixFeasiblePenaltyTables();
        output_.best_routes.resize(instance_.M);
        if (output_.best_routes.empty() || output_.best_routes.front().nodes.empty()) {
            output_.best_routes.resize(instance_.M);
            for (int k = 0; k < instance_.M; ++k) {
                output_.best_routes[k].vehicle = k;
                output_.best_routes[k].nodes = {0, 0};
            }
        }
        tsp_lb_ = computeDepotCycleLowerBounds(instance_);
        output_.has_solution = true;
    }

    InventorySearchOutput run(int threads = 1) {
        if (threads <= 1 || order_.empty() || domains_[order_.front()].size() <= 1) {
            return runSerial();
        }

        const int root_station = order_.front();
        const int worker_count = std::min<int>(threads, static_cast<int>(domains_[root_station].size()));
        std::vector<std::future<InventorySearchOutput>> futures;
        futures.reserve(worker_count);
        for (int worker_id = 0; worker_id < worker_count; ++worker_id) {
            futures.push_back(std::async(std::launch::async, [this, worker_id, worker_count, root_station]() {
                InventoryBranchSearch worker = *this;
                worker.output_.nodes = 0;
                worker.output_.route_checks = 0;
                worker.output_.complete = false;
                worker.timed_out_ = false;
                for (int idx = worker_id; idx < static_cast<int>(worker.domains_[root_station].size());
                     idx += worker_count) {
                    if (worker.shouldStop()) break;
                    worker.searchRootValue(worker.domains_[root_station][idx]);
                    if (worker.timed_out_) break;
                }
                worker.output_.complete = !worker.timed_out_;
                worker.output_.runtime_seconds =
                    std::chrono::duration<double>(Clock::now() - worker.start_).count();
                return worker.output_;
            }));
        }

        const long long domain_values = output_.domain_values;
        const int max_domain_size = output_.max_domain_size;
        output_.nodes = 0;
        output_.route_checks = 0;
        output_.complete = true;
        for (auto& future : futures) {
            InventorySearchOutput part = future.get();
            output_.nodes += part.nodes;
            output_.route_checks += part.route_checks;
            output_.complete = output_.complete && part.complete;
            if (part.has_solution &&
                (!output_.has_solution ||
                 part.best_parts.objective < output_.best_parts.objective - 1e-12)) {
                output_.has_solution = true;
                output_.best_parts = part.best_parts;
                output_.best_y = std::move(part.best_y);
                output_.best_routes = std::move(part.best_routes);
            }
        }
        output_.domain_values = domain_values;
        output_.max_domain_size = max_domain_size;
        output_.runtime_seconds = std::chrono::duration<double>(Clock::now() - start_).count();
        return output_;
    }

    InventorySearchOutput runSerial() {
        dfs(0, 0, 0, 0, 0.0);
        output_.complete = !timed_out_;
        output_.runtime_seconds = std::chrono::duration<double>(Clock::now() - start_).count();
        return output_;
    }

private:
    const Instance& instance_;
    double lambda_;
    double time_limit_seconds_;
    Clock::time_point start_;
    std::vector<int> order_;
    std::vector<std::vector<int>> domains_;
    std::vector<int> y_;
    std::vector<int> q_;
    std::vector<bool> assigned_;
    std::vector<double> r_lo_;
    std::vector<double> r_hi_;
    std::vector<double> min_penalty_;
    std::vector<double> suffix_min_penalty_;
    std::vector<int> min_pickup_;
    std::vector<int> max_net_q_;
    std::vector<int> suffix_min_pickup_;
    std::vector<int> suffix_max_net_q_;
    std::vector<double> tsp_lb_;
    int max_total_pickup_ = 0;
    int net_abs_limit_ = 0;
    int net_stride_ = 1;
    std::vector<std::vector<double>> suffix_feasible_penalty_;
    std::vector<std::vector<double>> suffix_feasible_max_ratio_;
    InventorySearchOutput output_;
    bool timed_out_ = false;

    bool shouldStop() {
        if (timed_out_) return true;
        if ((output_.nodes & 0x3fff) == 0 && deadlineReached(start_, time_limit_seconds_)) {
            timed_out_ = true;
            return true;
        }
        return false;
    }

    int flatIndex(int pickup, int net_index) const {
        return pickup * net_stride_ + net_index;
    }

    void buildSuffixFeasiblePenaltyTables() {
        for (int i = 1; i <= instance_.V; ++i) {
            int local_abs = 0;
            for (int val : domains_[i]) {
                local_abs = std::max(local_abs, std::abs(instance_.initial[i] - val));
            }
            net_abs_limit_ += local_abs;
        }
        net_stride_ = 2 * net_abs_limit_ + 1;
        const int table_size = (max_total_pickup_ + 1) * net_stride_;
        const double inf = std::numeric_limits<double>::infinity();
        const double neg_inf = -std::numeric_limits<double>::infinity();
        suffix_feasible_penalty_.assign(order_.size() + 1,
                                        std::vector<double>(table_size, inf));
        suffix_feasible_max_ratio_.assign(order_.size() + 1,
                                          std::vector<double>(table_size, neg_inf));

        auto storeBest = [&](int depth, const std::vector<double>& penalty_exact,
                             const std::vector<double>& ratio_exact) {
            std::vector<double> cap_min = penalty_exact;
            std::vector<double> cap_max = ratio_exact;
            for (int p = 1; p <= max_total_pickup_; ++p) {
                for (int ni = 0; ni < net_stride_; ++ni) {
                    cap_min[flatIndex(p, ni)] = std::min(cap_min[flatIndex(p, ni)],
                                                         cap_min[flatIndex(p - 1, ni)]);
                    cap_max[flatIndex(p, ni)] = std::max(cap_max[flatIndex(p, ni)],
                                                         cap_max[flatIndex(p - 1, ni)]);
                }
            }
            for (int p = 0; p <= max_total_pickup_; ++p) {
                double running = inf;
                double running_max = neg_inf;
                for (int ni = net_stride_ - 1; ni >= 0; --ni) {
                    running = std::min(running, cap_min[flatIndex(p, ni)]);
                    running_max = std::max(running_max, cap_max[flatIndex(p, ni)]);
                    suffix_feasible_penalty_[depth][flatIndex(p, ni)] = running;
                    suffix_feasible_max_ratio_[depth][flatIndex(p, ni)] = running_max;
                }
            }
        };

        std::vector<double> next_exact(table_size, inf);
        std::vector<double> next_ratio_exact(table_size, neg_inf);
        next_exact[flatIndex(0, net_abs_limit_)] = 0.0;
        next_ratio_exact[flatIndex(0, net_abs_limit_)] = 0.0;
        storeBest(static_cast<int>(order_.size()), next_exact, next_ratio_exact);

        for (int d = static_cast<int>(order_.size()) - 1; d >= 0; --d) {
            std::vector<double> cur_exact(table_size, inf);
            std::vector<double> cur_ratio_exact(table_size, neg_inf);
            const int station = order_[d];
            for (int p = 0; p <= max_total_pickup_; ++p) {
                for (int ni = 0; ni < net_stride_; ++ni) {
                    const double base = next_exact[flatIndex(p, ni)];
                    const double ratio_base = next_ratio_exact[flatIndex(p, ni)];
                    if (!std::isfinite(base) && !std::isfinite(ratio_base)) continue;
                    const int net = ni - net_abs_limit_;
                    for (int val : domains_[station]) {
                        const int q = instance_.initial[station] - val;
                        const int np = p + std::max(0, q);
                        if (np > max_total_pickup_) continue;
                        const int nnet = net + q;
                        if (nnet < -net_abs_limit_ || nnet > net_abs_limit_) continue;
                        const double ratio = static_cast<double>(val) / instance_.target[station];
                        const int idx = flatIndex(np, nnet + net_abs_limit_);
                        if (std::isfinite(base)) {
                            const double penalty = instance_.weights[station] * std::fabs(ratio - 1.0);
                            cur_exact[idx] = std::min(cur_exact[idx], base + penalty);
                        }
                        if (std::isfinite(ratio_base)) {
                            cur_ratio_exact[idx] = std::max(cur_ratio_exact[idx], ratio_base + ratio);
                        }
                    }
                }
            }
            next_exact = std::move(cur_exact);
            next_ratio_exact = std::move(cur_ratio_exact);
            storeBest(d, next_exact, next_ratio_exact);
        }
    }

    double suffixFeasiblePenalty(int depth, int pickup_cap, int required_net) const {
        if (pickup_cap < 0) return std::numeric_limits<double>::infinity();
        pickup_cap = std::min(pickup_cap, max_total_pickup_);
        if (required_net > net_abs_limit_) return std::numeric_limits<double>::infinity();
        if (required_net < -net_abs_limit_) required_net = -net_abs_limit_;
        return suffix_feasible_penalty_[depth][flatIndex(pickup_cap, required_net + net_abs_limit_)];
    }

    double suffixFeasibleMaxRatio(int depth, int pickup_cap, int required_net) const {
        if (pickup_cap < 0) return -std::numeric_limits<double>::infinity();
        pickup_cap = std::min(pickup_cap, max_total_pickup_);
        if (required_net > net_abs_limit_) return -std::numeric_limits<double>::infinity();
        if (required_net < -net_abs_limit_) required_net = -net_abs_limit_;
        return suffix_feasible_max_ratio_[depth][flatIndex(pickup_cap, required_net + net_abs_limit_)];
    }

    double partialLowerBound(int depth,
                             double penalty_prefix,
                             double penalty_lower_bound,
                             double feasible_s_max) const {
        double h_lb = 0.0;
        std::vector<double> lo(instance_.V + 1, 0.0), hi(instance_.V + 1, 0.0);
        const double p_limit = (lambda_ > 0.0)
            ? output_.best_parts.objective / lambda_
            : std::numeric_limits<double>::infinity();
        const double remaining_p_budget = p_limit - penalty_prefix;
        for (int i = 1; i <= instance_.V; ++i) {
            if (assigned_[i]) {
                lo[i] = hi[i] = static_cast<double>(y_[i]) / instance_.target[i];
            } else {
                if (domains_[i].empty()) return std::numeric_limits<double>::infinity();
                lo[i] = r_lo_[i];
                hi[i] = r_hi_[i];
                if (std::isfinite(remaining_p_budget)) {
                    const double other_min = suffix_min_penalty_[depth] - min_penalty_[i];
                    const double station_budget = remaining_p_budget - other_min;
                    if (station_budget < min_penalty_[i] - 1e-12) {
                        return std::numeric_limits<double>::infinity();
                    }
                    if (instance_.weights[i] > 1e-12) {
                        const double radius = station_budget / instance_.weights[i];
                        lo[i] = std::max(lo[i], 1.0 - radius);
                        hi[i] = std::min(hi[i], 1.0 + radius);
                        if (lo[i] > hi[i] + 1e-12) {
                            return std::numeric_limits<double>::infinity();
                        }
                    }
                }
            }
        }
        for (int i = 1; i <= instance_.V; ++i) {
            for (int j = i + 1; j <= instance_.V; ++j) {
                double gap = 0.0;
                if (hi[i] < lo[j]) gap = lo[j] - hi[i];
                else if (hi[j] < lo[i]) gap = lo[i] - hi[j];
                h_lb += gap;
                if (gap > 0.0) {
                    h_lb = std::max(h_lb, static_cast<double>(instance_.V - 1) * gap);
                }
            }
        }
        std::vector<double> lo_order;
        std::vector<double> hi_order;
        lo_order.reserve(instance_.V);
        hi_order.reserve(instance_.V);
        for (int i = 1; i <= instance_.V; ++i) {
            lo_order.push_back(lo[i]);
            hi_order.push_back(hi[i]);
        }
        std::sort(lo_order.begin(), lo_order.end());
        std::sort(hi_order.begin(), hi_order.end());
        double order_h_lb = 0.0;
        for (int k = 1; k <= instance_.V; ++k) {
            const double coef = static_cast<double>(2 * k - instance_.V - 1);
            if (coef > 0.0) {
                order_h_lb += coef * lo_order[k - 1];
            } else if (coef < 0.0) {
                order_h_lb += coef * hi_order[k - 1];
            }
        }
        h_lb = std::max(h_lb, std::max(0.0, order_h_lb));
        const double g_lb = (feasible_s_max > 0.0)
            ? h_lb / (static_cast<double>(instance_.V) * feasible_s_max) : 0.0;
        return g_lb + lambda_ * penalty_lower_bound;
    }

    int pickupOnMask(int mask) const {
        int pickup = 0;
        while (mask) {
            const int bit = mask & -mask;
            const int station = __builtin_ctz(static_cast<unsigned int>(bit)) + 1;
            pickup += std::max(0, q_[station]);
            mask -= bit;
        }
        return pickup;
    }

    bool routeDurationRelaxationFeasible(int support_mask) const {
        if (support_mask == 0) return true;
        const double cunit = instance_.pickup_time + instance_.drop_time;
        if (instance_.M == 1) {
            return tsp_lb_[support_mask] + cunit * pickupOnMask(support_mask)
                <= instance_.total_time_limit + 1e-9;
        }
        if (instance_.M != 2) return true;
        for (int sub = support_mask; ; sub = (sub - 1) & support_mask) {
            const int other = support_mask ^ sub;
            const double t0 = tsp_lb_[sub] + cunit * pickupOnMask(sub);
            const double t1 = tsp_lb_[other] + cunit * pickupOnMask(other);
            if (t0 <= instance_.total_time_limit + 1e-9 &&
                t1 <= instance_.total_time_limit + 1e-9) {
                return true;
            }
            if (sub == 0) break;
        }
        return false;
    }

    double assignedRatioSum() const {
        double sum = 0.0;
        for (int i = 1; i <= instance_.V; ++i) {
            if (assigned_[i]) sum += static_cast<double>(y_[i]) / instance_.target[i];
        }
        return sum;
    }

    void searchRootValue(int val) {
        ++output_.nodes;
        if (order_.empty() || shouldStop()) return;
        const int station = order_.front();
        assigned_[station] = true;
        y_[station] = val;
        q_[station] = instance_.initial[station] - val;
        const int pickup_sum = std::max(0, q_[station]);
        const int drop_sum = std::max(0, -q_[station]);
        const int support_mask = (q_[station] == 0) ? 0 : (1 << (station - 1));
        const double ratio = static_cast<double>(val) / instance_.target[station];
        const double penalty_prefix = instance_.weights[station] * std::fabs(ratio - 1.0);
        if ((pickup_sum - drop_sum) + suffix_max_net_q_[1] >= 0 &&
            pickup_sum + suffix_min_pickup_[1] <= max_total_pickup_) {
            const double child_penalty = suffixFeasiblePenalty(
                1, max_total_pickup_ - pickup_sum, drop_sum - pickup_sum);
            if (std::isfinite(child_penalty) &&
                lambda_ * (penalty_prefix + child_penalty) <
                    output_.best_parts.objective - 1e-12) {
                dfs(1, pickup_sum, drop_sum, support_mask, penalty_prefix);
            }
        }
        q_[station] = 0;
        assigned_[station] = false;
    }

    void dfs(int depth, int pickup_sum, int drop_sum, int support_mask, double penalty_prefix) {
        ++output_.nodes;
        if (shouldStop()) return;
        const int current_net = pickup_sum - drop_sum;
        if (current_net + suffix_max_net_q_[depth] < 0) return;
        if (pickup_sum + suffix_min_pickup_[depth] > max_total_pickup_) return;
        const double feasible_penalty = suffixFeasiblePenalty(
            depth, max_total_pickup_ - pickup_sum, drop_sum - pickup_sum);
        if (!std::isfinite(feasible_penalty)) return;
        const double feasible_tail_ratio = suffixFeasibleMaxRatio(
            depth, max_total_pickup_ - pickup_sum, drop_sum - pickup_sum);
        if (!std::isfinite(feasible_tail_ratio)) return;
        const double penalty_lb = penalty_prefix + feasible_penalty;
        if (lambda_ * penalty_lb >= output_.best_parts.objective - 1e-12) return;
        const double feasible_s_max = assignedRatioSum() + feasible_tail_ratio;
        if (partialLowerBound(depth, penalty_prefix, penalty_lb, feasible_s_max) >=
            output_.best_parts.objective - 1e-12) {
            return;
        }
        if (support_mask != 0 && !routeDurationRelaxationFeasible(support_mask)) {
            return;
        }

        if (depth == static_cast<int>(order_.size())) {
            if (pickup_sum < drop_sum) return;
            std::vector<int> final_y = instance_.initial;
            for (int i = 1; i <= instance_.V; ++i) final_y[i] = y_[i];
            ObjectiveParts parts = computeObjectiveParts(instance_, final_y, lambda_);
            if (parts.objective >= output_.best_parts.objective - 1e-12) return;
            std::vector<RoutePlan> routes;
            if (!buildFeasiblePartitionRoutes(instance_, q_, routes, output_.route_checks)) return;
            output_.best_parts = parts;
            output_.best_y = std::move(final_y);
            output_.best_routes = std::move(routes);
            output_.has_solution = true;
            return;
        }

        const int station = order_[depth];
        assigned_[station] = true;
        for (int val : domains_[station]) {
            y_[station] = val;
            q_[station] = instance_.initial[station] - val;
            const int np = pickup_sum + std::max(0, q_[station]);
            const int nd = drop_sum + std::max(0, -q_[station]);
            const int nsupport = (q_[station] == 0)
                ? support_mask : (support_mask | (1 << (station - 1)));
            const double ratio = static_cast<double>(val) / instance_.target[station];
            const double next_penalty = penalty_prefix
                + instance_.weights[station] * std::fabs(ratio - 1.0);
            if (lambda_ * (next_penalty + suffix_min_penalty_[depth + 1]) >=
                output_.best_parts.objective - 1e-12) {
                continue;
            }
            if ((np - nd) + suffix_max_net_q_[depth + 1] < 0) continue;
            if (np + suffix_min_pickup_[depth + 1] > max_total_pickup_) continue;
            const double child_penalty = suffixFeasiblePenalty(
                depth + 1, max_total_pickup_ - np, nd - np);
            if (!std::isfinite(child_penalty)) continue;
            if (lambda_ * (next_penalty + child_penalty) >=
                output_.best_parts.objective - 1e-12) {
                continue;
            }
            if (np <= max_total_pickup_) dfs(depth + 1, np, nd, nsupport, next_penalty);
            if (timed_out_) break;
        }
        q_[station] = 0;
        assigned_[station] = false;
    }
};

MasterOutput solveMasterExactly(const Instance& instance,
                                const std::vector<std::vector<Column>>& columns_by_vehicle,
                                double lambda,
                                double time_limit_seconds,
                                Clock::time_point start) {
    MasterOutput out;
    const int full_mask = (1 << instance.V) - 1;
    std::vector<MasterState> states;
    MasterState root;
    root.y = instance.initial;
    root.selected.assign(instance.M, -1);
    states.push_back(root);

    for (int k = 0; k < instance.M; ++k) {
        std::vector<std::vector<int>> buckets(1 << instance.V);
        for (int idx = 0; idx < static_cast<int>(columns_by_vehicle[k].size()); ++idx) {
            buckets[columns_by_vehicle[k][idx].mask].push_back(idx);
        }

        std::unordered_map<std::string, MasterState> next;
        next.reserve(states.size() * 2);
        for (const MasterState& state : states) {
            if ((out.states_processed & 0xffff) == 0 && deadlineReached(start, time_limit_seconds)) {
                out.complete = false;
                return out;
            }
            MasterState skip = state;
            skip.selected[k] = -1;
            next.emplace(stateKey(skip.mask, skip.y, instance.V), std::move(skip));

            const int complement = full_mask ^ state.mask;
            for (int sub = complement; sub > 0; sub = (sub - 1) & complement) {
                const auto& bucket = buckets[sub];
                if (bucket.empty()) continue;
                for (int col_idx : bucket) {
                    const Column& col = columns_by_vehicle[k][col_idx];
                    MasterState ns = state;
                    ns.mask |= col.mask;
                    ns.selected[k] = col_idx;
                    for (int i = 1; i <= instance.V; ++i) ns.y[i] -= col.q[i];
                    std::string key = stateKey(ns.mask, ns.y, instance.V);
                    if (next.find(key) == next.end()) next.emplace(std::move(key), std::move(ns));
                    ++out.states_processed;
                }
            }
        }
        states.clear();
        states.reserve(next.size());
        for (auto& kv : next) states.push_back(std::move(kv.second));
    }

    out.best_parts.objective = std::numeric_limits<double>::infinity();
    for (const MasterState& state : states) {
        ObjectiveParts parts = computeObjectiveParts(instance, state.y, lambda);
        if (parts.objective < out.best_parts.objective - 1e-12) {
            out.best_parts = parts;
            out.best_state = state;
        }
    }
    return out;
}

std::vector<RoutePlan> buildRoutes(const Instance& instance,
                                   const std::vector<std::vector<Column>>& columns_by_vehicle,
                                   const MasterState& state) {
    std::vector<RoutePlan> routes;
    routes.reserve(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        RoutePlan route;
        route.vehicle = k;
        route.nodes.push_back(0);
        const int col_idx = (k < static_cast<int>(state.selected.size())) ? state.selected[k] : -1;
        if (col_idx >= 0) {
            const Column& col = columns_by_vehicle[k][col_idx];
            for (int station : col.path) {
                route.nodes.push_back(station);
                StopOperation op;
                op.station = station;
                if (col.q[station] > 0) op.pickup = col.q[station];
                if (col.q[station] < 0) op.drop = -col.q[station];
                route.operations.push_back(op);
            }
        }
        route.nodes.push_back(0);
        routes.push_back(std::move(route));
    }
    return routes;
}

} // namespace

SolveResult solveTailoredExact(const Instance& instance, const SolveOptions& options) {
    const auto start = Clock::now();
    Logger log(options.log_path);
    SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "tailored";
    result.status = "running";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Tailored exact mode uses exhaustive feasible route-load column enumeration and exact station-disjoint master search.");

    long long inventory_probe_nodes = 0;
    long long inventory_probe_checks = 0;
    const int max_q = instance.Q.empty() ? 0 : *std::max_element(instance.Q.begin(), instance.Q.end());

    const bool explicit_inventory_probe = options.inventory_probe_seconds > 0.0 &&
        instance.V <= options.inventory_probe_max_v && instance.M <= 2 && max_q <= 31;
    const bool enumeration_volume_guard = (instance.V >= 8 || instance.M >= 2);

    if (explicit_inventory_probe && enumeration_volume_guard) {
        SolveOptions fallback_options = options;
        fallback_options.method = "cplex";
        fallback_options.plain_baseline = false;
        if (!fallback_options.log_path.empty()) fallback_options.log_path += ".cplex.log";
        SolveResult fallback = solveCplexBaseline(instance, fallback_options);
        fallback.method = "tailored";

        const SolveResult* incumbent = fallback.verification.feasible ? &fallback : nullptr;
        InventoryBranchSearch inv_search(instance, options.lambda,
                                         options.inventory_probe_seconds,
                                         Clock::now(), incumbent);
        InventorySearchOutput inv = inv_search.run(options.threads);
        std::ostringstream inv_note;
        inv_note << "Inventory branch-search proof after incumbent complete=" << (inv.complete ? "true" : "false")
                 << ", nodes=" << inv.nodes
                 << ", route_checks=" << inv.route_checks
                 << ", domain_values=" << inv.domain_values
                 << ", max_domain_size=" << inv.max_domain_size
                 << ", runtime=" << inv.runtime_seconds
                 << ", incumbent_source=" << fallback.status;
        log.line(inv_note.str());

        if (inv.complete && inv.has_solution) {
            result.routes = inv.best_routes;
            result.final_inventory = inv.best_y;
            result.G = inv.best_parts.G;
            result.P = inv.best_parts.P;
            result.objective = inv.best_parts.objective;
            result.lower_bound = result.objective;
            result.upper_bound = result.objective;
            result.gap = 0.0;
            result.nodes = inv.nodes;
            result.pricing_calls = inv.route_checks;
            result.status = "optimal";
            result.certificate = "tailored inventory-route search exhausted all admissible final-inventory vectors using exact route-load feasibility DP; compact solve supplied only the incumbent";
            result.verification = verifySolution(instance, result.routes, options.lambda);
            if (!result.verification.feasible) {
                result.status = "verification_failed";
                result.certificate = "inventory branch-search candidate failed independent verifier";
            }
            result.notes.push_back(inv_note.str());
            result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
            return result;
        }

        const double total_runtime = std::chrono::duration<double>(Clock::now() - start).count();
        fallback.method = "tailored";
        fallback.runtime_seconds = total_runtime;
        fallback.nodes += inv.nodes;
        fallback.pricing_calls += inv.route_checks;
        fallback.notes.insert(fallback.notes.begin(), inv_note.str());
        fallback.notes.insert(fallback.notes.begin(),
            "Inventory-route proof did not exhaust; portfolio returned strengthened compact exact fallback certificate when available.");
        if (fallback.status == "optimal") {
            fallback.certificate = "Tailored portfolio certificate via strengthened compact exact fallback: "
                + fallback.certificate;
        }
        return fallback;
    }

    if (options.inventory_probe_seconds != 0.0 &&
        instance.V <= options.inventory_probe_max_v && instance.M <= 2 && max_q <= 31) {
        const double inventory_limit = (options.inventory_probe_seconds > 0.0)
            ? options.inventory_probe_seconds
            : std::min(2.0, std::max(0.1, options.solve_time_limit * 0.05));
        InventoryBranchSearch inv_search(instance, options.lambda, inventory_limit, Clock::now());
        InventorySearchOutput inv = inv_search.run(options.threads);
        inventory_probe_nodes = inv.nodes;
        inventory_probe_checks = inv.route_checks;
        std::ostringstream inv_note;
        inv_note << "Inventory branch-search probe complete=" << (inv.complete ? "true" : "false")
                 << ", nodes=" << inv.nodes
                 << ", route_checks=" << inv.route_checks
                 << ", domain_values=" << inv.domain_values
                 << ", max_domain_size=" << inv.max_domain_size
                 << ", runtime=" << inv.runtime_seconds;
        result.notes.push_back(inv_note.str());
        log.line(inv_note.str());
        if (inv.complete && inv.has_solution) {
            result.routes = inv.best_routes;
            result.final_inventory = inv.best_y;
            result.G = inv.best_parts.G;
            result.P = inv.best_parts.P;
            result.objective = inv.best_parts.objective;
            result.lower_bound = result.objective;
            result.upper_bound = result.objective;
            result.gap = 0.0;
            result.nodes = inv.nodes;
            result.pricing_calls = inv.route_checks;
            result.status = "optimal";
            result.certificate = "all admissible station final-inventory vectors were fathomed by valid objective lower bounds or checked with exact route-load feasibility DP";
            result.verification = verifySolution(instance, result.routes, options.lambda);
            if (!result.verification.feasible) {
                result.status = "verification_failed";
                result.certificate = "inventory branch-search candidate failed independent verifier";
            }
            result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
            return result;
        }
    }

    if (enumeration_volume_guard) {
        SolveOptions fallback_options = options;
        fallback_options.method = "cplex";
        fallback_options.plain_baseline = false;
        if (!fallback_options.log_path.empty()) fallback_options.log_path += ".cplex.log";
        SolveResult fallback = solveCplexBaseline(instance, fallback_options);
        fallback.method = "tailored";
        const double total_runtime = std::chrono::duration<double>(Clock::now() - start).count();
        fallback.runtime_seconds = total_runtime;
        fallback.nodes += inventory_probe_nodes;
        fallback.pricing_calls += inventory_probe_checks;
        for (auto it = result.notes.rbegin(); it != result.notes.rend(); ++it) {
            fallback.notes.insert(fallback.notes.begin(), *it);
        }
        fallback.notes.insert(fallback.notes.begin(),
            "Portfolio selected strengthened compact exact fallback before full column materialization because the adaptive V/M guard predicts excessive route-load columns.");
        fallback.notes.push_back("The route-load enumerator remains available for smaller guarded cases and reports non-certified time_limit if interrupted.");
        if (fallback.status == "optimal") {
            fallback.certificate = "Tailored portfolio certificate via strengthened compact exact fallback: "
                + fallback.certificate;
        }
        return fallback;
    }

    if (instance.V > 12) {
        result.status = "unsupported";
        result.certificate = "full enumeration mode is currently guarded to V<=12";
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        return result;
    }

    std::atomic<bool> stop(false);
    std::vector<std::vector<Column>> columns_by_vehicle(instance.M);
    long long dfs_states = 0;
    bool enum_timed_out = false;
    const int worker_threads = std::max(1, options.threads);
    for (int k = 0; k < instance.M; ++k) {
        if (deadlineReached(start, options.solve_time_limit)) {
            enum_timed_out = true;
            break;
        }
        VehicleEnumerator enumerator(instance, k, options.solve_time_limit, start, stop);
        EnumOutput out = enumerator.enumerate(worker_threads);
        columns_by_vehicle[k] = std::move(out.columns);
        result.columns += static_cast<long long>(columns_by_vehicle[k].size());
        dfs_states += out.stats.dfs_states;
        enum_timed_out = enum_timed_out || out.stats.timed_out;
        std::ostringstream msg;
        msg << "vehicle " << k << " columns=" << columns_by_vehicle[k].size()
            << " dfs_states=" << out.stats.dfs_states
            << " generated_before_dedup=" << out.stats.generated_columns;
        log.line(msg.str());
    }

    if (enum_timed_out || stop.load()) {
        result.status = "time_limit";
        result.certificate = "not certified; route-load enumeration did not complete";
        result.nodes = dfs_states;
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        return result;
    }

    MasterOutput master = solveMasterExactly(instance, columns_by_vehicle, options.lambda,
                                             options.solve_time_limit, start);
    result.nodes = dfs_states + master.states_processed;
    if (!master.complete) {
        result.status = "time_limit";
        result.certificate = "not certified; exact master search did not complete";
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        return result;
    }

    result.routes = buildRoutes(instance, columns_by_vehicle, master.best_state);
    result.final_inventory = master.best_state.y;
    result.G = master.best_parts.G;
    result.P = master.best_parts.P;
    result.objective = master.best_parts.objective;
    result.lower_bound = result.objective;
    result.upper_bound = result.objective;
    result.gap = 0.0;
    result.status = "optimal";
    result.certificate = "all feasible route-load columns were enumerated and the induced integer master was searched exhaustively";
    result.verification = verifySolution(instance, result.routes, options.lambda);
    if (!result.verification.feasible) {
        result.status = "verification_failed";
        result.certificate = "candidate failed independent verifier";
    }
    result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();

    std::ostringstream done;
    done << "tailored status=" << result.status
         << " objective=" << result.objective
         << " G=" << result.G
         << " P=" << result.P
         << " runtime=" << result.runtime_seconds
         << " columns=" << result.columns
         << " master_transitions=" << master.states_processed;
    log.line(done.str());
    return result;
}

} // namespace ebrp
