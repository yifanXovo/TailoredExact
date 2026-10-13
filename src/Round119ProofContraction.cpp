#include "Round119ProofContraction.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "ProcessPhaseLedger.hpp"
#include "FixedIntervalMipBackend.hpp"
#include <algorithm>
#include <cmath>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace ebrp {
Round119ReturnDisposition evaluateRound119Return(const FixedIntervalMipOutcome& o,double remaining) {
    if(!o.attempted || o.optimize_return_code!=0 || !o.solver_finalization_reached ||
        !o.exact_zero_gap_roundtrip || !o.model_fingerprint_matches_request ||
        !o.feasibility_consistency_gate || o.failure_reason!="none")return Round119ReturnDisposition::Invalid;
    if(o.native_status=="OPTIMAL" || o.native_status=="INFEASIBLE")return Round119ReturnDisposition::MathematicalReturn;
    if(o.native_status=="INTERRUPTED")return remaining<=0 ? Round119ReturnDisposition::Deadline : Round119ReturnDisposition::MathematicalReturn;
    if(o.native_status=="TIME_LIMIT" && remaining<=0)return Round119ReturnDisposition::Deadline;
    if(o.native_status=="TIME_LIMIT" || o.native_status=="MEM_LIMIT" || o.native_status=="WORK_LIMIT" ||
        o.native_status=="NODE_LIMIT" || o.native_status=="ITERATION_LIMIT" || o.native_status=="SOLUTION_LIMIT")
        return Round119ReturnDisposition::ResourceStop;
    return Round119ReturnDisposition::Invalid;
}
namespace {
bool physical(const Verification& v) {
    return v.feasible && v.errors.empty() && v.original_solution_feasible &&
        v.original_objective_recomputed && std::isfinite(v.objective) && std::isfinite(v.G);
}
bool valid(const Round119Certificate& p) {
    return p.call > 0 && p.epoch >= 0 && p.side >= 0 && p.side <= 1 &&
        !p.parent.empty() && !p.leaf.empty() && !p.model.empty() && !p.path.empty() &&
        !p.scope.empty() && p.status == "OPTIMAL" && std::isfinite(p.bound) &&
        std::isfinite(p.cutoff) && p.cutoff >= 0 && p.parent_lower < p.parent_upper &&
        p.lower < p.upper && p.lower >= p.parent_lower && p.upper <= p.parent_upper &&
        (p.side == 0 ? p.lower == p.parent_lower : p.upper == p.parent_upper);
}
bool contradicts(const Round119Certificate& p, const Verification& v, double tol) {
    return physical(v) && v.G >= p.lower-tol && v.G <= p.upper+tol &&
        v.objective <= p.cutoff+tol && p.bound > v.objective+tol;
}
}

Round119Contraction chooseRound119Contraction(
    const std::vector<Round119Certificate>& proofs, const ControllingLeaf& leaf,
    const std::vector<std::string>& ancestors, double U, double tol,
    int maximum_depth, double minimum_width) {
    Round119Contraction out;
    if (!std::isfinite(U) || !std::isfinite(tol) || tol < 0 ||
        leaf.status != ControllingLeafStatus::Open || leaf.parent_replaced ||
        leaf.split_depth >= maximum_depth || leaf.lower_bound+tol>=U ||
        !(leaf.gamma_U-leaf.gamma_L > minimum_width+1e-12)) return out;
    std::vector<std::size_t> ordered;
    for (std::size_t i=0;i<proofs.size();++i) if(valid(proofs[i])) ordered.push_back(i);
    std::sort(ordered.begin(),ordered.end(),[&](auto i,auto j) {
        const auto& a=proofs[i];const auto& b=proofs[j];
        if(a.depth!=b.depth)return a.depth<b.depth;
        if(a.parent!=b.parent)return a.parent<b.parent;
        if(a.side!=b.side)return a.side<b.side;
        return a.call<b.call;
    });
    for(auto i:ordered) {
        const auto& p=proofs[i];
        if(p.used || std::find(ancestors.begin(),ancestors.end(),p.parent)==ancestors.end() ||
            leaf.gamma_L<p.parent_lower || leaf.gamma_U>p.parent_upper)continue;
        const double split=p.side==0?p.upper:p.lower;
        if(!(leaf.gamma_L<split && split<leaf.gamma_U))continue;
        const double conservative=std::min(p.bound,p.cutoff);
        if(!(U+tol<conservative))continue;
        for(auto j:ordered) {
            const auto& q=proofs[j];
            if(q.side==p.side || q.parent!=p.parent || q.epoch!=p.epoch ||
                q.cutoff!=p.cutoff || q.depth!=p.depth ||
                q.parent_lower!=p.parent_lower || q.parent_upper!=p.parent_upper ||
                (p.side==0 ? p.upper!=q.lower : q.upper!=p.lower))continue;
            // The exact two returned halves, not a merely overlapping fragment.
            if(p.side==0 ? q.upper!=p.parent_upper : q.lower!=p.parent_lower)continue;
            out.available=true;out.proof=i;out.sibling_proof=j;out.split=split;
            out.removed_side=p.side;
            out.left_bound=std::min((p.side==0?p:q).bound,p.cutoff);
            out.right_bound=std::min((p.side==1?p:q).bound,p.cutoff);
            out.close_both=!q.used && U+tol<std::min(q.bound,q.cutoff);
            return out;
        }
    }
    return out;
}

