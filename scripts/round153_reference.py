"""Restore exact old row identities and qualify the complete free reference."""
from fractions import Fraction as F
from round143_math import denominator,outward
from round145_math import joint_rows,row_activity
from round152_math import h_exact
from round153_lp import add_rows,finite_bounds,dual_certificate,primal_record,optimize,semantics
from round153_common import *

def direct_row(scope,row,index):
    assert row['terms']['G']==1. and row['sense']=='>'
    expected={f'e_{s["i"]}':s['omega'] for s in scope['stations'] if s['omega']}
    assert {k:v for k,v in row['terms'].items() if k.startswith('e_')}==expected
    terms={'G':1.};correction=F(0);details={}
    for s in scope['stations']:
        errors=[]
        for y in s['support']:
            k=f'state_{s["i"]}_{y}';exact=F(row['terms'].get(k,0.))+h_exact(s,y)
            a=float(exact);a=a if abs(a)>=1e-12 else 0.
            errors.append(F(a)-exact)
            if a:terms[k]=a
        correction+=min(errors);details[str(s['i'])]=str(min(errors))
    return dict(name=f'r153_direct_{index:02}',terms=terms,sense='>',rhs=outward(F(row['rhs'])+correction,False)),dict(
        source_row=row['name'],identity='old pi minus exact unary h; independent pricing identity',
        coefficient_correction_exact=str(correction),station_corrections=details)

def run(role):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'reference'/role;target.mkdir(parents=True,exist_ok=False)
    member_index={r['member']:r for r in load_gz(OLD/'artifacts'/f'research_{role}.members.json.gz')};dependencies={}
    def admit(path):
        path=Path(path);name=path.relative_to(ROOT).as_posix();r=member_index.get(name)
        assert r and sha(path)==r['SHA256'],name
        dependencies[name]=dict(r,commit=SCIENCE,archive=f'results/unified_exact_round152/artifacts/research_{role}.zip')
        return path
    d=read(admit(OLD/'domains'/role/'domain.json'));scope=d['scope'];ss=scope['stations']
    source=admit(OLD/'LP'/f'{role}_strongRN'/'model.mps')
    old=read(admit(source.parent/'result.json'));assert old['qualified'] and old['model_SHA']==sha(source)
    point=load_gz(admit(source.parent/'solution.json.gz'));dual=load_gz(admit(source.parent/'dual.json.gz'))['Pi']
    cycle=read(admit(OLD/'cycles'/f'{role}_cycle'/'result.json'));total_rows=[];sources=[]
    for r in cycle['records']:
        if r['stage']=='support':
            p=admit(Path(r['discovery']));bundle=read(p)
            assert bundle['qualified'] and bundle['scope']==scope and bundle['complete_parent_scope_covered_by_active_and_complement']
            total_rows.extend(bundle['rows']);sources.append(str(p.relative_to(ROOT)))
    assert len(total_rows)==8
    p=admit(OLD/'global'/f'{role}_global'/'result.json');bundle=read(p)
    assert bundle['qualified'] and bundle['scope']==scope
    total_rows.extend(bundle['rows']);sources.append(str(p.relative_to(ROOT)))
    p=admit(OLD/'oracle'/f'{role}_strong_zero'/'result.json');floor=read(p)
    if floor['decision']=='SEPARATION':
        assert floor['complete_cover'] and floor['scope']==scope and all(v==0 for v in floor['pi'].values())
        total_rows.append(dict(name='r153_reused_scalar_floor',sense='>',rhs=floor['lower'],terms={'G':1.,**{f'e_{s["i"]}':s['omega'] for s in ss if s['omega']}}))
        sources.append(str(p.relative_to(ROOT)))
    # Preserve the pricing/coverage records by fixed archive/member identity;
    # no old direction is reoptimized or re-priced.
    for name,r in member_index.items():
        if '/pricing/' in name or '/oracle/' in name or name.endswith('/support.json') or name.endswith('/lift.json'):
            dependencies.setdefault(name,dict(r,commit=SCIENCE,archive=f'results/unified_exact_round152/artifacts/research_{role}.zip'))
    spec=denominator({s['i']:s['c'] for s in ss},{s['i']:s['support'] for s in ss},scope['Bminus'],scope['B'])
    records=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with gp.read(str(source),env=env) as m:
            assert not m.IsMIP
            before=semantics(m);names={v.VarName for v in m.getVars()};cnames={c.ConstrName for c in m.getConstrs()}
            bounds,derivations=finite_bounds(m);save_gz(target/'implied_bounds.json.gz',dict(bounds=bounds,derivations=derivations))
            block=joint_rows(spec,bounds)
            direct=[];proofs=[]
            for i,row in enumerate(total_rows):
                rr,pp=direct_row(scope,row,i);direct.append(rr);proofs.append(pp)
            write(target/'domain.json',d);write(target/'rows.json',dict(NC_TS=block,total_union=total_rows,direct=direct,direct_proofs=proofs,reused_sources=sources))
            write(target/'source.json',dict(R152_source=str(source.relative_to(ROOT)),source_SHA=sha(source),Native=binding(),RN=spec,rows_retained=True))
            lower=old['L'];prior='strongRN'
            for label,rows in [('old_joint',block['rows']),('union',total_rows),('direct',direct)]:
                folder=target/label;folder.mkdir()
                activities=[row_activity(r,point) for r in rows];add_rows(m,rows,gp)
                assert semantics(m,names,cnames)==before
                check=primal_record(m,point);dc=dual_certificate(m,dual,bounds)
                zero=check['qualified'] and dc['qualified'] and check['objective']-dc['lower']<=1e-6
                if zero:
                    rr=dict(Status=2,Optimize_new=0,primal=check,objective=check['objective'],zero_solve_sandwich=True)
                    save_gz(folder/'solution.json.gz',point);save_gz(folder/'dual.json.gz',dict(Pi=dual))
                    m.write(str(folder/'model.mps'))
                else:
                    rr=optimize(m,folder);assert rr['Status']==2 and rr['primal']['qualified'],rr
                    point={v.VarName:v.X for v in m.getVars()};dual={c.ConstrName:c.Pi for c in m.getConstrs()}
                    dc=dual_certificate(m,dual,bounds);rr.update(Optimize_new=1,zero_solve_sandwich=False)
                assert dc['qualified'],dc['unresolved_infinite']
                save_gz(folder/'dual_certificate.json.gz',dc)
                rr.update(role=role,stage=label,parent=prior,original_semantics_retained=True,all_variables_free=True,
                          added_rows=len(rows),previous_numerical_value=lower,L=dc['lower'],U=rr['objective'],
                          g=point['G'],penalty=rr['objective']-point['G'],old_point_new_row_activities=activities,
                          model_SHA=sha(folder/'model.mps'),numerical_upper_policy=rr['primal']['policy'])
                # Read actual written model and retain all original rows/bounds.
                with gp.read(str(folder/'model.mps'),env=env) as back:assert semantics(back)==semantics(m)
                write(folder/'result.json',rr);records.append(rr);prior=label;lower=rr['objective']
                print(json.dumps(dict(role=role,stage=label,L=rr['L'],U=rr['U'],Optimize_new=rr['Optimize_new'])),flush=True)
    write(target/'reuse_index.json',dict(fixed_science=SCIENCE,dependencies=list(dependencies.values())))
    write(target/'result.json',dict(role=role,B=d['B_L'],old_RN=old['L'],stages=records,Q='direct',scope=scope))

if __name__=='__main__':run(*sys.argv[1:])
