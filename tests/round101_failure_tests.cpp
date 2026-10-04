// Include the production adapter to exercise its private C callback and summary
// writer directly. Fake API functions never load a DLL or call Optimize.
#include "../src/GurobiBaseline.cpp"
#include <iostream>
using namespace ebrp;
namespace {
int checks=0,terminated=0;
enum class Fault { none,status,cut,unknown };
Fault fault=Fault::none;
void require(bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);}
int __stdcall fakeGet(void*,int where,int what,void* out) {
    if(where==GRB_CB_MIPNODE) {
        if(what==GRB_CB_MIPNODE_STATUS) {
            if(fault==Fault::unknown)throw 17;
            if(fault==Fault::status)return 10003;
            *static_cast<int*>(out)=GRB_OPTIMAL;
        } else if(what==GRB_CB_MIPNODE_NODCNT)*static_cast<double*>(out)=0;
        else if(what==GRB_CB_MIPNODE_REL)for(int j=0;j<10;++j)static_cast<double*>(out)[j]=(j%2==0?1:0);
        else return 10003;
        return 0;
    }
    if(where==GRB_CB_MIP) {
        if(what==GRB_CB_MIP_SOLCNT||what==GRB_CB_MIP_PHASE)*static_cast<int*>(out)=0;
        else *static_cast<double*>(out)=(what==GRB_CB_MIP_OBJBND?.25:(what==GRB_CB_MIP_OBJBST?GRB_INFINITY:0));
        return 0;
    }
    return 10003;
}
int __stdcall fakeCut(void*,int,const int*,const double*,char,double){return fault==Fault::cut?10003:0;}
void __stdcall fakeTerminate(GRBmodel*){++terminated;}
Instance fixture(const std::filesystem::path& input) {
    Instance in;in.path=input.string();in.V=5;in.M=2;in.Q={5,5};
    in.initial.assign(6,5);in.target.assign(6,5);in.capacity.assign(6,10);in.weights.assign(6,.2);
    in.dist.assign(6,std::vector<double>(6,0));in.total_time_limit=5;in.pickup_time=2;in.drop_time=0;return in;
}
std::shared_ptr<NativeEvidenceJournal> journal(const Instance& in,const std::filesystem::path& path) {
    SolveOptions opt;opt.lambda=.15;opt.process_start_time_valid=true;
    opt.process_start_time=Clock::now();opt.native_evidence_dir=path.string();
    auto j=std::make_shared<NativeEvidenceJournal>(in,opt);
    NativeEvidenceScope scope;scope.full_original=scope.native_preconditions=true;scope.gmax=.8;
    scope.model_path=in.path;scope.model_sha256=fileSha256(in.path);
    scope.settings_json="{\"read_return_code\":0,\"Threads\":1,\"Seed\":0,\"Presolve\":-1,\"MIPGap\":0,\"MIPGapAbs\":0,\"FeasibilityTol\":1e-6,\"IntFeasTol\":1e-5,\"OptimalityTol\":1e-6}";
    require(j->beginCall(scope)==1,"first fixture call");j->nativeBound(1,.1);
    std::string data,why;
    require(readNativeEvidenceReceipt(path/"event_3.commit",1,2,data,why)&&
        data.find("\"global_available\":1")!=std::string::npos,"seeded bound has global eligibility");
    return j;
}
void checkFailure(ProgressCallbackState& s,const std::filesystem::path& dir,const char* reason) {
    require(s.fleet_failed&&s.fleet_failure==reason,"fatal fleet state");
    require(!s.native_evidence->enabled(),"journal disabled");
    std::string data,why;
    require(readNativeEvidenceReceipt(dir/"event_4.commit",1,2,data,why),"durable complete failure receipt");
    require(data.find("\"kind\":\"failure\"")!=std::string::npos&&data.find(reason)!=std::string::npos,"fatal reason persisted");
    s.native_evidence->nativeBound(1,.3);s.native_evidence->returned(1,0);
    progressAndBoundTargetCallback(nullptr,nullptr,GRB_CB_MIP,&s);
    require(!std::filesystem::exists(dir/"event_5.commit"),"no subsequent bound or returned publication");
}
}
int main(int argc,char** argv){try {
    require(argc==2,"exclusive artifact directory argument");
    const std::filesystem::path root=argv[1];require(std::filesystem::create_directory(root),"new artifact directory");
    const auto input=root/"fixture.txt";{std::ofstream f(input);f<<"synthetic callback control fixture\n";}
    auto in=fixture(input);GurobiApi api;api.cbget=fakeGet;api.cbcut=fakeCut;api.terminate=fakeTerminate;
    const std::vector<std::tuple<std::string,Fault,std::string,std::string>> cases={
        {"status",Fault::status,"shadow","fleet_status_read"},
        {"cut",Fault::cut,"submit","fleet_GRBcbcut:10003"},
        {"certificate",Fault::none,"shadow","fleet_certificate_write"},
        {"unknown",Fault::unknown,"shadow","fleet_unknown_callback_exception"}};
    for(const auto& [name,f,mode,reason]:cases) {
        ProgressCallbackState s;s.api=&api;s.fleet_mode=mode;s.fleet_range="root";s.fleet_margin=1e-5;
        s.fleet_contract=physicalFleetContract(in);s.fleet_contract.columns=10;
        s.fleet_contract.states.resize(6);
        for(int i=1;i<=5;++i)s.fleet_contract.states[i]={{4,2*(i-1)},{5,2*(i-1)+1}};
        // The synthetic control fixture intentionally leaves the certificate
        // stream unopened; it is not an imported-matrix qualification test.
        s.fleet_values.resize(10);s.native_evidence=journal(in,root/name);s.evidence_call=1;
        fault=f;const int before=terminated;
        require(progressAndBoundTargetCallback(nullptr,nullptr,GRB_CB_MIPNODE,&s)==0,"C callback returns safely");
        require(terminated==before+1,"fatal callback requests termination");
        checkFailure(s,root/name,reason.c_str());
        progressAndBoundTargetCallback(nullptr,nullptr,GRB_CB_MIPNODE,&s);
        require(terminated==before+1,"failed callback does not reenter separator");
    }
    fault=Fault::none;
    const std::vector<std::tuple<std::string,Fault,std::string,std::string>> service_cases={
        {"service_status",Fault::status,"shadow","service_status_read"},
        {"service_cut",Fault::cut,"submit","service_GRBcbcut:10003"},
        {"service_certificate",Fault::none,"shadow","service_certificate_write"},
        {"service_unknown",Fault::unknown,"shadow","service_unknown_callback_exception"}};
    for(const auto&[name,f,mode,reason]:service_cases){
        ProgressCallbackState s;s.api=&api;s.service_mode=mode;s.service_margin=1e-5;
        s.service_contract.valid=true;s.service_contract.resource=physicalFleetContract(in);s.service_contract.resource.columns=10;
        s.service_contract.columns.assign(2,std::vector<std::array<int,3>>(6,{-1,-1,-1}));
        for(int k=0;k<2;++k)for(int i=1;i<=5;++i)s.service_contract.columns[k][i]={2*(i-1),2*(i-1)+1,2*(i-1)};
        s.service_contract.identity=serviceContractJson(s.service_contract);s.service_values.resize(10);
        s.service_point_path=(root/(name+".point.json")).string();s.native_evidence=journal(in,root/name);s.evidence_call=1;
        fault=f;const int before=terminated;
        require(progressAndBoundTargetCallback(nullptr,nullptr,GRB_CB_MIPNODE,&s)==0,"service C callback safe return");
        require(terminated==before+1,"service failure terminates");checkFailure(s,root/name,reason.c_str());
        progressAndBoundTargetCallback(nullptr,nullptr,GRB_CB_MIPNODE,&s);require(terminated==before+1,"failed service callback no reentry");
    }
    fault=Fault::none;
    ProgressCallbackState service_summary;service_summary.api=&api;service_summary.service_mode="submit";
    service_summary.native_evidence=journal(in,root/"service_summary");service_summary.evidence_call=1;
    writeServiceSummary(service_summary,root.string(),1,0);
    checkFailure(service_summary,root/"service_summary","service_summary_write_failed");
    ProgressCallbackState summary;summary.api=&api;summary.fleet_mode="submit";
    summary.native_evidence=journal(in,root/"summary");summary.evidence_call=1;
    writeFleetSummary(summary,root.string(),1,0); // Existing directory cannot be opened as a file.
    checkFailure(summary,root/"summary","fleet_summary_write_failed");
    ProgressCallbackState good;good.api=&api;good.fleet_mode="shell";
    good.native_evidence=journal(in,root/"success");good.evidence_call=1;
    writeFleetSummary(good,(root/"success.json").string(),1,.01);
    require(!good.fleet_failed&&good.native_evidence->enabled(),"successful summary preserves eligibility");
    progressAndBoundTargetCallback(nullptr,nullptr,GRB_CB_MIP,&good);
    require(std::filesystem::exists(root/"success/event_4.commit"),"healthy callback still publishes bound");
    std::cout<<checks<<" actual callback/summary fault checks passed; zero Optimize calls\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
