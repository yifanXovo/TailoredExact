"""Finite current-only release using established R129/R130 carrier transport.

No native assets are distributed. Preparation and recovery are delivery work;
they must run after the complete serial experimental sequence has exited.
"""
from round132_common import *
from round127_release import scan,script_closure
import inspect,gzip,zipfile

def idle():
    assert (OUT/'sequence_completion.json').is_file(),'Required serial experiments have not closed'
    assert not budget()['unclosed'],budget()
    live=subprocess.check_output(['powershell.exe','-NoProfile','-Command',
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ExactEBRP|Round132Research|Round132Export|gurobi_cl|cmake|ninja|g\\+\\+|cc1plus|MSBuild)\\.exe$' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"],text=True).strip()
    assert not live,live

def pack_source():
    # The same finite ZIP/member-index/piece logic used by the passed R129/131
    # release. Only the current stage lists and truthful labels differ.
    import round129_release as old
    code=inspect.getsource(old.pack)
    old_groups="read(OUT/'experiment_manifest.json')['groups']"
    code=code.replace(old_groups,"(read(OUT/'experiment_plan.json')['D']+read(OUT/'C_experiment_plan.json')['groups'])")
    code=code.replace("f'formal_group{g[\"number\"]:02d}'","g['name'].replace('/','_')")
    needle="support=[p for p in (OUT/'qualification').rglob('*') if p.is_file()]"
    assert needle in code
    code=code.replace(needle,"""for group,(_,files) in zip((read(OUT/'experiment_plan.json')['D']+read(OUT/'C_experiment_plan.json')['groups']),plans):
        for launch in read(OUT/group['name']/'identity.json')['launches']:
            result=read(Path(launch['destination'])/'result.json')
            name=result.get('gurobi_progress_path')
            if name:
                p=ROOT/Path(name)
                assert p.resolve().is_relative_to((ROOT/'results/gurobi_work').resolve())
                if p.is_file():files.append(p)
    """+needle)
    needle="plans.append(('qualification_closed_fees',support))"
    assert needle in code
    code=code.replace(needle,"""support.extend(p for folder in ['engineering','research_sources'] for p in (OUT/folder).rglob('*') if p.is_file())
    plans.append(('qualification_closed_fees_research_sources',support))
    plans.append(('complete_tiny_joint_study',[p for p in (OUT/'joint').rglob('*') if p.is_file()]))""")
    code=code.replace("'round129-finite-carriers-v1'","'round132-finite-current-carriers-v1'")
    return code

def pack():
    idle();assert read(OUT/'observations.json')['execution']=='ALL_C_D_ARMS_SEALED'
    assert not (OUT/'raw_archive_manifest.json').exists(),'Preserve completed carriers'
    import round129_release as old
    code=pack_source()
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,WORK=WORK,sha=sha,read=read,write=write,idle=idle,budget=budget)
    exec(compile(code,__file__+'::inherited_current_pack','exec'),ns);ns['pack']()

def sources():
    idle();build=read(OUT/'research_build.json');rows=[];progress=[]
    for name,row in build['generated_sources'].items():
        p=Path(row['path']);assert sha(p)==row['SHA'];q=OUT/'research_sources'/p.name
        q.parent.mkdir(exist_ok=True)
        if q.exists():assert sha(q)==row['SHA']
        else:shutil.copyfile(p,q)
        rows.append(dict(stem=name,published=q.relative_to(ROOT).as_posix(),SHA=sha(q),original_path=str(p)))
    write(OUT/'research_source_publication.json',dict(files=rows,
        bound_build_receipt='research_build.json',frozen_production_sources_unchanged=True,
        old_build_qualification_pending_field='Immutable creation-time receipt; final qualification is in current_method_manifest.json and qualification/C_*_qualification.json',
        no_PE_DLL_objects_archive_or_license_published=True))
    for g in read(OUT/'experiment_plan.json')['D']+read(OUT/'C_experiment_plan.json')['groups']:
        for l in read(OUT/g['name']/'identity.json')['launches']:
            d=Path(l['destination']);r=read(d/'result.json');name=r.get('gurobi_progress_path')
            if name:
                p=ROOT/Path(name);assert p.resolve().is_relative_to((ROOT/'results/gurobi_work').resolve())
                progress.append(dict(id=l['id'],seed=l['seed'],method=l.get('comparison_method',l['method']),
                    result=d.relative_to(ROOT).as_posix()+'/result.json',path=p.relative_to(ROOT).as_posix(),
                    exists=p.is_file(),bytes=p.stat().st_size if p.is_file() else None,SHA=sha(p) if p.is_file() else None,
                    current_only_actual_recorded_path=True))
    write(OUT/'native_progress_index.json',dict(records=progress,
        current_progress_files_included_in_corresponding_group_carrier=True,no_historical_gurobi_work_traversal=True))

