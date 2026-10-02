"""Explicit finite stage1 actions; never retries existing labels."""
import sys,subprocess
from round99_common import *
PY=BUILD.parents[0]/'round88-ot/venv/Scripts/python.exe'
# Native Python is an existing installation, not the performance binary.
PY=ROOT/'build/research/round88-ot/venv/Scripts/python.exe'
def exports():
    roles=read(OUT/'development_inputs.json')['roles'];assert len(roles)==3
    for p in roles:
        command=[BUILD/'Round99ModelExport.exe',ROOT/p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],
            p['diagnostic_gamma_L'],p['diagnostic_gamma_U'],p['diagnostic_cutoff'],OUT/'exports'/p['id']]
        subprocess.run(list(map(str,command)),cwd=ROOT,env=env(),check=True,timeout=60)
    print('finite export children=3, optimizer_calls=0')
if __name__=='__main__':
    a=sys.argv[1]
    if a=='exports':exports()
    elif a=='prepare':
        subprocess.run([str(Path('D:/msys64/ucrt64/bin/python.exe')),str(ROOT/'scripts/round99_inputs.py')],cwd=ROOT,check=True)
        receipt('micro_export01',[BUILD/'Round99DiscreteTests.exe',OUT/'micro_models01'],cap=60)
        receipt('factor_exports01',[Path('D:/msys64/ucrt64/bin/python.exe'),__file__,'exports'],kind='qualification',cap=180,optimizer_calls=0)
    elif a=='micro':receipt('micro02',[PY,ROOT/'scripts/round99_qualification.py','micro02',OUT/'micro_models01'],kind='qualification',cap=120,optimizer_calls=10)
    elif a=='lp':
        for p in read(OUT/'development_inputs.json')['roles']:
            receipt('lp_'+p['id']+'01',[PY,ROOT/'scripts/round99_factor_diagnostic.py',p['id'],'lp_'+p['id']+'01'],kind='qualification',cap=300,optimizer_calls=4)
    else:raise ValueError(a)
