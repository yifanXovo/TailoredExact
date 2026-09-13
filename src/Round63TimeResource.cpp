#include "Round63TimeResource.hpp"
#include "DeterministicDinic.hpp"
#include "FileSha256.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>

namespace ebrp {
namespace {
double down(double x) { return x>0?std::nextafter(x,0.0):0.0; }
double up(double x) { return std::nextafter(x,std::numeric_limits<double>::infinity()); }
std::string xname(int k,int i,int j) {return "x_"+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(j);}
std::string pname(int k,int i) {return "p_"+std::to_string(k)+"_"+std::to_string(i);}
std::string fname(int k,int i,int j) {return "r63f_"+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(j);}
void validatePoint(const Round63TimeData& d,const Round63TimePoint& p,int k) {
    if(k<0||k>=d.M||p.x.size()!=static_cast<std::size_t>(d.M)||p.pickup.size()!=p.x.size())
        throw std::runtime_error("time point vehicle shape");
    if(p.x[k].size()!=static_cast<std::size_t>(d.V+1)||p.pickup[k].size()!=p.x[k].size())
        throw std::runtime_error("time point station shape");
    for(int i=0;i<=d.V;++i) {
        if(p.x[k][i].size()!=static_cast<std::size_t>(d.V+1)) throw std::runtime_error("time point arc shape");
        if(!std::isfinite(p.pickup[k][i])||p.pickup[k][i]<-1e-8) throw std::runtime_error("invalid raw pickup");
        for(int j=0;j<=d.V;++j) if(!std::isfinite(p.x[k][i][j])||p.x[k][i][j]<-1e-8)
            throw std::runtime_error("invalid raw route arc");
    }
}
void emitRow(std::ostream& o,const std::string& name,const std::map<std::string,double>& c,char sense='=',double rhs=0) {
    o<<' '<<name<<":";for(const auto& [n,v]:c) if(v!=0)o<<(v>=0?" + ":" - ")<<std::fabs(v)<<' '<<n;
    o<<(sense=='<'?" <= ":" = ")<<rhs<<'\n';
}
}
Round63TimeData prepareRound63Time(const Instance& in) {
    if(in.V<1||in.M<1||in.Q.size()!=static_cast<std::size_t>(in.M)||
       !std::isfinite(in.total_time_limit)||in.total_time_limit<0||
       !std::isfinite(in.pickup_time)||!std::isfinite(in.drop_time)||in.pickup_time<0||in.drop_time<0)
        throw std::runtime_error("invalid cumulative time input");
    Round63TimeData d;d.V=in.V;d.M=in.M;d.scale=std::max(1.0,in.total_time_limit);d.shortest=in.dist;
    if(in.dist.size()!=static_cast<std::size_t>(in.V+1))throw std::runtime_error("invalid time distances");
    for(const auto& r:in.dist) {
        if(r.size()!=in.dist.size())throw std::runtime_error("invalid time distance shape");
        for(double t:r)if(t<0||!std::isfinite(t))throw std::runtime_error("invalid time arc");
    }
    for(int i=0;i<=d.V;++i)d.shortest[i][i]=0;
    for(int h=0;h<=d.V;++h)for(int i=0;i<=d.V;++i)for(int j=0;j<=d.V;++j)
        d.shortest[i][j]=std::min(d.shortest[i][j],down(d.shortest[i][h]+d.shortest[h][j]));
    const long double handling=static_cast<long double>(in.pickup_time)+in.drop_time;
    if(!std::isfinite(static_cast<double>(handling)))throw std::runtime_error("handling overflow");
    d.handling=down(static_cast<double>(handling/d.scale));
    d.travel=in.dist;d.upper=in.dist;
    for(int i=0;i<=d.V;++i)for(int j=0;j<=d.V;++j) {
        d.travel[i][j]=i==j?0:down(in.dist[i][j]/d.scale);
        const long double b=static_cast<long double>(in.total_time_limit)-in.dist[i][j]-d.shortest[j][0];
        d.upper[i][j]=(i==0||i==j||b<=0)?0:up(static_cast<double>(b/d.scale));
    }
    std::ostringstream id;id<<std::setprecision(17)<<in.V<<','<<in.M<<','<<in.total_time_limit<<','<<in.pickup_time<<','<<in.drop_time;
    for(int q:in.Q){if(q<=0)throw std::runtime_error("invalid Q");id<<','<<q;}
    for(int b:in.initial)id<<','<<b;
    for(int b:in.capacity)id<<','<<b;
    for(const auto& r:in.dist)for(double t:r)id<<','<<t;
    d.identity=textSha256(id.str());return d;
}
Round63TimePoint emptyRound63TimePoint(const Round63TimeData& d) {
    return {std::vector<std::vector<std::vector<double>>>(d.M,std::vector<std::vector<double>>(d.V+1,std::vector<double>(d.V+1))),
            std::vector<std::vector<double>>(d.M,std::vector<double>(d.V+1))};
}
Round63TimeCut round63TimeRow(const Round63TimeData& d,int k,const std::vector<int>& support) {
    if(k<0||k>=d.M)throw std::runtime_error("invalid resource vehicle");
    Round63TimeCut r;r.vehicle=k;r.support=support;std::sort(r.support.begin(),r.support.end());r.identity=d.identity;
    std::vector<bool> inside(d.V+1);
    r.signature=d.identity+":"+std::to_string(k);
    for(int i:r.support) {
        if(i<1||i>d.V||inside[i])throw std::runtime_error("invalid resource support");
        inside[i]=true;r.signature+=":"+std::to_string(i);
    }
    for(int i:r.support) {
        if(d.handling)r.coefficients[pname(k,i)]=d.handling;
        for(int h=0;h<=d.V;++h)if(h!=i&&d.travel[h][i])r.coefficients[xname(k,h,i)]=d.travel[h][i];
        for(int j=0;j<=d.V;++j)if(!inside[j]&&d.upper[i][j])r.coefficients[xname(k,i,j)]=-d.upper[i][j];
    }
    return r;
}
double evaluateRound63TimeRow(const Round63TimeData& d,const Round63TimePoint& p,const Round63TimeCut& r) {
    validatePoint(d,p,r.vehicle);
    const auto canonical=round63TimeRow(d,r.vehicle,r.support);
    if(r.scope!="original_physical_global"||r.identity!=d.identity||r.signature!=canonical.signature||r.coefficients!=canonical.coefficients)
        throw std::runtime_error("stale or modified cumulative resource row");
    std::vector<bool> inside(d.V+1);for(int i:r.support)inside[i]=true;
    long double v=0;const int k=r.vehicle;
    for(int i:r.support) {
        v+=static_cast<long double>(d.handling)*p.pickup[k][i];
        for(int h=0;h<=d.V;++h)if(h!=i)v+=static_cast<long double>(d.travel[h][i])*p.x[k][h][i];
        for(int j=0;j<=d.V;++j)if(!inside[j])v-=static_cast<long double>(d.upper[i][j])*p.x[k][i][j];
    }
    return static_cast<double>(v);
}
Round63TimeCut separateRound63Time(const Round63TimeData& d,const Round63TimePoint& p,int k,double tolerance) {
    validatePoint(d,p,k);if(tolerance<0||!std::isfinite(tolerance))throw std::runtime_error("invalid time tolerance");
    DeterministicDinic graph(d.V+2);const int source=d.V+1;double total=0;
    for(int i=1;i<=d.V;++i) {
        double a=d.handling*std::max(0.0,p.pickup[k][i]);
        for(int h=0;h<=d.V;++h)if(h!=i)a+=d.travel[h][i]*std::max(0.0,p.x[k][h][i]);
        graph.addArc(source,i,a);total+=a;
        for(int j=0;j<=d.V;++j)if(j!=i)graph.addArc(i,j,d.upper[i][j]*std::max(0.0,p.x[k][i][j]));
    }
    const double flow=graph.maxFlow(source,0);const auto reachable=graph.sourceSide(source);
    std::vector<int> support;for(int i=1;i<=d.V;++i)if(reachable[i])support.push_back(i);
    auto r=round63TimeRow(d,k,support);r.source_capacity=total;r.mincut=flow;
    r.violation=evaluateRound63TimeRow(d,p,r);r.violated=!support.empty()&&r.violation>tolerance;
    return r;
}
bool acceptRound63TimeCut(const Round63TimeData& d,const Round63TimeCut& r,std::set<std::string>& seen) {
    const auto canonical=round63TimeRow(d,r.vehicle,r.support);
    if(r.scope!="original_physical_global"||r.identity!=d.identity||r.coefficients!=canonical.coefficients||r.signature!=canonical.signature)
        throw std::runtime_error("resource scope/coefficients mismatch");
    return r.violated&&r.violation>1e-7&&!r.support.empty()&&seen.insert(r.signature).second;
}
bool validRound63TimeMode(const std::string& m) {return m=="off"||m=="explicit"||m=="coupled"||m=="simple"||m=="dry"||m=="cuts"||m=="precrush"||m=="root"||m=="root-dry";}
void writeRound63TimeData(const Round63TimeData& d,const std::filesystem::path& path) {
    std::ofstream o(path);o<<std::setprecision(17)<<"{\"schema\":\"round63-resource-v1\",\"identity\":\""<<d.identity
        <<"\",\"scope\":\"original_physical_global\",\"V\":"<<d.V<<",\"M\":"<<d.M<<",\"scale\":"<<d.scale<<",\"handling\":"<<d.handling;
    auto matrix=[&](const char* name,const auto& m){o<<",\""<<name<<"\":[";for(int i=0;i<=d.V;++i){if(i)o<<',';o<<'[';for(int j=0;j<=d.V;++j){if(j)o<<',';o<<m[i][j];}o<<']';}o<<']';};
    matrix("travel",d.travel);matrix("upper",d.upper);matrix("shortest",d.shortest);o<<"}\n";
    if(!o)throw std::runtime_error("resource definition persistence failed");
}
void appendRound63TimeModel(const Instance& in,const std::filesystem::path& path,const std::string& mode) {
    if(!validRound63TimeMode(mode))throw std::runtime_error("invalid Round63 mode");
    if(mode=="off")return;
    const auto d=prepareRound63Time(in);writeRound63TimeData(d,path.string()+".round63.json");
    if(mode!="explicit"&&mode!="coupled"&&mode!="simple")return;
    std::ifstream f(path);std::string text((std::istreambuf_iterator<char>(f)),{});f.close();
    std::ostringstream rows;rows<<std::setprecision(17);long long count=0;
    for(int k=0;k<d.M;++k) {
        if(mode=="simple") {
            std::vector<int> all;for(int i=1;i<=d.V;++i)all.push_back(i);
            auto r=round63TimeRow(d,k,all);emitRow(rows,"r63_all_"+std::to_string(k),r.coefficients,'<');
            for(int i=1;i<=d.V;++i){r=round63TimeRow(d,k,{i});emitRow(rows,"r63_single_"+std::to_string(k)+"_"+std::to_string(i),r.coefficients,'<');}
            continue;
        }
        for(int i=1;i<=d.V;++i) {
            std::map<std::string,double> c;
            for(int j=0;j<=d.V;++j)if(i!=j)c[fname(k,i,j)]=1;
            for(int h=1;h<=d.V;++h)if(h!=i)c[fname(k,h,i)]=-1;
            if(d.handling)c[pname(k,i)]=-d.handling;
            for(int h=0;h<=d.V;++h)if(h!=i&&d.travel[h][i])c[xname(k,h,i)]=-d.travel[h][i];
            emitRow(rows,"r63_balance_"+std::to_string(count++),c);
            for(int j=0;j<=d.V;++j)if(i!=j) {
                c={{fname(k,i,j),1}};if(d.upper[i][j])c[xname(k,i,j)]=-d.upper[i][j];
                emitRow(rows,"r63_capacity_"+std::to_string(count++),c,'<');
            }
            if(mode=="coupled" && d.handling>0) {
                // load[k,i] is the existing post-service load. Empty departure
                // and nonnegative deliveries give load <= cumulative pickup.
                // On the unique outgoing route arc, f carries that prepaid
                // pickup resource plus nonnegative cumulative travel.
                c={{"load_"+std::to_string(k)+"_"+std::to_string(i),d.handling}};
                for(int j=0;j<=d.V;++j)if(i!=j)c[fname(k,i,j)]=-1;
                emitRow(rows,"r63_carried_"+std::to_string(k)+"_"+std::to_string(i),c,'<');
            }
        }
    }
    const auto bounds=text.find("\nBounds");if(bounds==std::string::npos)throw std::runtime_error("resource LP Bounds absent");
    text.insert(bounds+1,rows.str());std::ofstream out(path);out<<text;
    if(!out)throw std::runtime_error("resource LP write failed");
}
void writeRound63TimeCut(const Round63TimeCut& r,std::ostream& o,long long query,double node,int api_return) {
    o<<std::setprecision(17)<<"{\"query\":"<<query<<",\"node\":"<<node<<",\"vehicle\":"<<r.vehicle
     <<",\"identity\":\""<<r.identity<<"\",\"scope\":\""<<r.scope<<"\",\"violation\":"<<r.violation
     <<",\"source_capacity\":"<<r.source_capacity<<",\"mincut\":"<<r.mincut<<",\"api_return\":"<<api_return<<",\"support\":[";
    for(std::size_t i=0;i<r.support.size();++i){if(i)o<<',';o<<r.support[i];}o<<"],\"coefficients\":{";
    bool comma=false;for(const auto& [n,v]:r.coefficients){if(comma)o<<',';comma=true;o<<'"'<<n<<"\":"<<v;}o<<"}}\n";
}
} // namespace ebrp
