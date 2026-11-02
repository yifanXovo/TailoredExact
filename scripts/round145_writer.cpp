// Actual canonical writer, compact embedding and unchanged complete Start mapper.
#include "Round145Research.hpp"
#include "Round127Research.hpp"
#include "PaperK1AmSf.hpp"
#include "MipStartMapping.hpp"
#include "Parser.hpp"
#include <iostream>
using namespace ebrp;
static SolverNeutralModelDomain domain(const std::filesystem::path& path){
    SolverNeutralModelDomain d;std::ifstream f(path);std::string line,section;
    std::map<std::string,std::pair<double,double>> bounds;std::map<std::string,char> types;
    while(std::getline(f,line)){
        if(line=="Bounds"||line=="Generals"||line=="Binaries"||line=="End"){section=line;continue;}
        if(section=="Bounds"){std::istringstream s(line);std::string name,sign;double l,u;
            if(!(s>>l>>sign>>name>>sign>>u))throw std::runtime_error("finite writer bounds");bounds[name]={l,u};}
        else if(section=="Generals"||section=="Binaries"){std::istringstream s(line);std::string name;while(s>>name)types[name]=section=="Binaries"?'B':'I';}}
    for(const auto& term:bounds){d.names.push_back(term.first);d.lower_bounds.push_back(term.second.first);d.upper_bounds.push_back(term.second.second);d.variable_types.push_back(types.count(term.first)?types[term.first]:'C');}return d;
}
static CanonicalCompactModelArtifact model(const Instance& in,const SolveOptions& options,const std::filesystem::path& path,double lower,double upper,double U){
    CanonicalCompactModelSpec s;s.strengthened=s.interval_restricted=s.add_verified_incumbent_row=true;s.gamma_L=lower;s.gamma_U=upper;s.verified_incumbent=U;
    s.station_state_formulation="vd-p";s.round51_subset_duration_big_m="off";
    auto a=writeCanonicalCompactModel(in,options,path,s);if(!a.written)throw std::runtime_error(a.failure_reason);return a;
}
int main(int argc,char** argv){try{
    if(argc!=4)throw std::runtime_error("output, K35 input, K35 compiled row required");
    std::filesystem::path root(argv[1]);std::filesystem::create_directories(root);int checks=0;
    auto check=[&](bool ok,const std::string& why){++checks;if(!ok)throw std::runtime_error(why);};
    SolveOptions options;configurePaperK1AmSfOverrides(options);options.round98_state_service="m-binary";options.lambda=.15;
    round127().mode="ms2";round137Apply(options,"ms2");round144().enabled=true;
    Instance tiny;tiny.V=3;tiny.M=1;tiny.Q={1};tiny.initial={0,1,0,1};tiny.target={0,1,1,1};tiny.capacity={0,1,1,1};tiny.weights={0,1,1,1};
    tiny.dist.assign(4,std::vector<double>(4,0));tiny.total_time_limit=100;tiny.pickup_time=tiny.drop_time=1;tiny.path=(root/"tiny.txt").string();
    {std::ofstream f(tiny.path);f<<"local exact tiny writer\n";}
    auto base=model(tiny,options,root/"tiny_base.lp",0,.9,1.5);round144_detail::block(tiny,base);round144().cutoff=1.5;round144().ready=true;
    round144().row={"r145_PC",{{"G",-3},{"state_1_0",-1},{"state_2_0",.5},{"state_3_1",-3},{"Y_1",.1},{"state_1_1",-.1}},'<',-1};
    auto compact=round144_detail::embed(tiny,base,1.5,root/"tiny_compact.lp");auto d=domain(compact.path);
    const auto start=mapVerifiedRoutesToCanonicalModel(tiny,options,{{0,{0,0},{}}},"own_physical_fixture",0,.9,1.5,d);
    check(start.complete,"complete physical Start:"+start.failure_reason);
    {std::ofstream f(root/"tiny_start.json");f<<std::setprecision(17)<<'{';for(std::size_t j=0;j<d.names.size();++j){if(j)f<<',';f<<std::quoted(d.names[j])<<':'<<start.values[j];}f<<"}\n";}
    check(std::none_of(d.names.begin(),d.names.end(),[](const std::string& s){return s.rfind("rn_",0)==0;}),"zero extension columns");
    auto child=model(tiny,options,root/"tiny_child_base.lp",0,.8,1.4);round144_detail::embed(tiny,child,1.4,root/"tiny_child_compact.lp");++checks;
    bool rejected=false;try{round144_detail::embed(tiny,base,1.6,root/"invalid_cutoff.lp");}catch(const std::exception&){rejected=true;}check(rejected,"reject larger source scope");
    auto outside=base;outside.gamma_U=1.;rejected=false;try{round144_detail::embed(tiny,outside,1.5,root/"invalid_g.lp");}catch(const std::exception&){rejected=true;}check(rejected,"reject wider g domain");
    auto saved=round144().support;round144().support[1]={0};rejected=false;try{round144_detail::embed(tiny,base,1.5,root/"invalid_support.lp");}catch(const std::exception&){rejected=true;}check(rejected,"reject wider support");round144().support=saved;
    round144ResetRun();auto in=parseInstanceFile(argv[2],10800,60,60);double U=.7674566047247167;
    auto real=model(in,options,root/"K35_off.lp",0,U,U);const auto rn=round144_detail::block(in,real);
    check(rn.applicable,"real positive denominator");round144().cutoff=U;round144().ready=true;
    std::ifstream r(argv[3]);int nz=0;round144().row.name="r145_PC";round144().row.sense='<';r>>round144().row.rhs>>nz;
    for(int k=0;k<nz;++k){std::string name;double a;r>>name>>a;round144().row.coefficients[name]=a;}check(bool(r),"compiled real row input");
    round144_detail::embed(in,real,U,root/"K35_compact.lp");
    std::ofstream f(root/"cpp_receipt.json");f<<"{\"PASS\":true,\"checks\":"<<checks<<",\"Optimize\":0,\"Native_load\":0}\n";
    std::cout<<"PASS "<<checks<<" actual compact writer/Start/scope/off checks\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
