"""Exact product-block witness and finite physical route mixing, without a solver."""
from round140_common import *
from fractions import Fraction as F
import itertools

def main():
    g=F(1,6);alpha=F(0);beta=F(1,2);tau=F(3);J=F(1,2);H=F(2);B=5;Bm=3
    s=[F(1,2),F(1,4),F(1,4)];q=[g*x for x in s]
    assert sum(s)==1 and sum(q)==g and sum(y*q[y] for y in range(3))==F(1,8)
    for y in range(3):
        assert alpha*s[y]<=q[y]<=beta*s[y]
        assert g-beta*(1-s[y])<=q[y]<=g-alpha*(1-s[y])
    stock=[(J-alpha*tau-Bm*g,'>=',-alpha*Bm),
           (J-beta*tau-B*g,'>=',-beta*B),
           (J-beta*tau-Bm*g,'<=',-beta*Bm),
           (J-alpha*tau-B*g,'<=',-alpha*B)]
    assert all(lhs>=rhs if sense=='>=' else lhs<=rhs for lhs,sense,rhs in stock)
    assert H<=4*J and H==2<6
    b=(2,2,1,0);routes=[]
    for y in sorted(set(itertools.permutations((2,1,0,0)))):
        changed=[i for i in range(4) if b[i]!=y[i]];found=None
        for route in itertools.permutations(changed):
            load=0;loads=[]
            for i in route:
                load+=b[i]-y[i];loads.append(load)
                if not 0<=load<=2:break
            else:
                assert load==2
                found=dict(Y=list(y),weight='1/12',route=[i+1 for i in route],
                    loads=loads,services=[dict(station=i+1,p=max(b[i]-y[i],0),d=max(y[i]-b[i],0)) for i in route],return_load=load)
                break
        assert found;routes.append(found)
    for i in range(4):
        assert [F(sum(v['Y'][i]==y for v in routes),12) for y in range(3)]==s
    write(OUT/'math/strict_block_and_routes.json',dict(PASS=True,Optimize=0,solver_imports=0,
        g=str(g),g_domain=['0','1/2'],selector=list(map(str,s)),state_g=list(map(str,q)),
        H_sum=str(H),J=str(J),tau=str(tau),TC_rhs='2',TC2_rhs='6',
        exact_stock_rows=[dict(lhs=str(a),sense=b,rhs=str(c)) for a,b,c in stock],routes=routes,
        scope='Strict relaxation block; mixed physical route block, with sufficiently large travel/time allowance. No claim of complete exported matrix or own-H cutoff feasibility, nor objective gain.'))
    # A second exact block point shows why TC2 alone cannot replace old TC.
    # support {0,2}, Bminus=3, B=5 gives ell=u=2 at threshold 2.
    s_high=F(5,8);K=4*s_high;g2=F(2,5);tau2=F(5);J2=g2*tau2;H2=F(8)
    old=2*(4-2)*K;new=F(2)*2*2
    assert K>2 and H2==new==8 and old==10 and H2<=4*J2
    for slope,budget,sense in [(F(0),3,'>='),(F(1,2),5,'>='),(F(1,2),3,'<='),(F(0),5,'<=')]:
        lhs=J2-slope*tau2-budget*g2;rhs=-slope*budget
        assert lhs>=rhs if sense=='>=' else lhs<=rhs
    write(OUT/'math/no_single_row_dominance.json',dict(PASS=True,Optimize=0,n=4,support=[0,2],Bminus=3,B=5,
        selector=['3/8','5/8'],ell=2,u=2,K=str(K),tau=str(tau2),g=str(g2),J=str(J2),H_sum=str(H2),
        TC_rhs=str(old),TC2_rhs=str(new),exact_common_products=True,stock_four_rows_satisfied=True,
        scope='TC2-alone admits this fractional product/selector block point while old TC excludes it. This is not a full BRP feasibility witness.'))
    print('Exact shared products, four stock rows and all 12 capacity-2 route mixtures verified; full-matrix scope not claimed')

if __name__=='__main__':main()
