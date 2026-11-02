"""Idle-only finite carriers, anonymous recovery, protection checks and cleanup."""
import gzip
import io
import re
import shutil
import zipfile
from round147_common import *


def idle():
    configure()
    assert not budget()['unclosed']


def files(folder):
    return [p for p in folder.rglob('*') if p.is_file()] if folder.exists() else []


def local():
    idle()
    report = read(OUT / 'reports/full.json')
    assert not report['pending'] and read(OUT / 'candidate_decision.json')['study_complete']
    assert report['new_Native_Optimize'] == report['new_Native_returned']
    assert read(OUT / 'review/final_scientific_review.json')['PASS']
    assert read(OUT / 'qualification_wrapper_reader.json')['PASS']
    assert read(OUT / 'entry_check.json')['PASS']
    manifest = read(OUT / 'candidate_manifest.json')
    assert sha(manifest['production_PE']) == manifest['production_PE_SHA'] and sha(DLL) == DLL_SHA
    for name, digest in manifest['source_hashes'].items():
        assert sha(ROOT / name) == digest, name
    assert not git('diff', BASE, '--', 'src', 'include', 'CMakeLists.txt').strip()
    protected = git('ls-tree', '-r', '--name-only', BASE, '--', 'config', 'scripts').decode().splitlines()
    protected = [p for p in protected if p.startswith(('config/gi_tbc', 'scripts/paper_s2'))]
    for name in protected:
        assert not git('diff', BASE, '--', name).strip(), name
    assert not git('diff', BASE, '--', *[f'results/unified_exact_round{i}' for i in range(137, 147)]).strip()
    original = Path('E:/codes/ExactEBRP')
    start = read(OUT / 'start_receipt.json')
    assert git('status', '--porcelain=v1', '--untracked-files=no', cwd=original).decode() == \
        (OUT / 'protected_original_tracked_status.txt').read_text(encoding='utf-8')
    for name, digest in start['protected_modified_file_hashes'].items():
        assert sha(original / name) == digest, name
    for row in report['new_arms']:
        destination = Path(row['destination'])
        for name, digest in read(destination / 'producer_seal.json')['required_SHA'].items():
            assert sha(destination / name) == digest, name
        assert read(destination / 'verification_closeout.json')['necessary_verification_complete']
        assert read(destination / 'round147_control_audit.json')['PASS']
    write(OUT / 'local_semantic_check.json', dict(PASS=True, UTC=utc(),
        production_source_and_PE_unchanged=True, all_new_arms_verified=True,
        protected_old_entries=protected, old_results_R137_R146_unchanged=True,
        original_user_modified_bytes_unchanged=True, all_entered_preserved=True,
        Optimize=0, Native_load=0, compile=0))
    print('PASS local science, actual raw seals, historical identity and protected user bytes')


