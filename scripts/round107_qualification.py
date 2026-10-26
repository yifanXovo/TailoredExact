"""Finite native fixtures; independent of, and never fed into, formal arms."""
from round107_common import *
import csv
def run(name):
    d=OUT/'qualification'/name;d.mkdir(parents=True,exist_ok=False)
    jobs=[('scope','native',180),('target','target',300),('outer_deadline','deadline',60)]
    if name!='final03':jobs.append(('inner_deadline','inner-deadline',30))
    write(d/'plan.json',dict(layer='finite native qualification, no production handoff',jobs=jobs,declared_fixture_children=len(jobs),
        candidate_PE_SHA=sha(BUILD/'ExactEBRP.exe'),fixture_PE_SHA=sha(BUILD/'Round107Tests.exe'),DLL_SHA=sha(DLL),source_bindings=bindings()))
    for n,(label,mode,cap) in enumerate(jobs,1):
        command=list(map(str,[BUILD/'Round107Tests.exe',mode,d/label]));tick=time.perf_counter()
        write(d/f'{n:02d}_before.json',dict(command=command,started_unix=time.time()))
        with (d/f'{n:02d}_stdout.log').open('x') as so,(d/f'{n:02d}_stderr.log').open('x') as se:
            p=subprocess.Popen(command,cwd=ROOT,env=env(),stdout=so,stderr=se)
            write(d/f'{n:02d}_process.json',dict(pid=p.pid,parent_pid=os.getpid()))
            code=p.wait(timeout=cap)
        write(d/f'{n:02d}_after.json',dict(exit_code=code,outer_seconds=time.perf_counter()-tick))
        assert code==0,(label,(d/f'{n:02d}_stderr.log').read_text())
    target=read(d/'target/case_1/controller_result.json')
    assert target['partial_calls']>=1 and target['target_reached']>=1 and target['requeues']>=1 and target['terminal_calls']>=1 and target['certified']
    requests=[json.loads(s) for s in (d/'scope/terminal/round107/requests.jsonl').read_text().splitlines()]
    assert requests[0]['optimal_close_by_dominance'] and requests[1]['local_INF'] and not requests[1]['domain_start']
    assert not requests[2]['domain_start'] and requests[2]['qualified_local_bound']>requests[2]['own_global_UB']
    cross=read(d/'scope/terminal/round107/request_3/summary.json')
    assert cross['cross_request_hits']>0 and cross['remapped_rows']>0,cross
    inner=read((d if name!='final03' else OUT/'qualification/final02')/'inner_deadline/inner/deadline.json')
    assert inner['actual_oracle_Optimize']>0 and inner['IIS']==0 and inner['cancelled'] and inner['remaining']<.03,inner
    outer=read(d/'outer_deadline/round107/request_1/summary.json')
    assert outer['master_calls']==1 and outer['outer_cancelled'] and not read(d/'outer_deadline/deadline_outcome.json')['certified']
    totals={}
    for path in d.rglob('calls.csv'):
        for row in csv.DictReader(path.open(newline='')):
            if row['stage']=='after':totals[row['phase']]=totals.get(row['phase'],0)+1
    assert totals.get('iis',0)==0 and totals.get('core_confirm',0)==0
    write(d/'qualification.json',dict(passed=True,actual_target_controller_requeue_terminal=True,actual_outer_deadline=True,
        actual_inner_deadline=True,cross_request_FEAS_INF_and_semantic_rows=True,native_call_totals=totals,
        layer='finite actual native domains',production_handoff=False))
    write(OUT/f'qualification/identity_{name}.json',dict(source_bindings=bindings(),production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),
        fixture_PE_SHA=sha(BUILD/'Round107Tests.exe'),DLL_SHA=sha(DLL),qualification_path=d.relative_to(ROOT).as_posix(),
        plan_SHA=sha(d/'plan.json'),result_SHA=sha(d/'qualification.json'),native_call_totals=totals,passed=True))
    print(json.dumps(dict(passed=True,children=len(jobs),native_call_totals=totals)))
if __name__=='__main__':run(sys.argv[1])
