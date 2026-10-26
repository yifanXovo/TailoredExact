"""Independent synthetic next-leaf/whole-partition regression checks.

Source extraction only. No campaign input, actual model, native environment,
native DLL, solver or project import is read or executed.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse, ast, collections, copy, hashlib, json, math, re, sys, time, traceback

ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
root=Path(a.root).resolve();dest=Path(a.out).resolve()
assert dest.is_relative_to(root/'results/unified_exact_round108/review');dest.mkdir(exist_ok=False)
tick=time.perf_counter();cases=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def portable(r,v):
    p=Path(v).resolve();assert p.is_relative_to(r);return p
def require(b,message):assert b,message
def close(x,y,tol=1e-7):return abs(x-y)<=tol
def number(s):return None if s=='' else float(s)
source=root/'scripts/round108_reader.py';ownsource=root/'results/unified_exact_round108/review/campaign_raw_audit01.py'
def extract(path,names,ns):
    tree=ast.parse(path.read_text(encoding='utf-8'));body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(body)==len(names);exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),ns)
tables={}
def synthetic_rows(p):return copy.deepcopy(tables[Path(p).name])
ns=dict(math=math,collections=collections,re=re,portable=portable,sha=sha,rows=synthetic_rows,close=close,
    decision=SimpleNamespace(CLOSURE_TOL=1e-7,finite=lambda x:isinstance(x,(int,float)) and math.isfinite(x)),
    evidence=SimpleNamespace(number=number))
extract(source,{'returned_native_proofs','scoped_proofs','supported_leaf_bound','chronological_cover','complete_cover'},ns)
own=dict(math=math,rows=synthetic_rows,require=require,near=close,TOL=1e-7)
extract(ownsource,{'supported','final_partition'},own)
d=dest/'synthetic';d.mkdir()
leftlog=d/'left-next.log';rightlog=d/'right-terminal.log'
leftlog.write_text('Solve interrupted\nBest objective .8, best bound .6, gap 25.0000%\n',encoding='utf-8')
rightlog.write_text('Optimal solution found (tolerance 0.00e+00)\nBest objective .4, best bound .4, gap 0.0000%\n',encoding='utf-8')
calls={
    1:dict(call=1,sequence=2,full_original=False,native_preconditions=True,leaf='L0.0',model_sha256='left-synthetic-model',native_log_path=str(leftlog),lower_g=0.,upper_g=.2,cutoff=.8,
        cover=[dict(id='L0.0',lower_g=0.,upper_g=.2,lower=0.,cutoff=.8),dict(id='L0.1',lower_g=.2,upper_g=.8,lower=.2,cutoff=.8)]),
    2:dict(call=2,sequence=20,full_original=False,native_preconditions=True,leaf='L0.1',model_sha256='right-synthetic-model',native_log_path=str(rightlog),lower_g=.2,upper_g=.8,cutoff=.8,
        cover=[dict(id='L0.0',lower_g=0.,upper_g=.2,lower=.6,cutoff=.8),dict(id='L0.1',lower_g=.2,upper_g=.8,lower=.2,cutoff=.8)])}
j=dict(calls=calls,not_started_ids=set(),returned_ids={1,2},return_sequences={1:10,2:30},bounds=[])
controller=dict(controller_native=[
    dict(leaf_id='L0.0',model_sha256='left-synthetic-model',optimize_return_code='0',solve_kind='NEXT_LEAF_TARGET_MIP',native_status='INTERRUPTED',native_log=str(leftlog)),
    dict(leaf_id='L0.1',model_sha256='right-synthetic-model',optimize_return_code='0',solve_kind='MIP',native_status='OPTIMAL',native_log=str(rightlog))],controller_LP_status=[])
def leaf(i,parent,lo,hi,L,status,sources,closure=''):
    return dict(leaf_id=i,parent_id=parent,depth='0' if not parent else '1',gamma_L=str(lo),gamma_U=str(hi),lower_bound=str(L),status=status,lp_complete='0',lower_bound_sources=sources,closure_source=closure)
leaves=[leaf('L0','',0,.8,0,'replaced','objective_nonnegative_penalty_G_floor'),
    leaf('L0.0','L0',0,.2,.6,'open','valid_next_leaf_target_native_bound'),
    leaf('L0.1','L0',.2,.8,.4,'closed','native_terminal_mip_bound','native_terminal_mip_optimal')]
trace=[dict(verified_global_upper_bound='.4',active_leaf_valid_lower_bound='.4',other_open_leaf_min_valid_lower_bound='.6',valid_global_lower_bound='.4')]
events=[dict(event='atomic_split',leaf_id='L0')]
def setup(ls=None,ts=None):
    tables.update({'paper_leaf_ledger.csv':copy.deepcopy(leaves if ls is None else ls),'global_bound_trace.csv':copy.deepcopy(trace if ts is None else ts),'paper_tree_events.csv':copy.deepcopy(events)})
def qualified(x=None,c=None):
    x=copy.deepcopy(j if x is None else x);c=copy.deepcopy(controller if c is None else c)
    x['returned_native_proofs']=ns['returned_native_proofs'](root,x,c)
    return x,c
def primary(x=None,c=None,ls=None,ts=None):
    setup(ls,ts);x,c=qualified(x,c)
    chronology=ns['chronological_cover'](x,c,.4)
    result=ns['complete_cover'](d,.4,x,c,.9)
    return dict(L=result['L'],closed=result['all_relevant_closed'],open=result['open_leaves'],chronological_rows=len(chronology))
def independent(ls=None,proofs=None,native=None,ts=None):
    setup(ls,ts);x,c=qualified()
    pp=ns['scoped_proofs'](x,c,.4) if proofs is None else proofs
    nn=[dict(leaf=r['leaf_id'],solve_kind=r['solve_kind'],native_status=r['native_status']) for r in c['controller_native']] if native is None else native
    endpoint=min(float(r['lower_bound']) for r in tables['paper_leaf_ledger.csv'] if r['status'] not in {'replaced','coalesced'} and float(r['gamma_L'])<.4-1e-7)
    L,closed,result=own['final_partition'](d,{'V':10},.8,.4,pp,nn,[],{'lower_bound':endpoint})
    return dict(L=L,closed=closed,open=result['open_relevant_leaves'],actual_partitions=len(result['actual_parent_child_partitions']),qualified=result['independently_qualified_actual_leaves'])
def expect(name,action,reject=False):
    try:value=action()
    except (AssertionError,KeyError,ValueError) as e:
        assert reject,(name,type(e).__name__,str(e));cases.append(dict(name=name,outcome='correctly_rejected',exception=type(e).__name__));return
    assert not reject,(name,'unsupported evidence accepted',value)
    cases.append(dict(name=name,outcome='accepted',value=value))
save(dest/'launch.json',dict(command=[sys.executable,*sys.argv],cwd=str(Path.cwd()),explicit_read_root=str(root),source_SHA=sha(Path(__file__)),reader_source_SHA=sha(source),independent_raw_source_SHA=sha(ownsource),synthetic_only=True,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
try:
    expect('current reader discharges physically covered open next-leaf bound above own U',primary)
    expect('independent partition proves same open next-leaf discharge and genuine split',independent)
    x=copy.deepcopy(j);del x['calls'][1];x['returned_ids'].remove(1);del x['return_sequences'][1]
    c=copy.deepcopy(controller);c['controller_native']=c['controller_native'][1:]
    expect('missing successful next-leaf original native call cannot support open bound',lambda:primary(x,c),True)
    expect('independent actual next-leaf source requires exact corresponding NEXT call kind',lambda:independent(native=[dict(leaf='L0.0',solve_kind='MIP',native_status='INTERRUPTED'),dict(leaf='L0.1',solve_kind='MIP',native_status='OPTIMAL')]),True)
    c=copy.deepcopy(controller);c['controller_native'][0]['optimize_return_code']='1'
    expect('failed Optimize return rejected before next-leaf proof admission',lambda:primary(c=c),True)
    x=copy.deepcopy(j);x['returned_ids'].remove(1)
    expect('unreturned next-leaf call rejected',lambda:primary(x=x),True)
    c=copy.deepcopy(controller);c['controller_native'][0]['leaf_id']='wrong-leaf'
    expect('wrong leaf native-return identity rejected',lambda:primary(c=c),True)
    c=copy.deepcopy(controller);c['controller_native'][0]['model_sha256']='wrong-model'
    expect('wrong model native-return identity rejected',lambda:primary(c=c),True)
    c=copy.deepcopy(controller);c['controller_native'][0]['native_log']=str(rightlog)
    expect('wrong native log path rejected',lambda:primary(c=c),True)
    x=copy.deepcopy(j);x['calls'][2]['sequence']=7
    expect('future returned NEXT bound cannot support earlier native cover',lambda:primary(x=x),True)
    x=copy.deepcopy(j);x['calls'][1]['upper_g']=.1
    expect('next-leaf proof missing a true-G domain segment rejects claimed whole-leaf bound',lambda:primary(x=x),True)
    expect('no independent qualified proof cannot discharge a high raw open-leaf number',lambda:independent(proofs=[]),True)
    ls=copy.deepcopy(leaves);ls[1]['lower_bound_sources']='unreviewed_next_leaf_alias'
    expect('unreviewed provenance source token rejected',lambda:primary(ls=ls),True)
    expect('independent source token whitelist rejects unsupported alias',lambda:independent(ls=ls),True)
    ls=copy.deepcopy(leaves);ls[1]['gamma_U']='.1'
    expect('missing final true-G partition segment rejected',lambda:primary(ls=ls),True)
    expect('independent parent-child partition hole rejected',lambda:independent(ls=ls),True)
    ls=copy.deepcopy(leaves);ls[2]['parent_id']='nonexistent-parent'
    expect('independent actual ledger lineage rejects nonexistent parent',lambda:independent(ls=ls),True)
    ls=copy.deepcopy(leaves);ls[1]['lower_bound']='.3';ts=[dict(trace[0],other_open_leaf_min_valid_lower_bound='.3',valid_global_lower_bound='.3')]
    val=primary(ls=ls,ts=ts);assert val['closed'] is False and val['open']==1 and val['L']==.3
    cases.append(dict(name='covered but still-improving open leaf remains a certificate obligation',outcome='accepted',value=val))
    val=independent(ls=ls,ts=ts);assert not val['closed'] and val['open']==1
    cases.append(dict(name='independent still-improving open leaf remains open',outcome='accepted',value=val))
    ls=copy.deepcopy(leaves);ls[2]['lower_bound']=repr(.4000000000000001)
    for name,fn in [('current reader',primary),('independent reader',independent)]:
        ts=[dict(trace[0],active_leaf_valid_lower_bound=repr(.4000000000000001))]
        val=fn(ls=ls,ts=ts);assert val['L']==.4000000000000001 and .4-val['L']<0 and val['closed']
        cases.append(dict(name=name+' preserves tiny signed negative gap while qualifying complete scope',outcome='accepted',value=val,signed_gap=.4-val['L']))
    decision='ACCEPT';error=None;code=0
except Exception as e:
    decision='HOLD';error=type(e).__name__+': '+str(e);code=1;(dest/'traceback.txt').write_text(traceback.format_exc(),encoding='utf-8')
save(dest/'checks.json',dict(decision=decision,error=error,cases=cases,source_SHA=sha(Path(__file__)),reader_source_SHA=sha(source),independent_raw_source_SHA=sha(ownsource),synthetic_only=True,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
save(dest/'receipt.json',dict(command=[sys.executable,*sys.argv],explicit_read_root=str(root),source_SHA=sha(Path(__file__)),reader_source_SHA=sha(source),independent_raw_source_SHA=sha(ownsource),checks_SHA=sha(dest/'checks.json'),exit_code=code,decision=decision,error=error,seconds=time.perf_counter()-tick,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
print(json.dumps(dict(decision=decision,error=error,cases=len(cases),checks_SHA=sha(dest/'checks.json'))));sys.exit(code)
