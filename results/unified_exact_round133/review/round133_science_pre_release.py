"""Bind the reviewed science, without claiming future delivery checks pass."""
from pathlib import Path
import datetime,hashlib,json,re,time
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round133'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def table(text,marker,count):
    block=text[text.index(marker):].splitlines();found=[];started=False
    for line in block:
        if line.startswith('|'):
            started=True
            fields=[x.strip() for x in line.strip('|').split('|')]
            if fields[0].startswith('Role') or fields[0].startswith('---'):continue
            found.append(fields)
        elif started:break
    assert len(found)==count,(marker,len(found));return found
def main():
    tick=time.perf_counter();review=OUT/'review';prose=read(OUT/'prose_science_tense_check.json')
    docs={name:row['SHA256'] for name,row in prose['outputs'].items()}
    for name,digest in docs.items():assert sha(OUT/name)==digest,name
    assert docs['manuscript.md']=='76d176cb883a88b64d27b43f1994d66f5dd337f9bcc579540b91b707324c93ff'
    assert prose['scientific_results_unchanged'] and prose['planned_restore_not_claimed_executed']
    text=(OUT/'manuscript.md').read_text(encoding='utf-8')
    bib=(OUT/'references.bib').read_text(encoding='utf-8')
    entries=re.findall(r'^@\w+\{([^,]+),',bib,re.M);assert len(entries)==len(set(entries))
    citations=set(re.findall(r'@([A-Za-z][A-Za-z0-9_:-]*)',text));assert citations<=set(entries),citations-set(entries)
    a1=read(OUT/'reports/D1/arms.json')['arms'];a3=read(OUT/'reports/D3/arms.json')['arms']
    assert len(a1)==14 and len(a3)==8
    d1={(a['id'],a['seed'],a['method']):a for a in a1}
    for row in table(text,'**Table Q2.',14):
        role,seed,method=[x.strip() for x in row[0].split('/')];a=d1[(role,int(seed),method)]
        expected='CERT' if a['certificate'] else 'SOURCE_REJECTED / safe OPEN' if a['source_reduced'] else 'qualified OPEN'
        assert row[1]==expected and float(row[2])==float(format(a['signed_gap'],'.6g'))
        for col,key in [(3,'T_produce'),(4,'T_verify'),(5,'T_total')]:assert float(row[col])==float(format(a[key],'.3f'))
        assert row[6]=='null' if a['T_cert'] is None else float(row[6])==float(format(a['T_cert'],'.3f'))
    d3={(a['id'],a['seed'],a['version']=='candidate'):a for a in a3}
    for row in table(text,'**Table Q3.',8):
        role,seed,method,version=[x.strip() for x in row[0].split('/')];assert method=='S2'
        a=d3[(role,int(seed),version=='candidate')];assert row[1]=='CERT'
        assert float(row[2])==float(format(a['signed_gap'],'.6g'))
        for col,key in [(3,'T_produce'),(4,'T_verify'),(5,'T_total'),(6,'T_cert')]:assert float(row[col])==float(format(a[key],'.3f'))
    pairs={(a['id'],a['seed']):a for a in read(OUT/'reports/D3/pairs.json')['pairs']}
    for row in table(text,'**Table Q4.',4):
        role,seed=[x.strip() for x in row[0].split('/')];p=pairs[(role,int(seed))]
        assert float(row[1])==float(format(p['right_T_cert'],'.3f')) and float(row[2])==float(format(p['left_T_cert'],'.3f'))
        assert float(row[3])==float(format(p['left_minus_right_seconds'],'.6f')) and row[4]==p['direction'] and row[5]=='TIME_CLOSE'
    d1_review=read(review/'D1_completion_review.json');d3_review=read(review/'D3_completion_review.json')
    assert d1_review['formal_positions']==14 and d1_review['implementation_qualified']==14 and d1_review['native_source_qualified']==13
    assert d3_review['actual_positions']==8 and d3_review['certificates']==8 and d3_review['UNEVALUABLE']==0
    candidate_path=OUT/'candidate_manifest.json';candidate=read(candidate_path)
    matrices={stage:sha(OUT/'plans'/f'{stage}_matrix_frozen.json') for stage in ('D1','D3')}
    assert matrices['D1']==d1_review['matrix_SHA'] and matrices['D3']==d3_review['matrix_SHA']
    for stage in ('D1','D3'):
        for group in read(OUT/'plans'/f'{stage}_matrix_frozen.json')['groups']:
            d=Path(group['launch']['destination']);assert (d/'verification_closeout.json').is_file() and (d/'round133_endpoint.json').is_file()
    amendment=read(OUT/'plans/postverify_handoff_repair_amendment.json')
    adapter_SHA=sha(ROOT/'scripts/round133_postverify_repair.py');assert adapter_SHA==amendment['bindings']['adapter_SHA']
    docs.update({name:sha(OUT/name) for name in ['joint_objective_gap_note.md','historical_impact.md','historical_impact.json','references.bib','reproducibility.md','delivery_plan.json']})
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    detailed=dict(schema='round133-independent-pre-release-science-review-v1',UTC=now,reviewer='/root/reliability_review',decision='ACCEPT_SCIENTIFIC_PAYLOAD_ONLY',
        science_documents=docs,reviewed_manuscript_change_from_R132='127 added /18 removed lines; numerical source, qualification/bridge and exact objective-gap amendments',
        independently_checked_tables=dict(Q2_positions=14,Q3_positions=8,Q4_pairs=4,display_precision_matches_raw=True,negative_signed_gap_and_null_Tcert_retained=True),
        citation_keys=len(citations),bibliographic_entries=len(entries),all_manuscript_citation_keys_resolve=True,
        science_results=dict(D1='14 implementation /13 sources /8 certificates /5 qualified-open /1 source-rejected safe-open',
            D3='8 qualified certificates;4 complete pairs;2Win/2Lose all TIME_CLOSE;actual marker absent',
            math='J2 service difference; J2/J3 exact loaded LP=lambda_hat, IP=1/4+lambda_hat at stated coefficient; gap1/4',
            original_native_internal_causes='UNKNOWN',historical_D24_source='REJECTED'),
        retained_conditions=['Equal targets/weights and integer inventories for stated balancing/IP formula; tau0 and loaded return handled separately',
            'Actual serialized-binary64 point differs from tight ideal completion; same-DLL transfer discloses three signed zeros and initial-state scope',
            'R13217/24 plus independent own-zero,84 arms/64 comparisons stay historical; K35B UNKNOWN',
            'D1 real UC3split/child-target/requeue/cache path is distinct from unobserved natural NEXT',
            'D3 matrix identities match per pair and do not exercise removed-marker domains; no broad speed claim',
            'First verifier failure, effective adapter, old fees and real verification delay remain; wrapper wall is paid'],
        source_code_review='Previous independent design/freeze/ABI/consumer and exact boundary reviews retained; production identity unchanged',
        delivery_draft='Bounded current carriers, exact source bytes/main binding/old code dependencies, anonymous fixed commit, one owned root, three required pure checks; runtime still pending',
        pending=['Local closed-root replay and actual public one-root recovery, source publication/carrier scans and fixed manifest',
            'Rendered PDF formula/table/citation/cross-page visual QA',
            'Actual Draft PR/base/head/key-file remote readback and owned cleanup',
            'Final independent delivery/readiness review after those actual outcomes'],
        no_new_Native_or_matrix_required_by_this_review=True,native_Optimize=0,compilation=0,outer_review_seconds=time.perf_counter()-tick)
    write_path=review/'pre_release_science_review.json';assert not write_path.exists()
    write_path.write_text(json.dumps(detailed,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    gate=dict(schema='round133-independent-pre-release-science-admission-v1',UTC=now,reviewer='/root/reliability_review',
        primary_implementer_and_unique_delivery_launcher='/root',decision='ACCEPT',native_all_stopped=True,
        candidate_manifest_SHA=sha(candidate_path),matrix_SHA=matrices,effective_adapter_SHA=adapter_SHA,
        original_reader_SHA='933af994bf3def115d9870c33f409709d5509a1b42f7b0546645691ce1b7c80a',
        D1_completion_review_SHA=sha(review/'D1_completion_review.json'),D3_completion_review_SHA=sha(review/'D3_completion_review.json'),
        detailed_science_review_SHA=sha(write_path),science_document_bindings=docs,
        public_recovery_state='PENDING_ACTUAL_PUBLIC_RECOVERY',portable_local_replay_state='PENDING_ACTUAL_CLOSED_ROOT_REPLAY',
        PDF_visual_QA_state='PENDING_FULL_AFFECTED_PAGE_INSPECTION',remote_readback_cleanup_final_review_state='PENDING',
        allowed_next_phase='Publish exact sources; controlled pure preflight; finish PDF QA; bounded current-only carriers/fixed-science publication and actual public restore',
        not_final_delivery_acceptance=True,not_submission_authorization=True,not_universal_native_reliability=True,
        original_numerical_causes='UNKNOWN',historical_D24_call='REJECTED',Native_Optimize_by_reviewer=0)
    target=review/'pre_release_science_admission.json';assert not target.exists()
    target.write_text(json.dumps(gate,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(decision='ACCEPT_SCIENCE_ONLY',public_recovery='PENDING',tables_checked=26,citations=len(citations),Optimize=0,seconds=time.perf_counter()-tick)))
if __name__=='__main__':main()
