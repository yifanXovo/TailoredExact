"""Stage bounded late receipts without repacking the fixed science payload."""
from round133_common import *
from round133_release import publication_scan
import gzip


def main():
    current=os.environ.get('ROUND133_METERED_PARENT_LABEL')
    assert not [row for row in budget()['unclosed'] if row['label']!=current]
    manifest=read(OUT/'export_manifest.json');declared={row['path']:row for row in manifest['files']}
    archive=next(row for row in read(OUT/'raw_archive_manifest.json')['archives']
        if row['name']=='diagnostics_qualification_math_dependencies_closed_fees.zip')
    index=ROOT/archive['member_index']['path'];assert sha(index)==archive['member_index']['SHA256']
    packed={row['path'] for row in json.loads(gzip.decompress(index.read_bytes()))}
    names=set()
    for name in ('RESUME.md','public_restore_receipt.json','cleanup_receipt.json','delivery_receipt.json',
            'completion_audit.json','resource_accounting.json','remote_readback.json',
            'final_report.md','readiness.md','independent_review.md','reproducibility.md'):
        path=OUT/name
        if path.is_file():names.add(path)
    for path in (OUT/'review').rglob('*'):
        if not path.is_file():continue
        name=path.relative_to(ROOT).as_posix()
        if name not in declared or sha(path)!=declared[name]['SHA256']:names.add(path)
    for name in ('round133_public_resume_budget.py','round133_delivery_metadata.py'):
        path=ROOT/'scripts'/name
        if path.is_file():names.add(path)
    for folder in (OUT/'fees').iterdir():
        if not folder.is_dir() or not (folder/'receipt.json').exists():continue
        missing=[path for path in folder.rglob('*') if path.is_file() and path.relative_to(ROOT).as_posix() not in packed]
        if missing:
            assert read(folder/'launch.json')['kind'] not in LIMITS,'new experiment after science freeze is not permitted'
            names.update(missing)
    rows=[]
    for path in sorted(names):
        publication_scan(path)
        rows.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,SHA=sha(path)))
    assert git('branch','--show-current').decode().strip()=='codex/round133-native-reliability-and-objective-gap'
    temporary=TEMP/'metadata_staging';temporary.mkdir(parents=True,exist_ok=True)
    number=1
    while (temporary/f'attempt{number:02d}').exists():number+=1
    attempt=temporary/f'attempt{number:02d}';attempt.mkdir()
    pathspec=attempt/'paths.nul';pathspec.write_bytes(b''.join(row['path'].encode()+b'\0' for row in rows))
    git('add','--sparse','--force','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul')
    staged=git('diff','--cached','--name-only','-z').decode().split('\0')
    staged=[name for name in staged if name]
    assert set(staged).issubset({row['path'] for row in rows})
    write(attempt/'receipt.json',dict(UTC=utc(),science_commit='e4c6f82316f8697c6dfcf59d3a0807619b7bcae8',
        rows=rows,staged=staged,not_repacked_or_recovered=True,Optimize=0,compile=0))
    print(json.dumps(dict(selected_files=len(rows),staged_files=len(staged),bytes=sum(row['bytes'] for row in rows))))


if __name__=='__main__':main()
