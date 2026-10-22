"""Initialize the finite R130 protocol without H, Optimize or data generation."""
from pathlib import Path
import datetime, hashlib, json, shutil, subprocess, os

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round130'
WORK=Path('E:/codes/ExactEBRP-work')

def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def run():
    assert not (OUT/'argv_freeze.json').exists()
    OUT.mkdir(parents=True,exist_ok=True)
    src=(ROOT/'scripts/round129_common.py').read_text()
    src=src.replace('R129 finite','R130 finite').replace("worktrees/round127'","worktrees/round129'")
    src=src.replace("unified_exact_round129'","unified_exact_round130'").replace("temp/round129'","temp/round130'").replace("evidence/round129'","evidence/round130'")
    src=src.replace("BUILD=WORK/'build-cache/round128'","BUILD=WORK/'build-cache/round130'")
    src=src.replace("BASE='cc70757304a2019d95f0f934aa5520d0caa946c6'","BASE='ce70acd2fb3fa6b7d0033f0cbc74c2aab3113d73'")
    src=src.replace("E2=BUILD/'ExactEBRP.exe'","E2=WORK/'build-cache/round128/ExactEBRP.exe'\nE3=BUILD/'ExactEBRP.exe'")
    src=src.replace('QUAL_LIMIT=1800','QUAL_LIMIT=3600')
    src=src[:src.index('EXPORTER=BUILD/')]+'''EXPORTER=BUILD/"Round130ExportE3.exe"
E2_EXPORTER=WORK/"build-cache/round128/Round128ExportE2.exe"

def identity():
    assert sha(E2)==E2_SHA and sha(DLL)==DLL_SHA
    seal=read(OUT/"E3_frozen.json")
    assert sha(E3)==seal['PE_SHA'] and sha(EXPORTER)==seal['exporter_SHA']
    assert source_bindings()==seal['source_bindings']
    return dict(PE=str(E3),PE_SHA=seal['PE_SHA'],DLL=str(DLL),DLL_SHA=DLL_SHA,
        predecessor_PE_SHA=E2_SHA,exporter=str(EXPORTER),exporter_SHA=seal['exporter_SHA'])
'''
    (ROOT/'scripts/round130_common.py').write_text(src,encoding='utf-8')
    build=(ROOT/'scripts/round128_build.py').read_text().replace('from round128_common import *','from round130_common import *')
    build=build.replace("'-o',E2]","'-o',E3]").replace("OUT/'E2_build.json'","OUT/'E3_build.json'").replace('PE=str(E2),PE_SHA=sha(E2)','PE=str(E3),PE_SHA=sha(E3)').replace('PE_SHA=sha(E2),budget','PE_SHA=sha(E3),budget')
    (ROOT/'scripts/round130_build.py').write_text(build,encoding='utf-8')
    shutil.copyfile(ROOT/'scripts/round128_export.cpp',ROOT/'scripts/round130_export.cpp')
    init0=json.loads((ROOT/'results/unified_exact_round128/initialization.json').read_text())
    initial=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),base='ce70acd2fb3fa6b7d0033f0cbc74c2aab3113d73',
      remote='https://github.com/yifanXovo/TailoredExact.git',PR191=dict(state='open',draft=True,merged=False,head='ce70acd2fb3fa6b7d0033f0cbc74c2aab3113d73'),
      applicable_AGENTS=[],main_HEAD='8dc274eb34ee6d8a575f0b94b57ef04476efc0f1',main_dirty_preserved=True,initially_active_solvers=[],
      E2_SHA=sha(WORK/'build-cache/round128/ExactEBRP.exe'),DLL_SHA=sha(Path('D:/gurobi1302/win64/bin/gurobi130.dll')),
      compiler_SHA=init0['compiler_SHA'],frozen_core_archive_SHA=init0['frozen_core_archive_SHA'],
      free_bytes=shutil.disk_usage(WORK).free,peak_increment_allowance_bytes=20*1024**3,
      preledger_outer_upper_seconds=900,preledger_explanation='Conservative nonoverlapping setup/read/remote/sparse-initialization machine allowance, including failed own sparse initialization; subsequent substantial children separately metered.',
      total_outer_limit=39600,qualification_soft=1800,qualification_limit=3600)
    if not (OUT/'initialization.json').exists():write(OUT/'initialization.json',initial)
    attachment=Path('C:/Users/Administrator/.codex/attachments/78847bfb-841a-41da-ae5d-4770c279d32e/已粘贴的文本.txt')
    shutil.copyfile(attachment,OUT/'goal.md')
    write(OUT/'initialization_failure.json',dict(stage='sparse_checkout',cause='Missing new-worktree info directory before copying sparse patterns; read-tree interrupted and own stale index.lock removed after all Git children exited',
      user_or_previous_worktree_modified=False,scientific_output_lost=False,formal_or_native_started=False,repair='Create info directory; copy existing sparse pattern; read-tree completes; preserve any partial own checkout pending bounded cleanup'))
    old=json.loads((ROOT/'results/unified_exact_round129/input_manifest.json').read_text())
    ids=['UC-B20-B','UC-C20-U','UC-B30-S']
    roles=[next(p for p in old['roles'] if p['id']==k) for k in ids]
    for p in roles:
        original=p['input_path']
        source=WORK/'worktrees/round129'/original
        assert sha(source)==p['input_sha256']
        destination=OUT/'inputs'/source.name
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,destination)
        assert sha(destination)==p['input_sha256']
        p.update(source_input_path=original,input_path=destination.relative_to(ROOT).as_posix())
        p.update(cap_seconds=1200,panel_kind='known_role_attribution_diagnostic',prospective_new_validation=False)
    write(OUT/'input_manifest.json',dict(roles=roles,source_round=129,original_input_bytes_reused=True,no_generation=True))
    orders=[['P','PS','S2','S2R'],['S2R','S2','PS','P'],['PS','S2R','P','S2'],['S2','P','S2R','PS'],['S2','P','S2R','PS'],['PS','S2R','P','S2']]
    pairs=[['S2','P'],['PS','P'],['S2','PS'],['S2','S2R'],['S2R','PS']]
    groups=[dict(name=f'campaign/group{j+1:02d}',role=roles[j//2],seed=j%2,methods=order,pairs=pairs) for j,order in enumerate(orders)]
    write(OUT/'experiment_manifest.json',dict(round=130,base='ce70acd2fb3fa6b7d0033f0cbc74c2aab3113d73',groups=groups,pairs=pairs,
      sole_paper_method='GI-TBC (uniform pair-support implementation, MS2)',method_short_name='S2',formal_arms=24,typed_shared_comparisons=30,
      nominal_formal_seconds=28800,total_outer_limit=39600,build_qualification_limit=3600,management_reference=720,
      own_H_seed=20260626,Threads=1,MIPThreads=1,affinity_mask=4,shutdown_reserve=30,native_offset=6,hard_stop_offset=2,
      MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6,Presolve=-1,MIPFocus=0,Cuts=-1,
      max_external_failure_whole_group_recoveries=1,normal_results_retry=False,extra_experiments_authorized=False,
      selected_MS2_is_fixed=True,repository_default_changed=False,material_difference='slower-faster >= max(10,0.10*faster)',
      methods=dict(P='cold original compact',PS='independently paid complete H and full original-compact Start',S2='E2 ms2 unchanged',S2R='s2-root inclusive pair-support root LP + MIP')))
    (OUT/'RESUME.md').write_text('Round130 initialized; no formal arm started. Check live processes, fees and E3 seal before continuing. Do not overwrite any sealed producer.\n',encoding='utf-8')
    print('R130 protocol initialized; no Optimize or generated input')
if __name__=='__main__':run()
