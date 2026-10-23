"""Reuse finite current-only packaging; publish exact small dependencies."""
from round131_benchmark import *
from round127_release import scan,idle,script_closure
import csv, gzip, zipfile

def pack():
    import round129_release as old
    code=inspect.getsource(old.pack).replace("'round129-finite-carriers-v1'","'round131-finite-carriers-v1'")
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,WORK=WORK,sha=sha,read=read,write=write)
    exec(compile(code,__file__+'::inherited_current_only_pack','exec'),ns);ns['pack']()

def manifest():
    idle();assert (OUT/'raw_archive_manifest.json').exists()
    files={p for p in OUT.iterdir() if p.is_file() and p.name!='export_manifest.json' and p.suffix!='.log' and not p.name.endswith('.local.json')}
    files.update(p for folder in ['review','tables','evidence','inputs'] for p in (OUT/folder).rglob('*') if p.is_file())
    files.update(ROOT/n for n in read(OUT/'E3_binding.json')['source_bindings'])
    files.update(ROOT/n for n in read(OUT/'execution_binding.json')['adapters'])
    for a in read(OUT/'raw_archive_manifest.json')['archives']:files.update(ROOT/p['path'] for p in a['pieces'])
    starts=[p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('round131*.py')]
    files.update(ROOT/n for n in script_closure(starts))
    files.update(ROOT/n for n in ['.gitattributes','WORKSPACE_POLICY.md','scripts/round130_export.cpp','scripts/round131_cleanup.ps1',
        'reference/round106_confirmation/S12.txt','reference/round98_confirmation/C2.txt',
        'results/unified_exact_round94/preregistration.json'])
    prior_names=['E3_frozen.json','paper_version_manifest.json','paper_method_config.json','input_manifest.json','experiment_manifest.json',
        'qualification/zero_qualification.json','qualification/native_qualification.json','preformal_source_provenance.json',
        'review/support_count_correction/addendum.json','actual_method_differences.json','arms.csv','pairs.csv','mechanism_costs.csv',
        'evidence_migration.csv','claim_decision.md','scientific_decision.json','stratified_summary.json','manuscript_lineage.json']
    files.update(PRIOR/n for n in prior_names)
    for rnd,names in {127:['input_manifest.json','E1_frozen.json','method_matrix.md'],
        128:['E2_frozen.json','review/preformal_source_review.md','md_root_contract.md'],
        129:['candidate_decision.md','input_manifest.json','paper_method_config.json']}.items():
        files.update(ROOT/f'results/unified_exact_round{rnd}'/n for n in names)
    def get(n):
        p=ROOT/n
        if not p.is_file():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git('show',BASE+':'+n))
        return p
    # A complete labelled record table is a dependency, not an old carrier.
    for row in csv.DictReader((OUT/'evidence_registry.csv').open(encoding='utf-8-sig')):
        n=row['source_authority'];assert n.startswith('results/unified_exact_round') and n.endswith('.csv') and '..' not in Path(n).parts
        files.add(get(n))
    for rnd in [122,123]:
        for n in ['argv_freeze.json','protocol.json','production_identity.json']:files.add(get(f'results/unified_exact_round{rnd}/'+n))
    # The two safe historical source tables retain their own identity.
    for n in ['results/data_generation_citibike_round57/source_station_table.csv',
        'results/unified_exact_round116/source/source_station_table.csv','results/unified_exact_round116/source/snapshot.json',
        'results/unified_exact_round116/projection_contract.json']:
        files.add(get(n))
    entries=[];scanned=0
    for p in sorted(files):
        assert p.is_file(),str(p);scanned+=scan(p)
        entries.append(dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),bytes=p.stat().st_size,
            serialization='exact bytes; inherited Git text transport may require hash-checked LF/CRLF materialization'))
    write(OUT/'export_manifest.json',dict(schema='round131-current-and-exact-small-dependencies-v1',base_commit=BASE,
        files=entries,file_count=len(entries),archive_manifest='results/unified_exact_round131/raw_archive_manifest.json',
        no_native_software_licenses_fonts_or_external_full_papers=True,one_empty_root_recovery_only=True,
        no_historical_raw_carrier_recovered=True,manifest_does_not_hash_itself=True,fixed_science_snapshot_only=True,
        later_metadata_receipts_excluded_without_recursive_repacking=True))
    write(OUT/'review/loose_publication_scan.json',dict(UTC=utc(),status='PASS',files=len(entries),actual_bytes_scanned=scanned,
        export_manifest_SHA=sha(OUT/'export_manifest.json'),carrier_member_scan='review/publication_scan.json',future_receipts_excluded=True))
    print(json.dumps(dict(files=len(entries),bytes=sum(e['bytes'] for e in entries))))

def restore():
    # Same transport and safe member checking as the passed R130 recovery;
    # replace only this round's root, checker, and finite archive name set.
    import round130_public_restore as old
    code=inspect.getsource(old.main).replace('round130','round131').replace('Round130','Round131')
    expected="assert len(archives)==8 and {a['name'] for a in archives}=={f'formal_group{n:02d}.zip' for n in range(1,7)}|{'qualification_closed_fees.zip','R129_single_B20_coverage_reference.zip'}"
    assert expected in code
    code=code.replace(expected,"assert len(archives)==27 and {a['name'] for a in archives}=={f'formal_group{n:02d}.zip' for n in range(1,27)}|{'qualification_closed_fees.zip'}")
    # Full 52-arm read-only replay actually took 1079.55 seconds. The old
    # 24-arm recovery's 600-second checker ceiling is insufficient. This
    # publication-only engineering timeout never changes a formal contract.
    assert code.count('timeout=600')==1
    code=code.replace('timeout=600','timeout=2400')
    ns=dict(vars(old));exec(compile(code,__file__+'::single_public_restore','exec'),ns);ns['main']()

if __name__=='__main__':
    action=sys.argv.pop(1)
    {'pack':pack,'manifest':manifest,'restore':restore}[action]()
