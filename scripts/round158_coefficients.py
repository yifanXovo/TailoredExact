"""Bind the R92 envelope to actual inherited C++ duration coefficients.

Read the saved full physical LP, never execute an old producer. Nonzero,
nonunit max_digits10 writer coefficients reproduce their raw stored double.
The two finite inputs have no ambiguous unit/omitted positive travel terms.
"""
import re
from fractions import Fraction as F
from round157_inventory import instance
from round157_resource import travel_bounds
from round158_level import envelope,budgets,build
from round157_floor import lifted
from round143_lp import residual,semantics
from round158_common import *

def actual_duration(model,data):
    arcs={};handling={};rows={}
    for c in model.getConstrs():
        if c.Sense!='<' or c.RHS!=data['T']:continue
        expr=model.getRow(c);aa={};pp={};okay=True;vehicles=set()
        for j in range(expr.size()):
            name=expr.getVar(j).VarName;a=expr.getCoeff(j)
            arc=re.fullmatch(r'x_(\d+)_(\d+)_(\d+)',name);pickup=re.fullmatch(r'p_(\d+)_(\d+)',name)
            if arc:
                k,i,z=map(int,arc.groups());aa[i,z]=a;vehicles.add(k)
            elif pickup:
                k,i=map(int,pickup.groups());pp[i]=a;vehicles.add(k)
            else:okay=False;break
        if not okay or len(vehicles)!=1 or len(aa)!=data['n']*(data['n']+1):continue
        k=next(iter(vehicles));assert k not in rows
        assert set(aa)=={(i,j) for i in range(data['n']+1) for j in range(data['n']+1) if i!=j}
        assert set(pp)==set(range(1,data['n']+1))
        assert len(set(pp.values()))==1
        rows[k]=c.ConstrName;arcs[k]=aa;handling[k]=next(iter(pp.values()))
    assert set(rows)==set(range(len(data['Q']))),rows
    assert all(arcs[k]==arcs[0] and handling[k]==handling[0] for k in rows)
    # addTerm drops <=1e-12; writeExpr normalizes near1, otherwise emits
    # max_digits10. The actual finite matrices are outside both exceptions.
    assert all(a>1e-12 and a!=1. for a in arcs[0].values())
    matrix=[[0. if i==j else arcs[0][i,j] for j in range(data['n']+1)] for i in range(data['n']+1)]
    return matrix,handling[0],rows

