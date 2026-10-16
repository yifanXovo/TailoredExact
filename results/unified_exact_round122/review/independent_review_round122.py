"""Independent bounded review. Standard library only; never imports producers.

Input rederivation is in memory and does not create a research input. The only
writes are this reviewer's receipts inside the review directory.
"""
from pathlib import Path
import ast, csv, datetime, hashlib, json, math, statistics, sys, time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'results/unified_exact_round122'
REVIEW = Path(__file__).resolve().parent
CITI_SHA = '9f9aad24e61d661971c24c6f5ec78a69081edf01ffc433563e52a70b2eaca2d0'
CABI_RAW_SHA = 'd4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8'
CABI_TABLE_SHA = 'd982051e5871c575ecdf9df538605401bd98341ae9b3b48112482eff80d42ffa'
FIXED = [
    ('PB-C20-B', 'CITI', 20, 2, 'compact', 1, 'balanced', [30,30], 3600, 900, 'citi_r122_V20_compact_r1'),
    ('PB-B20-S', 'CABI', 20, 2, 'regional', 2, 'shortage', [20,40], 7200, 900, 'cabi_r122_V20_regional_r2'),
    ('PB-C35-U', 'CITI', 35, 3, 'regional', 1, 'surplus', [20,25,30], 10800, 2400, 'citi_r122_V35_regional_r1'),
    ('PB-B35-B', 'CABI', 35, 3, 'compact', 2, 'balanced', [25,25,25], 7200, 2400, 'cabi_r122_V35_compact_r2'),
    ('PB-C50-S', 'CITI', 50, 4, 'compact', 1, 'shortage', [30,30,30,30], 10800, 3600, 'citi_r122_V50_compact_r1'),
    ('PB-B50-U', 'CABI', 50, 4, 'regional', 2, 'surplus', [20,25,35,40], 18000, 3600, 'cabi_r122_V50_regional_r2'),
]
KEYS = ['id','source','V','M','geometry','replicate','inventory','Q_vector','T_seconds','cap_seconds','selection_id']
ORDERS = [
    ['P-GRB','ENS-C','M-B','MB-D1'], ['ENS-C','M-B','MB-D1','P-GRB'],
    ['M-B','MB-D1','P-GRB','ENS-C'], ['MB-D1','P-GRB','ENS-C','M-B'],
    ['MB-D1','M-B','ENS-C','P-GRB'], ['P-GRB','MB-D1','M-B','ENS-C'],
    ['ENS-C','P-GRB','MB-D1','M-B'], ['M-B','ENS-C','P-GRB','MB-D1'],
]

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while block := f.read(1024*1024): h.update(block)
    return h.hexdigest()

def family(source):
    return 'round122-paper-benchmark-v1|source='+source+'|source_sha256='+{'CITI':CITI_SHA,'CABI':CABI_RAW_SHA}[source]

def hash_order(ids, material):
    return sorted(ids, key=lambda i:(hashlib.sha256((material+'|'+str(i)).encode()).digest(),i))

def hash_unit(material):
    return int.from_bytes(hashlib.sha256(material.encode()).digest()[:8],'big')/float((1<<64)-1)

