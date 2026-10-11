"""Five direct serial wrappers, fixed children, original absolute clock/reserve."""
from round112_common import *
import copy, csv, inspect, shutil, traceback
import round109_campaign as original_campaign
from round109_prepare import COMMON
import round90_lp_g_g3 as supervisor
import round112_audit as audit
from round100_idle import ensure_idle

def helpers():
    names=set(original_campaign.helpers())
    names.update(['scripts/round111_seed_audit.py','scripts/round111_common.py','scripts/round110_common.py',
        'scripts/round103_common.py','scripts/round101_common.py'])
    names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('round112*') if p.suffix in ('.py','.cpp','.ps1'))
    return {p:sha(ROOT/p) for p in sorted(names)}

def records(camp):
    p=camp/'summary.jsonl';return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []

def prepare():
    production=check_identity();manifest=read(OUT/'input_manifest.json')
    for target,roles in [('campaign',manifest['roles']),('qualification/cli02',manifest['qualification_roles'][:1]),('qualification/positive01',manifest['qualification_roles'][1:2]),('qualification/zero01',manifest['qualification_roles'][2:])]:
        camp=OUT/target;camp.mkdir(parents=True,exist_ok=False)
        prereg=dict(common=COMMON,candidate_binary=PE.relative_to(ROOT).as_posix(),candidate_binary_sha256=sha(PE))
        launches=[];references={}
        for group,p0 in enumerate(roles,1):
            p=copy.deepcopy(p0);ref=OUT/'qualification/reference'/p['id'];p['reference']=read(ref/'build.json');p['instance_path']=p['input_path']
            assert p['reference']['canonical_sha256']==sha(ref/'original.lp')
            dst=camp/'reference'/p['id'];dst.mkdir(parents=True)
            for name in ('original.lp','build.json'):shutil.copyfile(ref/name,dst/name)
            references[p['id']]=p['reference']
            for arm in p['method_order']:
                n=len(launches)+1;dest=camp/'raw'/f'{n:02d}_{p["id"]}_S0_{arm}'
                cmd=supervisor.audited_runner_utilities.command_for(prereg,p,'P-GRB',dest) if arm in ('P-GRB','P-S') else supervisor.command_for(prereg,p,'ENS-C',dest)
                if arm=='P-S':cmd+=['--round112-ens-start-compact']
                if arm=='M-B':cmd+=['--round98-state-service','m-binary']
                launches.append(dict(number=n,group_number=group,id=p['id'],arm=arm,seed=0,panel=p,panel_kind=p['panel_kind'],
                    destination=str(dest),stage=p['panel_kind'],cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=cmd))
        write(camp/'identity.json',dict(prereg=prereg,prereg_sha256=sha(OUT/'protocol.json'),protocol_path=str(OUT/'protocol.json'),
            runner_sha256=sha(__file__),helpers=helpers(),source_hashes=bindings(),candidate_binary_sha256=sha(PE),dll_sha256=DLL_SHA,
            measured_source_commit=production['measured_source_commit'],delivery_base_commit=BASE,references=references,launches=launches,prepared_unix=time.time()))
    formal=read(OUT/'campaign/identity.json');assert len(formal['launches'])==20 and sum(l['cap_seconds'] for l in formal['launches'])==40800
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=sha(PE),DLL_SHA=DLL_SHA,
        source_bindings=bindings(),helpers=helpers(),input_manifest_SHA=sha(OUT/'input_manifest.json'),protocol_SHA=sha(OUT/'protocol.json'),
        campaign_identity_SHA=sha(OUT/'campaign/identity.json'),full_argv=[l['command'] for l in formal['launches']],
        qualification_campaign_identity_SHAs={k:sha(OUT/k/'identity.json') for k in ['qualification/cli02','qualification/positive01','qualification/zero01']},
        same_new_PE_for_all_four_methods=True,default_ENS_changed=False))
    print('20 formal +7 actual CLI argv frozen; no native start')

def supervised(launch,identity,arm_tick):
    source=inspect.getsource(supervisor.run_one)
    for marker,new in [
      ('    write_new(destination / "observations.json", observations)\n','    write_new(destination / "native_end_receipt.json", dict(complete_seconds_until_native_end=time.perf_counter()-_arm_tick, ended_unix=time.time()))\n'),
      ('    write_new(destination / "audit.json", audited)\n','    write_new(destination / "postexit_audit_receipt.json", dict(complete_seconds_until_audit_end=time.perf_counter()-_arm_tick, ended_unix=time.time()))\n')]:
        assert source.count(marker)==1;source=source.replace(marker,marker+new)
    namespace=dict(vars(supervisor),ROOT=ROOT,CAMPAIGN=Path(launch['destination']).parents[1],audit_launch=audit.adapter,_arm_tick=arm_tick)
    exec(compile(source,__file__+'::original_supervisor','exec'),namespace)
    return namespace['run_one'](launch,identity['prereg'],identity)

def reserve():
    path=OUT/'campaign/identity.json'
    if not path.exists():return dict(starts=25,nominal=40800,overhead=600)
    identity=read(path);done=len(records(path.parent));left=identity['launches'][done:]
    return dict(starts=len(left)+len({l['group_number'] for l in left}),nominal=sum(l['cap_seconds'] for l in left),overhead=120*len({l['group_number'] for l in left}))

