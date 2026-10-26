#include "NativeOtB1.hpp"
#include "FileSha256.hpp"
#include "FixedIntervalMipBackend.hpp"

#include <gurobi_c.h>

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#if defined(__SSE__) || defined(_M_X64)
#include <xmmintrin.h>
#endif

namespace {

void require(bool condition, const std::string& why) {
    if (!condition) throw std::runtime_error(why);
}

void row(ebrp::NativeOtB1LinearModel& m, char sense, double rhs,
         const std::map<int, double>& terms) {
    for (const auto& [column, value] : terms) {
        m.column_indices.push_back(column);
        m.coefficients.push_back(value);
    }
    m.row_starts.push_back(static_cast<int>(m.coefficients.size()));
    m.senses.push_back(sense);
    m.rhs.push_back(rhs);
}

ebrp::NativeOtB1LinearModel fixture(double alpha1, double alpha2) {
    ebrp::NativeOtB1LinearModel m;
    m.names = {"G", "Y_1", "Y_2", "r_1", "r_2", "h_1_2",
        "state_1_0", "state_1_1", "state_1_2",
        "state_2_0", "state_2_1", "state_2_2",
        "state_g_1_0", "state_g_1_1", "state_g_1_2",
        "state_g_2_0", "state_g_2_1", "state_g_2_2"};
    m.types = {'C','I','I','C','C','C',
        'B','B','B','B','B','B','C','C','C','C','C','C'};
    m.lower_bounds.assign(m.names.size(), 0.0);
    m.upper_bounds.assign(m.names.size(), 2.0);
    m.upper_bounds[0] = 0.0;
    for (int col = 6; col <= 11; ++col) m.upper_bounds[col] = 1.0;
    for (int col = 12; col <= 17; ++col) m.upper_bounds[col] = 0.0;
    m.upper_bounds[7] = 0.0;     // first station only endpoints
    m.upper_bounds[9] = 0.0;
    m.lower_bounds[10] = 1.0;    // second station fixed at middle
    m.upper_bounds[11] = 0.0;
    m.row_starts = {0};
    row(m, '=', 1.0, {{6,1.0},{7,1.0},{8,1.0}});
    row(m, '=', 0.0, {{1,1.0},{7,-1.0},{8,-2.0}});
    row(m, '=', 0.0, {{0,-1.0},{12,1.0},{13,1.0},{14,1.0}});
    row(m, '=', 0.0, {{1,-alpha1},{3,1.0}});
    row(m, '=', 1.0, {{9,1.0},{10,1.0},{11,1.0}});
    row(m, '=', 0.0, {{2,1.0},{10,-1.0},{11,-2.0}});
    row(m, '=', 0.0, {{0,-1.0},{15,1.0},{16,1.0},{17,1.0}});
    row(m, '=', 0.0, {{2,-alpha2},{4,1.0}});
    row(m, '>', 0.0, {{3,-1.0},{4,1.0},{5,1.0}});
    row(m, '>', 0.0, {{3,1.0},{4,-1.0},{5,1.0}});
    return m;
}

ebrp::NativeOtB1LinearModel wideFixture(double alpha1, double alpha2) {
    ebrp::NativeOtB1LinearModel m;
    m.names = {"G", "Y_1", "Y_2", "r_1", "r_2", "h_1_2"};
    m.types = {'C','I','I','C','C','C'};
    for (int station=1; station<=2; ++station)
        for (int y=0; y<=5; ++y) {
            m.names.push_back("state_"+std::to_string(station)+"_"+std::to_string(y));
            m.types.push_back('B');
        }
    for (int station=1; station<=2; ++station)
        for (int y=0; y<=5; ++y) {
            m.names.push_back("state_g_"+std::to_string(station)+"_"+std::to_string(y));
            m.types.push_back('C');
        }
    m.lower_bounds.assign(m.names.size(), 0.0);
    m.upper_bounds.assign(m.names.size(), 10.0);
    m.upper_bounds[0] = 0.0;
    m.upper_bounds[1] = 5.0;
    m.upper_bounds[2] = 5.0;
    for (int col=6; col<18; ++col) m.upper_bounds[col]=1.0;
    for (int col=18; col<30; ++col) m.upper_bounds[col]=0.0;
    m.row_starts = {0};
    for (int station=1; station<=2; ++station) {
        const int y_col=station, r_col=station+2;
        const int s_base=6+(station-1)*6, q_base=18+(station-1)*6;
        std::map<int,double> onehot, inventory={{y_col,1.0}},
                             g={{0,-1.0}};
        for (int y=0; y<=5; ++y) {
            onehot.emplace(s_base+y,1.0);
            if (y) inventory.emplace(s_base+y,-static_cast<double>(y));
            g.emplace(q_base+y,1.0);
        }
        row(m,'=',1.0,onehot);
        row(m,'=',0.0,inventory);
        row(m,'=',0.0,g);
        row(m,'=',0.0,{{y_col,station==1 ? -alpha1 : -alpha2},
                       {r_col,1.0}});
    }
    row(m,'>',0.0,{{3,-1.0},{4,1.0},{5,1.0}});
    row(m,'>',0.0,{{3,1.0},{4,-1.0},{5,1.0}});
    return m;
}

ebrp::NativeOtB1LinearModel parityExposureFixture() {
    auto model = wideFixture(1.0, 1.0);
    // This is one replacement exposure toy. Retain every state and every
    // original row; disable only parity-incompatible selectors by bound.
    for (int y=0; y<=5; ++y) {
        if (y%2) model.upper_bounds[static_cast<std::size_t>(6+y)] = 0.0;
        else model.upper_bounds[static_cast<std::size_t>(12+y)] = 0.0;
    }
    return model;
}

std::vector<double> parityFractionalPoint() {
    std::vector<double> point(30, 0.0);
    point[1]=point[2]=point[3]=point[4]=1.0;
    point[6]=point[8]=0.5;
    point[13]=1.0;
    return point;
}

std::vector<double> fractionalPoint() {
    std::vector<double> point(18, 0.0);
    point[1] = point[2] = point[3] = point[4] = 1.0;
    point[6] = point[8] = 0.5;
    point[10] = 1.0;
    return point;
}

void pure() {
    ebrp::FixedIntervalMipOutcome failure_gate;
    failure_gate.failure_reason =
        "gurobi_external_gate:native_log_parameter_rc=10001";
    failure_gate.solver_finalization_reached = true;
    failure_gate.optimal = true;
    failure_gate.native_exact_optimal = true;
    failure_gate.native_tolerance_optimal = true;
    failure_gate.infeasible = true;
    failure_gate.lp_terminal_valid = true;
    failure_gate.native_bound_available = true;
    failure_gate.incumbent_available = true;
    failure_gate.native_bound_events.emplace_back();
    failure_gate.native_bound_target_reached = true;
    failure_gate.native_bound_target_termination_requested = true;
    ebrp::invalidateRound89NativeOtB1FailedOutcome(failure_gate);
    require(!failure_gate.solver_finalization_reached && !failure_gate.optimal &&
            !failure_gate.native_exact_optimal &&
            !failure_gate.native_tolerance_optimal && !failure_gate.infeasible &&
            !failure_gate.lp_terminal_valid &&
            !failure_gate.native_bound_available &&
            !failure_gate.incumbent_available &&
            failure_gate.native_bound_events.empty() &&
            !failure_gate.native_bound_target_reached &&
            !failure_gate.native_bound_target_termination_requested,
            "Round89 log-parameter failure retained proof eligibility");
    ebrp::FixedIntervalMipOutcome status_gate;
    status_gate.failure_reason =
        "gurobi_external_gate:round89_native_status_read_ok=0";
    status_gate.solver_finalization_reached = true;
    status_gate.native_bound_available = true;
    status_gate.native_bound_events.emplace_back();
    ebrp::invalidateRound89NativeOtB1FailedOutcome(status_gate);
    require(!status_gate.solver_finalization_reached &&
            !status_gate.native_bound_available &&
            status_gate.native_bound_events.empty(),
            "Round89 Status API failure retained proof eligibility");
    ebrp::FixedIntervalMipOutcome clean_gate;
    clean_gate.failure_reason = "none";
    clean_gate.native_bound_available = true;
    ebrp::invalidateRound89NativeOtB1FailedOutcome(clean_gate);
    require(clean_gate.native_bound_available,
            "Round89 valid outcome was incorrectly invalidated");
    const auto model = fixture(1.0, 1.0);
    const auto prepared = ebrp::prepareNativeOtB1(model, 2);
    require(prepared.valid && prepared.audited_rows == 10 &&
            prepared.pairs.size() == 1, "two-link toy audit failed:"+prepared.reason);
#if defined(__SSE__) || defined(_M_X64)
    const unsigned int original_mxcsr = _mm_getcsr();
    _mm_setcsr(original_mxcsr | 0x8040u);
    const auto flushed = ebrp::prepareNativeOtB1(model, 2);
    _mm_setcsr(original_mxcsr);
    require(!flushed.valid &&
            flushed.reason == "binary64_arithmetic_environment_invalid",
            "runtime FTZ/DAZ guard accepted unsafe arithmetic");
#endif
    auto point = fractionalPoint();
    point[5] = 0.0;
    const auto cut = ebrp::separateNativeOtB1(prepared.pairs.front(), point, 1e-6);
    auto reverse_point = point;
    reverse_point[6]=0.0;reverse_point[8]=0.0;reverse_point[7]=1.0;
    reverse_point[9]=0.5;reverse_point[10]=0.0;reverse_point[11]=0.5;
    const auto reverse_cut = ebrp::separateNativeOtB1(
        prepared.pairs.front(), reverse_point, 1e-6);
    require(cut.status == ebrp::NativeOtB1Cut::Status::Reliable &&
            cut.reliable_violation_lower > 0.9,
            "fractional toy not reliably separated:"+cut.reason);
    auto broken = model;
    broken.coefficients[0] = 2.0;
    require(!ebrp::prepareNativeOtB1(broken, 2).valid,
            "malformed one-hot row accepted");
    auto invalid = point;
    invalid[5] = std::numeric_limits<double>::infinity();
    require(ebrp::separateNativeOtB1(prepared.pairs.front(), invalid, 1e-6).status !=
            ebrp::NativeOtB1Cut::Status::Reliable,
            "nonfinite callback point accepted");
    auto third = fixture(1.0/3.0, 1.0/7.0);
    const auto nonbinary = ebrp::prepareNativeOtB1(third, 2);
    require(nonbinary.valid && nonbinary.pairs.size() == 1 &&
            nonbinary.pairs.front().support_error_upper > 0.0,
            "nonbinary actual-chain product envelope absent");
    const auto wide = ebrp::prepareNativeOtB1(
        wideFixture(1.0/3.0,1.0/7.0),2);
    require(wide.valid && wide.stations[0].states.size()==6 &&
            wide.stations[1].states.size()==6,
            "wide actual-chain support audit failed:"+wide.reason);
    require(wide.stations[0].states[3].nominal_support == 1.0 &&
            wide.stations[0].states[3].support_error_upper > 0.0,
            "gamma-three rounded-product boundary absent");
    const auto parity = ebrp::prepareNativeOtB1(parityExposureFixture(),2);
    require(parity.valid && parity.stations[0].states.size()==6 &&
            parity.stations[1].states.size()==6,
            "parity exposure model rejected:"+parity.reason);
    const auto parity_cut = ebrp::separateNativeOtB1(
        parity.pairs.front(),parityFractionalPoint(),1e-6);
    require(parity_cut.status==ebrp::NativeOtB1Cut::Status::Reliable &&
            parity_cut.reliable_violation_lower > 0.9,
            "parity fractional witness not separated:"+parity_cut.reason);
    auto invalid_r_bound = wideFixture(1.0/3.0,1.0/7.0);
    invalid_r_bound.upper_bounds[3] = std::numeric_limits<double>::infinity();
    require(!ebrp::prepareNativeOtB1(invalid_r_bound,2).valid,
            "nonfinite r bound accepted");
    require(!ebrp::prepareNativeOtB1(wideFixture(1e308,1.0),2).valid,
            "overflowed support accepted");
    const auto collided = ebrp::prepareNativeOtB1(wideFixture(1.0,1.0),2);
    require(collided.valid && collided.pairs[0].knots.size()==6,
            "coincident cross-station knots not merged");
    const auto adjacent = ebrp::prepareNativeOtB1(
        wideFixture(std::nextafter(1.0,2.0),1.0),2);
    require(adjacent.valid &&
            adjacent.pairs[0].knots[1]==1.0 &&
            adjacent.pairs[0].knots[2]==std::nextafter(1.0,2.0),
            "adjacent binary64 knots not retained");
    auto reversed = fractionalPoint();
    reversed[6]=0.0;reversed[8]=0.0;reversed[7]=1.0;
    reversed[9]=0.5;reversed[10]=0.0;reversed[11]=0.5;
    const auto negative_sign = ebrp::separateNativeOtB1(
        prepared.pairs.front(),reversed,1e-6);
    const auto middle = std::find(negative_sign.indices.begin(),
                                  negative_sign.indices.end(),7);
    require(negative_sign.status==ebrp::NativeOtB1Cut::Status::Reliable &&
            middle != negative_sign.indices.end() &&
            negative_sign.coefficients[static_cast<std::size_t>(
                middle-negative_sign.indices.begin())] < 0.0,
            "negative CDF sign row absent");
}

void pureJson(const std::filesystem::path& path) {
    const double alpha1 = 1.0/3.0, alpha2 = 1.0/7.0;
    const auto prepared = ebrp::prepareNativeOtB1(fixture(alpha1, alpha2), 2);
    require(prepared.valid, "nonbinary fixture audit failed:"+prepared.reason);
    auto point = fractionalPoint();
    point[3] = alpha1; point[4] = alpha2;
    const auto cut = ebrp::separateNativeOtB1(prepared.pairs.front(), point, 1e-6);
    auto reverse_point = point;
    reverse_point[6]=0.0; reverse_point[8]=0.0; reverse_point[7]=1.0;
    reverse_point[9]=0.5; reverse_point[10]=0.0; reverse_point[11]=0.5;
    const auto reverse_cut = ebrp::separateNativeOtB1(
        prepared.pairs.front(), reverse_point, 1e-6);
    require(cut.status == ebrp::NativeOtB1Cut::Status::Reliable &&
            reverse_cut.status == ebrp::NativeOtB1Cut::Status::Reliable,
            "oracle CDF orientations not reliably separated");
    const auto wide = ebrp::prepareNativeOtB1(
        wideFixture(alpha1,alpha2),2);
    require(wide.valid, "wide oracle fixture audit failed:"+wide.reason);
    std::vector<double> wide_point(30,0.0);
    wide_point[1]=wide_point[2]=1.0;
    wide_point[3]=alpha1; wide_point[4]=alpha2;
    wide_point[6]=wide_point[8]=0.5;
    wide_point[13]=1.0;
    const auto wide_cut = ebrp::separateNativeOtB1(
        wide.pairs.front(),wide_point,1e-6);
    require(wide_cut.status == ebrp::NativeOtB1Cut::Status::Reliable,
            "wide rounded-product cut not reliably separated:"+wide_cut.reason);
    std::ofstream out(path);
    require(static_cast<bool>(out), "oracle output open failed");
    out << std::setprecision(17) << "{\"alpha\":[" << alpha1 << ',' << alpha2
        << "],\"gamma\":[[0,1,2],[0,1,2]],\"beta\":[[";
    for (int station = 0; station < 2; ++station) {
        if (station) out << "],[";
        const auto& states = prepared.stations[static_cast<std::size_t>(station)].states;
        for (std::size_t k = 0; k < states.size(); ++k) {
            if (k) out << ',';
            out << states[k].nominal_support;
        }
    }
    out << "]],\"state_support_errors\":[[";
    for (int station = 0; station < 2; ++station) {
        if (station) out << "],[";
        const auto& states = prepared.stations[static_cast<std::size_t>(station)].states;
        for (std::size_t k = 0; k < states.size(); ++k) {
            if (k) out << ',';
            out << states[k].support_error_upper;
        }
    }
    out << "]],\"wide_nonexact_products\":[[";
    for (int station=0; station<2; ++station) {
        if (station) out << "],[";
        for (int y : {3,5}) {
            if (y==5) out << ',';
            const auto& state = wide.stations[static_cast<std::size_t>(station)]
                                .states[static_cast<std::size_t>(y)];
            out << "{\"gamma\":" << y
                << ",\"beta\":" << state.nominal_support
                << ",\"error\":" << state.support_error_upper << '}';
        }
    }
    out << "]],\"support_error\":"
        << prepared.pairs.front().support_error_upper
        << ",\"cut\":{\"indices\":[";
    for (std::size_t k = 0; k < cut.indices.size(); ++k) {
        if (k) out << ',';
        out << cut.indices[k];
    }
    out << "],\"coefficients\":[";
    for (std::size_t k = 0; k < cut.coefficients.size(); ++k) {
        if (k) out << ',';
        out << cut.coefficients[k];
    }
    out << "],\"rhs\":" << cut.rhs
        << ",\"coefficient_error\":" << cut.coefficient_error_upper
        << ",\"status\":"
        << std::quoted(cut.reason) << "},\"reverse_cut\":{\"indices\":[";
    for (std::size_t k=0; k<reverse_cut.indices.size(); ++k) {
        if (k) out << ',';
        out << reverse_cut.indices[k];
    }
    out << "],\"coefficients\":[";
    for (std::size_t k=0; k<reverse_cut.coefficients.size(); ++k) {
        if (k) out << ',';
        out << reverse_cut.coefficients[k];
    }
    out << "],\"rhs\":" << reverse_cut.rhs
        << ",\"coefficient_error\":"
        << reverse_cut.coefficient_error_upper
        << ",\"status\":" << std::quoted(reverse_cut.reason)
        << "},\"wide_beta\":[[";
    for (int station=0; station<2; ++station) {
        if (station) out << "],[";
        for (std::size_t y=0; y<6; ++y) {
            if (y) out << ',';
            out << wide.stations[static_cast<std::size_t>(station)]
                         .states[y].nominal_support;
        }
    }
    out << "]],\"wide_support_error\":"
        << wide.pairs.front().support_error_upper
        << ",\"wide_cut\":{\"indices\":[";
    for (std::size_t k=0; k<wide_cut.indices.size(); ++k) {
        if (k) out << ',';
        out << wide_cut.indices[k];
    }
    out << "],\"coefficients\":[";
    for (std::size_t k=0; k<wide_cut.coefficients.size(); ++k) {
        if (k) out << ',';
        out << wide_cut.coefficients[k];
    }
    out << "],\"rhs\":" << wide_cut.rhs
        << ",\"coefficient_error\":"
        << wide_cut.coefficient_error_upper
        << ",\"status\":" << std::quoted(wide_cut.reason)
        << "}}\n";
    require(static_cast<bool>(out), "oracle output write failed");
}

struct Api {
    HMODULE dll = nullptr;
    decltype(&GRBemptyenvinternal) emptyenvinternal = nullptr;
    decltype(&GRBstartenv) startenv = nullptr;
    decltype(&GRBnewmodel) newmodel = nullptr;
    decltype(&GRBaddconstr) addconstr = nullptr;
    decltype(&GRBupdatemodel) update = nullptr;
    decltype(&GRBgetenv) getenv = nullptr;
    decltype(&GRBsetintparam) setintparam = nullptr;
    decltype(&GRBsetdblparam) setdblparam = nullptr;
    decltype(&GRBgetintparam) getintparam = nullptr;
    decltype(&GRBgetdblparam) getdblparam = nullptr;
    decltype(&GRBsetcallbackfunc) setcallback = nullptr;
    decltype(&GRBcbget) cbget = nullptr;
    decltype(&GRBcbcut) cbcut = nullptr;
    decltype(&GRBoptimize) optimize = nullptr;
    decltype(&GRBgetintattr) getintattr = nullptr;
    decltype(&GRBgetdblattr) getdblattr = nullptr;
    decltype(&GRBgetdblattrarray) getdblattrarray = nullptr;
    decltype(&GRBfreemodel) freemodel = nullptr;
    decltype(&GRBfreeenv) freeenv = nullptr;
    decltype(&GRBwrite) write = nullptr;

