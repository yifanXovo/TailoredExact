"""Reviewer-owned finite offline audit. Never loads a solver or starts a native process."""
import ast,csv,hashlib,json,math,pathlib,re,struct,sys,time
ROOT=pathlib.Path('E:/codes/ExactEBRP-round112')
OUT=ROOT/'results/unified_exact_round112'; DEST=OUT/'review/admission02'
sys.path.insert(0,str(ROOT/'scripts'))
import round108_reader as inherited_parser
BIND={}
def sha(p):
 p=pathlib.Path(p);h=hashlib.sha256(p.read_bytes()).hexdigest();BIND[str(p.resolve())]=h;return h
def read(p):
 sha(p);return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
def close(x,y,tol=1e-7): assert math.isfinite(x) and math.isfinite(y) and abs(x-y)<=tol,(x,y)
def instance(p):
 path=ROOT/p['input_path'];assert sha(path)==p['input_sha256'];s=path.read_text()
 def vector(k):return ast.literal_eval(re.search(r'^\s*'+k+r'\s*=\s*(\[[^\n]*\])',s,re.M)[1])
 a={k:vector(k) for k in ('initial','target','capacities','weights','points')}
 if abs(max(a['weights'][1:])-10)<1e-6:a['weights']=[x/10 for x in a['weights']]
 a['Q']=p['Q_vector'];assert len(a['Q'])==p['M'];return a
