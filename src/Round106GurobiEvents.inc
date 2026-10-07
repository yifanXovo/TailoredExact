// R106 uses the existing dynamic adapter; outer and inner own distinct envs.
// All route/IIS calls are synchronous, serial and share opt's process deadline.
struct R106Row {
    std::string family;
    int vehicle=0;
    std::vector<int> columns;
    std::vector<double> coefficients;
    double rhs=0, start_activity=0;
    long long submissions=0;
};
struct R106Submission {
    long long event=0;
    double objective=0;
    std::vector<double> values;
    bool observed=false, final_accepted=false;
};
struct R106State {
    R105Session& outer;
    R105Session inner;
    const Instance& in;
    const SolveOptions& opt;
    SolveResult& result;
    const SolverNeutralModelDomain& domain;
    const SolverNeutralLinearModel& linear;
    const std::map<std::string,int>& index;
    const std::vector<double>& start;
    double U0=0, GU=0, best_callback_bound=0;
    std::vector<double> objective_coefficients;
    double objective_constant=0;
    Round106Travel travel;
    std::map<std::string,Round105OracleResult> cache;
    std::map<std::string,long long> fleets, inventories, modes;
    std::map<std::string,std::size_t> row_keys;
    std::vector<R106Row> pool;
    std::vector<R106Submission> submitted;
    std::set<std::string> submitted_fleets;
    std::string startup_fleet;
    std::ofstream events, patterns, lazy;
    long long event_count=0, repeat_count=0, cache_hits=0, lazy_calls=0, rejected=0;
    long long new_ub=0, feasible_candidates=0, unknown_candidates=0, structural_proofs=0;
    double callback_seconds=0, separation_seconds=0, audit_mapping_seconds=0;
    double first_new_candidate_seconds=-1, first_new_ub_seconds=-1, outer_termination_seconds=-1;
    bool error=false, unresolved=false, outer_cancelled=false;
    std::string stop="native_return", error_reason;

