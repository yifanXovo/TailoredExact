"""Reuse saved LP vectors for extra resource diagnostics; zero new Optimize."""
from round138_common import *
from fractions import Fraction as F
import gzip,re,collections
import round108_reader as core

def vector(folder,variant):
    return json.loads(gzip.decompress((folder/variant/'solution.json.gz').read_bytes()))

def main():
    tick=time.perf_counter();handling=[];GS=[]
    for role in ['K-35-U','R-X20-S-T1','R-X35-S-T2','K-20-S']:
        folder=OUT/'roots'/role;scope=read(folder/'scope.json');p=scope['panel']
        a=core.evidence.instance(ROOT,p);x=vector(folder,'stock');h=F(p['pickup_seconds'])+F(p['drop_seconds'])
        C=F(0);Cq=F(0);supports=collections.defaultdict(list)
        for name,value in x.items():
            m=re.fullmatch(r'state_(\d+)_(\d+)',name)
            if not m:continue
            i,y=map(int,m.groups());supports[i].append(y);cost=max(a['b'][i]-y,0)
            C+=cost*F(value);Cq+=cost*F(x[f'state_g_{i}_{y}'])
        assert h>0
        cap=F(p['M'])*F(p['T_seconds'])/h;alpha=F(scope['alpha']);beta=F(scope['beta']);g=F(x['G'])
        upper_slack=alpha*C+cap*(g-alpha)-Cq
        lower_slack=Cq-beta*C-cap*(g-beta)
        handling.append(dict(role=role,cap=str(cap),B=scope['B'],C=float(C),Cq=float(Cq),
            linear_budget_slack=float(cap-C),upper_product_slack=float(upper_slack),lower_product_slack=float(lower_slack),
            max_product_violation=float(max(F(0),-upper_slack,-lower_slack)),
            local_VDP_already_implies_handling_products_when_cap_at_least_B=cap>=scope['B'],
            integer_basis='C(s)=sum pickups by shared one-way states; total handling h*C <= M*T includes return unloading',
            stock_solution_SHA=sha(folder/'stock/solution.json.gz')))
        if role not in ['K-35-U','R-X20-S-T1']:continue
        add=read(folder/'additions.json');ratio={int(i):F(v) for i,v in add['ratio_coefficients'].items()}
        minima={i:min(v) for i,v in supports.items()};remaining=max(0,scope['Bminus']-sum(minima.values()))
        lower=sum(ratio[i]*y for i,y in minima.items())
        for i in sorted(ratio,key=lambda i:ratio[i]):
            amount=min(remaining,max(supports[i])-minima[i]);lower+=amount*ratio[i];remaining-=amount
        assert remaining==0
        Sl=float(lower)
        if F(Sl)>lower:Sl=math.nextafter(Sl,-math.inf)
        assert F(Sl)<=lower
        for variant in ['gs_independent','gs_shared']:
            v=vector(folder,variant);S=sum(F(v[f'r_{i}']) for i in ratio);g=F(v['G'])
            W=F(v['r138_control_W_GS']) if variant=='gs_independent' else sum(c*F(v[f'zprod_{i}']) for i,c in ratio.items())
            assert alpha==0
            slacks=[W-F(Sl)*g,beta*S+F(Sl)*g-beta*F(Sl)-W]
            GS.append(dict(role=role,variant=variant,tighter_S_lower_exact=str(lower),safe_loaded_S_lower=Sl,
                new_lower_MC_slack=float(slacks[0]),new_upper_MC_slack=float(slacks[1]),
                saved_optimum_satisfies_tighter_lower_domain_products=min(slacks)>=0,
                stored_binary64_point_new_row_residuals_exactly_recomputed=True,
                full_vector_not_claimed_rational_LP_certificate=True,solution_SHA=sha(folder/variant/'solution.json.gz')))
    assert 'gurobipy' not in sys.modules
    write(OUT/'reports/offline_products.json',dict(UTC=utc(),handling=handling,GS_lower_bound_controls=GS,
        Optimize=0,solver_imports=0,seconds=time.perf_counter()-tick,
        source='Previously saved Round138 Seed0 LP vectors; no new solve and no invented new Seed',
        scope='Point diagnostics and new-row arithmetic, not new LP optimum or complete-method results'))
    print(json.dumps(dict(handling_violations={r['role']:r['max_product_violation'] for r in handling},
                         tighter_GS_lower_witnesses=[(r['role'],r['variant'],r['saved_optimum_satisfies_tighter_lower_domain_products']) for r in GS])))

if __name__=='__main__':main()