def manifest():
    idle();assert (OUT/'raw_archive_manifest.json').is_file()
    # Receipt-only metadata written after the science commit deliberately is not
    # recursively repacked or recovered. It cannot change a measured result.
    mutable={'export_manifest.json','runtime_status.json','RESUME.md','NEXT.md',
        'sequence_PID.json','public_restore_receipt.json','cleanup_receipt.json',
        'remote_readback.json','delivery_receipt.json'}
    files={p for p in OUT.iterdir() if p.is_file() and p.name not in mutable and p.suffix!='.log'}
    files.update(p for folder in ['review','tables','evidence','inputs','source','cost_segments']
        for p in (OUT/folder).rglob('*') if p.is_file())
    files.update(ROOT/n for n in read(OUT/'E3_binding.json')['source_bindings'])
    files.update(ROOT/n for n in read(OUT/'D_execution_binding.json')['adapters'])
    starts=[p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('round132*.py')]
    files.update(ROOT/n for n in script_closure(starts))
    files.update(ROOT/n for n in ['.gitattributes','WORKSPACE_POLICY.md','scripts/Round132Expression.hpp',
        'scripts/round130_export.cpp','reference/round106_confirmation/S12.txt',
        'reference/round98_confirmation/C2.txt','results/unified_exact_round94/preregistration.json'])
    for a in read(OUT/'raw_archive_manifest.json')['archives']:files.update(ROOT/p['path'] for p in a['pieces'])
    def inherited(n):
        p=ROOT/n
        if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git('show',BASE+':'+n))
        return p
    # Current diagnostic inputs, zero-Optimize contracts and small inherited
    # evidence tables; never restore any previous campaign archive.
    for g in read(OUT/'C_experiment_plan.json')['groups']:files.add(ROOT/g['role']['input_path'])
    prior={130:['E3_frozen.json','paper_version_manifest.json','paper_method_config.json','input_manifest.json',
                'qualification/native_qualification.json','qualification/zero_qualification.json',
                'actual_method_differences.json','arms.csv','pairs.csv','claim_decision.md'],
        131:['paper_version_manifest.json','input_manifest.json','observations.json','arms.csv','pairs.csv',
                'model_appendix.md','algorithm_appendix.md','manuscript.md','final_report.md','review/final_independent_evidence.json'],
        125:['contribution_ledger.md']}
    for rnd,names in prior.items():files.update(inherited(f'results/unified_exact_round{rnd}/'+n) for n in names)
    for n in ['results/data_generation_citibike_round57/source_station_table.csv',
        'results/unified_exact_round116/source/source_station_table.csv',
        'results/unified_exact_round116/source/snapshot.json',
        'results/unified_exact_round116/projection_contract.json']:files.add(inherited(n))
    for row in read(OUT/'historical_station_scope.json')['records']:files.add(inherited(row['path']))
    entries=[];scanned=0
    for p in sorted(files):
        assert p.is_file(),str(p);scanned+=scan(p)
        entries.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,SHA256=sha(p),
            serialization='exact bytes; inherited Git text transport may require hash-checked LF/CRLF materialization'))
    write(OUT/'export_manifest.json',dict(schema='round132-finite-current-and-small-dependencies-v1',base_commit=BASE,
        files=entries,file_count=len(entries),archive_manifest='results/unified_exact_round132/raw_archive_manifest.json',
        no_native_software_licenses_fonts_or_external_full_papers=True,one_empty_root_recovery_only=True,
        no_historical_raw_carrier_recovered=True,manifest_does_not_hash_itself=True,
        fixed_science_snapshot_only=True,later_metadata_receipts_excluded_without_recursive_repacking=True))
    write(OUT/'review/loose_publication_scan.json',dict(UTC=utc(),status='PASS',files=len(entries),actual_bytes_scanned=scanned,
        export_manifest_SHA=sha(OUT/'export_manifest.json'),carrier_member_scan='review/publication_scan.json',future_receipts_excluded=True))
    print(json.dumps(dict(files=len(entries),bytes=sum(r['bytes'] for r in entries))))

def restore():
    # Anonymous HTTPS with curlrc disabled, safe paths, exact SHA/CRC member
    # reconstruction, isolated Python and the current no-native checker.
    import round130_public_restore as old
    code=inspect.getsource(old.main).replace('round130','round132').replace('Round130','Round132')
    expected="assert len(archives)==8 and {a['name'] for a in archives}=={f'formal_group{n:02d}.zip' for n in range(1,7)}|{'qualification_closed_fees.zip','R129_single_B20_coverage_reference.zip'}"
    assert expected in code
    code=code.replace(expected,"assert len(archives)==34 and {a['name'] for a in archives}=={f'campaign_D_group{n:02d}.zip' for n in range(1,25)}|{f'campaign_C_group{n:02d}.zip' for n in range(1,9)}|{'qualification_closed_fees_research_sources.zip','complete_tiny_joint_study.zip'}")
    # 84 arms plus exact tiny witnesses are larger than the old24-arm check.
    # A separate finite delivery timeout never alters native formal windows.
    assert code.count('timeout=600')==1;code=code.replace('timeout=600','timeout=3600')
    ns=dict(vars(old));exec(compile(code,__file__+'::one_public_recovery','exec'),ns);ns['main']()

if __name__=='__main__':
    action=sys.argv.pop(1);{'sources':sources,'pack':pack,'manifest':manifest,'restore':restore}[action]()
