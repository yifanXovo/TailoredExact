"""Finite final arithmetic, provenance and selected primal audit; no Optimize."""
from fractions import Fraction as F
from functools import lru_cache
from round143_math import outward
from round152_math import states,s_bounds,unary_dp
from round153_lp import primal_record
from round153_pricing import stock_value
from round153_common import *

@lru_cache(maxsize=None)
def domain_arithmetic(scope_text,beta_text,cost_text):
    scope=json.loads(scope_text);costs={tuple(map(int,k.split(':'))):F(v) for k,v in json.loads(cost_text).items()}
    assert set(costs)==set(states(scope))
    dp=unary_dp(scope,costs);assert dp is not None
    # Saved dictionaries have JSON string keys for station-indexed box maps.
    bounds=json.loads(json.dumps(s_bounds(scope)))
    return bounds,F(beta_text)*F(scope['gamma_L'])+F(dp['exact'])

def mps_objective(path):
    section=None;name=None;objective={}
    with Path(path).open(encoding='utf-8') as stream:
        for line in stream:
            words=line.split()
            if not words or words[0].startswith('*'):continue
            if words[0] in ('ROWS','COLUMNS','RHS','BOUNDS','ENDATA'):
                section=words[0]
                if section in ('RHS','BOUNDS','ENDATA'):break
                continue
            if section=='ROWS' and words[0]=='N':assert name is None;name=words[1]
            if section=='COLUMNS' and "'MARKER'" not in words:
                assert len(words) in (3,5)
                for k in range(1,len(words),2):
                    if words[k]==name:
                        assert words[0] not in objective
                        objective[words[0]]=F(float(words[k+1]))
    assert name is not None;return objective

