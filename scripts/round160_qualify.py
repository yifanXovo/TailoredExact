"""Finite new-interface checks: exact objective map, parent lift and tiny exhaustive physical domain."""
from fractions import Fraction as F
from itertools import product,permutations
from round160_common import *
from round160_prepare import data
from round157_fleet import verify

def original(d,Y):
    r=[F(1./d['target'][i])*Y[i-1] for i in range(1,d['n']+1)];S=sum(r,F(0))
    G=sum((abs(a-b) for pos,a in enumerate(r) for b in r[pos+1:]),F(0))/(d['n']*S) if S else F(0)
    H=sum((F(d['lam']*d['weights'][i])*abs(r[i-1]-1) for i in range(1,d['n']+1)),F(0))
    return G+H,G

def model_objective(folder,d):
    from round100_gurobi_runtime import gp
    admission=read(folder/'admission.json');vals=read(folder/'start_values.json')
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(str(folder/'model.mps'),env=env) as model:
            assert model.NumVars==len(vals);assert len({v.VarName for v in model.getVars()})==model.NumVars
            assert len({v.ConstrName for v in model.getConstrs()})==model.NumConstrs
            point=dict(zip([v.VarName for v in model.getVars()],vals));nb=read(folder.parent/'neighborhood.json');B=nb['B'];parent=nb['parent_Y']
            import random
            rng=random.Random(160);errors=[]
            for trial in range(24):
                Y=list(parent)
                if trial:
                    for i in B:
                        ys=[int(v.VarName.split('_')[2]) for v in model.getVars() if v.VarName.startswith(f'x_{i}_')];Y[i-1]=rng.choice(ys)
                J,G=original(d,Y);S=sum(F(1./d['target'][i])*Y[i-1] for i in range(1,d['n']+1));assert S>0
                t=float(1/S);point['t']=t;point['q']=float(G)
                for i in B:
                    for v in model.getVars():
                        if v.VarName.startswith(f'x_{i}_'):point[v.VarName]=float(int(v.VarName.split('_')[2])==Y[i-1])
                        elif v.VarName.startswith(f'w_{i}_'):point[v.VarName]=t*float(int(v.VarName.split('_')[2])==Y[i-1])
                    point[f'rho_{i}']=(1./d['target'][i])*Y[i-1]*t
                for pos,i in enumerate(B):
                    for j in B[pos+1:]:point[f'a_{i}_{j}']=abs(point[f'rho_{i}']-point[f'rho_{j}'])
                actual=F(model.ObjCon)+sum((F(v.Obj)*F(point.get(v.VarName,0.)) for v in model.getVars()),F(0))
                errors.append(abs(float(actual)*admission['scale']-float(J)))
                for c in model.getConstrs():
                    if c.ConstrName.startswith(('normalization_','normalized_mass_','normalized_ratio_','full_original_Gini_','block_pair_','product_')):
                        row=model.getRow(c);lhs=sum(F(row.getCoeff(p))*F(point[row.getVar(p).VarName]) for p in range(row.size()));gap=float(lhs-F(c.RHS))
                        assert (abs(gap) if c.Sense=='=' else gap if c.Sense=='<' else -gap)<1e-10,(c.ConstrName,gap)
            assert max(errors)<1e-12
    return dict(samples=24,max_objective_error=max(errors),parent_lift_residual=admission['parent_lift_residual'],Optimize=0)

def real():
    facts=[]
    for role,label in [('R-X35-S-T2','qualify_rx'),('N-B35-S','qualify_nb')]:
        source=read(OUT/'inputs'/role/'source.json');run=OUT/'runs'/label;p=read(run/'final.json')
        verified=verify(source['data'],p);assert verified['original_T_feasible']
        facts.append(dict(role=role,check=model_objective(run/'block_0/positive',source['data']),physical_J=verified['J']))
    write(OUT/'qualification/real_interfaces.json',dict(PASS=True,facts=facts,Optimize=0))

def fixture():
    folder=OUT/'qualification/tiny';folder.mkdir(parents=True,exist_ok=False)
    text='4 2 [3, 3]\ncapacities = [50000, 2, 2, 3, 3]\ninitial = [50000, 2, 2, 0, 0]\ntarget = [1, 1, 1, 1, 1]\nweights = [0, 1, 1, 1, 1]\nmin_ratio = [0, 0, 0, 0, 0]\npoints = [(0,0), (1,0), (3,0), (3,1), (1,1)]\n'
    (folder/'instance.txt').write_text(text)
    (folder/'parent.txt').write_text('2\n0 6 0 1 4 2 3 0\n2 -1 2 -3\n1 2 0 0\n\n')
    p=dict(Q_vector=[3,3],T_seconds=100,pickup_seconds=2,drop_seconds=5,**{'lambda':.15});d=data(p,folder/'instance.txt')
    commands=[]
    for mode in ('joint','uncompressed'):
        command=[PE,folder/'instance.txt',100,2,5,.15,folder/'parent.txt',folder/mode,120,512,1,mode,1,2,3,4]
        subprocess.run(list(map(str,command)),env=meter.environment(),check=True);commands.append(list(map(str,command)))
    # Enumerate all supported stock vectors and elementary car assignments/orders.
    best=None;count=0
    for Y in product(range(3),range(3),range(4),range(4)):
        if sum(Y)>4:continue
        ids=[i for i in range(1,5) if Y[i-1]!=d['initial'][i]]
        feasible=False
        for order in permutations(ids):
            for cut in range(len(ids)+1):
                ok=True
                for k,part in enumerate((order[:cut],order[cut:])):
                    load=0;P=0
                    for i in part:delta=d['initial'][i]-Y[i-1];load+=delta;P+=max(0,delta);ok &= 0<=load<=3
                    travel=sum(d['distance'][a][b] for a,b in zip((0,)+part,part+(0,)))
                    ok &= travel+7*P<=100+1e-7
                count+=1
                if ok:feasible=True;break
            if feasible:break
        if feasible:
            J=original(d,Y)[0];best=J if best is None else min(best,J)
    for mode in ('joint','uncompressed'):
        result=read(folder/mode/'final.json');v=verify(d,result);assert v['original_T_feasible'] and abs(v['J']-float(best))<1e-10
    initial=read(folder/'joint/initial.json');assert initial['routes'][0]['P']==4>3
    assert initial['routes'][1]['nodes']==[0,0]
    # Same-domain compression equivalence on a nontrivial immutable outside run.
    for mode in ('joint','uncompressed'):
        command=[PE,folder/'instance.txt',100,2,5,.15,folder/'parent.txt',folder/('fixed_run_'+mode),120,512,1,mode,3]
        subprocess.run(list(map(str,command)),env=meter.environment(),check=True)
    assert abs(read(folder/'fixed_run_joint/final.json')['J']-read(folder/'fixed_run_uncompressed/final.json')['J'])<1e-10
    write(OUT/'qualification/tiny_interfaces.json',dict(PASS=True,brute_force_J_exact=str(best),enumerated_route_tests=count,
        general_pickup_drop=[2,5],cumulative_P=4,Q=3,empty_vehicle=True,zero_stock_branch_saved=True,
        same_domain_compression=True,commands=commands))

if __name__=='__main__':globals()[sys.argv[1]]()
