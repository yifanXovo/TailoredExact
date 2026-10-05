"""Reclassify the unchanged decisive complete point in a stronger domain."""
from round103_points import *
def main(label,parent,selection,cap=600.):
    from round100_idle import ensure_idle
    from round100_gurobi_runtime import gp,binding
    from round102_screen import service_values
    from round70_affinity import inherited_core
    ensure_idle();source=OUT/'diagnostics'/parent;directory=OUT/'diagnostics'/label;directory.mkdir(parents=True,exist_ok=False)
    context=read(OUT/'diagnostics'/selection/'selection.json');choice={r['vehicle']:r['anchors'] for r in context['selections']}
    where=sorted(source.glob('iteration_*'))[-1] if list(source.glob('iteration_*')) else source
    point=read(where/'complete_point.json');role_id=read(source/'summary.json')['role']
    role=next(r for r in read(OUT/'development_inputs.json')['roles'] if r['id']==role_id)
    matrix=(source/'matrix.txt') if (source/'matrix.txt').is_file() else OUT/'diagnostics'/read(source/'plan.json')['parent']/'matrix.txt'
    write(directory/'plan.json',dict(parent=parent,selection=selection,cap_seconds=cap,anchors=choice,
        question='excluding a prior mixture plan is insufficient: reclassify the original unchanged complete point in the strengthened necessary hull',production=False))
    tick=time.perf_counter()
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding();oracle=Oracle(role,matrix,directory);oracle.anchors=choice
        sv=service_values(oracle.contract['resource'],point['names'],point['values']);write(directory/'complete_point.json',point);write(directory/'service_point.json',sv)
        try:records=[classify(oracle,k,sv[k],engine,directory,tick+cap) for k in range(role['M'])]
        finally:oracle.close()
    write(directory/'summary.json',dict(role=role_id,statuses=[r['status'] for r in records],anchors=choice,
        total_Optimize_calls=sum(r['Optimize_calls'] for r in records),total_DP_calls=oracle.calls,outer_seconds=time.perf_counter()-tick,runtime=runtime,affinity=affinity))
    print(json.dumps(read(directory/'summary.json')))
if __name__=='__main__':main(sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4]) if len(sys.argv)>4 else 600.)
