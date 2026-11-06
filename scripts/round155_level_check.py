"""Targeted algebra/readback checks for the one feasible-level adjustment."""
from fractions import Fraction as F
from round152_qualify import scope
from round152_math import h_exact
from round153_audit import exact_matrix, independent_residual
from round153_pricing import stock_value, serial_stock
from round143_lp import semantics
from round155_level import LevelSelector
from round155_loop import Master, solve, classify_columns, witness
from round155_common import *


def matrix_check(master, actual, nominal_rhs):
    """Re-derive the compact dual from every actual primal coefficient."""
    p = master.m; gp = master.gp; pv = p.getVars(); pc = p.getConstrs()
    pi = {c.ConstrName: f'pi_{j}' for j,c in enumerate(pc)}
    original = [v for v in pv if v.VarName in master.original_names]
    rows = {}; variables = {}
    for c in pc:
        variables[pi[c.ConstrName]] = (0. if c.Sense=='>' else -gp.GRB.INFINITY,
                                      0. if c.Sense=='<' else gp.GRB.INFINITY, 0.)
    level_terms = {pi[c.ConstrName]: F(c.RHS) for c in pc if c.RHS}
    for j,v in enumerate(original):
        col = p.getCol(v)
        terms = {pi[col.getConstr(k).ConstrName]: F(col.getCoeff(k)) for k in range(col.size())}
        for side,bound in [('lb',v.LB),('ub',v.UB)]:
            if abs(bound)>=gp.GRB.INFINITY: continue
            name=f'{side}_{j}'; terms[name]=F(1)
            variables[name]=(0.,gp.GRB.INFINITY,0.) if side=='lb' else (-gp.GRB.INFINITY,0.,0.)
            if bound: level_terms[name]=F(bound)
        rows[f'dual_original_{j}']=('=',F(v.Obj),terms)
    for Y,v in master.columns.items():
        col=p.getCol(v)
        terms={pi[col.getConstr(k).ConstrName]:F(col.getCoeff(k)) for k in range(col.size())}
        assert v.LB==0. and v.UB>=gp.GRB.INFINITY and v.Obj==0.
        rows[f'dual_{v.VarName}']=('<',F(0),terms)
    rows['nominal_fixed_level']=('>',F(nominal_rhs),level_terms)
    centers=[]
    for s in master.scope['stations']:
        for y in s['support'][1:]:
            center=float(h_exact(s,s['support'][0])-h_exact(s,y))
            centers.append((f'dev_{s["i"]}_{y}',pi[f'hull_link_{s["i"]}_{y}'],center,
                            f'dev_pos_{s["i"]}_{y}',f'dev_neg_{s["i"]}_{y}'))
    centers.append(('dev_beta',pi['hull_gini'],1.,'dev_beta_pos','dev_beta_neg'))
    for dev,mult,center,pos,neg in centers:
        variables[dev]=(0.,gp.GRB.INFINITY,1.)
        rows[pos]=('>',-F(center),{dev:F(1),mult:F(-1)})
        rows[neg]=('>',F(center),{dev:F(1),mult:F(1)})
    # Gurobi accepts its 1e100 infinity sentinel but returns IEEE infinities
    # on model readback. Normalize only these nonfinite-bound representations.
    def canon(item):
        lo,hi,obj=item
        return (-math.inf if lo<=-gp.GRB.INFINITY else lo,
                math.inf if hi>=gp.GRB.INFINITY else hi,obj)
    av={v.VarName:canon((v.LB,v.UB,v.Obj)) for v in actual.getVars()}
    assert av=={name:canon(value) for name,value in variables.items()} and actual.ModelSense==1 and actual.ObjCon==0.
    ar={}
    for c in actual.getConstrs():
        e=actual.getRow(c)
        ar[c.ConstrName]=(c.Sense,F(c.RHS),{e.getVar(k).VarName:F(e.getCoeff(k)) for k in range(e.size())})
    # The nominal level is only a search aid. Preserve and identify Native's
    # actually omitted tiny RHS-as-coefficient terms, exclusively on this row;
    # all original-dual-domain equations and lambda inequalities remain exact.
    name='nominal_fixed_level';omissions={}
    for key,value in list(rows[name][2].items()):
        if key not in ar[name][2]:
            assert abs(value)<F(1e-13),(key,str(value),'unexpected omitted coefficient')
            omissions[key]=str(value);del rows[name][2][key]
    if len(ar)!=actual.NumConstrs or ar!=rows:
        differing=[]
        for name in sorted(set(ar)&set(rows)):
            if ar[name]==rows[name]:continue
            a,b=ar[name],rows[name]
            differing.append(dict(row=name,actual_sense_rhs=(a[0],str(a[1])),expected_sense_rhs=(b[0],str(b[1])),
                terms=[(k,str(a[2].get(k)),str(b[2].get(k))) for k in sorted(set(a[2])|set(b[2])) if a[2].get(k)!=b[2].get(k)][:8]))
            if len(differing)>=5:break
        raise AssertionError(dict(missing=sorted(set(rows)-set(ar))[:5],extra=sorted(set(ar)-set(rows))[:5],differing=differing))
    return dict(exact_dual_domain_transpose_and_all_bounds=True,original_variables=len(original),
                original_rows=len(pc),stock_constraints=len(master.columns),selector_variables=len(av),selector_rows=len(ar),
                nominal_level_omitted_coefficients_exact=omissions,exact_CQ_true_column_level_gate_still_required=True)