def physical(p,w):
 a=instance(p);Y=a['initial'].copy();seen=set();cars=set();full=[];returns=[];durations=[]
 by={r.get('vehicle',r.get('vehicle_id')):r for r in w['routes']};assert len(by)==len(w['routes']) and set(by)<=set(range(p['M']))
 for k,Q in enumerate(a['Q']):
  r=by.get(k,dict(nodes=[0,0],operations=[]));nodes=r['nodes'];assert len(nodes)>=2 and nodes[0]==nodes[-1]==0
  ops={}
  for op in r['operations']:
   i,x,y=(op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else op
   assert i not in ops and x>=0 and y>=0 and int(x)==x and int(y)==y and bool(x)!=bool(y);ops[i]=(x,y)
  assert len(nodes[1:-1])==len(ops) and set(nodes[1:-1])==set(ops);load=0;pick=0
  for i in nodes[1:-1]:
   assert 1<=i<=p['V'] and i not in seen;seen.add(i);x,y=ops[i];load+=x-y;pick+=x
   assert 0<=load<=Q;Y[i]+=y-x;assert 0<=Y[i]<=a['capacities'][i]
  travel=sum(math.hypot(a['points'][x][0]-a['points'][y][0],a['points'][x][1]-a['points'][y][1])/1.5 for x,y in zip(nodes,nodes[1:]))
  duration=travel+(p['pickup_seconds']+p['drop_seconds'])*pick;assert duration<=p['T_seconds']+1e-7
  durations.append(duration);returns.append(load);full.append(dict(vehicle=k,Q=Q,nodes=nodes,operations=[[i,*ops[i]] for i in nodes[1:-1]]))
 ratios=[Y[i]/a['target'][i] for i in range(1,p['V']+1)];S=sum(ratios)
 G=sum(abs(x-y) for j,x in enumerate(ratios) for y in ratios[j+1:])/(p['V']*S) if S else 0
 P=sum(a['weights'][i]*abs(ratios[i-1]-1) for i in range(1,p['V']+1));F=G+p['lambda']*P
 assert sum(Y[1:])==sum(a['initial'][1:])-sum(returns);close(F,w.get('F',w.get('objective')))
 return dict(F=F,G=G,P=P,Y=Y,full_fleet=full,return_loads=returns,maximum_duration=max(durations)),a
def vector_audit(p,d,stem,w):
 a=read(str(stem)+'.before.matrix.json');b=read(str(stem)+'.after.matrix.json');assert a==b
 path=pathlib.Path(str(stem)+'.values.csv');sha(path)
 with path.open(newline='') as f:rows=list(csv.DictReader(f))
 names=[c[0] for c in a['columns']];assert len(names)==len(set(names))==len(rows) and [r['variable'] for r in rows]==names
 vals={r['variable']:float(r['value']) for r in rows};v=[vals[n] for n in names]
 for r,c in zip(rows,a['columns']):
  x=float(r['value']);assert math.isfinite(x) and x==float(r['readback']) and r['type']==c[1]
  assert c[2]-1e-7<=x<=c[3]+1e-7
  if c[1] in 'BIN':assert abs(x-round(x))<=1e-7
 max_res=0
 for name,sense,rhs,terms in a['rows']:
  lhs=sum(v[i]*z for i,z in terms);res=abs(lhs-rhs) if sense=='=' else max(0,lhs-rhs) if sense=='<' else max(0,rhs-lhs)
  assert sense in '=<>',sense;assert res<=1e-7,(name,res);max_res=max(max_res,res)
 ph,inst=physical(p,w);obj=a['constant']+sum(v[i]*c[4] for i,c in enumerate(a['columns']));assert a['sense']==1;close(obj,ph['F'])
 # Independently reconstruct every original compact auxiliary and physical variable.
 expect={};ratio={i:ph['Y'][i]/inst['target'][i] for i in range(1,p['V']+1)}
 for r in ph['full_fleet']:
  k=r['vehicle'];nodes=r['nodes'];load=0
  if nodes==[0,0]:continue
  for pos,(x,y) in enumerate(zip(nodes,nodes[1:]),1):expect[f'x_{k}_{x}_{y}']=1.;expect[f'conn_{k}_{x}_{y}']=len(nodes)-1-pos
  for pos,(i,pick,drop) in enumerate(r['operations'],1):
   load+=pick-drop
   for family,val in [('z',1),('mode',int(pick>0)),('p',pick),('d',drop),('ord',pos),('load',load)]:expect[f'{family}_{k}_{i}']=val
 for n,x in vals.items():
  z=n.split('_');family=z[0];idx=[int(a) for a in z[1:] if re.fullmatch('-?\\d+',a)]
  if n in expect:y=expect[n]
  elif family in ('x','conn','z','mode','p','d','ord','load'):y=0
  elif n=='G':y=ph['G']
  elif n=='r_min':y=min(ratio.values())
  elif n=='r_max':y=max(ratio.values())
  elif n=='W_SP':y=sum(ratio.values())*ph['P']
  elif family=='Y':y=ph['Y'][idx[0]]
  elif family=='r':y=ratio[idx[0]]
  elif family=='e':y=abs(ratio[idx[0]]-1)
  elif family=='h':y=abs(ratio[idx[0]]-ratio[idx[1]])
  elif n.startswith('state_g_'):y=ph['G']*int(ph['Y'][idx[0]]==idx[1])
  elif family=='state':y=int(ph['Y'][idx[0]]==idx[1])
  elif family=='bit':y=(ph['Y'][idx[0]]>>idx[1])&1
  elif family=='prod':y=ph['G']*((ph['Y'][idx[0]]>>idx[1])&1)
  elif family=='zprod':y=ph['G']*ph['Y'][idx[0]]
  else:raise AssertionError(('unreviewed native column',n))
  close(x,y)
 return dict(columns=len(names),rows=len(a['rows']),maximum_row_residual=max_res,objective=obj,all_original_auxiliaries_from_own_fleet=True,before_SHA=sha(str(stem)+'.before.matrix.json'),after_SHA=sha(str(stem)+'.after.matrix.json'),vector_SHA=sha(path))
def semantic(x):
 if isinstance(x,dict):return {k:semantic(v) for k,v in x.items() if k not in {'sha256','elapsed_seconds','process_seconds','wall_seconds','timestamp','path'}}
 if isinstance(x,list):return [semantic(v) for v in x]
 return x
def traces(d):
 result={}
 for path in sorted(d.glob('hga.csv.*.csv'))+sorted((d/'hga.csv.exchange').iterdir()):
  sha(path);key=path.relative_to(d).as_posix()
  if path.suffix=='.csv':
   with path.open(newline='') as f:result[key]=[{k:v for k,v in r.items() if k not in {'process_seconds','elapsed_seconds','elapsed','timestamp','wall_seconds'}} for r in csv.DictReader(f)]
  elif path.suffix=='.json':result[key]=semantic(read(path))
  elif path.suffix=='.jsonl':result[key]=[semantic(json.loads(s)) for s in path.read_text().splitlines()]
  else:raise AssertionError(('unexpected H trace',path))
 return result
def argvflags(argv):
 d={};i=1
 while i<len(argv):
  k=argv[i];assert k.startswith('--') and k not in d
  if i+1<len(argv) and not argv[i+1].startswith('--'):d[k]=argv[i+1];i+=2
  else:d[k]=True;i+=1
 return d
def audit():
 DEST.mkdir(exist_ok=False);candidate=read(OUT/'candidate_identity.json');prod=read(OUT/'production_identity.json');campaign=read(OUT/'campaign/identity.json');protocol=read(OUT/'protocol.json')
 assert sha(OUT/'production_identity.json')==candidate['production_identity_SHA'];assert sha(OUT/'campaign/identity.json')==candidate['campaign_identity_SHA'];assert sha(OUT/'protocol.json')==candidate['protocol_SHA']==campaign['prereg_sha256'];assert sha(OUT/'goal.md')==protocol['full_goal_SHA'];assert sha(OUT/'input_manifest.json')==candidate['input_manifest_SHA']
 for group in ('source_bindings','helpers'):
  assert candidate[group]==(prod[group] if group=='source_bindings' else campaign[group])
  for path,h in candidate[group].items():assert sha(ROOT/path)==h,path
 assert campaign['source_hashes']==candidate['source_bindings'];assert campaign['runner_sha256']==sha(ROOT/'scripts/round112_campaign.py')
 pe=ROOT/campaign['prereg']['candidate_binary'];assert sha(pe)==candidate['production_PE_SHA']==prod['production_PE_SHA']==campaign['candidate_binary_sha256'];assert sha(pathlib.Path('D:/gurobi1302/win64/bin/gurobi130.dll'))==prod['DLL_SHA']==candidate['DLL_SHA'];assert sha(pathlib.Path(prod['compiler']))==prod['compiler_SHA']
 binary=pe.read_bytes();pos=struct.unpack_from('<I',binary,0x3c)[0]+24;assert struct.unpack_from('<Q',binary,pos+72)[0]==prod['stack_reserve']==2097152;assert struct.unpack_from('<Q',binary,pos+80)[0]==prod['stack_commit']==4096
 assert prod['measured_source_commit']==campaign['measured_source_commit']=='d0014a7163e3996fe120471420e56b089c9715ae';assert campaign['delivery_base_commit']=='ded38c756a32a464bfa9800212da75778707d974'
 fixed=[('F2',1200,['P-GRB','P-S','ENS-C','M-B']),('R98-C2',1800,['P-S','M-B','P-GRB','ENS-C']),('R108-L48',1800,['ENS-C','P-GRB','M-B','P-S']),('G50-C1',1800,['M-B','ENS-C','P-S','P-GRB']),('G100-R2',3600,['P-GRB','ENS-C','P-S','M-B'])]
 assert len(campaign['launches'])==20 and candidate['full_argv']==[l['command'] for l in campaign['launches']] and sum(l['cap_seconds'] for l in campaign['launches'])==40800
 argvs=[]
 for j,(role,cap,order) in enumerate(fixed):
  ls=campaign['launches'][4*j:4*j+4];assert [l['arm'] for l in ls]==order and all(l['id']==role and l['group_number']==j+1 and l['cap_seconds']==cap and l['seed']==0 and l['hard_stop_seconds']==cap-2 for l in ls)
  normalized={}
  for l in ls:
   assert not pathlib.Path(l['destination']).exists();a=argvflags(l['command']);p=l['panel'];instance(p)
   for flag,val in {'--threads':'1','--mip-threads':'1','--gurobi-seed':'0','--gurobi-presolve':'-1','--process-wall-time-limit':str(cap),'--process-shutdown-margin':'30','--time-limit':str(cap-6),'--input':p['input_path'],'--T':str(p['T_seconds']),'--lambda':'0.15','--pickup-time':'60','--drop-time':'60'}.items():assert a[flag]==val,(role,l['arm'],flag)
   assert '--gurobi-hga-start' not in a and '--round100-continuous-quantities' not in a
   if l['arm'] in ('P-GRB','P-S'):assert a['--method']=='gurobi' and a['--plain-baseline'] and a['--round61-candidate-mode']=='off'
   else:assert a['--algorithm-preset']=='research-round83-vds-equal-net-exchange' and a['--round65-witness-audit']=='true' and a['--round65-hga-zero-stop']=='true'
   if l['arm']=='P-S':assert a['--round112-ens-start-compact']
   if l['arm']=='M-B':assert a['--round98-state-service']=='m-binary'
   normalized[l['arm']]={k:v for k,v in a.items() if not k.endswith(('path','dir','log')) and k not in {'--out','--log','--process-phase-ledger','--gurobi-model-export','--gurobi-progress','--progress-log','--primal-heuristic-generation-log'}}
   argvs.append(dict(number=l['number'],id=role,arm=l['arm'],cap=cap,command_SHA=hashlib.sha256(json.dumps(l['command']).encode()).hexdigest()))
  ps=normalized['P-S'].copy();ps.pop('--round112-ens-start-compact');assert ps==normalized['P-GRB'];mb=normalized['M-B'].copy();mb.pop('--round98-state-service');assert mb==normalized['ENS-C']
 assert not (OUT/'campaign/summary.jsonl').exists();assert protocol['formal_arms']==20 and protocol['backend_exposure_required'] and protocol['zero_backend_not_exposed']
 summary=read(OUT/'qualification/summary.json');arms=[];starts=[]
 for x in summary['final_candidate_arms']:
  d=ROOT/x['raw'];l=read(d/'launch.json');result=read(d/'result.json');a=read(d/'audit.json');w=read(d/'whole_arm_receipt.json');post=read(d/'postexit_audit_receipt.json');n=read(d/'native_end_receipt.json');c=read(d/'completion.json');sha(d/'audit_execution_metrics.json')
  i=read(OUT/'qualification'/x['campaign']/'identity.json');assert all(l[k]==v for k,v in i['launches'][l['number']-1].items());assert sha(OUT/'qualification'/x['campaign']/'identity.json')==candidate['qualification_campaign_identity_SHAs']['qualification/'+x['campaign']]
  assert i['candidate_binary_sha256']==candidate['production_PE_SHA']==x['PE_SHA'];assert i['helpers']==candidate['helpers'] and i['source_hashes']==candidate['source_bindings'];assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
  assert 0<n['complete_seconds_until_native_end']<=post['complete_seconds_until_audit_end']<=w['complete_seconds']<=l['cap_seconds'];assert w['metrics_written_before_whole'] and w['includes_admission_identity_startup_native_outputs_necessary_postexit_audit_crosscheck_metrics'];assert sha(d/'whole_arm_receipt.json')==x['whole_receipt_SHA'];assert sha(d/'audit.json')==x['audit_SHA'];assert a['passed'];ph,_=physical(l['panel'],result);close(ph['F'],a['endpoint']['U']);close(a['endpoint']['gap'],a['endpoint']['U']-a['endpoint']['L'])
  assert result['gurobi_optimize_count']==x['Optimize'] if l['arm'] in ['P-GRB','P-S'] else True
  if l['arm']=='P-S':
   own=read(d/'result.json.round112.startup.json');physical(l['panel'],own);assert ph['F']<=own['objective']+1e-7
   if result['gurobi_optimize_count']:starts.append(dict(campaign=x['campaign'],**vector_audit(l['panel'],d,d/'native.log.round112.start',own)))
   else:assert result['status']=='startup_zero' and ph['F']<=1e-7
  arms.append(dict(campaign=x['campaign'],arm=x['arm'],id=x['id'],whole=w['complete_seconds'],U=ph['F'],L=a['endpoint']['L'],certificate=a['endpoint']['certificate'],Optimize=x['Optimize']))
 assert len(arms)==7 and sum(x['Optimize'] for x in arms)==14
 h100=OUT/'qualification/cli02/raw';hpaths={m:h100/f'{no:02d}_H100_S0_{m}' for no,m in [(2,'P-S'),(3,'ENS-C'),(4,'M-B')]};H={}
 for name,d in hpaths.items():
  launch=read(d/'launch.json');ph,_=physical(launch['panel'],read(d/'hga.csv.exchange/final.json'));t=traces(d);seeds={int(r['seed']) for r in t['hga.csv.descent.csv']};assert seeds==set(range(1,26)) and not any(r['interrupted']=='1' for r in t['hga.csv.descent.csv']);r=read(d/'result.json.round112.startup.json') if name=='P-S' else read(d/'result.json');assert any('seed=20260626, runs=24' in v for v in r['notes']);assert r['decoded_descent_complete'] and r['decoded_descent_seeds_completed']==25 and r['hga_stop_mode']=='decoded-descent-interroute';H[name]=(ph,t)
 for m in ('ENS-C','M-B'):assert H[m]==H['P-S'],m
 fees=[]
 for path in (OUT/'fees').glob('*/launch.json'):
  l=read(path);f=read(path.parent/'receipt.json');assert l['qualification'] and f['qualification'] and f['actual_exit_observed'] and f['necessary_trailer_complete'] and f['charge_includes_wrapper_exit_observation_delay'] and not f['nested_native_seconds_added'];assert 0<f['outer_seconds_lower']<=f['outer_seconds_upper'];assert abs(f['outer_seconds_upper']-(f['caller_observed_unix']-l['wrapper_creation_unix']))<.01;assert l['conservative_process_starts']==l['declared_native_children']+1;fees.append(dict(label=path.parent.name,starts=l['conservative_process_starts'],actual_children=f['actual_native_children'],upper=f['outer_seconds_upper'],lower=f['outer_seconds_lower'],code=f['exit_code']))
 assert sum(v['starts'] for v in fees)==19;close(sum(v['upper'] for v in fees),698.0634860992432);assert 19+25<=56 and sum(v['upper'] for v in fees)+40800+600<=48000
 assert next(x for x in fees if x['label']=='qualification_cli01')['starts']==5 and next(x for x in fees if x['label']=='qualification_cli01')['actual_children']==2 and next(x for x in fees if x['label']=='qualification_cli01')['code']==1
 casespath=OUT/'qualification/start_fault01/cases.jsonl';sha(casespath);cases=[json.loads(s) for s in casespath.read_text().splitlines()];assert len(cases)==13 and all(c['passed'] and c['native_Optimize_calls']==0 for c in cases);fault=read(OUT/'qualification/start_fault01/necessary_audit.json');assert fault['source_bindings']==candidate['source_bindings'] and fault['case_file_SHA']==sha(casespath);fl=read(OUT/'fees/start_fault01/native_launch.json');assert fl['production_source_bindings']==candidate['source_bindings'] and fl['test_source_SHA']==sha(OUT/'qualification/start_fault_batch.cpp') and fl['PE_SHA']==sha(ROOT/'build/research/round112-paid-v1/Round112StartFaultBatch.exe')
 for p in [protocol['roles'][0]]:pass
 eq=read(OUT/'qualification/original_model_equivalence.json');refs=[]
 for p in read(OUT/'input_manifest.json')['roles']+read(OUT/'input_manifest.json')['qualification_roles']:
  ref=OUT/'qualification/reference'/p['id'];r=read(ref/'build.json');assert r['optimizer_calls']==0 and sha(ref/'original.lp')==r['canonical_sha256'];refs.append(dict(id=p['id'],**r))
 oldpaths={'F2':'E:/codes/ExactEBRP-round108/results/unified_exact_round108/bridge01/reference/F2/original.lp','R98-C2':'E:/codes/ExactEBRP-round108/results/unified_exact_round108/bridge01/reference/C2/original.lp','R108-L48':'E:/codes/ExactEBRP-round108/results/unified_exact_round108/confirmation01/reference/L48/original.lp','G50-C1':'E:/codes/ExactEBRP-round110/results/unified_exact_round110/qualification/reference/G50-C1/original.lp','G100-R2':'E:/codes/ExactEBRP-round110/results/unified_exact_round110/qualification/reference/G100-R2/original.lp'}
 for r in eq['roles']:
  oldlp=pathlib.Path(oldpaths[r['id']]);assert oldlp.is_file(),oldlp;assert oldlp.read_bytes()==(OUT/'qualification/reference'/r['id']/'original.lp').read_bytes();sha(oldlp)
 payload=dict(passed=True,reviewer_native_starts=0,reviewer_Optimize=0,production_PE_SHA=candidate['production_PE_SHA'],candidate_identity_SHA=sha(OUT/'candidate_identity.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),compiler_SHA=prod['compiler_SHA'],DLL_SHA=prod['DLL_SHA'],source_count=len(candidate['source_bindings']),helper_count=len(candidate['helpers']),fixed_20_argv=argvs,seven_actual_arms=arms,paid_Starts=starts,H100_full_trace_and_capacity_fleet_equal=True,H100_trace_files=len(H['P-S'][1]),actual_H_seed=20260626,fault_cases=cases,fresh_references=refs,fees=fees,conservative_starts=19,outer_seconds_upper=sum(v['upper'] for v in fees),formal_starts_at_audit=0,finite_limitations=['No uncontrolled native API error was observed; injected errors exercise code guards only.','Deadline exhaustion after mapping and startup filesystem write failure were not executed.','No performance result or backend causal increment is concluded from qualification.'],bindings=BIND)
 (DEST/'raw_audit.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in payload.items() if k not in ('bindings','fixed_20_argv','seven_actual_arms','fault_cases','fresh_references','fees','paid_Starts')},indent=2))
if __name__=='__main__':audit()
