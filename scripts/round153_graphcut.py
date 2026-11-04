"""Exact integer-flow bounds for full-domain signed inventory pricing.

Resource/Gini/S restrictions are Lagrangian-relaxed only to obtain a lower.
The unrestricted cut labels are never assumed to be feasible stock uppers.
The threshold identity is the existing CDF absolute-difference identity.
"""
from bisect import bisect_right
from collections import deque
from fractions import Fraction as F
from itertools import combinations,product
from round143_math import outward
from round152_math import s_bounds,states,unary_dp
from round153_pricing import stock_value,serial_stock,keyed
from round153_common import *

SCALE=1<<40


class Thresholds:
    def __init__(self,scope):
        self.scope=scope;self.nodes={};self.labels={};self.ratios={};self.monotone=[]
        for s in scope['stations']:
            i=s['i'];ys=sorted(s['support']);assert ys==s['support'] and len(set(ys))==len(ys) and F(s['c'])>0
            self.labels[i]=ys;self.ratios[i]=[F(s['c'])*y for y in ys]
            for j in range(len(ys)-1):self.nodes[i,j]=len(self.nodes)
            self.monotone += [(self.nodes[i,j+1],self.nodes[i,j]) for j in range(len(ys)-2)]
        self.size=len(self.nodes);self.A_constant=F(0);self.A_unary=[F(0)]*self.size;self.A_pairs={}
        def indicator(i,q):
            if q<self.ratios[i][0]:return ('fixed',1)
            if q>=self.ratios[i][-1]:return ('fixed',0)
            return ('node',self.nodes[i,bisect_right(self.ratios[i],q)-1])
        for left,right in combinations(scope['stations'],2):
            i,j=left['i'],right['i'];points=sorted({F(0)}|set(self.ratios[i])|set(self.ratios[j]))
            for lo,hi in zip(points[:-1],points[1:]):
                delta=hi-lo;a,b=indicator(i,lo),indicator(j,lo)
                if a[0]==b[0]=='fixed':self.A_constant+=delta*abs(a[1]-b[1])
                elif a[0]==b[0]=='node':
                    pair=tuple(sorted((a[1],b[1])));self.A_pairs[pair]=self.A_pairs.get(pair,F(0))+delta
                else:
                    node,fixed=(a[1],b[1]) if a[0]=='node' else (b[1],a[1])
                    self.A_constant+=delta*fixed;self.A_unary[node]+=delta*(1-2*fixed)

    def features(self,Y,costs):
        r=[F(s['c'])*y for s,y in zip(self.scope['stations'],Y)]
        return dict(A=sum((abs(a-b) for a,b in combinations(r,2)),F(0)),S=sum(r,F(0)),T=sum(Y),
            d=sum((costs[s['i'],y] for s,y in zip(self.scope['stations'],Y)),F(0)))

    def network(self,beta,costs,lo,hi,p,r,eta):
        beta,p,r,eta=map(F,(beta,p,r,eta));lo,hi=F(lo),F(hi)
        assert beta>=0 and eta>=0 and 0<lo<=hi
        n=len(self.scope['stations']);g=F(self.scope['gamma_U']);k=beta/(n*hi)+eta
        unary=[k*a for a in self.A_unary]
        constant=k*self.A_constant-max(p*self.scope['Bminus'],p*self.scope['B'])-max(r*lo,r*hi)
        for s in self.scope['stations']:
            i=s['i'];ys=self.labels[i];q=r-eta*n*g
            values=[costs[i,y]+p*y+q*F(s['c'])*y for y in ys];constant+=values[0]
            for j in range(len(ys)-1):unary[self.nodes[i,j]]+=values[j+1]-values[j]
        source,sink=self.size,self.size+1;arcs=[]
        def floor(value):return (value*SCALE).__floor__()
        integer_constant=floor(constant)
        for node,value in enumerate(unary):
            coefficient=floor(value)
            if coefficient>=0:
                if coefficient:arcs.append((node,sink,coefficient))
            else:arcs.append((source,node,-coefficient));integer_constant+=coefficient
        for (a,b),delta in sorted(self.A_pairs.items()):
            capacity=floor(k*delta);assert capacity>=0
            if capacity:arcs.extend([(a,b,capacity),(b,a,capacity)])
        infinity=1+sum(c for a,b,c in arcs)
        arcs += [(a,b,infinity) for a,b in self.monotone]
        return dict(nodes=self.size+2,source=source,sink=sink,arcs=arcs,constant=integer_constant,
            infinity=infinity,rounding_terms=1+len(unary)+len(self.A_pairs))

    def labels_from_cut(self,source_side):
        inside=set(source_side);Y=[]
        for s in self.scope['stations']:
            i=s['i'];bits=[int(self.nodes[i,j] in inside) for j in range(len(self.labels[i])-1)]
            assert bits==sorted(bits,reverse=True);Y.append(self.labels[i][sum(bits)])
        return Y


