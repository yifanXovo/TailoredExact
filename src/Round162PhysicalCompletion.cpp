#include "Round162PhysicalCompletion.hpp"
#include "FileSha256.hpp"
#include "ObjectiveResourceCompression.hpp"
#include <gurobi_c.h>
#include <fstream>
#include <iomanip>
#include <regex>
#include <set>
#include <cmath>
#include <sstream>

namespace ebrp { namespace {
void ck(int rc){if(rc)throw std::runtime_error("round162_native_api_"+std::to_string(rc));}
struct Model {
    GRBenv* env=nullptr; GRBmodel* m=nullptr;
    explicit Model(const std::filesystem::path& p){
        ck(GRBemptyenv(&env));ck(GRBsetintparam(env,"OutputFlag",0));ck(GRBstartenv(env));
        ck(GRBreadmodel(env,p.string().c_str(),&m));
    }
    ~Model(){if(m)GRBfreemodel(m);if(env)GRBfreeenv(env);}
};
struct Matrix {
    std::vector<std::string> names,rows;
    std::vector<double> lb,ub,obj,rhs,coef;
    std::vector<char> type,sense;
    std::vector<int> start,index;
    explicit Matrix(GRBmodel* m){
        int n=0,r=0,nnz=0;ck(GRBgetintattr(m,"NumVars",&n));ck(GRBgetintattr(m,"NumConstrs",&r));
        names.resize(n);rows.resize(r);lb.resize(n);ub.resize(n);obj.resize(n);type.resize(n);
        rhs.resize(r);sense.resize(r);start.resize(r+1);
        ck(GRBgetdblattrarray(m,"LB",0,n,lb.data()));ck(GRBgetdblattrarray(m,"UB",0,n,ub.data()));
        ck(GRBgetdblattrarray(m,"Obj",0,n,obj.data()));ck(GRBgetcharattrarray(m,"VType",0,n,type.data()));
        for(int j=0;j<n;++j){char* s=nullptr;ck(GRBgetstrattrelement(m,"VarName",j,&s));names[j]=s;}
        for(int j=0;j<r;++j){char* s=nullptr;ck(GRBgetstrattrelement(m,"ConstrName",j,&s));rows[j]=s;}
        ck(GRBgetdblattrarray(m,"RHS",0,r,rhs.data()));ck(GRBgetcharattrarray(m,"Sense",0,r,sense.data()));
        ck(GRBgetconstrs(m,&nnz,nullptr,nullptr,nullptr,0,r));index.resize(nnz);coef.resize(nnz);
        ck(GRBgetconstrs(m,&nnz,start.data(),index.data(),coef.data(),0,r));start[r]=nnz;
    }
};
std::string q(const std::string& s){std::ostringstream o;o<<std::quoted(s);return o.str();}
void registry(const Matrix& a,const std::filesystem::path& dir,const std::string& label){
    std::ofstream c(dir/(label+"_columns.jsonl")),r(dir/(label+"_rows.jsonl"));
    c<<std::setprecision(17);r<<std::setprecision(17);
    for(size_t j=0;j<a.names.size();++j)c<<"{\"name\":"<<q(a.names[j])<<",\"lb\":"<<a.lb[j]<<",\"ub\":"<<a.ub[j]<<",\"obj\":"<<a.obj[j]<<",\"type\":"<<q(std::string(1,a.type[j]))<<"}\n";
    for(size_t i=0;i<a.rows.size();++i){r<<"{\"name\":"<<q(a.rows[i])<<",\"sense\":"<<q(std::string(1,a.sense[i]))<<",\"rhs\":"<<a.rhs[i]<<",\"terms\":{";
        for(int k=a.start[i];k<a.start[i+1];++k){if(k>a.start[i])r<<',';r<<q(a.names[a.index[k]])<<':'<<a.coef[k];}r<<"}}\n";}
    if(!c||!r)throw std::runtime_error("round162_registry_write");
}
std::map<std::string,int> ids(const Matrix& a){
    std::map<std::string,int> out;
    for(size_t j=0;j<a.names.size();++j){
        if(!out.emplace(a.names[j],int(j)).second)throw std::runtime_error("round162_duplicate_column");
    }
    return out;
}
using Terms=std::map<std::string,double>;
Terms terms(const Matrix& a,size_t i){Terms v;for(int k=a.start[i];k<a.start[i+1];++k)v[a.names[a.index[k]]]=a.coef[k];return v;}
void unchanged(const Matrix& a,const Matrix& b){
    auto js=ids(b);std::map<std::string,int> rs;for(size_t i=0;i<b.rows.size();++i)rs.emplace(b.rows[i],int(i));
    for(size_t j=0;j<a.names.size();++j){int k=js.at(a.names[j]);if(a.lb[j]!=b.lb[k]||a.ub[j]!=b.ub[k]||a.type[j]!=b.type[k]||a.obj[j]!=b.obj[k])throw std::runtime_error("round162_changed_old_column:"+a.names[j]);}
    for(size_t i=0;i<a.rows.size();++i){int k=rs.at(a.rows[i]);if(a.sense[i]!=b.sense[k]||a.rhs[i]!=b.rhs[k]||terms(a,i)!=terms(b,k))throw std::runtime_error("round162_changed_old_row:"+a.rows[i]);}
}
// GRBwrite's human-readable LP formatting can round a stored bound. Preserve
// all loaded doubles verbatim, then require exact native matrix readback.
void exactLp(GRBmodel* m,const Matrix& a,const std::filesystem::path& path){
    int sense=0;double constant=0;ck(GRBgetintattr(m,"ModelSense",&sense));ck(GRBgetdblattr(m,"ObjCon",&constant));
    if(sense!=1||constant!=0)throw std::runtime_error("round162_unregistered_objective");
    std::ofstream s(path);s<<std::setprecision(17)<<"Minimize\n obj:";
    auto term=[&](double c,const std::string& n){if(c)s<<(c<0?" - ":" + ")<<std::fabs(c)<<' '<<n;};
    for(size_t j=0;j<a.names.size();++j)term(a.obj[j],a.names[j]);
    s<<"\nSubject To\n";
    for(size_t i=0;i<a.rows.size();++i){s<<' '<<a.rows[i]<<':';
        for(int k=a.start[i];k<a.start[i+1];++k)term(a.coef[k],a.names[a.index[k]]);
        if(a.start[i]==a.start[i+1])s<<" 0 G";
        s<<(a.sense[i]=='='?" = ":a.sense[i]=='<'?" <= ":" >= ")<<a.rhs[i]<<'\n';}
    s<<"Bounds\n";
    for(size_t j=0;j<a.names.size();++j){
        const bool l=a.lb[j]>-GRB_INFINITY,u=a.ub[j]<GRB_INFINITY;
        if(!l&&!u)s<<' '<<a.names[j]<<" free\n";
        else if(l&&u)s<<' '<<a.lb[j]<<" <= "<<a.names[j]<<" <= "<<a.ub[j]<<'\n';
        else if(l)s<<' '<<a.names[j]<<" >= "<<a.lb[j]<<'\n';
        else s<<" -inf <= "<<a.names[j]<<" <= "<<a.ub[j]<<'\n';
    }
    s<<"Generals\n";for(size_t j=0;j<a.names.size();++j)if(a.type[j]=='I')s<<' '<<a.names[j]<<'\n';
    s<<"Binaries\n";for(size_t j=0;j<a.names.size();++j)if(a.type[j]=='B')s<<' '<<a.names[j]<<'\n';
    s<<"End\n";if(!s)throw std::runtime_error("round162_exact_lp_write");
}
}
Round162Artifact buildRound162Completion(const Instance& in,const std::filesystem::path& original,
        const std::filesystem::path& output,bool full,bool omit_endpoint_time){
    Model owner(original);auto* m=owner.m;Matrix a(m);const auto dir=output.parent_path();registry(a,dir,"original");
    auto js=ids(a);Round162Artifact out;out.original_columns=int(a.names.size());out.original_rows=int(a.rows.size());
    out.lower=a.lb.at(js.at("G"));out.upper=a.ub.at(js.at("G"));
    if(!std::isfinite(out.lower)||!std::isfinite(out.upper)||out.lower>out.upper)throw std::runtime_error("round162_G_interval");
    const std::regex physical("(?:x_[0-9]+_[0-9]+_[0-9]+|(?:p|d|z|mode|load|ord)_[0-9]+_[0-9]+|conn_[0-9]+_[0-9]+_[0-9]+|Y_[0-9]+|state_[0-9]+_[0-9]+)");
    const std::regex auxiliary("(?:G|W_SP|r_min|r_max|(?:r|e|zprod)_[0-9]+|h_[0-9]+_[0-9]+|state_g_[0-9]+_[0-9]+)");
    std::vector<bool> phys(a.names.size());std::vector<int> columns,rows;
    std::ofstream cr(dir/"Q_columns.jsonl"),rr(dir/"Q_rows.jsonl");
    for(size_t j=0;j<a.names.size();++j){const auto& n=a.names[j];phys[j]=std::regex_match(n,physical);
        if(!phys[j]&&!std::regex_match(n,auxiliary))throw std::runtime_error("round162_unknown_column:"+n);
        if(phys[j]){if(!std::isfinite(a.lb[j])||!std::isfinite(a.ub[j])||std::fabs(a.lb[j])>=GRB_INFINITY||std::fabs(a.ub[j])>=GRB_INFINITY)throw std::runtime_error("round162_unbounded_Q:"+n);
            columns.push_back(int(j));cr<<"{\"column\":"<<q(n)<<",\"original_index\":"<<j<<"}\n";}}
    bool stock_lo=false,stock_hi=false;long long B=0,cap=0;for(int i=1;i<=in.V;++i)B+=in.initial[i];for(int x:in.Q)cap+=x;
    const double floor=double(std::max(0LL,B-cap));
    for(size_t i=0;i<a.rows.size();++i){bool pure=true;for(int k=a.start[i];k<a.start[i+1];++k)if(!phys[a.index[k]])pure=false;
        rr<<"{\"row\":"<<q(a.rows[i])<<",\"in_Q\":"<<(pure?"true":"false")<<"}\n";
        if(pure){rows.push_back(int(i));auto t=terms(a,i);bool total=t.size()==size_t(in.V);for(int v=1;v<=in.V&&total;++v)total=t.count("Y_"+std::to_string(v))&&t.at("Y_"+std::to_string(v))==1;
            stock_lo=stock_lo||(total&&a.sense[i]=='>'&&(a.rhs[i]==floor||a.rhs[i]==double(B-cap)));
            stock_hi=stock_hi||(total&&a.sense[i]=='<'&&a.rhs[i]==B);}}
    for(int v=1;v<=in.V;++v)if(a.lb.at(js.at("Y_"+std::to_string(v)))<0)throw std::runtime_error("round162_negative_inventory_bound");
    if(!stock_lo||!stock_hi)throw std::runtime_error("round162_missing_original_total_stock_rows");
    out.physical_columns=int(columns.size());out.physical_rows=int(rows.size());
    std::set<int> time_rows;
    if(omit_endpoint_time){
        for(int vehicle=0;vehicle<in.M;++vehicle){Terms expected;
            for(int i=0;i<=in.V;++i)for(int j=0;j<=in.V;++j)if(i!=j&&std::fabs(in.dist[i][j])>1e-14)
                expected["x_"+std::to_string(vehicle)+"_"+std::to_string(i)+"_"+std::to_string(j)]=in.dist[i][j];
            const double handling=in.pickup_time+in.drop_time;
            if(std::fabs(handling)>1e-14)for(int i=1;i<=in.V;++i)expected["p_"+std::to_string(vehicle)+"_"+std::to_string(i)]=handling;
            int matches=0;
            for(int row:rows)if(a.sense[row]=='<'&&a.rhs[row]==in.total_time_limit&&terms(a,row)==expected){time_rows.insert(row);++matches;}
            if(matches!=1)throw std::runtime_error("round162_exact_time_family_not_unique");
        }
    }
    int scaled=0,added_rows=0;std::ofstream intended(dir/"new_rows_intended.jsonl");intended<<std::setprecision(17);
    auto add=[&](const std::string& name,Terms t,char sense,double rhs){
        double smallest=1;for(const auto& z:t)if(z.second)smallest=std::min(smallest,std::fabs(z.second));
        int exponent=0;while(std::ldexp(smallest,exponent)<1e-12)if(++exponent>=1023)throw std::runtime_error("round162_scale_overflow");
        if(exponent)++scaled;
        std::vector<int> index;std::vector<double> coef;
        for(auto& z:t)if(z.second){z.second=std::ldexp(z.second,exponent);if(!std::isfinite(z.second))throw std::runtime_error("round162_scaled_coefficient");index.push_back(js.at(z.first));coef.push_back(z.second);}
        rhs=std::ldexp(rhs,exponent);if(!std::isfinite(rhs))throw std::runtime_error("round162_scaled_rhs");
        ck(GRBaddconstr(m,int(index.size()),index.data(),coef.data(),sense,rhs,name.c_str()));++added_rows;
        intended<<"{\"name\":"<<q(name)<<",\"sense\":"<<q(std::string(1,sense))<<",\"rhs\":"<<rhs<<",\"terms\":{";bool first=true;
        for(const auto& z:t)if(z.second){if(!first)intended<<',';first=false;intended<<q(z.first)<<':'<<z.second;}
        intended<<"}}\n";
    };
    auto col=[&](const std::string& name,double l,double u){ck(GRBaddvar(m,0,nullptr,nullptr,0,l,u,GRB_CONTINUOUS,name.c_str()));};
    if(full){
        if(out.lower==out.upper){
            for(int j:columns){const auto& n=a.names[j];std::string product;
                if(n.rfind("state_",0)==0)product="state_g_"+n.substr(6);else if(n.rfind("Y_",0)==0)product="zprod_"+n.substr(2);
                if(!product.empty())add("pc162_fixed_"+n,{{product,1},{n,-out.lower}},'=',0);}
        }else{
            col("pc162_lambda_L",0,1);col("pc162_lambda_U",0,1);
            for(int j:columns)for(const auto& e:{"L","U"})col("pc162_"+std::string(e)+"_"+a.names[j],std::min(0.,a.lb[j]),std::max(0.,a.ub[j]));
            ck(GRBupdatemodel(m));js=ids(Matrix(m));
            add("pc162_lambda_sum",{{"pc162_lambda_L",1},{"pc162_lambda_U",1}},'=',1);
            add("pc162_G_link",{{"G",1},{"pc162_lambda_L",-out.lower},{"pc162_lambda_U",-out.upper}},'=',0);
            for(int j:columns){const auto& n=a.names[j];add("pc162_sum_"+n,{{n,1},{"pc162_L_"+n,-1},{"pc162_U_"+n,-1}},'=',0);
                for(const auto& e:{"L","U"}){std::string tag(e),xi="pc162_"+tag+"_"+n,lambda="pc162_lambda_"+tag;
                    add("pc162_lb"+tag+"_"+n,{{xi,1},{lambda,-a.lb[j]}},'>',0);
                    add("pc162_ub"+tag+"_"+n,{{xi,1},{lambda,-a.ub[j]}},'<',0);}
                std::string product;if(n.rfind("state_",0)==0)product="state_g_"+n.substr(6);else if(n.rfind("Y_",0)==0)product="zprod_"+n.substr(2);
                if(!product.empty()){if(!js.count(product))throw std::runtime_error("round162_missing_product:"+n);
                    add("pc162_product_"+n,{{product,1},{"pc162_L_"+n,-out.lower},{"pc162_U_"+n,-out.upper}},'=',0);}}
            for(int i:rows)if(!time_rows.count(i))for(const auto& e:{"L","U"}){std::string tag(e);Terms t;for(int k=a.start[i];k<a.start[i+1];++k)t["pc162_"+tag+"_"+a.names[a.index[k]]]=a.coef[k];
                t["pc162_lambda_"+tag]=-a.rhs[i];add("pc162_q"+tag+"_"+a.rows[i],t,a.sense[i],0);}
        }
    }
    ck(GRBupdatemodel(m));Matrix before(m);unchanged(a,before);
    exactLp(m,before,output);ck(GRBwrite(m,(dir/"model.mps").string().c_str()));
    Model loaded(output);Matrix actual(loaded.m);unchanged(before,actual);registry(actual,dir,"actual");
    out.sha256=fileSha256(output);out.row_signature=fileSha256(dir/"actual_rows.jsonl");
    std::ofstream f(dir/"block.json");f<<std::setprecision(17)<<std::boolalpha<<"{\"full\":"<<full<<",\"lower\":"<<out.lower<<",\"upper\":"<<out.upper
        <<",\"original_columns\":"<<out.original_columns<<",\"original_rows\":"<<out.original_rows<<",\"Q_columns\":"<<out.physical_columns<<",\"Q_rows\":"<<out.physical_rows
        <<",\"B\":"<<B<<",\"fleet_capacity\":"<<cap<<",\"stock_floor\":"<<floor<<",\"original_total_stock_rows\":true,\"old_block_exactly_unchanged\":true,\"loaded_new_rows_exact\":true,\"new_rows\":"<<added_rows<<",\"scaled_rows\":"<<scaled<<",\"omitted_endpoint_time_rows\":"<<time_rows.size()*2<<"}\n";
    return out;
}
SolverNeutralModelDomain round162Domain(const std::filesystem::path& path){Model m(path);Matrix a(m.m);return {a.names,a.lb,a.ub,a.type};}
std::vector<double> round162ExtendStart(const std::filesystem::path& path,const SolverNeutralModelDomain& domain,const std::vector<double>& x){
    Model m(path);Matrix a(m.m);std::map<std::string,double> values;for(size_t j=0;j<domain.names.size();++j)values.emplace(domain.names[j],x.at(j));
    auto js=ids(a);const double L=a.lb.at(js.at("G")),U=a.ub.at(js.at("G")),g=values.at("G");
    const double weight=U==L?0:(g-L)/(U-L);std::vector<double> out;
    for(const auto& n:a.names){double v=0;if(values.count(n))v=values.at(n);else if(n=="pc162_lambda_L")v=1-weight;else if(n=="pc162_lambda_U")v=weight;
        else if(n.rfind("pc162_L_",0)==0)v=(1-weight)*values.at(n.substr(8));else if(n.rfind("pc162_U_",0)==0)v=weight*values.at(n.substr(8));
        else throw std::runtime_error("round162_unknown_start_column:"+n);
        out.push_back(v);
    }
    return out;
}
double round162PointResidual(const std::filesystem::path& path,const std::vector<double>& x,bool types){
    Model m(path);Matrix a(m.m);if(x.size()!=a.names.size())throw std::runtime_error("round162_point_shape");double worst=0;
    for(size_t j=0;j<x.size();++j){if(!std::isfinite(x[j]))throw std::runtime_error("round162_nonfinite_point");worst=std::max({worst,a.lb[j]-x[j],x[j]-a.ub[j],!types||a.type[j]=='C'?0:std::fabs(x[j]-std::round(x[j]))});}
    for(size_t i=0;i<a.rows.size();++i){long double lhs=0;for(int k=a.start[i];k<a.start[i+1];++k)lhs+=static_cast<long double>(a.coef[k])*x[a.index[k]];
        double d=double(lhs-a.rhs[i]);worst=std::max(worst,a.sense[i]=='='?std::fabs(d):a.sense[i]=='<'?d:-d);}return worst;
}
void round162FixSavedPoint(const std::filesystem::path& path,const std::filesystem::path& point){
    Model m(path);Matrix a(m.m);auto js=ids(a);std::ifstream f(point);std::string name;double value;int count=0;
    while(f>>name>>value){if(name.rfind("pc162_",0)==0)throw std::runtime_error("round162_fixed_point_has_new_columns");int j=js.at(name);double c=1;
        const std::string row="pc162_saved_"+name;ck(GRBaddconstr(m.m,1,&j,&c,'=',value,row.c_str()));++count;}
    int originals=0;for(const auto& n:a.names)if(n.rfind("pc162_",0)!=0)++originals;
    if(!f.eof()||count!=originals)throw std::runtime_error("round162_fixed_point_incomplete");
    ck(GRBupdatemodel(m.m));exactLp(m.m,Matrix(m.m),path);ck(GRBwrite(m.m,(path.parent_path()/"model.mps").string().c_str()));
    Model loaded(path);registry(Matrix(loaded.m),path.parent_path(),"actual");
}
void saveRound162LpEvidence(const FixedIntervalMipOutcome& out,const std::filesystem::path& dir){
    if(!out.lp_primal_values_available)return;
    std::ofstream p(dir/"lp_values.tsv"),v(dir/"lp_variables.jsonl"),r(dir/"lp_duals.jsonl");
    p<<std::setprecision(17);v<<std::setprecision(17);r<<std::setprecision(17);
    for(const auto& e:out.lp_primal_dual_variable_evidence){p<<e.name<<'\t'<<e.primal_value<<'\n';
        v<<"{\"name\":"<<q(e.name)<<",\"value\":"<<e.primal_value<<",\"RC\":"<<e.reduced_cost<<",\"basis\":"<<e.variable_basis_status<<"}\n";}
    for(const auto& e:out.lp_primal_dual_constraint_evidence)r<<"{\"name\":"<<q(e.name)<<",\"dual\":"<<e.dual_multiplier<<",\"slack\":"<<e.slack<<",\"basis\":"<<e.constraint_basis_status<<"}\n";
    if(!p||!v||!r)throw std::runtime_error("round162_evidence_write");
}
Round162Artifact projectRound162Completion(const std::filesystem::path& baseline,const std::filesystem::path& source,
        const std::filesystem::path& duals,const std::filesystem::path& output,Round162Row* projected_row){
    Model base(baseline),full(source);Matrix b(base.m),a(full.m);unchanged(b,a);const auto dir=output.parent_path();
    registry(b,dir,"original");
    const auto indices=ids(a);std::map<std::string,double> pi;std::ifstream f(duals);std::string line;
    const std::regex pattern("\\{\"name\":\"([^\"]+)\",\"dual\":([^,]+),.*\\}");std::smatch match;
    while(std::getline(f,line)){if(!std::regex_match(line,match,pattern))throw std::runtime_error("round162_dual_syntax");
        double p=std::stod(match[2]);if(!std::isfinite(p)||!pi.emplace(match[1],p).second)throw std::runtime_error("round162_dual_value");}
    if(!f.eof()||pi.size()!=a.rows.size())throw std::runtime_error("round162_dual_incomplete");
    std::vector<bool> eliminate;for(const auto& n:a.names)eliminate.push_back(n.rfind("pc162_",0)==0);
    const auto source_sha=fileSha256(source);
    std::vector<ObjectiveResourceRow> rows;int repairs=0;std::ofstream weights(dir/"projection_multipliers.jsonl");weights<<std::setprecision(17);
    for(size_t i=0;i<a.rows.size();++i)if(a.rows[i].rfind("pc162_",0)==0){
        if(a.rows[i].rfind("pc162_saved_",0)==0)throw std::runtime_error("round162_fixed_source_for_projection");
        const double raw=pi.at(a.rows[i]);double p=raw;if(a.sense[i]=='<')p=std::min(0.,p);else if(a.sense[i]=='>')p=std::max(0.,p);else if(a.sense[i]!='=')throw std::runtime_error("round162_row_sense");
        repairs+=p!=raw;const double sign=p<0?1.:-1.;ObjectiveResourceRow row;row.scope=source_sha;row.vehicle=0;row.multiplier=std::fabs(p);row.rhs=sign*a.rhs[i];
        for(int k=a.start[i];k<a.start[i+1];++k){row.indices.push_back(a.index[k]);row.coefficients.push_back(sign*a.coef[k]);}
        if(p)weights<<"{\"row\":"<<q(a.rows[i])<<",\"raw\":"<<raw<<",\"used\":"<<p<<",\"normalization_sign\":"<<sign<<"}\n";
        rows.push_back(std::move(row));
    }
    if(rows.empty())throw std::runtime_error("round162_no_extension_rows");
    const auto projected=projectObjectiveResources(rows,a.lb,a.ub,eliminate);
    Terms cut;std::map<std::string,int> original=ids(b);std::vector<int> js;std::vector<double> cs;
    for(size_t k=0;k<projected.indices.size();++k){const auto& name=a.names.at(projected.indices[k]);
        if(eliminate.at(projected.indices[k])||!original.count(name))throw std::runtime_error("round162_projection_not_original");
        cut[name]=projected.coefficients[k];js.push_back(original.at(name));cs.push_back(projected.coefficients[k]);}
    const bool active=!cut.empty();if(!active&&projected.rhs<0)throw std::runtime_error("round162_empty_infeasible_projection");
    if(projected_row)*projected_row={cut,projected.rhs,active};
    if(active)ck(GRBaddconstr(base.m,int(js.size()),js.data(),cs.data(),'<',projected.rhs,"pc162_projected"));
    ck(GRBupdatemodel(base.m));Matrix intended(base.m);unchanged(b,intended);exactLp(base.m,intended,output);
    ck(GRBwrite(base.m,(dir/"model.mps").string().c_str()));Model loaded(output);Matrix actual(loaded.m);unchanged(intended,actual);registry(actual,dir,"actual");
    std::ofstream evidence(dir/"projection.json");evidence<<std::setprecision(17)<<std::boolalpha<<"{\"source_SHA256\":"<<q(fileSha256(source))<<",\"duals_SHA256\":"<<q(fileSha256(duals))
        <<",\"active\":"<<active<<",\"sign_repairs\":"<<repairs<<",\"extension_rows\":"<<rows.size()<<",\"nonzero_source_rows\":"<<projected.source_rows.size()<<",\"eliminated_columns\":"<<std::count(eliminate.begin(),eliminate.end(),true)
        <<",\"compensation_upper\":"<<projected.compensation_upper<<",\"row\":{\"name\":\"pc162_projected\",\"sense\":\"<\",\"rhs\":"<<projected.rhs<<",\"terms\":{";
    bool first=true;for(const auto& term:cut){if(!first)evidence<<',';first=false;evidence<<q(term.first)<<':'<<term.second;}evidence<<"}},\"original_physical_terms_retained\":true,\"new_columns_submitted\":0,\"loaded_row_exact\":true}\n";
    std::ofstream nr(dir/"new_rows_intended.jsonl");if(active){nr<<std::setprecision(17)<<"{\"name\":\"pc162_projected\",\"sense\":\"<\",\"rhs\":"<<projected.rhs<<",\"terms\":{";first=true;for(const auto& term:cut){if(!first)nr<<',';first=false;nr<<q(term.first)<<':'<<term.second;}nr<<"}}\n";}
    Round162Artifact result;result.sha256=fileSha256(output);result.row_signature=fileSha256(dir/"actual_rows.jsonl");return result;
}
Round162Artifact appendRound162Row(const std::filesystem::path& path,const std::filesystem::path& output,const Round162Row& row){
    Model model(path);Matrix before(model.m);auto index=ids(before);std::vector<int> js;std::vector<double> cs;
    if(!row.active)throw std::runtime_error("round162_append_inactive_row");
    for(const auto& term:row.coefficients){js.push_back(index.at(term.first));cs.push_back(term.second);}
    ck(GRBaddconstr(model.m,int(js.size()),js.data(),cs.data(),'<',row.rhs,"pc162_projected"));ck(GRBupdatemodel(model.m));
    Matrix intended(model.m);unchanged(before,intended);exactLp(model.m,intended,output);
    Model loaded(output);unchanged(intended,Matrix(loaded.m));
    Round162Artifact out;out.sha256=fileSha256(output);out.row_signature=out.sha256;return out;
}
}
