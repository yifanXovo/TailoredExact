"""Reusable full-domain pricing: beta*f(Y)+sum_i d_i(Y_i).

The R152 normalized binary inventory formulation is retained. Zero stock is
separate, beta=0 is a genuine projection direction, and hard-total DP always
supplies a safe fallback. No unary penalty is implicitly added.
"""
from fractions import Fraction as F
from itertools import combinations
from round152_math import states,s_bounds,unary_dp,h_exact
from round143_math import outward
from round143_lp import semantics
from round153_common import *

def keyed(d):return {f'{i}:{y}':float(v) for (i,y),v in d.items()}
def unkeyed(d):return {tuple(map(int,k.split(':'))):v for k,v in d.items()}

def stock_value(scope,Y,beta=1.,d=None):
    ss=scope['stations'];Y=tuple(map(int,Y));assert len(Y)==len(ss)
    r=sorted(F(s['c'])*y for s,y in zip(ss,Y));S=sum(r,F(0));n=len(ss)
    A=sum(((2*k-n+1)*v for k,v in enumerate(r)),F(0));G=A/(n*S) if S else F(0)
    f=max(F(scope['gamma_L']),G)
    feasible=all(y in s['support'] for s,y in zip(ss,Y)) and scope['Bminus']<=sum(Y)<=scope['B'] and G<=F(scope['gamma_U'])
    price=F(beta)*f+sum((F((d or {}).get((s['i'],y),0.)) for s,y in zip(ss,Y)),F(0))
    penalty=sum((h_exact(s,y) for s,y in zip(ss,Y)),F(0))
    return dict(Y=list(Y),feasible=feasible,G=G,f=f,price=price,penalty=penalty,phi=f+penalty,total=sum(Y),S=S)

def serial_stock(v):
    return {k:(float(x) if isinstance(x,F) else x) for k,x in v.items()}|{'f_exact':str(v['f']),'price_exact':str(v['price'])}

