"""Independent reconstruction of actual inventory prices; no Optimize calls."""
from fractions import Fraction as F
from round143_math import outward
from round143_lp import semantics
from round152_math import unary_dp
from round156_review import exact_value,check_point
from round156_common import *

def run(label):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_pricing import Oracle
    from round155_oracle import reconstruct
    from round156_residual import native_row
    affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'review'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.start()
        for endpoint in sorted((OUT/'oracle').glob('*/*/result.json')):
            arm=read(endpoint);base=endpoint.parent;plan=read(base/'plan.json');scope=arm['scope'];ss=scope['stations']
            d={(s['i'],y):F(s['omega'])*abs(F(s['c'])*y-1) for s in ss for y in s['support']}
            fallback=F(scope['gamma_L'])+F(unary_dp(scope,d)['exact'])
            paths=[base/'pricing'] if arm['method']=='RN' else sorted(base.glob('price_*'))
            L=F(plan['initial_lower']);U=F(plan['initial_upper']);positive_lifts=0
            for path in paths:
                r=read(path/'result.json');c=read(path/'call.json');call=r['calls'][0]
                assert c['scope']==scope
                for v in r['stocks']:
                    checked=exact_value(scope,v['Y']);assert checked['feasible'] and checked['phi']==F(v['price_exact'])
                assert F(r['upper'])>=min(F(v['price_exact']) for v in r['stocks'])
                if arm['method']=='RN':
                    assert c['Seed']==0 and c['Threads']==1 and c['node_limit']==plan['node_limit']
                    assert sha(path/'model.mps')==c['model_SHA']
                    with gp.read(str(path/'model.mps'),env=env) as saved:
                        oracle=Oracle(scope,env,old_joint=True);m=oracle.model
                        anchors={int(k):F(v) for k,v in c['anchors_exact'].items()};scale=F(c['scale'])
                        m.setObjective(float(1/scale)*oracle.q+gp.quicksum(outward((value-anchors[k[0]])/scale,False)*oracle.x[k] for k,value in d.items()))
                        m.update();assert semantics(m)==semantics(saved)
                        correction=sum((max([F(0)]+[F(oracle.x[s['i'],y].Obj)-(d[s['i'],y]-anchors[s['i']])/scale for y in s['support']]) for s in ss),F(0))
                        correction+=max(F(0),(F(oracle.q.Obj)-1/scale)*F(scope['gamma_U']))
                        assert correction==F(c['objective_correction_scaled_exact'])
                        oracle.close()
                    def convert(bound):
                        positive=max(fallback,scale*(F(bound)-F(c['numerical_guard_scaled'])-correction)+sum(anchors.values(),F(0)))
                        return min(positive,F(r['zero_lower'])) if r['zero_lower'] is not None else positive
                    assert call['Status'] in (2,8) and call['bound_status_qualified']
                    expected=convert(call['native_bound']);assert F(r['lower'])<=expected
                else:
                    assert c['d_exact']=={f'{i}:{y}':str(v) for (i,y),v in d.items()}
                    assert F(c['inventory_upper_exact'])==U and F(c['tau_exact'])==(L+U)/2
                    with reconstruct(path/'matrix_delta.json.gz',gp,env) as saved:
                        dr=native_row(saved,'hard_cost_D_definition')
                        aiy={k:-F(dr['terms'].get(f'x[{k[0]},{k[1]}]',0.)) for k in d}
                        assert {f'{i}:{y}':float(v) for (i,y),v in aiy.items()}==c['actual_costs']
                        anchors={int(k):F(v) for k,v in c['anchors_exact'].items()};scale=F(c['scale']);A0=sum(anchors.values(),F(0))
                        eplus=sum((max([F(0)]+[aiy[s['i'],y]-(d[s['i'],y]-anchors[s['i']])/scale for y in s['support']]) for s in ss),F(0))
                        assert eplus==F(c['eplus_exact'])
                        lo=F(unary_dp(scope,aiy)['exact']);hi=-F(unary_dp(scope,{k:-v for k,v in aiy.items()})['exact'])
                        cap=(U-F(scope['gamma_L'])-A0)/scale+eplus
                        a=outward(lo,False);b=min(outward(hi,True),outward(cap,True)) if c['condition_upper'] else outward(hi,True)
                        assert [a,b]==c['cost_bounds']
                        D=saved.getVarByName('hard_cost_D');assert (D.LB,D.UB)==(a,b)
                        l,u=map(F,c['positive_S_bounds'])
                        tau=F(c['tau_exact']);boundA=F(len(ss))*F(scope['gamma_U'])*u
                        floor_row=native_row(saved,'floor_residual');g_row=native_row(saved,'G_residual')
                        sf=-F(floor_row['terms'].get('S',0.));sg=-F(g_row['terms'].get('S',0.))
                        pairs=[(ss[i]['i'],ss[j]['i']) for i in range(len(ss)) for j in range(i+1,len(ss))]
                        ac=-F(g_row['terms'].get(f'abs[{pairs[0][0]},{pairs[0][1]}]',0.))
                        assert all(-F(g_row['terms'].get(f'abs[{i},{j}]',0.))==ac for i,j in pairs)
                        assert all(-F(row['terms'].get(f'Sx[{i},{y}]',0.))==value for row in (floor_row,g_row) for (i,y),value in aiy.items())
                        eps=max(u*eplus+u*max(F(0),sf-(A0+F(scope['gamma_L'])-tau)/scale),
                            u*eplus+u*max(F(0),sg-(A0-tau)/scale)+boundA*max(F(0),ac-F(1,len(ss))/scale))
                        assert eps==F(c['additional_scaled_error_exact'])
                        intended={k:outward((value-anchors[k[0]])/scale,False) for k,value in d.items()}
                        intended_sf=F(outward((A0+F(scope['gamma_L'])-tau)/scale,False))
                        intended_sg=F(outward((A0-tau)/scale,False));intended_ac=F(outward(F(1,len(ss))/scale,False))
                        terms=sum(max(abs(F(intended[s['i'],y])) for y in s['support']) for s in ss)*u
                        guard=outward(F(1e-6)*(1+terms+max(abs(intended_sf),abs(intended_sg))*u+intended_ac*boundA),True)
                        assert guard==c['residual_guard_scaled'] and c['original_guard_retained']
                        for name,slope,endpoint_,sense in [('ll',l,F(a),'>'),('uu',u,F(b),'>'),('ul',u,F(a),'<'),('lu',l,F(b),'<')]:
                            row=native_row(saved,'tight_DP_cost_product_'+name)
                            assert row==dict(sense=sense,rhs=outward(-slope*endpoint_,sense=='<'),
                                terms={k:float(v) for k,v in {'hard_cost_W':F(1),'hard_cost_D':-slope,'S':-endpoint_}.items() if v})
                        for v in [c['witness'],*r['stocks']]:
                            original=exact_value(scope,v['Y'])
                            if original['S'] and (not c['condition_upper'] or original['H']<=U-F(scope['gamma_L'])):
                                check_point(saved,scope,v['Y'],c);positive_lifts+=1
                    tau=F(c['tau_exact']);guard=F(c['residual_guard_scaled']);epsilon=F(c['additional_scaled_error_exact'])
                    def convert(bound):
                        ell=scale*(F(bound)-guard-epsilon)
                        restricted=max(fallback,tau+ell/(u if ell>=0 else l))
                        lower=min(U,restricted) if c['condition_upper'] else restricted
                        if r['zero_exact'] is not None:lower=min(lower,F(r['zero_exact']))
                        return lower
                    assert call['bound_status_qualified'] and call['Status'] in (2,8,9,11,15)
                    if call['Status']==11:assert call['counterexample_stop'] and r['target_disproved']
                    expected=convert(call['native_bound']);assert expected==F(r['lower_exact'])
                    assert F(r['lower'])<=expected
                events=[json.loads(line) for line in (base/'events.jsonl').read_text().splitlines()]
                index=int(path.name.split('_')[-1]) if path.name.startswith('price_') else None
                for e in events:
                    if index is not None and e['call']!=index:continue
                    if e['kind']=='stock':assert exact_value(scope,e['Y'])['phi']==F(e['price_exact'])
                    else:assert F(e['lower'])<=convert(e['native_bound'])
                L=max(L,F(r['lower']));U=min(U,F(r['upper']))
                assert L<=U
            assert float(L)==arm['lower'] and float(U)==arm['upper']
            facts.append(dict(role=arm['role'],method=arm['method'],lower=float(L),upper=float(U),
                calls=len(paths),positive_actual_row_lifts=positive_lifts,endpoint_SHA=sha(endpoint),Optimize=0))
    write(target/'result.json',dict(PASS=True,facts=facts,Optimize=0,source_SHA=sha(__file__),
        source_residual_SHA=sha(ROOT/'scripts/round156_residual.py'),same_agent_independent_reconstruction=True))
    print(json.dumps(facts),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
