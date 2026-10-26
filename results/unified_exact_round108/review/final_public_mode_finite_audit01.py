"""Synthetic-only checks of post-final fees, no-binary mode and final selection."""
from pathlib import Path
from types import SimpleNamespace
import argparse, ast, copy, hashlib, json, re, sys, time, traceback

ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
root=Path(a.root).resolve();dest=Path(a.out).resolve();assert dest.is_relative_to(root/'results/unified_exact_round108/review');dest.mkdir(exist_ok=False)
tick=time.perf_counter();cases=[];sha_reads=[]
def sha(p):
    p=Path(p).resolve();assert p.is_relative_to(dest) or p==source or p==Path(__file__).resolve()
    sha_reads.append(str(p));return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def require(b,message):assert b,message
source=root/'results/unified_exact_round108/review/campaign_raw_audit01.py';tree=ast.parse(source.read_bytes())
names={'binary_identity','next_group_reservation','own_final_selection','independent_checkpoints','data'}
body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(body)==len(names)
original_reads=[]
def original_data(p):original_reads.append(str(p));return Path(p).read_bytes()
ns=dict(Path=Path,re=re,require=require,sha=sha,ROOT=dest/'public',DLL=None,args=SimpleNamespace(isolated_public_math=True),original_data=original_data)
exec(compile(ast.Module(body=body,type_ignores=[]),str(source),'exec'),ns)
identity=ns['binary_identity'];reserve=ns['next_group_reservation'];selection=ns['own_final_selection'];checkpoint=ns['independent_checkpoints']
current=dest/'current';public=dest/'public';outside=dest/'original_available';public.mkdir();outside.mkdir()
pe=current/'build/research/round108-frozen-mb-v1/ExactEBRP.exe';pe.parent.mkdir(parents=True);pe.write_text('synthetic text bytes, never a native executable\n',encoding='utf-8')
dll=outside/'gurobi130.dll';dll.write_text('synthetic text bytes, never loaded\n',encoding='utf-8')
oldpe=outside/'old.ExactEBRP.exe';oldpe.write_bytes(pe.read_bytes());expectedPE=sha(pe);expectedDLL=sha(dll)
(public/'inside.txt').write_text('fresh public evidence\n',encoding='utf-8');(outside/'outside.txt').write_text('must never be read as a fallback\n',encoding='utf-8')
save(dest/'launch.json',dict(actual_command=[sys.executable,*sys.argv],explicit_read_root=str(root),source_SHA=sha(Path(__file__)),independent_raw_source_SHA=sha(source),synthetic_only=True,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
def expect(name,action,reject=False):
    try:v=action()
    except (AssertionError,KeyError,ValueError,FileNotFoundError) as e:
        assert reject,(name,type(e).__name__,str(e));cases.append(dict(name=name,outcome='correctly_rejected',exception=type(e).__name__));return
    assert not reject,(name,'invalid evidence accepted',v);cases.append(dict(name=name,outcome='accepted',value=v))
order=['S12','B24','L48','F5','N36'];roles=['F2','C2',*order]
arms=[dict(id=r,arm=m,PE_SHA='a'*64,DLL_SHA='b'*64) for r in roles for m in ['P-GRB','ENS-C','M-B']]
classes={'F2':'WIN','C2':'WIN','S12':'TIE','B24':'WIN','L48':'WIN','F5':'WIN','N36':'WIN'}
gate=dict(bridge_pass=True,pairs=[dict(id=r,control='P-GRB',classification=classes[r],severe_regression=False) for r in roles]+[dict(id=r,control='ENS-C',classification='LOSS',severe_regression=True) for r in roles])
eligibility={r:True for r in ['S12','B24','L48','N36']}
def select(change=None,aa=None,ee=None,cc=()):
    g=copy.deepcopy(gate)
    if change:change(g)
    return selection(arms if aa is None else aa,g,eligibility if ee is None else ee,cc)
def muststage(fn,stage):
    v=fn();assert v['stage']==stage;return v['conditions']
def alterpair(g,role,key,value):next(p for p in g['pairs'] if p['id']==role and p['control']=='P-GRB')[key]=value
try:
    expect('final46 starts reserves zero missing next group rather than fictitious50',lambda:reserve(order,46,47514.073242100014))
    expect('before N36 exact42 plus4/reserve16320 retained',lambda:reserve(order[:-1],42,31400.737309299933))
    expect('completed budget exact hard wall boundary allowed with zero next group',lambda:reserve(order,46,80000.))
    expect('completed outer budget above original bound rejected',lambda:reserve(order,46,80000.01),True)
    expect('an incomplete group cannot shrink actual conservative start count',lambda:reserve(order[:-1],46,31400.),True)
    expect('wrong frozen group ordering rejected',lambda:reserve(['B24'],30,8000.),True)
    expect('next whole group cannot exceed remaining wall budget',lambda:reserve(order[:-1],42,70000.),True)
    expect('current mode rehashes explicit root PE and supplied DLL bytes',lambda:identity(current,expectedPE,expectedDLL,False,dll))
    expect('current mode wrong PE byte identity rejected',lambda:identity(current,'0'*64,expectedDLL),True)
    expect('current mode wrong supplied DLL byte identity rejected',lambda:identity(current,expectedPE,'0'*64,False,dll),True)
    expect('current missing root PE rejects despite available old-root PE bytes',lambda:identity(public,expectedPE,expectedDLL),True)
    sha_reads.clear();value=identity(public,expectedPE,expectedDLL,True)
    assert not sha_reads and not value['PE_bytes_rehashed'] and not value['DLL_bytes_rehashed'] and value['retained_actual_run_identity_only']
    cases.append(dict(name='isolated public math binds retained identity with zero binary-byte reads',outcome='accepted',value=value))
    expect('isolated public math rejects explicit DLL without reading bytes',lambda:identity(public,expectedPE,expectedDLL,True,dll),True)
    expect('isolated public math rejects any root PE presence',lambda:identity(current,expectedPE,expectedDLL,True),True)
    expect('missing or malformed retained binary identity rejected',lambda:identity(public,'bad',expectedDLL,True),True)
    expect('isolated evidence data reader accepts fresh root plain file',lambda:ns['data'](public/'inside.txt').decode())
    expect('isolated reader rejects available original-root plain-file fallback',lambda:ns['data'](outside/'outside.txt'),True)
    assert str((outside/'outside.txt').resolve()) not in original_reads
    ns['args'].isolated_public_math=False;ns['DLL']=dll.resolve()
    expect('current mode only the explicitly declared outside DLL exception is allowed',lambda:ns['data'](dll).decode())
    expect('current mode other outside evidence is still rejected',lambda:ns['data'](outside/'outside.txt'),True)
    expect('all21/exactfour/resource selection retains severe ENS loss without hidden veto',lambda:muststage(select,'SELECT_MB_FOR_BROAD_EVALUATION'))
    expect('one whole registered ENS arm missing prevents complete21 admission',lambda:muststage(lambda:select(aa=arms[:-1]),'NO_NEW_UNIFORM_CANDIDATE_SELECTED'))
    expect('duplicate extra formal arm cannot fake complete21 identity',lambda:muststage(lambda:select(aa=arms+[arms[0]]),'NO_NEW_UNIFORM_CANDIDATE_SELECTED'))
    mixed=copy.deepcopy(arms);mixed[-1]['PE_SHA']='c'*64
    expect('mixed production PE blocks uniform candidate',lambda:muststage(lambda:select(aa=mixed),'NO_NEW_UNIFORM_CANDIDATE_SELECTED'))
    expect('any current cancellation blocks positive selection',lambda:muststage(lambda:select(cc=['N36 M-B']),'NO_NEW_UNIFORM_CANDIDATE_SELECTED'))
    expect('missing fourth prospective eligibility blocks denominator shrinkage',lambda:muststage(lambda:select(ee={r:True for r in ['S12','B24','L48']}),'NO_NEW_UNIFORM_CANDIDATE_SELECTED'))
    expect('exact two WIN and one LOSS boundary remains eligible',lambda:muststage(lambda:select(lambda g:alterpair(g,'N36','classification','LOSS')),'SELECT_MB_FOR_BROAD_EVALUATION'))
    expect('fewer than two fixed-four WIN blocks selection',lambda:muststage(lambda:select(lambda g:(alterpair(g,'L48','classification','TIE'),alterpair(g,'N36','classification','TIE'))),'NO_NEW_UNIFORM_CANDIDATE_SELECTED'))
    expect('more than one fixed-four LOSS blocks selection even two WIN remain',lambda:muststage(lambda:select(lambda g:(alterpair(g,'S12','classification','LOSS'),alterpair(g,'B24','classification','LOSS'))),'NO_NEW_UNIFORM_CANDIDATE_SELECTED'))
    expect('severe primary P regression blocks selection',lambda:muststage(lambda:select(lambda g:alterpair(g,'N36','severe_regression',True)),'NO_NEW_UNIFORM_CANDIDATE_SELECTED'))
    expect('F5 LOSS blocks selection independently of unseen count',lambda:muststage(lambda:select(lambda g:alterpair(g,'F5','classification','LOSS')),'NO_NEW_UNIFORM_CANDIDATE_SELECTED'))
    expect('unevaluable primary pair blocks selection',lambda:muststage(lambda:select(lambda g:alterpair(g,'F5','classification','UNEVALUABLE')),'NO_NEW_UNIFORM_CANDIDATE_SELECTED'))
    expect('failed bridge chooses stopped bridge stage',lambda:muststage(lambda:select(lambda g:g.update(bridge_pass=False)),'STOP_MB_REOPENING_AT_BRIDGE'))
    t=[dict(sequence=1,safe_complete_arm_available=305.,raw_supervisor_available=295.,own_U=1.,committed_global_L=.1,signed_gap=.9),dict(sequence=2,safe_complete_arm_available=3500.,raw_supervisor_available=3490.,own_U=.5,committed_global_L=.4,signed_gap=.1)]
    cp=checkpoint(dict(complete_seconds=5371.),dict(panel=dict(cap_seconds=5400)),t)
    assert cp[0]['observed'] is False and cp[-1]['observed'] is False and next(x for x in cp if x['seconds']==3600)['U']==.5
    cases.append(dict(name='checkpoint uses safe wrapper-overhead offset and never extrapolates reserve-ended5400',outcome='accepted',value=cp))
    decision='ACCEPT';error=None;code=0
except Exception as e:
    decision='HOLD';error=type(e).__name__+': '+str(e);code=1;(dest/'traceback.txt').write_text(traceback.format_exc(),encoding='utf-8')
save(dest/'checks.json',dict(decision=decision,error=error,cases=cases,script_SHA=sha(Path(__file__)),independent_raw_source_SHA=sha(source),synthetic_only=True,actual_original_reads=original_reads,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
save(dest/'receipt.json',dict(actual_command=[sys.executable,*sys.argv],explicit_read_root=str(root),source_SHA=sha(Path(__file__)),independent_raw_source_SHA=sha(source),checks_SHA=sha(dest/'checks.json'),exit_code=code,decision=decision,error=error,seconds=time.perf_counter()-tick,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
print(json.dumps(dict(decision=decision,error=error,cases=len(cases),checks_SHA=sha(dest/'checks.json'))));sys.exit(code)
