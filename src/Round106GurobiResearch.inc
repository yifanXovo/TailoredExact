// Offline qualification/diagnosis. None of these entry points is in main's
// production dispatch; historical starts never enter a formal arm.
std::vector<double> r106FileVector(const std::filesystem::path& path,
    const SolverNeutralModelDomain& d) {
    std::map<std::string,int> idx;for(std::size_t j=0;j<d.names.size();++j)idx.emplace(d.names[j],j);
    std::vector<double> x(d.names.size());std::ifstream f(path);if(!f)throw std::runtime_error("offline_vector_missing");
    std::string line;while(std::getline(f,line)) {
        if(line.empty()||line[0]=='#')continue;std::istringstream s(line);std::string name;double v=0;
        if(!(s>>name>>v)||!std::isfinite(v)||!idx.count(name))throw std::runtime_error("offline_vector_column:"+name);
        x[idx.at(name)]=v;
    }return x;
}
std::vector<RoutePlan> r106FleetDecode(const Instance& in,
    const SolverNeutralModelDomain& d,const std::vector<double>& x) {
    std::map<std::string,double> v;for(std::size_t j=0;j<d.names.size();++j)v.emplace(d.names[j],x[j]);
    std::vector<RoutePlan> routes;
    for(int k=0;k<in.M;++k) {
        RoutePlan r{k,{0},{}};int current=0;std::set<int> seen;
        while(true) {
            int next=-1;
            for(int j=0;j<=in.V;++j)if(j!=current&&v.at("x_"+std::to_string(k)+"_"+std::to_string(current)+"_"+std::to_string(j))>.5) {
                if(next!=-1)throw std::runtime_error("offline_fleet_ambiguous_arc");next=j;
            }
            if(next<0){if(current==0&&seen.empty())r.nodes.push_back(0);else throw std::runtime_error("offline_fleet_open_route");break;}
            r.nodes.push_back(next);if(!next)break;
            if(!seen.insert(next).second)throw std::runtime_error("offline_fleet_cycle");
            const auto tail=std::to_string(k)+"_"+std::to_string(next);
            r.operations.push_back({next,static_cast<int>(std::llround(v.at("p_"+tail))),static_cast<int>(std::llround(v.at("d_"+tail)))});current=next;
        }
        for(int i=1;i<=in.V;++i) {
            const auto tail=std::to_string(k)+"_"+std::to_string(i);
            if(bool(seen.count(i))!=bool(v.at("p_"+tail)>.5||v.at("d_"+tail)>.5))throw std::runtime_error("offline_fleet_service_mapping");
        }routes.push_back(r);
    }return routes;
}
SolveResult r106Replay(const Instance& in,const SolveOptions& opt,
    const std::filesystem::path& source,const std::filesystem::path& candidate,
    const std::filesystem::path& legal_start) {
    const auto dir=std::filesystem::path(opt.external_gini_artifact_dir)/"round106";
    R105Session session(in,opt,dir);session.strict_numeric_status=true;
    R105Model master;session.read(master,source);auto d=session.domain(master.value);
    const auto start=r106FileVector(legal_start,d),bad=r106FileVector(candidate,d);
    SolveResult result;result.routes=r106FleetDecode(in,d,start);
    result.verification=verifyCompletePhysicalStartingWitness(in,result.routes,opt.lambda);
    if(!result.verification.feasible)throw std::runtime_error("offline_start_not_physical");
    result.final_inventory=result.verification.final_inventory;
    result.objective=result.upper_bound=result.verification.objective;result.lower_bound=0;result.status="time_limit";
    int rows=0;session.check(session.api.getintattr(master.value,"NumConstrs",&rows));SolverNeutralLinearModel linear;
    if(!readLinearModel(session.api,master.value,static_cast<int>(d.names.size()),rows,linear))throw std::runtime_error("offline_matrix_read");
    std::map<std::string,int> idx;for(std::size_t j=0;j<d.names.size();++j)idx.emplace(d.names[j],j);
    R106State state(session,in,opt,result,d,linear,idx,start,result.upper_bound,std::min(1.0,result.upper_bound));
    state.objective_coefficients.resize(d.names.size());session.check(session.api.getdblattrarray(master.value,"Obj",0,static_cast<int>(d.names.size()),state.objective_coefficients.data()));
    session.check(session.api.getdblattr(master.value,"ObjCon",&state.objective_constant));state.audit(start);state.audit(bad);
    std::ofstream provenance(dir/"offline_scope.json");provenance<<"{\"layer\":\"actual_native_historical_master_candidate_replay\",\"production_handoff\":false,\"source_model_SHA\":"
      <<std::quoted(fileSha256(source))<<",\"candidate_SHA\":"<<std::quoted(fileSha256(candidate))<<",\"legal_start_SHA\":"<<std::quoted(fileSha256(legal_start))<<"}\n";
    r105Witness(dir/"seed.json",result.routes,result.upper_bound);
    session.check(session.api.setdblattrarray(master.value,"Start",0,static_cast<int>(bad.size()),const_cast<double*>(bad.data())));
    session.check(session.api.setintparam(session.api.getenv(master.value),"LazyConstraints",1));
    const auto path=dir/"master_0.lp";session.check(session.api.write(master.value,path.string().c_str()));
    return r106Finish(session,master,state,result,dir,path);
}

