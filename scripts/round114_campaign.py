"""Exactly two qualification CLI and four once-only fixed serial G100 arms."""
from round114_common import *
import copy, inspect, shutil, traceback
import round113_campaign as prior
import round90_lp_g_g3 as supervisor
import round114_audit as audit
from round114_claims import ClaimRejection,reconcile
from round113_progress import OptionalPublisher
from round109_prepare import COMMON
from round100_idle import ensure_idle

def helpers():
    names=set(prior.helpers())
    names.update('scripts/'+n for n in ['round114_common.py','round114_claims.py','round114_ps.py','round114_audit.py','round114_campaign.py'])
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
            claim_policy_SHA=sha(OUT/'claim_policy.md'),required_claim_rejection_closeout=True))
    formal=read(OUT/'campaign/identity.json');assert len(formal['launches'])==4 and sum(l['cap_seconds'] for l in formal['launches'])==14400
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        source_bindings=bindings(),helpers=helpers(),input_manifest_SHA=sha(OUT/'input_manifest.json'),protocol_SHA=sha(OUT/'protocol.json'),
        claim_policy_SHA=sha(OUT/'claim_policy.md'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),full_argv=[l['command'] for l in formal['launches']],
        qualification_campaign_identity_SHA=sha(OUT/'qualification/cli01/identity.json'),default_ENS_changed=False,
        helper_delta='necessary native claim qualification, independent evidence, closeout and zero-call audit; production unchanged'))
    write(OUT/'fixed_manifest.json',formal)
    print('4 formal and 2 qualification argv prepared; no native starts')

def supervisor_function(namespace):
    source=inspect.getsource(supervisor.run_one)
    edits=[
        ('    write_new(destination / "observations.json", observations)\n',
         '    write_new(destination / "observations.json", observations)\n    write_new(destination / "native_end_receipt.json", dict(complete_seconds_until_native_end=time.perf_counter()-_arm_tick, ended_unix=time.time()))\n'),
        ('    except Exception as exc:\n        audited = dict(passed=False, error=repr(exc), status="requires_independent_review",\n                       certificate=False, endpoint=None)\n',
         '    except ClaimRejection as exc:\n        audited = dict(exc.evidence, status="structured_claim_rejection", claim_rejection_recorded=True)\n    except Exception as exc:\n        audited = dict(passed=False, error=repr(exc), status="requires_independent_review",\n                       certificate=False, endpoint=None)\n'),
        ('    write_new(destination / "audit.json", audited)\n',
         '    write_new(destination / "audit.json", audited)\n    write_new(destination / "postexit_audit_receipt.json", dict(complete_seconds_until_audit_end=time.perf_counter()-_arm_tick, ended_unix=time.time()))\n'),
        ('    if not audited["passed"]:\n        raise RuntimeError("Audit failed; retain evidence and stop before next arm")\n',
         '    if not audited["passed"] and not (audited.get("claim_rejection_recorded") is True and audited.get("independent_evidence_audit_passed") is True):\n        raise RuntimeError("Audit failed; retain evidence and stop before next arm")\n')]
    for old,new in edits:assert source.count(old)==1;source=source.replace(old,new)
    exec(compile(source,__file__+'::source_extracted_R90','exec'),namespace)
    return namespace['run_one']

def supervised(l,i,tick):
    publisher=OptionalPublisher(l);d=Path(l['destination']);camp=d.parents[1]
    namespace=dict(vars(supervisor),ROOT=ROOT,CAMPAIGN=camp,audit_launch=audit.adapter,
        atomic_status=publisher,_arm_tick=tick,ClaimRejection=ClaimRejection)
    try:return supervisor_function(namespace)(l,i['prereg'],i)
    finally:
        if d.is_dir():write(d/'progress_publication_receipt.json',dict(publisher.receipt(),necessary_write_before_whole=True,
            global_namespace_modified=False,qualification_fault_injected=False))

def cohort_check(camp,current):
    same=[r for r in records(camp) if r['id']==current['id']]
    claims=[];witnesses=[];layers=[]
    for rec in same:
        d=Path(rec['destination']);ind=read(d/'independent_evidence.json')
        claims+=read(d/'native_claims.json');witnesses+=ind['witnesses']
        layers.append(dict(arm=rec['arm'],independent_evidence_SHA=sha(d/'independent_evidence.json'),
            own_evidence_inside_original_whole=True,whole_already_closed=(d/'whole_arm_receipt.json').exists(),
            time_layer='current_closeout' if rec['arm']==current['arm'] else 'previous_closed_arm'))
    value=dict(reconcile(claims,witnesses),witness_set=layers,checked_unix=time.time(),
        phase='inside_current_arm_whole',future_reconciliation_in_current_clock=False,online_witness_transfer=False)
    write(Path(current['destination'])/'cohort_check.json',value)
    return value

def reserve():
    path=OUT/'campaign/identity.json'
    if not path.exists():return dict(starts=5,nominal=14400,overhead=120)
    i=read(path);done=len(records(path.parent));left=i['launches'][done:]
    return dict(starts=len(left)+(1 if left else 0),nominal=sum(l['cap_seconds'] for l in left),overhead=120 if left else 0)

