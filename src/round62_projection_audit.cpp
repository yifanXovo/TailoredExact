// Bounded diagnostic only: optimize row activity over a frozen OFF LP.
// Does not change a formal solver model or generate performance candidates.
#include "Parser.hpp"
#include "Round62Thresholds.hpp"
#include "FileSha256.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <vector>
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
#define NOMINMAX
#include <windows.h>
#include <gurobi_c.h>
#endif

int main(int argc, char** argv) {
    try {
        const auto start=std::chrono::steady_clock::now();
        auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();};
        std::string input, model_path, expected_sha, output;
        double T=3600,pickup=60,drop=60,cap=120;
        for(int i=1;i<argc;++i) {
            std::string a=argv[i];
            auto value=[&](){if(++i>=argc)throw std::runtime_error("missing argument");return std::string(argv[i]);};
            if(a=="--input")input=value();else if(a=="--model")model_path=value();
            else if(a=="--expected-model-sha256")expected_sha=value();
            else if(a=="--out")output=value();else if(a=="--T")T=std::stod(value());
            else if(a=="--pickup-time")pickup=std::stod(value());else if(a=="--drop-time")drop=std::stod(value());
            else if(a=="--cap")cap=std::stod(value());else throw std::runtime_error("unknown argument "+a);
        }
        if(input.empty()||model_path.empty()||output.empty()||cap<=0||cap>300)
            throw std::runtime_error("invalid bounded LP audit request");
        if(expected_sha.empty()||ebrp::fileSha256(model_path)!=expected_sha)
            throw std::runtime_error("LP audit requires the frozen source-model SHA-256");
        const auto in=ebrp::parseInstanceFile(input,T,pickup,drop);
        const auto proof=ebrp::generateRound62Thresholds(in);
        const auto rows=ebrp::round62ThresholdRows(in,proof,"projection");
        const auto service_rows=ebrp::round62ThresholdRows(in,proof,"projection-service");
        const std::filesystem::path dir(output);std::filesystem::create_directories(dir);
        ebrp::writeRound62ThresholdProof(in,proof,rows,dir/"projection.round62.json");
        ebrp::writeRound62ThresholdProof(in,proof,service_rows,dir/"service_projection.round62.json");
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
        const auto name=L"gurobi"+std::to_wstring(GRB_VERSION_MAJOR)+std::to_wstring(GRB_VERSION_MINOR)+L".dll";
        HMODULE dll=LoadLibraryW(name.c_str());if(!dll)throw std::runtime_error("installed Gurobi unavailable");
        GRBenv* env=nullptr;GRBmodel* model=nullptr;
#define API(n) auto n=reinterpret_cast<decltype(&GRB##n)>(GetProcAddress(dll,"GRB" #n));if(!n)throw std::runtime_error("missing Gurobi symbol " #n)
        API(emptyenvinternal);API(startenv);API(freeenv);API(readmodel);API(freemodel);API(getenv);
        API(setintparam);API(setdblparam);API(setstrparam);API(getintparam);API(getdblparam);
        API(getintattr);API(getdblattr);API(getstrattrelement);API(getdblattrarray);API(getcharattrarray);
        API(setintattr);API(setdblattr);API(setdblattrarray);API(setcharattrarray);API(optimize);
        API(addconstr);
#undef API
        auto check=[](int code){if(code)throw std::runtime_error("Gurobi LP audit code "+std::to_string(code));};
        try {
            check(emptyenvinternal(&env,GRB_VERSION_MAJOR,GRB_VERSION_MINOR,GRB_VERSION_TECHNICAL));
            check(setintparam(env,"LogToConsole",0));check(startenv(env));
            check(readmodel(env,model_path.c_str(),&model));auto me=getenv(model);
            bool parameters=true;
            for(auto p:{std::pair<const char*,int>{"Threads",1},{"Seed",0},{"Presolve",-1}}) {
                check(setintparam(me,p.first,p.second));int value=0;check(getintparam(me,p.first,&value));parameters=parameters&&value==p.second;
            }
            for(const char* p:{"MIPGap","MIPGapAbs"}) {
                check(setdblparam(me,p,0));double value=1;check(getdblparam(me,p,&value));parameters=parameters&&value==0;
            }
            if(!parameters)throw std::runtime_error("LP audit parameter readback mismatch");
            int count=0;check(getintattr(model,"NumVars",&count));
            std::vector<char> original_types(count);
            std::vector<double> lower(count),upper(count),original_objective(count);
            check(getdblattrarray(model,"Obj",0,count,original_objective.data()));
            check(getcharattrarray(model,"VType",0,count,original_types.data()));
            check(getdblattrarray(model,"LB",0,count,lower.data()));check(getdblattrarray(model,"UB",0,count,upper.data()));
            for(int i=0;i<count;++i)if(original_types[i]==GRB_BINARY) {
                lower[i]=std::max(0.0,lower[i]);upper[i]=std::min(1.0,upper[i]);
            }
            std::vector<char> types(count,GRB_CONTINUOUS);check(setcharattrarray(model,"VType",0,count,types.data()));
            check(setdblattrarray(model,"LB",0,count,lower.data()));check(setdblattrarray(model,"UB",0,count,upper.data()));
            check(setintattr(model,"ModelSense",GRB_MINIMIZE));check(setdblattr(model,"ObjCon",0));
            std::map<std::string,int> index;std::vector<std::string> names(count);
            for(int i=0;i<count;++i){char* n=nullptr;check(getstrattrelement(model,"VarName",i,&n));names[i]=n;index[n]=i;}
            std::ofstream ledger(dir/"queries.csv");ledger<<std::setprecision(17)
                <<"query,row,native_status,valid_optimal,minimum_activity,rhs,violation,work,solver_seconds,constraint_violation,bound_violation,dual_violation\n";
            std::ofstream launches(dir/"native_calls.csv");launches<<"query,row,remaining_seconds\n";
            int calls=0,valid=0,separated=0;double best=-1e100,total_work=0;std::string best_row;
            bool service_optimal=false;double service_objective=0,service_work=0,service_runtime=0;
            std::vector<double> best_point;
            const std::size_t limit=std::min<std::size_t>(32,rows.size());
            for(std::size_t j=0;j<limit;++j) {
                const double remaining=cap-elapsed()-2;if(remaining<=0)break;
                std::vector<double> objective(count,0);
                for(const auto& [n,c]:rows[j].coefficients)objective.at(index.at(n))=c;
                check(setdblattrarray(model,"Obj",0,count,objective.data()));
                check(setstrparam(me,"LogFile",(dir/("query_"+std::to_string(j)+".log")).string().c_str()));
                check(setdblparam(me,"TimeLimit",remaining));
                launches<<j<<','<<rows[j].name<<','<<remaining<<'\n';launches.flush();
                ++calls;check(optimize(model));int status=0;check(getintattr(model,"Status",&status));
                double activity=0,work=0,runtime=0,cv=0,bv=0,dv=0;
                check(getdblattr(model,"Work",&work));check(getdblattr(model,"Runtime",&runtime));total_work+=work;
                const bool good=status==GRB_OPTIMAL && getdblattr(model,"ObjVal",&activity)==0 && std::isfinite(activity) &&
                    getdblattr(model,"ConstrVio",&cv)==0 && getdblattr(model,"BoundVio",&bv)==0 &&
                    getdblattr(model,"DualVio",&dv)==0 && cv<=1e-5 && bv<=1e-5 && dv<=1e-5;
                const double violation=rows[j].rhs-activity;
                if(good) {
                    ++valid;separated+=violation>1e-7;
                    if(violation>best) {
                        best=violation;best_row=rows[j].name;best_point.resize(count);
                        check(getdblattrarray(model,"X",0,count,best_point.data()));
                    }
                }
                ledger<<j<<','<<rows[j].name<<','<<status<<','<<good<<',';
                if(good)ledger<<activity;
                ledger<<','<<rows[j].rhs<<',';
                if(good)ledger<<violation;
                ledger<<','<<work<<','<<runtime<<','<<cv<<','<<bv<<','<<dv<<'\n';ledger.flush();
            }
            // One extra, predeclared query restores the original F objective
            // and adds only the service projection. Total query cap is 33.
            const double remaining=cap-elapsed()-2;
            if(remaining>0) {
                for(const auto& row:service_rows) {
                    std::vector<int> indices;std::vector<double> coefficients;
                    for(const auto& [n,c]:row.coefficients){indices.push_back(index.at(n));coefficients.push_back(c);}
                    check(addconstr(model,static_cast<int>(indices.size()),indices.data(),coefficients.data(),GRB_GREATER_EQUAL,row.rhs,row.name.c_str()));
                }
                check(setdblattrarray(model,"Obj",0,count,original_objective.data()));
                check(setstrparam(me,"LogFile",(dir/"service_projection_lp.log").string().c_str()));
                check(setdblparam(me,"TimeLimit",remaining));
                launches<<32<<",service_projection_objective,"<<remaining<<'\n';launches.flush();
                ++calls;check(optimize(model));int status=0;check(getintattr(model,"Status",&status));
                check(getdblattr(model,"Work",&service_work));check(getdblattr(model,"Runtime",&service_runtime));total_work+=service_work;
                double cv=0,bv=0,dv=0;
                service_optimal=status==GRB_OPTIMAL && getdblattr(model,"ObjVal",&service_objective)==0 && std::isfinite(service_objective) &&
                    getdblattr(model,"ConstrVio",&cv)==0 && getdblattr(model,"BoundVio",&bv)==0 && getdblattr(model,"DualVio",&dv)==0 &&
                    cv<=1e-5 && bv<=1e-5 && dv<=1e-5;
                ledger<<32<<",service_projection_objective,"<<status<<','<<service_optimal<<',';
                if(service_optimal)ledger<<service_objective;
                ledger<<",,,"<<service_work<<','<<service_runtime<<','<<cv<<','<<bv<<','<<dv<<'\n';ledger.flush();
                if(service_optimal) {
                    std::vector<double> values(count);check(getdblattrarray(model,"X",0,count,values.data()));
                    std::ofstream point(dir/"service_projection_optimum.csv");point<<std::setprecision(17)<<"variable,value\n";
                    for(int i=0;i<count;++i)point<<names[i]<<','<<values[i]<<'\n';
                }
            }
            if(!best_point.empty()) {
                std::ofstream point(dir/"maximum_violation_point.csv");point<<std::setprecision(17)<<"variable,value\n";
                for(int i=0;i<count;++i)point<<names[i]<<','<<best_point[i]<<'\n';
            }
            freemodel(model);model=nullptr;freeenv(env);env=nullptr;FreeLibrary(dll);
            std::ofstream result(dir/"audit_result.json");result<<std::setprecision(17)
                <<"{\"source_model_sha256\":\""<<expected_sha<<"\",\"query_limit\":33,\"rows_available\":"<<rows.size()<<",\"optimizer_calls\":"<<calls
                <<",\"valid_optimal_queries\":"<<valid<<",\"strictly_separating_rows\":"<<separated
                <<",\"maximum_violation\":";if(valid)result<<best;else result<<"null";
            result<<",\"maximum_violation_row\":\""<<best_row<<"\",\"service_projection_LP_optimal\":"<<service_optimal<<",\"service_projection_LP_objective\":";
            if(service_optimal)result<<service_objective;else result<<"null";
            result<<",\"service_projection_LP_work\":"<<service_work<<",\"service_projection_LP_seconds\":"<<service_runtime
                <<",\"parameters_verified\":true,\"work\":"<<total_work<<",\"seconds\":"<<elapsed()<<"}\n";
            return 0;
        } catch(...) {if(model)freemodel(model);if(env)freeenv(env);FreeLibrary(dll);throw;}
#else
        (void)elapsed;
        throw std::runtime_error("LP audit requires configured Windows Gurobi backend");
#endif
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
