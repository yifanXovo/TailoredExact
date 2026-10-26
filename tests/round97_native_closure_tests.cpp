#include "Round97NativeClosure.hpp"
#include "Evaluator.hpp"
#include "Round61Candidates.hpp"
#include "Round83BlockExchange.hpp"
#include "Round96RouteOrder.hpp"
#include <chrono>
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
void check(bool value,const char* why){if(!value)throw std::runtime_error(why);}
Instance fixture() {
    Instance in;in.V=3;in.M=2;in.Q={3,3};in.name="round97_directed_micro";
    in.initial={0,4,0,2};in.capacity={0,5,5,5};in.target={0,2,2,2};in.weights={0,1,1,1};
    in.total_time_limit=100;in.pickup_time=.5;in.drop_time=.75;
    in.dist={{0,1,9,2},{3,0,1,8},{1,6,0,1},{4,1,7,0}}; // directed, triangle inequality fails
    return in;
}
Round97Model model(const Instance& in) {
    Round97Model m;m.call=1;m.leaf="micro";m.sha="synthetic_semantic_registry_not_native";m.lower=0;m.upper=1;m.cutoff=10;
    auto add=[&](std::string name,char type,double upper,double objective=0){m.domain.names.push_back(name);
        m.domain.variable_types.push_back(type);m.domain.lower_bounds.push_back(0);m.domain.upper_bounds.push_back(upper);m.objective.push_back(objective);};
    add("G",'C',1,1);
    for(int i=1;i<=in.V;++i){add("Y_"+std::to_string(i),'I',in.capacity[i]);add("e_"+std::to_string(i),'C',10,.15*in.weights[i]);}
    for(int k=0;k<in.M;++k){for(int i=0;i<=in.V;++i)for(int j=0;j<=in.V;++j)if(i!=j)
        add("x_"+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(j),'B',1);
        for(int i=1;i<=in.V;++i){add("p_"+std::to_string(k)+"_"+std::to_string(i),'I',5);add("d_"+std::to_string(k)+"_"+std::to_string(i),'I',5);}}
    m.linear.variable_count=static_cast<int>(m.domain.names.size());m.linear.row_starts={0};return m;
}
Instance orderFixture() {
    Instance in;in.V=4;in.M=1;in.Q={3};
    in.initial={50,4,0,0,0};in.capacity={100,4,2,2,2};
    in.target={0,1,1,1,1};in.weights={0,1,1,1,1};
    in.points={{0,0},{0,1},{1,0},{1,1},{1000000,1000000}};
    in.dist.assign(5,std::vector<double>(5,1000000));
    for(int i=0;i<5;++i)in.dist[i][i]=0;
    for(int i=0;i<4;++i)for(int j=0;j<4;++j)
        in.dist[i][j]=std::hypot(in.points[i].first-in.points[j].first,in.points[i].second-in.points[j].second);
    in.total_time_limit=2+2*std::sqrt(2.)+.8;in.pickup_time=.2;in.drop_time=.2;
    return in; // unreachable station4 keeps the improved objective positive
}
int main(int argc,char** argv){try {
    check(argc==2,"supply fresh evidence directory");const std::filesystem::path dir=argv[1];
    check(!std::filesystem::exists(dir),"test destination exists");std::filesystem::create_directories(dir);
    auto in=fixture();SolveOptions opt;opt.lambda=.15;opt.round97_native_closure="feedback";
    std::vector<RoutePlan> loaded{{0,{0,1,0},{{1,2,0}}}},empty{{0,{0,0},{}},{1,{0,0},{}}};
    check(verifySolution(in,loaded,opt.lambda).route_duration[0]==6.5,"loaded-return handling changed");
    auto relabel=loaded;relabel[0].vehicle=1;
    check(round97StateHash(in,opt.lambda,loaded)==round97StateHash(in,opt.lambda,relabel),"legal equal-capacity normalization");
    auto heterogeneous=in;heterogeneous.Q={3,4};
    check(round97StateHash(heterogeneous,opt.lambda,loaded)!=round97StateHash(heterogeneous,opt.lambda,relabel),"illegal heterogeneous normalization");
    check(round97StateHash(in,opt.lambda,empty)==round97StateHash(in,opt.lambda,{}),"empty-route representation mismatch");
    auto m=model(in);auto start=mapVerifiedRoutesToCanonicalModel(in,opt,loaded,"micro",0,1,10,m.domain);
    check(start.complete,"micro input mapping failed");
    for(const std::string op:{"r83","r96"}) {
        auto gated_options=opt;gated_options.round97_native_operator=op;
        int gate_submits=0;auto gate_submit=[&](const auto&,double&){++gate_submits;return 0;};
        const auto loaded_hash=round97StateHash(in,opt.lambda,loaded);
        Round97NativeClosure initial_seed(in,gated_options,dir/(op+"_initial_seed"),loaded_hash);
        auto lifted=start.values;lifted[0]+=.01;auto no_start=model(in);
        initial_seed.solution(no_start,lifted,start.objective+.01,1e100,4,0,1,gate_submit);
        check(!initial_seed.failed()&&!initial_seed.archive().verified&&gate_submits==0,
            "initial seed with lifted model G and no actual Start entered closure");
        auto current=model(in);current.start_hash=loaded_hash;
        Round97NativeClosure gate(in,gated_options,dir/(op+"_current_start"),round97StateHash(in,opt.lambda,{}));
        auto empty_start=mapVerifiedRoutesToCanonicalModel(in,opt,{},"empty",0,1,10,current.domain);
        check(empty_start.complete,"empty seed mapping failed");
        gate.solution(current,empty_start.values,empty_start.objective,1e100,0,0,1,gate_submit);
        gate.solution(current,start.values,start.objective,1e100,1,1,1,gate_submit);
        check(!gate.failed()&&!gate.archive().verified&&gate_submits==0,"initial/current Start exclusion failed");
        current.call=2;current.start_hash.clear();
        gate.solution(current,start.values,start.objective,0,2,0,1,gate_submit);
        check(!gate.failed()&&gate.archive().verified&&gate.archive().objective<start.objective&&gate_submits==0,
            "seen source previously excluded as Start was incorrectly cached as closed");
        auto self=mapVerifiedRoutesToCanonicalModel(in,opt,gate.archive().routes,"self",0,1,10,current.domain);
        check(self.complete,"self-output mapping failed");
        gate.solution(current,self.values,self.objective,1e100,3,1,1,gate_submit);
        check(!gate.failed()&&gate_submits==0&&std::filesystem::exists(dir/(op+"_current_start")/"vector_4.csv"),
            "cached self-output looped or lost its first native source vector");
        std::vector<RoutePlan> a{{0,{0,1,3,0},{{1,2,0},{3,1,0}}}};
        auto b=a;b[0].nodes={0,3,1,0};
        check(verifySolution(in,a,opt.lambda).objective==verifySolution(in,b,opt.lambda).objective&&
            round97StateHash(in,opt.lambda,a)!=round97StateHash(in,opt.lambda,b),"same-F distinct-state fixture invalid");
        auto nm=model(in);nm.start_hash=round97StateHash(in,opt.lambda,a);
        auto bv=mapVerifiedRoutesToCanonicalModel(in,opt,b,"same_F",0,1,10,nm.domain);
        check(bv.complete,"same-F distinct-state mapping failed");
        Round97NativeClosure equal_F(in,gated_options,dir/(op+"_same_F"),nm.start_hash);
        equal_F.solution(nm,bv.values,bv.objective,0,0,0,1,gate_submit);
        check(!equal_F.failed()&&equal_F.archive().verified&&equal_F.archive().objective<bv.objective,
            "objective equality or non-improvement of native incumbent wrongly excluded a new physical state");
    }
    int submitted=0;auto submit=[&](const std::vector<double>&,double& obj){++submitted;obj=1e100;return 0;};
    Round97NativeClosure session(in,opt,dir/"feedback");
    session.solution(m,start.values,start.objective,0,7,0,1,submit); // non-improving MIPSOL must still be closed
    check(!session.failed()&&session.archive().verified&&session.archive().objective<start.objective,"non-improving native event lost");
    check(submitted==0,"worse-than-native candidate submitted");
    session.solution(m,start.values,start.objective,1e100,8,1,1,submit);
    check(!session.failed()&&submitted==1,"cached physical candidate failed new native admission");
    session.solution(m,start.values,start.objective,1e100,9,2,1,submit);
    check(submitted==1,"repeat feedback loop");
    auto same=m;same.call=2;same.epoch=1;same.submissions.clear();same.submitted_hashes.clear();same.cutoff=session.archive().objective;
    session.solution(same,start.values,start.objective,1e100,9,0,1,submit);
    check(submitted==2,"equal-cutoff missing-native candidate blocked");
    auto incompatible=same;incompatible.call=3;incompatible.lower=.9;incompatible.submitted_hashes.clear();
    session.solution(incompatible,start.values,start.objective,1e100,9,0,1,submit);
    check(!session.failed()&&submitted==2,"domain compatibility incorrectly reused");
    auto unsupported=same;unsupported.call=4;unsupported.submitted_hashes.clear();unsupported.domain.names.push_back("unknown_aux");
    unsupported.domain.lower_bounds.push_back(0);unsupported.domain.upper_bounds.push_back(1);unsupported.domain.variable_types.push_back('C');
    unsupported.objective.push_back(0);unsupported.linear.variable_count++;
    auto extra=start.values;extra.push_back(0);session.solution(unsupported,extra,start.objective,1e100,9,0,1,submit);
    check(!session.failed()&&submitted==2,"unknown mapping column silently completed");
    auto bad=same;bad.call=5;bad.submitted_hashes.clear();bad.linear.row_starts={0,1};bad.linear.column_indices={4};bad.linear.coefficients={1};
    bad.linear.senses={'='};bad.linear.rhs={start.values[4]}; // source e2=1, improved e2=0
    session.solution(bad,start.values,start.objective,1e100,9,0,1,submit);
    check(!session.failed()&&submitted==2,"invalid candidate row was submitted");
    SolveOptions shadow=opt;shadow.round97_native_closure="shadow";auto sm=model(in);
    Round97NativeClosure ss(in,shadow,dir/"shadow");int never=0;
    ss.solution(sm,start.values,start.objective,1e100,3,0,1,[&](const auto&,double&){++never;return 0;});
    check(!ss.failed()&&ss.archive().verified&&never==0,"shadow contaminated native submission");
    auto zero_in=in;zero_in.initial=zero_in.target;auto zm=model(zero_in);
    Round97NativeClosure zero(zero_in,opt,dir/"zero");auto zs=mapVerifiedRoutesToCanonicalModel(zero_in,opt,{},"zero",0,1,0,zm.domain);
    zero.solution(zm,zs.values,0,0,0,0,1,submit);check(!zero.failed(),"zero/empty state failed");
    auto expired=opt;expired.process_start_time_valid=true;expired.process_start_time=std::chrono::steady_clock::now()-std::chrono::seconds(2);
    expired.process_wall_time_limit=1;Round97NativeClosure deadline(in,expired,dir/"deadline");auto dm=model(in);
    deadline.solution(dm,start.values,start.objective,1e100,4,0,1,submit);check(!deadline.archive().verified&&!deadline.failed(),"deadline constructed archive");
    Round97NativeClosure numerical(in,opt,dir/"numerical");auto nm=model(in);auto invalid=start.values;invalid[1]+=.01;
    numerical.solution(nm,invalid,start.objective,1e100,4,0,1,submit);check(numerical.failed(),"noninteger native event admitted");
    SolveOptions interrupted=opt;interrupted.process_start_time_valid=true;interrupted.process_start_time=std::chrono::steady_clock::now();
    interrupted.process_wall_time_limit=100;Verification saved;
    auto retained=runRound83ExchangeDescent(in,interrupted,loaded,{},[&](const auto& routes,const auto& v){
        saved=verifySolution(in,routes,opt.lambda);check(saved.objective==v.objective,"accepted observer mismatch");
        interrupted.process_start_time=std::chrono::steady_clock::now()-std::chrono::seconds(200);
    });
    check(retained.deadline&&saved.feasible&&saved.objective<start.objective&&retained.verification.objective==saved.objective,
        "later interrupted scan discarded earlier accepted witness");
    auto order_in=orderFixture();
    std::vector<RoutePlan> order_routes{{0,{0,1,2,3,0},{{1,2,0},{2,0,1},{3,0,1}}}};
    const auto order_before=verifySolution(order_in,order_routes,opt.lambda);
    check(order_before.feasible,"order opportunity fixture invalid");
    const auto old_stop=runRound83ExchangeDescent(order_in,opt,order_routes);
    check(old_stop.exhausted&&old_stop.verification.objective==order_before.objective,"fixture is not old-closure exhausted");
    auto order_options=opt;order_options.round97_native_operator="r96";
    auto om=model(order_in);
    auto ov=mapVerifiedRoutesToCanonicalModel(order_in,opt,order_routes,"order",0,1,10,om.domain);
    check(ov.complete,"order source mapping failed");
    int order_submissions=0;
    Round97NativeClosure combined(order_in,order_options,dir/"combined");
    combined.solution(om,ov.values,ov.objective,1e100,6,0,1,[&](const auto&,double&){++order_submissions;return 0;});
    check(!combined.failed()&&combined.archive().verified&&combined.archive().objective<order_before.objective&&
        combined.archive().objective>0&&order_submissions==1,"combined operator failed its independent increment");
    SolveOptions order_interrupted=opt;order_interrupted.process_start_time_valid=true;
    order_interrupted.process_start_time=std::chrono::steady_clock::now();order_interrupted.process_wall_time_limit=100;
    Verification order_saved;
    auto order_retained=runRound96RouteOrder(order_in,order_interrupted,order_routes,{},
        [&](const auto& routes,const auto& v){
            if(v.objective>=order_before.objective-1e-12)return; // neutral step is not an F improvement
            order_saved=verifySolution(order_in,routes,opt.lambda);
            check(order_saved.feasible&&order_saved.objective==v.objective,"order observer independent witness mismatch");
            order_interrupted.process_start_time=std::chrono::steady_clock::now()-std::chrono::seconds(200);
        });
    check(order_retained.stats.accepted>0&&order_retained.stats.deadline&&order_saved.feasible&&
        order_retained.stats.initial_old_closure_complete&&
        order_retained.stats.initial_old_closure_F==order_before.objective&&
        order_saved.objective>0&&order_saved.objective<order_before.objective&&
        order_retained.verification.objective==order_saved.objective,"R96 later scan discarded predeadline old-closure acceptance");
    std::cout<<"Round97 semantic micro checks passed; optimizer_calls=0\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
