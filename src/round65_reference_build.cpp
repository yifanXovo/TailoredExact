// Build-only original P-GRB fingerprint. This executable never resolves or
// calls GRBoptimize; it supplies no primal point, bound, basis, or warm start.
#include "CanonicalCompactModel.hpp"
#include "Parser.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
#define NOMINMAX
#include <windows.h>
#include <gurobi_c.h>
#endif
int main(int argc,char** argv) {try {
    if(argc!=7)throw std::runtime_error("input T pickup drop lambda output_directory");
    auto in=ebrp::parseInstanceFile(argv[1],std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]));
    ebrp::SolveOptions opt;opt.lambda=std::stod(argv[5]);
    const std::filesystem::path dir(argv[6]);std::filesystem::create_directories(dir);
    ebrp::CanonicalCompactModelSpec spec;spec.strengthened=false;
    const auto a=ebrp::writeCanonicalCompactModel(in,opt,dir/"original.lp",spec);
    if(!a.written)throw std::runtime_error(a.failure_reason);
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
    HMODULE dll=LoadLibraryW((L"gurobi"+std::to_wstring(GRB_VERSION_MAJOR)+std::to_wstring(GRB_VERSION_MINOR)+L".dll").c_str());
    if(!dll)throw std::runtime_error("Gurobi DLL unavailable");
#define API(n) auto n=reinterpret_cast<decltype(&GRB##n)>(GetProcAddress(dll,"GRB" #n));if(!n)throw std::runtime_error("missing API " #n)
    API(emptyenvinternal);API(setintparam);API(startenv);API(readmodel);API(getintattr);API(freemodel);API(freeenv);
#undef API
    auto check=[](int rc){if(rc)throw std::runtime_error("native read-only API "+std::to_string(rc));};
    GRBenv* env=nullptr;GRBmodel* model=nullptr;
    try {
        check(emptyenvinternal(&env,GRB_VERSION_MAJOR,GRB_VERSION_MINOR,GRB_VERSION_TECHNICAL));
        check(setintparam(env,"OutputFlag",0));check(startenv(env));
        check(readmodel(env,(dir/"original.lp").string().c_str(),&model));
        int fingerprint=0,columns=0,rows=0;
        check(getintattr(model,"Fingerprint",&fingerprint));check(getintattr(model,"NumVars",&columns));check(getintattr(model,"NumConstrs",&rows));
        std::ofstream f(dir/"build.json");f<<"{\"optimizer_calls\":0,\"fingerprint\":"<<fingerprint
            <<",\"canonical_sha256\":\""<<a.sha256<<"\",\"columns\":"<<columns<<",\"rows\":"<<rows<<"}\n";
        if(!f)throw std::runtime_error("build record persistence");
    }catch(...){if(model)freemodel(model);if(env)freeenv(env);FreeLibrary(dll);throw;}
    freemodel(model);freeenv(env);FreeLibrary(dll);
#else
    throw std::runtime_error("build-only fingerprint requires local Gurobi");
#endif
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
