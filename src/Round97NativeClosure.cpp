#include "Round97NativeClosure.hpp"
#include "CanonicalCompactModel.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "ProcessPhaseLedger.hpp"
#include "Round61Candidates.hpp"
#include "Round83BlockExchange.hpp"
#include <algorithm>
#include <cmath>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <unordered_map>

namespace ebrp {
namespace {
using Clock=std::chrono::steady_clock;
double seconds(Clock::time_point t) { return std::chrono::duration<double>(Clock::now()-t).count(); }
std::string quote(const std::string& s) { std::ostringstream o; o<<std::quoted(s); return o.str(); }
std::string number(double x) { if(!std::isfinite(x)||std::fabs(x)>=1e100)return "null";std::ostringstream o;o<<std::setprecision(17)<<x;return o.str(); }
void require(bool ok,const std::string& reason) { if(!ok)throw std::runtime_error(reason); }
std::string routeKey(const RoutePlan& r) {
    auto copy=r;copy.vehicle=0;return canonicalCandidateSerialization({copy});
}
}
std::vector<RoutePlan> round97Normalize(const Instance& in,double lambda,const std::vector<RoutePlan>& routes) {
    std::set<int> vehicles;
    for(const auto& r:routes)require(r.vehicle>=0&&r.vehicle<in.M&&vehicles.insert(r.vehicle).second,"round97_duplicate_or_invalid_vehicle");
    const auto checked=verifySolution(in,routes,lambda);
    require(checked.feasible&&checked.errors.empty(),"round97_invalid_physical_routes");
    // Common T and common directed matrix: equal Q is the complete vehicle
    // interchangeability class supported by Instance, not an assumed metric.
    std::map<int,std::vector<int>> classes;
    for(int k=0;k<in.M;++k)classes[in.Q[k]].push_back(k);
    std::vector<RoutePlan> out;
    for(const auto& [q,ids]:classes) {
        std::vector<RoutePlan> used;
        for(const auto& r:routes)if(in.Q[r.vehicle]==q&&!r.operations.empty())used.push_back(r);
        std::sort(used.begin(),used.end(),[](const auto& a,const auto& b){
            if(a.operations.size()!=b.operations.size())return a.operations.size()>b.operations.size();
            return routeKey(a)<routeKey(b);
        });
        for(std::size_t j=0;j<used.size();++j){used[j].vehicle=ids[j];out.push_back(used[j]);}
    }
    std::sort(out.begin(),out.end(),[](const auto& a,const auto& b){return a.vehicle<b.vehicle;});
    const auto after=verifySolution(in,out,lambda);
    require(after.feasible&&after.errors.empty()&&after.final_inventory==checked.final_inventory&&
        after.objective==checked.objective,"round97_normalization_changed_physics");
    return out;
}
std::string round97StateHash(const Instance& in,double lambda,const std::vector<RoutePlan>& routes) {
    return textSha256(canonicalCandidateSerialization(round97Normalize(in,lambda,routes)));
}
Round97NativeClosure::Round97NativeClosure(const Instance& in,const SolveOptions& opt,const std::filesystem::path& dir)
    :instance_(in),options_(opt),directory_(dir) {
    require(opt.round97_native_closure=="observe"||opt.round97_native_closure=="shadow"||feedback(),"round97_invalid_mode");
    require(!std::filesystem::exists(dir),"round97_evidence_directory_exists");
    std::filesystem::create_directories(dir);events_.open(dir/"events.jsonl");
    require(bool(events_),"round97_event_open_failed");
    record("session","\"mode\":"+quote(opt.round97_native_closure)+",\"operator\":\"r83\"");
}
void Round97NativeClosure::record(const std::string& kind,const std::string& fields) {
    events_<<"{\"kind\":"<<quote(kind)<<",\"process_seconds\":"<<number(processElapsedSeconds(options_))<<','<<fields<<"}\n";
    events_.flush();require(bool(events_),"round97_event_write_failed");
}
void Round97NativeClosure::failure(const std::string& reason) noexcept {
    failed_=true;
    try {record("failure","\"reason\":"+quote(reason));}catch(...){}
}
void Round97NativeClosure::incumbent(Round97Model& m,double value) noexcept {
    if(failed_||!std::isfinite(value)||std::fabs(value)>=1e100)return;
    try {
        for(auto& s:m.submissions)if(!s.changed&&value<=s.objective+1e-8&&value<s.before-1e-8) {
            s.changed=true;
            record("native_incumbent_change","\"call\":"+std::to_string(m.call)+",\"submission_event\":"+
                std::to_string(s.event)+",\"native_incumbent\":"+number(value)+",\"unique_source_proven\":false");
        }
    }catch(const std::exception& e){failure(e.what());}catch(...){failure("round97_incumbent_unknown_exception");}
}
void Round97NativeClosure::solution(Round97Model& m,const std::vector<double>& values,double model_objective,
    double native_incumbent,double nodes,int solution_count,int phase,const Submit& submit) {
    if(failed_)return;
    const auto began=Clock::now();
    const long long event=++sequence_;
    std::string fields="\"event\":"+std::to_string(event)+",\"call\":"+std::to_string(m.call)+
        ",\"epoch\":"+std::to_string(m.epoch)+",\"leaf\":"+quote(m.leaf)+",\"model_sha256\":"+quote(m.sha)+
        ",\"gamma_L\":"+number(m.lower)+",\"gamma_U\":"+number(m.upper)+",\"cutoff\":"+number(m.cutoff)+
        ",\"model_objective\":"+number(model_objective)+",\"native_incumbent_before\":"+number(native_incumbent)+
        ",\"nodes\":"+number(nodes)+",\"solution_count\":"+std::to_string(solution_count)+",\"phase\":"+std::to_string(phase);
    auto finish=[&](const std::string& status){record("solution",fields+",\"status\":"+quote(status)+",\"total_seconds\":"+number(seconds(began)));};
    try {
        require(values.size()==m.domain.names.size(),"round97_native_vector_size");
        std::unordered_map<std::string,double> named;
        double input_objective=m.objective_constant;
        for(std::size_t j=0;j<values.size();++j) {
            require(std::isfinite(values[j]),"round97_nonfinite_native_vector");
            require(named.emplace(m.domain.names[j],values[j]).second,"round97_duplicate_column");
            require(values[j]>=m.domain.lower_bounds[j]-1e-6&&values[j]<=m.domain.upper_bounds[j]+1e-6,"round97_native_bound_residual");
            const char t=m.domain.variable_types[j];
            require((t!='I'&&t!='B')||std::fabs(values[j]-std::round(values[j]))<=1e-5,"round97_native_integrality_residual");
            input_objective+=m.objective[j]*values[j];
        }
        require(std::isfinite(model_objective)&&std::fabs(input_objective-model_objective)<=1e-6,"round97_native_objective_residual");
        for(auto& s:m.submissions)if(!s.observed&&s.values.size()==values.size()) {
            bool same=true;
            for(std::size_t j=0;j<values.size();++j)if(std::fabs(values[j]-s.values[j])>1e-6){same=false;break;}
            if(same){s.observed=true;record("submitted_vector_observed",fields+",\"submission_event\":"+std::to_string(s.event)+",\"unique_source_proven\":false");}
        }
        const auto decoded=reconstructCanonicalCompactRoutes(instance_,named);
        std::unordered_map<std::string,double> decoded_values;
        for(const auto& r:decoded) {
            for(std::size_t j=1;j<r.nodes.size();++j)if(r.nodes[j-1]!=r.nodes[j])
                decoded_values["x_"+std::to_string(r.vehicle)+"_"+std::to_string(r.nodes[j-1])+"_"+std::to_string(r.nodes[j])]=1;
            for(const auto& op:r.operations) {
                const auto suffix=std::to_string(r.vehicle)+"_"+std::to_string(op.station);
                decoded_values["p_"+suffix]=op.pickup;decoded_values["d_"+suffix]=op.drop;
            }
        }
        for(const auto& [name,value]:named)if(name.rfind("x_",0)==0||name.rfind("p_",0)==0||name.rfind("d_",0)==0)
            require(std::fabs(value-decoded_values[name])<=1e-5,"round97_decode_lost_arc_or_operation");
        const auto native_residual=validateCandidateLinearResidual(m.linear,values,1e-6);
        require(native_residual.checked&&native_residual.valid,"round97_native_linear_residual");
        auto routes=round97Normalize(instance_,options_.lambda,decoded);
        const auto original=verifySolution(instance_,routes,options_.lambda);
        require(original.objective<=model_objective+1e-6,"round97_model_below_true_objective");
        // Reconstruction must account for every native integer inventory.
        for(int i=1;i<=instance_.V;++i)
            require(std::fabs(named.at("Y_"+std::to_string(i))-original.final_inventory[i])<=1e-5,"round97_decode_inventory_mismatch");
        const auto hash=textSha256(canonicalCandidateSerialization(routes));
        fields+=",\"input_hash\":"+quote(hash)+",\"input_F\":"+number(original.objective)+
            ",\"input_G_true\":"+number(original.G)+",\"input_model_G\":"+number(named.at("G"))+
            ",\"matches_supplied_start_physical_state\":"+(m.start_hash.empty()?"null":(hash==m.start_hash?"true":"false"));
        auto cached=cache_.find(hash);
        if(cached==cache_.end()) {
            // Persist each genuinely new physical source before optional work.
            VerifiedCandidateStore input;
            require(input.consider(instance_,options_.lambda,routes,"round97_native_MIPSOL",m.sha),"round97_input_store");
            writeRound61Witness(directory_/("input_"+hash+".json"),instance_,options_.lambda,input.best());
            std::ofstream vector(directory_/("vector_"+std::to_string(event)+".csv"));vector<<std::setprecision(17)<<"name,value\n";
            for(std::size_t j=0;j<values.size();++j)vector<<m.domain.names[j]<<','<<values[j]<<'\n';
            vector.close();require(bool(vector),"round97_input_vector_write");
            if(options_.round97_native_closure=="observe") {
                cache_.emplace(hash,Cached{input.best(),false});finish("observe_new_state");return;
            }
            if(processWorkDeadlineReached(options_)){finish("deadline_before_closure");return;}
            const auto closure_start=Clock::now();
            auto complete=routes;
            for(int k=0;k<instance_.M;++k)if(std::none_of(complete.begin(),complete.end(),[&](const auto& r){return r.vehicle==k;}))
                complete.push_back(RoutePlan{k,{0,0},{}});
            // Save a newly verified strict improvement while it is still
            // inside the common deadline, even if a later scan is interrupted.
            auto accepted=[&](const std::vector<RoutePlan>& accepted_routes,const Verification& checked) {
                if(processWorkDeadlineReached(options_)||checked.objective>=original.objective-1e-9||
                    (archive_.verified&&checked.objective>=archive_.objective-1e-9))return;
                VerifiedCandidateStore saved;
                require(saved.consider(instance_,options_.lambda,round97Normalize(instance_,options_.lambda,accepted_routes),
                    "round97_predeadline_accepted_closure",m.sha),"round97_accepted_checkpoint_verification");
                if(processWorkDeadlineReached(options_))return;
                archive_=saved.best();
                const double verified_time=processElapsedSeconds(options_);
                const auto name="accepted_"+std::to_string(event)+"_"+archive_.content_sha256+".json";
                writeRound61Witness(directory_/name,instance_,options_.lambda,archive_);
                record("predeadline_verified_candidate","\"event\":"+std::to_string(event)+
                    ",\"verification_completed_seconds\":"+number(verified_time)+",\"F\":"+number(archive_.objective)+
                    ",\"witness\":"+quote(name));
            };
            const auto improved=runRound83ExchangeDescent(instance_,options_,complete,{},accepted);
            fields+=",\"closure_seconds\":"+number(seconds(closure_start))+
                ",\"closure_exhausted\":"+(improved.exhausted?"true":"false")+
                ",\"closure_deadline\":"+(improved.deadline?"true":"false")+
                ",\"old_neutral_moves\":"+std::to_string(improved.neutral)+
                ",\"quantity_moves\":"+std::to_string(improved.quantities)+",\"insertion_moves\":"+std::to_string(improved.insertions);
            require(!improved.verification_failed,"round97_closure_verification_failure");
            // No post-deadline improvement is promoted or backdated.
            if(processWorkDeadlineReached(options_)){finish("deadline_unexhausted_preserve_preverified_archive");return;}
            VerifiedCandidateStore store;
            require(store.consider(instance_,options_.lambda,round97Normalize(instance_,options_.lambda,improved.routes),
                "round97_native_physical_closure",m.sha),"round97_candidate_verification");
            if(processWorkDeadlineReached(options_)){finish("deadline_after_verification");return;}
            cached=cache_.emplace(hash,Cached{store.best(),improved.exhausted||improved.zero}).first;
            const auto& c=cached->second.candidate;
            // Only an exhausted output can bypass future closure work. A cached
            // physical result never bypasses the current-model mapping below.
            if(cached->second.exhausted)cache_.emplace(c.content_sha256,cached->second);
            writeRound61Witness(directory_/("candidate_"+std::to_string(event)+".json"),instance_,options_.lambda,c);
        } else fields+=",\"physical_cache_hit\":true";
        if(options_.round97_native_closure=="observe"){finish("observe_duplicate_state");return;}
        const auto& candidate=cached->second.candidate;
        fields+=",\"candidate_hash\":"+quote(candidate.content_sha256)+",\"candidate_F\":"+number(candidate.objective)+
            ",\"candidate_G_true\":"+number(candidate.G)+",\"original_feasible\":true";
        if(candidate.objective<original.objective-1e-9&&(!archive_.verified||candidate.objective<archive_.objective-1e-9)&&
            !processWorkDeadlineReached(options_))archive_=candidate;
        // An exhausted self-output is not re-submitted in the same call. In a
        // later domain it may fill a missing native incumbent, even F==cutoff.
        if(m.submitted_hashes.count(candidate.content_sha256)){finish("duplicate_submission_this_call");return;}
        const auto mapping_start=Clock::now();
        const auto mapped=mapVerifiedRoutesToCanonicalModel(instance_,options_,candidate.routes,
            candidate.source,m.lower,m.upper,m.cutoff,m.domain);
        fields+=",\"mapping_complete\":"+(mapped.complete?std::string("true"):"false")+
            ",\"mapping_reason\":"+quote(mapped.failure_reason)+",\"model_G\":"+number(mapped.G);
        if(!mapped.complete){fields+=",\"mapping_validation_seconds\":"+number(seconds(mapping_start));finish("physical_candidate_model_incompatible");return;}
        const auto residual=validateCandidateLinearResidual(m.linear,mapped.values,1e-7);
        double objective=m.objective_constant;
        for(std::size_t j=0;j<mapped.values.size();++j)objective+=m.objective[j]*mapped.values[j];
        const bool valid=residual.checked&&residual.valid&&std::isfinite(objective)&&std::fabs(objective-candidate.objective)<=1e-7;
        fields+=",\"model_objective_candidate\":"+number(objective)+",\"model_feasible\":"+(valid?"true":"false")+
            ",\"rows_checked\":"+std::to_string(residual.checked_rows)+",\"max_row_residual\":"+number(residual.maximum_violation)+
            ",\"mapping_validation_seconds\":"+number(seconds(mapping_start));
        if(!valid){finish("candidate_numeric_or_row_rejection");return;}
        const auto mapped_name="mapped_"+std::to_string(event)+".csv";
        std::ofstream mapped_file(directory_/mapped_name);mapped_file<<std::setprecision(17)<<"name,value\n";
        for(std::size_t j=0;j<mapped.values.size();++j)mapped_file<<m.domain.names[j]<<','<<mapped.values[j]<<'\n';
        mapped_file.close();require(bool(mapped_file),"round97_mapped_vector_write");
        fields+=",\"mapped_vector\":"+quote(mapped_name)+",\"mapped_vector_sha256\":"+quote(fileSha256(directory_/mapped_name));
        if(!feedback()){finish("shadow_valid_no_submission");return;}
        if(!round61ShouldSubmitCandidate(objective,m.cutoff,std::isfinite(native_incumbent)&&std::fabs(native_incumbent)<1e100,native_incumbent)){
            finish("not_better_than_native_or_above_cutoff");return;
        }
        if(processWorkDeadlineReached(options_)){finish("deadline_before_submission");return;}
        double returned=1e100;
        const int rc=submit(mapped.values,returned);
        fields+=",\"submission_return_code\":"+std::to_string(rc)+",\"submission_objective_returned\":"+number(returned);
        if(rc==0){m.submitted_hashes.insert(candidate.content_sha256);m.submissions.push_back({event,mapped.values,objective,native_incumbent,false,false});}
        finish(rc==0?"submitted_processing_pending":"submission_api_error");
    }catch(const std::exception& e){try{finish(std::string("exception:")+e.what());}catch(...){}failure(e.what());}
      catch(...){failure("round97_unknown_callback_exception");}
}
void Round97NativeClosure::handoff(long long epoch,double old_upper) {
    record("archive_handoff","\"new_epoch\":"+std::to_string(epoch)+",\"old_upper\":"+number(old_upper)+
        ",\"upper\":"+number(archive_.objective)+",\"candidate_hash\":"+quote(archive_.content_sha256));
}
void Round97NativeClosure::returned(Round97Model& m,int status,double objective,const std::vector<double>& values) noexcept {
    try {
        incumbent(m,objective);
        for(const auto& s:m.submissions) {
            bool same=!values.empty()&&values.size()==s.values.size();
            if(same)for(std::size_t j=0;j<values.size();++j)
                if(!std::isfinite(values[j])||std::fabs(values[j]-s.values[j])>1e-6){same=false;break;}
            record("final_submission_observation","\"call\":"+std::to_string(m.call)+
                ",\"submission_event\":"+std::to_string(s.event)+",\"full_vector_matches\":"+(same?"true":"false")+
                ",\"unique_source_proven\":false");
        }
        record("native_return","\"call\":"+std::to_string(m.call)+",\"native_status\":"+std::to_string(status)+
            ",\"native_objective\":"+number(objective)+",\"callback_count\":"+std::to_string(m.callback_count)+
            ",\"complete_new_callback_seconds\":"+number(m.callback_seconds)+",\"failed\":"+(failed_?"true":"false"));
    }catch(const std::exception& e){failure(e.what());}catch(...){failure("round97_return_exception");}
}
} // namespace ebrp
