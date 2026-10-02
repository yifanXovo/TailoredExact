"""Freeze observed development roles, never generate confirmation on import."""
from round99_common import *
old=read(ROOT/'results/unified_exact_round98/development_inputs.json')['roles']
confirmation=read(ROOT/'results/unified_exact_round98/confirmation_protocol01.json')['roles']
roles=[]
for name,cap,order in [
    ('F2',900,['ENS-C','Q-I','M-B','R1','R2','P-GRB']),
    ('R98-C1',600,['M-B','R2','ENS-C','Q-I','R1','P-GRB']),
    ('R98-C2',1800,['P-GRB','R1','M-B','ENS-C','R2','Q-I'])]:
    if name=='F2':p=dict(next(p for p in old if p['id']==name))
    else:
        p=dict(next(p for p in confirmation if 'R98-'+p['id']==name))
        p['historical_initial_witness']=f'results/unified_exact_round98/confirmation01/raw/{"03_C1" if name=="R98-C1" else "04_C2"}_ENS-C/external/initial_witness.json'
        p['historical_initial_witness_sha256']=sha(ROOT/p['historical_initial_witness'])
        p['diagnostic_cutoff']=read(ROOT/p['historical_initial_witness'])['objective']
        p['diagnostic_gamma_L']=0;p['diagnostic_gamma_U']=min(1,p['diagnostic_cutoff'])
    p['id']=name;p['cap_seconds']=cap;p['method_order']=order
    assert sha(ROOT/p['input_path'])==p['input_sha256']
    roles.append(p)
write(OUT/'development_inputs.json',dict(roles=roles,optimizer_calls=0,
    phase='observed development factorial',no_confirmation_reuse=True))
print('registered 18 factorial arms, max19800s; historical Starts diagnostic only')