def audit_price(path, seen, ancestors=()):
    path=Path(path).resolve()
    assert str(path) not in ancestors,'cyclic price provenance'
    ancestry=ancestors+(str(path),)
    if str(path) in seen:return read(path)
    p=read(path);scope=p['scope'];beta=F(p['beta'])
    assert beta>=0
    costs={tuple(map(int,k.split(':'))):F(v) for k,v in p['d_exact'].items()}
    bounds,fallback=domain_arithmetic(json.dumps(scope,sort_keys=True),str(beta),json.dumps(p['d_exact'],sort_keys=True))
    assert p['fallback_lower']==outward(fallback,False)
    for row in p['stocks']:
        value=stock_value(scope,row['Y'],beta,costs)
        assert value['feasible'] and F(row['price_exact'])==value['price']
        if 'S_interval_exact' in p:
            lo,hi=map(F,p['S_interval_exact']);assert lo<=value['S']<=hi
    if p['upper'] is not None:
        assert p['stocks'] and F(p['upper'])>=min(F(v['price_exact']) for v in p['stocks'])
    if p.get('partitioned_full_price'):
        assert p['complete_domain'] and p['exact_closed_interval_cover'] and p['legal_zero_separate']
        intervals=[tuple(map(F,v)) for v in p['intervals_exact']]
        assert p['positive_S_bounds']==bounds and F(p['fallback_exact'])==fallback
        assert bool(intervals)==(F(bounds['upper_exact'])>0)
        if intervals:
            assert intervals[0][0]==F(bounds['lower_exact']) and intervals[-1][1]==F(bounds['upper_exact'])
            assert all(0<a<=b for a,b in intervals)
            assert all(a[1]==b[0] for a,b in zip(intervals,intervals[1:]))
        parts=[F(p['fallback_exact'])]*len(intervals);used=set()
        for rec in p['child_results']:
            index=rec['index'];assert type(index)==int and 0<=index<len(intervals) and index not in used;used.add(index)
            child=audit_price(ROOT/rec['result'],seen,ancestry)
            assert not child['complete_domain'] and child['scope']==scope
            assert child['beta']==p['beta'] and child['d_exact']==p['d_exact']
            assert tuple(map(F,child['S_interval_exact']))==intervals[index]
            assert child['lower']==rec['lower'] and child['upper']==rec['upper']
            parts[index]=F(child['lower'])
        assert parts==list(map(F,p['positive_slice_lowers_exact']))
        if bounds['zero_possible']:
            zero=stock_value(scope,[0]*len(scope['stations']),beta,costs)
            assert zero['feasible'];parts.append(zero['price'])
        assert parts and F(p['lower'])<=max(F(p['fallback_exact']),min(parts))
    if p.get('overlay_full_price'):
        assert p['complete_domain'] and p['positive_S_bounds']==bounds and not p['calls']
        parents=[];conditions=[];points={F(bounds['lower_exact']),F(bounds['upper_exact'])}
        for record in p['source_prices']:
            source_path=Path(record['path']);assert sha(source_path)==record['SHA256']
            parent=audit_price(source_path,seen,ancestry)
            assert parent['complete_domain'] and parent['scope']==scope and parent['beta']==p['beta'] and parent['d_exact']==p['d_exact']
            parents.append(parent)
            for child_ref in parent.get('child_results',[]):
                child=audit_price(ROOT/child_ref['result'],seen,ancestry)
                lo,hi=map(F,child['S_interval_exact']);points.update([lo,hi]);conditions.append((lo,hi,F(child['lower'])))
        global_lower=max([fallback]+[F(v['lower']) for v in parents]);assert parents
        points=sorted(points);cells=[]
        if F(bounds['upper_exact'])>0:cells=[(points[0],points[0])] if len(points)==1 else list(zip(points[:-1],points[1:]))
        assert cells==[tuple(map(F,v)) for v in p['cells_exact']]
        lows=[max([global_lower]+[value for a,b,value in conditions if a<=lo<=hi<=b]) for lo,hi in cells]
        assert lows==list(map(F,p['cell_lowers_exact'])) and global_lower==F(p['same_direction_global_lower_exact'])
        if bounds['zero_possible']:lows.append(stock_value(scope,[0]*len(scope['stations']),beta,costs)['price'])
        assert lows and p['lower']==outward(max(global_lower,min(lows)),False)
    if p.get('graphcut_full_price'):
        from round153_graphcut import audit_graph_price
        audit_graph_price(p)
    raw=path.parent/'raw' if (path.parent/'restriction.json').exists() else path.parent
    call=raw/'call.json'
    if call.exists():
        c=read(call);assert c['model_SHA']==sha(raw/'model.mps') and c['matrix_readback']
        returned=read(raw/'return.json');assert len(p['calls'])==1;q=p['calls'][0]
        assert c['scope']==scope and c['beta']==p['beta'] and c['d_exact']==p['d_exact']
        assert c['Seed']==0 and c['Threads']==1 and c['full_support']
        assert returned['Status']==q['Status']
        anchors={s['i']:(min(costs[s['i'],y] for y in s['support'])+max(costs[s['i'],y] for y in s['support']))/2 for s in scope['stations']}
        assert {int(k):F(v) for k,v in c['anchors_exact'].items()}==anchors
        centered={k:v-anchors[k[0]] for k,v in costs.items()};scale=F(c['scale']);assert scale>0
        largest=max([abs(float(beta))]+[abs(float(v)) for v in centered.values()]+[1e-30])
        assert float(scale)==math.ldexp(1.,math.ceil(math.log2(largest)))
        scaled={k:v/scale for k,v in centered.items()};sb=beta/scale
        guard=1e-6*(abs(float(sb))+sum(max(abs(float(scaled[s['i'],y])) for y in s['support']) for s in scope['stations'])+1.)
        assert guard==c['numerical_guard_scaled']
        actual=mps_objective(raw/'model.mps')
        correction=sum(max([F(0)]+[actual.get(f'x[{s["i"]},{y}]',F(0))-scaled[s['i'],y] for y in s['support']]) for s in scope['stations'])
        correction+=max(F(0),(actual.get('q',F(0))-sb)*F(scope['gamma_U']))
        assert correction==F(c['objective_correction_scaled_exact'])
        positive=fallback
        if q['bound_status_qualified']:
            assert q['Status'] in ((2,9) if c.get('node_limit') is None else (2,8))
            assert q['native_bound'] is not None and math.isfinite(q['native_bound'])
            positive=max(positive,scale*(F(q['native_bound'])-F(guard)-correction)+sum(anchors.values(),F(0)))
        else:assert q['native_bound'] is None
        assert F(q['positive_lower'])<=positive
        qualified_lower=positive
        if bounds['zero_possible'] and 'S_interval_exact' not in p:
            zero=stock_value(scope,[0]*len(scope['stations']),beta,costs);assert zero['feasible']
            qualified_lower=min(qualified_lower,zero['price'])
        assert F(p['lower'])<=qualified_lower
        if 'S_interval_exact' in p:
            restriction=read(path.parent/'restriction.json')
            assert restriction['declared_before_Optimize'] and restriction['S_interval_exact']==p['S_interval_exact']
            assert c['S_interval_exact']==p['S_interval_exact']
            lo,hi=map(F,p['S_interval_exact']);expected=[outward(1/hi,False),outward(1/lo,True)]
            assert p['actual_t_bounds']==c['actual_t_bounds']==c['t_bounds']==restriction['actual_t_bounds']==expected
            assert read(raw/'result.json')==p
    elif not p.get('partitioned_full_price') and not p.get('overlay_full_price') and not p.get('graphcut_full_price'):
        assert not p['calls'] and F(p['lower'])<=fallback
    seen[str(path)]=dict(SHA256=sha(path),partitioned=p.get('partitioned_full_price',False),graphcut=p.get('graphcut_full_price',False))
    return p

