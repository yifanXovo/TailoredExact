"""Post-delivery bounded removal of verified reconstructible page previews only."""
from round140_common import *
import shutil

def main():
    assert not budget()['unclosed']
    assert OUT.resolve().is_relative_to(WORK.resolve())
    public=read(OUT/'public_restore_receipt.json');pin=read(OUT/'publication_pin.json')
    assert public['passed'] and public['commit']==pin['commit']
    assert public['manifest_SHA']==pin['manifest_SHA']==sha(OUT/'carrier_manifest.json')
    pr=read(OUT/'PR_delivery.json');assert pr['draft'] and pr['state']=='open'
    visual=read(OUT/'pdf_visual_review.json');assert visual['PASS'] and visual['PDF_SHA']==sha(OUT/'manuscript.pdf')
    render=read(OUT/'pdf_render_manifest.json');assert render['PDF_SHA']==sha(OUT/'manuscript.pdf')
    manifest=read(OUT/'carrier_manifest.json');science=next(c for c in manifest['carriers'] if c['path'].endswith('/science_and_paper.zip'))
    assert sha(ROOT/science['path'])==science['SHA256']
    import zipfile
    with zipfile.ZipFile(ROOT/science['path']) as z:
        index=json.loads(z.read('__round140_member_index__.json'))
        record=index[(OUT/'manuscript.pdf').relative_to(ROOT).as_posix()]
        assert record['SHA256']==sha(OUT/'manuscript.pdf')
    candidates=[]
    for item in render['pages']:
        p=(ROOT/item['preview']).resolve()
        assert p.is_relative_to((OUT/'qa_pages').resolve()) and p.suffix=='.png' and p.is_file()
        assert sha(p)==item['PNG_SHA']
        candidates.append(dict(path=str(p),SHA256=sha(p),bytes=p.stat().st_size))
    write(OUT/'cleanup_screening.json',dict(UTC=utc(),candidates=candidates,
        basis='Final PDF reviewed and publicly byte-checked; only its reconstructible final page PNGs are eligible',
        retained='Unique raw, all failures, old rounds, user content, final/source PDFs and TeX, all carriers, PE/DLL, build dependencies and active trees'))
    before=shutil.disk_usage(WORK).free;deleted=[]
    for item in candidates:
        p=Path(item['path']);assert p.resolve().is_relative_to((OUT/'qa_pages').resolve()) and sha(p)==item['SHA256']
        p.unlink();deleted.append(item)
    after=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_receipt.json',dict(UTC=utc(),completed=True,deleted=deleted,
        deleted_file_bytes=sum(x['bytes'] for x in deleted),observed_volume_free_before=before,observed_volume_free_after=after,
        observed_volume_free_change=after-before,free_space_change_is_not_exact_causal_allocation=True,
        no_recursive_delete=True,no_old_round_or_user_content_deleted=True,
        retained_assets='All unique science/raw/failures, PDF/TeX, carriers, preflight and final PE/objects, shared DLL/dependencies and active tree'))
    print(json.dumps(dict(deleted_files=len(deleted),file_bytes=sum(x['bytes'] for x in deleted),observed_free_change=after-before)))

if __name__=='__main__':main()
