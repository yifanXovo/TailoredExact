// Included after the single historical base-H definition in main.cpp.
// No optimizer, archive input, or alternative neighborhood is introduced here.
class Round169ObjectiveGuard {
    double lambda_, scaling_;
public:
    Round169ObjectiveGuard()
        : lambda_(get_greedy_objective_lambda()), scaling_(get_greedy_objective_scaling()) {}
    ~Round169ObjectiveGuard() noexcept { set_greedy_objective_params(lambda_, scaling_); }
    Round169ObjectiveGuard(const Round169ObjectiveGuard&) = delete;
    Round169ObjectiveGuard& operator=(const Round169ObjectiveGuard&) = delete;
};

void round169CheckGuard() {
    const double a=get_greedy_objective_lambda(), b=get_greedy_objective_scaling();
    try { Round169ObjectiveGuard guard; set_greedy_objective_params(.314159, 3.0);
        throw std::runtime_error("intentional scope-unwind fixture");
    } catch (const std::runtime_error&) {}
    auto early=[]() { Round169ObjectiveGuard guard; set_greedy_objective_params(.271828, 2.0); return; };
    early();
    if (a!=get_greedy_objective_lambda() || b!=get_greedy_objective_scaling())
        throw std::runtime_error("Round169 objective guard failed");
}

std::string round169PhysicalIdentity(const ebrp::Instance& x) {
    std::ostringstream s; s<<std::setprecision(17)<<x.V<<','<<x.M<<','
        <<x.total_time_limit<<','<<x.pickup_time<<','<<x.drop_time<<','<<x.distance_convention<<'\n';
    for (int q:x.Q) s<<q<<',';
    for (int i=0;i<=x.V;++i) s<<'\n'<<x.initial[i]<<','<<x.target[i]<<','<<x.capacity[i]<<','<<x.weights[i];
    for (const auto& row:x.dist) {s<<'\n';for (double d:row)s<<d<<',';}
    return ebrp::textSha256(s.str()); // excludes lambda; format explicitly R169
}

struct Round169Path {
    std::string name;
    unsigned seed=0;
    double search_lambda=0, evaluation_lambda=0, seconds=0, verification_seconds=0;
    bool complete=false, valid=false;
    PaperPrimalHeuristicResult h;
    ebrp::Verification original;
};

