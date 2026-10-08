"""Independent R108 raw bridge audit; Python stdlib only, zero solver.

Reuses this reviewer's previously audited input/physics/strict LP parser, not
the campaign reader's endpoint, cover, certificate or decision routines.
Only review/ files are written. Native logs are evidence, never instructions.
"""
from pathlib import Path
from collections import Counter
import argparse, ast, hashlib, json, math, re, runpy, sys, time, traceback

arguments=argparse.ArgumentParser()
arguments.add_argument('--root',required=True)
arguments.add_argument('--out')
arguments.add_argument('--dll',help='Optional explicit current installed DLL bytes to rehash; never loaded')
args=arguments.parse_args()
ROOT=Path(args.root).resolve()
OUT=ROOT/'results/unified_exact_round108'
REVIEW=OUT/'review'
DEST=Path(args.out).resolve() if args.out else REVIEW/'bridge_raw_audit01'
assert DEST.is_relative_to(REVIEW),'all independent writes must remain in this root review/'
OWN_PARSER=REVIEW/'current_qualification_audit01.py'
base=runpy.run_path(str(OWN_PARSER))
reads=base['reads'];count=0;milestones=[]
def require(b,message):
    global count
    count+=1
    if not b:raise AssertionError(message)
for fn in ['input_file','physical','lp','matrix','qualification','argv_map']:
    base[fn].__globals__['require']=require
    base[fn].__globals__.update(ROOT=ROOT,OUT=OUT,REVIEW=REVIEW,DEST=DEST)
data=base['data'];sha=base['sha'];txt=base['txt'];obj=base['obj'];rows=base['rows']
near=base['near'];lp=base['lp'];input_file=base['input_file'];physical=base['physical'];argv_map=base['argv_map']
TOL=1e-7;ZERO=1e-12
PE=ROOT/'build/research/round108-frozen-mb-v1/ExactEBRP.exe'
DLL=Path(args.dll).resolve() if args.dll else None
frozen_DLL_SHA=None
def native_dll_sha():return sha(DLL) if DLL is not None else frozen_DLL_SHA
cache={}
def under_root(value):
    """Translate saved absolute evidence paths to this explicit root, no fallback."""
    s=str(value).replace('\\','/')
    for marker in ['results/','reference/','build/','scripts/','src/','include/','tests/']:
        if marker in s:return ROOT/s[s.index(marker):]
    p=Path(s)
    require(not p.is_absolute(),'unsupported absolute evidence path')
    return ROOT/p
def model(p):
    digest=sha(p)
    if digest not in cache:cache[digest]=lp(p)
    return cache[digest]
def save(p,value):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def full_physics(q,routes,p):
    routes=[dict(r) for r in routes];cars=[r['vehicle'] for r in routes]
    require(len(set(cars))==len(cars),'unique represented vehicles')
    for k in range(q['M']):
        if k not in cars:routes.append(dict(vehicle=k,nodes=[0,0],operations=[]))
    ph=physical(q,routes,p['T_seconds'],p['lambda'],p['pickup_seconds'],p['drop_seconds'])
    ph.update(full_routes=routes,empty_vehicles_added=q['M']-len(cars))
    require(sum(ph['final_inventories'][1:])==sum(q['initial'][1:])-sum(x['return_load'] for x in ph['routes']),'fleet inventory minus depot return conservation')
    return ph

def domain_contract(m,q,arm):
    t=m['types'];quant=[n for n in t if n.startswith(('p_','d_'))]
    require(len(quant)==2*q['V']*q['M'],'complete quantity column domain')
    require(all(t[n]==('C' if arm=='M-B' else 'I') for n in quant),'original p/d native domain '+arm)
    require(all(t[n] in ['I','B'] for n in t if n.startswith(('x_','load_','Y_'))),'integer original route/load/inventory domain')
    require(all(t[n]=='B' for n in t if n.startswith(('mode_','z_')) or re.fullmatch(r'state_\d+_\d+',n)),'original binary state/direction/visit domain')
    require(sum(n.startswith('mode_') for n in t)==q['V']*q['M'],'all original direction binaries retained')
    expected=[]
    if arm=='M-B':
        for i in range(1,q['V']+1):
            a={f'{v}_{k}_{i}':1. for k in range(q['M']) for v in ['p','d']}
            selectors=[n for n in t if re.fullmatch(f'state_{i}_'+r'\d+',n)]
            require(bool(selectors),'existing admissible state selectors '+str(i))
            for n in selectors:
                motion=abs(q['initial'][i]-int(n.rsplit('_',1)[1]))
                if motion:a[n]=-float(motion)
            b={f'z_{k}_{i}':1. for k in range(q['M'])}
            initial=f"state_{i}_{q['initial'][i]}"
            if initial in t:b[initial]=1.
            expected.extend([('=',0.,tuple(sorted(a.items()))),('=',1.,tuple(sorted(b.items())))])
        require(not Counter(expected)-Counter(m['rows']),'all frozen A/B coefficient equations present')
    return dict(columns=len(t),rows=len(m['rows']),native_types=dict(Counter(t.values())),quantity_columns=len(quant),AB_exact_rows=len(expected))

