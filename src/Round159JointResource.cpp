#include "Round159JointResource.hpp"
#include <gurobi_c.h>
#include <windows.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <tuple>
#include <vector>

namespace round159 {
namespace {
constexpr int BlockSize=8, Iterations=12, Nodes=512, BaselineNodes=2048;
constexpr std::uint64_t StateCap=16777216;
constexpr double Accept=1e-10;
using Clock=std::chrono::steady_clock;
using Wide=unsigned __int128;
const Wide Inf=Wide(1)<<126;
struct Point {std::vector<int> y,owner; double j=0;};
struct Sub {std::vector<int> ids; int budget;};
struct Data {
    int n,m,bmin,bmax,U; double gamma,h,H,T;
    std::vector<int> Q,b,cap;
    std::vector<double> c,omega;
    std::vector<std::vector<int>> supports;
    std::vector<std::vector<double>> distance;
    std::vector<Sub> rows;
    Point start;
};
void require(bool ok,const std::string& msg) {if(!ok)throw std::runtime_error(msg);}
void check(int rc) {if(rc)throw std::runtime_error("Gurobi error "+std::to_string(rc));}
template<class T> void array(std::ostream& o,const std::vector<T>& v) {
    o<<'[';for(std::size_t i=0;i<v.size();++i){if(i)o<<',';o<<v[i];}o<<']';
}
Data load(const std::string& name) {
    std::ifstream in(name);require(bool(in),"data open failed");Data d;
    in>>d.n>>d.m>>d.bmin>>d.bmax>>d.gamma>>d.h>>d.H>>d.T;
    require(d.n>0&&d.m>0,"invalid dimensions");
    d.Q.resize(d.m);for(auto& v:d.Q)in>>v;
    d.b.resize(d.n+1);d.cap.resize(d.n+1);d.c.resize(d.n+1);d.omega.resize(d.n+1);d.supports.resize(d.n+1);
    for(int i=1;i<=d.n;++i){int z;in>>d.b[i]>>d.cap[i]>>d.c[i]>>d.omega[i]>>z;
        require(z>0,"empty support");d.supports[i].resize(z);for(auto& v:d.supports[i])in>>v;}
    d.distance.assign(d.n+1,std::vector<double>(d.n+1));for(auto& row:d.distance)for(auto& v:row)in>>v;
    int z;in>>d.U>>z;d.rows.resize(z);
    for(auto& row:d.rows){int sz;in>>sz;row.ids.resize(sz);for(auto& v:row.ids)in>>v;in>>row.budget;}
    d.start.y.resize(d.n);d.start.owner.resize(d.n);
    for(auto& v:d.start.y)in>>v;for(auto& v:d.start.owner)in>>v;
    require(bool(in),"truncated data");return d;
}
double objective(const Data& d,const std::vector<int>& y,double* gout=nullptr) {
    std::vector<long double> r(d.n);long double S=0,A=0,H=0;
    for(int i=1;i<=d.n;++i){r[i-1]=static_cast<long double>(d.c[i])*y[i-1];S+=r[i-1];H+=static_cast<long double>(d.omega[i])*std::abs(r[i-1]-1);}
    std::sort(r.begin(),r.end());for(int i=0;i<d.n;++i)A+=(2*i-d.n+1)*r[i];
    long double G=S?A/(d.n*S):0;if(gout)*gout=static_cast<double>(G);return static_cast<double>(G+H);
}
struct Stats {std::vector<int>P,D,R;std::vector<double>L3;};
Stats stats(const Data& d,const Point& p) {
    Stats s;s.P.assign(d.m,0);s.D=s.P;s.R=s.P;s.L3.assign(d.m,0);
    for(int i=1;i<=d.n;++i)if(p.y[i-1]!=d.b[i]){
        int k=p.owner[i-1];require(k>=0&&k<d.m,"nonzero service without owner");
        s.P[k]+=std::max(0,d.b[i]-p.y[i-1]);s.D[k]+=std::max(0,p.y[i-1]-d.b[i]);}
    for(int k=0;k<d.m;++k)s.R[k]=s.P[k]-s.D[k];
    // Direct small tours are used only for scoring, never for proof or acceptance.
    for(int k=0;k<d.m;++k){std::vector<int> a;
        for(int i=1;i<=d.n;++i)if(p.owner[i-1]==k&&p.y[i-1]!=d.b[i])a.push_back(i);
        for(int i:a){s.L3[k]=std::max(s.L3[k],d.distance[0][i]+d.distance[i][0]);
            for(int j:a)if(j!=i){s.L3[k]=std::max(s.L3[k],d.distance[0][i]+d.distance[i][j]+d.distance[j][0]);
                for(int t:a)if(t!=i&&t!=j){std::vector<int> v={i,j,t};std::sort(v.begin(),v.end());double lo=1e100;
                    do{lo=std::min(lo,d.distance[0][v[0]]+d.distance[v[0]][v[1]]+d.distance[v[1]][v[2]]+d.distance[v[2]][0]);}while(std::next_permutation(v.begin(),v.end()));
                    s.L3[k]=std::max(s.L3[k],lo);}}}}
    return s;
}
bool resource(const Data& d,Point& p) {
    if(int(p.y.size())!=d.n||int(p.owner.size())!=d.n)return false;
    double G; p.j=objective(d,p.y,&G);int total=std::accumulate(p.y.begin(),p.y.end(),0);
    if(total<d.bmin||total>d.bmax||G>d.gamma+1e-12)return false;
    for(int i=1;i<=d.n;++i){if(!std::binary_search(d.supports[i].begin(),d.supports[i].end(),p.y[i-1]))return false;
        if(p.y[i-1]!=d.b[i]){int k=p.owner[i-1];if(k<0||k>=d.m||std::abs(p.y[i-1]-d.b[i])>d.Q[k])return false;}}
    auto s=stats(d,p);for(int k=0;k<d.m;++k)if(s.R[k]<0||s.R[k]>d.Q[k]||s.P[k]>d.U)return false;
    for(const auto& row:d.rows)for(int k=0;k<d.m;++k){bool active=true;
        for(int i:row.ids)if(p.y[i-1]==d.b[i]||p.owner[i-1]!=k){active=false;break;}
        if(active&&(row.budget<0||s.P[k]>row.budget))return false;}
    return true;
}
void point(std::ostream& out,const Data& d,const Point& p){
    auto s=stats(d,p);out<<"\"Y\":";array(out,p.y);out<<",\"owner\":";array(out,p.owner);out<<",\"J\":"<<p.j;
    out<<",\"P\":";array(out,s.P);out<<",\"D\":";array(out,s.D);out<<",\"return\":";array(out,s.R);
}
void save(const std::string& path,const Data& d,const Point& p){
    std::ofstream o(path);o<<std::setprecision(17)<<'{';point(o,d,p);o<<"}\n";
    std::ofstream t(path+".txt");for(int v:p.y)t<<v<<' ';t<<'\n';for(int v:p.owner)t<<v<<' ';t<<'\n';
}
Point readpoint(const std::string& path,Data& d){Point p=d.start;if(!path.empty()){
    std::ifstream in(path);require(bool(in),"start open failed");for(auto& v:p.y)in>>v;for(auto& v:p.owner)in>>v;require(bool(in),"start truncated");}
    require(resource(d,p),"invalid resource start");return p;}
std::vector<int> block(const Data& d,const Point& p,int step){
    auto s=stats(d,p);std::vector<double> gain(d.n+1),score(d.n+1);std::vector<int> ids(d.n);std::iota(ids.begin(),ids.end(),1);
    for(int i:ids){auto y=p.y;double best=p.j;for(int v:d.supports[i]){y[i-1]=v;best=std::min(best,objective(d,y));}
        gain[i]=p.j-best;int k=p.owner[i-1];double pressure=k<0?0:120.*s.P[k]/std::max(1.,d.T-s.L3[k]);
        score[i]=gain[i]*(1+pressure);}
    std::sort(ids.begin(),ids.end(),[&](int a,int b){return score[a]!=score[b]?score[a]>score[b]:a<b;});
    int anchor=ids[step%d.n];double diameter=0;for(int j=1;j<=d.n;++j)diameter=std::max(diameter,d.distance[anchor][j]);
    std::sort(ids.begin(),ids.end(),[&](int a,int b){
        double av=score[a]+gain[anchor]*(1-d.distance[anchor][a]/std::max(1.,diameter));
        double bv=score[b]+gain[anchor]*(1-d.distance[anchor][b]/std::max(1.,diameter));
        return av!=bv?av>bv:a<b;});
    ids.erase(std::find(ids.begin(),ids.end(),anchor));ids.insert(ids.begin(),anchor);ids.resize(std::min(BlockSize,d.n));return ids;
}
struct Model {
    GRBenv* env=nullptr;GRBmodel* m=nullptr;int cols=0;
    std::map<std::pair<int,int>,int>x;
    std::map<std::tuple<int,int,int>,int>w;
    std::vector<std::vector<int>> visit;
    std::vector<int>P,D;
    explicit Model(const std::string& rn){check(GRBemptyenv(&env));check(GRBsetintparam(env,GRB_INT_PAR_OUTPUTFLAG,0));check(GRBstartenv(env));check(GRBreadmodel(env,rn.c_str(),&m));check(GRBgetintattr(m,GRB_INT_ATTR_NUMVARS,&cols));}
    ~Model(){if(m)GRBfreemodel(m);if(env)GRBfreeenv(env);}
    int var(double ub,char type,const std::string& name){int id=cols++;check(GRBaddvar(m,0,nullptr,nullptr,0,0,ub,type,name.c_str()));return id;}
    int find(const std::string& name){int id;check(GRBgetvarbyname(m,name.c_str(),&id));require(id>=0,"missing RN column "+name);return id;}
    void row(std::vector<int> ids,std::vector<double> a,char sense,double rhs,const std::string& name){check(GRBaddconstr(m,int(ids.size()),ids.data(),a.data(),sense,rhs,name.c_str()));}
    void fix(int id,double v){check(GRBsetdblattrelement(m,GRB_DBL_ATTR_LB,id,v));check(GRBsetdblattrelement(m,GRB_DBL_ATTR_UB,id,v));}
    void build(const Data& d,const Point& start,const std::vector<int>& released,bool baseline){
        std::vector<bool> free(d.n+1,false);for(int i:released)free[i]=true;
        for(int i=1;i<=d.n;++i)for(int y:d.supports[i])x[{i,y}]=find("x["+std::to_string(i)+","+std::to_string(y)+"]");
        for(int k=0;k<d.m;++k)for(int i=1;i<=d.n;++i)for(int y:d.supports[i])if(y!=d.b[i]&&std::abs(y-d.b[i])<=d.Q[k])
            w[{k,i,y}]=var(1,GRB_BINARY,"resource_service["+std::to_string(k)+","+std::to_string(i)+","+std::to_string(y)+"]");
        visit.assign(d.m,std::vector<int>(d.n+1));P.resize(d.m);D.resize(d.m);
        for(int k=0;k<d.m;++k){for(int i=1;i<=d.n;++i)visit[k][i]=var(1,GRB_CONTINUOUS,"resource_visit["+std::to_string(k)+","+std::to_string(i)+"]");
            P[k]=var(d.U,GRB_CONTINUOUS,"resource_pickup["+std::to_string(k)+"]");D[k]=var(std::accumulate(d.cap.begin(),d.cap.end(),0),GRB_CONTINUOUS,"resource_drop["+std::to_string(k)+"]");}
        check(GRBupdatemodel(m));
        for(int i=1;i<=d.n;++i)for(int y:d.supports[i])if(y!=d.b[i]){std::vector<int> ids={x[{i,y}]};std::vector<double>a={-1};
            for(int k=0;k<d.m;++k){auto it=w.find({k,i,y});if(it!=w.end()){ids.push_back(it->second);a.push_back(1);}}
            row(ids,a,GRB_EQUAL,0,"resource_assign_"+std::to_string(i)+"_"+std::to_string(y));}
        for(int k=0;k<d.m;++k){std::vector<int>pi={P[k]},di={D[k]};std::vector<double>pa={1},da={1};
            for(int i=1;i<=d.n;++i){std::vector<int>ids={visit[k][i]};std::vector<double>a={1};
                for(int y:d.supports[i]){auto it=w.find({k,i,y});if(it==w.end())continue;
                    ids.push_back(it->second);a.push_back(-1);pi.push_back(it->second);pa.push_back(-std::max(0,d.b[i]-y));di.push_back(it->second);da.push_back(-std::max(0,y-d.b[i]));}
                row(ids,a,GRB_EQUAL,0,"resource_visit_def_"+std::to_string(k)+"_"+std::to_string(i));}
            row(pi,pa,GRB_EQUAL,0,"resource_pickup_def_"+std::to_string(k));row(di,da,GRB_EQUAL,0,"resource_drop_def_"+std::to_string(k));
            row({P[k],D[k]},{1,-1},GRB_GREATER_EQUAL,0,"resource_return_lb_"+std::to_string(k));row({P[k],D[k]},{1,-1},GRB_LESS_EQUAL,d.Q[k],"resource_return_ub_"+std::to_string(k));
            int no=0;for(const auto& r:d.rows){std::vector<int> ids;std::vector<double>a;
                if(r.budget>=0){ids.push_back(P[k]);a.push_back(1);}
                for(int i:r.ids){ids.push_back(visit[k][i]);a.push_back(r.budget<0?1:d.U-r.budget);}
                row(ids,a,GRB_LESS_EQUAL,r.budget<0?int(r.ids.size())-1:r.budget+(d.U-r.budget)*int(r.ids.size()),"rounded_"+std::to_string(k)+"_"+std::to_string(no++));}
        }
        check(GRBupdatemodel(m));
        for(int i=1;i<=d.n;++i){if(!baseline&&!free[i])for(int y:d.supports[i])fix(x[{i,y}],y==start.y[i-1]);
            if(baseline&&start.owner[i-1]<0)for(int y:d.supports[i])fix(x[{i,y}],y==d.b[i]);
            for(int k=0;k<d.m;++k)if((baseline||!free[i])&&k!=start.owner[i-1])for(int y:d.supports[i]){auto it=w.find({k,i,y});if(it!=w.end())fix(it->second,0);}}
        if(baseline)for(int k=0;k<d.m;++k){int limit=d.U;for(const auto& r:d.rows){bool all=true;for(int i:r.ids)if(start.owner[i-1]!=k)all=false;if(all)limit=std::min(limit,r.budget);}
            row({P[k]},{1},GRB_LESS_EQUAL,limit,"fixed_A_conservative_budget_"+std::to_string(k));}
        check(GRBupdatemodel(m));
        // Complete RN and resource start: zero service retains membership only outside the model.
        std::vector<double> values(cols,0);long double S=0;for(int i=1;i<=d.n;++i)S+=static_cast<long double>(d.c[i])*start.y[i-1];require(S>0,"zero branch is not covered by this research export");
        double t=static_cast<double>(1/S);values[find("t")]=t;double G;objective(d,start.y,&G);values[find("q")]=G;
        for(int i=1;i<=d.n;++i){int y=start.y[i-1];values[x[{i,y}]]=1;values[find("w["+std::to_string(i)+","+std::to_string(y)+"]")]=t;
            values[find("z["+std::to_string(i)+"]")]=t*y;values[find("r["+std::to_string(i)+"]")]=d.c[i]*t*y;}
        for(int i=1;i<=d.n;++i)for(int j=i+1;j<=d.n;++j)values[find("a["+std::to_string(i)+","+std::to_string(j)+"]")]=std::abs(values[find("r["+std::to_string(i)+"]")]-values[find("r["+std::to_string(j)+"]")]);
        auto ss=stats(d,start);for(int k=0;k<d.m;++k){values[P[k]]=ss.P[k];values[D[k]]=ss.D[k];}
        for(int i=1;i<=d.n;++i)if(start.y[i-1]!=d.b[i]){int k=start.owner[i-1];values[w.at({k,i,start.y[i-1]})]=1;values[visit[k][i]]=1;}
        check(GRBsetdblattrarray(m,GRB_DBL_ATTR_START,0,cols,values.data()));
    }
};
struct Callback {
    const Data* d;Model* model;Point best;std::ofstream events;int iteration,seen=0,rejected=0;bool failed=false;Clock::time_point began;
    Callback(const Data& data,Model& mm,Point p,const std::string& file,int it):d(&data),model(&mm),best(std::move(p)),events(file),iteration(it),began(Clock::now()){events<<std::setprecision(17);}
    static int __stdcall call(GRBmodel*,void* cb,int where,void* opaque){
        auto& self=*static_cast<Callback*>(opaque);if(where!=GRB_CB_MIPSOL)return 0;
        try{std::vector<double> values(self.model->cols);check(GRBcbget(cb,where,GRB_CB_MIPSOL_SOL,values.data()));Point p=self.best;
            for(int i=1;i<=self.d->n;++i){int chosen=0;for(int y:self.d->supports[i])if(values[self.model->x.at({i,y})]>.5){p.y[i-1]=y;++chosen;}require(chosen==1,"invalid onehot callback");}
            for(int i=1;i<=self.d->n;++i)if(p.y[i-1]!=self.d->b[i]){int count=0;
                for(int k=0;k<self.d->m;++k){auto it=self.model->w.find({k,i,p.y[i-1]});if(it!=self.model->w.end()&&values[it->second]>.5){p.owner[i-1]=k;++count;}}require(count==1,"invalid service callback");}
            ++self.seen;bool valid=resource(*self.d,p);if(!valid)++self.rejected;
            if(valid&&p.j<self.best.j-Accept){self.best=p;double native;check(GRBcbget(cb,where,GRB_CB_MIPSOL_OBJ,&native));
                self.events<<"{\"iteration\":"<<self.iteration<<",\"native_objective\":"<<native<<",\"seconds\":"<<std::chrono::duration<double>(Clock::now()-self.began).count()<<',';point(self.events,*self.d,p);self.events<<"}\n";self.events.flush();}
        }catch(...){self.failed=true;return 1;}return 0;
    }
};
Wide exact(double value){if(value==0)return 0;int exponent;double fraction=std::frexp(value,&exponent);require(value>0&&exponent>=0,"unsupported DP coefficient scale");return Wide(static_cast<std::uint64_t>(std::ldexp(fraction,53)))<<exponent;}
std::string integer(Wide v){if(!v)return "0";std::string out;while(v){out.push_back(char('0'+v%10));v/=10;}std::reverse(out.begin(),out.end());return out;}
double seconds(Wide v){return static_cast<double>(static_cast<long double>(v)/9007199254740992.L);}
struct DPResult{bool complete=false;Wide travel=Inf;std::vector<int> route;std::uint64_t states=0;};
DPResult dp(const Data& d,const Point& p,int k,bool load){
    std::vector<int>a;for(int i=1;i<=d.n;++i)if(p.owner[i-1]==k&&p.y[i-1]!=d.b[i])a.push_back(i);std::size_t m=a.size();DPResult result;
    if(!m){result.complete=true;result.travel=0;result.route={0,0};return result;}
    if(m>=63||m*(std::uint64_t(1)<<m)>StateCap)return result;
    std::uint64_t size=std::uint64_t(1)<<m;std::vector<Wide>cost(size*m,Inf);std::vector<unsigned char>parent(size*m,255);std::vector<int>balance(size);
    for(std::uint64_t mask=1;mask<size;++mask){int pos=__builtin_ctzll(mask);balance[mask]=balance[mask&(mask-1)]+d.b[a[pos]]-p.y[a[pos]-1];}
    for(std::size_t i=0;i<m;++i)if(!load||(balance[std::uint64_t(1)<<i]>=0&&balance[std::uint64_t(1)<<i]<=d.Q[k]))cost[(std::uint64_t(1)<<i)*m+i]=exact(d.distance[0][a[i]]);
    for(std::uint64_t mask=1;mask<size;++mask){if(load&&(balance[mask]<0||balance[mask]>d.Q[k]))continue;
        for(std::size_t j=0;j<m;++j)if(mask&(std::uint64_t(1)<<j)){auto val=cost[mask*m+j];if(val==Inf)continue;++result.states;
            std::uint64_t rest=(size-1)^mask;while(rest){int h=__builtin_ctzll(rest);rest&=rest-1;auto next=mask|(std::uint64_t(1)<<h);
                if(load&&(balance[next]<0||balance[next]>d.Q[k]))continue;auto cand=val+exact(d.distance[a[j]][a[h]]);if(cand<cost[next*m+h]){cost[next*m+h]=cand;parent[next*m+h]=static_cast<unsigned char>(j);}}}}
    result.complete=true;int last=-1;for(std::size_t j=0;j<m;++j)if(cost[(size-1)*m+j]!=Inf){auto cand=cost[(size-1)*m+j]+exact(d.distance[a[j]][0]);if(cand<result.travel){result.travel=cand;last=int(j);}}
    if(last>=0){std::uint64_t mask=size-1;while(mask){result.route.push_back(a[last]);int old=last;last=parent[mask*m+last];mask^=std::uint64_t(1)<<old;}std::reverse(result.route.begin(),result.route.end());result.route.insert(result.route.begin(),0);result.route.push_back(0);}return result;
}
int complete(const Data& d,const Point& p,const std::string& out){
    std::ofstream o(out+"/completion.json");o<<std::setprecision(17)<<"{\"state_cap\":"<<StateCap<<",\"scale\":9007199254740992,\"point\":{";point(o,d,p);o<<"},\"vehicles\":[";auto ss=stats(d,p);
    bool feasible=true,unknown=false;for(int k=0;k<d.m;++k){if(k)o<<',';auto plain=dp(d,p,k,false),loaded=dp(d,p,k,true);
        o<<"{\"vehicle\":"<<k<<",\"complete\":"<<(loaded.complete?"true":"false")<<",\"states\":"<<loaded.states<<",\"unloaded_states\":"<<plain.states;
        if(loaded.complete){if(loaded.travel==Inf){o<<",\"load_feasible_order_exists\":false";feasible=false;}else{Wide total=loaded.travel+exact(120.)*ss.P[k];
                bool ok=total<=exact(d.T+1e-7);feasible&=ok;o<<",\"travel_scaled\":\""<<integer(loaded.travel)<<"\",\"travel\":"<<seconds(loaded.travel)<<",\"total\":"<<seconds(total)<<",\"T_feasible\":"<<(ok?"true":"false")<<",\"route\":";array(o,loaded.route);}}
        else{unknown=true;feasible=false;}
        if(plain.complete&&plain.travel!=Inf)o<<",\"unloaded_travel_scaled\":\""<<integer(plain.travel)<<"\",\"unloaded_travel\":"<<seconds(plain.travel);
        o<<'}';}
    o<<"],\"classification\":\""<<(feasible?"PHYSICAL_FEAS":unknown?"UNKNOWN":"FIXED_COMBINATION_INFEAS")<<"\"}\n";return 0;
}
} // namespace

int run(const std::string& mode,const std::string& file,const std::string& rn,const std::string& out,const std::string& startfile){
    require(SetProcessAffinityMask(GetCurrentProcess(),4)!=0,"affinity failed");Data d=load(file);Point current=readpoint(startfile,d);
    require(!std::filesystem::exists(out),"output exists; refuse overwrite");std::filesystem::create_directories(out);
    if(mode=="complete")return complete(d,current,out);
    if(mode=="qualify"){
        for(bool baseline:{true,false}){auto released=baseline?std::vector<int>{}:block(d,current,0);Model model(rn);model.build(d,current,released,baseline);
            std::string stem=out+(baseline?"/baseline":"/joint");check(GRBwrite(model.m,(stem+".mps").c_str()));check(GRBwrite(model.m,(stem+".mst").c_str()));
            std::ofstream o(stem+".json");o<<"{\"released\":";array(o,released);o<<"}\n";}
        save(out+"/start.json",d,current);return 0;
    }
    require(mode=="baseline"||mode=="joint","unknown mode");
    const auto methodStart=Clock::now();const char* limitText=std::getenv("ROUND159_METHOD_DEADLINE");
    double methodLimit=limitText?std::stod(limitText):28800.;
    std::ofstream summary(out+"/calls.jsonl");summary<<std::setprecision(17);save(out+"/start.json",d,current);
    bool baseline=mode=="baseline";int count=baseline?1:Iterations;
    for(int iteration=0;iteration<count;++iteration){auto began=Clock::now();auto released=baseline?std::vector<int>{}:block(d,current,iteration);std::string stem=out+"/call_"+std::to_string(iteration);
        if(std::chrono::duration<double>(began-methodStart).count()+10>=methodLimit)break;
        Model model(rn);model.build(d,current,released,baseline);GRBenv* env=GRBgetenv(model.m);
        check(GRBsetintparam(env,GRB_INT_PAR_THREADS,1));check(GRBsetintparam(env,GRB_INT_PAR_SEED,0));check(GRBsetintparam(env,GRB_INT_PAR_MIPFOCUS,1));
        check(GRBsetdblparam(env,GRB_DBL_PAR_NODELIMIT,baseline?BaselineNodes:Nodes));check(GRBsetdblparam(env,GRB_DBL_PAR_MIPGAP,0));check(GRBsetdblparam(env,GRB_DBL_PAR_MIPGAPABS,0));
        check(GRBsetdblparam(env,GRB_DBL_PAR_INTFEASTOL,1e-6));check(GRBsetdblparam(env,GRB_DBL_PAR_FEASIBILITYTOL,1e-6));check(GRBsetdblparam(env,GRB_DBL_PAR_OPTIMALITYTOL,1e-6));
        check(GRBsetdblparam(env,GRB_DBL_PAR_TIMELIMIT,std::max(.01,methodLimit-10-std::chrono::duration<double>(Clock::now()-methodStart).count())));
        check(GRBsetintparam(env,GRB_INT_PAR_DUALREDUCTIONS,0));check(GRBsetstrparam(env,GRB_STR_PAR_LOGFILE,(stem+".log").c_str()));check(GRBsetintparam(env,GRB_INT_PAR_OUTPUTFLAG,1));check(GRBsetintparam(env,GRB_INT_PAR_LOGTOCONSOLE,0));
        check(GRBwrite(model.m,(stem+".mps").c_str()));check(GRBwrite(model.m,(stem+".mst").c_str()));
        Callback cb(d,model,current,stem+"_events.jsonl",iteration);check(GRBsetcallbackfunc(model.m,Callback::call,&cb));check(GRBoptimize(model.m));require(!cb.failed,"callback failure");
        int status,solutions;double nodes,runtime,work,bound;check(GRBgetintattr(model.m,GRB_INT_ATTR_STATUS,&status));check(GRBgetintattr(model.m,GRB_INT_ATTR_SOLCOUNT,&solutions));
        check(GRBgetdblattr(model.m,GRB_DBL_ATTR_NODECOUNT,&nodes));check(GRBgetdblattr(model.m,GRB_DBL_ATTR_RUNTIME,&runtime));check(GRBgetdblattr(model.m,GRB_DBL_ATTR_WORK,&work));check(GRBgetdblattr(model.m,GRB_DBL_ATTR_OBJBOUND,&bound));
        double before=current.j;current=cb.best;save(out+"/best.json",d,current);
        summary<<"{\"iteration\":"<<iteration<<",\"released\":";array(summary,released);summary<<",\"status\":"<<status<<",\"solutions\":"<<solutions<<",\"nodes\":"<<nodes<<",\"Runtime\":"<<runtime<<",\"Work\":"<<work;
        summary<<",\"restricted_native_bound\":"<<bound<<",\"seconds\":"<<std::chrono::duration<double>(Clock::now()-began).count()<<",\"before_J\":"<<before<<",\"after_J\":"<<current.j<<",\"seen\":"<<cb.seen<<",\"rejected\":"<<cb.rejected<<"}\n";summary.flush();
        if(solutions)check(GRBwrite(model.m,(stem+".sol").c_str()));
    }
    return 0;
}
} // namespace round159
