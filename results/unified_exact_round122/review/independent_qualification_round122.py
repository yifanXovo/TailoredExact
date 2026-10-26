"""Independent qualification closeout; reads sealed evidence, no native work."""
from pathlib import Path
from fractions import Fraction
import ast, collections, csv, datetime, hashlib, json, math, re, time
import independent_contract_round122 as contract
from independent_review_round122 import read,sha,save_receipt

ROOT=contract.ROOT;OUT=contract.OUT;REVIEW=contract.REVIEW
USED={}
def rd(path):
    path=Path(path);USED[str(path)]=sha(path);return read(path)
def checked_bytes(path):
    path=Path(path);USED[str(path)]=sha(path);return path.read_bytes()
def csvrows(path):
    path=Path(path);USED[str(path)]=sha(path)
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def portable(value):
    path=Path(value);assert path.resolve().is_relative_to(ROOT.resolve()),value;return path

def instance(p):
    text=checked_bytes(ROOT/p['input_path']).decode();lines=text.splitlines()
    v,m,q=lines[0].split(maxsplit=2);a={}
    for line in lines[1:]:
        key,value=line.split('=',1);a[key.strip()]=ast.literal_eval(value)
    assert (int(v),int(m),ast.literal_eval(q))==(p['V'],p['M'],p['Q_vector'])
    return a

