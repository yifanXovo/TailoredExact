"""Actual saved-data second implementation of fleets/pairs/scopes/checkpoints.

Self-review, not a separate human/agent executor or native reproduction. Imports
only the standard library and the independently written exact-math/comparison
helper, never production/campaign/current-core reader functions.
"""
from pathlib import Path
import argparse,ast,collections,csv,datetime,hashlib,json,math,re,time
from fractions import Fraction
from round123_independent_math import compare

ROOT=Path(__file__).resolve().parents[1]
FILES={}
TOL=1e-7
def sha(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    result=h.hexdigest()
    if p.is_relative_to(ROOT):FILES[p.relative_to(ROOT).as_posix()]=result
    return result
def read(p):sha(p);return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
    if not Path(p).exists():return []
    sha(p)
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def portable(s):
    value=str(s).replace('\\','/')
    for marker in ['results/','reference/','scripts/','src/','include/']:
        if marker in value:
            p=(ROOT/value[value.index(marker):]).resolve();assert p.is_relative_to(ROOT);return p
    raise AssertionError(('No original-root fallback',value))
def near(a,b,tolerance=TOL):assert math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tolerance,(a,b)

def instance(path):
    sha(path);lines=Path(path).read_text(encoding='utf-8-sig').splitlines();h=re.fullmatch(r'(\d+)\s+(\d+)\s+(\[.*\])',lines[0]);assert h
    data={n.strip():ast.literal_eval(v.strip()) for n,v in (line.split('=',1) for line in lines[1:])}
    data.update(V=int(h[1]),M=int(h[2]),Q=ast.literal_eval(h[3]))
    assert all(len(data[k])==data['V']+1 for k in ['initial','target','capacities','weights','points'])
    assert all(d>0 for d in data['target'][1:]);return data

def physical(a,p,witness):
    Y=a['initial'].copy();served=set();cars=set();details=[]
    for route in witness['routes']:
        k=route.get('vehicle',route.get('vehicle_id'));assert k not in cars and k in range(a['M']);cars.add(k)
        nodes=route['nodes'];assert nodes[0]==nodes[-1]==0 and len(nodes)>=2
        ops={o['station']:(o['pickup'],o['drop']) for o in route['operations']}
        assert len(ops)==len(route['operations']) and len(set(nodes[1:-1]))==len(nodes[1:-1]) and set(ops)==set(nodes[1:-1])
        load=0;pickup=0;prefixes=[]
        for i in nodes[1:-1]:
            assert i in range(1,a['V']+1) and i not in served;served.add(i)
            u,v=ops[i];assert type(u) is int and type(v) is int and u>=0 and v>=0 and (u>0)!=(v>0)
            load+=u-v;pickup+=u;prefixes.append(load);assert 0<=load<=a['Q'][k]
            Y[i]+=v-u;assert 0<=Y[i]<=a['capacities'][i]
        travel=math.fsum(math.dist(a['points'][i],a['points'][j])/1.5 for i,j in zip(nodes,nodes[1:]))
        duration=travel+(p['pickup_seconds']+p['drop_seconds'])*pickup;assert duration<=p['T_seconds']+TOL
        details.append(dict(vehicle=k,prefix_loads=prefixes,return_load=load,cumulative_pickup=pickup,travel=travel,duration=duration))
    assert sum(Y[1:])+sum(r['return_load'] for r in details)==sum(a['initial'][1:])
    r=[Y[i]/a['target'][i] for i in range(1,a['V']+1)];S=math.fsum(r)
    G=math.fsum(abs(x-y) for i,x in enumerate(r) for y in r[i+1:])/(a['V']*S) if S else 0.
    weights=a['weights'];weights=[x/10 for x in weights] if abs(max(weights[1:])-10)<1e-6 else weights
    P=math.fsum(weights[i]*abs(r[i-1]-1) for i in range(1,a['V']+1));F=G+p['lambda']*P
    reported=witness.get('upper_bound',witness.get('objective',witness.get('F')));near(F,reported)
    return dict(F=F,G=G,P=P,lambda_P=p['lambda']*P,Y=Y,vehicle_details=details,
        explicit_empty_vehicles=[k for k in range(a['M']) if k not in cars])

def expr(s):
    out=collections.defaultdict(float);constant=0.;words=s.split();i=0;sign=1.
    while i<len(words):
        if words[i] in ['+','-']:sign=1. if words[i]=='+' else -1.;i+=1
        try:coef=sign*float(words[i]);i+=1
        except ValueError:out[words[i]]+=sign;i+=1;sign=1.;continue
        if i<len(words) and re.fullmatch(r'[A-Za-z_]\w*',words[i]):out[words[i]]+=coef;i+=1
        else:constant+=coef
        sign=1.
    return dict(out),constant

def model(path,a,arm):
    """Independent finite matrix scope/type/A-B check; other rows remain byte bound."""
    digest=sha(path);section=None;objective=None;bounds={};types={};special=[];row_count=0
    with Path(path).open(encoding='utf-8') as f:
        for raw in f:
            line=raw.strip()
            if not line or line.startswith('\\'):continue
            if line in ['Minimize','Subject To','Bounds','Generals','Binaries','End']:section=line;continue
            if section=='Minimize':objective=expr(line.split(':',1)[1])
            elif section=='Subject To':
                row_count+=1
                if (('state_' in line and any(x in line for x in [' p_',' d_',' z_'])) or
                    (' G' in line and ' e_' in line) or line.count('h_')==a['V']*(a['V']-1)//2):
                    body=line.split(':',1)[1];m=re.fullmatch(r'(.*)\s(<=|>=|=)\s(\S+)',body);assert m
                    terms,constant=expr(m[1]);special.append((terms,m[2],float(m[3])-constant))
            elif section=='Bounds':
                lo,le,n,le2,hi=line.split();assert le==le2=='<=' and n not in bounds;bounds[n]=(float(lo),float(hi))
            elif section in ['Generals','Binaries']:
                for n in line.split():assert n not in types;types[n]='I' if section=='Generals' else 'B'
    assert section=='End' and objective is not None
    for n in bounds:types.setdefault(n,'C')
    quantities=[n for n in bounds if n.startswith(('p_','d_'))];assert len(quantities)==2*a['M']*a['V']
    assert all(types[n]==('C' if arm=='M-B' else 'I') for n in quantities)
    assert all(types[n] in ['I','B'] for n in bounds if n.startswith(('Y_','load_')))
    assert all(types[n]=='B' for n in bounds if n.startswith(('z_','mode_')) or n.startswith('state_') and not n.startswith('state_g_'))
    obj,constant=objective;assert constant==0 and obj['G']==1 and all(v>=0 for n,v in obj.items() if n!='G')
    assert all(bounds[n][0]>=0 for n in obj)
    if arm=='M-B':
        for i in range(1,a['V']+1):
            A={f'p_{k}_{i}':1. for k in range(a['M'])};A.update({f'd_{k}_{i}':1. for k in range(a['M'])})
            for n in bounds:
                if re.fullmatch('state_'+str(i)+r'_\d+',n):
                    movement=abs(a['initial'][i]-int(n.rsplit('_',1)[1]))
                    if movement:A[n]=-float(movement)
            B={f'z_{k}_{i}':1. for k in range(a['M'])};s=f'state_{i}_{a["initial"][i]}'
            if s in bounds:B[s]=1.
            assert (A,'=',0.) in special and (B,'=',1.) in special,('A/B',i)
    return dict(SHA=digest,rows=row_count,columns=len(bounds),bounds=bounds,types=types,objective=objective,special=special)

def support(lo,hi,proofs):
    cuts=sorted({lo,hi,*[x for p in proofs for x in [p['lo'],p['hi']] if lo<x<hi]});pieces=list(zip(cuts,cuts[1:])) or [(lo,hi)]
    # This validates a published floor against its recorded sources. It is
    # never exported as a replacement production bound or used for search.
    return min(max([left]+[min(p['L'],p['cutoff']) for p in proofs if p['lo']<=left+1e-12 and p['hi']>=right-1e-12]) for left,right in pieces)

def arm_check(l,actual):
    d=portable(l['destination']);p=l['panel'];a=instance(ROOT/p['input_path']);r=read(d/'result.json');obs=read(d/'observations.json')
    prod=read(d/'producer_receipt.json');total=read(d/'arm_total_receipt.json');completion=read(d/'completion.json')
    assert completion['stop_reason']=='normal_return' and completion['returncode']==0
    assert prod['T_produce']<=l['cap_seconds'] and l['cap_seconds']==p['cap_seconds']
    near(total['T_total'],prod['T_produce']+total['T_verify'],1e-8)
    near(prod['T_produce'],prod['t_produce_perf']-prod['t0_perf'],1e-8)
    near(total['T_verify'],total['t_verified_perf']-prod['t_produce_perf'],1e-8)
    for n,h in read(d/'producer_seal.json')['required_SHA'].items():assert sha(d/n)==h
    assert read(d/'child_process_origin.json')['command']==l['command']
    physical_final=physical(a,p,r);near(physical_final['F'],actual['U']);assert physical_final['Y']==read(d/'independent_evidence.json')['physical']['Y']
    calls={};returns={};witnesses=[];bounds=[]
    for n,record in enumerate(obs,1):
        e=record['payload'];assert record['sequence']==e['sequence']==n
        ep=d/'journal'/f'event_{n}.json';assert read(ep)==e and sha(ep)==record['sha256']
        commit=(d/'journal'/f'event_{n}.commit').read_text(encoding='ascii').split();assert commit[0]=='NEJ1' and int(commit[1])==n and commit[4]==record['sha256']
        assert record['effective_available_seconds']==max(record['data_close_seconds'],record['first_observed_seconds'])
        if e['kind']=='call':calls[e['call']]=e
        elif e['kind']=='returned':assert e['return_code']==0;returns[e['call']]=record
        elif e['kind']=='witness':witnesses.append(dict(physical(a,p,e),sequence=n,available=record['effective_available_seconds']))
        elif e['kind']=='bound':assert not e['inconsistent'];bounds.append(e)
        elif e['kind']=='failure':raise AssertionError(('production journal failure',e))
    views=read(d/'call_log_views.json');bindings={b['call']:b for b in views['bindings']};not_started=set(views['not_started'])
    assert set(calls)==set(bindings)|not_started and set(returns)==set(bindings)
    cache={};segments={};proof_by_return={}
    lp_bindings=[cid for cid,v in bindings.items() if v['solve_kind']=='LP']
    lp_status_rows=rows(d/'external/lp_status_ledger.csv');assert len(lp_bindings)==len(lp_status_rows)
    lp_status=dict(zip(lp_bindings,lp_status_rows))
    for cid,call in calls.items():
        path=portable(call['model_path']);digest=sha(path);assert digest==call['model_sha256']
        if digest not in cache:cache[digest]=model(path,a,l['arm'])
        m=cache[digest]
        if not call['full_original']:
            assert m['bounds']['G']==(call['lower_g'],call['upper_g'])
            assert (m['objective'][0],'<=',call['cutoff']-m['objective'][1]) in m['special']
            for gamma,sense in [(call['lower_g'],'>='),(call['upper_g'],'<=')]:
                terms={f'h_{i}_{j}':1. for i in range(1,a['V']+1) for j in range(i+1,a['V']+1)}
                if gamma:terms.update({f'r_{i}':-a['V']*gamma for i in range(1,a['V']+1)})
                assert (terms,sense,0.) in m['special']
        if cid in not_started:continue
        view=bindings[cid];assert view['model_SHA']==digest and view['return_sequence']==returns[cid]['sequence']
        lp=ROOT/view['raw_log'];assert sha(lp)==view['raw_log_SHA'];data=lp.read_bytes()[view['byte_begin']:view['byte_end']]
        assert hashlib.sha256(data).hexdigest()==view['segment_SHA'] and data.count(b'Optimize a model with ')==1
        text=data.decode('utf-8',errors='strict');segments[cid]=text
        dims=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',text);assert dims and (int(dims[1]),int(dims[2]))==(m['rows'],m['columns'])
        expected=dict(read_return_code=0,Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
        assert call['settings']==expected and view['return_code']==0
        cutoff=call['cutoff'];base=dict(lo=call['lower_g'],hi=call['upper_g'],cutoff=cutoff,call=cid)
        if view['solve_kind']=='LP':
            status=view['ledger']['native_status'];row=lp_status[cid]
            assert row['leaf_id']==call['leaf'] and row['native_status']==status
            near(float(row['gamma_L']),call['lower_g'],1e-12);near(float(row['gamma_U']),call['upper_g'],1e-12)
            if status=='OPTIMAL':
                final=re.findall(r'Optimal objective\s+(\S+)',text);assert final and int(row['terminal_valid']) and int(row['optimal'])
                near(float(final[-1]),float(row['lower_bound']));L=float(row['lower_bound'])
            else:
                assert status=='INFEASIBLE' and ('Infeasible model' in text or 'Model is infeasible' in text);L=cutoff
            proof_by_return[cid]=dict(base,L=L)
        elif not call['full_original']:
            if 'Infeasible model' in text or 'Model is infeasible' in text:proof_by_return[cid]=dict(base,L=cutoff)
            else:
                values=re.findall(r'Best objective [^,]+, best bound ([^,]+), gap',text)
                if values and math.isfinite(float(values[-1])) and abs(float(values[-1]))<1e90:proof_by_return[cid]=dict(base,L=float(values[-1]))
    proofs=[];cover_records=0
    for record in obs:
        e=record['payload'];cid=e.get('call')
        if e['kind']=='returned' and cid in proof_by_return:proofs.append(proof_by_return[cid])
        if e['kind']!='bound':continue
        call=calls[cid]
        if not call['full_original'] and call['native_preconditions']:
            proofs.append(dict(lo=call['lower_g'],hi=call['upper_g'],cutoff=call['cutoff'],L=e['native_bound'],call=cid))
        if not e['global_available']:continue
        if call['full_original']:near(e['global_bound'],e['native_bound']);continue
        cover=[dict(x) for x in call['cover']];matched=False;covered=0.
        for piece in sorted(cover,key=lambda x:x['lower_g']):
            if piece['id']==call['leaf'] and piece['lower_g']==call['lower_g'] and piece['upper_g']==call['upper_g'] and piece['cutoff']==call['cutoff']:
                piece['lower']=max(piece['lower'],e['native_bound']);matched=True
            assert piece['lower_g']<=covered+TOL;covered=max(covered,piece['upper_g'])
            assert min(piece['lower'],piece['cutoff'])<=support(piece['lower_g'],piece['upper_g'],proofs)+TOL
        assert matched and covered+TOL>=min(call['cutoff'],call['gmax'])
        expected_global=min([call['cutoff']]+[min(x['lower'],x['cutoff']) for x in cover]);near(expected_global,e['global_bound']);cover_records+=1
    leaves=rows(d/'external/paper_leaf_ledger.csv');active=[x for x in leaves if x['status'] not in ['replaced','coalesced']]
    if l['arm']=='P-GRB':
        assert len(calls)==len(returns)==1 and next(iter(calls.values()))['full_original']
        text=next(iter(segments.values()));printed=re.findall(r'Best objective [^,]+, best bound ([^,]+), gap',text);assert printed
        near(float(printed[-1]),r['lower_bound']);near(r['lower_bound'],actual['L']);closed=r['gurobi_status']==2 and actual['gap']<=TOL
        unresolved=[] if closed else [dict(scope='complete original cold compact model',L=actual['L'],U=actual['U'])]
    else:
        covered=0.
        for leaf in sorted(active,key=lambda x:float(x['gamma_L'])):
            lo,hi=float(leaf['gamma_L']),float(leaf['gamma_U']);assert lo<=covered+TOL;covered=max(covered,hi)
            assert min(float(leaf['lower_bound']),actual['U'])<=support(lo,hi,proofs)+TOL
        assert covered+TOL>=min(actual['U'],(a['V']-1)/a['V'])
        relevant=[x for x in active if float(x['gamma_L'])<actual['U']-TOL]
        near(min((float(x['lower_bound']) for x in relevant),default=0.),actual['L'])
        unresolved=[x for x in relevant if x['status'] not in ['closed','empty','fathomed'] and float(x['lower_bound'])<actual['U']-TOL]
        closed=not unresolved and actual['gap']<=TOL
    assert closed==actual['certificate']==r['strict_certified_original_problem']
    best=min(witnesses+[dict(physical_final,sequence=None,available=prod['T_produce'])],key=lambda x:x['F'])
    origin_offset=max(0.,read(d/'native_end_receipt.json')['complete_seconds_until_native_end']-completion['fully_observed_end_to_end_seconds'])
    best_upper=best['available']+origin_offset if best['sequence'] is not None else best['available']
    return dict(arm=l['arm'],final=physical_final,clocks=dict(T_produce=prod['T_produce'],T_verify=total['T_verify'],T_total=total['T_total']),
        all_observed_witnesses=len(witnesses),all_native_bound_events=len(bounds),best_observed=dict(F=best['F'],G=best['G'],sequence=best['sequence'],available_upper_arm_seconds=best_upper),
        calls=calls,proofs=proofs,bounds=bounds,witnesses=witnesses,unresolved=unresolved,certificate=closed,
        checked_matrix_count=len(cache),chronological_cover_records=cover_records,source_directory=str(d.relative_to(ROOT)))

def main(qualification=False):
    tick=time.perf_counter();out=ROOT/'results/unified_exact_round123'
    core=read(out/('qualification/reconstructed02/current_core.json' if qualification else 'reconstruction/final/current_core.json'))
    ident=read(out/('qualification/h100_seed0/identity.json' if qualification else 'campaign/group01/identity.json'));candidate=read(out/'candidate_identity.json')
    for path,digest in {**candidate['source_bindings'],**candidate['helpers']}.items():assert sha(ROOT/path)==digest
    assert len(ident['launches'])==3 and [l['arm'] for l in ident['launches']]==['P-GRB','M-B','ENS-C']
    if qualification:assert all(l['id']=='H100' and l['panel']['V']==20 and l['cap_seconds']==120 for l in ident['launches'])
    else:assert all(l['id']=='PB-C50-S' and l['panel']['V']==50 and l['cap_seconds']==18000 and l['panel']['T_seconds']==10800 for l in ident['launches'])
    by={a['arm']:a for a in core['arms']};reviews=[arm_check(l,by[l['arm']]) for l in ident['launches']]
    all_witnesses=[w for v in reviews for w in v['witnesses']+[v['final']]];contradictions=[]
    for v in reviews:
        for b in v['bounds']:
            call=v['calls'][b['call']]
            for w in all_witnesses:
                if call['full_original'] or call['lower_g']-TOL<=w['G']<=call['upper_g']+TOL and w['F']<=call['cutoff']+TOL:
                    if b['native_bound']>w['F']+TOL:contradictions.append(dict(arm=v['arm'],call=b['call'],bound=b['native_bound'],witness_F=w['F'],witness_G=w['G']))
    comparisons=[]
    for q in core['pairs']:
        actual=compare(by[q['candidate']],by[q['control']]);assert actual==(q['classification'],q['severe_regression'])
        near(q['dgap'],q['dU']-q['dL'],1e-12);comparisons.append(dict(pair=q['candidate']+'/'+q['control'],classification=actual[0],severe=actual[1]))
    assert len(comparisons)==3
    checks=[]
    for cp in core['checkpoints']:
        arm=cp['arm'];v=next(x for x in reviews if x['arm']==arm);l=next(x for x in ident['launches'] if x['arm']==arm);d=portable(l['destination'])
        prod=read(d/'producer_receipt.json');point=cp['checkpoint_seconds']
        if cp['source']=='actual_sealed_endpoint_before_checkpoint':
            assert prod['T_produce']<=point and not cp['continued_computation_record'];near(cp['U_final'],by[arm]['U']);near(cp['L'],by[arm]['L'])
        else:
            offset=max(0.,read(d/'native_end_receipt.json')['complete_seconds_until_native_end']-read(d/'completion.json')['fully_observed_end_to_end_seconds'])
            prior=[r for r in read(d/'observations.json') if r['effective_available_seconds']+offset<=point]
            assert cp['last_any_record_sequence']==(prior[-1]['sequence'] if prior else None)
            witnesses=[w for w in v['witnesses'] if w['available']+offset<=point]
            if witnesses:near(cp['observed_best_F'],min(w['F'] for w in witnesses))
            else:assert cp['observed_best_F'] is None
            bs=[r['payload'] for r in prior if r['payload']['kind']=='bound' and r['payload']['global_available']]
            if bs:near(cp['L'],max(x['global_bound'] for x in bs))
            for k in ['last_any_record_available_upper_seconds','observed_best_available_upper_seconds','L_available_upper_seconds']:
                assert cp[k] is None or cp[k]<=point
        checks.append(dict(arm=arm,checkpoint=point,source=cp['source'],actual_record_upper=cp.get('actual_record_available_upper_seconds',cp.get('last_any_record_available_upper_seconds'))))
    expected='QUALIFICATION_ONLY_NOT_V50_EVIDENCE' if qualification else 'PROOF_RELIABILITY_PRIORITY' if contradictions else 'MB_NONZERO_V50_PROOF_OBSERVED' if by['M-B']['certificate'] else 'REFERENCE_PROOF_OBSERVED_MB_REMAINS_OPEN' if by['P-GRB']['certificate'] or by['ENS-C']['certificate'] else 'FINITE_LONG_WINDOW_PROOF_LIMIT_RECORDED'
    if not qualification:assert core['decision']['research_disposition']==expected
    output=dict(decision='ACCEPT' if not contradictions else 'PROOF_RELIABILITY_PRIORITY',method='Self-review by a separate saved-data implementation; no third-party executor or native reproduction',
        all_three_physical_fleets_and_clocks=reviews,all_three_comparisons=comparisons,all_fifteen_checkpoint_sources=checks,
        cross_arm_same_domain_counterexamples=contradictions,research_disposition=expected,
        all_negative_or_uncertain_pairs=[q for q in core['pairs'] if q['classification'] in ['LOSS','MIXED','UNEVALUABLE'] or q['severe_regression']],
        math_review_SHA=sha(out/'review/independent_math_and_R122.json'),new_native_starts=0,Optimize=0,
        no_new_route_or_production_bound=True,scope_limits=['Full saved matrices independently checked for actual types, objective, A/B and G/cutoff domain; other frozen routing/F0 rows remain byte-bound to the checked source and inherited full audits.',
            'No native LP/MIP replay or rational solver optimality proof. Parsed objective coefficients and finite arithmetic do not establish library-wide exactness.',
            'Chronological and final floors are recomputed only to validate published bound support, never substituted into production endpoints.',
            'Public export/recovery and cleanup are separate later receipts.'],
        qualification=qualification,files_SHA=FILES,script_SHA=sha(__file__),comparison_helper_SHA=sha(Path(__file__).with_name('round123_independent_math.py')),
        seconds=time.perf_counter()-tick,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
    write(out/('review/independent_qualification.json' if qualification else 'review/independent_post.json'),output)
    print(json.dumps(dict(decision=output['decision'],stage=expected,seconds=output['seconds'],physical_fleets=3,pairs=3,checkpoints=len(checks))))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(ROOT));parser.add_argument('--qualification',action='store_true');args=parser.parse_args();ROOT=Path(args.root).resolve();main(args.qualification)
