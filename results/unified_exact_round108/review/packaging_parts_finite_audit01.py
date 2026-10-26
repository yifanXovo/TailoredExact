"""Small synthetic integration/refusal audit of the frozen public carrier.

Uses the candidate's actual stdlib split/export/recombine/restore API. The CLI
95/90 MiB constants stay unchanged. Every fixture/output is under review/.
No performance inputs, native environments, solver or compiler are used.
"""
import argparse, contextlib, copy, gzip, hashlib, io, json, os, runpy, sys, tarfile, time, traceback
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);p.add_argument('--candidate-sha',required=True);a=p.parse_args()
root=Path(a.root).resolve();dest=Path(a.out).resolve();assert dest.is_relative_to(root/'results/unified_exact_round108/review')
dest.mkdir(exist_ok=False);candidate=root/'scripts/round108_public.py';candidate_bytes=candidate.read_bytes()
digest=lambda b:hashlib.sha256(b).hexdigest()
assert digest(candidate_bytes)==a.candidate_sha
api=runpy.run_path(str(candidate));cases=[];tick=time.perf_counter();active_links=[]
class FixtureError(Exception):pass
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def actual(name,fn,reject=False):
    where=dest/f'case{len(cases)+1:03d}';where.mkdir();start=time.perf_counter()
    output=io.StringIO()
    try:
        with contextlib.redirect_stdout(output):value=fn(where)
    except Exception as e:
        if isinstance(e,FixtureError):raise
        if not reject:raise
        cases.append(dict(name=name,expected='reject',actual='rejected',exception=type(e).__name__+': '+str(e),seconds=time.perf_counter()-start));return
    finally:(where/'api_stdout.log').write_text(output.getvalue(),encoding='utf-8',newline='\n')
    if reject:raise AssertionError('candidate incorrectly accepted: '+name)
    cases.append(dict(name=name,expected='accept',actual='accepted',value=value,seconds=time.perf_counter()-start))

def byte_carrier(where,total=157,limit=64,part_bytes=48):
    package=where/'package';package.mkdir();archive=package/'evidence.tar.gz';archive.write_bytes(bytes(i%251 for i in range(total)))
    parts=api['split_archive'](archive,limit,part_bytes)
    m=dict(archive_path='evidence.tar.gz',archive_bytes=total,archive_sha256=api['sha'](archive),parts=parts,single_blob_limit_bytes=limit,part_bytes=part_bytes)
    return package,m,archive
def mutate_carrier(where,mutation):
    package,m,archive=byte_carrier(where);mutation(package,m,archive)
    return api['validate_carrier'](package,m,64,48)
def tarbytes(entries):
    stream=io.BytesIO()
    with gzip.GzipFile(filename='',mode='wb',fileobj=stream,mtime=0) as gz,tarfile.open(fileobj=gz,mode='w|') as t:
        for name,contents,kind in entries:
            info=tarfile.TarInfo(name);info.mode=0o644;info.mtime=0
            if kind=='file':info.size=len(contents);t.addfile(info,io.BytesIO(contents))
            else:info.type=tarfile.SYMTYPE;info.linkname=contents;t.addfile(info)
    return stream.getvalue()
reader=b'# synthetic reader placeholder; never executed\n'
newline_payload='exact CRLF\r\n精确文字\r\n'.encode('utf-8')
default_entries=[('scripts/round108_public.py',candidate_bytes,'file'),('scripts/round108_reader.py',reader,'file'),('reference/synthetic_exact.txt',newline_payload,'file')]

def archive_fixture(where,split=True,entries=None):
    fixture=where/'original';public=where/'public';package=fixture/api['ROUND']/'compact_evidence';package.mkdir(parents=True)
    (fixture/'scripts').mkdir();(fixture/'scripts/round108_public.py').write_bytes(candidate_bytes)
    entries=default_entries if entries is None else entries
    b=tarbytes(entries);archive=package/'evidence.tar.gz';archive.write_bytes(b)
    limit,part= (1024,512) if split else (max(len(b)+100,2048),1024)
    records=[dict(path=n,bytes=len(v),sha256=digest(v)) for n,v,k in entries if k=='file']
    parts=api['split_archive'](archive,limit,part)
    m=dict(schema='round108-public-exact-byte-carrier-v2',archive_path='evidence.tar.gz',archive_bytes=len(b),archive_sha256=digest(b),parts=parts,single_blob_limit_bytes=limit,part_bytes=part,files=records,public_dependencies=[],reader_SHA=digest(reader),restore_source_SHA=a.candidate_sha)
    write(package/'manifest.json',m)
    # Export the actual candidate through its optional small API limits.
    api['export'](fixture,public,limit,part)
    exported=public/api['ROUND']/'compact_evidence'
    assert (exported/'evidence.tar.gz').exists()==(not bool(parts))
    assert digest((public/'scripts/round108_public.py').read_bytes())==a.candidate_sha
    assert {x.name for x in exported.iterdir()}==({'manifest.json'}|{r['path'] for r in parts} if parts else {'manifest.json','evidence.tar.gz'})
    exported_api=runpy.run_path(str(public/'scripts/round108_public.py'))
    return fixture,public,exported,m,limit,part,exported_api,b
