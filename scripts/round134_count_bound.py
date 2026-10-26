"""Exact stock-threshold coefficients and finite same-matrix tiny witnesses.

No solver dependency at import or in `tiny`. The old carrier is read without
alteration; all row arithmetic interprets stored binary64 values as rationals.
"""
from round134_common import *
from fractions import Fraction as F
import bisect,collections,itertools,zipfile

def downward(value):
    value=F(value);loaded=float(value)
    if F(loaded)>value:loaded=math.nextafter(loaded,-math.inf)
    assert F(loaded)<=value and math.isfinite(loaded)
    return loaded

def count_coefficients(supports,ratio_coefficient,B):
    supports={i:tuple(sorted(set(ys))) for i,ys in supports.items()}
    assert supports and set(supports)==set(ratio_coefficient)
    assert all(ys and all(type(y) is int and y>=0 for y in ys) and ratio_coefficient[i]>0 for i,ys in supports.items())
    n=len(supports);minima={i:min(ys) for i,ys in supports.items()};R=F(B)-sum(minima.values())
    if R<0:return dict(inventory_domain_infeasible=True,R=str(R),coefficients={},thresholds=[])
    ratios={i:[F(ratio_coefficient[i])*y for y in ys] for i,ys in supports.items()}
    levels=sorted({r for rs in ratios.values() for r in rs if r>0})
    coefficients={(i,y):F(0) for i,ys in supports.items() for y in ys};thresholds=[];previous=F(0)
    for t in levels:
        forced=[];optional=[]
        for i,ys in supports.items():
            if ratios[i][0]>=t:forced.append(i);continue
            k=bisect.bisect_left(ratios[i],t)
            if k<len(ys):optional.append((ys[k]-minima[i],i,ys[k]))
        optional.sort();used=0;k=0
        for cost,i,y in optional:
            assert cost>0
            if used+cost>R:break
            used+=cost;k+=1
        u=len(forced)+k;delta=t-previous
        assert 0<=u<=n and delta>0
        for i,ys in supports.items():
            first=bisect.bisect_left(ratios[i],t)
            for y in ys[first:]:coefficients[i,y]+=delta*(n-u)
        thresholds.append(dict(t=str(t),delta=str(delta),u=u,forced=forced,
            optional_minimum_increments=optional,optional_activations=k,paid_increment=used))
        previous=t
    return dict(inventory_domain_infeasible=False,B=str(F(B)),R=str(R),minima=minima,
        coefficients=coefficients,thresholds=thresholds)

def integer_extension(case,cars,pair,index):
    point=collections.defaultdict(F);y=list(case['b'])
    point[f'joint_mix[{index}]']=1
    for k,j in enumerate(pair):
        car=cars[k][j];point[f'mix{k}[{j}]']=1
        route=car['route'];route1=[i+1 for i in route];path=[0,*route1,0]
        assert len(route)==len(set(route)) and set(route)=={i for i,t in enumerate(car['v']) if t[2]}
        assert sum(t[0] for t in car['v'])*120<=case['T']
        if route:
            for a,b in zip(path,path[1:]):point[f'x_{k}_{a}_{b}']=1
        load=0
        for position,i in enumerate(route):
            p,d,z=car['v'][i];stock=case['b'][i]+d-p
            load+=p-d
            assert 0<=load<=case['Q'][k]
            point[f'load_{k}_{i+1}']=load
            point[f'ord_{k}_{i+1}']=position+1
            point[f'conn_{k}_{path[position]}_{i+1}']=len(route)-position
            point[f'mode_{k}_{i+1}']=int(p>0)
            point[f'theta{k}_{i}_{stock}']=1
        assert load==car['return_load']
        for i,(p,d,z) in enumerate(car['v']):
            for prefix,value in [('p',p),('d',d),('z',z)]:point[f'{prefix}_{k}_{i+1}']=value
            y[i]+=d-p
    for i,stock in enumerate(y,1):
        point[f'state_{i}_{stock}']=1;point[f'Y_{i}']=stock;point[f'r_{i}']=stock
    return point,y

