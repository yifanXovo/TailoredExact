"""Render only affected reading-draft pages for the author's finite visual review."""
from pathlib import Path
import hashlib,json,re,subprocess
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round129'
TEMP=Path('E:/codes/ExactEBRP-work/temp/round129')
POPPLER=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    pdf=OUT/'manuscript.pdf';reader=PdfReader(pdf)
    texts=[' '.join((p.extract_text() or '').split()) for p in reader.pages]
    starts=[i for i,t in enumerate(texts) if '6.9 Prospective confirmation' in t]
    assert len(starts)==1,starts
    start=starts[0]
    end=next(i for i in range(start,len(texts)) if '7. Extended endpoint evidence' in texts[i])
    appendix=[i for i,t in enumerate(texts) if i>start and 'B.13 Uniform support candidate confirmation' in t]
    assert len(appendix)==1
    selected=sorted({1,2,*range(max(0,start-1),min(len(texts),end+2)),*appendix})
    complete='\n'.join(texts)
    for needle in ['147.147','151.415','RECOMMEND_UNIFORM_MS2_AS_PAPER_CANDIDATE','UC-B30-S','B.13 Uniform support candidate confirmation']:
        assert needle in complete,needle
    target=TEMP/'pdf_review';number=1
    while target.exists():
        number+=1;target=TEMP/f'pdf_review{number:02d}'
    target.mkdir(exist_ok=False)
    rows=[]
    for i in selected:
        prefix=target/f'page{i+1:02d}'
        command=[str(POPPLER),'-f',str(i+1),'-l',str(i+1),'-r','115','-png','-singlefile',str(pdf),str(prefix)]
        subprocess.run(command,check=True,capture_output=True,timeout=60)
        image=prefix.with_suffix('.png')
        rows.append(dict(page=i+1,path=str(image),SHA=digest(image)))
    receipt=dict(status='RENDERED_PENDING_ACTUAL_VISUAL_INSPECTION',PDF=str(pdf),PDF_SHA=digest(pdf),
        pages=len(reader.pages),affected_section_pages=list(range(start+1,end+2)),rendered_images=rows,
        retained_historical_pages_not_all_rerendered=True,scope='Abstract/update, Section6.9 and boundaries, B.13; no all-history visual revalidation')
    (OUT/'review/pdf_render_manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(pages=len(reader.pages),rendered_pages=[r['page'] for r in rows],PDF_SHA=receipt['PDF_SHA'])))

if __name__=='__main__':main()
