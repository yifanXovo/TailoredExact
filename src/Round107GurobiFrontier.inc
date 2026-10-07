// Scoped event adapter: original canonical domain, one Optimize per original MIP request.
struct R107SemanticRow { Round105Conflict cut;std::string family,proof;int vehicle=0;long long origin=0; };
bool r107OutsideMapping(const SolverNeutralMipStart& m) {
    return m.candidate_independently_verified && m.original_problem_feasible && m.objective_recomputed &&
        ((m.failure_reason=="verified_start_outside_static_gini_interval"&&!m.interval_membership_valid) ||
         (m.failure_reason=="verified_start_violates_non_strict_cutoff"&&m.interval_membership_valid&&!m.cutoff_valid));
}
void r107AuditEmbedding(const SolverNeutralMipStart& m,const SolverNeutralModelDomain& d,
    const SolverNeutralLinearModel& l,const std::vector<double>& obj,double constant) {
    if(!m.complete||m.values.size()!=d.names.size())throw std::runtime_error("round107_in_domain_mapping_failed:"+m.failure_reason);
    for(std::size_t j=0;j<m.values.size();++j)if(!std::isfinite(m.values[j])||m.values[j]<d.lower_bounds[j]-1e-7||
        m.values[j]>d.upper_bounds[j]+1e-7||(d.variable_types[j]!='C'&&std::abs(m.values[j]-std::round(m.values[j]))>1e-7))
        throw std::runtime_error("round107_mapped_domain_failed:"+d.names[j]);
    if(!validateCandidateLinearResidual(l,m.values,1e-7).valid)throw std::runtime_error("round107_in_domain_embedding_base_rows_failed");
    long double dot=constant;for(std::size_t j=0;j<m.values.size();++j)dot+=obj[j]*m.values[j];
    if(std::abs(static_cast<double>(dot)-m.objective)>1e-7*std::max(1.0,std::abs(m.objective)))
        throw std::runtime_error("round107_mapped_objective_contract");
}
struct R107PhysicalSession {
    SolveResult own;
    bool initialized=false;
    std::map<std::string,Round105OracleResult> cache;
    std::map<std::string,long long> cache_origin;
    std::map<std::string,std::string> cache_proof;
    std::string startup_fleet;
    std::vector<R107SemanticRow> rows;
    std::map<std::string,std::size_t> row_keys;
    std::ofstream semantic;
    std::size_t remember(const Round105Conflict& cut,const std::string& family,int k,long long request,const std::string& proof) {
        std::ostringstream key;key<<std::setprecision(17)<<cut.rhs;
        for(const auto& [n,c]:cut.coefficients)key<<'/'<<n<<':'<<c;
        const auto found=row_keys.find(key.str());if(found!=row_keys.end())return found->second;
        const std::size_t id=rows.size();row_keys.emplace(key.str(),id);rows.push_back({cut,family,proof,k,request});
        semantic<<std::setprecision(17)<<"{\"id\":"<<id<<",\"origin_request\":"<<request<<",\"family\":"<<std::quoted(family)
            <<",\"vehicle\":"<<k<<",\"proof_path\":"<<std::quoted(proof)<<",\"rhs\":"<<cut.rhs<<",\"scope\":\"global_physical\",\"coefficients\":{";
        bool first=true;for(const auto& [n,c]:cut.coefficients){if(!first)semantic<<',';first=false;semantic<<std::quoted(n)<<':'<<c;}
        semantic<<"}}\n";semantic.flush();if(!semantic)throw std::runtime_error("round107_semantic_proof_persist");return id;
    }
};

struct R107State {
    R105Session& outer;
    R107PhysicalSession& evidence;
    const FixedIntervalMipRequest& request;
    double effective_cutoff = 0, optimize_launch = 0;
    bool target_observed = false;
    long long cross_request_hits = 0, remapped_rows = 0;
    std::ofstream cache_log, remap_log, feedback_log;
    std::vector<FixedIntervalNativeBoundEvent> bound_events;
    std::set<std::string> verified_fleets;
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
    std::map<std::string,Round105OracleResult>& cache;
    std::map<std::string,long long> fleets, inventories, modes;
    std::map<std::string,std::size_t> row_keys;
    std::vector<R106Row> pool;
    std::vector<R106Submission> submitted;
    std::set<std::string> submitted_fleets;
    std::string startup_fleet;
    std::ofstream events, patterns, lazy, candidate_audit;
    long long event_count=0, repeat_count=0, cache_hits=0, lazy_calls=0, rejected=0;
    long long new_ub=0, feasible_candidates=0, unknown_candidates=0, structural_proofs=0;
    long long new_semantic_rows=0;
    double callback_seconds=0, separation_seconds=0, audit_mapping_seconds=0;
    double first_new_candidate_seconds=-1, first_new_ub_seconds=-1, outer_termination_seconds=-1;
    bool error=false, unresolved=false, outer_cancelled=false, domain_witness_embeds=false;
    std::string stop="native_return", error_reason;

