// Included inside the existing Windows adapter's anonymous namespace.
// No changes to its original loader, callback or P/ENS parameter path.
struct R105Model {
    const GurobiApi* api = nullptr;
    GRBmodel* value = nullptr;
    ~R105Model() { if (value) api->freemodel(value); }
};

class R105Session {
public:
    GurobiApi api;
    GRBenv* env = nullptr;
    const Instance& in;
    const SolveOptions& opt;
    std::filesystem::path dir;
    std::ofstream calls;
    long long master_calls = 0, oracle_calls = 0, iis_calls = 0, core_calls = 0;
    double master_seconds = 0, oracle_seconds = 0, iis_seconds = 0, core_seconds = 0;
    long long sequence = 0;
    // Optional R106 inner-environment cancellation, off for historical R105.
    bool deadline_callback = false, cancellation_requested = false, strict_numeric_status = false;
    double cancellation_seconds = -1;
    static int __stdcall deadlineCheck(GRBmodel* model,void*,int,void* userdata) {
        auto& s=*static_cast<R105Session*>(userdata);
        if(s.remaining()<=0) {
            if(!s.cancellation_requested){s.cancellation_requested=true;s.cancellation_seconds=processElapsedSeconds(s.opt);}
            s.api.terminate(model);
        }
        return 0;
    }
    R105Session(const Instance& instance, const SolveOptions& options,
                const std::filesystem::path& folder) : in(instance), opt(options), dir(folder) {
        std::filesystem::create_directories(dir);
        std::filesystem::path root, library; std::string reason;
        if (!loadGurobiApi(opt,api,root,library,reason)) throw std::runtime_error(reason);
        try {
            check(startSilentGurobiEnvironment(api,&env));
            check(api.setintparam(env,"Threads",1));
            check(api.setintparam(env,"Seed",0));
            check(api.setintparam(env,"Presolve",-1));
            check(api.setdblparam(env,"MIPGap",0));
            check(api.setdblparam(env,"MIPGapAbs",0));
            calls.open(dir/"calls.csv");
            calls << "call,phase,stage,process_seconds,remaining,seconds,status,solutions,bound,objective,model_sha256\n";
            std::ofstream identity(dir/"runtime.json");
            identity << "{\"library\":" << std::quoted(library.generic_string())
                << ",\"dll_sha256\":" << std::quoted(fileSha256(library))
                << ",\"runtime\":" << std::quoted(versionString(api)) << ",\"parameters\":";
            NativeEvidenceScope parameters;
            if(!evidenceParameterReadback(api,env,parameters))
                throw std::runtime_error("round105_native_parameter_contract_failed");
            identity << parameters.settings_json << "}\n";
        } catch (...) {
            if (env) api.freeenv(env);
            FreeLibrary(api.library); api.library=nullptr; throw;
        }
    }
    ~R105Session() { if (env) api.freeenv(env); if (api.library) FreeLibrary(api.library); }
    void check(int rc) const { if (rc) throw std::runtime_error(apiError(api,env,rc)); }
    double remaining() const { return processWorkRemainingSeconds(opt); }
    void read(R105Model& model, const std::filesystem::path& path) {
        model.api=&api; check(api.readmodel(env,path.string().c_str(),&model.value));
    }
    SolverNeutralModelDomain domain(GRBmodel* model) {
        int n=0;check(api.getintattr(model,"NumVars",&n));
        SolverNeutralModelDomain d; d.names.resize(n);d.lower_bounds.resize(n);
        d.upper_bounds.resize(n);d.variable_types.resize(n);
        check(api.getdblattrarray(model,"LB",0,n,d.lower_bounds.data()));
        check(api.getdblattrarray(model,"UB",0,n,d.upper_bounds.data()));
        check(api.getcharattrarray(model,"VType",0,n,d.variable_types.data()));
        for (int i=0;i<n;++i) { char* name=nullptr;check(api.getstrattrelement(model,"VarName",i,&name));
            if (!name) throw std::runtime_error("round105_missing_column");d.names[i]=name; }
        return d;
    }
    std::unordered_map<std::string,double> values(GRBmodel* model) {
        auto d=domain(model);std::vector<double> x(d.names.size());
        check(api.getdblattrarray(model,"X",0,static_cast<int>(x.size()),x.data()));
        std::unordered_map<std::string,double> out;
        for (std::size_t i=0;i<x.size();++i) out.emplace(d.names[i],x[i]);
        return out;
    }
    int optimize(GRBmodel* model, const std::string& phase, const std::filesystem::path& path) {
        const double rem=remaining();if (rem<=0) return GRB_TIME_LIMIT;
        auto* menv=api.getenv(model);
        NativeEvidenceScope parameters;
        if(!evidenceParameterReadback(api,menv,parameters))throw std::runtime_error("round105_model_parameter_contract");
        check(api.setdblparam(menv,"TimeLimit",rem));
        check(api.setstrparam(menv,"LogFile",(path.string()+".log").c_str()));
        const long long id=++sequence;
        calls << std::setprecision(17) << id << ',' << phase << ",before," << processElapsedSeconds(opt)
              << ',' << rem << ",,,,,," << fileSha256(path) << '\n'; calls.flush();
        if (!calls) throw std::runtime_error("round105_ahead_of_call_persist_failed");
        if(deadline_callback)check(api.setcallbackfunc(model,deadlineCheck,this));
        const auto start=Clock::now();const int rc=api.optimize(model);
        if(deadline_callback)check(api.setcallbackfunc(model,nullptr,nullptr));
        const double sec=std::chrono::duration<double>(Clock::now()-start).count();
        if (phase=="master") { ++master_calls;master_seconds+=sec; }
        else if (phase=="core_confirm") { ++core_calls;core_seconds+=sec; }
        else { ++oracle_calls;oracle_seconds+=sec; }
        int status=0,solutions=0;double bound=0,objective=0;
        if (!rc) { check(api.getintattr(model,"Status",&status));check(api.getintattr(model,"SolCount",&solutions)); }
        const bool b=!rc && !api.getdblattr(model,"ObjBoundC",&bound) && std::isfinite(bound) && std::abs(bound)<GRB_INFINITY;
        const bool o=!rc && solutions>0 && !api.getdblattr(model,"ObjVal",&objective) && std::isfinite(objective);
        calls << id << ',' << phase << ",after," << processElapsedSeconds(opt) << ',' << remaining() << ','
              << sec << ',' << status << ',' << solutions << ',';
        if(b) calls<<bound;calls<<',';if(o)calls<<objective;
        calls << ',' << fileSha256(path) << '\n';calls.flush(); check(rc);
        std::ifstream log(path.string()+".log");if(!log)throw std::runtime_error("round105_native_log_missing");
        std::string text((std::istreambuf_iterator<char>(log)),{});
        std::transform(text.begin(),text.end(),text.begin(),[](unsigned char c){return char(std::tolower(c));});
        for(const char* phrase : {"numerical trouble","numerical difficulties","unscaled primal violation","unscaled dual violation"})
            if(text.find(phrase)!=std::string::npos)throw std::runtime_error("round105_native_numerical_warning");
        if(strict_numeric_status&&status==GRB_NUMERIC)throw std::runtime_error("round106_native_NUMERIC_status");
        if(solutions) {
            const auto d=domain(model);std::vector<double> x(d.names.size());
            check(api.getdblattrarray(model,"X",0,static_cast<int>(x.size()),x.data()));
            int rows=0;check(api.getintattr(model,"NumConstrs",&rows));SolverNeutralLinearModel matrix;
            if(!readLinearModel(api,model,static_cast<int>(x.size()),rows,matrix))throw std::runtime_error("round105_candidate_matrix_read");
            const auto residual=validateCandidateLinearResidual(matrix,x,1e-6);
            double cv=0,bv=0,iv=0;
            check(api.getdblattr(model,"ConstrVio",&cv));check(api.getdblattr(model,"BoundVio",&bv));check(api.getdblattr(model,"IntVio",&iv));
            if(!residual.valid || !std::isfinite(cv) || !std::isfinite(bv) || !std::isfinite(iv) || cv>1e-6 || bv>1e-6 || iv>1e-5)
                throw std::runtime_error("round105_native_candidate_quality_failed");
            std::ofstream quality(path.string()+".quality.json");quality<<std::setprecision(17)
                <<"{\"rows\":"<<rows<<",\"max_row_violation\":"<<residual.maximum_violation
                <<",\"ConstrVio\":"<<cv<<",\"BoundVio\":"<<bv<<",\"IntVio\":"<<iv
                <<",\"parameters\":"<<parameters.settings_json<<"}\n";
            quality.flush();if(!quality)throw std::runtime_error("round105_quality_persist_failed");
        }
        if(solutions)check(api.write(model,(path.string()+".sol").c_str()));
        return status;
    }
    Round105OracleResult oracle(const Round105Pattern& pattern,
                                const std::filesystem::path& folder, bool core) {
        round105ValidatePattern(in,pattern);
        Round105OracleResult out;out.route.vehicle=pattern.vehicle;
        std::vector<int> all;for(int i=1;i<=in.V;++i)all.push_back(i);
        std::filesystem::create_directories(folder);
        const auto path=folder/"full.lp";
        round105WriteOracle(in,pattern,all,path);
        R105Model model;read(model,path);
        const int status=optimize(model.value,"oracle",path);
        int count=0;check(api.getintattr(model.value,"SolCount",&count));
        if(count>0) {
            const auto v=values(model.value);int current=0;std::set<int> seen;
            out.route.nodes.push_back(0);
            while(true) {
                int next=-1;
                for(int j=0;j<=in.V;++j)if(j!=current && v.at("x_"+std::to_string(current)+"_"+std::to_string(j))>0.5) {
                    if(next!=-1)throw std::runtime_error("round105_oracle_ambiguous_arc");next=j;
                }
                if(next==-1) { if(current==0 && seen.empty()) out.route.nodes.push_back(0);
                    else throw std::runtime_error("round105_oracle_open_route");break; }
                out.route.nodes.push_back(next);if(!next)break;
                if(!seen.insert(next).second)throw std::runtime_error("round105_oracle_cycle");
                const int q=pattern.operation[next];
                out.route.operations.push_back({next,std::max(0,q),std::max(0,-q)});current=next;
            }
            for(int i=1;i<=in.V;++i)if(bool(pattern.operation[i])!=bool(seen.count(i)))
                throw std::runtime_error("round105_oracle_service_mismatch");
            std::vector<RoutePlan> complete;
            for(int k=0;k<in.M;++k)complete.push_back(k==pattern.vehicle ? out.route : RoutePlan{k,{0,0},{}});
            const auto verify=verifyCompletePhysicalStartingWitness(in,complete,opt.lambda);
            if(!verify.feasible)throw std::runtime_error("round105_oracle_physical_verification_failed");
            out.status=Round105OracleStatus::Feasible;out.reason="independently_verified_route";return out;
        }
        if(status!=GRB_INFEASIBLE) {
            out.status=Round105OracleStatus::Unknown;out.reason="native_status_"+std::to_string(status);return out;
        }
        out.status=Round105OracleStatus::ProvedInfeasible;out.reason="full_pattern_native_infeasible";
        out.core=all;
        if(!core || remaining()<=0)return out;
        // IIS is only a proposal of semantic groups. Rebuild and prove that
        // system with ALL other stations free before using a shorter row.
        decltype(&GRBcomputeIIS) compute=nullptr;
        if(!resolve(api.library,"GRBcomputeIIS",compute))throw std::runtime_error("round105_missing_computeIIS");
        check(api.setdblparam(api.getenv(model.value),"TimeLimit",remaining()));
        const long long id=++sequence;calls<<id<<",iis,before,"<<processElapsedSeconds(opt)<<','<<remaining()<<",,,,,,"<<fileSha256(path)<<'\n';calls.flush();
        if(!calls)throw std::runtime_error("round105_iis_ledger_failed");
        if(deadline_callback)check(api.setcallbackfunc(model.value,deadlineCheck,this));
        const auto start=Clock::now();const int rc=compute(model.value);
        if(deadline_callback)check(api.setcallbackfunc(model.value,nullptr,nullptr));
        const double sec=std::chrono::duration<double>(Clock::now()-start).count();++iis_calls;iis_seconds+=sec;
        calls<<id<<",iis,after,"<<processElapsedSeconds(opt)<<','<<remaining()<<','<<sec<<','<<rc<<",,,,"<<fileSha256(path)<<'\n';calls.flush();
        if(strict_numeric_status) {
            check(rc);
            std::ifstream log(path.string()+".log");if(!log)throw std::runtime_error("round106_IIS_log_missing");
            std::string text((std::istreambuf_iterator<char>(log)),{});
            std::transform(text.begin(),text.end(),text.begin(),[](unsigned char c){return char(std::tolower(c));});
            for(const char* phrase:{"numerical trouble","numerical difficulties","unscaled primal violation","unscaled dual violation"})
                if(text.find(phrase)!=std::string::npos)throw std::runtime_error("round106_IIS_numerical_warning");
        }
        if(rc || remaining()<=0) {out.reason="full_proof_retained_core_interrupted";return out;}
        check(api.write(model.value,(folder/"proposal.ilp").string().c_str()));
        int rows=0,minimal=0;check(api.getintattr(model.value,"NumConstrs",&rows));
        check(api.getintattr(model.value,"IISMinimal",&minimal));
        std::vector<int> included(rows);check(api.getintattrarray(model.value,"IISConstr",0,rows,included.data()));
        std::set<int> groups;
        for(int r=0;r<rows;++r)if(included[r]) {
            char* n=nullptr;check(api.getstrattrelement(model.value,"ConstrName",r,&n));
            if(n && std::string(n).rfind("a_",0)==0) {
                const std::string text(n);const auto pos=text.find('_',2);
                if(pos==std::string::npos)throw std::runtime_error("round105_iis_group_mapping_error");
                const int i=std::stoi(text.substr(2,pos-2));
                if(i<1 || i>in.V)throw std::runtime_error("round105_iis_bad_station");groups.insert(i);
            }
        }
        if(groups.empty())throw std::runtime_error("round105_iis_empty_semantic_core");
        std::ofstream proposal(folder/"proposal.json");proposal<<"{\"IISMinimal\":"<<minimal<<",\"groups\":[";
        bool first=true;for(int i:groups){if(!first)proposal<<',';first=false;proposal<<i;}proposal<<"]}\n";
        proposal.flush();if(!proposal)throw std::runtime_error("round105_IIS_proposal_persist_failed");
        if(groups.size()==all.size()) {out.reason="IIS_retains_all_groups";return out;}
        std::vector<int> candidate(groups.begin(),groups.end());
        const auto reduced=folder/"core_confirm.lp";round105WriteOracle(in,pattern,candidate,reduced);
        R105Model confirm;read(confirm,reduced);
        const int cs=optimize(confirm.value,"core_confirm",reduced);
        if(cs==GRB_INFEASIBLE) {out.core=candidate;out.core_confirmed=true;out.reason="shorter_core_reproved_all_other_stations_free";}
        else if(cs==GRB_TIME_LIMIT || cs==GRB_INTERRUPTED)out.reason="full_proof_retained_core_unknown";
        else if(cs==GRB_OPTIMAL)throw std::runtime_error("round105_IIS_core_confirmation_feasible");
        else out.reason="full_proof_retained_core_unqualified_status";
        return out;
    }
};

