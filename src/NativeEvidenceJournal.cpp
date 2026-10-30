#include "NativeEvidenceJournal.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "ProcessPhaseLedger.hpp"
#include "Round141Research.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <set>
#include <sstream>
#include <stdexcept>

namespace ebrp {
namespace {
std::string quoted(const std::string& text) {
    std::ostringstream out; out << '"';
    for (unsigned char c : text) {
        if (c=='"' || c=='\\') out << '\\' << c;
        else if (c<32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << unsigned(c);
        else out << c;
    }
    out << '"'; return out.str();
}
bool verified(const Verification& v) {
    return v.original_solution_feasible && v.original_objective_recomputed &&
        v.errors.empty() && std::isfinite(v.objective) && std::isfinite(v.G);
}
std::string scopeJson(const NativeEvidenceScope& s) {
    std::ostringstream o; o << std::setprecision(17);
    o << "\"full_original\":" << s.full_original << ",\"native_preconditions\":" << s.native_preconditions
      << ",\"precondition_reason\":" << quoted(nativeEvidencePreconditionReason(s))
      << ",\"leaf\":" << quoted(s.leaf) << ",\"model_sha256\":" << quoted(s.model_sha256)
      << ",\"model_path\":" << quoted(s.model_path) << ",\"model_scope\":" << quoted(s.model_scope)
      << ",\"native_log_path\":" << quoted(s.native_log_path)
      << ",\"settings\":" << s.settings_json
      << ",\"lower_g\":" << s.lower_g << ",\"upper_g\":" << s.upper_g
      << ",\"cutoff\":" << s.cutoff << ",\"gmax\":" << s.gmax << ",\"cover\":[";
    for (std::size_t i=0;i<s.cover.size();++i) {
        const auto& p=s.cover[i]; if(i)o << ',';
        o << "{\"id\":" << quoted(p.id) << ",\"source\":" << quoted(p.source)
          << ",\"lower_g\":" << p.lower_g << ",\"upper_g\":" << p.upper_g
          << ",\"lower\":" << p.lower << ",\"cutoff\":" << p.cutoff << '}';
    }
    o << ']'; return o.str();
}
void closedWrite(const std::filesystem::path& path,const std::string& text) {
    if(std::filesystem::exists(path)) throw std::runtime_error("immutable journal collision");
    std::ofstream out(path,std::ios::binary); out << text; out.flush();
    if(!out) throw std::runtime_error("journal write failed");
    out.close(); if(out.fail()) throw std::runtime_error("journal close failed");
}
}

std::vector<NativeEvidencePiece> nativeEvidenceCover(const std::vector<ControllingLeaf>& leaves) {
    std::vector<NativeEvidencePiece> out;
    for(const auto& l:leaves) {
        if(l.single_child_contraction_parent && l.strict_infeasible_half_verified)
            out.push_back({l.id+"/infeasible",l.contraction_source,
                l.contracted_infeasible_gamma_L,l.contracted_infeasible_gamma_U,l.cutoff,l.cutoff});
        if(l.parent_replaced || l.status==ControllingLeafStatus::Replaced ||
           l.status==ControllingLeafStatus::Coalesced || l.status==ControllingLeafStatus::Invalid) continue;
        if(!l.parent_child_coverage_valid) continue;
        std::string source=l.closure_source;
        for(const auto& x:l.lower_bound_sources) source += "|"+x;
        if(l.status==ControllingLeafStatus::Empty && l.closure_source.empty()) continue;
        out.push_back({l.id,source,l.gamma_L,l.gamma_U,
            l.status==ControllingLeafStatus::Empty?l.cutoff:l.lower_bound,l.cutoff});
    }
    return out;
}

std::string nativeEvidencePreconditionReason(const NativeEvidenceScope& s) {
    const std::string key="\"qualification_reason\":\"";
    const auto start=s.settings_json.find(key);
    if(start==std::string::npos)return "";
    const auto value=start+key.size(),end=s.settings_json.find('"',value);
    return end==std::string::npos?"parameter_qualification_reason_malformed":s.settings_json.substr(value,end-value);
}
void setNativeEvidencePreconditionReason(NativeEvidenceScope& s,const std::string& reason) {
    if(reason.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_,:;-")!=std::string::npos)
        throw std::invalid_argument("invalid_internal_qualification_reason");
    const std::string key="\"qualification_reason\":\"";
    const auto start=s.settings_json.find(key);
    if(start!=std::string::npos) {
        const auto value=start+key.size(),end=s.settings_json.find('"',value);
        if(end==std::string::npos)throw std::invalid_argument("malformed_internal_settings");
        s.settings_json.replace(value,end-value,reason);return;
    }
    if(s.settings_json.empty()||s.settings_json.back()!='}')throw std::invalid_argument("malformed_internal_settings");
    s.settings_json.pop_back();
    if(s.settings_json!="{")s.settings_json+=',';
    s.settings_json+=key+reason+"\"}";
}

std::string nativeParameterMismatch(const NativeParameterSettings& e,
    const NativeParameterSettings& a, int rc) {
    if(rc) return "parameter_readback_unavailable";
    if(e.seed<0 || e.seed>2000000000 || e.presolve < -1 || e.presolve>2)
        return "parameter_request_outside_declared_support";
    std::string mismatch;
    auto add=[&](bool ok,const char* name){if(!ok){if(!mismatch.empty())mismatch+=",";mismatch+=name;}};
    add(a.threads==e.threads,"Threads");add(a.seed==e.seed,"Seed");
    add(a.presolve==e.presolve,"Presolve");add(a.gap==e.gap,"MIPGap");
    add(a.mip_focus==e.mip_focus,"MIPFocus");add(a.cuts==e.cuts,"Cuts");
    add(a.absolute_gap==e.absolute_gap,"MIPGapAbs");
    add(a.feasibility==e.feasibility,"FeasibilityTol");
    add(a.integrality==e.integrality,"IntFeasTol");
    add(a.optimality==e.optimality,"OptimalityTol");
    return mismatch.empty()?"":"parameter_configuration_mismatch:"+mismatch;
}

NativeEvidenceBound evaluateNativeLocalBound(const NativeEvidenceScope& s,
    double b,const std::vector<Verification>& witnesses,double tol) {
    NativeEvidenceBound out;
    auto reject=[&](const std::string& reason,bool inconsistent=false) {
        out.reason=reason;out.inconsistent=inconsistent;return out;
    };
    std::string count_scope;
    try {count_scope=round141ScopeValue(s.settings_json);round141ScopeContains(count_scope,{});}
    catch(const std::exception&) {return reject("invalid_count_source_domain");}
    if(!std::isfinite(tol)||tol<0||!std::isfinite(s.gmax)||s.gmax<0||s.gmax>=1 ||
       (!s.full_original && (!std::isfinite(s.lower_g)||!std::isfinite(s.upper_g)||
        s.lower_g<0||s.upper_g<s.lower_g||!std::isfinite(s.cutoff)||s.cutoff<0)))
        return reject("invalid_physical_domain");
    if(!std::isfinite(b)||std::fabs(b)>=1e100)return reject("native_bound_unavailable");
    // Do not expand the witness domain by tolerance. Only the objective
    // comparison uses tol; a nearby out-of-domain point cannot refute a call.
    for(const auto& v:witnesses) if(verified(v) &&
        (s.full_original || (v.G>=s.lower_g && v.G<=s.upper_g && v.objective<=s.cutoff)) &&
        (count_scope.empty() || (!v.final_inventory.empty() && round141ScopeContains(count_scope,v.final_inventory))) &&
        b>v.objective+tol)
        return reject("source_bound_witness_contradiction",true);
    if(!s.native_preconditions)
        return reject(nativeEvidencePreconditionReason(s).empty()?"native_model_mapping_not_qualified":nativeEvidencePreconditionReason(s));
    if(s.model_sha256.empty())return reject("native_model_identity_unavailable");
    // The raw restricted claim was checked above. Its objective-cutoff
    // complement has floor c, so the unconditional regional floor is min(b,c).
    out.available=true;out.value=s.full_original?b:std::min(b,s.cutoff);
    out.reason="qualified_local_native_bound";return out;
}
bool nativeEvidenceStatusQualified(int status,int read_return_code) {
    if(read_return_code)return false;
    // Gurobi13 policy: optimal/infeasible and supported resource/user stops.
    // NUMERIC, SUBOPTIMAL and ambiguous/unbounded returns do not qualify.
    return status==2||status==3||(status>=7&&status<=11)||(status>=15&&status<=17);
}
NativeEvidenceBound evaluateNativeLocalScope(const NativeEvidenceScope& s) {
    // No synthetic native bound is introduced by a scope-only check.
    NativeEvidenceBound out;
    try {round141ScopeContains(round141ScopeValue(s.settings_json),{});}
    catch(const std::exception&) {out.reason="invalid_count_source_domain";return out;}
    if(!std::isfinite(s.gmax)||s.gmax<0||s.gmax>=1 ||
       (!s.full_original && (!std::isfinite(s.lower_g)||!std::isfinite(s.upper_g)||
        s.lower_g<0||s.upper_g<s.lower_g||!std::isfinite(s.cutoff)||s.cutoff<0)))
        out.reason="invalid_physical_domain";
    else if(!s.native_preconditions)
        out.reason=nativeEvidencePreconditionReason(s).empty()?"native_model_mapping_not_qualified":nativeEvidencePreconditionReason(s);
    else if(s.model_sha256.empty())out.reason="native_model_identity_unavailable";
    else {out.available=true;out.reason="qualified_local_native_scope";}
    return out;
}
NativeEvidenceBound evaluateNativeLocalInfeasibility(const NativeEvidenceScope& s,
    const std::vector<Verification>& witnesses) {
    const auto count_scope=round141ScopeValue(s.settings_json);
    // Preserve the historical contradiction-before-qualification order when
    // no new count domain is present. Count metadata itself must be valid
    // before it can decide whether a physical witness belongs to this side.
    if(!count_scope.empty()) {
        const auto valid=evaluateNativeLocalScope(s);if(!valid.available)return valid;
    }
    for(const auto& v:witnesses)if(verified(v) && (s.full_original ||
        (v.G>=s.lower_g && v.G<=s.upper_g && v.objective<=s.cutoff)) &&
        (count_scope.empty() || (!v.final_inventory.empty() && round141ScopeContains(count_scope,v.final_inventory)))) {
        NativeEvidenceBound out;out.inconsistent=true;
        out.reason="source_infeasibility_witness_contradiction";return out;
    }
    auto out=evaluateNativeLocalScope(s);
    if(out.available)out.reason="qualified_local_native_infeasibility";
    return out;
}

NativeEvidenceBound evaluateNativeEvidenceBound(const NativeEvidenceScope& s,double b,
    const std::vector<Verification>& witnesses,double tol) {
    NativeEvidenceBound out;
    auto reject=[&](const std::string& reason,bool inconsistent=false) {
        out.reason=reason; out.inconsistent=inconsistent; return out;
    };
    // A count side cannot masquerade as the parent/Gini frontier obligation.
    // Its local evidence is consumed only by the complete pair's floor rows.
    if(s.settings_json.find("\"round141_count_scope\"")!=std::string::npos)
        return reject("count_side_requires_cover_or_conditional_embedding");
    if(!std::isfinite(tol) || tol<0 || !std::isfinite(s.gmax) || s.gmax<0 || s.gmax>=1)
        return reject("invalid_physical_domain");
    double ub=std::numeric_limits<double>::infinity();
    for(const auto& v:witnesses) if(verified(v)) ub=std::min(ub,v.objective);
    const bool has_native=std::isfinite(b);
    if(has_native) {
        const auto local=evaluateNativeLocalBound(s,b,witnesses,tol);
        if(!local.available)return local;
    }
    if(s.full_original) {
        if(!s.native_preconditions || !has_native) return reject("full_native_preconditions_unavailable");
        if(b>ub+tol) return reject("full_bound_witness_inconsistency",true);
        out.available=true;out.value=b;out.reason="full_original_native_callback";return out;
    }
    if(!std::isfinite(s.cutoff) || s.cutoff<0 || !std::isfinite(ub) || s.cutoff+tol<ub)
        return reject("cutoff_without_same_run_physical_witness");
    auto pieces=s.cover;
    bool active=false;
    for(auto& p:pieces) {
        if(!std::isfinite(p.lower_g)||!std::isfinite(p.upper_g)||!std::isfinite(p.lower)||
           !std::isfinite(p.cutoff)||p.lower_g<0||p.upper_g<p.lower_g||p.cutoff+tol<s.cutoff)
            return reject("invalid_cover_piece");
        if(p.id==s.leaf && p.lower_g==s.lower_g && p.upper_g==s.upper_g &&
           p.cutoff==s.cutoff && s.native_preconditions && !s.model_sha256.empty()) {
            if(active) return reject("duplicate_active_scope");
            active=true;
            if(has_native) p.lower=std::max(p.lower,b);
        }
        // Check the restricted numerical claim BEFORE adding its cutoff
        // complement. Otherwise min(cutoff,bound) could hide a contradiction.
        for(const auto& v:witnesses) if(verified(v) &&
            v.G>=p.lower_g && v.G<=p.upper_g && v.objective<=p.cutoff &&
            p.lower>v.objective+tol) return reject("local_bound_witness_inconsistency",true);
    }
    if(has_native && !active) return reject("native_scope_not_matching_frozen_live_leaf");
    std::sort(pieces.begin(),pieces.end(),[](const auto& a,const auto& c){return a.lower_g<c.lower_g;});
    // The omitted G tail has F>=G>=cutoff; no physical G exceeds gmax.
    const double required=std::min(s.cutoff,s.gmax);
    double covered=0,lower=s.cutoff;
    if(pieces.empty()) return reject("empty_cover");
    for(const auto& p:pieces) {
        // Exact interval comparisons: no fabricated narrow gap coverage.
        if(p.lower_g>covered) return reject("uncovered_gini_range");
        covered=std::max(covered,p.upper_g);
        lower=std::min(lower,std::min(p.cutoff,p.lower));
    }
    if(covered<required) return reject("uncovered_gini_tail");
    if(lower>ub+tol) return reject("global_bound_witness_inconsistency",true);
    out.available=true;out.value=lower;out.reason=has_native?"complete_frozen_cover_native_callback":"complete_frozen_cover";
    return out;
}

NativeEvidenceJournal::NativeEvidenceJournal(const Instance& in,const SolveOptions& options)
    :instance_(in),options_(options),directory_(options.native_evidence_dir) {
    if(!directory_.empty() && !options.process_start_time_valid) throw std::runtime_error("journal requires process clock");
    if(!std::isfinite(options.lambda) || options.lambda<0 || in.V<1)
        throw std::runtime_error("journal nonnegative objective precondition");
    for(int i=1;i<=in.V;++i) if(in.weights.at(i)<0 || !std::isfinite(in.weights.at(i)))
        throw std::runtime_error("journal negative weight");
    if(directory_.empty())return; // In-memory same-instance qualification needs no file identity carrier.
    if(!directory_.empty() && !std::filesystem::create_directory(directory_)) throw std::runtime_error("journal directory must be new");
    std::ostringstream o; o << std::setprecision(17)
      << "\"input_sha256\":" << quoted(fileSha256(in.path))
      << ",\"preset\":" << quoted(options.algorithm_preset) << ",\"method\":" << quoted(options.method)
      << ",\"lambda\":" << options.lambda << ",\"V\":" << in.V << ",\"M\":" << in.M
      << ",\"T\":" << in.total_time_limit << ",\"pickup_seconds\":" << in.pickup_time
      << ",\"drop_seconds\":" << in.drop_time << ",\"analytical_full_domain_lower_bound\":0"
      << ",\"certificate\":\"none_source_qualification_round133\"";
    publish("identity",o.str());
}
void NativeEvidenceJournal::publish(const std::string& kind,const std::string& fields) {
    if(failed_) return;
    const auto seq=++sequence_;
    if(directory_.empty())return;
    const std::string stem="event_"+std::to_string(seq);
    const std::string data="{\"schema\":1,\"sequence\":"+std::to_string(seq)+",\"kind\":"+quoted(kind)+","+fields+"}\n";
    closedWrite(directory_/(stem+".json"),data);
    const std::string hash=textSha256(data);
    std::ostringstream receipt; receipt << std::setprecision(17) << "NEJ1 " << seq << ' '
      << processElapsedSeconds(options_) << ' ' << data.size() << ' ' << hash << '\n';
    closedWrite(directory_/(stem+".commit"),receipt.str());
}
long long NativeEvidenceJournal::beginCall(const NativeEvidenceScope& scope) {
    calls_.push_back(scope);last_bounds_.push_back(-std::numeric_limits<double>::infinity());
    first_native_witness_.push_back(false);native_infeasible_.push_back(false);
    const auto call=static_cast<long long>(calls_.size());
    publish("call", "\"call\":"+std::to_string(call)+","+scopeJson(scope));
    return call;
}
void NativeEvidenceJournal::witness(const std::vector<RoutePlan>& routes,const std::string& source,long long call) {
    if(failed_)return;
    auto v=verifySolution(instance_,routes,options_.lambda);
    if(!verified(v)) {
        publish("witness_rejected","\"call\":"+std::to_string(call)+",\"source\":"+quoted(source));return;
    }
    // Even non-improving MIPSOL vectors may expose a contradictory local bound.
    std::vector<std::pair<long long,std::string>> contradictions;
    for(std::size_t i=0;i<calls_.size();++i) {
        auto all=witnesses_;all.push_back(v);
        const auto check=evaluateNativeLocalBound(calls_[i],last_bounds_[i],all);
        if(check.inconsistent) contradictions.push_back({static_cast<long long>(i+1),check.reason});
        if(native_infeasible_[i]) {
            const auto infeasible=evaluateNativeLocalInfeasibility(calls_[i],all);
            if(infeasible.inconsistent)contradictions.push_back({static_cast<long long>(i+1),infeasible.reason});
        }
    }
    const bool first_native=call>0 && source=="native_MIPSOL_verified_original_routes" &&
        !first_native_witness_.at(static_cast<std::size_t>(call-1));
    const bool improving=v.objective<best_;
    if(!improving && !first_native && contradictions.empty())return;
    std::ostringstream o; o << std::setprecision(17) << "\"call\":" << call
      << ",\"source\":" << quoted(source) << ",\"improving\":" << improving << ",\"objective\":" << v.objective
      << ",\"G\":" << v.G << ",\"P\":" << v.P << ",\"routes\":[";
    for(std::size_t i=0;i<routes.size();++i) {
        const auto& r=routes[i];if(i)o << ',';
        o << "{\"vehicle\":" << r.vehicle << ",\"nodes\":[";
        for(std::size_t j=0;j<r.nodes.size();++j){if(j)o << ',';o << r.nodes[j];}
        o << "],\"operations\":[";
        for(std::size_t j=0;j<r.operations.size();++j){if(j)o << ',';const auto& op=r.operations[j];
          o << "{\"station\":" << op.station << ",\"pickup\":" << op.pickup << ",\"drop\":" << op.drop << '}';}
        o << "]}";
    }
    o << ']';publish("witness",o.str());
    if(v.objective<best_) {best_=v.objective;best_routes_=routes;}
    witnesses_.push_back(std::move(v));
    if(first_native)first_native_witness_[static_cast<std::size_t>(call-1)]=true;
    for(const auto& c:contradictions)rejectSource(c.first,c.second);
}
void NativeEvidenceJournal::nativeBound(long long call,double bound) {
    if(failed_ || !std::isfinite(bound))return;
    const auto i=static_cast<std::size_t>(call-1);
    if(bound<=last_bounds_.at(i))return;
    last_bounds_[i]=bound;
    const auto d=evaluateNativeEvidenceBound(calls_.at(i),bound,witnesses_);
    const auto local=evaluateNativeLocalBound(calls_.at(i),bound,witnesses_);
    std::ostringstream o;o << std::setprecision(17) << "\"call\":" << call << ",\"native_bound\":" << bound
      << ",\"global_available\":" << (d.available && proofUsable() && !local.inconsistent) << ",\"inconsistent\":" << d.inconsistent
      << ",\"reason\":" << quoted(proofUsable()?d.reason:proof_failure_reason_) << ",\"global_bound\":";
    if(d.available && proofUsable() && !local.inconsistent)o << d.value;else o << "null";
    o << ",\"local_available\":" << (local.available && proofUsable())
      << ",\"local_reason\":" << quoted(proofUsable()?local.reason:proof_failure_reason_)
      << ",\"local_bound\":";
    if(local.available && proofUsable())o<<local.value;else o<<"null";
    o << ",\"retrospective\":false";
    publish("bound",o.str());
    if(local.inconsistent)rejectSource(call,local.reason);
}
NativeEvidenceBound NativeEvidenceJournal::localBound(long long call,double bound) const {
    NativeEvidenceBound out;
    if(!proofUsable()) {out.reason=proof_failure_reason_;out.inconsistent=source_rejected_;return out;}
    if(call<1 || static_cast<std::size_t>(call)>calls_.size()) {out.reason="native_call_identity_unavailable";return out;}
    return evaluateNativeLocalBound(calls_[static_cast<std::size_t>(call-1)],bound,witnesses_);
}
NativeEvidenceBound NativeEvidenceJournal::localScope(long long call) const {
    NativeEvidenceBound out;
    if(!proofUsable()) {out.reason=proof_failure_reason_;out.inconsistent=source_rejected_;return out;}
    if(call<1 || static_cast<std::size_t>(call)>calls_.size()){out.reason="native_call_identity_unavailable";return out;}
    return evaluateNativeLocalScope(calls_[static_cast<std::size_t>(call-1)]);
}
NativeEvidenceBound NativeEvidenceJournal::localInfeasibility(long long call) const {
    const auto scope=localScope(call);if(!scope.available)return scope;
    return evaluateNativeLocalInfeasibility(calls_[static_cast<std::size_t>(call-1)],witnesses_);
}
void NativeEvidenceJournal::nativeInfeasible(long long call) {
    native_infeasible_.at(static_cast<std::size_t>(call-1))=true;
    const auto check=localInfeasibility(call);
    publish("native_infeasible","\"call\":"+std::to_string(call)+",\"qualified\":"+
        std::to_string(check.available)+",\"reason\":"+quoted(check.reason));
    if(check.inconsistent)rejectSource(call,check.reason);
}
void NativeEvidenceJournal::rejectSource(long long call,const std::string& reason) {
    publish("source_rejected","\"call\":"+std::to_string(call)+",\"reason\":"+quoted(reason)+
        ",\"dependent_control_state_requires_abandonment\":true");
    source_rejected_=true;
    if(proof_failure_reason_.empty())proof_failure_reason_=reason;
}
void NativeEvidenceJournal::nativeQuality(long long call,const std::string& fields,
    bool sufficient,const std::string& reason) {
    publish("native_quality","\"call\":"+std::to_string(call)+","+fields);
    if(!sufficient)rejectSource(call,"native_quality_insufficient:"+reason);
}
void NativeEvidenceJournal::returned(long long call,int rc) {
    publish("returned","\"call\":"+std::to_string(call)+",\"return_code\":"+std::to_string(rc));
}
void NativeEvidenceJournal::notStarted(long long call,const std::string& reason) {
    publish("not_started","\"call\":"+std::to_string(call)+",\"reason\":"+quoted(reason)+",\"actual_Optimize\":false");
}
void NativeEvidenceJournal::failure(const std::string& reason) noexcept {
    try {publish("failure","\"reason\":"+quoted(reason));} catch(...) {}
    failed_=true;
    if(proof_failure_reason_.empty())proof_failure_reason_="native_evidence_failure:"+reason;
}
bool readNativeEvidenceReceipt(const std::filesystem::path& receipt,double observed,double cutoff,
    std::string& payload,std::string& reason) {
    payload.clear();
    auto reject=[&](const char* why){reason=why;return false;};
    if(!std::isfinite(observed)||!std::isfinite(cutoff)||observed<0||observed>cutoff)
        return reject("observation_outside_cutoff");
    std::ifstream r(receipt,std::ios::binary);
    std::string raw((std::istreambuf_iterator<char>(r)),{});
    if(raw.empty() || raw.back()!='\n')return reject("incomplete_receipt");
    std::istringstream parser(raw);std::string schema,hash,trailing;long long seq=0;double t=-1;std::size_t size=0;
    if(!(parser>>schema>>seq>>t>>size>>hash)||parser>>trailing||schema!="NEJ1"||seq<1||
       !std::isfinite(t)||t<0||t>cutoff||hash.size()!=64 ||
       receipt.filename().string()!="event_"+std::to_string(seq)+".commit")return reject("invalid_receipt");
    auto data=receipt;data.replace_extension(".json");std::ifstream f(data,std::ios::binary);
    std::string text((std::istreambuf_iterator<char>(f)),{});
    if(text.size()!=size||textSha256(text)!=hash)return reject("data_hash_or_length_mismatch");
    payload=std::move(text);reason="complete_hash_checked_observation";return true;
}
} // namespace ebrp