Round119ProofContraction::Round119ProofContraction(const Instance& in,
    const SolveOptions& opt, const std::filesystem::path& path,
    const std::vector<RoutePlan>& initial,double tolerance):instance_(in),options_(opt),tolerance_(tolerance) {
    if(std::filesystem::exists(path))throw std::runtime_error("round119_journal_already_exists");
    journal_.open(path);if(!journal_)throw std::runtime_error("round119_journal_open");
    observe(initial,0);
}
void Round119ProofContraction::record(const std::string& kind,const std::string& fields) {
    journal_<<std::setprecision(17)<<"{\"sequence\":"<<++sequence_
        <<",\"kind\":"<<std::quoted(kind)<<",\"process_seconds\":"
        <<processElapsedSeconds(options_)<<','<<fields<<"}\n";
    journal_.flush();if(!journal_)throw std::runtime_error("round119_journal_write");
}
void Round119ProofContraction::add(Round119Certificate p) {
    if(!valid(p))throw std::runtime_error("round119_invalid_returned_certificate");
    if(fileSha256(p.path)!=p.model)throw std::runtime_error("round119_certificate_model_changed");
    for(const auto& w:witnesses_)if(contradicts(p,w,tolerance_)) {
        failure_="PROOF_RELIABILITY_PRIORITY:round119_returned_bound_counterexample";
        record("revoked", "\"call\":"+std::to_string(p.call)+",\"reason\":\"returned_bound_counterexample\"");
        throw std::runtime_error(failure_);
    }
    std::ostringstream s;s<<std::setprecision(17)<<"\"call\":"<<p.call<<",\"epoch\":"<<p.epoch
        <<",\"parent\":"<<std::quoted(p.parent)<<",\"leaf\":"<<std::quoted(p.leaf)
        <<",\"side\":"<<p.side<<",\"depth\":"<<p.depth<<",\"model\":"<<std::quoted(p.model)
        <<",\"path\":"<<std::quoted(p.path)<<",\"scope\":"<<std::quoted(p.scope)
        <<",\"status\":"<<std::quoted(p.status)<<",\"parent_lower\":"<<p.parent_lower
        <<",\"parent_upper\":"<<p.parent_upper<<",\"lower\":"<<p.lower<<",\"upper\":"<<p.upper
        <<",\"cutoff\":"<<p.cutoff<<",\"bound\":"<<p.bound;
    record("paid_certificate_returned",s.str());proofs_.push_back(std::move(p));
}
void Round119ProofContraction::observe(const std::vector<RoutePlan>& routes,long long call) {
    const auto v=verifySolution(instance_,routes,options_.lambda);
    if(!physical(v))return;
    for(const auto& p:proofs_)if(contradicts(p,v,tolerance_)) {
        failure_="PROOF_RELIABILITY_PRIORITY:round119_same_scope_counterexample";
        record("revoked", "\"call\":"+std::to_string(call)+",\"proof_call\":"+
            std::to_string(p.call)+",\"reason\":\"same_scope_counterexample_all_dependencies_revoked\"");
    }
    // Do not tie events to epigraph g or floating-point solver objectives.
    if(v.objective<best_upper_-1e-9) {
        best_upper_=v.objective;best_routes_=routes;witnesses_.push_back(v);
        std::ostringstream s;s<<std::setprecision(17)<<"\"call\":"<<call
            <<",\"own_update\":"<<++own_updates_<<",\"U\":"<<v.objective<<",\"G_true\":"<<v.G<<",\"Y\":[";
        for(std::size_t i=0;i<v.final_inventory.size();++i){if(i)s<<',';s<<v.final_inventory[i];}
        s<<']';record("own_verified",s.str());
    }
    if(failed())throw std::runtime_error(failure_);
}
Round119Contraction Round119ProofContraction::choose(const ControllingLeaf& leaf,
    const std::vector<std::string>& ancestors) const {
    if(failed())return {};
    return chooseRound119Contraction(proofs_,leaf,ancestors,best_upper_,
        tolerance_,options_.maximum_split_depth,options_.minimum_interval_width);
}
void Round119ProofContraction::consumed(const Round119Contraction& d) {
    proofs_.at(d.proof).used=true;
    if(d.close_both)proofs_.at(d.sibling_proof).used=true;
}
} // namespace ebrp
