#include "Round96RouteOrder.hpp"
#include "Round95FullBlockDescent.hpp"
#include <cmath>
#include <iostream>
#include <stdexcept>

int main(){try {
    ebrp::Instance in;in.V=3;in.M=1;in.Q={3};
    in.initial={50,4,0,0};in.capacity={100,4,2,2};in.target={0,1,1,1};in.weights={0,1,1,1};
    in.points={{0,0},{0,1},{1,0},{1,1}};in.dist.assign(4,std::vector<double>(4));
    for(int i=0;i<4;++i)for(int j=0;j<4;++j)
        in.dist[i][j]=std::hypot(in.points[i].first-in.points[j].first,in.points[i].second-in.points[j].second);
    in.total_time_limit=2+2*std::sqrt(2.)+.8;in.pickup_time=.2;in.drop_time=.2;
    ebrp::SolveOptions opt;opt.lambda=.15;
    std::vector<ebrp::RoutePlan> routes{{0,{0,1,2,3,0},{{1,2,0},{2,0,1},{3,0,1}}}};
    const auto before=ebrp::verifyRound95StartingWitness(in,routes,opt.lambda);
    const auto pair=ebrp::runRound95FullBlockDescent(in,opt,routes);
    if(!pair.stats.exhausted||pair.stats.accepted||pair.verification.objective!=before.objective)
        throw std::runtime_error("Fixture is not a complete pair stop");
    const auto old=ebrp::runRound83ExchangeDescent(in,opt,routes);
    if(!old.exhausted||old.verification.objective!=before.objective)
        throw std::runtime_error("Fixture is not an original R83 stop");
    const auto order=ebrp::runRound96RouteOrder(in,opt,old.routes);
    if(!order.stats.zero||order.verification.objective!=0||!order.stats.accepted||!order.stats.quantities)
        throw std::runtime_error("Order failed to release the quantity improvement");
    if(order.stats.verification_failed||!order.verification.feasible)throw std::runtime_error("Invalid order result");
    const auto again=ebrp::runRound96RouteOrder(in,opt,order.routes);
    if(!again.stats.zero||again.stats.accepted||again.verification.objective!=0)
        throw std::runtime_error("Non-idempotent zero endpoint");
    std::cout.precision(17);
    std::cout<<"{\"initial_F\":"<<before.objective<<",\"pair_F\":"<<pair.verification.objective
             <<",\"old_F\":"<<old.verification.objective<<",\"order_F\":"<<order.verification.objective
             <<",\"order_moves\":"<<order.stats.accepted<<",\"quantities\":"<<order.stats.quantities
             <<",\"optimizer_calls\":0}\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
