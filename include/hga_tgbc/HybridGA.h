#pragma once
#include <vector>
#include <random>
#include <deque>
#include <iostream>
#include <algorithm>
#include <numeric>
#include <chrono>
#include <unordered_map>
#include <limits>
#include <sstream>
#include <string>

#if __has_include("GreedyMethods.h")
#include "GreedyMethods.h"
#else
#include "../GreedyMethods.h"
#endif
#if __has_include("Solvers.h")
#include "Solvers.h"
#else
#include "../Solvers.h"
#endif
#if __has_include("InstanceData.h")
#include "InstanceData.h"
#else
#include "../InstanceData.h"
#endif

using namespace std;
using namespace chrono;

template <typename T = void>
class HybridGA_HGS {
public:
    enum class SelectionStyle {
        HGSBiased,
        HGAFitness
    };

    HybridGA_HGS(const InstanceData& inst,
        int ps = 24,
        double cr = 0.85,
        double crossover_mix_ratio = 0.65,
        double mr = 0.30,
        int mt = 60,
        int elite = 4,
        int li = 10,
        int in = 10,
        double lambda = 0.05,
        double scaling = 1.0,
        int no_improve_limit = 2000)
        : instance(inst), pop_size(max(4, ps)), crossover_rate(cr), mutation_rate(mr),
          max_time(mt), elite_size(max(1, elite)), log_interval(max(1, li)),
          g_iternum(in), objective_lambda(lambda), objective_scaling(scaling),
          no_improve_gen_limit(max(0, no_improve_limit)),
          inheritance_crossover_ratio(min(1.0, max(0.0, crossover_mix_ratio))) {
        random_device rd; gen.seed(rd());
        best_fitness = -numeric_limits<double>::infinity();
    }

    void set_seed(unsigned int seed) { gen.seed(seed); }
    void set_diversity_weight(double v) { if (v >= 0.0) diversity_weight = v; }
    void set_education_probability(double v) { if (v >= 0.0 && v <= 1.0) education_probability = v; }
    void set_education_trials(int v) { education_trials = std::max(0, v); }
    void set_tournament_size(int v) { tournament_size = std::max(2, v); }
    void set_constructive_noise(double v) { if (v >= 0.0) constructive_noise = v; }
    void set_constructive_mode(int v) { if (v >= 0 && v <= 2) constructive_mode = v; }
    void set_constructive_count(int v) { constructive_count = v; }
    void set_constructive_rcl_size(int v) { if (v >= 1) constructive_rcl_size = v; }
    void set_enable_tail_cross_route(bool v) { enable_tail_cross_route = v; }
    void set_selection_style(SelectionStyle style) { selection_style = style; }
    void set_use_hga_selection(bool enabled) {
        selection_style = enabled ? SelectionStyle::HGAFitness : SelectionStyle::HGSBiased;
    }
    void set_crossover_mix_ratio(double v) {
        if (v >= 0.0 && v <= 1.0) inheritance_crossover_ratio = v;
    }
    void set_decoder_compaction_mode(int v) { if (v >= 0 && v <= 3) { decoder_compaction_mode = v; decode_cache.clear(); } }
    void set_decode_cache_max_entries(size_t v) {
        decode_cache_max_entries = v;
        if (decode_cache_max_entries != std::numeric_limits<size_t>::max() &&
            decode_cache.size() > decode_cache_max_entries) {
            decode_cache.clear();
        }
    }
    void clear_decode_cache() { decode_cache.clear(); }
    vector<vector<int>> get_best_solution() const { return best_solution; }
    double get_best_fitness() const { return best_fitness; }
    void print_results() const {
        cout << "Best fitness: " << best_fitness << "\n";
        for (size_t r = 0; r < best_solution.size(); ++r) {
            cout << "Route " << r + 1 << ": 0 -> ";
            for (int n : best_solution[r]) cout << n << " -> ";
            cout << "0\n";
        }
    }

    void run() {
        auto start = high_resolution_clock::now();
        set_greedy_time_units(instance.load_time_unit, instance.unload_time_unit);
        set_greedy_objective_params(objective_lambda, objective_scaling);

        vector<Individual> population = initialize_population();
        evaluate_population(population);
        if (selection_style == SelectionStyle::HGSBiased) {
            update_diversity_and_biased(population);
        }
        update_best(population);
        int generation = 0;
        int generations_without_improve = 0;

        while (duration_cast<seconds>(high_resolution_clock::now() - start).count() < max_time) {
            vector<Individual> offspring;
            offspring.reserve(pop_size);
            while ((int)offspring.size() < pop_size) {
                const Individual& p1 = tournament_select(population);
                const Individual& p2 = tournament_select(population);
                Individual child;
                if (uni01() < crossover_rate) {
                    if (uni01() < inheritance_crossover_ratio) child.routes = route_inheritance_crossover(p1.routes, p2.routes);
                    else child.routes = ordered_sep_crossover(p1.routes, p2.routes);
                } else {
                    child.routes = (p1.fitness >= p2.fitness ? p1.routes : p2.routes);
                }
                mutate(child.routes);
                sanitize_routes(child.routes);
                child.chrom = routes_to_chromosome(child.routes);
                decode_individual(child);
                if (education_probability > 0.0 && uni01() < education_probability) {
                    educate(child);
                }
                offspring.push_back(std::move(child));
            }

            vector<Individual> pool = population;
            pool.insert(pool.end(), offspring.begin(), offspring.end());
            deduplicate_keep_best(pool);
            if (selection_style == SelectionStyle::HGSBiased) {
                update_diversity_and_biased(pool);
            }
            population = select_survivors(pool);
            const bool improved = update_best(population);
            if (improved) generations_without_improve = 0;
            else ++generations_without_improve;
            history.push_back(best_fitness);
            ++generation;
            if (generation % log_interval == 0) {
                // Production ExactEBRP bridge keeps the original HGA state update
                // but suppresses console tracing.
            }
            if (no_improve_gen_limit > 0 && generations_without_improve >= no_improve_gen_limit) break;
            //if (generation >= 30000) break;
        }
    }

private:
    struct Individual {
        vector<vector<int>> routes;
        vector<int> chrom;
        double fitness = -numeric_limits<double>::infinity();
        double diversity = 0.0;
        double biased = numeric_limits<double>::infinity();
        vector<int> decoded_ops;
    };

    struct RouteWindow {
        int exec_len = 0;
        int first_drop_pos = -1;
        int last_pick_pos = -1;
    };

