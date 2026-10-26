"""Round135-owned setup only; no optimizer or old-tree mutation."""
from pathlib import Path
import hashlib, json, shutil, subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round135'
WORK=Path('E:/codes/ExactEBRP-work')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    OUT.mkdir(parents=True,exist_ok=False)
    shutil.copyfile('C:/Users/Administrator/Desktop/TailoredExact_Round135_Complete_Goal.md',OUT/'goal.md')
    (OUT/'.gitignore').write_text('campaign/\nfees/\ncost_segments/\nqualification/references/\n',encoding='utf-8')
    code=(ROOT/'scripts/round134_common.py').read_text(encoding='utf-8-sig')
    code=code.replace('round134','round135').replace('Round134','Round135').replace('ROUND134','ROUND135')
    code=code.replace("BASE = '39043b15b3cceae2cab14a3fbaec39e2b16339ce'","BASE = 'd3353749e6933e6685c7f0d92d153d0641816bcb'")
    code=code.replace('57600','28800')
    (ROOT/'scripts/round135_common.py').write_text(code,encoding='utf-8')
    code=(ROOT/'scripts/round134_read.py').read_text(encoding='utf-8-sig')
    code=code.replace('from round134_common import *','from round135_common import *').replace('round134_endpoint.json','round135_endpoint.json')
    (ROOT/'scripts/round135_read.py').write_text(code,encoding='utf-8')
    original=ROOT/'results/unified_exact_round134/baseline.json'
    old=json.loads(original.read_text(encoding='utf-8-sig'))
    dirty={n:sha(Path('E:/codes/ExactEBRP')/n) for n in old['protected_dirty']}
    assets={n:sha(n) for n in old['protected_assets']}
    assets[str(WORK/'build-cache/round134/ExactEBRP.exe')]=sha(WORK/'build-cache/round134/ExactEBRP.exe')
    assert dirty==old['protected_dirty'] and all(assets[n]==v for n,v in old['protected_assets'].items())
    write(OUT/'baseline.json',dict(base='d3353749e6933e6685c7f0d92d153d0641816bcb',
        PR=196,no_AGENTS_found=True,initial_healthy_native_processes=0,
        protected_dirty=dirty,protected_assets=assets,goal_SHA256=sha(OUT/'goal.md'),
        new_compute_limit_seconds=28800,budget_allocations=dict(BC=3600,D=23520,repair=1680),
        stage1=dict(arms=10,cap_sum_seconds=8760),stage2=dict(arms=22,cap_sum_seconds=14760),
        workspace=str(ROOT),original_tree_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd='E:/codes/ExactEBRP').decode().strip(),
        old_trees_raw_failures_user_content_preserved=True))
    write(OUT/'infra/external_costs.json',dict(processes=[]))
    write(OUT/'RESUME.json',dict(state='IMPLEMENTATION_AND_QUALIFICATION',goal_active=True,
        next='build and default-off matrix/AP-only comparison; two incremental LPs; freeze staged campaign',
        no_production_default_change=True,no_automatic_rerun=True))
    print('Round135 setup; old protected bytes match; Optimize=0')
if __name__=='__main__':main()
