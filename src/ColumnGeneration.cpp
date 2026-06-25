#include "ColumnGeneration.hpp"

#include "Branching.hpp"
#include "Bounds.hpp"
#include "ColumnPool.hpp"
#include "Cuts.hpp"
#include "Evaluator.hpp"
#include "Pricing.hpp"
#include "Result.hpp"

#include <array>
#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <deque>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <limits>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <thread>
#include <unordered_map>
#include <unordered_set>
#include <utility>

namespace ebrp {
namespace {

using Clock = std::chrono::steady_clock;

std::string lowerPricingString(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(),
                   [](unsigned char c) {
                       return static_cast<char>(std::tolower(c));
                   });
    return value;
}

template <typename ResultLike>
void initializeBpcPricingFields(ResultLike& result,
                                const PricingOptions& options) {
    result.bpc_pricing_engine_requested = lowerPricingString(options.pricing_engine);
    if (result.bpc_pricing_engine_requested.empty() ||
        result.bpc_pricing_engine_requested == "auto") {
        result.bpc_pricing_engine_requested = "exact-label";
    }
    result.bpc_pricing_engine_used = result.bpc_pricing_engine_requested;
    result.ng_size = options.ng_size;
    result.ng_neighborhood_mode = options.ng_neighborhood_mode;
    result.cg_stabilization_mode = lowerPricingString(options.cg_dual_stabilization);
    if (result.cg_stabilization_mode.empty()) result.cg_stabilization_mode = "none";
    result.column_tracks = lowerPricingString(options.column_tracks);
    if (result.column_tracks.empty() || result.column_tracks == "auto") {
        result.column_tracks = "elementary-only";
    }
    result.rmp_column_space = lowerPricingString(options.rmp_column_space);
    if (result.rmp_column_space.empty() || result.rmp_column_space == "auto") {
        result.rmp_column_space =
            result.column_tracks == "two-track" ? "two-track" : "elementary";
    }
    result.relaxed_rmp_enabled = options.relaxed_columns_in_rmp ||
        result.column_tracks == "two-track" ||
        result.rmp_column_space == "ng-relaxed" ||
        result.rmp_column_space == "two-track";
}

template <typename ResultLike>
void accumulateBpcPricingStats(ResultLike& result,
                               const PricingResult& priced,
                               bool closure_relevant_call = true) {
    std::string used = lowerPricingString(priced.pricing_engine);
    if (used.empty()) used = "exact-label";
    result.bpc_pricing_engine_used = used;
    if (!result.bpc_pricing_engine_requested.empty() &&
        result.bpc_pricing_engine_requested != "auto" &&
        result.bpc_pricing_engine_requested != used) {
        ++result.bpc_pricing_engine_fallbacks;
    }
    if (used == "ng-dssr") ++result.bpc_nodes_using_ng_dssr;
    else if (used == "hybrid") ++result.bpc_nodes_using_hybrid;
    else ++result.bpc_nodes_using_exact_label;
    if (priced.complete && closure_relevant_call) ++result.bpc_nodes_exactly_priced;
    if ((used == "ng-dssr" || used == "hybrid") &&
        !priced.dssr_exact_closure_proved && !priced.complete) {
        ++result.bpc_nodes_dssr_incomplete;
    }
    if (priced.dssr_final_exact) {
        ++result.bpc_nodes_final_verifier_called;
        if (priced.dssr_exact_closure_proved || priced.complete) {
            ++result.bpc_nodes_final_verifier_completed;
        }
    }
    result.ng_size = std::max(result.ng_size, priced.ng_size);
    if (!priced.ng_neighborhood_mode.empty()) {
        result.ng_neighborhood_mode = priced.ng_neighborhood_mode;
    }
    result.ng_memory_total += priced.ng_memory_total;
    result.dssr_memory_total_initial += priced.dssr_memory_total_initial;
    result.dssr_memory_total_final += priced.dssr_memory_total_final;
    result.dssr_rounds += priced.dssr_rounds;
    result.dssr_memory_expansions += priced.dssr_memory_expansions;
    result.dssr_repeated_station_events += priced.dssr_repeated_station_events;
    result.dssr_relaxed_negative_routes += priced.dssr_relaxed_negative_routes;
    result.dssr_non_elementary_routes += priced.dssr_non_elementary_routes;
    result.dssr_elementary_columns_found += priced.dssr_elementary_columns_found;
    result.dssr_no_negative_relaxed_route =
        result.dssr_no_negative_relaxed_route || priced.dssr_no_negative_relaxed_route;
    result.dssr_exact_closure_proved =
        result.dssr_exact_closure_proved || priced.dssr_exact_closure_proved;
    result.dssr_final_exact_verification_time +=
        priced.dssr_final_exact_verification_time;
    result.dssr_time_seconds += priced.dssr_time_seconds;
    if (!priced.dssr_stop_reason.empty()) {
        if (!result.dssr_stop_reason.empty()) result.dssr_stop_reason += "; ";
        result.dssr_stop_reason += priced.dssr_stop_reason;
    }
    result.cg_stabilized_pricing_calls += priced.cg_stabilized_pricing_calls;
    result.cg_true_pricing_calls += priced.cg_true_pricing_calls;
    result.cg_stabilization_columns_found += priced.cg_stabilization_columns_found;
    result.cg_true_pricing_columns_found += priced.cg_true_pricing_columns_found;
    result.cg_dual_center_updates += priced.cg_dual_center_updates;
    result.cg_dual_oscillation_metric =
        std::max(result.cg_dual_oscillation_metric,
                 priced.cg_dual_oscillation_metric);
    result.cg_true_negative_columns_inserted +=
        priced.cg_true_negative_columns_inserted;
    result.cg_stabilization_false_negatives +=
        priced.cg_stabilization_false_negatives;
    result.cg_stabilization_time_seconds += priced.cg_stabilization_time_seconds;
    result.cg_final_true_pricing_rc = priced.cg_final_true_pricing_rc;
    if (!priced.column_tracks.empty()) result.column_tracks = priced.column_tracks;
    if (!priced.rmp_column_space.empty()) result.rmp_column_space = priced.rmp_column_space;
    result.elementary_columns_generated += priced.elementary_columns_generated;
    result.relaxed_columns_generated += priced.relaxed_columns_generated;
    result.relaxed_columns_rejected_projection +=
        priced.relaxed_columns_rejected_projection;
    result.relaxed_columns_rejected_infeasible_projection +=
        priced.relaxed_columns_rejected_infeasible_projection;
    result.relaxed_columns_used_in_lb_rmp += priced.relaxed_columns_used_in_lb_rmp;
    result.relaxed_columns_used_in_incumbent += priced.relaxed_columns_used_in_incumbent;
    result.non_elementary_relaxed_routes_seen +=
        priced.non_elementary_relaxed_routes_seen;
    result.non_elementary_relaxed_columns_validated +=
        priced.non_elementary_relaxed_columns_validated;
    result.non_elementary_relaxed_columns_inserted +=
        priced.non_elementary_relaxed_columns_inserted;
    result.non_elementary_relaxed_columns_rejected +=
        priced.non_elementary_relaxed_columns_rejected;
    result.relaxed_projection_rejected_load += priced.relaxed_projection_rejected_load;
    result.relaxed_projection_rejected_station_capacity +=
        priced.relaxed_projection_rejected_station_capacity;
    result.relaxed_projection_rejected_branch += priced.relaxed_projection_rejected_branch;
    result.relaxed_projection_rejected_operation_mode +=
        priced.relaxed_projection_rejected_operation_mode;
    result.relaxed_projection_rejected_unsafe_cut +=
        priced.relaxed_projection_rejected_unsafe_cut;
    result.relaxed_projection_validation_time_seconds +=
        priced.relaxed_projection_validation_time_seconds;
    result.relaxed_columns_blocked_from_incumbent +=
        priced.relaxed_columns_blocked_from_incumbent;
    result.relaxed_columns_blocked_from_export +=
        priced.relaxed_columns_blocked_from_export;
    result.relaxed_columns_blocked_from_candidate_reconstruction +=
        priced.relaxed_columns_blocked_from_candidate_reconstruction;
    result.relaxed_rmp_enabled = result.relaxed_rmp_enabled || priced.relaxed_rmp_enabled;
    result.elementary_pricing_closed =
        result.elementary_pricing_closed || priced.elementary_pricing_closed;
    result.ng_relaxed_pricing_closed =
        result.ng_relaxed_pricing_closed || priced.ng_relaxed_pricing_closed;
    result.dssr_exact_elementary_closed =
        result.dssr_exact_elementary_closed || priced.dssr_exact_elementary_closed;
    result.ng_relaxed_best_reduced_cost =
        std::min(result.ng_relaxed_best_reduced_cost,
                 priced.ng_relaxed_best_reduced_cost);
    result.ng_relaxed_negative_routes_found +=
        priced.ng_relaxed_negative_routes_found;
    result.ng_relaxed_negative_columns_inserted +=
        priced.ng_relaxed_negative_columns_inserted;
    result.ng_relaxed_negative_routes_rejected +=
        priced.ng_relaxed_negative_routes_rejected;
    result.ng_relaxed_closure_labels_processed +=
        priced.ng_relaxed_closure_labels_processed;
    result.ng_relaxed_closure_labels_pruned +=
        priced.ng_relaxed_closure_labels_pruned;
    result.ng_relaxed_closure_time_seconds +=
        priced.ng_relaxed_closure_time_seconds;
    if (!priced.ng_relaxed_closure_stop_reason.empty()) {
        result.ng_relaxed_closure_stop_reason =
            priced.ng_relaxed_closure_stop_reason;
    }
    result.ng_relaxed_pricing_calls += priced.ng_relaxed_pricing_calls;
    result.ng_relaxed_labels_processed += priced.ng_relaxed_labels_processed;
    result.ng_relaxed_labels_pruned += priced.ng_relaxed_labels_pruned;
    result.dssr_refinement_rounds_for_lb += priced.dssr_refinement_rounds_for_lb;
    result.dssr_lb_before_refinement =
        std::max(result.dssr_lb_before_refinement,
                 priced.dssr_lb_before_refinement);
    result.dssr_lb_after_refinement =
        std::max(result.dssr_lb_after_refinement,
                 priced.dssr_lb_after_refinement);
    result.label_dominance_comparisons += priced.label_dominance_comparisons;
    result.label_dominance_pruned_labels += priced.label_dominance_pruned_labels;
    result.label_dominance_cross_pickup_pruned_labels +=
        priced.label_dominance_cross_pickup_pruned_labels;
    result.label_dominance_inactive_entries_skipped +=
        priced.label_dominance_inactive_entries_skipped;
    result.label_dominance_bucket_compactions +=
        priced.label_dominance_bucket_compactions;
    result.label_dominance_compacted_entries +=
        priced.label_dominance_compacted_entries;
    result.operation_dp_dominance_pruned_states +=
        priced.operation_dp_dominance_pruned_states;
}

struct LpSolve {
    bool ok = false;
    std::string status;
    double objective = 0.0;
    std::unordered_map<std::string, double> variables;
    std::unordered_map<std::string, double> duals;
    std::filesystem::path lp_path;
    std::filesystem::path sol_path;
    std::filesystem::path log_path;
};

struct GiniCapBranchRestriction {
    std::vector<std::pair<int, int>> forbid_together_pairs;
    std::vector<std::pair<int, int>> require_together_pairs;
    std::vector<int> forbid_stations;
    std::vector<int> require_stations;
    std::vector<int> inventory_lower;
    std::vector<int> inventory_upper;
    std::vector<int> forbid_pickup_stations;
    std::vector<int> forbid_drop_stations;
};

std::string num(double value) {
    std::ostringstream out;
    out << std::setprecision(12) << value;
    return out.str();
}

std::string jsonEscapeCg(const std::string& value) {
    std::ostringstream out;
    for (unsigned char ch : value) {
        switch (ch) {
        case '"': out << "\\\""; break;
        case '\\': out << "\\\\"; break;
        case '\b': out << "\\b"; break;
        case '\f': out << "\\f"; break;
        case '\n': out << "\\n"; break;
        case '\r': out << "\\r"; break;
        case '\t': out << "\\t"; break;
        default:
            if (ch < 0x20) {
                out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
                    << static_cast<int>(ch) << std::dec << std::setfill(' ');
            } else {
                out << static_cast<char>(ch);
            }
        }
    }
    return out.str();
}

std::string jsonNumberCg(double value) {
    if (!std::isfinite(value)) return "null";
    return num(value);
}

std::string quote(const std::filesystem::path& p) {
    return "\"" + p.string() + "\"";
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

std::string zName(int vehicle, int idx) {
    return "z_" + std::to_string(vehicle) + "_" + std::to_string(idx);
}

std::string coverName(int station) {
    return "cover_" + std::to_string(station);
}

std::string vehicleName(int vehicle) {
    return "vehicle_" + std::to_string(vehicle);
}

std::string gcapVisitName(int station) {
    return "visit_" + std::to_string(station);
}

std::string gcapInventoryName(int station) {
    return "inventory_" + std::to_string(station);
}

std::string yName(int station) {
    return "y_" + std::to_string(station);
}

std::string rName(int station) {
    return "r_" + std::to_string(station);
}

std::string eName(int station) {
    return "e_" + std::to_string(station);
}

std::string hName(int first, int second) {
    return "h_" + std::to_string(first) + "_" + std::to_string(second);
}

std::string sName() {
    return "S_total";
}

std::string hTotalName() {
    return "H_total";
}

std::string gLowerName() {
    return "g_lb";
}

std::string invArtPlusName(int station) {
    return "art_inv_plus_" + std::to_string(station);
}

std::string invArtMinusName(int station) {
    return "art_inv_minus_" + std::to_string(station);
}

std::string giniArtName() {
    return "art_gini_cap";
}

std::string giniFloorArtName() {
    return "art_gini_floor";
}

std::string subsetRowCutName(int idx) {
    return "sri3_" + std::to_string(idx);
}

void parseLpSolution(const std::filesystem::path& sol_path, LpSolve& out) {
    std::ifstream in(sol_path);
    if (!in) throw std::runtime_error("CPLEX LP solution file missing: " + sol_path.string());
    std::ostringstream ss;
    ss << in.rdbuf();
    const std::string text = ss.str();

    std::smatch m;
    if (std::regex_search(text, m, std::regex("solutionStatusString=\"([^\"]*)\""))) {
        out.status = m[1].str();
    }
    if (std::regex_search(text, m, std::regex("objectiveValue=\"([^\"]*)\""))) {
        out.objective = std::stod(m[1].str());
    }

    const std::regex var_re("<variable [^>]*name=\"([^\"]+)\"[^>]*value=\"([^\"]+)\"");
    for (auto it = std::sregex_iterator(text.begin(), text.end(), var_re);
         it != std::sregex_iterator(); ++it) {
        out.variables[it->str(1)] = std::stod(it->str(2));
    }

    const std::regex con_re("<constraint [^>]*name=\"([^\"]+)\"[^>]*dual=\"([^\"]+)\"");
    for (auto it = std::sregex_iterator(text.begin(), text.end(), con_re);
         it != std::sregex_iterator(); ++it) {
        out.duals[it->str(1)] = std::stod(it->str(2));
    }
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

double ratioSumUpperBound(const Instance& instance,
                          const GiniCapBranchRestriction& branch,
                          double penalty_budget = std::numeric_limits<double>::infinity()) {
    int total_bikes = 0;
    for (int station = 1; station <= instance.V; ++station) {
        total_bikes += instance.initial[station];
    }

    auto branchLower = [&](int station) {
        int lower = 0;
        if (station < static_cast<int>(branch.inventory_lower.size())) {
            lower = std::max(lower, branch.inventory_lower[station]);
        }
        return lower;
    };
    auto branchUpper = [&](int station) {
        int upper = instance.capacity[station];
        if (station < static_cast<int>(branch.inventory_upper.size())) {
            upper = std::min(upper, branch.inventory_upper[station]);
        }
        return upper;
    };
    auto greedyConservationBound = [&]() {
        int remaining_bikes = total_bikes;
        struct RatioSlot {
            double ratio_per_bike = 0.0;
            int capacity = 0;
        };
        std::vector<RatioSlot> slots;
        slots.reserve(instance.V);
        for (int station = 1; station <= instance.V; ++station) {
            if (instance.target[station] <= 0) continue;
            slots.push_back(RatioSlot{
                1.0 / static_cast<double>(instance.target[station]),
                std::max(0, branchUpper(station))
            });
        }
        std::sort(slots.begin(), slots.end(), [](const RatioSlot& a, const RatioSlot& b) {
            return a.ratio_per_bike > b.ratio_per_bike;
        });
        double s_max = 0.0;
        for (const RatioSlot& slot : slots) {
            if (remaining_bikes <= 0) break;
            const int take = std::min(remaining_bikes, slot.capacity);
            s_max += static_cast<double>(take) * slot.ratio_per_bike;
            remaining_bikes -= take;
        }
        return std::max(s_max, 1e-9);
    };

    if (!std::isfinite(penalty_budget)) return greedyConservationBound();
    if (penalty_budget < -1e-9) return 1e-9;
    if (total_bikes > 2000) return greedyConservationBound();

    std::vector<std::vector<std::pair<double, double>>> states(total_bikes + 1);
    states[0].push_back({0.0, 0.0});
    const double eps = 1e-9;
    for (int station = 1; station <= instance.V; ++station) {
        const int lower = branchLower(station);
        const int upper = branchUpper(station);
        if (lower > upper) return 1e-9;
        std::vector<std::vector<std::pair<double, double>>> next(total_bikes + 1);
        for (int used = 0; used <= total_bikes; ++used) {
            if (states[used].empty()) continue;
            const int max_y = std::min(upper, total_bikes - used);
            for (const auto& state : states[used]) {
                for (int y = lower; y <= max_y; ++y) {
                    const double ratio = (instance.target[station] > 0)
                        ? static_cast<double>(y) / static_cast<double>(instance.target[station])
                        : 0.0;
                    const double p = state.first
                        + instance.weights[station] * std::fabs(ratio - 1.0);
                    if (p > penalty_budget + eps) continue;
                    next[used + y].push_back({p, state.second + ratio});
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
    for (const auto& bucket : states) {
        for (const auto& state : bucket) {
            if (state.first <= penalty_budget + eps) {
                best = std::max(best, state.second);
            }
        }
    }
    if (!std::isfinite(best)) return 1e-9;
    return std::max(best, 1e-9);
}

double dualValue(const LpSolve& lp, const std::string& name) {
    auto it = lp.duals.find(name);
    return (it == lp.duals.end()) ? 0.0 : it->second;
}

double variableValue(const LpSolve& lp, const std::string& name) {
    auto it = lp.variables.find(name);
    return (it == lp.variables.end()) ? 0.0 : it->second;
}

double phaseArtificialValue(const Instance& instance, const LpSolve& lp) {
    double value = variableValue(lp, giniArtName());
    value += variableValue(lp, giniFloorArtName());
    for (int station = 1; station <= instance.V; ++station) {
        value += variableValue(lp, invArtPlusName(station));
        value += variableValue(lp, invArtMinusName(station));
    }
    return value;
}

std::string columnKey(int vehicle, const RouteLoadColumn& col) {
    std::ostringstream key;
    key << vehicle << "|";
    for (int node : col.path) key << node << ",";
    key << "|";
    for (int q : col.q) key << q << ",";
    return key.str();
}

bool hasColumn(const std::vector<RouteLoadColumn>& columns, const RouteLoadColumn& candidate) {
    const std::string cand = columnKey(candidate.vehicle, candidate);
    for (const RouteLoadColumn& col : columns) {
        if (columnKey(col.vehicle, col) == cand) return true;
    }
    return false;
}

int findColumnIndex(const std::vector<RouteLoadColumn>& columns, const RouteLoadColumn& candidate) {
    const std::string cand = columnKey(candidate.vehicle, candidate);
    for (int idx = 0; idx < static_cast<int>(columns.size()); ++idx) {
        if (columnKey(columns[idx].vehicle, columns[idx]) == cand) return idx;
    }
    return -1;
}

bool containsStation(int mask, int station) {
    return station > 0 && (mask & (1 << (station - 1)));
}

bool containsBoth(int mask, const std::pair<int, int>& pair) {
    return containsStation(mask, pair.first) && containsStation(mask, pair.second);
}

bool containsExactlyOne(int mask, const std::pair<int, int>& pair) {
    return containsStation(mask, pair.first) != containsStation(mask, pair.second);
}

int subsetRowCoefficient(int mask, const std::vector<int>& stations) {
    int count = 0;
    for (int station : stations) {
        if (containsStation(mask, station)) ++count;
    }
    return count / 2;
}

bool columnAllowedByBranch(const RouteLoadColumn& column,
                           const GiniCapBranchRestriction& branch) {
    for (int station : branch.forbid_stations) {
        if (containsStation(column.mask, station)) return false;
    }
    for (const auto& pair : branch.forbid_together_pairs) {
        if (containsBoth(column.mask, pair)) return false;
    }
    for (const auto& pair : branch.require_together_pairs) {
        if (containsExactlyOne(column.mask, pair)) return false;
    }
    for (int station : branch.forbid_pickup_stations) {
        if (station >= 1 && station < static_cast<int>(column.q.size()) &&
            column.q[station] > 0) return false;
    }
    for (int station : branch.forbid_drop_stations) {
        if (station >= 1 && station < static_cast<int>(column.q.size()) &&
            column.q[station] < 0) return false;
    }
    return true;
}

std::string requireTogetherName(int first, int second) {
    return "branch_req_" + std::to_string(first) + "_" + std::to_string(second);
}

std::string requireStationName(int station) {
    return "branch_visit_" + std::to_string(station);
}

bool oneStopPickupColumn(const Instance& instance,
                         int vehicle,
                         int station,
                         RouteLoadColumn& column) {
    if (vehicle < 0 || vehicle >= instance.M || station <= 0 || station > instance.V) return false;
    if (instance.initial[station] <= 0 || instance.Q[vehicle] <= 0) return false;
    const double travel = instance.dist[0][station] + instance.dist[station][0];
    const double cunit = instance.pickup_time + instance.drop_time;
    if (travel + cunit > instance.total_time_limit + 1e-9) return false;
    column = RouteLoadColumn{};
    column.vehicle = vehicle;
    column.mask = 1 << (station - 1);
    column.path = {station};
    column.q.assign(instance.V + 1, 0);
    column.q[station] = 1;
    column.pickup = 1;
    column.travel = travel;
    column.duration = travel + cunit;
    column.reduced_cost = column.duration;
    return true;
}

std::pair<int, int> chooseRequiredPair(const Instance& instance) {
    for (int i = 1; i <= instance.V; ++i) {
        for (int j = i + 1; j <= instance.V; ++j) {
            RouteLoadColumn ci, cj;
            if (oneStopPickupColumn(instance, 0, i, ci) &&
                oneStopPickupColumn(instance, 0, j, cj)) {
                return {i, j};
            }
        }
    }
    return {0, 0};
}

LpSolve solveCoverageLp(const Instance& instance,
                        const std::vector<std::vector<RouteLoadColumn>>& columns_by_vehicle,
                        int required_i,
                        int required_j,
                        double time_limit_seconds,
                        int iteration) {
    const auto run_id = std::chrono::high_resolution_clock::now()
        .time_since_epoch().count();
    const auto thread_id = std::hash<std::thread::id>{}(std::this_thread::get_id());
    const std::filesystem::path work_dir = std::filesystem::path("results") / "cg_work"
        / (std::filesystem::path(instance.name).stem().string() + "_"
           + std::to_string(run_id) + "_" + std::to_string(thread_id) + "_"
           + std::to_string(iteration));
    std::filesystem::create_directories(work_dir);

    LpSolve lp;
    lp.lp_path = work_dir / "master.lp";
    lp.sol_path = work_dir / "master.sol";
    lp.log_path = work_dir / "master.log";
    const std::filesystem::path cmd_path = work_dir / "run.cplex";

    std::ofstream out(lp.lp_path);
    if (!out) throw std::runtime_error("Cannot write column-generation LP: " + lp.lp_path.string());
    out << std::setprecision(12);
    out << "\\ Coverage column-generation diagnostic LP\n";
    out << "Minimize\n obj:";
    bool first = true;
    for (int k = 0; k < instance.M; ++k) {
        for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
            out << (first ? " " : " + ") << num(columns_by_vehicle[k][c].duration)
                << " " << zName(k, c);
            first = false;
        }
    }
    if (first) out << " 0";
    out << "\nSubject To\n";
    for (int station : {required_i, required_j}) {
        out << " " << coverName(station) << ":";
        first = true;
        for (int k = 0; k < instance.M; ++k) {
            for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
                if (columns_by_vehicle[k][c].mask & (1 << (station - 1))) {
                    out << (first ? " " : " + ") << zName(k, c);
                    first = false;
                }
            }
        }
        if (first) out << " 0";
        out << " >= 1\n";
    }
    for (int k = 0; k < instance.M; ++k) {
        out << " " << vehicleName(k) << ":";
        first = true;
        for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
            out << (first ? " " : " + ") << zName(k, c);
            first = false;
        }
        if (first) out << " 0";
        out << " <= 1\n";
    }
    out << "Bounds\n";
    for (int k = 0; k < instance.M; ++k) {
        for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
            out << " 0 <= " << zName(k, c) << " <= 1\n";
        }
    }
    out << "End\n";
    out.close();

    std::ofstream cmd(cmd_path);
    cmd << "set threads 1\n";
    cmd << "set timelimit " << time_limit_seconds << "\n";
    cmd << "read " << lp.lp_path.string() << "\n";
    cmd << "optimize\n";
    cmd << "write " << lp.sol_path.string() << "\n";
    cmd << "quit\n";
    cmd.close();

    const std::string command = "cmd /C \"" + quote(defaultCplexPath()) + " -f "
        + quote(cmd_path) + " > " + quote(lp.log_path) + " 2>&1\"";
    const int rc = std::system(command.c_str());
    if (rc != 0) {
        throw std::runtime_error("CPLEX LP command failed with return code " + std::to_string(rc));
    }
    if (!std::filesystem::exists(lp.sol_path) && logSaysInfeasible(lp.log_path)) {
        lp.status = "infeasible";
        lp.ok = false;
        return lp;
    }
    parseLpSolution(lp.sol_path, lp);
    lp.ok = statusIsOptimal(lp.status);
    return lp;
}

LpSolve solveGiniCapLp(const Instance& instance,
                       const std::vector<std::vector<RouteLoadColumn>>& columns_by_vehicle,
                       double lambda,
                       double gamma,
                       double gamma_floor,
                       double time_limit_seconds,
                       int iteration,
                       const GiniCapBranchRestriction& branch = GiniCapBranchRestriction{},
                       bool phase_one = false,
                       bool use_combined_gini_lower_bound = false,
                       const std::vector<SubsetRowCut>& active_cuts = {},
                       double objective_cutoff = std::numeric_limits<double>::infinity()) {
    const auto run_id = std::chrono::high_resolution_clock::now()
        .time_since_epoch().count();
    const auto thread_id = std::hash<std::thread::id>{}(std::this_thread::get_id());
    const std::filesystem::path work_dir = std::filesystem::path("results") / "gcap_work"
        / (std::filesystem::path(instance.name).stem().string() + "_"
           + std::to_string(run_id) + "_" + std::to_string(thread_id) + "_"
           + std::to_string(iteration));
    std::filesystem::create_directories(work_dir);

    LpSolve lp;
    lp.lp_path = work_dir / "master.lp";
    lp.sol_path = work_dir / "master.sol";
    lp.log_path = work_dir / "master.log";
    const std::filesystem::path cmd_path = work_dir / "run.cplex";

    std::ofstream out(lp.lp_path);
    if (!out) throw std::runtime_error("Cannot write fixed-Gini-cap LP: " + lp.lp_path.string());
    out << std::setprecision(12);
    auto writeTerm = [&](double coeff, const std::string& var, bool& first) {
        if (std::fabs(coeff) <= 1e-12) return;
        if (first) out << (coeff < 0.0 ? " - " : " ");
        else out << (coeff < 0.0 ? " - " : " + ");
        const double mag = std::fabs(coeff);
        if (std::fabs(mag - 1.0) > 1e-12) out << num(mag) << " ";
        out << var;
        first = false;
    };

    out << (phase_one
        ? "\\ EBRP fixed-Gini-cap phase-I restricted master LP\n"
        : "\\ EBRP fixed-Gini-cap restricted master LP\n");
    out << "Minimize\n obj:";
    bool first = true;
    const double floor_bound = std::max(0.0, gamma_floor);
    const double penalty_budget =
        (!phase_one && use_combined_gini_lower_bound &&
         std::isfinite(objective_cutoff) && lambda > 1e-12)
            ? (objective_cutoff - floor_bound) / lambda
            : std::numeric_limits<double>::infinity();
    const double s_upper = ratioSumUpperBound(instance, branch, penalty_budget);
    const double h_gini_coeff = 1.0 / (static_cast<double>(instance.V) * s_upper);
    if (phase_one) {
        for (int i = 1; i <= instance.V; ++i) {
            writeTerm(1.0, invArtPlusName(i), first);
            writeTerm(1.0, invArtMinusName(i), first);
        }
        writeTerm(1.0, giniArtName(), first);
        if (gamma_floor >= 0.0) writeTerm(1.0, giniFloorArtName(), first);
    } else {
        if (use_combined_gini_lower_bound) {
            writeTerm(1.0, gLowerName(), first);
        }
        for (int i = 1; i <= instance.V; ++i) {
            writeTerm(lambda * instance.weights[i], eName(i), first);
        }
    }
    if (first) out << " 0";
    out << "\nSubject To\n";

    for (int k = 0; k < instance.M; ++k) {
        bool has_vehicle_column = false;
        for (const auto& col : columns_by_vehicle[k]) {
            if (columnAllowedByBranch(col, branch)) {
                has_vehicle_column = true;
                break;
            }
        }
        if (!has_vehicle_column) continue;
        out << " " << vehicleName(k) << ":";
        first = true;
        for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
            if (!columnAllowedByBranch(columns_by_vehicle[k][c], branch)) continue;
            writeTerm(1.0, zName(k, c), first);
        }
        out << " <= 1\n";
    }

    for (int station = 1; station <= instance.V; ++station) {
        bool has_visit_column = false;
        for (int k = 0; k < instance.M; ++k) {
            for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
                if (!columnAllowedByBranch(columns_by_vehicle[k][c], branch)) continue;
                if (columns_by_vehicle[k][c].mask & (1 << (station - 1))) {
                    has_visit_column = true;
                }
            }
        }
        if (!has_visit_column) continue;
        out << " " << gcapVisitName(station) << ":";
        first = true;
        for (int k = 0; k < instance.M; ++k) {
            for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
                if (!columnAllowedByBranch(columns_by_vehicle[k][c], branch)) continue;
                if (columns_by_vehicle[k][c].mask & (1 << (station - 1))) {
                    writeTerm(1.0, zName(k, c), first);
                }
            }
        }
        out << " <= 1\n";
    }

