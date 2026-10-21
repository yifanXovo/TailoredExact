"""Four fixed offline draws through R126/R122/R109/R57; no solver calls."""
from round129_common import *
import copy, dataclasses, math, statistics, csv
import round126_data as prior

source=prior.source
old=prior.old
landscape_math=prior.landscape_math
SOURCES=copy.deepcopy(prior.SOURCES)
VERSION='round129-thin-offline-adapter-v1'
REF=OUT/'inputs'
ROLES=[]
for j,(id,s,v,m,geo,r,stock,q,T,B) in enumerate([
 ('UC-C15-S','CITI',15,2,'compact',1,'shortage',[30,30],3600,600),
 ('UC-B20-B','CABI',20,2,'regional',2,'balanced',[20,40],7200,1200),
 ('UC-C20-U','CITI',20,2,'regional',1,'surplus',[30,30],7200,1200),
 ('UC-B30-S','CABI',30,3,'compact',2,'shortage',[25,25,25],7200,1200)]):
    ROLES.append(dict(j=j,id=id,source=s,V=v,M=m,geometry=geo,replicate=r,inventory=stock,Q_vector=q,
        T_seconds=T,cap_seconds=B,selection_id=f'r129_{id}_{geo}_r{r}',
        pickup_seconds=60,drop_seconds=60,**{'lambda':.15},panel_kind='new_prospective_input'))
PROTECT=dict(j=4,id='PB-C20-B',source='CITI',V=20,M=2,geometry='compact',replicate=1,inventory='balanced',
    Q_vector=[30,30],T_seconds=3600,cap_seconds=900,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},
    input_path='reference/round122_paper_benchmark/PB-C20-B.txt',
    input_sha256='b04a721313ebc18c4a3bc4cd4b9f6b69b74e3fce53897fce9a6cc8c32fc7babd',
    panel_kind='existing_certified_protection_not_new_problem')
ORDERS=[['P','MB','MS2'],['MS2','MB','P'],['MB','MS2','P'],['P','MS2','MB'],
        ['MS2','P','MB'],['MB','P','MS2'],['P','MB','MS2'],['MS2','MB','P'],
        ['MB','MS2','P'],['P','MS2','MB']]
PAIRS=[['MS2','P'],['MS2','MB'],['MB','P']]

def family(s):return f'round129-uniform-pair-support-v1|source={s}|source_sha256='+SOURCES[s]['identity_SHA']
def configure(s):
    old.FAMILY=family(s);landscape_math.VERSION=family(s);landscape_math.SOURCE_SHA=SOURCES[s]['identity_SHA']
    assert old.COORD_DECIMALS==3 and old.WEIGHT_DECIMALS==6
    assert old.GEOGRAPHIC_REGIMES==('compact','regional') and old.REPLICATES==(1,2)

