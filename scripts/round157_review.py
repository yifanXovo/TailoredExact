"""Independent saved-matrix/scope readbacks; never calls Optimize."""
from fractions import Fraction as F
from round157_inventory import instance,classes,family
from round157_resource import travel_bounds,fixed_model
from round143_lp import semantics,residual
from round157_common import *

def family_proof():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round107_reader import physical
    affinity();assert binding()['sha256']==DLL_SHA
    source=read(OUT/'inventory_families.json')['R-X35-S-T2'];candidate=source['candidates'][0]
    folder=OUT/'resource/rx35_family4096_v1';condition=read(folder/'condition.json');result=read(folder/'result.json')
    data=instance(source['panel']);members=family(source['scope'],candidate['Y'])
    assert len(members)==6 and members==condition['members']==candidate['members']
    assert result['condition_SHA']==sha(folder/'condition.json') and result['canonical_SHA']==sha(folder/'model.mps')
    assert condition['bounds_SHA']==sha(folder/'travel_bounds.json')
    execution=read(OUT/'engineering/source_snapshots/resource_rx35_family4096_v1.json')['files']
    digest=execution['scripts/round157_resource.py']
    assert condition['source_SHA']==digest==sha(OUT/'engineering/source_bytes'/f'{digest}.txt')
    supports={i:sorted({Y[i-1] for Y in members}) for i in range(1,data['n']+1)}
    active=[i for i,vs in supports.items() if any(v!=data['initial'][i] for v in vs)]
    assert all(sum(Y)==sum(data['initial'][1:]) for Y in members)
    largest_service=max(abs(data['initial'][i]-Y[i-1]) for Y in members for i in range(1,data['n']+1))
    assert largest_service<=min(data['Q'])
    bounds=travel_bounds(data,active);assert bounds==read(folder/'travel_bounds.json')
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        expected,ref=fixed_model(data,supports,classes(source['scope'],candidate['Y']),env,bounds)
        with gp.read(str(folder/'model.mps'),env=env) as actual:
            assert semantics(actual)==semantics(expected)
            assert actual.NumVars==result['NumVars'] and actual.NumConstrs==result['NumConstrs']
            assert actual.NumNZs==result['NumNZs']
            point=load_gz(folder/'solution.json.gz');quality=residual(actual,point)
            quality['integer']=max(abs(point[v.VarName]-round(point[v.VarName])) for v in actual.getVars() if v.VType!='C')
            assert max(quality[k] for k in ('constraints','bounds','integer'))<=1e-5,quality
            text=(folder/'native.log').read_text(encoding='utf-8').lower()
            assert not any(s in text for s in ('numerical trouble','unscaled primal violation','unscaled dual violation'))
        expected.dispose()
    assert result['status']==gp.GRB.INTERRUPTED and result['bound_stop'] and result['bound_status_qualified']
    assert result['required_time_lower']>data['T']+1e-5*max(1,data['T'])
    assert result['physical_U'] is None and result['physical_L_change']==0 and result['no_route_claim']
    fee=read(OUT/'fees/resource_rx35_family4096_v1/receipt.json')
    assert fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
    positives=[]
    for role,s in read(OUT/'inventory_families.json').items():
        v=physical(ROOT,s['panel'],s['positive_control']['witness'])
        positives.append(dict(role=role,F=v['F'],maximum_duration=v['maximum_duration']))
    target=OUT/'review/family_predeep_v1.json'
    write(target,dict(UTC=utc(),PASS=True,source_SHA=sha(__file__),Optimize=0,
        actual_matrix_rebuilt=True,actual_exact_travel_bounds_rebuilt=True,all_six_legal_members_covered=True,
        Native_lower=result['required_time_lower'],original_T=data['T'],margin=result['margin'],
        family_preserves_total_initial_inventory=True,all_vehicle_return_loads_forced_zero=True,
        largest_single_service=largest_service,individual_capacity_assignment_filter_inactive=True,
        explanation='Per-vehicle pickup/delivery balance, handling and small-subset travel already exclude the family without exact route order or prefix-load constraints.',
        native_return_qualified=True,inherited_R61_numerical_gate=quality,global_original_J_lower_gain=0.,
        excluded_scope='exact six-member objective-invariant class family only',
        resource_upper_is_not_physical_time_upper=True,existing_R107_physical_positive_checks=positives,
        same_agent_separate_reconstruction=True,fee_SHA=sha(OUT/'fees/resource_rx35_family4096_v1/receipt.json')))
    print(json.dumps(read(target)),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
