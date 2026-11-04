"""Research-only full price from an exhaustive positive-S partition.

The frozen Oracle arithmetic is reused with a conditional stock filter and
metadata writer. No frozen module or global namespace is mutated.
"""
import types
from fractions import Fraction as F
from itertools import product,combinations
from round153_pricing import Oracle,stock_value,serial_stock,keyed
from round152_math import s_bounds,states,unary_dp
from round143_math import outward
from round143_lp import semantics
from round153_common import *

class SliceOracle(Oracle):
    def __init__(self,scope,env,lo,hi,old_joint=True):
        super().__init__(scope,env,old_joint=old_joint)
        assert F(0)<lo<=hi and self.model is not None
        self.lo,self.hi=lo,hi;m=self.model;gp=self.gp
        tl,tu=outward(1/hi,False),outward(1/lo,True)
        t=m.getVarByName('t');assert tl>=t.LB and tu<=t.UB
        t.LB,t.UB=tl,tu
        self.bounds=dict(self.bounds,lower=outward(lo,False),upper=outward(hi,True),
            lower_exact=str(lo),upper_exact=str(hi),zero_possible=False)
        for i,y in self.x:
            m.getVarByName(f'w[{i},{y}]').UB=tu
            m.chgCoeff(m.getConstrByName(f'w_lb_{i}_{y}'),self.x[i,y],-tl)
            m.chgCoeff(m.getConstrByName(f'w_ub_{i}_{y}'),self.x[i,y],-tu)
        zsum=gp.quicksum(m.getVarByName(f'z[{s["i"]}]') for s in scope['stations'])
        self.slice_transport=[]
        for j,slope,endpoint,sense in [(1,tl,scope['Bminus'],'>'),(2,tu,scope['B'],'>'),(3,tu,scope['Bminus'],'<'),(4,tl,scope['B'],'<')]:
            coeff={k:float(-F(slope)*k[1]) for k in self.x}
            correction=sum((min if sense=='>' else max)(F(coeff[s['i'],y])+F(slope)*y for y in s['support']) for s in scope['stations'])
            e=zsum+gp.quicksum(coeff[k]*self.x[k] for k in self.x)-endpoint*t
            rhs=outward(-F(slope)*endpoint+correction,sense=='<')
            m.addConstr(e>=rhs if sense=='>' else e<=rhs,name=f'r153_slice_TS{j}')
            self.slice_transport.append(dict(row=f'r153_slice_TS{j}',onehot_coefficient_correction_exact=str(correction),rhs=rhs))
        m.update();self.t_bounds=[tl,tu];self.structure=semantics(m)
        self._core=types.FunctionType(Oracle.price.__code__,dict(Oracle.price.__globals__,
            stock_value=self._conditional_stock,write=self._write),argdefs=Oracle.price.__defaults__)

    def _conditional_stock(self,scope,Y,beta=1.,d=None):
        value=stock_value(scope,Y,beta,d)
        value['feasible']=value['feasible'] and self.lo<=value['S']<=self.hi
        return value

    def _metadata(self,original):
        value=dict(original)
        value.update(S_interval_exact=[str(self.lo),str(self.hi)],actual_t_bounds=self.t_bounds,
            lower_domain='original R intersect this positive-S interval',zero_handled_by_parent=True,
            true_stock_filter_includes_exact_S_interval=True,slice_TS_transport=self.slice_transport,
            core_source_SHA=sha(ROOT/'scripts/round153_pricing.py'))
        if value.get('kind')=='MIP_full_domain':value['kind']='MIP_positive_S_slice'
        if 'complete_domain' in value:
            value['complete_domain']=False
            value['upper_domain']='true feasible stock in this S interval'
            value['decision']='CONDITIONAL_'+value['decision']
            value['reason']={'complete_domain_normalized_integer_price':'conditional_normalized_integer_price',
                'safe_DP_fallback':'global_DP_fallback_for_conditional_slice',
                'exact_hard_total_DP_attained_in_full_domain':'global_DP_attained_by_a_slice_stock'}.get(value['reason'],value['reason'])
        return value

    def _write(self,path,value):write(path,self._metadata(value))

    def price(self,beta,d,target,cap=75.,warm=(),absolute_gap=1e-7):
        target=Path(target);target.mkdir(parents=True,exist_ok=False)
        write(target/'restriction.json',self._metadata(dict(declared_before_Optimize=True,
            original_scope=self.scope,only_pricing_restricted=True,all_original_states_retained=True)))
        # The core creates its own output directory; reserve a nested raw folder.
        result=self._core(self,beta,d,target/'raw',cap=cap,warm=warm,absolute_gap=absolute_gap)
        result=self._metadata(result);write(target/'result.json',result);return result

