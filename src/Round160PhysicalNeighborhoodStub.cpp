#include "Round160PhysicalNeighborhood.hpp"
#include <stdexcept>
namespace ebrp::round160 {
bool& enabled(){static bool value=false;return value;}
Outcome optimize(const Instance&,double,const std::vector<RoutePlan>&,
                 const std::filesystem::path&,const Config&,const std::function<double()>&){
    throw std::runtime_error("Round160 physical neighborhood requires the optional Gurobi backend");
}
}