def maxflow(network):
    """Dinic with Python integers; return a verifiable feasible flow and cut."""
    n=network['nodes'];source=network['source'];sink=network['sink'];adj=[[] for _ in range(n)];to=[];res=[]
    for a,b,c in network['arcs']:
        j=len(to);adj[a].append(j);adj[b].append(j+1);to.extend([b,a]);res.extend([c,0])
    sys.setrecursionlimit(max(sys.getrecursionlimit(),2*n+100));total=0
    while True:
        level=[-1]*n;level[source]=0;queue=deque([source])
        while queue:
            a=queue.popleft()
            for edge in adj[a]:
                b=to[edge]
                if res[edge] and level[b]<0:level[b]=level[a]+1;queue.append(b)
        if level[sink]<0:break
        cursor=[0]*n
        def send(a,amount):
            if a==sink:return amount
            while cursor[a]<len(adj[a]):
                edge=adj[a][cursor[a]];b=to[edge]
                if res[edge] and level[b]==level[a]+1:
                    flow=send(b,min(amount,res[edge]))
                    if flow:res[edge]-=flow;res[edge^1]+=flow;return flow
                cursor[a]+=1
            return 0
        while True:
            flow=send(source,network['infinity'])
            if not flow:break
            total+=flow
    side=[i for i,v in enumerate(level) if v>=0]
    flows=[[j,c-res[2*j]] for j,(a,b,c) in enumerate(network['arcs']) if c!=res[2*j]]
    record=dict(flow_value=total,positive_flows=flows,source_side=side)
    verify_flow(network,record);return record


def verify_flow(network,record):
    n=network['nodes'];source=network['source'];sink=network['sink'];balance=[0]*n;used=set()
    for index,flow in record['positive_flows']:
        assert type(index) is int and type(flow) is int and index not in used;used.add(index)
        assert 0<=index<len(network['arcs'])
        a,b,capacity=network['arcs'][index];assert 0<flow<=capacity
        balance[a]+=flow;balance[b]-=flow
    value=record['flow_value'];assert type(value) is int and value>=0
    assert balance[source]==value and balance[sink]==-value
    assert all(balance[i]==0 for i in range(n) if i not in (source,sink))
    side=set(record['source_side']);assert len(side)==len(record['source_side']) and source in side and sink not in side
    assert all(type(i) is int and 0<=i<n for i in side)
    cut=sum(c for a,b,c in network['arcs'] if a in side and b not in side)
    assert cut==value and cut<network['infinity']
    return F(network['constant']+value,SCALE)


def cut_bound(topology,beta,costs,lo,hi,parameters):
    parameters=list(map(F,parameters));network=topology.network(beta,costs,lo,hi,*parameters)
    tick=time.perf_counter();flow=maxflow(network);lower=verify_flow(network,flow)
    Y=topology.labels_from_cut(flow['source_side'])
    return dict(parameters_exact=list(map(str,parameters)),lower_exact=str(lower),Y=Y,flow=flow,
        network_arcs=len(network['arcs']),network_nodes=network['nodes'],constant_integer=network['constant'],
        integer_scale=SCALE,rounding_terms=network['rounding_terms'],maxflow_seconds=time.perf_counter()-tick)


def verify_bound(topology,beta,costs,lo,hi,record):
    assert record['integer_scale']==SCALE
    network=topology.network(beta,costs,lo,hi,*map(F,record['parameters_exact']))
    lower=verify_flow(network,record['flow'])
    assert lower==F(record['lower_exact']) and network['constant']==record['constant_integer']
    assert len(network['arcs'])==record['network_arcs'] and network['nodes']==record['network_nodes']
    assert topology.labels_from_cut(record['flow']['source_side'])==record['Y']
    return lower


