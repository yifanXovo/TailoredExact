"""Finite Rank-PC reconstruction from six saved R143 points; zero Optimize."""
import gzip
from fractions import Fraction as F
from round143_offline import station,value
from round144_lp import outward
from round144_common import *
configure()
def local_floor():
    """Exact fixed-selector old-block/RN cross-section; no Optimize or Native."""
    tick=time.perf_counter()
    s=[[F(0),F(1)],[F(1,2),F(1,2)],[F(1),F(0)]]
    y=[v[1] for v in s];tau=sum(y)
    h=[abs(y[i]-y[j]) for i in range(3) for j in range(i+1,3)];H=sum(h)
    def old(g):
        q=[[F(0),g],[F(0),g],[g,F(0)]];J=sum(v[1] for v in q)
        assert all(sum(v)==g and all(max(F(0),g+u-1)<=w<=min(g,u) for u,w in zip(a,v)) for a,v in zip(s,q))
        assert H<=3*J and max(g,tau+2*g-2)<=J<=min(tau+g-1,2*g)
        assert 1<=tau<=2 and H>=tau and H>=2
        # Endpoint pair couplings: one marginal in every pair is fixed.
        for i in range(3):
            for j in range(i+1,3):
                assert y[i] in (0,1) or y[j] in (0,1)
                pair=[[s[i][a]*s[j][b] for b in range(2)] for a in range(2)]
                assert all(sum(pair[a])==s[i][a] for a in range(2))
                assert all(sum(pair[a][b] for a in range(2))==s[j][b] for b in range(2))
                assert sum(pair[a][b]*abs(a-b) for a in range(2) for b in range(2))==abs(y[i]-y[j])
        return q,J
    g=F(1,3);penalty=F(1,12);q,J=old(g)
    floor=F(5,12);rhs=1-s[0][0]+s[1][0]/2-3*s[2][1]
    assert rhs-3*g==F(1,4) and g+penalty==floor
    # In this fixed-selector RN cross-section, v=(t,1-t,0),
    # w_20=2t-1>=1/4, hence t>=5/8 and g>=2t/3>=5/12.
    t=F(5,8);w=[[F(0),t],[2*t-1,1-t],[t,F(0)]]
    assert all(sum(v)==t and all(F(1,2)*u<=z<=u for u,z in zip(a,v)) for a,v in zip(s,w))
    v=[a[1] for a in w];assert sum(v)==1
    assert sum(abs(v[i]-v[j]) for i in range(3) for j in range(i+1,3))/3==floor
    old(floor)  # RN attaining point also extends all declared old rows.
    write(OUT/'math/local_floor_witness.json',dict(PASS=True,Optimize=0,Native_load=0,seconds=time.perf_counter()-tick,
        scope='Continuous three-site Gini/stock/TC/TC2/endpoint-pair block, selector masses fixed to (1,1/2,0), plus independent p>=0; not full routing P',
        objective='g+p',selectors=[[str(z) for z in a] for a in s],old_g=str(g),penalty=str(penalty),old_objective=str(g+penalty),RN_optimum=str(floor),
        RN_lower_proof='v=(t,1-t,0); w_20=2t-1>=1/4; g>=2t/3>=5/12',
        attaining_t=str(t),attaining_w=[[str(z) for z in a] for a in w],
        old_q=[[str(z) for z in a] for a in q],H=str(H),J=str(J),tau=str(tau),PC_rhs=str(rhs),PC_violation=str(rhs-3*g),
        PC=dict(sense='>=',terms=dict(G='3',state_1_0='1',state_2_0='-1/2',state_3_1='3'),rhs='1'),
        no_full_routing_or_universal_floor_dominance_claim=True))
    print('Exact local same-objective floor/PC witness PASS; zero Optimize/Native')
