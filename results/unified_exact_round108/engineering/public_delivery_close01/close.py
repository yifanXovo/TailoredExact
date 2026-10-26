"""Close delivery from the actually successful remote audit and stage metadata."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
here=Path(__file__).resolve().parent;root=here.parents[3];out=root/'results/unified_exact_round108'
start=time.perf_counter();verified=out/'engineering/public_remote_verify03/phase03';r=read(verified/'receipt.json')
assert r['exit_code']==0 and r['remote_draft'] and r['R107_latest_unchanged']
assert r['public_carrier_files_exact'] and r['PR_tables_exact_final_report'] and r['required_public_files_readable']
assert r['production_and_helpers_unchanged'] and r['original_user_changes_preserved']
assert r['combined_remote_archive_SHA']==read(out/'compact_evidence/manifest.json')['archive_sha256']
assert read(out/'review/public_isolated_review01.json')['decision']=='ACCEPT'
assert read(out/'public_comparison_receipt.json')['comparison']['passed']
before={name:sha(out/name) for name in ['RESUME.md','reproduce.md','delivery_checklist.md']}
resume=(out/'RESUME.md').read_text(encoding='utf-8')
old='The remaining delivery step is the new stacked draft PR and remote verification.'
assert resume.count(old)==1
resume=resume.replace(old,'Draft publication is complete: [Round108 PR #170](https://github.com/yifanXovo/TailoredExact/pull/170).\nThe new draft is attached to the chat. Actual remote verification passed at\nscientific delivery head `'+r['remote_head']+'`; this final supplement records that observed audit.')
old='Finish the new draft on R107, attach it to the chat and verify remote\nhead/base/draft, readable files, carrier bytes and PR tables.'
assert resume.count(old)==1
resume=resume.replace(old,'The new stacked draft and remote head/base/draft, readable files, exact carrier\nbytes and PR tables have passed actual verification. See\n`engineering/public_remote_verify03/phase03/receipt.json` and\n`public_delivery_receipt.json`. A later metadata-only delivery commit adds these\nreceipts and is verified again before the final reply; science, carrier and PR\nresult tables are unchanged by that supplement.')
(out/'RESUME.md').write_text(resume,encoding='utf-8',newline='\n')
checklist=(out/'delivery_checklist.md').read_text(encoding='utf-8')
old='| 11. New stacked draft and remote verification | The new Round108 draft will be created on the unchanged R107 branch after this concrete result is committed. Actual remote head/base/draft, readable files, compressed carrier SHA and exact PR tables must pass before marking the task complete. |'
assert checklist.count(old)==1
checklist=checklist.replace(old,'| 11. New stacked draft and remote verification | New [draft PR #170](https://github.com/yifanXovo/TailoredExact/pull/170) created on R107 and attached to the chat. Actual audit at '+r['remote_head']+' passed head/base/draft, unchanged latest R107, all 27 critical public file bytes, both carrier parts / combined SHA, and exact PR body/report tables. Receipt: engineering/public_remote_verify03/phase03/receipt.json. |')
checklist=checklist.replace('Publication remains a delivery step; no scientific experiment is pending.','Publication and remote verification passed. The final metadata-only supplement records these actual receipts; no scientific experiment is pending.')
(out/'delivery_checklist.md').write_text(checklist,encoding='utf-8',newline='\n')
append=f'''\n## Actual stacked draft publication and remote verification\n\nNew [Round108 draft PR #170](https://github.com/yifanXovo/TailoredExact/pull/170)\nwas created on `codex/round107-ens-frontier-route-events` and attached to the chat.\nScientific delivery commit: `{r['remote_head']}`; base `{r['remote_base']}`.\nThe actual remote audit returned exit 0 after {r['seconds']} seconds, with\nhead/base/draft and latest R107 unchanged, all 27 selected public file bytes\nreadable and exact, both compressed-byte parts and manifest actually downloaded\nand hashed, combined SHA `{r['combined_remote_archive_SHA']}`, and PR body\nexactly equal to its prepared report-derived text/tables. See\n`engineering/public_remote_verify03/phase03/receipt.json` / `file_checks.json`.\n\nThe first Git staging attempt rejected intended engineering logs under the\nexisting ignore rule. Its exact source/selected-path list and an honest failed\nreceipt are preserved in `public_stage01` / `public_stage02`; the retry used\nforce only on the explicit public allowlist. The first remote download attempt\nfailed MSYS Python CA verification; the second gh raw binary fetch returned\n`transform: short source buffer`. Their original sources, actual commands,\navailable outputs and failed receipts remain in `public_remote_verify01`–`03`.\nNeither failed script had a separately captured exact whole-script failure\ntimer; this is disclosed. The successful final client is Windows curl 8.13.0\nSchannel HTTPS, with certificate verification enabled and no proxy, CA or network\nconfiguration change. These publication checks perform zero solver/native calls.\n\nThis final metadata-only supplement publishes the observed successful audit and\ncurrent durable state. Its final remote head is verified again before delivery;\nall scientific decisions, raw carrier and PR result tables remain unchanged.\n'''
with (out/'reproduce.md').open('a',encoding='utf-8',newline='\n') as stream:stream.write(append)
delivery=dict(schema='round108-actual-delivery-v1',stage='SELECT_MB_FOR_BROAD_EVALUATION',
    PR_URL='https://github.com/yifanXovo/TailoredExact/pull/170',draft=True,base=r['remote_base'],
    verified_scientific_head=r['remote_head'],verified_remote_files=r['remote_files_checked'],
    actual_remote_verification_receipt_SHA=sha(verified/'receipt.json'),
    remote_carrier_SHA=r['combined_remote_archive_SHA'],remote_carrier_part_count=2,
    actual_public_math_review_SHA=sha(out/'review/public_isolated_review01.json'),
    actual_public_comparison_SHA=sha(out/'public_comparison_receipt.json'),
    formal_arms=21,failed_formal_arms=0,retries=0,cancelled_arms=0,unseen_WIN=3,unseen_LOSS=0,
    conservative_starts=46,outer_solver_fee_seconds=47514.073242100014,
    actual_public_recovery=True,actual_public_independent_review=True,
    independent_engine_performance_rerun=False,default_ENS_changed=False,
    final_supplement_scope='Delivery receipts and prose only; final remote head rechecked after this commit',
    engineering=True,Optimize=0,IIS=0,route_oracle=0)
write(out/'public_delivery_receipt.json',delivery)
files={out/name for name in ['RESUME.md','reproduce.md','delivery_checklist.md','public_delivery_receipt.json']}
for prefix in ['public_remote_verify01','public_remote_verify02','public_remote_verify03','public_delivery_close01']:
    files.update(p for p in (out/'engineering'/prefix).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
selected=sorted(p.relative_to(root).as_posix() for p in files)
command=['git','add','--force','--pathspec-from-file=-','--pathspec-file-nul']
child=subprocess.run(command,cwd=root,input=b''.join(p.encode()+b'\0' for p in selected),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
assert child.returncode==0,child.stderr.decode(errors='replace')
receipt=dict(actual_command=[sys.executable,str(Path(__file__).resolve())],exit_code=0,
    seconds=time.perf_counter()-start,source_SHA=sha(__file__),verified_head=r['remote_head'],
    before_SHA=before,after_SHA={name:sha(out/name) for name in before},
    published_delivery_receipt_SHA=sha(out/'public_delivery_receipt.json'),selected_paths=selected,
    staged_files=len(selected),metadata_and_prose_only=True,engineering=True,Optimize=0,IIS=0)
write(here/'receipt.json',receipt)
subprocess.run(['git','add','--force','--',(here/'receipt.json').relative_to(root).as_posix()],cwd=root,check=True)
print(json.dumps(dict(exit_code=0,staged_files=len(selected),verified_scientific_head=r['remote_head'])))
