"""Full old LP plus certified hull rows: valid outer approximation only.

Minimization never uses a finite-column objective as a BRP lower bound.
Closure requires optimal original-objective LP and every car's explicit
within-tolerance member certificate at that very point. Unfinished cases
retain an outer-approximation bound and honest UNKNOWN.
"""
from round103_points import *
def main(label,role_id,cap=600.,selection=None):
    from round100_idle import ensure_idle
    from round100_gurobi_runtime import gp,binding
    from gurobipy import GRB
    from round98_projection_vector_audit import check
    from round102_screen import service_values
    from round70_affinity import inherited_core
    ensure_idle();directory=OUT/'diagnostics'/label;directory.mkdir(parents=True,exist_ok=False)
    role=next(r for r in read(OUT/'development_inputs.json')['roles'] if r['id']==role_id)
    source,expected,old_values,_=sources(role_id,'raw');assert sha(source)==expected
    write(directory/'plan.json',dict(role=role,cap_seconds=cap,source=str(source.relative_to(ROOT)),source_sha256=expected,
        question='same-scope L0, finite R102 LJ, certified outer approximation LH; close only at all-member optimal point',
        reuse='only plans generated during this self-paid diagnostic; no imported historical directions',original_MIP_tolerances_unchanged=True,
        anchor_selection=selection,anchor_selection_sha256=sha(OUT/'diagnostics'/selection/'selection.json') if selection else None))
    tick=time.perf_counter();deadline=tick+cap;calls=0;added=0;iterations=[];rows_seen=set();status='UNKNOWN';reason='deadline';L0=LJ=lower=None
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding()
        with gp.read(str(source),env=engine) as original:
            matrix=directory/'matrix.txt';typed_matrix(original,matrix);oracle=Oracle(role,matrix,directory)
            if selection:oracle.anchors={r['vehicle']:r['anchors'] for r in read(OUT/'diagnostics'/selection/'selection.json')['selections']}
            model=original.relax();model.Params.Threads=1;model.Params.Seed=0;model.Params.Presolve=-1
            model.Params.FeasibilityTol=1e-9;model.Params.OptimalityTol=1e-9
            model.Params.LogFile=str(directory/'outer_lp.log');names=[v.VarName for v in model.getVars()];by={v.VarName:v for v in model.getVars()}
            def optimize(m,kind):
                nonlocal calls
                remaining=deadline-time.perf_counter()
                if remaining<=0:return False
                m.Params.TimeLimit=remaining;calls+=1
                with (directory/'outer_calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='begin',kind=kind,call=calls))+'\n')
                m.optimize()
                record=dict(kind=kind,call=calls,status=m.Status,seconds=m.Runtime,objective=m.ObjVal if m.SolCount else None)
                with (directory/'outer_calls.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
                return m.Status==GRB.OPTIMAL
            try:
                if not optimize(model,'L0'):raise RuntimeError('original LP not optimal within diagnostic cap')
                L0=model.ObjVal;lower=L0
                # Literal previous J rows on the exact same model/objective.
                # They are a retrospective comparison, never production inputs.
                finite=model.copy();finite.Params.Threads=1;finite.Params.Seed=0
                fby={v.VarName:v for v in finite.getVars()}
                for family in ['actual-direction','fixed-charge']:
                    saved=read(ROOT/'results/unified_exact_round102/compact_evidence/lp'/role_id/(family+'.json'))
                    finite.addConstr(gp.quicksum(a*fby[name] for name,a in saved['coefficients'].items())<=saved['rhs'])
                if optimize(finite,'LJ'):LJ=finite.ObjVal
                finite.dispose()
                while time.perf_counter()<deadline:
                    idir=directory/f'iteration_{len(iterations):03d}';idir.mkdir()
                    values=[v.X for v in model.getVars()];sv=service_values(oracle.contract['resource'],names,values)
                    residual=check(model,dict(zip(names,values)));assert residual['maximum_absolute_residual']<1e-6
                    write(idir/'complete_point.json',dict(names=names,values=values,objective=model.ObjVal,residual=residual))
                    records=[classify(oracle,k,sv[k],engine,idir,deadline) for k in range(role['M'])]
                    states=[r['status'] for r in records]
                    item=dict(iteration=len(iterations),objective=model.ObjVal,statuses=states,
                        master_Optimize_calls=sum(r['Optimize_calls'] for r in records),DP_calls=sum(r['DP_calls'] for r in records),added_rows_before=added)
                    iterations.append(item);print(json.dumps(item),flush=True)
                    if all(s=='INSIDE' for s in states):status='CLOSED_WITHIN_DECLARED_MEMBER_TOLERANCE';reason='optimal_outer_LP_and_all_explicit_members';break
                    new=0
                    for r in records:
                        if r['status']!='OUTSIDE':continue
                        k=r['vehicle'];weights=r['weights'];scale=r['coefficient_scale'];key=(k,tuple(v for row in weights for v in row))
                        if key in rows_seen:continue
                        rows_seen.add(key)
                        max_coefficient=max(abs(v)/scale for row in weights for v in row)
                        # Exact power-of-two rescaling reduces absolute LP tolerance
                        # sensitivity. It does not change support or variable scales.
                        multiplier=2.**(-math.floor(math.log2(max_coefficient)))
                        expr=gp.quicksum((a/scale)*multiplier*by[f'{tag}_{k}_{i}'] for i,row in enumerate(weights[1:],1) for tag,a in zip(['p','d','z'],row) if a)
                        rhs=(r['support']['upper']/scale)*multiplier;assert exact(rhs)==F(r['support']['upper'],scale)*exact(multiplier)
                        model.addConstr(expr<=rhs,name=f'r103_hull_{added}')
                        with (directory/'added_rows.jsonl').open('a') as f:f.write(json.dumps(dict(index=added,vehicle=k,weights=weights,scale=scale,multiplier=multiplier,rhs=rhs,support=r['support']))+'\n')
                        added+=1;new+=1
                    if not new:reason='no_new_certified_row_and_membership_incomplete';break
                    if not optimize(model,'outer_after_certified_rows'):reason='outer_LP_not_optimal_before_cap';break
                    lower=model.ObjVal
            finally:oracle.close();model.dispose()
    write(directory/'summary.json',dict(role=role_id,status=status,reason=reason,L0=L0,LJ=LJ,LH=lower if status.startswith('CLOSED') else None,
        certified_outer_approximation_LB=lower,added_rows=added,outer_Optimize_calls=calls,
        master_Optimize_calls=sum(r['master_Optimize_calls'] for r in iterations),DP_calls=oracle.calls,iterations=iterations,
        outer_seconds=time.perf_counter()-tick,runtime=runtime,affinity=affinity,source_sha256=expected,
        interpretation='Gurobi numerical LP optimum on certified valid outer rows; exact dyadic row validity. Within-tolerance combinations are not strict rational equality at the original point.'))
    print(json.dumps(read(directory/'summary.json')),flush=True)
if __name__=='__main__':main(sys.argv[1],sys.argv[2],float(sys.argv[3]) if len(sys.argv)>3 else 600.,sys.argv[4] if len(sys.argv)>4 else None)
