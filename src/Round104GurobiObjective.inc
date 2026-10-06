// Included in GurobiFixedIntervalBackend. All auxiliary models are disposable;
// the canonical source and the official MIP environment keep their tolerances.
    struct ObjectiveArtifact {
        std::filesystem::path path;
        std::string sha, signature, evidence;
    };
    std::map<std::string,ObjectiveArtifact> objective_artifacts_;

    void prepareObjectiveResources(FixedIntervalMipRequest& request) override {
        if (options_.round104_objective_resources == "off") return;
        if (!available_ || !configuration_valid_ ||
            request.solve_kind == FixedIntervalSolveKind::PaperLpRelaxation ||
            request.solve_kind == FixedIntervalSolveKind::LegacyMipQuantum ||
            request.interval_mip_policy != "round55-vd-p" ||
            request.canonical_model_fingerprint.empty() || request.leaf_id.empty() ||
            request.canonical_model_scope.empty() || request.canonical_row_signature.empty() ||
            request.native_log_path.empty() || !request.variable_bound_overrides.empty() ||
            !request.additional_linear_rows.empty() || !request.round60_fixed_inventory.empty() ||
            fileSha256(request.canonical_model_path) != request.canonical_model_fingerprint)
            throw std::runtime_error("round104_original_identity_or_scope");
        const auto started = Clock::now();
        const auto source_path = request.canonical_model_path;
        const auto source_sha = request.canonical_model_fingerprint;
        std::ostringstream key;
        key << std::setprecision(17) << source_sha << '|' << request.leaf_id << '|'
            << request.canonical_model_scope << '|' << request.canonical_row_signature << '|'
            << request.gamma_L << '|' << request.gamma_U << '|' << request.verified_cutoff
            << '|' << fileSha256(instance_.path) << '|' << options_.round104_objective_resources;
        const auto prefix = request.native_log_path.string()+".round104";
        if (request.native_log_path.has_parent_path())
            std::filesystem::create_directories(request.native_log_path.parent_path());
        auto persist = [](const std::string& path,const std::string& content) {
            if (std::filesystem::exists(path)) throw std::runtime_error("round104_evidence_exists:"+path);
            std::ofstream f(path,std::ios::binary);f << content << '\n';f.close();
            if (!f) throw std::runtime_error("round104_evidence_write:"+path);
        };
        auto adopt = [&](const ObjectiveArtifact& a) {
            if (fileSha256(a.path)!=a.sha) throw std::runtime_error("round104_cached_artifact_changed");
            request.canonical_model_path=a.path;request.canonical_model_fingerprint=a.sha;
            request.canonical_row_signature=a.signature;
            const auto old=leaves_.find(request.leaf_id);
            if(old!=leaves_.end()&&old->second.model_fingerprint!=a.sha)discardLeaf(request.leaf_id);
        };
        auto cached=objective_artifacts_.find(key.str());
        if(cached!=objective_artifacts_.end()) {
            adopt(cached->second);
            std::ostringstream s;s << "{\"cache_hit\":true,\"source_sha256\":" << std::quoted(source_sha)
                << ",\"canonical_sha256\":" << std::quoted(cached->second.sha)
                << ",\"paid_evidence\":" << std::quoted(cached->second.evidence) << '}';
            persist(prefix+".summary.json",s.str());return;
        }
        if(std::filesystem::exists(prefix+".calls.jsonl"))throw std::runtime_error("round104_calls_exists");
        std::ofstream calls(prefix+".calls.jsonl");
        if(!calls)throw std::runtime_error("round104_calls_open");
        auto trace=[&](const std::string& s){calls << s << '\n';calls.flush();if(!calls)throw std::runtime_error("round104_calls_write");};
        auto check=[](int rc){if(rc)throw std::runtime_error("round104_api_"+std::to_string(rc));};
        auto remaining=[&](){return request.global_deadline_remaining_seconds-
            std::chrono::duration<double>(Clock::now()-started).count();};
        auto own=[&](GRBmodel* m){return std::unique_ptr<GRBmodel,std::function<void(GRBmodel*)>>(m,[&](GRBmodel* p){if(p)api_.freemodel(p);});};
        GRBmodel* raw=nullptr;check(api_.readmodel(env_,source_path.string().c_str(),&raw));auto source=own(raw);
        if(!source)throw std::runtime_error("round104_source_null");
        int nv=0,nr=0,ng=0;check(api_.getintattr(source.get(),GRB_INT_ATTR_NUMVARS,&nv));
        check(api_.getintattr(source.get(),GRB_INT_ATTR_NUMCONSTRS,&nr));
        check(api_.getintattr(source.get(),GRB_INT_ATTR_NUMGENCONSTRS,&ng));
        if(nv<=0||ng)throw std::runtime_error("round104_linear_model_required");
        NativeOtB1LinearModel identity;identity.names.resize(nv);identity.types.resize(nv);
        identity.lower_bounds.resize(nv);identity.upper_bounds.resize(nv);
        for(int j=0;j<nv;++j){char* name=nullptr;check(api_.getstrattrelement(source.get(),GRB_STR_ATTR_VARNAME,j,&name));
            if(!name)throw std::runtime_error("round104_column_name");identity.names[j]=name;}
        check(api_.getcharattrarray(source.get(),GRB_CHAR_ATTR_VTYPE,0,nv,identity.types.data()));
        check(api_.getdblattrarray(source.get(),GRB_DBL_ATTR_LB,0,nv,identity.lower_bounds.data()));
        check(api_.getdblattrarray(source.get(),GRB_DBL_ATTR_UB,0,nv,identity.upper_bounds.data()));
        SolverNeutralLinearModel linear;if(!readLinearModel(api_,source.get(),nv,nr,linear))throw std::runtime_error("round104_matrix_read");
        identity.row_starts=linear.row_starts;identity.column_indices=linear.column_indices;
        identity.coefficients=linear.coefficients;identity.senses=linear.senses;identity.rhs=linear.rhs;
        const auto contract=prepareServiceContract(instance_,identity);
        if(!contract.valid)throw std::runtime_error("round104_model_audit:"+contract.reason);
        double mip_feas=0;check(api_.getdblparam(api_.getenv(source.get()),GRB_DBL_PAR_FEASIBILITYTOL,&mip_feas));
        std::ostringstream binding;binding << "{\"source_sha256\":" << std::quoted(source_sha)
            << ",\"source_path\":" << std::quoted(source_path.string()) << ",\"scope\":" << std::quoted(request.canonical_model_scope)
            << ",\"leaf\":" << std::quoted(request.leaf_id) << ",\"input_sha256\":" << std::quoted(fileSha256(instance_.path))
            << ",\"column_contract\":" << serviceContractJson(contract) << '}';
        persist(prefix+".contract.json",binding.str());
        auto root=own(api_.copymodel(source.get()));if(!root)throw std::runtime_error("round104_root_copy");
        std::vector<char> continuous(nv,GRB_CONTINUOUS);
        check(api_.setcharattrarray(root.get(),GRB_CHAR_ATTR_VTYPE,0,nv,continuous.data()));check(api_.updatemodel(root.get()));
        long long optimize_calls=0,dp_calls=0;int submitted=0,selected=0;std::vector<ServiceCut> rows;
        auto optimize=[&](GRBmodel* m,const std::string& kind,int vehicle,int column_count){
            if(remaining()<=0)return false;
            GRBenv* e=api_.getenv(m);if(!e)throw std::runtime_error("round104_aux_environment");
            check(api_.setintparam(e,GRB_INT_PAR_THREADS,1));check(api_.setintparam(e,GRB_INT_PAR_SEED,options_.gurobi_seed));
            check(api_.setintparam(e,GRB_INT_PAR_PRESOLVE,options_.gurobi_presolve));check(api_.setintparam(e,GRB_INT_PAR_METHOD,1));
            check(api_.setdblparam(e,GRB_DBL_PAR_FEASIBILITYTOL,1e-9));check(api_.setdblparam(e,GRB_DBL_PAR_OPTIMALITYTOL,1e-9));
            check(api_.setdblparam(e,GRB_DBL_PAR_WORKLIMIT,GRB_INFINITY));check(api_.setstrparam(e,GRB_STR_PAR_LOGFILE,""));
            check(api_.setintparam(e,GRB_INT_PAR_OUTPUTFLAG,0));
            const double global_remaining=remaining();if(global_remaining<=0)return false;
            check(api_.setdblparam(e,GRB_DBL_PAR_TIMELIMIT,global_remaining));
            const auto serial=++optimize_calls;std::ostringstream b;b << "{\"event\":\"Optimize_begin\",\"serial\":" << serial
                << ",\"kind\":" << std::quoted(kind) << ",\"vehicle\":" << vehicle << ",\"columns\":" << column_count << '}';trace(b.str());
            const int rc=api_.optimize(m);int status=0;double runtime=0;check(api_.getintattr(m,GRB_INT_ATTR_STATUS,&status));
            check(api_.getdblattr(m,GRB_DBL_ATTR_RUNTIME,&runtime));
            std::ostringstream r;r << std::setprecision(17) << "{\"event\":\"Optimize_return\",\"serial\":" << serial << ",\"return_code\":" << rc << ",\"status\":" << status << ",\"seconds\":" << runtime << '}';trace(r.str());
            check(rc);return status==GRB_OPTIMAL;
        };
        bool root_optimal=optimize(root.get(),"standard_root",-1,nv);
        std::vector<double> point(nv);double root_objective=0,initial_objective=0,compressed_objective=0;
        const bool standard_optimal=root_optimal;bool compressed_optimal=false;
        if(standard_optimal){check(api_.getdblattr(root.get(),GRB_DBL_ATTR_OBJVAL,&root_objective));initial_objective=root_objective;}
        int pool_iterations=0,positive_pi=0;std::string pool_stop="standard_LP_incomplete",qualification="UNKNOWN";
        std::vector<std::vector<ServicePlan>> paid_banks(contract.columns.size());std::set<std::string> pool_keys;
        int objective_sense=0;check(api_.getintattr(source.get(),GRB_INT_ATTR_MODELSENSE,&objective_sense));
        if(objective_sense!=GRB_MINIMIZE)throw std::runtime_error("round104_minimize_required");
        
        while(root_optimal&&remaining()>0){const auto before=rows.size();bool all_inside=true;std::size_t completed_vehicles=0;++pool_iterations;check(api_.getdblattrarray(root.get(),GRB_DBL_ATTR_X,0,nv,point.data()));check(api_.getdblattr(root.get(),GRB_DBL_ATTR_OBJVAL,&root_objective));
            if(pool_iterations==1)initial_objective=root_objective;
            std::ostringstream p;p << std::setprecision(17) << "{\"source_sha256\":" << std::quoted(source_sha) << ",\"objective\":" << root_objective << ",\"variables\":[";
            for(int j=0;j<nv;++j){if(j)p << ',';p << '[' << std::quoted(identity.names[j]) << ',' << point[j] << ']';}p << "]}";persist(prefix+(pool_iterations==1?".point.json":".iteration"+std::to_string(pool_iterations)+".point.json"),p.str());
            for(std::size_t k=0;k<contract.columns.size()&&remaining()>0;++k){
                const auto n=contract.resource.initial.size();ServicePoint v(n,{0,0,0});std::vector<std::array<int,3>> widths(n,{0,0,0});
                for(std::size_t i=1;i<n;++i){const int A=std::min(contract.resource.initial[i],contract.resource.capacities[k]);
                    const int B=std::min(contract.resource.station_capacity[i]-contract.resource.initial[i],contract.resource.capacities[k]);widths[i]={A,B,A>0||B>0?1:0};
                    for(int t=0;t<3;++t)v[i][t]=point.at(contract.columns[k][i][t]);}
                raw=nullptr;check(api_.newmodel(env_,&raw,"resource_hull_distance",0,nullptr,nullptr,nullptr,nullptr,nullptr));auto master=own(raw);
                if(!master)throw std::runtime_error("round104_master_null");
                check(api_.addvar(master.get(),0,nullptr,nullptr,1.,0.,GRB_INFINITY,GRB_CONTINUOUS,"distance"));check(api_.updatemodel(master.get()));
                std::vector<std::array<int,3>> lower(n,{-1,-1,-1}),upper=lower;int constraints=0;
                for(std::size_t i=1;i<n;++i)for(int t=0;t<3;++t)if(widths[i][t]){
                    int j=0;double a=1;lower[i][t]=constraints++;
                    check(api_.addconstr(master.get(),1,&j,&a,GRB_GREATER_EQUAL,v[i][t]/widths[i][t],nullptr));
                    a=-1;upper[i][t]=constraints++;check(api_.addconstr(master.get(),1,&j,&a,GRB_LESS_EQUAL,v[i][t]/widths[i][t],nullptr));}
                const int mass=constraints++;check(api_.addconstr(master.get(),0,nullptr,nullptr,GRB_EQUAL,1.,"mass"));check(api_.updatemodel(master.get()));
                std::size_t added=0;
                HullLpSolver solve=[&](const std::vector<ServicePlan>& library){
                    for(;added<library.size();++added){std::vector<int> index{mass};std::vector<double> values{1.};
                        for(std::size_t i=1;i<n;++i)for(int t=0;t<3;++t)if(widths[i][t]&&library[added][i][t]){
                            index.push_back(lower[i][t]);index.push_back(upper[i][t]);const double a=static_cast<double>(library[added][i][t])/widths[i][t];values.push_back(a);values.push_back(a);}
                        check(api_.addvar(master.get(),static_cast<int>(index.size()),index.data(),values.data(),0.,0.,GRB_INFINITY,GRB_CONTINUOUS,nullptr));}
                    check(api_.updatemodel(master.get()));HullMaster m;m.optimal=optimize(master.get(),"distance_master",static_cast<int>(k),static_cast<int>(added));
                    if(!m.optimal)return m;m.lambda.resize(added);m.direction.resize(n,{0,0,0});std::vector<double> dual(constraints);
                    check(api_.getdblattr(master.get(),GRB_DBL_ATTR_OBJVAL,&m.distance));check(api_.getdblattrarray(master.get(),GRB_DBL_ATTR_X,1,static_cast<int>(added),m.lambda.data()));
                    check(api_.getdblattrarray(master.get(),GRB_DBL_ATTR_PI,0,constraints,dual.data()));
                    for(std::size_t i=1;i<n;++i)for(int t=0;t<3;++t)if(widths[i][t])m.direction[i][t]=(dual[lower[i][t]]+dual[upper[i][t]])/widths[i][t];return m;
                };
                const auto member=classifyServiceHull(contract,static_cast<int>(k),v,solve,{},1e-8,trace,&paid_banks[k]);dp_calls+=member.dp_calls;
                ++completed_vehicles;
                if(member.status!="INSIDE")all_inside=false;
                persist(prefix+".iteration"+std::to_string(pool_iterations)+".vehicle"+std::to_string(k)+".json",hullMembershipJson(member));
                if(member.status=="OUTSIDE"){
                    ++selected;auto row=member.cut;double largest=0;for(double a:row.coefficients)largest=std::max(largest,std::fabs(a));
                    if(!largest)throw std::runtime_error("round104_empty_separation");
                    const int exponent=-std::ilogb(largest);bool representable=true;double activity=0;
                    for(std::size_t j=0;j<row.coefficients.size();++j){row.coefficients[j]=std::ldexp(row.coefficients[j],exponent);
                        const double a=row.coefficients[j];if(!std::isfinite(a)||std::fabs(a)<1e-13)representable=false;
                        activity=std::nextafter(activity+std::nextafter(a*point[row.indices[j]],-GRB_INFINITY),-GRB_INFINITY);}
                    row.rhs=std::ldexp(row.rhs,exponent);row.activity_lower=activity;row.violation_lower=std::nextafter(activity-row.rhs,-GRB_INFINITY);
                    if(representable&&std::isfinite(row.rhs)&&row.violation_lower>10*mip_feas){
                        std::ostringstream direction;direction<<k<<':';for(const auto&w:row.proofs.at(0).weights)for(auto a:w)direction<<a<<',';
                        if(pool_keys.insert(direction.str()).second)rows.push_back(std::move(row));}
                }
            }
            if(completed_vehicles!=contract.columns.size()){pool_stop="global_deadline_UNKNOWN";break;}
            if(all_inside){pool_stop="all_members_within_tolerance";break;}
            if(rows.size()==before){pool_stop="no_new_admissible_certified_direction_UNKNOWN";break;}
            for(std::size_t j=before;j<rows.size();++j){auto&r=rows[j];
                check(api_.addconstr(root.get(),static_cast<int>(r.indices.size()),r.indices.data(),r.coefficients.data(),GRB_LESS_EQUAL,r.rhs,nullptr));}
            check(api_.updatemodel(root.get()));
            root_optimal=optimize(root.get(),"finite_objective_pool",-1,nv);
            if(!root_optimal)pool_stop="objective_pool_incomplete_UNKNOWN";
        }
        if(remaining()<=0)pool_stop="global_deadline_UNKNOWN";
        const auto pool_rows=rows;std::vector<double> pi(pool_rows.size(),0);std::vector<ServiceCut> active;
        auto persistSolution=[&](GRBmodel*m,const std::string&tag){int nrows=0;double cv=0,bv=0,dv=0,obj=0;
            check(api_.getintattr(m,GRB_INT_ATTR_NUMCONSTRS,&nrows));
            check(api_.getdblattr(m,GRB_DBL_ATTR_CONSTR_VIO,&cv));check(api_.getdblattr(m,GRB_DBL_ATTR_BOUND_VIO,&bv));check(api_.getdblattr(m,GRB_DBL_ATTR_DUAL_VIO,&dv));
            check(api_.getdblattr(m,GRB_DBL_ATTR_OBJVAL,&obj));
            if(!std::isfinite(cv)||!std::isfinite(bv)||!std::isfinite(dv)||std::max({cv,bv,dv})>1e-7)throw std::runtime_error("round104_LP_residual_qualification");
            std::vector<double>x(nv),rc(nv),dual(nrows);check(api_.getdblattrarray(m,GRB_DBL_ATTR_X,0,nv,x.data()));
            check(api_.getdblattrarray(m,GRB_DBL_ATTR_RC,0,nv,rc.data()));check(api_.getdblattrarray(m,GRB_DBL_ATTR_PI,0,nrows,dual.data()));
            std::ostringstream s;s<<std::setprecision(17)<<"{\"objective\":"<<obj<<",\"ConstrVio\":"<<cv<<",\"BoundVio\":"<<bv<<",\"DualVio\":"<<dv<<",\"variables\":[";
            for(int j=0;j<nv;++j){if(j)s<<',';s<<'['<<std::quoted(identity.names[j])<<','<<x[j]<<','<<rc[j]<<']';}s<<"],\"Pi\":[";
            for(int r=0;r<nrows;++r){if(r)s<<',';s<<dual[r];}s<<"]}";persist(prefix+"."+tag+".solution.json",s.str());};
        auto dumpRows=[&](const std::vector<ServiceCut>& rs){std::ostringstream s;s<<std::setprecision(17)<<"{\"rows\":[";
            for(std::size_t r=0;r<rs.size();++r){if(r)s<<',';s<<"{\"rhs\":"<<rs[r].rhs<<",\"coefficients\":[";
                for(std::size_t j=0;j<rs[r].indices.size();++j){if(j)s<<',';s<<'['<<std::quoted(identity.names.at(rs[r].indices[j]))<<','<<rs[r].coefficients[j]<<']';}
                s<<"],\"proofs\":[";for(std::size_t j=0;j<rs[r].proofs.size();++j){if(j)s<<',';s<<serviceSupportJson(rs[r].proofs[j]);}s<<"]}";}
            s<<"]}";return s.str();};
        persist(prefix+".pool.rows.json",dumpRows(pool_rows));
        if(root_optimal){
            check(api_.getdblattr(root.get(),GRB_DBL_ATTR_OBJVAL,&root_objective));
            persistSolution(root.get(),"pool");
            if(!pi.empty())check(api_.getdblattrarray(root.get(),GRB_DBL_ATTR_PI,nr,static_cast<int>(pi.size()),pi.data()));
            for(std::size_t j=0;j<pi.size();++j){if(!std::isfinite(pi[j])||pi[j]>1e-8)throw std::runtime_error("round104_unqualified_Pi");
                if(pi[j]>0)++positive_pi;if(pi[j]<0)active.push_back(pool_rows[j]);}
            auto compressed=own(api_.copymodel(source.get()));if(!compressed)throw std::runtime_error("round104_compressed_copy");
            check(api_.setcharattrarray(compressed.get(),GRB_CHAR_ATTR_VTYPE,0,nv,continuous.data()));
            for(auto&r:active)check(api_.addconstr(compressed.get(),static_cast<int>(r.indices.size()),r.indices.data(),r.coefficients.data(),GRB_LESS_EQUAL,r.rhs,nullptr));
            check(api_.updatemodel(compressed.get()));
            if(optimize(compressed.get(),"compressed_objective_qualification",-1,nv)){
                compressed_optimal=true;persistSolution(compressed.get(),"compressed");
                check(api_.getdblattr(compressed.get(),GRB_DBL_ATTR_OBJVAL,&compressed_objective));
                if(std::fabs(compressed_objective-root_objective)>1e-7)throw std::runtime_error("round104_compression_numeric_loss");
                qualification="reoptimized_numerical_ACTIVE_not_rational_dual_certificate";rows=std::move(active);
            }else{qualification="UNKNOWN_compressed_LP_incomplete_emit_certified_ALL";compressed_objective=root_objective;}
        }else{qualification="UNKNOWN_pool_LP_incomplete_emit_certified_ALL";compressed_objective=root_objective;}
        std::ostringstream dual;dual<<std::setprecision(17)<<"{\"Pi\":[";
        for(std::size_t j=0;j<pi.size();++j){if(j)dual<<',';dual<<pi[j];}dual<<"],\"positive_repaired\":"<<positive_pi<<",\"qualification\":"<<std::quoted(qualification)<<'}';
        persist(prefix+".dual.json",dual.str());
        if(fileSha256(source_path)!=source_sha)throw std::runtime_error("round104_source_changed_during_preparation");
        ObjectiveArtifact artifact{source_path,source_sha,request.canonical_row_signature,prefix+".summary.json"};
        std::ostringstream row_evidence;row_evidence << std::setprecision(17) << "{\"source_sha256\":" << std::quoted(source_sha) << ",\"rows\":[";
        for(std::size_t r=0;r<rows.size();++r){if(r)row_evidence << ',';row_evidence << "{\"rhs\":" << rows[r].rhs << ",\"violation_lower\":" << rows[r].violation_lower << ",\"coefficients\":[";
            for(std::size_t j=0;j<rows[r].indices.size();++j){if(j)row_evidence << ',';row_evidence << '[' << std::quoted(identity.names.at(rows[r].indices[j])) << ',' << rows[r].coefficients[j] << ']';}
            row_evidence << "],\"proofs\":[";for(std::size_t j=0;j<rows[r].proofs.size();++j){if(j)row_evidence << ',';row_evidence << serviceSupportJson(rows[r].proofs[j]);}row_evidence << "]}";}
        row_evidence << "]}";persist(prefix+".rows.json",row_evidence.str());
        // Preserve every original byte. GRBwrite has a shorter decimal format;
        // using it here could change the actual certified dyadic coefficients.
        if(options_.round104_objective_resources=="active"&&!rows.empty()){
            std::ifstream original(source_path,std::ios::binary);std::string text((std::istreambuf_iterator<char>(original)),{});
            if(!original.eof()&&original.fail())throw std::runtime_error("round104_source_read");
            const std::string newline=text.find("\r\n")!=std::string::npos?"\r\n":"\n";
            std::size_t position=text.find("\nBounds");if(position==std::string::npos)throw std::runtime_error("round104_bounds_section");++position;
            std::ostringstream insert;insert << std::setprecision(17);
            for(std::size_t r=0;r<rows.size();++r){insert << " r104_objective_" << r << ":";
                for(std::size_t j=0;j<rows[r].indices.size();++j){const double a=rows[r].coefficients[j];insert << (a<0?" - ":" + ") << std::fabs(a) << ' ' << identity.names.at(rows[r].indices[j]);}
                insert << " <= " << rows[r].rhs << newline;}
            text.insert(position,insert.str());artifact.path=prefix+".lp";persist(artifact.path.string(),text);
            artifact.sha=fileSha256(artifact.path);artifact.signature=textSha256(request.canonical_row_signature+"|round104|"+insert.str());submitted=static_cast<int>(rows.size());
            // Parse/read back each newly submitted coefficient before any MIP.
            raw=nullptr;check(api_.readmodel(env_,artifact.path.string().c_str(),&raw));auto readback=own(raw);SolverNeutralLinearModel actual;int actual_rows=0,actual_vars=0;
            check(api_.getintattr(readback.get(),GRB_INT_ATTR_NUMCONSTRS,&actual_rows));check(api_.getintattr(readback.get(),GRB_INT_ATTR_NUMVARS,&actual_vars));
            if(actual_vars!=nv||actual_rows!=nr+submitted||!readLinearModel(api_,readback.get(),nv,actual_rows,actual))throw std::runtime_error("round104_artifact_dimensions");
            for(int j=0;j<nv;++j){char* name=nullptr;check(api_.getstrattrelement(readback.get(),GRB_STR_ATTR_VARNAME,j,&name));if(!name||identity.names[j]!=name)throw std::runtime_error("round104_artifact_column_order");}
            std::vector<char> actual_types(nv);std::vector<double> actual_lb(nv),actual_ub(nv),source_obj(nv),actual_obj(nv);
            check(api_.getcharattrarray(readback.get(),GRB_CHAR_ATTR_VTYPE,0,nv,actual_types.data()));
            check(api_.getdblattrarray(readback.get(),GRB_DBL_ATTR_LB,0,nv,actual_lb.data()));check(api_.getdblattrarray(readback.get(),GRB_DBL_ATTR_UB,0,nv,actual_ub.data()));
            check(api_.getdblattrarray(source.get(),GRB_DBL_ATTR_OBJ,0,nv,source_obj.data()));check(api_.getdblattrarray(readback.get(),GRB_DBL_ATTR_OBJ,0,nv,actual_obj.data()));
            if(actual_types!=identity.types||actual_lb!=identity.lower_bounds||actual_ub!=identity.upper_bounds||actual_obj!=source_obj)throw std::runtime_error("round104_original_domain_or_objective_changed");
            double original_constant=0,actual_constant=0;int original_sense=0,actual_sense=0;
            check(api_.getdblattr(source.get(),GRB_DBL_ATTR_OBJCON,&original_constant));check(api_.getdblattr(readback.get(),GRB_DBL_ATTR_OBJCON,&actual_constant));
            check(api_.getintattr(source.get(),GRB_INT_ATTR_MODELSENSE,&original_sense));check(api_.getintattr(readback.get(),GRB_INT_ATTR_MODELSENSE,&actual_sense));
            if(original_constant!=actual_constant||original_sense!=actual_sense)throw std::runtime_error("round104_original_objective_constant_or_sense_changed");
            for(int r=0;r<nr;++r){if(actual.senses[r]!=linear.senses[r]||actual.rhs[r]!=linear.rhs[r]||actual.row_starts[r+1]-actual.row_starts[r]!=linear.row_starts[r+1]-linear.row_starts[r])throw std::runtime_error("round104_original_row_changed");
                for(int j=linear.row_starts[r],a=actual.row_starts[r];j<linear.row_starts[r+1];++j,++a)if(actual.column_indices[a]!=linear.column_indices[j]||actual.coefficients[a]!=linear.coefficients[j])throw std::runtime_error("round104_original_coefficient_changed");}
            for(int r=0;r<submitted;++r){std::map<int,double> expected;for(std::size_t j=0;j<rows[r].indices.size();++j)expected[rows[r].indices[j]]=rows[r].coefficients[j];std::map<int,double> got;
                for(int j=actual.row_starts[nr+r];j<actual.row_starts[nr+r+1];++j)got[actual.column_indices[j]]=actual.coefficients[j];
                if(got!=expected||actual.senses[nr+r]!=GRB_LESS_EQUAL||actual.rhs[nr+r]!=rows[r].rhs)throw std::runtime_error("round104_dyadic_row_readback");}
        }
        calls.close();if(!calls)throw std::runtime_error("round104_calls_close");
        auto numeric=[](bool available,double value){std::ostringstream s;s<<std::setprecision(17);if(available)s<<value;else s<<"null";return s.str();};
        std::ostringstream summary;summary << std::setprecision(17) << "{\"mode\":" << std::quoted(options_.round104_objective_resources)
            << ",\"cache_hit\":false,\"source_sha256\":" << std::quoted(source_sha) << ",\"canonical_sha256\":" << std::quoted(artifact.sha)
            << ",\"canonical_path\":" << std::quoted(artifact.path.string()) << ",\"root_optimal\":" << (root_optimal?"true":"false")
            << ",\"root_objective\":";
        if(root_optimal)summary << root_objective;else summary << "null";
        summary << ",\"pool_rows\":" << pool_rows.size() << ",\"pool_iterations\":" << pool_iterations
            << ",\"initial_objective\":" << numeric(standard_optimal,initial_objective)
            << ",\"finite_pool_objective\":" << numeric(root_optimal,root_objective)
            << ",\"last_qualified_pool_bound\":" << numeric(standard_optimal,root_objective)
            << ",\"compressed_objective\":" << numeric(compressed_optimal,compressed_objective) << ",\"positive_Pi_repaired\":" << positive_pi
            << ",\"qualification\":" << std::quoted(qualification) << ",\"pool_stop\":" << std::quoted(pool_stop)
            << ",\"Optimize_calls\":" << optimize_calls << ",\"DP_calls\":" << dp_calls
            << ",\"selected\":" << selected << ",\"reliable_scaled_rows\":" << rows.size() << ",\"submitted\":" << submitted
            << ",\"original_mip_FeasibilityTol\":" << mip_feas << ",\"seconds\":" << std::chrono::duration<double>(Clock::now()-started).count() << '}';
        persist(prefix+".summary.json",summary.str());objective_artifacts_.emplace(key.str(),artifact);adopt(artifact);
    }
