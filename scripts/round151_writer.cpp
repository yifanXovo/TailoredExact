// Actual canonical writer and complete physical Start mapping. No Optimize.
#define main round146_unused_qualification_main
#include "round146_writer.cpp"
#undef main
#include "Round151Research.hpp"
static void nonminimal(const Instance& in,const SolverNeutralModelDomain& d,std::vector<double> v,
                       const std::filesystem::path& p,bool inflate_penalty=true){
    double g=0;for(std::size_t j=0;j<d.names.size();++j)if(d.names[j]=="G")g=v[j];
    for(std::size_t j=0;j<d.names.size();++j){const auto& name=d.names[j];
        if(name=="G")v[j]=g+.001;
        else if(name.rfind("state_g_",0)==0){
            const auto suffix=name.substr(8);const auto wanted="state_"+suffix;
            auto hit=std::find(d.names.begin(),d.names.end(),wanted);
            v[j]=(g+.001)*v[std::distance(d.names.begin(),hit)];
        }else if(name.rfind("zprod_",0)==0){
            const auto hit=std::find(d.names.begin(),d.names.end(),"Y_"+name.substr(6));
            v[j]=(g+.001)*v[std::distance(d.names.begin(),hit)];
        }else if(name=="e_1"&&inflate_penalty&&v[j]+.001<=d.upper_bounds[j])v[j]+=.001;
    }
    double S=0,P=0;for(std::size_t j=0;j<d.names.size();++j){const auto& name=d.names[j];
        if(name.rfind("r_",0)==0&&name.size()>2&&std::isdigit(name[2]))S+=v[j];
        else if(name.rfind("e_",0)==0)P+=in.weights.at(std::stoi(name.substr(2)))*v[j];}
    for(std::size_t j=0;j<d.names.size();++j)if(d.names[j]=="W_SP")v[j]=S*P;
    point(p,d,v);
}
int main(int argc,char** argv){try{
    if(argc!=2)throw std::runtime_error("output directory required");
    const std::filesystem::path root(argv[1]);std::filesystem::create_directories(root);int checks=0;
    const auto check=[&](bool ok,const std::string& why){++checks;if(!ok)throw std::runtime_error(why);};
    SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.round98_state_service="m-binary";
    opt.lambda=.15;round127().mode="ms2";round137Apply(opt,"ms2");
    round146().enabled=round149().enabled=round148().enabled=round138().stock_rlt=false;
    for(const std::string tag:{"shortage","fixed","zero_floor"}){
        const auto dir=root/tag;std::filesystem::create_directories(dir);Instance in;in.V=3;in.M=1;
        in.Q={tag=="fixed"?0:tag=="shortage"?1:3};
        in.initial=tag=="fixed"?std::vector<int>{0,2,0,1}:tag=="zero_floor"?std::vector<int>{0,1,1,1}:std::vector<int>{0,1,0,1};
        in.target={0,1,1,1};in.capacity={0,3,3,3};in.weights={0,1,1,1};
        in.dist.assign(4,std::vector<double>(4,0));in.total_time_limit=100;in.pickup_time=in.drop_time=1;
        in.path=(dir/"fixture.txt").string();{std::ofstream f(in.path);f<<tag<<" Round151 fixture\n";}
        round151().mode="off";round151ResetRun();const auto off=model(in,opt,dir/"off.lp",.8);
        const auto disabled=round151_detail::embed(in,off,.8,dir/"must_not_exist.lp");
        check(disabled.sha256==off.sha256&&!round151().generated&&!std::filesystem::exists(dir/"must_not_exist.lp"),"OFF identity");
        round151().mode="conditional";auto on=round151_detail::embed(in,off,.8,dir/"on.lp");
        if(on.path!=dir/"on.lp")std::filesystem::copy_file(on.path,dir/"on.lp");
        check(round151().expected.count(on.sha256)&&round146().expected.empty(),"independent expected");
        check(tag!="zero_floor"||round151().caps.floor.lower==0,"zero global floor");
        check(!round151().expected.at(on.sha256).empty(),"conditional rows including floor0");
        const auto d=domain(on.path);const auto start=mapVerifiedRoutesToCanonicalModel(in,opt,{{0,{0,0},{}}},"own_fixture",0,.8,.8,d);
        check(start.complete,"physical Start:"+start.failure_reason);point(dir/"physical_start.json",d,start.values);
        nonminimal(in,d,start.values,dir/"nonminimal_epigraph.json",tag!="fixed");
        if(tag=="shortage"){
            const auto child=model(in,opt,dir/"child_off.lp",.01);
            const auto sub=round151_detail::embed(in,child,.01,dir/"child_on.lp");
            if(sub.path!=dir/"child_on.lp")std::filesystem::copy_file(sub.path,dir/"child_on.lp");
            check(round141_detail::supports(round141_detail::material(child.path),in.V)!=round151().support,"strict child support");
            auto expanded=off;expanded.gamma_U=.9;bool rejected=false;
            try{round151_detail::embed(in,expanded,.8,dir/"invalid_gamma.lp");}catch(const std::exception&){rejected=true;}
            check(rejected,"gamma expansion rejected");rejected=false;
            try{round151_detail::embed(in,off,.81,dir/"invalid_cutoff.lp");}catch(const std::exception&){rejected=true;}
            check(rejected,"cutoff expansion rejected");
            auto altered=in;altered.target[1]=2;rejected=false;
            try{round151_detail::embed(altered,off,.8,dir/"invalid_ratio.lp");}catch(const std::exception&){rejected=true;}
            check(rejected,"ratio change rejected");
        }
    }
    // Reuse a historical physical witness only for offline validity qualification.
    // It is never injected into a complete experimental arm.
    if(std::filesystem::exists(root/"real_scope.txt")){
        std::ifstream f(root/"real_scope.txt");std::string input,source;double gl,gu,U;int count;
        f>>std::quoted(input)>>std::quoted(source)>>gl>>gu>>U>>count;
        std::vector<RoutePlan> routes(count);
        for(auto& r:routes){int m;f>>r.vehicle>>m;r.nodes.resize(m);for(int& node:r.nodes)f>>node;
            f>>m;r.operations.resize(m);for(auto& op:r.operations)f>>op.station>>op.pickup>>op.drop;}
        check(bool(f),"actual route file");const auto in=parseInstanceFile(input,7200,60,60);
        const auto dir=root/"actual_NB35";std::filesystem::create_directories(dir);
        CanonicalCompactModelArtifact base;base.path=dir/"off.lp";std::filesystem::copy_file(source,base.path);
        base.written=true;base.sha256=fileSha256(base.path);base.gamma_L=gl;base.gamma_U=gu;
        round151ResetRun();round151().mode="conditional";
        const auto on=round151_detail::embed(in,base,U,dir/"on.lp");
        const auto d=domain(on.path);const auto start=mapVerifiedRoutesToCanonicalModel(in,opt,routes,"offline_historical_physical_validity_only",gl,gu,U,d);
        check(start.complete,"actual complete physical Start:"+start.failure_reason);
        point(dir/"physical_start.json",d,start.values);nonminimal(in,d,start.values,dir/"nonminimal_epigraph.json");
    }
    // Directed boundary qualification of the production row function.
    std::vector<std::vector<int>> s{{},{0,1,2},{0,1,2}};
    auto caps=round151_detail::caps(s,{0,1,1},{0,.3,.3},0,2,.4,.4);
    check(caps.floor.lower==0,"boundary floor0");
    check(round151_detail::rows(caps,s,.3,"uniform").empty()&&!round151_detail::rows(caps,s,.3,"conditional").empty(),"child uniform redundant conditional active");
    caps=round151_detail::caps(s,{0,1,1},{0,.3,.3},0,2,.1,.4);
    bool signed_row=false;for(const auto& r:round151_detail::rows(caps,s,.4,"conditional"))
        for(const auto& t:r.coefficients)if(t.first.rfind("state_",0)==0&&t.first.rfind("state_g_",0)!=0&&t.second>0)signed_row=true;
    check(signed_row,"negative cap signed row without instance infeasibility");
    const std::vector<double> tiny{-1e-12,-5e-13,0.,5e-13,1e-12};double last=-1.;
    for(double beta:tiny){const double v=round151_detail::transport(beta);check(v>=beta&&v>=last,"monotone upward tiny transport");last=v;}
    round151_detail::Caps z;z.floor.feasible=true;z.beta0=5e-13;z.states={{1,0,0,0,-5e-13},{1,1,0,0,0},{1,2,0,0,5e-13}};
    const auto zr=round151_detail::rows(z,s,1.,"conditional");
    check(zr.size()==3&&zr[0].coefficients.size()==1&&zr[1].coefficients.size()==1&&zr[2].coefficients.size()==2,"zero and tiny rows transported");
    std::ofstream f(root/"cpp_receipt.json");f<<"{\"PASS\":true,\"checks\":"<<checks<<",\"Optimize\":0,\"Native_load\":0}\n";
    std::cout<<"PASS "<<checks<<" independent writer, Start, child and signed/tiny checks\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
