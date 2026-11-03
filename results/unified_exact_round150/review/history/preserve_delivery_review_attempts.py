"""Preserve two metadata-helper schema mistakes, without rerunning the helper."""
from pathlib import Path
import datetime,hashlib,json,time
tick=time.perf_counter();history=Path(__file__).resolve().parent;review=history.parent
attempts=[dict(source='check_delivery_metadata_before_index_accounting.py',
    process_outer_seconds=.1337639,exit_code=1,
    reason='Review helper assumed compressed_bytes meant seven zip files only. The actual aggregate correctly includes member_index.json.gz; adding its1414589 bytes closes23526310 exactly.',
    stderr='Traceback (most recent call last):\n  File "E:\\codes\\ExactEBRP-work\\worktrees\\paper-current\\results\\unified_exact_round150\\review\\check_delivery_metadata.py", line 35, in <module>\n    assert sum(a[\'bytes\'] for a in carriers[\'archives\'])==carriers[\'compressed_bytes\']==23526310\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nAssertionError\n'),
    dict(source='check_delivery_metadata_before_index_schema.py',
    process_outer_seconds=.1582769,exit_code=1,
    reason='Review helper assumed a top-level members key. The actual member index is a mapping from each archive path to its member list; the corrected metadata-only count sums those seven lists.',
    stderr='Traceback (most recent call last):\n  File "E:\\codes\\ExactEBRP-work\\worktrees\\paper-current\\results\\unified_exact_round150\\review\\check_delivery_metadata.py", line 39, in <module>\n    indexed_count=len(indexed) if isinstance(indexed,list) else len(indexed[\'members\'])\n                                                                    ~~~~~~~^^^^^^^^^^^\nKeyError: \'members\'\n')]
for number,attempt in enumerate(attempts,1):
    attempt['source_SHA256']=hashlib.sha256((history/attempt['source']).read_bytes()).hexdigest()
    name=f'delivery_metadata_attempt{number}_stderr_from_tool_transcript.txt'
    (history/name).write_text(attempt.pop('stderr'),encoding='utf-8');attempt['stderr_file']=name
    attempt['stderr_SHA256']=hashlib.sha256((history/name).read_bytes()).hexdigest()
receipt=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),attempts=attempts,
    actual_artifact_defect=False,scientific_conclusion_changed=False,pure_delivery_IO=True,
    no_archive_download_or_open=True,Native_load=0,Optimize=0,compile=0,
    old_helper_executed_again=False,known_total_delivery_IO_process_seconds_before_this_history_write=3.3007142)
(history/'delivery_metadata_attempts.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
path=review/'delivery_metadata_review.json';value=json.loads(path.read_text(encoding='utf-8'))
value['metadata_only_helper_attempts']='review/history/delivery_metadata_attempts.json'
value['all_failed_metadata_attempts_preserved']=True
value['observed_pure_delivery_IO_process_seconds_before_history_write']=3.3007142
value['metadata_attempt_errors_were_reviewer_schema_assumptions_not_carrier_defects']=True
path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(history_preserved=True,seconds=time.perf_counter()-tick,Optimize=0)))
