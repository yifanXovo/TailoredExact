"""Consume paid directions/columns in the complete free Q, preserving history."""
from fractions import Fraction as F
from round143_math import outward
from round153_coupled import Master,support_row
from round153_pricing import stock_value
from round153_lp import optimize,add_rows,finite_bounds,dual_certificate,primal_record
from round154_common import *

def inherited(role):
    row=next(r for r in read(OLD153/'reports/scientific_table.json')['rows'] if r['role']==role)
    return ROOT/row['coupled_result']

def ingest(role,label,previous='inherited',*price_folders):
    tick=time.perf_counter();source=inherited(role) if previous=='inherited' else Path(previous)
    prior=read(source);scope=prior['scope'];qp=OLD153/'reference'/role/'direct/model.mps'
    assert prior['role']==role and prior['Q_SHA']==sha(qp)
    folder=OUT/'coupled'/f'{role}_{label}';folder.mkdir(parents=True,exist_ok=False)
    pool={tuple(Y) for Y in prior['columns']};initial=len(pool);supports=list(prior['supports']);lower=F(prior['lower']);groups={};facts=[]
    for price_folder in price_folders:
        pf=Path(price_folder).resolve();r=read(pf/'result.json');h=read(pf/'hull_result.json')
        assert r['complete_domain'] and r['scope']==scope
        direction=next(p for p in (OUT/'directions').glob('*/direction.json') if sha(p)==h['direction_SHA'])
        d=read(direction);assert d['scope']==scope and d['Q_SHA']==prior['Q_SHA']
        assert r['beta']==d['beta'] and r['d_exact']==d['d_exact']
        costs={tuple(map(int,k.split(':'))):F(v) for k,v in r['d_exact'].items()}
        added=0
        for stock in r['stocks']:
            v=stock_value(scope,stock['Y'],r['beta'],costs)
            assert v['feasible'] and v['price']==F(stock['price_exact']) and v['f']==F(stock['f_exact'])
            Y=tuple(stock['Y']);added+=Y not in pool;pool.add(Y)
        facts.append(dict(path=str(pf/'result.json'),SHA256=sha(pf/'result.json'),added_columns=added,direction=str(direction)))
        groups.setdefault(str(direction),[]).append((pf,r))
    for direction,prices in groups.items():
        d=read(direction);cert=load_gz(Path(direction).parent/'certificate.json.gz');assert cert['qualified']
        best=max(prices,key=lambda p:p[1]['lower']);new_lower=max(F(d['inherited_price_lower']),F(best[1]['lower']))
        cq,aK=F(d['C_Q_exact']),F(d['a_K_exact']);lower=max(lower,cq+min(aK,new_lower))
        if new_lower>F(d['inherited_price_lower']):
            costs={tuple(map(int,k.split(':'))):F(v) for k,v in d['d_exact'].items()}
            row,correction=support_row(scope,d['beta'],{k:-v for k,v in costs.items()},outward(new_lower,False),len(supports))
            row['name']=f'r154_coupled_support_{len(supports):05}'
            supports.append(dict(row=row,transport_exact=correction,price_path=str((best[0]/'result.json').relative_to(ROOT)),beta=d['beta'],
                                 direction_SHA=sha(direction),source_prices=[str(p/'result.json') for p,r in prices]))
    result=dict(prior,label=label,lower=outward(lower,False),upper=prior['upper'],gap=prior['upper']-outward(lower,False),
                columns=[list(Y) for Y in sorted(pool)],supports=supports,records=facts,prior_results=[str(source)],
                columns_before=initial,new_columns=len(pool)-initial,refresh_required=bool(prior.get('refresh_required',False)) or len(pool)>initial,
                original_variables_free=True,upper_is_not_physical=True,new_RMP_solve=False,
                no_RMP_or_full_hull_upper_from_price=True,decision='PAID_PRICE_BOUND_AND_TRUE_COLUMN_INGEST',seconds=time.perf_counter()-tick)
    write(folder/'plan.json',dict(role=role,UTC=utc(),prior_SHA=sha(source),Q_SHA=sha(qp),price_inputs=facts,
          complete_supports_preserved=True,full_original_Q=True))
    write(folder/'result.json',result)
    print(json.dumps(dict(role=role,new_columns=result['new_columns'],columns=len(pool),supports=len(supports),lower=result['lower'],upper=result['upper'])),flush=True)

