"""Separate saved-model, exact original-J/resource and route readers. Same agent."""
from fractions import Fraction as F
from itertools import combinations,permutations
from round159_common import *
from round157_inventory import value
from round143_lp import residual,semantics

def check_resource(source,p):
    d=source['data'];scope=source['scope'];Y=p['Y'];owners=p['owner'];n=d['n'];m=len(d['Q'])
    v=value(scope,Y);assert v['feasible'];assert abs(float(v['phi'])-p['J'])<1e-12
    seen=[];vehicles=[]
    for k in range(m):
        ids=[i for i in range(1,n+1) if Y[i-1]!=d['initial'][i] and owners[i-1]==k];seen+=ids
        assert all(abs(Y[i-1]-d['initial'][i])<=d['Q'][k] for i in ids)
        P=sum(max(0,d['initial'][i]-Y[i-1]) for i in ids);D=sum(max(0,Y[i-1]-d['initial'][i]) for i in ids)
        assert 0<=P-D<=d['Q'][k]
        ell=max([F(0)]+[F(row['lower']) for row in source['rawbounds'] if set(row['stations'])<=set(ids)])
        time=F(d['pickup']+d['drop'])*P+ell
        assert time<=F(d['T']),('not nominal original-T feasible',k,str(time))
        vehicles.append(dict(vehicle=k,stations=ids,P=P,D=D,return_load=P-D,required_time=float(time),required_time_exact=str(time)))
    assert sorted(seen)==[i for i in range(1,n+1) if Y[i-1]!=d['initial'][i]]
    return dict(Y=Y,owner=owners,J=float(v['phi']),J_exact=str(v['phi']),G=float(v['G']),H=float(v['penalty']),
        vehicles=vehicles,original_T_resource_feasible=True,physical_U=None,global_lower=None)

def lift(source,model,p):
    from round157_family_floor import inventory_point
    from types import SimpleNamespace
    o=SimpleNamespace(scope=source['scope'],model=model)
    point,_=inventory_point(o,p['Y'],[])
    for k in range(len(source['data']['Q'])):
        P=D=0
        for i in range(1,source['data']['n']+1):
            if p['Y'][i-1]!=source['data']['initial'][i] and p['owner'][i-1]==k:
                point[f'resource_service[{k},{i},{p["Y"][i-1]}]']=1
                point[f'resource_visit[{k},{i}]']=1
                P+=max(0,source['data']['initial'][i]-p['Y'][i-1]);D+=max(0,p['Y'][i-1]-source['data']['initial'][i])
        point[f'resource_pickup[{k}]']=P;point[f'resource_drop[{k}]']=D
    return point

