"""Pricing-only threshold disaggregation of normalized pairwise differences.

At a true integer stock, cumulative w above every ratio threshold is either
zero or t. Integrating its pairwise absolute difference gives n*G exactly.
Downward threshold widths only weaken the added necessary inequalities.
"""
import types
from fractions import Fraction as F
from itertools import product,combinations
from round143_math import outward
from round143_lp import semantics
from round153_pricing import Oracle,stock_value
from round153_common import *


class TransportOracle(Oracle):
    def __init__(self,scope,env,old_joint=True):
        tick=time.perf_counter();super().__init__(scope,env,old_joint=old_joint)
        self.thresholds=[];self.extension_source_SHA=sha(__file__)
        self.core_source_SHA=sha(ROOT/'scripts/round153_pricing.py')
        before_rows=self.model.NumConstrs if self.model is not None else 0
        before_columns=self.model.NumVars if self.model is not None else 0
        if self.model is not None:
            m=self.model;gp=self.gp;ss=scope['stations'];terms=[]
            for left,right in combinations(ss,2):
                i,j=left['i'],right['i'];li={y:F(left['c'])*y for y in left['support']};rj={y:F(right['c'])*y for y in right['support']}
                points=sorted({F(0)}|set(li.values())|set(rj.values()))
                for k,(lo,hi) in enumerate(zip(points[:-1],points[1:])):
                    assert hi>lo
                    a=m.addVar(lb=0.,ub=self.t_bounds[1],name=f'td_{i}_{j}_{k}')
                    wi=gp.quicksum(m.getVarByName(f'w[{i},{y}]') for y,r in li.items() if r>lo)
                    wj=gp.quicksum(m.getVarByName(f'w[{j},{y}]') for y,r in rj.items() if r>lo)
                    m.addConstr(a>=wi-wj,name=f'td_pos_{i}_{j}_{k}')
                    m.addConstr(a>=wj-wi,name=f'td_neg_{i}_{j}_{k}')
                    coefficient=outward(hi-lo,False);assert F(0)<=F(coefficient)<=hi-lo
                    terms.append(coefficient*a);self.thresholds.append((i,j,lo,hi,a))
            D=gp.quicksum(terms);n=len(ss)
            m.addConstr(D<=n*self.q,name='td_true_G_epigraph')
            m.addConstr(D<=outward(F(n)*F(scope['gamma_U']),True),name='td_physical_G_upper')
            m.update();self.structure=semantics(m)
        self.extension=dict(name='normalized_threshold_pair_absolute_difference',
            antecedent='R88 B1/CDF-OT epigraph, homogenized by the existing common t',
            new_general_Gini_theory_claimed=False,
            extra_columns=(self.model.NumVars if self.model is not None else 0)-before_columns,
            extra_rows=(self.model.NumConstrs if self.model is not None else 0)-before_rows,
            threshold_intervals=len(self.thresholds),threshold_width_rounding='downward_nonnegative',
            true_integer_domain_unchanged=True,all_original_pricing_rows_retained=True,
            added_only_to_pricing_model=True,constructor_seconds=time.perf_counter()-tick,
            extension_source_SHA=self.extension_source_SHA,frozen_core_SHA=self.core_source_SHA)
        self._core=types.FunctionType(Oracle.price.__code__,dict(Oracle.price.__globals__,write=self._write),argdefs=Oracle.price.__defaults__)

    def _metadata(self,value):return dict(value,pricing_extension=self.extension)
    def _write(self,path,value):write(path,self._metadata(value))

    def price(self,beta,d,target,cap=300.,warm=(),absolute_gap=1e-7):
        result=self._core(self,beta,d,target,cap=cap,warm=warm,absolute_gap=absolute_gap)
        result=self._metadata(result);write(Path(target)/'result.json',result);return result


def qualify(label):
    from round100_gurobi_runtime import gp
    from round150_lp import affinity
    from round152_qualify import scope
    configure();affinity();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    domains=[scope([1.,.5,.25],[[0,1,2,3,4]]*3,2,5,0.,.75,[.125]*3),
        scope([1.,.5],[[0,1,2,3,4]]*2,0,4,.05,.3)]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for index,d in enumerate(domains):
            universe=[stock_value(d,Y) for Y in product(*[s['support'] for s in d['stations']])]
            universe=[v for v in universe if v['feasible']];oracle=TransportOracle(d,env);checks=0;identities=0
            for value in universe:
                if not value['S']:continue
                t=1/value['S'];point={'t':t,'q':value['f']};ratios={}
                for s,y0 in zip(d['stations'],value['Y']):
                    i=s['i'];ratios[i]=F(s['c'])*y0;point[f'z[{i}]']=y0*t;point[f'r[{i}]']=ratios[i]*t
                    for y in s['support']:point[f'x[{i},{y}]']=F(y==y0);point[f'w[{i},{y}]']=t*(y==y0)
                for i,j in combinations(ratios,2):point[f'a[{i},{j}]']=abs(ratios[i]-ratios[j])*t
                exact_D=F(0)
                for i,j,lo,hi,a in oracle.thresholds:
                    point[a.VarName]=t*int((ratios[i]>lo)!=(ratios[j]>lo));exact_D+=(hi-lo)*point[a.VarName]
                assert exact_D==len(d['stations'])*value['G'];identities+=1
                for v in oracle.model.getVars():assert F(v.LB)<=point[v.VarName] and (v.UB>1e90 or point[v.VarName]<=F(v.UB))
                for c in oracle.model.getConstrs():
                    row=oracle.model.getRow(c);lhs=sum(F(row.getCoeff(k))*point[row.getVar(k).VarName] for k in range(row.size()));rhs=F(c.RHS)
                    assert lhs>=rhs if c.Sense=='>' else lhs<=rhs if c.Sense=='<' else lhs==rhs,(index,c.ConstrName,value['Y'])
                    checks+=1
            costs={(s['i'],y):(-2.*y if s['i']==1 else .5*y) for s in d['stations'] for y in s['support']}
            for beta in [0.,1.7]:
                exact=min(stock_value(d,v['Y'],beta,costs)['price'] for v in universe)
                r=oracle.price(beta,costs,target/f'd{index}_beta{beta}',cap=20,warm=[v['Y'] for v in universe[:4]])
                assert r['complete_domain'] and F(r['lower'])<=exact and r['upper'] is not None and exact<=F(r['upper'])
                if index==1 and beta==0.:assert len(r['calls'])==1,'Forced beta-zero Native interface must be exercised'
                facts.append(dict(domain=index,beta=beta,exact=str(exact),lower=r['lower'],upper=r['upper'],
                    Native_calls=len(r['calls']),true_positive_stock_identities=identities,all_actual_integer_rows_checked=checks,
                    legal_stocks=len(universe),zero_separate=oracle.bounds['zero_possible'],extension=oracle.extension))
            oracle.close()
    write(target/'result.json',dict(PASS=True,facts=facts,new_qualification_only=True))
    print(json.dumps(dict(PASS=True,controls=len(facts))),flush=True)


if __name__=='__main__':qualify(*sys.argv[1:])
