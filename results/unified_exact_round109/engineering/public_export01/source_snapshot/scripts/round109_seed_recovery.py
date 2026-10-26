"""Recover the reader failure and consume the paid, never-started fifth CLI.

One new wrapper start, one child slot already conservatively paid in cli02.
Original failed audits/summary/fees survive byte-for-byte. No native rerun.
"""
from round109_common import *
import round109_campaign as campaign
import round109_seed_audit as audit
import shutil,traceback

def freeze(label='seed_reader_repair01'):
    from round100_idle import ensure_idle
    ensure_idle();check_identity();d=OUT/'engineering'/label;d.mkdir(parents=True,exist_ok=False)
    assert len(campaign.records(OUT/'qualification/cli01'))==4 and not (OUT/'campaign/summary.jsonl').exists()
    for name in ['campaign','qualification/cli01']:
        path=OUT/name/'identity.json';old=read(path);shutil.copyfile(path,d/(name.replace('/','_')+'_identity_before.json'))
        revised=dict(old,runner_sha256=sha(ROOT/'scripts/round109_campaign.py'),helpers=campaign.helpers())
        assert revised['launches']==old['launches']
        path.unlink();write(path,revised)
    path=OUT/'candidate_identity.json';old=read(path);shutil.copyfile(path,d/'candidate_identity_before.json')
    revised=dict(old,helpers=campaign.helpers(),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),planned_total_starts=72,
        starts_reserve=0,qualification_conservative_starts_with_failures=15,seed_reader_recovery=True,
        same_production_PE=True,all_42_argv_unchanged=True)
    path.unlink();write(path,revised)
    write(d/'repair.json',dict(production_or_search_change=False,raw_journal_bytes_and_global_flags_unchanged=True,
        reason='inherited evidenceParameterReadback returns false for actual Seed1 despite correct requested/effective readback',
        repair='strict normal-return parameter/matrix/type/scope/source/return proof; compatibility projection on in-memory copy only',
        helper_SHA=sha(ROOT/'scripts/round109_seed_scope.py'),candidate_identity_SHA=sha(path),
        all_42_argv_unchanged=True,formal_native_reruns=0,qualification_native_reruns=0,
        prepaid_child_slot='qualification_cli02 declared child5; launch05 absent at wrapper close',
        paid_failures_never_refunded=True,additional_wrapper_starts=1,qualification_starts=15,formal_starts=57,total_starts=72))
    print('strict evidence-only repair frozen; all42 argv unchanged; declared72 total starts')

def recover_fourth():
    camp=OUT/'qualification/cli01';identity=read(camp/'identity.json');launch=identity['launches'][3];dest=Path(launch['destination'])
    recs=campaign.records(camp);assert len(recs)==4 and not recs[3]['audit_passed']
    d=OUT/'qualification/seed_reader_recovery01';d.mkdir(parents=True,exist_ok=False)
    for name in ['audit.json','observations.json','completion.json','result.json']:
        if name=='audit.json':shutil.copyfile(dest/name,d/'failed_audit_before.json')
    shutil.copyfile(camp/'summary.jsonl',d/'failed_summary_before.jsonl')
    tick=time.perf_counter();audited=audit.adapter(launch,read(dest/'observations.json'),read(dest/'completion.json'),identity)
    assert audited['passed'];audited['offline_audit_seconds']=time.perf_counter()-tick
    audited['original_failed_audit_SHA']=sha(d/'failed_audit_before.json');audited['reader_only_recovery']=True
    (dest/'audit.json').unlink();write(dest/'audit.json',audited)
    recs[3].update(audit_passed=True,endpoint=audited['endpoint'],audit_error=None,
        original_failed_summary_SHA=sha(d/'failed_summary_before.jsonl'),reader_only_recovery=True)
    (camp/'summary.jsonl').unlink()
    with (camp/'summary.jsonl').open('x',encoding='utf-8',newline='\n') as f:
        for rec in recs:f.write(json.dumps(rec)+'\n')
    write(d/'recovery_receipt.json',dict(native_processes=0,proof_SHA=sha(dest/'computed_seed_scope.json'),
        old_audit_SHA=sha(d/'failed_audit_before.json'),new_audit_SHA=sha(dest/'audit.json'),
        old_summary_SHA=sha(d/'failed_summary_before.jsonl'),new_summary_SHA=sha(camp/'summary.jsonl'),
        full_fourth_qualification_arm_seconds='unknown: wrapper stopped before full receipt; legacy native/supervisor seconds retained',
        production_PE_SHA=PE_SHA,observations_SHA=sha(dest/'observations.json'),completion_SHA=sha(dest/'completion.json')))
    print('fourth actual CLI recovered strictly from same raw; no native rerun')

