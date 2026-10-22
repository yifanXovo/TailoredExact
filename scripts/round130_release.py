"""Finite R130 lossless carriers and publication manifest; zero native work.

Run only after all formal processes exit. One explicitly labelled R129 B20
arm is copied as an explanatory historical dependency, never as a new timing.
"""
from round130_common import *
from round127_release import scan, idle, script_closure
import csv, gzip, zipfile


def historical_reference():
    example = read(OUT/'R129_B20_coverage_example.json')
    source = Path(example['source_saved_arm']).resolve()
    expected = (WORK/'worktrees/round129/results/unified_exact_round129/campaign/group03/raw/02_UC-B20-B_S0_R1_MS2').resolve()
    assert source == expected and not source.is_symlink() and not source.is_junction()
    target = OUT/'coverage_reference/R129_B20_MS2_S0'
    assert not target.exists(), 'Preserve the once-copied historical dependency'
    target.mkdir(parents=True)
    rows = []
    for p in sorted(source.rglob('*')):
        if not p.is_file():
            continue
        assert not p.is_symlink() and not p.is_junction()
        q = target/p.relative_to(source)
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, q)
        assert sha(p) == sha(q)
        rows.append(dict(original_path=str(p), published_path=q.relative_to(ROOT).as_posix(),
                         SHA256=sha(q), bytes=q.stat().st_size))
    write(OUT/'coverage_reference/copy_receipt.json', dict(UTC=utc(),
        source_round=129, method='original E2 MS2', id='UC-B20-B', seed=0,
        source_arm=str(source), files=rows,
        scope='Exactly one saved explanatory coverage arm, not a historical campaign or a Round130 performance observation',
        formal_optimum_Start_or_bound_injection=False, Optimize=0))


