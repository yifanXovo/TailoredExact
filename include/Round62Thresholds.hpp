#pragma once
#include "Instance.hpp"
#include <filesystem>
#include <map>

namespace ebrp {
struct Round62Event {
    int station=0, direction=0, quantity=0; // -1 pickup, +1 drop; quantity != Q_k
    std::string name() const;
};
struct Round62Edge {
    int first=0,second=0;
    double travel_lower=0,handling_lower=0,duration_lower=0;
    std::vector<int> common_vehicles;
};
struct Round62Conflict {
    std::vector<Round62Event> events;
    std::vector<std::vector<int>> eligible;
    std::vector<Round62Edge> edges;
    std::vector<int> vehicle_union;
};
struct Round62ThresholdProof {
    std::vector<std::vector<double>> shortest;
    std::vector<Round62Conflict> conflicts;
    std::vector<Round62Event> dictionary;
    long long pair_checks=0,clique_search_nodes=0,weakening_checks=0;
    int incompatible_edges=0,initial_events=0;
    double margin=0,seconds=0,maximum_pair_lower=0;
    bool search_truncated=false;
    std::string scope="original_physical_global";
};
std::vector<std::vector<double>> round62Shortest(const Instance&);
bool proveRound62Conflict(const Instance&, const std::vector<std::vector<double>>&,
                         const std::vector<Round62Event>&,Round62Conflict* proof=nullptr);
Round62ThresholdProof generateRound62Thresholds(const Instance&);
struct Round62Row {
    std::string name; std::map<std::string,double> coefficients; char sense='>'; double rhs=0;
    std::string scope="original_physical_global";
    double gamma_lower=0,gamma_upper=1;
};
std::vector<Round62Row> round62ThresholdRows(const Instance&,const Round62ThresholdProof&,const std::string&,double gamma_lower=0,double gamma_upper=1);
void appendRound62ThresholdModel(const Instance&,const std::filesystem::path&,const std::string&,double gamma_lower=0,double gamma_upper=1);
void writeRound62ThresholdProof(const Instance&,const Round62ThresholdProof&,
                              const std::vector<Round62Row>&,const std::filesystem::path&);
} // namespace ebrp
