// Included in GurobiBaseline.cpp; no optimizer call or parameter tuning here.
#ifdef _WIN32
struct Round112NativeMatrix {
    SolverNeutralModelDomain domain;
    SolverNeutralLinearModel linear;
    std::vector<double> objective;
    double constant=0;
    int sense=0;
    std::string json;
};

static Round112NativeMatrix round112ReadMatrix(const GurobiApi& api, GRBmodel* model) {
    auto check=[](int rc) { if(rc) throw std::runtime_error("round112_matrix_api_"+std::to_string(rc)); };
    Round112NativeMatrix m;
    int n=0,r=0,g=0,q=0,qnz=0;
    check(api.getintattr(model,GRB_INT_ATTR_NUMVARS,&n));
    check(api.getintattr(model,GRB_INT_ATTR_NUMCONSTRS,&r));
    check(api.getintattr(model,GRB_INT_ATTR_NUMGENCONSTRS,&g));
    check(api.getintattr(model,GRB_INT_ATTR_NUMQCONSTRS,&q));
    check(api.getintattr(model,GRB_INT_ATTR_NUMQNZS,&qnz));
    if(n<=0 || g || q || qnz) throw std::runtime_error("round112_non_linear_model");
    m.domain.names.resize(n);m.domain.lower_bounds.resize(n);m.domain.upper_bounds.resize(n);
    m.domain.variable_types.resize(n);m.objective.resize(n);
    check(api.getdblattrarray(model,GRB_DBL_ATTR_LB,0,n,m.domain.lower_bounds.data()));
    check(api.getdblattrarray(model,GRB_DBL_ATTR_UB,0,n,m.domain.upper_bounds.data()));
    check(api.getcharattrarray(model,GRB_CHAR_ATTR_VTYPE,0,n,m.domain.variable_types.data()));
    check(api.getdblattrarray(model,GRB_DBL_ATTR_OBJ,0,n,m.objective.data()));
    check(api.getdblattr(model,GRB_DBL_ATTR_OBJCON,&m.constant));
    check(api.getintattr(model,GRB_INT_ATTR_MODELSENSE,&m.sense));
    if(!readLinearModel(api,model,n,r,m.linear)) throw std::runtime_error("round112_matrix_read_failed");
    std::ostringstream o;o<<std::setprecision(17)<<"{\"sense\":"<<m.sense<<",\"constant\":"<<m.constant<<",\"columns\":[";
    for(int i=0;i<n;++i) {
        char* name=nullptr;check(api.getstrattrelement(model,GRB_STR_ATTR_VARNAME,i,&name));
        if(!name)throw std::runtime_error("round112_missing_column_name");
        m.domain.names[i]=name;
        if(i)o<<',';
        o<<"["<<std::quoted(m.domain.names[i])<<','<<std::quoted(std::string(1,m.domain.variable_types[i]))
         <<','<<m.domain.lower_bounds[i]<<','<<m.domain.upper_bounds[i]<<','<<m.objective[i]<<']';
    }
    o<<"],\"rows\":[";
    for(int i=0;i<r;++i) {
        char* name=nullptr;check(api.getstrattrelement(model,GRB_STR_ATTR_CONSTRNAME,i,&name));
        if(!name)throw std::runtime_error("round112_missing_row_name");
        if(i)o<<',';
        o<<'['<<std::quoted(std::string(name))<<','<<std::quoted(std::string(1,m.linear.senses[i]))<<','<<m.linear.rhs[i]<<",[";
        for(int j=m.linear.row_starts[i];j<m.linear.row_starts[i+1];++j) {
            if(j!=m.linear.row_starts[i])o<<',';
            o<<'['<<m.linear.column_indices[j]<<','<<m.linear.coefficients[j]<<']';
        }
        o<<"]]";
    }
    o<<"]}\n";m.json=o.str();return m;
}

static void round112Save(const std::string& path,const std::string& data) {
    if(std::filesystem::exists(path))throw std::runtime_error("round112_evidence_collision");
    std::ofstream f(path,std::ios::binary);f<<data;f.close();
    if(!f)throw std::runtime_error("round112_evidence_write_failed");
}

