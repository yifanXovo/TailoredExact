"""Bounded read-only Native import of actual sealed-run matrices; never Optimize."""
from round140_common import *
from round140_qualify import exact_matrix

def main(batch):
    facts=[];seen={}
    for group in read(OUT/f'{batch}_matrix.json')['groups']:
        l=group['launch'];d=Path(l['destination']);assert (d/'verification_closeout.json').exists()
        for event in read(d/'observations.json'):
            c=event['payload']
            if c['kind']!='call':continue
            key=(c['model_path'],l['counts'],l['stock'])
            if key not in seen:
                fact,_=exact_matrix(Path(c['model_path']),l['panel'],l['counts'],l['stock'],True);seen[key]=fact
            assert seen[key]['SHA']==c['model_sha256']
            facts.append(dict(position=group['position'],role=l['id'],call=c['call'],leaf=c['leaf'],
                actual_solver_Seed=l['seed'],**seen[key]))
    write(OUT/'qualification'/f'{batch}_native_actual.json',dict(PASS=True,Optimize=0,actual_calls=facts,
        unique_artifact_paths=len(seen),distinct_matrix_SHA=len({f['SHA'] for f in seen.values()}),
        actual_solver_Seeds=sorted({g['launch']['seed'] for g in read(OUT/f'{batch}_matrix.json')['groups']}),
        read_only_import_controls=dict(Seed=0,Threads=1),
        scope='Read-only Native coefficient/type/RHS import; actual solve parameters are independently checked from original call records'))
    print(json.dumps(dict(batch=batch,calls=len(facts),unique_artifacts=len(seen),Optimize=0)))

if __name__=='__main__':main(sys.argv[1])
