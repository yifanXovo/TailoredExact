"""Protection and once-only untouched confirmation inputs, no Optimize.

The candidate source/rules never change here. Creation is exclusive and a
failed/zero/losing draw is retained. Confirmation is run only after admission.
"""
from round103_common import *
import random,math

def new_role(tag,V,Q,seed,cap,order):
    rng=random.Random(seed);M=len(Q);targets=[0]+[rng.randrange(15,29) for _ in range(V)]
    initial=[50000]+[max(1,min(d+14,d+rng.randrange(-15,16))) for d in targets[1:]]
    # Deterministic stock shortage ensures a positive original optimum with
    # strictly positive station weights, independently of a route search.
    wanted=round(.88*sum(targets));excess=sum(initial[1:])-wanted
    for j in range(V,0,-1):
        change=min(max(0,initial[j]-1),max(0,excess));initial[j]-=change;excess-=change
    if sum(initial[1:])>wanted:raise RuntimeError('shortage construction')
    capacities=[100000]+[max(targets[j]+16,initial[j]+4) for j in range(1,V+1)]
    weights=[0.]+[round(rng.uniform(.25,1.),6) for _ in range(V)]
    ratios=[0.]+[round(min(.7,.7*initial[j]/targets[j]),4) for j in range(1,V+1)]
    points=[(584000.,4512000.)]
    for j in range(V):
        if V==30:
            angle=2*math.pi*(j%10)/10+rng.uniform(-.08,.08);radius=400+330*(j//10)+rng.uniform(-65,65)
            x,y=radius*math.cos(angle),radius*math.sin(angle)
        else:
            x=(j%10-4.5)*205+rng.uniform(-35,35);y=(j//10-2)*280+rng.uniform(-35,35)+180*math.sin(j%10)
        points.append((round(584000+x,3),round(4512000+y,3)))
    path=ROOT/'reference/round103_confirmation'/(tag+'.txt');path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',newline='\n') as f:
        f.write(f'{V} {M} {Q}\n')
        for name,values in [('capacities',capacities),('initial',initial),('target',targets),('weights',weights),('min_ratio',ratios),('points',points)]:f.write(name+' = '+repr(values)+'\n')
    return dict(id='R103-'+tag,V=V,M=M,Q_vector=Q,T_seconds=7200,pickup_seconds=60,drop_seconds=60,lambda_=0.15,
        input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),
        seed=seed,cap_seconds=cap,method_order=order,total_initial=sum(initial[1:]),total_target=sum(targets),
        zero_excluded_by_stock_shortage=True,all_station_weights_positive=True,design_isolated_in_R103=True,
        historical_role_not_globally_unseen=False,selection='Two fixed seeds and layouts, no outcomes/LPs/routes inspected; no redraw',
        geometry='three_rings' if V==30 else 'bent_grid')

if __name__=='__main__':
    stage=sys.argv[1]
    if stage=='protection_C3':
        manifest=ROOT/'results/unified_exact_round98/confirmation_protocol01.json'
        p=dict(next(r for r in read(manifest)['roles'] if r['id']=='C3'))
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        p.update(id='R98-C3',cap_seconds=1800,method_order=['ENS-C','H-SUBMIT','P-GRB'],
            design_isolated_in_R103=False,historical_role_not_globally_unseen=True,
            metadata_source=manifest.relative_to(ROOT).as_posix(),metadata_sha256=sha(manifest),
            question='Known R102 regression protection; preserve ENS advantage and reveal principal P comparison.')
        write(OUT/'protection_C3_protocol.json',dict(roles=[p],phase='hull development',reference_billing='one_finite_batch',planned_once=True))
    elif stage=='confirmation':
        freeze=read(OUT/'production_freeze.json');assert freeze['source_bindings']==bindings()
        items=[new_role('H1',30,[18,24,30],103050301,900,['P-GRB','ENS-C','H-SUBMIT']),
               new_role('H2',50,[16,22,28,34],103050502,3600,['H-SUBMIT','P-GRB','ENS-C'])]
        for p in items:p['lambda']=p.pop('lambda_')
        f5=dict(next(r for r in read(OUT/'development_inputs.json')['roles'] if r['id']=='F5'))
        f5.update(cap_seconds=3600,method_order=['ENS-C','P-GRB','H-SUBMIT'],design_isolated_in_R103=False)
        stages=[]
        for name,p,phase in [('confirmation01',items[0],'hull confirmation'),('confirmation_long01',items[1],'hull long'),('long_tail01',f5,'hull long')]:
            protocol=dict(roles=[p],phase=phase,reference_billing='one_finite_batch',planned_once=True,
                source_freeze_sha256=sha(OUT/'production_freeze.json'),no_candidate_revision=True,
                admission='Only if completed development/protection leaves this unchanged candidate worthwhile; explicit cancellation otherwise.')
            file=OUT/(name+'_protocol.json');write(file,protocol);stages.append(dict(name=name,path=file.relative_to(ROOT).as_posix(),sha256=sha(file)))
        write(OUT/'confirmation_freeze.json',dict(roles=items,stages=stages,production_freeze_sha256=sha(OUT/'production_freeze.json'),
            generator_sha256=sha(__file__),
            before_any_confirmation_search=True,no_redraw=True,Optimize_calls=0,
            disclosure='New synthetic inputs; broad shortages/geometries belong to established research families, these bytes/seeds have no earlier data.',
            long_groups='H2 design-isolated V50 and F5 existing tail, each common3600s three arms; no short-window stitching'))
    else:raise ValueError(stage)
    print(stage+' written; Optimize=0')