    for (int station = 1; station <= instance.V; ++station) {
        out << " " << gcapInventoryName(station) << ":";
        first = true;
        writeTerm(1.0, yName(station), first);
        for (int k = 0; k < instance.M; ++k) {
            for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
                if (!columnAllowedByBranch(columns_by_vehicle[k][c], branch)) continue;
                const int q = (station < static_cast<int>(columns_by_vehicle[k][c].q.size()))
                    ? columns_by_vehicle[k][c].q[station] : 0;
                if (q != 0) writeTerm(static_cast<double>(q), zName(k, c), first);
            }
        }
        if (phase_one) {
            writeTerm(1.0, invArtPlusName(station), first);
            writeTerm(-1.0, invArtMinusName(station), first);
        }
        out << " = " << instance.initial[station] << "\n";
    }

    for (int station = 1; station <= instance.V; ++station) {
        out << " ratio_" << station << ":";
        first = true;
        writeTerm(1.0, yName(station), first);
        writeTerm(-static_cast<double>(instance.target[station]), rName(station), first);
        out << " = 0\n";

        out << " abs_hi_" << station << ":";
        first = true;
        writeTerm(1.0, rName(station), first);
        writeTerm(-1.0, eName(station), first);
        out << " <= 1\n";

        out << " abs_lo_" << station << ":";
        first = true;
        writeTerm(-1.0, rName(station), first);
        writeTerm(-1.0, eName(station), first);
        out << " <= -1\n";
    }

    for (int i = 1; i <= instance.V; ++i) {
        for (int j = i + 1; j <= instance.V; ++j) {
            out << " h_pos_" << i << "_" << j << ":";
            first = true;
            writeTerm(1.0, rName(i), first);
            writeTerm(-1.0, rName(j), first);
            writeTerm(-1.0, hName(i, j), first);
            out << " <= 0\n";

            out << " h_neg_" << i << "_" << j << ":";
            first = true;
            writeTerm(-1.0, rName(i), first);
            writeTerm(1.0, rName(j), first);
            writeTerm(-1.0, hName(i, j), first);
            out << " <= 0\n";
        }
    }

    out << " s_sum:";
    first = true;
    writeTerm(1.0, sName(), first);
    for (int station = 1; station <= instance.V; ++station) {
        writeTerm(-1.0, rName(station), first);
    }
    out << " = 0\n";

    out << " h_sum:";
    first = true;
    writeTerm(1.0, hTotalName(), first);
    for (int i = 1; i <= instance.V; ++i) {
        for (int j = i + 1; j <= instance.V; ++j) {
            writeTerm(-1.0, hName(i, j), first);
        }
    }
    out << " = 0\n";

    out << " gini_cap:";
    first = true;
    writeTerm(1.0, hTotalName(), first);
    writeTerm(-static_cast<double>(instance.V) * gamma, sName(), first);
    if (phase_one) writeTerm(-1.0, giniArtName(), first);
    out << " <= 0\n";

    if (gamma_floor >= 0.0) {
        out << " gini_floor:";
        first = true;
        writeTerm(1.0, hTotalName(), first);
        writeTerm(-static_cast<double>(instance.V) * gamma_floor, sName(), first);
        if (phase_one) writeTerm(1.0, giniFloorArtName(), first);
        out << " >= 0\n";
    }

    if (!phase_one && use_combined_gini_lower_bound) {
        out << " g_lb_floor:";
        first = true;
        writeTerm(1.0, gLowerName(), first);
        out << " >= " << std::max(0.0, gamma_floor) << "\n";

        out << " g_lb_hscaled:";
        first = true;
        writeTerm(1.0, gLowerName(), first);
        writeTerm(-h_gini_coeff, hTotalName(), first);
        out << " >= 0\n";
    }

    bool needs_branch_dummy = false;
    for (const auto& pair : branch.require_together_pairs) {
        out << " " << requireTogetherName(pair.first, pair.second) << ":";
        first = true;
        for (int k = 0; k < instance.M; ++k) {
            for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
                if (!columnAllowedByBranch(columns_by_vehicle[k][c], branch)) continue;
                if (containsBoth(columns_by_vehicle[k][c].mask, pair)) {
                    writeTerm(1.0, zName(k, c), first);
                }
            }
        }
        if (first) {
            writeTerm(1.0, "branch_infeas_dummy", first);
            needs_branch_dummy = true;
        }
        out << " = 1\n";
    }
    for (int station : branch.require_stations) {
        out << " " << requireStationName(station) << ":";
        first = true;
        for (int k = 0; k < instance.M; ++k) {
            for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
                if (!columnAllowedByBranch(columns_by_vehicle[k][c], branch)) continue;
                if (containsStation(columns_by_vehicle[k][c].mask, station)) {
                    writeTerm(1.0, zName(k, c), first);
                }
            }
        }
        if (first) {
            writeTerm(1.0, "branch_infeas_dummy", first);
            needs_branch_dummy = true;
        }
        out << " = 1\n";
    }

    for (int cut_idx = 0; cut_idx < static_cast<int>(active_cuts.size()); ++cut_idx) {
        out << " " << subsetRowCutName(cut_idx) << ":";
        first = true;
        for (int k = 0; k < instance.M; ++k) {
            for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
                if (!columnAllowedByBranch(columns_by_vehicle[k][c], branch)) continue;
                const int coeff = subsetRowCoefficient(columns_by_vehicle[k][c].mask,
                                                       active_cuts[cut_idx].stations);
                if (coeff > 0) {
                    writeTerm(static_cast<double>(coeff), zName(k, c), first);
                }
            }
        }
        if (first) out << " 0";
        out << " <= " << active_cuts[cut_idx].rhs << "\n";
    }

    out << "Bounds\n";
    for (int k = 0; k < instance.M; ++k) {
        for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
            if (!columnAllowedByBranch(columns_by_vehicle[k][c], branch)) continue;
            out << " 0 <= " << zName(k, c) << " <= 1\n";
        }
    }
    if (needs_branch_dummy) out << " 0 <= branch_infeas_dummy <= 0\n";
    for (int station = 1; station <= instance.V; ++station) {
        int y_lower = 0;
        int y_upper = instance.capacity[station];
        if (station < static_cast<int>(branch.inventory_lower.size())) {
            y_lower = std::max(y_lower, branch.inventory_lower[station]);
        }
        if (station < static_cast<int>(branch.inventory_upper.size())) {
            y_upper = std::min(y_upper, branch.inventory_upper[station]);
        }
        out << " " << y_lower << " <= " << yName(station) << " <= " << y_upper << "\n";
        out << " 0 <= " << rName(station) << "\n";
        out << " 0 <= " << eName(station) << "\n";
        if (phase_one) {
            out << " 0 <= " << invArtPlusName(station) << "\n";
            out << " 0 <= " << invArtMinusName(station) << "\n";
        }
    }
    for (int i = 1; i <= instance.V; ++i) {
        for (int j = i + 1; j <= instance.V; ++j) {
            out << " 0 <= " << hName(i, j) << "\n";
        }
    }
    out << " 0 <= " << sName() << "\n";
    out << " 0 <= " << hTotalName() << "\n";
    if (!phase_one && use_combined_gini_lower_bound) {
        out << " 0 <= " << gLowerName() << "\n";
    }
    if (phase_one) out << " 0 <= " << giniArtName() << "\n";
    if (phase_one && gamma_floor >= 0.0) {
        out << " 0 <= " << giniFloorArtName() << "\n";
    }
    out << "End\n";
    out.close();

    std::ofstream cmd(cmd_path);
    cmd << "set threads 1\n";
    cmd << "set timelimit " << time_limit_seconds << "\n";
    cmd << "read " << lp.lp_path.string() << "\n";
    cmd << "optimize\n";
    cmd << "write " << lp.sol_path.string() << "\n";
    cmd << "quit\n";
    cmd.close();

    const std::string command = "cmd /C \"" + quote(defaultCplexPath()) + " -f "
        + quote(cmd_path) + " > " + quote(lp.log_path) + " 2>&1\"";
    const int rc = std::system(command.c_str());
    if (rc != 0) {
        throw std::runtime_error("CPLEX fixed-Gini-cap LP command failed with return code "
            + std::to_string(rc));
    }
    if (!std::filesystem::exists(lp.sol_path) && logSaysInfeasible(lp.log_path)) {
        lp.status = "infeasible";
        lp.ok = false;
        return lp;
    }
    parseLpSolution(lp.sol_path, lp);
    lp.ok = statusIsOptimal(lp.status);
    return lp;
}

void captureColumnValues(const Instance& instance,
                         const std::vector<std::vector<RouteLoadColumn>>& columns_by_vehicle,
                         const GiniCapBranchRestriction& branch,
                         const LpSolve& lp,
                         std::vector<RouteLoadColumn>& columns,
                         std::vector<double>& z_values) {
    columns.clear();
    z_values.clear();
    for (int k = 0; k < instance.M; ++k) {
        for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
            if (!columnAllowedByBranch(columns_by_vehicle[k][c], branch)) continue;
            columns.push_back(columns_by_vehicle[k][c]);
            z_values.push_back(variableValue(lp, zName(k, c)));
        }
    }
}

bool zIntegral(const std::vector<double>& z_values, double tolerance = 1e-7) {
    for (double z : z_values) {
        if (z > tolerance && z < 1.0 - tolerance) return false;
    }
    return true;
}

int countSelectedColumns(const std::vector<double>& z_values, double tolerance = 1e-7) {
    int count = 0;
    for (double z : z_values) {
        if (z > 1.0 - tolerance) ++count;
    }
    return count;
}

std::string branchDescription(const GiniCapBranchRestriction& branch) {
    std::ostringstream out;
    bool first = true;
    for (const auto& pair : branch.forbid_together_pairs) {
        if (!first) out << ";";
        first = false;
        out << "forbid(" << pair.first << "," << pair.second << ")";
    }
    for (const auto& pair : branch.require_together_pairs) {
        if (!first) out << ";";
        first = false;
        out << "require(" << pair.first << "," << pair.second << ")";
    }
    for (int station : branch.forbid_stations) {
        if (!first) out << ";";
        first = false;
        out << "unserved(" << station << ")";
    }
    for (int station : branch.require_stations) {
        if (!first) out << ";";
        first = false;
        out << "served(" << station << ")";
    }
    for (int station : branch.forbid_pickup_stations) {
        if (!first) out << ";";
        first = false;
        out << "no_pickup(" << station << ")";
    }
    for (int station : branch.forbid_drop_stations) {
        if (!first) out << ";";
        first = false;
        out << "no_drop(" << station << ")";
    }
    for (int station = 1; station < static_cast<int>(branch.inventory_lower.size()); ++station) {
        if (branch.inventory_lower[station] > std::numeric_limits<int>::min() / 4) {
            if (!first) out << ";";
            first = false;
            out << "Y" << station << ">=" << branch.inventory_lower[station];
        }
    }
    for (int station = 1; station < static_cast<int>(branch.inventory_upper.size()); ++station) {
        if (branch.inventory_upper[station] < std::numeric_limits<int>::max() / 4) {
            if (!first) out << ";";
            first = false;
            out << "Y" << station << "<=" << branch.inventory_upper[station];
        }
    }
    if (first) out << "root";
    return out.str();
}

struct StationBranchCandidate {
    bool found = false;
    int station = 0;
    double value = 0.0;
    double fractional_score = 0.0;
};

StationBranchCandidate findStationBranchCandidate(
    int station_count,
    const std::vector<RouteLoadColumn>& columns,
    const std::vector<double>& z_values,
    double tolerance = 1e-7) {
    StationBranchCandidate best;
    for (int station = 1; station <= station_count; ++station) {
        double served = 0.0;
        for (int c = 0; c < static_cast<int>(columns.size()); ++c) {
            if (containsStation(columns[c].mask, station)) served += z_values[c];
        }
        if (served <= tolerance || served >= 1.0 - tolerance) continue;
        const double score = std::min(served, 1.0 - served);
        if (!best.found || score > best.fractional_score + 1e-12) {
            best.found = true;
            best.station = station;
            best.value = served;
            best.fractional_score = score;
        }
    }
    return best;
}

struct InventoryBranchCandidate {
    bool found = false;
    int station = 0;
    double value = 0.0;
    double fractional_score = 0.0;
};

InventoryBranchCandidate findInventoryBranchCandidate(
    const std::vector<double>& y_values,
    double tolerance = 1e-7) {
    InventoryBranchCandidate best;
    for (int station = 1; station < static_cast<int>(y_values.size()); ++station) {
        const double value = y_values[station];
        const double nearest = std::round(value);
        if (std::fabs(value - nearest) <= tolerance) continue;
        const double frac = value - std::floor(value);
        const double score = std::min(frac, 1.0 - frac);
        if (!best.found || score > best.fractional_score + 1e-12) {
            best.found = true;
            best.station = station;
            best.value = value;
            best.fractional_score = score;
        }
    }
    return best;
}

struct OperationModeBranchCandidate {
    bool found = false;
    int station = 0;
    double pickup_mass = 0.0;
    double drop_mass = 0.0;
    double score = 0.0;
};

OperationModeBranchCandidate findOperationModeBranchCandidate(
    int station_count,
    const std::vector<RouteLoadColumn>& columns,
    const std::vector<double>& z_values,
    double tolerance = 1e-7) {
    OperationModeBranchCandidate best;
    for (int station = 1; station <= station_count; ++station) {
        double pickup_mass = 0.0;
        double drop_mass = 0.0;
        for (int c = 0; c < static_cast<int>(columns.size()); ++c) {
            if (c >= static_cast<int>(z_values.size())) break;
            if (station >= static_cast<int>(columns[c].q.size())) continue;
            const double z = z_values[c];
            if (columns[c].q[station] > 0) pickup_mass += z;
            if (columns[c].q[station] < 0) drop_mass += z;
        }
        if (pickup_mass <= tolerance || drop_mass <= tolerance) continue;
        const double score = std::min(pickup_mass, drop_mass);
        if (!best.found || score > best.score + 1e-12) {
            best.found = true;
            best.station = station;
            best.pickup_mass = pickup_mass;
            best.drop_mass = drop_mass;
            best.score = score;
        }
    }
    return best;
}

