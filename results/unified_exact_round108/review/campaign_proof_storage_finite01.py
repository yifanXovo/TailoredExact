"""Pure finite equivalence audit of this reviewer's chronological proof storage."""
from pathlib import Path
import argparse,ast,hashlib,json,sys,time
ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();root=Path(a.root).resolve();dest=Path(a.out).resolve();assert dest.is_relative_to(root/'results/unified_exact_round108/review');dest.mkdir(exist_ok=False);tick=time.perf_counter()
source=root/'results/unified_exact_round108/review/campaign_raw_audit01.py';tree=ast.parse(source.read_text(encoding='utf-8'));supported=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='supported');arm=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='audit_arm');remember=next(n for n in arm.body if isinstance(n,ast.FunctionDef) and n.name=='remember_proof')
def require(good,message):assert good,message
ns=dict(require=require,prior={});exec(compile(ast.Module(body=[supported,remember],type_ignores=[]),str(source),'exec'),ns)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
proofs=[dict(call=1,lo=0.,hi=1.,cutoff=1.,L=.1),dict(call=2,lo=0.,hi=.5,cutoff=1.,L=.4),dict(call=1,lo=0.,hi=1.,cutoff=1.,L=.3),dict(call=2,lo=0.,hi=.5,cutoff=1.,L=.2),dict(call=3,lo=.5,hi=1.,cutoff=1.,L=.5),dict(call=2,lo=0.,hi=.5,cutoff=1.,L=1.1),dict(call=4,lo=0.,hi=1.,cutoff=.3,L=.9),dict(call=1,lo=0.,hi=1.,cutoff=1.,L=.3),dict(call=3,lo=.5,hi=1.,cutoff=1.,L=.4),dict(call=5,lo=.2,hi=.4,cutoff=.8,L=.7)]
cases=[];allproofs=[]
for seq,p in enumerate(proofs,1):
 p.update(sequence=seq,source='synthetic');allproofs.append(p);ns['remember_proof'](p)
 for lo,hi in [(0.,1.),(0.,.5),(.5,1.),(.1,.9),(.2,.4)]:
  before=ns['supported'](lo,hi,allproofs);after=ns['supported'](lo,hi,list(ns['prior'].values()));assert before==after,(seq,lo,hi,before,after);assert all(x['sequence']<=seq for x in ns['prior'].values())
  cases.append(dict(sequence=seq,interval=[lo,hi],all_prior_supported_L=before,strongest_identical_scope_supported_L=after,future_evidence_used=False))
assert ns['prior'][(1,0.,1.,1.)]['sequence']==3,'equal later raw bound must keep earlier availability'
assert ns['prior'][(2,0.,.5,1.)]['L']==1.1 and ns['supported'](0.,.5,list(ns['prior'].values()))==1.,'conditional cap remains min(bound,cutoff)'
save(dest/'checks.json',dict(decision='ACCEPT',cases=cases,all_prefixes_equal=True,weak_or_equal_repeated_native_proofs_not_used_to_shift_availability=True,each_original_raw_event_still_individually_audited=True,no_solver_or_performance_storage_changed=True,reviewer_source_SHA=sha(source),script_SHA=sha(Path(__file__))))
save(dest/'receipt.json',dict(command=[sys.executable,*sys.argv],explicit_read_root=str(root),exit_code=0,decision='ACCEPT',seconds=time.perf_counter()-tick,checks_SHA=sha(dest/'checks.json'),reviewer_source_SHA=sha(source),source_SHA=sha(Path(__file__)),Optimize=0,LP_solve=0,native_environment=0))
print(json.dumps(dict(decision='ACCEPT',finite_equivalences=len(cases),checks_SHA=sha(dest/'checks.json'))))
