"""Bounded new-carrier screening and post-PR reconstructible preview cleanup."""
from round138_common import *
import re,zipfile,shutil
from round138_delivery import BANNED,INDEX

def screen():
    assert not budget()['unclosed']
    manifest=read(OUT/'carrier_manifest.json');counts=0;total=0;largest=0
    patterns=[re.compile(p) for p in [
        rb'gh[pousr]_[A-Za-z0-9]{36,}',rb'github_pat_[A-Za-z0-9_]{30,}',
        rb'AKIA[0-9A-Z]{16}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        rb'(?i)WLSSECRET[ \t]*=[ \t]*[A-Za-z0-9_-]{12,}']]
    carriers=[]
    for record in manifest['carriers']:
        path=ROOT/record['path'];assert sha(path)==record['SHA256']
        assert path.stat().st_size==record['bytes']<100*1024*1024
        with zipfile.ZipFile(path) as z:
            index=json.loads(z.read(INDEX));assert len(index)==record['members']
            for name,item in index.items():
                p=Path(name);assert p.suffix.lower() not in BANNED and '.git' not in p.parts
                raw=z.read(name);assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['SHA256']
                assert not any(pattern.search(raw) for pattern in patterns),('credential-shaped data; inspect privately',name)
                counts+=1;total+=len(raw);largest=max(largest,len(raw))
        carriers.append(dict(path=record['path'],bytes=record['bytes'],SHA256=record['SHA256']))
    write(OUT/'publication_screen.json',dict(PASS=True,UTC=utc(),manifest_SHA=sha(OUT/'carrier_manifest.json'),scope='Only the newly published Round138 carriers and members',
        carriers=carriers,members=counts,uncompressed_bytes=total,largest_member_bytes=largest,
        banned_native_license_font_assets_found=0,credential_pattern_findings=0,
        credential_check_scope='Bounded explicit token/private-key patterns plus named license-secret assignments; not a claim about arbitrary undiscoverable secrets',
        old_round_assets_not_rescanned=True,Optimize=0,vendor_DLL_loads=0))
    print(json.dumps(dict(PASS=True,carriers=len(carriers),members=counts,bytes=total)))

def cleanup():
    assert not budget()['unclosed']
    public=read(OUT/'public_restore_receipt.json');qa=read(OUT/'pdf_visual_review.json')
    pr=read(OUT/'PR_delivery.json')
    assert public['passed'] and qa['PASS'] and pr['draft'] and pr['state'].lower()=='open'
    screening=read(OUT/'publication_screen.json')
    assert pr['number']>0 and screening['PASS'] and screening['manifest_SHA']==sha(OUT/'carrier_manifest.json')
    assert public['manifest_SHA']==sha(OUT/'carrier_manifest.json')
    assert qa['PDF_SHA']==sha(OUT/'manuscript.pdf')
    carrier=next(r for r in read(OUT/'carrier_manifest.json')['carriers'] if r['path'].endswith('/science_and_paper.zip'))
    archive=ROOT/carrier['path'];assert sha(archive)==carrier['SHA256']
    with zipfile.ZipFile(archive) as z:
        raw=z.read(INDEX);assert hashlib.sha256(raw).hexdigest()==carrier['member_index_SHA']
        assert json.loads(raw)[(OUT/'manuscript.pdf').relative_to(ROOT).as_posix()]['SHA256']==qa['PDF_SHA']
    render=read(OUT/'pdf_render_manifest.json')
    assert qa['render_manifest_SHA']==sha(OUT/'pdf_render_manifest.json') and render['PDF_SHA']==qa['PDF_SHA']
    target=(OUT/'qa_pages').resolve();intended=(WORK/'worktrees/paper-current/results/unified_exact_round138/qa_pages').resolve()
    assert target==intended and target.is_relative_to(WORK.resolve())
    assert target.parent==OUT.resolve() and target.name=='qa_pages'
    assert not (OUT/'cleanup_receipt.json').exists(),'Current-round cleanup is recorded once'
    before=shutil.disk_usage(WORK);files=[]
    if target.exists():
        assert target.is_dir() and not target.is_symlink()
        expected={(ROOT/row['preview']).resolve():row['PNG_SHA'] for row in render['pages']}
        assert all(p.is_relative_to(target) for p in expected)
        actual={p.resolve() for p in target.rglob('*') if p.is_file()}
        assert actual==set(expected),'Only the exact rendered and visually reviewed preview set may be removed'
        for path in sorted(target.rglob('*')):
            assert path.resolve().is_relative_to(target) and not path.is_symlink()
            if path.is_file():
                assert path.suffix.lower()=='.png',('Only reconstructible page PNGs are eligible',path)
                assert sha(path)==expected[path.resolve()]
                files.append(dict(path=path.relative_to(WORK).as_posix(),bytes=path.stat().st_size,SHA256=sha(path)))
        shutil.rmtree(target)
    after=shutil.disk_usage(WORK)
    write(OUT/'cleanup_receipt.json',dict(UTC=utc(),round=138,PR=pr['URL'],public_receipt_SHA=sha(OUT/'public_restore_receipt.json'),
        verified_absolute_target=str(target),files_deleted=files,file_count=len(files),file_bytes=sum(p['bytes'] for p in files),
        observed_free_before=before.free,observed_free_after=after.free,observed_free_change=after.free-before.free,
        free_space_is_a_concurrent_volume_observation=True,
        retained=['Unique raw and all native/reader failure records','New immutable carriers and finite public restore',
          'Final PDF, sources, figures and page-by-page visual-review receipt','Necessary R137/R138 PE and Gurobi DLL',
          'Original protected checkout, all old-round worktrees and still-used dependencies'],
        no_old_round_deletion=True,no_solver_or_build=True))
    print(json.dumps(dict(deleted_files=len(files),file_bytes=sum(p['bytes'] for p in files),observed_free_change=after.free-before.free)))

if __name__=='__main__':globals()[sys.argv[1]]()
