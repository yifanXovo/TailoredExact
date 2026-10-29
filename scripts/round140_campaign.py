"""Registered uniform TC/TC2 own-H complete runs, single-threaded and serial."""
from round140_common import *
import copy
import round133_campaign as inherited
from round121_campaign import finish_producer
from round122_prepare import COMMON
from round140_read import verify

def freeze(batch,positions,reason):
    assert not budget()['unclosed']
    target=OUT/f'{batch}_matrix.json';assert not target.exists()
    build=read(OUT/'candidate_build.json')
    for name,digest in build['source_hashes'].items():assert sha(ROOT/name)==digest,name
    manifest_path=OUT/'candidate_manifest.json'
    if not manifest_path.exists():
        write(manifest_path,dict(schema='round140-two-sided-count-v1',source_commit=git('rev-parse','HEAD').decode().strip(),
            base=BASE,source_hashes=build['source_hashes'],production_PE=str(E3),production_PE_SHA=sha(E3),
            research_PE=str(E3),research_PE_SHA=sha(E3),DLL=str(DLL),DLL_SHA=DLL_SHA,
            build_SHA=sha(OUT/'candidate_build.json'),stable_R137_entry_unchanged=True,stock_V2_retained=True))
    manifest=read(manifest_path);assert manifest['production_PE_SHA']==sha(E3)
    old=read(ROOT/'results/unified_exact_round138/matrix_frozen.json')
    by={g['launch']['id']:g['launch'] for g in old['groups'] if g['launch']['method']=='STOCK'}
    groups=[]
    for i,a in enumerate(positions,1):
        source=by[a['role']];l=copy.deepcopy(source);p=l['panel'];seed=a.get('seed',0)
        cap=a.get('cap',p['cap_seconds']);counts=a.get('counts','tc2');stock=a.get('stock',True)
        assert counts in ['tc','tc2']
        p['gurobi_seed']=seed;p['cap_seconds']=cap;p['round138_stock_rlt']=stock
        p['panel_kind']='Round140 exposed research panel / uniform inventory threshold counts';p['round140_counts']=counts
        camp=OUT/('qualification/runs' if batch=='qualification' else 'campaign_'+batch)/f'{i:03}'
        camp.mkdir(parents=True,exist_ok=False)
        method=counts.upper()+('_STOCK' if stock else '')
        armid=f'R140_{batch}_{i:03}_{a["role"]}_S{seed}_{method}';d=camp/'raw'/armid
        command=[v.replace(source['destination'],str(d)) for v in source['command'] if v!='--round138-stock-rlt']
        command[0]=str(E3)
        for flag,value in [('--gurobi-seed',seed),('--time-limit',cap-6),('--process-wall-time-limit',cap)]:command[command.index(flag)+1]=str(value)
        if stock:command+=['--round138-stock-rlt']
        command+=['--round140-counts',counts]
        l.update(number=1,group_number=i,global_launch_number=i,method=method,seed=seed,
            binary_layer='R140',version='candidate',panel=p,panel_kind=p['panel_kind'],destination=str(d),
            cap_seconds=cap,hard_stop_seconds=cap-2,command=command,arm_id=armid,stage=batch,counts=counts,stock=stock)
        identity=dict(schema='round140-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=seed),
            candidate_binary=str(E3),candidate_binary_sha256=sha(E3)),prereg_sha256=None,
            runner_sha256=sha(__file__),source_hashes=manifest['source_hashes'],candidate_binary_sha256=sha(E3),
            dll_sha256=DLL_SHA,measured_source_commit=manifest['source_commit'],delivery_base_commit=BASE,
            launches=[l],candidate_manifest_path=str(manifest_path),candidate_manifest_SHA=sha(manifest_path),stage=batch,
            no_cross_arm_information=True)
        identity['prereg_sha256']=hashlib.sha256(json.dumps(dict(batch=batch,positions=positions,reason=reason),sort_keys=True).encode()).hexdigest()
        write(camp/'identity.json',identity)
        groups.append(dict(position=i,stage=batch,group=camp.relative_to(OUT).as_posix(),arm_id=armid,
            identity_SHA=sha(camp/'identity.json'),launch=l))
    write(target,dict(UTC=utc(),batch=batch,groups=groups,selection_reason=reason,candidate_manifest_SHA=sha(manifest_path),
        helpers=inherited.helper_bindings(),new_nominal_caps=sum(g['launch']['cap_seconds'] for g in groups),
        Seed_default=0,H_seed=20260626,serial=True,threads=1,affinity_mask=4,all_own_H=True,known_adaptive_research_panel=True))
    print(json.dumps(dict(batch=batch,positions=len(groups),nominal_cap=sum(g['launch']['cap_seconds'] for g in groups))))

