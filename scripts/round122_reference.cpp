// R122 fixed six-input batch; original zero-Optimize writer and native columns reader.
// Administrative single-row batch; unchanged frozen original cold model writer.
// Additional reads expose actual native types/bounds/objective, never Optimize.
#define main inherited_cold_reference_main
#include "../src/round65_reference_build.cpp"
#undef main
#include <sstream>
#include <iomanip>
#include <vector>

static void native_columns(const std::filesystem::path& dir) {
    HMODULE dll=LoadLibraryW(L"gurobi130.dll");
    if(!dll)throw std::runtime_error("Gurobi DLL unavailable");
#define API(n) auto n=reinterpret_cast<decltype(&GRB##n)>(GetProcAddress(dll,"GRB" #n));if(!n)throw std::runtime_error("missing read-only API " #n)
    API(emptyenvinternal);API(setintparam);API(startenv);API(readmodel);
    API(getintattr);API(getdblattr);API(getcharattrarray);API(getdblattrarray);API(freemodel);API(freeenv);
#undef API
    auto check=[](int rc){if(rc)throw std::runtime_error("read-only API "+std::to_string(rc));};
    GRBenv* env=nullptr;GRBmodel* model=nullptr;
    try {
        check(emptyenvinternal(&env,GRB_VERSION_MAJOR,GRB_VERSION_MINOR,GRB_VERSION_TECHNICAL));
        check(setintparam(env,"OutputFlag",0));check(startenv(env));
        check(readmodel(env,(dir/"original.lp").string().c_str(),&model));
        int n=0,r=0,sense=0;double constant=0;
        check(getintattr(model,"NumVars",&n));check(getintattr(model,"NumConstrs",&r));
        check(getintattr(model,"ModelSense",&sense));check(getdblattr(model,"ObjCon",&constant));
        std::vector<char> types(n),senses(r);std::vector<double> lower(n),upper(n),objective(n),rhs(r);
        check(getcharattrarray(model,"VType",0,n,types.data()));
        check(getdblattrarray(model,"LB",0,n,lower.data()));check(getdblattrarray(model,"UB",0,n,upper.data()));
        check(getdblattrarray(model,"Obj",0,n,objective.data()));
        check(getcharattrarray(model,"Sense",0,r,senses.data()));check(getdblattrarray(model,"RHS",0,r,rhs.data()));
        std::ofstream c(dir/"native_columns.csv");c<<"index,type,lower,upper,objective\n"<<std::setprecision(17);
        for(int i=0;i<n;++i)c<<i<<','<<types[i]<<','<<lower[i]<<','<<upper[i]<<','<<objective[i]<<'\n';
        std::ofstream rows(dir/"native_rows.csv");rows<<"index,sense,RHS\n"<<std::setprecision(17);
        for(int i=0;i<r;++i)rows<<i<<','<<senses[i]<<','<<rhs[i]<<'\n';
        std::ofstream m(dir/"native_metadata.json");m<<std::setprecision(17)<<"{\"Optimize\":0,\"columns\":"<<n<<",\"rows\":"<<r
            <<",\"objective_sense\":"<<sense<<",\"objective_constant\":"<<constant<<"}\n";
        if(!c||!rows||!m)throw std::runtime_error("native reference persistence");
    }catch(...){if(model)freemodel(model);if(env)freeenv(env);FreeLibrary(dll);throw;}
    freemodel(model);freeenv(env);FreeLibrary(dll);
}

int main(int argc,char** argv) {try {
    if(argc!=2)throw std::runtime_error("fixed six-input TSV required");
    std::ifstream input(argv[1]);if(!input)throw std::runtime_error("manifest unavailable");
    std::string line;int count=0;
    while(std::getline(input,line)) {
        if(!line.empty()&&line.back()=='\r')line.pop_back();if(line.empty())continue;
        std::istringstream row(line);std::vector<std::string> fields{"Round122Reference"};std::string field;
        while(std::getline(row,field,'\t'))fields.push_back(field);
        if(fields.size()!=7)throw std::runtime_error("malformed manifest row");
        std::vector<char*> args;for(auto& f:fields)args.push_back(f.data());
        if(inherited_cold_reference_main(int(args.size()),args.data()))return 1;
        native_columns(fields[6]);++count;
        std::cout<<"read_only_cold_reference\t"<<fields[1]<<"\tOptimize=0\n";
    }
    if(count!=6)throw std::runtime_error("exactly six fixed new inputs required");
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
