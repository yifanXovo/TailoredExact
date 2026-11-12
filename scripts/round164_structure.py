"""C35 witness/trajectory explanation without any optimization or oracle."""
from round164_common import *
import math

def operations(p,witness):
    from round108_reader import full_fleet
    from round107_reader import instance
    physical=full_fleet(ROOT,p,witness);data=instance(ROOT,p);vehicles=[];owners={}
    for route in physical['routes']:
        k=route.get('vehicle',route.get('vehicle_id'));nodes=route['nodes'];load=0;peak=0;pickups=0;drops=0;ops=[]
        for operation in route['operations']:
            if isinstance(operation,dict):i,x,y=operation['station'],operation['pickup'],operation['drop']
            else:i,x,y=operation
            owners[i]=k;ops.append(dict(station=i,pickup=x,drop=y))
        lookup={o['station']:o for o in ops}
        for i in nodes[1:-1]:
            op=lookup[i];load+=op['pickup']-op['drop'];peak=max(peak,load)
            pickups+=op['pickup'];drops+=op['drop'];assert 0<=load<=data['Q'][k]
        travel=sum(math.hypot(data['xy'][x][0]-data['xy'][y][0],data['xy'][x][1]-data['xy'][y][1])/1.5 for x,y in zip(nodes,nodes[1:]))
        handling=(p['pickup_seconds']+p['drop_seconds'])*pickups
        vehicles.append(dict(vehicle=k,nodes=nodes,operations=ops,travel_seconds=travel,handling_seconds=handling,
            duration_seconds=travel+handling,pickups=pickups,drops=drops,returned_load=load,prefix_peak=peak,capacity=data['Q'][k]))
    return dict(F=physical['F'],G=physical['G'],P=physical['P'],weighted_penalty=p['lambda']*physical['P'],
        Y=physical['Y'],station_owners=owners,vehicles=vehicles,full_original_physical_check=True)

def target_on_saved_skeleton(p,witness):
    """Evaluate one counterfactual inventory; failure is not a domain proof."""
    from round107_reader import instance,objective
    data=instance(ROOT,p);served={i for route in witness['routes'] for i in route['nodes'][1:-1]}
    unserved=set(range(1,p['V']+1))-served
    floor=p['lambda']*sum(data['w'][i]*abs(data['b'][i]/data['D'][i]-1) for i in unserved)
    y=data['b'].copy()
    for i in served:y[i]=data['D'][i]
    value=objective(data,y,p['lambda']);routes=[]
    for route in witness['routes']:
        k=route.get('vehicle',route.get('vehicle_id'));nodes=[0];load=0;peak=0;low=0;pickups=0;drops=0
        for i in route['nodes'][1:-1]:
            delta=data['b'][i]-data['D'][i]
            if delta==0:continue
            nodes.append(i);pickups+=max(0,delta);drops+=max(0,-delta);load+=delta;peak=max(peak,load);low=min(low,load)
        nodes.append(0)
        travel=sum(math.hypot(data['xy'][a][0]-data['xy'][b][0],data['xy'][a][1]-data['xy'][b][1])/1.5 for a,b in zip(nodes,nodes[1:]))
        duration=travel+(p['pickup_seconds']+p['drop_seconds'])*pickups
        violations=[]
        if low<0:violations.append('empty_departure_or_prefix_load_negative')
        if peak>data['Q'][k]:violations.append('prefix_capacity_exceeded')
        if duration>p['T_seconds']+1e-7:violations.append('physical_route_time_exceeded')
        if not 0<=load<=data['Q'][k]:violations.append('illegal_loaded_return')
        routes.append(dict(vehicle=k,nodes=nodes,pickups=pickups,drops=drops,return_load=load,
            minimum_prefix_load=low,maximum_prefix_load=peak,duration_seconds=duration,violations=violations))
    return dict(unserved_stations=sorted(unserved),unserved_fixed_weighted_penalty=floor,
        all_saved_served_stations_at_target_inventory_objective=value,
        route_checks=routes,counterfactual_is_physical=all(not r['violations'] for r in routes),
        is_restricted_domain_lower_or_optimum=False,does_not_prove_target_unattainable_on_skeleton=True,
        optimization_oracle_calls=0)

