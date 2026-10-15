"""Independent final finite R121 review; no solver, generator or campaign imports."""
from pathlib import Path
from fractions import Fraction
import ast, collections, copy, csv, datetime, hashlib, json, math, re, statistics, subprocess, time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round121'
REVIEW=OUT/'review'
PE_SHA='5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
RAW_SHA='d4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8'
TABLE_SHA='d982051e5871c575ecdf9df538605401bd98341ae9b3b48112482eff80d42ffa'
FAMILY='round121-frozen-d1-confirmation-v1|source_sha256='+RAW_SHA
RECIPE_COMMIT='4a205b322a1ca94940479b53b2f87d4c79778318'
RUNTIME_FREEZE='af1dc6fb769a6c4fc78c6b6245fe0d166c422e42'
EXPECTED=[('F2',1,1200,['MB-D0','P-GRB','MB-D1','M-B']),
 ('Q30-C2-B',0,1800,['P-GRB','MB-D1','M-B']),('R98-C2',1,1800,['M-B','P-GRB','MB-D1']),
 ('Q40-R2-S',0,3600,['MB-D1','M-B','P-GRB']),('Q50-C2-U',0,3600,['M-B','P-GRB','MB-D1'])]
PAIRS6=[('MB-D1','M-B'),('MB-D1','P-GRB'),('MB-D1','MB-D0'),('MB-D0','M-B'),('MB-D0','P-GRB'),('M-B','P-GRB')]
PAIRS3=[('MB-D1','M-B'),('MB-D1','P-GRB'),('M-B','P-GRB')]
FILES={}

def sha(path):
    p=Path(path);h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    digest=h.hexdigest()
    if p.is_relative_to(ROOT):FILES[p.relative_to(ROOT).as_posix()]=digest
    return digest

def read(path):
    p=Path(path);sha(p)
    return json.loads(p.read_text(encoding='utf-8-sig'))

def text(path):
    p=Path(path);sha(p)
    return p.read_text(encoding='utf-8-sig')

def rows(path):
    p=Path(path)
    if not p.exists():return []
    sha(p)
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def pure_own_functions(path,names,namespace):
    tree=ast.parse(text(path));selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(selected)==len(names)
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path)+'::independent_pure_helpers','exec'),namespace)
    return namespace

HELPERS=pure_own_functions(ROOT/'scripts/round121_extra_review.py',
 ['parse_instance','physical','expression','lp','scope_check','start_check'],
 dict(Path=Path,read=read,sha=sha,text=text,math=math,re=re,collections=collections,ast=ast,csv=csv))
INPUTS=pure_own_functions(ROOT/'scripts/round121_precontract_review.py',
 ['order','unit','coordinates','distance','independent_selection','independent_landscape'],
 dict(FAMILY=FAMILY,hashlib=hashlib,math=math,statistics=statistics))

def near(a,b,tol=1e-7):
    assert math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a)-float(b))<=tol,(a,b,tol)