def old_extensions(point,beta):
    from round88_ot_epigraph import make_plan,evaluate
    facts={}
    supports={i:(0,1,2) for i in range(1,5)};targets={i:1 for i in supports}
    for arm in ('B1','B2'):
        plan=make_plan(arm,supports,targets,F(0),beta)
        extension=collections.defaultdict(F,point)
        for name in plan.columns:
            pieces=name.split('_')
            if len(pieces)==4 and pieces[1] in ('C','Q'):
                kind,i,k=pieces[1],int(pieces[2]),int(pieces[3])
                extension[name]=sum(point.get(f"{'state' if kind=='C' else 'state_g'}_{i}_{y}",F(0)) for y in (0,1,2)[:k])
            else:extension[name]=F(0)
        failures=[]
        for row in plan.rows:
            residual=evaluate(row,extension)
            if (row.sense=='=' and residual!=0) or (row.sense=='>' and residual<0):
                failures.append(dict(name=row.name,residual=str(residual),sense=row.sense))
        assert not failures,(arm,failures[:3])
        facts[arm]=dict(rows=len(plan.rows),new_columns=len(plan.columns),exact_feasible=True,
            actual_prefix_values={n:str(extension[n]) for n in plan.columns if extension[n]},
            zero_absolute_difference_columns=True,failures=failures)
    return facts

