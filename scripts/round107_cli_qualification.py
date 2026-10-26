"""Actual production CLI qualification after the inherited-start guard repair."""
from round107_common import *

def run(name='cli01',shared_wrapper=False):
    d=OUT/'qualification'/name;d.mkdir(parents=True,exist_ok=False)
    old=read(OUT/'development02/identity.json')['launches'][3]
    original=Path(old['destination']);command=[s.replace(str(original),str(d)) for s in old['command']]
    for flag,value in [('--time-limit','10'),('--process-wall-time-limit','10'),('--process-shutdown-margin','0')]:command[command.index(flag)+1]=value
    write(d/'plan.json',dict(layer='Actual production CLI, original preset/startup, finite whole10s, not performance',original_failed_launch=old,
        command=command,production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),fixture_PE_SHA=sha(BUILD/'Round107Tests.exe'),DLL_SHA=sha(DLL),source_bindings=bindings(),production_handoff=False))
    if shared_wrapper:
        write(d/'before.json',dict(command=command,maximum_whole_seconds=35,charged_by='cli_and_development03',actual_child_processes=1))
        tick=time.perf_counter()
        with (d/'stdout.log').open('x') as so,(d/'stderr.log').open('x') as se:
            p=subprocess.Popen(command,cwd=ROOT,env=env(),stdout=so,stderr=se)
            write(d/'process.json',dict(pid=p.pid,parent_pid=os.getpid()))
            try:code=p.wait(timeout=35)
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=se,stderr=se);p.wait();code=p.returncode
        write(d/'after.json',dict(exit_code=code,outer_seconds=time.perf_counter()-tick,actual_child_processes=1,fee_counted_in_shared_wrapper=True))
        assert code==0,(d/'stderr.log').read_text()[:2000]
    else:receipt(name,command,cap=35,engineering=False,children=1)
    result=read(d/'result.json');assert result['algorithm_preset']=='research-round107-ensc-frontier-struct'
    assert not any(s in result['status'].lower() for s in ['error','failed','invalid','numeric'])
    assert result['external_gini_tree_root_coverage_valid'] and result['external_gini_tree_parent_child_coverage_valid']
    assert result['external_gini_tree_backend_parameter_roundtrip_valid']
    requests=[json.loads(s) for s in (d/'external/round107/requests.jsonl').read_text().splitlines()]
    assert any(q['native_Optimize_started'] for q in requests)
    assert any(q['kind']!='LP' and q['native_Optimize_started'] for q in requests)
    assert all(q['failure'] in ['none',''] for q in requests),requests
    calls=[]
    import csv
    for p in d.rglob('calls.csv'):calls.extend(csv.DictReader(p.open(newline='')))
    assert not any(r['phase'] in ['iis','core_confirm'] for r in calls)
    closed={};begun={};not_started=set()
    for p in sorted((d/'journal').glob('event_*.json'),key=lambda x:int(x.stem.split('_')[1])):
        e=read(p)
        if e['kind']=='call':begun[e['call']]=e
        if e['kind']=='returned':closed[e['call']]=e
        if e['kind']=='not_started':not_started.add(e['call'])
        assert e['kind']!='failure',e
    assert set(begun)==set(closed)|not_started
    write(d/'qualification.json',dict(passed=True,actual_production_CLI=True,original_R83_preset_entered=True,
        inherited_R68_verified_start_retained=True,actual_backend_Optimize_count=result['external_gini_tree_optimize_count'],
        actual_original_LP=sum(q['kind']=='LP' and q['native_Optimize_started'] for q in requests),actual_scoped_MIP=sum(q['kind']!='LP' and q['native_Optimize_started'] for q in requests),IIS=0,
        status=result['status'],strict_certificate=result['strict_certified_original_problem'],request_count=len(requests),journal_intents=len(begun),journal_returns=len(closed),not_started=len(not_started),production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),production_handoff=False))
    print(json.dumps(dict(passed=True,production_CLI=True,PE=sha(BUILD/'ExactEBRP.exe'))))

if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else 'cli01')