struct R106ScriptedSnapshot {
    std::vector<double> x;double obj=0,bound=0;int lazy=0,submissions=0;
};
int __stdcall r106ScriptedGet(void* cb,int,int what,void* out) {
    auto& s=*static_cast<R106ScriptedSnapshot*>(cb);
    if(what==GRB_CB_MIPSOL_SOL)std::copy(s.x.begin(),s.x.end(),static_cast<double*>(out));
    else if(what==GRB_CB_MIPSOL_OBJ)*static_cast<double*>(out)=s.obj;
    else if(what==GRB_CB_MIPSOL_OBJBND)*static_cast<double*>(out)=s.bound;else return 1;return 0;
}
int __stdcall r106ScriptedLazy(void* cb,int n,const int* idx,const double* c,char sense,double rhs) {
    auto& s=*static_cast<R106ScriptedSnapshot*>(cb);double a=0;for(int j=0;j<n;++j)a+=c[j]*s.x[idx[j]];
    if(sense!=GRB_LESS_EQUAL||a-rhs<=std::max(1e-7,1e-6*std::max({1.,std::abs(a),std::abs(rhs)})))return 1;
    ++s.lazy;return 0;
}
int __stdcall r106ScriptedSolution(void* cb,const double*,double* obj) {
    ++static_cast<R106ScriptedSnapshot*>(cb)->submissions;*obj=GRB_INFINITY;return 0;
}
void __stdcall r106ScriptedTerminate(GRBmodel*) {}
void r106Contracts(const Instance& in,const SolveOptions& supplied,
    const std::filesystem::path& retained,const std::filesystem::path& inf,
    const std::filesystem::path& feas,const std::filesystem::path& initial) {
    auto opt=supplied;opt.round106_events="full";
    const auto dir=std::filesystem::path(opt.external_gini_artifact_dir);
    R105Session session(in,opt,dir);R105Model model;session.read(model,retained);
    const auto d=session.domain(model.value);auto start=r106FileVector(initial,d);
    SolveResult result;result.routes=r106FleetDecode(in,d,start);
    result.verification=verifyCompletePhysicalStartingWitness(in,result.routes,opt.lambda);
    if(!result.verification.feasible)throw std::runtime_error("scripted_start_physical");
    result.objective=result.upper_bound=result.verification.objective;result.final_inventory=result.verification.final_inventory;
    int rows=0;session.check(session.api.getintattr(model.value,"NumConstrs",&rows));SolverNeutralLinearModel linear;
    if(!readLinearModel(session.api,model.value,static_cast<int>(d.names.size()),rows,linear))throw std::runtime_error("scripted_matrix_read");
    std::map<std::string,int> idx;for(std::size_t j=0;j<d.names.size();++j)idx.emplace(d.names[j],j);
    R106State state(session,in,opt,result,d,linear,idx,start,result.upper_bound,std::min(1.,result.upper_bound));
    state.objective_coefficients.resize(d.names.size());session.check(session.api.getdblattrarray(model.value,"Obj",0,static_cast<int>(d.names.size()),state.objective_coefficients.data()));
    session.check(session.api.getdblattr(model.value,"ObjCon",&state.objective_constant));
    auto objective=[&](const std::vector<double>& x){double a=state.objective_constant;for(std::size_t j=0;j<x.size();++j)a+=x[j]*state.objective_coefficients[j];return a;};
    auto patterns=[&](const std::vector<double>& x){std::vector<Round105Pattern> p(in.M);for(int k=0;k<in.M;++k){p[k].vehicle=k;p[k].operation.assign(in.V+1,0);
        for(int i=1;i<=in.V;++i){const auto s=std::to_string(k)+"_"+std::to_string(i);p[k].operation[i]=static_cast<int>(std::llround(x[idx.at("p_"+s)]-x[idx.at("d_"+s)]));}}return p;};
    R106ScriptedSnapshot cb;cb.x=r106FileVector(inf,d);cb.obj=objective(cb.x);state.audit(cb.x);auto p=patterns(cb.x);
    // The caller binds this INF mode to retained actual native proof evidence.
    Round105OracleResult proof;proof.status=Round105OracleStatus::ProvedInfeasible;
    for(int i=1;i<=in.V;++i)proof.core.push_back(i);
    state.cache[round105PatternKey(in,p[0])]=proof;
    for(int k=1;k<in.M;++k){Round105OracleResult unknown;unknown.status=Round105OracleStatus::Unknown;state.cache[round105PatternKey(in,p[k])]=unknown;}
    session.api.cbget=r106ScriptedGet;session.api.cblazy=r106ScriptedLazy;
    session.api.cbsolution=r106ScriptedSolution;session.api.terminate=r106ScriptedTerminate;
    state.candidate(model.value,&cb);state.candidate(model.value,&cb);
    if(cb.lazy!=2||state.rejected!=2||state.repeat_count!=1||state.inner.oracle_calls!=0)throw std::runtime_error("repeat_INF_or_other_UNKNOWN_contract");
    cb.x=r106FileVector(feas,d);cb.obj=objective(cb.x);state.audit(cb.x);
    const auto routes=r106FleetDecode(in,d,cb.x);const auto verified=verifyCompletePhysicalStartingWitness(in,routes,opt.lambda);
    if(!verified.feasible)throw std::runtime_error("scripted_FEAS_not_physical");
    p=patterns(cb.x);for(int k=0;k<in.M;++k){Round105OracleResult a;a.status=Round105OracleStatus::Feasible;a.route=routes[k];state.cache[round105PatternKey(in,p[k])]=a;}
    const bool new_feas=verified.objective<result.upper_bound-1e-7;
    state.candidate(model.value,&cb);state.candidate(model.value,&cb);
    if(cb.lazy!=2||cb.submissions!=(new_feas?1:0)||state.inner.oracle_calls!=0)throw std::runtime_error("repeat_FEAS_or_nonviolated_lazy_contract");
    bool inflated=false;
    for(int i=1;i<=in.V&&!inflated;++i) {
        auto high=cb.x;const auto j=idx.at("e_"+std::to_string(i));high[j]+=.01;
        try{state.audit(high);}catch(...){continue;}
        const double highobj=objective(high);if(highobj<=verified.objective+1e-7)continue;
        cb.x=high;cb.obj=highobj;state.candidate(model.value,&cb);inflated=true;
    }
    if(new_feas&&!inflated)throw std::runtime_error("no_valid_inflated_epigraph_witness");
    state.pool.clear();state.row_keys.clear();state.cache.clear();
    opt.process_start_time=std::chrono::steady_clock::now()-std::chrono::seconds(2);opt.process_wall_time_limit=.001;
    cb.x=r106FileVector(inf,d);cb.obj=objective(cb.x);state.candidate(model.value,&cb);
    if(!state.unresolved||state.unknown_candidates!=1||cb.lazy!=2)throw std::runtime_error("UNKNOWN_without_rejection_contract");
    std::ofstream out(dir/"contracts.json");out<<std::boolalpha<<"{\"layer\":\"scripted_callback_C_API_contract_on_audited_actual_native_vectors\",\"Optimize_calls\":0,\"IIS_calls\":0,\"repeat_INF_resubmitted\":true,\"repeat_FEAS_not_resubmitted\":true,\"nonviolated_row_not_sent\":true,\"inflated_epigraph_checked\":"<<inflated
      <<",\"physical_UB_before_native_acceptance\":"<<new_feas<<",\"one_car_reject_other_UNKNOWN\":"<<(in.M>1)<<",\"UNKNOWN_without_rejection_interrupt\":true,\"oracle_calls\":"<<state.inner.oracle_calls<<"}\n";
}

