// Actual accepted canonical writer/complete Start helpers; zero Optimize.
#define main round146_qualified_helpers_unused_main
#include "round146_writer.cpp"
#undef main
#include "Round149Research.hpp"
int main(int argc,char** argv){try{
    if(argc!=2)throw std::runtime_error("output directory required");
    std::filesystem::path root(argv[1]);std::filesystem::create_directories(root);
    SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.round98_state_service="m-binary";
    opt.lambda=.15;round127().mode="ms2";round137Apply(opt,"ms2");int checks=0;
    const auto check=[&](bool ok,const std::string& why){++checks;if(!ok)throw std::runtime_error(why);};
    for(const std::string tag:{"shortage","fixed","zero_floor","zero_GD"}){
        const auto dir=root/tag;std::filesystem::create_directories(dir);Instance in;in.V=3;in.M=1;
        in.Q={tag=="fixed"?0:3};
        in.initial=tag=="fixed"?std::vector<int>{0,2,0,1}:tag=="zero_floor"?std::vector<int>{0,1,1,1}:
            tag=="zero_GD"?std::vector<int>{0,0,0,0}:std::vector<int>{0,1,0,1};
        in.target={0,1,1,1};in.capacity={0,3,3,3};in.weights={0,1,1,1};
        in.dist.assign(4,std::vector<double>(4,0));in.total_time_limit=100;in.pickup_time=in.drop_time=1;
        in.path=(dir/"fixture.txt").string();{std::ofstream f(in.path);f<<tag<<" Round149 fixture\n";}
        round146().enabled=true;round146ResetRun();round148().enabled=false;round148ResetRun();
        round149().enabled=false;round149ResetRun();
        const auto off=model(in,opt,dir/"off.lp",.8);
        const auto gd=round146_detail::embed(in,off,dir/"gd.lp");
        if(gd.path==off.path)std::filesystem::copy_file(off.path,dir/"gd.lp");
        const auto disabled=round149_detail::embed(in,gd,.8,dir/"must_not_exist.lp");
        check(disabled.sha256==gd.sha256&&!std::filesystem::exists(dir/"must_not_exist.lp"),"OFF byte identity");
        round149().enabled=true;
        auto on=round149_detail::embed(in,gd,.8,dir/"on.lp");
        if(on.path==gd.path)std::filesystem::copy_file(gd.path,dir/"on.lp");
        check(round146().expected.count(on.sha256)&&round149().expected.count(on.sha256),"expected final SHA");
        check((round149().floor.lower==0)==(tag=="zero_floor"),"positive/zero floor");
        check((round146().block.rows.empty())==(tag=="zero_GD"||tag=="zero_floor"),"zero GD boundary");
        const auto d=domain(on.path);
        auto start=mapVerifiedRoutesToCanonicalModel(in,opt,{{0,{0,0},{}}},"own_fixture",0,.8,.8,d);
        check(start.complete,"physical Start:"+start.failure_reason);point(dir/"physical_start.json",d,start.values);
        double g=0;for(std::size_t j=0;j<d.names.size();++j)if(d.names[j]=="G")g=start.values[j];
        auto epigraph=start.values;
        for(std::size_t j=0;j<d.names.size();++j){const auto& name=d.names[j];
            if(name=="G")epigraph[j]=g+.01;
            else if(name.rfind("state_g_",0)==0){
                const auto parts=round141_detail::split(name,'_');
                epigraph[j]=in.initial.at(std::stoi(parts[2]))==std::stoi(parts[3])?g+.01:0.;
            }else if(name.rfind("zprod_",0)==0)epigraph[j]=(g+.01)*in.initial.at(std::stoi(name.substr(6)));
            else if(name=="e_1")epigraph[j]+=.01;
        }
        point(dir/"nonminimal_epigraph.json",d,epigraph);
        if(tag=="shortage"){
            const auto child=model(in,opt,dir/"child_off.lp",.01);
            check(round141_detail::supports(round141_detail::material(child.path),in.V)!=round149().support,"strict child support");
            const auto child_gd=round146_detail::embed(in,child,dir/"child_gd.lp");
            const auto sub=round149_detail::embed(in,child_gd,.01,dir/"child_on.lp");
            check(round149().expected.at(sub.sha256).empty(),"child old upper dominates frozen beta");
            if(sub.path!=dir/"child_on.lp")std::filesystem::copy_file(sub.path,dir/"child_on.lp");
            auto expanded=gd;expanded.gamma_U=.9;bool rejected=false;
            try{round149_detail::embed(in,expanded,.8,dir/"invalid_gamma.lp");}catch(const std::exception&){rejected=true;}
            check(rejected,"expanded gamma rejected");rejected=false;
            try{round149_detail::embed(in,gd,.81,dir/"invalid_cutoff.lp");}catch(const std::exception&){rejected=true;}
            check(rejected,"relaxed cutoff rejected");
            auto altered=in;altered.target[1]=2;rejected=false;
            try{round149_detail::embed(altered,gd,.8,dir/"invalid_ratio.lp");}catch(const std::exception&){rejected=true;}
            check(rejected,"changed ratio rejected");
            check(round149_detail::rows(round149().support,1e-13,.8).empty(),"tiny beta whole row omitted");
        }
    }
    std::ofstream f(root/"cpp_receipt.json");f<<"{\"PASS\":true,\"checks\":"<<checks<<",\"Optimize\":0,\"Native_load\":0}\n";
    std::cout<<"PASS "<<checks<<" writer, floor, OFF, child, zero-GD and complete/nonminimal Start checks\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
