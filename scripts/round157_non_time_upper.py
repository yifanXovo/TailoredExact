"""Solver-free complete fleet witnesses at relaxed T, never original physical U."""
from round157_inventory import instance
from round157_fleet import verify
from round107_reader import physical
from round157_common import *

def run():
    target=OUT/'review/non_time_uppers';target.mkdir(parents=True,exist_ok=False);facts=[]
    for role,source in read(OUT/'inventory_families.json').items():
        data=instance(source['panel']);Y=source['candidates'][0]['Y']
        k=max(range(len(data['Q'])),key=lambda j:(data['Q'][j],-j));Q=data['Q'][k]
        todo={i for i,v in enumerate(Y,1) if data['initial'][i]!=v};nodes=[0];ops=[];load=0
        while todo:
            legal=[i for i in todo if 0<=load+data['initial'][i]-Y[i-1]<=Q]
            assert legal,'No non-time witness: do not infer infeasibility from a failed constructor'
            i=min(legal,key=lambda i:(data['distance'][nodes[-1]][i],i));delta=data['initial'][i]-Y[i-1]
            load+=delta;nodes.append(i);ops.append(dict(station=i,pickup=max(0,delta),drop=max(0,-delta)));todo.remove(i)
        witness=dict(routes=[dict(vehicle=k,nodes=nodes+[0],operations=ops)] if ops else [])
        checked=verify(data,witness);assert checked['Y']==Y
        witness['objective']=checked['J']
        safe=(data['n']+1)*max(max(v) for v in data['distance'])+(data['pickup']+data['drop'])*sum(data['initial'][1:])
        panel=dict(source['panel'],T_seconds=safe)
        independent=physical(ROOT,panel,witness)
        assert abs(independent['maximum_duration']-checked['maximum_duration'])<=1e-7
        write(target/f'{role}_witness.json',witness)
        result=dict(role=role,Y=Y,original_T=data['T'],safe_non_time_bound=safe,
            true_required_time_upper=checked['maximum_duration'],original_T_feasible=checked['original_T_feasible'],
            independent_R107=independent,physical_U_claim=False,Optimize=0,
            interpretation='Complete legal fleet for the same inventory with time relaxed; upper on Tstar, not an incumbent at original T.')
        assert not result['original_T_feasible']
        write(target/f'{role}_result.json',result);facts.append(result)
    write(target/'result.json',dict(UTC=utc(),PASS=True,facts=facts,source_SHA=sha(__file__),
        all_witnesses_full_original_non_time_physics=True,no_original_T_upper_claim=True))
    print(json.dumps(facts),flush=True)

if __name__=='__main__':run()