def git(*args):
    assert args[0] in ['show','ls-tree','log']
    result=subprocess.run(['git',*args],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    return result.stdout

def comparison(c,p):
    """Fresh direct implementation of the original verbal comparison contract."""
    assert c['certificate_qualified'] and p['certificate_qualified']
    good=all(a['numbers_qualified'] and all(isinstance(a[k],(int,float)) and math.isfinite(a[k]) for k in ['U','L']) for a in [c,p])
    if good:
        for a in [c,p]:assert a['L']<=a['U']+1e-7
    answer=dict(candidate=c['arm'],control=p['arm'],severe_regression=False,
                UB_improvement=p['U']-c['U'] if good else None,gap_improvement=p['gap']-c['gap'] if good else None,
                LB_change=c['L']-p['L'] if good else None)
    if c['certificate']!=p['certificate']:
        answer.update(classification='WIN' if c['certificate'] else 'LOSS',severe_regression=bool(p['certificate']),basis='certificate_priority')
    elif c['certificate']:
        delta=p['complete_seconds']-c['complete_seconds'];material=max(30.,.1*p['complete_seconds'])
        answer.update(classification='WIN' if delta>=material else 'LOSS' if delta<=-material else 'TIE',
            severe_regression=c['complete_seconds']>=2*p['complete_seconds'] and -delta>=120.,a_t=material,
            certified_time_ratio=c['complete_seconds']/p['complete_seconds'],basis='both_certified_time')
    elif not good:answer.update(classification='UNEVALUABLE',basis='unqualified_or_missing_numbers')
    else:
        u,g=answer['UB_improvement'],answer['gap_improvement'];au=max(.001,.01*abs(p['U']));ag=max(.001,.1*abs(p['gap']))
        favorable=u>=au or g>=ag;adverse=-u>=au or -g>=ag
        answer.update(classification='MIXED' if favorable and adverse else 'WIN' if favorable else 'LOSS' if adverse else 'TIE',
            severe_regression=-u>=max(.001,.05*abs(p['U'])) and -g>=max(.005,.25*abs(p['gap'])),a_U=au,a_gap=ag,basis='both_open_absolute_materiality')
    answer['evaluable']=answer['classification']!='UNEVALUABLE'
    return answer

def light_model(path,call,panel):
    """Read all model sections; parse the complete types/bounds and actual scope rows."""
    objective=None;bounds={};types={};rowcount=0;g_rows=[];cutoffs=[];section=None
    pair_count=panel['V']*(panel['V']-1)//2
    with Path(path).open(encoding='utf-8') as f:
        for raw in f:
            line=raw.strip()
            if not line or line.startswith('\\'):continue
            if line in ['Minimize','Subject To','Bounds','Generals','Binaries','End']:
                section=line;continue
            if section=='Minimize':objective=HELPERS['expression'](line.split(':',1)[1],lambda n:None)
            elif section=='Subject To':
                rowcount+=1
                match=re.fullmatch(r'(.*)\s(<=|>=|=)\s(\S+)',line.split(':',1)[1]);assert match
                sense,rhs=match[2],float(match[3])
                need_g=not call['full_original'] and abs(rhs)<=1e-12 and line.count('h_')>=pair_count
                need_cut=not call['full_original'] and sense=='<=' and abs(rhs-(call['cutoff']-objective[1]))<=1e-10
                if need_g or need_cut:
                    terms,constant=HELPERS['expression'](match[1],lambda n:None)
                    if need_g:g_rows.append((terms,sense,rhs-constant))
                    if need_cut:cutoffs.append((terms,sense,rhs-constant))
            elif section=='Bounds':
                lo,le,name,le2,hi=line.split();assert le==le2=='<=' and name not in bounds
                bounds[name]=(float(lo),float(hi))
            elif section in ['Generals','Binaries']:
                for name in line.split():assert name not in types;types[name]='I' if section=='Generals' else 'B'
            else:raise AssertionError(('unknown model section',section))
    assert section=='End' and objective and set(types)<=set(bounds)
    types={n:types.get(n,'C') for n in bounds}
    quantity={n:t for n,t in types.items() if n.startswith(('p_','d_'))}
    assert len(quantity)==2*panel['M']*panel['V']
    assert set(quantity.values())==({'I'} if call['full_original'] else {'C'})
    if not call['full_original']:
        assert all(t=='I' for n,t in types.items() if n.startswith(('Y_','load_')))
        assert bounds['G']==(call['lower_g'],call['upper_g'])
        assert any(terms==objective[0] and sense=='<=' and abs(rhs-(call['cutoff']-objective[1]))<=1e-12 for terms,sense,rhs in cutoffs)
        for gamma,sense in [(call['lower_g'],'>='),(call['upper_g'],'<=')]:
            expected={f'h_{i}_{j}':1. for i in range(1,panel['V']+1) for j in range(i+1,panel['V']+1)}
            if gamma:expected.update({f'r_{i}':-panel['V']*gamma for i in range(1,panel['V']+1)})
            assert any(s==sense and r==0 and set(t)==set(expected) and all(abs(t[n]-expected[n])<=1e-12 for n in t) for t,s,r in g_rows)
    if 'r120_h' in types:assert types['r120_h']=='B' and bounds['r120_h']==(0.,1.)
    return dict(SHA=sha(path),rows=rowcount,columns=len(bounds),types=dict(collections.Counter(types.values())),
                original_quantity_type=next(iter(quantity.values())),selector_installed='r120_h' in types,
                ObjCon=objective[1],scope=dict(full_original=bool(call['full_original']),lo=call['lower_g'],hi=call['upper_g'],cutoff=call.get('cutoff')),
                all_bounds_types_and_actual_true_G_scope_and_objective_cutoff_parsed=True)

def journal(directory,launch):
    obs=read(directory/'observations.json');calls={};returns={};cancelled=set();native_bounds=[];witnesses=[]
    for number,o in enumerate(obs,1):
        receipt=(directory/'journal'/f'event_{number}.commit').read_text().split()
        body=directory/'journal'/f'event_{number}.json';e=o['payload']
        assert receipt[:2]==['NEJ1',str(number)] and len(receipt)==5
        assert body.stat().st_size==int(receipt[3]) and sha(body)==receipt[4]==o['sha256'] and read(body)==e
        assert o['sequence']==e['sequence']==number and float(receipt[2])==o['data_close_seconds']
        assert o['effective_available_seconds']==max(o['first_observed_seconds'],o['data_close_seconds'])<=launch['cap_seconds']
        if e['kind']=='call':
            assert e['call']==len(calls)+1
            assert e['settings']==dict(read_return_code=0,Threads=1,Seed=launch['seed'],Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
            calls[e['call']]=e
        elif e['kind']=='returned':assert e['call'] in calls and e['call'] not in returns and e['return_code']==0;returns[e['call']]=number
        elif e['kind']=='not_started':assert e['actual_Optimize'] is False;cancelled.add(e['call'])
        elif e['kind']=='bound':native_bounds.append(e)
        elif e['kind']=='witness':witnesses.append(e)
        else:assert e['kind'] in ['identity','witness_rejected']
    actual={cid:c for cid,c in calls.items() if cid not in cancelled}
    assert set(actual)==set(returns)
    return dict(obs=obs,calls=actual,all_calls=calls,returns=returns,cancelled=cancelled,bounds=native_bounds,witnesses=witnesses)

def call_evidence(directory,launch,j):
    ledger=rows(directory/'external/paper_optimize_ledger.csv')
    assert not ledger if launch['arm']=='P-GRB' else len(ledger)==len(j['calls'])
    entries={cid:(ledger[n] if ledger else None) for n,cid in enumerate(j['calls'])}
    models={};groups=collections.defaultdict(list);facts=[];proofs=[]
    for cid,c in j['calls'].items():
        path=Path(c['model_path']);assert sha(path)==c['model_sha256']
        if c['model_sha256'] not in models:models[c['model_sha256']]=light_model(path,c,launch['panel'])
        model=models[c['model_sha256']];entry=entries[cid]
        if entry:
            assert entry['leaf_id']==c['leaf'] and entry['model_sha256']==c['model_sha256'] and int(entry['optimize_return_code'])==0
            assert Path(entry['native_log'])==Path(c['native_log_path'])
        else:assert c['full_original'] and model['SHA']==launch['panel']['reference']['canonical_sha256']
        groups[Path(c['native_log_path'])].append((cid,c,entry,model))
    frames={};span_facts=[]
    for path,items in groups.items():
        content=path.read_bytes();sha(path);starts=[m.start() for m in re.finditer(rb'(?m)^Gurobi Optimizer version ',content)]
        assert len(starts)==len(items)
        for (cid,c,entry,model),lo,hi in zip(items,starts,starts[1:]+[len(content)]):
            segment=content[lo:hi];frame=segment.decode();frames[cid]=frame
            match=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',frame);assert match
            assert (int(match[1]),int(match[2]))==(model['rows'],model['columns']) and frame.count('Optimize a model with ')==1
            is_lp=entry and entry['solve_kind']=='LP'
            counts=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',frame)
            if counts:
                actual=dict(C=int(counts[1]),I=int(counts[2])-int(counts[3]),B=int(counts[3]));expected=dict(C=model['columns'],I=0,B=0) if is_lp else model['types']
                assert all(actual[k]==expected.get(k,0) for k in actual)
            else:assert is_lp
            if is_lp:assert int(entry['integer_domain_restored'])==1
            assert c['native_preconditions']==(not is_lp and launch['seed']==0)
            if launch['arm']=='P-GRB':assert 'Loaded user MIP start' not in frame
            for key,value in re.findall(r'(?m)^(Seed|Threads|Presolve|MIPGap|MIPGapAbs|FeasibilityTol|OptimalityTol|IntFeasTol)\s+([-+0-9.eE]+)\s*$',frame):near(float(value),c['settings'][key],0.)
            span_facts.append(dict(call=cid,log_SHA=sha(path),start_byte=lo,end_byte=hi,segment_SHA=hashlib.sha256(segment).hexdigest(),LP=bool(is_lp),model=model))
    lp_status=rows(directory/'external/lp_status_ledger.csv');lp_calls=[cid for cid,row in entries.items() if row and row['solve_kind']=='LP']
    assert len(lp_calls)==len(lp_status)
    for cid,status in zip(lp_calls,lp_status):
        c=j['calls'][cid];entry=entries[cid]
        assert status['leaf_id']==c['leaf'] and status['native_status']==entry['native_status']
        near(float(status['gamma_L']),c['lower_g'],1e-12);near(float(status['gamma_U']),c['upper_g'],1e-12)
        if int(status['terminal_valid']) and int(status['optimal']) and int(status['bound_available']):
            value=float(status['lower_bound']);printed=re.findall(r'Optimal objective\s+([-+0-9.eE]+)',frames[cid]);assert printed
            near(float(printed[-1]),value)
            proofs.append(dict(call=cid,lo=c['lower_g'],hi=c['upper_g'],L=value,cutoff=c['cutoff'],sequence=j['returns'][cid],source='returned_actual_optimal_LP'))
        elif int(status['terminal_valid']) and int(status['infeasible']):
            assert re.search(r'(Infeasible model|Model is infeasible)',frames[cid]);proofs.append(dict(call=cid,lo=c['lower_g'],hi=c['upper_g'],L=c['cutoff'],cutoff=c['cutoff'],sequence=j['returns'][cid],source='returned_LP_infeasible_cutoff_complement'))
    for cid,c in j['calls'].items():
        entry=entries[cid]
        if entry and entry['solve_kind']=='LP':continue
        for b in j['bounds']:
            if b['call']==cid:proofs.append(dict(call=cid,lo=c['lower_g'],hi=c['upper_g'],L=b['native_bound'],cutoff=c.get('cutoff',1e100),sequence=b['sequence'],source='actual_committed_native_bound'))
        printed=re.findall(r'Best objective [^,]+, best bound ([^,]+), gap',frames[cid])
        if printed:
            try:value=float(printed[-1])
            except ValueError:value=math.nan
            if math.isfinite(value) and abs(value)<1e90:proofs.append(dict(call=cid,lo=c['lower_g'],hi=c['upper_g'],L=value,cutoff=c.get('cutoff',1e100),sequence=j['returns'][cid],source='actual_returned_native_log_bound'))
        if entry and entry['native_status']=='INFEASIBLE':
            assert re.search(r'(Infeasible model|Model is infeasible)',frames[cid]);proofs.append(dict(call=cid,lo=c['lower_g'],hi=c['upper_g'],L=c['cutoff'],cutoff=c['cutoff'],sequence=j['returns'][cid],source='returned_integer_infeasible_cutoff_complement'))
    return dict(spans=span_facts,proofs=proofs,frames=frames,entries=entries,models=models)

def support(lo,hi,proofs):
    knots=sorted({lo,hi,*[v for p in proofs for v in [p['lo'],p['hi']] if lo<v<hi]})
    cells=list(zip(knots,knots[1:])) or [(lo,hi)]
    return min(max([left]+[min(p['L'],p['cutoff']) for p in proofs if p['lo']<=left+1e-12 and p['hi']+1e-12>=right]) for left,right in cells)

def coverage(directory,launch,j,evidence,U):
    if launch['arm']=='P-GRB':
        result=read(directory/'result.json');L=result['native_mip_best_bound']
        near(L,max(p['L'] for p in evidence['proofs']))
        return dict(L=L,certificate=result['gurobi_status']==2 and U-L<=1e-7,full_original=True,cover_complement='cold complete original model')
    proofs=[p for p in evidence['proofs'] if p['cutoff']+1e-7>=U]
    audit=[]
    for event in [o['payload'] for o in j['obs']]:
        if event['kind'] not in ['call','bound']:continue
        call=event if event['kind']=='call' else j['all_calls'][event['call']]
        if call['full_original'] or event['kind']=='bound' and not event['global_available']:continue
        available=[p for p in proofs if p['sequence']<=event['sequence']]
        for piece in call['cover']:
            claim=piece['lower']
            if event['kind']=='bound' and (piece['id'],piece['lower_g'],piece['upper_g'],piece['cutoff'])==(call['leaf'],call['lower_g'],call['upper_g'],call['cutoff']):claim=max(claim,event['native_bound'])
            bound=support(piece['lower_g'],piece['upper_g'],available)
            assert min(claim,piece['cutoff'])<=bound+1e-7,('future_or_out_of_scope_cover',launch['id'],launch['arm'],event['sequence'],claim,bound)
            audit.append(dict(sequence=event['sequence'],lo=piece['lower_g'],hi=piece['upper_g'],claim=claim,cutoff=piece['cutoff'],support=bound))
    trace=rows(directory/'external/global_bound_trace.csv');leaves=rows(directory/'external/paper_leaf_ledger.csv')
    assert trace and leaves
    previous_L,previous_U=-math.inf,math.inf
    for row in trace:
        upper=float(row['verified_global_upper_bound']);parts=[float(row[k]) for k in ['active_leaf_valid_lower_bound','other_open_leaf_min_valid_lower_bound'] if row[k]]
        lower=float(row['valid_global_lower_bound']);near(lower,min([upper]+parts));assert lower>=previous_L-1e-7 and upper<=previous_U+1e-7
        previous_L,previous_U=lower,upper
    live=[l for l in leaves if l['status'] not in ['replaced','coalesced']];end=0.;scope=[]
    for leaf in sorted(live,key=lambda q:float(q['gamma_L'])):
        lo,hi,lower=map(float,[leaf['gamma_L'],leaf['gamma_U'],leaf['lower_bound']]);assert 0<=lo<=hi and lo<=end+1e-7 and leaf['status']!='invalid'
        supported=support(lo,hi,proofs);assert lower<=supported+1e-7,(launch['id'],launch['arm'],leaf,supported)
        scope.append(dict(lo=lo,hi=hi,reported=lower,supported=supported,status=leaf['status']));end=max(end,hi)
    assert end+1e-7>=min(U,(launch['panel']['V']-1)/launch['panel']['V'])
    raw_cutoff=float(trace[-1]['verified_global_upper_bound']);near(U,raw_cutoff)
    L=min((float(l['lower_bound']) for l in live if float(l['gamma_L'])<raw_cutoff-1e-7),default=0.)
    near(min(raw_cutoff,L),float(trace[-1]['valid_global_lower_bound']))
    closed=all(l['status'] in ['closed','fathomed','empty'] or float(l['gamma_L'])>=U-1e-7 or float(l['lower_bound'])>=U-1e-7 for l in live)
    return dict(L=L,certificate=closed and U-L<=1e-7,live_scope=scope,chronological_cover_count=len(audit),
                chronological_cover_SHA=hashlib.sha256(json.dumps(audit,sort_keys=True).encode()).hexdigest(),
                trace_rows=len(trace),complete_true_G_coverage_upper=end,proof_count=len(proofs),proofs=proofs,
                cutoff_complement='On each true-G interval F<=cutoff uses its actual original model proof; F>cutoff supplies cutoff. Outside covered [0,U], F>=true_G>=U because penalty is nonnegative.',
                raw_signed_endpoint_L_not_clipped=L)

def physical_record(launch,result):
    p=launch['panel'];value=copy.deepcopy(result)
    if 'upper_bound' not in value:value['upper_bound']=value.get('objective',value.get('F'))
    for route in value['routes']:
        route['operations']=[o if isinstance(o,dict) else dict(station=o[0],pickup=o[1],drop=o[2]) for o in route['operations']]
    return HELPERS['physical'](ROOT/p['input_path'],p,value)

def complete_H(launches):
    """Independent full trace comparison under the original metadata exclusion rule."""
    csv_metadata={'process_seconds','elapsed_seconds','elapsed','timestamp','wall_seconds'}
    json_metadata={'sha256','elapsed_seconds','process_seconds','wall_seconds','timestamp','path'}
    def semantic(value):
        if isinstance(value,dict):return {k:semantic(v) for k,v in value.items() if k not in json_metadata}
        if isinstance(value,list):return [semantic(v) for v in value]
        return value
    values=[]
    for launch in launches:
        if launch['arm']=='P-GRB':continue
        d=Path(launch['destination']);paths=list(d.glob('hga.csv.*.csv'))+list((d/'hga.csv.exchange').iterdir());traces={}
        for path in sorted(paths):
            key=path.relative_to(d).as_posix()
            if path.suffix=='.csv':traces[key]=[{k:v for k,v in row.items() if k not in csv_metadata} for row in rows(path)]
            elif path.suffix=='.json':traces[key]=semantic(read(path))
            elif path.suffix=='.jsonl':traces[key]=[semantic(json.loads(line)) for line in text(path).splitlines()]
        descent=traces['hga.csv.descent.csv'];assert {int(r['seed']) for r in descent}==set(range(1,26))
        assert all(r['interrupted']=='0' for r in descent)
        fleet=physical_record(launch,read(d/'hga.csv.exchange/final.json'))
        closure_count=0
        for path in (d/'hga.csv.exchange').glob('*.final.json'):physical_record(launch,read(path));closure_count+=1
        final=read(d/'hga.csv.exchange/final.json');by_vehicle={r.get('vehicle',r.get('vehicle_id')):r for r in final['routes']};capacity_fleet=[]
        for capacity in sorted(set(launch['panel']['Q_vector'])):
            members=[]
            for vehicle,q in enumerate(launch['panel']['Q_vector']):
                if q!=capacity:continue
                r=by_vehicle.get(vehicle,dict(nodes=[0,0],operations=[]))
                operations={(o['station'] if isinstance(o,dict) else o[0]):((o['pickup'],o['drop']) if isinstance(o,dict) else (o[1],o[2])) for o in r['operations']}
                members.append(dict(nodes=r['nodes'],operations=[(n,*operations[n]) for n in r['nodes'][1:-1]]))
            capacity_fleet.append((capacity,sorted(members,key=lambda x:json.dumps(x,sort_keys=True))))
        values.append(dict(arm=launch['arm'],traces=traces,fleet=fleet,capacity_fleet=capacity_fleet,closure_count=closure_count))
    control=next(v for v in values if v['arm']=='M-B')
    for value in values:
        assert value['traces']==control['traces'] and value['capacity_fleet']==control['capacity_fleet']
        assert value['fleet']['Y']==control['fleet']['Y'];near(value['fleet']['F'],control['fleet']['F'])
    return dict(id=launches[0]['id'],warm_arms=[v['arm'] for v in values],all25_seed_ids_complete=True,
        full_semantic_trace_files=len(control['traces']),closure_witnesses_replayed=[v['closure_count'] for v in values],
        full_capacity_assigned_fleet_and_inventory_equal=True,physical_final=control['fleet'],
        CSV_metadata_excluded=sorted(csv_metadata),JSON_metadata_excluded=sorted(json_metadata))

def csv_json_match(name,values,keys):
    records=rows(OUT/(name+'.csv'));assert len(records)==len(values)
    index={tuple(v[k] for k in keys):v for v in values};assert len(index)==len(values)
    for row in records:
        value=index[tuple(int(row[k]) if k=='seed' else row[k] for k in keys)]
        for key,raw in row.items():
            expected=value.get(key)
            if expected is None:assert raw==''
            elif isinstance(expected,bool):assert raw.lower()==str(expected).lower()
            elif isinstance(expected,(int,float)):near(float(raw),expected,1e-10)
            elif isinstance(expected,(list,dict)):assert json.loads(raw)==expected
            else:assert raw==str(expected)
    return dict(name=name,rows=len(records),all_serialized_fields_equal=True)

def review_arm(launch,identity,fee):
    d=Path(launch['destination']);p=launch['panel'];saved=read(d/'launch.json');origin=read(d/'child_process_origin.json');affinity=read(d/'affinity.json')
    assert saved['command']==launch['command']==origin['command'] and saved['panel']==p and saved['seed']==launch['seed']
    assert saved['prereg_sha256']==identity['prereg_sha256'] and saved['runner_sha256']==sha(ROOT/'scripts/round121_campaign.py')
    assert origin['pid']==affinity['pid'] and origin['parent_pid']==affinity['parent']['launcher_pid']==fee['launch']['wrapper_pid']
    assert origin['actual_creation_unix']>=fee['launch']['wrapper_creation_unix'] and origin['creation_from_live_OS_handle']
    assert origin['seed']==launch['seed'] and origin['PE_SHA']==PE_SHA and origin['source_commit']=='355eefd2be3fe5651195681faf7b3a63ee4032f8'
    assert affinity['child']['process_mask']==affinity['parent']['effective']['process_mask']==4
    command=launch['command'];assert command.count('--gurobi-seed')==1 and command[command.index('--gurobi-seed')+1]==str(launch['seed'])
    for name,value in [('--threads','1'),('--mip-threads','1'),('--gurobi-presolve','-1'),('--process-shutdown-margin','30'),('--process-wall-time-limit',str(launch['cap_seconds']))]:assert command[command.index(name)+1]==value
    result=read(d/'result.json');completion=read(d/'completion.json');producer=read(d/'producer_receipt.json');seal=read(d/'producer_seal.json');total=read(d/'arm_total_receipt.json');closeout=read(d/'verification_closeout.json')
    assert producer['producer_seal_SHA']==sha(d/'producer_seal.json') and all(sha(d/n)==h for n,h in seal['required_SHA'].items())
    assert 'child_process_origin.json' in seal['required_SHA']
    assert producer['T_produce']==producer['t_produce_perf']-producer['t0_perf']<=launch['cap_seconds']
    assert total['T_verify']==total['t_verified_perf']-producer['t_produce_perf'] and total['T_total']==total['t_verified_perf']-producer['t0_perf']
    near(total['T_total'],producer['T_produce']+total['T_verify'],1e-8)
    assert producer['t0_unix']<=origin['actual_creation_unix']<=producer['t_produce_unix']<=total['t_verified_unix']<=fee['receipt']['caller_observed_unix']
    assert completion['returncode']==0 and completion['stop_reason']=='normal_return' and completion['within_cap']
    assert completion['fully_observed_end_to_end_seconds']<=read(d/'native_end_receipt.json')['complete_seconds_until_native_end']<=producer['T_produce']
    assert total['producer_receipt_SHA']==sha(d/'producer_receipt.json') and total['verification_closeout_SHA']==sha(d/'verification_closeout.json')
    for field,name in [('audit_SHA','audit.json'),('own_evidence_SHA','independent_evidence.json'),('claims_SHA','native_claims.json'),('rejection_SHA','claim_rejections.json'),('metrics_SHA','audit_execution_metrics.json')]:assert closeout[field]==sha(d/name)
    assert result['process_shutdown_margin_seconds']==30
    physical=physical_record(launch,result);j=journal(d,launch);native=call_evidence(d,launch,j);cover=coverage(d,launch,j,native,physical['F'])
    near(cover['L'],result['lower_bound']);assert cover['certificate']==result['strict_certified_original_problem']
    bound_witnesses=[]
    for w in j['witnesses']:
        if 'routes' in w:
            source=d/'journal'/f'event_{w["sequence"]}.json';fleet=physical_record(launch,w)
        else:
            source=Path(w.get('path',w.get('witness_path','')));assert source.is_file(),w
            fleet=physical_record(launch,read(source))
        near(fleet['F'],w.get('F',w.get('objective')));near(fleet['G'],w['G'])
        bound_witnesses.append(dict(G=fleet['G'],F=fleet['F'],source_SHA=sha(source),input_SHA=p['input_sha256']))
    bound_witnesses.append(dict(G=physical['G'],F=physical['F'],source_SHA=sha(d/'result.json'),input_SHA=p['input_sha256']))
    arm=dict(id=launch['id'],arm=launch['arm'],seed=launch['seed'],U=physical['F'],L=cover['L'],gap=physical['F']-cover['L'],
        certificate=cover['certificate'],certificate_qualified=True,numbers_qualified=True,formal_protocol_qualified=True,actually_executed=True,
        complete_seconds=producer['T_produce'],T_produce=producer['T_produce'],T_verify=total['T_verify'],T_total=total['T_total'])
    return dict(arm=arm,launch=launch,physical=physical,cover=cover,witnesses=bound_witnesses,native=native,journal=j,
                provenance=dict(pid=origin['pid'],creation_unix=origin['actual_creation_unix'],parent_pid=origin['parent_pid'],
                    origin_SHA=sha(d/'child_process_origin.json'),producer_SHA=sha(d/'producer_receipt.json'),seal_SHA=sha(d/'producer_seal.json'),
                    total_receipt_SHA=sha(d/'arm_total_receipt.json'),actual_calls=len(j['calls']),not_started_calls=len(j['cancelled'])))

def inputs_and_chronology():
    manifest=read(OUT/'input_manifest.json');recipe=read(OUT/'source_recipe.json');receipt=read(OUT/'generation_receipt.json')
    assert recipe['family']==manifest['family']==FAMILY and manifest['source_recipe_SHA']==sha(OUT/'source_recipe.json')
    assert recipe['generated_input_count']==0 and receipt['unique_new_input_files_written']==3 and receipt['Optimize']==receipt['native_starts']==0
    assert recipe['frozen_UTC']<receipt['generated_UTC'] and receipt['recipe_commit']==manifest['recipe_commit_before_generation']==RECIPE_COMMIT
    old_recipe_bytes=git('show',RECIPE_COMMIT+':results/unified_exact_round121/source_recipe.json')
    assert json.loads(old_recipe_bytes.decode('utf-8-sig'))==recipe
    old_adapter_bytes=git('show',RECIPE_COMMIT+':scripts/round121_data.py');current_adapter=(ROOT/'scripts/round121_data.py').read_bytes()
    assert old_adapter_bytes.decode('utf-8-sig').replace('\r\n','\n')==current_adapter.decode('utf-8-sig').replace('\r\n','\n')
    assert not git('ls-tree','-r','--name-only',RECIPE_COMMIT,'--','reference/round121_confirmation').strip()
    commit_date=git('show','-s','--format=%cI',RECIPE_COMMIT).decode().strip()
    assert datetime.datetime.fromisoformat(commit_date)<=datetime.datetime.fromisoformat(receipt['generated_UTC'])
    assert len(recipe['full_fixed_running_table'])==5 and sum(len(p['method_order']) for p in recipe['full_fixed_running_table'])==16
    assert all(not any(k in p for k in ['total_initial','total_target','sum_weights','empty_fleet']) for p in recipe['roles'])
    table=ROOT/'results/unified_exact_round116/source/source_station_table.csv';assert sha(table)==TABLE_SHA
    source_rows=rows(table);assert len(source_rows)==865
    snapshot=read(ROOT/'results/unified_exact_round116/source/snapshot.json');assert sha(ROOT/snapshot['station_response_path'])==RAW_SHA
    for name,digest in recipe['generation_dependencies'].items():assert sha(ROOT/name)==digest
    old_roles=read(ROOT/'results/unified_exact_round116/input_manifest.json')['roles']+read(ROOT/'results/unified_exact_round118/input_manifest.json')['roles']
    old_hashes=set(read(ROOT/'results/unified_exact_round116/historical_input_hash_index.json')['SHA_to_paths'])|{p['input_sha256'] for p in old_roles}
    overlap=[];checked=[]
    for role in manifest['new_roles']:
        path=ROOT/role['input_path'];digest=sha(path);assert digest==role['input_sha256'] and digest not in old_hashes
        v,m,q,actual=HELPERS['parse_instance'](path)
        chosen,depot,anchors=INPUTS['independent_selection'](source_rows,role)
        expected=INPUTS['independent_landscape'](source_rows,role,chosen)
        assert (v,m,q)==(role['V'],role['M'],role['Q_vector'])
        for name in ['capacities','initial','target','weights','min_ratio']:assert actual[name][1:]==expected[name],(role['id'],name)
        assert actual['points'][0]==tuple(depot)
        assert actual['points'][1:]==[tuple(round(float(source_rows[i][k]),3) for k in ['utm18n_easting_m','utm18n_northing_m']) for i in chosen]
        assert read(ROOT/role['selection_path'])['selected_source_station_row_indices']==chosen
        assert read(ROOT/role['landscape_path'])['dataset_family']==FAMILY
        empty=physical_record(dict(panel=role),dict(routes=[],upper_bound=role['empty_fleet']['F']))
        near(empty['G'],role['empty_fleet']['G']);near(empty['P'],role['empty_fleet']['P'])
        for old in old_roles:
            if old['V']<=50:
                old_selected=read(ROOT/old['selection_path'])['selected_source_station_row_indices']
                overlap.append(dict(id=role['id'],old_id=old['id'],old_V=old['V'],new_V=v,overlap=len(set(chosen)&set(old_selected))))
        history=git('log','--reverse','--format=%H%x09%cI','--diff-filter=A','--',role['input_path']).decode().splitlines();assert history
        first_commit,first_date=history[0].split('\t')
        assert first_commit!=RECIPE_COMMIT and datetime.datetime.fromisoformat(first_date)>datetime.datetime.fromisoformat(commit_date)
        near(sum(expected['weights']),role['sum_weights'],1e-12)
        checked.append(dict(id=role['id'],SHA=digest,B=sum(expected['initial']),D=sum(expected['target']),sum_weights=sum(expected['weights']),
            lambda_sum_weights=.15*sum(expected['weights']),all_expected_values_rederived_in_memory=True,first_input_commit=first_commit,first_input_commit_date=first_date))
    assert overlap==manifest['overlaps'] and len(overlap)==15
    assert len(list((ROOT/'reference/round121_confirmation').glob('*.txt')))==3
    adapter=current_adapter.decode('utf-8-sig')
    assert 'old.FAMILY=FAMILY;landscape_math.VERSION=FAMILY;landscape_math.SOURCE_SHA=RAW_SHA' in adapter
    assert "assert not REF.exists()" in adapter and "path.open('x'" in adapter
    return dict(new_inputs=checked,overlaps=overlap,source_rows=865,recipe_commit=RECIPE_COMMIT,recipe_commit_date=commit_date,
        recipe_committed_JSON_semantics_equal=True,adapter_committed_text_equal_after_explicit_CRLF_LF_normalization=True,
        adapter_git_blob_SHA=hashlib.sha256(old_adapter_bytes).hexdigest(),adapter_worktree_SHA=sha(ROOT/'scripts/round121_data.py'),
        adapter_Git_and_Windows_bytes_equal=old_adapter_bytes==current_adapter,recipe_Git_and_Windows_bytes_equal=old_recipe_bytes==(OUT/'source_recipe.json').read_bytes(),
        no_input_at_recipe_commit=True,generated_UTC=receipt['generated_UTC'],same_known_city_not_IID=True,
        no_filter_evidence='Precommitted recipe/adapter, deterministic in-memory expected-value replay, exclusive single creation, all three retained files and chronology; no H/LP/MIP or outcome branch exists in that data path.',
        epistemic_limit='These repository/process records cannot prove absence of unlogged external prior measurements. No new input file, source download, research draw or solver was produced by this reviewer.')

def deep_D1(item):
    l=item['launch'];d=Path(l['destination']);events=[json.loads(line) for line in text(d/'external/round120_events.jsonl').splitlines()]
    installed=[e for e in events if e['kind']=='root_formulation_installed'];assert len(installed)==1
    event=installed[0];path=Path(event['path']);meta=read(str(path)+'.round120.json');pair=read(d/'external/round120_root_pair.json')
    assert meta['conditional'] is True and sha(path)==meta['SHA']==event['model']
    base=path.with_name(path.name.replace('_round120_d1',''));assert sha(base)==meta['base_SHA']==event['base_model']
    model=HELPERS['lp'](path);original=HELPERS['lp'](base)
    assert model['objective']==original['objective'] and set(model['order'])-set(original['order'])=={'r120_h'}
    assert {n:t for n,t in model['types'].items() if n!='r120_h'}==original['types']
    assert {n:b for n,b in model['bounds'].items() if n!='r120_h'}==original['bounds']
    assert model['rows'][:-3]==original['rows'] and len(model['rows'])==len(original['rows'])+3
    assert model['types']['r120_h']=='B' and model['bounds']['r120_h']==(0.,1.)
    ld,ud,fd=map(float,[meta['lower_delta'],meta['upper_delta'],meta['objective_delta']])
    objective=dict(original['objective'][0]);objective['r120_h']=-fd
    expected=[({'G':1.,'r120_h':-ld},'>=',float(meta['lower_base'])),({'G':1.,'r120_h':-ud},'<=',float(meta['upper_base'])),(objective,'>=',float(meta['objective_base']))]
    assert model['rows'][-3:]==expected
    assert model['objective'][1]==float(meta['objective_constant'])
    q=Fraction.from_float
    a,m,b=[q(float(pair[k])) for k in ['a','m','b']];beta0,beta1=[q(float(pair[k])) for k in ['beta0','beta1']]
    assert a<m<b and pair['input_SHA']==l['panel']['input_sha256']
    decimal=[Fraction(meta[k]) for k in ['lower_base','lower_delta','upper_base','upper_delta','objective_base','objective_delta']];lb,dl,ub,du,fb,df=decimal;c=Fraction.from_float(model['objective'][1])
    assert lb<=a and lb+dl<=m and ub>=m and ub+du>=b and fb+c<=beta0 and fb+df+c<=beta1
    source_checks=[]
    for side,proof in enumerate(pair['proofs']):
        call=item['journal']['calls'][proof['call']];assert item['native']['entries'][proof['call']]['solve_kind']=='LP'
        assert call['model_sha256']==proof['model']==sha(Path(proof['path']))
        expected_interval=(float(a),float(m)) if side==0 else (float(m),float(b))
        assert (call['lower_g'],call['upper_g'])==expected_interval and call['cutoff']==proof['cutoff']
        source_model=HELPERS['lp'](Path(proof['path']));HELPERS['scope_check'](source_model,call,l['panel'])
        bound=next(p['L'] for p in item['native']['proofs'] if p['call']==proof['call'] and p['source']=='returned_actual_optimal_LP')
        near(bound,proof['bound']);beta=beta0 if side==0 else beta1
        assert beta<=q(min(bound,proof['cutoff']))-q(1e-7) if min(bound,proof['cutoff'])>=1e-7 else beta==0
        assert item['journal']['returns'][proof['call']]<min(c['sequence'] for c in item['journal']['calls'].values() if c['model_sha256']==meta['SHA'])
        source_checks.append(dict(side=side,call=proof['call'],model_SHA=proof['model'],interval=expected_interval,cutoff=proof['cutoff'],bound=bound,beta=float(beta),
            complete_matrix_rows=len(source_model['rows']),columns=len(source_model['order']),actual_true_G_and_cutoff_rows_checked=True,complement='F>cutoff independently supplies cutoff; no sibling or subdomain bound lifted outside its true-G interval'))
    native_checks=[]
    for native_path in sorted((d/'external/native_logs').glob('*.round120.native.json')):
        native=read(native_path);assert native['model_SHA']==meta['SHA'] and native['rows']==len(model['rows']) and native['columns']==len(model['order'])
        assert native['h_type']=='B' and native['h_LB']==0 and native['h_UB']==1 and native['h_BranchPriority']==0
        nl,nd,nu,ne,nf,ng,nc=[q(float(native[k])) for k in ['lower_base','lower_delta','upper_base','upper_delta','objective_base','objective_delta','objective_constant']]
        for key in ['lower_base','lower_delta','upper_base','upper_delta','objective_base','objective_delta','objective_constant']:assert float(native[key])==float(meta[key])
        assert nl<=a and nl+nd<=m and nu>=m and nu+ne>=b and nf+nc<=beta0 and nf+ng+nc<=beta1
        native_checks.append(dict(SHA=sha(native_path),binary64_exact_endpoint_slacks=[str(v) for v in [a-nl,m-(nl+nd),nu-m,nu+ne-b,beta0-nf-nc,beta1-nf-ng-nc]],
            actual_ObjCon=float(nc),h_type=native['h_type'],h_bounds=[native['h_LB'],native['h_UB']],branch_priority=native['h_BranchPriority']))
    starts=[]
    for start in sorted((d/'external/native_logs').glob('*.round68.start.json')):
        if read(start)['model_sha256']==meta['SHA']:starts.append(HELPERS['start_check'](start,model))
    assert starts and all(s['submitted'] for s in starts)
    G,F=item['physical']['G'],item['physical']['F'];h=0 if G<=float(m) else 1
    added_slacks=[G-(float(meta['lower_base'])+ld*h),(float(meta['upper_base'])+ud*h)-G,F-(float(meta['objective_base'])+fd*h+model['objective'][1])]
    assert min(added_slacks)>=-1e-7
    assert native_checks and any(e['kind']=='extended_native_returned' and e['attempted'] and e['return_code']==0 for e in events)
    return dict(id=l['id'],model_SHA=sha(path),base_SHA=sha(base),actual_rows=len(model['rows']),actual_columns=len(model['order']),
        complete_base_objective_rows_bounds_VTypes_retained=True,three_actual_added_rows_equal_full_objective_expression=True,
        decimal_exact_endpoint_slacks=[str(v) for v in [a-lb,m-lb-dl,ub-m,ub+du-b,beta0-fb-c,beta1-fb-df-c]],
        native_binary64_endpoint_checks=native_checks,source_LP_checks=source_checks,complete_Starts=starts,
        final_physical_endpoint=dict(G=G,P=item['physical']['P'],F=F,selected_physical_embedding_h=h,three_added_row_slacks=added_slacks),
        final_full_native_primal_vector='Not saved; full actual submitted Start was checked. Final physical inverse embedding checks the real fleet and added three rows, not an invented final solver vector.',
        conditional_numerical_not_rational_solver_certificate=True,internal_h_fixing_or_branching='unknown')

def fee_review():
    fees={}
    for path in sorted((OUT/'fees').glob('*/launch.json')):
        l=read(path);r=read(path.parent/'receipt.json');assert r['actual_exit_observed'] and not r['nested_native_seconds_added']
        assert r['conservative_process_starts']==1+r['actual_native_children'] and r['outer_seconds_upper']>=r['outer_seconds_lower']
        near(r['outer_seconds_upper'],max(r['outer_seconds_lower'],r['caller_observed_unix']-l['wrapper_creation_unix']),1e-8)
        assert l['qualification']==path.parent.name.startswith('qualification')
        fees[path.parent.name]=dict(launch=l,receipt=r,launch_SHA=sha(path),receipt_SHA=sha(path.parent/'receipt.json'))
    assert len(fees)==10 and all(fees[f'qualification{n:02d}']['receipt']['exit_code']==1 for n in range(1,5))
    assert fees['qualification05']['receipt']['exit_code']==0
    q=[v for k,v in fees.items() if k.startswith('qualification')];formal=[v for k,v in fees.items() if k.startswith('formal')]
    assert len(formal)==5 and all(v['receipt']['exit_code']==0 for v in formal)
    starts=sum(f['receipt']['conservative_process_starts'] for f in fees.values());seconds=sum(f['receipt']['outer_seconds_upper'] for f in fees.values())
    qs=sum(f['receipt']['conservative_process_starts'] for f in q);qt=sum(f['receipt']['outer_seconds_upper'] for f in q)
    assert (starts,qs)==(31,10);near(seconds,35578.67575955391,1e-8);near(qt,670.1436495780945,1e-8)
    assert starts<=40 and seconds<=48000 and qs<=12 and qt<=1800
    public=read(OUT/'resource_summary.json');assert (public['paid_starts'],public['qualification_starts'])==(starts,qs)
    near(public['paid_outer_seconds'],seconds,0.);near(public['qualification_seconds'],qt,0.)
    baseline=read(REVIEW/'resume_precontract_baseline.json')
    for name,saved in baseline['preserved_failed_fees'].items():
        assert all(sha(OUT/'fees'/name/n)==h for n,h in saved['files'].items())
    for arm,saved in baseline['preserved_producers'].items():
        raw=Path(saved['path']);assert all(sha(raw/n)==h for n,h in saved['files'].items())
        assert len([p for p in raw.rglob('*') if p.is_file()])==len(saved['files'])
        attempt=OUT/'qualification/resume01/recovery'/arm;receipt=read(attempt/'traceable_receipt.json')
        assert receipt['original_all_file_SHA']==saved['files'] and all(sha(attempt/n)==h for n,h in receipt['derived_file_SHA'].items())
        total=read(attempt/'arm_total_receipt.json');producer=read(raw/'producer_receipt.json')
        assert producer['T_produce']==saved['producer']['T_produce'] and total['T_verify']==total['t_verified_perf']-producer['t_produce_perf']
        assert total['T_verify']>receipt['replay_seconds'] and total['T_total']==total['t_verified_perf']-producer['t0_perf']
        assert read(raw/'audit.json')['passed']==saved['original_audit_passed'] and (raw/'arm_total_receipt.json').exists()==saved['original_closeout']
    qualification=read(OUT/'qualification/resume01/current_core.json');assert len(qualification['arms'])==4
    assert read(OUT/'qualification/actual_CLI_status.json')['actual_CLI']==4
    return fees,dict(starts=starts,outer_seconds=seconds,qualification_starts=qs,qualification_seconds=qt,closed_parent_fees=10,
        failed_parent_fees=4,formal_children=16,formal_wrappers=5,qualification_children=5,qualification_wrappers=5,
        original_P_MB_qualification_producers_not_rerun=True,original_P_MB_all_files_unchanged=True,
        original_two_qualification_child_OS_birth='Not persisted; not backfilled',persistent_recovery_clock_waiting_gaps_retained=True,
        main_clock='T_produce',component_native_seconds_not_added_twice=True,human_time='unknown',publication_and_review_outside_claim_bearing_resource_ledger=True)

def stage_rule(groups,pairs,mechanisms,identity_valid,contradictions):
    arms=[a for g in groups for a in g['arms']]
    complete=len(groups)==5 and len(arms)==16 and len(pairs)==18 and all(a['actually_executed'] and a['formal_protocol_qualified'] for a in arms)
    fresh_ids={'Q30-C2-B','Q40-R2-S','Q50-C2-U'}
    primary=[p for p in pairs if (p['candidate'],p['control'])==('MB-D1','P-GRB')]
    fresh=[p for p in primary if p['id'] in fresh_ids]
    exposed={m['id'] for m in mechanisms if m['id'] in fresh_ids and m['arm']=='MB-D1' and m['installed']>0 and m['extended_calls']>0}
    counts={method:sum(a['certificate'] for a in arms if a['arm']==method) for method in ['MB-D1','M-B']}
    conditions=dict(three_once_only_postfreeze_new_inputs=identity_valid and len(fresh)==3,
        all_three_new_primary_evaluable=len(fresh)==3 and all(p['evaluable'] for p in fresh),
        new_primary_at_least_two_WIN_at_most_one_LOSS=sum(p['classification']=='WIN' for p in fresh)>=2 and sum(p['classification']=='LOSS' for p in fresh)<=1,
        at_least_two_new_D1_native_exposures=len(exposed)>=2,
        exposed_new_material_M_B_gain_or_new_certificate=any(p['id'] in exposed and (p['candidate'],p['control'])==('MB-D1','M-B') and p['classification']=='WIN' for p in pairs),
        all_five_primary_evaluable=len(primary)==5 and all(p['evaluable'] for p in primary),no_severe_primary_risk=not any(p['severe_regression'] for p in primary),
        D1_certificate_count_preserved=counts['MB-D1']>=counts['M-B'],
        both_fixed_Seed1_blocks_complete=all(any(g['id']==name and g['seed']==1 and all(a['formal_protocol_qualified'] for a in g['arms']) for g in groups) for name in ['F2','R98-C2']))
    veto=dict(any_of_five_severe_D1_P=any(p['severe_regression'] for p in primary),two_or_more_new_D1_P_LOSS=sum(p['classification']=='LOSS' for p in fresh)>=2,D1_fewer_certificates_than_M_B=counts['MB-D1']<counts['M-B'])
    if contradictions:stage='PROOF_RELIABILITY_PRIORITY'
    elif not complete:stage='BLOCKED'
    elif any(veto.values()):stage='STOP_FROZEN_D1_CONFIRMATION'
    elif all(conditions.values()):stage='ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK'
    else:stage='RETAIN_D1_AS_DEVELOPMENT_COMPONENT'
    return dict(execution_stage='COMPLETE' if complete else 'BLOCKED',stage=stage,conditions=conditions,veto=veto,
        certificate_counts=dict(D1=counts['MB-D1'],M_B=counts['M-B']),exposed_new_roles=sorted(exposed),formal_arms=len(arms),formal_pairs=len(pairs),
        full_priority=['PROOF_RELIABILITY_PRIORITY','BLOCKED','STOP_FROZEN_D1_CONFIRMATION','ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK','RETAIN_D1_AS_DEVELOPMENT_COMPONENT'])

def main():
    tick=time.perf_counter();print('Independent final review: identity/generation/fees',flush=True)
    candidate=read(OUT/'candidate_identity.json');gate=read(REVIEW/'resume_precontract.json')
    assert candidate['helpers']==gate['helpers'] and len(candidate['helpers'])==89 and len(candidate['source_bindings'])==216
    for name,digest in {**candidate['helpers'],**candidate['source_bindings']}.items():assert sha(ROOT/name)==digest
    assert sha(ROOT/'build/research/round120/ExactEBRP.exe')==candidate['production_PE_SHA']==PE_SHA
    assert sha(Path('D:/gurobi1302/win64/bin/gurobi130.dll'))==candidate['DLL_SHA']==DLL_SHA
    frozen_candidate=json.loads(git('show',RUNTIME_FREEZE+':results/unified_exact_round121/candidate_identity.json').decode('utf-8-sig'))
    assert frozen_candidate['helpers']==candidate['helpers'] and frozen_candidate['source_bindings']==candidate['source_bindings']
    assert sha(OUT/'candidate_identity.json')==gate['candidate_identity_SHA'] and sha(OUT/'protocol.json')==gate['protocol_SHA']
    generation=inputs_and_chronology();fees,resource=fee_review()
    all_arms=read(OUT/'all16_arms.json');published_pairs=read(OUT/'all18_pairs.json');argv=read(OUT/'argv_freeze.json');items=[];groups=[];pairs=[];mechanisms=[];full_H=[]
    assert candidate['argv_freeze_SHA']==sha(OUT/'argv_freeze.json') and candidate['input_manifest_SHA']==sha(OUT/'input_manifest.json')
    expected_keys=[];seen_origins=set();model_cache={}
    for number,(role,seed,cap,methods) in enumerate(EXPECTED,1):
        plan=argv['groups'][number-1];assert (plan['id'],plan['seed'],plan['cap_seconds'],plan['methods'])==(role,seed,cap,methods)
        identity_path=OUT/plan['campaign']/'identity.json';identity=read(identity_path)
        assert candidate['campaign_identities'][plan['campaign']]==sha(identity_path)
        assert identity['helpers']==candidate['helpers'] and identity['source_hashes']==candidate['source_bindings']
        assert identity['prereg_sha256']==sha(OUT/'protocol.json') and identity['candidate_binary_sha256']==PE_SHA and identity['dll_sha256']==DLL_SHA
        frozen_launches=next(p for p in argv['plans'] if p['name']==plan['campaign'])['launches']
        assert len(identity['launches'])==len(frozen_launches)==len(methods)
        for frozen,actual in zip(frozen_launches,identity['launches']):
            resolved=copy.deepcopy(frozen);reference=actual['panel']['reference'];resolved['panel']['reference']=reference
            resolved['command']=[str(reference['fingerprint']) if arg=='REFERENCE_FINGERPRINT' else arg for arg in resolved['command']]
            assert resolved==actual
        fee=next(f for name,f in fees.items() if name.startswith(f'formal{number:02d}_'));group_arms=[]
        for launch in identity['launches']:
            print('Review actual arm '+role+' / '+launch['arm'],flush=True)
            assert launch['arm'] in methods and launch['seed']==seed and launch['cap_seconds']==cap
            item=review_arm(launch,identity,fee);items.append(item);a=item['arm'];group_arms.append(a)
            origin=(item['provenance']['pid'],item['provenance']['creation_unix']);assert origin not in seen_origins;seen_origins.add(origin)
            expected_keys.append((role,seed,launch['arm']))
            recorded=next(a for a in all_arms if (a['id'],a['seed'],a['arm'])==(role,seed,launch['arm']))
            for key in ['U','L','gap','T_produce','T_verify','T_total']:near(recorded[key],a[key],1e-8)
            for key in ['certificate','formal_protocol_qualified','actually_executed']:assert recorded[key]==a[key]
            event_path=Path(launch['destination'])/'external/round120_events.jsonl'
            if event_path.exists():
                events=[json.loads(s) for s in text(event_path).splitlines()];assert [e['sequence'] for e in events]==list(range(1,len(events)+1))
                install=[e for e in events if e['kind']=='root_formulation_installed'];returns=[e for e in events if e['kind']=='extended_native_returned' and e['attempted']]
                assert not any(e['kind'] in ['revoked','termination_requested','atomic_contraction_committed'] for e in events)
                for e in returns:assert e['call'] in item['journal']['returns'] and e['return_code']==0
                mechanisms.append(dict(id=role,arm=launch['arm'],enabled=True,installed=len(install),extended_calls=len(returns),
                    paid_root_sides=[e['side'] for e in events if e['kind']=='paid_root_LP_returned'],
                    pair_present=(Path(launch['destination'])/'external/round120_root_pair.json').exists(),events_SHA=sha(event_path),h_fixing_or_branching='unknown'))
        assert [a['arm'] for a in group_arms]==methods
        full_H.append(complete_H(identity['launches']))
        by={a['arm']:a for a in group_arms}
        for c,p in PAIRS6 if number==1 else PAIRS3:
            pairs.append(dict(id=role,seed=seed,**comparison(by[c],by[p])))
        groups.append(dict(id=role,seed=seed,arms=group_arms))
    assert len(all_arms)==len(set(expected_keys))==16 and len(published_pairs)==len(pairs)==18
    csv_matches=[csv_json_match('all16_arms',all_arms,['id','seed','arm']),csv_json_match('all18_pairs',published_pairs,['id','seed','candidate','control'])]
    assert min(i['provenance']['creation_unix'] for i in items)>datetime.datetime.fromisoformat(generation['generated_UTC']).timestamp()
    for value in pairs:
        published=next(p for p in published_pairs if (p['id'],p['candidate'],p['control'])==(value['id'],value['candidate'],value['control']))
        for key in ['classification','severe_regression','evaluable']:assert published[key]==value[key],(value,published)
        for key in ['a_U','a_gap','a_t','UB_improvement','gap_improvement','LB_change']:
            if key in value and value[key] is not None:near(published[key],value[key],1e-12)
        by={a['arm']:a for g in groups if g['id']==value['id'] for a in g['arms']};c,p=by[value['candidate']],by[value['control']]
        near((c['gap']-p['gap']),(c['U']-p['U'])-(c['L']-p['L']),1e-12)
        for key,expected in [('dU',c['U']-p['U']),('dL',c['L']-p['L']),('dgap',c['gap']-p['gap'])]:near(published[key],expected,1e-12)
    contradictions=[]
    for item in items:
        for proof in item['native']['proofs']:
            for other in items:
                if other['launch']['panel']['input_sha256']!=item['launch']['panel']['input_sha256']:continue
                for w in other['witnesses']:
                    if proof['lo']<=w['G']<=proof['hi'] and w['F']<=proof['cutoff'] and proof['L']>w['F']+1e-7:contradictions.append(dict(id=item['arm']['id'],proof=proof,witness=w))
    decision=stage_rule(groups,pairs,mechanisms,True,contradictions);recorded=read(OUT/'stage_decision.json')
    for key in ['execution_stage','stage','conditions','veto','certificate_counts','formal_arms','formal_pairs']:assert decision[key]==recorded[key],(key,decision[key],recorded[key])
    assert not contradictions
    print('Review new D1 complete physical/three-row/native/Start/source endpoint',flush=True)
    deep=deep_D1(next(i for i in items if i['arm']['id']=='Q30-C2-B' and i['arm']['arm']=='MB-D1'))
    objective=rows(OUT/'objective_parts.csv');assert len(objective)==16
    for item in items:
        row=next(r for r in objective if r['id']==item['arm']['id'] and r['arm']==item['arm']['arm'])
        for k in ['G','P','lambda_P','F']:near(float(row[k]),item['physical'][k],1e-12)
    old=read(OUT/'preflight_R120_pair_replay.json');old_classes={};old_counts=collections.Counter()
    for group in old['saved_groups']:
        by={a['arm']:a for a in group['arms']}
        for p in group['pairs']:
            cmp=comparison(by[p['candidate']],by[p['control']]);assert cmp['classification']==p['classification'] and cmp['severe_regression']==p['severe_regression']
            old_classes[(group['arms'][0]['id'],p['candidate'],p['control'])]=cmp;old_counts[cmp['classification']]+=1
    layers=read(OUT/'seed_stratification.json');assert (layers['new_problem_denominator'],layers['known_Seed1_block_denominator'],layers['arm_denominator'],layers['pair_denominator'])==(3,2,16,18)
    for row in layers['sensitivity']:
        old_cmp=old_classes[(row['id'],row['candidate'],row['control'])];new_cmp=next(p for p in pairs if (p['id'],p['candidate'],p['control'])==(row['id'],row['candidate'],row['control']))
        assert (row['Seed0'],row['Seed1'],row['Seed0_severe'],row['Seed1_severe'],row['WIN_to_LOSS'])==(old_cmp['classification'],new_cmp['classification'],old_cmp['severe_regression'],new_cmp['severe_regression'],old_cmp['classification']=='WIN' and new_cmp['classification']=='LOSS')
    assert layers['no_best_of_Seeds'] and layers['no_pooled_exact_mean_or_win_rate']
    report=text(OUT/'final_report.md');spec=text(OUT/'paper_algorithm_spec.md');claims=text(OUT/'paper_claim_evidence_map.md')
    assert 'ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK' in report and 'New-input D1 complete certificates: 0/3' in report
    assert 'ENS-C remains default' in report and 'D0 remains' in report and 'R119 MB-PC remains stopped' in report
    assert decision['certificate_counts']==dict(D1=1,M_B=1)
    assert all(not i['arm']['certificate'] for i in items if i['arm']['id'] in ['Q30-C2-B','Q40-R2-S','Q50-C2-U'])
    public_mechanism=read(OUT/'mechanism_account.json')
    for m in mechanisms:
        original=next(r for r in public_mechanism['mechanism'] if r['id']==m['id'] and r['arm']==m['arm'])
        assert original['installed']==m['installed'] and original.get('actual_extended_Optimize',0)==m['extended_calls']
    assert [(m['installed'],m['extended_calls']) for m in mechanisms if m['id'] in ['Q30-C2-B','Q40-R2-S','Q50-C2-U']]==[(1,1),(1,2),(0,0)]
    for name in ['all16_arms.csv','all18_pairs.csv','paper_algorithm_spec.md','paper_claim_evidence_map.md','mechanism_account.json','seed_stratification.json','final_report.md','stage_decision.json','source_recipe.json','input_manifest.json','generation_receipt.json','argv_freeze.json','protocol.json','candidate_identity.json','resource_summary.json']:sha(OUT/name)
    prior=read(REVIEW/'extra_review_complete01_first_pass.json')
    prior_execution=dict(decision=prior['decision'],seconds=prior['seconds'],report_SHA=sha(REVIEW/'extra_review_complete01_first_pass.json'),
        script_SHA=sha(REVIEW/'extra_review_complete01_first_pass.py'),MD_SHA=sha(REVIEW/'extra_review_complete01_first_pass.md'),
        reason_for_final_run='Close exact frozen-plan/campaign identity binding, full-H semantic traces and JSON/CSV parity with actual data; no scientific file change.')
    output=dict(decision='ACCEPT_FINITE_COMPLETE_REVIEW',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),script_SHA=sha(__file__),
        actual_different_executor=True,method='Independent sparse LP/type/scope and full physical arithmetic; fresh verbal pair/stage implementation; committed recipe semantics and actual journals/log spans; no audited pair/decide/campaign function called.',
        independent_stage=decision,all18_recomputed_pairs=pairs,all16_recomputed_arms=[i['arm'] for i in items],
        all16_physical_endpoints=[dict(id=i['arm']['id'],arm=i['arm']['arm'],**i['physical']) for i in items],
        actual_launch_origins=[dict(id=i['arm']['id'],arm=i['arm']['arm'],**i['provenance']) for i in items],
        all16_complete_frozen_argv_equal=True,all16_and_all18_CSV_JSON=csv_matches,all_five_complete_H=full_H,
        actual_calls_and_scope_types=[dict(id=i['arm']['id'],arm=i['arm']['arm'],spans=i['native']['spans'],coverage=i['cover']) for i in items],
        source_counterexamples=contradictions,actual_mechanisms=mechanisms,new_D1_full_endpoint_three_rows_Start_source_scope=deep,
        new_input_identity_and_selection=generation,resource=resource,old_R120_pair_replay_classifications=dict(old_counts),Seed_sensitivity=layers['sensitivity'],
        new_D1_certificates=0,new_input_denominator=3,known_Seed1_block_denominator=2,default_ENS_changed=False,M_B_retained=True,D0_not_promoted=True,R119_MB_PC_remains_stopped=True,
        scope_limits=['No native execution, Optimize, compilation, new input, redraw, route, bound or LP was produced.',
            'One new D1 complete matrix/Start/source/selector endpoint was deeply parsed; all16 physical fleets, actual call-scoped types/scopes, returned proofs and complete finite cover bookkeeping were independently checked.',
            'The final native incumbent full primal vector was not saved. Its physical routes and three-row inverse embedding were checked; a complete actual submitted Start vector and every row/type/readback were checked.',
            'Native numeric certificates remain conditional at the original 1e-7 evidence policy, not rational-exact solver certificates; h fixing/branching remains unknown.',
            'Original P/MB qualification child OS birth timestamps are absent and not backfilled. Their original files and long postseal waits remain; recovered derived closeouts do not replace old failed audit files.',
            'Git checks are limited read-only commit/blob/history queries. Old Git LF versus Windows CRLF is explicit transport normalization, not falsely byte-identical freeze evidence.',
            'Unlogged external prior measurements cannot be excluded. The recorded fixed single generation and no-filter code path were checked; same-city subsets are not IID or new cities.',
            'Public carrier/empty-root recovery, publication safety, index bytes and remote PR observations are separately scoped; this scientific review does not certify those later actions.'],
        prior_read_only_review_execution=prior_execution,evidence_SHA=dict(sorted(FILES.items())),reviewer_native_starts=0,reviewer_Optimize=0,reviewer_compiles=0,reviewer_Git_mutations=0,
        seconds=time.perf_counter()-tick,human_time='unknown')
    destination=REVIEW/'extra_review_complete01.json'
    with destination.open('x',encoding='utf-8') as f:json.dump(output,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    md=['# Independent final Round121 extra review','','**ACCEPT: COMPLETE / '+decision['stage']+'.** The finite candidate criteria are met; this is not default adoption or a universal performance claim.','',
        'A different executor recomputed all 18 comparisons and the entire proof-risk/blocker/veto/support priority with a fresh implementation, without calling the audited pair/decide functions. All 16 physical fleets, signed gaps, objective parts, actual Seeds/live-OS birth receipts, producer seals, three clocks, returned call logs, actual model types/scopes and complete finite cover bookkeeping were checked. Each full actual argv equals the prospective plan with only the predetermined reference fingerprint resolved; all five campaign identity hashes bind to the candidate. Both CSV tables equal their JSON records in every serialized field. All five complete-H groups retain all25 descent seeds, complete nonmetadata semantic traces, capacity-assigned fleets and final inventories; closure final witnesses were also physically replayed. Source/PE/DLL and all216 production source/all89 runtime helper hashes match the frozen identities.','',
        'All three new D1/P comparisons are WIN. New D1/M-B is TIE/WIN/TIE. Q30 has one actual expanded native call; Q40 has two; Q50 has no installation or expanded call and only the paid left root LP. Two exposed new roles satisfy the exposure criterion, and Q40 supplies the exposed direct-M-B material WIN. New-input certificates are 0/3; D1 and M-B each have only the F2 certificate.','',
        'The Q30 actual complete D1 matrix retains every original objective, row, bound and VType plus one binary and three rows. Full source-LP matrices and true-G/cutoff domains, successful returned optimal logs and conservative beta margins were parsed. Decimal and actual native binary64 h=0/1 endpoints include ObjCon. Every submitted Start column/type/value/readback and every complete row was recomputed. The final physical fleet, true G, P and added-row embedding were checked. No final full native incumbent vector was invented; no internal h fixing/branching is inferred.','',
        'The three source-derived new inputs were rederived only in memory against the precommitted recipe/adapter and all15 old overlaps. The generation commit precedes the first input commit and native measurements. Git recipe JSON was compared semantically and adapter text after explicit LF/CRLF normalization; old Git bytes were not claimed identical to Windows bytes. This proves the recorded prospective single-generation path, not the absence of unlogged external work.','',
        'F2 D0/M-B changes from Seed0 WIN to Seed1 LOSS. R120 C2 direct-M-B severe LOSS and primary ordinary LOSS remain visible despite Seed1 WIN. The three-new-problem and two-known-Seed-block denominators remain separate, without best-of-Seed selection or pooled independent-sample claims.','',
        f'All failed fees remain charged: {resource["starts"]}/40 starts and {resource["outer_seconds"]:.12f}/48000 outer seconds; qualification {resource["qualification_starts"]}/12 and {resource["qualification_seconds"]:.12f}/1800. Original P/MB qualification producers were not rerun; all original files and failed audits are intact, and their recovered T_verify includes the entire wait. Original two qualification OS birth records were absent; all16 formal births are live-OS receipts sealed during production. Native component time is not added twice. Human time is unknown.','',
        'ENS-C stays default, M-B is retained, D0 is not promoted and R119 MB-PC remains stopped. Zero new native starts/Optimize/compilation and zero Git mutations were performed. Publication/recovery/index/remote receipts are outside this scientific verdict. Exact evidence SHA bindings and finite coverage details are in the JSON.','']
    with (REVIEW/'extra_review_complete01.md').open('x',encoding='utf-8') as f:f.write('\n'.join(md))
    print(json.dumps(dict(decision=output['decision'],stage=decision['stage'],arms=16,pairs=18,seconds=output['seconds'],native_starts=0,Optimize=0)),flush=True)

if __name__=='__main__':main()