def run(label='level_interfaces_v1'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_exact_worker import enable
    configure();affinity();enable();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    gate=read(OUT/'review/loop_admission.json')
    assert gate['source_SHA']==sha(ROOT/'scripts/round155_loop.py')
    assert gate['oracle_SHA']==sha(ROOT/'scripts/round155_oracle.py')
    domain=scope([1.,1.],[[0,1],[0,1]],1,2,0.,1.); legal=[(0,1),(1,0),(1,1)]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.Model(env=env) as m:
            m.addVar(lb=0.,ub=1.,obj=1.,name='G');x={}
            for s in domain['stations']:
                for y in s['support']:
                    x[s['i'],y]=m.addVar(lb=0.,ub=1.,obj=(.2 if s['i']==1 else .3)*y,name=f'state_{s["i"]}_{y}')
                m.addConstr(gp.quicksum(x[s['i'],y] for y in s['support'])==1,name=f'onehot_{s["i"]}')
            m.addConstr(x[1,1]+x[2,1]>=1,name='total_lower');m.update()
            original=exact_matrix(m);m.write(str(target/'original_Q.mps'))
            master=Master(m,domain,gp,env);master.add((1,0));master.add((0,1));m.update()
            before=solve(master,target/'before',save_model=True)
            assert before['Status']==2 and before['primal']['qualified']
            selector=LevelSelector(master);zeta=F(.6)
            # The zero-iteration case tests the real limited-status interface;
            # it is not assumed to return a feasible point on every Gurobi build.
            selected,dr,limited=selector.select(zeta,target/'limited',iterations=0,save_model=True)
            if selected is not None:
                assert dr['cq']+dr['aK']>=zeta and limited['primal']['qualified']
            facts.append(dict(case='actual_zero_iteration_return',Status=limited['Status'],SolCount=limited['SolCount'],
                accepted=limited['selected'],nonoptimal_feasible_accepted=limited['nonoptimal_feasible_accepted']))
            selected,dr,sr=selector.select(zeta,target/'selected',save_model=True)
            assert selected is not None and sr['primal']['qualified'] and dr['cq']+dr['aK']>=zeta
            assert sr['Status'] in (2,7,9)
            call=read(target/'selected/call.json')
            with gp.read(str(target/'selected/model.mps'),env=env) as actual:
                assert semantics(actual)==semantics(selector.m)
                checked=matrix_check(master,actual,call['nominal_RHS'])
            cq=independent_residual(original,master.bounds,dr['certificate'],domain)
            assert cq==dr['cq']
            prices=[stock_value(domain,Y,dr['beta'],dr['d']) for Y in legal]
            counter=min(prices,key=lambda v:v['price']);tau=zeta-cq
            assert counter['price']<tau<=dr['aK'] and tuple(counter['Y']) not in master.columns
            feedback,added=classify_columns(master,[serial_stock(counter)],dr['beta'],dr['d'],dr['aK'],tau)
            assert added==[(1,1)] and feedback[0]['negative'] and zeta==F(.6)
            after=solve(master,target/'after',save_model=True)
            assert after['Status']==2 and after['primal']['qualified'] and F(after['objective'])<zeta
            witness(master,target/'after_primal.json.gz',after['primal'])
            facts.append(dict(case='fixed_level_counterexample_then_complete_primal_exit',level_exact=str(zeta),
                corrected_ceiling_exact=str(cq+dr['aK']),counterexample_price_exact=str(counter['price']),
                tau_exact=str(tau),added=added,before=before['objective'],after=after['objective'],
                subsequent_weight=master.columns[1,1].X,matrix=checked,level_changed_on_counterexample=False))
            # Reuse this selector and append the new lambda inequality. The
            # enumerated full price independently exercises the lower exit.
            lower_level=F(.49)
            selected,dr,sr=selector.select(lower_level,target/'complete',save_model=True)
            assert selected is not None
            exact=min(stock_value(domain,Y,dr['beta'],dr['d'])['price'] for Y in legal)
            cq=independent_residual(original,master.bounds,dr['certificate'],domain)
            assert exact>=lower_level-cq and cq+min(dr['aK'],exact)>=lower_level
            assert len(selector.seen)==3
            with gp.read(str(target/'complete/model.mps'),env=env) as actual:
                checked=matrix_check(master,actual,read(target/'complete/call.json')['nominal_RHS'])
            duplicate=serial_stock(stock_value(domain,(1,1),dr['beta'],dr['d']))
            rows,added=classify_columns(master,[duplicate],dr['beta'],dr['d'],dr['aK'],lower_level-cq)
            assert not added and not rows[0]['new']
            facts.append(dict(case='full_enumeration_lower_exit_and_persistent_new_column',level_exact=str(lower_level),
                original_Q_CQ_exact=str(cq),full_price_exact=str(exact),qualified_lower_exact=str(cq+min(dr['aK'],exact)),
                duplicate_progress=0,matrix=checked))
            rejected,unused,bad=selector.select(F(.8),target/'unavailable',save_model=True)
            assert rejected is None and not bad['selected']
            facts.append(dict(case='unavailable_level_not_a_hull_bound',Status=bad['Status'],
                selector_return_used_as_hull_bound=False,upper_exists_only_from_saved_complete_primal=True))
            selector.close()
    result=dict(PASS=True,facts=facts,source_SHA=sha(ROOT/'scripts/round155_level.py'),
        loop_SHA=sha(ROOT/'scripts/round155_loop.py'),oracle_SHA=sha(ROOT/'scripts/round155_oracle.py'),checker_SHA=sha(__file__),
        inherited_interface_gate_SHA=sha(OUT/'review/loop_admission.json'),
        review='independent transpose/bounds reconstruction, enumeration, original-Q arithmetic and saved primal',
        nonimplementer_agent_review=False,no_pricing_or_production_formulation_change=True)
    write(target/'result.json',result);print(json.dumps(dict(PASS=True,checks=len(facts))),flush=True)


def admit(label='level_interfaces_v1'):
    path=OUT/'qualification'/label/'result.json';r=read(path)
    assert r['PASS'] and r['source_SHA']==sha(ROOT/'scripts/round155_level.py')
    assert r['loop_SHA']==sha(ROOT/'scripts/round155_loop.py') and r['oracle_SHA']==sha(ROOT/'scripts/round155_oracle.py')
    write(OUT/'review/level_admission.json',dict(decision='ACCEPT',source_SHA=r['source_SHA'],loop_SHA=r['loop_SHA'],
        oracle_SHA=r['oracle_SHA'],qualification_SHA=sha(path),review=r['review'],nonimplementer_agent_review=False,
        true_CQ_and_aK_gate=True,fixed_level_until_qualified_price_or_full_primal_exit=True,
        unchanged_full_Q_and_price_domain=True,selection_objective_is_never_a_bound=True,
        mathematical_readback='review/level_adjustment.md'))


def actual_initial(label,phase):
    """Read the saved actual large initial selector; no Optimize or model rebuild."""
    from types import SimpleNamespace
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_lp import primal_record
    configure();affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    folder=OUT/'coupled'/phase;plan=read(folder/'plan.json');prior=read(plan['source'])
    selected=folder/'iter000000/selection';call=read(selected/'call.json')
    assert sha(plan['source'])==plan['source_SHA'] and sha(plan['Q'])==plan['Q_SHA']
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(plan['Q'],env=env) as q:
            names={v.VarName for v in q.getVars()}
        with gp.read(str(folder/'iter000000/RMP/model.mps'),env=env) as m, gp.read(str(selected/'model.mps'),env=env) as d:
            master=SimpleNamespace(m=m,gp=gp,original_names=names,scope=plan['scope'],
                columns={tuple(Y):m.getVarByName(f'hull_lambda_{j:05}') for j,Y in enumerate(prior['columns'])})
            assert all(v is not None for v in master.columns.values())
            matrix=matrix_check(master,d,call['nominal_RHS'])
            warm=primal_record(d,load_gz(selected/'warm_point.json.gz'))
            assert warm['qualified'] and abs(warm['constraints']-call['warm_check']['constraints'])<1e-12
            point=None
            if (selected/'point.json.gz').exists():
                point=primal_record(d,load_gz(selected/'point.json.gz'))
                returned=read(selected/'result.json')
                assert point['qualified']==returned['primal']['qualified']
    result=dict(PASS=True,phase=phase,matrix=matrix,warm=warm,candidate=point,
        model_SHA=sha(selected/'model.mps'),call_SHA=sha(selected/'call.json'),
        result_SHA=sha(folder/'result.json'),Optimize=0,source_SHA=sha(__file__),nonimplementer_agent_review=False)
    write(target/'result.json',result);print(json.dumps(dict(PASS=True,phase=phase,Optimize=0,matrix=matrix)),flush=True)


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
