"""Bounded complete tiny universes; no optimization at import or freeze.

Single-car plans and every disjoint fleet pair are enumerated in full. The
reference is the actual current S2 canonical relaxation plus same-domain car
hulls, R98 theta, every small threshold-event rank and every R54 cutset row.
"""
from round132_common import *
import collections,copy,itertools,math
from fractions import Fraction as F

CASES=[dict(id='J1',b=[2,0,1,1],Q=[1,2],T=240),
       dict(id='J2',b=[2,1,0,0],Q=[1,2],T=240),
       dict(id='J3',b=[2,1,0,0],Q=[1,2],T=360),
       dict(id='J4',b=[1,1,1,1],Q=[1,1],T=240)]

def freeze():
    write(OUT/'E_experiment_plan.json',dict(UTC=utc(),cases=CASES,n=4,vehicles=2,capacity=[2]*4,target=[1]*4,
        weights=[1]*4,coordinates='depot and all four stations at(0,0); no exterior stations',handling=[60,60],lambda_value=.15,
        R='all finite integral one-way service plans; each operation<=Q, final return0..Q, 120*sum pickups<=T; enumerate all orders and retain a physical prefix-feasible route',
        completeness='all station options, all vehicle plans, all disjoint fleet pairs; no restricted-column maximum used as an upper bound',
        reference='current S2 canonical all-continuous root + same R_k convex combinations + R98 vehicle/state theta + all station-distinct threshold-event rank rows using exact joint maximum + all R54 IR-IN/OUT subsets',
        rank_relation='exact same-domain ranks may be stronger than R101 necessary-travel ranks; every legal complete tiny fleet embeds; no unqualified general domain containment claim',
        order='J1,J2,J3,J4; event-count controls first then64 fixed integer quantity/ownership support directions per case; current objective reoptimized on reference and full joint columns',
        normal_seed='SHA256 round132-joint-v2|case|direction|coordinate mapped to{-2,-1,0,1,2}',
        limits=dict(total_seconds=10800,per_LP_seconds=60,per_car_plans=4096,joint_pairs=65536,exact_basis_free_columns=90,exact_basis_seconds=45),
        strict_witness='exact joint integer support RHS plus rational full-reference extension, each car mixing certificate, theta/rank/IR checks; otherwise NUMERICAL_CANDIDATE_ONLY with exact obstacle',
        subsequent_gate='No real-role model use unless a valid joint support upper bound includes all outside donors/receivers and the exact same full R_k; tiny cuts do not transfer by deleting other stations',
        native_calls_serial=True,no_D_C_information_transfer=True,Optimize=0))
    print('E tiny universe, directions, reference structures and exit bounds fixed; no enumeration/Optimize.')

def plans(case,k):
    q=case['Q'][k];options=[]
    for b in case['b']:
        options.append([(0,0,0)]+[(p,0,1) for p in range(1,min(b,q)+1)]+[(0,d,1) for d in range(1,min(2-b,q)+1)])
    result=[]
    for v in itertools.product(*options):
        P=sum(x[0] for x in v);D=sum(x[1] for x in v)
        if not (0<=P-D<=q and 120*P<=case['T']):continue
        active=[i for i,x in enumerate(v) if x[2]];route=None
        for order in itertools.permutations(active):
            load=0;valid=True
            for i in order:
                load+=v[i][0]-v[i][1]
                if not 0<=load<=q:valid=False;break
            if valid:route=list(order);break
        if route is None:continue
        result.append(dict(v=[list(x) for x in v],route=route,pickup=P,drop=D,return_load=P-D))
    assert len(result)<=4096;return result

def vector(pair):return tuple(x for car in pair for station in car['v'] for x in station)
def events(case):
    pools=[]
    for i,b in enumerate(case['b']):
        pools.append([None]+[(i,'p',q) for q in range(1,b+1)]+[(i,'d',q) for q in range(1,3-b)])
    return [tuple(e for e in combo if e is not None) for combo in itertools.product(*pools) if any(e is not None for e in combo)]
def rank_value(pair,es):
    return sum(any(car['v'][i][0 if sign=='p' else 1]>=q for car in pair) for i,sign,q in es)

