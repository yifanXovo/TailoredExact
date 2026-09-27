// Two auxiliary LPs, one shared physical cap; no optimizer in callbacks and
// no row submission. Export a finite-bound-corrected Farkas combination.
#include "Round64SharedResource.hpp"
#include "Parser.hpp"
#include "FileSha256.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <gurobi_c.h>
#endif
using namespace ebrp;
namespace {
struct Row {std::string name;std::map<std::string,double> a,b;bool equality=false;};
std::string arc(const char* p,int k,int i,int j){return std::string(p)+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(j);}
std::string node(const char* p,int k,int i){return std::string(p)+std::to_string(k)+"_"+std::to_string(i);}
long double dot(const std::map<std::string,double>& a,const std::map<std::string,double>& x) {
    long double v=0;for(const auto& [n,c]:a)v+=static_cast<long double>(c)*x.at(n);return v;
}
}
int main(int argc,char** argv) {
 try {
    const auto started=std::chrono::steady_clock::now();auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();};
    std::string input,pinpath,expected,expected_identity,output;double T=0,pickup=60,drop=60,cap=120;
    for(int i=1;i<argc;++i){std::string a=argv[i];auto value=[&](){if(++i>=argc)throw std::runtime_error("argument missing");return std::string(argv[i]);};
        if(a=="--input")input=value();else if(a=="--pins")pinpath=value();else if(a=="--expected-sha")expected=value();else if(a=="--expected-resource-identity")expected_identity=value();else if(a=="--out")output=value();
        else if(a=="--T")T=std::stod(value());else if(a=="--pickup-time")pickup=std::stod(value());else if(a=="--drop-time")drop=std::stod(value());else if(a=="--cap")cap=std::stod(value());
        else throw std::runtime_error("unknown argument "+a);}
    if(input.empty()||output.empty()||pinpath.empty()||expected.empty()||fileSha256(pinpath)!=expected||cap<=3||cap>300)
        throw std::runtime_error("bounded audit requires frozen pins and physical input");
    const auto in=parseInstanceFile(input,T,pickup,drop);const auto d=prepareRound63Time(in);
    if(expected_identity.empty()||d.identity!=expected_identity)throw std::runtime_error("projection physical identity mismatch");
    const std::filesystem::path dir(output);std::filesystem::create_directories(dir);writeRound63TimeData(d,dir/"resource.json");
    std::map<std::string,double> point;std::ifstream pinfile(pinpath);std::string line;std::getline(pinfile,line);
    while(std::getline(pinfile,line)){auto comma=line.find(',');if(comma==std::string::npos)throw std::runtime_error("pin CSV");point[line.substr(0,comma)]=std::stod(line.substr(comma+1));}
    std::filesystem::copy_file(pinpath,dir/"original_pins.csv");
    std::vector<Row> base,sharing;std::map<std::string,double> upper;
    for(int k=0;k<in.M;++k)for(int i=1;i<=in.V;++i) {
        Row qb{node("q_balance_",k,i),{},{{node("p_",k,i),1},{node("d_",k,i),-1}},true};
        Row ql{node("q_load_",k,i),{},{{node("load_",k,i),1}},true};
        Row fb{node("f_balance_",k,i),{},{{node("p_",k,i),d.handling}},true};
        Row b4{node("B4_",k,i),{},{{node("load_",k,i),-d.handling}},false};
        for(int j=0;j<=in.V;++j)if(i!=j) {
            auto q=arc("q_",k,i,j),f=arc("f_",k,i,j),x=arc("x_",k,i,j);upper[q]=in.Q[k];upper[f]=d.upper[i][j];
            qb.a[q]=1;ql.a[q]=1;fb.a[f]=1;b4.a[f]=-1;
            base.push_back({arc("q_cap_",k,i,j),{{q,1}},{{x,double(in.Q[k])}},false});
            base.push_back({arc("f_cap_",k,i,j),{{f,1}},{{x,d.upper[i][j]}},false});
            sharing.push_back({arc("shared_",k,i,j),{{q,d.handling},{f,-1}},{},false});
        }
        for(int h=1;h<=in.V;++h)if(h!=i){qb.a[arc("q_",k,h,i)]=-1;fb.a[arc("f_",k,h,i)]=-1;}
        for(int h=0;h<=in.V;++h)if(h!=i)fb.b[arc("x_",k,h,i)]+=d.travel[h][i];
        base.push_back(qb);base.push_back(ql);base.push_back(fb);base.push_back(b4);
    }
    auto persist=[&](const std::vector<Row>& rows,const std::string& mode) {
        std::ofstream lp(dir/(mode+".lp")),terms(dir/(mode+"_terms.csv"));lp<<std::setprecision(17)<<"Minimize\n obj: 0 "<<upper.begin()->first<<"\nSubject To\n";
        terms<<std::setprecision(17)<<"row,equality,side,variable,coefficient\n";
        for(const auto& row:rows){lp<<' '<<row.name<<':';for(const auto& [n,c]:row.a){if(c)lp<<(c>=0?" + ":" - ")<<std::fabs(c)<<' '<<n;terms<<row.name<<','<<row.equality<<",aux,"<<n<<','<<c<<'\n';}
            lp<<(row.equality?" = ":" <= ")<<double(dot(row.b,point))<<'\n';for(const auto& [n,c]:row.b)terms<<row.name<<','<<row.equality<<",original,"<<n<<','<<c<<'\n';}
        lp<<"Bounds\n";for(const auto& [n,u]:upper)lp<<" 0 <= "<<n<<" <= "<<u<<'\n';lp<<"End\n";
        if(!lp||!terms)throw std::runtime_error("audit matrix persistence");
    };
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
    const auto dllname=L"gurobi"+std::to_wstring(GRB_VERSION_MAJOR)+std::to_wstring(GRB_VERSION_MINOR)+L".dll";
    HMODULE dll=LoadLibraryW(dllname.c_str());if(!dll)throw std::runtime_error("Gurobi DLL unavailable");GRBenv* env=nullptr;GRBmodel* model=nullptr;
#define API(n) auto n=reinterpret_cast<decltype(&GRB##n)>(GetProcAddress(dll,"GRB" #n));if(!n)throw std::runtime_error("missing Gurobi symbol " #n)
    API(emptyenvinternal);API(startenv);API(freeenv);API(readmodel);API(freemodel);API(getenv);API(setintparam);API(setdblparam);API(setstrparam);
    API(getintparam);API(getdblparam);API(getintattr);API(getdblattr);API(getdblattrarray);API(getstrattrelement);API(optimize);
#undef API
    auto check=[](int code){if(code)throw std::runtime_error("Gurobi audit error "+std::to_string(code));};
    try {
        check(emptyenvinternal(&env,GRB_VERSION_MAJOR,GRB_VERSION_MINOR,GRB_VERSION_TECHNICAL));check(setintparam(env,"LogToConsole",0));check(startenv(env));
        std::ofstream calls(dir/"native_calls.csv"),summary(dir/"audit_queries.csv"),parameters(dir/"parameters.csv");
        calls<<"query,arm,remaining_seconds,model_sha256\n";summary<<std::setprecision(17)<<"arm,status,work,solver_seconds,proof,corrected_global_violation,seconds\n";parameters<<"arm,parameter,requested,actual\n";
        int count=0;bool certified=false;double rawproof=0,violation=0;
        for(const std::string mode:{"sep","joint"}) {
            auto rows=base;if(mode=="joint")rows.insert(rows.end(),sharing.begin(),sharing.end());persist(rows,mode);
            const auto path=dir/(mode+".lp");check(readmodel(env,path.string().c_str(),&model));auto me=getenv(model);
            for(auto p:{std::pair<const char*,int>{"Threads",1},{"Seed",0},{"Presolve",-1},{"DualReductions",0},{"InfUnbdInfo",1}}) {
                check(setintparam(me,p.first,p.second));int v=0;check(getintparam(me,p.first,&v));parameters<<mode<<','<<p.first<<','<<p.second<<','<<v<<'\n';if(v!=p.second)throw std::runtime_error("parameter mismatch");}
            for(const char* p:{"MIPGap","MIPGapAbs"}){check(setdblparam(me,p,0));double v=1;check(getdblparam(me,p,&v));parameters<<mode<<','<<p<<",0,"<<v<<'\n';if(v!=0)throw std::runtime_error("gap parameter mismatch");}
            const double remaining=cap-elapsed()-3;if(remaining<=0)throw std::runtime_error("audit cap exhausted");
            check(setdblparam(me,"TimeLimit",remaining));check(setstrparam(me,"LogFile",(dir/(mode+".log")).string().c_str()));
            calls<<count++<<','<<mode<<','<<remaining<<','<<fileSha256(path)<<'\n';calls.flush();check(optimize(model));int status=0;check(getintattr(model,"Status",&status));
            double work=0,runtime=0;check(getdblattr(model,"Work",&work));check(getdblattr(model,"Runtime",&runtime));
            if(status==GRB_OPTIMAL) {
                int n=0;check(getintattr(model,"NumVars",&n));std::vector<double>x(n);check(getdblattrarray(model,"X",0,n,x.data()));
                std::ofstream p(dir/(mode+"_point.csv"));p<<std::setprecision(17)<<"variable,value\n";
                for(int i=0;i<n;++i){char* name=nullptr;check(getstrattrelement(model,"VarName",i,&name));p<<name<<','<<x[i]<<'\n';}
            } else if(status==GRB_INFEASIBLE&&mode=="joint") {
                int n=0;check(getintattr(model,"NumConstrs",&n));std::vector<double> ray(n);check(getdblattrarray(model,"FarkasDual",0,n,ray.data()));check(getdblattr(model,"FarkasProof",&rawproof));
                double norm=0;for(double y:ray){if(!std::isfinite(y))throw std::runtime_error("nonfinite Farkas multiplier");norm=std::max(norm,std::fabs(y));}
                if(norm==0)throw std::runtime_error("empty Farkas ray");
                std::map<std::string,const Row*> lookup;for(const auto& r:rows)lookup[r.name]=&r;
                std::map<std::string,long double> columns,projected;long double raw_rhs=0;
                std::ofstream ys(dir/"dual.csv");ys<<std::setprecision(17)<<"row,raw_multiplier,normalized_multiplier,equality\n";
                for(int i=0;i<n;++i){char* name=nullptr;check(getstrattrelement(model,"ConstrName",i,&name));const auto& r=*lookup.at(name);
                    // Nonnegative inequality multipliers, with complete re-evaluation
                    // after projection; equality multipliers stay free.
                    double y=ray[i]/norm;if(!r.equality)y=std::max(0.0,y);ys<<name<<','<<ray[i]<<','<<y<<','<<r.equality<<'\n';
                    for(const auto& [z,a]:r.a)columns[z]+=static_cast<long double>(y)*a;
                    for(const auto& [v,b]:r.b)projected[v]+=static_cast<long double>(y)*b;
                    raw_rhs+=static_cast<long double>(y)*dot(r.b,point);
                }
                long double beta=0;std::ofstream cs(dir/"column_residuals.csv");cs<<std::setprecision(17)<<"variable,aggregate_coefficient,lower,upper,bound_contribution\n";
                for(const auto& [z,u]:upper){const long double a=columns[z],contribution=std::min(0.L,a*u);beta+=contribution;cs<<z<<','<<double(a)<<",0,"<<u<<','<<double(contribution)<<'\n';}
                std::ofstream cut(dir/"projection_row.csv");cut<<std::setprecision(17)<<"variable,coefficient\n";long double activity=0;
                for(const auto& [v,b]:projected){cut<<v<<','<<double(b)<<'\n';activity+=b*point.at(v);}
                if(std::fabs(double(activity-raw_rhs))>1e-9)throw std::runtime_error("dual affine RHS mismatch");
                violation=double(beta-activity);certified=violation>1e-7;
                std::ofstream proof(dir/"projection_certificate.json");proof<<std::setprecision(17)<<"{\"scope\":\"original_physical_global\",\"identity\":\""<<d.identity
                    <<"\",\"pins_sha256\":\""<<expected<<"\",\"sense\":\">=\",\"rhs\":"<<double(beta)<<",\"raw_activity\":"<<double(activity)
                    <<",\"violation\":"<<violation<<",\"native_FarkasProof\":"<<rawproof<<",\"normalization\":"<<norm<<",\"submitted\":false,\"numeric_combination_verified\":"<<certified<<"}\n";
            } else throw std::runtime_error("unqualified auxiliary status "+std::to_string(status));
            if(mode=="sep"&&status!=GRB_OPTIMAL)throw std::runtime_error("SEP auxiliary control failed");
            summary<<mode<<','<<status<<','<<work<<','<<runtime<<','<<rawproof<<','<<violation<<','<<elapsed()<<'\n';summary.flush();freemodel(model);model=nullptr;
        }
        std::ofstream r(dir/"audit_result.json");r<<std::setprecision(17)<<"{\"optimizer_calls\":"<<count<<",\"query_limit\":2,\"sep_feasible\":true,\"projection_certificate\":"<<certified
            <<",\"violation\":"<<violation<<",\"process_seconds\":"<<elapsed()<<"}\n";freeenv(env);env=nullptr;FreeLibrary(dll);
    } catch(...) {if(model)freemodel(model);if(env)freeenv(env);FreeLibrary(dll);throw;}
#else
    throw std::runtime_error("native Gurobi required");
#endif
    return 0;
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