def candidate_lp(topology,env,beta,costs,lo,hi,features,box,target,cap):
    """A small LP proposes multipliers only; its objective is not a price bound."""
    from round100_gurobi_runtime import gp
    target.mkdir(parents=True,exist_ok=False)
    with gp.Model(env=env) as m:
        p=m.addVar(lb=-box,ub=box,name='p');r=m.addVar(lb=-box,ub=box,name='r')
        eta=m.addVar(lb=0,ub=box,name='eta');theta=m.addVar(lb=-gp.GRB.INFINITY,name='theta')
        u=m.addVar(lb=-gp.GRB.INFINITY,name='support_T');v=m.addVar(lb=-gp.GRB.INFINITY,name='support_S')
        scope=topology.scope;n=len(scope['stations']);g=F(scope['gamma_U'])
        m.addConstr(u>=scope['Bminus']*p);m.addConstr(u>=scope['B']*p)
        m.addConstr(v>=float(lo)*r);m.addConstr(v>=float(hi)*r)
        for j,f in enumerate(features):
            m.addConstr(theta<=float(F(beta)*f['A']/(n*hi)+f['d'])+f['T']*p+float(f['S'])*r+
                float(f['A']-n*g*f['S'])*eta,name=f'label_{j}')
        m.setObjective(theta-u-v,gp.GRB.MAXIMIZE)
        m.Params.Seed=0;m.Params.Threads=1;m.Params.Method=1;m.Params.TimeLimit=max(.01,float(cap))
        m.Params.FeasibilityTol=1e-8;m.Params.OptimalityTol=1e-8
        m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.LogFile=str(target/'native.log');m.update()
        m.write(str(target/'model.mps'))
        write(target/'call.json',dict(UTC=utc(),kind='Lagrangian_candidate_selection_only',Seed=0,Threads=1,
            model_SHA=sha(target/'model.mps'),variables=m.NumVars,rows=m.NumConstrs,cap=max(.01,float(cap)),
            finite_candidate_box=box,box_does_not_restrict_inventory_domain=True,objective_not_a_price_bound=True))
        m.optimize();record=dict(Status=m.Status,Runtime=m.Runtime,Work=m.Work,iterations=m.IterCount,
            model=str((target/'model.mps').relative_to(ROOT)),candidate_only=True,parameters=None)
        if m.Status==2:
            params=[p.X,r.X,max(0.,eta.X)]
            if all(math.isfinite(x) for x in params):record.update(parameters=params,objective=m.ObjVal)
            save_gz(target/'solution.json.gz',{x.VarName:x.X for x in m.getVars()})
        write(target/'return.json',record);return record