def groups(roles):
    return [dict(number=k+1,name=f'campaign/group{k+1:02d}',role=copy.deepcopy(roles[k//2]),
                 seed=k%2,methods=order,pairs=PAIRS) for k,order in enumerate(ORDERS)]

def freeze():
    identity();assert not REF.exists() and not (OUT/'source_recipe.json').exists()
    deps=['scripts/'+n for n in ['round129_data.py','round126_data.py','round122_data.py','round118_data.py',
        'round109_data.py','generate_citibike443_regional_v1.py']]
    assets=['results/data_generation_citibike_round57/source_station_table.csv',
        'results/unified_exact_round116/source/source_station_table.csv',
        'results/unified_exact_round116/source/snapshot.json','results/unified_exact_round116/source/row_decisions.json',
        'results/unified_exact_round116/source/requests/station_information/01.response',
        'results/unified_exact_round116/projection_contract.json']
    recipe=dict(round=129,UTC=utc(),base=BASE,adapter_version=VERSION,sources=SOURCES,
        families={s:family(s) for s in SOURCES},roles=ROLES,protection_role=PROTECT,
        generation_dependencies={p:sha(ROOT/p) for p in deps},source_asset_bindings={p:sha(ROOT/p) for p in assets},
        selection='Unchanged four original anchors, source-row tie rules and hash order',target_fraction=[.44,.56],
        coordinate_decimals=3,weight_decimals=6,delta='max(V,floor(.12*sum(D)+.5))',
        local_perturbation=dict(balanced=.18,other=.30),total_correction_and_sign_repair='unchanged R126/R122',
        weights='original squared target / maximum, six decimals',depot='original serialized-coordinate centroid',
        distance='Euclidean/1.5; no projection rerun',input_header='explicit fixed Q_vector',
        generated_input_count=0,Optimize=0,H_calls=0,no_difficulty_or_reachability_filter=True,no_redraw=True,
        no_network=True,full_fixed_running_table=groups(ROLES+[PROTECT]))
    write(OUT/'source_recipe.json',recipe)
    manifest=dict(round=129,base=BASE,PE_SHA=E2_SHA,DLL_SHA=DLL_SHA,groups=groups(ROLES+[PROTECT]),
        formal_arms=30,formal_groups=10,typed_pairs=30,new_input_arms=24,protection_arms=6,new_problems=4,
        formal_nominal_seconds=30600,total_outer_limit=39600,qualification_soft=900,qualification_limit=1800,
        management_reference=600,planned_maximum=33000,seed_H=20260626,Threads=1,MIP_threads=1,affinity_mask=4,
        shutdown_reserve=30,native_offset=6,hard_stop_offset=2,Presolve=-1,MIPFocus=0,Cuts=-1,
        MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6,
        sole_paper_method='frozen full M-B / GI-TBC',serial=True,no_information_shared_between_arms=True,
        no_tuning_or_extra_experiments=True,no_performance_retry=True,
        direction='strict unrounded certified producer time; one-sided certification; both open UNDETERMINED; unqualified UNEVALUABLE',
        research_material_gain='T_MB-T_MS2 >= max(10,0.10*T_MB), both certified; or MS2 only certified',
        research_material_cost='slower-faster >= max(10,0.10*faster), both certified',
        candidate_conditions={
          '1':'At each Seed MS2 new-input certificates >= MB; both-Seed-certified new problems >= MB',
          '2':'At each Seed P-certified/method-open new-input count for MS2 <= MB',
          '3':'Every protected MB certificate retained by MS2; reject if both Seeds both certify and MS2 loses >= max(30,.25*T_MB) at both',
          '4':'One new input exposes actual triple deletion at both Seeds and supplies MS2-only certification or material certified gain at both',
          '5':'One new input supplies direct MS2/P certification Win at both Seeds'},
        decision_priority=['PROOF_OR_IDENTITY_ISSUE_REQUIRES_DECISION','necessary missing evidence: PARTIAL',
            'conditions1-3 fail: RETAIN_FULL_MB_SIMPLIFICATION_NOT_CONFIRMED',
            'conditions4-5 missing: INSUFFICIENT_NEW_DIRECT_SUPPORT_RETAIN_MB',
            'all five: RECOMMEND_UNIFORM_MS2_AS_PAPER_CANDIDATE'],
        external_failure_recovery='At most one preregistered same-role/same-Seed COMPLETE THREE-METHOD group, only no qualified production and budget covers all obligations; retain failed original',
        support_candidates=[1120,2660,2660,13485,2660],expected_triple_deletions=[910,2280,2280,12180,2280],
        support_budget=50000,seed_repeats_not_new_problems=True,protection_excluded_from_new_signal_denominator=True)
    write(OUT/'experiment_manifest.json',manifest)
    (OUT/'RESUME.md').write_text('Recipe and complete 30-arm table frozen. Commit before once-only generation. No formal producer started.\n',encoding='utf-8')
    print('FROZEN: four inputs, one protection role, ten serial groups, thirty arms/comparisons; commit before generation')

def fixture(stations):
    p=read(ROOT/'results/unified_exact_round126/input_manifest.json')['roles'][0]
    prior.configure(p['source']);ss=stations[p['source']]
    s=old.build_selection(ss,p['V'],p['geometry'],p['replicate'])
    s.update(selection_id=p['selection_id'])
    v=landscape_math.landscape(s,p['inventory'],ss);landscape_math.assert_equivalent(s,p['inventory'],ss,v)
    lines=old.instance_text(v,p['M'],p['Q_vector'][0]).splitlines();lines[0]=f"{p['V']} {p['M']} {json.dumps(p['Q_vector'])}"
    actual='\n'.join(lines).rstrip()+'\n'
    assert actual.encode()==(ROOT/p['input_path']).read_bytes()
    write(OUT/'qualification/adapter_fixture.json',dict(id=p['id'],input_SHA=sha(ROOT/p['input_path']),
        regenerated_same_bytes=True,Optimize=0,H_calls=0,scope='one original R126 small fixture, original family; no formal input screened'))

def generate():
    tick=time.perf_counter();identity();r=read(OUT/'source_recipe.json');assert not REF.exists()
    for n,h in dict(r['generation_dependencies'],**r['source_asset_bindings']).items():assert sha(ROOT/n)==h
    commit=git('rev-parse','HEAD').decode().strip()
    for n in ['scripts/round129_data.py','results/unified_exact_round129/source_recipe.json','results/unified_exact_round129/experiment_manifest.json']:
        assert git('show',commit+':'+n).replace(b'\r\n',b'\n')==(ROOT/n).read_bytes().replace(b'\r\n',b'\n'),'commit before generation'
    stations=source.load_sources();fixture(stations);REF.mkdir(parents=True,exist_ok=False);roles=[];positive=[]
    for p0 in r['roles']:
        p=copy.deepcopy(p0);configure(p['source']);ss=stations[p['source']]
        s=old.build_selection(ss,p['V'],p['geometry'],p['replicate'])
        s.update(schema='round129-geographic-selection-v1',selection_id=p['selection_id'],generator_version=VERSION)
        v=landscape_math.landscape(s,p['inventory'],ss);landscape_math.assert_equivalent(s,p['inventory'],ss,v)
        assert s['dataset_family']==v['dataset_family']==family(p['source'])
        assert v['seed_derivation_material']==f"{family(p['source'])}|inventory|{p['selection_id']}|{p['inventory']}"
        v.update(schema='round129-station-landscape-v1',generator_version=VERSION,source_hashes=SOURCES[p['source']])
        lines=old.instance_text(v,p['M'],p['Q_vector'][0]).splitlines();lines[0]=f"{p['V']} {p['M']} {json.dumps(p['Q_vector'])}"
        path=REF/(p['id']+'.txt')
        with path.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines).rstrip()+'\n')
        parsed=old.parse_instance_mirror(path)
        assert (parsed['V'],parsed['M'],parsed['Q'])==(p['V'],p['M'],p['Q_vector'])
        assert len(set(s['selected_source_station_row_indices']))==p['V']
        assert len(parsed['initial'])==p['V']+1 and parsed['weights'][0]==0
        assert all(0<=b<=c and 0<d<=c for b,c,d in zip(v['initial'],v['capacities'],v['target']))
        assert all(w>0 for w in v['weights']) and max(v['weights'])==1
        by={q.source_row_index:q for q in ss}
        expected=[round(statistics.fmean(getattr(by[i],axis) for i in s['selected_source_station_row_indices']),3) for axis in ['x','y']]
        assert v['depot']['coordinate_utm18n_meters']==expected
        for suffix,obj in [('selection',s),('landscape',v),('parsed',parsed),('source_mapping',
            [dict(local_station_index=j,source=p['source'],**dataclasses.asdict(by[i]),source_identity_SHA=SOURCES[p['source']]['identity_SHA'])
             for j,i in enumerate(s['selected_source_station_row_indices'],1)])]:write(REF/(p['id']+'_'+suffix+'.json'),obj)
        p.update(input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),input_bytes=path.stat().st_size,
            selection_path=(REF/(p['id']+'_selection.json')).relative_to(ROOT).as_posix(),landscape_path=(REF/(p['id']+'_landscape.json')).relative_to(ROOT).as_posix(),
            source_identity_SHA=SOURCES[p['source']]['identity_SHA'],total_initial=sum(v['initial']),total_target=sum(v['target']),total_capacity=sum(v['capacities']),
            sum_weights=sum(v['weights']))
        positive.append(prior.positivity(parsed,p));roles.append(p)
    protect=copy.deepcopy(PROTECT);assert sha(ROOT/protect['input_path'])==protect['input_sha256'];protect['instance_path']=protect['input_path']
    parsed=old.parse_instance_mirror(ROOT/protect['input_path']);assert (parsed['V'],parsed['M'],parsed['Q'])==(20,2,[30,30])
    write(OUT/'input_manifest.json',dict(new_roles=roles,protection_role=protect,roles=roles+[protect],sources=SOURCES,
        families=r['families'],recipe_commit_before_generation=commit,source_recipe_SHA=sha(OUT/'source_recipe.json'),generated_once=True,
        new_problem_denominator=4,protection_not_new=True,formal_arms=30,formal_pairs=30,nonIID_nonfactorial_not_new_cities=True))
    overlap(roles)
    write(OUT/'shortage_positive_objective.json',dict(proof='F>=sum_i(lambda*w_i/D_i)*|Y_i-D_i|>=min_i(lambda*w_i/D_i)*(sumD-sumb)>0',
        premises='service stations only; empty departure, nonnegative loaded return, positive lambda and weights',roles=positive,
        not_injected_into_any_model_Start_or_formal_L=True))
    write(OUT/'generation_receipt.json',dict(UTC=utc(),recipe_commit=commit,inputs=4,Optimize=0,H_calls=0,LP_calls=0,MIP_calls=0,
        no_performance_screening=True,no_redraw=True,seconds=time.perf_counter()-tick))
    print(json.dumps([{k:p[k] for k in ['id','input_sha256','total_initial','total_target']} for p in roles]))

