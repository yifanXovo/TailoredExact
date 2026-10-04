"""Finite native/dev protocols. No outcome-based instance dispatch."""
from round102_common import *
from pathlib import Path
import sys
if __name__=='__main__':
    stage=sys.argv[1];roles={r['id']:r for r in read(OUT/'development_inputs.json')['roles']}
    if stage=='native01':
        p=dict(roles['F2']);p['cap_seconds']=120;p['method_order']=['J-SHADOW','J-SUBMIT']
        items=[p];phase='service qualification';question='Actual root original-column rows, full-old-model residual, API and lifecycle/failure/cost; no complete performance conclusion.'
    elif stage=='protection01':
        p=dict(roles['F2']);p['cap_seconds']=1200;p['method_order']=['ENS-C','J-SUBMIT','P-GRB']
        items=[p];phase='service development';question='Complete nonzero certification protection and direct net component value; P remains main benchmark.'
    elif stage=='development01':
        items=[]
        for id,order in [('R98-C2',['P-GRB','ENS-C','J-SUBMIT']),('R99-N2',['J-SUBMIT','P-GRB','ENS-C'])]:
            p=dict(roles[id]);p['cap_seconds']=1800;p['method_order']=order;items.append(p)
        phase='service development';question='Medium heterogeneous service-coordinate mechanism and real P disadvantage, complete budget UB/LB trajectories.'
    else:raise ValueError(stage)
    for p in items:p['question']=question
    write(OUT/(stage+'_protocol.json'),dict(roles=items,phase=phase,reference_billing='one_finite_batch',maximum_optimize_calls_per_arm=8,
        uniform_candidate='two exact-integer profit directions, audited DP, root-only, no R101 or M-B stacking',
        questions=question,planned_once=True))
    print(stage+' protocol saved; Optimize=0')
