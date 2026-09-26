"""Lossless stage evidence bundles and per-member byte verification."""
import hashlib
import gzip
import io
import json
import sys
import tarfile
import time
from pathlib import Path
from round83_qualify import ROOT,sha,read,write
OUT=ROOT/'results/unified_exact_round83'

def verify():
    index=read(OUT/'bundle_manifest.json')
    member_path=OUT/index['member_manifest_file']
    assert sha(member_path)==index['member_manifest_sha256']
    manifest=json.loads(gzip.decompress(member_path.read_bytes()))
    assert index['raw_files']==manifest['raw_files']
    assert index['raw_bytes']==manifest['raw_bytes']
    assert index['delivered_bytes']==manifest['delivered_bytes']
    assert index['bundles']==[{**{k:v for k,v in b.items() if k!='files'},'file_count':len(b['files'])} for b in manifest['bundles']]
    count=0
    for bundle in manifest['bundles']:
        path=ROOT/bundle['path'].replace('\\','/');assert sha(path)==bundle['sha256']
        expected={row['member']:row for row in bundle['files']}
        with tarfile.open(path,'r:gz') as archive:
            members=archive.getmembers();assert len(members)==len(expected)
            assert len({member.name for member in members})==len(members)
            for member in members:
                row=expected[member.name];assert member.isfile()
                data=archive.extractfile(member).read()
                assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
                count+=1
    assert count==manifest['raw_files']
    return dict(verified_files=count,bundles=len(manifest['bundles']),optimize_calls=0,extracted_files=0)

