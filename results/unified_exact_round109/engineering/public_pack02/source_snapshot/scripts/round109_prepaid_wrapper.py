"""Explicit supplemental wrapper for one paid, never-started slot and known raw faults.

All native commands and original supervisor/audit/affinity remain frozen. This
wrapper creates no extra driver and never rewrites a failed original record.
"""
import time
_entry_tick=time.perf_counter()
import copy,json,os,sys,traceback
from pathlib import Path
import round109_campaign as old
import round109_main06_recovery as repair
from round109_common import ROOT,OUT,PYTHON,read,write,sha,bindings,budget,check_identity
from round100_idle import ensure_idle

PLAN=OUT/'campaign/prepaid_recovery_plan02.json'
COUPON=OUT/'campaign/reader_recovery/prepaid18_consumption01.json'
GROUPS=[('main07_prepaid01',18,21),('main08',22,24),('main09',25,27),('main10',28,30),('main11',31,33),('main12',34,36),('seed01',37,38),('seed02',39,40),('seed03',41,42)]

def source_hashes():return {'scripts/'+n:sha(ROOT/'scripts'/n) for n in repair.SOURCES}

def wrapper_commands():return [[str(PYTHON),str(ROOT/'scripts/round109_prepaid_wrapper.py'),'billed',label,str(first),str(last)] for label,first,last in GROUPS]

def coupon_validate(coupon,receipt,launch,original_before,already_consumed,native_already_started):
    assert coupon['original_fee']=='main06' and coupon['original_receipt_SHA']==receipt['SHA']
    assert receipt['conservative_process_starts']==4 and receipt['actual_native_children_with_launch']==2 and receipt['exit_code']==1
    assert coupon['ordinal']==3 and coupon['original_number']==launch['number']==18
    assert coupon['command']==launch['command'] and coupon['consume_once'] and coupon['no_refund']
    assert not original_before and not already_consumed and not native_already_started

def check_coupon():
    proof=repair.verify(ROOT);q=read(OUT/'campaign/identity.json');r=read(OUT/'fees/main06/receipt.json')
    coupon_validate(proof['prepaid_coupon'],dict(r,SHA=sha(OUT/'fees/main06/receipt.json')),q['launches'][17],
        (OUT/'fees/main06/18_before.json').exists(),COUPON.exists(),Path(q['launches'][17]['destination']).exists())
    return proof['prepaid_coupon']

def plan():
    ensure_idle();check_identity();proof=repair.verify(ROOT);b=budget();q=read(OUT/'campaign/identity.json')
    assert b['paid_starts']==39 and not b['unclosed'] and len(old.records(OUT/'campaign'))==17
    check_coupon();assert old.helpers()==q['helpers'] and bindings()==q['source_hashes']
    write(PLAN,dict(original_candidate_identity_SHA=sha(OUT/'candidate_identity.json'),original_campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        recovery_sidecar_SHA=sha(ROOT/repair.SIDE),source_bindings=source_hashes(),original_helpers=old.helpers(),
        original_all42_native_argv=[x['command'] for x in q['launches']],supplemental_wrapper_argv=wrapper_commands(),
        remaining_native_numbers=list(range(18,43)),remaining_original_wrappers=9,new_driver_processes=0,
        original_budget_before=b,prepaid_coupon=proof['prepaid_coupon'],prepaid18_new_charge=0,original_main06_starts_retained=4,
        first_wrapper_native_numbers=list(range(18,22)),first_wrapper_actual_children=4,first_wrapper_newly_billed_children=3,first_wrapper_newly_billed_starts=4,
        total_newly_billed_native_children=24,total_newly_billed_wrappers=9,total_newly_billed_starts=33,planned_total_starts=72,
        remaining_nominal_seconds=68400,remaining_outer_overhead_seconds=1200,reserved_total_outer_seconds=b['paid_outer_seconds']+68400+1200,
        native_order_and_every_native_argv_unchanged=True,unknown_future_fault_stops=True,solver_calls=0))
    print('Nine explicit remaining wrappers frozen; paid18 once, no refund, no additional driver.')

