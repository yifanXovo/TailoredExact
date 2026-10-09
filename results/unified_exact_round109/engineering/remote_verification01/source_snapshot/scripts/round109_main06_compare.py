"""Compare actual old/full and current/affected reader science, not source metadata."""
from pathlib import Path
import csv,json,sys
from round108_reader import read,write,sha

def rows(p):
    with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def run(root,dest):
    root=Path(root).resolve();out=root/'results/unified_exact_round109';dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    old=out/'reports_main06_recovery01';new=out/'reports_main06_affected02';a=rows(old/'arms.csv');b=rows(new/'arms.csv')
    key=lambda r:(r['id'],r['seed'],r['arm']);baseline={key(r):r for r in a}
    fields=['U','L','gap','relative_gap','relative_gap_null_reason','certificate','certificate_qualified','numbers_qualified',
        'complete_seconds','complete_seconds_interval','complete_seconds_lower','complete_seconds_upper','raw_claimed_U','raw_claimed_L',
        'native_Optimize','PE_SHA','DLL_SHA','input_SHA','T_seconds','cap_seconds','source_commit','returned_journal_sequence','journal_return_missing']
    count=0
    for r in b:
        previous=baseline[key(r)]
        for name in fields:
            if name in r or name in previous:assert r.get(name)==previous.get(name),(key(r),name,r.get(name),previous.get(name));count+=1
    oldpairs={(r['id'],r['seed'],r['candidate'],r['control']):r for r in rows(old/'pairs.csv')}
    pairs=rows(new/'pairs.csv')
    for r in pairs:
        previous=oldpairs[r['id'],r['seed'],r['candidate'],r['control']]
        # Full-panel CSV has the union of other pairs' columns. An absent
        # partial-table column is equivalent only to a genuinely empty cell.
        names=set(r)|set(previous)
        assert all(r.get(k,'')==previous.get(k,'') for k in names),[(k,r.get(k,''),previous.get(k,'')) for k in names if r.get(k,'')!=previous.get(k,'')]
        assert r['classification']=='WIN' and r['certified_time_ratio']=='' and r['control_seconds']==''
        count+=len(names)
    assert len(b)==3 and len(pairs)==1
    write(dest/'audit.json',dict(decision='ACCEPT',science_fields_exactly_equal=True,checks=count,actual_selected_arms=3,actual_pairs=1,
        input_tables={str(p.relative_to(root)):sha(p) for p in [old/'arms.csv',new/'arms.csv',old/'pairs.csv',new/'pairs.csv']},
        source_SHA=sha(Path(__file__)),zero_Optimize=True,metadata_only_additions=['native_cleanup_gate','station_drop_and_return_unload_components','prepaid_fee_fields','new_immutable_recovery_source_bindings']))
    print('Actual before/after science fields equal:',count)

if __name__=='__main__':run(sys.argv[1],sys.argv[2])
