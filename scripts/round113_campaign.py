"""Two fixed serial groups; inherited production and truthful absolute clocks."""
from round113_common import *
import copy, inspect, shutil, traceback
import round112_campaign as old_campaign
import round90_lp_g_g3 as supervisor
import round113_audit as audit
from round113_progress import OptionalPublisher, DenyDeleteHandle
from round109_prepare import COMMON
from round100_idle import ensure_idle

def helpers():
    names=set(old_campaign.helpers())
    # Offline reports, export and review do not affect the performance closure.
    names.update('scripts/'+n for n in ['round113_common.py','round113_progress.py','round113_audit.py','round113_campaign.py'])
    return {p:sha(ROOT/p) for p in sorted(names)}

def records(camp):
    p=camp/'summary.jsonl'
    return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []

def prepare():
    production=check_identity();manifest=read(OUT/'input_manifest.json')
    for target,roles in [('campaign',manifest['roles']),('qualification/cli01',manifest['qualification_roles'])]:
        camp=OUT/target;camp.mkdir(parents=True,exist_ok=False)
        prereg=dict(common=COMMON,candidate_binary=PE.relative_to(ROOT).as_posix(),candidate_binary_sha256=PE_SHA)
        launches=[];references={}
        for group,p0 in enumerate(roles,1):
            p=copy.deepcopy(p0);ref=OUT/'qualification/reference'/p['id'];p['reference']=read(ref/'build.json');p['instance_path']=p['input_path']
            dst=camp/'reference'/p['id'];dst.mkdir(parents=True)
            for name in ['original.lp','build.json']:shutil.copyfile(ref/name,dst/name)
            references[p['id']]=p['reference']
            for arm in p['method_order']:
                n=len(launches)+1;d=camp/'raw'/f'{n:02d}_{p["id"]}_S0_{arm}'
                cmd=supervisor.audited_runner_utilities.command_for(prereg,p,'P-GRB',d) if arm in ['P-GRB','P-S'] else supervisor.command_for(prereg,p,'ENS-C',d)
                if arm=='P-S':cmd+=['--round112-ens-start-compact']
                if arm=='M-B':cmd+=['--round98-state-service','m-binary']
                launches.append(dict(number=n,group_number=group,id=p['id'],arm=arm,seed=0,panel=p,panel_kind=p['panel_kind'],
                    destination=str(d),cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=cmd))
        write(camp/'identity.json',dict(prereg=prereg,prereg_sha256=sha(OUT/'protocol.json'),runner_sha256=sha(__file__),
            helpers=helpers(),source_hashes=bindings(),candidate_binary_sha256=PE_SHA,dll_sha256=DLL_SHA,
            measured_source_commit=SOURCE,delivery_base_commit=BASE,references=references,launches=launches,
            optional_publication_failure_policy='one OSError then disable per arm; authoritative writes still fatal'))
    formal=read(OUT/'campaign/identity.json')
    assert len(formal['launches'])==8 and sum(l['cap_seconds'] for l in formal['launches'])==21600
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        source_bindings=bindings(),helpers=helpers(),input_manifest_SHA=sha(OUT/'input_manifest.json'),protocol_SHA=sha(OUT/'protocol.json'),
        campaign_identity_SHA=sha(OUT/'campaign/identity.json'),full_argv=[l['command'] for l in formal['launches']],
        qualification_campaign_identity_SHA=sha(OUT/'qualification/cli01/identity.json'),default_ENS_changed=False,
        helper_delta='progress publication isolation and normal no-Optimize audit support; production unchanged'))
    write(OUT/'fixed_manifest.json',formal)
    print('8 formal and 4 qualification argv frozen; 0 native starts')

def supervisor_function(namespace):
    source=inspect.getsource(supervisor.run_one)
    for marker,new in [
      ('    write_new(destination / "observations.json", observations)\n','    write_new(destination / "native_end_receipt.json", dict(complete_seconds_until_native_end=time.perf_counter()-_arm_tick, ended_unix=time.time()))\n'),
      ('    write_new(destination / "audit.json", audited)\n','    write_new(destination / "postexit_audit_receipt.json", dict(complete_seconds_until_audit_end=time.perf_counter()-_arm_tick, ended_unix=time.time()))\n')]:
        assert source.count(marker)==1;source=source.replace(marker,marker+new)
    exec(compile(source,__file__+'::original_supervisor','exec'),namespace)
    return namespace['run_one']

def supervised(l,i,tick,inject_fault=False):
    publisher=OptionalPublisher(l);d=Path(l['destination']);camp=d.parents[1]
    namespace=dict(vars(supervisor),ROOT=ROOT,CAMPAIGN=camp,audit_launch=audit.adapter,
        atomic_status=publisher,_arm_tick=tick)
    handle=None
    try:
        if inject_fault:
            assert l['arm']=='P-S' and 'qualification' in str(camp)
            handle=DenyDeleteHandle(camp/'runtime_status.json');handle.__enter__()
        rec=supervisor_function(namespace)(l,i['prereg'],i)
        if inject_fault:
            assert publisher.disabled and publisher.failure['winerror'] is not None, 'actual active CLI fault did not trigger'
        return rec
    finally:
        if handle is not None:handle.__exit__(None,None,None)
        if d.is_dir():
            write(d/'progress_publication_receipt.json',dict(publisher.receipt(),
                qualification_fault_injected=inject_fault,holder_process=os.getpid() if inject_fault else None,
                sharing_mask=3 if inject_fault else None,held_before_child_launch_until_supervisor_end=inject_fault,
                necessary_write_before_whole=True,global_namespace_modified=False))

