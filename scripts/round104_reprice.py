"""One finite GROUPED-direction repricing diagnosis, with complete support."""
from round104_common import *
from round104_pool import exact
from fractions import Fraction as F
import math,gzip

def main(label,cap):
    from round100_idle import ensure_idle
    from round100_gurobi_runtime import gp,binding
    from gurobipy import GRB
    from round103_hull import Oracle
    from round103_points import typed_matrix
    from round98_projection_vector_audit import check
    from round70_affinity import inherited_core
    ensure_idle();d=OUT/'diagnostics'/label;d.mkdir(parents=True,exist_ok=False)
    saved=OUT/'diagnostics/pool_F2_02';plan=read(saved/'plan.json');groups=read(saved/'GROUPED.rows.json')
    role=next(r for r in read(PRIOR/'development_inputs.json')['roles'] if r['id']=='F2')
    tick=time.perf_counter();deadline=tick+cap;rows=[];records=[]
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding()
        with gp.read(str(ROOT/plan['source']),env=engine) as old:
            typed_matrix(old,d/'matrix.txt');oracle=Oracle(role,d/'matrix.txt',d)
            try:
                c=oracle.contract['resource'];n=len(c['initial'])
                for g in groups:
                    k=g['vehicle'];width=sum(min(c['initial'][i],c['capacities'][k])+min(c['station_capacity'][i]-c['initial'][i],c['capacities'][k])+1 for i in range(1,n))
                    bits=max(30,math.ceil(math.log2(4*width/1e-8)));scale=1<<bits
                    weights=[[0,0,0] for _ in range(n)]
                    for name,a in g['coefficients']:
                        tag,kk,i=name.split('_');assert int(kk)==k
                        weights[int(i)][['p','d','z'].index(tag)]=round(a*scale)
                    score=sum(abs(w[0])*min(c['initial'][i],c['capacities'][k])+abs(w[1])*min(c['station_capacity'][i]-c['initial'][i],c['capacities'][k])+abs(w[2]) for i,w in enumerate(weights[1:],1))
                    if bits>48 or score>=1<<52:
                        records.append(dict(vehicle=k,status='UNKNOWN',reason='complete_support_score_or_precision_range'));continue
                    support=oracle.support(k,weights)
                    rhs=float(F(support['upper'],scale));assert exact(rhs)==F(support['upper'],scale)
                    coefficients=[(f'{tag}_{k}_{i}',float(F(a,scale))) for i,w in enumerate(weights[1:],1) for tag,a in zip(['p','d','z'],w) if a]
                    rows.append(dict(vehicle=k,sense='<',coefficients=coefficients,rhs=rhs,support=support,scale=scale))
                    records.append(dict(vehicle=k,status='SAFE_REPRICED',original_sum_rhs=g['rhs'],repriced_rhs=rhs,
                        caveat='quantized direction differs; objective may improve finite pool, not equivalence',bits=bits))
            finally:oracle.close()
            m=old.relax();by={v.VarName:v for v in m.getVars()}
            for j,r in enumerate(rows):m.addConstr(gp.quicksum(a*by[n] for n,a in r['coefficients'])<=r['rhs'],name=f'reprice_{j}')
            m.Params.Threads=1;m.Params.Seed=0;m.Params.Presolve=-1;m.Params.Method=1;m.Params.FeasibilityTol=1e-9;m.Params.OptimalityTol=1e-9
            m.Params.TimeLimit=max(.001,deadline-time.perf_counter())
            with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='Optimize_begin',serial=1,kind='repriced'))+'\n')
            m.optimize()
            with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='Optimize_return',serial=1,kind='repriced',status=m.Status,seconds=m.Runtime))+'\n')
            assert m.Status==GRB.OPTIMAL
            point={v.VarName:v.X for v in m.getVars()};residual=check(m,point)
            with gzip.open(d/'point.json.gz','wt') as f:json.dump(point,f)
            write(d/'summary.json',dict(records=records,objective=m.ObjVal,residual=residual,Optimize_calls=1,DP_calls=oracle.calls,
                signed_minus_finite_ALL=m.ObjVal-read(saved/'ALL.json')['objective'],
                signed_minus_historical_LH=m.ObjVal-read(saved/'summary.json')['actual_LH'],runtime=runtime,affinity=affinity,
                seconds=time.perf_counter()-tick,qualification='complete necessary supports; numerical LP; inherited full-hull premises only within tolerance'))
            write(d/'rows.json',rows);m.dispose()
    print(json.dumps(read(d/'summary.json')),flush=True)
if __name__=='__main__':main(sys.argv[1],float(sys.argv[2]))
