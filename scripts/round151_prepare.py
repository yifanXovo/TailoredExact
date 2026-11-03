"""Pin the actual workspace and restore only fixed saved B-root members; no Native."""
import zipfile
from round151_common import *
PROTECTED=['scripts/paper_s2.py','scripts/paper_s2_gd_only.py','scripts/paper_s2_penalty_feedback.py',
    'config/gi_tbc_round137.json','config/gi_tbc_gd_round147.json','config/gi_tbc_penalty_feedback_round149.json']
def main():
    OUT.mkdir(parents=True,exist_ok=False)
    goal=Path('C:/Users/Administrator/Downloads/TailoredExact_Round151_Complete_Goal.md')
    (OUT/'goal.md').write_bytes(goal.read_bytes())
    original=Path('E:/codes/ExactEBRP')
    dirty=git('diff','--name-only','HEAD',cwd=original).decode().splitlines()
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert git('rev-parse','origin/main').decode().strip()=='b2b940c1e517a72e226ec60fc49ff19651737632'
    processes=subprocess.check_output(['powershell','-NoProfile','-Command',
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'ExactEBRP|gurobi|g\\+\\+|cc1plus' } | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"],text=True).strip()
    assert not processes,processes
    write(OUT/'start_receipt.json',dict(UTC=utc(),goal_SHA=sha(goal),base=BASE,
        branch=git('branch','--show-current').decode().strip(),actual_main=git('rev-parse','origin/main').decode().strip(),
        PR_base='codex/round150-gd-confirmation-conditional-feedback',main_contains_R150=False,
        predecessor_PR=dict(number=212,state='open',draft=True,merged=False,head=BASE),
        workspace_policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md'),applicable_AGENTS=[],
        protected_original_status=git('status','--porcelain=v1','--untracked-files=no',cwd=original).decode(),
        protected_modified_file_hashes={p:sha(original/p) for p in dirty if (original/p).is_file()},
        protected_entry_bytes={p:sha(ROOT/p) for p in PROTECTED},observed_initial_solver_processes=0,
        outer_ceiling_seconds=14400,Seed=0,Threads=1,H_seed=20260626,serial=True,
        attachments_available=False,attachments_fallback='Fixed R150 science/member hashes and goal formulas',
        cleanup_authority='Only completed current-round reconstructible duplicates after public recovery; zero deletion acceptable'))
    records=[]
    for position,role,digest in [(3,'N-B35-S','952018137b3e8c4cd5cd53f9bf2230885fc4428810b90810fffdda5fa71fd5f1'),
                              (1,'N-C20-U','5abb5c3111ed7388b4c4da163e78c8e77edb7ce884480aa00909d4aa119c12dd')]:
        archive=ROOT/'results/unified_exact_round150/artifacts'/f'campaign_confirmation_{position:03}.zip'
        assert sha(archive)==digest
        target=WORK/'restore/round151-inherited'/role
        prefix=f'results/unified_exact_round150/campaign_confirmation/{position:03}/raw/R150_{position:03}_{role}_S0_B/'
        with zipfile.ZipFile(archive) as z:
            names=[n for n in z.namelist() if n.startswith(prefix) and (n.endswith('L0_epoch_0_generation_1.lp') or n.endswith('observations.json') or n.endswith('L0_lp.gurobi.log'))]
            assert len(names)==3,names
            members=[]
            for member in names:
                data=z.read(member);p=target/member[len(prefix):]
                p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
                assert hashlib.sha256(data).hexdigest()==sha(ROOT/member)
                members.append(dict(member=member,SHA256=sha(p),bytes=len(data),restored=str(p)))
        records.append(dict(role=role,archive=archive.relative_to(ROOT).as_posix(),archive_SHA=digest,
            fixed_science=SCIENCE150,members=members))
    inputs=[]
    for role,digest in [('N-B35-S','80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98'),
                         ('N-C20-U','93b93b6abed55cf97f8ee21ddd85fb8501554b8e4c35bb997ae75782f1f98e16')]:
        p=ROOT/'results/unified_exact_round137/inputs'/f'{role}.txt'
        assert sha(p)==digest
        assert hashlib.sha256(git('show',SCIENCE137+':'+p.relative_to(ROOT).as_posix())).hexdigest()==digest
        inputs.append(dict(role=role,path=p.relative_to(ROOT).as_posix(),SHA256=digest))
    write(OUT/'reuse_index.json',dict(domains=records,inputs=inputs,input_fixed_science=SCIENCE137,
        baseline_Optimize_new=0,old_producer_called=False,old_fees_recharged=False))
    (OUT/'RESUME.md').write_text('Round151 active. Fixed R150 base; new independent B/GD-off cap implementation.\n'
        'Next: compiled arithmetic, saved-root C then conditional P LP, unique candidate freeze and independent admission.\n'
        'No old producer is to be reentered; inspect fee/call receipts before any resume.\n',encoding='utf-8')
    print('Prepared fixed B-root sources, protected bytes and independent budget')
def points():
    reuse=read(OUT/'reuse_index.json')
    for d in reuse['domains']:
        archive=ROOT/d['archive'];assert sha(archive)==d['archive_SHA']
        prefix=d['members'][0]['member'].split('/raw/')[0]+'/raw/'
        target=WORK/'restore/round151-inherited'/d['role']
        with zipfile.ZipFile(archive) as z:
            names=[n for n in z.namelist() if n.startswith(prefix) and (n.endswith('/external/round127_root_lp.csv') or n.endswith('/external/round127_root_lp_status.json'))]
            assert len(names)==2
            for member in names:
                p=target/'external'/Path(member).name;data=z.read(member);p.write_bytes(data)
                assert hashlib.sha256(data).hexdigest()==sha(ROOT/member)
                d['members'].append(dict(member=member,SHA256=sha(p),bytes=len(data),restored=str(p)))
    write(OUT/'reuse_index.json',reuse)
if __name__=='__main__':points() if len(sys.argv)>1 and sys.argv[1]=='points' else main()
