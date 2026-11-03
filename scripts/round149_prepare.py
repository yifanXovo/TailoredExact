"""Capture authorized scope, immutable input reuse and protected workspace bytes."""
import zipfile
from round149_common import *


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    goal = Path('C:/Users/Administrator/Downloads/TailoredExact_Round149_Complete_Goal.md')
    (OUT/'goal.md').write_bytes(goal.read_bytes())
    original = Path('E:/codes/ExactEBRP')
    status = git('status', '--porcelain=v1', '--untracked-files=no', cwd=original).decode()
    (OUT/'protected_original_tracked_status.txt').write_text(status, encoding='utf-8')
    changed = git('diff', '--name-only', 'HEAD', cwd=original).decode().splitlines()
    untracked = git('ls-files', '--others', '--exclude-standard')
    (OUT/'preexisting_untracked_paths.txt').write_bytes(untracked)
    write(OUT/'start_receipt.json', dict(UTC=utc(), goal_SHA=sha(goal), base=BASE,
        branch=git('branch', '--show-current').decode().strip(),
        actual_main=git('rev-parse', 'origin/main').decode().strip(),
        main_contains_R148=False, PR_base='codex/round148-shared-denominator-gd',
        predecessor_PR=dict(number=210, open=True, Draft=True, head=BASE),
        applicable_AGENTS=[], workspace_policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md'),
        protected_modified_file_hashes={p:sha(original/p) for p in changed if (original/p).is_file()},
        active_initial_tracked_status=git('status', '--porcelain=v1', '--untracked-files=no').decode(),
        old_untracked_count=len(untracked.splitlines()), old_untracked_SHA=sha(OUT/'preexisting_untracked_paths.txt'),
        reusable_PE=str(WORK/'build-cache/round148/ExactEBRP.exe'),
        reusable_PE_SHA=sha(WORK/'build-cache/round148/ExactEBRP.exe'),
        DLL=str(DLL), DLL_SHA=sha(DLL), new_outer_ceiling_seconds=18000,
        Seed=0, Threads=1, H_seed=20260626, serial=True,
        entry_solver_processes=0, review_attachments_available=False,
        policy='All new build/raw/temp/restore in ExactEBRP-work; preserve original and old history'))
    archive = ROOT/'results/unified_exact_round146/artifacts/diagnostics_and_failures.zip'
    assert sha(archive) == 'ab7bd4e2139c403623f1a82558c0d6ab0ce25fbb524947338b7f8c910cc66a6b'
    records=[]
    with zipfile.ZipFile(archive) as z:
        for role in ROLES:
            folder=ROOT/'results/unified_exact_round146/LP'/f'{role}_base_GD'
            result=read(folder/'result.json');assert sha(folder/'model.mps')==result['model_SHA']
            files=[]
            for name in ['model.mps','compiled_rows.json','solution.json.gz','result.json']:
                path=folder/name; member=path.relative_to(ROOT).as_posix()
                assert hashlib.sha256(z.read(member)).hexdigest()==sha(path)
                files.append(dict(path=member,SHA256=sha(path),archive_member=member))
            records.append(dict(role=role,carrier='base',old_L=result['L'],files=files))
    write(OUT/'reuse_index.json',dict(fixed_science=SCIENCE146,archive=str(archive.relative_to(ROOT)),
        archive_SHA=sha(archive),domains=records,baseline_Optimize_new=0,old_fees_recharged=False))
    print(json.dumps(dict(prepared=True,matched_domains=len(records),Optimize=0,Native_load=0)))


if __name__=='__main__':main()
