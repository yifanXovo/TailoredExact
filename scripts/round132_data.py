"""Prospective D recipe: freeze before acquisition/generation; no H/Optimize."""
from round132_common import *
import collections, copy, csv, dataclasses, math, statistics, urllib.request
import round122_data as source
import round109_data as landscape_math
import generate_citibike443_regional_v1 as old

SPECS=[('15-S',15,'shortage','compact',[30,30],3600,600),
 ('15-B',15,'balanced','regional',[30,30],5400,600),
 ('20-S',20,'shortage','compact',[30,30],5400,1200),
 ('20-U',20,'surplus','compact',[30,30],7200,1200),
 ('35-B',35,'balanced','compact',[25,25,25],7200,2400),
 ('35-U',35,'surplus','regional',[20,25,30],10800,2400)]
DIVVY='https://gbfs.divvybikes.com/gbfs/2.3/gbfs.json'
LICENSE='https://divvybikes.com/data-license-agreement'
VERSION='round132-frozen-s2-prospective-v2'

def roles():
    rows=[]
    for layer in ['K','X']:
        for j,(suffix,V,stock,geo,Q,T,cap) in enumerate(SPECS):
            s=('CITI' if j%2==0 else 'CABI') if layer=='K' else 'DIVVY'
            rows.append(dict(id=f'{layer}-{suffix}',layer=layer,source=s,V=V,M=len(Q),inventory=stock,
                geometry=geo,replicate=1+j%2,Q_vector=Q,T_seconds=T,cap_seconds=cap,
                pickup_seconds=60,drop_seconds=60,**{'lambda':.15},
                selection_id=f'r132_{layer}_{suffix}_{s}',panel_kind='prospective_frozen_S2_validation'))
    return rows

