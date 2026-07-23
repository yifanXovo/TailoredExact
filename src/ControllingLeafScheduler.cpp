#include "ControllingLeafScheduler.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <unordered_set>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace ebrp {
namespace {

bool finite(double value) {
    return std::isfinite(value);
}

std::string jsonEscape(const std::string& value) {
    std::ostringstream out;
    for (const char ch : value) {
        switch (ch) {
        case '\\': out << "\\\\"; break;
        case '"': out << "\\\""; break;
        case '\n': out << "\\n"; break;
        case '\r': out << "\\r"; break;
        case '\t': out << "\\t"; break;
        default: out << ch; break;
        }
    }
    return out.str();
}

std::string readText(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return {};
    std::ostringstream out;
    out << in.rdbuf();
    return out.str();
}

std::string extractString(const std::string& text,
                          const std::string& key,
                          const std::string& fallback = {}) {
    const std::string needle = "\"" + key + "\"";
    std::size_t pos = text.find(needle);
    if (pos == std::string::npos) return fallback;
    pos = text.find(':', pos + needle.size());
    if (pos == std::string::npos) return fallback;
    pos = text.find('"', pos + 1);
    if (pos == std::string::npos) return fallback;
    std::string out;
    bool escaped = false;
    for (++pos; pos < text.size(); ++pos) {
        const char ch = text[pos];
        if (escaped) {
            switch (ch) {
            case 'n': out.push_back('\n'); break;
            case 'r': out.push_back('\r'); break;
            case 't': out.push_back('\t'); break;
            default: out.push_back(ch); break;
            }
            escaped = false;
        } else if (ch == '\\') {
            escaped = true;
        } else if (ch == '"') {
            return out;
        } else {
            out.push_back(ch);
        }
    }
    return fallback;
}

double extractDouble(const std::string& text,
                     const std::string& key,
                     double fallback = 0.0) {
    const std::string needle = "\"" + key + "\"";
    std::size_t pos = text.find(needle);
    if (pos == std::string::npos) return fallback;
    pos = text.find(':', pos + needle.size());
    if (pos == std::string::npos) return fallback;
    const std::size_t begin = text.find_first_not_of(" \t\r\n", pos + 1);
    if (begin == std::string::npos) return fallback;
    const std::size_t end = text.find_first_of(",}\r\n", begin);
    try {
        const double value = std::stod(text.substr(begin, end - begin));
        return finite(value) ? value : fallback;
    } catch (const std::exception&) {
        return fallback;
    }
}

std::uint64_t extractUint64(const std::string& text,
                            const std::string& key,
                            std::uint64_t fallback = 0) {
    const double value = extractDouble(text, key, static_cast<double>(fallback));
    if (!finite(value) || value < 0.0) return fallback;
    return static_cast<std::uint64_t>(value);
}

bool extractBool(const std::string& text,
                 const std::string& key,
                 bool fallback = false) {
    const std::string needle = "\"" + key + "\"";
    std::size_t pos = text.find(needle);
    if (pos == std::string::npos) return fallback;
    pos = text.find(':', pos + needle.size());
    if (pos == std::string::npos) return fallback;
    const std::size_t begin = text.find_first_not_of(" \t\r\n", pos + 1);
    if (begin == std::string::npos) return fallback;
    if (text.compare(begin, 4, "true") == 0) return true;
    if (text.compare(begin, 5, "false") == 0) return false;
    return fallback;
}

bool sameIdentityDouble(double lhs, double rhs, double tolerance) {
    return finite(lhs) && finite(rhs) && std::fabs(lhs - rhs) <= tolerance;
}

} // namespace

std::string controllingLeafStatusName(ControllingLeafStatus status) {
    switch (status) {
    case ControllingLeafStatus::Open: return "open";
    case ControllingLeafStatus::Closed: return "closed";
    case ControllingLeafStatus::Fathomed: return "fathomed";
    case ControllingLeafStatus::Empty: return "empty";
    case ControllingLeafStatus::Invalid: return "invalid";
    case ControllingLeafStatus::Replaced: return "replaced";
    }
    return "invalid";
}

ControllingLeafScheduler::ControllingLeafScheduler(double certificate_tolerance)
    : tolerance_(std::max(0.0, certificate_tolerance)) {}

