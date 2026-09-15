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
std::vector<NativeEvidencePiece> nativeEvidenceCover(
    const std::vector<ControllingLeaf>& leaves);
NativeEvidenceBound evaluateNativeEvidenceBound(const NativeEvidenceScope& scope,
    double native_bound, const std::vector<Verification>& witnesses,
    double tolerance = 1e-7);

// Read-only, same-run observer. No callback termination, Start, cut, bound
// import or algorithm selection is performed by this class.
class NativeEvidenceJournal {
public:
    NativeEvidenceJournal(const Instance&, const SolveOptions&);
    long long beginCall(const NativeEvidenceScope&);
    void witness(const std::vector<RoutePlan>&, const std::string& source, long long call = 0);
    void nativeBound(long long call, double bound);
    void returned(long long call, int return_code);
    void failure(const std::string& reason) noexcept;
    bool enabled() const { return !failed_; }
private:
    void publish(const std::string& kind, const std::string& fields);
    const Instance& instance_;
    const SolveOptions options_;
    std::filesystem::path directory_;
    long long sequence_ = 0;
    bool failed_ = false;
    std::vector<NativeEvidenceScope> calls_;
    std::vector<double> last_bounds_;
    std::vector<bool> first_native_witness_;
    std::vector<Verification> witnesses_;
    double best_ = std::numeric_limits<double>::infinity();
};
// A receipt is accepted only when complete, its immutable data matches the
// hash/length, and both data-close time and reader observation fit the cutoff.
bool readNativeEvidenceReceipt(const std::filesystem::path& receipt,
    double observation_seconds, double cutoff_seconds, std::string& payload,
    std::string& reason);
} // namespace ebrp
