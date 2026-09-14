#include "CanonicalCompactModel.hpp"
#include "Evaluator.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "MipStartMapping.hpp"
#include "PaperK1AmSf.hpp"
#include "Round61Candidates.hpp"
#include <cmath>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
void require(bool value,const std::string& reason) {if(!value)throw std::runtime_error(reason);}
ebrp::Instance fixture() {
    ebrp::Instance in;in.V=3;in.M=2;in.Q={3,3};
    in.initial={50,3,1,2};in.capacity={100,4,4,4};in.target={0,2,2,2};
    in.weights={0,1,1,1};in.min_ratio={0,0,0,0};
    in.total_time_limit=3;in.pickup_time=in.drop_time=0;
    in.dist.assign(4,std::vector<double>(4));
    for(int i=0;i<4;++i)for(int j=0;j<4;++j)in.dist[i][j]=1.5*std::abs(i-j);
    return in;
}
std::vector<ebrp::RoutePlan> witness() {
    return {{0,{0,0},{}},{1,{0,1,0},{{1,1,0}}}};
}
void mapping() {
    const auto in=fixture();ebrp::SolveOptions options;
    const auto normalized=ebrp::normalizeRound61Routes(in,options.lambda,witness());
    require(normalized.size()==1&&normalized[0].vehicle==0,"equal-Q representative mapping");
    const auto verification=ebrp::verifySolution(in,normalized,options.lambda);
    require(verification.feasible&&std::fabs(verification.objective-5./24)<1e-12,"physical loaded return");
    ebrp::SolverNeutralModelDomain domain;
    domain.names={"G","Y_1","state_1_1","state_1_2","state_1_3",
                  "state_g_1_1","state_g_1_2","state_g_1_3","zprod_1"};
    domain.lower_bounds.assign(domain.names.size(),0);
    domain.upper_bounds.assign(domain.names.size(),10);
    domain.variable_types.assign(domain.names.size(),'C');
    domain.variable_types[1]='I';
    for(int i=2;i<=4;++i){domain.variable_types[i]='B';domain.upper_bounds[i]=1;}
    const auto mapped=ebrp::mapVerifiedRoutesToCanonicalModel(in,options,normalized,
        "paid_current_witness",0,1,verification.objective,domain);
    require(mapped.complete,"VD-P exact-state columns map: "+mapped.failure_reason);
    require(mapped.values[2]==0&&mapped.values[3]==1&&mapped.values[4]==0,"one-hot state");
    require(mapped.values[5]==0&&mapped.values[6]==verification.G&&mapped.values[7]==0,"perspective state");
    require(std::fabs(mapped.values[8]-2*verification.G)<1e-12,"product reconstruction");
    auto outside=ebrp::mapVerifiedRoutesToCanonicalModel(in,options,normalized,
        "outside_interval",.2,1,verification.objective,domain);
    require(!outside.complete&&!outside.interval_membership_valid,"incompatible interval not submitted");
    auto unsupported=domain;unsupported.names.back()="state_code_1_0";
    require(!ebrp::mapVerifiedRoutesToCanonicalModel(in,options,normalized,
        "LOG_not_enabled",0,1,1,unsupported).complete,"unqualified LOG start accepted");
}

