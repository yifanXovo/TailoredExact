"""Exact hard-total network projection control, with a recovered joint mixture."""
from collections import defaultdict
from round152_math import evaluate
from round152_common import *

def project(scope,point,target):
    from round100_gurobi_runtime import gp
    start=time.perf_counter();target=Path(target);target.mkdir(parents=True,exist_ok=False);ss=scope['stations'];n=len(ss)
    marginal={};max_adjust=0.
    for s in ss:
        values={y:max(0.,point[f'state_{s["i"]}_{y}']) for y in s['support']}
        values={y:v for y,v in values.items() if v>1e-10};total=math.fsum(values.values());assert abs(total-1)<1e-7
        for y in s['support']:
            v=values.get(y,0.)/total;max_adjust=max(max_adjust,abs(v-point[f'state_{s["i"]}_{y}']))
            if v:marginal[s['i'],y]=v
    supports=[[y for y in s['support'] if (s['i'],y) in marginal] for s in ss]
    layers=[{0}];arcs=[]
    for j,s in enumerate(ss):
        layer=set();minrem=sum(min(ys) for ys in supports[j+1:]);maxrem=sum(max(ys) for ys in supports[j+1:])
        for t in sorted(layers[-1]):
            for y in supports[j]:
                u=t+y
                if u+minrem>scope['B'] or u+maxrem<scope['Bminus']:continue
                arcs.append((j,t,y));layer.add(u)
        layers.append(layer)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.Model(env=env) as m:
            flow=m.addVars(arcs,lb=0,name='f');incoming=defaultdict(list);outgoing=defaultdict(list);by_state=defaultdict(list)
            for j,t,y in arcs:incoming[j+1,t+y].append(flow[j,t,y]);outgoing[j,t].append(flow[j,t,y]);by_state[ss[j]['i'],y].append(flow[j,t,y])
            m.addConstr(gp.quicksum(outgoing[0,0])==1)
            for j in range(1,n):
                for t in layers[j]:m.addConstr(gp.quicksum(incoming[j,t])==gp.quicksum(outgoing[j,t]))
            for key,v in marginal.items():m.addConstr(gp.quicksum(by_state[key])==v,name=f'marginal_{key[0]}_{key[1]}')
            m.Params.TimeLimit=120;m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.LogFile=str(target/'native.log')
            m.update();m.write(str(target/'model.mps'));write(target/'call.json',dict(UTC=utc(),Seed=0,Threads=1,cap=120,kind='LP',model_SHA=sha(target/'model.mps')))
            m.optimize();write(target/'return.json',dict(UTC=utc(),Status=m.Status,Runtime=m.Runtime,Work=m.Work))
            result=dict(Status=m.Status,resource_projection_feasible=False,full_oracle_projection_feasible=False,columns=m.NumVars,rows=m.NumConstrs,nonzeros=m.NumNZs,
                        marginal_numerical_adjustment=max_adjust,Runtime=m.Runtime,Work=m.Work,seconds=time.perf_counter()-start)
            if m.Status==gp.GRB.OPTIMAL:
                quality={k:m.getAttr(k) for k in ['ConstrVio','BoundVio','ConstrResidual']};remaining={a:max(0.,flow[a].X) for a in arcs};paths=[]
                outkeys=defaultdict(list)
                for a in arcs:outkeys[a[0],a[1]].append(a)
                while math.fsum(remaining[a] for a in outkeys[0,0])>1e-8:
                    j,t,yy=0,0,[];chosen=[]
                    while j<n:
                        choices=[a for a in outkeys[j,t] if remaining[a]>1e-10]
                        assert choices,('flow decomposition',j,t)
                        a=max(choices,key=lambda a:remaining[a]);chosen.append(a);yy.append(a[2]);t+=a[2];j+=1
                    weight=min(remaining[a] for a in chosen)
                    for a in chosen:remaining[a]-=weight
                    paths.append(dict(weight=weight,**evaluate(scope,yy)))
                reconstructed={key:math.fsum(p['weight'] for p in paths if p['Y'][next(j for j,s in enumerate(ss) if s['i']==key[0])]==key[1]) for key in marginal}
                error=max(abs(reconstructed[k]-v) for k,v in marginal.items())
                total=math.fsum(p['weight'] for p in paths)
                result.update(quality=quality,paths=paths,marginal_reconstruction_error=error,mass=total,
                              resource_projection_feasible=error<1e-7 and abs(total-1)<1e-7 and max(quality.values())<1e-6,
                              full_oracle_projection_feasible=error<1e-7 and abs(total-1)<1e-7 and max(quality.values())<1e-6 and all(p['feasible'] for p in paths),
                              expected_phi=math.fsum(p['weight']*p['phi'] for p in paths),expected_G=math.fsum(p['weight']*max(scope['gamma_L'],p['G']) for p in paths))
            result['seconds']=time.perf_counter()-start
            write(target/'result.json',result)
    return result

if __name__=='__main__':
    from round150_lp import affinity
    configure();affinity();role,variant=sys.argv[1:3];scope=read(OUT/'domains'/role/'domain.json')['scope'];point=load_gz(OUT/'LP'/f'{role}_{variant}'/'solution.json.gz')
    rr=project(scope,point,OUT/'projection'/f'{role}_{variant}')
    print(json.dumps({k:v for k,v in rr.items() if k!='paths'}),flush=True)