def reserve():
    path=OUT/'campaign/identity.json'
    if not path.exists():return dict(starts=10,nominal=21600,overhead=240)
    i=read(path);done=len(records(path.parent));left=i['launches'][done:]
    return dict(starts=len(left)+len({l['group_number'] for l in left}),nominal=sum(l['cap_seconds'] for l in left),overhead=120*len({l['group_number'] for l in left}))

def fee_begin(label,children,cap,qualification):
    tick,creation=process_origin();b=budget();remaining=reserve();d=OUT/'fees'/label
    assert not b['unclosed']
    assert b['remaining_starts']>=remaining['starts']+(children+1 if qualification else 0)
    assert b['remaining_outer_seconds']>=remaining['nominal']+remaining['overhead']+(cap if qualification else 0)
    if qualification:
        assert b['qualification_starts']+children+1<=12 and b['qualification_seconds']+cap<=1200
    d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=sys.argv,cwd=str(ROOT),conservative_process_starts=children+1,qualification=qualification,
        declared_native_children=children,wrapper_pid=os.getpid(),wrapper_creation_unix=creation,outer_cap=cap,
        budget_before=b,all_remaining_fixed_reserve=remaining,helpers=helpers()))
    return d,tick

def fee_pending(d,tick,qualification,code,actual):
    write(d/'pending_exit_receipt.json',dict(exit_code=code,outer_seconds_lower=time.perf_counter()-tick,
        qualification=qualification,actual_native_children=actual,wrapper_pid=os.getpid(),necessary_trailer_complete=True,
        nested_native_seconds_added=False))
    print(json.dumps(dict(wrapper_pending_exit=str(d),exit_code=code)),flush=True)

def billed(name,first,last,label,qualification=False):
    camp=OUT/name;i=read(camp/'identity.json');count=last-first+1
    cap=sum(l['cap_seconds'] for l in i['launches'][first-1:last])+120
    fee,tick=fee_begin(label,count,cap,qualification);code=1
    try:
        ensure_idle();check_identity()
        assert i['source_hashes']==bindings() and i['helpers']==helpers() and i['runner_sha256']==sha(__file__)
        assert len(records(camp))==first-1
        if not qualification:
            gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
            assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and gate['production_PE_SHA']==PE_SHA
            assert gate['campaign_identity_SHA']==sha(camp/'identity.json')
        for n in range(first,last+1):
            arm_tick=tick if n==first else time.perf_counter();check_identity();l=i['launches'][n-1]
            assert not Path(l['destination']).exists() and sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
            write(fee/f'{n:02d}_before.json',dict(number=n,id=l['id'],arm=l['arm'],started_unix=time.time()))
            rec=supervised(l,i,arm_tick,inject_fault=qualification and l['arm']=='P-S');d=Path(l['destination'])
            same=[r for r in records(camp) if r['id']==l['id']]
            upper=[r['endpoint']['U'] for r in same if r['endpoint']['U'] is not None]
            assert not upper or max(r['endpoint']['L'] for r in same)<=min(upper)+1e-7
            write(d/'audit_execution_metrics.json',audit.last_metrics)
            seconds=time.perf_counter()-arm_tick
            write(d/'whole_arm_receipt.json',dict(number=n,id=l['id'],arm=l['arm'],seed=0,complete_seconds=seconds,
                includes_admission_identity_startup_native_outputs_necessary_postexit_audit_crosscheck_metrics=True,
                first_arm_includes_wrapper_creation_and_import=n==first,metrics_written_before_whole=True,
                progress_publication_receipt_written_before_whole=True,progress_receipt_SHA=sha(d/'progress_publication_receipt.json'),cap_seconds=l['cap_seconds']))
            write(fee/f'{n:02d}_after.json',dict(completed_and_audited=True,whole_arm_receipt_SHA=sha(d/'whole_arm_receipt.json')))
            assert seconds<=l['cap_seconds'],'full arm exceeded frozen cap'
        if qualification:
            write(camp/'qualification_trailer.json',dict(passed=True,normal_returns=count,records=records(camp),
                production_PE_SHA=PE_SHA,helpers=helpers(),inside_outer_clock=True,not_performance=True))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        fee_pending(fee,tick,qualification,code,sum((Path(l['destination'])/'launch.json').exists() for l in i['launches'][first-1:last]))

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='billed':billed(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5],'--qualification' in sys.argv[6:])
    else:raise ValueError(sys.argv[1])
