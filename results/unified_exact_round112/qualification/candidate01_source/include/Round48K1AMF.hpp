#pragma once

#include "PaperExternalGiniTree.hpp"

#include <filesystem>
#include <map>
#include <string>
#include <vector>

namespace ebrp {

inline constexpr double kRound48K1AMFTau = 0.07915;
inline constexpr const char* kRound48AMFProfileVersion =
    "round48-canonical-interval-sensitive-v1";

struct AMFVariableContraction {
    std::string variable;
    std::string family;
    double parent_lower = 0.0;
    double parent_upper = 0.0;
    double parent_width = 0.0;
    double width_tolerance = 0.0;
    double left_lower = 0.0;
    double left_upper = 0.0;
    double left_width = 0.0;
    double c_left = 0.0;
    double right_lower = 0.0;
    double right_upper = 0.0;
    double right_width = 0.0;
    double c_right = 0.0;
    bool fixed_left = false;
    bool fixed_right = false;
};

struct AMFFormulationProfile {
    bool valid = false;
    std::string failure_reason = "not_evaluated";
    std::string profile_version = kRound48AMFProfileVersion;
    long long eligible_variable_count = 0;
    long long excluded_gini_variable_count = 0;
    long long invalid_variable_count = 0;
    std::map<std::string, long long> family_counts;
    double phi_left = 0.0;
    double phi_right = 0.0;
    double left_min_contraction = 0.0;
    double left_mean_contraction = 0.0;
    double left_max_contraction = 0.0;
    double right_min_contraction = 0.0;
    double right_mean_contraction = 0.0;
    double right_max_contraction = 0.0;
    long long fixed_left_count = 0;
    long long fixed_right_count = 0;
    std::vector<AMFVariableContraction> variables;
};

struct K1AMFDecision {
    bool valid = false;
    bool profile_valid = false;
    bool fallback_to_am = false;
    std::string fallback_reason = "none";
    double g_left = 0.0;
    double g_right = 0.0;
    double eta = 0.0;
    double mu = 0.0;
    double s_am = 0.0;
    double phi_left = 0.0;
    double phi_right = 0.0;
    double gtilde_left = 0.0;
    double gtilde_right = 0.0;
    double eta_hat = 0.0;
    double s_amf = 0.0;
    double tau = kRound48K1AMFTau;
    double score_tolerance = 0.0;
    bool am_split = false;
    bool amf_split = false;
    bool rescue_activated = false;
    std::string am_action = "not_evaluated";
    std::string amf_action = "not_evaluated";
    std::string reason = "not_evaluated";
    std::string decision_hash;
};

std::string round48AMFEligibleFamily(const std::string& variable);

AMFFormulationProfile buildRound48AMFFormulationProfile(
    const std::filesystem::path& parent_model,
    const std::filesystem::path& left_model,
    const std::filesystem::path& right_model,
    double certificate_tolerance);

K1AMFDecision evaluateK1AMFDecision(
    const C6CurrentSplitDecision& adaptive_mass,
    const AMFFormulationProfile& profile,
    double tau = kRound48K1AMFTau);

void applyK1AMFDecision(C6CurrentSplitDecision& adaptive_mass,
                        const K1AMFDecision& amf);

} // namespace ebrp
