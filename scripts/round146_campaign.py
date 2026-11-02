"""One uniform STOCK+GD candidate; serial same-PE full-own-H comparisons."""
import copy
import round133_campaign as inherited
from round121_campaign import finish_producer
from round122_prepare import COMMON
from round146_read import verify
from round146_common import *
configure()
def freeze(batch,positions,reason):
    configure();assert not budget()['unclosed'];target=OUT/f'{batch}_matrix.json';assert not target.exists()
    manifest_path=OUT/'candidate_manifest.json';manifest=inherited._candidate(manifest_path)
    source=read(ROOT/'results/unified_exact_round137/matrix_frozen.json')
    by={g['launch']['id']:g['launch'] for g in source['groups'] if g['launch']['method']=='S2' and g['launch']['seed']==0};groups=[]
    for i,spec in enumerate(positions,1):
        old=by[spec['role']];l=copy.deepcopy(old);p=l['panel'];seed=spec.get('seed',0);method=spec['method'];assert method in ('BASE','STOCK','STOCK_GD')
        cap=spec.get('cap',p['cap_seconds']);p.update(gurobi_seed=seed,cap_seconds=cap,round146_method=method,
            round138_stock_rlt=method!='BASE',panel_kind='Round146 direct GD rows; complete own-H and same-PE control')
        camp=OUT/('qualification/runs' if batch.startswith('qualification') else 'campaign_'+batch)/f'{i:03}';camp.mkdir(parents=True,exist_ok=False)
        armid=f'R146_{batch}_{i:03}_{spec["role"]}_S{seed}_{method}';d=camp/'raw'/armid
        command=[v.replace(old['destination'],str(d)) for v in old['command']];command[0]=manifest['production_PE']
        for flag,v in [('--gurobi-seed',seed),('--time-limit',cap-6),('--process-wall-time-limit',cap)]:command[command.index(flag)+1]=str(v)
        if method!='BASE':command+=['--round138-stock-rlt']
        command+=['--round146-gd','on' if method=='STOCK_GD' else 'off']
        assert all(flag not in command for flag in ['--round140-counts','--round141-count-proof','--round142-count-products','--round143-rn','--round144-projection','--round145-projection'])
        l.update(number=1,group_number=i,global_launch_number=i,method='S2' if method=='BASE' else method,R146_method=method,seed=seed,
            binary_layer='R146',version='candidate',panel=p,panel_kind=p['panel_kind'],destination=str(d),cap_seconds=cap,
            hard_stop_seconds=cap-2,command=command,arm_id=armid,stage=batch,AM_threshold=.08)
        identity=dict(schema='round146-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=seed),candidate_binary=manifest['production_PE'],candidate_binary_sha256=manifest['production_PE_SHA']),
            prereg_sha256=hashlib.sha256(json.dumps(dict(batch=batch,positions=positions,reason=reason),sort_keys=True).encode()).hexdigest(),
            runner_sha256=sha(__file__),source_hashes=manifest['source_hashes'],candidate_binary_sha256=manifest['production_PE_SHA'],dll_sha256=DLL_SHA,
            measured_source_commit=manifest['source_commit'],delivery_base_commit=BASE,launches=[l],candidate_manifest_path=str(manifest_path),candidate_manifest_SHA=sha(manifest_path),stage=batch,no_cross_arm_information=True)
        write(camp/'identity.json',identity);groups.append(dict(position=i,stage=batch,group=camp.relative_to(OUT).as_posix(),arm_id=armid,identity_SHA=sha(camp/'identity.json'),launch=l))
    helpers=inherited.helper_bindings();helpers.update({str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in (ROOT/'scripts').glob('round146_*.py') if p.stem in ('round146_campaign','round146_read','round146_math','round146_common')})
    write(target,dict(UTC=utc(),batch=batch,groups=groups,selection_reason=reason,candidate_manifest_SHA=sha(manifest_path),helpers=helpers,
        new_nominal_caps=sum(g['launch']['cap_seconds'] for g in groups),Seed_default=0,H_seed=20260626,serial=True,threads=1,affinity_mask=4,all_own_H=True))
def admission(batch):
    path=OUT/f'{batch}_matrix.json';m=read(path);gate=read(OUT/'review'/f'{batch}_admission.json')
    assert gate['decision']=='ACCEPT' and gate['matrix_SHA']==sha(path)
    if not batch.startswith('qualification'):assert gate['independent_nonimplementer_review']
    assert m['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json');inherited._candidate(OUT/'candidate_manifest.json')
    for name,digest in m['helpers'].items():assert sha(ROOT/name)==digest,name
    return m
def arm(batch,position):
    group=admission(batch)['groups'][position-1];camp=OUT/group['group'];assert sha(camp/'identity.json')==group['identity_SHA']
    identity=read(camp/'identity.json');launch=identity['launches'][0];d=Path(launch['destination']);assert not (d/'verification_closeout.json').exists()
    if not d.exists():
        tick,creation=inherited.inherited.process_origin();inherited.supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(),'Inspect unsealed producer; never repeat'
    value=verify(launch,identity)
    write(OUT/'runtime_status.json',dict(UTC=utc(),batch=batch,position=position,arm_id=launch['arm_id'],certificate=value['arm']['certificate'],U=value['arm']['U'],L=value['arm']['L']))
    print(json.dumps(value['arm']),flush=True)
def run(batch,stop_after=None):
    configure()
    for group in admission(batch)['groups']:
        if stop_after is not None and group['position']>stop_after:break
        if (Path(group['launch']['destination'])/'verification_closeout.json').exists():continue
        label=f'{batch}_{group["position"]:03}';assert not (OUT/'fees'/label).exists(),'Inspect prior fee; never repeat'
        write(OUT/'active_position.json',dict(UTC=utc(),batch=batch,position=group['position'],fee_label=label,arm_id=group['arm_id']))
        assert metered(label,'diagnostic' if batch.startswith('qualification') else 'native',
            [PYTHON,'-B',__file__,'arm',batch,group['position']],group['launch']['cap_seconds']+120,group['launch']['cap_seconds']+1800)==0
    write(OUT/f'{batch}_run_return.json',dict(UTC=utc(),budget=budget()))
def qualification():
    freeze('qualification',[dict(role='K-20-S',cap=90,method='STOCK_GD')],
        'One short complete own-H/initial LP/target/terminal Start/proof health qualification, not a performance result')
    write(OUT/'review/qualification_admission.json',dict(decision='ACCEPT',matrix_SHA=sha(OUT/'qualification_matrix.json'),
        independent_nonimplementer_review=False,reason='Finite actual writer/Native/Start and exact oracle PASS; independent math/static review has no blocker; short health only'))
def k20():
    freeze('k20',[dict(role='K-20-S',method=m) for m in ['STOCK','STOCK_GD']],
        'Uniform STOCK+GD selected: K20 combination LP .251016 exceeds GD .236010 and STOCK .204590; test incremental complete certificate value against strong same-PE STOCK')
def rx20():
    freeze('rx20',[dict(role='R-X20-S-T1',method=m) for m in ['STOCK','STOCK_GD']], 'Conditional certified-role stability and cost test after independent K20 review')
if __name__=='__main__':
    if sys.argv[1]=='arm':arm(sys.argv[2],int(sys.argv[3]))
    elif sys.argv[1]=='run':run(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else None)
    else:globals()[sys.argv[1]]()
