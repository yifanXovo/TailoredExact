#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <iostream>
#include <limits>
#include <numeric>
#include <unordered_map>
#include <utility>
#include <vector>
#include <memory>

#include "hga_tgbc/GreedyMethods.h"
#include "hga_tgbc/GreedyExtensions.h"

using std::max;
using std::min;
using std::size_t;
using std::vector;

static double Load_time_unit = 60.0;
static double Unload_time_unit = 60.0;
static const double Greedy_lambda_default = 0.05;
static const double Greedy_scaling_default = 1.0;
static double greedy_lambda = Greedy_lambda_default;
static double greedy_scaling = Greedy_scaling_default;
static bool greedy_route_stats_enabled = false;

void set_greedy_time_units(double load_unit, double unload_unit) {
    Load_time_unit = load_unit;
    Unload_time_unit = unload_unit;
}

void set_greedy_objective_params(double lambda, double scaling) {
    if (lambda >= 0.0) greedy_lambda = lambda;
    if (scaling > 0.0) greedy_scaling = scaling;
}

void set_greedy_route_stats(bool enabled) {
    greedy_route_stats_enabled = enabled;
}

double get_greedy_objective_lambda() {
    return greedy_lambda;
}

double get_greedy_objective_scaling() {
    return greedy_scaling;
}

namespace {

static constexpr double EPS_LD = 1e-18;
static constexpr double EPS = 1e-12;
static constexpr int INF_INT = std::numeric_limits<int>::max() / 4;

struct Fenwick {
    int n = 0;
    vector<double> bit;

    Fenwick() = default;
    explicit Fenwick(int n_) { init(n_); }

    void init(int n_) {
        n = max(1, n_);
        bit.assign(n + 1, 0.0);
    }

    void add(int idx0, double delta) {
        for (int idx = idx0 + 1; idx <= n; idx += idx & -idx) bit[idx] += delta;
    }

    double sumPrefix(int idx0) const {
        if (idx0 < 0) return 0.0;
        idx0 = min(idx0, n - 1);
        double ans = 0.0;
        for (int idx = idx0 + 1; idx > 0; idx -= idx & -idx) ans += bit[idx];
        return ans;
    }

    double sumAll() const {
        return sumPrefix(n - 1);
    }
};

struct RangeAddMinMaxTree {
    struct Node {
        int mn = 0;
        int mx = 0;
        int lazy = 0;
    };

    int n = 0;
    vector<Node> tr;

    RangeAddMinMaxTree() = default;
    explicit RangeAddMinMaxTree(int n_) { init(n_); }

    void init(int n_) {
        n = max(1, n_);
        tr.assign(4 * n + 4, Node{});
    }

    void buildFromArray(int p, int l, int r, const vector<int>& a) {
        tr[p].lazy = 0;
        if (l == r) {
            int v = (l < (int)a.size()) ? a[l] : 0;
            tr[p].mn = v;
            tr[p].mx = v;
            return;
        }
        int m = (l + r) >> 1;
        buildFromArray(p << 1, l, m, a);
        buildFromArray(p << 1 | 1, m + 1, r, a);
        pull(p);
    }

    void buildFromArray(const vector<int>& a) {
        init((int)a.size());
        if (!a.empty()) buildFromArray(1, 0, n - 1, a);
    }

    void push(int p) {
        int lz = tr[p].lazy;
        if (lz == 0) return;
        for (int c : {p << 1, p << 1 | 1}) {
            tr[c].mn += lz;
            tr[c].mx += lz;
            tr[c].lazy += lz;
        }
        tr[p].lazy = 0;
    }

    void pull(int p) {
        tr[p].mn = min(tr[p << 1].mn, tr[p << 1 | 1].mn);
        tr[p].mx = max(tr[p << 1].mx, tr[p << 1 | 1].mx);
    }

    void rangeAdd(int p, int l, int r, int ql, int qr, int v) {
        if (ql > r || qr < l || ql > qr) return;
        if (ql <= l && r <= qr) {
            tr[p].mn += v;
            tr[p].mx += v;
            tr[p].lazy += v;
            return;
        }
        push(p);
        int m = (l + r) >> 1;
        rangeAdd(p << 1, l, m, ql, qr, v);
        rangeAdd(p << 1 | 1, m + 1, r, ql, qr, v);
        pull(p);
    }

    void rangeAdd(int ql, int qr, int v) {
        if (ql > qr || n <= 0) return;
        rangeAdd(1, 0, n - 1, ql, qr, v);
    }

    std::pair<int, int> queryMinMax(int p, int l, int r, int ql, int qr) const {
        if (ql > r || qr < l || ql > qr) {
            return {INF_INT, -INF_INT};
        }
        if (ql <= l && r <= qr) return {tr[p].mn, tr[p].mx};
        int lz = tr[p].lazy;
        int m = (l + r) >> 1;
        auto L = queryMinMax(p << 1, l, m, ql, qr);
        auto R = queryMinMax(p << 1 | 1, m + 1, r, ql, qr);
        return {min(L.first, R.first) + lz, max(L.second, R.second) + lz};
    }

    std::pair<int, int> queryMinMax(int ql, int qr) const {
        if (n <= 0 || ql > qr) return {0, 0};
        return queryMinMax(1, 0, n - 1, ql, qr);
    }
};


struct RatioUniverse {
    vector<double> coords;
    vector<vector<int>> ratio_index;
    const vector<int>* targets_src = nullptr;
    int targets_offset = 0;
    int station_count = 0;

    static bool almostEqual(double a, double b) {
        return fabs(a - b) <= EPS_LD;
    }

    int targetAt(int i) const {
        if (!targets_src) return 0;
        int idx = i + targets_offset;
        if (idx < 0 || idx >= (int)targets_src->size()) return 0;
        return (*targets_src)[idx];
    }

    static int valueAt(const vector<int>& src, int off, int i) {
        int idx = i + off;
        if (idx < 0 || idx >= (int)src.size()) return 0;
        return src[idx];
    }

    void build(const vector<int>& C_src, int C_off, const vector<int>& T_src, int T_off, int V) {
        targets_src = &T_src;
        targets_offset = T_off;
        station_count = V;
        coords.clear();
        ratio_index.assign(V, {});
        for (int i = 0; i < V; ++i) {
            int cap = valueAt(C_src, C_off, i);
            int target = valueAt(T_src, T_off, i);
            ratio_index[i].assign(cap + 1, -1);
            if (target <= 0) {
                coords.push_back(0.0);
            } else {
                for (int f = 0; f <= cap; ++f) coords.push_back((double)f / (double)target);
            }
        }
        std::sort(coords.begin(), coords.end());
        coords.erase(std::unique(coords.begin(), coords.end(), [](double a, double b) {
            return almostEqual(a, b);
        }), coords.end());

        for (int i = 0; i < V; ++i) {
            int cap = valueAt(C_src, C_off, i);
            int target = valueAt(T_src, T_off, i);
            if (target <= 0) {
                int idx = (int)(std::lower_bound(coords.begin(), coords.end(), 0.0 - EPS_LD) - coords.begin());
                if (idx >= (int)coords.size()) idx = (int)coords.size() - 1;
                for (int f = 0; f <= cap; ++f) ratio_index[i][f] = idx;
            } else {
                for (int f = 0; f <= cap; ++f) {
                    double v = (double)f / (double)target;
                    int idx = (int)(std::lower_bound(coords.begin(), coords.end(), v - EPS_LD) - coords.begin());
                    if (idx >= (int)coords.size()) idx = (int)coords.size() - 1;
                    if (idx > 0 && fabs(coords[idx] - v) > fabs(coords[idx - 1] - v)) idx--;
                    ratio_index[i][f] = idx;
                }
            }
        }
    }
};

struct RatioTracker {
    const RatioUniverse* universe = nullptr;
    Fenwick bit_count;
    Fenwick bit_sum;
    vector<int> current_index;
    vector<double> current_ratio;
    int total_count = 0;
    double total_sum = 0.0;
    double ordered_pair_sum = 0.0;

    void bind(const RatioUniverse* u) {
        universe = u;
        int n = (u ? (int)u->coords.size() : 0);
        bit_count.init(n);
        bit_sum.init(n);
    }

    static double ratioValue(int final_inv, int target) {
        if (target <= 0) return 0.0;
        return (double)final_inv / (double)target;
    }

    double sumAbsByIndex(int idx, double val) const {
        double left_count = bit_count.sumPrefix(idx);
        double left_sum = bit_sum.sumPrefix(idx);
        double right_count = (double)total_count - left_count;
        double right_sum = total_sum - left_sum;
        return val * left_count - left_sum + right_sum - val * right_count;
    }

    void init(const vector<int>& F) {
        const auto& ratio_index = universe->ratio_index;
        const auto& coords = universe->coords;
        bit_count.init((int)coords.size());
        bit_sum.init((int)coords.size());
        int V = (int)F.size();
        current_index.assign(V, 0);
        current_ratio.assign(V, 0.0);
        total_count = 0;
        total_sum = 0.0;
        ordered_pair_sum = 0.0;
        for (int i = 0; i < V; ++i) {
            int idx = ratio_index[i][F[i]];
            double val = ratioValue(F[i], universe->targetAt(i));
            current_index[i] = idx;
            current_ratio[i] = val;
            bit_count.add(idx, 1.0);
            bit_sum.add(idx, val);
            ++total_count;
            total_sum += val;
        }
        for (int i = 0; i < V; ++i) ordered_pair_sum += sumAbsByIndex(current_index[i], current_ratio[i]);
    }

    struct EvalResult {
        double ordered_pair_sum_new = 0.0;
        double ratio_sum_new = 0.0;
        double gini_new = 0.0;
    };

    EvalResult evaluateChangeRaw(const int* stations, const int* new_finals, int k, double current_ratio_sum) const {
        const auto& ratio_index = universe->ratio_index;
        const auto& coords = universe->coords;
        double oldv[8], newv[8];
        int oldidx[8], newidx[8];
        for (int t = 0; t < k; ++t) {
            int s = stations[t];
            oldv[t] = current_ratio[s];
            oldidx[t] = current_index[s];
            newidx[t] = ratio_index[s][new_finals[t]];
            newv[t] = coords[newidx[t]];
        }

        double sum_h_old = 0.0;
        double internal_old = 0.0;
        for (int i = 0; i < k; ++i) {
            sum_h_old += sumAbsByIndex(oldidx[i], oldv[i]);
            for (int j = 0; j < k; ++j) internal_old += fabs(oldv[i] - oldv[j]);
        }
        double daa = ordered_pair_sum - 2.0 * sum_h_old + internal_old;

        double cross_new = 0.0;
        for (int i = 0; i < k; ++i) {
            double h_new = sumAbsByIndex(newidx[i], newv[i]);
            double sub = 0.0;
            for (int j = 0; j < k; ++j) sub += fabs(newv[i] - oldv[j]);
            cross_new += 2.0 * (h_new - sub);
        }

        double internal_new = 0.0;
        double ratio_sum_new = current_ratio_sum;
        for (int i = 0; i < k; ++i) {
            ratio_sum_new += (newv[i] - oldv[i]);
            for (int j = 0; j < k; ++j) internal_new += fabs(newv[i] - newv[j]);
        }

        double d_new = daa + cross_new + internal_new;
        double gini = 0.0;
        if (ratio_sum_new > EPS_LD) {
            gini = d_new / (2.0 * (double)total_count * ratio_sum_new);
        }
        return {d_new, ratio_sum_new, gini};
    }

    EvalResult evaluateChange(const vector<int>& stations, const vector<int>& new_finals, double current_ratio_sum) const {
        return evaluateChangeRaw(stations.data(), new_finals.data(), (int)stations.size(), current_ratio_sum);
    }

    EvalResult evaluateOneChange(int station, int new_final, double current_ratio_sum) const {
        const auto& ratio_index = universe->ratio_index;
        const auto& coords = universe->coords;
        int oldidx = current_index[station];
        int newidx = ratio_index[station][new_final];
        double oldv = current_ratio[station];
        double newv = coords[newidx];
        double h_old = sumAbsByIndex(oldidx, oldv);
        double h_new = sumAbsByIndex(newidx, newv);
        double d_new = ordered_pair_sum - 2.0 * h_old + 2.0 * h_new - 2.0 * fabs(newv - oldv);
        double ratio_sum_new = current_ratio_sum + (newv - oldv);
        double gini = 0.0;
        if (ratio_sum_new > EPS_LD) {
            gini = d_new / (2.0 * (double)total_count * ratio_sum_new);
        }
        return {d_new, ratio_sum_new, gini};
    }

