#pragma once
#include "Round140Research.hpp"
#include "Round120NativeProof.hpp"
#include "FileSha256.hpp"
#include <regex>
#include <set>
#include <sstream>
#include <iomanip>
#include <numeric>

namespace ebrp {
// Process-local research state preserves all existing public structure ABIs.
// Count proofs never occupy a Gini leaf or a frontier cover piece.
namespace round141_detail {
using Int=round140_detail::Int;
inline void require(bool ok,const std::string& why) {if(!ok)throw std::runtime_error("round141_"+why);}
inline std::string integer(Int x) {
    if(!x)return "0";bool neg=x<0;if(neg)x=-x;std::string s;
    while(x){s.push_back(char('0'+x%10));x/=10;}if(neg)s.push_back('-');
    std::reverse(s.begin(),s.end());return s;
}
inline Int integer(const std::string& text) {
    require(!text.empty(),"empty_exact_threshold");Int x=0;bool neg=text[0]=='-';
    for(std::size_t j=neg?1:0;j<text.size();++j){require(text[j]>='0'&&text[j]<='9',"bad_exact_threshold");x=round140_detail::add(round140_detail::mul(x,10),text[j]-'0');}
    return neg?-x:x;
}
inline std::string number(double x){std::ostringstream s;s<<std::setprecision(17)<<x;return s.str();}
inline std::vector<std::string> split(const std::string& s,char c) {
    std::vector<std::string> a;std::istringstream f(s);std::string v;while(std::getline(f,v,c))a.push_back(v);return a;
}
inline std::string material(const std::filesystem::path& p) {
    std::ifstream f(p,std::ios::binary);require(bool(f),"model_read_failed");std::ostringstream s;s<<f.rdbuf();return s.str();
}
inline std::vector<std::vector<int>> supports(const std::string& text,int n) {
    std::vector<std::set<int>> found(n+1);std::regex pattern("\\bstate_([0-9]+)_([0-9]+)\\b");
    for(auto it=std::sregex_iterator(text.begin(),text.end(),pattern);it!=std::sregex_iterator();++it) {
        int i=std::stoi((*it)[1]),y=std::stoi((*it)[2]);require(i>0&&i<=n,"selector_station");found[i].insert(y);
    }
    std::vector<std::vector<int>> s(n+1);for(int i=1;i<=n;++i){require(!found[i].empty(),"empty_selector_support");s[i]={found[i].begin(),found[i].end()};}return s;
}
struct Row {std::string name;std::map<std::string,double> coefficients;char sense='>';double rhs=0;};
struct GridRow {Int t=0,delta=0;int ell=0,u=0;};
struct Grid {int exponent=0;std::vector<GridRow> rows;};
inline Grid grid(const std::vector<std::vector<int>>& s,const std::vector<double>& ratios,long long bm,long long b) {
    using namespace round140_detail;Grid g;int n=int(s.size())-1;long long minimum=0,maximum=0;
    for(int i=1;i<=n;++i){int e=0;std::frexp(ratios[i],&e);g.exponent=std::min(g.exponent,e-53);minimum+=s[i].front();maximum+=s[i].back();}
    bm=std::max(bm,minimum);b=std::min(b,maximum);require(bm<=b,"incompatible_inventory_domain");
    std::vector<std::vector<Int>> levels(n+1);std::set<Int> thresholds;
    for(int i=1;i<=n;++i)for(int y:s[i]){Int v=mul(units(ratios[i],g.exponent),y);levels[i].push_back(v);if(v>0)thresholds.insert(v);}
    Int previous=0;
    for(Int t:thresholds){int forced=0;long long C0=0;std::vector<long long> costs,gains;
        for(int i=1;i<=n;++i){auto k=std::lower_bound(levels[i].begin(),levels[i].end(),t)-levels[i].begin();
            if(k==0){++forced;C0+=s[i].back();}else if(k==static_cast<long long>(s[i].size()))C0+=s[i].back();
            else{costs.push_back(s[i][k]-s[i].front());gains.push_back(s[i].back()-s[i][k-1]);C0+=s[i][k-1];}}
        std::sort(costs.begin(),costs.end());std::sort(gains.rbegin(),gains.rend());long long used=0,total=C0;int u=forced,q=0;
        for(auto cost:costs){if(used+cost>b-minimum)break;used+=cost;++u;}
        while(total<bm&&q<int(gains.size()))total+=gains[q++];
        require(total>=bm&&forced+q<=u,"incompatible_count_interval");g.rows.push_back({t,t-previous,forced+q,u});previous=t;
    }return g;
}
struct Objective {std::map<std::string,double> coefficients;double constant=0;};
inline Objective objective(const std::string& text) {
    auto begin=text.find(" obj: "),end=text.find("\nSubject To\n");
    require(begin!=std::string::npos&&end!=std::string::npos&&begin<end,"objective_text");
    std::istringstream in(text.substr(begin+6,end-begin-6));std::vector<std::string> a;std::string token;while(in>>token)a.push_back(token);
    Objective result;double sign=1;
    for(std::size_t k=0;k<a.size();){if(a[k]=="+"){sign=1;++k;continue;}if(a[k]=="-"){sign=-1;++k;continue;}
        char* finish=nullptr;double value=std::strtod(a[k].c_str(),&finish);
        if(finish&&*finish=='\0'){++k;if(k==a.size()||a[k]=="+"||a[k]=="-")result.constant+=sign*value;else result.coefficients[a[k++]]+=sign*value;}
        else result.coefficients[a[k++]]+=sign;
        sign=1;
    }require(!result.coefficients.empty()&&std::isfinite(result.constant),"empty_objective");return result;
}
inline std::string emit(const Row& r) {
    std::ostringstream out;out<<std::setprecision(17)<<' '<<r.name<<": ";bool first=true;
    for(const auto& [name,value]:r.coefficients)if(value){out<<(first?(value<0?"- ":""):(value<0?" - ":" + "))<<std::fabs(value)<<' '<<name;first=false;}
    if(first)out<<"0 G";out<<(r.sense=='>'?" >= ":r.sense=='<'?" <= ":" = ")<<r.rhs<<'\n';return out.str();
}
}

struct Round141Choice {
    round141_detail::Int threshold=0;int exponent=0,ell=0,u=0,pivot=0;
    long double K=0,score=0;std::vector<double> ratios;std::vector<std::vector<int>> support;
    std::string support_sha,root_sha,input_sha;double a=0,z=0,cutoff=0,model_cutoff=0;
    std::array<double,2> beta{{0,0}},raw{{0,0}};
    std::array<long long,2> calls{{0,0}};std::array<std::string,2> proof_sha;
};
struct Round141Controls {
    std::string mode="off";bool attempted=false,ready=false,root_qualified=false;
    std::string root_selector_sha;std::map<std::string,double> root_selector;
    CanonicalCompactModelArtifact root_artifact;double root_cutoff=0;Round141Choice choice;
    std::filesystem::path events;
    std::map<std::string,std::vector<round141_detail::Row>> expected;
    bool enabled()const{return mode!="off";}
    void set(const std::string& value){round141_detail::require(value=="off"||value=="d0"||value=="d1","mode");mode=value;}
};
inline Round141Controls& round141(){static Round141Controls c;return c;}
inline void round141Event(const std::string& kind,const std::string& fields="") {
    if(round141().events.empty())return;std::ofstream f(round141().events,std::ios::app);
    f<<"{\"kind\":"<<std::quoted(kind);if(!fields.empty())f<<','<<fields;f<<"}\n";
    round141_detail::require(bool(f),"event_write");
}
inline int round141Count(const Round141Choice& c,const std::vector<int>& y,bool require_support=true) {
    using namespace round140_detail;round141_detail::require(y.size()==c.ratios.size(),"physical_inventory_shape");int K=0;
    for(std::size_t i=1;i<y.size();++i){if(require_support)round141_detail::require(std::binary_search(c.support[i].begin(),c.support[i].end(),y[i]),"inventory_outside_source_support");K+=mul(units(c.ratios[i],c.exponent),y[i])>=c.threshold;}return K;
}
inline std::vector<std::string> round141Membership(const Round141Choice& c,const std::vector<std::vector<int>>& s) {
    using namespace round140_detail;std::vector<std::string> names;
    for(std::size_t i=1;i<s.size();++i)for(int y:s[i])if(mul(units(c.ratios[i],c.exponent),y)>=c.threshold)names.push_back("state_"+std::to_string(i)+"_"+std::to_string(y));return names;
}
inline bool round141Choose(const Instance& instance) {
    using namespace round141_detail;using namespace round140_detail;auto& state=round141();auto& c=state.choice;
    require(state.root_qualified&&state.root_selector_sha==state.root_artifact.sha256,"qualified_root_selector_readback_missing");
    const auto text=material(state.root_artifact.path);c.support=supports(text,instance.V);c.ratios.resize(instance.V+1);
    long long B=0,Q=0;for(int i=1;i<=instance.V;++i){c.ratios[i]=1.0/instance.target[i];B+=instance.initial[i];}for(int q:instance.Q)Q+=q;
    const auto g=grid(c.support,c.ratios,std::max(0LL,B-Q),B);c.exponent=g.exponent;
    bool found=false;long double best=-1,best_violation=-1;
    for(const auto& r:g.rows){if(r.ell==r.u)continue;Round141Choice candidate=c;candidate.threshold=r.t;
        long double K=0;for(const auto& name:round141Membership(candidate,c.support)){
            auto it=state.root_selector.find(name);require(it!=state.root_selector.end()&&std::isfinite(it->second),"selector_readback_incomplete");K+=it->second;}
        const long double violation=std::max({static_cast<long double>(r.ell)-K,K-r.u,0.L});
        // A tiny range residual is not a negative chord score and is never
        // silently clipped into the interval. Other admissible counts remain.
        if(violation>0&&violation<=1e-7L)continue;
        const long double score=std::ldexp(static_cast<long double>(r.delta),g.exponent)*(K-r.ell)*(r.u-K);
        bool better=violation>1e-7L?(best_violation<=1e-7L||violation>best_violation):(best_violation<=1e-7L&&score>best);
        if(!found||better){found=true;c.threshold=r.t;c.ell=r.ell;c.u=r.u;c.K=K;c.score=score;best=score;best_violation=violation;}
    }
    if(!found){round141Event("not_triggered","\"reason\":\"no_nondegenerate_count\"");return false;}
    c.pivot=std::max(c.ell,std::min(c.u-1,int(std::floor(c.K))));
    c.root_sha=state.root_artifact.sha256;c.input_sha=fileSha256(instance.path);
    c.a=state.root_artifact.gamma_L;c.z=state.root_artifact.gamma_U;
    // Source cutoff is read from the complete objective row, never a displayed U.
    const auto obj=objective(text);std::istringstream lines(text);std::string line;bool got=false;
    while(std::getline(lines,line))if(line.find(" <= ")!=std::string::npos){
        auto pos=line.find(':');if(pos==std::string::npos)continue;
        std::string fake=" obj: "+line.substr(pos+1,line.find(" <= ")-pos-1)+"\nSubject To\n";
        auto candidate=objective(fake);if(candidate.coefficients==obj.coefficients){c.model_cutoff=std::stod(line.substr(line.find(" <= ")+4))+obj.constant;got=true;break;}}
    c.cutoff=state.root_cutoff;require(got&&std::isfinite(c.model_cutoff)&&std::isfinite(c.cutoff),"source_cutoff_missing");
    std::ostringstream support;support<<std::setprecision(17);
    for(int i=1;i<=instance.V;++i){support<<c.ratios[i]<<':';for(int y:c.support[i])support<<y<<',';support<<';';}
    c.support_sha=textSha256(support.str());
    round141Event("root_count_selected","\"threshold_units\":"+std::string("\"")+integer(c.threshold)+"\",\"threshold_exponent\":"+std::to_string(c.exponent)+
        ",\"ell\":"+std::to_string(c.ell)+",\"u\":"+std::to_string(c.u)+",\"pivot\":"+std::to_string(c.pivot)+",\"K_star\":"+number(double(c.K))+
        ",\"count_range_violation\":"+number(double(best_violation))+",\"rule\":\"max_weighted_remainder_then_lp_floor\",\"root_SHA\":\""+c.root_sha+"\",\"support_SHA\":\""+c.support_sha+"\",\"domain_cutoff\":"+number(c.cutoff)+",\"model_cutoff\":"+number(c.model_cutoff));
    return true;
}
inline std::string round141ScopePayload(const Round141Choice& c,int side) {
    using namespace round141_detail;std::ostringstream s;s<<std::setprecision(17)<<"v1;"<<integer(c.threshold)<<';'<<c.exponent<<';'<<c.pivot<<';'<<side<<';'<<c.ratios.size()-1<<';'<<c.root_sha<<';'<<c.support_sha;
    for(std::size_t i=1;i<c.ratios.size();++i){s<<';'<<c.ratios[i];for(int y:c.support[i])s<<','<<y;}return s.str();
}
inline std::string round141ScopeValue(const std::string& settings) {
    const std::string key="\"round141_count_scope\":\"";auto start=settings.find(key);if(start==std::string::npos)return "";
    auto end=settings.find('"',start+key.size());round141_detail::require(end!=std::string::npos,"count_scope_malformed");return settings.substr(start+key.size(),end-start-key.size());
}
inline bool round141ScopeContains(const std::string& value,const std::vector<int>& y) {
    using namespace round141_detail;if(value.empty())return true;auto a=split(value,';');require(a.size()>=8&&a[0]=="v1","count_scope_schema");
    Round141Choice c;c.threshold=integer(a[1]);c.exponent=std::stoi(a[2]);c.pivot=std::stoi(a[3]);int side=std::stoi(a[4]),n=std::stoi(a[5]);
    require((side==0||side==1)&&n>0&&a.size()==std::size_t(n+8)&&a[6].size()==64&&a[7].size()==64,"count_scope_shape");
    require(y.empty()||y.size()==std::size_t(n+1),"count_scope_witness_shape");c.ratios.resize(n+1);c.support.resize(n+1);
    for(int i=1;i<=n;++i){auto row=split(a[i+7],',');require(row.size()>1,"count_scope_support");c.ratios[i]=std::stod(row[0]);
        for(std::size_t k=1;k<row.size();++k)c.support[i].push_back(std::stoi(row[k]));
        require(std::isfinite(c.ratios[i])&&c.ratios[i]>0&&std::is_sorted(c.support[i].begin(),c.support[i].end()),"count_scope_ratio_or_support");}
    if(y.empty())return true;
    for(int i=1;i<=n;++i)if(!std::binary_search(c.support[i].begin(),c.support[i].end(),y[i]))return false;
    int K=round141Count(c,y);return side==0?K<=c.pivot:K>=c.pivot+1;
}
inline CanonicalCompactModelArtifact round141Append(const CanonicalCompactModelArtifact& base,
    std::vector<round141_detail::Row> rows,const std::filesystem::path& path,bool binary,const std::string& scope) {
    using namespace round141_detail;require(base.written&&fileSha256(base.path)==base.sha256&&!std::filesystem::exists(path),"append_identity_or_collision");
    std::string text=material(base.path),added;long long nz=0;for(const auto& r:rows){added+=emit(r);for(const auto& term:r.coefficients)nz+=term.second!=0;}
    auto bounds=text.find("Bounds\n");require(bounds!=std::string::npos,"bounds_missing");text.insert(bounds,added);
    if(binary){require(text.find("r141_b")==added.find("r141_b")+bounds,"duplicate_binary");auto bi=text.find("Binaries\n");require(bi!=std::string::npos,"binary_section_missing");text.insert(bi+9," r141_b\n");text.insert(text.find("Bounds\n")+7," 0 <= r141_b <= 1\n");}
    std::ofstream f(path,std::ios::binary);f<<text;f.close();require(bool(f),"append_write");auto out=base;out.path=path;out.sha256=fileSha256(path);
    out.row_signature+="|round141:"+out.sha256;out.model_scope+="_round141_"+scope;out.rows+=rows.size();out.columns+=binary?1:0;out.nonzeros+=nz;
    round141().expected[out.sha256]=std::move(rows);return out;
}
inline CanonicalCompactModelArtifact round141Probe(const Instance& instance,int side,const std::filesystem::path& path) {
    using namespace round141_detail;using namespace round140_detail;const auto& c=round141().choice;const auto& base=round141().root_artifact;
    std::vector<Row> rows;Row count;count.name="r141_count_side";count.sense=side==0?'<':'>';count.rhs=c.pivot+(side==1);
    for(const auto& name:round141Membership(c,c.support))count.coefficients[name]=1;rows.push_back(count);
    long long B=0,Q=0;for(int i=1;i<=instance.V;++i)B+=instance.initial[i];for(int q:instance.Q)Q+=q;
    const auto g=grid(c.support,c.ratios,std::max(0LL,B-Q),B);std::map<std::string,Int> coefficients;Int constant=0;
    for(auto r:g.rows){if(side==0&&r.t>=c.threshold)r.u=std::min(r.u,c.pivot);if(side==1&&r.t<=c.threshold)r.ell=std::max(r.ell,c.pivot+1);
        require(r.ell<=r.u,"incompatible_propagated_interval");Round141Choice temp=c;temp.threshold=r.t;
        for(const auto& name:round141Membership(temp,c.support))coefficients[name]=add(coefficients[name],mul(r.delta,instance.V-r.ell-r.u));constant=add(constant,mul(r.delta,static_cast<Int>(r.ell)*r.u));}
    Row chord;chord.name="r141_child_TC2";chord.rhs=down(constant,g.exponent);
    for(int i=1;i<=instance.V;++i)for(int j=i+1;j<=instance.V;++j)chord.coefficients["h_"+std::to_string(i)+"_"+std::to_string(j)]=1;
    for(const auto& [name,value]:coefficients)if(value)chord.coefficients[name]=-down(value,g.exponent);
    double smallest=1;for(const auto& [name,value]:chord.coefficients){(void)name;if(value)smallest=std::min(smallest,std::fabs(value));}int exponent=0;while(std::ldexp(smallest,exponent)<1e-12)++exponent;
    for(auto& term:chord.coefficients)term.second=std::ldexp(term.second,exponent);chord.rhs=std::ldexp(chord.rhs,exponent);rows.push_back(chord);
    return round141Append(base,std::move(rows),path,false,side==0?"count_low":"count_high");
}
inline bool round141Contains(const Round141Choice& c,const CanonicalCompactModelArtifact& base,double cutoff) {
    if(!base.interval_restricted||base.gamma_L<c.a||base.gamma_U>c.z||cutoff>c.cutoff)return false;
    auto s=round141_detail::supports(round141_detail::material(base.path),int(c.support.size())-1);
    for(std::size_t i=1;i<s.size();++i)for(int y:s[i])if(!std::binary_search(c.support[i].begin(),c.support[i].end(),y))return false;return true;
}
inline CanonicalCompactModelArtifact round141Embed(const CanonicalCompactModelArtifact& base,double cutoff,const std::filesystem::path& path) {
    using namespace round141_detail;const auto& c=round141().choice;require(round141().ready&&round141Contains(c,base,cutoff),"embedding_outside_source_domain");
    auto s=supports(material(base.path),int(c.support.size())-1);Row upper,lower;upper.name="r141_count_upper";upper.sense='<';upper.rhs=c.pivot;
    lower.name="r141_count_lower";lower.rhs=c.ell;
    for(const auto& name:round141Membership(c,s)){upper.coefficients[name]=1;lower.coefficients[name]=1;}
    upper.coefficients["r141_b"]=-(c.u-c.pivot);lower.coefficients["r141_b"]=-(c.pivot+1-c.ell);
    const auto obj=objective(material(base.path));Round120Pair scalar;scalar.a=0;scalar.m=1;scalar.b=2;scalar.beta0=c.beta[0];scalar.beta1=c.beta[1];
    const auto guarded=round120Rows(scalar,round141().mode=="d1",obj.constant);
    Row floor;floor.name="r141_objective_floor";floor.coefficients=obj.coefficients;if(guarded.objective_delta)floor.coefficients["r141_b"]=-guarded.objective_delta;floor.rhs=guarded.objective_base;
    return round141Append(base,{upper,lower,floor},path,true,"embedded_"+round141().mode);
}
}
