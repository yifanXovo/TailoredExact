"""One declared finite zero-Optimize batch: micro + three root exports."""
import subprocess
from round99_common import *
from round99_idle import ensure_idle
if __name__=='__main__':
    ensure_idle()
    commands=[[BUILD/'Round99DiscreteTests.exe',OUT/'linked_micro_models01']]
    for p in read(OUT/'development_inputs.json')['roles']:
        commands.append([BUILD/'Round99ModelExport.exe',ROOT/p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],
            p['diagnostic_gamma_L'],p['diagnostic_gamma_U'],p['diagnostic_cutoff'],OUT/'linked_exports01'/p['id']])
    assert len(commands)==4
    for command in commands:subprocess.run(list(map(str,command)),cwd=ROOT,env=env(),check=True,timeout=60)
    print('finite4 zero-Optimize export children, optimizer_calls=0')
