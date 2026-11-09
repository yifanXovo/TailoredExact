"""One bounded joint inventory/assignment construction, never an exclusion test.

Uniform math-state moves and an iteration schedule; no instance-name rules,
historical winners, timer switches, no-good loop or fixed assignment domain.
Only exact arithmetic plus a full saved-matrix lift can qualify an upper.
"""
import random
from fractions import Fraction as F
from round157_inventory import instance,value
from round157_resource import travel_bounds
from round158_resource import arithmetic
from round158_review import full_lift
from round157_floor import attach
from round153_pricing import Oracle
from round152_math import h_exact
from round143_lp import residual,semantics
from round143_math import outward
from round158_common import *

def run(role,label,iterations=131072):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    source=read(OLD157/'inventory_sources.json')[role];scope=source['scope'];data=instance(source['panel'])
    candidate=read(OUT/'candidates.json')[role];n=data['n'];ks=range(len(data['Q']));rng=random.Random(0)
    folder=OUT/'primal'/label;folder.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    source_dir=OUT/'resource'/('rx35_y3_v1' if role=='R-X35-S-T2' else 'nb35_continue_v1')
    members=candidate['members'];point=load_gz(source_dir/'solution.json.gz')
    oldbounds=read(source_dir/'travel_bounds.json');start=arithmetic(data,scope,members,point,oldbounds)
    Y=list(start['Y']);assignment=[-1]*n
    for k,ids in start['assignment'].items():
        for i in ids:assignment[i-1]=int(k)
    bounds=travel_bounds(data,list(range(1,n+1)))
    ordered=sorted(((r['lower'],sum(1<<(i-1) for i in r['stations'])) for r in bounds),reverse=True)
    support=[s['support'] for s in scope['stations']];position=[{y:j for j,y in enumerate(vs)} for vs in support]
    costs=[{y:float(h_exact(s,y)) for y in s['support']} for s in scope['stations']]
    c=[s['c'] for s in scope['stations']];b=data['initial'][1:];h=data['pickup']+data['drop'];cache={0:0.}
    tau=read(OUT/'initial_intervals.json')[role]['tau']
    def evaluate(y,owner):
        P=[0]*len(data['Q']);D=P.copy();masks=P.copy()
        for j,(v,k) in enumerate(zip(y,owner)):
            delta=b[j]-v
            if not delta:
                if k!=-1:return None
                continue
            if k not in ks or abs(delta)>data['Q'][k]:return None
            P[k]+=max(0,delta);D[k]+=max(0,-delta);masks[k]|=1<<j
        times=[];violation=0.
        for k in ks:
            mask=masks[k]
            if mask not in cache:cache[mask]=next((ell for ell,part in ordered if mask&part==part),0.)
            duration=h*P[k]+cache[mask];times.append(duration)
            violation+=max(0.,duration/data['T']-1)
            violation+=(max(0,D[k]-P[k])+max(0,P[k]-D[k]-data['Q'][k]))/data['Q'][k]
        total=sum(y);violation+=(max(0,scope['Bminus']-total)+max(0,total-scope['B']))/max(1,scope['B'])
        ratios=sorted(a*v for a,v in zip(c,y));S=math.fsum(ratios)
        G=math.fsum((2*j-n+1)*v for j,v in enumerate(ratios))/(n*S) if S else 0.
        J=G+math.fsum(costs[j][v] for j,v in enumerate(y))
        violation+=max(0.,G-scope['gamma_U'])+max(0.,J-tau)
        energy=J+2.*violation
        return energy,J,violation,times
    current=evaluate(Y,assignment);assert current is not None
    best=None;improvements=[];accepted=0
    write(folder/'plan.json',dict(UTC=utc(),role=role,iterations=int(iterations),seed=0,
        start_result_SHA=sha(source_dir/'result.json'),tau=tau,moves_do_not_fix_inventory_or_assignment=True,
        move_types=['adjacent stock state with optional owner change','one owner relocation','two owners swap','paired adjacent stock transfer'],
        temperature='0.01*(0.001**(iteration/iterations))',energy='true-J approximation + 2*dimensionless violation sum',
        feasible_point_requires_exact_J_and_balance_and_all_1_2_3_tour_checks=True,no_infeasibility_claim=True))
    for iteration in range(int(iterations)):
        y=Y.copy();owner=assignment.copy();kind=rng.randrange(4);i=rng.randrange(n)
        if kind in (0,3):
            sign=1 if rng.randrange(2) else -1;idx=position[i][y[i]]+sign
            if not 0<=idx<len(support[i]):continue
            y[i]=support[i][idx]
            if kind==3:
                j=rng.randrange(n)
                if i==j:continue
                idx=position[j][y[j]]-sign
                if not 0<=idx<len(support[j]):continue
                y[j]=support[j][idx]
                if y[j]==b[j]:owner[j]=-1
                elif owner[j]<0:owner[j]=rng.randrange(len(data['Q']))
            if y[i]==b[i]:owner[i]=-1
            elif owner[i]<0 or rng.randrange(4)==0:owner[i]=rng.randrange(len(data['Q']))
        elif kind==1:
            if y[i]==b[i]:continue
            owner[i]=rng.randrange(len(data['Q']))
        else:
            j=rng.randrange(n)
            if y[i]==b[i] or y[j]==b[j]:continue
            owner[i],owner[j]=owner[j],owner[i]
        proposal=evaluate(y,owner)
        if proposal is None:continue
        temperature=.01*(.001**(iteration/max(1,int(iterations)-1)))
        if proposal[0]<=current[0] or rng.random()<math.exp(min(0.,(current[0]-proposal[0])/temperature)):
            Y,assignment,current=y,owner,proposal;accepted+=1
        if current[2]<=1e-12 and (best is None or current[1]<best['J']-1e-13):
            val=value(scope,Y)
            if not val['feasible'] or val['phi']>F(tau):continue
            vehicles=[];okay=True
            for k in ks:
                ids=[j+1 for j,kk in enumerate(assignment) if kk==k]
                P=sum(max(0,b[j-1]-Y[j-1]) for j in ids);D=sum(max(0,Y[j-1]-b[j-1]) for j in ids)
                ell=max([F(0)]+[F(r['lower']) for r in bounds if set(r['stations'])<=set(ids)])
                duration=(F(data['pickup'])+F(data['drop']))*P+ell
                if not 0<=P-D<=data['Q'][k] or duration>F(data['T']):okay=False;break
                vehicles.append(dict(vehicle=k,stations=ids,P=P,D=D,required_time_exact=str(duration),required_time=float(duration)))
            if not okay:continue
            best=dict(Y=Y.copy(),assignment={k:[j+1 for j,kk in enumerate(assignment) if kk==k] for k in ks},
                J=outward(val['phi'],True),J_exact=str(val['phi']),vehicles=vehicles,iteration=iteration,physical_U=None)
            improvements.append(dict(iteration=iteration,J=best['J'],seconds=time.perf_counter()-tick))
            write(folder/'best_assignment.json',best);write(folder/'improvements.json',improvements)
    result=dict(UTC=utc(),role=role,iterations=int(iterations),accepted_moves=accepted,assignment_masks_evaluated=len(cache),
        classification='UNKNOWN',U_R=None,physical_U=None,source_SHA=sha(__file__),Optimize=0,
        final_energy=current[0],final_J_approx=current[1],final_violation=current[2],improvements=len(improvements))
    if best:
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.start();o=Oracle(scope,env,old_joint=True);ref=attach(o,data,bounds)
            p=full_lift(o,ref,best,data);q=residual(o.model,p);assert max(q['constraints'],q['bounds'])<=1e-7,q
            o.model.write(str(folder/'full_resource.mps'));save_gz(folder/'full_point.json.gz',p)
            with gp.read(str(folder/'full_resource.mps'),env=env) as back:assert semantics(back)==semantics(o.model)
            result.update(classification='RESOURCE_FEAS_IN_LEVEL',U_R=best['J'],full_matrix=q,
                model_SHA=sha(folder/'full_resource.mps'),point_SHA=sha(folder/'full_point.json.gz'));o.close()
    result['total_seconds']=time.perf_counter()-tick;write(folder/'result.json',result)
    print(json.dumps(result),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
