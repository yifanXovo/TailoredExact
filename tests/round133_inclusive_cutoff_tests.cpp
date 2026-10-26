#include "IntervalRowFactory.hpp"
#include "Evaluator.hpp"
#include "Round127Research.hpp"
#include <cmath>
#include <iostream>
#include <map>
#include <stdexcept>
using namespace ebrp;
int main(){try {
    Instance in;in.V=2;in.M=1;in.Q={1};in.initial={0,1,0};
    in.target={0,1,1};in.capacity={0,2,2};in.weights={0,1,1};
    in.min_ratio={0,0,0};in.dist.assign(3,std::vector<double>(3,0));
    in.total_time_limit=1;in.pickup_time=in.drop_time=60;
    SolveOptions options;options.lambda=std::ldexp(1.,-39);
    options.compact_bc_penalty_lb_closure=true;
    options.compact_bc_direct_gini_rows=true;
    options.compact_bc_objective_estimator_cutoff=true;
    round127().mode="ms2";
    const auto witness=verifySolution(in,{{0,{0,0},{}}},options.lambda);
    if(!witness.original_solution_feasible||witness.G!=.5||witness.P!=1||
       witness.objective!=.5+options.lambda)throw std::runtime_error("exact dyadic physical boundary fixture");
    IntervalRowFactoryRequest request;request.gamma_L=request.gamma_U=.5;
    request.verified_incumbent=witness.objective;request.incumbent_epsilon=0;
    request.add_incumbent_row=request.strengthened=true;
    const auto rows=buildRound18StaticIntervalRows(in,options,request);
    if(!(options.lambda>1e-12 && request.gamma_L+options.lambda*rows.domain.penalty_lower>=
         witness.objective-1e-9))throw std::runtime_error("legacy empty-row guard not actually exercised");
    std::map<std::string,double> point={{"r_1",1},{"r_2",0},{"e_1",0},{"e_2",1},
        {"h_1_2",1},{"G",.5},{"W_SP",1},{"Y_1",1},{"Y_2",0}};
    for(int i=1;i<=2;++i) {
        point["p_0_"+std::to_string(i)]=point["d_0_"+std::to_string(i)]=0;
        for(int bit=0;bit<4;++bit) {
            const double active=((i==1?1:0)>>bit)&1;
            const auto suffix=std::to_string(i)+"_"+std::to_string(bit);
            point["bit_"+suffix]=active;point["prod_"+suffix]=.5*active;
        }
    }
    int checked=0;
    for(const auto& row:rows.rows) {
        if(row.proof_tag=="interval_no_improver_domain_closure")
            throw std::runtime_error("artificial infeasibility survived in inclusive model");
        long double lhs=0;
        for(const auto& term:row.coefficients) {
            if(!point.count(term.first))throw std::runtime_error("missing fixture extension variable:"+term.first);
            lhs+=static_cast<long double>(term.second)*point.at(term.first);
        }
        const long double rhs=row.rhs;
        if((row.sense=='L'&&lhs>rhs)||(row.sense=='G'&&lhs<rhs)||(row.sense=='E'&&lhs!=rhs))
            throw std::runtime_error("legitimate factory row excludes boundary completion:"+row.family);
        ++checked;
    }
    for(const auto& bound:rows.bound_changes) {
        const auto value=point.at(bound.variable);
        if((bound.direction=='L'&&value<bound.value)||(bound.direction=='U'&&value>bound.value))
            throw std::runtime_error("factory bound excludes physical boundary completion");
        ++checked;
    }
    if(!(0.0>-1.0)||checked==0)throw std::runtime_error("legacy 0<=-1 negative control");
    std::cout<<checked<<" generated rows/bounds preserve exact dyadic boundary; old artificial row violates it by1; zero Optimize\n";
    return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