const ControllingLeaf* ControllingLeafScheduler::findLeaf(
    const std::string& leaf_id) const {
    const auto it = std::find_if(leaves_.begin(), leaves_.end(),
        [&](const ControllingLeaf& leaf) { return leaf.id == leaf_id; });
    return it == leaves_.end() ? nullptr : &*it;
}

ControllingLeaf* ControllingLeafScheduler::findLeaf(const std::string& leaf_id) {
    const auto it = std::find_if(leaves_.begin(), leaves_.end(),
        [&](const ControllingLeaf& leaf) { return leaf.id == leaf_id; });
    return it == leaves_.end() ? nullptr : &*it;
}

const std::vector<ControllingLeaf>& ControllingLeafScheduler::leaves() const {
    return leaves_;
}

bool ControllingLeafScheduler::addLeaf(const ControllingLeaf& input,
                                       std::string* reason) {
    if (input.id.empty()) {
        if (reason) *reason = "empty_leaf_id";
        return false;
    }
    if (findLeaf(input.id)) {
        if (reason) *reason = "duplicate_leaf_id";
        return false;
    }
    if (!finite(input.gamma_L) || !finite(input.gamma_U) ||
        input.gamma_U < input.gamma_L - tolerance_) {
        if (reason) *reason = "invalid_leaf_interval";
        return false;
    }
    if (!finite(input.base_lower_bound) || !finite(input.lower_bound) ||
        input.lower_bound + tolerance_ < input.base_lower_bound) {
        if (reason) *reason = "invalid_leaf_bound";
        return false;
    }
    ControllingLeaf leaf = input;
    leaf.lower_bound = std::max(leaf.base_lower_bound, leaf.lower_bound);
    leaves_.push_back(std::move(leaf));
    // Building the initial authoritative set is not a lower-bound update:
    // discovering another initial leaf may legitimately lower the minimum.
    global_bound_history_.push_back(globalLowerBound());
    if (reason) *reason = "accepted";
    return true;
}

bool ControllingLeafScheduler::splitLeafAtomically(
    const std::string& parent_id,
    const std::vector<ControllingLeaf>& children,
    std::string* reason) {
    ControllingLeaf* parent = findLeaf(parent_id);
    if (!parent) {
        if (reason) *reason = "parent_not_found";
        return false;
    }
    if (parent->status != ControllingLeafStatus::Open &&
        parent->status != ControllingLeafStatus::Invalid) {
        if (reason) *reason = "parent_not_open";
        return false;
    }
    if (children.size() < 2) {
        if (reason) *reason = "insufficient_children";
        return false;
    }
    std::vector<ControllingLeaf> checked = children;
    std::sort(checked.begin(), checked.end(),
        [](const ControllingLeaf& lhs, const ControllingLeaf& rhs) {
            if (lhs.gamma_L != rhs.gamma_L) return lhs.gamma_L < rhs.gamma_L;
            if (lhs.gamma_U != rhs.gamma_U) return lhs.gamma_U < rhs.gamma_U;
            return lhs.id < rhs.id;
        });
    std::unordered_set<std::string> ids;
    for (std::size_t i = 0; i < checked.size(); ++i) {
        ControllingLeaf& child = checked[i];
        if (child.id.empty() || findLeaf(child.id) || !ids.insert(child.id).second) {
            if (reason) *reason = "duplicate_or_empty_child_id";
            return false;
        }
        if (child.parent_id != parent_id ||
            child.split_depth != parent->split_depth + 1 ||
            child.child_index < 0) {
            if (reason) *reason = "child_lineage_mismatch";
            return false;
        }
        if (!finite(child.gamma_L) || !finite(child.gamma_U) ||
            child.gamma_U < child.gamma_L - tolerance_) {
            if (reason) *reason = "invalid_child_interval";
            return false;
        }
        if (child.lower_bound + tolerance_ < parent->lower_bound ||
            child.base_lower_bound + tolerance_ < parent->lower_bound) {
            if (reason) *reason = "child_did_not_inherit_parent_bound";
            return false;
        }
        if (i == 0 && std::fabs(child.gamma_L - parent->gamma_L) > tolerance_) {
            if (reason) *reason = "child_coverage_left_endpoint";
            return false;
        }
        if (i > 0 &&
            std::fabs(checked[i - 1].gamma_U - child.gamma_L) > tolerance_) {
            if (reason) *reason = "child_coverage_gap_or_overlap";
            return false;
        }
        if (i + 1 == checked.size() &&
            std::fabs(child.gamma_U - parent->gamma_U) > tolerance_) {
            if (reason) *reason = "child_coverage_right_endpoint";
            return false;
        }
        child.parent_child_coverage_valid = true;
        child.parent_replaced = false;
        child.status = ControllingLeafStatus::Open;
    }

    const double before = globalLowerBound();
    leaves_.reserve(leaves_.size() + checked.size());
    for (const ControllingLeaf& child : checked) leaves_.push_back(child);
    parent = findLeaf(parent_id);
    parent->parent_replaced = true;
    parent->status = ControllingLeafStatus::Replaced;
    const double after = globalLowerBound();
    if (after + tolerance_ < before) global_bound_monotone_ = false;
    noteGlobalBound();
    active_tie_order_.clear();
    if (reason) *reason = "accepted_exact_child_coverage";
    return true;
}