    struct GuidedCandidate {
        vector<vector<int>> routes;
        double approx_fitness = -numeric_limits<double>::infinity();
        int route_a = -1;
        int route_b = -1;
        int node = -1;
    };

    InstanceData instance;
    int pop_size;
    double crossover_rate;
    double mutation_rate;
    int max_time;
    int elite_size;
    int log_interval;
    int g_iternum;
    double objective_lambda;
    double objective_scaling;
    int no_improve_gen_limit;
    double inheritance_crossover_ratio = 0.65;
    SelectionStyle selection_style = SelectionStyle::HGAFitness;
    double diversity_weight = 0.20;
    double education_probability = 0.10;
    int education_trials = 5;
    int tournament_size = 3;
    int neighbor_diversity_k = 5;
    double constructive_noise = 0.20;
    int constructive_mode = 0; // 0=random only, 1=legacy priority+detour, 2=objective-aware GRASP
    int constructive_count = -1;
    int constructive_rcl_size = 4;
    bool enable_tail_cross_route = false;
    int decoder_compaction_mode = 1; // 0=legacy, 1=full compact rerun, 2=incremental compact rerun, 3=target-greedy budget truncation
    size_t decode_cache_max_entries = std::numeric_limits<size_t>::max();

    vector<vector<int>> best_solution;
    double best_fitness;
    vector<double> history;
    mt19937 gen;
    unordered_map<string, SolutionResult_ORO> decode_cache;

    static constexpr int SEP = 0;

    double uni01() { return uniform_real_distribution<double>(0.0, 1.0)(gen); }

    string chromosome_key(const vector<int>& chrom) const {
        string key;
        key.reserve(chrom.size() * 4);
        for (int x : chrom) {
            key += to_string(x);
            key.push_back(',');
        }
        return key;
    }

    string phenotype_key_from_routes(const vector<vector<int>>& routes) const {
        string key;
        key.reserve(instance.V * 4 + instance.M);
        for (int r = 0; r < instance.M; ++r) {
            key.push_back('|');
            if (r >= (int)routes.size()) continue;
            int exec = executed_prefix_length(routes[r]);
            for (int i = 0; i < exec; ++i) {
                key += to_string(routes[r][i]);
                key.push_back(',');
            }
        }
        return key;
    }

    vector<int> routes_to_chromosome(const vector<vector<int>>& routes) const {
        vector<int> chrom;
        chrom.reserve(instance.V + instance.M - 1);
        for (int r = 0; r < instance.M; ++r) {
            if (r < (int)routes.size()) chrom.insert(chrom.end(), routes[r].begin(), routes[r].end());
            if (r + 1 < instance.M) chrom.push_back(SEP);
        }
        return chrom;
    }

    vector<vector<int>> chromosome_to_routes(const vector<int>& chrom) const {
        vector<vector<int>> routes; routes.reserve(instance.M);
        vector<int> cur;
        for (int g : chrom) {
            if (g == SEP) { routes.push_back(cur); cur.clear(); }
            else cur.push_back(g);
        }
        routes.push_back(cur);
        while ((int)routes.size() < instance.M) routes.emplace_back();
        if ((int)routes.size() > instance.M) routes.resize(instance.M);
        return routes;
    }



    int routing_prefix_length(const vector<int>& route) const {
        if (instance.total_time_limit <= 0.0) return (int)route.size();
        double travel = 0.0;
        int prev = 0;
        int exec = 0;
        for (int node : route) {
            double cand = travel + instance.dist[prev][node] + instance.dist[node][0];
            if (cand > instance.total_time_limit + 1e-12) break;
            travel += instance.dist[prev][node];
            prev = node;
            ++exec;
        }
        return exec;
    }

    int predict_cut_target_greedy(const vector<int>& route, int route_q, const vector<int>* fixed_ops = nullptr) const {
        const int hi = routing_prefix_length(route);
        if (hi <= 0) return 0;
        const double per_pick_cycle = instance.load_time_unit + instance.unload_time_unit;
        double travel = 0.0;
        int prev = 0;
        int load = 0;
        double est_time = 0.0;
        double cross_est = -1.0;
        int best = -1;
        for (int p = 0; p < hi; ++p) {
            int node = route[p];
            travel += instance.dist[prev][node];
            double closed = travel + instance.dist[node][0];
            double rem_time = instance.total_time_limit - closed;
            int residual = instance.s[node] - instance.Target[node];
            if (fixed_ops) residual -= (*fixed_ops)[node];
            int local_service = 0;
            if (residual > 0) {
                int x = std::min(residual, route_q - load);
                if (x > 0) {
                    load += x;
                    est_time += (double)x * per_pick_cycle;
                    local_service = x;
                }
            } else if (residual < 0) {
                int need = -residual;
                int y = std::min(need, load);
                if (y > 0) {
                    load -= y;
                    local_service = y;
                }
            }
            if (cross_est < 0.0 && est_time + 1e-12 >= rem_time) {
                cross_est = est_time;
                if (local_service > 0) best = p + 1;
            } else if (cross_est >= 0.0) {
                if (std::fabs(est_time - cross_est) <= 1e-12) {
                    if (local_service > 0) best = p + 1;
                } else {
                    break;
                }
            }
            prev = node;
        }
        if (cross_est < 0.0) return hi;
        if (best < 0) return hi;
        return best;
    }

    vector<vector<int>> truncate_routes_target_greedy(const vector<vector<int>>& routes) const {
        vector<vector<int>> out = routes;
        for (int r = 0; r < instance.M; ++r) {
            int cut = predict_cut_target_greedy(routes[r], instance.Q[r], nullptr);
            if (cut < (int)out[r].size()) out[r].resize(cut);
        }
        return out;
    }

    vector<int> ordered_crossover_sep_chrom(const vector<int>& p1, const vector<int>& p2) {
        const int V = instance.V;
        auto encode = [&](const vector<int>& p) {
            vector<int> u; u.reserve(p.size());
            int sep_idx = 0;
            for (int g : p) u.push_back(g == SEP ? V + (++sep_idx) : g);
            return u;
        };
        vector<int> u1 = encode(p1), u2 = encode(p2);
        int L = (int)u1.size();
        if (L == 0) return p1;
        uniform_int_distribution<int> dis(0, L - 1);
        int a = dis(gen), b = dis(gen); if (a > b) swap(a, b);
        vector<int> child_u(L, -1);
        vector<char> used(V + instance.M + 1, 0);
        for (int i = a; i <= b; ++i) { child_u[i] = u1[i]; used[u1[i]] = 1; }
        int idx = (b + 1) % L;
        for (int g : u2) {
            if (used[g]) continue;
            while (child_u[idx] != -1) idx = (idx + 1) % L;
            child_u[idx] = g;
            used[g] = 1;
        }
        vector<int> child; child.reserve(L);
        for (int g : child_u) child.push_back(g > V ? SEP : g);
        return child;
    }

