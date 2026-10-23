"""Independent finite read-only D admission checks; never constructs/solves a model."""
from pathlib import Path
import collections, copy, csv, dataclasses, hashlib, json, math, os, subprocess, sys, time
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'results/unified_exact_round132'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT/'scripts'))
sys.path.insert(0, 'E:/codes/ExactEBRP-work/temp/round132/python-deps')
import pyproj
import round132_data as data
import round109_data as landscape
import generate_citibike443_regional_v1 as old

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a): return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT)
def check(condition, label):
    assert condition, label
    counts['checks'] += 1

start = time.perf_counter()
counts = collections.Counter()
recipe=read(OUT/'source_recipe.json'); manifest=read(OUT/'input_manifest.json')
plan=read(OUT/'experiment_plan.json'); freeze=read(OUT/'D_argv_freeze.json'); binding=read(OUT/'D_execution_binding.json')
recipe_commit=manifest['recipe_commit']
check(recipe_commit=='f91df6c3b19d29177e8ec6092efab97e1e19c4e1','recipe commit')
check(git('show',recipe_commit+':results/unified_exact_round132/source_recipe.json').replace(b'\r\n',b'\n')==(OUT/'source_recipe.json').read_bytes().replace(b'\r\n',b'\n'),'committed recipe bytes')
check(manifest['source_recipe_SHA']==sha(OUT/'source_recipe.json'),'recipe binding')
for key,path in [('plan_SHA','experiment_plan.json'),('inputs_SHA','input_manifest.json'),('argv_SHA','D_argv_freeze.json')]:
    check(binding[key]==sha(OUT/path),key)
for path,h in binding['adapters'].items(): check(sha(ROOT/path)==h,'adapter '+path)
asset=data.frozen_identity()
check(asset['PE_SHA']==freeze['PE_SHA'] and asset['DLL_SHA']==freeze['DLL_SHA'],'actual frozen asset identity')

d=OUT/'source/DIVVY'; raw=read(d/'station_information.json')['data']['stations']; qualified=read(d/'qualified_stations.json')
receipt=read(d/'station_information.receipt.json'); snapshot=read(d/'snapshot.json')
check(sha(d/'station_information.json')==receipt['SHA']==snapshot['response_SHA'],'DIVVY snapshot hash')
feed=read(d/'gbfs.json')['data']['en']['feeds']
check(next(q['url'] for q in feed if q['name']=='station_information')==receipt['url'],'official discovery chain')
forward=pyproj.Transformer.from_crs(4326,32616,always_xy=True); inverse=pyproj.Transformer.from_crs(32616,4326,always_xy=True)
by=collections.defaultdict(list)
for j,q in enumerate(raw): by[str(q.get('station_id',''))].append((j,q))
expected_ids=[]
for sid,items in sorted(by.items(),key=lambda x:x[0].encode()):
    q=items[0][1]
    try:
        lat,lon=float(q['lat']),float(q['lon']); c=q['capacity']
        valid=bool(sid) and isinstance(c,int) and not isinstance(c,bool) and 0<c<100
        valid=valid and math.isfinite(lat) and math.isfinite(lon) and 0<lat<84 and -90<=lon<=-84 and not q.get('is_virtual_station',False)
        valid=valid and all((r.get('lat'),r.get('lon'),r.get('capacity'),r.get('is_virtual_station',False))==(q['lat'],q['lon'],c,q.get('is_virtual_station',False)) for _,r in items)
        if valid: expected_ids.append(sid)
    except (KeyError,TypeError,ValueError): pass
check([q['station_id'] for q in qualified]==expected_ids,'all qualified public rows')
max_projection_error=0.
for index,q in enumerate(qualified):
    check(q['source_row_index']==index,'source row index')
    x,y=forward.transform(q['longitude'],q['latitude']); lon,lat=inverse.transform(x,y)
    max_projection_error=max(max_projection_error,abs(lon-q['longitude']),abs(lat-q['latitude']))
    check((q['x'],q['y'])==(round(x,3),round(y,3)),'UTM16N coordinates')
    for original in q['original_row_indices']:
        rr=raw[original]; check((rr['station_id'],rr['capacity'],rr['lat'],rr['lon'])==(q['station_id'],q['capacity'],q['latitude'],q['longitude']),'public row mapping')
check(max_projection_error<=1e-8,'inverse projection residual')

stations=data.source.load_sources()
stations['DIVVY']=[data.source.cabi.Station(q['source_row_index'],q['station_id'],q['capacity'],q['x'],q['y'],q['latitude'],q['longitude'],tuple(q['original_row_indices'])) for q in qualified]
history=read(OUT/'historical_station_scope.json'); exposure=collections.defaultdict(collections.Counter)
check(history['unresolved']==[],'resolved historical source identities')
for h in history['records']:
    b=git('show',data.BASE+':'+h['path']); check(hashlib.sha256(b).hexdigest()==h['selection_content_SHA'],'historical selection binding')
    check(json.loads(b)['selected_source_station_row_indices']==h['indices'],'historical station identity')
    exposure[h['source']].update(set(h['indices']))
