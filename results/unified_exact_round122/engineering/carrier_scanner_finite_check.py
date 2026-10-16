"""Bounded toy scanner equivalence, not a scientific export or recovery."""
import gzip,hashlib,io,json,pathlib,sys,tarfile,tempfile,time,shutil
ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import publication_security as original
from round122_release import scan_carrier
from round122_common import TEMP,write,sha

tick=time.perf_counter();before=shutil.disk_usage(TEMP).free;names=[];logical=0
with tempfile.TemporaryDirectory(prefix='r122-scanner-fixture-',dir=TEMP) as name:
    fixture=pathlib.Path(name).resolve()
    assert fixture.is_relative_to(TEMP.resolve()) and not fixture.is_junction() and not fixture.is_symlink()
    target=fixture/'carrier';target.mkdir()
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w') as archive:
        raw=b'{"fixture": true, "scientific_data": false}\n'
        member=tarfile.TarInfo('fixture/record.json');member.size=len(raw)
        archive.addfile(member,io.BytesIO(raw))
    compressed=gzip.compress(buffer.getvalue(),mtime=0);parts=[]
    for n,start in enumerate(range(0,len(compressed),17),1):
        p=target/f'evidence.tar.gz.part{n:03d}';data=compressed[start:start+17];p.write_bytes(data)
        parts.append(dict(path=p.relative_to(fixture).as_posix(),SHA=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    write(target/'manifest.json',dict(fixture_only=True,parts=parts))
    streamed=scan_carrier(fixture,target,parts)
    baseline=original.scan_items(original.file_items(fixture,['carrier']))
    for key in ['passed','files','archive_members','bytes_scanned','findings','errors']:
        assert streamed[key]==baseline[key],(key,streamed[key],baseline[key])
    assert streamed['passed'] and streamed['archive_members']==1
    names=[p.relative_to(fixture).as_posix() for p in target.iterdir()]
    logical=sum(p.stat().st_size for p in target.iterdir())
    # TemporaryDirectory deletes only this newly owned, resolved and verified root.
    checked_root=str(fixture)
write(pathlib.Path(__file__).with_suffix('.json'),dict(passed=True,fixture_only=True,scientific_exports=0,scientific_restores=0,
    unchanged_scan_semantics_keys=['passed','files','archive_members','bytes_scanned','findings','errors'],
    streamed_result=streamed,baseline_result=baseline,part_bytes=17,temporary_root=checked_root,temporary_files_removed=names,
    removed_logical_bytes=logical,free_before=before,free_after=shutil.disk_usage(TEMP).free,
    free_change_not_attributed_solely_to_fixture=True,native_starts=0,Optimize=0,release_SHA=sha(ROOT/'scripts/round122_release.py'),
    code_SHA=sha(__file__),engineering_seconds=time.perf_counter()-tick))
print(json.dumps(dict(passed=True,parts=len(parts),scientific_exports=0,scientific_restores=0,logical_temp_bytes_removed=logical)))
