#pragma once
#include "Instance.hpp"
#include "NativeOtB1.hpp"
#include <map>
#include <deque>
#include <string>
#include <vector>

namespace ebrp {
struct FleetEvent { int station=0, direction=0, quantity=0; };
struct FleetContract {
    bool valid=false;
    std::string reason;
    std::string proof_identity; // full serialized immutable contract, not a certificate substitute
    int columns=0, audited_rows=0;
    double handling_lower=0, horizon_upper=0;
    std::vector<int> capacities, initial, station_capacity;
    std::vector<std::vector<double>> travel_lower, shortest_lower;
    std::vector<std::vector<std::pair<int,int>>> states; // (inventory, original column)
};
struct FleetProof {
    bool valid=false;
    std::string reason, method;
    int rank=0;
    std::vector<FleetEvent> events;
    std::vector<std::vector<unsigned char>> allowed; // complete small necessary system
    std::vector<std::vector<int>> dp;
    std::vector<int> pickup_counts, drop_counts;
    std::vector<double> travel_min;
};
struct FleetCut {
    FleetProof proof;
    std::vector<int> indices;
    std::vector<double> coefficients;
    double activity_lower=0, violation_lower=0;
    std::string key;
};
struct FleetStatistics {
    long long candidates=0, proofs=0, small_proofs=0, large_proofs=0;
    long long greedy_full=0, reliable=0, duplicates=0, arithmetic_skips=0;
    long long cache_hits=0;
    std::string cache_contract;
    std::map<std::string,FleetProof> proof_cache;
    std::deque<std::string> cache_order;
};
FleetContract prepareFleetContract(const Instance&,const NativeOtB1LinearModel&);
FleetContract physicalFleetContract(const Instance&); // independent tests/diagnostics only
FleetProof proveFleetSmall(const FleetContract&,const std::vector<FleetEvent>&);
FleetProof proveFleetLarge(const FleetContract&,const std::vector<FleetEvent>&,bool hall=true);
std::vector<FleetCut> separateFleetEvents(const FleetContract&,const std::vector<double>&,
    double violation_margin,FleetStatistics&,int max_rows=2);
std::string fleetProofJson(const FleetProof&);
std::string fleetContractJson(const FleetContract&);
} // namespace ebrp
