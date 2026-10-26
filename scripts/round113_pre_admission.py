"""Offline finite-authority copy and final identity seal; no qualification execution."""
from round113_common import *
from round113_campaign import helpers, reserve
import csv, shutil

def main():
    tick=time.perf_counter()
    assert not (OUT/'campaign/summary.jsonl').exists()
    assert not list((OUT/'campaign/raw').glob('*'))
    check_identity()
    old=OUT/'inherited_r112'; oldout=OLD_ROOT/'results/unified_exact_round112'
    legacy=read(oldout/'campaign/identity.json'); reports=list(csv.DictReader((old/'reports_final/arms.csv').open(encoding='utf-8',newline='')))
    assert sha(oldout/'campaign/identity.json')==read(old/'fixed_manifest.json')['campaign_identity_SHA']
    clocks=[]; files={}
    names=['launch.json','result.json','completion.json','audit.json','audit_execution_metrics.json',
        'whole_arm_receipt.json','native_end_receipt.json','postexit_audit_receipt.json','affinity.json',
        'process_start_marker.json','phases.csv','result.json.round112.startup.json',
        'native.log.round112.start.json','native.log.round112.start.values.csv','native.log.round112.native.json']
    (old/'authoritative/campaign').mkdir(parents=True,exist_ok=True)
    shutil.copyfile(oldout/'campaign/identity.json',old/'authoritative/campaign/identity.json')
    files['authoritative/campaign/identity.json']=sha(oldout/'campaign/identity.json')
    for l in legacy['launches'][:12]:
        source=oldout/'campaign/raw'/Path(l['destination']).name
        target=old/'authoritative/campaign/raw'/source.name;target.mkdir(parents=True,exist_ok=False)
        for name in names:
            p=source/name
            if not p.exists():continue
            shutil.copyfile(p,target/name);relative=(target/name).relative_to(old).as_posix()
            files[relative]=sha(p);assert files[relative]==sha(target/name)
        row=next(r for r in reports if int(r['number'])==l['number'])
        w=read(target/'whole_arm_receipt.json'); a=read(target/'audit.json'); c=read(target/'completion.json')
        assert row['formal_protocol_qualified']=='True' and a['passed'] and c['returncode']==0
        assert w['complete_seconds']==float(row['complete_seconds'])<=l['cap_seconds']
        assert row['PE_SHA']==PE_SHA and row['DLL_SHA']==DLL_SHA
        assert sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']==row['input_SHA']
        for k in ['U','L','gap']:assert abs(a['endpoint'][k]-float(row[k]))<=1e-7
        assert a['endpoint']['certificate']==(row['certificate']=='True')
        clocks.append(dict(number=l['number'],id=l['id'],arm=l['arm'],original_complete_seconds=w['complete_seconds'],
            path=(target/'whole_arm_receipt.json').relative_to(old).as_posix(),
            audit_path=(target/'audit.json').relative_to(old).as_posix(),
            result_path=(target/'result.json').relative_to(old).as_posix(),
            completion_path=(target/'completion.json').relative_to(old).as_posix(),
            original_launch_path=(target/'launch.json').relative_to(old).as_posix(),
            original_candidate_identity_SHA=sha(old/'candidate_identity.json'),
            input_SHA=l['panel']['input_sha256'],PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
            original_audit_passed=True,new_performance_clock=False,old_LP_matrix_reparsed=False))
    shutil.copyfile(OLD_ROOT/'scripts/read_round112.py',old/'signed_read_round112.py')
    files['signed_read_round112.py']=sha(old/'signed_read_round112.py')
    write(old/'clock_manifest.json',dict(arms=clocks,files=files,old_qualified=12,
        policy='Limited original results, necessary audits, clocks and Start handoff receipts; inherit signed matrix/scope/cover authority, not a fresh old-matrix audit.',
        old_partial13_excluded=True,old_raw_reaudited=False,original_clock_adjusted=False,
        original_R112_final_reader_SHA=files['signed_read_round112.py']))
    d=OUT/'engineering/pre_admission_seal02';d.mkdir(exist_ok=False)
    shutil.copyfile(OUT/'candidate_identity.json',d/'prior_candidate_identity.json')
    candidate=read(OUT/'candidate_identity.json')
    assert candidate['helpers']==helpers()==read(OUT/'qualification/cli01/identity.json')['helpers']
    assert candidate['full_argv']==[l['command'] for l in read(OUT/'campaign/identity.json')['launches']]
    candidate.update(offline_reader_SHA=sha(ROOT/'scripts/read_round113.py'),
        qualification_test_SHA=sha(ROOT/'scripts/qualify_round113.py'),
        qualification_post_test_SHA=sha(ROOT/'scripts/qualify_round113_post.py'),
        inherited_clock_manifest_SHA=sha(old/'clock_manifest.json'))
    (OUT/'candidate_identity.json').unlink();write(OUT/'candidate_identity.json',candidate)
    b=budget();assert not b['unclosed'] and b['qualification_starts']==10 and b['qualification_seconds']<1200
    launches=read(OUT/'qualification/cli01/identity.json')['launches']; actual=[]
    for l in launches:
        p=Path(l['destination']);w=read(p/'whole_arm_receipt.json');a=read(p/'audit.json')
        assert a['passed'] and w['complete_seconds']<=120
        actual.append(dict(arm=l['arm'],whole_seconds=w['complete_seconds'],endpoint=a['endpoint'],
            necessary_audit_SHA=sha(p/'audit.json'),whole_SHA=sha(p/'whole_arm_receipt.json'),
            progress_SHA=sha(p/'progress_publication_receipt.json')))
    roots=['qualification/finite01/sharing','qualification/finite01/supervisor','qualification/finite01/lifecycle',
        'qualification/finite02/compatibility','qualification/finite03/lifecycle','qualification/post02']
    evidence={p.relative_to(OUT).as_posix():sha(p) for r in roots for p in sorted((OUT/r).rglob('*')) if p.is_file()}
    evidence.update({p.relative_to(OUT).as_posix():sha(p) for p in sorted((OUT/'fees').rglob('*')) if p.is_file()})
    write(OUT/'qualification/summary.json',dict(passed=True,actual_CLI=actual,qualification_fee=b,
        formal_reserve=reserve(),candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
        evidence_SHA=evidence,no_formal_started=True,actual_native_CLI_count=4,
        actual_native_cancellation_branch_executed=False,
        lifecycle_scope='source-derived synthetic fixtures executed through necessary and offline boundary; no extra Optimize',
        finite01_failed_compatibility_assertion_retained=True,post01_failed_pending_fee_read_retained=True,
        old12_targeted_compatibility_only=True,old_partial13_endpoint_rejected=True,
        old_LP_matrix_reparse=False,PE_recompiled=False,
        driver_processes=5,wrapper_processes=1,native_children=4,
        process_count_note='finite01/02/03 and post01/02: five drivers; cli01: one wrapper plus four native children; total ten.',
        holder_processes=0,holder_in_CLI_wrapper=True,OS_mock_children=0))
    write(d/'receipt.json',dict(pure_offline_engineering=True,Optimize=0,native_starts=0,
        prior_candidate_SHA=sha(d/'prior_candidate_identity.json'),final_candidate_SHA=sha(OUT/'candidate_identity.json'),
        production_unchanged=True,all_performance_helpers_unchanged_since_actual_CLI=True,all_argv_unchanged=True,
        offline_reader_changes=['necessary-audit floating arithmetic compared under inherited 1e-7; no new numerical policy',
            'reader inside active qualification driver records own fee pending; final reader requires all fees closed',
            'restored-root inherited old12 clocks and results bound to limited original authority'],
        original_old12_receipts_copied=True,whole_old_carrier_copied=False,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(sealed=True,candidate_SHA=sha(OUT/'candidate_identity.json'),budget=b,old_authority_files=len(files))))

if __name__=='__main__':main()