def scope_contract(c,m,q):
    if c['full_original']:
        require(c['native_preconditions']==1,'full original model uses integer native call');return
    lo,hi,cut=c['lower_g'],c['upper_g'],c['cutoff']
    require(c['gmax']==(q['V']-1)/q['V'] and 0<=lo<=hi<=c['gmax']+TOL,'actual physical gmax and scope')
    require(m['bounds']['G']==(lo,hi),'saved native G domain equals journal scope')
    rr=Counter(m['rows'])
    require(rr[('<',cut,tuple(sorted(m['objective'].items())))]>=1,'actual objective cutoff row equals journal cutoff')
    for g,sense in [(lo,'>'),(hi,'<')]:
        terms={f'h_{i}_{j}':1. for i in range(1,q['V']+1) for j in range(i+1,q['V']+1)}
        if g:
            for i in range(1,q['V']+1):terms[f'r_{i}']=-q['V']*g
        require(rr[(sense,0.,tuple(sorted(terms.items())))]>=1,'actual shared true-G cap/floor row equals scope')

def supported(lo,hi,proofs):
    """Unconditional bound on a true-G interval; no epigraph-scope extension."""
    require(0<=lo<=hi,'valid requested proof interval')
    points=sorted({lo,hi,*[x for p in proofs for x in [p['lo'],p['hi']] if lo<x<hi]})
    segments=list(zip(points,points[1:])) or [(lo,hi)]
    return min(max([left]+[min(p['L'],p['cutoff']) for p in proofs if p['lo']<=left+1e-12 and p['hi']+1e-12>=right]) for left,right in segments)

def cover_check(c,value,proofs,witnesses):
    if c['full_original']:
        require(value<=min((w['U'] for w in witnesses),default=math.inf)+TOL,'plain full-model native bound does not contradict available physical U');return value
    pieces=[dict(x) for x in c['cover']];cutoff=c['cutoff'];matched=0
    for x in pieces:
        if value is not None and (x['id'],x['lower_g'],x['upper_g'],x['cutoff'])==(c['leaf'],c['lower_g'],c['upper_g'],cutoff):
            x['lower']=max(x['lower'],value);matched+=1
        require(math.isfinite(x['lower']) and x['cutoff']+TOL>=cutoff,'finite same-or-weaker coverage cutoff')
        bound=supported(x['lower_g'],x['upper_g'],proofs)
        require(min(x['lower'],x['cutoff'])<=bound+TOL,'chronologically supported actual saved cover piece')
        for w in witnesses:
            if x['lower_g']-TOL<=w['G']<=x['upper_g']+TOL and w['U']<=x['cutoff']+TOL:
                require(x['lower']<=w['U']+TOL,'cover piece bound consistent with own physical witnesses')
    if value is not None:require(matched==1,'current native bound updates exactly one matching active cover piece')
    covered=0.
    for x in sorted(pieces,key=lambda x:x['lower_g']):
        require(0<=x['lower_g']<=covered+1e-12 and x['lower_g']<=x['upper_g'],'saved full cover has no hole');covered=max(covered,x['upper_g'])
    require(pieces and covered+1e-12>=min(cutoff,c['gmax']),'saved full cover covers every possible improving true G')
    require(cutoff+TOL>=min(w['U'] for w in witnesses),'same-run cutoff has own physical witness')
    return min([cutoff]+[min(x['lower'],x['cutoff']) for x in pieces])

def start_check(d,sp,m,q,p):
    meta=obj(sp);csvp=sp.with_name(sp.name.replace('.json','.values.csv'));rr=rows(csvp)
    vals={r['variable']:float(r['value']) for r in rr}
    require(meta['submitted'] and meta['mapping_complete'] and meta['readback_valid'],'complete actually submitted native Start')
    require(meta['model_sha256']==sha(next(under_root(c['model_path']) for c in start_check.calls if c['model_sha256']==meta['model_sha256'])),'Start exact measured model SHA')
    require(set(vals)==set(m['bounds']) and len(vals)==len(rr),'Start has every original model column exactly once')
    for r in rr:
        n=r['variable'];v=vals[n];low,high=m['bounds'][n]
        require(r['type']==m['types'][n] and math.isfinite(v) and near(v,float(r['readback']),1e-12),'actual native Start type/value readback')
        require(low-1e-6<=v<=high+1e-6 and (r['type']=='C' or abs(v-round(v))<=1e-5),'Start finite native bound/domain')
    violations=[]
    for sense,rhs,terms in m['rows']:
        lhs=sum(vals[n]*a for n,a in terms)
        violations.append(abs(lhs-rhs) if sense=='=' else max(0,lhs-rhs) if sense=='<' else max(0,rhs-lhs))
    require(max(violations,default=0)<=1e-6,'all actual Start numeric original rows hold')
    w=obj(d/'external'/(meta['source']+'_witness.json'));ph=full_physics(q,w['routes'],p)
    require(near(ph['U'],w['objective']) and near(ph['U'],meta['objective']) and near(ph['U'],sum(vals[n]*a for n,a in m['objective'].items())),'Start physical/objective agreement')
    operations={(r['vehicle'],o['station']):(o['pickup'],o['drop']) for r in w['routes'] for o in r['operations']}
    for k in range(q['M']):
        for i in range(1,q['V']+1):
            pu,dr=operations.get((k,i),(0,0))
            require(near(vals[f'p_{k}_{i}'],pu,1e-5) and near(vals[f'd_{k}_{i}'],dr,1e-5),'complete visited and unvisited native quantities')
    return dict(metadata_path=str(sp.relative_to(ROOT)),metadata_SHA=sha(sp),values_SHA=sha(csvp),model_SHA=meta['model_sha256'],columns=len(vals),rows_checked=len(violations),max_row_violation=max(violations,default=0),own_physical_U=ph['U'],native_types=dict(Counter(r['type'] for r in rr)))

