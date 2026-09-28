#include "Round96MultiQuantity.hpp"
#include "Round95FullBlockDescent.hpp"
#include <cmath>
#include <iostream>
#include <stdexcept>

int main(){try {
    ebrp::Instance in;in.V=4;in.M=1;in.Q={6};
    in.capacity={100,50,2,2,2};in.initial={50,8,0,0,0};in.target={0,50,2,2,2};
    in.weights={0,.001,1,1,1};in.dist.assign(5,std::vector<double>(5,0));
    in.total_time_limit=12;in.pickup_time=1;in.drop_time=1;
    std::vector<ebrp::RoutePlan> routes{{0,{0,1,2,3,4,0},{{1,3,0},{2,0,1},{3,0,1},{4,0,1}}}};
    ebrp::SolveOptions opt;opt.lambda=.15;
    const auto before=ebrp::verifyRound95StartingWitness(in,routes,opt.lambda);
    const auto pair=ebrp::runRound95FullBlockDescent(in,opt,routes);
    if(!pair.stats.exhausted||pair.stats.accepted||std::fabs(pair.verification.objective-before.objective)>1e-12)
        throw std::runtime_error("fixture is not a full two-station stop");
    const auto multi=ebrp::runRound96MultiQuantity(in,opt,pair.routes);
    if(!multi.stats.exhausted||!multi.stats.accepted||!(multi.verification.objective<before.objective-1e-4))
        throw std::runtime_error("multi-station rays did not escape");
    if(!multi.verification.feasible)throw std::runtime_error("nonphysical fixture result");
    std::cout.precision(17);
    std::cout<<"{\"initial_F\":"<<before.objective<<",\"pair_F\":"<<pair.verification.objective
             <<",\"multi_F\":"<<multi.verification.objective<<",\"accepted\":"<<multi.stats.accepted
             <<",\"points\":"<<multi.stats.points<<",\"optimizer_calls\":0}\n";
    // Repeating a complete exhausted pass must not change the incumbent.
    const auto again=ebrp::runRound96MultiQuantity(in,opt,multi.routes);
    if(again.stats.accepted||!again.stats.exhausted||again.verification.objective!=multi.verification.objective)
        throw std::runtime_error("non-idempotent exhausted neighborhood");
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
