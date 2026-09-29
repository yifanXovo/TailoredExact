#include "Round97NativeClosure.hpp"
#include "Evaluator.hpp"
#include "Round61Candidates.hpp"
#include <chrono>
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
    std::cout<<"Round97 semantic micro checks passed; optimizer_calls=0\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