class Oracle:
    def __init__(self,scope,env,old_joint=False):
        from round100_gurobi_runtime import gp
        self.gp=gp;self.env=env;self.scope=scope;self.bounds=s_bounds(scope);self.model=None;self.old_joint=old_joint
        if self.bounds['upper']<=0:return
        ss=scope['stations'];n=len(ss);b=self.bounds
        tl=outward(1/F(b['upper']),False);tu=outward(1/F(b['lower']),True)
        m=gp.Model(env=env);self.model=m
        self.x=m.addVars(states(scope),vtype=gp.GRB.BINARY,name='x')
        w=m.addVars(states(scope),lb=0,ub=tu,name='w');t=m.addVar(lb=tl,ub=tu,name='t')
        z=m.addVars([s['i'] for s in ss],lb=0,name='z');r=m.addVars([s['i'] for s in ss],lb=0,name='r')
        for s in ss:
            i=s['i'];ys=s['support'];m.addConstr(gp.quicksum(self.x[i,y] for y in ys)==1,name=f'onehot_{i}')
            m.addConstr(gp.quicksum(w[i,y] for y in ys)==t,name=f'mass_{i}')
            for y in ys:
                m.addConstr(w[i,y]>=tl*self.x[i,y],name=f'w_lb_{i}_{y}')
                m.addConstr(w[i,y]<=tu*self.x[i,y],name=f'w_ub_{i}_{y}')
            m.addConstr(z[i]==gp.quicksum(y*w[i,y] for y in ys),name=f'normalized_inventory_{i}')
            m.addConstr(r[i]==s['c']*z[i],name=f'normalized_ratio_{i}')
        total=gp.quicksum(y*self.x[i,y] for i,y in self.x)
        m.addConstr(total>=scope['Bminus'],name='hard_lower');m.addConstr(total<=scope['B'],name='hard_upper')
        m.addConstr(gp.quicksum(r.values())==1,name='normalization')
        m.addConstr(gp.quicksum(z.values())>=scope['Bminus']*t,name='scaled_stock_lower')
        m.addConstr(gp.quicksum(z.values())<=scope['B']*t,name='scaled_stock_upper')
        pairs=list(combinations([s['i'] for s in ss],2));a=m.addVars(pairs,lb=0,name='a')
        for i,j in pairs:
            m.addConstr(a[i,j]>=r[i]-r[j],name=f'abs_p_{i}_{j}')
            m.addConstr(a[i,j]>=r[j]-r[i],name=f'abs_m_{i}_{j}')
        self.q=m.addVar(lb=scope['gamma_L'],ub=scope['gamma_U'],name='q');A=gp.quicksum(a.values())
        m.addConstr(A<=n*self.q,name='true_G_epigraph')
        m.addConstr(A<=outward(F(n)*F(scope['gamma_U']),True),name='physical_G_upper')
        if old_joint:
            # Optional necessary integer consequences, also valid with positive
            # denominator at every legal inventory. No state/domain is removed.
            from round140_math import count_rows
            counts=count_rows({s['i']:s['support'] for s in ss},{s['i']:F(s['c']) for s in ss},scope['Bminus'],scope['B'])
            for label,cst in [('TC',F(0)),('TC2',counts['constant'])]:
                terms=gp.quicksum(outward(v,False)*w[k] for k,v in counts[label].items())
                m.addConstr(A>=outward(cst,False)*t+terms,name='old_normalized_'+label)
            self.joint_transport=[]
            for j,slope,endpoint,sense in [(1,tl,scope['Bminus'],'>'),(2,tu,scope['B'],'>'),(3,tu,scope['Bminus'],'<'),(4,tl,scope['B'],'<')]:
                coeff={k:float(-F(slope)*k[1]) for k in self.x}
                correction=sum((min if sense=='>' else max)(F(coeff[s['i'],y])+F(slope)*y for y in s['support']) for s in ss)
                e=gp.quicksum(z.values())+gp.quicksum(coeff[k]*self.x[k] for k in self.x)-endpoint*t
                rhs=outward(-F(slope)*endpoint+correction,sense=='<')
                m.addConstr(e>=rhs if sense=='>' else e<=rhs,name=f'old_TS{j}')
                self.joint_transport.append(dict(row=f'old_TS{j}',onehot_coefficient_correction_exact=str(correction),rhs=rhs))
        m.update();self.structure=semantics(m);self.t_bounds=[tl,tu]

    def close(self):
        if self.model is not None:self.model.dispose()

    def price(self,beta,d,target,cap=30.,warm=(),absolute_gap=1e-7,node_limit=None,global_deadline=None):
        gp=self.gp;scope=self.scope;ss=scope['stations'];beta=float(beta)
        assert beta>=0 and math.isfinite(beta)
        d={k:F(d.get(k,0.)) for k in states(scope)}
        target=Path(target);target.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
        dp=unary_dp(scope,d);assert dp is not None
        fallback=F(beta)*F(scope['gamma_L'])+F(dp['exact']);stocks={};best=None;zero=None
        def consider(Y):
            nonlocal best
            v=stock_value(scope,Y,beta,d)
            if not v['feasible']:return
            stocks[tuple(v['Y'])]=v
            if best is None or v['price']<best:best=v['price']
        consider(dp['Y'])
        if self.bounds['zero_possible']:
            z=stock_value(scope,[0]*len(ss),beta,d);assert z['feasible'];zero=z['price'];consider(z['Y'])
        for Y in warm:consider(Y)
        calls=[];lower=outward(fallback,False)
        if best is not None and best==fallback:
            reason='exact_hard_total_DP_attained_in_full_domain'
        elif self.model is None:
            assert zero is not None;lower=outward(zero,False);reason='zero_only'
        else:
            m=self.model
            anchors={s['i']:(min(d[s['i'],y] for y in s['support'])+max(d[s['i'],y] for y in s['support']))/2 for s in ss}
            centered={k:v-anchors[k[0]] for k,v in d.items()}
            largest=max([abs(beta)]+[abs(float(v)) for v in centered.values()]+[1e-30])
            scale=math.ldexp(1.,math.ceil(math.log2(largest)))
            costs={k:v/F(scale) for k,v in centered.items()};scaled_beta=F(beta)/F(scale)
            m.setObjective(float(scaled_beta)*self.q+gp.quicksum(outward(v,False)*self.x[k] for k,v in costs.items()))
            m.update();m.write(str(target/'model.mps'))
            with gp.read(str(target/'model.mps'),env=self.env) as back:assert semantics(back)==semantics(m)
            correction=sum(max([F(0)]+[F(self.x[s['i'],y].Obj)-costs[s['i'],y] for y in s['support']]) for s in ss)
            correction+=max(F(0),(F(self.q.Obj)-scaled_beta)*F(scope['gamma_U']))
            guard=1e-6*(abs(float(scaled_beta))+sum(max(abs(float(costs[s['i'],y])) for y in s['support']) for s in ss)+1.)
            if stocks:
                candidate=min((v for v in stocks.values() if v['S']>0),key=lambda v:v['price'],default=None)
                if candidate:
                    for s,y0 in zip(ss,candidate['Y']):
                        for y in s['support']:self.x[s['i'],y].Start=float(y==y0)
            m.Params.Threads=1;m.Params.Seed=0
            m.Params.TimeLimit=float(cap) if node_limit is None else gp.GRB.INFINITY
            if global_deadline is not None:m.Params.TimeLimit=max(0.,global_deadline-time.perf_counter())
            m.Params.NodeLimit=gp.GRB.INFINITY if node_limit is None else float(node_limit)
            m.Params.MIPGap=1e-7 if node_limit is None else 0.;m.Params.MIPGapAbs=float(absolute_gap/scale)
            m.Params.IntFeasTol=1e-6;m.Params.FeasibilityTol=1e-6;m.Params.OptimalityTol=1e-6
            m.Params.PoolSolutions=20;m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.LogFile=str(target/'native.log')
            write(target/'call.json',dict(UTC=utc(),kind='MIP_full_domain',scope=scope,beta=beta,d=keyed(d),d_exact={f'{i}:{y}':str(v) for (i,y),v in d.items()},
                  cap=cap if node_limit is None else None,node_limit=node_limit,online_wall_time_switch=False,
                  whole_method_global_deadline_present=global_deadline is not None,
                  actual_Native_TimeLimit=m.Params.TimeLimit if m.Params.TimeLimit<1e99 else None,
                  Seed=0,Threads=1,model_SHA=sha(target/'model.mps'),t_bounds=self.t_bounds,
                  scale=scale,anchors_exact={str(i):str(v) for i,v in anchors.items()},
                  numerical_guard_scaled=guard,objective_correction_scaled_exact=str(correction),
                  full_support=True,old_joint=self.old_joint,joint_transport=getattr(self,'joint_transport',[]),matrix_readback=True))
            built=time.perf_counter();m.optimize();done=time.perf_counter()
            write(target/'return.json',dict(UTC=utc(),Status=m.Status,Runtime=m.Runtime,Work=m.Work))
            accepted=(gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT) if node_limit is None else (gp.GRB.OPTIMAL,gp.GRB.NODE_LIMIT)
            qualified=m.Status in accepted and math.isfinite(m.ObjBound) and abs(m.ObjBound)<1e90
            positive=max(fallback,F(scale)*(F(m.ObjBound)-F(guard)-correction)+sum(anchors.values(),F(0))) if qualified else fallback
            # An unexpected/INFEASIBLE Native status is not an exact proof
            # that the positive-stock branch is empty. Retain the hard-total
            # DP lower for that branch, even when a zero branch also exists.
            empty=False
            for j in range(m.SolCount):
                m.Params.SolutionNumber=j
                consider([max(s['support'],key=lambda y:self.x[s['i'],y].Xn) for s in ss])
            if m.SolCount:save_gz(target/'solution.json.gz',{v.VarName:v.X for v in m.getVars()})
            parts=([positive] if not empty else [])+([zero] if zero is not None else [])
            lower=outward(min(parts),False) if parts else None
            calls=[dict(Status=m.Status,Runtime=m.Runtime,Work=m.Work,nodes=m.NodeCount,
                        native_bound=m.ObjBound if qualified else None,bound_status_qualified=qualified,
                        construct_seconds=built-tick,optimize_seconds=done-built,positive_lower=outward(positive,False),
                        guard_original=scale*guard,scale=scale,pool_count=m.SolCount)]
            reason='complete_domain_normalized_integer_price' if qualified else 'safe_DP_fallback'
        best_out=outward(best,True) if best is not None else None
        result=dict(scope=scope,beta=beta,d=keyed(d),d_exact={f'{i}:{y}':str(v) for (i,y),v in d.items()},lower=lower,upper=best_out,
                    fallback_lower=outward(fallback,False),zero_lower=outward(zero,False) if zero is not None else None,
                    stocks=[serial_stock(v) for v in stocks.values()],calls=calls,reason=reason,
                    complete_domain=True,seconds=time.perf_counter()-tick,
                    decision='EMPTY_DOMAIN' if lower is None else 'RESOLVED' if best_out is not None and best_out-lower<=1e-5 else 'UNDECIDED',
                    upper_is_inventory_price_only=True)
        write(target/'result.json',result);return result