def witnesses(result_path,seen=None):
    seen=set() if seen is None else seen;path=Path(result_path)
    if path in seen:return []
    seen.add(path);data=read(path);found=[]
    own=path.parent/'best_primal.json.gz'
    if own.exists():found.append(own)
    if data.get('upper_witness_source'):found.append(Path(data['upper_witness_source']))
    for previous in data.get('prior_results',[]):found.extend(witnesses(previous,seen))
    return sorted(set(found))

def exact_matrix(m):
    """Copy the actually read binary64 Q, with no solver-derived dual data."""
    assert m.ModelSense==1 and m.NumQNZs==m.NumQConstrs==m.NumGenConstrs==m.NumSOS==0
    assert all(v.VType=='C' for v in m.getVars())
    assert len({v.VarName for v in m.getVars()})==m.NumVars
    assert len({c.ConstrName for c in m.getConstrs()})==m.NumConstrs
    variables={v.VarName:dict(objective=F(v.Obj),bounds=[v.LB if v.LB>-1e99 else None,
        v.UB if v.UB<1e99 else None]) for v in m.getVars()}
    rows={}
    for c in m.getConstrs():
        e=m.getRow(c)
        rows[c.ConstrName]=dict(sense=c.Sense,rhs=F(c.RHS),
            terms={e.getVar(j).VarName:F(e.getCoeff(j)) for j in range(e.size())})
    return dict(variables=variables,rows=rows,constant=F(m.ObjCon))


def replay_q_bounds(matrix,record):
    """Replay each implied bound from Q and earlier proved bounds only."""
    bounds={k:list(v['bounds']) for k,v in matrix['variables'].items()}
    for d in record['derivations']:
        row=matrix['rows'][d['row']];sign=d['row_sign'];assert sign in (-1,1)
        assert row['sense']=='=' or (row['sense']=='<' and sign==1) or (row['sense']=='>' and sign==-1)
        k=d['variable'];a=sign*row['terms'][k];side=1 if a>0 else 0
        assert d['side']==['LB','UB'][side] and bounds[k][side] is None
        other=F(0)
        for name,coefficient in row['terms'].items():
            if name==k:continue
            coefficient*=sign;b=bounds[name][0 if coefficient>0 else 1]
            assert b is not None;other+=coefficient*F(b)
        exact=(sign*row['rhs']-other)/a
        assert exact==F(d['exact']) and d['value']==outward(exact,side==1)
        bounds[k][side]=d['value']
    assert bounds==record['bounds']
    return bounds


def independent_residual(matrix,bounds,certificate,scope=None):
    """Recompute C_Q or a free-LP dual from actual matrix coefficients."""
    multipliers=certificate['multipliers'];expected=set(matrix['rows'])
    residual={k:v['objective'] for k,v in matrix['variables'].items()}
    value=matrix['constant']
    if scope is not None:
        expected|={'hull_convexity','hull_gini'}
        assert F(multipliers['hull_convexity'])==F(certificate['a_raw'])
        assert F(multipliers['hull_gini'])==F(certificate['beta'])>=0
        for s in scope['stations']:
            assert F(certificate['pi'].get(f'{s["i"]}:{s["support"][0]}',0))==0
            for y in s['support'][1:]:
                name=f'hull_link_{s["i"]}_{y}';expected.add(name)
                p=F(multipliers[name]);assert p==F(certificate['pi'][f'{s["i"]}:{y}'])
                residual[f'state_{s["i"]}_{y}']+=p
        residual['G']-=F(certificate['beta'])
    assert set(multipliers)==expected
    for name,row in matrix['rows'].items():
        p=F(multipliers[name])
        assert row['sense']=='=' or (row['sense']=='>' and p>=0) or (row['sense']=='<' and p<=0)
        value+=p*row['rhs']
        if p:
            for k,a in row['terms'].items():residual[k]-=p*a
    row_value=value;contributions={}
    for k,r in residual.items():
        if not r:continue
        b=bounds[k][0 if r>0 else 1];assert b is not None
        term=r*F(b);value+=term
        if term:contributions[k]=str(term)
    assert value==F(certificate['lower_exact']) and F(certificate['lower'])<=value
    assert row_value==F(certificate['row_objective_exact'])
    assert value-row_value==F(certificate['residual_support_exact'])
    assert {k:str(v) for k,v in residual.items() if v}==certificate['nonzero_column_residuals']
    assert contributions==certificate['bound_contributions_exact']
    return value