std::string r106FixedFleet(const Instance& in,const SolveOptions& opt,const std::vector<int>& Y) {
    const auto dir=std::filesystem::path(opt.external_gini_artifact_dir);
    Round61TimeRequest request;request.inventory=Y;request.directory=dir;writeRound61TimeModel(in,request);
    R105Session session(in,opt,dir);session.deadline_callback=session.strict_numeric_status=true;
    R105Model model;session.read(model,dir/"time_oracle.lp");auto d=session.domain(model.value);
    std::vector<double> zero(d.names.size());session.check(session.api.setdblattrarray(model.value,"Obj",0,static_cast<int>(zero.size()),zero.data()));
    double constant=0;session.check(session.api.getdblattr(model.value,"ObjCon",&constant));
    if(constant!=0)throw std::runtime_error("fleet_feasibility_objective_constant");
    auto t=std::find(d.names.begin(),d.names.end(),"Tstar");if(t==d.names.end())throw std::runtime_error("fleet_Tstar_missing");
    d.upper_bounds[static_cast<int>(t-d.names.begin())]=in.total_time_limit;
    session.check(session.api.setdblattrarray(model.value,"UB",0,static_cast<int>(d.names.size()),d.upper_bounds.data()));
    session.check(session.api.updatemodel(model.value));const auto path=dir/"fixed_feasibility.lp";session.check(session.api.write(model.value,path.string().c_str()));
    const int status=session.optimize(model.value,"oracle",path);int count=0;session.check(session.api.getintattr(model.value,"SolCount",&count));
    std::string classification="UNKNOWN";bool physical=false;
    if(count>0) {
        d=session.domain(model.value);std::vector<double> x(d.names.size());session.check(session.api.getdblattrarray(model.value,"X",0,static_cast<int>(x.size()),x.data()));
        const auto routes=r106FleetDecode(in,d,x);const auto v=verifyCompletePhysicalStartingWitness(in,routes,opt.lambda);
        if(!v.feasible||v.final_inventory!=Y)throw std::runtime_error("fleet_independent_physical_or_Y_validation");
        r105Witness(dir/"witness.json",routes,v.objective);classification="FEAS";physical=true;
    }else if(status==GRB_INFEASIBLE)classification="PROVED_INF";
    std::ofstream f(dir/"diagnostic.json");f<<std::setprecision(17)<<std::boolalpha<<"{\"classification\":"<<std::quoted(classification)<<",\"native_status\":"<<status
      <<",\"physical_verified\":"<<physical<<",\"Ftrue_fixed_Y\":"<<computeObjectiveParts(in,Y,opt.lambda).objective<<",\"original_T\":"<<in.total_time_limit
      <<",\"Optimize_calls\":"<<session.oracle_calls<<",\"IIS_calls\":0,\"native_seconds\":"<<session.oracle_seconds<<",\"algorithm_seconds\":"<<processElapsedSeconds(opt)
      <<",\"production_handoff\":false,\"objective\":\"zero_feasibility\",\"cancelled\":"<<session.cancellation_requested<<",\"Y\":[";
    for(int i=1;i<=in.V;++i){if(i>1)f<<',';f<<Y[i];}f<<"]}\n";f.flush();if(!f)throw std::runtime_error("fleet_result_persist");return classification;
}
