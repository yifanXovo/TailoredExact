"""Matched fixed-objective calls with explicit paid reconstruction."""
from fractions import Fraction as F
from round152_math import h_exact
from round153_pricing import stock_value
from round143_math import outward
from round156_common import *

def rn(role,label,nodes,cap):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round156_rn import ObservedRN,GENERATED_SOURCE,GENERATED_SHA
    tick=time.perf_counter();affinity();assert binding()['sha256']==DLL_SHA
    prior=read(OUT/'starting_inventory.json')[role];scope=prior['scope']
    costs={(s['i'],y):h_exact(s,y) for s in scope['stations'] for y in s['support']}
    target=OUT/'oracle'/role/label;target.mkdir(parents=True,exist_ok=False)
    write(target/'plan.json',dict(UTC=utc(),method='RN',role=role,node_limit=int(nodes),
        offline_safety_cap=float(cap),initial_lower=prior['lower'],initial_upper=prior['upper'],
        initial_warm=prior['warm'],starting_inventory_SHA=sha(OUT/'starting_inventory.json'),
        new_tree=True,saved_BB_tree_inherited=False,same_fixed_objective_beta1_dh=True,
        absolute_price_gap=1e-4,Seed=0,Threads=1,generated_SHA=GENERATED_SHA))
    (target/'generated_price.py.txt').write_text(GENERATED_SOURCE,encoding='utf-8',newline='\n')
    with (target/'events.jsonl').open('w',encoding='utf-8') as events:
        def record(row):
            row.update(elapsed=time.perf_counter()-tick)
            events.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n');events.flush()
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
            built=time.perf_counter();oracle=ObservedRN(scope,env,old_joint=True)
            construct=time.perf_counter()-built;oracle.record_event=record
            try:
                r=oracle.price(1.,costs,target/'pricing',warm=prior['warm'],node_limit=int(nodes),
                    absolute_gap=1e-4,global_deadline=tick+float(cap))
            finally:oracle.close()
    r.update(lower=max(prior['lower'],r['lower']),upper=min(prior['upper'],r['upper']),
        arm_seconds=time.perf_counter()-tick,oracle_construct_seconds=construct,
        initial_lower=prior['lower'],initial_upper=prior['upper'],role=role,method='RN',label=label)
    assert r['lower']<=r['upper']
    r['qualified_gap']=r['upper']-r['lower']
    r['resolved']=r['qualified_gap']<=1e-4
    write(target/'result.json',r)
    print(json.dumps({k:r[k] for k in ('lower','upper','qualified_gap','resolved','arm_seconds','calls')}),flush=True)

def residual(role,label,nodes,cap,condition,max_targets='16'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round156_residual import InventoryResidual
    tick=time.perf_counter();affinity();assert binding()['sha256']==DLL_SHA
    prior=read(OUT/'starting_inventory.json')[role];scope=prior['scope']
    target=OUT/'oracle'/role/label;target.mkdir(parents=True,exist_ok=False)
    node_budget=int(nodes);deadline=tick+float(cap);condition=bool(int(condition))
    lower,upper=map(F,(prior['lower'],prior['upper']));warm=list(prior['warm'])
    write(target/'plan.json',dict(UTC=utc(),method='residual_U' if condition else 'residual',
        role=role,total_node_capacity=node_budget,max_targets=int(max_targets),
        offline_safety_cap=float(cap),initial_lower=float(lower),initial_upper=float(upper),
        initial_warm=warm,starting_inventory_SHA=sha(OUT/'starting_inventory.json'),
        same_fixed_objective_beta1_dh=True,absolute_price_gap=1e-4,Seed=0,Threads=1,
        target_rule='midpoint of current qualified own interval; stop on undecided target',
        node_budget_rule='sum(max(1,ceil(nodes))) across calls',condition_upper=condition))
    records=[];total_nodes=0;stop='target_capacity';outer_construct=None
    with (target/'events.jsonl').open('w',encoding='utf-8') as events:
        current=[0]
        def record(row):
            row.update(elapsed=time.perf_counter()-tick,call=current[0])
            events.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n');events.flush()
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
            built=time.perf_counter();oracle=InventoryResidual(scope,env,target/'evidence',condition)
            outer_construct=time.perf_counter()-built;oracle.record_event=record
            try:
                for j in range(int(max_targets)):
                    current[0]=j
                    if upper-lower<=F(1e-4):stop='original_price_precision';break
                    if total_nodes>=node_budget:stop='total_node_capacity';break
                    if time.perf_counter()>=deadline:stop='offline_safety_deadline';break
                    tau=(lower+upper)/2;before=[float(lower),float(upper)]
                    r=oracle.price(tau,upper,warm,target/f'price_{j:03}',node_budget-total_nodes,deadline,
                        absolute_gap=1e-4,lp_cap=30. if j==0 else 0.)
                    lower=max(lower,F(r['lower']));upper=min(upper,F(r['upper']))
                    assert lower<=upper
                    warm=[v['Y'] for v in sorted(r['stocks'],key=lambda v:F(v['price_exact']))[:20]]
                    total_nodes+=sum(max(1,math.ceil(c['nodes'])) for c in r['calls'])
                    records.append(dict(call=j,tau_exact=str(tau),before=before,lower=float(lower),upper=float(upper),
                        target_proved=r.get('target_proved',False),target_disproved=r.get('target_disproved',False),
                        cumulative_nodes=total_nodes,elapsed=time.perf_counter()-tick,result_SHA=sha(target/f'price_{j:03}/result.json')))
                    write(target/'progress.json',dict(records=records,lower=float(lower),upper=float(upper),elapsed=time.perf_counter()-tick))
                    if r.get('global_deadline_stop'):stop='offline_safety_deadline';break
                    if not (r.get('target_proved') or r.get('target_disproved')):stop='undecided_target';break
                if upper-lower<=F(1e-4):stop='original_price_precision'
            finally:oracle.close()
    result=dict(role=role,method='residual_U' if condition else 'residual',label=label,scope=scope,
        initial_lower=prior['lower'],initial_upper=prior['upper'],lower=outward(lower,False),upper=outward(upper,True),
        qualified_gap=float(upper-lower),resolved=upper-lower<=F(1e-4),stop=stop,
        total_nodes=total_nodes,records=records,oracle_construct_seconds=outer_construct,arm_seconds=time.perf_counter()-tick)
    write(target/'result.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
