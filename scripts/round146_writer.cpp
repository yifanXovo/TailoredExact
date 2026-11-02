// Actual canonical writer and complete physical Start mapper; no Optimize.
#include "Round146Research.hpp"
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
static void point(const std::filesystem::path& path,const SolverNeutralModelDomain& d,const std::vector<double>& values){
    std::ofstream f(path);f<<std::setprecision(17)<<'{';for(std::size_t j=0;j<d.names.size();++j){if(j)f<<',';f<<std::quoted(d.names[j])<<':'<<values[j];}f<<"}\n";
}
static CanonicalCompactModelArtifact model(const Instance& in,const SolveOptions& opt,const std::filesystem::path& path,double U=1.5){
    CanonicalCompactModelSpec spec;spec.strengthened=spec.interval_restricted=spec.add_verified_incumbent_row=true;
    spec.gamma_L=0;spec.gamma_U=std::min(.9,U);spec.verified_incumbent=U;spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    auto a=writeCanonicalCompactModel(in,opt,path,spec);if(!a.written)throw std::runtime_error(a.failure_reason);return a;
}
int main(int argc,char** argv){try{
    if(argc!=3)throw std::runtime_error("output directory and K35 input required");std::filesystem::path root(argv[1]);std::filesystem::create_directories(root);
    SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.round98_state_service="m-binary";opt.lambda=.15;round127().mode="ms2";round137Apply(opt,"ms2");int checks=0;
    auto check=[&](bool ok,const std::string& why){++checks;if(!ok)throw std::runtime_error(why);};
    for(const std::string tag:{"positive","fixed","zero_lower"}){
        auto dir=root/tag;std::filesystem::create_directories(dir);Instance in;in.V=3;in.M=1;in.Q={tag=="fixed"?0:tag=="zero_lower"?3:1};
        in.initial={0,2,0,1};in.target={0,1,1,1};in.capacity={0,3,3,3};in.weights={0,1,1,1};
        in.dist.assign(4,std::vector<double>(4,0));in.total_time_limit=100;in.pickup_time=in.drop_time=1;
        in.path=(dir/"fixture.txt").string();{std::ofstream f(in.path);f<<tag<<" GD fixture\n";}
        round146().enabled=false;round146ResetRun();auto off=model(in,opt,dir/"off.lp");
        auto unchanged=round146_detail::embed(in,off,dir/"should_not_exist.lp");check(unchanged.sha256==off.sha256&&!std::filesystem::exists(dir/"should_not_exist.lp"),"default off identity");
        round146().enabled=true;auto on=round146_detail::embed(in,off,dir/"on.lp");
        check(round146().block.applicable==(tag!="zero_lower"),"zero-domain convention");
        if(on.path==off.path)std::filesystem::copy_file(off.path,dir/"on.lp");
        auto d=domain(on.path);auto start=mapVerifiedRoutesToCanonicalModel(in,opt,{{0,{0,0},{}}},"own_physical_fixture",0,.9,1.5,d);
        check(start.complete,"complete physical Start:"+start.failure_reason);point(dir/"physical_start.json",d,start.values);
        auto epigraph=start.values;
        for(std::size_t j=0;j<d.names.size();++j){const auto& name=d.names[j];
            if(name=="G")epigraph[j]=.8;else if(name.rfind("state_g_",0)==0)epigraph[j]=epigraph[j]>0?.8:0;
            else if(name.rfind("zprod_",0)==0)epigraph[j]=.8*in.initial[std::stoi(name.substr(6))];}
        point(dir/"nonminimal_epigraph.json",d,epigraph);
        if(tag=="positive"){
            auto child=model(in,opt,dir/"child_off.lp",.01);const auto cs=round141_detail::supports(round141_detail::material(child.path),in.V);
            check(cs!=round146().support,"strict canonical subsupport fixture");
            auto sub=round146_detail::embed(in,child,dir/"child_on.lp");
            for(const auto& row:round146().expected.at(sub.sha256))for(const auto& term:row.coefficients)if(term.first!="G")
                check(round146().block.rows[row.name=="r146_GD_low"?0:1].coefficients.at(term.first)==term.second,"inherited coefficient identity");
            auto altered=in;altered.target[1]=2;bool rejected=false;
            try{round146_detail::embed(altered,off,dir/"invalid_ratio.lp");}catch(const std::exception&){rejected=true;}check(rejected,"changed actual ratio rejected");
            altered=in;altered.Q[0]=2;rejected=false;
            try{round146_detail::embed(altered,off,dir/"invalid_inventory.lp");}catch(const std::exception&){rejected=true;}check(rejected,"changed inventory scope rejected");
            {std::ofstream f(in.path,std::ios::app);f<<"changed input\n";}rejected=false;
            try{round146_detail::embed(in,off,dir/"invalid_input.lp");}catch(const std::exception&){rejected=true;}check(rejected,"changed input hash rejected");
            round146ResetRun();round146_detail::embed(in,child,dir/"child_as_root.lp");rejected=false;
            try{round146_detail::embed(in,off,dir/"invalid_expansion.lp");}catch(const std::exception&){rejected=true;}check(rejected,"expanded support rejected");
        }
    }
    const auto in=parseInstanceFile(argv[2],10800,60,60);auto dir=root/"K35";std::filesystem::create_directories(dir);
    round146ResetRun();auto off=model(in,opt,dir/"off.lp",.7674566047247167);round146_detail::embed(in,off,dir/"on.lp");
    std::ofstream f(root/"cpp_receipt.json");f<<"{\"PASS\":true,\"checks\":"<<checks<<",\"Optimize\":0,\"Native_load\":0}\n";
    std::cout<<"PASS "<<checks<<" canonical writer, Start and scope checks\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
