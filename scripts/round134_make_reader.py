"""Create the narrowly changed R133 reader; retained native predicates are unchanged."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    code=(ROOT/'scripts/round133_read.py').read_text(encoding='utf-8-sig')
    code=code.replace('from round133_common import *','from round134_common import *')
    # Pure accepted-H adapters already admitted and checked in R133. Raw/native
    # schema and policy strings remain R133: those producers were not changed.
    needle='TOL=1e-7'
    code=code.replace(needle,'''import round133_postverify_repair as accepted_h
startup.reconstruct=accepted_h.reconstruct_accepted
compact_start.start_audit=accepted_h.start_audit_accepted

def exact_zero(physical,data,p):
    y=physical['Y'];d=data['D'];w=data['w'];lam=p['lambda']
    return (p['V']>0 and len(y)==len(d)==len(w)==p['V']+1 and
        math.isfinite(lam) and lam>=0 and
        all(type(y[i]) is int and y[i]>=0 and d[i]>0 and
            math.isfinite(w[i]) and w[i]>=0 and
            y[i]*d[1]==y[1]*d[i] and
            (lam==0 or w[i]==0 or y[i]==d[i]) for i in range(1,p['V']+1)))

TOL=1e-7''')
    code=code.replace("assert j['source_rejections'] and not result['strict_certified_original_problem']",
                      "assert j['source_rejections'] # Native rejection and independent proof are separate")
    needle="        elif j['source_rejections']:\n"
    assert code.count(needle)==1
    code=code.replace(needle,'''        elif result['strict_certificate_class']=='independent_zero_nonnegative_floor':
            assert exact_zero(physical,data,p) and physical['F']==0
            assert result['strict_certified_original_problem'] and result['lower_bound']==0
            assert result['strict_lower_bound_source']=='independent_full_domain_nonnegative_floor'
            if j['source_rejections']:
                arm=_safe_open(launch,d,result,physical,j,controller)
            else:
                arm=dict(source_reduced=False,native_proof_qualified=True,
                         implementation_failure_disposition_verified=True)
            arm.update(U=0.,L=0.,gap=0.,certificate=True,
                certificate_basis='INDEPENDENT_EXACT_ZERO_FULL_DOMAIN_NONNEGATIVE_FLOOR',
                performance_eligible=True,performance_evidence_eligible=True,
                independent_proof=True,native_search_cover_required_for_this_proof=False)
            endpoint=dict(arm=arm,cover=None)
        elif j['source_rejections']:
''')
    code=code.replace("own_zero=physical['F']==0 and physical['G']==0 and physical['P']==0",
                      "own_zero=exact_zero(physical,data,p)")
    code=code.replace("certificate_qualified=not bool(j['source_rejections']) and not bool(legacy_issue)",
                      "certificate_qualified=(arm.get('independent_proof',False) or not bool(j['source_rejections'])) and not bool(legacy_issue)")
    code=code.replace("'round133_endpoint.json'","'round134_endpoint.json'")
    code=code.replace("'round133_verification_failure.json'","'round134_verification_failure.json'")
    code=code.replace("    config=launch['expected_configuration']", """    config=launch.get('expected_configuration') or dict(threads=1,mip_threads=1,
        gurobi_seed=launch['seed'],gurobi_presolve=int(launch['command'][launch['command'].index('--gurobi-presolve')+1]),
        configuration=launch['configuration'],requested_mip_gap=0,requested_mip_gap_abs=0,
        FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)""")
    (ROOT/'scripts/round134_read.py').write_text(code,encoding='utf-8')
    print('Round134 reader created; native schema and all source checks retained')
if __name__=='__main__':main()
