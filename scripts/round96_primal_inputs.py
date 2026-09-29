"""Generate the two previously reserved primal validation roles once, no solve."""
from round96_prepare import ROOT,OUT,read,write,sha,landscape,citi

ROLES=[dict(id='V1',V=30,M=3,Q=25,geometry='three_clusters',inventory='shortage',T_seconds=7200,
            cap_seconds=1800,method_order=['P-GRB','ORDER-ON','ENS-C']),
       dict(id='V2',V=50,M=4,Q=25,geometry='anisotropic_cloud',inventory='balanced',T_seconds=7200,
            cap_seconds=1800,method_order=['ENS-C','ORDER-ON','P-GRB'])]

def main():
    assert sha(ROOT/'scripts/round96_prepare.py')=='1708be14cb731cefac5719b1a956fe59cb6e06fd8581ba5b224a1343ffa9fcbe'
    build=read(OUT/'production_build_identity.json')
    assert build['plan_sha256']==sha(OUT/'primal_followup_plan.md')
    assert build['primal_rule_sha256']==sha(OUT/'route_order_admission.md')
    dest=ROOT/'reference/round96_primal_validation';dest.mkdir(exist_ok=False);rows=[]
    for role in ROLES:
        obj=landscape(role);path=dest/(role['id']+'.txt')
        path.write_text(citi.instance_text(obj,role['M'],role['Q']),encoding='utf-8',newline='\n')
        parsed=citi.parse_instance_mirror(path)
        assert all(0<=b<=c and 0<d<=c for b,c,d in zip(obj['initial'],obj['capacities'],obj['target']))
        assert len(set(map(tuple,parsed['points'])))==role['V']+1
        rows.append(dict(role,input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),
            input_sha256=sha(path),scenario_id='round96-primal-validation-'+role['id'],
            pickup_seconds=60,drop_seconds=60,**{'lambda':.15},total_initial=sum(obj['initial']),total_target=sum(obj['target'])))
    write(OUT/'primal_validation_inputs.json',dict(roles=rows,optimizer_calls=0,
        plan_sha256=sha(OUT/'primal_followup_plan.md'),generator_sha256=sha(__file__),
        production_build_identity_sha256=sha(OUT/'production_build_identity.json'),
        status='Both retained, never optimized or used for mechanism development at generation.'))

if __name__=='__main__':main()
