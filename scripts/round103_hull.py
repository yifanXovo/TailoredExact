"""Certified numerical hull diagnostic using the production C++ support oracle.

The restricted master minimizes normalized infinity distance, hence provides
an UPPER bound on the full distance. Positive restricted distance is never an
outside certificate. Returned combinations are explicitly verified with exact
binary-rational arithmetic. Quantized supports are recomputed on the declared
C++ floating predicate domain; continuous pricing bounds enclose quantization.
This module is diagnostic orchestration, not a production root mechanism.
"""
from round103_common import *
from fractions import Fraction as F
import math
from itertools import permutations
def exact(x):return F.from_float(float(x))
def down(x):return math.nextafter(float(x),-math.inf)
def add_lower(a,b):return b if a==0 else a if b==0 else max(0.,down(a+b))
def mul_lower(a,b):return 0. if a==0 or b==0 else max(0.,down(a*b))
def anchor_travel(c,anchors):
    assert len(anchors)<=3 and len(set(anchors))==len(anchors)
    tau=[0.]*(1<<len(anchors))
    for mask in range(1,len(tau)):
        selected=[i for j,i in enumerate(anchors) if mask&(1<<j)];best=math.inf
        for order in permutations(selected):
            cost=0.;previous=0
            for i in order:cost=add_lower(cost,c['shortest_lower'][previous][i]);previous=i
            best=min(best,add_lower(cost,c['shortest_lower'][previous][0]))
        tau[mask]=best
    return tau
def validate(c,k,plan,anchors=()):
    assert len(plan)==len(c['initial']) and plan[0]==[0,0,0]
    P=D=0;travel=0.;Q=c['capacities'][k]
    for i,(p,d,z) in enumerate(plan[1:],1):
        assert all(type(v)==int for v in (p,d,z))
        assert 0<=p<=min(c['initial'][i],Q) and 0<=d<=min(c['station_capacity'][i]-c['initial'][i],Q)
        assert not(p and d) and z==int(p+d>0)
        P+=p;D+=d
        if z:travel=max(travel,add_lower(c['shortest_lower'][0][i],c['shortest_lower'][i][0]))
    if anchors:
        tau=anchor_travel(c,anchors);mask=sum((1<<j) for j,i in enumerate(anchors) if plan[i][2]);travel=max(travel,tau[mask])
    assert D<=P and add_lower(travel,mul_lower(c['handling_lower'],P))<=c['horizon_upper']
    return dict(P=P,D=D,travel_lower=travel)
