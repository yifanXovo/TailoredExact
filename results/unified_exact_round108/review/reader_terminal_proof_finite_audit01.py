"""Finite source-extracted reader checks; synthetic dictionaries/models only.

No campaign raw data, instance file, native DLL or solver is opened. The only
native-looking logs are tiny synthetic texts under this review output folder.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse, ast, collections, copy, hashlib, json, math, re, sys, time, traceback

ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
ROOT=Path(a.root).resolve();DEST=Path(a.out).resolve();assert DEST.is_relative_to(ROOT/'results/unified_exact_round108/review')
DEST.mkdir(exist_ok=False);tick=time.perf_counter();checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def portable(root,value):
    p=Path(value);assert p.is_relative_to(root);return p
source=ROOT/'scripts/round108_reader.py';tree=ast.parse(source.read_text(encoding='utf-8'))
names={'returned_native_proofs','scoped_proofs','supported_leaf_bound','chronological_cover','model_scope_contract'}
selected=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
assert len(selected.body)==len(names)
namespace=dict(collections=collections,math=math,re=re,portable=portable,sha=sha,
    decision=SimpleNamespace(CLOSURE_TOL=1e-7,finite=lambda x:isinstance(x,(int,float)) and math.isfinite(x)))
exec(compile(selected,str(source),'exec'),namespace)
save(DEST/'launch.json',dict(command=[sys.executable,*sys.argv],cwd=str(Path.cwd()),explicit_read_root=str(ROOT),reader_source_SHA=sha(source),script_SHA=sha(Path(__file__)),engineering=True,synthetic_only=True,Optimize=0,LP_solve=0,native_environment=0))
def expect(name,fn,reject=False):
    try:value=fn()
    except (AssertionError,KeyError,ValueError) as e:
        assert reject,(name,type(e).__name__,str(e));checks.append(dict(name=name,outcome='correctly_rejected',exception=type(e).__name__));return
    assert not reject,(name,'unsupported synthetic evidence was accepted',value)
    checks.append(dict(name=name,outcome='accepted',value=value))

log=DEST/'synthetic_terminal.log';log.write_text('Optimal solution found (tolerance 0.00e+00)\nBest objective 8.000000000000e-01, best bound 8.000000000000e-01, gap 0.0000%\n',encoding='utf-8')
other=DEST/'synthetic_other_call.log';other.write_bytes(log.read_bytes())
call=dict(call=1,sequence=5,full_original=False,native_preconditions=True,leaf='L0',model_sha256='synthetic-same-model',native_log_path=str(log),lower_g=0.,upper_g=.9,cutoff=.9,
    cover=[dict(id='L0',lower_g=0.,upper_g=.9,lower=0.,cutoff=.9)])
row=dict(leaf_id='L0',model_sha256='synthetic-same-model',optimize_return_code='0',solve_kind='MIP',native_status='OPTIMAL',native_log=str(log))
j=dict(calls={1:call},not_started_ids=set(),returned_ids={1},return_sequences={1:10},bounds=[])
controller=dict(controller_native=[row],controller_LP_status=[])
returned=namespace['returned_native_proofs'];chronological=namespace['chronological_cover'];scope=namespace['model_scope_contract'];supported=namespace['supported_leaf_bound']
def changed_return(call_change=None,row_change=None,j_change=None):
    x=copy.deepcopy(j);c=copy.deepcopy(controller)
    if call_change:x['calls'][1].update(call_change)
    if row_change:c['controller_native'][0].update(row_change)
    if j_change:x.update(j_change)
    return returned(ROOT,x,c)
def future():
    x=copy.deepcopy(j);x['calls'][1]['cover'][0]['lower']=.8
    x['returned_native_proofs']=returned(ROOT,x,controller)
    return chronological(x,controller,.8)
def current_bound():
    x=copy.deepcopy(j);x['bounds']=[dict(sequence=7,call=1,native_bound=.7,global_available=True)]
    x['returned_native_proofs']=returned(ROOT,x,controller)
    return chronological(x,controller,.8)
def prior_return_available():
    x=copy.deepcopy(j);c=copy.deepcopy(controller)
    second=copy.deepcopy(call);second.update(call=2,sequence=12);second['cover'][0]['lower']=.8
    x['calls'][2]=second;x['returned_ids'].add(2);x['return_sequences'][2]=20;c['controller_native'].append(copy.deepcopy(row))
    x['returned_native_proofs']=returned(ROOT,x,c)
    return chronological(x,c,.8)

try:
    expect('valid final OPTIMAL native log bound linked exact call/model/log/return',lambda:returned(ROOT,j,controller))
    expect('different native log path rejected even byte-identical same model/leaf',lambda:changed_return(row_change={'native_log':str(other)}),True)
    expect('wrong model SHA rejected',lambda:changed_return(row_change={'model_sha256':'different'}),True)
    expect('wrong leaf rejected',lambda:changed_return(row_change={'leaf_id':'L1'}),True)
    expect('failed native Optimize return rejected',lambda:changed_return(row_change={'optimize_return_code':'1'}),True)
    expect('missing committed native return rejected',lambda:changed_return(j_change={'returned_ids':set()}),True)
    expect('missing return sequence rejected',lambda:changed_return(j_change={'return_sequences':{}}),True)
    expect('future terminal final bound cannot justify earlier cover snapshot',future,True)
    expect('current committed native bound is chronologically usable',current_bound)
    expect('terminal final log becomes usable for next call only after its return',prior_return_available)
    leaf=dict(gamma_L=0.,gamma_U=.9,lower_bound=1.1)
    proof=dict(lo=0.,hi=.9,L=1.1,cutoff=.9,sequence=10,call=1)
    expect('conditional native b above cutoff supplies min(b,cutoff) and preserves raw claim',lambda:supported(leaf,[proof],.9))
    expect('same above-cutoff claim cannot be used unconditionally',lambda:supported(leaf,[proof]),True)
    expect('missing tail cannot supply a whole-leaf positive bound',lambda:supported(dict(gamma_L=0.,gamma_U=.9,lower_bound=.8),[dict(proof,hi=.5,L=.8)],.9),True)
    expect('missing middle cannot supply a whole-leaf positive bound',lambda:supported(dict(gamma_L=0.,gamma_U=.9,lower_bound=.8),[dict(proof,hi=.2,L=.8),dict(proof,lo=.5,L=.8)],.9),True)
    # Model grammar is that of the pure reader, not this reviewer's LP parser.
    c=dict(full_original=False,lower_g=0.,upper_g=.4,cutoff=.8)
    objective=(tuple(sorted([('G',1.),('e_1',.15)])),0.)
    rows=[(objective[0],'<=',.8),((('h_1_2',1.),),'>=',0.),(tuple(sorted([('h_1_2',1.),('r_1',-.8),('r_2',-.8)])),'<=',0.)]
    m=dict(bounds={'G':(0.,.4)},objective=objective,rows=rows);panel={'V':2}
    expect('valid original Bounds-only G domain plus shared true-G rows',lambda:scope(c,m,panel))
    expect('metadata upper wider than actual G bounds rejected',lambda:scope(dict(c,upper_g=.5),m,panel),True)
    expect('metadata lower wider than actual G bounds rejected',lambda:scope(dict(c,lower_g=.1),m,panel),True)
    expect('actual G domain widened without matching metadata rejected',lambda:scope(c,dict(m,bounds={'G':(0.,.5)}),panel),True)
    expect('saved cutoff widened rejected',lambda:scope(c,dict(m,rows=[(objective[0],'<=',.9),*rows[1:]]),panel),True)
    expect('saved true-G cap missing rejected',lambda:scope(c,dict(m,rows=rows[:2]),panel),True)
    expect('saved true-G floor missing rejected',lambda:scope(c,dict(m,rows=[rows[0],rows[2]]),panel),True)
    expect('saved true-G cap wider rejected',lambda:scope(c,dict(m,rows=[*rows[:2],(tuple(sorted([('h_1_2',1.),('r_1',-1.),('r_2',-1.)])),'<=',0.)]),panel),True)
    shifted=dict(c,lower_g=.1);mr=dict(m,bounds={'G':(.1,.4)},rows=[rows[0],(tuple(sorted([('h_1_2',1.),('r_1',-.2),('r_2',-.2)])),'>=',0.),rows[2]])
    expect('valid positive true-G floor and matching saved Bounds',lambda:scope(shifted,mr,panel))
    expect('positive true-G floor widened to zero rejected',lambda:scope(shifted,dict(mr,rows=rows),panel),True)
    # LP-row native log linkage is checked too, before LP proofs are skipped.
    expect('LP wrong native log path rejected',lambda:changed_return(call_change={'native_preconditions':False},row_change={'solve_kind':'LP','native_log':str(other)}),True)
    decision='ACCEPT';error=None;code=0
except Exception as e:
    decision='HOLD';error=type(e).__name__+': '+str(e);code=1
    (DEST/'traceback.txt').write_text(traceback.format_exc(),encoding='utf-8')
save(DEST/'checks.json',dict(decision=decision,error=error,cases=checks,reader_source_SHA=sha(source),script_SHA=sha(Path(__file__)),synthetic_only=True,Optimize=0,LP_solve=0,native_environment=0))
save(DEST/'receipt.json',dict(command=[sys.executable,*sys.argv],explicit_read_root=str(ROOT),exit_code=code,decision=decision,error=error,source_SHA=sha(Path(__file__)),reader_source_SHA=sha(source),checks_SHA=sha(DEST/'checks.json'),engineering_elapsed_seconds=time.perf_counter()-tick,Optimize=0,LP_solve=0,native_environment=0))
print(json.dumps(dict(decision=decision,error=error,cases=len(checks),checks_SHA=sha(DEST/'checks.json'))));sys.exit(code)
