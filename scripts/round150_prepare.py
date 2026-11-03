"""Pin authorized scope and verify existing carriers without Optimize."""
import zipfile
from round150_common import *

PROTECTED = ['scripts/paper_s2.py', 'scripts/paper_s2_gd_only.py',
             'config/gi_tbc_round137.json', 'config/gi_tbc_gd_round147.json']


def main():
    tick = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=False)
    goal = Path('C:/Users/Administrator/Downloads/TailoredExact_Round150_Complete_Goal.md')
    (OUT/'goal.md').write_bytes(goal.read_bytes())
    original = Path('E:/codes/ExactEBRP')
    dirty = git('diff', '--name-only', 'HEAD', cwd=original).decode().splitlines()
    untracked = git('ls-files', '--others', '--exclude-standard')
    private = TEMP/'preexisting_untracked_paths.txt'
    private.parent.mkdir(parents=True, exist_ok=True)
    private.write_bytes(untracked)
    pe = WORK/'build-cache/round149/ExactEBRP.exe'
    manifest = read(ROOT/'results/unified_exact_round149/candidate_manifest.json')
    assert manifest['source_commit'] == SOURCE
    assert sha(pe) == manifest['production_PE_SHA'] == '373efa9a596aaf02fb332685515fcfe88df1b169cbe53b295ab6027140620295'
    assert sha(DLL) == DLL_SHA
    for name, digest in manifest['source_hashes'].items():
        assert sha(ROOT/name) == digest, name
    candidate = {k: manifest[k] for k in ['source_commit', 'source_hashes', 'production_PE',
                 'production_PE_SHA', 'research_PE', 'research_PE_SHA', 'DLL', 'DLL_SHA']}
    candidate.update(schema='round150-reused-r149-pe-v1', base=BASE, new_build=False,
        inherited_manifest_SHA=sha(ROOT/'results/unified_exact_round149/candidate_manifest.json'),
        source_PE_build_fixed_science=SCIENCE149,
        methods=dict(B='R137 GI-TBC; GD off; PF off', D='B plus standalone R147 GD; PF off'),
        method_definition_science=dict(B=SCIENCE137, D='a0673b683c645d35de829fa101a55cc9fc4774c7'),
        wrapper='scripts/round150_campaign.py', original_stable_entries_unchanged=True,
        source_build_metadata_reused_not_new_build=True)
    write(OUT/'candidate_manifest.json', candidate)
    write(OUT/'start_receipt.json', dict(UTC=utc(), goal_SHA=sha(goal), base=BASE,
        branch=git('branch', '--show-current').decode().strip(),
        actual_main=git('rev-parse', 'origin/main').decode().strip(),
        main_contains_R149=False, PR_base='codex/round149-penalty-product-feedback',
        predecessor_PR=dict(number=211, state='open', draft=True, merged=False, head=BASE),
        applicable_AGENTS=[], workspace_policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md'),
        protected_original_status=git('status', '--porcelain=v1', '--untracked-files=no', cwd=original).decode(),
        protected_modified_file_hashes={p:sha(original/p) for p in dirty if (original/p).is_file()},
        active_initial_tracked_status=git('status', '--porcelain=v1', '--untracked-files=no').decode(),
        protected_entry_bytes={p:sha(ROOT/p) for p in PROTECTED},
        old_untracked_count=len(untracked.splitlines()), old_untracked_SHA=sha(private),
        local_only_old_untracked_inventory=str(private),
        reusable_PE=str(pe), PE_SHA=sha(pe), DLL=str(DLL), DLL_SHA=DLL_SHA,
        outer_ceiling_seconds=14400, Seed=0, Threads=1, H_seed=20260626, serial=True,
        observed_initial_solver_processes=0, review_attachments_available=False,
        cleanup_authority='Current-round reconstructible duplicates only after public recovery; zero deletion acceptable'))
    archive = ROOT/'results/unified_exact_round149/artifacts/diagnostics_qualification_failures.zip'
    assert sha(archive) == '09a128897c372e3c46c98af18418852080348c639fea03c843d22aec865b332e'
    records = []
    with zipfile.ZipFile(archive) as z:
        for role in ROLES:
            folder = ROOT/'results/unified_exact_round149/LP'/f'{role}_PF'
            old = read(folder/'result.json')
            assert sha(folder/'model.mps') == old['model_SHA']
            files = []
            for name in ['model.mps', 'result.json', 'solution.json.gz', 'arithmetic.json', 'construction.json']:
                path = folder/name
                member = path.relative_to(ROOT).as_posix()
                assert hashlib.sha256(z.read(member)).hexdigest() == sha(path)
                files.append(dict(path=member, SHA256=sha(path), bytes=path.stat().st_size))
            records.append(dict(role=role, PF_L=old['L'], D_L=old['old_L'], files=files))
    frozen = json.loads(git('show', SCIENCE137+':results/unified_exact_round137/matrix_frozen.json'))
    local = read(ROOT/'results/unified_exact_round137/matrix_frozen.json')
    assert frozen == local
    inputs = []
    for role, digest in [('N-C20-U', '93b93b6abed55cf97f8ee21ddd85fb8501554b8e4c35bb997ae75782f1f98e16'),
                         ('N-B35-S', '80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98')]:
        path = ROOT/'results/unified_exact_round137/inputs'/f'{role}.txt'
        assert sha(path) == digest
        assert hashlib.sha256(git('show', SCIENCE137+':'+path.relative_to(ROOT).as_posix())).hexdigest() == digest
        inputs.append(dict(role=role, path=path.relative_to(ROOT).as_posix(), SHA256=digest,
                           known=True, exposed=True, used_in_GD_selection=False))
    write(OUT/'reuse_index.json', dict(fixed_science=SCIENCE149, archive=archive.relative_to(ROOT).as_posix(),
        archive_SHA=sha(archive), domains=records, inputs=inputs, input_fixed_science=SCIENCE137,
        baseline_Optimize_new=0, old_fees_recharged=False, no_old_producer_loaded=True,
        seconds=time.perf_counter()-tick))
    print(json.dumps(dict(prepared=True, domains=3, inputs=2, Optimize=0, Native_load=0,
                          seconds=time.perf_counter()-tick)))


if __name__ == '__main__':
    main()