class PartitionedOracle:
    def __init__(self,scope,env,old_joint=True,parts=4):
        tick=time.perf_counter();self.scope=scope;self.bounds=s_bounds(scope);self.children=[]
        lo,hi=F(self.bounds['lower_exact']),F(self.bounds['upper_exact'])
        self.intervals=[]
        if hi>0:
            assert lo>0
            points=[lo,hi] if lo==hi else [lo+(hi-lo)*j/parts for j in range(parts+1)]
            self.intervals=list(zip(points[:-1],points[1:]))
            self.children=[SliceOracle(scope,env,a,b,old_joint) for a,b in self.intervals]
            assert self.intervals[0][0]==lo and self.intervals[-1][1]==hi
            assert all(a[1]==b[0] for a,b in zip(self.intervals,self.intervals[1:]))
        self.build_seconds=time.perf_counter()-tick

    def close(self):
        for child in self.children:child.close()

    def price(self,beta,d,target,cap=300.,warm=(),absolute_gap=1e-7):
        target=Path(target);target.mkdir(parents=True,exist_ok=False);tick=time.perf_counter();beta=float(beta)
        assert beta>=0 and math.isfinite(beta)
        scope=self.scope;costs={k:F(d.get(k,0.)) for k in states(scope)};dp=unary_dp(scope,costs);assert dp is not None
        fallback=F(beta)*F(scope['gamma_L'])+F(dp['exact']);stock={}
        def consider(Y):
            value=stock_value(scope,Y,beta,costs)
            if value['feasible']:stock[tuple(value['Y'])]=value
        consider(dp['Y'])
        for Y in warm:consider(Y)
        zero=None
        if self.bounds['zero_possible']:
            value=stock_value(scope,[0]*len(scope['stations']),beta,costs);assert value['feasible']
            zero=value['price'];consider(value['Y'])
        record=dict(scope=scope,beta=beta,d=keyed(costs),d_exact={f'{i}:{y}':str(v) for (i,y),v in costs.items()},
            positive_S_bounds=self.bounds,intervals_exact=[[str(a),str(b)] for a,b in self.intervals],
            exact_closed_interval_cover=True,legal_zero_separate=True,unresolved_or_missing_slice_uses_global_DP=True,
            frozen_core_SHA=sha(ROOT/'scripts/round153_pricing.py'),oracle_initial_build_seconds=self.build_seconds,
            Native_cap_sum=float(cap),outer_cost_includes_all_build_DP_and_output=True)
        write(target/'partition.json',record)
        pieces=[fallback]*len(self.children);child_results=[];calls=[]
        for j,child in enumerate(self.children):
            if stock and min(v['price'] for v in stock.values())==fallback:break
            folder=target/f'slice{j:03}'
            child_warm=[v['Y'] for v in stock.values() if child.lo<=v['S']<=child.hi]
            child_warm=sorted(child_warm,key=lambda Y:stock[tuple(Y)]['price'])[:4]
            r=child.price(beta,costs,folder,cap=float(cap)/len(self.children),warm=child_warm,absolute_gap=absolute_gap)
            assert not r['complete_domain'] and r['lower'] is not None
            pieces[j]=F(r['lower']);child_results.append(dict(index=j,result=str((folder/'result.json').relative_to(ROOT)),lower=r['lower'],upper=r['upper']))
            for value in r['stocks']:consider(value['Y'])
            calls.extend(dict(c,slice_index=j,scope_restriction=r['S_interval_exact'],conditional=True) for c in r['calls'])
        all_lower=pieces+([zero] if zero is not None else []);assert all_lower
        lower=outward(max(fallback,min(all_lower)),False)
        best=min((v['price'] for v in stock.values()),default=None);upper=outward(best,True) if best is not None else None
        record.update(lower=lower,upper=upper,fallback_lower=outward(fallback,False),fallback_exact=str(fallback),
            zero_lower=outward(zero,False) if zero is not None else None,positive_slice_lowers_exact=list(map(str,pieces)),
            stocks=[serial_stock(v) for v in stock.values()],calls=calls,child_results=child_results,
            complete_domain=True,partitioned_full_price=True,seconds=time.perf_counter()-tick,
            reason='exhaustive_positive_S_partition_plus_zero',upper_is_inventory_price_only=True,
            decision='RESOLVED' if upper is not None and upper-lower<=1e-5 else 'UNDECIDED')
        write(target/'result.json',record);return record