bool ControllingLeafScheduler::mergeValidLowerBound(
    const std::string& leaf_id,
    double value,
    const std::string& source,
    std::string* reason) {
    ControllingLeaf* leaf = findLeaf(leaf_id);
    if (!leaf) {
        if (reason) *reason = "leaf_not_found";
        return false;
    }
    if (!finite(value) || source.empty()) {
        if (reason) *reason = "invalid_bound_or_source";
        return false;
    }
    const double before_leaf = leaf->lower_bound;
    const double before_global = globalLowerBound();
    leaf->lower_bound = std::max(leaf->lower_bound, value);
    if (leaf->lower_bound + tolerance_ < before_leaf) leaf_bounds_monotone_ = false;
    if (std::find(leaf->lower_bound_sources.begin(),
                  leaf->lower_bound_sources.end(), source) ==
        leaf->lower_bound_sources.end()) {
        leaf->lower_bound_sources.push_back(source);
    }
    const double after_global = globalLowerBound();
    if (after_global + tolerance_ < before_global) global_bound_monotone_ = false;
    noteGlobalBound();
    if (reason) *reason = leaf->lower_bound > before_leaf + tolerance_
        ? "accepted_improved" : "accepted_no_change";
    return true;
}

bool ControllingLeafScheduler::setStatus(const std::string& leaf_id,
                                         ControllingLeafStatus status,
                                         const std::string& closure_source,
                                         std::string* reason) {
    ControllingLeaf* leaf = findLeaf(leaf_id);
    if (!leaf) {
        if (reason) *reason = "leaf_not_found";
        return false;
    }
    if (status == ControllingLeafStatus::Closed ||
        status == ControllingLeafStatus::Fathomed ||
        status == ControllingLeafStatus::Empty) {
        if (closure_source.empty()) {
            if (reason) *reason = "missing_closure_source";
            return false;
        }
        if (status == ControllingLeafStatus::Fathomed &&
            leaf->lower_bound < leaf->cutoff - tolerance_) {
            if (reason) *reason = "fathom_bound_below_cutoff";
            return false;
        }
    }
    const double before_global = globalLowerBound();
    leaf->status = status;
    leaf->closure_source = closure_source;
    if (status == ControllingLeafStatus::Fathomed ||
        status == ControllingLeafStatus::Empty) {
        leaf->lower_bound = std::max(leaf->lower_bound, leaf->cutoff);
    }
    const double after_global = globalLowerBound();
    if (after_global + tolerance_ < before_global) global_bound_monotone_ = false;
    noteGlobalBound();
    active_tie_order_.clear();
    if (reason) *reason = "accepted";
    return true;
}

