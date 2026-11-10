"""New-interface checks only: exact witnesses, tiny exhaustive optima, matrix closure."""
from round161_common import *
from fractions import Fraction as F
from itertools import product,permutations

def rows(folder,label):
    return {r['name']:r for r in map(json.loads,(folder/f'{label}_rows.jsonl').read_text().splitlines())}
def cols(folder,label):
    return {r['name']:r for r in map(json.loads,(folder/f'{label}_columns.jsonl').read_text().splitlines())}

def matrix(folder):
    original,actual=rows(folder,'original'),rows(folder,'actual')
    oc,ac=cols(folder,'original'),cols(folder,'actual')
    reg=list(map(json.loads,(folder/'replacement_registry.jsonl').read_text().splitlines()))
    removed={r['column'] for r in reg if 'column' in r};deleted={r['row'] for r in reg if 'row' in r}
    assert set(ac)==(set(oc)-removed)|{s for s in ac if s.startswith('rn_')}
    assert all(ac[s]==v for s,v in oc.items() if s not in removed)
    assert {s:v for s,v in original.items() if s not in deleted}=={s:v for s,v in actual.items() if not s.startswith('rn_')}
    assert {s for s,v in original.items() if set(v['terms'])&removed}==deleted
    assert all(not set(r['terms'])&removed for r in actual.values())
    assert all(v['type']=='B' for s,v in ac.items() if s.startswith('state_'))
    # Check original penalty epigraph rows and objective byte-value equality.
    assert all(actual[s]==r for s,r in original.items() if any(t.startswith('e_') for t in r['terms']) and not set(r['terms'])&removed)
    return dict(PASS=True,common_rows=len(original)-len(deleted),common_columns=len(oc)-len(removed),
        removed_rows=len(deleted),removed_columns=len(removed),penalty_objective_same=True,physical_types_same=True)

def exact_witnesses():
    # First declared basic block. OLD lower 1/16 attained at G=z1=z2=1/16.
    g=F(1,16);m=[F(1,2),F(3,4)];t=F(3,4);L=F(1,2);U=F(1)
    w=[[F(1,4),F(1,2)]]*2
    for x,ws in zip(m,w):
        assert sum(ws)==t
        for mass,val in zip([1-x,x],ws):assert L*mass<=val<=U*mass
    assert sum(ws[1] for ws in w)==1 and w[0][1]==w[1][1]
    for x in m:assert 0<=g<=U*x and 0<=g-g<=U*(1-x)
    assert F(1,4)==2*(g+g)
    # R143's other direction; all state mass/product bounds explicitly checked.
    g2=F(1,3);mass=[F(1),F(1,2),F(0)];prod=[g2,g2,F(0)]
    for x,z in zip(mass,prod):
        assert 0<=z<=g2 and 0<=g2-z<=F(2,3)*(1-x) and z<=F(2,3)*x
    assert sum(abs(x-y) for i,x in enumerate(mass) for y in mass[i+1:])==3*sum(prod)
    t2=F(5,8);w2=[[0,t2],[F(1,4),F(3,8)],[t2,0]]
    for x,ws in zip(mass,w2):
        assert sum(ws)==t2
        for x0,val in zip([1-x,x],ws):assert L*x0<=val<=U*x0
    rho=[ws[1] for ws in w2];assert sum(rho)==1
    assert sum(abs(x-y) for i,x in enumerate(rho) for y in rho[i+1:])/3==F(5,12)
    # Complete RN t bound: site1 rho=t, site3 rho=0, middle zero mass forces
    # t - rho2 = 2t-1 >= L/2=1/4; hence t>=5/8, sum pairs=2t.
    return dict(PASS=True,first=dict(RN_G='0',OLD_min_G='1/16',stock='5/4'),
        second=dict(OLD_G='1/3',RN_min_G='5/12',stock='3/2',prior='R143'),scope='objective/stock subblocks only')

def tiny():
    root=OUT/'qualification/tiny';root.mkdir(parents=True,exist_ok=True);results=[]
    fixtures=[('positive',1,[2,0],[1,2]),('zero_union',2,[2,0],[1,2]),('zero_only',2,[0,0],[1,2])]
    for tag,q,initial,target in fixtures:
        folder=root/tag;folder.mkdir(exist_ok=True);inp=folder/'instance.txt';parent=folder/'parent.txt'
        inp.write_text(f'2 1 [{q}]\ncapacities = [100,2,2]\ninitial = [0,{initial[0]},{initial[1]}]\ntarget = [0,{target[0]},{target[1]}]\nweights = [0,1,1]\npoints = [(0,0),(0,0),(0,0)]\n')
        parent.write_text('1\n0 2 0 0\n\n')
        best=math.inf;feasible=[]
        for Y in product(range(3),repeat=2):
            delta=[b-y for b,y in zip(initial,Y)];active=[i for i in range(2) if delta[i]]
            good=False
            for perm in permutations(active):
                load=0;P=0
                for i in perm:
                    load+=delta[i];P+=max(0,delta[i])
                    if not 0<=load<=q:break
                else:
                    if 5*P<=100:good=True
            if good:
                r=[F(1./d)*y for y,d in zip(Y,target)];S=sum(r);G=abs(r[0]-r[1])/(2*S) if S else F(0)
                J=G+sum(F(.1)*abs(x-1) for x in r);best=min(best,float(J));feasible.append(dict(Y=Y,J=float(J)))
        for form in ('OLD','RN'):
            dest=folder/form;cmd=[PE,inp,100,2,3,.1,parent,dest,form,'MIP',30,-1]
            if tag=='zero_only' and form=='RN' and (dest/'outcome.json').exists() and not (folder/'RN_bound_fix_v2').exists():
                dest.rename(folder/'RN_bound_fix_v2')
            if not (dest/'outcome.json').exists():
                if dest.exists():dest.rename(folder/(form+'_failed_v1'))
                rc=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=meter.environment(),capture_output=True)
                (folder/(form+'.stdout')).write_bytes(rc.stdout);(folder/(form+'.stderr')).write_bytes(rc.stderr)
                assert rc.returncode==0,(tag,form,rc.stderr.decode())
            value=read(dest/'outcome.json');assert abs(value['physical_U']-best)<1e-7,(tag,form,value,best)
            assert value['bound_available'] and abs(value['qualified_lower']-best)<1e-6,value
            if form=='RN':audit=matrix(dest)
            results.append(dict(fixture=tag,form=form,enumerated_optimum=best,outcome=value))
        write(folder/'enumeration.json',dict(physical_Y=feasible,minimum=best,audit=audit))
    write(OUT/'qualification/tiny.json',dict(PASS=True,results=results))

def all_checks():
    write(OUT/'qualification/exact_witnesses.json',exact_witnesses());tiny()
    results=[]
    for role in ('R-X35-S-T2','N-B35-S'):
        label='RX35_RN_export_v1' if role.startswith('R-') else 'NB35_RN_export_v1'
        path=OUT/'runs'/label
        if not path.exists():
            from round161_experiment import command
            cmd=command(role,'RN','export',label,120,-1)
            rc=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=meter.environment(),capture_output=True)
            assert rc.returncode==0,rc.stderr.decode()
        results.append(dict(role=role,admission=read(path/'admission.json'),matrix=matrix(path),block=read(path/'block.json')))
    write(OUT/'qualification/new_interfaces.json',dict(PASS=True,real_Starts=results,scope='new replacement interfaces only'))
    print('PASS exact non-dominance, tiny exhaustive positive/zero, full real Start/common blocks')

if __name__=='__main__':all_checks()
