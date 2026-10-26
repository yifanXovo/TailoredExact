"""Record actual publication completion after the remote payload check; zero solver work."""
from pathlib import Path
import hashlib,json,subprocess,time
ROOT=Path(__file__).absolute().parents[1] if Path(__file__).parent.name=='tmp' else Path(__file__).absolute().parents[4]
OUT=ROOT/'results/unified_exact_round107'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
pub=OUT/'review/publication03'
verification=read(pub/'result.json')
assert verification['status']=='PASS_REMOTE_DRAFT_AND_EXACT_PUBLIC_PAYLOAD'
assert verification['production_source_bindings_checked']==205 and verification['public_file_count']==62
assert verification['Optimize_calls']==0 and verification['IIS_calls']==0
url=verification['PR']['url']
fields='url,title,body,baseRefName,headRefName,headRefOid,state,isDraft'
command=['gh','pr','view',url,'--json',fields]
write(pub/'PR_metadata_before.json',dict(command=command,Optimize_calls=0,IIS_calls=0))
tick=time.perf_counter()
process=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(pub/'PR_metadata_stderr.log').write_bytes(process.stderr)
assert process.returncode==0
pr=json.loads(process.stdout)
expected=(ROOT/'tmp/round107_pr_body.md').read_text(encoding='utf-8')
assert pr['body'].replace('\r\n','\n').rstrip()==expected.rstrip()
assert pr['title']=='[Research R107] Scope STRUCT events through ENS-C; full eight-arm negative result'
assert pr['headRefOid']==verification['verified_payload_commit']
assert pr['baseRefName']=='codex/round106-structural-conflict-events' and pr['isDraft'] and pr['state']=='OPEN'
(pub/'PR_body.md').write_bytes((ROOT/'tmp/round107_pr_body.md').read_bytes())
write(pub/'PR_metadata_after.json',dict(PR=pr,returncode=process.returncode,engineering_seconds=time.perf_counter()-tick,body_matches_exact_authored_text=True,body_file_SHA=digest(pub/'PR_body.md'),Optimize_calls=0,IIS_calls=0))
frozen={str(p.relative_to(ROOT)):digest(p) for p in [OUT/'final_report.md',OUT/'admission_decision.json',ROOT/'scripts/round107_reader.py',ROOT/'scripts/round107_restore.py',OUT/'compact_evidence/manifest.json',OUT/'compact_evidence/parts_manifest.json']}
resume=OUT/'RESUME.md'
s=resume.read_text(encoding='utf-8')
old='Remaining delivery work is the verified new stacked draft PR.'
assert old in s
s=s.replace(old,f'New stacked draft PR: {url}, base codex/round106-structural-conflict-events. Remote draft/base/head and all 62 selected public files (including all seven compact parts and 205 production source bindings) were verified at payload commit {verification["verified_payload_commit"]}. Subsequent committed changes only record publication receipts and completion metadata. No research, native performance or restoration work remains.')
resume.write_text(s,encoding='utf-8',newline='\n')
reproduce=OUT/'reproduce.md'
s=reproduce.read_text(encoding='utf-8')
assert '## Executed remote publication verification' not in s
s+=f'\n## Executed remote publication verification\n\nThe new stacked draft PR is [{url}]({url}), based on `codex/round106-structural-conflict-events` at `0350dbcc60d1c68e5c499d2e9880ecc1deaf031c`. Actual GitHub read APIs verified the draft/open state, head/base and all 62 selected public files at payload commit `{verification["verified_payload_commit"]}`. Every file matched its committed blob identity, byte length and SHA256; this includes all seven Round107 parts, manifests, reader/restorer, all authoritative tables and principal reports/protocols/reviews. All 205 production source bindings matched. The PR body was fetched and compared with the exact authored English text.\n\nActual per-file request before/after records, errors, SHA, lengths and zero-solver engineering receipts are in `review/publication03/` and `engineering/publication_verify03/`. The receipt pins the verified payload commit above; the later commit publishes those executed receipts and updates completion/handoff/reproduction metadata and the delivery-only verifier traversal. It does not alter the measured source, reader, carrier, tables, frozen performance decision or reviewed final report. The final remote metadata head is checked after that follow-up push, without repeating native solving or the already passed evidence reconstruction.\n'
s+='\nThe first remote verifier attempt rejected GitHub\'s explicitly truncated whole-repository recursive tree (3.810808 engineering seconds, 0 solver calls). The corrected verifier walks only required directories using exact parent tree SHA, then fetches and hashes actual file bytes over verified HTTPS. A second gh raw-binary attempt failed with `transform: short source buffer` (18.624458 engineering seconds); its two-byte output was rejected, and exact source/logs/receipt remain in `review/publication02/` and `engineering/publication_verify02/`. The successful verifier uses native curl for exact raw bytes. The first failed source and receipt are retained in `review/publication01/` and `engineering/publication_verify01/`; no measured production, raw evidence, carrier or reader changed.\n'
reproduce.write_text(s,encoding='utf-8',newline='\n')
c=read(OUT/'completion_checklist.json')
assert c['status']=='EVIDENCE_COMPLETE_PUBLICATION_PENDING'
assert all(x['status']=='COMPLETE' for x in c['requirements'])
c['status']='COMPLETE'
c['draft_PR_creation_and_remote_payload_verification']='COMPLETE'
c['publication']=dict(PR_url=url,base_branch=pr['baseRefName'],base_commit=verification['base_commit'],head_branch=pr['headRefName'],isDraft=pr['isDraft'],PR_state=pr['state'],verified_payload_commit=verification['verified_payload_commit'],exact_public_files_verified=62,production_source_bindings_verified=205,publication_result_path='review/publication03/result.json',publication_result_SHA=digest(pub/'result.json'),PR_body_SHA=digest(pub/'PR_body.md'),metadata_followup_scope='Actual publication receipts, delivery-only verifier and completion/handoff/reproduction metadata only; scientific payload remains pinned to verified_payload_commit.')
c['requirements'].append(dict(requirement='13_new_stacked_draft_PR_actual_remote_bytes',status='COMPLETE',evidence=[dict(path='review/publication03/result.json'),dict(path='review/publication03/PR_metadata_after.json'),dict(path='review/publication03/PR_body.md')]))
for requirement in c['requirements']:
    for evidence in requirement['evidence']:
        evidence['sha256']=digest(OUT/evidence['path'])
c['recorded_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
write(OUT/'completion_checklist.json',c)
for relative,expected_SHA in frozen.items():assert digest(ROOT/relative)==expected_SHA,relative
write(pub/'completion_metadata_result.json',dict(status='PASS_ACTUAL_PUBLICATION_COMPLETION_METADATA',PR_url=url,verified_payload_commit=verification['verified_payload_commit'],checklist_status=c['status'],frozen_payload_SHA=frozen,updated_metadata_files=['results/unified_exact_round107/RESUME.md','results/unified_exact_round107/reproduce.md','results/unified_exact_round107/completion_checklist.json'],actual_public_files_verified=62,production_source_bindings_checked=205,retained_failed_verifications=["review/publication01/failure.json","review/publication02/failure.json"],Optimize_calls=0,IIS_calls=0,paid_starts=0))
print(json.dumps(dict(status=c['status'],PR_url=url,verified_payload_commit=verification['verified_payload_commit'],Optimize_calls=0,IIS_calls=0)))