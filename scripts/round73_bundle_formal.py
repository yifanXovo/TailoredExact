"""Bundle the audited per-file evidence, retaining byte-exact member identities."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import time
from round73_qualify import ROOT, OUT as STAGE, sha, write
OUT=STAGE/'formal_small'


def verify(manifest):
    count=0
    for bundle in manifest['bundles']:
        path=OUT/bundle['path']
        assert sha(path)==bundle['sha256']
        expected={m['member']:m for m in bundle['members']}
        with tarfile.open(path,'r:gz') as tf:
            seen=set()
            for member in tf:
                assert member.isfile() and member.name in expected and member.name not in seen
                assert not member.name.startswith('/') and '..' not in Path(member.name).parts
                record=expected[member.name];data=tf.extractfile(member).read()
                assert len(data)==record['bytes'] and hashlib.sha256(data).hexdigest()==record['source_sha256']
                seen.add(member.name);count+=1
            assert seen==set(expected)
    return count


def main():
    start=time.perf_counter();audit=json.loads((OUT/'audit.json').read_text())
    assert audit['all_checks_passed'] and not (OUT/'active_run.lock').exists()
    original=json.loads((OUT/'evidence_manifest.json').read_text());groups={}
    for item in original:
        parts=Path(item['artifact']).parts
        group='run_'+parts[2] if parts[1]=='diagnoses' else 'reference'
        member=Path(*parts[1:]).as_posix()[:-3]
        groups.setdefault(group,[]).append(dict(source=item['source'],member=member,
            source_sha256=item['source_sha256'],bytes=item['raw_bytes']))
    dest=OUT/'bundles';assert not dest.exists(),'Do not replace a completed bundle delivery';dest.mkdir()
    bundles=[]
    for group,members in sorted(groups.items()):
        path=dest/(group+'.tar.gz')
        with path.open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
                for m in members:
                    data=(ROOT/m['source']).read_bytes()
                    assert hashlib.sha256(data).hexdigest()==m['source_sha256']
                    info=tarfile.TarInfo(m['member']);info.size=len(data);info.mode=0o644;info.mtime=0
                    tf.addfile(info,io.BytesIO(data))
        bundles.append(dict(path=str(path.relative_to(OUT)),sha256=sha(path),bytes=path.stat().st_size,members=members))
    manifest=dict(schema='round73-lossless-formal-bundles-v1',bundles=bundles,
        original_file_audit_sha256=sha(OUT/'audit.json'),original_files=len(original),
        source_manifest_scope='Each source/member hash maps all original raw files; local per-file gzip duplicates need not be published.')
    assert verify(manifest)==len(original)
    write(OUT/'bundle_manifest.json',manifest)
    delivery=dict(bundles=len(bundles),original_files=len(original),raw_bytes=sum(m['raw_bytes'] for m in original),
        delivered_bytes=sum(b['bytes'] for b in bundles),all_members_hash_verified=True,
        wall_seconds=time.perf_counter()-start,optimizer_calls=0,
        prior_per_file_archival_wall_seconds=audit['wall_seconds'],script_sha256=sha(__file__),
        verification_command='python scripts/round73_verify_bundles.py',
        scope='Same audited evidence, packed for review. Prior packaging cost and local duplicates are retained.')
    write(OUT/'delivery.json',delivery)
    resource=json.loads((STAGE/'formal_resource_summary.json').read_text())
    resource['formal_bundle_seconds']=delivery['wall_seconds'];resource['delivered_formal_bundle_bytes']=delivery['delivered_bytes']
    write(STAGE/'formal_resource_summary.json',resource)
    print(json.dumps(delivery,indent=2))


if __name__=='__main__':main()