def rational_extension(model,deadline):
    """Recover one exact rational active basis, then check every row and bound.

    A failure returns an explicit numerical-only obstacle, never a strict proof.
    All coefficients are rationals of the actual loaded binary64 matrix.
    """
    vs=model.getVars();values=[v.X for v in vs];fixed={};free=[]
    for j,v in enumerate(vs):
        if abs(values[j]-v.LB)<=1e-8:fixed[j]=F.from_float(v.LB)
        elif v.UB<1e90 and abs(values[j]-v.UB)<=1e-8:fixed[j]=F.from_float(v.UB)
        else:free.append(j)
    if len(free)>90:return dict(status='UNKNOWN',obstacle='more than90 free basis columns',free=len(free))
    by={v.VarName:j for j,v in enumerate(vs)};rows=[];active=[]
    for con in model.getConstrs():
        if time.perf_counter()>deadline:return dict(status='UNKNOWN',obstacle='exact basis45-second matrix-read exit')
        row=model.getRow(con);c={by[row.getVar(i).VarName]:F.from_float(row.getCoeff(i)) for i in range(row.size())}
        rhs=F.from_float(con.RHS);sense=con.Sense;rows.append((c,sense,rhs,con.ConstrName))
        residual=sum(float(a)*values[j] for j,a in c.items())-float(rhs)
        if sense=='=' or abs(residual)<=1e-7:active.append((sense!='=',c,rhs))
    pivots={}
    for _,c,rhs in sorted(active,key=lambda q:q[0]):
        if time.perf_counter()>deadline:return dict(status='UNKNOWN',obstacle='exact basis45-second exit')
        r={j:a for j,a in c.items() if j not in fixed};b=rhs-sum(a*fixed[j] for j,a in c.items() if j in fixed)
        for pivot,(old,ob) in pivots.items():
            if pivot not in r:continue
            scale=r.pop(pivot);b-=scale*ob
            for j,a in old.items():
                if j==pivot:continue
                r[j]=r.get(j,F(0))-scale*a
                if not r[j]:r.pop(j)
        if not r:continue
        pivot=min(r);scale=r[pivot];r={j:a/scale for j,a in r.items()};b/=scale
        pivots[pivot]=(r,b)
        if len(pivots)==len(free):break
    if len(pivots)!=len(free):return dict(status='UNKNOWN',obstacle='active rational basis rank incomplete',rank=len(pivots),free=len(free))
    answer=dict(fixed)
    for pivot in sorted(pivots,reverse=True):
        if time.perf_counter()>deadline:return dict(status='UNKNOWN',obstacle='exact basis45-second back-substitution exit')
        r,b=pivots[pivot];answer[pivot]=b-sum(a*answer[j] for j,a in r.items() if j!=pivot)
    bad=[]
    for j,v in enumerate(vs):
        if time.perf_counter()>deadline:return dict(status='UNKNOWN',obstacle='exact basis45-second bound-check exit')
        if answer[j]<F.from_float(v.LB) or (v.UB<1e90 and answer[j]>F.from_float(v.UB)):bad.append('bound:'+v.VarName)
    for c,sense,rhs,name in rows:
        if time.perf_counter()>deadline:return dict(status='UNKNOWN',obstacle='exact basis45-second full-row-check exit')
        lhs=sum(a*answer[j] for j,a in c.items())
        if (sense=='=' and lhs!=rhs) or (sense=='<' and lhs>rhs) or (sense=='>' and lhs<rhs):bad.append(name)
    if bad:return dict(status='UNKNOWN',obstacle='recovered active basis violates exact retained row/bound',first_bad=bad[:12])
    return dict(status='EXACT_EXTENSION',values={v.VarName:str(answer[j]) for j,v in enumerate(vs) if answer[j]},
        all_rows_and_bounds_checked=len(rows)+len(vs),fraction_semantics='exact rationals of loaded binary64 coefficients')

