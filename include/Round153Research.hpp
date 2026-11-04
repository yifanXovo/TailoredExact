#pragma once
#include "Round151Research.hpp"
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace ebrp {
struct Round153Controls {
    bool enabled=false,generated=false,accepted=false,global_stop=false;
    std::string python,helper,manifest,helper_sha,manifest_sha,input_sha,root_source_sha;
    long long bm=0,b=0;
    double gamma_L=0,gamma_U=0,cutoff=0,lower=0,helper_seconds=0;
    int helper_exit=-1;
    std::vector<std::vector<int>> support;
    std::vector<double> ratios,weights;
    std::map<std::string,std::vector<round143_detail::Row>> expected;
};
inline Round153Controls& round153(){static Round153Controls c;return c;}
inline void round153ResetRun(){
    const auto old=round153();round153()=Round153Controls{};
    auto& c=round153();c.enabled=old.enabled;c.python=old.python;c.helper=old.helper;
    c.manifest=old.manifest;c.helper_sha=old.helper_sha;c.manifest_sha=old.manifest_sha;
}
namespace round153_detail {
inline void require(bool ok,const std::string& why){if(!ok)throw std::runtime_error("round153_"+why);}
inline std::wstring quoteWindows(const std::wstring& arg){
    std::wstring out=L"\"";std::size_t slashes=0;
    for(wchar_t ch:arg){
        if(ch==L'\\'){++slashes;continue;}
        if(ch==L'\"'){out.append(2*slashes+1,L'\\');out+=ch;slashes=0;continue;}
        out.append(slashes,L'\\');slashes=0;out+=ch;
    }
    out.append(2*slashes,L'\\');out+=L'\"';return out;
}
inline int hiddenHelper(const std::vector<std::string>& argv,double remaining){
#ifdef _WIN32
    if(remaining<=0)return 124;
    const auto tick=std::chrono::steady_clock::now();
    std::wstring command;
    for(const auto& arg:argv){if(!command.empty())command+=L' ';command+=quoteWindows(std::filesystem::path(arg).wstring());}
    std::vector<wchar_t> buffer(command.begin(),command.end());buffer.push_back(0);
    STARTUPINFOW start{};start.cb=sizeof(start);start.dwFlags=STARTF_USESHOWWINDOW;start.wShowWindow=SW_HIDE;
    HANDLE job=CreateJobObjectW(nullptr,nullptr);if(!job)return -int(GetLastError());
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if(!SetInformationJobObject(job,JobObjectExtendedLimitInformation,&limits,sizeof(limits))){const int error=-int(GetLastError());CloseHandle(job);return error;}
    PROCESS_INFORMATION process{};
    if(!CreateProcessW(nullptr,buffer.data(),nullptr,nullptr,FALSE,CREATE_NO_WINDOW|CREATE_SUSPENDED,nullptr,nullptr,&start,&process)){
        const int error=-int(GetLastError());CloseHandle(job);return error;
    }
    if(!AssignProcessToJobObject(job,process.hProcess)){
        const int error=-int(GetLastError());TerminateProcess(process.hProcess,1);WaitForSingleObject(process.hProcess,2000);
        CloseHandle(process.hThread);CloseHandle(process.hProcess);CloseHandle(job);return error;
    }
    if(ResumeThread(process.hThread)==DWORD(-1)){
        const int error=-int(GetLastError());TerminateJobObject(job,1);WaitForSingleObject(process.hProcess,2000);
        CloseHandle(process.hThread);CloseHandle(process.hProcess);CloseHandle(job);return error;
    }
    const double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-tick).count();
    const DWORD wait_ms=DWORD(std::min(4294967294.,std::max(0.,std::ceil((remaining-elapsed)*1000.))));
    const DWORD waited=WaitForSingleObject(process.hProcess,wait_ms);DWORD code=1;
    if(waited==WAIT_OBJECT_0)GetExitCodeProcess(process.hProcess,&code);
    else{TerminateJobObject(job,124);WaitForSingleObject(process.hProcess,2000);code=124;}
    CloseHandle(process.hThread);CloseHandle(process.hProcess);CloseHandle(job);return int(code);
#else
    (void)argv;(void)remaining;return -1;
#endif
}
inline CanonicalCompactModelArtifact embed(const Instance& instance,const CanonicalCompactModelArtifact& base,
                                           double cutoff,const std::filesystem::path& path,double global_remaining){
    auto& c=round153();if(!c.enabled)return base;
    const auto embed_tick=std::chrono::steady_clock::now();
    require(base.written&&fileSha256(base.path)==base.sha256&&std::isfinite(cutoff),"base_identity");
    const auto text=round141_detail::material(base.path);const auto support=round141_detail::supports(text,instance.V);
    const auto objective=round141_detail::objective(text);
    require(objective.constant==0&&objective.coefficients.at("G")==1,"objective_units");
    std::vector<double> ratios(instance.V+1),weights(instance.V+1);long long b=0,q=0;
    for(const auto& term:objective.coefficients)
        require(term.first=="G"||(term.first.rfind("e_",0)==0&&term.second>=0),"objective_scope");
    for(int i=1;i<=instance.V;++i){
        b+=instance.initial[i];ratios[i]=1./instance.target[i];
        const auto hit=objective.coefficients.find("e_"+std::to_string(i));weights[i]=hit==objective.coefficients.end()?0.:hit->second;
    }
    for(int capacity:instance.Q)q+=capacity;const long long bm=std::max(0LL,b-q);
    const auto input_sha=fileSha256(instance.path);
    if(!c.generated){
        c.generated=true;c.input_sha=input_sha;c.root_source_sha=base.sha256;c.bm=bm;c.b=b;
        c.ratios=ratios;c.weights=weights;c.support=support;c.gamma_L=base.gamma_L;c.gamma_U=base.gamma_U;c.cutoff=cutoff;
        const auto target=path.parent_path().parent_path()/"round153_floor";
        require(!std::filesystem::exists(target),"helper_output_collision");
        require(fileSha256(c.helper)==c.helper_sha,"helper_source_identity");
        require(fileSha256(c.manifest)==c.manifest_sha,"helper_manifest_identity");
        const auto tick=std::chrono::steady_clock::now();
        const double remaining=std::max(0.,global_remaining-std::chrono::duration<double>(tick-embed_tick).count());
        std::ostringstream remaining_text;remaining_text<<std::setprecision(17)<<remaining;
        c.helper_exit=hiddenHelper({c.python,"-B",c.helper,"--source",base.path.string(),"--out",target.string(),
                                   "--Bminus",std::to_string(bm),"--B",std::to_string(b),"--manifest",c.manifest,
                                   "--remaining-global-seconds",remaining_text.str()},remaining);
        c.helper_seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-tick).count();
        c.global_stop=c.helper_exit==124;
        require(fileSha256(c.helper)==c.helper_sha&&fileSha256(c.manifest)==c.manifest_sha&&fileSha256(base.path)==base.sha256,"helper_return_identity");
        if(c.helper_exit==0){
            std::ifstream response(target/"response.txt");std::string protocol,source_sha,manifest_sha,helper_sha;int qualified=0;double lower=0;
            if(response>>protocol>>source_sha>>manifest_sha>>helper_sha>>qualified>>lower){
                c.accepted=protocol=="R153-FLOOR-v2"&&source_sha==base.sha256&&manifest_sha==c.manifest_sha&&helper_sha==c.helper_sha&&qualified==1&&
                    std::isfinite(lower)&&lower>=0&&lower<=cutoff+1e-8;
                if(c.accepted)c.lower=lower;
            }
        }
        // Failed/undecided helper sources cannot add an unqualified row.
        // Existing B information and the ordinary full-run controller remain.
        std::ofstream f(path.parent_path()/"round153_root.json");f<<std::setprecision(17)
            <<"{\"input_SHA\":"<<std::quoted(input_sha)<<",\"source_SHA\":"<<std::quoted(base.sha256)
            <<",\"helper_SHA\":"<<std::quoted(c.helper_sha)<<",\"helper_manifest_SHA\":"<<std::quoted(c.manifest_sha)
            <<",\"Bminus\":"<<bm<<",\"B\":"<<b<<",\"gamma_L\":"<<c.gamma_L<<",\"gamma_U\":"<<c.gamma_U
            <<",\"own_cutoff\":"<<cutoff<<",\"qualified\":"<<(c.accepted?"true":"false")<<",\"lower\":"<<c.lower
            <<",\"helper_exit\":"<<c.helper_exit<<",\"helper_process_seconds\":"<<c.helper_seconds
            <<",\"whole_method_remaining_at_launch\":"<<remaining<<",\"global_deadline_stop\":"<<(c.global_stop?"true":"false")
            <<",\"owned_helper_job_kill_on_close\":true"
            <<",\"node_limit\":4096,\"price_gap_target\":0.0001,\"root_once\":true,\"offline_data_used\":false"
            <<",\"formal_AP_GD_RN_NC_TS\":false,\"formal_new_columns\":0,\"extra_root_LP\":0}\n";
        f.close();require(bool(f),"root_evidence_write");
    }
    require(c.input_sha==input_sha&&c.ratios==ratios&&c.weights==weights&&c.bm==bm&&c.b==b&&
            base.gamma_L>=c.gamma_L&&base.gamma_U<=c.gamma_U&&cutoff<=c.cutoff,"descendant_scope");
    for(int i=1;i<=instance.V;++i)
        require(std::includes(c.support[i].begin(),c.support[i].end(),support[i].begin(),support[i].end()),"support_expanded");
    std::vector<round143_detail::Row> rows;
    if(c.accepted&&c.lower>base.gamma_L+1e-7)rows.push_back({"r153_root_floor",objective.coefficients,'>',c.lower});
    auto out=base;
    if(!rows.empty()){
        out=round144_detail::append(base,rows,{},path,"R153");
        out.model_scope=base.model_scope+"_round153_root_floor";out.row_signature=base.row_signature+"|round153:"+out.sha256;
    }
    c.expected.emplace(out.sha256,rows);
    std::ofstream f(path.string()+".round153.json");f<<std::setprecision(17)
        <<"{\"base_SHA\":"<<std::quoted(base.sha256)<<",\"final_SHA\":"<<std::quoted(out.sha256)
        <<",\"root_source_SHA\":"<<std::quoted(c.root_source_sha)<<",\"qualified_source\":"<<(c.accepted?"true":"false")
        <<",\"lower\":"<<c.lower<<",\"added_rows\":"<<rows.size()<<",\"new_columns\":0,\"compatible_domain\":true}\n";
    f.close();require(bool(f),"embedding_evidence_write");return out;
}
}
}