bool ControllingLeafScheduler::recordAttempt(
    const std::string& leaf_id,
    const ControllingLeafAttempt& attempt,
    double elapsed_start_seconds,
    double elapsed_end_seconds,
    std::string* reason) {
    ControllingLeaf* leaf = findLeaf(leaf_id);
    if (!leaf) {
        if (reason) *reason = "leaf_not_found";
        return false;
    }
    if (attempt.attempt_number != leaf->exact_solver_attempt_count ||
        attempt.requested_quantum_seconds <= 0.0 ||
        attempt.effective_native_time_limit_seconds <= 0.0 ||
        attempt.effective_native_time_limit_seconds >
            attempt.requested_quantum_seconds + tolerance_ ||
        attempt.actual_solver_time_seconds < 0.0) {
        if (reason) *reason = "invalid_attempt_accounting";
        return false;
    }
    if (leaf->exact_solver_attempt_count == 0) {
        leaf->first_attempt_elapsed_seconds = elapsed_start_seconds;
    }
    leaf->last_attempt_elapsed_seconds = elapsed_end_seconds;
    leaf->cumulative_allocated_time_seconds +=
        attempt.effective_native_time_limit_seconds;
    leaf->cumulative_solver_time_seconds += attempt.actual_solver_time_seconds;
    if (attempt.selected_while_controlling) {
        leaf->time_while_controlling_seconds += attempt.actual_solver_time_seconds;
    } else {
        leaf->time_while_noncontrolling_seconds += attempt.actual_solver_time_seconds;
    }
    if (attempt.solver_final_best_bound_valid) {
        leaf->latest_solver_final_best_bound_valid = true;
        leaf->latest_solver_final_best_bound = attempt.solver_final_best_bound;
    }
    if (attempt.checkpoint_best_bound_valid) {
        leaf->latest_checkpoint_best_bound_valid = true;
        leaf->latest_checkpoint_best_bound = attempt.checkpoint_best_bound;
    }
    leaf->latest_solver_final_status = attempt.solver_status;
    leaf->attempts.push_back(attempt);
    ++leaf->exact_solver_attempt_count;
    if (reason) *reason = "accepted";
    return true;
}

bool ControllingLeafScheduler::isRelevantFinalLeaf(
    const ControllingLeaf& leaf) const {
    return leaf.status != ControllingLeafStatus::Replaced &&
           !leaf.parent_replaced &&
           leaf.gamma_L < leaf.cutoff - tolerance_;
}

bool ControllingLeafScheduler::isOpenRelevantLeaf(
    const ControllingLeaf& leaf) const {
    return isRelevantFinalLeaf(leaf) &&
           (leaf.status == ControllingLeafStatus::Open ||
            leaf.status == ControllingLeafStatus::Invalid) &&
           leaf.lower_bound < leaf.cutoff - tolerance_;
}

double ControllingLeafScheduler::globalLowerBound() const {
    double bound = std::numeric_limits<double>::infinity();
    for (const ControllingLeaf& leaf : leaves_) {
        if (!isRelevantFinalLeaf(leaf)) continue;
        bound = std::min(bound, leaf.lower_bound);
    }
    return finite(bound) ? bound : 0.0;
}

std::vector<std::string> ControllingLeafScheduler::orderedControllingSet(
    double* min_bound) const {
    double minimum = std::numeric_limits<double>::infinity();
    for (const ControllingLeaf& leaf : leaves_) {
        if (!isOpenRelevantLeaf(leaf)) continue;
        minimum = std::min(minimum, leaf.lower_bound);
    }
    std::vector<const ControllingLeaf*> controlling;
    if (finite(minimum)) {
        for (const ControllingLeaf& leaf : leaves_) {
            if (isOpenRelevantLeaf(leaf) &&
                leaf.lower_bound <= minimum + tolerance_) {
                controlling.push_back(&leaf);
            }
        }
    }
    std::sort(controlling.begin(), controlling.end(),
        [](const ControllingLeaf* lhs, const ControllingLeaf* rhs) {
            const double lw = lhs->gamma_U - lhs->gamma_L;
            const double rw = rhs->gamma_U - rhs->gamma_L;
            if (std::fabs(lw - rw) > 1e-12) return lw > rw;
            if (std::fabs(lhs->gamma_L - rhs->gamma_L) > 1e-12) {
                return lhs->gamma_L < rhs->gamma_L;
            }
            if (std::fabs(lhs->gamma_U - rhs->gamma_U) > 1e-12) {
                return lhs->gamma_U < rhs->gamma_U;
            }
            return lhs->id < rhs->id;
        });
    std::vector<std::string> ids;
    ids.reserve(controlling.size());
    for (const ControllingLeaf* leaf : controlling) ids.push_back(leaf->id);
    if (min_bound) *min_bound = finite(minimum) ? minimum : globalLowerBound();
    return ids;
}

