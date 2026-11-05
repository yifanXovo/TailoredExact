"""Qualify target stops only, reusing the already qualified original models."""
from fractions import Fraction as F
from itertools import product
from round152_qualify import scope
from round153_pricing import stock_value
from round152_math import unary_dp
from round154_goal_oracle import TargetRNOracle,TargetResidualOracle,RESIDUAL_SOURCE,RN_SOURCE
from round154_common import *

def run(label='goal_stop_v1'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    # Keep a real margin at G=3/10: binary64(.3) is slightly smaller.
    # This new-interface check must not reopen the inherited tiny-boundary policy.
    domain=scope([1.,.5],[[0,1,2,3,4]]*2,1,4,.05,.31)
    costs={(s['i'],y):F(-2)*y if s['i']==1 else F(.5)*y for s in domain['stations'] for y in s['support']}
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        for beta in [F(0),F(1.7)]:
            legal=[stock_value(domain,Y,beta,costs) for Y in product(*[s['support'] for s in domain['stations']])]
            legal=[v for v in legal if v['feasible']];true=min(v['price'] for v in legal)
            warm=[max(legal,key=lambda v:v['price'])['Y']]
            for kind in ['RN','residual']:
                fallback=beta*F(domain['gamma_L'])+F(unary_dp(domain,costs)['exact'])
                for decision,tau in [('prove',true-F(.25)),('reject',true+F(.25)),
                                     ('at_true',true),('early_reject',max(v['price'] for v in legal)+F(.25)),
                                     ('far_prove',fallback+F(.01))]:
                    folder=target/f'{kind}_beta{float(beta)}_{decision}'
                    if kind=='RN':
                        oracle=TargetRNOracle(domain,env,old_joint=True)
                        r=oracle.price(float(beta),costs,folder,cap=20.,warm=warm,tau=tau)
                    else:
                        oracle=TargetResidualOracle(domain,env)
                        r=oracle.price(beta,costs,tau,folder,cap=20.,warm=warm,lp_cap=10.)
                    oracle.close();assert r['calls'] and F(r['lower'])<=true<=F(r['upper'])
                    plan=read(folder/'target_stop_plan.json');assert plan['no_model_changes'] and plan['guard_already_paid']
                    assert plan['model_SHA']==sha(folder/'model.mps') and plan['generated_source_SHA']==sha(folder/'target_stop_source.txt')
                    if decision in ('prove','far_prove'):assert F(r['lower'])>=tau and not (folder/'counterexample_stop.json').exists()
                    elif decision=='at_true':
                        assert F(r['lower'])<tau and F(r['upper'])>=tau
                        assert not (folder/'counterexample_stop.json').exists()
                    else:
                        cex=read(folder/'counterexample_stop.json');value=stock_value(domain,cex['stock']['Y'],beta,costs)
                        assert value['feasible'] and value['price']<tau and value['price']==F(cex['original_price_exact'])
                        assert F(r['upper'])<tau
                    facts.append(dict(kind=kind,beta=float(beta),decision=decision,tau_exact=str(tau),true_price_exact=str(true),
                        lower=r['lower'],upper=r['upper'],status=r['calls'][0]['Status'],
                        exact_stock_counterexample=decision in ('reject','early_reject'),readback_source=True))
        # A positive-branch proof does not prove the full target when a legal
        # zero inventory has a lower original price.
        mixed=scope([.5,1.],[[0,1,3],[0,1,2]],0,3,.2,.5)
        dc={(s['i'],y):F(y) for s in mixed['stations'] for y in s['support']}
        for kind in ['RN','residual']:
            folder=target/(kind+'_mixed_zero');tau=F(.325)
            if kind=='RN':
                oracle=TargetRNOracle(mixed,env,old_joint=True);r=oracle.price(1.,dc,folder,cap=20.,tau=tau)
            else:
                oracle=TargetResidualOracle(mixed,env);r=oracle.price(1.,dc,tau,folder,cap=20.,lp_cap=10.)
            oracle.close();assert r['lower']==r['upper']==.2 and F(r['lower'])<tau
            facts.append(dict(kind=kind,mixed_zero=True,full_target_proved=False,lower=r['lower'],upper=r['upper'],
                              status=r['calls'][0]['Status'] if r['calls'] else None))
        # One unsupported normal return must retain only the original DP floor.
        oracle=TargetRNOracle(domain,env,old_joint=True);oracle.model.Params.SolutionLimit=1;oracle.model.Params.Presolve=0
        r=oracle.price(1.7,costs,target/'unsupported_stop',cap=20.,warm=warm,tau=true)
        oracle.close();assert r['calls'] and r['calls'][0]['Status']==gp.GRB.SOLUTION_LIMIT
        assert not r['calls'][0]['bound_status_qualified'] and r['lower']==r['fallback_lower']
        facts.append(dict(unsupported_status=r['calls'][0]['Status'],only_DP_retained=True))
    assert any(v.get('status')==gp.GRB.INTERRUPTED for v in facts)
    assert any(v.get('status')==gp.GRB.USER_OBJ_LIMIT for v in facts)
    write(target/'result.json',dict(PASS=True,facts=facts,new_interface_only=True,existing_full_model_qualification_reused=True,
          core_SHA=sha(ROOT/'scripts/round154_residual.py'),strong_SHA=sha(ROOT/'scripts/round154_strengthened.py'),
          RN_core_SHA=sha(ROOT/'scripts/round153_pricing.py'),goal_oracle_SHA=sha(ROOT/'scripts/round154_goal_oracle.py'),
          generated_residual_source=RESIDUAL_SOURCE,generated_RN_source=RN_SOURCE,
          unowned_interrupt_rejection_static=True,unsupported_native_return_tested=True,no_production_helper_change=True))
    print(json.dumps(dict(PASS=True,fixtures=len(facts))),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