struct LeafReconstructionResult {
    bool found = false;
    long long states = 0;
    int selected_count = 0;
    double surrogate = std::numeric_limits<double>::infinity();
    ObjectiveParts parts;
    std::vector<int> final_inventory;
    std::vector<int> selected_by_vehicle;
    std::vector<RoutePlan> routes;
};

std::vector<RoutePlan> routesFromSelection(
    const Instance& instance,
    const std::vector<std::vector<RouteLoadColumn>>& columns_by_vehicle,
    const std::vector<int>& selected_by_vehicle) {
    std::vector<RoutePlan> routes;
    routes.reserve(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        RoutePlan route;
        route.vehicle = k;
        route.nodes.push_back(0);
        const int col_idx = (k < static_cast<int>(selected_by_vehicle.size()))
            ? selected_by_vehicle[k] : -1;
        if (col_idx >= 0 && col_idx < static_cast<int>(columns_by_vehicle[k].size())) {
            const RouteLoadColumn& col = columns_by_vehicle[k][col_idx];
            if (col.can_be_used_for_incumbent &&
                col.elementary &&
                col.column_kind != "ng_relaxed_lower_bound") {
                for (int station : col.path) {
                    route.nodes.push_back(station);
                    StopOperation op;
                    op.station = station;
                    if (col.q[station] > 0) op.pickup = col.q[station];
                    if (col.q[station] < 0) op.drop = -col.q[station];
                    if (op.pickup > 0 || op.drop > 0) route.operations.push_back(op);
                }
            }
        }
        route.nodes.push_back(0);
        routes.push_back(std::move(route));
    }
    return routes;
}

std::vector<RoutePlan> emptyRoutes(const Instance& instance) {
    std::vector<RoutePlan> routes;
    routes.reserve(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        RoutePlan route;
        route.vehicle = k;
        route.nodes = {0, 0};
        routes.push_back(std::move(route));
    }
    return routes;
}

bool routeToColumn(const Instance& instance,
                   const RoutePlan& route,
                   RouteLoadColumn& column) {
    if (route.vehicle < 0 || route.vehicle >= instance.M) return false;
    if (route.nodes.size() < 2 || route.nodes.front() != 0 || route.nodes.back() != 0) {
        return false;
    }

    column = RouteLoadColumn{};
    column.vehicle = route.vehicle;
    column.q.assign(instance.V + 1, 0);
    for (std::size_t idx = 1; idx + 1 < route.nodes.size(); ++idx) {
        const int station = route.nodes[idx];
        if (station <= 0 || station > instance.V) return false;
        if (containsStation(column.mask, station)) return false;
        column.mask |= 1 << (station - 1);
        column.path.push_back(station);
    }
    for (const StopOperation& op : route.operations) {
        if (op.station <= 0 || op.station > instance.V) return false;
        column.q[op.station] += op.pickup;
        column.q[op.station] -= op.drop;
        column.pickup += op.pickup;
    }
    for (int q : column.q) {
        (void)q;
    }
    for (std::size_t idx = 0; idx + 1 < route.nodes.size(); ++idx) {
        column.travel += instance.dist[route.nodes[idx]][route.nodes[idx + 1]];
    }
    column.duration = column.travel
        + (instance.pickup_time + instance.drop_time) * column.pickup;
    column.reduced_cost = column.duration;
    return column.mask != 0 && column.duration <= instance.total_time_limit + 1e-9;
}

std::vector<std::vector<RouteLoadColumn>> columnsFromSeedRoutes(
    const Instance& instance,
    const std::vector<RoutePlan>& routes) {
    std::vector<std::vector<RouteLoadColumn>> columns(instance.M);
    for (const RoutePlan& route : routes) {
        RouteLoadColumn col;
        if (routeToColumn(instance, route, col) &&
            !hasColumn(columns[col.vehicle], col)) {
            columns[col.vehicle].push_back(std::move(col));
        }
    }
    return columns;
}

void addUniqueCandidate(std::vector<int>& values, int value, int upper) {
    if (value <= 0 || value > upper) return;
    if (std::find(values.begin(), values.end(), value) == values.end()) {
        values.push_back(value);
    }
}

void appendWarmStartColumns(const Instance& instance,
                            std::vector<std::vector<RouteLoadColumn>>& columns,
                            int warmstart_level) {
    if (warmstart_level <= 0) return;
    const double cunit = instance.pickup_time + instance.drop_time;
    if (cunit <= 1e-12) return;
    std::vector<std::unordered_set<std::string>> seen(instance.M);
    for (int k = 0; k < instance.M && k < static_cast<int>(columns.size()); ++k) {
        for (const RouteLoadColumn& col : columns[k]) {
            seen[k].insert(columnKey(k, col));
        }
    }
    auto appendIfNew = [&](int vehicle, RouteLoadColumn&& col) {
        const std::string key = columnKey(vehicle, col);
        if (seen[vehicle].insert(key).second) {
            columns[vehicle].push_back(std::move(col));
        }
    };
    for (int k = 0; k < instance.M; ++k) {
        if (k >= static_cast<int>(columns.size())) break;
        const int q_capacity = instance.Q[k];
        for (int pickup_station = 1; pickup_station <= instance.V; ++pickup_station) {
            const double one_stop_travel =
                instance.dist[0][pickup_station] + instance.dist[pickup_station][0];
            const int max_one_pick = std::min(
                instance.initial[pickup_station], q_capacity);
            std::vector<int> one_stop_pickups;
            if (warmstart_level >= 2) {
                for (int p = 1; p <= max_one_pick; ++p) one_stop_pickups.push_back(p);
            } else {
                addUniqueCandidate(one_stop_pickups, 1, max_one_pick);
                addUniqueCandidate(one_stop_pickups,
                                   instance.initial[pickup_station] -
                                       instance.target[pickup_station],
                                   max_one_pick);
                addUniqueCandidate(one_stop_pickups, max_one_pick, max_one_pick);
            }
            std::sort(one_stop_pickups.begin(), one_stop_pickups.end());
            for (int p : one_stop_pickups) {
                const double duration = one_stop_travel + cunit * p;
                if (duration > instance.total_time_limit + 1e-9) continue;
                RouteLoadColumn col;
                col.vehicle = k;
                col.mask = 1 << (pickup_station - 1);
                col.path = {pickup_station};
                col.q.assign(instance.V + 1, 0);
                col.q[pickup_station] = p;
                col.pickup = p;
                col.travel = one_stop_travel;
                col.duration = duration;
                col.reduced_cost = duration;
                appendIfNew(k, std::move(col));
            }

            for (int drop_station = 1; drop_station <= instance.V; ++drop_station) {
                if (drop_station == pickup_station) continue;
                const int drop_room =
                    instance.capacity[drop_station] - instance.initial[drop_station];
                if (drop_room <= 0) continue;
                const double two_stop_travel = instance.dist[0][pickup_station]
                    + instance.dist[pickup_station][drop_station]
                    + instance.dist[drop_station][0];
                if (two_stop_travel > instance.total_time_limit + 1e-9) continue;
                const int max_pick = std::min(
                    {instance.initial[pickup_station], q_capacity,
                     static_cast<int>(std::floor((instance.total_time_limit - two_stop_travel) /
                         cunit + 1e-9))});
                std::vector<int> pickup_values;
                if (warmstart_level >= 2) {
                    for (int p = 1; p <= max_pick; ++p) pickup_values.push_back(p);
                } else {
                    addUniqueCandidate(pickup_values, 1, max_pick);
                    addUniqueCandidate(pickup_values,
                                       instance.initial[pickup_station] -
                                           instance.target[pickup_station],
                                       max_pick);
                    addUniqueCandidate(pickup_values, max_pick, max_pick);
                }
                std::sort(pickup_values.begin(), pickup_values.end());
                for (int p : pickup_values) {
                    const int max_drop = std::min(drop_room, p);
                    std::vector<int> drop_values;
                    if (warmstart_level >= 2) {
                        for (int d = 1; d <= max_drop; ++d) drop_values.push_back(d);
                    } else {
                        addUniqueCandidate(drop_values, 1, max_drop);
                        addUniqueCandidate(drop_values,
                                           instance.target[drop_station] -
                                               instance.initial[drop_station],
                                           max_drop);
                        addUniqueCandidate(drop_values, max_drop, max_drop);
                    }
                    std::sort(drop_values.begin(), drop_values.end());
                    for (int d : drop_values) {
                        RouteLoadColumn col;
                        col.vehicle = k;
                        col.mask = (1 << (pickup_station - 1)) |
                                   (1 << (drop_station - 1));
                        col.path = {pickup_station, drop_station};
                        col.q.assign(instance.V + 1, 0);
                        col.q[pickup_station] = p;
                        col.q[drop_station] = -d;
                        col.pickup = p;
                        col.travel = two_stop_travel;
                        col.duration = two_stop_travel + cunit * p;
                        col.reduced_cost = col.duration;
                        appendIfNew(k, std::move(col));
                    }
                }
            }
        }
    }
}

bool satisfiesIntegerBranchRows(
    const std::vector<std::vector<RouteLoadColumn>>& columns_by_vehicle,
    const std::vector<int>& selected_by_vehicle,
    const GiniCapBranchRestriction& branch) {
    for (const auto& pair : branch.require_together_pairs) {
        int count = 0;
        for (int k = 0; k < static_cast<int>(selected_by_vehicle.size()); ++k) {
            const int idx = selected_by_vehicle[k];
            if (idx >= 0 && idx < static_cast<int>(columns_by_vehicle[k].size()) &&
                containsBoth(columns_by_vehicle[k][idx].mask, pair)) {
                ++count;
            }
        }
        if (count != 1) return false;
    }
    for (int station : branch.require_stations) {
        int count = 0;
        for (int k = 0; k < static_cast<int>(selected_by_vehicle.size()); ++k) {
            const int idx = selected_by_vehicle[k];
            if (idx >= 0 && idx < static_cast<int>(columns_by_vehicle[k].size()) &&
                containsStation(columns_by_vehicle[k][idx].mask, station)) {
                ++count;
            }
        }
        if (count != 1) return false;
    }
    return true;
}

bool objectivePartsInGiniInterval(const ObjectiveParts& parts,
                                  double gamma_floor,
                                  double gamma_cap) {
    if (parts.G > gamma_cap + 1e-8) return false;
    if (gamma_floor >= 0.0 && parts.G < gamma_floor - 1e-8) return false;
    return true;
}

double lowerBoundMetricFromParts(const Instance& instance,
                                 const ObjectiveParts& parts,
                                 double lambda,
                                 double gamma_floor,
                                 bool use_combined_gini_lower_bound,
                                 double s_upper) {
    const double floor_bound = std::max(0.0, gamma_floor);
    double gini_bound = floor_bound;
    if (use_combined_gini_lower_bound) {
        gini_bound = std::max(gini_bound,
                              parts.H / (static_cast<double>(instance.V) * s_upper));
    }
    return gini_bound + lambda * parts.P;
}

LeafReconstructionResult reconstructProjectedLeaf(
    const Instance& instance,
    const std::vector<std::vector<RouteLoadColumn>>& columns_by_vehicle,
    const GiniCapBranchRestriction& branch,
    const std::vector<double>& y_values,
    double lambda,
    double bound_gamma,
    bool use_combined_gini_lower_bound,
    double s_upper) {
    LeafReconstructionResult out;
    if (static_cast<int>(columns_by_vehicle.size()) != instance.M ||
        static_cast<int>(y_values.size()) <= instance.V) {
        return out;
    }

    std::vector<int> target_y(instance.V + 1, 0);
    for (int i = 1; i <= instance.V; ++i) {
        target_y[i] = static_cast<int>(std::llround(y_values[i]));
        if (target_y[i] < 0 || target_y[i] > instance.capacity[i]) return out;
    }

    std::vector<std::vector<int>> candidate_indices(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        candidate_indices[k].push_back(-1);
        for (int c = 0; c < static_cast<int>(columns_by_vehicle[k].size()); ++c) {
            const RouteLoadColumn& col = columns_by_vehicle[k][c];
            if (col.can_be_used_for_incumbent &&
                col.elementary &&
                col.column_kind != "ng_relaxed_lower_bound" &&
                columnAllowedByBranch(col, branch)) {
                candidate_indices[k].push_back(c);
            }
        }
    }

    std::vector<int> y = instance.initial;
    std::vector<int> selected(instance.M, -1);
    const int full_mask = (1 << instance.V) - 1;

    std::function<bool(int, int)> dfs = [&](int vehicle, int mask) -> bool {
        ++out.states;
        if (vehicle == instance.M) {
            for (int i = 1; i <= instance.V; ++i) {
                if (y[i] != target_y[i]) return false;
            }
            if (!satisfiesIntegerBranchRows(columns_by_vehicle, selected, branch)) return false;
            out.found = true;
            out.final_inventory = y;
            out.selected_by_vehicle = selected;
            out.selected_count = 0;
            for (int idx : selected) if (idx >= 0) ++out.selected_count;
            out.parts = computeObjectiveParts(instance, y, lambda);
            out.surrogate = use_combined_gini_lower_bound
                ? lowerBoundMetricFromParts(instance, out.parts, lambda, bound_gamma,
                                            true, s_upper)
                : bound_gamma + lambda * out.parts.P;
            out.routes = routesFromSelection(instance, columns_by_vehicle, selected);
            return true;
        }

        for (int col_idx : candidate_indices[vehicle]) {
            if (col_idx < 0) {
                selected[vehicle] = -1;
                if (dfs(vehicle + 1, mask)) return true;
                continue;
            }
            const RouteLoadColumn& col = columns_by_vehicle[vehicle][col_idx];
            if ((mask & col.mask) != 0) continue;
            if ((col.mask & ~full_mask) != 0) continue;
            bool ok = true;
            for (int i = 1; i <= instance.V; ++i) {
                y[i] -= col.q[i];
                if (y[i] < 0 || y[i] > instance.capacity[i]) ok = false;
            }
            if (ok) {
                bool possible = true;
                for (int i = 1; i <= instance.V; ++i) {
                    if (vehicle == instance.M - 1 && y[i] != target_y[i]) {
                        possible = false;
                        break;
                    }
                }
                if (possible) {
                    selected[vehicle] = col_idx;
                    if (dfs(vehicle + 1, mask | col.mask)) return true;
                }
            }
            for (int i = 1; i <= instance.V; ++i) y[i] += col.q[i];
        }
        selected[vehicle] = -1;
        return false;
    };

    if (dfs(0, 0)) return out;

    std::vector<int> q(instance.V + 1, 0);
    std::vector<int> active_stations;
    for (int i = 1; i <= instance.V; ++i) {
        q[i] = instance.initial[i] - target_y[i];
        if (q[i] != 0) active_stations.push_back(i);
    }
    const int active_count = static_cast<int>(active_stations.size());
    if (active_count > 20) return out;
    const int all_active_mask = (1 << active_count) - 1;
    const double cunit = instance.pickup_time + instance.drop_time;

    std::vector<std::vector<RouteLoadColumn>> feasible_by_vehicle(
        instance.M, std::vector<RouteLoadColumn>(1 << active_count));
    std::vector<std::vector<char>> feasible(
        instance.M, std::vector<char>(1 << active_count, 0));
    for (int k = 0; k < instance.M; ++k) {
        feasible[k][0] = 1;
        feasible_by_vehicle[k][0].vehicle = k;
        feasible_by_vehicle[k][0].q.assign(instance.V + 1, 0);
        for (int subset = 1; subset <= all_active_mask; ++subset) {
            RouteLoadColumn best;
            best.vehicle = k;
            best.q.assign(instance.V + 1, 0);
            int station_mask = 0;
            int pickup_sum = 0;
            for (int bit = 0; bit < active_count; ++bit) {
                if (!(subset & (1 << bit))) continue;
                const int station = active_stations[bit];
                station_mask |= 1 << (station - 1);
                best.q[station] = q[station];
                if (q[station] > 0) pickup_sum += q[station];
            }
            best.mask = station_mask;
            best.pickup = pickup_sum;
            if (!columnAllowedByBranch(best, branch)) continue;
            bool found_order = false;
            std::vector<int> path;
            std::vector<char> used(active_count, 0);
            double best_duration = std::numeric_limits<double>::infinity();
            std::vector<int> best_path;
            std::function<void(int, int, double, int, int)> order_dfs =
                [&](int last, int load, double travel, int visited, int pickup_total) {
                    if (visited == subset) {
                        const double total_travel = travel + instance.dist[last][0];
                        const double duration = total_travel + cunit * pickup_total;
                        if (duration <= instance.total_time_limit + 1e-9 &&
                            duration < best_duration) {
                            best_duration = duration;
                            best.travel = total_travel;
                            best.duration = duration;
                            best_path = path;
                            found_order = true;
                        }
                        return;
                    }
                    if (travel + instance.dist[last][0] > instance.total_time_limit + 1e-9) {
                        return;
                    }
                    for (int bit = 0; bit < active_count; ++bit) {
                        if (!(subset & (1 << bit)) || used[bit]) continue;
                        const int station = active_stations[bit];
                        const int delta = q[station];
                        int next_load = load;
                        int next_pickup = pickup_total;
                        if (delta > 0) {
                            next_load += delta;
                            next_pickup += delta;
                            if (next_load > instance.Q[k]) continue;
                        } else {
                            next_load += delta;
                            if (next_load < 0) continue;
                        }
                        const double next_travel = travel + instance.dist[last][station];
                        if (next_travel + instance.dist[station][0] +
                                cunit * next_pickup > instance.total_time_limit + 1e-9) {
                            continue;
                        }
                        used[bit] = 1;
                        path.push_back(station);
                        order_dfs(station, next_load, next_travel,
                                  visited | (1 << bit), next_pickup);
                        path.pop_back();
                        used[bit] = 0;
                    }
                };
            order_dfs(0, 0, 0.0, 0, 0);
            if (found_order) {
                best.path = best_path;
                feasible[k][subset] = 1;
                feasible_by_vehicle[k][subset] = std::move(best);
            }
        }
    }

    std::vector<RouteLoadColumn> chosen(instance.M);
    std::vector<int> chosen_subset(instance.M, 0);
    std::function<bool(int, int)> partition_dfs = [&](int vehicle, int covered) -> bool {
        ++out.states;
        if (vehicle == instance.M) {
            if (covered != all_active_mask) return false;
            std::vector<std::vector<RouteLoadColumn>> selected_columns(instance.M);
            std::vector<int> selected_indices(instance.M, -1);
            for (int k = 0; k < instance.M; ++k) {
                if (chosen_subset[k] != 0) {
                    selected_columns[k].push_back(chosen[k]);
                    selected_indices[k] = 0;
                }
            }
            if (!satisfiesIntegerBranchRows(selected_columns, selected_indices, branch)) {
                return false;
            }
            out.found = true;
            out.final_inventory = target_y;
            out.selected_by_vehicle = selected_indices;
            out.selected_count = 0;
            for (int idx : selected_indices) if (idx >= 0) ++out.selected_count;
            out.parts = computeObjectiveParts(instance, target_y, lambda);
            out.surrogate = use_combined_gini_lower_bound
                ? lowerBoundMetricFromParts(instance, out.parts, lambda, bound_gamma,
                                            true, s_upper)
                : bound_gamma + lambda * out.parts.P;
            out.routes = routesFromSelection(instance, selected_columns, selected_indices);
            return true;
        }
        const int remaining = all_active_mask ^ covered;
        for (int sub = remaining; ; sub = (sub - 1) & remaining) {
            if (feasible[vehicle][sub]) {
                chosen_subset[vehicle] = sub;
                chosen[vehicle] = feasible_by_vehicle[vehicle][sub];
                if (partition_dfs(vehicle + 1, covered | sub)) return true;
            }
            if (sub == 0) break;
        }
        chosen_subset[vehicle] = 0;
        return false;
    };

    partition_dfs(0, 0);
    return out;
}

