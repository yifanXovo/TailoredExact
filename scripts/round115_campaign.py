"""Prospective producer boundary; original R90 supervision and original PE."""
from round115_common import *
import copy,inspect,shutil,traceback,csv
import round114_campaign as prior
import round90_lp_g_g3 as supervisor
import round114_audit as audit
from round113_progress import OptionalPublisher
from round109_prepare import COMMON
from round100_idle import ensure_idle
from round115_verify import verify
csv.field_size_limit(64*1024*1024)

def helpers():
    names=set(prior.helpers())
    names.update('scripts/'+n for n in ['round115_common.py','round115_campaign.py','round115_verify.py'])
    return {p:sha(ROOT/p) for p in sorted(names)}

def records(camp):return prior.records(camp)

def prepare():
    check_identity();manifest=read(OUT/'input_manifest.json')
    for target,roles in [('campaign',manifest['roles']),('qualification/cli01',manifest['qualification_roles'])]:
        camp=OUT/target;camp.mkdir(parents=True,exist_ok=False)
        prereg=dict(common=COMMON,candidate_binary=PE.relative_to(ROOT).as_posix(),candidate_binary_sha256=PE_SHA)
        launches=[];references={}
        for p0 in roles:
            p=copy.deepcopy(p0);ref=OUT/'qualification/reference'/p['id'];p['reference']=read(ref/'build.json');p['instance_path']=p['input_path']
            dst=camp/'reference'/p['id'];dst.mkdir(parents=True)
            for name in ['original.lp','build.json']:shutil.copyfile(ref/name,dst/name)
            references[p['id']]=p['reference']
            for arm in p['method_order']:
                n=len(launches)+1;d=camp/'raw'/f'{n:02d}_{p["id"]}_S0_{arm}'
                cmd=supervisor.audited_runner_utilities.command_for(prereg,p,'P-GRB',d) if arm in ['P-GRB','P-S'] else supervisor.command_for(prereg,p,'ENS-C',d)
                if arm=='P-S':cmd+=['--round112-ens-start-compact']
                if arm=='M-B':cmd+=['--round98-state-service','m-binary']
                launches.append(dict(number=n,group_number=1,id=p['id'],arm=arm,seed=0,panel=p,panel_kind=p['panel_kind'],
                    destination=str(d),cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=cmd))
        write(camp/'identity.json',dict(prereg=prereg,prereg_sha256=sha(OUT/'protocol.json'),runner_sha256=sha(__file__),
            helpers=helpers(),source_hashes=bindings(),candidate_binary_sha256=PE_SHA,dll_sha256=DLL_SHA,
            measured_source_commit=SOURCE,delivery_base_commit=BASE,references=references,launches=launches,
            measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md'),dependency_graph_SHA=sha(OUT/'producer_dependency_graph.json'),
            original_native_window_unchanged=True))
    formal=read(OUT/'campaign/identity.json');assert len(formal['launches'])==4 and sum(l['cap_seconds'] for l in formal['launches'])==14400
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        source_bindings=bindings(),helpers=helpers(),input_manifest_SHA=sha(OUT/'input_manifest.json'),protocol_SHA=sha(OUT/'protocol.json'),
        measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md'),dependency_graph_SHA=sha(OUT/'producer_dependency_graph.json'),
        campaign_identity_SHA=sha(OUT/'campaign/identity.json'),full_argv=[l['command'] for l in formal['launches']],
        qualification_campaign_identity_SHA=sha(OUT/'qualification/cli01/identity.json'),default_ENS_changed=False,
        qualification_test_SHA=sha(ROOT/'scripts/qualify_round115.py'),offline_reader_SHA=sha(ROOT/'scripts/read_round115.py'),
        mathematical_verifier_SHA=sha(ROOT/'scripts/round115_sublevel.py'),
        qualification_post_driver_SHA=sha(ROOT/'scripts/qualify_round115_post.py')))
    write(OUT/'fixed_manifest.json',formal)

def production_check(l,observations,c,i):
    """Existing lightweight final physical/return check; no history/model replay."""
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    d=Path(l['destination']);r=read(d/'result.json')
    assert r['process_return_code']==0 and r['process_shutdown_margin_seconds']==30
    physical=audit.core.full_fleet(ROOT,l['panel'],r)
    assert abs(physical['F']-r['upper_bound'])<=1e-7
    assert (d/'phases.csv').is_file() and (d/'observations.json').is_file()
    return dict(state='PRODUCED_PENDING_VERIFICATION',verification_passed=None,production_checks_passed=True,
        final_physical_verification=physical,normal_return=True,model_Start_history_audit_pending=True,
        known_independent_floor0=True,own_strict_zero=physical['Y'][1:]==audit.core.evidence.instance(ROOT,l['panel'])['D'][1:])

def supervisor_function(namespace):
    source=inspect.getsource(supervisor.run_one)
    old='    audit_started = time.perf_counter()\n'
    assert source.count(old)==1
    source=source[:source.index(old)]+'''    assert completion["within_cap"]
    assert affinity.read_masks() == binding["before"]
    assert reason == "normal_return", "Production execution/resource failure"
    write_new(destination / "native_end_receipt.json", dict(complete_seconds_until_native_end=time.perf_counter()-_arm_tick, ended_unix=time.time()))
    produced = production_check(launch, observations, completion, identity)
    write_new(destination / "production_checks.json", produced)
    record = dict(number=launch["number"], id=launch["id"], arm=launch["arm"], destination=str(destination),
                  completion=completion, verification_state="PRODUCED_PENDING_VERIFICATION", audit_passed=None, endpoint=None)
    append_jsonl(CAMPAIGN / "summary.jsonl", record)
    print(json.dumps(dict(produced=record)), flush=True)
    return record
'''
    exec(compile(source,__file__+'::source_extracted_R90_producer','exec'),namespace)
    return namespace['run_one']

