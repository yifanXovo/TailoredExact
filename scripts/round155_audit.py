"""Finite independent arithmetic, incremental-evidence and lifecycle readback.

Uses no Optimize, compiler or producer. Lower-improving directions receive
complete current-column minima; all directions receive Q and price arithmetic.
"""
from fractions import Fraction as F
from copy import deepcopy
import inspect, types
from round143_math import outward
from round152_math import states,s_bounds,unary_dp
from round153_audit import exact_matrix,replay_q_bounds,independent_residual,witnesses
from round153_pricing import stock_value
from round153_lp import primal_record
from round154_audit import residual_matrix,complete_support_matrix
from round155_oracle import reconstruct,FIRST_SHA,BOUNDED_SHA
from round155_price_certificate import qualified_price,qualified_phase
from round155_common import *

def full_price_matrix(path,gp,env):
    """Apply the inherited independent mathematical checker to reconstruction."""
    path=Path(path);delta=path.parent/'matrix_delta.json.gz';call=read(path.parent/'call.json')
    source=inspect.getsource(residual_matrix)
    needle='with gp.read(str(path),env=env) as m:'
    assert source.count(needle)==1 and source.count('SHA256=sha(path)')==1
    source=source.replace(needle,'with reconstruct(delta,gp,env) as m:')
    source=source.replace('SHA256=sha(path)','SHA256=sha(delta)')
    ns=dict(residual_matrix.__globals__,reconstruct=reconstruct,delta=delta)
    exec(compile(source,__file__+'::reconstructed_math','exec'),ns)
    # The matrix checker checks the actual D costs, their complete DP range,
    # W products and all original domain rows. Original-price transport is
    # checked independently below, against the unchanged exact potentials.
    actual_delta=load_gz(delta)
    definition=next(r for r in actual_delta['rows'] if r[0]=='hard_cost_D_definition')
    coefficients=dict(definition[3]);native_call=deepcopy(call)
    native_call['residual_coefficients']['state']={f'{i}:{y}':-coefficients.get(f'x[{i},{y}]',0.)
        for i,y in states(call['scope'])}
    result=ns['residual_matrix'](gp,env,path.parent/'model.mps',native_call)
    result.update(actual_Native_state_costs_checked=True,original_price_transport_checked_separately=True)
    return result