def replay(role,label,previous):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_exact_worker import enable
    configure();affinity();enable();assert binding()['sha256']==DLL_SHA
    tick=time.perf_counter();source=Path(previous);prior=read(source);scope=prior['scope']
    qp=OLD153/'reference'/role/'direct/model.mps';assert prior['Q_SHA']==sha(qp)
    folder=OUT/'support_LP'/f'{role}_{label}';folder.mkdir(parents=True,exist_ok=False)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.read(str(qp),env=env) as m:
            bounds,derivations=finite_bounds(m);add_rows(m,[s['row'] for s in prior['supports']],gp)
            solved=optimize(m,folder/'solve',cap=180.)
            assert solved['Status']==2 and solved['primal']['qualified']
            cert=dual_certificate(m,bounds=bounds);assert cert['qualified']
            save_gz(folder/'certificate.json.gz',cert);save_gz(folder/'Q_bounds.json.gz',dict(bounds=bounds,derivations=derivations))
            lower=max(prior['lower'],cert['lower']);upper=solved['objective']
    result=dict(prior,lower=lower,gap=prior['upper']-lower,prior_results=[str(source)],
        support_replay=dict(L=cert['lower'],U=upper,supports=len(prior['supports']),projection_rows=0,
                            finite_support_upper_is_not_full_hull_upper=True,all_original_variables_free=True,
                            original_Q_SHA=sha(qp),primal=solved['primal']),seconds=time.perf_counter()-tick,
        decision='COMPLETE_FREE_Q_ALL_SUPPORTS_REPLAY')
    write(folder/'result.json',result);print(json.dumps(result['support_replay']),flush=True)

def refresh(role,label,previous):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_exact_worker import enable
    configure();affinity();enable();assert binding()['sha256']==DLL_SHA
    tick=time.perf_counter();source=Path(previous);prior=read(source);scope=prior['scope']
    qp=OLD153/'reference'/role/'direct/model.mps';assert prior['Q_SHA']==sha(qp)
    folder=OUT/'coupled'/f'{role}_{label}';folder.mkdir(parents=True,exist_ok=False)
    upper=prior['upper'];primal=None;updated=False
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.read(str(qp),env=env) as m:
            master=Master(m,scope,gp,env)
            for Y in prior['columns']:master.add(Y)
            m.update();solved=optimize(m,folder/'solve',cap=180.)
            assert solved['Status']==2
            primal=master.primal()
            assert primal['qualified'],'unqualified refresh cannot discharge pending columns'
            if primal['qualified']:
                save_gz(folder/'primal.json.gz',dict(point={v.VarName:v.X for v in m.getVars()},check=primal,
                    stocks=[dict(Y=list(Y),weight=var.X,f_exact=str(master.values[Y]['f'])) for Y,var in master.columns.items() if abs(var.X)>1e-14]))
                if m.ObjVal<upper:upper=m.ObjVal;updated=True
    result=dict(prior,upper=upper,gap=upper-prior['lower'],prior_results=[str(source)],refresh_required=False,
        refresh=dict(Native_status=solved['Status'],RMP_objective=solved['objective'],primal=primal,upper_updated=updated,
                     all_columns=len(prior['columns']),no_new_lower_claim=True),seconds=time.perf_counter()-tick,
        decision='FULL_Q_RMP_REFRESH_ALL_CURRENT_COLUMNS')
    write(folder/'result.json',result);print(json.dumps(dict(role=role,lower=prior['lower'],upper=upper,columns=len(prior['columns']),primal_qualified=primal['qualified'])),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