def rewrite_manifest(package,m):
    (package/'manifest.json').write_text(json.dumps(m)+'\n',encoding='utf-8')
def verify_restore(where,split):
    fixture,public,package,m,limit,part,exported,b=archive_fixture(where,split)
    restored=where/'recovered';exported['restore'](public,restored,limit,part)
    rr=json.loads((restored/'restore_receipt.json').read_text())
    assert rr['restorer_SHA']==a.candidate_sha and rr['archive_SHA']==digest(b)
    assert rr['exact_part_count']==len(m['parts']) and rr['exit_code']==0 and rr['public_files_only'] and not rr['original_workspace_reads']
    for n,v,k in default_entries:assert (restored/n).read_bytes()==v
    if split:assert (restored/'restored_public_carrier.tar.gz').read_bytes()==b
    return dict(compressed_bytes=len(b),parts=len(m['parts']),exported_without_large_combined_blob=split,exact_bytes_and_CRLF=True,restore_receipt_SHA=api['sha'](restored/'restore_receipt.json'))
def bad_restore(where,mutation,split=True,entries=None):
    fixture,public,package,m,limit,part,exported,b=archive_fixture(where,split,entries)
    mutation(where,public,package,m,fixture)
    rewrite_manifest(package,m)
    return exported['restore'](public,where/'recovered',limit,part)
def make_link(link,target,directory=False):
    # Actual OS links, removed after the case so pack gets plain artifacts.
    try:os.symlink(target,link,target_is_directory=directory)
    except OSError as e:raise FixtureError('actual link fixture could not be created: '+str(e)) from e
    active_links.append(link)
def symlink_part(where):
    package,m,archive=byte_carrier(where);part=package/m['parts'][0]['path'];copyout=where/'outside_part';copyout.write_bytes(part.read_bytes());part.unlink();make_link(part,copyout)
    return api['validate_carrier'](package,m,64,48)
def symlink_dependency(where,public,package,m,fixture):
    q=where/'outside_doc.txt';q.write_bytes(b'outside public root synthetic document\n');d=public/'reference';d.mkdir()
    make_link(d/'history.txt',q);m['public_dependencies']=[dict(path='reference/history.txt',bytes=q.stat().st_size,sha256=api['sha'](q))]
def symlink_package(where,public,package,m,fixture):
    outside=where/'outside_package';package.rename(outside);make_link(package,outside,True)
    # No manifest rewrite through the escaped link; the bytes are already valid.
    return outside

