"""Measure a bounded ordinary child outside timed experiments."""
from round141_common import *
import round140_common as clocks

def main():
    assert not budget()['unclosed'], 'ordinary build/IO/PDF must wait for Native'
    assert not os.environ.get('ROUND141_ORDINARY_PARENT_LABEL'), 'no nested ordinary clock'
    assert all((p.parent/'receipt.json').exists() for p in (OUT/'ordinary_steps').glob('*/launch.json')), 'inspect pending ordinary process before continuing'
    label=sys.argv[1];timeout=float(sys.argv[2]);assert sys.argv[3]=='--'
    assert label and label not in ('.','..') and Path(label).name==label and 0<timeout<=1900
    folder=OUT/'ordinary_steps'/label;folder.mkdir(parents=True,exist_ok=False)
    command=list(map(str,sys.argv[4:]));assert command
    write(folder/'launch.json',dict(UTC=utc(),command=command,timeout=timeout,experimental=False))
    tick=time.perf_counter();error=None;child=None;identity=None;code=127
    with (folder/'stdout.txt').open('wb') as out,(folder/'stderr.txt').open('wb') as err:
        try:
            env=environment();env['ROUND141_ORDINARY_PARENT_LABEL']=label
            child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=out,stderr=err)
            birth=clocks.process_birth(child.pid)
            if birth:
                identity=dict(pid=child.pid,parent_pid=os.getpid(),command=command,**birth)
                write(folder/'PID.json',identity)
            elif child.poll() is None:
                raise RuntimeError('ordinary child birth unavailable; preserve pending process')
            child.wait(timeout=timeout);code=child.returncode
        except subprocess.TimeoutExpired:
            code=124;error='ordinary child timeout'
            assert identity is not None
            clocks._kill_owned_tree(child,identity,folder)
        except BaseException as failure:
            error=dict(type=type(failure).__name__,message=str(failure))
            if child is not None and child.poll() is None:
                if identity is None:
                    write(folder/'pending_exit.json',dict(UTC=utc(),PID=child.pid,error=error,
                        no_automatic_retry=True));raise
                clocks._kill_owned_tree(child,identity,folder)
    exited=child is None or child.poll() is not None
    assert exited
    write(folder/'receipt.json',dict(UTC=utc(),exit_code=code,seconds=time.perf_counter()-tick,
        Optimize=0,experimental=False,error=error,exit_observed=exited,
        owned_tree_termination_on_timeout=True))
    print(json.dumps(read(folder/'receipt.json')))
    sys.exit(code)

if __name__=='__main__':main()
