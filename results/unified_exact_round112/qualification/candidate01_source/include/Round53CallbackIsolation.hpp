#pragma once

#include "Round50IntervalMip.hpp"

namespace ebrp {

bool round53CallbackPreCrushEnabled(const Round50IntervalMipPolicy& policy);
bool round53CallbackMipNodeEnabled(const Round50IntervalMipPolicy& policy);
bool round53CallbackRelaxationEnabled(const Round50IntervalMipPolicy& policy);
bool round53CallbackSeparatorEnabled(const Round50IntervalMipPolicy& policy);
bool round53CallbackSubmissionEnabled(const Round50IntervalMipPolicy& policy);

} // namespace ebrp