def fee_begin(label,children,cap,qualification):
    tick,creation=process_origin();before=budget();remaining=reserve();d=OUT/'fees'/label
    assert not before['unclosed']
    assert before['remaining_starts']>=remaining['starts']+(children+1 if qualification else 0)
    assert before['remaining_outer_seconds']>=remaining['nominal']+remaining['overhead']+(cap if qualification else 0)
    if qualification:
        assert before['qualification_starts']+children+1<=20 and before['qualification_seconds']+cap<=1800
    d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=sys.argv,cwd=str(ROOT),conservative_process_starts=children+1,qualification=qualification,
        declared_native_children=children,wrapper_pid=os.getpid(),wrapper_creation_unix=creation,outer_cap=cap,
        budget_before=before,all_remaining_fixed_reserve=remaining,helpers=helpers()))
    return d,tick

def fee_pending(d,tick,qualification,code,actual):
    write(d/'pending_exit_receipt.json',dict(exit_code=code,outer_seconds_lower=time.perf_counter()-tick,qualification=qualification,
        actual_native_children=actual,wrapper_pid=os.getpid(),necessary_trailer_complete=True,nested_native_seconds_added=False))
    print(json.dumps(dict(wrapper_pending_exit=str(d),exit_code=code)),flush=True)

def reference():
    d,tick=fee_begin('reference01',1,180,True);code=1
    try:
        ensure_idle()
        command=[str(BUILD/'Round112ReferenceBatch.exe'),str(OUT/'qualification/reference_batch.tsv')]
        write(d/'native_launch.json',dict(command=command,PE_SHA=sha(command[0]),source_bindings=bindings(),Optimize=0))
        with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
            child=subprocess.run(command,cwd=ROOT,env=env(),stdout=so,stderr=se,timeout=175)
        assert child.returncode==0,(d/'stderr.log').read_text()
        code=0
    finally:fee_pending(d,tick,True,code,1)

def billed(name,first,last,label,qualification=False):
    camp=OUT/name;ident=read(camp/'identity.json');count=last-first+1
    cap=sum(l['cap_seconds'] for l in ident['launches'][first-1:last])+120
    d,tick=fee_begin(label,count,cap,qualification);code=1
    try:
        ensure_idle();check_identity()
        assert ident['source_hashes']==bindings() and ident['helpers']==helpers() and ident['runner_sha256']==sha(__file__)
        assert len(records(camp))==first-1
        if not qualification:
            gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
            assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and gate['production_PE_SHA']==sha(PE)
            assert gate['campaign_identity_SHA']==sha(camp/'identity.json')
        for number in range(first,last+1):
            arm_tick=tick if number==first else time.perf_counter();check_identity();launch=ident['launches'][number-1]
            assert not Path(launch['destination']).exists() and sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
            write(d/f'{number:02d}_before.json',dict(number=number,id=launch['id'],arm=launch['arm'],started_unix=time.time()))
            rec=supervised(launch,ident,arm_tick);dest=Path(launch['destination'])
            same=[r for r in records(camp) if r['id']==launch['id']]
            lower=[r['endpoint']['L'] for r in same];upper=[r['endpoint']['U'] for r in same if r['endpoint']['U'] is not None]
            assert not upper or max(lower)<=min(upper)+1e-7,'cross-arm offline contradiction; no imported UB or LB'
            write(dest/'audit_execution_metrics.json',audit.last_metrics)
            seconds=time.perf_counter()-arm_tick
            write(dest/'whole_arm_receipt.json',dict(number=number,id=rec['id'],arm=rec['arm'],seed=0,complete_seconds=seconds,
                includes_admission_identity_startup_native_outputs_necessary_postexit_audit_crosscheck_metrics=True,
                first_arm_includes_wrapper_creation_and_import=number==first,metrics_written_before_whole=True,cap_seconds=launch['cap_seconds']))
            write(d/f'{number:02d}_after.json',dict(completed_and_audited=True,whole_arm_receipt_SHA=sha(dest/'whole_arm_receipt.json')))
            assert seconds<=launch['cap_seconds'],'full arm exceeded frozen cap'
        if qualification:
            write(camp/'qualification_trailer.json',dict(passed=True,records=records(camp),production_PE_SHA=sha(PE),helpers=helpers(),
                inside_outer_clock=True,not_performance=True,normal_returns=count))
        code=0
    except BaseException:
        (d/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(d,tick,qualification,code,sum((Path(l['destination'])/'launch.json').exists() for l in ident['launches'][first-1:last]))

def close_fee(label):
    d=OUT/'fees'/label;launch=read(d/'launch.json');pending=read(d/'pending_exit_receipt.json')
    assert not (d/'receipt.json').exists()
    # Executed by the caller only after the direct wrapper has actually exited.
    import ctypes
    api=ctypes.WinDLL('kernel32');api.OpenProcess.restype=ctypes.c_void_p
    handle=api.OpenProcess(0x1000,False,launch['wrapper_pid'])
    if handle:
        code=ctypes.c_ulong();assert api.GetExitCodeProcess(ctypes.c_void_p(handle),ctypes.byref(code));api.CloseHandle(ctypes.c_void_p(handle));assert code.value!=259
    upper=max(pending['outer_seconds_lower'],time.time()-launch['wrapper_creation_unix'])
    write(d/'receipt.json',dict(pending,outer_seconds_upper=upper,actual_exit_observed=True,
        outer_interval=[pending['outer_seconds_lower'],upper],caller_observed_unix=time.time(),
        charge_includes_wrapper_exit_observation_delay=True,clock_not_claimed_exact=True,fee_closure_engineering_native_starts=0))
    print(json.dumps(budget()),flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='prepare':prepare()
    elif action=='reference':reference()
    elif action=='close-fee':close_fee(sys.argv[2])
    elif action=='billed':billed(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5],'--qualification' in sys.argv[6:])
    else:raise ValueError(action)
