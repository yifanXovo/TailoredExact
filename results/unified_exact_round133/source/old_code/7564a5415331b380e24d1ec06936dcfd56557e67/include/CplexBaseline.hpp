#pragma once

#include "Instance.hpp"
#include "Result.hpp"

namespace ebrp {

SolveResult solveCplexBaseline(const Instance& instance, const SolveOptions& options);
SolveResult solveIntervalExactCutoffOracle(const Instance& instance, const SolveOptions& options);
SolveResult solveGlobalGiniTree(const Instance& instance,
                                const SolveOptions& options,
                                const SolveResult& verified_seed,
                                double root_gamma_L,
                                double root_gamma_U);

} // namespace ebrp
