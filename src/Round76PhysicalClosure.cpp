#include "Round76PhysicalClosure.hpp"
#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"
#include "Round61Candidates.hpp"
#include <cmath>
#include <fstream>
#include <iomanip>
#include <stdexcept>

namespace ebrp {
Round76ClosureResult runRound76PhysicalClosure(const Instance& in,const SolveOptions& options,
    const std::vector<RoutePlan>& routes,const std::filesystem::path& trace_path) {
    Round76ClosureResult out;out.routes=routes;
    out.verification=verifySolution(in,routes,options.lambda);
    if(!out.verification.feasible || !out.verification.errors.empty() ||
        !out.verification.original_objective_recomputed)
        throw std::invalid_argument("Physical closure requires a verified original input witness");
    std::ofstream trace;
    auto snapshot=[&](const char* suffix) {
        if(trace_path.empty())return;
        VerifiedCandidateStore store;
        if(!store.consider(in,options.lambda,out.routes,"round76_physical_closure","original_problem"))
            throw std::runtime_error("Physical closure snapshot verification failed");
        writeRound61Witness(trace_path.string()+suffix,in,options.lambda,store.best());
    };
    if(!trace_path.empty()) {
        if(trace_path.has_parent_path())std::filesystem::create_directories(trace_path.parent_path());
        trace.open(trace_path);
        if(!trace)throw std::runtime_error("Cannot open physical closure trace");
        trace<<"step,process_seconds,kind,vehicle,pickup,drop,quantity,pickup_leg,drop_leg,travel_delta,added_duration,first,second,delta,F,G,P,insertion_placements,insertion_quantities,quantity_feasible,status\n"<<std::setprecision(17);
        snapshot(".initial.json");
    }
    auto record=[&](const char* kind,const Round73InsertionChoice& i,
                    const Round75QuantityChoice& q,const char* status) {
        if(!trace.is_open())return;
        trace<<out.stats.accepted<<','<<processElapsedSeconds(options)<<','<<kind<<','
            <<i.vehicle<<','<<i.pickup<<','<<i.drop<<','<<i.quantity<<','<<i.pickup_leg<<','<<i.drop_leg<<','
            <<i.travel_delta<<','<<i.added_duration<<','<<q.first<<','<<q.second<<','<<q.delta<<','
            <<out.verification.objective<<','<<out.verification.G<<','<<out.verification.P<<','
            <<out.stats.insertion.placements<<','<<out.stats.insertion.quantity_evaluations<<','
            <<out.stats.quantity.feasible_candidates<<','<<status<<'\n';
        trace.flush();if(!trace)throw std::runtime_error("Physical closure trace write failed");
    };
    record("none",{}, {},"initial_verified");
    for(;;) {
        const auto insertion=bestRound73Insertion(in,out.routes,options.lambda,out.stats.insertion,&options);
        if(out.stats.insertion.deadline_reached) {
            out.stats.deadline_reached=true;record("none",{}, {},"whole_run_deadline");break;
        }
        const auto quantity=bestRound75QuantityChange(in,out.routes,options.lambda,out.stats.quantity,&options);
        if(out.stats.quantity.deadline_reached) {
            out.stats.deadline_reached=true;record("none",{}, {},"whole_run_deadline");break;
        }
        if(!insertion.found && !quantity.found) {
            out.stats.exhausted=true;record("none",{}, {},"joint_neighborhood_exhausted");break;
        }
        const bool use_insertion=insertion.found && (!quantity.found || insertion.objective<=quantity.objective);
        auto next=use_insertion?applyRound73Insertion(out.routes,insertion):applyRound75QuantityChange(out.routes,quantity);
        auto verified=verifySolution(in,next,options.lambda);
        const double proposed=use_insertion?insertion.objective:quantity.objective;
        if(!verified.feasible || !verified.errors.empty() || !verified.original_objective_recomputed ||
            std::abs(verified.objective-proposed)>1e-10 || !(out.verification.objective-verified.objective>1e-12)) {
            out.stats.verification_failed=true;
            record(use_insertion?"insertion":"quantity",insertion,quantity,"verification_rejected");break;
        }
        out.routes=std::move(next);out.verification=std::move(verified);++out.stats.accepted;
        if(use_insertion)++out.stats.accepted_insertions;else ++out.stats.accepted_quantities;
        record(use_insertion?"insertion":"quantity",use_insertion?insertion:Round73InsertionChoice{},
            use_insertion?Round75QuantityChoice{}:quantity,"accepted_verified");
    }
    snapshot(".final.json");
    return out;
}
} // namespace ebrp