def exact_matrix(model,path):
    rows=[]
    for con in model.getConstrs():
        row=model.getRow(con)
        rows.append(dict(name=con.ConstrName,sense=con.Sense,RHS=str(F.from_float(con.RHS)),
            coefficients={row.getVar(i).VarName:str(F.from_float(row.getCoeff(i))) for i in range(row.size())}))
    write(path,dict(rows=rows,bounds={v.VarName:[str(F.from_float(v.LB)),str(F.from_float(v.UB))] for v in model.getVars()},
        coefficient_contract='exact rationals of actual loaded binary64 coefficients; all types relaxed to continuous'))

def objective_receipt(model,objective_terms,constant):
    """Retain the existing LP return; no extra solve or evidence promotion."""
    fact=dict(native_status=model.Status,Runtime=model.Runtime,Work=model.Work,model_sense=model.ModelSense,
        objective_coefficients={n:str(F.from_float(a)) for n,a in objective_terms.items()},
        objective_constant=str(F.from_float(constant)),
        numeric_policy=dict(FeasibilityTol=model.Params.FeasibilityTol,OptimalityTol=model.Params.OptimalityTol),
        no_extra_Optimize=True,strict_rational_optimality_not_claimed=True)
    if model.Status==2:
        fact.update(objective=model.ObjVal,
            values={v.VarName:str(F.from_float(v.X)) for v in model.getVars() if v.X},
            reduced_costs={v.VarName:str(F.from_float(v.RC)) for v in model.getVars() if v.RC},
            row_duals_by_index={str(j):str(F.from_float(c.Pi)) for j,c in enumerate(model.getConstrs()) if c.Pi})
        quality={}
        for name in ['ConstrVio','ConstrResidual','BoundVio','DualVio','DualResidual','ComplVio']:
            try:quality[name]=model.getAttr(name)
            except Exception:quality[name]=None
        fact['native_quality']=quality
    return fact

def add_reference(m,case,cars,joint,gp):
    original={v.VarName:v for v in m.getVars()};lam=[]
    for k,ps in enumerate(cars):
        ll=m.addVars(len(ps),lb=0,ub=1,name=f'mix{k}');m.addConstr(ll.sum()==1,name=f'car{k}_convexity');lam.append(ll)
        for i in range(4):
            for t,prefix in enumerate(['p','d','z']):
                m.addConstr(original[f'{prefix}_{k}_{i+1}']==gp.quicksum(ps[j]['v'][i][t]*ll[j] for j in range(len(ps))),name=f'car{k}_{prefix}{i}')
    theta={}
    for i,b in enumerate(case['b']):
        states=[y for y in range(3) if f'state_{i+1}_{y}' in original and y!=b]
        for k in range(2):
            for y in states:
                if abs(y-b)<=case['Q'][k]:theta[k,i,y]=m.addVar(lb=0,ub=1,name=f'theta{k}_{i}_{y}')
        for y in states:m.addConstr(gp.quicksum(theta[k,i,y] for k in range(2) if (k,i,y) in theta)==original[f'state_{i+1}_{y}'],name=f'theta_state{i}_{y}')
        for k in range(2):
            ys=[y for y in states if (k,i,y) in theta]
            m.addConstr(gp.quicksum(theta[k,i,y] for y in ys)==original[f'z_{k}_{i+1}'])
            m.addConstr(gp.quicksum(max(b-y,0)*theta[k,i,y] for y in ys)==original[f'p_{k}_{i+1}'])
            m.addConstr(gp.quicksum(max(y-b,0)*theta[k,i,y] for y in ys)==original[f'd_{k}_{i+1}'])
    rank_records=[]
    for j,es in enumerate(events(case)):
        rhs=max(rank_value(pair,es) for pair in joint)
        terms=[]
        for i,sign,q in es:
            for y in range(3):
                n=f'state_{i+1}_{y}'
                if n in original and ((sign=='p' and y<=case['b'][i]-q) or (sign=='d' and y>=case['b'][i]+q)):terms.append(original[n])
        m.addConstr(gp.quicksum(terms)<=rhs,name=f'exact_threshold_rank{j}')
        rank_records.append(dict(events=es,RHS=rhs))
    ir=0
    for mask in range(1,16):
        inside={i+1 for i in range(4) if mask&(1<<i)};outside=set(range(5))-inside
        net=gp.quicksum(original[f'Y_{i}']-case['b'][i-1] for i in inside)
        incoming=gp.quicksum(case['Q'][k]*original[f'x_{k}_{a}_{b}'] for k in range(2) for a in outside for b in inside)
        outgoing=gp.quicksum(case['Q'][k]*original[f'x_{k}_{a}_{b}'] for k in range(2) for a in inside for b in outside)
        m.addConstr(net<=incoming,name=f'IR_IN{mask}');m.addConstr(-net<=outgoing,name=f'IR_OUT{mask}');ir+=2
    m.update();return original,rank_records,ir