def source_rows():
    citi_path=ROOT/'results/data_generation_citibike_round57/source_station_table.csv'
    assert sha(citi_path)==CITI_SHA and citi_path.stat().st_size==69678
    with citi_path.open(encoding='utf-8',newline='') as f: citi=list(csv.DictReader(f))
    assert len(citi)==443
    assert [int(r['source_station_row_index']) for r in citi]==list(range(443))
    assert sum(0<int(r['capacity'])<100 for r in citi)==442
    cabi_root=ROOT/'results/unified_exact_round116'
    cabi_path=cabi_root/'source/source_station_table.csv'
    assert sha(cabi_path)==CABI_TABLE_SHA
    snap=read(cabi_root/'source/snapshot.json')
    response=ROOT/snap['station_response_path']
    assert sha(response)==snap['station_response_SHA']==CABI_RAW_SHA
    raw=read(response)['data']['stations']
    decisions=read(cabi_root/'source/row_decisions.json')
    area=read(cabi_root/'projection_contract.json')['area_of_use']
    with cabi_path.open(encoding='utf-8',newline='') as f: cabi=list(csv.DictReader(f))
    assert len(cabi)==len(raw)==len(decisions)==865
    assert [r['station_id'] for r in cabi]==sorted((r['station_id'] for r in cabi),key=lambda s:s.encode())
    assert len({r['station_id'] for r in cabi})==865
    for i,r in enumerate(cabi):
        assert int(r['source_row_index'])==i and r['raw_source_SHA']==CABI_RAW_SHA
        lat,lon=float(r['latitude']),float(r['longitude'])
        assert area['west']<=lon<=area['east'] and area['south']<=lat<=area['north']
        for k in ['easting','northing']:
            x=float(r['utm18n_'+k+'_unrounded_m'])
            assert math.isfinite(x) and r['utm18n_'+k+'_m']==f'{round(x,3):.3f}'
        assert abs(float(r['inverse_latitude'])-lat)<1e-10
        assert abs(float(r['inverse_longitude'])-lon)<1e-10
        for j in json.loads(r['original_row_indices']):
            q=raw[j]
            assert q['station_id']==r['station_id'] and q['capacity']==int(r['capacity'])
            assert q['lat']==lat and q['lon']==lon and q.get('is_virtual_station') is not True
            assert decisions[j]['original_row']==q and decisions[j]['qualified_physical_row']
    return {'CITI':citi,'CABI':cabi},dict(CITI_table_SHA=sha(citi_path),CABI_table_SHA=sha(cabi_path),
        CABI_response_SHA=sha(response),CITI_rows=443,CITI_eligible=442,CABI_rows=865)

def distance(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])

def independently_derive(rows,p):
    fam=family(p['source']);n=p['V']
    xy=[(float(r['utm18n_easting_m']),float(r['utm18n_northing_m'])) for r in rows]
    eligible=[i for i,r in enumerate(rows) if 0<int(r['capacity'])<100]
    anchors=[hash_order(eligible,fam+f'|geographic-anchor-set|V={n}')[0]]
    for _ in range(3):
        anchors.append(max((i for i in eligible if i not in anchors),
            key=lambda i:(min(distance(xy[i],xy[a]) for a in anchors),-i)))
    slot=(0 if p['geometry']=='compact' else 2)+p['replicate']-1
    anchor=anchors[slot]
    nearest=sorted(eligible,key=lambda i:(distance(xy[i],xy[anchor]),i))
    if p['geometry']=='compact': chosen=nearest[:n]
    else:
        pool=nearest[:2*n];chosen=[anchor]
        while len(chosen)<n:
            chosen.append(max((i for i in pool if i not in chosen),key=lambda i:(
                min(distance(xy[i],xy[j]) for j in chosen),-distance(xy[i],xy[anchor]),-i)))
    depot=[round(statistics.fmean(xy[i][j] for i in chosen),3) for j in range(2)]
    caps=[int(rows[i]['capacity']) for i in chosen]
    target=[max(1,min(c,math.floor(c*(.44+.12*hash_unit(fam+'|target-profile|'+p['selection_id']+f'|row={i}'))+.5))) for c,i in zip(caps,chosen)]
    delta=max(n,math.floor(.12*sum(target)+.5));regime=p['inventory']
    desired=sum(target) if regime=='balanced' else max(0,sum(target)-delta) if regime=='shortage' else min(sum(caps),sum(target)+delta)
    scale=.18 if regime=='balanced' else .30
    material=fam+'|inventory|'+p['selection_id']+'|'+regime
    order=hash_order(range(n),material);initial=target.copy()
    for rank,i in enumerate(order):
        bump=max(1,math.floor(scale*caps[i]+.5))
        initial[i]=max(0,min(caps[i],target[i]+(bump if rank%2==0 else -bump)))
    before=initial.copy()
    while sum(initial)!=desired:
        step=1 if sum(initial)<desired else -1;progress=False
        for i in order:
            if (step>0 and initial[i]<caps[i]) or (step<0 and initial[i]>0):
                initial[i]+=step;progress=True
                if sum(initial)==desired: break
        assert progress
    corrected=initial.copy()
    def both(): return any(b>d for b,d in zip(initial,target)) and any(b<d for b,d in zip(initial,target))
    repaired=not both()
    if repaired:
        repair=hash_order(range(n),material+'|sign-repair')
        receive=next(i for i in repair if initial[i]<caps[i])
        give=next(i for i in reversed(repair) if initial[i]>0 and i!=receive)
        amount=min(caps[receive]-initial[receive],initial[give],max(1,target[receive]+1-initial[receive],initial[give]-target[give]+1))
        initial[receive]+=amount;initial[give]-=amount
        if not both():
            found=False
            for receive in repair:
                for give in reversed(repair):
                    if receive==give: continue
                    amount=max(1,target[receive]+1-initial[receive],initial[give]-target[give]+1)
                    if initial[receive]+amount<=caps[receive] and initial[give]-amount>=0:
                        initial[receive]+=amount;initial[give]-=amount;found=True;break
                if found: break
            assert found
    assert both() and sum(initial)==desired
    w0=[round(max(.1,(d/max(target))**2),6) for d in target]
    weights=[round(w/max(w0),6) for w in w0]
    minimum=[round(.10+.40*(d/c),4) for d,c in zip(target,caps)]
    parsed=dict(capacities=[100000]+caps,initial=[50000]+initial,target=[0]+target,
        weights=[0.]+weights,min_ratio=[0.]+minimum,points=[tuple(depot)]+[xy[i] for i in chosen])
    return dict(chosen=chosen,anchors=anchors,anchor=anchor,depot=depot,parsed=parsed,
        delta=delta,desired=desired,initial_before=before,initial_corrected=corrected,
        sign_repair_used=repaired,inventory_order=order,inventory_material=material)