    R107State(R105Session& session,const Instance& instance,const SolveOptions& options,
       SolveResult& state,const SolverNeutralModelDomain& d,const SolverNeutralLinearModel& l,
       const std::map<std::string,int>& idx,const std::vector<double>& initial,double u,double g,
       R107PhysicalSession& shared,const FixedIntervalMipRequest& scope,double actual_cutoff,
       std::function<void(const char*,double)> lifecycle)
       :outer(session),evidence(shared),request(scope),effective_cutoff(actual_cutoff),
        inner(instance,options,session.dir/"inner",std::move(lifecycle)),in(instance),opt(options),
        result(state),domain(d),linear(l),index(idx),start(initial),U0(u),GU(g),cache(shared.cache) {
        inner.deadline_callback=inner.strict_numeric_status=true;
        travel=round106ConservativeTravel(in);
        events.open(outer.dir/"events.jsonl");patterns.open(outer.dir/"patterns.csv");lazy.open(outer.dir/"lazy.csv");
        candidate_audit.open(outer.dir/"candidate_audit.jsonl");
        patterns<<"event,vehicle,station,operation,inventory,mode_id,source\n";
        lazy<<"event,row,family,vehicle,activity,rhs,start_activity,violation,repeat_submission,api_return,process_seconds\n";
        cache_log.open(outer.dir/"cache.csv");remap_log.open(outer.dir/"remap.csv");feedback_log.open(outer.dir/"feedback.jsonl");
        cache_log<<"event,vehicle,origin_request,current_request,initial,cache_status,key\n";
        remap_log<<"row,origin_request,current_request,semantic_variable,coefficient,current_column,omitted_fixed_zero,Y_lower,Y_upper,omission_proof\n";
        if(!events||!patterns||!lazy||!cache_log||!remap_log||!feedback_log||!candidate_audit)throw std::runtime_error("round107_event_stream_open");
        std::string fleet;
        for(const auto& route:result.routes) {
            Round105Pattern p;p.vehicle=route.vehicle;p.operation.assign(in.V+1,0);
            for(const auto& op:route.operations)p.operation[op.station]=op.pickup-op.drop;
            Round105OracleResult a;a.status=Round105OracleStatus::Feasible;a.route=route;a.reason="own_verified_controller_witness";
            const auto key=round105PatternKey(in,p);cache.emplace(key,a);
            evidence.cache_origin.emplace(key,evidence.startup_fleet.empty()?0:request.round107_request_id);
            evidence.cache_proof.emplace(key,(evidence.startup_fleet.empty()?outer.dir.parent_path()/"seed.json":outer.dir/"entry_witness.json").generic_string());fleet+=key+';';
        }
        r105Witness(outer.dir/"entry_witness.json",result.routes,result.upper_bound);
        if(evidence.startup_fleet.empty())evidence.startup_fleet=fleet;
        startup_fleet=evidence.startup_fleet;domain_witness_embeds=!start.empty();
        // An old request submission is never assumed submitted to this request.
        const auto inherited=evidence.rows;
        for(const auto& row:inherited){add(row.cut,row.family,row.vehicle,true,row.proof);++remapped_rows;}
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
        f.flush();if(!f)throw std::runtime_error("round107_snapshot_persist_failed");
    }
    CandidateLinearResidual audit(const std::vector<double>& x)const {
        if(x.size()!=domain.names.size())throw std::runtime_error("round107_candidate_dimension");
        for(std::size_t j=0;j<x.size();++j) {
            if(!std::isfinite(x[j])||x[j]<domain.lower_bounds[j]-1e-6||x[j]>domain.upper_bounds[j]+1e-6)
                throw std::runtime_error("round107_candidate_bound:"+domain.names[j]);
            if(domain.variable_types[j]!='C'&&std::abs(x[j]-std::round(x[j]))>1e-5)
                throw std::runtime_error("round107_candidate_integrality:"+domain.names[j]);
        }
        const auto residual=validateCandidateLinearResidual(linear,x,1e-6);
        if(!residual.valid)
            throw std::runtime_error("round107_candidate_base_rows");
        return residual;
    }
    std::size_t add(const Round105Conflict& cut,const std::string& family,int vehicle,
                    bool allow_missing_states=false,const std::string& proof="") {
        const auto previous_size=evidence.rows.size();
        const auto semantic_id=evidence.remember(cut,family,vehicle,request.round107_request_id,proof);
        if(evidence.rows.size()>previous_size)++new_semantic_rows;
        R106Row row;row.family=family;row.vehicle=vehicle;row.rhs=cut.rhs;
        std::ostringstream key;key<<std::setprecision(17)<<cut.rhs;
        for(const auto& [name,c]:cut.coefficients)if(c) {
            const auto col=index.find(name);
            if(col==index.end()) {
                if(name.rfind("state_",0)==0) {
                    // VD-P omitted selector means zero only in this current domain.
                    int station=-1,value=-1;char tail=0;
                    if(std::sscanf(name.c_str(),"state_%d_%d%c",&station,&value,&tail)!=2 ||
                        station<1||station>in.V||value<0||value>in.capacity[station])
                        throw std::runtime_error("round107_invalid_missing_state");
                    const auto y=index.at("Y_"+std::to_string(station));
                    if(value>=domain.lower_bounds[y]-1e-9&&value<=domain.upper_bounds[y]+1e-9)
                        throw std::runtime_error("round107_missing_state_inside_current_Y_domain:"+name);
                    remap_log<<semantic_id<<','<<evidence.rows[semantic_id].origin<<','<<request.round107_request_id
                        <<','<<name<<','<<c<<",-1,1,"<<domain.lower_bounds[y]<<','<<domain.upper_bounds[y]<<",outside_audited_current_integer_Y_selector_domain\n";
                    continue;
                }
                throw std::runtime_error("round107_missing_conflict_column:"+name);
            }
            row.columns.push_back(col->second);row.coefficients.push_back(c);
            remap_log<<semantic_id<<','<<evidence.rows[semantic_id].origin<<','<<request.round107_request_id
                <<','<<name<<','<<std::setprecision(17)<<c<<','<<col->second<<",0,,,present_current_column\n";
            key<<'/'<<col->second<<':'<<c;
        }
        const auto old=row_keys.find(key.str());if(old!=row_keys.end())return old->second;
        (void)allow_missing_states;remap_log.flush();if(!remap_log)throw std::runtime_error("round107_remap_persist");
        row.start_activity=start.empty()?0:activity(row,start);
        if(!start.empty()&&row.start_activity>row.rhs+1e-7*std::max({1.0,std::abs(row.start_activity),std::abs(row.rhs)}))
            throw std::runtime_error("round107_conflict_excludes_legal_start");
        const std::size_t id=pool.size();row_keys.emplace(key.str(),id);pool.push_back(row);
        std::ofstream f(outer.dir/("row_"+std::to_string(id)+".csv"));f<<std::setprecision(17)
            <<"family,vehicle,rhs,start_activity,variable,coefficient\n";
        for(std::size_t j=0;j<row.columns.size();++j)f<<family<<','<<vehicle<<','<<row.rhs<<','
            <<row.start_activity<<','<<domain.names[row.columns[j]]<<','<<row.coefficients[j]<<'\n';
        f.flush();if(!f)throw std::runtime_error("round107_row_persist_failed");return id;
    }
    void cancel(GRBmodel* model,const std::string& reason,bool pending=false) {
        if(!outer_cancelled){outer_cancelled=true;outer_termination_seconds=elapsed();}
        stop=reason;unresolved=unresolved||pending;outer.api.terminate(model);
    }
    void publish(long long e,double entered,double model_obj,double true_obj,double bound,
       long long fleet,long long stock,bool repeat,bool is_start,bool is_start_fleet,const std::string& outcome,
       const std::vector<int>& inventory,const std::vector<Round105Pattern>& cars,
       const std::vector<std::size_t>& cuts,long long ub_events) {
        events<<std::setprecision(17)<<std::boolalpha<<"{\"request\":"<<request.round107_request_id<<",\"epoch\":"<<request.round107_epoch<<",\"gamma_L\":"<<request.gamma_L<<",\"gamma_U\":"<<request.gamma_U<<",\"effective_cutoff\":"<<effective_cutoff<<",\"event\":"<<e<<",\"entered_seconds\":"<<entered
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
        events<<"]}\n";events.flush();if(!events)throw std::runtime_error("round107_event_persist_failed");
    }
    void candidate(GRBmodel* master,void* cbdata) {
        const double entered=elapsed();const long long e=++event_count;const auto audit_start=Clock::now();
        std::vector<double> x(domain.names.size());double model_obj=0,bound=-GRB_INFINITY;
        outer.check(outer.api.cbget(cbdata,GRB_CB_MIPSOL,GRB_CB_MIPSOL_SOL,x.data()));
        outer.check(outer.api.cbget(cbdata,GRB_CB_MIPSOL,GRB_CB_MIPSOL_OBJ,&model_obj));
        outer.check(outer.api.cbget(cbdata,GRB_CB_MIPSOL,GRB_CB_MIPSOL_OBJBND,&bound));
        snapshot(outer.dir/("candidate_"+std::to_string(e)+".sol"),x,model_obj);
        candidate_audit<<"{\"event\":"<<e<<",\"stage\":\"raw_saved_before_audit\",\"request\":"<<request.round107_request_id<<"}\n";
        candidate_audit.flush();if(!candidate_audit)throw std::runtime_error("round107_raw_audit_ahead_persist");
        // MIPSOL bound is retained only after this candidate is resolved.
        const auto residual=audit(x);
        auto integer=[&](const std::string& name){return static_cast<int>(std::llround(x.at(index.at(name))));};
        std::vector<int> inventory=in.initial;std::vector<Round105Pattern> cars(in.M);
        for(int k=0;k<in.M;++k){cars[k].vehicle=k;cars[k].operation.assign(in.V+1,0);}
        for(int i=1;i<=in.V;++i) {
            inventory[i]=integer("Y_"+std::to_string(i));int served=0;
            if(integer("state_"+std::to_string(i)+"_"+std::to_string(inventory[i]))!=1)
                throw std::runtime_error("round107_state_mapping");
            for(int k=0;k<in.M;++k) {
                const std::string suffix=std::to_string(k)+"_"+std::to_string(i);
                const int z=integer("z_"+suffix),p=integer("p_"+suffix),d=integer("d_"+suffix),m=integer("mode_"+suffix);
                if((z!=0&&z!=1)||p<0||d<0||(p&&d)||(!z&&(p||d))||(z&&!p&&!d)||
                   (p&&m!=1)||(d&&m!=0))throw std::runtime_error("round107_service_mapping");
                if(z){++served;if(p!=std::max(0,in.initial[i]-inventory[i])||d!=std::max(0,inventory[i]-in.initial[i]))
                    throw std::runtime_error("round107_inventory_operation_mapping");cars[k].operation[i]=p-d;}
            }
            if(served!=(inventory[i]!=in.initial[i]?1:0))throw std::runtime_error("round107_unique_service");
        }
        const auto F=computeObjectiveParts(in,inventory,opt.lambda);
        long double dot=objective_constant;for(std::size_t j=0;j<x.size();++j)dot+=objective_coefficients[j]*x[j];
        if(!std::isfinite(model_obj)||!std::isfinite(F.objective)||!std::isfinite(static_cast<double>(dot)))
            throw std::runtime_error("round107_snapshot_nonfinite_objective");
        candidate_audit<<std::boolalpha<<std::setprecision(17)<<"{\"event\":"<<e<<",\"stage\":\"base_and_objective_audit\",\"base_rows_valid\":true,\"max_row_violation\":"
            <<residual.maximum_violation<<",\"bounds_integrality_valid\":true,\"model_objective\":"<<model_obj<<",\"objective_dot\":"<<static_cast<double>(dot)
            <<",\"Ftrue\":"<<F.objective<<",\"epigraph_valid\":"<<(model_obj+1e-7>=F.objective)<<"}\n";
        candidate_audit.flush();if(!candidate_audit)throw std::runtime_error("round107_base_audit_persist");
        if(!std::isfinite(model_obj)||!std::isfinite(F.objective)||std::abs(static_cast<double>(dot)-model_obj)>1e-7*std::max(1.0,std::abs(model_obj)))
            throw std::runtime_error("round107_snapshot_objective_contract");
        if(model_obj<F.objective-1e-7)throw std::runtime_error("round107_model_objective_below_true_F");
        std::string fleet,stock;std::vector<std::string> keys;
        for(int i=1;i<=in.V;++i)stock+=std::to_string(inventory[i])+',';
        for(const auto& p:cars){auto key=round105PatternKey(in,p);keys.push_back(key);fleet+=key+';';
            if(!modes.count(key))modes.emplace(key,modes.size()+1);}
        const bool repeat=fleets.count(fleet)!=0;if(repeat)++repeat_count;
        else{fleets.emplace(fleet,fleets.size()+1);if(first_new_candidate_seconds<0&&fleet!=startup_fleet)first_new_candidate_seconds=entered;}
        if(!inventories.count(stock))inventories.emplace(stock,inventories.size()+1);
        for(int k=0;k<in.M;++k)for(int i=1;i<=in.V;++i)patterns<<e<<','<<k<<','<<i<<','<<cars[k].operation[i]
            <<','<<inventory[i]<<','<<modes.at(keys[k])<<",MIPSOL_SOL\n";
        patterns.flush();if(!patterns)throw std::runtime_error("round107_pattern_persist_failed");
        for(auto& s:submitted)if(!s.observed&&equal(x,s.values))s.observed=true;
        audit_mapping_seconds+=std::chrono::duration<double>(Clock::now()-audit_start).count();
        std::vector<std::size_t> cuts;
        if(outer_cancelled) {
            ++unknown_candidates;cancel(master,"post_cancel_unresolved_delivered_candidate",true);
            publish(e,entered,model_obj,F.objective,bound,fleets.at(fleet),inventories.at(stock),repeat,equal(x,start),fleet==startup_fleet,
                "UNKNOWN_POST_CANCEL_SAFE_INTERRUPT",inventory,cars,cuts,0);return;
        }
        auto collect=[&](){cuts.clear();for(std::size_t j=0;j<pool.size();++j)if(violated(pool[j],x))cuts.push_back(j);};
        collect();
        // Check every car's own-run cache before the uniform arithmetic scan.
        for(int k=0;k<in.M;++k) {
            const auto hit=cache.find(keys[k]);if(hit==cache.end())continue;++cache_hits;
            const auto origin=evidence.cache_origin.at(keys[k]);if(origin&&origin!=request.round107_request_id)++cross_request_hits;
            cache_log<<e<<','<<k<<','<<origin<<','<<request.round107_request_id<<','<<(origin==0)<<','
                <<(hit->second.status==Round105OracleStatus::Feasible?"FEAS":"INF")<<','<<std::quoted(keys[k])<<'\n';
            cache_log.flush();if(!cache_log)throw std::runtime_error("round107_cache_persist");
            if(hit->second.status==Round105OracleStatus::ProvedInfeasible)
                add(round105Conflict(in,cars[k],hit->second.core),hit->second.core_confirmed?"CORE":"FULL",k,false,evidence.cache_proof.at(keys[k]));
        }
        if(!expired()) {
            const auto tick=Clock::now();
            for(int k=0;k<in.M&&!expired();++k)for(const auto& c:round106Separate(in,cars[k],travel,[&](){return expired();})) {
                ++structural_proofs;const auto proof=outer.dir/("certificate_"+std::to_string(e)+"_"+std::to_string(structural_proofs)+".json");round106WriteCertificate(proof,c);
                add(c.row,c.family,k,c.family=="B_THRESHOLD",proof.generic_string());
                // A has no Q premise; only these compatible common h/T parameters transfer.
                if(c.family=="A_MST")for(int other=0;other<in.M;++other)if(other!=k) {
                    auto cross=c.row;cross.coefficients.clear();
                    for(int i:c.support){cross.coefficients["p_"+std::to_string(other)+"_"+std::to_string(i)]=c.handling_lower;
                        cross.coefficients["z_"+std::to_string(other)+"_"+std::to_string(i)]=c.travel_lower;}
                    add(cross,"A_MST_COMPATIBLE",other,false,proof.generic_string());
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
                answer=inner.oracle(cars[k],outer.dir/("event_"+std::to_string(e)+"_k"+std::to_string(k)),false);
                if(answer.status==Round105OracleStatus::Feasible||answer.status==Round105OracleStatus::ProvedInfeasible) {
                    cache.emplace(keys[k],answer);evidence.cache_origin.emplace(keys[k],request.round107_request_id);
                    evidence.cache_proof.emplace(keys[k],(outer.dir/("event_"+std::to_string(e)+"_k"+std::to_string(k))/"full.lp").generic_string());
                }
            }
            if(answer.status==Round105OracleStatus::Feasible){routes.push_back(answer.route);continue;}
            if(answer.status==Round105OracleStatus::ProvedInfeasible) {
                add(round105Conflict(in,cars[k],answer.core),answer.core_confirmed?"CORE":"FULL",k,false,evidence.cache_proof.at(keys[k]));collect();
                if(cuts.empty())throw std::runtime_error("round107_proved_mode_without_raw_violated_lazy");break;
            }
            if(answer.status==Round105OracleStatus::Error)throw std::runtime_error("round107_inner_error:"+answer.reason);
            break;
        }
        if(!cuts.empty()) {
            // Re-submit known violated rows; success on an earlier event is no rejection now.
            for(std::size_t id:cuts) {
                auto& row=pool[id];const double a=activity(row,x);
                if(!violated(row,x))throw std::runtime_error("round107_attempted_nonviolated_lazy");
                const int rc=outer.api.cblazy(cbdata,static_cast<int>(row.columns.size()),row.columns.data(),row.coefficients.data(),GRB_LESS_EQUAL,row.rhs);
                lazy<<std::setprecision(17)<<e<<','<<id<<','<<row.family<<','<<row.vehicle<<','<<a<<','<<row.rhs
                    <<','<<row.start_activity<<','<<a-row.rhs<<','<<(row.submissions>0)<<','<<rc<<','<<elapsed()<<'\n';
                lazy.flush();outer.check(rc);++row.submissions;++lazy_calls;
            }
            if(!lazy)throw std::runtime_error("round107_lazy_ledger_persist_failed");++rejected;
            qualifiedBound(bound,false);
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
            throw std::runtime_error("round107_combined_physical_witness");
        verified_fleets.insert(fleet);qualifiedBound(bound,false);
        ++feasible_candidates;bool improvement=verify.objective<result.upper_bound-1e-7;
        if(improvement) {
            result.routes=routes;result.verification=verify;result.final_inventory=inventory;
            result.objective=result.upper_bound=verify.objective;result.G=verify.G;result.P=verify.P;
            ++new_ub;if(first_new_ub_seconds<0)first_new_ub_seconds=elapsed();
            r105Witness(outer.dir/("physical_ub_"+std::to_string(new_ub)+".json"),routes,verify.objective);
        }
        if(improvement||!submitted_fleets.count(fleet)) {
            auto map_opt=opt;map_opt.round106_events="off";map_opt.round107_frontier_struct=false;
            const auto mapped=mapVerifiedRoutesToCanonicalModel(in,map_opt,normalizeRound61Routes(in,opt.lambda,routes),"R107_own_verified_routes",request.gamma_L,request.gamma_U,effective_cutoff,domain);
            if(!mapped.complete) {
                if(!r107OutsideMapping(mapped))throw std::runtime_error("round107_feedback_embedding_failed:"+mapped.failure_reason);
                feedback_log<<"{\"event\":"<<e<<",\"global_physical_UB_retained\":true,\"submitted\":false,\"reason\":"
                    <<std::quoted(mapped.failure_reason)<<"}\n";feedback_log.flush();
                audit_mapping_seconds+=std::chrono::duration<double>(Clock::now()-mapping_tick).count();
                publish(e,entered,model_obj,F.objective,bound,fleets.at(fleet),inventories.at(stock),repeat,equal(x,start),fleet==startup_fleet,"FEASIBLE_PHYSICAL_FEEDBACK_SKIPPED",inventory,cars,cuts,improvement?1:0);
                if(expired())cancel(master,"global_deadline_after_verified_candidate");return;
            }
            r107AuditEmbedding(mapped,domain,linear,objective_coefficients,objective_constant);
            for(const auto& row:pool)if(violated(row,mapped.values))throw std::runtime_error("round107_physical_witness_violates_proved_row");
            domain_witness_embeds=true;
            if(expired()) { cancel(master,"global_deadline_after_verified_embedding");
                publish(e,entered,model_obj,F.objective,bound,fleets.at(fleet),inventories.at(stock),repeat,equal(x,start),fleet==startup_fleet,
                    "FEASIBLE_PHYSICAL_NO_SUBMISSION_AFTER_DEADLINE",inventory,cars,cuts,improvement?1:0);return; }
            double returned=GRB_INFINITY;const double attempt=elapsed();
            const int rc=outer.api.cbsolution(cbdata,mapped.values.data(),&returned);
            std::ofstream f(outer.dir/("submission_"+std::to_string(submitted.size()+1)+".json"));f<<std::setprecision(17)
              <<"{\"event\":"<<e<<",\"attempt_seconds\":"<<attempt<<",\"physical_F\":"<<verify.objective
              <<",\"physical_UB_established\":true,\"api_return\":"<<rc<<",\"returned_objective\":";
            if(std::abs(returned)<GRB_INFINITY)f<<returned;else f<<"null";
            f<<",\"deferred_at_MIPSOL\":true}\n";f.flush();if(!f)throw std::runtime_error("round107_submission_persist_failed");
            outer.check(rc);submitted.push_back({e,verify.objective,mapped.values,false,false});submitted_fleets.insert(fleet);
            snapshot(outer.dir/("submission_"+std::to_string(submitted.size())+".sol"),mapped.values,verify.objective);
        }
        audit_mapping_seconds+=std::chrono::duration<double>(Clock::now()-mapping_tick).count();
        publish(e,entered,model_obj,F.objective,bound,fleets.at(fleet),inventories.at(stock),repeat,equal(x,start),fleet==startup_fleet,"FEASIBLE_PHYSICAL",inventory,cars,cuts,improvement?1:0);
        if(expired())cancel(master,"global_deadline_after_verified_candidate");
    }
    void qualifiedBound(double b,bool observe,double nodes=0) {
        if(error||unresolved)return;
        if(!std::isfinite(b)||std::abs(b)>=GRB_INFINITY)return;
        const bool improved=b>best_callback_bound+1e-12;
        best_callback_bound=std::max(best_callback_bound,b);
        if(observe&&improved) {
            FixedIntervalNativeBoundEvent ev;ev.native_bound=b;ev.native_bound_available=true;
            ev.bound_improved=true;ev.solver_runtime_seconds=elapsed()-optimize_launch;
            ev.processed_nodes=nodes;
            ev.target_reached=request.native_bound_target_enabled&&b+request.native_bound_target_tolerance>=request.native_bound_target;
            bound_events.push_back(ev);
        }
    }
    static int __stdcall callback(GRBmodel* master,void* cbdata,int where,void* userdata) {
        auto& s=*static_cast<R107State*>(userdata);const auto tick=Clock::now();
        try {
            if(s.error) {s.outer.api.terminate(master);}
            else if(where==GRB_CB_MIPSOL)s.candidate(master,cbdata);
            else if(s.outer_cancelled)s.outer.api.terminate(master);
            else {
                if(where==GRB_CB_MIP) {
                    double b=-GRB_INFINITY,nodes=0;s.outer.check(s.outer.api.cbget(cbdata,where,GRB_CB_MIP_OBJBND,&b));
                    s.outer.check(s.outer.api.cbget(cbdata,where,GRB_CB_MIP_NODCNT,&nodes));
                    s.qualifiedBound(b,true,nodes);
                    if(s.request.native_bound_target_enabled&&std::isfinite(b)&&std::abs(b)<GRB_INFINITY&&
                       b+s.request.native_bound_target_tolerance>=s.request.native_bound_target) {
                        s.target_observed=true;s.cancel(master,"qualified_mathematical_bound_target");
                    }
                }
                if(s.expired())s.cancel(master,"global_deadline_in_master");
            }
        }catch(const std::exception& ex){s.error=true;s.error_reason=ex.what();s.cancel(master,"ERROR:"+s.error_reason,true);}
        catch(...){s.error=true;s.error_reason="nonstandard_callback_exception";s.cancel(master,"ERROR:"+s.error_reason,true);}
        s.callback_seconds+=std::chrono::duration<double>(Clock::now()-tick).count();return 0;
    }
};
// The original backend owns LP model objects. Event MIPs always read canonical
// bytes afresh, so their native lazy pool cannot contaminate a later LP.
class R107FrontierBackend final : public FixedIntervalMipBackend {
    const Instance& in;
    SolveOptions opt;
    std::unique_ptr<FixedIntervalMipBackend> lp;
    R107PhysicalSession evidence;
    FixedIntervalMipBackendStats extra;
    std::filesystem::path root;
    std::ofstream requests;
    long long sequence=0;
    void auditAssignmentDomain(const SolverNeutralModelDomain& d,const SolverNeutralLinearModel& l,const std::map<std::string,int>& index)const {
        std::map<std::vector<std::pair<int,double>>,std::set<double>> equalities;
        for(std::size_t r=0;r<l.senses.size();++r)if(l.senses[r]==GRB_EQUAL) {
            std::vector<std::pair<int,double>> a;for(int t=l.row_starts[r];t<l.row_starts[r+1];++t)
                if(l.coefficients[t])a.emplace_back(l.column_indices[t],l.coefficients[t]);
            std::sort(a.begin(),a.end());equalities[a].insert(l.rhs[r]);
        }
        for(int i=1;i<=in.V;++i) {
            const int y=index.at("Y_"+std::to_string(i));const double lo=d.lower_bounds[y],hi=d.upper_bounds[y];
            if(d.variable_types[y]!='I'||!std::isfinite(lo)||!std::isfinite(hi)||lo<0||hi>in.capacity[i]||
                lo!=std::round(lo)||hi!=std::round(hi)||lo>hi)throw std::runtime_error("round107_integer_Y_domain_contract");
            std::vector<std::pair<int,double>> sum,link={{y,1}};
            for(int v=static_cast<int>(lo);v<=static_cast<int>(hi);++v) {
                const int s=index.at("state_"+std::to_string(i)+"_"+std::to_string(v));
                if(d.variable_types[s]!='B'||d.lower_bounds[s]<0||d.upper_bounds[s]>1)
                    throw std::runtime_error("round107_selector_type_contract");
                sum.emplace_back(s,1);if(v)link.emplace_back(s,-static_cast<double>(v));
            }
            std::sort(sum.begin(),sum.end());std::sort(link.begin(),link.end());
            if(!equalities[sum].count(1)||!equalities[link].count(0))throw std::runtime_error("round107_selector_reconstruction_row_contract");
            for(int k=0;k<in.M;++k)for(const auto& name: {"z_","mode_","p_","d_"}) {
                const auto j=index.at(std::string(name)+std::to_string(k)+"_"+std::to_string(i));
                if(d.variable_types[j]!=(name[0]=='p'||name[0]=='d'?'I':'B'))throw std::runtime_error("round107_retained_service_type_contract");
            }
        }
        for(const auto& [name,j]:index)if(name.rfind("state_",0)==0&&name.size()>6&&std::isdigit(static_cast<unsigned char>(name[6]))) {
            int i=0,v=0;char tail=0;if(std::sscanf(name.c_str(),"state_%d_%d%c",&i,&v,&tail)!=2||i<1||i>in.V)
                throw std::runtime_error("round107_selector_name_contract");
            const auto y=index.at("Y_"+std::to_string(i));if(v<d.lower_bounds[y]||v>d.upper_bounds[y])throw std::runtime_error("round107_selector_outside_Y_domain");
        }
    }
public:
    R107FrontierBackend(const Instance& i,const SolveOptions& o):in(i),opt(o),
        lp(std::make_unique<GurobiFixedIntervalBackend>(i,o)),
        root(std::filesystem::path(o.external_gini_artifact_dir)/"round107") {
        std::filesystem::create_directories(root);
        requests.open(root/"requests.jsonl");evidence.semantic.open(root/"semantic_rows.jsonl");
        if(!requests||!evidence.semantic)throw std::runtime_error("round107_session_stream_open");
    }
    FixedIntervalMipCapabilities capabilities()const override {return lp->capabilities();}
    void discardLeaf(const std::string& id)override {lp->discardLeaf(id);}
    void release()override {lp->release();}
    FixedIntervalMipBackendStats stats()const override {
        auto s=lp->stats();
        s.environment_count+=extra.environment_count;s.environment_free_count+=extra.environment_free_count;
        s.model_count+=extra.model_count;s.model_free_count+=extra.model_free_count;
        s.model_read_count+=extra.model_read_count;s.optimize_count+=extra.optimize_count;
        s.partial_bound_target_mip_optimize_count+=extra.partial_bound_target_mip_optimize_count;
        s.terminal_mip_optimize_count+=extra.terminal_mip_optimize_count;
        s.native_bound_target_reached_count+=extra.native_bound_target_reached_count;
        s.native_bound_event_count+=extra.native_bound_event_count;s.fresh_restart_count+=extra.fresh_restart_count;
        s.cumulative_model_read_seconds+=extra.cumulative_model_read_seconds;
        s.cumulative_model_build_seconds+=extra.cumulative_model_build_seconds;
        s.cumulative_solver_runtime_seconds+=extra.cumulative_solver_runtime_seconds;
        s.cumulative_partial_bound_target_mip_work+=extra.cumulative_partial_bound_target_mip_work;
        s.cumulative_terminal_mip_work+=extra.cumulative_terminal_mip_work;s.cumulative_work+=extra.cumulative_work;
        s.cumulative_nodes+=extra.cumulative_nodes;s.cumulative_simplex_iterations+=extra.cumulative_simplex_iterations;
        s.cumulative_barrier_iterations+=extra.cumulative_barrier_iterations;
        return s;
    }
    void publishRequest(const FixedIntervalMipRequest& q,const FixedIntervalMipOutcome& out,
                        bool cutoff_row,double cutoff,double epsilon,const std::string& start_reason,
                        const std::filesystem::path& dir) {
        requests<<std::setprecision(17)<<std::boolalpha<<"{\"request\":"<<q.round107_request_id
          <<",\"epoch\":"<<q.round107_epoch<<",\"leaf\":"<<std::quoted(q.leaf_id)
          <<",\"kind\":"<<std::quoted(out.lp_relaxation?"LP":(out.partial_bound_target_mip?"PARTIAL_TARGET":"TERMINAL"))
          <<",\"gamma_L\":"<<q.gamma_L<<",\"gamma_U\":"<<q.gamma_U<<",\"verified_cutoff\":"<<q.verified_cutoff
          <<",\"cutoff_row_present\":"<<cutoff_row<<",\"effective_cutoff\":"<<cutoff<<",\"epsilon\":"<<epsilon
          <<",\"canonical_path\":"<<std::quoted(q.canonical_model_path.generic_string())
          <<",\"canonical_sha256\":"<<std::quoted(q.canonical_model_fingerprint)
          <<",\"canonical_scope\":"<<std::quoted(q.canonical_model_scope)<<",\"row_signature\":"<<std::quoted(q.canonical_row_signature)
          <<",\"domain_start\":"<<out.warm_start_mapping_complete<<",\"start_reason\":"<<std::quoted(start_reason)
          <<",\"target_enabled\":"<<q.native_bound_target_enabled<<",\"target\":"<<q.native_bound_target
          <<",\"target_reached\":"<<out.native_bound_target_reached<<",\"native_status\":"<<out.native_status_code
          <<",\"native_Optimize_started\":"<<out.attempted<<",\"native_status_text\":"<<std::quoted(out.native_status)
          <<",\"qualified_local_bound_available\":"<<out.native_bound_available<<",\"qualified_local_bound\":"<<out.native_bound
          <<",\"optimal_close_by_dominance\":"<<(!out.lp_relaxation&&out.optimal)<<",\"LP_optimal\":"<<(out.lp_relaxation&&out.optimal)<<",\"local_INF\":"<<out.infeasible
          <<",\"own_global_UB\":"<<(evidence.initialized?evidence.own.upper_bound:q.verified_cutoff)
          <<",\"stop_whole_run\":"<<out.interrupted<<",\"unresolved\":"<<out.round107_unresolved_stop
          <<",\"reason\":"<<std::quoted(out.round107_local_reason)<<",\"failure\":"<<std::quoted(out.failure_reason)
          <<",\"fresh_canonical_MIP\":"<<(!out.lp_relaxation)<<",\"native_continuation_claimed\":false,\"evidence_dir\":"
          <<std::quoted(dir.generic_string())<<",\"published_process_seconds\":"<<processElapsedSeconds(opt)<<"}\n";
        requests.flush();if(!requests)throw std::runtime_error("round107_request_persist");
    }
    FixedIntervalMipOutcome solve(const FixedIntervalMipRequest& original)override {
        const double request_launch=processElapsedSeconds(opt);
        auto q=original;if(!q.round107_request_id)q.round107_request_id=++sequence;
        if(q.solve_kind==FixedIntervalSolveKind::PaperLpRelaxation) {
            auto out=lp->solve(q);out.round107_scoped=true;out.round107_local_reason="original_canonical_all_continuous_LP";
            bool has=false;double rhs=q.verified_cutoff;
            if(q.verified_cutoff>0&&opt.lambda>1e-12) {
                std::ifstream file(q.canonical_model_path);
                const auto metadata=round107ReadLpCutoff(file,q.verified_cutoff);
                has=metadata.present;rhs=metadata.rhs;
            }
            publishRequest(q,out,has,rhs,has?q.verified_cutoff-rhs:0,"LP_no_event_oracle_original_factory_domain",{});return out;
        }
        FixedIntervalMipOutcome out;out.round107_scoped=true;out.available=capabilities().available;
        out.terminal_mip=q.solve_kind==FixedIntervalSolveKind::PaperTerminalMip;
        out.partial_bound_target_mip=q.solve_kind==FixedIntervalSolveKind::PaperPartialBoundTargetMip;
        out.native_bound_target=q.native_bound_target;out.failure_reason="none";
        const auto dir=root/("request_"+std::to_string(q.round107_request_id));
        bool cutoff_present=false;double cutoff=q.verified_cutoff,epsilon=0;
        std::string start_reason="no_domain_start";
        long long journal_call=0;bool journal_finalized=false;
        NativeEvidenceScope journal_scope=q.native_evidence_scope;
        auto lifecycle=[&](const char* event,double seconds) {
            const std::string e=event;
            if(e=="environment_created")++extra.environment_count;
            else if(e=="environment_freed")++extra.environment_free_count;
            else if(e=="model_created")++extra.model_count;
            else if(e=="model_freed")++extra.model_free_count;
            else if(e=="model_read")++extra.model_read_count;
            else if(e=="master_optimize_intent") {if(q.native_evidence)journal_call=q.native_evidence->beginCall(journal_scope);}
            else if(e=="master_optimize_start") {
                out.attempted=true;++extra.optimize_count;++extra.fresh_restart_count;
                if(out.partial_bound_target_mip)++extra.partial_bound_target_mip_optimize_count;
                if(out.terminal_mip)++extra.terminal_mip_optimize_count;
            } else if(e=="master_optimize_return") {extra.cumulative_solver_runtime_seconds+=seconds;out.solver_runtime_seconds=seconds;}
            else if(e=="master_native_rc")out.optimize_return_code=static_cast<int>(seconds);
        };
        try {
            if(!out.available||!hasMetricTravelLowerBounds(in)||
               (!out.terminal_mip&&!out.partial_bound_target_mip))throw std::runtime_error("round107_request_backend_contract");
            if(fileSha256(q.canonical_model_path)!=q.canonical_model_fingerprint)throw std::runtime_error("round107_canonical_SHA_mismatch");
            for(double w:in.weights)if(!std::isfinite(w)||w<0)throw std::runtime_error("round107_weight_contract");
            if(!std::isfinite(opt.lambda)||opt.lambda<0)throw std::runtime_error("round107_lambda_contract");
            if(processWorkRemainingSeconds(opt)<=0) {
                out.interrupted=true;out.failure_reason="none";out.native_status="NOT_STARTED_DEADLINE";
                out.round107_open_stop=true;
                out.round107_local_reason="global_deadline_before_Optimize";publishRequest(q,out,false,cutoff,0,start_reason,dir);return out;
            }
            if(!evidence.initialized) {
                std::vector<RoutePlan> routes(in.M);std::set<int> seen;
                for(int k=0;k<in.M;++k)routes[k]={k,{0,0},{}};
                for(const auto& route:q.verified_start_routes) {
                    if(route.vehicle<0||route.vehicle>=in.M||!seen.insert(route.vehicle).second)
                        throw std::runtime_error("round107_global_witness_vehicle");
                    routes[route.vehicle]=route;
                }
                const auto v=verifyCompletePhysicalStartingWitness(in,routes,opt.lambda);
                if(!v.feasible||std::abs(v.objective-q.verified_cutoff)>1e-7)throw std::runtime_error("round107_initial_global_witness");
                evidence.own.routes=routes;evidence.own.verification=v;evidence.own.upper_bound=evidence.own.objective=v.objective;
                evidence.own.G=v.G;evidence.own.P=v.P;evidence.own.final_inventory=v.final_inventory;
                evidence.initialized=true;r105Witness(root/"seed.json",routes,v.objective);
            }
            const auto setup=Clock::now();
            R105Session session(in,opt,dir,lifecycle);session.strict_numeric_status=true;
            auto& api=session.api;R105Model model;const auto read_started=Clock::now();session.read(model,q.canonical_model_path);
            out.model_read_seconds=std::chrono::duration<double>(Clock::now()-read_started).count();extra.cumulative_model_read_seconds+=out.model_read_seconds;
            auto domain=session.domain(model.value);const int n=static_cast<int>(domain.names.size());
            std::map<std::string,int> index;for(int j=0;j<n;++j)if(!index.emplace(domain.names[j],j).second)throw std::runtime_error("round107_duplicate_column");
            int rows=0;session.check(api.getintattr(model.value,"NumConstrs",&rows));SolverNeutralLinearModel linear;
            if(!readLinearModel(api,model.value,n,rows,linear))throw std::runtime_error("round107_base_matrix_read");
            auditAssignmentDomain(domain,linear,index);
            std::vector<double> objective(n);double constant=0;session.check(api.getdblattrarray(model.value,"Obj",0,n,objective.data()));
            session.check(api.getdblattr(model.value,"ObjCon",&constant));
            // Lambda-zero / zero-cutoff absence follows the original factory.
            if(q.verified_cutoff>0&&opt.lambda>1e-12) {
                for(int r=0;r<rows;++r)if(linear.senses[r]==GRB_LESS_EQUAL) {
                    std::vector<double> a(n);for(int t=linear.row_starts[r];t<linear.row_starts[r+1];++t)a[linear.column_indices[t]]=linear.coefficients[t];
                    if(a==objective){const double rhs=linear.rhs[r]+constant;if(!cutoff_present||rhs<cutoff)cutoff=rhs;cutoff_present=true;}
                }
                if(!cutoff_present)throw std::runtime_error("round107_missing_actual_objective_cutoff_row");
                epsilon=q.verified_cutoff-cutoff;if(epsilon< -1e-7)throw std::runtime_error("round107_cutoff_rhs_contract");
            }
            const auto old=domain;std::ofstream vars(dir/"variables.csv");vars<<"index,name,old_type,master_type,relaxed\n";
            for(int j=0;j<n;++j) {
                const bool route=domain.names[j].rfind("x_",0)==0,load=domain.names[j].rfind("load_",0)==0;
                if(route&&domain.variable_types[j]!='B')throw std::runtime_error("round107_route_type");
                if(load&&domain.variable_types[j]!='I')throw std::runtime_error("round107_load_type");
                if(route||load)domain.variable_types[j]='C';
                vars<<j<<','<<domain.names[j]<<','<<old.variable_types[j]<<','<<domain.variable_types[j]<<','<<(route||load)<<'\n';
            }
            vars.flush();if(!vars)throw std::runtime_error("round107_variables_persist");
            session.check(api.setcharattrarray(model.value,"VType",0,n,domain.variable_types.data()));session.check(api.updatemodel(model.value));
            const auto observed=session.domain(model.value);
            if(observed.names!=domain.names||observed.variable_types!=domain.variable_types||observed.lower_bounds!=old.lower_bounds||observed.upper_bounds!=old.upper_bounds)
                throw std::runtime_error("round107_domain_readback");
            out.model_fingerprint_matches_request=true;out.model_variable_count=n;out.model_linear_constraint_count=rows;
            out.model_nonzero_count=linear.coefficients.size();out.fresh_restart=true;out.integer_domain_restored=true;
            out.retained_state_classification="fresh_canonical_MIP_no_tree_or_basis_reuse";out.basis_reuse_status="not_requested";
            const auto mapped=mapVerifiedRoutesToCanonicalModel(in,opt,normalizeRound61Routes(in,opt.lambda,evidence.own.routes),"own_global_scope_checked",q.gamma_L,q.gamma_U,cutoff,domain);
            std::vector<double> start;
            if(mapped.complete) {
                r107AuditEmbedding(mapped,domain,linear,objective,constant);
                start=mapped.values;out.warm_start_mapping_complete=true;
                session.check(api.setdblattrarray(model.value,"Start",0,n,start.data()));
                out.warm_start_submitted=true;start_reason="fully_audited_domain_witness";
                session.check(api.write(model.value,(dir/"start.mst").string().c_str()));
            } else {if(!r107OutsideMapping(mapped))throw std::runtime_error("round107_start_embedding_failed:"+mapped.failure_reason);start_reason=mapped.failure_reason;}
            out.warm_start_candidate_available=true;out.warm_start_status=start_reason;
            session.check(api.setintparam(api.getenv(model.value),"LazyConstraints",1));int lazy=0;
            session.check(api.getintparam(api.getenv(model.value),"LazyConstraints",&lazy));if(lazy!=1)throw std::runtime_error("round107_LazyConstraints_readback");
            NativeEvidenceScope params;if(!evidenceParameterReadback(api,api.getenv(model.value),params))throw std::runtime_error("round107_parameters_readback");
            out.exact_zero_gap_roundtrip=true;
            const auto path=dir/"master.lp";session.check(api.write(model.value,path.string().c_str()));
            std::filesystem::copy_file(q.canonical_model_path,dir/"original.lp");
            R107State state(session,in,opt,evidence.own,domain,linear,index,start,evidence.own.upper_bound,q.gamma_U,evidence,q,cutoff,lifecycle);
            state.objective_coefficients=objective;state.objective_constant=constant;
            const double setup_seconds=std::chrono::duration<double>(Clock::now()-setup).count();
            // Controller translates event offsets from this backend request's
            // launch, including setup; native Optimize timing remains separate.
            state.optimize_launch=request_launch;
            journal_scope.native_preconditions=true;journal_scope.settings_json=params.settings_json;journal_scope.native_log_path=path.string()+".log";
            session.check(api.setcallbackfunc(model.value,R107State::callback,&state));
            const int status=session.optimize(model.value,"master",path);
            session.check(api.setcallbackfunc(model.value,nullptr,nullptr));
            if(!session.master_calls) {
                if(journal_call&&q.native_evidence){q.native_evidence->notStarted(journal_call,"global_deadline_after_ahead_persistence");journal_finalized=true;}
                out.interrupted=out.round107_open_stop=true;out.round107_local_reason="global_deadline_after_setup_without_Optimize";
                out.failure_reason="none";out.solver_finalization_reached=true;out.feasibility_consistency_gate=true;
                out.native_bound_available=false;out.native_bound=0;out.native_status_code=0;out.native_status="NOT_STARTED_DEADLINE";
                out.attempted=false;
                if(evidence.initialized){out.incumbent_available=out.incumbent_independently_verified=true;out.incumbent_routes=evidence.own.routes;out.incumbent_objective=evidence.own.upper_bound;}
                publishRequest(q,out,cutoff_present,cutoff,epsilon,start_reason,dir);return out;
            }
            out.optimize_return_code=0;out.solver_finalization_reached=true;out.native_status_code=status;out.native_status=gurobiStatusName(status);
            out.native_status_supported=status==GRB_OPTIMAL||status==GRB_INFEASIBLE||status==GRB_INF_OR_UNBD||status==GRB_TIME_LIMIT||status==GRB_INTERRUPTED;
            out.solver_runtime_seconds=session.master_seconds;
            const bool work_ok=api.getdblattr(model.value,"Work",&out.work)==0&&std::isfinite(out.work);
            const bool nodes_ok=api.getdblattr(model.value,"NodeCount",&out.nodes)==0&&std::isfinite(out.nodes);
            const bool iter_ok=api.getdblattr(model.value,"IterCount",&out.simplex_iterations)==0&&std::isfinite(out.simplex_iterations);
            int bar=0;const bool bar_ok=api.getintattr(model.value,"BarIterCount",&bar)==0;out.barrier_iterations=bar_ok?bar:0;
            extra.cumulative_work+=work_ok?out.work:0;extra.cumulative_nodes+=nodes_ok?out.nodes:0;
            extra.cumulative_simplex_iterations+=iter_ok?out.simplex_iterations:0;extra.cumulative_barrier_iterations+=out.barrier_iterations;
            extra.cumulative_partial_bound_target_mip_work+=out.partial_bound_target_mip&&work_ok?out.work:0;
            extra.cumulative_terminal_mip_work+=out.terminal_mip&&work_ok?out.work:0;
            std::ofstream metrics(dir/"native_metrics.json");metrics<<std::boolalpha<<std::setprecision(17)
                <<"{\"Work_available\":"<<work_ok<<",\"Work\":"<<out.work<<",\"NodeCount_available\":"<<nodes_ok<<",\"NodeCount\":"<<out.nodes
                <<",\"IterCount_available\":"<<iter_ok<<",\"IterCount\":"<<out.simplex_iterations<<",\"BarIterCount_available\":"<<bar_ok<<",\"BarIterCount\":"<<bar
                <<",\"canonical_read_seconds\":"<<out.model_read_seconds<<",\"request_setup_seconds\":"<<setup_seconds<<"}\n";
            metrics.flush();if(!metrics)throw std::runtime_error("round107_native_metrics_persist");
            double final_bound=0;const bool final_b=api.getdblattr(model.value,"ObjBoundC",&final_bound)==0&&std::isfinite(final_bound)&&std::abs(final_bound)<GRB_INFINITY;
            out.native_bound=state.best_callback_bound;out.native_bound_available=true;
            if(!state.error&&!state.unresolved&&final_b&&(status==GRB_OPTIMAL||status==GRB_TIME_LIMIT||status==GRB_INTERRUPTED))out.native_bound=std::max(out.native_bound,final_bound);
            int count=0;session.check(api.getintattr(model.value,"SolCount",&count));bool final_verified=false;
            if(count&&!state.error) {
                std::vector<double> x(n);session.check(api.getdblattrarray(model.value,"X",0,n,x.data()));state.audit(x);
                std::vector<RoutePlan> fleet;auto Y=in.initial;
                for(int i=1;i<=in.V;++i)Y[i]=static_cast<int>(std::llround(x[index.at("Y_"+std::to_string(i))]));
                const auto physical=computeObjectiveParts(in,Y,opt.lambda);double obj=0;session.check(api.getdblattr(model.value,"ObjVal",&obj));
                long double dot=constant;for(int j=0;j<n;++j)dot+=objective[j]*x[j];
                if(!std::isfinite(obj)||!std::isfinite(physical.objective)||std::abs(static_cast<double>(dot)-obj)>1e-7*std::max(1.0,std::abs(obj)))
                    throw std::runtime_error("round107_final_objective_contract");
                if(obj+1e-7<physical.objective)throw std::runtime_error("round107_final_model_objective_below_true_F");
                for(int k=0;k<in.M;++k){Round105Pattern p;p.vehicle=k;p.operation.assign(in.V+1,0);
                    for(int i=1;i<=in.V;++i)p.operation[i]=static_cast<int>(std::llround(x[index.at("p_"+std::to_string(k)+"_"+std::to_string(i))]-x[index.at("d_"+std::to_string(k)+"_"+std::to_string(i))]));
                    const auto found=evidence.cache.find(round105PatternKey(in,p));
                    if(found==evidence.cache.end()||found->second.status!=Round105OracleStatus::Feasible)break;fleet.push_back(found->second.route);
                }
                if(fleet.size()==static_cast<std::size_t>(in.M)) {
                    const auto v=verifyCompletePhysicalStartingWitness(in,fleet,opt.lambda);
                    const bool physical_mode=v.feasible&&v.final_inventory==Y&&std::abs(v.objective-physical.objective)<=1e-7;
                    // A final cached complete fleet is a physical witness even
                    // when native attributes cannot close this request.
                    if(physical_mode&&v.objective<evidence.own.upper_bound-1e-7) {
                        evidence.own.routes=fleet;evidence.own.verification=v;evidence.own.final_inventory=Y;
                        evidence.own.objective=evidence.own.upper_bound=v.objective;evidence.own.G=v.G;evidence.own.P=v.P;
                        ++state.new_ub;if(state.first_new_ub_seconds<0)state.first_new_ub_seconds=state.elapsed();
                        r105Witness(dir/("physical_ub_"+std::to_string(state.new_ub)+".json"),fleet,v.objective);
                    }
                    final_verified=!state.unresolved&&physical_mode;
                    if(final_verified)r105Witness(dir/"final_accepted_physical.json",fleet,v.objective);
                }
                for(auto& submission:state.submitted)if(R107State::equal(x,submission.values))submission.final_accepted=true;
            }
            if(status==GRB_INF_OR_UNBD || (count&&!final_verified&&!state.error))state.unresolved=true;
            const bool qualified_final=!state.error&&!state.unresolved&&final_b&&(status==GRB_OPTIMAL||status==GRB_TIME_LIMIT||status==GRB_INTERRUPTED);
            if(!qualified_final)out.native_bound=state.best_callback_bound;
            Round107ScopeFacts facts;facts.error=state.error||!out.native_status_supported;facts.unresolved=state.unresolved;
            facts.native_optimal=status==GRB_OPTIMAL;facts.native_infeasible=status==GRB_INFEASIBLE;
            facts.final_mode_verified=final_verified;facts.domain_witness_embeds=state.domain_witness_embeds;facts.bound_available=out.native_bound_available;
            facts.bound=out.native_bound;facts.own_global_ub=evidence.own.upper_bound;facts.target=q.native_bound_target;
            facts.target_requested=q.native_bound_target_enabled;facts.target_observed=state.target_observed;facts.tolerance=q.native_bound_target_tolerance;
            const auto decision=decideRound107Scope(facts);out.round107_local_reason=decision.reason;
            if(state.unresolved)out.round107_local_reason += ":" + (status==GRB_INF_OR_UNBD?std::string("native_INF_OR_UNBD"):state.stop);
            out.feasibility_consistency_gate=decision.valid;out.optimal=decision.close_by_dominance;out.infeasible=decision.empty_improvement_domain;
            out.native_exact_optimal=facts.native_optimal&&decision.close_by_dominance;
            out.native_bound_target_reached=decision.target_reached;out.native_bound_target_termination_requested=decision.target_reached;
            out.interrupted=decision.stop_whole_run||(!out.optimal&&!out.infeasible&&!decision.target_reached);
            if(out.interrupted&&!state.unresolved&&state.stop!="native_return")out.round107_local_reason += ":"+state.stop;
            out.round107_unresolved_stop=state.unresolved;out.native_bound_events=state.bound_events;
            out.round107_open_stop=out.interrupted;
            if(!decision.valid){out.native_bound_available=false;out.native_bound_events.clear();out.solver_finalization_reached=false;out.failure_reason=state.error?state.error_reason:decision.reason;}
            // Targets never survive UNKNOWN. Final attributes are excluded on that branch.
            if(state.unresolved)for(auto& ev:out.native_bound_events)ev.target_reached=false;
            std::ofstream acceptance(dir/"submission_acceptance.csv");acceptance<<"event,physical_F,observed_MIPSOL_vector,final_native_accepted\n";
            for(const auto& a:state.submitted)acceptance<<std::setprecision(17)<<a.event<<','<<a.objective<<','<<a.observed<<','<<a.final_accepted<<'\n';
            acceptance.flush();if(!acceptance)throw std::runtime_error("round107_acceptance_persist");
            std::ofstream sum(dir/"summary.json");sum<<std::setprecision(17)<<std::boolalpha
              <<"{\"request\":"<<q.round107_request_id<<",\"events\":"<<state.event_count<<",\"distinct_Y\":"<<state.inventories.size()
              <<",\"distinct_fleets\":"<<state.fleets.size()<<",\"cache_hits\":"<<state.cache_hits<<",\"cross_request_hits\":"<<state.cross_request_hits
              <<",\"remapped_rows\":"<<state.remapped_rows<<",\"structural_proofs\":"<<state.structural_proofs<<",\"lazy_calls\":"<<state.lazy_calls
              <<",\"structural_certificate_emissions\":"<<state.structural_proofs<<",\"new_semantic_rows\":"<<state.new_semantic_rows
              <<",\"rejected_events\":"<<state.rejected<<",\"feasible_candidates\":"<<state.feasible_candidates<<",\"unknown_candidates\":"<<state.unknown_candidates
              <<",\"new_physical_UBs\":"<<state.new_ub<<",\"submission_attempts\":"<<state.submitted.size()<<",\"final_mode_verified\":"<<final_verified
              <<",\"final_native_bound_qualified\":"<<(qualified_final&&decision.valid)<<",\"domain_witness_embeds\":"<<state.domain_witness_embeds<<",\"master_calls\":"<<session.master_calls
              <<",\"oracle_calls\":"<<state.inner.oracle_calls<<",\"iis_calls\":0,\"master_inclusive_seconds\":"<<session.master_seconds
              <<",\"master_exclusive_seconds\":"<<session.master_seconds-state.callback_seconds<<",\"callback_seconds\":"<<state.callback_seconds
              <<",\"oracle_seconds\":"<<state.inner.oracle_seconds<<",\"separation_seconds\":"<<state.separation_seconds
              <<",\"audit_mapping_seconds\":"<<state.audit_mapping_seconds<<",\"callback_other_seconds\":"
              <<state.callback_seconds-state.inner.oracle_seconds-state.separation_seconds-state.audit_mapping_seconds
              <<",\"inner_cancelled\":"<<state.inner.cancellation_requested<<",\"outer_cancelled\":"<<state.outer_cancelled
              <<",\"native_target_observed\":"<<state.target_observed<<",\"native_cancel_reason\":"<<std::quoted(state.stop)
              <<",\"unresolved\":"<<state.unresolved<<",\"reason\":"<<std::quoted(out.round107_local_reason)<<"}\n";
            sum.flush();if(!sum)throw std::runtime_error("round107_summary_persist");
            if(q.native_evidence){q.native_evidence->witness(evidence.own.routes,"round107_own_physical_archive",journal_call);
                if(out.native_bound_available)q.native_evidence->nativeBound(journal_call,out.native_bound);q.native_evidence->returned(journal_call,0);journal_finalized=true;}
            extra.native_bound_target_reached_count+=out.native_bound_target_reached;extra.native_bound_event_count+=out.native_bound_events.size();
        } catch(const std::exception& e) {
            if(q.native_evidence){
                if(journal_call&&!journal_finalized){try{q.native_evidence->returned(journal_call,out.optimize_return_code);journal_finalized=true;}catch(...){}}
                q.native_evidence->failure(std::string("round107_request:")+e.what());}
            out.failure_reason=e.what();out.round107_local_reason="ERROR_request_contract";out.feasibility_consistency_gate=false;
            out.solver_finalization_reached=false;out.optimal=out.infeasible=out.native_bound_available=false;
            out.native_exact_optimal=false;out.round107_open_stop=true;
            out.native_bound_target_reached=out.native_bound_target_termination_requested=false;out.native_bound_events.clear();out.interrupted=true;
            std::filesystem::create_directories(dir);std::ofstream f(dir/"error.json");f<<"{\"reason\":"<<std::quoted(e.what())<<"}\n";
        }
        if(evidence.initialized){out.incumbent_available=out.incumbent_independently_verified=true;
            out.incumbent_objective=evidence.own.upper_bound;out.incumbent_routes=evidence.own.routes;r105Witness(root/"witness.json",evidence.own.routes,evidence.own.upper_bound);}
        publishRequest(q,out,cutoff_present,cutoff,epsilon,start_reason,dir);return out;
    }
};
