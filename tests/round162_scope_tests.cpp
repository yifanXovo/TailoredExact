#include "Round162PhysicalCompletion.hpp"
#include "Round138Research.hpp"
#include "Round127Research.hpp"
#include "PaperK1AmSf.hpp"
#include "Evaluator.hpp"
#include "Parser.hpp"
#include "FileSha256.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>

using namespace ebrp;
int main(int argc,char** argv){try{
    if(argc!=9)throw std::runtime_error("input T tp td lambda parent paid_Native_C_folder new_output");
    auto in=parseInstanceFile(argv[1],std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]));
    SolveOptions options;configurePaperK1AmSfOverrides(options);options.lambda=std::stod(argv[5]);options.round98_state_service="m-binary";
    round127().mode="ms2";round137Apply(options,"ms2");round138().stock_rlt=true;
    std::ifstream p(argv[6]);int count=0;p>>count;std::vector<RoutePlan> routes;
    for(int k=0;k<count;++k){RoutePlan r;int n=0;p>>r.vehicle>>n;r.nodes.resize(n);for(int& i:r.nodes)p>>i;
        for(int j=1;j+1<n;++j){int delta=0;p>>delta;r.operations.push_back({r.nodes[j],std::max(0,delta),std::max(0,-delta)});}routes.push_back(r);}
    if(!p)throw std::runtime_error("parent read");auto parent=verifySolution(in,routes,options.lambda);if(!parent.feasible)throw std::runtime_error("parent physical");
    std::filesystem::path old(argv[7]),dir(argv[8]);if(!std::filesystem::create_directories(dir))throw std::runtime_error("new output required");
    auto& c=round162();c.enabled=true;c.input_sha=fileSha256(in.path);c.cutoff=std::nextafter(parent.objective,std::numeric_limits<double>::infinity());
    c.root_domain=round162Domain(old/"original.lp");
    for(size_t j=0;j<c.root_domain.names.size();++j)if(c.root_domain.names[j]=="G"){c.lower=c.root_domain.lower_bounds[j];c.upper=c.root_domain.upper_bounds[j];}
    std::filesystem::create_directories(dir/"projection");
    projectRound162Completion(old/"original.lp",old/"source/model.lp",old/"source/lp_duals.jsonl",dir/"projection/model.lp",&c.row);
    c.ready=c.row.active;c.source_sha=fileSha256(old/"source/model.lp");if(!c.ready)throw std::runtime_error("positive NB35 scope qualification needs active row");
    CanonicalCompactModelSpec spec;spec.strengthened=spec.interval_restricted=spec.add_verified_incumbent_row=true;
    spec.gamma_L=0;spec.gamma_U=std::min(.4,c.upper);spec.verified_incumbent=c.cutoff;spec.incumbent_epsilon=0;
    spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    auto child=writeCanonicalCompactModel(in,options,dir/"child.lp",spec);if(!child.written)throw std::runtime_error(child.failure_reason);
    auto with_pc=embedRound162Row(in,child,c.cutoff,dir/"child_pc.lp");if(with_pc.sha256==child.sha256)throw std::runtime_error("covered child did not inherit");
    auto domain=round162Domain(with_pc.path);auto start=mapVerifiedRoutesToCanonicalModel(in,options,routes,"scope_qualification",0,spec.gamma_U,c.cutoff,domain);
    if(!start.complete)throw std::runtime_error(start.failure_reason);const double residual=round162PointResidual(with_pc.path,start.values);
    if(residual>1e-6)throw std::runtime_error("child Start residual");
    auto uncovered=embedRound162Row(in,child,std::nextafter(c.cutoff,std::numeric_limits<double>::infinity()),dir/"uncovered.lp");
    if(uncovered.sha256!=child.sha256)throw std::runtime_error("larger cutoff inherited local row");
    std::ofstream f(dir/"scope_qualification.json");f<<std::setprecision(17)<<"{\"PASS\":true,\"original_integer_Start_residual\":"<<residual
        <<",\"covered_child_inherited\":true,\"larger_cutoff_rejected\":true,\"old_new_hash_differ\":true,\"source_solves\":0,\"Optimize\":0,\"offline_saved_source_only_for_interface_qualification\":true}\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
