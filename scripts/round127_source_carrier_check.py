"""Bind all original E0 source replacements to the finished support carrier."""
from round127_common import *
import gzip,zipfile

def check():
    manifest=read(OUT/'raw_archive_manifest.json')
    candidates=[a for a in manifest['archives'] if a['name']=='qualification_closed_fees_original_sources.zip']
    assert len(candidates)==1;a=candidates[0]
    archive=Path(a['temporary_complete_archive'])
    assert archive.stat().st_size==a['compressed_bytes'] and sha(archive)==a['SHA256']
    index=a['member_index'];payload=(ROOT/index['path']).read_bytes()
    assert len(payload)==index['bytes'] and hashlib.sha256(payload).hexdigest()==index['SHA256']
    decoded=gzip.decompress(payload)
    assert len(decoded)==index['decoded_bytes'] and hashlib.sha256(decoded).hexdigest()==index['decoded_SHA256']
    member_list=json.loads(decoded);members={row['path']:row for row in member_list}
    assert len(members)==len(member_list)==a['file_count']==index['members']
    frozen=read(OUT/'E0_identity.json')['source_bindings']
    source=read(OUT/'source_E0_manifest.json');rows=[]
    expected={'src/'+name for name in ['CplexBaseline.cpp','GurobiBaseline.cpp','IntervalRowFactory.cpp','main.cpp','PaperExternalGiniTree.cpp']}
    assert len(source['files'])==5
    assert {r['original_source'] for r in source['files']}==expected
    assert {(r['original_source'],r['path']) for r in source['files']}=={(p,'results/unified_exact_round127/source_E0/'+p) for p in expected}
    with zipfile.ZipFile(archive) as z:
        for row in source['files']:
            data=z.read(row['path']);actual=hashlib.sha256(data).hexdigest()
            assert len(data)==row['bytes']==members[row['path']]['bytes']
            assert actual==row['SHA']==members[row['path']]['SHA256']==frozen[row['original_source']]
            assert actual==sha(ROOT/row['path'])
            rows.append(dict(**row,member_and_local_SHA256=actual))
    report=dict(status='PASS',UTC=utc(),source_files=rows,archive_SHA256=a['SHA256'],
        archive=archive.name,raw_manifest_SHA256=sha(OUT/'raw_archive_manifest.json'),
        source_manifest_SHA256=sha(OUT/'source_E0_manifest.json'),
        originals_retained_locally=True,safe_to_remove_only_these_five_index_entries=True,
        native_solver_starts=0,Optimize=0)
    write(OUT/'review/source_E0_carrier_check.json',report)
    print(json.dumps(dict(status='PASS',source_files=len(rows),bytes=sum(r['bytes'] for r in rows))))

if __name__=='__main__':check()
