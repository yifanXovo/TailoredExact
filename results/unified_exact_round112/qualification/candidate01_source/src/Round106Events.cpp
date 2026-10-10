#include "Round106Events.hpp"
#include "PaperK1AmSf.hpp"
#include "PhysicalDurationTolerance.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>

namespace ebrp {
namespace {
constexpr std::int64_t max_edge = std::numeric_limits<std::int64_t>::max()/1024;
double lowerSeconds(std::int64_t ms) {
    return ms ? std::nextafter(static_cast<double>(ms)/1000.0,0.0) : 0.0;
}
double handling(const Instance& in) {
    const double h=in.pickup_time+in.drop_time;
    if(!std::isfinite(h)||in.pickup_time<0||in.drop_time<0)
        throw std::runtime_error("round106_invalid_handling");
    return h ? std::nextafter(h,0.0) : 0.0;
}
double margin(const Instance& in) {return 1e-5*std::max(1.0,in.total_time_limit);}
std::string z(int k,int i) {return "z_"+std::to_string(k)+"_"+std::to_string(i);}
std::string p(int k,int i) {return "p_"+std::to_string(k)+"_"+std::to_string(i);}
std::string state(int i,int y) {return "state_"+std::to_string(i)+"_"+std::to_string(y);}
}
Round106Travel round106ConservativeTravel(const Instance& in) {
    if(!hasMetricTravelLowerBounds(in)||!std::isfinite(in.total_time_limit)||in.total_time_limit<0)
        throw std::runtime_error("round106_requires_inherited_metric_domain");
    Round106Travel out;const int n=in.V+1;
    out.milliseconds.assign(n,std::vector<std::int64_t>(n,0));
    for(int i=0;i<n;++i)for(int j=i+1;j<n;++j) {
        const long double arc=std::min(in.dist[i][j],in.dist[j][i]);
        const long double value=std::nextafter(arc*1000.0L,0.0L);
        if(value<0||value>max_edge)throw std::runtime_error("round106_travel_integer_range");
        out.milliseconds[i][j]=out.milliseconds[j][i]=static_cast<std::int64_t>(std::floor(value));
    }
    // Each closure arc is <= each corresponding actual directed input arc.
    // Integer Floyd restores exact triangle inequalities after arc flooring.
    for(int k=0;k<n;++k)for(int i=0;i<n;++i)for(int j=0;j<n;++j)
        out.milliseconds[i][j]=std::min(out.milliseconds[i][j],
            out.milliseconds[i][k]+out.milliseconds[k][j]);
    (void)handling(in);return out;
}
double round106Mst(const Round106Travel& t,const std::vector<int>& stations,
                   std::vector<std::pair<int,int>>* edges) {
    std::vector<int> nodes{0};nodes.insert(nodes.end(),stations.begin(),stations.end());
    std::set<int> unique(nodes.begin(),nodes.end());
    if(unique.size()!=nodes.size())throw std::runtime_error("round106_mst_duplicate_support");
    const int n=static_cast<int>(nodes.size());
    std::vector<std::int64_t> best(n,max_edge);std::vector<int> parent(n,-1);
    std::vector<bool> used(n,false);best[0]=0;std::int64_t sum=0;
    if(edges)edges->clear();
    for(int step=0;step<n;++step) {
        int a=-1;for(int j=0;j<n;++j)if(!used[j]&&(a<0||best[j]<best[a]))a=j;
        if(a<0||best[a]>=max_edge||sum>max_edge-best[a])throw std::runtime_error("round106_mst_range");
        sum+=best[a];used[a]=true;if(edges&&parent[a]>=0)edges->push_back({nodes[parent[a]],nodes[a]});
        for(int j=0;j<n;++j)if(!used[j]) {
            const auto d=t.milliseconds.at(nodes[a]).at(nodes[j]);
            if(d<best[j]) {best[j]=d;parent[j]=a;}
        }
    }
    return lowerSeconds(sum);
}
std::vector<Round106Certificate> round106Separate(const Instance& in,
    const Round105Pattern& mode,const Round106Travel& travel,const std::function<bool()>& expired) {
    round105ValidatePattern(in,mode);
    std::vector<Round106Certificate> out;
    auto done=[&](){return expired&&expired();};
    const double h=handling(in), T=in.total_time_limit+kPhysicalDurationTolerance, safety=margin(in);
    std::vector<int> pickups,services;
    for(int i=1;i<=in.V;++i)if(mode.operation[i]) {
        services.push_back(i);if(mode.operation[i]>0)pickups.push_back(i);
    }
    auto amount=[&](const std::vector<int>& s){long long q=0;for(int i:s)q+=mode.operation[i];return q;};
    auto violatedA=[&](const std::vector<int>& s){return !s.empty()&&
        h*amount(s)+round106Mst(travel,s)>T+safety;};
    if(!done()&&violatedA(pickups)) {
        // Dynamic current pickup support, deterministic deletion; no subset enumeration.
        auto support=pickups;
        for(int i:pickups) {
            if(done())break;
            auto trial=support;trial.erase(std::remove(trial.begin(),trial.end(),i),trial.end());
            if(violatedA(trial))support=std::move(trial);
        }
        Round106Certificate c;c.family="A_MST";c.vehicle=mode.vehicle;c.support=support;
        c.pickup=amount(support);c.handling_lower=h;
        c.travel_lower=round106Mst(travel,support,&c.mst_edges);
        c.budget_margin=h*c.pickup+c.travel_lower-T;
        c.row.assumptions=support;c.row.positive_groups=static_cast<int>(support.size());
        c.row.rhs=T+c.travel_lower*(support.size()-1);
        for(int i:support) {
            c.operations.push_back(mode.operation[i]);
            c.row.coefficients[p(mode.vehicle,i)]=h;
            c.row.coefficients[z(mode.vehicle,i)]=c.travel_lower;
        }
        out.push_back(std::move(c));
    }
    if(h==0||done())return out;
    // Fixed-order balanced three-station family. Match two amounts to the third.
    std::map<int,std::vector<int>> by_amount;
    for(int i:services)by_amount[mode.operation[i]].push_back(i);
    for(std::size_t a=0;a<services.size()&&!done();++a)
      for(std::size_t b=a+1;b<services.size()&&!done();++b) {
        const int i=services[a],j=services[b];
        const long long wanted=-static_cast<long long>(mode.operation[i])-mode.operation[j];
        if(wanted<std::numeric_limits<int>::min()||wanted>std::numeric_limits<int>::max())continue;
        const auto match=by_amount.find(static_cast<int>(wanted));if(match==by_amount.end())continue;
        for(int l:match->second)if(l>j) {
            if(done())return out;
            Round106Certificate c;c.vehicle=mode.vehicle;c.support={i,j,l};c.handling_lower=h;
            for(int s:c.support){const int q=mode.operation[s];c.operations.push_back(q);
                c.pickup+=std::max(0,q);c.delivery+=std::max(0,-q);}
            if(c.pickup!=c.delivery||c.pickup<=0)throw std::runtime_error("round106_balanced_match_contract");
            std::array<int,3> order{i,j,l};std::int64_t minimum=max_edge;bool all_infeasible=true;
            do {
                Round106OrderProof proof;proof.order=order;long long load=0;proof.prefix_feasible=true;
                std::int64_t ms=0;int last=0;
                for(int q=0;q<3;++q) {
                    const int s=order[q];ms+=travel.milliseconds[last][s];last=s;
                    load+=mode.operation[s];proof.loads[q]=load;
                    if(load<0||load>in.Q[mode.vehicle])proof.prefix_feasible=false;
                }
                ms+=travel.milliseconds[last][0];minimum=std::min(minimum,ms);
                proof.travel_lower=lowerSeconds(ms);proof.duration_lower=proof.travel_lower+h*c.pickup;
                if(proof.prefix_feasible&&proof.duration_lower<=T+safety)all_infeasible=false;
                c.orders.push_back(proof);
            }while(std::next_permutation(order.begin(),order.end()));
            c.travel_lower=lowerSeconds(minimum);
            c.budget_margin=c.travel_lower+h*(c.pickup+1)-T;
            if(!all_infeasible||c.budget_margin<=safety)continue;
            c.row.assumptions=c.support;c.row.positive_groups=3;c.row.rhs=5;
            for(int s:c.support) {c.row.coefficients[z(mode.vehicle,s)]=1;
                c.row.coefficients[state(s,in.initial[s]-mode.operation[s])]=1;}
            c.family="B_EXACT";out.push_back(c);
            c.family="B_THRESHOLD";c.row.coefficients.clear();
            for(int s:c.support) {
                c.row.coefficients[z(mode.vehicle,s)]=1;
                const int threshold=in.initial[s]-mode.operation[s];
                for(int y=0;y<=in.capacity[s];++y) {
                    if((y&1023)==0&&done())return out;
                    if((mode.operation[s]>0&&y<=threshold)||(mode.operation[s]<0&&y>=threshold))
                        c.row.coefficients[state(s,y)]=1;
                    if(y==in.capacity[s])break;
                }
            }
            out.push_back(std::move(c));
        }
      }
    return out;
}
void round106WriteCertificate(const std::filesystem::path& path,const Round106Certificate& c) {
    std::filesystem::create_directories(path.parent_path());std::ofstream f(path);
    f<<std::setprecision(17)<<std::boolalpha<<"{\"family\":"<<std::quoted(c.family)
      <<",\"vehicle\":"<<c.vehicle<<",\"support\":[";
    for(std::size_t j=0;j<c.support.size();++j){if(j)f<<',';f<<c.support[j];}
    f<<"],\"operations\":[";for(std::size_t j=0;j<c.operations.size();++j){if(j)f<<',';f<<c.operations[j];}
    f<<"],\"pickup\":"<<c.pickup<<",\"delivery\":"<<c.delivery
      <<",\"travel_lower\":"<<c.travel_lower<<",\"handling_lower\":"<<c.handling_lower
      <<",\"budget_margin\":"<<c.budget_margin<<",\"rhs\":"<<c.row.rhs<<",\"mst_edges\":[";
    for(std::size_t j=0;j<c.mst_edges.size();++j){if(j)f<<',';f<<'['<<c.mst_edges[j].first<<','<<c.mst_edges[j].second<<']';}
    f<<"],\"orders\":[";
    for(std::size_t j=0;j<c.orders.size();++j){if(j)f<<',';const auto& o=c.orders[j];
        f<<"{\"order\":["<<o.order[0]<<','<<o.order[1]<<','<<o.order[2]<<"],\"loads\":["
         <<o.loads[0]<<','<<o.loads[1]<<','<<o.loads[2]<<"],\"prefix_feasible\":"<<o.prefix_feasible
         <<",\"travel_lower\":"<<o.travel_lower<<",\"duration_lower\":"<<o.duration_lower<<'}';}
    f<<"],\"coefficients\":{";bool first=true;
    for(const auto& [name,value]:c.row.coefficients){if(!first)f<<',';first=false;f<<std::quoted(name)<<':'<<value;}
    f<<"}}\n";f.flush();if(!f)throw std::runtime_error("round106_certificate_persist_failed");
}
} // namespace ebrp