Round169Path round169RunPath(const ebrp::Instance& instance, const ebrp::SolveOptions& opt,
                            const std::string& name, unsigned seed, double search_lambda,
                            bool base) {
    const auto started=std::chrono::steady_clock::now();
    Round169Path r; r.name=name;r.seed=seed;r.search_lambda=search_lambda;r.evaluation_lambda=opt.lambda;
    const auto folder=std::filesystem::path(opt.round169_trace_directory)/name;
    std::filesystem::create_directories(folder);
    if (std::filesystem::exists(folder/"path.json")) throw std::runtime_error("Round169 evidence collision");
    auto effective=opt;
    effective.round169_primal_mode="off";effective.round169_h_panel=false;
    // Presets are already fully parsed. Never apply them again to a child H.
    effective.lambda=search_lambda;effective.primal_heuristic_seed=seed;
    if (!base) {
        effective.out_path=(folder/"unused_result.json").string();
        effective.export_incumbent_path=(folder/"export.json").string();
        effective.primal_heuristic_generation_log=(folder/"hga.csv").string();
        effective.heuristic_candidates_csv=(folder/"candidates.csv").string();
        effective.round60_hga_candidate_log=(folder/"verified_search_candidates.jsonl").string();
        effective.ub_event_log_path=(folder/"search_ub.csv").string();
        effective.native_evidence_dir=(folder/"unused_native").string();
        effective.process_phase_ledger_path=(folder/"phases.csv").string();
        effective.primal_heuristic_phase_label="round169_"+name;
        Round169ObjectiveGuard guard;
        r.h=runPaperPrimalHeuristicBase(instance,effective);
    } else r.h=runPaperPrimalHeuristicBase(instance,effective);
    const auto verify_start=std::chrono::steady_clock::now();
    r.original=ebrp::verifySolution(instance,r.h.routes,opt.lambda);
    r.valid=r.h.found && r.original.feasible && r.original.objective_matches && r.original.errors.empty();
    if (!r.valid) throw std::runtime_error("Round169 returned fleet fails original physical verification");
    const bool zero=opt.round65_hga_zero_stop && r.original.objective>=0 && r.original.objective<=1e-12;
    r.complete=zero || (r.h.round169_joint_complete && r.h.decoded_descent_complete && r.h.round169_closure_complete);
    r.verification_seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-verify_start).count();
    writeRouteJson((folder/"fleet.json").string(),r.h.routes);
    ebrp::writeTextFile((folder/"initial_random_orders.txt").string(),r.h.round169_initial_orders);
    r.seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
    std::ofstream f(folder/"path.json");f<<std::setprecision(17)
        <<"{\"name\":"<<std::quoted(name)<<",\"preset\":"<<std::quoted(effective.algorithm_preset)
        <<",\"effective_seed\":"<<effective.primal_heuristic_seed
        <<",\"search_lambda\":"<<effective.lambda<<",\"evaluation_lambda\":"<<opt.lambda
        <<",\"search_F\":"<<r.h.verification.objective<<",\"F\":"<<r.original.objective
        <<",\"G\":"<<r.original.G<<",\"P\":"<<r.original.P
        <<",\"input_SHA256\":"<<std::quoted(ebrp::fileSha256(instance.path))
        <<",\"physical_R169_SHA256\":"<<std::quoted(round169PhysicalIdentity(instance))
        <<",\"fleet_SHA256\":"<<std::quoted(ebrp::fileSha256(folder/"fleet.json"))
        <<",\"initial_random_orders_SHA256\":"<<std::quoted(ebrp::textSha256(r.h.round169_initial_orders))
        <<",\"valid\":true,\"complete\":"<<(r.complete?"true":"false")
        <<",\"joint_complete\":"<<(r.h.round169_joint_complete?"true":"false")
        <<",\"descent_complete\":"<<(r.h.decoded_descent_complete?"true":"false")
        <<",\"closure_complete\":"<<(r.h.round169_closure_complete?"true":"false")
        <<",\"qualified_zero\":"<<(zero?"true":"false")
        <<",\"descent_seeds_completed\":"<<r.h.decoded_descent_seeds_completed
        <<",\"decoded_checks\":"<<r.h.decoded_descent_checks
        <<",\"cross_route_checks\":"<<r.h.decoded_descent_cross_route_checks
        <<",\"physical_work_counter_sum\":"<<r.h.local_moves_tested
        <<",\"H_seconds\":"<<r.h.runtime_seconds<<",\"path_seconds\":"<<r.seconds
        <<",\"original_verification_seconds\":"<<r.verification_seconds
        <<",\"whole_run_elapsed_seconds\":"<<ebrp::processElapsedSeconds(opt)
        <<",\"notes\":[";
    for (size_t i=0;i<r.h.notes.size();++i) {if(i)f<<',';f<<'"'<<jsonEscapeLocal(r.h.notes[i])<<'"';}
    f<<"]}\n";f.close();if(!f)throw std::runtime_error("Round169 path evidence write failed");
    return r;
}

