#include "NativeEvidenceJournal.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "ProcessPhaseLedger.hpp"
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

NativeEvidenceBound evaluateNativeEvidenceBound(const NativeEvidenceScope& s,double b,
    const std::vector<Verification>& witnesses,double tol) {
    NativeEvidenceBound out;
    auto reject=[&](const std::string& reason,bool inconsistent=false) {
        out.reason=reason; out.inconsistent=inconsistent; return out;
    };
    if(!std::isfinite(tol) || tol<0 || !std::isfinite(s.gmax) || s.gmax<0 || s.gmax>=1)
        return reject("invalid_physical_domain");
    double ub=std::numeric_limits<double>::infinity();
    for(const auto& v:witnesses) if(verified(v)) ub=std::min(ub,v.objective);
    const bool has_native=std::isfinite(b);
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
            v.G>=p.lower_g-tol && v.G<=p.upper_g+tol && v.objective<=p.cutoff+tol &&
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
    if(directory_.empty() || !options.process_start_time_valid) throw std::runtime_error("journal requires path and process clock");
    if(!std::isfinite(options.lambda) || options.lambda<0 || in.V<1)
        throw std::runtime_error("journal nonnegative objective precondition");
    for(int i=1;i<=in.V;++i) if(in.weights.at(i)<0 || !std::isfinite(in.weights.at(i)))
        throw std::runtime_error("journal negative weight");
    if(!std::filesystem::create_directory(directory_)) throw std::runtime_error("journal directory must be new");
    std::ostringstream o; o << std::setprecision(17)
      << "\"input_sha256\":" << quoted(fileSha256(in.path))
      << ",\"preset\":" << quoted(options.algorithm_preset) << ",\"method\":" << quoted(options.method)
      << ",\"lambda\":" << options.lambda << ",\"V\":" << in.V << ",\"M\":" << in.M
      << ",\"T\":" << in.total_time_limit << ",\"pickup_seconds\":" << in.pickup_time
      << ",\"drop_seconds\":" << in.drop_time << ",\"analytical_full_domain_lower_bound\":0"
      << ",\"certificate\":\"none_read_only_observation\"";
    publish("identity",o.str());
}
void NativeEvidenceJournal::publish(const std::string& kind,const std::string& fields) {
    if(failed_) return;
    const auto seq=++sequence_;
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
    first_native_witness_.push_back(false);
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
    std::string contradiction;
    for(std::size_t i=0;i<calls_.size();++i) {
        auto all=witnesses_;all.push_back(v);
        const auto check=evaluateNativeEvidenceBound(calls_[i],last_bounds_[i],all);
        if(check.inconsistent) contradiction=check.reason;
    }
    const bool first_native=call>0 && source=="native_MIPSOL_verified_original_routes" &&
        !first_native_witness_.at(static_cast<std::size_t>(call-1));
    const bool improving=v.objective<best_;
    if(!improving && !first_native && contradiction.empty())return;
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
    o << ']';publish("witness",o.str());best_=std::min(best_,v.objective);witnesses_.push_back(std::move(v));
    if(first_native)first_native_witness_[static_cast<std::size_t>(call-1)]=true;
    if(!contradiction.empty())failure(contradiction);
}
void NativeEvidenceJournal::nativeBound(long long call,double bound) {
    if(failed_ || !std::isfinite(bound))return;
    const auto i=static_cast<std::size_t>(call-1);
    if(bound<=last_bounds_.at(i))return;
    last_bounds_[i]=bound;
    const auto d=evaluateNativeEvidenceBound(calls_.at(i),bound,witnesses_);
    std::ostringstream o;o << std::setprecision(17) << "\"call\":" << call << ",\"native_bound\":" << bound
      << ",\"global_available\":" << d.available << ",\"inconsistent\":" << d.inconsistent
      << ",\"reason\":" << quoted(d.reason) << ",\"global_bound\":";
    if(d.available)o << d.value;else o << "null";
    publish("bound",o.str());
    if(d.inconsistent)failure(d.reason);
}
void NativeEvidenceJournal::returned(long long call,int rc) {
    publish("returned","\"call\":"+std::to_string(call)+",\"return_code\":"+std::to_string(rc));
}
void NativeEvidenceJournal::failure(const std::string& reason) noexcept {
    try {publish("failure","\"reason\":"+quoted(reason));} catch(...) {}
    failed_=true;
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