def pack():
    idle()
    tick = time.perf_counter()
    archives, index = [], {}

    def archive(name, paths):
        paths = sorted(set(paths))
        target = OUT / 'artifacts' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.exists(), 'Sealed carriers are not silently replaced'
        members = []
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
            for path in paths:
                assert path.resolve().is_relative_to(ROOT.resolve())
                assert path.suffix.lower() not in {'.exe', '.dll', '.lic', '.o', '.obj', '.a', '.lib', '.pyc'}
                member = path.relative_to(ROOT).as_posix()
                data = path.read_bytes()
                zipped.writestr(member, data)
                members.append(dict(member=member, SHA256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
        assert target.stat().st_size < 100_000_000
        relative = target.relative_to(ROOT).as_posix()
        index[relative] = members
        archives.append(dict(path=relative, SHA256=sha(target), bytes=target.stat().st_size,
                             member_count=len(members)))

    arm_fees = set()
    for path in sorted(OUT.glob('*_matrix.json')):
        matrix = read(path)
        for group in matrix['groups']:
            arm_fees.add(f'{matrix["batch"]}_{group["position"]:03}')
            archive(f'campaign_{matrix["batch"]}_{group["position"]:03}.zip',
                files(OUT / group['group']) + files(OUT / 'fees' / f'{matrix["batch"]}_{group["position"]:03}'))
    diagnostics = files(OUT / 'qualification') + files(OUT / 'engineering') + files(OUT / 'infra')
    diagnostics += [p for folder in (OUT / 'fees').iterdir() if folder.name not in arm_fees for p in files(folder)]
    archive('qualification_and_preparation.zip', diagnostics)
    parent = read(OLD / 'carrier_manifest.json')
    required = ['source_and_helpers.zip', 'qualification_complete.zip', 'diagnostics_and_failures.zip',
                'finite_inherited_inputs.zip']
    for item in read(OUT / 'reuse_index.json')['old_cells']:
        required.append(f'campaign_{item["batch"]}_{item["position"]:03}.zip')
    inherited = [a for a in parent['archives'] if Path(a['path']).name in required]
    assert {Path(a['path']).name for a in inherited} == set(required)
    write(OUT / 'inherited_carrier_index.json', dict(fixed_science=SCIENCE146,
        parent_manifest_path='results/unified_exact_round146/carrier_manifest.json',
        parent_manifest_SHA256=sha(OLD / 'carrier_manifest.json'), member_index=parent['member_index'],
        required_archives=inherited, existing_qualified_results_not_copied=True,
        source_rows_driver='results/unified_exact_round146/rows_driver.json',
        old_cost_not_recharged=True, new_Optimize=0, Native_load=0))
    sources = [*ROOT.glob('scripts/round147*.py'), ROOT / 'scripts/paper_s2_gd_only.py',
               ROOT / 'config/gi_tbc_gd_round147.json', ROOT / '.gitattributes']
    archive('new_source_and_helpers.zip', sources)
    excluded = {'carrier_manifest.json', 'publication_pin.json', 'public_restore_owner.json',
        'public_attempt_history.json', 'public_restore_receipt.json', 'cleanup_record.json',
        'PR_delivery.json', 'PR_readback.json', 'PR_description.md', 'delivery_costs.json'}
    science = [p for p in OUT.iterdir() if p.is_file() and p.name not in excluded]
    for folder in ['reports', 'review', 'figures', 'stages']:
        science += files(OUT / folder)
    archive('science_and_paper.zip', science)
    target = OUT / 'artifacts/member_index.json.gz'
    target.write_bytes(gzip.compress(json.dumps(index, separators=(',', ':'), ensure_ascii=False).encode(),
                                     compresslevel=6, mtime=0))
    write(OUT / 'carrier_manifest.json', dict(UTC=utc(), schema='round147-incremental-carriers-v1',
        archives=archives, archive_count=len(archives), indexed_members=sum(len(v) for v in index.values()),
        compressed_bytes=sum(a['bytes'] for a in archives) + target.stat().st_size,
        member_index=dict(path=target.relative_to(ROOT).as_posix(), SHA256=sha(target), bytes=target.stat().st_size),
        inherited_science=SCIENCE146, old_history_duplicated=False,
        Optimize=0, Native_load=0, compile=0, seconds=time.perf_counter() - tick,
        commercial_binaries_or_licenses_published=False))
    print(json.dumps(dict(archives=len(archives), members=sum(len(v) for v in index.values()),
                          seconds=time.perf_counter() - tick)))


def public(commit):
    idle()
    assert re.fullmatch('[0-9a-f]{40}', commit)
    history_path = OUT / 'public_attempt_history.json'
    history = read(history_path) if history_path.exists() else []
    spent = sum(r['seconds'] for r in history)
    assert spent < 1800
    tick = time.perf_counter()
    target = WORK / 'restore' / f'round147-public-{commit[:12]}-attempt{len(history) + 1:02}'
    assert target.resolve().is_relative_to((WORK / 'restore').resolve())
    target.mkdir(parents=True, exist_ok=False)
    write(OUT / 'public_restore_owner.json', dict(UTC=utc(), directory=str(target), fixed_commit=commit))
    manifest = read(OUT / 'carrier_manifest.json')
    records = []

    def fetch(relative):
        assert spent + time.perf_counter() - tick < 1800
        url = f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{commit}/{relative}'
        # Use the existing Windows trust store through Schannel. The MSYS
        # OpenSSL build lacks the local issuer; never disable TLS verification.
        client = Path('C:/Windows/System32/curl.exe')
        destination = target / Path(relative).name
        run = subprocess.run([str(client), '--disable', '--fail', '--silent', '--show-error',
            '--location', '--max-time', '90', '--proto', '=https', '--proto-redir', '=https',
            '--output', str(destination), '--url', url], capture_output=True, timeout=100)
        assert run.returncode == 0, run.stderr.decode(errors='replace')
        return destination.read_bytes(), url

    try:
        data, manifest_url = fetch('results/unified_exact_round147/carrier_manifest.json')
        assert hashlib.sha256(data).hexdigest() == sha(OUT / 'carrier_manifest.json')
        (target / 'carrier_manifest.json').write_bytes(data)
        item = manifest['member_index']
        data, index_url = fetch(item['path'])
        assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['SHA256']
        index = json.loads(gzip.decompress(data))
        assert set(index) == {a['path'] for a in manifest['archives']}
        (target / 'member_index.json.gz').write_bytes(data)
        for item in manifest['archives']:
            data, url = fetch(item['path'])
            assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['SHA256']
            members = index[item['path']]
            with zipfile.ZipFile(io.BytesIO(data)) as zipped:
                assert sorted(zipped.namelist()) == sorted(m['member'] for m in members)
                for member in members:
                    value = zipped.read(member['member'])
                    assert len(value) == member['bytes'] and hashlib.sha256(value).hexdigest() == member['SHA256']
            (target / Path(item['path']).name).write_bytes(data)
            records.append(dict(path=item['path'], url=url, SHA256=item['SHA256'], bytes=len(data),
                                members_checked=len(members), anonymous=True))
        assert sum(r['members_checked'] for r in records) == manifest['indexed_members']
        receipt = dict(PASS=True, UTC=utc(), fixed_commit=commit, archives=records,
            seconds=time.perf_counter() - tick, manifest_url=manifest_url, member_index_url=index_url,
            manifest_SHA256=sha(OUT / 'carrier_manifest.json'), credentials_used=False,
            transport='Windows curl / Schannel; curlrc disabled; HTTPS only; default certificate verification enabled',
            TLS_verification_enabled=True, helper_SHA256=sha(__file__),
            transport_helper_is_late_delivery_only=True,
            Optimize=0, Native_load=0, compile=0, only_public_bytes_and_members=True)
    except BaseException as error:
        receipt = dict(PASS=False, UTC=utc(), fixed_commit=commit, archives=records,
            seconds=time.perf_counter() - tick, error=repr(error), Optimize=0, Native_load=0, compile=0)
        history.append(receipt)
        write(history_path, history)
        write(OUT / 'public_restore_receipt.json', dict(receipt, cumulative_seconds=spent + receipt['seconds']))
        raise
    history.append(receipt)
    write(history_path, history)
    write(OUT / 'public_restore_receipt.json', dict(receipt, cumulative_seconds=spent + receipt['seconds']))
    print(json.dumps(dict(PASS=True, archives=len(records), members=sum(r['members_checked'] for r in records),
                          seconds=receipt['seconds'])))


def prbody(commit):
    idle()
    assert re.fullmatch('[0-9a-f]{40}', commit)
    full, cost, decision = [read(OUT / name) for name in ['reports/full.json', 'cost_report.json', 'candidate_decision.json']]
    assert not full['pending'] and read(OUT / 'review/final_scientific_review.json')['PASS']
    manifest = read(OUT / 'candidate_manifest.json')
    base = read(OUT / 'PR_base_selection.json')
    url = f'https://github.com/yifanXovo/TailoredExact/blob/{commit}/results/unified_exact_round147'
    text = f'''The existing direct Gini-deviation rows had complete-search evidence only on top of STOCK. This adds a separate standalone GD entry/profile and a four-cell reader, preserving the old SD/S entry meanings. Production C++, PE and mathematical construction are unchanged: at most two root-generated selector rows, no new columns or source solves. The reader also handles legitimate zero-row omission using the actual original model and root metadata.

{decision['core_discussion']}

{decision['extension_discussion']}

Decision: **{decision['decision']}**. {decision['decision_discussion']}

The study has {len(full['new_arms'])} new complete own-H positions and seven verified sealed same-PE R146 references. Every new arm retains Seed0/Threads1, H seed20260626 and full physical, Start, scope, quality, lifecycle and R134 proof validation. All {full['new_Native_Optimize']} new Native Optimize calls returned. No standalone LP, source optimization, production build, repeated Native health qualification, placement grid or extra seed was opened. Actual CLI/zero-row fixture checks use zero Optimize and Native load. Charged new outer cost is **{cost['charged_new_experiment_seconds']:.9f} seconds** of 18000, including qualification/failure costs and postverification without nested double counting. Historical fees remain historical; cross-round identity does not assume equal host load. Open certificates are not replaced by caps, and no wall-clock factorial interaction is claimed.

Fixed science `{commit}`:

- [Scientific report]({url}/final_report.md), [decision]({url}/candidate_decision.json), [four-cell results]({url}/reports/four_cell_evidence.csv)
- [Paper section]({url}/manuscript.md), [mathematics]({url}/mathematical_analysis.md), [verified trajectories]({url}/reports/verified_U_trajectories.csv)
- [Independent review]({url}/review/final_scientific_review.json), [cost]({url}/cost_report.json), [reuse index]({url}/reuse_index.json), [carriers]({url}/carrier_manifest.json)

Measured production source is `{manifest['source_commit']}`; PE SHA256 is `{manifest['production_PE_SHA']}`. Wrapping, scientific and late delivery commits have separate identities. Stable R137, all earlier entries/profiles and historical results retain their bytes. {base['explanation']}. This remains an English Draft PR; no merge, force push or old-round deletion. Anonymous bounded public byte/member recovery and post-PR current-round cleanup are recorded in the [latest delivery record](https://github.com/yifanXovo/TailoredExact/blob/codex/round147-gd-independent-value/results/unified_exact_round147/RESUME.md).
'''
    (OUT / 'PR_description.md').write_text(text, encoding='utf-8', newline='\n')
    print(str(OUT / 'PR_description.md'))


def cleanup():
    idle()
    assert read(OUT / 'public_restore_receipt.json')['PASS'] and read(OUT / 'PR_readback.json')['draft']
    before = shutil.disk_usage(WORK).free
    roots = [OUT, TEMP]
    for i, attempt in enumerate(read(OUT / 'public_attempt_history.json'), 1):
        assert re.fullmatch('[0-9a-f]{40}', attempt['fixed_commit'])
        roots.append(WORK / 'restore' / f'round147-public-{attempt["fixed_commit"][:12]}-attempt{i:02}')
    retained = []
    for root in roots:
        assert root.resolve().is_relative_to(WORK.resolve())
        paths = files(root)
        retained.append(dict(path=str(root), files=len(paths), logical_bytes=sum(p.stat().st_size for p in paths),
            reason='Unique current-round raw, active science/lineage, or finite accepted public restore retained'))
    manifest = read(OUT / 'candidate_manifest.json')
    runtime = [Path(manifest['production_PE']), DLL, Path(read(OLD / 'rows_driver.json')['PE'])]
    runtime_files = [dict(path=str(path), bytes=path.stat().st_size, SHA256=sha(path),
        reason='Required inherited production/Native/pure-arithmetic runtime; retained in place') for path in runtime]
    after = shutil.disk_usage(WORK).free
    write(OUT / 'cleanup_record.json', dict(UTC=utc(), deleted_paths=[], deleted_logical_bytes=0,
        retained=retained, free_bytes_before=before, free_bytes_after=after, observed_volume_delta=after - before,
        volume_delta_not_attributed_to_deletion=True, bounded_current_round_only=True,
        old_rounds_deleted=False, original_user_tree_modified=False,
        necessary_inherited_PE_DLL_retained=True, retained_runtime_files=runtime_files,
        zero_deletion_reason='Retain unique raw and active tree; zero deletion is explicitly accepted by goal I',
        public_acceptance_SHA=sha(OUT / 'public_restore_receipt.json'), PR_readback_SHA=sha(OUT / 'PR_readback.json')))
    print('Bounded cleanup complete: zero deletion; unique raw, runtime and active tree retained')


if __name__ == '__main__':
    if sys.argv[1] in ('public', 'prbody'):
        globals()[sys.argv[1]](sys.argv[2])
    else:
        globals()[sys.argv[1]]()