static void round112Submit(const GurobiApi& api,GRBmodel* model,const Instance& in,
    const SolveOptions& options,const SolveResult& seed,const std::string& path,
    std::vector<double>& values,std::vector<char>& types) {
    const auto started=Clock::now();
    auto check=[](int rc){if(rc)throw std::runtime_error("round112_start_api_"+std::to_string(rc));};
    try {
        const auto before=round112ReadMatrix(api,model);
        round112Save(path+".before.matrix.json",before.json);
        auto routes=normalizeRound61Routes(in,options.lambda,seed.routes);
        // Explicit empty vehicles retain their own original capacity/ID.
        for(int k=0;k<in.M;++k)if(std::none_of(routes.begin(),routes.end(),[&](const RoutePlan& r){return r.vehicle==k;}))
            routes.push_back({k,{0,0},{}});
        std::sort(routes.begin(),routes.end(),[](const RoutePlan& a,const RoutePlan& b){return a.vehicle<b.vehicle;});
        const auto mapped=mapVerifiedRoutesToCanonicalModel(in,options,routes,
            "round112_own_complete_ENS_H",0.0,double(in.V-1)/in.V,seed.objective,before.domain);
        if(!mapped.complete)throw std::runtime_error("round112_mapping_"+mapped.failure_reason);
        const auto residual=validateCandidateLinearResidual(before.linear,mapped.values,1e-7);
        if(!residual.checked || !residual.valid)throw std::runtime_error("round112_rows_"+residual.failure_reason);
        double obj=before.constant;
        for(std::size_t i=0;i<mapped.values.size();++i)obj+=mapped.values[i]*before.objective[i];
        if(before.sense!=GRB_MINIMIZE || !std::isfinite(obj) || std::abs(obj-seed.objective)>1e-7)
            throw std::runtime_error("round112_objective_mismatch");
        check(api.setintattr(model,GRB_INT_ATTR_NUMSTART,1));
        check(api.setintparam(api.getenv(model),GRB_INT_PAR_STARTNUMBER,0));
        check(api.updatemodel(model));
        check(api.setdblattrarray(model,GRB_DBL_ATTR_START,0,int(mapped.values.size()),const_cast<double*>(mapped.values.data())));
        check(api.updatemodel(model));
        std::vector<double> readback(mapped.values.size());
        check(api.getdblattrarray(model,GRB_DBL_ATTR_START,0,int(readback.size()),readback.data()));
        std::ostringstream v;v<<std::setprecision(17)<<"variable,type,value,readback\n";
        for(std::size_t i=0;i<readback.size();++i) {
            v<<before.domain.names[i]<<','<<before.domain.variable_types[i]<<','<<mapped.values[i]<<','<<readback[i]<<'\n';
            if(!std::isfinite(readback[i]) || readback[i]!=mapped.values[i])throw std::runtime_error("round112_start_readback_mismatch");
        }
        round112Save(path+".values.csv",v.str());
        const auto after=round112ReadMatrix(api,model);
        round112Save(path+".after.matrix.json",after.json);
        if(before.json!=after.json)throw std::runtime_error("round112_start_changed_matrix_domain_objective_or_names");
        std::ostringstream receipt;receipt<<std::setprecision(17)
          <<"{\"submitted\":true,\"API\":\"GRBsetdblattrarray(Start)\",\"submission_count\":1,\"readback_valid\":true,\"matrix_unchanged\":true"
          <<",\"columns\":"<<mapped.values.size()<<",\"rows_checked\":"<<residual.checked_rows
          <<",\"maximum_row_violation\":"<<residual.maximum_violation<<",\"objective\":"<<obj
          <<",\"mapping_validation_submission_seconds\":"<<std::chrono::duration<double>(Clock::now()-started).count()
          <<",\"native_adoption\":\"unknown_pending_native_log\"}\n";
        round112Save(path+".json",receipt.str());values=mapped.values;types=before.domain.variable_types;
    } catch(const std::exception& e) {
        std::ostringstream receipt;receipt<<"{\"qualified\":false,\"failure\":"<<std::quoted(e.what())<<"}\n";
        if(!std::filesystem::exists(path+".json"))round112Save(path+".json",receipt.str());
        throw;
    }
}
#endif
