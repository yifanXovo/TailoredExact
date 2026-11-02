"""Read-only entry inventory, fixed history bindings and goal capture."""
from round148_common import *


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    goal = Path('C:/Users/Administrator/Downloads/TailoredExact_Round148_Complete_Goal.md')
    (OUT/'goal.md').write_bytes(goal.read_bytes())
    original = Path('E:/codes/ExactEBRP')
    status = git('status', '--porcelain=v1', '--untracked-files=no', cwd=original).decode()
    (OUT/'protected_original_tracked_status.txt').write_text(status, encoding='utf-8')
    modified = git('diff', '--name-only', 'HEAD', cwd=original).decode().splitlines()
    untracked = git('ls-files', '--others', '--exclude-standard')
    write(OUT/'start_receipt.json', dict(UTC=utc(), goal_SHA=sha(goal),
        branch=git('branch', '--show-current').decode().strip(), base=BASE,
        main=git('rev-parse', 'origin/main').decode().strip(), main_contains_R147=False,
        applicable_AGENTS=[], workspace_policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md'),
        protected_modified_file_hashes={p: sha(original/p) for p in modified if (original/p).is_file()},
        active_initial_tracked_status=git('status', '--porcelain=v1', '--untracked-files=no').decode(),
        active_untracked_inventory=dict(count=len(untracked.splitlines()),
            SHA256=hashlib.sha256(untracked).hexdigest(),
            first_paths=untracked.decode().splitlines()[:12],
            policy='Read-only inventory; old raw and untracked user paths retained'),
        production_PE=str(WORK/'build-cache/round146/ExactEBRP.exe'),
        production_PE_SHA=sha(WORK/'build-cache/round146/ExactEBRP.exe'),
        DLL=str(DLL), DLL_SHA=sha(DLL), new_experiment_outer_budget=18000,
        process_preflight='No existing ExactEBRP/python/cmake/ninja/MSBuild process at entry',
        review_attachment_available=False, regenerate_screen_from_fixed_R146=True))
    archive = ROOT/'results/unified_exact_round146/artifacts/diagnostics_and_failures.zip'
    assert sha(archive) == 'ab7bd4e2139c403623f1a82558c0d6ab0ce25fbb524947338b7f8c910cc66a6b'
    bindings = []
    import gzip, zipfile
    with zipfile.ZipFile(archive) as z:
        for role, carrier in ROLES:
            folder = ROOT/'results/unified_exact_round146/LP'/f'{role}_{carrier}_GD'
            old = read(folder/'result.json')
            assert sha(folder/'model.mps') == old['model_SHA']
            files = []
            for name in ('compiled_rows.json', 'solution.json.gz', 'model.mps', 'result.json'):
                member = (folder/name).relative_to(ROOT).as_posix()
                data = z.read(member)
                assert hashlib.sha256(data).hexdigest() == sha(folder/name)
                files.append(dict(path=member, SHA256=sha(folder/name), archive_member=member))
            bindings.append(dict(role=role, carrier=carrier, fixed_science=SCIENCE146,
                archive=str(archive.relative_to(ROOT)), archive_SHA=sha(archive), files=files,
                old_L=old['L'], old_g=old['g'], new_baseline_Optimize=0))
    write(OUT/'reuse_index.json', dict(five_models_three_instances=True, domains=bindings,
        historical_fees_recharged=False, review_attachment_missing=True))
    print(json.dumps(dict(prepared=True, fixed_domains=len(bindings), Optimize=0, Native_load=0)))


if __name__ == '__main__':
    main()