def groups(rr):
    out=[]
    for p in rr:
        for seed in [0,1]:
            methods=['P','S2','PS'] if p['id'].split('-',1)[1] in ['15-S','20-U','35-B'] else ['P','S2']
            # Opposite order per Seed; alternate first method across roles.
            if (len(out)//2+seed)%2:methods=list(reversed(methods))
            out.append(dict(number=len(out)+1,name=f'campaign/D_group{len(out)+1:02d}',
                role=copy.deepcopy(p),seed=seed,repeat=1,methods=methods,
                pairs=[['S2','P']]+([['S2','PS'],['PS','P']] if 'PS' in methods else [])))
    assert sum(len(g['methods']) for g in out)==60
    assert sum(len(g['methods'])*g['role']['cap_seconds'] for g in out)==84000
    return out

def freeze():
    frozen_identity();assert not (OUT/'source_recipe.json').exists()
    rr=roles()
    recipe=dict(UTC=utc(),version=VERSION,roles=rr,source_assignment='fixed alternating K:CITI/CABI by table row; X:DIVVY Chicago',
        source_urls=dict(DIVVY=DIVVY,official_reference='https://divvybikes.com/system-data',license=LICENSE),
        acquisition='one official GBFS discovery and station_information snapshot; 60s each, <=3 same-endpoint transport retries; no performance-dependent source replacement',
        source_failure='If acquisition/qualification cannot succeed, freeze a declared constructed-source replacement before any H/LP/MIP; no silent substitution',
        source_qualification='unique UTF-8 station ID; finite valid lat/lon; integer 0<capacity<100; nonvirtual; duplicate IDs with identical records deduplicate, conflicting records exclude',
        projection=dict(K='original serialized UTM18N metres',X='EPSG:4326 to EPSG:32616 (UTM16N), always_xy=True, forward/inverse residual <=1e-8 degrees; round metres to 3 decimals'),
        missing_fields='exclude missing/nonfinite ID/coordinate/capacity; never impute public capacity',
        selection='Process roles in fixed table order. Exclude stations used by earlier new roles of the same source. Prefer stations absent from every accessible tracked historical small selection. If fewer than required candidate pool, include whole exposure-count tiers in ascending order until at least min(remaining, 2V) for regional or V for compact. Apply unchanged R57 4-anchor/compact-nearest/regional-farthest-first and source-row tie rules within that pool.',
        historical_scope='BASE tracked *_selection.json small records; source identified from dataset_family/selection_id and exact CITI/CABI identities; no raw campaign recovery. Report unresolved identities.',
        seed='SHA256-derived original stable_seed; material round132-frozen-s2-prospective-v2|source=<source>|source_sha256=<snapshot SHA>; fixed role selection_id',
        inventory='Unchanged R109/R122 target .44+.12*hash; delta=max(V,floor(.12*sumD+.5)); local .18 balanced/.30 otherwise; unchanged total correction and sign repair',
        weights='original squared target / maximum with .1 floor, six decimals; not sum-normalized',
        fields=dict(capacity='public source snapshot',coordinates='public source transformed/rounded',target='synthetic',initial='synthetic',weights='synthetic',depot='synthetic centroid'),
        lambda_value=.15,handling_seconds=[60,60],H_seed=20260626,Threads=1,MIPThreads=1,
        distance='Euclidean serialized metre coordinates /1.5 m/s, unchanged parser',
        full_run_table=groups(rr),Optimize=0,H=0,no_redraw=True,no_difficulty_filter=True)
    write(OUT/'source_recipe.json',recipe)
    write(OUT/'experiment_plan.json',dict(round=132,base=BASE,D=groups(rr),D_arms=60,D_cap_sum=84000,
        C=dict(roles=['SC-C15-B','SC-B20-S','UC-C20-U','PB-C35-U'],caps=[600,1200,1200,2400],Seeds=[0,1],
               methods=['S2R','S2R-GEOM','S2R-SP'],max_arms=24,cap_sum=32400,conditional_on_B_and_matrix_Start_bridge=True),
        E=dict(required='bounded exact complete tiny comparison, 2 vehicles, 4-6 stations, 0/1/2 domains',limit=10800,
               further_steps='only after proved valid new structural difference and full B_ref extension'),
        C3=dict(optional=True,max_new_arms=4,cap_sum=4800,choose_at_most_one_after_C2=True),
        limits=LIMITS,total_G1_limit=144000,postproduction_non_native_cost_separate=True,
        direction='unrounded certification time or one-sided certificate; both open UNDETERMINED; invalid UNEVALUABLE',
        denominators='12 problems, 24 S2/P repeated observations; 6 problems, 12 S2/PS and 12 PS/P repeated observations; C separate shared baselines',
        serial_native=True,no_cross_arm_information=True,prior_C_and_D_inputs_not_pooled=True))
    print('Recipe and all 60 D positions fixed before acquisition/generation/H/LP/MIP.')

def request(url,destination):
    assert not destination.exists()
    req=urllib.request.Request(url,headers={'User-Agent':'TailoredExact-research/132'})
    attempts=[]
    for attempt in range(1,4):
        try:
            tick=time.perf_counter()
            with urllib.request.urlopen(req,timeout=60) as r:data=r.read();final=r.url;status=r.status
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
            write(destination.with_suffix('.receipt.json'),dict(url=url,final_url=final,status=status,UTC=utc(),SHA=sha(destination),bytes=len(data),attempts=attempts,seconds=time.perf_counter()-tick))
            return json.loads(data)
        except Exception as e:
            attempts.append(dict(attempt=attempt,error=type(e).__name__,message=str(e)))
    write(OUT/'source/acquisition_failure.json',dict(url=url,attempts=attempts));raise RuntimeError('Public source unavailable; no H or formal solve authorized before declared replacement')

def acquire():
    assert (OUT/'source_recipe.json').exists();d=OUT/'source/DIVVY'
    feed=request(DIVVY,d/'gbfs.json')
    url=next(q['url'] for q in feed['data']['en']['feeds'] if q['name']=='station_information')
    data=request(url,d/'station_information.json')
    from pyproj import Transformer,__version__
    forward=Transformer.from_crs(4326,32616,always_xy=True);inverse=Transformer.from_crs(32616,4326,always_xy=True)
    by=collections.defaultdict(list)
    for j,q in enumerate(data['data']['stations']):by[str(q.get('station_id',''))].append((j,q))
    accepted=[];decisions=[]
    for sid,items in sorted(by.items(),key=lambda x:x[0].encode()):
        q=items[0][1];reason=None
        try:
            lat,lon=float(q['lat']),float(q['lon']);c=q['capacity']
            assert sid and isinstance(c,int) and not isinstance(c,bool) and 0<c<100
            assert math.isfinite(lat) and math.isfinite(lon) and 0<lat<84 and -90<=lon<=-84
            assert not q.get('is_virtual_station',False)
            assert all((r.get('lat'),r.get('lon'),r.get('capacity'),r.get('is_virtual_station',False))==(q['lat'],q['lon'],c,q.get('is_virtual_station',False)) for _,r in items)
            x,y=forward.transform(lon,lat);lo,la=inverse.transform(x,y)
            assert max(abs(lo-lon),abs(la-lat))<=1e-8
            accepted.append(dict(source_row_index=len(accepted),station_id=sid,capacity=c,x=round(x,3),y=round(y,3),
                latitude=lat,longitude=lon,original_row_indices=[j for j,_ in items],unrounded_x=x,unrounded_y=y,
                inverse_latitude=la,inverse_longitude=lo))
        except (KeyError,AssertionError,TypeError,ValueError):reason='missing/invalid/nonphysical/duplicate-conflicting public field'
        decisions.append(dict(station_id=sid,original_rows=[j for j,_ in items],accepted=reason is None,reason=reason))
    assert len(accepted)>=140
    write(d/'qualified_stations.json',accepted);write(d/'row_decisions.json',decisions)
    write(d/'snapshot.json',dict(UTC=utc(),source='DIVVY Chicago',response_SHA=sha(d/'station_information.json'),
        response_path=(d/'station_information.json').relative_to(ROOT).as_posix(),raw_rows=len(data['data']['stations']),qualified=len(accepted),
        projection='EPSG:4326 -> EPSG:32616 always_xy; metre precision .001',pyproj_version=__version__,
        pipeline=forward.definition,license_url=LICENSE,publication='source material within this noncommercial research study; not a standalone dataset',
        system_name_used_only_for_data_attribution=True))
    print(json.dumps(dict(DIVVY_qualified=len(accepted),SHA=sha(d/'station_information.json'))))

def historical():
    names=git('ls-tree','-r','--name-only',BASE).decode().splitlines();counts=collections.defaultdict(collections.Counter);records=[];seen=set();unresolved=[]
    for n in names:
        if not n.endswith('_selection.json'):continue
        try:q=json.loads(git('show',BASE+':'+n))
        except (ValueError,subprocess.CalledProcessError):continue
        if not isinstance(q,dict):continue
        ids=q.get('selected_source_station_row_indices')
        if not ids:continue
        text=(q.get('dataset_family','')+' '+q.get('selection_id','')).upper()
        s='CABI' if 'CABI' in text else 'CITI' if any(k in text for k in ['CITI','CB443','CB_','SOURCE=CITI']) else None
        if s is None:unresolved.append(n);continue
        key=(s,tuple(ids))
        if key in seen:continue
        seen.add(key);counts[s].update(set(ids));records.append(dict(source=s,path=n,indices=ids,selection_content_SHA=hashlib.sha256(git('show',BASE+':'+n)).hexdigest()))
    write(OUT/'historical_station_scope.json',dict(base=BASE,records=records,unresolved=unresolved,no_raw_recovery=True))
    return counts,records

def generate():
    frozen_identity();assert not (OUT/'input_manifest.json').exists()
    recipe=read(OUT/'source_recipe.json');assert git('show','HEAD:results/unified_exact_round132/source_recipe.json').replace(b'\r\n',b'\n')==(OUT/'source_recipe.json').read_bytes().replace(b'\r\n',b'\n')
    station_sets=source.load_sources()
    with (ROOT/'results/data_generation_citibike_round57/source_station_table.csv').open(encoding='utf-8',newline='') as fh:
        annotations={int(q['source_station_row_index']):q for q in csv.DictReader(fh)}
    station_sets['CITI']=[dataclasses.replace(q,station_id=annotations[q.source_row_index]['station_id'],
        name=annotations[q.source_row_index]['station_name'],latitude=float(annotations[q.source_row_index]['latitude']),
        longitude=float(annotations[q.source_row_index]['longitude'])) for q in station_sets['CITI']]
    station_sets['DIVVY']=[source.cabi.Station(q['source_row_index'],q['station_id'],q['capacity'],q['x'],q['y'],q['latitude'],q['longitude'],tuple(q['original_row_indices'])) for q in read(OUT/'source/DIVVY/qualified_stations.json')]
    hashes={s:v['identity_SHA'] for s,v in source.SOURCES.items()};hashes['DIVVY']=sha(OUT/'source/DIVVY/station_information.json')
    exposure,history=historical();used=collections.defaultdict(set);rr=[];overlap=[]
    for p0 in recipe['roles']:
        p=copy.deepcopy(p0);s=p['source'];ss=station_sets[s]
        remaining=[q for q in ss if 0<q.capacity<100 and q.source_row_index not in used[s]]
        required=min(len(remaining),p['V']*(2 if p['geometry']=='regional' else 1))
        tiers=sorted(set(exposure[s][q.source_row_index] for q in remaining));pool=[]
        for tier in tiers:
            pool.extend(q for q in remaining if exposure[s][q.source_row_index]==tier)
            if len(pool)>=required:break
        pool.sort(key=lambda q:q.source_row_index)
        f=f'{VERSION}|source={s}|source_sha256={hashes[s]}'
        old.FAMILY=f;landscape_math.VERSION=f;landscape_math.SOURCE_SHA=hashes[s]
        sel=old.build_selection(pool,p['V'],p['geometry'],p['replicate']);sel['selection_id']=p['selection_id']
        sel.update(schema='round132-selection-v1',source=s,coordinate_CRS='EPSG:32616' if s=='DIVVY' else 'EPSG:32618',
            historical_exposure_tier=tier,previous_new_stations_excluded=len(used[s]),pool_indices=[q.source_row_index for q in pool])
        v=landscape_math.landscape(sel,p['inventory'],ss);landscape_math.assert_equivalent(sel,p['inventory'],ss,v)
        # Legacy JSON field spelling *_utm18n_meters is retained for the pure
        # writer interface. The explicit CRS above and below governs X.
        v['coordinate_CRS']=sel['coordinate_CRS'];v['source']=s
        lines=old.instance_text(v,p['M'],p['Q_vector'][0]).splitlines();lines[0]=f"{p['V']} {p['M']} {json.dumps(p['Q_vector'])}"
        dest=OUT/'inputs'/(p['id']+'.txt');dest.parent.mkdir(exist_ok=True)
        with dest.open('x',encoding='utf-8',newline='\n') as fh:fh.write('\n'.join(lines).rstrip()+'\n')
        parsed=old.parse_instance_mirror(dest);assert (parsed['V'],parsed['M'],parsed['Q'])==(p['V'],p['M'],p['Q_vector'])
        selected=set(sel['selected_source_station_row_indices']);assert not used[s]&selected;used[s]|=selected
        for suffix,value in [('selection',sel),('landscape',v),('parsed',parsed),('source_mapping',[dataclasses.asdict(q) for q in ss if q.source_row_index in selected])]:write(dest.with_name(p['id']+'_'+suffix+'.json'),value)
        p.update(input_path=dest.relative_to(ROOT).as_posix(),instance_path=dest.relative_to(ROOT).as_posix(),input_sha256=sha(dest),
            selection_path=dest.with_name(p['id']+'_selection.json').relative_to(ROOT).as_posix(),
            landscape_path=dest.with_name(p['id']+'_landscape.json').relative_to(ROOT).as_posix(),
            input_bytes=dest.stat().st_size,source_identity_SHA=hashes[s],total_initial=sum(v['initial']),total_target=sum(v['target']),
            total_capacity=sum(v['capacities']),sum_weights=sum(v['weights']),Omega=sum(v['weights']),rho=.15*sum(v['weights']))
        if p['inventory']=='shortage':assert p['total_initial']<p['total_target'] and min(v['weights'])>0
        for h in history:
            if h['source']==s:overlap.append(dict(id=p['id'],source=s,historical_selection=h['path'],station_overlap=len(selected&set(h['indices']))))
        rr.append(p)
    write(OUT/'input_manifest.json',dict(roles=rr,generated_once=True,recipe_commit=git('rev-parse','HEAD').decode().strip(),source_recipe_SHA=sha(OUT/'source_recipe.json'),
        K='known source and generator, new nonnested disjoint station draws',X='third geographic source only; same synthetic inventory/target/weight mechanism',
        new_problems=12,Seeds_are_repeated_observations=True,within_source_new_station_overlap=0,Optimize=0,H=0))
    write(OUT/'station_overlap.json',dict(comparisons=overlap,scope='accessible tracked small selections; not full historical raw recovery'))
    plan=read(OUT/'experiment_plan.json');plan['D']=groups(rr);write(OUT/'experiment_plan.json',plan)
    print(json.dumps([dict(id=p['id'],SHA=p['input_sha256'],Omega=p['Omega'],rho=p['rho']) for p in rr]))
if __name__=='__main__':{'freeze':freeze,'acquire':acquire,'generate':generate}[sys.argv[1]]()
