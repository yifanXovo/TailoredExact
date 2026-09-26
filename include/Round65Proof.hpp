#pragma once
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <string>
#include <set>

namespace ebrp {
// One account for initial/child LPs, proof closure and vehicle queries.
// Actual native overshoot is charged as debt, never rounded down to the grant.
struct Round65Budget {
    double seed_work = 30, seed_seconds = 30;
    double rho = .1, call_work = 10, call_seconds = 15;
    double optional_work = 0, core_work = 0;
    double optional_seconds = 0, core_seconds = 0;
    long long calls = 0;
    bool stopped = false;
    std::ofstream ledger;
    struct Grant { double work = 0, seconds = 0; bool allowed() const { return work > 0 && seconds > 0; } };
    Grant grant(double remaining) const {
        if (stopped || !std::isfinite(remaining) || remaining <= 0) return {};
        return {std::max(0., std::min(call_work, seed_work + rho*core_work - optional_work)),
                std::max(0., std::min({call_seconds, seed_seconds + rho*core_seconds - optional_seconds, remaining*.5}))};
    }
    void charge(bool optional, double work, double seconds,
                const std::string& state, const std::string& status, Grant g) {
        if (!std::isfinite(work) || !std::isfinite(seconds) || work < 0 || seconds < 0) {
            stopped = true; return;
        }
        (optional ? optional_work : core_work) += work;
        (optional ? optional_seconds : core_seconds) += seconds;
        if (ledger) {
            ledger << std::setprecision(17) << calls++ << ',' << std::quoted(state) << ','
                << (optional ? "optional" : "core") << ',' << status << ',' << g.work << ',' << g.seconds << ','
                << work << ',' << seconds << ',' << optional_work << ',' << core_work << ','
                << optional_seconds << ',' << core_seconds << '\n';
            ledger.flush();
        }
    }
};
} // namespace ebrp
