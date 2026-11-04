"""Independent pure-B scalar-floor opportunity; no offline data enters production."""
from round152_math import h_exact
from round153_pricing import Oracle
from round153_common import *

def run(role='K-35-U',label='initial',cap=120):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    d=read(OLD/'domains'/role/'domain.json');scope=d['scope'];target=OUT/'floor'/f'{role}_{label}'
    target.mkdir(parents=True,exist_ok=False)
    costs={(s['i'],y):h_exact(s,y) for s in scope['stations'] for y in s['support']}
    old=read(OLD/'oracle'/f'{role}_strong_zero'/'result.json')
    warm=[v['Y'] for v in old.get('stocks',[])]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        oracle=Oracle(scope,env,old_joint=True);r=oracle.price(1.,costs,target/'pricing',cap=float(cap),warm=warm);oracle.close()
    r.update(role=role,pure_B=d['B_L'],initial_B_not_terminal=True,
             classification='ROOT_FLOOR_GAIN' if r['lower']>d['B_L']+1e-6 else 'NO_ROOT_GAIN' if r['upper'] is not None and r['upper']<=d['B_L'] else 'UNDECIDED')
    write(target/'result.json',r)
    print(json.dumps({k:r[k] for k in ['role','pure_B','lower','upper','classification']}),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
