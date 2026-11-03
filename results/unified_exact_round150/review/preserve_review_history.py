"""Preserve an exact earlier review helper using its known edit; never run it."""
from pathlib import Path
import datetime,hashlib,json,time
tick=time.perf_counter();review=Path(__file__).resolve().parent;history=review/'history';history.mkdir(exist_ok=True)
current=review/'independent_final_check.py';raw=current.read_bytes()
removed=(b'        # Trucks start empty; residual return load is unloaded at the depot\n'
         b'        # and pays the same drop handling time in the original physical model.\n'
         b'        handling+=60*load\n')
assert raw.count(removed)==1
initial=raw.replace(removed,b'')
digest=hashlib.sha256(initial).hexdigest()
assert digest=='c781ff05e8431ab31f9f5cd8d1ca41df09b49bbb74d6f94477fab0d19bbb11ae'
target=history/'independent_final_check_before_depot_drop.py'
target.write_bytes(initial)
assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
stdout='{"PASS": true, "independent_nonimplementer_review": true, "UTC": "2026-11-03T16:22:39.588821+00:00", "Native_load": 0, "Optimize": 0, "compile": 0, "new_baseline_solve": 0, "elapsed_seconds": 1.279126500012353, "independent_script_SHA": "c781ff05e8431ab31f9f5cd8d1ca41df09b49bbb74d6f94477fab0d19bbb11ae", "observed_cost_before_final_review_charge": 5543.6389105000735, "final_review_charge_pending": true, "exact_rational_LP_optimality_claimed": false, "public_delivery_not_yet_verified": true}\n'
(history/'initial_helper_stdout_from_tool_transcript.txt').write_text(stdout,encoding='utf-8')
receipt=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    disposition='REVIEW_HELPER_UNDERCHECK_CORRECTED_ON_THE_SAME_IMMUTABLE_EVIDENCE',
    original_source_recovered=True,recovery='Reverse only the exactly known three-line depot-drop insertion and require the original SHA; do not execute the recovered helper.',
    initial_source=target.name,initial_source_SHA256=digest,initial_bytes=len(initial),
    original_stdout_recovered_from='Existing tool transcript, cell result chunk e52de3',
    original_stdout_file='initial_helper_stdout_from_tool_transcript.txt',
    original_stdout_SHA256=hashlib.sha256((history/'initial_helper_stdout_from_tool_transcript.txt').read_bytes()).hexdigest(),
    initial_process_exit_code=0,initial_process_outer_seconds=1.3961074,
    initial_script_nested_seconds=1.279126500012353,
    actual_original_error_message=None,
    explanation='The initial process returned PASS under an incomplete independent duration check. There was no traceback or nonzero-return failure. Inspection against the accepted physical verification revealed the helper omitted drop handling for residual vehicle load unloaded at the depot. Treat this as a review qualification defect, not a failed producer or a failed Optimize. The corrected helper was subsequently run against the same immutable saved records and passed.',
    initial_helper_limitation='Independent reconstructed duration omitted60 seconds per returned bike. Native/main physical verification already included this depot handling.',
    corrected_source='review/independent_final_check.py',
    corrected_source_SHA256=hashlib.sha256(raw).hexdigest(),
    corrected_process_outer_seconds=1.3362286,
    Native_load=0,Optimize=0,compile=0,old_helper_executed_again=False,new_qualification=False,
    frozen_science_data_changed=False,review_conclusion_changed=False,
    original_and_corrected_process_fees_already_disclosed_once=True,
    evidence_preservation_IO_separate=True,IO_seconds_before_receipt_serialization=time.perf_counter()-tick)
(history/'initial_helper_defect_preservation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(preserved=True,initial_source_SHA256=digest,seconds=time.perf_counter()-tick,Optimize=0,Native_load=0)))
