"""Independent, finite, offline review of Round112 completed and interrupted arms.

No solver imports, native launch, compiler, source mutation, or old result edits.
"""
import collections, copy, csv, datetime, hashlib, json, math, pathlib, sys
HERE=pathlib.Path(__file__).parent
sys.path.insert(0,str(HERE))
import admission_audit as r
ROOT=r.ROOT; OUT=r.OUT; DEST=OUT/'review/postformal03'
sys.path.insert(0,str(ROOT/'scripts'))
import round111_seed_audit as models

def rows(p):
 r.sha(p)
 with pathlib.Path(p).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def normalized(w,p):
 w=copy.deepcopy(w); classes=collections.defaultdict(list)
 for k,Q in enumerate(p['Q_vector']):classes[Q].append(k)
 by={a.get('vehicle',a.get('vehicle_id')):a for a in w['routes']}
 used=[]
 for Q,ids in classes.items():
  routes=[copy.deepcopy(by[k]) for k in ids if k in by and by[k]['operations']]
  routes.sort(key=lambda a:-len(a['operations']))
  for k,a in zip(ids,routes):a['vehicle']=k;used.append(a)
 w['routes']=sorted(used,key=lambda a:a['vehicle']);return w
def fleetkey(ph):
 return sorted((a['Q'],tuple(a['nodes']),tuple(tuple(z) for z in a['operations'])) for a in ph['full_fleet'])
def own_pair(A,C):
 U,L,t=A['U'],A['L'],A['t'];uc,lc,tc=C['U'],C['L'],C['t'];gap=U-L;gc=uc-lc
 au=max(.001,.01*abs(uc));ag=max(.001,.10*abs(gc));at=max(30.,.10*tc)
 if A['certificate']!=C['certificate']:
  return ('WIN' if A['certificate'] else 'LOSS',bool(C['certificate']))
 if A['certificate']:
  return ('WIN' if tc-t>=at else 'LOSS' if t-tc>=at else 'TIE',t>=2*tc and t-tc>=120)
 good=(uc-U>=au or gc-gap>=ag);bad=(U-uc>=au or gap-gc>=ag)
 cls='MIXED' if good and bad else 'WIN' if good else 'LOSS' if bad else 'TIE'
 severe=(U-uc>=max(.001,.05*abs(uc)) and gap-gc>=max(.005,.25*abs(gc)))
 return cls,severe
