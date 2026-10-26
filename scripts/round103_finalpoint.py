"""One bounded terminal-point recomputation, retaining explicit distance UB.
Reuses self-paid prior plans as diagnostic columns, not production inputs.
"""
from round103_points import *
def main(label,parent,cap=300.):
    from round100_idle import ensure_idle
    from round100_gurobi_runtime import gp,binding
    from round102_screen import service_values
    from round70_affinity import inherited_core
    ensure_idle();source=OUT/'diagnostics'/parent;directory=OUT/'diagnostics'/label;directory.mkdir(parents=True,exist_ok=False)
    plan=read(source/'plan.json');role=plan['role'];iteration=sorted(source.glob('iteration_*'))[-1];point=read(iteration/'complete_point.json')
    write(directory/'plan.json',dict(parent=parent,parent_terminal_point_sha256=sha(iteration/'complete_point.json'),cap_seconds=cap,
        question='retain current restricted combination and verified full-distance upper bound at unchanged terminal point; no tolerance relaxation'))
    tick=time.perf_counter()
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding();oracle=Oracle(role,source/'matrix.txt',directory)
        for line in (source/'oracle_calls.jsonl').read_text().splitlines():
            p=json.loads(line)['proof'];r=p['solution'];validate(oracle.contract['resource'],p['vehicle'],r)
            oracle.plan_bank.setdefault(p['vehicle'],{})[tuple(v for row in r for v in row)]=r
        sv=service_values(oracle.contract['resource'],point['names'],point['values'])
        write(directory/'complete_point.json',point);write(directory/'service_point.json',sv)
        try:records=[classify(oracle,k,sv[k],engine,directory,tick+cap) for k in range(role['M'])]
        finally:oracle.close()
    write(directory/'summary.json',dict(role=role['id'],statuses=[r['status'] for r in records],outer_seconds=time.perf_counter()-tick,
        total_Optimize_calls=sum(r['Optimize_calls'] for r in records),total_DP_calls=oracle.calls,runtime=runtime,
        verified_distance_upper=[r.get('verified_distance_upper') for r in records],affinity=affinity))
    print(json.dumps(read(directory/'summary.json')))
if __name__=='__main__':main(sys.argv[1],sys.argv[2],float(sys.argv[3]) if len(sys.argv)>3 else 300.)
