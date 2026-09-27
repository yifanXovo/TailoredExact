#include "Round62Thresholds.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <functional>
#include <iomanip>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>

namespace ebrp {
namespace {
double margin(const Instance& in) { return 1e-5*std::max(1.0,in.total_time_limit); }
double pairTravel(const std::vector<std::vector<double>>& d,int i,int j) {
    return std::min(d[0][i]+d[i][j]+d[j][0],d[0][j]+d[j][i]+d[i][0]);
}
std::vector<int> eligible(const Instance& in,const std::vector<std::vector<double>>& d,const Round62Event& e) {
    std::vector<int> out;
    const double single=d[0][e.station]+d[e.station][0]+(in.pickup_time+in.drop_time)*e.quantity;
    for (int k=0;k<in.M;++k)
        if (e.quantity<=in.Q[k] && single<=in.total_time_limit+margin(in)) out.push_back(k);
    return out;
}
std::string signature(const std::vector<Round62Event>& events) {
    std::string s;
    for (const auto& e:events) s+=e.name()+";";
    return s;
}
bool validMode(const std::string& s) {
    return s=="events"||s=="conflicts"||s=="projection"||s=="service"||s=="service-conflicts"||s=="projection-rlt"||s=="projection-service";
}
bool dominates(const Round62Conflict& a,const Round62Conflict& b) {
    // Only the same station/direction support. Smaller thresholds forbid a superset.
    if (a.events.size()!=b.events.size()) return false;
    for (std::size_t j=0;j<a.events.size();++j) {
        const auto& x=a.events[j];const auto& y=b.events[j];
        if (x.station!=y.station||x.direction!=y.direction||x.quantity>y.quantity) return false;
    }
    return true;
}
} // namespace
std::string Round62Event::name() const {
    return std::string(direction<0?"r62lo_":"r62hi_")+std::to_string(station)+"_"+std::to_string(quantity);
}
std::vector<std::vector<double>> round62Shortest(const Instance& in) {
    auto d=in.dist;
    if (static_cast<int>(d.size())!=in.V+1 || in.M<1 || static_cast<int>(in.Q.size())!=in.M ||
        in.pickup_time<0 || in.drop_time<0 || !std::isfinite(in.pickup_time+in.drop_time))
        throw std::runtime_error("invalid threshold input");
    for (auto& row:d) {
        if (row.size()!=d.size()) throw std::runtime_error("invalid distance shape");
        for (double v:row) if (!std::isfinite(v)||v<0) throw std::runtime_error("negative/nonfinite travel");
    }
    for (int i=0;i<=in.V;++i) d[i][i]=0;
    for (int k=0;k<=in.V;++k) for(int i=0;i<=in.V;++i) for(int j=0;j<=in.V;++j)
        d[i][j]=std::min(d[i][j],d[i][k]+d[k][j]);
    return d;
}
bool proveRound62Conflict(const Instance& in,const std::vector<std::vector<double>>& d,
                         const std::vector<Round62Event>& events,Round62Conflict* proof) {
    Round62Conflict p;p.events=events;std::set<int> stations,vehicles;
    for (const auto& e:events) {
        if (e.station<1||e.station>in.V||!stations.insert(e.station).second||e.quantity<=0||
            (e.direction!=-1&&e.direction!=1)||e.quantity>(e.direction<0?in.initial[e.station]:
             in.capacity[e.station]-in.initial[e.station])) return false;
        p.eligible.push_back(eligible(in,d,e));
        vehicles.insert(p.eligible.back().begin(),p.eligible.back().end());
    }
    for (std::size_t i=0;i<events.size();++i) for (std::size_t j=i+1;j<events.size();++j) {
        const auto& a=events[i];const auto& b=events[j];Round62Edge edge;
        edge.first=static_cast<int>(i);edge.second=static_cast<int>(j);
        edge.travel_lower=pairTravel(d,a.station,b.station);
        edge.handling_lower=(in.pickup_time+in.drop_time)*(a.direction==b.direction?
            a.quantity+b.quantity:std::max(a.quantity,b.quantity));
        edge.duration_lower=edge.travel_lower+edge.handling_lower;
        std::set_intersection(p.eligible[i].begin(),p.eligible[i].end(),p.eligible[j].begin(),p.eligible[j].end(),
            std::back_inserter(edge.common_vehicles));
        if (!edge.common_vehicles.empty() && edge.duration_lower<=in.total_time_limit+margin(in)) return false;
        p.edges.push_back(edge);
    }
    p.vehicle_union.assign(vehicles.begin(),vehicles.end());
    if (events.empty()||events.size()<=vehicles.size()) return false;
    if(proof) *proof=std::move(p);
    return true;
}
Round62ThresholdProof generateRound62Thresholds(const Instance& in) {
    const auto start=std::chrono::steady_clock::now();Round62ThresholdProof out;
    out.shortest=round62Shortest(in);out.margin=margin(in);
    const int maxQ=*std::max_element(in.Q.begin(),in.Q.end());
    const double c=in.pickup_time+in.drop_time;
    std::vector<Round62Event> candidates;
    // Two maximal direction events per station; no Cartesian inventory expansion.
    for (int i=1;i<=in.V;++i) for(int sign:{-1,1}) {
        int q=std::min(maxQ,sign<0?in.initial[i]:in.capacity[i]-in.initial[i]);
        if (c>0) q=std::min(q,static_cast<int>(std::floor((in.total_time_limit+out.margin-
            out.shortest[0][i]-out.shortest[i][0])/c)));
        if(q>0) candidates.push_back({i,sign,q});
    }
    out.initial_events=static_cast<int>(candidates.size());
    std::vector<std::vector<bool>> edges(candidates.size(),std::vector<bool>(candidates.size()));
    for(std::size_t i=0;i<candidates.size();++i) for(std::size_t j=i+1;j<candidates.size();++j) {
        if(candidates[i].station==candidates[j].station) continue;
        ++out.pair_checks;
        const auto& a=candidates[i];const auto& b=candidates[j];
        const double lb=pairTravel(out.shortest,a.station,b.station)+c*(a.direction==b.direction?
            a.quantity+b.quantity:std::max(a.quantity,b.quantity));
        out.maximum_pair_lower=std::max(out.maximum_pair_lower,lb);
        const auto ka=eligible(in,out.shortest,a),kb=eligible(in,out.shortest,b);
        std::vector<int> common;
        std::set_intersection(ka.begin(),ka.end(),kb.begin(),kb.end(),std::back_inserter(common));
        edges[i][j]=edges[j][i]=common.empty()||lb>in.total_time_limit+out.margin;
        out.incompatible_edges+=edges[i][j];
    }
    std::vector<std::vector<Round62Event>> seeds;
    std::vector<int> selected;
    std::function<void(int)> search=[&](int next) {
        if(out.clique_search_nodes>=50000||seeds.size()>=64) {out.search_truncated=true;return;}
        ++out.clique_search_nodes;
        std::vector<Round62Event> es;for(int index:selected) es.push_back(candidates[index]);
        if(proveRound62Conflict(in,out.shortest,es)) {seeds.push_back(es);return;}
        if(selected.size()>=static_cast<std::size_t>(in.M+1)) return;
        for(int j=next;j<static_cast<int>(candidates.size());++j) {
            bool all=true;for(int k:selected) if(!edges[k][j]) {all=false;break;}
            if(!all) continue;
            selected.push_back(j);search(j+1);selected.pop_back();
            if(out.search_truncated)return;
        }
    };
    search(0);
    std::set<std::string> seen;
    for(auto es:seeds) {
        for(std::size_t j=0;j<es.size();++j) {
            int lo=1,hi=es[j].quantity;
            while(lo<hi && out.weakening_checks<4096) {
                const int mid=lo+(hi-lo)/2;auto trial=es;trial[j].quantity=mid;
                ++out.weakening_checks;
                if(proveRound62Conflict(in,out.shortest,trial)) hi=mid;else lo=mid+1;
            }
            es[j].quantity=hi;
        }
        Round62Conflict proof;
        if(!proveRound62Conflict(in,out.shortest,es,&proof)) throw std::runtime_error("weakening lost proof");
        if(!seen.insert(signature(es)).second)continue;
        bool dominated=false;for(const auto& old:out.conflicts) if(dominates(old,proof))dominated=true;
        if(dominated)continue;
        out.conflicts.erase(std::remove_if(out.conflicts.begin(),out.conflicts.end(),[&](auto& x){return dominates(proof,x);}),out.conflicts.end());
        out.conflicts.push_back(proof);
        if(out.conflicts.size()>=32)break;
    }
    std::map<std::string,Round62Event> dict;
    for(const auto& p:out.conflicts)for(const auto& e:p.events)dict[e.name()]=e;
    for(const auto& e:dict)out.dictionary.push_back(e.second);
    out.seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    return out;
}
std::vector<Round62Row> round62ThresholdRows(const Instance& in,const Round62ThresholdProof& proof,const std::string& mode,double gamma_lower,double gamma_upper) {
    if(!validMode(mode)||proof.scope!="original_physical_global") throw std::runtime_error("invalid threshold mode/scope");
    if(!proof.conflicts.empty() && proof.shortest!=round62Shortest(in))
        throw std::runtime_error("threshold proof belongs to different travel data");
    if(mode=="projection-rlt") {
        if(!std::isfinite(gamma_lower)||!std::isfinite(gamma_upper)||gamma_lower<0||gamma_upper<gamma_lower||gamma_upper>1)
            throw std::runtime_error("invalid RLT Gini interval");
        auto base=round62ThresholdRows(in,proof,"projection");auto all=base;
        for(const auto& r:base) {
            Round62Row lower,upper;
            lower.name=r.name+"_rlt_lower";upper.name=r.name+"_rlt_upper";
            lower.rhs=-r.rhs*gamma_lower;upper.rhs=r.rhs*gamma_upper;
            lower.coefficients["G"]=-r.rhs;upper.coefficients["G"]=r.rhs;
            lower.scope=upper.scope="canonical_gini_interval";
            lower.gamma_lower=upper.gamma_lower=gamma_lower;lower.gamma_upper=upper.gamma_upper=gamma_upper;
            for(const auto& [name,a]:r.coefficients) {
                if(name.rfind("Y_",0)!=0)throw std::runtime_error("non-inventory projection");
                const std::string w="zprod_"+name.substr(2);
                lower.coefficients[w]=a;upper.coefficients[w]=-a;
                if(gamma_lower!=0)lower.coefficients[name]=-gamma_lower*a;
                if(gamma_upper!=0)upper.coefficients[name]=gamma_upper*a;
            }
            all.push_back(lower);all.push_back(upper);
        }
        return all;
    }
    std::vector<Round62Row> rows;
    const bool projected=mode=="projection" || mode=="projection-service";
    const int maxQ=*std::max_element(in.Q.begin(),in.Q.end());
    auto domain=[&](int i){return std::make_pair(std::max(0,in.initial[i]-maxQ),std::min(in.capacity[i],in.initial[i]+maxQ));};
    if(!projected) {
        for(const auto& e:proof.dictionary) {
            const auto [L,U]=domain(e.station);const int theta=in.initial[e.station]+e.direction*e.quantity;
            const auto y="Y_"+std::to_string(e.station),z=e.name();
            const bool always=e.direction<0?U<=theta:L>=theta,never=e.direction<0?L>theta:U<theta;
            if(always||never) {rows.push_back({z+"_constant",{{z,1}},'=',always?1.0:0.0});continue;}
            if(e.direction<0) {
                rows.push_back({z+"_upper",{{y,1},{z,static_cast<double>(U-theta)}},'<',static_cast<double>(U)});
                rows.push_back({z+"_lower",{{y,1},{z,static_cast<double>(theta+1-L)}},'>',static_cast<double>(theta+1)});
            } else {
                rows.push_back({z+"_lower",{{y,1},{z,-static_cast<double>(theta-L)}},'>',static_cast<double>(L)});
                rows.push_back({z+"_upper",{{y,1},{z,-static_cast<double>(U-theta+1)}},'<',static_cast<double>(theta-1)});
            }
            if(mode=="service"||mode=="service-conflicts") {
                // Joint service representation: valid because there is at most one
                // nonzero unidirectional visit over all vehicles at a station.
                const int cap=std::min(maxQ,e.direction<0?in.initial[e.station]:in.capacity[e.station]-in.initial[e.station]);
                Round62Row lower{z+"_service_lower",{{z,-static_cast<double>(e.quantity)}},'>',0};
                Round62Row upper{z+"_service_upper",{{z,-static_cast<double>(cap-e.quantity+1)}},'<',static_cast<double>(e.quantity-1)};
                Round62Row visit{z+"_visit",{{z,1}},'<',0};
                for(int k=0;k<in.M;++k) {
                    const auto prefix=std::to_string(k)+"_"+std::to_string(e.station);
                    const auto quantity=(e.direction<0?"p_":"d_")+prefix;
                    lower.coefficients[quantity]=upper.coefficients[quantity]=1;
                    visit.coefficients["z_"+prefix]=-1;
                }
                rows.push_back(lower);rows.push_back(upper);rows.push_back(visit);
            }
        }
        for(const auto& a:proof.dictionary)for(const auto& b:proof.dictionary)
            if(a.station==b.station&&a.direction==b.direction&&a.quantity<b.quantity)
                rows.push_back({b.name()+"_nested_"+std::to_string(a.quantity),{{b.name(),1},{a.name(),-1}},'<',0});
    }
    if(mode=="conflicts"||mode=="service-conflicts"||projected) {
        int index=0;
        for(const auto& conflict:proof.conflicts) {
            Round62Conflict verified;
            if(!proveRound62Conflict(in,proof.shortest,conflict.events,&verified) ||
               verified.eligible!=conflict.eligible || verified.vehicle_union!=conflict.vehicle_union)
                throw std::runtime_error("invalid or stale row proof");
            Round62Row row;row.name="r62conflict_"+std::to_string(index++);
            if(!projected) {
                row.sense='<';row.rhs=static_cast<double>(conflict.vehicle_union.size());
                for(const auto& e:conflict.events)row.coefficients[e.name()]=1;
            } else if(mode=="projection-service") {
                // At least one required service event is false. Unlike a net-Y
                // term, this term has no opposite-direction service slack.
                row.sense='>';row.rhs=1;bool redundant=false;
                for(const auto& e:conflict.events) {
                    const int cap=std::min(maxQ,e.direction<0?in.initial[e.station]:in.capacity[e.station]-in.initial[e.station]);
                    if(e.quantity>cap){redundant=true;break;}
                    const double denominator=cap-e.quantity+1;
                    if(denominator<=0)throw std::runtime_error("invalid service projection denominator");
                    row.rhs-=cap/denominator;
                    for(int k=0;k<in.M;++k)
                        row.coefficients[(e.direction<0?"p_":"d_")+std::to_string(k)+"_"+std::to_string(e.station)]=-1.0/denominator;
                }
                if(redundant)continue;
            } else {
                row.sense='>';row.rhs=1;bool redundant=false;
                for(const auto& e:conflict.events) {
                    const auto [L,U]=domain(e.station);const int theta=in.initial[e.station]+e.direction*e.quantity;
                    const bool never=e.direction<0?L>theta:U<theta,always=e.direction<0?U<=theta:L>=theta;
                    if(never){redundant=true;break;}if(always)continue;
                    const double denom=e.direction<0?theta+1-L:U-theta+1;
                    if(denom<=0)throw std::runtime_error("invalid projection denominator");
                    row.coefficients["Y_"+std::to_string(e.station)]=(e.direction<0?1.0:-1.0)/denom;
                    row.rhs+=(e.direction<0?L:-U)/denom;
                }
                if(redundant)continue;
            }
            rows.push_back(row);
        }
    }
    return rows;
}
void writeRound62ThresholdProof(const Instance& in,const Round62ThresholdProof& p,const std::vector<Round62Row>& rows,const std::filesystem::path& path) {
    std::ofstream f(path);f<<std::setprecision(17);
    f<<"{\"scope\":\""<<p.scope<<"\",\"T\":"<<in.total_time_limit<<",\"handling\":"<<in.pickup_time+in.drop_time
     <<",\"margin\":"<<p.margin<<",\"seconds\":"<<p.seconds<<",\"initial_events\":"<<p.initial_events
     <<",\"pair_checks\":"<<p.pair_checks<<",\"incompatible_edges\":"<<p.incompatible_edges<<",\"maximum_pair_lower\":"<<p.maximum_pair_lower
     <<",\"search_nodes\":"<<p.clique_search_nodes<<",\"weakening_checks\":"<<p.weakening_checks<<",\"truncated\":"<<(p.search_truncated?"true":"false")
     <<",\"dictionary_size\":"<<p.dictionary.size()<<",\"conflicts\":[";
    for(std::size_t j=0;j<p.conflicts.size();++j) {
        if(j)f<<',';const auto& c=p.conflicts[j];f<<"{\"events\":[";
        for(std::size_t i=0;i<c.events.size();++i) {
            if(i)f<<',';const auto& e=c.events[i];f<<"{\"station\":"<<e.station<<",\"direction\":"<<e.direction<<",\"q\":"<<e.quantity<<",\"eligible\":[";
            for(std::size_t k=0;k<c.eligible[i].size();++k){if(k)f<<',';f<<c.eligible[i][k];}f<<"]}";
        }
        f<<"],\"edges\":[";
        for(std::size_t i=0;i<c.edges.size();++i){if(i)f<<',';const auto& e=c.edges[i];
            f<<"{\"first\":"<<e.first<<",\"second\":"<<e.second<<",\"travel\":"<<e.travel_lower<<",\"handling\":"<<e.handling_lower<<",\"duration\":"<<e.duration_lower<<",\"common\":[";
            for(std::size_t k=0;k<e.common_vehicles.size();++k){if(k)f<<',';f<<e.common_vehicles[k];}f<<"]}";}
        f<<"],\"vehicle_union\":[";for(std::size_t k=0;k<c.vehicle_union.size();++k){if(k)f<<',';f<<c.vehicle_union[k];}f<<"]}";
    }
    f<<"],\"rows\":[";
    for(std::size_t i=0;i<rows.size();++i){if(i)f<<',';const auto& r=rows[i];f<<"{\"name\":\""<<r.name<<"\",\"sense\":\""<<r.sense<<"\",\"rhs\":"<<r.rhs
        <<",\"scope\":\""<<r.scope<<"\",\"gamma_lower\":"<<r.gamma_lower<<",\"gamma_upper\":"<<r.gamma_upper<<",\"coefficients\":{";
        bool comma=false;for(const auto& [n,v]:r.coefficients){if(comma)f<<',';comma=true;f<<'"'<<n<<"\":"<<v;}f<<"}}";}
    f<<"],\"domains\":[";
    const int maxQ=*std::max_element(in.Q.begin(),in.Q.end());
    for(int i=1;i<=in.V;++i){if(i>1)f<<',';f<<"["<<i<<','<<std::max(0,in.initial[i]-maxQ)<<','<<std::min(in.capacity[i],in.initial[i]+maxQ)<<']';}
    f<<"]}\n";if(!f)throw std::runtime_error("threshold proof persistence failed");
}
void appendRound62ThresholdModel(const Instance& in,const std::filesystem::path& path,const std::string& mode,double gamma_lower,double gamma_upper) {
    if(mode=="off")return;
    auto p=generateRound62Thresholds(in);const auto rows=round62ThresholdRows(in,p,mode,gamma_lower,gamma_upper);
    writeRound62ThresholdProof(in,p,rows,path.string()+".round62.json");
    if(rows.empty())return;
    std::ifstream input(path);std::string model((std::istreambuf_iterator<char>(input)),{});input.close();
    std::ostringstream added;added<<std::setprecision(17);
    for(const auto& row:rows) {
        added<<' '<<row.name<<":";
        for(const auto& [name,value]:row.coefficients)added<<(value>=0?" + ":" - ")<<std::fabs(value)<<' '<<name;
        added<<(row.sense=='<'?" <= ":row.sense=='>'?" >= ":" = ")<<row.rhs<<'\n';
    }
    const auto bounds=model.find("\nBounds");if(bounds==std::string::npos)throw std::runtime_error("LP Bounds missing");
    model.insert(bounds+1,added.str());
    if(mode!="projection"&&mode!="projection-rlt"&&mode!="projection-service") {
        std::ostringstream vars;for(const auto& e:p.dictionary)vars<<' '<<e.name()<<'\n';
        const auto binaries=model.find("\nBinary\n");
        const auto binaries2=model.find("\nBinaries\n");
        if(binaries!=std::string::npos)model.insert(binaries+8,vars.str());
        else if(binaries2!=std::string::npos)model.insert(binaries2+10,vars.str());
        else {const auto end=model.rfind("End");if(end==std::string::npos)throw std::runtime_error("LP End missing");model.insert(end,"Binary\n"+vars.str());}
    }
    std::ofstream output(path);output<<model;if(!output)throw std::runtime_error("threshold LP write failed");
}
} // namespace ebrp
