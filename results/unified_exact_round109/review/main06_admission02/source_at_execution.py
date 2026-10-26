"""Actually reconstruct known15, ENS16 and own-zero17, then seal bounded admission.
All core math is independent; primary completed tables only corroborate results.
"""
from pathlib import Path
import argparse,hashlib,json,math,runpy,sys,time,traceback
ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--sidecar',required=True);ap.add_argument('--plan',required=True);ap.add_argument('--reports',required=True);ap.add_argument('--rebuild-receipt',required=True);ap.add_argument('--finite-audit',required=True);ap.add_argument('--finite-receipt',required=True);args=ap.parse_args()
ROOT=Path(args.root).resolve();OUT=ROOT/'results/unified_exact_round109';REVIEW=OUT/'review';DEST=Path(args.out).resolve();assert DEST.is_relative_to(REVIEW);DEST.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def path(relative):
    p=(ROOT/relative).resolve();assert p.is_relative_to(ROOT);return p
tick=time.perf_counter();error=None;value={};save(DEST/'launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=sha(__file__),Optimize=0,native_environment=0));(DEST/'source_at_execution.py').write_bytes(Path(__file__).read_bytes())
try:
    rawargv=sys.argv[:];sys.argv=[str(REVIEW/'round109_independent_raw.py'),'--root',str(ROOT),'--mode','final','--out',str(DEST),'--dll','D:/gurobi1302/win64/bin/gurobi130.dll']
    core=runpy.run_path(str(REVIEW/'round109_independent_raw.py'));sys.argv=rawargv
    sources=DEST/'reviewer_source_at_execution';sources.mkdir()
    for name in ['round109_independent_raw.py','round109_independent_kernel.py','round109_independent_parser.py','round109_independent_decision.py','round109_independent_seed_scope.py','round109_independent_numerical.py','round109_independent_main06.py']:(sources/name).write_bytes((REVIEW/name).read_bytes())
    protocol,manifest,inputs=core['frozen_protocol']();candidate,identity=core['current_bindings']();launches=core['bind_launches'](identity,manifest);refs=core['audit_references'](manifest)
    qidentity=core['obj'](OUT/'qualification/cli01/identity.json');qreceipt=core['obj'](OUT/'qualification/identity.json');qualification=[]
    assert qreceipt['passed'] and len(qidentity['launches'])==5
    for launch in qidentity['launches']:
        a,_,_=core['audit_arm'](launch,qidentity,False);qualification.append(a);core['cache'].clear()
    arms=[]
    for number in (15,16,17):
        a,_,_=core['audit_arm'](launches[number-1],identity,True);arms.append(a);core['cache'].clear()
    old15,ens,plain=arms;sidepath=path(args.sidecar);side=read(sidepath);planpath=path(args.plan);plan=read(planpath);contract=read(REVIEW/'main06_recovery_contract_review01.json')
    assert old15['L']==0 and old15['certificate'] is False and old15['complete_seconds'] is None and old15['independent_numerical_recovery']['current_bridge_SHA']==sha(sidepath)
    assert ens['certificate'] is True and ens['U']==0 and plain['certificate'] is True and plain['U']==plain['L']==plain['gap']==0
    assert plain['independent_main06_recovery']['sidecar_SHA']==sha(sidepath) and plain['native_return_journal_sequence'] is None and plain['raw_audit_passed'] is False
    assert side['complete_own_physical_zero_certificate'] and side['qualified_L']==0 and side['raw_returned_journal_sequence'] is None and side['raw_failure_sequence']==142
    assert side['current_reader_source_bindings']==plan['source_bindings']
    for rel,digest in plan['source_bindings'].items():assert sha(ROOT/rel)==digest
    assert plan['original_candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and plan['original_campaign_identity_SHA']==sha(OUT/'campaign/identity.json') and plan['recovery_sidecar_SHA']==sha(sidepath)
    assert plan['original_all42_native_argv']==[l['command'] for l in launches] and plan['original_helpers']==identity['helpers']
    expected_groups=[('main07_prepaid01',18,21),('main08',22,24),('main09',25,27),('main10',28,30),('main11',31,33),('main12',34,36),('seed01',37,38),('seed02',39,40),('seed03',41,42)]
    expected_commands=[[sys.executable,str(ROOT/'scripts/round109_prepaid_wrapper.py'),'billed',label,str(first),str(last)] for label,first,last in expected_groups]
    assert [[str(x).replace('\\','/') for x in v] for v in plan['supplemental_wrapper_argv']]==[[str(x).replace('\\','/') for x in v] for v in expected_commands]
    assert plan['remaining_native_numbers']==list(range(18,43)) and all(not core['under_root'](l['destination']).exists() for l in launches[17:])
    assert not (OUT/'campaign/reader_recovery/prepaid18_consumption01.json').exists() and not (OUT/'fees/main06/18_before.json').exists()
    coupon=plan['prepaid_coupon'];fee=read(OUT/'fees/main06/receipt.json');assert coupon==side['prepaid_coupon']==contract['prepaid_coupon']
    assert coupon['original_fee']=='main06' and coupon['ordinal']==3 and coupon['original_number']==18 and coupon['command']==launches[17]['command'] and coupon['no_refund'] and coupon['consume_once'] and coupon['original_receipt_SHA']==sha(OUT/'fees/main06/receipt.json')
    assert fee['exit_code']==1 and fee['actual_native_children_with_launch']==2 and fee['conservative_process_starts']==4
    fees=[]
    for f in sorted((OUT/'fees').glob('*/receipt.json')):
        r=read(f);l=read(f.parent/'launch.json');assert r['conservative_process_starts']==l['conservative_process_starts'];fees.append(dict(label=f.parent.name,receipt_SHA=sha(f),launch_SHA=sha(f.parent/'launch.json'),**r))
    starts=sum(f['conservative_process_starts'] for f in fees);seconds=sum(f['outer_seconds'] for f in fees)
    assert starts==39 and abs(seconds-11659.298868327402)<=1e-8
    assert plan['new_driver_processes']==0 and plan['remaining_original_wrappers']==9 and plan['total_newly_billed_native_children']==24 and plan['total_newly_billed_wrappers']==9 and plan['total_newly_billed_starts']==33 and plan['planned_total_starts']==72
    assert plan['first_wrapper_actual_children']==4 and plan['first_wrapper_newly_billed_children']==3 and plan['first_wrapper_newly_billed_starts']==4 and plan['prepaid18_new_charge']==0 and plan['original_main06_starts_retained']==4
    assert sum(l['cap_seconds'] for l in launches[17:])==plan['remaining_nominal_seconds']==68400 and plan['remaining_outer_overhead_seconds']==1200 and starts+33==72 and seconds+68400+1200<100000
    # Actual finite and whole primary rebuild must already have closed.
    freceiptpath=path(args.finite_receipt);freceipt=read(freceiptpath);fa=read(path(args.finite_audit));rp=path(args.rebuild_receipt);rr=read(rp)
    for receipt,folder in [(freceipt,freceiptpath.parent),(rr,rp.parent)]:assert receipt['exit_code']==0 and receipt['engineering'] and receipt['conservative_solver_starts']==0 and receipt['stdout_SHA']==sha(folder/'stdout.log') and receipt['stderr_SHA']==sha(folder/'stderr.log') and not (folder/'stderr.log').read_text().strip()
    assert fa['decision']=='ACCEPT' and fa['zero_Optimize'] and fa['zero_native_environment'] and fa['sidecar_SHA']==sha(sidepath) and fa['supplemental_plan_SHA']==sha(planpath) and fa['source_bindings']==plan['source_bindings']
    assert all(v['rejected'] for v in fa['cases']) and fa['checks']==len(fa['cases'])+len(fa['interval_pair_cases'])
    for receipt in (freceipt,rr):
        captured={s['path']:s['SHA'] for s in receipt['sources']}
        for rel,digest in plan['source_bindings'].items():assert captured[rel]==digest
    reports=path(args.reports);tables=core['rows'](reports/'arms.csv');native=core['rows'](reports/'native_calls.csv');summary=read(reports/'summary.json')
    assert len(tables)==summary['formal_arms']==3 and summary['conservative_starts']==39 and summary['independently_proved_actual_native_returns_without_journal']==1 and summary['actual_native_returns_including_independent_rc_sources']==summary['actual_Optimize']
    baseline=OUT/'reports_main06_recovery01';baseline_rows=core['rows'](baseline/'arms.csv');baseline_summary=read(baseline/'summary.json');baseline_receipt=read(OUT/'engineering/main06_reader_rebuild01/receipt.json')
    assert len(baseline_rows)==baseline_summary['formal_arms']==17 and baseline_summary['functional_qualification_arms']==5 and baseline_summary['actual_Optimize']==69 and baseline_summary['actual_native_returns_including_independent_rc_sources']==69 and baseline_receipt['exit_code']==0
    for a in arms:
        b=next(v for v in tables if (v['id'],v['arm'])==(a['id'],a['arm']))
        assert abs(float(b['U'])-a['U'])<=1e-7 and abs(float(b['L'])-a['L'])<=1e-7 and (b['certificate']=='True')==a['certificate']
        assert (b['complete_seconds']=='' if a['complete_seconds'] is None else abs(float(b['complete_seconds'])-a['complete_seconds'])<=1e-9)
        if a['complete_seconds'] is None:assert json.loads(b['complete_seconds_interval'])==a['complete_seconds_interval']
        before=next(v for v in baseline_rows if (v['id'],v['arm'])==(a['id'],a['arm']))
        assert [before[k] for k in ['U','L','gap','certificate','complete_seconds','complete_seconds_interval']]==[b[k] for k in ['U','L','gap','certificate','complete_seconds','complete_seconds_interval']]
    pn=next(v for v in native if (v['id'],v['arm'])==('G50-C2','P-GRB'));assert pn['returned']=='False' and pn['returned_journal_missing']=='True' and pn['actual_normal_return_from_independent_rc_source']=='True' and pn['native_bounds_mathematically_qualified']=='False'
    pair=core['decision']['pair'](ens,plain);published=next(v for v in core['rows'](reports/'pairs.csv') if (v['id'],v['candidate'],v['control'])==('G50-C2','ENS-C','P-GRB'))
    assert pair['classification']=='WIN' and pair['severe_regression'] is False and pair['certified_time_ratio'] is None and pair['control_seconds'] is None
    assert published['classification']==pair['classification'] and published['severe_regression']=='False' and published['control_seconds']==published['certified_time_ratio']=='' and json.loads(published['certified_time_ratio_interval'])==pair['certified_time_ratio_interval']
    ip=read(REVIEW/'interval_independent_finite02/audit.json');assert ip['decision']=='ACCEPT' and ip['subject_SHA']==sha(ROOT/'scripts/round109_interval_pairs.py')
    value=dict(decision='ACCEPT',resumption_allowed=True,candidate_identity_SHA=sha(OUT/'candidate_identity.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),supplemental_wrapper_plan_SHA=sha(planpath),recovery_sidecar_SHA=sha(sidepath),
        original_performance_admission_SHA=sha(REVIEW/'performance_admission.json'),previous_resumption_admission_SHA=sha(REVIEW/'performance_admission_resumption01.json'),production_PE_SHA=candidate['production_PE_SHA'],DLL_SHA=candidate['DLL_SHA'],source_bindings=candidate['source_bindings'],original_frozen_helpers=identity['helpers'],supplemental_source_bindings=plan['source_bindings'],all42_argv=[l['command'] for l in launches],
        own_actual_arms=arms,own_qualification=qualification,own_references=refs,own_input_physical_checks=inputs,own_ENS_P_interval_pair=pair,own_completed_checks=core['require'].__globals__['count'],
        paid_fees=fees,paid_starts=starts,paid_outer_seconds=seconds,remaining_native25=25,prepaid18_coupon=coupon,new_native_fees=24,new_wrappers=9,total_starts=72,remaining_nominal_seconds=68400,remaining_overhead_seconds=1200,
        primary_rebuild_receipt_SHA=sha(rp),primary_full17_baseline_receipt_SHA=sha(OUT/'engineering/main06_reader_rebuild01/receipt.json'),primary_full17_baseline_summary_SHA=sha(baseline/'summary.json'),primary_current_affected_projection_only=True,primary_finite_audit_SHA=sha(path(args.finite_audit)),primary_finite_receipt_SHA=sha(freceiptpath),own_interval_finite_SHA=sha(REVIEW/'interval_independent_finite02/audit.json'),
        reviewer_source_bindings={p.name:sha(p) for p in sources.iterdir()},read_bindings=core['reads'],original_failed_audit_returned_and_whole_clock_missing_preserved=True,no_refund=True,no_extra_driver=True,no_old_native_rerun=True,
        scope='Only exact remaining serial25native via9bound wrappers, beginning18/19/20/21 with unique prepaid18slot; everyothernewfault stillstop. Final42decision remains pending.',Optimize=0,native_environment=0,production_edits=0,engineering_elapsed_seconds=time.perf_counter()-tick)
    save(DEST/'audit.json',value);target=REVIEW/'performance_admission_resumption02.json';assert not target.exists();target.write_bytes((DEST/'audit.json').read_bytes());print(json.dumps(dict(decision='ACCEPT',signed_SHA=sha(target),checks=value['own_completed_checks'])),flush=True)
except Exception:
    error=traceback.format_exc();save(DEST/'audit.json',dict(decision='HOLD',error=error));print(error,file=sys.stderr,flush=True)
save(DEST/'receipt.json',dict(exit_code=int(error is not None),decision='HOLD' if error else 'ACCEPT',engineering_elapsed_seconds=time.perf_counter()-tick,source_SHA=sha(__file__),audit_SHA=sha(DEST/'audit.json'),Optimize=0,native_environment=0))
if error:sys.exit(1)
