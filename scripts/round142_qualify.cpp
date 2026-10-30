// New-risk writer qualification only. No Native load or Optimize.
#include "Round141Research.hpp"
#include "Round127Research.hpp"
#include "Round138Research.hpp"
#include "PaperK1AmSf.hpp"
#include <iostream>
using namespace ebrp;
int main(int argc,char** argv){try {
    if(argc!=2)throw std::runtime_error("output directory required");
    const std::filesystem::path root(argv[1]);std::filesystem::create_directories(root);
    round141_detail::require(!round142().enabled(),"r142_default_off");
    Instance in;in.V=4;in.M=1;in.Q={2};in.initial={0,2,1,1,0};in.target={0,1,1,1,1};
    in.capacity={0,2,2,2,2};in.weights={0,.25,.25,.25,.25};
    in.dist.assign(5,std::vector<double>(5,0));in.total_time_limit=100;in.pickup_time=in.drop_time=1;
    SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.round98_state_service="m-binary";opt.lambda=.15;
    round127().mode="ms2";round138().stock_rlt=true;round140().set("tc2");round137Apply(opt,"ms2");
    for(const auto& domain:std::vector<std::pair<double,double>>{{.125,.75},{.125,.125},{std::ldexp(1.,-50),std::ldexp(1.,-48)}}) {
        std::string tag=domain.first==domain.second?"fixed":domain.first==.125?"positive":"tiny";
        auto dir=root/tag;std::filesystem::create_directories(dir);
        CanonicalCompactModelSpec spec;spec.strengthened=spec.interval_restricted=spec.add_verified_incumbent_row=true;
        spec.gamma_L=domain.first;spec.gamma_U=domain.second;spec.verified_incumbent=.9;
        spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
        auto parent=writeCanonicalCompactModel(in,opt,dir/"parent.lp",spec);
        auto& state=round141();state.mode="d1";state.root_artifact=parent;
        auto& c=state.choice;c.ratios={0,1,1,1,1};c.support=round141_detail::supports(round141_detail::material(parent.path),4);
        const auto grid=round141_detail::grid(c.support,c.ratios,2,4);c.exponent=grid.exponent;
        c.threshold=round140_detail::units(1.,c.exponent);
        auto selected=std::find_if(grid.rows.begin(),grid.rows.end(),[&](const auto& r){return r.t==c.threshold;});
        round141_detail::require(selected!=grid.rows.end()&&selected->ell<selected->u,"fixture_count_domain");
        c.ell=selected->ell;c.u=selected->u;c.pivot=(c.ell+c.u)/2;c.a=spec.gamma_L;c.z=spec.gamma_U;
        for(const auto& mode:{"off","selected","all"})for(int side=0;side<2;++side) {
            round142().set(mode);const auto artifact=round141Probe(in,side,dir/(std::string(mode)+"_"+std::to_string(side)+".lp"));
            const auto& rows=state.expected.at(artifact.sha256);
            round141_detail::require(rows.size()==(std::string(mode)=="off"?2:std::string(mode)=="selected"?7:rows.size()),"combined_expected_rows");
            std::ofstream f(artifact.path.string()+".expected.json");
            f<<std::setprecision(17)<<"{\"model_SHA\":"<<std::quoted(artifact.sha256)<<",\"mode\":"<<std::quoted(mode)
                <<",\"side\":"<<side<<",\"alpha\":"<<c.a<<",\"beta\":"<<c.z
                <<",\"threshold\":\"1\",\"ell\":"<<c.ell<<",\"u\":"<<c.u<<",\"pivot\":"<<c.pivot<<",\"rows\":[";
            bool first=true;for(const auto& r:rows){if(!first)f<<',';first=false;
                f<<"{\"name\":"<<std::quoted(r.name)<<",\"sense\":"<<std::quoted(std::string(1,r.sense))<<",\"rhs\":"<<r.rhs<<",\"terms\":{";
                bool term_first=true;for(const auto& t:r.coefficients){if(!term_first)f<<',';term_first=false;f<<std::quoted(t.first)<<':'<<t.second;}f<<"}}";
            }f<<"]}\n";f.close();round141_detail::require(bool(f),"expected_fixture_write");
        }
    }
    std::cout<<"PASS off/selected/all source writer, positive/fixed/tiny g; Optimize=0\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