def tiny():
    from round133_joint_check import CARRIER,CARRIER_SHA,PREFIX,row_check,regenerate,loaded_lower_bound_rows
    tick=time.perf_counter();carrier=ROOT/CARRIER
    assert sha(carrier)==CARRIER_SHA and 'gurobipy' not in sys.modules
    archive=zipfile.ZipFile(carrier);dependencies=[];cases={}
    for name,indices in [('J2',[18,41,49,52]),('J3',[18,48,56,59])]:
        def member(n):
            path=PREFIX+name+'/'+n;raw=archive.read(path)
            dependencies.append(dict(member=path,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
            return json.loads(raw)
        enumeration=member('enumeration.json');matrix=member('B_joint_exact_matrix.json')
        objective=member('original_objective_joint.json');case=enumeration['case'];cars=enumeration['cars']
        for k in range(2):assert set(regenerate(case,k))=={tuple(tuple(t) for t in p['v']) for p in cars[k]}
        pairs=[(a,b) for a,pa in enumerate(cars[0]) for b,pb in enumerate(cars[1]) if all(pa['v'][i][2]+pb['v'][i][2]<=1 for i in range(4))]
        assert pairs==[tuple(p) for p in enumeration['joint_pair_indices']]
        beta=F(matrix['bounds']['G'][1]);assert matrix['bounds']['G'][0]=='0' and beta==F(3,4)
        ratio_rows=loaded_lower_bound_rows(matrix)
        tc=count_coefficients({i:(0,1,2) for i in range(1,5)},{i:F(1) for i in range(1,5)},3)
        assert {k:v for k,v in tc['coefficients'].items() if v}=={(i,y):F(1 if y==1 else 4) for i in range(1,5) for y in (1,2)}
        point=collections.defaultdict(F);fleets=[]
        for index in indices:
            extension,y=integer_extension(case,cars,pairs[index],index)
            assert sorted(y)==[0,1,1,1]
            fleets.append(dict(index=index,pair=pairs[index],Y=y,weight='1/4',services=[cars[k][j]['v'] for k,j in enumerate(pairs[index])]))
            for column,value in extension.items():point[column]+=F(value,4)
        assert {tuple(f['Y']) for f in fleets}=={(0,1,1,1),(1,0,1,1),(1,1,0,1),(1,1,1,0)}
        for i in range(1,5):
            point[f'e_{i}']=F(1,4)
            assert point[f'Y_{i}']==point[f'r_{i}']==F(3,4)
            assert [point[f'state_{i}_{y}'] for y in (0,1,2)]==[F(1,4),F(3,4),0]
        point['r_max']=point['r_min']=F(3,4)
        point={k:F(v) for k,v in point.items() if v}
        old=row_check(matrix,point);assert old['status']=='EXACT_FEASIBLE',old
        penalty=[]
        for i in range(1,5):
            lhs=point[f'e_{i}'];rhs=sum(abs(F(y)-1)*point.get(f'state_{i}_{y}',F(0)) for y in (0,1,2))
            assert lhs>=rhs;penalty.append(dict(station=i,lhs=str(lhs),rhs=str(rhs)))
        old_cdf=old_extensions(point,beta)
        new=dict(point,G=F(3,16))
        for i in range(1,5):new[f'state_g_{i}_1']=new[f'zprod_{i}']=F(3,16)
        for i in range(1,5):
            for j in range(i+1,5):new[f'h_{i}_{j}']=F(1,2)
        check=row_check(matrix,new);assert check['status']=='EXACT_FEASIBLE',check
        new_cdf=old_extensions(new,beta)
        lhs=sum(new[f'h_{i}_{j}'] for i in range(1,5) for j in range(i+1,5))
        rhs=sum(c*new.get(f'state_{i}_{y}',F(0)) for (i,y),c in tc['coefficients'].items())
        assert lhs==rhs==3
        lam=F(objective['objective_coefficients']['e_1']);assert lam>F(1,16)
        assert {n:F(v) for n,v in objective['objective_coefficients'].items()}==dict(G=F(1),**{f'e_{i}':lam for i in range(1,5)})
        ip_values=[]
        for index,pair in enumerate(pairs):
            y=[case['b'][i]+sum(cars[k][j]['v'][i][1]-cars[k][j]['v'][i][0] for k,j in enumerate(pair)) for i in range(4)]
            tau=sum(y);A=sum(abs(a-b) for j,a in enumerate(y) for b in y[j+1:])
            ip_values.append((F(A,4*tau) if tau else F(0))+lam*sum(abs(a-1) for a in y))
        ip=min(ip_values);assert ip==lam+F(1,4)
        cases[name]=dict(status='EXACT_OLD_AND_NEW_FULL_MATRIX_PLUS_OLD_PENALTY_AND_CDF',
            G_bounds=['0',str(beta)],lambda_hat=str(lam),loaded_ratio_and_stock_rows=ratio_rows,
            balanced_joint_columns=fleets,old_point={n:str(v) for n,v in point.items()},
            new_point={n:str(v) for n,v in new.items()},old_full_check=old,new_full_check=check,
            old_state_penalty_check=penalty,old_CDF_extensions=old_cdf,new_CDF_extensions=new_cdf,
            TC_lhs=str(lhs),TC_rhs=str(rhs),L_old=str(lam),L_new=str(lam+F(3,16)),
            exact_increment='3/16',integer_optimum=str(ip),remaining_gap='1/16',gap_closed_fraction='3/4',
            lower_proof='a+2b<=3; P>=4-a; sumZ<=4g+beta*b; a+4b<=4sumZ; beta<=1 implies g>=a/16; lambda_hat>1/16 implies F>=lambda_hat+3/16',
            added_controls_are_exact_algebraic_extensions_not_reexported_native_matrix=True)
    assert 'gurobipy' not in sys.modules
    write(OUT/'math/tiny_exact.json',dict(UTC=utc(),status='PASS',cases=cases,dependencies=dependencies,
        carrier_path=CARRIER,carrier_pin='52b02252ba47e8228b73e071d6ed692385a4f816',carrier_SHA256=CARRIER_SHA,
        seconds=time.perf_counter()-tick,Optimize=0,vendor_DLL_loads=0,source_SHA256=sha(__file__)))
    print(json.dumps({name:{'rows':c['new_full_check']['rows'],'bounds':c['new_full_check']['bounds'],
        'L_old':c['L_old'],'L_new':c['L_new'],'remaining_gap':c['remaining_gap']} for name,c in cases.items()}))

if __name__=='__main__':tiny()
