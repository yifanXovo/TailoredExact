#pragma once

#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace ebrp {

enum class ConnectivityFlowVariant {
    Off,
    Round20Current,
    ZeroReturn,
    Normalized,
    NormalizedStartCoupled,
};

const char* connectivityFlowVariantName(ConnectivityFlowVariant variant) noexcept;

bool parseConnectivityFlowVariant(std::string_view value,
                                  ConnectivityFlowVariant& variant,
                                  std::string* failure_reason = nullptr);

struct ConnectivityFlowVariantResolution {
    bool valid = false;
    ConnectivityFlowVariant variant = ConnectivityFlowVariant::Off;
    std::string requested;
    std::string resolved;
    std::string failure_reason;
    bool used_legacy_switch = false;
};

// An empty explicit value means that only the legacy Boolean was supplied.
// A true legacy switch is exactly the Round 20 formulation.  Supplying a
// conflicting explicit value together with a true legacy switch fails closed.
ConnectivityFlowVariantResolution resolveConnectivityFlowVariant(
    bool legacy_enabled,
    std::string_view explicit_value);

bool connectivityFlowEnabled(ConnectivityFlowVariant variant) noexcept;
bool connectivityFlowUsesReturnColumns(ConnectivityFlowVariant variant) noexcept;
bool connectivityFlowHasLowerLinks(ConnectivityFlowVariant variant) noexcept;
bool connectivityFlowHasStartCoupling(ConnectivityFlowVariant variant) noexcept;

bool hasConnectivityFlowColumn(ConnectivityFlowVariant variant,
                               int station_count,
                               int from,
                               int to) noexcept;

// Returns no value when the requested arc has no auxiliary-flow column.
std::optional<double> connectivityFlowArcUpperBound(
    ConnectivityFlowVariant variant,
    int station_count,
    int from,
    int to) noexcept;

struct ConnectivityFlowCounts {
    bool valid = false;
    std::string failure_reason;
    long long columns = 0;
    long long upper_link_rows = 0;
    long long lower_link_rows = 0;
    long long station_balance_rows = 0;
    long long depot_balance_rows = 0;
    long long start_upper_rows = 0;
    long long start_lower_rows = 0;
    long long total_rows = 0;
    long long total_nonzeros = 0;
};

// Counts only the connectivity-flow extension, not the underlying compact
// model.  Bounds are column bounds and therefore are not counted as rows.
ConnectivityFlowCounts connectivityFlowTheoreticalCounts(
    ConnectivityFlowVariant variant,
    int station_count,
    int vehicle_count);

struct ConnectivityFlowArcValue {
    int from = 0;
    int to = 0;
    double value = 0.0;
};

struct ConnectivityFlowProjection {
    bool valid = false;
    std::string failure_reason;
    int visited_station_count = 0;
    std::vector<ConnectivityFlowArcValue> arc_values;
};

// Builds the canonical projection for an elementary depot-closed route.
// Both {0} and {0, 0} denote an unused vehicle.  F0 includes the used return
// arc with value zero; F1--F3 eliminate that column.
ConnectivityFlowProjection buildCanonicalConnectivityFlowProjection(
    ConnectivityFlowVariant variant,
    int station_count,
    const std::vector<int>& depot_closed_route);

// Missing arcs, including every unused auxiliary column, have value zero.
double connectivityFlowProjectionValue(const ConnectivityFlowProjection& projection,
                                       int from,
                                       int to) noexcept;

// True exactly along the proved projection/dominance chain
// F3 -> F2 -> F1 -> F0 -> off.
bool connectivityFlowCanEmbedInto(ConnectivityFlowVariant stronger,
                                  ConnectivityFlowVariant weaker) noexcept;

} // namespace ebrp
