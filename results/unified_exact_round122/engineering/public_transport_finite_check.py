"""Finite mocked public transport checks; no scientific export or network call."""
import collections,gzip,hashlib,io,json,pathlib,sys,tarfile,time
from unittest import mock

ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import round122_release as release
from round122_common import OUT,TEMP,helpers,bindings,identity,read,sha,write,utc

tick=time.perf_counter();commit='a'*40;prefix=release.ROUND+'/compact_evidence/'
original={'fixture/a.json':b'{"x":[1,-0.0,true]}','fixture/b.txt':b'finite public transport fixture\n'}
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w') as arc:
    for name,data in original.items():
        item=tarfile.TarInfo(name);item.size=len(data);arc.addfile(item,io.BytesIO(data))
compressed=gzip.compress(buffer.getvalue(),mtime=0)
parts=[];payload={}
for i,offset in enumerate(range(0,len(compressed),17)):
    name=prefix+f'toy-part-{i:02d}.bin';data=compressed[offset:offset+17];payload[name]=data
    parts.append(dict(path=name,bytes=len(data),SHA=hashlib.sha256(data).hexdigest()))
manifest=dict(schema='round122-current-safe-evidence-v1',parts=parts,files={name:dict(bytes=len(data),SHA=hashlib.sha256(data).hexdigest()) for name,data in original.items()})
encoded=lambda m:(json.dumps(m,sort_keys=True)+'\n').encode()
expected=encoded(manifest);manifest_name=prefix+'manifest.json';base='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+commit+'/'
fixture=(TEMP/'public-transport-finite').resolve();assert fixture.is_relative_to(TEMP.resolve()) and not fixture.exists()
for p in [fixture.parent,*fixture.parents]:assert not p.is_symlink() and not p.is_junction()
fixture.mkdir();created=[];cases=[];all_requests=[]

def exercise(label,m,overrides=None,valid=False,revision=commit,archive=None,expected_calls=None):
    raw=encoded(m);contents=dict(payload);contents[manifest_name]=raw;contents.update(overrides or {})
    requests=[];target=archive or fixture/(label+'.tar')
    def fetch(request,timeout):
        assert timeout==45 and request.get_method()=='GET'
        assert request.get_header('Authorization') is None and request.get_header('Cookie') is None
        assert request.full_url.startswith(base)
        name=request.full_url[len(base):];assert name in contents
        requests.append(request.full_url);return io.BytesIO(contents[name])
    with mock.patch.object(release.urllib.request,'urlopen',side_effect=fetch),mock.patch.object(release.subprocess,'run',side_effect=AssertionError('local process/fallback forbidden')) as process:
        try:result=release.public_carrier_export(revision,raw,target)
        except (AssertionError,OSError,ValueError) as exc:
            assert not valid,(label,type(exc).__name__);cases.append(dict(case=label,rejected=True,error_class=type(exc).__name__))
        else:
            assert valid,label
            assert result['application_credentials_supplied'] is False and result['local_git_archive_used'] is False and result['no_local_part_or_original_raw_fallback'] is True
            assert len(result['fetched'])==len(parts)+1
            with tarfile.open(target) as published:
                assert published.getnames()==[manifest_name]+[p['path'] for p in parts]
                assert published.extractfile(manifest_name).read()==expected
                for part in parts:assert published.extractfile(part['path']).read()==payload[part['path']]
                with tarfile.open(fileobj=release.Joined(published,[p['path'] for p in parts]),mode='r|gz') as inner:
                    reconstructed={member.name:inner.extractfile(member).read() for member in inner}
            assert reconstructed==original
            cases.append(dict(case=label,accepted=True,member_names_and_bytes_equal=True,streamed_reconstruction_equal=True))
        assert process.call_count==0
    if expected_calls is not None:assert len(requests)==expected_calls,(label,len(requests))
    all_requests.extend(requests)
    if target.exists() and target.parent==fixture:created.append(target)

exercise('positive_streaming',manifest,valid=True,expected_calls=len(parts)+1)
exercise('changed_public_manifest',manifest,{manifest_name:expected+b'x'},expected_calls=1)
first=parts[0]['path'];changed=bytes([payload[first][0]^1])+payload[first][1:]
exercise('wrong_part_hash',manifest,{first:changed},expected_calls=2)
exercise('truncated_part',manifest,{first:payload[first][:-1]},expected_calls=2)
exercise('trailing_part',manifest,{first:payload[first]+b'x'},expected_calls=2)
copy=lambda:json.loads(json.dumps(manifest))
m=copy();m['parts'][0]['path']='outside/carrier.bin';exercise('outside_carrier_prefix',m,expected_calls=0)
m=copy();m['parts'][0]['path']='../escape';exercise('unsafe_member',m,expected_calls=0)
m=copy();m['parts'].append(dict(m['parts'][0]));exercise('duplicate_part',m,expected_calls=0)
m=copy();m['parts'][0]['bytes']=True;exercise('boolean_part_size',m,expected_calls=0)
m=copy();m['parts'][0]['SHA']='g'*64;exercise('invalid_digest',m,expected_calls=0)
exercise('unfixed_ref',manifest,revision='HEAD',expected_calls=0)
exercise('invalid_commit',manifest,revision='g'*40,expected_calls=0)
exercise('outside_TEMP',manifest,archive=ROOT/'uncreated-public-transport-fixture.tar',expected_calls=0)
assert not (ROOT/'uncreated-public-transport-fixture.tar').exists()
retained=[dict(name=p.name,bytes=p.stat().st_size,SHA=sha(p)) for p in created]
for p in created:
    assert p.resolve().parent==fixture and fixture.is_relative_to(TEMP.resolve()) and not p.is_symlink()
    p.unlink()
assert not list(fixture.iterdir());fixture.rmdir()
candidate=read(OUT/'candidate_identity.json');identity();assert helpers()==candidate['helpers'] and bindings()==candidate['source_bindings']
receipt=dict(UTC=utc(),passed=True,cases=cases,fixture_parts=len(parts),fixture_compressed_bytes=len(compressed),
    simulated_HTTP_requests=len(all_requests),actual_public_network_requests=0,scientific_carrier_exports=0,scientific_restores=0,
    local_process_or_git_archive_calls=0,removed_toy_files=retained,removed_toy_logical_bytes=sum(x['bytes'] for x in retained),
    TEMP_fixture_path=str(fixture),fixture_path_guarded_and_removed=True,code_SHA=sha(__file__),release_SHA=sha(ROOT/'scripts/round122_release.py'),
    measured_helpers_unchanged=True,production_sources_unchanged=True,native_starts=0,Optimize=0,engineering_seconds=time.perf_counter()-tick)
write(pathlib.Path(__file__).with_suffix('.json'),receipt)
print(json.dumps({k:receipt[k] for k in ['passed','fixture_parts','simulated_HTTP_requests','actual_public_network_requests','scientific_carrier_exports','scientific_restores','removed_toy_logical_bytes','release_SHA']}))