    EvalResult evaluateTwoChange(int s1, int nf1, int s2, int nf2, double current_ratio_sum) const {
        const auto& ratio_index = universe->ratio_index;
        const auto& coords = universe->coords;
        int oldidx1 = current_index[s1];
        int oldidx2 = current_index[s2];
        int newidx1 = ratio_index[s1][nf1];
        int newidx2 = ratio_index[s2][nf2];
        double oldv1 = current_ratio[s1];
        double oldv2 = current_ratio[s2];
        double newv1 = coords[newidx1];
        double newv2 = coords[newidx2];
        double h_old1 = sumAbsByIndex(oldidx1, oldv1);
        double h_old2 = sumAbsByIndex(oldidx2, oldv2);
        double h_new1 = sumAbsByIndex(newidx1, newv1);
        double h_new2 = sumAbsByIndex(newidx2, newv2);
        double old_cross = fabs(oldv1 - oldv2);
        double new_cross = fabs(newv1 - newv2);
        double d_new = ordered_pair_sum
            - 2.0 * (h_old1 + h_old2)
            + 2.0 * old_cross
            + 2.0 * (h_new1 - fabs(newv1 - oldv1) - fabs(newv1 - oldv2))
            + 2.0 * (h_new2 - fabs(newv2 - oldv1) - fabs(newv2 - oldv2))
            + 2.0 * new_cross;
        double ratio_sum_new = current_ratio_sum + (newv1 - oldv1) + (newv2 - oldv2);
        double gini = 0.0;
        if (ratio_sum_new > EPS_LD) {
            gini = d_new / (2.0 * (double)total_count * ratio_sum_new);
        }
        return {d_new, ratio_sum_new, gini};
    }

    void applyChange(const vector<int>& stations, const vector<int>& new_finals, double ordered_pair_sum_new) {
        const auto& ratio_index = universe->ratio_index;
        const auto& coords = universe->coords;
        const int k = (int)stations.size();
        vector<int> newidx(k);
        vector<double> newv(k);
        for (int t = 0; t < k; ++t) {
            int s = stations[t];
            newidx[t] = ratio_index[s][new_finals[t]];
            newv[t] = coords[newidx[t]];
        }
        for (int t = 0; t < k; ++t) {
            int s = stations[t];
            bit_count.add(current_index[s], -1.0);
            bit_sum.add(current_index[s], -current_ratio[s]);
            --total_count;
            total_sum -= current_ratio[s];
        }
        for (int t = 0; t < k; ++t) {
            int s = stations[t];
            current_index[s] = newidx[t];
            current_ratio[s] = newv[t];
            bit_count.add(current_index[s], 1.0);
            bit_sum.add(current_index[s], current_ratio[s]);
            ++total_count;
            total_sum += current_ratio[s];
        }
        ordered_pair_sum = ordered_pair_sum_new;
    }
};

struct RouteInfo {
    vector<int> raw_route;
    vector<int> visits;
    double travel_time = 0.0;
    int capacity = 0;
    int pickup_budget = 0;
    int pickups_used = 0;
    vector<int> visit_oper;
    RangeAddMinMaxTree load_tree;
};

struct Move {
    bool valid = false;
    int route = -1;
    int source_pos = -1;
    int sink_pos = -1; // -1 means depot
    int amount = 0;
    int sign = 1;
    double objective = std::numeric_limits<double>::infinity();
    double ordered_pair_sum_new = 0.0;
    double ratio_sum_new = 0.0;
    double gini_new = 0.0;
    double penalty_sum_new = 0.0;
    int pickup_delta = 0;
};


static inline void rebuildRouteLoadTree(RouteInfo& rt) {
    int L = (int)rt.visits.size();
    if (L <= 0) {
        rt.load_tree.init(0);
        return;
    }
    vector<int> loads(L, 0);
    int load = 0;
    for (int p = 0; p < L; ++p) {
        load += rt.visit_oper[p];
        loads[p] = load;
    }
    rt.load_tree.buildFromArray(loads);
}

struct GreedyStaticData {
    RatioUniverse universe;
    vector<vector<double>> penalty_table;
    const vector<int>* C_src = nullptr;
    const vector<int>* T_src = nullptr;
    const vector<double>* W_src = nullptr;
    int C_off = 0;
    int T_off = 0;
    int W_off = 0;
    int V = 0;
    std::uint64_t c_sig = 0;
    std::uint64_t t_sig = 0;
    std::uint64_t w_sig = 0;
};

static std::uint64_t mix_u64(std::uint64_t h, std::uint64_t x) {
    x += 0x9e3779b97f4a7c15ULL;
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
    x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
    x ^= (x >> 31);
    return h ^ (x + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2));
}

static std::uint64_t signature_int_slice(const vector<int>& src, int off, int V) {
    std::uint64_t h = 1469598103934665603ULL;
    h = mix_u64(h, (std::uint64_t)(std::uint32_t)off);
    h = mix_u64(h, (std::uint64_t)(std::uint32_t)V);
    for (int i = 0; i < V; ++i) {
        int idx = i + off;
        int val = (idx >= 0 && idx < (int)src.size()) ? src[idx] : 0;
        h = mix_u64(h, (std::uint64_t)(std::int64_t)val);
    }
    return h;
}

static std::uint64_t signature_double_slice(const vector<double>& src, int off, int V) {
    std::uint64_t h = 1469598103934665603ULL;
    h = mix_u64(h, (std::uint64_t)(std::uint32_t)off);
    h = mix_u64(h, (std::uint64_t)(std::uint32_t)V);
    std::hash<double> hasher;
    for (int i = 0; i < V; ++i) {
        int idx = i + off;
        double val = (idx >= 0 && idx < (int)src.size()) ? src[idx] : 1.0;
        h = mix_u64(h, (std::uint64_t)hasher(val));
    }
    return h;
}

static std::shared_ptr<const GreedyStaticData> getGreedyStaticData(
    const vector<int>& C_src, int C_off,
    const vector<int>& T_src, int T_off,
    const vector<double>& W_src, int W_off,
    int V) {
    static std::shared_ptr<const GreedyStaticData> cache;
    const std::uint64_t c_sig = signature_int_slice(C_src, C_off, V);
    const std::uint64_t t_sig = signature_int_slice(T_src, T_off, V);
    const std::uint64_t w_sig = signature_double_slice(W_src, W_off, V);
    if (cache &&
        cache->C_src == &C_src && cache->C_off == C_off &&
        cache->T_src == &T_src && cache->T_off == T_off &&
        cache->W_src == &W_src && cache->W_off == W_off &&
        cache->V == V &&
        cache->c_sig == c_sig &&
        cache->t_sig == t_sig &&
        cache->w_sig == w_sig) {
        return cache;
    }
    auto data = std::make_shared<GreedyStaticData>();
    data->C_src = &C_src;
    data->T_src = &T_src;
    data->W_src = &W_src;
    data->C_off = C_off;
    data->T_off = T_off;
    data->W_off = W_off;
    data->V = V;
    data->c_sig = c_sig;
    data->t_sig = t_sig;
    data->w_sig = w_sig;
    data->universe.build(C_src, C_off, T_src, T_off, V);
    data->penalty_table.assign(V, {});
    for (int i = 0; i < V; ++i) {
        int cap = RatioUniverse::valueAt(C_src, C_off, i);
        int target = RatioUniverse::valueAt(T_src, T_off, i);
        int widx = i + W_off;
        double weight = (widx >= 0 && widx < (int)W_src.size()) ? W_src[widx] : 1.0;
        cap = max(0, cap);
        data->penalty_table[i].assign(cap + 1, 0.0);
        for (int f = 0; f <= cap; ++f) {
            double ratio = (target > 0) ? ((double)f / (double)target) : 0.0;
            data->penalty_table[i][f] = weight * std::fabs(ratio - 1.0);
        }
    }
    cache = data;
    return cache;
}

struct GreedyEngine {
    int V = 0;
    int M = 0;
    double total_time_limit = 0.0;
    double lambda = 0.0;
    double scaling = 1.0;
    int max_accept_moves = 500;

    const vector<int>* I_src = nullptr;
    const vector<int>* T_src = nullptr;
    const vector<int>* C_src = nullptr;
    const vector<double>* W_src = nullptr;
    const vector<double>* min_ratio_src = nullptr;
    int I_off = 0;
    int T_off = 0;
    int C_off = 0;
    int W_off = 0;
    int min_ratio_off = 0;
    std::shared_ptr<const GreedyStaticData> static_data;
    vector<int> desired_final;
    vector<RouteInfo> routes;
    vector<int> station_oper;
    vector<int> final_inv;
    RatioTracker tracker;
    double ratio_sum = 0.0;
    double ordered_pair_sum = 0.0;
    double penalty_sum = 0.0;
    double current_gini = 0.0;
    double current_objective = 0.0;

    static constexpr int AtomicLimit = 8;
    static constexpr int LocalLimit = 6;

    struct PreparedTemplate {
        bool valid = false;
        int route = -1;
        int source_pos = -1;
        int sink_pos = -1;
        int sign = 1;
        int end = -1;
        int cap_budget = 0;
        int source_station = -1;
        int sink_station = -1;
        int old_src_op = 0;
        int old_sink_op = 0;
        double old_src_penalty = 0.0;
        double old_sink_penalty = 0.0;
    };

    struct LocalCandidate;
    struct CrossCandidate;

    mutable std::uint64_t state_epoch = 1;
    mutable std::uint64_t atomic_cache_epoch = 0;
    mutable int atomic_cache_K = 0;
    mutable Move atomic_cache_best;
    mutable vector<vector<Move>> atomic_cache_top;
    mutable std::uint64_t local_cache_epoch = 0;
    mutable vector<vector<LocalCandidate>> local_cache_all;

    static int positivePart(int x) { return (x > 0 ? x : 0); }
    int IVal(int i) const { return (*I_src)[i + I_off]; }
    int TVal(int i) const { return (*T_src)[i + T_off]; }
    int CVal(int i) const { return (*C_src)[i + C_off]; }
    double WVal(int i) const { return (*W_src)[i + W_off]; }
    double MinRatioVal(int i) const { return (*min_ratio_src)[i + min_ratio_off]; }

    static double stationPenalty(int final_inv, int target, double weight) {
        double ratio = (target > 0) ? ((double)final_inv / (double)target) : 0.0;
        return weight * std::fabs(ratio - 1.0);
    }

    double penaltyValue(int station, int final_inv) const {
        return static_data->penalty_table[station][final_inv];
    }

    void buildPenaltyTable() {
        static_data = getGreedyStaticData(*C_src, C_off, *T_src, T_off, *W_src, W_off, V);
        tracker.bind(&static_data->universe);
    }

    double exactObjectiveFromFinal(const vector<int>& F) const {
        int V = (int)F.size();
        vector<double> r(V, 0.0);
        double S = 0.0, D = 0.0, P = 0.0;
        for (int i = 0; i < V; ++i) {
            int t = TVal(i);
            r[i] = (t > 0) ? ((double)F[i] / (double)t) : 0.0;
            S += r[i];
            P += stationPenalty(F[i], t, WVal(i));
        }
        for (int i = 0; i < V; ++i) {
            for (int j = 0; j < V; ++j) D += fabs(r[i] - r[j]);
        }
        double G = (S > EPS_LD) ? D / (2.0 * (double)V * S) : 0.0;
        return (double)(scaling * (G + lambda * P));
    }


    void invalidateSearchCaches() const {
        ++state_epoch;
        atomic_cache_epoch = 0;
        atomic_cache_K = 0;
        atomic_cache_top.clear();
        local_cache_epoch = 0;
        local_cache_all.clear();
    }

    void buildRoutes(const vector<vector<int>>& raw_routes, const vector<int>& Q, const vector<vector<double>>& dist) {
        routes.clear();
        routes.resize(M);
        const double denom = Load_time_unit + Unload_time_unit;
        for (int r = 0; r < M; ++r) {
            routes[r].raw_route = raw_routes[r];
            routes[r].capacity = Q[r];
            routes[r].visits.clear();
            routes[r].travel_time = 0.0;
            int prev = 0;
            for (size_t p = 0; p < raw_routes[r].size(); ++p) {
                int node = raw_routes[r][p];
                if (node == 0) continue;
                double candidate = routes[r].travel_time + dist[prev][node] + dist[node][0];
                if (candidate > total_time_limit + EPS) break;
                routes[r].travel_time += dist[prev][node];
                routes[r].visits.push_back(node - 1);
                prev = node;
            }
            if (!routes[r].visits.empty()) routes[r].travel_time += dist[prev][0];
            if (denom <= EPS) routes[r].pickup_budget = INF_INT;
            else routes[r].pickup_budget = max(0, (int)std::floor((total_time_limit - routes[r].travel_time + EPS) / denom));
            routes[r].pickups_used = 0;
            routes[r].visit_oper.assign(routes[r].visits.size(), 0);
            routes[r].load_tree.init((int)routes[r].visits.size());

            //std::cout << routes[r].visits.size() << std::endl;
        }
    }