def price_arithmetic(path,base_bounds):
    raw=read(path);p=qualified_price(path);c=read(path.parent/'call.json');beta=F(p['beta_exact']);tau=F(p['tau_exact']);scope=p['scope'];ss=scope['stations']
    assert beta>=0 and p['complete_domain'] and c['full_support'] and c['q_can_be_negative']
    assert (c['scope'],c['beta_exact'],c['d_exact'],c['tau_exact'])==(scope,p['beta_exact'],p['d_exact'],p['tau_exact'])
    assert c['Seed']==0 and c['Threads']==1
    delta=load_gz(path.parent/'matrix_delta.json.gz');e=c['matrix_evidence']
    assert e['matrix_evidence_SHA']==sha(path.parent/'matrix_delta.json.gz') and e['semantics_SHA']==delta['semantics_SHA']
    assert sha(delta['base'])==delta['base_SHA']
    d={tuple(map(int,k.split(':'))):F(v) for k,v in p['d_exact'].items()};assert set(d)==set(states(scope))
    anchors={s['i']:(min(d[s['i'],y] for y in s['support'])+max(d[s['i'],y] for y in s['support']))/2 for s in ss}
    assert {int(k):F(v) for k,v in c['anchors_exact'].items()}==anchors
    scale=F(c['scale']);assert scale>0;anchor=sum(anchors.values(),F(0));written=c['residual_coefficients']
    wc={tuple(map(int,k.split(':'))):F(v) for k,v in written['state'].items()}
    for k in states(scope):
        error=(d[k]-anchors[k[0]])/scale-wc[k]
        assert error>=0 and error==F(c['state_downward_errors_exact'][f'{k[0]}:{k[1]}'])
    assert F(written['S_floor'])<=(anchor+beta*F(scope['gamma_L'])-tau)/scale
    assert F(written['S_G'])<=(anchor-tau)/scale and 0<=F(written['A'])<=beta/F(len(ss))/scale
    bounds=json.loads(json.dumps(s_bounds(scope)));assert c['bounds']==bounds
    l,u=map(F,c['positive_S_bounds']);assert [float(l),float(u)]==[bounds['lower'],bounds['upper']]
    guard=outward(F(1e-6)*(1+sum(max(abs(wc[s['i'],y]) for y in s['support']) for s in ss)*u+
        max(abs(F(written['S_floor'])),abs(F(written['S_G'])))*u+F(written['A'])*len(ss)*F(scope['gamma_U'])*u),True)
    assert guard==c['residual_guard_scaled']
    # Independently validate every changed coefficient, including tightened
    # product bounds, directly from the serialized actual matrix delta.
    ext=read(path.parent/'strengthening.json');lo=unary_dp(scope,wc);hi=unary_dp(scope,{k:-v for k,v in wc.items()})
    a,b=map(F,ext['tight_cost_bounds']);assert a<=F(lo['exact']) and b>=-F(hi['exact'])
    actual_bounds=dict(base_bounds)
    for change in delta['column_updates']:
        assert change['name'] in ('hard_cost_D','hard_cost_W')
        actual_bounds[change['name']]=[change['LB'],change['UB']]
    assert list(map(F,actual_bounds['hard_cost_D']))==[a,b]
    assert actual_bounds['hard_cost_W'][0]<-1e90 and actual_bounds['hard_cost_W'][1]>1e90
    actual={name:(sense,F(rhs),{k:F(v) for k,v in terms}) for name,sense,rhs,terms in delta['rows']}
    native_cost={k:-actual['hard_cost_D_definition'][2].get(f'x[{k[0]},{k[1]}]',F(0)) for k in states(scope)}
    native_lo=unary_dp(scope,native_cost);native_hi=unary_dp(scope,{k:-v for k,v in native_cost.items()})
    domain_covered=a<=F(native_lo['exact']) and b>=-F(native_hi['exact'])
    epsilon=u*sum((max([F(0)]+[native_cost[s['i'],y]-(d[s['i'],y]-anchors[s['i']])/scale
                               for y in s['support']]) for s in ss),F(0))
    def row(name,terms,sense,rhs):assert actual[name]==(sense,F(rhs),{k:F(v) for k,v in terms.items() if v}),name
    row('hard_cost_D_definition',{'hard_cost_D':1}|{f'x[{i},{y}]':-v for (i,y),v in native_cost.items()},'=',0)
    row('hard_cost_W_definition',{'hard_cost_W':1}|{f'Sx[{i},{y}]':-v for (i,y),v in native_cost.items()},'=',0)
    W={f'Sx[{i},{y}]':-v for (i,y),v in native_cost.items()}
    row('floor_residual',W|{'S':-F(written['S_floor']),'residual_scaled':1},'>',0)
    from itertools import combinations
    row('G_residual',W|{'S':-F(written['S_G']),'residual_scaled':1}|
        {f'abs[{i},{j}]':-F(written['A']) for i,j in combinations([s['i'] for s in ss],2)},'>',0)
    for name,slope,endpoint,sense in [('ll',l,a,'>'),('uu',u,b,'>'),('ul',u,a,'<'),('lu',l,b,'<')]:
        row('tight_DP_cost_product_'+name,{'hard_cost_W':1,'hard_cost_D':-slope,'S':-endpoint},sense,outward(-slope*endpoint,sense=='<'))
    assert len(actual)==8
    base_id=read(Path(delta['base']).parent/'base_identity.json');assert base_id['SHA256']==delta['base_SHA']
    q=p['calls'][0];assert q==read(path.parent/'return.json')
    stop=path.parent/'target_stop_plan.json';first=stop.exists()
    if first:
        plan=read(stop);assert plan['generated_source_SHA']==FIRST_SHA
        assert sha(OUT/'engineering/source_bytes'/f'{plan["wrapper_SHA"]}.py.txt')==plan['wrapper_SHA']
        assert F(plan['bound_stop_exact'])==F(guard) and F(plan['Native_BestBdStop'])>=F(guard)
        assert plan['tau_exact']==p['tau_exact'] and plan['guard_already_paid']
        if q['Status']==11 and q['bound_status_qualified']:
            ce=read(path.parent/'counterexample_stop.json');v=stock_value(scope,ce['stock']['Y'],beta,d)
            assert v['feasible'] and v['price']<tau and str(v['price'])==ce['original_price_exact']
    fallback=beta*F(scope['gamma_L'])+F(unary_dp(scope,d)['exact']);positive=fallback;ell=None
    assert p['fallback_lower']==outward(fallback,False) and not p['prior_residual_transports']
    accepted=bool(q['bound_status_qualified'] and domain_covered)
    if 'native_state_transport' in p:
        transport=p['native_state_transport']
        assert transport['call_SHA']==sha(path.parent/'call.json') and transport['matrix_delta_SHA']==sha(path.parent/'matrix_delta.json.gz')
        assert transport['actual_cost_bounds_cover_complete_domain']==domain_covered
        assert F(transport['native_cost_DP_lower_exact'])==F(native_lo['exact'])
        assert F(transport['native_cost_DP_upper_exact'])==-F(native_hi['exact'])
        assert F(transport['additional_scaled_residual_error_exact'])==epsilon
        assert transport['original_numerical_guard_retained'] and transport['native_bound_accepted']==accepted
    else:
        assert native_cost==wc and epsilon==0 and domain_covered,'unqualified Native coefficient change requires explicit correction'
    if accepted:
        assert q['Status'] in ((2,8,9,11,15) if first else (2,8,9)) and math.isfinite(q['native_bound'])
        ell=scale*(F(q['native_bound'])-F(guard)-epsilon);positive=max(positive,tau+ell/(u if ell>=0 else l))
    assert p['residual_lower_exact']==(str(ell) if ell is not None else None)
    lower=min(positive,stock_value(scope,[0]*len(ss),beta,d)['price']) if bounds['zero_possible'] else positive
    if p['inherited_lower'] is not None:
        assert F(p['inherited_lower'])<=fallback;lower=max(lower,F(p['inherited_lower']))
    assert p['lower']==outward(lower,False)
    if 'native_state_transport' in p:assert F(p['native_state_transport']['lower_exact'])==lower
    for v in p['stocks']:
        assert all(type(y) is int for y in v['Y'])
        real=stock_value(scope,v['Y'],beta,d)
        assert real['feasible'] and real['price']==F(v['price_exact']) and real['f']==F(v['f_exact'])
    assert F(p['upper'])>=min(F(v['price_exact']) for v in p['stocks'])>=F(p['lower'])
    return dict(path=str(path),SHA256=sha(path),lower=p['lower'],upper=p['upper'],
        raw_recorded_lower=raw['lower'],additional_scaled_error_exact=str(epsilon),
        actual_cost_domain_covered=domain_covered,all_dynamic_rows_and_guard_checked=True,
        explicit_native_transport='native_state_transport' in p)

