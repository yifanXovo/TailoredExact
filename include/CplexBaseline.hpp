#pragma once

#include "Instance.hpp"
#include "Result.hpp"

namespace ebrp {

SolveResult solveCplexBaseline(const Instance& instance, const SolveOptions& options);

} // namespace ebrp