    R106State(R105Session& session,const Instance& instance,const SolveOptions& options,
       SolveResult& state,const SolverNeutralModelDomain& d,const SolverNeutralLinearModel& l,
       const std::map<std::string,int>& idx,const std::vector<double>& initial,double u,double g)
       :outer(session),inner(instance,options,session.dir/"inner"),in(instance),opt(options),
        result(state),domain(d),linear(l),index(idx),start(initial),U0(u),GU(g) {
        inner.deadline_callback=inner.strict_numeric_status=true;
        if(opt.round106_events=="struct")travel=round106ConservativeTravel(in);
        events.open(outer.dir/"events.jsonl");patterns.open(outer.dir/"patterns.csv");lazy.open(outer.dir/"lazy.csv");
        patterns<<"event,vehicle,station,operation,inventory,mode_id,source\n";
        lazy<<"event,row,family,vehicle,activity,rhs,start_activity,violation,repeat_submission,api_return,process_seconds\n";
        if(!events||!patterns||!lazy)throw std::runtime_error("round106_event_stream_open");
        std::string fleet;
        for(const auto& route:result.routes) {
            Round105Pattern p;p.vehicle=route.vehicle;p.operation.assign(in.V+1,0);
            for(const auto& op:route.operations)p.operation[op.station]=op.pickup-op.drop;
            Round105OracleResult a;a.status=Round105OracleStatus::Feasible;a.route=route;a.reason="own_paid_startup";
            const auto key=round105PatternKey(in,p);cache.emplace(key,a);fleet+=key+';';
        }
        startup_fleet=fleet;submitted_fleets.insert(fleet);
    }
    double elapsed()const{return processElapsedSeconds(opt);}
    bool expired()const{return outer.remaining()<=0;}
    static bool equal(const std::vector<double>& a,const std::vector<double>& b) {
        if(a.size()!=b.size())return false;
        for(std::size_t i=0;i<a.size();++i)if(std::abs(a[i]-b[i])>1e-5)return false;
        return true;
    }
    double activity(const R106Row& row,const std::vector<double>& x)const {
        long double v=0;for(std::size_t j=0;j<row.columns.size();++j)v+=row.coefficients[j]*x[row.columns[j]];
        return static_cast<double>(v);
    }
    bool violated(const R106Row& row,const std::vector<double>& x)const {
        const double a=activity(row,x);
        const double tolerance=std::max(1e-7,1e-6*std::max({1.0,std::abs(a),std::abs(row.rhs)}));
        return a-row.rhs>tolerance;
    }
    void snapshot(const std::filesystem::path& path,const std::vector<double>& x,double obj)const {
        std::ofstream f(path);f<<std::setprecision(17)<<"# MIPSOL snapshot, objective "<<obj<<'\n';
        for(std::size_t j=0;j<x.size();++j)if(x[j]!=0)f<<domain.names[j]<<' '<<x[j]<<'\n';
        f.flush();if(!f)throw std::runtime_error("round106_snapshot_persist_failed");
    }
    void audit(const std::vector<double>& x)const {
        if(x.size()!=domain.names.size())throw std::runtime_error("round106_candidate_dimension");
        for(std::size_t j=0;j<x.size();++j) {
            if(!std::isfinite(x[j])||x[j]<domain.lower_bounds[j]-1e-6||x[j]>domain.upper_bounds[j]+1e-6)
                throw std::runtime_error("round106_candidate_bound:"+domain.names[j]);
            if(domain.variable_types[j]!='C'&&std::abs(x[j]-std::round(x[j]))>1e-5)
                throw std::runtime_error("round106_candidate_integrality:"+domain.names[j]);
        }
        if(!validateCandidateLinearResidual(linear,x,1e-6).valid)
            throw std::runtime_error("round106_candidate_base_rows");
    }
    std::size_t add(const Round105Conflict& cut,const std::string& family,int vehicle,
                    bool allow_missing_states=false) {
        R106Row row;row.family=family;row.vehicle=vehicle;row.rhs=cut.rhs;
        std::ostringstream key;key<<std::setprecision(17)<<cut.rhs;
        for(const auto& [name,c]:cut.coefficients)if(c) {
            const auto col=index.find(name);
            if(col==index.end()) {
                if(allow_missing_states&&name.rfind("state_",0)==0)continue;
                throw std::runtime_error("round106_missing_conflict_column:"+name);
            }
            row.columns.push_back(col->second);row.coefficients.push_back(c);
            key<<'/'<<col->second<<':'<<c;
        }
        const auto old=row_keys.find(key.str());if(old!=row_keys.end())return old->second;
        row.start_activity=activity(row,start);
        if(row.start_activity>row.rhs+1e-7*std::max({1.0,std::abs(row.start_activity),std::abs(row.rhs)}))
            throw std::runtime_error("round106_conflict_excludes_legal_start");
        const std::size_t id=pool.size();row_keys.emplace(key.str(),id);pool.push_back(row);
        std::ofstream f(outer.dir/("row_"+std::to_string(id)+".csv"));f<<std::setprecision(17)
            <<"family,vehicle,rhs,start_activity,variable,coefficient\n";
        for(std::size_t j=0;j<row.columns.size();++j)f<<family<<','<<vehicle<<','<<row.rhs<<','
            <<row.start_activity<<','<<domain.names[row.columns[j]]<<','<<row.coefficients[j]<<'\n';
        f.flush();if(!f)throw std::runtime_error("round106_row_persist_failed");return id;
    }
    void cancel(GRBmodel* model,const std::string& reason,bool pending=false) {
        if(!outer_cancelled){outer_cancelled=true;outer_termination_seconds=elapsed();}
        stop=reason;unresolved=unresolved||pending;outer.api.terminate(model);
    }
    void publish(long long e,double entered,double model_obj,double true_obj,double bound,
       long long fleet,long long stock,bool repeat,bool is_start,bool is_start_fleet,const std::string& outcome,
       const std::vector<int>& inventory,const std::vector<Round105Pattern>& cars,
       const std::vector<std::size_t>& cuts,long long ub_events) {
        events<<std::setprecision(17)<<std::boolalpha<<"{\"event\":"<<e<<",\"entered_seconds\":"<<entered
          <<",\"published_seconds\":"<<elapsed()<<",\"model_objective\":"<<model_obj<<",\"Ftrue\":"<<true_obj
          <<",\"native_global_bound\":";
        if(std::isfinite(bound)&&std::abs(bound)<GRB_INFINITY)events<<bound;else events<<"null";
        events<<",\"bound_requires_post_return_numeric_gate\":true,\"fleet_id\":"<<fleet<<",\"inventory_id\":"<<stock
          <<",\"repeat\":"<<repeat<<",\"matches_start_vector\":"<<is_start<<",\"matches_start_fleet\":"<<is_start_fleet<<",\"outcome\":"<<std::quoted(outcome)
          <<",\"physical_ub_events\":"<<ub_events<<",\"own_UB\":"<<result.upper_bound<<",\"Y\":[";
        for(int i=1;i<=in.V;++i){if(i>1)events<<',';events<<inventory[i];}
        events<<"],\"operations\":[";
        for(int k=0;k<in.M;++k){if(k)events<<',';events<<'[';for(int i=1;i<=in.V;++i){if(i>1)events<<',';events<<cars[k].operation[i];}events<<']';}
        events<<"],\"submitted_lazy_rows\":[";for(std::size_t j=0;j<cuts.size();++j){if(j)events<<',';events<<cuts[j];}
        events<<"]}\n";events.flush();if(!events)throw std::runtime_error("round106_event_persist_failed");
    }
    void candidate(GRBmodel* master,void* cbdata) {
        const double entered=elapsed();const long long e=++event_count;const auto audit_start=Clock::now();
        std::vector<double> x(domain.names.size());double model_obj=0,bound=-GRB_INFINITY;
        outer.check(outer.api.cbget(cbdata,GRB_CB_MIPSOL,GRB_CB_MIPSOL_SOL,x.data()));
        outer.check(outer.api.cbget(cbdata,GRB_CB_MIPSOL,GRB_CB_MIPSOL_OBJ,&model_obj));
        outer.check(outer.api.cbget(cbdata,GRB_CB_MIPSOL,GRB_CB_MIPSOL_OBJBND,&bound));
        if(std::isfinite(bound)&&std::abs(bound)<GRB_INFINITY)best_callback_bound=std::max(best_callback_bound,bound);
        audit(x);
        auto integer=[&](const std::string& name){return static_cast<int>(std::llround(x.at(index.at(name))));};
        std::vector<int> inventory=in.initial;std::vector<Round105Pattern> cars(in.M);
        for(int k=0;k<in.M;++k){cars[k].vehicle=k;cars[k].operation.assign(in.V+1,0);}
        for(int i=1;i<=in.V;++i) {
            inventory[i]=integer("Y_"+std::to_string(i));int served=0;
            if(integer("state_"+std::to_string(i)+"_"+std::to_string(inventory[i]))!=1)
                throw std::runtime_error("round106_state_mapping");
            for(int k=0;k<in.M;++k) {
                const std::string suffix=std::to_string(k)+"_"+std::to_string(i);
                const int z=integer("z_"+suffix),p=integer("p_"+suffix),d=integer("d_"+suffix),m=integer("mode_"+suffix);
                if((z!=0&&z!=1)||p<0||d<0||(p&&d)||(!z&&(p||d))||(z&&!p&&!d)||
                   (p&&m!=1)||(d&&m!=0))throw std::runtime_error("round106_service_mapping");
                if(z){++served;if(p!=std::max(0,in.initial[i]-inventory[i])||d!=std::max(0,inventory[i]-in.initial[i]))
                    throw std::runtime_error("round106_inventory_operation_mapping");cars[k].operation[i]=p-d;}
            }
            if(served!=(inventory[i]!=in.initial[i]?1:0))throw std::runtime_error("round106_unique_service");
        }
        const auto F=computeObjectiveParts(in,inventory,opt.lambda);
        long double dot=objective_constant;for(std::size_t j=0;j<x.size();++j)dot+=objective_coefficients[j]*x[j];
        if(!std::isfinite(model_obj)||!std::isfinite(F.objective)||std::abs(static_cast<double>(dot)-model_obj)>1e-7*std::max(1.0,std::abs(model_obj)))
            throw std::runtime_error("round106_snapshot_objective_contract");
        if(model_obj<F.objective-1e-7)throw std::runtime_error("round106_model_objective_below_true_F");
        std::string fleet,stock;std::vector<std::string> keys;
        for(int i=1;i<=in.V;++i)stock+=std::to_string(inventory[i])+',';
        for(const auto& p:cars){auto key=round105PatternKey(in,p);keys.push_back(key);fleet+=key+';';
            if(!modes.count(key))modes.emplace(key,modes.size()+1);}
        const bool repeat=fleets.count(fleet)!=0;if(repeat)++repeat_count;
        else{fleets.emplace(fleet,fleets.size()+1);if(first_new_candidate_seconds<0&&fleet!=startup_fleet)first_new_candidate_seconds=entered;}
        if(!inventories.count(stock))inventories.emplace(stock,inventories.size()+1);
        snapshot(outer.dir/("candidate_"+std::to_string(e)+".sol"),x,model_obj);
        for(int k=0;k<in.M;++k)for(int i=1;i<=in.V;++i)patterns<<e<<','<<k<<','<<i<<','<<cars[k].operation[i]
            <<','<<inventory[i]<<','<<modes.at(keys[k])<<",MIPSOL_SOL\n";
        patterns.flush();if(!patterns)throw std::runtime_error("round106_pattern_persist_failed");
        for(auto& s:submitted)if(!s.observed&&equal(x,s.values))s.observed=true;
        audit_mapping_seconds+=std::chrono::duration<double>(Clock::now()-audit_start).count();
        std::vector<std::size_t> cuts;
        auto collect=[&](){cuts.clear();for(std::size_t j=0;j<pool.size();++j)if(violated(pool[j],x))cuts.push_back(j);};
        collect();
        // Check every car's own-run cache before the uniform arithmetic scan.
        for(int k=0;k<in.M;++k) {
            const auto hit=cache.find(keys[k]);if(hit==cache.end())continue;++cache_hits;
            if(hit->second.status==Round105OracleStatus::ProvedInfeasible)
                add(round105Conflict(in,cars[k],hit->second.core),hit->second.core_confirmed?"CORE":"FULL",k);
        }
        if(opt.round106_events=="struct"&&!expired()) {
            const auto tick=Clock::now();
            for(int k=0;k<in.M&&!expired();++k)for(const auto& c:round106Separate(in,cars[k],travel,[&](){return expired();})) {
                ++structural_proofs;round106WriteCertificate(outer.dir/("certificate_"+std::to_string(e)+"_"+std::to_string(structural_proofs)+".json"),c);
                add(c.row,c.family,k,c.family=="B_THRESHOLD");
                // A has no Q premise; only these compatible common h/T parameters transfer.
                if(c.family=="A_MST")for(int other=0;other<in.M;++other)if(other!=k) {
                    auto cross=c.row;cross.coefficients.clear();
                    for(int i:c.support){cross.coefficients["p_"+std::to_string(other)+"_"+std::to_string(i)]=c.handling_lower;
                        cross.coefficients["z_"+std::to_string(other)+"_"+std::to_string(i)]=c.travel_lower;}
                    add(cross,"A_MST_COMPATIBLE",other);
                }
            }
            separation_seconds+=std::chrono::duration<double>(Clock::now()-tick).count();
        }
        collect();
        std::vector<RoutePlan> routes;
        if(cuts.empty())for(int k=0;k<in.M;++k) {
            if(expired())break;
            Round105OracleResult answer;const auto found=cache.find(keys[k]);
            if(found!=cache.end())answer=found->second;
            else {
                answer=inner.oracle(cars[k],outer.dir/("event_"+std::to_string(e)+"_k"+std::to_string(k)),opt.round106_events=="core");
                if(answer.status==Round105OracleStatus::Feasible||answer.status==Round105OracleStatus::ProvedInfeasible)cache.emplace(keys[k],answer);
            }
            if(answer.status==Round105OracleStatus::Feasible){routes.push_back(answer.route);continue;}
            if(answer.status==Round105OracleStatus::ProvedInfeasible) {
                add(round105Conflict(in,cars[k],answer.core),answer.core_confirmed?"CORE":"FULL",k);collect();
                if(cuts.empty())throw std::runtime_error("round106_proved_mode_without_raw_violated_lazy");break;
            }
            if(answer.status==Round105OracleStatus::Error)throw std::runtime_error("round106_inner_error:"+answer.reason);
            break;
        }
        if(!cuts.empty()) {
            // Re-submit known violated rows; success on an earlier event is no rejection now.
            for(std::size_t id:cuts) {
                auto& row=pool[id];const double a=activity(row,x);
                if(!violated(row,x))throw std::runtime_error("round106_attempted_nonviolated_lazy");
                const int rc=outer.api.cblazy(cbdata,static_cast<int>(row.columns.size()),row.columns.data(),row.coefficients.data(),GRB_LESS_EQUAL,row.rhs);
                lazy<<std::setprecision(17)<<e<<','<<id<<','<<row.family<<','<<row.vehicle<<','<<a<<','<<row.rhs
                    <<','<<row.start_activity<<','<<a-row.rhs<<','<<(row.submissions>0)<<','<<rc<<','<<elapsed()<<'\n';
                lazy.flush();outer.check(rc);++row.submissions;++lazy_calls;
            }
            if(!lazy)throw std::runtime_error("round106_lazy_ledger_persist_failed");++rejected;
            publish(e,entered,model_obj,F.objective,bound,fleets.at(fleet),inventories.at(stock),repeat,equal(x,start),fleet==startup_fleet,"REJECTED_PROVED_LAZY",inventory,cars,cuts,0);
            if(expired())cancel(master,"global_deadline_after_valid_rejection");return;
        }
        if(routes.size()!=static_cast<std::size_t>(in.M)) {
            ++unknown_candidates;cancel(master,expired()?"global_deadline_unresolved_candidate":"oracle_UNKNOWN_unresolved_candidate",true);
            publish(e,entered,model_obj,F.objective,bound,fleets.at(fleet),inventories.at(stock),repeat,equal(x,start),fleet==startup_fleet,"UNKNOWN_SAFE_INTERRUPT",inventory,cars,cuts,0);return;
        }
        const auto mapping_tick=Clock::now();
        const auto verify=verifyCompletePhysicalStartingWitness(in,routes,opt.lambda);
        if(!verify.feasible||verify.final_inventory!=inventory||std::abs(verify.objective-F.objective)>1e-7)
            throw std::runtime_error("round106_combined_physical_witness");
        ++feasible_candidates;bool improvement=verify.objective<result.upper_bound-1e-7;
        if(improvement) {
            result.routes=routes;result.verification=verify;result.final_inventory=inventory;
            result.objective=result.upper_bound=verify.objective;result.G=verify.G;result.P=verify.P;
            ++new_ub;if(first_new_ub_seconds<0)first_new_ub_seconds=elapsed();
            r105Witness(outer.dir/("physical_ub_"+std::to_string(new_ub)+".json"),routes,verify.objective);
        }
        if(!expired()&&(improvement||!submitted_fleets.count(fleet))) {
            auto map_opt=opt;map_opt.round106_events="off";
            const auto mapped=mapVerifiedRoutesToCanonicalModel(in,map_opt,normalizeRound61Routes(in,opt.lambda,routes),"R106_own_verified_routes",0,GU,U0,domain);
            if(!mapped.complete)throw std::runtime_error("round106_witness_mapping:"+mapped.failure_reason);
            audit(mapped.values);for(const auto& row:pool)if(violated(row,mapped.values))throw std::runtime_error("round106_physical_witness_violates_proved_row");
            double returned=GRB_INFINITY;const double attempt=elapsed();
            const int rc=outer.api.cbsolution(cbdata,mapped.values.data(),&returned);
            std::ofstream f(outer.dir/("submission_"+std::to_string(submitted.size()+1)+".json"));f<<std::setprecision(17)
              <<"{\"event\":"<<e<<",\"attempt_seconds\":"<<attempt<<",\"physical_F\":"<<verify.objective
              <<",\"physical_UB_established\":true,\"api_return\":"<<rc<<",\"returned_objective\":";
            if(std::abs(returned)<GRB_INFINITY)f<<returned;else f<<"null";
            f<<",\"deferred_at_MIPSOL\":true}\n";f.flush();if(!f)throw std::runtime_error("round106_submission_persist_failed");
            outer.check(rc);submitted.push_back({e,verify.objective,mapped.values,false,false});submitted_fleets.insert(fleet);
            snapshot(outer.dir/("submission_"+std::to_string(submitted.size())+".sol"),mapped.values,verify.objective);
        }
        audit_mapping_seconds+=std::chrono::duration<double>(Clock::now()-mapping_tick).count();
        publish(e,entered,model_obj,F.objective,bound,fleets.at(fleet),inventories.at(stock),repeat,equal(x,start),fleet==startup_fleet,"FEASIBLE_PHYSICAL",inventory,cars,cuts,improvement?1:0);
        if(expired())cancel(master,"global_deadline_after_verified_candidate");
    }
    static int __stdcall callback(GRBmodel* master,void* cbdata,int where,void* userdata) {
        auto& s=*static_cast<R106State*>(userdata);const auto tick=Clock::now();
        try {
            if(s.error||s.outer_cancelled) {s.outer.api.terminate(master);}
            else if(where==GRB_CB_MIPSOL)s.candidate(master,cbdata);
            else {
                if(where==GRB_CB_MIP) {
                    double b=-GRB_INFINITY;s.outer.check(s.outer.api.cbget(cbdata,where,GRB_CB_MIP_OBJBND,&b));
                    if(std::isfinite(b)&&std::abs(b)<GRB_INFINITY)s.best_callback_bound=std::max(s.best_callback_bound,b);
                }
                if(s.expired())s.cancel(master,"global_deadline_in_master");
            }
        }catch(const std::exception& ex){s.error=true;s.error_reason=ex.what();s.cancel(master,"ERROR:"+s.error_reason,true);}
        catch(...){s.error=true;s.error_reason="nonstandard_callback_exception";s.cancel(master,"ERROR:"+s.error_reason,true);}
        s.callback_seconds+=std::chrono::duration<double>(Clock::now()-tick).count();return 0;
    }
};