def primal(m,scope,pool,path,claimed):
    data=load_gz(path);sparse=data.get('sparse_point',data.get('point'))
    point={v.VarName:sparse.get(v.VarName,0.) for v in m.getVars()};check=primal_record(m,point)
    assert check['qualified'] and check['objective']<=claimed+1e-9
    mass=math.fsum(r['weight'] for r in data['stocks']);negative=math.fsum(max(0.,-r['weight']) for r in data['stocks'])
    assert abs(mass-1)<=1e-8 and negative<=1e-8
    expected=F(0);marg={k:[] for k in states(scope)}
    for r in data['stocks']:
        Y=tuple(r['Y']);assert Y in pool
        v=stock_value(scope,Y);assert v['feasible'] and v['f']==F(r['f_exact']);expected+=F(r['weight'])*v['f']
        for s,y in zip(scope['stations'],Y):marg[s['i'],y].append(r['weight'])
    error=max(abs(math.fsum(v)-point[f'state_{i}_{y}']) for (i,y),v in marg.items())
    assert error<=1e-8 and F(point['G'])>=expected
    return dict(path=str(path),SHA256=sha(path),upper=claimed,objective=check['objective'],mass=mass,negative_mass=negative,
        full_marginal_error=error,true_completion_slack=float(F(point['G'])-expected),original_Q_primal=check)

