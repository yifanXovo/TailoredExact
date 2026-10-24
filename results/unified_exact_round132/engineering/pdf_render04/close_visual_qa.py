"""Close actual, hash-bound page inspection; never export or render a PDF."""
from pathlib import Path
import datetime, hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'results/unified_exact_round132'
TEMP = Path('E:/codes/ExactEBRP-work/temp/round132/pdf')

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p, v):
    Path(p).write_bytes((json.dumps(v, indent=2, allow_nan=False) + '\n').encode())

def binding(p):
    return dict(path=Path(p).relative_to(ROOT).as_posix(), SHA256=sha(p))

pdf = OUT / 'manuscript.pdf'
pdf_sha = sha(pdf)
export = read(OUT / 'pdf_export.json')
author = read(OUT / 'review/pdf_author_visual_qa.json')
other = read(OUT / 'review/PDF_independent_final.json')
document = read(OUT / 'review/pdf_document_checks.json')
final = read(TEMP / 'render04/render_inventory.json')
assert all(r['PDF_SHA'] == pdf_sha for r in (export, author, other, document, final))
assert other['status'] == 'PASS_FINITE_PDF_VISUAL_SCOPE'
assert not other['remaining_visual_blockers_in_scope']
assert not author['remaining_visual_findings']
for row in export['source_bindings']:
    assert sha(ROOT / row['path']) == row['SHA']
a = {r['page']: r['SHA256'] for r in author['page_bindings']}
b = {r['page']: r['final_render_SHA'] for r in other['pages']}
assert set(a) == set(range(1,25)) and set(b) == set(range(24,46))
assert all(r['byte_identical_to_inspected_image'] and
           r['final_render_SHA'] == r['inspected_image_SHA'] for r in other['pages'])
coverage = []
for r in final['pages']:
    n, h = r['page'], r['SHA256']
    assert sha(r['path']) == h and Path(r['path']).stat().st_size == r['bytes']
    assert (n in a and a[n] == h) or (n in b and b[n] == h)
    coverage.append(dict(page=n, SHA256=h, author=n in a, independent=n in b))
assert len(coverage) == 45 and {r['page'] for r in coverage} == set(range(1,46))
images = [dict(kind='final page raster', **r) for r in final['pages']]
images += [dict(kind='final inspection sheet', **r) for r in final['sheets']]
for r in images:
    assert sha(r['path']) == r['SHA256']

# Earlier draft PDFs have different bytes and remain retained. Their own PNGs
# can be reconstructed without deleting any distinct manuscript or failure.
prior = []
for n in range(1,4):
    inv_path = TEMP / f'render{n:02d}/render_inventory.json'
    inv = read(inv_path)
    retained = TEMP / f'attempt{n:02d}/reading.pdf'
    assert sha(retained) == inv['PDF_SHA'] and inv['PDF_SHA'] != pdf_sha
    copied = OUT / f'engineering/pdf_render{n:02d}/render_inventory.json'
    if copied.exists():
        assert sha(copied) == sha(inv_path)
    else:
        shutil.copyfile(inv_path, copied)
    rows = [dict(kind='reconstructible prior page raster', **r) for r in inv['pages']]
    rows += [dict(kind='reconstructible prior inspection sheet', **r) for r in inv['sheets']]
    for r in rows:
        assert sha(r['path']) == r['SHA256']
    prior.append(dict(retained_different_PDF=str(retained), PDF_SHA=inv['PDF_SHA'],
        original_inventory=binding(copied), images=rows,
        no_claim_all_prior_images_inspected=True))
copied = OUT / 'engineering/pdf_render04/render_inventory.json'
if copied.exists():
    assert sha(copied) == sha(TEMP / 'render04/render_inventory.json')
else:
    shutil.copyfile(TEMP / 'render04/render_inventory.json', copied)

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
manifest = dict(UTC=now, PDF_SHA=pdf_sha, status='FINAL_45_PAGES_VISUALLY_ACCEPTED',
    page_count=45, pages=images, reconstructible_prior_render_sets=prior,
    rendering_dpi=110, deletion_requires_exact_hash_and_owned_temp_path=True,
    all_different_PDFs_retained=True)
write(OUT / 'review/pdf_render_manifest.json', manifest)
qa = dict(UTC=now, status='PASS', PDF_SHA=pdf_sha, page_count=45,
    source_bindings=export['source_bindings'], actual_page_coverage=coverage,
    author_receipt=binding(OUT / 'review/pdf_author_visual_qa.json'),
    independent_receipt=binding(OUT / 'review/PDF_independent_final.json'),
    document_checks=binding(OUT / 'review/pdf_document_checks.json'),
    render_manifest=binding(OUT / 'review/pdf_render_manifest.json'),
    defects_resolved=['Table6 caption continuity', 'Readable C3/C4 LaTeX proof notation',
        'Current and historical section references', 'B1 current60D/24C launch authority'],
    remaining_visual_blockers=[], evidence_acceptance_is_separate=True,
    author_creation_time_pending_coverage_superseded=True,
    limitations='Actual110dpi page inspection and document checks; not a glyph-by-glyph or accessibility audit.')
write(OUT / 'review/pdf_visual_qa.json', qa)
export['visual_review_pending'] = False
export['visual_QA'] = binding(OUT / 'review/pdf_visual_qa.json')
write(OUT / 'pdf_export.json', export)
print(json.dumps(dict(status='PASS', PDF_SHA=pdf_sha, pages=45,
    final_reconstructible_images=len(images), prior_reconstructible_images=sum(len(x['images']) for x in prior))))