void addStats(GiniCapTreeResult& total, const GiniCapColumnGenerationResult& node) {
    total.pricing_calls += node.pricing_calls;
    total.generated_columns += node.generated_columns;
    total.columns_generated_raw += node.columns_generated_raw;
    total.columns_after_dominance += node.columns_after_dominance;
    total.columns_dominated += node.columns_dominated;
    total.pricing_columns_enumerated += node.pricing_columns_enumerated;
    total.dominance_input_columns += node.dominance_input_columns;
    total.dominance_kept_columns += node.dominance_kept_columns;
    total.dominance_removed_columns += node.dominance_removed_columns;
    total.dominance_removed_existing_projection +=
        node.dominance_removed_existing_projection;
    total.dominance_removed_candidate_projection +=
        node.dominance_removed_candidate_projection;
    total.rmp_columns_inserted += node.rmp_columns_inserted;
    total.rmp_columns_active += node.rmp_columns_active;
    total.dominance_time_seconds += node.dominance_time_seconds;
    total.dominance_mode = node.dominance_mode;
    total.dominance_exact_safe =
        total.dominance_exact_safe && node.dominance_exact_safe;
    total.pricing_negative_columns_found += node.pricing_negative_columns_found;
    total.pricing_negative_columns_inserted += node.pricing_negative_columns_inserted;
    total.pricing_negative_columns_dominated += node.pricing_negative_columns_dominated;
    total.pricing_completed_exactly =
        total.pricing_completed_exactly && node.pricing_completed_exactly;
    total.pricing_best_reduced_cost_any =
        std::min(total.pricing_best_reduced_cost_any,
                 node.pricing_best_reduced_cost_any);
    total.pricing_best_new_reduced_cost =
        std::min(total.pricing_best_new_reduced_cost,
                 node.pricing_best_new_reduced_cost);
    total.pricing_duplicate_negative_projections +=
        node.pricing_duplicate_negative_projections;
    total.pricing_new_negative_projections +=
        node.pricing_new_negative_projections;
    total.pricing_blocked_by_duplicate_projection =
        total.pricing_blocked_by_duplicate_projection ||
        node.pricing_blocked_by_duplicate_projection;
    total.pricing_closure_certified_exact =
        total.pricing_closure_certified_exact &&
        node.pricing_closure_certified_exact;
    if (total.pricing_closure_status.empty() ||
        total.pricing_closure_status == "not_run" ||
        node.pricing_closure_status == "negative_columns_remaining" ||
        node.pricing_closure_status == "duplicate_negative_projection" ||
        node.pricing_closure_status == "pricing_time_limit") {
        total.pricing_closure_status = node.pricing_closure_status;
    }
    if (node.pricing_remaining_negative_rc < total.pricing_remaining_negative_rc) {
        total.pricing_remaining_negative_rc = node.pricing_remaining_negative_rc;
    }
    total.pricing_exact_verification_calls +=
        node.pricing_exact_verification_calls;
    total.pricing_exact_verification_time_seconds +=
        node.pricing_exact_verification_time_seconds;
    total.bpc_pricing_engine_fallbacks += node.bpc_pricing_engine_fallbacks;
    if (!node.bpc_pricing_engine_requested.empty()) {
        total.bpc_pricing_engine_requested = node.bpc_pricing_engine_requested;
    }
    if (!node.bpc_pricing_engine_used.empty()) {
        total.bpc_pricing_engine_used = node.bpc_pricing_engine_used;
    }
    total.bpc_nodes_using_ng_dssr += node.bpc_nodes_using_ng_dssr;
    total.bpc_nodes_using_exact_label += node.bpc_nodes_using_exact_label;
    total.bpc_nodes_using_hybrid += node.bpc_nodes_using_hybrid;
    total.bpc_nodes_exactly_priced += node.bpc_nodes_exactly_priced;
    total.bpc_nodes_dssr_incomplete += node.bpc_nodes_dssr_incomplete;
    total.bpc_nodes_final_verifier_called +=
        node.bpc_nodes_final_verifier_called;
    total.bpc_nodes_final_verifier_completed +=
        node.bpc_nodes_final_verifier_completed;
    if (!node.column_tracks.empty()) total.column_tracks = node.column_tracks;
    if (!node.rmp_column_space.empty()) total.rmp_column_space = node.rmp_column_space;
    total.elementary_columns_generated += node.elementary_columns_generated;
    total.elementary_columns_inserted += node.elementary_columns_inserted;
    total.relaxed_columns_generated += node.relaxed_columns_generated;
    total.relaxed_columns_inserted += node.relaxed_columns_inserted;
    total.relaxed_columns_rejected_projection +=
        node.relaxed_columns_rejected_projection;
    total.relaxed_columns_rejected_infeasible_projection +=
        node.relaxed_columns_rejected_infeasible_projection;
    total.relaxed_columns_used_in_lb_rmp += node.relaxed_columns_used_in_lb_rmp;
    total.relaxed_columns_used_in_incumbent += node.relaxed_columns_used_in_incumbent;
    total.non_elementary_relaxed_routes_seen +=
        node.non_elementary_relaxed_routes_seen;
    total.non_elementary_relaxed_columns_validated +=
        node.non_elementary_relaxed_columns_validated;
    total.non_elementary_relaxed_columns_inserted +=
        node.non_elementary_relaxed_columns_inserted;
    total.non_elementary_relaxed_columns_rejected +=
        node.non_elementary_relaxed_columns_rejected;
    total.relaxed_projection_rejected_load += node.relaxed_projection_rejected_load;
    total.relaxed_projection_rejected_station_capacity +=
        node.relaxed_projection_rejected_station_capacity;
    total.relaxed_projection_rejected_branch += node.relaxed_projection_rejected_branch;
    total.relaxed_projection_rejected_operation_mode +=
        node.relaxed_projection_rejected_operation_mode;
    total.relaxed_projection_rejected_unsafe_cut +=
        node.relaxed_projection_rejected_unsafe_cut;
    total.relaxed_projection_validation_time_seconds +=
        node.relaxed_projection_validation_time_seconds;
    total.relaxed_columns_blocked_from_incumbent +=
        node.relaxed_columns_blocked_from_incumbent;
    total.relaxed_columns_blocked_from_export +=
        node.relaxed_columns_blocked_from_export;
    total.relaxed_columns_blocked_from_candidate_reconstruction +=
        node.relaxed_columns_blocked_from_candidate_reconstruction;
    total.relaxed_rmp_enabled = total.relaxed_rmp_enabled || node.relaxed_rmp_enabled;
    total.relaxed_rmp_objective = std::max(total.relaxed_rmp_objective,
                                           node.relaxed_rmp_objective);
    total.relaxed_rmp_lower_bound = std::max(total.relaxed_rmp_lower_bound,
                                             node.relaxed_rmp_lower_bound);
    total.relaxed_rmp_columns += node.relaxed_rmp_columns;
    total.relaxed_rmp_iterations += node.relaxed_rmp_iterations;
    total.relaxed_rmp_pricing_closed =
        total.relaxed_rmp_pricing_closed || node.relaxed_rmp_pricing_closed;
    total.relaxed_rmp_best_reduced_cost =
        std::min(total.relaxed_rmp_best_reduced_cost,
                 node.relaxed_rmp_best_reduced_cost);
    total.relaxed_rmp_certificate_valid =
        total.relaxed_rmp_certificate_valid || node.relaxed_rmp_certificate_valid;
    if (!node.relaxed_rmp_certificate_rejection_reason.empty()) {
        total.relaxed_rmp_certificate_rejection_reason =
            node.relaxed_rmp_certificate_rejection_reason;
    }
    total.elementary_pricing_closed =
        total.elementary_pricing_closed || node.elementary_pricing_closed;
    total.ng_relaxed_pricing_closed =
        total.ng_relaxed_pricing_closed || node.ng_relaxed_pricing_closed;
    total.dssr_exact_elementary_closed =
        total.dssr_exact_elementary_closed || node.dssr_exact_elementary_closed;
    total.ng_relaxed_best_reduced_cost =
        std::min(total.ng_relaxed_best_reduced_cost,
                 node.ng_relaxed_best_reduced_cost);
    total.ng_relaxed_negative_routes_found += node.ng_relaxed_negative_routes_found;
    total.ng_relaxed_negative_columns_inserted +=
        node.ng_relaxed_negative_columns_inserted;
    total.ng_relaxed_negative_routes_rejected +=
        node.ng_relaxed_negative_routes_rejected;
    total.ng_relaxed_closure_labels_processed +=
        node.ng_relaxed_closure_labels_processed;
    total.ng_relaxed_closure_labels_pruned +=
        node.ng_relaxed_closure_labels_pruned;
    total.ng_relaxed_closure_time_seconds +=
        node.ng_relaxed_closure_time_seconds;
    if (!node.ng_relaxed_closure_stop_reason.empty()) {
        total.ng_relaxed_closure_stop_reason =
            node.ng_relaxed_closure_stop_reason;
    }
    total.ng_relaxed_pricing_calls += node.ng_relaxed_pricing_calls;
    total.ng_relaxed_labels_processed += node.ng_relaxed_labels_processed;
    total.ng_relaxed_labels_pruned += node.ng_relaxed_labels_pruned;
    total.dssr_refinement_rounds_for_lb += node.dssr_refinement_rounds_for_lb;
    total.dssr_lb_before_refinement =
        std::max(total.dssr_lb_before_refinement, node.dssr_lb_before_refinement);
    total.dssr_lb_after_refinement =
        std::max(total.dssr_lb_after_refinement, node.dssr_lb_after_refinement);
    total.relaxed_rmp_cg_iterations += node.relaxed_rmp_cg_iterations;
    total.relaxed_rmp_cg_columns_added += node.relaxed_rmp_cg_columns_added;
    total.relaxed_rmp_cg_final_best_rc =
        std::min(total.relaxed_rmp_cg_final_best_rc,
                 node.relaxed_rmp_cg_final_best_rc);
    total.relaxed_rmp_cg_closed =
        total.relaxed_rmp_cg_closed || node.relaxed_rmp_cg_closed;
    if (!node.relaxed_rmp_cg_stop_reason.empty()) {
        total.relaxed_rmp_cg_stop_reason = node.relaxed_rmp_cg_stop_reason;
    }
    total.relaxed_rmp_lb_before_cg =
        std::max(total.relaxed_rmp_lb_before_cg, node.relaxed_rmp_lb_before_cg);
    total.relaxed_rmp_lb_after_cg =
        std::max(total.relaxed_rmp_lb_after_cg, node.relaxed_rmp_lb_after_cg);
    total.ng_size = std::max(total.ng_size, node.ng_size);
    if (!node.ng_neighborhood_mode.empty()) {
        total.ng_neighborhood_mode = node.ng_neighborhood_mode;
    }
    total.ng_memory_total += node.ng_memory_total;
    total.dssr_memory_total_initial += node.dssr_memory_total_initial;
    total.dssr_memory_total_final += node.dssr_memory_total_final;
    total.dssr_rounds += node.dssr_rounds;
    total.dssr_memory_expansions += node.dssr_memory_expansions;
    total.dssr_repeated_station_events += node.dssr_repeated_station_events;
    total.dssr_relaxed_negative_routes += node.dssr_relaxed_negative_routes;
    total.dssr_non_elementary_routes += node.dssr_non_elementary_routes;
    total.dssr_elementary_columns_found += node.dssr_elementary_columns_found;
    total.dssr_no_negative_relaxed_route =
        total.dssr_no_negative_relaxed_route || node.dssr_no_negative_relaxed_route;
    total.dssr_exact_closure_proved =
        total.dssr_exact_closure_proved || node.dssr_exact_closure_proved;
    total.dssr_final_exact_verification_time +=
        node.dssr_final_exact_verification_time;
    total.dssr_time_seconds += node.dssr_time_seconds;
    if (!node.dssr_stop_reason.empty()) {
        if (!total.dssr_stop_reason.empty()) total.dssr_stop_reason += "; ";
        total.dssr_stop_reason += node.dssr_stop_reason;
    }
    total.cg_stabilization_mode = node.cg_stabilization_mode;
    total.cg_stabilized_pricing_calls += node.cg_stabilized_pricing_calls;
    total.cg_true_pricing_calls += node.cg_true_pricing_calls;
    total.cg_stabilization_columns_found += node.cg_stabilization_columns_found;
    total.cg_true_pricing_columns_found += node.cg_true_pricing_columns_found;
    total.cg_dual_center_updates += node.cg_dual_center_updates;
    total.cg_dual_oscillation_metric =
        std::max(total.cg_dual_oscillation_metric,
                 node.cg_dual_oscillation_metric);
    total.cg_true_negative_columns_inserted +=
        node.cg_true_negative_columns_inserted;
    total.cg_stabilization_false_negatives +=
        node.cg_stabilization_false_negatives;
    total.cg_final_true_pricing_rc = node.cg_final_true_pricing_rc;
    total.support_duration_cuts_generated += node.support_duration_cuts_generated;
    total.support_duration_pruned_labels += node.support_duration_pruned_labels;
    total.support_duration_pruned_columns += node.support_duration_pruned_columns;
    total.support_duration_strong_cuts_generated +=
        node.support_duration_strong_cuts_generated;
    total.support_duration_strong_pruned_labels +=
        node.support_duration_strong_pruned_labels;
    total.support_duration_strong_pruned_columns +=
        node.support_duration_strong_pruned_columns;
    total.completion_lb_pruned_labels += node.completion_lb_pruned_labels;
    total.required_closure_pruned_labels +=
        node.required_closure_pruned_labels;
    total.label_dominance_comparisons += node.label_dominance_comparisons;
    total.label_dominance_pruned_labels += node.label_dominance_pruned_labels;
    total.label_dominance_cross_pickup_pruned_labels +=
        node.label_dominance_cross_pickup_pruned_labels;
    total.label_dominance_inactive_entries_skipped +=
        node.label_dominance_inactive_entries_skipped;
    total.label_dominance_bucket_compactions +=
        node.label_dominance_bucket_compactions;
    total.label_dominance_compacted_entries +=
        node.label_dominance_compacted_entries;
    total.operation_dp_dominance_pruned_states +=
        node.operation_dp_dominance_pruned_states;
    total.support_duration_max_subset_size =
        std::max(total.support_duration_max_subset_size,
                 node.support_duration_max_subset_size);
    total.support_duration_precompute_time_seconds +=
        node.support_duration_precompute_time_seconds;
    total.route_states += node.route_states;
    total.operation_states += node.operation_states;
    total.cuts_added += node.cuts_added;
    total.pricing_time_seconds += node.pricing_time_seconds;
    total.master_time_seconds += node.master_time_seconds;
}

template <typename ResultLike>
void finalizePricingClosureFields(ResultLike& result,
                                  double tolerance = 1e-7) {
    const bool has_pricing = result.pricing_calls > 0;
    const double best_rc = std::isfinite(result.pricing_best_reduced_cost_any)
        ? result.pricing_best_reduced_cost_any
        : 0.0;
    const bool negative_remaining = std::isfinite(best_rc) &&
        best_rc < -tolerance;
    result.pricing_remaining_negative_rc = negative_remaining ? best_rc : 0.0;
    if (!has_pricing) {
        result.pricing_closure_status = "not_run";
    } else if (result.pricing_blocked_by_duplicate_projection) {
        result.pricing_closure_status = "duplicate_negative_projection";
    } else if (!result.pricing_completed_exactly) {
        result.pricing_closure_status = negative_remaining
            ? "negative_columns_remaining"
            : "pricing_time_limit";
    } else if (negative_remaining) {
        result.pricing_closure_status = "negative_columns_remaining";
    } else {
        result.pricing_closure_status = "exact_no_negative";
    }
    result.pricing_closure_certified_exact =
        has_pricing &&
        result.pricing_completed_exactly &&
        !result.pricing_blocked_by_duplicate_projection &&
        !negative_remaining;
    result.pricing_exact_verification_calls =
        result.pricing_closure_certified_exact ? 1 : 0;
}

} // namespace

ColumnGenerationResult runCoverageColumnGenerationDiagnostic(
    const Instance& instance,
    double time_limit_seconds,
    int max_iterations,
    const PricingOptions& base_pricing_options) {
    const auto start = Clock::now();
    ColumnGenerationResult result;
    initializeBpcPricingFields(result, base_pricing_options);
    const auto required = chooseRequiredPair(instance);
    result.required_i = required.first;
    result.required_j = required.second;
    if (required.first == 0) {
        result.notes.push_back("No feasible one-stop pickup pair was found for the coverage diagnostic.");
        return result;
    }

    result.columns_by_vehicle.assign(instance.M, {});
    for (int k = 0; k < instance.M; ++k) {
        for (int station : {required.first, required.second}) {
            RouteLoadColumn col;
            if (oneStopPickupColumn(instance, k, station, col)) {
                result.columns_by_vehicle[k].push_back(std::move(col));
            }
        }
    }

    double best_rc = std::numeric_limits<double>::infinity();
    for (int iter = 0; iter < max_iterations; ++iter) {
        result.iterations = iter + 1;
        const double elapsed = std::chrono::duration<double>(Clock::now() - start).count();
        const double remaining = (time_limit_seconds > 0.0)
            ? std::max(0.1, time_limit_seconds - elapsed) : 0.0;
        LpSolve lp = solveCoverageLp(instance, result.columns_by_vehicle,
                                     required.first, required.second,
                                     remaining, iter);
        result.lp_objective = lp.objective;
        result.notes.push_back("iteration " + std::to_string(iter)
            + " LP status=" + lp.status
            + ", objective=" + num(lp.objective)
            + ", columns=" + std::to_string([&]() {
                long long total = 0;
                for (const auto& cols : result.columns_by_vehicle) total += cols.size();
                return total;
            }()));
        if (!lp.ok) return result;

        best_rc = std::numeric_limits<double>::infinity();
        bool added = false;
        for (int k = 0; k < instance.M; ++k) {
            PricingDuals duals;
            duals.travel_cost = 1.0;
            duals.pickup_cost = instance.pickup_time + instance.drop_time;
            duals.constant = -dualValue(lp, vehicleName(k));
            duals.visit_cost.assign(instance.V + 1, 0.0);
            duals.visit_cost[required.first] -= dualValue(lp, coverName(required.first));
            duals.visit_cost[required.second] -= dualValue(lp, coverName(required.second));

            PricingOptions pricing_options = base_pricing_options;
            pricing_options.time_limit_seconds = remaining;
            pricing_options.allowed_station_mask =
                (1 << (required.first - 1)) | (1 << (required.second - 1));
            PricingResult priced = priceRouteLoadColumnExact(
                instance, k, duals, pricing_options, Clock::now());
            accumulateBpcPricingStats(result, priced);
            ++result.pricing_calls;
            result.route_states += priced.route_states;
            result.operation_states += priced.operation_states;
            result.support_duration_cuts_generated +=
                priced.support_duration_cuts_generated;
            result.support_duration_pruned_labels +=
                priced.support_duration_pruned_labels;
            result.support_duration_pruned_columns +=
                priced.support_duration_pruned_columns;
            result.support_duration_strong_cuts_generated +=
                priced.support_duration_strong_cuts_generated;
            result.support_duration_strong_pruned_labels +=
                priced.support_duration_strong_pruned_labels;
            result.support_duration_strong_pruned_columns +=
                priced.support_duration_strong_pruned_columns;
            result.completion_lb_pruned_labels += priced.completion_lb_pruned_labels;
            result.required_closure_pruned_labels +=
                priced.required_closure_pruned_labels;
            result.support_duration_max_subset_size =
                std::max(result.support_duration_max_subset_size,
                         priced.support_duration_max_subset_size);
            result.support_duration_precompute_time_seconds +=
                priced.support_duration_precompute_time_seconds;
            if (!priced.complete) return result;
            best_rc = std::min(best_rc, priced.best_reduced_cost);
            if (priced.has_column && priced.best_reduced_cost < -1e-7 &&
                !hasColumn(result.columns_by_vehicle[k], priced.best_column)) {
                result.columns_by_vehicle[k].push_back(std::move(priced.best_column));
                result.notes.push_back("iteration " + std::to_string(iter)
                    + " added vehicle " + std::to_string(k)
                    + " column with reduced_cost=" + num(best_rc));
                added = true;
            }
        }
        result.best_pricing_reduced_cost = best_rc;
        if (!added) {
            result.complete = true;
            break;
        }
    }
    for (const auto& cols : result.columns_by_vehicle) {
        result.generated_columns += static_cast<long long>(cols.size());
    }
    return result;
}

