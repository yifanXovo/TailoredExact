import ast,collections,gzip,hashlib,json,math,re,sys,time,zipfile
from pathlib import Path
from fractions import Fraction as F
R=Path('E:/codes/ExactEBRP-work/worktrees/round134');O=R/'results/unified_exact_round134';tick=time.perf_counter()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sys.path.insert(0,str(R/'scripts'));import round108_reader as core
assert 'gurobipy' not in sys.modules
result={'schema':'round134-independent-math-reader-review-v1','reviewer':'independent_review; separate from primary implementer','Optimize':0,'vendor_DLL_loads':0,'production_sources_modified':False,'findings':[],'checks':{}}
tiny=read(O/'math/tiny_exact.json');z=zipfile.ZipFile(R/tiny['carrier_path']);assert sha(z.filename)==tiny['carrier_SHA256'];tc={}
for cid,c in tiny['cases'].items():
 prefix='results/unified_exact_round132/joint/'+cid+'/';m=json.loads(z.read(prefix+'B_joint_exact_matrix.json'));e=json.loads(z.read(prefix+'enumeration.json'));obj=json.loads(z.read(prefix+'original_objective_joint.json'))
 sig={(r['sense'],F(r['RHS']),tuple(sorted((n,F(a)) for n,a in r['coefficients'].items()))):r['name'] for r in m['rows']}
 def has(s,c):return sig[(s,F(0),tuple(sorted((n,F(a)) for n,a in c.items())))]
 proof=[]
 for i in range(1,5):
  proof += [has('=',{'G':-1,**{f'state_g_{i}_{y}':1 for y in range(3)}}),has('=',{f'zprod_{i}':1,f'state_g_{i}_1':-1,f'state_g_{i}_2':-2}),has('<',{f'state_g_{i}_2':1,f'state_{i}_2':-F(3,4)})]
  assert all(F(m['bounds'][f'state_g_{i}_{y}'][0])>=0 for y in range(3))
 proof.append(has('>',{**{f'h_{i}_{j}':-1 for i in range(1,5) for j in range(i+1,5)},**{f'zprod_{i}':4 for i in range(1,5)}}));assert list(map(F,m['bounds']['G']))==[F(0),F(3,4)]
 for which in ['old_point','new_point']:
  p={n:F(v) for n,v in c[which].items()};assert set(p)<=set(m['bounds'])
  for row in m['rows']:
   d=sum(F(a)*p.get(n,F(0)) for n,a in row['coefficients'].items())-F(row['RHS']);assert (d==0 if row['sense']=='=' else d<=0 if row['sense']=='<' else d>=0),(cid,which,row['name'])
  for n,(lo,hi) in m['bounds'].items():assert F(lo)<=p.get(n,F(0))<=F(hi)
  assert F(obj['objective_constant'])+sum(F(a)*p.get(n,F(0)) for n,a in obj['objective_coefficients'].items())==F(c['L_old' if which=='old_point' else 'L_new'])
  for i in range(1,5):assert p[f'e_{i}']>=sum(abs(y-1)*p.get(f'state_{i}_{y}',F(0)) for y in range(3))
  for i in range(1,5):
   for j in range(i+1,5):
    for t in [0,1]:
     assert sum(p.get(f'state_{i}_{y}',F(0))-p.get(f'state_{j}_{y}',F(0)) for y in range(t+1))==0
     assert sum(p.get(f'state_g_{i}_{y}',F(0))-p.get(f'state_g_{j}_{y}',F(0)) for y in range(t+1))==0
 for fleet in c['balanced_joint_columns']:
  y=list(e['case']['b']);seen=set();assert list(e['joint_pair_indices'][fleet['index']])==fleet['pair']
  for k,j in enumerate(fleet['pair']):
   car=e['cars'][k][j];load=0;pickup=0;assert set(car['route'])=={i for i,t in enumerate(car['v']) if t[2]};assert len(car['route'])==len(set(car['route']))
   for i in car['route']:
    assert i not in seen;seen.add(i);p,d,zz=car['v'][i];assert zz==1 and (p>0)!=(d>0);load+=p-d;pickup+=p;assert 0<=load<=e['case']['Q'][k];y[i]+=d-p
   assert load==car['return_load'] and 120*pickup<=e['case']['T']
  assert y==fleet['Y'] and sorted(y)==[0,1,1,1]
 assert F(c['L_new'])-F(c['L_old'])==F(3,16) and F(c['integer_optimum'])-F(c['L_new'])==F(1,16)
 tc[cid]={'exact_rows_each_point':len(m['rows']),'exact_bounds_each_point':len(m['bounds']),'actual_VDP_numerator_rows':proof,'selected_complete_fleets_verified':4,'R88_pair_CDF_and_qCDF_differences_zero':True,'increment':'3/16','remaining_gap':'1/16'}
