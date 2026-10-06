"""Same-scope finite-pool expressions; historical rows are diagnosis only."""
from round104_common import *
from fractions import Fraction as F
import gzip, math

def exact(x): return F.from_float(float(x))
def upper(x):
    v=float(x)
    return math.nextafter(v,math.inf) if exact(v)<x else v
def combine(rows, multipliers, bounds):
    assert len(rows)==len(multipliers)
    a={}; b=F(0)
    for row,lam in zip(rows,multipliers):
        assert math.isfinite(lam) and lam>=0 and row['sense']=='<'
        b+=exact(lam)*exact(row['rhs'])
        for name,value in row['coefficients']:
            a[name]=a.get(name,F(0))+exact(lam)*exact(value)
    if not any(a.values()): return None
    # An exact power of two normalizes both sides before binary64 conversion.
    biggest=max(abs(v) for v in a.values()); exponent=-math.floor(math.log2(float(biggest)))
    scale=F(2)**exponent; a={n:v*scale for n,v in a.items()}; b*=scale
    ahat={n:float(v) for n,v in a.items() if v}; correction=F(0)
    for n,v in a.items():
        diff=exact(ahat.get(n,0.))-v
        if diff:
            lo,hi=bounds[n]; assert math.isfinite(lo) and math.isfinite(hi)
            correction+=max(diff*exact(lo),diff*exact(hi))
    rhs=upper(b+correction)
    assert all(math.isfinite(v) for v in ahat.values()) and math.isfinite(rhs)
    return dict(sense='<',rhs=rhs,coefficients=sorted(ahat.items()),
        exact_rhs=str(b),safe_compensation=str(correction),outward_rhs_error=str(exact(rhs)-b-correction),
        power2_exponent=exponent,exact_coefficients={n:str(v) for n,v in a.items() if v})

def old_pool(role):
    label={'F2':'capacity_F2_01','R98-C2':'capacity_C2_01','F5':'capacity_F5_01'}[role]
    path=PRIOR/'diagnostics'/label/'added_rows.jsonl'
    manifest=read(PRIOR/'compact_evidence03/manifest.json')
    entry=next(c for c in manifest['copies'] if c['source']==path.relative_to(ROOT).as_posix())
    assert sha(path)==entry['source_sha256']
    target=ROOT/entry['target']; assert sha(target)==entry['sha256']
    assert gzip.decompress(target.read_bytes())==path.read_bytes()
    rows=[]
    for line in path.read_text().splitlines():
        r=json.loads(line); k=r['vehicle']; p=r['support']; assert p['valid'] and not p.get('anchors',[])
        coeff=[(f'{tag}_{k}_{i}',float(F(w,r['scale'])*exact(r['multiplier'])))
            for i,ww in enumerate(r['weights'][1:],1) for tag,w in zip(['p','d','z'],ww) if w]
        assert exact(r['rhs'])==F(p['upper'],r['scale'])*exact(r['multiplier'])
        rows.append(dict(index=r['index'],vehicle=k,sense='<',rhs=r['rhs'],coefficients=coeff,support=p))
    return rows,dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),compact=entry['target'],
        summary=read(PRIOR/'diagnostics'/label/'summary.json'),contract=read(PRIOR/'diagnostics'/label/'contract.json'))

def pass_pool(role,resource):
    campaign,arm={'F2':('protection01','01_F2_H-SUBMIT'),'R98-C2':('development01','02_R98-C2_H-SUBMIT'),
        'F5':('long_tail01','03_F5_H-SUBMIT')}[role]
    paths=list((PRIOR/campaign/'raw'/arm).rglob('*.round103.rows.json')); assert len(paths)==1,paths
    path=paths[0]; c=read(str(path).replace('.rows.json','.contract.json'))
    assert c['column_contract']['resource']==resource, 'global necessary domain mismatch'
    rows=read(path)['rows']
    for r in rows:r.update(sense='<')
    return rows,dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),
        production_source_sha256=c['source_sha256'],scope=c['scope'],
        transfer='same all-station necessary resource contract; current old raw matrix unchanged')