def audit_arm(launch,identity,formal):
    d=under_root(launch['destination']);p=launch['panel'];arm=launch['arm'];label=p['id']+' '+arm
    actual=obj(d/'launch.json');raw=obj(d/'result.json');comp=obj(d/'completion.json');audit=obj(d/'audit.json')
    require(actual['command']==launch['command'] and actual['panel']==p and actual['prereg_sha256']==identity['prereg_sha256'],'actual frozen complete launch identity '+label)
    require(comp['returncode']==0 and comp['stop_reason']=='normal_return' and comp['within_cap'] and audit['passed'],'normal closed functional execution '+label)
    require(audit['binary_sha256']==sha(PE),'postexit actual production binary SHA '+label)
    require(raw['algorithm_preset']=={'P-GRB':'custom','ENS-C':'research-round83-vds-equal-net-exchange','M-B':'research-round99-ensc-discrete-structure-m-binary'}[arm],'actual effective parser/preset identity '+label)
    q=input_file(ROOT/p['input_path']);require(sha(ROOT/p['input_path'])==p['input_sha256'] and (q['V'],q['M'],q['Q'])==(p['V'],p['M'],p['Q_vector']),'actual frozen input bytes/header '+label)
    ph=full_physics(q,raw['routes'],p);require(near(ph['U'],raw['upper_bound']) and near(ph['U'],raw['objective']) and ph['final_inventories']==raw['final_inventories'],'own final physical fleet objective and station inventory '+label)
    timing=obj(d/'whole_arm_receipt.json') if formal else None
    complete=timing['complete_seconds'] if formal else comp['fully_observed_end_to_end_seconds']
    offset=complete-comp['fully_observed_end_to_end_seconds'] if formal else 0.
    require(0<=offset+1e-9 and complete<=launch['cap_seconds'],'complete arm within original cap '+label)
    if formal:
        require(timing['completion_SHA']==sha(d/'completion.json') and timing['audit_SHA']==sha(d/'audit.json'),'complete timing binds actual termination/audit '+label)
        require(timing['includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck'] and not timing['native_time_added'],'all arm work included exactly once '+label)
    observations=obj(d/'observations.json');calls={};returns={};notstarted=set();witnesses=[];bound_events=[];timeline=[]
    for seq,o in enumerate(observations,1):
        e=o['payload'];require(e['sequence']==o['sequence']==seq,'contiguous journal sequence '+label)
        f=d/'journal'/f'event_{seq}.json';bb=data(f);co=txt(f.with_suffix('.commit')).split()
        require(hashlib.sha256(bb).hexdigest()==o['sha256']==co[4] and json.loads(bb)==e and co[0]=='NEJ1' and int(co[1])==seq and int(co[3])==len(bb),'raw journal atomic committed exact bytes '+label)
        require(near(float(co[2]),o['data_close_seconds'],1e-9) and near(o['effective_available_seconds'],max(o['data_close_seconds'],o['first_observed_seconds']),1e-9),'actual read availability timestamps '+label)
        if e['kind']=='identity':
            require(seq==1 and e['input_sha256']==p['input_sha256'] and (e['V'],e['M'],e['T'],e['lambda'],e['pickup_seconds'],e['drop_seconds'])==(p['V'],p['M'],p['T_seconds'],p['lambda'],p['pickup_seconds'],p['drop_seconds']),'actual native identity settings '+label)
        elif e['kind']=='call':
            require(e['call'] not in calls and e['settings']==dict(read_return_code=0,**base['SETTINGS']),'every actual native call unchanged numerical parameters '+label)
            require(sha(under_root(e['model_path']))==e['model_sha256'],'every actual native call saved model bytes '+label);calls[e['call']]=e
        elif e['kind']=='returned':
            require(e['call'] in calls and e['call'] not in returns and e['return_code']==0,'successful actual native call return '+label);returns[e['call']]=seq
        elif e['kind']=='not_started':
            require(not e['actual_Optimize'],'deadline skip had no native Optimize');notstarted.add(e['call'])
        elif e['kind']=='witness':
            w=full_physics(q,e['routes'],p);require(near(w['U'],e['objective']) and near(w['G'],e['G']) and near(w['P'],e['P']),'every own committed physical witness '+label)
            require(e['call']==0 or e['call'] in calls and e['call'] not in returns,'witness belongs to live same-arm call '+label)
            w.update(sequence=seq,source=e['source'],improving=e['improving'],raw_available=o['effective_available_seconds'],safe_complete_arm_available=o['effective_available_seconds']+max(0.,offset));witnesses.append(w)
        elif e['kind']=='bound':require(e['call'] in calls and e['call'] not in returns and not e['inconsistent'],'actual bound belongs to live noncontradictory same-arm call '+label);bound_events.append(e)
        elif e['kind']=='witness_rejected':pass
        else:raise AssertionError(('unexpected native event',label,e))
    require(set(calls)==set(returns)|notstarted and not set(returns)&notstarted,'every declared native call returned or genuinely skipped '+label)
    require(witnesses and near(min(w['U'] for w in witnesses),ph['U']),'final physical U from same-arm committed witnesses '+label)
    # Parse every saved model, even speculative/uncommitted child scopes.
    paths=[d/'compact.lp'] if arm=='P-GRB' else sorted((d/'external/models').glob('*.lp'))
    models={};contracts=[]
    for path in paths:
        m=model(path);digest=sha(path);models[digest]=m
        contracts.append(dict(path=str(path.relative_to(ROOT)),SHA=digest,**domain_contract(m,q,arm)))
    for c in calls.values():require(c['model_sha256'] in models,'every native call bound to saved model contract');scope_contract(c,models[c['model_sha256']],q)
    ledger=rows(d/'external/paper_optimize_ledger.csv') if arm!='P-GRB' else []
    lpstatus=rows(d/'external/lp_status_ledger.csv') if arm!='P-GRB' else []
    if ledger:require(len(ledger)==len(returns),'one actual native ledger per successful native call')
    returned_proofs={};native_records=[];lp_index=0
    for (callid,c),r in zip(calls.items(),ledger or [dict(model_sha256=sha(d/'compact.lp'),leaf_id='',solve_kind='MIP',native_status=raw['native_mip_status_text'],optimize_return_code=raw['native_mipopt_return_code'],native_log=str(d/'native.log'))]):
        require(callid in returns and int(r['optimize_return_code'])==0 and r['model_sha256']==c['model_sha256'],'actual native ledger matches call/model/return '+label)
        if ledger:require(r['leaf_id']==c['leaf'] and Path(r['native_log'])==Path(c['native_log_path']),'actual native ledger log/leaf identity '+label)
        m=models[c['model_sha256']];native_log=under_root(r['native_log']);nt=txt(native_log);size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',nt)
        require(size and (int(size[1]),int(size[2]))==(len(m['rows']),len(m['bounds'])),'actual native original model size before presolve '+label)
        native_types=None;proofvalue=None
        if r['solve_kind']=='LP':
            require(not c['native_preconditions'],'LP carries relaxation identity, not integer bound identity')
            s=lpstatus[lp_index];lp_index+=1
            require(s['leaf_id']==r['leaf_id'] and s['native_status']==r['native_status'] and float(s['gamma_L'])==c['lower_g'] and float(s['gamma_U'])==c['upper_g'],'actual LP status/leaf/range linked to returned call')
            if int(s['terminal_valid']) and int(s['optimal']) and int(s['bound_available']):
                printed=re.findall(r'Optimal objective\s+([-+0-9.eE]+)',nt);proofvalue=float(s['lower_bound'])
                require(r['native_status']=='OPTIMAL' and printed and near(float(printed[-1]),proofvalue),'actual returned native LP numeric objective bound')
            elif int(s['terminal_valid']) and int(s['infeasible']):
                require(r['native_status']=='INFEASIBLE' and 'Infeasible model' in nt,'actual complete LP infeasibility terminal native log');proofvalue=c['cutoff']
        else:
            require(c['native_preconditions']==1,'actual restored integer-domain native bound call')
            match=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',nt);ct=Counter(m['types'].values())
            native_types={'C':int(match[1]),'I':int(match[2])-int(match[3]),'B':int(match[3])} if match else None
            require(native_types=={k:ct.get(k,0) for k in ['C','I','B']},'actual native pre-presolve VType restored exactly to saved model')
            printed=re.findall(r'Best objective ([^,]+), best bound ([^,]+), gap ([^\n]+)',nt)
            require(bool(printed),'actual successful native MIP final bound log')
            proofvalue=float(printed[-1][1]);require(math.isfinite(proofvalue) and abs(proofvalue)<1e90,'finite actual returned native bound')
            if r['native_status']=='OPTIMAL':require('Optimal solution found (tolerance 0.00e+00)' in nt,'actual zero requested native MIP optimum')
            elif r['native_status']=='TIME_LIMIT':require('Time limit reached' in nt,'actual normal native time limit')
            elif r['native_status']=='INTERRUPTED':require('Solve interrupted' in nt,'actual original child target interruption')
            else:raise AssertionError(('unqualified native status',r))
        if proofvalue is not None and not c['full_original']:
            require(c['cutoff']+TOL>=ph['U'],'proof cutoff qualified by same-arm final physical U')
            returned_proofs[callid]=dict(lo=c['lower_g'],hi=c['upper_g'],L=proofvalue,cutoff=c['cutoff'],sequence=returns[callid],call=callid,source='actual_returned_native_LP' if r['solve_kind']=='LP' else 'actual_returned_integer_native_final_log')
        native_records.append(dict(call=callid,model_SHA=c['model_sha256'],model_path=c['model_path'],native_log_path=r['native_log'],actual_read_native_log=str(native_log.relative_to(ROOT)),native_log_SHA=sha(native_log),native_status=r['native_status'],solve_kind=r['solve_kind'],return_sequence=returns[callid],native_types=native_types,returned_native_log_L=proofvalue))
    require(lp_index==len(lpstatus),'all complete LP status rows independently linked')
    # Chronological proof accumulation: final native log only exists after return.
    prior=[];seenw=[];chronology=[];bestplain=0.;maxjournal=0.
    for o in observations:
        e=o['payload'];seq=e['sequence'];kind=e['kind']
        if kind=='witness':seenw.append(next(w for w in witnesses if w['sequence']==seq))
        if kind=='returned' and e['call'] in returned_proofs:prior.append(returned_proofs[e['call']])
        if kind=='call' and not e['full_original']:
            cover_check(e,None,prior,seenw)
            chronology.append(dict(sequence=seq,kind=kind,call=e['call'],prior_proof_count=len(prior),maximum_prior_sequence=max((x['sequence'] for x in prior),default=0)))
        if kind=='bound':
            c=calls[e['call']]
            require(c['native_preconditions']==1,'callbacks bound only restored original integer model')
            if not c['full_original']:prior.append(dict(lo=c['lower_g'],hi=c['upper_g'],L=e['native_bound'],cutoff=c['cutoff'],sequence=seq,call=e['call'],source='actual_same_arm_committed_integer_native_callback'))
            if e['global_available']:
                L=cover_check(c,e['native_bound'],prior,seenw)
                require(near(L,e['global_bound'],1e-10),'independently recomputed actual native full-cover global callback bound')
                maxjournal=max(maxjournal,L)
                if c['full_original']:bestplain=max(bestplain,L)
                chronology.append(dict(sequence=seq,kind=kind,call=e['call'],global_L=L,maximum_prior_sequence=max((x['sequence'] for x in prior),default=0)))
            else:require(e['global_bound'] is None,'unavailable global callback bound not used')
        require(all(x['sequence']<=seq for x in prior),'never use future proof in chronological cover')
        if seenw:
            U=min(w['U'] for w in seenw)
            require(maxjournal<=U+TOL,'all chronological global bounds consistent with own physical U')
            timeline.append(dict(sequence=seq,kind=kind,raw_supervisor_available=o['effective_available_seconds'],safe_complete_arm_available=o['effective_available_seconds']+max(0.,offset),own_U=U,committed_global_L=maxjournal,signed_gap=U-maxjournal))
    start_check.calls=list(calls.values());starts=[];cover=None
    if arm=='P-GRB':
        require(len(calls)==len(returns)==1 and next(iter(calls.values()))['full_original'],'P one complete original cold compact MIP')
        require(raw['gurobi_hga_start_requested'] is False and raw['gurobi_native_domain_audit_passed'] is True and 'Loaded user MIP start' not in txt(d/'native.log'),'actual P cold, original native domain audit')
        ref=d.parent.parent/'reference'/p['id']/'original.lp'
        require(sha(ref)==sha(d/'compact.lp')==p['reference']['canonical_sha256'],'current P model byte-identical own current reference')
        for key,field in [('fingerprint','gurobi_model_fingerprint'),('columns','gurobi_num_vars'),('rows','gurobi_num_constrs')]:require(raw[field]==p['reference'][key],'P original native reference '+key)
        require(raw['native_mip_lifecycle_valid'] and raw['native_mip_solver_finalization_reached'] and raw['native_mip_problem_freed'] and raw['native_mip_environment_closed'] and raw['native_mip_mipopt_count']==1,'actual P native model/environment finalized')
        require(raw['native_mip_best_bound_available'] and near(raw['native_mip_best_bound'],raw['lower_bound']) and near(bestplain,raw['lower_bound']) and near(native_records[0]['returned_native_log_L'],raw['lower_bound']),'P exact final attribute/journal/log original bound linkage')
        L=raw['native_mip_best_bound'];cert=raw['native_mip_status_text']=='OPTIMAL' and ph['U']-L<=TOL
    else:
        initial=obj(d/'external/initial_witness.json');initialph=full_physics(q,initial['routes'],p)
        require(near(initialph['U'],initial['objective']),'actual original same-run startup physical U0')
        leaves=rows(d/'external/paper_leaf_ledger.csv');live=[x for x in leaves if x['status'] not in ['replaced','coalesced']]
        # These measured arms retain one genuine active parent, with speculative child LPs.
        require(len(live)==1 and live[0]['leaf_id']=='L0' and live[0]['parent_id']=='' and float(live[0]['gamma_L'])==0 and near(float(live[0]['gamma_U']),min(initialph['U'],(q['V']-1)/q['V']),1e-12),'actual root interval covers all potentially improving physical solutions')
        leaf=live[0];L=float(leaf['lower_bound']);lo=float(leaf['gamma_L']);hi=float(leaf['gamma_U'])
        lower=supported(lo,hi,prior)
        require(min(L,ph['U'])<=lower+TOL,'independent full-domain partition proves conditional raw final leaf bound')
        relevant=[x for x in live if float(x['gamma_L'])<ph['U']-TOL]
        L=min((float(x['lower_bound']) for x in relevant),default=0.)
        traces=rows(d/'external/global_bound_trace.csv');previous=-math.inf;previousU=math.inf
        for t in traces:
            upper=float(t['verified_global_upper_bound']);parts=[float(t[k]) for k in ['active_leaf_valid_lower_bound','other_open_leaf_min_valid_lower_bound'] if t[k]!='']
            reported=float(t['valid_global_lower_bound'])
            require(near(reported,min([upper]+parts)) and reported+TOL>=previous and upper<=previousU+TOL and reported<=upper+TOL,'raw complete scheduler trace aggregation and monotonicity')
            previous=reported;previousU=upper
        require(traces and near(previous,min(L,previousU)) and near(L,raw['lower_bound']),'original final published raw leaf L linked trace/result')
        closed=all(x['status'] in ['closed','fathomed','empty'] for x in relevant)
        if closed:require(leaf['closure_source']=='native_terminal_mip_optimal' and any(r['solve_kind']=='MIP' and r['native_status']=='OPTIMAL' for r in native_records),'complete closed cover actual terminal proof')
        reason=raw['external_gini_tree_failure_reason']
        require(reason=='none' or reason=='overall_global_deadline' and raw['status'] in ['time_limit','round31_c6_external_gini_tree_time_limit'],'only inherited legal overall time-window termination')
        for flag in ['root_coverage_valid','parent_child_coverage_valid','all_leaf_bounds_valid','leaf_bounds_monotone','global_bound_monotone','lifecycle_complete','feasibility_consistency_gate']:require(raw['external_gini_tree_'+flag] is True,'original complete native/tree lifecycle corroboration '+flag)
        cert=closed and ph['U']-L<=TOL
        require(leaf['lower_bound_sources']=='objective_nonnegative_penalty_G_floor;optimal_complete_lp_relaxation;valid_child_target_native_bound;native_terminal_mip_bound','exact inherited root bound sources')
        for sp in sorted((d/'external/native_logs').glob('*.round68.start.json')):
            meta=obj(sp)
            if meta.get('submitted'):starts.append(start_check(d,sp,models[meta['model_sha256']],q,p))
        require(len(starts)==2,'both original target and terminal Starts completely checked')
        cover=dict(root_gamma=[lo,hi],same_arm_startup_physical_U=initialph['U'],physical_gmax=(q['V']-1)/q['V'],raw_published_final_L=L,unconditional_whole_root_supported_L=lower,conditional_min_raw_L_own_U=min(L,ph['U']),live_leaves=live,whole_improving_domain_covered=True,all_relevant_closed=closed,open_relevant_leaves=0 if closed else len(relevant),proofs=prior,native_final_proofs=list(returned_proofs.values()),global_trace_rows=len(traces),raw_final_trace=traces[-1],genuine_active_leaf_split=False)
    require(math.isfinite(L) and L<=ph['U']+TOL,'finite independently qualified noncontradictory endpoint L')
    require(cert==raw['strict_certified_original_problem'],'own complete certificate agrees with serialized flag only after proof')
    gap=ph['U']-L
    require(gap>TOL or cert,'numerical closure cannot silently bypass certificate obligations')
    improved=[];best=math.inf
    for w in witnesses:
        if w['U']<best:
            improved.append(w);best=w['U']
    result=dict(id=p['id'],arm=arm,U=ph['U'],L=L,gap=gap,relative_gap=gap/abs(ph['U']) if abs(ph['U'])>ZERO else None,
        numbers_qualified=True,certificate_qualified=True,certificate=cert,complete_seconds=complete,PE_SHA=sha(PE),DLL_SHA=native_dll_sha(),
        complete_receipt=timing,normal_completion=comp,raw_status=raw['status'],raw_tree_termination_reason=raw.get('external_gini_tree_failure_reason'),
        physical=ph,new_physical_UBs=improved,total_physical_witnesses=len(witnesses),native_records=native_records,model_contracts=contracts,
        starts=starts,cover=cover,journal_event_count=len(observations),chronological_native_cover_events=len(chronology),
        chronological_cover_max_support_sequence_le_event=True,all_journal_commits_exact=True,availability_offset_seconds=max(0.,offset),
        availability_offset_is_upper_bound_unknown_prelaunch=True,availability_exact_first_discovery=False,
        bindings={n:sha(d/n) for n in ['launch.json','result.json','completion.json','audit.json','observations.json','native.log']},actual_full_argv=actual['command'])
    save(DEST/(p['id']+'_'+arm.replace('-','_')+'_timeline.json'),timeline)
    save(DEST/(p['id']+'_'+arm.replace('-','_')+'_cover_chronology.json'),chronology)
    milestones.append(label);print(json.dumps(dict(completed=label,U=ph['U'],L=L,gap=gap,certificate=cert,complete_seconds=complete,events=len(observations))),flush=True)
    return result,models,q

