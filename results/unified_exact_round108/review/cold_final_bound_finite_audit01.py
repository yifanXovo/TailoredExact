"""Synthetic-only finite checks of the plain cold final-bound reader."""
from pathlib import Path
from types import SimpleNamespace
import argparse, ast, copy, hashlib, json, math, re, sys, time, traceback
ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
root=Path(a.root).resolve();dest=Path(a.out).resolve();assert dest.is_relative_to(root/'results/unified_exact_round108/review');dest.mkdir(exist_ok=False)
tick=time.perf_counter();cases=[];source=root/'scripts/round108_reader.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def portable(r,v):
    p=Path(v).resolve();assert p.is_relative_to(r);return p
tree=ast.parse(source.read_text(encoding='utf-8'));body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='cold_returned_bound'];assert len(body)==1
ns=dict(portable=portable,sha=sha,re=re,decision=SimpleNamespace(CLOSURE_TOL=1e-7,finite=lambda x:isinstance(x,(int,float)) and math.isfinite(x)),close=lambda x,y:abs(x-y)<=1e-7)
exec(compile(ast.Module(body=body,type_ignores=[]),str(source),'exec'),ns);fn=ns['cold_returned_bound']
d=dest/'synthetic';d.mkdir();compact=d/'compact.lp';compact.write_text('synthetic saved model bytes; no native model loaded\n',encoding='utf-8')
log=d/'native.log';other=d/'another_call.log'
valid_text='Optimal solution found (tolerance 0.00e+00)\nBest objective 8.000000000000e-01, best bound 8.000000000000e-01, gap 0.0000%\n'
log.write_text(valid_text,encoding='utf-8');other.write_text(valid_text,encoding='utf-8')
call=dict(full_original=True,native_preconditions=True,native_log_path=str(log),model_sha256=sha(compact),lower_g=0.,upper_g=.95)
j=dict(calls={1:call},started=1,returned=1,returned_ids={1},return_sequences={1:17},bounds=[dict(global_available=True,global_bound=.79)])
r=dict(gurobi_status=2,native_mip_best_bound=.8,native_mip_best_bound_available=True,lower_bound=.8)
save(dest/'launch.json',dict(command=[sys.executable,*sys.argv],cwd=str(Path.cwd()),explicit_read_root=str(root),source_SHA=sha(Path(__file__)),reader_source_SHA=sha(source),synthetic_only=True,Optimize=0,native_environment=0))
def invoke(jchange=None,rchange=None,cchange=None,text=None):
    x=copy.deepcopy(j);v=copy.deepcopy(r)
    if jchange:x.update(jchange)
    if rchange:v.update(rchange)
    if cchange:x['calls'][1].update(cchange)
    log.write_text(valid_text if text is None else text,encoding='utf-8')
    return fn(root,d,x,v)
def expect(name,action,reject=False):
    try:value=action()
    except (AssertionError,KeyError,ValueError) as e:
        assert reject,(name,str(e));cases.append(dict(name=name,outcome='rejected',exception=type(e).__name__));return
    assert not reject,(name,'invalid evidence accepted',value)
    cases.append(dict(name=name,outcome='accepted',value=value))
try:
    expect('valid final original integer bound stronger than every callback is accepted at returned sequence',invoke)
    expect('absence of callbacks does not remove a valid returned native bound',lambda:invoke(jchange={'bounds':[]}))
    expect('different native log path rejected even identical bytes',lambda:invoke(cchange={'native_log_path':str(other)}),True)
    expect('wrong saved original model hash rejected',lambda:invoke(cchange={'model_sha256':'wrong'}),True)
    expect('partial scope cannot masquerade as original cold model',lambda:invoke(cchange={'full_original':False}),True)
    expect('LP relaxation cannot supply integer final proof',lambda:invoke(cchange={'native_preconditions':False}),True)
    expect('unreturned native call rejected',lambda:invoke(jchange={'returned':0}),True)
    expect('missing returned event identity rejected',lambda:invoke(jchange={'returned_ids':set()}),True)
    expect('missing returned event sequence rejected',lambda:invoke(jchange={'return_sequences':{}}),True)
    expect('more than one native call rejected for original single cold solve',lambda:invoke(jchange={'calls':{1:call,2:call}}),True)
    expect('final readback status OPTIMAL cannot use TIME_LIMIT-only terminal text',lambda:invoke(text='Time limit reached\nBest objective .8, best bound .8, gap 0%\n'),True)
    expect('final readback requires finite original native bound',lambda:invoke(rchange={'native_mip_best_bound':float('nan')}),True)
    expect('unavailable final native bound rejected',lambda:invoke(rchange={'native_mip_best_bound_available':False}),True)
    expect('printed bound disagreement rejected',lambda:invoke(text=valid_text.replace('best bound 8.000000000000e-01','best bound 7.000000000000e-01')),True)
    expect('raw published lower bound disagreement rejected',lambda:invoke(rchange={'lower_bound':.7}),True)
    expect('prior callback greater than final by beyond tolerance rejected',lambda:invoke(jchange={'bounds':[dict(global_available=True,global_bound=.800001)]}),True)
    tiny=invoke(rchange={'native_mip_best_bound':.8000000000000002,'lower_bound':.8000000000000002})
    assert tiny['L']==.8000000000000002 and tiny['printed_native_final_bound']==.8 and tiny['sequence']==17
    cases.append(dict(name='printed precision does not round or replace exact raw final L and returned availability',outcome='accepted',value=tiny))
    expect('qualified normal native TIME_LIMIT final bound',lambda:invoke(rchange={'gurobi_status':9},text='Time limit reached\nBest objective .8, best bound .8, gap 0%\n'))
    expect('qualified original target interruption final bound',lambda:invoke(rchange={'gurobi_status':11},text='Solve interrupted\nBest objective .8, best bound .8, gap 0%\n'))
    # A final proof carries return sequence, never an earlier callback discovery.
    assert invoke()['sequence']==17 and invoke()['L']==.8
    cases.append(dict(name='final native proof is not available at a prior sequence',outcome='accepted',returned_sequence=17,prior_sequence=16,prior_available=False))
    decision='ACCEPT';error=None;code=0
except Exception as e:
    decision='HOLD';error=type(e).__name__+': '+str(e);code=1;(dest/'traceback.txt').write_text(traceback.format_exc(),encoding='utf-8')
save(dest/'checks.json',dict(decision=decision,error=error,cases=cases,reader_source_SHA=sha(source),script_SHA=sha(Path(__file__)),synthetic_only=True,Optimize=0,LP_solve=0,native_environment=0))
save(dest/'receipt.json',dict(command=[sys.executable,*sys.argv],explicit_read_root=str(root),source_SHA=sha(Path(__file__)),reader_source_SHA=sha(source),checks_SHA=sha(dest/'checks.json'),exit_code=code,decision=decision,error=error,seconds=time.perf_counter()-tick,Optimize=0,LP_solve=0,native_environment=0))
print(json.dumps(dict(decision=decision,error=error,cases=len(cases),checks_SHA=sha(dest/'checks.json'))));sys.exit(code)
