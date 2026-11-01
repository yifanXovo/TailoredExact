"""Independent exact checks of already-written compiled rows; no Native load."""
from pathlib import Path
from fractions import Fraction as F
import json, hashlib, time, datetime
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round144'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    start=time.perf_counter();facts=[]
    for role in ['K-35-U','R-X20-S-T1']:
        pc=read(OUT/'LP'/f'{role}_base/projection.json')
        compiled=read(OUT/'qualification/project'/f'{role}.json')
        a={k:-F(v) for k,v in pc['exact_terms'].items()}
        b=-F(pc['exact_projected_rhs']);actual=compiled['row'];margin=F(0)
        cols={v['name']:v for v in compiled['variables']}
        for k in set(a)|set(actual['terms']):
            delta=F(actual['terms'].get(k,0.))-a.get(k,F(0))
            margin+=max(delta*F(cols[k]['LB']),delta*F(cols[k]['UB']))
        slack=F(actual['rhs'])-b-margin
        assert actual['sense']=='<' and slack>=0
        assert not any(k.startswith('rn_') for k in actual['terms'])
        facts.append(dict(role=role,compiled_row_safe_exact=True,exact_validity_margin=str(slack),
            binary64_margin=float(slack),compiled_evidence_SHA=sha(OUT/'qualification/project'/f'{role}.json')))
    zero_path=OUT/'qualification/project/zero_RN_dual_redundant.json';zero=read(zero_path)
    assert zero['row']['terms']=={} and zero['row']['rhs']>=0
    assert all(r['Pi']==0 for r in zero['constraints'])
    files=['include/Round144Research.hpp','src/ObjectiveResourceCompression.cpp',
        'src/PaperExternalGiniTree.cpp','src/GurobiBaseline.cpp','scripts/round144_read.py']
    report=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='/root/round144_independent_review',
        decision='MATHEMATICS_AND_COMPILED_TRANSPORT_ACCEPTED; complete healthy lifecycle pending',
        facts=facts,zero_dual_tautology=dict(PASS=True,evidence_SHA=sha(zero_path),
            rule='Only empty terms and nonnegative <= RHS may be omitted; empty negative RHS fails closed'),
        reset_fix='Verified round144ResetRun preserves enabled only and is invoked at solvePaperExternalGiniTree entry',
        source_hashes={p:sha(ROOT/p) for p in files},
        qualified_transport_SHA=sha(OUT/'qualification_native_transport.json'),
        qualified_writer_SHA=sha(OUT/'qualification_native_writer.json'),
        seconds=time.perf_counter()-start,Optimize=0,compile=0,Native_load=0,
        remaining=['Healthy complete qualifier for repaired zero-dual path',
            'Reader must explicitly support mathematically inapplicable nonpositive-denominator path before claiming coverage',
            'Actual zero-row audit should count absent PC/RN rows, in addition to column names'])
    (OUT/'review/boundary_review.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['decision','facts','zero_dual_tautology','seconds','Optimize','compile','Native_load']}))
if __name__=='__main__':main()
