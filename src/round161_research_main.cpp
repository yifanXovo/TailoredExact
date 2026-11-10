#include "Round161NativeRN.hpp"
#include "Round127Research.hpp"
#include "PaperK1AmSf.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "Evaluator.hpp"
#include "Parser.hpp"
#include "FileSha256.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <chrono>

using namespace ebrp;
int main(int argc,char** argv) {try {
    if(argc!=12)throw std::runtime_error("Round161Research input T tp td lambda parent out OLD|RN export|LP|MIP seconds nodes(-1=unlimited)");
    const auto began=std::chrono::steady_clock::now();const double cap=std::stod(argv[10]);
    auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count();};
    auto in=parseInstanceFile(argv[1],std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]));
    SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.lambda=std::stod(argv[5]);opt.round98_state_service="m-binary";
    opt.algorithm_preset="research-round83-vds-equal-net-exchange";opt.method="gcap-frontier";
    opt.round68_verified_start=true;opt.gurobi_seed=0;opt.gurobi_threads=1;
    opt.process_start_time=began;opt.process_start_time_valid=true;
    round127().mode="ms2";round137Apply(opt,"ms2");round161().active=true;
    round161().development_node_limit=std::stod(argv[11]);
    const bool rn=std::string(argv[8])=="RN";const std::string mode=argv[9];
    if(!rn&&std::string(argv[8])!="OLD")throw std::runtime_error("unknown formulation");
    if(mode!="export"&&mode!="LP"&&mode!="MIP")throw std::runtime_error("unknown solve mode");
    std::filesystem::path dir(argv[7]);if(!std::filesystem::create_directories(dir))throw std::runtime_error("output must be new");
    std::ifstream f(argv[6]);int count=0;f>>count;std::vector<RoutePlan> routes;
    for(int k=0;k<count;++k){RoutePlan r;int n=0;f>>r.vehicle>>n;if(n<2)throw std::runtime_error("parent nodes");r.nodes.resize(n);for(int& i:r.nodes)f>>i;
        for(int j=1;j+1<n;++j){int delta=0;f>>delta;r.operations.push_back({r.nodes[j],std::max(0,delta),std::max(0,-delta)});}routes.push_back(r);}
    if(!f)throw std::runtime_error("parent read");const auto parent=verifySolution(in,routes,opt.lambda);
    if(!parent.feasible)throw std::runtime_error("parent infeasible");
    const double cutoff=std::nextafter(parent.objective,std::numeric_limits<double>::infinity());
    const double gmax=std::nextafter(double(in.V-1)/in.V,std::numeric_limits<double>::infinity());
    const double gu=std::min(gmax,cutoff);
    CanonicalCompactModelSpec spec;spec.strengthened=spec.interval_restricted=spec.add_verified_incumbent_row=true;
    spec.gamma_L=0;spec.gamma_U=gu;spec.verified_incumbent=cutoff;spec.incumbent_epsilon=0;
    spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    auto old=writeCanonicalCompactModel(in,opt,dir/"original.lp",spec);if(!old.written)throw std::runtime_error(old.failure_reason);
    auto art=replaceRound161Objective(in,old.path,dir/"model.lp",rn,gu);
    auto domain=round161Domain(dir/"model.lp");
    auto start=mapVerifiedRoutesToCanonicalModel(in,opt,routes,"offline_own_H",0,gu,cutoff,domain);
    if(!start.complete)throw std::runtime_error("Start:"+start.failure_reason);
    const double residual=round161StartResidual(dir/"model.lp",start.values);
    {std::ofstream s(dir/"start.json");s<<std::setprecision(17)<<'{';for(size_t j=0;j<domain.names.size();++j){if(j)s<<',';s<<std::quoted(domain.names[j])<<':'<<start.values[j];}s<<"}\n";}
    {std::ofstream s(dir/"admission.json");s<<std::setprecision(17)<<"{\"parent_J\":"<<parent.objective<<",\"G\":"<<parent.G<<",\"P\":"<<parent.P<<",\"cutoff\":"<<cutoff<<",\"gamma_U\":"<<gu<<",\"Start_residual\":"<<residual<<",\"Start_complete\":true,\"build_seconds\":"<<elapsed()<<"}\n";}
    if(residual>1e-6)throw std::runtime_error("Start matrix residual");
    if(mode=="export")return 0;
    opt.native_evidence_dir=(dir/"journal").string();
    auto journal=std::make_shared<NativeEvidenceJournal>(in,opt);journal->witness(routes,"same_own_H_parent");
    auto backend=makeGurobiFixedIntervalBackend(in,opt);
    FixedIntervalMipRequest req;req.solve_kind=mode=="LP"?FixedIntervalSolveKind::PaperLpRelaxation:FixedIntervalSolveKind::PaperTerminalMip;
    req.leaf_id="R161_complete_root";req.gamma_L=0;req.gamma_U=gu;req.verified_cutoff=cutoff;
    req.canonical_model_path=dir/"model.lp";req.canonical_model_fingerprint=art.sha256;req.canonical_row_signature=art.row_signature;
    req.canonical_model_scope="full_original_J_inclusive_improvement_domain";
    req.native_log_path=dir/"native.log";req.time_limit_seconds=req.global_deadline_remaining_seconds=std::max(0.,cap-elapsed()-2);
    req.round68_verified_start=mode=="MIP";req.verified_start_routes=routes;req.verified_start_source="offline_own_H";
    req.interval_mip_policy="round55-vd-p";req.capture_native_bound_events=true;req.capture_lp_primal_dual_evidence=mode=="LP";
    req.native_evidence=journal;auto& scope=req.native_evidence_scope;scope.leaf=req.leaf_id;
    scope.model_path=req.canonical_model_path.string();scope.model_sha256=art.sha256;scope.model_scope=req.canonical_model_scope;
    scope.native_log_path=req.native_log_path.string();scope.lower_g=0;scope.upper_g=gu;scope.cutoff=cutoff;scope.gmax=gmax;
    // Complete true-G improvement region; objective complement >= cutoff.
    scope.cover.push_back({req.leaf_id,"same_matrix_complete_native",0,gu,0,cutoff});
    auto out=backend->solve(req);backend->release();
    {std::ofstream s(dir/"progress.csv");s<<std::setprecision(17)<<"time,work,nodes,raw_lower,available,native_upper\n";
        for(const auto& e:out.native_bound_events)s<<e.solver_runtime_seconds<<','<<e.work<<','<<e.processed_nodes<<','<<e.native_bound<<','<<e.native_bound_available<<','<<e.native_incumbent<<'\n';}
    if(mode=="LP") {std::ofstream s(dir/"lp_values.json");s<<std::setprecision(17)<<'{';bool first=true;
        for(const auto& v:out.lp_primal_dual_variable_evidence){if(!first)s<<',';first=false;s<<std::quoted(v.name)<<':'<<v.primal_value;}s<<"}\n";}
    std::ofstream s(dir/"outcome.json");s<<std::setprecision(17)<<std::boolalpha<<"{\"formulation\":\""<<argv[8]<<"\",\"mode\":\""<<mode
        <<"\",\"status\":"<<std::quoted(out.native_status)<<",\"failure\":"<<std::quoted(out.failure_reason)<<",\"available\":"<<out.available
        <<",\"bound_available\":"<<out.native_bound_available<<",\"qualified_lower\":"<<out.native_bound
        <<",\"physical_U\":"<<journal->bestObjective()<<",\"proof_usable\":"<<journal->proofUsable()<<",\"source_rejected\":"<<journal->sourceRejected()
        <<",\"runtime\":"<<out.solver_runtime_seconds<<",\"work\":"<<out.work<<",\"nodes\":"<<out.nodes<<",\"outer_seconds\":"<<elapsed()
        <<",\"rows\":"<<out.model_linear_constraint_count<<",\"cols\":"<<out.model_variable_count<<",\"nonzeros\":"<<out.model_nonzero_count
        <<",\"binaries\":"<<out.model_binary_variable_count<<",\"integers\":"<<out.model_integer_variable_count<<",\"continuous\":"<<out.model_continuous_variable_count
        <<",\"min_coefficient\":"<<out.minimum_matrix_coefficient<<",\"max_coefficient\":"<<out.maximum_matrix_coefficient
        <<",\"presolved_available\":"<<out.presolved_model_size_available<<",\"presolved_rows\":"<<out.presolved_row_count<<",\"presolved_cols\":"<<out.presolved_column_count
        <<",\"presolved_nonzeros\":"<<out.presolved_nonzero_count<<",\"Start_submitted\":"<<out.warm_start_submitted<<",\"Start_status\":"<<std::quoted(out.warm_start_status)
        <<",\"model_matches\":"<<out.model_fingerprint_matches_request<<",\"zero_gaps\":"<<out.exact_zero_gap_roundtrip<<",\"feasibility_gate\":"<<out.feasibility_consistency_gate<<"}\n";
    std::cout<<argv[8]<<' '<<mode<<' '<<out.native_status<<" U="<<journal->bestObjective()<<" L="<<out.native_bound<<" nodes="<<out.nodes<<" failure="<<out.failure_reason<<'\n';
    return out.available?0:2;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