def main():
    started=time.perf_counter()
    if '--verify-only' in sys.argv:
        result=verify();result['wall_seconds']=time.perf_counter()-started;print(json.dumps(result));return
    assert not (OUT/'campaign/active_run.lock').exists()
    assert not (OUT/'startup/active_run.lock').exists() and not (OUT/'qualification_active.lock').exists()
    assert read(OUT/'startup/completion_summary.json')['all_original_commands_completed']
    assert read(OUT/'diagnostic/v1/summary.json')['failure'] is None
    assert read(OUT/'campaign/audit.json')['all_checks_passed']
    assert read(OUT/'campaign/mechanism_audit.json')['all_checks_passed']
    assert not (OUT/'bundle_manifest.json').exists() and not (OUT/'bundles').exists()
    (OUT/'bundles').mkdir()
    bundles=[]
    def package(name,files):
        path=OUT/'bundles'/(name+'.tar.gz');members=[]
        assert len({name for _,name in files})==len(files)
        with tarfile.open(path,'w:gz',compresslevel=9) as archive:
            for source,member in sorted(files,key=lambda item:item[1]):
                assert source.suffix.lower() not in ['.lic','.exe','.dll','.pem','.key'],source
                data=source.read_bytes();info=tarfile.TarInfo(member);info.size=len(data);info.mtime=0;info.mode=0o644
                archive.addfile(info,io.BytesIO(data))
                members.append(dict(source=str(source),member=member,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        bundles.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),bytes=path.stat().st_size,files=members))
    qualified=read(OUT/'qualification_v1.json')['identity']
    measured=[]
    for name,digest in qualified['source'].items():
        path=ROOT/name;assert sha(path)==digest
        measured.append((path,Path(name).as_posix()))
    assert sha(ROOT/'CMakeLists.txt')==qualified['cmake_sha256']
    measured.append((ROOT/'CMakeLists.txt','CMakeLists.txt'))
    package('measured_source_bytes',measured)
    for version in ['v1']:
        build=ROOT/'build/round83'/version;audit=read(OUT/f'qualification_{version}_audit.json')
        files=[(build/name,name) for name in ['configure.log','build.log','tests.log','CMakeCache.txt']]
        for folder in sorted(build.iterdir()):
            if folder.is_dir() and ('_cli_' in folder.name or folder.name.startswith('native_evidence_test_') or folder.name.startswith('round76_structural_') or folder.name.startswith('round78_structural_') or folder.name.startswith('round83_structural_')):
                files.extend((p,p.relative_to(build).as_posix()) for p in sorted(folder.rglob('*')) if p.is_file())
        native_dir=Path(audit['native_fixture_logs'][0]['path']).parent
        files.extend((p,'round68_native_fixture/'+p.relative_to(native_dir).as_posix())
                     for p in sorted(native_dir.rglob('*')) if p.is_file())
        sources={str(source.resolve()) for source,_ in files}
        assert all(str(Path(row['path']).resolve()) in sources for row in audit['all_native_logs'])
        package('qualification_'+version,files)
    raw=OUT/'startup/local_raw'
    package('startup',[(p,p.relative_to(raw).as_posix()) for p in sorted(raw.rglob('*')) if p.is_file()])
    raw=OUT/'diagnostic/v1/local_raw'
    package('fixed_diagnostic',[(p,p.relative_to(raw).as_posix()) for p in sorted(raw.rglob('*')) if p.is_file()])
    package('diagnostic_compile',[(ROOT/'build/round83/diagnostic/v1/compile.log','compile.log')])
    frozen=read(OUT/'campaign/identity.json')
    for launch in frozen['launches']:
        raw=ROOT/launch['destination']
        package(f"full_run_{launch['number']}",[(p,p.relative_to(raw).as_posix()) for p in sorted(raw.rglob('*')) if p.is_file()])
    raw=OUT/'campaign/reference'
    package('full_reference',[(p,p.relative_to(raw).as_posix()) for p in sorted(raw.rglob('*')) if p.is_file()])
    manifest=dict(bundles=bundles,source_scope='All13 complete-run trees, four original compact references, ten startup outputs including recovered original run6, six standalone diagnostic trees, new native/CLI/structural qualification evidence/build logs, and exact qualified working source bytes including line endings; no executable or license',
        raw_files=sum(len(b['files']) for b in bundles),raw_bytes=sum(r['bytes'] for b in bundles for r in b['files']),
        delivered_bytes=sum(b['bytes'] for b in bundles),script_sha256=sha(__file__))
    member_path=OUT/'bundle_members.json.gz'
    member_path.write_bytes(gzip.compress((json.dumps(manifest,indent=2)+'\n').encode('utf-8'),compresslevel=9,mtime=0))
    index={k:v for k,v in manifest.items() if k!='bundles'}
    index['bundles']=[{**{k:v for k,v in b.items() if k!='files'},'file_count':len(b['files'])} for b in bundles]
    index.update(member_manifest_file=member_path.name,member_manifest_sha256=sha(member_path),
        member_manifest_bytes=member_path.stat().st_size,
        manifest_format='Full original per-member source/path/bytes/SHA256 records in gzip JSON; this index is compact.')
    write(OUT/'bundle_manifest.json',index)
    result=verify();result['package_and_verify_seconds']=time.perf_counter()-started
    result.update({k:manifest[k] for k in ['raw_files','raw_bytes','delivered_bytes']})
    write(OUT/'delivery.json',result)
    full=read(OUT/'campaign/summary.json');a=read(OUT/'campaign/audit.json')
    mechanism=read(OUT/'campaign/mechanism_audit.json');preflight=read(OUT/'full_preflight.json')
    qualification=read(OUT/'qualification_v1_audit.json');qa=read(OUT/'qualification_v1.json')
    diagnostic=read(OUT/'diagnostic/v1/summary.json');startup=read(OUT/'startup/completion_summary.json')
    native=read(OUT/'native_integration_audit.json')
    resource=dict(new_qualification_calls=qualification['actual_optimize_calls'],new_release_builds=1,
        new_ctests=62,new_native_fixture_calls_nested=3,
        qualification_wall_seconds=qualification['full_qualification_wall_seconds'],
        qualification_phases=qa['attempts'],qualification_offline_audit_seconds=qualification['offline_audit_seconds'],
        native_start_offline_audit_seconds=native['offline_wall_seconds'],
        diagnostic_compile_seconds=diagnostic['compile']['wall_seconds'],
        diagnostic_processes=len(diagnostic['records']),
        diagnostic_process_seconds=sum(x['completion']['wall_seconds'] for x in diagnostic['records']),
        diagnostic_offline_replay_seconds=sum(x.get('audit',{}).get('offline_seconds',0) for x in diagnostic['records']),
        diagnostic_driver_seconds_nested=diagnostic['total_driver_seconds'],
        new_startup_processes=startup['attempted'],startup_process_seconds=startup['paid_wall_seconds'],
        startup_offline_replay_seconds=sum(x['offline_audit_seconds'] for x in startup['records']),
        failed_reader_offline_seconds=None,failed_reader_scope='Original D7 replay interrupted on empty-route representation; duration not independently retained. No native rerun.',
        startup_resume_seconds_nested=startup['resume_seconds'],reader_representation_test=read(OUT/'startup/reader_v2_check.json'),
        new_full_runs=full['completed'],full_run_seconds=full['total_wall_seconds'],
        full_run_optimize_calls=a['actual_optimize_calls'],
        total_new_optimize_calls=qualification['actual_optimize_calls']+a['actual_optimize_calls'],
        full_run_offline_replay_seconds=full['offline_replay_seconds'],
        full_preflight_seconds=preflight['preflight_wall_including_reference_seconds'],
        full_reference_seconds_nested=preflight['reference_wall_seconds'],
        final_audit_seconds=a['wall_seconds'],mechanism_audit_seconds=mechanism['wall_seconds'],
        new_inputs_generated=0,package_and_verify_seconds=result['package_and_verify_seconds'],
        stage_complete=False,overall_goal_complete=False,reset_credits_consumed=0,
        scope='Full paid processes and measured offline steps. Nested costs are not additive again; missing failed-reader duration is not zero. Interactive work is not a complete machine-time census.')
    write(OUT/'resource_summary.json',resource);print(json.dumps(result))

if __name__=='__main__':main()