std::vector<std::string> ControllingLeafScheduler::controllingSet() const {
    return orderedControllingSet(nullptr);
}

ControllingLeafSelection ControllingLeafScheduler::selectNext() {
    ControllingLeafSelection result = selectNextByBoundOnly();
    if (!result.available) return result;
    const ControllingLeaf* leaf = findLeaf(result.selected_leaf_id);
    result.next_attempt_number = leaf ? leaf->exact_solver_attempt_count : 0;
    result.requested_quantum_seconds =
        requestedQuantumSeconds(result.next_attempt_number);
    return result;
}

ControllingLeafSelection ControllingLeafScheduler::selectNextByBoundOnly() {
    ControllingLeafSelection result;
    double min_bound = globalLowerBound();
    std::vector<std::string> order = orderedControllingSet(&min_bound);
    result.global_lower_bound = globalLowerBound();
    result.competing_minimum_bound = min_bound;
    result.controlling_leaf_ids = order;
    result.deterministic_tie_order = order;
    if (order.empty()) return result;

    if (order != active_tie_order_ ||
        std::fabs(min_bound - active_tie_bound_) > tolerance_) {
        active_tie_order_ = order;
        active_tie_bound_ = min_bound;
        active_tie_cursor_ = 0;
        active_tie_round_ = 0;
    }
    if (active_tie_cursor_ >= active_tie_order_.size()) {
        active_tie_cursor_ = 0;
        ++active_tie_round_;
    }
    result.available = true;
    result.selection_position = static_cast<int>(active_tie_cursor_);
    result.tie_round = active_tie_round_;
    result.selected_leaf_id = active_tie_order_[active_tie_cursor_++];
    return result;
}

ControllingLeafSelection ControllingLeafScheduler::selectNextCplexReplica() {
    ControllingLeafSelection result;
    std::vector<const ControllingLeaf*> open;
    for (const ControllingLeaf& leaf : leaves_) {
        if (isOpenRelevantLeaf(leaf)) open.push_back(&leaf);
    }
    std::sort(open.begin(), open.end(),
        [](const ControllingLeaf* lhs, const ControllingLeaf* rhs) {
            if (lhs->lower_bound != rhs->lower_bound) {
                return lhs->lower_bound < rhs->lower_bound;
            }
            const double lhs_width = lhs->gamma_U - lhs->gamma_L;
            const double rhs_width = rhs->gamma_U - rhs->gamma_L;
            if (lhs_width != rhs_width) return lhs_width < rhs_width;
            if (lhs->split_depth != rhs->split_depth) {
                return lhs->split_depth > rhs->split_depth;
            }
            if (lhs->gamma_L != rhs->gamma_L) {
                return lhs->gamma_L < rhs->gamma_L;
            }
            if (lhs->gamma_U != rhs->gamma_U) {
                return lhs->gamma_U < rhs->gamma_U;
            }
            return lhs->id < rhs->id;
        });
    result.global_lower_bound = globalLowerBound();
    if (open.empty()) return result;
    result.available = true;
    result.selected_leaf_id = open.front()->id;
    result.competing_minimum_bound = open.front()->lower_bound;
    result.selection_position = 0;
    for (const ControllingLeaf* leaf : open) {
        if (leaf->lower_bound != open.front()->lower_bound) break;
        result.controlling_leaf_ids.push_back(leaf->id);
        result.deterministic_tie_order.push_back(leaf->id);
    }
    return result;
}

bool ControllingLeafScheduler::tightenVerifiedCutoff(
    double cutoff, std::string* reason) {
    if (!finite(cutoff)) {
        if (reason) *reason = "nonfinite_cutoff";
        return false;
    }
    for (ControllingLeaf& leaf : leaves_) {
        if (cutoff > leaf.cutoff + tolerance_) {
            if (reason) *reason = "cutoff_would_weaken_existing_incumbent";
            return false;
        }
    }
    const double before = globalLowerBound();
    for (ControllingLeaf& leaf : leaves_) {
        leaf.cutoff = std::min(leaf.cutoff, cutoff);
    }
    const double after = globalLowerBound();
    if (after + tolerance_ < before) global_bound_monotone_ = false;
    noteGlobalBound();
    active_tie_order_.clear();
    if (reason) *reason = "accepted_tighter_verified_cutoff";
    return true;
}

