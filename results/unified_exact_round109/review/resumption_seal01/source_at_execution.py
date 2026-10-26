"""Seal an actually executed independent admission supplement; no solver."""
from pathlib import Path
import argparse,contextlib,hashlib,json,runpy,sys,time,traceback
ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
ROOT=Path(args.root).resolve();OUT=ROOT/'results/unified_exact_round109';REVIEW=OUT/'review';DEST=Path(args.out).resolve();assert DEST.is_relative_to(REVIEW);DEST.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
tick=time.perf_counter();error=None;value={}
save(DEST/'launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=sha(__file__),Optimize=0,native_environment=0))
(DEST/'source_at_execution.py').write_bytes(Path(__file__).read_bytes())
try:
    auditdir=REVIEW/'resumption_raw_rebuild01';a=read(auditdir/'audit.json');receipt=read(auditdir/'receipt.json');r=a['resumption']
    assert a['decision']==r['decision']=='ACCEPT' and receipt['exit_code']==0 and receipt['audit_SHA']==sha(auditdir/'audit.json') and a['mode']=='resumption'
    assert len(a['arms'])==15 and len(a['qualification'])==5 and len(a['references'])==12 and len(a['bindings']['all42_complete_argv'])==42
    assert r['resumption_allowed_now'] and r['remaining_budget']['passed'] and a['reviewer_calls']['Optimize']==a['reviewer_calls']['native_environment']==0
    for key,path in [('candidate_identity_SHA',OUT/'candidate_identity.json'),('campaign_identity_SHA',OUT/'campaign/identity.json'),('qualification_identity_SHA',OUT/'qualification/identity.json')]:assert a[key]==sha(path)
    assert r['recovery']['sidecar_SHA']==sha(OUT/'campaign/reader_recovery/main05_numerical01.json')
    assert r['recovery']['primary_helper_SHA']==sha(ROOT/'scripts/round109_numerical_recovery.py') and r['recovery']['primary_reader_SHA']==sha(ROOT/'scripts/round109_reader.py')
    for rel,digest in a['bindings']['source_bindings'].items():assert sha(ROOT/rel)==digest
    for rel,digest in a['bindings']['helper_bindings'].items():assert sha(ROOT/rel)==digest
    assert sha(ROOT/'build/research/round109-inherited-mb-v1/ExactEBRP.exe')==a['bindings']['PE_SHA']
    assert sha('D:/gurobi1302/win64/bin/gurobi130.dll')==a['bindings']['DLL_SHA']
    assert r['original_performance_admission_SHA']==sha(REVIEW/'performance_admission.json')
    # Preserve the actual old stdout. The sole post-audit edit corrects its
    # internal cap-validation upper-bound label; no calculation changes.
    old=auditdir/'source_at_execution/round109_independent_kernel.py';new=REVIEW/'round109_independent_kernel.py'
    oldtext=old.read_text();newtext=new.read_text()
    before="complete_seconds=complete,events=len(observations)"
    after="complete_seconds=result['complete_seconds'],complete_seconds_interval=result.get('complete_seconds_interval'),events=len(observations)"
    assert before in oldtext and oldtext.replace(before,after)==newtext
    for name,digest in a['reviewer_sources'].items():
        if name!='round109_independent_kernel.py':assert sha(REVIEW/name)==digest
    logging=DEST/'logging_correction_actual_P_recheck';logging.mkdir()
    oldargv=sys.argv[:];sys.argv=[str(REVIEW/'round109_independent_raw.py'),'--root',str(ROOT),'--mode','final','--out',str(logging),'--dll','D:/gurobi1302/win64/bin/gurobi130.dll']
    kernel=runpy.run_path(str(REVIEW/'round109_independent_raw.py'));sys.argv=oldargv
    identity=read(OUT/'campaign/identity.json')
    with (logging/'stdout.log').open('x',encoding='utf-8') as stream,contextlib.redirect_stdout(stream):
        actual,_,_=kernel['audit_arm'](identity['launches'][14],identity,True)
    assert actual==a['arms'][14] and actual['complete_seconds'] is None
    printed=json.loads((logging/'stdout.log').read_text().strip());assert printed['complete_seconds'] is None and printed['complete_seconds_interval']==[1770.375,1771.833281]
    save(logging/'audit.json',dict(decision='ACCEPT',actual_affected_arm_exactly_equals_full_rebuild=True,actual_P=actual,source_SHA=sha(new),old_source_SHA=sha(old),diagnostic_logging_only_patch=True,Optimize=0,native_environment=0))
    correction=read(auditdir/'mechanism_correction01.json');assert correction['decision']=='ACCEPT_CORRECTION'
    correctionpath=REVIEW/'mechanism_correction01.json';assert not correctionpath.exists();correctionpath.write_bytes((auditdir/'mechanism_correction01.json').read_bytes())
    value=dict(decision='ACCEPT',resumption_allowed_now=True,scope='Next never-started fixed group only; all42 remain mandatory; no solver rerun or production/search/campaign-helper change',
        candidate_identity_SHA=a['candidate_identity_SHA'],campaign_identity_SHA=a['campaign_identity_SHA'],original_performance_admission_SHA=r['original_performance_admission_SHA'],qualification_identity_SHA=a['qualification_identity_SHA'],
        actual_independent_audit='results/unified_exact_round109/review/resumption_raw_rebuild01/audit.json',actual_independent_audit_SHA=sha(auditdir/'audit.json'),actual_independent_receipt_SHA=sha(auditdir/'receipt.json'),
        actual_independent_stdout_SHA=sha(REVIEW/'resumption_raw_rebuild01.stdout.log'),actual_independent_stderr_SHA=sha(REVIEW/'resumption_raw_rebuild01.stderr.log'),
        bound_sidecar_SHA=r['recovery']['sidecar_SHA'],bound_primary_helper_SHA=r['recovery']['primary_helper_SHA'],bound_primary_reader_SHA=r['recovery']['primary_reader_SHA'],
        production_PE_SHA=a['bindings']['PE_SHA'],DLL_SHA=a['bindings']['DLL_SHA'],all42_argv=a['bindings']['all42_complete_argv'],production_source_bindings=a['bindings']['source_bindings'],frozen_performance_helper_bindings=a['bindings']['helper_bindings'],
        completed_raw_formal_arms=15,completed_raw_qualification_arms=5,original_cold_references=12,completed_checks=a['completed_checks'],remaining_budget=r['remaining_budget'],
        recovery=r['recovery'],mechanism_correction_SHA=sha(correctionpath),mechanism_counts={'M-B':{'Optimize':4,'LP':3,'terminal_MIP':1},'ENS-C':{'Optimize':4,'LP':3,'terminal_MIP':1}},
        mechanism_correction='Previous human zeroOptimize/HGA-only account withdrawn. Both original and repeated independent kernels checked all4calls. ENS physical zero was native_MIPSOL call4, with returned OPTIMAL integer log and closed root coverage.',
        primary_rebuild_receipt_SHA=r['primary_rebuild_receipt_SHA'],primary_rebuild_tables=r['primary_rebuild_tables'],finite_audit_SHA=r['finite_audit_SHA'],finite_receipt_SHA=r['finite_receipt_SHA'],
        independent_pairs=r['independent_pairs'],original_failure_fee_SHA=r['recovery']['unmodified_native_failure_fee_SHA'],no_fee_refund=True,no_missing_receipt_fabricated=True,
        exact_P_complete_seconds=None,P_complete_seconds_interval=[1770.375,1771.833281],
        reviewer_stdout_correction='The original resumption debug line mislabeled the cap-validation upper bound as complete_seconds. Its archive is preserved; endpoint audit was already null. Sole logging patch and actual affected-arm recheck now output null plus interval; all arm fields exactly equal the full rebuild.',
        logging_patch_old_source_SHA=sha(old),current_reviewer_kernel_SHA=sha(new),actual_logging_recheck_SHA=sha(logging/'audit.json'),
        future_gate='Any new contradiction keeps the original stop guard. This is specific to call1 of frozen arm15, not authorization for generic native-bound substitution.',
        final42_selection_not_yet_made=True,reviewer_Optimize=0,reviewer_native_environment=0,production_edits=0)
    signed=REVIEW/'performance_admission_resumption01.json';assert not signed.exists();save(signed,value)
    save(DEST/'signed_receipt.json',dict(decision='ACCEPT',signed_path=str(signed.relative_to(ROOT)),signed_SHA=sha(signed),Optimize=0,native_environment=0))
    print(json.dumps(dict(decision='ACCEPT',signed_SHA=sha(signed),raw_audit_SHA=sha(auditdir/'audit.json'),reviewer_Optimize=0)),flush=True)
except Exception:
    error=traceback.format_exc();print(error,file=sys.stderr,flush=True)
save(DEST/'receipt.json',dict(exit_code=int(error is not None),decision='HOLD' if error else 'ACCEPT',elapsed_engineering_seconds=time.perf_counter()-tick,source_SHA=sha(__file__),Optimize=0,native_environment=0,error=error))
if error:sys.exit(1)
