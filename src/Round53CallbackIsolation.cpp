#include "Round53CallbackIsolation.hpp"

namespace ebrp {

bool round53CallbackPreCrushEnabled(
    const Round50IntervalMipPolicy& policy) {
    return policy.round53_callback_mode == "c1-precrush-only" ||
        policy.round53_callback_mode == "c3-status-precrush" ||
        policy.round53_callback_mode == "c4-separator-dry-run" ||
        policy.round53_callback_mode == "c5-live" ||
        policy.round53_callback_mode == "legacy-live-root" ||
        policy.round53_callback_mode == "legacy-live-tree";
}

bool round53CallbackMipNodeEnabled(
    const Round50IntervalMipPolicy& policy) {
    return policy.round53_callback_mode == "c2-status-only" ||
        policy.round53_callback_mode == "c3-status-precrush" ||
        round53CallbackSeparatorEnabled(policy);
}

bool round53CallbackRelaxationEnabled(
    const Round50IntervalMipPolicy& policy) {
    return round53CallbackSeparatorEnabled(policy);
}

bool round53CallbackSeparatorEnabled(
    const Round50IntervalMipPolicy& policy) {
    return policy.round53_callback_mode == "c4-separator-dry-run" ||
        policy.round53_callback_mode == "c5-live" ||
        policy.round53_callback_mode == "legacy-live-root" ||
        policy.round53_callback_mode == "legacy-live-tree";
}

bool round53CallbackSubmissionEnabled(
    const Round50IntervalMipPolicy& policy) {
    return policy.round53_callback_mode == "c5-live" ||
        policy.round53_callback_mode == "legacy-live-root" ||
        policy.round53_callback_mode == "legacy-live-tree";
}

} // namespace ebrp
