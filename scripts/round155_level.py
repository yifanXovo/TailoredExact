"""One persistent feasible-selector adjustment with fixed midpoint stages.

Selection is never a hull certificate. Only the unchanged exact original-Q
residual, true current-column minimum, whole-domain price, and complete primal
interfaces can move the retained interval.
"""
from fractions import Fraction as F
from round152_math import h_exact
from round155_loop import (Master, solve, direction, witness, classify_columns,
                           column_usage, support_row, outward)
from round153_lp import primal_record
from round155_common import *


class LevelSelector:
    """Explicit RMP dual, with nonnegative lambda columns eliminated.

    Rows and original variables stay fixed. Each new lambda adds its actual
    written dual inequality. The L1 center is the inherited AP center; no box
    or radius restricts potentials. A complete PStart comes from current Pi/RC.
    """
    def __init__(self, master):
        assert not master.phase and master.m.Status == 2
        self.master = master
        self.gp = master.gp
        self.m = self.gp.Model(env=master.env)
        self.pi = {}; self.lb = {}; self.ub = {}; self.dev = {}; self.seen = set()
        primal = master.m; gp = self.gp; dual = self.m
        self.original = [v for v in primal.getVars() if v.VarName in master.original_names]
        equations = {v.VarName: dual.addConstr(gp.LinExpr() == v.Obj,
                     name=f'dual_original_{j}') for j, v in enumerate(self.original)}
        self.level = dual.addConstr(gp.LinExpr() >= 0, name='nominal_fixed_level')
        dual.update()
        self.row_names = [c.ConstrName for c in primal.getConstrs()]
        for j, c in enumerate(primal.getConstrs()):
            e = primal.getRow(c); coeff = []; rows = []
            for k in range(e.size()):
                name = e.getVar(k).VarName
                if name in equations:
                    coeff.append(e.getCoeff(k)); rows.append(equations[name])
            if c.RHS:
                coeff.append(c.RHS); rows.append(self.level)
            self.pi[c.ConstrName] = dual.addVar(
                lb=0. if c.Sense == '>' else -gp.GRB.INFINITY,
                ub=0. if c.Sense == '<' else gp.GRB.INFINITY,
                column=gp.Column(coeff, rows), name=f'pi_{j}')
        for j, v in enumerate(self.original):
            for side, bound, lower, upper in [('lb', v.LB, 0., gp.GRB.INFINITY),
                                            ('ub', v.UB, -gp.GRB.INFINITY, 0.)]:
                if abs(bound) >= gp.GRB.INFINITY: continue
                coeff = [1.]; rows = [equations[v.VarName]]
                if bound:
                    coeff.append(bound); rows.append(self.level)
                getattr(self, side)[v.VarName] = dual.addVar(
                    lb=lower, ub=upper, column=gp.Column(coeff, rows), name=f'{side}_{j}')
        for s in master.scope['stations']:
            anchor = s['support'][0]
            for y in s['support'][1:]:
                name = f'hull_link_{s["i"]}_{y}'
                center = float(h_exact(s, anchor) - h_exact(s, y))
                dev = dual.addVar(lb=0., obj=1., name=f'dev_{s["i"]}_{y}')
                dual.addConstr(dev >= self.pi[name] - center, name=f'dev_pos_{s["i"]}_{y}')
                dual.addConstr(dev >= center - self.pi[name], name=f'dev_neg_{s["i"]}_{y}')
                self.dev[name] = (dev, center)
        dev = dual.addVar(lb=0., obj=1., name='dev_beta')
        dual.addConstr(dev >= self.pi['hull_gini'] - 1., name='dev_beta_pos')
        dual.addConstr(dev >= 1. - self.pi['hull_gini'], name='dev_beta_neg')
        self.dev['hull_gini'] = (dev, 1.)
        dual.update(); self.sync()
        # Moving a tiny primal RHS into a matrix coefficient can make Native
        # omit it. This occurs only in the nominal selection-level row in the
        # observed model. Preserve the exact discrepancy; the C_Q+a_K gate is
        # still evaluated on every original Q RHS and the true columns.
        nominal_terms = {self.pi[c.ConstrName].VarName:c.RHS for c in primal.getConstrs() if c.RHS}
        for v in self.original:
            if v.VarName in self.lb and v.LB: nominal_terms[self.lb[v.VarName].VarName]=v.LB
            if v.VarName in self.ub and v.UB: nominal_terms[self.ub[v.VarName].VarName]=v.UB
        row=dual.getRow(self.level)
        actual={row.getVar(j).VarName:row.getCoeff(j) for j in range(row.size())}
        assert set(actual)<=set(nominal_terms) and all(value==nominal_terms[name] for name,value in actual.items())
        self.nominal_omissions={name:value for name,value in nominal_terms.items() if name not in actual}
        assert all(abs(value)<1e-13 for value in self.nominal_omissions.values())

    def sync(self):
        p = self.master.m; gp = self.gp
        assert [c.ConstrName for c in p.getConstrs()] == self.row_names
        added = []
        for Y, v in self.master.columns.items():
            if Y in self.seen: continue
            assert v.LB == 0. and v.UB >= gp.GRB.INFINITY and v.Obj == 0.
            col = p.getCol(v)
            e = gp.LinExpr([col.getCoeff(j) for j in range(col.size())],
                          [self.pi[col.getConstr(j).ConstrName] for j in range(col.size())])
            self.m.addConstr(e <= 0., name=f'dual_{v.VarName}')
            self.seen.add(Y); added.append(list(Y))
        self.m.update()
        return added

    def warm_point(self):
        """Native optimal Pi/RC provides a candidate start, never a proof."""
        p = self.master.m; point = {}
        for c in p.getConstrs():
            raw = c.Pi
            value = max(0., raw) if c.Sense == '>' else min(0., raw) if c.Sense == '<' else raw
            point[self.pi[c.ConstrName].VarName] = value
        for v in self.original:
            if v.VarName in self.lb: point[self.lb[v.VarName].VarName] = max(0., v.RC)
            if v.VarName in self.ub: point[self.ub[v.VarName].VarName] = min(0., v.RC)
        for name, (dev, center) in self.dev.items():
            point[dev.VarName] = abs(point[self.pi[name].VarName] - center)
        assert set(point) == {v.VarName for v in self.m.getVars()}
        return point

    def select(self, zeta, target, cap=120., iterations=None, save_model=False):
        start = time.perf_counter(); target = Path(target); target.mkdir(parents=True, exist_ok=False)
        added = self.sync(); m = self.m
        # This cushion is only a numerical candidate-selection aid. Exact C_Q
        # and true a_K below remain the mandatory, unrelaxed level gate.
        nominal = F(zeta) + F(1e-7)
        self.level.RHS = outward(nominal - F(self.master.m.ObjCon), True)
        m.update(); warm = self.warm_point(); warm_check = primal_record(m, warm)
        # The full-PStart crossover itself can exceed2000 iterations on the
        # inherited large Q. Reserve a deterministic model-sized allowance.
        # This does not assert that crossover or L1 optimization must finish.
        iteration_limit = m.NumVars + 2000 if iterations is None else int(iterations)
        m.Params.Threads = 1; m.Params.Seed = 0; m.Params.Method = 0
        m.Params.LPWarmStart = 1; m.Params.IterationLimit = iteration_limit; m.Params.TimeLimit = float(cap)
        m.Params.FeasibilityTol = 1e-8; m.Params.OptimalityTol = 1e-8
        m.Params.OutputFlag = 1; m.Params.LogToConsole = 0; m.Params.LogFile = str(target/'native.log')
        # Discard the obsolete selector basis so LPWarmStart=1 uses the newly
        # supplied current-master point. The model/matrix itself is retained.
        m.reset()
        # Model edits are completed before setting every PStart value.
        m.setAttr('PStart', m.getVars(), [warm[v.VarName] for v in m.getVars()])
        if save_model: m.write(str(target/'model.mps'))
        save_gz(target/'warm_point.json.gz', warm)
        write(target/'call.json', dict(UTC=utc(), zeta_exact=str(zeta), nominal_level_exact=str(nominal),
            nominal_RHS=self.level.RHS, original_constant=self.master.m.ObjCon,
            Seed=0, Threads=1, Method=0, LPWarmStart=1, IterationLimit=iteration_limit, cap=cap,
            iteration_rule='selector_variable_count_plus_2000' if iterations is None else 'explicit_qualification_limit',
            columns=m.NumVars, rows=m.NumConstrs, nonzeros=m.NumNZs, new_stocks=added,
            current_stock_count=len(self.seen), warm_check=warm_check,
            nominal_level_omitted_coefficients_exact={k:str(F(v)) for k,v in self.nominal_omissions.items()},
            model_SHA=sha(target/'model.mps') if save_model else None,
            objective='inherited AP L1 deviation; not a hull bound', no_potential_radius=True))
        tick = time.perf_counter(); m.optimize(); native = time.perf_counter() - tick
        record = dict(Status=m.Status, Runtime=m.Runtime, Work=m.Work, native_seconds=native,
                      iterations=m.IterCount, SolCount=m.SolCount, selected=False)
        selected = None; dr = None
        if m.SolCount:
            point = {v.VarName: v.X for v in m.getVars()}; check = primal_record(m, point)
            save_gz(target/'point.json.gz', point)
            record.update(primal=check, L1_objective=m.ObjVal)
            record['nominal_level_omitted_contribution_exact']=str(sum(
                (F(value)*F(point[name]) for name,value in self.nominal_omissions.items()),F(0)))
            if m.Status in (2, 7, 9) and check['qualified']:
                candidate = {name: point[v.VarName] for name, v in self.pi.items()}
                tick = time.perf_counter()
                dr = direction(self.master, candidate)
                record['certificate_seconds'] = time.perf_counter() - tick
                record['qualified_ceiling_exact'] = str(dr['cq'] + dr['aK'])
                record['ceiling_meets_level'] = dr['cq'] + dr['aK'] >= zeta
                save_gz(target/'candidate_certificate.json.gz', dr['certificate'])
                save_gz(target/'candidate_multipliers.json.gz', candidate)
                if record['ceiling_meets_level']:
                    selected = candidate; record['selected'] = True
        record.update(seconds=time.perf_counter()-start, zeta_exact=str(zeta),
            nonoptimal_feasible_accepted=bool(selected is not None and m.Status != 2),
            no_hull_bound_from_selection_objective=True)
        write(target/'result.json', record)
        return selected, dr if selected is not None else None, record

    def close(self):
        self.m.dispose()


