"""Exact count-product algebra and saved-point screening; no solver import."""
from round142_common import *
from fractions import Fraction as F
from round141_math import membership, child_rows
from round140_math import count_rows, serializable
import gzip, itertools, zipfile
configure()

OLD = ROOT/'results/unified_exact_round141'
ARCHIVE_SHA = '8552f9cbc2927e16b9f1e77f470a31651e4764c9034daa0e1fb0f04ee7a10d31'

def ranges(add, spec, mode):
    assert mode in ('selected','all')
    selected = F(spec['threshold'])
    found = []
    for r in add['thresholds']:
        t=F(r['t']); ell,u=r['ell'],r['u']
        if spec['side']=='low' and t>=selected: u=min(u,spec['pivot'])
        if spec['side']=='high' and t<=selected: ell=max(ell,spec['pivot']+1)
        assert ell<=u
        if mode=='all' or t==selected: found.append(dict(t=str(t),ell=ell,u=u))
    assert mode=='all' or len(found)==1
    return found

def row(name, terms, rhs, **metadata):
    """Normalize to >=, outward RHS and exact positive dyadic row scaling.

    Coefficients are already loaded binary64 endpoints, integers and +/-1.
    One outward ULP follows the R138 writer, even for an exact nonzero product.
    """
    terms={k:float(v) for k,v in terms.items() if v}
    rhs=F(rhs); actual=float(rhs)
    if rhs: actual=math.nextafter(actual,-math.inf)
    assert F(actual)<=rhs
    smallest=min([abs(v) for v in terms.values() if v] or [1.])
    exponent=0
    while math.ldexp(smallest,exponent)<1e-12: exponent+=1
    terms={k:math.ldexp(v,exponent) for k,v in terms.items()}
    actual=math.ldexp(actual,exponent)
    assert all(math.isfinite(v) for v in [*terms.values(),actual])
    return dict(name=name,terms=terms,sense='>',rhs=actual,
                exact_unscaled_rhs=str(rhs),scale_exponent=exponent,**metadata)

def product_rows(add, intervals, alpha, beta):
    a,z=F(alpha),F(beta); assert 0<=a<=z
    out=[]
    for i,r in enumerate(intervals):
        keys=membership(add,r['t']); l,u=r['ell'],r['u']
        for j,(slope,bound,sign) in enumerate([(a,l,1),(z,u,1),(z,l,-1),(a,u,-1)]):
            terms={k:-sign*slope for k in keys}
            terms.update({k.replace('state_','state_g_',1):F(sign) for k in keys})
            terms['G']=-sign*bound
            out.append(row(f'r142_cp_{i}_{j}',terms,-sign*slope*bound,
                           threshold=r['t'],ell=l,u=u,alpha=float(a),beta=float(z),facet=j))
    return out

def range_rows(add, intervals, spec):
    out=[]; selected=F(spec['threshold'])
    for i,r in enumerate(intervals):
        keys=membership(add,r['t'])
        for upper,bound in [(False,r['ell']),(True,r['u'])]:
            # This side row is already present in the immutable source.
            if F(r['t'])==selected and ((upper and spec['side']=='low') or
                                        (not upper and spec['side']=='high')): continue
            sign=-1 if upper else 1
            out.append(dict(name=f'r142_range_{i}_{int(upper)}',terms={k:float(sign) for k in keys},
                            sense='>',rhs=float(sign*bound),threshold=r['t'],ell=r['ell'],u=r['u']))
    return out

def residual(rows, point):
    # Exact arithmetic on the stored binary64 values, with normalized units.
    return max([float((F(r['rhs'])-sum((F(v)*F(point[k]) for k,v in r['terms'].items()),F(0))) /
                     F(2)**r.get('scale_exponent',0)) for r in rows] or [0.])

def count_diagnostic(add,interval,point,alpha,beta):
    keys=membership(add,interval['t'])
    K=sum((F(point[k]) for k in keys),F(0))
    W=sum((F(point[k.replace('state_','state_g_',1)]) for k in keys),F(0))
    g=F(point['G']);a,z=F(alpha),F(beta)
    mass_a=z*K-W;mass_z=W-a*K
    return dict(**interval,K=float(K),W=float(W),g=float(g),
        endpoint_alpha_count=float(mass_a/(z-g)) if z!=g else None,
        endpoint_beta_count=float(mass_z/(g-a)) if g!=a else None,
        endpoint_alpha_mass=float(mass_a),endpoint_beta_mass=float(mass_z),
        alpha_denominator=float(z-g),beta_denominator=float(g-a),
        max_CP_violation=max(0.,residual(product_rows(add,[interval],alpha,beta),point)))