    void rebuildObjectiveState() {
        tracker.init(final_inv);
        ordered_pair_sum = tracker.ordered_pair_sum;
        ratio_sum = 0.0;
        penalty_sum = 0.0;
        for (int i = 0; i < V; ++i) {
            ratio_sum += tracker.current_ratio[i];
            penalty_sum += penaltyValue(i, final_inv[i]);
        }
        current_gini = (ratio_sum > EPS_LD) ? ordered_pair_sum / (2.0 * (double)V * ratio_sum) : 0.0;
        current_objective = (double)(scaling * (current_gini + lambda * penalty_sum));
    }

    void initializeState() {
        station_oper.assign(V, 0);
        final_inv.assign(V, 0);
        desired_final.resize(V);
        for (int i = 0; i < V; ++i) {
            final_inv[i] = IVal(i);
            desired_final[i] = min(CVal(i), max(0, TVal(i)));
        }
        for (RouteInfo& rt : routes) {
            rt.pickups_used = 0;
            std::fill(rt.visit_oper.begin(), rt.visit_oper.end(), 0);
            rt.load_tree.init((int)rt.visits.size());
        }
        rebuildObjectiveState();
        invalidateSearchCaches();
    }

    void initializeFixedState(const vector<int>& fixed_oper, int fixed_off) {
        station_oper.assign(V, 0);
        for (int i = 0; i < V; ++i) station_oper[i] = fixed_oper[i + fixed_off];
        final_inv.assign(V, 0);
        desired_final.resize(V);
        for (int i = 0; i < V; ++i) {
            desired_final[i] = min(CVal(i), max(0, TVal(i)));
            final_inv[i] = IVal(i) - station_oper[i];
        }
        for (RouteInfo& rt : routes) {
            rt.pickups_used = 0;
            std::fill(rt.visit_oper.begin(), rt.visit_oper.end(), 0);
            rt.load_tree.init((int)rt.visits.size());
        }
        rebuildObjectiveState();
        invalidateSearchCaches();
    }

    int deltaPickupFromOpChange(int old_op, int new_op) const {
        return positivePart(new_op) - positivePart(old_op);
    }

    int routeTension(int route_id) const {
        const RouteInfo& rt = routes[route_id];
        double score = 0.0;
        for (int s : rt.visits) score += penaltyValue(s, final_inv[s]);
        return (int)std::round((double)(1000.0 * score));
    }

    int stationBoundCap(int route_id, int i, int j, int sign) const {
        const RouteInfo& rt = routes[route_id];
        int src_station = rt.visits[i];
        int cap = INF_INT;
        if (sign > 0) cap = min(cap, final_inv[src_station]);
        else cap = min(cap, CVal(src_station) - final_inv[src_station]);
        if (j != -1) {
            int sink_station = rt.visits[j];
            if (sign > 0) cap = min(cap, CVal(sink_station) - final_inv[sink_station]);
            else cap = min(cap, final_inv[sink_station]);
        }
        return max(0, cap);
    }

    int loadBoundCap(int route_id, int i, int j, int sign) const {
        const RouteInfo& rt = routes[route_id];
        int end = (j == -1) ? (int)rt.visits.size() : j;
        auto mm = rt.load_tree.queryMinMax(i, end - 1);
        if (sign > 0) return rt.capacity - mm.second;
        return mm.first;
    }

    int pickupDeltaForAmount(int old_src, int old_sink, int sign, bool has_sink, int d) const {
        int delta_pick = deltaPickupFromOpChange(old_src, old_src + sign * d);
        if (has_sink) delta_pick += deltaPickupFromOpChange(old_sink, old_sink - sign * d);
        return delta_pick;
    }

    int maxAmountByBudget(const RouteInfo& rt, int i, int j, int sign, int hard_cap) const {
        if (hard_cap <= 0) return 0;

        const int old_src = rt.visit_oper[i];
        const bool has_sink = (j != -1);
        const int old_sink = has_sink ? rt.visit_oper[j] : 0;

        const int lower_need = -rt.pickups_used;
        const int upper_room = rt.pickup_budget - rt.pickups_used;
        if (upper_room < lower_need) return 0;

        vector<int> bp;
        bp.reserve(4);
        bp.push_back(0);
        bp.push_back(hard_cap + 1);

        if (sign > 0) {
            if (old_src < 0) bp.push_back(-old_src);
            if (has_sink && old_sink > 0) bp.push_back(old_sink);
        } else {
            if (old_src > 0) bp.push_back(old_src);
            if (has_sink && old_sink < 0) bp.push_back(-old_sink);
        }

        for (int& x : bp) x = max(0, min(x, hard_cap + 1));
        std::sort(bp.begin(), bp.end());
        bp.erase(std::unique(bp.begin(), bp.end()), bp.end());

        auto consider_segment = [&](int l, int r, int& best) {
            if (l > r || l > hard_cap) return;
            r = min(r, hard_cap);
            if (l > r) return;

            int f_l = pickupDeltaForAmount(old_src, old_sink, sign, has_sink, l);
            if (l == r) {
                if (lower_need <= f_l && f_l <= upper_room) best = max(best, l);
                return;
            }

            int f_lp1 = pickupDeltaForAmount(old_src, old_sink, sign, has_sink, l + 1);
            int m = f_lp1 - f_l;
            int c = f_l - m * l;

            int lo = l, hi = r;
            if (m == 0) {
                if (lower_need <= c && c <= upper_room) best = max(best, hi);
                return;
            }
            if (m == 1) {
                lo = max(lo, lower_need - c);
                hi = min(hi, upper_room - c);
            } else if (m == -1) {
                lo = max(lo, c - upper_room);
                hi = min(hi, c - lower_need);
            } else {
                for (int d = l; d <= r; ++d) {
                    int f = pickupDeltaForAmount(old_src, old_sink, sign, has_sink, d);
                    if (lower_need <= f && f <= upper_room) best = max(best, d);
                }
                return;
            }
            if (lo <= hi) best = max(best, hi);
        };

        int best = 0;
        for (size_t z = 0; z + 1 < bp.size(); ++z) {
            int l = bp[z];
            int r = bp[z + 1] - 1;
            consider_segment(l, r, best);
        }
        return best;
    }

    bool prepareTemplate(int route_id, int i, int j, int sign, PreparedTemplate& pt) const {
        pt = PreparedTemplate{};
        const RouteInfo& rt = routes[route_id];
        int L = (int)rt.visits.size();
        if (i < 0 || i >= L) return false;
        if (j != -1 && (j <= i || j >= L)) return false;
        int end = (j == -1) ? L : j;
        if (end <= i) return false;
        int source_station = rt.visits[i];
        int sink_station = (j == -1) ? -1 : rt.visits[j];
        if (source_station == sink_station) return false;
        int cap_station = stationBoundCap(route_id, i, j, sign);
        if (cap_station <= 0) return false;
        int cap_load = loadBoundCap(route_id, i, j, sign);
        if (cap_load <= 0) return false;
        int hard_cap = min(cap_station, cap_load);
        int cap_budget = maxAmountByBudget(rt, i, j, sign, hard_cap);
        if (cap_budget <= 0) return false;
        pt.valid = true;
        pt.route = route_id;
        pt.source_pos = i;
        pt.sink_pos = j;
        pt.sign = sign;
        pt.end = end;
        pt.cap_budget = cap_budget;
        pt.source_station = source_station;
        pt.sink_station = sink_station;
        pt.old_src_op = rt.visit_oper[i];
        pt.old_sink_op = (j == -1) ? 0 : rt.visit_oper[j];
        pt.old_src_penalty = penaltyValue(source_station, final_inv[source_station]);
        pt.old_sink_penalty = (sink_station == -1) ? 0.0 : penaltyValue(sink_station, final_inv[sink_station]);
        return true;
    }

    Move evaluatePreparedMove(const PreparedTemplate& pt, int amount) const {
        Move mv;
        if (!pt.valid || amount <= 0 || amount > pt.cap_budget) return mv;
        int src_station = pt.source_station;
        int nf_src = final_inv[src_station] - pt.sign * amount;
        double penalty_new = penalty_sum + (penaltyValue(src_station, nf_src) - pt.old_src_penalty);
        RatioTracker::EvalResult eval;
        if (pt.sink_station == -1) {
            eval = tracker.evaluateOneChange(src_station, nf_src, ratio_sum);
        } else {
            int sink_station = pt.sink_station;
            int nf_sink = final_inv[sink_station] + pt.sign * amount;
            penalty_new += (penaltyValue(sink_station, nf_sink) - pt.old_sink_penalty);
            eval = tracker.evaluateTwoChange(src_station, nf_src, sink_station, nf_sink, ratio_sum);
        }
        int new_src_op = pt.old_src_op + pt.sign * amount;
        int pickup_delta = deltaPickupFromOpChange(pt.old_src_op, new_src_op);
        if (pt.sink_station != -1) {
            int new_sink_op = pt.old_sink_op - pt.sign * amount;
            pickup_delta += deltaPickupFromOpChange(pt.old_sink_op, new_sink_op);
        }
        double obj = (double)(scaling * (eval.gini_new + lambda * penalty_new));
        mv.valid = true;
        mv.route = pt.route;
        mv.source_pos = pt.source_pos;
        mv.sink_pos = pt.sink_pos;
        mv.amount = amount;
        mv.sign = pt.sign;
        mv.objective = obj;
        mv.ordered_pair_sum_new = eval.ordered_pair_sum_new;
        mv.ratio_sum_new = eval.ratio_sum_new;
        mv.gini_new = eval.gini_new;
        mv.penalty_sum_new = penalty_new;
        mv.pickup_delta = pickup_delta;
        return mv;
    }

    Move tryMove(int route_id, int i, int j, int sign, int amount) const {
        Move mv;
        if (amount <= 0) return mv;
        const RouteInfo& rt = routes[route_id];
        if (i < 0 || i >= (int)rt.visits.size()) return mv;
        if (j != -1 && (j <= i || j >= (int)rt.visits.size())) return mv;
        int end = (j == -1) ? (int)rt.visits.size() : j;
        if (end <= i) return mv;

        auto mm = rt.load_tree.queryMinMax(i, end - 1);
        if (sign > 0) {
            if (mm.second + amount > rt.capacity) return mv;
        } else {
            if (mm.first - amount < 0) return mv;
        }

        int old_src_op = rt.visit_oper[i];
        int new_src_op = old_src_op + sign * amount;
        int pickup_delta = deltaPickupFromOpChange(old_src_op, new_src_op);
        int sink_station = -1;
        if (j != -1) {
            int old_sink_op = rt.visit_oper[j];
            int new_sink_op = old_sink_op - sign * amount;
            pickup_delta += deltaPickupFromOpChange(old_sink_op, new_sink_op);
            sink_station = rt.visits[j];
        }
        if (rt.pickups_used + pickup_delta > rt.pickup_budget || rt.pickups_used + pickup_delta < 0) return mv;

        int source_station = rt.visits[i];
        if (source_station == sink_station) return mv;

        vector<int> stations;
        vector<int> deltas;
        stations.push_back(source_station);
        deltas.push_back(sign * amount);
        if (sink_station != -1) {
            stations.push_back(sink_station);
            deltas.push_back(-sign * amount);
        }

        vector<int> new_finals;
        new_finals.reserve(stations.size());
        double penalty_new = penalty_sum;
        for (size_t z = 0; z < stations.size(); ++z) {
            int s = stations[z];
            int nf = final_inv[s] - deltas[z];
            if (nf < 0 || nf > CVal(s)) return mv;
            penalty_new += (penaltyValue(s, nf) - penaltyValue(s, final_inv[s]));
            new_finals.push_back(nf);
        }

        auto eval = tracker.evaluateChange(stations, new_finals, ratio_sum);
        double obj = (double)(scaling * (eval.gini_new + lambda * penalty_new));

        mv.valid = true;
        mv.route = route_id;
        mv.source_pos = i;
        mv.sink_pos = j;
        mv.amount = amount;
        mv.sign = sign;
        mv.objective = obj;
        mv.ordered_pair_sum_new = eval.ordered_pair_sum_new;
        mv.ratio_sum_new = eval.ratio_sum_new;
        mv.gini_new = eval.gini_new;
        mv.penalty_sum_new = penalty_new;
        mv.pickup_delta = pickup_delta;
        return mv;
    }

