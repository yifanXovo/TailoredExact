"""Render real final PDF pages; never assert visual acceptance automatically."""
from round135_common import *
import re

POPPLER=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin')
PDFFONTS=Path('C:/Users/Administrator/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdffonts.exe')

def main():
    from PIL import Image,ImageDraw,ImageOps
    import pdfplumber
    assert read(OUT/'candidate_decision.json')['study_complete'] and not budget()['unclosed']
    pdf=OUT/'manuscript.pdf';folder=TEMP/('pdf/visual_QA_'+sha(pdf)[:12]);folder.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter()
    subprocess.run([POPPLER/'pdftoppm.exe','-r','90','-png',pdf,folder/'page'],check=True,capture_output=True,timeout=300)
    fonts=subprocess.check_output([PDFFONTS,pdf],text=True,errors='replace')
    (folder/'fonts.txt').write_text(fonts,encoding='utf-8')
    pages=[]
    topics=['Proposition 1','Algorithm 1','Table 1','Table 2','Table 3','Within-instance',
        'State information','Implicit service','Ordered supply','References','Appendix A','Appendix B','A.7','B.4.1']
    with pdfplumber.open(pdf) as document:
        for number,page in enumerate(document.pages,1):
            text=page.extract_text() or ''
            outside=[dict(text=c.get('text'),x0=c['x0'],x1=c['x1'],top=c['top'],bottom=c['bottom'])
                for c in page.chars if c['x0']<-.5 or c['x1']>page.width+.5 or c['top']<-.5 or c['bottom']>page.height+.5]
            (folder/f'text-{number:02}.txt').write_text(text,encoding='utf-8')
            pages.append(dict(page=number,width=page.width,height=page.height,characters=len(page.chars),
                replacement_characters=text.count('\ufffd'),outside_page_characters=outside,
                opening=text[:140],topics=[t for t in topics if t in text]))
    images=sorted(folder.glob('page-*.png'));assert len(images)==len(pages)
    sheets=[]
    for start in range(0,len(images),6):
        sheet=Image.new('RGB',(1440,3030),'#cccccc');draw=ImageDraw.Draw(sheet)
        for index,path in enumerate(images[start:start+6]):
            with Image.open(path) as page:thumb=ImageOps.contain(page.convert('RGB'),(700,970))
            x=(index%2)*720+(720-thumb.width)//2;y=(index//2)*1010+28
            sheet.paste(thumb,(x,y));draw.text(((index%2)*720+12,(index//2)*1010+8),f'Actual page {start+index+1}',fill='black')
        target=folder/f'contact-{start//6+1:02}.png';sheet.save(target)
        sheets.append(dict(path=str(target),SHA256=sha(target),pages=list(range(start+1,min(start+6,len(images))+1))))
    receipt=dict(status='RENDERED_PENDING_ACTUAL_VISUAL_INSPECTION',UTC=utc(),PDF_SHA=sha(pdf),
        manuscript_SHA=sha(OUT/'manuscript.md'),page_count=len(pages),pages=pages,
        page_images=[dict(page=i+1,path=str(path),SHA256=sha(path)) for i,path in enumerate(images)],
        contact_sheets=sheets,fonts=fonts,renderer='bundled Poppler90dpi; PDF itself is unchanged',
        separate_document_seconds=time.perf_counter()-tick,Optimize=0,production_compile=0,
        actual_visual_inspection_complete=False,marker_successful_invocations=1)
    existing=OUT/'review/pdf_render_receipt.json'
    if existing.exists():
        old=read(existing);assert old['PDF_SHA']!=receipt['PDF_SHA'],'same PDF is already rendered; inspect that receipt'
        oldpath=existing.with_name('pdf_render_'+old['PDF_SHA'][:12]+'.json');assert not oldpath.exists();oldpath.write_bytes(existing.read_bytes())
    write(existing,receipt)
    print(json.dumps(dict(pages=len(pages),outside=sum(len(p['outside_page_characters']) for p in pages),
        replacements=sum(p['replacement_characters'] for p in pages),contact_sheets=[r['path'] for r in sheets],
        topic_pages=[dict(page=p['page'],topics=p['topics']) for p in pages if p['topics']])))

if __name__=='__main__':main()
