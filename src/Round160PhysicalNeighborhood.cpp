#include "Round160PhysicalNeighborhood.hpp"
#include "Evaluator.hpp"
#include <gurobi_c.h>
#include <windows.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
#include <tuple>

namespace ebrp::round160 {
bool& enabled(){static bool value=false;return value;}
namespace {
using Clock=std::chrono::steady_clock;
using Path=std::filesystem::path;
constexpr double Accept=1e-10;
double elapsed(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
void need(bool ok,const std::string& why){if(!ok)throw std::runtime_error("Round160: "+why);}
void check(int rc){if(rc)throw std::runtime_error("Round160 Gurobi error "+std::to_string(rc));}
template<class T> void array(std::ostream& o,const std::vector<T>& v){o<<'[';for(std::size_t j=0;j<v.size();++j){if(j)o<<',';o<<v[j];}o<<']';}
struct Point {std::vector<RoutePlan> routes;std::vector<int> y,owner;double j=0.,g=0.;};
struct Data {
    const Instance& in;double lambda;int n,m,bmin,bmax;std::vector<double> c,alpha;
    std::vector<std::vector<int>> support;
    explicit Data(const Instance& a,double lam):in(a),lambda(lam),n(a.V),m(a.M){
        bmax=std::accumulate(a.initial.begin()+1,a.initial.end(),0);
        bmin=std::max(0,bmax-std::accumulate(a.Q.begin(),a.Q.end(),0));
        c.resize(n+1);alpha.resize(n+1);support.resize(n+1);
        int q=*std::max_element(a.Q.begin(),a.Q.end());
        for(int i=1;i<=n;++i){c[i]=1./a.target[i];alpha[i]=lam*a.weights[i];
            for(int y=std::max(0,a.initial[i]-q);y<=std::min(a.capacity[i],a.initial[i]+q);++y)support[i].push_back(y);}
    }
    double objective(const std::vector<int>& y,double* gg=nullptr)const{
        long double S=0,A=0,H=0;std::vector<long double> r(n);
        for(int i=1;i<=n;++i){r[i-1]=static_cast<long double>(c[i])*y[i-1];S+=r[i-1];H+=static_cast<long double>(alpha[i])*std::abs(r[i-1]-1);}
        for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)A+=std::abs(r[i]-r[j]);
        long double G=S>0?A/(n*S):0;if(gg)*gg=static_cast<double>(G);return static_cast<double>(G+H);
    }
};
Point validated(const Data& d,const std::vector<RoutePlan>& routes){
    auto v=verifySolution(d.in,routes,d.lambda);need(v.feasible&&v.errors.empty(),"original physical verifier rejected point");
    Point p;p.routes=routes;p.y.assign(v.final_inventory.begin()+1,v.final_inventory.end());p.owner.assign(d.n,-1);
    std::set<int> cars;
    for(const auto& r:routes){need(cars.insert(r.vehicle).second,"repeated vehicle");for(int i:r.nodes)if(i){need(p.owner[i-1]<0,"duplicate owner");p.owner[i-1]=r.vehicle;}}
    for(int i=1;i<=d.n;++i){need(std::binary_search(d.support[i].begin(),d.support[i].end(),p.y[i-1]),"unsupported inventory");need((p.y[i-1]!=d.in.initial[i])==(p.owner[i-1]>=0),"zero-service membership");}
    p.j=d.objective(p.y,&p.g);need(std::abs(p.j-v.objective)<=1e-12,"original coefficient/objective mismatch");return p;
}
void point(std::ostream& o,const Data& d,const Point& p){
    o<<"\"J\":"<<p.j<<",\"G\":"<<p.g<<",\"Y\":";array(o,p.y);o<<",\"owner\":";array(o,p.owner);o<<",\"routes\":[";
    for(std::size_t k=0;k<p.routes.size();++k){if(k)o<<',';const auto& r=p.routes[k];int load=0,low=0,high=0,P=0,D=0;double travel=0.;
        std::vector<int>loads={0};for(std::size_t j=1;j<r.nodes.size();++j)travel+=d.in.dist[r.nodes[j-1]][r.nodes[j]];
        for(const auto& op:r.operations){load+=op.pickup-op.drop;low=std::min(low,load);high=std::max(high,load);P+=op.pickup;D+=op.drop;loads.push_back(load);}
        double handling=d.in.pickup_time*P+d.in.drop_time*(D+load);
        o<<"{\"vehicle\":"<<r.vehicle<<",\"nodes\":";array(o,r.nodes);o<<",\"operations\":[";
        for(std::size_t j=0;j<r.operations.size();++j){if(j)o<<',';const auto& a=r.operations[j];o<<"{\"station\":"<<a.station<<",\"pickup\":"<<a.pickup<<",\"drop\":"<<a.drop<<'}';}
        o<<"],\"prefix_loads\":";array(o,loads);o<<",\"P\":"<<P<<",\"D\":"<<D<<",\"return\":"<<load<<",\"min_load\":"<<low<<",\"max_load\":"<<high<<",\"travel\":"<<travel<<",\"handling\":"<<handling<<",\"duration\":"<<travel+handling<<",\"time_slack\":"<<d.in.total_time_limit-travel-handling<<'}';}
    o<<']';
}
void save(const Path& path,const Data& d,const Point& p){
    std::ofstream o(path);o<<std::setprecision(17)<<'{';point(o,d,p);o<<"}\n";
    std::ofstream text(path.string()+".txt");text<<p.routes.size()<<'\n';for(const auto& r:p.routes){text<<r.vehicle<<' '<<r.nodes.size();for(int i:r.nodes)text<<' '<<i;text<<'\n';for(int i:r.nodes)if(i)text<<d.in.initial[i]-p.y[i-1]<<' ';text<<'\n';}
}
std::vector<double> gains(const Data& d,const Point& p){
    std::vector<double> gain(d.n+1);for(int i=1;i<=d.n;++i){auto y=p.y;double best=p.j;for(int v:d.support[i]){y[i-1]=v;best=std::min(best,d.objective(y));}gain[i]=p.j-best;}return gain;
}
std::vector<int> anchors(const Data& d,const Point& p){
    auto g=gains(d,p);std::vector<int>a;for(int i=1;i<=d.n;++i)if(d.support[i].size()>1)a.push_back(i);
    std::sort(a.begin(),a.end(),[&](int i,int j){return g[i]!=g[j]?g[i]>g[j]:i<j;});return a;
}
std::vector<int> select(const Data& d,const Point& p,int anchor,int b){
    auto g=gains(d,p);std::vector<int>nearby,rank;for(int i=1;i<=d.n;++i)if(i!=anchor&&d.support[i].size()>1)nearby.push_back(i);rank=nearby;
    std::sort(nearby.begin(),nearby.end(),[&](int i,int j){return d.in.dist[anchor][i]!=d.in.dist[anchor][j]?d.in.dist[anchor][i]<d.in.dist[anchor][j]:i<j;});
    std::sort(rank.begin(),rank.end(),[&](int i,int j){return g[i]!=g[j]?g[i]>g[j]:i<j;});
    std::vector<int>r={anchor};std::set<int>used={anchor};std::size_t a=0,z=0;
    while(int(r.size())<b&&used.size()<nearby.size()+1){auto& order=r.size()%2?nearby:rank;auto& pos=r.size()%2?a:z;
        while(pos<order.size()&&used.count(order[pos]))++pos;
        if(pos==order.size())break;
        int i=order[pos++];r.push_back(i);used.insert(i);}
    return r;
}
struct Segment {int car;std::vector<int> ids;int delta=0,low=0,high=0,P=0,D=0;double travel=0.;};
Segment segment(const Data& d,const Point& p,int k,const std::vector<int>& ids){
    Segment a;a.car=k;a.ids=ids;for(std::size_t t=0;t<ids.size();++t){int i=ids[t],v=d.in.initial[i]-p.y[i-1];a.delta+=v;a.low=std::min(a.low,a.delta);a.high=std::max(a.high,a.delta);a.P+=std::max(0,v);a.D+=std::max(0,-v);if(t)a.travel+=d.in.dist[ids[t-1]][i];}return a;
}
struct Port {int car,a,b;double cost;};
struct Neighborhood {
    std::vector<int>B;std::vector<Segment>segments;std::vector<Port>ports;std::vector<std::vector<int>>seq;
    std::vector<std::pair<int,int>>locked;
    Neighborhood(const Data& d,const Point& p,std::vector<int> block,int g,bool uncompressed):B(std::move(block)),seq(d.m){
        std::set<int>free(B.begin(),B.end());std::vector<Segment>runs;
        for(const auto& r:p.routes){std::vector<int>run;
            auto flush=[&](){if(!run.empty()){runs.push_back(segment(d,p,r.vehicle,run));run.clear();}};
            for(int i:r.nodes)if(i){if(free.count(i))flush();else run.push_back(i);}
            flush();}
        std::vector<std::vector<Port>>candidate(d.m);
        for(const auto& run:runs)for(std::size_t pos=1;pos<run.ids.size();++pos){int a=run.ids[pos-1],b=run.ids[pos];double cost=1e100;
            for(int i:B){bool legal=false;for(int y:d.support[i])if(y!=d.in.initial[i]&&std::abs(y-d.in.initial[i])<=d.in.Q[run.car]){legal=true;break;}
                if(legal)cost=std::min(cost,d.in.dist[a][i]+d.in.dist[i][b]-d.in.dist[a][b]);}
            if(cost<1e90)candidate[run.car].push_back({run.car,a,b,cost});}
        for(auto& v:candidate)std::sort(v.begin(),v.end(),[](const Port& a,const Port& b){return std::tie(a.cost,a.a,a.b)<std::tie(b.cost,b.a,b.b);});
        std::vector<std::size_t>pos(d.m);bool found=true;while(int(ports.size())<g&&found){found=false;for(int k=0;k<d.m&&int(ports.size())<g;++k)if(pos[k]<candidate[k].size()){ports.push_back(candidate[k][pos[k]++]);found=true;}}
        std::set<std::tuple<int,int,int>>cuts;for(const auto& cut:ports)cuts.insert({cut.car,cut.a,cut.b});
        for(const auto& run:runs){std::vector<int>part;for(int i:run.ids){if(!part.empty()&&(uncompressed||cuts.count({run.car,part.back(),i}))){
                    bool keep_arc=uncompressed&&!cuts.count({run.car,part.back(),i});
                    seq[run.car].push_back(int(segments.size()));segments.push_back(segment(d,p,run.car,part));
                    if(keep_arc)locked.push_back({int(segments.size())-1,int(segments.size())});
                    part.clear();}part.push_back(i);}
            if(!part.empty()){seq[run.car].push_back(int(segments.size()));segments.push_back(segment(d,p,run.car,part));}}
    }
    void write(const Path& file,const Point& p)const{
        std::ofstream o(file);o<<std::setprecision(17)<<"{\"B\":";array(o,B);o<<",\"parent_J\":"<<p.j<<",\"parent_Y\":";array(o,p.y);o<<",\"parent_owner\":";array(o,p.owner);o<<",\"ports\":[";
        for(std::size_t i=0;i<ports.size();++i){if(i)o<<',';auto a=ports[i];o<<"{\"vehicle\":"<<a.car<<",\"arc\":["<<a.a<<','<<a.b<<"],\"insertion_delta\":"<<a.cost<<'}';}
        o<<"],\"segments\":[";for(std::size_t i=0;i<segments.size();++i){if(i)o<<',';const auto& a=segments[i];o<<"{\"car\":"<<a.car<<",\"ids\":";array(o,a.ids);o<<",\"delta\":"<<a.delta<<",\"min_prefix\":"<<a.low<<",\"max_prefix\":"<<a.high<<",\"P\":"<<a.P<<",\"D\":"<<a.D<<",\"internal_travel\":"<<a.travel<<'}';}o<<"]}\n";
    }
};
struct Expr {
    std::map<int,double> a;
    Expr& add(int v,double c=1.){if(c)a[v]+=c;return *this;}
};
struct Primitive {int station=0,seg=-1,head=0,tail=0;};
struct Model {
    const Data& d;const Point& parent;const Neighborhood& nb;bool zero;
    GRBenv* env=nullptr;GRBmodel* model=nullptr;int cols=0,rowno=0;
    std::vector<double> starts;std::vector<Primitive> prim;
    std::vector<std::vector<int>>available;
    std::map<std::pair<int,int>,int>x,w,visit,rank;
    std::map<std::tuple<int,int,int>,int>service,arc,flow;
    std::map<int,int>rho;std::map<std::pair<int,int>,int>pair;
    std::map<int,double>anchor;
    int t=-1,q=-1;double SO=0.,AO=0.,HO=0.,scale=1.,constant=0.,gamma=1.;
    double tl=0.,tu=0.;int outside_total=0;
    std::vector<int>fixedP;
    Model(const Data& dd,const Point& pp,const Neighborhood& nn,bool zz):d(dd),parent(pp),nb(nn),zero(zz),available(dd.m),fixedP(dd.m){
        check(GRBemptyenv(&env));check(GRBsetintparam(env,GRB_INT_PAR_OUTPUTFLAG,0));check(GRBstartenv(env));
        check(GRBnewmodel(env,&model,"R160_physical_neighborhood",0,nullptr,nullptr,nullptr,nullptr,nullptr));
    }
    ~Model(){if(model)GRBfreemodel(model);if(env)GRBfreeenv(env);}
    int var(double lo,double hi,char type,const std::string& name,double obj=0.){
        int id=cols++;check(GRBaddvar(model,0,nullptr,nullptr,obj,lo,hi,type,name.c_str()));starts.push_back(0.);return id;
    }
    void row(const Expr& e,char sense,double rhs,const std::string& name){
        std::vector<int> ids;std::vector<double>a;for(auto [v,c]:e.a)if(c){ids.push_back(v);a.push_back(c);}
        std::string unique=name+"_"+std::to_string(rowno++);
        check(GRBaddconstr(model,int(ids.size()),ids.data(),a.data(),sense,rhs,unique.c_str()));
    }
    void fix(int id,double value){check(GRBsetdblattrelement(model,GRB_DBL_ATTR_LB,id,value));check(GRBsetdblattrelement(model,GRB_DBL_ATTR_UB,id,value));}
    void objective(){
        std::set<int>free(nb.B.begin(),nb.B.end());std::vector<double>outside;
        for(int i=1;i<=d.n;++i)if(!free.count(i)){double r=d.c[i]*parent.y[i-1];outside.push_back(r);SO+=r;HO+=d.alpha[i]*std::abs(r-1);outside_total+=parent.y[i-1];}
        for(std::size_t i=0;i<outside.size();++i)for(std::size_t j=i+1;j<outside.size();++j)AO+=std::abs(outside[i]-outside[j]);
        long double lower=SO,upper=SO;double minc=1e100,minpositive=1e100;
        for(int i:nb.B){lower+=static_cast<long double>(d.c[i])*d.support[i].front();upper+=static_cast<long double>(d.c[i])*d.support[i].back();minc=std::min(minc,d.c[i]);
            double low=1e100,high=0;for(int y:d.support[i]){double h=d.alpha[i]*std::abs(d.c[i]*y-1);low=std::min(low,h);high=std::max(high,h);if(y)minpositive=std::min(minpositive,d.c[i]*y);}anchor[i]=(low+high)/2;}
        constant=HO;double largest=1.;for(int i:nb.B){constant+=anchor[i];for(int y:d.support[i])largest=std::max(largest,std::abs(d.alpha[i]*std::abs(d.c[i]*y-1)-anchor[i]));}
        scale=std::ldexp(1.,int(std::ceil(std::log2(largest))));
        gamma=std::min(1.,parent.j+1e-8);
        if(!zero){
            lower=std::max(lower,static_cast<long double>(SO)+minc*std::max(0,d.bmin-outside_total));
            if(lower<=0)lower=std::max(minpositive,minc*std::max(1,d.bmin-outside_total));
            need(lower>0&&upper>0&&lower<=upper+1e-12,"positive normalization bounds");
            // Widen analytic endpoints to cover binary summation/transport.
            tl=std::nextafter(1./static_cast<double>(upper)*(1.-1e-12),0.);
            tu=std::nextafter(1./static_cast<double>(lower)*(1.+1e-12),std::numeric_limits<double>::infinity());
            t=var(tl,tu,GRB_CONTINUOUS,"t");q=var(0,gamma,GRB_CONTINUOUS,"q",1./scale);
        }
        for(int i:nb.B){
            for(int y:d.support[i]){std::string id=std::to_string(i)+"_"+std::to_string(y);
                x[{i,y}]=var(0,1,GRB_BINARY,"x_"+id,(d.alpha[i]*std::abs(d.c[i]*y-1)-anchor[i])/scale);
                if(!zero)w[{i,y}]=var(0,tu,GRB_CONTINUOUS,"w_"+id);}
            if(!zero)rho[i]=var(0,1,GRB_CONTINUOUS,"rho_"+std::to_string(i));
        }
        if(!zero)for(std::size_t i=0;i<nb.B.size();++i)for(std::size_t j=i+1;j<nb.B.size();++j){int a=nb.B[i],b=nb.B[j];pair[{a,b}]=var(0,1,GRB_CONTINUOUS,"a_"+std::to_string(a)+"_"+std::to_string(b));}
        check(GRBupdatemodel(model));check(GRBsetdblattr(model,GRB_DBL_ATTR_OBJCON,constant/scale));
        Expr total,cut; if(!zero)cut.add(q);
        for(int i:nb.B){Expr hot,mass,ratio;if(!zero){mass.add(t,-1);ratio.add(rho[i]);}
            for(int y:d.support[i]){int xx=x.at({i,y});hot.add(xx);total.add(xx,y);cut.add(xx,d.alpha[i]*std::abs(d.c[i]*y-1));
                if(zero){fix(xx,y==0?1:0);continue;}
                int ww=w.at({i,y});mass.add(ww);ratio.add(ww,-d.c[i]*y);
                row(Expr{}.add(ww).add(xx,-tl),GRB_GREATER_EQUAL,0,"product_lb");row(Expr{}.add(ww).add(xx,-tu),GRB_LESS_EQUAL,0,"product_ub");}
            row(hot,GRB_EQUAL,1,"onehot_"+std::to_string(i));
            if(!zero){row(mass,GRB_EQUAL,0,"normalized_mass_"+std::to_string(i));row(ratio,GRB_EQUAL,0,"normalized_ratio_"+std::to_string(i));}}
        row(total,GRB_GREATER_EQUAL,std::max(d.bmin-outside_total,(!zero&&SO==0)?1:0),"stock_lb");row(total,GRB_LESS_EQUAL,d.bmax-outside_total,"stock_ub");
        row(cut,GRB_LESS_EQUAL,parent.j+1e-8-HO,"parent_nonstrict_scope");
        if(!zero){Expr norm,num;norm.add(t,SO);num.add(q,d.n).add(t,-AO);
            for(int i:nb.B){norm.add(rho.at(i));for(int y:d.support[i]){double psi=0;for(double r:outside)psi+=std::abs(d.c[i]*y-r);num.add(w.at({i,y}),-psi);}}
            for(auto [ids,v]:pair){auto [i,j]=ids;row(Expr{}.add(v).add(rho.at(i),-1).add(rho.at(j)),GRB_GREATER_EQUAL,0,"block_pair_pos");row(Expr{}.add(v).add(rho.at(i)).add(rho.at(j),-1),GRB_GREATER_EQUAL,0,"block_pair_neg");num.add(v,-1);}
            row(norm,GRB_EQUAL,1,"normalization");row(num,GRB_GREATER_EQUAL,0,"full_original_Gini");}
    }
    void physical(bool fixed_owner){
        prim.push_back({});
        for(std::size_t s=0;s<nb.segments.size();++s){const auto& a=nb.segments[s];prim.push_back({0,int(s),a.ids.front(),a.ids.back()});available[a.car].push_back(int(prim.size())-1);fixedP[a.car]+=a.P;}
        for(int i:nb.B){int u=int(prim.size());prim.push_back({i,-1,i,i});for(int k=0;k<d.m;++k){bool ok=false;
                for(int y:d.support[i])if(y!=d.in.initial[i]&&std::abs(y-d.in.initial[i])<=d.in.Q[k]&&(!fixed_owner||parent.owner[i-1]<0||parent.owner[i-1]==k)){
                    service[{k,i,y}]=var(0,1,GRB_BINARY,"service_"+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(y));ok=true;}
                if(ok)available[k].push_back(u);}}
        for(int k=0;k<d.m;++k){int N=int(available[k].size());std::vector<int>nodes={0};nodes.insert(nodes.end(),available[k].begin(),available[k].end());
            for(int u:available[k]){bool mandatory=prim[u].seg>=0;visit[{k,u}]=var(mandatory?1:0,1,GRB_CONTINUOUS,"visit_"+std::to_string(k)+"_"+std::to_string(u));rank[{k,u}]=var(0,N,GRB_CONTINUOUS,"order_"+std::to_string(k)+"_"+std::to_string(u));}
            for(int u:nodes)for(int v:nodes)if(u!=v||u==0){auto key=std::make_tuple(k,u,v);std::string id=std::to_string(k)+"_"+std::to_string(u)+"_"+std::to_string(v);
                arc[key]=var(0,1,GRB_BINARY,"arc_"+id);flow[key]=var(0,u==0?0:d.in.Q[k],GRB_CONTINUOUS,"load_"+id);}
        }
        check(GRBupdatemodel(model));
        for(auto [a,b]:nb.locked)fix(arc.at({nb.segments[a].car,a+1,b+1}),1.);
        for(int i:nb.B)for(int y:d.support[i])if(y!=d.in.initial[i]){Expr e;e.add(x.at({i,y}),-1);for(int k=0;k<d.m;++k){auto it=service.find({k,i,y});if(it!=service.end())e.add(it->second);}row(e,GRB_EQUAL,0,"unique_nonzero_owner");}
        for(int k=0;k<d.m;++k){int N=int(available[k].size());std::vector<int>nodes={0};nodes.insert(nodes.end(),available[k].begin(),available[k].end());Expr time;
            double internal=0;for(const auto& a:nb.segments)if(a.car==k)internal+=a.travel;
            for(int u:nodes)for(int v:nodes)if(u!=v||u==0){auto key=std::make_tuple(k,u,v);int ar=arc.at(key),f=flow.at(key);
                row(Expr{}.add(f).add(ar,-d.in.Q[k]),GRB_LESS_EQUAL,0,"arc_capacity");
                time.add(ar,d.in.dist[prim[u].tail][prim[v].head]);
                if(u&&v)row(Expr{}.add(rank.at({k,v})).add(rank.at({k,u}),-1).add(ar,-(N+1)),GRB_GREATER_EQUAL,-N,"connected_order_arc");}
            for(int u:nodes){Expr out,in,load,entry;for(int v:nodes)if(u!=v||u==0){out.add(arc.at({k,u,v}));in.add(arc.at({k,v,u}));load.add(flow.at({k,u,v})).add(flow.at({k,v,u}),-1);entry.add(flow.at({k,v,u}));}
                if(!u){row(out,GRB_EQUAL,1,"depot_departure_or_bypass");row(in,GRB_EQUAL,1,"depot_return_or_bypass");continue;}
                int vis=visit.at({k,u});out.add(vis,-1);in.add(vis,-1);row(out,GRB_EQUAL,0,"out_degree");row(in,GRB_EQUAL,0,"in_degree");
                row(Expr{}.add(rank.at({k,u})).add(vis,-1),GRB_GREATER_EQUAL,0,"order_active_lb");row(Expr{}.add(rank.at({k,u})).add(vis,-N),GRB_LESS_EQUAL,0,"order_active_ub");
                if(prim[u].seg>=0){const auto& a=nb.segments[prim[u].seg];row(load,GRB_EQUAL,a.delta,"segment_load_conservation");row(entry,GRB_GREATER_EQUAL,-a.low,"segment_prefix_lb");row(entry,GRB_LESS_EQUAL,d.in.Q[k]-a.high,"segment_prefix_ub");}
                else {int i=prim[u].station;Expr service_visit;service_visit.add(vis,-1);
                    for(int y:d.support[i]){auto it=service.find({k,i,y});if(it==service.end())continue;int z=it->second;service_visit.add(z);load.add(z,-(d.in.initial[i]-y));time.add(z,(d.in.pickup_time+d.in.drop_time)*std::max(0,d.in.initial[i]-y));}
                    row(service_visit,GRB_EQUAL,0,"service_visit_def");row(load,GRB_EQUAL,0,"free_load_conservation");}}
            for(std::size_t s=1;s<nb.seq[k].size();++s)row(Expr{}.add(rank.at({k,nb.seq[k][s]+1})).add(rank.at({k,nb.seq[k][s-1]+1}),-1),GRB_GREATER_EQUAL,1,"fixed_segment_relative_order");
            row(time,GRB_LESS_EQUAL,d.in.total_time_limit-internal-(d.in.pickup_time+d.in.drop_time)*fixedP[k],"original_T_including_depot_unload");}
        check(GRBupdatemodel(model));
    }
    bool parent_branch()const{return zero?std::accumulate(parent.y.begin(),parent.y.end(),0)==0:std::accumulate(parent.y.begin(),parent.y.end(),0)>0;}
    void lift(){
        if(!parent_branch())return;
        long double S=0;for(int i=1;i<=d.n;++i)S+=static_cast<long double>(d.c[i])*parent.y[i-1];double tt=S>0?static_cast<double>(1/S):0;
        if(t>=0){starts[t]=tt;starts[q]=parent.g;}
        for(int i:nb.B){int y0=parent.y[i-1];starts[x.at({i,y0})]=1;if(!zero){starts[w.at({i,y0})]=tt;starts[rho.at(i)]=d.c[i]*y0*tt;}}
        if(!zero)for(auto [ids,v]:pair)starts[v]=std::abs(starts[rho.at(ids.first)]-starts[rho.at(ids.second)]);
        for(auto [ids,v]:service){auto [k,i,y]=ids;if(parent.owner[i-1]==k&&parent.y[i-1]==y)starts[v]=1;}
        std::map<int,int>station_token;for(std::size_t u=1;u<prim.size();++u){if(prim[u].station)station_token[prim[u].station]=int(u);else for(int i:nb.segments[prim[u].seg].ids)station_token[i]=int(u);}
        for(int k=0;k<d.m;++k){std::vector<int>order;for(const auto& r:parent.routes)if(r.vehicle==k)for(int i:r.nodes)if(i){int u=station_token.at(i);if(order.empty()||order.back()!=u)order.push_back(u);}
            int previous=0,load=0,pos=0;for(int u:order){auto edge=std::make_tuple(k,previous,u);starts[arc.at(edge)]=1;starts[flow.at(edge)]=load;starts[visit.at({k,u})]=1;starts[rank.at({k,u})]=++pos;
                load+=prim[u].seg>=0?nb.segments[prim[u].seg].delta:d.in.initial[prim[u].station]-parent.y[prim[u].station-1];previous=u;}
            starts[arc.at({k,previous,0})]=1;starts[flow.at({k,previous,0})]=load;}
        check(GRBsetdblattrarray(model,GRB_DBL_ATTR_START,0,cols,starts.data()));
    }
    double residual(const std::vector<double>& vals){
        int nrows;check(GRBgetintattr(model,GRB_INT_ATTR_NUMCONSTRS,&nrows));int nz;
        check(GRBgetconstrs(model,&nz,nullptr,nullptr,nullptr,0,nrows));std::vector<int>beg(nrows),ind(nz);std::vector<double>a(nz),rhs(nrows),lb(cols),ub(cols);std::vector<char>sense(nrows),type(cols);
        check(GRBgetconstrs(model,&nz,beg.data(),ind.data(),a.data(),0,nrows));check(GRBgetdblattrarray(model,GRB_DBL_ATTR_RHS,0,nrows,rhs.data()));check(GRBgetcharattrarray(model,GRB_CHAR_ATTR_SENSE,0,nrows,sense.data()));
        check(GRBgetdblattrarray(model,GRB_DBL_ATTR_LB,0,cols,lb.data()));check(GRBgetdblattrarray(model,GRB_DBL_ATTR_UB,0,cols,ub.data()));check(GRBgetcharattrarray(model,GRB_CHAR_ATTR_VTYPE,0,cols,type.data()));
        double error=0.;for(int i=0;i<cols;++i){error=std::max({error,lb[i]-vals[i],vals[i]-ub[i]});if(type[i]!=GRB_CONTINUOUS)error=std::max(error,std::abs(vals[i]-std::round(vals[i])));}
        for(int r=0;r<nrows;++r){long double lhs=0;for(int j=beg[r];j<(r+1<nrows?beg[r+1]:nz);++j)lhs+=static_cast<long double>(a[j])*vals[ind[j]];double gap=static_cast<double>(lhs-rhs[r]);error=std::max(error,sense[r]==GRB_EQUAL?std::abs(gap):sense[r]==GRB_LESS_EQUAL?gap:-gap);}return error;
    }
    Point decode(const std::vector<double>& vals)const{
        std::vector<int>Y=parent.y;for(int i:nb.B){int count=0;for(int y:d.support[i])if(vals[x.at({i,y})]>.5){Y[i-1]=y;++count;}need(count==1,"callback onehot");}
        std::vector<RoutePlan>routes;
        for(int k=0;k<d.m;++k){std::map<int,int>succ;for(auto [ids,v]:arc){auto [kk,a,b]=ids;if(kk==k&&vals[v]>.5){need(!succ.count(a),"multiple successors");succ[a]=b;}}
            RoutePlan r;r.vehicle=k;r.nodes={0};std::set<int>seen;int u=0;
            do{need(succ.count(u),"disconnected depot path");u=succ.at(u);if(!u)break;need(seen.insert(u).second,"subtour");std::vector<int>ids=prim[u].seg>=0?nb.segments[prim[u].seg].ids:std::vector<int>{prim[u].station};
                for(int i:ids){int delta=d.in.initial[i]-Y[i-1];need(delta!=0,"zero operation transit");r.nodes.push_back(i);r.operations.push_back({i,std::max(0,delta),std::max(0,-delta)});}}
            while(true);
            need(seen.size()+1==succ.size(),"disconnected macro cycle");r.nodes.push_back(0);routes.push_back(r);}
        Point p=validated(d,routes);need(p.y==Y,"physical decode stock mismatch");return p;
    }
    void save_start(const Path& folder){
        std::ofstream o(folder/"start_values.json");o<<std::setprecision(17)<<'[';for(int v=0;v<cols;++v){if(v)o<<',';o<<starts[v];}o<<"]\n";
        if(parent_branch())check(GRBwrite(model,(folder/"parent.mst").string().c_str()));
    }
};
struct Callback {
    Model& model;Point best;Path folder;Clock::time_point began,whole;
    const std::function<double()>& remaining;int seen=0,accepted=0;double verify_seconds=0.;bool failed=false;std::string failure;std::vector<double>last_values;
    Callback(Model& m,const Point& p,Path f,Clock::time_point all,const std::function<double()>& rem):model(m),best(p),folder(std::move(f)),began(Clock::now()),whole(all),remaining(rem){}
    void consider(const std::vector<double>& values,const std::string& origin){
        std::vector<int>Y=model.parent.y;for(int i:model.nb.B){int count=0;for(int y:model.d.support[i])if(values[model.x.at({i,y})]>.5){Y[i-1]=y;++count;}need(count==1,"incumbent onehot");}
        double j=model.d.objective(Y);++seen;if(j>=best.j-Accept)return;
        auto tick=Clock::now();Point p=model.decode(values);verify_seconds+=elapsed(tick);
        need(p.j<best.j-Accept,"recomputed strict decrease");best=p;++accepted;
        save(folder/("event_"+std::to_string(accepted)+".json"),model.d,p);
        std::ofstream ev(folder/"events.jsonl",std::ios::app);ev<<std::setprecision(17)<<"{\"origin\":\""<<origin<<"\",\"event\":"<<accepted<<",\"block_seconds\":"<<elapsed(began)<<",\"whole_seconds\":"<<elapsed(whole)<<',';point(ev,model.d,p);ev<<"}\n";ev.flush();
    }
    static int __stdcall call(GRBmodel* m,void* cb,int where,void* opaque){auto& self=*static_cast<Callback*>(opaque);
        try {if(self.remaining()<=0){GRBterminate(m);return 0;}if(where==GRB_CB_MIPSOL){self.last_values.resize(self.model.cols);check(GRBcbget(cb,where,GRB_CB_MIPSOL_SOL,self.last_values.data()));self.consider(self.last_values,"MIPSOL");}}
        catch(const std::exception& e){self.failed=true;self.failure=e.what();std::ofstream o(self.folder/"callback_failure.txt");o<<e.what()<<'\n';std::ofstream values(self.folder/"rejected_values.json");values<<std::setprecision(17);array(values,self.last_values);GRBterminate(m);}return 0;}
};
} // namespace

Outcome optimize(const Instance& in,double lambda,const std::vector<RoutePlan>& routes,const Path& evidence,const Config& cfg,const std::function<double()>& remaining){
    auto whole=Clock::now();Data d(in,lambda);Point current=validated(d,routes);std::filesystem::create_directories(evidence);save(evidence/"initial.json",d,current);
    need(cfg.nodes>0&&cfg.passes>0&&cfg.block_size>0&&cfg.extra_ports>=0,"invalid work capacity");
    Outcome out;std::ofstream trace(evidence/"trajectory.jsonl");trace<<std::setprecision(17);
    bool stop=false;int number=0;
    for(int pass=0;pass<cfg.passes&&!stop;++pass){auto queue=cfg.block.empty()?anchors(d,current):std::vector<int>{cfg.block.front()};
        std::ofstream aq(evidence/("anchor_queue_"+std::to_string(pass)+".json"));array(aq,queue);aq<<'\n';aq.close();int pass_improvements=out.improvements;
        for(int anchor:queue){if(remaining()<=0){out.deadline=true;stop=true;break;}
            if(current.j==0){stop=true;break;} // Original objective is nonnegative.
            auto B=cfg.block.empty()?select(d,current,anchor,std::min(cfg.block_size,int(queue.size()))):cfg.block;
            need(!B.empty(),"empty block");std::set<int>unique;
            for(int i:B)need(i>0&&i<=d.n&&unique.insert(i).second,"invalid/duplicate released station");
            Neighborhood nb(d,current,B,std::min(cfg.extra_ports,int(B.size())),cfg.uncompressed);
            Path base=evidence/("block_"+std::to_string(number++));std::filesystem::create_directories(base);nb.write(base/"neighborhood.json",current);save(base/"parent.json",d,current);++out.anchors;
            bool zero_possible=d.bmin==0;std::set<int>free(B.begin(),B.end());for(int i=1;i<=d.n;++i){if(!free.count(i)&&current.y[i-1])zero_possible=false;if(free.count(i)&&!std::binary_search(d.support[i].begin(),d.support[i].end(),0))zero_possible=false;}
            bool positive_possible=false;for(int y:current.y)if(y)positive_possible=true;for(int i:B)if(d.support[i].back()>0)positive_possible=true;
            Point next=current;
            for(int branch=0;branch<2;++branch){bool zero=branch==1;if((zero&&!zero_possible)||(!zero&&!positive_possible))continue;
                if(remaining()<=0){out.deadline=true;stop=true;break;}
                Path folder=base/(zero?"zero":"positive");std::filesystem::create_directories(folder);auto began=Clock::now();
                Model m(d,current,nb,zero);m.objective();m.physical(cfg.fixed_old_owner);m.lift();
                double start_residual=m.parent_branch()?m.residual(m.starts):0.;need(start_residual<=1e-5,"parent does not lift; residual="+std::to_string(start_residual));
                check(GRBwrite(m.model,(folder/"model.mps").string().c_str()));m.save_start(folder);
                int nr;check(GRBgetintattr(m.model,GRB_INT_ATTR_NUMCONSTRS,&nr));double build=elapsed(began);
                std::ofstream admission(folder/"admission.json");admission<<std::setprecision(17)<<"{\"parent_lift_residual\":"<<start_residual<<",\"parent_in_branch\":"<<(m.parent_branch()?"true":"false")<<",\"NumVars\":"<<m.cols<<",\"NumConstrs\":"<<nr<<",\"SO\":"<<m.SO<<",\"AO\":"<<m.AO<<",\"HO\":"<<m.HO<<",\"t_lower\":"<<m.tl<<",\"t_upper\":"<<m.tu<<",\"scale\":"<<m.scale<<",\"objective_constant\":"<<m.constant<<",\"zero_branch\":"<<(zero?"true":"false")<<",\"nodes\":"<<cfg.nodes<<",\"Seed\":0,\"Threads\":1,\"build_seconds\":"<<build<<"}\n";admission.close();
                if(cfg.qualify_only)continue;
                auto* env=GRBgetenv(m.model);check(GRBsetintparam(env,GRB_INT_PAR_THREADS,1));check(GRBsetintparam(env,GRB_INT_PAR_SEED,0));check(GRBsetintparam(env,GRB_INT_PAR_MIPFOCUS,1));
                check(GRBsetdblparam(env,GRB_DBL_PAR_NODELIMIT,cfg.nodes));check(GRBsetdblparam(env,GRB_DBL_PAR_TIMELIMIT,std::max(0.,remaining())));
                check(GRBsetdblparam(env,GRB_DBL_PAR_MIPGAP,0));check(GRBsetdblparam(env,GRB_DBL_PAR_MIPGAPABS,0));check(GRBsetdblparam(env,GRB_DBL_PAR_INTFEASTOL,1e-6));check(GRBsetdblparam(env,GRB_DBL_PAR_FEASIBILITYTOL,1e-6));check(GRBsetdblparam(env,GRB_DBL_PAR_OPTIMALITYTOL,1e-6));
                check(GRBsetintparam(env,GRB_INT_PAR_OUTPUTFLAG,1));check(GRBsetintparam(env,GRB_INT_PAR_LOGTOCONSOLE,0));check(GRBsetstrparam(env,GRB_STR_PAR_LOGFILE,(folder/"native.log").string().c_str()));
                Callback cb(m,current,folder,whole,remaining);check(GRBsetcallbackfunc(m.model,Callback::call,&cb));auto solve=Clock::now();check(GRBoptimize(m.model));double solve_seconds=elapsed(solve);++out.calls;
                int status,count;double runtime,work,nodes,bound;check(GRBgetintattr(m.model,GRB_INT_ATTR_STATUS,&status));check(GRBgetintattr(m.model,GRB_INT_ATTR_SOLCOUNT,&count));check(GRBgetdblattr(m.model,GRB_DBL_ATTR_RUNTIME,&runtime));check(GRBgetdblattr(m.model,GRB_DBL_ATTR_WORK,&work));check(GRBgetdblattr(m.model,GRB_DBL_ATTR_NODECOUNT,&nodes));check(GRBgetdblattr(m.model,GRB_DBL_ATTR_OBJBOUND,&bound));
                if(count&&!cb.failed){std::vector<double>values(m.cols);check(GRBgetdblattrarray(m.model,GRB_DBL_ATTR_X,0,m.cols,values.data()));cb.consider(values,"FINAL");check(GRBwrite(m.model,(folder/"native.sol").string().c_str()));}
                std::ofstream receipt(folder/"result.json");receipt<<std::setprecision(17)<<"{\"Status\":"<<status<<",\"SolCount\":"<<count<<",\"Runtime\":"<<runtime<<",\"Work\":"<<work<<",\"NodeCount\":"<<nodes<<",\"native_restricted_bound\":";
                if(std::isfinite(bound)&&std::abs(bound)<1e90)receipt<<bound;else receipt<<"null";
                receipt<<",\"scale\":"<<m.scale<<",\"build_seconds\":"<<build<<",\"solve_outer_seconds\":"<<solve_seconds<<",\"validation_seconds\":"<<cb.verify_seconds<<",\"accepted\":"<<cb.accepted<<",\"incumbents_seen\":"<<cb.seen<<",\"best_J\":"<<cb.best.j<<",\"callback_failed\":"<<(cb.failed?"true":"false")<<",\"global_proof_changes\":0}\n";receipt.close();
                need(!cb.failed,"physical callback rejected model incumbent: "+cb.failure);if(cb.best.j<next.j-Accept)next=cb.best;out.improvements+=cb.accepted;
            }
            if(next.j<current.j-Accept){current=next;save(evidence/"best.json",d,current);}
            trace<<"{\"pass\":"<<pass<<",\"anchor\":"<<anchor<<",\"block\":"<<number-1<<",\"B\":";array(trace,B);trace<<",\"J\":"<<current.j<<",\"whole_seconds\":"<<elapsed(whole)<<"}\n";trace.flush();
            if(cfg.qualify_only){stop=true;break;}
        }
        if(out.improvements==pass_improvements)break;
    }
    save(evidence/"final.json",d,current);out.routes=current.routes;out.objective=current.j;
    std::ofstream summary(evidence/"summary.json");summary<<std::setprecision(17)<<"{\"J\":"<<current.j<<",\"calls\":"<<out.calls<<",\"accepted\":"<<out.improvements<<",\"anchors\":"<<out.anchors<<",\"deadline\":"<<(out.deadline?"true":"false")<<",\"seconds\":"<<elapsed(whole)<<",\"nodes_per_block\":"<<cfg.nodes<<",\"passes\":"<<cfg.passes<<",\"global_proof_changes\":0}\n";return out;
}
} // namespace ebrp::round160
