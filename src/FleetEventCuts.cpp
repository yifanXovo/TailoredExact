#include "FleetEventCuts.hpp"
#include "PhysicalDurationTolerance.hpp"
#include <algorithm>
#include <cfenv>
#include <cmath>
#include <iomanip>
#include <limits>
#include <numeric>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <unordered_map>
#if defined(__SSE__) || defined(_M_X64)
#include <xmmintrin.h>
#endif

namespace ebrp { namespace {
double down(double v) { return std::nextafter(v,-std::numeric_limits<double>::infinity()); }
double up(double v) { return std::nextafter(v,std::numeric_limits<double>::infinity()); }
double plusLower(double a,double b) { if(a==0)return b;if(b==0)return a;return std::max(0.0,down(a+b)); }
double timesLower(double a,long long b) { if(a==0||b==0)return 0;return std::max(0.0,down(a*static_cast<double>(b))); }
bool ready() {
    volatile double a=std::numeric_limits<double>::denorm_min(),b=a;
    volatile double sum=a+b;
    bool ok=std::numeric_limits<double>::is_iec559 && std::fegetround()==FE_TONEAREST && sum==2*std::numeric_limits<double>::denorm_min();
#if defined(__SSE__) || defined(_M_X64)
    ok=ok&&(_mm_getcsr()&0x8040u)==0;
#endif
    return ok;
}
void shortest(FleetContract& c) {
    c.shortest_lower=c.travel_lower;
    auto& d=c.shortest_lower;
    for(std::size_t i=0;i<d.size();++i)d[i][i]=0;
    for(std::size_t k=0;k<d.size();++k)for(std::size_t i=0;i<d.size();++i)for(std::size_t j=0;j<d.size();++j)
        d[i][j]=std::min(d[i][j],plusLower(d[i][k],d[k][j]));
}
bool goodEvents(const FleetContract& c,const std::vector<FleetEvent>& es) {
    std::set<int> used;
    if(!c.valid||!ready()||es.empty())return false;
    for(const auto& e:es)if(e.station<1||static_cast<std::size_t>(e.station)>=c.initial.size()||
        !used.insert(e.station).second||(e.direction!=-1&&e.direction!=1)||e.quantity<1||
        e.quantity>(e.direction<0?c.initial[e.station]:c.station_capacity[e.station]-c.initial[e.station]))return false;
    return true;
}
double single(const FleetContract& c,int i) { return plusLower(c.shortest_lower[0][i],c.shortest_lower[i][0]); }
bool eligible(const FleetContract& c,int k,const FleetEvent& e) {
    return e.quantity<=c.capacities[k]&&plusLower(single(c,e.station),timesLower(c.handling_lower,e.quantity))<=c.horizon_upper;
}
std::string key(const std::vector<FleetEvent>& es) {
    std::ostringstream s;for(auto e:es)s<<e.station<<':'<<e.direction<<':'<<e.quantity<<';';return s.str();
}
std::vector<double> tours(const FleetContract& c,const std::vector<FleetEvent>& es) {
    const int n=static_cast<int>(es.size()),N=1<<n;
    const double inf=std::numeric_limits<double>::infinity();
    std::vector<double> path(static_cast<std::size_t>(N)*n,inf),out(N,inf);out[0]=0;
    for(int j=0;j<n;++j)path[(1<<j)*n+j]=c.shortest_lower[0][es[j].station];
    for(int mask=1;mask<N;++mask)for(int j=0;j<n;++j)if(mask&(1<<j)) {
        const double v=path[mask*n+j];if(!std::isfinite(v))continue;
        out[mask]=std::min(out[mask],plusLower(v,c.shortest_lower[es[j].station][0]));
        for(int h=0;h<n;++h)if(!(mask&(1<<h))) {
            auto& w=path[(mask|(1<<h))*n+h];
            w=std::min(w,plusLower(v,c.shortest_lower[es[j].station][es[h].station]));
        }
    }
    return out;
}
// Maximum-cardinality bipartite matching to per-vehicle, per-direction slots.
// Every necessary assignment embeds in this relaxation; its optimum is an UPPER bound.
int matching(const std::vector<std::vector<int>>& eligible_sets,const std::vector<int>& cap) {
    std::vector<int> slots;for(std::size_t k=0;k<cap.size();++k)for(int j=0;j<cap[k];++j)slots.push_back(static_cast<int>(k));
    std::vector<int> owner(slots.size(),-1);int result=0;
    for(int e=0;e<static_cast<int>(eligible_sets.size());++e) {
        std::vector<unsigned char> seen(slots.size());
        auto dfs=[&](auto&& self,int event)->bool {
            for(std::size_t s=0;s<slots.size();++s)if(!seen[s]&&
                std::find(eligible_sets[event].begin(),eligible_sets[event].end(),slots[s])!=eligible_sets[event].end()) {
                seen[s]=1;if(owner[s]<0||self(self,owner[s])){owner[s]=event;return true;}
            }
            return false;
        };
        result+=dfs(dfs,e);
    }
    return result;
}
} // namespace

FleetContract physicalFleetContract(const Instance& in) {
    FleetContract c;c.initial=in.initial;c.station_capacity=in.capacity;c.capacities=in.Q;
    c.horizon_upper=up(in.total_time_limit+kPhysicalDurationTolerance);c.handling_lower=std::max(0.0,down(in.pickup_time+in.drop_time));c.travel_lower=in.dist;
    if(!ready()||in.V<1||in.M<1||in.Q.size()!=static_cast<std::size_t>(in.M)||
        in.initial.size()!=static_cast<std::size_t>(in.V+1)||in.capacity.size()!=in.initial.size()||
        in.dist.size()!=in.initial.size()||!std::isfinite(c.horizon_upper)||c.horizon_upper<0||
        !std::isfinite(in.pickup_time)||in.pickup_time<0||!std::isfinite(in.drop_time)||in.drop_time<0||
        !std::isfinite(c.handling_lower)){c.reason="invalid_physical_contract";return c;}
    for(int q:c.capacities)if(q<0){c.reason="invalid_capacity";return c;}
    for(auto& row:c.travel_lower) {
        if(row.size()!=in.initial.size()){c.reason="invalid_travel_shape";return c;}
        for(double x:row)if(!std::isfinite(x)||x<0){c.reason="invalid_travel_value";return c;}
    }
    for(int i=1;i<=in.V;++i)if(c.initial[i]<0||c.initial[i]>c.station_capacity[i]){c.reason="invalid_inventory";return c;}
    shortest(c);c.valid=true;c.reason="physical_only";c.proof_identity=fleetContractJson(c);return c;
}

FleetContract prepareFleetContract(const Instance& in,const NativeOtB1LinearModel& m) {
    auto c=physicalFleetContract(in);c.valid=false;
    try {
        if(c.reason!="physical_only")throw std::runtime_error(c.reason);
        const int n=static_cast<int>(m.names.size()),R=static_cast<int>(m.senses.size());c.columns=n;
        if(n<1||m.types.size()!=m.names.size()||m.lower_bounds.size()!=m.names.size()||m.upper_bounds.size()!=m.names.size()||
            m.rhs.size()!=m.senses.size()||m.row_starts.size()!=static_cast<std::size_t>(R+1)||m.row_starts.front()!=0||
            m.column_indices.size()!=m.coefficients.size()||m.row_starts.back()!=static_cast<int>(m.coefficients.size()))throw std::runtime_error("matrix_shape");
        std::unordered_map<std::string,int> col;
        std::vector<std::vector<int>> incident(n);
        for(int j=0;j<n;++j)if(!col.emplace(m.names[j],j).second||!std::isfinite(m.lower_bounds[j])||!std::isfinite(m.upper_bounds[j])||
            m.lower_bounds[j]>m.upper_bounds[j])throw std::runtime_error("column_identity_or_bounds");
        for(int r=0;r<R;++r) {
            if(m.row_starts[r]>m.row_starts[r+1]||!std::isfinite(m.rhs[r]))throw std::runtime_error("row_shape");
            std::set<int> used;
            for(int t=m.row_starts[r];t<m.row_starts[r+1];++t) {
                int j=m.column_indices[t];if(j<0||j>=n||!std::isfinite(m.coefficients[t])||!used.insert(j).second)throw std::runtime_error("matrix_coefficient");
                incident[j].push_back(r);
            }
        }
        auto column=[&](const std::string& name,char type,double lo,double hi) {
            const auto it=col.find(name);if(it==col.end())throw std::runtime_error("missing_column:"+name);
            const int j=it->second;if(m.types[j]!=type||m.lower_bounds[j]<lo||m.upper_bounds[j]>hi)throw std::runtime_error("column_contract:"+name);return j;
        };
        using Row=std::map<int,double>;
        auto require=[&](char sense,double rhs,Row expected) {
            for(auto it=expected.begin();it!=expected.end();)if(it->second==0)it=expected.erase(it);else ++it;
            if(expected.empty())throw std::runtime_error("empty_audit_row");
            int first=expected.begin()->first;
            for(auto [j,a]:expected){(void)a;if(incident[j].size()<incident[first].size())first=j;}
            for(int r:incident[first])if(m.senses[r]==sense&&m.rhs[r]==rhs&&
                m.row_starts[r+1]-m.row_starts[r]==static_cast<int>(expected.size())) {
                bool ok=true;for(int t=m.row_starts[r];t<m.row_starts[r+1];++t) {
                    auto it=expected.find(m.column_indices[t]);if(it==expected.end()||it->second!=m.coefficients[t]){ok=false;break;}
                }
                if(ok){++c.audited_rows;return;}
            }
            throw std::runtime_error("required_row_missing");
        };
        auto tag=[](const std::string& p,int k,int i){return p+std::to_string(k)+"_"+std::to_string(i);};
        auto arc=[](int k,int i,int j){return "x_"+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(j);};
        std::vector<std::vector<int>> p(in.M,std::vector<int>(in.V+1)),d=p,z=p,mode=p,u=p;
        std::vector<std::vector<std::vector<int>>> x(in.M,std::vector<std::vector<int>>(in.V+1,std::vector<int>(in.V+1,-1)));
        c.states.resize(in.V+1);
        for(int i=1;i<=in.V;++i) {
            const int y=column("Y_"+std::to_string(i),'I',0,in.capacity[i]);
            const int L=static_cast<int>(std::ceil(m.lower_bounds[y])),U=static_cast<int>(std::floor(m.upper_bounds[y]));
            Row one,link{{y,1}},balance{{y,1}},unique;
            for(int v=L;v<=U;++v) {
                const int s=column("state_"+std::to_string(i)+"_"+std::to_string(v),'B',0,1);
                c.states[i].push_back({v,s});one[s]=1;link[s]=-static_cast<double>(v);
            }
            require('=',1,one);require('=',0,link);
            for(int k=0;k<in.M;++k) {
                p[k][i]=column(tag("p_",k,i),'I',0,std::min(in.initial[i],in.Q[k]));
                d[k][i]=column(tag("d_",k,i),'I',0,std::min(in.capacity[i]-in.initial[i],in.Q[k]));
                z[k][i]=column(tag("z_",k,i),'B',0,1);mode[k][i]=column(tag("mode_",k,i),'B',0,1);
                u[k][i]=column(tag("ord_",k,i),'C',0,in.V);
                balance[p[k][i]]=1;balance[d[k][i]]=-1;unique[z[k][i]]=1;
                const int a=std::min(in.initial[i],in.Q[k]),b=std::min(in.capacity[i]-in.initial[i],in.Q[k]);
                require('<',0,{{mode[k][i],1},{z[k][i],-1}});
                require('<',0,{{p[k][i],1},{mode[k][i],-static_cast<double>(a)}});
                require('<',0,{{d[k][i],1},{z[k][i],-static_cast<double>(b)},{mode[k][i],static_cast<double>(b)}});
                require('>',0,{{p[k][i],1},{d[k][i],1},{z[k][i],-1}});
            }
            require('=',in.initial[i],balance);require('<',1,unique);
        }
        for(int k=0;k<in.M;++k) {
            for(int i=0;i<=in.V;++i)for(int j=0;j<=in.V;++j)if(i!=j)x[k][i][j]=column(arc(k,i,j),'B',0,1);
            Row start,end,final;
            for(int i=1;i<=in.V;++i) {
                start[x[k][0][i]]=1;end[x[k][0][i]]=1;end[x[k][i][0]]=-1;
                final[p[k][i]]=1;final[d[k][i]]=-1;
                Row incoming{{z[k][i],-1}},outgoing{{z[k][i],-1}};
                for(int j=0;j<=in.V;++j)if(i!=j){incoming[x[k][j][i]]=1;outgoing[x[k][i][j]]=1;}
                require('=',0,incoming);require('=',0,outgoing);
                for(int j=1;j<=in.V;++j)if(i!=j)
                    require('<',in.V-1,{{u[k][i],1},{u[k][j],-1},{x[k][i][j],static_cast<double>(in.V)}});
            }
            require('<',1,start);require('=',0,end);require('>',0,final);
            // Identify the imported duration row by its ENTIRE allowed support,
            // including all positive original arcs and each positive handling term.
            std::set<int> support;
            for(int i=0;i<=in.V;++i)for(int j=0;j<=in.V;++j)if(i!=j&&in.dist[i][j]>0)support.insert(x[k][i][j]);
            if(in.pickup_time+in.drop_time>0)for(int i=1;i<=in.V;++i)support.insert(p[k][i]);
            if(support.empty()) { if(c.handling_lower!=0)throw std::runtime_error("duration_zero_support");continue; }
            bool found=false;
            for(int r:incident[*support.begin()])if(m.senses[r]=='<'&&m.rhs[r]>=0&&
                m.row_starts[r+1]-m.row_starts[r]==static_cast<int>(support.size())) {
                Row actual;bool ok=true;
                for(int t=m.row_starts[r];t<m.row_starts[r+1];++t) {
                    const int j=m.column_indices[t];const double a=m.coefficients[t];
                    if(!support.count(j)||a<=0){ok=false;break;}actual[j]=a;
                }
                if(!ok)continue;
                if(found)throw std::runtime_error("ambiguous_duration_row");
                found=true;++c.audited_rows;
                c.horizon_upper=std::max(c.horizon_upper,m.rhs[r]);
                for(int i=0;i<=in.V;++i)for(int j=0;j<=in.V;++j)if(i!=j&&in.dist[i][j]>0)
                    c.travel_lower[i][j]=std::min(c.travel_lower[i][j],actual.at(x[k][i][j]));
                if(in.pickup_time+in.drop_time>0)for(int i=1;i<=in.V;++i)c.handling_lower=std::min(c.handling_lower,actual.at(p[k][i]));
            }
            if(!found)throw std::runtime_error("duration_row_missing");
        }
        shortest(c);c.valid=true;c.reason="audited_original_integer_model";c.proof_identity=fleetContractJson(c);
    } catch(const std::exception& e) { c.valid=false;c.reason=e.what(); }
    return c;
}

FleetProof proveFleetSmall(const FleetContract& c,const std::vector<FleetEvent>& es) {
    FleetProof out;out.events=es;out.rank=static_cast<int>(es.size());out.method="complete_subset_dp";
    if(!goodEvents(c,es)||es.size()>10){out.reason="invalid_or_unsupported_small_support";return out;}
    const int n=static_cast<int>(es.size()),N=1<<n,M=static_cast<int>(c.capacities.size());
    auto travel=tours(c,es);
    for(int b=1;b<N;++b)for(int j=0;j<n;++j)if(b&(1<<j))travel[b]=std::max(travel[b],single(c,es[j].station));
    std::vector<long long> P(N),D(N);std::vector<int> counts(N);
    for(int b=1;b<N;++b) { int j=0;while(!(b&(1<<j)))++j;const int rest=b^(1<<j);
        P[b]=P[rest]+(es[j].direction<0?es[j].quantity:0);D[b]=D[rest]+(es[j].direction>0?es[j].quantity:0);counts[b]=counts[rest]+1; }
    out.allowed.assign(M,std::vector<unsigned char>(N,1));
    for(int k=0;k<M;++k)for(int b=1;b<N;++b) {
        bool possible=true;for(int j=0;j<n;++j)if((b&(1<<j))&&es[j].quantity>c.capacities[k])possible=false;
        const double lb=plusLower(travel[b],timesLower(c.handling_lower,std::max(P[b],D[b])));
        if(std::isfinite(lb)&&lb>c.horizon_upper)possible=false;
        out.allowed[k][b]=static_cast<unsigned char>(possible); // unknown arithmetic retains assignment
    }
    // A full disjoint assignment in the NECESSARY system proves rank=n and
    // avoids the 3^r recurrence. Failure of this greedy attempt proves nothing.
    int remaining=N-1;
    for(int k=0;k<M&&remaining;++k) {
        int best=0;
        for(int a=remaining;a;a=(a-1)&remaining)if(out.allowed[k][a]&&counts[a]>counts[best])best=a;
        remaining^=best;
    }
    if(!remaining){out.valid=true;out.reason="full_necessary_assignment_rank_is_support";return out;}
    out.dp.assign(M+1,std::vector<int>(N,0));
    for(int k=1;k<=M;++k)for(int b=1;b<N;++b) {
        int best=out.dp[k-1][b];
        for(int a=b;a;a=(a-1)&b)if(out.allowed[k-1][a])best=std::max(best,counts[a]+out.dp[k-1][b^a]);
        out.dp[k][b]=best;
    }
    out.rank=out.dp[M][N-1];out.valid=true;out.reason="complete_necessary_system_not_route_sufficiency";return out;
}

FleetProof proveFleetLarge(const FleetContract& c,const std::vector<FleetEvent>& es,bool hall) {
    FleetProof out;out.events=es;out.rank=static_cast<int>(es.size());out.method=hall?"eligibility_slot_upper":"sum_cardinality_upper";
    if(!goodEvents(c,es)){out.reason="invalid_events_or_arithmetic";return out;}
    const int M=static_cast<int>(c.capacities.size());out.pickup_counts.resize(M);out.drop_counts.resize(M);out.travel_min.resize(M);
    std::vector<std::vector<int>> sets;for(const auto& e:es) { std::vector<int> a;
        for(int k=0;k<M;++k)if(eligible(c,k,e))a.push_back(2*k+(e.direction>0));
        sets.push_back(std::move(a)); }
    std::vector<int> caps(2*M);int total=0;
    for(int k=0;k<M;++k) {
        double ell=std::numeric_limits<double>::infinity();std::vector<int> pick,drop;
        for(const auto& e:es)if(eligible(c,k,e)) {ell=std::min(ell,single(c,e.station));(e.direction<0?pick:drop).push_back(e.quantity);}
        if(!std::isfinite(ell)){out.travel_min[k]=0;continue;}out.travel_min[k]=ell;
        auto count=[&](std::vector<int>& qs) { std::sort(qs.begin(),qs.end());long long sum=0;int r=0;
            for(int q:qs) {sum+=q;const double lb=plusLower(ell,timesLower(c.handling_lower,sum));
                if(std::isfinite(lb)&&lb>c.horizon_upper)break;
                ++r;}return r; };
        out.pickup_counts[k]=caps[2*k]=count(pick);out.drop_counts[k]=caps[2*k+1]=count(drop);
        total+=caps[2*k]+caps[2*k+1];
    }
    const bool same_eligibility=std::all_of(sets.begin(),sets.end(),[&](const auto& s){return s==sets.front();});
    // Uniform-q, same-direction pools have one common eligibility set on the
    // current common resource contract. Matching is then just slot counting.
    int rank=total;
    if(hall) {
        if(same_eligibility){rank=0;for(int slot:sets.front())rank+=caps[slot];}
        else rank=matching(sets,caps);
    }
    out.rank=std::min(static_cast<int>(es.size()),rank);
    out.valid=true;out.reason="relaxed_eligibility_counts_upper_bound";return out;
}

std::vector<FleetCut> separateFleetEvents(const FleetContract& c,const std::vector<double>& point,double margin,FleetStatistics& stats,int max_rows) {
    std::vector<FleetCut> rows;if(!c.valid||!ready()||point.size()!=static_cast<std::size_t>(c.columns)||
        !std::isfinite(margin)||margin<0||max_rows<1||max_rows>8){++stats.arithmetic_skips;return rows;}
    for(double v:point)if(!std::isfinite(v)){++stats.arithmetic_skips;return rows;}
    if(stats.cache_contract!=c.proof_identity){stats.proof_cache.clear();stats.cache_order.clear();stats.cache_contract=c.proof_identity;}
    const int V=static_cast<int>(c.initial.size())-1,maxQ=*std::max_element(c.capacities.begin(),c.capacities.end());
    std::vector<std::vector<double>> low(V+1),high(V+1);
    for(int i=1;i<=V;++i) {low[i].assign(maxQ+1,0);high[i].assign(maxQ+1,0);
        for(auto [y,j]:c.states[i])for(int q=1;q<=maxQ;++q) {
            if(y<=static_cast<long long>(c.initial[i])-q)low[i][q]+=point[j];
            if(y>=static_cast<long long>(c.initial[i])+q)high[i][q]+=point[j];
        }
    }
    std::set<std::string> seen;
    auto evaluate=[&](std::vector<FleetEvent> es,bool small) {
        if(es.empty())return;
        std::sort(es.begin(),es.end(),[](auto a,auto b){return a.station<b.station;});
        const std::string signature=key(es)+(small?"dp":"large");
        if(!seen.insert(signature).second){++stats.duplicates;return;}++stats.candidates;
        FleetProof proof;
        const auto cached=stats.proof_cache.find(signature);
        if(cached!=stats.proof_cache.end()){proof=cached->second;++stats.cache_hits;}
        else {
            proof=small?proveFleetSmall(c,es):proveFleetLarge(c,es);
            if(proof.valid && small) {
                // A declared memory cache, not a separation/time quota. Eviction
                // only causes exact recomputation, including no-conflict answers.
                if(stats.proof_cache.size()>=256){stats.proof_cache.erase(stats.cache_order.front());stats.cache_order.pop_front();}
                stats.cache_order.push_back(signature);stats.proof_cache.emplace(signature,proof);
            }
        }
        if(!proof.valid){++stats.arithmetic_skips;return;}++stats.proofs;small?++stats.small_proofs:++stats.large_proofs;
        if(proof.rank>=static_cast<int>(es.size())){++stats.greedy_full;return;}
        FleetCut row;row.proof=std::move(proof);row.key=key(es)+"rhs"+std::to_string(row.proof.rank);
        for(auto e:es)for(auto [y,j]:c.states[e.station])if(e.direction<0?y<=c.initial[e.station]-e.quantity:y>=c.initial[e.station]+e.quantity)
            row.indices.push_back(j);
        std::sort(row.indices.begin(),row.indices.end());row.coefficients.assign(row.indices.size(),1);
        double activity=0;for(int j:row.indices)activity=down(activity+point[j]);
        row.activity_lower=activity;row.violation_lower=down(activity-row.proof.rank);
        if(!std::isfinite(activity)||row.violation_lower<=margin)return;
        ++stats.reliable;rows.push_back(std::move(row));
    };
    // Uniform-q pools: all positive-mass distinct stations, mass-ordered prefixes.
    // Large supports use polynomial upper bounds; only the best dense <=9 prefix uses DP.
    for(int sign:{-1,1})for(int q=1;q<=maxQ;++q) {
        std::vector<FleetEvent> es;auto& mass=sign<0?low:high;
        for(int i=1;i<=V;++i)if(q<static_cast<int>(mass[i].size())&&mass[i][q]>margin&&
            q<=(sign<0?c.initial[i]:c.station_capacity[i]-c.initial[i]))es.push_back({i,sign,q});
        std::sort(es.begin(),es.end(),[&](auto a,auto b){return mass[a.station][q]!=mass[b.station][q]?
            mass[a.station][q]>mass[b.station][q]:a.station<b.station;});
        if(es.empty())continue;
        // All prefix sizes are checked by the scalable proof, without support truncation.
        for(std::size_t s=1;s<=es.size();++s)evaluate(std::vector<FleetEvent>(es.begin(),es.begin()+s),false);
        if(es.size()>=3) {
            const int n=std::min(9,static_cast<int>(es.size()));
            double quality=0;for(int j=0;j<n;++j)quality+=mass[es[j].station][q];
            // At least one event per eligible vehicle is a certified achievable
            // necessary-system lower bound via matching singleton slots.
            std::vector<std::vector<int>> ks;
            for(int j=0;j<n;++j){std::vector<int> a;for(std::size_t k=0;k<c.capacities.size();++k)if(eligible(c,static_cast<int>(k),es[j]))a.push_back(static_cast<int>(k));ks.push_back(a);}
            const int lower=matching(ks,std::vector<int>(c.capacities.size(),1));
            if(quality>lower+margin)evaluate(std::vector<FleetEvent>(es.begin(),es.begin()+n),true);
        }
    }
    // Mixed, nonuniform thresholds: largest q retaining a specified event mass.
    for(double quality:{0.5,0.75,0.9}) {
        std::vector<FleetEvent> es;
        for(int i=1;i<=V;++i) {
            FleetEvent best;for(int sign:{-1,1})for(int q=1;q<=maxQ;++q) {
                const double m=sign<0?low[i][q]:high[i][q];
                if(m>=quality&&q>best.quantity)best={i,sign,q};
            }
            if(best.quantity>0)es.push_back(best);
        }
        evaluate(es,false);
        std::sort(es.begin(),es.end(),[](auto a,auto b){return a.quantity!=b.quantity?a.quantity>b.quantity:a.station<b.station;});
        if(!es.empty())evaluate(std::vector<FleetEvent>(es.begin(),es.begin()+std::min<std::size_t>(9,es.size())),true);
    }
    std::sort(rows.begin(),rows.end(),[](const auto& a,const auto& b){return a.violation_lower!=b.violation_lower?a.violation_lower>b.violation_lower:a.key<b.key;});
    std::vector<FleetCut> selected;std::set<std::string> keys;
    for(auto& row:rows) {
        if(!keys.insert(row.key).second)continue;
        bool overlap=false;
        for(const auto& old:selected) {
            int count=0;for(auto e:row.proof.events)for(auto f:old.proof.events)count+=e.station==f.station;
            if(2*count>static_cast<int>(std::min(row.proof.events.size(),old.proof.events.size())))overlap=true;
        }
        if(overlap)continue;
        selected.push_back(std::move(row));if(static_cast<int>(selected.size())>=max_rows)break;
    }
    return selected;
}

std::string fleetProofJson(const FleetProof& p) {
    std::ostringstream f;f<<std::setprecision(17)<<"{\"valid\":"<<(p.valid?"true":"false")<<",\"method\":\""<<p.method<<"\",\"rank\":"<<p.rank<<",\"events\":[";
    for(std::size_t j=0;j<p.events.size();++j){if(j)f<<',';auto e=p.events[j];f<<'['<<e.station<<','<<e.direction<<','<<e.quantity<<']';}f<<"]";
    auto table=[&](const char* name,const auto& a){f<<",\""<<name<<"\":[";for(std::size_t k=0;k<a.size();++k){if(k)f<<',';f<<'[';for(std::size_t j=0;j<a[k].size();++j){if(j)f<<',';f<<static_cast<int>(a[k][j]);}f<<']';}f<<']';};
    auto vec=[&](const char* name,const auto& a){f<<",\""<<name<<"\":[";for(std::size_t j=0;j<a.size();++j){if(j)f<<',';f<<a[j];}f<<']';};
    table("allowed",p.allowed);table("dp",p.dp);vec("pickup_counts",p.pickup_counts);vec("drop_counts",p.drop_counts);vec("travel_min",p.travel_min);f<<'}';return f.str();
}
std::string fleetContractJson(const FleetContract& c) {
    std::ostringstream f;f<<std::setprecision(17)<<"{\"valid\":"<<(c.valid?"true":"false")<<",\"handling_lower\":"<<c.handling_lower<<",\"horizon_upper\":"<<c.horizon_upper<<",\"columns\":"<<c.columns<<",\"audited_rows\":"<<c.audited_rows;
    auto vec=[&](const char* name,const auto& a){f<<",\""<<name<<"\":[";for(std::size_t j=0;j<a.size();++j){if(j)f<<',';f<<a[j];}f<<']';};
    vec("capacities",c.capacities);vec("initial",c.initial);vec("station_capacity",c.station_capacity);
    auto table=[&](const char* name,const auto& a){f<<",\""<<name<<"\":[";for(std::size_t k=0;k<a.size();++k){if(k)f<<',';f<<'[';for(std::size_t j=0;j<a[k].size();++j){if(j)f<<',';f<<a[k][j];}f<<']';}f<<']';};
    table("travel_lower",c.travel_lower);table("shortest_lower",c.shortest_lower);
    f<<",\"states\":[";for(std::size_t i=0;i<c.states.size();++i){if(i)f<<',';f<<'[';for(std::size_t j=0;j<c.states[i].size();++j){if(j)f<<',';auto [y,col]=c.states[i][j];f<<'['<<y<<','<<col<<']';}f<<']';}f<<"]}";return f.str();
}
} // namespace ebrp