def serialize(p,a):
    def iv(name,x): return name+' = ['+', '.join(map(str,x))+']'
    def fv(name,x,d): return name+' = ['+', '.join(f'{v:.{d}f}' for v in x)+']'
    lines=[f"{p['V']} {p['M']} {json.dumps(p['Q_vector'])}",iv('capacities',a['capacities']),
        iv('initial    ',a['initial']),iv('target     ',a['target']),fv('weights    ',a['weights'],6),
        fv('min_ratio  ',a['min_ratio'],4),'points = ['+', '.join(f'({x:.3f}, {y:.3f})' for x,y in a['points'])+']']
    return ('\n'.join(lines)+'\n').encode()

def input_review():
    start=time.perf_counter();source,source_facts=source_rows();m=read(OUT/'input_manifest.json');recipe=read(OUT/'source_recipe.json')
    assert len(m['new_roles'])==6 and len(m['roles'])==8
    assert m['formal_arm_denominator']==32 and m['new_problem_denominator']==6 and m['fixed_input_Seed1_blocks']==2
    assert recipe['generated_input_count']==0 and recipe['formal_arms']==32 and recipe['formal_pairs']==48 and recipe['nominal_seconds']==79200
    assert m['source_recipe_SHA']==sha(OUT/'source_recipe.json')
    history=set(read(ROOT/'results/unified_exact_round116/historical_input_hash_index.json')['SHA_to_paths'])
    for rn in [109,116,118,121]:
        for old in read(ROOT/f'results/unified_exact_round{rn}/input_manifest.json').get('roles',[]):
            if old.get('input_sha256'): history.add(old['input_sha256'])
    results=[];observed_hashes=set()
    for values,p in zip(FIXED,m['new_roles']):
        expected=dict(zip(KEYS,values));assert {k:p[k] for k in KEYS}==expected
        assert p['lambda']==.15 and p['pickup_seconds']==p['drop_seconds']==60 and p['gurobi_seed']==0
        derived=independently_derive(source[p['source']],p)
        path=ROOT/p['input_path'];data=path.read_bytes();expected_bytes=serialize(p,derived['parsed'])
        assert data==expected_bytes,('independent full serialized input mismatch',p['id'])
        assert sha(path)==p['input_sha256'] and len(data)==p['input_bytes']
        assert sha(path) not in history and sha(path) not in observed_hashes
        observed_hashes.add(sha(path))
        saved_parsed=read(path.with_name(p['id']+'_parsed.json'))
        assert (saved_parsed['V'],saved_parsed['M'],saved_parsed['Q'])==(p['V'],p['M'],p['Q_vector'])
        for field in ['capacities','initial','target','weights','min_ratio']:
            assert saved_parsed[field]==derived['parsed'][field],('saved parser mismatch',p['id'],field)
        assert saved_parsed['points']==[list(x) for x in derived['parsed']['points']]
        s=read(ROOT/p['selection_path']);v=read(ROOT/p['landscape_path'])
        assert s['selected_source_station_row_indices']==derived['chosen']
        assert s['anchor_source_station_row_index']==derived['anchor']
        assert s['depot_coordinate_utm18n_meters']==derived['depot'] and s['dataset_family']==family(p['source'])
        assert s['selection_id']==p['selection_id'] and v['dataset_family']==family(p['source'])
        for field in ['capacities','initial','target','weights','min_ratio']:
            assert v[field]==derived['parsed'][field][1:],(p['id'],field)
        trace=v['generation_trace']
        assert trace['desired_total']==derived['desired'] and trace['delta_amount']==derived['delta']
        assert trace['initial_before_total_correction']==derived['initial_before']
        assert trace['initial_after_total_correction']==derived['initial_corrected']
        assert trace['inventory_hash_order']==derived['inventory_order']
        assert v['seed_derivation_material']==derived['inventory_material']
        source_map=read(path.with_name(p['id']+'_source_mapping.json'))
        assert [q['local_station_index'] for q in source_map]==list(range(1,p['V']+1))
        assert [q['source_row_index'] for q in source_map]==derived['chosen']
        assert all(q['source']==p['source'] for q in source_map)
        assert [q['capacity'] for q in source_map]==derived['parsed']['capacities'][1:]
        assert [[q['x'],q['y']] for q in source_map]==[list(x) for x in derived['parsed']['points'][1:]]
        parsed=derived['parsed'];ratios=[b/d for b,d in zip(parsed['initial'][1:],parsed['target'][1:])];S=sum(ratios)
        G=sum(abs(x-y) for j,x in enumerate(ratios) for y in ratios[j+1:])/(len(ratios)*S) if S else 0.
        P=sum(w*abs(r-1) for w,r in zip(parsed['weights'][1:],ratios))
        assert p['total_initial']==sum(parsed['initial'][1:]) and p['total_target']==sum(parsed['target'][1:])
        assert p['sum_weights']==sum(parsed['weights'][1:]) and p['lambda_sum_weights']==.15*p['sum_weights']
        assert abs(p['empty_fleet']['G']-G)<1e-14 and abs(p['empty_fleet']['lambda_P']-.15*P)<1e-14
        results.append(dict(id=p['id'],source=p['source'],input_SHA=sha(path),independent_serialized_bytes_equal=True,
            chosen_source_rows=derived['chosen'],anchors=derived['anchors'],sign_repair_used=derived['sign_repair_used'],
            sum_weights=p['sum_weights'],lambda_sum_weights=p['lambda_sum_weights'],empty_G=G,empty_lambda_P=.15*P))
    for j,(p,order) in enumerate(zip(m['roles'],ORDERS),1):
        base=m['new_roles'][j-1 if j<=6 else 3 if j==7 else 4]
        assert p['id']==base['id'] and p['input_sha256']==base['input_sha256'] and p['method_order']==order
        assert p['gurobi_seed']==int(j>6)
    assert sum(len(p['method_order'])*p['cap_seconds'] for p in m['roles'])==79200
    return dict(decision='ACCEPT_INPUT_REDERIVATION_ONLY',reviewer='independent delegated executor',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),script_SHA=sha(__file__),
        input_manifest_SHA=sha(OUT/'input_manifest.json'),recipe_SHA=sha(OUT/'source_recipe.json'),
        source_checks=source_facts,roles=results,groups=8,arms=32,pairs=48,
        distinct_new_problem_count=6,Seed1_blocks=2,native_starts=0,Optimize=0,compiles=0,Git=0,
        actual_exact_historical_SHA_duplicates=False,
        production_helpers_imported=False,research_inputs_written=0,seconds=time.perf_counter()-start,
        limitation='This receipt checks sources, prescribed input mathematics/bytes and group table only; performance admission remains pending.')

def save_receipt(name,value):
    path=REVIEW/name
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(path=str(path),SHA=sha(path),decision=value['decision'],seconds=value['seconds'])))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]=='inputs'
    save_receipt('independent_inputs_01.json',input_review())
