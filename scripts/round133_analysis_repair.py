"""Repair only C-R3 physical readout, reusing healthy exact row calculations.

The original analyzer passed a route without its required reported F into a
comparison helper. Keep that failed derived file; no native workflow is rerun.
"""
from round133_common import *
import csv, gzip
import round108_reader as core
from round133_diagnostic import reconstruct_routes

def recompute(panel,routes):
    data=core.evidence.instance(ROOT,panel);inventory=data['b'].copy()
    for route in routes:
        for operation in route['operations']:
            inventory[operation['station']]+=operation['drop']-operation['pickup']
    value=core.evidence.objective(data,inventory,panel['lambda'])
    # The established helper now checks every physical condition as well as
    # agreement with the independently route-recomputed inventory objective.
    return core.full_fleet(ROOT,panel,dict(routes=routes,objective=value['F']))

def main():
    plan=read(OUT/'plans/C_diagnostics_runtime_repair.json');dest=ROOT/plan['C_R3']['destination']
    failed=dest/'physical_residual_analysis.json';old=read(failed)
    assert old['Optimize']==old['native_module_imports']==0
    assert all(not row['physical_verified'] and 'None)' in row['physical_error'] for row in old['records'])
    target=dest/'physical_residual_analysis_repaired.json';assert not target.exists()
    columns=read(dest/'columns.json')['columns'];names=[row['name'] for row in columns]
    points=[]
    if (dest/'final_vector.csv').exists():
        with (dest/'final_vector.csv').open(newline='',encoding='utf-8') as stream:rows=list(csv.DictReader(stream))
        assert [row['name'] for row in rows]==names
        points.append(('native_final',[float(row['value']) for row in rows]))
    with gzip.open(dest/'MIPSOL_vectors.jsonl.gz','rt',encoding='utf-8') as stream:
        for index,line in enumerate(stream,1):points.append((f'MIPSOL_{index}',json.loads(line)['values']))
    assert len(points)==len(old['records'])
    records=[]
    for (label,values),previous in zip(points,old['records']):
        assert label==previous['label'] and len(values)==len(names)
        digest=hashlib.sha256(json.dumps(values,separators=(',',':')).encode()).hexdigest()
        assert digest==previous['raw_point_SHA256']
        point=dict(zip(names,values));routes=reconstruct_routes(point,plan['panel'])
        physical=recompute(plan['panel'],routes)
        row=dict(previous);row.pop('physical_error')
        row.update(physical_verified=True,physical=physical,
            objective_propagation=dict(physical_minus_loaded=physical['F']-row['loaded_objective'],
                physical_G_minus_native_G=physical['G']-point['G'],
                physical_penalty_contribution=plan['panel']['lambda']*physical['P'],
                native_penalty_contribution=row['loaded_objective']-point['G']))
        records.append(row)
    write(target,dict(UTC=utc(),records=records,original_failed_analysis_SHA=sha(failed),
        repair_source_SHA=sha(__file__),loaded_matrix_SHA=sha(dest/'loaded_matrix.json.gz'),
        columns_SHA=sha(dest/'columns.json'),registration_SHA=sha(OUT/'plans/C_diagnostics_runtime_repair.json'),
        repair='Supply route-recomputed F to the established comparison helper; retain and reuse exact row/domain facts bound by identical raw-point SHA',
        repeated_rational_row_calculations=0,Optimize=0,Env=0,native_module_imports=0,
        original_failed_analysis_preserved=True,diagnostic_not_performance=True))
    print(json.dumps(dict(points=len(records),physical_passed=len(records),
        final=records[0]['objective_propagation'])))

if __name__=='__main__':main()
