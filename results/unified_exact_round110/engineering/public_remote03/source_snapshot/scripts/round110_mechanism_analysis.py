"""Offline replay of recorded fleets and tabulation of published trajectories.

No proposed fleet, oracle, model solve or new operator is produced.
"""
import argparse, csv, json
from pathlib import Path
import round110_reader as r

def rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();root=a.root.resolve();out=root/'results/unified_exact_round110';identity=r.read(out/'campaign/identity.json')
    binding={};initial={};endpoints={};instances={}
    for launch in identity['launches']:
        n=launch['number'];d=r.portable(root,launch['destination']);obs=r.read(d/'observations.json');result=r.read(d/'result.json')
        binding[str(n)]={p.name:r.sha(p) for p in [d/'observations.json',d/'result.json',d/'completion.json']}
        witnesses=[e for e in obs if e['payload']['kind']=='witness']
        initial[n]=r.full_fleet(root,launch['panel'],witnesses[0]['payload']) if witnesses else None
        endpoints[n]=r.full_fleet(root,launch['panel'],result)
        instances[n]=r.evidence.instance(root,launch['panel'])
    same=[]
    for left,right in [(13,14),(25,27),(34,36),(36,42)]:
        x,y=initial[left],initial[right]
        same.append(dict(left=left,right=right,own_initial_U_left=x['F'],own_initial_U_right=y['F'],
                         initial_Y_equal=x['Y']==y['Y'],complete_initial_routes_equal=x['routes']==y['routes'],
                         native_full_column_Starts_or_acceptance_equal_inferred=False))
    fleet=endpoints[13];data=instances[13]
    discrepancies=[dict(station=i,Y=fleet['Y'][i],D=data['D'][i],difference=fleet['Y'][i]-data['D'][i])
                   for i in range(1,51) if fleet['Y'][i]!=data['D'][i]]
    assert len(discrepancies)==1 and discrepancies[0]['difference']==-1
    station=discrepancies[0]['station'];service=next(q for q in fleet['routes'] if any(o['station']==station for o in q['operations']))
    load=0;original=[];changed=[];first_bad=None;reached=False
    for op in service['operations']:
        load+=op['pickup']-op['drop'];original.append(dict(station=op['station'],load=load))
        reached=reached or op['station']==station
        replay=load-int(reached);changed.append(dict(station=op['station'],load=replay))
        if replay<0 and first_bad is None:first_bad=dict(station=op['station'],load=replay)
    assert first_bad is not None
    returns=[dict(vehicle=q['vehicle'],return_load=q['return_unload']) for q in fleet['cars'] if q['return_unload']]
    mechanics=rows(out/'reports_final/mechanism_summary.csv');times=rows(out/'reports_final/time_partitions.csv')
    value=dict(schema='round110-existing-trajectory-diagnostics-v1',raw_bindings=binding,
               same_initial_fleet_checks=same,G50_C1=dict(discrepancies=discrepancies,own_MB_U=fleet['F'],own_ENS_U=endpoints[14]['F'],
                  MB_service_vehicle=service['vehicle'],MB_returning_vehicles=returns,MB_service_vehicle_original_prefixes=original,
                  replay_of_only_one_less_recorded_pickup=changed,first_negative_prefix=first_bad,
                  counterfactual_is_infeasible=True,proposed_fleet_generated=False,new_operator=False),
               native_mechanisms=mechanics,V100_time_partitions=[t for t in times if t['id'].startswith('G100')],
               full_physical_UB_stream='reports_final/physical_UBs.csv',complete_fleets='reports_final/physical_fleets.csv',
               checkpoints='reports_final/checkpoints.csv',optimal_witness_intervals='reports_final/optimal_witness_bounds.csv',
               new_native_calls=0,oracle=0,causal_quantity_A_B_or_branching_identification=False)
    with a.out.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(same_initial_fleets=same,G50_C1=value['G50_C1'],Optimize=0)))

if __name__=='__main__':main()