def admission(batch):
    path=OUT/f'{batch}_matrix.json';m=read(path);gate=read(OUT/'review'/f'{batch}_admission.json')
    assert gate['decision']=='ACCEPT' and gate['matrix_SHA']==sha(path)
    assert m['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    inherited._candidate(OUT/'candidate_manifest.json')
    for name,digest in m['helpers'].items():assert sha(ROOT/name)==digest,name
    return m

def arm(batch,position,label):
    group=admission(batch)['groups'][position-1];camp=OUT/group['group']
    assert sha(camp/'identity.json')==group['identity_SHA']
    identity=read(camp/'identity.json');launch=identity['launches'][0];d=Path(launch['destination'])
    assert not (d/'verification_closeout.json').exists()
    if not d.exists():
        tick,creation=inherited.inherited.process_origin()
        inherited.supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(),'Never repeat an unsealed run'
    started=time.perf_counter()
    try:value=verify(launch,identity)
    finally:write(OUT/'cost_segments'/label/'verification.json',dict(native_Optimize=0,seconds=time.perf_counter()-started,kind='postproduction physical/proof audit'))
    write(OUT/'runtime_status.json',dict(UTC=utc(),batch=batch,position=position,arm_id=launch['arm_id'],counts=launch['counts'],
        certificate=value['arm']['certificate'],U=value['arm']['U'],L=value['arm']['L']))
    print(json.dumps(value['arm']),flush=True)

def run(batch,stop_after=None):
    for group in admission(batch)['groups']:
        if stop_after is not None and group['position']>stop_after:break
        if (Path(group['launch']['destination'])/'verification_closeout.json').exists():continue
        label=f'{batch}_{group["position"]:03}';assert not (OUT/'fees'/label).exists(),'Inspect/resume existing fee; never automatically rerun'
        write(OUT/'active_position.json',dict(UTC=utc(),batch=batch,position=group['position'],arm_id=group['arm_id'],fee_label=label))
        kind='diagnostic' if batch=='qualification' else 'native'
        assert metered(label,kind,[PYTHON,ROOT/'scripts/round140_campaign.py','arm',batch,group['position'],label],
            reservation=group['launch']['cap_seconds'],timeout=group['launch']['cap_seconds']+1800)==0
    write(OUT/f'{batch}_run_return.json',dict(UTC=utc(),stop_after=stop_after,budget=budget()))

def qualification():
    freeze('qualification',[dict(role='K-15-S',counts='tc2',cap=90),dict(role='K-20-S',counts='tc',cap=90)],
        'Targeted actual Native/LP/target/terminal lifecycle qualification, not a performance ranking; own H and Seed0')

def primary():
    freeze('primary',[dict(role=r,counts='tc2') for r in ['K-20-S','R-B35-S-T2','K-15-S','K-35-U','R-X35-S-T2']],
        'D2 one uniform main candidate STK+TC+TC2 after exact qualifications and real same-domain LP gains; default Seed0, five mandatory roles, full caps')
    freeze('incremental',[dict(role=r,counts='tc') for r in ['K-20-S','R-B35-S-T2']],
        'D3 necessary complete STK+TC controls for K20 and RB35-T2; distinct own-H independent methods, no attribution of old TC gains to TC2')

if __name__=='__main__':
    if sys.argv[1]=='arm':arm(sys.argv[2],int(sys.argv[3]),sys.argv[4])
    elif sys.argv[1]=='run':run(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else None)
    else:globals()[sys.argv[1]]()