def loops(label='loop_evidence_v1',phase='all'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_exact_worker import enable
    configure();affinity();enable();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[];prices=[];primals=[];matrices=[]
    starts=read(OUT/'starting_pools.json');values={};base_bounds={};reads=0
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for rp in sorted((OUT/'coupled').glob('*/result.json')):
            if phase!='all' and rp.parent.name!=phase:continue
            qualified_result,r=qualified_phase(rp);plan=read(rp.parent/'plan.json');prior=read(plan['source']);scope=r['scope'];role=r['role']
            qualified_records={v['iteration']:v for v in r['records']}
            assert sha(plan['source'])==plan['source_SHA'] and scope==prior['scope']==starts[role]['scope']
            assert not r['refresh_required'] and r['Q_SHA']==sha(plan['Q'])==starts[role]['Q_SHA']
            pool=dict.fromkeys(tuple(Y) for Y in prior['columns']);fvalues=values.setdefault(role,{})
            lower,upper=prior['lower'],prior['upper'];paths=sorted(rp.parent.glob('iter*/direction.json'));steps=[];all_supports=list(prior['supports'])
            with gp.read(plan['Q'],env=env) as q:
                reads+=1;matrix=exact_matrix(q);bounds=replay_q_bounds(matrix,load_gz(rp.parent/'Q_bounds.json.gz'))
                for number,dp in enumerate(paths):
                    d=read(dp);cert=load_gz(dp.parent/'certificate.json.gz');cq=independent_residual(matrix,bounds,cert,scope)
                    assert d['scope']==scope and d['Q_SHA']==r['Q_SHA'] and len(pool)==d['columns_before']
                    assert cq==F(d['C_Q_exact']) and F(d['zeta_exact'])==cq+F(d['tau_exact'])
                    pp=dp.parent/'pricing/result.json'
                    if not pp.exists():
                        assert cq+F(d['a_K_exact'])<F(d['zeta_exact']);continue
                    p=qualified_price(pp);raw_record=read(dp.parent/'result.json');rec=qualified_records[raw_record['iteration']]
                    assert all(rec[k]==v for k,v in raw_record.items() if k!='price_lower')
                    assert rec['price_lower']==p['lower']
                    assert p['scope']==scope and p['d_exact']==d['d_exact'] and p['beta']==d['beta']
                    delta=load_gz(pp.parent/'matrix_delta.json.gz')
                    if delta['base'] not in base_bounds:
                        with gp.read(delta['base'],env=env) as base_model:
                            reads+=1;base_bounds[delta['base']]={v.VarName:[v.LB,v.UB] for v in base_model.getVars() if v.VarName in ('hard_cost_D','hard_cost_W')}
                    prices.append(price_arithmetic(pp,base_bounds[delta['base']]));new_lower=cq+min(F(d['a_K_exact']),F(p['lower']))
                    full_minimum=(number in (0,len(paths)-1) or number%16==0 or outward(new_lower,False)>lower)
                    costs={tuple(map(int,k.split(':'))):F(v) for k,v in d['d_exact'].items()}
                    support=r['supports'][len(all_supports)];raw_support=read(dp.parent/'support.json')
                    if 'raw_support_SHA' in support:
                        assert support['raw_support_SHA']==sha(dp.parent/'support.json')
                        assert support['row']['terms']==raw_support['row']['terms'] and support['row']['name']==raw_support['row']['name']
                        assert support['row']['rhs']<=raw_support['row']['rhs']
                        assert sha(ROOT/support['qualified_price_path'])==support['qualified_price_SHA']
                    else:assert support==raw_support
                    row=support['row'];terms=row['terms']
                    assert row['sense']=='>' and set(terms)<={'G'}|{f'state_{i}_{y}' for i,y in states(scope)}
                    assert support['direction_SHA']==sha(dp) and support['price_path']==pp.relative_to(ROOT).as_posix()
                    correction=min((F(terms.get('G',0))-F(d['beta']))*F(scope[k]) for k in ('gamma_L','gamma_U'))
                    for s in scope['stations']:
                        correction+=min(F(terms.get(f'state_{s["i"]}_{y}',0))-costs[s['i'],y] for y in s['support'])
                    assert correction==F(support['transport_exact']) and F(row['rhs'])<=F(p['lower'])+correction
                    all_supports.append(support)
                    if full_minimum:
                        for Y in pool:
                            if Y not in fvalues:
                                v=stock_value(scope,Y);assert v['feasible'];fvalues[Y]=v['f']
                        minimum=min(F(d['beta'])*fvalues[Y]+sum((costs[s['i'],y] for s,y in zip(scope['stations'],Y)),F(0)) for Y in pool)
                        assert F(d['a_K_exact'])==min(F(cert['a_raw']),minimum)
                        assert F(d['initial_true_price_upper_exact'])==minimum
                    feedback=load_gz(dp.parent/'column_feedback.json.gz');new=0
                    for row in feedback:
                        v=row['stock'];Y=tuple(v['Y']);fresh=Y not in pool
                        assert row['new']==fresh and F(row['true_reduced_cost_exact'])==F(v['price_exact'])-F(d['a_K_exact'])
                        assert row['negative']==(F(row['true_reduced_cost_exact'])<0)
                        if fresh:new+=1;pool[Y]=None
                    assert rec['added']==new and rec['columns']==len(pool)
                    lower=max(lower,outward(new_lower,False));upper=min(upper,rec['RMP_objective'])
                    assert rec['lower']==lower and rec['upper']==upper and rec['gap']==upper-lower
                    if (dp.parent/'primal.json.gz').exists():primals.append(primal(q,scope,pool,dp.parent/'primal.json.gz',rec['RMP_objective']))
                    if number in (0,len(paths)-1):matrices.append(full_price_matrix(pp,gp,env));reads+=1
                    steps.append(dict(iteration=rec['iteration'],complete_C_Q=True,complete_price_recovery=True,all_current_column_minimum=full_minimum,new_columns=new))
                assert list(pool)==[tuple(Y) for Y in r['columns']] and r['lower']==lower and r['upper']<=upper
                assert r['supports']==all_supports
                own=rp.parent/'final_primal.json.gz'
                if own.exists():primals.append(primal(q,scope,pool,own,read(rp.parent/'final_RMP/result.json')['objective']))
                candidates=([Path(r['upper_witness_source'])] if r.get('upper_witness_source') else [])+witnesses(plan['source'])
                admitted=[]
                for path in dict.fromkeys(candidates):
                    if not path.exists():continue
                    try:admitted.append(primal(q,scope,pool,path,r['upper']))
                    except AssertionError:continue
                assert admitted,('actual qualified retained upper witness missing',str(rp),r['upper'])
                primals.append(admitted[0])
                facts.append(dict(result=str(rp),SHA256=sha(rp),qualified_result=str(qualified_result),
                    qualified_result_SHA=sha(qualified_result),steps=steps,upper_witness=admitted[0],columns=len(pool),lower=r['lower'],upper=r['upper']))
    assert facts,('no completed phase selected',phase)
    write(target/'result.json',dict(PASS=True,selected_phase=phase,phases=facts,prices=prices,primals=primals,matrices=matrices,Native_model_reads=reads,Optimize=0,
        minimum_scope='every lower-improving direction plus first/last/every16; all Q certificates and all price/feedback arithmetic',
        source_SHA=sha(__file__),nonimplementer_agent_review=False))
    print(json.dumps(dict(PASS=True,phases=len(facts),prices=len(prices),primals=len(primals),model_reads=reads,Optimize=0)),flush=True)

def support_replays(label='support_readback_v1',phase='all'):
    """Independent free-Q identity, exact dual and saved numerical-primal checks."""
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    starts=read(OUT/'starting_pools.json');facts=[]
    def inherited_bounds(source,seen=None):
        seen=set() if seen is None else seen;source=Path(source).resolve()
        assert source not in seen;seen.add(source)
        candidate=source.parent/'Q_bounds.json.gz'
        if candidate.exists():return candidate
        previous=read(source)['prior_results'];assert len(previous)==1
        return inherited_bounds(previous[0],seen)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for path in sorted((OUT/'support_LP').glob('*/result.json')):
            if phase!='all' and path.parent.name!=phase:continue
            result=read(path);role=result['role'];source=Path(result['prior_results'][0]);prior=read(source)
            assert result['scope']==prior['scope']==starts[role]['scope']
            assert result['supports']==prior['supports'] and result['columns']==prior['columns']
            original_path=Path(starts[role]['Q']);actual_path=path.parent/'solve/model.mps'
            assert sha(original_path)==result['Q_SHA']==starts[role]['Q_SHA']
            call=read(path.parent/'solve/call.json');returned=read(path.parent/'solve/return.json')
            assert call['model_SHA']==sha(actual_path) and call['all_original_variables_free']
            assert call['Threads']==1 and call['Seed']==0 and returned['Status']==2
            with gp.read(str(original_path),env=env) as original, gp.read(str(actual_path),env=env) as actual:
                original_matrix=exact_matrix(original);actual_matrix=exact_matrix(actual)
                complete_support_matrix(original_matrix,actual_matrix,[entry['row'] for entry in result['supports']])
                bounds=replay_q_bounds(original_matrix,load_gz(inherited_bounds(source)))
                certificate=load_gz(path.parent/'certificate.json.gz')
                exact_lower=independent_residual(actual_matrix,bounds,certificate)
                point=load_gz(path.parent/'solve/solution.json.gz');check=primal_record(actual,point)
                assert check['qualified'] and set(point)==set(actual_matrix['variables'])
                objective=actual_matrix['constant']+sum((v['objective']*F(point[name])
                    for name,v in actual_matrix['variables'].items()),F(0))
                claim=result['support_replay']
                assert abs(float(objective)-claim['U'])<=1e-9
                assert claim['L']==certificate['lower'] and F(claim['L'])<=exact_lower
                assert result['lower']==max(prior['lower'],claim['L']) and result['upper']==prior['upper']
                assert claim['supports']==len(result['supports']) and claim['all_original_variables_free']
                assert claim['finite_support_upper_not_full_hull_upper']
                facts.append(dict(result=str(path),SHA256=sha(path),original_Q_SHA=sha(original_path),
                    actual_matrix_SHA=sha(actual_path),supports=len(result['supports']),all_original_variables_free=True,
                    exactly_original_Q_plus_declared_supports=True,dual_lower_exact=str(exact_lower),primal_check=check,
                    saved_LP_primal_objective_exact=str(objective),LP_primal_not_used_as_full_hull_upper=True,
                    retained_hull_lower=result['lower'],retained_hull_upper=result['upper']))
    assert facts,('no completed support replay selected',phase)
    write(target/'result.json',dict(PASS=True,selected_phase=phase,replays=facts,Optimize=0,source_SHA=sha(__file__),
        nonimplementer_agent_review=False,review_method='actual complete matrix equality, independent exact dual residual and saved primal readback'))
    print(json.dumps(dict(PASS=True,replays=len(facts),Optimize=0)),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
