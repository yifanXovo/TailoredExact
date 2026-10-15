// Exactly six predeclared complete-model LPs, in one serial process. Models
// come from the current arm's paid root/child LP export; no formal feedback.
#include "round120_qualification_support.hpp"
#include <array>

namespace {
struct Api {
    HMODULE dll=nullptr;
#define MEMBER(n) decltype(&GRB##n) n=nullptr
    MEMBER(emptyenvinternal);MEMBER(setintparam);MEMBER(setdblparam);MEMBER(startenv);MEMBER(readmodel);
    MEMBER(setcharattrarray);MEMBER(updatemodel);MEMBER(getintattr);MEMBER(getdblattr);MEMBER(getdblattrarray);
    MEMBER(setdblattrarray);MEMBER(setdblattr);MEMBER(setintattr);MEMBER(optimize);MEMBER(write);MEMBER(freemodel);MEMBER(freeenv);
#undef MEMBER
    Api(){dll=LoadLibraryW(L"gurobi130.dll");require(dll!=nullptr,"diagnostic DLL");
#define LOAD(n) n=reinterpret_cast<decltype(n)>(GetProcAddress(dll,"GRB" #n));require(n!=nullptr,"diagnostic API " #n)
        LOAD(emptyenvinternal);LOAD(setintparam);LOAD(setdblparam);LOAD(startenv);LOAD(readmodel);LOAD(setcharattrarray);
        LOAD(updatemodel);LOAD(getintattr);LOAD(getdblattr);LOAD(getdblattrarray);LOAD(setdblattrarray);LOAD(setdblattr);LOAD(setintattr);
        LOAD(optimize);LOAD(write);LOAD(freemodel);LOAD(freeenv);
#undef LOAD
    }
    ~Api(){if(dll)FreeLibrary(dll);}
};
void array(std::ostream& f,const std::vector<double>& values){f<<'[';for(std::size_t j=0;j<values.size();++j){if(j)f<<',';f<<values[j];}f<<']';}
void ints(std::ostream& f,const std::vector<int>& values){f<<'[';for(std::size_t j=0;j<values.size();++j){if(j)f<<',';f<<values[j];}f<<']';}
void one(Api& api,const std::filesystem::path& model_path,const std::filesystem::path& D1,
    double beta0,double beta1,bool violation,double cap,const std::filesystem::path& dir) {
    require(!std::filesystem::exists(dir),"LP diagnostic output exists");std::filesystem::create_directories(dir);
    const auto original=read_native(model_path),conditional=read_native(D1);
    require(original.domain.names==conditional.domain.names,"D0/D1 actual column order differs");
    GRBenv* env=nullptr;GRBmodel* model=nullptr;auto check=[](int rc){if(rc)throw std::runtime_error("diagnostic native API "+std::to_string(rc));};
    try {
        check(api.emptyenvinternal(&env,GRB_VERSION_MAJOR,GRB_VERSION_MINOR,GRB_VERSION_TECHNICAL));
        check(api.setintparam(env,"OutputFlag",0));check(api.setintparam(env,"Threads",1));check(api.setintparam(env,"Seed",0));
        check(api.setintparam(env,"Presolve",-1));check(api.setdblparam(env,"FeasibilityTol",1e-6));
        check(api.setdblparam(env,"OptimalityTol",1e-6));check(api.setdblparam(env,"IntFeasTol",1e-5));
        check(api.setdblparam(env,"MIPGap",0));check(api.setdblparam(env,"MIPGapAbs",0));check(api.setdblparam(env,"TimeLimit",cap));
        check(api.startenv(env));check(api.readmodel(env,model_path.string().c_str(),&model));
        const int n=int(original.domain.names.size());std::vector<char> types(n,'C');
        check(api.setcharattrarray(model,"VType",0,n,types.data()));
        const auto h=std::find(original.domain.names.begin(),original.domain.names.end(),"r120_h")-original.domain.names.begin();
        require(h<n,"diagnostic selector missing");
        if(violation) {
            std::vector<double> objective=original.objective;for(auto& c:objective)c=-c;
            objective[h]+=beta1-beta0;
            check(api.setdblattrarray(model,"Obj",0,n,objective.data()));
            check(api.setdblattr(model,"ObjCon",beta0-original.constant));check(api.setintattr(model,"ModelSense",-1));
        }
        check(api.updatemodel(model));check(api.write(model,(dir/"actual_complete_relaxation.mps").string().c_str()));
        {std::ofstream launch(dir/"optimize_launch.json");launch<<"{\"Optimize\":1,\"cap_seconds\":120,\"source_model_SHA\":"
            <<std::quoted(fileSha256(model_path))<<",\"complete_original_rows_retained\":true}\n";launch.close();require(bool(launch),"diagnostic pre-Optimize receipt");}
        const auto started=std::chrono::steady_clock::now();const int rc=api.optimize(model);
        const double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
        int status=0,solutions=0;double value=0,runtime=0,work=0;
        check(api.getintattr(model,"Status",&status));check(api.getintattr(model,"SolCount",&solutions));
        check(api.getdblattr(model,"Runtime",&runtime));check(api.getdblattr(model,"Work",&work));
        const bool primal=solutions>0;std::vector<double> x(primal?n:0);
        if(primal){check(api.getdblattrarray(model,"X",0,n,x.data()));check(api.getdblattr(model,"ObjVal",&value));}
        // Original full route/resource/inventory rows stay in every relaxation.
        double bound_violation=0,objective_error=0,actual_D1_violation=0,qualified_beta_violation=0;
        decltype(validateCandidateLinearResidual(original.linear,x,1e-7)) residual;
        if(primal) {
            residual=validateCandidateLinearResidual(original.linear,x,1e-7);
            for(int j=0;j<n;++j)bound_violation=std::max({bound_violation,original.domain.lower_bounds[j]-x[j],x[j]-original.domain.upper_bounds[j]});
            long double f=original.constant;for(int j=0;j<n;++j)f+=static_cast<long double>(original.objective[j])*x[j];
            const double expected=violation?beta0+(beta1-beta0)*x[h]-double(f):double(f);
            objective_error=std::fabs(expected-value);qualified_beta_violation=beta0+(beta1-beta0)*x[h]-double(f);
            const int last=int(conditional.linear.rhs.size())-1;long double activity=0;
            for(int z=conditional.linear.row_starts[last];z<conditional.linear.row_starts[last+1];++z)
                activity+=static_cast<long double>(conditional.linear.coefficients[z])*x[conditional.linear.column_indices[z]];
            actual_D1_violation=conditional.linear.rhs[last]-double(activity);
        }
        const bool qualified=rc==0&&status==GRB_OPTIMAL&&primal&&residual.valid&&bound_violation<=1e-7&&objective_error<=1e-7;
        std::ofstream record(dir/"record.json");record<<std::setprecision(17)
            <<"{\"Optimize\":1,\"return_code\":"<<rc<<",\"status\":"<<status<<",\"optimal\":"<<(status==GRB_OPTIMAL?"true":"false")
            <<",\"primal_available\":"<<(primal?"true":"false")<<",\"qualified\":"<<(qualified?"true":"false")
            <<",\"objective\":";
        if(primal)record<<value;else record<<"null";
        record<<",\"qualified_bound\":";
        if(qualified)record<<value;else record<<"null";
        record<<",\"full_precision_primal_objective\":";if(primal)record<<value;else record<<"null";
        record<<",\"actual_D1_row_violation\":"<<actual_D1_violation<<",\"qualified_beta_violation\":"<<qualified_beta_violation
            <<",\"maximum_row_violation\":"<<residual.maximum_violation<<",\"maximum_bound_violation\":"<<bound_violation
            <<",\"objective_expression_error\":"<<objective_error<<",\"wall_seconds\":"<<wall<<",\"Runtime\":"<<runtime<<",\"Work\":"<<work
            <<",\"cap_seconds\":"<<cap<<",\"source_model_SHA\":"<<std::quoted(fileSha256(model_path))
            <<",\"saved_model_SHA\":"<<std::quoted(fileSha256(dir/"actual_complete_relaxation.mps"))
            <<",\"rows\":"<<original.linear.rhs.size()<<",\"columns\":"<<n<<",\"nonzeros\":"<<original.linear.coefficients.size()<<"}\n";
        record.close();require(bool(record),"diagnostic receipt write");
        std::ofstream point(dir/"full_primal_and_original_matrix.json");point<<std::setprecision(17)<<"{\"names\":[";
        for(int j=0;j<n;++j){if(j)point<<',';point<<std::quoted(original.domain.names[j]);}
        point<<"],\"primal\":";array(point,x);point<<",\"original_objective\":";array(point,original.objective);
        point<<",\"original_objective_constant\":"<<original.constant<<",\"lower_bounds\":";array(point,original.domain.lower_bounds);
        point<<",\"upper_bounds\":";array(point,original.domain.upper_bounds);point<<",\"row_starts\":";ints(point,original.linear.row_starts);
        point<<",\"column_indices\":";ints(point,original.linear.column_indices);point<<",\"coefficients\":";array(point,original.linear.coefficients);
        point<<",\"rhs\":";array(point,original.linear.rhs);point<<",\"senses\":\"";for(char c:original.linear.senses)point<<c;
        point<<"\"}\n";point.close();require(bool(point),"complete primal/matrix write");
        std::cout<<dir.filename().string()<<" status="<<status<<" qualified="<<qualified<<" actual_D1_violation="<<actual_D1_violation<<'\n';
    }catch(...){if(model)api.freemodel(model);if(env)api.freeenv(env);throw;}
    api.freemodel(model);api.freeenv(env);
}
}
int main(int argc,char** argv){try{
    require(SetProcessAffinityMask(GetCurrentProcess(),4)!=0,"fixed diagnostic affinity");
    require(argc==2,"frozen two-role diagnostic TSV required");std::ifstream input(argv[1]);std::string line;int count=0;Api api;
    while(std::getline(input,line)) {
        if(!line.empty()&&line.back()=='\r')line.pop_back();if(line.empty())continue;
        std::istringstream row(line);std::vector<std::string> f;std::string v;while(std::getline(row,v,'\t'))f.push_back(v);
        require(f.size()==7,"diagnostic TSV shape");const double b0=std::stod(f[3]),b1=std::stod(f[4]),cap=std::stod(f[6]);
        require(cap==120,"diagnostic cap changed");
        const std::filesystem::path out(f[5]);
        one(api,f[1],f[2],b0,b1,false,cap,out/"D0_original_objective");
        one(api,f[2],f[2],b0,b1,false,cap,out/"D1_original_objective");
        one(api,f[1],f[2],b0,b1,true,cap,out/"D0_max_conditional_violation");++count;
    }
    require(count==2,"exactly F2 and R98-C2 diagnostic roles");return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
