#pragma once
#include "FixedIntervalMipBackend.hpp"
#include "PaperK1AmSf.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace ebrp {
// Compatibility adapter for the Round 59 fixed-state harness.  Both it and
// the paper K1 entry point now consume the same authoritative F0 contract.
inline void configureRound59CurrentF0(SolveOptions& o) {
    configurePaperK1AmSfCanonicalF0(o);
}
// Metric closure makes the lower bound valid even for nonmetric directed data:
// shortcut a realized route in the closure, not in the original distances.
inline std::vector<FixedIntervalMipRequest::AdditionalLinearRow>
round59PairDurationRows(const Instance& instance) {
    auto d = instance.dist;
    for (const auto& row : d) for (double t : row)
        if (!std::isfinite(t) || t < 0) throw std::runtime_error("invalid travel time");
    for (int h=0; h<=instance.V; ++h)
        for (int i=0; i<=instance.V; ++i)
            for (int j=0; j<=instance.V; ++j)
                d[i][j]=std::min(d[i][j], d[i][h]+d[h][j]);
    std::vector<FixedIntervalMipRequest::AdditionalLinearRow> rows;
    for (int k=0; k<instance.M; ++k)
        for (int a=1; a<=instance.V; ++a)
            for (int b=a+1; b<=instance.V; ++b) {
                const double t=std::min(d[0][a]+d[a][b]+d[b][0],
                                        d[0][b]+d[b][a]+d[a][0]);
                if (t<=0) continue;
                FixedIntervalMipRequest::AdditionalLinearRow row;
                const auto suffix=std::to_string(k)+"_"+std::to_string(a)+"_"+std::to_string(b);
                row.row_name="r59_pair_"+suffix;
                row.variable_names={"p_"+std::to_string(k)+"_"+std::to_string(a),
                                    "p_"+std::to_string(k)+"_"+std::to_string(b),
                                    "z_"+std::to_string(k)+"_"+std::to_string(a),
                                    "z_"+std::to_string(k)+"_"+std::to_string(b)};
                const double c=instance.pickup_time+instance.drop_time;
                row.coefficients={c,c,t,t};
                row.rhs=instance.total_time_limit+t;
                row.canonical_signature=row.row_name;
                row.scope="global";
                rows.push_back(std::move(row));
            }
    return rows;
}
} // namespace ebrp