    void applyMove(const Move& mv) {
        RouteInfo& rt = routes[mv.route];
        int i = mv.source_pos;
        int j = mv.sink_pos;
        int end = (j == -1) ? (int)rt.visits.size() : j;

        int src_station = rt.visits[i];
        rt.visit_oper[i] += mv.sign * mv.amount;
        rt.pickups_used += mv.pickup_delta;

        vector<int> stations;
        vector<int> new_finals;
        stations.push_back(src_station);
        station_oper[src_station] += mv.sign * mv.amount;
        final_inv[src_station] -= mv.sign * mv.amount;
        new_finals.push_back(final_inv[src_station]);

        if (j != -1) {
            int sink_station = rt.visits[j];
            rt.visit_oper[j] -= mv.sign * mv.amount;
            station_oper[sink_station] -= mv.sign * mv.amount;
            final_inv[sink_station] += mv.sign * mv.amount;
            stations.push_back(sink_station);
            new_finals.push_back(final_inv[sink_station]);
        }

        tracker.applyChange(stations, new_finals, mv.ordered_pair_sum_new);
        ordered_pair_sum = mv.ordered_pair_sum_new;
        ratio_sum = mv.ratio_sum_new;
        penalty_sum = mv.penalty_sum_new;
        current_gini = mv.gini_new;
        current_objective = mv.objective;
        rt.load_tree.rangeAdd(i, end - 1, mv.sign * mv.amount);
        invalidateSearchCaches();
    }

    Move bestIntervalMoveSearch() const {
        ensureAtomicCache(AtomicLimit);
        return atomic_cache_best;
    }

    void constructiveSeed(bool allow_depot_pick, bool reverse_order) {
        for (int step = 0; step < M; ++step) {
            int r = reverse_order ? (M - 1 - step) : step;
            RouteInfo& rt = routes[r];
            int L = (int)rt.visits.size();
            if (L == 0) continue;
            for (int i = 0; i < L; ++i) {
                int s = rt.visits[i];
                int supply = max(0, final_inv[s] - desired_final[s]);
                if (supply <= 0) continue;
                for (int jj = i + 1; jj < L && supply > 0; ++jj) {
                    int t = rt.visits[jj];
                    int demand = max(0, desired_final[t] - final_inv[t]);
                    if (demand <= 0) continue;
                    int hard = min(supply, min(stationBoundCap(r, i, jj, +1), loadBoundCap(r, i, jj, +1)));
                    if (hard <= 0) continue;
                    hard = maxAmountByBudget(rt, i, jj, +1, hard);
                    int d = min(supply, min(demand, hard));
                    if (d <= 0) continue;
                    PreparedTemplate pt;
                    prepareTemplate(r, i, jj, +1, pt);
                    Move mv = evaluatePreparedMove(pt, d);
                    if (mv.valid) {
                        applyMove(mv);
                        supply -= d;
                    }
                }
                if (!allow_depot_pick || supply <= 0) continue;
                int hard = min(supply, min(stationBoundCap(r, i, -1, +1), loadBoundCap(r, i, -1, +1)));
                if (hard <= 0) continue;
                hard = maxAmountByBudget(rt, i, -1, +1, hard);
                int d = min(supply, hard);
                if (d > 0) {
                    PreparedTemplate pt;
                    prepareTemplate(r, i, -1, +1, pt);
                    Move mv = evaluatePreparedMove(pt, d);
                    if (mv.valid) applyMove(mv);
                }
            }
        }
    }

    struct StaticRatioSet {
        vector<double> vals;
        vector<double> pref;
        double sum_vals = 0.0;
        double pair_sum = 0.0;
        double penalty = 0.0;
        double ratio_sum = 0.0;

        void build(const GreedyEngine* eng, const vector<int>& final_inv, const vector<char>& variable_mask) {
            vals.clear();
            pref.clear();
            sum_vals = 0.0;
            pair_sum = 0.0;
            penalty = 0.0;
            ratio_sum = 0.0;
            int V = (int)final_inv.size();
            for (int i = 0; i < V; ++i) {
                if (variable_mask[i]) continue;
                int target = eng->TVal(i);
                double r = (target > 0) ? ((double)final_inv[i] / (double)target) : 0.0;
                vals.push_back(r);
                ratio_sum += r;
                penalty += stationPenalty(final_inv[i], target, eng->WVal(i));
            }
            std::sort(vals.begin(), vals.end());
            pref.assign(vals.size() + 1, 0.0);
            for (size_t i = 0; i < vals.size(); ++i) pref[i + 1] = pref[i] + vals[i];
            sum_vals = pref.back();
            for (size_t i = 0; i < vals.size(); ++i) {
                pair_sum += vals[i] * (double)i - pref[i];
            }
            pair_sum *= 2.0;
        }

        double sumAbs(double x) const {
            size_t k = std::lower_bound(vals.begin(), vals.end(), x) - vals.begin();
            double left = x * (double)k - pref[k];
            double right = (sum_vals - pref[k]) - x * (double)(vals.size() - k);
            return left + right;
        }
    };

    struct ExactSubsetOracle {
        const GreedyEngine* eng = nullptr;
        vector<int> selected_routes;
        vector<vector<int>> sel_visits;
        vector<int> sel_caps;
        vector<int> sel_budgets;
        vector<int> current_front;
        vector<int> current_load;
        vector<int> current_pick;
        vector<int> assigned_final;
        vector<char> variable_mask;
        vector<int> variable_stations;
        StaticRatioSet comp_set;
        int nodes = 0;
        int node_limit = 1000000;
        double time_limit_sec = 0.50;
        std::chrono::steady_clock::time_point start;
        double best_obj = 0.0;
        vector<int> best_final;
        bool complete = true;

        void init(const GreedyEngine* e, const vector<int>& routes_in, int nlimit, double tlimit) {
            eng = e;
            selected_routes = routes_in;
            node_limit = nlimit;
            time_limit_sec = tlimit;
            int V = eng->V;
            variable_mask.assign(V, 0);
            variable_stations.clear();
            sel_visits.clear();
            sel_caps.clear();
            sel_budgets.clear();
            for (int rid : selected_routes) {
                sel_visits.push_back(eng->routes[rid].visits);
                sel_caps.push_back(eng->routes[rid].capacity);
                sel_budgets.push_back(eng->routes[rid].pickup_budget);
                for (int s : eng->routes[rid].visits) {
                    if (!variable_mask[s]) {
                        variable_mask[s] = 1;
                        variable_stations.push_back(s);
                    }
                }
            }
            assigned_final.assign(V, -1);
            for (int i = 0; i < V; ++i) {
                if (!variable_mask[i]) assigned_final[i] = eng->final_inv[i];
            }
            comp_set.build(eng, eng->final_inv, variable_mask);
            current_front.assign(selected_routes.size(), 0);
            current_load.assign(selected_routes.size(), 0);
            current_pick.assign(selected_routes.size(), 0);
            best_obj = eng->current_objective;
            best_final = eng->final_inv;
            nodes = 0;
            complete = true;
            start = std::chrono::steady_clock::now();
        }

        double elapsed() const {
            return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
        }

        double lowerBound() const {
            int V = eng->V;
            double S_max = comp_set.ratio_sum;
            double P_lb = comp_set.penalty;
            double D_lb = comp_set.pair_sum;
            vector<double> fixed_extra;
            vector<std::pair<double, double>> intervals;
            fixed_extra.reserve(variable_stations.size());
            intervals.reserve(variable_stations.size());

            for (size_t rr = 0; rr < selected_routes.size(); ++rr) {
                const auto& rt = sel_visits[rr];
                for (int pos = 0; pos < (int)rt.size(); ++pos) {
                    int s = rt[pos];
                    if (assigned_final[s] >= 0) {
                        int target = eng->TVal(s);
                        double r = (target > 0) ? ((double)assigned_final[s] / (double)target) : 0.0;
                        fixed_extra.push_back(r);
                        S_max += r;
                        P_lb += eng->WVal(s) * fabs(r - 1.0);
                    } else {
                        int lo, hi;
                        if (pos == current_front[rr]) {
                            lo = max(0, eng->IVal(s) - (sel_caps[rr] - current_load[rr]));
                            hi = min(eng->CVal(s), eng->IVal(s) + current_load[rr]);
                        } else if (pos > current_front[rr]) {
                            lo = max(0, eng->IVal(s) - sel_caps[rr]);
                            hi = min(eng->CVal(s), eng->IVal(s) + sel_caps[rr]);
                        } else {
                            continue;
                        }
                        int target = eng->TVal(s);
                        double rl = (target > 0) ? ((double)lo / (double)target) : 0.0;
                        double ru = (target > 0) ? ((double)hi / (double)target) : 0.0;
                        intervals.push_back({rl, ru});
                        S_max += ru;
                        if (1.0 < rl) P_lb += eng->WVal(s) * (rl - 1.0);
                        else if (1.0 > ru) P_lb += eng->WVal(s) * (1.0 - ru);
                    }
                }
            }

            for (double a : fixed_extra) {
                D_lb += 2.0 * comp_set.sumAbs(a);
            }
            for (size_t i = 0; i < fixed_extra.size(); ++i) {
                for (size_t j = 0; j < fixed_extra.size(); ++j) D_lb += fabs(fixed_extra[i] - fixed_extra[j]);
            }
            for (double a : fixed_extra) {
                for (auto pr : intervals) {
                    double d = 0.0;
                    if (a < pr.first) d = pr.first - a;
                    else if (a > pr.second) d = a - pr.second;
                    D_lb += 2.0 * d;
                }
            }
            for (size_t i = 0; i < intervals.size(); ++i) {
                for (size_t j = 0; j < intervals.size(); ++j) {
                    if (i == j) continue;
                    double d = max((double)0.0, max(intervals[i].first, intervals[j].first) - min(intervals[i].second, intervals[j].second));
                    D_lb += d;
                }
            }
            double G_lb = (S_max > EPS_LD) ? D_lb / (2.0 * (double)V * S_max) : 0.0;
            return eng->scaling * (G_lb + eng->lambda * P_lb);
        }

        struct Choice {
            int rr = -1;
            int station = -1;
            vector<int> dom;
        };

        Choice chooseNext() const {
            Choice best;
            for (size_t rr = 0; rr < selected_routes.size(); ++rr) {
                const auto& rt = sel_visits[rr];
                int pos = current_front[rr];
                if (pos >= (int)rt.size()) continue;
                int s = rt[pos];
                int lo = max(0, eng->IVal(s) - (sel_caps[rr] - current_load[rr]));
                int hi = min(eng->CVal(s), eng->IVal(s) + current_load[rr]);
                vector<int> dom;
                dom.reserve(max(0, hi - lo + 1));
                for (int F = lo; F <= hi; ++F) {
                    int delta = eng->IVal(s) - F;
                    int pu = max(delta, 0);
                    if (current_pick[rr] + pu <= sel_budgets[rr]) dom.push_back(F);
                }
                if (dom.empty()) return Choice{};
                int incumbent_val = eng->final_inv[s];
                std::sort(dom.begin(), dom.end(), [&](int a, int b) {
                    bool pa = (a == incumbent_val);
                    bool pb = (b == incumbent_val);
                    if (pa != pb) return pa > pb;
                    int target = eng->TVal(s);
                    double ra = (target > 0) ? (double)a / (double)target : 0.0;
                    double rb = (target > 0) ? (double)b / (double)target : 0.0;
                    double da = fabs(ra - 1.0), db = fabs(rb - 1.0);
                    if (fabs(da - db) > EPS_LD) return da < db;
                    return std::abs(a - eng->IVal(s)) < std::abs(b - eng->IVal(s));
                });
                if (best.rr == -1 || dom.size() < best.dom.size()) best = {(int)rr, s, std::move(dom)};
            }
            return best;
        }

