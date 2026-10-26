"""Small auditable closeout snapshots; no solver or compilation."""
from round133_common import *
import collections, shutil


def accounting(name):
    assert name in ('resource_accounting_science.json','resource_accounting.json')
    by_kind=collections.defaultdict(float);records=[]
    for folder in sorted((OUT/'fees').iterdir()):
        if not folder.is_dir() or not (folder/'receipt.json').exists():continue
        launch=read(folder/'launch.json');receipt=read(folder/'receipt.json')
        by_kind[launch['kind']]+=receipt['outer_seconds']
        records.append(dict(label=folder.name,kind=launch['kind'],outer_seconds=receipt['outer_seconds'],
            G1_seconds=receipt['G1_seconds'],separately_reported_seconds=receipt['separately_reported_seconds'],
            exit_code=receipt['exit_code'],receipt_SHA=sha(folder/'receipt.json')))
    current=os.environ.get('ROUND133_METERED_PARENT_LABEL')
    pending=[row for row in budget()['unclosed'] if row['label']!=current]
    assert not pending,pending
    external_review_costs=[]
    for relative in ('review/D1_completion_review.json','review/D3_completion_review.json'):
        path=OUT/relative
        if path.exists():
            value=read(path)
            external_review_costs.append(dict(path=relative,receipt_SHA=sha(path),
                outer_review_seconds=value.get('outer_review_seconds'),
                note='Independent read-only review receipt; not added to the common fee subtotal.'))
    write(OUT/name,dict(UTC=utc(),snapshot_not_recursive_final_transport=True,budget=budget(),
        closed_fee_outer_by_kind=dict(by_kind),closed_fees=records,
        unclosed_current_snapshot_process=current,
        costs='Each outer counted once. Nested H/LP/MIP/Work and child checker clocks are not added. G1 excludes explicitly metered disjoint postverification segments; those remain reported by the outer receipts.',
        static_manual_work='Reading/writing and tool orchestration are not claimed as exact CPU time or an additive measured process total.',
        external_E_costs=read(OUT/'infra/external_costs.json'),
        external_readonly_reviews=external_review_costs))
    print(json.dumps(dict(snapshot=name,G1_seconds=budget()['G1_seconds'],closed_outer_by_kind=dict(by_kind))))


def protected():
    baseline=read(OUT/'baseline.json');rows=[]
    for row in baseline['dirty_bindings']:
        digest=sha(row['path']);assert digest==row['sha256'],row['path']
        rows.append(dict(path=row['path'],SHA=digest))
    assets=[]
    expected=[(ORIGINAL_E3,ORIGINAL_PE_SHA),(DLL,DLL_SHA),
        (ORIGINAL_RESEARCH,'eac4e778cacb316c61928d4a6f1e4c90c8397cc94e0dc528695773703e98cce2'),
        (E3,'edfd4e2839afbe8571f00860402ae7596f702d4b494c1da8af0043acabf209ce'),
        (RESEARCH,'e0ff2e616124c2521af77fcd62ac068cf9f51fabdc5a60b03a58b66a6d988e0f')]
    for path,digest in expected:
        actual=sha(path);assert actual==digest,str(path)
        assets.append(dict(path=str(path),SHA=actual,bytes=path.stat().st_size))
    write(OUT/'review/protected_final.json',dict(status='PASS',UTC=utc(),directed_dirty_bindings=rows,
        assets=assets,scope='Only these directed bytes and declared native assets; not a whole disk or whole directory guarantee.',
        original_checkout_untouched_by_this_check=True,free_E_bytes=shutil.disk_usage(WORK).free,Optimize=0,compile=0))
    print(json.dumps(dict(protected_paths=len(rows),assets=len(assets),status='PASS')))


if __name__=='__main__':
    if sys.argv[1]=='protected':protected()
    else:accounting(sys.argv[1])