class GraphOracle:
    def __init__(self,scope,env,parts=16,iterations=20):
        tick=time.perf_counter();self.scope=scope;self.env=env;self.parts=int(parts);self.iterations=int(iterations)
        assert 1<=self.parts<=128 and 1<=self.iterations<=64
        self.bounds=s_bounds(scope);self.topology=Thresholds(scope);self.intervals=[]
        lo,hi=F(self.bounds['lower_exact']),F(self.bounds['upper_exact'])
        if hi>0:
            assert lo>0
            points=[lo,hi] if lo==hi else [lo+(hi-lo)*j/self.parts for j in range(self.parts+1)]
            self.intervals=list(zip(points[:-1],points[1:]))
        self.build_seconds=time.perf_counter()-tick

    def close(self):pass

    def price(self,beta,d,target,cap=600.,warm=(),absolute_gap=1e-7):
        target=Path(target);target.mkdir(parents=True,exist_ok=False);tick=time.perf_counter();beta=float(beta)
        assert math.isfinite(beta) and beta>=0;scope=self.scope;topology=self.topology
        costs={key:F(d.get(key,0)) for key in states(scope)};dp=unary_dp(scope,costs);assert dp is not None
        fallback=F(beta)*F(scope['gamma_L'])+F(dp['exact']);stocks={};features={}
        def consider(Y):
            key=tuple(Y)
            if key not in features:features[key]=topology.features(Y,costs)
            value=stock_value(scope,Y,beta,costs)
            if value['feasible']:stocks[key]=value
        consider(dp['Y'])
        for Y in warm:consider(Y)
        consider([s['support'][0] for s in scope['stations']]);consider([s['support'][-1] for s in scope['stations']])
        zero=None
        if self.bounds['zero_possible']:
            value=stock_value(scope,[0]*len(scope['stations']),beta,costs);assert value['feasible']
            consider(value['Y']);zero=value['price']
        box=max(1.,abs(beta)+sum(float(max(costs[s['i'],y] for y in s['support'])-
            min(costs[s['i'],y] for y in s['support'])) for s in scope['stations']))
        record=dict(scope=scope,beta=beta,d=keyed(costs),d_exact={f'{i}:{y}':str(v) for (i,y),v in costs.items()},
            positive_S_bounds=self.bounds,intervals_exact=[[str(a),str(b)] for a,b in self.intervals],
            source_SHA=sha(__file__),frozen_core_SHA=sha(ROOT/'scripts/round153_pricing.py'),
            integer_scale=SCALE,iterations_per_slice=self.iterations,candidate_box=box,offline_cap=float(cap),
            constructor_seconds=self.build_seconds,all_states_retained=True,legal_zero_separate=True,
            resource_and_Gupper_relaxed_only_for_valid_lower=True,no_relaxed_label_is_automatically_an_upper=True)
        write(target/'plan.json',record);deadline=tick+float(cap);pieces=[fallback]*len(self.intervals)
        slices=[];calls=[];warm_parameters=[0.,0.,0.];flow_count=0
        for j,(lo,hi) in enumerate(self.intervals):
            if time.perf_counter()>=deadline:break
            if stocks and min(v['price'] for v in stocks.values())==fallback:break
            folder=target/f'slice{j:03}';folder.mkdir();end=min(deadline,time.perf_counter()+float(cap)/max(1,len(self.intervals)))
            parameters=warm_parameters;best=None;best_path=None;trials=[]
            for k in range(self.iterations):
                if k and time.perf_counter()>=end:break
                proof=cut_bound(topology,beta,costs,lo,hi,parameters);flow_count+=1
                path=folder/f'flow{k:03}.json.gz';save_gz(path,proof);consider(proof['Y'])
                value=F(proof['lower_exact']);trials.append(dict(proof=str(path.relative_to(ROOT)),SHA256=sha(path),
                    lower_exact=str(value),seconds=proof['maxflow_seconds']))
                if best is None or value>best:
                    best=value;best_path=path;warm_parameters=list(map(float,map(F,proof['parameters_exact'])))
                if k+1==self.iterations or time.perf_counter()>=end:break
                proposed=candidate_lp(topology,self.env,beta,costs,lo,hi,list(features.values()),box,
                    folder/f'candidate{k:03}',min(15.,end-time.perf_counter()))
                calls.append(dict(proposed,slice_index=j));parameters=proposed['parameters']
                if parameters is None:break
                # This only stops candidate search; it is not a full-price upper.
                if proposed['objective']-float(best)<=absolute_gap:break
            assert best is not None
            pieces[j]=max(fallback,best)
            slices.append(dict(index=j,S_interval_exact=[str(lo),str(hi)],lower_exact=str(pieces[j]),
                best_proof=str(best_path.relative_to(ROOT)),best_proof_SHA=sha(best_path),trials=trials))
            write(folder/'result.json',slices[-1])
        lower=max(fallback,min(pieces+([zero] if zero is not None else [])))
        upper=min((v['price'] for v in stocks.values()),default=None)
        record.update(lower=outward(lower,False),upper=outward(upper,True) if upper is not None else None,
            fallback_lower=outward(fallback,False),fallback_exact=str(fallback),zero_lower_exact=str(zero) if zero is not None else None,
            positive_slice_lowers_exact=list(map(str,pieces)),slices=slices,stocks=[serial_stock(v) for v in stocks.values()],
            calls=[],candidate_LP_calls=calls,exact_integer_flow_calls=flow_count,
            complete_domain=True,graphcut_full_price=True,seconds=time.perf_counter()-tick,
            decision='RESOLVED' if upper is not None and upper-lower<=F(absolute_gap) else 'UNDECIDED',
            reason='exhaustive_positive_S_Lagrangian_integer_flow_bounds_plus_zero',upper_is_inventory_price_only=True)
        write(target/'result.json',record);return record