    vector<vector<int>> ordered_sep_crossover(const vector<vector<int>>& parent1,
        const vector<vector<int>>& parent2) {
        auto c = ordered_crossover_sep_chrom(routes_to_chromosome(parent1), routes_to_chromosome(parent2));
        return chromosome_to_routes(c);
    }

    vector<vector<int>> route_inheritance_crossover(const vector<vector<int>>& parent1,
        const vector<vector<int>>& parent2) {
        vector<vector<int>> child = parent2;
        int copy_count = max(1, min(instance.M, (int)round(0.5 * instance.M)));
        vector<int> route_ids(instance.M); iota(route_ids.begin(), route_ids.end(), 0);
        shuffle(route_ids.begin(), route_ids.end(), gen);
        route_ids.resize(copy_count);
        vector<char> copied(instance.V + 1, 0);
        for (int r : route_ids) {
            for (int n : parent1[r]) copied[n] = 1;
        }
        for (auto& route : child) {
            route.erase(remove_if(route.begin(), route.end(), [&](int n) { return copied[n]; }), route.end());
        }
        for (int r : route_ids) child[r] = parent1[r];
        return child;
    }

    void sanitize_routes(vector<vector<int>>& routes) {
        vector<char> seen(instance.V + 1, 0);
        for (auto& route : routes) {
            vector<int> clean; clean.reserve(route.size());
            for (int n : route) {
                if (n < 1 || n > instance.V) continue;
                if (seen[n]) continue;
                seen[n] = 1;
                clean.push_back(n);
            }
            route.swap(clean);
        }
        vector<int> missing;
        for (int n = 1; n <= instance.V; ++n) if (!seen[n]) missing.push_back(n);
        shuffle(missing.begin(), missing.end(), gen);
        for (int node : missing) {
            int best_route = 0;
            double best_tail = numeric_limits<double>::infinity();
            for (int r = 0; r < instance.M; ++r) {
                int last = routes[r].empty() ? 0 : routes[r].back();
                double det = instance.dist[last][node] + instance.dist[node][0] - instance.dist[last][0];
                if (det < best_tail) { best_tail = det; best_route = r; }
            }
            routes[best_route].push_back(node);
        }
    }


SolutionResult_ORO decode_routes(const vector<vector<int>>& routes, vector<int>* chrom_ptr = nullptr) {
    (void)chrom_ptr;
    vector<vector<int>> truncated;
    const vector<vector<int>>* keyed_routes = &routes;
    if (decoder_compaction_mode == 3) {
        truncated = truncate_routes_target_greedy(routes);
        keyed_routes = &truncated;
    }
    string key = to_string(decoder_compaction_mode) + ":" + phenotype_key_from_routes(*keyed_routes);
    if (decode_cache_max_entries != 0) {
        auto it = decode_cache.find(key);
        if (it != decode_cache.end()) return it->second;
    }
    SolutionResult_ORO res;
    if (decoder_compaction_mode == 0) {
        res = nGreedyLU_RA(1, instance.V, instance.M, instance.total_time_limit,
            routes, instance.Q, instance.s, instance.c, instance.Target,
            instance.dist, g_iternum, -1.0, instance.weights, instance.min_ratio,
            objective_lambda, objective_scaling);
    } else if (decoder_compaction_mode == 1) {
        res = nGreedyLU_RA_compact_full(1, instance.V, instance.M, instance.total_time_limit,
            routes, instance.Q, instance.s, instance.c, instance.Target,
            instance.dist, g_iternum, -1.0, instance.weights, instance.min_ratio,
            objective_lambda, objective_scaling, nullptr);
    } else if (decoder_compaction_mode == 2) {
        res = nGreedyLU_RA_compact_incremental(1, instance.V, instance.M, instance.total_time_limit,
            routes, instance.Q, instance.s, instance.c, instance.Target,
            instance.dist, g_iternum, -1.0, instance.weights, instance.min_ratio,
            objective_lambda, objective_scaling, nullptr);
    } else {   /*
        res = nGreedyLU_RA(1, instance.V, instance.M, instance.total_time_limit,
            truncated, instance.Q, instance.s, instance.c, instance.Target,
            instance.dist, g_iternum, -1.0, instance.weights, instance.min_ratio,
            objective_lambda, objective_scaling);*/

        res = nGreedyLU_RA_compact_incremental(1, instance.V, instance.M, instance.total_time_limit,
            truncated, instance.Q, instance.s, instance.c, instance.Target,
            instance.dist, g_iternum, -1.0, instance.weights, instance.min_ratio,
            objective_lambda, objective_scaling, nullptr);
    }
    if (decode_cache_max_entries != 0) {
        if (decode_cache_max_entries != std::numeric_limits<size_t>::max() &&
            decode_cache.size() >= decode_cache_max_entries) {
            decode_cache.clear();
        }
        decode_cache.emplace(key, res);
    }
    return res;
}



public:
    double evaluate_routes(const vector<vector<int>>& routes, vector<int>* chrom_ptr = nullptr) {
        return decode_routes(routes, chrom_ptr).objective_value;
    }

private:
    void decode_individual(Individual& ind) {
        if (ind.chrom.empty()) ind.chrom = routes_to_chromosome(ind.routes);
        SolutionResult_ORO res = decode_routes(ind.routes, &ind.chrom);
        ind.fitness = res.objective_value;
        ind.decoded_ops = res.Y_Oper_best;
    }


    double objective_from_ops_offset(const vector<int>& ops_offset) const {
        vector<double> ratios(instance.V + 1, 1.0);
        double ratio_sum = 0.0;
        double penalty = 0.0;
        for (int node = 1; node <= instance.V; ++node) {
            double target = (instance.Target[node] > 0 ? (double)instance.Target[node] : 1.0);
            double final_inv = (double)instance.s[node] - (double)ops_offset[node];
            double ratio = final_inv / target;
            ratios[node] = ratio;
            ratio_sum += ratio;
            double w = instance.weights.empty() ? 1.0 : instance.weights[node];
            penalty += w * fabs(ratio - 1.0);
        }
        double pair_sum = 0.0;
        for (int i = 1; i <= instance.V; ++i) {
            for (int j = 1; j <= instance.V; ++j) {
                pair_sum += fabs(ratios[i] - ratios[j]);
            }
        }
        double gini = (ratio_sum > 1e-18) ? pair_sum / (2.0 * (double)instance.V * ratio_sum) : 0.0;
        return -(objective_scaling * (gini + objective_lambda * penalty));
    }