bool ControllingLeafScheduler::everyRelevantLeafClosed() const {
    for (const ControllingLeaf& leaf : leaves_) {
        if (isOpenRelevantLeaf(leaf)) return false;
    }
    return true;
}

bool ControllingLeafScheduler::parentChildCoverageValid(std::string* reason) const {
    for (const ControllingLeaf& parent : leaves_) {
        if (parent.status != ControllingLeafStatus::Replaced &&
            !parent.parent_replaced) continue;
        std::vector<const ControllingLeaf*> children;
        for (const ControllingLeaf& leaf : leaves_) {
            if (leaf.parent_id == parent.id) children.push_back(&leaf);
        }
        if (children.size() < 2) {
            if (reason) *reason = "replaced_parent_missing_children:" + parent.id;
            return false;
        }
        std::sort(children.begin(), children.end(),
            [](const ControllingLeaf* lhs, const ControllingLeaf* rhs) {
                return lhs->gamma_L < rhs->gamma_L;
            });
        if (std::fabs(children.front()->gamma_L - parent.gamma_L) > tolerance_ ||
            std::fabs(children.back()->gamma_U - parent.gamma_U) > tolerance_) {
            if (reason) *reason = "parent_endpoint_coverage:" + parent.id;
            return false;
        }
        for (std::size_t i = 1; i < children.size(); ++i) {
            if (std::fabs(children[i - 1]->gamma_U - children[i]->gamma_L) >
                tolerance_) {
                if (reason) *reason = "parent_child_gap_or_overlap:" + parent.id;
                return false;
            }
        }
    }
    if (reason) *reason = "passed";
    return true;
}

bool ControllingLeafScheduler::leafBoundsMonotone() const {
    return leaf_bounds_monotone_;
}

bool ControllingLeafScheduler::globalBoundMonotone() const {
    return global_bound_monotone_;
}

double ControllingLeafScheduler::certificateTolerance() const {
    return tolerance_;
}

void ControllingLeafScheduler::noteGlobalBound() {
    const double bound = globalLowerBound();
    if (!global_bound_history_.empty() &&
        bound + tolerance_ < global_bound_history_.back()) {
        global_bound_monotone_ = false;
    }
    global_bound_history_.push_back(bound);
}

double ControllingLeafScheduler::requestedQuantumSeconds(int zero_based_attempt) {
    if (zero_based_attempt <= 0) return 30.0;
    if (zero_based_attempt >= 1020) {
        return std::numeric_limits<double>::max();
    }
    const double value = std::ldexp(30.0, zero_based_attempt);
    return finite(value) ? value : std::numeric_limits<double>::max();
}

double ControllingLeafScheduler::finalizationReserveSeconds(
    double nominal_total_budget_seconds) {
    return std::min(30.0,
        std::max(5.0, 0.02 * std::max(0.0, nominal_total_budget_seconds)));
}

DeadlineLaunchDecision ControllingLeafScheduler::planLaunch(
    double requested_quantum_seconds,
    double remaining_parent_time_seconds,
    double reserve_seconds) {
    DeadlineLaunchDecision result;
    result.requested_quantum_seconds = requested_quantum_seconds;
    result.remaining_parent_time_seconds = remaining_parent_time_seconds;
    result.finalization_reserve_seconds = std::max(0.0, reserve_seconds);
    if (!finite(requested_quantum_seconds) || requested_quantum_seconds <= 0.0) {
        result.rejection_reason = "invalid_requested_quantum";
        return result;
    }
    const double available = remaining_parent_time_seconds - result.finalization_reserve_seconds;
    if (available <= 1e-9) {
        result.rejection_reason = "finalization_reserve_boundary";
        return result;
    }
    result.effective_native_time_limit_seconds =
        std::min(requested_quantum_seconds, available);
    if (result.effective_native_time_limit_seconds <= 1e-9) {
        result.rejection_reason = "no_effective_solver_time";
        return result;
    }
    result.launch_allowed = true;
    result.rejection_reason = "none";
    return result;
}