def own_pair(c,p):
    require(c['certificate_qualified'] and p['certificate_qualified'],'independently resolved both certificate scopes')
    u=p['U']-c['U'];g=p['gap']-c['gap'];au=max(.001,.01*abs(p['U']));ag=max(.001,.10*abs(p['gap']))
    if c['certificate']!=p['certificate']:
        classification='WIN' if c['certificate'] else 'LOSS';severe=p['certificate'];basis='one_complete_certificate'
    elif c['certificate']:
        dt=p['complete_seconds']-c['complete_seconds'];at=max(30,.1*p['complete_seconds'])
        classification='WIN' if dt>=at else 'LOSS' if -dt>=at else 'TIE';severe=c['complete_seconds']>=2*p['complete_seconds'] and -dt>=120;basis='both_certified_complete_arm_time'
    else:
        good=u>=au or g>=ag;bad=-u>=au or -g>=ag
        classification='MIXED' if good and bad else 'WIN' if good else 'LOSS' if bad else 'TIE';severe=-u>=max(.001,.05*abs(p['U'])) and -g>=max(.005,.25*abs(p['gap']));basis='both_uncertified_absolute_materiality'
    percentage=p['gap']>TOL and c['gap']>=0
    return dict(id=c['id'],candidate=c['arm'],control=p['arm'],classification=classification,severe_regression=bool(severe),basis=basis,
        UB_improvement=u,gap_improvement=g,LB_change=c['L']-p['L'],a_U=au,a_gap=ag,
        time_improvement=p['complete_seconds']-c['complete_seconds'],a_t=max(30,.1*p['complete_seconds']),
        UB_ratio=c['U']/p['U'] if abs(p['U'])>ZERO else None,gap_ratio=c['gap']/p['gap'] if percentage else None,
        percentage_gap_path_applicable=percentage,candidate_signed_gap=c['gap'],control_signed_gap=p['gap'])