SolveResult r106Finish(R105Session& session,R105Model& master,R106State& state,
    SolveResult& result,const std::filesystem::path& dir,const std::filesystem::path& path) {
    auto& api=session.api;const int n=static_cast<int>(state.domain.names.size());
    const double U0=state.U0;const auto& opt=state.opt;
    int status=GRB_TIME_LIMIT;double final_bound=0;bool final_bound_available=false;
    const double qualified_before=result.lower_bound;
    try {
        session.check(api.setcallbackfunc(master.value,R106State::callback,&state));
        status=session.optimize(master.value,"master",path);
        session.check(api.setcallbackfunc(master.value,nullptr,nullptr));
        final_bound_available=api.getdblattr(master.value,"ObjBoundC",&final_bound)==0&&std::isfinite(final_bound)&&std::abs(final_bound)<GRB_INFINITY;
        if(state.error)throw std::runtime_error(state.error_reason);
        if(status==GRB_INFEASIBLE||status==GRB_INF_OR_UNBD)throw std::runtime_error("round106_master_lost_known_legal_start");
        double proposed_bound=qualified_before;
        if(status==GRB_OPTIMAL||status==GRB_TIME_LIMIT||status==GRB_INTERRUPTED) {
            proposed_bound=std::max(proposed_bound,state.best_callback_bound);
            // An unresolved candidate can be tentatively native-accepted after terminate.
            // Only the pre-candidate global bounds remain admissible on that branch.
            if(!state.unresolved&&final_bound_available)proposed_bound=std::max(proposed_bound,final_bound);
        }
        if(proposed_bound>result.upper_bound+1e-7)throw std::runtime_error("round106_LB_above_own_physical_UB");
        int count=0;session.check(api.getintattr(master.value,"SolCount",&count));
        if(count>0) {
            std::vector<double> x(n);session.check(api.getdblattrarray(master.value,"X",0,n,x.data()));
            for(auto& s:state.submitted)if(R106State::equal(x,s.values))s.final_accepted=true;
        }
        result.lower_bound=proposed_bound;
        if(!state.unresolved&&std::abs(result.upper_bound-result.lower_bound)<=1e-7) {
            result.strict_certified_original_problem=true;result.status="optimal";state.stop="certified";
            result.strict_certificate_class="engineering_exact_MIPSOL_structural_route_learning";
            result.strict_certificate_policy_version="round106-qualified-global-master-own-physical-UB-v1";
            result.strict_certificate_rejection_reason="none";
        } else if(!state.outer_cancelled)state.stop="native_status_"+std::to_string(status);
    }catch(const std::exception& ex){result.lower_bound=qualified_before;state.error=true;state.error_reason=ex.what();state.stop="ERROR:"+state.error_reason;result.status="error";
        result.strict_certified_original_problem=false;result.strict_certificate_rejection_reason=ex.what();session.check(api.setcallbackfunc(master.value,nullptr,nullptr));}
    result.gap=result.upper_bound-result.lower_bound;result.external_gini_tree_global_lower_bound=result.lower_bound;
    result.certificate=result.strict_certified_original_problem?"Qualified single-master global LB closes with own independently verified physical routes":"UNKNOWN; own physical UB and qualified global LB retained";
    result.notes.push_back("Round106 single MIPSOL/lazy master; "+state.stop);r105Witness(dir/"witness.json",result.routes,result.upper_bound);
    std::ofstream acceptance(dir/"submission_acceptance.csv");acceptance<<"event,physical_F,observed_MIPSOL_vector,final_native_accepted\n";
    for(const auto& s:state.submitted)acceptance<<std::setprecision(17)<<s.event<<','<<s.objective<<','<<s.observed<<','<<s.final_accepted<<'\n';
    acceptance.flush();if(!acceptance)throw std::runtime_error("round106_acceptance_persist");
    if(state.error){std::ofstream e(dir/"error.json");e<<"{\"reason\":"<<std::quoted(state.error_reason)<<"}\n";}
    std::ofstream f(dir/"summary.json");f<<std::setprecision(17)<<std::boolalpha
      <<"{\"strategy\":"<<std::quoted(opt.round106_events)<<",\"status\":"<<std::quoted(state.stop)<<",\"native_status\":"<<status
      <<",\"certified\":"<<result.strict_certified_original_problem<<",\"LB\":"<<result.lower_bound<<",\"UB\":"<<result.upper_bound<<",\"U0\":"<<U0
      <<",\"events\":"<<state.event_count<<",\"distinct_fleet_candidates\":"<<state.fleets.size()<<",\"distinct_Y\":"<<state.inventories.size()<<",\"distinct_car_modes\":"<<state.modes.size()
      <<",\"repeat_events\":"<<state.repeat_count<<",\"cache_hits\":"<<state.cache_hits<<",\"structural_proofs\":"<<state.structural_proofs
      <<",\"pool_rows\":"<<state.pool.size()<<",\"lazy_calls\":"<<state.lazy_calls<<",\"rejected_events\":"<<state.rejected
      <<",\"feasible_candidates\":"<<state.feasible_candidates<<",\"unknown_candidates\":"<<state.unknown_candidates<<",\"new_physical_UBs\":"<<state.new_ub
      <<",\"submission_attempts\":"<<state.submitted.size()<<",\"master_calls\":"<<session.master_calls<<",\"oracle_calls\":"<<state.inner.oracle_calls<<",\"iis_calls\":"<<state.inner.iis_calls
      <<",\"core_confirmation_calls\":"<<state.inner.core_calls<<",\"master_inclusive_seconds\":"<<session.master_seconds<<",\"callback_inclusive_seconds\":"<<state.callback_seconds
      <<",\"master_exclusive_seconds\":"<<session.master_seconds-state.callback_seconds<<",\"oracle_seconds\":"<<state.inner.oracle_seconds<<",\"iis_seconds\":"<<state.inner.iis_seconds
      <<",\"core_confirmation_seconds\":"<<state.inner.core_seconds<<",\"separation_seconds\":"<<state.separation_seconds<<",\"audit_mapping_seconds\":"<<state.audit_mapping_seconds
      <<",\"callback_other_seconds\":"<<state.callback_seconds-state.inner.oracle_seconds-state.inner.iis_seconds-state.inner.core_seconds-state.separation_seconds-state.audit_mapping_seconds
      <<",\"first_new_candidate_seconds\":"<<state.first_new_candidate_seconds<<",\"first_new_physical_UB_seconds\":"<<state.first_new_ub_seconds
      <<",\"outer_cancelled\":"<<state.outer_cancelled<<",\"outer_termination_seconds\":"<<state.outer_termination_seconds
      <<",\"inner_cancelled\":"<<state.inner.cancellation_requested<<",\"inner_termination_seconds\":"<<state.inner.cancellation_seconds
      <<",\"unresolved_candidate\":"<<state.unresolved<<",\"final_native_bound\":";
    if(final_bound_available)f<<final_bound;else f<<"null";
    f<<",\"final_native_bound_qualified\":"<<(!state.error&&!state.unresolved&&final_bound_available&&
       (status==GRB_OPTIMAL||status==GRB_TIME_LIMIT||status==GRB_INTERRUPTED))<<"}\n";
    f.flush();if(!f)throw std::runtime_error("round106_summary_persist_failed");return result;
}