PaperPrimalHeuristicResult runPaperPrimalHeuristic(const ebrp::Instance& instance,
                                                 const ebrp::SolveOptions& opt) {
    // Ordinary B has exactly its historical call, with no additional logging/work.
    if (opt.round169_primal_mode=="off" && !opt.round169_h_panel && opt.round169_trace_directory.empty())
        return runPaperPrimalHeuristicBase(instance,opt);
    if (opt.round169_primal_mode!="off" && opt.round169_primal_mode!="multistart" && opt.round169_primal_mode!="reweight")
        throw std::runtime_error("Round169 mode must be off, multistart, or reweight");
    if(opt.round169_trace_directory.empty() || opt.algorithm_preset!="research-round83-vds-equal-net-exchange" ||
       opt.primal_heuristic_seed!=20260626u || opt.primal_heuristic_runs!=24 || opt.round96_route_order ||
       opt.round88_constructive_only_descent || opt.primal_heuristic_stop!="decoded-descent-interroute")
        throw std::runtime_error("Round169 requires complete parsed B/R83 and an isolated trace directory");
    if(opt.round169_h_panel && !opt.round169_h_only) throw std::runtime_error("Round169 panel is H-only");
    const auto started=std::chrono::steady_clock::now();round169CheckGuard();
    std::vector<Round169Path> paths;
    paths.push_back(round169RunPath(instance,opt,"base",20260626u,opt.lambda,true));
    const double saved_lambda=get_greedy_objective_lambda(),saved_scaling=get_greedy_objective_scaling();
    size_t best_m=0,best_c=0;
    std::string skip;
    bool all_weights_zero=true;for(int i=1;i<=instance.V;++i)if(instance.weights[i]!=0)all_weights_zero=false;
    if(opt.lambda==0)skip="lambda_zero";
    else if(all_weights_zero)skip="all_penalty_weights_zero";
    else if(opt.round65_hga_zero_stop && paths[0].original.objective>=0 && paths[0].original.objective<=1e-12)
        skip="qualified_original_zero";
    auto add=[&](bool reweight) {
        size_t& best=reweight?best_c:best_m;
        for(int j=1;j<=2;++j) {
            if(!skip.empty() || ebrp::processWorkDeadlineReached(opt))return;
            const unsigned seed=20260626u+static_cast<unsigned>(j);
            const double a=reweight?opt.lambda*(j==1?.5:2.):opt.lambda;
            paths.push_back(round169RunPath(instance,opt,(reweight?"C_s":"M_s")+std::to_string(j),seed,a,false));
            const size_t i=paths.size()-1;
            if(paths[i].original.objective<paths[best].original.objective-1e-10)best=i;
            if(opt.round65_hga_zero_stop && paths[best].original.objective>=0 && paths[best].original.objective<=1e-12) {
                skip="qualified_original_zero";return;
            }
        }
    };
    if(opt.round169_h_panel || opt.round169_primal_mode=="multistart")add(false);
    // Panel's independent C pool retains the base; M paths are never C inputs.
    if(opt.round169_h_panel && skip=="qualified_original_zero" && paths[0].original.objective>1e-12)skip.clear();
    if(opt.round169_h_panel || opt.round169_primal_mode=="reweight")add(true);
    if(saved_lambda!=get_greedy_objective_lambda() || saved_scaling!=get_greedy_objective_scaling())
        throw std::runtime_error("Round169 greedy global objective leaked from child H");
    auto again=ebrp::verifySolution(instance,paths[0].h.routes,opt.lambda);
    if(!again.feasible || again.objective!=paths[0].original.objective)throw std::runtime_error("Round169 original reevaluation changed");
    const size_t selected=opt.round169_primal_mode=="multistart"?best_m:
        (opt.round169_primal_mode=="reweight"?best_c:0);
    auto out=paths[0].h; // retain all historical base-H diagnostic fields
    out.routes=paths[selected].h.routes;out.verification=paths[selected].original;out.found=true;
    out.runtime_seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
    bool complete=true;for(const auto& p:paths)complete=complete&&p.complete&&p.valid;
    const bool necessary_complete=complete && (paths.size()==5 || (!skip.empty() && paths[0].complete));
    const double B=paths[0].original.objective,M=paths[best_m].original.objective,C=paths[best_c].original.objective;
    const double delta=std::max(1e-6,.001*std::max(B,1e-12));
    const bool gate=opt.round169_h_panel && necessary_complete && C<std::min(B,M)-delta;
    std::ofstream f(std::filesystem::path(opt.round169_trace_directory)/"selection.json");
    f<<std::setprecision(17)<<"{\"mode\":"<<std::quoted(opt.round169_primal_mode)
        <<",\"h_panel\":"<<(opt.round169_h_panel?"true":"false")<<",\"calls\":"<<paths.size()
        <<",\"B\":"<<B<<",\"M\":"<<M<<",\"C\":"<<C
        <<",\"Delta_restart\":"<<B-M<<",\"Delta_weight\":"<<M-C<<",\"delta\":"<<delta
        <<",\"necessary_H_complete\":"<<(necessary_complete?"true":"false")
        <<",\"E4_role_gate\":"<<(gate?"true":"false")<<",\"selected\":"<<std::quoted(paths[selected].name)
        <<",\"selected_M\":"<<std::quoted(paths[best_m].name)<<",\"selected_C\":"<<std::quoted(paths[best_c].name)
        <<",\"skip_reason\":"<<std::quoted(skip)<<",\"greedy_restored\":true,\"guard_exception_early_return_pass\":true"
        <<",\"total_initialization_seconds\":"<<out.runtime_seconds<<"}\n";
    f.close();if(!f)throw std::runtime_error("Round169 selection evidence write failed");
    out.notes.push_back("Round169 own-H original-objective selected="+paths[selected].name+
        "; historical hga/decoded fields describe base only; all child work in isolated trace and total initialization time");
    return out;
}
