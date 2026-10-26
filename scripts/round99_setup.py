"""Zero-solver exclusive setup; preserve Round98 helpers unchanged."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def create(name,text):
    p=ROOT/'scripts'/name
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
common=(ROOT/'scripts/round98_common.py').read_text()
common=common.replace('unified_exact_round98','unified_exact_round99').replace('round98-state-service-v3','round99-discrete-v1')
# On failure count durable started Optimize records rather than infer zero.
common=common.replace("optimizer_calls=optimizer_calls if code==0 else None)","optimizer_calls=optimizer_calls if code==0 else None)")
create('round99_common.py',common)
build=(ROOT/'scripts/round98_build.py').read_text().replace('round98_common','round99_common')
build=build.replace("'Round98StateServiceTests','Round98ModelExport'","'Round99DiscreteTests','Round99ModelExport'")
create('round99_build.py',build)
campaign=(ROOT/'scripts/round98_campaign.py').read_text().replace('round98_common','round99_common')
campaign=campaign.replace("'round98_campaign.py','round98_common.py'","'round99_campaign.py','round99_common.py'")
campaign=campaign.replace("'R3':'research-round98-ensc-state-service-vehicle-state'","'R3':'research-round98-ensc-state-service-vehicle-state',\n            'Q-I':'research-round99-ensc-discrete-structure-q-integer',\n            'M-B':'research-round99-ensc-discrete-structure-m-binary'")
campaign=campaign.replace("['P-GRB','ENS-C','R1','R2','R3']","['P-GRB','ENS-C','R1','R2','R3','Q-I','M-B']")
campaign=campaign.replace("['R1','R2','R3']","['R1','R2','R3','Q-I','M-B']")
campaign=campaign.replace("'R3':'vehicle-state'}[arm]","'R3':'vehicle-state','Q-I':'q-integer','M-B':'m-binary'}[arm]")
create('round99_campaign.py',campaign)
batch=(ROOT/'scripts/round98_run_batch.py').read_text().replace('round98_campaign','round99_campaign')
create('round99_run_batch.py',batch)
from round99_common import OUT,write,sha
OUT.mkdir(exist_ok=True)
tracked=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
user=[p for p in tracked if p.startswith('results/gf_')]
write(OUT/'user_edit_preservation.json',{p:sha(ROOT/p) for p in user})
raw=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT)
with (OUT/'preexisting_untracked_paths.txt').open('xb') as f:f.write(raw)
write(OUT/'environment.json',dict(base='10d777d8ecf8d2aaa181f0fbe7445c266a968ef2',
    branch='codex/round99-discrete-structure-native-search',python='D:/msys64/ucrt64/bin/python.exe',
    native_python='build/research/round88-ot/venv/Scripts/python.exe',Gurobi='13.0.2',
    compiler='GCC14.2 UCRT64',build_type='',performance_serial=True,affinity=4,
    active_solver_processes=0,AGENTS_found=False,optimizer_calls=0))
print('Round99 helpers and preservation receipt created; optimizer_calls=0')