def inverse_inventory(add,interval,lo,hi):
    forced=0; minimum=0; baseline=0;costs=[];gains=[];t=F(interval['t'])
    for i,ys in add['supports'].items():
        low=[y for y in ys if F(add['ratios'][i])*y<t]
        high=[y for y in ys if F(add['ratios'][i])*y>=t]
        minimum+=min(ys)
        if not low: forced+=1;baseline+=max(ys)
        elif not high: baseline+=max(ys)
        else:
            baseline+=max(low);costs.append(min(high)-min(ys));gains.append(max(ys)-max(low))
    minimum+=sum(sorted(costs)[:max(0,interval['ell']-forced)])
    maximum=baseline+sum(sorted(gains,reverse=True)[:max(0,interval['u']-forced)])
    return [max(lo,minimum),min(hi,maximum)]

def prepare():
    tick=time.perf_counter();archive=OLD/'artifacts/diagnostics_and_failures.zip'
    assert sha(archive)==ARCHIVE_SHA
    dependencies=[];positions=[];screens=[];reverse=[]
    records=read(OLD/'reports/LP_positions.json')['positions']
    chosen=[r for r in records if r['record'].get('pivot_kind')=='lp_floor' and r['record'].get('variant')=='conditional']
    assert len(chosen)==6
    with zipfile.ZipFile(archive) as z:
        def member(path):
            name=Path(path).relative_to(ROOT).as_posix();data=z.read(name)
            assert Path(path).read_bytes()==data,name
            dependencies.append(dict(path=name,SHA256=sha(path),bytes=len(data)))
        for saved in chosen:
            old=saved['record'];folder=ROOT/saved['result_path'];folder=folder.parent
            assert sha(folder/'result.json')==saved['result_SHA']
            for name in ['result.json','scope.json','model.mps','solution.json.gz','conditional_exact.json']:member(folder/name)
            assert sha(folder/'model.mps')==old['canonical_SHA'] and sha(folder/'solution.json.gz')==old['solution_SHA']
            role=old['role'];scope=read(OLD/'domains'/role/'scope.json');add=read(OLD/'domains'/role/'additions.json')
            for name in ['scope.json','additions.json']:member(OLD/'domains'/role/name)
            point=json.loads(gzip.decompress((folder/'solution.json.gz').read_bytes()))
            spec={k:old[k] for k in ['role','pivot','side','threshold','ell','u']}
            spec.update(label=f'{len(positions)+1:02}_{role}_{old["side"]}',old_label=old['label'],
                source_model=str(folder/'model.mps'),source_SHA=old['canonical_SHA'],
                old_solution=str(folder/'solution.json.gz'),old_solution_SHA=old['solution_SHA'],
                source_result=str(folder/'result.json'),source_result_SHA=saved['result_SHA'],cap_seconds=90,
                old_L=old['L'],old_beta=old['beta'],alpha=scope['alpha'],beta=scope['beta'],cutoff=scope['validated_U'])
            facts={}
            for mode in ['selected','all']:
                rs=ranges(add,spec,mode);linear=range_rows(add,rs,spec)
                products=product_rows(add,rs,spec['alpha'],spec['beta'])
                facts[mode]=dict(range_max_violation=max(0.,residual(linear,point)),
                    CP_max_violation=max(0.,residual(products,point)),range_rows=len(linear),CP_rows=len(products),
                    range_only_saved_optimum_feasible=residual(linear,point)<=1e-6,
                    diagnostic=count_diagnostic(add,ranges(add,spec,'selected')[0],point,spec['alpha'],spec['beta']))
            positions.append(spec);screens.append(dict(role=role,side=old['side'],old_L=old['L'],facts=facts))
        for saved in records:
            old=saved['record']
            if old.get('variant') not in ['conditional','plain']:continue
            add=read(OLD/'domains'/old['role']/'additions.json');scope=read(OLD/'domains'/old['role']/'scope.json')
            interval=ranges(add,old,'selected')[0]
            reverse.append(dict(role=old['role'],side=old['side'],variant=old['variant'],pivot=old['pivot'],
                original=[scope['Bminus'],scope['B']],inverse=inverse_inventory(add,interval,scope['Bminus'],scope['B'])))
    assert all(r['original']==r['inverse'] for r in reverse)
    write(OUT/'LP_plan.json',dict(positions=positions,Seed=0,Threads=1,affinity_mask=4,serial=True,
        selected_first=True,ALL_conditional=True,original_rows_objective_cutoff_support_g_retained=True))
    write(OUT/'inherited_dependencies.json',dict(science_commit=SCIENCE141,archive=str(archive),
        archive_SHA=ARCHIVE_SHA,members=dependencies,Optimize=0))
    write(OUT/'offline_screen.json',dict(roles=screens,inverse_inventory=reverse,Optimize=0,
        elapsed_seconds=time.perf_counter()-tick,source_saved_points_not_new_bounds=True))
    write(OUT/'start_receipt.json',dict(UTC=utc(),base=BASE,science141=SCIENCE141,
        branch=git('branch','--show-current').decode().strip(),actual_main=git('rev-parse','origin/main').decode().strip(),
        R141_in_main=False,PR_base='codex/round141-count-disjunction',goal_SHA=sha(OUT/'goal.md'),
        compute_cap_seconds=28800,protected_original='E:/codes/ExactEBRP',
        no_active_solver_at_start=True,stable_entry='scripts/paper_s2.py -> config/gi_tbc_round137.json',
        Gurobi_Seed=0,H_seed=20260626,new_assets_under_WORK=True,old_raw_not_deleted=True))
    print(json.dumps(screens,indent=2))

