"""Full-support residual master/pricing contrast to the active-complement lift."""
from fractions import Fraction as F
from round152_discover import dual_master
from round152_oracle import pi_json
from round152_normalized import price_normalized
from round152_math import h_exact,states,evaluate,outward
from round152_common import *

def run(role,label='global',iterations=6):
    from round150_lp import affinity
    from round100_gurobi_runtime import binding
    from round152_projection import project
    from round152_lp import solve
    from round152_cycle import floor_bundle
    configure();affinity();assert binding()['sha256']==DLL_SHA
    base='strongRN';scope=read(OUT/'domains'/role/'domain.json')['scope'];ss=scope['stations']
    target=OUT/'global'/f'{role}_{label}';target.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
    floor=floor_bundle(role,target/'floor_rows.json')
    if floor and read(floor)['rows'][0]['rhs']>read(OUT/'LP'/f'{role}_{base}'/'result.json')['L']+1e-6:
        solve(role,'RNfloor',base,str(floor));base='RNfloor'
    point=load_gz(OUT/'LP'/f'{role}_{base}'/'solution.json.gz')
    eta=read(OUT/'LP'/f'{role}_{base}'/'result.json')['L']
    proj=project(scope,point,target/'projection');assert proj['full_oracle_projection_feasible']
    columns={tuple(p['Y']) for p in proj['paths']}
    # Previous qualified oracle inventories are reusable pricing upper candidates,
    # not free online data or global lower bounds.
    for p in (OUT/'discovery').glob(f'{role}_*/iter*/pricing/result.json'):
        r=read(p)
        for stock in r['stocks']:
            if evaluate(scope,stock['Y'])['feasible']:columns.add(tuple(stock['Y']))
    active={s['i']:s['support'] for s in ss};records=[];rows=[]
    write(target/'plan.json',dict(UTC=utc(),role=role,parent=base,scope=scope,radius=.05,maximum_master_iterations=iterations,
                                full_support_pricing=True,no_inactive_penalty=True,oracle='normalized_integer_exact_positive',
                                question='Does complement-lift weakness explain free-LP migration beyond old RN?',before_results=True))
    for k in range(iterations):
        folder=target/f'iter{k:02}';psi,anchors,master=dual_master(scope,active,point,sorted(columns),.05,folder/'master')
        pi={(s['i'],y):float(h_exact(s,y))+psi[s['i'],y]-anchors[s['i']] for s in ss for y in s['support']}
        dot=math.fsum(pi[i,y]*point[f'state_{i}_{y}'] for i,y in pi)
        uncertainty=math.fsum(abs(pi[i,y]*point[f'state_{i}_{y}']) for i,y in pi if point[f'state_{i}_{y}']<0)
        rr=price_normalized(scope,pi,folder/'pricing',threshold=eta-dot+uncertainty+1e-6,cap=120)
        for stock in rr['stocks']:columns.add(tuple(stock['Y']))
        pi_hat={key:(v if abs(v)>=1e-12 else 0.) for key,v in pi.items()}
        correction=sum(max(F(pi_hat[s['i'],y])-F(pi[s['i'],y]) for y in s['support']) for s in ss)
        alpha=outward(F(rr['lower'])-correction,False);activity=alpha+math.fsum(pi_hat[i,y]*point[f'state_{i}_{y}'] for i,y in pi_hat)
        separated=activity>eta+uncertainty+1e-6
        record=dict(iteration=k,master=master,decision=rr['decision'],lower=rr['lower'],upper=rr['upper'],alpha=alpha,
                    pi=pi_json(pi_hat),eta=eta,activity=activity,violation=activity-eta,uncertainty=uncertainty,separated=separated,
                    pricing_seconds=rr['seconds'],column_count=len(columns),potential_transport_exact=str(correction))
        records.append(record);write(folder/'support.json',record)
        print(json.dumps(dict(role=role,iteration=k,decision=rr['decision'],violation=activity-eta,columns=len(columns))),flush=True)
        if separated:
            terms={'G':1.};terms.update({f'e_{s["i"]}':s['omega'] for s in ss if s['omega']})
            terms.update({f'state_{i}_{y}':-v for (i,y),v in pi_hat.items() if v})
            rows=[dict(name=f'r152_full_support_{label}',terms=terms,sense='>',rhs=alpha)];break
        if rr['decision']=='UNDECIDED':break
        H=math.fsum(float(h_exact(s,y))*point[f'state_{s["i"]}_{y}'] for s in ss for y in s['support'])
        if master['objective']+H<=eta+1e-7:break
    result=dict(role=role,parent=base,scope=scope,qualified=bool(rows),rows=rows,iterations=records,seconds=time.perf_counter()-start)
    write(target/'result.json',result)
    if rows:
        solve(role,label,base,str(target/'result.json'))
        result['LP']=read(OUT/'LP'/f'{role}_{label}'/'result.json');result['seconds']=time.perf_counter()-start
        write(target/'result.json',result)
    print(json.dumps(dict(role=role,qualified=bool(rows),seconds=result['seconds'],L=result.get('LP',{}).get('L'))),flush=True)

if __name__=='__main__':run(*sys.argv[1:3],iterations=int(sys.argv[3]) if len(sys.argv)>3 else 6)