        void dfs() {
            ++nodes;
            if (nodes > node_limit || elapsed() > time_limit_sec) {
                complete = false;
                return;
            }
            if (lowerBound() >= best_obj - EPS) return;
            bool done = true;
            for (size_t rr = 0; rr < selected_routes.size(); ++rr) {
                if (current_front[rr] < (int)sel_visits[rr].size()) { done = false; break; }
            }
            if (done) {
                double obj = eng->exactObjectiveFromFinal(assigned_final);
                if (obj + EPS < best_obj) {
                    best_obj = obj;
                    best_final = assigned_final;
                }
                return;
            }
            Choice ch = chooseNext();
            if (ch.rr == -1) return;
            int rr = ch.rr;
            int s = ch.station;
            int old_pos = current_front[rr];
            int old_load = current_load[rr];
            current_front[rr]++;
            for (int F : ch.dom) {
                int delta = eng->IVal(s) - F;
                int pu = max(delta, 0);
                assigned_final[s] = F;
                current_load[rr] = old_load + delta;
                current_pick[rr] += pu;
                dfs();
                current_pick[rr] -= pu;
                current_load[rr] = old_load;
                assigned_final[s] = -1;
                if (!complete && (nodes > node_limit || elapsed() > time_limit_sec)) {
                    // keep the best incumbent found so far but stop branching.
                    continue;
                }
            }
            current_front[rr] = old_pos;
        }
    };

    void applySelectedFinals(const vector<int>& new_final, const vector<int>& selected_routes) {
        vector<char> mask(V, 0);
        for (int rid : selected_routes) {
            RouteInfo& rt = routes[rid];
            rt.pickups_used = 0;
            for (size_t p = 0; p < rt.visits.size(); ++p) {
                int s = rt.visits[p];
                mask[s] = 1;
                int op = IVal(s) - new_final[s];
                rt.visit_oper[p] = op;
                rt.pickups_used += positivePart(op);
                station_oper[s] = op;
                final_inv[s] = new_final[s];
            }
            rebuildRouteLoadTree(rt);
        }
        vector<int> changed_stations;
        vector<int> new_finals;
        for (int i = 0; i < V; ++i) {
            if (mask[i]) {
                changed_stations.push_back(i);
                new_finals.push_back(final_inv[i]);
            }
        }
        (void)changed_stations;
        (void)new_finals;
        rebuildObjectiveState();
        invalidateSearchCaches();
    }




    struct LocalCandidate {
        bool valid = false;
        int route = -1;
        double objective = std::numeric_limits<double>::infinity();
        double ordered_pair_sum_new = 0.0;
        double ratio_sum_new = 0.0;
        double gini_new = 0.0;
        double penalty_sum_new = 0.0;
        double penalty_delta = 0.0;
        vector<int> pos_delta;
        vector<int> stations;
        vector<int> new_finals;
        int pickup_used_new = 0;
    };

    struct CrossCandidate {
        bool valid = false;
        int route_a = -1;
        int route_b = -1;
        LocalCandidate a, b;
        double objective = std::numeric_limits<double>::infinity();
        double ordered_pair_sum_new = 0.0;
        double ratio_sum_new = 0.0;
        double gini_new = 0.0;
        double penalty_sum_new = 0.0;
        vector<int> stations;
        vector<int> new_finals;
    };

    struct FlowPair {
        vector<int> pick_positions;
        vector<int> drop_positions;
    };

    vector<FlowPair> extractFlowPairs(const RouteInfo& rt) const {
        vector<FlowPair> pairs;
        struct Segment {
            int sign = 0;
            vector<int> positions;
        };
        vector<Segment> segs;
        for (int p = 0; p < (int)rt.visits.size(); ++p) {
            int op = rt.visit_oper[p];
            if (op == 0) continue;
            int sign = (op > 0) ? 1 : -1;
            if (segs.empty() || segs.back().sign != sign) segs.push_back(Segment{sign, {}});
            segs.back().positions.push_back(p);
        }
        for (size_t k = 0; k + 1 < segs.size(); ++k) {
            if (segs[k].sign > 0 && segs[k + 1].sign < 0) {
                pairs.push_back(FlowPair{segs[k].positions, segs[k + 1].positions});
            }
        }
        return pairs;
    }

    bool checkTwoIntervalDelta(const RouteInfo& rt,
        int l1, int r1, int delta1,
        int l2, int r2, int delta2) const {
        int L = (int)rt.visits.size();
        if (L <= 0) return true;
        vector<std::pair<int, int>> events;
        auto add_interval = [&](int l, int r, int delta) {
            if (delta == 0 || l > r) return;
            l = max(l, 0);
            r = min(r, L - 1);
            if (l > r) return;
            events.push_back({l, delta});
            if (r + 1 < L) events.push_back({r + 1, -delta});
        };
        add_interval(l1, r1, delta1);
        add_interval(l2, r2, delta2);
        if (events.empty()) return true;
        std::sort(events.begin(), events.end());
        int cur_delta = 0;
        int prev = 0;
        size_t idx = 0;
        while (idx < events.size()) {
            int pos = events[idx].first;
            if (prev <= pos - 1 && cur_delta != 0) {
                auto mm = rt.load_tree.queryMinMax(prev, pos - 1);
                if (mm.first + cur_delta < 0 || mm.second + cur_delta > rt.capacity) return false;
            }
            while (idx < events.size() && events[idx].first == pos) {
                cur_delta += events[idx].second;
                ++idx;
            }
            prev = pos;
        }
        if (prev <= L - 1 && cur_delta != 0) {
            auto mm = rt.load_tree.queryMinMax(prev, L - 1);
            if (mm.first + cur_delta < 0 || mm.second + cur_delta > rt.capacity) return false;
        }
        return true;
    }

    LocalCandidate evaluatePairTransferCandidate(int route_id,
        int pick_from, int drop_from,
        int pick_to, int drop_to,
        bool require_improve) const {
        LocalCandidate lc;
        const RouteInfo& rt = routes[route_id];
        const int L = (int)rt.visits.size();
        if (pick_from < 0 || drop_from <= pick_from || pick_to < 0 || drop_to <= pick_to) return lc;
        if (rt.visit_oper[pick_from] <= 0 || rt.visit_oper[drop_from] >= 0) return lc;
        if (rt.visit_oper[pick_to] <= 0 || rt.visit_oper[drop_to] >= 0) return lc;
        if (!checkTwoIntervalDelta(rt, pick_from, drop_from - 1, -1, pick_to, drop_to - 1, +1)) return lc;

        vector<int> pos_delta(L, 0);
        pos_delta[pick_from] -= 1;
        pos_delta[drop_from] += 1;
        pos_delta[pick_to] += 1;
        pos_delta[drop_to] -= 1;

        vector<std::pair<int, int>> touched;
        touched.reserve(4);
        for (int p : {pick_from, drop_from, pick_to, drop_to}) {
            if (pos_delta[p] != 0) touched.push_back({rt.visits[p], pos_delta[p]});
        }
        if (touched.empty()) return lc;
        std::sort(touched.begin(), touched.end(), [](const auto& a, const auto& b) {
            return a.first < b.first;
        });

        vector<int> stations;
        vector<int> new_finals;
        stations.reserve(touched.size());
        new_finals.reserve(touched.size());
        double pen_new = penalty_sum;
        for (size_t t = 0; t < touched.size(); ) {
            int s = touched[t].first;
            int d = 0;
            while (t < touched.size() && touched[t].first == s) {
                d += touched[t].second;
                ++t;
            }
            if (d == 0) continue;
            int nf = final_inv[s] - d;
            if (nf < 0 || nf > CVal(s)) return lc;
            pen_new += (penaltyValue(s, nf) - penaltyValue(s, final_inv[s]));
            stations.push_back(s);
            new_finals.push_back(nf);
        }
        if (stations.empty()) return lc;

        auto eval = tracker.evaluateChange(stations, new_finals, ratio_sum);
        double obj = (double)(scaling * (eval.gini_new + lambda * pen_new));
        if (require_improve && obj + EPS >= current_objective) return lc;

        lc.valid = true;
        lc.route = route_id;
        lc.objective = obj;
        lc.ordered_pair_sum_new = eval.ordered_pair_sum_new;
        lc.ratio_sum_new = eval.ratio_sum_new;
        lc.gini_new = eval.gini_new;
        lc.penalty_sum_new = pen_new;
        lc.penalty_delta = pen_new - penalty_sum;
        lc.pos_delta = std::move(pos_delta);
        lc.stations = std::move(stations);
        lc.new_finals = std::move(new_finals);
        lc.pickup_used_new = rt.pickups_used;
        return lc;
    }

    LocalCandidate makeAtomicCandidate(const Move& mv, bool require_improve) const {
        LocalCandidate lc;
        if (!mv.valid) return lc;
        const RouteInfo& rt = routes[mv.route];
        int L = (int)rt.visits.size();
        lc.valid = true;
        lc.route = mv.route;
        lc.objective = mv.objective;
        lc.ordered_pair_sum_new = mv.ordered_pair_sum_new;
        lc.ratio_sum_new = mv.ratio_sum_new;
        lc.gini_new = mv.gini_new;
        lc.penalty_sum_new = mv.penalty_sum_new;
        lc.penalty_delta = mv.penalty_sum_new - penalty_sum;
        lc.pos_delta.assign(L, 0);
        lc.pos_delta[mv.source_pos] += mv.sign * mv.amount;
        if (mv.sink_pos != -1) lc.pos_delta[mv.sink_pos] -= mv.sign * mv.amount;
        lc.pickup_used_new = rt.pickups_used + mv.pickup_delta;
        lc.stations.push_back(rt.visits[mv.source_pos]);
        lc.new_finals.push_back(final_inv[rt.visits[mv.source_pos]] - mv.sign * mv.amount);
        if (mv.sink_pos != -1) {
            lc.stations.push_back(rt.visits[mv.sink_pos]);
            lc.new_finals.push_back(final_inv[rt.visits[mv.sink_pos]] + mv.sign * mv.amount);
        }
        if (require_improve && mv.objective + EPS >= current_objective) lc.valid = false;
        return lc;
    }

    LocalCandidate tryPairCandidateSameRoute(int route_id, const Move& m1, const Move& m2, bool require_improve) const {
        LocalCandidate lc;
        if (!m1.valid || !m2.valid) return lc;
        if (m1.route != route_id || m2.route != route_id) return lc;
        const RouteInfo& rt = routes[route_id];
        int L = (int)rt.visits.size();
        if (L == 0) return lc;

        vector<int> pos_delta(L, 0);
        auto add_move = [&](const Move& mv) {
            pos_delta[mv.source_pos] += mv.sign * mv.amount;
            if (mv.sink_pos != -1) pos_delta[mv.sink_pos] -= mv.sign * mv.amount;
        };
        add_move(m1);
        add_move(m2);

        int load = 0;
        int pickup_new = 0;
        for (int p = 0; p < L; ++p) {
            int op = rt.visit_oper[p] + pos_delta[p];
            load += op;
            if (load < 0 || load > rt.capacity) return lc;
            pickup_new += positivePart(op);
            if (pickup_new > rt.pickup_budget) return lc;
        }

        vector<std::pair<int, int>> touched;
        touched.reserve(L);
        for (int p = 0; p < L; ++p) {
            if (pos_delta[p] != 0) touched.push_back({rt.visits[p], pos_delta[p]});
        }
        if (touched.empty()) return lc;
        std::sort(touched.begin(), touched.end(), [](const std::pair<int, int>& a, const std::pair<int, int>& b) {
            return a.first < b.first;
        });

        vector<int> stations;
        vector<int> deltas;
        stations.reserve(touched.size());
        deltas.reserve(touched.size());
        for (size_t t = 0; t < touched.size(); ) {
            int s = touched[t].first;
            int d = 0;
            while (t < touched.size() && touched[t].first == s) {
                d += touched[t].second;
                ++t;
            }
            if (d != 0) {
                stations.push_back(s);
                deltas.push_back(d);
            }
        }

        vector<int> new_finals;
        new_finals.reserve(stations.size());
        double pen_new = penalty_sum;
        for (size_t z = 0; z < stations.size(); ++z) {
            int s = stations[z];
            int nf = final_inv[s] - deltas[z];
            if (nf < 0 || nf > CVal(s)) return lc;
            pen_new += (penaltyValue(s, nf) - penaltyValue(s, final_inv[s]));
            new_finals.push_back(nf);
        }
        if (stations.empty()) return lc;
        auto eval = tracker.evaluateChange(stations, new_finals, ratio_sum);
        double obj = (double)(scaling * (eval.gini_new + lambda * pen_new));
        if (require_improve && obj + EPS >= current_objective) return lc;

        lc.valid = true;
        lc.route = route_id;
        lc.objective = obj;
        lc.ordered_pair_sum_new = eval.ordered_pair_sum_new;
        lc.ratio_sum_new = eval.ratio_sum_new;
        lc.gini_new = eval.gini_new;
        lc.penalty_sum_new = pen_new;
        lc.penalty_delta = pen_new - penalty_sum;
        lc.pos_delta = std::move(pos_delta);
        lc.stations = std::move(stations);
        lc.new_finals = std::move(new_finals);
        lc.pickup_used_new = pickup_new;
        return lc;
    }

