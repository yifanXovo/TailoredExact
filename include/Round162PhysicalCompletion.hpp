#pragma once
#include "CanonicalCompactModel.hpp"
#include "MipStartMapping.hpp"
#include "FixedIntervalMipBackend.hpp"
#include <filesystem>
#include <map>
#include <set>
#include <functional>

namespace ebrp {
// Research entry only. It never enables any RN replacement/source.
struct Round162Row {
    std::map<std::string,double> coefficients;
    double rhs=0;
    bool active=false;
};
struct Round162Controls {
    bool active=false;
    double development_node_limit=-1;
    bool enabled=false,stock_control=false,attempted=false,ready=false,source_running=false;
    std::string input_sha,source_sha;
    double lower=0,upper=0,cutoff=0;
    double source_seconds=0,project_seconds=0;
    int source_calls=0,embeddings=0,scope_skips=0;
    SolverNeutralModelDomain root_domain;
    Round162Row row;
    std::map<std::string,Round162Row> expected;
    std::set<std::string> expected_without_row;
};
inline Round162Controls& round162(){static Round162Controls c;return c;}
inline void round162ResetRun(){const bool enabled=round162().enabled,stock=round162().stock_control;round162()=Round162Controls{};round162().enabled=enabled;round162().stock_control=stock;}
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
    const std::filesystem::path& source,const std::filesystem::path& duals,const std::filesystem::path& output,
    Round162Row* projected_row=nullptr);
void saveRound162LpEvidence(const FixedIntervalMipOutcome&,const std::filesystem::path&);
Round162Artifact appendRound162Row(const std::filesystem::path& base,const std::filesystem::path& output,
    const Round162Row& row);
CanonicalCompactModelArtifact embedRound162Row(const Instance&,const CanonicalCompactModelArtifact&,double cutoff,
    const std::filesystem::path& output);
CanonicalCompactModelArtifact prepareRound162Root(const Instance&,const SolveOptions&,const CanonicalCompactModelArtifact&,
    double cutoff,const std::vector<RoutePlan>&,const std::filesystem::path& directory,const std::function<double()>& remaining);
void finishRound162Run(const std::filesystem::path&);
}
