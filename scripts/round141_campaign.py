"""One uniform root-count candidate, own-H controls and complete outer clocks."""
from round141_common import *
import copy
import round133_campaign as inherited
from round121_campaign import finish_producer
from round122_prepare import COMMON
from round141_read import verify

def freeze(batch,positions,reason):
    assert not budget()['unclosed']
    target=OUT/f'{batch}_matrix.json';assert not target.exists()
    manifest_path=OUT/'candidate_manifest.json';manifest=inherited._candidate(manifest_path)
    source=read(ROOT/'results/unified_exact_round138/matrix_frozen.json')
    by={g['launch']['id']:g['launch'] for g in source['groups'] if g['launch']['method']=='STOCK'}
    groups=[]
    for i,spec in enumerate(positions,1):
        old=by[spec['role']];l=copy.deepcopy(old);p=l['panel'];seed=spec.get('seed',0)
        mode=spec.get('mode','d1');cap=spec.get('cap',p['cap_seconds']);assert mode in ['d0','d1']
        p.update(gurobi_seed=seed,cap_seconds=cap,round138_stock_rlt=True,round140_counts='tc2',
            round141_count_proof=mode,panel_kind='Round141 own-H count-disjunction exposed research panel')
        camp=OUT/('qualification/runs' if batch=='qualification' else 'campaign_'+batch)/f'{i:03}'
        camp.mkdir(parents=True,exist_ok=False);armid=f'R141_{batch}_{i:03}_{spec["role"]}_S{seed}_{mode.upper()}'
        d=camp/'raw'/armid;command=[v.replace(old['destination'],str(d)) for v in old['command']]
        command[0]=manifest['production_PE']
        for flag,value in [('--gurobi-seed',seed),('--time-limit',cap-6),('--process-wall-time-limit',cap)]:
            command[command.index(flag)+1]=str(value)
        assert '--round138-stock-rlt' in command
        command+=['--round140-counts','tc2','--round141-count-proof',mode]
        l.update(number=1,group_number=i,global_launch_number=i,method=mode.upper(),proof_mode=mode,seed=seed,
            binary_layer='R141',version='candidate',panel=p,panel_kind=p['panel_kind'],destination=str(d),
            cap_seconds=cap,hard_stop_seconds=cap-2,command=command,arm_id=armid,stage=batch,counts='tc2',stock=True)
        identity=dict(schema='round141-own-complete-lifecycle-v1',
            prereg=dict(common=dict(COMMON,gurobi_seed=seed),candidate_binary=manifest['production_PE'],candidate_binary_sha256=manifest['production_PE_SHA']),
            prereg_sha256=hashlib.sha256(json.dumps(dict(batch=batch,positions=positions,reason=reason),sort_keys=True).encode()).hexdigest(),
            runner_sha256=sha(__file__),source_hashes=manifest['source_hashes'],candidate_binary_sha256=manifest['production_PE_SHA'],
            dll_sha256=DLL_SHA,measured_source_commit=manifest['source_commit'],delivery_base_commit=BASE,
            launches=[l],candidate_manifest_path=str(manifest_path),candidate_manifest_SHA=sha(manifest_path),stage=batch,no_cross_arm_information=True)
        write(camp/'identity.json',identity)
        groups.append(dict(position=i,stage=batch,group=camp.relative_to(OUT).as_posix(),arm_id=armid,identity_SHA=sha(camp/'identity.json'),launch=l))
    write(target,dict(UTC=utc(),batch=batch,groups=groups,selection_reason=reason,candidate_manifest_SHA=sha(manifest_path),
        helpers=inherited.helper_bindings(),new_nominal_caps=sum(g['launch']['cap_seconds'] for g in groups),
        Seed_default=0,H_seed=20260626,serial=True,threads=1,affinity_mask=4,all_own_H=True))

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
    else:assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(),'Never rerun an unsealed producer'
    started=time.perf_counter()
    try:value=verify(launch,identity)
    finally:write(OUT/'cost_segments'/label/'verification.json',dict(native_Optimize=0,seconds=time.perf_counter()-started,kind='pure postproduction audit'))
    write(OUT/'runtime_status.json',dict(UTC=utc(),batch=batch,position=position,arm_id=launch['arm_id'],
        certificate=value['arm']['certificate'],U=value['arm']['U'],L=value['arm']['L']))
    print(json.dumps(value['arm']),flush=True)

def run(batch,stop_after=None):
    for group in admission(batch)['groups']:
        if stop_after is not None and group['position']>stop_after:break
        if (Path(group['launch']['destination'])/'verification_closeout.json').exists():continue
        label=f'{batch}_{group["position"]:03}';assert not (OUT/'fees'/label).exists(),'Inspect existing fee and sealed producer; no automatic repeat'
        write(OUT/'active_position.json',dict(UTC=utc(),batch=batch,position=group['position'],fee_label=label,arm_id=group['arm_id']))
        assert metered(label,'diagnostic' if batch.startswith('qualification') else 'native',
            [PYTHON,ROOT/'scripts/round141_campaign.py','arm',batch,group['position'],label],group['launch']['cap_seconds'],group['launch']['cap_seconds']+1800)==0
    write(OUT/f'{batch}_run_return.json',dict(UTC=utc(),budget=budget()))

def qualification():
    freeze('qualification_v6',[dict(role='K-20-S',mode='d1',cap=90),dict(role='K-15-S',mode='d0',cap=90)],
        'Finite own-H/normal-root/count-probe/Native target and terminal qualification after exact writer/Start/source tests; not performance observations')

def pilot():
    freeze('pilot',[dict(role=r) for r in ['K-20-S','K-35-U','K-15-S','R-B35-S-T2']],
        'Uniform max weighted remainder / LP-floor D1: three cover gains and two actual scalar D0-point separations support the four-role finite pilot')
    freeze('control',[dict(role=r,mode='d0') for r in ['K-20-S','K-35-U']],
        'Necessary independent paid D0: identical online selection/count links/two probes; only objective floor becomes common cover')

if __name__=='__main__':
    if sys.argv[1]=='arm':arm(sys.argv[2],int(sys.argv[3]),sys.argv[4])
    elif sys.argv[1]=='run':run(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else None)
    else:globals()[sys.argv[1]]()