def pack():
    idle()
    assert not (OUT/'raw_archive_manifest.json').exists(), 'Preserve completed carriers'
    groups = read(OUT/'experiment_manifest.json')['groups']
    assert len(groups) == 6 and all((OUT/g['name']/'reconstructed.json').is_file() for g in groups)
    # The current pack meter itself is intentionally excluded from its archive.
    unclosed = budget()['unclosed']
    assert len(unclosed) <= 1 and all(n.startswith('release_pack') for n in unclosed), unclosed
    historical_reference()
    target = OUT/'artifacts'
    target.mkdir(exist_ok=True)
    temporary = TEMP/'archives'
    temporary.mkdir(parents=True, exist_ok=False)
    plans = [(f'formal_group{n:02d}', [p for p in (OUT/g['name']).rglob('*') if p.is_file()])
             for n, g in enumerate(groups, 1)]
    support = [p for p in (OUT/'qualification').rglob('*') if p.is_file()]
    support.extend(p for folder in (OUT/'fees').iterdir()
                   if folder.is_dir() and (folder/'receipt.json').is_file()
                   for p in folder.rglob('*') if p.is_file())
    plans.append(('qualification_closed_fees', support))
    plans.append(('R129_single_B20_coverage_reference',
                  [p for p in (OUT/'coverage_reference').rglob('*') if p.is_file()]))
    raw = sum(p.stat().st_size for _, files in plans for p in set(files))
    archive_upper = raw + sum(len(files) for _, files in plans)*2048 + 1024**3
    additional = raw + 6*archive_upper + 2*1024**3
    free = shutil.disk_usage(WORK).free
    write(OUT/'review/packing_space_check.json', dict(UTC=utc(),
        status='PASS' if free >= additional else 'INSUFFICIENT_SPACE',
        free_bytes=free, logical_planned_member_bytes=raw,
        conservative_additional_peak_bytes=additional,
        preliminary_peak_allowance_bytes=read(OUT/'initialization.json')['peak_increment_allowance_bytes'],
        planning_bound_only_not_a_measured_peak_or_reclamation=True))
    assert free >= additional
    archives = []
    scanned = 0
    for label, files in plans:
        complete = temporary/(label+'.zip')
        members = []
        with zipfile.ZipFile(complete, 'x', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
            for p in sorted(set(files)):
                scanned += scan(p)
                member = p.relative_to(ROOT).as_posix()
                members.append(dict(path=member, bytes=p.stat().st_size, SHA256=sha(p)))
                z.write(p, member)
        decoded = json.dumps(members, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        index = OUT/'evidence'/(label+'.members.json.gz')
        index.parent.mkdir(exist_ok=True)
        index.write_bytes(gzip.compress(decoded, mtime=0))
        pieces = []
        with complete.open('rb') as stream:
            number = 1
            while data := stream.read(48*1024**2):
                name = complete.name if complete.stat().st_size <= 48*1024**2 else complete.name+f'.part{number:02d}'
                p = target/name
                assert not p.exists()
                p.write_bytes(data)
                pieces.append(dict(path=p.relative_to(ROOT).as_posix(), bytes=len(data), SHA256=sha(p)))
                number += 1
        archives.append(dict(name=complete.name, SHA256=sha(complete),
            compressed_bytes=complete.stat().st_size,
            uncompressed_bytes=sum(m['bytes'] for m in members), file_count=len(members), pieces=pieces,
            member_index=dict(format='gzip-json-utf8-list-v1', path=index.relative_to(ROOT).as_posix(),
                SHA256=sha(index), bytes=index.stat().st_size, decoded_bytes=len(decoded),
                decoded_SHA256=hashlib.sha256(decoded).hexdigest(), members=len(members)),
            historical_dependency=(label == 'R129_single_B20_coverage_reference'),
            temporary_complete_archive=str(complete)))
    write(OUT/'raw_archive_manifest.json', dict(schema='round130-finite-carriers-v1', archives=archives,
        current_formal_groups=6, qualification_and_closed_fee_archives=1,
        accurately_labelled_single_historical_coverage_arm_archives=1,
        raw_remains_authoritative_in_place=True,
        no_PE_DLL_license_fonts_or_full_historical_campaigns=True,
        live_pack_fee_and_future_receipts_excluded=True))
    write(OUT/'review/publication_scan.json', dict(status='PASS',
        actual_precompression_bytes_scanned=scanned, actual_archives=len(archives),
        scope='Every actual member before compression; inherited credential and forbidden-extension checks',
        future_receipts_not_claimed_scanned=True))
    print(json.dumps(dict(archives=len(archives), raw_bytes=raw,
        compressed_bytes=sum(a['compressed_bytes'] for a in archives), scanned_bytes=scanned)))


def manifest():
    idle()
    assert (OUT/'raw_archive_manifest.json').is_file()
    files = {p for p in OUT.iterdir() if p.is_file()
             and p.name != 'export_manifest.json' and p.suffix != '.log' and not p.name.endswith('.local.json')}
    files.update(p for folder in ['review', 'tables', 'evidence', 'inputs']
                 for p in (OUT/folder).rglob('*') if p.is_file())
    files.update(ROOT/name for name in read(OUT/'E3_frozen.json')['source_bindings'])
    files.update(ROOT/p['input_path'] for p in read(OUT/'input_manifest.json')['roles'])
    for archive in read(OUT/'raw_archive_manifest.json')['archives']:
        files.update(ROOT/p['path'] for p in archive['pieces'])
    starts = [p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('round130_*.py')]
    files.update(ROOT/name for name in script_closure(starts))
    files.update(ROOT/name for name in read(OUT/'execution_binding.json')['adapters'])
    files.update(ROOT/name for name in [
        'scripts/round130_export.cpp', 'scripts/round130_cleanup.ps1',
        'reference/round106_confirmation/S12.txt', 'reference/round98_confirmation/C2.txt',
        'results/unified_exact_round94/preregistration.json'])
    # Small source tables retain their own historical identities. No previous
    # campaign carrier is traversed or restored to fill a current observation.
    for round_no, names in {
        129: ['goal.md', 'candidate_decision.md', 'input_manifest.json', 'arms.csv', 'pairs.csv',
              'mechanism_costs.csv', 'actual_method_differences.json', 'paper_method_config.json'],
        128: ['md_root_contract.md', 'source_fix_scope.md', 'E2_frozen.json'],
        127: ['method_matrix.md', 'E1_frozen.json'],
    }.items():
        for name in names:
            p = ROOT/f'results/unified_exact_round{round_no}'/name
            if p.is_file():
                files.add(p)
    for row in csv.DictReader((OUT/'evidence_migration.csv').open(encoding='utf-8-sig')):
        name = row['source_authority']
        assert name.startswith('results/unified_exact_round') and name.endswith(('/arms.csv','/main_arms.csv','/core_arms.csv')) and '..' not in Path(name).parts
        p = ROOT/name
        if not p.is_file():
            blob = git('show', BASE+':'+name)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(blob)
        files.add(p)
    for round_no in [122,123]:
        for filename in ['argv_freeze.json','protocol.json','production_identity.json']:
            name=f'results/unified_exact_round{round_no}/'+filename
            p=ROOT/name
            if not p.is_file():
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(git('show',BASE+':'+name))
            files.add(p)
    entries = []
    scanned = 0
    for p in sorted(files):
        assert p.is_file(), str(p)
        scanned += scan(p)
        entries.append(dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size, SHA256=sha(p),
            serialization='exact bytes; inherited Git text transport may require hash-checked LF/CRLF materialization'))
    write(OUT/'export_manifest.json', dict(schema='round130-current-and-exact-dependencies-export-v1',
        base_commit=BASE, files=entries, file_count=len(entries),
        archive_manifest='results/unified_exact_round130/raw_archive_manifest.json',
        no_native_software_licenses_fonts_or_external_full_papers=True,
        one_empty_root_recovery_only=True,
        historical_raw_scope='One explicitly labelled R129 B20 MS2 Seed0 coverage arm only; no historical campaign',
        manifest_does_not_hash_itself=True, fixed_science_snapshot_only=True,
        later_metadata_prose_or_receipts_may_differ_without_repeating_science_recovery=True,
        future_delivery_receipts_excluded=True))
    write(OUT/'review/loose_publication_scan.json', dict(UTC=utc(), status='PASS',
        files=len(entries), actual_bytes_scanned=scanned,
        export_manifest_SHA=sha(OUT/'export_manifest.json'),
        carrier_members_scanned_before_compression='review/publication_scan.json',
        future_delivery_receipts_excluded=True))
    print(json.dumps(dict(export_files=len(entries), bytes=sum(e['bytes'] for e in entries))))


if __name__ == '__main__':
    {'pack': pack, 'manifest': manifest}[sys.argv[1]]()
