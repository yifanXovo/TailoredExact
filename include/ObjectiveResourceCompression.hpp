#pragma once
#include <string>
#include <vector>
namespace ebrp {
struct ObjectiveResourceRow {
    std::string scope;
    int vehicle=0;
    std::vector<int> indices;
    std::vector<double> coefficients;
    double rhs=0, multiplier=0;
};
struct CompressedResourceRow {
    std::string scope;
    int vehicle=0;
    std::vector<int> indices, source_rows;
    std::vector<double> coefficients;
    double rhs=0, compensation_upper=0;
};
// Validity follows safe nonnegative combination. Objective preservation is a
// separate primal/dual qualification and MUST be checked by reoptimization.
double resourceMultiplier(double pi, char sense, int objective_sense);
std::vector<int> activeResourceRows(const std::vector<ObjectiveResourceRow>&);
std::vector<CompressedResourceRow> compressObjectiveResources(
    const std::vector<ObjectiveResourceRow>&, const std::vector<double>& lower,
    const std::vector<double>& upper, bool fleet=false);
// One <= combination. Selected zero-objective extension columns are submitted
// with coefficient zero; their finite boxes absorb the entire coefficient,
// including nonzero dual residuals. Existing compression semantics are intact.
CompressedResourceRow projectObjectiveResources(
    const std::vector<ObjectiveResourceRow>&, const std::vector<double>& lower,
    const std::vector<double>& upper, const std::vector<bool>& eliminate);
}