used=collections.defaultdict(set); roles=[]; newhash=set(); actual_overlap=[]
for initial,p in zip(recipe['roles'],manifest['roles']):
    check(all(p[k]==v for k,v in initial.items()),'role frozen before generation')
    path=ROOT/p['input_path']; check(sha(path)==p['input_sha256'] and path.stat().st_size==p['input_bytes'],'actual input hash')
    check(p['input_sha256'] not in newhash,'unique new input'); newhash.add(p['input_sha256'])
    s=p['source']; ss=stations[s]; byindex={q.source_row_index:q for q in ss}
    selection=read(ROOT/p['selection_path']); saved=read(ROOT/p['landscape_path']); parsed=old.parse_instance_mirror(path)
    remaining=[q for q in ss if 0<q.capacity<100 and q.source_row_index not in used[s]]
    required=min(len(remaining),p['V']*(2 if p['geometry']=='regional' else 1)); pool=[]
    for tier in sorted({exposure[s][q.source_row_index] for q in remaining}):
        pool.extend(q for q in remaining if exposure[s][q.source_row_index]==tier)
        if len(pool)>=required: break
    pool.sort(key=lambda q:q.source_row_index)
    check(selection['pool_indices']==[q.source_row_index for q in pool] and selection['historical_exposure_tier']==tier,'fixed exposure tiers')
    f=f"{data.VERSION}|source={s}|source_sha256={p['source_identity_SHA']}"
    old.FAMILY=f; landscape.VERSION=f; landscape.SOURCE_SHA=p['source_identity_SHA']
    expected=old.build_selection(pool,p['V'],p['geometry'],p['replicate']); expected['selection_id']=p['selection_id']
    for k,v in expected.items():
        if k!='schema': check(selection[k]==v,'selection reconstruction '+k)
    values=landscape.landscape(selection,p['inventory'],ss); landscape.assert_equivalent(selection,p['inventory'],ss,values)
    values['coordinate_CRS']='EPSG:32616' if s=='DIVVY' else 'EPSG:32618'; values['source']=s
    check(saved==values,'complete inventory/target/weight reconstruction')
    lines=old.instance_text(values,p['M'],p['Q_vector'][0]).splitlines(); lines[0]=f"{p['V']} {p['M']} {json.dumps(p['Q_vector'])}"
    expected_bytes=('\n'.join(lines).rstrip()+'\n').encode(); check(path.read_bytes()==expected_bytes,'all input bytes reproduced')
    selected=selection['selected_source_station_row_indices']; chosen=set(selected)
    check(len(selected)==len(chosen)==p['V'] and not used[s]&chosen,'unique disjoint new stations')
    used[s]|=chosen
    check((parsed['V'],parsed['M'],parsed['Q'])==(p['V'],p['M'],p['Q_vector']),'parsed V M Q')
    for j,i in enumerate(selected,1):
        q=byindex[i]; check((parsed['capacities'][j],tuple(parsed['points'][j]))==(q.capacity,(q.x,q.y)),'source capacity/coordinate mapping')
        check(0<=parsed['initial'][j]<=q.capacity and 0<parsed['target'][j]<=q.capacity and parsed['weights'][j]>0,'station bounds')
    check(sum(parsed['initial'][1:])==p['total_initial'] and sum(parsed['target'][1:])==p['total_target'],'depot excluded totals')
    check(abs(sum(parsed['weights'][1:])-p['Omega'])<1e-12 and abs(p['rho']-.15*p['Omega'])<1e-12,'weights rho')
    if p['inventory']=='shortage':check(p['total_initial']<p['total_target'],'shortage positivity premise')
    for h in history['records']:
        if h['source']==s:actual_overlap.append(dict(id=p['id'],source=s,historical_selection=h['path'],station_overlap=len(chosen&set(h['indices']))))
    ref=OUT/'qualification/references'/p['id']; q=read(ref/'build.json')
    check(q['optimizer_calls']==0 and read(ref/'native_metadata.json')['Optimize']==0 and sha(ref/'original.lp')==q['canonical_sha256'],'zero Optimize reference')
    roles.append(dict(id=p['id'],source=s,V=p['V'],input_SHA=p['input_sha256'],T=p['T_seconds'],Q=p['Q_vector'],cap=p['cap_seconds'],historical_tier=tier,total_initial=p['total_initial'],total_target=p['total_target'],Omega=p['Omega']))
check(actual_overlap==read(OUT/'station_overlap.json')['comparisons'],'all saved historical overlap counts')
check(len(roles)==12 and collections.Counter(p['layer'] for p in manifest['roles'])=={'K':6,'X':6},'12 roles K X')