GiniCapColumnGenerationResult runGiniCapColumnGenerationInternal(
    const Instance& instance,
    double lambda,
    double gamma,
    double gamma_floor,
    double time_limit_seconds,
    int max_iterations,
    const GiniCapBranchRestriction& branch,
    const std::vector<std::vector<RouteLoadColumn>>* initial_columns = nullptr,
    bool use_combined_gini_lower_bound = false,
    double objective_cutoff = std::numeric_limits<double>::infinity(),
    int pricing_return_columns = 1,
    bool column_dominance_enabled = true,
    const std::string& column_dominance_mode = "exact",
    bool support_duration_pruning_enabled = true,
    int support_duration_max_subset_size = 5,
    const PricingOptions& base_pricing_options = PricingOptions{}) {
    const auto start = Clock::now();
    GiniCapColumnGenerationResult result;
    initializeBpcPricingFields(result, base_pricing_options);
    result.pricing_best_reduced_cost_any =
        std::numeric_limits<double>::infinity();
    result.pricing_best_new_reduced_cost =
        std::numeric_limits<double>::infinity();
    result.gamma = gamma;
    result.gamma_floor = gamma_floor;
    result.columns_by_vehicle = initial_columns
        ? *initial_columns : std::vector<std::vector<RouteLoadColumn>>(instance.M);
    ColumnDominanceOptions dominance_options;
    dominance_options.enabled = column_dominance_enabled;
    dominance_options.mode = parseColumnDominanceMode(column_dominance_mode);
    dominance_options.exact_safe = true;
    dominance_options = normalizeColumnDominanceOptions(dominance_options);
    result.dominance_mode = columnDominanceModeName(dominance_options.mode);
    result.dominance_exact_safe = dominance_options.exact_safe;
    if (dominance_options.enabled) {
        for (auto& cols : result.columns_by_vehicle) {
            ColumnDominanceStats stats;
            applyColumnDominance(cols, dominance_options, stats);
            result.columns_generated_raw += stats.columns_generated_raw;
            result.columns_after_dominance += stats.columns_after_dominance;
            result.columns_dominated += stats.columns_dominated;
            result.dominance_input_columns += stats.dominance_input_columns;
            result.dominance_kept_columns += stats.dominance_kept_columns;
            result.dominance_removed_columns += stats.dominance_removed_columns;
            result.dominance_removed_existing_projection +=
                stats.dominance_removed_existing_projection;
            result.dominance_removed_candidate_projection +=
                stats.dominance_removed_candidate_projection;
            result.dominance_time_seconds += stats.dominance_time_seconds;
        }
    }
    const double bound_gamma = (gamma_floor >= 0.0) ? gamma_floor : gamma;
    if (use_combined_gini_lower_bound) {
        result.notes.push_back(gamma_floor >= 0.0
            ? "Fixed-Gini-interval restricted master uses V*floor*S <= H <= V*gamma*S and minimizes a valid linear lower bound on G+lambda*P over the current route-load column pool."
            : "Fixed-Gini-cap restricted master uses H <= V*gamma*S and minimizes a valid linear lower bound on G+lambda*P over the current route-load column pool.");
    } else {
        result.notes.push_back(gamma_floor >= 0.0
            ? "Fixed-Gini-interval restricted master uses V*floor*S <= H <= V*gamma*S and minimizes lambda*P over the current route-load column pool."
            : "Fixed-Gini-cap restricted master uses H <= V*gamma*S and minimizes lambda*P over the current route-load column pool.");
    }
    if (use_combined_gini_lower_bound) {
        result.notes.push_back("Restricted master objective uses the valid linear Gini lower estimator g_lb >= floor and g_lb >= H/(V*S_max), with S_max from station-bike conservation and current inventory upper bounds.");
        if (std::isfinite(objective_cutoff) && lambda > 1e-12) {
            const double floor_bound = std::max(0.0, gamma_floor);
            const double penalty_budget = (objective_cutoff - floor_bound) / lambda;
            result.notes.push_back("Incumbent cutoff mode tightens S_max for potentially improving solutions using P <= (cutoff-floor)/lambda; cutoff="
                + num(objective_cutoff) + ", penalty_budget=" + num(penalty_budget));
        }
    }
    result.notes.push_back("This diagnostic certifies only the continuous root relaxation when exact pricing closes; it is not an integer EBRP certificate.");
    std::vector<SubsetRowCut> active_cuts;
    auto refreshPoolColumnCount = [&]() {
        result.generated_columns = 0;
        for (const auto& cols : result.columns_by_vehicle) {
            for (const auto& col : cols) {
                if (columnAllowedByBranch(col, branch)) ++result.generated_columns;
            }
        }
    };

    bool phase_one_active = false;
    int phase_one_iterations = 0;
    for (int iter = 0; iter < max_iterations; ++iter) {
        result.iterations = iter + 1;
        const double elapsed = std::chrono::duration<double>(Clock::now() - start).count();
        if (time_limit_seconds > 0.0 && elapsed >= time_limit_seconds) {
            result.notes.push_back("time limit reached before LP iteration " + std::to_string(iter));
            break;
        }
        const double remaining = (time_limit_seconds > 0.0)
            ? std::max(0.1, time_limit_seconds - elapsed) : 0.0;

        const auto master_start = Clock::now();
        LpSolve lp = solveGiniCapLp(instance, result.columns_by_vehicle,
                                    lambda, gamma, gamma_floor, remaining, iter, branch,
                                    phase_one_active, use_combined_gini_lower_bound,
                                    active_cuts, objective_cutoff);
        result.master_time_seconds +=
            std::chrono::duration<double>(Clock::now() - master_start).count();
        if (phase_one_active) ++phase_one_iterations;
        if (!phase_one_active) {
            double lambda_penalty = 0.0;
            for (int i = 1; i <= instance.V; ++i) {
                lambda_penalty += lambda * instance.weights[i] * variableValue(lp, eName(i));
            }
            result.lp_lambda_penalty = lambda_penalty;
            result.fixed_cap_surrogate = use_combined_gini_lower_bound
                ? lp.objective : bound_gamma + lp.objective;
            long long relaxed_columns_in_pool = 0;
            for (const auto& cols : result.columns_by_vehicle) {
                for (const RouteLoadColumn& col : cols) {
                    if ((!col.elementary ||
                         col.column_kind == "ng_relaxed_lower_bound" ||
                         !col.can_be_used_for_incumbent) &&
                        columnAllowedByBranch(col, branch)) {
                        ++relaxed_columns_in_pool;
                    }
                }
            }
            if (result.relaxed_rmp_enabled || relaxed_columns_in_pool > 0) {
                result.relaxed_rmp_enabled = true;
                result.relaxed_rmp_columns = relaxed_columns_in_pool;
                result.relaxed_rmp_objective = result.fixed_cap_surrogate;
                result.relaxed_rmp_lower_bound = result.fixed_cap_surrogate;
                result.relaxed_rmp_iterations = result.iterations;
                result.relaxed_rmp_certificate_valid = false;
                result.relaxed_rmp_certificate_rejection_reason =
                    "ng_relaxed_pricing_not_yet_closed";
            }
        }
        captureColumnValues(instance, result.columns_by_vehicle, branch, lp,
                            result.flat_columns, result.z_values);
        result.y_values.assign(instance.V + 1, 0.0);
        for (int station = 1; station <= instance.V; ++station) {
            result.y_values[station] = variableValue(lp, yName(station));
        }
        const double artificial = phase_one_active
            ? phaseArtificialValue(instance, lp) : 0.0;

        long long total_columns = 0;
        for (const auto& cols : result.columns_by_vehicle) {
            for (const auto& col : cols) {
                if (columnAllowedByBranch(col, branch)) ++total_columns;
            }
        }
        long long positive_z = 0;
        for (int k = 0; k < instance.M; ++k) {
            for (int c = 0; c < static_cast<int>(result.columns_by_vehicle[k].size()); ++c) {
                if (variableValue(lp, zName(k, c)) > 1e-8) ++positive_z;
            }
        }
        result.notes.push_back("iteration " + std::to_string(iter)
            + (phase_one_active ? " phase-I" : "")
            + " LP status=" + lp.status
            + (phase_one_active
                ? ", artificial=" + num(artificial)
                : ", lambdaP=" + num(result.lp_lambda_penalty)
                    + (use_combined_gini_lower_bound
                        ? ", g_lb=" + num(variableValue(lp, gLowerName()))
                            + ", gini_lb_plus_lambdaP=" + num(result.fixed_cap_surrogate)
                        : ", bound_gamma_plus_lambdaP=" + num(result.fixed_cap_surrogate)))
            + ", S=" + num(variableValue(lp, sName()))
            + ", H=" + num(variableValue(lp, hTotalName()))
            + ", columns=" + std::to_string(total_columns)
            + ", positive_z=" + std::to_string(positive_z));
        if (!lp.ok) {
            if (!phase_one_active && statusIsInfeasible(lp.status)) {
                result.notes.push_back("restricted master infeasible; entering phase-I column generation with artificial inventory and Gini-cap slack");
                phase_one_active = true;
                continue;
            }
            if (statusIsInfeasible(lp.status)) {
                result.complete = true;
                result.infeasible = true;
                result.lp_lambda_penalty = std::numeric_limits<double>::infinity();
                result.fixed_cap_surrogate = std::numeric_limits<double>::infinity();
                result.notes.push_back("restricted master LP is infeasible under current branch restrictions; node is fathomed");
                refreshPoolColumnCount();
                return result;
            }
            refreshPoolColumnCount();
            result.pricing_completed_exactly = false;
            return result;
        }

        if (phase_one_active && artificial <= 1e-7) {
            result.notes.push_back("phase-I artificial variables are zero; switching back to the original fixed-Gini-cap master");
            phase_one_active = false;
            continue;
        }

        if (!phase_one_active) {
            const std::vector<int> cut_sizes =
                (instance.V >= 5) ? std::vector<int>{3, 5} : std::vector<int>{3};
            std::vector<SubsetRowCut> cuts =
                separateSubsetRowCuts(instance.V, result.flat_columns,
                                      result.z_values, cut_sizes, 1e-7, 10);
            int added_cuts = 0;
            for (const SubsetRowCut& cut : cuts) {
                auto sameStations = [&](const SubsetRowCut& existing) {
                    return existing.stations == cut.stations;
                };
                if (std::find_if(active_cuts.begin(), active_cuts.end(), sameStations) !=
                    active_cuts.end()) {
                    continue;
                }
                active_cuts.push_back(cut);
                ++added_cuts;
                ++result.cuts_added;
                std::ostringstream cut_note;
                cut_note << "iteration " << iter
                         << " added subset-row cut size=" << cut.stations.size()
                         << " rhs=" << cut.rhs
                         << " stations=(";
                for (int pos = 0; pos < static_cast<int>(cut.stations.size()); ++pos) {
                    if (pos > 0) cut_note << ",";
                    cut_note << cut.stations[pos];
                }
                cut_note << "), lhs=" << num(cut.lhs)
                         << ", violation=" << num(cut.violation);
                result.notes.push_back(cut_note.str());
            }
            if (added_cuts > 0) {
                continue;
            }
        }

        double best_rc = std::numeric_limits<double>::infinity();
        bool added = false;
        bool duplicate_negative = false;
        PricingDuals shared_duals;
        shared_duals.visit_cost.assign(instance.V + 1, 0.0);
        shared_duals.operation_cost.assign(instance.V + 1, 0.0);
        for (int station = 1; station <= instance.V; ++station) {
            shared_duals.visit_cost[station] = -dualValue(lp, gcapVisitName(station));
            shared_duals.operation_cost[station] = -dualValue(lp, gcapInventoryName(station));
        }
        for (const auto& pair : branch.require_together_pairs) {
            shared_duals.pair_cost.push_back({
                pair, -dualValue(lp, requireTogetherName(pair.first, pair.second))
            });
        }
        for (int cut_idx = 0; cut_idx < static_cast<int>(active_cuts.size()); ++cut_idx) {
            shared_duals.subset_row_cost.push_back({
                active_cuts[cut_idx].stations, -dualValue(lp, subsetRowCutName(cut_idx))
            });
        }
        for (int station : branch.require_stations) {
            shared_duals.visit_cost[station] -= dualValue(lp, requireStationName(station));
        }
        int forbidden_station_mask = 0;
        for (int station : branch.forbid_stations) {
            if (station >= 1 && station <= instance.V) {
                forbidden_station_mask |= (1 << (station - 1));
            }
        }
        int forbid_pickup_station_mask = 0;
        for (int station : branch.forbid_pickup_stations) {
            if (station >= 1 && station <= instance.V) {
                forbid_pickup_station_mask |= (1 << (station - 1));
            }
        }
        int forbid_drop_station_mask = 0;
        for (int station : branch.forbid_drop_stations) {
            if (station >= 1 && station <= instance.V) {
                forbid_drop_station_mask |= (1 << (station - 1));
            }
        }
        std::vector<double> vehicle_constants(instance.M, 0.0);
        std::unordered_map<int, double> stop_threshold_by_capacity;
        for (int k = 0; k < instance.M; ++k) {
            vehicle_constants[k] = -dualValue(lp, vehicleName(k));
            const double threshold =
                (pricing_return_columns > 1 && instance.V >= 10 && !phase_one_active)
                ? -vehicle_constants[k] - 1e-2
                : -std::numeric_limits<double>::infinity();
            auto [it, inserted] = stop_threshold_by_capacity.emplace(instance.Q[k], threshold);
            if (!inserted) it->second = std::min(it->second, threshold);
        }
        std::unordered_map<int, PricingResult> pricing_by_capacity;
        for (int k = 0; k < instance.M; ++k) {
            const double vehicle_elapsed = std::chrono::duration<double>(
                Clock::now() - start).count();
            const double vehicle_remaining = (time_limit_seconds > 0.0)
                ? std::max(0.1, time_limit_seconds - vehicle_elapsed) : 0.0;

            const double vehicle_constant = vehicle_constants[k];
            PricingResult priced;
            auto cached = pricing_by_capacity.find(instance.Q[k]);
            bool reused_pricing = cached != pricing_by_capacity.end();
            double pricing_call_seconds = 0.0;
            if (reused_pricing) {
                priced = cached->second;
            } else {
                PricingDuals duals = shared_duals;
                duals.constant = 0.0;
                PricingOptions pricing_options = base_pricing_options;
                pricing_options.time_limit_seconds = vehicle_remaining;
                pricing_options.forbidden_station_mask = forbidden_station_mask;
                pricing_options.forbid_pickup_station_mask = forbid_pickup_station_mask;
                pricing_options.forbid_drop_station_mask = forbid_drop_station_mask;
                pricing_options.forbid_together_pairs = branch.forbid_together_pairs;
                pricing_options.require_together_pairs = branch.require_together_pairs;
                pricing_options.support_duration_pruning =
                    support_duration_pruning_enabled;
                pricing_options.support_duration_max_subset_size =
                    support_duration_max_subset_size;
                pricing_options.stop_reduced_cost =
                    stop_threshold_by_capacity.at(instance.Q[k]);
                pricing_options.max_returned_columns =
                    (instance.V >= 10 && !phase_one_active)
                        ? std::max(1, pricing_return_columns)
                        : 1;
                const auto pricing_start = Clock::now();
                priced = priceRouteLoadColumnExact(
                    instance, k, duals, pricing_options, pricing_start);
                pricing_call_seconds =
                    std::chrono::duration<double>(Clock::now() - pricing_start).count();
                accumulateBpcPricingStats(result, priced);
                result.pricing_time_seconds += pricing_call_seconds;
                pricing_by_capacity.emplace(instance.Q[k], priced);
                ++result.pricing_calls;
                result.route_states += priced.route_states;
                result.operation_states += priced.operation_states;
                result.columns_generated_raw += priced.generated_columns;
                result.pricing_columns_enumerated += priced.generated_columns;
                result.support_duration_cuts_generated +=
                    priced.support_duration_cuts_generated;
                result.support_duration_pruned_labels +=
                    priced.support_duration_pruned_labels;
                result.support_duration_pruned_columns +=
                    priced.support_duration_pruned_columns;
                result.support_duration_strong_cuts_generated +=
                    priced.support_duration_strong_cuts_generated;
                result.support_duration_strong_pruned_labels +=
                    priced.support_duration_strong_pruned_labels;
                result.support_duration_strong_pruned_columns +=
                    priced.support_duration_strong_pruned_columns;
                result.completion_lb_pruned_labels +=
                    priced.completion_lb_pruned_labels;
                result.required_closure_pruned_labels +=
                    priced.required_closure_pruned_labels;
                result.support_duration_max_subset_size =
                    std::max(result.support_duration_max_subset_size,
                             priced.support_duration_max_subset_size);
                result.support_duration_precompute_time_seconds +=
                    priced.support_duration_precompute_time_seconds;
            }
            if (priced.has_column) {
                priced.best_column.vehicle = k;
                priced.best_column.reduced_cost += vehicle_constant;
            }
            for (RouteLoadColumn& column : priced.negative_columns) {
                column.vehicle = k;
                column.reduced_cost += vehicle_constant;
            }
            priced.best_reduced_cost += vehicle_constant;
            priced.has_negative_column = priced.has_column &&
                priced.best_reduced_cost < -1e-9;
            auto appendPricingTrace = [&](const PricingResult& trace_priced,
                                          double trace_seconds,
                                          bool trace_reused_pricing,
                                          const std::string& event) {
                std::ostringstream trace;
                trace << std::setprecision(12)
                      << "{"
                      << "\"iteration\": " << iter
                      << ", \"vehicle\": " << k
                      << ", \"event\": \"" << jsonEscapeCg(event) << "\""
                      << ", \"dual_summary\": \""
                      << jsonEscapeCg("visit_l1=" + num([&]() {
                             double sum = 0.0;
                             for (double v : shared_duals.visit_cost) sum += std::fabs(v);
                             return sum;
                         }()) + ";operation_l1=" + num([&]() {
                             double sum = 0.0;
                             for (double v : shared_duals.operation_cost) sum += std::fabs(v);
                             return sum;
                         }()) + ";vehicle_constant=" + num(vehicle_constant))
                      << "\""
                      << ", \"pricing_engine_requested\": \""
                      << jsonEscapeCg(result.bpc_pricing_engine_requested) << "\""
                      << ", \"pricing_engine_used\": \""
                      << jsonEscapeCg(trace_priced.pricing_engine) << "\""
                      << ", \"reused_capacity_price\": "
                      << (trace_reused_pricing ? "true" : "false")
                      << ", \"generated_columns\": " << trace_priced.generated_columns
                      << ", \"returned_negative_columns\": "
                      << trace_priced.negative_columns.size()
                      << ", \"route_states\": "
                      << (trace_reused_pricing ? 0 : trace_priced.route_states)
                      << ", \"operation_states\": "
                      << (trace_reused_pricing ? 0 : trace_priced.operation_states)
                      << ", \"labels_pruned_support_duration\": "
                      << (trace_priced.support_duration_pruned_labels +
                          trace_priced.support_duration_strong_pruned_labels)
                      << ", \"labels_pruned_completion_lb\": "
                      << trace_priced.completion_lb_pruned_labels
                      << ", \"labels_pruned_required_closure\": "
                      << trace_priced.required_closure_pruned_labels
                      << ", \"label_dominance_comparisons\": "
                      << trace_priced.label_dominance_comparisons
                      << ", \"labels_pruned_label_dominance\": "
                      << trace_priced.label_dominance_pruned_labels
                      << ", \"labels_pruned_cross_pickup_dominance\": "
                      << trace_priced.label_dominance_cross_pickup_pruned_labels
                      << ", \"label_dominance_inactive_entries_skipped\": "
                      << trace_priced.label_dominance_inactive_entries_skipped
                      << ", \"label_dominance_bucket_compactions\": "
                      << trace_priced.label_dominance_bucket_compactions
                      << ", \"label_dominance_compacted_entries\": "
                      << trace_priced.label_dominance_compacted_entries
                      << ", \"operation_dp_dominance_pruned_states\": "
                      << trace_priced.operation_dp_dominance_pruned_states
                      << ", \"best_reduced_cost\": "
                      << jsonNumberCg(trace_priced.best_reduced_cost)
                      << ", \"exact_completed\": "
                      << (trace_priced.complete ? "true" : "false")
                      << ", \"early_negative_stop\": "
                      << (trace_priced.stopped_early_with_column ? "true" : "false")
                      << ", \"time_seconds\": "
                      << jsonNumberCg(trace_seconds)
                      << ", \"timeout_unfinished_state_count\": "
                      << (trace_priced.complete ? 0 :
                          trace_priced.route_states + trace_priced.operation_states)
                      << "}";
                result.pricing_trace_json_objects.push_back(trace.str());
            };
            if (!priced.complete) {
                if (priced.stopped_early_with_column && priced.has_negative_column) {
                    result.notes.push_back("iteration " + std::to_string(iter)
                        + " vehicle " + std::to_string(k)
                        + " pricing stopped after finding a valid negative column; exact closure is deferred");
                } else {
                    appendPricingTrace(priced, pricing_call_seconds,
                                       reused_pricing, "pricing_time_limit");
                    result.notes.push_back("iteration " + std::to_string(iter)
                        + " vehicle " + std::to_string(k)
                        + " pricing hit the time limit after route_states="
                        + std::to_string(priced.route_states)
                        + ", operation_states=" + std::to_string(priced.operation_states));
                    result.best_pricing_reduced_cost =
                        std::isfinite(best_rc) ? best_rc : priced.best_reduced_cost;
                    result.pricing_best_reduced_cost_any =
                        result.best_pricing_reduced_cost;
                    refreshPoolColumnCount();
                    result.pricing_completed_exactly = false;
                    finalizePricingClosureFields(result);
                    return result;
                }
            }

            double exact_rerun_pricing_seconds = 0.0;
            auto rerun_exact_pricing_for_capacity = [&]() {
                const double exact_elapsed = std::chrono::duration<double>(
                    Clock::now() - start).count();
                const double exact_remaining = (time_limit_seconds > 0.0)
                    ? std::max(0.1, time_limit_seconds - exact_elapsed) : 0.0;
                PricingDuals duals = shared_duals;
                duals.constant = 0.0;
                PricingOptions pricing_options = base_pricing_options;
                pricing_options.time_limit_seconds = exact_remaining;
                pricing_options.forbidden_station_mask = forbidden_station_mask;
                pricing_options.forbid_pickup_station_mask = forbid_pickup_station_mask;
                pricing_options.forbid_drop_station_mask = forbid_drop_station_mask;
                pricing_options.forbid_together_pairs = branch.forbid_together_pairs;
                pricing_options.require_together_pairs = branch.require_together_pairs;
                pricing_options.support_duration_pruning =
                    support_duration_pruning_enabled;
                pricing_options.support_duration_max_subset_size =
                    support_duration_max_subset_size;
                pricing_options.max_returned_columns =
                    (instance.V >= 10 && !phase_one_active)
                        ? std::max(1, pricing_return_columns)
                        : 1;
                const auto pricing_start = Clock::now();
                PricingResult exact =
                    priceRouteLoadColumnExact(
                        instance, k, duals, pricing_options, pricing_start);
                exact_rerun_pricing_seconds =
                    std::chrono::duration<double>(Clock::now() - pricing_start).count();
                accumulateBpcPricingStats(result, exact);
                result.pricing_time_seconds += exact_rerun_pricing_seconds;
                pricing_by_capacity[instance.Q[k]] = exact;
                ++result.pricing_calls;
                result.route_states += exact.route_states;
                result.operation_states += exact.operation_states;
                result.columns_generated_raw += exact.generated_columns;
                result.pricing_columns_enumerated += exact.generated_columns;
                result.support_duration_cuts_generated +=
                    exact.support_duration_cuts_generated;
                result.support_duration_pruned_labels +=
                    exact.support_duration_pruned_labels;
                result.support_duration_pruned_columns +=
                    exact.support_duration_pruned_columns;
                result.support_duration_strong_cuts_generated +=
                    exact.support_duration_strong_cuts_generated;
                result.support_duration_strong_pruned_labels +=
                    exact.support_duration_strong_pruned_labels;
                result.support_duration_strong_pruned_columns +=
                    exact.support_duration_strong_pruned_columns;
                result.completion_lb_pruned_labels +=
                    exact.completion_lb_pruned_labels;
                result.required_closure_pruned_labels +=
                    exact.required_closure_pruned_labels;
                result.support_duration_max_subset_size =
                    std::max(result.support_duration_max_subset_size,
                             exact.support_duration_max_subset_size);
                result.support_duration_precompute_time_seconds +=
                    exact.support_duration_precompute_time_seconds;
                return exact;
            };

            if (priced.stopped_early_with_column && priced.has_negative_column &&
                hasColumn(result.columns_by_vehicle[k], priced.best_column)) {
                result.notes.push_back("iteration " + std::to_string(iter)
                    + " vehicle " + std::to_string(k)
                    + " early negative column is already present; rerunning exact pricing before any closure claim");
                PricingResult exact = rerun_exact_pricing_for_capacity();
                priced = exact;
                pricing_call_seconds = exact_rerun_pricing_seconds;
                reused_pricing = false;
                if (priced.has_column) {
                    priced.best_column.vehicle = k;
                    priced.best_column.reduced_cost += vehicle_constant;
                }
                for (RouteLoadColumn& column : priced.negative_columns) {
                    column.vehicle = k;
                    column.reduced_cost += vehicle_constant;
                }
                priced.best_reduced_cost += vehicle_constant;
                priced.has_negative_column = priced.has_column &&
                    priced.best_reduced_cost < -1e-9;
                if (!priced.complete) {
                    appendPricingTrace(priced, pricing_call_seconds,
                                       reused_pricing, "exact_rerun_time_limit");
                    result.notes.push_back("iteration " + std::to_string(iter)
                        + " vehicle " + std::to_string(k)
                        + " exact pricing rerun hit the time limit after route_states="
                        + std::to_string(priced.route_states)
                        + ", operation_states=" + std::to_string(priced.operation_states));
                    result.best_pricing_reduced_cost =
                        std::isfinite(best_rc) ? best_rc : priced.best_reduced_cost;
                    result.pricing_best_reduced_cost_any =
                        result.best_pricing_reduced_cost;
                    refreshPoolColumnCount();
                    result.pricing_completed_exactly = false;
                    finalizePricingClosureFields(result);
                    return result;
                }
            }

            best_rc = std::min(best_rc, priced.best_reduced_cost);
            result.pricing_best_reduced_cost_any =
                std::min(result.pricing_best_reduced_cost_any,
                         priced.best_reduced_cost);
            std::ostringstream note;
            note << "iteration " << iter
                 << " vehicle " << k
                 << " pricing_engine_requested=" << result.bpc_pricing_engine_requested
                 << ", pricing_engine_used=" << priced.pricing_engine
                 << ", dssr_stop_reason=" << priced.dssr_stop_reason
                 << ", pricing_complete=" << (priced.complete ? "true" : "false")
                 << ", early_negative_stop="
                 << (priced.stopped_early_with_column ? "true" : "false")
                 << ", reused_capacity_price=" << (reused_pricing ? "true" : "false")
                 << ", generated_columns=" << priced.generated_columns
                 << ", returned_negative_columns=" << priced.negative_columns.size()
                 << ", route_states=" << (reused_pricing ? 0 : priced.route_states)
                 << ", operation_states=" << (reused_pricing ? 0 : priced.operation_states)
                 << ", best_reduced_cost=" << priced.best_reduced_cost;
            result.notes.push_back(note.str());
            appendPricingTrace(priced, pricing_call_seconds,
                               reused_pricing, "pricing_complete");
            if (!result.bpc_pricing_engine_requested.empty() &&
                result.bpc_pricing_engine_requested != "auto" &&
                result.bpc_pricing_engine_requested != priced.pricing_engine) {
                std::string reason = "other";
                if (result.bpc_pricing_engine_requested == "hybrid" &&
                    priced.pricing_engine == "exact-label" && instance.V <= 16) {
                    reason = "small_instance_exact_label_verification";
                } else if (priced.pricing_closure_status.find("unsupported") !=
                           std::string::npos) {
                    reason = "large_instance_guard";
                }
                result.notes.push_back("iteration " + std::to_string(iter)
                    + " vehicle " + std::to_string(k)
                    + " pricing_engine_fallback_reason=" + reason
                    + ", requested=" + result.bpc_pricing_engine_requested
                    + ", used=" + priced.pricing_engine);
            }

            std::vector<RouteLoadColumn> negative_candidates;
            if (priced.has_column && priced.best_reduced_cost < -1e-7) {
                negative_candidates.push_back(priced.best_column);
            }
            for (RouteLoadColumn column : priced.negative_columns) {
                if (column.reduced_cost >= -1e-7) continue;
                if (!columnAllowedByBranch(column, branch)) {
                    result.notes.push_back("iteration " + std::to_string(iter)
                        + " vehicle " + std::to_string(k)
                        + " returned an extra branch-infeasible pricing column; stopping without claiming closure");
                    refreshPoolColumnCount();
                    result.pricing_completed_exactly = false;
                    return result;
                }
                negative_candidates.push_back(std::move(column));
            }
            long long relaxed_candidates_seen = 0;
            for (const RouteLoadColumn& column : negative_candidates) {
                if (!column.elementary ||
                    column.column_kind == "ng_relaxed_lower_bound" ||
                    !column.can_be_used_for_incumbent) {
                    ++relaxed_candidates_seen;
                }
            }

            if (!negative_candidates.empty()) {
                for (const RouteLoadColumn& column : negative_candidates) {
                    if (!columnAllowedByBranch(column, branch)) {
                        result.notes.push_back("iteration " + std::to_string(iter)
                            + " vehicle " + std::to_string(k)
                            + " pricing returned a branch-infeasible column; stopping without claiming closure");
                        refreshPoolColumnCount();
                        result.pricing_completed_exactly = false;
                        return result;
                    }
                }
                result.pricing_negative_columns_found +=
                    static_cast<long long>(negative_candidates.size());
                std::unordered_set<std::string> existing_projection_keys;
                existing_projection_keys.reserve(result.columns_by_vehicle[k].size());
                for (const RouteLoadColumn& existing_column :
                     result.columns_by_vehicle[k]) {
                    existing_projection_keys.insert(projectionKey(existing_column));
                }
                long long duplicate_projection_candidates = 0;
                for (const RouteLoadColumn& column : negative_candidates) {
                    if (existing_projection_keys.find(projectionKey(column)) !=
                        existing_projection_keys.end()) {
                        ++duplicate_projection_candidates;
                    }
                }
                ColumnDominanceStats stats;
                std::vector<RouteLoadColumn> filtered =
                    filterNewColumnsByDominance(
                        result.columns_by_vehicle[k], std::move(negative_candidates),
                        dominance_options, stats);
                result.columns_after_dominance += stats.columns_after_dominance;
                result.columns_dominated += stats.columns_dominated;
                result.dominance_input_columns += stats.dominance_input_columns;
                result.dominance_kept_columns += stats.dominance_kept_columns;
                result.dominance_removed_columns += stats.dominance_removed_columns;
                result.dominance_removed_existing_projection +=
                    stats.dominance_removed_existing_projection;
                result.dominance_removed_candidate_projection +=
                    stats.dominance_removed_candidate_projection;
                result.dominance_time_seconds += stats.dominance_time_seconds;
                result.pricing_duplicate_negative_projections +=
                    std::max(duplicate_projection_candidates,
                             stats.dominance_removed_existing_projection);
                const int inserted_before =
                    static_cast<int>(result.columns_by_vehicle[k].size());
                int inserted = 0;
                int relaxed_inserted = 0;
                int elementary_inserted = 0;
                for (RouteLoadColumn& column : filtered) {
                    if (!column.can_be_used_for_lower_bound) {
                        ++result.relaxed_columns_rejected_projection;
                        continue;
                    }
                    if (hasColumn(result.columns_by_vehicle[k], column)) continue;
                    result.pricing_best_new_reduced_cost =
                        std::min(result.pricing_best_new_reduced_cost,
                                 column.reduced_cost);
                    const bool relaxed_column =
                        !column.elementary ||
                        column.column_kind == "ng_relaxed_lower_bound" ||
                        !column.can_be_used_for_incumbent;
                    result.columns_by_vehicle[k].push_back(std::move(column));
                    ++inserted;
                    if (relaxed_column) ++relaxed_inserted;
                    else ++elementary_inserted;
                }
                if (inserted > 0) {
                    added = true;
                    result.pricing_negative_columns_inserted += inserted;
                    result.pricing_new_negative_projections += inserted;
                    result.rmp_columns_inserted += inserted;
                    result.elementary_columns_inserted += elementary_inserted;
                    result.relaxed_columns_inserted += relaxed_inserted;
                    result.relaxed_columns_used_in_lb_rmp += relaxed_inserted;
                    result.relaxed_rmp_columns += relaxed_inserted;
                    result.relaxed_rmp_enabled =
                        result.relaxed_rmp_enabled || relaxed_inserted > 0;
                } else {
                    duplicate_negative = true;
                    result.pricing_blocked_by_duplicate_projection = true;
                    result.notes.push_back("iteration " + std::to_string(iter)
                        + " vehicle " + std::to_string(k)
                        + " all negative pricing columns were already present or dominated; stopping conservatively without claiming closure");
                }
                result.pricing_negative_columns_dominated +=
                    std::max(0, static_cast<int>(stats.columns_dominated));
                result.notes.push_back("iteration " + std::to_string(iter)
                    + " vehicle " + std::to_string(k)
                    + " dominance-filtered negative pricing columns: found="
                    + std::to_string(result.pricing_negative_columns_found)
                    + ", inserted_this_vehicle=" + std::to_string(inserted)
                    + ", pool_before=" + std::to_string(inserted_before)
                    + ", pool_after="
                    + std::to_string(result.columns_by_vehicle[k].size())
                    + ", relaxed_candidates_seen="
                    + std::to_string(relaxed_candidates_seen)
                    + ", relaxed_inserted_this_vehicle="
                    + std::to_string(relaxed_inserted)
                    + ", dominated_total="
                    + std::to_string(result.pricing_negative_columns_dominated)
                    + ", mode=" + result.dominance_mode);
            }
        }
        result.best_pricing_reduced_cost = best_rc;
        result.pricing_best_reduced_cost_any = best_rc;
        if (result.relaxed_rmp_enabled) {
            result.relaxed_rmp_best_reduced_cost = best_rc;
            result.relaxed_rmp_pricing_closed =
                result.pricing_completed_exactly &&
                result.ng_relaxed_pricing_closed && best_rc >= -1e-7;
            result.relaxed_rmp_certificate_valid =
                result.relaxed_rmp_pricing_closed;
            result.relaxed_rmp_certificate_rejection_reason =
                result.relaxed_rmp_certificate_valid
                    ? "none"
                    : "ng_relaxed_pricing_incomplete_or_negative_reduced_cost";
            result.relaxed_rmp_cg_iterations = iter + 1;
            result.relaxed_rmp_cg_final_best_rc = best_rc;
            result.relaxed_rmp_cg_closed = result.relaxed_rmp_pricing_closed;
            result.relaxed_rmp_cg_stop_reason =
                result.relaxed_rmp_cg_closed
                    ? "ng_relaxed_pricing_closed"
                    : result.relaxed_rmp_certificate_rejection_reason;
        }
        if (!added) {
            if (phase_one_active) {
                if (!duplicate_negative && best_rc >= -1e-7) {
                    result.complete = true;
                    result.infeasible = true;
                    result.lp_lambda_penalty = std::numeric_limits<double>::infinity();
                    result.fixed_cap_surrogate = std::numeric_limits<double>::infinity();
                    result.notes.push_back("phase-I pricing closed with positive artificial value; no feasible route-load column combination satisfies this fixed cap/branch node");
                    refreshPoolColumnCount();
                    finalizePricingClosureFields(result);
                    return result;
                } else if (duplicate_negative) {
                    result.complete = false;
                    result.pricing_completed_exactly = false;
                    result.pricing_closure_certified_exact = false;
                    result.notes.push_back("phase-I duplicate negative projection prevented progress; node is left unresolved because duplicate columns do not prove closure");
    refreshPoolColumnCount();
    finalizePricingClosureFields(result);
    if (result.relaxed_rmp_enabled) {
        result.relaxed_rmp_lb_after_cg = result.fixed_cap_surrogate;
        if (result.relaxed_rmp_lb_before_cg == 0.0) {
            result.relaxed_rmp_lb_before_cg = result.fixed_cap_surrogate;
        }
        result.relaxed_rmp_cg_columns_added = result.relaxed_columns_inserted;
    }
    return result;
}
            } else if (!duplicate_negative && best_rc >= -1e-7) {
                result.complete = true;
            } else if (duplicate_negative) {
                result.complete = false;
                result.pricing_completed_exactly = false;
                result.pricing_closure_certified_exact = false;
                result.notes.push_back("duplicate or dominated negative pricing projection prevents node closure; exact pricing did not certify absence of missing negative projections");
                refreshPoolColumnCount();
                finalizePricingClosureFields(result);
                return result;
            }
            break;
        }
    }

    refreshPoolColumnCount();
    result.rmp_columns_active = result.generated_columns;
    if (!result.complete && result.iterations >= max_iterations) {
        result.notes.push_back("maximum column-generation iterations reached before exact pricing closure");
    }
    result.pricing_completed_exactly = result.complete;
    finalizePricingClosureFields(result);
    if (!std::isfinite(result.pricing_best_new_reduced_cost)) {
        result.pricing_best_new_reduced_cost = 0.0;
    }
    if (!std::isfinite(result.pricing_best_reduced_cost_any)) {
        result.pricing_best_reduced_cost_any = 0.0;
    }
    if (phase_one_iterations > 0) {
        result.notes.push_back("phase-I iterations used=" + std::to_string(phase_one_iterations));
    }
    return result;
}