    vector<int> combine_route_ops_offset(const vector<vector<int>>& route_ops, int except_route = -1) const {
        vector<int> fixed(instance.V + 1, 0);
        for (int r = 0; r < (int)route_ops.size(); ++r) {
            if (r == except_route) continue;
            for (int node = 1; node <= instance.V; ++node) fixed[node] += route_ops[r][node - 1];
        }
        return fixed;
    }

    vector<vector<int>> build_constructive_individual_legacy() {
        vector<int> nodes(instance.V);
        iota(nodes.begin(), nodes.end(), 1);
        vector<double> priority(instance.V + 1, 0.0);
        for (int node : nodes) {
            double base = abs(instance.s[node] - instance.Target[node]) * (instance.weights.empty() ? 1.0 : instance.weights[node]);
            double noise = 1.0 + constructive_noise * (uni01() - 0.5);
            priority[node] = base * noise;
        }
        sort(nodes.begin(), nodes.end(), [&](int a, int b) {
            if (fabs(priority[a] - priority[b]) > 1e-12) return priority[a] > priority[b];
            return a < b;
        });
        vector<vector<int>> routes(instance.M);
        for (int node : nodes) {
            vector<pair<double, int>> cand;
            cand.reserve(instance.M);
            for (int r = 0; r < instance.M; ++r) {
                int last = routes[r].empty() ? 0 : routes[r].back();
                double det = instance.dist[last][node] + instance.dist[node][0] - instance.dist[last][0];
                cand.push_back({det, r});
            }
            sort(cand.begin(), cand.end());
            int choose = cand[min((int)cand.size() - 1, (int)floor(pow(uni01(), 1.5) * cand.size()))].second;
            routes[choose].push_back(node);
        }
        return routes;
    }

    vector<vector<int>> build_constructive_individual_objective() {
        struct Cand {
            int node = -1;
            int route = -1;
            double fit = -numeric_limits<double>::infinity();
            int exec = 0;
            vector<int> route_ops;
        };

        vector<vector<int>> routes(instance.M);
        vector<vector<int>> route_ops(instance.M, vector<int>(instance.V, 0));
        vector<int> remaining(instance.V);
        iota(remaining.begin(), remaining.end(), 1);
        double base_fit = objective_from_ops_offset(combine_route_ops_offset(route_ops));

        while (!remaining.empty()) {
            vector<Cand> cand_list;
            cand_list.reserve((int)remaining.size() * instance.M);
            bool any_prefix_extension = false;
            for (int node : remaining) {
                for (int r = 0; r < instance.M; ++r) {
                    vector<int> trial = routes[r];
                    trial.push_back(node);
                    vector<int> fixed = combine_route_ops_offset(route_ops, r);
                    auto res = nGreedyLU_RA_route_incremental(instance.V, instance.total_time_limit,
                        trial, instance.Q[r], instance.s, instance.c, instance.Target,
                        instance.dist, fixed, instance.weights, instance.min_ratio,
                        objective_lambda, objective_scaling);
                    Cand c;
                    c.node = node;
                    c.route = r;
                    c.fit = res.objective_value;
                    c.exec = executed_prefix_length(trial);
                    c.route_ops = std::move(res.Y_Oper_best);
                    if (c.exec > executed_prefix_length(routes[r])) any_prefix_extension = true;
                    cand_list.push_back(std::move(c));
                }
            }
            sort(cand_list.begin(), cand_list.end(), [](const Cand& a, const Cand& b) {
                if (fabs(a.fit - b.fit) > 1e-12) return a.fit > b.fit;
                return a.node < b.node;
            });
            if (cand_list.empty()) break;
            const Cand& best = cand_list.front();
            if (best.fit <= base_fit + 1e-12 && !any_prefix_extension) break;
            int rcl = min((int)cand_list.size(), max(1, constructive_rcl_size));
            int pick = uniform_int_distribution<int>(0, rcl - 1)(gen);
            const Cand chosen = cand_list[pick];
            routes[chosen.route].push_back(chosen.node);
            route_ops[chosen.route] = chosen.route_ops;
            base_fit = objective_from_ops_offset(combine_route_ops_offset(route_ops));
            remaining.erase(find(remaining.begin(), remaining.end(), chosen.node));
        }

        shuffle(remaining.begin(), remaining.end(), gen);
        for (int node : remaining) {
            int r = uniform_int_distribution<int>(0, instance.M - 1)(gen);
            routes[r].push_back(node);
        }
        return routes;
    }

    vector<vector<int>> build_constructive_individual() {
        if (constructive_mode == 1) return build_constructive_individual_legacy();
        if (constructive_mode == 2) return build_constructive_individual_objective();
        return chromosome_to_routes(make_random_chromosome());
    }

    vector<int> make_random_chromosome() {
        vector<int> chrom; chrom.reserve(instance.V + instance.M - 1);
        for (int i = 1; i <= instance.V; ++i) chrom.push_back(i);
        for (int i = 0; i < instance.M - 1; ++i) chrom.push_back(SEP);
        shuffle(chrom.begin(), chrom.end(), gen);
        return chrom;
    }

    vector<Individual> initialize_population() {
        vector<Individual> pop; pop.reserve(pop_size);
        int cc = constructive_count;
        if (cc < 0) cc = (constructive_mode == 0 ? 0 : max(2, pop_size / 5));
        cc = min(pop_size, max(0, cc));
        for (int i = 0; i < pop_size; ++i) {
            Individual ind;
            if (i < cc) ind.routes = build_constructive_individual();
            else ind.routes = chromosome_to_routes(make_random_chromosome());
            ind.chrom = routes_to_chromosome(ind.routes);
            pop.push_back(std::move(ind));
        }
        return pop;
    }

    void evaluate_population(vector<Individual>& pop) {
        for (auto& ind : pop) decode_individual(ind);
    }

    vector<pair<int,int>> pred_succ_signature(const vector<vector<int>>& routes) const {
        vector<pair<int,int>> sig(instance.V + 1, {0,0});
        for (const auto& route : routes) {
            for (int i = 0; i < (int)route.size(); ++i) {
                int node = route[i];
                int pred = (i == 0) ? 0 : route[i - 1];
                int succ = (i + 1 == (int)route.size()) ? 0 : route[i + 1];
                sig[node] = {pred, succ};
            }
        }
        return sig;
    }

