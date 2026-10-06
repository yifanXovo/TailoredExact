#include "Round105Decomposition.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <set>
#include <sstream>
#include <stdexcept>

namespace ebrp {
void round105ValidatePattern(const Instance& in, const Round105Pattern& p) {
    if (p.vehicle < 0 || p.vehicle >= in.M ||
        p.operation.size() != static_cast<std::size_t>(in.V + 1) || p.operation[0])
        throw std::runtime_error("round105_invalid_complete_pattern");
    for (int i = 1; i <= in.V; ++i) {
        const long long q = p.operation[i];
        if (q > std::min(in.initial[i], in.Q[p.vehicle]) ||
            -q > std::min(in.capacity[i] - in.initial[i], in.Q[p.vehicle]))
            throw std::runtime_error("round105_operation_outside_physical_domain");
    }
}
Round105Conflict round105Conflict(const Instance& in, const Round105Pattern& p,
                                  const std::vector<int>& assumptions) {
    round105ValidatePattern(in, p);
    if (assumptions.empty()) throw std::runtime_error("round105_empty_core");
    Round105Conflict out;
    std::set<int> seen;
    for (int i : assumptions) {
        if (i < 1 || i > in.V || !seen.insert(i).second)
            throw std::runtime_error("round105_invalid_assumption_group");
        const std::string z = "z_" + std::to_string(p.vehicle) + "_" + std::to_string(i);
        if (p.operation[i]) {
            out.coefficients[z] += 1;
            out.coefficients["state_" + std::to_string(i) + "_" +
                std::to_string(in.initial[i] - p.operation[i])] += 1;
            ++out.positive_groups;
        } else {
            out.coefficients[z] -= 1;
            ++out.negative_groups;
        }
    }
    // Sum mismatch >= 1: served has two true literals (z,state), absent one.
    out.rhs = 2 * out.positive_groups - 1;
    out.assumptions.assign(seen.begin(), seen.end());
    return out;
}
std::string round105PatternKey(const Instance& in, const Round105Pattern& p) {
    round105ValidatePattern(in, p);
    std::ostringstream s; s << std::setprecision(17);
    s << "R105-physical-v1/FeasTol-native/IntFeasTol-native/" << in.V << '/' << in.M
      << '/' << p.vehicle << '/' << in.Q[p.vehicle] << '/' << in.total_time_limit
      << '/' << in.pickup_time << '/' << in.drop_time;
    for (int i = 0; i <= in.V; ++i) {
        s << '/' << in.initial[i] << '/' << in.capacity[i] << '/' << p.operation[i];
        for (int j = 0; j <= in.V; ++j) s << '/' << in.dist[i][j];
    }
    return s.str();
}
void round105WriteOracle(const Instance& in, const Round105Pattern& p,
                        const std::vector<int>& assumptions,
                        const std::filesystem::path& path) {
    round105ValidatePattern(in, p);
    std::filesystem::create_directories(path.parent_path());
    std::ofstream f(path); if (!f) throw std::runtime_error("round105_oracle_write_failed");
    f << std::setprecision(17) << "Minimize\n obj: 0 z_1\nSubject To\n";
    int row = 0;
    auto name = [&](const std::string& kind, int i) { return kind + "_" + std::to_string(i); };
    auto x = [&](int i, int j) { return "x_" + std::to_string(i) + "_" + std::to_string(j); };
    using Terms = std::map<std::string,double>;
    auto emit = [&](const Terms& t, const std::string& sense, double rhs,
                    const std::string& explicit_name = "") {
        f << ' ' << (explicit_name.empty() ? "r" + std::to_string(++row) : explicit_name) << ':';
        bool any = false;
        for (const auto& [n,c] : t) if (c) {
            f << (c < 0 ? " - " : " + ") << std::abs(c) << ' ' << n; any = true;
        }
        if (!any) f << " 0 z_1";
        f << ' ' << sense << ' ' << rhs << '\n';
    };
    const int V = in.V, Q = in.Q[p.vehicle];
    Terms departure, balance, duration;
    for (int i = 1; i <= V; ++i) {
        departure[x(0,i)] = 1; balance[x(0,i)] = 1; balance[x(i,0)] = -1;
        Terms incoming{{name("z",i),-1}}, outgoing = incoming;
        for (int j = 0; j <= V; ++j) if (i != j) {
            incoming[x(j,i)] = 1; outgoing[x(i,j)] = 1;
        }
        emit(incoming,"=",0); emit(outgoing,"=",0);
        const int pm = std::min(in.initial[i],Q), dm = std::min(in.capacity[i]-in.initial[i],Q);
        emit({{name("mode",i),1},{name("z",i),-1}},"<=",0);
        emit({{name("p",i),1},{name("mode",i),-double(pm)}},"<=",0);
        emit({{name("d",i),1},{name("mode",i),double(dm)},{name("z",i),-double(dm)}},"<=",0);
        emit({{name("p",i),1},{name("d",i),1},{name("z",i),-1}},">=",0);
        emit({{name("load",i),1},{name("z",i),-double(Q)}},"<=",0);
        emit({{name("ord",i),1},{name("z",i),-double(V)}},"<=",0);
        emit({{name("ord",i),1},{name("z",i),-1}},">=",0);
        for (int sign : {-1,1}) {
            emit({{name("load",i),double(sign)},{name("p",i),-double(sign)},
                  {name("d",i),double(sign)},{x(0,i),2.0*Q}},"<=",2.0*Q);
        }
        duration[name("p",i)] = in.pickup_time + in.drop_time;
    }
    emit(departure,"<=",1); emit(balance,"=",0);
    for (int i = 0; i <= V; ++i) for (int j = 0; j <= V; ++j) if (i != j) {
        if (!std::isfinite(in.dist[i][j]) || in.dist[i][j] < 0)
            throw std::runtime_error("round105_invalid_travel");
        duration[x(i,j)] = in.dist[i][j];
        if (i && j) {
            emit({{name("ord",i),1},{name("ord",j),-1},{x(i,j),double(V+1)}},"<=",V);
            for (int sign : {-1,1})
                emit({{name("load",j),double(sign)},{name("load",i),-double(sign)},
                      {name("p",j),-double(sign)},{name("d",j),double(sign)},
                      {x(i,j),2.0*Q}},"<=",2.0*Q);
        }
    }
    emit(duration,"<=",in.total_time_limit);
    std::set<int> seen;
    for (int i : assumptions) {
        if (i < 1 || i > V || !seen.insert(i).second) throw std::runtime_error("round105_bad_assumption");
        const std::string a = "a_" + std::to_string(i) + "_";
        emit({{name("z",i),1}},"=",p.operation[i] ? 1 : 0,a+"z");
        if (p.operation[i]) {
            emit({{name("p",i),1}},"=",std::max(0,p.operation[i]),a+"p");
            emit({{name("d",i),1}},"=",std::max(0,-p.operation[i]),a+"d");
        }
    }
    f << "Bounds\n";
    for (int i = 1; i <= V; ++i) {
        f << " 0 <= p_" << i << " <= " << std::min(in.initial[i],Q) << '\n'
          << " 0 <= d_" << i << " <= " << std::min(in.capacity[i]-in.initial[i],Q) << '\n'
          << " 0 <= load_" << i << " <= " << Q << '\n'
          << " 0 <= ord_" << i << " <= " << V << '\n';
    }
    f << "Generals\n";
    for (int i = 1; i <= V; ++i) f << " p_" << i << " d_" << i << '\n';
    f << "Binaries\n";
    for (int i = 1; i <= V; ++i) f << " z_" << i << " mode_" << i << '\n';
    for (int i = 0; i <= V; ++i) for (int j = 0; j <= V; ++j) if (i != j) f << ' ' << x(i,j) << '\n';
    f << "End\n"; f.flush(); if (!f) throw std::runtime_error("round105_oracle_persist_failed");
}
} // namespace ebrp
