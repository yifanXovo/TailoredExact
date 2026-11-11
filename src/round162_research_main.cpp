#include "Round162PhysicalCompletion.hpp"
#include "Round138Research.hpp"
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
#include <algorithm>
#ifdef _WIN32
#include <windows.h>
#endif

using namespace ebrp;
int main(int argc,char** argv){try{
    if(argc!=15)throw std::runtime_error("Round162Research input T tp td lambda parent out S|F export|LP|MIP|completion seconds nodes lower upper(-1=natural) saved_values(-=none)");
    const auto began=std::chrono::steady_clock::now();const double cap=std::stod(argv[10]);
    auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count();};
    auto in=parseInstanceFile(argv[1],std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]));
    SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.lambda=std::stod(argv[5]);opt.round98_state_service="m-binary";
    opt.algorithm_preset="research-round83-vds-equal-net-exchange";opt.method="gcap-frontier";
    opt.round68_verified_start=true;opt.gurobi_seed=0;opt.gurobi_threads=1;
    opt.process_start_time=began;opt.process_start_time_valid=true;
    round127().mode="ms2";round137Apply(opt,"ms2");round138().stock_rlt=true;
    round162().active=true;round162().development_node_limit=std::stod(argv[11]);
    const bool no_time=std::string(argv[8])=="F-no-time";
    const bool full=std::string(argv[8])=="F"||no_time,compact=std::string(argv[8])=="C";const std::string mode=argv[9];
    if(!full&&!compact&&std::string(argv[8])!="S")throw std::runtime_error("unknown formulation");
    if(mode!="export"&&mode!="LP"&&mode!="MIP"&&mode!="completion")throw std::runtime_error("unknown mode");
    std::filesystem::path dir(argv[7]);if(!std::filesystem::create_directories(dir))throw std::runtime_error("output must be new");
    std::ifstream f(argv[6]);int count=0;f>>count;std::vector<RoutePlan> routes;
    for(int k=0;k<count;++k){RoutePlan r;int n=0;f>>r.vehicle>>n;if(n<2)throw std::runtime_error("parent nodes");r.nodes.resize(n);for(int& i:r.nodes)f>>i;
        for(int j=1;j+1<n;++j){int delta=0;f>>delta;r.operations.push_back({r.nodes[j],std::max(0,delta),std::max(0,-delta)});}routes.push_back(r);}
    if(!f)throw std::runtime_error("parent read");
    const auto parent=verifySolution(in,routes,opt.lambda);
    if(!parent.feasible)throw std::runtime_error("parent infeasible");
    const double cutoff=std::nextafter(parent.objective,std::numeric_limits<double>::infinity());
    const double gmax=std::nextafter(double(in.V-1)/in.V,std::numeric_limits<double>::infinity());
    const double gl=std::stod(argv[12]),natural=std::min(gmax,cutoff);
    const double gu=std::stod(argv[13])<0?natural:std::stod(argv[13]);
    if(!(0<=gl&&gl<=gu&&gu<=natural))throw std::runtime_error("scope bounds");
    CanonicalCompactModelSpec spec;spec.strengthened=spec.interval_restricted=spec.add_verified_incumbent_row=true;
    spec.gamma_L=gl;spec.gamma_U=gu;spec.verified_incumbent=cutoff;spec.incumbent_epsilon=0;
    spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    auto original=writeCanonicalCompactModel(in,opt,dir/"original.lp",spec);if(!original.written)throw std::runtime_error(original.failure_reason);
    auto artifact=buildRound162Completion(in,original.path,dir/"model.lp",full,no_time);
    double source_seconds=0,project_seconds=0;bool source_qualified=false;
    if(compact){
        std::filesystem::path source_dir(argv[14]);
        if(source_dir=="paid"){
            source_dir=dir/"source";std::filesystem::create_directories(source_dir);const double tick=elapsed();
            const auto source_art=buildRound162Completion(in,original.path,source_dir/"model.lp",true);
            auto source_options=opt;source_options.native_evidence_dir=(source_dir/"journal").string();
            auto source_journal=std::make_shared<NativeEvidenceJournal>(in,source_options);source_journal->witness(routes,"same_own_H_parent");
            auto source_backend=makeGurobiFixedIntervalBackend(in,source_options);FixedIntervalMipRequest r;
            r.solve_kind=FixedIntervalSolveKind::PaperLpRelaxation;r.leaf_id="R162_once_root_source";r.gamma_L=gl;r.gamma_U=gu;r.verified_cutoff=cutoff;
            r.canonical_model_path=source_dir/"model.lp";r.canonical_model_fingerprint=source_art.sha256;r.canonical_row_signature=source_art.row_signature;
            r.canonical_model_scope="full_original_J_inclusive_improvement_domain";r.native_log_path=source_dir/"native.log";
            r.time_limit_seconds=r.global_deadline_remaining_seconds=std::max(0.,cap-elapsed()-2);r.interval_mip_policy="round55-vd-p";
            r.capture_lp_primal_dual_evidence=true;r.capture_native_bound_events=true;r.native_evidence=source_journal;
            auto& s=r.native_evidence_scope;s.leaf=r.leaf_id;s.model_path=r.canonical_model_path.string();s.model_sha256=source_art.sha256;s.model_scope=r.canonical_model_scope;
            s.native_log_path=r.native_log_path.string();s.lower_g=gl;s.upper_g=gu;s.cutoff=cutoff;s.gmax=gmax;s.cover.push_back({r.leaf_id,"same_matrix_complete_native",gl,gu,0,cutoff});
            const auto out=source_backend->solve(r);source_backend->release();saveRound162LpEvidence(out,source_dir);
            source_qualified=out.native_status=="OPTIMAL"&&out.lp_primal_dual_evidence_available&&out.lp_constraint_evidence_available&&out.native_bound_available&&source_journal->proofUsable();
            source_seconds=elapsed()-tick;
            std::ofstream receipt(source_dir/"source_outcome.json");receipt<<std::setprecision(17)<<std::boolalpha<<"{\"status\":"<<std::quoted(out.native_status)<<",\"qualified\":"<<source_qualified
                <<",\"raw_lower\":"<<out.native_bound<<",\"diagnostic_only_lower\":true,\"runtime\":"<<out.solver_runtime_seconds<<",\"work\":"<<out.work<<",\"iterations\":"<<out.simplex_iterations
                <<",\"rows\":"<<out.model_linear_constraint_count<<",\"cols\":"<<out.model_variable_count<<",\"nonzeros\":"<<out.model_nonzero_count<<",\"seconds\":"<<source_seconds<<",\"failure\":"<<std::quoted(out.failure_reason)<<"}\n";
        }else{
            std::ifstream f(source_dir/"outcome.json");std::string text((std::istreambuf_iterator<char>(f)),{});
            source_qualified=text.find("\"status\":\"OPTIMAL\"")!=std::string::npos&&text.find("\"LP_primal_dual_available\":true")!=std::string::npos
                &&text.find("\"LP_duals_available\":true")!=std::string::npos&&text.find("\"global_floor_available\":true")!=std::string::npos;
            if(!source_qualified)throw std::runtime_error("saved full-Q source not qualified");
        }
        if(source_qualified){const double tick=elapsed();artifact=projectRound162Completion(dir/"model.lp",source_dir/"model.lp",source_dir/"lp_duals.jsonl",dir/"model.lp");project_seconds=elapsed()-tick;}
    }
    const double built=elapsed();auto domain=round162Domain(original.path);
    auto start=mapVerifiedRoutesToCanonicalModel(in,opt,routes,"offline_own_H",gl,gu,cutoff,domain);
    if(!start.complete)throw std::runtime_error("Start:"+start.failure_reason);
    auto point=round162ExtendStart(dir/"model.lp",domain,start.values);auto extended=round162Domain(dir/"model.lp");
    const double residual=round162PointResidual(dir/"model.lp",point);
    {std::ofstream s(dir/"start.json");s<<std::setprecision(17)<<'{';for(size_t j=0;j<extended.names.size();++j){if(j)s<<',';s<<std::quoted(extended.names[j])<<':'<<point[j];}s<<"}\n";}
    {std::ofstream s(dir/"admission.json");s<<std::setprecision(17)<<"{\"parent_J\":"<<parent.objective<<",\"G\":"<<parent.G<<",\"P\":"<<parent.P<<",\"cutoff\":"<<cutoff<<",\"gamma_L\":"<<gl<<",\"gamma_U\":"<<gu<<",\"Start_residual\":"<<residual<<",\"Start_complete\":true,\"build_seconds\":"<<built<<",\"Start_registry_readback_seconds\":"<<elapsed()-built<<"}\n";}
    if(residual>1e-6)throw std::runtime_error("Start full matrix residual");
