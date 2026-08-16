#pragma once

#include "GiniFrontierGeometry.hpp"

#include <string>
#include <vector>

namespace ebrp {

struct GiniLookaheadBound {
    GiniIntervalGeometry interval;
    bool terminal_valid = false;
    bool optimal = false;
    bool infeasible = false;
    bool bound_available = false;
    double lower_bound = 0.0;
};

struct GiniEnvelopeFacet {
    double alpha = 0.0;
    double beta = 0.0;
    double source_lower = 0.0;
    double source_upper = 0.0;
    bool constant_parent_candidate = false;
    std::string construction = "unclassified";
};

double evaluateGiniEnvelopeFacet(const GiniEnvelopeFacet& facet, double g);

struct GiniEnvelopeInput {
    GiniIntervalGeometry parent;
    double parent_lower_bound = 0.0;
    double verified_upper_bound = 0.0;
    std::vector<GiniLookaheadBound> lookahead;
    double certificate_tolerance = 1e-7;
};

struct GiniEnvelopeResult {
    bool valid = false;
    std::string status = "not_evaluated";
    std::vector<double> clipped_bounds;
    std::vector<GiniEnvelopeFacet> facets;
    long long generated_facet_count = 0;
    long long duplicate_facet_count = 0;
    long long dominated_facet_count = 0;
    long long numerically_adjusted_facet_count = 0;
    long long numerically_rejected_facet_count = 0;
    long long accepted_facet_count = 0;
    double V_local = 0.0;
    double V_envelope = 0.0;
    double V_residual = 0.0;
    double tau_d = 0.0;
    double D_d = 0.0;
    double max_endpoint_violation = 0.0;
    double integral_identity_residual = 0.0;
};

GiniEnvelopeResult constructGiniLowerBoundEnvelope(
    const GiniEnvelopeInput& input);

bool giniEnvelopeFacetValidOnProfile(
    const GiniEnvelopeFacet& facet,
    const GiniEnvelopeInput& input,
    const std::vector<double>& clipped_bounds,
    double* maximum_violation = nullptr,
    std::string* reason = nullptr);

std::vector<GiniIntervalGeometry> makeEnvelopeInitialPartition(
    const GiniIntervalGeometry& root,
    int K0);

std::vector<GiniIntervalGeometry> makeDyadicLookaheadPartition(
    const GiniIntervalGeometry& parent,
    int depth);

struct AggregatedLookaheadBound {
    bool valid = false;
    bool infeasible = false;
    double lower_bound = 0.0;
    int contributing_cell_count = 0;
    std::string reason = "not_evaluated";
};

AggregatedLookaheadBound aggregateLookaheadBoundForInterval(
    const GiniIntervalGeometry& target,
    double inherited_parent_bound,
    const std::vector<GiniLookaheadBound>& lookahead,
    double certificate_tolerance);

// A completed infeasibility proof is represented by +infinity.  It is a
// valid coverage bound only for an empty leaf; every nonempty leaf must retain
// a finite lower bound.
bool validFinalEnvelopeLeafBound(double lower_bound, bool infeasible);

bool validEnvelopeFacetScope(
    const GiniEnvelopeFacet& facet,
    const GiniIntervalGeometry& target,
    double certificate_tolerance,
    std::string* reason = nullptr);

struct FormulationContractionInput {
    GiniIntervalGeometry parent;
    double parent_A = 0.0;
    std::vector<GiniIntervalGeometry> lookahead_intervals;
    std::vector<double> lookahead_A;
    double epsilon_width = 1e-12;
};

struct FormulationContractionResult {
    bool valid = false;
    double C_d = 0.0;
    double weighted_child_A = 0.0;
    std::string reason = "not_evaluated";
};

FormulationContractionResult evaluateFormulationContraction(
    const FormulationContractionInput& input);

struct EnvelopeRefinementDecision {
    bool valid = false;
    bool split = false;
    double score = 0.0;
    std::string score_mode = "d";
    std::string reason = "not_evaluated";
};

EnvelopeRefinementDecision evaluateEnvelopeRefinementDecision(
    double D_d,
    double C_d,
    const std::string& score_mode,
    double rho,
    double certificate_tolerance);

} // namespace ebrp
