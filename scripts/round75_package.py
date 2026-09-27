"""Lossless stage evidence bundles and per-member byte verification."""
import hashlib
import io
import json
import sys
import tarfile
import time
from pathlib import Path
from round75_qualify import ROOT,OUT,sha,read,write

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
    summary=read(OUT/'startup/summary.json');oracle=read(OUT/'endpoint_oracles.json')
    assert summary['attempted']==summary['valid']==10 and oracle['completed']
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
    for version in ['v1','v2']:
        build=ROOT/'build/round75'/version;audit=read(OUT/f'qualification_{version}_audit.json')
        files=[(build/name,name) for name in ['configure.log','build.log','tests.log','CMakeCache.txt']]
        for folder in sorted(build.iterdir()):
            if folder.is_dir() and ('_cli_' in folder.name or folder.name.startswith('native_evidence_test_')):
                files.extend((p,p.relative_to(build).as_posix()) for p in sorted(folder.rglob('*')) if p.is_file())
        native_dir=Path(audit['native_fixture_logs'][0]['path']).parent
        files.extend((p,'round68_native_fixture/'+p.relative_to(native_dir).as_posix())
                     for p in sorted(native_dir.rglob('*')) if p.is_file())
        sources={str(source.resolve()) for source,_ in files}
        assert all(str(Path(row['path']).resolve()) in sources for row in audit['all_native_logs'])
        package('qualification_'+version,files)
    raw=OUT/'startup/local_raw'
    package('startup',[(p,p.relative_to(raw).as_posix()) for p in sorted(raw.rglob('*')) if p.is_file()])
    manifest=dict(bundles=bundles,source_scope='All startup raw files, all native qualification CLI/model/log trees and native Start fixture; full build/test logs, no executable binaries',
        raw_files=sum(len(b['files']) for b in bundles),raw_bytes=sum(r['bytes'] for b in bundles for r in b['files']),
        delivered_bytes=sum(b['bytes'] for b in bundles),script_sha256=sha(__file__))
    write(OUT/'bundle_manifest.json',manifest)
    result=verify();result['package_and_verify_seconds']=time.perf_counter()-started
    result.update({k:manifest[k] for k in ['raw_files','raw_bytes','delivered_bytes']})
    write(OUT/'delivery.json',result);print(json.dumps(result))

if __name__=='__main__':main()
