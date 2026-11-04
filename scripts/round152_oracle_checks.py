"""Review-driven aggregation checks, no repeated historical qualification suite."""
from itertools import product
from fractions import Fraction as F
import round152_oracle as oracle
from round152_qualify import scope
from round152_math import evaluate,states,bins
from round152_common import *

def run():
    from round150_lp import affinity
    configure();affinity();target=OUT/('qualification_aggregate'+(sys.argv[1] if len(sys.argv)>1 else ''));target.mkdir(exist_ok=False)
    d=scope([1.]*4,[[0,1,2]]*4,0,3,0.,.75,[.15]*4);pi={k:0. for k in states(d)}
    low,_=oracle.fallback(d,pi);original=oracle.solve_bin
    def mock(scope,pi,interval,target,cap,warm):
        return dict(Status=9,proven_empty=False,lower=low,upper=None,incumbent=None,bin=interval,
                    approximation_epsilon=.2,native_incumbent=low,native_bound=low)
    oracle.solve_bin=mock
    try:
        r0=oracle.price(d,pi,target/'none',None,max_calls=0)
        assert r0['lower']==low and len(r0['calls'])==0
        r1=oracle.price(d,pi,target/'partial',None,max_calls=1)
        assert r1['lower']==low and any(not b['solved'] for b in r1['active_bins'])
        r2=oracle.price(d,pi,target/'split',None,max_calls=12,width=.3)
        assert r2['lower']==low and any(b['depth']>0 for b in r2['active_bins'])
        for Y in product([0,1,2],repeat=4):
            p=evaluate(d,Y)
            if p['feasible'] and p['S']>0:assert any(b['interval'][0]<=p['S']<=b['interval'][1] for b in r2['active_bins'])
    finally:oracle.solve_bin=original
    zero=scope([1.,.5],[[0],[0]],0,0,.3,.5)
    rz=oracle.price(zero,{k:0. for k in states(zero)},target/'zero',None,max_calls=0)
    exact_zero=evaluate(zero,[0,0],exact=True)['phi']
    assert F(rz['lower'])<=exact_zero<=F(rz['upper']) and not rz['active_bins']
    # One actual tiny MIP checks the changed full-matrix readback/whitelist path.
    dd=scope([1.,.5],[[0,1,2],[0,1,2]],1,2,.2,.5)
    pp={k:.125*(-1 if k[1] else 1) for k in states(dd)}
    rr=original(dd,pp,bins(dd,.5)[1][0],target/'readback',cap=10)
    assert rr['complete_matrix_native_readback'] and rr['bound_status_qualified']
    write(target/'result.json',dict(PASS=True,unsolved_components_retained=True,partial_cover_lower_safe=True,
           refinement_inherits_parent_lower=True,zero_gamma_L_included=True,full_matrix_readback=True,
           mocks_only_test_aggregation_control_flow=True,actual_new_MIP=1))
    print('Aggregation and actual full-matrix readback PASS',flush=True)

if __name__=='__main__':run()