GiniCapColumnGenerationResult runGiniCapColumnGenerationDiagnostic(
    const Instance& instance,
    double lambda,
    double gamma,
    double time_limit_seconds,
    int max_iterations,
    bool support_duration_pruning_enabled,
    int support_duration_max_subset_size,
    const PricingOptions& pricing_options) {
    return runGiniCapColumnGenerationInternal(
        instance, lambda, gamma, -1.0, time_limit_seconds, max_iterations,
        GiniCapBranchRestriction{}, nullptr, false,
        std::numeric_limits<double>::infinity(), 1, true, "exact",
        support_duration_pruning_enabled, support_duration_max_subset_size,
        pricing_options);
}

GiniCapBranchProbeResult runGiniCapRyanFosterBranchProbe(
    const Instance& instance,
    double lambda,
    double gamma,
    double time_limit_seconds,
    int max_iterations,
    bool support_duration_pruning_enabled,
    int support_duration_max_subset_size,
    const PricingOptions& pricing_options) {
    const auto start = Clock::now();
    GiniCapBranchProbeResult result;
    initializeBpcPricingFields(result, pricing_options);
    result.notes.push_back("Fixed-Gini-cap Ryan-Foster branch probe closes the root LP, selects one fractional co-route pair, then closes both child root LPs if time allows. This is one branch level, not a full integer tree.");

    const double root_budget = (time_limit_seconds > 0.0) ? time_limit_seconds * 0.45 : 0.0;
    GiniCapColumnGenerationResult root = runGiniCapColumnGenerationInternal(
        instance, lambda, gamma, -1.0, root_budget, max_iterations,
        GiniCapBranchRestriction{}, nullptr, false,
        std::numeric_limits<double>::infinity(), 1, true, "exact",
        support_duration_pruning_enabled, support_duration_max_subset_size,
        pricing_options);
    result.root_complete = root.complete;
    result.bpc_pricing_engine_fallbacks += root.bpc_pricing_engine_fallbacks;
    result.bpc_nodes_using_ng_dssr += root.bpc_nodes_using_ng_dssr;
    result.bpc_nodes_using_exact_label += root.bpc_nodes_using_exact_label;
    result.bpc_nodes_using_hybrid += root.bpc_nodes_using_hybrid;
    result.bpc_nodes_exactly_priced += root.bpc_nodes_exactly_priced;
    result.bpc_nodes_dssr_incomplete += root.bpc_nodes_dssr_incomplete;
    result.bpc_nodes_final_verifier_called += root.bpc_nodes_final_verifier_called;
    result.bpc_nodes_final_verifier_completed += root.bpc_nodes_final_verifier_completed;
    result.root_bound = root.fixed_cap_surrogate;
    result.pricing_calls += root.pricing_calls;
    result.generated_columns += root.generated_columns;
    result.columns_generated_raw += root.columns_generated_raw;
    result.columns_after_dominance += root.columns_after_dominance;
    result.columns_dominated += root.columns_dominated;
    result.dominance_time_seconds += root.dominance_time_seconds;
    result.dominance_mode = root.dominance_mode;
    result.dominance_exact_safe =
        result.dominance_exact_safe && root.dominance_exact_safe;
    result.pricing_negative_columns_found += root.pricing_negative_columns_found;
    result.pricing_negative_columns_inserted += root.pricing_negative_columns_inserted;
    result.pricing_negative_columns_dominated += root.pricing_negative_columns_dominated;
    result.pricing_completed_exactly =
        result.pricing_completed_exactly && root.pricing_completed_exactly;
    result.support_duration_cuts_generated += root.support_duration_cuts_generated;
    result.support_duration_pruned_labels += root.support_duration_pruned_labels;
    result.support_duration_pruned_columns += root.support_duration_pruned_columns;
    result.support_duration_strong_cuts_generated +=
        root.support_duration_strong_cuts_generated;
    result.support_duration_strong_pruned_labels +=
        root.support_duration_strong_pruned_labels;
    result.support_duration_strong_pruned_columns +=
        root.support_duration_strong_pruned_columns;
    result.completion_lb_pruned_labels += root.completion_lb_pruned_labels;
    result.required_closure_pruned_labels +=
        root.required_closure_pruned_labels;
    result.label_dominance_comparisons += root.label_dominance_comparisons;
    result.label_dominance_pruned_labels += root.label_dominance_pruned_labels;
    result.label_dominance_cross_pickup_pruned_labels +=
        root.label_dominance_cross_pickup_pruned_labels;
    result.label_dominance_inactive_entries_skipped +=
        root.label_dominance_inactive_entries_skipped;
    result.label_dominance_bucket_compactions +=
        root.label_dominance_bucket_compactions;
    result.label_dominance_compacted_entries +=
        root.label_dominance_compacted_entries;
    result.operation_dp_dominance_pruned_states +=
        root.operation_dp_dominance_pruned_states;
    result.support_duration_max_subset_size =
        std::max(result.support_duration_max_subset_size,
                 root.support_duration_max_subset_size);
    result.support_duration_precompute_time_seconds +=
        root.support_duration_precompute_time_seconds;
    result.route_states += root.route_states;
    result.operation_states += root.operation_states;
    result.notes.push_back("root complete=" + std::string(root.complete ? "true" : "false")
        + ", columns=" + std::to_string(root.generated_columns)
        + ", bound=" + num(root.fixed_cap_surrogate));
    result.notes.insert(result.notes.end(), root.notes.begin(), root.notes.end());
    if (!root.complete) return result;

    RyanFosterBranchCandidate candidate = findRyanFosterBranchCandidate(
        instance.V, root.flat_columns, root.z_values, 1e-7);
    if (!candidate.found) {
        result.complete = true;
        result.forbid_child_complete = true;
        result.require_child_complete = true;
        result.notes.push_back("root LP has no fractional Ryan-Foster co-route pair; one-level branch probe is vacuously closed");
        return result;
    }
    result.station_i = candidate.station_i;
    result.station_j = candidate.station_j;
    result.together_value = candidate.together_value;
    result.notes.push_back("selected Ryan-Foster pair=("
        + std::to_string(candidate.station_i) + ","
        + std::to_string(candidate.station_j) + "), together_value="
        + num(candidate.together_value));

    const double elapsed_after_root = std::chrono::duration<double>(Clock::now() - start).count();
    const double remaining = (time_limit_seconds > 0.0)
        ? std::max(0.1, time_limit_seconds - elapsed_after_root) : 0.0;
    const double child_budget = (time_limit_seconds > 0.0) ? std::max(0.1, remaining * 0.5) : 0.0;

    GiniCapBranchRestriction forbid;
    forbid.forbid_together_pairs.push_back({candidate.station_i, candidate.station_j});
    GiniCapColumnGenerationResult forbid_child = runGiniCapColumnGenerationInternal(
        instance, lambda, gamma, -1.0, child_budget, max_iterations,
        forbid, &root.columns_by_vehicle, false,
        std::numeric_limits<double>::infinity(), 1, true, "exact",
        support_duration_pruning_enabled, support_duration_max_subset_size,
        pricing_options);
    result.forbid_child_complete = forbid_child.complete;
    result.bpc_pricing_engine_fallbacks += forbid_child.bpc_pricing_engine_fallbacks;
    result.bpc_nodes_using_ng_dssr += forbid_child.bpc_nodes_using_ng_dssr;
    result.bpc_nodes_using_exact_label += forbid_child.bpc_nodes_using_exact_label;
    result.bpc_nodes_using_hybrid += forbid_child.bpc_nodes_using_hybrid;
    result.bpc_nodes_exactly_priced += forbid_child.bpc_nodes_exactly_priced;
    result.bpc_nodes_dssr_incomplete += forbid_child.bpc_nodes_dssr_incomplete;
    result.bpc_nodes_final_verifier_called += forbid_child.bpc_nodes_final_verifier_called;
    result.bpc_nodes_final_verifier_completed += forbid_child.bpc_nodes_final_verifier_completed;
    result.forbid_child_bound = forbid_child.fixed_cap_surrogate;
    result.pricing_calls += forbid_child.pricing_calls;
    result.generated_columns += forbid_child.generated_columns;
    result.columns_generated_raw += forbid_child.columns_generated_raw;
    result.columns_after_dominance += forbid_child.columns_after_dominance;
    result.columns_dominated += forbid_child.columns_dominated;
    result.dominance_time_seconds += forbid_child.dominance_time_seconds;
    result.dominance_mode = forbid_child.dominance_mode;
    result.dominance_exact_safe =
        result.dominance_exact_safe && forbid_child.dominance_exact_safe;
    result.pricing_negative_columns_found += forbid_child.pricing_negative_columns_found;
    result.pricing_negative_columns_inserted += forbid_child.pricing_negative_columns_inserted;
    result.pricing_negative_columns_dominated += forbid_child.pricing_negative_columns_dominated;
    result.pricing_completed_exactly =
        result.pricing_completed_exactly && forbid_child.pricing_completed_exactly;
    result.support_duration_cuts_generated += forbid_child.support_duration_cuts_generated;
    result.support_duration_pruned_labels += forbid_child.support_duration_pruned_labels;
    result.support_duration_pruned_columns += forbid_child.support_duration_pruned_columns;
    result.support_duration_strong_cuts_generated +=
        forbid_child.support_duration_strong_cuts_generated;
    result.support_duration_strong_pruned_labels +=
        forbid_child.support_duration_strong_pruned_labels;
    result.support_duration_strong_pruned_columns +=
        forbid_child.support_duration_strong_pruned_columns;
    result.completion_lb_pruned_labels += forbid_child.completion_lb_pruned_labels;
    result.required_closure_pruned_labels +=
        forbid_child.required_closure_pruned_labels;
    result.label_dominance_comparisons +=
        forbid_child.label_dominance_comparisons;
    result.label_dominance_pruned_labels +=
        forbid_child.label_dominance_pruned_labels;
    result.label_dominance_cross_pickup_pruned_labels +=
        forbid_child.label_dominance_cross_pickup_pruned_labels;
    result.label_dominance_inactive_entries_skipped +=
        forbid_child.label_dominance_inactive_entries_skipped;
    result.label_dominance_bucket_compactions +=
        forbid_child.label_dominance_bucket_compactions;
    result.label_dominance_compacted_entries +=
        forbid_child.label_dominance_compacted_entries;
    result.operation_dp_dominance_pruned_states +=
        forbid_child.operation_dp_dominance_pruned_states;
    result.support_duration_max_subset_size =
        std::max(result.support_duration_max_subset_size,
                 forbid_child.support_duration_max_subset_size);
    result.support_duration_precompute_time_seconds +=
        forbid_child.support_duration_precompute_time_seconds;
    result.route_states += forbid_child.route_states;
    result.operation_states += forbid_child.operation_states;
    result.notes.push_back("forbid child complete="
        + std::string(forbid_child.complete ? "true" : "false")
        + ", bound=" + num(forbid_child.fixed_cap_surrogate)
        + ", columns=" + std::to_string(forbid_child.generated_columns));

    const double elapsed_after_forbid = std::chrono::duration<double>(Clock::now() - start).count();
    const double require_budget = (time_limit_seconds > 0.0)
        ? std::max(0.1, time_limit_seconds - elapsed_after_forbid) : 0.0;
    GiniCapBranchRestriction require;
    require.require_together_pairs.push_back({candidate.station_i, candidate.station_j});
    GiniCapColumnGenerationResult require_child = runGiniCapColumnGenerationInternal(
        instance, lambda, gamma, -1.0, require_budget, max_iterations,
        require, &root.columns_by_vehicle, false,
        std::numeric_limits<double>::infinity(), 1, true, "exact",
        support_duration_pruning_enabled, support_duration_max_subset_size,
        pricing_options);
    result.require_child_complete = require_child.complete;
    result.bpc_pricing_engine_fallbacks += require_child.bpc_pricing_engine_fallbacks;
    result.bpc_nodes_using_ng_dssr += require_child.bpc_nodes_using_ng_dssr;
    result.bpc_nodes_using_exact_label += require_child.bpc_nodes_using_exact_label;
    result.bpc_nodes_using_hybrid += require_child.bpc_nodes_using_hybrid;
    result.bpc_nodes_exactly_priced += require_child.bpc_nodes_exactly_priced;
    result.bpc_nodes_dssr_incomplete += require_child.bpc_nodes_dssr_incomplete;
    result.bpc_nodes_final_verifier_called += require_child.bpc_nodes_final_verifier_called;
    result.bpc_nodes_final_verifier_completed += require_child.bpc_nodes_final_verifier_completed;
    result.require_child_bound = require_child.fixed_cap_surrogate;
    result.pricing_calls += require_child.pricing_calls;
    result.generated_columns += require_child.generated_columns;
    result.columns_generated_raw += require_child.columns_generated_raw;
    result.columns_after_dominance += require_child.columns_after_dominance;
    result.columns_dominated += require_child.columns_dominated;
    result.dominance_time_seconds += require_child.dominance_time_seconds;
    result.dominance_mode = require_child.dominance_mode;
    result.dominance_exact_safe =
        result.dominance_exact_safe && require_child.dominance_exact_safe;
    result.pricing_negative_columns_found += require_child.pricing_negative_columns_found;
    result.pricing_negative_columns_inserted += require_child.pricing_negative_columns_inserted;
    result.pricing_negative_columns_dominated += require_child.pricing_negative_columns_dominated;
    result.pricing_completed_exactly =
        result.pricing_completed_exactly && require_child.pricing_completed_exactly;
    result.support_duration_cuts_generated += require_child.support_duration_cuts_generated;
    result.support_duration_pruned_labels += require_child.support_duration_pruned_labels;
    result.support_duration_pruned_columns += require_child.support_duration_pruned_columns;
    result.support_duration_strong_cuts_generated +=
        require_child.support_duration_strong_cuts_generated;
    result.support_duration_strong_pruned_labels +=
        require_child.support_duration_strong_pruned_labels;
    result.support_duration_strong_pruned_columns +=
        require_child.support_duration_strong_pruned_columns;
    result.completion_lb_pruned_labels += require_child.completion_lb_pruned_labels;
    result.required_closure_pruned_labels +=
        require_child.required_closure_pruned_labels;
    result.label_dominance_comparisons +=
        require_child.label_dominance_comparisons;
    result.label_dominance_pruned_labels +=
        require_child.label_dominance_pruned_labels;
    result.label_dominance_cross_pickup_pruned_labels +=
        require_child.label_dominance_cross_pickup_pruned_labels;
    result.label_dominance_inactive_entries_skipped +=
        require_child.label_dominance_inactive_entries_skipped;
    result.label_dominance_bucket_compactions +=
        require_child.label_dominance_bucket_compactions;
    result.label_dominance_compacted_entries +=
        require_child.label_dominance_compacted_entries;
    result.operation_dp_dominance_pruned_states +=
        require_child.operation_dp_dominance_pruned_states;
    result.support_duration_max_subset_size =
        std::max(result.support_duration_max_subset_size,
                 require_child.support_duration_max_subset_size);
    result.support_duration_precompute_time_seconds +=
        require_child.support_duration_precompute_time_seconds;
    result.route_states += require_child.route_states;
    result.operation_states += require_child.operation_states;
    result.notes.push_back("require child complete="
        + std::string(require_child.complete ? "true" : "false")
        + ", bound=" + num(require_child.fixed_cap_surrogate)
        + ", columns=" + std::to_string(require_child.generated_columns));

    result.complete = result.root_complete &&
        result.forbid_child_complete && result.require_child_complete;
    return result;
}

