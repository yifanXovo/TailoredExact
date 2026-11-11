#pragma once
#include "CanonicalCompactModel.hpp"
#include "MipStartMapping.hpp"
#include "FixedIntervalMipBackend.hpp"
#include <filesystem>
#include <map>

namespace ebrp {
// Research entry only. It never enables any RN replacement/source.
struct Round162Controls {
    bool active=false;
    double development_node_limit=-1;
};
inline Round162Controls& round162(){static Round162Controls c;return c;}
struct Round162Artifact {
    std::string sha256,row_signature;
    double lower=0,upper=0;
    int original_columns=0,original_rows=0,physical_columns=0,physical_rows=0;
};
Round162Artifact buildRound162Completion(const Instance&,const std::filesystem::path& original,
    const std::filesystem::path& output,bool full,bool omit_endpoint_time=false);
SolverNeutralModelDomain round162Domain(const std::filesystem::path&);
std::vector<double> round162ExtendStart(const std::filesystem::path&,
    const SolverNeutralModelDomain&,const std::vector<double>& original);
double round162PointResidual(const std::filesystem::path&,const std::vector<double>&,bool check_types=true);
void round162FixSavedPoint(const std::filesystem::path& model,const std::filesystem::path& values);
Round162Artifact projectRound162Completion(const std::filesystem::path& baseline,
    const std::filesystem::path& source,const std::filesystem::path& duals,const std::filesystem::path& output);
void saveRound162LpEvidence(const FixedIntervalMipOutcome&,const std::filesystem::path&);
}
