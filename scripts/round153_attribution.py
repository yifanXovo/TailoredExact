"""Current-Q projection witnesses and useful-price rows in a free complete LP."""
from fractions import Fraction as F
from round152_projection import project
from round153_lp import add_rows,dual_certificate,finite_bounds,primal_record,optimize,semantics
from round153_common import *

def projection(role):
    from round150_lp import affinity
    configure();affinity();ref=OUT/'reference'/role
    scope=read(ref/'domain.json')['scope'];point=load_gz(ref/'direct/solution.json.gz')
    target=OUT/'projection'/role;r=project(scope,point,target)
    ref_result=read(ref/'direct/result.json')
    r.update(current_Q_SHA=ref_result['model_SHA'],current_Q_L=ref_result['L'],current_Q_U=ref_result['U'],
             current_Q_point_SHA=sha(ref/'direct/solution.json.gz'),
             projection_value_interval=[ref_result['L'],ref_result['U']] if r['full_oracle_projection_feasible'] else None,
             expected_G_is_witness_not_minimum=True,compatible_distribution_not_completion_feasibility=True)
    write(target/'result.json',r)
    print(json.dumps({k:r[k] for k in ['current_Q_L','current_Q_U','full_oracle_projection_feasible','projection_value_interval']}),flush=True)

def supports(role,coupled,label):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_coupled import support_row
    from round153_pricing import unkeyed
    configure();affinity();assert binding()['sha256']==DLL_SHA
    ref=OUT/'reference'/role;scope=read(ref/'domain.json')['scope'];data=read(Path(coupled)/'result.json')
    assert data['scope']==scope and data['Q_SHA']==sha(ref/'direct/model.mps')
    target=OUT/'support_LP'/f'{role}_{label}';target.mkdir(parents=True,exist_ok=False)
    rows=[];prows=[]
    for index,rec in enumerate(data['supports']):
        price=read(ROOT/rec['price_path']);assert price['scope']==scope and price['complete_domain']
        costs={tuple(map(int,k.split(':'))):F(v) for k,v in price['d_exact'].items()} if 'd_exact' in price else unkeyed(price['d'])
        pi={k:-v for k,v in costs.items()};row,transport=support_row(scope,price['beta'],pi,price['lower'],index)
        assert row==rec['row'] and transport==rec['transport_exact']
        rows.append(row)
        if not row['terms'].get('G',0.):prows.append(row)
    point=load_gz(ref/'direct/solution.json.gz');dual=load_gz(ref/'direct/dual.json.gz')['Pi'];reference=read(ref/'direct/result.json');records=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with gp.read(str(ref/'direct/model.mps'),env=env) as m:
            bounds,_=finite_bounds(m);before=semantics(m);names={v.VarName for v in m.getVars()};oldrows={c.ConstrName for c in m.getConstrs()}
            for stage,new in [('projection',prows),('all_supports',[r for r in rows if r not in prows])]:
                folder=target/stage;folder.mkdir();add_rows(m,new,gp)
                assert semantics(m,names,oldrows)==before
                primal=primal_record(m,point);dc=dual_certificate(m,dual,bounds)
                if primal['qualified'] and dc['qualified'] and primal['objective']-dc['lower']<=1e-6:
                    rr=dict(Status=2,objective=primal['objective'],primal=primal,Optimize_new=0)
                    m.write(str(folder/'model.mps'));save_gz(folder/'solution.json.gz',point);save_gz(folder/'dual.json.gz',dict(Pi=dual))
                else:
                    rr=optimize(m,folder);assert rr['Status']==2 and rr['primal']['qualified'];rr['Optimize_new']=1
                    point={v.VarName:v.X for v in m.getVars()};dual={c.ConstrName:c.Pi for c in m.getConstrs()};dc=dual_certificate(m,dual,bounds)
                assert dc['qualified'];save_gz(folder/'dual_certificate.json.gz',dc)
                rr.update(role=role,stage=stage,added_rows=len(new),L=dc['lower'],U=rr['objective'],reference_L=reference['L'],
                          all_original_variables_free=True,original_Q_SHA=data['Q_SHA'],coupled_source=str(coupled),
                          discovery_and_pricing_cost_not_free=True)
                write(folder/'rows.json',new);write(folder/'result.json',rr);records.append(rr)
                print(json.dumps({k:rr[k] for k in ['role','stage','L','U','Optimize_new','added_rows']}),flush=True)
    write(target/'result.json',dict(role=role,records=records,rows=len(rows),projection_rows=len(prows),
          Q_SHA=data['Q_SHA'],coupled_source=str(coupled),coupled_lower=data['lower'],coupled_upper=data['upper']))

def floor_close(role,coupled,floor,label):
    from round153_coupled import support_row
    data=read(Path(coupled)/'result.json');price_path=Path(floor)/'pricing/result.json';price=read(price_path)
    assert data['scope']==price['scope'] and price['beta']==1. and price['complete_domain']
    costs={tuple(map(int,k.split(':'))):F(v) for k,v in price['d_exact'].items()}
    row,transport=support_row(data['scope'],1.,{k:-v for k,v in costs.items()},price['lower'],len(data['supports']))
    data['supports']=data['supports']+[dict(row=row,transport_exact=transport,price_path=str(price_path.relative_to(ROOT)),beta=1.)]
    temp=OUT/'coupled'/f'{role}_{label}';temp.mkdir(parents=True,exist_ok=False)
    data.update(prior_results=data['prior_results']+[str(Path(coupled)/'result.json')],label=label,
                decision='FLOOR_TRANSFER_PENDING_FREE_Q_CHECK',new_RMP_solve=False,
                upper_witness_source=str(Path(coupled)/'best_primal.json.gz'))
    write(temp/'result.json',data)
    supports(role,str(temp),label)
    lp=read(OUT/'support_LP'/f'{role}_{label}'/'all_supports/result.json')
    data.update(lower=max(data['lower'],lp['L']),decision='VALUE_BOUNDED_BY_QUALIFIED_FLOOR_AND_COMPLETE_PRIMAL',
                free_Q_support_result=str(OUT/'support_LP'/f'{role}_{label}'/'result.json'))
    data['gap']=data['upper']-data['lower'];write(temp/'result.json',data)
    print(json.dumps(dict(role=role,lower=data['lower'],upper=data['upper'],gap=data['gap'])),flush=True)

def support_close(role,coupled,label):
    supports(role,coupled,label)
    source=Path(coupled)/'result.json';data=read(source)
    proof=OUT/'support_LP'/f'{role}_{label}'/'result.json';value=read(proof)['records'][-1]['L']
    target=OUT/'coupled'/f'{role}_{label}';target.mkdir(parents=True,exist_ok=False)
    data.update(label=label,lower=max(data['lower'],value),records=[],prior_results=[str(source)],
        decision='FREE_Q_SUPPORT_BOUND_TRANSFER',new_RMP_solve=False,free_Q_support_result=str(proof),
        primal_discovery_only=False,no_new_lower_claim=False,primal_sweeps=[],
        ancestor_primal_evidence_retained_via_prior_results=True)
    data['gap']=data['upper']-data['lower'];write(target/'result.json',data)
    print(json.dumps(dict(role=role,lower=data['lower'],upper=data['upper'],gap=data['gap'])),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
