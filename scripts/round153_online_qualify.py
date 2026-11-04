"""Finite checks of new deterministic Native and owned helper exits."""
from itertools import product
from fractions import Fraction as F
from round152_qualify import scope
from round153_pricing import Oracle,stock_value
from round153_common import *

def run(label):
    from round100_gurobi_runtime import gp
    from round150_lp import affinity
    configure();affinity();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    d=scope([1.,.5],[[0,1,2,3,4]]*2,1,4,.05,.3)
    universe=[stock_value(d,Y) for Y in product(*[s['support'] for s in d['stations']])]
    universe=[v for v in universe if v['feasible']]
    costs={(s['i'],y):(-2.*y if s['i']==1 else .5*y) for s in d['stations'] for y in s['support']}
    exact=min(stock_value(d,v['Y'],1.,costs)['price'] for v in universe)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        for name,nodes,deadline in [('zero_nodes',0,None),('normal_nodes',4096,None),('expired_global',4096,time.perf_counter()-1)]:
            oracle=Oracle(d,env,old_joint=True)
            try:r=oracle.price(1.,costs,target/name,node_limit=nodes,absolute_gap=1e-4,global_deadline=deadline)
            finally:oracle.close()
            assert r['calls'] and F(r['lower'])<=exact and (r['upper'] is None or exact<=F(r['upper']))
            call=read(target/name/'call.json');assert call['node_limit']==nodes and call['cap'] is None
            q=r['calls'][0]
            if name=='expired_global':assert q['Status']==9 and not q['bound_status_qualified'] and r['reason']=='safe_DP_fallback'
            assert q['bound_status_qualified']==(q['Status'] in (2,8))
            facts.append(dict(name=name,Status=q['Status'],nodes=q['nodes'],lower=r['lower'],upper=r['upper'],exact=str(exact),
                native_bound_qualified=q['bound_status_qualified'],Native_TimeLimit=call['actual_Native_TimeLimit']))
    driver=read(OUT/'helper_control_driver.json');assert sha(driver['PE'])==driver['PE_SHA']
    sleeper=target/'sleep with spaces.py'
    sleeper.write_text('import subprocess,sys,time,os,json\nfrom pathlib import Path\np=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"])\nPath(sys.argv[1]).write_text(json.dumps({"parent":os.getpid(),"child":p.pid}))\ntime.sleep(60)\n',encoding='utf-8')
    pidfile=target/'owned_pids.json'
    tests=[('clean',5,[PYTHON,'-c','import sys;sys.exit(0)'],0),
           ('failed',5,[PYTHON,'-c','import sys;sys.exit(7)'],7),
           ('expired',0,[PYTHON,'-c','import sys;sys.exit(0)'],124),
           ('owned_tree_timeout',1,[PYTHON,sleeper,pidfile],124)]
    for name,remaining,args,expected in tests:
        command=[driver['PE'],str(remaining),*map(str,args)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=10,check=True)
        (target/f'{name}.stdout.txt').write_text(result.stdout,encoding='utf-8')
        actual=json.loads(result.stdout);assert actual['exit']==expected
        assert actual['seconds']<remaining+3
        facts.append(dict(name=name,actual=actual,command=command))
    pids=read(pidfile);assert meter.process_birth(pids['parent']) is None and meter.process_birth(pids['child']) is None
    manifest=read(OUT/'helper_manifest.json');manifest['python_SHA']='0'*64;write(target/'bad_manifest.json',manifest)
    source=OUT/'reference/N-B35-S/direct/model.lp'
    # Dependency rejection is checked before the supplied source is opened.
    command=[str(PYTHON),'-B',str(ROOT/'scripts/round153_online.py'),'--source',str(source),'--out',str(target/'rejected_helper'),
        '--Bminus','0','--B','1','--manifest',str(target/'bad_manifest.json'),'--remaining-global-seconds','30']
    failed=subprocess.run(command,capture_output=True,text=True,timeout=35)
    assert failed.returncode==1 and (target/'rejected_helper/failure.json').exists() and not (target/'rejected_helper/response.txt').exists()
    facts.append(dict(name='dependency_rejection',exit_code=failed.returncode,response_absent=True))
    write(target/'result.json',dict(PASS=True,facts=facts,owned_child_and_grandchild_absent=True,
        tests_only_new_interfaces=True,not_performance_sample=True))
    print(json.dumps(dict(PASS=True,fixtures=len(facts))),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