def run():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification/coefficient_v2';target.mkdir(parents=True,exist_ok=False);facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for role,source in read(OLD157/'inventory_sources.json').items():
            data=instance(source['panel']);path=Path(source['scope_source']);assert sha(path)==source['scope_source_SHA']
            with gp.read(str(path),env=env) as model:matrix,h,rows=actual_duration(model,data)
            assert F(h)==F(data['pickup'])+F(data['drop'])
            differences=[F(data['distance'][i][j])-F(matrix[i][j]) for i in range(data['n']+1) for j in range(data['n']+1)]
            excess=max([F(0)]+differences);max_absolute=max(map(abs,differences))
            sqrt_mismatch=0
            for i,a in enumerate(data['points']):
                for j,b in enumerate(data['points']):
                    dx=float(a[0])-float(b[0]);dy=float(a[1])-float(b[1])
                    calculated=math.sqrt(dx*dx+dy*dy)/1.5
                    if calculated!=matrix[i][j]:sqrt_mismatch+=1
                    assert abs(F(calculated)-F(matrix[i][j]))<=4*F(math.ulp(matrix[i][j]))
            olddata,contract=envelope(data);newdata=dict(olddata,distance=matrix)
            oldbounds=travel_bounds(olddata,list(range(1,data['n']+1)));newbounds=travel_bounds(newdata,list(range(1,data['n']+1)))
            oldplan=budgets(olddata,oldbounds);newplan=budgets(newdata,newbounds)
            assert [r['budget'] for r in oldplan['rows']]==[r['budget'] for r in newplan['rows']]
            assert [r['stations'] for r in oldplan['kept']]==[r['stations'] for r in newplan['kept']]
            nominal_old=budgets(dict(olddata,T=data['T']),oldbounds);nominal_new=budgets(dict(newdata,T=data['T']),newbounds)
            assert [r['budget'] for r in nominal_old['rows']]==[r['budget'] for r in nominal_new['rows']]
            allowance=(data['n']+1)*excess
            assert F(contract['H_exact'])>F(contract['physical_horizon_exact'])+allowance
            package=dict(role=role,input_SHA=source['panel']['input_sha256'],distance=matrix,handling=h,
                source=dict(commit=source['fixed_commit'],path=str(path),SHA256=sha(path),
                    member=path.relative_to(WORK/'worktrees/round156').as_posix(),duration_rows=rows),
                proof='Actual nonzero nonunit C++ max_digits10 duration coefficients equal raw stored and emitted coefficients; no unit or omitted travel ambiguity on these inputs.',
                hypot_cpp_mismatches=sum(v!=0 for v in differences),sqrt_cpp_mismatches=sqrt_mismatch,
                maximum_hypot_excess_exact=str(excess),maximum_absolute_difference_exact=str(max_absolute),
                lawful_route_arc_excess_allowance_exact=str(allowance),
                global_and_all_7175_integer_budgets_equal_at_nominal_and_guarded_T=True,
                old_raw_rounded_integer_projection_unchanged=True,positive_physical_horizon_surplus=True)
            dest=target/(source['panel']['input_sha256']+'.json');write(dest,package)
            facts.append(dict(role=role,package_SHA=sha(dest),source_SHA=sha(path),duration_rows=rows,
                hypot_cpp_mismatches=package['hypot_cpp_mismatches'],sqrt_cpp_mismatches=sqrt_mismatch,
                maximum_absolute_difference=float(max_absolute),arc_allowance=float(allowance),
                nominal_budget_changes=0,guarded_budget_changes=0,kept_subsets=newplan['kept_subsets']))
    write(target/'result.json',dict(UTC=utc(),PASS=True,Optimize=0,old_producer_executions=0,new_build=0,facts=facts,
        prelong_v1_omission='The actual C++ sqrt/writer coefficient identity was missing; v2 deep call was normally stopped and fully charged before this finite repair.',
        existing_finite_family_exclusions_preserved_by_guard_and_identical_integer_budgets=True,
        scope='Only actual RX35/NB35 original inputs and saved physical LPs; no universal parser/FP repair, tolerance grid or historical performance rerun'))
    print(json.dumps(dict(PASS=True,facts=facts)),flush=True)