def overlap(current):
    history=[];scope=[];all_hashes={}
    for rn in [122,126,127,128]:
        root=WORK/f'worktrees/round{rn}';mp=root/f'results/unified_exact_round{rn}/input_manifest.json';m=read(mp);seen=set()
        for key in ['roles','new_roles','tiny_roles','main_roles','core_roles','training_roles']:
            for p in m.get(key,[]):
                tok=(p.get('id'),p.get('input_sha256'))
                if tok in seen:continue
                seen.add(tok)
                if p.get('input_sha256'):all_hashes.setdefault(p['input_sha256'],[]).append(dict(round=rn,id=p['id']))
                sp=p.get('selection_path')
                if not sp:continue
                path=root/sp
                if not path.is_file():path=ROOT/sp
                if path.is_file():history.append(dict(round=rn,id=p['id'],source=p['source'],V=p['V'],input_SHA=p['input_sha256'],
                    indices=set(read(path)['selected_source_station_row_indices']),selection_SHA=sha(path)))
        scope.append(dict(round=rn,manifest_SHA=sha(mp),unique_manifest_roles=len(seen),available_small_selections=sum(q['round']==rn for q in history)))
    rows=[]
    for p in current:
        if p['input_sha256'] in all_hashes:
            write(OUT/'DATA_BLOCKED.json',dict(id=p['id'],reason='complete duplicate input',prior=all_hashes[p['input_sha256']],no_redraw=True))
            raise RuntimeError('DATA_BLOCKED complete duplicate; no redraw')
        chosen=set(read(ROOT/p['selection_path'])['selected_source_station_row_indices'])
        for q in history:
            if q['source']==p['source']:rows.append(dict(id=p['id'],source=p['source'],new_V=p['V'],previous_round=q['round'],previous_id=q['id'],
                previous_V=q['V'],station_overlap=len(chosen&q['indices']),complete_input_duplicate=False,previous_selection_SHA=q['selection_SHA']))
    for k,p in enumerate(current):
        a=set(read(ROOT/p['selection_path'])['selected_source_station_row_indices'])
        for q in current[:k]:
            assert p['input_sha256']!=q['input_sha256']
            if p['source']==q['source']:
                b=set(read(ROOT/q['selection_path'])['selected_source_station_row_indices'])
                rows.append(dict(id=p['id'],source=p['source'],new_V=p['V'],previous_round=129,previous_id=q['id'],previous_V=q['V'],
                    station_overlap=len(a&b),complete_input_duplicate=False,previous_selection_SHA=sha(ROOT/q['selection_path'])))
    with (OUT/'station_overlap.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
    write(OUT/'station_overlap_scope.json',dict(scope=scope,comparisons=len(rows),no_large_history_carrier_recovered=True,Optimize=0,
        note='R128 known roles inherit R126/R122 selections; duplicate historical roles remain labelled by source round',all_complete_duplicates=False))

if __name__=='__main__':{'freeze':freeze,'generate':generate}[sys.argv[1]]()