    void applyLocalCandidate(const LocalCandidate& lc) {
        RouteInfo& rt = routes[lc.route];
        int L = (int)rt.visits.size();
        for (int p = 0; p < L; ++p) rt.visit_oper[p] += lc.pos_delta[p];
        rt.pickups_used = lc.pickup_used_new;
        rebuildRouteLoadTree(rt);
        for (size_t z = 0; z < lc.stations.size(); ++z) {
            int s = lc.stations[z];
            station_oper[s] = IVal(s) - lc.new_finals[z];
            final_inv[s] = lc.new_finals[z];
        }
        tracker.applyChange(lc.stations, lc.new_finals, lc.ordered_pair_sum_new);
        ordered_pair_sum = lc.ordered_pair_sum_new;
        ratio_sum = lc.ratio_sum_new;
        penalty_sum = lc.penalty_sum_new;
        current_gini = lc.gini_new;
        current_objective = lc.objective;
        invalidateSearchCaches();
    }

    void applyCrossCandidate(const CrossCandidate& cc) {
        applyLocalCandidate(cc.a);
        // b was built on the pre-move state, so reapply by direct route mutation instead of recompute via objective.
        RouteInfo& rt = routes[cc.route_b];
        int L = (int)rt.visits.size();
        for (int p = 0; p < L; ++p) rt.visit_oper[p] += cc.b.pos_delta[p];
        rt.pickups_used = cc.b.pickup_used_new;
        rebuildRouteLoadTree(rt);
        for (size_t z = 0; z < cc.stations.size(); ++z) {
            int s = cc.stations[z];
            final_inv[s] = cc.new_finals[z];
            station_oper[s] = IVal(s) - cc.new_finals[z];
        }
        tracker.applyChange(cc.stations, cc.new_finals, cc.ordered_pair_sum_new);
        ordered_pair_sum = cc.ordered_pair_sum_new;
        ratio_sum = cc.ratio_sum_new;
        penalty_sum = cc.penalty_sum_new;
        current_gini = cc.gini_new;
        current_objective = cc.objective;
        invalidateSearchCaches();
    }

    void ensureAtomicCache(int K) const {
        if (K <= 0) return;
        if (atomic_cache_epoch == state_epoch && atomic_cache_K >= K) return;
        atomic_cache_best = Move{};
        atomic_cache_best.valid = false;
        atomic_cache_best.objective = current_objective - EPS;
        atomic_cache_top.assign(M, {});
        atomic_cache_K = K;
        auto worse = [](const Move& a, const Move& b) { return a.objective < b.objective; };

        for (int r = 0; r < M; ++r) {
            const RouteInfo& rt = routes[r];
            int L = (int)rt.visits.size();
            if (L == 0) continue;
            vector<Move>& top = atomic_cache_top[r];
            for (int i = 0; i < L; ++i) {
                for (int jj = i + 1; jj <= L; ++jj) {
                    int j = (jj == L) ? -1 : jj;
                    for (int sign : {+1, -1}) {
                        PreparedTemplate pt;
                        if (!prepareTemplate(r, i, j, sign, pt)) continue;
                        for (int d = 1; d <= pt.cap_budget; ++d) {
                            Move cand = evaluatePreparedMove(pt, d);
                            if (cand.objective + EPS < atomic_cache_best.objective) atomic_cache_best = cand;
                            if ((int)top.size() < K) {
                                top.push_back(cand);
                                std::push_heap(top.begin(), top.end(), worse);
                            } else if (cand.objective + EPS < top.front().objective) {
                                std::pop_heap(top.begin(), top.end(), worse);
                                top.back() = cand;
                                std::push_heap(top.begin(), top.end(), worse);
                            }
                        }
                    }
                }
            }
            std::sort(top.begin(), top.end(), [](const Move& a, const Move& b) { return a.objective < b.objective; });
        }
        atomic_cache_epoch = state_epoch;
        local_cache_epoch = 0;
        local_cache_all.clear();
    }

    void ensureLocalCandidateCache() const {
        if (local_cache_epoch == state_epoch) return;
        ensureAtomicCache(AtomicLimit);
        local_cache_all.assign(M, {});
        auto worse = [](const LocalCandidate& a, const LocalCandidate& b) { return a.objective < b.objective; };
        for (int route_id = 0; route_id < M; ++route_id) {
            if (routes[route_id].visits.empty()) continue;
            vector<LocalCandidate>& best = local_cache_all[route_id];
            auto consider = [&](const LocalCandidate& cand) {
                if (!cand.valid) return;
                if ((int)best.size() < LocalLimit) {
                    best.push_back(cand);
                    std::push_heap(best.begin(), best.end(), worse);
                } else if (cand.objective + EPS < best.front().objective) {
                    std::pop_heap(best.begin(), best.end(), worse);
                    best.back() = cand;
                    std::push_heap(best.begin(), best.end(), worse);
                }
            };
            const auto& atoms = atomic_cache_top[route_id];
            for (const Move& mv : atoms) consider(makeAtomicCandidate(mv, false));
            for (size_t i = 0; i < atoms.size(); ++i) {
                for (size_t j = i + 1; j < atoms.size(); ++j) {
                    consider(tryPairCandidateSameRoute(route_id, atoms[i], atoms[j], false));
                }
            }
            std::sort(best.begin(), best.end(), [](const LocalCandidate& a, const LocalCandidate& b) { return a.objective < b.objective; });
        }
        local_cache_epoch = state_epoch;
    }

    vector<Move> collectTopRouteMoves(int route_id, int K) const {
        vector<Move> top;
        if (route_id < 0 || route_id >= M || K <= 0 || routes[route_id].visits.empty()) return top;
        ensureAtomicCache(K);
        top = atomic_cache_top[route_id];
        if ((int)top.size() > K) top.resize(K);
        return top;
    }

    vector<LocalCandidate> collectLocalCandidates(int route_id, bool require_improve) const {
        vector<LocalCandidate> out;
        if (route_id < 0 || route_id >= M || routes[route_id].visits.empty()) return out;
        ensureLocalCandidateCache();
        const auto& all = local_cache_all[route_id];
        if (!require_improve) return all;
        for (const auto& cand : all) {
            if (cand.objective + EPS < current_objective) out.push_back(cand);
            else break;
        }
        return out;
    }

    bool tryLocalCompositeNeighborhood() {
        ensureLocalCandidateCache();
        LocalCandidate best;
        best.objective = current_objective - EPS;
        for (int r = 0; r < M; ++r) {
            if (routes[r].visits.empty()) continue;
            const auto& cand = local_cache_all[r];
            if (!cand.empty() && cand.front().objective + EPS < best.objective) best = cand.front();
        }
        if (!best.valid) return false;
        applyLocalCandidate(best);
        return true;
    }

    bool tryPairedIntervalNeighborhood() {
        if (M < 2) return false;
        ensureLocalCandidateCache();
        const vector<vector<LocalCandidate>>& pool = local_cache_all;
        CrossCandidate best;
        best.objective = current_objective - EPS;
        int station_buf[8];
        int final_buf[8];
        for (int a = 0; a < M; ++a) {
            if (pool[a].empty()) continue;
            for (int b = a + 1; b < M; ++b) {
                if (pool[b].empty()) continue;
                for (const LocalCandidate& ca : pool[a]) {
                    for (const LocalCandidate& cb : pool[b]) {
                        int k = 0;
                        for (size_t t = 0; t < ca.stations.size(); ++t) {
                            station_buf[k] = ca.stations[t];
                            final_buf[k] = ca.new_finals[t];
                            ++k;
                        }
                        for (size_t t = 0; t < cb.stations.size(); ++t) {
                            station_buf[k] = cb.stations[t];
                            final_buf[k] = cb.new_finals[t];
                            ++k;
                        }
                        double pen_new = penalty_sum + ca.penalty_delta + cb.penalty_delta;
                        auto eval = tracker.evaluateChangeRaw(station_buf, final_buf, k, ratio_sum);
                        double obj = (double)(scaling * (eval.gini_new + lambda * pen_new));
                        if (obj + EPS < best.objective) {
                            best.valid = true;
                            best.route_a = a;
                            best.route_b = b;
                            best.a = ca;
                            best.b = cb;
                            best.objective = obj;
                            best.ordered_pair_sum_new = eval.ordered_pair_sum_new;
                            best.ratio_sum_new = eval.ratio_sum_new;
                            best.gini_new = eval.gini_new;
                            best.penalty_sum_new = pen_new;
                            best.stations.assign(station_buf, station_buf + k);
                            best.new_finals.assign(final_buf, final_buf + k);
                        }
                    }
                }
            }
        }
        if (!best.valid) return false;
        applyCrossCandidate(best);
        return true;
    }


    bool tryResidualUnitPolish() {
        Move best;
        static constexpr double POLISH_EPS = 1e-14;
        best.objective = current_objective - POLISH_EPS;
        for (int r = 0; r < M; ++r) {
            const RouteInfo& rt = routes[r];
            int L = (int)rt.visits.size();
            if (L == 0) continue;
            for (int i = 0; i < L; ++i) {
                for (int jj = i + 1; jj <= L; ++jj) {
                    int j = (jj == L) ? -1 : jj;
                    for (int sign : {+1, -1}) {
                        PreparedTemplate pt;
                        if (!prepareTemplate(r, i, j, sign, pt)) continue;
                        Move cand = evaluatePreparedMove(pt, 1);
                        //std::cout << i+1 << " " << j+1 << " " << cand.objective << std::endl;
                        if (cand.valid && cand.objective + POLISH_EPS < best.objective) best = cand;
                    }
                }
            }
        }
        if (!best.valid) return false;
        applyMove(best);
        return true;
    }

    bool tryPairFlowRebalanceNeighborhood() {
        LocalCandidate best;
        static constexpr double POLISH_EPS = 1e-14;
        best.objective = current_objective - POLISH_EPS;
        for (int r = 0; r < M; ++r) {
            const RouteInfo& rt = routes[r];
            if (rt.visits.size() <= 1) continue;
            vector<FlowPair> pairs = extractFlowPairs(rt);
            if (pairs.size() <= 1) continue;
            for (size_t a = 0; a < pairs.size(); ++a) {
                for (size_t b = 0; b < pairs.size(); ++b) {
                    if (a == b) continue;
                    // std::cout << pairs[a].pick_positions.size() << " " << pairs[a].drop_positions.size() << std::endl;
                    for (int pick_from : pairs[a].pick_positions) {
                        for (int drop_from : pairs[a].drop_positions) {
                            for (int pick_to : pairs[b].pick_positions) {
                                for (int drop_to : pairs[b].drop_positions) {
                                    LocalCandidate cand = evaluatePairTransferCandidate(r, pick_from, drop_from, pick_to, drop_to, true);
                                    if (cand.valid && cand.objective + POLISH_EPS < best.objective) best = cand;
                                }
                            }
                        }
                    }
                }
            }
        }
        if (!best.valid) return false;
        applyLocalCandidate(best);
        return true;
    }

