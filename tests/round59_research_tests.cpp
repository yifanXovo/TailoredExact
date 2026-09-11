#include "Round59Research.hpp"
#include "Evaluator.hpp"
#include <iostream>
#include <stdexcept>

int main() {
    const ebrp::FixedIntervalMipRequest defaults;
    if (defaults.round59_additional_rows_user_pool || defaults.round59_mip_focus != -1 ||
        !defaults.round59_node_samples_path.empty()) throw std::runtime_error("research must default off");
    ebrp::Instance inst;
    inst.V=3; inst.M=1; inst.Q={3};
    inst.capacity={100,4,4,4}; inst.initial={50,3,1,2};
    inst.target={0,2,2,2}; inst.weights={0,1,1,1};
    inst.pickup_time=1; inst.drop_time=1; inst.total_time_limit=30;
    // Deliberately nonmetric directed distances: closure must be used.
    inst.dist={{0,2,20,3},{4,0,2,8},{2,9,0,1},{3,2,7,0}};
    const auto cuts=ebrp::round59PairDurationRows(inst);
    if(cuts.size()!=3) throw std::runtime_error("pair count");
    if(!ebrp::verifySolution(inst,{},0.15).feasible) throw std::runtime_error("empty");
    int checked=0, returns_loaded=0;
    std::vector<int> permutation={1,2,3};
    do {
        for(int length=1;length<=3;++length)
            for(int code=0;code<343;++code) {
                int value=code;
                ebrp::RoutePlan route; route.vehicle=0; route.nodes={0};
                for(int j=0;j<length;++j) {
                    int amount=value%7-3; value/=7;
                    route.nodes.push_back(permutation[j]);
                    ebrp::StopOperation op; op.station=permutation[j];
                    op.pickup=std::max(amount,0); op.drop=std::max(-amount,0);
                    route.operations.push_back(op);
                }
                route.nodes.push_back(0);
                const auto v=ebrp::verifySolution(inst,{route},0.15);
                if(!v.feasible) continue;
                ++checked;
                int load=0; for(const auto& op:route.operations) load+=op.pickup-op.drop;
                if(load>0) ++returns_loaded;
                for(const auto& cut:cuts) {
                    double lhs=0;
                    for(std::size_t j=0;j<cut.variable_names.size();++j) {
                        const auto& name=cut.variable_names[j];
                        int station=std::stoi(name.substr(name.find_last_of('_')+1));
                        for(const auto& op:route.operations) if(op.station==station)
                            lhs+=cut.coefficients[j]*(name[0]=='p'?op.pickup:1);
                    }
                    if(lhs>cut.rhs+1e-9) throw std::runtime_error("invalid support cut");
                }
            }
    } while(std::next_permutation(permutation.begin(),permutation.end()));
    if(!checked || !returns_loaded) throw std::runtime_error("enumeration empty");
    inst.dist[0][1]=-1;
    bool rejected=false;
    try { ebrp::round59PairDurationRows(inst); } catch(const std::runtime_error&) { rejected=true; }
    if(!rejected) throw std::runtime_error("negative travel accepted");
    std::cout<<"Verified "<<checked<<" feasible route/operation realizations; "
             <<returns_loaded<<" return loaded; all pair cuts valid.\n";
}