def physical(p,a,w):
    Y=a['initial'].copy();seen=set();by={r.get('vehicle',r.get('vehicle_id')):r for r in w['routes']}
    assert len(by)==len(w['routes']) and set(by)<=set(range(p['M']))
    facts=[]
    for k,Q in enumerate(p['Q_vector']):
        route=by.get(k,dict(nodes=[0,0],operations=[]));nodes=route['nodes']
        assert nodes[0]==nodes[-1]==0
        ops={}
        for op in route['operations']:
            i,pick,drop=(op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else op
            assert i not in ops;ops[i]=(pick,drop)
        assert set(ops)==set(nodes[1:-1]) and len(set(nodes[1:-1]))==len(nodes[1:-1])
        load=0;pickups=0;loads=[0]
        for i in nodes[1:-1]:
            assert 1<=i<=p['V'] and i not in seen;seen.add(i)
            pick,drop=ops[i]
            assert pick>=0 and drop>=0 and (pick>0) != (drop>0)
            assert abs(pick-round(pick))<1e-7 and abs(drop-round(drop))<1e-7
            load+=pick-drop;pickups+=pick;Y[i]+=drop-pick
            assert -1e-7<=load<=Q+1e-7 and -1e-7<=Y[i]<=a['capacities'][i]+1e-7;loads.append(load)
        travel=sum(math.hypot(a['points'][u][0]-a['points'][v][0],a['points'][u][1]-a['points'][v][1])/1.5 for u,v in zip(nodes,nodes[1:]))
        duration=travel+(p['pickup_seconds']+p['drop_seconds'])*pickups
        assert duration<=p['T_seconds']+1e-7
        facts.append(dict(vehicle=k,Q=Q,nodes=nodes,operations=sorted((i,*ops[i]) for i in ops),return_load=load,pickups=pickups,duration=duration,loads=loads))
    ratios=[Y[i]/a['target'][i] for i in range(1,p['V']+1)];S=sum(ratios)
    G=sum(abs(x-y) for j,x in enumerate(ratios) for y in ratios[j+1:])/(len(ratios)*S) if S else 0.
    P=sum(a['weights'][i]*abs(ratios[i-1]-1) for i in range(1,p['V']+1))
    return dict(Y=Y,G=G,P=P,F=G+p['lambda']*P,fleet=facts)

def model_check(p,a,path,c,arm):
    USED[str(path)]=sha(path);order,bounds,vtypes,rows,obj=contract.lp_reference(path)
    if not c['full_original']:
        assert bounds['G']==(c['lower_g'],c['upper_g'])
        assert (obj[0],'<=',c['cutoff']-obj[1]) in rows
        for gamma,sense in [(c['upper_g'],'<='),(c['lower_g'],'>=')]:
            terms={f'h_{i}_{j}':1. for i in range(1,p['V']+1) for j in range(i+1,p['V']+1)}
            if gamma:
                for i in range(1,p['V']+1):terms[f'r_{i}']=-p['V']*gamma
            assert (terms,sense,0.) in rows
        quantities=[n for n in order if n.startswith(('p_','d_'))]
        assert len(quantities)==2*p['M']*p['V']
        assert all(vtypes[n]==('I' if arm=='ENS-C' else 'C') for n in quantities)
        assert all(vtypes[n] in ['I','B'] for n in order if n.startswith(('x_','load_','Y_')))
        assert all(vtypes[n]=='B' for n in order if n.startswith(('mode_','z_','state_')) and not n.startswith('state_g_'))
        if arm in ['M-B','MB-D1']:
            for i in range(1,p['V']+1):
                terms={n:1. for n in quantities if n.endswith('_'+str(i))}
                for n in order:
                    if re.fullmatch(r'state_'+str(i)+r'_\d+',n):
                        amount=abs(a['initial'][i]-int(n.rsplit('_',1)[1]))
                        if amount:terms[n]=-float(amount)
                assert (terms,'=',0.) in rows
                terms={f'z_{k}_{i}':1. for k in range(p['M'])};name=f'state_{i}_{a["initial"][i]}'
                if name in vtypes:terms[name]=1.
                assert (terms,'=',1.) in rows
    return order,bounds,vtypes,rows,obj

def start_check(model,log,p,a,d):
    order,bounds,vtypes,rows,obj=model
    meta_path=Path(str(log)+'.round68.start.json')
    if not meta_path.exists():return None
    meta=rd(meta_path);values=csvrows(Path(str(log)+'.round68.start.values.csv'))
    assert meta['mapping_complete'] and meta['submitted'] and meta['readback_valid'] and meta['objective_valid']
    vector={r['variable']:float(r['value']) for r in values}
    assert len(vector)==len(values)==len(order) and set(vector)==set(order)
    for r in values:
        n=r['variable'];x=vector[n]
        assert float(r['readback'])==x and r['type']==vtypes[n]
        assert bounds[n][0]-1e-7<=x<=bounds[n][1]+1e-7
        if vtypes[n] in ['I','B']:assert abs(x-round(x))<=1e-7
    violation=0.
    for terms,sense,rhs in rows:
        lhs=math.fsum(coef*vector[name] for name,coef in terms.items())
        delta=abs(lhs-rhs) if sense=='=' else max(0,lhs-rhs) if sense=='<=' else max(0,rhs-lhs)
        violation=max(violation,delta)
    assert violation<=1e-7,('Start residual',violation)
    objective=obj[1]+math.fsum(coef*vector[name] for name,coef in obj[0].items())
    assert abs(objective-meta['objective'])<=1e-7
    witness=rd(d/'external'/(meta['source']+'_witness.json'));phys=physical(p,a,witness)
    assert abs(objective-phys['F'])<=1e-7
    return dict(source=meta['source'],columns=len(vector),maximum_row_violation=violation,objective=objective,
        submitted=meta['submitted'],API_readback_equal=True,status=meta['status'],
        new_native_incumbent_observed=meta.get('exact_vector_observed_in_mipsol'),
        h_type=vtypes.get('r120_h'),h_value=vector.get('r120_h'),physical_F=phys['F'])

def h_review(p,a,d):
    CSV_META={'process_seconds','elapsed_seconds','elapsed','timestamp','wall_seconds'}
    JSON_META={'sha256','elapsed_seconds','process_seconds','wall_seconds','timestamp','path'}
    def semantic(v):
        if isinstance(v,dict):return {k:semantic(x) for k,x in v.items() if k not in JSON_META}
        if isinstance(v,list):return [semantic(x) for x in v]
        return v
    traces={}
    for path in sorted(d.glob('hga.csv.*.csv')):
        traces[path.name]=[{k:v for k,v in r.items() if k not in CSV_META} for r in csvrows(path)]
    base=d/'hga.csv.exchange'
    for path in sorted(base.iterdir()):
        if path.suffix=='.csv':traces['exchange/'+path.name]=[{k:v for k,v in r.items() if k not in CSV_META} for r in csvrows(path)]
        elif path.suffix=='.json':traces['exchange/'+path.name]=semantic(rd(path))
        elif path.suffix=='.jsonl':traces['exchange/'+path.name]=[semantic(json.loads(s)) for s in checked_bytes(path).decode().splitlines()]
    descent=traces['hga.csv.descent.csv']
    assert {int(r['seed']) for r in descent}==set(range(1,26)) and not any(r.get('interrupted')=='1' for r in descent)
    final=physical(p,a,rd(base/'final.json'))
    for path in base.glob('*.final.json'):physical(p,a,rd(path))
    return traces,final

def arm_review(l,i,endpoint,fee_pid):
    p=l['panel'];a=instance(p);d=portable(l['destination'])
    assert endpoint['formal_protocol_qualified'] and endpoint['actually_executed'] and endpoint['numbers_qualified']
    assert endpoint['native_proof_qualified'] and not endpoint['source_reduced'] and not endpoint['rejected_calls']
    seal=rd(d/'producer_seal.json');producer=rd(d/'producer_receipt.json');total=rd(d/'arm_total_receipt.json')
    assert producer['producer_seal_SHA']==sha(d/'producer_seal.json')
    for n,h in seal['required_SHA'].items():assert sha(d/n)==h;USED[str(d/n)]=h
    audit=rd(d/'audit.json');close=rd(d/'verification_closeout.json');r=rd(d/'result.json');completion=rd(d/'completion.json')
    assert audit['passed'] and audit['independent_evidence_audit_passed'] and audit['native_proof_qualified']
    assert close['audit_SHA']==sha(d/'audit.json') and total['verification_closeout_SHA']==sha(d/'verification_closeout.json')
    assert close['producer_receipt_SHA']==total['producer_receipt_SHA']==sha(d/'producer_receipt.json')
    assert total['T_verify']==total['t_verified_perf']-producer['t_produce_perf'] and total['T_total']==total['t_verified_perf']-producer['t0_perf']
    assert abs(total['T_total']-producer['T_produce']-total['T_verify'])<1e-8 and producer['T_produce']<=120
    assert endpoint['T_produce']==producer['T_produce'] and endpoint['T_verify']==total['T_verify'] and endpoint['T_total']==total['T_total']
    assert completion['stop_reason']=='normal_return' and completion['returncode']==0 and completion['within_cap']
    birth=rd(d/'child_process_origin.json');launch=rd(d/'launch.json');affinity=rd(d/'affinity.json')
    assert birth['creation_from_live_OS_handle'] and birth['parent_pid']==fee_pid and birth['command']==launch['command']==l['command']
    assert birth['seed']==l['seed'] and birth['PE_SHA']==contract.PE_SHA
    assert affinity['pid']==birth['pid'] and affinity['child']['process_mask']==4
    resultphysical=physical(p,a,r)
    assert abs(resultphysical['F']-endpoint['U'])<1e-7 and abs(endpoint['U']-endpoint['L']-endpoint['gap'])<1e-12
    observations=rd(d/'observations.json');views=rd(d/'call_log_views.json');contracts=rd(d/'round120_model_contracts.json')
    calls={q['payload']['call']:q['payload'] for q in observations if q['payload']['kind']=='call'}
    returned={q['payload']['call'] for q in observations if q['payload']['kind']=='returned'}
    not_started={q['payload']['call'] for q in observations if q['payload']['kind']=='not_started'}
    assert not not_started and returned==set(calls)=={b['call'] for b in views['bindings']}
    assert views['actual_Optimize']==len(calls)==endpoint['native_Optimize'] and len(contracts['contracts'])==len(calls)
    expected=dict(read_return_code=0,Threads=1,Seed=l['seed'],Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
    model_cache={};starts=[];facts=[]
    for b in views['bindings']:
        c=calls[b['call']];assert c['settings']==expected
        if l['seed']==1:assert not c['native_preconditions']
        path=portable(c['model_path']);log=portable(c['native_log_path'])
        assert sha(path)==c['model_sha256']==b['model_SHA'] and sha(log)==b['raw_log_SHA']
        data=checked_bytes(log);segment=data[b['byte_begin']:b['byte_end']]
        assert hashlib.sha256(segment).hexdigest()==b['segment_SHA'] and b['journal_returned'] and b['return_code']==0
        assert segment.count(b'Optimize a model with ')==1
        if c['model_sha256'] not in model_cache:model_cache[c['model_sha256']]=model_check(p,a,path,c,l['arm'])
        model=model_cache[c['model_sha256']]
        size=re.search(rb'Optimize a model with (\d+) rows, (\d+) columns',segment);assert size
        assert (int(size[1]),int(size[2]))==(len(model[3]),len(model[0]))
        if b['solve_kind']!='LP':
            start=start_check(model,log,p,a,d)
            if l['arm']=='P-GRB':assert start is None and r['gurobi_hga_start_requested'] is False
            else:assert start is not None;starts.append(start)
        facts.append(dict(call=b['call'],leaf=c['leaf'],solve_kind=b['solve_kind'],model_SHA=c['model_sha256'],
            lower_g=c['lower_g'],upper_g=c['upper_g'],cutoff=c['cutoff'],raw_native_preconditions=c['native_preconditions']))
    if l['seed']==1:
        seed=rd(d/'computed_seed_scope.json');assert seed['actual_seed']==1 and seed['raw_flags_preserved']
        recovered={x['call'] for x in seed['recovered_calls']}
        assert recovered=={b['call'] for b in views['bindings'] if b['solve_kind']!='LP'}
        assert all(not q['payload']['global_available'] and q['payload']['global_bound'] is None for q in observations if q['payload']['kind']=='bound')
    extended=rd(d/'round120_extended_verification.json');event=extended['event_contract']
    if l['arm']=='MB-D1':
        pair=rd(d/'external/round120_root_pair.json');assert pair['input_SHA']==p['input_sha256'] and event['installed']==1 and event['actual_extended_Optimize']==2
        assert all(start['h_type']=='B' and start['h_value'] in [0.,1.] for start in starts)
        for j,proof in enumerate(pair['proofs']):
            assert proof['call'] in calls and sha(portable(proof['path']))==proof['model']
            beta=max(0.,math.nextafter(min(proof['bound'],proof['cutoff'])-1e-7,-math.inf))
            assert pair['beta'+str(j)]==beta
        for b in views['bindings']:
            if b['solve_kind']=='LP':continue
            model=model_cache[b['model_SHA']];native=rd(Path(str(portable(calls[b['call']]['native_log_path']))+'.round120.native.json'))
            assert native['model_SHA']==b['model_SHA'] and native['h_type']=='B' and native['h_BranchPriority']==0
            frac=lambda x:Fraction.from_float(float(x))
            assert frac(native['lower_base'])+frac(native['lower_delta'])<=frac(pair['m'])
            assert frac(native['upper_base'])>=frac(pair['m']) and frac(native['upper_base'])+frac(native['upper_delta'])>=frac(pair['b'])
            assert frac(native['objective_base'])+frac(native['objective_constant'])<=frac(pair['beta0'])
            assert frac(native['objective_base'])+frac(native['objective_delta'])+frac(native['objective_constant'])<=frac(pair['beta1'])
        events=[json.loads(s) for s in checked_bytes(d/'external/round120_events.jsonl').decode().splitlines()]
        assert not any(e['kind']=='revoked' for e in events)
        installed=[e for e in events if e['kind']=='root_formulation_installed'];paid=[e for e in events if e['kind']=='paid_root_LP_returned']
        assert len(installed)==1 and installed[0]['leaf']=='L0' and len(paid)==2
        assert all(e['process_seconds']<=installed[0]['process_seconds'] for e in paid)
    else:assert not event['enabled'] and event['installed']==0
    H=None
    if l['arm']!='P-GRB':H=h_review(p,a,d)
    return dict(arm=l['arm'],seed=l['seed'],PID=birth['pid'],producer_receipt_SHA=sha(d/'producer_receipt.json'),
        seal_SHA=sha(d/'producer_seal.json'),audit_SHA=sha(d/'audit.json'),T_produce=producer['T_produce'],T_verify=total['T_verify'],T_total=total['T_total'],
        U=endpoint['U'],L=endpoint['L'],signed_gap=endpoint['gap'],certificate=endpoint['certificate'],
        independent_physical_F=resultphysical['F'],calls=facts,Starts=starts,
        D1_installed=event.get('installed',0),D1_extended_Optimize=event.get('actual_extended_Optimize',0),
        legacy_formal_performance=endpoint['formal_performance'],validity_field='formal_protocol_qualified'),H

def check():
    tick=time.perf_counter();candidate,binding=contract.frozen_bindings();pre=rd(REVIEW/'pre_contract.json');gate=rd(REVIEW/'performance_admission.json')
    assert pre['decision']==gate['decision']=='ACCEPT' and gate['pre_contract_SHA']==sha(REVIEW/'pre_contract.json')
    assert pre['candidate_identity_SHA']==gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json')
    assert pre['helpers']==gate['helpers']==candidate['helpers'] and pre['source_bindings']==gate['source_bindings']==candidate['source_bindings']
    core=rd(OUT/'qualification/current_core.json');Hsaved=rd(OUT/'qualification/full_H_comparison.json')
    assert gate['qualification_core_SHA']==sha(OUT/'qualification/current_core.json') and core['actual_CLI']==5
    fees=[];controllers=set();native_births=set()
    for name in ['reference01','qualification01']:
        fee=rd(OUT/'fees'/name/'receipt.json');launch=rd(OUT/'fees'/name/'launch.json');controller=rd(OUT/'controller'/name/'launch.json')
        assert fee['exit_code']==fee['actual_exit_code']==0 and fee['actual_exit_observed'] and fee['uncertain_native_children']==0
        assert fee['wrapper_pid']==launch['wrapper_pid']==controller['pid']
        assert fee['outer_seconds_upper']>=fee['outer_seconds_lower'] and not fee['nested_native_seconds_added']
        controllers.add((controller['controller_pid'],controller['controller_actual_creation_unix']))
        fees.append(fee)
    assert sum(f['conservative_process_starts'] for f in fees)==8 and len(controllers)==2
    paid=sum(f['outer_seconds_upper'] for f in fees);assert paid<3000 and paid+80160<100000
    qualification_fee=fees[1];assert qualification_fee['actual_native_children']==5
    facts=[];hvalues={}
    for group in core['groups']:
        i=rd(OUT/group['plan']/'identity.json');assert i['helpers']==candidate['helpers'] and i['source_hashes']==candidate['source_bindings']
        assert not group['adjudication']['rejections']
        by={a['arm']:a for a in group['arms']}
        for l in i['launches']:
            fact,H=arm_review(l,i,by[l['arm']],qualification_fee['wrapper_pid']);facts.append(fact);native_births.add(fact['PID'])
            if H is not None:hvalues[(l['arm'],l['seed'])]=H
    assert len(facts)==len(native_births)==5 and {(f['arm'],f['seed']) for f in facts}=={('P-GRB',1),('ENS-C',1),('M-B',1),('MB-D1',1),('MB-D1',0)}
    baseline=hvalues['M-B',1]
    for key,value in hvalues.items():
        assert value[0]==baseline[0] and value[1]==baseline[1],('complete H mismatch',key)
    assert all(c['qualified'] for c in Hsaved['comparisons'])
    for arm in ['ENS-C','M-B','MB-D1']:
        assert Hsaved['arms'][arm]['semantic_traces']==hvalues[arm,1][0]
    argv=rd(OUT/'argv_freeze.json');formal_observed=[]
    for plan in argv['plans']:
        if not plan['name'].startswith('campaign/'):continue
        i=rd(OUT/plan['name']/'identity.json')
        for l in i['launches']:
            d=Path(l['destination'])
            if d.exists():formal_observed.append(dict(group=l['group_number'],arm=l['arm'],
                launch_record_exists=(d/'launch.json').exists(),actual_OS_birth_record_exists=(d/'child_process_origin.json').exists(),
                producer_receipt_exists=(d/'producer_receipt.json').exists()))
    formal_fees_observed=[p.name for p in (OUT/'fees').iterdir() if p.name.startswith('formal')]
    contract.frozen_bindings()
    assert all(sha(Path(path))==digest for path,digest in USED.items()),'reviewed evidence changed during closeout'
    value=dict(decision='ACCEPT',scope='Corroboration of sealed five-CLI qualification evidence after the independently pre-reviewed formal campaign began.',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='independent executor /root/contract_review',script_SHA=sha(__file__),
        candidate_identity_SHA=sha(OUT/'candidate_identity.json'),pre_contract_SHA=sha(REVIEW/'pre_contract.json'),performance_admission_SHA=sha(REVIEW/'performance_admission.json'),
        helper_binding_unchanged=True,source_binding_unchanged=True,helper_files=len(candidate['helpers']),source_files=len(candidate['source_bindings']),
        qualification_core_SHA=sha(OUT/'qualification/current_core.json'),full_H_comparison_SHA=sha(OUT/'qualification/full_H_comparison.json'),
        five_actual_CLI=facts,full_H_independently_replayed=True,full_H_trace_SHA=canonical(baseline[0]),
        H_seed_ids=list(range(1,26)),H_Seed0_equal_to_Seed1=True,
        outer_seconds=paid,fee_level_starts=8,additional_distinct_controllers=len(controllers),all_observed_launches=10,
        uncertain_qualification_children=0,failed_qualification_native_producers=0,
        concurrent_formal_positions_observed=formal_observed,concurrent_formal_fees_observed=formal_fees_observed,
        formal_full_design_positions=32,formal_full_design_obligation_seconds=80160,only_closed_qualification_fees_summed_here=True,
        sequence='Independent pre_contract ACCEPT preceded qualification and formal. All five CLI and qualification01 fee closed before formal01. This corroborating review completed after formal01 started; it is not a new admission prerequisite.',
        verified_necessary_evidence_files=len(USED),necessary_evidence_unchanged_during_review=True,
        no_native_launches_or_solver_Optimize=True,no_measured_helpers_or_raw_modified=True,
        signed_gap_policy='Original signed gaps retained, including ENS-C tiny negative gap within 1e-7.',
        legacy_field_policy='formal_performance is preserved legacy R108 metadata; qualification validity is formal_protocol_qualified. H100 is not current formal performance evidence.',
        limitations=['This closeout checks actual five known-fixture producers and necessary scope/Start/type/physical/clock evidence; it does not replace the required post-formal 32-arm/48-pair review or public restore.'],
        seconds=time.perf_counter()-tick)
    save_receipt('independent_qualification_closeout.json',value)
    lines=['# Independent Round122 qualification closeout','', '**Decision: ACCEPT.** All five prescribed known-fixture CLI qualifications are complete. This corroborating review completed after the already pre-reviewed formal campaign began.','',
        'Pre-contract, candidate, measured helpers, production sources and performance-admission hashes agree. Seals, actual OS child births, successful returns, five physical fleets, every saved call model and scope, Seed0/1 settings, call-scoped native log segments, integer/continuous quantity declarations, frozen A/B and all submitted Start vectors were checked from raw evidence. Start rows, bounds, integrality, objectives and readback were independently recomputed. D1 installed once at the original root in both Seeds and made two extended Optimize calls; actual binary h, zero BranchPriority, conservative beta/ObjCon endpoints and paid root-proof ordering were checked.','',
        'Complete 24+1 H and closure/exchange traces were independently replayed across ENS-C, M-B and D1, including D1 Seed0. All five producer/verify/total clocks satisfy the original policy. Signed tiny gaps remain unchanged. The legacy formal_performance field is retained; formal_protocol_qualified is the validity field.','',
        f'The two closed qualification fees total {paid:.7f} outer seconds: 8 fee-level starts plus 2 distinct observed controllers, with no uncertain qualification children or failed native producers. Together with the full 80160-second formal design they fit the 100000-second total limit. Active formal time is not represented as a closed fee in this qualification-only sum.','',
        'The original independent pre_contract ACCEPT is the pre-formal contract review. All five CLI and the qualification fee closed before the parent intentionally started formal01. This additional corroboration is not a new admission prerequisite. Observed concurrent formal launch metadata is preserved in the JSON; no healthy solver was stopped or changed.','',
        'No native process, Optimize, measured-helper change or raw write occurred during this review. Complete formal execution, independent post-formal review, public recovery and safe cleanup remain required.','']
    with (REVIEW/'independent_qualification_closeout.md').open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))

if __name__=='__main__':check()