def run(role, label, seconds, previous, price_cap='120'):
    from round100_gurobi_runtime import gp, binding
    from round150_lp import affinity
    from round153_exact_worker import enable
    from round155_oracle import make_oracle
    configure(); affinity(); enable(); assert binding()['sha256'] == DLL_SHA
    gate = read(OUT/'review/level_admission.json')
    assert gate['decision'] == 'ACCEPT' and gate['source_SHA'] == sha(__file__)
    assert gate['loop_SHA'] == sha(ROOT/'scripts/round155_loop.py')
    assert gate['oracle_SHA'] == sha(ROOT/'scripts/round155_oracle.py')
    tick = time.perf_counter(); seconds = float(seconds); price_cap = float(price_cap); tolerance = 1e-4
    initial = read(OUT/'starting_pools.json')[role]; source = Path(previous); prior = read(source)
    qp = Path(initial['Q']); assert sha(qp) == initial['Q_SHA'] == prior['Q_SHA']
    assert prior['scope'] == initial['scope'] and not prior.get('refresh_required', False)
    folder = OUT/'coupled'/f'{role}_{label}'; folder.mkdir(parents=True, exist_ok=False)
    lower, upper = prior['lower'], prior['upper']; scope = prior['scope']; supports = list(prior['supports'])
    zeta = (F(lower)+F(upper))/2; levels = []; records = []; initial_count = len(prior['columns'])
    tracked = {tuple(r['Y']): {k:v for k,v in r.items() if k!='Y'} for r in prior.get('new_column_usage', [])}
    upper_witness = prior.get('upper_witness_source')
    write(folder/'plan.json', dict(UTC=utc(), role=role, label=label, rule='fixed_level_feasible_AP',
        source=str(source), source_SHA=sha(source), Q=str(qp), Q_SHA=sha(qp), scope=scope,
        initial_columns=initial_count, initial_supports=len(supports), inherited_lower=lower, inherited_upper=upper,
        initial_zeta_exact=str(zeta), outer_allowance=seconds, iteration_limit=None, tolerance=tolerance,
        price_cap=price_cap, node_limit=256, price_absolute_gap=1e-7, Seed=0, Threads=1,
        selection='persistent explicit dual; AP L1; feasible limited primal simplex',
        selection_iteration_rule='selector_variable_count_plus_2000', selection_cap=120., target='fixed_midpoint_until_qualified_exit',
        original_Q_variables_free=True, rule_does_not_switch_after_elapsed_seconds=True))
    costs = dict(build=0., RMP=0., selection=0., certificate=0., pricing=0., feedback=0.)
    reason = 'offline_phase_allowance'; refresh = True; iteration = 0; selector = None
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0); env.setParam('Seed',0); env.setParam('Threads',1); env.start()
        with gp.read(str(qp), env=env) as m:
            start = time.perf_counter(); master = Master(m,scope,gp,env)
            for Y in prior['columns']: assert master.add(Y)
            m.update(); save_gz(folder/'Q_bounds.json.gz',dict(bounds=master.bounds,derivations=master.derivations))
            if (source.parent/'last_master.bas').exists(): m.read(str(source.parent/'last_master.bas'))
            oracle = make_oracle(scope,env,'bounded',folder/'oracle_evidence'); costs['build'] += time.perf_counter()-start
            while time.perf_counter()-tick < seconds-price_cap-420:
                step = folder/f'iter{iteration:06}'
                start=time.perf_counter(); rr=solve(master,step/'RMP',save_model=iteration==0); costs['RMP']+=time.perf_counter()-start
                if rr['Status']!=2 or not rr['primal']['qualified']:
                    reason='RMP_status_or_primal_qualification'; break
                refresh=True
                if rr['objective']<upper:
                    upper=rr['objective']; upper_witness=str(step/'primal.json.gz'); witness(master,Path(upper_witness),rr['primal'])
                elif iteration==0: witness(master,step/'primal.json.gz',rr['primal'])
                used=column_usage(master,tracked,label,iteration,step/'new_column_usage.json.gz')
                if F(upper)<zeta:
                    levels.append(dict(zeta_exact=str(zeta), exit='qualified_full_Q_primal_below', iteration=iteration,
                                       lower=lower, upper=upper, witness=upper_witness))
                    zeta=(F(lower)+F(upper))/2
                if upper-lower<=tolerance: reason='requested_hull_accuracy'; break
                if selector is None:
                    start=time.perf_counter(); selector=LevelSelector(master); costs['build']+=time.perf_counter()-start
                start=time.perf_counter()
                selected,dr,sr=selector.select(zeta,step/'selection',save_model=iteration==0)
                spent=time.perf_counter()-start; certificate_seconds=sr.get('certificate_seconds',0.)
                costs['selection']+=spent-certificate_seconds; costs['certificate']+=certificate_seconds
                if selected is None:
                    reason='no_qualified_feasible_level_candidate'; break
                beta,pi,d,aK,cq=(dr[k] for k in ('beta','pi','d','aK','cq')); tau=zeta-cq
                assert cq+aK>=zeta and tau<=aK
                warm=sorted(dr['prices'],key=lambda Y:(dr['prices'][Y],Y))[:4]; cert=dr['certificate']
                frozen=dict(role=role,scope=scope,Q_SHA=prior['Q_SHA'],beta=float(beta),
                    d_exact={f'{i}:{y}':str(v) for (i,y),v in d.items()}, C_Q_exact=str(cq),a_K_exact=str(aK),
                    tau_exact=str(tau),zeta_exact=str(zeta),initial_stocks=[list(Y) for Y in warm],
                    initial_true_price_upper_exact=str(min(dr['prices'].values())),inherited_price_lower_exact=str(dr['fallback']),
                    columns_before=len(master.columns),inherited_hull_lower=lower,inherited_hull_upper=upper,
                    selection_method='persistent_feasible_AP_fixed_level',selection_status=sr['Status'],
                    selection_result_SHA=sha(step/'selection/result.json'),frozen_before_price=True)
                write(step/'direction.json',frozen)
                start=time.perf_counter()
                price=oracle.price(beta,d,tau,step/'pricing',cap=price_cap,warm=warm,lp_cap=0.,absolute_gap=1e-7,
                    inherited_lower=outward(dr['fallback'],False),node_limit=256)
                costs['pricing']+=time.perf_counter()-start
                lm=F(price['lower']); fixed=cq+min(aK,lm); lower=max(lower,outward(fixed,False))
                cert.update(pricing_lower=price['lower'],pricing_lower_exact=str(lm),D_K_exact=str(cq+aK),
                    delta_exact=str(max(F(0),aK-lm)),coupled_lower=outward(fixed,False))
                save_gz(step/'certificate.json.gz',cert)
                start=time.perf_counter(); row,correction=support_row(scope,beta,pi,price['lower'],len(supports))
                row['name']=f'r155_coupled_support_{len(supports):06}'
                support=dict(row=row,transport_exact=correction,price_path=(step/'pricing/result.json').relative_to(ROOT).as_posix(),
                    beta=float(beta),direction_SHA=sha(step/'direction.json'))
                supports.append(support); write(step/'support.json',support)
                feedback,added=classify_columns(master,price['stocks'],beta,d,aK,tau)
                save_gz(step/'column_feedback.json.gz',feedback)
                for Y in added: tracked[Y]=dict(origin_phase=label,added_iteration=iteration,used_iterations=0,
                    maximum_weight=0.,first_used_iteration=None,first_used_phase=None)
                m.update(); refresh=not bool(added); costs['feedback']+=time.perf_counter()-start
                negatives=sum(r['new'] and r['negative'] for r in feedback)
                true_upper=min([min(dr['prices'].values())]+[F(v['price_exact']) for v in price['stocks']])
                rec=dict(iteration=iteration,RMP_objective=rr['objective'],lower=lower,upper=upper,gap=upper-lower,
                    C_Q=float(cq),a_K=float(aK),beta=float(beta),target_hull=float(zeta),target_price=float(tau),
                    price_lower=price['lower'],price_upper=outward(true_upper,True),target_proved=lm>=tau,
                    target_disproved=true_upper<tau,columns=len(master.columns),supports=len(supports),
                    added=len(added),added_negative=negatives,duplicate_returns=sum(not r['new'] for r in feedback),
                    new_columns_used=len(used),new_column_total_weight=math.fsum(r['weight'] for r in used),
                    pricing_seconds=price['seconds'],selection_seconds=spent-certificate_seconds,selection_LP_Optimize=1,
                    selection_status=sr['Status'],nonoptimal_feasible_accepted=sr['nonoptimal_feasible_accepted'],
                    RMP_seconds=rr['native_seconds'],cumulative_costs=dict(costs),elapsed_seconds=time.perf_counter()-tick,
                    Native_status=price['calls'][0]['Status'] if price['calls'] else None,rule='fixed_level_feasible_AP')
                records.append(rec);write(step/'result.json',rec)
                write(folder/'status.json',dict(role=role,label=label,decision='RUNNING',**rec));print(json.dumps(rec),flush=True)
                iteration+=1
                if lm>=tau:
                    levels.append(dict(zeta_exact=str(zeta),exit='qualified_whole_price_lower',iteration=iteration-1,
                        lower=lower,upper=upper,direction=str(step/'direction.json'),price=str(step/'pricing/result.json')))
                    zeta=(F(lower)+F(upper))/2
                if upper-lower<=tolerance:reason='requested_hull_accuracy';break
                if lm<tau and not added:reason='undecided_price_no_new_column';break
                if lm<tau and not negatives:reason='no_new_true_negative_column';break
                if (folder/'checkpoint_requested.json').exists():reason='reviewed_checkpoint';break
            if not refresh:
                start=time.perf_counter();rr=solve(master,folder/'final_RMP',cap=180.,save_model=True);costs['RMP']+=time.perf_counter()-start
                if rr['Status']==2 and rr['primal']['qualified']:
                    refresh=True;witness(master,folder/'final_primal.json.gz',rr['primal'])
                    if rr['objective']<upper:upper=rr['objective'];upper_witness=str(folder/'final_primal.json.gz')
                    column_usage(master,tracked,label,iteration,folder/'final_column_usage.json.gz')
                    if F(upper)<zeta:
                        levels.append(dict(zeta_exact=str(zeta),exit='qualified_full_Q_primal_below',iteration=iteration,
                            lower=lower,upper=upper,witness=upper_witness));zeta=(F(lower)+F(upper))/2
            m.write(str(folder/'last_master.mps'))
            if m.Status==2:m.write(str(folder/'last_master.bas'))
            if oracle.model is not None:oracle.model.write(str(folder/'last_price.mps'))
            oracle.close()
            if selector is not None:
                selector.sync();selector.m.write(str(folder/'last_selection.mps'));selector.close()
            costs['other_python_and_output']=max(0.,time.perf_counter()-tick-sum(costs.values()))
            result=dict(role=role,label=label,scope=scope,Q_SHA=prior['Q_SHA'],lower=lower,upper=upper,gap=upper-lower,
                columns=[list(Y) for Y in master.columns],supports=supports,records=records,prior_results=[str(source)],
                refresh_required=not refresh,upper_witness_source=upper_witness,decision=reason,
                inherited_upper_record=str(source),seconds=time.perf_counter()-tick,costs=costs,initial_columns=initial_count,
                rule='fixed_level_feasible_AP',original_variables_free=True,upper_is_not_physical=True,
                resolved_levels=levels,unresolved_level_exact=str(zeta),
                new_column_usage=[dict(Y=list(Y),**meta) for Y,meta in tracked.items()])
            write(folder/'result.json',result)
    print(json.dumps({k:result[k] for k in ('role','label','lower','upper','gap','decision','seconds','resolved_levels')}),flush=True)


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
