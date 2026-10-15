// One qualification process: finite physical/contract checks and zero-Optimize
// native matrix/Start readback. No GRBoptimize symbol is resolved here.
#define main round119_cold_reference_main
#include "../src/round65_reference_build.cpp"
#undef main
#include "Round119ProofContraction.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "PaperK1AmSf.hpp"
#include "Evaluator.hpp"
#include "MipStartMapping.hpp"
#include "Round60Candidates.hpp"
#include "FileSha256.hpp"
#include <sstream>
#include <functional>
#include <algorithm>
#include <iomanip>
#include <cmath>
using namespace ebrp;
namespace {
void require(bool v,const char* why){if(!v)throw std::runtime_error(why);}
Round119Certificate certificate(int side,double bound,double cutoff=.65) {
    Round119Certificate p;p.parent="L0";p.leaf="L0."+std::to_string(side);
    p.side=side;p.depth=0;p.call=side+1;p.epoch=0;p.model="model";p.path="path";p.scope="scope";p.status="OPTIMAL";
    p.parent_lower=0;p.parent_upper=.5;p.lower=side==0?0:.25;p.upper=side==0?.25:.5;
    p.bound=bound;p.cutoff=cutoff;return p;
}
void finite(const std::filesystem::path& dir) {
    ControllingLeaf l;l.id="L0";l.gamma_U=.5;l.cutoff=.65;
    std::vector<Round119Certificate> p{certificate(0,.15),certificate(1,.4)};
    auto choose=[&](double U){return chooseRound119Contraction(p,l,{"L0"},U,1e-7,8,1e-4);};
    require(!choose(.5).available,"bound below U triggered");
    require(!choose(.4).available,"equality triggered");
    require(!choose(.4-5e-8).available,"tolerance edge triggered");
    require(choose(.3).available,"strict valid exclusion missing");
    p[0].cutoff=p[1].cutoff=.2;require(!choose(.3).available,"cutoff complement omitted");p[0].cutoff=p[1].cutoff=.65;
    p[1].used=true;require(!choose(.3).available,"same proof reused");p[1].used=false;
    p[0].epoch=1;require(!choose(.3).available,"different epoch pair admitted");p[0].epoch=0;
    p[0].parent_upper=.6;require(!choose(.3).available,"different original scope admitted");p[0].parent_upper=.5;
    p[0].model.clear();require(!choose(.3).available,"missing model admitted");p[0].model="model";
    l.split_depth=8;require(!choose(.3).available,"depth reset");l.split_depth=0;
    l.lower_bound=.3;require(!choose(.3).available,"existing complete bound should close first");l.lower_bound=0;
    auto copy=l;copy.gamma_L=.25;require(!chooseRound119Contraction(p,copy,{"L0"},.3,1e-7,8,1e-4).available,"same domain renamed restart");
    ControllingLeafScheduler scheduler;std::string why;require(scheduler.addLeaf(l,&why),"root add");
    auto before=scheduler.leaves();ControllingLeaf bad=l;bad.id="new";bad.parent_id="L0";bad.split_depth=1;
    require(!scheduler.splitLeafAtomically("L0",{bad},&why),"failed atomic proposal admitted");
    require(scheduler.leaves().size()==before.size() && !scheduler.findLeaf("L0")->parent_replaced,"failed transaction changed cover");
    FixedIntervalMipOutcome returned;returned.attempted=true;returned.optimize_return_code=0;
    returned.solver_finalization_reached=returned.exact_zero_gap_roundtrip=returned.model_fingerprint_matches_request=returned.feasibility_consistency_gate=true;
    returned.failure_reason="none";returned.native_status="INTERRUPTED";
    require(evaluateRound119Return(returned,1)==Round119ReturnDisposition::MathematicalReturn,"normal mathematical return rejected");
    returned.solver_finalization_reached=false;
    require(evaluateRound119Return(returned,1)==Round119ReturnDisposition::Invalid,"pending termination treated as returned");
    returned.solver_finalization_reached=true;returned.native_status="TIME_LIMIT";
    require(evaluateRound119Return(returned,0)==Round119ReturnDisposition::Deadline,"deadline race rejected or resumed");
    returned.native_status="MEM_LIMIT";
    require(evaluateRound119Return(returned,1)==Round119ReturnDisposition::ResourceStop,"resource stop resumed");
    returned.native_status="UNKNOWN";require(evaluateRound119Return(returned,1)==Round119ReturnDisposition::Invalid,"unknown return admitted");
    returned.native_status="INTERRUPTED";returned.optimize_return_code=1;
    require(evaluateRound119Return(returned,1)==Round119ReturnDisposition::Invalid,"native error admitted as mathematical interrupt");
    std::ofstream f(dir/"finite_contract.json");f<<"{\"Optimize\":0,\"passed\":true,\"cases\":20,\"scope\":\"predicate_transaction_and_real_return_preconditions\"}\n";
}
struct Native {
    SolverNeutralModelDomain domain;SolverNeutralLinearModel linear;
    std::vector<double> objective;double constant=0;
};
Native read_native(const std::filesystem::path& path) {
    HMODULE dll=LoadLibraryW(L"gurobi130.dll");if(!dll)throw std::runtime_error("native DLL unavailable");
#define API(n) auto n=reinterpret_cast<decltype(&GRB##n)>(GetProcAddress(dll,"GRB" #n));if(!n)throw std::runtime_error("missing " #n)
    API(emptyenvinternal);API(setintparam);API(startenv);API(readmodel);API(getintattr);API(getdblattr);
    API(getstrattrarray);API(getcharattrarray);API(getdblattrarray);API(getconstrs);API(freemodel);API(freeenv);
#undef API
    auto check=[](int rc){if(rc)throw std::runtime_error("native readback "+std::to_string(rc));};
    GRBenv* env=nullptr;GRBmodel* model=nullptr;Native out;
    try {
        check(emptyenvinternal(&env,GRB_VERSION_MAJOR,GRB_VERSION_MINOR,GRB_VERSION_TECHNICAL));
        check(setintparam(env,"OutputFlag",0));check(startenv(env));check(readmodel(env,path.string().c_str(),&model));
        int n=0,r=0,nnz=0;check(getintattr(model,"NumVars",&n));check(getintattr(model,"NumConstrs",&r));
        std::vector<char*> names(n);check(getstrattrarray(model,"VarName",0,n,names.data()));
        auto& d=out.domain;for(auto name:names)d.names.emplace_back(name);
        d.variable_types.resize(n);d.lower_bounds.resize(n);d.upper_bounds.resize(n);out.objective.resize(n);
        check(getcharattrarray(model,"VType",0,n,d.variable_types.data()));
        check(getdblattrarray(model,"LB",0,n,d.lower_bounds.data()));check(getdblattrarray(model,"UB",0,n,d.upper_bounds.data()));
        check(getdblattrarray(model,"Obj",0,n,out.objective.data()));check(getdblattr(model,"ObjCon",&out.constant));
        auto& m=out.linear;m.variable_count=n;m.row_starts.resize(r+1);m.senses.resize(r);m.rhs.resize(r);
        check(getcharattrarray(model,"Sense",0,r,m.senses.data()));check(getdblattrarray(model,"RHS",0,r,m.rhs.data()));
        check(getconstrs(model,&nnz,nullptr,nullptr,nullptr,0,r));m.column_indices.resize(nnz);m.coefficients.resize(nnz);
        check(getconstrs(model,&nnz,m.row_starts.data(),m.column_indices.data(),m.coefficients.data(),0,r));m.row_starts[r]=nnz;
    }catch(...){if(model)freemodel(model);if(env)freeenv(env);FreeLibrary(dll);throw;}
    freemodel(model);freeenv(env);FreeLibrary(dll);return out;
}
std::vector<std::vector<RoutePlan>> enumerate(const Instance& in) {
    std::vector<std::vector<RoutePlan>> all;std::vector<int> operations(in.V+1);
    std::function<void(int)> visit=[&](int i) {
        if(i<=in.V) {
            for(int net=-in.initial[i];net<=in.capacity[i]-in.initial[i];++net){operations[i]=net;visit(i+1);}return;
        }
        std::vector<int> order;for(int j=1;j<=in.V;++j)if(operations[j])order.push_back(j);
        do {
            RoutePlan r;r.vehicle=0;r.nodes={0};
            for(int j:order){r.nodes.push_back(j);r.operations.push_back({j,std::max(0,-operations[j]),std::max(0,operations[j])});}
            r.nodes.push_back(0);std::vector<RoutePlan> routes{r};
            const auto v=verifySolution(in,routes,.15);if(v.feasible&&v.errors.empty())all.push_back(std::move(routes));
        }while(std::next_permutation(order.begin(),order.end()));
    };visit(1);return all;
}
void physical_embedding(const std::filesystem::path& dir,const std::filesystem::path& fixture) {
    const auto in=parseInstanceFile(fixture.string(),1000,60,60);
    auto fleets=enumerate(in);require(fleets.size()>=3,"physical finite domain too small");
    SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.lambda=.15;opt.round98_state_service="m-binary";
    CanonicalCompactModelSpec spec;spec.strengthened=true;spec.interval_restricted=true;
    spec.gamma_U=.5;spec.add_verified_incumbent_row=true;spec.verified_incumbent=.65;
    spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    int mapped=0,excluded=0;double optimum=1e10;
    for(int side=-1;side<=1;++side) {
        spec.gamma_L=side==1?.25:0;spec.gamma_U=side==0?.25:.5;
        const auto path=dir/("physical_"+std::to_string(side)+".lp");
        const auto a=writeCanonicalCompactModel(in,opt,path,spec);require(a.written,"physical model write");
        auto data=read_native(path);
        for(const auto& routes:fleets) {
            const auto v=verifySolution(in,routes,.15);optimum=std::min(optimum,v.objective);
            if(side==1 && v.G>=.25){require(v.objective>=.4-1e-7,"removed physical interval contains strict improver");++excluded;}
            if(v.G<spec.gamma_L || v.G>spec.gamma_U) {
                const auto outside=mapVerifiedRoutesToCanonicalModel(in,opt,routes,"outside_true_G_scope",spec.gamma_L,spec.gamma_U,.65,data.domain);
                require(!outside.complete,"positive-G local model admitted a physical zero-G witness as in-scope");
                continue;
            }
            if(v.objective>.65+1e-7)continue;
            const auto start=mapVerifiedRoutesToCanonicalModel(in,opt,routes,"enumerated_own_physical",spec.gamma_L,spec.gamma_U,.65,data.domain);
            require(start.complete && start.bounds_valid && start.integrality_valid,"physical exact-G embedding missing");
            auto residual=validateCandidateLinearResidual(data.linear,start.values,1e-7);
            require(residual.checked && residual.valid,"physical embedding violates actual native row");
            double F=data.constant;for(std::size_t j=0;j<start.values.size();++j)F+=data.objective[j]*start.values[j];
            require(std::fabs(F-v.objective)<1e-7,"model g/objective not physical embedding");++mapped;
        }
        // A controller-only opt-in must not change the mathematical matrix.
        opt.round119_proof_contraction=true;
        const auto same=writeCanonicalCompactModel(in,opt,dir/("same_"+std::to_string(side)+".lp"),spec);
        require(same.written && a.sha256==same.sha256,"off/on changed original matrix at same scope");
        opt.round119_proof_contraction=false;
    }
    require(std::fabs(optimum-.3)<1e-12 && excluded>0,"constructed physical optimum/side expectation");
    // P/P-S and ENS/M-B keep their original actual numerical matrices/types,
    // while the opt-in flag has no matrix effect at an identical scope.
    std::string plain_sha;int profile_embeddings=0;
    for(const auto& profile:std::vector<std::string>{"P","ENS","M-B","P-S"}) {
        SolveOptions base;configurePaperK1AmSfOverrides(base);base.lambda=.15;
        CanonicalCompactModelSpec s;
        if(profile=="ENS" || profile=="M-B") {
            s.strengthened=true;s.interval_restricted=true;s.gamma_U=.5;s.add_verified_incumbent_row=true;
            s.verified_incumbent=.65;s.station_state_formulation="vd-p";s.round51_subset_duration_big_m="off";
            base.round98_state_service=profile=="M-B"?"m-binary":"off";
        } else {s.strengthened=false;base=SolveOptions{};base.lambda=.15;base.round112_ens_start_compact=profile=="P-S";}
        const auto path=dir/("profile_"+profile+".lp");auto a=writeCanonicalCompactModel(in,base,path,s);
        require(a.written,"default-off profile write");
        if(profile=="P")plain_sha=a.sha256;if(profile=="P-S")require(a.sha256==plain_sha,"P-S original matrix differs from P");
        auto native=read_native(path);
        for(std::size_t j=0;j<native.domain.names.size();++j) {
            const auto& name=native.domain.names[j];
            if(name.rfind("p_",0)==0 || name.rfind("d_",0)==0)
                require(native.domain.variable_types[j]==(profile=="M-B"?'C':'I'),"quantity native type changed");
        }
        for(const auto& routes:fleets) {
            const auto start=mapVerifiedRoutesToCanonicalModel(in,base,routes,"default_off_own_fleet",0,.5,.65,native.domain);
            require(start.complete && validateCandidateLinearResidual(native.linear,start.values).valid,"default-off actual full Start/rows changed");
            ++profile_embeddings;
        }
        base.round119_proof_contraction=true;
        const auto same=writeCanonicalCompactModel(in,base,dir/("profile_flag_"+profile+".lp"),s);
        require(same.written && same.sha256==a.sha256,"controller flag changed same-scope original profile matrix");
    }
    std::ofstream f(dir/"physical_embedding.json");f<<std::setprecision(17)
        <<"{\"Optimize\":0,\"passed\":true,\"physical_fleets\":"<<fleets.size()
        <<",\"actual_native_embeddings\":"<<mapped<<",\"four_profile_Start_embeddings\":"<<profile_embeddings<<",\"removed_side_fleets\":"<<excluded
        <<",\"physical_optimum\":"<<optimum<<",\"independent_enumeration\":true}\n";
}
}
