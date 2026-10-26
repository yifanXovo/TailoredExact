"""Two real pre-MIP persistence faults plus unchanged-reader rejection.

Runs only in a separately billed idle qualification window. Files are
exclusive test destinations; no permissions or production inputs change.
"""
from round103_common import *
import round86_native_evidence as nej
if __name__=='__main__':
    from round100_idle import ensure_idle
    ensure_idle();label=sys.argv[1];directory=OUT/'diagnostics'/label;directory.mkdir(parents=True,exist_ok=False)
    identity=read(OUT/'native01/identity.json');template=identity['launches'][1];records=[]
    for name,suffix in [('calls_open','.calls.jsonl'),('rows_write','.rows.json')]:
        dest=directory/name;dest.mkdir();old=template['destination'];command=[s.replace(old,str(dest)) for s in template['command']]
        collision=dest/'external/native_logs'/('L0_c6_1_child_disjunction_target_mip.gurobi.log.round103'+suffix)
        collision.parent.mkdir(parents=True);collision.write_text('exclusive intentional fault marker\n')
        write(dest/'launch.json',dict(command=command,question='actual preparation persistence failure invalidates durable stream',
            collision=str(collision),binary_sha256=sha(BUILD/'ExactEBRP.exe')))
        tick=time.perf_counter()
        with (dest/'stdout.log').open('x') as so,(dest/'stderr.log').open('x') as se:
            child=subprocess.Popen(command,cwd=ROOT,env=env(),stdout=so,stderr=se)
            write(dest/'process.json',dict(pid=child.pid))
            try:code=child.wait(timeout=120)
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],stdout=se,stderr=se);child.wait();raise
        write(dest/'completion.json',dict(exit_code=code,outer_seconds=time.perf_counter()-tick))
        observations=[nej.receipt(p,1,120) for p in sorted((dest/'journal').glob('event_*.commit'),key=lambda p:int(p.stem.split('_')[1]))]
        failures=[r['payload'] for r in observations if r['payload']['kind']=='failure'];assert code!=0 and len(failures)==1
        assert 'round103_preparation:' in failures[0]['reason']
        try:nej.audit(ROOT,template['panel'],observations,sha(BUILD/'ExactEBRP.exe'))
        except AssertionError as e:assert e.args[0][0]=='journal_failure'
        else:raise AssertionError('failed root preparation stream accepted')
        calls=[r for r in observations if r['payload']['kind']=='call'];assert all(not r['payload']['native_preconditions'] for r in calls)
        auxiliary=[]
        for path in (dest/'external/native_logs').glob('*.round103.calls.jsonl'):
            if path==collision:continue
            auxiliary.extend(json.loads(line) for line in path.read_text().splitlines())
        records.append(dict(case=name,failure=failures[0]['reason'],reader_rejected=True,native_MIP_Optimize=0,
            auxiliary_Optimize_calls=sum(r['event']=='Optimize_begin' for r in auxiliary),DP_calls=sum(r['event']=='DP_begin' for r in auxiliary),
            required_LP_Optimize=len(calls),exit_code=code,scope='real production process; deliberate destination collision, no storage-loss or native B&B failure claim'))
    write(directory/'summary.json',dict(passed=True,records=records,physical_solver_children=2,
        no_native_BB=True,scope='two actual preparation faults; whole process and reader included in parent receipt'))
    print(json.dumps(dict(passed=True,cases=records)))