    explicit Api(const std::filesystem::path& path) {
        dll = LoadLibraryW(path.wstring().c_str());
        require(dll != nullptr, "toy LoadLibrary failed");
#define LOAD(member, name) \
        member = reinterpret_cast<decltype(member)>(GetProcAddress(dll, name)); \
        require(member != nullptr, std::string("toy missing symbol:")+name)
        LOAD(emptyenvinternal,"GRBemptyenvinternal"); LOAD(startenv,"GRBstartenv");
        LOAD(newmodel,"GRBnewmodel"); LOAD(addconstr,"GRBaddconstr");
        LOAD(update,"GRBupdatemodel"); LOAD(getenv,"GRBgetenv");
        LOAD(setintparam,"GRBsetintparam"); LOAD(setdblparam,"GRBsetdblparam");
        LOAD(getintparam,"GRBgetintparam"); LOAD(getdblparam,"GRBgetdblparam");
        LOAD(setcallback,"GRBsetcallbackfunc");
        LOAD(cbget,"GRBcbget"); LOAD(cbcut,"GRBcbcut");
        LOAD(optimize,"GRBoptimize"); LOAD(getintattr,"GRBgetintattr");
        LOAD(getdblattr,"GRBgetdblattr");
        LOAD(getdblattrarray,"GRBgetdblattrarray");
        LOAD(freemodel,"GRBfreemodel"); LOAD(freeenv,"GRBfreeenv");
        LOAD(write,"GRBwrite");
#undef LOAD
    }
    ~Api() { if (dll) FreeLibrary(dll); }
};

struct ToyCallback {
    Api* api = nullptr;
    const ebrp::NativeOtB1Pair* pair = nullptr;
    int original_columns = 0;
    long long optimal_nodes = 0;
    long long fractional_nodes = 0;
    long long fractional_reliable_rows = 0;
    long long reliable_rows = 0;
    long long submitted_api_ok = 0;
    long long fractional_submitted_api_ok = 0;
    int failure_code = 0;
    double integrality_tolerance = 0.0;
    double feasibility_tolerance = 0.0;
    std::vector<int> enabled_selector_columns;
    std::vector<double> first_fractional_point;
    std::vector<double> first_reliable_point;
    ebrp::NativeOtB1Cut first_reliable_cut;
};

int __stdcall callback(GRBmodel*, void* cbdata, int where, void* userdata) {
    if (where != GRB_CB_MIPNODE) return 0;
    auto& state = *static_cast<ToyCallback*>(userdata);
    if (state.failure_code != 0) return 0;
    try {
    int status = 0;
    if (state.api->cbget(cbdata, where, GRB_CB_MIPNODE_STATUS, &status)) {
        state.failure_code = -1;
        return 0;
    }
    if (status != GRB_OPTIMAL) return 0;
    ++state.optimal_nodes;
    std::vector<double> x(static_cast<std::size_t>(state.original_columns));
    if (state.api->cbget(cbdata, where, GRB_CB_MIPNODE_REL, x.data())) {
        state.failure_code = -2;
        return 0;
    }
    const bool fractional_selector = std::any_of(
        state.enabled_selector_columns.begin(),
        state.enabled_selector_columns.end(), [&](int column) {
            const double value = x[static_cast<std::size_t>(column)];
            return std::isfinite(value) &&
                value > state.integrality_tolerance &&
                value < 1.0-state.integrality_tolerance;
        });
    if (fractional_selector) {
        ++state.fractional_nodes;
        if (state.first_fractional_point.empty())
            state.first_fractional_point = x;
    }
    const auto cut = ebrp::separateNativeOtB1(
        *state.pair, x, state.feasibility_tolerance);
    if (cut.status != ebrp::NativeOtB1Cut::Status::Reliable) return 0;
    ++state.reliable_rows;
    if (fractional_selector) ++state.fractional_reliable_rows;
    if (state.first_reliable_point.empty()) {
        state.first_reliable_point = x;
        state.first_reliable_cut = cut;
    }
    const int rc = state.api->cbcut(cbdata,
        static_cast<int>(cut.indices.size()),
        const_cast<int*>(cut.indices.data()),
        const_cast<double*>(cut.coefficients.data()), cut.sense, cut.rhs);
    if (rc) state.failure_code = rc;
    else {
        ++state.submitted_api_ok;
        if (fractional_selector) ++state.fractional_submitted_api_ok;
    }
    } catch (...) {
        state.failure_code = -99;
    }
    return 0;
}

struct ToyResult {
    std::string arm;
    int optimize_rc = -1;
    int status = -1;
    int precrush = -1;
    double objective = 0.0;
    double work = 0.0;
    double runtime = 0.0;
    std::vector<double> primal;
    ToyCallback observer;
    std::filesystem::path model_export;
    std::string model_sha256;
    std::map<std::string,int> integer_parameter_readback;
    std::map<std::string,double> double_parameter_readback;
    bool static_cut_added = false;
    ebrp::NativeOtB1Cut static_cut;
};

void writeValues(std::ostream& out, const std::vector<double>& values) {
    out << '[';
    for (std::size_t k=0; k<values.size(); ++k) {
        if (k) out << ',';
        out << values[k];
    }
    out << ']';
}

struct PrimalDomainResiduals {
    double bounds = 0.0;
    double integrality = 0.0;
};

PrimalDomainResiduals domainResiduals(
    const ebrp::NativeOtB1LinearModel& model,
    const std::vector<double>& values) {
    require(values.size()==model.names.size(),"toy primal domain length mismatch");
    PrimalDomainResiduals result;
    for (std::size_t col=0; col<values.size(); ++col) {
        const double value=values[col];
        require(std::isfinite(value),"toy primal is nonfinite");
        result.bounds=std::max(result.bounds,
            std::max(model.lower_bounds[col]-value,
                     value-model.upper_bounds[col]));
        if (model.types[col]=='B' || model.types[col]=='I')
            result.integrality=std::max(result.integrality,
                std::fabs(value-std::round(value)));
    }
    return result;
}

double writeOriginalRowResiduals(
    std::ostream& out, const ebrp::NativeOtB1LinearModel& model,
    const std::vector<double>& values) {
    require(values.size()==model.names.size(),
            "toy primal length does not match original model");
    double maximum = 0.0;
    out << '[';
    for (std::size_t row_number=0; row_number<model.senses.size();
         ++row_number) {
        if (row_number) out << ',';
        double activity = 0.0;
        for (int k=model.row_starts[row_number];
             k<model.row_starts[row_number+1]; ++k)
            activity += model.coefficients[static_cast<std::size_t>(k)] *
                values[static_cast<std::size_t>(model.column_indices[k])];
        const double rhs = model.rhs[row_number];
        const char sense = model.senses[row_number];
        const double violation = sense=='='
            ? std::fabs(activity-rhs)
            : sense=='>' ? std::max(0.0,rhs-activity)
                         : std::max(0.0,activity-rhs);
        maximum = std::max(maximum,violation);
        out << "{\"row\":" << row_number << ",\"sense\":"
            << std::quoted(std::string(1,sense))
            << ",\"rhs\":" << rhs << ",\"activity\":"
            << activity << ",\"violation\":" << violation << '}';
    }
    out << ']';
    return maximum;
}

void writeCut(std::ostream& out, const ebrp::NativeOtB1Cut& cut,
              const std::vector<double>& values) {
    out << "{\"status\":" << std::quoted(cut.reason)
        << ",\"sense\":" << std::quoted(std::string(1,cut.sense))
        << ",\"rhs\":" << cut.rhs << ",\"indices\":[";
    double activity = 0.0;
    for (std::size_t k=0; k<cut.indices.size(); ++k) {
        if (k) out << ',';
        out << cut.indices[k];
        if (values.size()>static_cast<std::size_t>(cut.indices[k]))
            activity += cut.coefficients[k] *
                values[static_cast<std::size_t>(cut.indices[k])];
    }
    out << "],\"coefficients\":";
    writeValues(out,cut.coefficients);
    out << ",\"activity\":" << activity
        << ",\"violation\":" << std::max(0.0,cut.rhs-activity)
        << ",\"reliable_violation_lower\":"
        << cut.reliable_violation_lower << '}';
}

void writeDirectArmRecord(const std::filesystem::path& path,
    const ToyResult& result, const ebrp::NativeOtB1LinearModel& model) {
    require(!std::filesystem::exists(path),"direct arm raw receipt already exists");
    std::ofstream out(path);
    require(static_cast<bool>(out),"direct arm raw receipt open failed");
    out << std::setprecision(17) << "{\"arm\":" << std::quoted(result.arm)
        << ",\"model_path\":" << std::quoted(result.model_export.string())
        << ",\"model_sha256\":" << std::quoted(result.model_sha256)
        << ",\"optimize_rc\":" << result.optimize_rc
        << ",\"status\":" << result.status
        << ",\"objective\":" << result.objective
        << ",\"work\":" << result.work
        << ",\"runtime\":" << result.runtime
        << ",\"parameter_readback_int\":{";
    bool first = true;
    for (const auto& [name,value] : result.integer_parameter_readback) {
        if (!first) out << ',';
        first = false;
        out << std::quoted(name) << ':' << value;
    }
    out << "},\"parameter_readback_double\":{";
    first = true;
    for (const auto& [name,value] : result.double_parameter_readback) {
        if (!first) out << ',';
        first = false;
        out << std::quoted(name) << ':' << value;
    }
    out << "},\"raw_primal\":";
    writeValues(out,result.primal);
    out << ",\"original_rows\":";
    if (result.primal.size()==model.names.size()) {
        const double maximum = writeOriginalRowResiduals(
            out,model,result.primal);
        const auto domain=domainResiduals(model,result.primal);
        out << ",\"maximum_original_row_violation\":" << maximum
            << ",\"maximum_bound_violation\":" << domain.bounds
            << ",\"maximum_integrality_violation\":"
            << domain.integrality;
    } else out << "null,\"maximum_original_row_violation\":null";
    out << ",\"static_row\":";
    if (result.static_cut_added) writeCut(out,result.static_cut,result.primal);
    else out << "null";
    out << ",\"callback\":{\"optimal_nodes\":"
        << result.observer.optimal_nodes
        << ",\"fractional_selector_nodes\":"
        << result.observer.fractional_nodes
        << ",\"fractional_reliable_rows\":"
        << result.observer.fractional_reliable_rows
        << ",\"reliable_rows\":" << result.observer.reliable_rows
        << ",\"submitted_api_ok\":"
        << result.observer.submitted_api_ok
        << ",\"fractional_submitted_api_ok\":"
        << result.observer.fractional_submitted_api_ok
        << ",\"failure_code\":" << result.observer.failure_code
        << ",\"integrality_tolerance_readback\":"
        << result.observer.integrality_tolerance
        << ",\"feasibility_tolerance_readback\":"
        << result.observer.feasibility_tolerance
        << ",\"enabled_selector_columns\":[";
    for (std::size_t k=0; k<result.observer.enabled_selector_columns.size();
         ++k) {
        if (k) out << ',';
        out << result.observer.enabled_selector_columns[k];
    }
    out << "],\"first_fractional_primal\":";
    writeValues(out,result.observer.first_fractional_point);
    out << ",\"first_reliable_primal\":";
    writeValues(out,result.observer.first_reliable_point);
    out << ",\"first_reliable_cut\":";
    if (!result.observer.first_reliable_point.empty())
        writeCut(out,result.observer.first_reliable_cut,
                 result.observer.first_reliable_point);
    else out << "null";
    out << "}}\n";
    out.flush();
    require(static_cast<bool>(out),"direct arm raw receipt write failed");
}

ToyResult runToy(Api& api, const std::string& arm,
                 const ebrp::NativeOtB1LinearModel& fixture_model,
                 const ebrp::NativeOtB1Pair& pair,
                 const std::filesystem::path& model_export) {
    ToyResult result;
    result.arm = arm;
    result.model_export = model_export;
    GRBenv* env = nullptr;
    GRBmodel* model = nullptr;
    try {
        require(api.emptyenvinternal(&env, GRB_VERSION_MAJOR,
                GRB_VERSION_MINOR, GRB_VERSION_TECHNICAL) == 0,
                "toy emptyenv failed");
        require(api.startenv(env) == 0, "toy startenv failed");
        const int count = static_cast<int>(fixture_model.names.size());
        std::vector<double> objective(static_cast<std::size_t>(count), 0.0);
        objective[5] = 1.0;
        std::vector<char*> names(static_cast<std::size_t>(count));
        for (int i = 0; i < count; ++i)
            names[static_cast<std::size_t>(i)] =
                const_cast<char*>(fixture_model.names[static_cast<std::size_t>(i)].c_str());
        require(api.newmodel(env, &model, "round89_native_B1_toy", count,
            objective.data(), const_cast<double*>(fixture_model.lower_bounds.data()),
            const_cast<double*>(fixture_model.upper_bounds.data()),
            const_cast<char*>(fixture_model.types.data()), names.data()) == 0,
            "toy newmodel failed");
        for (std::size_t r = 0; r < fixture_model.senses.size(); ++r) {
            const int begin = fixture_model.row_starts[r];
            const int length = fixture_model.row_starts[r+1]-begin;
            require(api.addconstr(model, length,
                const_cast<int*>(fixture_model.column_indices.data()+begin),
                const_cast<double*>(fixture_model.coefficients.data()+begin),
                fixture_model.senses[r], fixture_model.rhs[r], nullptr) == 0,
                "toy original row add failed");
        }
        GRBenv* model_env = api.getenv(model);
        require(model_env != nullptr, "toy model environment missing");
        double static_feasibility_tolerance = 0.0;
        require(api.getdblparam(model_env, GRB_DBL_PAR_FEASIBILITYTOL,
                                &static_feasibility_tolerance)==0 &&
                std::isfinite(static_feasibility_tolerance) &&
                static_feasibility_tolerance>=0.0,
                "toy FeasibilityTol readback failed");
        if (arm == "static") {
            const auto cut = ebrp::separateNativeOtB1(
                pair, parityFractionalPoint(),
                static_feasibility_tolerance);
            require(cut.status == ebrp::NativeOtB1Cut::Status::Reliable,
                    "toy static B1 row missing");
            require(api.addconstr(model, static_cast<int>(cut.indices.size()),
                const_cast<int*>(cut.indices.data()),
                const_cast<double*>(cut.coefficients.data()),
                cut.sense, cut.rhs, "static_B1") == 0,
                "toy static B1 add failed");
            result.static_cut_added = true;
            result.static_cut = cut;
        }
        require(api.update(model) == 0, "toy update failed");
        require(api.write(model, model_export.string().c_str()) == 0,
                "toy arm LP export failed");
        result.model_sha256 = ebrp::fileSha256(model_export);
        require(!result.model_sha256.empty(), "toy arm LP hash failed");
        for (const auto& [name, value] :
             std::vector<std::pair<const char*, int>>{
                 {GRB_INT_PAR_OUTPUTFLAG,0}, {GRB_INT_PAR_THREADS,1},
                 {GRB_INT_PAR_SEED,0}, {GRB_INT_PAR_PRESOLVE,0},
                 {GRB_INT_PAR_CUTS,0}, {GRB_INT_PAR_PRECRUSH,arm=="callback" ? 1 : 0}})
            require(api.setintparam(model_env, name, value) == 0,
                    std::string("toy parameter failed:")+name);
        require(api.setdblparam(model_env, GRB_DBL_PAR_HEURISTICS, 0.0) == 0,
                "toy Heuristics failed");
        require(api.setdblparam(model_env, GRB_DBL_PAR_MIPGAP, 0.0) == 0,
                "toy MIPGap failed");
        require(api.getintparam(model_env, GRB_INT_PAR_PRECRUSH,
                                &result.precrush) == 0,
                "toy PreCrush readback failed");
        for (const char* name : {GRB_INT_PAR_OUTPUTFLAG,
                 GRB_INT_PAR_THREADS,GRB_INT_PAR_SEED,
                 GRB_INT_PAR_PRESOLVE,GRB_INT_PAR_CUTS,
                 GRB_INT_PAR_PRECRUSH}) {
            int value = 0;
            require(api.getintparam(model_env,name,&value)==0,
                    std::string("toy integer parameter readback failed:")+name);
            result.integer_parameter_readback.emplace(name,value);
        }
        for (const char* name : {GRB_DBL_PAR_HEURISTICS,
                 GRB_DBL_PAR_MIPGAP,GRB_DBL_PAR_INTFEASTOL,
                 GRB_DBL_PAR_FEASIBILITYTOL}) {
            double value = 0.0;
            require(api.getdblparam(model_env,name,&value)==0,
                    std::string("toy double parameter readback failed:")+name);
            result.double_parameter_readback.emplace(name,value);
        }
        result.observer.api = &api;
        result.observer.pair = &pair;
        result.observer.original_columns = count;
        result.observer.integrality_tolerance =
            result.double_parameter_readback.at(GRB_DBL_PAR_INTFEASTOL);
        result.observer.feasibility_tolerance =
            result.double_parameter_readback.at(GRB_DBL_PAR_FEASIBILITYTOL);
        require(std::isfinite(result.observer.integrality_tolerance) &&
                result.observer.integrality_tolerance>=0.0 &&
                result.observer.integrality_tolerance<0.5 &&
                std::isfinite(result.observer.feasibility_tolerance) &&
                result.observer.feasibility_tolerance>=0.0 &&
                result.observer.feasibility_tolerance==
                    static_feasibility_tolerance,
                "toy tolerance readback invalid or changed");
        for (int col=0; col<count; ++col)
            if (fixture_model.types[static_cast<std::size_t>(col)]=='B' &&
                fixture_model.upper_bounds[static_cast<std::size_t>(col)]>0.0)
                result.observer.enabled_selector_columns.push_back(col);
        if (arm == "callback")
            require(api.setcallback(model, callback, &result.observer) == 0,
                    "toy callback register failed");
        result.optimize_rc = api.optimize(model);
        require(result.optimize_rc == 0, "toy Optimize API failed");
        require(api.getintattr(model, GRB_INT_ATTR_STATUS, &result.status) == 0,
                "toy Status failed");
        if (result.status == GRB_OPTIMAL) {
            require(api.getdblattr(model, GRB_DBL_ATTR_OBJVAL,
                                   &result.objective) == 0, "toy ObjVal failed");
            result.primal.resize(static_cast<std::size_t>(count));
            require(api.getdblattrarray(model, GRB_DBL_ATTR_X, 0, count,
                                        result.primal.data()) == 0,
                    "toy primal read failed");
        }
        api.getdblattr(model, GRB_DBL_ATTR_WORK, &result.work);
        api.getdblattr(model, GRB_DBL_ATTR_RUNTIME, &result.runtime);
    } catch (...) {
        if (model) api.freemodel(model);
        if (env) api.freeenv(env);
        throw;
    }
    if (model) api.freemodel(model);
    if (env) api.freeenv(env);
    return result;
}

struct BackendToyResult {
    std::string arm;
    ebrp::FixedIntervalMipOutcome outcome;
};

void writeBackendArmRecord(const std::filesystem::path& path,
    const std::string& arm, const ebrp::FixedIntervalMipRequest& request,
    const ebrp::FixedIntervalMipOutcome& outcome,
    const ebrp::FixedIntervalMipBackendStats& stats,
    const ebrp::NativeOtB1LinearModel& original_model) {
    require(!std::filesystem::exists(path),"backend arm raw receipt already exists");
    std::ofstream out(path);
    require(static_cast<bool>(out),"backend arm raw receipt open failed");
    out << std::setprecision(17) << "{\"arm\":" << std::quoted(arm)
        << ",\"canonical_model_path\":"
        << std::quoted(request.canonical_model_path.string())
        << ",\"canonical_model_sha256\":"
        << std::quoted(request.canonical_model_fingerprint)
        << ",\"canonical_model_scope\":"
        << std::quoted(request.canonical_model_scope)
        << ",\"canonical_row_signature\":"
        << std::quoted(request.canonical_row_signature)
        << ",\"policy\":" << std::quoted(request.interval_mip_policy)
        << ",\"native_log_path\":"
        << std::quoted(request.native_log_path.string())
        << ",\"native_log_sha256\":"
        << std::quoted(std::filesystem::exists(request.native_log_path)
            ? ebrp::fileSha256(request.native_log_path) : std::string());
    const std::filesystem::path summary_path =
        request.native_log_path.string()+".round89.ot_b1.summary.json";
    out << ",\"B1_summary_path\":"
        << std::quoted(outcome.round89_native_ot_b1_active
            ? summary_path.string() : std::string())
        << ",\"B1_summary_sha256\":"
        << std::quoted(outcome.round89_native_ot_b1_active &&
                       std::filesystem::exists(summary_path)
            ? ebrp::fileSha256(summary_path) : std::string())
        << ",\"capture_lp_primal_dual_evidence\":"
        << std::boolalpha << request.capture_lp_primal_dual_evidence
        << ",\"optimize_rc\":" << outcome.optimize_return_code
        << ",\"status\":" << std::quoted(outcome.native_status)
        << ",\"failure_reason\":" << std::quoted(outcome.failure_reason)
        << ",\"finalized\":" << outcome.solver_finalization_reached
        << ",\"optimal\":" << outcome.optimal
        << ",\"native_bound_available\":"
        << outcome.native_bound_available
        << ",\"native_bound\":" << outcome.native_bound
        << ",\"incumbent_available\":" << outcome.incumbent_available
        << ",\"incumbent_objective\":"
        << outcome.incumbent_objective
        << ",\"model_fingerprint_matches_request\":"
        << outcome.model_fingerprint_matches_request
        << ",\"B1_active\":" << outcome.round89_native_ot_b1_active
        << ",\"B1_audit_valid\":"
        << outcome.round89_native_ot_b1_audit_valid
        << ",\"B1_audited_rows\":"
        << outcome.round89_native_ot_b1_audited_rows
        << ",\"B1_pairs\":" << outcome.round89_native_ot_b1_pairs
        << ",\"B1_mipnode_calls\":"
        << outcome.round89_native_ot_b1_mipnode_calls
        << ",\"B1_optimal_nodes\":"
        << outcome.round89_native_ot_b1_optimal_nodes
        << ",\"B1_reliable_rows\":"
        << outcome.round89_native_ot_b1_reliable_rows
        << ",\"B1_submitted_api_ok\":"
        << outcome.round89_native_ot_b1_submitted_api_ok
        << ",\"B1_numerical_skips\":"
        << outcome.round89_native_ot_b1_numerical_skips
        << ",\"B1_status\":"
        << std::quoted(outcome.round89_native_ot_b1_status)
        << ",\"runtime\":" << outcome.solver_runtime_seconds
        << ",\"work\":" << outcome.work
        << ",\"backend_parameter_readback\":{\"threads\":"
        << stats.threads_effective << ",\"presolve\":"
        << stats.presolve_effective << ",\"seed\":"
        << stats.seed_effective << ",\"mip_gap\":"
        << stats.mip_gap_effective << ",\"mip_gap_abs\":"
        << stats.mip_gap_abs_effective << "}"
        << ",\"raw_primal_scope\":"
        << std::quoted(outcome.lp_relaxation
            ? "lp_via_frozen_outcome_if_available"
            : "backend_mip_raw_primal_unavailable_via_frozen_interface")
        << ",\"raw_primal\":";
    std::map<std::string,double> values_by_name;
    if (outcome.lp_relaxation && outcome.lp_primal_values_available &&
        !outcome.lp_primal_dual_variable_evidence.empty()) {
        out << '[';
        for (std::size_t k=0;
             k<outcome.lp_primal_dual_variable_evidence.size(); ++k) {
            if (k) out << ',';
            const auto& item=outcome.lp_primal_dual_variable_evidence[k];
            out << "{\"name\":" << std::quoted(item.name)
                << ",\"value\":" << item.primal_value << '}';
            values_by_name.emplace(item.name,item.primal_value);
        }
        out << ']';
    } else out << "null";
    out << ",\"original_rows\":";
    std::vector<double> ordered_values;
    for (const auto& name : original_model.names) {
        const auto found=values_by_name.find(name);
        if (found==values_by_name.end()) {
            ordered_values.clear();
            break;
        }
        ordered_values.push_back(found->second);
    }
    if (ordered_values.size()==original_model.names.size()) {
        const double maximum=writeOriginalRowResiduals(
            out,original_model,ordered_values);
        out << ",\"maximum_original_row_violation\":" << maximum;
    } else out << "null,\"maximum_original_row_violation\":null";
    out << "}\n";
    out.flush();
    require(static_cast<bool>(out),"backend arm raw receipt write failed");
}

std::vector<BackendToyResult> runBackendToy(
    const std::filesystem::path& canonical,
    const std::filesystem::path& dll,
    const std::filesystem::path& receipt,
    std::ostream& arm_receipts,
    const ebrp::NativeOtB1LinearModel& original_model) {
    ebrp::Instance instance;
    instance.name = "round89_native_B1_isolated_backend_toy";
    instance.V = 2;
    instance.M = 1;
    instance.Q = {5};
    instance.capacity = {0,5,5};
    instance.initial = {0,1,1};
    instance.target = {0,1,1};
    instance.weights = {0.0,1.0,1.0};
    instance.min_ratio = {0.0,0.0,0.0};
    instance.points = {{0.0,0.0},{1.0,0.0},{2.0,0.0}};
    instance.dist.assign(3, std::vector<double>(3, 0.0));
    instance.total_time_limit = 10.0;
    instance.pickup_time = instance.drop_time = 0.0;
    ebrp::SolveOptions options;
    options.algorithm_preset = "research-round83-vds-equal-net-exchange";
    options.round89_native_ot_b1 = true;
    options.gurobi_presolve = 0; // isolated fixture exposure only
    options.gurobi_home = dll.parent_path().parent_path().string();
    auto backend = ebrp::makeGurobiFixedIntervalBackend(instance, options);
    require(backend && backend->capabilities().available,
            "toy production backend unavailable");
    const std::string fingerprint = ebrp::fileSha256(canonical);
    require(!fingerprint.empty(), "toy canonical LP hash failed");
    const std::vector<std::pair<std::string, ebrp::FixedIntervalSolveKind>> arms = {
        {"backend_lp_negative", ebrp::FixedIntervalSolveKind::PaperLpRelaxation},
        {"backend_terminal", ebrp::FixedIntervalSolveKind::PaperTerminalMip},
        {"backend_partial", ebrp::FixedIntervalSolveKind::PaperPartialBoundTargetMip}};
    std::vector<BackendToyResult> results;
    for (const auto& [name, kind] : arms) {
        ebrp::FixedIntervalMipRequest request;
        request.solve_kind = kind;
        request.leaf_id = name;
        request.gamma_L = 0.0;
        request.gamma_U = 1.0;
        request.verified_cutoff = 10.0;
        request.global_deadline_remaining_seconds = 30.0;
        request.canonical_model_path = canonical;
        request.canonical_model_fingerprint = fingerprint;
        request.canonical_model_scope = "round89_isolated_toy_original_model";
        request.canonical_row_signature = "round89_isolated_toy_original_rows";
        request.native_log_path =
            receipt.string() + "." + name + ".gurobi.log";
        request.interval_mip_policy = "round55-vd-p";
        request.capture_lp_primal_dual_evidence =
            kind == ebrp::FixedIntervalSolveKind::PaperLpRelaxation;
        results.push_back({name, backend->solve(request)});
        const auto& out = results.back().outcome;
        writeBackendArmRecord(receipt.string()+"."+name+".raw.json",
            name,request,out,backend->stats(),original_model);
        arm_receipts << "{\"arm\":" << std::quoted(name)
            << ",\"optimize_rc\":" << out.optimize_return_code
            << ",\"status\":" << std::quoted(out.native_status)
            << ",\"failure_reason\":" << std::quoted(out.failure_reason)
            << ",\"B1_active\":" << std::boolalpha
            << out.round89_native_ot_b1_active
            << ",\"B1_audit_valid\":" << out.round89_native_ot_b1_audit_valid
            << ",\"B1_submitted_api_ok\":"
            << out.round89_native_ot_b1_submitted_api_ok
            << ",\"runtime\":" << out.solver_runtime_seconds
            << ",\"work\":" << out.work << "}\n";
        arm_receipts.flush();
        require(static_cast<bool>(arm_receipts),
                "toy backend arm receipt write failed");
    }
    backend->release();
    require(results.size() == 3, "toy backend arm count invalid");
    for (std::size_t k = 0; k < results.size(); ++k) {
        const auto& out = results[k].outcome;
        const bool expected_b1 = k != 0;
        require(out.optimize_return_code == 0 &&
                out.solver_finalization_reached &&
                out.model_fingerprint_matches_request &&
                out.round89_native_ot_b1_active == expected_b1 &&
                out.round89_native_ot_b1_audit_valid == expected_b1 &&
                out.failure_reason == "none",
                "toy production backend integration failed:"+results[k].arm+
                    ":"+out.failure_reason);
    }
    return results;
}

void native(const std::filesystem::path& dll,
            const std::filesystem::path& receipt) {
    const auto m = parityExposureFixture();
    const auto prepared = ebrp::prepareNativeOtB1(m, 2);
    require(prepared.valid && prepared.pairs.size()==1,
            "native toy pure audit failed:"+prepared.reason);
    Api api(dll);
    std::vector<ToyResult> results;
    const std::filesystem::path canonical =
        receipt.string()+".original.lp";
    std::ofstream arm_receipts(receipt.string()+".arms.jsonl");
    require(static_cast<bool>(arm_receipts), "native arm receipt open failed");
    arm_receipts << std::setprecision(17);
    for (const std::string arm : {"off", "static", "callback"}) {
        const std::filesystem::path model_export = arm=="off"
            ? canonical : std::filesystem::path(receipt.string()+"."+arm+".lp");
        results.push_back(runToy(api, arm, m, prepared.pairs.front(), model_export));
        const auto& completed = results.back();
        writeDirectArmRecord(receipt.string()+"."+arm+".raw.json",
            completed,m);
        arm_receipts << "{\"arm\":" << std::quoted(arm)
            << ",\"optimize_rc\":" << completed.optimize_rc
            << ",\"status\":" << completed.status
            << ",\"objective\":" << completed.objective
            << ",\"runtime\":" << completed.runtime
            << ",\"work\":" << completed.work
            << ",\"fractional_nodes\":"
            << completed.observer.fractional_nodes
            << ",\"submitted_api_ok\":"
            << completed.observer.submitted_api_ok << "}\n";
        arm_receipts.flush();
        require(static_cast<bool>(arm_receipts), "native arm receipt write failed");
    }
    const auto backend_results = runBackendToy(
        canonical, dll, receipt, arm_receipts, m);
    std::ofstream out(receipt);
    require(static_cast<bool>(out), "native receipt open failed");
    out << std::setprecision(17) << "{\"toy_only_parameters\":{"
        << "\"Presolve\":0,\"Cuts\":0,\"Heuristics\":0,"
        << "\"Threads\":1,\"Seed\":0},\"arms\":[";
    for (std::size_t k = 0; k < results.size(); ++k) {
        if (k) out << ',';
        const auto& r = results[k];
        out << "{\"arm\":" << std::quoted(r.arm)
            << ",\"optimize_rc\":" << r.optimize_rc
            << ",\"status\":" << r.status
            << ",\"precrush\":" << r.precrush
            << ",\"objective\":" << r.objective
            << ",\"work\":" << r.work
            << ",\"runtime\":" << r.runtime
            << ",\"optimal_nodes\":" << r.observer.optimal_nodes
            << ",\"fractional_nodes\":" << r.observer.fractional_nodes
            << ",\"reliable_rows\":" << r.observer.reliable_rows
            << ",\"submitted_api_ok\":" << r.observer.submitted_api_ok
            << ",\"callback_failure_code\":" << r.observer.failure_code
            << ",\"primal\":[";
        for (std::size_t col=0; col<r.primal.size(); ++col) {
            if (col) out << ',';
            out << r.primal[col];
        }
        out << "]}";
    }
    out << "],\"backend_arms\":[";
    for (std::size_t k = 0; k < backend_results.size(); ++k) {
        if (k) out << ',';
        const auto& b = backend_results[k];
        out << "{\"arm\":" << std::quoted(b.arm)
            << ",\"optimize_rc\":" << b.outcome.optimize_return_code
            << ",\"status\":" << std::quoted(b.outcome.native_status)
            << ",\"B1_active\":" << std::boolalpha
            << b.outcome.round89_native_ot_b1_active
            << ",\"B1_audit_valid\":"
            << b.outcome.round89_native_ot_b1_audit_valid
            << ",\"B1_mipnode_calls\":"
            << b.outcome.round89_native_ot_b1_mipnode_calls
            << ",\"B1_submitted_api_ok\":"
            << b.outcome.round89_native_ot_b1_submitted_api_ok
            << ",\"runtime\":" << b.outcome.solver_runtime_seconds
            << ",\"work\":" << b.outcome.work << '}';
    }
    out << "]}\n";
    require(static_cast<bool>(out), "native receipt write failed");
    for (const auto& r : results) {
        require(r.optimize_rc == 0 && r.status == GRB_OPTIMAL &&
                std::fabs(r.objective - 1.0) <= 1e-6,
                "toy integer optimum disagreement:"+r.arm);
        require(r.primal.size() == m.names.size() &&
                r.primal[5] + 1e-6 >= std::fabs(r.primal[3]-r.primal[4]),
                "toy original h row/physical witness mismatch:"+r.arm);
        std::ostringstream row_sink;
        const double maximum_row = writeOriginalRowResiduals(
            row_sink,m,r.primal);
        const auto domain = domainResiduals(m,r.primal);
        require(maximum_row<=1e-6 && domain.bounds<=1e-6 &&
                domain.integrality<=1e-6,
                "toy original rows/domain witness mismatch:"+r.arm);
    }
    const auto& cb = results[2];
    require(cb.precrush == 1 && cb.observer.optimal_nodes > 0 &&
            cb.observer.fractional_nodes > 0 &&
            cb.observer.fractional_reliable_rows > 0 &&
            cb.observer.fractional_submitted_api_ok > 0 &&
            cb.observer.failure_code == 0,
            "toy callback qualification inapplicable_or_failed");
    for (std::size_t k=1; k<backend_results.size(); ++k)
        require(backend_results[k].outcome.round89_native_ot_b1_mipnode_calls>0 &&
                backend_results[k].outcome.round89_native_ot_b1_submitted_api_ok>0,
                "toy production callback exposure inapplicable:"+
                    backend_results[k].arm);
}
} // namespace

int main(int argc, char** argv) {
    const auto started = std::chrono::steady_clock::now();
    try {
        require(argc >= 2, "usage: pure | pure-json PATH | native DLL RECEIPT");
        const std::string mode = argv[1];
        if (mode == "pure") pure();
        else if (mode == "pure-json" && argc == 3) pureJson(argv[2]);
        else if (mode == "native" && argc == 4) native(argv[2], argv[3]);
        else throw std::runtime_error("unknown micro-test mode");
        std::cout << "round89_native_ot_b1_" << mode << "_passed\n";
        return 0;
    } catch (const std::exception& error) {
        if (argc == 4 && std::string(argv[1]) == "native") {
            // Preserve paid setup/Optimize failures even when the three-arm
            // success receipt could not be completed.
            std::ofstream failed(std::string(argv[3])+".failure.json");
            if (failed)
                failed << std::setprecision(17)
                    << "{\"status\":\"failed\",\"reason\":"
                    << std::quoted(error.what())
                    << ",\"external_process_wall_seconds\":"
                    << std::chrono::duration<double>(
                        std::chrono::steady_clock::now()-started).count()
                    << "}\n";
        }
        std::cerr << "round89_native_ot_b1_micro_failed:" << error.what() << '\n';
        return 1;
    }
}