def supervised(l,i,tick):
    publisher=OptionalPublisher(l);d=Path(l['destination'])
    namespace=dict(vars(supervisor),ROOT=ROOT,CAMPAIGN=d.parents[1],atomic_status=publisher,_arm_tick=tick,production_check=production_check)
    try:return supervisor_function(namespace)(l,i['prereg'],i)
    finally:
        if d.is_dir():write(d/'progress_publication_receipt.json',dict(publisher.receipt(),necessary_write_before_production=True,
            global_namespace_modified=False,qualification_fault_injected=False))

def finish_producer(l,tick,t0unix):
    d=Path(l['destination'])
    names=['result.json','completion.json','observations.json','phases.csv','production_checks.json','progress_publication_receipt.json','native_end_receipt.json']
    assert all((d/n).is_file() for n in names)
    write(d/'producer_seal.json',dict(required_SHA={n:sha(d/n) for n in names},
        produced_files=[dict(path=p.relative_to(d).as_posix(),bytes=p.stat().st_size) for p in sorted(d.rglob('*')) if p.is_file()],
        scope='all native output files closed; original call/model SHA assertions deferred to verification',
        native_stopped_no_reentry=True,cohort_review_excluded=True))
    digest=sha(d/'producer_seal.json');produced=time.perf_counter();producedunix=time.time()
    write(d/'producer_receipt.json',dict(number=l['number'],id=l['id'],arm=l['arm'],state='PRODUCED_PENDING_VERIFICATION',
        verification_passed=None,t0_perf=tick,t0_unix=t0unix,t_produce_perf=produced,t_produce_unix=producedunix,T_produce=produced-tick,
        cap_seconds=l['cap_seconds'],producer_seal_SHA=digest,required_outputs_closed=True,native_stopped_no_reentry=True,
        includes_H_models_online_checks_native_cleanup_serialization_supervision=True,
        first_arm_includes_wrapper_creation_and_import=l['number']==1,
        receipt_write_is_subsequent_management_charged_in_T_verify=True))
    assert produced-tick<=l['cap_seconds'],'producer exceeded frozen cap'

def fee_begin(label,children,cap,qualification):
    tick,creation=process_origin();b=budget();d=OUT/'fees'/label
    assert not b['unclosed'] and b['remaining_starts']>=children+1 and b['remaining_outer_seconds']>=cap
    if qualification:
        assert b['qualification_starts']+children+1<=10 and b['qualification_seconds']+cap<=600
        assert b['remaining_starts']>=children+1+5 and b['remaining_outer_seconds']>=cap+14520
    d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=sys.argv,cwd=str(ROOT),conservative_process_starts=children+1,qualification=qualification,
        declared_native_children=children,wrapper_pid=os.getpid(),wrapper_creation_unix=creation,outer_cap=cap,budget_before=b,helpers=helpers()))
    return d,tick

def fee_pending(d,tick,qualification,code,actual):
    write(d/'pending_exit_receipt.json',dict(exit_code=code,outer_seconds_lower=time.perf_counter()-tick,qualification=qualification,
        actual_native_children=actual,conservative_process_starts=read(d/'launch.json')['conservative_process_starts'],
        wrapper_pid=os.getpid(),necessary_trailer_complete=True,nested_native_seconds_added=False))
    print(json.dumps(dict(wrapper_pending_exit=str(d),exit_code=code)),flush=True)

def billed(name,label,qualification=False):
    camp=OUT/name;i=read(camp/'identity.json');count=len(i['launches'])
    cap=540 if qualification else budget()['remaining_outer_seconds']
    fee,tick=fee_begin(label,count,cap,qualification);code=1
    try:
        ensure_idle();check_identity();assert i['source_hashes']==bindings() and i['helpers']==helpers() and i['runner_sha256']==sha(__file__)
        assert not records(camp)
        if not qualification:
            gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
            assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and gate['helpers']==helpers()
            assert gate['campaign_identity_SHA']==sha(camp/'identity.json')
        for n,l in enumerate(i['launches'],1):
            arm_tick=tick if n==1 else time.perf_counter();armunix=read(fee/'launch.json')['wrapper_creation_unix'] if n==1 else time.time()
            check_identity();assert not Path(l['destination']).exists() and sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
            write(fee/f'{n:02d}_before.json',dict(number=n,id=l['id'],arm=l['arm'],t0_perf=arm_tick,t0_unix=armunix))
            supervised(l,i,arm_tick);finish_producer(l,arm_tick,armunix)
            verified=verify(l,i)
            write(fee/f'{n:02d}_after.json',dict(producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),
                total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json'),verification_complete=True))
            assert time.perf_counter()-tick<=cap,'campaign outer cap exceeded'
        if qualification:write(camp/'qualification_trailer.json',dict(passed=True,normal_returns=count,production_PE_SHA=PE_SHA,
            helpers=helpers(),inside_outer_clock=True,not_performance=True))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,qualification,code,sum((Path(l['destination'])/'launch.json').exists() for l in i['launches']))

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='billed':billed(sys.argv[2],sys.argv[3],'--qualification' in sys.argv[4:])
    else:raise ValueError(sys.argv[1])