#ifdef _WIN32
    {char path[MAX_PATH]={};auto module=GetModuleHandleA("gurobi130.dll");if(!module||!GetModuleFileNameA(module,path,MAX_PATH))throw std::runtime_error("actual DLL binding");
        std::ofstream s(dir/"runtime_binding.json");s<<"{\"OS_loaded_DLL\":"<<std::quoted(std::filesystem::path(path).generic_string())<<",\"SHA256\":"<<std::quoted(fileSha256(path))<<"}\n";}
#endif
    if(mode=="export")return 0;
    if(mode=="completion"){
        if(!full||std::string(argv[14])=="-")throw std::runtime_error("completion needs saved S point");
        round162FixSavedPoint(dir/"model.lp",argv[14]);artifact.sha256=fileSha256(dir/"model.lp");artifact.row_signature=fileSha256(dir/"actual_rows.jsonl");
    }
    opt.native_evidence_dir=(dir/"journal").string();auto journal=std::make_shared<NativeEvidenceJournal>(in,opt);journal->witness(routes,"same_offline_own_H_parent");
    auto backend=makeGurobiFixedIntervalBackend(in,opt);FixedIntervalMipRequest req;
    const bool lp=mode!="MIP";req.solve_kind=lp?FixedIntervalSolveKind::PaperLpRelaxation:FixedIntervalSolveKind::PaperTerminalMip;
    req.leaf_id="R162_complete_root";req.gamma_L=gl;req.gamma_U=gu;req.verified_cutoff=cutoff;
    req.canonical_model_path=dir/"model.lp";req.canonical_model_fingerprint=artifact.sha256;req.canonical_row_signature=artifact.row_signature;
    req.canonical_model_scope=mode=="completion"?"fixed_saved_S_point_diagnostic":"full_original_J_inclusive_improvement_domain";
    req.native_log_path=dir/"native.log";req.time_limit_seconds=req.global_deadline_remaining_seconds=std::max(0.,cap-elapsed()-2);
    // Expanded Starts are checked above. Formal projected models have no new columns.
    req.round68_verified_start=!lp&&!full;req.verified_start_routes=routes;req.verified_start_source="offline_own_H";
    req.interval_mip_policy="round55-vd-p";req.capture_native_bound_events=true;req.capture_lp_primal_dual_evidence=lp;
    // A fixed fractional point need not contain the physical parent. Do not
    // apply the original-domain witness/cover qualifier to this diagnostic.
    if(mode!="completion")req.native_evidence=journal;
    auto& scope=req.native_evidence_scope;scope.leaf=req.leaf_id;
    scope.model_path=req.canonical_model_path.string();scope.model_sha256=artifact.sha256;scope.model_scope=req.canonical_model_scope;
    scope.native_log_path=req.native_log_path.string();scope.lower_g=gl;scope.upper_g=gu;scope.cutoff=cutoff;scope.gmax=gmax;
    if(mode!="completion")scope.cover.push_back({req.leaf_id,"same_matrix_complete_native",gl,gu,0,cutoff});
    const double prepared=elapsed();auto out=backend->solve(req);backend->release();
    {std::ofstream s(dir/"progress.csv");s<<std::setprecision(17)<<"time,work,nodes,raw_lower,available,native_upper\n";for(const auto& e:out.native_bound_events)s<<e.solver_runtime_seconds<<','<<e.work<<','<<e.processed_nodes<<','<<e.native_bound<<','<<e.native_bound_available<<','<<e.native_incumbent<<'\n';}
    double point_residual=0,objective=0;
    if(lp&&out.lp_primal_values_available){saveRound162LpEvidence(out,dir);
        std::map<std::string,double> values;for(const auto& e:out.lp_primal_dual_variable_evidence)values[e.name]=e.primal_value;
        std::vector<double> x;for(const auto& n:round162Domain(dir/"model.lp").names)x.push_back(values.at(n));point_residual=round162PointResidual(dir/"model.lp",x,false);objective=out.lp_objective_value;}
    const bool usable=out.native_bound_available&&journal->proofUsable()&&mode!="completion";
    std::ofstream s(dir/"outcome.json");s<<std::setprecision(17)<<std::boolalpha<<"{\"formulation\":\""<<argv[8]<<"\",\"mode\":\""<<mode<<"\",\"status\":"<<std::quoted(out.native_status)<<",\"failure\":"<<std::quoted(out.failure_reason)
        <<",\"available\":"<<out.available<<",\"optimal\":"<<out.optimal<<",\"bound_available\":"<<out.native_bound_available<<",\"raw_lower\":"<<out.native_bound<<",\"qualified_restricted_lower\":"<<out.native_bound
        <<",\"global_floor_available\":"<<usable<<",\"global_transported_floor\":"<<std::min(out.native_bound,cutoff)<<",\"physical_U\":"<<journal->bestObjective()<<",\"proof_usable\":"<<journal->proofUsable()<<",\"source_rejected\":"<<journal->sourceRejected()
        <<",\"LP_primal_dual_available\":"<<out.lp_primal_dual_evidence_available<<",\"LP_duals_available\":"<<out.lp_constraint_duals_available<<",\"LP_objective\":"<<objective<<",\"LP_point_residual\":"<<point_residual
        <<",\"runtime\":"<<out.solver_runtime_seconds<<",\"work\":"<<out.work<<",\"nodes\":"<<out.nodes<<",\"iterations\":"<<out.simplex_iterations<<",\"outer_seconds\":"<<elapsed()<<",\"pre_native_seconds\":"<<prepared
        <<",\"source_seconds\":"<<source_seconds<<",\"project_seconds\":"<<project_seconds<<",\"source_qualified\":"<<source_qualified
        <<",\"rows\":"<<out.model_linear_constraint_count<<",\"cols\":"<<out.model_variable_count<<",\"nonzeros\":"<<out.model_nonzero_count<<",\"binaries\":"<<out.model_binary_variable_count<<",\"integers\":"<<out.model_integer_variable_count<<",\"continuous\":"<<out.model_continuous_variable_count
        <<",\"min_coefficient\":"<<out.minimum_matrix_coefficient<<",\"max_coefficient\":"<<out.maximum_matrix_coefficient<<",\"presolved_rows\":"<<out.presolved_row_count<<",\"presolved_cols\":"<<out.presolved_column_count
        <<",\"Start_submitted\":"<<out.warm_start_submitted<<",\"Start_status\":"<<std::quoted(out.warm_start_status)<<",\"model_matches\":"<<out.model_fingerprint_matches_request<<",\"zero_gaps\":"<<out.exact_zero_gap_roundtrip<<",\"feasibility_gate\":"<<out.feasibility_consistency_gate<<"}\n";
    std::cout<<argv[8]<<' '<<mode<<' '<<out.native_status<<" LP="<<objective<<" L="<<out.native_bound<<" residual="<<point_residual<<" failure="<<out.failure_reason<<'\n';
    return (out.available||(mode=="completion"&&out.infeasible))?0:2;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
