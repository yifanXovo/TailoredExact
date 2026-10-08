"""Tiny synthetic proof audit; source extraction only, no project imports/data/models."""
from pathlib import Path
import ast, collections, copy, hashlib, json, math, sys, time, types

ROOT=Path('E:/codes/ExactEBRP-round108');REVIEW=ROOT/'results/unified_exact_round108/review';DEST=REVIEW/'reader_proof_finite_audit01'
SOURCE=ROOT/'scripts/round108_reader.py';DEST.mkdir(exist_ok=False)
tick=time.perf_counter();source=SOURCE.read_bytes();source_sha=hashlib.sha256(source).hexdigest();tests=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,q):
    with p.open('x',encoding='utf-8') as f:json.dump(q,f,indent=2,allow_nan=False);f.write('\n')
def good(name,fn,expect=None):
    value=fn();assert expect is None or expect(value),name;tests.append(dict(name=name,passed=True,rejected=False));return value
def reject(name,fn):
    try:fn()
    except (AssertionError,KeyError):tests.append(dict(name=name,passed=True,rejected=True));return
    raise AssertionError('failed to reject: '+name)
try:
    tree=ast.parse(source);wanted={'scoped_proofs','supported_leaf_bound','chronological_cover','complete_cover','model_scope_contract'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted];assert len(nodes)==len(wanted)
    tables={};finite=lambda v:isinstance(v,(int,float)) and math.isfinite(v)
    ns=dict(math=math,collections=collections,decision=types.SimpleNamespace(CLOSURE_TOL=1e-7,finite=finite),
        evidence=types.SimpleNamespace(number=lambda x:float(x) if x not in ['',None] else None),close=lambda a,b:abs(a-b)<=1e-7,
        rows=lambda p:tables[p.name])
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE),'exec'),ns)
    support=ns['supported_leaf_bound'];chrono=ns['chronological_cover'];scoped=ns['scoped_proofs'];scope=ns['model_scope_contract'];cover=ns['complete_cover']
    def call(i,seq,lo=0.,hi=.3,cutoff=.3,native=True,claim=0.,pieces=None):
        return dict(call=i,sequence=seq,leaf='L0',lower_g=lo,upper_g=hi,cutoff=cutoff,model_sha256='synthetic-'+str(i),native_preconditions=int(native),full_original=False,
            cover=pieces or [dict(id='L0',lower_g=lo,upper_g=hi,lower=claim,cutoff=cutoff)])
    def journal(calls,bounds=(),returns=None):
        return dict(calls={c['call']:c for c in calls},bounds=list(bounds),return_sequences=returns or {},not_started_ids=set())
    def controller(lp=None):
        if not lp:return dict(controller_native=[],controller_LP_status=[])
        c,L=lp
        return dict(controller_native=[dict(leaf_id=c['leaf'],solve_kind='LP',model_sha256=c['model_sha256'],optimize_return_code='0',native_status='OPTIMAL')],
            controller_LP_status=[dict(leaf_id=c['leaf'],gamma_L=str(c['lower_g']),gamma_U=str(c['upper_g']),terminal_valid='1',optimal='1',infeasible='0',bound_available='1',lower_bound=str(L),native_status='OPTIMAL')])
    def bound(i,seq,L):return dict(call=i,sequence=seq,native_bound=L,global_available=1,global_bound=min(L,.3))
    pieces=[dict(id='left',lower_g=0.,upper_g=.1,lower=0.,cutoff=.3),dict(id='L0',lower_g=.1,upper_g=.2,lower=.1,cutoff=.3),dict(id='right',lower_g=.2,upper_g=.3,lower=.2,cutoff=.3)]
    cj=journal([call(1,1,.1,.2,pieces=pieces)],[bound(1,2,.4)])
    result=good('valid native bound above cutoff remains valid conditional proof',lambda:chrono(cj,controller(),.3),lambda a:any(r['reported_lower']==.4 and r['unconditional_claim']==.3 and abs(r['independently_supported_lower']-.3)<1e-12 for r in a))
    good('conditional proof cap leaves raw input claim untouched',lambda:cj['bounds'][0]['native_bound'],lambda v:v==.4)
    reject('unsupported native snapshot lower rejects',lambda:chrono(journal([call(1,1,claim=.2)]),controller(),.3))
    lp=call(1,1,native=False);mip=call(2,4,claim=.2);lc=controller((lp,.2))
    good('completed earlier LP supports later native snapshot',lambda:chrono(journal([lp,mip],returns={1:3}),lc,.3))
    reject('future LP return cannot support earlier call snapshot',lambda:chrono(journal([lp,call(2,2,claim=.2)],returns={1:3}),lc,.3))
    reject('future native bound cannot support earlier call snapshot',lambda:chrono(journal([call(1,1),call(2,2,claim=.2)],[bound(1,3,.2)]),controller(),.3))
    good('earlier committed native bound supports next call',lambda:chrono(journal([call(1,1),call(2,3,claim=.2)],[bound(1,2,.2)]),controller(),.3))
    bad=copy.deepcopy(lc);bad['controller_LP_status'][0]['gamma_U']='.2'
    reject('LP status interval mismatch rejects',lambda:scoped(journal([lp],returns={1:3}),bad,.3))
    bad=copy.deepcopy(lc);bad['controller_native'][0]['model_sha256']='different'
    reject('LP native model SHA mismatch rejects',lambda:scoped(journal([lp],returns={1:3}),bad,.3))
    bad=copy.deepcopy(lc);bad['controller_LP_status'][0]['terminal_valid']='0'
    reject('nonterminal LP cannot support later snapshot',lambda:chrono(journal([lp,mip],returns={1:3}),bad,.3))
    proof=lambda lo,hi,L:dict(lo=lo,hi=hi,L=L,cutoff=.3)
    reject('local proof misses tail and cannot support whole leaf',lambda:support(dict(gamma_L=0,gamma_U=.3,lower_bound=.2),[proof(0,.1,.2)],.3))
    reject('interior domain hole prevents whole-leaf lower',lambda:support(dict(gamma_L=0,gamma_U=.3,lower_bound=.2),[proof(0,.1,.2),proof(.2,.3,.25)],.3))
    good('physical true-G floor is valid without optimization',lambda:support(dict(gamma_L=.2,gamma_U=.3,lower_bound=.2),[]),lambda v:v==.2)
    good('scoped objective complement caps proof without mutating it',lambda:support(dict(gamma_L=0,gamma_U=.3,lower_bound=.4),[proof(0,.3,.4)],.3),lambda v:v==.3)
    def synthetic_model(lo=.1,hi=.3,cutoff=.6):
        objective=((('G',1.),('e_1',.05)),.02)
        rr=[((('G',1.),),'>=',lo),((('G',1.),),'<=',hi),(objective[0],'<=',cutoff-objective[1])]
        for gamma,sense in [(hi,'<='),(lo,'>=')]:
            t={f'h_{i}_{k}':1. for i in range(1,4) for k in range(i+1,4)}
            if gamma:t.update({f'r_{i}':-3*gamma for i in range(1,4)})
            rr.append((tuple(sorted(t.items())),sense,0.))
        return dict(bounds={'G':(lo,hi)},objective=objective,rows=rr)
    sc=call(1,1,.1,.3,.6);model=synthetic_model()
    good('actual saved G/rows/cap/floor/objective cutoff scope matches',lambda:scope(sc,model,{'V':3}),lambda q:q['metadata_scope_is_actual_model_scope'])
    wide=dict(sc,upper_g=.4)
    reject('metadata interval wider than actual G bounds rejects',lambda:scope(wide,model,{'V':3}))
    mod=copy.deepcopy(model);mod['bounds']['G']=(.1,.4)
    reject('metadata wider than saved explicit G upper row rejects',lambda:scope(wide,mod,{'V':3}))
    mod=copy.deepcopy(model);mod['bounds']['G']=(.1,.4);mod['rows'][1]=((('G',1.),),'<=',.4)
    reject('metadata wider than actual true-G cap rejects despite widened epigraph G',lambda:scope(wide,mod,{'V':3}))
    mod=copy.deepcopy(model);mod['rows'][-1]=synthetic_model(lo=.15)['rows'][-1]
    reject('saved true-G floor differs from metadata rejects',lambda:scope(sc,mod,{'V':3}))
    mod=copy.deepcopy(model);mod['rows'][2]=(mod['objective'][0],'<=',.5-mod['objective'][1])
    reject('saved objective cutoff differs from metadata rejects',lambda:scope(sc,mod,{'V':3}))
    raw_L=.3+1e-15;native=call(1,1);j=journal([native],[bound(1,2,raw_L)]);cc=controller()
    cc['controller_native']=[dict(leaf_id='L0',solve_kind='MIP',optimize_return_code='0',native_status='OPTIMAL')]
    tables.update({'paper_leaf_ledger.csv':[dict(leaf_id='L0',gamma_L='0',gamma_U='.3',lower_bound=str(raw_L),status='closed',lower_bound_sources='native_terminal_mip_bound',lp_complete='0',closure_source='native_terminal_mip_optimal')],
        'global_bound_trace.csv':[dict(verified_global_upper_bound='.3',active_leaf_valid_lower_bound=str(raw_L),other_open_leaf_min_valid_lower_bound='',valid_global_lower_bound='.3')]})
    out=good('final raw lower and tiny negative signed gap retained',lambda:cover(Path('synthetic-only'),.3,j,cc,.5),lambda r:r['L']==raw_L and .3-r['L']<0)
    tables['paper_leaf_ledger.csv'][0].update(gamma_U='.1',lower_bound='.1');tables['global_bound_trace.csv'][0].update(active_leaf_valid_lower_bound='.1',valid_global_lower_bound='.1')
    reject('complete cover missing physical domain tail rejects',lambda:cover(Path('synthetic-only'),.3,j,cc,.5))
    # Availability source check and finite arithmetic; execute no full rebuild.
    text=source.decode();assert "available_offset_upper=arm['complete_seconds']-ep['completion']['fully_observed_end_to_end_seconds']" in text
    assert "x['available']+available_offset_upper<=checkpoint" in text and 'original_supervisor_available_seconds' in text
    for pre,post,supervisor,w in [(0,0,10,5),(2,3,10,5),(0,7,10,9),(7,0,10,9)]:
        total=pre+supervisor+post;offset=total-supervisor;safe=w+offset;actual=w+pre
        good('whole-arm omitted overhead safely bounds unknown prelude '+str((pre,post)),lambda:offset,lambda z:z>=pre and safe>=actual)
    assert sha(SOURCE)==source_sha,'source changed during finite audit'
    outcome=dict(decision='ACCEPT',review_scope='Pure synthetic proof functions and source-only conservative availability offset',source_path=str(SOURCE),source_SHA=source_sha,
        extracted_functions=sorted(wanted),cases=tests,total_cases=len(tests),actual_performance_models_or_inputs_read=False,
        conditional_raw_bound_above_cutoff_preserved=True,final_raw_L_preserved=out['L'],final_synthetic_signed_gap=.3-out['L'],
        availability_offset_scope='whole-arm minus supervisor includes all omitted pre/post work and bounds unknown prelude; raw original availability preserved',reviewer_calls=dict(Optimize=0,LP_solve=0,IIS=0,native_environment=0,compiler=0,full_reader=0,actual_model_reader=0,sealed_input_reader=0))
    save(DEST/'checks.json',outcome);code=0;error=None
except Exception as e:
    code=1;error=type(e).__name__+': '+str(e);save(DEST/'failure.json',dict(error=error,source_SHA=source_sha,completed_cases=tests))
receipt=dict(exit_code=code,error=error,command=['D:/msys64/ucrt64/bin/python.exe',str(Path(__file__))],cwd=str(ROOT),actual_python_executable=sys.executable,
    reviewer_source_SHA=sha(Path(__file__)),reader_source_SHA=source_sha,elapsed_seconds=time.perf_counter()-tick,
    output_SHA=sha(DEST/('checks.json' if code==0 else 'failure.json')),Optimize=0,LP_solve=0,IIS=0,compiler=0,full_reader=0)
save(DEST/'receipt.json',receipt)
print(json.dumps(dict(exit_code=code,error=error,cases=len(tests),source_SHA=source_sha,receipt_SHA=sha(DEST/'receipt.json'))));sys.exit(code)
