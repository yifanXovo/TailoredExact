#include "IndependentObjectiveProof.hpp"
#include "Evaluator.hpp"
#include <climits>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
void require(bool ok, const char* message) { if (!ok) throw std::runtime_error(message); }
int main() { try {
    Instance in; in.V=2; in.M=1; in.Q={2}; in.capacity={0,4,4};
    in.initial={0,2,2}; in.target={0,2,2}; in.weights={0,1,1};
    in.dist.assign(3,std::vector<double>(3,0));
    SolveResult result; result.routes={{0,{0,0},{}}};
    result.verification=verifySolution(in,result.routes,.15);
    result.gurobi_failure_reason="native_source_unqualified:fixture";
    result.external_gini_tree_lifecycle_complete=false;
    require(applyIndependentZeroCertificate(in,.15,result,true),"complete own zero must certify");
    require(result.lower_bound==0 && result.strict_certified_original_problem &&
        result.strict_certificate_class=="independent_zero_nonnegative_floor", "independent certificate missing");
    require(result.gurobi_failure_reason=="native_source_unqualified:fixture" &&
        !result.external_gini_tree_lifecycle_complete,"native failure must remain rejected");
    result.routes.clear(); result.verification=verifySolution(in,result.routes,.15);
    require(!applyIndependentZeroCertificate(in,.15,result),"missing vehicle must not certify");
    result.routes={{0,{0,0},{}},{0,{0,0},{}}}; result.verification=verifySolution(in,result.routes,.15);
    require(!applyIndependentZeroCertificate(in,.15,result),"duplicate vehicle must not certify");
    in.initial={0,INT_MAX-1,INT_MAX-1}; in.target={0,INT_MAX,INT_MAX};
    in.capacity={0,INT_MAX,INT_MAX}; result.routes={{0,{0,0},{}}};
    for (double lambda : {.075,.15,.30}) {
        result.verification=verifySolution(in,result.routes,lambda);
        require(result.verification.objective>0 && result.verification.objective<1e-7,"near-zero fixture invalid");
        require(!applyIndependentZeroCertificate(in,lambda,result),"near-zero positive must not be strict zero");
    }
    require(!exactZeroInventoryObjective(in,-.15,in.target),"negative lambda invalidates floor");
    require(exactZeroInventoryObjective(in,0,in.initial),"equal exact ratios with lambda0 have zero objective");
    result.verification=verifySolution(in,result.routes,0);
    require(applyIndependentZeroCertificate(in,0,result) && result.P>0,"lambda0 proof must retain physical penalty");
    in.initial={0,0,0}; in.target={0,2,2}; in.capacity={0,4,4};
    require(exactZeroInventoryObjective(in,0,in.initial),"S0 case must be supported");
    result.verification=verifySolution(in,result.routes,.15);
    require(!applyIndependentZeroCertificate(in,.15,result),"positive empty-stock penalty cannot certify zero");
    std::cout<<"independent zero, rejected source, complete fleet, near-zero and lambda premises PASS; Optimize=0\n";
    return 0;
} catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;} }
