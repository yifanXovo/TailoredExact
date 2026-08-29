#pragma once

#include "PaperExternalGiniTree.hpp"

#include <map>
#include <string>
#include <vector>

namespace ebrp {

inline constexpr const char* kRound49RCProfileVersion =
    "round49-primitive-integer-reduced-cost-v1";

struct Round49RCStateDomain {
    int effective_lower = 0;
    int effective_upper = -1;
    int rc_lower = 0;
    int rc_upper = -1;
    long long effective_count = 0;
    long long rc_count = 0;
    double primal_value = 0.0;
    double reduced_cost = 0.0;
    int variable_basis_status = 0;
    std::string reason = "not_evaluated";
};

struct Round49RCVariableDomain {
    std::string variable;
    std::string family;
    Round49RCStateDomain parent;
    Round49RCStateDomain left;
    Round49RCStateDomain right;
    bool exact_child_disjoint = false;
};

struct Round49RCSummary {
    double D = 0.0;
    double H = 0.0;
    long long residual_count = 0;
    long long base_residual_count = 0;
    long long fixed_count = 0;
    long long tightened_count = 0;
};

struct Round49RCDomainProfile {
    bool valid = false;
    std::string failure_reason = "not_evaluated";
    std::string profile_version = kRound49RCProfileVersion;
    double verified_incumbent = 0.0;
    double parent_lp_bound = 0.0;
    double left_lp_bound = 0.0;
    double right_lp_bound = 0.0;
    std::string parent_model_fingerprint;
    std::string left_model_fingerprint;
    std::string right_model_fingerprint;
    long long primitive_variable_count = 0;
    long long rc_valid_variable_count = 0;
    long long nonfixed_parent_variable_count = 0;
    long long disjoint_domain_count = 0;
    std::map<std::string, long long> family_counts;
    Round49RCSummary parent;
    Round49RCSummary left;
    Round49RCSummary right;
    std::vector<Round49RCVariableDomain> variables;
};

struct K1AMRCDecision {
    bool valid = false;
    bool profile_valid = false;
    bool fallback_to_am = false;
    bool am_split = false;
    bool dominance = false;
    bool strict_mean_improvement = false;
    bool exact_separation = false;
    bool rescue_activated = false;
    std::string rule = "off";
    std::string summary = "D";
    double parent_summary = 0.0;
    double left_summary = 0.0;
    double right_summary = 0.0;
    double numerical_tolerance = 0.0;
    double exact_domain_count_margin = 0.0;
    std::string am_action = "not_evaluated";
    std::string final_action = "not_evaluated";
    std::string reason = "not_evaluated";
    std::string fallback_reason = "none";
    std::string decision_hash;
};

std::string round49PrimitiveIntegerFamily(const std::string& variable);

Round49RCDomainProfile buildRound49RCDomainProfile(
    const PaperLpResult& parent,
    const PaperLpResult& left,
    const PaperLpResult& right,
    double verified_incumbent,
    double certificate_tolerance);

K1AMRCDecision evaluateK1AMRCDecision(
    const C6CurrentSplitDecision& adaptive_mass,
    const Round49RCDomainProfile& profile,
    const std::string& rule,
    double certificate_tolerance);

void applyK1AMRCDecision(C6CurrentSplitDecision& adaptive_mass,
                         const K1AMRCDecision& decision);

} // namespace ebrp