NativeCheckpointValidation validateNativeCheckpoint(
    const NativeCheckpointRecord& record,
    const NativeCheckpointExpectation& expected,
    double identity_tolerance) {
    auto reject = [](const std::string& reason) {
        NativeCheckpointValidation result;
        result.reason = reason;
        return result;
    };
    if (!record.complete) return reject("partial_checkpoint");
    if (!record.atomic_persistence_complete) return reject("non_atomic_checkpoint");
    if (record.run_id != expected.run_id) return reject("stale_run_id");
    if (record.sequence <= expected.last_accepted_sequence) {
        return reject("stale_or_nonmonotone_sequence");
    }
    if (record.instance_hash != expected.instance_hash) {
        return reject("instance_hash_mismatch");
    }
    if (!sameIdentityDouble(record.gamma_L, expected.gamma_L, identity_tolerance) ||
        !sameIdentityDouble(record.gamma_U, expected.gamma_U, identity_tolerance)) {
        return reject("interval_mismatch");
    }
    if (!sameIdentityDouble(record.cutoff, expected.cutoff, identity_tolerance)) {
        return reject("cutoff_mismatch");
    }
    if (record.objective_sense != "minimize") {
        return reject("objective_sense_mismatch");
    }
    if (record.model_fingerprint != expected.model_fingerprint) {
        return reject("model_fingerprint_mismatch");
    }
    if (record.formulation_profile != expected.formulation_profile) {
        return reject("formulation_profile_mismatch");
    }
    if (record.cplex_threads != expected.cplex_threads) {
        return reject("thread_policy_mismatch");
    }
    if (record.native_time_limit_param_id != expected.native_time_limit_param_id ||
        !sameIdentityDouble(record.native_time_limit_seconds,
                            expected.native_time_limit_seconds,
                            identity_tolerance) ||
        record.native_time_limit_set_rc != 0) {
        return reject("native_time_limit_mismatch");
    }
    if (record.bound_source != "cplex_native_best_bound") {
        return reject("non_native_bound_source");
    }
    if (record.model_type != "original_fixed_interval_compact_mip" ||
        !record.original_objective_unchanged) {
        return reject("fixed_interval_model_scope_mismatch");
    }
    if (!finite(record.best_bound)) return reject("nonfinite_best_bound");
    if (record.forbidden_evidence_used) return reject("forbidden_evidence_source");
    NativeCheckpointValidation result;
    result.accepted = true;
    result.reason = "accepted_native_checkpoint";
    return result;
}