def require_plan():
    q=read(OUT/'campaign/identity.json');p=read(PLAN)
    assert p['source_bindings']==source_hashes() and p['original_helpers']==old.helpers()==q['helpers']
    assert p['original_candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and p['original_campaign_identity_SHA']==sha(OUT/'campaign/identity.json')
    assert p['original_all42_native_argv']==[x['command'] for x in q['launches']]
    assert p['recovery_sidecar_SHA']==sha(ROOT/repair.SIDE) and p['supplemental_wrapper_argv']==wrapper_commands()
    assert p['planned_total_starts']==72 and p['remaining_outer_overhead_seconds']==1200
    return p,q

def run(n):
    ensure_idle();check_identity();p,q=require_plan();camp=OUT/'campaign'
    assert q['source_hashes']==bindings() and q['runner_sha256']==sha(ROOT/'scripts/round109_campaign.py')
    assert q['prereg_sha256']==sha(q['protocol_path'])
    raw_previous=old.records(camp);previous=repair.record_view(ROOT,raw_previous)
    assert len(previous)==n-1 and all(r['audit_passed'] for r in previous),'only next never-started arm with explicit known-fault proof'
    launch=q['launches'][n-1];assert not Path(launch['destination']).exists()
    assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    gate=read(OUT/'review/performance_admission_resumption02.json')
    assert gate['decision']=='ACCEPT' and gate['resumption_allowed'] is True
    assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and gate['campaign_identity_SHA']==sha(camp/'identity.json')
    assert gate['supplemental_wrapper_plan_SHA']==sha(PLAN) and gate['recovery_sidecar_SHA']==sha(ROOT/repair.SIDE)
    if n==18:
        coupon=check_coupon()
        write(COUPON,dict(coupon=coupon,consuming_wrapper='main07_prepaid01',number=18,original_fee_SHA=coupon['original_receipt_SHA'],
            native_command=launch['command'],supplemental_plan_SHA=sha(PLAN),signed_admission_SHA=sha(OUT/'review/performance_admission_resumption02.json'),
            new_native_start_charge=0,original_paid_slot_retained=True,consumed_once_before_actual_native_launch=True))
    else:
        consumption=read(COUPON);assert consumption['number']==18 and consumption['native_command']==q['launches'][17]['command']
        assert (Path(q['launches'][17]['destination'])/'launch.json').exists()
    old.supervisor.CAMPAIGN=camp;old.supervisor.audit_launch=old.seed_audit.adapter
    rec=old.supervisor.run_one(launch,q['prereg'],q)
    same=[r for r in previous+[rec] if r['id']==launch['id']]
    lower=[r['endpoint']['L'] for r in same];upper=[r['endpoint']['U'] for r in same if r['endpoint']['U'] is not None]
    assert not upper or max(lower)<=min(upper)+1e-7,'offline contradictory cross-arm physical/native evidence'
    write(camp/f'cross_arm_{launch["id"]}_{len(same)}.json',dict(strongest_L=max(lower),best_physical_U=min(upper) if upper else None,passed=True,
        scope='offline contradiction check only; explicitly computed known15/17 own-floor records; never combined certificate or injected knowledge',
        original_failed_summary_preserved=True,recovery_sidecar_SHA=sha(ROOT/repair.SIDE)))
    return rec

def billed(label,first,last):
    outer_tick,creation_unix=old.wrapper_start_tick();ensure_idle();check_identity();p,q=require_plan();b=budget()
    assert (label,first,last) in GROUPS and not b['unclosed'] and len(old.records(OUT/'campaign'))==first-1
    ix=GROUPS.index((label,first,last));children=last-first+1;prepaid=1 if first==18 else 0;charge=children+1-prepaid
    remaining=q['launches'][first-1:];remaining_starts=len(remaining)+len(GROUPS)-ix-prepaid
    nominal=sum(x['cap_seconds'] for x in remaining);overhead=1200 if ix==0 else 120*(len(GROUPS)-ix)
    assert b['remaining_starts']>=remaining_starts and b['remaining_outer_seconds']>=nominal+overhead
    if first==18:check_coupon()
    else:assert COUPON.exists()
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    command=wrapper_commands()[ix];group_nominal=sum(x['cap_seconds'] for x in q['launches'][first-1:last])
    write(d/'launch.json',dict(command=command,cwd=str(ROOT),conservative_process_starts=charge,declared_native_children=children,
        newly_billed_native_children=children-prepaid,prepaid_native_children=prepaid,actual_wrapper_processes=1,new_driver_processes=0,
        cap_seconds=group_nominal+120,budget_before=b,remaining_fixed_reserve=dict(starts=remaining_starts,nominal_seconds=nominal,overhead_seconds=overhead),
        wrapper_creation_unix=creation_unix,source_bindings=bindings(),helpers=old.helpers(),supplemental_sources=source_hashes(),
        supplemental_plan_SHA=sha(PLAN),recovery_sidecar_SHA=sha(ROOT/repair.SIDE),original_coupon=p['prepaid_coupon'] if prepaid else None,
        production_PE_SHA=old.PE_SHA,DLL_SHA=old.DLL_SHA,earlier_failed_fee_refunded=False,qualification=False))
    for source in list(old.helpers())+list(source_hashes()):
        target=d/'source_snapshot'/source;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/source).read_bytes())
    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=0;reason='normal_return'
    try:
        for n in range(first,last+1):
            arm_tick=time.perf_counter();launch=q['launches'][n-1]
            write(d/f'{n:02d}_before.json',dict(number=n,id=launch['id'],arm=launch['arm'],seed=launch['seed'],paid_original_slot=n==18))
            rec=run(n);write(d/f'{n:02d}_after.json',dict(completed_and_audited=True))
            dest=Path(launch['destination']);seconds=time.perf_counter()-arm_tick
            write(dest/'whole_arm_receipt.json',dict(number=n,id=rec['id'],arm=rec['arm'],seed=launch['seed'],complete_seconds=seconds,
                completion_SHA=sha(dest/'completion.json'),audit_SHA=sha(dest/'audit.json'),
                original_supervisor_observed_seconds=rec['completion']['fully_observed_end_to_end_seconds'],
                includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck=True,
                supplemental_wrapper_plan_SHA=sha(PLAN),prepaid_original_native_slot=n==18))
            assert seconds<=launch['cap_seconds'],'full arm exceeded frozen cap'
    except BaseException:
        code=1;reason='actual_exception';(d/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        value=dict(exit_code=code,outer_seconds=time.perf_counter()-outer_tick,stop_reason=reason,conservative_process_starts=charge,
            timing_basis='actual wrapper process creation through native/postexit audit/closure; nested seconds not added',
            actual_native_children_with_launch=sum((Path(x['destination'])/'launch.json').exists() for x in q['launches'][first-1:last]),
            prepaid_native_children=prepaid,newly_billed_native_children=children-prepaid,extra_driver_processes=0,earlier_fee_refunded=False)
        write(d/'receipt.json',value);print(json.dumps(value),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='plan':plan()
    elif sys.argv[1]=='billed':billed(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]))
    else:raise ValueError(sys.argv[1])