def run(label):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    decision=read(OUT/'candidate_decision.json');certificates=[];primals=[];deps={};prices={};refinements=[];iteration_paths=set()
    residual_checks=[];support_checks=[];reference_checks=[];inherited_support_checks=[];primal_discovery_checks=[];primal_refresh_checks=[];model_reads=0
    indices={role:{r['member']:r for r in load_gz(OLD/'artifacts'/f'research_{role}.members.json.gz')}
        for role in decision['science_evidence']}
    for role in decision['science_evidence']:
        for record in read(OUT/'reference'/role/'reuse_index.json')['dependencies']:
            assert sha(ROOT/record['member'])==record['SHA256'];deps[record['member']]=record
        for p in (OUT/'coupled').glob(role+'*/seed_sources.json'):
            for record in read(p):
                if record['commit']!=SCIENCE:continue
                r=indices[role][record['path']];assert record['SHA256']==r['SHA256']==sha(ROOT/record['path'])
                deps[record['path']]=dict(r,commit=SCIENCE,archive=f'results/unified_exact_round152/artifacts/research_{role}.zip')
    for path in sorted((OUT/'coupled').glob('*/result.json')):
        data=read(path)
        if data.get('primal_refresh_only'):
            plan=read(path.parent/'plan.json');prior=Path(plan['prior_result']);previous=read(prior)
            assert plan['prior_result_SHA']==sha(prior) and data['prior_results']==[str(prior)]
            assert data['Q_SHA']==previous['Q_SHA']==plan['Q_SHA']
            assert data['scope']==previous['scope']==plan['scope']
            assert data['lower']==previous['lower'] and data['supports']==previous['supports']
            assert data['columns']==previous['columns'] and len(data['columns'])==plan['columns']
            assert data['no_new_lower_claim'] and data['no_new_pricing'] and data['original_variables_free']
            assert data['new_RMP_solve'] and not data['primal_discovery_only']
            assert data['upper']<=previous['upper'] and data['refresh']['prior_upper']==previous['upper']
            native=read(path.parent/'solve/return.json')
            assert native['Status']==data['refresh']['Native_status'] and native['Status'] in (2,9)
            if data['refresh']['upper_witness_updated']:
                assert native['solution_count']>0 and data['refresh']['primal']['qualified']
                assert (path.parent/'best_primal.json.gz').exists()
                assert data['upper']<previous['upper'] and data['upper']==data['refresh']['RMP_objective']
            else:assert data['upper']==previous['upper']
            primal_refresh_checks.append(dict(path=path.relative_to(ROOT).as_posix(),
                prior_result_SHA=sha(prior),no_new_columns_or_lower=True,
                lower_and_supports_unchanged=True,selected_endpoint_upper_is_checked_separately=True))
        if not data.get('primal_discovery_only'):continue
        plan=read(path.parent/'plan.json');prior=Path(plan['prior_result']);previous=read(prior)
        assert plan['prior_result_SHA']==sha(prior) and data['prior_results']==[str(prior)]
        assert data['Q_SHA']==previous['Q_SHA']==plan['Q_SHA']
        assert data['scope']==previous['scope']==plan['scope']
        assert data['lower']==previous['lower'] and data['supports']==previous['supports']
        assert data['upper']<=previous['upper'] and data['no_new_lower_claim']
        columns=[tuple(Y) for Y in data['columns']];initial=[tuple(Y) for Y in previous['columns']]
        assert len(columns)==len(set(columns)) and columns[:len(initial)]==initial
        assert len(initial)==plan['initial_columns'];count=len(initial)
        for step in sorted(path.parent.glob('sweep*/result.json')):
            r=read(step);discovery=read(step.parent/'discovery.json')
            assert r['lower']==previous['lower'] and r['columns_before']==count
            assert r['columns']==count+r['added']
            selected=discovery.get('selected',[]);added=[tuple(Y) for Y in discovery['new_columns']]
            assert len(added)==r['added'] and added==columns[count:r['columns']]
            costs={tuple(map(int,k.split(':'))):v for k,v in discovery['d'].items()}
            for item in selected:
                value=stock_value(data['scope'],item['Y'],discovery['beta'],costs)
                assert value['feasible'] and value['f']==F(item['f_exact'])
                assert value['price']==F(item['price_exact'])<F(discovery['a'])-F(1e-9)
            pairs=discovery['paired_exchange']['pairs'];before=set(columns[:count]);paired_children=set()
            solution=load_gz(step.parent/'solution.json.gz') if pairs else {}
            column_index={Y:j for j,Y in enumerate(columns[:count])}
            for pair in pairs:
                first,second=map(tuple,pair['parents']);left,right=map(tuple,pair['children'])
                assert first in before and second in before
                weights=[solution[f'hull_lambda_{column_index[Y]:05}'] for Y in (first,second)]
                assert weights==pair['parent_weights'] and min(weights)==pair['movable_weight']>1e-10
                assert all(sorted((first[j],second[j]))==sorted((left[j],right[j])) for j in range(len(first)))
                values=[stock_value(data['scope'],Y) for Y in (first,second,left,right)]
                assert all(v['feasible'] for v in values)
                assert [str(v['f']) for v in values]==pair['f_exact']
                assert values[2]['f']+values[3]['f']-values[0]['f']-values[1]['f']==F(pair['f_sum_change_exact'])<0
                paired_children.update((left,right))
            assert set(added)==({tuple(v['Y']) for v in selected}|paired_children)-before
            count=r['columns']
        assert count==len(columns)
        primal_discovery_checks.append(dict(path=path.relative_to(ROOT).as_posix(),
            columns_added=len(columns)-len(initial),all_new_stocks_recomputed=True,lower_unchanged=True,
            selected_endpoint_upper_is_checked_separately=True,local_search_not_pricing_lower=True))
    for path in sorted((OUT/'coupled').glob('*/iter*/certificate.json.gz')):
        c=load_gz(path);price=audit_price(path.parent/'pricing/result.json',prices)
        assert c['qualified'] and c['bounds_derived_only_from_Q'] and c['one_convexity_correction']
        assert F(c['D_K_exact'])==F(c['lower_exact'])+F(c['a_true_RMP_exact'])
        assert F(c['a_true_RMP_exact'])<=F(c['true_column_min_exact'])
        delta=max(F(0),F(c['a_true_RMP_exact'])-F(price['lower']))
        assert delta==F(c['delta_exact']) and F(c['coupled_lower'])<=F(c['D_K_exact'])-delta
        assert price['complete_domain'] and price['lower']==c['pricing_lower'] and price['beta']==c['beta']
        certificates.append(dict(path=path.relative_to(ROOT).as_posix(),lower=c['coupled_lower'],beta=c['beta']))
        iteration_paths.add(path.resolve())
    for path in sorted((OUT/'coupled').glob('*/refined_certificate.json.gz')):
        c=load_gz(path);source=load_gz(c['source_certificate'])
        plan=read(path.parent/'plan.json');source_path=Path(c['source_certificate']);old_plan=read(source_path.parent.parent/'plan.json')
        assert source_path.resolve() in iteration_paths
        data=read(path.parent/'result.json');prior=Path(data['prior_results'][0]);previous=read(prior)
        assert c['qualified'] and source['qualified'] and c['beta']==source['beta'] and c['pi']==source['pi']
        assert plan['source_certificate_SHA']==sha(source_path) and plan['prior_result_SHA']==sha(prior)
        assert Path(plan['source_iteration']).resolve()==source_path.parent.resolve()
        assert plan['Q_SHA']==old_plan['Q_SHA']==previous['Q_SHA']==data['Q_SHA']
        assert plan['scope']==old_plan['scope']==previous['scope']==data['scope']
        assert plan['Q_SHA']==sha(OUT/'reference'/plan['role']/'direct/model.mps')
        if 'source_plan_SHA' in plan:assert plan['source_plan_SHA']==sha(source_path.parent.parent/'plan.json')
        assert plan['source_price_SHA']==sha(Path(c['price_paths'][0]))
        pp=[audit_price(p,prices) for p in c['price_paths']]
        assert all(p['complete_domain'] and p['scope']==pp[0]['scope'] and p['beta']==pp[0]['beta'] and p['d_exact']==pp[0]['d_exact'] for p in pp)
        assert pp[0]['scope']==plan['scope'] and pp[0]['beta']==source['beta']
        assert all(F(v)==-F(source['pi'].get(k,0.)) for k,v in pp[0]['d_exact'].items())
        assert c['lower_exact']==source['lower_exact'] and c['a_true_RMP_exact']==source['a_true_RMP_exact']
        lm=max(F(p['lower']) for p in pp);dk=F(c['lower_exact'])+F(c['a_true_RMP_exact'])
        delta=max(F(0),F(c['a_true_RMP_exact'])-lm)
        assert F(c['pricing_lower_exact'])==lm and F(c['D_K_exact'])==dk and F(c['delta_exact'])==delta
        assert F(c['coupled_lower'])<=dk-delta and c['one_convexity_correction']
        refinements.append(dict(path=path.relative_to(ROOT).as_posix(),lower=c['coupled_lower']))
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        for role,spec in decision['science_evidence'].items():
            result_path=ROOT/spec['coupled_result'];data=read(result_path);scope=data['scope'];qp=OUT/'reference'/role/'direct/model.mps'
            assert data['Q_SHA']==sha(qp) and scope==read(OUT/'reference'/role/'domain.json')['scope'];options=[]
            for p in witnesses(result_path):
                v=load_gz(p)
                if abs(v['check']['objective']-data['upper'])<=1e-8:options.append((v['check']['objective'],p,v))
            assert options,role
            _,source,witness=min(options,key=lambda v:v[0]);point=witness['point'];stocks=witness['stocks'];exact_f=F(0)
            mass=sum(F(r['weight']) for r in stocks);negative=sum(max(F(0),-F(r['weight'])) for r in stocks)
            for row in stocks:
                v=stock_value(scope,row['Y']);assert v['feasible'] and v['f']==F(row['f_exact'])
                exact_f+=F(row['weight'])*v['f']
            mismatch=max(abs(sum(F(r['weight']) for r in stocks if r['Y'][j]==y)-F(point[f'state_{s["i"]}_{y}']))
                for j,s in enumerate(scope['stations']) for y in s['support'])
            slack=F(point['G'])-exact_f
            assert abs(mass-1)<=F(1e-8) and negative<=F(1e-8) and mismatch<=F(1e-8) and slack>=0
            with gp.read(str(qp),env=env) as m:
                model_reads+=1;matrix=exact_matrix(m);bound_records={};phase_results={};true_values={}
                reference_bounds=replay_q_bounds(matrix,load_gz(OUT/'reference'/role/'implied_bounds.json.gz'))
                reference_certificate=load_gz(OUT/'reference'/role/'direct/dual_certificate.json.gz')
                reference_lower=independent_residual(matrix,reference_bounds,reference_certificate)
                assert F(read(OUT/'reference'/role/'direct/result.json')['L'])<=reference_lower
                reference_checks.append(dict(role=role,Q_SHA=data['Q_SHA'],exact_lower=str(reference_lower)))
                for bp in sorted((OUT/'coupled').glob(role+'*/Q_bounds.json.gz')):
                    bound_records[bp.parent]=replay_q_bounds(matrix,load_gz(bp))
                assert bound_records and all(v==next(iter(bound_records.values())) for v in bound_records.values())
                for cp in sorted((OUT/'coupled').glob(role+'*/iter*/certificate.json.gz')):
                    c=load_gz(cp);phase=cp.parent.parent;plan=read(phase/'plan.json')
                    assert plan['scope']==scope and plan['Q_SHA']==data['Q_SHA']
                    cp_price=audit_price(cp.parent/'pricing/result.json',prices)
                    assert cp_price['complete_domain'] and cp_price['scope']==scope and cp_price['beta']==c['beta']
                    assert set(cp_price['d_exact'])=={f'{s["i"]}:{y}' for s in scope['stations'] for y in s['support']}
                    assert all(F(v)==-F(c['pi'].get(k,0)) for k,v in cp_price['d_exact'].items())
                    cq=independent_residual(matrix,bound_records[phase],c,scope)
                    if phase not in phase_results:
                        phase_results[phase]=read(phase/'result.json');pr=phase_results[phase]
                        assert len(pr['columns'])==len({tuple(Y) for Y in pr['columns']})
                        expected_count=plan['initial_columns']
                        for rp in sorted(phase.glob('iter*/result.json')):
                            recorded=read(rp)
                            if 'iteration' not in recorded:continue
                            assert recorded.get('columns_before',recorded['columns']-recorded['added'])==expected_count
                            assert recorded['columns']==expected_count+recorded['added'];expected_count=recorded['columns']
                        assert len(pr['columns'])==expected_count
                    phase_result=phase_results[phase];rr=read(cp.parent/'result.json')
                    before=rr.get('columns_before',rr['columns']-rr['added'])
                    assert before==rr['columns']-rr['added'] and before>0
                    columns=phase_result['columns'][:before];assert len(columns)==before
                    beta=F(c['beta']);costs={tuple(map(int,k.split(':'))):-F(v) for k,v in c['pi'].items()}
                    for Y in columns:
                        key=tuple(Y)
                        if key not in true_values:
                            v=stock_value(scope,Y);assert v['feasible'];true_values[key]=v['f']
                    minK=min(beta*true_values[tuple(Y)]+sum((costs.get((s['i'],y),F(0))
                        for s,y in zip(scope['stations'],Y)),F(0)) for Y in columns)
                    assert minK==F(c['true_column_min_exact'])
                    assert min(F(c['a_raw']),minK)==F(c['a_true_RMP_exact'])
                    residual_checks.append(dict(certificate=cp.relative_to(ROOT).as_posix(),Q_SHA=data['Q_SHA'],
                        C_Q_exact=str(cq),actual_RMP_columns=before,true_column_min_exact=str(minK),
                        Q_residual_and_column_min_recomputed=True))
                check=primal_record(m,point);assert check['qualified'] and abs(check['objective']-data['upper'])<=1e-8
            sp=ROOT/spec['support_result'];sr=read(sp);sf=sp.parent/'all_supports'
            assert sr['Q_SHA']==data['Q_SHA'];saved=load_gz(sf/'dual_certificate.json.gz')
            with gp.read(str(sf/'model.mps'),env=env) as sm:
                model_reads+=1;s_matrix=exact_matrix(sm)
                assert s_matrix['variables']==matrix['variables'] and s_matrix['constant']==matrix['constant']
                assert all(s_matrix['rows'].get(k)==v for k,v in matrix['rows'].items())
                source_data=read(Path(sr['coupled_source'])/'result.json')
                for index,rec in enumerate(source_data['supports']):
                    p=audit_price(ROOT/rec['price_path'],prices)
                    assert p['complete_domain'] and p['scope']==scope and p['beta']==rec['beta']
                    beta=F(p['beta']);actual_beta=float(beta) if abs(beta)>=F(1e-12) else 0.
                    terms={'G':actual_beta} if actual_beta else {}
                    correction=min((F(actual_beta)-beta)*F(scope[k]) for k in ('gamma_L','gamma_U'))
                    for s in scope['stations']:
                        errors=[]
                        for y in s['support']:
                            original=F(p['d_exact'][f'{s["i"]}:{y}']);actual=float(original)
                            actual=actual if abs(actual)>=1e-12 else 0.
                            if actual:terms[f'state_{s["i"]}_{y}']=actual
                            errors.append(F(actual)-original)
                        correction+=min(errors)
                    expected=dict(name=f'r153_coupled_support_{index:05}',sense='>',terms=terms,
                        rhs=outward(F(p['lower'])+correction,False))
                    assert rec['row']==expected and F(rec['transport_exact'])==correction
                expected_rows={r['row']['name']:r['row'] for r in source_data['supports']}
                assert set(s_matrix['rows'])-set(matrix['rows'])==set(expected_rows)
                for name,r in expected_rows.items():
                    assert s_matrix['rows'][name]==dict(sense=r['sense'],rhs=F(r['rhs']),terms={k:F(v) for k,v in r['terms'].items()})
                support_lower=independent_residual(s_matrix,next(iter(bound_records.values())),saved)
                assert F(sr['records'][-1]['L'])<=support_lower
                support_point=load_gz(sf/'solution.json.gz');support_primal=primal_record(sm,support_point)
                assert support_primal['qualified'] and abs(support_primal['objective']-sr['records'][-1]['U'])<=1e-8
                known=[support_lower,reference_lower]
                known += [F(r['lower']) for r in certificates+refinements if any(part.startswith(role+'_') for part in Path(r['path']).parts)]
                for previous_dual in sorted((OUT/'support_LP').glob(role+'*/all_supports/dual_certificate.json.gz')):
                    if previous_dual.resolve()==(sf/'dual_certificate.json.gz').resolve():continue
                    previous_result=read(previous_dual.parent.parent/'result.json')
                    assert previous_result['Q_SHA']==data['Q_SHA']
                    previous_source=read(Path(previous_result['coupled_source'])/'result.json')
                    previous_rows={r['row']['name']:r['row'] for r in previous_source['supports']}
                    if not all(expected_rows.get(k)==v for k,v in previous_rows.items()):continue
                    previous_certificate=load_gz(previous_dual)
                    assert set(previous_certificate['multipliers'])==set(matrix['rows'])|set(previous_rows)
                    added_zero=sorted(set(s_matrix['rows'])-set(previous_certificate['multipliers']))
                    extended=dict(previous_certificate,multipliers=dict(previous_certificate['multipliers'],
                        **{k:0. for k in added_zero}))
                    recomputed=independent_residual(s_matrix,next(iter(bound_records.values())),extended)
                    assert F(previous_result['records'][-1]['L'])<=recomputed;known.append(recomputed)
                    inherited_support_checks.append(dict(role=role,source_dual=previous_dual.relative_to(ROOT).as_posix(),
                        source_dual_SHA=sha(previous_dual),current_model_SHA=sha(sf/'model.mps'),
                        additional_zero_multiplier_rows=added_zero,recomputed_lower_exact=str(recomputed),
                        recomputed_on_current_qualified_matrix=True,old_LP_not_reread=True))
                assert F(data['lower'])<=max(known)
                support_checks.append(dict(role=role,source=sp.relative_to(ROOT).as_posix(),model_SHA=sha(sf/'model.mps'),
                    exact_lower=str(support_lower),primal=support_primal,all_original_Q_rows_and_columns_preserved=True))
            penalty_observations=[]
            for name,pnt in [('current_Q_optimum',load_gz(OUT/'reference'/role/'direct/solution.json.gz')),
                             ('selected_coupled_upper',point)]:
                H=sum((F(s['omega'])*abs(F(s['c'])*y-1)*F(pnt[f'state_{s["i"]}_{y}'])
                    for s in scope['stations'] for y in s['support']),F(0))
                Pe=matrix['constant']+sum((v['objective']*F(pnt[k]) for k,v in matrix['variables'].items() if k!='G'),F(0))
                penalty_observations.append(dict(point=name,Pe_exact=str(Pe),H_exact=str(H),
                    Pe_minus_H=float(Pe-H),G=pnt['G'],slack_not_presumed_to_explain_failure=True))
            primals.append(dict(role=role,source=source.relative_to(ROOT).as_posix(),source_SHA=sha(source),Q_SHA=sha(qp),
                objective=check['objective'],Q_check=check,mass_exact=str(mass),negative_mass_exact=str(negative),
                maximum_marginal_residual=float(mismatch),true_completion_slack_exact=str(slack),
                penalty_observations=penalty_observations,
                numerical_primal_not_rational_certificate=True,upper_is_not_physical=True))
    write(OUT/'reuse_index.json',dict(fixed_science=SCIENCE,dependencies=list(deps.values()),old_carriers_repacked=0,
        stable_production_source='results/unified_exact_round137/matrix_frozen.json',
        production_candidate_source='results/unified_exact_round153/candidate_manifest.json',
        stable_R137_entry_unchanged=True,source_and_input_dependencies_bound_by_commit_and_SHA=True))
    write(target/'result.json',dict(PASS=True,qualified_iteration_certificates=len(certificates),certificates=certificates,
        selected_complete_Q_primals=primals,old_dependencies=len(deps),Optimize=0,Native_model_reads=model_reads,
        independent_Q_residual_checks=residual_checks,independent_free_Q_support_checks=support_checks,
        independent_current_reference_checks=reference_checks,
        inherited_support_duals_on_current_matrix=inherited_support_checks,
        primal_discovery_checks=primal_discovery_checks,
        primal_refresh_checks=primal_refresh_checks,
        price_evidence=prices,same_direction_refinements=refinements,
        no_performance_rerun=True,all_bounds_preserve_declared_numerical_policy=True))
    print(json.dumps(dict(PASS=True,certificates=len(certificates),primals=len(primals),dependencies=len(deps))),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
