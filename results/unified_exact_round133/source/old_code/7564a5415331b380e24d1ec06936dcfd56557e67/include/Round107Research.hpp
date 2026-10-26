#pragma once
#include "Round105Decomposition.hpp"
namespace ebrp {
// Isolated qualification only; never called from a production controller.
Round105OracleResult round107OracleDeadlineQualification(const Instance&,const SolveOptions&,
    const Round105Pattern&,const std::filesystem::path&);
}
