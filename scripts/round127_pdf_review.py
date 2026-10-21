"""Finite Poppler page extraction/rendering; visual judgments are recorded separately."""
from round127_common import *
import argparse,re

POPPLER=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin')

def inspect(attempt):
    target=TEMP/'pdf_review'/attempt
    target.mkdir(parents=True,exist_ok=False)
    pdf=OUT/'manuscript.pdf'
    info_bytes=subprocess.check_output([str(POPPLER/'pdfinfo.exe'),str(pdf)])
    (target/'pdfinfo.raw').write_bytes(info_bytes)
    try:info=info_bytes.decode('utf-8');info_encoding='utf-8'
    except UnicodeDecodeError:info=info_bytes.decode('cp936');info_encoding='cp936 Windows locale'
    (target/'pdfinfo.txt').write_text(info,encoding='utf-8')
    textpath=target/'pages.txt'
    text_tool=POPPLER/'pdftotext.exe'
    if not text_tool.is_file():text_tool=Path(shutil.which('pdftotext') or '')
    assert text_tool.is_file(),'No installed pdftotext available'
    subprocess.run([str(text_tool),'-layout','-enc','UTF-8',str(pdf),str(textpath)],check=True)
    pages=textpath.read_text(encoding='utf-8').split('\f')
    if not pages[-1].strip():pages.pop()
    page_map=[]
    for n,page in enumerate(pages,1):
        lines=[x.strip() for x in page.splitlines() if x.strip()]
        labels=[x for x in lines if re.search(r'R127|^Abstract$|^\d\. |^6\.[4-7] |^Appendix|^A\.1 |^References$',x)]
        page_map.append(dict(page=n,first_lines=lines[:2],labels=labels))
    match=re.search(r'^Pages:\s+(\d+)',info,re.M)
    assert match and int(match.group(1))==len(pages)
    result=dict(attempt=attempt,PDF_SHA256=sha(pdf),PDF_bytes=pdf.stat().st_size,pdfinfo_encoding=info_encoding,pdftotext=str(text_tool),
        pages=len(pages),text_SHA256=sha(textpath),page_map=page_map,
        export_receipt=read(OUT/'pdf_export.json'),visual_inspection_completed=False)
    write(target/'page_map.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='export_receipt'}))

def render(attempt,numbers):
    target=TEMP/'pdf_review'/attempt
    page_map=read(target/'page_map.json');pdf=OUT/'manuscript.pdf'
    assert sha(pdf)==page_map['PDF_SHA256'],'PDF changed since page-map extraction'
    selected=sorted({int(n) for n in numbers.split(',')})
    assert selected and selected[0]>=1 and selected[-1]<=page_map['pages']
    images=[]
    for n in selected:
        prefix=target/f'page{n:03d}'
        assert not prefix.with_suffix('.png').exists()
        subprocess.run([str(POPPLER/'pdftoppm.exe'),'-f',str(n),'-l',str(n),'-scale-to','1800',
            '-singlefile','-png',str(pdf),str(prefix)],check=True,stdout=subprocess.DEVNULL)
        p=prefix.with_suffix('.png');images.append(dict(page=n,path=str(p),SHA256=sha(p),bytes=p.stat().st_size))
    result=dict(attempt=attempt,PDF_SHA256=sha(pdf),rendered=images,visual_inspection_completed=False,
        judgment='Rendering is not a visual PASS; inspect the returned page images and record actual observations.')
    write(target/'render_receipt.json',result)
    print(json.dumps(result))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['inspect','render'])
    parser.add_argument('--attempt',required=True);parser.add_argument('--pages')
    args=parser.parse_args()
    if args.mode=='inspect':inspect(args.attempt)
    else:render(args.attempt,args.pages)