def qualify(label):
    from round100_gurobi_runtime import gp
    from round150_lp import affinity
    from round152_qualify import scope
    configure();affinity();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    domains=[scope([1.,.5,.25],[[0,1,2,3,4]]*3,2,5,0.,.75,[.125]*3),
             scope([1.,.5],[[0,1,2,3,4]]*2,0,4,.05,.3)]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for j,d in enumerate(domains):
            universe=[stock_value(d,Y) for Y in product(*[s['support'] for s in d['stations']])]
            universe=[v for v in universe if v['feasible']]
            oracle=PartitionedOracle(d,env);checks=0
            for value in universe:
                if value['S']==0:assert oracle.bounds['zero_possible'];continue
                covered=[child for child in oracle.children if child.lo<=value['S']<=child.hi];assert covered
                for child in covered:
                    t=1/value['S'];point={'t':t,'q':value['f']}
                    for s,y0 in zip(d['stations'],value['Y']):
                        i=s['i'];point[f'z[{i}]']=y0*t;point[f'r[{i}]']=F(s['c'])*y0*t
                        for y in s['support']:point[f'x[{i},{y}]']=F(y==y0);point[f'w[{i},{y}]']=t*(y==y0)
                    for i,k in combinations([s['i'] for s in d['stations']],2):point[f'a[{i},{k}]']=abs(point[f'r[{i}]']-point[f'r[{k}]'])
                    for v in child.model.getVars():
                        assert F(v.LB)<=point[v.VarName] and (v.UB>1e90 or point[v.VarName]<=F(v.UB))
                    for c in child.model.getConstrs():
                        e=child.model.getRow(c);lhs=sum(F(e.getCoeff(k))*point[e.getVar(k).VarName] for k in range(e.size()));rhs=F(c.RHS)
                        assert lhs>=rhs if c.Sense=='>' else lhs<=rhs if c.Sense=='<' else lhs==rhs,(j,c.ConstrName,value['Y'])
                        checks+=1
            costs={(s['i'],y):(-2.*y if s['i']==1 else .5*y) for s in d['stations'] for y in s['support']}
            for beta in [0.,1.7]:
                exact=min(stock_value(d,v['Y'],beta,costs)['price'] for v in universe)
                r=oracle.price(beta,costs,target/f'd{j}_beta{beta}',cap=20)
                assert F(r['lower'])<=exact and r['upper'] is not None and exact<=F(r['upper'])
                segment_checks=[]
                for child_record in r['child_results']:
                    child=oracle.children[child_record['index']];cr=read(ROOT/child_record['result'])
                    relevant=[v for v in universe if child.lo<=v['S']<=child.hi]
                    for value in cr['stocks']:
                        true_stock=stock_value(d,value['Y'],beta,costs)
                        assert true_stock['feasible'] and child.lo<=true_stock['S']<=child.hi
                    if relevant:
                        true_min=min(stock_value(d,v['Y'],beta,costs)['price'] for v in relevant)
                        assert F(cr['lower'])<=true_min and (cr['upper'] is None or true_min<=F(cr['upper']))
                    else:
                        true_min=None;assert not cr['stocks'] and cr['upper'] is None
                    segment_checks.append(dict(index=child_record['index'],stocks=len(relevant),
                        exact=str(true_min) if true_min is not None else None,lower=cr['lower'],upper=cr['upper']))
                facts.append(dict(domain=j,beta=beta,exact=str(exact),lower=r['lower'],upper=r['upper'],calls=len(r['calls']),
                    all_true_integer_rows_checked=checks,stocks=len(universe),all_positive_stocks_covered=True,
                    zero_separate=oracle.bounds['zero_possible'],individual_segment_checks=segment_checks))
            oracle.close()
    write(target/'result.json',dict(PASS=True,facts=facts,tests_only_new_partition_and_transport=True,Optimize_is_qualification_only=True))
    print(json.dumps(dict(PASS=True,controls=len(facts))),flush=True)

if __name__=='__main__':qualify(*sys.argv[1:])
