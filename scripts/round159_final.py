"""Final saved-evidence audit, with no Optimize and no independent-person claim."""
import ast
from round159_common import *
from round159_verify import check_resource

def run():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round143_lp import residual
    from round159_delivery import protect
    affinity();assert binding()['sha256']==DLL_SHA
    for p in (ROOT/'scripts').glob('round159_*.py'):ast.parse(p.read_text(encoding='utf-8-sig'))
    manifest=read(OUT/'build_manifest.json');assert sha(PE)==manifest['PE_SHA']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    inputs=read(OUT/'inputs_v2/manifest.json')
    for row in inputs['roles']:
        folder=OUT/'inputs_v2'/row['role'];assert sha(folder/'data.txt')==row['data_SHA'] and sha(folder/'rn.mps')==row['RN_SHA']
    assert read(OUT/'qualification.json')['PASS'] and read(OUT/'dp_qualification.json')['PASS'] and read(OUT/'interface_qualification.json')['PASS']
    facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for role,suffix in [('R-X35-S-T2','rx'),('N-B35-S','nb')]:
            source=read(OUT/'inputs_v2'/role/'source.json')
            for stage in ('baseline','joint'):
                label=f'{stage}_{suffix}';folder=OUT/'review'/label
                p=read(OUT/'runs'/label/'best.json');accepted=check_resource(source,p)
                with gp.read(str(folder/'full_resource.mps'),env=env) as m:
                    point=load_gz(folder/'full_point.json.gz');q=residual(m,point)
                    assert max(q['constraints'],q['bounds'])<1e-7
                    integer=max([abs(point[v.VarName]-round(point[v.VarName])) for v in m.getVars() if v.VType!='C']+[0])
                    assert integer<1e-10
                    facts.append(dict(label=label,J=accepted['J'],J_exact=accepted['J_exact'],full_raw_rows=m.NumConstrs,columns=m.NumVars,
                        residual=q,integer=integer,model_SHA=sha(folder/'full_resource.mps'),point_SHA=sha(folder/'full_point.json.gz')))
            physical=read(OUT/'review'/f'complete_joint_{suffix}.json')
            assert physical['PASS'] and physical['result']['classification']=='FIXED_COMBINATION_INFEAS' and physical['physical'] is None
        E=OUT/'deepening/free_owner_rx';condition=read(E/'condition.json');result=read(E/'result.json')
        assert result['normal_Optimize_return'] and result['model_SHA']==condition['model_SHA']==sha(E/'model.mps')
        with gp.read(str(E/'model.mps'),env=env) as m:
            service=[v for v in m.getVars() if v.VarName.startswith('service[')]
            assert len(service)==len(condition['eligibility'])
            assert all(v.LB==0 and v.UB==1 and v.VType=='B' for v in service)
            assert all(v.LB==0 and v.UB==1 for v in m.getVars() if v.VarName.startswith('arc['))
            Ecolumns=m.NumVars;Erows=m.NumConstrs
        assert result['classification'] in ('UNKNOWN','FIXED_Y_ALL_OWNER_INFEAS'), 'Physical benefit requires an actual F integration decision before closing'
    protected=protect()
    for v in inputs['roles']:
        source=read(OUT/'inputs_v2'/v['role']/'source.json')
        assert all((__import__('fractions').Fraction(x)*2**53).denominator==1 for row in source['data']['distance'] for x in row)
        assert source['data']['pickup']==source['data']['drop']==60
    write(OUT/'final_review.json',dict(UTC=utc(),PASS=True,Optimize=0,facts=facts,E1=dict(classification=result['classification'],rows=Erows,columns=Ecolumns,
        all_eligible_owners_free=True,inventory_scope='one saved Y'),protected_dirty_files=len(protected),
        PE_SHA=sha(PE),DLL=binding(),review_identity='same agent, separate saved-data/model/exact-arithmetic routine',
        independent_person_or_agent_review=False,global_proof_ledger_changes=0,stable_production_changes=0,
        scopes=['resource upper','fixed-combination physical failure','free-owner query status'],
        rejected_claims=['full-Q ceiling','global resource lower from restricted bound','all-owner exclusion from DP','complete performance gain','new DP/handling theory']))
    decision=read(OUT/'final_decision.json');decision.update(study_complete=True,review='Final saved-evidence audit PASS; same-agent separate routine')
    write(OUT/'final_decision.json',decision)

if __name__=='__main__':run()
