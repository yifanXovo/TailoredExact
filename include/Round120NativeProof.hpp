#pragma once
#include "CanonicalCompactModel.hpp"
#include "Round119ProofContraction.hpp"
#include <array>
#include <fstream>
#include <stdexcept>

namespace ebrp {
struct Round120Rows {
    double lower_base=0,lower_delta=0,upper_base=0,upper_delta=0;
    double objective_base=0,objective_delta=0,objective_constant=0;
};
struct Round120Pair {
    std::array<Round119Certificate,2> proof;
    double a=0,m=0,b=0,beta0=0,beta1=0;
    std::string input_sha;
};
// Directed binary64 arithmetic guards serialization as well as endpoint sums.
// These guards supplement, never replace, the original 1e-7 evidence margin.
Round120Rows round120Rows(const Round120Pair&,bool conditional,double constant=0);
bool round120Endpoints(const Round120Rows&,const Round120Pair&,bool conditional);
bool round120Contains(const Round120Pair&,double lower,double upper);
Round120Pair makeRound120Pair(const std::array<Round119Certificate,2>&,const std::string& input_sha);
CanonicalCompactModelArtifact extendRound120Artifact(const CanonicalCompactModelArtifact&,
    const Round120Pair&,bool conditional,const std::filesystem::path&);
class Round120ExportComplete : public std::runtime_error {
public:Round120ExportComplete():std::runtime_error("Round120 paid proof/model export complete; no integer Optimize"){}
};
class Round120NativeProof {
public:
    Round120NativeProof(const Instance&,const SolveOptions&,const std::filesystem::path&,
        double a,double b,const std::vector<RoutePlan>& own);
    void add(const Round119Certificate&);
    bool firstInteger(const std::string& leaf,double lower,double upper,double remaining);
    void observe(const std::vector<RoutePlan>&,long long call);
    void record(const std::string&,const std::string& fields);
    void savePair(const std::filesystem::path&) const;
    bool installed() const{return installed_;}
    bool failed() const{return failed_;}
    const Round120Pair& pair() const;
private:
    const Instance& instance_;const SolveOptions& options_;std::ofstream events_;
    std::array<Round119Certificate,2> pending_;std::array<bool,2> present_{{false,false}};
    Round120Pair pair_;bool ready_=false,decided_=false,installed_=false,failed_=false;
    double a_,b_;long long sequence_=0;std::vector<Verification> witnesses_;
};
}