def decisions(arms):
    dd={(a['id'],a['arm']):a for a in arms};pairs=[];gates={}
    for role in ['F2','C2']:
        c=dd[role,'M-B'];p=dd[role,'P-GRB'];e=dd[role,'ENS-C'];cp=own_pair(c,p);pairs.extend([cp,own_pair(c,e)])
        percentage=p['gap']>TOL and c['gap']>=0
        bothopen=not c['certificate'] and not p['certificate']
        if role=='F2':passed=(c['certificate'] or bothopen and percentage and c['U']<=1.01*p['U'] and c['gap']<=1.05*p['gap']) and not cp['severe_regression']
        else:passed=c['certificate'] and not p['certificate'] or c['certificate'] and p['certificate'] and p['complete_seconds']-c['complete_seconds']>=30 and c['complete_seconds']<=.9*p['complete_seconds'] or bothopen and percentage and c['U']<=.99*p['U'] and c['gap']<=.8*p['gap']
        gates[role]=dict(passed=bool(passed),percentage_path_applicable=percentage,primary_pair=cp)
    # Cross-check only after own decisions: isolated pure source, no project import.
    source=txt(ROOT/'scripts/round108_decisions.py');tree=ast.parse(source);namespace={}
    exec(compile(tree,str(ROOT/'scripts/round108_decisions.py'),'exec'),namespace)
    theirgate=namespace['bridge'](arms)
    require(theirgate['bridge_pass']==all(g['passed'] for g in gates.values()),'frozen corrected decision gate agrees with independent arithmetic')
    for pair in pairs:
        q=namespace['pair'](dd[pair['id'],'M-B'],dd[pair['id'],pair['control']])
        require(q['classification']==pair['classification'] and q['severe_regression']==pair['severe_regression'] and q['gap_ratio']==pair['gap_ratio'],'frozen corrected decision pair agrees with independent signed arithmetic')
    return dict(bridge_pass=all(g['passed'] for g in gates.values()),gates=gates,pairs=pairs,
        no_hidden_ENS_dominance_gate=True,resource_admission_only=True,uniform_selection_not_yet_qualified=True,
        future_roles_required=['S12','B24','L48','F5','N36'],current_positive_selection_unreachable=namespace['early_impossible'](arms))

