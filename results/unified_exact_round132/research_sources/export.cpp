#include "Round132Expression.hpp"
// Zero-Optimize export using actual E0 or E1 writer, plus native type/readback.
#include "CanonicalCompactModel.hpp"
#include "Parser.hpp"
#include <windows.h>
#include <gurobi_c.h>
#include <iomanip>
#include <iostream>
#include "Round127Research.hpp"
#include "PaperK1AmSf.hpp"
static int native_columns(const std::filesystem::path& dir) {
    HMODULE dll=LoadLibraryW(L"gurobi130.dll");
    if(!dll)throw std::runtime_error("Gurobi DLL unavailable");
#define API(n) auto n=reinterpret_cast<decltype(&GRB##n)>(GetProcAddress(dll,"GRB" #n));if(!n)throw std::runtime_error("missing read-only API " #n)
    API(version);API(emptyenvinternal);API(setintparam);API(startenv);API(readmodel);
    API(getintattr);API(getdblattr);API(getcharattrarray);API(getdblattrarray);API(freemodel);API(freeenv);
#undef API
    auto check=[](int rc){if(rc)throw std::runtime_error("read-only API "+std::to_string(rc));};
    int major=0,minor=0,technical=0;version(&major,&minor,&technical);
    std::ofstream version_out(dir/"native_version.json");version_out<<"{\"major\":"<<major<<",\"minor\":"<<minor<<",\"technical\":"<<technical<<"}\n";
    GRBenv* env=nullptr;GRBmodel* model=nullptr;int fingerprint=0;
    try {
        check(emptyenvinternal(&env,GRB_VERSION_MAJOR,GRB_VERSION_MINOR,GRB_VERSION_TECHNICAL));
        check(setintparam(env,"OutputFlag",0));check(startenv(env));
        check(readmodel(env,(dir/"original.lp").string().c_str(),&model));
        int n=0,r=0,sense=0;double constant=0;
        check(getintattr(model,"NumVars",&n));check(getintattr(model,"NumConstrs",&r));
        check(getintattr(model,"ModelSense",&sense));check(getdblattr(model,"ObjCon",&constant));
        check(getintattr(model,"Fingerprint",&fingerprint));
        std::vector<char> types(n),senses(r);std::vector<double> lower(n),upper(n),objective(n),rhs(r);
        check(getcharattrarray(model,"VType",0,n,types.data()));
        check(getdblattrarray(model,"LB",0,n,lower.data()));check(getdblattrarray(model,"UB",0,n,upper.data()));
        check(getdblattrarray(model,"Obj",0,n,objective.data()));
        check(getcharattrarray(model,"Sense",0,r,senses.data()));check(getdblattrarray(model,"RHS",0,r,rhs.data()));
        std::ofstream c(dir/"native_columns.csv");c<<"index,type,lower,upper,objective\n"<<std::setprecision(17);
        for(int i=0;i<n;++i)c<<i<<','<<types[i]<<','<<lower[i]<<','<<upper[i]<<','<<objective[i]<<'\n';
        std::ofstream rows(dir/"native_rows.csv");rows<<"index,sense,RHS\n"<<std::setprecision(17);
        for(int i=0;i<r;++i)rows<<i<<','<<senses[i]<<','<<rhs[i]<<'\n';
        std::ofstream m(dir/"native_metadata.json");m<<"{\"Optimize\":0,\"columns\":"<<n<<",\"rows\":"<<r
            <<",\"objective_sense\":"<<sense<<",\"objective_constant\":"<<constant<<"}\n";
        if(!c||!rows||!m)throw std::runtime_error("native reference persistence");
    }catch(...){if(model)freemodel(model);if(env)freeenv(env);FreeLibrary(dll);throw;}
    freemodel(model);freeenv(env);FreeLibrary(dll);return fingerprint;
}
int main(int argc,char** argv) {try {
    if(argc!=8 && argc!=9)throw std::runtime_error("input T gL gU U mode directory");
    auto in=ebrp::parseInstanceFile(argv[1],std::stod(argv[2]),60,60);
    ebrp::SolveOptions opt;ebrp::configurePaperK1AmSfOverrides(opt);opt.lambda=.15;
    opt.round98_state_service="m-binary";
    if(argc==9 && std::string(argv[8])=="fallback")opt.interval_row_factory_round19=false;
    const std::string mode=argv[6];ebrp::round127().mode=mode;
    if(argc==9 && std::string(argv[8])!="fallback")ebrp::round132SetExpression(argv[8]);
    ebrp::CanonicalCompactModelSpec spec;
    spec.strengthened=mode!="p";spec.interval_restricted=mode!="p";
    spec.gamma_L=std::stod(argv[3]);spec.gamma_U=std::stod(argv[4]);
    spec.add_verified_incumbent_row=mode!="p";spec.verified_incumbent=std::stod(argv[5]);
    spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    if(mode=="p") {opt=ebrp::SolveOptions{};opt.lambda=.15;opt.plain_baseline=true;spec.station_state_formulation="bit-product";}
    const std::filesystem::path d(argv[7]);std::filesystem::create_directories(d);
    const auto a=ebrp::writeCanonicalCompactModel(in,opt,d/"original.lp",spec);
    if(!a.written)throw std::runtime_error(a.failure_reason);
    const int fingerprint=native_columns(d);
    std::ofstream f(d/"build.json");f<<"{\"optimizer_calls\":0,\"canonical_sha256\":\""<<a.sha256
        <<"\",\"rows\":"<<a.rows<<",\"columns\":"<<a.columns<<",\"nonzeros\":"<<a.nonzeros<<",\"fingerprint\":"<<fingerprint<<"}\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
