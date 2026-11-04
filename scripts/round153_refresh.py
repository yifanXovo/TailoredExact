"""One complete-Q restricted-master primal refresh, without new pricing.

Use only if a preceding price supplied new stocks whose effect on the
retained numerical upper has not yet been checked. No lower is generated.
"""
from round153_common import *
from round153_coupled import Master
from round153_lp import optimize
from round153_exact_worker import enable


def run(role,label,resume,cap='180'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    text_qualification=OUT/'qualification/exact_text_v1/result.json'
    text_proof=read(text_qualification)
    assert text_proof['PASS'] and text_proof['source_SHA']==sha(ROOT/'scripts/round153_exact_worker.py')
    prior_limit=enable()
    master_qualification=OUT/'qualification/primal_pool_v1/result.json'
    master_proof=read(master_qualification)
    assert master_proof['PASS'] and master_proof['unchanged_master_qualification_reused']
    assert master_proof['core_SHA']==sha(ROOT/'scripts/round153_coupled.py')
    assert master_proof['stock_value_SHA']==sha(ROOT/'scripts/round153_pricing.py')
    tick=time.perf_counter();source=Path(resume)/'result.json';previous=read(source)
    qp=OUT/'reference'/role/'direct/model.mps';scope=read(OUT/'reference'/role/'domain.json')['scope']
    assert previous['role']==role and previous['scope']==scope and previous['Q_SHA']==sha(qp)
    columns=[tuple(Y) for Y in previous['columns']];assert len(columns)==len(set(columns))
    lower=previous['lower'];upper=previous['upper'];assert upper is not None
    target=OUT/'coupled'/f'{role}_{label}';target.mkdir(parents=True,exist_ok=False)
    write(target/'plan.json',dict(UTC=utc(),role=role,scope=scope,Q_SHA=sha(qp),
        prior_result=str(source),prior_result_SHA=sha(source),columns=len(columns),
        Native_LP_cap=float(cap),no_pricing=True,no_new_lower=True,all_original_Q_free=True,
        master_qualification_SHA=sha(master_qualification),text_qualification_SHA=sha(text_qualification),
        previous_process_digit_limit=prior_limit,active_process_digit_limit=0,process_local_only=True))
    primal=None;improved=False
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with gp.read(str(qp),env=env) as m:
            master=Master(m,scope,gp,env)
            for Y in columns:assert master.add(Y)
            m.update()
            save_gz(target/'Q_bounds.json.gz',dict(bounds=master.bounds,derivations=master.derivations))
            solved=optimize(m,target/'solve',cap=float(cap))
            assert solved['Status'] in (gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT)
            if m.SolCount:
                primal=master.primal()
                if primal['qualified'] and m.ObjVal<upper:
                    upper=m.ObjVal;improved=True
                    save_gz(target/'best_primal.json.gz',dict(point={v.VarName:v.X for v in m.getVars()},
                        stocks=[dict(Y=list(Y),weight=v.X,f_exact=str(master.values[Y]['f']))
                            for Y,v in master.columns.items() if abs(v.X)>1e-14],check=primal))
    result=dict(previous,label=label,lower=lower,upper=upper,gap=upper-lower,
        columns=[list(Y) for Y in columns],records=[],primal_sweeps=[],refinements=[],
        prior_results=[str(source)],new_RMP_solve=True,primal_refresh_only=True,
        primal_discovery_only=False,no_new_lower_claim=True,upper_is_not_physical=True,
        original_variables_free=True,no_new_pricing=True,
        refresh=dict(Native_status=solved['Status'],RMP_objective=solved.get('objective'),primal=primal,
            upper_witness_updated=improved,prior_upper=previous['upper']),
        decision='RMP_PRIMAL_REFRESH_QUALIFIED_UPPER_UPDATED' if improved else 'RMP_PRIMAL_REFRESH_PRIOR_UPPER_RETAINED',
        seconds=time.perf_counter()-tick)
    write(target/'result.json',result)
    print(json.dumps(dict(role=role,decision=result['decision'],lower=lower,upper=upper,
        gap=upper-lower,columns=len(columns),Native_status=solved['Status'],
        primal_qualified=bool(primal and primal['qualified']))),flush=True)


if __name__=='__main__':run(*sys.argv[1:])