def fee_begin(label,children,cap,qualification):
    tick,creation=process_origin();b=budget();remaining=reserve();d=OUT/'fees'/label
    assert not b['unclosed']
    assert b['remaining_starts']>=remaining['starts']+(children+1 if qualification else 0)
    assert b['remaining_outer_seconds']>=remaining['nominal']+remaining['overhead']+(cap if qualification else 0)
    if qualification:assert b['qualification_starts']+children+1<=8 and b['qualification_seconds']+cap<=900
    d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=sys.argv,cwd=str(ROOT),conservative_process_starts=children+1,qualification=qualification,
        declared_native_children=children,wrapper_pid=os.getpid(),wrapper_creation_unix=creation,outer_cap=cap,
        budget_before=b,all_remaining_fixed_reserve=remaining,helpers=helpers()))
    return d,tick

def fee_pending(d,tick,qualification,code,actual):
    write(d/'pending_exit_receipt.json',dict(exit_code=code,outer_seconds_lower=time.perf_counter()-tick,
        qualification=qualification,actual_native_children=actual,conservative_process_starts=read(d/'launch.json')['conservative_process_starts'],
        wrapper_pid=os.getpid(),necessary_trailer_complete=True,nested_native_seconds_added=False))
    print(json.dumps(dict(wrapper_pending_exit=str(d),exit_code=code)),flush=True)

def finish_arm(l,i,tick,rec,fee):
    d=Path(l['destination']);cohort_check(d.parents[1],rec)
    write(d/'audit_execution_metrics.json',audit.last_metrics)
    write(d/'independent_endpoint_closeout.json',dict(own_evidence_SHA=sha(d/'independent_evidence.json'),
        own_UB_floor_and_own_zero_validated_before_whole=True,claim_records_SHA=sha(d/'native_claims.json'),
        rejection_SHA=sha(d/'claim_rejections.json'),cohort_SHA=sha(d/'cohort_check.json'),
        audit_SHA=sha(d/'audit.json'),required_audit_complete=True,formal_eligibility_pending_actual_whole=True))
    progress_digest=sha(d/'progress_publication_receipt.json')
    independent_digest=sha(d/'independent_evidence.json');closeout_digest=sha(d/'independent_endpoint_closeout.json')
    seconds=time.perf_counter()-tick
    write(d/'whole_arm_receipt.json',dict(number=l['number'],id=l['id'],arm=l['arm'],seed=0,complete_seconds=seconds,
        includes_admission_identity_startup_native_outputs_necessary_postexit_audit_crosscheck_metrics=True,
        first_arm_includes_wrapper_creation_and_import=l['number']==1,metrics_written_before_whole=True,
        progress_publication_receipt_written_before_whole=True,progress_receipt_SHA=progress_digest,
        independent_evidence_SHA=independent_digest,independent_closeout_SHA=closeout_digest,
        own_UB_floor_zero_evidence_written_before_whole=True,claim_rejections_written_before_whole=True,
        future_cohort_review_in_clock=False,cap_seconds=l['cap_seconds']))
    write(fee/f'{l["number"]:02d}_after.json',dict(completed_and_audited=True,whole_arm_receipt_SHA=sha(d/'whole_arm_receipt.json')))
    assert seconds<=l['cap_seconds'],'full arm exceeded frozen cap'

def billed(name,label,qualification=False):
    camp=OUT/name;i=read(camp/'identity.json');count=len(i['launches'])
    cap=sum(l['cap_seconds'] for l in i['launches'])+120
    fee,tick=fee_begin(label,count,cap,qualification);code=1
    try:
        ensure_idle();check_identity()
        assert i['source_hashes']==bindings() and i['helpers']==helpers() and i['runner_sha256']==sha(__file__)
        assert not records(camp)
        if not qualification:
            gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
            assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and gate['production_PE_SHA']==PE_SHA
            assert gate['campaign_identity_SHA']==sha(camp/'identity.json')
            assert gate['helpers']==helpers()
        for n,l in enumerate(i['launches'],1):
            arm_tick=tick if n==1 else time.perf_counter();check_identity()
            assert not Path(l['destination']).exists() and sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
            write(fee/f'{n:02d}_before.json',dict(number=n,id=l['id'],arm=l['arm'],started_unix=time.time()))
            rec=supervised(l,i,arm_tick);finish_arm(l,i,arm_tick,rec,fee)
        if qualification:write(camp/'qualification_trailer.json',dict(passed=True,normal_returns=count,production_PE_SHA=PE_SHA,
            helpers=helpers(),inside_outer_clock=True,not_performance=True,numerical_contradiction_reproduced=False))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,qualification,code,sum((Path(l['destination'])/'launch.json').exists() for l in i['launches']))

def seal():
    assert not records(OUT/'campaign') and not records(OUT/'qualification/cli01')
    for name in ['campaign','qualification/cli01']:
        p=OUT/name/'identity.json';i=read(p);i['helpers']=helpers();i['runner_sha256']=sha(__file__)
        i['prereg_sha256']=sha(OUT/'protocol.json');p.unlink();write(p,i)
    p=OUT/'candidate_identity.json';i=read(p);i.update(helpers=helpers(),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        qualification_campaign_identity_SHA=sha(OUT/'qualification/cli01/identity.json'),
        qualification_test_SHA=sha(ROOT/'scripts/qualify_round114.py'),offline_reader_SHA=sha(ROOT/'scripts/read_round114.py'),
        qualification_post_driver_SHA=sha(ROOT/'scripts/qualify_round114_post.py'),protocol_SHA=sha(OUT/'protocol.json'))
    p.unlink();write(p,i);p=OUT/'fixed_manifest.json';p.unlink();write(p,read(OUT/'campaign/identity.json'))
    print('final performance bytes and exact argv sealed before real CLI')

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='seal':seal()
    elif sys.argv[1]=='billed':billed(sys.argv[2],sys.argv[3],'--qualification' in sys.argv[4:])
    else:raise ValueError(sys.argv[1])
