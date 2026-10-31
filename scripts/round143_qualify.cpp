// Actual writer and complete Start mapper, without loading a solver.
#include "Round143Research.hpp"
#include "Round127Research.hpp"
#include "PaperK1AmSf.hpp"
#include "CanonicalCompactModel.hpp"
#include "MipStartMapping.hpp"
#include "Parser.hpp"
#include <fstream>
#include <iostream>
using namespace ebrp;
static SolverNeutralModelDomain domain(const std::filesystem::path& path) {
    SolverNeutralModelDomain d;std::ifstream f(path);std::string line,section;
    std::map<std::string,std::pair<double,double>> bounds;std::map<std::string,char> types;
    while(std::getline(f,line)) {
        if(line=="Bounds"||line=="Generals"||line=="Binaries"||line=="End"){section=line;continue;}
        if(section=="Bounds") {
            std::istringstream s(line);std::string name,sign;double l,u;
            if(!(s>>l>>sign>>name>>sign>>u))throw std::runtime_error("finite qualifier bounds");bounds[name]={l,u};
        } else if(section=="Generals"||section=="Binaries") {
            std::istringstream s(line);std::string name;while(s>>name)types[name]=section=="Binaries"?'B':'I';
        }
    }
    for(const auto& [name,b]:bounds){d.names.push_back(name);d.lower_bounds.push_back(b.first);d.upper_bounds.push_back(b.second);d.variable_types.push_back(types.count(name)?types[name]:'C');}return d;
}
static void point(const std::filesystem::path& path,const SolverNeutralModelDomain& d,const std::vector<double>& values) {
    std::ofstream f(path);f<<std::setprecision(17)<<'{';for(std::size_t j=0;j<d.names.size();++j){if(j)f<<',';f<<std::quoted(d.names[j])<<':'<<values[j];}f<<"}\n";
}
static CanonicalCompactModelArtifact model(const Instance& in,SolveOptions& opt,const std::filesystem::path& path,double a=0,double b=.9,double cutoff=1.5) {
    CanonicalCompactModelSpec spec;spec.strengthened=spec.interval_restricted=spec.add_verified_incumbent_row=true;
    spec.gamma_L=a;spec.gamma_U=b;spec.verified_incumbent=cutoff;spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    auto m=writeCanonicalCompactModel(in,opt,path,spec);if(!m.written)throw std::runtime_error(m.failure_reason);return m;
}
int main(int argc,char** argv){try {
    if(argc!=3)throw std::runtime_error("output-directory and K35-input required");
    std::filesystem::path root(argv[1]);std::filesystem::create_directories(root);
    SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.round98_state_service="m-binary";opt.lambda=.15;
    round127().mode="ms2";round137Apply(opt,"ms2");int checks=0;
    auto check=[&](bool v,const std::string& why){++checks;if(!v)throw std::runtime_error(why);};
    for(const std::string tag:{"positive","fixed","zero_lower"}) {
        auto dir=root/tag;std::filesystem::create_directories(dir);
        Instance in;in.V=3;in.M=1;in.Q={tag=="fixed"?0:tag=="zero_lower"?3:1};
        in.initial={0,2,0,1};in.target={0,1,1,1};in.capacity={0,3,3,3};in.weights={0,1,1,1};
        in.dist.assign(4,std::vector<double>(4,0));in.total_time_limit=100;in.pickup_time=in.drop_time=1;
        in.path=(dir/"fixture.txt").string();{std::ofstream f(in.path);f<<tag<<" RN fixture\n";}
        for(bool enabled:{false,true}) {
            round143().rn=enabled;const std::string mode=enabled?"on":"off";
            auto a=model(in,opt,dir/(mode+".lp"));auto d=domain(a.path);
            auto start=mapVerifiedRoutesToCanonicalModel(in,opt,{{0,{0,0},{}}},"own_physical_fixture",0,.9,1.5,d);
            check(start.complete,"complete Start "+tag+mode+":"+start.failure_reason);
            point(dir/(mode+"_start.json"),d,start.values);
            bool rn=std::find(d.names.begin(),d.names.end(),"rn_t")!=d.names.end();
            check(rn==(enabled&&tag!="zero_lower"),"positive-domain applicability");
            auto bad=mapVerifiedRoutesToCanonicalModel(in,opt,{{0,{0,0},{}}},"physical_outside_g_domain",.7,.9,1.5,d);
            check(!bad.complete&&bad.failure_reason=="verified_start_outside_static_gini_interval","physical G-domain rejection");
            if(enabled&&rn) {
                auto epigraph=start.values;
                for(std::size_t j=0;j<d.names.size();++j) {
                    const auto& name=d.names[j];
                    if(name=="G")epigraph[j]=.8;
                    else if(name.rfind("state_g_",0)==0)epigraph[j]=epigraph[j]>0?.8:0;
                    else if(name.rfind("zprod_",0)==0)epigraph[j]=.8*in.initial[std::stoi(name.substr(6))];
                }
                point(dir/"nonminimal_epigraph.json",d,epigraph);
            }
        }
    }
    // Heterogeneous actual real writer: root off must match the inherited matrix.
    auto in=parseInstanceFile(argv[2],10800,60,60);opt.lambda=.15;
    for(bool enabled:{false,true}) {
        round143().rn=enabled;std::string mode=enabled?"on":"off";
        auto dir=root/"K35";std::filesystem::create_directories(dir);
        model(in,opt,dir/(mode+".lp"),0,.7674566047247167,.7674566047247167);
    }
    std::ofstream f(root/"cpp_receipt.json");f<<"{\"PASS\":true,\"checks\":"<<checks<<",\"Optimize\":0,\"Native_load\":0}\n";
    std::cout<<"PASS "<<checks<<" RN writer/complete-Start checks\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
