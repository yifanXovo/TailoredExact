"""Lossless stage evidence bundles and per-member byte verification."""
import hashlib
import gzip
import io
import json
import sys
import tarfile
import time
from pathlib import Path
from round78_qualify import ROOT,sha,read,write
OUT=ROOT/'results/unified_exact_round81'

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
    assert read(OUT/'campaign/audit.json')['all_checks_passed']
    assert read(OUT/'campaign/mechanism_audit.json')['all_checks_passed']
    assert read(OUT/'campaign/replication_audit.json')['all_checks_passed']
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
    frozen=read(OUT/'campaign/identity.json')
    for launch in frozen['launches']:
        raw=ROOT/launch['destination']
        package(f"full_run_{launch['number']}",[(p,p.relative_to(raw).as_posix()) for p in sorted(raw.rglob('*')) if p.is_file()])
    raw=OUT/'campaign/reference'
    package('full_reference',[(p,p.relative_to(raw).as_posix()) for p in sorted(raw.rglob('*')) if p.is_file()])
    manifest=dict(bundles=bundles,source_scope='All14 complete-run raw files and five original compact reference trees; inherited R78 qualification/startup/diagnostic bundles are referenced, not duplicated',
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
    replication=read(OUT/'campaign/replication_audit.json')
    resource=dict(new_qualification_calls=0,new_build_calls=0,new_ctests=0,new_native_fixture_calls=0,
        new_full_runs=full['completed'],full_run_seconds=full['total_wall_seconds'],
        full_run_optimize_calls=a['actual_optimize_calls'],full_run_offline_replay_seconds=full['offline_replay_seconds'],
        full_preflight_seconds=preflight['preflight_wall_including_reference_seconds'],
        full_reference_seconds_nested=preflight['reference_wall_seconds'],
        final_audit_seconds=a['wall_seconds'],mechanism_audit_seconds=mechanism['wall_seconds'],
        replication_audit_seconds=replication['wall_seconds'],
        package_and_verify_seconds=result['package_and_verify_seconds'],
        stage_complete=False,overall_goal_complete=False,reset_credits_consumed=0,
        scope='Full paid processes and separately measured offline steps; inherited qualification costs not counted again; interactive work is not a complete machine-time census.')
    write(OUT/'resource_summary.json',resource);print(json.dumps(result))

if __name__=='__main__':main()
