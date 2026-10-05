"""First eight complete real-point classifications. Fresh labels only."""
from round103_hull import *
from pathlib import Path
def typed_matrix(model,path):
    v=model.getVars();rows=model.getConstrs()
    with path.open('x') as f:
        f.write(f'{len(v)} {len(rows)}\n')
        for a in v:f.write(f'{a.VarName} {a.VType} {a.LB:.17g} {a.UB:.17g}\n')
        for r in rows:
            expr=model.getRow(r);terms=[(expr.getVar(j).index,expr.getCoeff(j)) for j in range(expr.size())]
            f.write(f'{r.Sense} {r.RHS:.17g} {len(terms)}' + ''.join(f' {i} {a:.17g}' for i,a in terms)+'\n')
def sources(role,kind):
    if kind=='raw':
        old=ROOT/'results/unified_exact_round101'
        q=next(r for r in read(old/'diagnostics/lp01/summary.json')['records'] if r['role']==role)
        return ROOT/q['actual_source'],q['actual_sha256'],list(map(float,(old/'compact_evidence/lp'/role/'raw.point').read_text().split())),None
    campaign,arm={'F2':('protection01','02_F2_J-SUBMIT'),'R98-C2':('development01','03_R98-C2_J-SUBMIT'),
        'F5':('long_tail01','02_F5_J-SUBMIT'),'R99-N2':('development01','04_R99-N2_J-SUBMIT')}[role]
    base=ROOT/'results/unified_exact_round102'/campaign/'raw'/arm
    points=sorted(base.rglob('*terminal_mip.gurobi.log.round102.point.json'))
    assert points,base
    point=points[0];contract=read(Path(str(point).replace('.point.json','.contract.json')))
    models=[p for p in (base/'external/models').glob('*.lp') if sha(p)==contract['canonical_sha256']]
    assert len(models)==1,(base,models)
    return models[0],contract['canonical_sha256'],read(point)['point'],point
def main(label,role_id,kind,cap=600.):
    from round100_idle import ensure_idle
    from round100_gurobi_runtime import gp,binding
    from round98_projection_vector_audit import check
    from round102_screen import service_values
    from round70_affinity import inherited_core
    ensure_idle();directory=OUT/'diagnostics'/label;directory.mkdir(parents=True,exist_ok=False)
    role=next(r for r in read(OUT/'development_inputs.json')['roles'] if r['id']==role_id)
    source,expected,values,point_source=sources(role_id,kind);assert sha(source)==expected
    write(directory/'plan.json',dict(role=role,kind=kind,cap_seconds=cap,source=str(source.relative_to(ROOT)),source_sha256=expected,
        point_source=str(point_source.relative_to(ROOT)) if point_source else 'R101 complete raw LP point',
        mechanism='restricted infinity-distance LP, complete C++ witness support, exact-dyadic certificates',production=False))
    tick=time.perf_counter();deadline=tick+cap;oracle=None
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding();assert gp.gurobi.version()==(13,0,2)
        with gp.read(str(source),env=engine) as model:
            names=[v.VarName for v in model.getVars()];assert len(names)==len(values)
            residual=check(model,dict(zip(names,values)));assert residual['maximum_absolute_residual']<=1e-6
            matrix=directory/'matrix.txt';typed_matrix(model,matrix)
            write(directory/'complete_point.json',dict(names=names,values=values,source_sha256=expected,residual=residual))
            oracle=Oracle(role,matrix,directory);sv=service_values(oracle.contract['resource'],names,values)
            write(directory/'service_point.json',sv)
            try:records=[classify(oracle,k,sv[k],engine,directory,deadline) for k in range(role['M'])]
            finally:oracle.close()
    write(directory/'summary.json',dict(role=role_id,kind=kind,statuses=[r['status'] for r in records],records=[{k:v for k,v in r.items() if k not in ['history','combination','support','weights']} for r in records],
        total_Optimize_calls=sum(r['Optimize_calls'] for r in records),total_DP_calls=oracle.calls,outer_seconds=time.perf_counter()-tick,
        runtime=runtime,affinity=affinity,actual_matrix_residual=residual,source_sha256=expected))
    print(json.dumps(read(directory/'summary.json')),flush=True)
if __name__=='__main__':main(sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4]) if len(sys.argv)>4 else 600.)
