#pragma once
#include "MipStartMapping.hpp"
#include "Round60Candidates.hpp"
#include <filesystem>
#include <fstream>
#include <functional>
#include <map>
#include <set>

namespace ebrp {
// Session owns only physical candidates and evidence. It never owns a model,
// changes a cutoff, terminates a native call, or invokes an optimizer.
struct Round97Model {
    long long call = 0, epoch = 0;
    std::string leaf, sha;
    std::string start_hash;
    double callback_seconds = 0;
    long long callback_count = 0;
    double lower = 0, upper = 0, cutoff = 0, objective_constant = 0;
    SolverNeutralModelDomain domain;
    SolverNeutralLinearModel linear;
    std::vector<double> objective;
    std::set<std::string> submitted_hashes;
    struct Submission { long long event; std::vector<double> values; double objective, before; bool observed=false, changed=false; };
    std::vector<Submission> submissions;
};

std::vector<RoutePlan> round97Normalize(const Instance&, double, const std::vector<RoutePlan>&);
std::string round97StateHash(const Instance&, double, const std::vector<RoutePlan>&);

class Round97NativeClosure {
public:
    Round97NativeClosure(const Instance&, const SolveOptions&, const std::filesystem::path&,
        const std::string& initial_seed_hash = {});
    using Submit = std::function<int(const std::vector<double>&, double&)>;
    void solution(Round97Model&, const std::vector<double>&, double model_objective,
                  double native_incumbent, double nodes, int solution_count, int phase,
                  const Submit&);
    void incumbent(Round97Model&, double) noexcept;
    void returned(Round97Model&, int status, double objective, const std::vector<double>&) noexcept;
    void failure(const std::string&) noexcept;
    void handoff(long long epoch, double old_upper) noexcept;
    bool feedback() const { return options_.round97_native_closure == "feedback"; }
    const VerifiedBrpCandidate& archive() const { return archive_; }
    bool failed() const { return failed_; }
private:
    void record(const std::string& kind, const std::string& fields);
    const Instance& instance_;
    SolveOptions options_;
    const std::string initial_seed_hash_;
    std::set<std::string> seen_inputs_;
    std::filesystem::path directory_;
    std::ofstream events_;
    long long sequence_ = 0;
    bool failed_ = false;
    struct Cached { VerifiedBrpCandidate candidate; bool exhausted=false; };
    std::map<std::string,Cached> cache_;
    VerifiedBrpCandidate archive_;
};
} // namespace ebrp