    double distance_between(const vector<pair<int,int>>& a, const vector<pair<int,int>>& b) const {
        int shared = 0;
        for (int i = 1; i <= instance.V; ++i) {
            shared += (a[i].first == b[i].first);
            shared += (a[i].second == b[i].second);
        }
        return 1.0 - (double)shared / (2.0 * instance.V);
    }

    void update_diversity_and_biased(vector<Individual>& pop) {
        int n = (int)pop.size();
        vector<vector<pair<int,int>>> sigs(n);
        for (int i = 0; i < n; ++i) sigs[i] = pred_succ_signature(pop[i].routes);
        vector<vector<double>> dmat(n, vector<double>(n, 0.0));
        for (int i = 0; i < n; ++i) for (int j = i + 1; j < n; ++j) {
            dmat[i][j] = dmat[j][i] = distance_between(sigs[i], sigs[j]);
        }
        for (int i = 0; i < n; ++i) {
            vector<double> ds; ds.reserve(n - 1);
            for (int j = 0; j < n; ++j) if (i != j) ds.push_back(dmat[i][j]);
            sort(ds.begin(), ds.end());
            int k = min((int)ds.size(), max(1, neighbor_diversity_k));
            double avg = 0.0; for (int t = 0; t < k; ++t) avg += ds[t];
            pop[i].diversity = (k > 0 ? avg / k : 0.0);
        }
        vector<int> cost_rank(n), div_rank(n);
        vector<int> ids(n); iota(ids.begin(), ids.end(), 0);
        sort(ids.begin(), ids.end(), [&](int a, int b){ return pop[a].fitness > pop[b].fitness; });
        for (int r = 0; r < n; ++r) cost_rank[ids[r]] = r;
        sort(ids.begin(), ids.end(), [&](int a, int b){ return pop[a].diversity > pop[b].diversity; });
        for (int r = 0; r < n; ++r) div_rank[ids[r]] = r;
        for (int i = 0; i < n; ++i) pop[i].biased = (double)cost_rank[i] + diversity_weight * (double)div_rank[i];
    }

    const Individual& tournament_select(const vector<Individual>& pop) {
        uniform_int_distribution<int> dis(0, (int)pop.size() - 1);
        int best = dis(gen);
        for (int k = 1; k < tournament_size; ++k) {
            int cand = dis(gen);
            if (selection_style == SelectionStyle::HGAFitness) {
                if (pop[cand].fitness > pop[best].fitness + 1e-12) best = cand;
            } else {
                if (pop[cand].biased < pop[best].biased - 1e-12) best = cand;
                else if (fabs(pop[cand].biased - pop[best].biased) <= 1e-12 && pop[cand].fitness > pop[best].fitness) best = cand;
            }
        }
        return pop[best];
    }

    void mutate(vector<vector<int>>& routes) {
        if (uni01() >= mutation_rate) return;
        int ops = 1 + (uni01() < 0.25);
        for (int it = 0; it < ops; ++it) {
            int op = uniform_int_distribution<int>(0, 2)(gen);
            if (op == 0) {
                vector<int> cand;
                for (int r = 0; r < instance.M; ++r) if ((int)routes[r].size() >= 2) cand.push_back(r);
                if (cand.empty()) continue;
                int rid = cand[uniform_int_distribution<int>(0, (int)cand.size() - 1)(gen)];
                int i = uniform_int_distribution<int>(0, (int)routes[rid].size() - 2)(gen);
                int j = uniform_int_distribution<int>(i + 1, (int)routes[rid].size() - 1)(gen);
                reverse(routes[rid].begin() + i, routes[rid].begin() + j + 1);
            } else if (op == 1) {
                vector<int> srcs;
                for (int r = 0; r < instance.M; ++r) if (!routes[r].empty()) srcs.push_back(r);
                if (srcs.empty()) continue;
                int ra = srcs[uniform_int_distribution<int>(0, (int)srcs.size() - 1)(gen)];
                int rb = uniform_int_distribution<int>(0, instance.M - 1)(gen);
                int pa = uniform_int_distribution<int>(0, (int)routes[ra].size() - 1)(gen);
                int node = routes[ra][pa];
                routes[ra].erase(routes[ra].begin() + pa);
                int pb = routes[rb].empty() ? 0 : uniform_int_distribution<int>(0, (int)routes[rb].size())(gen);
                routes[rb].insert(routes[rb].begin() + pb, node);
            } else {
                vector<int> srcs;
                for (int r = 0; r < instance.M; ++r) if (!routes[r].empty()) srcs.push_back(r);
                if (srcs.empty()) continue;
                int ra = srcs[uniform_int_distribution<int>(0, (int)srcs.size() - 1)(gen)];
                int rb = srcs[uniform_int_distribution<int>(0, (int)srcs.size() - 1)(gen)];
                int pa = uniform_int_distribution<int>(0, (int)routes[ra].size() - 1)(gen);
                int pb = uniform_int_distribution<int>(0, (int)routes[rb].size() - 1)(gen);
                if (ra == rb && pa == pb) continue;
                swap(routes[ra][pa], routes[rb][pb]);
            }
        }
    }

    int executed_prefix_length(const vector<int>& route) const {
        if (instance.total_time_limit <= 0.0) return (int)route.size();
        double travel = 0.0;
        int prev = 0;
        int exec = 0;
        for (int node : route) {
            double cand = travel + instance.dist[prev][node] + instance.dist[node][0];
            if (cand > instance.total_time_limit + 1e-12) break;
            travel += instance.dist[prev][node];
            prev = node;
            ++exec;
        }
        return exec;
    }

    RouteWindow build_route_window(const vector<int>& route, const vector<int>& ops) const {
        RouteWindow ctx;
        ctx.exec_len = executed_prefix_length(route);
        for (int p = 0; p < ctx.exec_len; ++p) {
            int op = ops[route[p] - 1];
            if (op > 0) ctx.last_pick_pos = p;
            else if (op < 0 && ctx.first_drop_pos == -1) ctx.first_drop_pos = p;
        }
        return ctx;
    }

    int final_inventory_for_node(int node, const vector<int>& ops) const {
        return instance.s[node] - ops[node - 1];
    }

    int node_gap_after_decode(int node, const vector<int>& ops) const {
        return instance.Target[node] - final_inventory_for_node(node, ops);
    }

