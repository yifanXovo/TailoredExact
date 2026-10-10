#pragma once

namespace ebrp {

struct TailoredBCCutValiditySummary {
    bool gini_subset_envelope_valid = true;
    bool low_gini_l1_centering_valid = true;
    bool local_centering_valid = true;
    bool subset_cross_h_centering_valid = true;
    bool local_q_centering_valid = true;
    bool subset_inventory_imbalance_valid = true;
    bool transfer_cutset_basic_valid = true;
    bool compatible_source_transfer_valid = true;
    bool required_external_source_valid = true;
    bool s_bucket_requires_full_coverage = true;
};

TailoredBCCutValiditySummary tailoredBCCutValiditySummary();

} // namespace ebrp
