"""Lossless stage evidence bundles and per-member byte verification."""
import hashlib
import io
import json
import sys
import tarfile
import time
from pathlib import Path
from round78_qualify import ROOT,OUT,sha,read,write

def verify():
    manifest=read(OUT/'bundle_manifest.json');count=0
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
    return dict(verified_files=count,bundles=len(manifest['bundles']),optimize_calls=0,extracted_files=0)

def main():
    started=time.perf_counter()
    if '--verify-only' in sys.argv:
        result=verify();result['wall_seconds']=time.perf_counter()-started;print(json.dumps(result));return
    assert not (OUT/'startup/active_run.lock').exists() and not (OUT/'qualification_active.lock').exists()
    assert not (OUT/'campaign/active_run.lock').exists()
    assert read(OUT/'campaign/audit.json')['all_checks_passed']
    assert read(OUT/'campaign/mechanism_audit.json')['all_checks_passed']
    summary=read(OUT/'startup/summary.json');diagnostic=read(OUT/'diagnostic/v1/summary.json')
    assert summary['attempted']==summary['valid']==10 and diagnostic['failure'] is None
    assert not (OUT/'bundle_manifest.json').exists() and not (OUT/'bundles').exists()
    (OUT/'bundles').mkdir()
    bundles=[]
    def package(name,files):
        path=OUT/'bundles'/(name+'.tar.gz');members=[]
        assert len({name for _,name in files})==len(files)
        with tarfile.open(path,'w:gz',compresslevel=9) as archive:
            for source,member in sorted(files,key=lambda item:item[1]):
                data=source.read_bytes();info=tarfile.TarInfo(member);info.size=len(data);info.mtime=0;info.mode=0o644
                archive.addfile(info,io.BytesIO(data))
                members.append(dict(source=str(source),member=member,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        bundles.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),bytes=path.stat().st_size,files=members))
    for version in ['v1']:
        build=ROOT/'build/round78'/version;audit=read(OUT/f'qualification_{version}_audit.json')
        files=[(build/name,name) for name in ['configure.log','build.log','tests.log','CMakeCache.txt']]
        for folder in sorted(build.iterdir()):
            if folder.is_dir() and ('_cli_' in folder.name or folder.name.startswith('native_evidence_test_') or folder.name.startswith('round76_structural_') or folder.name.startswith('round78_structural_')):
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
    package('diagnostic_compile',[(ROOT/'build/round78/diagnostic/v1/compile.log','compile.log')])
    frozen=read(OUT/'campaign/identity.json')
    for launch in frozen['launches']:
        raw=ROOT/launch['destination']
        package(f"full_run_{launch['number']}",[(p,p.relative_to(raw).as_posix()) for p in sorted(raw.rglob('*')) if p.is_file()])
    raw=OUT/'campaign/reference'
    package('full_reference',[(p,p.relative_to(raw).as_posix()) for p in sorted(raw.rglob('*')) if p.is_file()])
    prototype=read(OUT/'diagnostic/v1/identity.json')
    for name,digest in prototype['prototype_sources'].items():assert sha(OUT/'diagnostic/v1/source_archive'/name)==digest
    manifest=dict(bundles=bundles,source_scope='All startup, fixed-diagnostic and full-run/reference raw files; structural traces, all native qualification CLI/model/log trees and Start fixture; full build/test/diagnostic-compile logs, no executable binaries',
        raw_files=sum(len(b['files']) for b in bundles),raw_bytes=sum(r['bytes'] for b in bundles for r in b['files']),
        delivered_bytes=sum(b['bytes'] for b in bundles),script_sha256=sha(__file__))
    write(OUT/'bundle_manifest.json',manifest)
    result=verify();result['package_and_verify_seconds']=time.perf_counter()-started
    result.update({k:manifest[k] for k in ['raw_files','raw_bytes','delivered_bytes']})
    write(OUT/'delivery.json',result)
    resource=read(OUT/'resource_summary.json')
    q=read(OUT/'qualification_v1_audit.json');n=read(OUT/'native_integration_audit.json')
    full=read(OUT/'campaign/summary.json');a=read(OUT/'campaign/audit.json')
    mechanism=read(OUT/'campaign/mechanism_audit.json');preflight=read(OUT/'full_preflight.json')
    resource.update(qualification_offline_audit_seconds=q['offline_audit_seconds'],
        native_start_offline_audit_seconds=n['offline_wall_seconds'],new_full_runs=full['completed'],
        full_run_seconds=full['total_wall_seconds'],full_run_optimize_calls=a['actual_optimize_calls'],
        full_run_offline_replay_seconds=full['offline_replay_seconds'],
        full_preflight_seconds=preflight['preflight_wall_including_reference_seconds'],
        full_reference_seconds_nested=preflight['reference_wall_seconds'],
        final_audit_seconds=a['wall_seconds'],mechanism_audit_seconds=mechanism['wall_seconds'],
        package_and_verify_seconds=result['package_and_verify_seconds'],
        stage_complete=False,overall_goal_complete=False)
    write(OUT/'resource_summary.json',resource);print(json.dumps(result))

if __name__=='__main__':main()
