#pragma once
#include "ControllingLeafScheduler.hpp"
#include "Result.hpp"
#include <filesystem>
#include <limits>
#include <memory>

namespace ebrp {
// Each piece certifies F >= lower only inside its G interval and F <= cutoff.
// Its complement in objective value is covered by F >= cutoff, not by a clamp
// of a purported full-domain bound. Empty pieces have a verified infeasibility.
struct NativeEvidencePiece {
    std::string id, source;
    double lower_g = 0, upper_g = 0, lower = 0, cutoff = 0;
};
struct NativeEvidenceScope {
    bool full_original = false, native_preconditions = false;
    std::string leaf, model_sha256, model_path, model_scope, native_log_path;
    std::string settings_json = "{}";
    double lower_g = 0, upper_g = 0, cutoff = 0, gmax = 0;
    std::vector<NativeEvidencePiece> cover;
};
struct NativeEvidenceBound {
    bool available = false, inconsistent = false;
    double value = 0;
    std::string reason;
};
// Store new policy metadata in the existing JSON carrier. Scope is embedded
// in the public backend request; its inherited binary layout is preserved.
std::string nativeEvidencePreconditionReason(const NativeEvidenceScope&);
void setNativeEvidencePreconditionReason(NativeEvidenceScope&, const std::string&);
// Declared numerical policy. Expected values are never copied from readback.
struct NativeParameterSettings {
    int threads = 1, seed = 0, presolve = -1, mip_focus = 0, cuts = -1;
    double gap = 0, absolute_gap = 0, feasibility = 1e-6,
        integrality = 1e-5, optimality = 1e-6;
};
std::string nativeParameterMismatch(const NativeParameterSettings& expected,
    const NativeParameterSettings& actual, int read_return_code);
bool nativeEvidenceStatusQualified(int status, int read_return_code);
// A local source does not require a complete global cover. Witness membership
// is tested against this call's frozen physical domain before any complement.
NativeEvidenceBound evaluateNativeLocalBound(const NativeEvidenceScope&,
    double, const std::vector<Verification>&, double tolerance = 1e-7);
NativeEvidenceBound evaluateNativeLocalScope(const NativeEvidenceScope&);
NativeEvidenceBound evaluateNativeLocalInfeasibility(const NativeEvidenceScope&,
    const std::vector<Verification>&);
std::vector<NativeEvidencePiece> nativeEvidenceCover(
    const std::vector<ControllingLeaf>& leaves);
NativeEvidenceBound evaluateNativeEvidenceBound(const NativeEvidenceScope& scope,
    double native_bound, const std::vector<Verification>& witnesses,
    double tolerance = 1e-7);

// Same-run source qualification with optional immutable observation files.
// Callers must use localBound/proofUsable before consuming native claims.
class NativeEvidenceJournal {
public:
    NativeEvidenceJournal(const Instance&, const SolveOptions&);
    long long beginCall(const NativeEvidenceScope&);
    void witness(const std::vector<RoutePlan>&, const std::string& source, long long call = 0);
    void nativeBound(long long call, double bound);
    void returned(long long call, int return_code);
    void notStarted(long long call, const std::string& reason);
    void failure(const std::string& reason) noexcept;
    bool enabled() const { return !failed_; }
    bool proofUsable() const { return !failed_ && !source_rejected_; }
    bool sourceRejected() const { return source_rejected_; }
    const std::string& proofFailureReason() const { return proof_failure_reason_; }
    NativeEvidenceBound localBound(long long call, double bound) const;
    NativeEvidenceBound localScope(long long call) const;
    NativeEvidenceBound localInfeasibility(long long call) const;
    void nativeInfeasible(long long call);
    double bestObjective() const { return best_; }
    const std::vector<RoutePlan>& bestRoutes() const { return best_routes_; }
    void nativeQuality(long long call, const std::string& fields,
                       bool sufficient=true, const std::string& reason="");
private:
    void rejectSource(long long call, const std::string& reason);
    void publish(const std::string& kind, const std::string& fields);
    const Instance& instance_;
    const SolveOptions options_;
    std::filesystem::path directory_;
    long long sequence_ = 0;
    bool failed_ = false;
    bool source_rejected_ = false;
    std::string proof_failure_reason_;
    std::vector<NativeEvidenceScope> calls_;
    std::vector<double> last_bounds_;
    std::vector<bool> first_native_witness_;
    std::vector<bool> native_infeasible_;
    std::vector<Verification> witnesses_;
    std::vector<RoutePlan> best_routes_;
    double best_ = std::numeric_limits<double>::infinity();
};
// A receipt is accepted only when complete, its immutable data matches the
// hash/length, and both data-close time and reader observation fit the cutoff.
bool readNativeEvidenceReceipt(const std::filesystem::path& receipt,
    double observation_seconds, double cutoff_seconds, std::string& payload,
    std::string& reason);
} // namespace ebrp
