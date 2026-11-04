"""Interruptible original-coordinate target residual, with signed state costs.

All nonintegral RHS coefficients in the two residual epigraphs are rounded
down. Their objective is a relaxation of the exact binary64-input residual.
Native error is paid in residual units before positive-S conversion.
"""
from fractions import Fraction as F
from itertools import combinations
from round143_math import outward
from round143_lp import semantics
from round152_math import states,s_bounds,unary_dp
from round153_pricing import stock_value,serial_stock,keyed
from round154_common import *

def recover(tau,ell,l,u):
    tau,ell,l,u=map(F,(tau,ell,l,u)); assert 0<l<=u
    return tau+ell/(u if ell>=0 else l)

def transport(ell,tau,next_tau,l,u):
    delta=F(next_tau)-F(tau)
    return F(ell)-max(delta*F(l),delta*F(u))

class ResidualOracle:
    def __init__(self,scope,env,total_product=True):
        from round100_gurobi_runtime import gp
        self.gp=gp; self.env=env; self.scope=scope; self.bounds=s_bounds(scope)
        self.model=None; self.total_product=total_product
        if self.bounds['upper']<=0: return
        b=self.bounds; l,u=b['lower'],b['upper']; assert 0<l<=u
        ss=scope['stations']; n=len(ss); m=gp.Model(env=env); self.model=m
        self.x=m.addVars(states(scope),vtype=gp.GRB.BINARY,name='x')
        self.z=m.addVars(states(scope),lb=0.,ub=u,name='Sx')
        self.S=m.addVar(lb=l,ub=u,name='S')
        self.Y=m.addVars([s['i'] for s in ss],lb=0.,name='Y')
        self.r=m.addVars([s['i'] for s in ss],lb=0.,name='r')
        for s in ss:
            i=s['i']; ys=s['support']
            m.addConstr(gp.quicksum(self.x[i,y] for y in ys)==1,name=f'onehot_{i}')
            m.addConstr(self.Y[i]==gp.quicksum(y*self.x[i,y] for y in ys),name=f'inventory_{i}')
            # Avoid rounding c_i*y coefficients: c_i is the declared binary64.
            m.addConstr(self.r[i]==s['c']*self.Y[i],name=f'ratio_{i}')
            m.addConstr(gp.quicksum(self.z[i,y] for y in ys)==self.S,name=f'product_mass_{i}')
            for y in ys:
                x,z=self.x[i,y],self.z[i,y]
                m.addConstr(z>=l*x,name=f'product_lx_{i}_{y}')
                m.addConstr(z<=u*x,name=f'product_ux_{i}_{y}')
                m.addConstr(z>=self.S-u*(1-x),name=f'product_Su_{i}_{y}')
                m.addConstr(z<=self.S-l*(1-x),name=f'product_Sl_{i}_{y}')
        m.addConstr(self.S==gp.quicksum(self.r.values()),name='denominator')
        total=gp.quicksum(self.Y.values())
        m.addConstr(total>=scope['Bminus'],name='hard_lower')
        m.addConstr(total<=scope['B'],name='hard_upper')
        self.a=m.addVars(list(combinations([s['i'] for s in ss],2)),lb=0.,name='abs')
        for i,j in self.a:
            m.addConstr(self.a[i,j]>=self.r[i]-self.r[j],name=f'abs_p_{i}_{j}')
            m.addConstr(self.a[i,j]>=self.r[j]-self.r[i],name=f'abs_m_{i}_{j}')
        self.A=gp.quicksum(self.a.values())
        physical=outward(F(n)*F(scope['gamma_U']),True)
        m.addConstr(self.A<=physical*self.S,name='physical_G_upper_outward')
        if total_product:
            product=gp.quicksum(y*self.z[i,y] for i,y in self.z)
            m.addConstr(product>=scope['Bminus']*self.S,name='total_product_lower')
            m.addConstr(product<=scope['B']*self.S,name='total_product_upper')
        self.q=m.addVar(lb=-gp.GRB.INFINITY,name='residual_scaled')
        self.epigraph=[]; m.setObjective(self.q); m.update()

    def close(self):
        if self.model is not None: self.model.dispose()

    def price(self,beta,d,tau,target,cap=60.,warm=(),absolute_gap=1e-7,
              inherited_lower=None,prior_residuals=(),lp_cap=30.,node_limit=None):
        tick=time.perf_counter(); gp=self.gp; ss=self.scope['stations']; scope=self.scope
        beta=F(beta); tau=F(tau); assert beta>=0
        d={k:F(d.get(k,0.)) for k in states(scope)}
        target=Path(target); target.mkdir(parents=True,exist_ok=False)
        dp=unary_dp(scope,d); assert dp is not None
        fallback=beta*F(scope['gamma_L'])+F(dp['exact']); stocks={}
        def consider(Y):
            v=stock_value(scope,Y,beta,d)
            if v['feasible']: stocks[tuple(v['Y'])]=v
        consider(dp['Y'])
        for Y in warm: consider(Y)
        zero=None
        if self.bounds['zero_possible']:
            consider([0]*len(ss)); zero=stocks[tuple([0]*len(ss))]['price']
        calls=[]; positive=fallback; ell=None; lp=None; transformed=[]
        if self.model is not None:
            m=self.model; l,u=map(F,(self.bounds['lower'],self.bounds['upper']))
            anchors={s['i']:(min(d[s['i'],y] for y in s['support'])+max(d[s['i'],y] for y in s['support']))/2 for s in ss}
            centered={k:v-anchors[k[0]] for k,v in d.items()}; anchor=sum(anchors.values(),F(0))
            # Scale the residual envelope, including S and A ranges.
            boundA=F(len(ss))*F(scope['gamma_U'])*u
            magnitude=max(sum(max(abs(centered[s['i'],y]) for y in s['support']) for s in ss)*u,
                          abs(anchor-tau)*u,abs(anchor+beta*F(scope['gamma_L'])-tau)*u,
                          beta/F(len(ss))*boundA,F(1,2**40))
            scale=math.ldexp(1.,math.ceil(math.log2(float(magnitude))))
            cost={k:outward(v/F(scale),False) for k,v in centered.items()}
            s1=outward((anchor+beta*F(scope['gamma_L'])-tau)/F(scale),False)
            s2=outward((anchor-tau)/F(scale),False)
            ac=outward(beta/F(len(ss))/F(scale),False)
            if self.epigraph: m.remove(self.epigraph); m.update()
            W=gp.quicksum(cost[k]*self.z[k] for k in cost)
            self.epigraph=[m.addConstr(self.q>=W+s1*self.S,name='floor_residual'),
                           m.addConstr(self.q>=W+s2*self.S+ac*self.A,name='G_residual')]
            m.update(); structure=semantics(m); m.write(str(target/'model.mps'))
            with gp.read(str(target/'model.mps'),env=self.env) as back: assert semantics(back)==structure
            terms=sum(max(abs(F(cost[s['i'],y])) for y in s['support']) for s in ss)*u
            row_size=max(abs(F(s1)),abs(F(s2)))*u+F(ac)*boundA
            guard=outward(F(1e-6)*(1+terms+row_size),True)
            for r in prior_residuals:
                assert r['scope']==scope and F(r['beta_exact'])==beta and r['d_exact']=={f'{i}:{y}':str(v) for (i,y),v in d.items()}
                if r.get('residual_lower_exact') is not None:
                    v=transport(F(r['residual_lower_exact']),F(r['tau_exact']),tau,l,u)
                    transformed.append(dict(source=r.get('result_path'),tau_exact=r['tau_exact'],transported_lower_exact=str(v)))
                    ell=v if ell is None else max(ell,v)
            rounding={k:str(centered[k]/F(scale)-F(cost[k])) for k in centered}
            assert all(F(v)>=0 for v in rounding.values())
            call=dict(UTC=utc(),scope=scope,beta=float(beta),beta_exact=str(beta),d=keyed(d),d_exact={f'{i}:{y}':str(v) for (i,y),v in d.items()},
                      tau=float(tau),tau_exact=str(tau),positive_S_bounds=[float(l),float(u)],bounds=self.bounds,
                      anchors_exact={str(i):str(v) for i,v in anchors.items()},scale=scale,
                      residual_coefficients=dict(state=keyed(cost),S_floor=s1,S_G=s2,A=ac),
                      state_downward_errors_exact={f'{i}:{y}':v for (i,y),v in rounding.items()},
                      residual_guard_scaled=guard,residual_guard_original=scale*guard,
                      guard_rule='1e-6*(1+sum_station_max_abs_centered_scaled_cost*u+max_abs_S_coefficient*u+abs_A_coefficient*n*gamma_U*u)',
                      transport_policy='outward-down residual epigraph coefficients; c_i*Y_i factored through original binary64 c_i',
                      q_can_be_negative=self.q.LB<-1e90,total_product=self.total_product,
                      full_support=True,matrix_readback=True,model_SHA=sha(target/'model.mps'),
                      Native_vars=m.NumVars,Native_binary=m.NumBinVars,Native_rows=m.NumConstrs,Native_nz=m.NumNZs,
                      Seed=0,Threads=1,cap=float(cap),node_limit=node_limit,absolute_price_gap=absolute_gap)
            write(target/'call.json',call)
            m.Params.Threads=1; m.Params.Seed=0
            m.Params.IntFeasTol=1e-6; m.Params.FeasibilityTol=1e-6; m.Params.OptimalityTol=1e-6
            m.Params.OutputFlag=1; m.Params.LogToConsole=0
            if lp_cap:
                with m.relax() as relaxation:
                    relaxation.Params.TimeLimit=float(lp_cap); relaxation.Params.LogFile=str(target/'lp.log')
                    relaxation.optimize()
                    lp=dict(Status=relaxation.Status,Runtime=relaxation.Runtime,Work=relaxation.Work,
                            objective=relaxation.ObjVal if relaxation.SolCount else None)
                    if relaxation.SolCount: save_gz(target/'lp_solution.json.gz',{v.VarName:v.X for v in relaxation.getVars()})
                write(target/'LP.json',lp)
            candidate=min((v for v in stocks.values() if v['S']>0),key=lambda v:v['price'],default=None)
            if candidate:
                for s,y0 in zip(ss,candidate['Y']):
                    for y in s['support']: self.x[s['i'],y].Start=float(y==y0)
            m.Params.TimeLimit=float(cap); m.Params.NodeLimit=gp.GRB.INFINITY if node_limit is None else float(node_limit)
            m.Params.MIPGap=0.; m.Params.MIPGapAbs=outward(F(absolute_gap)*l/F(scale),False)
            m.Params.PoolSolutions=20; m.Params.LogFile=str(target/'native.log')
            built=time.perf_counter(); m.optimize(); done=time.perf_counter()
            qualified=m.Status in (gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT,gp.GRB.NODE_LIMIT) and math.isfinite(m.ObjBound) and abs(m.ObjBound)<1e90
            if qualified:
                current=F(scale)*(F(m.ObjBound)-F(guard)); ell=current if ell is None else max(ell,current)
            if ell is not None: positive=max(positive,recover(tau,ell,l,u))
            for j in range(m.SolCount):
                m.Params.SolutionNumber=j
                consider([max(s['support'],key=lambda y:self.x[s['i'],y].Xn) for s in ss])
            if m.SolCount: save_gz(target/'solution.json.gz',{v.VarName:v.X for v in m.getVars()})
            calls=[dict(Status=m.Status,Runtime=m.Runtime,Work=m.Work,nodes=m.NodeCount,
                        native_bound=m.ObjBound if qualified else None,native_incumbent=m.ObjVal if m.SolCount else None,
                        bound_status_qualified=qualified,construct_LP_seconds=built-tick,optimize_seconds=done-built,
                        scale=scale,guard_original=scale*guard,positive_lower=outward(positive,False),pool_count=m.SolCount)]
            write(target/'return.json',calls[0])
        lower=min(positive,zero) if zero is not None else positive
        if self.model is None: assert zero is not None; lower=zero
        if inherited_lower is not None: lower=max(lower,F(inherited_lower))
        upper=min((v['price'] for v in stocks.values()),default=None)
        assert upper is None or lower<=upper
        result=dict(scope=scope,beta=float(beta),beta_exact=str(beta),d=keyed(d),d_exact={f'{i}:{y}':str(v) for (i,y),v in d.items()},
                    tau=float(tau),tau_exact=str(tau),lower=outward(lower,False),upper=outward(upper,True) if upper is not None else None,
                    fallback_lower=outward(fallback,False),zero_lower=outward(zero,False) if zero is not None else None,
                    positive_lower=outward(positive,False),residual_lower_exact=str(ell) if ell is not None else None,
                    inherited_lower=inherited_lower,prior_residual_transports=transformed,LP=lp,
                    stocks=[serial_stock(v) for v in stocks.values()],calls=calls,complete_domain=True,
                    target_proved=lower>=tau,target_disproved_by_true_stock=upper is not None and upper<tau,
                    seconds=time.perf_counter()-tick,reason='original_coordinate_target_residual',
                    decision='RESOLVED' if upper is not None and upper-lower<=F(absolute_gap) else 'UNDECIDED',
                    result_path=str(target/'result.json'),upper_is_inventory_price_only=True)
        write(target/'result.json',result); return result
