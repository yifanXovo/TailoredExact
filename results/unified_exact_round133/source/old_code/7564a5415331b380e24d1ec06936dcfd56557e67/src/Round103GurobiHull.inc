// Included in GurobiFixedIntervalBackend. All auxiliary models are disposable;
// the canonical source and the official MIP environment keep their tolerances.
    struct HullArtifact {
        std::filesystem::path path;
        std::string sha, signature, evidence;
    };
    std::map<std::string,HullArtifact> hull_artifacts_;

    void prepareResourceHull(FixedIntervalMipRequest& request) override {
        if (options_.round103_resource_hull == "off") return;
        if (!available_ || !configuration_valid_ ||
            request.solve_kind == FixedIntervalSolveKind::PaperLpRelaxation ||
            request.solve_kind == FixedIntervalSolveKind::LegacyMipQuantum ||
            request.interval_mip_policy != "round55-vd-p" ||
            request.canonical_model_fingerprint.empty() || request.leaf_id.empty() ||
            request.canonical_model_scope.empty() || request.canonical_row_signature.empty() ||
            request.native_log_path.empty() || !request.variable_bound_overrides.empty() ||
            !request.additional_linear_rows.empty() || !request.round60_fixed_inventory.empty() ||
            fileSha256(request.canonical_model_path) != request.canonical_model_fingerprint)
            throw std::runtime_error("round103_original_identity_or_scope");
        const auto started = Clock::now();
        const auto source_path = request.canonical_model_path;
        const auto source_sha = request.canonical_model_fingerprint;
        std::ostringstream key;
        key << std::setprecision(17) << source_sha << '|' << request.leaf_id << '|'
            << request.canonical_model_scope << '|' << request.canonical_row_signature << '|'
            << request.gamma_L << '|' << request.gamma_U << '|' << request.verified_cutoff
            << '|' << fileSha256(instance_.path) << '|' << options_.round103_resource_hull;
        const auto prefix = request.native_log_path.string()+".round103";
        if (request.native_log_path.has_parent_path())
            std::filesystem::create_directories(request.native_log_path.parent_path());
        auto persist = [](const std::string& path,const std::string& content) {
            if (std::filesystem::exists(path)) throw std::runtime_error("round103_evidence_exists:"+path);
            std::ofstream f(path,std::ios::binary);f << content << '\n';f.close();
            if (!f) throw std::runtime_error("round103_evidence_write:"+path);
        };
        auto adopt = [&](const HullArtifact& a) {
            if (fileSha256(a.path)!=a.sha) throw std::runtime_error("round103_cached_artifact_changed");
            request.canonical_model_path=a.path;request.canonical_model_fingerprint=a.sha;
            request.canonical_row_signature=a.signature;
            const auto old=leaves_.find(request.leaf_id);
            if(old!=leaves_.end()&&old->second.model_fingerprint!=a.sha)discardLeaf(request.leaf_id);
        };
        auto cached=hull_artifacts_.find(key.str());
        if(cached!=hull_artifacts_.end()) {
            adopt(cached->second);
            std::ostringstream s;s << "{\"cache_hit\":true,\"source_sha256\":" << std::quoted(source_sha)
                << ",\"canonical_sha256\":" << std::quoted(cached->second.sha)
                << ",\"paid_evidence\":" << std::quoted(cached->second.evidence) << '}';
            persist(prefix+".summary.json",s.str());return;
        }
        if(std::filesystem::exists(prefix+".calls.jsonl"))throw std::runtime_error("round103_calls_exists");
        std::ofstream calls(prefix+".calls.jsonl");
        if(!calls)throw std::runtime_error("round103_calls_open");
        auto trace=[&](const std::string& s){calls << s << '\n';calls.flush();if(!calls)throw std::runtime_error("round103_calls_write");};
        auto check=[](int rc){if(rc)throw std::runtime_error("round103_api_"+std::to_string(rc));};
        auto remaining=[&](){return request.global_deadline_remaining_seconds-
            std::chrono::duration<double>(Clock::now()-started).count();};
        auto own=[&](GRBmodel* m){return std::unique_ptr<GRBmodel,std::function<void(GRBmodel*)>>(m,[&](GRBmodel* p){if(p)api_.freemodel(p);});};
        GRBmodel* raw=nullptr;check(api_.readmodel(env_,source_path.string().c_str(),&raw));auto source=own(raw);
        if(!source)throw std::runtime_error("round103_source_null");
        int nv=0,nr=0,ng=0;check(api_.getintattr(source.get(),GRB_INT_ATTR_NUMVARS,&nv));
        check(api_.getintattr(source.get(),GRB_INT_ATTR_NUMCONSTRS,&nr));
        check(api_.getintattr(source.get(),GRB_INT_ATTR_NUMGENCONSTRS,&ng));
        if(nv<=0||ng)throw std::runtime_error("round103_linear_model_required");
        NativeOtB1LinearModel identity;identity.names.resize(nv);identity.types.resize(nv);
        identity.lower_bounds.resize(nv);identity.upper_bounds.resize(nv);
        for(int j=0;j<nv;++j){char* name=nullptr;check(api_.getstrattrelement(source.get(),GRB_STR_ATTR_VARNAME,j,&name));
            if(!name)throw std::runtime_error("round103_column_name");identity.names[j]=name;}
        check(api_.getcharattrarray(source.get(),GRB_CHAR_ATTR_VTYPE,0,nv,identity.types.data()));
        check(api_.getdblattrarray(source.get(),GRB_DBL_ATTR_LB,0,nv,identity.lower_bounds.data()));
        check(api_.getdblattrarray(source.get(),GRB_DBL_ATTR_UB,0,nv,identity.upper_bounds.data()));
        SolverNeutralLinearModel linear;if(!readLinearModel(api_,source.get(),nv,nr,linear))throw std::runtime_error("round103_matrix_read");
        identity.row_starts=linear.row_starts;identity.column_indices=linear.column_indices;
        identity.coefficients=linear.coefficients;identity.senses=linear.senses;identity.rhs=linear.rhs;
        const auto contract=prepareServiceContract(instance_,identity);
        if(!contract.valid)throw std::runtime_error("round103_model_audit:"+contract.reason);
        double mip_feas=0;check(api_.getdblparam(api_.getenv(source.get()),GRB_DBL_PAR_FEASIBILITYTOL,&mip_feas));
        std::ostringstream binding;binding << "{\"source_sha256\":" << std::quoted(source_sha)
            << ",\"source_path\":" << std::quoted(source_path.string()) << ",\"scope\":" << std::quoted(request.canonical_model_scope)
            << ",\"leaf\":" << std::quoted(request.leaf_id) << ",\"input_sha256\":" << std::quoted(fileSha256(instance_.path))
            << ",\"column_contract\":" << serviceContractJson(contract) << '}';
        persist(prefix+".contract.json",binding.str());
        auto root=own(api_.copymodel(source.get()));if(!root)throw std::runtime_error("round103_root_copy");
        std::vector<char> continuous(nv,GRB_CONTINUOUS);
        check(api_.setcharattrarray(root.get(),GRB_CHAR_ATTR_VTYPE,0,nv,continuous.data()));check(api_.updatemodel(root.get()));
        long long optimize_calls=0,dp_calls=0;int submitted=0,selected=0;std::vector<ServiceCut> rows;
        auto optimize=[&](GRBmodel* m,const std::string& kind,int vehicle,int column_count){
            if(remaining()<=0)return false;
            GRBenv* e=api_.getenv(m);if(!e)throw std::runtime_error("round103_aux_environment");
            check(api_.setintparam(e,GRB_INT_PAR_THREADS,1));check(api_.setintparam(e,GRB_INT_PAR_SEED,options_.gurobi_seed));
            check(api_.setintparam(e,GRB_INT_PAR_PRESOLVE,options_.gurobi_presolve));check(api_.setintparam(e,GRB_INT_PAR_METHOD,1));
            check(api_.setdblparam(e,GRB_DBL_PAR_FEASIBILITYTOL,1e-9));check(api_.setdblparam(e,GRB_DBL_PAR_OPTIMALITYTOL,1e-9));
            check(api_.setdblparam(e,GRB_DBL_PAR_WORKLIMIT,GRB_INFINITY));check(api_.setstrparam(e,GRB_STR_PAR_LOGFILE,""));
            check(api_.setintparam(e,GRB_INT_PAR_OUTPUTFLAG,0));
            const double global_remaining=remaining();if(global_remaining<=0)return false;
            check(api_.setdblparam(e,GRB_DBL_PAR_TIMELIMIT,global_remaining));
            const auto serial=++optimize_calls;std::ostringstream b;b << "{\"event\":\"Optimize_begin\",\"serial\":" << serial
                << ",\"kind\":" << std::quoted(kind) << ",\"vehicle\":" << vehicle << ",\"columns\":" << column_count << '}';trace(b.str());
            const int rc=api_.optimize(m);int status=0;check(api_.getintattr(m,GRB_INT_ATTR_STATUS,&status));
            std::ostringstream r;r << "{\"event\":\"Optimize_return\",\"serial\":" << serial << ",\"return_code\":" << rc << ",\"status\":" << status << '}';trace(r.str());
            check(rc);return status==GRB_OPTIMAL;
        };
        const bool root_optimal=optimize(root.get(),"standard_root",-1,nv);
        std::vector<double> point(nv);double root_objective=0;
        if(root_optimal){check(api_.getdblattrarray(root.get(),GRB_DBL_ATTR_X,0,nv,point.data()));check(api_.getdblattr(root.get(),GRB_DBL_ATTR_OBJVAL,&root_objective));
            std::ostringstream p;p << std::setprecision(17) << "{\"source_sha256\":" << std::quoted(source_sha) << ",\"objective\":" << root_objective << ",\"variables\":[";
            for(int j=0;j<nv;++j){if(j)p << ',';p << '[' << std::quoted(identity.names[j]) << ',' << point[j] << ']';}p << "]}";persist(prefix+".point.json",p.str());
            for(std::size_t k=0;k<contract.columns.size()&&remaining()>0;++k){
                const auto n=contract.resource.initial.size();ServicePoint v(n,{0,0,0});std::vector<std::array<int,3>> widths(n,{0,0,0});
                for(std::size_t i=1;i<n;++i){const int A=std::min(contract.resource.initial[i],contract.resource.capacities[k]);
                    const int B=std::min(contract.resource.station_capacity[i]-contract.resource.initial[i],contract.resource.capacities[k]);widths[i]={A,B,A>0||B>0?1:0};
                    for(int t=0;t<3;++t)v[i][t]=point.at(contract.columns[k][i][t]);}
                raw=nullptr;check(api_.newmodel(env_,&raw,"resource_hull_distance",0,nullptr,nullptr,nullptr,nullptr,nullptr));auto master=own(raw);
                if(!master)throw std::runtime_error("round103_master_null");
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
                const auto member=classifyServiceHull(contract,static_cast<int>(k),v,solve,{},1e-8,trace);dp_calls+=member.dp_calls;
                persist(prefix+".vehicle"+std::to_string(k)+".json",hullMembershipJson(member));
                if(member.status=="OUTSIDE"){
                    ++selected;auto row=member.cut;double largest=0;for(double a:row.coefficients)largest=std::max(largest,std::fabs(a));
                    if(!largest)throw std::runtime_error("round103_empty_separation");
                    const int exponent=-std::ilogb(largest);bool representable=true;double activity=0;
                    for(std::size_t j=0;j<row.coefficients.size();++j){row.coefficients[j]=std::ldexp(row.coefficients[j],exponent);
                        const double a=row.coefficients[j];if(!std::isfinite(a)||std::fabs(a)<1e-13)representable=false;
                        activity=std::nextafter(activity+std::nextafter(a*point[row.indices[j]],-GRB_INFINITY),-GRB_INFINITY);}
                    row.rhs=std::ldexp(row.rhs,exponent);row.activity_lower=activity;row.violation_lower=std::nextafter(activity-row.rhs,-GRB_INFINITY);
                    if(representable&&std::isfinite(row.rhs)&&row.violation_lower>10*mip_feas)rows.push_back(std::move(row));
                }
            }
        }
        if(fileSha256(source_path)!=source_sha)throw std::runtime_error("round103_source_changed_during_preparation");
        HullArtifact artifact{source_path,source_sha,request.canonical_row_signature,prefix+".summary.json"};
        std::ostringstream row_evidence;row_evidence << std::setprecision(17) << "{\"source_sha256\":" << std::quoted(source_sha) << ",\"rows\":[";
        for(std::size_t r=0;r<rows.size();++r){if(r)row_evidence << ',';row_evidence << "{\"rhs\":" << rows[r].rhs << ",\"violation_lower\":" << rows[r].violation_lower << ",\"coefficients\":[";
            for(std::size_t j=0;j<rows[r].indices.size();++j){if(j)row_evidence << ',';row_evidence << '[' << std::quoted(identity.names.at(rows[r].indices[j])) << ',' << rows[r].coefficients[j] << ']';}
            row_evidence << "],\"proofs\":[";for(std::size_t j=0;j<rows[r].proofs.size();++j){if(j)row_evidence << ',';row_evidence << serviceSupportJson(rows[r].proofs[j]);}row_evidence << "]}";}
        row_evidence << "]}";persist(prefix+".rows.json",row_evidence.str());
        // Preserve every original byte. GRBwrite has a shorter decimal format;
        // using it here could change the actual certified dyadic coefficients.
        if(options_.round103_resource_hull=="submit"&&!rows.empty()){
            std::ifstream original(source_path,std::ios::binary);std::string text((std::istreambuf_iterator<char>(original)),{});
            if(!original.eof()&&original.fail())throw std::runtime_error("round103_source_read");
            const std::string newline=text.find("\r\n")!=std::string::npos?"\r\n":"\n";
            std::size_t position=text.find("\nBounds");if(position==std::string::npos)throw std::runtime_error("round103_bounds_section");++position;
            std::ostringstream insert;insert << std::setprecision(17);
            for(std::size_t r=0;r<rows.size();++r){insert << " r103_hull_" << r << ":";
                for(std::size_t j=0;j<rows[r].indices.size();++j){const double a=rows[r].coefficients[j];insert << (a<0?" - ":" + ") << std::fabs(a) << ' ' << identity.names.at(rows[r].indices[j]);}
                insert << " <= " << rows[r].rhs << newline;}
            text.insert(position,insert.str());artifact.path=prefix+".lp";persist(artifact.path.string(),text);
            artifact.sha=fileSha256(artifact.path);artifact.signature=textSha256(request.canonical_row_signature+"|round103|"+insert.str());submitted=static_cast<int>(rows.size());
            // Parse/read back each newly submitted coefficient before any MIP.
            raw=nullptr;check(api_.readmodel(env_,artifact.path.string().c_str(),&raw));auto readback=own(raw);SolverNeutralLinearModel actual;int actual_rows=0,actual_vars=0;
            check(api_.getintattr(readback.get(),GRB_INT_ATTR_NUMCONSTRS,&actual_rows));check(api_.getintattr(readback.get(),GRB_INT_ATTR_NUMVARS,&actual_vars));
            if(actual_vars!=nv||actual_rows!=nr+submitted||!readLinearModel(api_,readback.get(),nv,actual_rows,actual))throw std::runtime_error("round103_artifact_dimensions");
            for(int j=0;j<nv;++j){char* name=nullptr;check(api_.getstrattrelement(readback.get(),GRB_STR_ATTR_VARNAME,j,&name));if(!name||identity.names[j]!=name)throw std::runtime_error("round103_artifact_column_order");}
            std::vector<char> actual_types(nv);std::vector<double> actual_lb(nv),actual_ub(nv),source_obj(nv),actual_obj(nv);
            check(api_.getcharattrarray(readback.get(),GRB_CHAR_ATTR_VTYPE,0,nv,actual_types.data()));
            check(api_.getdblattrarray(readback.get(),GRB_DBL_ATTR_LB,0,nv,actual_lb.data()));check(api_.getdblattrarray(readback.get(),GRB_DBL_ATTR_UB,0,nv,actual_ub.data()));
            check(api_.getdblattrarray(source.get(),GRB_DBL_ATTR_OBJ,0,nv,source_obj.data()));check(api_.getdblattrarray(readback.get(),GRB_DBL_ATTR_OBJ,0,nv,actual_obj.data()));
            if(actual_types!=identity.types||actual_lb!=identity.lower_bounds||actual_ub!=identity.upper_bounds||actual_obj!=source_obj)throw std::runtime_error("round103_original_domain_or_objective_changed");
            double original_constant=0,actual_constant=0;int original_sense=0,actual_sense=0;
            check(api_.getdblattr(source.get(),GRB_DBL_ATTR_OBJCON,&original_constant));check(api_.getdblattr(readback.get(),GRB_DBL_ATTR_OBJCON,&actual_constant));
            check(api_.getintattr(source.get(),GRB_INT_ATTR_MODELSENSE,&original_sense));check(api_.getintattr(readback.get(),GRB_INT_ATTR_MODELSENSE,&actual_sense));
            if(original_constant!=actual_constant||original_sense!=actual_sense)throw std::runtime_error("round103_original_objective_constant_or_sense_changed");
            for(int r=0;r<nr;++r){if(actual.senses[r]!=linear.senses[r]||actual.rhs[r]!=linear.rhs[r]||actual.row_starts[r+1]-actual.row_starts[r]!=linear.row_starts[r+1]-linear.row_starts[r])throw std::runtime_error("round103_original_row_changed");
                for(int j=linear.row_starts[r],a=actual.row_starts[r];j<linear.row_starts[r+1];++j,++a)if(actual.column_indices[a]!=linear.column_indices[j]||actual.coefficients[a]!=linear.coefficients[j])throw std::runtime_error("round103_original_coefficient_changed");}
            for(int r=0;r<submitted;++r){std::map<int,double> expected;for(std::size_t j=0;j<rows[r].indices.size();++j)expected[rows[r].indices[j]]=rows[r].coefficients[j];std::map<int,double> got;
                for(int j=actual.row_starts[nr+r];j<actual.row_starts[nr+r+1];++j)got[actual.column_indices[j]]=actual.coefficients[j];
                if(got!=expected||actual.senses[nr+r]!=GRB_LESS_EQUAL||actual.rhs[nr+r]!=rows[r].rhs)throw std::runtime_error("round103_dyadic_row_readback");}
        }
        calls.close();if(!calls)throw std::runtime_error("round103_calls_close");
        std::ostringstream summary;summary << std::setprecision(17) << "{\"mode\":" << std::quoted(options_.round103_resource_hull)
            << ",\"cache_hit\":false,\"source_sha256\":" << std::quoted(source_sha) << ",\"canonical_sha256\":" << std::quoted(artifact.sha)
            << ",\"canonical_path\":" << std::quoted(artifact.path.string()) << ",\"root_optimal\":" << (root_optimal?"true":"false")
            << ",\"root_objective\":";
        if(root_optimal)summary << root_objective;else summary << "null";
        summary << ",\"Optimize_calls\":" << optimize_calls << ",\"DP_calls\":" << dp_calls
            << ",\"selected\":" << selected << ",\"reliable_scaled_rows\":" << rows.size() << ",\"submitted\":" << submitted
            << ",\"original_mip_FeasibilityTol\":" << mip_feas << ",\"seconds\":" << std::chrono::duration<double>(Clock::now()-started).count() << '}';
        persist(prefix+".summary.json",summary.str());hull_artifacts_.emplace(key.str(),artifact);adopt(artifact);
    }
