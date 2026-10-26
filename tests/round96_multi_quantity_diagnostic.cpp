#include "Round96MultiQuantity.hpp"
#include "Round95FullBlockDescent.hpp"
#include "Round60Candidates.hpp"
#include "Round61Candidates.hpp"
#include "Parser.hpp"
#include "FileSha256.hpp"
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>

int main(int argc,char** argv) {try {
    const auto start=std::chrono::steady_clock::now();
    if(argc!=8)throw std::invalid_argument("input route_text T pickup drop lambda output_dir");
    const auto in=ebrp::parseInstanceFile(argv[1],std::stod(argv[3]),std::stod(argv[4]),std::stod(argv[5]));
    ebrp::SolveOptions options;options.lambda=std::stod(argv[6]);
    std::ifstream file(argv[2]);int count=0;file>>count;
    if(count!=in.M)throw std::invalid_argument("route count");
    std::vector<ebrp::RoutePlan> routes;
    for(int k=0;k<count;++k) {
        int vehicle,n;file>>vehicle>>n;
        if(!file||n<0||n>in.V)throw std::invalid_argument("route text header");
        ebrp::RoutePlan r;r.vehicle=vehicle;r.nodes={0};
        for(int j=0;j<n;++j) {
            int i,p,d;file>>i>>p>>d;if(!file)throw std::invalid_argument("route text operation");
            r.nodes.push_back(i);r.operations.push_back({i,p,d});
        }
        r.nodes.push_back(0);routes.push_back(std::move(r));
    }
    const auto initial=ebrp::verifyRound95StartingWitness(in,routes,options.lambda);
    const std::filesystem::path dest(argv[7]);
    if(std::filesystem::exists(dest))throw std::invalid_argument("output exists");
    std::filesystem::create_directories(dest);
    auto save=[&](const char* name,const std::vector<ebrp::RoutePlan>& r) {
        ebrp::VerifiedCandidateStore store;
        if(!store.consider(in,options.lambda,r,"round96_quantity_diagnostic","original_problem"))
            throw std::runtime_error("witness publication failed");
        ebrp::writeRound61Witness(dest/name,in,options.lambda,store.best());
    };
    const auto begin_direct=std::chrono::steady_clock::now();
    const auto direct=ebrp::runRound96MultiQuantity(in,options,routes);
    const auto begin_pair=std::chrono::steady_clock::now();
    save("direct.json",direct.routes);
    const auto pair=ebrp::runRound95FullBlockDescent(in,options,routes);
    const auto begin_after=std::chrono::steady_clock::now();
    save("pair.json",pair.routes);
    const auto after=ebrp::runRound96MultiQuantity(in,options,pair.routes);
    const auto end=std::chrono::steady_clock::now();save("after_pair.json",after.routes);
    auto seconds=[](auto a,auto b){return std::chrono::duration<double>(b-a).count();};
    std::ofstream out(dest/"summary.json");out<<std::setprecision(17);
    out<<"{\"input_sha256\":\""<<ebrp::fileSha256(argv[1])<<"\",\"route_sha256\":\""<<ebrp::fileSha256(argv[2])
       <<"\",\"initial_F\":"<<initial.objective<<",\"pair_F\":"<<pair.verification.objective
       <<",\"pair_accepted\":"<<pair.stats.accepted<<",\"pair_exhausted\":"<<pair.stats.exhausted
       <<",\"pair_points\":"<<pair.stats.evaluator_points<<",\"pair_seconds\":"<<seconds(begin_pair,begin_after);
    auto result=[&](const char* name,const ebrp::Round96MultiResult& r,double sec) {
        out<<",\""<<name<<"\":{\"F\":"<<r.verification.objective<<",\"passes\":"<<r.stats.passes
           <<",\"directions\":"<<r.stats.directions<<",\"points\":"<<r.stats.points
           <<",\"physical\":"<<r.stats.physical<<",\"accepted\":"<<r.stats.accepted
           <<",\"exhausted\":"<<r.stats.exhausted<<",\"seconds\":"<<sec<<",\"inventories\":[";
        bool first=true;
        for(const auto& v:r.accepted_inventories){if(!first)out<<',';first=false;out<<'[';for(std::size_t i=0;i<v.size();++i){if(i)out<<',';out<<v[i];}out<<']';}
        out<<"]}";
    };
    result("direct",direct,seconds(begin_direct,begin_pair));result("after_pair",after,seconds(begin_after,end));
    out<<",\"elapsed_before_summary\":"<<seconds(start,end)<<",\"optimizer_calls\":0}\n";
    out.flush();if(!out)throw std::runtime_error("summary write");
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