SolveResult r106Solve(const Instance& in,const SolveOptions& opt,const SolveResult& seed,SolveResult& result) {
    if(!hasMetricTravelLowerBounds(in)||!std::isfinite(opt.lambda)||opt.lambda<0)
        throw std::runtime_error("round106_master_metric_nonnegative_contract");
    for(double w:in.weights)if(!std::isfinite(w)||w<0)throw std::runtime_error("round106_weight_contract");
    result.strict_certified_original_problem=false;result.strict_certificate_class="certificate_rejected";
    result.strict_lower_bound_source="nonnegative_then_qualified_global_assignment_master_bound";
    result.strict_native_model_scope="single_MIPSOL_lazy_assignment_master";result.lower_bound=0;result.status="time_limit";
    std::vector<RoutePlan> complete(in.M);std::set<int> seen;
    for(int k=0;k<in.M;++k)complete[k]={k,{0,0},{}};
    for(const auto& r:seed.routes){if(r.vehicle<0||r.vehicle>=in.M||!seen.insert(r.vehicle).second)throw std::runtime_error("round106_seed_vehicle");complete[r.vehicle]=r;}
    const auto seed_verify=verifyCompletePhysicalStartingWitness(in,complete,opt.lambda);
    if(!seed_verify.feasible||std::abs(seed_verify.objective-seed.upper_bound)>1e-7)throw std::runtime_error("round106_invalid_paid_startup");
    result.routes=complete;result.verification=seed_verify;result.final_inventory=seed_verify.final_inventory;
    result.G=seed_verify.G;result.P=seed_verify.P;result.objective=result.upper_bound=seed_verify.objective;
    const double U0=seed_verify.objective,GU=std::min(1.0,U0);
    const auto dir=std::filesystem::path(opt.external_gini_artifact_dir)/"round106";
    R105Session session(in,opt,dir);session.strict_numeric_status=true;auto& api=session.api;r105Witness(dir/"seed.json",complete,U0);
    auto model_opt=opt;model_opt.round105_decomposition=model_opt.round106_events="off";
    CanonicalCompactModelSpec spec;spec.strengthened=true;spec.interval_restricted=true;spec.gamma_L=0;spec.gamma_U=GU;
    spec.add_verified_incumbent_row=true;spec.verified_incumbent=U0;spec.incumbent_epsilon=0;
    spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    const auto original=writeCanonicalCompactModel(in,model_opt,dir/"original.lp",spec);
    if(!original.written)throw std::runtime_error(original.failure_reason);
    R105Model master;session.read(master,original.path);auto domain=session.domain(master.value);
    const int n=static_cast<int>(domain.names.size());std::map<std::string,int> index;
    for(int j=0;j<n;++j)if(!index.emplace(domain.names[j],j).second)throw std::runtime_error("round106_duplicate_column");
    auto require=[&](const std::string& name,char type){const int j=index.at(name);if(domain.variable_types[j]!=type)throw std::runtime_error("round106_master_type:"+name);return j;};
    std::set<int> relaxed;
    for(int k=0;k<in.M;++k) {
        for(int i=0;i<=in.V;++i)for(int j=0;j<=in.V;++j)if(i!=j)relaxed.insert(require("x_"+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(j),'B'));
        for(int i=1;i<=in.V;++i){const std::string s=std::to_string(k)+"_"+std::to_string(i);
            relaxed.insert(require("load_"+s,'I'));require("z_"+s,'B');require("mode_"+s,'B');require("p_"+s,'I');require("d_"+s,'I');require("ord_"+s,'C');}
    }
    for(int i=1;i<=in.V;++i){require("Y_"+std::to_string(i),'I');bool found=false;
        for(int y=0;y<=in.capacity[i];++y){const std::string name="state_"+std::to_string(i)+"_"+std::to_string(y);if(index.count(name)){require(name,'B');found=true;}}
        if(!found)throw std::runtime_error("round106_missing_state_columns");}
    auto types=domain.variable_types;for(int j:relaxed)types[j]='C';session.check(api.setcharattrarray(master.value,"VType",0,n,types.data()));session.check(api.updatemodel(master.value));
    const auto observed=session.domain(master.value);std::ofstream variables(dir/"variables.csv");variables<<"index,name,old_type,master_type,relaxed\n";
    for(int j=0;j<n;++j){if(observed.names[j]!=domain.names[j]||observed.lower_bounds[j]!=domain.lower_bounds[j]||observed.upper_bounds[j]!=domain.upper_bounds[j]||observed.variable_types[j]!=types[j])throw std::runtime_error("round106_type_readback");
        variables<<j<<','<<domain.names[j]<<','<<domain.variable_types[j]<<','<<types[j]<<','<<relaxed.count(j)<<'\n';}
    variables.flush();if(!variables)throw std::runtime_error("round106_variables_persist");
    const auto start=mapVerifiedRoutesToCanonicalModel(in,model_opt,normalizeRound61Routes(in,opt.lambda,complete),"own_paid_ENS_startup",0,GU,U0,observed);
    if(!start.complete)throw std::runtime_error("round106_start_mapping:"+start.failure_reason);
    int rows=0;session.check(api.getintattr(master.value,"NumConstrs",&rows));SolverNeutralLinearModel linear;
    if(!readLinearModel(api,master.value,n,rows,linear))throw std::runtime_error("round106_base_matrix_read");
    const auto residual=validateCandidateLinearResidual(linear,start.values,1e-7);
    if(!residual.valid)throw std::runtime_error("round106_start_base_row_residual");
    session.check(api.setdblattrarray(master.value,"Start",0,n,const_cast<double*>(start.values.data())));
    session.check(api.setintparam(api.getenv(master.value),"LazyConstraints",1));
    std::ofstream embedding(dir/"embedding.json");embedding<<std::setprecision(17)<<"{\"U0\":"<<U0<<",\"gamma_L\":0,\"gamma_U\":"<<GU<<",\"epsilon\":0,\"all_columns\":"<<n
      <<",\"checked_rows\":"<<rows<<",\"max_row_violation\":"<<residual.maximum_violation<<",\"original_sha256\":"<<std::quoted(original.sha256)<<",\"LazyConstraints\":1}\n";
    embedding.flush();if(!embedding)throw std::runtime_error("round106_embedding_persist");
    const auto path=dir/"master_0.lp";session.check(api.write(master.value,path.string().c_str()));session.check(api.write(master.value,(dir/"start.mst").string().c_str()));
    R106State state(session,in,opt,result,observed,linear,index,start.values,U0,GU);
    state.objective_coefficients.resize(n);session.check(api.getdblattrarray(master.value,"Obj",0,n,state.objective_coefficients.data()));session.check(api.getdblattr(master.value,"ObjCon",&state.objective_constant));
    return r106Finish(session,master,state,result,dir,path);
}
