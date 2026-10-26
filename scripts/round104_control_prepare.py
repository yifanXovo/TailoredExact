from round104_common import *
if __name__=='__main__':
    role=dict(next(r for r in read(PRIOR/'development_inputs.json')['roles'] if r['id']=='F2'))
    role.update(cap_seconds=1200,method_order=['OC-ACTIVE','OC-SHADOW','ENS-C','P-GRB'],
        question='Complete certification-scale self-paid finite-pool ACTIVE and full SHADOW cost, contemporary protected ENS and principal compact P')
    write(OUT/'control01_protocol.json',dict(roles=[role],phase='hull development',reference_billing='one_finite_batch',
        uniform_candidate='fresh same-model certified finite pool, numerical objective-dual ACTIVE, complete Start, default off',
        no_historical_pool_or_direction_import=True,no_component_time_Work_or_stall_gate=True,
        no_LONG_admission=True,conditional_stop='F5 same native scope zero and no medium-large opportunity; stop if F2 does not repay complete cost',
        materiality=read(OUT/'protocol.json')['materiality']))
    print('one fixed F2 four-arm complete control prepared; Optimize=0')
