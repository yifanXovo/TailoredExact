"""Bounded actual reader reconstruction of affected15/16/17; no native work.

Only loop inventory is restricted in memory. Every original identity, source,
model, journal, native type, route, parameter and Start audit is still executed.
This partial projection is never represented as the final42-arm rebuild.
"""
from pathlib import Path
import json,sys
import round109_reader as reader

def run(root,dest):
    root=Path(root).resolve();dest=Path(dest);original=reader.read;campaign=root/reader.ROUND/'campaign/identity.json';qualification=root/reader.ROUND/'qualification/cli01/identity.json'
    def selected(path):
        value=original(path)
        if Path(path).resolve()==campaign:value=dict(value,launches=[x for x in value['launches'] if x['number'] in [15,16,17]])
        elif Path(path).resolve()==qualification:value=dict(value,launches=[])
        return value
    reader.read=selected
    try:value=reader.rebuild(root,dest)
    finally:reader.read=original
    rows=reader.rows(dest/'arms.csv');assert len(rows)==3 and {r['id'] for r in rows}=={'G50-C1','G50-C2'}
    proof=reader.numerical.verify(root)
    assert value['actual_Optimize']==6 and value['Optimize_returned']==5 and value['independently_proved_actual_native_returns_without_journal']==1
    reader.write(dest/'projection_scope.json',dict(partial_actual_raw_reconstruction=True,formal_numbers=[15,16,17],qualification_numbers=[],not_final42_rebuild=True,
        original_all42_campaign_identity_SHA=reader.sha(campaign),reader_SHA=reader.sha(root/'scripts/round109_reader.py'),
        projection_source_SHA=reader.sha(Path(__file__)),known_recovery_sidecar_SHA=reader.sha(root/reader.numerical.SIDE),
        original_failed_audit_and_missing_returned_preserved=True,solver_calls=0,summary=value))
    print(json.dumps(value))

if __name__=='__main__':run(sys.argv[1],sys.argv[2])