class Oracle:
    def __init__(self,role,matrix,directory):
        self.directory=directory;self.calls=0;self.plan_bank={};self.anchors={}
        args=[BUILD/'Round103HullOracle.exe',ROOT/role['input_path'],str(role['T_seconds']),str(role['pickup_seconds']),str(role['drop_seconds']),matrix]
        self.err=(directory/'oracle.stderr.log').open('x')
        self.p=subprocess.Popen(list(map(str,args)),cwd=ROOT,env=env(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,text=True,bufsize=1)
        line=self.p.stdout.readline()
        if not line:raise RuntimeError('oracle contract failure')
        self.contract=json.loads(line);write(directory/'contract.json',self.contract)
        write(directory/'oracle_identity.json',dict(binary_sha256=sha(BUILD/'Round103HullOracle.exe'),matrix_sha256=sha(matrix),command=list(map(str,args))))
    def support(self,k,weights):
        self.calls+=1
        with (self.directory/'oracle_attempts.jsonl').open('a') as f:f.write(json.dumps(dict(event='begin',call=self.calls,vehicle=k,weights=weights))+'\n')
        anchors=self.anchors.get(k,[])
        prefix=('A '+str(k)+' '+str(len(anchors))+' '+' '.join(map(str,anchors))) if anchors else str(k)
        self.p.stdin.write(prefix+' '+' '.join(str(v) for row in weights[1:] for v in row)+'\n');self.p.stdin.flush()
        line=self.p.stdout.readline()
        if not line:raise RuntimeError('oracle support failure')
        record=json.loads(line);proof=record['proof'];assert proof['valid'] and proof['weights']==weights and proof['vehicle']==k
        assert proof.get('anchors',[])==anchors
        record['plan_validation']=validate(self.contract['resource'],k,proof['solution'],anchors)
        assert sum(a*v for w,r in zip(weights,proof['solution']) for a,v in zip(w,r))==proof['upper']
        key=tuple(v for row in proof['solution'] for v in row)
        self.plan_bank.setdefault(k,{})[key]=proof['solution']
        with (self.directory/'oracle_calls.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
        with (self.directory/'oracle_attempts.jsonl').open('a') as f:f.write(json.dumps(dict(event='return',call=self.calls,vehicle=k,seconds=record['seconds']))+'\n')
        return proof
    def close(self):
        if self.p.poll() is None:self.p.stdin.write('-1\n');self.p.stdin.flush()
        code=self.p.wait();self.err.close();assert code==0
def classify(oracle,k,point,engine,directory,deadline,tolerance=1e-8,max_columns=4096):
    from round100_gurobi_runtime import gp
    from gurobipy import GRB
    c=oracle.contract['resource'];n=len(c['initial'])-1;Q=c['capacities'][k];anchors=oracle.anchors.get(k,[])
    widths=[[0,0,0]]+[[min(c['initial'][i],Q),min(c['station_capacity'][i]-c['initial'][i],Q),int(min(c['initial'][i],Q)+min(c['station_capacity'][i]-c['initial'][i],Q)>0)] for i in range(1,n+1)]
    coordinates=[(i,t,widths[i][t]) for i in range(1,n+1) for t in range(3) if widths[i][t]>0]
    zero_residual=max([abs(point[i][t]) for i in range(1,n+1) for t in range(3) if widths[i][t]==0]+[0.])
    if zero_residual>tolerance:return dict(status='UNKNOWN',reason='zero_width_point_residual',zero_residual=zero_residual,Optimize_calls=0,DP_calls=0)
    start=time.perf_counter();calls=0;dp_start=oracle.calls;history=[];plans=[];seen=set();duplicates=0;last_combination=None;last_residual=None
    def finish(status,reason,**extra):
        if last_combination is not None:
            extra.setdefault('combination',[dict(lambda_rational=str(a),lambda_float=float(a),plan=p) for a,p in last_combination])
            extra.setdefault('verified_distance_upper',float(last_residual))
        result=dict(status=status,reason=reason,vehicle=k,seconds=time.perf_counter()-start,Optimize_calls=calls,DP_calls=oracle.calls-dp_start,
            columns=len(plans),duplicates=duplicates,tolerance=tolerance,zero_width_residual=zero_residual,history=history,**extra)
        write(directory/f'vehicle_{k}.json',result);return result
    if not coordinates:
        plan=[[0,0,0] for _ in range(n+1)]
        return finish('INSIDE','singleton_zero_domain',combination=[dict(lambda_rational='1',plan=plan)],normalized_residual=0.)
    with gp.Model('resource_hull_distance',env=engine) as master:
        master.Params.OutputFlag=0;master.Params.Threads=1;master.Params.Seed=0;master.Params.Presolve=-1
        # Diagnostic precision only. Full original MIP tolerances are unchanged.
        master.Params.FeasibilityTol=1e-9;master.Params.OptimalityTol=1e-9;master.Params.Method=1
        tvar=master.addVar(lb=0.,obj=1.,name='distance');master.update()
        lower=[master.addConstr(tvar>=point[i][t]/s,name=f'lower_{i}_{t}') for i,t,s in coordinates]
        upper=[master.addConstr(-tvar<=point[i][t]/s,name=f'upper_{i}_{t}') for i,t,s in coordinates]
        mass=master.addConstr(gp.LinExpr()==1.,name='mass');lambdas=[]
        def add(plan):
            nonlocal duplicates
            validate(c,k,plan,anchors);key=tuple(v for r in plan for v in r)
            if key in seen:duplicates+=1;return False
            seen.add(key);column=gp.Column([plan[i][t]/s for i,t,s in coordinates]*2+[1.],lower+upper+[mass])
            lambdas.append(master.addVar(lb=0.,obj=0.,column=column,name='lambda_'+str(len(plans))));plans.append(plan);return True
        add([[0,0,0] for _ in range(n+1)])
        for plan in oracle.plan_bank.get(k,{}).values():add(plan)
        while len(plans)<=max_columns:
            if time.perf_counter()>=deadline:return finish('UNKNOWN','diagnostic_deadline')
            master.Params.TimeLimit=max(.001,deadline-time.perf_counter());calls+=1
            with (directory/'master_calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='begin',vehicle=k,call=calls,columns=len(plans)))+'\n')
            master.optimize()
            with (directory/'master_calls.jsonl').open('a') as f:f.write(json.dumps(dict(vehicle=k,call=calls,status=master.Status,seconds=master.Runtime,columns=len(plans)))+'\n')
            if master.Status!=GRB.OPTIMAL:return finish('UNKNOWN','restricted_master_not_optimal',master_status=master.Status)
            restricted=master.ObjVal
            positive=[(exact(v.X),p) for v,p in zip(lambdas,plans) if v.X>0.]
            total=sum((a for a,p in positive),F(0));combination=[(a/total,p) for a,p in positive]
            residual=max(abs(exact(point[i][t])-sum((a*p[i][t] for a,p in combination),F(0)))/s for i,t,s in coordinates)
            last_combination=combination;last_residual=residual
            if residual<=exact(tolerance):
                for a,p in combination:assert a>=0;validate(c,k,p,anchors)
                assert sum((a for a,p in combination),F(0))==1
                return finish('INSIDE','explicit_exact_rational_combination_within_declared_tolerance',restricted_distance=restricted,normalized_residual=float(residual),
                    combination=[dict(lambda_rational=str(a),lambda_float=float(a),plan=p) for a,p in combination])
            w=[[0.,0.,0.] for _ in range(n+1)]
            for (i,t,s),lo,hi in zip(coordinates,lower,upper):w[i][t]=(lo.Pi+hi.Pi)/s
            norm=sum(abs(exact(w[i][t]))*s for i,t,s in coordinates)
            if norm==0:return finish('UNKNOWN','zero_dual_direction',restricted_distance=restricted)
            # An exact normalization enclosure; no claim based on solver duals alone.
            divisor=max(F(1),norm);wf=[[float(exact(a)/divisor) for a in row] for row in w]
            # Nearest dyadic rounding has error <=sum(widths)/(2*scale).
            # Choose precision so that this envelope is <=tolerance/8.
            # This is derived from physical widths, not fitted to any role.
            bits=max(30,math.ceil(math.log2(4*sum(s for i,t,s in coordinates)/tolerance)))
            if bits>48:return finish('UNKNOWN','requested_quantization_precision_exceeds_exact_profit_contract',restricted_distance=restricted)
            scale=1<<bits;weights=[[round(a*scale) for a in row] for row in wf]
            proof=oracle.support(k,weights);quantized=[[F(a,scale) for a in row] for row in weights]
            act=sum(exact(x)*a for r,wq in zip(point,quantized) for x,a in zip(r,wq));safe_rhs=F(proof['upper'],scale)
            qnorm=sum(abs(quantized[i][t])*s for i,t,s in coordinates)
            excess=act-safe_rhs
            error=sum(abs(exact(wf[i][t])-quantized[i][t])*s for i,t,s in coordinates)
            support_upper= safe_rhs+error
            continuous_act=sum(exact(x)*exact(a) for r,ww in zip(point,wf) for x,a in zip(r,ww))
            continuous_norm=sum(abs(exact(wf[i][t]))*s for i,t,s in coordinates)
            lower_bound=max(F(0),continuous_act-support_upper)/max(F(1),continuous_norm)
            item=dict(iteration=calls,restricted_distance=restricted,verified_combination_residual=float(residual),
                support_lower=float(sum(exact(a)*r for ww,pp in zip(wf,proof['solution']) for a,r in zip(ww,pp))),support_upper=float(support_upper),
                pricing_quantization_error=float(error),full_distance_lower=float(lower_bound),quantized_violation=float(excess),normalization=float(qnorm),plan=proof['solution'])
            history.append(item)
            # Positive violation is an exact binary-rational mathematical test.
            # Require the declared material diagnostic gap after normalization.
            if qnorm>0 and excess>exact(tolerance)*qnorm:
                return finish('OUTSIDE','complete_domain_dyadic_support_row',restricted_distance=restricted,
                    full_distance_lower=float(excess/qnorm),weights=weights,coefficient_scale=scale,safe_rhs_rational=str(safe_rhs),
                    exact_activity_rational=str(act),exact_excess_rational=str(excess),support=proof)
            if not add(proof['solution']):
                return finish('UNKNOWN','duplicate_column_without_membership_or_closed_pricing',restricted_distance=restricted,
                    full_distance_lower=float(lower_bound),continuous_pricing_upper=float(support_upper))
        return finish('UNKNOWN','structural_column_limit')