def finish_identity():
    camp=OUT/'qualification/cli01';identity=read(camp/'identity.json');recs=campaign.records(camp)
    assert len(recs)==5 and all(r['audit_passed'] for r in recs)
    import csv
    LPs=[];MIPs=[];starts=[]
    for rec in recs:
        d=Path(rec['destination']);obs=read(d/'observations.json')
        assert all(r['payload']['settings']==audit.expected(identity['launches'][rec['number']-1]['seed']) for r in obs if r['payload']['kind']=='call')
        if rec['arm']!='P-GRB':
            with (d/'external/paper_optimize_ledger.csv').open(newline='') as f:rows=list(csv.DictReader(f))
            LPs.append(any(r['solve_kind']=='LP' for r in rows));MIPs.append(any(r['solve_kind']!='LP' for r in rows))
            starts.extend(p.relative_to(ROOT).as_posix() for p in (d/'external/native_logs').glob('*.round68.start.json') if read(p).get('submitted'))
    assert all(LPs) and all(MIPs) and starts and any(r['endpoint']['certificate'] for r in recs)
    write(OUT/'qualification/identity.json',dict(passed=True,production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,source_bindings=bindings(),
        current_CLI_records=recs,qualified_argv=[x['command'] for x in identity['launches']],actual_seeds=[x['seed'] for x in identity['launches']],
        LP_reached=LPs,MIP_reached=MIPs,submitted_Starts=starts,legal_terminations=5,
        batch_export_receipt_SHA=sha(OUT/'qualification/batch_export_receipt.json'),qualification_campaign_identity_SHA=sha(camp/'identity.json'),
        qualification_not_performance=True,reader_only_seed_guard_recovery=True,raw_false_flags_retained=True,
        fourth_full_qualification_clock='unknown',fifth_prepaid_slot_review_SHA=sha(OUT/'review/seed_recovery_budget_review.json')))

def billed():
    outer,creation=campaign.wrapper_start_tick();campaign.ensure_idle();check_identity()
    review=read(OUT/'review/seed_recovery_budget_review.json');assert review['decision']=='ACCEPT'
    assert review['candidate_identity_SHA']==sha(OUT/'candidate_identity.json')
    old=read(OUT/'fees/qualification_cli02/receipt.json');assert old['actual_native_children_with_launch']==4
    assert old['conservative_process_starts']==6
    b=budget();reserve=campaign.full_remaining_reserve()
    assert not b['unclosed'] and b['remaining_starts']>=1+reserve['starts']
    assert b['remaining_outer_seconds']>=240+reserve['nominal_seconds']+reserve['overhead_seconds']
    identity=read(OUT/'qualification/cli01/identity.json');last=identity['launches'][4]
    assert not Path(last['destination']).exists()
    d=OUT/'fees/qualification_seed_recovery01';d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=[sys.executable,__file__,'billed'],cwd=str(ROOT),conservative_process_starts=1,
        declared_native_children=1,actual_wrapper_processes=1,wrapper_creation_unix=creation,
        prepaid_native_child=dict(fee='qualification_cli02',ordinal=5,receipt_SHA=sha(OUT/'fees/qualification_cli02/receipt.json'),
            never_started_verified=True,argv=last['command']),no_refund=True,no_double_native_fee=True,budget_before=b,
        all_remaining_fixed_reserve=reserve,source_bindings=bindings(),helpers=campaign.helpers(),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA))
    snapshots=d/'source_snapshot';snapshots.mkdir()
    for name in [*campaign.helpers(),'scripts/round109_seed_recovery.py']:
        target=snapshots/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=0
    try:
        recover_fourth();tick=time.perf_counter();rec=campaign.run('qualification/cli01',5,True)
        dest=Path(last['destination']);seconds=time.perf_counter()-tick
        write(dest/'whole_arm_receipt.json',dict(number=5,id=rec['id'],arm=rec['arm'],seed=1,complete_seconds=seconds,
            completion_SHA=sha(dest/'completion.json'),audit_SHA=sha(dest/'audit.json'),
            original_supervisor_observed_seconds=rec['completion']['fully_observed_end_to_end_seconds'],
            includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck=True))
        assert seconds<=120;finish_identity()
    except BaseException:
        code=1;(d/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        write(d/'receipt.json',dict(exit_code=code,outer_seconds=time.perf_counter()-outer,conservative_process_starts=1,
            stop_reason='normal_return' if code==0 else 'actual_exception',actual_native_children_with_launch=int((Path(last['destination'])/'launch.json').exists()),
            native_child_fee_already_in_qualification_cli02=True,nested_seconds_added=False))
    print('all5 actual CLI qualified; same PE; 15 prepaid/recovery qualification starts; 57 reserved formal starts')

if __name__=='__main__':
    if sys.argv[1]=='freeze':freeze(sys.argv[2] if len(sys.argv)>2 else 'seed_reader_repair01')
    elif sys.argv[1]=='billed':billed()
    else:raise ValueError(sys.argv[1])
