#pragma once

namespace ebrp {

struct TailoredBCCutValiditySummary {
    bool gini_subset_envelope_valid = true;
    bool low_gini_l1_centering_valid = true;
    bool transfer_cutset_basic_valid = true;
    bool s_bucket_requires_full_coverage = true;
};

TailoredBCCutValiditySummary tailoredBCCutValiditySummary();

} // namespace ebrp
