#include "ConnectivityFlow.hpp"

#include <algorithm>
#include <cctype>
#include <set>

namespace ebrp {
namespace {

std::string normalizedVariantText(std::string_view value) {
    std::size_t first = 0;
    while (first < value.size() &&
           std::isspace(static_cast<unsigned char>(value[first])) != 0) {
        ++first;
    }
    std::size_t last = value.size();
    while (last > first &&
           std::isspace(static_cast<unsigned char>(value[last - 1])) != 0) {
        --last;
    }
    std::string normalized(value.substr(first, last - first));
    std::transform(normalized.begin(), normalized.end(), normalized.begin(),
                   [](unsigned char ch) {
                       if (ch == '_') return '-';
                       return static_cast<char>(std::tolower(ch));
                   });
    return normalized;
}

int dominanceRank(ConnectivityFlowVariant variant) noexcept {
    switch (variant) {
    case ConnectivityFlowVariant::Off: return 0;
    case ConnectivityFlowVariant::Round20Current: return 1;
    case ConnectivityFlowVariant::ZeroReturn: return 2;
    case ConnectivityFlowVariant::Normalized: return 3;
    case ConnectivityFlowVariant::NormalizedStartCoupled: return 4;
    }
    return -1;
}

bool validArc(int station_count, int from, int to) noexcept {
    return station_count >= 1 && from >= 0 && from <= station_count &&
        to >= 0 && to <= station_count && from != to;
}

} // namespace

const char* connectivityFlowVariantName(ConnectivityFlowVariant variant) noexcept {
    switch (variant) {
    case ConnectivityFlowVariant::Off: return "off";
    case ConnectivityFlowVariant::Round20Current: return "round20-current";
    case ConnectivityFlowVariant::ZeroReturn: return "zero-return";
    case ConnectivityFlowVariant::Normalized: return "normalized";
    case ConnectivityFlowVariant::NormalizedStartCoupled:
        return "normalized-start-coupled";
    }
    return "invalid";
}

bool parseConnectivityFlowVariant(std::string_view value,
                                  ConnectivityFlowVariant& variant,
                                  std::string* failure_reason) {
    const std::string normalized = normalizedVariantText(value);
    if (normalized == "off" || normalized == "none" ||
        normalized == "false" || normalized == "0") {
        variant = ConnectivityFlowVariant::Off;
    } else if (normalized == "round20-current" || normalized == "current" ||
               normalized == "f0" || normalized == "true" ||
               normalized == "1") {
        variant = ConnectivityFlowVariant::Round20Current;
    } else if (normalized == "zero-return" || normalized == "f1") {
        variant = ConnectivityFlowVariant::ZeroReturn;
    } else if (normalized == "normalized" || normalized == "f2") {
        variant = ConnectivityFlowVariant::Normalized;
    } else if (normalized == "normalized-start-coupled" ||
               normalized == "start-coupled" || normalized == "f3") {
        variant = ConnectivityFlowVariant::NormalizedStartCoupled;
    } else {
        if (failure_reason != nullptr) {
            *failure_reason = normalized.empty()
                ? "empty_connectivity_flow_variant"
                : "unknown_connectivity_flow_variant:" + normalized;
        }
        return false;
    }
    if (failure_reason != nullptr) failure_reason->clear();
    return true;
}

ConnectivityFlowVariantResolution resolveConnectivityFlowVariant(
    bool legacy_enabled,
    std::string_view explicit_value) {
    ConnectivityFlowVariantResolution resolution;
    const std::string normalized = normalizedVariantText(explicit_value);
    if (normalized.empty()) {
        resolution.valid = true;
        resolution.used_legacy_switch = true;
        resolution.requested = legacy_enabled ? "legacy:true" : "legacy:false";
        resolution.variant = legacy_enabled
            ? ConnectivityFlowVariant::Round20Current
            : ConnectivityFlowVariant::Off;
        resolution.resolved = connectivityFlowVariantName(resolution.variant);
        return resolution;
    }

    resolution.requested = std::string(explicit_value);
    if (!parseConnectivityFlowVariant(
            explicit_value, resolution.variant, &resolution.failure_reason)) {
        return resolution;
    }
    if (legacy_enabled &&
        resolution.variant != ConnectivityFlowVariant::Round20Current) {
        resolution.failure_reason =
            "conflicting_legacy_and_explicit_connectivity_flow_variants";
        return resolution;
    }
    resolution.valid = true;
    resolution.resolved = connectivityFlowVariantName(resolution.variant);
    return resolution;
}

bool connectivityFlowEnabled(ConnectivityFlowVariant variant) noexcept {
    return variant != ConnectivityFlowVariant::Off;
}

bool connectivityFlowUsesReturnColumns(ConnectivityFlowVariant variant) noexcept {
    return variant == ConnectivityFlowVariant::Round20Current;
}

bool connectivityFlowHasLowerLinks(ConnectivityFlowVariant variant) noexcept {
    return variant == ConnectivityFlowVariant::Normalized ||
        variant == ConnectivityFlowVariant::NormalizedStartCoupled;
}

bool connectivityFlowHasStartCoupling(ConnectivityFlowVariant variant) noexcept {
    return variant == ConnectivityFlowVariant::NormalizedStartCoupled;
}

bool hasConnectivityFlowColumn(ConnectivityFlowVariant variant,
                               int station_count,
                               int from,
                               int to) noexcept {
    if (!connectivityFlowEnabled(variant) ||
        !validArc(station_count, from, to)) {
        return false;
    }
    return connectivityFlowUsesReturnColumns(variant) || to != 0;
}

std::optional<double> connectivityFlowArcUpperBound(
    ConnectivityFlowVariant variant,
    int station_count,
    int from,
    int to) noexcept {
    if (!hasConnectivityFlowColumn(variant, station_count, from, to)) {
        return std::nullopt;
    }
    if (variant == ConnectivityFlowVariant::Round20Current ||
        variant == ConnectivityFlowVariant::ZeroReturn || from == 0) {
        return static_cast<double>(station_count);
    }
    return static_cast<double>(station_count - 1);
}

ConnectivityFlowCounts connectivityFlowTheoreticalCounts(
    ConnectivityFlowVariant variant,
    int station_count,
    int vehicle_count) {
    ConnectivityFlowCounts counts;
    if (station_count < 1) {
        counts.failure_reason = "station_count_must_be_positive";
        return counts;
    }
    if (vehicle_count < 1) {
        counts.failure_reason = "vehicle_count_must_be_positive";
        return counts;
    }
    counts.valid = true;
    if (!connectivityFlowEnabled(variant)) return counts;

    const long long v = station_count;
    const long long m = vehicle_count;
    const bool f0 = variant == ConnectivityFlowVariant::Round20Current;
    const long long flow_arcs = f0 ? v * (v + 1) : v * v;
    counts.columns = m * flow_arcs;
    counts.upper_link_rows = m * flow_arcs;
    counts.station_balance_rows = m * v;
    counts.depot_balance_rows = m;
    if (connectivityFlowHasLowerLinks(variant)) {
        counts.lower_link_rows = m * v * v;
    }
    if (connectivityFlowHasStartCoupling(variant)) {
        counts.start_upper_rows = m * v;
        counts.start_lower_rows = m * v;
    }
    counts.total_rows = counts.upper_link_rows + counts.lower_link_rows +
        counts.station_balance_rows + counts.depot_balance_rows +
        counts.start_upper_rows + counts.start_lower_rows;

    const long long upper_nonzeros = 2 * counts.upper_link_rows;
    const long long lower_nonzeros = 2 * counts.lower_link_rows;
    const long long station_nonzeros = f0
        ? m * v * (2 * v + 1)
        : m * v * (2 * v);
    const long long depot_nonzeros = f0 ? m * 3 * v : m * 2 * v;
    const long long start_nonzeros = connectivityFlowHasStartCoupling(variant)
        ? m * v * ((v + 1) + (v + 2))
        : 0;
    counts.total_nonzeros = upper_nonzeros + lower_nonzeros +
        station_nonzeros + depot_nonzeros + start_nonzeros;
    return counts;
}

ConnectivityFlowProjection buildCanonicalConnectivityFlowProjection(
    ConnectivityFlowVariant variant,
    int station_count,
    const std::vector<int>& depot_closed_route) {
    ConnectivityFlowProjection projection;
    if (station_count < 1) {
        projection.failure_reason = "station_count_must_be_positive";
        return projection;
    }
    if (depot_closed_route.empty() || depot_closed_route.front() != 0 ||
        depot_closed_route.back() != 0) {
        projection.failure_reason = "route_must_be_depot_closed";
        return projection;
    }

    std::size_t interior_begin = 1;
    std::size_t interior_end = depot_closed_route.size() - 1;
    if (depot_closed_route.size() == 1) {
        interior_begin = interior_end = 0;
    }
    std::set<int> visited;
    for (std::size_t position = interior_begin; position < interior_end;
         ++position) {
        const int station = depot_closed_route[position];
        if (station < 1 || station > station_count) {
            projection.failure_reason = "route_contains_invalid_station";
            return projection;
        }
        if (!visited.insert(station).second) {
            projection.failure_reason = "route_is_not_elementary";
            return projection;
        }
    }
    projection.visited_station_count = static_cast<int>(visited.size());
    projection.valid = true;
    if (!connectivityFlowEnabled(variant) || visited.empty()) {
        return projection;
    }

    const int s = projection.visited_station_count;
    for (int position = 0; position < s; ++position) {
        const int from = depot_closed_route[static_cast<std::size_t>(position)];
        const int to = depot_closed_route[static_cast<std::size_t>(position + 1)];
        if (!hasConnectivityFlowColumn(variant, station_count, from, to)) {
            projection.valid = false;
            projection.failure_reason = "canonical_nonreturn_flow_column_missing";
            projection.arc_values.clear();
            return projection;
        }
        projection.arc_values.push_back(
            {from, to, static_cast<double>(s - position)});
    }
    if (connectivityFlowUsesReturnColumns(variant)) {
        projection.arc_values.push_back(
            {depot_closed_route[static_cast<std::size_t>(s)], 0, 0.0});
    }
    return projection;
}

double connectivityFlowProjectionValue(const ConnectivityFlowProjection& projection,
                                       int from,
                                       int to) noexcept {
    for (const ConnectivityFlowArcValue& arc : projection.arc_values) {
        if (arc.from == from && arc.to == to) return arc.value;
    }
    return 0.0;
}

bool connectivityFlowCanEmbedInto(ConnectivityFlowVariant stronger,
                                  ConnectivityFlowVariant weaker) noexcept {
    return dominanceRank(stronger) >= dominanceRank(weaker);
}

} // namespace ebrp
