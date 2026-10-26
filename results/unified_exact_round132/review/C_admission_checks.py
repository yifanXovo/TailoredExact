"""Lightweight saved-evidence C review; no native API, build or optimization."""
from pathlib import Path
from fractions import Fraction as F
import collections,csv,hashlib,json,math,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round132'
sys.path.insert(0,str(ROOT/'scripts'))
import round108_reader as core
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csvrows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def check(c,label):
    assert c,label
    global checks;checks+=1
checks=0;tick=time.perf_counter();build=read(OUT/'research_build.json')
binding=read(OUT/'C_execution_binding.json');binding_sha=sha(OUT/'C_execution_binding.json')
plan=read(OUT/'C_experiment_plan.json');argv=read(OUT/'C_argv_freeze.json')
for key,path in [('plan_SHA','C_experiment_plan.json'),('argv_SHA','C_argv_freeze.json'),('research_build_SHA','research_build.json')]:check(binding[key]==sha(OUT/path),key)
check(sha(build['PE'])==build['PE_SHA']==binding['PE_SHA'],'same actual research PE')
check(sha(build['exporter'])==build['exporter_SHA'],'actual exporter')
check(sha(build['DLL'])==build['DLL_SHA']==binding['DLL_SHA'],'same actual DLL')
for r in build['generated_sources'].values():check(sha(r['path'])==r['SHA'],'generated source identity')
check(sha(ROOT/'scripts/round132_build.py')==build['generator_SHA'],'source generator')
check(sha(ROOT/'scripts/Round132Expression.hpp')==build['header_SHA'],'expression implementation')
check(sha(ROOT/'scripts/round132_C.py')==binding['runner_SHA'],'current C runner')
check(build['default']=='off' and build['options']==['off','geom','sp'],'default-off finite options')

native=read(OUT/'qualification/C_native_qualification.json');matrix=read(OUT/'qualification/C_matrix_qualification.json')
check(native['passed'] and matrix['passed'],'both qualification gates')
check(matrix['LP_calls']==12 and matrix['H_calls']==0 and len(matrix['records'])==4,'12 canonical qualification LPs')
check(matrix['research_PE_SHA']==build['PE_SHA'] and matrix['research_exporter_SHA']==build['exporter_SHA'],'qualification binary identity')
check(native['own_H_fleets_and_actions_equal'] and native['default_off_E3_behavioral_and_matrix_bridge'],'own H bridge')
numeric=max(r['actual_matrix_differences']['sp']['max_coefficient_serialization_residual_bound'] for r in matrix['records'])
check(numeric<1e-7,'published FM serialization bounds')
check(read(OUT/'qualification/C_matrix_wording_addendum.json')['original_report_SHA']==sha(OUT/'qualification/C_matrix_qualification.json'),'rounding wording receipt bound')
models={};starts={};startfacts=[]
for r in native['records']:
    camp=OUT/r['name'];identity=read(camp/'identity.json');l=identity['launches'][0];d=Path(l['destination'])
    mpath=d/'external/models/L0_epoch_0_generation_1.lp';check(sha(mpath)==r['matrix_SHA'],'actual qualified root SHA')
    models[r['name'].rsplit('_',1)[-1]]=core.lp_model(mpath)
    ledger=csvrows(d/'external/paper_optimize_ledger.csv')
    check([q['solve_kind'] for q in ledger]==['LP','MIP'] and all(q['leaf_id']=='L0' and q['optimize_return_code']=='0' for q in ledger),'actual full root LP MIP returns')
    close=read(d/'verification_closeout.json');check(close['necessary_verification_complete'] and close['native_proof_qualified'],'closed native qualification evidence')
    receipts=list((d/'external/native_logs').glob('*.round68.start.json'));submitted=[read(p) for p in receipts if read(p)['submitted']]
    check(len(submitted)==1,'one own complete Start')
    st=submitted[0]
    check(all(st[k] for k in ['mapping_complete','rows_valid','objective_valid','readback_valid','submitted']),'Start mapping rows objective readback')
    values=csvrows(d/'external/native_logs/L0_terminal_mip.gurobi.log.round68.start.values.csv')
    starts[r['expression'] if r['name'].endswith('_E3') is False else 'E3']={v['variable']:float(v['value']) for v in values}
    check(all(v['value']==v['readback'] for v in values),'actual Start vector readback')
    startfacts.append(dict(name=r['name'],matrix_SHA=r['matrix_SHA'],checked_rows=st['checked_rows'],maximum_row_violation=st['maximum_row_violation'],Start_objective=st['objective'],status=st['status']))
check(models['E3']==models['off'],'old and new default-off entire matrix equal')
check(starts['E3']==starts['off']==starts['geom'],'same complete Start E3 off geometry')
check(starts['sp']=={n:v for n,v in starts['off'].items() if n!='W_SP'},'same physical Start after W removal')
base=models['off'];geo=models['geom'];sp=models['sp']
check(base['objective']==geo['objective']==sp['objective'],'all objective coefficients preserved')
for name in ['geom','sp']:
    m=models[name];expected=set(base['types'])-({'W_SP'} if name=='sp' else set())
    check(set(m['types'])==expected,'only intended column removal')
    check(all(m['types'][n]==base['types'][n] and m['bounds'][n]==base['bounds'][n] for n in expected),'all retained bounds and types')