def run():
    from round164_analyze import History
    from round108_reader import full_fleet
    arms=[a for a in read(OUT/'reports/three_seed_arms.json') if a['id']=='R163-C35-U']
    new=read(OUT/'matrix_frozen.json')['groups'];old=read(ROOT/'results/unified_exact_round163/matrix_frozen.json')['groups']
    history=History();values=[];seed0_b=None;panel=None
    try:
        for arm in arms:
            if arm['historical']:
                group=next(g for g in old if g['launch']['id']==arm['id'] and g['launch']['R163_method']==arm['method'])
                launch=group['launch'];prefix=arm['source_archive_prefix']
                result=history.read(prefix+'/result.json');audit=history.read(prefix+'/audit.json')
                observations=history.read(prefix+'/observations.json')
            else:
                group=next(g for g in new if g['arm']['input_id']==arm['id'] and g['arm']['method']==arm['method'] and g['arm']['gurobi_seed']==arm['seed'])
                launch=group['launch'];d=Path(launch['destination']);result=read(d/'result.json');audit=read(d/'audit.json')
                observations=read(d/'observations.json')
            p=launch['panel'];final=operations(p,result);events=[]
            for record in observations:
                if record['payload']['kind']=='witness':
                    physical=full_fleet(ROOT,p,record['payload'])
                    events.append(dict(sequence=record['sequence'],source=record['payload']['source'],F=physical['F'],
                        G=physical['G'],weighted_penalty=p['lambda']*physical['P'],
                        data_close_seconds=record['data_close_seconds'],supervisor_available_seconds=record['effective_available_seconds']))
            h=audit.get('full_H');h_phys=h.get('physical') if h else None
            values.append(dict(id=arm['id'],seed=arm['seed'],method=arm['method'],historical=arm['historical'],
                qualified_L=arm['L'],certificate=arm['certificate'],H_physical=h_phys,final_fleet=final,
                saved_witness_events=events,producer_clock_reconstruction='see reports/primal_target_arrival.json'))
            if arm['seed']==0 and arm['method']=='B':seed0_b=result;panel=p
        counterfactual=target_on_saved_skeleton(panel,seed0_b)
        oldp=next(v for v in values if v['seed']==0 and v['method']=='P')
        oldb=next(v for v in values if v['seed']==0 and v['method']=='B')
        assert abs(oldb['H_physical']['F']-.1744902036)<1e-9
        assert abs(oldb['final_fleet']['F']-.12956638965196035)<1e-7
        assert abs(oldp['final_fleet']['F']-.09331934374779818)<1e-7
        assert abs(counterfactual['unserved_fixed_weighted_penalty']-.0114025534)<1e-9
        assert abs(counterfactual['all_saved_served_stations_at_target_inventory_objective']['F']-.0335925462)<1e-9
        assert not counterfactual['counterfactual_is_physical']
        write(OUT/'structural_synthesis.json',dict(UTC=utc(),scope='C35 complete saved H/B/P fleets and native trajectories only',
            runs=values,Seed0_skeleton_counterfactual=counterfactual,primal_and_proof_deficits_distinct=True,
            route_differences_simultaneously_change_ownership_order_quantities=True,
            single_operator_causality_established=False,route_feedback_complete_benefit_established=False,
            R96_R97_prior_mixed_feedback_evidence_retained=True,restricted_MIP_oracle_new_producer_calls=0))
    finally:
        history.zip.close()
        write(OUT/'structural_member_sources.json',dict(accesses=history.access,old_Optimize=0,full_archive_expanded=False))
    print('PASS: C35 saved-fleet structure, decompositions and infeasible target counterfactual; Optimize=0.')

if __name__=='__main__':run()