def qualify():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    records=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for role,label in [('R-X35-S-T2','qualify_rx'),('N-B35-S','qualify_nb')]:
            source=read(OUT/'inputs_v2'/role/'source.json');folder=OUT/'runs'/label
            p=read(folder/'start.json');accepted=check_resource(source,p);d=source['data'];plan=source['budget_plan']
            with gp.read(str(OUT/'inputs_v2'/role/'rn.mps'),env=env) as original:
                original_sem=semantics(original);old_rows={r.ConstrName for r in original.getConstrs()};old_cols={v.VarName for v in original.getVars()}
                for mode in ('baseline','joint'):
                    with gp.read(str(folder/(mode+'.mps')),env=env) as m:
                        vs={v.VarName:v for v in m.getVars()};actual=semantics(m,old_cols,old_rows)
                        assert actual['rows']==original_sem['rows'] and actual['ModelSense']==1 and actual['ObjCon']==original_sem['ObjCon']
                        assert [(v[0],v[3:]) for v in actual['columns']]==[(v[0],v[3:]) for v in original_sem['columns']]
                        released=read(folder/(mode+'.json'))['released']
                        for s in source['scope']['stations']:
                            i=s['i'];outside=i not in released
                            for y in s['support']:
                                var=vs[f'x[{i},{y}]']
                                if mode=='joint' and outside:assert var.LB==var.UB==int(y==p['Y'][i-1])
                                elif mode=='baseline' and p['owner'][i-1]<0:assert var.LB==var.UB==int(y==d['initial'][i])
                                else:assert (var.LB,var.UB)==(0,1)
                            for k in range(len(d['Q'])):
                                for y in s['support']:
                                    name=f'resource_service[{k},{i},{y}]'
                                    if name not in vs:assert y==d['initial'][i] or abs(y-d['initial'][i])>d['Q'][k];continue
                                    expected=0 if (mode=='baseline' or outside) and k!=p['owner'][i-1] else 1
                                    assert vs[name].LB==0 and vs[name].UB==expected
                        # Read every actual conditional budget and its emitted RHS.
                        for k in range(len(d['Q'])):
                            assert vs[f'resource_pickup[{k}]'].UB==plan['U']
                            for no,r in enumerate(plan['kept']):
                                c=m.getConstrByName(f'rounded_{k}_{no}');e=m.getRow(c)
                                terms={e.getVar(j).VarName:e.getCoeff(j) for j in range(e.size()) if e.getCoeff(j)}
                                expected={f'resource_visit[{k},{i}]':1 if r['budget']<0 else plan['U']-r['budget'] for i in r['stations']}
                                if r['budget']>=0:expected[f'resource_pickup[{k}]']=1
                                assert terms==expected and c.Sense=='<'
                                assert c.RHS==(len(r['stations'])-1 if r['budget']<0 else r['budget']+(plan['U']-r['budget'])*len(r['stations']))
                        point=lift(source,m,p);q=residual(m,point);assert max(q['constraints'],q['bounds'])<1e-7,q
                        m.read(str(folder/(mode+'.mst')));start={v.VarName:v.Start for v in m.getVars()};qs=residual(m,start)
                        assert max(qs['constraints'],qs['bounds'])<1e-7,qs
                        transport=source['transport'];original_objective=F(transport['scale'])*F(q['objective'])+sum(map(F,transport['anchors_exact'].values()),F(0))
                        assert abs(original_objective-F(accepted['J_exact']))<F('1e-12')
                        # A duplicated owner must violate the service assignment equality.
                        bad=dict(point);changed=next(i for i in range(1,d['n']+1) if p['Y'][i-1]!=d['initial'][i])
                        other=next(k for k in range(len(d['Q'])) if k!=p['owner'][changed-1])
                        bad[f'resource_service[{other},{changed},{p["Y"][changed-1]}]']=1
                        assert residual(m,bad)['constraints']>=1
                        records.append(dict(role=role,mode=mode,model_SHA=sha(folder/(mode+'.mps')),rows=m.NumConstrs,columns=m.NumVars,
                            all_RN_rows_preserved=True,objective_mapping_error=float(original_objective-F(accepted['J_exact'])),
                            full_start=qs,independent_lift=q,release_and_owner_bounds_checked=True,conditional_budget_rows_checked=len(plan['kept'])*len(d['Q']),duplicate_owner_rejected=True))
    write(OUT/'qualification.json',dict(UTC=utc(),PASS=True,Optimize=0,facts=records,
        review_identity='same agent; separate Python exact arithmetic/saved C++ model reader',
        inherited_boundary_qualification='R158 actual_raw_implication and R92 envelope; no nominal-floor substitution',
        global_lower_transport=False,not_an_online_production_admission=True))