def main():
 DEST.mkdir(exist_ok=False)
 candidate=r.read(OUT/'candidate_identity.json');campaign=r.read(OUT/'campaign/identity.json');gate=r.read(OUT/'review/performance_admission.json')
 assert r.sha(OUT/'candidate_identity.json')==gate['candidate_identity_SHA']
 assert r.sha(OUT/'campaign/identity.json')==gate['campaign_identity_SHA']
 assert r.sha(ROOT/campaign['prereg']['candidate_binary'])==gate['production_PE_SHA']
 for group in ('source_bindings','helpers'):
  for p,h in candidate[group].items():assert r.sha(ROOT/p)==h,p
 initial=OUT/'review/postformal01/reconstruction'
 for p in sorted(initial.iterdir()):
  if p.is_file():r.sha(p)
 arms0=rows(initial/'arms.csv'); assert len(arms0)==12
 by0={(a['id'],a['arm']):a for a in arms0};arms=[];by={};starts=[];H={}
 for l in campaign['launches'][:12]:
  d=pathlib.Path(l['destination']);actual=r.read(d/'launch.json')
  assert all(actual[k]==v for k,v in l.items())
  res=r.read(d/'result.json');a=r.read(d/'audit.json');c=r.read(d/'completion.json')
  native=r.read(d/'native_end_receipt.json');post=r.read(d/'postexit_audit_receipt.json');whole=r.read(d/'whole_arm_receipt.json');r.read(d/'audit_execution_metrics.json')
  assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap'] and a['passed']
  assert 0<native['complete_seconds_until_native_end']<=post['complete_seconds_until_audit_end']<=whole['complete_seconds']<=l['cap_seconds']
  assert whole['metrics_written_before_whole'] and whole['includes_admission_identity_startup_native_outputs_necessary_postexit_audit_crosscheck_metrics']
  ph,_=r.physical(l['panel'],res);x=by0[(l['id'],l['arm'])]
  r.close(ph['F'],float(x['U']));r.close(a['endpoint']['L'],float(x['L']));r.close(float(x['gap']),float(x['U'])-float(x['L']),1e-15)
  r.close(whole['complete_seconds'],float(x['complete_seconds']),1e-10)
  assert x['formal_protocol_qualified']=='True' and x['formal_performance']=='True' and x['numbers_qualified']=='True' and x['certificate_qualified']=='True'
  arm=dict(number=l['number'],id=l['id'],arm=l['arm'],U=ph['F'],L=float(x['L']),gap=ph['F']-float(x['L']),certificate=x['certificate']=='True',t=whole['complete_seconds'],native_Optimize=int(x['native_Optimize']),whole_SHA=r.sha(d/'whole_arm_receipt.json'),audit_SHA=r.sha(d/'audit.json'))
  arms.append(arm);by[(l['id'],l['arm'])]=arm
  if l['arm']!='P-GRB':
   hw=r.read(d/'hga.csv.exchange/final.json');hp,_=r.physical(l['panel'],hw);tr=r.traces(d)
   assert {int(z['seed']) for z in tr['hga.csv.descent.csv']}==set(range(1,26))
   assert not any(z['interrupted']=='1' for z in tr['hga.csv.descent.csv'])
   hr=r.read(d/'result.json.round112.startup.json') if l['arm']=='P-S' else res
   assert hr['decoded_descent_complete'] and hr['decoded_descent_seeds_completed']==25
   assert any('seed=20260626, runs=24' in z for z in hr['notes'])
   H[(l['id'],l['arm'])]=(hp,tr)
  if l['arm']=='P-S':
   own=r.read(d/'result.json.round112.startup.json');op,_=r.physical(l['panel'],own)
   assert ph['F']<=op['F']+1e-7 and res['gurobi_optimize_count']==1
   mapped=normalized(own,l['panel']); mp,_=r.physical(l['panel'],mapped);r.close(mp['F'],op['F'],1e-10)
   v=r.vector_audit(l['panel'],d,d/'native.log.round112.start',mapped)
   receipt=r.read(d/'native.log.round112.start.json')
   assert receipt['submitted'] and receipt['submission_count']==1 and receipt['readback_valid'] and receipt['matrix_unchanged'] and receipt['API']=='GRBsetdblattrarray(Start)'
   starts.append(dict(id=l['id'],own_H_U=op['F'],semantic_capacity_normalization='stable descending operation count within equal Q classes',receipt=receipt,**v))
 assert sum(a['native_Optimize'] for a in arms)==46
 same=[]
 for role in ('F2','R98-C2','R108-L48'):
  p,t=H[(role,'P-S')]
  for method in ('ENS-C','M-B'):
   ph,tr=H[(role,method)];assert tr==t and ph['Y']==p['Y'] and fleetkey(ph)==fleetkey(p)
   r.close(ph['F'],p['F'],1e-14);same.append(dict(id=role,candidate=method,qualified=True,trace_files=len(t),full_capacity_assigned_fleet_equal=True,actual_H_seed=20260626))
 pairs=[]
 for x in rows(initial/'pairs.csv'):
  if x['id'] not in ('F2','R98-C2','R108-L48'):assert x['classification']=='UNEVALUABLE';continue
  cls,severe=own_pair(by[(x['id'],x['candidate'])],by[(x['id'],x['control'])])
  assert cls==x['classification'] and severe==(x['severe_regression']=='True'),(x,cls,severe)
  pairs.append(dict(id=x['id'],candidate=x['candidate'],control=x['control'],classification=cls,severe_regression=severe))
 assert len(pairs)==18
 fees=[]
 for path in sorted((OUT/'fees').glob('*/launch.json')):
  l=r.read(path);f=r.read(path.parent/'receipt.json')
  assert f['actual_exit_observed'] and f['necessary_trailer_complete'] and f['charge_includes_wrapper_exit_observation_delay'] and not f['nested_native_seconds_added']
  assert 0<f['outer_seconds_lower']<=f['outer_seconds_upper']
  assert abs(f['outer_seconds_upper']-(f['caller_observed_unix']-l['wrapper_creation_unix']))<.01
  assert l['conservative_process_starts']==l['declared_native_children']+1
  fees.append(dict(label=path.parent.name,starts=l['conservative_process_starts'],actual_children=f['actual_native_children'],upper=f['outer_seconds_upper'],lower=f['outer_seconds_lower'],code=f['exit_code']))
 assert sum(f['starts'] for f in fees)==39;r.close(sum(f['upper'] for f in fees),18061.35593342781,1e-8)
 main04=next(f for f in fees if f['label']=='main04');assert main04['code']==1 and main04['actual_children']==1 and main04['starts']==5
 l=campaign['launches'][12];d=pathlib.Path(l['destination']);p=l['panel'];actual=r.read(d/'launch.json');assert all(actual[k]==v for k,v in l.items())
 missing=['result.json','completion.json','observations.json','audit.json','native_end_receipt.json','postexit_audit_receipt.json','whole_arm_receipt.json','audit_execution_metrics.json']
 assert all(not (d/n).exists() for n in missing)
 commits=[];events=[];prior=0
 for seq in range(1,13):
  cp=d/'journal'/f'event_{seq}.commit';jp=d/'journal'/f'event_{seq}.json';r.sha(cp);data=jp.read_bytes();sha=r.sha(jp)
  sig=cp.read_text().split();assert sig[0]=='NEJ1' and int(sig[1])==seq and int(sig[3])==len(data) and sig[4]==sha
  assert float(sig[2])>=prior;prior=float(sig[2]);event=json.loads(data);assert event['sequence']==seq
  commits.append(dict(sequence=seq,data_close_seconds=prior,bytes=len(data),SHA=sha,kind=event['kind']));events.append(event)
 assert len(list((d/'journal').glob('*.commit')))==12
 witnesses=[];calls=[];context=models.ArmModels();unique={}
 for e in events:
  if e['kind']=='witness':
   ph,_=r.physical(p,e);witnesses.append(dict(sequence=e['sequence'],call=e['call'],source=e['source'],F=ph['F'],G=ph['G'],P=ph['P'],maximum_duration=ph['maximum_duration'],Y=ph['Y'],full_fleet=ph['full_fleet'],return_loads=ph['return_loads']))
  if e['kind']=='call':
   path=pathlib.Path(e['model_path']);assert r.sha(path)==e['model_sha256']
   con,model=context.model_contract(ROOT,p,path,'M-B');sc=context.model_scope_contract(e,model,p);unique[con['SHA']]=con
   z=e['settings'];assert z['read_return_code']==0 and z['Threads']==1 and z['Seed']==0 and z['Presolve']==-1 and z['MIPGap']==z['MIPGapAbs']==0
   assert z['FeasibilityTol']==1e-6 and z['IntFeasTol']==1e-5 and z['OptimalityTol']==1e-6
   calls.append(dict(call=e['call'],full_original=e['full_original'],native_preconditions=e['native_preconditions'],leaf=e['leaf'],model_contract=con,scope_contract=sc,settings=z,returned=any(x['kind']=='returned' and x['call']==e['call'] for x in events)))
 context.clear();assert len(calls)==4 and len(unique)==3 and [c['returned'] for c in calls]==[True,True,True,False]
 assert len(witnesses)==3;r.close(witnesses[-1]['F'],.008182628062360801)
 hp,_=r.physical(p,r.read(d/'hga.csv.exchange/final.json'));tr=r.traces(d)
 assert {int(z['seed']) for z in tr['hga.csv.descent.csv']}==set(range(1,26)) and not any(z['interrupted']=='1' for z in tr['hga.csv.descent.csv'])
 assert fleetkey(hp)==fleetkey(r.physical(p,r.read(d/'external/initial_witness.json'))[0])
 ledgers={n:len(rows(d/'external'/n)) for n in ['paper_optimize_ledger.csv','lp_status_ledger.csv']};assert all(n==0 for n in ledgers.values())
 for path in sorted(d.rglob('*')):
  if path.is_file():r.sha(path)
 samples=[json.loads(s) for s in (d/'samples.jsonl').read_text().splitlines()];last=samples[-1]
 r.sha(OUT/'fees/main04/failure.txt');failure=(OUT/'fees/main04/failure.txt').read_text(encoding='utf-8')
 assert 'PermissionError: [WinError 5]' in failure and 'os.replace(temporary, path)' in failure
 status=r.read(OUT/'campaign/runtime_status.json');temporary=r.read(OUT/'campaign/runtime_status.json.tmp')
 for n in ('scripts/round112_campaign.py','scripts/round90_lp_g_g3.py','scripts/round88_a1_g3.py'):r.sha(ROOT/n)
 assert all(not pathlib.Path(z['destination']).exists() for z in campaign['launches'][13:])
 output=dict(schema='round112_independent_postformal_review_v1',decision='BLOCKED',reviewer='/root/independent_review',signed_at_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_identity_SHA=gate['candidate_identity_SHA'],production_PE_SHA=gate['production_PE_SHA'],campaign_identity_SHA=gate['campaign_identity_SHA'],historical_admission_SHA=r.sha(OUT/'review/performance_admission.json'),source_and_performance_helpers_unchanged=True,reviewer_native_starts=0,reviewer_Optimize=0,completed_qualified=12,actual_interrupted=1,truly_unstarted=7,formal_pair_positions=30,evaluable_pairs=18,UNEVALUABLE_pairs=12,completed_native_Optimize=46,qualified_arms=arms,paid_Starts=starts,same_H=same,independent_pairs=pairs,backend_vector_for_each_ENS_C_and_M_B=['WIN','WIN','LOSS','UNEVALUABLE','UNEVALUABLE'],backend_denominator=5,backend_conclusion_for_each='INCOMPLETE_ATTRIBUTION',fees=fees,conservative_process_starts=39,outer_seconds_upper=sum(f['upper'] for f in fees),partial=dict(number=13,id=l['id'],arm=l['arm'],classification='ACTUAL_INTERRUPTED',formal_endpoint_qualified=False,missing=missing,commits=commits,witnesses=witnesses,models=list(unique.values()),calls=calls,H_complete=True,H_comparable_to_unstarted_control=False,buffered_ledgers=ledgers,last_sample=last,status_before_failed_replace=status,failed_replace_temporary=temporary,own_original_valid_UB=witnesses[-1]['F'],independent_analytical_floor=0,strict_certificate=False,whole_clock_available=False,mathematical_only=True,normal_return_lower_claim_or_complete_cover_not_admitted=True),observed_failure='atomic_status os.replace(runtime_status.json.tmp,runtime_status.json) raised PermissionError WinError 5; wrapper returned 1; source finally kills and waits for an active child before exception propagation; outer fee closed.',cause_limit='Parent reports concurrent PowerShell Get-Content reads. A Windows delete-sharing conflict is plausible. No handle trace, access control trace, or antivirus trace proves this is the unique cause. Saved samples are above resource-stop RAM and disk thresholds.',limitations=['The current partial native call has no returned record or native-end/whole receipts. No partial journal is promoted into a formal endpoint, clock, certificate, or full-cover proof.','All 20 fixed argv slots and 30 pair positions remain. Declared main04 wrapper and 4 child slots remain charged although only 1 child started.','The initial ordinary reader reconstruction predates its new interrupted/unstarted distinction; its 12 completed mathematical results are retained, while the final BLOCKED reader still requires delta review.','Historical ACCEPT was finite admission before performance. It remains a distinct historical signature and does not imply completion or repair this execution failure.'],bindings=r.BIND)
 (DEST/'postformal_review.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
 print(json.dumps({k:output[k] for k in ['decision','completed_qualified','actual_interrupted','truly_unstarted','evaluable_pairs','UNEVALUABLE_pairs','completed_native_Optimize','conservative_process_starts','outer_seconds_upper']},indent=2))
if __name__=='__main__':main()
