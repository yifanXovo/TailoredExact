"""Fixed beta=1,d=h residual, optionally restricted by its own inventory upper.

The inherited signed state-product/conditional-S model is unchanged. Only
the aggregate actual-Native cost upper changes. Bounds on the restricted
phi are restored to the original domain by min(U, lower), after residual
conversion. No restricted residual minimum is equated to the original one.
"""
from fractions import Fraction as F
from itertools import combinations
from round143_math import outward
from round152_math import states, unary_dp, h_exact
from round153_pricing import stock_value, serial_stock, keyed
from round154_strengthened import StrengthenedResidualOracle
from round155_oracle import capture
from round156_common import *


def native_row(model, name):
    c=model.getConstrByName(name);e=model.getRow(c)
    return dict(sense=c.Sense,rhs=c.RHS,terms={e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())})


class InventoryResidual(StrengthenedResidualOracle):
    def __init__(self,scope,env,evidence_root,condition_upper):
        super().__init__(scope,env)
        self.evidence_root=Path(evidence_root)
        self.condition_upper=bool(condition_upper)
        self.record_event=lambda row:None

    def price(self,tau,upper,warm,target,node_limit,deadline,absolute_gap=1e-4,lp_cap=0.):
        tick=time.perf_counter();gp=self.gp;scope=self.scope;ss=scope['stations'];n=len(ss)
        tau,upper=F(tau),F(upper);assert tau<upper
        target=Path(target);target.mkdir(parents=True,exist_ok=False)
        d={(s['i'],y):h_exact(s,y) for s in ss for y in s['support']}
        dp_start=time.perf_counter();dp=unary_dp(scope,d);assert dp
        fallback=F(scope['gamma_L'])+F(dp['exact']);stocks={}
        def consider(Y):
            v=stock_value(scope,Y,1.,d)
            if v['feasible']:stocks[tuple(v['Y'])]=v
            return v
        for Y in warm:consider(Y)
        assert stocks and min(v['price'] for v in stocks.values())<=upper,'upper needs its own legal witness'
        consider(dp['Y']);zero=None
        if self.bounds['zero_possible']:zero=consider([0]*n)['price']
        initial_dp_seconds=time.perf_counter()-dp_start
        if self.model is None:
            assert zero is not None
            result=dict(lower=outward(zero,False),upper=outward(min(v['price'] for v in stocks.values()),True),
                calls=[],stocks=[serial_stock(v) for v in stocks.values()],scope=scope,zero_only=True,
                seconds=time.perf_counter()-tick,complete_domain=True)
            write(target/'result.json',result);return result
        m=self.model;l,u=map(F,(self.bounds['lower'],self.bounds['upper']))
        anchors={s['i']:(min(d[s['i'],y] for y in s['support'])+max(d[s['i'],y] for y in s['support']))/2 for s in ss}
        anchor=sum(anchors.values(),F(0));centered={k:v-anchors[k[0]] for k,v in d.items()}
        boundA=F(n)*F(scope['gamma_U'])*u
        magnitude=max(sum(max(abs(centered[s['i'],y]) for y in s['support']) for s in ss)*u,
            abs(anchor-tau)*u,abs(anchor+F(scope['gamma_L'])-tau)*u,boundA/n,F(1,2**40))
        scale=math.ldexp(1.,math.ceil(math.log2(float(magnitude))))
        intended={k:outward(v/F(scale),False) for k,v in centered.items()}
        if self.cost_rows:m.remove(self.cost_rows)
        if self.epigraph:m.remove(self.epigraph)
        m.update()
        definition=m.addConstr(self.Dcost==gp.quicksum(intended[k]*self.x[k] for k in intended),name='hard_cost_D_definition')
        m.update();dr=native_row(m,'hard_cost_D_definition')
        actual={k:-dr['terms'].get(f'x[{k[0]},{k[1]}]',0.) for k in intended}
        actualF={k:F(v) for k,v in actual.items()}
        dp_start=time.perf_counter()
        lo=F(unary_dp(scope,actualF)['exact'])
        hi=-F(unary_dp(scope,{k:-v for k,v in actualF.items()})['exact'])
        cost_dp_seconds=time.perf_counter()-dp_start
        eplus=sum((max([F(0)]+[actualF[s['i'],y]-centered[s['i'],y]/F(scale) for y in s['support']]) for s in ss),F(0))
        cap_exact=(upper-F(scope['gamma_L'])-anchor)/F(scale)+eplus
        a=outward(lo,False);old_b=outward(hi,True)
        b=min(old_b,outward(cap_exact,True)) if self.condition_upper else old_b
        assert a<=b
        self.Dcost.LB=a;self.Dcost.UB=b
        rows=[definition,m.addConstr(self.Wcost==gp.quicksum(actual[k]*self.z[k] for k in actual),name='hard_cost_W_definition')]
        for name,slope,endpoint,sense in [('ll',float(l),a,'>'),('uu',float(u),b,'>'),('ul',float(u),a,'<'),('lu',float(l),b,'<')]:
            expr=self.Wcost-slope*self.Dcost-endpoint*self.S
            rhs=outward(-F(slope)*F(endpoint),sense=='<')
            rows.append(m.addConstr(expr>=rhs if sense=='>' else expr<=rhs,name='tight_DP_cost_product_'+name))
        self.cost_rows=rows
        s1=outward((anchor+F(scope['gamma_L'])-tau)/F(scale),False)
        s2=outward((anchor-tau)/F(scale),False);ac=outward(F(1,n)/F(scale),False)
        W=gp.quicksum(actual[k]*self.z[k] for k in actual)
        self.epigraph=[m.addConstr(self.q>=W+s1*self.S,name='floor_residual'),
            m.addConstr(self.q>=W+s2*self.S+ac*self.A,name='G_residual')]
        m.update()
        floor_row=native_row(m,'floor_residual');g_row=native_row(m,'G_residual')
        actual_s1=-F(floor_row['terms'].get('S',0.));actual_s2=-F(g_row['terms'].get('S',0.))
        actual_ac=-F(g_row['terms'].get(f'abs[{ss[0]["i"]},{ss[1]["i"]}]',0.))
        assert all(-F(g_row['terms'].get(f'abs[{i},{j}]',0.))==actual_ac for i,j in combinations([s['i'] for s in ss],2))
        assert all(-F(row['terms'].get(f'Sx[{i},{y}]',0.))==actualF[i,y] for row in (floor_row,g_row) for i,y in actualF)
        eps_state=u*eplus
        eps_floor=eps_state+u*max(F(0),actual_s1-(anchor+F(scope['gamma_L'])-tau)/F(scale))
        eps_g=eps_state+u*max(F(0),actual_s2-(anchor-tau)/F(scale))+boundA*max(F(0),actual_ac-F(1,n)/F(scale))
        epsilon=max(eps_floor,eps_g)
        terms=sum(max(abs(F(intended[s['i'],y])) for y in s['support']) for s in ss)*u
        row_size=max(abs(F(s1)),abs(F(s2)))*u+F(ac)*boundA
        guard=outward(F(1e-6)*(1+terms+row_size),True)
        matrix=capture(self,m,target)
        witness=min(stocks.values(),key=lambda v:v['price'])
        witness_D=sum((actualF[s['i'],y] for s,y in zip(ss,witness['Y'])),F(0))
        assert F(a)<=witness_D<=F(b),'own inventory witness excluded'
        call=dict(UTC=utc(),scope=scope,beta_exact='1',d_exact={f'{i}:{y}':str(v) for (i,y),v in d.items()},
            tau_exact=str(tau),inventory_upper_exact=str(upper),condition_upper=self.condition_upper,
            anchors_exact={str(i):str(v) for i,v in anchors.items()},anchor_sum_exact=str(anchor),scale=scale,
            intended_costs=keyed(intended),actual_costs=keyed(actual),actual_cost_DP_exact=[str(lo),str(hi)],
            eplus_exact=str(eplus),cap_actual_D_exact=str(cap_exact),cost_bounds=[a,b],original_cost_upper=old_b,
            positive_S_bounds=[float(l),float(u)],residual_guard_scaled=guard,
            additional_scaled_error_exact=str(epsilon),original_guard_retained=True,
            q_can_be_negative=self.q.LB<-1e90,full_original_support=True,
            preserved_objective_not_residual_minimum=True,restoration='min(inventory_upper, restricted_phi_lower)',
            matrix_evidence=matrix,witness=serial_stock(witness),witness_actual_D_exact=str(witness_D),
            conditional_S_bounds=self.conditional,conditional_construct_seconds=self.tighten_construct_seconds,
            initial_dp_seconds=initial_dp_seconds,cost_dp_seconds=cost_dp_seconds,
            absolute_gap=absolute_gap,node_limit=node_limit,Seed=0,Threads=1)
        write(target/'call.json',call)
        def bound_value(native):
            ell=F(scale)*(F(native)-F(guard)-epsilon)
            restricted=max(fallback,tau+ell/(u if ell>=0 else l))
            positive=min(upper,restricted) if self.condition_upper else restricted
            whole=min(positive,zero) if zero is not None else positive
            return ell,restricted,whole
        m.Params.Threads=1;m.Params.Seed=0
        m.Params.FeasibilityTol=1e-6;m.Params.IntFeasTol=1e-6;m.Params.OptimalityTol=1e-6
        m.Params.OutputFlag=1;m.Params.LogToConsole=0
        lp=None
        if lp_cap:
            with m.relax() as relaxation:
                relaxation.Params.TimeLimit=min(float(lp_cap),max(0.,deadline-time.perf_counter()))
                relaxation.Params.LogFile=str(target/'lp.log');relaxation.optimize()
                lp=dict(Status=relaxation.Status,Runtime=relaxation.Runtime,Work=relaxation.Work,
                    objective=relaxation.ObjVal if relaxation.SolCount else None)
                if relaxation.Status==gp.GRB.OPTIMAL:lp['converted_guarded_lower']=outward(bound_value(relaxation.ObjVal)[2],False)
            write(target/'LP.json',lp)
        positive_stocks=[v for v in stocks.values() if v['S']>0 and sum((actualF[s['i'],y] for s,y in zip(ss,v['Y'])),F(0))<=F(b)]
        if positive_stocks:
            chosen=min(positive_stocks,key=lambda v:v['price'])
            for s,y0 in zip(ss,chosen['Y']):
                for y in s['support']:self.x[s['i'],y].Start=float(y==y0)
        m.Params.TimeLimit=max(0.,deadline-time.perf_counter());m.Params.NodeLimit=float(node_limit)
        m.Params.MIPGap=0.;m.Params.MIPGapAbs=outward(F(absolute_gap)*l/F(scale),False)
        m.Params.BestBdStop=outward(F(guard)+epsilon,True);m.Params.BestObjStop=-gp.GRB.INFINITY
        m.Params.PoolSolutions=20;m.Params.LogFile=str(target/'native.log')
        callback_errors=[];counterexample=[False];last=[-1.,None]
        def observe(model,where):
            try:
                if where==gp.GRB.Callback.MIPSOL:
                    xx=model.cbGetSolution(self.x)
                    Y=[max(s['support'],key=lambda y:xx[s['i'],y]) for s in ss]
                    v=consider(Y)
                    if v['feasible']:
                        self.record_event(dict(kind='stock',Y=v['Y'],price_exact=str(v['price']),
                            price=outward(v['price'],True),nodes=model.cbGet(gp.GRB.Callback.MIPSOL_NODCNT)))
                        if v['price']<tau:
                            counterexample[0]=True;model.terminate()
                elif where==gp.GRB.Callback.MIP:
                    bound=model.cbGet(gp.GRB.Callback.MIP_OBJBND);now=time.perf_counter()
                    if math.isfinite(bound) and abs(bound)<1e90 and (bound!=last[1] or now-last[0]>=5.):
                        self.record_event(dict(kind='bound',native_bound=bound,lower=outward(bound_value(bound)[2],False),
                            nodes=model.cbGet(gp.GRB.Callback.MIP_NODCNT),work=model.cbGet(gp.GRB.Callback.WORK)))
                        last[:]=[now,bound]
            except BaseException as error:
                callback_errors.append(repr(error));model.terminate()
        built=time.perf_counter();m.optimize(observe);done=time.perf_counter()
        if callback_errors:raise RuntimeError('residual_callback_failed:'+str(callback_errors))
        accepted=m.Status in (gp.GRB.OPTIMAL,gp.GRB.NODE_LIMIT,gp.GRB.TIME_LIMIT,gp.GRB.USER_OBJ_LIMIT) or (m.Status==gp.GRB.INTERRUPTED and counterexample[0])
        qualified=accepted and math.isfinite(m.ObjBound) and abs(m.ObjBound)<1e90
        ell,restricted,lower=bound_value(m.ObjBound) if qualified else (None,fallback,fallback)
        for j in range(m.SolCount):
            m.Params.SolutionNumber=j
            consider([max(s['support'],key=lambda y:self.x[s['i'],y].Xn) for s in ss])
        best=min(v['price'] for v in stocks.values());assert lower<=best
        if m.SolCount:save_gz(target/'solution.json.gz',{v.VarName:v.X for v in m.getVars()})
        result=dict(scope=scope,tau_exact=str(tau),lower=outward(lower,False),lower_exact=str(lower),
            upper=outward(best,True),upper_exact=str(best),stocks=[serial_stock(v) for v in stocks.values()],
            residual_lower_exact=str(ell) if ell is not None else None,restricted_phi_lower_exact=str(restricted),
            complete_domain=True,condition_upper=self.condition_upper,inventory_upper_used=float(upper),
            target_proved=lower>=tau,target_disproved=best<tau,zero_exact=str(zero) if zero is not None else None,
            fallback_exact=str(fallback),LP=lp,global_deadline_stop=m.Status==gp.GRB.TIME_LIMIT,
            calls=[dict(Status=m.Status,Runtime=m.Runtime,Work=m.Work,nodes=m.NodeCount,
                native_bound=m.ObjBound if qualified else None,native_incumbent=m.ObjVal if m.SolCount else None,
                bound_status_qualified=qualified,counterexample_stop=counterexample[0],
                construct_DP_LP_seconds=built-tick,optimize_seconds=done-built)],
            seconds=time.perf_counter()-tick,upper_is_inventory_only=True)
        write(target/'result.json',result);return result
