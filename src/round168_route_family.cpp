// Offline complete route-family diagnostics. No controller or production feedback.
// All model construction, Starts, decoding, enumeration and research decisions
// in this executable are C++; Python helpers only transport bytes and summarize.
#include "Parser.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "gurobi_c.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
using namespace ebrp;
namespace fs=std::filesystem;
namespace {
using Fleet=std::vector<RoutePlan>;
using Terms=std::map<int,double>;
using Clock=std::chrono::steady_clock;
constexpr double eps=1e-7;
void need(bool p,const std::string& s){if(!p)throw std::runtime_error(s);}
void ck(int e){if(e)throw std::runtime_error("Gurobi API error "+std::to_string(e));}
double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
double unixTime(){return std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();}
std::string key(const std::string& p,int i,int j=-1,int k=-1){return p+"_"+std::to_string(i)+(j<0?"":"_"+std::to_string(j))+(k<0?"":"_"+std::to_string(k));}
template<class T>void array(std::ostream& f,const std::vector<T>& a){f<<'[';for(size_t j=0;j<a.size();++j){if(j)f<<',';f<<a[j];}f<<']';}
void number(std::ostream& f,double a){if(std::isfinite(a)&&std::abs(a)<1e90)f<<a;else f<<"null";}
void strings(std::ostream& f,const std::vector<std::string>& a){f<<'[';for(size_t j=0;j<a.size();++j){if(j)f<<',';f<<std::quoted(a[j]);}f<<']';}
Fleet loadFleet(const fs::path& p){
    std::ifstream f(p);int count=0;f>>count;need(count>=0&&count<=100,"fleet count");Fleet out;
    for(int k=0;k<count;++k){RoutePlan r;int n=0;f>>r.vehicle>>n;need(n>=2&&n<10000,"fleet route length");r.nodes.resize(n);for(int& i:r.nodes)f>>i;
        for(int j=1;j+1<n;++j){int d=0;f>>d;r.operations.push_back({r.nodes[j],std::max(0,d),std::max(0,-d)});}out.push_back(r);}
    need(bool(f),"fleet read "+p.string());return out;
}
void saveFleet(const fs::path& p,const Fleet& routes){std::ofstream f(p);f<<routes.size()<<'\n';for(const auto& r:routes){f<<r.vehicle<<' '<<r.nodes.size();for(int i:r.nodes)f<<' '<<i;f<<'\n';for(const auto& op:r.operations)f<<op.pickup-op.drop<<' ';f<<'\n';}}
Fleet canonical(const Instance& in,const Fleet& routes){
    Fleet out(in.M);std::set<int> seen;
    for(int k=0;k<in.M;++k){out[k].vehicle=k;out[k].nodes={0,0};}
    for(auto r:routes){need(r.vehicle>=0&&r.vehicle<in.M&&seen.insert(r.vehicle).second,"duplicate/invalid vehicle");
        need(r.nodes.size()>=2&&r.nodes.front()==0&&r.nodes.back()==0,"depot endpoints");
        need(r.operations.size()+2==r.nodes.size(),"one operation per visit");std::map<int,StopOperation> ops;
        for(auto op:r.operations)need(op.station>0&&op.station<=in.V&&ops.emplace(op.station,op).second,"operation uniqueness");
        r.operations.clear();for(size_t j=1;j+1<r.nodes.size();++j){need(ops.count(r.nodes[j]),"internal depot or missing operation");r.operations.push_back(ops.at(r.nodes[j]));}
        out[r.vehicle]=r;}
    return out;
}
Verification physical(const Instance& in,const Fleet& routes,double lambda){return verifySolution(in,canonical(in,routes),lambda);}
void fleetJSON(std::ostream& f,const Instance& in,const Fleet& fleet,double lambda){
    const auto routes=canonical(in,fleet);const auto v=physical(in,routes,lambda);
    f<<std::setprecision(17)<<std::boolalpha<<"{\"feasible\":"<<v.feasible<<",\"F\":"<<v.objective<<",\"G\":"<<v.G<<",\"P\":"<<v.P<<",\"Y\":";array(f,v.final_inventory);
    f<<",\"errors\":";strings(f,v.errors);f<<",\"routes\":[";
    for(int k=0;k<in.M;++k){if(k)f<<',';const auto& r=routes[k];int load=0,maxload=0,pick=0,drop=0;std::vector<int> prefixes;
        for(auto op:r.operations){pick+=op.pickup;drop+=op.drop;load+=op.pickup-op.drop;maxload=std::max(maxload,load);prefixes.push_back(load);}
        f<<"{\"vehicle\":"<<k<<",\"nodes\":";array(f,r.nodes);f<<",\"operations\":[";
        for(size_t j=0;j<r.operations.size();++j){if(j)f<<',';auto op=r.operations[j];f<<"{\"station\":"<<op.station<<",\"pickup\":"<<op.pickup<<",\"drop\":"<<op.drop<<'}';}
        f<<"],\"prefix_loads\":";array(f,prefixes);f<<",\"return_load\":"<<load<<",\"max_prefix_load\":"<<maxload<<",\"pickup\":"<<pick<<",\"station_drop\":"<<drop<<",\"travel\":"<<v.route_travel_time[k]<<",\"handling_including_return\":"<<v.route_operation_time[k]<<",\"duration\":"<<v.route_duration[k]<<'}';}
    f<<"]}";
}
struct Record{std::string id,inputId,method,inputPath,fleetPath,inputSHA,fleetSHA;int seed=0;double T=0,lambda=0,tp=0,td=0,expected=0;Instance in;Fleet fleet;Verification checked;};
std::vector<Record> pool(const fs::path& p){
    std::ifstream f(p);std::vector<Record> out;Record r;
    while(f>>r.id>>r.inputId>>r.seed>>r.method>>std::quoted(r.inputPath)>>r.T>>r.lambda>>r.tp>>r.td>>std::quoted(r.fleetPath)>>r.expected>>r.inputSHA>>r.fleetSHA){
        need(fileSha256(r.inputPath)==r.inputSHA&&fileSha256(r.fleetPath)==r.fleetSHA,"pool input/fleet fingerprint");
        r.in=parseInstanceFile(r.inputPath,r.T,r.tp,r.td);r.fleet=canonical(r.in,loadFleet(r.fleetPath));r.checked=physical(r.in,r.fleet,r.lambda);
        need(r.checked.feasible,"unqualified archive "+r.id);need(std::abs(r.expected-r.checked.objective)<=eps,"archive F mismatch "+r.id);out.push_back(r);}
    need(f.eof()&&!out.empty(),"pool parse");return out;
}
struct Family{std::vector<std::vector<int>> pi;std::vector<int> owner;};
Family family(const Instance& in,const Fleet& parent){Family a;a.pi.resize(in.M);a.owner.assign(in.V+1,-1);for(auto r:canonical(in,parent))for(auto op:r.operations){need(op.pickup+op.drop>0,"zero parent operation");a.pi[r.vehicle].push_back(op.station);need(a.owner[op.station]<0,"duplicate parent station");a.owner[op.station]=r.vehicle;}return a;}
bool member(const Instance& in,const Family& a,const Fleet& cand,const std::string& scope){
    auto routes=canonical(in,cand);
    for(auto r:routes){int previous=-1;for(int i:r.nodes)if(i){if(a.owner[i]<0)return false;if(scope!="eligible"&&a.owner[i]!=r.vehicle)return false;
            if(scope=="order"){auto it=std::find(a.pi[r.vehicle].begin(),a.pi[r.vehicle].end(),i);int pos=static_cast<int>(it-a.pi[r.vehicle].begin());if(pos<=previous)return false;previous=pos;}}}return true;
}
bool relabelMember(const Instance& in,const Family& a,const Fleet& fleet,const std::string& scope,Fleet& mapped,std::vector<int>& labels){
    labels.resize(in.M);std::iota(labels.begin(),labels.end(),0);do{bool legal=true;for(int k=0;k<in.M;++k)legal=legal&&in.Q[k]==in.Q[labels[k]];if(!legal)continue;
        mapped=fleet;for(auto& r:mapped)r.vehicle=labels[r.vehicle];mapped=canonical(in,mapped);if(member(in,a,mapped,scope))return true;
    }while(std::next_permutation(labels.begin(),labels.end()));return false;
}
Fleet embed(const Instance& in,const Family& a,const std::vector<int>& y){Fleet out(in.M);for(int k=0;k<in.M;++k){auto& r=out[k];r.vehicle=k;r.nodes={0};for(int i:a.pi[k])if(y[i]!=in.initial[i]){int d=in.initial[i]-y[i];r.nodes.push_back(i);r.operations.push_back({i,std::max(0,d),std::max(0,-d)});}r.nodes.push_back(0);}return out;}
struct Position{const Record* parent;std::string scope,id;};
std::vector<Position> positions(const std::vector<Record>& records){
    std::vector<Position> out;for(const auto& alias:{"R163-C35-U","R163-B35-S","R163-X35-S"})for(int seed=0;seed<3;++seed){auto it=std::find_if(records.begin(),records.end(),[&](const Record& r){return r.inputId==alias&&r.seed==seed&&r.method=="B";});need(it!=records.end(),"missing parent");
        out.push_back({&*it,"order",std::string(alias)+"_S"+std::to_string(seed)+"_order"});if(std::string(alias)=="R163-C35-U"&&seed==0)for(const auto& scope:{"owner","eligible"})out.push_back({&*it,scope,std::string(alias)+"_S0_"+scope});}return out;
}
std::string familyIdentity(const Record& r,const std::string& scope,const fs::path& dest){std::ofstream f(dest);f<<std::setprecision(17)<<r.inputSHA<<' '<<r.T<<' '<<r.lambda<<' '<<r.tp<<' '<<r.td<<' '<<scope<<'\n';array(f,r.in.Q);const auto a=family(r.in,r.fleet);for(auto seq:a.pi){f<<'\n';if(scope=="owner")std::sort(seq.begin(),seq.end());array(f,seq);}f.close();return fileSha256(dest);}
double target(const std::vector<Record>& records,const std::string& alias){double tau=std::numeric_limits<double>::infinity();int count=0;for(auto& r:records)if(r.inputId==alias){++count;tau=std::min(tau,r.checked.objective);}need(count==6,"closed six-fleet target pool");return tau;}
void preflight(const fs::path& index,const fs::path& out){
    const auto begin=Clock::now();need(fs::create_directories(out),"exclusive preflight directory");auto records=pool(index);
    std::ofstream tj(out/"target_manifest.json");tj<<std::setprecision(17)<<"{\"schema\":\"round168-frozen-targets-v1\",\"Optimize_before_freeze\":0,\"comparison_epsilon\":1e-7,\"pool_SHA256\":"<<std::quoted(fileSha256(index))<<",\"targets\":[";bool comma=false;
    for(const auto& alias:{"R163-C35-U","R163-B35-S","R163-X35-S"}){if(comma)tj<<',';comma=true;double tau=target(records,alias);tj<<"{\"input_id\":"<<std::quoted(alias)<<",\"tau\":"<<tau<<",\"theta\":"<<tau+eps<<",\"records\":[";bool c=false;
        for(auto& r:records)if(r.inputId==alias){if(c)tj<<',';c=true;tj<<"{\"run\":"<<std::quoted(r.id)<<",\"input_SHA256\":"<<std::quoted(r.inputSHA)<<",\"fleet_SHA256\":"<<std::quoted(r.fleetSHA)<<",\"parameter_T\":"<<r.T<<",\"lambda\":"<<r.lambda<<",\"physical\":";fleetJSON(tj,r.in,r.fleet,r.lambda);tj<<'}';}tj<<"]}";}tj<<"]}\n";
    std::ofstream f(out/"family_manifest.json");f<<std::setprecision(17)<<std::boolalpha<<"{\"schema\":\"round168-frozen-families-v1\",\"original_global_bound\":false,\"Optimize_before_freeze\":0,\"inventory_support\":\"all 0..C on E; b outside E\",\"g_domain\":[0,1],\"target_cutoff_row\":false,\"parameters\":{\"Threads\":1,\"Seed\":0,\"MIPGap\":0,\"MIPGapAbs\":0,\"FeasibilityTol\":1e-6,\"IntFeasTol\":1e-5,\"OptimalityTol\":1e-6},\"bound_guard\":1e-7,\"physical_time_tolerance\":1e-7,\"qualification\":\"complete-family model and finalized finite bound, accepted status 2/9/11/15, bound<=physical U+1e-7; subtract 1e-7 and round downward; objective nonnegativity floor zero\",\"substantive_call_cap\":9,\"per_family_Native_cap\":300,\"tiny_call_cap\":10,\"diagnostic_outer_cap\":5400,\"positions\":[";
    std::set<std::string> unique;int freeHits=0;bool first=true;
    for(const auto& pos:positions(records)){const auto& r=*pos.parent;const auto a=family(r.in,r.fleet);const auto tau=target(records,r.inputId);const auto theta=tau+eps;
        if(!first)f<<',';first=false;const auto id=familyIdentity(r,pos.scope,out/(pos.id+".identity"));bool duplicate=!unique.insert(id).second;
        f<<"{\"position\":"<<std::quoted(pos.id)<<",\"parent\":"<<std::quoted(r.id)<<",\"scope\":"<<std::quoted(pos.scope)<<",\"family_SHA256\":"<<std::quoted(id)<<",\"duplicate\":"<<duplicate<<",\"parent_F\":"<<r.checked.objective<<",\"tau\":"<<tau<<",\"theta\":"<<theta<<",\"pi\":[";
        for(int k=0;k<r.in.M;++k){if(k)f<<',';array(f,a.pi[k]);}f<<"],\"outside_E\":[";bool c=false;for(int i=1;i<=r.in.V;++i)if(a.owner[i]<0){if(c)f<<',';c=true;f<<i;}f<<"],\"target_checks\":[";
        bool hit=false;Fleet witness;std::string source;bool cc=false;
        for(const auto& ref:records)if(ref.inputId==r.inputId&&ref.checked.objective<=theta){
            if(cc)f<<',';cc=true;need(ref.inputSHA==r.inputSHA&&ref.T==r.T&&ref.lambda==r.lambda&&ref.in.Q==r.in.Q&&ref.tp==r.tp&&ref.td==r.td,"target physical parameter identity");Fleet mapped;std::vector<int> labels;bool direct=relabelMember(r.in,a,ref.fleet,pos.scope,mapped,labels);if(direct&&!hit){hit=true;witness=mapped;source=ref.id+":direct";}
            std::vector<int> outside;for(int i=1;i<=r.in.V;++i)if(a.owner[i]<0&&ref.checked.final_inventory[i]!=r.in.initial[i])outside.push_back(i);
            auto embedded=embed(r.in,a,ref.checked.final_inventory);auto v=physical(r.in,embedded,r.lambda);bool embeddedOK=outside.empty()&&v.feasible;
            if(embeddedOK&&!hit){hit=true;witness=embedded;source=ref.id+":inventory_embedding";}
            f<<"{\"source\":"<<std::quoted(ref.id)<<",\"direct_member_up_to_compatible_relabel\":"<<direct<<",\"relabel\":";array(f,labels);f<<",\"inventory_embedding_feasible\":"<<embeddedOK<<",\"outside_inventory_changes\":";array(f,outside);f<<",\"embedded_physical\":";fleetJSON(f,r.in,embedded,r.lambda);f<<'}';}
        f<<"],\"free_HIT\":"<<hit<<",\"free_source\":"<<std::quoted(source)<<",\"start_parent\":"<<std::quoted(r.id)<<'}';
        if(hit){++freeHits;saveFleet(out/(pos.id+"_free.fleet"),witness);}
    }f<<"],\"unique_positions\":"<<unique.size()<<",\"free_HIT_positions\":"<<freeHits<<",\"outer_seconds\":"<<seconds(begin)<<"}\n";
    std::cout<<"Preflight: 18 physical fleets; "<<unique.size()<<" unique positions; "<<freeHits<<" free HITs; zero Optimize\n";
}

// Minimal C-API matrix builder. Row audit reads back the ACTUAL Gurobi matrix.
struct Model{
    GRBenv* env=nullptr;GRBmodel* model=nullptr;int n=0;std::map<std::string,int> ix;std::vector<std::string> names;
    Model(){ck(GRBemptyenv(&env));ck(GRBsetintparam(env,"OutputFlag",0));ck(GRBstartenv(env));ck(GRBnewmodel(env,&model,"Round168_restricted_family",0,nullptr,nullptr,nullptr,nullptr,nullptr));}
    ~Model(){if(model)GRBfreemodel(model);if(env)GRBfreeenv(env);}
    int var(const std::string& name,double lo=0,double hi=GRB_INFINITY,char type='C',double obj=0){need(!ix.count(name),"duplicate column");ck(GRBaddvar(model,0,nullptr,nullptr,obj,lo,hi,type,name.c_str()));ix[name]=n;names.push_back(name);return n++;}
    int col(const std::string& name)const{auto it=ix.find(name);need(it!=ix.end(),"unmapped column "+name);return it->second;}
    void row(const Terms& terms,char sense,double rhs,const std::string& name){std::vector<int> j;std::vector<double> a;for(auto t:terms)if(t.second){j.push_back(t.first);a.push_back(t.second);}ck(GRBaddconstr(model,static_cast<int>(j.size()),j.data(),a.data(),sense,rhs,name.c_str()));}
    double attr(const char* name,int j){double a;ck(GRBgetdblattrelement(model,name,j,&a));return a;}
    double audit(const std::vector<double>& x,double* objective=nullptr){ck(GRBupdatemodel(model));need(x.size()==static_cast<size_t>(n),"incomplete vector");double residual=0,obj=0;int nr;ck(GRBgetintattr(model,"NumConstrs",&nr));
        for(int j=0;j<n;++j){char type;ck(GRBgetcharattrelement(model,"VType",j,&type));residual=std::max({residual,attr("LB",j)-x[j],x[j]-attr("UB",j)});if(type!='C')residual=std::max(residual,std::abs(x[j]-std::round(x[j])));obj+=x[j]*attr("Obj",j);}
        for(int r=0;r<nr;++r){int nz=0,start=0;ck(GRBgetconstrs(model,&nz,nullptr,nullptr,nullptr,r,1));std::vector<int> j(nz);std::vector<double> a(nz);ck(GRBgetconstrs(model,&nz,&start,j.data(),a.data(),r,1));char sense;ck(GRBgetcharattrelement(model,"Sense",r,&sense));double lhs=0;for(int t=0;t<nz;++t)lhs+=a[t]*x[j[t]];double rhs=attr("RHS",r);residual=std::max(residual,sense=='='?std::abs(lhs-rhs):sense=='<'?lhs-rhs:rhs-lhs);}
        if(objective)*objective=obj;return residual;
    }
};
struct Arc{int k,a,b,x,load=-1;};
struct Built{
    Model m;const Instance& in;double lambda;Family fam;std::string scope;std::vector<std::vector<int>> supports;std::vector<Arc> arcs;
    Built(const Instance& data,double lam,const Fleet& parent,const std::string& sc):in(data),lambda(lam),fam(family(in,parent)),scope(sc){
        need(scope=="order"||scope=="owner"||scope=="eligible","invalid scope");need(lambda>=0,"nonnegative lambda");
        const int g=m.var("G",0,1,'C',1);supports.resize(in.V+1);Terms gini;
        for(int i=1;i<=in.V;++i){need(in.weights[i]>=0&&in.target[i]>0,"legal target and weight");if(fam.owner[i]>=0)for(int y=0;y<=in.capacity[i];++y)supports[i].push_back(y);else supports[i]={in.initial[i]};
            int r=m.var(key("r",i),0,static_cast<double>(in.capacity[i])/in.target[i]);int e=m.var(key("e",i),0,GRB_INFINITY,'C',lambda*in.weights[i]);Terms mass,qsum{{g,-1}},ratio{{r,1}};
            for(int y:supports[i]){int s=m.var(key("s",i,y),0,1,'B'),q=m.var(key("q",i,y),0,1);mass[s]=1;qsum[q]=1;ratio[s]=-static_cast<double>(y)/in.target[i];
                m.row({{q,1},{s,-1}},'<',0,key("q_le_s",i,y));m.row({{q,1},{g,-1}},'<',0,key("q_le_g",i,y));m.row({{q,1},{g,-1},{s,-1}},'>',-1,key("q_ge_gs",i,y));gini[q]=-static_cast<double>(in.V)*y/in.target[i];}
            m.row(mass,'=',1,key("one_stock",i));m.row(qsum,'=',0,key("common_G",i));m.row(ratio,'=',0,key("ratio",i));m.row({{e,1},{r,-1}},'>',-1,key("penalty_plus",i));m.row({{e,1},{r,1}},'>',1,key("penalty_minus",i));
        }
        for(int i=1;i<=in.V;++i)for(int j=i+1;j<=in.V;++j){int h=m.var(key("h",i,j));gini[h]=1;int ri=m.col(key("r",i)),rj=m.col(key("r",j));m.row({{h,1},{ri,-1},{rj,1}},'>',0,key("abs_plus",i,j));m.row({{h,1},{ri,1},{rj,-1}},'>',0,key("abs_minus",i,j));}
        m.row(gini,'<',0,"whole_system_true_Gini_epigraph");
        for(int i=1;i<=in.V;++i)if(fam.owner[i]>=0){Terms visit{{m.col(key("s",i,in.initial[i])),1}},pick,drop;
            for(int y:supports[i]){pick[m.col(key("s",i,y))]=-std::max(0,in.initial[i]-y);drop[m.col(key("s",i,y))]=-std::max(0,y-in.initial[i]);}
            for(int k=0;k<in.M;++k)if(scope=="eligible"||fam.owner[i]==k){int z=m.var(key("z",k,i),0,1,'B'),p=m.var(key("p",k,i),0,in.initial[i]),d=m.var(key("d",k,i),0,in.capacity[i]-in.initial[i]);visit[z]=1;pick[p]=1;drop[d]=1;
                m.row({{p,1},{z,-static_cast<double>(in.initial[i])}},'<',0,key("pickup_visit",k,i));m.row({{d,1},{z,-static_cast<double>(in.capacity[i]-in.initial[i])}},'<',0,key("drop_visit",k,i));}
            m.row(visit,'=',1,key("optional_nonzero",i));m.row(pick,'=',0,key("stock_pickup",i));m.row(drop,'=',0,key("stock_drop",i));}
        const int sink=in.V+1;
        for(int k=0;k<in.M;++k){std::vector<int> nodes=fam.pi[k];if(scope=="eligible"){nodes.clear();for(int i=1;i<=in.V;++i)if(fam.owner[i]>=0)nodes.push_back(i);}
            std::map<int,Terms> incoming,outgoing,loadBalance;Terms source,sinkrow,time;
            auto add=[&](int a,int b){int x=m.var(key("a",k,a,b),0,1,'B');Arc arc{k,a,b,x,-1};outgoing[a][x]=1;incoming[b][x]=1;if(a==0)source[x]=1;if(b==sink)sinkrow[x]=1;time[x]=in.dist[a==sink?0:a][b==sink?0:b];
                if(scope!="order"){arc.load=m.var(key("load",k,a,b),0,a==0?0:in.Q[k]);m.row({{arc.load,1},{x,-static_cast<double>(in.Q[k])}},'<',0,key("arc_capacity",k,a,b));loadBalance[a][arc.load]+=1;loadBalance[b][arc.load]-=1;}
                arcs.push_back(arc);};
            add(0,sink);for(int i:nodes){add(0,i);add(i,sink);}
            if(scope=="order"){for(size_t a=0;a<nodes.size();++a)for(size_t b=a+1;b<nodes.size();++b)add(nodes[a],nodes[b]);}
            else {for(int i:nodes)for(int j:nodes)if(i!=j)add(i,j);}
            m.row(source,'=',1,key("source",k));m.row(sinkrow,'=',1,key("sink",k));Terms prefix;
            for(int i:nodes){int z=m.col(key("z",k,i)),p=m.col(key("p",k,i)),d=m.col(key("d",k,i));incoming[i][z]=-1;outgoing[i][z]=-1;m.row(incoming[i],'=',0,key("in_degree",k,i));m.row(outgoing[i],'=',0,key("out_degree",k,i));time[p]=in.pickup_time+in.drop_time;
                if(scope=="order"){prefix[p]=1;prefix[d]=-1;m.row(prefix,'>',0,key("prefix_min",k,i));m.row(prefix,'<',in.Q[k],key("prefix_max",k,i));}
                else{loadBalance[i][p]=-1;loadBalance[i][d]=1;m.row(loadBalance[i],'=',0,key("load_balance",k,i));int rank=m.var(key("rank",k,i),0,nodes.size());m.row({{rank,1},{z,-1}},'>',0,key("rank_min",k,i));m.row({{rank,1},{z,-static_cast<double>(nodes.size())}},'<',0,key("rank_max",k,i));}}
            if(scope!="order")for(const auto& a:arcs)if(a.k==k&&a.a&&a.b!=sink){double big=nodes.size()+1;m.row({{m.col(key("rank",k,a.b)),1},{m.col(key("rank",k,a.a)),-1},{a.x,-big}},'>',1-big,key("acyclic",k,a.a,a.b));}
            m.row(time,'<',in.total_time_limit,key("full_travel_and_handling",k));}
        ck(GRBupdatemodel(m.model));
    }
    std::vector<double> map(const Fleet& input){
        auto routes=canonical(in,input);need(member(in,fam,routes,scope),"fleet outside "+scope);const auto v=physical(in,routes,lambda);need(v.feasible,"map requires physical fleet");std::vector<double> x(m.n);x[m.col("G")]=v.G;
        auto set=[&](const std::string& name,double a){x[m.col(name)]=a;};
        for(int i=1;i<=in.V;++i){int y=v.final_inventory[i];need(std::find(supports[i].begin(),supports[i].end(),y)!=supports[i].end(),"stock outside support");set(key("s",i,y),1);set(key("q",i,y),v.G);double r=static_cast<double>(y)/in.target[i];set(key("r",i),r);set(key("e",i),std::abs(r-1));}
        for(int i=1;i<=in.V;++i)for(int j=i+1;j<=in.V;++j)set(key("h",i,j),std::abs(x[m.col(key("r",i))]-x[m.col(key("r",j))]));
        for(auto r:routes){int load=0;std::map<int,int> after;for(size_t t=0;t<r.operations.size();++t){auto op=r.operations[t];set(key("z",r.vehicle,op.station),1);set(key("p",r.vehicle,op.station),op.pickup);set(key("d",r.vehicle,op.station),op.drop);load+=op.pickup-op.drop;after[op.station]=load;if(scope!="order")set(key("rank",r.vehicle,op.station),t+1);}
            for(size_t j=1;j<r.nodes.size();++j){int a=r.nodes[j-1],b=r.nodes[j]?r.nodes[j]:in.V+1;set(key("a",r.vehicle,a,b),1);if(scope!="order")set(key("load",r.vehicle,a,b),a?after[a]:0);}}
        return x;
    }
    Fleet decode(const std::vector<double>& x)const{
        std::vector<int> y=in.initial;for(int i=1;i<=in.V;++i){int count=0;for(int v:supports[i])if(x[m.col(key("s",i,v))]>.5){y[i]=v;++count;}need(count==1,"decode unique stock");}
        Fleet out(in.M);for(int k=0;k<in.M;++k){auto& r=out[k];r.vehicle=k;r.nodes={0};int node=0;std::set<int> seen;while(node!=in.V+1){int next=-1,count=0;for(auto a:arcs)if(a.k==k&&a.a==node&&x[a.x]>.5){next=a.b;++count;}need(count==1,"decode degree");if(next==in.V+1){r.nodes.push_back(0);node=next;break;}need(next>0&&next<=in.V&&seen.insert(next).second,"decode cycle");need(y[next]!=in.initial[next],"decode zero service");int d=in.initial[next]-y[next];r.nodes.push_back(next);r.operations.push_back({next,std::max(0,d),std::max(0,-d)});node=next;}
        }need(member(in,fam,out,scope),"decoded membership");need(physical(in,out,lambda).feasible,"decoded physical infeasibility");return out;
    }
};
void start(Built& b,const Fleet& fleet,const fs::path& out){auto x=b.map(fleet);double obj=0;double residual=b.m.audit(x,&obj);double F=physical(b.in,fleet,b.lambda).objective;need(residual<=eps&&std::abs(obj-F)<=eps,"Start actual row/type/objective gate");
    std::ofstream f(out/"start_check.json");f<<std::setprecision(17)<<"{\"complete\":true,\"actual_columns\":"<<b.m.n<<",\"max_row_bound_type_residual\":"<<residual<<",\"model_F\":"<<obj<<",\"physical_F\":"<<F<<"}\n";
    std::ofstream v(out/"start.csv");v<<"name,value\n"<<std::setprecision(17);for(int j=0;j<b.m.n;++j)v<<b.m.names[j]<<','<<x[j]<<'\n';ck(GRBsetdblattrarray(b.m.model,"Start",0,b.m.n,x.data()));ck(GRBwrite(b.m.model,(out/"start.mst").string().c_str()));
    auto decoded=b.decode(x);need(physical(b.in,decoded,b.lambda).final_inventory==physical(b.in,fleet,b.lambda).final_inventory,"Start reverse decoding");
}
struct Callback{Built* b;double theta,parentF;bool stopEvidence=false,hit=false,excluded=false;Fleet witness;std::string failure;};
int __stdcall callback(GRBmodel* model,void* data,int where,void* user){auto& c=*static_cast<Callback*>(user);if(!c.stopEvidence)return 0;
    try{if(where==GRB_CB_MIPSOL){std::vector<double>x(c.b->m.n);ck(GRBcbget(data,where,GRB_CB_MIPSOL_SOL,x.data()));try{auto w=c.b->decode(x);if(physical(c.b->in,w,c.b->lambda).objective<=c.theta){c.witness=w;c.hit=true;GRBterminate(model);}}catch(const std::exception&){/* A toleranced candidate is not a physical HIT. */}}
        if(where==GRB_CB_MIP&&!c.hit){double bound=0;ck(GRBcbget(data,where,GRB_CB_MIP_OBJBND,&bound));if(std::isfinite(bound)&&std::abs(bound)<1e90&&bound<=c.parentF+eps&&std::nextafter(bound-eps,-INFINITY)>c.theta){c.excluded=true;GRBterminate(model);}}
    }catch(const std::exception& e){c.failure=e.what();GRBterminate(model);}return 0;
}
struct Outcome{double rawBound=-INFINITY,L=0,U=INFINITY,runtime=0,work=0,outer=0;int status=0,columns=0,rows=0;bool qualified=false;std::string verdict,source,origin;Fleet fleet;};
Outcome solveOne(const Instance& in,double lambda,const Fleet& parent,const std::string& scope,double tau,double cap,const fs::path& out,const std::string& callid,bool tiny){
    const auto begin=Clock::now();need(fs::create_directories(out),"exclusive solve directory");Built b(in,lambda,parent,scope);start(b,parent,out);ck(GRBwrite(b.m.model,(out/"model.lp").string().c_str()));std::string modelSHA=fileSha256(out/"model.lp");const auto parentV=physical(in,parent,lambda);
    GRBenv* env=GRBgetenv(b.m.model);ck(GRBsetintparam(env,"OutputFlag",1));ck(GRBsetintparam(env,"LogToConsole",0));ck(GRBsetstrparam(env,"LogFile",(out/"native.log").string().c_str()));ck(GRBsetintparam(env,"Threads",1));ck(GRBsetintparam(env,"Seed",0));ck(GRBsetdblparam(env,"MIPGap",0));ck(GRBsetdblparam(env,"MIPGapAbs",0));ck(GRBsetdblparam(env,"TimeLimit",cap));
    std::ofstream params(out/"parameters.json");params<<std::setprecision(17)<<'{';bool first=true;for(const char* name:{"Threads","Seed","Method","Presolve","MIPFocus","Cuts"}){int v;ck(GRBgetintparam(env,name,&v));if(!first)params<<',';first=false;params<<std::quoted(name)<<':'<<v;}for(const char* name:{"MIPGap","MIPGapAbs","TimeLimit","FeasibilityTol","IntFeasTol","OptimalityTol"}){double v;ck(GRBgetdblparam(env,name,&v));params<<','<<std::quoted(name)<<':'<<v;}params<<"}\n";params.close();ck(GRBwriteparams(env,(out/"native.prm").string().c_str()));
    Callback cb{&b,tau+eps,parentV.objective,!tiny};ck(GRBsetcallbackfunc(b.m.model,callback,&cb));
    int nr,nz,ni;ck(GRBgetintattr(b.m.model,"NumConstrs",&nr));ck(GRBgetintattr(b.m.model,"NumNZs",&nz));ck(GRBgetintattr(b.m.model,"NumIntVars",&ni));
    std::ofstream ledger(out/"Optimize.jsonl");ledger<<std::setprecision(17)<<"{\"phase\":\"begin\",\"call_id\":"<<std::quoted(callid)<<",\"unix\":"<<unixTime()<<",\"tiny\":"<<(tiny?"true":"false")<<",\"scope\":"<<std::quoted(scope)<<",\"cap\":"<<cap<<",\"model_SHA256\":"<<std::quoted(modelSHA)<<"}\n";ledger.flush();const int api=GRBoptimize(b.m.model);ledger<<"{\"phase\":\"end\",\"call_id\":"<<std::quoted(callid)<<",\"unix\":"<<unixTime()<<",\"api_return\":"<<api<<"}\n";ledger.flush();ck(api);need(cb.failure.empty(),cb.failure);
    int status,count;double runtime,work,bound=-INFINITY,modelF=INFINITY,cv=0,bv=0,iv=0;ck(GRBgetintattr(b.m.model,"Status",&status));ck(GRBgetintattr(b.m.model,"SolCount",&count));ck(GRBgetdblattr(b.m.model,"Runtime",&runtime));ck(GRBgetdblattr(b.m.model,"Work",&work));ck(GRBgetdblattr(b.m.model,"ObjBound",&bound));
    Fleet best=parent;double U=parentV.objective,residual=0;std::string solutionError;
    if(cb.hit){const auto v=physical(in,cb.witness,lambda);if(v.objective<U){best=cb.witness;U=v.objective;}}
    if(count){ck(GRBgetdblattr(b.m.model,"ObjVal",&modelF));ck(GRBgetdblattr(b.m.model,"ConstrVio",&cv));ck(GRBgetdblattr(b.m.model,"BoundVio",&bv));ck(GRBgetdblattr(b.m.model,"IntVio",&iv));std::vector<double>x(b.m.n);ck(GRBgetdblattrarray(b.m.model,"X",0,b.m.n,x.data()));residual=b.m.audit(x);ck(GRBwrite(b.m.model,(out/"solution.sol").string().c_str()));
        try{auto w=b.decode(x);auto v=physical(in,w,lambda);need(v.objective<=modelF+eps,"epigraph underestimates physical F");if(v.objective<U){best=w;U=v.objective;}}catch(const std::exception& e){solutionError=e.what();}}
    bool qualified=(status==2||status==9||status==11||status==15)&&std::isfinite(bound)&&std::abs(bound)<1e90&&bound<=U+eps
        &&(!count||(std::max({cv,bv,iv,residual})<=eps&&solutionError.empty()))&&fileSha256(out/"model.lp")==modelSHA;
    // A known exact nonnegative objective supplies L=0 even when Native L is unavailable.
    double L=qualified?std::max(0.0,std::nextafter(bound-eps,-INFINITY)):0;
    const auto verdict=U<=tau+eps?"HIT":qualified&&L>tau+eps?"EXCLUDED":"UNKNOWN";
    saveFleet(out/"best.fleet",best);std::ofstream wf(out/"witness.json");fleetJSON(wf,in,best,lambda);wf<<'\n';
    auto mapped=b.map(best);double mappedObj=0;double physicalMapResidual=b.m.audit(mapped,&mappedObj);need(physicalMapResidual<=eps,"best fleet reverse mapping");
    std::ofstream f(out/"result.json");f<<std::setprecision(17)<<std::boolalpha<<"{\"call_id\":"<<std::quoted(callid)<<",\"scope\":"<<std::quoted(scope)<<",\"restricted_scope_nonperformance\":true,\"Optimize\":1,\"tiny\":"<<tiny<<",\"status\":"<<status<<",\"solutions\":"<<count<<",\"tau\":"<<tau<<",\"theta\":"<<tau+eps<<",\"parent_F\":"<<parentV.objective<<",\"raw_bound\":";number(f,bound);f<<",\"safe_L\":"<<L<<",\"bound_qualified\":"<<qualified<<",\"true_U\":"<<U<<",\"model_objective\":";number(f,modelF);f<<",\"verdict\":"<<std::quoted(verdict)<<",\"ConstrVio\":"<<cv<<",\"BoundVio\":"<<bv<<",\"IntVio\":"<<iv<<",\"actual_matrix_residual\":"<<residual<<",\"physical_reverse_map_residual\":"<<physicalMapResidual<<",\"solution_decode_error\":"<<std::quoted(solutionError)<<",\"columns\":"<<b.m.n<<",\"rows\":"<<nr<<",\"nonzeros\":"<<nz<<",\"integer_columns\":"<<ni<<",\"Native_Runtime\":"<<runtime<<",\"Native_Work\":"<<work<<",\"outer_seconds\":"<<seconds(begin)<<",\"model_SHA256\":"<<std::quoted(modelSHA)<<",\"early_HIT\":"<<cb.hit<<",\"early_EXCLUDED\":"<<cb.excluded<<",\"physical\":";fleetJSON(f,in,best,lambda);f<<"}\n";
    if(tiny)need(status==2&&count&&qualified&&std::abs(U-bound)<=eps&&std::abs(U-tau)<=eps&&residual<=eps,"tiny solve numerical/enumeration qualification");std::cout<<callid<<' '<<scope<<' '<<verdict<<" L="<<L<<" U="<<U<<" Native="<<runtime<<std::endl;
    return{bound,L,U,runtime,work,seconds(begin),status,b.m.n,nr,qualified,verdict,callid,"new_solve",best};
}

// Frozen substantive sequence and reuse/propagation are owned by this C++ driver.
// The caller supplies the enclosing diagnostic epoch, which includes tiny MIPs.
void campaign(const fs::path& index,const fs::path& frozen,const fs::path& out,const fs::path& epoch){
    const auto begin=Clock::now();double diagnosticStart=0;{std::ifstream f(epoch);f>>diagnosticStart;need(bool(f),"diagnostic enclosing epoch");}
    need(fs::is_regular_file(frozen/"family_manifest.json")&&fs::is_regular_file(frozen/"target_manifest.json"),"pre-Optimize manifests required");
    need(fs::is_regular_file(out.parent_path()/"tiny_qualification/qualification_PASS.txt"),"six tiny qualifications must pass before substantive queries");
    need(fs::create_directories(out),"exclusive campaign output");auto records=pool(index);auto slots=positions(records);std::vector<Outcome> raw;std::map<std::string,Outcome> seen;
    int calls=0;double runtimeSum=0,workSum=0;std::ofstream stream(out/"positions.jsonl");
    for(const auto& pos:slots){const auto& r=*pos.parent;double tau=target(records,r.inputId),theta=tau+eps;const auto fam=family(r.in,r.fleet);Outcome o;o.U=r.checked.objective;o.fleet=r.fleet;o.origin="parent_upper";o.source=r.id;
        bool found=false;std::vector<int> labels;
        for(const auto& ref:records)if(!found&&ref.inputId==r.inputId&&ref.checked.objective<=theta){Fleet mapped;if(relabelMember(r.in,fam,ref.fleet,pos.scope,mapped,labels)){o.fleet=mapped;o.U=physical(r.in,mapped,r.lambda).objective;o.source=ref.id+":direct";o.origin="archive_witness";found=true;}
            if(!found){bool outsideOK=true;for(int i=1;i<=r.in.V;++i)outsideOK=outsideOK&&(fam.owner[i]>=0||ref.checked.final_inventory[i]==r.in.initial[i]);auto embedded=embed(r.in,fam,ref.checked.final_inventory);if(outsideOK&&physical(r.in,embedded,r.lambda).feasible){o.fleet=embedded;o.U=physical(r.in,embedded,r.lambda).objective;o.source=ref.id+":inventory_embedding";o.origin="archive_embedding";found=true;}}}
        for(size_t j=0;j<raw.size()&&!found;++j)if(slots[j].parent->id==r.id&&raw[j].verdict=="HIT"&&member(r.in,fam,raw[j].fleet,pos.scope)){o=raw[j];o.runtime=o.work=o.outer=0;o.status=o.columns=o.rows=0;o.rawBound=-INFINITY;o.L=0;o.qualified=false;o.origin="witness_reuse";found=true;}
        const auto identity=familyIdentity(r,pos.scope,out/(pos.id+".identity"));
        if(!found&&seen.count(identity)){o=seen.at(identity);o.runtime=o.work=o.outer=0;o.origin="same_family_reuse";found=true;}
        if(found)o.verdict=o.U<=theta?"HIT":o.qualified&&o.L>theta?"EXCLUDED":"UNKNOWN";
        else{need(calls<9,"substantive call count exhausted");need(unixTime()-diagnosticStart+305<5400,"enclosing diagnostic window exhausted");++calls;std::string callid="R168_S"+std::to_string(calls);o=solveOne(r.in,r.lambda,r.fleet,pos.scope,tau,300,out/pos.id,callid,false);runtimeSum+=o.runtime;workSum+=o.work;}
        seen[identity]=o;raw.push_back(o);saveFleet(out/(pos.id+"_witness.fleet"),o.fleet);
        stream<<std::setprecision(17)<<"{\"position\":"<<std::quoted(pos.id)<<",\"verdict\":"<<std::quoted(o.verdict)<<",\"origin\":"<<std::quoted(o.origin)<<",\"source\":"<<std::quoted(o.source)<<",\"raw_bound\":";number(stream,o.rawBound);stream<<",\"safe_L\":"<<o.L<<",\"true_U\":"<<o.U<<"}\n";stream.flush();
    }
    std::ofstream f(out/"route_family_results.json"),csv(out/"route_family_results.csv");f<<std::setprecision(17)<<std::boolalpha<<"{\"restricted_scope_nonperformance\":true,\"positions\":[";
    csv<<std::setprecision(17)<<"restricted_scope_nonperformance,input_id,parent_seed,parent_run,family,family_SHA256,parent_F,tau,theta,raw_bound,raw_safe_L,raw_true_U,raw_verdict,propagated_L,propagated_U,verdict,L_source,U_source,origin,solve_id,native_status,columns,rows,Native_Runtime,Native_Work,outer_seconds,quantity_potential_lower,quantity_potential_upper,obstacle_lower,obstacle_upper\n";
    for(size_t i=0;i<slots.size();++i){const auto& pos=slots[i];const auto& r=*pos.parent;const auto& a=raw[i];double tau=target(records,r.inputId),theta=tau+eps,L=a.L,U=a.U;std::string ls=pos.id,us=pos.id;Fleet best=a.fleet;
        // Larger-domain lower bounds propagate downward. Feasible subdomain
        // witnesses propagate upward. Never overwrite the raw solver fields.
        auto level=[](const std::string& s){return s=="order"?0:s=="owner"?1:2;};
        for(size_t j=0;j<slots.size();++j)if(slots[j].parent->id==r.id){if(level(slots[j].scope)>=level(pos.scope)&&raw[j].L>L){L=raw[j].L;ls=slots[j].id;}if(level(slots[j].scope)<=level(pos.scope)&&raw[j].U<U){U=raw[j].U;us=slots[j].id;best=raw[j].fleet;}}
        need(L<=U+eps&&U<=r.checked.objective+eps,"propagated interval consistency");std::string verdict=U<=theta?"HIT":L>theta?"EXCLUDED":"UNKNOWN";auto fid=fileSha256(out/(pos.id+".identity"));
        if(i)f<<',';f<<"{\"position\":"<<std::quoted(pos.id)<<",\"input_id\":"<<std::quoted(r.inputId)<<",\"parent_seed\":"<<r.seed<<",\"parent\":"<<std::quoted(r.id)<<",\"scope\":"<<std::quoted(pos.scope)<<",\"family_SHA256\":"<<std::quoted(fid)<<",\"parent_F\":"<<r.checked.objective<<",\"tau\":"<<tau<<",\"theta\":"<<theta<<",\"raw_bound\":";number(f,a.rawBound);f<<",\"raw_safe_L\":"<<a.L<<",\"raw_true_U\":"<<a.U<<",\"raw_verdict\":"<<std::quoted(a.verdict)<<",\"propagated_L\":"<<L<<",\"propagated_U\":"<<U<<",\"verdict\":"<<std::quoted(verdict)<<",\"L_source\":"<<std::quoted(ls)<<",\"U_source\":"<<std::quoted(us)<<",\"origin\":"<<std::quoted(a.origin)<<",\"solve_id\":"<<std::quoted(a.source)<<",\"quantity_potential\":["<<r.checked.objective-U<<','<<r.checked.objective-L<<"],\"obstacle_to_theta\":["<<std::max(0.,L-theta)<<','<<std::max(0.,U-theta)<<"],\"physical\":";fleetJSON(f,r.in,best,r.lambda);f<<'}';
        csv<<"true,"<<r.inputId<<','<<r.seed<<','<<r.id<<','<<pos.scope<<','<<fid<<','<<r.checked.objective<<','<<tau<<','<<theta<<',';if(std::isfinite(a.rawBound))csv<<a.rawBound;csv<<','<<a.L<<','<<a.U<<','<<a.verdict<<','<<L<<','<<U<<','<<verdict<<','<<ls<<','<<us<<','<<a.origin<<','<<a.source<<','<<a.status<<','<<a.columns<<','<<a.rows<<','<<a.runtime<<','<<a.work<<','<<a.outer<<','<<r.checked.objective-U<<','<<r.checked.objective-L<<','<<std::max(0.,L-theta)<<','<<std::max(0.,U-theta)<<'\n';
    }f<<"],\"actual_substantive_Optimize\":"<<calls<<",\"Native_Runtime_sum\":"<<runtimeSum<<",\"Native_Work_sum\":"<<workSum<<",\"campaign_outer_seconds\":"<<seconds(begin)<<",\"diagnostic_elapsed_seconds\":"<<unixTime()-diagnosticStart<<"}\n";
}

// Independent exhaustive oracle: no model columns, arcs or Gurobi used here.
struct Enumeration{double optimum=INFINITY;Fleet best,ownerOnly,eligibleOnly;long long candidates=0,feasible=0,capacityReject=0,timeReject=0,empty=0,loaded=0,flipped=0,deleted=0,internal=0;bool zeroFeasible=false;Fleet zero;};
bool oraclePhysical(const Instance& in,const Fleet& routes,const std::vector<int>& y,Enumeration& e){
    ++e.candidates;for(auto r:routes){long double travel=0;for(size_t j=1;j<r.nodes.size();++j)travel+=in.dist[r.nodes[j-1]][r.nodes[j]];int load=0,pick=0,drop=0;
        for(size_t j=1;j+1<r.nodes.size();++j){int i=r.nodes[j],d=in.initial[i]-y[i];load+=d;pick+=std::max(0,d);drop+=std::max(0,-d);if(load<0||load>in.Q[r.vehicle]){++e.capacityReject;return false;}}
        long double duration=travel+in.pickup_time*static_cast<long double>(pick)+in.drop_time*static_cast<long double>(drop+load);if(duration>in.total_time_limit+1e-7L){++e.timeReject;return false;}}
    return true;
}
long double oracleObjective(const Instance& in,const std::vector<int>& y,double lambda){long double s=0,h=0,p=0;std::vector<long double> r(in.V+1);for(int i=1;i<=in.V;++i){r[i]=static_cast<long double>(y[i])/in.target[i];s+=r[i];p+=static_cast<long double>(in.weights[i])*std::abs(r[i]-1);}for(int i=1;i<=in.V;++i)for(int j=i+1;j<=in.V;++j)h+=std::abs(r[i]-r[j]);return(s>0?h/(in.V*s):0)+lambda*p;}
Enumeration enumerate(const Instance& in,double lambda,const Fleet& parent,const std::string& scope){
    const auto fam=family(in,parent);Enumeration e;std::vector<int> y=in.initial;std::vector<std::vector<int>> assign(in.M);std::function<void(int)> stocks;
    stocks=[&](int i){if(i<=in.V){int lo=fam.owner[i]>=0?0:in.initial[i],hi=fam.owner[i]>=0?in.capacity[i]:in.initial[i];for(int v=lo;v<=hi;++v){y[i]=v;stocks(i+1);}return;}
        std::vector<int> active;for(int j=1;j<=in.V;++j)if(y[j]!=in.initial[j])active.push_back(j);
        std::function<void(int)> owners;owners=[&](int at){if(at<static_cast<int>(active.size())){int node=active[at];for(int k=0;k<in.M;++k)if(scope=="eligible"||fam.owner[node]==k){assign[k].push_back(node);owners(at+1);assign[k].pop_back();}return;}
            Fleet routes(in.M);std::function<void(int)> permutations;permutations=[&](int k){if(k<in.M){auto seq=assign[k];if(scope=="order"){seq.clear();for(int node:fam.pi[k])if(y[node]!=in.initial[node])seq.push_back(node);}
                    else std::sort(seq.begin(),seq.end());do{RoutePlan r;r.vehicle=k;r.nodes={0};for(int node:seq){int d=in.initial[node]-y[node];r.nodes.push_back(node);r.operations.push_back({node,std::max(0,d),std::max(0,-d)});}r.nodes.push_back(0);routes[k]=r;permutations(k+1);if(scope=="order")break;}while(std::next_permutation(seq.begin(),seq.end()));return;}
                if(!oraclePhysical(in,routes,y,e))return;++e.feasible;const double F=static_cast<double>(oracleObjective(in,y,lambda));if(F<e.optimum-1e-13){e.optimum=F;e.best=routes;}
                bool ownerOK=true,orderOK=true;for(auto r:routes){int last=-1;for(auto op:r.operations){if(fam.owner[op.station]!=r.vehicle){ownerOK=false;orderOK=false;continue;}auto it=std::find(fam.pi[r.vehicle].begin(),fam.pi[r.vehicle].end(),op.station);int pos=it-fam.pi[r.vehicle].begin();if(pos<=last)orderOK=false;last=pos;}}
                if(ownerOK&&!orderOK&&e.ownerOnly.empty())e.ownerOnly=routes;if(!ownerOK&&e.eligibleOnly.empty())e.eligibleOnly=routes;
                bool zero=true;for(int j=1;j<=in.V;++j){zero=zero&&y[j]==0;if(y[j]>0&&y[j]<in.capacity[j])++e.internal;if(fam.owner[j]>=0&&y[j]==in.initial[j])++e.deleted;}
                if(zero){e.zeroFeasible=true;e.zero=routes;}
                for(auto r:routes){if(r.operations.empty())++e.empty;int load=0;for(auto op:r.operations){load+=op.pickup-op.drop;for(auto pr:parent)for(auto prev:pr.operations)if(prev.station==op.station&&(prev.pickup-prev.drop)*(op.pickup-op.drop)<0)++e.flipped;}if(load>0)++e.loaded;}
            };permutations(0);};owners(0);
    };stocks(1);return e;
}
std::pair<Instance,Fleet> tiny(const std::string& id){Instance in;in.name=id;in.V=4;in.M=2;in.Q=id=="A"?std::vector<int>{3,2}:std::vector<int>{3,3};in.capacity={0,3,3,3,3};in.initial=id=="A"?std::vector<int>{0,3,0,2,1}:std::vector<int>{0,2,1,3,0};in.target={1,2,2,2,2};in.weights={0,.2,.3,.25,.25};in.total_time_limit=id=="A"?14:12;in.pickup_time=1;in.drop_time=1;in.dist.assign(5,std::vector<double>(5));for(int i=0;i<=4;++i)for(int j=0;j<=4;++j)in.dist[i][j]=std::abs(i-j);
    Fleet f;if(id=="A")f={{0,{0,1,2,3,4,0},{{1,2,0},{2,0,1},{3,1,0},{4,0,1}}},{1,{0,0},{}}};else{in.target={1,1,2,1,2};f={{0,{0,1,2,0},{{1,1,0},{2,0,1}}},{1,{0,3,4,0},{{3,2,0},{4,0,1}}}};}need(physical(in,f,.3).feasible,"tiny parent");return{in,f};}
void tinyFreeze(const fs::path& out){need(fs::create_directories(out),"exclusive tiny freeze");std::ofstream f(out/"enumeration.json");f<<std::setprecision(17)<<std::boolalpha<<"{\"qualification\":\"complete enumeration with long-double arithmetic and frozen floating numerical policy; not a symbolic exact certificate\",\"Optimize\":0,\"cases\":[";bool comma=false;
    for(auto id:{"A","B"}){auto data=tiny(id);const auto& in=data.first;const auto& parent=data.second;saveFleet(out/(std::string(id)+"_parent.fleet"),parent);if(comma)f<<',';comma=true;f<<"{\"id\":"<<std::quoted(id)<<",\"V\":4,\"M\":2,\"Q\":";array(f,in.Q);f<<",\"b\":";array(f,in.initial);f<<",\"C\":";array(f,in.capacity);f<<",\"target\":";array(f,in.target);f<<",\"weights\":";array(f,in.weights);f<<",\"T\":"<<in.total_time_limit<<",\"lambda\":0.3,\"pickup_seconds\":1,\"drop_seconds\":1,\"distances\":\"abs(i-j), depot index0\",\"families\":[";bool c=false;
        for(auto scope:{"order","owner","eligible"}){auto e=enumerate(in,.3,parent,scope);need(std::isfinite(e.optimum),"tiny enumeration nonempty");saveFleet(out/(std::string(id)+"_"+scope+"_oracle.fleet"),e.best);if(!e.ownerOnly.empty())saveFleet(out/(std::string(id)+"_owner_not_order.fleet"),e.ownerOnly);if(!e.eligibleOnly.empty())saveFleet(out/(std::string(id)+"_eligible_not_owner.fleet"),e.eligibleOnly);if(e.zeroFeasible)saveFleet(out/(std::string(id)+"_zero.fleet"),e.zero);
            if(c)f<<',';c=true;f<<"{\"scope\":"<<std::quoted(scope)<<",\"optimum\":"<<e.optimum<<",\"candidates\":"<<e.candidates<<",\"feasible\":"<<e.feasible<<",\"capacity_rejected\":"<<e.capacityReject<<",\"time_rejected\":"<<e.timeReject<<",\"empty\":"<<e.empty<<",\"loaded_return\":"<<e.loaded<<",\"direction_flips\":"<<e.flipped<<",\"deleted\":"<<e.deleted<<",\"internal_stock\":"<<e.internal<<",\"zero_feasible\":"<<e.zeroFeasible<<",\"owner_not_order_found\":"<<!e.ownerOnly.empty()<<",\"eligible_not_owner_found\":"<<!e.eligibleOnly.empty()<<",\"optimum_physical\":";fleetJSON(f,in,e.best,.3);f<<'}';}
        f<<"]}";}f<<"]}\n";std::cout<<"Tiny complete enumeration frozen, no Optimize\n";
}
void tinyMapAudit(const fs::path& frozen,const fs::path& out){need(fs::create_directories(out),"exclusive map audit");std::ofstream f(out/"checks.json");f<<std::setprecision(17)<<"{\"Optimize\":0,\"checks\":[";bool first=true;int ownerPass=0,eligiblePass=0,zeroPass=0;
    for(auto id:{"A","B"}){auto data=tiny(id);const auto& in=data.first;const auto& p=data.second;for(auto scope:{"order","owner","eligible"}){Built b(in,.3,p,scope);auto x=b.map(p);need(b.m.audit(x)<=eps,"tiny parent map");auto oracle=loadFleet(frozen/(std::string(id)+"_"+scope+"_oracle.fleet"));auto y=b.map(oracle);double obj=0;need(b.m.audit(y,&obj)<=eps,"tiny oracle map");need(std::abs(obj-static_cast<double>(oracleObjective(in,physical(in,oracle,.3).final_inventory,.3)))<=eps,"independent oracle/model F");
            for(auto type:{"owner_not_order","eligible_not_owner","zero"}){auto path=frozen/(std::string(id)+"_"+type+".fleet");if(!fs::exists(path))continue;auto w=loadFleet(path);bool accepted=false;double residual=-1;try{auto z=b.map(w);residual=b.m.audit(z);accepted=residual<=eps;}catch(const std::exception&){}
                bool expected=std::string(type)=="zero"?member(in,b.fam,w,scope):std::string(type)=="owner_not_order"?std::string(scope)!="order":std::string(scope)=="eligible";
                need(accepted==expected,"structural domain acceptance mismatch");if(accepted){if(std::string(type)=="owner_not_order")++ownerPass;if(std::string(type)=="eligible_not_owner")++eligiblePass;if(std::string(type)=="zero")++zeroPass;}
                if(!first)f<<',';first=false;f<<"{\"tiny\":"<<std::quoted(id)<<",\"scope\":"<<std::quoted(scope)<<",\"witness\":"<<std::quoted(type)<<",\"accepted\":"<<(accepted?"true":"false")<<",\"expected\":"<<(expected?"true":"false")<<",\"max_actual_residual\":"<<residual<<'}';}
            ck(GRBwrite(b.m.model,(out/(std::string(id)+"_"+scope+".lp")).string().c_str()));}
    }need(ownerPass>0&&eligiblePass>0&&zeroPass>0,"required structural/zero witness coverage");f<<"],\"owner_release_acceptances\":"<<ownerPass<<",\"eligible_release_acceptances\":"<<eligiblePass<<",\"zero_acceptances\":"<<zeroPass<<",\"PASS\":true}\n";
}
void qualification(const fs::path& frozen,const fs::path& out){need(fs::create_directories(out),"exclusive qualification output");tinyMapAudit(frozen,out/"mapping");int calls=0;for(auto id:{"A","B"})for(auto scope:{"order","owner","eligible"}){auto d=tiny(id);auto e=enumerate(d.first,.3,d.second,scope);++calls;solveOne(d.first,.3,d.second,scope,e.optimum,60,out/(std::string(id)+"_"+scope),"R168_Q"+std::to_string(calls),true);}std::ofstream f(out/"qualification_PASS.txt");f<<"six independent-enumeration/MIP qualifications and structural mappings passed\n"<<fileSha256(frozen/"enumeration.json")<<'\n';}
} // namespace
int main(int argc,char** argv){try{need(argc>=2,"command required");std::string cmd=argv[1];if(cmd=="preflight"){need(argc==4,"preflight pool.txt out");preflight(argv[2],argv[3]);}
    else if(cmd=="tiny-freeze"){need(argc==3,"tiny-freeze out");tinyFreeze(argv[2]);}
    else if(cmd=="tiny-map"){need(argc==4,"tiny-map frozen out");tinyMapAudit(argv[2],argv[3]);}
    else if(cmd=="qualification"){need(argc==4,"qualification frozen out");qualification(argv[2],argv[3]);}
    else if(cmd=="tiny-solve"){need(argc==6,"tiny-solve A|B scope out call_id");auto data=tiny(argv[2]);auto e=enumerate(data.first,.3,data.second,argv[3]);solveOne(data.first,.3,data.second,argv[3],e.optimum,60,argv[4],argv[5],true);}
    else if(cmd=="campaign"){need(argc==6,"campaign pool frozen out diagnostic_epoch.txt");campaign(argv[2],argv[3],argv[4],argv[5]);}
    else if(cmd=="solve"){need(argc==8,"solve pool parent_id scope cap out call_id");auto records=pool(argv[2]);auto it=std::find_if(records.begin(),records.end(),[&](const Record& r){return r.id==argv[3];});need(it!=records.end(),"unknown parent");double cap=std::stod(argv[5]);need(cap>0&&cap<=300,"family quota");solveOne(it->in,it->lambda,it->fleet,argv[4],target(records,it->inputId),cap,argv[6],argv[7],false);}
    else need(false,"unknown command");return 0;
}catch(const std::exception& e){std::cerr<<"Round168 error: "<<e.what()<<'\n';return 1;}}
