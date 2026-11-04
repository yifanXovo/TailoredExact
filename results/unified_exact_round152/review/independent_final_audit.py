"""Independent saved-evidence review; stdlib only, no solver or producer.

This reconstructs the key full LP comparisons and bound transports from
serialized data. It does not assert rational Native optimality.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter, defaultdict
from itertools import combinations
import gzip, hashlib, json, math, subprocess, time

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def gz(p):
    with gzip.open(p,'rt',encoding='utf-8') as stream:
        return json.load(stream)


def inventory(scope,Y,pi):
    assert all(isinstance(y,int) for y in Y)
    stations = scope['stations']
    assert len(Y) == len(stations)
    assert all(y in s['support'] for s,y in zip(stations,Y))
    assert scope['Bminus'] <= sum(Y) <= scope['B']
    ratio = [F(s['c'])*y for s,y in zip(stations,Y)]
    S = sum(ratio,F(0))
    A = sum((abs(a-b) for a,b in combinations(ratio,2)),F(0))
    G = A/(len(stations)*S) if S else F(0)
    assert G <= F(scope['gamma_U'])
    P = sum((F(s['omega'])*abs(r-1) for s,r in zip(stations,ratio)),F(0))
    phi = max(F(scope['gamma_L']),G)+P
    price = phi-sum((F(pi[f'{s["i"]}:{y}']) for s,y in zip(stations,Y)),F(0))
    return price,phi


def mps(path):
    section = None
    senses, rows, rhs, bounds, variables = {}, defaultdict(dict), {}, {}, set()
    for raw in Path(path).read_text().splitlines():
        if not raw or raw.startswith('*'):
            continue
        f = raw.split()
        if f[0] in {'NAME','OBJSENSE','ROWS','COLUMNS','RHS','BOUNDS','ENDATA'}:
            section = f[0]
            continue
        if section == 'OBJSENSE':
            assert f == ['MIN']
        elif section == 'ROWS':
            assert f[1] not in senses
            senses[f[1]] = f[0]
        elif section == 'COLUMNS':
            assert 'MARKER' not in raw, 'Expected an entirely continuous saved LP'
            name = f[0]
            variables.add(name)
            for j in range(1,len(f),2):
                assert name not in rows[f[j]]
                rows[f[j]][name] = float(f[j+1])
        elif section == 'RHS':
            for j in range(1,len(f),2):
                rhs[f[j]] = float(f[j+1])
        elif section == 'BOUNDS':
            kind,_,name,*value=f
            lo,hi=bounds.get(name,(0.,math.inf))
            if kind=='LO': lo=float(value[0])
            elif kind=='UP': hi=float(value[0])
            elif kind=='FX': lo=hi=float(value[0])
            elif kind=='FR': lo,hi=-math.inf,math.inf
            elif kind=='MI': lo=-math.inf
            elif kind=='PL': hi=math.inf
            else: raise AssertionError(('unexpected bound/type',f))
            bounds[name]=(lo,hi)
    objective=next(k for k,v in senses.items() if v=='N')
    assert rhs.get(objective,0.)==0.
    return dict(senses=senses,rows=dict(rows),rhs=rhs,bounds={k:bounds.get(k,(0.,math.inf)) for k in variables},
                variables=variables,objective=objective)


def check_point(model,point):
    assert set(point)==model['variables']
    high=0.
    for name,sense in model['senses'].items():
        if sense=='N':continue
        lhs=math.fsum(a*point[k] for k,a in model['rows'].get(name,{}).items())
        rhs=model['rhs'].get(name,0.)
        residual=abs(lhs-rhs) if sense=='E' else max(0.,rhs-lhs) if sense=='G' else max(0.,lhs-rhs)
        high=max(high,residual)
    bound=max(max(lo-point[k],point[k]-hi,0.) for k,(lo,hi) in model['bounds'].items())
    value=math.fsum(a*point[k] for k,a in model['rows'][model['objective']].items())
    assert max(high,bound)<=1e-6
    return dict(constraint_residual=high,bound_residual=bound,objective=value)


def lp_record(role,variant,cache):
    key=role+'_'+variant
    if key not in cache:
        folder=BASE/'LP'/key
        record=read(folder/'result.json')
        assert record['qualified'] and record['all_variables_free']
        assert max(record['quality'].values())<=1e-6
        assert digest(folder/'model.mps')==record['model_SHA']
        model=mps(folder/'model.mps')
        point=gz(folder/'solution.json.gz')
        check=check_point(model,point)
        assert abs(check['objective']-record['L'])<1e-8
        dual=gz(folder/'dual.json.gz')
        bound_terms=[];infinite=[]
        for name,rc in dual['RC'].items():
            selected=model['bounds'][name][0 if rc>=0 else 1]
            if math.isfinite(selected):bound_terms.append(rc*selected)
            else:infinite.append(abs(rc))
        dvalue=math.fsum(v*model['rhs'].get(k,0.) for k,v in dual['Pi'].items())+math.fsum(bound_terms)
        assert abs(check['objective']-dvalue)<=1e-6
        assert max(infinite or [0])<=1e-12
        check.update(dual_objective=dvalue,primal_dual_gap=check['objective']-dvalue)
        cache[key]=(record,model,point,check)
    return cache[key]


def main():
    start=time.perf_counter();calls=[]
    for path in sorted(BASE.rglob('*call.json')):
        if path.name not in {'call.json','joint_call.json'}:continue
        call=read(path);returned=read(path.with_name(path.name.replace('call','return')))
        assert returned['Status'] in (2,3,9)
        calls.append((str(path.relative_to(BASE)),call.get('kind','LP'),returned['Status']))
    assert len(calls)==274
    prices=[];upper_vectors=0
    for path in sorted(BASE.rglob('result.json')):
        record=read(path)
        if not all(k in record for k in ('decision','pi','scope','lower','upper','stocks')):continue
        if path.parts[len(BASE.parts)].startswith('qualification_aggregate'):continue
        true=[]
        for candidate in record['stocks']:
            value,_=inventory(record['scope'],candidate['Y'],record['pi'])
            assert abs(float(value)-candidate['price'])<=1e-10
            true.append(value);upper_vectors+=1
        if record['upper'] is not None:
            assert true and F(record['upper'])>=min(true)
        if record['lower'] is not None and record['upper'] is not None:
            assert record['lower']<=record['upper']+1e-7
        if 'active_bins' in record:
            nodes=record['active_bins']
            components=[b['lower'] for b in nodes if not b['empty']]
            if record['zero_lower'] is not None:components.append(record['zero_lower'])
            assert record['lower']==(min(components) if components else None)
            intervals=sorted(b['interval'] for b in nodes)
            if record['denominator_scope']['upper']>0:
                assert intervals[0][0]<=record['denominator_scope']['lower']
                assert intervals[-1][1]>=record['denominator_scope']['upper']
                assert all(a[1]>=b[0] for a,b in zip(intervals,intervals[1:]))
        if record['decision']=='SEPARATION':assert record['lower']>record['threshold']+1e-7
        if record['decision']=='DIRECTION_NONSEPARATING':assert record['upper']<=record['threshold']+1e-9
        prices.append((str(path.relative_to(BASE)),record['decision']))
    assert len(prices)==52 and upper_vectors==156

    cache={};edges=[]
    for role,parent,child in [('N-B35-S','strongRN','RNfloor'),('N-B35-S','RNfloor','global'),
                              ('K-35-U','strongRN','global'),('N-C20-U','strongRN','global')]:
        old,om,_,oc=lp_record(role,parent,cache);new,nm,_,nc=lp_record(role,child,cache)
        assert om['variables']==nm['variables']
        assert om['bounds']==nm['bounds']
        for name in om['senses']:
            assert om['senses'][name]==nm['senses'][name]
            assert om['rows'].get(name,{})==nm['rows'].get(name,{})
            assert om['rhs'].get(name,0.)==nm['rhs'].get(name,0.)
        additions=set(nm['senses'])-set(om['senses'])
        rows=read(BASE/'LP'/f'{role}_{child}'/'rows.json')
        assert additions=={r['name'] for r in rows} and len(rows)==1
        for row in rows:
            assert nm['rows'][row['name']]==row['terms']
            assert nm['rhs'].get(row['name'],0.)==row['rhs']
            assert nm['senses'][row['name']]=={'<':'L','>':'G','=':'E'}[row['sense']]
        edges.append(dict(role=role,parent=parent,child=child,parent_L=old['L'],child_L=new['L'],
                          gain=new['L']-old['L'],old_semantics_identical=True,new_row_readback=True,
                          parent_check=oc,child_check=nc))

    floor=read(BASE/'oracle/N-B35-S_strong_zero/result.json')
    scope=read(BASE/'domains/N-B35-S/domain.json')['scope']
    assert floor['scope']==scope and all(v==0 for v in floor['pi'].values())
    assert len(floor['active_bins'])==6
    assert all(b['solved'] and not b['empty'] for b in floor['active_bins'])
    for node in floor['active_bins']:
        bound=node['result'];assert bound['Status'] in (2,9)
        admitted=bound['native_bound']-bound['numerical_guard']-bound['objective_correction']
        assert abs(bound['lower']-admitted)<1e-14
        assert node['lower']<=max(floor['fallback_lower'],admitted)+1e-14
    floor_row=read(BASE/'LP/N-B35-S_RNfloor/rows.json')[0]
    assert floor_row['rhs']==floor['lower']
    assert floor_row['terms']=={'G':1.,**{f'e_{s["i"]}':s['omega'] for s in scope['stations'] if s['omega']}}

    supports=[]
    for role in ('N-B35-S','K-35-U','N-C20-U'):
        folder=BASE/'global'/f'{role}_global';bundle=read(folder/'result.json')
        scope=read(BASE/'domains'/role/'domain.json')['scope'];assert bundle['scope']==scope
        last=bundle['iterations'][-1];pricing=read(folder/f'iter{last["iteration"]:02}'/'pricing/result.json')
        assert pricing['scope']==scope
        delta=sum(max(F(last['pi'][f'{s["i"]}:{y}'])-F(pricing['pi'][f'{s["i"]}:{y}'])
                      for y in s['support']) for s in scope['stations'])
        assert F(last['alpha'])<=F(pricing['lower'])-delta
        row=bundle['rows'][0];assert row['rhs']==last['alpha']
        expected={'G':1.,**{f'e_{s["i"]}':s['omega'] for s in scope['stations'] if s['omega']}}
        expected.update({f'state_{i}_{y}':-v for key,v in last['pi'].items() for i,y in [key.split(':')] if v})
        assert row['terms']==expected
        call=pricing['calls'][0];assert call['Status'] in (2,9) and call['bound_status_qualified']
        admitted=call['native_bound']-call['numerical_guard']-call['objective_correction']
        assert abs(pricing['lower']-max(pricing['fallback_lower'],admitted))<1e-14
        supports.append(dict(role=role,full_scope=True,lower=pricing['lower'],upper=pricing['upper'],
                             threshold=pricing['threshold'],transport_exact=str(delta),alpha=last['alpha'],
                             Native_status=call['Status'],negative_intercept_retained=last['alpha']<0))

    receipts=[]
    for path in sorted((BASE/'fees').glob('*/receipt.json')):
        r=read(path);assert r['exit_observed'] and not r['timeout']
        assert r['outer_seconds']>=0
        receipts.append(dict(label=path.parent.name,**r))
    ordered=sorted(receipts,key=lambda r:r['start_unix'])
    assert all(a['end_unix']<=b['start_unix'] for a,b in zip(ordered,ordered[1:])), 'Timed process overlap'
    external=read(BASE/'infra/external_costs.json')['processes']
    charge=math.fsum(r['G1_seconds'] for r in receipts)+math.fsum(r['outer_seconds'] for r in external)
    assert abs(charge-read(BASE/'cost_report.json')['charged_new_experiment_seconds'])<1e-8
    assert sum(r['exit_code']!=0 for r in receipts)==7
    manifest=read(BASE/'source_manifest.json')
    for name,sha in manifest['research_sources'].items():assert digest(ROOT/name)==sha,name
    snapshot_count=0
    for path in (BASE/'engineering/source_snapshots').glob('*.json'):
        snapshot=read(path)
        for name,sha in snapshot['files'].items():assert digest(BASE/'engineering/source_bytes'/f'{sha}.py.txt')==sha
        snapshot_count+=1
    changed=subprocess.check_output(['git','diff',manifest['fixed_dependency_base'],'--name-only','--','src','include','config',
                                     'scripts/paper_s2.py','scripts/paper_s2_round137.py'],cwd=ROOT,text=True)
    assert not changed.strip()
    pe=Path('E:/codes/ExactEBRP-work/build-cache/round151/ExactEBRP.exe')
    dll=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
    assert digest(pe)==manifest['production_PE_SHA'] and digest(dll)==manifest['Native_DLL_SHA']
    output=dict(PASS=True,Native_calls=len(calls),Native_returns=len(calls),call_kinds=dict(Counter(c[1] for c in calls)),
                pricing_records=len(prices),pricing_decisions=dict(Counter(p[1] for p in prices)),
                independently_recomputed_inventory_uppers=upper_vectors,key_LP_edges=edges,
                floor_scope_and_six_bin_lower_aggregation=True,global_supports=supports,
                charged_seconds_before_this_final_review=charge,receipt_count=len(receipts),failed_outer_attempts=7,
                timed_receipts_serial=True,source_snapshot_count=snapshot_count,source_manifest_matches=True,
                unchanged_production_source_and_runtime=True,new_Optimize=0,new_Native_calls=0,
                reviewer_script_SHA256=digest(Path(__file__)),
                proof_policy='Exact arithmetic for inventory objectives/transport; floating Native bounds and LP certificates retain the existing numerical policy.')
    output['nested_script_seconds']=time.perf_counter()-start
    destination=Path(__file__).with_name('independent_final_audit.json')
    assert not destination.exists()
    destination.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
