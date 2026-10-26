"""Portable standard-library evidence reconstruction; never loads a solver."""
import argparse, ast, csv, hashlib, json, math, re
from pathlib import Path

TOL = 1e-7
ROUND = 'results/unified_exact_round107'

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        while block:=f.read(1024*1024): h.update(block)
    return h.hexdigest()

def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f))

def lines(p):
    return [json.loads(s) for s in Path(p).read_text(encoding='utf-8').splitlines() if s]

def write(p,value):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n')

def scalar(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')) if isinstance(value,(dict,list)) else value

def table(p,data):
    if not data: return
    keys=list(dict.fromkeys(k for r in data for k in r))
    with Path(p).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader()
        w.writerows({k:scalar(v) for k,v in r.items()} for r in data)

def portable(root,value):
    s=str(value).replace('\\','/')
    for marker in ['results/','reference/','scripts/','src/','include/','tests/']:
        if marker in s: return root/s[s.index(marker):]
    p=Path(s);assert not p.is_absolute(),('unsupported evidence path',value)
    return root/p

def number(v):
    return float(v) if v not in ('',None) else None

def close(a,b):
    return abs(a-b)<=TOL

def instance(root,p):
    text=(root/p['input_path']).read_text(encoding='utf-8')
    def vector(name):return ast.literal_eval(re.search(r'^\s*'+name+r'\s*=\s*(\[[^\n]*\])',text,re.M)[1])
    w=vector('weights')
    if abs(max(w[1:])-10)<1e-6:w=[a/10 for a in w]
    return dict(b=vector('initial'),D=vector('target'),c=vector('capacities'),xy=vector('points'),w=w,Q=p['Q_vector'])

def objective(a,Y,lam):
    r=[Y[i]/a['D'][i] for i in range(1,len(Y))];S=sum(r)
    G=sum(abs(x-y) for j,x in enumerate(r) for y in r[j+1:])/(len(r)*S) if S>0 else 0
    P=sum(a['w'][i]*abs(r[i-1]-1) for i in range(1,len(Y)))
    return dict(G=G,P=P,F=G+lam*P,Y=Y)

def physical(root,p,witness):
    a=instance(root,p);Y=a['b'].copy();seen=set();cars=set();durations=[];returns=[];pickups=[]
    for route in witness['routes']:
        k=route.get('vehicle',route.get('vehicle_id'));assert k not in cars and 0<=k<len(a['Q']);cars.add(k)
        nodes=route['nodes'];assert nodes[0]==nodes[-1]==0
        operations={}
        for op in route['operations']:
            i,x,y=(op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else op
            assert i not in operations and x>=0 and y>=0 and int(x)==x and int(y)==y and bool(x)!=bool(y)
            operations[i]=(x,y)
        assert set(nodes[1:-1])==set(operations);load=0;pickup=0
        for i in nodes[1:-1]:
            assert 1<=i<len(Y) and i not in seen;seen.add(i);x,y=operations[i]
            load+=x-y;pickup+=x;assert 0<=load<=a['Q'][k]
            Y[i]+=y-x;assert 0<=Y[i]<=a['c'][i]
        travel=sum(math.hypot(a['xy'][x][0]-a['xy'][y][0],a['xy'][x][1]-a['xy'][y][1])/1.5 for x,y in zip(nodes,nodes[1:]))
        duration=travel+(p['pickup_seconds']+p['drop_seconds'])*pickup
        assert duration<=p['T_seconds']+TOL;durations.append(duration);returns.append(load);pickups.append(pickup)
    assert sum(Y[1:])==sum(a['b'][1:])-sum(returns)
    result=objective(a,Y,p['lambda']);reported=witness.get('F',witness.get('objective'))
    assert reported is not None and close(result['F'],reported),(result,reported)
    return dict(result,maximum_duration=max(durations,default=0),pickups=pickups,return_loads=returns)

def bound(scope,value,witnesses):
    U=min((w['F'] for w in witnesses),default=math.inf)
    if scope['full_original']:
        assert scope['native_preconditions'] and value<=U+TOL
        return value
    cutoff=scope['cutoff'];assert math.isfinite(U) and cutoff+TOL>=U
    pieces=[dict(x) for x in scope['cover']];matched=0
    for piece in pieces:
        assert all(math.isfinite(piece[k]) for k in ['lower_g','upper_g','lower','cutoff'])
        assert 0<=piece['lower_g']<=piece['upper_g'] and piece['cutoff']+TOL>=cutoff
        if (piece['id'],piece['lower_g'],piece['upper_g'],piece['cutoff'])==(scope['leaf'],scope['lower_g'],scope['upper_g'],cutoff):
            assert scope['native_preconditions'] and scope['model_sha256'];matched+=1
            piece['lower']=max(piece['lower'],value)
        for w in witnesses:
            if piece['lower_g']-TOL<=w['G']<=piece['upper_g']+TOL and w['F']<=piece['cutoff']+TOL:
                assert piece['lower']<=w['F']+TOL
    assert matched==1;covered=0;L=cutoff
    for piece in sorted(pieces,key=lambda x:x['lower_g']):
        assert piece['lower_g']<=covered;covered=max(covered,piece['upper_g'])
        L=min(L,piece['lower'],piece['cutoff'])
    assert pieces and covered>=min(cutoff,scope['gmax']) and L<=U+TOL
    return L

def journal(root,p,d):
    observations=read(d/'observations.json');calls={};witnesses=[];bounds=[];returned=set();not_started=set()
    trace=[]
    settings=dict(read_return_code=0,Threads=1,Seed=p.get('gurobi_seed',0),Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
    for seq,r in enumerate(observations,1):
        e=r['payload'];assert e['sequence']==seq
        raw=d/'journal'/f'event_{seq}.json';assert sha(raw)==r['sha256'] and read(raw)==e
        commit=(d/'journal'/f'event_{seq}.commit').read_text().split();assert int(commit[1])==seq and int(commit[3])==raw.stat().st_size and commit[4]==sha(raw)
        if e['kind']=='identity':
            assert seq==1 and e['input_sha256']==p['input_sha256']
            assert (e['lambda'],e['T'],e['pickup_seconds'],e['drop_seconds'])==(p['lambda'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'])
        elif e['kind']=='call':
            assert e['call'] not in calls and sha(portable(root,e['model_path']))==e['model_sha256']
            assert e['settings']==settings;calls[e['call']]=e
        elif e['kind']=='witness':
            w=physical(root,p,e);assert close(w['G'],e['G']) and close(w['P'],e['P'])
            witnesses.append(dict(w,source=e['source'],sequence=seq,available=r['effective_available_seconds']))
        elif e['kind']=='bound':
            assert not e['inconsistent']
            L=bound(calls[e['call']],e['native_bound'],witnesses) if e['global_available'] else None
            assert L is None and e['global_bound'] is None or L is not None and abs(L-e['global_bound'])<1e-10
            bounds.append(e)
        elif e['kind']=='returned':assert e['call'] in calls and e['return_code']==0;returned.add(e['call'])
        elif e['kind']=='not_started':assert not e['actual_Optimize'];not_started.add(e['call'])
        elif e['kind']=='witness_rejected':pass
        else:raise AssertionError(('journal failure/unknown kind',e))
        if witnesses:
            U=min(w['F'] for w in witnesses);L=max([0]+[x['global_bound'] for x in bounds if x['global_available']])
            assert L<=U+TOL
            trace.append(dict(sequence=seq,available=r['effective_available_seconds'],kind=e['kind'],U=U,L=L,gap=U-L))
    assert not returned&not_started and returned|not_started==set(calls)
    for e in bounds:
        if e['global_available']:bound(calls[e['call']],e['native_bound'],witnesses)
    return dict(calls=calls,witnesses=witnesses,bounds=bounds,started=len(calls)-len(not_started),returned=len(returned),not_started=len(not_started),trace=trace,returned_ids=returned,not_started_ids=not_started)

def fees(out):
    data=[];corrections={}
    for p in sorted((out/'fee_corrections').glob('*.json')):
        q=read(p);label=q.get('label',p.stem);corrections[label]=corrections.get(label,0)+q['additional_conservative_starts']
    for folder in sorted((out/'fees').iterdir()):
        launch=read(folder/'launch.json');receipt=read(folder/'receipt.json');declared=launch['conservative_process_starts']
        assert receipt['conservative_process_starts']==declared and not launch['engineering'] and not receipt['engineering']
        added=corrections.get(folder.name,0)
        data.append(dict(label=folder.name,outer_seconds=receipt['outer_seconds'],exit_code=receipt['exit_code'],stop_reason=receipt['stop_reason'],original_declared_starts=declared,additional_retained_correction_starts=added,conservative_process_starts=declared+added,wrapper_processes=launch.get('actual_wrapper_processes'),declared_children=launch.get('declared_native_children',launch.get('declared_children')),nested_seconds_added=False))
    assert set(corrections)<=set(x['label'] for x in data)
    return data

def native(root,out,campaigns,control_journals=()):
    records=[];scopes=[out/'qualification']+[c for c in campaigns]
    for base in scopes:
        for p in sorted(base.rglob('calls.csv')):
            rr=rows(p)
            for phase in sorted({r['phase'] for r in rr}):
                before=[r for r in rr if r['phase']==phase and r['stage']=='before']
                after=[r for r in rr if r['phase']==phase and r['stage']=='after']
                skipped=[r for r in rr if r['phase']==phase and r['stage']=='not_started_deadline']
                assert len(after)+len(skipped)<=len(before)
                records.append(dict(path=p.relative_to(root).as_posix(),phase=phase,intents=len(before),not_started=len(skipped),started=len(before)-len(skipped),returned=len(after),missing_after=len(before)-len(skipped)-len(after),native_seconds=sum(float(r['seconds']) for r in after)))
        for p in sorted(base.rglob('requests.jsonl')):
            qs=[r for r in lines(p) if r['kind']=='LP']
            if qs:
                legacy=[q for q in qs if 'native_Optimize_started' not in q]
                source='Actual per-request native_Optimize_started record'
                if legacy:
                    # Early real fixtures predate this observational field.
                    # A native return status plus the actual original optimize
                    # ledger/log is required; there is no default-True fallback.
                    assert len(legacy)==len(qs) and all(q['native_status'] in [2,3] for q in legacy),(p,[q['native_status'] for q in legacy])
                    for q in legacy:assert sha(portable(root,q['canonical_path']))==q['canonical_sha256']
                    folder=p.parent.parent;ledger=folder/'paper_optimize_ledger.csv'
                    if ledger.exists():
                        rr=[r for r in rows(ledger) if r['solve_kind']=='LP']
                        assert len(rr)==len(legacy) and all(int(r['optimize_return_code'])==0 for r in rr)
                        assert [r['native_status'] for r in rr]==[{2:'OPTIMAL',3:'INFEASIBLE'}[q['native_status']] for q in legacy]
                        assert [r['model_sha256'] for r in rr]==[q['canonical_sha256'] for q in legacy]
                        source='Historical LP native Optimize/return ledger and canonical SHA'
                    else:
                        log=folder/'native.log';text=log.read_text(encoding='utf-8')
                        assert all(q['native_status']==2 for q in legacy) and text.count('Solved in ')==len(legacy) and text.count('Optimal objective')==len(legacy)
                        source='Historical real LP returned status, canonical SHA and native log with exact LP solve count'
                started=len(legacy)+sum(q.get('native_Optimize_started',False) for q in qs if q not in legacy)
                records.append(dict(path=p.relative_to(root).as_posix(),phase='LP',intents=len(qs),not_started=len(qs)-started,started=started,returned=started,missing_after=0,native_seconds=None,count_source=source))
    # Production CLI cli01 threw only after the original LP Optimize returned.
    # Its emergency counter/request stream cannot erase the committed native call.
    for folder in sorted((out/'qualification').rglob('journal')):
        if not folder.is_dir():continue
        ee=[read(p) for p in sorted(folder.glob('event_*.json'),key=lambda p:int(p.stem.split('_')[-1]))]
        cc={e['call']:e for e in ee if e['kind']=='call' and '_lp.' in e.get('native_log_path','').lower()}
        returned={e['call'] for e in ee if e['kind']=='returned'}
        not_started={e['call'] for e in ee if e['kind']=='not_started'}
        recorded=sum(q['kind']=='LP' and (q.get('native_Optimize_started',False) or 'native_Optimize_started' not in q and q['native_status'] in [2,3])
            for p in folder.parent.rglob('requests.jsonl') for q in lines(p))
        actual=len(set(cc)-not_started);assert actual>=recorded
        if actual>recorded:
            assert recorded==0 and set(cc)<=returned|not_started
            records.append(dict(path=folder.relative_to(root).as_posix(),phase='LP_recovered_after_metadata_failure',
                intents=len(cc),not_started=len(set(cc)&not_started),started=actual,returned=len(set(cc)&returned),missing_after=0,native_seconds=None,
                recovery_source='Raw native call/returned journal, independently of emergency controller counters'))
    for folder,arm,j in control_journals:
        for phase in sorted({'LP' if '_lp.' in e.get('native_log_path','').lower() else arm+'_master' for e in j['calls'].values()}):
            selected={i for i,e in j['calls'].items() if ('LP' if '_lp.' in e.get('native_log_path','').lower() else arm+'_master')==phase}
            skipped=selected&j['not_started_ids'];returned=selected&j['returned_ids']
            records.append(dict(path=(folder/'journal').relative_to(root).as_posix(),phase=phase,intents=len(selected),not_started=len(skipped),
                started=len(selected)-len(skipped),returned=len(returned),missing_after=len(selected-skipped-returned),native_seconds=None))
    return records

def cover(d,U):
    trace=rows(d/'external/global_bound_trace.csv');leaves=rows(d/'external/paper_leaf_ledger.csv')
    previous=0; timeline=[]
    for n,r in enumerate(trace,1):
        upper=float(r['verified_global_upper_bound']);active=number(r['active_leaf_valid_lower_bound']);other=number(r['other_open_leaf_min_valid_lower_bound'])
        candidates=[upper]+[v for v in [active,other] if v is not None]
        lower=min(candidates);reported=float(r['valid_global_lower_bound'])
        assert close(lower,reported),(r,lower)
        assert reported>=previous-TOL and reported<=upper+TOL;previous=reported
        timeline.append(dict(row=n,**r,recomputed_complete_cover_bound=lower))
    live=[r for r in leaves if r['status'] not in ['replaced','coalesced']]
    assert live
    covered=0
    for r in sorted(live,key=lambda x:float(x['gamma_L'])):
        lo,hi=float(r['gamma_L']),float(r['gamma_U']);assert lo<=hi and lo<=covered+TOL
        covered=max(covered,hi)
    assert covered+TOL>=min(U,1)
    values=[float(r['lower_bound']) for r in live]
    assert all(v>=-TOL for v in values)
    lower=min([U]+values)
    assert close(lower,previous),(lower,previous)
    return dict(L=lower,certificate=U-lower<=TOL,live_leaves=len(live),open_leaves=sum(r['status'] in ['open','invalid','terminal_ready'] for r in live),covered_gini_upper=covered,timeline=timeline,leaves=leaves)

def endpoint(root,launch,ident,d,j):
    completion=read(d/'completion.json');result=read(d/'result.json')
    assert completion['stop_reason']=='normal_return' and completion['returncode']==0 and completion['within_cap']
    p=launch['panel'];assert sha(root/p['input_path'])==p['input_sha256']
    final=physical(root,p,result);U=final['F'];final_witnesses=j['witnesses']+[final]
    for b in j['bounds']:
        if b['global_available']:bound(j['calls'][b['call']],b['native_bound'],final_witnesses)
    if launch['arm'] in ['ENS-C','FRONTIER-STRUCT']:
        c=cover(d,U);L=c['L'];certificate=c['certificate']
    elif launch['arm']=='GLOBAL-STRUCT':
        s=read(d/'external/round106/summary.json');c=None
        runtime=read(d/'external/round106/runtime.json')
        assert runtime['dll_sha256']==ident['DLL_sha256'] and runtime['runtime']=='13.0.2'
        assert runtime['parameters']==dict(read_return_code=0,Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
        returned=[q for q in rows(d/'external/round106/calls.csv') if q['phase']=='master' and q['stage']=='after']
        assert len(returned)==1 and int(returned[0]['status'])==s['native_status']
        native_bound=max([0]+[e['native_global_bound'] for e in lines(d/'external/round106/events.jsonl') if e['native_global_bound'] is not None])
        if s['final_native_bound_qualified']:
            final_attribute=float(returned[0]['bound']);assert close(final_attribute,s['final_native_bound'])
            native_bound=max(native_bound,final_attribute)
        # R106 also accumulates MIP callback bounds between MIPSOL events.
        # Their exact post-return qualified accumulator is retained in the raw
        # summary; do not manufacture missing per-callback precision from logs.
        assert s['LB']+TOL>=native_bound and not s['status'].startswith('ERROR')
        if s['final_native_bound_qualified']:
            assert close(s['LB'],native_bound),'qualified final native/event bound differs from accumulator'
            L=native_bound
        else:L=s['LB']
        certificate=not s['unresolved_candidate'] and U-L<=TOL
    else:
        c=None;L=max([0]+[b['global_bound'] for b in j['bounds'] if b['global_available']])
        if result['native_mip_best_bound_available']:L=max(L,result['lower_bound'])
        certificate=result['gurobi_status']==2 and U-L<=TOL
        assert result['gurobi_model_fingerprint']==p['reference']['fingerprint'] and result['gurobi_native_domain_audit_passed']
    assert L<=U+TOL and close(L,result['lower_bound']) and close(U,result['upper_bound'])
    assert certificate==result['strict_certified_original_problem']
    audit=read(d/'audit.json');assert audit['passed']
    assert close(U,audit['endpoint']['U']) and close(L,audit['endpoint']['L']) and certificate==audit['endpoint']['certificate']
    return dict(U=U,L=L,gap=U-L,relative_gap=(U-L)/abs(U) if abs(U)>TOL else 0,certificate=certificate,status=result['status'],physical=final,cover=c,completion=completion,result=result)

def event_data(root,p,folder):
    data=[];a=instance(root,p)
    if not (folder/'events.jsonl').exists():return data
    for e in lines(folder/'events.jsonl'):
        stock=[a['b'][0]]+e['Y'];F=objective(a,stock,p['lambda'])
        assert close(F['F'],e['Ftrue']) and e['model_objective']+TOL>=F['F']
        seen=set();rebuilt=a['b'].copy()
        for k,operation in enumerate(e['operations']):
            assert len(operation)==p['V']
            for i,q in enumerate(operation,1):
                assert int(q)==q
                if q:assert i not in seen;seen.add(i);rebuilt[i]-=q
        assert rebuilt==stock
        vector=folder/f'candidate_{e["event"]}.sol'
        assert vector.exists();values={}
        for line in vector.read_text(encoding='utf-8').splitlines():
            if not line or line.startswith('#'):continue
            key,value=line.split();values[key]=float(value)
        for i,Y in enumerate(e['Y'],1):
            assert abs(values.get(f'Y_{i}',0)-Y)<=1e-5 and abs(values.get(f'state_{i}_{Y}',0)-1)<=1e-5
            for k,operations in enumerate(e['operations']):
                q=operations[i-1]
                assert abs(values.get(f'p_{k}_{i}',0)-max(q,0))<=1e-5 and abs(values.get(f'd_{k}_{i}',0)-max(-q,0))<=1e-5
                assert abs(values.get(f'z_{k}_{i}',0)-int(q!=0))<=1e-5
        data.append(dict(e,candidate_SHA=sha(vector)))
    return data

def mechanism(root,launch,d):
    arm=launch['arm'];p=launch['panel'];all_events=[];requests=[];cuts=[];acceptance=[];cache=[];remaps=[];semantic=[];summaries=[];physical_ubs=[];attempts=[];feedback=[]
    if arm=='GLOBAL-STRUCT':
        folder=d/'external/round106';folders=[folder];summaries=[read(folder/'summary.json')]
    elif arm=='FRONTIER-STRUCT':
        folder=d/'external/round107';requests=lines(folder/'requests.jsonl')
        if (folder/'semantic_rows.jsonl').exists():semantic=lines(folder/'semantic_rows.jsonl')
        folders=[portable(root,q['evidence_dir']) for q in requests if q['kind']!='LP' and q['native_Optimize_started']]
        for q in requests:
            assert sha(portable(root,q['canonical_path']))==q['canonical_sha256']
            assert not q['optimal_close_by_dominance'] or q['qualified_local_bound']+TOL>=q['own_global_UB']
            assert not q['local_INF'] or not read(portable(root,q['evidence_dir'])/'summary.json')['domain_witness_embeds']
            assert not q['unresolved'] or not q['target_reached']
            if q['kind']=='LP':assert not q['fresh_canonical_MIP'] and not q['optimal_close_by_dominance']
        summaries=[read(f/'summary.json') for f in folders]
    else:
        return dict(statistics={},events=[],requests=[],cuts=[],acceptance=[],cache=[],remaps=[],semantic=[],modes=[],physical_ubs=[],attempts=[],feedback=[])
    for f in folders:
        request=read(f/'summary.json').get('request',0)
        raw_summary=read(f/'summary.json')
        ev=event_data(root,p,f);all_events.extend(dict(e,evidence_dir=f.relative_to(root).as_posix()) for e in ev)
        assert len(ev)==raw_summary['events']
        assert sum(e['outcome']=='FEASIBLE_PHYSICAL' for e in ev)==raw_summary['feasible_candidates']
        assert sum(e['physical_ub_events'] for e in ev)<=raw_summary['new_physical_UBs']
        by_event={e['event']:e for e in ev}
        local=rows(f/'lazy.csv');cuts.extend(dict(r,request=request) for r in local)
        assert len(local)==raw_summary['lazy_calls']
        for r in local:
            assert int(r['api_return'])==0 and float(r['violation'])>max(TOL,1e-6*max(1,abs(float(r['activity'])),abs(float(r['rhs']))))
            mapped=rows(f/f'row_{r["row"]}.csv');values={}
            for line in (f/f'candidate_{r["event"]}.sol').read_text().splitlines():
                if line and not line.startswith('#'):
                    n,v=line.split();values[n]=float(v)
            activity=sum(float(x['coefficient'])*values.get(x['variable'],0) for x in mapped)
            assert close(activity,float(r['activity']))
        for file,target in [('submission_acceptance.csv',acceptance),('cache.csv',cache),('remap.csv',remaps)]:
            if (f/file).exists():target.extend(dict(r,request=request) for r in rows(f/file))
        if (f/'cache.csv').exists():
            hits=rows(f/'cache.csv');assert len(hits)==raw_summary['cache_hits']
            assert sum(int(r['origin_request'])!=0 and r['origin_request']!=r['current_request'] for r in hits)==raw_summary['cross_request_hits']
        for file in sorted(f.glob('physical_ub_*.json'),key=lambda x:int(x.stem.split('_')[-1])):
            w=read(file);v=physical(root,p,w)
            physical_ubs.append(dict(request=request,witness_path=file.relative_to(root).as_posix(),witness_SHA=sha(file),routes=w['routes'],**v))
        assert len(list(f.glob('physical_ub_*.json')))==raw_summary['new_physical_UBs']
        for file in sorted(f.glob('submission_*.json'),key=lambda x:int(x.stem.split('_')[-1])):
            value=read(file);assert value['api_return']==0 and value['physical_UB_established']
            attempts.append(dict(request=request,path=file.relative_to(root).as_posix(),SHA=sha(file),**value))
        assert len(list(f.glob('submission_*.json')))==raw_summary['submission_attempts']
        if (f/'feedback.jsonl').exists():feedback.extend(dict(q,request=request) for q in lines(f/'feedback.jsonl'))
        if (f/'candidate_audit.jsonl').exists():
            audits=lines(f/'candidate_audit.jsonl');assert len(audits)==2*len(ev)
            for r in audits[1::2]:assert r['base_rows_valid'] and r['bounds_integrality_valid'] and r['epigraph_valid'] and close(r['Ftrue'],by_event[r['event']]['Ftrue'])
    fleets={tuple(tuple(v) for v in e['operations']) for e in all_events};inventories={tuple(e['Y']) for e in all_events}
    modes={};
    for e in all_events:
        for k,op in enumerate(e['operations']):
            key=(k,tuple(op))
            if key not in modes:modes[key]=dict(request=e.get('request',0),event=e['event'],vehicle=k,operations=op,Y=e['Y'],outcome=e['outcome'],candidate_SHA=e['candidate_SHA'])
    sums=['cache_hits','cross_request_hits','remapped_rows','structural_proofs','lazy_calls','rejected_events','feasible_candidates','unknown_candidates','new_physical_UBs','submission_attempts','master_calls','oracle_calls','iis_calls','master_inclusive_seconds','master_exclusive_seconds','oracle_seconds','separation_seconds','audit_mapping_seconds','callback_other_seconds']
    statistics={k:sum(s.get(k,0) for s in summaries) for k in sums}
    statistics.update(events=len(all_events),distinct_event_fleets=len(fleets),distinct_event_Y=len(inventories),distinct_event_vehicle_modes=len(modes),repeat_event_fleets=len(all_events)-len(fleets),A_lazy_calls=sum(r['family'].startswith('A_') for r in cuts),B_lazy_calls=sum(r['family'].startswith('B_') for r in cuts),FULL_lazy_calls=sum(r['family']=='FULL' for r in cuts),native_exact_vector_acceptances=sum(int(r['final_native_accepted']) for r in acceptance),new_global_physical_UB_events=sum(e['physical_ub_events'] for e in all_events),new_semantic_rows=len(semantic),request_count=len(requests),LP_requests=sum(q['kind']=='LP' for q in requests),partial_requests=sum(q['kind']=='PARTIAL_TARGET' for q in requests),terminal_requests=sum(q['kind']=='TERMINAL' for q in requests),actual_target_reached=sum(q['target_reached'] for q in requests),local_INF_requests=sum(q['local_INF'] for q in requests),dominance_closed_requests=sum(q['optimal_close_by_dominance'] for q in requests),no_domain_Start_requests=sum(q['kind']!='LP' and not q['domain_start'] for q in requests),unresolved_requests=sum(q['unresolved'] for q in requests))
    statistics.update(physical_UB_witness_files=len(physical_ubs),submission_API0_attempts=len(attempts),submission_deferred_attempts=sum(q['deferred_at_MIPSOL'] for q in attempts),domain_feedback_skips=len(feedback),initial_physical_cache_hits=sum(int(q['initial']) for q in cache),B_EXACT_lazy_calls=sum(q['family']=='B_EXACT' for q in cuts),B_THRESHOLD_lazy_calls=sum(q['family']=='B_THRESHOLD' for q in cuts),B_event_vehicle_groups=len({(q['request'],q['event'],q['vehicle']) for q in cuts if q['family'].startswith('B_')}),physical_UB_per_event=len(physical_ubs)/len(all_events) if all_events else None,first_new_physical_UB_event_seconds=min((e['published_seconds'] for e in all_events if e['physical_ub_events']),default=None))
    if arm=='GLOBAL-STRUCT':
        statistics['new_semantic_rows']=summaries[0]['pool_rows']
        assert len(list(folder.glob('row_*.csv')))==statistics['new_semantic_rows']
        # R106 did not emit R107's per-hit CSV. Reconstruct its actual pre-scan
        # cache from the physical startup and event-specific native oracle
        # returns. Cached startup modes are neither new nor cross-request proof.
        initial=set()
        for route in read(folder/'seed.json')['routes']:
            op=[0]*p['V']
            for operation in route['operations']:
                i,x,y=(operation['station'],operation['pickup'],operation['drop']) if isinstance(operation,dict) else operation
                op[i-1]=x-y
            initial.add((route['vehicle'],tuple(op)))
        known=set(initial);hits=0;initial_hits=0
        returned=rows(folder/'inner/calls.csv')
        by_sha={}
        for q in returned:
            if q['stage']=='after' and q['phase']=='oracle':by_sha.setdefault(q['model_sha256'],[]).append(q)
        for e in all_events:
            for k,op in enumerate(e['operations']):
                key=(k,tuple(op));hits+=key in known;initial_hits+=key in initial
            for k,op in enumerate(e['operations']):
                oracle=folder/f'event_{e["event"]}_k{k}/full.lp'
                if not oracle.exists():continue
                oracle_sha=sha(oracle);matched=by_sha.get(oracle_sha,[])
                assert matched
                # Identical native oracle matrices can repeat across events;
                # FEAS/INF are physical and therefore have identical cache keys.
                if any(int(q['status']) in [2,3] for q in matched):known.add((k,tuple(op)))
        assert hits==statistics['cache_hits'],('GLOBAL physical cache reconstruction',hits,statistics['cache_hits'])
        statistics['initial_physical_cache_hits']=initial_hits
        statistics['cache_count_source']='Physical startup modes and raw event-specific oracle returns'
    else:statistics['cache_count_source']='Actual per-event physical cache-hit CSV'
    for s in summaries:
        parts=[s.get(k,0) for k in ['master_exclusive_seconds','oracle_seconds','separation_seconds','audit_mapping_seconds','callback_other_seconds']]
        assert min(parts)>=-1e-6 and abs(sum(parts)-s['master_inclusive_seconds'])<1e-6
    return dict(statistics=statistics,events=all_events,requests=requests,cuts=cuts,acceptance=acceptance,cache=cache,remaps=remaps,semantic=semantic,modes=list(modes.values()),physical_ubs=physical_ubs,attempts=attempts,feedback=feedback)

def controller_tables(d,result):
    data={}
    for name,file in [('controller_AM','adaptive_mass_decision_ledger.csv'),('controller_targets','native_target_ledger.csv'),('controller_events','paper_tree_events.csv'),('controller_child_bounds','parent_child_bound_ledger.csv'),('controller_native','paper_optimize_ledger.csv'),('controller_LP_status','lp_status_ledger.csv')]:
        p=d/'external'/file;data[name]=rows(p) if p.exists() else []
    for r in data['controller_AM']:
        gap=float(r['U'])-float(r['B_p'])
        assert close(gap,float(r['proof_gap']))
        if gap>TOL:
            gl=(float(r['B_L'])-float(r['B_p']))/gap;gr=(float(r['B_R'])-float(r['B_p']))/gap
            assert close(gl,float(r['g_L_raw'])) and close(gr,float(r['g_R_raw']))
            gl=max(0,min(1,gl));gr=max(0,min(1,gr));eta=min(gl,gr);mu=(gl+gr)/2
            assert close(eta,float(r['eta'])) and close(mu,float(r['mu'])) and close(eta*mu,float(r['S_AM']))
            r['recomputed_AM_score']=eta*mu
    for r in data['controller_targets']:
        if int(r['target_reached']):
            assert float(r['native_bound'])+TOL>=float(r['target_bound']) and int(r['requeued']) and not int(r['exact_closure'])
    return data

def time_partition(arm,endpoint,mechanism,controller):
    r=endpoint['result'];c=endpoint['completion'];s=mechanism['statistics']
    lp=sum(float(q['solver_runtime']) for q in controller['controller_native'] if q['solve_kind']=='LP')
    if arm in ['ENS-C','FRONTIER-STRUCT']:
        master=sum(float(q['solver_runtime']) for q in controller['controller_native'] if q['solve_kind']!='LP')
    elif arm=='GLOBAL-STRUCT':master=s['master_inclusive_seconds']
    else:master=r['gurobi_runtime']
    startup=r['process_elapsed_at_exact_phase_start_seconds'] if arm!='P-GRB' else 0
    residual=c['process_wall_seconds']-startup-lp-master
    assert residual>=-1e-3,(arm,residual)
    result=dict(process_wall_seconds=c['process_wall_seconds'],fully_observed_outer_seconds=c['fully_observed_end_to_end_seconds'],
        startup_before_exact_phase_seconds=startup,HGA_diagnostic_overlapping_startup_seconds=r.get('hga_wall_time_seconds'),
        original_LP_native_inclusive_seconds=lp,master_native_inclusive_seconds=master,
        other_controller_setup_mapping_write_seconds=residual,
        AM_math_timer='NOT_SEPARATELY_MEASURED; included in controller residual',
        native_timers_added_to_outer_fee=False,
        partition_identity_seconds=startup+lp+master+residual)
    if arm in ['GLOBAL-STRUCT','FRONTIER-STRUCT']:
        result.update({k:s[k] for k in ['master_exclusive_seconds','oracle_seconds','separation_seconds','audit_mapping_seconds','callback_other_seconds']})
        assert abs(sum(result[k] for k in ['master_exclusive_seconds','oracle_seconds','separation_seconds','audit_mapping_seconds','callback_other_seconds'])-master)<1e-6
    else:result['master_callback_partition']='NOT_SEPARATELY_MEASURED on unchanged control; included in native inclusive'
    return result

def paired(arms):
    data=[]
    for a in arms:
        if a['arm'] not in ['GLOBAL-STRUCT','FRONTIER-STRUCT']:continue
        for c in arms:
            if (c['campaign'],c['id'])!=(a['campaign'],a['id']) or c['arm'] not in ['P-GRB','ENS-C','GLOBAL-STRUCT'] or c['arm']==a['arm']:continue
            classification='both_certified' if a['certificate'] and c['certificate'] else 'candidate_certified_control_censored' if a['certificate'] else 'control_certified_candidate_censored' if c['certificate'] else 'both_censored'
            data.append(dict(campaign=a['campaign'],id=a['id'],candidate=a['arm'],control=c['arm'],classification=classification,candidate_U=a['U'],candidate_L=a['L'],candidate_gap=a['gap'],control_U=c['U'],control_L=c['L'],control_gap=c['gap'],candidate_seconds=a['observed_end_to_end_seconds'],control_seconds=c['observed_end_to_end_seconds'],certified_time_ratio=a['observed_end_to_end_seconds']/c['observed_end_to_end_seconds'] if classification=='both_certified' else None,own_U_ratio=a['U']/c['U'] if abs(c['U'])>TOL else None,absolute_gap_ratio=a['gap']/c['gap'] if c['gap']>TOL else None,PE_sha256=a['PE_sha256']))
    return data

def confirmation_gate(arms,campaign):
    g={(a['id'],a['arm']):a for a in arms if a['campaign']==campaign}
    assert all((r,m) in g for r in ['F2','R98-C2'] for m in ['P-GRB','ENS-C','GLOBAL-STRUCT','FRONTIER-STRUCT'])
    strong={};compatible={}
    for role in ['F2','R98-C2']:
        a=g[role,'FRONTIER-STRUCT'];p=g[role,'P-GRB']
        strong[role]=a['certificate'] and (not p['certificate'] or a['observed_end_to_end_seconds']<=.9*p['observed_end_to_end_seconds']-TOL)
        compatible[role]=a['certificate'] or (not p['certificate'] and a['U']<=1.01*p['U']+TOL and a['gap']<=1.25*p['gap']+TOL)
    A=any(strong[r] and compatible[next(x for x in strong if x!=r)] for r in strong)
    a=g['R98-C2','FRONTIER-STRUCT'];p=g['R98-C2','P-GRB'];f=g['F2','FRONTIER-STRUCT'];fp=g['F2','P-GRB']
    F2_guard=f['certificate'] if fp['certificate'] else f['certificate'] or (f['U']<=1.01*fp['U']+TOL and f['gap']<=1.05*fp['gap']+TOL)
    B=a['U']<=.99*p['U']-TOL and a['gap']<=.8*p['gap']-TOL and a['U']<p['U']-TOL and F2_guard
    return dict(campaign=campaign,A=A,B=B,admit_confirmation=A or B,strong_certificate_roles=strong,other_role_guard=compatible,F2_B_guard=F2_guard,tolerance=TOL,thresholds_frozen_before_formal=True,statistical_significance_claim=False)

def same(a,b):
    if str(a)==str(b):return True
    try:return math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-9)
    except (ValueError,TypeError):return False

def compare(expected,actual):
    fields=0
    for p in sorted(Path(expected).glob('*.csv')):
        x,y=rows(p),rows(Path(actual)/p.name);assert len(x)==len(y),(p,len(x),len(y))
        for i,(a,b) in enumerate(zip(x,y),1):
            assert set(a)==set(b),(p,i,set(a)^set(b))
            for k in a:assert same(a[k],b[k]),(p,i,k,a[k],b[k]);fields+=1
    for name in ['summary.json','confirmation_gate.json']:
        assert read(Path(expected)/name)==read(Path(actual)/name),name
    return fields

def rebuild(root,dest):
    out=root/ROUND;dest.mkdir(parents=True,exist_ok=False);campaigns=[];arms=[]
    records={k:[] for k in ['candidate_events','requests','request_outcomes','global_master_domains','arm_parameters','conflict_submissions','submission_acceptance','submission_attempts','domain_feedback_skips','cache_hits','row_remaps','semantic_rows','car_modes','new_physical_UB_witnesses','final_physical_fleets','physical_UB_timeline','frontier_timeline','leaf_obligations','controller_AM','controller_targets','controller_events','controller_child_bounds','controller_native','controller_LP_status','time_partitions']}
    formal_gate=read(out/'review/performance_admission.json');assert formal_gate['decision']=='ACCEPT'
    decision=read(out/'admission_decision.json') if (out/'admission_decision.json').exists() else {}
    final_campaign=decision.get('final_development_campaign','development03')
    selected={final_campaign,*decision.get('completed_confirmation_campaigns',[])}
    withdrawn=[];failures=[];unstarted=[];control_journals=[];P_ENS_native=0
    def labeled(label,value):
        return dict(label,**{('raw_'+k if k in label else k):v for k,v in value.items()})
    for camp in sorted(out.iterdir()):
        if not (camp/'identity.json').exists():continue
        ident=read(camp/'identity.json')
        if 'launches' not in ident:continue
        campaigns.append(camp)
        for launch in ident['launches']:
            d=portable(root,launch['destination'])
            label=dict(campaign=camp.name,id=launch['id'],arm=launch['arm'])
            if not (d/'completion.json').exists():
                unstarted.append(dict(label,number=launch['number'],cap_seconds=launch['cap_seconds'],
                    PE_sha256=ident['candidate_binary_sha256'],reason='Prepared launch with no native process completion; retained, excluded from final comparisons'))
                continue
            completion=read(d/'completion.json')
            if completion['stop_reason']!='normal_return' or completion['returncode']!=0 or not (d/'result.json').exists():
                stderr=d/'stderr.log'
                failures.append(dict(label,number=launch['number'],PE_sha256=ident['candidate_binary_sha256'],
                    returncode=completion['returncode'],stop_reason=completion['stop_reason'],
                    observed_end_to_end_seconds=completion['fully_observed_end_to_end_seconds'],
                    result_present=(d/'result.json').exists(),stderr_SHA=sha(stderr) if stderr.exists() else None,
                    error_first_line=stderr.read_text(encoding='utf-8').splitlines()[0] if stderr.exists() and stderr.stat().st_size else None))
                continue
            j=journal(root,launch['panel'],d);ep=endpoint(root,launch,ident,d,j);m=mechanism(root,launch,d)
            row=dict(label,number=launch['number'],cap_seconds=launch['cap_seconds'],reserve_seconds=ident['prereg']['common']['shutdown_margin_seconds'],observed_end_to_end_seconds=ep['completion']['fully_observed_end_to_end_seconds'],process_wall_seconds=ep['completion']['process_wall_seconds'],audit_passed=True,status=ep['status'],certificate=ep['certificate'],U=ep['U'],L=ep['L'],gap=ep['gap'],relative_gap=ep['relative_gap'],journal_native_Optimize_starts=j['started'],journal_not_started_intents=j['not_started'],PE_sha256=ident['candidate_binary_sha256'],DLL_sha256=ident['DLL_sha256'],source_commit=ident['measured_source_commit'],input_sha256=launch['panel']['input_sha256'],destination=d.relative_to(root).as_posix(),**m['statistics'])
            if launch['arm'] in ['P-GRB','ENS-C']:
                P_ENS_native+=j['started'];control_journals.append((d,launch['arm'],j))
            r=ep['result']
            for key in ['external_gini_tree_lp_relaxation_count','external_gini_tree_terminal_mip_count','external_gini_tree_partial_bound_target_mip_count','external_gini_tree_fresh_restart_count','external_gini_tree_native_bound_target_reached_count','external_gini_tree_root_coverage_valid','external_gini_tree_parent_child_coverage_valid','external_gini_tree_backend_parameter_roundtrip_valid']:
                row[key]=r.get(key)
            if launch['arm']=='P-GRB':
                row.update(canonical_SHA=sha(d/'compact.lp'),native_fingerprint=r['gurobi_model_fingerprint'],reference_fingerprint=launch['panel']['reference']['fingerprint'],native_columns=r['gurobi_num_vars'],native_rows=r['gurobi_num_constrs'],native_binary_columns=r['gurobi_num_bin_vars'],native_integer_columns=r['gurobi_num_int_vars'])
            if camp.name in selected:
                assert ident['candidate_binary_sha256']==formal_gate['production_PE_SHA']
                arms.append(row)
            else:withdrawn.append(dict(row,configuration_scope='Superseded partial/unused preparation; retained qualified result, excluded from final paired conclusions'))
            evidence_label=dict(label,configuration_scope='FINAL' if camp.name in selected else 'SUPERSEDED_RETAINED')
            records['arm_parameters'].append(dict(evidence_label,input_path=launch['panel']['input_path'],input_sha256=launch['panel']['input_sha256'],
                V=launch['panel']['V'],M=launch['panel']['M'],Q=launch['panel']['Q_vector'],T=launch['panel']['T_seconds'],
                lambda_value=launch['panel']['lambda'],pickup_seconds=launch['panel']['pickup_seconds'],drop_seconds=launch['panel']['drop_seconds'],
                cap_seconds=launch['cap_seconds'],reserve_seconds=ident['prereg']['common']['shutdown_margin_seconds'],
                PE_sha256=ident['candidate_binary_sha256'],DLL_sha256=ident['DLL_sha256'],source_commit=ident['measured_source_commit'],
                protocol_sha256=ident['prereg_sha256'],actual_parameter_contract_verified=True,
                parameter_readback_source='Native session runtime/quality records' if launch['arm']=='GLOBAL-STRUCT' else 'Native call journal',
                Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6))
            if launch['arm']=='GLOBAL-STRUCT':
                folder=d/'external/round106';embedding=read(folder/'embedding.json')
                assert embedding['LazyConstraints']==1 and embedding['original_sha256']==sha(folder/'original.lp')
                records['global_master_domains'].append(labeled(evidence_label,dict(embedding,epsilon=0,
                    request_scope='Global assignment improvement domain; not an ENS leaf request',
                    physical_seed_SHA=sha(folder/'seed.json'),master_SHA=sha(folder/'master_0.lp'))))
            for target,key in [('candidate_events','events'),('requests','requests'),('conflict_submissions','cuts'),('submission_acceptance','acceptance'),('submission_attempts','attempts'),('domain_feedback_skips','feedback'),('cache_hits','cache'),('row_remaps','remaps'),('semantic_rows','semantic'),('car_modes','modes'),('new_physical_UB_witnesses','physical_ubs')]:records[target].extend(labeled(evidence_label,x) for x in m[key])
            controller=controller_tables(d,r)
            for name,data in controller.items():records[name].extend(labeled(evidence_label,x) for x in data)
            records['time_partitions'].append(labeled(evidence_label,time_partition(launch['arm'],ep,m,controller)))
            records['final_physical_fleets'].append(labeled(evidence_label,dict(ep['physical'],routes=r['routes'],witness_path=(d/'result.json').relative_to(root).as_posix(),witness_SHA=sha(d/'result.json'))))
            for q in m['requests']:
                conclusion='original_LP' if q['kind']=='LP' else 'ERROR' if q['failure'] not in ['none',''] else \
                    'whole_open_stop_UNKNOWN' if q['unresolved'] else 'local_improvement_domain_excluded' if q['local_INF'] else \
                    'local_bound_dominance_closed' if q['optimal_close_by_dominance'] else 'local_target_requeue' if q['target_reached'] else 'whole_open_stop_deadline_or_unclosed'
                records['request_outcomes'].append(dict(evidence_label,request=q['request'],epoch=q['epoch'],leaf=q['leaf'],kind=q['kind'],
                    gamma_L=q['gamma_L'],gamma_U=q['gamma_U'],effective_cutoff=q['effective_cutoff'],epsilon=q['epsilon'],
                    local_bound=q['qualified_local_bound'],bound_qualified=q['qualified_local_bound_available'],own_global_UB=q['own_global_UB'],
                    native_status=q['native_status_text'],native_Optimize_started=q['native_Optimize_started'],domain_Start=q['domain_start'],
                    target_reached=q['target_reached'],controller_obligation_class=conclusion,
                    native_interrupted_raw=q['stop_whole_run'],derived_whole_run_stop=conclusion.startswith('whole_') or conclusion=='ERROR',
                    serialization_note='Raw stop_whole_run serializes native out.interrupted; target interruption requeues locally. Derived controller class uses scoped results, not this mislabeled bit.',reason=q['reason']))
            records['physical_UB_timeline'].extend(labeled(evidence_label,x) for x in j['trace'])
            if ep['cover']:
                records['frontier_timeline'].extend(labeled(evidence_label,x) for x in ep['cover']['timeline'])
                records['leaf_obligations'].extend(labeled(evidence_label,x) for x in ep['cover']['leaves'])
    final=[a for a in arms if a['campaign']==final_campaign]
    assert len(final)==8 and {(a['id'],a['arm']) for a in final}=={(r,m) for r in ['F2','R98-C2'] for m in ['P-GRB','ENS-C','GLOBAL-STRUCT','FRONTIER-STRUCT']}
    for identity in {a['input_sha256'] for a in arms+withdrawn}:
        same_input=[a for a in arms+withdrawn if a['input_sha256']==identity]
        best_physical=min(a['U'] for a in same_input)
        assert all(a['L']<=best_physical+TOL for a in same_input),'cross-arm original-problem contradiction'
    paid=fees(out);nc=native(root,out,campaigns,control_journals)
    summary=dict(formal_arms=len(arms),final_development_arms=len(final),final_development_campaign=final_campaign,
        retained_superseded_completed_arms=len(withdrawn),retained_failed_arms=len(failures),prepared_unstarted_arms=len(unstarted),
        paid_process_starts=sum(r['conservative_process_starts'] for r in paid),paid_outer_seconds=sum(r['outer_seconds'] for r in paid),all_Optimize_starts=sum(r['started'] for r in nc if r['phase'] not in ['iis','core_confirm']),all_IIS_starts=sum(r['started'] for r in nc if r['phase'] in ['iis','core_confirm']),P_ENS_Optimize_starts=P_ENS_native,native_missing_after=sum(r['missing_after'] for r in nc),not_started_intents=sum(r['not_started'] for r in nc),failed_fees=[r['label'] for r in paid if r['exit_code']!=0],nested_native_time_added_to_outer_fee=False,reader_Optimize_calls=0,reader_IIS_calls=0,production_PE_SHA=formal_gate['production_PE_SHA'])
    assert summary['paid_process_starts']<=72 and summary['paid_outer_seconds']<=80000
    if decision:
        assert decision['confirmation_gate']==confirmation_gate(arms,final_campaign)
        assert decision['paid_starts']==summary['paid_process_starts'] and close(decision['paid_outer_seconds'],summary['paid_outer_seconds'])
        assert decision['formal_arms_completed']==8 and decision['confirmation_arms_started']==0
        assert decision['stage']=='STOP_TESTED_CONFIGURATION' and not decision['confirmation_gate']['admit_confirmation']
        for role in decision['confirmation_groups']:
            assert sha(root/role['input_path'])==role['input_sha256'] and role['actual_native_processes']==0 and role['actual_Optimize_calls']==0
            assert role['status']=='NOT_STARTED_CANCELLED'
    table(dest/'arm_results.csv',arms);table(dest/'paired_results.csv',paired(arms));table(dest/'fees.csv',paid);table(dest/'native_calls.csv',nc)
    table(dest/'superseded_arm_results.csv',withdrawn);table(dest/'failed_arms.csv',failures);table(dest/'unstarted_arms.csv',unstarted)
    for name,data in records.items():table(dest/(name+'.csv'),data)
    write(dest/'summary.json',summary);write(dest/'confirmation_gate.json',confirmation_gate(arms,final_campaign))
    return summary

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--compare',type=Path);a=p.parse_args()
    root=a.root.resolve();dest=a.out.resolve();summary=rebuild(root,dest)
    count=compare(a.compare,dest) if a.compare else None
    write(dest/'reader_receipt.json',dict(source_root=str(root),reader_SHA=sha(__file__),compared_fields=count,summary=summary,Optimize_calls=0,IIS_calls=0))
    print(json.dumps(dict(summary=summary,compared_fields=count,Optimize_calls=0,IIS_calls=0)))

if __name__=='__main__':main()