    int classify_node_role(int node, const vector<int>& ops) const {
        int op = ops[node - 1];
        if (op > 0) return +1;   // pickup / supply
        if (op < 0) return -1;   // drop / demand
        int gap = node_gap_after_decode(node, ops);
        if (gap > 0) return -1;  // still short, treat as demand
        if (gap < 0) return +1;  // still excess, treat as supply
        return 0;
    }

    static void erase_at(vector<int>& route, int pos) {
        route.erase(route.begin() + pos);
    }

    static void insert_at(vector<int>& route, int pos, int node) {
        pos = max(0, min(pos, (int)route.size()));
        route.insert(route.begin() + pos, node);
    }

    vector<vector<int>> relocate_node(const vector<vector<int>>& base_routes,
        int from_route, int from_pos, int to_route, int to_pos) const {
        vector<vector<int>> out = base_routes;
        int node = out[from_route][from_pos];
        erase_at(out[from_route], from_pos);
        if (from_route == to_route && to_pos > from_pos) --to_pos;
        insert_at(out[to_route], to_pos, node);
        return out;
    }

    vector<int> build_fixed_ops_excluding(const vector<vector<int>>& routes, const vector<int>& ops, int excl_a, int excl_b = -1) const {
        vector<int> fixed(instance.V + 1, 0);
        for (int r = 0; r < instance.M; ++r) {
            if (r == excl_a || r == excl_b) continue;
            for (int node : routes[r]) fixed[node] = ops[node - 1];
        }
        return fixed;
    }


    int route_pickup_budget(const vector<int>& route) const {
        if (route.empty()) return 0;
        double travel = 0.0;
        int prev = 0;
        for (int node : route) {
            travel += instance.dist[prev][node];
            prev = node;
        }
        travel += instance.dist[prev][0];
        const double per_pick_cycle = instance.load_time_unit + instance.unload_time_unit;
        if (per_pick_cycle <= 1e-12) return std::numeric_limits<int>::max() / 4;
        return max(0, (int)std::floor((instance.total_time_limit - travel + 1e-12) / per_pick_cycle));
    }

    vector<int> estimate_route_ops_inherited(const vector<int>& raw_route, int route_id,
        const vector<int>& fixed_ops, const vector<int>& base_ops) const {
        vector<int> out(instance.V + 1, 0);
        vector<int> eval_route = raw_route;
        if (decoder_compaction_mode == 3) {
            int cut = predict_cut_target_greedy(raw_route, instance.Q[route_id], &fixed_ops);
            if (cut < (int)eval_route.size()) eval_route.resize(cut);
        } else {
            int exec = executed_prefix_length(raw_route);
            if (exec < (int)eval_route.size()) eval_route.resize(exec);
        }
        if (eval_route.empty()) return out;

        const int q = instance.Q[route_id];
        const int pickup_budget = route_pickup_budget(eval_route);
        int load = 0;
        int pickups_used = 0;

        for (int node : eval_route) {
            int op = 0;
            int desired = base_ops[node - 1];

            if (desired > 0) {
                int station_room = instance.s[node] - max(0, op);
                int x = min(min(desired, station_room), min(q - load, pickup_budget - pickups_used));
                if (x > 0) {
                    op += x;
                    load += x;
                    pickups_used += x;
                }
            } else if (desired < 0) {
                int station_room = instance.c[node] - instance.s[node] - max(0, -op);
                int y = min(min(-desired, station_room), load);
                if (y > 0) {
                    op -= y;
                    load -= y;
                }
            }

            int final_after = instance.s[node] - fixed_ops[node] - op;
            if (op >= 0 && final_after > instance.Target[node]) {
                int extra_need = final_after - instance.Target[node];
                int station_room = instance.s[node] - max(0, op);
                int extra = min(min(extra_need, station_room), min(q - load, pickup_budget - pickups_used));
                if (extra > 0) {
                    op += extra;
                    load += extra;
                    pickups_used += extra;
                }
            } else if (op <= 0 && final_after < instance.Target[node]) {
                int extra_need = instance.Target[node] - final_after;
                int station_room = instance.c[node] - instance.s[node] - max(0, -op);
                int extra = min(min(extra_need, station_room), load);
                if (extra > 0) {
                    op -= extra;
                    load -= extra;
                }
            }

            out[node] = op;
        }
        return out;
    }

    double approx_eval_single_route(const vector<vector<int>>& base_routes, int route_id,
        const vector<int>& new_route, const vector<int>& base_ops) {
        vector<int> fixed = build_fixed_ops_excluding(base_routes, base_ops, route_id);
        if (decoder_compaction_mode == 3) {
            vector<int> est = estimate_route_ops_inherited(new_route, route_id, fixed, base_ops);
            vector<int> total = fixed;
            for (int node = 1; node <= instance.V; ++node) total[node] += est[node];
            return objective_from_ops_offset(total);
        }
        vector<int> eval_route = new_route;
        auto res = nGreedyLU_RA_route_incremental(instance.V, instance.total_time_limit,
            eval_route, instance.Q[route_id], instance.s, instance.c, instance.Target,
            instance.dist, fixed, instance.weights, instance.min_ratio,
            objective_lambda, objective_scaling);
        return res.objective_value;
    }

    double approx_eval_two_routes_ordered(const vector<vector<int>>& base_routes,
        int route_a, const vector<int>& new_a,
        int route_b, const vector<int>& new_b,
        const vector<int>& base_ops) {
        vector<int> fixed = build_fixed_ops_excluding(base_routes, base_ops, route_a, route_b);
        if (decoder_compaction_mode == 3) {
            vector<int> est_a = estimate_route_ops_inherited(new_a, route_a, fixed, base_ops);
            vector<int> fixed_ab = fixed;
            for (int node = 1; node <= instance.V; ++node) fixed_ab[node] += est_a[node];
            vector<int> est_b = estimate_route_ops_inherited(new_b, route_b, fixed_ab, base_ops);
            vector<int> total = fixed_ab;
            for (int node = 1; node <= instance.V; ++node) total[node] += est_b[node];
            return objective_from_ops_offset(total);
        }
        vector<int> eval_a = new_a;
        auto res_a = nGreedyLU_RA_route_incremental(instance.V, instance.total_time_limit,
            eval_a, instance.Q[route_a], instance.s, instance.c, instance.Target,
            instance.dist, fixed, instance.weights, instance.min_ratio,
            objective_lambda, objective_scaling);
        vector<int> fixed_ab = fixed;
        for (int node : eval_a) fixed_ab[node] = res_a.Y_Oper_best[node - 1];
        vector<int> eval_b = new_b;
        auto res_b = nGreedyLU_RA_route_incremental(instance.V, instance.total_time_limit,
            eval_b, instance.Q[route_b], instance.s, instance.c, instance.Target,
            instance.dist, fixed_ab, instance.weights, instance.min_ratio,
            objective_lambda, objective_scaling);
        return res_b.objective_value;
    }

