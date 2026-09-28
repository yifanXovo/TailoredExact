"""Optimizer-free endpoint, returned-vector and provenance audit for the six R cases."""
import csv
import math
from pathlib import Path
import round96_fixed_route as f

def main():
    cases=f.read(f.OUT/'fixed_route_cases.json')['cases'];records=[];inventory=[]
    assert f.sha(f.__file__)==f.read(f.OUT/'qualification/gate.json')['diagnostic_source_sha256']
    for c in cases:
        dest=f.OUT/'fixed_route'/c['id'];r=f.read(dest/'result.json');mapping=f.read(dest/'mapping.json')
        receipt=f.read(f.OUT/f'fixed_route_{c["id"]}.receipt.json')
        assert receipt['exit_code']==0 and receipt['wall_seconds']<=c['cap_seconds']
        assert f.sha(dest/'model.lp')==mapping['model_sha256']
        initial=f.read(f.ROOT/c['witness_path']);final=f.read(dest/'witness.json');p=c['panel']
        physical=f.evidence.physical_module.physical(p,final);assert physical['original_T_feasible']
        model,start,ins,states=f.build(p,initial);model.verify(start)
        values={}
        for line in (dest/'solution.sol').read_text().splitlines():
            if line.startswith('#') or not line.strip():continue
            name,value=line.split();values[name]=float(value)
        residual=model.verify(values)
        objective=sum(coef*values[name] for name,coef in model.objective.items())
        assert abs(objective-r['model_objective'])<1e-7
        assert abs(physical['F']-r['final']['F'])<1e-12
        assert r['restricted_bound']<=physical['F']+1e-7
        assert r['certificate']==(r['status']==2 and abs(physical['F']-r['restricted_bound'])<=1e-7)
        old=ins['initial'].copy()
        for route in initial['routes']:
            for op in route['operations']:old[op['station']]+=op['drop']-op['pickup']
        changed=[i for i in range(1,ins['V']+1) if old[i]!=final['inventory'][i]]
        deleted=sum(1 for route in initial['routes'] for i in route['nodes'][1:-1] if final['inventory'][i]==ins['initial'][i])
        record=dict(id=c['id'],initial_F=r['initial_F'],final_F=physical['F'],improvement=r['initial_F']-physical['F'],
            restricted_L=r['restricted_bound'],restricted_gap=physical['F']-r['restricted_bound'],
            restricted_certificate=r['certificate'],status=r['status'],process_seconds=receipt['wall_seconds'],
            changed_stations=len(changed),deleted_stations=deleted,solution_max_residual=residual,
            original_global_certificate=False,optimizer_calls=1)
        records.append(record)
        inventory.append(dict(id=c['id'],changes=[dict(station=i,b=ins['initial'][i],before=old[i],after=final['inventory'][i]) for i in changed]))
    paths=sorted((f.OUT/'fixed_route').rglob('*'))
    index=[dict(path=p.relative_to(f.ROOT).as_posix(),bytes=p.stat().st_size,sha256=f.sha(p)) for p in paths if p.is_file()]
    f.write(f.OUT/'fixed_route_audit.json',dict(passed=True,records=records,changes=inventory,
        raw_index=index,paid_starts=6,optimizer_calls=6,total_process_seconds=sum(r['process_seconds'] for r in records),
        interpretation='Only restricted R certificates. Time limits remain unknown; no original global bound promotion.'))
    with (f.OUT/'fixed_route_results.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    print(records)

if __name__=='__main__':main()
