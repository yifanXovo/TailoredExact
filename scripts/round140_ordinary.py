"""Record disjoint document/analysis/public I/O wall costs outside timed solves."""
from round140_common import *

def main():
    label=sys.argv[1];command=sys.argv[2:]
    assert label and Path(label).name==label and command and not budget()['unclosed']
    folder=OUT/'ordinary_steps'/label;folder.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    write(folder/'launch.json',dict(UTC=utc(),command=command,cwd=str(ROOT),Optimize=0))
    failure=None;exit_code=127
    try:
        with (folder/'stdout.log').open('xb') as stdout,(folder/'stderr.log').open('xb') as stderr:
            result=subprocess.run(command,cwd=ROOT,env=environment(),stdout=stdout,stderr=stderr,timeout=1900)
            exit_code=result.returncode
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        write(folder/'receipt.json',dict(UTC=utc(),exit_code=exit_code,seconds=time.perf_counter()-tick,
            G1_seconds=0,Optimize=0,not_also_in_fee_meter=True,failure=failure))
    print(json.dumps(read(folder/'receipt.json')),flush=True);sys.exit(exit_code)

if __name__=='__main__':main()
