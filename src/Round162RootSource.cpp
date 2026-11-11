#include "Round162PhysicalCompletion.hpp"
#include "FileSha256.hpp"
#include "NativeEvidenceJournal.hpp"
#include "Round153Research.hpp"
#include "Round154Research.hpp"
#include <fstream>
#include <iomanip>
#include <regex>
#include <chrono>
#include <algorithm>

namespace ebrp {
namespace {
using Clock=std::chrono::steady_clock;
void require(bool ok,const std::string& why){if(!ok)throw std::runtime_error("round162_"+why);}
void inheritProofOnlyRegistry(const std::string& base,const std::string& added){
    if(!round153().enabled)return;
    require(round154Enabled(),"helper_must_remain_proof_only");
    const auto it=round153().expected.find(base);
    require(it!=round153().expected.end()&&it->second.empty(),"proof_only_registry");
    round153().expected.emplace(added,it->second);
}
std::map<std::string,size_t> indices(const SolverNeutralModelDomain& d){
    std::map<std::string,size_t> out;
    for(size_t j=0;j<d.names.size();++j)require(out.emplace(d.names[j],j).second,"duplicate_scope_column");
    return out;
}
void scopeReceipt(const std::filesystem::path& output,bool applied,const std::string& reason,double cutoff){
    std::ofstream f(output.string()+".scope.json");f<<std::setprecision(17)<<std::boolalpha
        <<"{\"applied\":"<<applied<<",\"reason\":"<<std::quoted(reason)<<",\"cutoff\":"<<cutoff
        <<",\"root_input_SHA256\":"<<std::quoted(round162().input_sha)<<",\"root_source_SHA256\":"<<std::quoted(round162().source_sha)<<"}\n";
    require(bool(f),"scope_receipt_write");
}
}
CanonicalCompactModelArtifact embedRound162Row(const Instance& in,const CanonicalCompactModelArtifact& base,double cutoff,
        const std::filesystem::path& output){
    auto& c=round162();if(!c.enabled||!c.ready)return base;
    require(base.written&&fileSha256(base.path)==base.sha256,"base_identity");
    require(c.input_sha==fileSha256(in.path),"input_scope_changed");
    auto child=round162Domain(base.path);auto ci=indices(child),ri=indices(c.root_domain);
    std::string reason;Round162Row row=c.row;
    if(cutoff>c.cutoff)reason="cutoff_not_covered";
    const auto gj=ci.at("G");
    if(child.lower_bounds[gj]<c.lower||child.upper_bounds[gj]>c.upper)reason="G_interval_not_covered";
    const std::regex state("state_([0-9]+)_([0-9]+)");
    for(size_t j=0;j<child.names.size()&&reason.empty();++j)if(std::regex_match(child.names[j],state)&&child.upper_bounds[j]>0){
        const auto it=ri.find(child.names[j]);
        if(it==ri.end()||c.root_domain.upper_bounds[it->second]<=0)reason="selector_support_not_covered";
    }
    for(auto it=row.coefficients.begin();it!=row.coefficients.end()&&reason.empty();){
        auto j=ci.find(it->first);const auto root=ri.at(it->first);
        if(j==ci.end()){
            // Missing selector/moment coordinates in a smaller legal support
            // are exactly zero. No other physical coordinate is discarded.
            if(it->first.rfind("state_",0)==0||it->first.rfind("state_g_",0)==0){it=row.coefficients.erase(it);continue;}
            reason="physical_column_missing";break;
        }
        if(child.lower_bounds[j->second]<c.root_domain.lower_bounds[root]||child.upper_bounds[j->second]>c.root_domain.upper_bounds[root])reason="finite_box_not_covered";
        ++it;
    }
    if(!reason.empty()){
        ++c.scope_skips;c.expected_without_row.insert(base.sha256);scopeReceipt(output,false,reason,cutoff);return base;
    }
    if(row.coefficients.empty()&&row.rhs>=0){c.expected_without_row.insert(base.sha256);scopeReceipt(output,false,"true_constant_projection",cutoff);return base;}
    auto added=appendRound162Row(base.path,output,row);auto out=base;
    out.path=output;out.sha256=added.sha256;out.row_signature+="|round162:"+out.sha256;
    out.model_scope+="_round162_PC";++out.rows;out.nonzeros+=row.coefficients.size();
    inheritProofOnlyRegistry(base.sha256,out.sha256);
    c.expected.emplace(out.sha256,std::move(row));++c.embeddings;scopeReceipt(output,true,"covered_root_subdomain",cutoff);return out;
}
CanonicalCompactModelArtifact prepareRound162Root(const Instance& in,const SolveOptions& options,
        const CanonicalCompactModelArtifact& base,double cutoff,const std::vector<RoutePlan>& routes,
        const std::filesystem::path& directory,const std::function<double()>& remaining){
    auto& c=round162();require(c.enabled&&!c.attempted,"once_root_lifecycle");c.attempted=true;
    c.input_sha=fileSha256(in.path);c.cutoff=cutoff;c.root_domain=round162Domain(base.path);
    auto ix=indices(c.root_domain);c.lower=c.root_domain.lower_bounds[ix.at("G")];c.upper=c.root_domain.upper_bounds[ix.at("G")];
    require(std::filesystem::create_directories(directory),"source_directory_collision");
    if(c.lower==c.upper){
        std::ofstream f(directory/"source.json");f<<"{\"applicable\":false,\"reason\":\"collapsed_G_interval_exact_product_identity\",\"source_calls\":0,\"PC\":false}\n";return base;
    }
    const auto began=Clock::now();const auto src=buildRound162Completion(in,base.path,directory/"model.lp",true);c.source_sha=src.sha256;
    inheritProofOnlyRegistry(base.sha256,src.sha256);
    SolveOptions source_options=options;source_options.native_evidence_dir=(directory/"journal").string();
    auto journal=std::make_shared<NativeEvidenceJournal>(in,source_options);journal->witness(routes,"same_run_own_H_root_parent");
    FixedIntervalMipOutcome out;
    if(remaining()>0){
        FixedIntervalMipRequest r;r.interval_mip_policy=options.external_gini_interval_mip_policy;
        r.solve_kind=FixedIntervalSolveKind::PaperLpRelaxation;r.leaf_id="round162_disposable_root";
        r.gamma_L=base.gamma_L;r.gamma_U=base.gamma_U;r.verified_cutoff=cutoff;r.new_leaf=true;
        r.canonical_model_path=directory/"model.lp";r.canonical_model_fingerprint=src.sha256;r.canonical_row_signature=src.row_signature;
        r.canonical_model_scope="round162_complete_original_J_root_source_diagnostic_lower_only";
        r.native_log_path=directory/"native.log";r.capture_lp_primal_dual_evidence=true;r.capture_native_bound_events=true;
        r.time_limit_seconds=r.global_deadline_remaining_seconds=remaining();r.native_evidence=journal;
        auto& s=r.native_evidence_scope;s.leaf=r.leaf_id;s.model_path=r.canonical_model_path.string();s.model_sha256=src.sha256;s.model_scope=r.canonical_model_scope;
        s.native_log_path=r.native_log_path.string();s.lower_g=base.gamma_L;s.upper_g=base.gamma_U;s.cutoff=cutoff;s.gmax=double(in.V-1)/in.V;
        s.cover.push_back({r.leaf_id,"same_matrix_complete_native",base.gamma_L,base.gamma_U,0,cutoff});
        struct SourceScope{SourceScope(){round162().source_running=true;}~SourceScope(){round162().source_running=false;}} scope;
        auto backend=makeGurobiFixedIntervalBackend(in,source_options);++c.source_calls;out=backend->solve(r);backend->release();
    }
    saveRound162LpEvidence(out,directory);c.source_seconds=std::chrono::duration<double>(Clock::now()-began).count();
    const bool qualified=out.lp_terminal_valid&&out.optimal&&out.native_bound_available&&out.exact_zero_gap_roundtrip&&out.model_fingerprint_matches_request&&
        out.feasibility_consistency_gate&&out.solver_finalization_reached&&out.optimize_return_code==0&&out.failure_reason=="none"&&
        out.lp_primal_dual_evidence_available&&out.lp_constraint_evidence_available&&journal->proofUsable();
    if(qualified&&remaining()>0){const auto project_began=Clock::now();
        std::filesystem::create_directories(directory/"compact");
        projectRound162Completion(base.path,directory/"model.lp",directory/"lp_duals.jsonl",directory/"compact/model.lp",&c.row);
        c.project_seconds=std::chrono::duration<double>(Clock::now()-project_began).count();c.ready=c.row.active&&remaining()>0;
    }
    std::ofstream f(directory/"source.json");f<<std::setprecision(17)<<std::boolalpha<<"{\"qualified\":"<<qualified<<",\"source_calls\":"<<c.source_calls
        <<",\"status\":"<<std::quoted(out.native_status)<<",\"failure\":"<<std::quoted(out.failure_reason)<<",\"raw_lower\":"<<out.native_bound
        <<",\"qualified_restricted_lower_available\":"<<(qualified&&out.native_bound_available)<<",\"qualified_restricted_lower\":"<<out.native_bound
        <<",\"diagnostic_global_transport\":"<<std::min(out.native_bound,cutoff)<<",\"lower_consumed_by_formal_ledger\":false,\"primal_consumed\":false"
        <<",\"source_seconds\":"<<c.source_seconds<<",\"project_seconds\":"<<c.project_seconds<<",\"Runtime\":"<<out.solver_runtime_seconds<<",\"Work\":"<<out.work
        <<",\"iterations\":"<<out.simplex_iterations<<",\"nodes\":"<<out.nodes<<",\"source_SHA256\":"<<std::quoted(c.source_sha)<<",\"input_SHA256\":"<<std::quoted(c.input_sha)
        <<",\"lower_G\":"<<c.lower<<",\"upper_G\":"<<c.upper<<",\"cutoff\":"<<c.cutoff<<",\"PC_ready\":"<<c.ready<<",\"released\":true,\"formal_new_columns\":0}\n";
    require(bool(f),"source_receipt_write");
    return c.ready?embedRound162Row(in,base,cutoff,base.path.parent_path()/(base.path.stem().string()+"_round162_PC.lp")):base;
}
void finishRound162Run(const std::filesystem::path& directory){
    if(!round162().enabled)return;
    const auto& c=round162();
    std::ofstream f(directory/"round162_run.json");f<<std::setprecision(17)<<std::boolalpha<<"{\"enabled\":true,\"attempted\":"<<c.attempted<<",\"ready\":"<<c.ready
        <<",\"source_calls\":"<<c.source_calls<<",\"source_seconds\":"<<c.source_seconds<<",\"project_seconds\":"<<c.project_seconds<<",\"embeddings\":"<<c.embeddings
        <<",\"scope_skips\":"<<c.scope_skips<<",\"source_lower_formal_floor\":false,\"formal_new_columns\":0,\"root_source_SHA256\":"<<std::quoted(c.source_sha)<<"}\n";
}
}
