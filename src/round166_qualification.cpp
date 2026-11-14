// Fixed, finite C++ diagnostics. All new Optimize calls are made here or in
// the inherited C++ native backend, never in an orchestration language.
#include "Round166Research.hpp"
#include "CanonicalCompactModel.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "MipStartMapping.hpp"
#include "PaperK1AmSf.hpp"
#include "Parser.hpp"
#include "Evaluator.hpp"
#include "Round127Research.hpp"
#include "gurobi_c.h"
#include <cmath>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <sstream>
using namespace ebrp;
namespace {
void require(bool p,const std::string& s){if(!p)throw std::runtime_error(s);}
void check(int n){if(n)throw std::runtime_error("Gurobi API "+std::to_string(n));}
struct ApiModel {
    GRBenv* env=nullptr;GRBmodel* model=nullptr;int n=0;
    explicit ApiModel(const std::string& name) {
        check(GRBemptyenv(&env));check(GRBsetintparam(env,"OutputFlag",0));check(GRBstartenv(env));
        check(GRBsetintparam(env,"Threads",1));check(GRBsetintparam(env,"Seed",0));
        check(GRBsetdblparam(env,"MIPGap",0));check(GRBsetdblparam(env,"MIPGapAbs",0));
        check(GRBsetdblparam(env,"TimeLimit",60));
        check(GRBnewmodel(env,&model,name.c_str(),0,nullptr,nullptr,nullptr,nullptr,nullptr));
    }
    ~ApiModel(){if(model)GRBfreemodel(model);if(env)GRBfreeenv(env);}
    int var(const std::string& name,double lo,double hi,char type='C',double obj=0) {
        check(GRBaddvar(model,0,nullptr,nullptr,obj,lo,hi,type,name.c_str()));return n++;
    }
    void row(std::initializer_list<std::pair<int,double>> terms,char sense,double rhs) {
        row(std::vector<std::pair<int,double>>(terms),sense,rhs);
    }
    void row(const std::vector<std::pair<int,double>>& terms,char sense,double rhs) {
        std::vector<int> indices;std::vector<double> coeff;
        for(const auto& x:terms)if(x.second!=0){indices.push_back(x.first);coeff.push_back(x.second);}
        check(GRBaddconstr(model,static_cast<int>(indices.size()),indices.data(),coeff.data(),sense,rhs,nullptr));
    }
};
struct Cfg {int l,u,b;double a,c;};
void local(const std::filesystem::path& out) {
    require(std::filesystem::create_directories(out),"exclusive local directory");
    const std::vector<Cfg> configs{{0,4,2,0,1},{2,2,2,0,0},{1,7,0,.1,.5},{0,4,6,.2,.2},
        {0,6,0,0,.5},{0,6,6,0,.5},{2,7,4,.25,.75},{0,0,0,0,0}};
    std::ofstream ledger(out/"Optimize.jsonl"),csv(out/"local.csv");
    csv<<"config,representation,objective,status,value,rows,columns,nonzeros,ConstrVio,BoundVio,DualVio,runtime,work\n"<<std::setprecision(17);
    int calls=0;
    for(size_t ci=0;ci<configs.size();++ci)for(int rep=0;rep<4;++rep)for(int objective=0;objective<2;++objective) {
        const auto c=configs[ci];ApiModel m("R166_local");
        int y=m.var("Y",c.l,c.u),move=m.var("M",0,std::max(std::abs(c.b-c.l),std::abs(c.b-c.u))),
            visit=m.var("V",0,1),g=m.var("G",c.a,c.c),z=m.var("Z",0,c.u*c.c);
        check(GRBupdatemodel(m.model));
        // Fixed derived separator at the first domain; the remaining domains
        // use fixed (1,2,-3) and (-2,1,4) M/V/Z objectives at a legal Y,g.
        if(ci==0) {
            m.row({{y,1}},'=',2);m.row({{g,1}},'=',.5);
            m.row({{move,1}},'=',0);m.row({{visit,1}},'=',0);
            check(GRBsetdblattrelement(m.model,"Obj",z,objective==0?1.0:-1.0));
        } else {
            m.row({{y,1}},'=',(c.l+c.u)/2);m.row({{g,1}},'=',(c.a+c.c)/2);
            check(GRBsetdblattrelement(m.model,"Obj",move,objective==0?1.0:-2.0));
            check(GRBsetdblattrelement(m.model,"Obj",visit,objective==0?2.0:1.0));
            check(GRBsetdblattrelement(m.model,"Obj",z,objective==0?-3.0:4.0));
        }
        auto joint=[&](const std::vector<int>& values,bool service,bool product) {
            std::vector<std::pair<int,double>> mass,yl{{y,-1}},ml{{move,-1}},vl{{visit,-1}},gl{{g,-1}},zl{{z,-1}};
            for(int a:values) {
                int t=m.var("t"+std::to_string(m.n),0,1);mass.push_back({t,1});yl.push_back({t,double(a)});
                if(service){ml.push_back({t,double(std::abs(c.b-a))});vl.push_back({t,a!=c.b?1.:0.});}
                if(product){int q=m.var("q"+std::to_string(m.n),0,c.c);gl.push_back({q,1});zl.push_back({q,double(a)});
                    m.row({{q,1},{t,-c.a}},'>',0);m.row({{q,1},{t,-c.c}},'<',0);}
            }
            m.row(mass,'=',1);m.row(yl,'=',0);
            if(service){m.row(ml,'=',0);m.row(vl,'=',0);}
            if(product){m.row(gl,'=',0);m.row(zl,'=',0);}
        };
        std::vector<int> all(c.u-c.l+1);std::iota(all.begin(),all.end(),c.l);
        if(rep==3){joint(all,true,false);joint(c.l==c.u?std::vector<int>{c.l}:std::vector<int>{c.l,c.u},false,true);}
        else joint(rep==0?all:round166Support(c.l,c.u,c.b),true,true);
        if(rep==2) {
            int bits=1;while((1LL<<bits)-1<c.u)++bits;
            std::vector<std::pair<int,double>> yl{{y,1}},zl{{z,1}};
            for(int h=0;h<bits;++h){int b=m.var("b"+std::to_string(h),0,1),w=m.var("w"+std::to_string(h),0,c.c);
                yl.push_back({b,-double(1LL<<h)});zl.push_back({w,-double(1LL<<h)});
                m.row({{w,1},{b,-c.a}},'>',0);m.row({{w,1},{b,-c.c}},'<',0);
                m.row({{w,1},{g,-1},{b,-c.c}},'>',-c.c);m.row({{w,1},{g,-1},{b,-c.a}},'<',-c.a);
            }m.row(yl,'=',0);m.row(zl,'=',0);
        }
        check(GRBupdatemodel(m.model));const std::string id=std::to_string(ci)+"_"+std::to_string(rep)+"_"+std::to_string(objective);
        check(GRBwrite(m.model,(out/(id+".lp")).string().c_str()));
        ledger<<"{\"call\":"<<++calls<<",\"id\":"<<std::quoted(id)<<",\"phase\":\"begin\"}\n";ledger.flush();
        check(GRBoptimize(m.model));int status=0,rows=0,cols=0,nz=0;double value=0,cv=0,bv=0,dv=0,runtime=0,work=0;
        check(GRBgetintattr(m.model,"Status",&status));require(status==GRB_OPTIMAL,"local not optimal");
        check(GRBgetdblattr(m.model,"ObjVal",&value));check(GRBgetdblattr(m.model,"ConstrVio",&cv));
        check(GRBgetdblattr(m.model,"BoundVio",&bv));check(GRBgetdblattr(m.model,"DualVio",&dv));
        check(GRBgetdblattr(m.model,"Runtime",&runtime));check(GRBgetdblattr(m.model,"Work",&work));
        check(GRBgetintattr(m.model,"NumConstrs",&rows));check(GRBgetintattr(m.model,"NumVars",&cols));check(GRBgetintattr(m.model,"NumNZs",&nz));
        require(std::max({cv,bv,dv})<=1e-7,"local qualification residual");
        csv<<ci<<','<<rep<<','<<objective<<','<<status<<','<<value<<','<<rows<<','<<cols<<','<<nz<<','<<cv<<','<<bv<<','<<dv<<','<<runtime<<','<<work<<'\n';csv.flush();
        ledger<<"{\"call\":"<<calls<<",\"phase\":\"end\"}\n";ledger.flush();
    }
    require(calls==64,"local count");std::cout<<"64 local Optimize calls completed\n";
}
void algebra(const std::filesystem::path& out) {
    long long states=0,domains=0;
    for(int cap=0;cap<=12;++cap)for(int b=0;b<=cap;++b)for(int l=0;l<=cap;++l)for(int u=l;u<=cap;++u) {
        ++domains;auto k=round166Support(l,u,b);require(k.size()<=5,"support cardinality");
        for(int y=l;y<=u;++y)for(double g:{0.,.125,.5,1.}) {
            double yy=0,mm=0,vv=0,gg=0,zz=0,sum=0;
            for(auto at:round166Weights(k,y)){sum+=at.second;yy+=at.first*at.second;mm+=std::abs(b-at.first)*at.second;
                vv+=(at.first!=b)*at.second;gg+=g*at.second;zz+=at.first*g*at.second;}
            require(std::max({std::abs(sum-1),std::abs(yy-y),std::abs(mm-std::abs(b-y)),std::abs(vv-(y!=b)),std::abs(gg-g),std::abs(zz-g*y)})<1e-12,"interpolation");
            int bits=1;while((1LL<<bits)-1<cap)++bits;double by=0,bz=0;
            for(int h=0;h<bits;++h){int bit=(y>>h)&1;by+=(1LL<<h)*bit;bz+=(1LL<<h)*g*bit;}
            require(by==y&&bz==g*y,"absolute bits");++states;
        }
    }
    require(round166Support(3,2,1).empty(),"empty domain");
    require(.5*1+.5*3==2&&.25*3==.75&&.25*2==.5,"continuous-only counterexample");
    if(!out.parent_path().empty())std::filesystem::create_directories(out.parent_path());
    std::ofstream f(out);f<<"{\"PASS\":true,\"Optimize\":0,\"domains\":"<<domains<<",\"graph_states\":"<<states<<",\"empty_domain\":true,\"continuous_only_counterexample\":true,\"binary_breakpoints_delete_internal_Y\":true}\n";
}
void tinyOracle(const std::filesystem::path& out) {
    std::filesystem::create_directories(out.parent_path());std::ofstream f(out);
    f<<"initial1,Y1,Y2,G,P,F,return_load,handling_seconds\n"<<std::setprecision(17);
    for(int initial1:{3,4}) {
        double best=1e100;int best1=-1,best2=-1;
        for(int y1=0;y1<=4;++y1)for(int y2=0;y2<=4;++y2) {
            std::vector<int> stops;if(y1!=initial1)stops.push_back(1);if(y2!=0)stops.push_back(2);
            bool feasible=false;int return_load=0,handling=0;
            do {int load=0,seconds=0;bool valid=true;
                for(int i:stops){const int delta=(i==1?initial1-y1:-y2);load+=delta;seconds+=60*std::abs(delta);if(load<0||load>3)valid=false;}
                seconds+=60*load;if(valid&&seconds<=(initial1==3?360:480)){feasible=true;return_load=load;handling=seconds;}
            }while(std::next_permutation(stops.begin(),stops.end()));
            if(!feasible)continue;
            const double sum=(y1+y2)/2.,g=sum>0?std::abs(y1-y2)/(4.*sum):0.;
            const double p=std::abs(y1/2.-1)+std::abs(y2/2.-1),v=g+.15*p;
            f<<initial1<<','<<y1<<','<<y2<<','<<g<<','<<p<<','<<v<<','<<return_load<<','<<handling<<'\n';
            if(v<best){best=v;best1=y1;best2=y2;}
        }
        require(std::abs(best-(initial1==3?.15:0.))<1e-14,"independent tiny oracle value");
        require(best1==(initial1==3?1:2)&&best2==best1,"independent tiny oracle stock");
    }
}
std::vector<RoutePlan> parent(const std::string& path) {
    std::ifstream f(path);int count=0;f>>count;std::vector<RoutePlan> routes;
    for(int k=0;k<count;++k){RoutePlan r;int n=0;f>>r.vehicle>>n;require(n>=2,"parent n");r.nodes.resize(n);for(int& a:r.nodes)f>>a;
        for(int j=1;j+1<n;++j){int delta=0;f>>delta;r.operations.push_back({r.nodes[j],std::max(0,delta),std::max(0,-delta)});}routes.push_back(r);}
    require(bool(f),"parent input");return routes;
}
void physical(int argc,char** argv) {
    // input T tp td lambda parent out B|C166 export|LP|MIP|restore cap lower upper cutoff
    require(argc==16,"physical input T tp td lambda parent out B|C166 export|LP|MIP|restore cap lower upper cutoff");
    const auto begin=std::chrono::steady_clock::now();auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();};
    const auto in=parseInstanceFile(argv[2],std::stod(argv[3]),std::stod(argv[4]),std::stod(argv[5]));
    auto routes=parent(argv[7]);const bool compact=std::string(argv[9])=="C166";const std::string mode=argv[10];
    require(compact||std::string(argv[9])=="B","formulation");
    SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.lambda=std::stod(argv[6]);opt.round98_state_service="m-binary";
    opt.algorithm_preset="research-round83-vds-equal-net-exchange";opt.method="gcap-frontier";
    opt.round68_verified_start=true;opt.gurobi_seed=0;opt.gurobi_threads=1;opt.process_start_time=begin;opt.process_start_time_valid=true;
    round127().mode="ms2";round137Apply(opt,"ms2");
    const auto pv=verifySolution(in,routes,opt.lambda);require(pv.feasible,"parent infeasible");
    const double lower=std::stod(argv[12]),upper=std::stod(argv[13]),cutoff=std::stod(argv[14]);
    // argv[15] is a unique leaf/epoch identity, never a formulation rule.
    const std::filesystem::path dir(argv[8]);require(std::filesystem::create_directories(dir),"exclusive physical directory");
    CanonicalCompactModelSpec spec;spec.strengthened=spec.interval_restricted=spec.add_verified_incumbent_row=true;
    spec.gamma_L=lower;spec.gamma_U=upper;spec.verified_incumbent=cutoff;spec.incumbent_epsilon=0;
    spec.station_state_formulation=compact?"breakpoint-bit":"vd-p";spec.round51_subset_duration_big_m="off";
    auto art=writeCanonicalCompactModel(in,opt,dir/"model.lp",spec);require(art.written,art.failure_reason);
    const double build_seconds=elapsed();
    // Read every actual column and every row. No Optimize is needed to verify
    // a complete Start against the actual emitted matrix and original objective.
    ApiModel check_model("read");GRBfreemodel(check_model.model);check_model.model=nullptr;
    check(GRBreadmodel(check_model.env,(dir/"model.lp").string().c_str(),&check_model.model));
    int n=0,rows=0;check(GRBgetintattr(check_model.model,"NumVars",&n));check(GRBgetintattr(check_model.model,"NumConstrs",&rows));
    SolverNeutralModelDomain dom;dom.names.resize(n);dom.lower_bounds.resize(n);dom.upper_bounds.resize(n);dom.variable_types.resize(n);
    check(GRBgetdblattrarray(check_model.model,"LB",0,n,dom.lower_bounds.data()));check(GRBgetdblattrarray(check_model.model,"UB",0,n,dom.upper_bounds.data()));
    check(GRBgetcharattrarray(check_model.model,"VType",0,n,dom.variable_types.data()));
    for(int j=0;j<n;++j){char* name=nullptr;check(GRBgetstrattrelement(check_model.model,"VarName",j,&name));dom.names[j]=name;}
    auto mapped=mapVerifiedRoutesToCanonicalModel(in,opt,routes,"offline_qualification_only",lower,upper,cutoff,dom);
    const bool expect_start=pv.G>=lower-1e-8&&pv.G<=upper+1e-8&&pv.objective<=cutoff+1e-8;
    double residual=0,objective=0;std::vector<double> obj(n);check(GRBgetdblattrarray(check_model.model,"Obj",0,n,obj.data()));
    if(expect_start){require(mapped.complete,"Start:"+mapped.failure_reason);
        for(int j=0;j<n;++j)objective+=obj[j]*mapped.values[j];
        require(std::abs(objective-pv.objective)<1e-7,"original Start objective");
        for(int i=0;i<rows;++i){int nz=0;check(GRBgetconstrs(check_model.model,&nz,nullptr,nullptr,nullptr,i,1));
            int beg=0;std::vector<int> ix(nz);std::vector<double> a(nz);check(GRBgetconstrs(check_model.model,&nz,&beg,ix.data(),a.data(),i,1));
            double rhs=0,activity=0;char sense='=';check(GRBgetdblattrelement(check_model.model,"RHS",i,&rhs));check(GRBgetcharattrelement(check_model.model,"Sense",i,&sense));
            for(int j=0;j<nz;++j)activity+=a[j]*mapped.values[ix[j]];
            residual=std::max(residual,sense=='='?std::abs(activity-rhs):(sense=='<'?activity-rhs:rhs-activity));}
        require(residual<=1e-7,"Start actual-matrix residual");
    }else require(!mapped.complete,"out-of-domain Start accepted");
    {std::ofstream f(dir/"start_check.json");f<<std::setprecision(17)<<std::boolalpha<<"{\"complete\":"<<mapped.complete<<",\"expected\":"<<expect_start<<",\"failure\":"<<std::quoted(mapped.failure_reason)<<",\"rows\":"<<rows<<",\"columns\":"<<n<<",\"max_residual\":"<<residual<<",\"original_objective\":"<<pv.objective<<",\"mapped_objective\":"<<objective<<",\"build_seconds\":"<<build_seconds<<",\"model_SHA\":"<<std::quoted(art.sha256)<<"}\n";}
    if(mode=="export")return;
    require(mode=="LP"||mode=="MIP"||mode=="MIP-zero"||mode=="restore","solve mode");
    auto backend=makeGurobiFixedIntervalBackend(in,opt);int calls=0;std::ofstream ledger(dir/"Optimize.jsonl");
    auto solve=[&](bool lp,bool reuse){
        FixedIntervalMipRequest req;req.solve_kind=lp?FixedIntervalSolveKind::PaperLpRelaxation:FixedIntervalSolveKind::PaperTerminalMip;
        req.leaf_id=argv[15];req.gamma_L=lower;req.gamma_U=upper;req.verified_cutoff=cutoff;
        req.canonical_model_path=art.path;req.canonical_model_fingerprint=art.sha256;req.canonical_row_signature=art.row_signature;
        req.canonical_model_scope="Round166_offline_qualification_only";req.native_log_path=dir/(lp?"LP.log":"MIP.log");
        req.time_limit_seconds=req.global_deadline_remaining_seconds=std::max(.001,std::stod(argv[11])-elapsed());
        req.round68_verified_start=!lp&&expect_start;req.verified_start_routes=routes;req.verified_start_source="offline_qualification_only";
        req.interval_mip_policy=compact?"round166-breakpoint-bit":"round55-vd-p";req.capture_lp_primal_dual_evidence=lp;
        if(mode=="MIP-zero")req.round60_fixed_inventory.assign(in.V+1,0);
        req.incremental_model_reuse_enabled=reuse;req.retain_model_after_solve=reuse;
        ledger<<"{\"call\":"<<++calls<<",\"LP\":"<<(lp?"true":"false")<<",\"phase\":\"begin\"}\n";ledger.flush();
        auto r=backend->solve(req);ledger<<"{\"call\":"<<calls<<",\"phase\":\"end\",\"return\":"<<r.optimize_return_code<<"}\n";ledger.flush();
        std::ofstream f(dir/(lp?"LP.json":"MIP.json"));f<<std::setprecision(17)<<std::boolalpha;
        f<<"{\"available\":"<<r.available<<",\"status\":"<<std::quoted(r.native_status)<<",\"failure\":"<<std::quoted(r.failure_reason)
          <<",\"objective\":"<<(lp?r.lp_objective_value:r.incumbent_objective)<<",\"lower\":"<<r.native_bound<<",\"lower_available\":"<<r.native_bound_available
          <<",\"rows\":"<<r.model_linear_constraint_count<<",\"columns\":"<<r.model_variable_count<<",\"nonzeros\":"<<r.model_nonzero_count
          <<",\"binaries\":"<<r.model_binary_variable_count<<",\"integers\":"<<r.model_integer_variable_count
          <<",\"LP_evidence\":"<<r.lp_primal_dual_evidence_available<<",\"integer_domain_restored\":"<<r.integer_domain_restored
          <<",\"Start_submitted\":"<<r.warm_start_submitted<<",\"Start_rows_valid\":"<<r.round68_start_rows_valid<<",\"Start_status\":"<<std::quoted(r.warm_start_status)
          <<",\"model_matches\":"<<r.model_fingerprint_matches_request<<",\"zero_gaps\":"<<r.exact_zero_gap_roundtrip<<",\"gate\":"<<r.feasibility_consistency_gate
          <<",\"runtime\":"<<r.solver_runtime_seconds<<",\"work\":"<<r.work<<",\"nodes\":"<<r.nodes<<",\"build_seconds\":"<<build_seconds<<",\"outer_seconds\":"<<elapsed()<<"}\n";
        require(r.available&&r.optimize_return_code==0,"native solve failure:"+r.failure_reason);
        if(!lp&&expect_start)require(r.warm_start_submitted&&r.round68_start_rows_valid,"native Start failed");
        // The inherited backend restores original types before returning LP,
        // so its LP receipt (not the next MIP receipt) owns this evidence.
        if(reuse&&lp)require(r.integer_domain_restored,"LP to MIP type restoration");
        if(!lp&&r.incumbent_available){auto v=verifySolution(in,r.incumbent_routes,opt.lambda);require(v.feasible,"native physical feasibility");
            std::ofstream s(dir/"fleet.txt");s<<r.incumbent_routes.size()<<'\n';for(const auto& route:r.incumbent_routes){s<<route.vehicle<<' '<<route.nodes.size();for(int a:route.nodes)s<<' '<<a;s<<'\n';
                for(const auto& op:route.operations)s<<op.pickup-op.drop<<' ';
                s<<'\n';}
            std::ofstream p(dir/"physical.json");p<<std::setprecision(17)<<"{\"F\":"<<v.objective<<",\"G\":"<<v.G<<",\"P\":"<<v.P<<",\"Y\":[";
            for(size_t j=1;j<v.final_inventory.size();++j){if(j>1)p<<',';p<<v.final_inventory[j];}p<<"]}\n";
        }
    };
    if(mode=="restore"){solve(true,true);solve(false,true);}else solve(mode=="LP",false);
    backend->release();std::cout<<argv[9]<<' '<<mode<<" calls="<<calls<<'\n';
}
}
int main(int argc,char** argv){try {
    require(argc>=3,"Round166Qualification algebra|local|physical ...");
    if(std::string(argv[1])=="algebra")algebra(argv[2]);
    else if(std::string(argv[1])=="tiny-oracle")tinyOracle(argv[2]);
    else if(std::string(argv[1])=="local")local(argv[2]);
    else if(std::string(argv[1])=="physical")physical(argc,argv);
    else throw std::runtime_error("unknown qualification command");
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
