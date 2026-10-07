"""Recover exact old ledgers; never reconstruct raw calls from aggregate tables."""
from round106_common import *
import csv, shutil

def recover(source):
    source=Path(source).resolve();old=source/'results/unified_exact_round105'
    dest=OUT/'r105_supplement';dest.mkdir(exist_ok=False);records=[]
    missing=set(r['path'] for r in csv.DictReader((old/'reports02/native_calls.csv').open(newline='')))
    packed={r['path'] for r in read(old/'compact_evidence/manifest.json')['files']}
    targets=sorted(p for p in missing-packed if '/qualification/native' in p)
    assert len(targets)==66, ('unexpected omission surface',targets)
    counts={'Optimize':0,'IIS':0}
    for relative in targets:
        p=source/relative;assert p.is_file(),('original raw ledger missing',p)
        target=dest/'raw'/Path(relative).relative_to('results/unified_exact_round105')
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        assert sha(p)==sha(target)
        rows=list(csv.DictReader(p.open(newline='')))
        started=[r for r in rows if r['stage']=='before']
        returned=[r for r in rows if r['stage']=='after']
        assert [r['call'] for r in started]==[r['call'] for r in returned]
        for r in started:counts['IIS' if r['phase']=='iis' else 'Optimize']+=1
        records.append(dict(original_path=relative,recovered_path=target.relative_to(ROOT).as_posix(),
            source_absolute_path=str(p),sha256=sha(p),bytes=p.stat().st_size,
            evidence_level='exact_original_per_call_ledger',started=len(started),returned=len(returned)))
    assert counts==dict(Optimize=76,IIS=17)
    write(dest/'manifest.json',dict(inherited_delivery_sha='8dc274eb34ee6d8a575f0b94b57ef04476efc0f1',
        original_archive_sha256=sha(old/'compact_evidence/evidence.tar.gz'),files=records,
        omitted_calls_recovered=counts,original_pack_only=dict(Optimize=87,IIS=20),
        corrected_exact_byte_delivery_total=dict(Optimize=163,IIS=37),
        historical_measurements_changed=False,Optimize_calls=0,IIS_calls=0))
    arms=list(csv.DictReader((old/'reports02/arm_results.csv').open(newline='')))
    fees=list(csv.DictReader((old/'reports02/fees.csv').open(newline='')))
    a=next(a for a in arms if a['campaign']=='diagnostic04' and a['id']=='F5')
    fee=next(f for f in fees if f['label']=='diagnostic_F5_02')
    write(dest/'timing_correction.json',dict(role='F5',campaign='diagnostic04',
        algorithm_end_to_end_seconds=float(a['observed_end_to_end_seconds']),
        paid_outer_fee_seconds=float(fee['outer_seconds']),
        native_master_seconds=float(a['master_seconds']),
        sources={'arm_results_sha256':sha(old/'reports02/arm_results.csv'),
                 'fees_sha256':sha(old/'reports02/fees.csv')},
        historical_measurements_changed=False,Optimize_calls=0,IIS_calls=0))
    print(json.dumps(dict(recovered_ledgers=len(records),calls=counts)))

if __name__=='__main__':recover(sys.argv[1])
