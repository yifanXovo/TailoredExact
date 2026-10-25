"""Render the actual complete PDF and prepare, but never fake, visual QA."""
from round133_common import *
import re, shutil


def render():
    from PIL import Image, ImageDraw, ImageOps
    import pdfplumber
    pdf=OUT/'manuscript.pdf';directory=TEMP/('pdf/visual_QA_'+sha(pdf)[:10])
    directory.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter()
    subprocess.run(['pdftoppm','-r','90','-png',str(pdf),str(directory/'page')],check=True,timeout=240)
    fonts=subprocess.check_output(['pdffonts',str(pdf)],text=True,errors='replace')
    (directory/'fonts.txt').write_text(fonts,encoding='utf-8')
    pages=[]
    with pdfplumber.open(pdf) as document:
        for n,page in enumerate(document.pages,1):
            text=page.extract_text() or ''
            outside=[dict(text=c.get('text'),x0=c['x0'],x1=c['x1'],top=c['top'],bottom=c['bottom'])
                for c in page.chars if c['x0']<-.5 or c['x1']>page.width+.5 or c['top']<-.5 or c['bottom']>page.height+.5]
            pages.append(dict(page=n,width=page.width,height=page.height,characters=len(page.chars),
                extracted_characters=len(text),replacement_characters=text.count('\ufffd'),
                outside_page_characters=outside,opening=text[:180],
                topics=[word for word in ('Table Q1','Table Q2','Table Q3','Table Q4','J2','J3','References',
                    '5.4 Numerical','A.7','B.4.2','Appendix C','540431955','1/4') if word in text]))
            (directory/f'text-{n:02d}.txt').write_text(text,encoding='utf-8')
    images=sorted(directory.glob('page-*.png'))
    assert len(images)==len(pages)
    sheets=[]
    for start in range(0,len(images),6):
        sheet=Image.new('RGB',(1440,3030),'#c9c9c9');draw=ImageDraw.Draw(sheet)
        for i,path in enumerate(images[start:start+6]):
            with Image.open(path) as page:
                thumb=ImageOps.contain(page.convert('RGB'),(700,970))
                x=(i%2)*720+(720-thumb.width)//2;y=(i//2)*1010+28
                sheet.paste(thumb,(x,y))
            draw.text(((i%2)*720+12,(i//2)*1010+8),f'Actual PDF page {start+i+1}',fill='black')
        target=directory/f'contact-{start//6+1:02d}.png';sheet.save(target)
        sheets.append(dict(path=str(target),SHA=sha(target),pages=list(range(start+1,min(start+6,len(images))+1))))
    receipt=dict(status='RENDERED_PENDING_ACTUAL_VISUAL_INSPECTION',UTC=utc(),PDF_SHA=sha(pdf),
        manuscript_SHA=sha(OUT/'manuscript.md'),pages=pages,page_count=len(pages),
        page_images=[dict(page=i+1,path=str(path),SHA=sha(path)) for i,path in enumerate(images)],
        contact_sheets=sheets,fonts=fonts,fonts_embedded_review_pending=True,
        renderer='pdftoppm 90dpi; no scientific text changed',seconds=time.perf_counter()-tick,
        Optimize=0,native_starts=0,compile=0,
        prior_export_attempt01_preserved=True,marker_successful_invocations=1,
        export_only_repairs='Bare prose SHA break opportunities and paragraph emergency stretch; maintained source unchanged')
    write(OUT/'review/pdf_render_receipt.json',receipt)
    print(json.dumps(dict(pages=len(pages),outside=sum(len(p['outside_page_characters']) for p in pages),
        replacements=sum(p['replacement_characters'] for p in pages),seconds=receipt['seconds'],
        contact_sheets=[r['path'] for r in sheets],topic_pages=[dict(page=p['page'],topics=p['topics']) for p in pages if p['topics']])))


def attest_actual_inspection():
    # Invoked only by the primary after the actual image views, not by render.
    receipt=read(OUT/'review/pdf_render_receipt.json')
    assert receipt['page_count']==50 and receipt['PDF_SHA']==sha(OUT/'manuscript.pdf')
    assert receipt['manuscript_SHA']==sha(OUT/'manuscript.md')
    assert all(not row['outside_page_characters'] and not row['replacement_characters'] for row in receipt['pages'])
    prior=read(OUT/'review/pdf_render_attempt02.json')
    old={row['page']:row for row in prior['page_images']}
    same=[]
    for row in receipt['page_images']:
        assert sha(row['path'])==row['SHA']
        if old[row['page']]['SHA']==row['SHA']:same.append(row['page'])
    assert same==[1,*range(3,38)]
    font_rows=receipt['fonts'].splitlines()[2:]
    assert len(font_rows)==19 and all(re.search(r'\s+yes\s+yes\s+(?:yes|no)\s+\d+\s+0\s*$',line) for line in font_rows)
    export=read(OUT/'pdf_export.json')
    overfull=[float(re.search(r'\(([0-9.]+)pt',line)[1]) for line in export['warnings'] if 'Overfull' in line]
    assert not overfull or max(overfull)<.2
    receipt.update(status='PASS',actual_inspector='/root',UTC_inspected=utc(),
        all_50_pages_actual_visual_QA=True,
        procedure='All53 prior rendered pages viewed in nine contact sheets. Exact PNG equality reuses inspection of current pages1,3-37. Final pages2,38-50 viewed again in final contact sheets/full pages. Full-size affected pages11,12,16,17,28,39,40,50 inspected for scientific text, equations, tables, null clocks, signed gaps, references and page flow.',
        exact_identical_final_pages_reusing_actual_inspection=same,
        final_changed_pages_reinspected=[2,*range(38,51)],
        full_size_affected_pages=[2,11,12,16,17,28,39,40,50],
        fonts_embedded=19,fonts_embedded_review_pending=False,
        visual_findings='No clipping, overlap, missing glyph or table/caption loss. Repaired bare-hash overhangs and orphan engineering paragraph; Q2-Q4 retain ordered landscape flow. The remaining <0.2pt longtable arithmetic warnings have no visible overhang or page-boundary violation.',
        maintained_scientific_text_unchanged=True,publication_ready_layout=True)
    write(OUT/'review/pdf_visual_QA.json',receipt)
    export.update(visual_review_pending=False,page_visual_QA='PASS actual all-page render inspection; review/pdf_visual_QA.json',
        final_pages=50,PDF_SHA=receipt['PDF_SHA'],visual_QA_SHA=sha(OUT/'review/pdf_visual_QA.json'))
    write(OUT/'pdf_export.json',export)
    print(json.dumps(dict(status='PASS',pages=50,PDF_SHA=receipt['PDF_SHA'],fonts_embedded=19)))


if __name__=='__main__':
    if sys.argv[1:]==['attest-actual-inspection']:attest_actual_inspection()
    else:
        assert not sys.argv[1:]
        render()
