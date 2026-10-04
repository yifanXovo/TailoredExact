"""Billed read-only native-point/model qualification; zero Optimize."""
from round102_common import *
from pathlib import Path
from round102_screen import service_values,J_catalog,activity,S_candidates
from round102_support import row,exact
import sys
def main(label,campaign):
    from round100_idle import ensure_idle
    ensure_idle()
    from round100_gurobi_runtime import gp,binding
    from round98_projection_vector_audit import check
    d=OUT/'diagnostics'/label;d.mkdir(parents=True,exist_ok=False);records=[]
    with gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding()
        for point in (OUT/campaign/'raw').rglob('*.round102.point.json'):
            q=read(point);contract_file=Path(str(point).replace('.point.json','.contract.json'));binding_record=read(contract_file);c=binding_record['column_contract']['resource']
            arm=point.parents[1].name if point.parent.name=='external' else next(x.name for x in point.parents if x.name.startswith(('01_','02_','03_')))
            destination=next(x for x in point.parents if x.parent.name=='raw')
            models=[p for p in (destination/'external/models').glob('*.lp') if sha(p)==binding_record['canonical_sha256']]
            assert len(models)==1,(point,models,binding_record['canonical_sha256']);source=models[0]
            with gp.read(str(source),env=engine) as m:
                names=[v.VarName for v in m.getVars()];assert len(names)==len(q['point'])==c['columns']
                for k,rows in enumerate(binding_record['column_contract']['service_columns']):
                    for i,cols in enumerate(rows[1:],1):
                        for tag,j in zip(['p','d','z'],cols):assert names[j]==f'{tag}_{k}_{i}'
                residual=check(m,{name:x for name,x in zip(names,q['point'])})
                sv=service_values(c,names,q['point']);J=[]
                for family,W in J_catalog(c,sv):
                    r=row(c,W);per=[]
                    for k,w in enumerate(W):
                        act=sum(exact(x)*a for wi,vi in zip(w,sv[k]) for a,x in zip(wi,vi));per.append(float(act-r['proofs'][k]['upper']))
                    J.append(dict(family=family,fleet_excess=float(activity(W,sv)-r['rhs']),per_vehicle_excesses=per,
                        support_certificate=r))
                record=dict(point_source=str(point.relative_to(ROOT)),point_sha256=sha(point),actual_source=str(source.relative_to(ROOT)),actual_sha256=sha(source),
                    source='optimal original-column native root vector after native root processing',residual=residual,
                    old_complete_model_feasible_to_tol=residual['maximum_absolute_residual']<=1e-6,J=J)
                write(d/(destination.name+'_'+point.name),record)
                records.append({k:v for k,v in record.items() if k!='J'}|dict(J=[{k:v for k,v in r.items() if k!='support_certificate'} for r in J]))
    write(d/'summary.json',dict(records=records,runtime=runtime,Optimize_calls=0));print(json.dumps(records))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