source_sha=digest(Path(__file__).read_bytes());write(dest/'launch.json',dict(actual_command=[sys.executable,*sys.argv],explicit_read_root=str(root),source_SHA=source_sha,candidate_source_SHA=a.candidate_sha,synthetic_only=True,small_limits_API_only=True,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
error=None;decision='HOLD'
try:
    assert api['SINGLE_BLOB_LIMIT']==95*1024*1024 and api['PART_BYTES']==90*1024*1024
    for size in [0,63,64,65,157]:
        def boundary(where,total=size):
            package,m,archive=byte_carrier(where,total);paths=api['validate_carrier'](package,m,64,48);rebuilt=where/'combined';api['recombine_carrier'](package,m,rebuilt,64,48)
            assert rebuilt.read_bytes()==archive.read_bytes() and bool(m['parts'])==(total>=64)
            return dict(actual_bytes=total,parts=len(m['parts']),strict_boundary_split=total>=64)
        actual('strict threshold bytes '+str(size)+' split only if >= limit',boundary)
    def tiny_default(where):
        archive=where/'evidence.tar.gz';archive.write_bytes(b'unchanged exact bytes');assert api['split_archive'](archive)==[]
        return dict(actual_bytes=archive.stat().st_size,default_limits_unchanged=True)
    actual('default95/90 parameters remain fixed and tiny real archive stays unsplit',tiny_default)
    actual('split refuses preexisting part without overwriting',lambda w:mutate_carrier(w,lambda p,m,a:api['split_archive'](a,64,48)),True)
    actual('split rejects nonpositive part size',lambda w: (lambda p:api['split_archive'](p,64,0))((lambda p:(p.write_bytes(b'xx'),p)[1])(w/'evidence.tar.gz')),True)
    mutations=[
        ('manifest archive path escape',lambda p,m,a:m.update(archive_path='../evidence.tar.gz')),
        ('wrong manifest default/API limit',lambda p,m,a:m.update(single_blob_limit_bytes=65)),
        ('wrong part capacity',lambda p,m,a:m.update(part_bytes=47)),
        ('Boolean total size forbidden',lambda p,m,a:m.update(archive_bytes=True)),
        ('missing declared part record',lambda p,m,a:m['parts'].pop()),
        ('part record reorder',lambda p,m,a:m['parts'].reverse()),
        ('wrong part index',lambda p,m,a:m['parts'][0].update(index=2)),
        ('noncanonical path traversal',lambda p,m,a:m['parts'][0].update(path='../external.part001')),
        ('duplicate part path',lambda p,m,a:m['parts'][1].update(path=m['parts'][0]['path'])),
        ('offset gap',lambda p,m,a:m['parts'][1].update(offset=m['parts'][1]['offset']+1)),
        ('offset overlap',lambda p,m,a:m['parts'][1].update(offset=0)),
        ('wrong expected part length',lambda p,m,a:m['parts'][0].update(bytes=47)),
        ('wrong per-part hash',lambda p,m,a:m['parts'][0].update(sha256='0'*64)),
        ('wrong combined hash',lambda p,m,a:m.update(archive_sha256='f'*64)),
        ('missing actual part file',lambda p,m,a:(p/m['parts'][0]['path']).unlink()),
        ('extra actual canonical-looking part',lambda p,m,a:(p/'evidence.tar.gz.part999').write_bytes(b'extra')),
        ('same-size corrupt actual part',lambda p,m,a:(p/m['parts'][0]['path']).write_bytes(b'X'*48)),
    ]
    for name,mutation in mutations:actual(name,lambda w,fn=mutation:mutate_carrier(w,fn),True)
    def correct_part_wrong_whole(package,m,archive):
        target=package/m['parts'][0]['path'];target.write_bytes(b'X'*48);m['parts'][0]['sha256']=api['sha'](target)
    actual('all per-part hashes valid but concatenated whole hash wrong',lambda w:mutate_carrier(w,correct_part_wrong_whole),True)
    actual('actual file symlink part rejected',symlink_part,True)
    def small_with_parts(where):
        package,m,archive=byte_carrier(where,63);m['parts']=[dict(index=1,path='evidence.tar.gz.part001',offset=0,bytes=63,sha256=m['archive_sha256'])]
        (package/m['parts'][0]['path']).write_bytes(archive.read_bytes());return api['validate_carrier'](package,m,64,48)
    actual('small carrier artificial part manifest rejected',small_with_parts,True)
    def extra_unsplit(where):
        package,m,archive=byte_carrier(where,63);(package/'evidence.tar.gz.part001').write_bytes(b'x');return api['validate_carrier'](package,m,64,48)
    actual('unsplit carrier extra part rejected',extra_unsplit,True)
    def recombine_existing(where):
        package,m,archive=byte_carrier(where);target=where/'existing';target.write_bytes(b'retained bytes');return api['recombine_carrier'](package,m,target,64,48)
    actual('recombine never overwrites existing destination',recombine_existing,True)
    actual('actual split export/fresh restore exact compressed stream and member CRLF',lambda w:verify_restore(w,True))
    actual('actual unsplit export/fresh restore leaves small carrier unsplit',lambda w:verify_restore(w,False))
    def legitimate_dependency(where):
        fixture,public,package,m,limit,part,exported,b=archive_fixture(where)
        doc=public/'reference/history.txt';doc.parent.mkdir();doc.write_bytes(b'precise public dependency\r\n')
        m['public_dependencies']=[dict(path='reference/history.txt',bytes=doc.stat().st_size,sha256=api['sha'](doc))];rewrite_manifest(package,m)
        exported['restore'](public,where/'recovered',limit,part);assert (where/'recovered/reference/history.txt').read_bytes()==doc.read_bytes()
        return dict(exact_public_dependency_only=True)
    actual('legitimate contained explicit public dependency exact bytes',legitimate_dependency)
    def escaped_dependency(where,public,package,m,fixture):
        doc=where/'outside.txt';doc.write_bytes(b'outside public synthetic bytes\n');(public/'reference').mkdir()
        m['public_dependencies']=[dict(path='reference/../../outside.txt',bytes=doc.stat().st_size,sha256=api['sha'](doc))]
    actual('dependency path escape actual old counterexample now rejected',lambda w:bad_restore(w,escaped_dependency),True)
    actual('actual public dependency file symlink rejected',lambda w:bad_restore(w,symlink_dependency),True)
    def package_link(where):
        fixture,public,package,m,limit,part,exported,b=archive_fixture(where);symlink_package(where,public,package,m,fixture)
        return exported['restore'](public,where/'recovered',limit,part)
    actual('public package directory symlink cannot read escaped manifest',package_link,True)
    actual('wrong dependency hash refused',lambda w:bad_restore(w,lambda w,p,k,m,f:(lambda q:(q.parent.mkdir(),q.write_bytes(b'wrong'),m.update(public_dependencies=[dict(path='reference/history.txt',bytes=5,sha256='0'*64)])))(p/'reference/history.txt')),True)
    actual('wrong dependency declared size refused',lambda w:bad_restore(w,lambda w,p,k,m,f:(lambda q:(q.parent.mkdir(),q.write_bytes(b'exact'),m.update(public_dependencies=[dict(path='reference/history.txt',bytes=6,sha256=api['sha'](q))])))(p/'reference/history.txt')),True)
    actual('wrong member SHA refused after exact whole validation',lambda w:bad_restore(w,lambda w,p,k,m,f:m['files'][0].update(sha256='0'*64)),True)
    actual('manifest restore script identity mismatch refused',lambda w:bad_restore(w,lambda w,p,k,m,f:m.update(restore_source_SHA='0'*64)),True)
    actual('manifest restored reader identity mismatch refused',lambda w:bad_restore(w,lambda w,p,k,m,f:m.update(reader_SHA='f'*64)),True)
    actual('missing expected archive member refused',lambda w:bad_restore(w,lambda w,p,k,m,f:m['files'].append(dict(path='reference/absent.txt',bytes=1,sha256=digest(b'x')))),True)
    actual('unexpected actual archive member refused',lambda w:bad_restore(w,lambda w,p,k,m,f:m['files'].pop()),True)
    # Existing output: no overwrite or fallback to another readable root.
    def existing_restore(where):
        f,p,k,m,l,b,ex,z=archive_fixture(where);target=where/'recovered';target.mkdir();(target/'keep.txt').write_bytes(b'keep');return ex['restore'](p,target,l,b)
    actual('fresh restoration refuses existing directory',existing_restore,True)
    actual('missing public part does not fallback to available original fixture part',lambda w:bad_restore(w,lambda w,p,k,m,f:(k/m['parts'][0]['path']).unlink()),True)
    # These are plain synthetic tar archives; no symlink is left on disk.
    def tar_refusal(where,entries):
        f,p,k,m,l,b,ex,z=archive_fixture(where,True,entries)
        m['files']=list({q['path']:q for q in m['files']}.values());rewrite_manifest(k,m)
        return ex['restore'](p,where/'recovered',l,b)
    dup=default_entries+[default_entries[1]]
    actual('duplicate plain-file member refused',lambda w:tar_refusal(w,dup),True)
    link=default_entries+[('reference/linked.txt','../../outside.txt','symlink')]
    actual('native tar symlink member refused before extraction',lambda w:tar_refusal(w,link),True)
    escape=default_entries+[('../escaped.txt',b'outside','file')]
    actual('tar member path escape refused',lambda w:tar_refusal(w,escape),True)
    forbidden=default_entries+[('scripts/not_public.dll',b'synthetic text only','file')]
    actual('forbidden native binary extension refused even for synthetic text',lambda w:tar_refusal(w,forbidden),True)
    assert digest(candidate.read_bytes())==a.candidate_sha
    decision='ACCEPT'
except Exception as e:error=type(e).__name__+': '+str(e);trace=traceback.format_exc()
finally:
    for link in reversed(active_links):
        assert link.absolute().is_relative_to(dest)
        if link.is_symlink():link.unlink()
result=dict(decision=decision,error=error,cases=cases,case_count=len(cases),candidate_source_SHA=a.candidate_sha,source_SHA=source_sha,explicit_read_root=str(root),small_limits_API_only=True,default_CLI_limit_bytes=95*1024*1024,default_CLI_part_bytes=90*1024*1024,links_cleaned=len(active_links),Optimize=0,LP_solve=0,native_environment=0,compiler=0)
if error:result['traceback']=trace
write(dest/'checks.json',result)
write(dest/'receipt.json',dict(actual_command=[sys.executable,*sys.argv],explicit_read_root=str(root),source_SHA=source_sha,candidate_source_SHA=a.candidate_sha,exit_code=0 if decision=='ACCEPT' else 1,decision=decision,error=error,seconds=time.perf_counter()-tick,cases=len(cases),checks_SHA=digest((dest/'checks.json').read_bytes()),Optimize=0,LP_solve=0,native_environment=0,compiler=0))
print(json.dumps(dict(decision=decision,error=error,cases=len(cases),candidate_source_SHA=a.candidate_sha,checks_SHA=digest((dest/'checks.json').read_bytes())),ensure_ascii=False),flush=True)
if decision!='ACCEPT':sys.exit(1)
