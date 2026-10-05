"""Finite protocols. Imported modules never launch work."""
from round103_common import *
if __name__=='__main__':
    stage=sys.argv[1];roles={r['id']:r for r in read(OUT/'development_inputs.json')['roles']}
    if stage=='native01':
        p=dict(roles['F2']);p['cap_seconds']=120;p['method_order']=['H-SHADOW','H-SUBMIT'];items=[p]
        phase='hull qualification';question='Actual root separation, scaled row readback, Start all-row validation, journal/ledger identities and costs; no complete performance claim.'
    elif stage=='protection01':
        p=dict(roles['F2']);p['cap_seconds']=1200;p['method_order']=['H-SUBMIT','ENS-C','P-GRB','J-SUBMIT'];items=[p]
        phase='hull development';question='Complete F2 certification and main P position, same-build ENS protection and one finite J attribution reference.'
    elif stage=='development01':
        items=[]
        for id,order in [('R98-C2',['P-GRB','H-SUBMIT','ENS-C']),('R99-N2',['ENS-C','P-GRB','H-SUBMIT'])]:
            p=dict(roles[id]);p['cap_seconds']=1800;p['method_order']=order;items.append(p)
        phase='hull development';question='Complete medium no-hit and activation roles; protect actual P/ENS position, quality and all preparation costs.'
    else:raise ValueError(stage)
    for p in items:p['question']=question
    write(OUT/(stage+'_protocol.json'),dict(roles=items,phase=phase,reference_billing='one_finite_batch',
        uniform_candidate='one pre-MIP standard-LP pass, normalized full-domain dyadic support separation, base domain, at most one row per car',
        questions=question,planned_once=True))
    print(stage+' protocol saved; Optimize=0')