def results(label,role):
    from round100_gurobi_runtime import gp
    from round150_lp import affinity
    affinity();source=read(OUT/'inputs_v2'/role/'source.json');folder=OUT/'runs'/label;accepted=[];calls=[]
    for path in sorted(folder.glob('*_events.jsonl')):
        for text in path.read_text().splitlines():
            p=json.loads(text);checked=check_resource(source,p)
            accepted.append(dict(checked,event_file=path.name,event_seconds=p['seconds'],iteration=p['iteration']))
    best=read(folder/'best.json');checked=check_resource(source,best)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for text in (folder/'calls.jsonl').read_text().splitlines():
            c=json.loads(text);stem=folder/f'call_{c["iteration"]}'
            log=Path(str(stem)+'.log').read_text(errors='replace').lower()
            assert not any(w in log for w in ('numerical trouble','unscaled primal violation','unscaled dual violation'))
            with gp.read(str(stem)+'.mps',env=env) as m:
                sol=Path(str(stem)+'.sol')
                if sol.exists():
                    vals={line.split()[0]:float(line.split()[1]) for line in sol.read_text().splitlines() if line and not line.startswith('#')}
                    q=residual(m,vals);integer=max([abs(vals[v.VarName]-round(vals[v.VarName])) for v in m.getVars() if v.VType!='C']+[0])
                    assert max(q['constraints'],q['bounds'],integer)<=1e-5,(stem,q,integer)
                    c['saved_solution_residual']=q;c['integer_violation']=integer
            c['model_SHA']=sha(str(stem)+'.mps');calls.append(c)
        # A full old raw resource lift at the new point. No new Optimize.
        from round153_pricing import Oracle
        from round157_floor import attach
        o=Oracle(source['scope'],env,old_joint=True);attach(o,source['data'],source['rawbounds'])
        full=lift(source,o.model,best);q=residual(o.model,full);assert max(q['constraints'],q['bounds'])<1e-7,q
        review=OUT/'review'/label;review.mkdir(parents=True,exist_ok=False)
        o.model.write(str(review/'full_resource.mps'));save_gz(review/'full_point.json.gz',full);o.close()
    write(OUT/'review'/f'{label}.json',dict(UTC=utc(),PASS=True,role=role,accepted=accepted,best=checked,calls=calls,
        full_raw_resource_lift=q,all_restricted_bounds_excluded_from_global_ledger=True,physical_U=None,Optimize=0))

def completion(label,role):
    from round157_fleet import verify
    source=read(OUT/'inputs_v2'/role/'source.json');record=read(OUT/'runs'/label/'completion.json')
    checked=check_resource(source,record['point']);d=source['data'];routes=[]
    for row in record['vehicles']:
        if not row['complete'] or 'route' not in row:continue
        nodes=row['route'];k=row['vehicle'];load=0;P=0
        for i in nodes[1:-1]:load+=d['initial'][i]-checked['Y'][i-1];assert 0<=load<=d['Q'][k];P+=max(0,d['initial'][i]-checked['Y'][i-1])
        travel=sum((F(d['distance'][i][j]) for i,j in zip(nodes,nodes[1:])),F(0))
        assert travel==F(row['travel_scaled'])/2**53
        assert abs(float(travel+F(120)*P)-row['total'])<1e-10
        if 'unloaded_travel_scaled' in row:
            unloaded=F(row['unloaded_travel_scaled'])/2**53;assert unloaded<=travel
            row['pure_tour_handling_infeasible']=unloaded+120*P>F(d['T']+1e-7)
            row['prefix_load_penalty']=float(travel-unloaded)
        routes.append(dict(vehicle=k,nodes=nodes,operations=[dict(station=i,pickup=max(0,d['initial'][i]-checked['Y'][i-1]),drop=max(0,checked['Y'][i-1]-d['initial'][i])) for i in nodes[1:-1]]))
    physical=None
    if record['classification']=='PHYSICAL_FEAS':
        witness=dict(routes=routes);physical=verify(d,witness);assert physical['original_T_feasible'];assert physical['Y']==checked['Y'];assert abs(physical['J']-checked['J'])<1e-7
        write(OUT/'review'/f'{label}_witness.json',witness)
    write(OUT/'review'/f'{label}.json',dict(UTC=utc(),PASS=True,scope='fixed Y and owner, all elementary visit orders; finite DP slot capacity',
        result=record,resource=checked,physical=physical,global_inventory_exclusion=False,Optimize=0,
        review_identity='same agent independent exact route-cost/prefix reader; DP optimality from recurrence and qualified fixtures'))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
