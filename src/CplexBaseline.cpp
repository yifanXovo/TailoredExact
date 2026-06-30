#include "CplexBaseline.hpp"

#include "Evaluator.hpp"
#include "Logger.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <unordered_map>

namespace ebrp {
namespace {

using Clock = std::chrono::steady_clock;
using Expr = std::map<std::string, double>;

struct VarRegistry {
    std::map<std::string, std::pair<double, double>> bounds;
    std::set<std::string> binaries;
    std::set<std::string> generals;

    void add(const std::string& name, double lb, double ub, const std::string& type) {
        bounds[name] = {lb, ub};
        if (type == "B") binaries.insert(name);
        if (type == "I") generals.insert(name);
    }
};

struct CompactIntervalCutoffConfig {
    bool enabled = false;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    double incumbent_ub = 0.0;
    double epsilon = 1e-8;
};

void addTerm(Expr& e, const std::string& var, double coef) {
    if (std::fabs(coef) <= 1e-12) return;
    e[var] += coef;
    if (std::fabs(e[var]) <= 1e-12) e.erase(var);
}

std::string num(double v) {
    std::ostringstream ss;
    ss << std::setprecision(12) << v;
    return ss.str();
}

void writeExpr(std::ostream& out, const Expr& e) {
    if (e.empty()) {
        out << "0";
        return;
    }
    bool first = true;
    for (const auto& kv : e) {
        const double c = kv.second;
        if (first) {
            if (c < 0) out << "- ";
        } else {
            out << (c < 0 ? " - " : " + ");
        }
        const double a = std::fabs(c);
        if (std::fabs(a - 1.0) > 1e-12) out << num(a) << " ";
        out << kv.first;
        first = false;
    }
}

void writeConstraint(std::ostream& out,
                     int& id,
                     const Expr& e,
                     const std::string& sense,
                     double rhs) {
    out << " c" << id++ << ": ";
    writeExpr(out, e);
    out << " " << sense << " " << num(rhs) << "\n";
}

std::string xName(int k, int i, int j) { return "x_" + std::to_string(k) + "_" + std::to_string(i) + "_" + std::to_string(j); }
std::string zName(int k, int i) { return "z_" + std::to_string(k) + "_" + std::to_string(i); }
std::string pName(int k, int i) { return "p_" + std::to_string(k) + "_" + std::to_string(i); }
std::string dName(int k, int i) { return "d_" + std::to_string(k) + "_" + std::to_string(i); }
std::string lName(int k, int i) { return "load_" + std::to_string(k) + "_" + std::to_string(i); }
std::string uName(int k, int i) { return "ord_" + std::to_string(k) + "_" + std::to_string(i); }
std::string mName(int k, int i) { return "mode_" + std::to_string(k) + "_" + std::to_string(i); }
std::string yName(int i) { return "Y_" + std::to_string(i); }
std::string rName(int i) { return "r_" + std::to_string(i); }
std::string eName(int i) { return "e_" + std::to_string(i); }
std::string hName(int i, int j) { return "h_" + std::to_string(i) + "_" + std::to_string(j); }
std::string bitName(int i, int b) { return "bit_" + std::to_string(i) + "_" + std::to_string(b); }
std::string prodName(int i, int b) { return "prod_" + std::to_string(i) + "_" + std::to_string(b); }
std::string zprodName(int i) { return "zprod_" + std::to_string(i); }

std::vector<double> subsetTspLowerBounds(const Instance& instance) {
    const int V = instance.V;
    const int nmask = 1 << V;
    const double inf = 1e100;
    std::vector<std::vector<double>> dp(nmask, std::vector<double>(V, inf));
    for (int j = 0; j < V; ++j) dp[1 << j][j] = instance.dist[0][j + 1];
    for (int mask = 1; mask < nmask; ++mask) {
        for (int last = 0; last < V; ++last) {
            const double val = dp[mask][last];
            if (val >= inf / 2) continue;
            int rem = (nmask - 1) ^ mask;
            while (rem) {
                const int bit = rem & -rem;
                const int nxt = __builtin_ctz(static_cast<unsigned int>(bit));
                const int nm = mask | bit;
                dp[nm][nxt] = std::min(dp[nm][nxt], val + instance.dist[last + 1][nxt + 1]);
                rem -= bit;
            }
        }
    }
    std::vector<double> tsp(nmask, 0.0);
    for (int mask = 1; mask < nmask; ++mask) {
        double best = inf;
        int m = mask;
        while (m) {
            const int bit = m & -m;
            const int last = __builtin_ctz(static_cast<unsigned int>(bit));
            best = std::min(best, dp[mask][last] + instance.dist[last + 1][0]);
            m -= bit;
        }
        tsp[mask] = best;
    }
    return tsp;
}

void writeCompactLp(const Instance& instance,
                    const SolveOptions& options,
                    const std::filesystem::path& lp_path,
                    bool strengthened,
                    const CompactIntervalCutoffConfig* cutoff = nullptr) {
    VarRegistry vars;
    const int V = instance.V;
    const int M = instance.M;
    const double cunit = instance.pickup_time + instance.drop_time;

    for (int k = 0; k < M; ++k) {
        for (int i = 0; i <= V; ++i) {
            for (int j = 0; j <= V; ++j) {
                if (i != j) vars.add(xName(k, i, j), 0, 1, "B");
            }
        }
        for (int i = 1; i <= V; ++i) {
            const int pmax = std::min(instance.initial[i], instance.Q[k]);
            const int dmax = std::min(instance.capacity[i] - instance.initial[i], instance.Q[k]);
            vars.add(zName(k, i), 0, 1, "B");
            vars.add(mName(k, i), 0, 1, "B");
            vars.add(pName(k, i), 0, pmax, "I");
            vars.add(dName(k, i), 0, dmax, "I");
            vars.add(lName(k, i), 0, instance.Q[k], "I");
            vars.add(uName(k, i), 0, V, "C");
        }
    }
    vars.add("G", 0, 1, "C");
    for (int i = 1; i <= V; ++i) {
        vars.add(yName(i), 0, instance.capacity[i], "I");
        vars.add(rName(i), 0, static_cast<double>(instance.capacity[i]) / instance.target[i], "C");
        vars.add(eName(i), 0, std::max(1.0, static_cast<double>(instance.capacity[i]) / instance.target[i] - 1.0), "C");
        vars.add(zprodName(i), 0, instance.capacity[i], "C");
        int bits = 1;
        while (((1LL << bits) - 1) < instance.capacity[i]) ++bits;
        for (int b = 0; b < bits; ++b) {
            vars.add(bitName(i, b), 0, 1, "B");
            vars.add(prodName(i, b), 0, 1, "C");
        }
    }
    for (int i = 1; i <= V; ++i) {
        for (int j = i + 1; j <= V; ++j) {
            const double ub = static_cast<double>(instance.capacity[i]) / instance.target[i]
                + static_cast<double>(instance.capacity[j]) / instance.target[j];
            vars.add(hName(i, j), 0, ub, "C");
        }
    }

    std::filesystem::create_directories(lp_path.parent_path());
    std::ofstream out(lp_path);
    if (!out) throw std::runtime_error("Cannot write CPLEX LP: " + lp_path.string());
    out << std::setprecision(12);
    out << "\\ ExactEBRP compact MILP generated from C++ command-line runner\n";
    out << "Minimize\n obj: G";
    for (int i = 1; i <= V; ++i) {
        const double coef = options.lambda * instance.weights[i];
        if (coef >= 0) out << " + " << num(coef) << " " << eName(i);
        else out << " - " << num(-coef) << " " << eName(i);
    }
    out << "\nSubject To\n";

    int cid = 1;
    for (int k = 0; k < M; ++k) {
        Expr start_end;
        Expr start;
        for (int j = 1; j <= V; ++j) {
            addTerm(start, xName(k, 0, j), 1);
            addTerm(start_end, xName(k, 0, j), 1);
            addTerm(start_end, xName(k, j, 0), -1);
        }
        writeConstraint(out, cid, start_end, "=", 0);
        writeConstraint(out, cid, start, "<=", 1);
        for (int i = 1; i <= V; ++i) {
            Expr in_flow;
            Expr out_flow;
            for (int j = 0; j <= V; ++j) {
                if (j == i) continue;
                addTerm(in_flow, xName(k, j, i), 1);
                addTerm(out_flow, xName(k, i, j), 1);
            }
            addTerm(in_flow, zName(k, i), -1);
            addTerm(out_flow, zName(k, i), -1);
            writeConstraint(out, cid, in_flow, "=", 0);
            writeConstraint(out, cid, out_flow, "=", 0);
        }
    }

    for (int i = 1; i <= V; ++i) {
        Expr e;
        for (int k = 0; k < M; ++k) addTerm(e, zName(k, i), 1);
        writeConstraint(out, cid, e, "<=", 1);
    }

    for (int k = 0; k < M; ++k) {
        for (int i = 1; i <= V; ++i) {
            Expr lb; addTerm(lb, uName(k, i), 1); addTerm(lb, zName(k, i), -1);
            writeConstraint(out, cid, lb, ">=", 0);
            Expr ub; addTerm(ub, uName(k, i), 1); addTerm(ub, zName(k, i), -V);
            writeConstraint(out, cid, ub, "<=", 0);
        }
        for (int i = 1; i <= V; ++i) {
            for (int j = 1; j <= V; ++j) {
                if (i == j) continue;
                Expr e;
                addTerm(e, uName(k, i), 1);
                addTerm(e, uName(k, j), -1);
                addTerm(e, xName(k, i, j), V);
                writeConstraint(out, cid, e, "<=", V - 1);
            }
        }
    }

    for (int k = 0; k < M; ++k) {
        const int Q = instance.Q[k];
        for (int i = 1; i <= V; ++i) {
            const int pmax = std::min(instance.initial[i], Q);
            const int dmax = std::min(instance.capacity[i] - instance.initial[i], Q);
            Expr ep; addTerm(ep, pName(k, i), 1); addTerm(ep, zName(k, i), -pmax);
            writeConstraint(out, cid, ep, "<=", 0);
            Expr ed; addTerm(ed, dName(k, i), 1); addTerm(ed, zName(k, i), -dmax);
            writeConstraint(out, cid, ed, "<=", 0);
            Expr mm; addTerm(mm, mName(k, i), 1); addTerm(mm, zName(k, i), -1);
            writeConstraint(out, cid, mm, "<=", 0);
            Expr pm; addTerm(pm, pName(k, i), 1); addTerm(pm, mName(k, i), -pmax);
            writeConstraint(out, cid, pm, "<=", 0);
            Expr dm; addTerm(dm, dName(k, i), 1); addTerm(dm, zName(k, i), -dmax); addTerm(dm, mName(k, i), dmax);
            writeConstraint(out, cid, dm, "<=", 0);
            Expr nonzero; addTerm(nonzero, pName(k, i), 1); addTerm(nonzero, dName(k, i), 1); addTerm(nonzero, zName(k, i), -1);
            writeConstraint(out, cid, nonzero, ">=", 0);
            Expr loadz; addTerm(loadz, lName(k, i), 1); addTerm(loadz, zName(k, i), -Q);
            writeConstraint(out, cid, loadz, "<=", 0);
        }

        for (int i = 1; i <= V; ++i) {
            Expr up;
            addTerm(up, lName(k, i), 1);
            addTerm(up, pName(k, i), -1);
            addTerm(up, dName(k, i), 1);
            addTerm(up, xName(k, 0, i), Q);
            writeConstraint(out, cid, up, "<=", Q);
            Expr lo;
            addTerm(lo, lName(k, i), 1);
            addTerm(lo, pName(k, i), -1);
            addTerm(lo, dName(k, i), 1);
            addTerm(lo, xName(k, 0, i), -Q);
            writeConstraint(out, cid, lo, ">=", -Q);
        }
        for (int i = 1; i <= V; ++i) {
            for (int j = 1; j <= V; ++j) {
                if (i == j) continue;
                Expr up;
                addTerm(up, lName(k, j), 1);
                addTerm(up, lName(k, i), -1);
                addTerm(up, pName(k, j), -1);
                addTerm(up, dName(k, j), 1);
                addTerm(up, xName(k, i, j), Q);
                writeConstraint(out, cid, up, "<=", Q);
                Expr lo;
                addTerm(lo, lName(k, j), 1);
                addTerm(lo, lName(k, i), -1);
                addTerm(lo, pName(k, j), -1);
                addTerm(lo, dName(k, j), 1);
                addTerm(lo, xName(k, i, j), -Q);
                writeConstraint(out, cid, lo, ">=", -Q);
            }
        }
        Expr final_load;
        for (int i = 1; i <= V; ++i) {
            addTerm(final_load, pName(k, i), 1);
            addTerm(final_load, dName(k, i), -1);
        }
        writeConstraint(out, cid, final_load, ">=", 0);

        Expr duration;
        for (int i = 0; i <= V; ++i) {
            for (int j = 0; j <= V; ++j) {
                if (i != j) addTerm(duration, xName(k, i, j), instance.dist[i][j]);
            }
        }
        for (int i = 1; i <= V; ++i) addTerm(duration, pName(k, i), cunit);
        writeConstraint(out, cid, duration, "<=", instance.total_time_limit);
    }

    if (strengthened && V <= 12) {
        const std::vector<double> tsp = subsetTspLowerBounds(instance);
        const double big = 100000.0;
        for (int k = 0; k < M; ++k) {
            for (int mask = 1; mask < (1 << V); ++mask) {
                Expr e;
                int count = 0;
                for (int b = 0; b < V; ++b) {
                    if (mask & (1 << b)) {
                        const int i = b + 1;
                        ++count;
                        addTerm(e, pName(k, i), cunit);
                        addTerm(e, zName(k, i), big);
                    }
                }
                writeConstraint(out, cid, e, "<=", instance.total_time_limit - tsp[mask] + big * count);
            }
        }
    }

    const bool identical_q = std::all_of(instance.Q.begin(), instance.Q.end(),
        [&](int q) { return q == instance.Q.front(); });
    if (strengthened && options.interval_oracle_symmetry_breaking && identical_q && M > 1) {
        for (int k = 0; k + 1 < M; ++k) {
            Expr e;
            for (int i = 1; i <= V; ++i) {
                addTerm(e, zName(k, i), 1);
                addTerm(e, zName(k + 1, i), -1);
            }
            writeConstraint(out, cid, e, ">=", 0);
        }
    }

    for (int i = 1; i <= V; ++i) {
        Expr inv;
        addTerm(inv, yName(i), 1);
        for (int k = 0; k < M; ++k) {
            addTerm(inv, pName(k, i), 1);
            addTerm(inv, dName(k, i), -1);
        }
        writeConstraint(out, cid, inv, "=", instance.initial[i]);
        Expr ratio; addTerm(ratio, rName(i), 1); addTerm(ratio, yName(i), -1.0 / instance.target[i]);
        writeConstraint(out, cid, ratio, "=", 0);
        Expr ep; addTerm(ep, eName(i), 1); addTerm(ep, rName(i), -1);
        writeConstraint(out, cid, ep, ">=", -1);
        Expr em; addTerm(em, eName(i), 1); addTerm(em, rName(i), 1);
        writeConstraint(out, cid, em, ">=", 1);
    }
    for (int i = 1; i <= V; ++i) {
        for (int j = i + 1; j <= V; ++j) {
            Expr h1; addTerm(h1, hName(i, j), 1); addTerm(h1, rName(i), -1); addTerm(h1, rName(j), 1);
            writeConstraint(out, cid, h1, ">=", 0);
            Expr h2; addTerm(h2, hName(i, j), 1); addTerm(h2, rName(i), 1); addTerm(h2, rName(j), -1);
            writeConstraint(out, cid, h2, ">=", 0);
        }
    }

    for (int i = 1; i <= V; ++i) {
        int bits = 1;
        while (((1LL << bits) - 1) < instance.capacity[i]) ++bits;
        Expr ybits; addTerm(ybits, yName(i), 1);
        Expr zprod; addTerm(zprod, zprodName(i), 1);
        for (int b = 0; b < bits; ++b) {
            const double coef = static_cast<double>(1LL << b);
            addTerm(ybits, bitName(i, b), -coef);
            addTerm(zprod, prodName(i, b), -coef);
        }
        writeConstraint(out, cid, ybits, "=", 0);
        writeConstraint(out, cid, zprod, "=", 0);
        for (int b = 0; b < bits; ++b) {
            Expr p_le_g; addTerm(p_le_g, prodName(i, b), 1); addTerm(p_le_g, "G", -1);
            writeConstraint(out, cid, p_le_g, "<=", 0);
            Expr p_le_bit; addTerm(p_le_bit, prodName(i, b), 1); addTerm(p_le_bit, bitName(i, b), -1);
            writeConstraint(out, cid, p_le_bit, "<=", 0);
            Expr p_ge; addTerm(p_ge, prodName(i, b), 1); addTerm(p_ge, "G", -1); addTerm(p_ge, bitName(i, b), -1);
            writeConstraint(out, cid, p_ge, ">=", -1);
        }
    }
    Expr gini;
    for (int i = 1; i <= V; ++i) addTerm(gini, zprodName(i), static_cast<double>(V) / instance.target[i]);
    for (int i = 1; i <= V; ++i) {
        for (int j = i + 1; j <= V; ++j) addTerm(gini, hName(i, j), -1);
    }
    writeConstraint(out, cid, gini, ">=", 0);

    if (cutoff != nullptr && cutoff->enabled) {
        Expr gl; addTerm(gl, "G", 1);
        writeConstraint(out, cid, gl, ">=", cutoff->gamma_L);
        Expr gu; addTerm(gu, "G", 1);
        writeConstraint(out, cid, gu, "<=", cutoff->gamma_U);
        Expr obj_cutoff; addTerm(obj_cutoff, "G", 1);
        for (int i = 1; i <= V; ++i) {
            addTerm(obj_cutoff, eName(i), options.lambda * instance.weights[i]);
        }
        writeConstraint(out, cid, obj_cutoff, "<=", cutoff->incumbent_ub - cutoff->epsilon);

        if ((options.interval_oracle_penalty_domain_tightening ||
             options.interval_oracle_low_gini_tightening) &&
            options.lambda > 1e-12) {
            const double cutoff_value = cutoff->incumbent_ub - cutoff->epsilon;
            const double penalty_budget = (cutoff_value - cutoff->gamma_L) / options.lambda;
            if (std::isfinite(penalty_budget) && penalty_budget >= -1e-10) {
                for (int i = 1; i <= V; ++i) {
                    if (instance.weights[i] <= 1e-12) continue;
                    const double e_ub = std::max(0.0, penalty_budget / instance.weights[i]);
                    Expr ei; addTerm(ei, eName(i), 1);
                    writeConstraint(out, cid, ei, "<=", e_ub);
                }
            }
        }
    }

    out << "Bounds\n";
    for (const auto& kv : vars.bounds) {
        if (kv.second.second >= 1e90) out << " " << num(kv.second.first) << " <= " << kv.first << "\n";
        else out << " " << num(kv.second.first) << " <= " << kv.first << " <= " << num(kv.second.second) << "\n";
    }
    if (!vars.generals.empty()) {
        out << "Generals\n";
        for (const auto& v : vars.generals) out << " " << v << "\n";
    }
    if (!vars.binaries.empty()) {
        out << "Binaries\n";
        for (const auto& v : vars.binaries) out << " " << v << "\n";
    }
    out << "End\n";
}

std::string defaultCplexPath() {
    const char* bin = std::getenv("CPLEX_STUDIO_BINARIES2211");
    if (bin && *bin) {
        std::string s(bin);
        const std::size_t semi = s.find(';');
        if (semi != std::string::npos) s = s.substr(0, semi);
        std::filesystem::path p = std::filesystem::path(s) / "cplex.exe";
        if (std::filesystem::exists(p)) return p.string();
    }
    const std::filesystem::path fallback =
        "C:/Program Files/IBM/ILOG/CPLEX_Studio2211/cplex/bin/x64_win64/cplex.exe";
    if (std::filesystem::exists(fallback)) return fallback.string();
    return "cplex.exe";
}

std::string quote(const std::filesystem::path& p) {
    return "\"" + p.string() + "\"";
}

std::unordered_map<std::string, double> parseSolValues(const std::filesystem::path& sol_path,
                                                       std::string& status,
                                                       double& objective,
                                                       double& best_bound) {
    std::ifstream in(sol_path);
    if (!in) throw std::runtime_error("CPLEX solution file missing: " + sol_path.string());
    std::ostringstream ss;
    ss << in.rdbuf();
    const std::string text = ss.str();

    std::smatch m;
    if (std::regex_search(text, m, std::regex("solutionStatusString=\"([^\"]*)\""))) status = m[1].str();
    if (std::regex_search(text, m, std::regex("objectiveValue=\"([^\"]*)\""))) objective = std::stod(m[1].str());
    if (std::regex_search(text, m, std::regex("bestObjective=\"([^\"]*)\""))) best_bound = std::stod(m[1].str());

    std::unordered_map<std::string, double> values;
    const std::regex var_re("<variable [^>]*name=\"([^\"]+)\"[^>]*value=\"([^\"]+)\"");
    for (auto it = std::sregex_iterator(text.begin(), text.end(), var_re);
         it != std::sregex_iterator(); ++it) {
        values[it->str(1)] = std::stod(it->str(2));
    }
    return values;
}

long long parseCplexNodes(const std::filesystem::path& log_path) {
    std::ifstream in(log_path);
    if (!in) return 0;
    std::ostringstream ss;
    ss << in.rdbuf();
    const std::string text = ss.str();
    std::smatch m;
    long long nodes = 0;
    const std::regex nodes_re(R"(Nodes\s*=\s*([0-9]+))");
    for (auto it = std::sregex_iterator(text.begin(), text.end(), nodes_re);
         it != std::sregex_iterator(); ++it) {
        nodes = std::stoll(it->str(1));
    }
    return nodes;
}

double parseCplexBestBound(const std::filesystem::path& log_path) {
    std::ifstream in(log_path);
    if (!in) return std::numeric_limits<double>::quiet_NaN();
    std::ostringstream ss;
    ss << in.rdbuf();
    const std::string text = ss.str();
    std::smatch m;
    double bound = std::numeric_limits<double>::quiet_NaN();
    const std::regex final_bound_re(R"(Current MIP best bound\s*=\s*([-+0-9.eE]+))");
    if (std::regex_search(text, m, final_bound_re)) {
        bound = std::stod(m[1].str());
    }
    return bound;
}

std::string parseCplexTerminalStatus(const std::filesystem::path& log_path) {
    std::ifstream in(log_path);
    if (!in) return "log missing";
    std::ostringstream ss;
    ss << in.rdbuf();
    std::string text = ss.str();
    std::string lower = text;
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    if (lower.find("time limit exceeded") != std::string::npos) {
        return "time limit exceeded";
    }
    if (lower.find("integer infeasible") != std::string::npos ||
        lower.find("mip - integer infeasible") != std::string::npos ||
        lower.find("problem is integer infeasible") != std::string::npos ||
        lower.find("infeasibility row") != std::string::npos) {
        return "infeasible";
    }
    if (lower.find("optimal") != std::string::npos) {
        return "optimal";
    }
    return "unknown";
}

std::vector<RoutePlan> reconstructRoutes(const Instance& instance,
                                         const std::unordered_map<std::string, double>& v) {
    std::vector<RoutePlan> routes;
    for (int k = 0; k < instance.M; ++k) {
        RoutePlan route;
        route.vehicle = k;
        route.nodes.push_back(0);
        int current = 0;
        std::set<int> seen;
        while (true) {
            int next = -1;
            for (int j = 0; j <= instance.V; ++j) {
                if (j == current) continue;
                auto it = v.find(xName(k, current, j));
                if (it != v.end() && it->second > 0.5) {
                    next = j;
                    break;
                }
            }
            if (next <= 0) break;
            if (!seen.insert(next).second) break;
            route.nodes.push_back(next);
            current = next;
        }
        route.nodes.push_back(0);
        for (std::size_t idx = 1; idx + 1 < route.nodes.size(); ++idx) {
            const int station = route.nodes[idx];
            StopOperation op;
            op.station = station;
            auto pit = v.find(pName(k, station));
            auto dit = v.find(dName(k, station));
            op.pickup = (pit == v.end()) ? 0 : static_cast<int>(std::llround(pit->second));
            op.drop = (dit == v.end()) ? 0 : static_cast<int>(std::llround(dit->second));
            route.operations.push_back(op);
        }
        routes.push_back(std::move(route));
    }
    return routes;
}

bool statusIsOptimal(const std::string& status) {
    std::string s = status;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s.find("optimal") != std::string::npos;
}

bool statusIsInfeasible(const std::string& status) {
    std::string s = status;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s.find("infeasible") != std::string::npos;
}

bool statusIsTimeLimited(const std::string& status) {
    std::string s = status;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s.find("time") != std::string::npos || s.find("limit") != std::string::npos;
}

} // namespace

SolveResult solveCplexBaseline(const Instance& instance, const SolveOptions& options) {
    const auto start = Clock::now();
    SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "cplex";
    result.status = "running";
    result.notes.push_back(instance.distance_convention);

    const bool strengthened = !options.plain_baseline;
    result.notes.push_back(strengthened
        ? "CPLEX compact MILP with operation-time conservation, mode constraints, subset duration cuts, and symmetry cuts."
        : "CPLEX compact MILP with operation-time conservation and original-style Gini product linearization.");

    try {
        const std::string stem = std::filesystem::path(instance.name).stem().string()
            + (strengthened ? "_strengthened" : "_plain");
        const auto run_id = std::chrono::duration_cast<std::chrono::milliseconds>(
            Clock::now().time_since_epoch()).count();
        const std::filesystem::path work_dir = std::filesystem::path("results") / "cplex_work"
            / (stem + "_" + std::to_string(run_id));
        std::filesystem::create_directories(work_dir);
        const std::filesystem::path lp_path = work_dir / "model.lp";
        const std::filesystem::path sol_path = work_dir / "solution.sol";
        const std::filesystem::path cmd_path = work_dir / "run.cplex";
        const std::filesystem::path cplex_log = options.log_path.empty()
            ? (work_dir / "cplex.log") : std::filesystem::path(options.log_path);
        result.log_file = cplex_log.string();
        result.notes.push_back("CPLEX command file sets threads="
            + std::to_string(std::max(1, options.threads))
            + "; this is the current baseline behavior and was not changed for the threading audit.");
        std::error_code ignored;
        std::filesystem::remove(sol_path, ignored);
        std::filesystem::remove(cplex_log, ignored);

        writeCompactLp(instance, options, lp_path, strengthened);

        std::ofstream cmd(cmd_path);
        cmd << "set threads " << std::max(1, options.threads) << "\n";
        cmd << "set timelimit " << options.solve_time_limit << "\n";
        cmd << "set mip tolerances mipgap 1e-8\n";
        cmd << "read " << lp_path.string() << "\n";
        cmd << "optimize\n";
        cmd << "write " << sol_path.string() << "\n";
        cmd << "quit\n";
        cmd.close();

        const std::string cplex = defaultCplexPath();
        std::filesystem::create_directories(cplex_log.parent_path());
        const std::string command = "cmd /C \"" + quote(cplex) + " -f "
            + quote(cmd_path) + " > " + quote(cplex_log) + " 2>&1\"";
        const int rc = std::system(command.c_str());
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();

        std::string cplex_status = "unknown";
        double cplex_obj = 0.0;
        double best_bound = std::numeric_limits<double>::quiet_NaN();
        auto values = parseSolValues(sol_path, cplex_status, cplex_obj, best_bound);
        result.nodes = parseCplexNodes(cplex_log);
        const double log_best_bound = parseCplexBestBound(cplex_log);
        if (!std::isfinite(best_bound) && std::isfinite(log_best_bound)) best_bound = log_best_bound;
        result.routes = reconstructRoutes(instance, values);
        result.verification = verifySolution(instance, result.routes, options.lambda);
        result.final_inventory = result.verification.final_inventory;
        result.G = result.verification.G;
        result.P = result.verification.P;
        result.objective = result.verification.objective;
        result.upper_bound = result.objective;
        if (statusIsOptimal(cplex_status)) {
            result.status = result.verification.feasible ? "optimal" : "verification_failed";
            result.lower_bound = result.objective;
            result.gap = 0.0;
            result.certificate = result.verification.feasible
                ? "CPLEX reported optimality and the independent verifier recomputed the same feasible objective."
                : "CPLEX reported optimality, but the independent verifier rejected the reconstructed solution.";
        } else {
            result.status = "not_certified";
            result.lower_bound = std::isfinite(best_bound) ? best_bound : 0.0;
            result.gap = (std::fabs(result.upper_bound) > 1e-12)
                ? std::max(0.0, (result.upper_bound - result.lower_bound) / std::fabs(result.upper_bound))
                : 0.0;
            result.certificate = "CPLEX did not report optimality: " + cplex_status;
        }
        result.notes.push_back("CPLEX solution status: " + cplex_status);
        result.notes.push_back("CPLEX process return code: " + std::to_string(rc));
        result.notes.push_back("LP file: " + lp_path.string());
        result.notes.push_back("CPLEX log: " + cplex_log.string());
    } catch (const std::exception& e) {
        result.status = "error";
        result.certificate = std::string("CPLEX baseline failed: ") + e.what();
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
    }

    return result;
}

SolveResult solveIntervalExactCutoffOracle(const Instance& instance, const SolveOptions& options) {
    const auto start = Clock::now();
    SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "interval-cutoff-oracle";
    result.status = "running";
    result.certificate_scope = "interval_original_cutoff_oracle";
    result.interval_exact_cutoff_oracle = options.interval_exact_cutoff_oracle;
    result.interval_exact_cutoff_attempted = true;
    result.interval_exact_cutoff_gamma_L = options.interval_exact_cutoff_gamma_L;
    result.interval_exact_cutoff_gamma_U = options.interval_exact_cutoff_gamma_U;
    result.interval_exact_cutoff_UB = options.interval_exact_cutoff_UB;
    result.interval_exact_cutoff_epsilon = options.interval_exact_cutoff_epsilon;
    result.interval_exact_cutoff_scope = "original fixed-interval cutoff feasibility compact MIP";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Interval oracle is local to one Gini interval. It never certifies the full original problem unless merged into a complete full-frontier ledger.");

    const bool params_valid =
        options.interval_exact_cutoff_oracle == "compact-mip" &&
        std::isfinite(options.interval_exact_cutoff_gamma_L) &&
        std::isfinite(options.interval_exact_cutoff_gamma_U) &&
        options.interval_exact_cutoff_gamma_L >= -1e-12 &&
        options.interval_exact_cutoff_gamma_U >= options.interval_exact_cutoff_gamma_L - 1e-12 &&
        std::isfinite(options.interval_exact_cutoff_UB) &&
        options.interval_exact_cutoff_UB > 0.0;
    if (!params_valid) {
        result.status = "error";
        result.certificate = "interval cutoff oracle requires --interval-exact-cutoff-oracle compact-mip, valid gamma bounds, and positive --interval-exact-cutoff-UB";
        result.interval_exact_cutoff_certificate_basis = "interval_exact_cutoff_mip_invalid_parameters";
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        return result;
    }

    try {
        const std::string stem = std::filesystem::path(instance.name).stem().string()
            + "_interval_cutoff_"
            + std::to_string(static_cast<long long>(std::llround(options.interval_exact_cutoff_gamma_L * 1000000000.0)))
            + "_"
            + std::to_string(static_cast<long long>(std::llround(options.interval_exact_cutoff_gamma_U * 1000000000.0)));
        const auto run_id = std::chrono::duration_cast<std::chrono::milliseconds>(
            Clock::now().time_since_epoch()).count();
        const std::filesystem::path default_dir = std::filesystem::path("results") / "interval_cutoff_work"
            / (stem + "_" + std::to_string(run_id));
        std::filesystem::create_directories(default_dir);
        const std::filesystem::path lp_path = options.interval_exact_cutoff_export_lp.empty()
            ? (default_dir / "interval_cutoff.lp")
            : std::filesystem::path(options.interval_exact_cutoff_export_lp);
        const std::filesystem::path sol_path = options.interval_exact_cutoff_result.empty()
            ? (default_dir / "interval_cutoff.sol")
            : std::filesystem::path(options.interval_exact_cutoff_result);
        const std::filesystem::path cmd_path = default_dir / "run_interval_cutoff.cplex";
        const std::filesystem::path cplex_log = options.log_path.empty()
            ? (default_dir / "interval_cutoff.cplex.log") : std::filesystem::path(options.log_path);
        result.log_file = cplex_log.string();
        result.interval_exact_cutoff_lp_path = lp_path.string();
        result.interval_exact_cutoff_solution_path = sol_path.string();
        result.interval_exact_cutoff_log_path = cplex_log.string();

        std::filesystem::create_directories(lp_path.parent_path());
        std::filesystem::create_directories(sol_path.parent_path());
        std::filesystem::create_directories(cplex_log.parent_path());
        std::error_code ignored;
        std::filesystem::remove(sol_path, ignored);
        std::filesystem::remove(cplex_log, ignored);

        CompactIntervalCutoffConfig cutoff;
        cutoff.enabled = true;
        cutoff.gamma_L = options.interval_exact_cutoff_gamma_L;
        cutoff.gamma_U = options.interval_exact_cutoff_gamma_U;
        cutoff.incumbent_ub = options.interval_exact_cutoff_UB;
        cutoff.epsilon = options.interval_exact_cutoff_epsilon;
        if (!options.interval_oracle_objective_cutoff_row) {
            result.notes.push_back(
                "interval_oracle_objective_cutoff_row=false requested; exact cutoff oracle keeps the original cutoff row because it is required for a valid interval certificate");
        }
        writeCompactLp(instance, options, lp_path, true, &cutoff);
        if (options.interval_oracle_penalty_domain_tightening ||
            options.interval_oracle_low_gini_tightening) {
            result.notes.push_back(
                "interval oracle added safe penalty-budget e_i upper bounds derived from G>=gamma_L and G+lambda*P<=UB-epsilon");
        }

        const double time_limit = options.interval_exact_cutoff_time_limit > 0.0
            ? options.interval_exact_cutoff_time_limit
            : std::max(1.0, options.solve_time_limit);
        std::ofstream cmd(cmd_path);
        cmd << "set threads " << std::max(1, options.threads) << "\n";
        cmd << "set timelimit " << time_limit << "\n";
        cmd << "set mip tolerances mipgap 0\n";
        cmd << "read " << lp_path.string() << "\n";
        cmd << "optimize\n";
        cmd << "write " << sol_path.string() << "\n";
        cmd << "quit\n";
        cmd.close();

        const std::string cplex = defaultCplexPath();
        const std::string command = "cmd /C \"" + quote(cplex) + " -f "
            + quote(cmd_path) + " > " + quote(cplex_log) + " 2>&1\"";
        const int rc = std::system(command.c_str());
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.interval_exact_cutoff_runtime_seconds = result.runtime_seconds;

        std::string cplex_status = "unknown";
        double cplex_obj = std::numeric_limits<double>::quiet_NaN();
        double best_bound = std::numeric_limits<double>::quiet_NaN();
        std::unordered_map<std::string, double> values;
        if (std::filesystem::exists(sol_path)) {
            values = parseSolValues(sol_path, cplex_status, cplex_obj, best_bound);
        } else {
            cplex_status = parseCplexTerminalStatus(cplex_log);
            if (cplex_status == "unknown") {
                cplex_status = (rc == 0) ? "no solution file" : "cplex process failed";
            }
        }
        result.interval_exact_cutoff_solver_status = cplex_status;
        result.nodes = parseCplexNodes(cplex_log);
        result.interval_exact_cutoff_nodes = result.nodes;
        const double log_best_bound = parseCplexBestBound(cplex_log);
        if (!std::isfinite(best_bound) && std::isfinite(log_best_bound)) best_bound = log_best_bound;
        result.interval_exact_cutoff_best_bound = std::isfinite(best_bound) ? best_bound : 0.0;
        result.interval_exact_cutoff_objective = std::isfinite(cplex_obj) ? cplex_obj : 0.0;

        const double cutoff_value = options.interval_exact_cutoff_UB - options.interval_exact_cutoff_epsilon;
        if (statusIsInfeasible(cplex_status)) {
            result.status = "interval_closed";
            result.lower_bound = options.interval_exact_cutoff_UB;
            result.upper_bound = options.interval_exact_cutoff_UB;
            result.gap = 0.0;
            result.interval_exact_cutoff_proven_infeasible = true;
            result.interval_exact_cutoff_certificate_basis = "interval_exact_cutoff_mip_infeasible";
            result.certificate = "CPLEX proved the original compact fixed-interval cutoff MIP infeasible; no incumbent-improving original solution exists in this interval.";
        } else if (statusIsOptimal(cplex_status) && std::isfinite(cplex_obj) &&
                   cplex_obj > cutoff_value + 1e-7) {
            result.status = "interval_closed";
            result.lower_bound = cplex_obj;
            result.upper_bound = options.interval_exact_cutoff_UB;
            result.gap = 0.0;
            result.interval_exact_cutoff_proven_infeasible = true;
            result.interval_exact_cutoff_certificate_basis = "interval_exact_cutoff_mip_optimal_no_improver";
            result.certificate = "CPLEX optimized the fixed-interval cutoff MIP and its objective excludes all incumbent-improving solutions in this interval.";
        } else if (statusIsOptimal(cplex_status) && !values.empty()) {
            result.routes = reconstructRoutes(instance, values);
            result.verification = verifySolution(instance, result.routes, options.lambda);
            result.final_inventory = result.verification.final_inventory;
            result.G = result.verification.G;
            result.P = result.verification.P;
            result.objective = result.verification.objective;
            result.upper_bound = result.objective;
            result.lower_bound = std::isfinite(best_bound) ? best_bound : 0.0;
            result.gap = (std::fabs(result.upper_bound) > 1e-12)
                ? std::max(0.0, (result.upper_bound - result.lower_bound) / std::fabs(result.upper_bound))
                : 0.0;
            const bool in_interval =
                result.G >= options.interval_exact_cutoff_gamma_L - 1e-7 &&
                result.G <= options.interval_exact_cutoff_gamma_U + 1e-7;
            const bool improving = result.verification.feasible &&
                in_interval &&
                result.objective <= cutoff_value + 1e-7;
            result.interval_exact_cutoff_feasible_improving = improving;
            result.status = improving ? "interval_feasible_improving_ub" : "interval_unresolved_feasible_relaxation_solution";
            result.interval_exact_cutoff_certificate_basis = improving
                ? "interval_exact_cutoff_mip_feasible_improving"
                : "interval_exact_cutoff_mip_feasible_not_verified_original_interval_improver";
            result.certificate = improving
                ? "CPLEX found an original feasible incumbent-improving route plan in this interval; it is UB-only and requires frontier restart."
                : "CPLEX found a cutoff-MIP solution, but the independently reconstructed original route plan did not verify as an improving solution in the requested interval; interval remains unresolved.";
        } else {
            result.status = statusIsTimeLimited(cplex_status) ? "interval_unresolved_timeout" : "interval_unresolved";
            result.interval_exact_cutoff_timeout = statusIsTimeLimited(cplex_status);
            result.lower_bound = std::isfinite(best_bound) ? best_bound : 0.0;
            result.upper_bound = options.interval_exact_cutoff_UB;
            result.gap = (std::fabs(result.upper_bound) > 1e-12)
                ? std::max(0.0, (result.upper_bound - result.lower_bound) / std::fabs(result.upper_bound))
                : 0.0;
            result.interval_exact_cutoff_gap = result.gap;
            result.interval_exact_cutoff_certificate_basis = result.interval_exact_cutoff_timeout
                ? "interval_exact_cutoff_mip_timeout"
                : "interval_exact_cutoff_mip_unresolved";
            result.certificate = "CPLEX did not prove fixed-interval cutoff infeasibility or produce a verified improving original solution; interval remains unresolved. CPLEX status: " + cplex_status;
        }
        result.notes.push_back("CPLEX solution status: " + cplex_status);
        result.notes.push_back("CPLEX process return code: " + std::to_string(rc));
        result.notes.push_back("LP file: " + lp_path.string());
        result.notes.push_back("CPLEX log: " + cplex_log.string());
    } catch (const std::exception& e) {
        result.status = "error";
        result.interval_exact_cutoff_certificate_basis = "interval_exact_cutoff_mip_error";
        result.certificate = std::string("Interval exact cutoff oracle failed: ") + e.what();
        result.runtime_seconds = std::chrono::duration<double>(Clock::now() - start).count();
        result.interval_exact_cutoff_runtime_seconds = result.runtime_seconds;
    }
    return result;
}

} // namespace ebrp
