"""One-time setup; only reads old trees and creates Round134-owned files."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round134'
OUT.mkdir(parents=True,exist_ok=True)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
if __name__=='__main__':
    shutil.copyfile('C:/Users/Administrator/Desktop/TailoredExact_Round134_Complete_Goal.md',OUT/'goal.md')
    (OUT/'.gitignore').write_text('campaign/\nfees/\ncost_segments/\nqualification/references/\n',encoding='utf-8')
    source=(ROOT/'scripts/round133_common.py').read_text(encoding='utf-8-sig')
    source=source.replace('round133','round134').replace('Round133','Round134').replace('ROUND133','ROUND134')
    source=source.replace("BASE = '1ae14721e800d7c601adc1e7e42d5dfa89e48fbb'","BASE = '39043b15b3cceae2cab14a3fbaec39e2b16339ce'")
    source=source.replace("ORIGINAL_E3 = WORK / 'build-cache/round130/ExactEBRP.exe'","ORIGINAL_E3 = WORK / 'build-cache/round133/ExactEBRP.exe'")
    source=source.replace("ORIGINAL_PE_SHA = '2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c'","ORIGINAL_PE_SHA = 'edfd4e2839afbe8571f00860402ae7596f702d4b494c1da8af0043acabf209ce'")
    source=source.replace('LIMITS = dict(C=7200., D=18000., E=1800., D3=7200., repair=5400.)','LIMITS = dict(B=57600., C=57600., D=57600., E=57600., repair=57600.)')
    source=source.replace('39600','57600')
    (ROOT/'scripts/round134_common.py').write_text(source,encoding='utf-8')
    dirty=['results/gf_compact_bc_round/handling_convention_test/handling_convention.json',
           'results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv',
           'results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json']
    assets=['E:/codes/ExactEBRP-work/build-cache/round133/ExactEBRP.exe',
            'E:/codes/ExactEBRP-work/build-cache/round130/ExactEBRP.exe',
            'E:/codes/ExactEBRP-work/build-cache/round132/Round132Research.exe',
            'D:/gurobi1302/win64/bin/gurobi130.dll']
    write(OUT/'baseline.json',dict(base='39043b15b3cceae2cab14a3fbaec39e2b16339ce',
        no_AGENTS_found=True,healthy_native_processes_at_start=0,
        original_tree_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd='E:/codes/ExactEBRP').decode().strip(),
        protected_dirty={n:digest(Path('E:/codes/ExactEBRP')/n) for n in dirty},
        protected_assets={n:digest(n) for n in assets},
        goal_SHA256=digest(OUT/'goal.md'),new_compute_limit_seconds=57600,
        budget_allocations=dict(B=3600,C=42720,D=3600,E=3600,repair=4080),
        category_limits_are_fungible_total_limit_hard=True,
        workspace='E:/codes/ExactEBRP-work/worktrees/round134',
        old_worktrees_and_dirty_contents_untouched=True))
    print('Round134 setup complete; no Optimize')