GiniCapTreeResult runGiniCapBranchPriceTreeDiagnostic(
    const Instance& instance,
    double lambda,
    double gamma,
    double gamma_floor,
    double time_limit_seconds,
    int max_iterations,
    int max_nodes,
    const std::vector<RoutePlan>* seed_routes,
    bool use_combined_gini_lower_bound,
    double objective_cutoff,
    int warmstart_level,
    double early_stop_lower_bound,
    int pricing_return_columns,
    bool column_dominance_enabled,
    const std::string& column_dominance_mode,
    bool projection_bound_enabled,
    bool penalty_domain_tightening_enabled,
    bool movement_domain_tightening_enabled,
    bool support_duration_pruning_enabled,
    int support_duration_max_subset_size,
    bool branch_inventory_enabled,
    double branch_inventory_priority,
    bool branch_operation_mode_enabled,
    const std::string& branch_selection_mode,
    int strong_branching_candidates,
    double strong_branching_time_seconds,
    bool reliability_branching_enabled,
    const PricingOptions& pricing_options) {
    const auto start = Clock::now();
    struct TreeNode {
        GiniCapBranchRestriction branch;
        std::vector<std::vector<RouteLoadColumn>> columns_by_vehicle;
        int depth = 0;
        double inherited_lower_bound = 0.0;
        int node_id = 0;
        int parent_id = -1;
    };

    GiniCapTreeResult result;
    result.columns_by_vehicle.assign(instance.M, {});
    initializeBpcPricingFields(result, pricing_options);
    result.pricing_best_reduced_cost_any =
        std::numeric_limits<double>::infinity();
    result.pricing_best_new_reduced_cost =
        std::numeric_limits<double>::infinity();
    result.gamma = gamma;
    result.gamma_floor = gamma_floor;
    result.branch_selection_mode = branch_selection_mode;
    (void)strong_branching_time_seconds;
    (void)reliability_branching_enabled;
    result.notes.push_back("branch selection mode=" + branch_selection_mode
        + ", inventory_branching=" + std::string(branch_inventory_enabled ? "true" : "false")
        + ", operation_mode_branching=" + std::string(branch_operation_mode_enabled ? "true" : "false")
        + ", strong_branching_candidates=" + std::to_string(strong_branching_candidates)
        + "; strong mode uses certificate-neutral cheap child-bound scoring in this pass");
    result.global_lower_bound = std::numeric_limits<double>::infinity();
    ColumnDominanceOptions dominance_options;
    dominance_options.enabled = column_dominance_enabled;
    dominance_options.mode = parseColumnDominanceMode(column_dominance_mode);
    dominance_options.exact_safe = true;
    dominance_options = normalizeColumnDominanceOptions(dominance_options);
    result.dominance_mode = columnDominanceModeName(dominance_options.mode);
    result.dominance_exact_safe = dominance_options.exact_safe;
    const double bound_gamma = (gamma_floor >= 0.0) ? gamma_floor : gamma;
    const bool cutoff_mode = use_combined_gini_lower_bound &&
        std::isfinite(objective_cutoff);
    const ResourceRelaxationBound resource_bound =
        use_combined_gini_lower_bound
            ? computeResourceRelaxationBound(instance, lambda)
            : ResourceRelaxationBound{};
    result.resource_penalty_lower_bound = resource_bound.penalty_lower_bound;
    result.resource_objective_lower_bound = resource_bound.objective_lower_bound;
    result.resource_total_pickup_limit = resource_bound.total_pickup_limit;
    const double root_s_upper = ratioSumUpperBound(instance, GiniCapBranchRestriction{});
    ObjectiveParts initial_parts = computeObjectiveParts(instance, instance.initial, lambda);
    result.best_integer_columns = 0;
    result.best_integer_surrogate = std::numeric_limits<double>::infinity();
    std::vector<std::vector<RouteLoadColumn>> root_columns(instance.M);
    if (initial_parts.G <= gamma + 1e-9 &&
        (gamma_floor < 0.0 || initial_parts.G >= gamma_floor - 1e-9)) {
        result.has_integer_incumbent = true;
        result.best_integer_surrogate = use_combined_gini_lower_bound
            ? lowerBoundMetricFromParts(instance, initial_parts, lambda, bound_gamma,
                                        true, root_s_upper)
            : bound_gamma + lambda * initial_parts.P;
        result.incumbent_source = "empty-route incumbent";
        result.best_integer_parts = initial_parts;
        result.best_final_inventory = instance.initial;
        result.best_routes = emptyRoutes(instance);
    } else {
        result.incumbent_source = "none";
    }
    if (seed_routes != nullptr && !seed_routes->empty()) {
        Verification seed_verification = verifySolution(instance, *seed_routes, lambda);
        if (seed_verification.feasible) {
            std::vector<std::vector<RouteLoadColumn>> seed_columns =
                columnsFromSeedRoutes(instance, *seed_routes);
            long long seed_column_count = 0;
            for (int k = 0; k < instance.M; ++k) {
                for (const RouteLoadColumn& col : seed_columns[k]) {
                    if (!hasColumn(root_columns[k], col)) root_columns[k].push_back(col);
                }
                seed_column_count += static_cast<long long>(seed_columns[k].size());
            }
            result.notes.push_back("accepted verified seed-route columns for interval pricing warm start: columns="
                + std::to_string(seed_column_count)
                + ", seed_G=" + num(seed_verification.G)
                + ", floor=" + num(gamma_floor)
                + ", gamma=" + num(gamma));
        }
        if (seed_verification.feasible &&
            seed_verification.G <= gamma + 1e-9 &&
            (gamma_floor < 0.0 || seed_verification.G >= gamma_floor - 1e-9)) {
            const ObjectiveParts seed_parts =
                computeObjectiveParts(instance, seed_verification.final_inventory, lambda);
            const double seed_surrogate = use_combined_gini_lower_bound
                ? lowerBoundMetricFromParts(instance, seed_parts, lambda, bound_gamma,
                                            true, root_s_upper)
                : bound_gamma + lambda * seed_verification.P;
            if (!result.has_integer_incumbent ||
                seed_surrogate < result.best_integer_surrogate - 1e-9) {
                result.has_integer_incumbent = true;
                result.best_integer_surrogate = seed_surrogate;
                result.best_integer_columns = 0;
                for (const auto& cols : root_columns) {
                    result.best_integer_columns += static_cast<int>(cols.size());
                }
                result.incumbent_source = "seed route incumbent";
                result.best_final_inventory = seed_verification.final_inventory;
                result.best_integer_parts = seed_parts;
                result.best_routes = *seed_routes;
            }
            long long seed_columns = 0;
            for (const auto& cols : root_columns) seed_columns += static_cast<long long>(cols.size());
            result.notes.push_back("accepted fixed-cap seed routes: objective="
                + num(seed_verification.objective)
                + ", G=" + num(seed_verification.G)
                + ", P=" + num(seed_verification.P)
                + ", seed_columns=" + std::to_string(seed_columns));
        } else {
            result.notes.push_back("discarded supplied fixed-cap seed routes: feasible="
                + std::string(seed_verification.feasible ? "true" : "false")
                + ", G=" + num(seed_verification.G)
                + ", floor=" + num(gamma_floor)
                + ", gamma=" + num(gamma));
        }
    }
    const long long columns_before_warm_start = [&]() {
        long long count = 0;
        for (const auto& cols : root_columns) count += static_cast<long long>(cols.size());
        return count;
    }();
    appendWarmStartColumns(instance, root_columns, warmstart_level);
    if (dominance_options.enabled) {
        for (auto& cols : root_columns) {
            ColumnDominanceStats stats;
            applyColumnDominance(cols, dominance_options, stats);
            result.columns_generated_raw += stats.columns_generated_raw;
            result.columns_after_dominance += stats.columns_after_dominance;
            result.columns_dominated += stats.columns_dominated;
            result.dominance_input_columns += stats.dominance_input_columns;
            result.dominance_kept_columns += stats.dominance_kept_columns;
            result.dominance_removed_columns += stats.dominance_removed_columns;
            result.dominance_removed_existing_projection +=
                stats.dominance_removed_existing_projection;
            result.dominance_removed_candidate_projection +=
                stats.dominance_removed_candidate_projection;
            result.dominance_time_seconds += stats.dominance_time_seconds;
        }
    }
    const long long columns_after_warm_start = [&]() {
        long long count = 0;
        for (const auto& cols : root_columns) count += static_cast<long long>(cols.size());
        return count;
    }();
    if (columns_after_warm_start > columns_before_warm_start) {
        result.notes.push_back("added generic singleton and pickup-drop warm-start route-load columns: mode="
            + std::string(warmstart_level >= 2 ? "full" : "sparse")
            + ", added="
            + std::to_string(columns_after_warm_start - columns_before_warm_start)
            + ", total_root_columns=" + std::to_string(columns_after_warm_start));
    } else if (warmstart_level <= 0) {
        result.notes.push_back("generic singleton and pickup-drop warm-start route-load columns disabled; using seed/priced columns only");
    }
    result.notes.push_back("closed-column dominance: enabled="
        + std::string(dominance_options.enabled ? "true" : "false")
        + ", mode=" + result.dominance_mode
        + ", exact_safe=" + std::string(result.dominance_exact_safe ? "true" : "false")
        + ", root_columns_dominated=" + std::to_string(result.columns_dominated));
    result.notes.push_back(gamma_floor >= 0.0
        ? "Fixed-Gini-interval branch-price tree diagnostic solves closed LP/pricing nodes and branches on Ryan-Foster co-route pairs. Bounds are for the valid interval lower-bound metric gamma_floor+lambda*P."
        : "Fixed-Gini-cap branch-price tree diagnostic solves closed LP/pricing nodes and branches on Ryan-Foster co-route pairs. Bounds are for the fixed-cap surrogate gamma+lambda*P.");
    if (use_combined_gini_lower_bound) {
        result.notes.push_back("Tree node bounds use g_lb+lambda*P, where g_lb is constrained by both the interval floor and H/(V*S_max).");
        result.notes.push_back(resource_bound.note.empty()
            ? "resource relaxation lower bound unavailable; using zero"
            : resource_bound.note);
    }
    if (cutoff_mode) {
        result.notes.push_back("Incumbent-cutoff certification mode is active: LP nodes with lower bound at least the verified incumbent objective are fathomed, and route-integer leaves are accounted with their independently recomputed true objective.");
    }
    if (std::isfinite(early_stop_lower_bound)) {
        result.notes.push_back("Target lower-bound mode is active: the tree may return incomplete once its valid open-node lower bound reaches "
            + num(early_stop_lower_bound)
            + "; open nodes remain counted and this is not a full interval closure");
    }
    if (pricing_return_columns > 1) {
        result.notes.push_back("Multi-column exact pricing mode is active: a completed pricing pass may return up to "
            + std::to_string(pricing_return_columns)
            + " negative route-load columns. Early negative stops are used only to add columns and never to certify node closure.");
    }
    if (result.has_integer_incumbent) {
        result.notes.push_back("initial fixed-cap incumbent from empty routes: surrogate="
            + num(result.best_integer_surrogate));
    } else {
        result.notes.push_back("empty-route solution violates supplied fixed Gini cap; starting without a fixed-cap integer incumbent");
    }

    auto exportColumn = [&](const RouteLoadColumn& column,
                            const std::string& source) {
        if (column.vehicle < 0 || column.vehicle >= instance.M) return;
        result.columns_by_vehicle[column.vehicle].push_back(column);
        result.flat_columns.push_back(column);
        ++result.columns_exported_from_tree;
        if (source == "warmstart") {
            result.warm_start_columns.push_back(column);
            ++result.columns_exported_from_warmstart;
        } else if (source == "pricing") {
            result.priced_columns_added.push_back(column);
            ++result.columns_exported_from_pricing;
        } else if (source == "integer_leaf") {
            result.integer_leaf_columns.push_back(column);
            ++result.columns_exported_from_integer_leaves;
        }
    };
    for (const auto& cols : root_columns) {
        for (const RouteLoadColumn& col : cols) exportColumn(col, "warmstart");
    }

    std::deque<TreeNode> open;
    open.push_back(TreeNode{GiniCapBranchRestriction{},
                            root_columns,
                            0,
                            std::max(0.0, resource_bound.objective_lower_bound),
                            0,
                            -1});
    int next_node_id = 1;
    result.notes.push_back("branch-price tree nodes are scheduled by best inherited lower bound; this changes search order only, not certificate conditions");

    auto remainingTime = [&]() {
        if (time_limit_seconds <= 0.0) return 0.0;
        const double elapsed = std::chrono::duration<double>(Clock::now() - start).count();
        return std::max(0.0, time_limit_seconds - elapsed);
    };
    auto effectiveLowerBound = [&](double value) {
        if (std::isfinite(value)) {
            value = std::max(value, resource_bound.objective_lower_bound);
        }
        if (cutoff_mode && std::isfinite(value)) {
            return std::min(value, objective_cutoff);
        }
        return value;
    };
    auto addTerminalLowerBound = [&](double value) {
        const double effective = effectiveLowerBound(value);
        if (std::isfinite(effective)) {
            result.global_lower_bound = std::min(result.global_lower_bound, effective);
        }
    };
    auto bestOpenNode = [&]() {
        return std::min_element(open.begin(), open.end(),
            [](const TreeNode& a, const TreeNode& b) {
                if (a.inherited_lower_bound < b.inherited_lower_bound - 1e-12) return true;
                if (a.inherited_lower_bound > b.inherited_lower_bound + 1e-12) return false;
                return a.depth < b.depth;
            });
    };
    auto bestOpenLowerBound = [&]() {
        if (open.empty()) return std::numeric_limits<double>::infinity();
        return bestOpenNode()->inherited_lower_bound;
    };
    auto currentTreeLowerBound = [&]() {
        double lb = result.global_lower_bound;
        for (const TreeNode& n : open) {
            lb = std::min(lb, effectiveLowerBound(n.inherited_lower_bound));
        }
        if (!std::isfinite(lb)) return std::numeric_limits<double>::infinity();
        return lb;
    };
    auto finishIncomplete = [&](const std::string& reason,
                                double node_lb,
                                int current_extra,
                                bool lower_bound_valid = true) {
        result.hit_time_limit = reason.find("time") != std::string::npos;
        result.lower_bound_valid = result.lower_bound_valid && lower_bound_valid;
        result.open_nodes = static_cast<int>(open.size()) + current_extra;
        result.global_lower_bound = std::min(result.global_lower_bound,
                                            effectiveLowerBound(node_lb));
        for (const TreeNode& n : open) {
            result.global_lower_bound = std::min(result.global_lower_bound,
                                                effectiveLowerBound(n.inherited_lower_bound));
        }
        if (!std::isfinite(result.global_lower_bound)) result.global_lower_bound = 0.0;
        result.notes.push_back(reason + "; global_lower_bound_valid="
            + std::string(result.lower_bound_valid ? "true" : "false"));
    };

    while (!open.empty()) {
        if (std::isfinite(early_stop_lower_bound)) {
            const double current_lb = currentTreeLowerBound();
            if (current_lb >= early_stop_lower_bound - 1e-9) {
                finishIncomplete("target lower bound reached before full tree closure; target="
                                 + num(early_stop_lower_bound),
                                 current_lb, 0);
                return result;
            }
        }
        if (max_nodes > 0 && result.nodes_solved >= max_nodes) {
            finishIncomplete("maximum branch-price nodes reached before tree closure",
                             bestOpenLowerBound(), 0);
            return result;
        }
        if (time_limit_seconds > 0.0 && remainingTime() <= 0.0) {
            finishIncomplete("time limit reached before next branch-price node",
                             bestOpenLowerBound(), 0);
            return result;
        }

        auto next_node = bestOpenNode();
        TreeNode node = std::move(*next_node);
        open.erase(next_node);
        result.max_depth = std::max(result.max_depth, node.depth);
        if (use_combined_gini_lower_bound) {
            std::vector<int> inventory_lower(instance.V + 1, 0);
            std::vector<int> inventory_upper(instance.V + 1, 0);
            for (int station = 1; station <= instance.V; ++station) {
                inventory_upper[station] = instance.capacity[station];
                if (station < static_cast<int>(node.branch.inventory_lower.size())) {
                    inventory_lower[station] =
                        std::max(inventory_lower[station],
                                 node.branch.inventory_lower[station]);
                }
                if (station < static_cast<int>(node.branch.inventory_upper.size())) {
                    inventory_upper[station] =
                        std::min(inventory_upper[station],
                                 node.branch.inventory_upper[station]);
                }
            }
            if (movement_domain_tightening_enabled) {
                MovementReachabilityTighteningResult move_tighten =
                    tightenInventoryIntervalsByMovementReachability(
                        instance, inventory_lower, inventory_upper);
                result.movement_tightening_time_seconds += move_tighten.time_seconds;
                result.movement_domains_tightened_count +=
                    move_tighten.domains_tightened_count;
                result.movement_domain_width_before +=
                    move_tighten.total_domain_width_before;
                result.movement_domain_width_after +=
                    move_tighten.total_domain_width_after;
                result.movement_unreachable_station_count +=
                    move_tighten.unreachable_station_count;
            }
            const auto tighten_start = Clock::now();
            PenaltyDomainTighteningResult tighten;
            if (cutoff_mode && penalty_domain_tightening_enabled) {
                tighten = tightenInventoryIntervalsByPenaltyBudget(
                    instance, lambda, gamma_floor, objective_cutoff,
                    inventory_lower, inventory_upper);
            } else {
                tighten.total_domain_width_before = 0;
                tighten.total_domain_width_after = 0;
                for (int station = 1; station <= instance.V; ++station) {
                    const int width = std::max(0, inventory_upper[station] -
                                                   inventory_lower[station]);
                    tighten.total_domain_width_before += width;
                    tighten.total_domain_width_after += width;
                }
            }
            result.penalty_tightening_time_seconds +=
                std::chrono::duration<double>(Clock::now() - tighten_start).count();
            result.penalty_budget = tighten.penalty_budget;
            result.domains_tightened_count += tighten.domains_tightened_count;
            result.total_domain_width_before += tighten.total_domain_width_before;
            result.total_domain_width_after += tighten.total_domain_width_after;
            if (tighten.fathomed_by_budget) {
                ++result.pruned_by_bound;
                addTerminalLowerBound(objective_cutoff);
                result.notes.push_back("node fathomed by penalty-budget domain tightening before LP at depth="
                    + std::to_string(node.depth));
                continue;
            }
            bool empty_domain = false;
            for (int station = 1; station <= instance.V; ++station) {
                if (inventory_lower[station] > inventory_upper[station]) {
                    empty_domain = true;
                    break;
                }
            }
            if (empty_domain) {
                ++result.pruned_by_bound;
                addTerminalLowerBound(cutoff_mode ? objective_cutoff
                                                  : node.inherited_lower_bound);
                result.notes.push_back("node fathomed by empty branched final-inventory interval before LP at depth="
                    + std::to_string(node.depth));
                continue;
            }
            if (projection_bound_enabled) {
                const auto projection_start = Clock::now();
                InventoryRatioProjectionBound projection =
                    computeInventoryRatioProjectionBound(
                        instance, lambda, inventory_lower, inventory_upper,
                        gamma_floor, "global");
                result.projection_bound_time_seconds +=
                    std::chrono::duration<double>(Clock::now() - projection_start).count();
                if (projection.valid) {
                    result.projection_bound_best_value =
                        std::max(result.projection_bound_best_value,
                                 projection.objective_lower_bound);
                    result.projection_bound_scope = projection.bound_scope;
                    if (cutoff_mode &&
                        projection.objective_lower_bound >= objective_cutoff - 1e-9) {
                        ++result.pruned_by_bound;
                        ++result.projection_bound_prunes;
                        addTerminalLowerBound(objective_cutoff);
                        result.notes.push_back("node fathomed by inventory-ratio projection lower bound before LP at depth="
                            + std::to_string(node.depth)
                            + ", projection_lb=" + num(projection.objective_lower_bound)
                            + ", cutoff=" + num(objective_cutoff));
                        continue;
                    }
                    node.inherited_lower_bound =
                        std::max(node.inherited_lower_bound,
                                 projection.objective_lower_bound);
                }
            }
        }
        const double node_budget = (time_limit_seconds > 0.0)
            ? std::max(0.1, remainingTime()) : 0.0;
        GiniCapColumnGenerationResult lp_node = runGiniCapColumnGenerationInternal(
            instance, lambda, gamma, gamma_floor, node_budget, max_iterations,
            node.branch, &node.columns_by_vehicle, use_combined_gini_lower_bound,
            objective_cutoff, pricing_return_columns,
            column_dominance_enabled, column_dominance_mode,
            support_duration_pruning_enabled, support_duration_max_subset_size,
            pricing_options);
        ++result.nodes_solved;
        addStats(result, lp_node);
        for (const RouteLoadColumn& col : lp_node.flat_columns) {
            exportColumn(col, "pricing");
        }
        int node_pricing_call = 0;
        for (const std::string& pricing_trace : lp_node.pricing_trace_json_objects) {
            std::ostringstream wrapped;
            wrapped << "{"
                    << "\"node_id\": " << node.node_id
                    << ", \"parent_id\": " << node.parent_id
                    << ", \"tree_node_sequence\": " << result.nodes_solved
                    << ", \"depth\": " << node.depth
                    << ", \"node_pricing_call\": " << node_pricing_call++
                    << ", \"pricing_call\": " << pricing_trace
                    << "}";
            result.pricing_trace_json_objects.push_back(wrapped.str());
        }
        auto appendNodeTrace = [&](const std::string& outcome,
                                   const std::string& branch_decision,
                                   const std::string& not_closed_reason) {
            std::ostringstream node_trace;
            node_trace << std::setprecision(12)
                       << "{"
                       << "\"node_id\": " << node.node_id
                       << ", \"parent_id\": " << node.parent_id
                       << ", \"tree_node_sequence\": " << result.nodes_solved
                       << ", \"depth\": " << node.depth
                       << ", \"branch_restrictions\": \""
                       << jsonEscapeCg(branchDescription(node.branch)) << "\""
                       << ", \"lp_rmp_objective\": "
                       << jsonNumberCg(lp_node.fixed_cap_surrogate)
                       << ", \"inherited_lower_bound\": "
                       << jsonNumberCg(node.inherited_lower_bound)
                       << ", \"best_node_lower_bound\": "
                       << jsonNumberCg(lp_node.fixed_cap_surrogate)
                       << ", \"cg_iterations\": " << lp_node.iterations
                       << ", \"active_columns\": " << lp_node.generated_columns
                       << ", \"cuts\": " << lp_node.cuts_added
                       << ", \"branching_decision\": \""
                       << jsonEscapeCg(branch_decision) << "\""
                       << ", \"pricing_closed\": "
                       << (lp_node.complete ? "true" : "false")
                       << ", \"not_closed_reason\": \""
                       << jsonEscapeCg(not_closed_reason) << "\""
                       << ", \"outcome\": \"" << jsonEscapeCg(outcome) << "\""
                       << "}";
            result.node_trace_json_objects.push_back(node_trace.str());
        };

        std::ostringstream solved_note;
        solved_note << "node " << result.nodes_solved
                    << " depth=" << node.depth
                    << " branch=" << branchDescription(node.branch)
                    << " complete=" << (lp_node.complete ? "true" : "false")
                    << " bound=" << lp_node.fixed_cap_surrogate
                    << " columns=" << lp_node.generated_columns;
        result.notes.push_back(solved_note.str());
        for (const std::string& note : lp_node.notes) {
            if (note.find("phase-I") != std::string::npos ||
                note.find("artificial") != std::string::npos ||
                note.find("entering phase") != std::string::npos) {
                result.notes.push_back("node " + std::to_string(result.nodes_solved)
                    + " detail: " + note);
            }
        }

        if (!lp_node.complete) {
            result.notes.insert(result.notes.end(), lp_node.notes.begin(), lp_node.notes.end());
            appendNodeTrace("unresolved", "none", "pricing_did_not_close");
            finishIncomplete("node pricing did not close; tree remains open",
                             node.inherited_lower_bound, 1);
            result.notes.push_back("unfinished node contributes only its inherited lower bound; the unclosed restricted-master objective is not used for certification");
            return result;
        }

        if (lp_node.infeasible) {
            result.notes.push_back("infeasible branch-price node fathomed at depth="
                + std::to_string(node.depth));
            appendNodeTrace("infeasible_fathomed", "none", "");
            continue;
        }

        if (cutoff_mode &&
            lp_node.fixed_cap_surrogate >= objective_cutoff - 1e-9) {
            ++result.pruned_by_bound;
            addTerminalLowerBound(objective_cutoff);
            result.notes.push_back("node fathomed by verified incumbent objective cutoff at depth="
                + std::to_string(node.depth)
                + ", node_bound=" + num(lp_node.fixed_cap_surrogate)
                + ", cutoff=" + num(objective_cutoff));
            appendNodeTrace("bound_fathomed", "none", "");
            continue;
        }

        if (!cutoff_mode && result.has_integer_incumbent &&
            lp_node.fixed_cap_surrogate >= result.best_integer_surrogate - 1e-9) {
            ++result.pruned_by_bound;
            addTerminalLowerBound(lp_node.fixed_cap_surrogate);
            result.notes.push_back("node fathomed by incumbent bound at depth="
                + std::to_string(node.depth)
                + ", node_bound=" + num(lp_node.fixed_cap_surrogate)
                + ", incumbent=" + num(result.best_integer_surrogate));
            appendNodeTrace("bound_fathomed", "none", "");
            continue;
        }

        if (zIntegral(lp_node.z_values)) {
            ++result.integer_leaves;
            const int selected = countSelectedColumns(lp_node.z_values);
            std::vector<int> leaf_inventory(instance.V + 1, 0);
            for (int i = 1; i <= instance.V; ++i) {
                leaf_inventory[i] = static_cast<int>(std::llround(lp_node.y_values[i]));
            }
            leaf_inventory[0] = instance.initial[0];
            ObjectiveParts leaf_parts =
                computeObjectiveParts(instance, leaf_inventory, lambda);
            if (objectivePartsInGiniInterval(leaf_parts, gamma_floor, gamma)) {
                addTerminalLowerBound(cutoff_mode
                    ? leaf_parts.objective : lp_node.fixed_cap_surrogate);
                std::vector<int> selected_by_vehicle(instance.M, -1);
                for (int c = 0; c < static_cast<int>(lp_node.flat_columns.size()); ++c) {
                    if (lp_node.z_values[c] <= 1.0 - 1e-7) continue;
                    const RouteLoadColumn& col = lp_node.flat_columns[c];
                    exportColumn(col, "integer_leaf");
                    if (col.vehicle >= 0 && col.vehicle < instance.M) {
                        selected_by_vehicle[col.vehicle] =
                            findColumnIndex(lp_node.columns_by_vehicle[col.vehicle], col);
                    }
                }
                const double candidate_value = cutoff_mode
                    ? leaf_parts.objective : lp_node.fixed_cap_surrogate;
                const double incumbent_value = (cutoff_mode && result.has_integer_incumbent)
                    ? result.best_integer_parts.objective : result.best_integer_surrogate;
                if (!result.has_integer_incumbent ||
                    candidate_value < incumbent_value - 1e-9) {
                    result.has_integer_incumbent = true;
                    result.best_integer_surrogate = lp_node.fixed_cap_surrogate;
                    result.best_integer_columns = selected;
                    result.incumbent_source = "integer leaf at depth " + std::to_string(node.depth);
                    result.best_final_inventory = std::move(leaf_inventory);
                    result.best_integer_parts = leaf_parts;
                    result.best_routes = routesFromSelection(
                        instance, lp_node.columns_by_vehicle, selected_by_vehicle);
                }
            } else if (!objectivePartsInGiniInterval(leaf_parts, gamma_floor, gamma)) {
                result.notes.push_back("integer leaf true G=" + num(leaf_parts.G)
                    + " lies outside requested Gini interval; node kept only as a lower-bound leaf");
            }
            std::ostringstream leaf_note;
            leaf_note << "integer leaf at depth=" << node.depth
                      << ", surrogate=" << lp_node.fixed_cap_surrogate
                      << ", selected_columns=" << selected;
            result.notes.push_back(leaf_note.str());
            appendNodeTrace("integer_leaf", "none", "");
            continue;
        }

        InventoryBranchCandidate inventory_candidate =
            findInventoryBranchCandidate(lp_node.y_values, 1e-7);
        OperationModeBranchCandidate operation_candidate =
            findOperationModeBranchCandidate(instance.V, lp_node.flat_columns,
                                             lp_node.z_values, 1e-7);
        RyanFosterBranchCandidate candidate = findRyanFosterBranchCandidate(
            instance.V, lp_node.flat_columns, lp_node.z_values, 1e-7);
        StationBranchCandidate station_candidate = findStationBranchCandidate(
            instance.V, lp_node.flat_columns, lp_node.z_values, 1e-7);

        if (inventory_candidate.found) ++result.inventory_branch_candidates;
        if (operation_candidate.found) ++result.operation_mode_branch_candidates;

        auto childLower = [&]() {
            return std::max(lp_node.fixed_cap_surrogate,
                            resource_bound.objective_lower_bound);
        };
        auto branchRyanFoster = [&]() {
            ++result.branched_nodes;
            result.branch_nodes_by_type_ryan_foster += 2;
            result.selected_branch_type = "ryan_foster";
            result.selected_branch_score = candidate.fractional_score;
            result.selected_branch_child_lb_left = childLower();
            result.selected_branch_child_lb_right = childLower();
            std::ostringstream branch_note;
            branch_note << "branching on pair=(" << candidate.station_i << ","
                        << candidate.station_j << ") at depth=" << node.depth
                        << ", together_value=" << candidate.together_value;
            result.notes.push_back(branch_note.str());

            GiniCapBranchRestriction forbid = node.branch;
            forbid.forbid_together_pairs.push_back({candidate.station_i, candidate.station_j});
            open.push_back(TreeNode{forbid, lp_node.columns_by_vehicle,
                                    node.depth + 1, childLower(),
                                    next_node_id++, node.node_id});

            GiniCapBranchRestriction require = node.branch;
            require.require_together_pairs.push_back({candidate.station_i, candidate.station_j});
            open.push_back(TreeNode{require, lp_node.columns_by_vehicle,
                                    node.depth + 1, childLower(),
                                    next_node_id++, node.node_id});
            appendNodeTrace("branched", "ryan_foster", "");
        };
        auto branchStation = [&]() {
            ++result.branched_nodes;
            std::ostringstream branch_note;
            branch_note << "branching on station=" << station_candidate.station
                        << " served value=" << station_candidate.value
                        << " at depth=" << node.depth;
            result.notes.push_back(branch_note.str());

            GiniCapBranchRestriction unserved = node.branch;
            unserved.forbid_stations.push_back(station_candidate.station);
            open.push_back(TreeNode{unserved, lp_node.columns_by_vehicle,
                                    node.depth + 1, childLower(),
                                    next_node_id++, node.node_id});

            GiniCapBranchRestriction served = node.branch;
            served.require_stations.push_back(station_candidate.station);
            open.push_back(TreeNode{served, lp_node.columns_by_vehicle,
                                    node.depth + 1, childLower(),
                                    next_node_id++, node.node_id});
            appendNodeTrace("branched", "station_served_unserved", "");
        };
        auto branchInventory = [&]() {
            ++result.branched_nodes;
            result.inventory_branch_nodes_created += 2;
            result.branch_nodes_by_type_inventory += 2;
            result.inventory_branch_station = inventory_candidate.station;
            result.inventory_branch_value = inventory_candidate.value;
            result.inventory_branch_max_depth =
                std::max(result.inventory_branch_max_depth, node.depth + 1);
            result.selected_branch_type = "inventory";
            result.selected_branch_score = inventory_candidate.fractional_score;
            result.selected_branch_child_lb_left = childLower();
            result.selected_branch_child_lb_right = childLower();
            const int floor_value = static_cast<int>(std::floor(inventory_candidate.value));
            const int ceil_value = static_cast<int>(std::ceil(inventory_candidate.value));
            result.inventory_branch_left_bound = floor_value;
            result.inventory_branch_right_bound = ceil_value;
            std::ostringstream branch_note;
            branch_note << "branching on inventory Y_" << inventory_candidate.station
                        << "=" << inventory_candidate.value
                        << " with <= " << floor_value
                        << " / >= " << ceil_value
                        << " at depth=" << node.depth;
            result.notes.push_back(branch_note.str());

            GiniCapBranchRestriction low = node.branch;
            if (low.inventory_upper.empty()) {
                low.inventory_upper.assign(instance.V + 1,
                                           std::numeric_limits<int>::max() / 2);
            }
            low.inventory_upper[inventory_candidate.station] =
                std::min(low.inventory_upper[inventory_candidate.station], floor_value);
            if (!low.inventory_lower.empty() &&
                low.inventory_lower[inventory_candidate.station] >
                    low.inventory_upper[inventory_candidate.station]) {
                ++result.inventory_branch_pruned_nodes;
            } else {
                open.push_back(TreeNode{low, lp_node.columns_by_vehicle,
                                        node.depth + 1, childLower(),
                                        next_node_id++, node.node_id});
            }

            GiniCapBranchRestriction high = node.branch;
            if (high.inventory_lower.empty()) {
                high.inventory_lower.assign(instance.V + 1,
                                            std::numeric_limits<int>::min() / 2);
            }
            high.inventory_lower[inventory_candidate.station] =
                std::max(high.inventory_lower[inventory_candidate.station], ceil_value);
            if (!high.inventory_upper.empty() &&
                high.inventory_lower[inventory_candidate.station] >
                    high.inventory_upper[inventory_candidate.station]) {
                ++result.inventory_branch_pruned_nodes;
            } else {
                open.push_back(TreeNode{high, lp_node.columns_by_vehicle,
                                        node.depth + 1, childLower(),
                                        next_node_id++, node.node_id});
            }
            appendNodeTrace("branched", "final_inventory", "");
        };
        auto branchOperation = [&]() {
            ++result.branched_nodes;
            result.operation_mode_branch_nodes_created += 2;
            result.branch_nodes_by_type_operation_mode += 2;
            result.operation_mode_branch_station = operation_candidate.station;
            result.operation_mode_branch_type = "forbid_pickup_vs_forbid_drop";
            result.selected_branch_type = "operation_mode";
            result.selected_branch_score = operation_candidate.score;
            result.selected_branch_child_lb_left = childLower();
            result.selected_branch_child_lb_right = childLower();
            std::ostringstream branch_note;
            branch_note << "branching on operation mode station="
                        << operation_candidate.station
                        << " pickup_mass=" << operation_candidate.pickup_mass
                        << " drop_mass=" << operation_candidate.drop_mass
                        << " at depth=" << node.depth;
            result.notes.push_back(branch_note.str());

            GiniCapBranchRestriction no_pickup = node.branch;
            no_pickup.forbid_pickup_stations.push_back(operation_candidate.station);
            open.push_back(TreeNode{no_pickup, lp_node.columns_by_vehicle,
                                    node.depth + 1, childLower(),
                                    next_node_id++, node.node_id});

            GiniCapBranchRestriction no_drop = node.branch;
            no_drop.forbid_drop_stations.push_back(operation_candidate.station);
            open.push_back(TreeNode{no_drop, lp_node.columns_by_vehicle,
                                    node.depth + 1, childLower(),
                                    next_node_id++, node.node_id});
            appendNodeTrace("branched", "operation_mode", "");
        };

        auto mode = branch_selection_mode;
        std::transform(mode.begin(), mode.end(), mode.begin(), [](unsigned char c) {
            return static_cast<char>(std::tolower(c));
        });
        std::string chosen;
        if (mode == "strong") {
            ++result.strong_branching_calls;
            struct ScoredBranch { std::string type; double score = 0.0; };
            std::vector<ScoredBranch> scored;
            if (branch_inventory_enabled && inventory_candidate.found) {
                scored.push_back({"inventory",
                                  inventory_candidate.fractional_score *
                                      std::max(0.0, branch_inventory_priority)});
            }
            if (branch_operation_mode_enabled && operation_candidate.found) {
                scored.push_back({"operation_mode", operation_candidate.score});
            }
            if (candidate.found) scored.push_back({"ryan_foster", candidate.fractional_score});
            if (station_candidate.found) scored.push_back({"station", station_candidate.fractional_score});
            std::sort(scored.begin(), scored.end(),
                      [](const ScoredBranch& a, const ScoredBranch& b) {
                          if (std::fabs(a.score - b.score) > 1e-12) return a.score > b.score;
                          return a.type < b.type;
                      });
            result.strong_branching_candidates_tested +=
                std::min<long long>(strong_branching_candidates,
                                    static_cast<long long>(scored.size()));
            if (!scored.empty()) chosen = scored.front().type;
        } else if (mode == "inventory") {
            if (branch_inventory_enabled && inventory_candidate.found) chosen = "inventory";
        } else if (mode == "operation-mode" || mode == "operation_mode") {
            if (branch_operation_mode_enabled && operation_candidate.found) chosen = "operation_mode";
        } else if (mode == "ryan-foster" || mode == "ryan_foster") {
            if (candidate.found) chosen = "ryan_foster";
        } else {
            if (branch_inventory_enabled && inventory_candidate.found) chosen = "inventory";
            else if (branch_operation_mode_enabled && operation_candidate.found) chosen = "operation_mode";
            else if (candidate.found) chosen = "ryan_foster";
            else if (station_candidate.found) chosen = "station";
        }
        if (chosen.empty()) {
            if (branch_inventory_enabled && inventory_candidate.found) chosen = "inventory";
            else if (branch_operation_mode_enabled && operation_candidate.found) chosen = "operation_mode";
            else if (candidate.found) chosen = "ryan_foster";
            else if (station_candidate.found) chosen = "station";
        }

        if (chosen == "inventory") {
            branchInventory();
            continue;
        }
        if (chosen == "operation_mode") {
            branchOperation();
            continue;
        }
        if (chosen == "ryan_foster") {
            branchRyanFoster();
            continue;
        }
        if (chosen == "station") {
            branchStation();
            continue;
        }

        if (!inventory_candidate.found && !operation_candidate.found &&
            !candidate.found && !station_candidate.found) {
            LeafReconstructionResult reconstructed = reconstructProjectedLeaf(
                instance, lp_node.columns_by_vehicle, node.branch,
                lp_node.y_values, lambda, bound_gamma,
                use_combined_gini_lower_bound,
                ratioSumUpperBound(instance, node.branch));
            if (!reconstructed.found) {
                ++result.projected_leaves;
                appendNodeTrace("unresolved", "none",
                                "projected_leaf_reconstruction_failed");
                finishIncomplete("projected leaf reconstruction failed; column-variable branching or a stronger integer master is needed",
                                 lp_node.fixed_cap_surrogate, 1);
                return result;
            }
            ++result.integer_leaves;
            const bool reconstructed_in_interval =
                objectivePartsInGiniInterval(reconstructed.parts, gamma_floor, gamma);
            if (reconstructed_in_interval) {
                addTerminalLowerBound(cutoff_mode
                    ? reconstructed.parts.objective : reconstructed.surrogate);
                const double candidate_value = cutoff_mode
                    ? reconstructed.parts.objective : reconstructed.surrogate;
                const double incumbent_value = (cutoff_mode && result.has_integer_incumbent)
                    ? result.best_integer_parts.objective : result.best_integer_surrogate;
                if (!result.has_integer_incumbent ||
                    candidate_value < incumbent_value - 1e-9) {
                    result.has_integer_incumbent = true;
                    result.best_integer_surrogate = reconstructed.surrogate;
                    result.best_integer_columns = reconstructed.selected_count;
                    result.incumbent_source = "reconstructed route-integer leaf at depth "
                        + std::to_string(node.depth);
                    result.best_integer_parts = reconstructed.parts;
                    result.best_final_inventory = reconstructed.final_inventory;
                    result.best_routes = reconstructed.routes;
                }
            } else if (!reconstructed_in_interval) {
                result.notes.push_back("reconstructed route true G=" + num(reconstructed.parts.G)
                    + " lies outside requested Gini interval; node kept only as a lower-bound leaf");
            }
            std::ostringstream recon_note;
            recon_note << "reconstructed route-integer leaf at depth=" << node.depth
                       << ", states=" << reconstructed.states
                       << ", selected_columns=" << reconstructed.selected_count
                       << ", surrogate=" << reconstructed.surrogate
                       << ", objective=" << reconstructed.parts.objective;
            result.notes.push_back(recon_note.str());
            appendNodeTrace("reconstructed_integer_leaf", "none", "");
            continue;
        }
        appendNodeTrace("unresolved", "none",
                        "no_enabled_branch_despite_fractional_candidates");
        finishIncomplete("branch selection found no enabled branch despite fractional candidates",
                         lp_node.fixed_cap_surrogate, 1);
        return result;
    }

    result.complete = true;
    result.open_nodes = 0;
    if (cutoff_mode) {
        if (!std::isfinite(result.global_lower_bound)) {
            result.global_lower_bound = effectiveLowerBound(objective_cutoff);
        } else {
            result.global_lower_bound = effectiveLowerBound(result.global_lower_bound);
        }
    } else if (result.has_integer_incumbent) {
        result.global_lower_bound = result.best_integer_surrogate;
    } else if (!std::isfinite(result.global_lower_bound)) {
        result.global_lower_bound = 0.0;
    }
    result.notes.push_back(std::string(gamma_floor >= 0.0
        ? "fixed-Gini-interval branch-price tree exhausted all open nodes; incumbent_source="
        : "fixed-Gini-cap branch-price tree exhausted all open nodes; incumbent_source=")
        + result.incumbent_source);
    if (!std::isfinite(result.pricing_best_reduced_cost_any)) {
        result.pricing_best_reduced_cost_any = 0.0;
    }
    if (!std::isfinite(result.pricing_best_new_reduced_cost)) {
        result.pricing_best_new_reduced_cost = 0.0;
    }
    finalizePricingClosureFields(result);
    return result;
}

} // namespace ebrp