void r105Witness(const std::filesystem::path& path,const std::vector<RoutePlan>& routes,double objective) {
    std::ofstream f(path);f<<std::setprecision(17)<<"{\"objective\":"<<objective<<",\"routes\":[";
    bool first=true;for(const auto& r:routes){if(!first)f<<',';first=false;
        f<<"{\"vehicle\":"<<r.vehicle<<",\"nodes\":[";
        for(std::size_t j=0;j<r.nodes.size();++j){if(j)f<<',';f<<r.nodes[j];}f<<"],\"operations\":[";
        for(std::size_t j=0;j<r.operations.size();++j){if(j)f<<',';const auto& o=r.operations[j];
            f<<"{\"station\":"<<o.station<<",\"pickup\":"<<o.pickup<<",\"drop\":"<<o.drop<<'}';}
        f<<"]}";}f<<"]}\n";f.flush();if(!f)throw std::runtime_error("round105_witness_persist_failed");
}

SolveResult r105Solve(const Instance& in,const SolveOptions& opt,const SolveResult& seed,SolveResult& result) {
    if(!hasMetricTravelLowerBounds(in) || opt.lambda<0 || !std::isfinite(opt.lambda))
        throw std::runtime_error("round105_master_requires_original_nonnegative_metric_domain");
    for(double w:in.weights)if(w<0 || !std::isfinite(w))throw std::runtime_error("round105_invalid_weight");
    result.strict_certified_original_problem=false;
    result.strict_certificate_class="certificate_rejected";
    result.strict_lower_bound_source="nonnegative_objective_then_valid_assignment_master_ObjBoundC";
    result.strict_native_model_scope="inventory_assignment_master_outer_relaxation";
    result.status="time_limit";result.lower_bound=0;
    // ENS uses a sparse list; the strict physical verifier uses one record/car.
    std::vector<RoutePlan> complete_seed(in.M);std::vector<bool> seed_seen(in.M,false);
    for(int k=0;k<in.M;++k)complete_seed[k]={k,{0,0},{}};
    for(const auto& route:seed.routes) {
        if(route.vehicle<0 || route.vehicle>=in.M || seed_seen[route.vehicle])throw std::runtime_error("round105_duplicate_seed_vehicle");
        seed_seen[route.vehicle]=true;complete_seed[route.vehicle]=route;
    }
    result.routes=complete_seed;
    const auto seed_verify=verifyCompletePhysicalStartingWitness(in,complete_seed,opt.lambda);
    if(!seed_verify.feasible || std::abs(seed_verify.objective-seed.upper_bound)>1e-7)
        throw std::runtime_error("round105_invalid_paid_startup");
    const auto dir=std::filesystem::path(opt.external_gini_artifact_dir)/"round105";
    R105Session session(in,opt,dir);auto& api=session.api;
    r105Witness(dir/"seed.json",complete_seed,seed_verify.objective);
    const double U0=seed_verify.objective,GU=std::min(1.0,U0);
    auto model_opt=opt;model_opt.round105_decomposition="off";
    CanonicalCompactModelSpec spec;spec.strengthened=true;spec.interval_restricted=true;
    spec.gamma_L=0;spec.gamma_U=GU;spec.add_verified_incumbent_row=true;
    spec.verified_incumbent=U0;spec.incumbent_epsilon=0;
    spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    const auto original=writeCanonicalCompactModel(in,model_opt,dir/"original.lp",spec);
    if(!original.written)throw std::runtime_error(original.failure_reason);
    R105Model master;session.read(master,original.path);
    auto domain=session.domain(master.value);const int n=static_cast<int>(domain.names.size());
    std::map<std::string,int> index;for(int i=0;i<n;++i)if(!index.emplace(domain.names[i],i).second)
        throw std::runtime_error("round105_duplicate_column");
    auto require=[&](const std::string& name,char type) {
        const int i=index.at(name);if(domain.variable_types[i]!=type)throw std::runtime_error("round105_unexpected_type:"+name);return i; };
    std::set<int> relaxed;
    for(int k=0;k<in.M;++k) {
        for(int i=0;i<=in.V;++i)for(int j=0;j<=in.V;++j)if(i!=j)
            relaxed.insert(require("x_"+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(j),'B'));
        for(int i=1;i<=in.V;++i) {
            const std::string suffix=std::to_string(k)+"_"+std::to_string(i);
            relaxed.insert(require("load_"+suffix,'I'));
            require("z_"+suffix,'B');require("mode_"+suffix,'B');require("p_"+suffix,'I');require("d_"+suffix,'I');
            require("ord_"+suffix,'C');
        }
    }
    for(int i=1;i<=in.V;++i) {require("Y_"+std::to_string(i),'I');
        bool state=false;for(int y=0;y<=in.capacity[i];++y){const std::string name="state_"+std::to_string(i)+"_"+std::to_string(y);
            if(index.count(name)){require(name,'B');state=true;}}
        if(!state)throw std::runtime_error("round105_missing_inventory_selector"); }
    auto types=domain.variable_types;for(int i:relaxed)types[i]='C';
    session.check(api.setcharattrarray(master.value,"VType",0,n,types.data()));session.check(api.updatemodel(master.value));
    const auto observed=session.domain(master.value);
    std::ofstream variables(dir/"variables.csv");variables<<"index,name,old_type,master_type,relaxed\n";
    for(int i=0;i<n;++i) {
        if(observed.names[i]!=domain.names[i] || observed.lower_bounds[i]!=domain.lower_bounds[i] ||
           observed.upper_bounds[i]!=domain.upper_bounds[i] || observed.variable_types[i]!=types[i])
            throw std::runtime_error("round105_type_only_transform_readback_failed");
        variables<<i<<','<<domain.names[i]<<','<<domain.variable_types[i]<<','<<types[i]<<','<<relaxed.count(i)<<'\n';
    }
    variables.flush();if(!variables)throw std::runtime_error("round105_variables_persist_failed");
    // Complete initial route embedding is checked against EVERY original row.
    const auto normalized=normalizeRound61Routes(in,opt.lambda,complete_seed);
    const auto start=mapVerifiedRoutesToCanonicalModel(in,model_opt,normalized,"paid_ENS_startup",0,GU,U0,observed);
    if(!start.complete)throw std::runtime_error("round105_start_mapping:"+start.failure_reason);
    int rows=0;session.check(api.getintattr(master.value,"NumConstrs",&rows));SolverNeutralLinearModel linear;
    if(!readLinearModel(api,master.value,n,rows,linear))throw std::runtime_error("round105_matrix_read_failed");
    const auto residual=validateCandidateLinearResidual(linear,start.values,1e-7);
    if(!residual.valid)throw std::runtime_error("round105_start_row_residual_failed");
    session.check(api.setdblattrarray(master.value,"Start",0,n,const_cast<double*>(start.values.data())));
    std::ofstream embedding(dir/"embedding.json");embedding<<std::setprecision(17)<<"{\"U0\":"<<U0
        <<",\"gamma_L\":0,\"gamma_U\":"<<GU<<",\"epsilon\":0,\"all_columns\":"<<n
        <<",\"checked_rows\":"<<residual.checked_rows<<",\"max_row_violation\":"<<residual.maximum_violation
        <<",\"original_sha256\":"<<std::quoted(original.sha256)<<"}\n";
    embedding.flush();if(!embedding)throw std::runtime_error("round105_embedding_persist_failed");
    session.check(api.write(master.value,(dir/"master_0.lp").string().c_str()));
    session.check(api.write(master.value,(dir/"start.mst").string().c_str()));
    std::ofstream patterns(dir/"patterns.csv"),cuts(dir/"conflicts.csv");
    patterns<<"iteration,vehicle,station,operation,inventory,source\n";
    cuts<<"iteration,vehicle,groups,positive_groups,negative_groups,core_confirmed,row_name,rhs,variable,coefficient\n";
    std::map<std::string,Round105OracleResult> cache;std::set<std::string> candidates;
    long long iteration=0,cut_count=0,cache_hits=0,feasible=0,infeasible=0,unknown=0;
    std::string stop="global_deadline";
    try {
    while(session.remaining()>0) {
        ++iteration;const auto path=dir/("master_"+std::to_string(iteration)+".lp");
        session.check(api.write(master.value,path.string().c_str()));
        const int status=session.optimize(master.value,"master",path);
        double bound=0;
        if(api.getdblattr(master.value,"ObjBoundC",&bound)==0 && std::isfinite(bound) && std::abs(bound)<GRB_INFINITY &&
           (status==GRB_OPTIMAL || status==GRB_TIME_LIMIT || status==GRB_INTERRUPTED))
            result.lower_bound=std::max(result.lower_bound,bound);
        if(result.lower_bound>result.upper_bound+1e-7)throw std::runtime_error("round105_LB_above_verified_UB");
        if(status==GRB_INFEASIBLE || status==GRB_INF_OR_UNBD)throw std::runtime_error("round105_master_lost_known_witness");
        if(status!=GRB_OPTIMAL) {stop="master_unknown_status_"+std::to_string(status);break;}
        const auto v=session.values(master.value);std::vector<int> inventory=in.initial;
        std::vector<Round105Pattern> p(in.M);for(int k=0;k<in.M;++k){p[k].vehicle=k;p[k].operation.assign(in.V+1,0);}
        auto integer=[&](const std::string& name) {const double val=v.at(name);
            if(!std::isfinite(val) || std::abs(val-std::round(val))>1e-5)throw std::runtime_error("round105_noninteger_candidate:"+name);
            return static_cast<int>(std::llround(val));};
        for(int i=1;i<=in.V;++i) {
            inventory[i]=integer("Y_"+std::to_string(i));int served=0;
            if(integer("state_"+std::to_string(i)+"_"+std::to_string(inventory[i]))!=1)
                throw std::runtime_error("round105_inventory_selector_mismatch");
            for(int k=0;k<in.M;++k) {
                const std::string suffix=std::to_string(k)+"_"+std::to_string(i);
                const int z=integer("z_"+suffix),pick=integer("p_"+suffix),drop=integer("d_"+suffix),mode=integer("mode_"+suffix);
                if((z!=0 && z!=1) || pick<0 || drop<0 || (pick && drop) ||
                   (z==0 && (pick || drop)) || (z==1 && !pick && !drop) ||
                   (pick && mode!=1) || (drop && mode!=0))throw std::runtime_error("round105_service_contract");
                if(z){++served;if(pick!=std::max(0,in.initial[i]-inventory[i]) || drop!=std::max(0,inventory[i]-in.initial[i]))
                    throw std::runtime_error("round105_inventory_operation_mismatch");p[k].operation[i]=pick-drop;}
                patterns<<iteration<<','<<k<<','<<i<<','<<p[k].operation[i]<<','<<inventory[i]<<",optimal_integer_master\n";
            }
            if(served!=(inventory[i]!=in.initial[i] ? 1 : 0))throw std::runtime_error("round105_unique_service_contract");
        }
        patterns.flush();if(!patterns)throw std::runtime_error("round105_patterns_persist_failed");
        const auto F=computeObjectiveParts(in,inventory,opt.lambda);
        double obj=0;session.check(api.getdblattr(master.value,"ObjVal",&obj));
        if(std::abs(obj-F.objective)>1e-7)throw std::runtime_error("round105_integer_objective_mapping_gap");
        std::string candidate;for(const auto& pattern:p)candidate+=round105PatternKey(in,pattern)+";";
        if(!candidates.insert(candidate).second)throw std::runtime_error("round105_repeated_complete_candidate");
        std::vector<RoutePlan> routes;bool cut=false,failed=false;
        for(int k=0;k<in.M;++k) {
            const auto key=round105PatternKey(in,p[k]);Round105OracleResult answer;
            const auto found=cache.find(key);
            if(found!=cache.end()){answer=found->second;++cache_hits;}
            else {
                answer=session.oracle(p[k],dir/("pattern_"+std::to_string(iteration)+"_k"+std::to_string(k)),opt.round105_decomposition=="core");
                if(answer.status==Round105OracleStatus::Feasible || answer.status==Round105OracleStatus::ProvedInfeasible)cache.emplace(key,answer);
            }
            if(answer.status==Round105OracleStatus::Feasible) {++feasible;routes.push_back(answer.route);continue;}
            if(answer.status!=Round105OracleStatus::ProvedInfeasible){++unknown;failed=true;stop="oracle_unknown:"+answer.reason;break;}
            ++infeasible;const auto conflict=round105Conflict(in,p[k],answer.core);
            std::vector<int> columns;std::vector<double> coefficients;double activity=0;
            const std::string name="r105_conflict_"+std::to_string(++cut_count);
            for(const auto& [n,c]:conflict.coefficients){columns.push_back(index.at(n));coefficients.push_back(c);activity+=c*v.at(n);
                cuts<<iteration<<','<<k<<','<<conflict.assumptions.size()<<','<<conflict.positive_groups<<','<<conflict.negative_groups<<','
                    <<answer.core_confirmed<<','<<name<<','<<conflict.rhs<<','<<n<<','<<c<<'\n';}
            if(activity<conflict.rhs+0.9)throw std::runtime_error("round105_conflict_does_not_exclude_current_pattern");
            double start_activity=0;for(std::size_t j=0;j<columns.size();++j)start_activity+=coefficients[j]*start.values[columns[j]];
            if(start_activity>conflict.rhs+1e-7)throw std::runtime_error("round105_conflict_excludes_known_feasible_start");
            session.check(api.addconstr(master.value,static_cast<int>(columns.size()),columns.data(),coefficients.data(),GRB_LESS_EQUAL,conflict.rhs,name.c_str()));
            session.check(api.updatemodel(master.value));cuts.flush();
            if(!cuts)throw std::runtime_error("round105_conflict_persist_failed");cut=true;
            // One proved conflict is enough new mathematical information.
            break;
        }
        if(failed)break;
        if(cut)continue;
        const auto verify=verifyCompletePhysicalStartingWitness(in,routes,opt.lambda);
        if(!verify.feasible || verify.final_inventory!=inventory || std::abs(verify.objective-obj)>1e-7)
            throw std::runtime_error("round105_combined_route_objective_contract");
        if(verify.objective<result.upper_bound){result.routes=routes;result.verification=verify;
            result.final_inventory=verify.final_inventory;result.G=verify.G;result.P=verify.P;
            result.objective=verify.objective;result.upper_bound=verify.objective;}
        if(std::abs(result.upper_bound-result.lower_bound)>1e-7)throw std::runtime_error("round105_optimal_master_feasible_but_not_closed");
        result.strict_certified_original_problem=true;result.strict_certificate_class="engineering_exact_assignment_route_decomposition";
        result.strict_certificate_policy_version="round105-valid-master-and-independently-verified-routes-v1";
        result.strict_certificate_rejection_reason="none";result.status="optimal";stop="certified";break;
    }
    } catch(const std::exception& ex) {
        stop="ERROR:"+std::string(ex.what());result.status="error";
        result.strict_certified_original_problem=false;
        result.strict_certificate_rejection_reason=ex.what();
        std::ofstream error(dir/"error.json");error<<std::setprecision(17)
            <<"{\"reason\":"<<std::quoted(ex.what())<<",\"LB\":"<<result.lower_bound<<",\"UB\":"<<result.upper_bound
            <<",\"iteration\":"<<iteration<<"}\n";
    }
    result.gap=result.upper_bound-result.lower_bound;
    result.certificate=result.strict_certified_original_problem ? "Valid assignment-master global bound closes with independently verified full routes" : "UNKNOWN; valid master LB and self-paid verified UB retained";
    result.external_gini_tree_global_lower_bound=result.lower_bound;
    result.notes.push_back("Round105: single global assignment master, no AM; "+stop);
    r105Witness(dir/"witness.json",result.routes,result.upper_bound);
    std::ofstream summary(dir/"summary.json");summary<<std::setprecision(17)<<std::boolalpha
        <<"{\"status\":"<<std::quoted(stop)<<",\"certified\":"<<result.strict_certified_original_problem
        <<",\"LB\":"<<result.lower_bound<<",\"UB\":"<<result.upper_bound<<",\"U0\":"<<U0
        <<",\"iterations\":"<<iteration<<",\"conflicts\":"<<cut_count<<",\"cache_hits\":"<<cache_hits
        <<",\"feasible\":"<<feasible<<",\"proved_infeasible\":"<<infeasible<<",\"unknown\":"<<unknown
        <<",\"master_calls\":"<<session.master_calls<<",\"oracle_calls\":"<<session.oracle_calls
        <<",\"iis_calls\":"<<session.iis_calls<<",\"core_confirmation_calls\":"<<session.core_calls
        <<",\"master_seconds\":"<<session.master_seconds<<",\"oracle_seconds\":"<<session.oracle_seconds
        <<",\"iis_seconds\":"<<session.iis_seconds<<",\"core_confirmation_seconds\":"<<session.core_seconds<<"}\n";
    summary.flush();if(!summary)throw std::runtime_error("round105_summary_persist_failed");
    return result;
}
