"""Bounded source/history intake; no old Optimize, no whole archive restore."""
from round162_common import *
import shutil, re

def setup():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'goal.md').write_bytes(Path('C:/Users/Administrator/Downloads/TailoredExact_Round162_Complete_Goal.md').read_bytes())
    protected=[]
    for tree in [Path('E:/codes/ExactEBRP'),WORK/'worktrees/paper-current',WORK/'worktrees/round160',WORK/'worktrees/round161']:
        paths=[x[3:] for x in git('status','--short','--untracked-files=no','-z',cwd=tree).decode().split('\0') if x]
        protected.append(dict(tree=str(tree),head=git('rev-parse','HEAD',cwd=tree).decode().strip(),dirty={p:sha(tree/p) for p in paths if (tree/p).is_file()}))
    write(OUT/'infra/protected_initial.json',dict(UTC=utc(),trees=protected))
    write(OUT/'infra/intake.json',dict(UTC=utc(),base=BASE,branch=git('branch','--show-current').decode().strip(),
        main='b2b940c1e517a72e226ec60fc49ff19651737632',R161_PR=223,open=True,draft=True,
        AGENTS='No applicable ancestor or tracked AGENTS.md',policy_SHA256=sha(ROOT/'WORKSPACE_POLICY.md'),
        active_solver_processes_at_entry=0,capacity=TOTAL,free_bytes=shutil.disk_usage(WORK).free,
        original_goal_SHA256=sha(OUT/'goal.md'),old_producers=0))
    inputs=read(PRIOR/'input_manifest.json')
    for role in inputs['roles']:
        name=role['role']; dest=OUT/'inputs'/name;dest.mkdir(parents=True,exist_ok=True)
        for member in ('instance.txt','parent.txt','source.json'):
            shutil.copyfile(PRIOR/'inputs'/name/member,dest/member)
        assert sha(dest/'instance.txt')==role['input_SHA']
    write(OUT/'input_manifest.json',dict(roles=inputs['roles'],R161_fixed_science='fcd83fdf4d8980cbfdd6a860d5fe44fb7aa98158',
        R161_carrier_SHA256=sha(PRIOR/'artifacts/new_evidence.zip'),offline_development_only=True,old_producer_reruns=0))
    recent={}
    for name in ['goal.md','final_report.md','decision.json','reports/bridge.json','reports/LP_product_diagnostics.json',
                 'reports/envelope_diagnostic.json','cost_report.json','measured_manifest.json','measured_manifest_RNP.json']:
        p=PRIOR/name;raw=p.read_bytes();recent[name]=dict(SHA256=sha(p),bytes=len(raw))
    write(OUT/'history_readback.json',dict(fixed_commit=BASE,recent=recent,
        R161_cost=read(PRIOR/'cost_report.json')['G1_seconds'],R161_decision=read(PRIOR/'decision.json'),
        R161_bridge=read(PRIOR/'reports/bridge.json'),R161_product=read(PRIOR/'reports/LP_product_diagnostics.json'),
        R161_envelope=read(PRIOR/'reports/envelope_diagnostic.json')))
    paths=['results/gf_passive_threshold_conflicts_round62/final_report.md',
        'results/unified_exact_round132/final_report.md','results/unified_exact_round133/final_report.md',
        'results/unified_exact_round138/mathematical_analysis.md','results/unified_exact_round138/final_report.md',
        'results/unified_exact_round139/final_report.md','results/unified_exact_round143/mathematical_analysis.md',
        'results/unified_exact_round144/final_report.md','results/unified_exact_round145/final_report.md',
        'results/unified_exact_round153/final_report.md','results/unified_exact_round156/final_report.md',
        'results/unified_exact_round159/final_report.md','results/unified_exact_round160/final_report.md']
    refs=[]
    for path in paths:
        raw=git('show',BASE+':'+path)
        dest=OUT/'engineering/history'/Path(path).parent.name/Path(path).name
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        refs.append(dict(commit=BASE,path=path,SHA256=sha(dest),bytes=len(raw)))
    write(OUT/'history_fixed_references.json',dict(files=refs,old_Optimize=0,whole_archive_extractions=0))
    c=PRIOR/'runs/R-X35-S-T2_OLD_LP_v1/actual_columns.jsonl'
    counts={}
    for row in map(json.loads,c.read_text().splitlines()):
        family=re.sub(r'_[0-9]+','_#',row['name']);counts[family]=counts.get(family,0)+1
    write(OUT/'engineering/old_column_families.json',counts)
    print(json.dumps(dict(setup='PASS',families=counts,protected_dirty=sum(len(p['dirty']) for p in protected))))

if __name__=='__main__': setup()