#if EXACT_EBRP_ENABLE_GUROBI
void nativeRetainedTransition() {
    const auto in=fixture();ebrp::SolveOptions options;
    ebrp::configurePaperK1AmSfOverrides(options);
    options.round68_verified_start=true;options.mip_threads=1;
    const auto verified=ebrp::verifySolution(in,witness(),options.lambda);
    require(verified.feasible,"native fixture original witness");
    const auto dir=std::filesystem::temp_directory_path()/
        ("exactebrp_round68_native_start_"+std::to_string(
            std::chrono::steady_clock::now().time_since_epoch().count()));
    std::filesystem::create_directories(dir);
    ebrp::CanonicalCompactModelSpec spec;
    spec.strengthened=true;spec.interval_restricted=true;
    spec.gamma_L=0;spec.gamma_U=verified.objective;
    spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    spec.add_verified_incumbent_row=true;spec.verified_incumbent=verified.objective;
    const auto model=ebrp::writeCanonicalCompactModel(in,options,dir/"model.lp",spec);
    require(model.written,"native VD-P model: "+model.failure_reason);
    std::ifstream model_input(model.path);
    const std::string model_text{std::istreambuf_iterator<char>(model_input),{}};
    require(model_text.find(": 0 G <= 6")!=std::string::npos,
        "zero-handling constant row lacks an explicit zero linear term");
    auto backend=ebrp::makeGurobiFixedIntervalBackend(in,options);
    require(backend->capabilities().available,"native Gurobi qualification unavailable");
    ebrp::FixedIntervalMipRequest request;
    request.leaf_id="L0";request.gamma_L=0;request.gamma_U=spec.gamma_U;
    request.verified_cutoff=verified.objective;request.global_deadline_remaining_seconds=10;
    request.incremental_model_reuse_enabled=true;request.retain_model_after_solve=true;
    request.canonical_model_path=model.path;request.canonical_model_fingerprint=model.sha256;
    request.canonical_row_signature=model.row_signature;request.interval_mip_policy="round55-vd-p";
    request.solve_kind=ebrp::FixedIntervalSolveKind::PaperLpRelaxation;
    request.native_log_path=dir/"lp.log";
    const auto lp=backend->solve(request);
    require(lp.lp_terminal_valid&&lp.integer_domain_restored,"LP types restored: "+lp.failure_reason);
    request.new_leaf=false;request.solve_kind=ebrp::FixedIntervalSolveKind::PaperTerminalMip;
    request.warm_start_enabled=true;request.round68_verified_start=true;
    request.verified_start_routes=witness();request.verified_start_source="unit_paid_complete";
    request.native_log_path=dir/"mip.log";
    const auto mip=backend->solve(request);
    require(mip.failure_reason.empty()||mip.failure_reason=="none",
        "native Start integration: "+mip.failure_reason);
    require(mip.in_memory_model_reused&&!mip.reset_called,"retained object without reset");
    require(mip.warm_start_mapping_complete&&mip.round68_start_rows_valid&&
        mip.round68_start_objective_valid&&mip.warm_start_submitted&&mip.round68_start_readback_valid,
        "complete verified native Start not active");
    require(mip.warm_start_status=="accepted_by_native_log","no native acceptance: "+mip.warm_start_status);
    require(mip.round68_start_integer_vector_observed,"native Start integer vector not observed");
    require(mip.optimal&&mip.incumbent_independently_verified&&
        std::fabs(mip.incumbent_objective-5./24)<1e-7,"original objective after native Start");
    require(mip.round68_effective_native_deadline<10&&mip.round68_effective_native_deadline>=0,
        "mapping cost did not consume global deadline");
    // Empty routes are valid original witnesses, but this one exceeds the
    // tighter current interval/cutoff. Explicit prior Start must be cleared safely.
    request.verified_start_routes.clear();request.verified_start_source="unit_ineligible_current";
    request.native_log_path=dir/"ineligible.log";
    const auto skipped=backend->solve(request);
    require((skipped.failure_reason.empty()||skipped.failure_reason=="none")&&!skipped.warm_start_submitted&&
        skipped.warm_start_status.find("ineligible:")==0,"ineligible witness silently resubmitted");
    require(skipped.optimal&&skipped.incumbent_independently_verified,"skip corrupted complete proof");
    require(backend->stats().optimize_count==3,"unplanned native calls");
    backend->release();
    std::cout<<"Native qualification: 3 Optimize calls; retained Start accepted and observed; "
             <<mip.round68_start_checked_rows<<" rows checked; evidence "<<dir<<'\n';
}
#endif
}
int main() {
    try {
        mapping();
#if EXACT_EBRP_ENABLE_GUROBI
        nativeRetainedTransition();
#else
        std::cout<<"Native Start qualification not built (Gurobi disabled)\n";
#endif
        std::cout<<"Round68 existing-witness integration tests passed\n";return 0;
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
