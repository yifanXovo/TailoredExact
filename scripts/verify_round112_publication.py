"""Read-only GitHub/Git checks; never imports performance or evidence readers."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expected-head', required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    records = []

    def run(argv, label, binary=False):
        result = subprocess.run(argv, cwd=root, capture_output=True)
        (args.out / (label + '.stdout')).write_bytes(result.stdout)
        (args.out / (label + '.stderr')).write_bytes(result.stderr)
        records.append(dict(argv=argv, label=label, returncode=result.returncode))
        result.check_returncode()
        return result.stdout if binary else result.stdout.decode('utf-8')

    repo = 'yifanXovo/TailoredExact'
    base_name = 'codex/round111-seed-block-confirmation'
    head_name = 'codex/round112-paid-start-backend-attribution'
    base_oid = 'ded38c756a32a464bfa9800212da75778707d974'
    prefix = 'results/unified_exact_round112'
    try:
        local_head = run(['git', 'rev-parse', 'HEAD'], 'local_head').strip()
        assert local_head == args.expected_head
        fields = 'number,url,title,body,headRefName,headRefOid,baseRefName,isDraft,state,headRepository,headRepositoryOwner'
        pr = json.loads(run(['gh', 'pr', 'view', '174', '--repo', repo, '--json', fields], 'pr174'))
        base_pr = json.loads(run(['gh', 'pr', 'view', '173', '--repo', repo, '--json', 'url,headRefName,headRefOid,baseRefName,isDraft,state'], 'pr173'))
        assert pr['state'] == 'OPEN' and pr['isDraft'] is True
        assert pr['headRefName'] == head_name and pr['baseRefName'] == base_name
        assert pr['headRefOid'] == local_head
        assert pr['headRepository']['name'] == 'TailoredExact'
        assert pr['headRepositoryOwner']['login'] == 'yifanXovo'
        assert pr['body'].startswith('**BLOCKED. ENS-C: INCOMPLETE_ATTRIBUTION. M-B: INCOMPLETE_ATTRIBUTION.**')
        assert base_pr['state'] == 'OPEN' and base_pr['isDraft'] is True
        assert base_pr['headRefName'] == base_name and base_pr['headRefOid'] == base_oid
        refs = run(['git', 'ls-remote', 'origin', 'refs/heads/' + head_name, 'refs/heads/' + base_name], 'ls_remote')
        parsed_refs = dict(line.split()[::-1] for line in refs.splitlines())
        assert parsed_refs['refs/heads/' + head_name] == local_head
        assert parsed_refs['refs/heads/' + base_name] == base_oid
        candidate = json.loads((root / prefix / 'candidate_identity.json').read_text(encoding='utf-8'))
        source = candidate['source_bindings']
        helpers = candidate['helpers']
        assert len(source) == 206 and len(helpers) == 38
        # Every committed current-round file, all measured sources and helpers,
        # and the pinned public restorer dependency are required on GitHub.
        round112_scripts = run(['git', 'ls-tree', '-r', '--name-only', 'HEAD', '--', 'scripts'], 'local_script_paths').splitlines()
        current_scripts = {path for path in round112_scripts if 'round112' in Path(path).name}
        paths = sorted(set(source) | set(helpers) | current_scripts | {'scripts/round110_public.py'})
        ls = run(['git', 'ls-tree', '-r', '-l', '-z', 'HEAD', '--', prefix] + paths, 'local_required_tree', True)
        local = {}
        for row in ls.split(b'\0'):
            if not row:
                continue
            meta, name = row.split(b'\t', 1)
            mode, kind, oid, size = meta.decode().split()
            assert kind == 'blob'
            local[name.decode()] = dict(SHA1=oid, bytes=int(size))
        assert all(path in local for path in paths)
        assert prefix + '/compact_evidence/evidence.tar.gz' in local
        # Fetch only the required subtrees; avoid truncation in historical data.
        cache = {}

        def tree(oid, recursive=False):
            key = (oid, recursive)
            if key not in cache:
                endpoint = 'repos/' + repo + '/git/trees/' + oid
                if recursive:
                    endpoint += '?recursive=1'
                value = json.loads(run(['gh', 'api', endpoint], 'remote_tree_' + str(len(cache))))
                assert not value.get('truncated', False)
                cache[key] = value
            return cache[key]

        commit = json.loads(run(['gh', 'api', 'repos/' + repo + '/git/commits/' + local_head], 'remote_commit'))
        local_tree = run(['git', 'rev-parse', 'HEAD^{tree}'], 'local_tree').strip()
        assert commit['sha'] == local_head and commit['tree']['sha'] == local_tree
        root_tree = tree(local_tree)
        assert root_tree['sha'] == local_tree
        remote = {entry['path']: entry for entry in root_tree['tree'] if entry['type'] == 'blob'}
        tops = {path.split('/', 1)[0] for path in local if '/' in path}
        entries = {entry['path']: entry for entry in root_tree['tree']}
        for top in sorted(tops):
            if top == 'results':
                result_entries = {entry['path']: entry for entry in tree(entries[top]['sha'])['tree']}
                r112 = tree(result_entries['unified_exact_round112']['sha'], True)
                for entry in r112['tree']:
                    if entry['type'] == 'blob':
                        remote[prefix + '/' + entry['path']] = entry
            else:
                for entry in tree(entries[top]['sha'], True)['tree']:
                    if entry['type'] == 'blob':
                        remote[top + '/' + entry['path']] = entry
        bindings = []
        for path, expected in sorted(local.items()):
            actual = remote[path]
            assert actual['sha'] == expected['SHA1'] and actual['size'] == expected['bytes'], path
            bindings.append(dict(path=path, Git_blob_SHA1=actual['sha'], bytes=actual['size']))
        expected_current = {path for path in local if path.startswith(prefix + '/')}
        actual_current = {path for path in remote if path.startswith(prefix + '/')}
        assert expected_current == actual_current
        archive = local[prefix + '/compact_evidence/evidence.tar.gz']
        manifest = json.loads((root / prefix / 'compact_evidence/manifest.json').read_text(encoding='utf-8'))
        assert archive['bytes'] == manifest['archive_bytes'] == 82842777
        assert archive['bytes'] < 95 * 1024 * 1024 and not manifest['parts']
        assert len(manifest['files']) == 55916
        forbidden = [path for path in actual_current if Path(path).suffix.lower() in {'.exe', '.dll', '.lic'}]
        assert not forbidden
        receipt = dict(schema='round112_actual_remote_publication_verification_v1',
                       observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       decision='PASS', scientific_stage='BLOCKED', PR=pr['url'],
                       head_commit=local_head, base_commit=base_oid,
                       remote_commit_tree=local_tree,
                       head_ref=head_name, base_ref=base_name, state=pr['state'], draft=pr['isDraft'],
                       scientific_payload_commit='a3cac1df0ee1d4eaaeb87343508e0af31cfc3b40',
                       measured_production_commit='d0014a7163e3996fe120471420e56b089c9715ae',
                       all_remote_required_Git_blobs_equal=True,
                       required_files=len(bindings), current_round_files=len(actual_current),
                       measured_sources=206, frozen_helpers=38,
                       current_round_scripts=len(current_scripts),
                       archive_bytes=archive['bytes'], archive_Git_blob_SHA1=archive['SHA1'],
                       archive_SHA256_from_actual_public_recovery=manifest['archive_sha256'],
                       archive_remote_identity_basis='same Git blob SHA1 and size as committed local archive',
                       archive_downloaded_again=False, artificial_parts=0,
                       public_member_count=55916, public_forbidden_native_files=forbidden,
                       future_receipt_commit_verified=False, native_starts=0, Optimize=0,
                       compiler_starts=0, commands=records, bindings=bindings,
                       elapsed_engineering_seconds=time.perf_counter() - start)
        (args.out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({key:receipt[key] for key in ('decision','PR','head_commit','base_commit','state','draft','required_files','current_round_files','archive_bytes')}))
    except Exception as error:
        failure = dict(decision='FAIL', observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       error=repr(error), commands=records, native_starts=0, Optimize=0,
                       compiler_starts=0, elapsed_engineering_seconds=time.perf_counter()-start)
        (args.out / 'failure_receipt.json').write_text(json.dumps(failure, indent=2) + '\n', encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
