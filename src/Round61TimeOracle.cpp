#include "Round61TimeOracle.hpp"
#include "Evaluator.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <numeric>
#include <stdexcept>
#include <sstream>
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
#define NOMINMAX
#include <windows.h>
#include <gurobi_c.h>
#endif

namespace ebrp {
namespace {
using Clock=std::chrono::steady_clock;
double seconds(Clock::time_point t) { return std::chrono::duration<double>(Clock::now()-t).count(); }
std::string v(const char* prefix,int k,int i) { return std::string(prefix)+"_"+std::to_string(k)+"_"+std::to_string(i); }
std::string x(int k,int i,int j) { return v("x",k,i)+"_"+std::to_string(j); }
std::string y(int i) { return "Y_"+std::to_string(i); }
}

double round61SafeDurationBound(const Instance& in) {
    double largest=0;
    for(const auto& row:in.dist) for(double d:row) {
        if(!std::isfinite(d) || d<0) throw std::invalid_argument("nonnegative finite travel required");
        largest=std::max(largest,d);
    }
    if(in.pickup_time<0 || in.drop_time<0) throw std::invalid_argument("nonnegative handling required");
    // At most V+1 arcs per simple depot tour, and no station can supply more
    // than its original inventory (single nonzero one-direction service).
    const double b=std::accumulate(in.initial.begin()+1,in.initial.end(),0.0);
    return (in.V+1)*largest+(in.pickup_time+in.drop_time)*b;
}

void writeRound61TimeModel(const Instance& in,const Round61TimeRequest& r) {
    if(r.inventory.size()!=in.initial.size()) throw std::invalid_argument("fixed inventory dimensions");
    for(int i=1;i<=in.V;++i) if(r.inventory[i]<-1 || r.inventory[i]>in.capacity[i])
        throw std::invalid_argument("invalid fixed inventory");
    std::filesystem::create_directories(r.directory);
    std::ofstream f(r.directory/"time_oracle.lp"); f<<std::setprecision(17);
    f<<"Minimize\n obj: Tstar\nSubject To\n";
    int row=0;
    auto line=[&]() -> std::ofstream& { f<<" r"<<++row<<":"; return f; };
    std::vector<std::string> binaries,integers;
    std::ostringstream bounds; bounds<<std::setprecision(17);
    const double c=in.pickup_time+in.drop_time;
    const double safe=round61SafeDurationBound(in);
    bounds<<" 0 <= Tstar <= "<<safe<<'\n';
    auto shortest=in.dist;
    for(int h=0;h<=in.V;++h) for(int i=0;i<=in.V;++i) for(int j=0;j<=in.V;++j)
        shortest[i][j]=std::min(shortest[i][j],shortest[i][h]+shortest[h][j]);
    for(int i=1;i<=in.V;++i) {
        integers.push_back(y(i));
        bounds<<" "<<(r.inventory[i]<0?0:r.inventory[i])<<" <= "<<y(i)<<" <= "
              <<(r.inventory[i]<0?in.capacity[i]:r.inventory[i])<<'\n';
        line()<<" + "<<y(i);
        for(int k=0;k<in.M;++k) f<<" + "<<v("p",k,i)<<" - "<<v("d",k,i);
        f<<" = "<<in.initial[i]<<'\n';
        line(); for(int k=0;k<in.M;++k) f<<" + "<<v("z",k,i); f<<" <= 1\n";
    }
    for(int k=0;k<in.M;++k) {
        const int Q=in.Q[k], N=in.V;
        line(); for(int j=1;j<=N;++j) f<<" + "<<x(k,0,j); f<<" <= 1\n";
        line(); for(int j=1;j<=N;++j) f<<" + "<<x(k,0,j)<<" - "<<x(k,j,0); f<<" = 0\n";
        for(int i=0;i<=N;++i) for(int j=0;j<=N;++j) if(i!=j) binaries.push_back(x(k,i,j));
        for(int i=1;i<=N;++i) {
            const auto p=v("p",k,i),d=v("d",k,i),z=v("z",k,i),w=v("w",k,i),l=v("L",k,i),u=v("u",k,i);
            const int P=std::min(Q,r.inventory[i]<0?in.initial[i]:std::max(0,in.initial[i]-r.inventory[i]));
            const int D=std::min(Q,r.inventory[i]<0?in.capacity[i]-in.initial[i]:std::max(0,r.inventory[i]-in.initial[i]));
            binaries.push_back(z); binaries.push_back(w); integers.push_back(p); integers.push_back(d);
            bounds<<" 0 <= "<<p<<" <= "<<P<<"\n 0 <= "<<d<<" <= "<<D
                  <<"\n 0 <= "<<l<<" <= "<<Q<<"\n 0 <= "<<u<<" <= "<<N<<'\n';
            line()<<" + "<<p<<" - "<<P<<' '<<z<<" <= 0\n";
            line()<<" + "<<p<<" - "<<P<<' '<<w<<" <= 0\n";
            line()<<" + "<<d<<" - "<<D<<' '<<z<<" <= 0\n";
            line()<<" + "<<d<<" + "<<D<<' '<<w<<" <= "<<D<<'\n';
            line()<<" + "<<p<<" + "<<d<<" - "<<z<<" >= 0\n";
            line()<<" + "<<l<<" - "<<Q<<' '<<z<<" <= 0\n";
            line()<<" + "<<u<<" - "<<N<<' '<<z<<" <= 0\n";
            line()<<" + "<<u<<" - "<<z<<" >= 0\n";
            line()<<" - "<<z; for(int j=0;j<=N;++j) if(j!=i) f<<" + "<<x(k,i,j); f<<" = 0\n";
            line()<<" - "<<z; for(int j=0;j<=N;++j) if(j!=i) f<<" + "<<x(k,j,i); f<<" = 0\n";
            line()<<" + Tstar - "<<shortest[0][i]+shortest[i][0]<<' '<<z<<" - "<<c<<' '<<p<<" >= 0\n";
            for(int j=0;j<=N;++j) if(j!=i) {
                // Load equality at each visited successor, not at the return
                // depot; 2Q is safe for L_i-L_j+p_j-d_j in [-2Q,2Q].
                line()<<" + "<<l; if(j) f<<" - "<<v("L",k,j);
                f<<" - "<<p<<" + "<<d<<" + "<<2*Q<<' '<<x(k,j,i)<<" <= "<<2*Q<<'\n';
                line()<<" + "<<l; if(j) f<<" - "<<v("L",k,j);
                f<<" - "<<p<<" + "<<d<<" - "<<2*Q<<' '<<x(k,j,i)<<" >= "<<-2*Q<<'\n';
                line()<<" + "<<u; if(j) f<<" - "<<v("u",k,j);
                f<<" - "<<N+1<<' '<<x(k,j,i)<<" >= "<<-N<<'\n';
            }
        }
        line()<<" - Tstar";
        for(int i=0;i<=N;++i) for(int j=0;j<=N;++j) if(i!=j) f<<" + "<<in.dist[i][j]<<' '<<x(k,i,j);
        for(int i=1;i<=N;++i) f<<" + "<<c<<' '<<v("p",k,i);
        f<<" <= 0\n";
    }
    f<<"Bounds\n"<<bounds.str();
    if(r.lp) for(const auto& b:binaries) f<<" 0 <= "<<b<<" <= 1\n";
    else {
        f<<"Binaries\n"; for(const auto& b:binaries) f<<' '<<b<<'\n';
        f<<"Generals\n"; for(const auto& i:integers) f<<' '<<i<<'\n';
    }
    f<<"End\n";
    if(!f) throw std::runtime_error("time model write failure");
}

Round61NoGood round61InventoryNoGood(const Instance& in,const std::vector<int>& inventory) {
    if(inventory.size()!=in.initial.size()) throw std::invalid_argument("no-good dimensions");
    Round61NoGood out;
    for(int i=1;i<=in.V;++i) if(inventory[i]>=0) {
        if(inventory[i]>in.capacity[i]) throw std::invalid_argument("no-good inventory");
        for(int h=0; (1LL<<h)<=in.capacity[i]; ++h) {
            bool bit=((inventory[i]>>h)&1)!=0;
            out.names.push_back("bit_"+std::to_string(i)+"_"+std::to_string(h));
            out.coefficients.push_back(bit?-1:1); if(bit) --out.rhs;
        }
    }
    return out;
}

Round61TimeResult solveRound61TimeOracle(const Instance& in,double lambda,const Round61TimeRequest& r) {
    const auto start=Clock::now(); Round61TimeResult out;
    out.safe_duration_bound=round61SafeDurationBound(in);
    writeRound61TimeModel(in,r);
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
    const auto dll_name=L"gurobi"+std::to_wstring(GRB_VERSION_MAJOR)+
        std::to_wstring(GRB_VERSION_MINOR)+L".dll";
    HMODULE dll=LoadLibraryW(dll_name.c_str());
    if(!dll) throw std::runtime_error("cannot load installed Gurobi 13 DLL");
    GRBenv* env=nullptr; GRBmodel* model=nullptr;
#define API(name) auto name=reinterpret_cast<decltype(&GRB##name)>(GetProcAddress(dll,"GRB" #name)); if(!name) throw std::runtime_error("Gurobi symbol " #name)
    API(emptyenvinternal); API(startenv); API(freeenv); API(readmodel); API(freemodel);
    API(setintparam); API(setdblparam); API(setstrparam); API(getintparam); API(getdblparam);
    API(optimize); API(getintattr); API(getdblattr); API(getdblattrarray); API(getstrattrelement); API(getenv);
#undef API
    auto check=[](int code) { if(code) throw std::runtime_error("Gurobi oracle error "+std::to_string(code)); };
    try {
        check(emptyenvinternal(&env,GRB_VERSION_MAJOR,GRB_VERSION_MINOR,GRB_VERSION_TECHNICAL));
        check(setintparam(env,"OutputFlag",0));
        check(setstrparam(env,"LogFile",(r.directory/"native.log").string().c_str()));
        check(startenv(env));
        check(readmodel(env,(r.directory/"time_oracle.lp").string().c_str(),&model));
        GRBenv* me=getenv(model);
        for(auto p: {std::pair<const char*,int>{"Threads",1},{"Seed",0},{"Presolve",-1},{"DualReductions",0}})
            check(setintparam(me,p.first,p.second));
        check(setdblparam(me,"MIPGap",0)); check(setdblparam(me,"MIPGapAbs",0));
        const double remaining=r.process_cap_seconds-seconds(start)-2;
        if(remaining<=0) throw std::runtime_error("oracle cap exhausted before optimize");
        check(setdblparam(me,"TimeLimit",remaining));
        int th=0,se=0,pre=0; double ga=1,ab=1;
        check(getintparam(me,"Threads",&th));check(getintparam(me,"Seed",&se));check(getintparam(me,"Presolve",&pre));
        check(getdblparam(me,"MIPGap",&ga));check(getdblparam(me,"MIPGapAbs",&ab));
        out.parameters_verified=th==1 && se==0 && pre==-1 && ga==0 && ab==0;
        if(!out.parameters_verified) throw std::runtime_error("oracle parameter readback mismatch");
        check(optimize(model)); check(getintattr(model,"Status",&out.status));
        getdblattr(model,"Runtime",&out.solver_seconds); getdblattr(model,"Work",&out.work);
        double constraint_violation=0, bound_violation=0, dual_violation=0;
        bool primal_quality=getdblattr(model,"ConstrVio",&constraint_violation)==0 &&
            getdblattr(model,"BoundVio",&bound_violation)==0;
        bool dual_quality=!r.lp || getdblattr(model,"DualVio",&dual_violation)==0;
        const bool numeric_ok=primal_quality && dual_quality && constraint_violation<=1e-5 &&
            bound_violation<=1e-5 && dual_violation<=1e-5;
        std::ofstream quality(r.directory/"numerical_quality.json"); quality<<std::setprecision(17)
            <<"{\"primal_quality_available\":"<<primal_quality<<",\"dual_quality_available\":"<<dual_quality
            <<",\"constraint_violation\":"<<constraint_violation<<",\"bound_violation\":"<<bound_violation
            <<",\"dual_violation\":"<<dual_violation<<",\"numeric_ok\":"<<numeric_ok<<"}\n";
        out.time_independent_infeasible=out.status==GRB_INFEASIBLE;
        if(r.lp && out.status==GRB_OPTIMAL) out.lower_available=getdblattr(model,"ObjVal",&out.lower)==0;
        if(!r.lp && (out.status==GRB_OPTIMAL || out.status==GRB_TIME_LIMIT || out.status==GRB_INTERRUPTED))
            out.lower_available=getdblattr(model,"ObjBound",&out.lower)==0 && std::isfinite(out.lower) && std::abs(out.lower)<GRB_INFINITY;
        int solcount=0; check(getintattr(model,"SolCount",&solcount));
        if((out.status==GRB_OPTIMAL && !numeric_ok) || out.status==GRB_NUMERIC)
            out.lower_available=false;
        if(!r.lp && solcount>0) {
            int n=0; check(getintattr(model,"NumVars",&n)); std::vector<double> values(n);
            check(getdblattrarray(model,"X",0,n,values.data())); std::map<std::string,double> vars;
            for(int i=0;i<n;++i) { char* name=nullptr; check(getstrattrelement(model,"VarName",i,&name)); vars[name]=values[i]; }
            std::vector<RoutePlan> routes;
            for(int k=0;k<in.M;++k) {
                RoutePlan route; route.vehicle=k; route.nodes={0}; int current=0;
                for(int s=0;s<=in.V;++s) {
                    int next=-1;
                    for(int j=0;j<=in.V;++j) if(j!=current && vars[x(k,current,j)]>.5) {
                        if(next>=0) throw std::runtime_error("multiple oracle successor arcs"); next=j;
                    }
                    if(next<0 && current==0 && s==0) break;
                    if(next<0) throw std::runtime_error("missing oracle successor");
                    route.nodes.push_back(next); if(!next) break;
                    auto integral=[&](const std::string& name) {
                        double value=vars[name]; if(std::abs(value-std::round(value))>1e-5) throw std::runtime_error("nonintegral oracle service");
                        return int(std::llround(value));
                    };
                    route.operations.push_back({next,integral(v("p",k,next)),integral(v("d",k,next))}); current=next;
                }
                if(!route.operations.empty()) routes.push_back(route);
            }
            Instance relaxed=in; relaxed.total_time_limit=out.safe_duration_bound;
            VerifiedCandidateStore store; store.consider(relaxed,lambda,routes,"time_oracle_witness","fixed_inventory_time_diagnostic");
            if(!store.hasBest()) throw std::runtime_error("oracle route independent verification failed");
            for(int i=1;i<=in.V;++i) if(r.inventory[i]>=0 && store.best().final_inventory[i]!=r.inventory[i])
                throw std::runtime_error("oracle fixed inventory mismatch");
            out.witness=store.best(); auto verified=verifySolution(relaxed,routes,lambda);
            for(double d:verified.route_duration) out.upper=std::max(out.upper,d);
            out.upper_verified=true;
            writeRound61Witness(r.directory/"route_witness.json",relaxed,lambda,out.witness);
        }
        if(out.time_independent_infeasible) out.classification=r.lp?"LP_infeasible_time_independent":"MIP_infeasible_time_independent";
        else if(out.upper_verified && out.upper<=in.total_time_limit+1e-7) out.classification="original_T_feasible";
        else if(out.lower_available && out.lower>in.total_time_limit+1e-5*std::max(1.0,in.total_time_limit)) out.classification="original_T_strictly_infeasible";
        else out.classification=out.status==GRB_NUMERIC?"numerical_failure":"unknown";
        freemodel(model);model=nullptr;freeenv(env);env=nullptr;FreeLibrary(dll);
    } catch(...) { if(model) freemodel(model); if(env) freeenv(env); FreeLibrary(dll); throw; }
#else
    (void)lambda;
    throw std::runtime_error("time oracle requires configured Windows Gurobi backend");
#endif
    out.seconds=seconds(start);
    std::ofstream f(r.directory/"oracle_result.json"); f<<std::setprecision(17)
        <<"{\"classification\":\""<<out.classification<<"\",\"status\":"<<out.status
        <<",\"LP\":"<<r.lp<<",\"T_original\":"<<in.total_time_limit
        <<",\"safe_duration_bound\":"<<out.safe_duration_bound<<",\"lower\":";
    if(out.lower_available) f<<out.lower; else f<<"null";
    f<<",\"upper\":"; if(out.upper_verified) f<<out.upper; else f<<"null";
    f<<",\"time_independent_infeasible\":"<<out.time_independent_infeasible
     <<",\"parameters_verified\":"<<out.parameters_verified<<",\"seconds\":"<<out.seconds
     <<",\"solver_seconds\":"<<out.solver_seconds<<",\"work\":"<<out.work<<"}\n";
    return out;
}
}
