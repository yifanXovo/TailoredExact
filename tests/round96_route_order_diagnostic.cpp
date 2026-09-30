#include "Round96RouteOrder.hpp"
#include "PhysicalWitnessValidation.hpp"
#include "Round61Candidates.hpp"
#include "Parser.hpp"
#include "FileSha256.hpp"
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>

int main(int argc,char** argv){try {
    const auto start=std::chrono::steady_clock::now();
    if(argc!=8)throw std::invalid_argument("input route_text T pickup drop lambda output_dir");
    const auto in=ebrp::parseInstanceFile(argv[1],std::stod(argv[3]),std::stod(argv[4]),std::stod(argv[5]));
    ebrp::SolveOptions opt;opt.lambda=std::stod(argv[6]);
    std::ifstream file(argv[2]);int count=0;file>>count;
    if(count!=in.M)throw std::invalid_argument("Route count");
    std::vector<ebrp::RoutePlan> routes;
    for(int k=0;k<count;++k) {
        int vehicle,n;file>>vehicle>>n;if(!file||n<0||n>in.V)throw std::invalid_argument("Route header");
        ebrp::RoutePlan r;r.vehicle=vehicle;r.nodes={0};
        for(int j=0;j<n;++j){int i,p,d;file>>i>>p>>d;if(!file)throw std::invalid_argument("Route operation");
            r.nodes.push_back(i);r.operations.push_back({i,p,d});}
        r.nodes.push_back(0);routes.push_back(std::move(r));
    }
    const auto initial=ebrp::verifyCompletePhysicalStartingWitness(in,routes,opt.lambda);
    const std::filesystem::path dest(argv[7]);if(std::filesystem::exists(dest))throw std::invalid_argument("Output exists");
    std::filesystem::create_directories(dest);
    const auto before_old=std::chrono::steady_clock::now();
    const auto old=ebrp::runRound83ExchangeDescent(in,opt,routes,dest/"old");
    const auto before_new=std::chrono::steady_clock::now();
    const auto changed=ebrp::runRound96RouteOrder(in,opt,old.routes,dest/"order");
    const auto end=std::chrono::steady_clock::now();
    auto seconds=[](auto a,auto b){return std::chrono::duration<double>(b-a).count();};
    const auto& s=changed.stats;
    std::ofstream out(dest/"summary.json");out<<std::setprecision(17)
       <<"{\"input_sha256\":\""<<ebrp::fileSha256(argv[1])<<"\",\"route_sha256\":\""<<ebrp::fileSha256(argv[2])
       <<"\",\"initial_F\":"<<initial.objective<<",\"old_F\":"<<old.verification.objective
       <<",\"old_exhausted\":"<<old.exhausted<<",\"old_zero\":"<<old.zero<<",\"old_failed\":"<<old.verification_failed
       <<",\"old_neutral\":"<<old.neutral<<",\"old_insertions\":"<<old.insertions<<",\"old_quantities\":"<<old.quantities
       <<",\"old_seconds\":"<<seconds(before_old,before_new)<<",\"order_seconds\":"<<seconds(before_new,end)
       <<",\"order_F\":"<<changed.verification.objective<<",\"order_moves\":"<<s.accepted
       <<",\"proposals\":"<<s.proposals<<",\"load_feasible\":"<<s.load_feasible<<",\"duration_feasible\":"<<s.duration_feasible
       <<",\"old_neutral_after_order\":"<<s.old_neutral<<",\"insertions_after_order\":"<<s.insertions
       <<",\"quantities_after_order\":"<<s.quantities<<",\"exhausted\":"<<s.exhausted<<",\"zero\":"<<s.zero
       <<",\"deadline\":"<<s.deadline<<",\"verification_failed\":"<<s.verification_failed
       <<",\"elapsed_before_summary\":"<<seconds(start,end)<<",\"optimizer_calls\":0}\n";
    out.flush();if(!out)throw std::runtime_error("Summary write failed");return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
