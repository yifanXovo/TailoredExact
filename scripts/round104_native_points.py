"""Charged complete original-ENS point/scope/finite-pool separation reader."""
from round104_common import *
from round104_pool import exact,old_pool
from fractions import Fraction as F
import csv,math,gzip

def main(label,campaign):
    from round100_idle import ensure_idle
    from round100_gurobi_runtime import gp,binding
    from round98_projection_vector_audit import check
    from round70_affinity import inherited_core
    ensure_idle();d=OUT/'diagnostics'/label;d.mkdir(parents=True,exist_ok=False)
    camp=OUT/campaign;identity=read(camp/'identity.json');results=[];reads=0
    def signed(row,point):return sum((exact(a)*exact(point[n]) for n,a in row['coefficients']),F(0))-exact(row['rhs'])
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding()
        for launch in identity['launches']:
            role=launch['id'];folder=Path(launch['destination']); assert read(folder/'audit.json')['passed']
            lp={'F2':'pool_F2_02','R98-C2':'pool_C2_02','F5':'pool_F5_01'}[role]
            saved=OUT/'diagnostics'/lp;plan=read(saved/'plan.json');pool,_=old_pool(role)
            sets={'ALL':pool,'ACTIVE':read(saved/'ACTIVE.rows.json'),'GROUPED':read(saved/'GROUPED.rows.json'),
                'FLEET':read(saved/'FLEET.rows.json'),'PASS':read(saved/'PASS.rows.json')}
            points=sorted(folder.rglob('*.round104.samples.csv'));assert len(points)==1,points
            path=points[0];logpath=str(path).removesuffix('.round104.samples.csv')
            # Journal BEGIN binds actual model, mathematical domain and interval.
            observations=read(folder/'observations.json')
            begins=[o['payload'] for o in observations if o['payload']['kind']=='call' and o['payload']['native_log_path']==logpath]
            assert len(begins)==1,(logpath,[o['payload']['kind'] for o in observations[:12]])
            begin=begins[0];source=Path(begin['model_path']);assert sha(source)==begin['model_sha256']
            groups={}
            with path.open(newline='') as f:
                for r in csv.DictReader(f):groups.setdefault((r['sample_kind'],r['root_callback_sequence'],r['node_count']),{})[r['variable']]=float(r['value'])
            with gp.read(str(source),env=engine) as model:
                reads+=1
                for number,(key,point) in enumerate(groups.items()):
                    name,seq,node=key;residual=check(model,point)
                    assert residual['maximum_absolute_residual']<=1e-6,residual
                    assert set(point)=={v.VarName for v in model.getVars()}
                    rr=dict(role=role,kind=name,root_sequence=int(seq),node_count=float(node),
                        source_sha256=begin['model_sha256'],raw_source_sha256=plan['source_sha256'],
                        same_matrix=begin['model_sha256']==plan['source_sha256'],begin=begin,residual=residual,
                        point_objective=residual['objective'],pool_LH=read(saved/'summary.json')['actual_LH'],sets={})
                    # If hashes differ, old raw scope is checked separately and no
                    # identical-scope objective claim is made from a hash mismatch.
                    for kind,rows in sets.items():
                        excess=[signed(row,point) for row in rows]
                        reliable=[j for j,v in enumerate(excess) if v>exact(1e-5)]
                        rr['sets'][kind]=dict(rows=len(rows),positive=sum(v>0 for v in excess),
                            reliable_over_10_native_FeasibilityTol=len(reliable),indices=reliable,
                            maximum_signed=float(max(excess)) if excess else None,
                            maximum_signed_exact=str(max(excess)) if excess else None)
                    with gzip.open(d/f'{role}_{number:02d}.point.json.gz','wt') as f:json.dump(point,f)
                    write(d/f'{role}_{number:02d}.json',rr);results.append(rr)
            assert all(r['node_count']==0 for r in results if r['role']==role and r['kind'] in ['first_root_relaxation','latest_root_relaxation'])
    write(d/'summary.json',dict(passed=True,records=results,Optimize_calls=0,DP_calls=0,model_reads=reads,
        runtime=runtime,affinity=affinity,scope='actual original ENS terminal native model; complete vectors; last observable root only; no all-cut closure or hidden-cut implication claim'))
    print(json.dumps([dict(role=r['role'],kind=r['kind'],node=r['node_count'],same_matrix=r['same_matrix'],
        objective=r['point_objective'],violations={k:v['reliable_over_10_native_FeasibilityTol'] for k,v in r['sets'].items()}) for r in results]),flush=True)
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