a,b=collections.Counter(base['rows']),collections.Counter(geo['rows']);check(not b-a,'geometry adds no rows')
removed=list((a-b).elements());check(len(removed)==330,'geometry deletes 5 rows per S12 pair')
classes=collections.Counter()
for terms,sense,rhs in removed:
    hs=[(n,v) for n,v in terms if n.startswith('h_')];rs=[(n,v) for n,v in terms if n.startswith('r_')]
    check(sense=='<=' and len(terms)==len(hs)+len(rs),'geometry family variables and sense')
    if hs:check(len(hs)==1 and hs[0][1]==11 and len(rs)==12 and rhs==0,'H spread shape');classes['spread']+=1
    elif len(rs)==2:check(sorted(v for n,v in rs)==[-1.,1.] and rhs>0,'fixed centering shape');classes['fixed']+=1
    else:check(len(rs)==12 and rhs==0,'variable-S centering shape');classes['variable']+=1
check(classes=={'spread':66,'fixed':132,'variable':132},'exact geometry row family cardinalities')

lower=[];upper=[];kept=[]
for terms,sense,rhs in base['rows']:
    c=dict(terms)
    if not c.get('W_SP',0):kept.append((terms,sense,rhs));continue
    check(sense!='=','no W equality')
    if sense=='>=':c={n:-v for n,v in c.items()};rhs=-rhs
    q=({n:F.from_float(v) for n,v in c.items()},F.from_float(rhs))
    (lower if c['W_SP']<0 else upper).append(q)
check(len(lower)==2 and len(upper)==3,'four MC and one SP W usages')
wl,wu=base['bounds']['W_SP'];lower.append(({'W_SP':F(-1)},-F.from_float(wl)));upper.append(({'W_SP':F(1)},F.from_float(wu)))
candidate=collections.Counter(sp['rows']);check(not collections.Counter(kept)-candidate,'every W-free row preserved')
actual=list((candidate-collections.Counter(kept)).elements());check(len(actual)==12,'all12 lower upper pairs retained')
errors=[]
for l,lr in lower:
    for u,ur in upper:
        x,y=-l['W_SP'],u['W_SP'];c={n:y*l.get(n,F(0))+x*u.get(n,F(0)) for n in l.keys()|u.keys() if n!='W_SP'};c={n:v for n,v in c.items() if v};rhs=y*lr+x*ur
        candidates=[]
        for j,(terms,sense,rr) in enumerate(actual):
            cc=dict(terms)
            if sense!='<=' or cc.keys()!=c.keys():continue
            err=abs(F.from_float(rr)-rhs)+sum(abs(F.from_float(cc[n])-v)*F.from_float(max(map(abs,base['bounds'][n]))) for n,v in c.items())
            candidates.append((err,j))
        check(bool(candidates),'exact-reference FM coefficient support')
        err,j=min(candidates);actual.pop(j);errors.append(float(err))
check(not actual and max(errors)<1e-7,'complete multiplicity-preserving numerical FM matching')

roles=[('SC-C15-B',600),('SC-B20-S',1200),('UC-C20-U',1200),('PB-C35-U',2400)]
positions=[];caps=0
check(len(plan['groups'])==len(argv['plans'])==8,'8 formal C groups')
for g,i in zip(plan['groups'],argv['plans']):
    check(i==read(OUT/g['name']/'identity.json') and sha(OUT/g['name']/'identity.json')==binding['groups'][g['name']],'C group complete argv binding')
    check([l['expression'] for l in i['launches']]==g['expressions'] and sorted(g['expressions'])==['geom','off','sp'],'one baseline and two separate candidates')
    check((g['role']['id'],g['role']['cap_seconds'])==roles[(g['number']-1)//2] and g['seed']==(g['number']-1)%2,'fixed four roles two Seeds')
    for l in i['launches']:
        command=l['command'];flag=lambda n:command[command.index(n)+1]
        check(command[0]==build['PE'] and flag('--round132-expression')==l['expression'],'same-build actual expression')
        check(command.count('--round132-expression')==command.count('--round127-mode')==1 and flag('--round127-mode')=='s2-root','one legal inclusive-root mode')
        check(flag('--round98-state-service')=='m-binary' and flag('--round90-lp-g-split')=='false' and flag('--algorithm-preset')=='research-round83-vds-equal-net-exchange','same resolved preset')
        check(flag('--time-limit')==str(g['role']['cap_seconds']-6) and flag('--process-wall-time-limit')==str(g['role']['cap_seconds']) and flag('--gurobi-seed')==str(g['seed']),'complete same timing and Seed')
        check(sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256'],'exact historical diagnostic input')
        check(not Path(l['destination']).exists(),'formal C position unexposed')
        positions.append((g['number'],g['role']['id'],g['seed'],l['comparison_method']));caps+=l['cap_seconds']
check(len(positions)==24 and caps==plan['cap_sum']==32400,'24 C arms cap sum')
check(plan['pairs']==[['S2R-GEOM','S2R'],['S2R-SP','S2R']] and plan['comparison_direction']=='candidate / same-build S2R baseline','explicit candidate comparison directions')
check('4 known problems x 2 Seeds = 8 repeated comparisons' in plan['denominators'] and 'not independent trials' in plan['denominators'],'explicit shared-baseline denominators')
check(sha(OUT/'C_execution_binding.json')==binding_sha,'C binding stable throughout review')
result=dict(scope='lightweight separate internal C review of saved qualification and frozen formal positions',C_execution_binding_SHA=binding_sha,checks_passed=checks,formal_arms=24,groups=8,cap_seconds=32400,actual_S12_geometry_rows=dict(classes),actual_S12_projected_rows=12,actual_S12_FM_max_rounding_residual_bound=max(errors),reported_all_fixture_FM_max_bound=numeric,actual_Start_receipts=startfacts,all_formal_positions_unexposed=True,review_Optimize=0,review_H=0,review_compile=0,elapsed_readonly_seconds=time.perf_counter()-tick,strict_rational_serialized_matrix_equivalence_proved=False,external_reproduction=False)
(OUT/'review/C_admission_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='actual_Start_receipts'},indent=2))