    double approx_eval_two_routes(const vector<vector<int>>& base_routes,
        int route_a, const vector<int>& new_a,
        int route_b, const vector<int>& new_b,
        const vector<int>& base_ops) {
        double ab = approx_eval_two_routes_ordered(base_routes, route_a, new_a, route_b, new_b, base_ops);
        double ba = approx_eval_two_routes_ordered(base_routes, route_b, new_b, route_a, new_a, base_ops);
        return max(ab, ba);
    }

    int anchor_supply_position(const RouteWindow& ctx) const {
        return (ctx.first_drop_pos != -1) ? ctx.first_drop_pos : 0;
    }

    int anchor_demand_position(const RouteWindow& ctx, const vector<int>& route) const {
        if (ctx.last_pick_pos != -1) return ctx.last_pick_pos + 1;
        return min(ctx.exec_len, (int)route.size());
    }

    void collect_key_positions(const vector<int>& route, const RouteWindow& ctx, const vector<int>& ops,
        vector<int>& positions_out) const {
        positions_out.clear();
        vector<char> chosen(route.size(), 0);
        for (int p = 0; p < ctx.exec_len; ++p) {
            int node = route[p];
            int role = classify_node_role(node, ops);
            if (role == 0) continue;
            chosen[p] = 1;
            positions_out.push_back(p);
        }
        int tail_supply = -1, tail_demand = -1;
        for (int p = ctx.exec_len; p < (int)route.size(); ++p) {
            int node = route[p];
            int role = classify_node_role(node, ops);
            if (role > 0 && tail_supply == -1) tail_supply = p;
            if (role < 0 && tail_demand == -1) tail_demand = p;
            if (tail_supply != -1 && tail_demand != -1) break;
        }
        if (tail_supply != -1) positions_out.push_back(tail_supply);
        if (tail_demand != -1) positions_out.push_back(tail_demand);
    }

    void try_add_same_route_candidate(const vector<vector<int>>& base_routes,
        int route_id, int from_pos, int to_pos,
        const vector<int>& base_ops, vector<GuidedCandidate>& out) {
        if (from_pos < 0 || from_pos >= (int)base_routes[route_id].size()) return;
        if (to_pos < 0) to_pos = 0;
        if (to_pos > (int)base_routes[route_id].size()) to_pos = (int)base_routes[route_id].size();
        vector<vector<int>> cand_routes = relocate_node(base_routes, route_id, from_pos, route_id, to_pos);
        if (cand_routes[route_id] == base_routes[route_id]) return;
        GuidedCandidate cand;
        cand.routes = std::move(cand_routes);
        cand.approx_fitness = approx_eval_single_route(base_routes, route_id, cand.routes[route_id], base_ops);
        cand.route_a = route_id;
        cand.node = base_routes[route_id][from_pos];
        out.push_back(std::move(cand));
    }

    void try_add_zero_prefix_tail_candidate(const vector<vector<int>>& base_routes,
        int route_id, const vector<int>& base_ops, vector<GuidedCandidate>& out) {
        const vector<int>& route = base_routes[route_id];
        if (route.empty()) return;

        int exec = executed_prefix_length(route);
        int last_zero_pos = -1;
        for (int p = 0; p < exec; ++p) {
            int node = route[p];
            if (base_ops[node - 1] == 0) last_zero_pos = p;
        }
        if (last_zero_pos == -1) return;

        vector<vector<int>> cand_routes =
            relocate_node(base_routes, route_id, last_zero_pos, route_id, (int)route.size());

        if (cand_routes[route_id] == route) return;

        GuidedCandidate cand;
        cand.routes = std::move(cand_routes);
        cand.approx_fitness =
            approx_eval_single_route(base_routes, route_id, cand.routes[route_id], base_ops);
        cand.route_a = route_id;
        cand.node = route[last_zero_pos];
        out.push_back(std::move(cand));
    }

    void try_add_cross_route_candidate(const vector<vector<int>>& base_routes,
        int from_route, int from_pos, int to_route, int to_pos,
        const vector<int>& base_ops, vector<GuidedCandidate>& out) {
        if (from_route == to_route) return;
        if (from_pos < 0 || from_pos >= (int)base_routes[from_route].size()) return;
        vector<vector<int>> cand_routes = relocate_node(base_routes, from_route, from_pos, to_route, to_pos);
        GuidedCandidate cand;
        cand.routes = std::move(cand_routes);
        cand.approx_fitness = approx_eval_two_routes(base_routes,
            from_route, cand.routes[from_route], to_route, cand.routes[to_route], base_ops);
        cand.route_a = from_route;
        cand.route_b = to_route;
        cand.node = base_routes[from_route][from_pos];
        out.push_back(std::move(cand));
    }

