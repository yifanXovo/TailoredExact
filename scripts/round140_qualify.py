"""Exact actual-writer/Native qualification. No Optimize in export/read actions."""
from round140_common import *
from round140_math import model_counts,serializable
from round138_repair import scaled_rows
import collections,csv
import round108_reader as core

def expected_counts(model,Bminus,B,counts):
    exact=model_counts(model,Bminus,B)
    if exact['inventory_domain_infeasible']:
        return [(((('G',0.),)),'<=',-1.)]
    a=serializable(exact);result=[]
    for name,constant in [('TC',0),('TC2',a['constant'])][:1 if counts=='tc' else 2]:
        row={n:1. for n in model['order'] if n.startswith('h_')}
        row.update({n:-v for n,v in a[name].items()})
        scale=0;smallest=min([1.]+[abs(v) for v in row.values() if v])
        while math.ldexp(smallest,scale)<1e-12:scale+=1
        result.append((tuple(sorted((n,math.ldexp(v,scale)) for n,v in row.items())), '>=',math.ldexp(constant,scale)))
    return result

def exact_matrix(path,p,counts='tc2',stock=True,native=False):
    path=Path(path);m=core.lp_model(path);data=core.evidence.instance(ROOT,p)
    B=sum(data['b'][1:]);Bm=max(0,B-sum(p['Q_vector']));alpha,beta=m['bounds']['G']
    rows=expected_counts(m,Bm,B,counts) if counts!='off' else []
    stock_rows=scaled_rows(p['V'],alpha,beta,Bm,B)
    counter=collections.Counter(m['rows']);wanted=collections.Counter(rows)
    assert not wanted-counter,('missing/wrong TC/TC2 rows',path)
    assert all(counter[r]==q for r,q in wanted.items()),('wrong row multiplicity',path)
    if stock:assert not collections.Counter(stock_rows)-counter,('stock rows missing',path)
    fact=dict(path=path.relative_to(ROOT).as_posix(),SHA=sha(path),counts=counts,stock=stock,
        new_rows=len(rows),new_columns=0,B=B,Bminus=Bm,alpha=alpha,beta=beta,exact_count_row_multiplicity=True)
    if native:
        from round100_gurobi_runtime import gp,binding
        assert binding()['sha256']==DLL_SHA
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
            with gp.read(str(path),env=env) as model:
                assert model.NumVars==len(m['order']) and model.NumConstrs==len(m['rows'])
                assert {v.VarName:v.VType for v in model.getVars()}==m['types']
                for j,r in enumerate(m['rows']):
                    if r not in wanted:continue
                    terms,sense,rhs=r;constraint=model.getConstrs()[j];row=model.getRow(constraint)
                    assert {row.getVar(k).VarName:row.getCoeff(k) for k in range(row.size())}==dict(terms),(path,j)
                    assert constraint.RHS==rhs and constraint.Sense=='>'
        fact.update(native_exact_coefficients_RHS_types=True,Optimize=0,Seed=0,Threads=1)
    return fact,m

def exports():
    scope=read(OUT/'roots/K-20-S/scope.json');p=scope['panel'];beta=scope['beta']
    cases=[dict(name='root',alpha=scope['alpha'],beta=beta,cutoff=beta),
           dict(name='child',alpha=beta/4,beta=beta/2,cutoff=beta),
           dict(name='cutoff_refresh',alpha=0,beta=beta-1e-4,cutoff=beta-1e-4)]
    plan=dict(cases=cases,panel=p,variants=['off','stock','tc_stock','tc2_stock'],Seed=0,Threads=1,Optimize=0)
    write(OUT/'qualification/export_plan.json',plan)
    for c in cases:
        for v in plan['variants']:
            d=OUT/'qualification/exports'/c['name']/v
            cmd=[BUILD/'Round140Export.exe',ROOT/p['input_path'],p['T_seconds'],c['alpha'],c['beta'],c['cutoff'],'ms2',d,p['lambda'],v]
            assert metered('export_'+c['name']+'_'+v,'diagnostic',cmd,timeout=60)==0

def check():
    plan=read(OUT/'qualification/export_plan.json');facts=[];comparisons=[]
    for c in plan['cases']:
        models={}
        for v in plan['variants']:
            counts='tc2' if v=='tc2_stock' else 'tc' if v=='tc_stock' else 'off'
            fact,m=exact_matrix(OUT/'qualification/exports'/c['name']/v/'original.lp',plan['panel'],counts,v!='off',True)
            models[v]=m;facts.append(dict(case=c['name'],variant=v,**fact))
        old=models['stock']
        for v,amount in [('tc_stock',1),('tc2_stock',2)]:
            new=models[v]
            assert all(old[k]==new[k] for k in ['order','bounds','types','objective'])
            assert not collections.Counter(old['rows'])-collections.Counter(new['rows'])
            assert sum((collections.Counter(new['rows'])-collections.Counter(old['rows'])).values())==amount
        comparisons.append(dict(case=c['name'],same_columns_types_objective_bounds=True,only_TC_rows_added=True))
    # The off writer is unchanged relative to the actual inherited K20 root.
    inherited=core.lp_model(Path(read(OUT/'roots/K-20-S/scope.json')['base_model']))
    root=core.lp_model(OUT/'qualification/exports/root/off/original.lp')
    assert inherited==root,'off behavior changed'
    write(OUT/'qualification/matrix_checks.json',dict(PASS=True,Optimize=0,cases=facts,comparisons=comparisons,
        exact_historical_off_equal=True,old_TC_retained=True,negative_coefficients_and_nonzero_constants_checked=True))
    print('12 real root/child/cutoff exports match the exact Fraction oracle and Native readback')

if __name__=='__main__':globals()[sys.argv[1]]()
