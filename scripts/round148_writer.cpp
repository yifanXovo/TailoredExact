// Reuse the accepted solver-neutral writer/domain/Start helpers, no Optimize.
#define main round146_qualified_helpers_unused_main
#include "round146_writer.cpp"
#undef main
#include "Round148Research.hpp"
int main(int argc,char** argv){try{
    if(argc!=2)throw std::runtime_error("output directory required");std::filesystem::path root(argv[1]);
    std::filesystem::create_directories(root);SolveOptions opt;configurePaperK1AmSfOverrides(opt);
    opt.round98_state_service="m-binary";opt.lambda=.15;round127().mode="ms2";round137Apply(opt,"ms2");int checks=0;
    const auto check=[&](bool ok,const std::string& why){++checks;if(!ok)throw std::runtime_error(why);};
    for(const std::string tag:{"positive","fixed","zero_lower"}){
        auto dir=root/tag;std::filesystem::create_directories(dir);Instance in;in.V=3;in.M=1;
        in.Q={tag=="fixed"?0:tag=="zero_lower"?3:1};in.initial={0,2,0,1};in.target={0,1,1,1};
        in.capacity={0,3,3,3};in.weights={0,1,1,1};in.dist.assign(4,std::vector<double>(4,0));
        in.total_time_limit=100;in.pickup_time=in.drop_time=1;in.path=(dir/"fixture.txt").string();
        {std::ofstream f(in.path);f<<tag<<" Round148 fixture\n";}
        round146().enabled=true;round146ResetRun();round148().enabled=false;round148ResetRun();
        auto off=model(in,opt,dir/"off.lp");auto gd=round146_detail::embed(in,off,dir/"gd.lp");
        if(gd.path==off.path)std::filesystem::copy_file(off.path,dir/"gd.lp");
        auto unchanged=round148_detail::embed(in,gd,1.5,dir/"should_not_exist.lp");
        check(unchanged.sha256==gd.sha256&&!std::filesystem::exists(dir/"should_not_exist.lp"),"OFF identity");
        auto d=domain(gd.path);auto start=mapVerifiedRoutesToCanonicalModel(in,opt,{{0,{0,0},{}}},"own_fixture",0,.9,1.5,d);
        check(start.complete,"physical Start:"+start.failure_reason);point(dir/"physical_start.json",d,start.values);
        auto epigraph=start.values;for(std::size_t j=0;j<d.names.size();++j){const auto& name=d.names[j];
            if(name=="G")epigraph[j]=.8;else if(name.rfind("state_g_",0)==0)epigraph[j]=epigraph[j]>0?.8:0;
            else if(name.rfind("zprod_",0)==0)epigraph[j]=.8*in.initial[std::stoi(name.substr(6))];}
        point(dir/"nonminimal_epigraph.json",d,epigraph);
        round148().enabled=true;round148().gamma_L=0;round148().gamma_U=.9;round148().cutoff=1.5;
        if(round146().block.applicable){
            std::map<std::string,double> p;for(std::size_t j=0;j<d.names.size();++j)p[d.names[j]]=start.values[j];
            round148().selection=round148_detail::select(round146().block,round146().ratios,p);round148().ready=true;
        }
        auto on=round148_detail::embed(in,gd,1.5,dir/"on.lp");
        if(on.path==gd.path)std::filesystem::copy_file(gd.path,dir/"on.lp");
        check(round146().expected.count(on.sha256)>0,"GD expected SHA migration");
        std::ofstream f(dir/"row.json");f<<std::setprecision(17)<<"{\"rows\":[";
        if(round148().ready)round148_detail::emitRow(f,round148().selection.row);f<<"]}\n";f.close();
        if(tag=="positive"){
            auto child=model(in,opt,dir/"child_off.lp",.01);const auto cs=round141_detail::supports(round141_detail::material(child.path),in.V);
            check(cs!=round146().support,"strict subsupport fixture");
            const auto child_gd=round146_detail::embed(in,child,dir/"child_gd.lp");
            auto sub=round148_detail::embed(in,child_gd,.01,dir/"child_on.lp");
            check(round146().expected.count(sub.sha256)&&round148().expected.count(sub.sha256),"child expected identities");
            auto expanded=gd;expanded.gamma_U=1.;bool rejected=false;
            try{round148_detail::embed(in,expanded,1.5,dir/"invalid_expansion.lp");}catch(const std::exception&){rejected=true;}check(rejected,"expanded gamma rejected");
        }
    }
    std::ofstream f(root/"cpp_receipt.json");f<<"{\"PASS\":true,\"checks\":"<<checks<<",\"Optimize\":0,\"Native_load\":0}\n";
    std::cout<<"PASS "<<checks<<" writer, OFF, expected migration, compatible subset, Start checks\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