def qualify():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    assert read(OUT/'qualification/coefficient_v2/result.json')['PASS']
    target=OUT/'qualification/level_v2';target.mkdir(parents=True,exist_ok=False);facts=[]
    families=read(OLD157/'inventory_families.json')
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for role,source in read(OLD157/'inventory_sources.json').items():
            data=instance(source['panel']);tau=F(read(OUT/'initial_intervals.json')[role]['tau'])
            for variant in ('raw','rounded'):
                o,ref,info=build(source,env,variant,tau);m=o.model
                path=target/f'{role}_{variant}.mps';m.write(str(path));counts=dict(NumVars=m.NumVars,NumConstrs=m.NumConstrs,NumNZs=m.NumNZs)
                with gp.read(str(path),env=env) as back:assert semantics(back)==semantics(m)
                # All RN/cutoff algebra and the rounded integer matrix are
                # reused from v1; only actual duration coefficient binding is new.
                with gp.read(str(OUT/'qualification/level_v1'/path.name),env=env) as old:
                    nc=m.getConstrByName('original_objective_level');oc=old.getConstrByName('original_objective_level')
                    def row(mm,rr):
                        e=mm.getRow(rr);return rr.Sense,rr.RHS,{e.getVar(j).VarName:e.getCoeff(j) for j in range(e.size())}
                    assert row(m,nc)==row(old,oc)
                    if variant=='rounded':assert semantics(m)==semantics(old)
                point,physical=lifted(data,source['scope'],o,ref,families[role]['positive_control']['witness'])
                assert physical['J']>float(tau);m.remove(m.getConstrByName('original_objective_level'));m.update()
                q=residual(m,point);assert max(q['constraints'],q['bounds'])<=1e-7,q
                facts.append(dict(role=role,variant=variant,model_SHA=sha(path),**counts,positive_other_rows=q,
                    original_subsets=info['budget_plan']['original_subsets'],kept_subsets=info['budget_plan']['kept_subsets'],
                    actual_cpp_coefficient_package_SHA=info['contract']['coefficient_package_SHA']))
                o.close()
    write(target/'result.json',dict(UTC=utc(),PASS=True,Optimize=0,facts=facts,
        coefficient_qualification_SHA=sha(OUT/'qualification/coefficient_v2/result.json'),
        reused_v1_checks_SHA=sha(OUT/'qualification/level_v1/result.json'),
        reused='Cutoff all-state one-sided transport, R92 physical boundary/counterexample, integer rounding/subset dominance and durable normal-terminate interface; no repeat Native test or performance calls',
        actual_new_matrices_read_back=True,physical_controls_outside_level_not_starts=True))
    print(json.dumps(dict(PASS=True,facts=facts)),flush=True)

def implication():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round158_level import coefficient_package
    affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification/level_v2';facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for role,source in read(OLD157/'inventory_sources.json').items():
            data=instance(source['panel']);actual,package_SHA=coefficient_package(source);md,contract=envelope(data,actual)
            bounds=travel_bounds(md,list(range(1,data['n']+1)));plan=budgets(md,bounds)
            h=F(contract['h_exact']);U=plan['U'];minimum=None;count=0
            path=target/f'{role}_raw.mps'
            with gp.read(str(path),env=env) as m:
                for k in range(len(data['Q'])):
                    assert h*U<=F(m.getConstrByName(f'resource_handling_{k}').RHS)
                    for r in plan['rows']:
                        row=m.getConstrByName(f'resource_subset_{k}_{r["index"]}');e=m.getRow(row)
                        a={e.getVar(j).VarName:F(e.getCoeff(j)) for j in range(e.size())}
                        ell=F(r['lower']);ids=r['stations'];b=r['budget']
                        expected={f'resource_pickup[{k}]':h}|{f'resource_visit[{k},{i}]':ell for i in ids}
                        assert a=={n:v for n,v in expected.items() if v} and row.Sense=='<'
                        assert ((F(row.RHS)-ell*len(ids))//h)==b
                        endpoint=h*U+ell*(len(ids)-1)
                        assert endpoint<=F(row.RHS)
                        if b>=0:endpoint=max(endpoint,h*min(b,U)+ell*len(ids))
                        slack=F(row.RHS)-endpoint;assert slack>=0
                        minimum=slack if minimum is None else min(minimum,slack);count+=1
            facts.append(dict(role=role,model_SHA=sha(path),actual_rows=count,
                minimum_endpoint_slack_exact=str(minimum),integer_budget_and_actual_binary_RHS_equal=True,
                all_rounded_rows_imply_actual_raw_rows=True,coefficient_package_SHA=package_SHA))
    write(target/'actual_raw_implication.json',dict(UTC=utc(),PASS=True,Optimize=0,facts=facts,
        scope='Both actual C++ coefficient packages, every vehicle/subset row and global budget; floating RHS read directly'))
    print(json.dumps(dict(PASS=True,facts=facts)),flush=True)

if __name__=='__main__':{'run':run,'qualify':qualify,'implication':implication}[sys.argv[1]]()
