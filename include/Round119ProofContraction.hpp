#pragma once
#include "ControllingLeafScheduler.hpp"
#include "Result.hpp"
#include <fstream>
#include <limits>

namespace ebrp {
struct FixedIntervalMipOutcome;
enum class Round119ReturnDisposition { Invalid, MathematicalReturn, Deadline, ResourceStop };
Round119ReturnDisposition evaluateRound119Return(const FixedIntervalMipOutcome&, double remaining);
struct Round119Certificate {
    std::string parent, leaf, model, path, scope, status;
    int depth = 0, side = -1;
    long long call = 0, epoch = -1;
    double parent_lower = 0, parent_upper = 0, lower = 0, upper = 0;
    double cutoff = 0, bound = 0, available_seconds = 0;
    bool used = false;
};
struct Round119Contraction {
    bool available = false, close_both = false;
    std::size_t proof = 0, sibling_proof = 0;
    double split = 0, left_bound = 0, right_bound = 0;
    int removed_side = -1;
};
Round119Contraction chooseRound119Contraction(
    const std::vector<Round119Certificate>& proofs, const ControllingLeaf& leaf,
    const std::vector<std::string>& ancestors, double own_upper, double tolerance,
    int maximum_depth, double minimum_width);

// Same-run paid certificates are distinct from the epoch-keyed solver cache.
// This object never changes a model, invokes Optimize, or mutates a scheduler.
class Round119ProofContraction {
public:
    Round119ProofContraction(const Instance&, const SolveOptions&,
        const std::filesystem::path&, const std::vector<RoutePlan>&, double tolerance);
    void add(Round119Certificate);
    void observe(const std::vector<RoutePlan>&, long long call);
    Round119Contraction choose(const ControllingLeaf&, const std::vector<std::string>&) const;
    void record(const std::string& kind, const std::string& fields);
    void consumed(const Round119Contraction&);
    const Round119Certificate& proof(std::size_t i) const { return proofs_.at(i); }
    const std::vector<RoutePlan>& routes() const { return best_routes_; }
    double upper() const { return best_upper_; }
    bool failed() const { return !failure_.empty(); }
    const std::string& failure() const { return failure_; }
private:
    const Instance& instance_;
    SolveOptions options_;
    std::ofstream journal_;
    std::vector<Round119Certificate> proofs_;
    std::vector<Verification> witnesses_;
    std::vector<RoutePlan> best_routes_;
    double best_upper_ = std::numeric_limits<double>::infinity();
    double tolerance_ = 1e-7;
    std::string failure_;
    long long sequence_ = 0, own_updates_ = 0;
};
} // namespace ebrp
