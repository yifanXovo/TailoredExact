// Charged integration diagnostic: exercise the actual native final-stop API.
// Unlike the full algorithm it deliberately enters a native call even when the
// external structural floor could certify at the preceding outer boundary.
#include "Round62Passive.hpp"
#include "Round61Candidates.hpp"
#include "Round59Research.hpp"
#include "Round50IntervalMip.hpp"
#include "CanonicalCompactModel.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "Evaluator.hpp"
#include "Parser.hpp"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
int main(int argc,char** argv){try{
    const auto start=std::chrono::steady_clock::now();
    std::string input,out;double T=3600,pick=60,drop=60,lambda=.15,cap=20;
    for(int i=1;i<argc;++i){std::string a=argv[i];auto val=[&](){if(++i>=argc)throw std::runtime_error("missing value");return std::string(argv[i]);};
        if(a=="--input")input=val();else if(a=="--out")out=val();else if(a=="--T")T=std::stod(val());
        else if(a=="--pickup-time")pick=std::stod(val());else if(a=="--drop-time")drop=std::stod(val());
        else if(a=="--lambda")lambda=std::stod(val());else if(a=="--cap")cap=std::stod(val());else throw std::runtime_error("unknown argument");}
    auto in=ebrp::parseInstanceFile(input,T,pick,drop);
    ebrp::SolveOptions options;ebrp::configureRound50IntervalMipV0(options);ebrp::configureRound59CurrentF0(options);
    options.lambda=lambda;options.round61_candidate_mode="passive-cert";
    options.process_wall_time_limit=cap;options.process_start_time=start;options.process_start_time_valid=true;
    auto archive=ebrp::prepareRound61Candidate(in,options,std::filesystem::path(out)/"archive");
    const auto control=ebrp::verifySolution(in,{},lambda);
    if(!control.feasible||!archive->archive.verified)throw std::runtime_error("unverified micro witnesses");
    ebrp::CanonicalCompactModelSpec spec;spec.strengthened=spec.interval_restricted=spec.add_verified_incumbent_row=true;
    spec.verified_incumbent=control.objective;spec.gamma_L=0;spec.gamma_U=std::min(control.objective,double(in.V-1)/in.V);
    spec.round51_subset_duration_big_m="off";
    auto artifact=ebrp::writeCanonicalCompactModel(in,options,std::filesystem::path(out)/"model.lp",spec);
    if(!artifact.written)throw std::runtime_error(artifact.failure_reason);
    ebrp::Round62CoverageSnapshot s;s.control_ub=s.request_cutoff=control.objective;s.archive_ub=archive->archive.objective;
    s.archive_verified=s.root_coverage=s.tree_coverage=true;s.root_upper=spec.gamma_U;s.active_leaf="micro";s.model_identity=artifact.sha256;
    ebrp::ControllingLeaf leaf;leaf.id="micro";leaf.gamma_U=spec.gamma_U;leaf.cutoff=control.objective;s.leaves={leaf};
    ebrp::FixedIntervalMipRequest r;r.solve_kind=ebrp::FixedIntervalSolveKind::PaperTerminalMip;r.leaf_id="micro";
    r.gamma_U=spec.gamma_U;r.verified_cutoff=control.objective;r.canonical_model_path=artifact.path;
    r.canonical_model_fingerprint=artifact.sha256;r.canonical_row_signature=artifact.row_signature;r.canonical_model_scope=artifact.model_scope;
    r.native_log_path=std::filesystem::path(out)/"native.log";r.interval_mip_policy="interval-mip-core-no-exhaustive-subset-duration";
    r.capture_native_bound_events=true;r.global_deadline_remaining_seconds=cap-2-std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    int checks=0;r.round62_external_stop=[s,&checks](double b){++checks;return ebrp::evaluateRound62Passive(s,b).certified;};
    auto backend=ebrp::makeGurobiFixedIntervalBackend(in,options);auto result=backend->solve(r);backend->release();
    auto cert=ebrp::evaluateRound62Passive(s,result.native_bound);
    const auto witness=ebrp::verifySolution(in,archive->archive.routes,lambda);
    const bool accepted=cert.certified&&result.solver_finalization_reached&&result.model_fingerprint_matches_request&&
        result.exact_zero_gap_roundtrip&&result.round62_numeric_valid&&result.native_bound_available&&witness.feasible&&
        witness.original_objective_recomputed&&std::abs(witness.objective-archive->archive.objective)<=1e-7;
    std::ofstream f(std::filesystem::path(out)/"micro_result.json");f<<std::setprecision(17)
        <<"{\"native_status\":\""<<result.native_status<<"\",\"native_optimal\":"<<result.optimal
        <<",\"external_requested\":"<<result.round62_external_termination_requested<<",\"external_certified\":"<<accepted
        <<",\"native_incumbent\":"<<result.incumbent_available<<",\"checks\":"<<checks<<",\"LB\":"<<result.native_bound
        <<",\"archive_UB\":"<<s.archive_ub<<",\"control_UB\":"<<s.control_ub<<",\"optimizer_calls\":1}\n";
    std::cout<<result.native_status<<" external="<<accepted<<" requested="<<result.round62_external_termination_requested<<'\n';
    return accepted?0:1;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