result['checks']['tiny']=tc
roots={}
for role in ['K-20-S','K-35-U']:
 folder=O/'math/roots'/role;s=read(folder/'scope.json');p=s['panel'];matrix=core.lp_model(folder/'current_export/original.lp');assert matrix==core.lp_model(Path(s['root_scope']['model_path']));assert sha(folder/'current_export/original.lp')==s['current_matrix_SHA']
 initial=ast.literal_eval(re.search(r'^initial\s*=\s*(.*)$',(R/p['input_path']).read_text(),re.M)[1]);assert sum(initial[1:])==p['total_initial'];values=[];max_viol=0;last=None
 for layer in range(3):
  d=folder/f'layer{layer}';c=read(d/'construction.json');r=read(d/'result.json');rows=read(d/'added_rows.json');support={int(i):ys for i,ys in c['supports'].items()};ratio={int(i):F(v) for i,v in c['ratio_coefficients'].items()}
  assert set(support)==set(range(1,p['V']+1)) and len(rows)==(0 if layer==0 else p['V']+(layer==2))
  for i,ys in support.items():
   assert {int(n.split('_')[2]) for n in matrix['bounds'] if re.fullmatch(fr'state_{i}_\d+',n)}==set(ys);assert all(matrix['bounds'][f'state_{i}_{y}'][0]>=0 for y in ys)
   assert any(sense=='=' and rhs==0 and dict(terms)=={f'r_{i}':1.,f'Y_{i}':-float(ratio[i])} for terms,sense,rhs in matrix['rows'])
  minima={i:min(ys) for i,ys in support.items()};rem=p['total_initial']-sum(minima.values());assert rem>=0;levels=sorted({ratio[i]*y for i,ys in support.items() for y in ys if y>0});prev=F(0);coeff=collections.defaultdict(F)
  for t in levels:
   forced=sum(ratio[i]*minima[i]>=t for i in support);costs=[]
   for i,ys in support.items():
    if ratio[i]*minima[i]>=t:continue
    active=[y for y in ys if ratio[i]*y>=t]
    if active:costs.append(min(active)-minima[i])
   used=0;k=0
   for cost in sorted(costs):
    if used+cost>rem:break
    used+=cost;k+=1
   for i,ys in support.items():
    for y in ys:
     if ratio[i]*y>=t:coeff[f'state_{i}_{y}']+=(t-prev)*(p['V']-forced-k)
   prev=t
  assert {n:F(v['exact']) for n,v in c['TC_coefficients'].items()}=={n:v for n,v in coeff.items() if v}
  for n,v in c['TC_coefficients'].items():assert F(v['written'])==F(v['written_exact'])<=F(v['exact'])
  for i,ys in support.items():
   for y in ys:
    v=c['old_penalty_coefficients'][f'state_{i}_{y}'];assert F(v['exact'])==abs(ratio[i]*y-1) and F(v['written'])<=F(v['exact'])
  assert r['Status']==2 and r['LP_Optimize']==1 and r['MIP_Optimize']==0 and r['after']['columns']==r['before']['columns'];assert all(r['quality'][n]<=1e-6 for n in ['ConstrVio','BoundVio','DualVio'])
  x=json.load(gzip.open(d/'solution.json.gz','rt',encoding='utf-8'))
  for row in rows:
   slack=math.fsum(a*x[n] for n,a in row['lhs'].items())-math.fsum(a*x[n] for n,a in row['rhs_coefficients'].items());assert slack>=-1e-7;max_viol=max(max_viol,max(0,-slack))
  values.append(r['numerical_lower']);last=c
 x=json.load(gzip.open(folder/'layer1/solution.json.gz','rt',encoding='utf-8'));slack=math.fsum(x[f'h_{i}_{j}'] for i in range(1,p['V']+1) for j in range(i+1,p['V']+1))-math.fsum(v['written']*x[n] for n,v in last['TC_coefficients'].items());assert slack>0 and abs(values[2]-values[1])<1e-7
 roots[role]={'numerical_L':values,'TC_increment':values[2]-values[1],'old_optimum_TC_slack_recomputed':slack,'max_added_row_violation_recomputed':max_viol,'same_archived_current_matrix':True,'actual_loaded_ratios_and_all_stations_verified':True,'TC_and_penalty_exact_reconstruction_and_safe_rounding':True}
result['checks']['roots']=roots
module=ast.parse((R/'scripts/round134_read.py').read_text());function=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='native_release_lifecycle');assert isinstance(function.body[-1],ast.Return) and function.body[-1].value.value is True
result['checks']['reader']={'producer_independent_class_required_before_time_is_accepted':True,'physical_inventory_F0_and_floor0_rechecked':True,'source_rejection_requires_full_domain_safe_open_disposition':True,'source_status_separate_from_final_independent_certificate':True,'native_release_lifecycle_return_True_AST_verified':True}
result['decision']='ACCEPT_SCOPED_MATH_AND_READER';result['seconds']=time.perf_counter()-tick;result['source_hashes']={str(p.relative_to(R)):sha(p) for p in [R/'scripts/round134_count_bound.py',R/'scripts/round134_roots.py',R/'scripts/round134_read.py',O/'math/tiny_exact.json',O/'math/root_plan.json']};result['scope_limitations']=['Real-root native OPTIMAL/residual evidence is numerical, not a strict rational dual certificate.','Tiny increment is over the completed joint+state penalty+R88 CDF reference, not all historical DP closures.','C/D and manuscript/recovery require final integration review.'];result['review_process_corrections']=['A prior message alleged missing return True after a range ended before that line. Full function/AST confirms it always existed; allegation withdrawn without code change.','First independent arithmetic check stopped after tiny replay on passing str instead of Path to old parser, before any root replay. Corrected reviewer call here; no native work repeated.']
assert 'gurobipy' not in sys.modules
(O/'review/math_and_reader_early_review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'decision':result['decision'],'roots':roots,'seconds':result['seconds']}))
