"""Compact the finite member-SHA lists without touching a carrier or raw file."""
from round127_common import *
import gzip

def compact():
    path=OUT/'raw_archive_manifest.json';original=read(path)
    assert original['archives'] and all('members' in a for a in original['archives'])
    # Preserve the original exact full index locally. The same complete lists
    # remain public in deterministic gzip files bound by the compact manifest.
    preserved=TEMP/'archives/raw_archive_manifest_before_compaction.json'
    assert not preserved.exists();preserved.write_bytes(path.read_bytes())
    before_SHA=sha(path);before_bytes=path.stat().st_size
    indexes=[]
    for archive in original['archives']:
        members=archive.pop('members')
        assert len(members)==archive['file_count'] and len({m['path'] for m in members})==len(members)
        data=json.dumps(members,ensure_ascii=True,separators=(',',':')).encode('utf-8')
        payload=gzip.compress(data,compresslevel=6,mtime=0)
        assert json.loads(gzip.decompress(payload))==members
        target=OUT/'artifacts/member_hashes'/(archive['name']+'.members.json.gz')
        target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();target.write_bytes(payload)
        binding=dict(path=target.relative_to(ROOT).as_posix(),format='gzip-json-utf8-list-v1',
            bytes=len(payload),SHA256=sha(target),decoded_bytes=len(data),
            decoded_SHA256=hashlib.sha256(data).hexdigest(),members=len(members))
        archive['member_index']=binding;indexes.append(binding)
    original.update(schema='round127-finite-carriers-compact-member-index-v2',
        member_index_note='All original member paths, sizes and SHA256 values retained exactly; compressed index files are independently SHA-bound. Carrier ZIP bytes are unchanged.')
    write(path,original)
    receipt=dict(status='PASS',UTC=utc(),old_manifest_SHA256=before_SHA,old_manifest_bytes=before_bytes,
        old_manifest_preserved_locally=str(preserved),new_manifest_SHA256=sha(path),new_manifest_bytes=path.stat().st_size,
        member_indexes=indexes,total_members=sum(x['members'] for x in indexes),
        raw_or_carrier_bytes_changed=False,Optimize=0,
        scope='Packaging representation only; no evidence member, native run, scientific table or gate changed.')
    write(OUT/'review/member_index_compaction.json',receipt)
    print(json.dumps(receipt))

if __name__=='__main__':compact()
