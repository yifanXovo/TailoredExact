#pragma once

#include "Instance.hpp"
#include "Result.hpp"

namespace ebrp {

// Cold-start external-Gurobi realization of the corrected stable S0/F0
// paper algorithm.  It reproduces the Gini decomposition, static tailored
// rows, pruning, terminal exact subproblems, and global certificate; it does
// not claim native CPLEX tree-state or event-sequence equivalence.
SolveResult solveReplicaExternalGiniTree(const Instance& instance,
                                         const SolveOptions& options,
                                         const SolveResult& verified_seed,
                                         double root_gamma_L,
                                         double root_gamma_U);

} // namespace ebrp