def audit_graph_price(record):
    scope=record['scope'];beta=F(record['beta']);costs={tuple(map(int,k.split(':'))):F(v) for k,v in record['d_exact'].items()}
    assert beta>=0
    topology=Thresholds(scope);bounds=json.loads(json.dumps(s_bounds(scope)))
    assert record['graphcut_full_price'] and record['complete_domain']
    assert json.loads(json.dumps(record['positive_S_bounds']))==bounds
    assert record['source_SHA']==sha(__file__) and record['frozen_core_SHA']==sha(ROOT/'scripts/round153_pricing.py')
    assert record['all_states_retained'] and record['legal_zero_separate'] and not record['calls']
    assert set(costs)==set(states(scope));dp=unary_dp(scope,costs)
    fallback=beta*F(scope['gamma_L'])+F(dp['exact']);assert fallback==F(record['fallback_exact'])
    intervals=[tuple(map(F,v)) for v in record['intervals_exact']]
    if F(bounds['upper_exact'])>0:
        assert intervals and intervals[0][0]==F(bounds['lower_exact']) and intervals[-1][1]==F(bounds['upper_exact'])
        assert all(0<a<=b for a,b in intervals)
        assert all(a[1]==b[0] for a,b in zip(intervals,intervals[1:]))
    else:assert not intervals
    pieces=[fallback]*len(intervals);seen=set();flows=0
    for piece in record['slices']:
        index=piece['index'];assert type(index) is int and 0<=index<len(intervals) and index not in seen;seen.add(index)
        lo,hi=intervals[index];assert piece['S_interval_exact']==[str(lo),str(hi)]
        best=None;paths={}
        for trial in piece['trials']:
            p=ROOT/trial['proof'];assert sha(p)==trial['SHA256'];proof=load_gz(p)
            value=verify_bound(topology,beta,costs,lo,hi,proof);flows+=1
            assert value==F(trial['lower_exact']);paths[str(p.resolve())]=value
            best=value if best is None else max(best,value)
        assert best is not None and paths[str((ROOT/piece['best_proof']).resolve())]==best
        assert sha(ROOT/piece['best_proof'])==piece['best_proof_SHA']
        pieces[index]=max(fallback,best);assert pieces[index]==F(piece['lower_exact'])
    assert flows==record['exact_integer_flow_calls'] and list(map(str,pieces))==record['positive_slice_lowers_exact']
    lows=list(pieces)
    if bounds['zero_possible']:
        value=stock_value(scope,[0]*len(scope['stations']),beta,costs);assert value['feasible']
        assert value['price']==F(record['zero_lower_exact']);lows.append(value['price'])
    else:assert record['zero_lower_exact'] is None
    assert lows and record['lower']==outward(max(fallback,min(lows)),False)
    for call in record['candidate_LP_calls']:
        assert call['candidate_only'];folder=(ROOT/call['model']).parent
        launch=read(folder/'call.json');returned=read(folder/'return.json')
        assert launch['kind']=='Lagrangian_candidate_selection_only' and launch['objective_not_a_price_bound']
        assert launch['Seed']==0 and launch['Threads']==1 and launch['model_SHA']==sha(folder/'model.mps')
        assert all(returned[k]==call[k] for k in returned)
    return dict(exact_flow_certificates=flows,candidate_LP_calls=len(record['candidate_LP_calls']),Optimize_replayed=0)


