#include "Round62Passive.hpp"
#include "Round62Thresholds.hpp"
#include "PaperExternalGiniTree.hpp"
#include "Evaluator.hpp"
#include "MipStartMapping.hpp"
#include <algorithm>
#include <cmath>
#include <functional>
#include <iostream>
#include <set>
#include <stdexcept>

using namespace ebrp;
void require(bool x,const char* s){if(!x)throw std::runtime_error(s);}
Instance tiny() {
    Instance in;in.V=3;in.M=2;in.Q={2,3};
    in.capacity={0,3,3,3};in.initial={0,3,0,1};in.target={0,1,1,1};in.weights={0,1,1,1};
    in.dist={{0,2,9,2},{2,0,2,9},{9,2,0,2},{2,9,2,0}};
    in.total_time_limit=10;in.pickup_time=1;in.drop_time=1;return in;
}
void passive() {
    require(SolveOptions{}.round62_threshold_mode=="off" && !FixedIntervalMipRequest{}.round62_external_stop,
        "new native mechanisms must default off");
    require(!round62PassiveMode("archive") && round62PassiveMode("passive-cert"),"outer archive mislabeled passive");
    Round62CoverageSnapshot s;s.control_ub=.8;s.archive_ub=.4;s.archive_verified=true;
    s.root_coverage=s.tree_coverage=true;s.root_upper=.8;s.request_cutoff=.8;
    s.active_leaf="a";s.model_identity="canonical-test";
    ControllingLeaf a;a.id="a";a.gamma_L=0;a.gamma_U=.4;a.lower_bound=.2;a.cutoff=.8;
    ControllingLeaf b=a;b.id="b";b.gamma_L=.4;b.gamma_U=.8;b.lower_bound=.4;
    s.leaves={a,b};const auto before=s.leaves;
    auto d=evaluateRound62Passive(s,.4);
    require(d.certified,"external certificate must not require native incumbent");
    require(s.control_ub==.8 && s.epoch==0 && s.leaves[0].lower_bound==before[0].lower_bound,"passive mutation");
    s.leaves[1].lower_bound=.1;require(!evaluateRound62Passive(s,.5).certified,"ignore unsolved leaf");
    s.leaves[1].lower_bound=.4;s.request_epoch=1;require(!evaluateRound62Passive(s,.4).valid,"stale epoch");
    s.request_epoch=0;s.leaves[1].gamma_L=.5;require(!evaluateRound62Passive(s,.4).valid,"coverage hole");
    s.leaves[1].gamma_L=.4;s.request_cutoff=.3;require(!evaluateRound62Passive(s,.4).valid,"wrong cutoff");
    s.request_cutoff=.8;s.leaves[1].cutoff=std::numeric_limits<double>::quiet_NaN();
    require(!evaluateRound62Passive(s,.4).valid,"nonfinite bound scope");s.leaves[1].cutoff=.8;
    s.request_cutoff=.8;s.leaves[1].status=ControllingLeafStatus::Invalid;
    require(!evaluateRound62Passive(s,.4).valid,"invalid bound scope");
    FixedIntervalMipOutcome outcome;outcome.attempted=outcome.available=outcome.solver_finalization_reached=true;
    outcome.model_fingerprint_matches_request=outcome.exact_zero_gap_roundtrip=outcome.feasibility_consistency_gate=true;
    outcome.terminal_mip=outcome.interrupted=outcome.round62_external_termination_requested=true;
    outcome.native_status="INTERRUPTED";
    auto t=evaluatePaperTerminalMipDecision(outcome);
    require(t.valid&&!t.close_leaf&&!outcome.optimal,"native interrupted disguised optimal");
}
bool satisfied(const Round62Row& row,const std::map<std::string,double>& values) {
    double activity=0;for(const auto& [name,c]:row.coefficients) {
        const auto it=values.find(name);activity+=c*(it==values.end()?0:it->second);
    }
    return row.sense=='<'?activity<=row.rhs+1e-8:row.sense=='>'?activity>=row.rhs-1e-8:std::fabs(activity-row.rhs)<=1e-8;
}
void thresholds() {
    auto in=tiny();auto d=round62Shortest(in);
    require(d[0][2]==4&&d[1][3]==4,"nonmetric shortest-path lower bound");
    auto directed=in;directed.dist[2][0]=1;auto dd=round62Shortest(directed);
    require(dd[0][2]==4&&dd[2][0]==1,"directed lower bounds");
    auto bad=in;bad.dist[0][1]=-1;bool threw=false;try{round62Shortest(bad);}catch(...){threw=true;}require(threw,"negative arcs");
    require(!proveRound62Conflict(in,d,{{1,-1,1},{1,-1,2}}),"nested same station double count");
    require(!proveRound62Conflict(in,d,{{1,-1,0}}),"zero service event");
    auto proof=generateRound62Thresholds(in);
    require(!proof.conflicts.empty(),"test fixture no conflicts");
    for(const auto& c:proof.conflicts) {
        require(proveRound62Conflict(in,d,c.events),"invalid generated proof");
        require(c.events.size()==c.vehicle_union.size()+1,"automatic clique deficiency invariant");
    }
    // Weakening may gain an eligible small vehicle, removing the Hall contradiction.
    Instance h=in;h.V=2;h.capacity={0,3,3};h.initial={0,3,3};h.dist={{0,1,1},{1,0,10},{1,10,0}};
    h.total_time_limit=9;h.Q={1,3};auto hd=round62Shortest(h);
    require(proveRound62Conflict(h,hd,{{1,-1,3},{2,-1,3}}),"heterogeneous proof");
    require(!proveRound62Conflict(h,hd,{{1,-1,1},{2,-1,1}}),"weakening must recheck vehicles and edges");
    const auto rows=round62ThresholdRows(in,proof,"service-conflicts");
    const auto projections=round62ThresholdRows(in,proof,"projection");
    const auto service_projections=round62ThresholdRows(in,proof,"projection-service");
    const auto rlt=round62ThresholdRows(in,proof,"projection-rlt",.1,.7);
    // Exhaustive feasible route/action enumeration with all other stations free.
    struct R{int mask=0;std::vector<int> move;};std::vector<std::vector<R>> routes(in.M);
    for(int k=0;k<in.M;++k) {
        std::vector<int> move(in.V+1);
        std::function<void(int,int,int,double,int)> dfs=[&](int last,int mask,int load,double travel,int pick) {
            if(travel+in.dist[last][0]+2*pick<=in.total_time_limit+1e-9)routes[k].push_back({mask,move});
            for(int i=1;i<=in.V;++i)if(!(mask&(1<<i)))for(int x=-in.initial[i];x<=in.capacity[i]-in.initial[i];++x) {
                if(x==0||load-x<0||load-x>in.Q[k])continue;
                const auto time=travel+in.dist[last][i];if(time>in.total_time_limit)continue;
                move[i]=x;dfs(i,mask|(1<<i),load-x,time,pick+std::max(0,-x));move[i]=0;
            }
        };dfs(0,0,0,0,0);
    }
    int checked=0;
    for(const auto& a:routes[0])for(const auto& b:routes[1])if(!(a.mask&b.mask)) {
        std::map<std::string,double> values;auto y=in.initial;
        for(int i=1;i<=in.V;++i) {
            y[i]+=a.move[i]+b.move[i];values["Y_"+std::to_string(i)]=y[i];
            for(int k=0;k<in.M;++k){const int x=k==0?a.move[i]:b.move[i];auto suffix=std::to_string(k)+"_"+std::to_string(i);
                values["p_"+suffix]=std::max(0,-x);values["d_"+suffix]=std::max(0,x);values["z_"+suffix]=x!=0;}
        }
        for(const auto& e:proof.dictionary)values[e.name()]=e.direction<0?y[e.station]<=in.initial[e.station]-e.quantity:y[e.station]>=in.initial[e.station]+e.quantity;
        for(const auto& row:rows)require(satisfied(row,values),"feasible routing violates event/conflict row");
        for(const auto& row:projections)require(satisfied(row,values),"feasible routing violates projection");
        for(const auto& row:service_projections)require(satisfied(row,values),"feasible routing violates service projection");
        for(double g:{.1,.3,.7}) {
            values["G"]=g;for(int i=1;i<=in.V;++i)values["zprod_"+std::to_string(i)]=g*y[i];
            for(const auto& row:rlt)require(satisfied(row,values),"feasible product violates RLT projection");
        }
        ++checked;
    }
    require(checked>10,"insufficient exhaustive routes");
    // Scalar iff including constant events; LP completion uses the actual allowed
    // z interval, not arbitrary favorable binary values at a frozen fractional Y.
    Round62ThresholdProof scalar;scalar.shortest=d;
    scalar.dictionary={{1,-1,1},{1,-1,3},{2,1,1},{2,1,3},{3,1,3}};
    auto definitions=round62ThresholdRows(in,scalar,"events");
    for(int y1=0;y1<=3;++y1)for(int y2=0;y2<=3;++y2) {
        std::map<std::string,double> vals={{"Y_1",static_cast<double>(y1)},{"Y_2",static_cast<double>(y2)},{"Y_3",1}};
        for(const auto& e:scalar.dictionary){int y=static_cast<int>(vals["Y_"+std::to_string(e.station)]);
            vals[e.name()]=e.direction<0?y<=in.initial[e.station]-e.quantity:y>=in.initial[e.station]+e.quantity;}
        for(const auto& row:definitions)require(satisfied(row,vals),"iff/domain/nesting mismatch");
        for(const auto& e:scalar.dictionary) {
            vals[e.name()]=1-vals[e.name()];
            require(std::any_of(definitions.begin(),definitions.end(),[&](const auto& row){return !satisfied(row,vals);}),
                "wrong integer event can bypass exact definition");
            vals[e.name()]=1-vals[e.name()];
        }
    }
    // Constant connector corner case. A zero service threshold is rejected by
    // the proof API above, but the scalar connector still handles theta=U=L.
    auto constant=in;constant.initial[1]=constant.capacity[1]=0;
    Round62ThresholdProof cp;cp.dictionary={{1,-1,0},{1,1,1}};
    auto cr=round62ThresholdRows(constant,cp,"events");
    std::map<std::string,double> cv={{"Y_1",0},{"r62lo_1_0",1},{"r62hi_1_1",0}};
    require(cr.size()==2,"constant threshold simplification");
    for(const auto& row:cr)require(satisfied(row,cv),"constant true/false threshold");
    auto local=proof;local.scope="node_local";threw=false;
    try{round62ThresholdRows(in,local,"projection");}catch(...){threw=true;}require(threw,"local proof reused globally");
    auto stale=proof;stale.shortest[0][1]+=1;threw=false;
    try{round62ThresholdRows(in,stale,"projection");}catch(...){threw=true;}require(threw,"proof reused on different travel data");
    stale=proof;stale.conflicts.front().vehicle_union.clear();threw=false;
    try{round62ThresholdRows(in,stale,"conflicts");}catch(...){threw=true;}require(threw,"stale vehicle-union RHS");
    threw=false;try{round62ThresholdRows(in,proof,"projection-rlt",.7,.1);}catch(...){threw=true;}require(threw,"invalid RLT factor interval");
    // A false event contributes >= 1 to its box projection; scalar completion
    // lower endpoint equals 1 minus that nonnegative contribution, clipped at 0.
    for(double y=0;y<=3;y+=.125){const int L=0,U=3,theta=1;
        double lo=std::max(0.0,(theta+1-y)/(theta+1-L));
        double hi=std::min(1.0,(U-y)/(U-theta));require(lo<=hi+1e-12,"legal continuous completion");}
    for(double t1=0;t1<=2;t1+=.125)for(double t2=0;t2<=2;t2+=.125)for(double t3=0;t3<=2;t3+=.125) {
        const double minimum=std::max(0.0,1-t1)+std::max(0.0,1-t2)+std::max(0.0,1-t3);
        require((minimum<=2+1e-12)==(t1+t2+t3>=1-1e-12),"scalar clique exact LP projection");
    }

    // Service projection dominates the inventory projection throughout the
    // existing station perspective hull, and its minimum event completion is
    // compatible with the scalar upper bound and the service/visit caps.
    for(double p=0;p<=3;p+=.125)for(double drop=0;drop<=2;drop+=.125) {
        if(p/3+drop/2>1+1e-12)continue;
        for(int q=1;q<=3;++q) {
            const double service=(3-p)/(4-q),box=(3+drop-p)/(4-q);
            const double z=std::max(0.,1-service),scalar_upper=(2+p-drop)/(2+q);
            require(service<=box+1e-12 && z<=scalar_upper+1e-12 && z<=p/3+1e-12,
                "service projection dominance/completion");
        }
    }

    // One vehicle may pick up more than Q in total after deliveries unload it.
    // The other supply station remains available; no fixed-inventory no-good
    // or pair proof may remove this legal route by bounding total pickup by Q.
    Instance cycle;cycle.V=4;cycle.M=1;cycle.Q={2};
    cycle.capacity={0,2,2,2,2};cycle.initial={0,2,0,2,0};
    cycle.target={0,1,1,1,1};cycle.weights={0,1,1,1,1};
    cycle.dist.assign(5,std::vector<double>(5,1));for(int i=0;i<5;++i)cycle.dist[i][i]=0;
    cycle.total_time_limit=20;cycle.pickup_time=cycle.drop_time=1;
    RoutePlan route;route.vehicle=0;route.nodes={0,1,2,3,4,0};
    route.operations={{1,2,0},{2,0,2},{3,2,0},{4,0,2}};
    require(verifySolution(cycle,{route},.15).original_solution_feasible,"prefix-feasible pickup total greater than Q");
    require(!proveRound62Conflict(cycle,round62Shortest(cycle),{{1,-1,2},{3,-1,2}}),"incorrect total pickup capacity conflict");
    require(!proveRound62Conflict(cycle,round62Shortest(cycle),{{2,1,2},{4,1,2}}),"other suppliers improperly excluded");
    SolverNeutralModelDomain domain;
    domain.names={"r62lo_1_2","r62lo_2_1","r62hi_2_2","r62hi_3_1"};
    domain.lower_bounds.assign(4,0);domain.upper_bounds.assign(4,1);domain.variable_types.assign(4,'B');
    const auto mapped=mapVerifiedRoutesToCanonicalModel(cycle,SolveOptions{},{route},"round62-test",0,1,2,domain);
    require(mapped.complete && mapped.values==std::vector<double>({1,0,1,0}),"exact pickup/drop threshold MIP mapper");
}
int main(){try{passive();thresholds();std::cout<<"Round62 solver-free correctness tests passed\n";return 0;}
catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
