"""Read-only analysis of saved, qualified root LP vectors; no solver/import.

Necessary vehicle-state extension tests, not a complete theta-feasibility test.
The greedy envelopes allocate a vehicle's z mass from all capacity-eligible
state masses. A violation proves no such allocation; success is inconclusive.
"""
import gzip,json,math,sys
from round98_common import *
import generate_citibike443_regional_v1 as parser

LABELS={'F2':'lp_F2','F5':'lp_strict_F5','R97-C2':'lp_strict_R97-C2',
        'R97-C3':'lp_strict_R97-C3','D6':'lp_strict_D6'}

def envelope(pool,mass,cost,reverse=False):
    remaining=mass;answer=0.
    for y,w in sorted(pool,key=lambda yw:cost(yw[0]),reverse=reverse):
        take=min(w,max(0.,remaining));answer+=take*cost(y);remaining-=take
    return answer,remaining

def run(output='saved_vector_vehicle_state_screen_v2.json'):
    records=[]
    for p in read(OUT/'development_inputs.json')['roles']:
        role=p['id'];folder=OUT/'diagnostics'/LABELS[role]
        r=next(x for x in read(folder/'summary.json')['records'] if x['mode']=='projected')
        values_path=folder/'projected_values.json.gz'
        if 'primal_violation' not in r:
            records.append(dict(role=role,skipped='Legacy diagnostic record lacks native primal-violation readback',
                domain_coefficient_changes=None,maximum_domain_envelope_residual=None,necessary_allocation_violations=[]))
            continue
        assert sha(values_path)==r['values_sha256'] and r['status']==2 and r['primal_violation']<=1e-6
        assert sha(OUT/'exports'/role/'projected.lp')==r['model_sha256']
        with gzip.open(values_path,'rt') as stream:values=json.load(stream)
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        data=parser.parse_instance_mirror(ROOT/p['input_path'])
        assert data['Q']==p['Q_vector'] and data['M']==p['M'] and data['V']==p['V']
        assert all(math.isfinite(v) for v in values.values())
        violations=[];changed=0;domain_max=0.;bound_residual=0.;maximum_missing_mass=0.
        for i in range(1,p['V']+1):
            b=data['initial'][i];cap=data['capacities'][i]
            original={int(n.split('_')[2]):w for n,w in values.items() if n.startswith(f'state_{i}_')}
            assert original and all(0<=y<=cap for y in original)
            bound_residual=max(bound_residual,max(max(-w,w-1) for w in original.values()))
            assert bound_residual<=1e-6
            states={y:max(0.,w) for y,w in original.items()}
            negative_mass=math.fsum(max(0.,-w) for w in original.values())
            assert abs(math.fsum(original.values())-1)<=1e-6
            ap=max(max(0,b-y) for y in states);ad=max(max(0,y-b) for y in states)
            for k,Q in enumerate(p['Q_vector']):
                pickup=values[f'p_{k}_{i}'];delivery=values[f'd_{k}_{i}'];z=values[f'z_{k}_{i}']
                bound_residual=max(bound_residual,-pickup,-delivery,-z,z-1)
                assert bound_residual<=1e-6
                a=min(Q,ap);c=min(Q,ad)
                changed+=int(a!=min(Q,b) or c!=min(Q,cap-b))
                residual=max(pickup-a*z,delivery-c*z)
                if a and c:residual=max(residual,c*pickup+a*delivery-a*c*z)
                domain_max=max(domain_max,residual)
                pool=[(y,w) for y,w in states.items() if y!=b and abs(y-b)<=Q]
                available=math.fsum(w for y,w in pool)
                if z>available+1e-6:
                    violations.append(dict(station=i,vehicle=k,test='eligible_mass',value=z,bound=available,residual=z-available))
                    continue
                for name,actual,cost in [('pickup',pickup,lambda y:max(0,b-y)),
                                         ('delivery',delivery,lambda y:max(0,y-b)),
                                         ('movement',pickup+delivery,lambda y:abs(y-b))]:
                    lo,left=envelope(pool,max(0.,z),cost);hi,left_hi=envelope(pool,max(0.,z),cost,True)
                    maximum_missing_mass=max(maximum_missing_mass,left,left_hi)
                    if left>1e-6 or left_hi>1e-6:continue
                    # All eligible costs are in [0,Q]. Cover omitted numerical
                    # mass, clamped negatives and a tiny negative z explicitly.
                    error=Q*(max(left,left_hi)+negative_mass+max(0.,-z))
                    for direction,resid,bound in [('minimum',lo-actual,lo),('maximum',actual-hi,hi)]:
                        if resid>1e-6+error:violations.append(dict(station=i,vehicle=k,test=name+'_'+direction,value=actual,
                            bound=bound,residual=resid,missing_mass_minimum=left,missing_mass_maximum=left_hi,maximum_numerical_cost_error=error))
        records.append(dict(role=role,model_sha256=r['model_sha256'],values_sha256=sha(values_path),
            input_sha256=p['input_sha256'],Q_vector=p['Q_vector'],relevant_bound_residual=bound_residual,
            maximum_missing_mass=maximum_missing_mass,
            native_reported_primal_violation=r['primal_violation'],domain_coefficient_changes=changed,
            maximum_domain_envelope_residual=domain_max,necessary_allocation_violations=violations))
    write(OUT/output,dict(optimizer_calls=0,new_solver_processes=0,
        scope='Offline analysis of existing qualified root vectors. No new LP or MIP. A failed necessary allocation condition proves lack of theta extension; passed conditions do not prove extension.',
        independent_all_original_rows_and_bounds_replayed=False,
        records=records,source_sha256=sha(__file__)))
    print(json.dumps([{k:r[k] for k in ['role','domain_coefficient_changes','maximum_domain_envelope_residual']}|
        {'allocation_violations':len(r['necessary_allocation_violations'])} for r in records]))

if __name__=='__main__':run(*(sys.argv[1:]))