    bool tryResidualPairUnitPolish() {  return false; /* disabled in fast unified mode */
        static constexpr double POLISH_EPS = 1e-14;
        static constexpr int GLOBAL_KEEP = 12;
        static constexpr int PER_SOURCE_KEEP = 2;
        static constexpr int PER_SINK_KEEP = 1;

        auto moveKey = [](const Move& mv) {
            return std::make_tuple(mv.source_pos, mv.sink_pos, mv.sign, mv.amount);
        };
        auto better = [](const Move& a, const Move& b) { return a.objective < b.objective; };

        LocalCandidate best;
        best.objective = current_objective - POLISH_EPS;

        for (int r = 0; r < M; ++r) {
            const RouteInfo& rt = routes[r];
            const int L = (int)rt.visits.size();
            if (L <= 1) continue;

            vector<Move> global_top;
            vector<vector<vector<Move>>> by_source(L, vector<vector<Move>>(2));
            vector<vector<Move>> by_sink(L + 1, vector<Move>(2));
            vector<vector<char>> by_sink_used(L + 1, vector<char>(2, 0));

            auto consider_top = [&](vector<Move>& bucket, const Move& cand, int keep) {
                if (!cand.valid || keep <= 0) return;
                if ((int)bucket.size() < keep) {
                    bucket.push_back(cand);
                    std::push_heap(bucket.begin(), bucket.end(), [](const Move& a, const Move& b) { return a.objective < b.objective; });
                } else if (cand.objective + EPS < bucket.front().objective) {
                    std::pop_heap(bucket.begin(), bucket.end(), [](const Move& a, const Move& b) { return a.objective < b.objective; });
                    bucket.back() = cand;
                    std::push_heap(bucket.begin(), bucket.end(), [](const Move& a, const Move& b) { return a.objective < b.objective; });
                }
            };

            for (int i = 0; i < L; ++i) {
                for (int jj = i + 1; jj <= L; ++jj) {
                    int j = (jj == L) ? -1 : jj;
                    for (int sign : {+1, -1}) {
                        PreparedTemplate pt;
                        if (!prepareTemplate(r, i, j, sign, pt)) continue;
                        Move cand = evaluatePreparedMove(pt, 1);
                        if (!cand.valid) continue;
                        consider_top(global_top, cand, GLOBAL_KEEP);
                        int sid = (sign > 0) ? 1 : 0;
                        consider_top(by_source[i][sid], cand, PER_SOURCE_KEEP);
                        int sink_bucket = (j == -1) ? L : j;
                        if (!by_sink_used[sink_bucket][sid] || cand.objective + EPS < by_sink[sink_bucket][sid].objective) {
                            by_sink[sink_bucket][sid] = cand;
                            by_sink_used[sink_bucket][sid] = 1;
                        }
                    }
                }
            }

            vector<Move> pool;
            pool.reserve(GLOBAL_KEEP + 3 * L);
            for (auto mv : global_top) pool.push_back(mv);
            for (int i = 0; i < L; ++i) {
                for (int sid = 0; sid < 2; ++sid) {
                    for (const Move& mv : by_source[i][sid]) pool.push_back(mv);
                }
            }
            for (int j = 0; j <= L; ++j) {
                for (int sid = 0; sid < 2; ++sid) if (by_sink_used[j][sid]) pool.push_back(by_sink[j][sid]);
            }
            std::sort(pool.begin(), pool.end(), [&](const Move& a, const Move& b) {
                if (std::fabs(a.objective - b.objective) > EPS) return a.objective < b.objective;
                return moveKey(a) < moveKey(b);
            });
            pool.erase(std::unique(pool.begin(), pool.end(), [&](const Move& a, const Move& b) {
                return moveKey(a) == moveKey(b);
            }), pool.end());

            for (size_t a = 0; a < pool.size(); ++a) {
                for (size_t b = a + 1; b < pool.size(); ++b) {
                    if (pool[a].sign != pool[b].sign) continue;
                    if (moveKey(pool[a]) == moveKey(pool[b])) continue;
                    LocalCandidate cand = tryPairCandidateSameRoute(r, pool[a], pool[b], true);
                    if (cand.valid && cand.objective + POLISH_EPS < best.objective) best = cand;
                }
            }
        }

        if (!best.valid) return false;
        applyLocalCandidate(best);
        return true;
    }

    bool tryRouteExactNeighborhood() { return false; /* disabled in fast unified mode */

        vector<std::pair<int, int>> ord;
        ord.reserve(M);
        for (int r = 0; r < M; ++r) if (!routes[r].visits.empty()) ord.push_back({-routeTension(r), r});
        std::sort(ord.begin(), ord.end());
        bool improved = false;
        for (auto pr : ord) {
            int r = pr.second;
            ExactSubsetOracle oracle;
            oracle.init(this, vector<int>{r}, 300000, 0.10);
            oracle.dfs();
            if (oracle.best_obj + EPS < current_objective) {
                applySelectedFinals(oracle.best_final, vector<int>{r});
                improved = true;
                break;
            }
        }
        return improved;
    }

    bool tryPairExactNeighborhood() { return false; /* disabled in fast unified mode */

        if (M < 2) return false;
        vector<std::pair<int, int>> tension;
        for (int r = 0; r < M; ++r) {
            if (!routes[r].visits.empty()) tension.push_back({routeTension(r), r});
        }
        if ((int)tension.size() < 2) return false;
        vector<std::tuple<int, int, int>> pairs;
        for (size_t i = 0; i < tension.size(); ++i) {
            for (size_t j = i + 1; j < tension.size(); ++j) {
                pairs.emplace_back(-(tension[i].first + tension[j].first), tension[i].second, tension[j].second);
            }
        }
        std::sort(pairs.begin(), pairs.end());
        const int pair_trials = min(3, (int)pairs.size());
        for (int z = 0; z < pair_trials; ++z) {
            int a = std::get<1>(pairs[z]);
            int b = std::get<2>(pairs[z]);
            ExactSubsetOracle oracle;
            oracle.init(this, vector<int>{a, b}, 1200000, 0.40);
            oracle.dfs();
            if (oracle.best_obj + EPS < current_objective) {
                applySelectedFinals(oracle.best_final, vector<int>{a, b});
                return true;
            }
        }
        return false;
    }

    SolutionResult_ORO runFromCurrentState(int mode) {
        bool allow_depot_pick = (mode == 1 || mode == 3);
        bool reverse_seed = (mode == 2 || mode == 3);
        constructiveSeed(allow_depot_pick, reverse_seed);
        while (true) {
            bool any_interval = false;
            while (true) {
                Move mv = bestIntervalMoveSearch();
                if (!mv.valid || mv.objective + EPS >= current_objective) break;
                applyMove(mv);
                any_interval = true;
            }
            if (tryLocalCompositeNeighborhood()) continue;
            if (tryPairedIntervalNeighborhood()) continue;
            if (tryResidualUnitPolish()) continue;
            if (tryPairFlowRebalanceNeighborhood()) continue;
            if (!any_interval) break;
        }

        SolutionResult_ORO res;
        res.Y_Oper_best = station_oper;
        res.objective_value = current_objective;
        res.r_avg_best = -1.0;
        return res;
    }

    SolutionResult_ORO runOneMode(int max_moves, int mode) {
        (void)max_moves;
        initializeState();
        return runFromCurrentState(mode);
    }
};

template <typename T>
int inferDepotOffset(const vector<T>& src, int V) {
    return ((int)src.size() >= V + 1) ? 1 : 0;
}

} // namespace

SolutionResult_ORO nF_R(int IterNum, int V, int M, double r_avgi, double total_time_limit,
    const vector<vector<int>>& routes, const vector<int>& Q, const vector<vector<double>>& dist,
    const vector<int>& Y_Ii, const vector<int>& Y_Ri, const vector<int>& Ci,
    const vector<double>& Wi, const vector<double>& min_ratio, double lambda, double scaling) {

    (void)IterNum;
    (void)r_avgi;
    const int I_off = inferDepotOffset(Y_Ii, V);
    const int T_off = inferDepotOffset(Y_Ri, V);
    const int C_off = inferDepotOffset(Ci, V);
    const int W_off = inferDepotOffset(Wi, V);
    const int min_ratio_off = inferDepotOffset(min_ratio, V);

    const double effective_lambda = (lambda >= 0.0) ? lambda : get_greedy_objective_lambda();
    const double effective_scaling = (scaling > 0.0) ? scaling : get_greedy_objective_scaling();

    GreedyEngine engine;
    engine.V = V;
    engine.M = M;
    engine.total_time_limit = total_time_limit;
    engine.lambda = effective_lambda;
    engine.scaling = effective_scaling;
    engine.max_accept_moves = 0;
    engine.I_src = &Y_Ii;
    engine.T_src = &Y_Ri;
    engine.C_src = &Ci;
    engine.W_src = &Wi;
    engine.min_ratio_src = &min_ratio;
    engine.I_off = I_off;
    engine.T_off = T_off;
    engine.C_off = C_off;
    engine.W_off = W_off;
    engine.min_ratio_off = min_ratio_off;
    engine.buildPenaltyTable();
    engine.buildRoutes(routes, Q, dist);

    if (greedy_route_stats_enabled) {
        double total_dist = 0.0;
        int total_nodes = 0;
        for (const auto& rt : engine.routes) {
            total_dist += rt.travel_time;
            total_nodes += (int)rt.visits.size();
        }
        double avg_dist = (M > 0) ? total_dist / (double)M : 0.0;
        double avg_nodes = (M > 0) ? (double)total_nodes / (double)M : 0.0;
        std::cout << "[Greedy] Avg route length=" << avg_dist
                  << " Avg visited nodes=" << avg_nodes
                  << " (routes=" << M << ")" << std::endl;
    }

    const int modes[1] = {1};
    int tries = 1;
    SolutionResult_ORO best_res;
    bool first = true;
    for (int k = 0; k < tries; ++k) {
        SolutionResult_ORO cur = engine.runOneMode(0, modes[k]);
        if (first || cur.objective_value < best_res.objective_value) {
            best_res = cur;
            first = false;
        }
    }
    return best_res;
}

SolutionResult_ORO enhanced_armijo_search1(
    const int V, const int M,
    const double r0,
    const double ttl,
    const vector<vector<int>>& routes,
    const vector<int>& Q,
    const vector<vector<double>>& dist,
    const vector<int>& Y_Ii,
    const vector<int>& Y_Ri,
    const vector<int>& Ci,
    const vector<double>& W,
    const vector<double>& min_ratio,
    double lambda,
    double scaling,
    double init_step,
    double gamma,
    double beta,
    double min_step,
    int max_iter,
    double tol
) {
    (void)init_step;
    (void)gamma;
    (void)beta;
    (void)min_step;
    (void)max_iter;
    (void)tol;
    return nF_R(2, V, M, r0, ttl, routes, Q, dist, Y_Ii, Y_Ri, Ci, W, min_ratio, lambda, scaling);
}

SolutionResult_ORO nGreedyLU_RA(int IterNum, int V, int M, double total_time_limit, const vector<vector<int>>& routes,
    const vector<int>& Q, const vector<int>& s, const vector<int>& c, const vector<int>& t,
    const vector<vector<double>>& dist, const int& max_iter, const double& r_avg_start,
    const vector<double>& Wi, const vector<double>& min_ratio, double lambda, double scaling) {

    (void)max_iter;
    SolutionResult_ORO best_res = nF_R(1, V, M, r_avg_start, total_time_limit,
        routes, Q, dist, s, t, c, Wi, min_ratio, lambda, scaling);
    best_res.objective_value = -best_res.objective_value;
    return best_res;
}

SolutionResult_ORO nGreedyLU_RA_route_incremental(int V, double total_time_limit,
    const vector<int>& route, int Q_single,
    const vector<int>& s, const vector<int>& c, const vector<int>& t,
    const vector<vector<double>>& dist,
    const vector<int>& fixed_station_oper,
    const vector<double>& Wi, const vector<double>& min_ratio,
    double lambda, double scaling) {

    const int I_off = inferDepotOffset(s, V);
    const int T_off = inferDepotOffset(t, V);
    const int C_off = inferDepotOffset(c, V);
    const int fixed_off = inferDepotOffset(fixed_station_oper, V);
    const int W_off = inferDepotOffset(Wi, V);
    const int min_ratio_off = inferDepotOffset(min_ratio, V);

    GreedyEngine engine;
    engine.V = V;
    engine.M = 1;
    engine.total_time_limit = total_time_limit;
    engine.lambda = (lambda >= 0.0) ? lambda : get_greedy_objective_lambda();
    engine.scaling = (scaling > 0.0) ? scaling : get_greedy_objective_scaling();
    engine.max_accept_moves = 0;
    engine.I_src = &s;
    engine.T_src = &t;
    engine.C_src = &c;
    engine.W_src = &Wi;
    engine.min_ratio_src = &min_ratio;
    engine.I_off = I_off;
    engine.T_off = T_off;
    engine.C_off = C_off;
    engine.W_off = W_off;
    engine.min_ratio_off = min_ratio_off;
    engine.buildPenaltyTable();
    engine.buildRoutes(vector<vector<int>>{route}, vector<int>{Q_single}, dist);
    engine.initializeFixedState(fixed_station_oper, fixed_off);
    SolutionResult_ORO res = engine.runFromCurrentState(1);
    res.objective_value = -res.objective_value;
    return res;
}