    vector<GuidedCandidate> build_guided_candidates(const Individual& ind) {
        vector<GuidedCandidate> out;
        vector<RouteWindow> windows(instance.M);
        for (int r = 0; r < instance.M; ++r) windows[r] = build_route_window(ind.routes[r], ind.decoded_ops);

        for (int r = 0; r < instance.M; ++r) {
            const vector<int>& route = ind.routes[r];
            if (route.empty()) continue;
            const RouteWindow& ctx = windows[r];
            try_add_zero_prefix_tail_candidate(ind.routes, r, ind.decoded_ops, out);
            vector<int> key_positions;
            collect_key_positions(route, ctx, ind.decoded_ops, key_positions);
            for (int pos : key_positions) {
                int node = route[pos];
                int role = classify_node_role(node, ind.decoded_ops);
                if (role > 0) {
                    if (ctx.first_drop_pos != -1 && pos > ctx.first_drop_pos) {
                        try_add_same_route_candidate(ind.routes, r, pos, anchor_supply_position(ctx), ind.decoded_ops, out);
                    }
                    if (pos >= ctx.exec_len) {
                        try_add_same_route_candidate(ind.routes, r, pos, anchor_supply_position(ctx), ind.decoded_ops, out);
                    }
                } else if (role < 0) {
                    if (ctx.last_pick_pos != -1 && pos < ctx.last_pick_pos) {
                        try_add_same_route_candidate(ind.routes, r, pos, anchor_demand_position(ctx, route), ind.decoded_ops, out);
                    }
                    if (pos >= ctx.exec_len && ctx.last_pick_pos != -1) {
                        try_add_same_route_candidate(ind.routes, r, pos, anchor_demand_position(ctx, route), ind.decoded_ops, out);
                    }
                }
            }
        }

        if (enable_tail_cross_route) {
            vector<RouteWindow> windows(instance.M);
            for (int r = 0; r < instance.M; ++r) windows[r] = build_route_window(ind.routes[r], ind.decoded_ops);
            for (int src = 0; src < instance.M; ++src) {
                int tail_supply = -1, tail_demand = -1;
                for (int p = windows[src].exec_len; p < (int)ind.routes[src].size(); ++p) {
                    int role = classify_node_role(ind.routes[src][p], ind.decoded_ops);
                    if (role > 0 && tail_supply == -1) tail_supply = p;
                    if (role < 0 && tail_demand == -1) tail_demand = p;
                    if (tail_supply != -1 && tail_demand != -1) break;
                }
                for (int dst = 0; dst < instance.M; ++dst) {
                    if (dst == src) continue;
                    if (tail_supply != -1) {
                        bool dst_has_demand = false;
                        for (int node : ind.routes[dst]) if (classify_node_role(node, ind.decoded_ops) < 0) { dst_has_demand = true; break; }
                        if (dst_has_demand) {
                            try_add_cross_route_candidate(ind.routes, src, tail_supply, dst, anchor_supply_position(windows[dst]), ind.decoded_ops, out);
                        }
                    }
                    if (tail_demand != -1 && windows[dst].last_pick_pos != -1) {
                        try_add_cross_route_candidate(ind.routes, src, tail_demand, dst, anchor_demand_position(windows[dst], ind.routes[dst]), ind.decoded_ops, out);
                    }
                }
            }
        }

        sort(out.begin(), out.end(), [](const GuidedCandidate& a, const GuidedCandidate& b) {
            return a.approx_fitness > b.approx_fitness;
        });
        return out;
    }

    bool improve_once_guided(Individual& ind) {
        if (ind.chrom.empty()) ind.chrom = routes_to_chromosome(ind.routes);
        if (ind.decoded_ops.empty() || !isfinite(ind.fitness)) decode_individual(ind);
        vector<GuidedCandidate> candidates = build_guided_candidates(ind);
        for (const GuidedCandidate& cand : candidates) {
            if (cand.approx_fitness <= ind.fitness + 1e-12) break;
            vector<int> chrom = routes_to_chromosome(cand.routes);
            SolutionResult_ORO dec = decode_routes(cand.routes, &chrom);
            if (dec.objective_value > ind.fitness + 1e-12) {
                ind.routes = cand.routes;
                ind.chrom = std::move(chrom);
                ind.fitness = dec.objective_value;
                ind.decoded_ops = dec.Y_Oper_best;
                return true;
            }
        }
        return false;
    }

    void educate(Individual& ind) {
        if (education_trials <= 0) return;
        for (int rep = 0; rep < max(1, education_trials); ++rep) {
            bool improved = false;
            while (improve_once_guided(ind)) improved = true;
            if (!improved) break;
        }
    }

    void deduplicate_keep_best(vector<Individual>& pop) {
        unordered_map<string, int> best_idx;
        vector<Individual> out;
        out.reserve(pop.size());
        for (auto& ind : pop) {
            if (ind.chrom.empty()) ind.chrom = routes_to_chromosome(ind.routes);
            string key = chromosome_key(ind.chrom);
            auto it = best_idx.find(key);
            if (it == best_idx.end()) {
                best_idx.emplace(key, (int)out.size());
                out.push_back(std::move(ind));
            } else if (ind.fitness > out[it->second].fitness + 1e-12) {
                out[it->second] = std::move(ind);
            }
        }
        pop.swap(out);
    }

    vector<Individual> select_survivors(vector<Individual>& pool) {
        vector<Individual> next;
        next.reserve(pop_size);
        vector<int> ids(pool.size()); iota(ids.begin(), ids.end(), 0);
        if (selection_style == SelectionStyle::HGAFitness) {
            sort(ids.begin(), ids.end(), [&](int a, int b) {
                return pool[a].fitness > pool[b].fitness;
            });
            for (int id : ids) {
                if ((int)next.size() >= pop_size) break;
                next.push_back(pool[id]);
            }
            return next;
        }

        sort(ids.begin(), ids.end(), [&](int a, int b){ return pool[a].fitness > pool[b].fitness; });
        vector<char> taken(pool.size(), 0);
        for (int i = 0; i < min((int)pool.size(), elite_size); ++i) {
            next.push_back(pool[ids[i]]);
            taken[ids[i]] = 1;
        }
        sort(ids.begin(), ids.end(), [&](int a, int b){
            if (fabs(pool[a].biased - pool[b].biased) > 1e-12) return pool[a].biased < pool[b].biased;
            return pool[a].fitness > pool[b].fitness;
        });
        for (int id : ids) {
            if ((int)next.size() >= pop_size) break;
            if (taken[id]) continue;
            next.push_back(pool[id]);
            taken[id] = 1;
        }
        return next;
    }

    bool update_best(const vector<Individual>& pop) {
        bool improved = false;
        for (const auto& ind : pop) {
            if (ind.fitness > best_fitness + 1e-12) {
                best_fitness = ind.fitness;
                best_solution = ind.routes;
                improved = true;
            }
        }
        return improved;
    }
};

template <typename T = void>
class HybridGA : public HybridGA_HGS<T> {
public:
    using HybridGA_HGS<T>::HybridGA_HGS;

    HybridGA(const InstanceData& inst,
        int ps,
        double cr,
        double crossover_mix_ratio,
        double mr,
        int mt,
        int tabu_tenure,
        int TABU_Max_Gens,
        int TABU_Neighbors,
        int li,
        int lu_model,
        int method,
        int in,
        double best,
        int no_improve_limit = 2000)
        : HybridGA_HGS<T>(inst, ps, cr, crossover_mix_ratio, mr, mt, 4, li, in, 0.05, 1.0, no_improve_limit) {
        (void)tabu_tenure;
        (void)TABU_Max_Gens;
        (void)TABU_Neighbors;
        (void)lu_model;
        (void)method;
        (void)best;
    }
};
