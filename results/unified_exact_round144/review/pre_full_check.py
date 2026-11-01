"""Independent exact replay of saved RN combinations; zero solver imports."""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import gzip, hashlib, json, math, datetime
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round144'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    facts=[]
    for role in ['K-35-U','R-X20-S-T1']:
        folder=OUT/'LP'/f'{role}_base'
        m=json.loads(gzip.decompress((folder/'primal_dual_matrix.json.gz').read_bytes()))
        pc=read(folder/'projection.json');r=read(folder/'result.json')
        a=defaultdict(F);b=F(0);wrong=[];active=0
        assert m['ModelSense']==1
        for row in m['rows']:
            if not row['name'].startswith('rn_'):continue
            p=F(row['Pi'])
            if row['sense']=='>' and p<0:wrong.append(row['name']);p=F(0)
            elif row['sense']=='<' and p>0:wrong.append(row['name']);p=F(0)
            else:assert row['sense'] in ('>','<','=')
            if not p:continue
            active+=1;b+=p*F(row['rhs'])
            for k,v in row['terms'].items():a[k]+=p*F(v)
        extension=[k for k in a if k.startswith('rn_')]
        sigma=F(0)
        for k in extension:
            col=m['columns'][k]
            assert col['Obj']==0 and abs(col['LB'])<1e100 and abs(col['UB'])<1e100
            sigma+=max(a[k]*F(col['LB']),a[k]*F(col['UB']))
            assert a[k]==F(pc['new_column_residuals_exact'][k])
        original={k:v for k,v in a.items() if not k.startswith('rn_') and v}
        assert original=={k:F(v) for k,v in pc['exact_terms'].items()}
        exact_rhs=b-sigma
        assert exact_rhs==F(pc['exact_projected_rhs'])
        conversion=F(0)
        for k,v in original.items():
            col=m['columns'][k];delta=F(pc['terms'].get(k,0.))-v
            conversion+=min(delta*F(col['LB']),delta*F(col['UB']))
        # Exact validity of the actual serialized >= row, including every
        # deleted or rounded original coefficient, not a tolerance test.
        safe_rhs=exact_rhs+conversion
        assert F(pc['rhs'])<=safe_rhs
        assert all(k=='G' or k.startswith('state_') for k in pc['terms'])
        assert r['qualified'] and r['added_RN_columns']==0 and r['added_PC_rows']==1
        assert r['Seed']==0 and r['Threads']==1 and r['LP_Optimize']==2
        assert sha(folder/'source.mps')==r['source_SHA']
        assert sha(folder/'compact.mps')==r['compact_SHA']
        assert sha(folder/'projection.json')==r['projection_SHA']
        facts.append(dict(role=role,active_RN_rows=active,wrong_sign_repair_names=wrong,
            exact_box_support=str(sigma),exact_transport_loss=str(exact_rhs-F(pc['rhs'])),
            serialized_rhs_safe_exact=True,root_retention_loss=r['root_retention_loss'],
            retention_fraction=r['retention_fraction'],matrix_binding=True))
    files=['include/Round144Research.hpp','include/ObjectiveResourceCompression.hpp',
        'src/ObjectiveResourceCompression.cpp','src/PaperExternalGiniTree.cpp',
        'src/GurobiBaseline.cpp','src/main.cpp','scripts/round144_lp.py']
    report=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        reviewer='Independent non-implementer /root/round144_independent_review',
        mathematical_check='PASS',exact_saved_PC_checks=facts,
        source_hashes={p:sha(ROOT/p) for p in files},Optimize=0,Native_load=0,compile=0,
        uncovered=['Actual compiled C++ row transport versus Fraction oracle',
            'Actual Native readback / complete Start / short complete health qualification',
            'Full-role endpoints, descendant loss and paid-floor attribution'],
        lifecycle_finding='Add/reset per-run Round144 state before multiple same-process runs; main and solver currently only reset R141',
        admission='CONDITIONAL: complete scoped lifecycle repair and measured qualification before expensive full runs')
    (OUT/'review/pre_full_review.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(mathematical_check='PASS',facts=facts,Optimize=0,Native_load=0)))
if __name__=='__main__':main()