def bindings():
    global frozen_DLL_SHA
    c=obj(OUT/'candidate_identity.json');identity=obj(OUT/'bridge01/identity.json');qual=obj(OUT/'qualification/identity.json');con=obj(OUT/'confirmation01/identity.json')
    frozen_DLL_SHA=c['DLL_SHA']
    require(c['production_PE_SHA']==identity['candidate_binary_sha256']==qual['production_PE_SHA']==sha(PE),'same current frozen candidate/bridge/qualified production PE')
    require(c['DLL_SHA']==identity['dll_sha256']==qual['DLL_SHA']==native_dll_sha(),'same frozen/qualified native DLL identity, optional actual installed bytes')
    require(identity['source_hashes']==qual['source_bindings']==c['source_bindings']==con['source_hashes'],'same full production source bindings')
    for p,h in c['source_bindings'].items():require(sha(ROOT/p)==h,'current frozen production source '+p)
    for p,h in c['helpers'].items():require(sha(ROOT/p)==h,'current frozen campaign performance helper '+p)
    require(identity['helpers']==c['helpers']==con['helpers'],'same frozen final performance wrapper/helpers')
    require(c['development_protocol_SHA']==identity['prereg_sha256']==sha(OUT/'development_protocol.json'),'frozen actual development protocol')
    require(c['confirmation_protocol_SHA']==con['prereg_sha256']==sha(OUT/'confirmation_protocol.json'),'frozen actual confirmation protocol')
    require(c['input_manifest_SHA']==sha(OUT/'input_manifest.json'),'frozen exact input manifest')
    require(c['full_argv']['bridge01']==[x['command'] for x in identity['launches']] and c['full_argv']['confirmation01']==[x['command'] for x in con['launches']],'all frozen 21 complete argv unchanged')
    olddecision=OUT/'engineering/signed_gap_reader_correction01/round108_decisions.py'
    require(sha(olddecision)==c['decision_reader_SHA'] and sha(ROOT/'scripts/round108_decisions.py')=='9a827d2fccd9b37483c2d3a5f8aa5877abb5c2db434554d18abed28d13c63c46','approved narrowly corrected decision reader preserves original frozen source')
    require(obj(REVIEW/'reader_correction_review01.json')['decision']=='ACCEPT','own previous finite signed gap correction acceptance')
    return dict(production_PE_SHA=sha(PE),DLL_SHA=native_dll_sha(),current_installed_DLL_bytes_rehashed=DLL is not None,explicit_read_root=str(ROOT),no_original_root_fallback=True,candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
        qualification_identity_SHA=sha(OUT/'qualification/identity.json'),development_protocol_SHA=sha(OUT/'development_protocol.json'),
        confirmation_protocol_SHA=sha(OUT/'confirmation_protocol.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),
        bridge_identity_SHA=sha(OUT/'bridge01/identity.json'),confirmation_identity_SHA=sha(OUT/'confirmation01/identity.json'),
        performance_admission_SHA=sha(REVIEW/'performance_admission.json'),eligibility_review_SHA=sha(REVIEW/'sealed_input_eligibility.json'),
        source_bindings=c['source_bindings'],performance_helper_bindings=c['helpers'],frozen_original_decision_SHA=c['decision_reader_SHA'],
        approved_current_decision_SHA=sha(ROOT/'scripts/round108_decisions.py'),pure_current_campaign_reader_SHA=sha(ROOT/'scripts/round108_reader.py'),
        own_parser_SHA=sha(OWN_PARSER)),identity,obj(OUT/'qualification/cli01/identity.json')

def paired_models(armsmodels):
    records=[]
    for role in ['F2','C2']:
        ma,qa=armsmodels[role,'ENS-C'];mb,qb=armsmodels[role,'M-B'];require(qa==qb,'paired exact same input parse')
        for a in ma.values():
            b=next(x for x in mb.values() if x['bounds']['G']==a['bounds']['G'])
            require(a['bounds']==b['bounds'] and a['objective']==b['objective'],'paired actual interval model bounds/objective equal')
            changed=[n for n in a['types'] if a['types'][n]!=b['types'][n]]
            require(len(changed)==2*qa['V']*qa['M'] and all(n.startswith(('p_','d_')) and a['types'][n]=='I' and b['types'][n]=='C' for n in changed),'paired actual interval native types only p/d I to C')
            aa,bb=Counter(a['rows']),Counter(b['rows']);require(not aa-bb and sum((bb-aa).values())==2*qa['V'],'paired no row removed; exactly original 2V A/B added')
            # Presence already coefficient-exact checked against q for every MB model.
            records.append(dict(id=role,G_interval=a['bounds']['G'],ENS_rows=len(a['rows']),MB_rows=len(b['rows']),columns=len(a['bounds']),only_changed_quantity_types=len(changed),no_removed_original_row=True,exact_AB_added=2*qa['V']))
    return records

def fees():
    corrections={};records=[];starts=0;seconds=0.
    for p in sorted((OUT/'fee_corrections').glob('*.json')):
        q=obj(p);require(q['additional_conservative_starts']==1,'actual qualification inner-driver start correction only +1');corrections[q['label']]=q
    require(set(corrections)=={'qualification_prepare01','qualification_cli01'},'exact two omitted qualification drivers corrected')
    for folder in sorted((OUT/'fees').iterdir()):
        launch=obj(folder/'launch.json');receipt=obj(folder/'receipt.json')
        require(not launch['engineering'] and not receipt['engineering'] and receipt['exit_code']==0 and receipt['stop_reason']=='normal_return' and receipt['conservative_process_starts']==launch['conservative_process_starts'],'all paid outer wrappers closed normally')
        extra=corrections.get(folder.name,{}).get('additional_conservative_starts',0);n=launch['conservative_process_starts']+extra
        starts+=n;seconds+=receipt['outer_seconds'];records.append(dict(label=folder.name,declared_starts=launch['conservative_process_starts'],retained_inner_driver_correction=extra,corrected_starts=n,outer_seconds=receipt['outer_seconds'],launch_SHA=sha(folder/'launch.json'),receipt_SHA=sha(folder/'receipt.json'),nested_seconds_added=False))
    require(starts==26 and starts+20==46 and starts+4<=48 and seconds<80000,'corrected current 26/full46 conservative starts within48')
    require(near(next(x['outer_seconds'] for x in records if x['label']=='bridge01_all'),7739.755911200016,1e-9),'actual closed full six-arm bridge outer fee')
    return dict(paid_corrected_starts=starts,paid_outer_seconds=seconds,max_starts=48,max_outer_seconds=80000,full21_conservative_starts=46,next_complete_S12_group_reserved_starts=4,next_S12_total_starts=30,records=records,correction_bindings={q['label']:sha(OUT/'fee_corrections'/n) for n,q in [(p.name,obj(p)) for p in sorted((OUT/'fee_corrections').glob('*.json'))]},future_manual_corrected_fee_check_required=True)

def main():
    DEST.mkdir(exist_ok=False);tick=time.perf_counter();value={};error=None;decision='HOLD'
    save(DEST/'launch.json',dict(command=[sys.executable,*sys.argv],cwd=str(Path.cwd()),explicit_read_root=str(ROOT),exclusive_output=str(DEST),source_SHA=sha(Path(__file__)),own_parser_SHA=sha(OWN_PARSER),engineering=True,Optimize=0,LP_solve=0,IIS=0,native_environment=0,compiler=0,started_unix=time.time()))
    try:
        value['bindings'],identity,qi=bindings();value['fixed_F2_matrix']=base['matrix']()
        quals=[]
        for launch in qi['launches']:
            a,_,_=audit_arm(launch,qi,False);quals.append(a)
        value['qualification']=quals;arms=[];armmodels={}
        for launch in identity['launches']:
            a,m,q=audit_arm(launch,identity,True);arms.append(a);armmodels[a['id'],a['arm']]=(m,q)
        value['arms']=arms;value['paired_actual_interval_matrices']=paired_models(armmodels);value['gate']=decisions(arms);value['fees']=fees()
        require(value['gate']['bridge_pass'],'independently computed complete bridge passes')
        require(not value['gate']['current_positive_selection_unreachable']['positive_selection_unreachable'],'current measured pairs do not already make selection impossible')
        value['four_sealed_input_eligibility']=obj(REVIEW/'sealed_input_eligibility.json')['all_four_eligible_at_freeze']
        require(value['four_sealed_input_eligibility'],'actual independent four prospective inputs qualified at first freeze')
        decision='ACCEPT'
    except Exception as e:
        error=type(e).__name__+': '+str(e);value['traceback']=traceback.format_exc()
    value.update(decision=decision,error=error,reviewer_script_SHA=sha(Path(__file__)),completed_checks=count,completed_arms=milestones,
        read_bindings=reads,reviewer_zero_solver_calls=dict(Optimize=0,LP_solve=0,IIS=0,native_environment=0,compiler=0,production_edits=0),
        engineering_elapsed_seconds=time.perf_counter()-tick,scope='qualification plus all six raw bridge arms; no uniform selection or confirmation outcome inferred')
    save(DEST/'audit.json',value)
    save(DEST/'receipt.json',dict(decision=decision,error=error,exit_code=0 if decision=='ACCEPT' else 1,source_SHA=sha(Path(__file__)),audit_SHA=sha(DEST/'audit.json'),engineering_elapsed_seconds=time.perf_counter()-tick,Optimize=0,LP_solve=0,IIS=0,native_environment=0,compiler=0))
    print(json.dumps(dict(decision=decision,error=error,completed_checks=count,audit_SHA=sha(DEST/'audit.json')),ensure_ascii=False),flush=True)
    if decision!='ACCEPT':sys.exit(1)

if __name__=='__main__':main()
