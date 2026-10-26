// Finite actual production-function tests. Real read-only Gurobi model;
// explicit fault-injected API responses, no native Optimize.
#include "../../../src/GurobiBaseline.cpp"
#include "Parser.hpp"
#include <iostream>
using namespace ebrp;
static GurobiApi real_api;
static std::string fault;
static int submissions=0;
static int hooked_set(GRBmodel* m,const char* a,int s,int n,double* v) {
    if(std::string(a)==GRB_DBL_ATTR_START) {
        ++submissions;if(fault=="submit_api_failure")return 777;
    }
    return real_api.setdblattrarray(m,a,s,n,v);
}
static int hooked_dbl(GRBmodel* m,const char* a,int s,int n,double* v) {
    if(fault=="readback_api_failure" && std::string(a)==GRB_DBL_ATTR_START)return 778;
    int rc=real_api.getdblattrarray(m,a,s,n,v);if(rc)return rc;
    if(fault=="bound_violation" && std::string(a)==GRB_DBL_ATTR_UB)for(int j=0;j<n;++j)v[j]=0;
    if(fault=="row_violation" && std::string(a)==GRB_DBL_ATTR_RHS)for(int j=0;j<n;++j)v[j]+=100000;
    if(std::string(a)==GRB_DBL_ATTR_START && n) {
        if(fault=="nonfinite_readback")v[0]=std::numeric_limits<double>::quiet_NaN();
        if(fault=="readback_mismatch")v[0]+=1;
    }
    return 0;
}
static int hooked_char(GRBmodel* m,const char* a,int s,int n,char* v) {
    int rc=real_api.getcharattrarray(m,a,s,n,v);if(rc)return rc;
    if(fault=="type_violation" && std::string(a)==GRB_CHAR_ATTR_VTYPE)for(int j=0;j<n;++j)v[j]='I';
    return 0;
}
static int hooked_name(GRBmodel* m,const char* a,int i,char** v) {
    int rc=real_api.getstrattrelement(m,a,i,v);if(rc)return rc;
    if(fault=="unsupported_column" && std::string(a)==GRB_STR_ATTR_VARNAME && i==0) {
        static char unknown[]="unsupported_round112_column";*v=unknown;
    }
    return 0;
}
static std::vector<RoutePlan> actual_h() {
    return {
        {0,{0,17,15,7,3,6,13,18,12,14,20,0},{{3,8,0},{20,0,10},{12,7,0},{14,0,3},{13,5,0},{18,0,7},{17,7,0},{7,0,7},{15,1,0},{6,0,1}}},
        {1,{0,5,2,11,8,10,16,9,0},{{16,7,0},{9,0,9},{8,4,0},{10,0,8},{2,4,0},{11,0,2},{5,4,0}}}
    };
}
int main(int argc,char** argv) {try {
    if(argc!=4)throw std::runtime_error("input original.lp output");
    const auto in=parseInstanceFile(argv[1],5100,60,60);
    SolveOptions opt;opt.lambda=.15;
    std::filesystem::path root,library;std::string why;
    if(!loadGurobiApi(opt,real_api,root,library,why))throw std::runtime_error(why);
    GurobiApi api=real_api;api.setdblattrarray=hooked_set;api.getdblattrarray=hooked_dbl;
    api.getcharattrarray=hooked_char;api.getstrattrelement=hooked_name;
    GRBenv* env=nullptr;
    if(real_api.emptyenvinternal(&env,GRB_VERSION_MAJOR,GRB_VERSION_MINOR,GRB_VERSION_TECHNICAL) ||
       real_api.setintparam(env,GRB_INT_PAR_OUTPUTFLAG,0) || real_api.startenv(env))throw std::runtime_error("environment");
    const std::filesystem::path out(argv[3]);std::filesystem::create_directories(out);
    std::ofstream summary(out/"cases.jsonl");int count=0;
    for(const std::string name:{"actual_heterogeneous_H","empty_vehicle_0","loaded_return","unsupported_column",
        "bound_violation","type_violation","row_violation","objective_mismatch","invalid_physical",
        "submit_api_failure","readback_api_failure","nonfinite_readback","readback_mismatch"}) {
        GRBmodel* model=nullptr;if(real_api.readmodel(env,argv[2],&model))throw std::runtime_error("readmodel");
        SolveResult seed;seed.routes=actual_h();
        if(name=="empty_vehicle_0")seed.routes.erase(seed.routes.begin());
        if(name=="loaded_return")seed.routes[0].operations[1].drop-=1;
        if(name=="invalid_physical")seed.routes[0].operations[0].pickup=100;
        const auto verified=verifySolution(in,seed.routes,opt.lambda);seed.objective=verified.objective;
        if(name=="objective_mismatch")seed.objective+=.01;
        fault=name;submissions=0;bool rejected=false;std::string reason;
        std::vector<double> values;std::vector<char> types;
        try {round112Submit(api,model,in,opt,seed,(out/name).string(),values,types);}
        catch(const std::exception& e){rejected=true;reason=e.what();}
        bool expected=name!="actual_heterogeneous_H" && name!="empty_vehicle_0" && name!="loaded_return";
        const bool passed=rejected==expected && (expected || submissions==1);
        summary<<"{\"case\":"<<std::quoted(name)<<",\"passed\":"<<(passed?"true":"false")
            <<",\"rejected\":"<<(rejected?"true":"false")<<",\"submission_API_calls\":"<<submissions
            <<",\"native_Optimize_calls\":0,\"fault_injected\":"<<(expected?"true":"false")
            <<",\"physical_valid_before_fault\":"<<(verified.feasible?"true":"false")
            <<",\"reason\":"<<std::quoted(reason)<<"}\n";summary.flush();
        real_api.freemodel(model);if(!passed)throw std::runtime_error("case failed:"+name+":"+reason);
        ++count;
    }
    real_api.freeenv(env);FreeLibrary(real_api.library);summary.close();
    std::cout<<count<<" production-path cases, zero Optimize\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