def tiny():
    tick=time.perf_counter();supports={str(i):[0,1,2] for i in range(1,5)}
    raw=count_rows({int(i):ys for i,ys in supports.items()}, {i:F(1) for i in range(1,5)},3,5)
    raw.update(supports={int(i):ys for i,ys in supports.items()},ratios={i:F(1) for i in range(1,5)})
    add=json.loads(json.dumps(serializable(raw)))
    add.update(supports=supports,ratios={i:1. for i in supports})
    x={'G':F(3,8)}
    for i in supports:
        x.update({f'state_{i}_{y}':s for y,s in enumerate([F(1,4),F(1,2),F(1,4)])})
        x.update({f'state_g_{i}_{y}':q for y,q in enumerate([F(3,20),F(3,40),F(3,20)])})
    a,z=F(0),F(3,4);g=x['G']
    for i in supports:
        assert sum(x[f'state_{i}_{y}'] for y in range(3))==1
        assert sum(x[f'state_g_{i}_{y}'] for y in range(3))==g
        assert all(a*x[f'state_{i}_{y}']<=x[f'state_g_{i}_{y}']<=z*x[f'state_{i}_{y}'] for y in range(3))
    tau=sum(y*x[f'state_{i}_{y}'] for i in supports for y in range(3))
    J=sum(y*x[f'state_g_{i}_{y}'] for i in supports for y in range(3))
    assert tau==4 and J==F(3,2)==g*tau
    H=F(5);K1=sum(x[k] for k in membership(add,'1'));K2=sum(x[k] for k in membership(add,'2'))
    W1=sum(x[k.replace('state_','state_g_',1)] for k in membership(add,'1'))
    W2=sum(x[k.replace('state_','state_g_',1)] for k in membership(add,'2'))
    parent_TC=sum(F(v)*x[k] for k,v in add['TC_exact'].items())
    parent_TC2=sum(F(r['delta'])*((4-r['ell']-r['u'])*sum(x[k] for k in membership(add,r['t']))+r['ell']*r['u']) for r in add['thresholds'])
    child=child_rows(add,'2',1,'low')
    child_TC2=F(child['constant_exact'])+sum(F(v)*x[k] for k,v in child['exact'].items())
    assert parent_TC==2 and parent_TC2==4 and child_TC2==5 and H<=4*J
    assert residual(product_rows(add,add['thresholds'],a,z),x)<=0
    assert W2-g==F(9,40)
    alpha_selector=[(z*x[f'state_1_{y}']-x[f'state_g_1_{y}'])/(z-g) for y in range(3)]
    beta_selector=[(x[f'state_g_1_{y}']-a*x[f'state_1_{y}'])/(g-a) for y in range(3)]
    assert alpha_selector==[F(1,10),F(4,5),F(1,10)] and beta_selector==[F(2,5),F(1,5),F(2,5)]
    # Positive lower endpoint, fixed g, signed constants and a tiny dyadic slope.
    fixtures=[];checked=0
    for a,z in [(F(1,8),F(3,4)),(F(1,8),F(1,8)),(F(1,2**50),F(1,2**48))]:
        intervals=[dict(t='1',ell=1,u=3),dict(t='2',ell=0,u=2)]
        rows=product_rows(add,intervals,a,z)
        for ys in itertools.product(range(3),repeat=4):
            counts=[sum(y>=int(F(r['t'])) for y in ys) for r in intervals]
            if not all(r['ell']<=K<=r['u'] for r,K in zip(intervals,counts)):continue
            for g in sorted(set([a,(a+z)/2,z])):
                p={'G':float(g)}
                for i,y0 in zip(supports,ys):
                    for y in range(3):p[f'state_{i}_{y}']=float(y==y0);p[f'state_g_{i}_{y}']=float(g*(y==y0))
                assert residual(rows,p)<=0;checked+=1
        fixtures.append(dict(alpha=float(a),beta=float(z),rows=rows))
    write(OUT/'math/tiny.json',dict(PASS=True,Optimize=0,scope='VD-P/count/stock/TC subblock; not a BRP point',
        rational_witness=dict(tau=str(tau),J=str(J),K1=str(K1),K2=str(K2),W1=str(W1),W2=str(W2),
            H=str(H),TC=str(parent_TC),TC2=str(parent_TC2),child_TC2=str(child_TC2),violation=str(W2-g),
            endpoint_alpha=list(map(str,alpha_selector)),endpoint_beta=list(map(str,beta_selector))),
        positive_fixed_tiny_fixtures=fixtures,integer_product_extensions_checked=checked,
        seconds=time.perf_counter()-tick))
    print(json.dumps(dict(PASS=True,extensions=checked,strict_violation=str(W2-g))))

if __name__=='__main__':globals()[sys.argv[1]]()