arm_counts=collections.Counter(); cap_sum=0; positions=[]
check(len(plan['D'])==len(freeze['plans'])==len(binding['groups'])==24,'24 groups')
for g,i in zip(plan['D'],freeze['plans']):
    identity_path=OUT/g['name']/'identity.json'; check(sha(identity_path)==binding['groups'][g['name']],'group binding')
    check(i==read(identity_path),'full argv copy equals actual group')
    check([l['method'] for l in i['launches']]==g['methods'],'frozen order')
    check(i['measured_source_commit']==data.SOURCE and i['candidate_binary_sha256']==asset['PE_SHA'] and i['dll_sha256']==asset['DLL_SHA'],'group production identity')
    for name,h in i['source_hashes'].items():check(sha(ROOT/name)==h,'group source '+name)
    for l in i['launches']:
        command=l['command']; method=l['method']; p=l['panel']; cap=p['cap_seconds']
        flags=[v for v in command if v.startswith('--')];check(len(flags)==len(set(flags)),'no repeated command option')
        def val(flag):return command[command.index(flag)+1]
        check(command[0]==asset['PE'] and val('--input')==p['input_path'],'actual executable and input')
        for flag,value in {'--T':p['T_seconds'],'--lambda':.15,'--pickup-time':60,'--drop-time':60,'--time-limit':cap-6,'--process-wall-time-limit':cap,'--process-shutdown-margin':30,'--threads':1,'--mip-threads':1,'--gurobi-seed':g['seed'],'--gurobi-presolve':-1}.items():check(val(flag)==str(value),flag)
        check(l['seed']==g['seed'] in [0,1] and l['hard_stop_seconds']==cap-2,'Seed hard stop')
        check(not any(v in command for v in ['--round128-mode','--round132-expression','s2-root','--gurobi-hga-start']),'no other mode')
        if method=='P':check(val('--method')=='gurobi' and val('--round127-mode')=='p' and '--plain-baseline' in command and '--round112-ens-start-compact' not in command,'cold P')
        elif method=='PS':check(val('--method')=='gurobi' and '--round112-ens-start-compact' in command and '--round127-mode' not in command and '--plain-baseline' in command,'own H PS compact')
        else:check(method=='S2' and val('--method')=='gcap-frontier' and val('--algorithm-preset')=='research-round83-vds-equal-net-exchange' and val('--round98-state-service')=='m-binary' and val('--round127-mode')=='ms2' and val('--round90-lp-g-split')=='false','frozen S2')
        common=i['prereg']['common']; check(all(common[k]==v for k,v in {'Threads':1}.items()) if 'Threads' in common else common['threads']==1,'common threads')
        check(all(common[k]==v for k,v in {'mip_threads':1,'requested_mip_gap':0,'requested_mip_gap_abs':0,'FeasibilityTol':1e-6,'OptimalityTol':1e-6,'IntFeasTol':1e-5,'affinity_mask':4,'shutdown_margin_seconds':30,'native_limit_offset_seconds':6,'hard_stop_offset_seconds':2}.items()),'numerical contract')
        check(l['configuration']==dict(id='q0',MIPFocus=0,Cuts=-1),'native defaults')
        check(Path(l['destination']).is_relative_to(ROOT) and not Path(l['destination']).exists(),'unexposed output position')
        check(sha(ROOT/p['input_path'])==p['input_sha256'],'arm input bytes')
        arm_counts[method]+=1;cap_sum+=cap;positions.append((g['number'],p['id'],g['seed'],method,cap))
check(arm_counts=={'P':24,'S2':24,'PS':12} and cap_sum==84000,'60 arms cap sum')
for recipe_g,g in zip(recipe['full_run_table'],plan['D']):
    check(recipe_g['methods']==g['methods'] and recipe_g['seed']==g['seed'] and recipe_g['pairs']==g['pairs'],'recipe launch order and pair direction')
check(plan['limits']==dict(C=32400,D=84000,qualification=3600,E=10800,C3=4800,repair=8400),'category limits')
check(sum(plan['limits'].values())==plan['total_G1_limit']==144000,'G1 total')
check(plan['postproduction_non_native_cost_separate'] and plan['no_cross_arm_information'] and plan['serial_native'],'cost information serial contract')
check(not list((OUT/'campaign').glob('D_group*/raw/*/launch.json')),'no formal producer before gate')
result=dict(scope='finite independent internal D admission: source, inputs, argv, original assets, static accounting review',checks_passed=counts['checks'],D_execution_binding_SHA=sha(OUT/'D_execution_binding.json'),recipe_commit=recipe_commit,source_recipe_SHA=sha(OUT/'source_recipe.json'),DIVVY_raw_rows=len(raw),DIVVY_qualified_rows=len(qualified),projection_max_inverse_degrees=max_projection_error,within_source_new_overlap=0,unresolved_historical_sources=0,roles=roles,formal_arms=dict(arm_counts),D_cap_sum=cap_sum,all_formal_positions_unexposed=True,Optimize=0,H=0,compile=0,elapsed_readonly_seconds=time.perf_counter()-start,disclaimer='Finite reconstruction and hashes are not a strict rational model proof or external reproduction.')
(OUT/'review/D_admission_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='roles'},ensure_ascii=False,indent=2))