def run():
    from round100_gurobi_runtime import gp,binding
    from round100_idle import ensure_idle
    ensure_idle()
    assets=frozen_identity()
    plan=read(OUT/'E_experiment_plan.json');start=time.perf_counter();root=OUT/'joint';root.mkdir(exist_ok=False)
    write(root/'identity.json',dict(UTC=utc(),assets=assets,plan_SHA=sha(OUT/'E_experiment_plan.json'),
        runner_SHA=sha(__file__),base=BASE,all_original_production_sources_checked=True))
    summaries=[];budget_exit=False
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start();runtime=binding()
        for case in plan['cases']:
            if time.perf_counter()-start>=10000:budget_exit=True;break
            d=root/case['id'];d.mkdir();cars=[plans(case,k) for k in range(2)]
            joint=[(a,b) for a in cars[0] for b in cars[1] if all(a['v'][i][2]+b['v'][i][2]<=1 for i in range(4))]
            assert len(joint)<=65536
            write(d/'enumeration.json',dict(case=case,cars=cars,joint_pair_indices=[(cars[0].index(a),cars[1].index(b)) for a,b in joint],complete_universe=True))
            write(d/'stage.json',dict(stage='complete enumeration sealed',seconds=time.perf_counter()-start))
            inp=d/'input.txt';inp.write_text('4 2 '+json.dumps(case['Q'])+'\ncapacities = [100000,2,2,2,2]\ninitial = '+str([50000]+case['b'])+'\ntarget = [0,1,1,1,1]\nweights = [0,1,1,1,1]\nmin_ratio = [0,0,0,0,0]\npoints = [(0,0),(0,0),(0,0),(0,0),(0,0)]\n',encoding='utf-8')
            ratios=case['b'];S=sum(ratios);G=sum(abs(x-y) for i,x in enumerate(ratios) for y in ratios[i+1:])/(4*S) if S else 0.
            U=G+.15*sum(abs(x-1) for x in ratios);beta=min(U,.75)
            subprocess.run(list(map(str,[EXPORTER,inp,case['T'],0,beta,U,'s2-root',d/'canonical'])),cwd=ROOT,env=environment(),check=True,capture_output=True,timeout=120)
            with gp.read(str(d/'canonical/original.lp'),env=env) as m:
                m.Params.Threads=1;m.Params.Seed=0;m.Params.TimeLimit=60
                for v in m.getVars():v.VType=gp.GRB.CONTINUOUS
                m.update();objective=m.getObjective();objective_constant=objective.getConstant()
                objective_terms={objective.getVar(t).VarName:objective.getCoeff(t) for t in range(objective.size())}
                cutoff_present=False
                for con in m.getConstrs():
                    row=m.getRow(con);terms={row.getVar(t).VarName:row.getCoeff(t) for t in range(row.size())}
                    if con.Sense=='<' and con.RHS==U and terms==objective_terms:cutoff_present=True
                canonical_scope=dict(requested_cutoff=U,actual_objective_cutoff_present=cutoff_present,
                    W_present=any(v.VarName=='W_SP' for v in m.getVars()),G_bounds=[0,beta],
                    production_backend_exposure='none; physical startup-zero' if U==0 else 'diagnostic canonical root, not a production timing arm')
                write(d/'canonical_scope.json',canonical_scope)
                original,ranks,ir=add_reference(m,case,cars,joint,gp)
                write(d/'rank_rows.json',ranks);m.write(str(d/'B_ref.lp'));records=[];best_numeric=None;best_strict=None
                exact_matrix(m,d/'B_ref_exact_matrix.json')
                write(d/'stage.json',dict(stage='complete reference model sealed',seconds=time.perf_counter()-start,
                    canonical_SHA=sha(d/'canonical/original.lp'),reference_exact_matrix_SHA=sha(d/'B_ref_exact_matrix.json')))
                names=[f'{prefix}_{k}_{i+1}' for k in range(2) for i in range(4) for prefix in ['p','d','z']]
                # Pure threshold-event count controls precede quantity queries,
                # exactly as fixed in the pre-execution plan.
                controls=[]
                for r in ranks[::max(1,len(ranks)//8)][:8]:
                    terms=[]
                    for i,sign,q in r['events']:
                        for y in range(3):
                            n=f'state_{i+1}_{y}'
                            if n in original and ((sign=='p' and y<=case['b'][i]-q) or (sign=='d' and y>=case['b'][i]+q)):terms.append(original[n])
                    m.setObjective(gp.quicksum(terms),gp.GRB.MAXIMIZE);m.optimize()
                    if m.Status==gp.GRB.INFEASIBLE:
                        write(d/'reference_infeasibility_contradiction.json',dict(stage='event control',known_empty_fleet=True))
                        raise RuntimeError('Full reference excludes its known feasible empty fleet')
                    value=m.ObjVal if m.Status==gp.GRB.OPTIMAL else None
                    controls.append(dict(events=r['events'],exact_rank=r['RHS'],status=m.Status,value=value,
                        qualification='PASS' if value is not None and value<=r['RHS']+1e-7 else 'UNKNOWN' if value is None else 'CONTRADICTION'))
                    write(d/'event_controls.json',controls)
                    if value is not None and value>r['RHS']+1e-7:
                        write(d/'control_contradiction.json',dict(control=controls[-1],priority='investigate reference/rank/numeric issue; no novelty claim'))
                        raise RuntimeError('Pure event control contradicts its retained exact rank')
                for j in range(64):
                    if time.perf_counter()-start>=10000:budget_exit=True;break
                    w=[int(hashlib.sha256(f'round132-joint-v2|{case["id"]}|{j}|{t}'.encode()).hexdigest()[:8],16)%5-2 for t in range(24)]
                    rhs=max(sum(a*b for a,b in zip(w,vector(pair))) for pair in joint)
                    m.setObjective(gp.quicksum(a*original[n] for a,n in zip(w,names)),gp.GRB.MAXIMIZE);m.optimize()
                    if m.Status==gp.GRB.INFEASIBLE:
                        write(d/'reference_infeasibility_contradiction.json',dict(stage='quantity support',direction=j,known_empty_fleet=True))
                        raise RuntimeError('Full reference excludes its known feasible empty fleet')
                    if m.Status!=gp.GRB.OPTIMAL:
                        records.append(dict(direction=j,status='UNKNOWN',native_status=m.Status))
                        write(d/'support_queries.json',dict(records=records,controls=controls));continue
                    value=m.ObjVal;gap=value-rhs
                    records.append(dict(direction=j,w=w,Psi_exact=rhs,reference_support=value,gap=gap,Work=m.Work,Runtime=m.Runtime))
                    if gap>1e-7 and (best_numeric is None or gap>best_numeric['gap'] or best_strict is None or gap>best_strict['gap']):
                        proof=rational_extension(m,time.perf_counter()+45)
                        if proof['status']=='EXACT_EXTENSION':
                            vals=proof['values'];exact_lhs=sum(F(a)*F(vals.get(n,'0')) for a,n in zip(w,names))
                            proof.update(lhs=str(exact_lhs),RHS=rhs,strict=exact_lhs>rhs)
                        item=dict(direction=j,w=w,gap=gap,Psi_exact=rhs,proof=proof,
                            reference_exact_matrix_SHA=sha(d/'B_ref_exact_matrix.json'),enumeration_SHA=sha(d/'enumeration.json'))
                        if best_numeric is None or gap>best_numeric['gap']:best_numeric=item
                        if proof.get('strict') and (best_strict is None or gap>best_strict['gap']):best_strict=item
                        write(d/'best_separation.json',dict(best_numeric=best_numeric,best_strict=best_strict))
                    write(d/'support_queries.json',dict(records=records,controls=controls))
                m.setObjective(objective,gp.GRB.MINIMIZE);m.optimize();before=m.ObjVal if m.Status==gp.GRB.OPTIMAL else None
                before_receipt=objective_receipt(m,objective_terms,objective_constant)
                write(d/'original_objective_reference.json',before_receipt)
                if m.Status==gp.GRB.INFEASIBLE:
                    write(d/'reference_infeasibility_contradiction.json',dict(stage='original objective',known_empty_fleet=True))
                    raise RuntimeError('Full reference excludes its known feasible empty fleet')
                ll=m.addVars(len(joint),lb=0,ub=1,name='joint_mix');m.addConstr(ll.sum()==1)
                vectors=[vector(pair) for pair in joint]
                for t,n in enumerate(names):m.addConstr(original[n]==gp.quicksum(vectors[j][t]*ll[j] for j in range(len(joint))))
                m.optimize();after=m.ObjVal if m.Status==gp.GRB.OPTIMAL else None;m.write(str(d/'B_joint.lp'))
                after_receipt=objective_receipt(m,objective_terms,objective_constant)
                write(d/'original_objective_joint.json',after_receipt)
                exact_matrix(m,d/'B_joint_exact_matrix.json')
                if m.Status==gp.GRB.INFEASIBLE:
                    write(d/'joint_infeasibility_contradiction.json',dict(known_empty_fleet=True))
                    raise RuntimeError('Full joint model excludes its known feasible empty fleet')
                if before is not None and after is not None and after<before-1e-7:
                    write(d/'objective_contradiction.json',dict(reference=before,joint=after,signed_increment=after-before,
                        priority='investigate domain/model/numeric issue; never a negative-strength conclusion'))
                    raise RuntimeError('Adding a joint hull apparently reduced the optimum outside numerical policy')
                if best_numeric:write(d/'best_separation.json',dict(best_numeric=best_numeric,best_strict=best_strict))
                write(d/'support_queries.json',dict(records=records,controls=controls))
                summaries.append(dict(id=case['id'],single_plans=list(map(len,cars)),joint_pairs=len(joint),theta=True,threshold_ranks=len(ranks),IR_rows=ir,
                    queried_directions=len(records),positive_numeric_gaps=sum(q.get('gap',0)>1e-7 for q in records),
                    best_numeric=best_numeric,best_strict=best_strict,event_controls=controls,budget_exit=budget_exit,
                    canonical_scope=canonical_scope,
                    canonical_SHA=sha(d/'canonical/original.lp'),reference_exact_matrix_SHA=sha(d/'B_ref_exact_matrix.json'),
                    joint_exact_matrix_SHA=sha(d/'B_joint_exact_matrix.json'),
                    original_objective_receipt_SHAs={n:sha(d/n) for n in ['original_objective_reference.json','original_objective_joint.json']},
                    full_current_micro_objective_reference=before,full_current_micro_objective_joint=after,
                    current_objective_increment=None if before is None or after is None else after-before))
                write(d/'case_result.json',summaries[-1])
    write(OUT/'joint_results.json',dict(execution='PARTIAL_BUDGET' if budget_exit else 'COMPLETE_BOUNDED_TINY_STEP',cases=summaries,runtime=runtime,
        plan_SHA=sha(OUT/'E_experiment_plan.json'),runner_SHA=sha(__file__),
        seconds=time.perf_counter()-start,full_real_role_steps='NOT_ADMITTED: tiny exact joint maxima cannot omit outside supply/receiver stations; no complete full-universe support upper bound is supplied',
        no_large_separator_or_production_change=True,limited_directions_do_not_prove_full_hull_equality=True))
    print('E_REQUIRED_COMPLETE_TINY_COMPARISON_FINISHED',flush=True)
if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()
