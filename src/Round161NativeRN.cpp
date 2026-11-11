#include "Round161NativeRN.hpp"
#include "Round143Research.hpp"
#include "FileSha256.hpp"
#include <gurobi_c.h>
#include <fstream>
#include <regex>
#include <set>
#include <numeric>

namespace ebrp {
namespace {
void ck(int rc) { if(rc) throw std::runtime_error("round161_native_api_"+std::to_string(rc)); }
struct Model {
    GRBenv* env=nullptr; GRBmodel* m=nullptr;
    explicit Model(const std::filesystem::path& p) {
        ck(GRBemptyenv(&env)); ck(GRBsetintparam(env,"OutputFlag",0)); ck(GRBstartenv(env));
        ck(GRBreadmodel(env,p.string().c_str(),&m));
    }
    ~Model(){if(m)GRBfreemodel(m);if(env)GRBfreeenv(env);}
};
struct Matrix {
    std::vector<std::string> names, rows;
    std::vector<double> lb,ub,obj,rhs,coef;
    std::vector<char> type,sense;
    std::vector<int> start,index;
    explicit Matrix(GRBmodel* m) {
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
std::string quoted(const std::string& s){std::ostringstream o;o<<std::quoted(s);return o.str();}
// The shared e budget implies a ratio-box fractional knapsack. All full-item
// costs and comparisons use checked exact dyadics. Only the final partial
// item needs division; its conversion/division/subtraction are outward.
std::pair<double,double> penaltyBounds(const Instance& in,const Matrix& a,
        const std::map<std::string,int>& indices,const std::vector<std::vector<int>>& ys,double cutoff) {
    using namespace round140_detail;
    int er=0,ea=0;std::vector<double> c(in.V+1),alpha(in.V+1);
    for(int i=1;i<=in.V;++i){c[i]=1./in.target[i];alpha[i]=a.obj.at(indices.at("e_"+std::to_string(i)));
        if(alpha[i]<0||!std::isfinite(alpha[i]))throw std::runtime_error("round161_penalty_sign");
        int e=0;std::frexp(c[i],&e);er=std::min(er,e-53);
        if(alpha[i]){std::frexp(alpha[i],&e);ea=std::min(ea,e-53);}}
    const Int one=units(1.,er);std::vector<Int> lo(in.V+1),hi(in.V+1),base(in.V+1),cost(in.V+1);
    Int sum=0,minimum_cost=0;
    for(int i=1;i<=in.V;++i){lo[i]=mul(units(c[i],er),ys[i].front());hi[i]=mul(units(c[i],er),ys[i].back());
        base[i]=std::min(std::max(one,lo[i]),hi[i]);cost[i]=units(alpha[i],ea);sum=add(sum,base[i]);
        Int delta=base[i]-one;if(delta<0)delta=-delta;minimum_cost=add(minimum_cost,mul(cost[i],delta));}
    Int budget=add(units(cutoff,er+ea),-minimum_cost);
    if(budget<0)throw std::runtime_error("round161_shared_penalty_box_infeasible");
    std::vector<int> order(in.V);std::iota(order.begin(),order.end(),1);
    std::sort(order.begin(),order.end(),[&](int i,int j){return cost[i]<cost[j]||(cost[i]==cost[j]&&i<j);});
    const auto extreme=[&](bool upper){Int remaining=budget,total=sum;
        for(int i:order){const Int room=upper?hi[i]-base[i]:base[i]-lo[i];const Int full=mul(cost[i],room);
            if(full<=remaining){remaining-=full;total=add(total,upper?room:-room);continue;}
            // Positive alpha is guaranteed when full > remaining >= 0.
            const double available=-down(-remaining,er+ea);
            const double partial=std::nextafter(available/alpha[i],std::numeric_limits<double>::infinity());
            const double value=upper?-down(-total,er):down(total,er);
            return std::nextafter(upper?value+partial:value-partial,upper?std::numeric_limits<double>::infinity():-std::numeric_limits<double>::infinity());
        }
        return upper?-down(-total,er):down(total,er);
    };
    return {extreme(false),extreme(true)};
}
void registry(GRBmodel* m,const std::filesystem::path& dir,const std::string& label) {
    Matrix a(m);std::ofstream c(dir/(label+"_columns.jsonl")),r(dir/(label+"_rows.jsonl"));
    c<<std::setprecision(17);r<<std::setprecision(17);
    for(size_t j=0;j<a.names.size();++j)c<<"{\"name\":"<<quoted(a.names[j])<<",\"lb\":"<<a.lb[j]<<",\"ub\":"<<a.ub[j]<<",\"obj\":"<<a.obj[j]<<",\"type\":\""<<a.type[j]<<"\"}\n";
    for(size_t i=0;i<a.rows.size();++i){r<<"{\"name\":"<<quoted(a.rows[i])<<",\"sense\":\""<<a.sense[i]<<"\",\"rhs\":"<<a.rhs[i]<<",\"terms\":{";
        for(int k=a.start[i];k<a.start[i+1];++k){if(k>a.start[i])r<<',';r<<quoted(a.names[a.index[k]])<<':'<<a.coef[k];}r<<"}}\n";}
    if(!c||!r)throw std::runtime_error("round161_registry_write");
}
void zeroBranch(round143_detail::Block& block,const std::vector<std::vector<int>>& supports,long long B,double gu) {
    block.columns["rn_z0"]={0,1};block.columns["rn_t"].first=0;
    std::set<std::string> states;for(size_t i=1;i<supports.size();++i)for(int y:supports[i])states.insert(round143_detail::state(int(i),y));
    for(auto& row:block.rows) {
        if(row.name.rfind("rn_lb_",0)==0){double stored=0;for(const auto& term:row.coefficients)if(states.count(term.first))stored=-term.second;row.coefficients["rn_z0"]=stored;}
        if(row.name=="rn_normalization")row.coefficients["rn_z0"]=row.rhs;
    }
    using R=round143_detail::Row;
    std::map<std::string,double> lo{{"rn_z0",1}},hi{{"rn_z0",double(B)}};
    for(size_t i=1;i<supports.size();++i){lo["Y_"+std::to_string(i)]=1;hi["Y_"+std::to_string(i)]=1;}
    block.rows.push_back(R{"rn_positive_stock",lo,'>',1});block.rows.push_back(R{"rn_zero_stock",hi,'<',double(B)});
    block.rows.push_back(R{"rn_t_positive",{{"rn_t",1},{"rn_z0",block.lt}},'>',block.lt});
    block.rows.push_back(R{"rn_t_zero",{{"rn_t",1},{"rn_z0",block.ut}},'<',block.ut});
    block.rows.push_back(R{"rn_G_zero",{{"G",1},{"rn_z0",gu}},'<',gu});
}
}
void qualifyRound161ScaledZeroKernel(const std::filesystem::path& output) {
    // An algebraic objective-block unit, not an admissible route input: the
    // project reader stores integer demands. No Native environment/Optimize.
    std::vector<std::vector<int>> supports{{},{0,1},{0,1}};std::vector<double> c{0,1e13,1e13};
    auto b=round143_detail::block(supports,c,1,1);zeroBranch(b,supports,1,.5);
    std::map<std::string,double> point{{"G",0},{"Y_1",0},{"Y_2",0},{"rn_z0",1}};
    for(const auto& col:b.columns)if(col.first!="rn_z0")point[col.first]=0;
    for(int i=1;i<=2;++i){point[round143_detail::state(i,0)]=1;point[round143_detail::state(i,1)]=0;}
    int scaled=0;for(const auto& row:b.rows){long double lhs=0;
        for(const auto& term:row.coefficients)lhs+=static_cast<long double>(term.second)*point.at(term.first);
        const long double residual=lhs-row.rhs;
        if(row.sense=='='?residual!=0:row.sense=='<'?residual>0:residual<0)throw std::runtime_error("round161_scaled_zero_kernel:"+row.name);
        if(row.name.rfind("rn_lb_",0)==0)for(const auto& term:row.coefficients)if(term.first.rfind("rn_w_",0)==0&&term.second>1)++scaled;
    }
    if(!scaled)throw std::runtime_error("round161_kernel_did_not_exercise_scaling");
    std::ofstream f(output);f<<"{\"PASS\":true,\"scaled_lower_rows\":"<<scaled<<",\"kernel_only\":true,\"route_input\":false,\"Native_Optimize\":0,\"integer_target_reader_unchanged\":true}\n";
    if(!f)throw std::runtime_error("round161_kernel_receipt_write");
}
Round161Artifact replaceRound161Objective(const Instance& in,const std::filesystem::path& old_lp,
        const std::filesystem::path& output,bool rn,double gu,bool penalty_envelope,double cutoff) {
    Model owner(old_lp);auto* m=owner.m;Matrix a(m);auto dir=output.parent_path();
    registry(m,dir,"original");
    std::map<std::string,int> indices;std::vector<std::vector<int>> supports(in.V+1);
    for(size_t j=0;j<a.names.size();++j)if(!indices.emplace(a.names[j],int(j)).second)throw std::runtime_error("round161_duplicate_column");
    // Strict selector grammar identifies legal states; the deleted set is then
    // generated by exact semantic names, never a broad deletion regex.
    const std::regex state("state_([0-9]+)_([0-9]+)");std::smatch match;std::set<std::string> products,inventory_names{"G","r_min","r_max"};
    for(const auto& name:a.names)if(std::regex_match(name,match,state)) {
        int i=std::stoi(match[1]),y=std::stoi(match[2]);
        if(i<1||i>in.V||a.type[indices.at(name)]!='B')throw std::runtime_error("round161_selector_type");
        products.insert("state_g_"+std::to_string(i)+"_"+std::to_string(y));inventory_names.insert(name);
        if(a.ub[indices.at(name)]>0)supports[i].push_back(y);
    }
    std::set<std::string> removed;long long B=0,Q=0;bool allzero=true;
    removed.insert(products.begin(),products.end());
    for(int i=1;i<=in.V;++i){auto& ys=supports[i];std::sort(ys.begin(),ys.end());if(ys.empty())throw std::runtime_error("round161_empty_support");
        allzero=allzero&&ys.front()==0;B+=in.initial[i];
        for(const auto& prefix:{"Y_","r_","e_"})inventory_names.insert(std::string(prefix)+std::to_string(i));
        removed.insert("zprod_"+std::to_string(i));
        for(int j=i+1;j<=in.V;++j)removed.insert("h_"+std::to_string(i)+"_"+std::to_string(j));
    }
    for(const auto& name:a.names)if(name.rfind("state_g_",0)==0&&!removed.count(name))throw std::runtime_error("round161_unregistered_old_product");
    if(indices.count("W_SP"))removed.insert("W_SP");
    for(const auto& name:removed)if(!indices.count(name))throw std::runtime_error("round161_missing_old_objective_column:"+name);
    // The original ratio coefficient must survive the inherited writer/reader
    // exactly. Otherwise this entry cannot promise the declared loaded-c map.
    for(int i=1;i<=in.V;++i){const auto r=indices.at("r_"+std::to_string(i)),y=indices.at("Y_"+std::to_string(i));bool found=false;
        for(size_t row=0;row<a.rows.size();++row)if(a.sense[row]=='='&&a.rhs[row]==0&&a.start[row+1]-a.start[row]==2){double rc=0,yc=0;
            for(int k=a.start[row];k<a.start[row+1];++k){if(a.index[k]==r)rc=a.coef[k];if(a.index[k]==y)yc=a.coef[k];}
            if(rc==1&&yc==-(1./in.target[i]))found=true;}
        if(!found)throw std::runtime_error("round161_original_ratio_coefficient_not_preserved");}
    for(int q:in.Q)Q+=q;
    Round161Artifact out;out.zero_possible=allzero&&B<=Q;out.zero_only=B==0;
    double box_sl=0,box_su=0,penalty_sl=0,penalty_su=0;
    std::vector<int> rows,cols;std::ofstream closure(dir/"replacement_registry.jsonl");
    for(size_t i=0;i<a.rows.size();++i){std::set<std::string> consumers;
        for(int k=a.start[i];k<a.start[i+1];++k)if(removed.count(a.names[a.index[k]]))consumers.insert(a.names[a.index[k]]);
        if(!consumers.empty()){
            for(int k=a.start[i];k<a.start[i+1];++k)if(!removed.count(a.names[a.index[k]])&&!inventory_names.count(a.names[a.index[k]]))
                throw std::runtime_error("round161_objective_consumer_has_physical_or_unknown_column:"+a.names[a.index[k]]);
            rows.push_back(int(i));closure<<"{\"row\":"<<quoted(a.rows[i])<<",\"old_objective_consumers\":[";bool first=true;
            for(const auto& s:consumers){if(!first)closure<<',';first=false;closure<<quoted(s);}closure<<"]}\n";}}
    for(const auto& s:removed){cols.push_back(indices.at(s));closure<<"{\"column\":"<<quoted(s)<<",\"reason\":\"replaced_old_objective_module\"}\n";}
    if(rn) {
        ck(GRBdelconstrs(m,int(rows.size()),rows.data()));ck(GRBdelvars(m,int(cols.size()),cols.data()));ck(GRBupdatemodel(m));
        std::vector<double> c(in.V+1);for(int i=1;i<=in.V;++i)c[i]=1./in.target[i];
        round143_detail::Block block;
        if(!out.zero_only)block=round143_detail::block(supports,c,std::max(1LL,B-Q),B);
        box_sl=block.sl;box_su=block.su;
        if(!out.zero_only && (block.infeasible||!block.applicable)) {
            if(!out.zero_possible)throw std::runtime_error("round161_no_positive_denominator");
            // An empty positive relaxation implies an all-zero physical domain.
            out.zero_only=true;
        }
        if(penalty_envelope&&!out.zero_only){auto p=penaltyBounds(in,a,indices,supports,cutoff);penalty_sl=p.first;penalty_su=p.second;
            block.sl=std::max(block.sl,p.first);block.su=std::min(block.su,p.second);
            if(!(block.sl>0&&block.su>=block.sl)){
                if(!out.zero_possible)throw std::runtime_error("round161_penalty_positive_domain_empty");out.zero_only=true;
            }
            if(!out.zero_only){
            block.lt=std::nextafter(1./block.su,-std::numeric_limits<double>::infinity());block.ut=std::nextafter(1./block.sl,std::numeric_limits<double>::infinity());
            block.columns["rn_t"]={block.lt,block.ut};
            for(int i=1;i<=in.V;++i){block.columns[round143_detail::Y(i)].second=supports[i].back()?std::nextafter(block.ut*supports[i].back(),std::numeric_limits<double>::infinity()):0;
                for(int y:supports[i])block.columns[round143_detail::w(i,y)].second=block.ut;}
            for(auto& row:block.rows)if(row.name.rfind("rn_lb_",0)==0||row.name.rfind("rn_ub_",0)==0){double factor=0;
                for(const auto& term:row.coefficients)if(term.first.rfind("rn_w_",0)==0)factor=term.second;
                for(auto& term:row.coefficients)if(inventory_names.count(term.first))term.second=-factor*(row.name.rfind("rn_lb_",0)==0?block.lt:block.ut);}
            }
        }
        if(out.zero_only) {
            int j=-1;double one=1;ck(GRBgetvarbyname(m,"G",&j));
            ck(GRBaddconstr(m,1,&j,&one,'=',0,"rn_zero_only_g"));
        } else {
            out.s_lower=block.sl;out.s_upper=block.su;out.t_lower=block.lt;out.t_upper=block.ut;
            if(out.zero_possible) {
                zeroBranch(block,supports,B,gu);
            }
            for(const auto& [name,b]:block.columns)ck(GRBaddvar(m,0,nullptr,nullptr,0,b.first,b.second,name=="rn_z0"?GRB_BINARY:GRB_CONTINUOUS,name.c_str()));
            ck(GRBupdatemodel(m));
            for(auto row:block.rows){std::vector<int> js;std::vector<double> vs;
                double smallest=1;for(const auto& term:row.coefficients)if(term.second)smallest=std::min(smallest,std::fabs(term.second));
                int scale=0;while(std::ldexp(smallest,scale)<1e-12)if(++scale>=1023)throw std::runtime_error("round161_zero_row_scale");
                for(auto& term:row.coefficients){term.second=std::ldexp(term.second,scale);if(!std::isfinite(term.second))throw std::runtime_error("round161_nonfinite_scaled_coefficient");}
                row.rhs=std::ldexp(row.rhs,scale);if(!std::isfinite(row.rhs))throw std::runtime_error("round161_nonfinite_scaled_rhs");
                for(const auto& [name,value]:row.coefficients)if(value){int j=-1;ck(GRBgetvarbyname(m,name.c_str(),&j));if(j<0)throw std::runtime_error("round161_missing_new_row_column");js.push_back(j);vs.push_back(value);}
                ck(GRBaddconstr(m,int(js.size()),js.data(),vs.data(),row.sense,row.rhs,row.name.c_str()));}
        }
        ck(GRBupdatemodel(m));
    }
    registry(m,dir,"actual");ck(GRBwrite(m,output.string().c_str()));ck(GRBwrite(m,(dir/"model.mps").string().c_str()));
    out.sha256=fileSha256(output);out.row_signature=fileSha256(dir/"actual_rows.jsonl");
    std::ofstream f(dir/"block.json");f<<std::setprecision(17)<<std::boolalpha<<"{\"RN\":"<<rn<<",\"B\":"<<B<<",\"fleet_capacity\":"<<Q
        <<",\"zero_possible\":"<<out.zero_possible<<",\"zero_only\":"<<out.zero_only<<",\"S_lower\":"<<out.s_lower<<",\"S_upper\":"<<out.s_upper
        <<",\"t_lower\":"<<out.t_lower<<",\"t_upper\":"<<out.t_upper<<",\"box_S_lower\":"<<box_sl<<",\"box_S_upper\":"<<box_su
        <<",\"penalty_envelope\":"<<penalty_envelope<<",\"penalty_S_lower\":"<<penalty_sl<<",\"penalty_S_upper\":"<<penalty_su
        <<",\"old_module_columns\":"<<cols.size()<<",\"old_module_rows\":"<<rows.size()<<",\"domain_sha256\":"<<quoted(fileSha256(dir/"actual_columns.jsonl"))
        <<",\"row_registry_sha256\":"<<quoted(out.row_signature)<<",\"sha256\":"<<quoted(out.sha256)<<"}\n";
    return out;
}
SolverNeutralModelDomain round161Domain(const std::filesystem::path& path) {
    Model m(path);Matrix a(m.m);return {a.names,a.lb,a.ub,a.type};
}
double round161StartResidual(const std::filesystem::path& path,const std::vector<double>& x) {
    Model m(path);Matrix a(m.m);if(x.size()!=a.names.size())throw std::runtime_error("round161_start_shape");double worst=0;
    for(size_t j=0;j<x.size();++j)worst=std::max({worst,a.lb[j]-x[j],x[j]-a.ub[j],a.type[j]=='C'?0:std::fabs(x[j]-std::round(x[j]))});
    for(size_t i=0;i<a.rows.size();++i){long double lhs=0;for(int k=a.start[i];k<a.start[i+1];++k)lhs+=static_cast<long double>(a.coef[k])*x[a.index[k]];
        double e=double(lhs-a.rhs[i]);worst=std::max(worst,a.sense[i]=='='?std::fabs(e):a.sense[i]=='<'?e:-e);}
    return worst;
}
}
