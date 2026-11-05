"""Targeted tightening after the observed weak state-product LP screen.

Conditional S bounds use only the same hard-total/support domain. Four tight
aggregate cost McCormick rows retain hard-total DP information that state
products alone need not imply. No partition/CDF/flow or instance rule is used.
"""
from fractions import Fraction as F
from round143_math import denominator,outward
from round152_math import states,unary_dp
from round154_residual import ResidualOracle
from round154_common import *

class StrengthenedResidualOracle(ResidualOracle):
    def __init__(self,scope,env):
        tick=time.perf_counter();super().__init__(scope,env,total_product=True)
        self.conditional=[];self.cost_rows=[]
        if self.model is None:return
        gp=self.gp;m=self.model;ss=scope['stations'];c={s['i']:F(s['c']) for s in ss}
        supports={s['i']:s['support'] for s in ss};l,u=self.bounds['lower'],self.bounds['upper']
        for i,y in states(scope):
            x,z=self.x[i,y],self.z[i,y];parts={}
            for active in [True,False]:
                ys=[y] if active else [v for v in supports[i] if v!=y]
                if ys:
                    b=denominator(c,supports|{i:ys},scope['Bminus'],scope['B'])
                else:b=dict(applicable=False)
                # The old denominator helper also says "not applicable" when
                # S_L=0. That is not an empty domain: our positive branch can
                # still use its S_U and the already qualified global l.
                if 'S_U_exact' not in b:
                    if active:x.UB=0.
                    else:x.LB=1.
                    parts[str(active)]=dict(impossible=True);continue
                lo=max(F(l),F(b['S_L_exact']));hi=min(F(u),F(b['S_U_exact']))
                if hi<lo:
                    if active:x.UB=0.
                    else:x.LB=1.
                    parts[str(active)]=dict(impossible_positive_branch=True);continue
                lo,hi=outward(lo,False),outward(hi,True)
                if active:
                    m.addConstr(z>=lo*x,name=f'conditional_Sx_lower_{i}_{y}')
                    m.addConstr(z<=hi*x,name=f'conditional_Sx_upper_{i}_{y}')
                else:
                    m.addConstr(self.S-z>=lo*(1-x),name=f'conditional_complement_lower_{i}_{y}')
                    m.addConstr(self.S-z<=hi*(1-x),name=f'conditional_complement_upper_{i}_{y}')
                parts[str(active)]=dict(lower=lo,upper=hi)
            self.conditional.append(dict(i=i,y=y,parts=parts))
        self.Dcost=m.addVar(lb=-gp.GRB.INFINITY,name='hard_cost_D')
        self.Wcost=m.addVar(lb=-gp.GRB.INFINITY,name='hard_cost_W')
        m.update();self.tighten_construct_seconds=time.perf_counter()-tick

    def price(self,beta,d,tau,target,**kwargs):
        if self.model is None:return super().price(beta,d,tau,target,**kwargs)
        tick=time.perf_counter();beta=F(beta);tau=F(tau);ss=self.scope['stations'];u=F(self.bounds['upper']);gp=self.gp;m=self.model
        d={k:F(d.get(k,0.)) for k in states(self.scope)}
        anchors={s['i']:(min(d[s['i'],y] for y in s['support'])+max(d[s['i'],y] for y in s['support']))/2 for s in ss}
        centered={k:v-anchors[k[0]] for k,v in d.items()};anchor=sum(anchors.values(),F(0))
        boundA=F(len(ss))*F(self.scope['gamma_U'])*u
        magnitude=max(sum(max(abs(centered[s['i'],y]) for y in s['support']) for s in ss)*u,
                      abs(anchor-tau)*u,abs(anchor+beta*F(self.scope['gamma_L'])-tau)*u,
                      beta/F(len(ss))*boundA,F(1,2**40))
        scale=math.ldexp(1.,math.ceil(math.log2(float(magnitude))))
        cost={k:outward(v/F(scale),False) for k,v in centered.items()}
        if self.cost_rows:m.remove(self.cost_rows);m.update()
        lo=unary_dp(self.scope,{k:F(v) for k,v in cost.items()});hi=unary_dp(self.scope,{k:-F(v) for k,v in cost.items()})
        assert lo and hi
        a=outward(F(lo['exact']),False);b=outward(-F(hi['exact']),True)
        self.Dcost.LB=a;self.Dcost.UB=b
        rows=[m.addConstr(self.Dcost==gp.quicksum(cost[k]*self.x[k] for k in cost),name='hard_cost_D_definition'),
              m.addConstr(self.Wcost==gp.quicksum(cost[k]*self.z[k] for k in cost),name='hard_cost_W_definition')]
        l,u=self.bounds['lower'],self.bounds['upper']
        for name,slope,endpoint,sense in [('ll',l,a,'>'),('uu',u,b,'>'),('ul',u,a,'<'),('lu',l,b,'<')]:
            e=self.Wcost-slope*self.Dcost-endpoint*self.S
            rhs=outward(-F(slope)*F(endpoint),sense=='<')
            rows.append(m.addConstr(e>=rhs if sense=='>' else e<=rhs,name='tight_DP_cost_product_'+name))
        self.cost_rows=rows;m.update();setup=time.perf_counter()-tick
        result=super().price(beta,d,tau,target,**kwargs)
        call=read(Path(target)/'call.json')
        assert call['scale']==scale and call['residual_coefficients']['state']=={f'{i}:{y}':v for (i,y),v in cost.items()}
        extension=dict(source_SHA=sha(__file__),frozen_core_SHA=sha(ROOT/'scripts/round154_residual.py'),
                       conditional_S_bounds=self.conditional,tight_cost_bounds=[a,b],tight_cost_DP_exact=[lo['exact'],str(-F(hi['exact']))],
                       conditional_construct_seconds=self.tighten_construct_seconds,cost_product_setup_seconds=setup,
                       same_integer_domain=True,not_an_RN_dominance_claim=True)
        write(Path(target)/'strengthening.json',extension)
        result['strengthening']=extension;result['seconds']+=setup;write(Path(target)/'result.json',result)
        return result
