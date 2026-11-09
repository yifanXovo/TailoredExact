"""Exact saved-matrix fractional-ownership witness, never an integer upper.

Run serially after the main call. No Optimize. This checks whether a known
impossible integer stock survives both explicit formulations' bare LPs.
It does not bound the integer resource optimum or strengthened Native cuts.
"""
from fractions import Fraction as F
from itertools import combinations
from round157_inventory import instance,value
from round158_common import *

def run():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();own=os.environ.get('ROUND140_METERED_PARENT_LABEL')
    assert not [r for r in budget()['unclosed'] if r['label']!=own],'serialize with the active main experiment'
    affinity();assert binding()['sha256']==DLL_SHA
    role='R-X35-S-T2';source=read(OLD157/'inventory_sources.json')[role];scope=source['scope'];data=instance(source['panel'])
    old=read(OUT/'resource/rx35_y3_v1/assignment_check.json');Y=old['Y'];val=value(scope,Y)
    assert val['feasible'] and Y in read(OUT/'candidates.json')[role]['members']
    assert val['phi']==F(read(OUT/'candidates.json')[role]['J_exact'])
    proof=read(OUT/'resource/rx35_y3_v1/result.json');assert proof['classification']=='FAMILY_RESOURCE_INFEAS'
    M=len(data['Q']);alpha=F(1,M);assert M>=2
    P=sum(max(0,data['initial'][i]-y) for i,y in enumerate(Y,1))
    D=sum(max(0,y-data['initial'][i]) for i,y in enumerate(Y,1));assert 0<=F(P-D,M)<=min(data['Q'])
    assert all(abs(data['initial'][i]-y)<=min(data['Q']) for i,y in enumerate(Y,1))
    target=OUT/'qualification/lp_fractional_ownership_v2';target.mkdir(parents=True,exist_ok=False);facts=[];common=None
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for variant in ('raw','rounded'):
            path=OUT/'qualification/level_v2'/f'{role}_{variant}.mps'
            approved=next(r for r in read(OUT/'qualification/level_v2/result.json')['facts'] if r['role']==role and r['variant']==variant)
            assert sha(path)==approved['model_SHA']
            with gp.read(str(path),env=env) as model:
                point={v.VarName:F(0) for v in model.getVars()};t=1/val['S'];point['t']=t;point['q']=val['G']
                for s,y in zip(scope['stations'],Y):
                    i=s['i'];point[f'x[{i},{y}]']=F(1);point[f'w[{i},{y}]']=t
                    point[f'z[{i}]']=t*y;point[f'r[{i}]']=F(s['c'])*t*y
                for a,b in combinations(scope['stations'],2):
                    i,j=a['i'],b['i'];point[f'a[{i},{j}]']=abs(point[f'r[{i}]']-point[f'r[{j}]'])
                for k in range(M):
                    for i,y in enumerate(Y,1):
                        if y!=data['initial'][i]:
                            point[f'resource_service[{k},{i},{y}]']=alpha;point[f'resource_visit[{k},{i}]']=alpha
                    point[f'resource_pickup[{k}]']=alpha*P;point[f'resource_drop[{k}]']=alpha*D
                assert set(point)=={v.VarName for v in model.getVars()}
                maximum=F(0);bad=[]
                for c in model.getConstrs():
                    row=model.getRow(c);lhs=sum((F(row.getCoeff(j))*point[row.getVar(j).VarName] for j in range(row.size())),F(0));rhs=F(c.RHS)
                    violation=max(F(0),rhs-lhs) if c.Sense=='>' else max(F(0),lhs-rhs) if c.Sense=='<' else abs(lhs-rhs)
                    maximum=max(maximum,violation)
                    if violation:bad.append(dict(row=c.ConstrName,violation_exact=str(violation)))
                bound_violations=[F(0)];unbounded=[]
                for v in model.getVars():
                    for side,bound in (('LB',v.LB),('UB',v.UB)):
                        if math.isfinite(bound):
                            bound_violations.append(F(bound)-point[v.VarName] if side=='LB' else point[v.VarName]-F(bound))
                        else:
                            assert bound==(-math.inf if side=='LB' else math.inf),(v.VarName,side,bound)
                            unbounded.append(dict(variable=v.VarName,side=side))
                bounds=max(bound_violations)
                integer=max([min(point[v.VarName]-math.floor(point[v.VarName]),math.ceil(point[v.VarName])-point[v.VarName])
                    for v in model.getVars() if v.VType!='C']+[F(0)])
                assert maximum<=F(1e-7) and bounds<=F(1e-7)
                assert integer>0,'a fractional ownership point is not an integer resource witness'
                if common is None:common=point;save_gz(target/'point_exact.json.gz',{n:str(v) for n,v in point.items()})
                else:assert point==common
                facts.append(dict(variant=variant,model_SHA=sha(path),rows=model.NumConstrs,columns=model.NumVars,
                    maximum_row_violation_exact=str(maximum),maximum_bound_violation_exact=str(bounds),
                    exact_rational_feasible=maximum==0 and bounds==0,violated_rows=bad,
                    maximum_integrality_violation_exact=str(integer),unbounded_native_bounds=unbounded))
    exact=all(r['exact_rational_feasible'] for r in facts)
    result=dict(UTC=utc(),PASS=True,Optimize=0,role=role,Y=Y,J_exact=str(val['phi']),J=float(val['phi']),
        owner_fraction_exact=str(alpha),total_pickups=P,total_drops=D,return_per_vehicle_exact=str(F(P-D,M)),facts=facts,
        exact_rational_feasible_in_both_models=exact,point_SHA=sha(target/'point_exact.json.gz'),
        integer_resource_upper=None,physical_U=None,whole_level_exclusion=False,
        integer_family_excluded=True,family_proof_SHA=sha(OUT/'resource/rx35_y3_v1/result.json'),
        interpretation='An integer stock proved resource-impossible admits fractional vehicle ownership in both explicit bare LP matrices. This is not a resource assignment upper, not a ceiling on integer F_R or on additional integer-valid cuts.',
        LP_price_upper_exact=str(val['phi']) if exact else None,
        reader_correction=dict(previous_fee='lp_fractional_witness',previous_failure='Fraction(Infinity) in bound reader',
            change='Check finite bounds exactly; recognize only -Infinity lower and +Infinity upper as unbounded. No matrix or tolerance change.',
            failed_originals_and_fees_retained=True),
        caveat='Only if the exact checks pass may this value upper-bound the defined original-price bare LP optimum. It never upper-bounds the integer resource optimum. No LP optimality or Native-root-cut closure is claimed.')
    write(target/'result.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':run()
