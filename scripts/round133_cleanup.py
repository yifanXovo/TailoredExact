"""Delete only verified owned duplicates after actual public recovery."""
from round133_common import *
import gzip, shutil, zipfile


def safe(path,parent):
    path=Path(path).resolve();parent=Path(parent).resolve()
    assert path!=parent and path.is_relative_to(parent),(str(path),str(parent))
    for node in (path,*path.parents):
        if node.exists():assert not node.is_symlink() and not node.is_junction(),str(node)
    return path


def main():
    assert not (OUT/'cleanup_receipt.json').exists(),'completed cleanup is read-only; never repeat it'
    public=read(OUT/'public_restore_receipt.json');assert public['status']=='PASS'
    gate=read(OUT/'review/post_public_delivery_review.json')
    assert gate['decision']=='ACCEPT_PUBLIC_RECOVERY_AND_GUARDED_CLEANUP'
    assert gate['public_restore_receipt_SHA']==sha(OUT/'public_restore_receipt.json')
    owner=read(OUT/'review/round133_owned_public_recovery_root.json')
    assert owner['science_commit']==public['science_commit'] and owner['destination']==public['destination']
    restored=safe(public['destination'],WORK/'restore')
    state=read(restored/'restore_state.json')
    assert state['status']=='PASS' and state['initially_empty'] and state['commit']==public['science_commit']
    assert state['destination']==str(restored)
    manifest=read(OUT/'export_manifest.json');assert sha(OUT/'export_manifest.json')==public['export_manifest_SHA']
    expected={}
    def add(name,size,digest):
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts
        row=dict(bytes=size,SHA=digest)
        if name in expected:assert expected[name]==row,('inconsistent registered duplicate',name)
        else:expected[name]=row
    for row in manifest['files']:add(row['path'],row['bytes'],row['SHA256'])
    add('results/unified_exact_round133/export_manifest.json',(OUT/'export_manifest.json').stat().st_size,sha(OUT/'export_manifest.json'))
    archives=read(OUT/'raw_archive_manifest.json')['archives']
    duplicates=[]
    for archive in archives:
        index=ROOT/archive['member_index']['path'];assert sha(index)==archive['member_index']['SHA256']
        rows=json.loads(gzip.decompress(index.read_bytes()))
        for row in rows:add(row['path'],row['bytes'],row['SHA256'])
        add('archive_transport/'+archive['name'],archive['compressed_bytes'],archive['SHA256'])
        target=safe(archive['temporary_complete_archive'],TEMP/'archives')
        assert target.is_file() and target.stat().st_size==archive['compressed_bytes'] and sha(target)==archive['SHA256']
        combined=hashlib.sha256()
        for row in archive['pieces']:
            path=ROOT/row['path'];assert path.stat().st_size==row['bytes'] and sha(path)==row['SHA256']
            with path.open('rb') as stream:
                for block in iter(lambda:stream.read(1048576),b''):combined.update(block)
        assert combined.hexdigest()==archive['SHA256']
        duplicates.append(dict(path=str(target),bytes=target.stat().st_size,SHA=archive['SHA256'],kind='complete archive duplicate; public pieces retained'))
    pub=read(OUT/'source_publication.json')
    for bundle in (pub['candidate_source_bundle'],pub['execution_helpers']):
        path=ROOT/bundle['path'];assert sha(path)==bundle['SHA']
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():add(info.filename,info.file_size,hashlib.sha256(archive.read(info)).hexdigest())
    for row in manifest['external_dependencies']:add(row['target'],row['bytes'],row['SHA256'])
    state_copy=Path(public['attempt'])/'restore_state.json'
    assert sha(state_copy)==sha(restored/'restore_state.json')
    add('restore_state.json',state_copy.stat().st_size,sha(state_copy))
    actual={}
    for path in restored.rglob('*'):
        assert not path.is_symlink() and not path.is_junction(),str(path)
        if path.is_file():actual[path.relative_to(restored).as_posix()]=path
    assert set(actual)==set(expected),dict(unexpected=sorted(set(actual)-set(expected)),missing=sorted(set(expected)-set(actual)))
    restored_bytes=0
    for name,path in actual.items():
        row=expected[name];assert path.stat().st_size==row['bytes'] and sha(path)==row['SHA'],name
        restored_bytes+=row['bytes']
    # Only the hash-recorded PNG duplicates are removed from rendering areas;
    # distinct drafts, source/logs, text checks and failure history are kept.
    render_receipts=sorted((OUT/'review').glob('pdf_render_attempt*.json'))+[OUT/'review/pdf_render_receipt.json']
    for receipt_path in render_receipts:
        receipt=read(receipt_path)
        for row in receipt['page_images']+receipt['contact_sheets']:
            path=safe(row['path'],TEMP/'pdf')
            assert path.suffix=='.png' and path.is_file() and sha(path)==row['SHA']
            duplicates.append(dict(path=str(path),bytes=path.stat().st_size,SHA=row['SHA'],kind='hash-recorded reconstructible PDF render'))
    pdf=Path(read(OUT/'pdf_export.json')['intermediate_root'])/'reading.pdf'
    pdf=safe(pdf,TEMP/'pdf')
    assert pdf.is_file() and sha(pdf)==sha(OUT/'manuscript.pdf')
    duplicates.append(dict(path=str(pdf),bytes=pdf.stat().st_size,SHA=sha(pdf),kind='byte-identical final PDF duplicate'))
    assert len({row['path'] for row in duplicates})==len(duplicates)
    plan=dict(UTC=utc(),owned_restore_root=str(restored),restored_files=len(actual),restored_file_bytes=restored_bytes,
        root_all_files_match_declared_science_source_state=True,manifest_SHA=sha(OUT/'export_manifest.json'),
        duplicates=duplicates,logical_file_bytes=restored_bytes+sum(row['bytes'] for row in duplicates),
        kept='Unique current raw and failures, original/new PE and DLL, distinct PDF drafts/logs, source/receipts, published carriers, original and all old worktrees and user content')
    write(OUT/'review/cleanup_plan.json',plan)
    before=shutil.disk_usage(WORK).free;tick=time.perf_counter()
    # Absolute resolved paths and every leaf have been checked above. Use one
    # Python filesystem API, never cross-shell computed deletion commands.
    shutil.rmtree(restored)
    removed=[]
    for row in duplicates:
        path=Path(row['path']);assert sha(path)==row['SHA'];path.unlink();removed.append(row)
    after=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_receipt.json',dict(status='PASS',UTC=utc(),science_commit=public['science_commit'],
        plan_SHA=sha(OUT/'review/cleanup_plan.json'),public_restore_receipt_SHA=sha(OUT/'public_restore_receipt.json'),
        removed_owned_restore_root=str(restored),removed_restore_files=len(actual),removed_duplicates=removed,
        logical_deleted_file_bytes=plan['logical_file_bytes'],free_E_before=before,free_E_after=after,
        observed_free_E_change_bytes=after-before,free_space_change_is_not_attributed_entirely_to_cleanup=True,
        kept=plan['kept'],all_absolute_targets_preverified=True,Optimize=0,compile=0,
        cleanup_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(status='PASS',logical_deleted_file_bytes=plan['logical_file_bytes'],observed_free_E_change_bytes=after-before)))


if __name__=='__main__':main()