bool writeNativeCheckpointAtomic(const std::filesystem::path& path,
                                 const NativeCheckpointRecord& record,
                                 std::string* reason) {
    try {
        if (!path.parent_path().empty()) {
            std::filesystem::create_directories(path.parent_path());
        }
        const std::filesystem::path temporary = path.string() + ".tmp";
        {
            std::ofstream out(temporary, std::ios::out | std::ios::trunc);
            if (!out) {
                if (reason) *reason = "temporary_open_failed";
                return false;
            }
            out << std::setprecision(17)
                << "{\n"
                << "  \"checkpoint_schema\": \"exactebrp_native_leaf_checkpoint_v1\",\n"
                << "  \"run_id\": \"" << jsonEscape(record.run_id) << "\",\n"
                << "  \"sequence\": " << record.sequence << ",\n"
                << "  \"instance_hash\": \"" << jsonEscape(record.instance_hash) << "\",\n"
                << "  \"gamma_L\": " << record.gamma_L << ",\n"
                << "  \"gamma_U\": " << record.gamma_U << ",\n"
                << "  \"cutoff\": " << record.cutoff << ",\n"
                << "  \"objective_sense\": \"" << jsonEscape(record.objective_sense) << "\",\n"
                << "  \"model_fingerprint\": \"" << jsonEscape(record.model_fingerprint) << "\",\n"
                << "  \"formulation_profile\": \"" << jsonEscape(record.formulation_profile) << "\",\n"
                << "  \"cplex_threads\": " << record.cplex_threads << ",\n"
                << "  \"native_time_limit_param_id\": " << record.native_time_limit_param_id << ",\n"
                << "  \"native_time_limit_seconds\": " << record.native_time_limit_seconds << ",\n"
                << "  \"native_time_limit_set_rc\": " << record.native_time_limit_set_rc << ",\n"
                << "  \"best_bound\": " << record.best_bound << ",\n"
                << "  \"bound_source\": \"" << jsonEscape(record.bound_source) << "\",\n"
                << "  \"model_type\": \"" << jsonEscape(record.model_type) << "\",\n"
                << "  \"original_objective_unchanged\": "
                << (record.original_objective_unchanged ? "true" : "false") << ",\n"
                << "  \"forbidden_evidence_used\": "
                << (record.forbidden_evidence_used ? "true" : "false") << ",\n"
                << "  \"atomic_persistence_complete\": "
                << (record.atomic_persistence_complete ? "true" : "false") << ",\n"
                << "  \"complete\": " << (record.complete ? "true" : "false") << "\n"
                << "}\n";
            out.flush();
            if (!out) {
                if (reason) *reason = "temporary_flush_failed";
                return false;
            }
        }
#ifdef _WIN32
        const std::wstring from = temporary.wstring();
        const std::wstring to = path.wstring();
        if (!MoveFileExW(from.c_str(), to.c_str(),
                         MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
            if (reason) *reason = "atomic_replace_failed:" +
                std::to_string(static_cast<unsigned long>(GetLastError()));
            std::error_code ignored;
            std::filesystem::remove(temporary, ignored);
            return false;
        }
#else
        std::error_code ignored;
        std::filesystem::remove(path, ignored);
        std::filesystem::rename(temporary, path);
#endif
        if (reason) *reason = "atomic_rename_complete";
        return true;
    } catch (const std::exception& ex) {
        if (reason) *reason = std::string("checkpoint_write_exception:") + ex.what();
        return false;
    }
}

bool readNativeCheckpoint(const std::filesystem::path& path,
                          NativeCheckpointRecord& record,
                          std::string* reason) {
    const std::string text = readText(path);
    if (text.empty()) {
        if (reason) *reason = "checkpoint_missing_or_empty";
        return false;
    }
    if (extractString(text, "checkpoint_schema") !=
        "exactebrp_native_leaf_checkpoint_v1") {
        if (reason) *reason = "checkpoint_schema_mismatch";
        return false;
    }
    record.run_id = extractString(text, "run_id");
    record.sequence = extractUint64(text, "sequence");
    record.instance_hash = extractString(text, "instance_hash");
    record.gamma_L = extractDouble(text, "gamma_L");
    record.gamma_U = extractDouble(text, "gamma_U");
    record.cutoff = extractDouble(text, "cutoff");
    record.objective_sense = extractString(text, "objective_sense");
    record.model_fingerprint = extractString(text, "model_fingerprint");
    record.formulation_profile = extractString(text, "formulation_profile");
    record.cplex_threads = static_cast<int>(extractDouble(text, "cplex_threads", 0));
    record.native_time_limit_param_id = static_cast<int>(
        extractDouble(text, "native_time_limit_param_id", 0));
    record.native_time_limit_seconds =
        extractDouble(text, "native_time_limit_seconds");
    record.native_time_limit_set_rc = static_cast<int>(
        extractDouble(text, "native_time_limit_set_rc", -1));
    record.best_bound = extractDouble(
        text, "best_bound", std::numeric_limits<double>::quiet_NaN());
    record.bound_source = extractString(text, "bound_source");
    record.model_type = extractString(text, "model_type");
    record.original_objective_unchanged =
        extractBool(text, "original_objective_unchanged", false);
    record.forbidden_evidence_used =
        extractBool(text, "forbidden_evidence_used", true);
    record.atomic_persistence_complete =
        extractBool(text, "atomic_persistence_complete", false);
    record.complete = extractBool(text, "complete", false);
    if (reason) *reason = "parsed";
    return true;
}

std::string stableFileFingerprint(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return {};
    std::uint64_t hash = 1469598103934665603ull;
    char ch = 0;
    while (in.get(ch)) {
        hash ^= static_cast<unsigned char>(ch);
        hash *= 1099511628211ull;
    }
    std::ostringstream out;
    out << std::hex << std::setfill('0') << std::setw(16) << hash;
    return out.str();
}

} // namespace ebrp