def main():
    tick=time.perf_counter();old=ROOT/'results/unified_exact_round143';certs=read(old/'math/offline_point_checks.json')['results'];facts=[]
    for cert in certs:
        role,variant=cert['role'],cert['variant']
        if role not in ['K-35-U','R-X20-S-T1']:continue
        folder=old/'inherited/roots'/role;point_path=folder/variant/'solution.json.gz'
        assert sha(point_path)==cert['source_point_SHA'];point=json.loads(gzip.decompress(point_path.read_bytes()))
        spec=read(old/'domains'/role/'RN.json');supports={int(i):ys for i,ys in spec['supports'].items()}
        lt,ut=F(cert['L_t']),F(cert['U_t']);a={int(i):F(v) for i,v in cert['rank_coefficients'].items()};eta=F(cert['eta']);n=len(supports)
        ordered=sorted(a.values());assert sum(ordered)==0
        for k in range(1,n):assert sum(ordered[:k])>=sum(F(2*r-n-1) for r in range(1,k+1))
        slopes={i:(a[i]-eta)*F(spec['c_binary64'][str(i)]) for i in supports}
        sites={}
        for i,ys in supports.items():
            states=[(y,max(F(0),F(point[f'state_{i}_{y}']))) for y in ys]
            sites[i]=station(slopes[i],states,lt,ut,reverse=slopes[i]<0)
        lo=max([lt]+[s['breaks'][0] for s in sites.values()]);hi=min([ut]+[s['breaks'][-1] for s in sites.values()]);assert lo<=hi
        knots=sorted({lo,hi}|{t for s in sites.values() for t in s['breaks'] if lo<t<hi})
        t=min(knots,key=lambda t:sum(value(s,t) for s in sites.values()))
        intervals={i:(min(v[2] for v in s['segments'] if v[0]<=t<=v[1]),max(v[2] for v in s['segments'] if v[0]<=t<=v[1])) for i,s in sites.items()}
        lam={i:v[0] for i,v in intervals.items()};lower=sum(lam.values());upper=sum(v[1] for v in intervals.values())
        if lower<=0<=upper:
            left=-lower
            for i in supports:
                take=min(left,intervals[i][1]-lam[i]);lam[i]+=take;left-=take
            assert left==0
        elif upper<0:lam={i:v[1] for i,v in intervals.items()}
        Lambda=sum(lam.values());rhs=eta+min(lt*Lambda,ut*Lambda);terms={'G':F(n)}
        for i,ys in supports.items():
            for y in ys:
                d=slopes[i]*y-lam[i];kappa=min(lt*d,ut*d)
                if kappa:terms[f'state_{i}_{y}']=-kappa
        violation=rhs-sum(v*F(point[k]) for k,v in terms.items());assert violation>0,(role,variant,float(violation))
        transported={};correction=F(0)
        for k,v in terms.items():
            w=float(v)
            if abs(w)<1e-12:w=0.
            error=F(w)-v;upper_bound=F(cert.get('old_g',1)) if k=='G' else F(1)
            # G's coefficient n is exact, so its bound does not affect this sum.
            assert k!='G' or error==0
            correction+=min(F(0),error*upper_bound)
            if w:transported[k]=w
        binary_rhs=outward(rhs+correction,False);binary_violation=F(binary_rhs)-sum(F(v)*F(point[k]) for k,v in transported.items())
        row=dict(role=role,variant=variant,source_point_SHA=sha(point_path),rank_coefficients={str(i):str(v) for i,v in a.items()},eta=str(eta),
            lambda_exact={str(i):str(v) for i,v in lam.items()},L_t=str(lt),U_t=str(ut),exact_terms={k:str(v) for k,v in terms.items()},exact_rhs=str(rhs),
            exact_violation=str(violation),violation_div_n=float(violation/n),exact_nonzeros=len(terms),
            binary64=dict(sense='>',terms=transported,rhs=binary_rhs,conversion_correction=str(correction),violation_div_n=float(binary_violation/n)),
            identity='Finite reconstruction from saved rank/eta and actual binary64 points; independent of the missing supplemental ZIP',
            scope='Valid structural Rank-PC; point evaluation is not an optimized objective increment or Native qualification')
        write(OUT/'math/rank_PC'/(role+'_'+variant+'.json'),row)
        facts.append({k:row[k] for k in ['role','variant','source_point_SHA','violation_div_n','exact_nonzeros']})
    assert len(facts)==6
    write(OUT/'math/offline_rank_PC.json',dict(PASS=True,facts=facts,seconds=time.perf_counter()-tick,Optimize=0,Native_load=0,missing_supplement_reconstructed=True))
    print(json.dumps(facts),flush=True)
if __name__=='__main__':local_floor() if len(sys.argv)>1 and sys.argv[1]=='local_floor' else main()