def main(label,role,cap,source_override=None):
    from round100_idle import ensure_idle
    from round100_gurobi_runtime import gp,binding
    from gurobipy import GRB
    from round103_points import sources,typed_matrix
    from round98_projection_vector_audit import check
    from round70_affinity import inherited_core
    ensure_idle(); d=OUT/'diagnostics'/label; d.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter(); deadline=tick+cap; rows,origin=old_pool(role)
    source,expected,_,_=sources(role,'raw'); assert sha(source)==expected
    old_source_sha=expected
    if source_override:
        source=Path(source_override).resolve();expected=sha(source)
    passed,pass_origin=pass_pool(role,origin['contract']['resource'])
    write(d/'plan.json',dict(role=role,source=source.relative_to(ROOT).as_posix(),source_sha256=expected,
        inherited_pool=origin,actual_H_pass=pass_origin,historical_free_pool_diagnostic=True,cap_seconds=cap,
        original_raw_source_sha256=old_source_sha,native_scope_override=bool(source_override)))
    count=0; records={}
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0); engine.start(); runtime=binding()
        with gp.read(str(source),env=engine) as original:
            typed_matrix(original,d/'matrix.txt')
            if source_override:
                from round103_hull import Oracle
                panel=next(r for r in read(PRIOR/'development_inputs.json')['roles'] if r['id']==role)
                oracle=Oracle(panel,d/'matrix.txt',d)
                try:assert oracle.contract['resource']==origin['contract']['resource'], 'current native-scope resource contract differs'
                finally:oracle.close()
            bounds={v.VarName:(v.LB,v.UB) for v in original.getVars()}
            def solve(kind,new):
                nonlocal count
                m=original.relax(); by={v.VarName:v for v in m.getVars()}
                m.Params.Threads=1; m.Params.Seed=0; m.Params.Presolve=-1; m.Params.Method=1
                m.Params.FeasibilityTol=1e-9; m.Params.OptimalityTol=1e-9
                added=[m.addConstr(gp.quicksum(a*by[n] for n,a in r['coefficients'])<=r['rhs'],name=f'r104_{j}') for j,r in enumerate(new)]
                m.update(); remaining=deadline-time.perf_counter(); assert remaining>0
                m.Params.TimeLimit=remaining; count+=1
                with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='Optimize_begin',serial=count,kind=kind))+'\n')
                m.optimize()
                with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='Optimize_return',serial=count,kind=kind,status=m.Status,seconds=m.Runtime))+'\n')
                assert m.Status==GRB.OPTIMAL,(kind,m.Status)
                x={v.VarName:v.X for v in m.getVars()}; residual=check(m,x)
                pi=m.getAttr('Pi',m.getConstrs()); rc=m.getAttr('RC',m.getVars())
                station=[r-v.Obj for r,v in zip(rc,m.getVars())]
                for row,dual_value in zip(m.getConstrs(),pi):
                    expr=m.getRow(row)
                    for j in range(expr.size()):station[expr.getVar(j).index]+=dual_value*expr.getCoeff(j)
                dual=m.ObjCon+math.fsum(r.Pi*r.RHS for r in m.getConstrs())+math.fsum(
                    v.RC*(v.LB if v.RC>0 else v.UB) for v in m.getVars() if v.RC)
                r=dict(objective=m.ObjVal,primal=residual,dual_objective=dual,signed_primal_minus_dual=m.ObjVal-dual,
                    stationarity_max=max(map(abs,station),default=0),solver_ConstrVio=m.ConstrVio,solver_DualVio=m.DualVio,
                    rows=len(new),nonzeros=sum(len(r['coefficients']) for r in new),seconds=m.Runtime,
                    new_Pi=[a.Pi for a in added],new_slack=[a.Slack for a in added])
                records[kind]=r
                with gzip.open(d/(kind+'.point.json.gz'),'wt',encoding='utf-8') as f:json.dump(x,f)
                write(d/(kind+'.rows.json'),new); write(d/(kind+'.json'),r)
                m.dispose(); return r
            solve('RAW',[]); solve('PASS',passed); allr=solve('ALL',rows)
            multipliers=[max(0.,-p) for p in allr['new_Pi']]
            assert max(allr['new_Pi'],default=0)<=1e-8
            active=[r for r,l in zip(rows,multipliers) if l>0]
            solve('ACTIVE',active)
            grouped=[]
            for k in sorted({r['vehicle'] for r in rows}):
                rr=[r for r in rows if r['vehicle']==k]; ll=[l for r,l in zip(rows,multipliers) if r['vehicle']==k]
                group=combine(rr,ll,bounds)
                if group:group.update(vehicle=k,source_indices=[r['index'] for r,l in zip(rr,ll) if l>0]);grouped.append(group)
            solve('GROUPED',grouped)
            fleet=combine(rows,multipliers,bounds); solve('FLEET',[fleet] if fleet else [])
            write(d/'dual_support.json',dict(multipliers=multipliers,all_Pi=allr['new_Pi'],strictly_nonzero=sum(l>0 for l in multipliers),
                tiny_nonzero=sum(0<l<1e-8 for l in multipliers),no_epsilon_pruning=True,negative_Pi_is_nonnegative_lagrange=True))
    write(d/'summary.json',dict(role=role,records=records,Optimize_calls=count,DP_calls=0,
        seconds=time.perf_counter()-tick,runtime=runtime,affinity=affinity,source_sha256=expected,
        actual_LH=origin['summary']['LH'] if not source_override else None,historical_status=origin['summary']['status'],
        signed_GROUPED_minus_ALL=records['GROUPED']['objective']-records['ALL']['objective'],
        scope='same old raw original LP; transferred H rows have identical necessary domain; numerical certificates only'))
    print(json.dumps(dict(role=role,objectives={k:r['objective'] for k,r in records.items()},
        counts={k:r['rows'] for k,r in records.items()},signed_GROUPED_minus_ALL=records['GROUPED']['objective']-records['ALL']['objective'])),flush=True)
if __name__=='__main__':main(sys.argv[1],sys.argv[2],float(sys.argv[3]),sys.argv[4] if len(sys.argv)>4 else None)
