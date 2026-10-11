"""Small offline supplement: actual result parameter readbacks and native version."""
from pathlib import Path
import json, sys, hashlib
ROOT=Path('E:/codes/ExactEBRP-round113');DEST=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
import round94_lpg_contemporary as params
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ident=read(ROOT/'results/unified_exact_round113/campaign/identity.json');rows=[]
for l in ident['launches'][:4]:
    d=Path(l['destination']);r=read(d/'result.json')
    roundtrip=params.parameter_readback(r,require_call=True,arm='P-GRB' if l['arm'] in ['P-GRB','P-S'] else 'ENS-C')
    logs=[d/'native.log'] if l['arm'] in ['P-GRB','P-S'] else sorted((d/'external/native_logs').glob('*.gurobi.log'))
    assert logs
    versions=[]
    for log in logs:
        assert 'Gurobi Optimizer version 13.0.2' in log.read_text(encoding='utf-8')
        versions.append(dict(path=log.relative_to(ROOT).as_posix(),SHA=sha(log),version='13.0.2'))
    starts=[dict(path=p.relative_to(ROOT).as_posix(),SHA=sha(p),submitted=read(p)['submitted'],
        original_vector_exact_MIPSOL_adoption=read(p)['exact_vector_observed_in_mipsol'],
        original_vector_integer_MIPSOL_adoption=read(p)['integer_vector_observed_in_mipsol'])
        for p in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(p).get('submitted')]
    assert all(s['original_vector_exact_MIPSOL_adoption'] and s['original_vector_integer_MIPSOL_adoption'] for s in starts)
    rows.append(dict(arm=l['arm'],all_five_result_parameter_roundtrips_pass=True,roundtrip=roundtrip,native_versions=versions,ENS_MB_actual_Start_adoption=starts))
value=dict(scope='four new actual raw only; pure offline review supplement',rows=rows,native_starts=0,qualification_starts=0,
    production_or_raw_changed=False,script_SHA=sha(Path(__file__)))
(DEST/'supplement.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(pass_all=True,arms=4,native_starts=0)))