namespace {

static GreedyRouteProfile extractRouteProfileFromEngine(const GreedyEngine& engine) {
    GreedyRouteProfile prof;
    prof.objective_value = -engine.current_objective;
    if (engine.routes.empty()) return prof;
    const RouteInfo& rt = engine.routes[0];
    prof.pickup_budget = rt.pickup_budget;
    prof.pickups_used = rt.pickups_used;
    prof.travel_time = rt.travel_time;
    prof.visited_nodes.reserve(rt.visits.size());
    prof.visit_oper = rt.visit_oper;
    prof.load_after_visit.reserve(rt.visits.size());
    int load = 0;
    for (int p = 0; p < (int)rt.visits.size(); ++p) {
        prof.visited_nodes.push_back(rt.visits[p] + 1);
        load += rt.visit_oper[p];
        prof.load_after_visit.push_back(load);
    }
    return prof;
}

static GreedyEngine buildSingleRouteEngineWithOffsets(
    int V, double total_time_limit,
    const vector<int>& route, int Q_single,
    const vector<int>& s, const vector<int>& c, const vector<int>& t,
    const vector<vector<double>>& dist,
    const vector<int>& fixed_station_oper,
    const vector<double>& Wi, const vector<double>& min_ratio,
    double lambda, double scaling,
    int I_off, int C_off, int T_off, int fixed_off, int W_off, int min_ratio_off) {

    GreedyEngine engine;
    engine.V = V;
    engine.M = 1;
    engine.total_time_limit = total_time_limit;
    engine.lambda = (lambda >= 0.0) ? lambda : get_greedy_objective_lambda();
    engine.scaling = (scaling > 0.0) ? scaling : get_greedy_objective_scaling();
    engine.max_accept_moves = 0;
    engine.I_src = &s;
    engine.C_src = &c;
    engine.T_src = &t;
    engine.W_src = &Wi;
    engine.min_ratio_src = &min_ratio;
    engine.I_off = I_off;
    engine.C_off = C_off;
    engine.T_off = T_off;
    engine.W_off = W_off;
    engine.min_ratio_off = min_ratio_off;
    engine.buildPenaltyTable();
    engine.buildRoutes(vector<vector<int>>{route}, vector<int>{Q_single}, dist);
    engine.initializeFixedState(fixed_station_oper, fixed_off);
    return engine;
}

} // namespace

SolutionResult_ORO nGreedyLU_RA_route_incremental_norm(int V, double total_time_limit,
    const vector<int>& route, int Q_single,
    const vector<int>& s0, const vector<int>& c0, const vector<int>& t0,
    const vector<vector<double>>& dist,
    const vector<int>& fixed_station_oper0,
    const vector<double>& W0, const vector<double>& min_ratio0,
    double lambda, double scaling) {

    GreedyEngine engine = buildSingleRouteEngineWithOffsets(
        V, total_time_limit, route, Q_single, s0, c0, t0, dist, fixed_station_oper0, W0, min_ratio0,
        lambda, scaling, 0, 0, 0, 0, 0, 0);
    SolutionResult_ORO res = engine.runFromCurrentState(1);
    res.objective_value = -res.objective_value;
    return res;
}

GreedyRouteProfile nGreedyLU_RA_route_profile_incremental_norm(int V, double total_time_limit,
    const vector<int>& route, int Q_single,
    const vector<int>& s0, const vector<int>& c0, const vector<int>& t0,
    const vector<vector<double>>& dist,
    const vector<int>& fixed_station_oper0,
    const vector<double>& W0, const vector<double>& min_ratio0,
    double lambda, double scaling) {

    GreedyEngine engine = buildSingleRouteEngineWithOffsets(
        V, total_time_limit, route, Q_single, s0, c0, t0, dist, fixed_station_oper0, W0, min_ratio0,
        lambda, scaling, 0, 0, 0, 0, 0, 0);
    (void)engine.runFromCurrentState(1);
    return extractRouteProfileFromEngine(engine);
}

GreedyRouteProfile nGreedyLU_RA_route_profile_incremental(int V, double total_time_limit,
    const vector<int>& route, int Q_single,
    const vector<int>& s, const vector<int>& c, const vector<int>& t,
    const vector<vector<double>>& dist,
    const vector<int>& fixed_station_oper,
    const vector<double>& Wi, const vector<double>& min_ratio,
    double lambda, double scaling) {

    const int I_off = inferDepotOffset(s, V);
    const int C_off = inferDepotOffset(c, V);
    const int T_off = inferDepotOffset(t, V);
    const int fixed_off = inferDepotOffset(fixed_station_oper, V);
    const int W_off = inferDepotOffset(Wi, V);
    const int min_ratio_off = inferDepotOffset(min_ratio, V);

    GreedyEngine engine = buildSingleRouteEngineWithOffsets(
        V, total_time_limit, route, Q_single, s, c, t, dist, fixed_station_oper, Wi, min_ratio,
        lambda, scaling, I_off, C_off, T_off, fixed_off, W_off, min_ratio_off);
    (void)engine.runFromCurrentState(1);
    return extractRouteProfileFromEngine(engine);
}



namespace {

static GreedyEngine buildMultiRouteEngineWithOffsets(
    int V, int M, double total_time_limit,
    const vector<vector<int>>& routes, const vector<int>& Q,
    const vector<vector<double>>& dist,
    const vector<int>& Y_Ii, const vector<int>& Y_Ri, const vector<int>& Ci,
    const vector<double>& Wi, const vector<double>& min_ratio,
    double lambda, double scaling,
    int I_off, int T_off, int C_off, int W_off, int min_ratio_off) {

    GreedyEngine engine;
    engine.V = V;
    engine.M = M;
    engine.total_time_limit = total_time_limit;
    engine.lambda = (lambda >= 0.0) ? lambda : get_greedy_objective_lambda();
    engine.scaling = (scaling > 0.0) ? scaling : get_greedy_objective_scaling();
    engine.max_accept_moves = 0;
    engine.I_src = &Y_Ii;
    engine.T_src = &Y_Ri;
    engine.C_src = &Ci;
    engine.W_src = &Wi;
    engine.min_ratio_src = &min_ratio;
    engine.I_off = I_off;
    engine.T_off = T_off;
    engine.C_off = C_off;
    engine.W_off = W_off;
    engine.min_ratio_off = min_ratio_off;
    engine.buildPenaltyTable();
    engine.buildRoutes(routes, Q, dist);
    return engine;
}

static vector<vector<int>> extractCompactedActiveRoutes(const GreedyEngine& engine, bool& had_zero_op_prefix) {
    vector<vector<int>> compacted(engine.M);
    had_zero_op_prefix = false;
    for (int r = 0; r < engine.M; ++r) {
        const RouteInfo& rt = engine.routes[r];
        for (int p = 0; p < (int)rt.visits.size(); ++p) {
            int node1 = rt.visits[p] + 1;
            if (rt.visit_oper[p] != 0) compacted[r].push_back(node1);
            else had_zero_op_prefix = true;
        }
    }
    return compacted;
}

static void warmStartCompactedEngine(GreedyEngine& compact_engine, const GreedyEngine& base_engine) {
    compact_engine.station_oper.assign(compact_engine.V, 0);
    compact_engine.final_inv.assign(compact_engine.V, 0);
    compact_engine.desired_final.resize(compact_engine.V);
    for (int i = 0; i < compact_engine.V; ++i) {
        compact_engine.desired_final[i] = min(compact_engine.CVal(i), max(0, compact_engine.TVal(i)));
    }

    for (int r = 0; r < compact_engine.M; ++r) {
        RouteInfo& crt = compact_engine.routes[r];
        const RouteInfo& brt = base_engine.routes[r];
        crt.pickups_used = 0;
        std::fill(crt.visit_oper.begin(), crt.visit_oper.end(), 0);
        int idx = 0;
        for (int p = 0; p < (int)brt.visits.size(); ++p) {
            int op = brt.visit_oper[p];
            if (op == 0) continue;
            if (idx >= (int)crt.visit_oper.size()) break;
            crt.visit_oper[idx] = op;
            compact_engine.station_oper[crt.visits[idx]] += op;
            crt.pickups_used += GreedyEngine::positivePart(op);
            ++idx;
        }
        rebuildRouteLoadTree(crt);
    }

    for (int i = 0; i < compact_engine.V; ++i) {
        compact_engine.final_inv[i] = compact_engine.IVal(i) - compact_engine.station_oper[i];
    }
    compact_engine.rebuildObjectiveState();
    compact_engine.invalidateSearchCaches();
}

static inline SolutionResult_ORO negatedResult(SolutionResult_ORO res) {
    res.objective_value = -res.objective_value;
    return res;
}

} // namespace

SolutionResult_ORO nGreedyLU_RA_compact_full(int IterNum, int V, int M, double total_time_limit, const vector<vector<int>>& routes,
    const vector<int>& Q, const vector<int>& s, const vector<int>& c, const vector<int>& t,
    const vector<vector<double>>& dist, const int& max_iter, const double& r_avg_start,
    const vector<double>& Wi, const vector<double>& min_ratio, double lambda, double scaling,
    GreedyCompactionInfo* info) {

    (void)IterNum;
    (void)max_iter;
    (void)r_avg_start;
    const int I_off = inferDepotOffset(s, V);
    const int T_off = inferDepotOffset(t, V);
    const int C_off = inferDepotOffset(c, V);
    const int W_off = inferDepotOffset(Wi, V);
    const int min_ratio_off = inferDepotOffset(min_ratio, V);

    GreedyEngine base_engine = buildMultiRouteEngineWithOffsets(
        V, M, total_time_limit, routes, Q, dist, s, t, c, Wi, min_ratio,
        lambda, scaling, I_off, T_off, C_off, W_off, min_ratio_off);
    SolutionResult_ORO first_raw = base_engine.runOneMode(0, 1);
    SolutionResult_ORO first_out = negatedResult(first_raw);

    bool had_zero = false;
    vector<vector<int>> compacted_routes = extractCompactedActiveRoutes(base_engine, had_zero);

    if (info) {
        info->had_zero_op_prefix = had_zero;
        info->compacted_routes = compacted_routes;
        info->first_pass_result = first_out;
        info->rerun_result = SolutionResult_ORO{};
    }

    if (!had_zero) return first_out;

    GreedyEngine rerun_engine = buildMultiRouteEngineWithOffsets(
        V, M, total_time_limit, compacted_routes, Q, dist, s, t, c, Wi, min_ratio,
        lambda, scaling, I_off, T_off, C_off, W_off, min_ratio_off);
    SolutionResult_ORO rerun_raw = rerun_engine.runOneMode(0, 1);
    SolutionResult_ORO rerun_out = negatedResult(rerun_raw);
    if (info) info->rerun_result = rerun_out;
    return (rerun_out.objective_value > first_out.objective_value) ? rerun_out : first_out;
}

SolutionResult_ORO nGreedyLU_RA_compact_incremental(int IterNum, int V, int M, double total_time_limit, const vector<vector<int>>& routes,
    const vector<int>& Q, const vector<int>& s, const vector<int>& c, const vector<int>& t,
    const vector<vector<double>>& dist, const int& max_iter, const double& r_avg_start,
    const vector<double>& Wi, const vector<double>& min_ratio, double lambda, double scaling,
    GreedyCompactionInfo* info) {

    (void)IterNum;
    (void)max_iter;
    (void)r_avg_start;
    const int I_off = inferDepotOffset(s, V);
    const int T_off = inferDepotOffset(t, V);
    const int C_off = inferDepotOffset(c, V);
    const int W_off = inferDepotOffset(Wi, V);
    const int min_ratio_off = inferDepotOffset(min_ratio, V);

    GreedyEngine base_engine = buildMultiRouteEngineWithOffsets(
        V, M, total_time_limit, routes, Q, dist, s, t, c, Wi, min_ratio,
        lambda, scaling, I_off, T_off, C_off, W_off, min_ratio_off);
    SolutionResult_ORO first_raw = base_engine.runOneMode(0, 1);
    SolutionResult_ORO first_out = negatedResult(first_raw);

    bool had_zero = false;
    vector<vector<int>> compacted_routes = extractCompactedActiveRoutes(base_engine, had_zero);

    if (info) {
        info->had_zero_op_prefix = had_zero;
        info->compacted_routes = compacted_routes;
        info->first_pass_result = first_out;
        info->rerun_result = SolutionResult_ORO{};
    }

    if (!had_zero) return first_out;

    GreedyEngine rerun_engine = buildMultiRouteEngineWithOffsets(
        V, M, total_time_limit, compacted_routes, Q, dist, s, t, c, Wi, min_ratio,
        lambda, scaling, I_off, T_off, C_off, W_off, min_ratio_off);
    warmStartCompactedEngine(rerun_engine, base_engine);
    SolutionResult_ORO rerun_raw = rerun_engine.runFromCurrentState(1);
    SolutionResult_ORO rerun_out = negatedResult(rerun_raw);
    if (info) info->rerun_result = rerun_out;
    return (rerun_out.objective_value > first_out.objective_value) ? rerun_out : first_out;
}

#ifdef UNIFIED_GREEDY_EXAMPLE_MAIN
int main() {
    return 0;
}
#endif