def qualify(label):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round152_qualify import scope
    configure();affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[];energy_checks=0;rejected=0
    domains=[scope([1.,.5,.25],[[0,1,2,3,4]]*3,2,5,0.,.75,[.125]*3),
        scope([1.,.5],[[0,1,2,3,4]]*2,0,4,.05,.3),
        scope([.5,.25,.75],[[1],[0,2,5],[1,3]],2,7,.2,.8)]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for domain_index,domain in enumerate(domains):
            topology=Thresholds(domain);oracle=GraphOracle(domain,env,parts=3,iterations=4)
            labels=list(product(*[s['support'] for s in domain['stations']]))
            legal=[Y for Y in labels if stock_value(domain,Y)['feasible']];assert legal
            costs={(s['i'],y):F(((-1)**(s['i']+y))*(y+1),8) for s in domain['stations'] for y in s['support']}
            for beta in [0.,1.7]:
                for index,(lo,hi) in enumerate(oracle.intervals):
                    for parameter_index,parameters in enumerate([(0,0,0),(.375,-.25,.125),(-.5,.375,0),(-.5,-.25,.5)]):
                        proof=cut_bound(topology,beta,costs,lo,hi,parameters)
                        network=topology.network(beta,costs,lo,hi,*parameters)
                        lower=verify_bound(topology,beta,costs,lo,hi,proof);energies=[]
                        if rejected==0 and proof['flow']['positive_flows']:
                            invalid=[];base=proof['flow']
                            invalid.append(dict(base,flow_value=base['flow_value']+1))
                            wrong=json.loads(json.dumps(base));arc_index=wrong['positive_flows'][0][0]
                            wrong['positive_flows'][0][1]=network['arcs'][arc_index][2]+1;invalid.append(wrong)
                            wrong=json.loads(json.dumps(base));wrong['positive_flows'][0][0]=-1;invalid.append(wrong)
                            for bad in invalid:
                                try:verify_flow(network,bad)
                                except AssertionError:rejected+=1
                                else:raise AssertionError('altered flow certificate was accepted')
                        p,r,eta=map(F,parameters);n=len(domain['stations'])
                        for Y in labels:
                            f=topology.features(Y,costs);side={network['source']}
                            for s,y in zip(domain['stations'],Y):
                                for j,z in enumerate(s['support'][:-1]):
                                    if y>z:side.add(topology.nodes[s['i'],j])
                            represented_A=topology.A_constant+sum((a*int(node in side) for node,a in enumerate(topology.A_unary)),F(0))
                            represented_A+=sum((a*abs(int(u in side)-int(v in side)) for (u,v),a in topology.A_pairs.items()),F(0))
                            assert represented_A==f['A']
                            cut=F(network['constant']+sum(c for a,b,c in network['arcs'] if a in side and b not in side),SCALE)
                            exact=(F(beta)*f['A']/(n*hi)+f['d']+p*f['T']-max(p*domain['Bminus'],p*domain['B'])+
                                r*f['S']-max(r*lo,r*hi)+eta*(f['A']-n*F(domain['gamma_U'])*f['S']))
                            assert 0<=exact-cut<=F(network['rounding_terms'],SCALE)
                            assert lower<=cut;energies.append(cut);energy_checks+=1
                            v=stock_value(domain,Y,beta,costs)
                            if v['feasible'] and lo<=v['S']<=hi:assert exact<=v['price']
                        assert lower==min(energies)
                        save_gz(target/f'energy_{domain_index}_{beta}_{index}_{parameter_index}.json.gz',proof)
                true=min(stock_value(domain,Y,beta,costs)['price'] for Y in legal)
                result=oracle.price(beta,costs,target/f'price_{domain_index}_{beta}',cap=20,warm=legal[:2])
                assert F(result['lower'])<=true<=F(result['upper'])
                verification=audit_graph_price(result)
                facts.append(dict(domain=domain_index,beta=beta,Cartesian_labels=len(labels),legal_stocks=len(legal),
                    exact_price=str(true),lower=result['lower'],upper=result['upper'],verification=verification,
                    source_SHA=sha(__file__),frozen_core_SHA=sha(ROOT/'scripts/round153_pricing.py')))
    assert rejected==3
    write(target/'result.json',dict(PASS=True,facts=facts,Cartesian_energy_checks=energy_checks,rejected_altered_flows=rejected,
        source_SHA=sha(__file__),integer_scale=SCALE,all_floors_are_mathematical_floor=True,
        signed_unary_and_constant=True,beta_zero=True,zero_branch=True,fixed_and_gapped_state_sets=True,
        candidate_LP_objectives_are_not_price_uppers=True))
    print(json.dumps(dict(PASS=True,controls=len(facts),Cartesian_energy_checks=energy_checks)),flush=True)


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
